"""Special Tab [S5]: Terminal Exhaustion & Delta Divergence Radar.

Deterministic quantitative replacement for subjective Elliott Wave counting (Wave 5 Tops
and Wave C Bottoms). Combines Tom DeMark's TD Sequential (TD-9 / TD-13), multi-horizon
Cumulative Volume Delta (CVD) regular and hidden divergences, and Open Interest / Funding
Rate climax stress into a unified 0-100 Exhaustion Score.
"""

from datetime import datetime, timezone
from typing import List, Optional, Sequence, Tuple

import numpy as np

from config.settings import EngineConfig
from core.models import (
    CVDDivergenceItem,
    DerivativesSnapshot,
    ExhaustionRadarEvaluation,
    ExhaustionRegime,
    ExhaustionTradePlan,
    FlowSnapshot,
    KlineBar,
    TDSignal,
    VolumeProfileResult,
)
from core.state_store import StateStore
from .volume_profile import compute_atr


class ExhaustionEngine:
    """Evaluates Special Tab [S5]: Terminal Exhaustion & Delta Divergence Radar."""

    def __init__(self, config: EngineConfig) -> None:
        self.config = config

    def _compute_td_sequential(
        self, bars: Sequence[KlineBar], horizon_label: str
    ) -> TDSignal:
        """Computes deterministic Tom DeMark (TD) 9-count price sequential.

        Rules:
        - Bearish Setup (Price rising into exhaustion top): close[i] > close[i-4] for 9 consecutive bars.
          Perfected if high of bar 8 or 9 >= high of bars 6 & 7.
        - Bullish Setup (Price falling into exhaustion bottom): close[i] < close[i-4] for 9 consecutive bars.
          Perfected if low of bar 8 or 9 <= low of bars 6 & 7.
        """
        if len(bars) < 13:
            return TDSignal(
                horizon=horizon_label,
                setup_count=0,
                direction="NEUTRAL",
                is_perfected=False,
                status="INSUFFICIENT DATA",
                invalidation_level=0.0,
            )

        closes = [b.close for b in bars]
        highs = [b.high for b in bars]
        lows = [b.low for b in bars]
        n = len(closes)

        # Track rolling counts
        bearish_count = 0  # close > close[i-4]
        bullish_count = 0  # close < close[i-4]

        # Scan backwards to get active unbroken streak
        for i in range(n - 1, 3, -1):
            c_curr = closes[i]
            c_prev = closes[i - 4]
            if c_curr > c_prev:
                if bullish_count > 0:
                    break
                bearish_count += 1
            elif c_curr < c_prev:
                if bearish_count > 0:
                    break
                bullish_count += 1
            else:
                break

        # Cap setup at 9
        if bearish_count > 0:
            count = min(bearish_count, 9)
            direction = "BEARISH_EXHAUSTION (Price Up / Top Setup)"
            is_perfected = False
            inv = max(highs[-count:])
            if count == 9:
                # Check perfection: high of bar 8 or 9 >= high of bars 6 & 7
                # In 0-indexed relative to last 9 bars: 8 and 7 vs 5 and 4
                h8_9 = max(highs[-1], highs[-2])
                h6_7 = max(highs[-3], highs[-4])
                is_perfected = h8_9 >= h6_7
                status = "PERFECTED 9/9 (REVERSAL ARMED)" if is_perfected else "UNPERFECTED 9/9"
            elif count >= 7:
                status = f"COUNTING ({count}/9 - LATE SETUP)"
            else:
                status = f"COUNTING ({count}/9)"

            return TDSignal(
                horizon=horizon_label,
                setup_count=count,
                direction=direction,
                is_perfected=is_perfected,
                status=status,
                invalidation_level=round(inv, 2),
            )

        elif bullish_count > 0:
            count = min(bullish_count, 9)
            direction = "BULLISH_EXHAUSTION (Price Down / Bottom Setup)"
            is_perfected = False
            inv = min(lows[-count:])
            if count == 9:
                l8_9 = min(lows[-1], lows[-2])
                l6_7 = min(lows[-3], lows[-4])
                is_perfected = l8_9 <= l6_7
                status = "PERFECTED 9/9 (REVERSAL ARMED)" if is_perfected else "UNPERFECTED 9/9"
            elif count >= 7:
                status = f"COUNTING ({count}/9 - LATE SETUP)"
            else:
                status = f"COUNTING ({count}/9)"

            return TDSignal(
                horizon=horizon_label,
                setup_count=count,
                direction=direction,
                is_perfected=is_perfected,
                status=status,
                invalidation_level=round(inv, 2),
            )

        return TDSignal(
            horizon=horizon_label,
            setup_count=0,
            direction="NEUTRAL",
            is_perfected=False,
            status="NEUTRAL CHOP",
            invalidation_level=0.0,
        )

    def _detect_fractal_pivots(
        self, bars: Sequence[KlineBar], left_bars: int = 3, right_bars: int = 1
    ) -> Tuple[List[Tuple[int, float]], List[Tuple[int, float]]]:
        """Detects objective swing highs and swing lows (bar_index, price)."""
        highs: List[Tuple[int, float]] = []
        lows: List[Tuple[int, float]] = []
        n = len(bars)
        if n < (left_bars + right_bars + 1):
            return highs, lows

        high_prices = [b.high for b in bars]
        low_prices = [b.low for b in bars]

        for i in range(left_bars, n - right_bars):
            val_h = high_prices[i]
            if val_h == max(high_prices[i - left_bars : i + right_bars + 1]):
                highs.append((i, float(val_h)))

            val_l = low_prices[i]
            if val_l == min(low_prices[i - left_bars : i + right_bars + 1]):
                lows.append((i, float(val_l)))

        return highs, lows

    def _detect_cvd_divergences(
        self,
        bars: Sequence[KlineBar],
        horizon_label: str,
        spot_delta: float,
        perp_delta: float,
    ) -> List[CVDDivergenceItem]:
        """Detects objective price vs. CVD fractal divergences."""
        items: List[CVDDivergenceItem] = []
        if len(bars) < 12:
            return items

        high_pivots, low_pivots = self._detect_fractal_pivots(bars, left_bars=3, right_bars=1)

        # 1. Bearish Divergence (Price Higher High vs. Delta Exhaustion)
        if len(high_pivots) >= 2:
            idx1, p1 = high_pivots[-2]
            idx2, p2 = high_pivots[-1]
            if p2 > p1:  # Higher High in Price
                # Check volume delta of the impulse
                bar_vol_1 = bars[idx1].volume
                bar_vol_2 = bars[idx2].volume
                bar_taker_1 = bars[idx1].taker_buy_volume
                bar_taker_2 = bars[idx2].taker_buy_volume
                delta_1 = 2 * bar_taker_1 - bar_vol_1
                delta_2 = 2 * bar_taker_2 - bar_vol_2

                if delta_2 < delta_1 or spot_delta < 0:
                    items.append(
                        CVDDivergenceItem(
                            horizon=horizon_label,
                            divergence_type="REGULAR_BEARISH (Wave 5 Top Exhaustion)",
                            price_extrema=f"Higher High (${p2:,.0f} vs ${p1:,.0f})",
                            cvd_extrema=f"Delta Deceleration ({delta_2:+.1f} vs {delta_1:+.1f} BTC)",
                            spot_delta=round(spot_delta, 2),
                            perp_delta=round(perp_delta, 2),
                            significance="CRITICAL DIVERGENCE",
                        )
                    )

        # 2. Bullish Divergence (Price Lower Low vs. Passive Absorption)
        if len(low_pivots) >= 2:
            idx1, p1 = low_pivots[-2]
            idx2, p2 = low_pivots[-1]
            if p2 < p1:  # Lower Low in Price
                bar_vol_1 = bars[idx1].volume
                bar_vol_2 = bars[idx2].volume
                bar_taker_1 = bars[idx1].taker_buy_volume
                bar_taker_2 = bars[idx2].taker_buy_volume
                delta_1 = 2 * bar_taker_1 - bar_vol_1
                delta_2 = 2 * bar_taker_2 - bar_vol_2

                if delta_2 > delta_1 or spot_delta > 0:
                    items.append(
                        CVDDivergenceItem(
                            horizon=horizon_label,
                            divergence_type="REGULAR_BULLISH (Wave C Bottom Absorption)",
                            price_extrema=f"Lower Low (${p2:,.0f} vs ${p1:,.0f})",
                            cvd_extrema=f"Delta Absorption ({delta_2:+.1f} vs {delta_1:+.1f} BTC)",
                            spot_delta=round(spot_delta, 2),
                            perp_delta=round(perp_delta, 2),
                            significance="CRITICAL DIVERGENCE",
                        )
                    )

        # 3. Derivatives Trap Divergence (Perp chasers vs Spot passivity)
        if (perp_delta > 20.0 and spot_delta < -5.0) or (perp_delta < -20.0 and spot_delta > 5.0):
            trap_type = "PERP LONG CHASER TRAP" if perp_delta > 0 else "PERP SHORT CHASER TRAP"
            items.append(
                CVDDivergenceItem(
                    horizon=horizon_label,
                    divergence_type=f"DERIVATIVES TRAP ({trap_type})",
                    price_extrema=f"Spot-Perp Decoupling ({horizon_label})",
                    cvd_extrema=f"Perp {perp_delta:+.1f} BTC vs Spot {spot_delta:+.1f} BTC",
                    spot_delta=round(spot_delta, 2),
                    perp_delta=round(perp_delta, 2),
                    significance="ABSORPTION",
                )
            )

        return items

    def evaluate(
        self,
        store: StateStore,
        bars_1h: Sequence[KlineBar],
        bars_4h: Sequence[KlineBar],
        bars_15m: Sequence[KlineBar],
        deriv: DerivativesSnapshot,
        flow: FlowSnapshot,
        active_vp: Optional[VolumeProfileResult] = None,
    ) -> Optional[ExhaustionRadarEvaluation]:
        """Evaluates Special Tab [S5]: Terminal Exhaustion & Delta Divergence Radar."""
        if not bars_1h:
            return None

        current_price = store.binance_spot_price or bars_1h[-1].close
        atr_1h = max(compute_atr(bars_1h[-30:], period=self.config.atr_period), 1.0)

        # 1. Compute Tom DeMark TD-9 Sequential on 1H and 4H
        td_1h = self._compute_td_sequential(bars_1h, "1H")
        td_4h = self._compute_td_sequential(bars_4h, "4H")

        # 2. Multi-Horizon CVD Divergences
        divergences: List[CVDDivergenceItem] = []
        div_15m = self._detect_cvd_divergences(
            bars_15m, "15m", flow.w_15m.spot_delta_btc, deriv.perp_5m_delta_btc
        )
        div_1h = self._detect_cvd_divergences(
            bars_1h, "1H", flow.w_1h.spot_delta_btc, flow.w_1h.perp_delta_btc
        )
        divergences.extend(div_15m)
        divergences.extend(div_1h)

        # 3. Open Interest & Funding Climax Metrics
        oi_15m_pct = deriv.oi_change_15m_pct
        oi_1h_pct = deriv.oi_change_1h_pct
        oi_climax_flag = (abs(oi_1h_pct) >= 1.20) or (abs(oi_15m_pct) >= 0.40)

        funding_pct = deriv.funding_rate_pct
        funding_climax_flag = (funding_pct >= 0.025) or (funding_pct <= -0.015)

        # 4. Composite Exhaustion Scoring (0 to 100)
        # Pillar A: TD Sequential (up to 35 pts)
        td_score = 0.0
        if td_1h.is_perfected or td_4h.is_perfected:
            td_score = 35.0
        elif td_1h.setup_count == 9 or td_4h.setup_count == 9:
            td_score = 25.0
        elif td_1h.setup_count >= 7 or td_4h.setup_count >= 7:
            td_score = 15.0

        # Pillar B: Delta Divergences (up to 35 pts)
        div_score = 0.0
        has_critical_div = any(d.significance == "CRITICAL DIVERGENCE" for d in divergences)
        has_absorption_div = any(d.significance == "ABSORPTION" for d in divergences)
        if has_critical_div and has_absorption_div:
            div_score = 35.0
        elif has_critical_div:
            div_score = 25.0
        elif has_absorption_div:
            div_score = 15.0

        # Pillar C: OI & Funding Climax Stress (up to 30 pts)
        climax_score = 0.0
        if oi_climax_flag and funding_climax_flag:
            climax_score = 30.0
        elif oi_climax_flag or funding_climax_flag:
            climax_score = 15.0

        total_score = min(td_score + div_score + climax_score, 100.0)

        # 5. Resolve Regime State & Primary Signal
        if total_score >= 80.0:
            regime = ExhaustionRegime.ACTIVE_REVERSAL_TRIGGER
        elif total_score >= 60.0:
            regime = ExhaustionRegime.TERMINAL_EXHAUSTION_ARMED
        elif total_score >= 35.0:
            regime = ExhaustionRegime.LATE_CYCLE_STRAIN
        else:
            regime = ExhaustionRegime.MOMENTUM_HEALTHY

        # Directional exhaustion orientation
        is_bearish_exhaustion = (
            "BEARISH" in td_1h.direction
            or "BEARISH" in td_4h.direction
            or any("BEARISH" in d.divergence_type for d in divergences)
            or funding_pct > 0.015
        )
        is_bullish_exhaustion = (
            "BULLISH" in td_1h.direction
            or "BULLISH" in td_4h.direction
            or any("BULLISH" in d.divergence_type for d in divergences)
            or funding_pct < -0.010
        )

        active_signal = "MOMENTUM BALANCED (Trend Intact)"
        trade_plan: Optional[ExhaustionTradePlan] = None

        poc_target = active_vp.c_poc if active_vp else (current_price - 2.0 * atr_1h)
        val_target = active_vp.c_val if active_vp else (current_price - 4.0 * atr_1h)
        vah_target = active_vp.c_vah if active_vp else (current_price + 4.0 * atr_1h)

        if regime in (ExhaustionRegime.ACTIVE_REVERSAL_TRIGGER, ExhaustionRegime.TERMINAL_EXHAUSTION_ARMED):
            if is_bearish_exhaustion and not is_bullish_exhaustion:
                active_signal = f"🚨 BEARISH EXHAUSTION (Score: {total_score:.0f}/100 • TD-9 + CVD Divergence)"
                sl_price = (td_1h.invalidation_level or current_price) + 0.5 * atr_1h
                risk = max(sl_price - current_price, 10.0)
                reward = max(current_price - poc_target, 10.0)
                rr = reward / risk
                trade_plan = ExhaustionTradePlan(
                    direction="SHORT (WAVE 5 EXHAUSTION SQUEEZE)",
                    entry_price=round(current_price, 2),
                    stop_loss=round(sl_price, 2),
                    tp1_fast_mean=round(poc_target, 2),
                    tp2_value_poc=round(val_target, 2),
                    risk_dollars=round(risk, 2),
                    reward_dollars=round(reward, 2),
                    rr_ratio=round(rr, 2),
                    invalidation_summary=f"Strict invalidation on 1H close above exhaustion wick (${sl_price:,.0f}).",
                )
                summary = (
                    f"Terminal upside exhaustion confirmed (Score: {total_score:.0f}/100). Aggressive buyers are hitting passive limit walls "
                    f"with TD-9 setup perfected on {td_1h.horizon} and delta deceleration. Target mean reversion to Composite POC (${poc_target:,.0f})."
                )
                takeaway = "TRIM SPOT / HEDGE DERIVATIVES — Do not chase late breakout highs into terminal exhaustion."

            elif is_bullish_exhaustion:
                active_signal = f"✅ BULLISH EXHAUSTION (Score: {total_score:.0f}/100 • TD-9 + CVD Absorption)"
                sl_price = (td_1h.invalidation_level or current_price) - 0.5 * atr_1h
                risk = max(current_price - sl_price, 10.0)
                reward = max(poc_target - current_price, 10.0)
                rr = reward / risk
                trade_plan = ExhaustionTradePlan(
                    direction="LONG (WAVE C CLIMAX REVERSAL)",
                    entry_price=round(current_price, 2),
                    stop_loss=round(sl_price, 2),
                    tp1_fast_mean=round(poc_target, 2),
                    tp2_value_poc=round(vah_target, 2),
                    risk_dollars=round(risk, 2),
                    reward_dollars=round(reward, 2),
                    rr_ratio=round(rr, 2),
                    invalidation_summary=f"Strict invalidation on 1H close below exhaustion wick (${sl_price:,.0f}).",
                )
                summary = (
                    f"Terminal downside exhaustion confirmed (Score: {total_score:.0f}/100). Aggressive sellers are absorbed by institutional limit bids "
                    f"with TD-9 setup perfected and delta divergence. Target mean reversion to Composite POC (${poc_target:,.0f})."
                )
                takeaway = "ACCUMULATE SPOT REBOUND — Trap late panic shorts into mean reversion rebound."
            else:
                active_signal = f"⚠️ TWO-SIDED EXHAUSTION STRAIN (Score: {total_score:.0f}/100)"
                summary = "Momentum is decelerating with conflicting directional signals. Await confirmed boundary break or candle close."
                takeaway = "HOLD CASH / OBSERVE — High volatility compression imminent."

        elif regime == ExhaustionRegime.LATE_CYCLE_STRAIN:
            active_signal = f"MOMENTUM STRAIN (Score: {total_score:.0f}/100 • Late Cycle Deceleration)"
            summary = "Trend is maturing. Trailing profit stops recommended; do not add fresh leverage."
            takeaway = "TIGHTEN STOPS — Trend momentum is entering late-stage compression."
        else:
            active_signal = f"MOMENTUM HEALTHY (Score: {total_score:.0f}/100 • Trend Expanding)"
            summary = "Price and volume delta are expanding in harmony without terminal divergence."
            takeaway = "TREND INTACT — Let winning swing positions run toward value boundaries."

        evaluation = ExhaustionRadarEvaluation(
            timestamp_utc=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            spot_price=round(current_price, 2),
            exhaustion_regime=regime,
            exhaustion_score=round(total_score, 1),
            active_exhaustion_signal=active_signal,
            td_1h=td_1h,
            td_4h=td_4h,
            divergences=divergences,
            oi_climax_pct=round(oi_1h_pct, 3),
            oi_climax_flag=oi_climax_flag,
            funding_climax_flag=funding_climax_flag,
            current_funding_pct=round(funding_pct, 4),
            trade_plan=trade_plan,
            plain_english_summary=summary,
            quantitative_takeaway=takeaway,
        )

        store.exhaustion_evaluation = evaluation
        return evaluation
