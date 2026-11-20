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


SETUP_TRIGGER_KEY = "[Setup Trigger]"
VETO_GATE_KEY = "[Veto Gate]"
BLOCKING_STATES = frozenset({"SYNTHETIC", "STALE", "UNAVAILABLE", "NO_MATCH", "REFUSED"})


def tab_z_precedence(input_states: Dict[str, str]) -> str:
    """Resolve the veto-only decision ladder from the exact states published to operators.

    This is a PURE function of the printed table - nothing outside `input_states` may
    influence the verdict, so a reader can recompute it from the screen. Two reserved keys
    carry the non-desk conditions:
      "[Veto Gate]"     REFUSED when a supreme veto is active (a blocking state)
      "[Setup Trigger]" OBSERVED when an entry setup exists, NONE otherwise

    Ladder, in order:
      1. any blocking state (SYNTHETIC / STALE / UNAVAILABLE / NO_MATCH / REFUSED) -> NO_TRADE
      2. a clean table with an observed setup -> SETUP_STATE_OPERATOR_DECIDES
      3. otherwise -> SETUP_FORMING
    Greens never authorize anything, and missing/synthetic/stale evidence cannot lift NO_TRADE.
    """
    if any(state in BLOCKING_STATES for state in input_states.values()):
        return "NO_TRADE"
    if input_states.get(SETUP_TRIGGER_KEY) == "OBSERVED":
        return "SETUP_STATE_OPERATOR_DECIDES"
    return "SETUP_FORMING"


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
        rmev: RegimeMatrixEvaluation | None,
        flow: FlowSnapshot,
        deriv: DerivativesSnapshot,
    ) -> MasterSynthesisEvaluation:
        """Synthesizes Tabs [1]–[9] into a single authoritative Supreme Master Conclusion."""
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        price = sig.current_price
        tp = sig.trade_plan
        target_support = tp.reference_entry if tp else (sig.support_hvn or sig.c_val)

        # Without Tab [4], the master desk cannot establish a regime or evaluate its gates.
        if rmev is None:
            unavailable = TabVerdictRow(
                tab_num=4,
                tab_name="[4] Regime Matrix",
                traffic_light="YELLOW",
                score_or_status="UNAVAILABLE",
                primary_driver="Missing input: regime_matrix_evaluation",
                tab_conclusion="Master synthesis held in unavailable state",
            )
            unavailable_ev = MasterSynthesisEvaluation(
                timestamp_utc=now_str,
                current_price=round(price, 2),
                tab_rows=[unavailable],
                tabs_yellow_count=1,
                master_alignment_score=0.0,
                alignment_status="UNAVAILABLE",
                supreme_veto_active=True,
                supreme_veto_reason="Missing input: regime_matrix_evaluation",
                master_traffic_light="YELLOW",
                master_headline="YELLOW LIGHT — MASTER SYNTHESIS UNAVAILABLE (Tab [4] regime evaluation missing)",
                master_what_is_happening="UNAVAILABLE — missing input: regime_matrix_evaluation; no regime configuration nominated.",
                master_why_resolution="Master synthesis did not evaluate because Tab [4] regime telemetry is missing.",
            )
            unavailable_ev.input_states = {"[4] Regime Matrix": "UNAVAILABLE"}
            unavailable_ev.decision_verdict = "NO_TRADE"
            store.master_synthesis_evaluation = unavailable_ev
            return unavailable_ev

        active_cfg: RegimeConfigItem | None = next(
            (c for c in rmev.configs if c.is_active and c.code == rmev.active_config_code),
            None,
        )
        config_code = active_cfg.code if active_cfg else "NO_MATCH"
        config_category = active_cfg.category if active_cfg else None

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
        # 1. BUILD PANEL 1: 8-FLAGSHIP TOP-RIBBON DESK MATRIX (P, G, R, M, A, F, W, 0)
        # =====================================================================
        # --- Desk [P] Structure & SLSP v1.0 (Tab 13) ---
        slsp = getattr(store, "slsp_evaluation", None)
        if slsp is not None:
            supp_px = slsp.nearest_support.center_price if slsp.nearest_support else 0.0
            res_px = slsp.nearest_resistance.center_price if slsp.nearest_resistance else 0.0
            if slsp.tell_tale_veto or slsp.trade_state in ("STAND_ASIDE", "CIRCUIT_BREAKER_LOCKOUT"):
                p_light = "RED"
            elif slsp.trade_state in ("TRIGGER_FIRED", "IN_POSITION"):
                p_light = "GREEN"
            elif slsp.trade_state in ("REJECTION_ARMED", "VALUE_ZONE_WATCH") or slsp.ema_3_value_zone_active:
                p_light = "BLUE"
            else:
                p_light = "YELLOW"
            p_status = f"{slsp.regime} • 3EMA:{slsp.ema_3_regime}"
            p_driver = f"Sup:${supp_px:,.0f} Res:${res_px:,.0f} | TT:{'VETO' if slsp.tell_tale_veto else 'PASS'}"
            obs_r = slsp.active_setup.obstacle_r if slsp.active_setup else 0.0
            p_conc = f"{slsp.trade_state} | Sup ${supp_px:,.0f} ({obs_r:.1f}R)"
        else:
            p_light = "YELLOW"
            p_status = "UNAVAILABLE"
            p_driver = "Missing input: slsp_evaluation"
            p_conc = "UNAVAILABLE — structure desk did not evaluate"

        row_p = TabVerdictRow(
            tab_num=13,
            tab_name="[P] Structure",
            traffic_light=p_light,
            score_or_status=p_status,
            primary_driver=p_driver,
            tab_conclusion=p_conc,
        )

        # --- Desk [G] Grok Dual-Horizon Flow & VWAP SD Matrix (Tab 15) ---
        grk = getattr(store, "grok_quant_evaluation", None)
        if grk is not None:
            vwap_px = float(getattr(grk, "vwap_daily", 0.0) or 0.0)
            vwap_sd = float(getattr(grk, "vwap_stretch_z", 0.0) or 0.0)
            s_4h = float(getattr(grk, "spot_cvd_4h", flow.w_4h.spot_delta_btc))
            p_4h = float(getattr(grk, "futures_cvd_4h", flow.w_4h.perp_delta_btc))
            cpi_pct = float(getattr(grk, "coinbase_premium_pct", deriv.coinbase_premium_pct))
            if s_4h > 0 and cpi_pct > 0 and -1.5 <= vwap_sd <= 1.5:
                g_light = "GREEN"
            elif s_4h < 0 and vwap_sd < -1.5:
                g_light = "RED"
            elif s_4h > 0:
                g_light = "BLUE"
            else:
                g_light = "YELLOW"
            g_status = f"VWAP ${vwap_px:,.0f} ({vwap_sd:+.2f}SD)"
            g_driver = f"4H S:{s_4h:+,.0f} P:{p_4h:+,.0f} BTC | CPI:{cpi_pct:+.3f}%"
            g_conc = f"4H Spot {s_4h:+,.0f} BTC | VWAP {vwap_sd:+.2f}SD"
        else:
            g_light = "YELLOW"
            g_status = "UNAVAILABLE"
            g_driver = "Missing input: grok_quant_evaluation"
            g_conc = "UNAVAILABLE — Grok flow desk did not evaluate"

        row_g = TabVerdictRow(
            tab_num=15,
            tab_name="[G] Grok Flow",
            traffic_light=g_light,
            score_or_status=g_status,
            primary_driver=g_driver,
            tab_conclusion=g_conc,
        )

        # --- Desk [R] SSRN Quantitative Alpha Deck (Tab 16) ---
        ssrn = getattr(store, "ssrn_alpha_evaluation", None)
        if ssrn is not None:
            models_list = getattr(ssrn, "models", []) or []
            m_pass = sum(1 for m in models_list if getattr(m, "is_gate_pass", False))
            m_tot = max(len(models_list), 5)
            rvol = float(getattr(ssrn, "realized_vol_20d_ann", 0.0) or 0.0)
            vt_wt = float(getattr(ssrn, "target_vol_sizing_pct", 0.0) or 0.0)
            macd_ok = bool(getattr(ssrn, "mtf_macd_gate_pass", False))
            if m_pass >= 4 and macd_ok:
                r_light = "GREEN"
            elif m_pass <= 1 and not macd_ok:
                r_light = "RED"
            elif m_pass >= 3 or macd_ok:
                r_light = "BLUE"
            else:
                r_light = "YELLOW"
            r_status = f"{m_pass}/{m_tot} Models • 1D MACD:{macd_ok}"
            r_driver = f"20D RVol:{rvol:.1f}% | VolTarget:{vt_wt:.0f}% | MVRV:{ssrn.live_mvrv_ratio:.2f}"
            r_conc = f"{m_pass}/{m_tot} SSRN Gates | VolTarget {vt_wt:.0f}%"
        else:
            r_light = "YELLOW"
            r_status = "UNAVAILABLE"
            r_driver = "Missing input: ssrn_alpha_evaluation"
            r_conc = "UNAVAILABLE — SSRN desk did not evaluate"

        row_r = TabVerdictRow(
            tab_num=16,
            tab_name="[R] SSRN Alpha",
            traffic_light=r_light,
            score_or_status=r_status,
            primary_driver=r_driver,
            tab_conclusion=r_conc,
        )

        # --- Desk [M] BTC Magnet Liquidation Gravity Deck (Tab 17) ---
        bmag = getattr(store, "btc_magnet_evaluation", None)
        if bmag is not None and getattr(bmag, "upper_magnet", None) is not None and getattr(bmag, "lower_magnet", None) is not None:
            up_mag = float(bmag.upper_magnet.price or pev.short_liq_magnet_usd)
            dn_mag = float(bmag.lower_magnet.price or pev.long_liq_magnet_usd)
            up_dist_pct = abs(float(bmag.upper_magnet.dist_pct))
            dn_dist_pct = abs(float(bmag.lower_magnet.dist_pct))
            m_rules = sum(1 for r in getattr(bmag, "rule_checks", [])[:6] if getattr(r, "passed", False))
            pull_dir = str(getattr(bmag, "pull_direction", "BALANCED"))
            pull_rat = float(getattr(bmag, "pull_ratio", 1.0) or 1.0)
            if m_rules >= 5:
                m_light = "GREEN"
            elif m_rules >= 3 or "UPPER" in pull_dir.upper() or "UP" in pull_dir.upper():
                m_light = "BLUE"
            else:
                m_light = "YELLOW"
            m_status = f"{m_rules}/6 Rules • Pull {pull_rat:.2f}x ({pull_dir[:6]})"
            m_driver = f"Up:${up_mag:,.0f} (+{up_dist_pct:.1f}%) | Low:${dn_mag:,.0f} (-{dn_dist_pct:.1f}%)"
            m_conc = f"Up ${up_mag:,.0f} (+{up_dist_pct:.1f}%) | Low ${dn_mag:,.0f} (-{dn_dist_pct:.1f}%)"
        else:
            # Keep cross-desk calculations available from Tab [2], while the Tab [M]
            # row itself remains explicitly unavailable without its own evaluation.
            up_mag = float(pev.short_liq_magnet_usd)
            dn_mag = float(pev.long_liq_magnet_usd)
            up_dist_pct = ((up_mag - price) / price * 100.0) if price > 0 and up_mag > 0 else 0.0
            dn_dist_pct = ((price - dn_mag) / price * 100.0) if price > 0 and dn_mag > 0 else 0.0
            m_light = "YELLOW"
            m_status = "UNAVAILABLE"
            m_driver = "Missing input: btc_magnet_evaluation.upper_magnet/lower_magnet"
            m_conc = "UNAVAILABLE — magnet desk did not evaluate"

        row_m = TabVerdictRow(
            tab_num=17,
            tab_name="[M] Magnet",
            traffic_light=m_light,
            score_or_status=m_status,
            primary_driver=m_driver,
            tab_conclusion=m_conc,
        )

        # --- Desk [A] BTC Trend-Pullback v1.0 Strategy (Tab 18) ---
        tpb = getattr(store, "trend_pullback_evaluation", None)
        if tpb is not None:
            c_1d = bool(tpb.daily_close_above_sma200 and tpb.daily_sma200_rising)
            c_4h = bool(tpb.ema50_above_ema200 and tpb.ema50_rising_6bars and tpb.close_4h_above_ema200)
            c_rec = bool(tpb.rec_all_conditions_met and not tpb.candle_4h_low_below_zone_lower)
            if tpb.strategy_verdict in ("ENTRY READY", "LONG ENTRY"):
                a_light = "GREEN"
            elif c_1d and c_4h:
                a_light = "BLUE"
            elif not c_1d:
                a_light = "RED"
            else:
                a_light = "YELLOW"
            a_status = f"1D:{c_1d} • 4H:{c_4h} • Rec:{c_rec}"
            a_driver = f"Zone ${tpb.pullback_zone_lower:,.0f}–${tpb.pullback_zone_upper:,.0f} | Stop ${tpb.structural_stop:,.0f}"
            a_conc = f"{tpb.strategy_verdict} ({tpb.decision_state[:22]})"
        else:
            a_light = "YELLOW"
            a_status = "UNAVAILABLE"
            a_driver = "Missing input: trend_pullback_evaluation"
            a_conc = "UNAVAILABLE — strategy desk did not evaluate"

        row_a = TabVerdictRow(
            tab_num=18,
            tab_name="[A] BTC Strategy",
            traffic_light=a_light,
            score_or_status=a_status,
            primary_driver=a_driver,
            tab_conclusion=a_conc,
        )

        # --- Desk [F] Footprint Swing & 3-Variant Forward Test (Tab 11) ---
        fp = getattr(store, "footprint_evaluation", None)
        if fp is not None:
            fp_sig = str(getattr(fp, "signal_state", None) or getattr(fp, "verdict", "OBSERVING")).upper()
            raw_fp_delta = getattr(fp, "active_bar_delta", None)
            if raw_fp_delta is None:
                raw_fp_delta = getattr(fp, "current_bar_delta", 0.0)
            fp_delta = float(raw_fp_delta or 0.0)
            if "BUY" in fp_sig or "LONG" in fp_sig or "TRIGGER" in fp_sig:
                f_light = "GREEN"
            elif "VETO" in fp_sig or "LOCKED" in fp_sig:
                f_light = "RED"
            elif fp_delta > 0:
                f_light = "BLUE"
            else:
                f_light = "YELLOW"
            f_status = f"15m Δ:{fp_delta:+.1f} BTC"
            f_driver = f"Delta {fp_delta:+.1f} BTC | State: {fp_sig[:18]}"
            f_conc = f"{fp_sig[:24]} (Δ {fp_delta:+.1f} BTC)"
        else:
            f_light = "YELLOW"
            f_status = "UNAVAILABLE"
            f_driver = "Missing input: footprint_evaluation"
            f_conc = "UNAVAILABLE — footprint desk did not evaluate"

        row_f = TabVerdictRow(
            tab_num=11,
            tab_name="[F] Footprint",
            traffic_light=f_light,
            score_or_status=f_status,
            primary_driver=f_driver,
            tab_conclusion=f_conc,
        )

        # --- Desk [W] 5-Pillar Institutional Decision Waterfall (Tab 12) ---
        active_sells = sum(1 for s in pev.sell_triggers if s.status == "CONFIRMED")
        p1_pass = not mev.gatekeeper_veto
        p2_pass = not sig.is_mid_range_chop and sig.location_score >= 15.0
        p3_pass = sig.flow_score >= 15.0
        p4_pass = pev.non_trade_zone_status == "NO" and not pev.any_sell_confirmed
        p5_pass = sig.gate_state == ExecutionGateState.GATE3_RECLAIM_TRIGGERED and not sig.hard_veto_triggered
        w_passes = sum([p1_pass, p2_pass, p3_pass, p4_pass, p5_pass])
        if not p4_pass or len(true_tab1_vetoes) > 0:
            w_light = "RED"
            w_conc = f"VETO LOCKED ({w_passes}/5 Pillars) • {config_code}"
        elif w_passes == 5:
            w_light = "GREEN"
            w_conc = f"ALL 5/5 PILLARS PASS • {config_code}"
        elif w_passes >= 3:
            w_light = "BLUE"
            w_conc = f"{w_passes}/5 Pillars Pass • {config_code} ({sig. confluence_score:.0f}/100)"
        else:
            w_light = "YELLOW"
            w_conc = f"{w_passes}/5 Pillars Pass • Bid ${target_support:,.0f}"
        w_status = f"{w_passes}/5 Gates • {config_code}"
        w_driver = f"Conf {sig.confluence_score:.0f}/100 | VA {sig.va_position_pct:.0f}% | NTZ:{pev.non_trade_zone_status}"

        row_w = TabVerdictRow(
            tab_num=12,
            tab_name="[W] Waterfall",
            traffic_light=w_light,
            score_or_status=w_status,
            primary_driver=w_driver,
            tab_conclusion=w_conc,
        )

        # --- Desk [0] BTC Spot Swing 1:3 RRR Screener (Tab 0) ---
        sw_ev = store.spot_swing_evaluation
        if sw_ev is not None and sw_ev.data_ready and sw_ev.macro is not None:
            sw_light = sw_ev.traffic_light if sw_ev.traffic_light in ("GREEN", "BLUE", "YELLOW", "RED") else "YELLOW"
            rrr_val = sw_ev.magnet.rrr_to_magnet if sw_ev.magnet else 0.0
            sw_status = f"1D:{'PASS' if sw_ev.macro.macro_approved else 'WAIT'} • R:R to magnet {rrr_val:.2f}R"
            sw_driver = f"50D:${pev.sma_50_1d:,.0f} | R:R to magnet {rrr_val:.2f}R (req >=3.0R)"
            sw_conc = f"{sw_ev.verdict} (R:R to magnet {rrr_val:.2f}R)"
        else:
            sw_light = "YELLOW"
            sw_status = "UNAVAILABLE"
            sw_driver = "Missing input: ready spot_swing_evaluation (data_ready and macro required)"
            sw_conc = "UNAVAILABLE — spot swing desk did not evaluate"

        row_0 = TabVerdictRow(
            tab_num=0,
            tab_name="[0] Spot Swing",
            traffic_light=sw_light,
            score_or_status=sw_status,
            primary_driver=sw_driver,
            tab_conclusion=sw_conc,
        )

        regime_mult = _CONFIG_MULTIPLIER_MAP.get(config_code, 0.0) if active_cfg else 0.0
        tab_rows = [row_p, row_g, row_r, row_m, row_a, row_f, row_w, row_0]
        input_states = {row.tab_name: ("UNAVAILABLE" if row.score_or_status == "UNAVAILABLE" else "LIVE")
                        for row in tab_rows}
        input_states["[4] Regime Matrix"] = "LIVE" if active_cfg is not None else "NO_MATCH"
        if fp is not None and bool(getattr(fp, "is_synthetic", False)):
            input_states["[F] Footprint"] = "SYNTHETIC"
        # Desks that publish freshness must contribute it: a stale input blocks like a missing
        # one, and it must be visible in the table rather than inferred from the verdict.
        for _name, _ev in (("[4] Regime Matrix", rmev), ("[F] Footprint", fp)):
            if _ev is not None and str(getattr(_ev, "data_status", "")).upper() == "STALE":
                input_states[_name] = "STALE"
        lights = [r.traffic_light for r in tab_rows]
        g_cnt = lights.count("GREEN")
        b_cnt = lights.count("BLUE")
        y_cnt = lights.count("YELLOW")
        r_cnt = lights.count("RED")

        # =====================================================================
        # 2. BUILD PANEL 2: 4 ORTHOGONAL TOP-RIBBON DOMAIN PILLARS
        # =====================================================================
        supreme_veto = False
        supreme_veto_reasons: List[str] = []
        if slsp is not None and slsp.tell_tale_veto:
            supreme_veto = True
            supreme_veto_reasons.append("Desk [P] Tell-Tale 5x Volume Climax Veto")
        if pev.any_sell_confirmed:
            supreme_veto = True
            supreme_veto_reasons.append(f"Desk [W/2] Sell Trigger ({active_sells}/4)")
        if pev.non_trade_zone_status == "YES":
            supreme_veto = True
            supreme_veto_reasons.append("Desk [W/2] Non-Trade Zone (8A–8F)")
        if config_category == "DEFENSIVE_CASH":
            supreme_veto = True
            supreme_veto_reasons.append(f"Desk [W/4] {active_cfg.code} ({active_cfg.short_title})")
        for vr in true_tab1_vetoes:
            supreme_veto = True
            supreme_veto_reasons.append(vr.split(":")[0])

        if supreme_veto:
            l1_status = "VETO"
            l1_ruling = f"LOCKED: {'; '.join(supreme_veto_reasons[:2])[:44]}"
            supreme_veto_reason_str = "; ".join(supreme_veto_reasons)
        elif pev.non_trade_zone_status == "UNVERIFIED":
            l1_status = "CAUTION"
            l1_ruling = "Tell-Tale PASS; 8A–8E CLEAR; 8F UNVERIFIED"
            supreme_veto_reason_str = "8F Event Schedule Unverified"
        else:
            l1_status = "PASS"
            l1_ruling = "Tell-Tale PASS • Liq Flush NORMAL • 8A–8F CLEAR"
            supreme_veto_reason_str = "NONE"

        for row in tab_rows:
            if row.traffic_light == "RED":
                input_states[row.tab_name] = "REFUSED"
        input_states["[Veto Gate]"] = "REFUSED" if supreme_veto else "LIVE"

        # Object presence is not a setup. A Trend-Pullback evaluation exists whenever that desk
        # has run at all, so "(tpb is not None)" reported the trigger OBSERVED on a desk whose own
        # verdict was "NO TRADE (DEFENSIVE / BEARISH REGIME)" - the same fail-open shape as the
        # rest of the audit: the existence of an answer treated as a positive answer.
        tpb_affirmative = bool(
            tpb is not None
            and {getattr(tpb, "trade_decision", "NO TRADE"),
                 getattr(tpb, "strategy_verdict", "NO TRADE")}
            & {"ENTRY READY", "WAIT FOR RETEST", "CONFIRMED"}
        )
        # `sig.trade_plan` is BUILT ON EVERY EVALUATION and is never None (signal_detector
        # builds it unconditionally and no path passes None), so truthiness of the plan asserted
        # "a setup exists" on every single run - the trigger read OBSERVED while all four desks
        # said REFUSED. A live setup is an active sweep/retest FSM, not the presence of a plan.
        _ACTIVE_FSM_STATES = {"SEEKING_REJECTION", "PENDING_RETEST", "TRIGGERED"}
        tp_affirmative = getattr(sig, "fsm_state", None) in _ACTIVE_FSM_STATES
        # A desk that cannot produce an answer cannot create a trigger. Tab [0] carries a verdict
        # field even when its own data_ready/macro inputs are missing - the desk row then reports
        # UNAVAILABLE while the trigger read OBSERVED off the same object.
        sw_affirmative = bool(
            sw_ev is not None
            and getattr(sw_ev, "data_ready", False)
            and getattr(sw_ev, "macro", None) is not None
            and getattr(sw_ev, "verdict", "") == "NEW LONG SETUP"
        )
        setup_observed = bool(tp_affirmative or tpb_affirmative or sw_affirmative)
        input_states[SETUP_TRIGGER_KEY] = "OBSERVED" if setup_observed else "NONE"
        decision_verdict = tab_z_precedence(input_states)
        master_light = "RED" if decision_verdict == "NO_TRADE" else ("BLUE" if decision_verdict == "SETUP_FORMING" else "YELLOW")
        master_headline = f"{decision_verdict} — regime {config_code if active_cfg else 'NO_MATCH'}"

        # Domain Pillar 2: Macro & 4H Trend Filter (Desks A, 0, W)
        has_macro_bars = len(store.spot_klines_1d) >= 50
        a_4h_ok = bool(tpb and tpb.ema50_above_ema200 and tpb.ema50_rising_6bars and tpb.close_4h_above_ema200)
        if not has_macro_bars or (not mev.gatekeeper_veto and a_4h_ok):
            l2_status = "PASS"
            base_risk_pct = self.config.risk_per_trade_pct  # 1.0%
            l2_ruling = f"1D >200SMA (${mev.sma_200_1d:,.0f}) & 4H EMA50>200 -> PASS"
        elif not mev.gatekeeper_veto and not a_4h_ok:
            l2_status = "STANDBY"
            base_risk_pct = self.config.risk_per_trade_pct
            l2_ruling = f"1D >200SMA (${mev.sma_200_1d:,.0f}) TRUE | 4H EMA50>200 FALSE"
        elif mev.crash_rung_override_active:
            l2_status = "ARMED"
            base_risk_pct = self.config.counter_trend_risk_pct  # 0.5%
            l2_ruling = f"{mev.active_crash_rung[:12]} Active -> {base_risk_pct:.2f}% Risk Cap"
        else:
            l2_status = "CAUTION"
            base_risk_pct = self.config.counter_trend_risk_pct  # 0.5%
            l2_ruling = f"1D Below 200SMA (${mev.sma_200_1d:,.0f}) -> {base_risk_pct:.2f}% Cap"

        # Domain Pillar 3: Structure Shelves & Liquidation Magnets (Desks P, M, B)
        p_shelf_px = slsp.nearest_support.center_price if (slsp and slsp.nearest_support) else target_support
        if row_p.traffic_light in ("GREEN", "BLUE") and not sig.is_mid_range_chop:
            l3_status = "PASS" if row_p.traffic_light == "GREEN" else "ARMED"
        else:
            l3_status = "STANDBY"
        l3_ruling = f"Shelf ${p_shelf_px:,.0f} | Mag ↑${up_mag:,.0f} ↓${dn_mag:,.0f}"

        # Domain Pillar 4: Order Flow, Footprint, SSRN & Strategy Triggers (Desks G, F, R, A)
        if (row_a.traffic_light == "GREEN" or row_p.traffic_light == "GREEN") and not supreme_veto:
            l4_status = "PASS"
            l4_ruling = f"Trigger Fired | 4H Spot CVD {flow.w_4h.spot_delta_btc:+,.0f} BTC"
        elif flow.w_4h.spot_delta_btc > 0 and row_g.traffic_light in ("GREEN", "BLUE"):
            l4_status = "ARMED"
            l4_ruling = f"4H Spot {flow.w_4h.spot_delta_btc:+,.0f} BTC | Pending Desk P/A/0 Trigger"
        else:
            l4_status = "STANDBY"
            l4_ruling = f"4H Spot {flow.w_4h.spot_delta_btc:+,.0f} BTC | Pending Pullback & Trigger"

        hierarchy_rows = [
            HierarchyLayerRow(
                layer_num=1,
                layer_name="D1: Crash/Veto Guards [P,W]",
                status=l1_status,
                authority_rule="Tell-Tale 5x & NTZ 8A–8F",
                live_ruling=l1_ruling,
            ),
            HierarchyLayerRow(
                layer_num=2,
                layer_name="D2: 1D/4H Trend [A,0,W]",
                status=l2_status,
                authority_rule="1D SMA200 & 4H EMA50/200",
                live_ruling=l2_ruling,
            ),
            HierarchyLayerRow(
                layer_num=3,
                layer_name="D3: Shelves & Magnets [P,M]",
                status=l3_status,
                authority_rule="SLSP Shelf & Liq Magnets",
                live_ruling=l3_ruling,
            ),
            HierarchyLayerRow(
                layer_num=4,
                layer_name="D4: Flow & Triggers [G,F,R,A]",
                status=l4_status,
                authority_rule="CVD, Footprint & Triggers",
                live_ruling=l4_ruling,
            ),
        ]

        # Compute 8-Desk Top-Ribbon Readiness Percentage (0-100%)
        desk_pts = {"GREEN": 100.0, "BLUE": 75.0, "YELLOW": 45.0, "RED": 10.0}
        raw_alignment = sum(desk_pts.get(r.traffic_light, 45.0) for r in tab_rows) / max(len(tab_rows), 1)
        if supreme_veto:
            master_alignment_score = round(min(raw_alignment, 25.0), 1)
            alignment_status = "DEFENSIVE VETO ACTIVE"
        elif g_cnt >= 3 and r_cnt == 0:
            # Multi-desk alignment is a real state, but it must not invent readiness.
            # A floor of 75 made the published score unrecomputable from the desks beside
            # it (3 green + 5 yellow = 65.6 printed as 75.0) and could cross the >=70
            # readiness gate on its own. The label carries the interpretation; the
            # number stays the actual mean.
            master_alignment_score = round(raw_alignment, 1)
            alignment_status = "MULTI-DESK ALIGNMENT"
        elif (g_cnt + b_cnt) >= 4 and r_cnt == 0:
            master_alignment_score = round(raw_alignment, 1)
            alignment_status = "CONSTRUCTIVE — AWAITING TRIGGER"
        else:
            master_alignment_score = round(raw_alignment, 1)
            alignment_status = "SELECTIVE / STANDBY"

        # =====================================================================
        # 3. BUILD PANEL 3: CROSS-TAB AGREEMENT & CONFLICT DIAGNOSTIC
        # =====================================================================
        confluence_points: List[str] = []
        conflict_points: List[str] = []
        upgrade_catalysts: List[str] = []

        if flow.w_4h.spot_delta_btc > 0 and rmev.spot_buy_sell_ratio_4h >= 1.0:
            confluence_points.append(
                f"Spot Order Flow Alignment [Desks G, F, W]: 4H Spot CVD is positive ({flow.w_4h.spot_delta_btc:+,.1f} BTC) "
                f"with 4H Buy/Sell Ratio at {rmev.spot_buy_sell_ratio_4h:.2f} (>1.00 real spot demand)."
            )
        else:
            confluence_points.append(
                f"Order Flow Restraint [Desks G, F, W]: 4H Spot CVD is {flow.w_4h.spot_delta_btc:+,.1f} BTC "
                f"(B/S Ratio {rmev.spot_buy_sell_ratio_4h:.2f}), confirming why desks avoid chasing mid-range candles."
            )

        if deriv.funding_rate_pct <= self.config.funding_neutral_max_pct:
            confluence_points.append(
                f"Derivatives & Magnet Hygiene [Desks M, G, W]: Perp funding is uncrowded ({deriv.funding_rate_pct:+.4f}%) "
                f"with Upper Short-Liq Magnet at ${up_mag:,.0f} and Lower Long-Liq Magnet at ${dn_mag:,.0f}."
            )

        if tpb is not None:
            confluence_points.append(
                f"BTC Trend-Pullback Strategy [Desk A]: 1D Close>SMA200={bool(tpb.daily_close_above_sma200)} | "
                f"4H EMA50>EMA200={bool(tpb.ema50_above_ema200)} | Pullback Zone ${tpb.pullback_zone_lower:,.0f}–${tpb.pullback_zone_upper:,.0f} "
                f"(Ref Entry ${tpb.reference_entry_price:,.0f}, Ref Stop ${tpb.structural_stop:,.0f}, Size {tpb.position_size_btc:.5f} BTC)."
            )

        # Desk [0] Spot Swing Protocol Confluence
        if sw_ev and sw_ev.data_ready and sw_ev.macro:
            if sw_ev.trade is not None:
                confluence_points.append(
                    f"Spot Swing Protocol [Tab 0]: Active position from ${sw_ev.trade.entry:,.0f} "
                    f"(Stop ${sw_ev.trade.current_stop:,.0f}, TP1 ${sw_ev.trade.tp1:,.0f}, PWH ${sw_ev.trade.tp2:,.0f})."
                )
            elif sw_ev.verdict == "NEW LONG SETUP" and sw_ev.risk:
                confluence_points.append(
                    f"Spot Swing Protocol [Tab 0]: NEW LONG SETUP armed at ${sw_ev.risk.entry:,.0f} "
                    f"(Stop ${sw_ev.risk.stop:,.0f}, 1% Size: {sw_ev.risk.qty_btc:.4f} BTC, +2.0R Target ${sw_ev.risk.tp1:,.0f})."
                )

        if slsp is not None and slsp.nearest_support is not None:
            confluence_points.append(
                f"Structure & Level Protocol [Desk P]: Nearest Support Shelf at ${slsp.nearest_support.center_price:,.0f} "
                f"({slsp.nearest_support.strength}/5 stars, {slsp.nearest_support.touch_count}x touches) | "
                f"3-EMA Regime: {slsp.ema_3_regime} | Tell-Tale Veto: {'ACTIVE' if slsp.tell_tale_veto else 'CLEAR'}."
            )

        if tpb is not None and tpb.daily_close_above_sma200 and not tpb.ema50_above_ema200:
            conflict_points.append(
                f"1D Macro Regime [Desk A/0 TRUE] vs. 4H Trend Structure [Desk A FALSE]: "
                f"1D Close (${tpb.daily_close_completed:,.0f}) is above 1D SMA200 (${tpb.daily_sma200:,.0f}), "
                f"BUT 4H EMA50 (${tpb.ema50_4h:,.0f}) is below 4H EMA200 (${tpb.ema200_4h:,.0f}). "
                f"Resolution -> Keep each strategy independent; Desk A requires 4H EMA50 > EMA200 before arming pullbacks."
            )
        elif not mev.gatekeeper_veto and sig.is_mid_range_chop:
            conflict_points.append(
                f"1D Macro Gate [Desk W/0] vs. Mid-Range Location [Desk P/W]: Price is above 1D 200 SMA (${mev.sma_200_1d:,.0f}), "
                f"BUT trading at {sig.va_position_pct:.0f}% of 30D Value Area. "
                f"Resolution -> Do not chase mid-range; monitor support shelf at ${target_support:,.0f}."
            )
        elif mev.gatekeeper_veto and (row_w.traffic_light in ("GREEN", "BLUE") or sig.flow_score >= 15.0):
            conflict_points.append(
                f"Short-Horizon Flow [Desks G, F] vs. 1D 200 SMA Gatekeeper [Desks A, 0, W]: "
                f"Short-term flow is constructive, BUT price is below 1D 200 SMA (${mev.sma_200_1d:,.0f}). "
                f"Resolution -> Cap counter-trend risk at {self.config.counter_trend_risk_pct:.1f}%."
            )

        if sig.gate_state != ExecutionGateState.GATE3_RECLAIM_TRIGGERED and (pev.buy_allowed == "YES" or row_w.traffic_light in ("GREEN", "BLUE")):
            conflict_points.append(
                f"Support Zone Proximity [Desks P, M] vs. Candle Trigger [Desks A, P, 0]: "
                f"Price is near structural support (${target_support:,.0f}), while execution desks await a closed 4H/1H trigger candle "
                f"with +1H Spot Z-Score ({flow.w_1h.spot_zscore:+.2f})."
            )

        if not conflict_points:
            conflict_points.append(
                f"All 8 Top-Ribbon Flagship Desks Synchronized: {g_cnt} Green • {b_cnt} Blue • {y_cnt} Yellow • {r_cnt} Red ({master_alignment_score:.1f}% readiness)."
            )

        upgrade_catalysts.append(
            f"Desk [P] / [A] / [0] Trigger Conditions: Closed 4H/1H reclaim candle above support (${target_support:,.0f}) "
            f"or sweep of Lower Long-Liq Magnet (${dn_mag:,.0f}) with +Spot CVD."
        )
        upgrade_catalysts.append(
            f"Invalidation / Hard Veto Conditions: Daily close below 1D Support (${pev.daily_support:,.0f}), "
            f"Desk [P] Tell-Tale 5x selling climax, or breach of Lower Long-Liq Magnet (${dn_mag:,.0f})."
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

        breached_30d_hvn = bool(sig.support_hvn and price < sig.support_hvn)
        if tp:
            if breached_30d_hvn and sig.support_hvn:
                cash_entry_zone_str = (
                    f"T1 (40%): ${tp.entry_zone_low:,.0f}–${tp.entry_zone_high:,.0f} (7D HVN/1D Sup) • "
                    f"T2 (60%): ${pev.long_liq_magnet_usd:,.0f} (Long-Liq Magnet) | "
                    f"TP1: ${sig.support_hvn:,.0f} (Overhead 30D HVN)"
                )
            elif sig.support_hvn and sig.support_hvn < sig.c_val:
                cash_entry_zone_str = (
                    f"T1: ${sig.c_val:,.0f} (30D cVAL) • T2: ${sig.support_hvn:,.0f} (30D HVN) "
                    f"(Active Bid: ${tp.entry_zone_low:,.0f}–${tp.entry_zone_high:,.0f} • Liq Floor: ${pev.long_liq_magnet_usd:,.0f})"
                )
            else:
                cash_entry_zone_str = (
                    f"${tp.entry_zone_low:,.0f} – ${tp.entry_zone_high:,.0f} (Liq Floor: ${pev.long_liq_magnet_usd:,.0f})"
                )
        else:
            cash_entry_zone_str = f"${target_support:,.0f} – ${pev.long_liq_magnet_usd:,.0f}"

        if supreme_veto:
            cash_trigger_instruction = f"VETO ({supreme_veto_reason_str[:32]}) -> Stay 100% Cash."
        elif breached_30d_hvn and sig.support_hvn:
            active_btc = cash_final_btc if cash_final_risk_pct > 0 else cash_edge_btc
            t1_btc = round(active_btc * 0.40, 4)
            t2_btc = round(active_btc * 0.60, 4)
            z_low = tp.entry_zone_low if tp else target_support
            z_high = tp.entry_zone_high if tp else target_support
            s_stop = tp.stop_loss if tp else pev.downside_ref_1d_atr
            cash_trigger_instruction = (
                f"30D HVN (${sig.support_hvn:,.0f}) breached -> "
                f"T1 (40%): {t1_btc:.4f} BTC @ ${z_low:,.0f}–${z_high:,.0f} (15m reclaim); "
                f"T2 (60%): {t2_btc:.4f} BTC @ ${pev.long_liq_magnet_usd:,.0f} "
                f"(Stop ${s_stop:,.0f} < 1D 200EMA/ATR; TP1 ${sig.support_hvn:,.0f} Overhead Supply)."
            )
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
        tab4_stop = active_cfg.computed_stop_usd if active_cfg else 0.0
        valid_stops = [s for s in (tab1_stop, tab4_stop) if 0 < s < price * 0.998]
        reconciled_stop = round(min(valid_stops), 2) if valid_stops else round(price * 0.985, 2)
        if pev.long_liq_magnet_usd > 0 and reconciled_stop >= (pev.long_liq_magnet_usd - 75.0) and price < sig.c_val:
            ema_200_1d = getattr(mev, "ema_200_1d", 0.0) if mev else 0.0
            deep_stops = [s for s in (ema_200_1d, pev.downside_ref_1d_atr) if 0 < s < (pev.long_liq_magnet_usd - 100.0)]
            if deep_stops:
                reconciled_stop = round(max(deep_stops) - 50.0, 2)
            else:
                reconciled_stop = round(pev.long_liq_magnet_usd - 450.0, 2)
        stop_source = f"Tab 1 Tactical: ${tab1_stop:,.0f} • Tab 4 Macro Floor: ${tab4_stop:,.0f} • 50D: ${pev.sma_50_1d:,.0f}"

        # Track B: Macro Spot Holder Targets (Multi-Day Swing / Reversion)
        raw_tp1_cands = [sig.c_poc, mev.ema_21_1d if mev else sig.c_poc]
        if breached_30d_hvn and sig.support_hvn:
            raw_tp1_cands.append(sig.support_hvn)
        macro_tp1_candidates = [c for c in raw_tp1_cands if c > price]
        holder_tp1_usd = round(min(macro_tp1_candidates), 2) if macro_tp1_candidates else round(max(sig.c_poc, price * 1.03), 2)
        if breached_30d_hvn and sig.support_hvn and abs(holder_tp1_usd - sig.support_hvn) < 5.0:
            holder_tp1_source = "Breached 30D HVN Overhead Supply"
        elif mev and abs(holder_tp1_usd - mev.ema_21_1d) < 5.0:
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
        elif config_category == "DEFENSIVE_CASH":
            holder_action = f"DEFENSIVE REDUCE / TIGHTEN STOP ({active_cfg.code.upper()})"
            holder_note = f"Trail hard stop tightly at ${reconciled_stop:,.0f} under {active_cfg.code}."
        elif "TAKE PARTIAL PROFIT" in pev.liq_magnet_verdict or (active_cfg is not None and active_cfg.code in ("Config D", "Config E")):
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
        elif active_cfg is None:
            master_light = "YELLOW"
            master_headline = "YELLOW LIGHT — NO-MATCH REGIME (SETUP STATE ONLY; OPERATOR DECIDES)"
        elif (
            sig.gate_state == ExecutionGateState.GATE3_RECLAIM_TRIGGERED
            and pev.buy_allowed == "YES"
            and config_category in ("BULL_LONG", "ACCUMULATE")
        ):
            master_light = "GREEN"
            master_headline = (
                f"GREEN LIGHT — SETUP STATE ONLY: MULTI-TAB BUY CONFLUENCE "
                f"({cash_final_btc:.4f} BTC / ${cash_final_usd:,.0f} SPOT SWING LONG). "
                "NOT an instruction or permission to place an order; operator decides."
            )
        elif (g_cnt + b_cnt) >= 2 and r_cnt == 0 and not sig.is_mid_range_chop:
            master_light = "BLUE"
            master_headline = (
                f"BLUE LIGHT — SETUP STATE ONLY: CONSTRUCTIVE MULTI-TAB ACCUMULATION ZONE "
                f"({cash_edge_btc:.4f} BTC reference size at ${ref_entry:,.0f} support). "
                "NOT an instruction or permission to place an order; operator decides."
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
            + (f"BTC (${price:,.0f}) is in {active_cfg.code} ({active_cfg.short_title}, {active_cfg.match_pct:.0f}% match) "
               if active_cfg else f"BTC (${price:,.0f}) regime: NO-MATCH — no active configuration qualifies. ")
            + f"with 4H Spot CVD {flow.w_4h.spot_delta_btc:+,.1f} BTC."
        )
        master_why = conflict_points[0]
        master_cmd = (
            "SETUP STATE ONLY — NOT an instruction or permission to place an order; operator decides. "
            f"[IF IN CASH]: {cash_permission} -> Zone ${tp.entry_zone_low if tp else ref_entry:,.0f}–${tp.entry_zone_high if tp else ref_entry:,.0f} "
            f"({cash_edge_btc:.4f} BTC / ${cash_edge_usd:,.0f}).  "
            f"[IF HOLDING SPOT]: {holder_action} | Stop ${reconciled_stop:,.0f} | TP1 ${holder_tp1_usd:,.0f} • TP2 ${holder_tp2_usd:,.0f}."
        )

        master_light = "RED" if decision_verdict == "NO_TRADE" else ("BLUE" if decision_verdict == "SETUP_FORMING" else "YELLOW")
        master_headline = f"{decision_verdict} — regime {config_code if active_cfg else 'NO_MATCH'}"
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
        # Kept as additive attributes to preserve the shared evaluation model API.
        ev.input_states = input_states
        ev.decision_verdict = decision_verdict
        ev.master_alignment_raw = round(raw_alignment, 1)
        ev.regime_code = config_code
        store.master_synthesis_evaluation = ev
        return ev
