"""4-Gate Swing Execution State Machine, 0-100 Confluence Scorer, Veto Filters, and JSONL Logger."""

import json
import logging
import os
import time
from datetime import datetime, timezone
from typing import List, Optional, Sequence

from config.settings import EngineConfig
from core.models import (
    DerivativesSnapshot,
    ExecutionGateState,
    FlowSnapshot,
    KlineBar,
    MarketRegime,
    OIPositioningQuadrant,
    SignalEvaluation,
    TradePlan,
    VolumeProfileResult,
)
from core.state_store import StateStore
from .cvd_engine import compute_derivatives_snapshot, compute_flow_snapshot
from .ema_strategy_engine import EMAStrategyEngine
from .gartley_engine import GartleyEngine
from .macro_radar import MacroRadarEvaluator
from .master_synthesis import MasterSynthesisEvaluator
from .mm_btc_engine import MMBTCEngine
from .protocol_v13 import ProtocolV13Evaluator
from .regime_matrix import RegimeMatrixEvaluator
from .spot_swing_engine import SpotSwingEngine
from .sweep_retest_fsm import (
    Candle,
    FSMState,
    FSMStorageManager,
    SweepDirection,
    SweepInstance,
    SweepRetestFSM,
)
from .slsp_engine import SLSPEngine
from .trap_engine import TrapEngine
from .exhaustion_engine import ExhaustionEngine
from .volatility_cone_engine import VolatilityConeEngine
from .volume_profile import compute_atr, compute_composite_profile, synthesize_4h_bars


