"""Structure + Level Swing Protocol (SLSP v1.0) & 4-in-1 Integration Engine.

Implements the institutional swing trading system defined in File A (SLSP v1.0)
and integrates:
- File B: Industrial 3-EMA Strategy (Daily 200 EMA slope anchor, 4H value zone, ADX)
- Project 7: Tell-Tale Engine (Volume Capitulation Climax Sensor & Anti-Knife Guard)
- Project 8: BTC Liquidation Flush Detector (4H Liquidation Sweep & OI Purge Sensor)

Core Rules:
1. Daily Regime: UPTREND (HH/HL), DOWNTREND (LH/LL), or RANGE (>=10 daily bars).
2. Key Level Identification: Visible on Daily chart, >=2 touches, scored 1-5 stars.
3. 4H Candlestick Rejection: Pinbar (>=50% wick) or Engulfing with Volume > 20 SMA.
4. Runway Obstacle Check: No major opposing resistance within 1.5R.
5. 3-EMA Confluence: Daily 200 EMA slope >= -0.05%, in 4H 21-50 EMA value band.
6. Tell-Tale Climax Veto: Vetoes long entries if an active 5x volume dump is occurring.
7. Liquidation Flush Boost: Boosts confluence when 4H liquidation flush wicks sweep stops.
8. Trade Execution & Sizing: Fixed 0.75% risk (max 1.0%), TP1 at 1.5R (50%), TP2 at 2.5R,
   auto-ratchet stop to Breakeven (+0.1% fees) at +1.0R.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import List, Optional, Sequence, Tuple

import numpy as np

from config.settings import EngineConfig
from core.models import (
    KlineBar,
    SLSPEvaluation,
    SLSPKeyLevel,
    SLSPTradeSetup,
    VolumeProfileResult,
)
from analytics.btc_magnet_engine import BTCMagnetEngine
from core.state_store import StateStore
from .liquidation_reader import read_latest_liquidation_report
from .slsp_trade_manager import SLSPTradeManager
from .volume_profile import compute_atr

logger = logging.getLogger(__name__)


class SLSPEngine:
    """Evaluates Tab [13]: Structure + Level Swing Protocol (SLSP v1.0) & 4-in-1 System."""

    def __init__(self, config: Optional[EngineConfig] = None, read_only: bool = True) -> None:
        self.config = config or EngineConfig()
        self.read_only = read_only

        self.risk_pct = getattr(self.config, "slsp_risk_pct", 0.75)
        self.min_rr = getattr(self.config, "slsp_min_rr", 1.50)
        self.min_level_strength = getattr(self.config, "slsp_min_level_strength", 3)
        self.max_daily_loss_pct = getattr(self.config, "slsp_max_daily_loss_pct", 2.0)
        self.max_weekly_loss_pct = getattr(self.config, "slsp_max_weekly_loss_pct", 4.0)
        self.mode = getattr(self.config, "slsp_mode", "SEMI_AUTO")

        state_path = getattr(self.config, "slsp_state_path", None)
        self.trade_manager = SLSPTradeManager(
            state_path=state_path,
            account_equity=100_000.0,
            risk_pct=self.risk_pct,
            max_daily_loss_pct=self.max_daily_loss_pct,
            max_weekly_loss_pct=self.max_weekly_loss_pct,
        )

    def detect_daily_regime(
        self, bars_1d: Sequence[KlineBar], current_price: float
    ) -> Tuple[str, str, float, float]:
        """Classifies Daily market structure as UPTREND, DOWNTREND, or RANGE (SLSP Section 3).

        - Uptrend: Price makes higher highs and higher lows. Last swing low is intact.
        - Downtrend: Price makes lower highs and lower lows. Last swing high is intact.
        - Range: Contained between two clear horizontal levels for >= 10 daily candles.
        """
        if len(bars_1d) < 10:
            return "UNCLEAR", "Insufficient daily candles (< 10 bars)", 0.0, 0.0

        highs = [b.high for b in bars_1d]
        lows = [b.low for b in bars_1d]
        n = len(bars_1d)

        # Detect swing pivots (left=2, right=1)
        swing_highs: List[Tuple[int, float]] = []
        swing_lows: List[Tuple[int, float]] = []

        for i in range(1, n - 1):
            if highs[i] > highs[i - 1] and highs[i] >= highs[i + 1]:
                swing_highs.append((i, highs[i]))
            if lows[i] < lows[i - 1] and lows[i] <= lows[i + 1]:
                swing_lows.append((i, lows[i]))

        if len(swing_highs) < 2 or len(swing_lows) < 2:
            # Fallback based on 10-bar range containment
            recent_10_high = max(highs[-10:])
            recent_10_low = min(lows[-10:])
            range_pct = (recent_10_high - recent_10_low) / max(recent_10_low, 1.0) * 100.0
            if range_pct <= 12.0:
                return (
                    "RANGE",
                    f"Consolidation range: ${recent_10_low:,.0f} - ${recent_10_high:,.0f} ({range_pct:.1f}% span over 10 days)",
                    recent_10_high,
                    recent_10_low,
                )
            return "UNCLEAR", "Developing market structure, pivots establishing", 0.0, 0.0

        prev_sh, last_sh = swing_highs[-2][1], swing_highs[-1][1]
        prev_sl, last_sl = swing_lows[-2][1], swing_lows[-1][1]

        # Check Uptrend: HH + HL and last swing low intact
        is_higher_high = last_sh > prev_sh
        is_higher_low = last_sl > prev_sl
        last_low_intact = current_price >= last_sl

        if is_higher_high and is_higher_low and last_low_intact:
            reason = f"Higher Highs (${last_sh:,.0f} > ${prev_sh:,.0f}) & Higher Lows (${last_sl:,.0f} > ${prev_sl:,.0f}); Swing Low Intact"
            return "UPTREND", reason, last_sh, last_sl

        # Check Downtrend: LH + LL and last swing high intact
        is_lower_high = last_sh < prev_sh
        is_lower_low = last_sl < prev_sl
        last_high_intact = current_price <= last_sh

        if is_lower_high and is_lower_low and last_high_intact:
            reason = f"Lower Highs (${last_sh:,.0f} < ${prev_sh:,.0f}) & Lower Lows (${last_sl:,.0f} < ${prev_sl:,.0f}); Swing High Intact"
            return "DOWNTREND", reason, last_sh, last_sl

        # Range structure: price contained within bounds for >= 10 daily candles
        recent_10_high = max(highs[-10:])
        recent_10_low = min(lows[-10:])
        range_span = (recent_10_high - recent_10_low) / max(recent_10_low, 1.0) * 100.0
        if range_span <= 15.0:
            return (
                "RANGE",
                f"Range bound between ${recent_10_low:,.0f} and ${recent_10_high:,.0f} (>= 10 daily candles)",
                recent_10_high,
                recent_10_low,
            )

        return "UNCLEAR", "Transitional or mixed swing structure", last_sh, last_sl

    def detect_key_levels(
        self,
        bars_1d: Sequence[KlineBar],
        current_price: float,
        active_vp: Optional[VolumeProfileResult] = None,
    ) -> List[SLSPKeyLevel]:
        """Automatically identifies and scores key Daily horizontal levels 1-5 (SLSP Section 4).

        Scoring Rules:
        1. Visible on Daily chart.
        2. Respected >= 2 times (touch count >= 2).
        3. Priority & Strength (1-5):
           - Major previous swing high/low (+1 or +2)
           - Multiple daily touches (+1 if >= 2 touches, +2 if >= 3 touches)
           - Round numbers ($5,000 / $10,000 multiples) (+1)
           - High-Volume Node (HVN) confluence (+1)
        """
        if len(bars_1d) < 5:
            return []

        # 1. Harvest candidate level points from daily swing pivots and candle extremes
        candidates: List[float] = []
        n = len(bars_1d)
        for i in range(1, n - 1):
            cur = bars_1d[i]
            prev = bars_1d[i - 1]
            nxt = bars_1d[i + 1]
            if cur.high >= prev.high and cur.high >= nxt.high:
                candidates.append(cur.high)
            if cur.low <= prev.low and cur.low <= nxt.low:
                candidates.append(cur.low)

        # Add major round numbers in the vicinity of current price
        base_round = round(current_price / 5000.0) * 5000.0
        for offset in (-15000.0, -10000.0, -5000.0, 0.0, 5000.0, 10000.0, 15000.0):
            r_num = base_round + offset
            if r_num > 0:
                candidates.append(r_num)

        # Add HVN / POC from volume profile if present
        if active_vp:
            if getattr(active_vp, 'c_poc', getattr(active_vp, 'poc', 0.0)) > 0:
                candidates.append(getattr(active_vp, 'c_poc', getattr(active_vp, 'poc', 0.0)))
            if active_vp.c_val > 0:
                candidates.append(active_vp.c_val)
            if active_vp.c_vah > 0:
                candidates.append(active_vp.c_vah)

        # 2. Cluster candidates within a 1.0% tolerance band
        clusters: List[List[float]] = []
        tolerance = 0.010  # 1.0% band

        for p in sorted(candidates):
            added = False
            for c in clusters:
                avg_c = sum(c) / len(c)
                if abs(p - avg_c) / avg_c <= tolerance:
                    c.append(p)
                    added = True
                    break
            if not added:
                clusters.append([p])

        levels: List[SLSPKeyLevel] = []
        for c in clusters:
            center = float(np.mean(c))
            p_min = float(min(c))
            p_max = float(max(c))

            # Count daily candle touches (high/low within 0.8% of center)
            touches = 0
            for b in bars_1d:
                if (b.low <= center * 1.008) and (b.high >= center * 0.992):
                    touches += 1

            if touches < 2:
                continue  # SLSP Rule: Must be respected at least twice

            # Determine round number confluence ($5k / $10k multiples)
            is_round = False
            dist_to_round = abs(center - round(center / 5000.0) * 5000.0) / center
            if dist_to_round <= 0.006:
                is_round = True

            # Determine HVN confluence
            is_hvn = False
            if active_vp:
                for hvn in [getattr(active_vp, 'c_poc', getattr(active_vp, 'poc', 0.0)), active_vp.c_val, active_vp.c_vah]:
                    if hvn > 0 and abs(center - hvn) / center <= 0.008:
                        is_hvn = True
                        break

            # Calculate strength score (1 to 5)
            score = 1
            if touches >= 3:
                score += 2
            elif touches >= 2:
                score += 1

            if is_round:
                score += 1
            if is_hvn:
                score += 1

            strength = min(5, max(1, score))

            level_type = "SUPPORT" if center <= current_price else "RESISTANCE"
            desc_parts = [f"{touches}x Daily Touches"]
            if is_round:
                desc_parts.append(f"Round Number (~${round(center/1000)*1000:,.0f})")
            if is_hvn:
                desc_parts.append("Volume Profile Node")

            levels.append(
                SLSPKeyLevel(
                    price_min=round(p_min, 2),
                    price_max=round(p_max, 2),
                    center_price=round(center, 2),
                    level_type=level_type,
                    strength=strength,
                    touch_count=touches,
                    is_round_number=is_round,
                    is_hvn=is_hvn,
                    is_swing_pivot=True,
                    description=" • ".join(desc_parts),
                )
            )

        # Sort: Supports descending by center price, Resistances ascending by center price
        supports = sorted(
            [lv for lv in levels if lv.level_type == "SUPPORT"],
            key=lambda x: x.center_price,
            reverse=True,
        )
        resistances = sorted(
            [lv for lv in levels if lv.level_type == "RESISTANCE"],
            key=lambda x: x.center_price,
        )

        return supports + resistances

    def evaluate_4h_rejection(
        self, bars_4h: Sequence[KlineBar]
    ) -> Tuple[bool, str, float, float]:
        """Evaluates whether the latest closed 4H candle exhibits valid rejection & volume (SLSP Section 5).

        Conditions:
        1. 4H candle shows rejection (long lower wick >= 50% or bullish engulfing for longs).
        2. Volume on the rejection candle is strictly above the 20-period average.
        """
        if len(bars_4h) < 22:
            return False, "NONE", 0.0, 0.0

        # Evaluate the last 2 completed bars
        cur = bars_4h[-1]
        prev = bars_4h[-2]

        baseline_bars = bars_4h[-21:-1]
        base_vol = float(np.mean([b.volume for b in baseline_bars])) if baseline_bars else 1.0
        vol_ratio = round(cur.volume / base_vol, 2) if base_vol > 0 else 0.0
        volume_confirmed = vol_ratio >= 1.0  # SLSP Rule: Volume above 20-period average

        rng = cur.high - cur.low
        if rng <= 0:
            return False, "NONE", 0.0, vol_ratio

        lower_wick = min(cur.open, cur.close) - cur.low
        lower_wick_ratio = round(lower_wick / rng, 3)

        upper_wick = cur.high - max(cur.open, cur.close)
        upper_wick_ratio = round(upper_wick / rng, 3)

        # Bullish Rejection Checks:
        # A) Bullish Pinbar: lower wick >= 50% of candle range
        is_pinbar = lower_wick_ratio >= 0.50
        # B) Bullish Engulfing: green candle whose body engulfs previous red candle
        is_engulfing = (
            cur.close > cur.open
            and prev.close < prev.open
            and cur.open <= prev.close
            and cur.close >= prev.open
        )

        if is_pinbar and volume_confirmed:
            return True, "PINBAR", lower_wick_ratio, vol_ratio
        if is_engulfing and volume_confirmed:
            return True, "ENGULFING", lower_wick_ratio, vol_ratio
        if is_pinbar and not volume_confirmed:
            return False, "PINBAR_LOW_VOL", lower_wick_ratio, vol_ratio

        return False, "NONE", lower_wick_ratio, vol_ratio

    def check_obstacle_clearance(
        self,
        entry_price: float,
        stop_price: float,
        resistances: List[SLSPKeyLevel],
    ) -> Tuple[bool, float, str]:
        """Verifies no major resistance (strength >= 3) sits within 1.5R of the entry (SLSP Section 5)."""
        risk_per_coin = entry_price - stop_price
        if risk_per_coin <= 0:
            return False, 0.0, "Invalid risk geometry (Stop >= Entry)"

        hurdle_price = entry_price + (1.50 * risk_per_coin)

        for r_lvl in resistances:
            if r_lvl.strength >= self.min_level_strength:
                if entry_price < r_lvl.center_price <= hurdle_price:
                    dist_r = (r_lvl.center_price - entry_price) / risk_per_coin
                    return (
                        False,
                        dist_r,
                        f"OBSTACLE VETO: {r_lvl.strength}-Star Resistance at ${r_lvl.center_price:,.2f} within 1.5R ({dist_r:.2f}R)",
                    )

        # Measure clearance to nearest resistance
        nearest_r = resistances[0] if resistances else None
        if nearest_r:
            clearance_r = (nearest_r.center_price - entry_price) / risk_per_coin
            return (
                True,
                clearance_r,
                f"RUNWAY CLEAR: Nearest major resistance at ${nearest_r.center_price:,.2f} ({clearance_r:.2f}R > 1.5R)",
            )

        return True, 999.0, "RUNWAY CLEAR: No major opposing resistance mapped"

    def evaluate(
        self,
        store: StateStore,
        spot_1d: Optional[Sequence[KlineBar]] = None,
        bars_4h: Optional[Sequence[KlineBar]] = None,
        current_price: float = 0.0,
        active_vp: Optional[VolumeProfileResult] = None,
    ) -> SLSPEvaluation:
        if spot_1d is None:
            spot_1d = getattr(store, "spot_klines_1d", []) or []
        if bars_4h is None:
            bars_4h = getattr(store, "spot_klines_4h", []) or []
        if current_price <= 0.0:
            current_price = float(getattr(store, "binance_spot_price", 0.0) or (spot_1d[-1].close if spot_1d else 0.0))
        """Executes full SLSP v1.0 evaluation and synthesizes all 4 components into Tab [13]."""
        now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        # Integrated Tab M Microstructure & Liquidation Gravity
        mag_eval = getattr(store, "btc_magnet_evaluation", None)
        if mag_eval is None:
            try:
                mag_eval = BTCMagnetEngine(self.config).evaluate(store)
            except Exception:
                mag_eval = None

        macro_reg_id = getattr(mag_eval, "regime_id", "RANGE_LIQUIDATION_MAGNET") if mag_eval else "RANGE_LIQUIDATION_MAGNET"
        macro_reg_name = getattr(mag_eval, "regime_name", "Range / Liquidation Magnet") if mag_eval else "Range / Liquidation Magnet"
        macro_score = getattr(mag_eval, "majority_score", "4/4") if mag_eval else "4/4"
        macro_diag = getattr(mag_eval, "regime_diagnosis", "Positioning imbalance and forced liquidations dominate") if mag_eval else ""
        macro_sizing = getattr(mag_eval, "sizing_factor", 0.50) if mag_eval else 0.50
        macro_rotation = getattr(mag_eval, "rotation", "Remain USDT") if mag_eval else "Remain USDT"
        lsce_stat = getattr(mag_eval, "lsce_status", "UNTESTED") if mag_eval else "UNTESTED"
        lsce_cluster = getattr(mag_eval, "lsce_cluster_tested", "N/A") if mag_eval else "N/A"
        lsce_verdict = getattr(mag_eval, "lsce_action_verdict", "Wait for sweep confirmation") if mag_eval else ""
        u_mag_p = getattr(getattr(mag_eval, "upper_magnet", None), "price", 0.0)
        u_mag_dist = getattr(getattr(mag_eval, "upper_magnet", None), "dist_pct", 0.0)
        u_mag_vol = getattr(getattr(mag_eval, "upper_magnet", None), "usd_volume", 0.0)
        l_mag_p = getattr(getattr(mag_eval, "lower_magnet", None), "price", 0.0)
        l_mag_dist = getattr(getattr(mag_eval, "lower_magnet", None), "dist_pct", 0.0)
        l_mag_vol = getattr(getattr(mag_eval, "lower_magnet", None), "usd_volume", 0.0)
        pull_dir = getattr(mag_eval, "pull_direction", "NEUTRAL") if mag_eval else "NEUTRAL"
        imm_ratio = getattr(mag_eval, "immediate_ratio", 1.0) if mag_eval else 1.0
        tot_ratio = getattr(mag_eval, "total_ladder_ratio", 1.0) if mag_eval else 1.0
        s_stop = getattr(mag_eval, "structural_stop_price", 0.0) if mag_eval else 0.0
        s_dist = getattr(mag_eval, "structural_stop_dist_pct", 0.0) if mag_eval else 0.0
        d_stop = getattr(mag_eval, "disaster_stop_price", 0.0) if mag_eval else 0.0
        d_dist = getattr(mag_eval, "disaster_stop_dist_pct", 0.0) if mag_eval else 0.0

        # 1. Component 1: Daily Market Structure & Horizontal Key Levels
        regime, reg_reason, last_sh, last_sl = self.detect_daily_regime(spot_1d, current_price)
        all_levels = self.detect_key_levels(spot_1d, current_price, active_vp)

        # Cross-reference Key Shelves with Liquidation Clusters (Type-Aligned)
        for lv in all_levels:
            if lv.level_type == "SUPPORT" and l_mag_p > 0:
                in_band = (lv.price_min <= l_mag_p <= lv.price_max)
                near_center = (abs(lv.center_price - l_mag_p) / l_mag_p <= 0.015)
                if in_band or near_center:
                    lv.liquidation_volume_usd = l_mag_vol
                    lv.liquidation_cluster_tag = f"Lower Long Pool (${l_mag_vol/1e6:.1f}M • {l_mag_dist:+.1f}%)"
                    lv.strength = min(5, lv.strength + 1)
            elif lv.level_type == "RESISTANCE" and u_mag_p > 0:
                in_band = (lv.price_min <= u_mag_p <= lv.price_max)
                near_center = (abs(lv.center_price - u_mag_p) / u_mag_p <= 0.015)
                if in_band or near_center:
                    lv.liquidation_volume_usd = u_mag_vol
                    lv.liquidation_cluster_tag = f"Upper Short Magnet (${u_mag_vol/1e6:.1f}M • {u_mag_dist:+.1f}%)"
                    lv.strength = min(5, lv.strength + 1)
        supports = [lv for lv in all_levels if lv.level_type == "SUPPORT"]
        resistances = [lv for lv in all_levels if lv.level_type == "RESISTANCE"]

        nearest_supp = supports[0] if supports else None
        nearest_res = resistances[0] if resistances else None

        # 2. Component 2: Industrial 3-EMA Telemetry
        ema_snap = store.ema_strategy
        ema_3_reg = ema_snap.daily_regime if ema_snap else "NEUTRAL"
        ema_3_slope = ema_snap.daily_ema_200_slope if ema_snap else 0.0
        ema_3_vz = ema_snap.pullback_zone_active if ema_snap else False
        ema_3_adx = ema_snap.daily_adx if ema_snap else 0.0
        ema_3_pos_met = ema_snap.positioning_confirmations_met if ema_snap else 0
        ema_3_trigger = ema_snap.trigger_active if ema_snap else False

        # 3. Component 3: Tell-Tale Climax Sensor (Anti-Knife Guard)
        tt_eval = (
            store.exhaustion_evaluation.tell_tale
            if (store.exhaustion_evaluation and store.exhaustion_evaluation.tell_tale)
            else None
        )
        tt_status = tt_eval.plain_status if tt_eval else "NORMAL ORDER FLOW"
        tt_veto = tt_eval.is_selling_climax if tt_eval else False
        tt_relvol_15m = tt_eval.bar_15m.relvol if (tt_eval and tt_eval.bar_15m) else 0.0
        tt_relvol_5m = tt_eval.bar_5m.relvol if (tt_eval and tt_eval.bar_5m) else 0.0

        # 4. Component 4: Liquidation Flush Detector (Smart Money Sweep Confirmation)
        trap_eval = store.trap_evaluation
        liq_report = read_latest_liquidation_report()
        store.liquidation_report = liq_report

        liq_detected = False
        liq_wick_ratio = 0.0
        liq_oi_delta = 0.0
        liq_status = "STANDBY"

        if liq_report and liq_report.is_available:
            liq_status = f"{liq_report.verdict} ({liq_report.primary_classification})"
            if liq_report.primary_classification in (
                "LONG_SQUEEZE_EXHAUSTION",
                "POST_FLUSH_REVERSAL",
                "LIQUIDATION_FLUSH",
            ):
                liq_detected = True

        if trap_eval:
            if trap_eval.asia_low_swept:
                liq_detected = True
                liq_status = "ASIA LOW SWEPT & RECLAIMED"
            liq_oi_delta = trap_eval.oi_1h_delta_pct

        # 5. Check 4H Rejection & Volume on Bar Close
        rejection_confirmed, rej_type, wick_ratio, vol_ratio = self.evaluate_4h_rejection(bars_4h)

        # 6. Check Circuit Breaker Status
        cb_active, cb_reason = self.trade_manager.is_circuit_breaker_active()
        daily_loss_pct = (
            self.trade_manager.daily_realized_loss_usd
            / max(self.trade_manager.account_equity, 1.0)
        ) * 100.0
        weekly_loss_pct = (
            self.trade_manager.weekly_realized_loss_usd
            / max(self.trade_manager.account_equity, 1.0)
        ) * 100.0

        # 7. Evaluate Trade Setup Confluence
        confluence_score = 0
        decision_log: List[str] = []
        trade_state = "SCANNING"

        # Check Support Proximity (within 0.5% of valid support zone)
        in_support_pocket = False
        if nearest_supp:
            dist_to_supp_pct = (current_price - nearest_supp.center_price) / nearest_supp.center_price * 100.0
            if -0.50 <= dist_to_supp_pct <= 0.75:
                in_support_pocket = True
                confluence_score += 25
                decision_log.append(f"At Key Support: ${nearest_supp.center_price:,.0f} ({nearest_supp.strength} Stars)")

        # Check Daily Structure & 200 EMA Slope Shield
        if regime in ("UPTREND", "RANGE"):
            confluence_score += 20
            decision_log.append(f"Daily Structure: {regime} ({reg_reason})")
        if ema_3_slope >= -0.05:
            confluence_score += 10
            decision_log.append(f"Daily 200 EMA Slope Shield Active: {ema_3_slope:+.2f}%")

        # Check 4H Dynamic Value Zone
        if ema_3_vz:
            confluence_score += 15
            decision_log.append("Price Inside 4H 21-50 EMA Dynamic Value Zone")

        # Check Pre-Flight Sensors:
        # A) Tell-Tale Veto Check
        if tt_veto:
            decision_log.append("[ALERT] HARD VETO: 5x Tell-Tale Selling Climax Active (Anti-Knife Guard Engaged)")
            trade_state = "STAND_ASIDE"
        else:
            confluence_score += 10

        # B) Liquidation Flush Confluence
        if liq_detected:
            confluence_score += 15
            decision_log.append(f"Liquidation Flush Confirmed: {liq_status}")

        # Check 4H Rejection & 9 EMA Trigger
        if rejection_confirmed:
            confluence_score += 10
            decision_log.append(f"4H Rejection Confirmed: {rej_type} (Wick: {wick_ratio*100:.1f}%, Vol: {vol_ratio:.1f}x)")

        # Integrated Tab M Macro Positioning & LSCE Checks
        macro_hard_lock = False
        macro_lock_reason = ""
        recon_eval = getattr(store, "reconciliation_evaluation", None)
        recon_auth = getattr(recon_eval, "execution_authorization", "") if recon_eval else getattr(mag_eval, "reconciliation_auth", "AUTHORIZED")
        if recon_auth == "DENIED":
            macro_hard_lock = True
            fail_reasons = getattr(recon_eval, "fail_reasons", []) if recon_eval else getattr(mag_eval, "reconciliation_fail_reasons", [])
            fail_msg = fail_reasons[0] if fail_reasons else "Critical data integrity discrepancy"
            macro_lock_reason = f"RECONCILIATION GATE FAIL-CLOSED LOCKOUT: {fail_msg}"
            trade_state = "STAND_ASIDE"
            decision_log.append(f"[FAIL-CLOSED LOCKOUT (100% USDT)]: {macro_lock_reason}")
        elif macro_reg_id in ("CASCADE_FORCED_DELEVERAGING", "LEVERAGED_FRAGILE_UPSIDE", "DISTRIBUTION_BEAR_CONTINUATION") or getattr(mag_eval, "is_conflicted", False):
            macro_hard_lock = True
            macro_lock_reason = f"Macro Regime ({macro_reg_name}) commands 100% Cash. No knife-catching allowed."
            trade_state = "STAND_ASIDE"
            decision_log.append(f"[ALERT] MACRO HARD-LOCK (100% CASH): {macro_lock_reason}")
        elif lsce_stat == "SWEEP_IN_PROGRESS":
            macro_hard_lock = True
            macro_lock_reason = f"Active liquidation sweep in progress at {lsce_cluster}. Wait for absorption."
            trade_state = "STAND_ASIDE"
            decision_log.append(f"[ALERT] MACRO VETO: {macro_lock_reason}")
        elif lsce_stat == "SWEEP_AND_RECLAIM_CONFIRMED":
            confluence_score = min(100, confluence_score + 20)
            decision_log.append("LSCE Confirmed: Lower liquidity shelf swept and reclaimed with positive spot absorption (+20 pts)!")

        # 8. Construct Candidate Trade Setup
        active_setup: Optional[SLSPTradeSetup] = None
        if nearest_supp:
            # Stop loss: below support zone center or swing low, clamped with ATR buffer
            atr_4h = max(compute_atr(bars_4h[-30:], period=14), 100.0)
            stop_candidate = min(nearest_supp.price_min - (0.10 * atr_4h), current_price - (0.50 * atr_4h))
            stop_loss = round(stop_candidate, 2)
            risk_per_coin = current_price - stop_loss

            if risk_per_coin > 0:
                # Obstacle Clearance Check (1.5R Rule)
                runway_ok, clear_r, obstacle_msg = self.check_obstacle_clearance(
                    current_price, stop_loss, resistances
                )
                decision_log.append(obstacle_msg)

                # Sizing Arithmetic
                risk_usd, size_btc, notional_usd = self.trade_manager.calculate_sizing(
                    current_price, stop_loss, risk_pct_override=self.risk_pct
                )

                tp1_price = round(current_price + (1.50 * risk_per_coin), 2)
                tp2_price = round(current_price + (2.50 * risk_per_coin), 2)
                be_trigger = round(current_price + (1.00 * risk_per_coin), 2)

                # Valid setup conditions (SLSP Section 5):
                # 1. Regime is UPTREND or RANGE
                # 2. Price is at or very near valid support level (in_support_pocket)
                # 3. 4H rejection candle confirmed (or 3-EMA trigger)
                # 4. Volume > 20-period average
                # 5. No major resistance within 1.5R
                # 6. No Tell-Tale selling climax veto
                # 7. No Circuit Breaker active
                is_valid = (
                    regime in ("UPTREND", "RANGE")
                    and in_support_pocket
                    and (rejection_confirmed or ema_3_trigger)
                    and runway_ok
                    and not tt_veto
                    and not cb_active
                    and nearest_supp.strength >= self.min_level_strength
                )

                effective_size_btc = round(size_btc * macro_sizing, 4)
                effective_notional_usd = round(notional_usd * macro_sizing, 2)
                effective_is_valid = is_valid and not macro_hard_lock and (macro_sizing > 0.0)

                active_setup = SLSPTradeSetup(
                    is_valid=effective_is_valid,
                    direction="LONG" if not macro_hard_lock else "STAND_ASIDE",
                    regime=regime,
                    level=nearest_supp,
                    entry_price=round(current_price, 2),
                    stop_loss=stop_loss,
                    risk_per_coin=round(risk_per_coin, 2),
                    risk_pct=self.risk_pct,
                    position_size_btc=effective_size_btc,
                    notional_value_usd=effective_notional_usd,
                    tp1_price=tp1_price,
                    tp2_price=tp2_price,
                    breakeven_trigger_price=be_trigger,
                    breakeven_active=False,
                    obstacle_detected=not runway_ok,
                    obstacle_r=round(clear_r, 2),
                    obstacle_description=obstacle_msg,
                    rejection_candle_type=rej_type,
                    rejection_wick_ratio=wick_ratio,
                    rejection_volume_ratio=vol_ratio,
                    confluence_notes=decision_log,
                    disaster_stop=d_stop,
                    macro_sizing_factor=macro_sizing,
                )

        # 9. Update Active Trade State via Trade Manager
        last_4h_close = bars_4h[-1].close if bars_4h else None
        live_trade = self.trade_manager.update_tick(
            current_price=current_price,
            last_4h_close=last_4h_close,
            daily_regime=regime,
        )

        if live_trade and live_trade.state in ("OPEN", "TP1_HARVESTED"):
            trade_state = "IN_POSITION"
        elif cb_active:
            trade_state = "CIRCUIT_BREAKER_LOCKOUT"
        elif tt_veto or macro_hard_lock:
            trade_state = "STAND_ASIDE"
        elif active_setup and active_setup.is_valid:
            trade_state = "TRIGGER_FIRED"
        elif in_support_pocket and ema_3_vz:
            trade_state = "VALUE_ZONE_WATCH"
        elif in_support_pocket:
            trade_state = "REJECTION_ARMED"
        else:
            trade_state = "SCANNING"

        # 10. Construct Plain English Executive Summary
        if trade_state == "IN_POSITION" and live_trade:
            summary = (
                f"ACTIVE POSITION: {live_trade.direction} {live_trade.remaining_size_btc:.4f} BTC @ ${live_trade.entry_price:,.2f} "
                f"| SL: ${live_trade.current_stop:,.2f} | TP1: ${live_trade.tp1_price:,.2f} | TP2: ${live_trade.tp2_price:,.2f} "
                f"| Unrealized: ${live_trade.unrealized_pnl_usd:+,.2f} ({live_trade.state})"
            )
        elif trade_state == "TRIGGER_FIRED" and active_setup:
            summary = (
                f"🚀 SLSP SWING BUY TRIGGER FIRED @ ${current_price:,.2f} | Support: ${nearest_supp.center_price:,.2f} ({nearest_supp.strength}★) "
                f"| Stop: ${active_setup.stop_loss:,.2f} | TP1 (+1.5R): ${active_setup.tp1_price:,.2f} | TP2 (+2.5R): ${active_setup.tp2_price:,.2f} "
                f"| Size: {active_setup.position_size_btc:.4f} BTC (${active_setup.notional_value_usd:,.0f}) | Confluence: {confluence_score}/100"
            )
        elif trade_state == "STAND_ASIDE":
            if macro_hard_lock:
                summary = f"STAND ASIDE: Macro Hard-Lock Active ({macro_lock_reason}). Derivatives positioning dictates 100% Cash ($0.00)."
            else:
                summary = "STAND ASIDE: 5x Tell-Tale Volume Climax Active or Macro Downtrend Veto Engaged."
        elif trade_state == "CIRCUIT_BREAKER_LOCKOUT":
            summary = f"CIRCUIT BREAKER LOCKOUT: {cb_reason} Trading suspended."
        elif trade_state in ("VALUE_ZONE_WATCH", "REJECTION_ARMED"):
            supp_txt = f"${nearest_supp.center_price:,.2f}" if nearest_supp else "N/A"
            summary = (
                f"MONITORING PULLBACK: Price at {supp_txt} support zone. Awaiting 4H rejection candle confirmation "
                f"with Volume > 20 SMA. (Score: {confluence_score}/100)"
            )
        else:
            summary = f"SCANNING: Market regime is {regime}. Awaiting retracement to high-strength horizontal shelf."

        evaluation = SLSPEvaluation(
            timestamp_utc=now_utc,
            spot_price=round(current_price, 2),
            regime=regime,
            regime_reason=reg_reason,
            key_levels=all_levels,
            nearest_support=nearest_supp,
            nearest_resistance=nearest_res,
            active_setup=active_setup,
            trade_state=trade_state,
            mode=self.mode,
            circuit_breaker_active=cb_active,
            circuit_breaker_reason=cb_reason,
            daily_loss_pct=round(daily_loss_pct, 2),
            weekly_loss_pct=round(weekly_loss_pct, 2),
            ema_3_regime=ema_3_reg,
            ema_3_slope_200=round(ema_3_slope, 3),
            ema_3_value_zone_active=ema_3_vz,
            ema_3_adx=round(ema_3_adx, 2),
            ema_3_positioning_met=ema_3_pos_met,
            tell_tale_status=tt_status,
            tell_tale_veto=tt_veto,
            tell_tale_relvol_15m=tt_relvol_15m,
            tell_tale_relvol_5m=tt_relvol_5m,
            liq_flush_status=liq_status,
            liq_flush_detected=liq_detected,
            liq_flush_wick_ratio=liq_wick_ratio,
            liq_flush_oi_delta=liq_oi_delta,
            liq_detector_report=liq_report,
            confluence_score=min(100, confluence_score),
            plain_english_summary=summary,
            decision_log=decision_log,
            macro_regime_id=macro_reg_id,
            macro_regime_name=macro_reg_name,
            macro_regime_score=macro_score,
            macro_regime_diagnosis=macro_diag,
            macro_sizing_factor=macro_sizing,
            macro_rotation=macro_rotation,
            macro_hard_lock_cash=macro_hard_lock,
            macro_lock_reason=macro_lock_reason,
            upper_magnet_price=u_mag_p,
            upper_magnet_dist_pct=u_mag_dist,
            upper_magnet_vol_usd=u_mag_vol,
            lower_magnet_price=l_mag_p,
            lower_magnet_dist_pct=l_mag_dist,
            lower_magnet_vol_usd=l_mag_vol,
            dominant_pull_dir=pull_dir,
            immediate_ratio=imm_ratio,
            total_ladder_ratio=tot_ratio,
            lsce_status=lsce_stat,
            lsce_cluster_tested=lsce_cluster,
            lsce_action_verdict=lsce_verdict,
            structural_stop_price=s_stop,
            structural_stop_dist_pct=s_dist,
            disaster_stop_price=d_stop,
            disaster_stop_dist_pct=d_dist,
        )

        store.slsp_evaluation = evaluation
        return evaluation
