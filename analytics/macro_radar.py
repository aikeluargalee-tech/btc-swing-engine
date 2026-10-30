"""Tab [3] Analytics Engine: Macro Quant & Cycle Radar (Replaces 4-Page Web Platform).

Computes:
- Panel 1 (Quant Radar — The Gatekeeper): 1D Close vs 1D 200 SMA & 5-Day 200 SMA Slope
  (Rule 1 Gatekeeper Veto if Close < 200 SMA or Slope <= 0), 1D 21 EMA Bull Support Band,
  14D Wilder RSI, and 30D Volume Profile POC.
- Panel 2 (Regime Radar — Cycle Armor & Drawdown Rungs): Cycle High reference, current
  drawdown %, active crash accumulation rungs (-25%, -35%, -45%, -55%, -65%), and
  multi-month scale-out ceiling targets.
- Panel 3 (Liquidity Radar — Multi-Timeframe 1W / 1D / 4H Sniper Matrix): 1W, 1D (Completed
  vs Forming), and 4H candle structure, 4H Liquidation Wick Flush detector, and momentum alignment.
- Panel 4 (Unified Macro Arb & Allocation Engine): 4-Family composite Macro Confidence Score
  (0-100%), Gatekeeper Veto status, and recommended Spot Allocation tier.
"""

from datetime import datetime, timezone
import math
from typing import List, Optional, Sequence, Tuple

import numpy as np

from config.settings import EngineConfig
from core.models import (
    CrashRungItem,
    DerivativesSnapshot,
    FlowSnapshot,
    KlineBar,
    MacroRadarEvaluation,
    MacroTimeframeRow,
    VolumeProfileResult,
)
from core.state_store import StateStore
from .protocol_v13 import synthesize_1d_bars_from_1h
from .volume_profile import synthesize_4h_bars


def compute_ema(values: Sequence[float], period: int) -> float:
    """Computes standard Exponential Moving Average over `values`."""
    if not values:
        return 0.0
    if len(values) < period:
        return float(np.mean(values))
    alpha = 2.0 / (period + 1.0)
    ema = float(np.mean(values[:period]))
    for v in values[period:]:
        ema = (float(v) - ema) * alpha + ema
    return ema


def compute_wilder_rsi(closes: Sequence[float], period: int = 14) -> float:
    """Computes exact 14-period Wilder RSI over daily closes."""
    if len(closes) < period + 1:
        return 50.0
    diffs = np.diff(np.array(closes, dtype=float))
    gains = np.where(diffs > 0, diffs, 0.0)
    losses = np.where(diffs < 0, -diffs, 0.0)

    avg_gain = float(np.mean(gains[:period]))
    avg_loss = float(np.mean(losses[:period]))

    for i in range(period, len(diffs)):
        avg_gain = (avg_gain * (period - 1) + float(gains[i])) / period
        avg_loss = (avg_loss * (period - 1) + float(losses[i])) / period

    if avg_loss <= 1e-9:
        return 100.0 if avg_gain > 0 else 50.0
    rs = avg_gain / avg_loss
    return float(100.0 - (100.0 / (1.0 + rs)))


def compute_200d_sma_and_slope(closes: Sequence[float], period: int = 200, slope_days: int = 5) -> Tuple[float, float, float]:
    """Returns (current_200d_sma, slope_usd_per_day, slope_5d_pct).

    Falls back gracefully to available lookback window if fewer than 200 bars exist in unit tests.
    """
    if not closes:
        return 0.0, 0.0, 0.0
    eff_period = min(period, max(10, len(closes) - slope_days)) if len(closes) > slope_days + 5 else len(closes)
    cur_sma = float(np.mean(closes[-eff_period:]))
    if len(closes) > eff_period + slope_days:
        prev_window = closes[-(eff_period + slope_days) : -slope_days]
        prev_sma = float(np.mean(prev_window))
        slope_usd_per_day = (cur_sma - prev_sma) / float(slope_days)
        slope_5d_pct = ((cur_sma - prev_sma) / max(prev_sma, 1.0)) * 100.0
    else:
        slope_usd_per_day = 0.0
        slope_5d_pct = 0.0
    return cur_sma, slope_usd_per_day, slope_5d_pct


