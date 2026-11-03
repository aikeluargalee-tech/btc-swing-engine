"""Tab [5] Master Synthesis & Supreme Order of Battle Evaluator.

Synthesizes the live outputs of all 9 specialist desks (Tabs [1]–[9]):
- Tab [1]: Tactical Swing Execution Engine (`SignalEvaluation`)
- Tab [2]: BTC Spot Swing Protocol v1.3 & Liquidation Magnet (`ProtocolV13Evaluation`)
- Tab [3]: Macro Quant & Cycle Radar (`MacroRadarEvaluation`)
- Tab [4]: Quantitative Microstructure Configurations A–J (`RegimeMatrixEvaluation`)

Applies a strict 4-Layer Institutional Decision Funnel:
  Layer 1: Capital Preservation & Hard Veto Gate (Tab [2] + Tab [4] Config G/H + Tab [1] Hard Veto)
  Layer 2: Macro Structural Regime & Base Risk Budget (Tab [3] 200D SMA + Slope & Cycle Rungs)
  Layer 3: Microstructure Sizing Multiplier & Liquidation Magnet (Tab [4] A–J + Tab [2] Magnet)
  Layer 4: Tactical Auction Location, Chop Filter & Entry Trigger (Tab [1] cVAL / Gate 1–4)
"""

from datetime import datetime, timezone
from typing import Dict, List

from config.settings import EngineConfig
from core.models import (
    DerivativesSnapshot,
    ExecutionGateState,
    FlowSnapshot,
    HierarchyLayerRow,
    MacroRadarEvaluation,
    MasterSynthesisEvaluation,
    ProtocolV13Evaluation,
    RegimeConfigItem,
    RegimeMatrixEvaluation,
    SignalEvaluation,
    TabVerdictRow,
)
from core.state_store import StateStore


_CONFIG_MULTIPLIER_MAP: Dict[str, float] = {
    "Config A": 1.00,
    "Config B": 0.75,
    "Config C": 0.75,
    "Config D": 0.00,
    "Config E": 0.00,
    "Config F": 0.75,
    "Config G": 0.00,
    "Config H": 0.00,
    "Config I": 0.25,
    "Config J": 0.50,
}


