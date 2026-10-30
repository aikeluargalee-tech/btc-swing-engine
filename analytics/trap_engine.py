"""Special Tab [S4]: Pattern Invalidation, Liquidity Sweep & SFP Trap Engine.

Weaponizes classical chart pattern boundaries (Head & Shoulders necklines, Double Tops/Bottoms,
Range Extremes, and Consolidation Channels) by modeling them as mechanical clusters of resting
retail stop-loss and breakout liquidity.

Executes the 3-State Microstructure Trap Finite State Machine:
- State 0: COMPRESSION (Building Open Interest into Pattern Boundary)
- State 1: BOUNDARY BREACH & SWEEP (Liquidity Stop Run beyond textbook boundary)
- State 2: SFP RECLAIM & ABSORPTION (Swing Failure Pattern execution with asymmetric R:R >= 1:3)
"""

from datetime import datetime, timezone
from typing import List, Optional, Sequence, Tuple

import numpy as np

from config.settings import EngineConfig
from core.models import (
    DerivativesSnapshot,
    FairValueGapItem,
    FlowSnapshot,
    KlineBar,
    PatternBoundaryItem,
    PatternType,
    TrapRadarEvaluation,
    TrapState,
    TrapTradePlan,
    VolumeProfileResult,
)
from core.state_store import StateStore
from .volume_profile import compute_atr