def compute_power_law_valuation(
    current_price: float,
    now_utc: Optional[datetime] = None,
) -> Tuple[float, float, str]:
    """Computes Bitcoin Genesis Power-Law fair-value midline and % discount/premium.

    Strictly quarantined as a long-horizon positional regime filter (never used for short-term timing).
    Formula: P_fair(t) = 10^(-16.493 + 5.680 * log10(days_since_genesis)), where Genesis = 2009-01-03.
    """
    ref_dt = now_utc if now_utc is not None else datetime.now(timezone.utc)
    genesis_dt = datetime(2009, 1, 3, 0, 0, tzinfo=timezone.utc)
    days_since_genesis = max(1.0, (ref_dt - genesis_dt).total_seconds() / 86_400.0)
    fair_usd = 10.0 ** (-16.493 + 5.680 * math.log10(days_since_genesis))
    discount_pct = ((current_price - fair_usd) / max(fair_usd, 1.0)) * 100.0

    if discount_pct <= -35.0:
        zone_label = "DEEP DISCOUNT [BIAS ONLY]"
    elif discount_pct <= -10.0:
        zone_label = "DISCOUNT TILT [BIAS ONLY]"
    elif discount_pct <= 25.0:
        zone_label = "FAIR VALUE [BIAS ONLY]"
    else:
        zone_label = "PREMIUM ZONE [BIAS ONLY]"

    return round(fair_usd, 2), round(discount_pct, 1), zone_label