class SignalDetector:
    """Evaluates auction structure, order flow, and derivatives to drive the 4-Gate Swing FSM."""

    def __init__(self, config: EngineConfig) -> None:
        self.config = config
        self.protocol_evaluator = ProtocolV13Evaluator(config)
        self.macro_evaluator = MacroRadarEvaluator(config)
        self.regime_matrix_evaluator = RegimeMatrixEvaluator(config)
        self.master_synthesis_evaluator = MasterSynthesisEvaluator(config)
        self.mm_btc_engine = MMBTCEngine(config)
        self.volatility_cone_engine = VolatilityConeEngine(config)
        self.gartley_engine = GartleyEngine(config)
        self.trap_engine = TrapEngine(config)
        self.exhaustion_engine = ExhaustionEngine(config)
        self.ema_strategy_engine = EMAStrategyEngine(config)
        self.slsp_engine = SLSPEngine(config, read_only=True)
        # Side-effect free by default (no state writes / alerts). Only the live HUD opts in via set_read_only(False).
        self.spot_swing_engine = SpotSwingEngine(config, read_only=True)
        fsm_db_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "sweep_fsm_state.json",
        )
        self.fsm_engine = SweepRetestFSM()
        self.fsm_storage = FSMStorageManager(storage_path=fsm_db_path)
        self._last_logged_regime: Optional[MarketRegime] = None
        self._last_logged_gate: Optional[ExecutionGateState] = None
        self._last_log_ts: float = 0.0

    def _detect_value_area_reclaim(
        self,
        bars_15m: Sequence[KlineBar],
        bars_1h: Sequence[KlineBar],
        c_val: float,
        current_price: Optional[float] = None,
    ) -> bool:
        """Checks if a recent 15m or 1H candle swept below `c_val`, closed back >= `c_val`, and live price still holds >= `c_val`."""
        if current_price is not None and current_price < c_val:
            return False
        # Check last 3 1H candles
        for bar in bars_1h[-3:]:
            if bar.low < c_val and bar.close >= c_val and bar.delta >= 0:
                return True
        # Check last 4 15m candles
        for bar in bars_15m[-4:]:
            if bar.low < c_val and bar.close >= c_val and bar.delta >= 0:
                return True
        return False

    def _build_trade_plan(
        self,
        current_price: float,
        c_val: float,
        c_poc: float,
        c_vah: float,
        primary_lvn: Optional[float],
        support_hvn: Optional[float],
        atr_1h: float,
        recent_bars_1h: Sequence[KlineBar],
        tactical_vp: Optional[VolumeProfileResult] = None,
        session_vp: Optional[VolumeProfileResult] = None,
        testing_support_hvn: bool = False,
        risk_pct_override: Optional[float] = None,
        protocol_ev: Optional[object] = None,
        macro_ev: Optional[object] = None,
    ) -> TradePlan:
        """Calculates structural entry zone, sweep-low/LVN stop-loss, cPOC/cVAH targets, and sizing."""
        recent_swing_low = (
            min(b.low for b in recent_bars_1h[-4:]) if recent_bars_1h else (current_price - atr_1h)
        )

        tact_val = tactical_vp.c_val if tactical_vp is not None else c_val
        if support_hvn is not None and current_price < support_hvn:
            # Dynamic Price-Floor Waterfall (Case B: spot_price < hvn_30d):
            # 30D Support HVN is breached and now acts as overhead supply (TP1).
            # Cascade Track A support bids down to min(hvn_7d, support_1d) / lower structural shelves.
            hvn_7d_candidates = [
                lvl
                for lvl in (
                    tactical_vp.support_hvn_below_val if tactical_vp is not None else None,
                    tactical_vp.c_val if tactical_vp is not None else None,
                    session_vp.c_val if session_vp is not None else None,
                )
                if lvl is not None and 0 < lvl <= current_price
            ]
            hvn_7d = min(hvn_7d_candidates) if hvn_7d_candidates else None
            daily_sup_raw = getattr(protocol_ev, "daily_support", 0.0) if protocol_ev is not None else 0.0
            support_1d = daily_sup_raw if (0 < daily_sup_raw <= current_price) else None

            if hvn_7d is not None and support_1d is not None:
                entry_low = min(hvn_7d, support_1d)
                entry_high = min(current_price, max(hvn_7d, support_1d, entry_low + 0.15 * atr_1h))
            elif hvn_7d is not None:
                entry_low = hvn_7d
                entry_high = min(current_price, entry_low + 0.25 * atr_1h)
            elif support_1d is not None:
                entry_low = support_1d
                entry_high = min(current_price, entry_low + 0.25 * atr_1h)
            else:
                fallback_floor = min(recent_swing_low, current_price - 0.35 * atr_1h)
                entry_low = fallback_floor
                entry_high = min(current_price, max(fallback_floor + 0.20 * atr_1h, recent_swing_low))

            if entry_low > entry_high:
                entry_low = entry_high
            ref_entry = entry_high

            # Stop Loss: Never park the hard stop directly on top of long_liq_magnet
            long_liq_mag = getattr(protocol_ev, "long_liq_magnet_usd", 0.0) if protocol_ev is not None else 0.0
            ema_200_1d = getattr(macro_ev, "ema_200_1d", 0.0) if macro_ev is not None else 0.0
            atr_1d_floor = getattr(protocol_ev, "downside_ref_1d_atr", 0.0) if protocol_ev is not None else 0.0

            base_floor = min(recent_swing_low, entry_low)
            stop_loss = base_floor - (self.config.stop_atr_buffer_mult * atr_1h)

            if long_liq_mag > 0 and stop_loss >= (long_liq_mag - 75.0):
                deep_anchors = [
                    lvl
                    for lvl in (ema_200_1d, atr_1d_floor)
                    if 0 < lvl < (long_liq_mag - 100.0)
                ]
                if deep_anchors:
                    stop_loss = max(deep_anchors) - 50.0
                else:
                    stop_loss = long_liq_mag - max(atr_1h, 450.0)

            # Re-anchor breached 30D HVN as TP1 (Overhead Supply) and 7D/30D cPOC as TP2
            tp1_poc = max(support_hvn, ref_entry + 0.75 * atr_1h)
            tact_poc = tactical_vp.c_poc if tactical_vp is not None else c_poc
            tp2_vah = max(tact_poc, c_poc, tp1_poc + 1.5 * atr_1h)
        elif support_hvn is not None and current_price < (c_val - 0.5 * atr_1h):
            # Trading below 30D Macro cVAL ($81,321) near 7D Tactical cVAL / 30D Support HVN Floor ($79,587):
            # Anchor tactical entry on 7D Tactical cVAL / 24H Session cVAL / 30D Support HVN shelf
            if tactical_vp is not None and support_hvn <= tact_val <= (support_hvn + 2.0 * atr_1h):
                dev_val = tact_val
            elif session_vp is not None and support_hvn < session_vp.c_val <= (support_hvn + 2.0 * atr_1h):
                dev_val = session_vp.c_val
            else:
                dev_val = support_hvn + 0.25 * atr_1h
            entry_low = min(support_hvn, dev_val)
            entry_high = min(current_price, max(dev_val, entry_low + 0.25 * atr_1h))
            if entry_low > entry_high:
                entry_low = support_hvn
                entry_high = max(support_hvn, min(current_price, support_hvn + 0.25 * atr_1h))
            ref_entry = entry_high

            floor_candidates = [recent_swing_low, support_hvn]
            if tactical_vp and tactical_vp.support_hvn_below_val:
                floor_candidates.append(tactical_vp.support_hvn_below_val)
            base_floor = min(floor_candidates)
            stop_loss = base_floor - (self.config.stop_atr_buffer_mult * atr_1h)

            # Structural targets: TP1 -> 7D Tactical cPOC / 30D cPOC, TP2 -> 30D Macro cVAH ($84k+)
            min_tp1_dist = max(self.config.min_structural_rr_to_poc * max(ref_entry - stop_loss, 1.0), atr_1h)
            tp1_poc = (
                tactical_vp.c_poc
                if (tactical_vp is not None and tactical_vp.c_poc >= ref_entry + min_tp1_dist)
                else max(c_poc, ref_entry + min_tp1_dist)
            )
            tp2_vah = max(c_vah, tp1_poc + 1.5 * atr_1h)
        else:
            # Standard cVAL Sweep & Reclaim Geometry
            ref_entry = max(current_price, c_val) if abs(current_price - c_val) <= atr_1h else c_val
            entry_low = c_val
            entry_high = c_val + 0.25 * atr_1h

            if recent_swing_low <= c_val:
                base_floor = recent_swing_low
            elif primary_lvn is not None and (c_val - 1.25 * atr_1h) <= primary_lvn < c_val:
                base_floor = primary_lvn
            else:
                base_floor = min(recent_swing_low, c_val - 0.75 * atr_1h)

            stop_loss = base_floor - (self.config.stop_atr_buffer_mult * atr_1h)
            tp1_poc = max(c_poc, ref_entry + 1.0 * atr_1h)
            tp2_vah = max(c_vah, tp1_poc + 1.0 * atr_1h)

        # Ensure stop is strictly below reference entry by at least 0.5 * ATR
        if ref_entry - stop_loss < 0.5 * atr_1h:
            stop_loss = ref_entry - 1.0 * atr_1h

        risk_per_btc = max(ref_entry - stop_loss, 1.0)
        rr_to_poc = (tp1_poc - ref_entry) / risk_per_btc
        rr_to_vah = (tp2_vah - ref_entry) / risk_per_btc

        eff_risk_pct = risk_pct_override if risk_pct_override is not None else self.config.risk_per_trade_pct
        risk_usd = self.config.portfolio_equity_usd * (eff_risk_pct / 100.0)
        pos_btc = risk_usd / risk_per_btc
        pos_notional = pos_btc * ref_entry
        # Enforce 50% Max Single-Position Notional Cap (Institutional Concentration Guardrail)
        max_notional_usd = self.config.portfolio_equity_usd * 0.50
        if pos_notional > max_notional_usd and ref_entry > 0:
            pos_notional = max_notional_usd
            pos_btc = pos_notional / ref_entry
            risk_usd = pos_btc * risk_per_btc

        return TradePlan(
            entry_zone_low=round(entry_low, 2),
            entry_zone_high=round(entry_high, 2),
            reference_entry=round(ref_entry, 2),
            stop_loss=round(stop_loss, 2),
            tp1_poc=round(tp1_poc, 2),
            tp1_allocation_pct=self.config.tp1_allocation_pct,
            tp2_vah=round(tp2_vah, 2),
            tp2_allocation_pct=self.config.tp2_allocation_pct,
            rr_to_poc=round(rr_to_poc, 2),
            rr_to_vah=round(rr_to_vah, 2),
            position_size_btc=round(pos_btc, 4),
            position_notional_usd=round(pos_notional, 2),
            risk_usd=round(risk_usd, 2),
            risk_pct=round(eff_risk_pct, 2),
        )

    def evaluate(self, store: StateStore) -> Optional[SignalEvaluation]:
        """Runs a full evaluation cycle across Volume Profile, CVD, Derivatives, and the 4-Gate FSM."""
        spot_1h = list(store.spot_klines_1h)
        spot_15m = list(store.spot_klines_15m)
        if len(spot_1h) < 24:
            return None

        # 1. Compute Composite Volume Profiles (30D Macro, 7D Tactical, 24H Session)
        macro_bars = spot_1h[-self.config.macro_profile_days * 24 :]
        tactical_bars = spot_1h[-self.config.tactical_profile_days * 24 :]
        session_bars = spot_1h[-24:]

        macro_vp = compute_composite_profile(
            macro_bars,
            horizon_label=f"{self.config.macro_profile_days}D Macro",
            num_bins=self.config.profile_num_bins,
            value_area_pct=self.config.value_area_pct,
            gaussian_sigma=self.config.gaussian_sigma_bins,
            lvn_rel_threshold=self.config.lvn_relative_threshold,
            hvn_rel_threshold=self.config.hvn_relative_threshold,
        )
        tactical_vp = compute_composite_profile(
            tactical_bars,
            horizon_label=f"{self.config.tactical_profile_days}D Tactical",
            num_bins=self.config.profile_num_bins,
            value_area_pct=self.config.value_area_pct,
            gaussian_sigma=self.config.gaussian_sigma_bins,
            lvn_rel_threshold=self.config.lvn_relative_threshold,
            hvn_rel_threshold=self.config.hvn_relative_threshold,
        )
        session_vp = compute_composite_profile(
            session_bars,
            horizon_label="24H Session",
            num_bins=60,
            value_area_pct=self.config.value_area_pct,
        )

        store.macro_profile = macro_vp
        store.tactical_profile = tactical_vp
        store.session_profile = session_vp

        if macro_vp is None or tactical_vp is None:
            if hasattr(store, "footprint_engine") and store.footprint_engine is not None:
                try:
                    store.footprint_evaluation = store.footprint_engine.evaluate(store)
                except Exception:
                    pass
            return None

        # 2. Compute Order Flow & Derivatives Snapshots
        flow = compute_flow_snapshot(self.config, store)
        deriv = compute_derivatives_snapshot(self.config, store, flow)
        store.flow_snapshot = flow
        store.derivatives_snapshot = deriv

        # 2b. Evaluate Tab [2] Protocol v1.3, Tab [3] Macro Radar, Tab [4] Regime Matrix A-J, Special Tab [S1] MM-BTC, Special Tab [S2] Volatility Cone, & Special Tab [S3] Gartley 222
        protocol_ev = self.protocol_evaluator.evaluate(store, flow, deriv)
        macro_ev = self.macro_evaluator.evaluate(store, flow, deriv, macro_vp)
        self.regime_matrix_evaluator.evaluate(store, flow, deriv, macro_vp)
        self.mm_btc_engine.evaluate(store, spot_1h, spot_15m, deriv)
        self.volatility_cone_engine.evaluate(store, spot_1h, macro_vp)
        self.gartley_engine.evaluate(store)

        current_price = store.binance_spot_price or spot_1h[-1].close
        bars_4h = synthesize_4h_bars(spot_1h)
        atr_1h = max(compute_atr(spot_1h[-30:], period=self.config.atr_period), 1.0)
        atr_4h = max(compute_atr(bars_4h[-30:], period=self.config.atr_period), 1.0)

        # Select active structural profile:
        # Primary structure is 30D Macro Profile; switch to 7D Tactical only when expanding above 30D cVAH
        active_vp = tactical_vp if current_price > macro_vp.c_vah else macro_vp

        # 2c. Evaluate Special Tab [S4]: Pattern Invalidation & Special Tab [S5]: Terminal Exhaustion
        self.trap_engine.evaluate(store, spot_1h, spot_15m, deriv, flow, active_vp=active_vp)
        self.exhaustion_engine.evaluate(store, spot_1h, bars_4h, spot_15m, deriv, flow, active_vp=active_vp)
        try:
            self.spot_swing_engine.evaluate(store)  # Tab [0]: Spot Swing & Liquidation Magnet Engine
        except Exception:
            logging.getLogger("spot_swing").exception("Tab [0] spot swing evaluation failed")

        # 2d. Evaluate 3-EMA Industrial Trend & Pullback System
        ema_snap = self.ema_strategy_engine.evaluate(
            store=store,
            spot_1d=list(store.spot_klines_1d),
            bars_4h=bars_4h,
            current_price=current_price,
            flow=flow,
            deriv=deriv,
            atr_4h=atr_4h,
        )
        store.ema_strategy = ema_snap
        # 2e. Evaluate Intra-Candle Footprint & Order Flow Microstructure
        try:
            if hasattr(store, "footprint_engine") and store.footprint_engine is not None:
                store.footprint_evaluation = store.footprint_engine.evaluate(store)
        except Exception:
            logging.getLogger("footprint").exception("Footprint evaluation failed")

        # 2f. Evaluate Tab [13]: Structure + Level Swing Protocol (SLSP v1.0) & 4-in-1 Integration
        try:
            self.slsp_engine.evaluate(
                store=store,
                spot_1d=list(store.spot_klines_1d),
                bars_4h=bars_4h,
                current_price=current_price,
                active_vp=active_vp,
            )
        except Exception:
            logging.getLogger("slsp").exception("Tab [13] SLSP evaluation failed")

        c_vah = active_vp.c_vah
        c_poc = active_vp.c_poc
        c_val = active_vp.c_val
        primary_lvn = active_vp.primary_lvn_below_val
        support_hvn = active_vp.support_hvn_below_val

        dist_to_val_pct = ((current_price - c_val) / c_val) * 100.0
        dist_to_val_atr = (current_price - c_val) / atr_1h
        va_span = max(c_vah - c_val, 1.0)
        va_position_pct = ((current_price - c_val) / va_span) * 100.0
        is_mid_range_chop = False

        rationale: List[str] = []
        veto_reasons: List[str] = []

        # --- GATE 1: Structural Location Score (Max 25 pts) ---
        location_score = 0.0
        in_val_zone = abs(dist_to_val_atr) <= self.config.val_proximity_atr_mult
        in_tact_val_zone = abs(current_price - tactical_vp.c_val) <= self.config.val_proximity_atr_mult * atr_1h
        sweeping_lvn = (
            current_price < c_val
            and (support_hvn is None or current_price >= support_hvn - 0.25 * atr_1h)
            and dist_to_val_atr >= -2.5
        )
        testing_support_hvn = (
            current_price < c_val
            and support_hvn is not None
            and (support_hvn - 0.60 * atr_1h) <= current_price <= (support_hvn + 1.0 * atr_1h)
        )
        in_actionable_zone = in_val_zone or in_tact_val_zone or sweeping_lvn or testing_support_hvn

        if in_val_zone:
            location_score = 25.0
            rationale.append(
                f"Gate 1 [PASS]: Price testing {active_vp.horizon_label} cVAL (${c_val:,.0f}, {dist_to_val_atr:+.2f} ATR)."
            )
        elif in_tact_val_zone:
            location_score = 23.0
            rationale.append(
                f"Gate 1 [PASS]: Price testing 7D Tactical cVAL (${tactical_vp.c_val:,.0f})."
            )
        elif sweeping_lvn:
            location_score = 22.0
            rationale.append(
                f"Gate 1 [PASS]: Price sweeping LVN liquidity pocket below cVAL (${c_val:,.0f})."
            )
        elif testing_support_hvn and support_hvn is not None:
            location_score = 22.0
            rationale.append(
                f"Gate 1 [SUPPORT HVN FLOOR]: Price testing 30D Support HVN shelf (${support_hvn:,.0f}) below cVAL (${c_val:,.0f})."
            )

        if in_actionable_zone and ema_snap.pullback_zone_active:
            location_score = min(25.0, location_score + 1.0)
            rationale.append(
                f"Gate 1 [EMA PULLBACK CONFLUENCE]: Pullback into 4H 50-EMA zone (${ema_snap.ema_4h_50:,.0f}, {ema_snap.daily_regime})."
            )
        elif 30.0 <= va_position_pct <= 70.0:
            is_mid_range_chop = True
            location_score = 5.0
            rationale.append(
                f"Gate 1 [MID-RANGE CHOP — AVOID]: Price at {va_position_pct:.0f}% of Value Area (${c_val:,.0f}–${c_vah:,.0f}); avoid mid-range entries, wait for cVAL edge."
            )
        elif current_price > c_val and current_price < c_poc:
            # Inside lower 0-30% of Value Area (approaching cVAL edge)
            frac = max(0.0, 1.0 - (current_price - c_val) / max(c_poc - c_val, 1.0))
            location_score = round(15.0 * frac, 1)
            rationale.append(
                f"Gate 1 [NEAR LOWER EDGE]: Price at {va_position_pct:.0f}% of Value Area approaching cVAL (${c_val:,.0f})."
            )
        elif current_price >= c_poc and current_price <= c_vah:
            is_mid_range_chop = va_position_pct <= 75.0
            location_score = 5.0
            rationale.append(
                f"Gate 1 [HIGH IN VA — AVOID]: Price at {va_position_pct:.0f}% of Value Area above cPOC (${c_poc:,.0f}); poor asymmetric entry location."
            )
        elif current_price > c_vah:
            location_score = 0.0
            rationale.append(
                f"Gate 1 [EXTENDED]: Price trading above cVAH (${c_vah:,.0f}); take-profit / trail zone."
            )
        elif support_hvn is not None and current_price > support_hvn and current_price < c_val:
            is_mid_range_chop = True
            location_score = 6.0
            rationale.append(
                f"Gate 1 [MID-GAP CHOP — AVOID]: Price floating mid-range between Support HVN (${support_hvn:,.0f}) and cVAL (${c_val:,.0f}); wait for range edge."
            )
        else:
            location_score = 0.0
            rationale.append(
                f"Gate 1 [BELOW FLOOR]: Price accepted below cVAL (${c_val:,.0f}) and Support HVN (${support_hvn or 0:,.0f})."
            )

        # --- GATE 2: Order Flow & Absorption Score (Max 35 pts) ---
        flow_score = 0.0
        # 2a. Spot CVD Resilience / Divergence (up to 15 pts)
        if flow.w_1h.spot_zscore >= 0.4 and flow.w_4h.spot_zscore >= 0.2:
            flow_score += 15.0
            rationale.append(
                f"Gate 2a [BULLISH SPOT]: Strong aligned Spot buying (1H Z={flow.w_1h.spot_zscore:+.2f}, 4H Z={flow.w_4h.spot_zscore:+.2f})."
            )
        elif flow.w_1h.spot_zscore >= 0.5:
            flow_score += 15.0
            rationale.append(
                f"Gate 2a [BULLISH SPOT]: Strong 1H Spot buying (1H Z={flow.w_1h.spot_zscore:+.2f}, 4H Z={flow.w_4h.spot_zscore:+.2f})."
            )
        elif flow.bullish_pivot_divergence or flow.absorption_divergence:
            flow_score += 14.0
            rationale.append("Gate 2a [DIVERGENCE]: Bullish Spot CVD / Absorption pivot divergence detected.")
        elif flow.w_4h.spot_zscore >= 0.5 and flow.w_1h.spot_zscore < 0.0:
            flow_score += 10.0
            rationale.append(
                f"Gate 2a [4H SPOT CONSTRUCTIVE]: 4H Spot positive (Z={flow.w_4h.spot_zscore:+.2f}), awaiting 1H Spot turn (Z={flow.w_1h.spot_zscore:+.2f})."
            )
        elif flow.w_1h.spot_delta_btc >= 0 or flow.session_spot_cvd > 0:
            flow_score += 9.0
            rationale.append("Gate 2a [RESILIENT]: Spot delta holding positive/flat.")

        # 2b. Spot vs. Perp Divergence or Passive Absorption Index (up to 10 pts)
        if (
            flow.w_1h.flow_divergence_z >= self.config.divergence_z_spread_threshold
            or flow.w_1h.absorption_index >= self.config.absorption_effort_threshold
        ):
            flow_score += 10.0
            rationale.append(
                f"Gate 2b [ABSORPTION]: Passive spot bids absorbing perp sellers (DivZ={flow.w_1h.flow_divergence_z:+.2f}, AbsIdx={flow.w_1h.absorption_index:.2f})."
            )
        elif flow.w_1h.spot_delta_ratio > flow.w_1h.perp_delta_ratio:
            flow_score += 5.0

        # 2c. Coinbase Premium Index (up to 10 pts)
        if (
            deriv.coinbase_premium_pct > self.config.cpi_positive_threshold_pct
            and deriv.coinbase_premium_zscore >= self.config.cpi_zscore_bullish_threshold
        ):
            flow_score += 10.0
            rationale.append(
                f"Gate 2c [US INSTITUTIONAL]: Coinbase Premium positive & expanding ({deriv.coinbase_premium_pct:+.3f}%, Z={deriv.coinbase_premium_zscore:+.2f})."
            )
        elif (
            deriv.coinbase_premium_pct > self.config.cpi_positive_threshold_pct
            or deriv.coinbase_premium_zscore >= 0.25
        ):
            flow_score += 6.0
            rationale.append(
                f"Gate 2c [CPI SUPPORTIVE]: Coinbase Premium constructive ({deriv.coinbase_premium_pct:+.3f}%, Z={deriv.coinbase_premium_zscore:+.2f})."
            )

        # --- GATE 3: Derivatives & Leverage Clearance Score (Max 20 pts) ---
        derivatives_score = 0.0
        if deriv.oi_regime_quadrant == OIPositioningQuadrant.LONG_LIQUIDATION_FLUSH:
            derivatives_score += 12.0
            rationale.append(
                f"Gate 3a [OI FLUSHED]: Long liquidations cleared excess leverage (4H dOI={deriv.oi_change_4h_pct:+.2f}%)."
            )
        elif deriv.oi_regime_quadrant == OIPositioningQuadrant.AGGRESSIVE_SHORT_BUILD:
            derivatives_score += 12.0
            rationale.append(
                f"Gate 3a [TRAPPED SHORTS]: Shorts piling into support (1H dOI={deriv.oi_change_1h_pct:+.2f}%)."
            )
        elif abs(deriv.oi_change_1h_pct) < 0.5:
            derivatives_score += 6.0

        if deriv.funding_rate_pct <= 0.0:
            derivatives_score += 8.0
            rationale.append(
                f"Gate 3b [NEGATIVE FUNDING]: Shorts paying longs ({deriv.funding_rate_pct:+.4f}%)."
            )
        elif deriv.funding_rate_pct <= self.config.funding_neutral_max_pct:
            derivatives_score += 6.0
            rationale.append(
                f"Gate 3b [HEALTHY FUNDING]: Uncrowded funding rate ({deriv.funding_rate_pct:+.4f}%)."
            )

        # Gate 3c: 3-EMA Industrial Positioning Confluence & Daily Regime
        if ema_snap.positioning_pass:
            derivatives_score = min(20.0, derivatives_score + 2.0)
            rationale.append(
                f"Gate 3c [3-EMA POSITIONING]: Confluence pass ({ema_snap.positioning_confirmations_met}/3) in Daily {ema_snap.daily_regime} (ADX: {ema_snap.daily_adx:.1f})."
            )
        else:
            rationale.append(
                f"Gate 3c [3-EMA REGIME]: Daily {ema_snap.daily_regime} (200 EMA ${ema_snap.daily_ema_200:,.0f}, ADX {ema_snap.daily_adx:.1f})."
            )

        # --- GATE 4: Value Area Acceptance / Reclaim Trigger (Max 20 pts) & SweepRetestFSM ---
        reclaim_target_val = (
            session_vp.c_val
            if (testing_support_hvn and session_vp is not None and current_price < c_val - 0.5 * atr_1h)
            else c_val
        )
        is_reclaim = self._detect_value_area_reclaim(
            spot_15m,
            spot_1h,
            reclaim_target_val,
            current_price=current_price,
        )

        # ---------------------------------------------------------------------
        # SweepRetestFSM Integration on Auction Value Area Low (cVAL)
        # ---------------------------------------------------------------------
        active_fsm: Optional[SweepInstance] = None
        fsm_triggered = False
        fsm_pending_retest = False
        fsm_summary = "IDLE (Monitoring cVAL)"

        active_setups = self.fsm_storage.load_active_instances()
        latest_candle = (
            Candle(
                timestamp=int(spot_1h[-1].timestamp_ms / 1000),
                open=spot_1h[-1].open,
                high=spot_1h[-1].high,
                low=spot_1h[-1].low,
                close=spot_1h[-1].close,
                volume=spot_1h[-1].volume,
            )
            if spot_1h
            else None
        )

        if latest_candle is not None:
            # 1. Advance existing active setups with the latest closed 1H bar
            for sid, setup in list(active_setups.items()):
                if setup.metadata.get("last_processed_timestamp") != latest_candle.timestamp:
                    setup = self.fsm_engine.transition(setup, latest_candle)
                    setup.metadata["last_processed_timestamp"] = latest_candle.timestamp
                    active_setups[sid] = setup

            # 2. Check for new Bullish Sweep on cVAL
            c_val_sweep_excess = (reclaim_target_val - latest_candle.low) / max(reclaim_target_val, 1.0)
            if 0.0015 <= c_val_sweep_excess <= 0.03:
                new_inst = self.fsm_engine.register_sweep(
                    SweepDirection.BULLISH,
                    reclaim_target_val,
                    latest_candle,
                    timeframe="1H",
                )
                if new_inst.instance_id not in active_setups:
                    new_inst.metadata["last_processed_timestamp"] = latest_candle.timestamp
                    if latest_candle.close >= reclaim_target_val:
                        new_inst.current_state = FSMState.PENDING_RETEST
                        new_inst.rejection_timestamp = latest_candle.timestamp
                    active_setups[new_inst.instance_id] = new_inst

            # 3. Check live price / latest candle against retest envelopes of active setups
            for sid, setup in list(active_setups.items()):
                if setup.current_state == FSMState.PENDING_RETEST:
                    active_fsm = setup
                    fsm_pending_retest = True
                    fsm_summary = f"PENDING RETEST (Bar {setup.bars_elapsed}/{self.fsm_engine.max_retest_bars}) at ${setup.key_level:,.0f}"

                    # Live price or candle wicks into retest envelope
                    touched_band = (
                        (setup.retest_band_low <= current_price <= setup.retest_band_high)
                        or (setup.retest_band_low <= latest_candle.low <= setup.retest_band_high)
                    )
                    held_structure = current_price >= (setup.retest_band_low - 0.25 * atr_1h)
                    if touched_band and held_structure:
                        setup.current_state = FSMState.TRIGGERED
                        setup.trigger_timestamp = latest_candle.timestamp
                        active_setups[sid] = setup
                        active_fsm = setup
                        fsm_triggered = True
                        fsm_pending_retest = False
                        fsm_summary = f"RETEST TRIGGERED: ${setup.key_level:,.0f} retest confirmed (Stop: ${setup.suggested_stop:,.0f})"
                        break
                elif setup.current_state == FSMState.TRIGGERED:
                    active_fsm = setup
                    fsm_triggered = True
                    fsm_summary = f"RETEST TRIGGERED: ${setup.key_level:,.0f} retest confirmed"
                    break

            # Persist updated FSM states atomically to disk
            self.fsm_storage.commit(active_setups)

        trigger_score = 0.0
        if is_reclaim or fsm_triggered:
            trigger_score = 20.0
            if fsm_triggered and active_fsm is not None:
                rationale.append(
                    f"Gate 4 [FSM RETEST TRIGGERED]: cVAL (${active_fsm.key_level:,.0f}) retest confirmed within band ${active_fsm.retest_band_low:,.0f}–${active_fsm.retest_band_high:,.0f}. Stop: ${active_fsm.suggested_stop:,.0f}."
                )
            else:
                rationale.append(
                    f"Gate 4 [TRIGGERED]: Candle swept below VAL (${reclaim_target_val:,.0f}) and closed back inside Value with positive Spot delta."
                )
        elif fsm_pending_retest and active_fsm is not None:
            trigger_score = 14.0
            rationale.append(
                f"Gate 4 [FSM PENDING RETEST]: cVAL (${active_fsm.key_level:,.0f}) rejection verified; awaiting retest touch (Bar {active_fsm.bars_elapsed}/{self.fsm_engine.max_retest_bars})."
            )
        elif in_actionable_zone and flow.w_15m.spot_delta_btc > 0 and current_price >= reclaim_target_val:
            trigger_score = 12.0
            rationale.append(
                f"Gate 4 [DEVELOPING]: Holding above ${reclaim_target_val:,.0f} with positive 15m Spot delta."
            )

        if ema_snap.trigger_active and in_actionable_zone:
            trigger_score = min(20.0, trigger_score + 2.0)
            rationale.append(
                f"Gate 4 [EMA TRIGGER]: 4H close (${current_price:,.0f}) above 9/20 EMA (${ema_snap.ema_4h_9:,.0f}/${ema_snap.ema_4h_20:,.0f})."
            )

        # Determine if Macro 200D SMA Counter-Trend Risk Cap applies (Two-Tier Mode)
        has_macro_1d_bars = len(store.spot_klines_1d) >= 50
        effective_risk_pct = (
            self.config.counter_trend_risk_pct
            if (has_macro_1d_bars and macro_ev.gatekeeper_veto)
            else self.config.risk_per_trade_pct
        )

        # Build Execution Trade Plan & R:R check
        trade_plan = self._build_trade_plan(
            current_price=current_price,
            c_val=c_val,
            c_poc=c_poc,
            c_vah=c_vah,
            primary_lvn=primary_lvn,
            support_hvn=support_hvn,
            atr_1h=atr_1h,
            recent_bars_1h=spot_1h,
            tactical_vp=tactical_vp,
            session_vp=session_vp,
            testing_support_hvn=testing_support_hvn,
            risk_pct_override=effective_risk_pct,
            protocol_ev=protocol_ev,
            macro_ev=macro_ev,
        )

        if has_macro_1d_bars and macro_ev.gatekeeper_veto:
            rationale.append(
                f"Macro Caution [Tab 3]: Below 1D 200 SMA (${macro_ev.sma_200_1d:,.0f}) -> Counter-Trend {effective_risk_pct:.1f}% Risk Cap."
            )

        # --- HARD VETO FILTERS ---
        # Cross-Tab Master Veto 0a: Tab [2] Protocol v1.3 Non-Trade Zones (8A-8F)
        if protocol_ev.non_trade_zone_status != "NO":
            for ntz_reason in protocol_ev.active_ntz_reasons:
                veto_reasons.append(ntz_reason)

        # Cross-Tab Master Veto 0b: Optional Strict 200D SMA Hard Lock on Tab [1] (when enabled in protocol_context.json)
        if (
            has_macro_1d_bars
            and protocol_ev.enforce_200d_hard_veto_on_tab1
            and macro_ev.gatekeeper_veto
            and not macro_ev.crash_rung_override_active
        ):
            veto_reasons.append(
                f"MACRO 200D SMA GATEKEEPER VETO [Tab 3]: {macro_ev.gatekeeper_status_text}"
            )
        # Veto 1: Leveraged Bounce Trap (Perps surging + OI rising while Spot lags/sells)
        leveraged_trap = (
            flow.w_1h.price_change_pct > 0.10
            and flow.w_1h.perp_zscore > 0.8
            and flow.w_1h.spot_zscore <= -0.15
            and deriv.oi_change_1h_pct >= self.config.oi_surge_trap_pct_1h
        ) or (flow.w_1h.flow_divergence_z <= self.config.leveraged_trap_z_spread and deriv.oi_change_1h_pct > 0.3)

        if leveraged_trap:
            veto_reasons.append(
                "LEVERAGED LONG TRAP: Bounce driven by Perp buying + rising OI without Spot accumulation."
            )

        # Veto 2: Initiative Markdown Auction (Accepted below cVAL with continuous 1H & 4H Spot selling)
        two_4h_below_val = (
            len(bars_4h) >= 2
            and bars_4h[-1].close < c_val - 0.5 * atr_1h
            and bars_4h[-2].close < c_val - 0.5 * atr_1h
        )
        initiative_markdown = (
            two_4h_below_val
            and flow.w_4h.spot_delta_btc < 0
            and flow.w_1h.spot_delta_btc < 0
            and deriv.coinbase_premium_pct < 0
        )
        if initiative_markdown:
            veto_reasons.append(
                "INITIATIVE MARKDOWN: Multi-4H acceptance below cVAL with negative 1H/4H Spot CVD & negative Coinbase Premium (Stay 100% Cash)."
            )

        # Veto 3: Crowded Funding Rate
        if deriv.funding_rate_pct > self.config.funding_crowded_veto_pct:
            veto_reasons.append(
                f"CROWDED LONGS: Funding rate ({deriv.funding_rate_pct:+.4f}%) exceeds safety cap ({self.config.funding_crowded_veto_pct:+.4f}%)."
            )

        # Veto 4: Insufficient Structural Reward-to-Risk to TP1 (when attempting entry)
        if in_actionable_zone and trade_plan.rr_to_poc < self.config.min_structural_rr_to_poc:
            veto_reasons.append(
                f"INSUFFICIENT STRUCTURAL R:R: R:R to TP1 is {trade_plan.rr_to_poc:.2f}R (minimum required: {self.config.min_structural_rr_to_poc:.2f}R)."
            )

        # Veto 5: Strict 3-EMA Regime Veto (Price below falling Daily 200 EMA)
        if (
            ema_snap.daily_regime in ("STRONG_BEAR", "WEAK_BEAR")
            and current_price < ema_snap.daily_ema_200
            and ema_snap.daily_ema_200_slope < 0
        ):
            veto_reasons.append(
                f"3-EMA REGIME VETO: Price (${current_price:,.0f}) below falling Daily 200 EMA (${ema_snap.daily_ema_200:,.0f}, slope {ema_snap.daily_ema_200_slope:+,.1f}$/day); no longs allowed."
            )

        hard_veto = len(veto_reasons) > 0
        total_score = round(location_score + flow_score + derivatives_score + trigger_score, 1)

        # --- Classify Market Regime & 4-Gate State ---
        if initiative_markdown:
            regime = MarketRegime.MARKDOWN
            gate_state = ExecutionGateState.CASH_MARKDOWN
        elif leveraged_trap:
            regime = MarketRegime.LEVERAGE_TRAP
            gate_state = ExecutionGateState.NEUTRAL_OBSERVATION
        elif in_actionable_zone and flow_score >= 18.0 and not hard_veto:
            regime = MarketRegime.ABSORPTION_AT_SUPPORT
            if (is_reclaim or fsm_triggered) and total_score >= self.config.signal_confluence_threshold:
                gate_state = ExecutionGateState.GATE3_RECLAIM_TRIGGERED
            elif fsm_pending_retest:
                gate_state = ExecutionGateState.GATE4_PENDING_RETEST
            else:
                gate_state = ExecutionGateState.GATE2_MICROSTRUCTURE_ARMED
        elif in_actionable_zone:
            regime = MarketRegime.BALANCED
            if fsm_pending_retest:
                gate_state = ExecutionGateState.GATE4_PENDING_RETEST
            else:
                gate_state = ExecutionGateState.GATE1_ZONE_ALERT
        elif deriv.oi_regime_quadrant == OIPositioningQuadrant.LEVERAGED_LONG_EXPANSION and flow.w_1h.spot_delta_btc > 0:
            regime = MarketRegime.LEVERAGE_EXPANSION
            gate_state = ExecutionGateState.NEUTRAL_OBSERVATION
        else:
            regime = MarketRegime.BALANCED
            gate_state = ExecutionGateState.NEUTRAL_OBSERVATION

        evaluation = SignalEvaluation(
            timestamp_utc=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            regime=regime,
            gate_state=gate_state,
            confluence_score=total_score,
            location_score=location_score,
            flow_score=flow_score,
            derivatives_score=derivatives_score,
            trigger_score=trigger_score,
            active_horizon=active_vp.horizon_label,
            current_price=round(current_price, 2),
            c_vah=round(c_vah, 2),
            c_poc=round(c_poc, 2),
            c_val=round(c_val, 2),
            primary_lvn=round(primary_lvn, 2) if primary_lvn is not None else None,
            support_hvn=round(support_hvn, 2) if support_hvn is not None else None,
            atr_1h=round(atr_1h, 2),
            atr_4h=round(atr_4h, 2),
            distance_to_val_pct=round(dist_to_val_pct, 3),
            distance_to_val_atr=round(dist_to_val_atr, 2),
            va_position_pct=round(va_position_pct, 1),
            is_mid_range_chop=is_mid_range_chop,
            is_reclaim_candle=is_reclaim or fsm_triggered,
            hard_veto_triggered=hard_veto,
            veto_reasons=veto_reasons,
            rationale_notes=rationale,
            trade_plan=trade_plan,
            fsm_instance_id=active_fsm.instance_id if active_fsm else None,
            fsm_state=active_fsm.current_state.value if active_fsm else None,
            fsm_bars_elapsed=active_fsm.bars_elapsed if active_fsm else 0,
            fsm_max_bars=self.fsm_engine.max_retest_bars,
            fsm_retest_band_low=active_fsm.retest_band_low if active_fsm else 0.0,
            fsm_retest_band_high=active_fsm.retest_band_high if active_fsm else 0.0,
            fsm_invalidation_level=active_fsm.invalidation_level if active_fsm else 0.0,
            fsm_suggested_stop=active_fsm.suggested_stop if active_fsm else 0.0,
            fsm_direction=active_fsm.direction.value if active_fsm else None,
            fsm_status_summary=fsm_summary,
            ema_strategy=ema_snap,
        )

        store.latest_signal = evaluation
        if store.regime_matrix_evaluation is not None:
            self.master_synthesis_evaluator.evaluate(
                store=store,
                sig=evaluation,
                pev=protocol_ev,
                mev=macro_ev,
                rmev=store.regime_matrix_evaluation,
                flow=flow,
                deriv=deriv,
            )
        self._maybe_log_signal(evaluation, flow, deriv)
        return evaluation

    def _maybe_log_signal(
        self,
        ev: SignalEvaluation,
        flow: FlowSnapshot,
        deriv: DerivativesSnapshot,
    ) -> None:
        """Writes structured JSONL records on regime/gate transitions or periodic 5m heartbeats."""
        now = time.time()
        state_changed = (
            ev.regime != self._last_logged_regime
            or ev.gate_state != self._last_logged_gate
        )
        if not state_changed and (now - self._last_log_ts) < 300.0:
            return

        self._last_logged_regime = ev.regime
        self._last_logged_gate = ev.gate_state
        self._last_log_ts = now

        log_path = self.config.signal_log_path
        log_path.parent.mkdir(parents=True, exist_ok=True)

        record = {
            "timestamp_utc": ev.timestamp_utc,
            "regime": ev.regime.value,
            "gate_state": ev.gate_state.value,
            "confluence_score": ev.confluence_score,
            "scores": {
                "location": ev.location_score,
                "flow": ev.flow_score,
                "derivatives": ev.derivatives_score,
                "trigger": ev.trigger_score,
            },
            "price": ev.current_price,
            "coinbase_premium_pct": round(deriv.coinbase_premium_pct, 4),
            "coinbase_premium_z": round(deriv.coinbase_premium_zscore, 2),
            "profile": {
                "horizon": ev.active_horizon,
                "cVAH": ev.c_vah,
                "cPOC": ev.c_poc,
                "cVAL": ev.c_val,
                "primary_LVN": ev.primary_lvn,
                "support_HVN": ev.support_hvn,
                "dist_to_cVAL_atr": ev.distance_to_val_atr,
            },
            "flow_1h": {
                "spot_delta_btc": round(flow.w_1h.spot_delta_btc, 3),
                "spot_z": round(flow.w_1h.spot_zscore, 2),
                "perp_delta_btc": round(flow.w_1h.perp_delta_btc, 3),
                "perp_z": round(flow.w_1h.perp_zscore, 2),
                "divergence_z": round(flow.w_1h.flow_divergence_z, 2),
                "absorption_index": round(flow.w_1h.absorption_index, 2),
            },
            "derivatives": {
                "oi_btc": round(deriv.open_interest_btc, 2),
                "oi_change_1h_pct": round(deriv.oi_change_1h_pct, 3),
                "oi_change_4h_pct": round(deriv.oi_change_4h_pct, 3),
                "oi_quadrant": deriv.oi_regime_quadrant.value,
                "funding_rate_pct": round(deriv.funding_rate_pct, 4),
            },
            "hard_veto": ev.hard_veto_triggered,
            "veto_reasons": ev.veto_reasons,
            "trade_plan": (
                {
                    "entry_zone": [ev.trade_plan.entry_zone_low, ev.trade_plan.entry_zone_high],
                    "stop_loss": ev.trade_plan.stop_loss,
                    "tp1_poc": ev.trade_plan.tp1_poc,
                    "tp2_vah": ev.trade_plan.tp2_vah,
                    "rr_to_poc": ev.trade_plan.rr_to_poc,
                    "size_btc": ev.trade_plan.position_size_btc,
                }
                if ev.trade_plan
                else None
            ),
        }

        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")
        except Exception:
            pass