class TrapEngine:
    """Evaluates Special Tab [S4]: Pattern Invalidation, Liquidity Sweep & SFP Trap Desk."""

    def __init__(self, config: EngineConfig) -> None:
        self.config = config

    def _detect_fractal_pivots(
        self, bars: Sequence[KlineBar], left_bars: int = 4, right_bars: int = 2
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

    def _detect_asia_session_levels(
        self,
        bars_15m: Sequence[KlineBar],
        current_price: float,
        atr_1h: float,
    ) -> Tuple[List[PatternBoundaryItem], float, float, bool, bool]:
        """Calculates Asia Session (00:00 - 08:00 UTC) High/Low and evaluates session liquidity sweeps."""
        if not bars_15m:
            return [], 0.0, 0.0, False, False

        latest_dt = datetime.fromtimestamp(bars_15m[-1].timestamp_ms / 1000.0, tz=timezone.utc)
        target_date = latest_dt.date()

        asia_bars = [
            b
            for b in bars_15m
            if datetime.fromtimestamp(b.timestamp_ms / 1000.0, tz=timezone.utc).date() == target_date
            and 0 <= datetime.fromtimestamp(b.timestamp_ms / 1000.0, tz=timezone.utc).hour < 8
        ]

        if not asia_bars and len(bars_15m) >= 32:
            # Look back to previous completed day's Asia session
            prev_bars = [
                b
                for b in bars_15m
                if 0 <= datetime.fromtimestamp(b.timestamp_ms / 1000.0, tz=timezone.utc).hour < 8
            ]
            if prev_bars:
                last_prev_dt = datetime.fromtimestamp(prev_bars[-1].timestamp_ms / 1000.0, tz=timezone.utc).date()
                asia_bars = [
                    b
                    for b in prev_bars
                    if datetime.fromtimestamp(b.timestamp_ms / 1000.0, tz=timezone.utc).date() == last_prev_dt
                ]

        if not asia_bars:
            return [], 0.0, 0.0, False, False

        asia_high = max(b.high for b in asia_bars)
        asia_low = min(b.low for b in asia_bars)

        post_asia_bars = [b for b in bars_15m if b.timestamp_ms > asia_bars[-1].timestamp_ms]
        post_high = max((b.high for b in post_asia_bars), default=asia_high)
        post_low = min((b.low for b in post_asia_bars), default=asia_low)

        asia_high_swept = post_high > asia_high
        asia_low_swept = post_low < asia_low

        items: List[PatternBoundaryItem] = []

        # Asia High Boundary
        dist_h_pct = ((current_price - asia_high) / asia_high) * 100.0
        dist_h_atr = (current_price - asia_high) / atr_1h
        status_h = "COMPRESSION"
        if asia_high_swept:
            status_h = "SFP REJECTED" if current_price <= asia_high else "SWEEPING"

        items.append(
            PatternBoundaryItem(
                pattern_name="Asia Session High (00:00-08:00 UTC)",
                pattern_type=PatternType.ASIA_SESSION_HIGH,
                boundary_level=round(asia_high, 2),
                sweep_wick_extreme=round(post_high, 2),
                distance_pct=round(dist_h_pct, 2),
                distance_atr=round(dist_h_atr, 2),
                status=status_h,
                trap_bias="BEARISH (BULL TRAP)",
                liquidation_tier="SESSION OPEN RESTING STOPS",
            )
        )

        # Asia Low Boundary
        dist_l_pct = ((current_price - asia_low) / asia_low) * 100.0
        dist_l_atr = (current_price - asia_low) / atr_1h
        status_l = "COMPRESSION"
        if asia_low_swept:
            status_l = "SFP RECLAIMED" if current_price >= asia_low else "SWEEPING"

        items.append(
            PatternBoundaryItem(
                pattern_name="Asia Session Low (00:00-08:00 UTC)",
                pattern_type=PatternType.ASIA_SESSION_LOW,
                boundary_level=round(asia_low, 2),
                sweep_wick_extreme=round(post_low, 2),
                distance_pct=round(dist_l_pct, 2),
                distance_atr=round(dist_l_atr, 2),
                status=status_l,
                trap_bias="BULLISH (BEAR TRAP)",
                liquidation_tier="SESSION OPEN RESTING STOPS",
            )
        )

        return items, asia_high, asia_low, asia_high_swept, asia_low_swept

    def _detect_fair_value_gaps(
        self,
        bars: Sequence[KlineBar],
        timeframe: str,
        current_price: float,
        min_gap_pct: float = 0.05,
    ) -> List[FairValueGapItem]:
        """Detects 3-bar displacement imbalances (FVGs) and evaluates Consequent Encroachment (50% CE) mitigation state."""
        fvgs: List[FairValueGapItem] = []
        n = len(bars)
        if n < 3:
            return fvgs

        gap_counter = 0
        for i in range(2, n):
            b_prev2 = bars[i - 2]
            b_curr = bars[i]

            # 1. Bullish FVG: Low of candle 3 is strictly above High of candle 1
            if b_curr.low > b_prev2.high:
                gap_size = b_curr.low - b_prev2.high
                gap_pct = (gap_size / b_prev2.high) * 100.0
                if gap_pct >= min_gap_pct:
                    gap_counter += 1
                    top = b_curr.low
                    bottom = b_prev2.high
                    ce_mid = (top + bottom) / 2.0

                    sub_lows = [bars[k].low for k in range(i + 1, n)]
                    min_sub = min(sub_lows) if sub_lows else current_price
                    min_sub = min(min_sub, current_price)

                    if min_sub <= bottom:
                        status = "FULLY_MITIGATED"
                    elif min_sub <= ce_mid:
                        status = "PARTIALLY_MITIGATED"
                    else:
                        status = "UNMITIGATED"

                    if status != "FULLY_MITIGATED":
                        dist_pct = ((current_price - ce_mid) / ce_mid) * 100.0
                        if abs(dist_pct) <= 5.0:
                            fvgs.append(
                                FairValueGapItem(
                                    id=gap_counter,
                                    direction="BULLISH",
                                    timeframe=timeframe,
                                    top_price=round(top, 2),
                                    bottom_price=round(bottom, 2),
                                    ce_midpoint=round(ce_mid, 2),
                                    gap_pct=round(gap_pct, 2),
                                    status=status,
                                    distance_pct=round(dist_pct, 2),
                                )
                            )

            # 2. Bearish FVG: High of candle 3 is strictly below Low of candle 1
            elif b_curr.high < b_prev2.low:
                gap_size = b_prev2.low - b_curr.high
                gap_pct = (gap_size / b_prev2.low) * 100.0
                if gap_pct >= min_gap_pct:
                    gap_counter += 1
                    top = b_prev2.low
                    bottom = b_curr.high
                    ce_mid = (top + bottom) / 2.0

                    sub_highs = [bars[k].high for k in range(i + 1, n)]
                    max_sub = max(sub_highs) if sub_highs else current_price
                    max_sub = max(max_sub, current_price)

                    if max_sub >= top:
                        status = "FULLY_MITIGATED"
                    elif max_sub >= ce_mid:
                        status = "PARTIALLY_MITIGATED"
                    else:
                        status = "UNMITIGATED"

                    if status != "FULLY_MITIGATED":
                        dist_pct = ((current_price - ce_mid) / ce_mid) * 100.0
                        if abs(dist_pct) <= 5.0:
                            fvgs.append(
                                FairValueGapItem(
                                    id=gap_counter,
                                    direction="BEARISH",
                                    timeframe=timeframe,
                                    top_price=round(top, 2),
                                    bottom_price=round(bottom, 2),
                                    ce_midpoint=round(ce_mid, 2),
                                    gap_pct=round(gap_pct, 2),
                                    status=status,
                                    distance_pct=round(dist_pct, 2),
                                )
                            )

        return fvgs

    def _discover_pattern_boundaries(
        self,
        bars_1h: Sequence[KlineBar],
        current_price: float,
        atr_1h: float,
        active_vp: Optional[VolumeProfileResult] = None,
        bars_15m: Optional[Sequence[KlineBar]] = None,
    ) -> List[PatternBoundaryItem]:
        """Identifies active classical chart pattern boundaries and session extremes where retail orders cluster."""
        boundaries: List[PatternBoundaryItem] = []

        if bars_15m:
            asia_items, _, _, _, _ = self._detect_asia_session_levels(bars_15m, current_price, atr_1h)
            boundaries.extend(asia_items)

        if len(bars_1h) >= 10:
            high_pivots, low_pivots = self._detect_fractal_pivots(bars_1h, left_bars=3, right_bars=1)
        else:
            high_pivots, low_pivots = [], []

        # 1. Double Bottom / Equal Lows Liquidity Shelf
        if len(low_pivots) >= 2:
            l1 = low_pivots[-2][1]
            l2 = low_pivots[-1][1]
            if abs(l1 - l2) / min(l1, l2) <= 0.0075:  # Within 0.75%
                boundary_lvl = min(l1, l2)
                sweep_ext = min(b.low for b in bars_1h[low_pivots[-1][0] :])
                dist_pct = ((current_price - boundary_lvl) / boundary_lvl) * 100.0
                dist_atr = (current_price - boundary_lvl) / atr_1h
                status = "COMPRESSION"
                if sweep_ext < boundary_lvl:
                    status = "SFP RECLAIMED" if current_price >= boundary_lvl else "SWEEPING"
                boundaries.append(
                    PatternBoundaryItem(
                        pattern_name="1H Double Bottom Equal Lows",
                        pattern_type=PatternType.DOUBLE_BOTTOM,
                        boundary_level=round(boundary_lvl, 2),
                        sweep_wick_extreme=round(sweep_ext, 2),
                        distance_pct=round(dist_pct, 2),
                        distance_atr=round(dist_atr, 2),
                        status=status,
                        trap_bias="BULLISH (BEAR TRAP)",
                        liquidation_tier="HIGH DENSITY STOP CLUSTER",
                    )
                )

        # 2. Double Top / Equal Highs Resistance Shelf
        if len(high_pivots) >= 2:
            h1 = high_pivots[-2][1]
            h2 = high_pivots[-1][1]
            if abs(h1 - h2) / max(h1, h2) <= 0.0075:
                boundary_lvl = max(h1, h2)
                sweep_ext = max(b.high for b in bars_1h[high_pivots[-1][0] :])
                dist_pct = ((current_price - boundary_lvl) / boundary_lvl) * 100.0
                dist_atr = (current_price - boundary_lvl) / atr_1h
                status = "COMPRESSION"
                if sweep_ext > boundary_lvl:
                    status = "SFP REJECTED" if current_price <= boundary_lvl else "SWEEPING"
                boundaries.append(
                    PatternBoundaryItem(
                        pattern_name="1H Double Top Equal Highs",
                        pattern_type=PatternType.DOUBLE_TOP,
                        boundary_level=round(boundary_lvl, 2),
                        sweep_wick_extreme=round(sweep_ext, 2),
                        distance_pct=round(dist_pct, 2),
                        distance_atr=round(dist_atr, 2),
                        status=status,
                        trap_bias="BEARISH (BULL TRAP)",
                        liquidation_tier="HIGH DENSITY SHORT SQUEEZE POOL",
                    )
                )

        # 3. Head & Shoulders Neckline (3 Consecutive Highs: L Shoulder < Head > R Shoulder)
        if len(high_pivots) >= 3 and len(low_pivots) >= 2:
            sh_left = high_pivots[-3][1]
            head = high_pivots[-2][1]
            sh_right = high_pivots[-1][1]
            if head > sh_left and head > sh_right and abs(sh_left - sh_right) / head <= 0.035:
                # Neckline = low between left shoulder & head, and low between head & right shoulder
                neck_lows = [p[1] for p in low_pivots if high_pivots[-3][0] < p[0] < high_pivots[-1][0]]
                if neck_lows:
                    neck_lvl = min(neck_lows)
                    sweep_ext = min(b.low for b in bars_1h[high_pivots[-1][0] :]) if bars_1h else neck_lvl
                    dist_pct = ((current_price - neck_lvl) / neck_lvl) * 100.0
                    dist_atr = (current_price - neck_lvl) / atr_1h
                    status = "COMPRESSION"
                    if sweep_ext < neck_lvl:
                        status = "SFP RECLAIMED" if current_price >= neck_lvl else "SWEEPING"
                    boundaries.append(
                        PatternBoundaryItem(
                            pattern_name="1H Head & Shoulders Neckline",
                            pattern_type=PatternType.HEAD_AND_SHOULDERS,
                            boundary_level=round(neck_lvl, 2),
                            sweep_wick_extreme=round(sweep_ext, 2),
                            distance_pct=round(dist_pct, 2),
                            distance_atr=round(dist_atr, 2),
                            status=status,
                            trap_bias="BULLISH (BEAR TRAP)",
                            liquidation_tier="EXTREME BREAKOUT SHORT POOL",
                        )
                    )

        # 4. Range Extreme Support / Value Area Low
        if active_vp is not None:
            # 70% Value Area Low acts as primary structural range floor
            val_lvl = active_vp.c_val
            sweep_val = min(b.low for b in bars_1h[-12:]) if bars_1h else val_lvl
            dist_val_pct = ((current_price - val_lvl) / val_lvl) * 100.0
            dist_val_atr = (current_price - val_lvl) / atr_1h
            status_val = "COMPRESSION"
            if sweep_val < val_lvl:
                status_val = "SFP RECLAIMED" if current_price >= val_lvl else "SWEEPING"

            boundaries.append(
                PatternBoundaryItem(
                    pattern_name=f"{active_vp.horizon_label} Value Area Low (cVAL)",
                    pattern_type=PatternType.RANGE_SUPPORT_EXTREME,
                    boundary_level=round(val_lvl, 2),
                    sweep_wick_extreme=round(sweep_val, 2),
                    distance_pct=round(dist_val_pct, 2),
                    distance_atr=round(dist_val_atr, 2),
                    status=status_val,
                    trap_bias="BULLISH (BEAR TRAP)",
                    liquidation_tier="INSTITUTIONAL LIQUIDITY SHELF",
                )
            )

            # 70% Value Area High acts as structural range ceiling
            vah_lvl = active_vp.c_vah
            sweep_vah = max(b.high for b in bars_1h[-12:]) if bars_1h else vah_lvl
            dist_vah_pct = ((current_price - vah_lvl) / vah_lvl) * 100.0
            dist_vah_atr = (current_price - vah_lvl) / atr_1h
            status_vah = "COMPRESSION"
            if sweep_vah > vah_lvl:
                status_vah = "SFP REJECTED" if current_price <= vah_lvl else "SWEEPING"

            boundaries.append(
                PatternBoundaryItem(
                    pattern_name=f"{active_vp.horizon_label} Value Area High (cVAH)",
                    pattern_type=PatternType.RANGE_RESISTANCE_EXTREME,
                    boundary_level=round(vah_lvl, 2),
                    sweep_wick_extreme=round(sweep_vah, 2),
                    distance_pct=round(dist_vah_pct, 2),
                    distance_atr=round(dist_vah_atr, 2),
                    status=status_vah,
                    trap_bias="BEARISH (BULL TRAP)",
                    liquidation_tier="INSTITUTIONAL LIQUIDITY CEILING",
                )
            )

        return boundaries

    def evaluate(
        self,
        store: StateStore,
        bars_1h: Sequence[KlineBar],
        bars_15m: Sequence[KlineBar],
        deriv: DerivativesSnapshot,
        flow: FlowSnapshot,
        active_vp: Optional[VolumeProfileResult] = None,
    ) -> Optional[TrapRadarEvaluation]:
        """Runs the 3-State Trap FSM, calculates CVD absorption elasticity, and generates asymmetric SFP trade plans."""
        if not bars_1h:
            return None

        current_price = store.binance_spot_price or bars_1h[-1].close
        atr_1h = max(compute_atr(bars_1h[-30:], period=self.config.atr_period), 1.0)

        # 1. Microstructure CVD & OI Velocity
        rolling_15m_cvd = flow.w_15m.spot_delta_btc
        rolling_5m_cvd = deriv.perp_5m_delta_btc
        rolling_1m_cvd = (store.live_spot_buy_15m - store.live_spot_sell_15m) * 0.25

        oi_15m_pct = deriv.oi_change_15m_pct
        oi_1h_pct = deriv.oi_change_1h_pct
        oi_surge_flag = (oi_15m_pct >= 0.40) or (oi_1h_pct >= 1.00)

        # Measure 15m price displacement
        ref_15m_price = bars_15m[-1].open if bars_15m else current_price
        price_disp_pct = ((current_price - ref_15m_price) / ref_15m_price) * 100.0

        # Absorption elasticity: High CVD with clamped price displacement
        heavy_perp_selling = (deriv.perp_5m_delta_btc <= -15.0) or (rolling_15m_cvd < 0 and flow.w_1h.perp_delta_btc <= -40.0)
        heavy_perp_buying = (deriv.perp_5m_delta_btc >= 15.0) or (rolling_15m_cvd > 0 and flow.w_1h.perp_delta_btc >= 40.0)

        passive_absorption = False
        if heavy_perp_selling and price_disp_pct >= -0.20:
            passive_absorption = True
        elif heavy_perp_buying and price_disp_pct <= 0.20:
            passive_absorption = True

        absorption_ratio = abs(rolling_15m_cvd) / (abs(price_disp_pct) + 0.01)

        # 2. Discover Pattern Boundaries & Session Extremes
        patterns = self._discover_pattern_boundaries(
            bars_1h, current_price, atr_1h, active_vp=active_vp, bars_15m=bars_15m
        )

        asia_h = 0.0
        asia_l = 0.0
        asia_h_sw = False
        asia_l_sw = False
        for p in patterns:
            if p.pattern_type == PatternType.ASIA_SESSION_HIGH:
                asia_h = p.boundary_level
                asia_h_sw = ("REJECTED" in p.status) or ("SWEEPING" in p.status)
            elif p.pattern_type == PatternType.ASIA_SESSION_LOW:
                asia_l = p.boundary_level
                asia_l_sw = ("RECLAIMED" in p.status) or ("SWEEPING" in p.status)

        # 3. Detect 3-Bar Fair Value Gaps (FVG) and 50% Consequent Encroachment (CE)
        fvgs_15m = self._detect_fair_value_gaps(bars_15m[-60:], timeframe="15m", current_price=current_price) if bars_15m else []
        fvgs_1h = self._detect_fair_value_gaps(bars_1h[-40:], timeframe="1H", current_price=current_price)
        all_fvgs = sorted(fvgs_15m + fvgs_1h, key=lambda f: abs(f.distance_pct))

        # Check for nearby bullish FVG CE for optimal pullback limit entry
        bullish_ce_entry = None
        for f in all_fvgs:
            if f.direction == "BULLISH" and f.ce_midpoint <= current_price:
                bullish_ce_entry = f.ce_midpoint
                break

        # Check for overhead bearish FVG target
        overhead_fvg_target = None
        for f in all_fvgs:
            if f.direction == "BEARISH" and f.ce_midpoint > current_price:
                overhead_fvg_target = f.ce_midpoint
                break

        # 4. Evaluate 3-State Trap FSM
        active_state = TrapState.NEUTRAL_OBSERVATION
        trap_signal = "NEUTRAL (Observing Order Flow)"
        trade_plan: Optional[TrapTradePlan] = None

        # Look for active SFP reclaim on support boundaries (Bear Trap)
        bear_trap_boundary: Optional[PatternBoundaryItem] = None
        bull_trap_boundary: Optional[PatternBoundaryItem] = None

        for p in patterns:
            if p.trap_bias == "BULLISH (BEAR TRAP)":
                # Check if recent candle swept below and closed back inside
                swept = p.sweep_wick_extreme < p.boundary_level
                reclaimed = current_price >= p.boundary_level and (current_price - p.boundary_level) <= 1.5 * atr_1h
                if swept and reclaimed:
                    bear_trap_boundary = p
                    break
                elif swept and not reclaimed:
                    active_state = TrapState.STATE_1_BOUNDARY_SWEEP
                    trap_signal = f"SWEEP IN PROGRESS ({p.pattern_name} @ ${p.boundary_level:,.0f})"
                elif abs(p.distance_atr) <= 0.75 and oi_surge_flag:
                    active_state = TrapState.STATE_0_COMPRESSION
                    trap_signal = f"COMPRESSION (Building OI near {p.pattern_name})"

            elif p.trap_bias == "BEARISH (BULL TRAP)":
                swept = p.sweep_wick_extreme > p.boundary_level
                rejected = current_price <= p.boundary_level and (p.boundary_level - current_price) <= 1.5 * atr_1h
                if swept and rejected:
                    bull_trap_boundary = p
                    break

        # 5. Resolve Trigger & Construct Asymmetric Trade Plan
        poc_target = active_vp.c_poc if active_vp else (current_price + 2.0 * atr_1h)
        vah_target = active_vp.c_vah if active_vp else (current_price + 4.0 * atr_1h)

        if bear_trap_boundary is not None and (passive_absorption or flow.w_1h.spot_delta_btc >= 0):
            active_state = TrapState.STATE_2_SFP_RECLAIM_TRIGGERED
            trap_signal = f"🚨 BEAR TRAP CONFIRMED: SFP Reclaim on {bear_trap_boundary.pattern_name} (${bear_trap_boundary.boundary_level:,.0f})"
            sl_price = bear_trap_boundary.sweep_wick_extreme - 0.25 * atr_1h
            risk = max(current_price - sl_price, 10.0)
            reward_poc = max(poc_target - current_price, 10.0)
            rr = reward_poc / risk

            fvg_entry_note = f" Optimal 50% CE Limit Entry: ${bullish_ce_entry:,.1f}." if bullish_ce_entry else ""
            fvg_target_note = f" Overhead FVG Target: ${overhead_fvg_target:,.1f}." if overhead_fvg_target else ""

            trade_plan = TrapTradePlan(
                direction="LONG (BEAR TRAP SQUEEZE)",
                entry_price=round(current_price, 2),
                stop_loss=round(sl_price, 2),
                tp1_poc=round(poc_target, 2),
                tp2_opposite_boundary=round(vah_target, 2),
                risk_dollars=round(risk, 2),
                reward_dollars=round(reward_poc, 2),
                rr_ratio=round(rr, 2),
                invalidation_summary=f"Strict invalidation if 15m candle closes below sweep wick extreme (${sl_price:,.0f}).{fvg_entry_note}{fvg_target_note}",
            )
            summary = (
                f"Bear Trap confirmed! Price swept textbook support ({bear_trap_boundary.pattern_name} @ ${bear_trap_boundary.boundary_level:,.0f}) "
                f"to flush stops down to ${bear_trap_boundary.sweep_wick_extreme:,.0f}, but passive spot limit bids absorbed the move. "
                f"Price has reclaimed support. Target TP1 cPOC (${poc_target:,.0f}) with R:R of {rr:.2f}R.{fvg_entry_note}"
            )
            takeaway = "ACCUMULATE SPOT LONG — Trap late breakout shorts with tight stop below sweep wick."

        elif bull_trap_boundary is not None and (passive_absorption or flow.w_1h.spot_delta_btc <= 0):
            active_state = TrapState.STATE_2_SFP_RECLAIM_TRIGGERED
            trap_signal = f"⚠️ BULL TRAP CONFIRMED: Rejection on {bull_trap_boundary.pattern_name} (${bull_trap_boundary.boundary_level:,.0f})"
            val_target = active_vp.c_val if active_vp else (current_price - 2.0 * atr_1h)
            sl_price = bull_trap_boundary.sweep_wick_extreme + 0.25 * atr_1h
            risk = max(sl_price - current_price, 10.0)
            reward = max(current_price - val_target, 10.0)
            rr = reward / risk

            trade_plan = TrapTradePlan(
                direction="USDT HEDGE (BULL TRAP)",
                entry_price=round(current_price, 2),
                stop_loss=round(sl_price, 2),
                tp1_poc=round(poc_target, 2),
                tp2_opposite_boundary=round(val_target, 2),
                risk_dollars=round(risk, 2),
                reward_dollars=round(reward, 2),
                rr_ratio=round(rr, 2),
                invalidation_summary=f"Invalidated if price reclaims and expands above sweep peak (${sl_price:,.0f}).",
            )
            summary = (
                f"Bull Trap confirmed! Breakout above {bull_trap_boundary.pattern_name} (${bull_trap_boundary.boundary_level:,.0f}) "
                "was met with passive institutional selling into aggressive perp buyers. Stand aside in USDT or take profits."
            )
            takeaway = "MAINTAIN CASH / HEDGE SPOT — Do not chase textbook breakout longs."

        elif active_state == TrapState.STATE_1_BOUNDARY_SWEEP:
            summary = "Price is currently sweeping beyond a classical pattern boundary. Do not front-run; wait for 15m candle close back inside to confirm SFP reclaim."
            takeaway = "OBSERVE SWEEP WICK EXTREME — Armed for SFP reclaim trigger."
        elif active_state == TrapState.STATE_0_COMPRESSION:
            summary = "Open interest is building as price compresses into pattern boundaries. High probability of an imminent liquidity run."
            takeaway = "PREPARE LIMIT TRANCHES — Await liquidity sweep."
        else:
            summary = "Order flow and pattern boundaries are in balanced churn. No active liquidity traps detected."
            takeaway = "NEUTRAL OBSERVATION — Respect structural Volume Profile boundaries."

        evaluation = TrapRadarEvaluation(
            timestamp_utc=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            spot_price=round(current_price, 2),
            active_trap_state=active_state,
            active_trap_signal=trap_signal,
            rolling_1m_cvd=round(rolling_1m_cvd, 2),
            rolling_5m_cvd=round(rolling_5m_cvd, 2),
            rolling_15m_cvd=round(rolling_15m_cvd, 2),
            oi_15m_delta_pct=round(oi_15m_pct, 3),
            oi_1h_delta_pct=round(oi_1h_pct, 3),
            oi_surge_flag=oi_surge_flag,
            passive_absorption_flag=passive_absorption,
            absorption_divergence_ratio=round(absorption_ratio, 2),
            active_patterns=patterns,
            active_fvgs=all_fvgs,
            asia_high=round(asia_h, 2),
            asia_low=round(asia_l, 2),
            asia_high_swept=asia_h_sw,
            asia_low_swept=asia_l_sw,
            trade_plan=trade_plan,
            plain_english_summary=summary,
            quantitative_takeaway=takeaway,
        )

        store.trap_evaluation = evaluation
        return evaluation