class MacroRadarEvaluator:
    """Evaluates Tab [3] Macro Quant & Cycle Radar across 1W, 1D, and 4H timeframes."""

    def __init__(self, config: EngineConfig) -> None:
        self.config = config

    @staticmethod
    def _detect_4h_wick_flush(
        bars_4h: Sequence[KlineBar],
        deriv: DerivativesSnapshot,
        support_ref: float,
    ) -> Tuple[bool, float, str]:
        """Detects 4H lower-wick liquidity sweep paired with OI flush / funding reset."""
        if not bars_4h:
            return False, 0.0, "Insufficient 4H data"

        best_ratio = 0.0
        flush_detected = False
        best_bar: Optional[KlineBar] = None

        for bar in bars_4h[-4:]:
            rng = max(bar.high - bar.low, 1e-6)
            body_floor = min(bar.open, bar.close)
            lower_wick = max(0.0, body_floor - bar.low)
            wick_ratio = (lower_wick / rng) * 100.0
            if wick_ratio > best_ratio:
                best_ratio = wick_ratio
                best_bar = bar

            near_support = bar.low <= support_ref * 1.015
            oi_or_funding_reset = deriv.oi_change_4h_pct <= -1.0 or deriv.funding_rate_pct <= 0.010
            if wick_ratio >= 42.0 and bar.close >= bar.open and near_support and oi_or_funding_reset:
                flush_detected = True

        if flush_detected and best_bar is not None:
            detail = (
                f"ACTIVE FLUSH: 4H lower wick {best_ratio:.1f}% of range (Low ${best_bar.low:,.0f}) "
                f"+ 4H dOI {deriv.oi_change_4h_pct:+.2f}% / Funding {deriv.funding_rate_pct:+.4f}%"
            )
        else:
            detail = (
                f"STANDBY: Max recent 4H lower wick {best_ratio:.1f}% (Need >=42% sweep + OI/Funding reset)"
            )
        return flush_detected, round(best_ratio, 1), detail

    @staticmethod
    def _build_tf_row(label: str, bars: Sequence[KlineBar], idx: int = -1) -> MacroTimeframeRow:
        """Constructs a multi-timeframe sniper matrix row for 1W, 1D [-2], 1D [-1], or 4H."""
        if not bars:
            return MacroTimeframeRow(label, "WARMING UP", 0.0, "N/A", "NEUTRAL")
        eff_idx = idx if abs(idx) <= len(bars) else -1
        b = bars[eff_idx]
        prev = bars[eff_idx - 1] if abs(eff_idx - 1) <= len(bars) else b

        chg_pct = ((b.close - b.open) / max(b.open, 1.0)) * 100.0
        rng = max(b.high - b.low, 1e-6)
        lower_wick_pct = (max(0.0, min(b.open, b.close) - b.low) / rng) * 100.0

        if b.close > prev.close and b.low >= prev.low:
            struct = "BULLISH (HH / HL)"
        elif b.close < prev.low:
            struct = "BEARISH (LH / LL)"
        else:
            struct = "CONSOLIDATION / INSIDE"

        sig = (
            f"Close ${b.close:,.0f} ({chg_pct:+.2f}%) | Low Wick {lower_wick_pct:.0f}%"
        )
        flow_mom = (
            f"Delta {b.delta:+,.0f} BTC ({'BUY' if b.delta > 0 else 'SELL'})"
        )
        return MacroTimeframeRow(
            timeframe=label,
            structure=struct,
            close_vs_open_pct=round(chg_pct, 2),
            candle_signature=sig,
            flow_momentum=flow_mom,
        )

    def evaluate(
        self,
        store: StateStore,
        flow: FlowSnapshot,
        deriv: DerivativesSnapshot,
        macro_vp: Optional[VolumeProfileResult],
        cycle_ath_override: float = 0.0,
    ) -> MacroRadarEvaluation:
        """Runs full Tab [3] Macro Quant & Cycle Radar evaluation."""
        spot_1h = list(store.spot_klines_1h)
        spot_1d = list(store.spot_klines_1d) or synthesize_1d_bars_from_1h(spot_1h)
        spot_1w = list(store.spot_klines_1w)
        bars_4h = synthesize_4h_bars(spot_1h)

        current_price = store.binance_spot_price or (spot_1h[-1].close if spot_1h else 0.0)
        comp_1d_close = spot_1d[-2].close if len(spot_1d) >= 2 else current_price
        form_1d_close = spot_1d[-1].close if spot_1d else current_price

        # Use Completed 1D closes up to [-2] + current price for live responsive MA, or strict completed closes
        daily_closes_completed = [b.close for b in spot_1d[:-1]] if len(spot_1d) >= 2 else [b.close for b in spot_1d]
        daily_closes_all = [b.close for b in spot_1d] if spot_1d else [current_price]

        # 1. Quant Radar: 1D 200 SMA & 5-Day Slope, 1D 21 EMA, 14D Wilder RSI, 30D POC
        sma_200, slope_5d_usd, slope_5d_pct = compute_200d_sma_and_slope(
            daily_closes_completed or daily_closes_all, period=200, slope_days=5
        )
        ema_21 = compute_ema(daily_closes_all, period=21)
        rsi_14 = compute_wilder_rsi(daily_closes_all, period=14)

        if rsi_14 < 30.0:
            rsi_zone = "OVERSOLD (<30 - Deep Value)"
        elif rsi_14 < 45.0:
            rsi_zone = "COOL / ACCUMULATION (30-45)"
        elif rsi_14 <= 68.0:
            rsi_zone = "BULL / NEUTRAL MOMENTUM (45-68)"
        else:
            rsi_zone = "OVERBOUGHT (>68 - Trim Risk)"

        poc_30d = macro_vp.c_poc if macro_vp is not None else current_price
        dist_21ema_pct = ((current_price - ema_21) / max(ema_21, 1.0)) * 100.0
        dist_30dpoc_pct = ((current_price - poc_30d) / max(poc_30d, 1.0)) * 100.0
        pl_fair_usd, pl_discount_pct, pl_zone_label = compute_power_law_valuation(current_price)

        # Rule 1 Macro Gatekeeper Check: Close >= 200D SMA AND 5D Slope > 0
        above_200d = current_price >= sma_200 and comp_1d_close >= sma_200
        slope_positive = slope_5d_usd > 0.0
        gatekeeper_veto = not (above_200d and slope_positive)

        if not gatekeeper_veto:
            gatekeeper_status_text = "PASS (Price >= 200D SMA & Slope Rising -> Macro Bull Trend)"
        elif not above_200d and not slope_positive:
            gatekeeper_status_text = "VETO ACTIVE (1D Close < 200D SMA & 5D Slope Falling/Flat)"
        elif not above_200d:
            gatekeeper_status_text = "VETO ACTIVE (1D Close Below 200D SMA — Defensive Regime)"
        else:
            gatekeeper_status_text = "VETO ACTIVE (200D SMA 5-Day Slope <= 0)"

        # 2. Regime Radar: Cycle High Drawdown & Crash Accumulation Rungs (-25% to -65%)
        max_1w_high = max((b.high for b in spot_1w), default=0.0)
        max_1d_high = max((b.high for b in spot_1d), default=0.0)
        ref_ath = max(cycle_ath_override, self.config.default_cycle_ath_usd, max_1w_high, max_1d_high, current_price)
        drawdown_pct = ((current_price - ref_ath) / max(ref_ath, 1.0)) * 100.0  # negative percentage

        rung_specs = [
            ("-25% Rung 1 (Bull Pullback)", -25.0, "15% Spot Tranche"),
            ("-35% Rung 2 (Mid Correction)", -35.0, "20% Spot Tranche"),
            ("-45% Rung 3 (Deep Value)", -45.0, "25% Spot Tranche"),
            ("-55% Rung 4 (Capitulation)", -55.0, "25% Spot Tranche"),
            ("-65% Rung 5 (Generational Floor)", -65.0, "15% Max Vault"),
        ]
        crash_rungs: List[CrashRungItem] = []
        active_crash_rung = "NONE (Above -25% Rung)"
        any_rung_hit = False

        for label, dd_lvl, tranche in rung_specs:
            lvl_price = ref_ath * (1.0 + dd_lvl / 100.0)
            dist_pct = ((current_price - lvl_price) / max(lvl_price, 1.0)) * 100.0
            if drawdown_pct <= dd_lvl:
                status = "HIT / ACTIVE"
                active_crash_rung = f"{label} (${lvl_price:,.0f})"
                any_rung_hit = True
            elif abs(dist_pct) <= 3.0:
                status = "NEAR (<3.0%)"
                if active_crash_rung.startswith("NONE"):
                    active_crash_rung = f"APPROACHING {label} (${lvl_price:,.0f})"
            else:
                status = "STANDBY"

            crash_rungs.append(
                CrashRungItem(
                    rung_label=label,
                    drawdown_pct=dd_lvl,
                    target_price=round(lvl_price, 2),
                    distance_pct=round(dist_pct, 2),
                    allocation_tranche=tranche,
                    status=status,
                )
            )

        scale_out_targets = [
            f"T1 (1D 21 EMA Mean Reversion): ${ema_21:,.0f} ({((ema_21 - current_price) / max(current_price, 1.0)) * 100:+.1f}%)",
            f"T2 (1D 200 SMA Macro Reclaim): ${sma_200:,.0f} ({((sma_200 - current_price) / max(current_price, 1.0)) * 100:+.1f}%)",
            f"T3 (Cycle High Re-Test): ${ref_ath:,.0f} ({((ref_ath - current_price) / max(current_price, 1.0)) * 100:+.1f}%)",
            f"T4 (1.272x Cycle Extension): ${ref_ath * 1.272:,.0f}",
        ]

        # 3. Liquidity Radar: 1W / 1D / 4H Sniper Matrix & 4H Liquidation Wick Flush
        support_ref = (
            macro_vp.support_hvn_below_val
            if (macro_vp and macro_vp.support_hvn_below_val)
            else (macro_vp.c_val if macro_vp else current_price)
        )
        wick_flush_ok, wick_ratio, wick_detail = self._detect_4h_wick_flush(
            bars_4h, deriv, support_ref
        )

        tf_rows = [
            self._build_tf_row("1W Macro Candle", spot_1w or spot_1d, idx=-1),
            self._build_tf_row("1D Completed [-2]", spot_1d, idx=-2),
            self._build_tf_row("1D Forming [-1]", spot_1d, idx=-1),
            self._build_tf_row("4H Tactical Sniper", bars_4h, idx=-1),
        ]

        # 4. Unified 4-Family Macro Arb & Allocation Engine (Trend, Momentum, Flow, Structure)
        # Family 1: Trend (Max 25)
        trend_score = 0.0
        if above_200d:
            trend_score += 12.0
        if slope_positive:
            trend_score += 6.0
        if current_price >= ema_21:
            trend_score += 7.0
        elif abs(dist_21ema_pct) <= 2.0:
            trend_score += 3.5

        # Family 2: Momentum (Max 25)
        momentum_score = 0.0
        if 45.0 <= rsi_14 <= 65.0 and above_200d:
            momentum_score = 22.0
        elif rsi_14 < 35.0:
            # Deeply oversold mean-reversion coils
            momentum_score = 20.0
        elif 35.0 <= rsi_14 < 45.0:
            momentum_score = 12.0
        else:
            momentum_score = 8.0

        # Family 3: Order Flow & Derivatives (Max 25)
        flow_score = 0.0
        if flow.w_4h.spot_delta_btc > 0:
            flow_score += 10.0
        if flow.w_1h.spot_delta_btc > 0:
            flow_score += 6.0
        if deriv.coinbase_premium_pct > 0:
            flow_score += 5.0
        if deriv.funding_rate_pct <= self.config.funding_neutral_max_pct:
            flow_score += 4.0

        # Family 4: Structure, Crash Rung & 4H Wick Flush (Max 25)
        structure_score = 0.0
        if any_rung_hit:
            structure_score += 12.0
        elif current_price >= poc_30d:
            structure_score += 10.0
        else:
            structure_score += 5.0

        if wick_flush_ok:
            structure_score += 13.0
        elif wick_ratio >= 30.0:
            structure_score += 5.0

        macro_conf = round(trend_score + momentum_score + flow_score + structure_score, 1)
        crash_rung_override = any_rung_hit and (wick_flush_ok or rsi_14 <= 34.0) and flow.w_4h.spot_delta_btc > 0

        macro_notes: List[str] = []
        if not gatekeeper_veto:
            if macro_conf >= 70.0:
                recommended_allocation = "75% – 100% SPOT (Full Bull Trend Regime)"
            else:
                recommended_allocation = "50% SPOT (Core Bull Trend Hold / Buy 21D EMA Dips)"
            macro_notes.append(
                f"Rule 1 Gatekeeper PASSED: BTC (${current_price:,.0f}) is above rising 1D 200 SMA (${sma_200:,.0f}, +{slope_5d_usd:,.1f}/day)."
            )
        elif crash_rung_override:
            recommended_allocation = "20% – 25% TRANCHE (Crash-Rung Deep Value Accumulation Override)"
            macro_notes.append(
                f"Gatekeeper Override Active: Price below 200D SMA (${sma_200:,.0f}), but {active_crash_rung} + 4H Wick Flush/RSI exhaustion triggered."
            )
        elif any_rung_hit:
            recommended_allocation = "0% NEW TREND / LIMIT DCA ONLY AT CRASH RUNGS (Wait for 4H Flush + Spot Turn)"
            macro_notes.append(
                f"Rule 1 Gatekeeper VETO: Below 1D 200 SMA (${sma_200:,.0f}). Sitting in {active_crash_rung}; wait for 4H Wick Flush & Spot absorption."
            )
        else:
            recommended_allocation = "0% TREND ALLOCATION (100% Defensive Cash / Tactical 0.5% Risk Cap)"
            macro_notes.append(
                f"Rule 1 Gatekeeper VETO: 1D Close (${comp_1d_close:,.0f}) < 200D SMA (${sma_200:,.0f}) or 5D Slope ({slope_5d_usd:+.1f}/d) <= 0."
            )

        macro_notes.append(
            f"1D 21 EMA Band: ${ema_21:,.0f} ({dist_21ema_pct:+.2f}%) | 14D Wilder RSI: {rsi_14:.1f} ({rsi_zone})"
        )
        macro_notes.append(
            f"Cycle High: ${ref_ath:,.0f} (Drawdown: {drawdown_pct:+.2f}%) | Active Rung: {active_crash_rung}"
        )
        macro_notes.append(f"4H Wick Flush Sniper: {wick_detail}")

        ev = MacroRadarEvaluation(
            timestamp_utc=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            current_price=round(current_price, 2),
            completed_1d_close=round(comp_1d_close, 2),
            forming_1d_close=round(form_1d_close, 2),
            sma_200_1d=round(sma_200, 2),
            sma_200_slope_5d_usd=round(slope_5d_usd, 2),
            sma_200_slope_5d_pct=round(slope_5d_pct, 3),
            above_200d_sma=above_200d,
            slope_200d_positive=slope_positive,
            gatekeeper_veto=gatekeeper_veto,
            gatekeeper_status_text=gatekeeper_status_text,
            ema_21_1d=round(ema_21, 2),
            dist_to_21d_ema_pct=round(dist_21ema_pct, 2),
            rsi_14_1d=round(rsi_14, 1),
            rsi_zone=rsi_zone,
            poc_30d=round(poc_30d, 2),
            dist_to_30d_poc_pct=round(dist_30dpoc_pct, 2),
            power_law_fair_usd=pl_fair_usd,
            power_law_discount_pct=pl_discount_pct,
            power_law_zone_label=pl_zone_label,
            cycle_high_usd=round(ref_ath, 2),
            current_drawdown_pct=round(drawdown_pct, 2),
            active_crash_rung=active_crash_rung,
            crash_rung_override_active=crash_rung_override,
            crash_rungs=crash_rungs,
            scale_out_targets=scale_out_targets,
            tf_rows=tf_rows,
            wick_flush_4h_detected=wick_flush_ok,
            wick_flush_4h_ratio=wick_ratio,
            wick_flush_detail=wick_detail,
            trend_score=round(trend_score, 1),
            momentum_score=round(momentum_score, 1),
            flow_score=round(flow_score, 1),
            structure_score=round(structure_score, 1),
            macro_confidence_pct=macro_conf,
            recommended_allocation=recommended_allocation,
            macro_notes=macro_notes,
        )
        store.macro_evaluation = ev
        return ev