class MasterSynthesisEvaluator:
    """Computes the unified Tab [5] Master Conclusion & Reconciled Execution Playbook."""

    def __init__(self, config: EngineConfig) -> None:
        self.config = config

    def evaluate(
        self,
        store: StateStore,
        sig: SignalEvaluation,
        pev: ProtocolV13Evaluation,
        mev: MacroRadarEvaluation,
        rmev: RegimeMatrixEvaluation,
        flow: FlowSnapshot,
        deriv: DerivativesSnapshot,
    ) -> MasterSynthesisEvaluation:
        """Synthesizes Tabs [1]–[9] into a single authoritative Supreme Master Conclusion."""
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        price = sig.current_price
        tp = sig.trade_plan
        target_support = tp.reference_entry if tp else (sig.support_hvn or sig.c_val)

        active_cfg: RegimeConfigItem = next(
            (c for c in rmev.configs if c.is_active),
            rmev.configs[0],
        )

        # Check true capital-preservation vetoes (excluding pure entry-geometry R:R notes)
        true_tab1_vetoes = [
            vr
            for vr in sig.veto_reasons
            if "UNVERIFIED" not in vr and "INSUFFICIENT STRUCTURAL R:R" not in vr
        ]
        rr_veto_only = (
            sig.hard_veto_triggered
            and len(true_tab1_vetoes) == 0
            and any("INSUFFICIENT STRUCTURAL R:R" in vr for vr in sig.veto_reasons)
        )

        # =====================================================================
        # 1. BUILD PANEL 1: 4-TAB EXECUTIVE VERDICT ROLLUP MATRIX
        # =====================================================================
        # --- Tab [1] Swing Engine Verdict ---
        if len(true_tab1_vetoes) > 0 or sig.gate_state == ExecutionGateState.CASH_MARKDOWN:
            t1_light = "RED"
            t1_conc = "HARD VETO — NO NEW BUYS"
        elif sig.gate_state == ExecutionGateState.GATE3_RECLAIM_TRIGGERED and not sig.hard_veto_triggered:
            t1_light = "GREEN"
            t1_conc = f"BUY TRIGGERED (${target_support:,.0f} RECLAIM)"
        elif sig.gate_state == ExecutionGateState.GATE4_PENDING_RETEST:
            t1_light = "YELLOW"
            bars_txt = f"Bar {sig.fsm_bars_elapsed}/{sig.fsm_max_bars}" if sig.fsm_bars_elapsed > 0 else "ARMED"
            t1_conc = f"FSM PENDING RETEST ({bars_txt} @ ${target_support:,.0f})"
        elif (
            sig.gate_state in (ExecutionGateState.GATE1_ZONE_ALERT, ExecutionGateState.GATE2_MICROSTRUCTURE_ARMED)
            and not sig.is_mid_range_chop
        ):
            t1_light = "BLUE"
            t1_conc = f"AT SUPPORT — WAIT RECLAIM (${target_support:,.0f})"
        else:
            t1_light = "YELLOW"
            if sig.is_mid_range_chop:
                t1_conc = f"CHOP ({sig.va_position_pct:.0f}% VA) — WAIT ${target_support:,.0f}"
            else:
                t1_conc = f"STAND ASIDE — BID ${target_support:,.0f}"

        ema_tag = f" | 3-EMA: {sig.ema_strategy.daily_regime}" if sig.ema_strategy else ""
        t1_driver = (
            f"VA Pos: {sig.va_position_pct:.0f}% [{'CHOP' if sig.is_mid_range_chop else 'EDGE'}] "
            f"| cVAL ${sig.c_val:,.0f}{ema_tag}"
        )
        score_state_str = f"{sig.confluence_score:.0f}/100"
        if sig.ema_strategy:
            score_state_str += f" • {sig.ema_strategy.daily_regime}"
        else:
            score_state_str += f" ({sig.regime.value[:10]})"

        t1_row = TabVerdictRow(
            tab_num=1,
            tab_name="[1] Swing Engine",
            traffic_light=t1_light,
            score_or_status=score_state_str,
            primary_driver=t1_driver,
            tab_conclusion=t1_conc,
        )

        # --- Tab [2] Protocol v1.3 & Liquidation Magnet Verdict ---
        active_sells = sum(1 for s in pev.sell_triggers if s.status == "CONFIRMED")
        if pev.any_sell_confirmed:
            t2_light = "RED"
            t2_conc = f"SELL CONFIRMED ({active_sells}/4) — EXIT"
        elif pev.non_trade_zone_status == "YES":
            t2_light = "RED"
            t2_conc = "NON-TRADE ZONE (8A–8F) LOCKED"
        elif pev.buy_allowed == "YES" and pev.entry_status == "READY":
            t2_light = "GREEN"
            t2_conc = "PROTOCOL READY — BUY ALLOWED"
        elif "LONG-LIQ SWEEP" in pev.liq_magnet_verdict or "HOLD SPOT" in pev.liq_magnet_verdict:
            t2_light = "BLUE" if pev.non_trade_zone_status == "NO" else "YELLOW"
            t2_conc = "HOLD SPOT • WAIT MAGNET SWEEP"
        else:
            t2_light = "YELLOW"
            t2_conc = f"BUY:{pev.buy_allowed} ({pev.entry_status}) • DO NOTHING"

        t2_driver = (
            f"1D:{pev.daily_bias} | S:${pev.short_liq_magnet_usd:,.0f} L:${pev.long_liq_magnet_usd:,.0f}"
        )
        t2_row = TabVerdictRow(
            tab_num=2,
            tab_name="[2] Protocol 1.3",
            traffic_light=t2_light,
            score_or_status=f"NTZ:{pev.non_trade_zone_status} • Sell:{active_sells}/4",
            primary_driver=t2_driver,
            tab_conclusion=t2_conc,
        )

        # --- Tab [3] Macro Quant & Cycle Radar Verdict ---
        if not mev.gatekeeper_veto and mev.macro_confidence_pct >= 65.0:
            t3_light = "GREEN"
            t3_conc = "BULL EXPANSION (75–100% SPOT)"
        elif not mev.gatekeeper_veto:
            t3_light = "BLUE"
            t3_conc = "CONSTRUCTIVE BULL (50–75% SPOT)"
        elif mev.crash_rung_override_active:
            t3_light = "BLUE"
            t3_conc = f"SNIPER VALUE ({mev.active_crash_rung[:10]})"
        elif mev.macro_confidence_pct >= 35.0:
            t3_light = "YELLOW"
            t3_conc = "REPAIR (<200D • 0.5% RISK CAP)"
        else:
            t3_light = "RED"
            t3_conc = "MACRO BEAR VETO (100% CASH)"

        t3_driver = (
            f"200D ${mev.sma_200_1d:,.0f} | PowerLaw {mev.power_law_discount_pct:+.1f}%"
        )
        t3_row = TabVerdictRow(
            tab_num=3,
            tab_name="[3] Macro Radar",
            traffic_light=t3_light,
            score_or_status=f"{mev.macro_confidence_pct:.1f}% ({'BULL >200D' if not mev.gatekeeper_veto else 'BELOW 200D'})",
            primary_driver=t3_driver,
            tab_conclusion=t3_conc,
        )

        # --- Tab [4] Regime Matrix A–J Verdict ---
        if active_cfg.category == "BULL_LONG":
            t4_light = "GREEN"
        elif active_cfg.category == "ACCUMULATE":
            t4_light = "BLUE"
        elif active_cfg.category == "HARVEST_WAIT":
            t4_light = "YELLOW"
        else:
            t4_light = "RED"

        regime_mult = _CONFIG_MULTIPLIER_MAP.get(active_cfg.code, 0.50)
        t4_driver = f"{active_cfg.short_title} ({active_cfg.key_live_facts})"
        t4_conc = f"{active_cfg.action_headline} | Stop ${active_cfg.computed_stop_usd:,.0f}"
        t4_row = TabVerdictRow(
            tab_num=4,
            tab_name="[4] Regime A–J",
            traffic_light=t4_light,
            score_or_status=f"{active_cfg.code} ({active_cfg.match_pct:.0f}% Match)",
            primary_driver=t4_driver,
            tab_conclusion=t4_conc,
        )

        # --- Tab [5] MM-BTC Rough Path Arbitrator Verdict ---
        mm_ev = store.mm_btc_evaluation
        if mm_ev is not None:
            if "CLEAR" in mm_ev.signature.arbiter_gate_status and mm_ev.agreeing_models_count >= 3:
                t5_light = "GREEN"
            elif "VETO" in mm_ev.signature.arbiter_gate_status or mm_ev.signature.roughness > 4.5:
                t5_light = "RED"
            elif mm_ev.agreeing_models_count >= 2:
                t5_light = "BLUE"
            else:
                t5_light = "YELLOW"
            t5_driver = f"R={mm_ev.signature.roughness:.2f} | Consensus: {mm_ev.agreeing_models_count}/5"
            t5_conc = f"{mm_ev.action_plan_cash} ({mm_ev.final_weight:.2f}x)"
            t5_status = f"{mm_ev.microstructure_pattern} • H={mm_ev.hurst.hurst:.2f}"
        else:
            t5_light = "YELLOW"
            t5_driver = "Scanning path signatures..."
            t5_conc = "WARMING UP"
            t5_status = "INITIALIZING"

        t5_row = TabVerdictRow(
            tab_num=5,
            tab_name="[5] MM-BTC",
            traffic_light=t5_light,
            score_or_status=t5_status,
            primary_driver=t5_driver,
            tab_conclusion=t5_conc,
        )

        # --- Tab [6] 72H Forward Volatility Cone Verdict ---
        vc_ev = store.volatility_cone_evaluation
        if vc_ev is not None:
            if vc_ev.coiled_spring_alert:
                t6_light = "YELLOW"
                t6_conc = "COILED SPRING (BREAKOUT IMMINENT)"
            elif "COMPRESSION" in vc_ev.vcr_status:
                t6_light = "BLUE"
                t6_conc = "COMPRESSING VOL (ACCUMULATION)"
            else:
                t6_light = "GREEN"
                t6_conc = "IN-CONE VOLATILITY DISPERSION"
            t6_driver = f"GK Vol: {vc_ev.garman_klass_annualized_vol * 100:.1f}% | H={vc_ev.hurst_exponent:.2f}"
            t6_status = f"VCR: {vc_ev.vcr_72h:.2f} • {vc_ev.vcr_status}"
        else:
            t6_light = "YELLOW"
            t6_driver = "Computing Garman-Klass volatility..."
            t6_conc = "WARMING UP"
            t6_status = "INITIALIZING"

        t6_row = TabVerdictRow(
            tab_num=6,
            tab_name="[6] 72H Cone",
            traffic_light=t6_light,
            score_or_status=t6_status,
            primary_driver=t6_driver,
            tab_conclusion=t6_conc,
        )

        # --- Tab [7] Gartley 222 & Confluence Radar Verdict ---
        gy_ev = store.gartley_evaluation
        if gy_ev is not None:
            if "BUY" in gy_ev.overall_verdict or "CONFLUENCE" in gy_ev.overall_verdict:
                t7_light = "GREEN"
            elif "SELL" in gy_ev.overall_verdict or "USDT" in gy_ev.overall_verdict:
                t7_light = "RED"
            elif "HOLD" in gy_ev.overall_verdict:
                t7_light = "BLUE"
            else:
                t7_light = "YELLOW"
            t7_driver = f"1D:{gy_ev.res_1d.verdict} | 4H:{gy_ev.res_4h.verdict}"
            t7_conc = gy_ev.overall_verdict
            t7_status = f"Spot: ${gy_ev.close_price:,.0f} • Parity: ON"
        else:
            t7_light = "YELLOW"
            t7_driver = "Scanning harmonic pivots..."
            t7_conc = "WARMING UP"
            t7_status = "INITIALIZING"

        t7_row = TabVerdictRow(
            tab_num=7,
            tab_name="[7] Gartley 222",
            traffic_light=t7_light,
            score_or_status=t7_status,
            primary_driver=t7_driver,
            tab_conclusion=t7_conc,
        )

        # --- Tab [8] Pattern Invalidation & SFP Trap Radar Verdict ---
        tp_ev = store.trap_evaluation
        if tp_ev is not None:
            if "BEAR TRAP" in tp_ev.active_trap_signal:
                t8_light = "GREEN"
                t8_conc = "BEAR TRAP RECLAIM"
            elif "BULL TRAP" in tp_ev.active_trap_signal:
                t8_light = "RED"
                t8_conc = "BULL TRAP BREAKOUT FAILURE"
            elif "SWEEP" in tp_ev.active_trap_signal:
                t8_light = "YELLOW"
                t8_conc = "LIQUIDITY SWEEP IN PROGRESS"
            else:
                t8_light = "GREEN"
                t8_conc = "NO ACTIVE TRAP (STRUCTURE CLEAN)"
            t8_driver = f"Trap: {tp_ev.active_trap_signal} | Abs: {'YES' if tp_ev.passive_absorption_flag else 'NO'}"
            t8_status = f"{tp_ev.active_trap_state.value}"
        else:
            t8_light = "YELLOW"
            t8_driver = "Scanning fractal pivots..."
            t8_conc = "WARMING UP"
            t8_status = "INITIALIZING"

        t8_row = TabVerdictRow(
            tab_num=8,
            tab_name="[8] SFP Trap",
            traffic_light=t8_light,
            score_or_status=t8_status,
            primary_driver=t8_driver,
            tab_conclusion=t8_conc,
        )

        # --- Tab [9] Terminal Exhaustion & Delta Divergence Radar Verdict ---
        ex_ev = store.exhaustion_evaluation
        if ex_ev is not None:
            if ex_ev.exhaustion_score >= 80.0:
                t9_light = "RED"
                t9_conc = f"TERMINAL EXHAUSTION ({ex_ev.exhaustion_score:.1f}/100)"
            elif ex_ev.exhaustion_score >= 60.0:
                t9_light = "YELLOW"
                t9_conc = f"ELEVATED FATIGUE ({ex_ev.exhaustion_score:.1f}/100)"
            elif ex_ev.exhaustion_score >= 35.0:
                t9_light = "BLUE"
                t9_conc = f"MODERATE MOMENTUM ({ex_ev.exhaustion_score:.1f}/100)"
            else:
                t9_light = "GREEN"
                t9_conc = "MOMENTUM HEALTHY (NO DIVERGENCE)"
            t9_driver = f"Score: {ex_ev.exhaustion_score:.1f} | TD 1H:{ex_ev.td_1h.setup_count}/9 4H:{ex_ev.td_4h.setup_count}/9"
            t9_status = f"{ex_ev.active_exhaustion_signal}"
        else:
            t9_light = "YELLOW"
            t9_driver = "Scanning TD setups..."
            t9_conc = "WARMING UP"
            t9_status = "INITIALIZING"

        t9_row = TabVerdictRow(
            tab_num=9,
            tab_name="[9] Exhaustion",
            traffic_light=t9_light,
            score_or_status=t9_status,
            primary_driver=t9_driver,
            tab_conclusion=t9_conc,
        )

        tab_rows = [t1_row, t2_row, t3_row, t4_row, t5_row, t6_row, t7_row, t8_row, t9_row]
        lights = [r.traffic_light for r in tab_rows]
        g_cnt = lights.count("GREEN")
        b_cnt = lights.count("BLUE")
        y_cnt = lights.count("YELLOW")
        r_cnt = lights.count("RED")

        # =====================================================================
        # 2. BUILD PANEL 2: 4-LAYER HIERARCHICAL DECISION FUNNEL & CONFLICT RESOLVER
        # =====================================================================
        supreme_veto = False
        supreme_veto_reasons: List[str] = []
        if pev.any_sell_confirmed:
            supreme_veto = True
            supreme_veto_reasons.append(f"Tab [2] Sell Trigger ({active_sells}/4)")
        if pev.non_trade_zone_status == "YES":
            supreme_veto = True
            supreme_veto_reasons.append("Tab [2] Non-Trade Zone (8A–8F)")
        if active_cfg.category == "DEFENSIVE_CASH":
            supreme_veto = True
            supreme_veto_reasons.append(f"Tab [4] {active_cfg.code} ({active_cfg.short_title})")
        for vr in true_tab1_vetoes:
            supreme_veto = True
            supreme_veto_reasons.append(vr.split(":")[0])

        if supreme_veto:
            l1_status = "VETO"
            l1_ruling = f"LOCKED: {'; '.join(supreme_veto_reasons[:2])[:44]}"
            supreme_veto_reason_str = "; ".join(supreme_veto_reasons)
        elif pev.non_trade_zone_status == "UNVERIFIED":
            l1_status = "CAUTION"
            l1_ruling = "8A–8E CLEAR; 8F Event Window UNVERIFIED"
            supreme_veto_reason_str = "8F Event Schedule Unverified"
        else:
            l1_status = "PASS"
            l1_ruling = "8A–8F CLEAR • 0/4 Sells • No Squeeze Veto"
            supreme_veto_reason_str = "NONE"

        # Layer 2: Macro Structural Regime & Base Risk Budget (Tab [3])
        has_macro_bars = len(store.spot_klines_1d) >= 50
        if not has_macro_bars or not mev.gatekeeper_veto:
            l2_status = "PASS"
            base_risk_pct = self.config.risk_per_trade_pct  # 1.0%
            l2_ruling = f"Bull >200D (${mev.sma_200_1d:,.0f}, +Slope) -> {base_risk_pct:.2f}% Risk"
        elif mev.crash_rung_override_active:
            l2_status = "ARMED"
            base_risk_pct = self.config.counter_trend_risk_pct  # 0.5%
            l2_ruling = f"{mev.active_crash_rung[:12]} Active -> {base_risk_pct:.2f}% Sniper Risk"
        else:
            l2_status = "CAUTION"
            base_risk_pct = self.config.counter_trend_risk_pct  # 0.5%
            l2_ruling = f"Below 200D (${mev.sma_200_1d:,.0f}) -> {base_risk_pct:.2f}% Risk Cap"

        # Layer 3: Microstructure Sizing Multiplier & Liquidation Magnet (Tab [4] + Tab [2])
        if regime_mult >= 0.75:
            l3_status = "PASS"
        elif regime_mult >= 0.25:
            l3_status = "ARMED"
        else:
            l3_status = "STANDBY"
        l3_ruling = (
            f"{active_cfg.code} ({regime_mult:.2f}x) | Mag S:${pev.short_liq_magnet_usd:,.0f} L:${pev.long_liq_magnet_usd:,.0f}"
        )

        # Layer 4: Tactical Auction Location, Chop Filter & Entry Trigger (Tab [1])
        if sig.gate_state == ExecutionGateState.GATE3_RECLAIM_TRIGGERED and not sig.hard_veto_triggered:
            l4_status = "PASS"
            l4_ruling = f"Gate 3/4 Triggered >=${target_support:,.0f} (+Spot CVD)"
        elif sig.gate_state == ExecutionGateState.GATE4_PENDING_RETEST:
            l4_status = "ARMED"
            bars_txt = f"Bar {sig.fsm_bars_elapsed}/{sig.fsm_max_bars}" if sig.fsm_bars_elapsed > 0 else "ARMED"
            l4_ruling = f"FSM Retest Window ({bars_txt}) -> Band ${sig.fsm_retest_band_low:,.0f}–${sig.fsm_retest_band_high:,.0f}"
        elif sig.is_mid_range_chop:
            l4_status = "STANDBY"
            l4_ruling = f"Mid-Range Chop ({sig.va_position_pct:.0f}% VA) -> Bid ${target_support:,.0f}"
        elif rr_veto_only:
            l4_status = "ARMED"
            l4_ruling = f"Support ${target_support:,.0f} -> Wait Dip for >=1.3R"
        elif sig.gate_state in (ExecutionGateState.GATE1_ZONE_ALERT, ExecutionGateState.GATE2_MICROSTRUCTURE_ARMED):
            l4_status = "ARMED"
            l4_ruling = f"At Support (${target_support:,.0f}) -> Wait 15m/1H Reclaim"
        else:
            l4_status = "STANDBY"
            l4_ruling = f"Price ${price:,.0f} -> Wait for ${target_support:,.0f} Test"

        hierarchy_rows = [
            HierarchyLayerRow(
                layer_num=1,
                layer_name="L1: Veto Gate (Tab 2+4)",
                status=l1_status,
                authority_rule="Supreme Veto Power",
                live_ruling=l1_ruling,
            ),
            HierarchyLayerRow(
                layer_num=2,
                layer_name="L2: Macro Risk (Tab 3)",
                status=l2_status,
                authority_rule="Base Risk (1.0% vs 0.5%)",
                live_ruling=l2_ruling,
            ),
            HierarchyLayerRow(
                layer_num=3,
                layer_name="L3: Size & Mag (Tab 4+2)",
                status=l3_status,
                authority_rule="Size (0.0–1.0x) & Magnet",
                live_ruling=l3_ruling,
            ),
            HierarchyLayerRow(
                layer_num=4,
                layer_name="L4: Entry Timing (Tab 1)",
                status=l4_status,
                authority_rule="Controls Entry Trigger",
                live_ruling=l4_ruling,
            ),
        ]

        # Compute Master Alignment Score (0-100%)
        t2_num_score = (
            0.0
            if (pev.any_sell_confirmed or pev.non_trade_zone_status == "YES")
            else (95.0 if (pev.buy_allowed == "YES" and pev.entry_status == "READY") else (72.0 if t2_light == "BLUE" else 50.0))
        )
        t4_num_score = (
            95.0
            if active_cfg.category == "BULL_LONG"
            else (82.0 if active_cfg.category == "ACCUMULATE" else (48.0 if active_cfg.category == "HARVEST_WAIT" else 10.0))
        )
        raw_alignment = (
            0.30 * sig.confluence_score
            + 0.25 * t2_num_score
            + 0.25 * mev.macro_confidence_pct
            + 0.20 * t4_num_score
        )
        if supreme_veto:
            master_alignment_score = round(min(raw_alignment, 25.0), 1)
            alignment_status = "DEFENSIVE VETO ACTIVE"
        elif g_cnt >= 2 and r_cnt == 0 and not sig.is_mid_range_chop:
            master_alignment_score = round(max(raw_alignment, 75.0), 1)
            alignment_status = "MULTI-TAB BULLISH CONFLUENCE"
        elif (g_cnt + b_cnt) >= 2 and r_cnt == 0:
            master_alignment_score = round(raw_alignment, 1)
            alignment_status = "CONSTRUCTIVE — AWAITING TRIGGER"
        else:
            master_alignment_score = round(raw_alignment, 1)
            alignment_status = "SELECTIVE / PATIENCE REQUIRED"

        # =====================================================================
        # 3. BUILD PANEL 3: CROSS-TAB AGREEMENT & CONFLICT DIAGNOSTIC
        # =====================================================================
        confluence_points: List[str] = []
        conflict_points: List[str] = []
        upgrade_catalysts: List[str] = []

        if flow.w_4h.spot_delta_btc > 0 and rmev.spot_buy_sell_ratio_4h >= 1.0:
            confluence_points.append(
                f"Spot Order Flow Alignment [Tabs 1, 2, 4]: 4H Spot CVD is positive ({flow.w_4h.spot_delta_btc:+,.1f} BTC) "
                f"with 4H Buy/Sell Ratio at {rmev.spot_buy_sell_ratio_4h:.2f} (>1.00 real spot demand)."
            )
        else:
            confluence_points.append(
                f"Order Flow Restraint [Tabs 1, 2, 4]: 4H Spot CVD is {flow.w_4h.spot_delta_btc:+,.1f} BTC "
                f"(B/S Ratio {rmev.spot_buy_sell_ratio_4h:.2f}), confirming why all tabs avoid chasing green candles."
            )

        if deriv.funding_rate_pct <= self.config.funding_neutral_max_pct:
            confluence_points.append(
                f"Derivatives Hygiene [Tabs 1, 2, 4]: Perp funding is uncrowded ({deriv.funding_rate_pct:+.4f}%) "
                f"and Annualized Basis is {rmev.annualized_basis_pct:+.2f}%, eliminating long-crowding veto risk."
            )

        if sig.ema_strategy and sig.ema_strategy.daily_regime in ("STRONG_BULL", "WEAK_BULL"):
            es = sig.ema_strategy
            confluence_points.append(
                f"Trend & EMA Alignment [Tabs 1, 3]: Daily 3-EMA is {es.daily_regime} (200 EMA ${es.daily_ema_200:,.0f}, ADX {es.daily_adx:.1f}) "
                f"with 4H 50-EMA support at ${es.ema_4h_50:,.0f} (Setup: {es.setup_status})."
            )

        if mev.power_law_discount_pct <= 0:
            confluence_points.append(
                f"Valuation & Structural Floor [Tab 3 + Tab 1]: BTC (${price:,.0f}) trades at a {mev.power_law_discount_pct:+.1f}% "
                f"discount to Power-Law Fair Value (${mev.power_law_fair_usd:,.0f}) with 30D Support HVN at ${sig.support_hvn or sig.c_val:,.0f}."
            )
        else:
            confluence_points.append(
                f"Structural Value Anchors [Tab 1 + Tab 3]: 30D Composite POC sits at ${mev.poc_30d:,.0f} "
                f"with active Value Area bounds at ${sig.c_val:,.0f} (cVAL) to ${sig.c_vah:,.0f} (cVAH)."
            )

        if not mev.gatekeeper_veto and sig.is_mid_range_chop:
            conflict_points.append(
                f"Macro Bull [Tab 3] vs. Mid-Range Chop [Tab 1]: Tab [3] is Bullish (>200D SMA ${mev.sma_200_1d:,.0f}), "
                f"BUT Tab [1] blocks mid-range entry at {sig.va_position_pct:.0f}% of VA. "
                f"Resolution -> Keep Bullish bias, but only bid at ${target_support:,.0f}."
            )
        elif mev.gatekeeper_veto and (t4_light in ("GREEN", "BLUE") or sig.flow_score >= 15.0):
            conflict_points.append(
                f"Microstructure Accumulation [Tab 4 {active_cfg.code}] vs. Macro 200D Gatekeeper [Tab 3]: "
                f"Short-term flow shows {active_cfg.short_title}, BUT price is below 1D 200 SMA (${mev.sma_200_1d:,.0f}). "
                f"Resolution -> Cap tactical risk at {self.config.counter_trend_risk_pct:.1f}% and harvest into 21D EMA (${mev.ema_21_1d:,.0f})."
            )

        if sig.gate_state != ExecutionGateState.GATE3_RECLAIM_TRIGGERED and (pev.buy_allowed == "YES" or t4_light in ("GREEN", "BLUE")):
            conflict_points.append(
                f"Protocol/Regime Readiness [Tabs 2, 3, 4] vs. Candle Reclaim Trigger [Tab 1]: "
                f"Tabs [2–4] authorize {regime_mult:.2f}x spot accumulation ({active_cfg.code}), while Tab [1] awaits a 15m/1H reclaim close above ${target_support:,.0f} "
                f"with +1H Spot Z-Score ({flow.w_1h.spot_zscore:+.2f}). Resolution -> Stage limit bid at ${target_support:,.0f}."
            )
        elif sig.gate_state == ExecutionGateState.GATE3_RECLAIM_TRIGGERED and t2_light == "YELLOW":
            conflict_points.append(
                f"Tactical Reclaim [Tab 1 GREEN] vs. 4H Base Consolidation [Tab 2 YELLOW]: "
                f"Tab [1] triggered a 15m/1H HVN reclaim (${target_support:,.0f}), while Tab [2] flags 4H base consolidation "
                f"with Long-Liq Magnet at ${pev.long_liq_magnet_usd:,.0f}. Resolution -> Execute {regime_mult:.2f}x ({active_cfg.code}) via limit bids in ${target_support:,.0f} zone (protect below ${pev.long_liq_magnet_usd:,.0f})."
            )

        if not conflict_points:
            conflict_points.append(
                f"All 4 Specialist Tabs Aligned: Unified under {active_cfg.code} ({active_cfg.short_title}) with {master_alignment_score:.1f}% alignment."
            )

        upgrade_catalysts.append(
            f"To Trigger Full GREEN Execution: 15m/1H candle reclaim close >= ${target_support:,.0f} "
            f"(or sweep of Long-Liq Magnet ${pev.long_liq_magnet_usd:,.0f}) with +1H Spot CVD."
        )
        upgrade_catalysts.append(
            f"To Trigger RED Hard Exit: Daily close below 1D Support (${pev.daily_support:,.0f}) "
            f"/ Tab 1 Tactical Stop (${tp.stop_loss if tp else pev.downside_ref_1d_atr:,.0f}) "
            f"or Track B Macro Liquidation Floor (${pev.long_liq_magnet_usd:,.0f}) with expanding Spot selling."
        )

        # =====================================================================
        # 4. BUILD PANEL 4: RECONCILED MASTER PLAYBOOK (CASH VS. SPOT HOLDER)
        # =====================================================================
        ref_entry = tp.reference_entry if tp else target_support
        plan_stop = tp.stop_loss if tp else pev.downside_ref_1d_atr
        risk_per_btc = max(ref_entry - plan_stop, 1.0)

        edge_mult = regime_mult if regime_mult > 0.0 else (0.50 if not supreme_veto else 0.0)
        final_live_mult = 0.0 if (supreme_veto or sig.is_mid_range_chop or pev.buy_allowed == "NO") else regime_mult

        max_notional_cap = self.config.portfolio_equity_usd * 0.50 * max(edge_mult, 0.50)

        cash_final_risk_pct = round(base_risk_pct * final_live_mult, 3)
        cash_final_risk_usd = self.config.portfolio_equity_usd * (cash_final_risk_pct / 100.0)
        cash_final_btc = round(cash_final_risk_usd / risk_per_btc, 4) if cash_final_risk_pct > 0 else 0.0
        cash_final_usd = round(cash_final_btc * ref_entry, 2)
        if cash_final_usd > max_notional_cap and ref_entry > 0:
            cash_final_usd = round(max_notional_cap, 2)
            cash_final_btc = round(cash_final_usd / ref_entry, 4)

        cash_edge_risk_pct = round(base_risk_pct * edge_mult, 3)
        cash_edge_risk_usd = self.config.portfolio_equity_usd * (cash_edge_risk_pct / 100.0)
        cash_edge_btc = round(cash_edge_risk_usd / risk_per_btc, 4) if cash_edge_risk_pct > 0 else 0.0
        cash_edge_usd = round(cash_edge_btc * ref_entry, 2)
        if cash_edge_usd > max_notional_cap and ref_entry > 0:
            cash_edge_usd = round(max_notional_cap, 2)
            cash_edge_btc = round(cash_edge_usd / ref_entry, 4)

        if supreme_veto:
            cash_permission = "FORBIDDEN (HARD VETO — STAY 100% CASH)"
        elif sig.gate_state == ExecutionGateState.GATE3_RECLAIM_TRIGGERED and pev.buy_allowed == "YES":
            cash_permission = f"AUTHORIZED NOW ({final_live_mult:.2f}x = {cash_final_risk_pct:.2f}% RISK)"
        elif not sig.is_mid_range_chop and (
            pev.buy_allowed == "YES"
            or sig.gate_state in (ExecutionGateState.GATE1_ZONE_ALERT, ExecutionGateState.GATE2_MICROSTRUCTURE_ARMED)
        ):
            cash_permission = f"ACCUMULATE AT SUPPORT ({edge_mult:.2f}x = {cash_edge_risk_pct:.2f}% RISK)"
        else:
            cash_permission = f"WAIT FOR EDGE (0% NOW • {cash_edge_risk_pct:.2f}% AT ${target_support:,.0f})"

        if tp:
            cash_entry_zone_str = (
                f"${tp.entry_zone_low:,.0f} – ${tp.entry_zone_high:,.0f} (Liq Floor: ${pev.long_liq_magnet_usd:,.0f})"
            )
        else:
            cash_entry_zone_str = f"${target_support:,.0f} – ${pev.long_liq_magnet_usd:,.0f}"

        if supreme_veto:
            cash_trigger_instruction = f"VETO ({supreme_veto_reason_str[:32]}) -> Stay 100% Cash."
        elif cash_final_risk_pct > 0:
            cash_trigger_instruction = (
                f"Bid ${tp.entry_zone_low if tp else target_support:,.0f}–${tp.entry_zone_high if tp else target_support:,.0f} "
                f"for {cash_final_btc:.4f} BTC (${cash_final_usd:,.0f})."
            )
        else:
            cash_trigger_instruction = (
                f"Stage bid at ${target_support:,.0f} for {cash_edge_btc:.4f} BTC (${cash_edge_usd:,.0f}) on reclaim."
            )

        # Track B: If Already Holding Spot BTC
        tab1_stop = tp.stop_loss if tp else pev.downside_ref_1d_atr
        tab4_stop = active_cfg.computed_stop_usd
        valid_stops = [s for s in (tab1_stop, tab4_stop) if 0 < s < price * 0.998]
        reconciled_stop = round(min(valid_stops), 2) if valid_stops else round(price * 0.985, 2)
        stop_source = f"Tab 1 Tactical: ${tab1_stop:,.0f} • Tab 4 Macro Floor: ${tab4_stop:,.0f} • 50D: ${pev.sma_50_1d:,.0f}"

        # Track B: Macro Spot Holder Targets (Multi-Day Swing / Reversion)
        macro_tp1_candidates = [c for c in [sig.c_poc, mev.ema_21_1d if mev else sig.c_poc] if c > price]
        holder_tp1_usd = round(min(macro_tp1_candidates), 2) if macro_tp1_candidates else round(max(sig.c_poc, price * 1.03), 2)
        if mev and abs(holder_tp1_usd - mev.ema_21_1d) < 5.0:
            holder_tp1_source = "1D 21 EMA Mean Reversion"
        else:
            holder_tp1_source = "30D cPOC Fair Value Magnet"

        tp2_candidates = [
            (c, src)
            for c, src in [
                (sig.c_vah, "30D cVAH Value Extreme"),
                (pev.short_liq_magnet_usd, f"Short-Liq Magnet (${pev.short_liq_magnet_usd:,.0f})"),
                (pev.daily_resistance, "1D Structural Resistance"),
            ]
            if c > holder_tp1_usd + 300.0
        ]
        if tp2_candidates:
            min_c, min_src = min(tp2_candidates, key=lambda x: x[0])
            holder_tp2_usd = round(min_c, 2)
            holder_tp2_source = min_src
        else:
            holder_tp2_usd = round(max(sig.c_vah, holder_tp1_usd * 1.025), 2)
            holder_tp2_source = "cVAH / Macro Resistance"

        if pev.any_sell_confirmed:
            holder_action = "EXIT / REDUCE IMMEDIATELY (SELL TRIGGER ACTIVE)"
            holder_note = f"Confirmed Sell Trigger ({active_sells}/4). Protect spot capital now."
        elif active_cfg.category == "DEFENSIVE_CASH":
            holder_action = f"DEFENSIVE REDUCE / TIGHTEN STOP ({active_cfg.code.upper()})"
            holder_note = f"Trail hard stop tightly at ${reconciled_stop:,.0f} under {active_cfg.code}."
        elif "TAKE PARTIAL PROFIT" in pev.liq_magnet_verdict or active_cfg.code in ("Config D", "Config E"):
            holder_action = f"HOLD CORE + SCALE 30–50% AT ${holder_tp1_usd:,.0f}"
            holder_note = f"Harvest 30–50% at ${holder_tp1_usd:,.0f}; keep hard stop at ${reconciled_stop:,.0f}."
        else:
            holder_action = "HOLD EXISTING SPOT LONG (PROTECT WITH STOP)"
            holder_note = (
                f"Hold core > ${reconciled_stop:,.0f}; scale 40% @ ${holder_tp1_usd:,.0f} & 60% @ ${holder_tp2_usd:,.0f}."
            )

        # =====================================================================
        # 5. BUILD PANEL 5: SUPREME MASTER EXECUTIVE BOTTOM LINE
        # =====================================================================
        if supreme_veto:
            master_light = "RED"
            master_headline = (
                f"RED LIGHT — SUPREME CAPITAL PRESERVATION VETO ACTIVE ({supreme_veto_reason_str.upper()[:65]})"
            )
        elif (
            sig.gate_state == ExecutionGateState.GATE3_RECLAIM_TRIGGERED
            and pev.buy_allowed == "YES"
            and active_cfg.category in ("BULL_LONG", "ACCUMULATE")
        ):
            master_light = "GREEN"
            master_headline = (
                f"GREEN LIGHT — MULTI-TAB BUY CONFLUENCE CONFIRMED "
                f"(EXECUTE {cash_final_btc:.4f} BTC / ${cash_final_usd:,.0f} SPOT SWING LONG)"
            )
        elif (g_cnt + b_cnt) >= 2 and r_cnt == 0 and not sig.is_mid_range_chop:
            master_light = "BLUE"
            master_headline = (
                f"BLUE LIGHT — CONSTRUCTIVE MULTI-TAB ACCUMULATION ZONE "
                f"(STAGE {cash_edge_btc:.4f} BTC BID AT ${ref_entry:,.0f} SUPPORT)"
            )
        else:
            master_light = "YELLOW"
            master_headline = (
                f"YELLOW LIGHT — PATIENCE / SELECTIVE EQUILIBRIUM "
                f"(NO MARKET CHASING AT ${price:,.0f} — WAIT FOR ${ref_entry:,.0f} EDGE)"
            )

        master_what = (
            f"Scoreboard: {g_cnt} Green • {b_cnt} Blue • {y_cnt} Yellow • {r_cnt} Red "
            f"(Master Alignment: {master_alignment_score:.1f}% — {alignment_status}). "
            f"BTC (${price:,.0f}) is in {active_cfg.code} ({active_cfg.short_title}, {active_cfg.match_pct:.0f}% match) "
            f"with 4H Spot CVD {flow.w_4h.spot_delta_btc:+,.1f} BTC."
        )
        master_why = conflict_points[0]
        master_cmd = (
            f"[IF IN CASH]: {cash_permission} -> Zone ${tp.entry_zone_low if tp else ref_entry:,.0f}–${tp.entry_zone_high if tp else ref_entry:,.0f} "
            f"({cash_edge_btc:.4f} BTC / ${cash_edge_usd:,.0f}).  "
            f"[IF HOLDING SPOT]: {holder_action} | Stop ${reconciled_stop:,.0f} | TP1 ${holder_tp1_usd:,.0f} • TP2 ${holder_tp2_usd:,.0f}."
        )

        ev = MasterSynthesisEvaluation(
            timestamp_utc=now_str,
            current_price=round(price, 2),
            tab_rows=tab_rows,
            tabs_green_count=g_cnt,
            tabs_blue_count=b_cnt,
            tabs_yellow_count=y_cnt,
            tabs_red_count=r_cnt,
            hierarchy_rows=hierarchy_rows,
            master_alignment_score=master_alignment_score,
            alignment_status=alignment_status,
            supreme_veto_active=supreme_veto,
            supreme_veto_reason=supreme_veto_reason_str,
            confluence_points=confluence_points,
            conflict_points=conflict_points,
            upgrade_catalysts=upgrade_catalysts,
            cash_permission=cash_permission,
            cash_entry_zone_str=cash_entry_zone_str,
            cash_base_risk_pct=base_risk_pct,
            cash_regime_multiplier=regime_mult,
            cash_final_risk_pct=cash_final_risk_pct,
            cash_final_notional_usd=cash_final_usd,
            cash_final_size_btc=cash_final_btc,
            cash_edge_risk_pct=cash_edge_risk_pct,
            cash_edge_notional_usd=cash_edge_usd,
            cash_edge_size_btc=cash_edge_btc,
            cash_trigger_instruction=cash_trigger_instruction,
            holder_action=holder_action,
            holder_hard_stop_usd=reconciled_stop,
            holder_hard_stop_source=stop_source,
            holder_tp1_usd=holder_tp1_usd,
            holder_tp1_source=holder_tp1_source,
            holder_tp2_usd=holder_tp2_usd,
            holder_tp2_source=holder_tp2_source,
            holder_management_note=holder_note,
            master_traffic_light=master_light,
            master_headline=master_headline,
            master_what_is_happening=master_what,
            master_why_resolution=master_why,
            master_final_command=master_cmd,
        )
        store.master_synthesis_evaluation = ev
        return ev
