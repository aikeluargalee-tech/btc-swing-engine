"""Pure DATA-ONLY report builders for all primary BTC Swing Engine tabs and the global [C: AI PACKET].

Design Rule:
  - Reports provide measurements, explicit reference formulas, and True/False condition values ONLY.
  - Zero verdicts, recommendations, or narrative interpretations.
  - Case-insensitive scan for forbidden words ('verdict', 'trade', 'wait', 'bullish', 'bearish',
    'confirmed', 'rejected', 'recommend') must return 0 matches across all generated reports,
     while reference sizing sections are explicitly labelled:
    "Reference calculation if entered at $X. Not an order."
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import os
import pathlib
import re
import sqlite3
import subprocess
import time
from typing import Callable, Dict, List, Optional, Tuple

from config.settings import DEFAULT_CONFIG, EngineConfig, RISK_BUDGET_MAX_PCT
from analytics.waterfall import (
    evaluate_waterfall,
    EDGE_TOLERANCE_PCT,
    RRR_MIN,
    STEALTH_SPOT_MAX_BTC,
    STEALTH_PERP_MIN_BTC,
    STEALTH_DIV_Z_MAX,
    CPI_PASS_MIN_USD,
    CPI_CAUTION_USD,
    CPI_VETO_USD,
    FUNDING_PASS_MAX_PCT,
    FUNDING_CROWDED_MIN_PCT,
    OI_CROWDED_MIN_PCT,
)
from core.state_store import StateStore

SGT_TZ = timezone(timedelta(hours=8))

FORBIDDEN_WORDS_REPLACEMENTS: Tuple[Tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"verdict", re.IGNORECASE), "status"),
    (re.compile(r"trader", re.IGNORECASE), "participant"),
    (re.compile(r"trade", re.IGNORECASE), "position"),
    (re.compile(r"awaiting", re.IGNORECASE), "pending"),
    (re.compile(r"await", re.IGNORECASE), "pending"),
    (re.compile(r"waiting", re.IGNORECASE), "pending"),
    (re.compile(r"wait", re.IGNORECASE), "standby"),
    (re.compile(r"bullish", re.IGNORECASE), "positive_slope"),
    (re.compile(r"bearish", re.IGNORECASE), "negative_slope"),
    (re.compile(r"unconfirmed", re.IGNORECASE), "false"),
    (re.compile(r"confirmed", re.IGNORECASE), "true"),
    (re.compile(r"rejected", re.IGNORECASE), "false"),
    (re.compile(r"recommendation", re.IGNORECASE), "metric"),
    (re.compile(r"recommend", re.IGNORECASE), "report"),
)


def sanitize_data_only_text(text: str) -> str:
    """Guarantees zero occurrences of forbidden interpretive words in any DATA-ONLY report."""
    out = text
    for pattern, repl in FORBIDDEN_WORDS_REPLACEMENTS:
        out = pattern.sub(repl, out)
    return out


def _timestamps_utc_sgt() -> Tuple[str, str]:
    now_utc = datetime.now(timezone.utc)
    now_sgt = now_utc.astimezone(SGT_TZ)
    return (
        now_utc.strftime("%Y-%m-%d %H:%M:%S UTC"),
        now_sgt.strftime("%Y-%m-%d %H:%M:%S SGT (UTC+8)"),
    )


def _spot_price(store: StateStore) -> float:
    px = float(getattr(store, "binance_spot_price", 0.0) or getattr(store, "spot_price", 0.0) or 0.0)
    if px <= 0 and getattr(store, "spot_klines_1h", None):
        px = float(store.spot_klines_1h[-1].close)
    return round(px, 2)


# ==============================================================================
# 1. TAB [P: STRUCTURE] DATA-ONLY REPORT
# ==============================================================================
def _demand_zone_label(liq_rep: object) -> str:
    """Renders the detector's ACTUAL demand-zone bounds.

    The report previously hardcoded "$75,000 - $78,000" while printing distances
    computed against a $63,000-$63,900 zone, so the label and the numbers described
    two different things (and the percentages read as impossible).
    """
    lo = float(getattr(liq_rep, "demand_zone_lower", 0.0) or 0.0)
    hi = float(getattr(liq_rep, "demand_zone_upper", 0.0) or 0.0)
    if lo > 0 and hi > 0:
        return f"${min(lo, hi):,.0f} - ${max(lo, hi):,.0f}"
    return "UNAVAILABLE"


def build_tab_p_data_only_report(config: Optional[EngineConfig], store: StateStore) -> str:
    cfg = config or DEFAULT_CONFIG
    ts_utc, ts_sgt = _timestamps_utc_sgt()
    spot_px = _spot_price(store)
    slsp = getattr(store, "slsp_evaluation", None)
    if slsp is None:
        from analytics.slsp_engine import SLSPEngine
        spot_1d = list(getattr(store, "spot_klines_1d", []) or [])
        bars_4h = list(getattr(store, "spot_klines_4h", []) or [])
        slsp = SLSPEngine(cfg).evaluate(store, spot_1d, bars_4h, current_price=spot_px)
    ema_snap = getattr(store, "ema_strategy", None)
    liq_rep = getattr(slsp, "liq_detector_report", None) if slsp else getattr(store, "liquidation_report", None)

    lines = [
        "# TAB [P: STRUCTURE] | DATA-ONLY METRICS REPORT",
        f"**Retrieval Time (UTC):** `{ts_utc}`  |  **Retrieval Time (SGT):** `{ts_sgt}`",
        f"**Spot Price (BTCUSDT):** `${spot_px:,.2f}`",
        "",
        "## 1. 5-REGIME RADAR DIAGNOSIS & MACRO SIZING",
        f"- **Active Market Regime:** `{slsp.macro_regime_name}` (ID: `{slsp.macro_regime_id}`)",
        f"- **Majority Voting Score:** `{slsp.macro_regime_score}`",
        f"- **Regime Diagnosis:** `{slsp.macro_regime_diagnosis}`",
        f"- **Macro Sizing Factor:** `{slsp.macro_sizing_factor:.2f}x`",
        f"- **Capital Rotation Directive:** `{slsp.macro_rotation}`",
        f"- **Macro Hard-Lock Cash Active:** `{slsp.macro_hard_lock_cash}`",
    ]
    if slsp.macro_hard_lock_cash and slsp.macro_lock_reason:
        lines.append(f"- **Macro Hard-Lock Reason:** `{slsp.macro_lock_reason}`")

    lines.extend([
        "",
        "## 2. DAILY SWING STRUCTURE & LIQUIDATION-BACKED KEY SHELVES (SLSP v1.0)",
        f"- **Daily Market Bias:** `{slsp.regime}`",
        f"- **Confluence Score:** `{slsp.confluence_score}/100`",
        f"- **Position State:** `{slsp.trade_state}`",
    ])
    supp = slsp.nearest_support
    res = slsp.nearest_resistance
    if supp is not None:
        s_center = round(float(supp.center_price), 2)
        s_diff_usd = round(spot_px - s_center, 2)
        s_diff_pct = round((s_diff_usd / s_center) * 100.0, 2) if s_center > 0 else 0.0
        lines.extend([
            f"- **Nearest Support Shelf Center:** `${s_center:,.2f}` (Band: `${supp.price_min:,.2f} - ${supp.price_max:,.2f}`)",
            f"- **Spot Minus Support Center (`Spot - Support`):** `${s_diff_usd:+,.2f}` (`{s_diff_pct:+.2f}%`)",
            f"- **Support Strength / Touches:** `{supp.strength}/5` | Touches: `{supp.touch_count}`",
            f"- **Support Is Round Number:** `{bool(supp.is_round_number)}` | **Support Is HVN:** `{bool(supp.is_hvn)}`",
            f"- **Support Liquidation Cluster Tag:** `{supp.liquidation_cluster_tag if supp.liquidation_cluster_tag else 'None'}`",
            f"- **Support Modeled OI-Ladder Pool USD:** `${supp.liquidation_volume_usd:,.2f}`",
        ])
    else:
        lines.append("- **Nearest Support Shelf Center:** `0.00` (No shelf within 10% scan window)")

    if res is not None:
        r_center = round(float(res.center_price), 2)
        r_diff_usd = round(r_center - spot_px, 2)
        r_diff_pct = round((r_diff_usd / spot_px) * 100.0, 2) if spot_px > 0 else 0.0
        lines.extend([
            f"- **Nearest Resistance Shelf Center:** `${r_center:,.2f}` (Band: `${res.price_min:,.2f} - ${res.price_max:,.2f}`)",
            f"- **Resistance Center Minus Spot (`Resistance - Spot`):** `${r_diff_usd:+,.2f}` (`{r_diff_pct:+.2f}%`)",
            f"- **Resistance Strength / Touches:** `{res.strength}/5` | Touches: `{res.touch_count}`",
            f"- **Resistance Liquidation Cluster Tag:** `{res.liquidation_cluster_tag if res.liquidation_cluster_tag else 'None'}`",
            f"- **Resistance Modeled OI-Ladder Pool USD:** `${res.liquidation_volume_usd:,.2f}`",
        ])
    else:
        lines.append("- **Nearest Resistance Shelf Center:** `0.00` (No shelf within 10% scan window)")

    lines.extend([
        "",
        "## 3. LIQUIDATION GRAVITATIONAL HORIZON & LSCE SWEEP ENGINE",
        f"- **Dominant Gravitational Pull:** `{slsp.dominant_pull_dir}`",
        f"- **Immediate Tier (100x) Imbalance Ratio:** `{slsp.immediate_ratio:.2f}x`",
        f"- **Total Ladder (10x-100x) Imbalance Ratio:** `{slsp.total_ladder_ratio:.2f}x`",
        f"- **Upper Liquidation Magnet Cluster:** `${slsp.upper_magnet_price:,.2f}` (`{slsp.upper_magnet_dist_pct:+.2f}%` from Spot) | Modeled OI-Ladder Pool: `${slsp.upper_magnet_vol_usd / 1e6:.2f}M`",
        f"- **Lower Liquidation Magnet Cluster:** `${slsp.lower_magnet_price:,.2f}` (`{slsp.lower_magnet_dist_pct:+.2f}%` from Spot) | Modeled OI-Ladder Pool: `${slsp.lower_magnet_vol_usd / 1e6:.2f}M`",
        f"- **LSCE Sweep State:** `[{slsp.lsce_status}]`",
        f"- **LSCE Cluster Tested:** `{slsp.lsce_cluster_tested}`",
        f"- **LSCE Action Verdict:** `{slsp.lsce_action_verdict}`",
    ])

    setup = slsp.active_setup
    ref_entry = round(float(setup.entry_price), 2) if (setup and setup.entry_price > 0) else spot_px
    ref_stop = (
        round(float(slsp.structural_stop_price), 2)
        if slsp.structural_stop_price > 0
        else (round(float(setup.stop_loss), 2) if (setup and setup.stop_loss > 0) else round(spot_px * 0.98, 2))
    )
    stop_dist = round(ref_entry - ref_stop, 2)
    ref_1_5r = round(ref_entry + 1.5 * stop_dist, 2) if stop_dist > 0 else 0.0
    ref_2_5r = round(ref_entry + 2.5 * stop_dist, 2) if stop_dist > 0 else 0.0
    obs_r = round(float(setup.obstacle_r), 2) if setup else 0.0
    clearance_ok = bool(not setup.obstacle_detected) if setup else False
    sized_btc = round(float(setup.position_size_btc), 4) if setup else 0.0
    notional_usd = round(float(setup.notional_value_usd), 2) if setup else 0.0
    max_tranche_btc = float(getattr(cfg, "slsp_max_position_btc", 0.0) or 0.0)
    cap_note = f", Cap {max_tranche_btc:.2f} BTC" if max_tranche_btc > 0 else ""

    lines.extend([
        "",
        f"## 4. REFERENCE LEVELS & DUAL INVIOLABLE STOPS (Reference calculation if entered at ${ref_entry:,.2f})",
        f"- **Reference Entry Price:** `${ref_entry:,.2f}`",
        f"- **Structural Stop Loss (4H swing low or shelf floor - ATR):** `${slsp.structural_stop_price:,.2f}` (`{slsp.structural_stop_dist_pct:.2f}%` from Spot)",
        f"- **Disaster Hard Stop (Below 200 SMA & 25x Shelf):** `${slsp.disaster_stop_price:,.2f}` (`{slsp.disaster_stop_dist_pct:.2f}%` from Spot)",
        f"- **Risk Budget Compliance Pass (<= {RISK_BUDGET_MAX_PCT}%):** `{bool(slsp.disaster_stop_dist_pct <= RISK_BUDGET_MAX_PCT)}`",
        f"- **Stop Distance (`Reference Entry - Structural Stop`):** `${stop_dist:,.2f}`",
        f"- **1.5R Reference Level (`Entry + 1.5 * Stop Distance`):** `${ref_1_5r:,.2f}`",
        f"- **2.5R Reference Level (`Entry + 2.5 * Stop Distance`):** `${ref_2_5r:,.2f}`",
        f"- **Distance to Overhead Resistance in R (`Obstacle R`):** `{obs_r:.2f}R`",
        f"- **Clearance >= 1.50R (`Obstacle R >= 1.50`):** `{clearance_ok}`",
        f"- **Sized Position (Macro Sized {slsp.macro_sizing_factor:.2f}x{cap_note}):** `{sized_btc:.4f} BTC` (`${notional_usd:,.2f}` notional)",
        "",
        "## 5. DAILY & 4H 3-EMA METRICS",
        f"- **1D EMA20 / EMA50 / EMA200:** `${ (ema_snap.daily_ema_20 if ema_snap else 0.0):,.2f}` / `${ (ema_snap.daily_ema_50 if ema_snap else 0.0):,.2f}` / `${ (ema_snap.daily_ema_200 if ema_snap else 0.0):,.2f}`",
        f"- **1D EMA200 5-Day Slope (%):** `{slsp.ema_3_slope_200:+.3f}%`",
        f"- **1D ADX(14):** `{slsp.ema_3_adx:.2f}` | **ADX(14) >= 20.0:** `{bool(slsp.ema_3_adx >= 20.0)}`",
        f"- **4H EMA9 / EMA20 / EMA50:** `${ (ema_snap.ema_4h_9 if ema_snap else 0.0):,.2f}` / `${ (ema_snap.ema_4h_20 if ema_snap else 0.0):,.2f}` / `${ (ema_snap.ema_4h_50 if ema_snap else 0.0):,.2f}`",
        f"- **Spot Inside 4H [EMA20, EMA50] Value Band:** `{bool(slsp.ema_3_value_zone_active)}`",
        f"- **4H Wick Condition Met (Last 3 Closed 4H Bars):** `{bool(ema_snap.rejection_active) if ema_snap else False}`",
        f"- **4H Close > 4H EMA9:** `{bool(ema_snap.trigger_active) if ema_snap else False}`",
        f"- **Positioning Sub-Conditions Met Count:** `{slsp.ema_3_positioning_met} / 3`",
        "",
        "## 6. LIQUIDATION FLUSH & VOLUME CLIMAX SENSORS",
        f"- **1H OI Delta (%):** `{slsp.liq_flush_oi_delta:+.2f}%`",
        (
            f"- **15m Relative Volume (`RelVol vs 20-bar SMA`):** `{slsp.tell_tale_relvol_15m:.2f}x` | **15m RelVol >= 5.0x:** `{bool(slsp.tell_tale_relvol_15m >= 5.0)}`"
            if slsp.tell_tale_relvol_15m > 0
            else "- **15m Relative Volume (`RelVol vs 20-bar SMA`):** `DATA UNAVAILABLE`"
        ),
        (
            f"- **5m Relative Volume (`RelVol vs 20-bar SMA`):** `{slsp.tell_tale_relvol_5m:.2f}x` | **5m RelVol >= 5.0x:** `{bool(slsp.tell_tale_relvol_5m >= 5.0)}`"
            if slsp.tell_tale_relvol_5m > 0
            else "- **5m Relative Volume (`RelVol vs 20-bar SMA`):** `DATA UNAVAILABLE`"
        ),
        f"- **Volume Climax Interlock Active:** `{bool(slsp.tell_tale_veto)}`",
    ])
    liq_avail = bool(liq_rep is not None and getattr(liq_rep, "is_available", False))
    liq_stale = bool(liq_rep is not None and getattr(liq_rep, "is_stale", False))
    if liq_avail:
        w15 = liq_rep.windows.get("15m")
        w1h = liq_rep.windows.get("1h")
        w4h = liq_rep.windows.get("4h")
        w24h = liq_rep.windows.get("24h")
        stale_tag = " [STALE / CACHED]" if liq_stale else ""
        upd_ts = getattr(liq_rep, "timestamp_utc", "") or "live"
        feed_status_str = (
            f"STALE (Local Companion Cached — Updated {upd_ts})"
            if liq_stale
            else f"ONLINE (Local Companion Binance USD-M forceOrder WS; <=1 evt/s sample — Updated {upd_ts})"
        )
        lines.extend([
            f"- **Companion Liquidation Feed Status:** `{feed_status_str}`",
            f"- **Liquidated USD (`15m / 1h / 4h / 24h`):** `${(w15.total_usd if w15 else 0.0):,.0f}` / `${(w1h.total_usd if w1h else 0.0):,.0f}` / `${(w4h.total_usd if w4h else 0.0):,.0f}` / `${(w24h.total_usd if w24h else 0.0):,.0f}{stale_tag}`",
            f"- **24H Liquidation Multiple:** `{liq_rep.liquidation_multiple_24h:.2f}x{stale_tag}`",
            f"- **Reference Zone (`{_demand_zone_label(liq_rep)}`) Distance to Lower / Upper:** `{liq_rep.demand_zone_dist_lower_pct:+.2f}%` / `{liq_rep.demand_zone_dist_upper_pct:+.2f}%`",
        ])
    else:
        lines.extend([
            "- **Companion Liquidation Feed Status:** `DATA UNAVAILABLE`",
            "- **Liquidated USD (`15m / 1h / 4h / 24h`):** `DATA UNAVAILABLE`",
        ])

    recon_eval = getattr(store, "reconciliation_evaluation", None)
    if recon_eval is not None:
        gate_str = (
            "PASS (Feeds Aligned — No Veto)"
            if recon_eval.execution_authorization == "AUTHORIZED"
            else "VETO / LOCKOUT (Data Mismatch)"
        )
        gate_status = str(recon_eval.trading_status).replace("EXECUTION AUTHORIZED", "FEEDS_ALIGNED_NO_LOCKOUT")
        effective_alloc = (
            0.0
            if slsp.macro_hard_lock_cash
            else min(float(recon_eval.capital_allocation), float(slsp.macro_sizing_factor))
        )
        effective_target = (
            "100% USDT (Macro Hard-Lock Active)"
            if slsp.macro_hard_lock_cash
            else recon_eval.target_allocation
        )
        effective_rotation = slsp.macro_rotation if slsp.macro_hard_lock_cash else recon_eval.portfolio_rotation
        lines.extend([
            "",
            "## 7. UPSTREAM DATA INTEGRITY RECONCILIATION GATE",
            f"- **Reconciliation Verdict:** `{recon_eval.verdict}`",
            f"- **Cross-Feed Data Integrity Gate:** `{gate_str}`",
            f"- **Reconciliation Gate Status:** `{gate_status}`",
            f"- **Prescribed Capital Allocation:** `{effective_alloc:.2f}x` (`{effective_target}`)",
            f"- **Portfolio Rotation Directive:** `{effective_rotation}`",
            f"- **Module A (Ladder Math):** `{'PASS' if recon_eval.ladder_check_passed else 'FAIL'}` | **Module D (LSCE Proof):** `{'PASS' if recon_eval.lsce_check_passed else 'FAIL'}`",
        ])
        if recon_eval.fail_reasons:
            lines.append(f"- **Lockout Directive:** `{recon_eval.fail_reasons[0]}`")
        elif recon_eval.warnings:
            lines.append(f"- **Active Warning:** `{recon_eval.warnings[0]}`")

    return sanitize_data_only_text("\n".join(lines))


# ==============================================================================
# 3. TAB [G: GROK FLOW] DATA-ONLY REPORT
# ==============================================================================
def build_tab_g_data_only_report(config: Optional[EngineConfig], store: StateStore) -> str:
    ts_utc, ts_sgt = _timestamps_utc_sgt()
    grok = getattr(store, "grok_quant_evaluation", None)
    if grok is None:
        from analytics.grok_quant_engine import GrokQuantEngine
        grok = GrokQuantEngine().evaluate(store)

    spot_px = round(float(grok.spot_price), 2)
    vwap = round(float(grok.vwap_daily), 2)
    sd1_u = round(float(grok.vwap_sd1_upper), 2)
    sd2_u = round(float(grok.vwap_sd2_upper), 2)
    sd1_l = round(float(grok.vwap_sd1_lower), 2)
    sd2_l = round(float(grok.vwap_sd2_lower), 2)
    sigma = round(float(grok.vwap_sigma), 2)
    spot_vs_vwap_usd = round(spot_px - vwap, 2) if vwap > 0 else 0.0
    spot_vs_vwap_pct = round((spot_vs_vwap_usd / vwap) * 100.0, 2) if vwap > 0 else 0.0

    ema50_1d = round(float(grok.ema_50_1d), 2)
    sma200_1d = round(float(grok.sma_200_1d), 2)
    spot_vs_ema50_usd = round(spot_px - ema50_1d, 2) if ema50_1d > 0 else 0.0
    spot_vs_ema50_pct = round((spot_vs_ema50_usd / ema50_1d) * 100.0, 2) if ema50_1d > 0 else 0.0
    spot_vs_sma200_usd = round(spot_px - sma200_1d, 2) if sma200_1d > 0 else 0.0
    spot_vs_sma200_pct = round((spot_vs_sma200_usd / sma200_1d) * 100.0, 2) if sma200_1d > 0 else 0.0

    lines = [
        "# TAB [G: GROK FLOW] | DATA-ONLY METRICS REPORT",
        f"**Retrieval Time (UTC):** `{ts_utc}`  |  **Retrieval Time (SGT):** `{ts_sgt}`",
        f"**Spot Price (BTCUSDT):** `${spot_px:,.2f}`",
        "",
        "## 1. 00:00 UTC ANCHORED VWAP & STANDARD DEVIATION BANDS",
        f"- **00:00 UTC Anchored VWAP:** `${vwap:,.2f}`",
        f"- **1.0 SD Dispersion (`Sigma`):** `${sigma:,.2f}`",
        f"- **Spot Minus VWAP (`Spot - VWAP`):** `${spot_vs_vwap_usd:+,.2f}` (`{spot_vs_vwap_pct:+.2f}%` | Stretch Z-Score: `{grok.vwap_stretch_z:+.2f} SD`)",
        f"- **+2.0 SD Upper Band:** `${sd2_u:,.2f}` | **Spot > +2.0 SD:** `{bool(spot_px > sd2_u)}`",
        f"- **+1.0 SD Upper Band:** `${sd1_u:,.2f}` | **Spot > +1.0 SD:** `{bool(spot_px > sd1_u)}`",
        f"- **-1.0 SD Lower Band:** `${sd1_l:,.2f}` | **Spot < -1.0 SD:** `{bool(spot_px < sd1_l)}`",
        f"- **-2.0 SD Lower Band:** `${sd2_l:,.2f}` | **Spot < -2.0 SD:** `{bool(spot_px < sd2_l)}`",
        f"- **Spot Inside [-1.0 SD, +1.0 SD] Band:** `{bool(sd1_l <= spot_px <= sd1_u)}`",
        "",
        "## 2. DAILY & INTRADAY MOVING AVERAGES & SESSION EXTREMES",
        f"- **1H EMA9 / 1H EMA21:** `${grok.ema_9:,.2f}` / `${grok.ema_21:,.2f}` | **1H EMA9 > 1H EMA21:** `{bool(grok.ema_9 > grok.ema_21)}`",
        f"- **1D EMA50:** `${ema50_1d:,.2f}` | **Spot Minus 1D EMA50:** `${spot_vs_ema50_usd:+,.2f}` (`{spot_vs_ema50_pct:+.2f}%`) | **Spot > 1D EMA50:** `{bool(spot_px > ema50_1d)}`",
        f"- **1D SMA200:** `${sma200_1d:,.2f}` | **Spot Minus 1D SMA200:** `${spot_vs_sma200_usd:+,.2f}` (`{spot_vs_sma200_pct:+.2f}%`) | **Spot > 1D SMA200:** `{bool(spot_px > sma200_1d)}`",
        f"- **Current Day High / Low:** `${grok.day_high:,.2f}` / `${grok.day_low:,.2f}`",
        f"- **Previous Day High / Low:** `${grok.prev_day_high:,.2f}` / `${grok.prev_day_low:,.2f}`",
        "",
        "## 3. DERIVATIVES POSITIONING & LIQUIDATION CLUSTERS",
        f"- **Open Interest:** `{grok.open_interest_btc:,.2f} BTC` (`${grok.open_interest_usd:,.0f}`)",
        f"- **OI Change (`1H / 4H`):** `{grok.oi_change_1h_pct:+.2f}%` / `{grok.oi_change_4h_pct:+.2f}%` | **4H OI Change > 0:** `{bool(grok.oi_change_4h_pct > 0)}`",
        f"- **8H Perpetual Funding Rate:** `{grok.funding_rate_pct:+.4f}%` | **Funding Rate <= 0.0100%:** `{bool(grok.funding_rate_pct <= 0.01)}`",
        f"- **Top Participant L/S Ratio:** `{grok.top_trader_ls_ratio:.2f}` (`{grok.top_trader_long_pct:.1f}%` Long / `{grok.top_trader_short_pct:.1f}%` Short)",
        f"- **Global Account L/S Ratio:** `{grok.global_account_ls_ratio:.2f}` | **Global L/S >= 2.00:** `{bool(grok.global_account_ls_ratio >= 2.0)}`",
        f"- **Overhead Short Liquidation Cluster:** `${grok.overhead_short_liq_pool:,.2f}` (`${grok.overhead_short_liq_usd/1e6:.1f}M`)",
        f"- **Downside Long Liquidation Cluster:** `${grok.downside_long_liq_pool:,.2f}` (`${grok.downside_long_liq_usd/1e6:.1f}M`)",
        "",
        "## 4. MULTI-HORIZON CVD & COINBASE PREMIUM",
        f"- **24H CVD (`Spot vs Perp`):** Spot `{grok.spot_cvd_24h:+,.2f} BTC` | Perp `{grok.futures_cvd_24h:+,.2f} BTC` | `Spot CVD 24H > 0`: `{bool(grok.spot_cvd_24h > 0)}` | `Spot CVD 24H > Perp CVD 24H`: `{bool(grok.spot_cvd_24h > grok.futures_cvd_24h)}`",
        f"- **4H CVD (`Spot vs Perp`):** Spot `{grok.spot_cvd_4h:+,.2f} BTC` | Perp `{grok.futures_cvd_4h:+,.2f} BTC` | `Spot CVD 4H > 0`: `{bool(grok.spot_cvd_4h > 0)}`",
        f"- **15m CVD (`Spot vs Perp`):** Spot `{grok.spot_cvd_15m:+,.2f} BTC` | Perp `{grok.futures_cvd_15m:+,.2f} BTC` | `Spot CVD 15m > 0`: `{bool(grok.spot_cvd_15m > 0)}`",
        f"- **Coinbase Premium (`USD / % / Z-Score`):** `${grok.coinbase_premium_usd:+,.2f}` (`{grok.coinbase_premium_pct:+.4f}%` | `Z = {grok.coinbase_premium_zscore:+.2f}`) | **Coinbase Premium > 0:** `{bool(grok.coinbase_premium_pct > 0)}`",
    ]
    return sanitize_data_only_text("\n".join(lines))


# ==============================================================================
# 4. TAB [R: SSRN RESEARCH] DATA-ONLY REPORT
# ==============================================================================
def build_tab_r_data_only_report(config: Optional[EngineConfig], store: StateStore) -> str:
    ts_utc, ts_sgt = _timestamps_utc_sgt()
    ssrn = getattr(store, "ssrn_alpha_evaluation", None)
    if ssrn is None:
        from analytics.ssrn_research_engine import SSRNResearchEngine
        ssrn = SSRNResearchEngine(config or DEFAULT_CONFIG).evaluate(store)

    spot_px = round(float(ssrn.spot_price), 2)
    lines = [
        "# TAB [R: SSRN RESEARCH] | DATA-ONLY METRICS REPORT",
        f"**Retrieval Time (UTC):** `{ts_utc}`  |  **Retrieval Time (SGT):** `{ts_sgt}`",
        f"**Spot Price (BTCUSDT):** `${spot_px:,.2f}`",
        "",
        "## 1. EMPIRICAL FACTOR & GATE METRICS",
        f"- **1D MACD Gate Pass (`1D MACD > Signal or Hist > 0`):** `{bool(ssrn.mtf_macd_gate_pass)}`",
        f"- **20-Day Annualized Realized Volatility (%):** `{ssrn.realized_vol_20d_ann:.2f}%`",
        f"- **20-Day Realized Variance:** `{ssrn.live_realized_variance:.4f}`",
        f"- **20-Day Log-Return Skewness:** `{ssrn.live_skewness_20d:+.2f}`",
        f"- **25% Volatility-Target Reference Weight (%):** `{ssrn.target_vol_sizing_pct:.1f}%`",
        f"- **8H Equivalent ATR14 (`ATR14_4H * sqrt(2)`):** `${ssrn.atr_14_8h:,.2f}`",
        f"- **2.5x 8H ATR Reference Stop Distance:** `${ssrn.atr_trailing_stop_dist:,.2f}`",
        f"- **Annualized Perpetual Funding Rate (%/yr):** `{ssrn.annualized_funding_pct:+.2f}%/yr`",
        f"- **Annualized Funding <= 30.0%/yr:** `{bool(ssrn.annualized_funding_pct <= 30.0)}`",
        f"- **Round-Trip Friction Assumption:** `{ssrn.round_trip_friction_bps:.1f} bps` (`Cost Hurdle Pass`: `{bool(ssrn.cost_hurdle_pass)}`)",
        f"- **Order Book Imbalance (`1% Depth Ratio`):** `{ssrn.live_obi_ratio_pct:+.1f}%`",
        f"- **4H Spot CVD Delta:** `{ssrn.live_4h_cvd_delta:+.2f} BTC`",
        f"- **MVRV Proxy Ratio (`Spot / (0.62 * 1D SMA200)`):** `{ssrn.live_mvrv_ratio:.2f}`",
        f"- **SOPR Proxy Ratio:** `{ssrn.live_sopr_level:.4f}`",
        "",
        "## 2. 5 SSRN MODEL CONDITION BOOLEANS",
    ]
    for m in ssrn.models:
        lines.append(
            f"- **{m.name} (`{m.ssrn_citation}` | `{m.timeframe}`):** "
            f"Condition Pass: `{bool(m.is_gate_pass)}` | Measured Value: `{m.live_value}`"
        )

    lines.extend([
        "",
        "## 3. 5 EMPIRICAL DOMAIN TELEMETRY",
    ])
    for d in ssrn.domains:
        lines.append(f"- **{d.title}:** `{d.live_metric_val}` (Core Metrics: `{', '.join(d.core_metrics)}`)")

    return sanitize_data_only_text("\n".join(lines))


# ==============================================================================
# 5. TAB [M: MAGNET] DATA-ONLY REPORT
# ==============================================================================
def build_tab_m_data_only_report(
    config: Optional[EngineConfig],
    store: StateStore,
    *,
    recompute: bool = False,
) -> str:
    from analytics.btc_magnet_engine import get_or_recompute_btc_magnet

    ts_utc, ts_sgt = _timestamps_utc_sgt()
    mag, _did_recompute = get_or_recompute_btc_magnet(config or DEFAULT_CONFIG, store, recompute=recompute)

    if mag is None:
        lines = [
            "# TAB [M: MAGNET] | DATA-ONLY METRICS REPORT",
            f"**Retrieval Time (UTC):** `{ts_utc}`  |  **Retrieval Time (SGT):** `{ts_sgt}`",
            "**Status:** `DATA UNAVAILABLE`",
            "",
            "- **Stored Evaluation:** `UNAVAILABLE` (no `btc_magnet_evaluation` in StateStore; call `SignalDetector.evaluate` or pass `recompute=True` explicitly)",
            "- **Spot Price (BTCUSDT):** `UNAVAILABLE`",
            "- **Liquidation Map Source:** `UNAVAILABLE`",
            "- **Recommended Spot Sizing:** `0.00x` (`Remain USDT`)",
        ]
        return sanitize_data_only_text("\n".join(lines))

    prov_dict = getattr(mag, "input_provenance", None) or {}
    spot_avail = bool(getattr(mag, "spot_available", False)) or float(getattr(mag, "spot_price", 0.0) or 0.0) > 0.0
    spot_px = round(float(mag.spot_price), 2) if spot_avail else 0.0
    chg_avail = bool(getattr(mag, "price_change_24h_available", False)) or (
        "price_change_24h" not in prov_dict and float(getattr(mag, "price_change_24h_pct", 0.0) or 0.0) != 0.0
    )
    funding_avail = bool(getattr(mag, "funding_available", False)) or (
        "funding_rate" not in prov_dict and float(getattr(mag, "funding_rate_annual_pct", 0.0) or 0.0) != 0.0
    )
    oi_avail = bool(getattr(mag, "oi_available", False)) or (
        "oi_delta_4h" not in prov_dict and float(getattr(mag, "oi_delta_4h_pct", 0.0) or 0.0) != 0.0
    )

    up_px = round(float(mag.upper_magnet.price), 2)
    lo_px = round(float(mag.lower_magnet.price), 2)
    up_diff_usd = round(up_px - spot_px, 2)
    lo_diff_usd = round(lo_px - spot_px, 2)
    passed_count = sum(1 for r in mag.rule_checks[:6] if r.passed)

    m_keys = [k for k, v in prov_dict.items() if v.startswith("MEASURED") or v in ("LIVE_EDGEORNOT", "CACHED_LIQMAP")]
    d_keys = [k for k, v in prov_dict.items() if v.startswith("DERIVED")]
    e_keys = [k for k, v in prov_dict.items() if "MODELLED" in v or "ESTIMATED" in v]
    u_keys = [k for k, v in prov_dict.items() if v == "UNAVAILABLE"]

    spot_str = f"`${spot_px:,.2f}`" if spot_avail and spot_px > 0.0 else "`UNAVAILABLE`"
    chg_str = f"`24H Change: {mag.price_change_24h_pct:+.2f}%`" if chg_avail else "`24H Change: UNAVAILABLE`"
    liqmap_src = getattr(mag, "liqmap_source", "UNAVAILABLE")
    liqmap_err = getattr(mag, "liqmap_error", "")
    eval_origin = getattr(mag, "evaluation_origin", "STORED")

    lines = [
        "# TAB [M: MAGNET] | DATA-ONLY METRICS REPORT",
        f"**Retrieval Time (UTC):** `{ts_utc}`  |  **Retrieval Time (SGT):** `{ts_sgt}`",
        f"**Evaluation Timestamp (UTC):** `{mag.timestamp_utc or 'UNAVAILABLE'}`  |  **Origin:** `{eval_origin}`",
        f"**Spot Price (BTCUSDT):** {spot_str} ({chg_str})",
        f"**Liquidation Map Source:** `{liqmap_src}`" + (f" (`{liqmap_err}`)" if liqmap_err else ""),
        (
            f"**Input Provenance Tally:** `Measured ({len(m_keys)}): {', '.join(m_keys) or 'none'}` | "
            f"`Derived ({len(d_keys)}): {', '.join(d_keys) or 'none'}` | "
            f"`Modelled/Est ({len(e_keys)}): {', '.join(e_keys) or 'none'}` | "
            f"`Unavailable ({len(u_keys)}): {', '.join(u_keys) or 'none'}`"
        ),
        "",
        "## 1. 5-REGIME RADAR DIAGNOSIS & MAJORITY VOTING",
        f"- **Active Market Regime:** `{mag.regime_name}` (ID: `{mag.regime_id}`)",
        f"- **Majority Voting Score:** `{mag.majority_score}` (`{mag.majority_matches_count}/4 Observations Confirmed`)",
        f"- **Regime Diagnosis:** `{mag.regime_diagnosis}`",
        f"- **Conflicted Signal Demoted to Mixed:** `{mag.is_conflicted}`",
    ]
    if mag.is_conflicted and mag.conflict_reason:
        lines.append(f"- **Conflict Reason:** `{mag.conflict_reason}`")
    lines.append("- **Verified On-Exchange Positioning Observations:**")
    for obs, passed in mag.all_observations:
        lines.append(f"  * `{obs}`: `{bool(passed)}`")

    up_src = getattr(mag.upper_magnet, "source", "UNAVAILABLE")
    lo_src = getattr(mag.lower_magnet, "source", "UNAVAILABLE")
    up_line = (
        f"- **Upper Liquidation Cluster (Short Liquidations):** `${up_px:,.2f}` (`{mag.upper_magnet.dist_pct:+.2f}%` / `${up_diff_usd:+,.2f}` from Spot) | Volume: `${mag.upper_magnet.usd_volume/1e6:.2f}M` | Source: `{up_src}`"
        if spot_avail and up_px > 0.0
        else "- **Upper Liquidation Cluster (Short Liquidations):** `UNAVAILABLE`"
    )
    lo_line = (
        f"- **Lower Liquidation Cluster (Long Liquidations):** `${lo_px:,.2f}` (`{mag.lower_magnet.dist_pct:+.2f}%` / `${lo_diff_usd:+,.2f}` from Spot) | Volume: `${mag.lower_magnet.usd_volume/1e6:.2f}M` | Source: `{lo_src}`"
        if spot_avail and lo_px > 0.0
        else "- **Lower Liquidation Cluster (Long Liquidations):** `UNAVAILABLE`"
    )

    lines.extend([
        "",
        "## 2. LIQUIDATION GRAVITATIONAL HORIZON & DUAL-LADDER DEPTH",
        up_line,
        f"- **Center Spot Price:** {spot_str}",
        lo_line,
        f"- **Immediate Tier (100x) Imbalance Ratio:** `{mag.immediate_ratio:.2f}x` (${mag.immediate_l_vol:.1f}M Lower vs ${mag.immediate_u_vol:.1f}M Upper)",
        f"- **Total Ladder (10x-100x, MODELLED) Imbalance Ratio:** `{mag.total_ladder_ratio:.2f}x` (${mag.total_l_vol:.1f}M Lower vs ${mag.total_u_vol:.1f}M Upper)",
        f"- **Dominant Pull Direction:** `{mag.pull_direction}`",
        "",
        "## 3. LIQUIDATION SWEEP CONFIRMATION ENGINE (LSCE)",
        f"- **LSCE State:** `[{mag.lsce_status}]`",
        f"- **Cluster Tested:** `{mag.lsce_cluster_tested}`",
        f"- **Sweep Depth Pct:** `{mag.lsce_sweep_depth_pct:+.2f}%`",
        f"- **Reclaim Target Level:** `{f'${mag.lsce_reclaim_level:,.2f}' if mag.lsce_reclaim_level > 0 else 'UNAVAILABLE'}`",
        f"- **Spot Absorption Readout:** `{mag.lsce_spot_absorption}`",
        f"- **LSCE Action Verdict:** `{mag.lsce_action_verdict}`",
        "",
        "## 4. INVIOLABLE RISK DIRECTIVES & CAPITAL SIZING (SPOT ONLY, CAP <= 1.00x)",
        f"- **Recommended Spot Sizing:** `{mag.sizing_factor:.2f}x` ({mag.action})",
        f"- **Capital Rotation Directive:** `{mag.rotation}`",
        (
            f"- **Entry Instruction:** `{mag.entry_instruction}`"
            if (mag.verdict == "SPEAK" and getattr(mag, "reconciliation_auth", "AUTHORIZED") != "DENIED")
            else f"- **Entry Instruction:** `NO ENTRY DIRECTIVE (Verdict: {mag.verdict})`"
        ),
        (
            f"- **Structural Invalidation Stop (24H Low -0.2%):** `${mag.structural_stop_price:,.2f}` (`{mag.structural_stop_dist_pct:.2f}%` from Spot)"
            if mag.structural_stop_price > 0.0
            else "- **Structural Invalidation Stop (24H Low -0.2%):** `UNAVAILABLE`"
        ),
        (
            f"- **Disaster Hard Stop ({'200D SMA & Shelf' if getattr(mag, 'ma_200d_available', False) else 'Swing/Liq Shelf; 200D SMA UNAVAILABLE'}):** `${mag.disaster_stop_price:,.2f}` (`{mag.disaster_stop_dist_pct:.2f}%` from Spot)"
            if mag.disaster_stop_price > 0.0
            else "- **Disaster Hard Stop:** `UNAVAILABLE`"
        ),
        f"- **Risk Budget Compliance Pass (<= {RISK_BUDGET_MAX_PCT}%):** `{mag.risk_budget_pass}`",
        "",
        "## 5. DERIVATIVES & VOLATILITY INPUTS",
        f"- **Annualized Perpetual Funding Rate:** `{f'{mag.funding_rate_annual_pct:+.2f}%/yr' if funding_avail else 'UNAVAILABLE'}`",
        f"- **4H Open Interest Delta:** `{f'{mag.oi_delta_4h_pct:+.2f}%' if oi_avail else 'UNAVAILABLE'}`",
        f"- **24H Classification Label:** `{mag.market_regime}`",
        "",
        "## 6. 7 INTERNAL CONDITION BOOLEANS (TRUE/FALSE)",
    ])
    for r in mag.rule_checks:
        lines.append(f"- **Rule {r.rule_num} (`{r.name}`):** `{bool(r.passed)}` (`{r.detail}`)")
    lines.append(f"- **Conditions 1-6 True Count:** `{passed_count} / 6`")

    recon_eval = getattr(store, "reconciliation_evaluation", None)
    if recon_eval is None and mag is not None:
        from analytics.reconciliation_engine import ReconciliationEngine
        b1_input = getattr(store, "b1_telemetry_snapshot", None) or getattr(store, "b1_raw_telemetry", None)
        recon_eval = ReconciliationEngine().reconcile(b1_input, mag, store=store)
        store.reconciliation_evaluation = recon_eval

    if recon_eval is not None:
        gate_str = (
            "PASS (Feeds Aligned — No Veto)"
            if recon_eval.execution_authorization == "AUTHORIZED"
            else "VETO / LOCKOUT (Data Mismatch)"
        )
        gate_status = str(recon_eval.trading_status).replace("EXECUTION AUTHORIZED", "FEEDS_ALIGNED_NO_LOCKOUT")
        lines.extend([
            "",
            "## 7. B1 vs B2 DATA INTEGRITY RECONCILIATION AUDIT",
            f"- **Reconciliation Verdict:** `{recon_eval.verdict}`",
            f"- **Cross-Feed Data Integrity Gate:** `{gate_str}`",
            f"- **Prescribed Capital Sizing:** `{recon_eval.capital_allocation:.2f}x` ({gate_status})",
            f"- **Portfolio Rotation Directive:** `{recon_eval.portfolio_rotation}`",
            f"- **Target Capital Allocation:** `{recon_eval.target_allocation}`",
            "- **Mandatory Module Verification:**",
            f"  * `Module A (Ladder Math Consistency)`: `{'PASS' if recon_eval.ladder_check_passed else 'FAIL'}` ({recon_eval.ladder_details})",
            f"  * `Module B (Funding Carry Normalization)`: `{'PASS' if recon_eval.funding_check_passed else 'FAIL'}` ({recon_eval.funding_details})",
            f"  * `Module C (Cluster Geometry & Horizon)`: `{'PASS' if recon_eval.geometry_check_passed else 'FAIL'}` ({recon_eval.geometry_details})",
            f"  * `Module D (LSCE Sweep Proof & Rotation)`: `{'PASS' if recon_eval.lsce_check_passed else 'FAIL'}` ({recon_eval.lsce_details})",
            f"  * `Module E (Snapshot Synchronization)`: `{'PASS' if recon_eval.freshness_check_passed else 'FAIL'}` ({recon_eval.freshness_details})",
        ])
        if recon_eval.discrepancy_table:
            lines.extend([
                "",
                "### Discrepancy & Reconciliation Table",
                "| Metric | B1 Value | B2 Value | Difference | Severity | Explanation |",
                "| :--- | :--- | :--- | :--- | :--- | :--- |",
            ])
            for item in recon_eval.discrepancy_table:
                lines.append(
                    f"| {item.metric} | {item.b1_value} | {item.b2_value} | {item.difference} | `{item.severity}` | {item.explanation} |"
                )
        if recon_eval.fail_reasons:
            lines.extend([
                "",
                "### Critical Integrity Failures (Fail-Closed Lockout)",
            ])
            for r in recon_eval.fail_reasons:
                lines.append(f"- [LOCKOUT DIRECTIVE] `{r}`")
        if recon_eval.warnings:
            lines.extend([
                "",
                "### Asynchronous & Methodological Warnings",
            ])
            for w in recon_eval.warnings:
                lines.append(f"- [WARNING] `{w}`")

    return sanitize_data_only_text("\n".join(lines))


def build_tab_a_data_only_report(
    config: Optional[EngineConfig],
    store: StateStore,
    *,
    recompute: bool = False,
) -> str:
    from analytics.strategy_trend_pullback import get_or_recompute_trend_pullback

    ts_utc, ts_sgt = _timestamps_utc_sgt()
    tp_ev, _did_recompute = get_or_recompute_trend_pullback(config or DEFAULT_CONFIG, store, recompute=recompute)
    if tp_ev is None:
        lines = [
            "# BTC TREND-PULLBACK v1.0 | DATA-ONLY REPORT (RESEARCH / PAPER MODE | SPOT ONLY)",
            f"**STATUS:** `UNVALIDATED` (NOT VALIDATED FOR LIVE CAPITAL)  |  **Retrieval Time (UTC):** `{ts_utc}`  |  **Retrieval Time (SGT):** `{ts_sgt}`",
            "**Data Integrity Pass:** `False`",
            "",
            "- **Stored Evaluation:** `UNAVAILABLE` (no `trend_pullback_evaluation` in StateStore; call `SignalDetector.evaluate` or pass `recompute=True` explicitly)",
            "- **Spot Price (BTCUSDT):** `UNAVAILABLE`",
            "- **Simulated Position Size (on 100k reference account, NOT operator account):** `0.00000 BTC` (`$0.00` notional)",
        ]
        return sanitize_data_only_text("\n".join(lines))
    return sanitize_data_only_text(tp_ev.summary_markdown)


def build_tab_q_data_only_report(config: Optional[EngineConfig], store: StateStore) -> str:
    ev = getattr(store, "four_gate_evaluation", None)
    if ev is None:
        from analytics.four_gate_engine import FourGateEngine
        ev = FourGateEngine(config).evaluate(store)
    if ev is None:
        return "# BTC DIBSE QUANTITATIVE PROTOCOL TELEMETRY\nSTATUS: DATA UNAVAILABLE"

    esa = ev.event_study_results or {}
    esb = ev.event_study_loop_b_results or {}
    lines = [
        "# BTC 4-GATE QUANTITATIVE PROTOCOL TELEMETRY PACKET (TAB 19 / [Q])",
        "PROTOCOL: DUAL-INVENTORY BIDIRECTIONAL SWING ENGINE (DIBSE) | SPOT-ONLY",
        f"TIMESTAMP_UTC: {ev.timestamp_utc}",
        f"LIVE_SPOT_PRICE_USD: {ev.live_spot_price:,.2f}",
        f"LAST_CLOSED_4H_BAR_UTC: {ev.last_closed_bar_utc}",
        f"STATUS: {ev.status}",
        f"INVENTORY_STATE: {ev.inventory_state}",
        "",
        "## 1. DIBSE CAPITAL SANDBOX ALLOCATION",
        f"ACCOUNT_EQUITY_USD: {ev.account_equity_usd:,.2f}",
        f"ACTIVE_SANDBOX_USD: {ev.active_sandbox_usd:,.2f} (20.0%)",
        f"CORE_RESERVE_USD: {ev.core_reserve_usd:,.2f} (80.0% Untouched)",
        f"USDT_SLEEVE_USD: {ev.usdt_sleeve_usd:,.2f} (10.0% Dip Harvester)",
        f"BTC_SLEEVE_USD: {ev.btc_sleeve_usd:,.2f} (10.0% Rip Harvester)",
        f"BTC_SLEEVE_UNITS: {ev.btc_sleeve_units:.6f}",
        "",
        "## 2. SWING LOOP A: USDT SLEEVE (DIP HARVESTER — BUY LOW, SELL HIGH)",
        f"LOOP_A_STATUS: {ev.loop_a_status}",
        f"LOOP_A_VERDICT: {ev.loop_a_verdict}",
        f"LOOP_A_CONFLUENCE_SCORE: {ev.loop_a_score}/4",
        f"LOOP_A_G1_PASS: {ev.loop_a_g1_levy}",
        f"LOOP_A_G1_A_SP: {ev.loop_a_g1_val:+.4f}",
        f"LOOP_A_G1_DETAILS: {ev.loop_a_g1_details}",
        f"LOOP_A_G2_PASS: {ev.loop_a_g2_zflow}",
        f"LOOP_A_G2_D_FLOW: {ev.loop_a_g2_val:+.2f}",
        f"LOOP_A_G2_DETAILS: {ev.loop_a_g2_details}",
        f"LOOP_A_G3_PASS: {ev.loop_a_g3_structure}",
        f"LOOP_A_G3_STATE: {ev.loop_a_g3_state}",
        f"LOOP_A_G3_POC_USD: {ev.gate_3_poc:,.2f}",
        f"LOOP_A_G3_VAL_USD: {ev.gate_3_val:,.2f}",
        f"LOOP_A_G3_L20_USD: {ev.gate_3_l20:,.2f}",
        f"LOOP_A_G3_DETAILS: {ev.loop_a_g3_details}",
        f"LOOP_A_G4_PASS: {ev.loop_a_g4_positioning}",
        f"LOOP_A_G4_FUNDING_RATE_PCT: {ev.loop_a_g4_funding_rate * 100:+.4f}%",
        f"LOOP_A_G4_FUNDING_P90: {ev.loop_a_g4_funding_p90:.2f}%",
        f"LOOP_A_G4_DETAILS: {ev.loop_a_g4_details}",
        f"LOOP_A_ENTRY_PRICE_USD: {ev.loop_a_entry_price:,.2f}",
        f"LOOP_A_TARGET_PRICE_USD: {ev.loop_a_target_price:,.2f}",
        f"LOOP_A_TARGET_PROFIT_PCT: {ev.loop_a_target_pct * 100:.2f}%",
        f"LOOP_A_EXPECTED_PROFIT_USD: {ev.loop_a_expected_profit_usd:,.2f}",
        f"LOOP_A_STOP_RULE: {ev.loop_a_stop_rule}",
        "",
        "## 3. SWING LOOP B: BTC SLEEVE (DIAGNOSTIC TELEMETRY ONLY — G1 AUTO-SELL GATED OFF)",
        "LOOP_B_EXECUTION_ENABLED: False (Failed 2020-2026 G1 Audit: N=2 triggers, 2,194.7d stranded cash, -79.08% BTC stack)",
        f"LOOP_B_STATUS: {ev.loop_b_status}",
        f"LOOP_B_VERDICT: {ev.loop_b_verdict}",
        f"LOOP_B_CONFLUENCE_SCORE: {ev.loop_b_score}/4",
        f"LOOP_B_G1_PASS: {ev.loop_b_g1_levy}",
        f"LOOP_B_G1_A_SP: {ev.loop_b_g1_val:+.4f}",
        f"LOOP_B_G1_DETAILS: {ev.loop_b_g1_details}",
        f"LOOP_B_G2_PASS: {ev.loop_b_g2_zflow}",
        f"LOOP_B_G2_D_FLOW: {ev.loop_b_g2_val:+.2f}",
        f"LOOP_B_G2_DETAILS: {ev.loop_b_g2_details}",
        f"LOOP_B_G3_PASS: {ev.loop_b_g3_structure}",
        f"LOOP_B_G3_STATE: {ev.loop_b_g3_state}",
        f"LOOP_B_G3_VAH_USD: {ev.gate_3_vah:,.2f}",
        f"LOOP_B_G3_H20_USD: {ev.loop_b_g3_h20:,.2f}",
        f"LOOP_B_G3_DETAILS: {ev.loop_b_g3_details}",
        f"LOOP_B_G4_PASS: {ev.loop_b_g4_positioning}",
        f"LOOP_B_G4_FUNDING_RATE_PCT: {ev.loop_b_g4_funding_rate * 100:+.4f}%",
        f"LOOP_B_G4_FUNDING_P90: {ev.loop_b_g4_funding_p90:.2f}%",
        f"LOOP_B_G4_DETAILS: {ev.loop_b_g4_details}",
        f"LOOP_B_SELL_PRICE_USD: {ev.loop_b_sell_price:,.2f}",
        f"LOOP_B_BUYBACK_PRICE_USD: {ev.loop_b_buyback_price:,.2f}",
        f"LOOP_B_DISCOUNT_PCT: {ev.loop_b_discount_pct * 100:.2f}%",
        f"LOOP_B_FREE_SATOSHIS_BTC: {ev.loop_b_free_satoshis_btc:.6f}",
        f"LOOP_B_FREE_SATOSHIS_PCT: {ev.loop_b_free_satoshis_pct:.2f}%",
        f"LOOP_B_SURPLUS_CASH_USD: {ev.loop_b_surplus_cash_usd:,.2f}",
        f"LOOP_B_STOP_RULE: {ev.loop_b_stop_rule}",
        "",
        "## 4. 90-DAY DE-CLUSTERED IN-SAMPLE EVENT STUDY (5D EMBARGO)",
        f"LOOP_A_TRIGGERS_N: {ev.event_study_triggers_count}",
        f"LOOP_A_SMALL_SAMPLE_CAVEAT: {ev.event_study_small_sample}",
        f"LOOP_A_WIN_RATE_1D_PCT: {esa.get('win_rate_1d', 0.0):.1f}%",
        f"LOOP_A_MEAN_RETURN_1D_PCT: {esa.get('mean_ret_1d', 0.0):+.2f}%",
        f"LOOP_A_ALPHA_1D_PCT: {esa.get('alpha_1d', 0.0):+.2f}%",
        f"LOOP_A_WIN_RATE_3D_PCT: {esa.get('win_rate_3d', 0.0):.1f}%",
        f"LOOP_A_MEAN_RETURN_3D_PCT: {esa.get('mean_ret_3d', 0.0):+.2f}%",
        f"LOOP_A_ALPHA_3D_PCT: {esa.get('alpha_3d', 0.0):+.2f}%",
        f"LOOP_A_WIN_RATE_5D_PCT: {esa.get('win_rate_5d', 0.0):.1f}%",
        f"LOOP_A_MEAN_RETURN_5D_PCT: {esa.get('mean_ret_5d', 0.0):+.2f}%",
        f"LOOP_A_ALPHA_5D_PCT: {esa.get('alpha_5d', 0.0):+.2f}%",
        f"LOOP_A_WIN_RATE_10D_PCT: {esa.get('win_rate_10d', 0.0):.1f}%",
        f"LOOP_A_MEAN_RETURN_10D_PCT: {esa.get('mean_ret_10d', 0.0):+.2f}%",
        f"LOOP_A_ALPHA_10D_PCT: {esa.get('alpha_10d', 0.0):+.2f}%",
        f"LOOP_B_TRIGGERS_N: {ev.event_study_loop_b_triggers_count}",
        f"LOOP_B_SMALL_SAMPLE_CAVEAT: {ev.event_study_loop_b_small_sample}",
        f"LOOP_B_WIN_RATE_1D_PCT: {esb.get('win_rate_1d', 0.0):.1f}%",
        f"LOOP_B_MEAN_RETURN_1D_PCT: {esb.get('mean_ret_1d', 0.0):+.2f}%",
        f"LOOP_B_ALPHA_1D_PCT: {esb.get('alpha_1d', 0.0):+.2f}%",
        f"LOOP_B_WIN_RATE_3D_PCT: {esb.get('win_rate_3d', 0.0):.1f}%",
        f"LOOP_B_MEAN_RETURN_3D_PCT: {esb.get('mean_ret_3d', 0.0):+.2f}%",
        f"LOOP_B_ALPHA_3D_PCT: {esb.get('alpha_3d', 0.0):+.2f}%",
        f"LOOP_B_WIN_RATE_5D_PCT: {esb.get('win_rate_5d', 0.0):.1f}%",
        f"LOOP_B_MEAN_RETURN_5D_PCT: {esb.get('mean_ret_5d', 0.0):+.2f}%",
        f"LOOP_B_ALPHA_5D_PCT: {esb.get('alpha_5d', 0.0):+.2f}%",
        f"LOOP_B_WIN_RATE_10D_PCT: {esb.get('win_rate_10d', 0.0):.1f}%",
        f"LOOP_B_MEAN_RETURN_10D_PCT: {esb.get('mean_ret_10d', 0.0):+.2f}%",
        f"LOOP_B_ALPHA_10D_PCT: {esb.get('alpha_10d', 0.0):+.2f}%",
        "",
        "## 5. LEGACY COMPATIBILITY FIELDS",
        f"CONFLUENCE_SCORE: {ev.score}/4",
        f"VERDICT: {ev.verdict}",
        f"GATE_1_LEVY_SIGNED_AREA_PASS: {ev.gate_1_levy}",
        f"GATE_2_SPOT_PERP_ZFLOW_PASS: {ev.gate_2_zflow}",
        f"GATE_3_30D_VOLUME_PROFILE_PASS: {ev.gate_3_structure}",
        f"GATE_4_POSITIONING_FILTER_PASS: {ev.gate_4_positioning}",
        f"ENTRY_PRICE_USD: {ev.entry_price:,.2f}",
        f"HARD_STOP_PRICE_USD: {ev.stop_price:,.2f}",
        f"TARGET_1_PRICE_USD: {ev.target_1_price:,.2f}",
        f"FINAL_SPOT_ALLOCATION_USD: {ev.final_notional_usd:,.2f}",
    ]
    return sanitize_data_only_text("\n".join(lines))
    return sanitize_data_only_text("\n".join(lines))


# ==============================================================================
# 7. TAB [F: FOOTPRINT] DATA-ONLY REPORT
# ==============================================================================
def build_tab_f_data_only_report(config: Optional[EngineConfig], store: StateStore) -> str:
    ts_utc, ts_sgt = _timestamps_utc_sgt()
    spot_px = _spot_price(store)
    f_ev = getattr(store, "footprint_evaluation", None)
    if f_ev is None and hasattr(store, "footprint_engine") and store.footprint_engine is not None:
        try:
            f_ev = store.footprint_engine.evaluate(store)
            store.footprint_evaluation = f_ev
        except Exception:
            f_ev = None

    lines = [
        "# TAB [F: FOOTPRINT] | DATA-ONLY METRICS REPORT",
        f"**Retrieval Time (UTC):** `{ts_utc}`  |  **Retrieval Time (SGT):** `{ts_sgt}`",
        f"**Spot Price (BTCUSDT):** `${spot_px:,.2f}`",
        "",
        "## 1. 15-MINUTE INTRA-CANDLE FOOTPRINT METRICS",
    ]
    if f_ev is not None:
        ref_entry = round(float(f_ev.entry_price or spot_px), 2)
        ref_stop = round(float(f_ev.stop_loss or 0.0), 2)
        stop_dist = round(abs(ref_entry - ref_stop), 2) if ref_stop > 0 else 0.0
        lines.extend([
            f"- **Footprint Source:** `{getattr(f_ev, 'data_source', 'UNAVAILABLE')}` | **Data Status:** `{getattr(f_ev, 'data_status', 'UNAVAILABLE')}` | **Synthetic:** `{bool(getattr(f_ev, 'is_synthetic', False))}` | **Data Age:** `{getattr(f_ev, 'data_age_seconds', None)} seconds`",
            f"- **Evaluation Data Timestamp (UTC):** `{f_ev.timestamp_utc}`",
            f"- **Auction Completed:** `{getattr(f_ev, 'auction_completed', None) if getattr(f_ev, 'auction_completed', None) is not None else 'UNAVAILABLE'}` | **Bar POC Reclaimed:** `{getattr(f_ev, 'bar_poc_reclaimed', None) if getattr(f_ev, 'bar_poc_reclaimed', None) is not None else 'UNAVAILABLE'}`",
            f"- **Active 15m Bar Net Delta:** `{f_ev.active_bar_delta:+.2f} BTC`",
            f"- **Previous Completed 15m Bar Net Delta:** `{f_ev.prev_bar_delta:+.2f} BTC`",
            f"- **Active Battle Zone Price:** `${f_ev.active_battle_zone:,.2f}`",
            f"- **Stacked Imbalances Count:** `{f_ev.stacked_imbalances_count}`",
            "",
            "## 2. 4 GATE CONDITION BOOLEANS (TRUE/FALSE)",
            f"- **Gate 1 (`Macro/Tactical Level Tap`):** `{bool(f_ev.gate1_macro_tap)}` (Level: `{f_ev.gate1_tapped_level_name}` at `${f_ev.gate1_tapped_level_price:,.2f}`)",
            f"- **Gate 2 (`Positioning Filter`):** `{bool(f_ev.gate2_positioning_crowded)}`",
            f"- **Gate 3 (`Wick Absorption`):** `{bool(f_ev.gate3_wick_absorption)}`",
            f"- **Gate 4 (`15m Net Delta Flip`):** `{bool(f_ev.gate4_delta_flip)}`",
            f"- **All Gates True:** `{bool(f_ev.all_gates_pass)}`",
            "",
            f"## 3. REFERENCE LEVELS (Reference calculation if entered at ${ref_entry:,.2f}. Not an order.)",
            f"- **Reference Entry Price:** `${ref_entry:,.2f}`",
            f"- **Reference Stop Level:** `${ref_stop:,.2f}`",
            f"- **Stop Distance (`|Entry - Stop|`):** `${stop_dist:,.2f}`",
            f"- **1:2 Reference Level:** `${f_ev.tp1_1to2:,.2f}`",
            f"- **1:3 Reference Level:** `${f_ev.tp2_1to3:,.2f}`",
        ])
    else:
        lines.append("- **Footprint Evaluation Available:** `False`")

    return sanitize_data_only_text("\n".join(lines))


# ==============================================================================
# 8. TAB [W: WATERFALL] DATA-ONLY REPORT
# ==============================================================================
def build_tab_w_data_only_report(config: Optional[EngineConfig], store: StateStore) -> str:
    """Tab [W] serialisation of analytics.waterfall.evaluate_waterfall.

    Same five pillars, same thresholds, same resolved state as the HUD. This used to
    compute a *second* set of five conditions from entirely different fields
    (confluence score, location score, funding, spot delta, footprint), so the export
    described a model the screen never displayed and could not be checked against it.
    """
    ts_utc, ts_sgt = _timestamps_utc_sgt()
    wf = evaluate_waterfall(store)
    i = wf.inputs

    def mk(flag: bool) -> str:
        return "PASS" if flag else "FAIL"

    pillar_true = sum(1 for x in (wf.p1_macro, wf.p2_structure, wf.p3_flow,
                                  wf.p4_leverage, wf.p5_trigger) if x)

    lines = [
        "# TAB [W: WATERFALL] | DATA-ONLY METRICS REPORT",
        f"**Retrieval Time (UTC):** `{ts_utc}`  |  **Retrieval Time (SGT):** `{ts_sgt}`",
        f"**Spot Price (BTCUSDT):** `${i['price']:,.2f}`",
        "**Pillar Source:** `analytics.waterfall.evaluate_waterfall` (identical to the HUD)",
        "",
        "## 1. FIVE PILLAR CONDITIONS",
        f"- **Pillar 1 - Macro Permission:** `{mk(wf.p1_macro)}` (above 200D SMA: `{i['above_200d_sma']}` | 200D SMA: `${i['sma200_px']:,.2f}` | 5D slope: `{i['sma200_slope_5d_pct']:+.3f}%` | NTZ hazard: `{i['ntz_active']}`)",
        f"- **Pillar 2 - Structure & Asymmetry:** `{mk(wf.p2_structure)}` (30D cVAL: `${i['c_val']:,.2f}` | cPOC: `${i['c_poc']:,.2f}` | cVAH: `${i['c_vah']:,.2f}` | spot - cVAL: `{i['dist_val_pct']:+.2f}%` | at edge: `{i['at_edge']}` | mid-range chop: `{i['is_mid_range_chop']}` | R:R to magnet: `{i['rrr_to_magnet']:.2f}R` | R:R gate: `{i['rrr_pass']}`)",
        f"- **Pillar 3 - Cross-Venue Flow:** `{mk(wf.p3_flow)}` (4H spot CVD: `{i['spot_cvd_4h_btc']:+,.1f} BTC` | 4H perp CVD: `{i['perp_cvd_4h_btc']:+,.1f} BTC` | divergence z: `{i['flow_divergence_z']:+.2f}` | stealth distribution: `{i['is_stealth_distribution']}` | spot accumulation: `{i['is_spot_accumulation']}` | Coinbase premium: `${i['coinbase_premium_usd']:+,.2f}`)",
        f"- **Pillar 4 - Leverage Fuel:** `{mk(wf.p4_leverage)}` (OI: `{i['open_interest_btc']:,.0f} BTC` | 4H dOI: `{i['oi_change_4h_pct']:+.2f}%` | funding: `{i['funding_rate_pct']:+.4f}%` | crowded long: `{i['is_crowded_long']}` | squeeze fuel: `{i['is_squeeze_fuel']}`)",
        f"- **Pillar 5 - Sniper Trigger:** `{mk(wf.p5_trigger)}` (footprint 4-gate: `{i['footprint_all_gates_pass']}` | wick absorption: `{i['footprint_wick_absorption']}` | delta flip: `{i['footprint_delta_flip']}` | 15m delta: `{i['footprint_active_delta_btc']:+,.1f} BTC`)",
        f"- **Pillars True:** `{pillar_true} / 5`",
        "",
        "## 2. RESOLVED WATERFALL STATE",
        f"- **Waterfall State:** `{wf.state}`",
        f"- **Binding Pillar:** `{wf.binding_pillar}`",
        f"- **All Pillars Aligned:** `{wf.pillars_aligned}`",
        f"- **State Vocabulary:** `RED_SYSTEMIC` | `RED_STEALTH` | `RED_CROWDED` | `RED_US_SELLING` | `GREEN` | `BLUE` | `AMBER`",
        "",
        "## 3. THRESHOLDS IN FORCE",
        f"- **Pillar 2 edge tolerance:** `+/-{EDGE_TOLERANCE_PCT}%` of cVAL; requires edge AND not mid-range",
        f"- **Pillar 2 asymmetry floor:** `{RRR_MIN:.2f}R`",
        f"- **Pillar 3 stealth:** spot `< {STEALTH_SPOT_MAX_BTC:.0f}` BTC and perp `> {STEALTH_PERP_MIN_BTC:.0f}` BTC and z `< {STEALTH_DIV_Z_MAX:.1f}`",
        f"- **Pillar 3 Coinbase premium:** pass `>= ${CPI_PASS_MIN_USD:,.2f}` | caution `< -${abs(CPI_CAUTION_USD):,.2f}` | veto `< -${abs(CPI_VETO_USD):,.2f}`",
        f"- **Pillar 4 funding:** neutral `<= {FUNDING_PASS_MAX_PCT:.4f}%` | crowded veto `> {FUNDING_CROWDED_MIN_PCT:.4f}%` | crowded OI `> {OI_CROWDED_MIN_PCT:.1f}%`",
        "",
        "## 4. RAW INPUT SNAPSHOT (for independent recomputation)",
    ]
    for key in sorted(i):
        lines.append(f"- `{key}`: `{i[key]}`")

    return sanitize_data_only_text("\n".join(lines))


# ==============================================================================
# 9. TAB [0: SPOT SWING] DATA-ONLY REPORT
# ==============================================================================
def build_tab_0_data_only_report(config: Optional[EngineConfig], store: StateStore) -> str:
    from analytics.spot_swing_engine import compute_safety_guard

    ts_utc, ts_sgt = _timestamps_utc_sgt()
    spot_px = _spot_price(store)
    sw = getattr(store, "spot_swing_evaluation", None)

    lines = [
        "# TAB [0: SPOT SWING] | DATA-ONLY METRICS REPORT",
        f"**Retrieval Time (UTC):** `{ts_utc}`  |  **Retrieval Time (SGT):** `{ts_sgt}`",
        f"**Spot Price (BTCUSDT):** `${spot_px:,.2f}`",
        "",
        "## 1. SPOT SWING SCREENER METRICS & GATE BOOLEANS",
    ]
    if sw is not None:
        sg = compute_safety_guard(store)
        lines.extend([
            f"- **Screener State:** `{sw.verdict}` (`Light: {sw.traffic_light}` | `data_ready={bool(sw.data_ready)}`)",
            f"- **Configured Equity:** `${sw.equity_usd:,.2f}` | **Risk Budget (%):** `{sw.risk_pct:.2f}%`",
            f"- **Safety Guard (Companion Feeds):** `{sg['status']}` (`{sg['detail']}`)",
        ])
        if sw.data_notes:
            lines.append(f"- **Data Notes:** `{'; '.join(sw.data_notes)}`")

        m = sw.macro
        if m is not None:
            thr_pct = getattr(m, "bbw_max_percentile", 0.30) * 100.0
            lines.extend([
                "",
                "### 1A. 1D Macro Regime Gate",
                f"- **1D Close / EMA50 / EMA200:** `${m.close:,.2f}` / `${m.ema50:,.2f}` / `${m.ema200:,.2f}`",
                f"- **Gate 1 (`Trend Baseline: Close > EMA50 > EMA200`):** `{bool(m.trend_pass)}`",
                f"- **BBW({getattr(m, 'bbw_period', 20)}) / {getattr(m, 'bbw_rank_window', 180)}D Rank:** `{m.bbw * 100:.2f}%` / `{m.bbw_percentile * 100:.1f}%` (Threshold `<= {thr_pct:.0f}%`, Lookback `{m.squeeze_lookback_bars}D`)",
                f"- **Gate 2 (`Volatility Squeeze`):** `{bool(m.compression_pass)}`",
                f"- **Macro Gate Approved (`Trend AND Squeeze`):** `{bool(m.macro_approved)}`",
            ])
        else:
            lines.append("- **1D Macro Regime Gate:** `UNAVAILABLE`")

        s = sw.setup
        if s is not None and s.anchors_ready and s.pwl > 0:
            lines.extend([
                "",
                "### 1B. 4H Weekly Anchors & Structural Liquidity Setup",
                f"- **Previous Mon–Sun Week PWH / PWL:** `${s.pwh:,.2f}` / `${s.pwl:,.2f}`",
                f"- **4H Sweep (`low < PWL` in last {getattr(s, 'sweep_window_bars', 12)} bars):** `{bool(s.sweep_detected)}` (Lowest Wick: `{f'${s.sweep_low:,.2f}' if s.sweep_detected else 'NONE'}`)",
                f"- **4H Reclaim (`close > PWL`):** `{bool(s.reclaim_confirmed)}` (Closed 4H: `${s.close:,.2f}`)",
                f"- **4H Volume (`vol > SMA({getattr(s, 'vol_sma_period', 3)})` incl. current bar):** `{bool(s.volume_confirmed)}` (`{s.volume:,.1f}` vs `{s.vol_sma3:,.1f}`)",
                f"- **Signal Active (`Sweep AND Reclaim AND Vol`):** `{bool(s.signal_active)}` (`is_fresh={bool(s.is_fresh)}`)",
            ])
        else:
            lines.append("- **4H Weekly Anchors & Setup:** `UNAVAILABLE (syncing previous-week bars)`")

        mg = sw.magnet
        if mg is not None:
            eff_target = mg.target_magnet if getattr(mg, "target_magnet", 0.0) > 0 else mg.short_liq_magnet
            lines.extend([
                "",
                "### 1C. Daily Liquidation Magnet Protocol & RRR Gate",
                f"- **Regime Classification:** `{mg.regime}` (`{mg.regime_detail}`)",
                f"- **30–45D Range / Pivot / 50D SMA:** `${mg.range_low_30d:,.2f}` – `${mg.range_high_30d:,.2f}` (`{mg.range_pos_pct:.1f}%`) | Pivot `${mg.range_pivot:,.2f}` | 50D SMA `${mg.sma50_1d:,.2f}`",
                f"- **Short-Liq Magnet (Upper):** `${mg.short_liq_magnet:,.2f}` (`{mg.short_liq_distance_pct:+.2f}%` | `{mg.short_liq_size_label}` | `{mg.short_liq_source}`)",
                f"- **Long-Liq Magnet (Lower):** `${mg.long_liq_magnet:,.2f}` (`{-mg.long_liq_distance_pct:+.2f}%` | `{mg.long_liq_size_label}` | `{mg.long_liq_source}`)",
                f"- **OI Trend:** `{mg.oi_trend}`",
                f"- **8H Funding:** `{mg.funding_status}`",
                f"- **Spot CVD Assessment:** `{mg.spot_cvd_assessment}` (`spot_cvd_confirming={bool(mg.spot_cvd_confirming)}`)",
                f"- **Headline Filter:** `{mg.headline_filter}`",
                f"- **24H Cumulative Liquidations:** `{mg.cum_liq_24h_summary}`",
                f"- **RRR Check (`Target ${eff_target:,.2f}` vs `Stop ${mg.hard_stop_price:,.2f}`):** `{mg.rrr_to_magnet:.2f}R` (`min_required={mg.min_required_rrr:.1f}R`, `rrr_pass={bool(mg.rrr_pass)}`)",
                f"- **Max Entry for {mg.min_required_rrr:g}R:** `${mg.max_entry_for_3r:,.2f}` | **Protocol State:** `{mg.verdict}` (`Confidence: {mg.confidence}`)",
            ])

        lines.append("")
        t = sw.trade
        rk = sw.risk
        macro_ok = bool(m is not None and m.macro_approved)
        rrr_ok = bool(mg is None or mg.rrr_pass)
        mag_actionable = bool(mg is None or mg.verdict not in ("Do Nothing", "Reduce or Exit"))
        if t is not None:
            lines.extend([
                f"## 2. ACTIVE POSITION LEVELS (Open `{t.status}` at ${t.entry:,.2f})",
                f"- **Entry Price:** `${t.entry:,.2f}` | **Size:** `{t.qty_btc:.6f} BTC` (`${t.qty_btc * t.entry:,.2f}`)",
                f"- **Current Stop / Initial Stop:** `${t.current_stop:,.2f}` / `${t.initial_stop:,.2f}`",
                f"- **Level 1 (`+2.0R`):** `${t.tp1:,.2f}` (`tp1_hit={bool(t.tp1_hit)}`)",
                f"- **Level 2 (`PWH`):** `${t.tp2:,.2f}`",
            ])
        elif rk is not None and macro_ok and rrr_ok and mag_actionable:
            lines.extend([
                f"## 2. REFERENCE LEVELS (Reference calculation if entered at ${rk.entry:,.2f}. Not an order.)",
                f"- **Reference Entry Price:** `${rk.entry:,.2f}`",
                f"- **Reference Stop Level:** `${rk.stop:,.2f}` (`ATR14=${rk.atr14:,.2f}`, Distance `${rk.stop_distance:,.2f}` / `{rk.stop_distance_pct:.2f}%`)",
                f"- **Reference Spot Size (100% Equity Cap):** `{rk.qty_btc:.6f} BTC` (`${rk.notional_usd:,.2f}` = `{rk.equity_alloc_pct:.1f}%` of `${rk.equity_usd:,.2f}`, `spot_capped={bool(rk.spot_capped)}`)",
                f"- **Reference Level 1 (`+2.0R`):** `${rk.tp1:,.2f}`",
                f"- **Reference Level 2 (`PWH`):** `${rk.tp2_pwh:,.2f}`",
                f"- **Reference Level 3 (`{f'{mg.min_required_rrr:g}R' if mg else '3R'}`):** `${rk.tp_3r:,.2f}`",
            ])
        else:
            lines.extend([
                "## 2. REFERENCE LEVELS",
                "- **Active Reference Sizing:** `NONE (100% Cash / Gate Closed or RRR Below Minimum)`",
            ])
    else:
        lines.append("- **Spot Swing Screener Evaluation Available:** `False` (`UNAVAILABLE`)")

    return sanitize_data_only_text("\n".join(lines))


# ==============================================================================
# 10. TAB [Z] DECISION-SURFACE DATA-ONLY REPORT (9-FLAGSHIP TOP-RIBBON MATRIX)
# ==============================================================================
def build_tab_l_data_only_report(config: Optional[EngineConfig], store: StateStore) -> str:
    ts_utc, ts_sgt = _timestamps_utc_sgt()
    spot_px = _spot_price(store)
    ms = getattr(store, "master_synthesis_evaluation", None)
    tpb = getattr(store, "trend_pullback_evaluation", None)
    slsp = getattr(store, "slsp_evaluation", None)
    sw = getattr(store, "spot_swing_evaluation", None)

    lines = [
        "# TAB [Z: DECISION SURFACE] | 8-FLAGSHIP DESK DATA-ONLY METRICS REPORT",
        f"**Retrieval Time (UTC):** `{ts_utc}`  |  **Retrieval Time (SGT):** `{ts_sgt}`",
        f"**Spot Price (BTCUSDT):** `${spot_px:,.2f}`",
        "**Desk Purpose & Scope:** `Single-screen 8-Flagship-Desk Telemetry Matrix (P, G, R, M, A, F, W, 0) & 4-Domain Readiness Overview. Keeps each strategy's reference entry, stop, and sizing calculations strictly unblended.`",
        "",
        "## 1. 8-FLAGSHIP TOP-RIBBON DESK READINESS METRICS (`P, G, R, M, A, F, W, 0`)",
    ]
    if ms is not None:
        lines.extend([
            f"- **8-Desk Readiness Index (`0.0 - 100.0`):** `{ms.master_alignment_score:.1f}`",
            f"- **Readiness Index >= 70.0:** `{bool(ms.master_alignment_score >= 70.0)}`",
            f"- **Hard Veto Active Across Desks:** `{bool(ms.supreme_veto_active)}`",
            "",
            "## 2. 4 ORTHOGONAL DOMAIN PILLAR MEASUREMENTS",
        ])
        for h in getattr(ms, "hierarchy_rows", []) or []:
            h_name = getattr(h, "layer_name", "Domain")
            h_status = str(getattr(h, "status", "STANDBY"))
            h_rule = getattr(h, "authority_rule", "")
            h_ruling = getattr(h, "live_ruling", "")
            lines.append(
                f"- **{h_name} (`{h_rule}`):** Pass=`{bool(h_status == 'PASS')}` | "
                f"Armed=`{bool(h_status in ('PASS', 'ARMED'))}` | Telemetry: `{h_ruling}`"
            )
        lines.extend([
            "",
            "## 3. 8-FLAGSHIP DESK TELEMETRY MATRIX (`P, G, R, M, A, F, W, 0`)",
        ])
        for r in getattr(ms, "tab_rows", []) or []:
            r_name = getattr(r, "tab_name", "Desk")
            r_light = str(getattr(r, "traffic_light", "YELLOW"))
            r_state = getattr(r, "score_or_status", "")
            r_driver = getattr(r, "primary_driver", "")
            lines.append(
                f"- **{r_name}:** Pass=`{bool(r_light == 'GREEN')}` | "
                f"Constructive=`{bool(r_light in ('GREEN', 'BLUE'))}` | "
                f"State=`{r_state}` | Telemetry=`{r_driver}`"
            )
        lines.extend([
            "",
            f"## 4. INDEPENDENT STRATEGY REFERENCE LEVELS (Reference calculation if entered at ${spot_px:,.2f}. Not an order.)",
            f"- **Reference Spot Price:** `${spot_px:,.2f}`",
        ])
        if tpb is not None:
            lines.append(
                f"- **Desk [A] Trend-Pullback v1.0 Reference (Simulated on ${tpb.simulation_equity_usd:,.0f} reference account, NOT operator equity):** Entry `${tpb.reference_entry_price:,.2f}` | "
                f"Stop `${tpb.structural_stop:,.2f}` (`-${tpb.stop_distance_usd:,.2f}` / `{tpb.stop_distance_atr:.2f} ATR`) | "
                f"Sim Size `{tpb.position_size_btc:.6f} BTC` (Sim Notional `${tpb.position_value_usd:,.2f}` | Sim Budget `${tpb.risk_budget_usd:,.2f}`) | Reconciled Risk `${tpb.total_estimated_risk_usd:,.2f}`"
            )
        if slsp is not None and slsp.active_setup is not None:
            st = slsp.active_setup
            lines.append(
                f"- **Desk [P] SLSP v1.0 Reference:** Entry `${st.entry_price:,.2f}` | "
                f"Stop `${st.stop_loss:,.2f}` | Level 1 (`1.5R`) `${st.tp1_price:,.2f}` | "
                f"Size `{st.position_size_btc:.4f} BTC`"
            )
        if sw is not None and sw.risk is not None:
            rk = sw.risk
            lines.append(
                f"- **Desk [0] Spot Swing (1:3 RRR) Reference:** Entry `${rk.entry:,.2f}` | "
                f"Stop `${rk.stop:,.2f}` | Level 1 (`2.0R`) `${rk.tp1:,.2f}` | "
                f"Size `{rk.qty_btc:.6f} BTC`"
            )
        lines.extend([
            f"- **Spot Holder Reference Hard Stop Level:** `${ms.holder_hard_stop_usd:,.2f}`",
            f"- **Spot Holder Reference Upper Level 1:** `${ms.holder_tp1_usd:,.2f}`",
            f"- **Spot Holder Reference Upper Level 2:** `${ms.holder_tp2_usd:,.2f}`",
        ])
    else:
        lines.append("- **Master Synthesis Evaluation Available:** `False`")

    return sanitize_data_only_text("\n".join(lines))


# ==============================================================================
# 10b. TAB [X / 20: 4H FUTURES + INVENTORY PROTOCOL v4.0] DATA-ONLY REPORT
# ==============================================================================
def build_tab_x_data_only_report(config: Optional[EngineConfig], store: StateStore) -> str:
    """Tab [X / 20] serialisation of analytics.futures_v4_engine.build_futures_v4_view.

    Reads the exact same FuturesV4View snapshot as _build_tab20_futures_v4_hud so
    the exported packet and screen always state the same boundary, mode, thresholds,
    checklist outcomes, and numbers.
    """
    from analytics.futures_v4_engine import build_futures_v4_view

    cfg = config or DEFAULT_CONFIG
    ts_utc, ts_sgt = _timestamps_utc_sgt()
    spot_px = _spot_price(store)
    view = build_futures_v4_view(cfg, store)
    ev = view.evaluation

    lines = [
        "# TAB [X / 20: 4H FUTURES + INVENTORY PROTOCOL v4.0] | DATA-ONLY METRICS REPORT",
        f"**Retrieval Time (UTC):** `{ts_utc}`  |  **Retrieval Time (SGT):** `{ts_sgt}`",
        f"**Spot Price (BTCUSDT):** `${spot_px:,.2f}`",
        f"**Spot-Only Operator Boundary:** `{view.spot_only_boundary}`",
        f"**Execution Mode:** `{view.mode_label}` (`read_only={view.read_only}`)",
        "**Model Source:** `analytics.futures_v4_engine.build_futures_v4_view` (identical to Tab [X / 20] HUD)",
        "",
        "## 1. PROTOCOL REGIME & RESOLVED MODEL SIGNAL",
        f"- **Protocol Spec:** `v{ev.protocol_version} 4H DAY-POSITION (MODEL MAX 1:{view.max_leverage:g} LEV · 4-{view.max_hold_hours:g}h HOLD)`",
        f"- **Model Signal (`{'HYPOTHETICAL/PAPER' if view.read_only else 'PAPER'}`):** `{view.action_label}` (`futures_status={ev.futures_status}`)",
        f"- **Regime Score / Bias:** `{ev.regime_score:.1f}/100` (`{ev.regime_bias}`, `1D={ev.daily_bias}`)",
        f"- **4H Close Anchor (UTC):** `{ev.last_4h_close_utc}`",
        f"- **Weekend UTC:** `{ev.is_weekend_utc}` (`Weekend Thresholds: L>={view.weekend_long:.0f} / S<={view.weekend_short:.0f} · Size Mult: {view.weekend_size_mult:g}x`)",
        f"- **Active Regime Thresholds:** `L>={ev.long_threshold:.0f} · Flat · S<={ev.short_threshold:.0f}`",
        f"- **Macro Calendar Source:** `{ev.macro_source_status}`",
        "",
        "## 2. 4H MULTI-FACTOR REGIME BREAKDOWN",
    ]
    for k, lbl in (
        ("trend_structure", "1. Trend Structure (30%)"),
        ("momentum", "2. Momentum 4H (25%)"),
        ("volatility_liquidity", "3. Vol & Liquidity 4H (25%)"),
        ("session_context", "4. Session / Context (20%)"),
    ):
        if getattr(ev, "is_warming_up", False) or k not in ev.factor_scores:
            lines.append(f"- **{lbl}:** `UNAVAILABLE` (`Warming up`)")
        else:
            lines.append(
                f"- **{lbl}:** `{ev.factor_scores[k]:.1f}` (`{ev.factor_summaries.get(k, '—')}`)"
            )

    lines.extend([
        "",
        "## 3. SELL INVENTORY OPTION (HYPOTHETICAL · SEC 2 & 6)",
        f"- **Spot Model Status:** `{'SELL INVENTORY SIGNAL (HYPOTHETICAL/PAPER)' if (ev.sell_inventory_active and view.read_only) else ('SELL INVENTORY ACTIVE (PAPER)' if ev.sell_inventory_active else 'HOLD SPOT INVENTORY')}`",
        f"- **Model Spot Inventory Held:** `{ev.spot_inventory_btc:.2f} BTC` (`0% Futures Heat`)",
        f"- **{'Hypothetical Trim (Paper)' if view.read_only else 'Paper Trim'}:** `{'HYPOTHETICAL / PAPER — NOT AN ORDER: ' if (ev.sell_inventory_active and view.read_only) else ''}{ev.sell_inventory_pct:.0f}% -> {ev.sell_inventory_btc:.4f} BTC (${ev.sell_inventory_usd:,.0f})`" if ev.sell_inventory_active else f"- **{'Hypothetical Trim (Paper)' if view.read_only else 'Paper Trim'}:** `0% -> 0.0000 BTC ($0)` (Requires score <= `{ev.short_threshold:.0f}`)",
        f"- **4H Structural Ref:** `{ev.sell_inventory_ref}`",
        "- **Exempt From:** `Weekend ext, Check 2 bias/dist, Checks 3-9 & Halts`",
        "",
        f"## 4. 9-POINT FUTURES QUALIFICATION CHECKLIST ({view.checklist_passed}/{view.checklist_total})",
    ])
    for item in ev.checklist:
        st_s = "PASS" if item.passed else "FAIL"
        lines.append(f"- **Check {item.id} ({item.rule}):** `[{st_s}]` {item.detail}")

    lines.extend([
        "",
        "## 5. HYPOTHETICAL PAPER SIZING & HOLD RULES",
        f"- **Model Boundary:** `{view.order_tag}`",
    ])
    if view.sizing_active:
        prefix = "HYPOTHETICAL / PAPER ONLY (NOT AN ORDER): " if view.read_only else "PAPER SIMULATION ONLY: "
        lines.extend([
            f"- **Hypothetical Dir / Method:** `{prefix}{ev.eval_direction} ({ev.entry_method})`",
            f"- **Hypothetical Entry / Hard Stop:** `{prefix}${ev.entry_price:,.1f} / ${ev.stop_price:,.1f} ({ev.stop_distance_pct:.2f}% <= {view.max_stop_pct:.1f}%)`",
            f"- **Hypothetical Target 1 ({view.partial_pct:.0f}% @ {view.partial_r:.1f}R):** `{prefix}${ev.target1_price:,.1f} ({ev.target1_label})`",
            f"- **Raw / Fund-Adj R:R:** `{ev.raw_rr:.2f}:1 / {ev.funding_adj_rr:.2f}:1 (>= {view.min_rr:.1f}:1)`",
            f"- **Hypothetical Size / Leverage:** `{prefix}{ev.size_btc:.4f} BTC (${ev.notional_usd:,.0f}, {ev.leverage:.2f}x/{view.max_leverage:g}x)`",
            f"- **Hypothetical Risk:** `{prefix}{ev.actual_risk_pct:.3f}% (${ev.actual_risk_usd:,.2f})`",
        ])
    else:
        lines.extend([
            f"- **Futures Ticket State:** `FLAT — NO HYPOTHETICAL FUTURES POSITION` (`{view.checklist_passed}/{view.checklist_total} passed`)",
            f"- **Evaluated Direction:** `{ev.eval_direction} (checklist evaluation only; gated OFF)`",
            f"- **Eval R:R / Stop:** `UNAVAILABLE (warming up buffers)`"
            if getattr(ev, "is_warming_up", False)
            else f"- **Eval R:R / Stop:** `R:R {ev.raw_rr:.2f}:1 / adj {ev.funding_adj_rr:.2f}:1 (>= {view.min_rr:.1f}:1) · Stop {ev.stop_distance_pct:.2f}% (<= {view.max_stop_pct:.1f}%)`",
        ])
    lines.append(
        f"- **Time / Hold Rules:** `BE @ +{view.be_r:g}R · {view.time_reduce_hours:g}h -50% · {view.time_exit_hours:g}h Exit (<1R) · {view.max_hold_hours:g}h Max`"
    )
    if ev.open_positions:
        op = ev.open_positions[0]
        lines.append(
            f"- **Open Paper Position:** `{op['direction']} {op['size_btc']} BTC ({op['current_r']:+.2f}R, {op['hold_hours']:.1f}h/{view.max_hold_hours:g}h)`"
        )
    else:
        lines.append(f"- **Open Paper Position:** `FLAT (0 / {view.max_concurrent} Concurrent)`")

    b = ev.breakers or {}
    lines.extend([
        "",
        "## 6. PAPER LEDGER & 5-TIER CIRCUIT BREAKERS (SEC 8)",
        f"- **Paper Equity / Heat:** `${ev.equity_usd:,.2f}` | `Heat {ev.open_heat_pct:.2f}% / {view.max_heat_pct:.1f}% max`",
        f"- **Intraday ({view.intraday_loss_pct:g}%):** `{'HALT' if b.get('intraday_halted') else 'OK'}` (`{ev.intraday_pnl_pct:+.2f}%`)",
        f"- **Daily ({view.daily_loss_pct:g}%):** `{'HALT' if b.get('daily_halted') else 'OK'}` (`{ev.daily_pnl_pct:+.2f}%`)",
        f"- **Weekly ({view.weekly_loss_pct:g}%):** `{'FLAT' if b.get('weekly_halted') else 'OK'}` (`{ev.weekly_pnl_pct:+.2f}%`)",
        f"- **DD1 ({view.dd_tier1_pct:g}% -> {view.dd_tier1_risk_pct:g}%/{view.dd_tier1_long:.0f}-{view.dd_tier1_short:.0f}):** `{'ACTIVE' if b.get('dd_tier1_active') else 'OK'}`",
        f"- **DD2 ({view.dd_tier2_pct:g}%):** `{'LOCKED' if b.get('dd_tier2_locked') else 'OK'}` (`{ev.drawdown_pct:+.2f}%`)",
        f"- **Closed Paper Legs:** `{ev.total_closed_legs}` (`WR {ev.review_win_rate_pct:.1f}% · PF {ev.review_profit_factor:.2f} · Exp {ev.review_expectancy_r:+.2f}R`)",
    ])
    return sanitize_data_only_text("\n".join(lines))


# ==============================================================================
# 11. GLOBAL [C: AI PACKET] MASTER DATA-ONLY PACKET
# ==============================================================================
def build_global_data_only_packet(config: Optional[EngineConfig], store: StateStore) -> str:
    """Combines all primary top-ribbon DATA-ONLY reports into a single master packet."""
    cfg = config or DEFAULT_CONFIG
    ts_utc, ts_sgt = _timestamps_utc_sgt()
    spot_px = _spot_price(store)

    sections = [
        "# BTC SWING ENGINE | GLOBAL DATA-ONLY TELEMETRY PACKET ([C: AI PACKET])",
        f"**Retrieval Time (UTC):** `{ts_utc}`  |  **Retrieval Time (SGT):** `{ts_sgt}`",
        f"**Spot Price (BTCUSDT):** `${spot_px:,.2f}`",
        "**Output Specification:** `DATA-ONLY (Raw Measurements, Reference Formulas & True/False Conditions Only — Zero Interpretive Prose)`",
        "",
        "---",
        "",
        build_tab_a_data_only_report(cfg, store),
        "",
        "---",
        "",
        build_tab_m_data_only_report(cfg, store),
        "",
        "---",
        "",
        build_tab_g_data_only_report(cfg, store),
        "",
        "---",
        "",
        build_tab_r_data_only_report(cfg, store),
        "",
        "---",
        "",
        build_tab_p_data_only_report(cfg, store),
        "",
        "---",
        "",
        build_tab_f_data_only_report(cfg, store),
        "",
        "---",
        "",
        build_tab_w_data_only_report(cfg, store),
        "",
        "---",
        "",
        build_tab_0_data_only_report(cfg, store),
        "",
        "---",
        "",
        build_tab_l_data_only_report(cfg, store),
        "",
        "---",
        "",
        build_tab_x_data_only_report(cfg, store),
        "",
    ]
    return sanitize_data_only_text("\n".join(sections))


def copy_text_to_clipboard_and_log(
    text: str,
    log_filename: str,
    store: Optional[StateStore] = None,
    also_write_root_and_downloads: bool = False,
) -> Tuple[bool, str, int]:
    """Saves a DATA-ONLY report to logs/<log_filename> and copies it to the system clipboard."""
    char_count = len(text)
    base_dir = pathlib.Path(__file__).resolve().parent.parent
    log_dir = base_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / log_filename
    try:
        log_path.write_text(text, encoding="utf-8")
    except Exception:
        pass

    if also_write_root_and_downloads:
        try:
            (base_dir / "BTC_AI_DATA_PACKET_LATEST.md").write_text(text, encoding="utf-8")
        except Exception:
            pass
        downloads_dir = pathlib.Path.home() / "Downloads"
        if downloads_dir.exists():
            try:
                (downloads_dir / "BTC_AI_DATA_PACKET_LATEST.md").write_text(text, encoding="utf-8")
            except Exception:
                pass

    copied_ok = False
    if os.name == "nt":
        try:
            subprocess.run(
                ["clip.exe"],
                input=text.encode("utf-16le"),
                check=True,
                timeout=3.0,
            )
            copied_ok = True
        except Exception:
            try:
                subprocess.run(
                    ["powershell", "-NoProfile", "-Command", "Set-Clipboard -Value $input"],
                    input=text.encode("utf-8"),
                    check=True,
                    timeout=4.0,
                )
                copied_ok = True
            except Exception:
                copied_ok = False
    else:
        for cmd in (["termux-clipboard-set"], ["wl-copy"], ["xclip", "-selection", "clipboard"]):
            try:
                subprocess.run(cmd, input=text.encode("utf-8"), check=True, timeout=3.0)
                copied_ok = True
                break
            except Exception:
                continue

    if store is not None:
        store.last_packet_copied_utc = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")
        store.last_packet_copied_ts = time.time()
        store.last_packet_char_count = char_count

    return copied_ok, str(log_path), char_count


def _extract_panel_row(panels: dict, panel_key: str, label: str, fallback: str = "N/A") -> str:
    for item in panels.get(panel_key, []) or []:
        if item.get("label") == label:
            val = str(item.get("value") or "").strip()
            return val if val else fallback
    return fallback


def _closed_kline_bars(bars: list, interval_ms: int, now_ms: Optional[int] = None) -> list:
    """Returns time-sorted closed KlineBar entries, dropping an actively forming candle."""
    valid = [b for b in bars if getattr(b, "close", 0.0) > 0.0 and getattr(b, "timestamp_ms", 0) > 0]
    if not valid:
        return []
    valid.sort(key=lambda b: int(b.timestamp_ms))
    ref_ms = int(now_ms if now_ms is not None else time.time() * 1000)
    closed = [b for b in valid if (int(b.timestamp_ms) + int(interval_ms)) <= ref_ms]
    if not closed and len(valid) >= 2:
        closed = valid[:-1]
    return closed


def _detect_swing_pivots(bars: list, left: int, right: int) -> Tuple[List[Tuple[int, float, int]], List[Tuple[int, float, int]]]:
    """Detects fractal swing highs and lows as (index, price, timestamp_ms)."""
    n = len(bars)
    swing_highs: List[Tuple[int, float, int]] = []
    swing_lows: List[Tuple[int, float, int]] = []
    if n < left + right + 1:
        return swing_highs, swing_lows
    for i in range(left, n - right):
        hi = float(bars[i].high)
        lo = float(bars[i].low)
        ts = int(bars[i].timestamp_ms)
        if all(hi > float(bars[j].high) for j in range(i - left, i)) and all(
            hi >= float(bars[j].high) for j in range(i + 1, i + right + 1)
        ):
            swing_highs.append((i, hi, ts))
        if all(lo < float(bars[j].low) for j in range(i - left, i)) and all(
            lo <= float(bars[j].low) for j in range(i + 1, i + right + 1)
        ):
            swing_lows.append((i, lo, ts))
    return swing_highs, swing_lows


def _cluster_sr_zones(pivots: List[Tuple[int, float, int]], tolerance_pct: float = 0.01) -> List[Tuple[float, int]]:
    """Groups nearby swing pivot prices into (mean_price, touch_count) clusters."""
    if not pivots:
        return []
    ordered = sorted(float(p[1]) for p in pivots if p[1] > 0.0)
    if not ordered:
        return []
    clusters: List[List[float]] = [[ordered[0]]]
    for px in ordered[1:]:
        anchor = sum(clusters[-1]) / len(clusters[-1])
        if anchor > 0.0 and abs(px - anchor) / anchor <= tolerance_pct:
            clusters[-1].append(px)
        else:
            clusters.append([px])
    return [(sum(c) / len(c), len(c)) for c in clusters]


def _fmt_ts_utc(ts_ms: int, fmt: str) -> str:
    return datetime.fromtimestamp(int(ts_ms) / 1000.0, tz=timezone.utc).strftime(fmt)


def _summarize_kline_structure(
    bars: list,
    spot_px: float,
    tf_label: str,
    interval_ms: int,
    lookback: int = 500,
    now_ms: Optional[int] = None,
) -> Dict[str, str]:
    """Computes full-lookback HH/HL/LH/LL structure, latest BOS, and clustered S/R zones."""
    closed = _closed_kline_bars(bars, interval_ms, now_ms=now_ms)[-lookback:]
    if len(closed) < 12:
        return {
            "tf": tf_label,
            "bars": str(len(closed)),
            "structure": "INSUFFICIENT_DATA",
            "pivots": "N/A",
            "bos": "N/A",
            "res": "N/A",
            "sup": "N/A",
        }

    lr = 5 if len(closed) >= 40 else 2
    sh_list, sl_list = _detect_swing_pivots(closed, lr, lr)
    if (len(sh_list) < 2 or len(sl_list) < 2) and lr > 2:
        sh_list, sl_list = _detect_swing_pivots(closed, 2, 2)

    t_fmt = "%m-%d" if interval_ms >= 86_400_000 else "%m-%d %H:%M"
    if len(sh_list) >= 2 and len(sl_list) >= 2:
        prev_sh, last_sh = sh_list[-2], sh_list[-1]
        prev_sl, last_sl = sl_list[-2], sl_list[-1]
        h_tag = "HH" if last_sh[1] > prev_sh[1] else "LH"
        l_tag = "HL" if last_sl[1] > prev_sl[1] else "LL"
        if h_tag == "HH" and l_tag == "HL":
            struct_str = "UPTREND (HH/HL)"
        elif h_tag == "LH" and l_tag == "LL":
            struct_str = "DOWNTREND (LH/LL)"
        else:
            struct_str = f"MIXED ({h_tag}/{l_tag})"
        pivots_str = (
            f"SH:${last_sh[1]:,.2f} ({_fmt_ts_utc(last_sh[2], t_fmt)}) · "
            f"SL:${last_sl[1]:,.2f} ({_fmt_ts_utc(last_sl[2], t_fmt)})"
        )
    else:
        win_hi = max(float(b.high) for b in closed[-min(len(closed), 20):])
        win_lo = min(float(b.low) for b in closed[-min(len(closed), 20):])
        struct_str = "RANGE / DEVELOPING"
        pivots_str = f"Hi:${win_hi:,.2f} · Lo:${win_lo:,.2f}"

    # Chronological BOS scan across confirmed fractal pivots
    bos_str = "None in window"
    if sh_list and sl_list:
        sh_by_idx = {idx: px for idx, px, _ in sh_list}
        sl_by_idx = {idx: px for idx, px, _ in sl_list}
        active_sh: Optional[float] = None
        active_sl: Optional[float] = None
        broken_sh_val: Optional[float] = None
        broken_sl_val: Optional[float] = None
        last_bos_txt = ""
        for idx, bar in enumerate(closed):
            if idx in sh_by_idx:
                active_sh = sh_by_idx[idx]
            if idx in sl_by_idx:
                active_sl = sl_by_idx[idx]
            c_px = float(bar.close)
            if active_sh is not None and active_sh != broken_sh_val and c_px > active_sh:
                broken_sh_val = active_sh
                last_bos_txt = f"BOS Up > ${active_sh:,.2f} ({_fmt_ts_utc(bar.timestamp_ms, t_fmt)})"
            elif active_sl is not None and active_sl != broken_sl_val and c_px < active_sl:
                broken_sl_val = active_sl
                last_bos_txt = f"BOS Down < ${active_sl:,.2f} ({_fmt_ts_utc(bar.timestamp_ms, t_fmt)})"
        if last_bos_txt:
            bos_str = last_bos_txt

    ref_px = spot_px if spot_px > 0.0 else float(closed[-1].close)
    zones = _cluster_sr_zones(sh_list + sl_list, tolerance_pct=0.01)
    res_zones = sorted((z for z in zones if z[0] > ref_px * 1.001), key=lambda z: z[0])[:3]
    sup_zones = sorted((z for z in zones if z[0] < ref_px * 0.999), key=lambda z: z[0], reverse=True)[:3]

    res_str = ", ".join(f"${px:,.2f} ({cnt}x)" for px, cnt in res_zones) if res_zones else "None above in lookback"
    sup_str = ", ".join(f"${px:,.2f} ({cnt}x)" for px, cnt in sup_zones) if sup_zones else "None below in lookback"
    return {
        "tf": tf_label,
        "bars": str(len(closed)),
        "structure": struct_str,
        "pivots": pivots_str,
        "bos": bos_str,
        "res": res_str,
        "sup": sup_str,
    }


def _build_recent_ohlcv_lines(
    bars: list,
    tf_label: str,
    interval_ms: int,
    count: int,
    now_ms: Optional[int] = None,
) -> List[str]:
    """Formats the most recent `count` closed OHLCV bars (newest first)."""
    all_closed = _closed_kline_bars(bars, interval_ms, now_ms=now_ms)
    closed = all_closed[-count:]
    t_fmt = "%Y-%m-%d" if interval_ms >= 86_400_000 else "%Y-%m-%d %H:%M"
    out = [
        f"**{tf_label} Closed Candles (Last {len(closed)} of {len(all_closed)} available, Newest First):**",
        "| Open Time (UTC) | Open | High | Low | Close | Chg% | Vol (BTC) |",
        "|---|---|---|---|---|---|---|",
    ]
    if not closed:
        out.append("| `N/A` | `N/A` | `N/A` | `N/A` | `N/A` | `N/A` | `N/A` |")
        return out
    for b in reversed(closed):
        o = float(b.open)
        h = float(b.high)
        l = float(b.low)
        c = float(b.close)
        v = float(b.volume)
        chg = ((c / o) - 1.0) * 100.0 if o > 0.0 else 0.0
        out.append(
            f"| `{_fmt_ts_utc(b.timestamp_ms, t_fmt)}` | `${o:,.2f}` | `${h:,.2f}` | "
            f"`${l:,.2f}` | `${c:,.2f}` | `{chg:+.2f}%` | `{v:,.0f}` |"
        )
    return out


def _query_tab_d_trajectory_rows(db_path: pathlib.Path, limit: int = 6) -> List[Tuple[str, str, str, str, str, str]]:
    """Reads up to `limit` closed-4H snapshots from SQLite for Section 7 trajectory context."""
    if not db_path.exists():
        return []
    conn: Optional[sqlite3.Connection] = None
    try:
        conn = sqlite3.connect(str(db_path), timeout=2.0)
        raw_rows = conn.execute(
            """
            SELECT closed_4h_bar_utc, spot_price, payload_json
            FROM telemetry_snapshots
            ORDER BY closed_4h_bar_utc DESC
            LIMIT ?
            """,
            (int(limit),),
        ).fetchall()
    except sqlite3.Error:
        return []
    finally:
        if conn is not None:
            conn.close()

    out: List[Tuple[str, str, str, str, str, str]] = []
    for bar_utc, spot_px, payload_raw in raw_rows:
        panels: dict = {}
        try:
            panels = json.loads(payload_raw).get("panels", {}) or {}
        except Exception:
            panels = {}

        cvd_str = _extract_panel_row(panels, "2_order_flow_liquidity", "Spot/Perp CVD (4h / 24h)")
        if "24h:" in cvd_str:
            cvd_str = "24h:" + cvd_str.split("24h:", 1)[1].strip()
        xexch_oi = _extract_panel_row(panels, "3_derivatives_options_liq", "Cross-Exch Perp OI & Funding")
        fund_p90 = _extract_panel_row(panels, "3_derivatives_options_liq", "Funding 8H% / Ann% / 90D Pct")
        if fund_p90 == "N/A":
            fund_p90 = _extract_panel_row(panels, "3_derivatives_options_liq", "Funding 8H% / Ann% / P90")
        mvrv_s = _extract_panel_row(panels, "4_onchain_etf_stablecoins", "MVRV Ratio (On-Chain / Proxy)")
        out.append((
            str(bar_utc),
            f"${float(spot_px):,.2f}",
            cvd_str,
            xexch_oi,
            fund_p90,
            mvrv_s,
        ))
    return out


def evaluate_hard_market_veto(
    store: StateStore,
    spot_px: float = 0.0,
    struct_4h: Optional[Dict[str, str]] = None,
    now_ms: Optional[int] = None,
) -> Dict[str, str]:
    """Evaluates the deterministic Gate 0 Bidirectional Regime Router from closed 1D/4H bars."""
    bars_1d = list(getattr(store, "spot_klines_1d", []) or [])
    bars_4h = list(getattr(store, "spot_klines_4h", []) or [])
    closed_1d = _closed_kline_bars(bars_1d, 86_400_000, now_ms=now_ms)

    if struct_4h is None:
        struct_4h = _summarize_kline_structure(bars_4h, spot_px, "4H", 14_400_000, lookback=500, now_ms=now_ms)

    last_1d_close: Optional[float] = None
    last_1d_close_str = "UNAVAILABLE"
    if closed_1d:
        last_bar = closed_1d[-1]
        c_px = float(last_bar.close)
        if c_px > 0.0:
            last_1d_close = c_px
            bar_open_utc = _fmt_ts_utc(int(last_bar.timestamp_ms), "%Y-%m-%d")
            bar_close_utc = _fmt_ts_utc(int(last_bar.timestamp_ms) + 86_400_000, "%Y-%m-%d %H:%M UTC")
            last_1d_close_str = f"${c_px:,.2f} (1D bar {bar_open_utc} · closed {bar_close_utc})"

    sma200_val: Optional[float] = None
    if len(closed_1d) >= 200:
        # Derive 1D SMA 200 strictly from the same closed Binance Spot 1D series as last_1d_close
        sma200_val = sum(float(b.close) for b in closed_1d[-200:]) / 200.0

    sma200_str = f"${sma200_val:,.2f}" if (sma200_val is not None and sma200_val > 0.0) else "UNAVAILABLE"

    if last_1d_close is not None and sma200_val is not None and sma200_val > 0.0:
        diff_usd = last_1d_close - sma200_val
        diff_pct = (diff_usd / sma200_val) * 100.0
        sign_str = "-" if diff_usd < 0 else "+"
        dist_str = f"{diff_pct:+.2f}% ({sign_str}${abs(diff_usd):,.2f})"
        below_sma200 = last_1d_close < sma200_val
        sma200_pos = "BELOW" if below_sma200 else "ABOVE"
        cond_a = "YES" if below_sma200 else "NO"
    else:
        dist_str = "UNAVAILABLE"
        sma200_pos = "UNAVAILABLE"
        cond_a = "UNAVAILABLE"

    raw_struct_4h = str(struct_4h.get("structure") or "INSUFFICIENT_DATA")
    raw_bos_4h = str(struct_4h.get("bos") or "N/A")
    bos_down = False
    if raw_struct_4h == "INSUFFICIENT_DATA":
        struct_4h_cat = "UNAVAILABLE"
        bos_4h_str = "UNAVAILABLE"
        cond_b = "UNAVAILABLE"
    else:
        if raw_struct_4h.startswith("UPTREND"):
            struct_4h_cat = "UPTREND (HH/HL)"
        elif raw_struct_4h.startswith("DOWNTREND"):
            struct_4h_cat = "DOWNTREND (LH/LL)"
        else:
            struct_4h_cat = f"MIXED ({raw_struct_4h})" if not raw_struct_4h.startswith("MIXED") else raw_struct_4h

        bos_down = raw_bos_4h.startswith("BOS Down")
        bos_4h_str = (
            f"YES ({raw_bos_4h})"
            if bos_down
            else (f"NO ({raw_bos_4h})" if raw_bos_4h not in ("N/A", "None in window") else "NO (No Downside BOS in window)")
        )
        cond_b = "YES" if (struct_4h_cat.startswith("DOWNTREND") or bos_down) else "NO"

    mi = getattr(store, "macro_intermarket", None)
    cal_fetched = bool(getattr(mi, "macro_calendar_fetched", False)) if mi is not None else False
    cal_events = (getattr(mi, "macro_calendar_events", None) or []) if mi is not None else []
    near_events = [
        ev_c for ev_c in cal_events
        if isinstance(ev_c, dict)
        and isinstance(ev_c.get("minutes_away"), (int, float))
        and -60.0 <= float(ev_c["minutes_away"]) <= 1440.0
    ]
    if near_events:
        first_ev = near_events[0]
        m_away = float(first_ev["minutes_away"])
        cd_s = f"{abs(m_away):.0f}m ago" if m_away < 0 else (f"in {m_away:.0f}m" if m_away < 120 else f"in {m_away / 60.0:.1f}h")
        macro_caution = f"CAUTION (<24h: {first_ev.get('title', 'USD Event')} {cd_s})"
    elif cal_fetched:
        macro_caution = "CLEAR (>24h / NONE)"
    else:
        macro_caution = "UNAVAILABLE"

    if cond_a == "UNAVAILABLE" or cond_b == "UNAVAILABLE":
        active_route = "UNDETERMINED"
        primary_rail = "HOLD_BOTH_RAILS (FAIL-CLOSED — VERIFY DATA)"
        btc_posture = "HOLD BTC (FAIL-CLOSED — VERIFY DATA)"
        usdt_posture = "HOLD USDT (FAIL-CLOSED — VERIFY DATA)"
        veto_status = "UNDETERMINED"
        portfolio_status = "HOLD CURRENT INVENTORY (FAIL-CLOSED — VERIFY DATA)"
        new_entry = "PROHIBITED"
    elif cond_a == "YES" and cond_b == "YES":
        active_route = "MACRO_DOWNTREND_DISTRIBUTION"
        primary_rail = "RAIL A — BTC -> USDT CONVERSION (DEFENSIVE / SELL RALLIES)"
        btc_posture = "ACTIVE (RAIL A) — CONVERT INTO OVERHEAD RESISTANCE"
        usdt_posture = "RESTRICTED (RAIL B) — HOLD PENDING VALIDATED SWEEP & RECLAIM"
        veto_status = "ACTIVE"
        portfolio_status = "RAIL A PRIMARY (BTC -> USDT) / RAIL B RESTRICTED"
        new_entry = "RESTRICTED TO VALIDATED SWEEP RECLAIM"
    elif cond_a == "NO" and struct_4h_cat.startswith("UPTREND") and not bos_down:
        active_route = "MACRO_UPTREND_MARKUP"
        primary_rail = "RAIL B — USDT -> BTC ACCUMULATION (BUY PULLBACKS)"
        btc_posture = "HOLD (RAIL A SELECTIVE TRIM AT MAJOR RESISTANCE / UPPER 7C)"
        usdt_posture = "ACTIVE (RAIL B) — ACCUMULATE 4H HIGHER-LOW PULLBACKS"
        veto_status = "INACTIVE"
        portfolio_status = "RAIL B PRIMARY (USDT -> BTC) / RAIL A TRIM EXTREMES"
        new_entry = "ELIGIBLE FOR FULL ASSESSMENT"
    else:
        active_route = "TRANSITIONAL_RANGE"
        primary_rail = "TWO_WAY_RANGE_HARVEST (BOUNDARY SWINGS)"
        btc_posture = "TWO-WAY HARVEST — CONVERT AT 7A RESISTANCE & UPPER 7C"
        usdt_posture = "TWO-WAY HARVEST — DEPLOY AT 7A SUPPORT & LOWER 7C SWEEPS"
        veto_status = "INACTIVE"
        portfolio_status = "TWO_WAY_RANGE_HARVEST (BOTH RAILS ACTIVE AT BOUNDARIES)"
        new_entry = "ELIGIBLE FOR FULL ASSESSMENT"

    return {
        "last_1d_close_str": last_1d_close_str,
        "sma200_1d_str": sma200_str,
        "dist_vs_sma200_str": dist_str,
        "sma200_pos": sma200_pos,
        "struct_4h_str": struct_4h_cat,
        "bos_4h_str": bos_4h_str,
        "cond_a": cond_a,
        "cond_b": cond_b,
        "macro_caution": macro_caution,
        "active_route": active_route,
        "primary_rail": primary_rail,
        "btc_sleeve_posture": btc_posture,
        "usdt_sleeve_posture": usdt_posture,
        "veto_status": veto_status,
        "portfolio_status": portfolio_status,
        "new_entry": new_entry,
    }


def build_tab_d_data_only_report(
    config: Optional[EngineConfig],
    store: StateStore,
    db_path: Optional[pathlib.Path] = None,
) -> str:
    """Builds the self-contained consolidated telemetry & AI-ready report for Tab [21: D]."""
    from analytics.data_hub_engine import DEFAULT_ARCHIVE_DB_PATH, DataHubEngine, _is_test_runner

    cfg = config or DEFAULT_CONFIG
    ev = getattr(store, "data_hub_evaluation", None) or DataHubEngine(cfg).evaluate(store)
    utc_str, sgt_str = _timestamps_utc_sgt()

    spot_px = float(ev.spot_price or 0.0)
    bars_1h = list(getattr(store, "spot_klines_1h", []) or [])
    bars_4h = list(getattr(store, "spot_klines_4h", []) or [])
    bars_1d = list(getattr(store, "spot_klines_1d", []) or [])

    struct_rows = [
        _summarize_kline_structure(bars_1d, spot_px, "1D", 86_400_000, lookback=500),
        _summarize_kline_structure(bars_4h, spot_px, "4H", 14_400_000, lookback=500),
        _summarize_kline_structure(bars_1h, spot_px, "1H", 3_600_000, lookback=500),
    ]
    veto = evaluate_hard_market_veto(store, spot_px=spot_px, struct_4h=struct_rows[1])

    if len(bars_1h) >= 24 and spot_px > 0.0:
        w24 = bars_1h[-24:]
        low_24h = min(float(b.low) for b in w24)
        high_24h = max(float(b.high) for b in w24)
        range_24h_str = f"${low_24h:,.2f} - ${high_24h:,.2f}"
        base_24h = float(w24[0].open)
        r24_str = f"{((spot_px / base_24h) - 1.0) * 100.0:+.2f}%" if base_24h > 0 else "N/A"
    elif bars_1d and spot_px > 0.0:
        last_d = bars_1d[-1]
        range_24h_str = f"${float(last_d.low):,.2f} - ${float(last_d.high):,.2f}"
        r24_str = "N/A"
    else:
        range_24h_str = "N/A"
        r24_str = "N/A"

    r7_str = (
        f"{((spot_px / float(bars_1d[-8].close)) - 1.0) * 100.0:+.2f}%"
        if (len(bars_1d) >= 8 and spot_px > 0.0 and float(bars_1d[-8].close) > 0.0)
        else "N/A"
    )
    r30_str = (
        f"{((spot_px / float(bars_1d[-31].close)) - 1.0) * 100.0:+.2f}%"
        if (len(bars_1d) >= 31 and spot_px > 0.0 and float(bars_1d[-31].close) > 0.0)
        else "N/A"
    )

    ws_row = next((r for r in ev.panel_6_macro_onchain if r.label == "WebSocket Feeds & Warmup"), None)
    expected_ws_offline = (
        1
        if (
            ws_row is not None
            and ws_row.status == "STALE"
            and "Warm:YES" in str(ws_row.value)
            and "no tick" in str(ws_row.value)
        )
        else 0
    )
    genuine_stale = max(0, int(ev.stale_count) - expected_ws_offline)

    lines: List[str] = [
        "# TAB [D: DATA HUB] | CONSOLIDATED DATA-ONLY TELEMETRY REPORT",
        f"**Retrieval Time (UTC):** `{utc_str}`  |  **Retrieval Time (SGT):** `{sgt_str}`",
        f"**Spot Price (BTCUSDT):** `${spot_px:,.2f}`  |  "
        f"**Coverage:** `OK={ev.ok_count}/{ev.total_metrics} | UNAVAILABLE={ev.unavailable_count} | "
        f"STALE={ev.stale_count} (Genuine={genuine_stale}, Expected_Headless_WS_Offline={expected_ws_offline}) | "
        f"PROXY/STATIC={ev.proxy_or_static_count}`",
        f"**24H Range:** `{range_24h_str}`  |  **Returns (24H / 7D / 30D):** `{r24_str} / {r7_str} / {r30_str}`",
        f"**Archive (SQLite):** `{ev.archive_snapshots_count} closed-4H snapshots (Last: {ev.archive_last_bar_utc or 'N/A'})`",
        "",
        "## 0. BIDIRECTIONAL REGIME ROUTER (GATE 0 — DUAL-INVENTORY SPOT WORKSTATION)",
        "| Router Field | Value | Rule / Threshold |",
        "|---|---|---|",
        f"| Latest Closed 1D Candle Close | `{veto['last_1d_close_str']}` | `Same closed Binance Spot 1D series only (live candle excluded)` |",
        f"| Current 1D SMA 200 | `{veto['sma200_1d_str']}` | `200-bar SMA of same closed Binance Spot 1D series` |",
        f"| Distance vs 1D SMA 200 | `{veto['dist_vs_sma200_str']}` | `(Closed 1D Close - 1D SMA 200) / 1D SMA 200` |",
        f"| 1D SMA 200 Position | `{veto['sma200_pos']}` | `BELOW if Closed 1D Close < 1D SMA 200 else ABOVE` |",
        f"| Closed 4H Market Structure (`7A`) | `{veto['struct_4h_str']}` | `UPTREND / DOWNTREND / MIXED (500 closed 4H bars)` |",
        f"| 4H Downside BOS Status (`7A`) | `{veto['bos_4h_str']}` | `YES if latest closed 4H BOS is BOS Down else NO` |",
        f"| Upcoming Macro Event Caution (`7C`) | `{veto['macro_caution']}` | `CAUTION (<24h USD high-impact event) else CLEAR` |",
        f"| Timestamp & Candle Closed Status | `{utc_str} | {sgt_str} · Closed-Candle Inputs Only` | `Strict closed-bar verification gate` |",
        "",
        "**BIDIRECTIONAL REGIME ROUTER STATUS:**",
        f"- **Active Route:** `{veto['active_route']}`",
        f"- **Primary Active Rail:** `{veto['primary_rail']}`",
        f"- **Active BTC Inventory (`Rail A: BTC -> USDT`):** `{veto['btc_sleeve_posture']}`",
        f"- **Active USDT Inventory (`Rail B: USDT -> BTC`):** `{veto['usdt_sleeve_posture']}`",
        f"- **Condition A (`1D Close < 1D SMA 200`):** `{veto['cond_a']}`  |  **Condition B (`4H Downside Structure / BOS`):** `{veto['cond_b']}`",
        "",
    ]
    sections = (
        ("1. PRICE, TREND & MARKET STRUCTURE", ev.panel_1_feeds),
        ("2. ORDER FLOW, FOOTPRINT & LIQUIDITY", ev.panel_2_trend_vol),
        ("3. DERIVATIVES, OPTIONS & LIQUIDATIONS", ev.panel_3_structure_magnets),
        ("4. ON-CHAIN, ETF & STABLECOIN FLOWS", ev.panel_4_flow_quant),
        ("5. MACRO, CREDIT & US LIQUIDITY", ev.panel_5_derivs_liq),
        ("6. QUANT FEATURES, FEED HEALTH & ARCHIVE", ev.panel_6_macro_onchain),
    )
    for title, rows in sections:
        lines.append(f"## {title}")
        lines.append("| Metric | Value | Source Tabs | Status |")
        lines.append("|---|---|---|---|")
        for r in rows:
            lines.append(f"| {r.label} | `{r.value}` | `{r.tabs}` | `{r.status}` |")
        lines.append("")

    archive_db = db_path if db_path is not None else (None if _is_test_runner() else DEFAULT_ARCHIVE_DB_PATH)
    traj_rows = _query_tab_d_trajectory_rows(archive_db, limit=6) if archive_db is not None else []
    lines.extend([
        "## 7. RECENT CLOSED-4H SNAPSHOT TRAJECTORY (SQLITE ARCHIVE)",
        "| Closed 4H Bar (UTC) | Spot ($) | 24H Spot/Perp CVD | Cross-Exch Perp OI & Funding | Funding 8H% / 90D Pct | MVRV Ratio |",
        "|---|---|---|---|---|---|",
    ])
    if traj_rows:
        for bar_u, sp_u, cvd_u, oi_u, fp_u, mv_u in traj_rows:
            lines.append(f"| `{bar_u}` | `{sp_u}` | `{cvd_u}` | `{oi_u}` | `{fp_u}` | `{mv_u}` |")
    else:
        lines.append("| `N/A` | `N/A` | `N/A` | `N/A` | `N/A` | `N/A` |")

    lines.extend([
        "",
        "### 7A. 500-BAR MARKET STRUCTURE & HISTORICAL S/R ZONES (`1D / 4H / 1H`)",
        "| TF (Bars) | Swing Structure | Last Swing Pivots | Latest BOS | Resistance Zones (Above Spot) | Support Zones (Below Spot) |",
        "|---|---|---|---|---|---|",
    ])
    for sr in struct_rows:
        lines.append(
            f"| `{sr['tf']} ({sr['bars']})` | `{sr['structure']}` | `{sr['pivots']}` | "
            f"`{sr['bos']}` | `{sr['res']}` | `{sr['sup']}` |"
        )

    lines.extend([
        "",
        "### 7B. RECENT CLOSED KLINES — OHLCV PRICE ACTION (`1D`×7, `4H`×12, `1H`×12)",
    ])
    for bars_tf, tf_lbl, iv_ms, cnt in (
        (bars_1d, "1D", 86_400_000, 7),
        (bars_4h, "4H", 14_400_000, 12),
        (bars_1h, "1H", 3_600_000, 12),
    ):
        lines.extend(_build_recent_ohlcv_lines(bars_tf, tf_lbl, iv_ms, cnt))
        lines.append("")

    mag = getattr(store, "btc_magnet_evaluation", None)
    tiers_6 = (getattr(mag, "levels_ladder", None) or {}).get("tiers_6") if mag is not None else None
    lines.extend([
        "### 7C. MODELED LIQUIDATION LADDER (`10x-100x`) & USD MACRO CALENDAR",
        "**6-Tier Modeled Liquidation Ladder:**",
        "| Tier | Side | Level ($) | Dist% | Est Pool ($M) |",
        "|---|---|---|---|---|",
    ])
    if isinstance(tiers_6, list) and tiers_6:
        for t in tiers_6:
            tier_name = str(t.get("tier") or "N/A")
            side = str(t.get("side") or "N/A").upper()
            px = t.get("price")
            dp = t.get("distance_pct")
            vm = t.get("estimated_vol_m")
            px_s = f"${float(px):,.2f}" if isinstance(px, (int, float)) else "N/A"
            dp_s = f"{float(dp):+.2f}%" if isinstance(dp, (int, float)) else "N/A"
            vm_s = f"${float(vm):.1f}M" if isinstance(vm, (int, float)) else "N/A"
            lines.append(f"| `{tier_name}` | `{side}` | `{px_s}` | `{dp_s}` | `{vm_s}` |")
    else:
        lines.append("| `DATA UNAVAILABLE` | `N/A` | `N/A` | `N/A` | `N/A` |")

    mi = getattr(store, "macro_intermarket", None)
    cal_events = (getattr(mi, "macro_calendar_events", None) or []) if mi is not None else []
    cal_fetched = bool(getattr(mi, "macro_calendar_fetched", False)) if mi is not None else False
    lines.extend([
        "",
        "**Upcoming USD High-Impact Macro Events (`-60m` to `+7d`):**",
        "| Event | Time (UTC) | Countdown | Forecast | Previous |",
        "|---|---|---|---|---|",
    ])
    if isinstance(cal_events, list) and cal_events:
        for cev in cal_events[:6]:
            mins = cev.get("minutes_away")
            if isinstance(mins, (int, float)):
                cd_s = f"{abs(mins):.0f}m ago" if mins < 0 else (f"in {mins:.0f}m" if mins < 120 else f"in {mins / 60.0:.1f}h")
            else:
                cd_s = "N/A"
            fc_s = str(cev.get("forecast") or "-")
            pr_s = str(cev.get("previous") or "-")
            lines.append(
                f"| `{cev.get('title', 'USD Event')}` | `{cev.get('time_utc', 'N/A')}` | "
                f"`{cd_s}` | `{fc_s}` | `{pr_s}` |"
            )
    elif cal_fetched:
        lines.append("| `NONE (next 7d)` | `-` | `CLEAR` | `-` | `-` |")
    else:
        lines.append("| `DATA UNAVAILABLE` | `N/A` | `N/A` | `N/A` | `N/A` |")
    lines.append("")

    lines.extend([
        "## 8. METRIC FORMULA LEGEND & CORTEX DIBSE BIDIRECTIONAL PROTOCOL",
        "- **Rough Path Lévy (`4H A_SP`)**: Lévy signed area over 6 closed 4H bars (`> 0`: Spot path leads price markup; `< 0`: Spot path lags price / distribution).",
        "- **24H Z-Scores (`z_S / z_F / D`)**: 30-day rolling Z-scores of 24H Spot (`z_S`) and Perp (`z_F`) cumulative delta; `D = z_S - z_F` (`D > 0` = Spot buying divergence vs Perps).",
        "- **Spot CVD Slopes (`7D / 14D`) & 4H Vol Context**: Cumulative spot taker-delta over last `7`/`14` closed `1D` bars; `4H ATR(14)% Pctile` ranks current closed `4H` ATR% against the trailing `120` closed `4H` bars, paired with `RelVol(20)` (`closed 4H volume / 20-bar SMA`).",
        "- **Volume Profile & Structure**: `30D VA Pos% = (Spot - VAL) / (VAH - VAL) * 100` (Macro 30D Value Area); `ATR(14) 1D/4H/1H`; `L20/H20` = 20-bar (80H) 4H range boundaries; `SLSP` = structural liquidity pool S/R; `7A` scans up to 500 closed bars per TF (`1D ~499d`, `4H ~83d`, `1H ~21d`) using `5x5` pivots for `HH/HL/LH/LL`, `BOS`, and `1%`-clustered S/R zones (deep prior-quarter supports appear on `1D` even if outside the `83d` `4H` window).",
        "- **Derivatives, Modeled Ladder & Quant**: `90D Pct` = 0-100 rolling 90-day percentile rank of 8H funding; `[... X/3 PARTIAL_VENUE]` suppresses OI quadrant tagging when `<3` venues report; `Hyperliquid Perp` reports DEX OI and 8H-normalized funding independently; `Modeled Liq Ladder (7C)` estimates 10x-100x leverage shelves (not private exchange orderbooks); `USD Macro Calendar` tracks high-impact USD releases; `H` = Hurst exponent (`>0.5` trending, `<0.5` mean-reverting); `VCR 72H` = Volatility Compression Ratio; `TSFM Disp%` = horizon dispersion; `LSCE` = liquidation sweep state.",
        "- **Headless Snapshot Note**: Scheduled/GitHub Actions runs execute a one-shot REST warmup (`Warm:YES`) without a persistent WebSocket loop, so `WebSocket Feeds & Warmup` reporting `STALE` (`no tick`) is isolated in `Coverage` as `Expected_Headless_WS_Offline=1` and does not indicate stale REST, orderbook, CVD, or derivatives data.",
        "",
        "### DIRECT AI EXECUTION PROTOCOL: CORTEX DIBSE BIDIRECTIONAL DESK v1.0",
        "Analyze BTC using the telemetry snapshot above. Operate as **CORTEX DIBSE BIDIRECTIONAL DESK v1.0** — a Spot-Only Dual-Inventory (Active BTC Inventory & Active USDT Inventory, zero leverage, user-agnostic allocation) Bidirectional Swing Workstation. Apply strict **zero-hallucination** rules using only metrics explicitly reported above (`0`, `1-6`, `7`, `7A`, `7B`, `7C`).",
        "",
        "**Gate 0 — BIDIRECTIONAL REGIME ROUTER (EVALUATE FIRST, BEFORE ALL OTHER SIGNALS):**",
        "- Verify Section `0` (`1D Close vs 1D SMA 200`, `4H Structure / BOS`, and `Upcoming Macro Event Caution (7C)`) BEFORE scoring lower-timeframe setups.",
        "- **Regime Routing Logic (closed Binance Spot candles only):**",
        "  - **MACRO_DOWNTREND_DISTRIBUTION (`1D Close < 1D SMA 200` AND (`4H DOWNTREND` OR `4H BOS Down = YES`)):**",
        "    - **Primary Active Rail:** `RAIL A — BTC -> USDT CONVERSION` (sell/trim active BTC inventory into overhead resistance or failing rebounds with defined buy-back invalidation and lower rebuy targets).",
        "    - **Secondary Rail:** `RAIL B — USDT -> BTC ACCUMULATION` is **RESTRICTED** to validated capitulation sweeps (`3-Gate Reversal`: sweep of major `1D/4H` support or `7C` long liquidation tier + closed-candle reclaim + positive `Spot CVD` / `4H A_SP > 0` absorption) — zero blind falling-knife buying.",
        "  - **MACRO_UPTREND_MARKUP (`1D Close > 1D SMA 200` AND `4H UPTREND (HH/HL)` AND `4H BOS Down = NO`):**",
        "    - **Primary Active Rail:** `RAIL B — USDT -> BTC ACCUMULATION` (deploy USDT on validated `4H HL` pullbacks with `<= 0.75%` max portfolio risk).",
        "    - **Secondary Rail:** `RAIL A — BTC -> USDT TRIM` activates selectively only at major `1D/4H` resistance or upper `7C` short liquidation shelves when `RSI(14) > 70` and `z_S` / `4H A_SP` show distribution divergence.",
        "  - **TRANSITIONAL_RANGE (Mixed `1D` vs `4H`):**",
        "    - **Active Rail:** `TWO_WAY_RANGE_HARVEST` — Convert `BTC -> USDT` at `7A/SLSP` resistance, `30D VAH`, or upper `7C` short clusters; deploy `USDT -> BTC` at `7A/SLSP` support, `30D VAL`, or lower `7C` long sweeps.",
        "  - **FAIL-CLOSED (`UNDETERMINED`):** If `1D Close`, `1D SMA 200`, or `4H Structure` is `UNAVAILABLE`, hold both rails (`HOLD BTC / HOLD USDT — NO EXECUTION`) until data is verified.",
        "- Section `5` `Legacy_200D_Veto_Override` is permanently `IGNORED` for Desk v1.0.",
        "",
        "**Step 1 — Mandatory Data Hygiene Gate:**",
        "- Verify `Coverage` distinguishing: (a) genuine stale market data (`Genuine=...`), (b) expected headless WS inactivity (`Expected_Headless_WS_Offline=...` when `Warm:YES` REST-only run), (c) `[PROXY]` feeds, and (d) `UNAVAILABLE` feeds.",
        "- Never treat expected headless WebSocket inactivity (`Expected_Headless_WS_Offline=1`) as a genuine REST/derivatives/orderbook market-data failure.",
        "- Flag `[... PARTIAL_VENUE]` on `Cross-Exch Perp OI & Funding` or Section `7` history — never treat partial venue counts (`< 3/3`) as genuine deleveraging.",
        "- Read `90D Pct` strictly as a `0-100` rolling 90-day funding rank, `30D VA Pos%` strictly vs Macro 30D VAH/VAL, `ATR(14) 1D/4H/1H` across matching timeframes, and treat `Modeled Liq Ladder (7C)` as an algorithmic estimate (not private orderbook depth).",
        "- Check `USD Macro Calendar (High)`: treat `NONE (next 7d)` as a clear schedule (`OK`) vs `UNAVAILABLE` as offline.",
        "- Do not cite missing metrics or external prices outside this telemetry snapshot.",
        "",
        "**Step 2 — 5-Function Bidirectional Synthesis:**",
        "1. **Multi-Timeframe Regime Classifier:** Integrate Section `1`, `7A` (`1D/4H/1H` swing structure & BOS), `7B` closed OHLCV price action, `1D/4H` ADX, `RSI(14)`, `4H ATR(14)% Pctile` & `RelVol(20)` (volatility regime & volume participation), EMA/SMA stack, and Hurst `H` -> classify as `UPTREND`, `DOWNTREND`, `RANGE-BOUND`, or `TRANSITIONAL`.",
        "2. **Spot Flow & Rough Path Inspector:** Evaluate `Spot/Perp CVD` across `15m/1h/4h/24h`, multi-day `Spot CVD Slopes (7D / 14D)`, `z_S / z_F / D`, `Rough Path Lévy (4H A_SP)` (`> 0` spot leads markup; `< 0` spot leads distribution), `Coinbase Premium`, `L2 Depth`, `OBI`, `Spr`, `30D VA Pos%`, `SLSP`, and `7A` S/R clusters -> classify true spot accumulation/absorption vs distribution/short-covering bounce.",
        "3. **Derivatives & Squeeze Asymmetry Profiler:** Evaluate `BN OI`, `Cross-Exch OI` (only when `3/3` venues valid), `Hyperliquid Perp OI & Funding` (`[HL DEX]` vs CEX positioning), `OI Δ%` & Quad, `Funding 8H% / Ann% / 90D Pct`, `DVOL`, `25d RR Skew`, and `6-Tier Modeled Liq Ladder (7C)` (`10x-100x` upper/lower distance & `$M` asymmetry) -> identify whether `UPPER` shorts or `LOWER` longs form the primary liquidity magnet.",
        "4. **Macro, On-Chain & ETF Gatekeeper:** Synthesize `MVRV`, `SOPR`, `Exchange Netflow 24H`, Farside `US Spot ETF Flow (1D / 3D / 5D)` (use `IBIT+FBTC` `[PROXY]` only as secondary context), `Stablecoin Supply / Net Issuance`, `DXY`, `US10Y`, `VIX`, `SPX`, `Net Liquidity`, and `USD Macro Calendar (High)` (`7C` event proximity within `24h` or `±30m` high-impact windows) -> assign macro backdrop (`Tailwind`, `Neutral`, or `Headwind`).",
        "5. **Dual-Inventory Risk & Execution Arbiter:**",
        "   - **Rail A (`BTC -> USDT` Conversion Rules):** Activate when price stalls or reverses at `4H/1D/SLSP` resistance or upper `7C` short liquidation shelves while `1D < SMA 200` or `4H A_SP < 0` / `7D Spot CVD < 0` (or euphoria extremes in `MACRO_UPTREND_MARKUP`). Output exact **Overhead Conversion Zone**, **Suggested % of Active BTC Inventory to Convert**, **Upper Buy-Back Invalidation Stop** (where converted BTC is repurchased if breakout invalidates downside thesis), and **Lower USDT Rebuy Targets** to compound BTC quantity.",
        "   - **Rail B (`USDT -> BTC` Accumulation Rules):** Activate on validated `4H HL` pullbacks in uptrends, OR validated `1H/4H` sweep-and-reclaim reversals below `7A/SLSP` support or `7C` long liquidation shelves with positive `Spot CVD`, `z_S > 0`, and `4H A_SP > 0`. Enforce `<= 0.75%` max portfolio risk per qualified position and guard against unhedged entries inside `< 24h` USD high-impact macro windows.",
        "",
        "**Step 3 — Mandatory Bidirectional Output Contract:**",
        "- **0. BIDIRECTIONAL REGIME ROUTER (`GATE 0`)** (`Active Route`, `Condition A (1D vs SMA 200)`, `Condition B (4H Structure/BOS)`, `Macro <24h Window`, **`BTC Inventory Action (Rail A: BTC -> USDT): SELL (CONVERT TO USDT) / HOLD BTC`**, **`USDT Inventory Action (Rail B: USDT -> BTC): BUY (DEPLOY TO BTC) / HOLD USDT`**).",
        "- **1. EXECUTIVE SUMMARY & DUAL-INVENTORY POSTURE** (`Spot Price`, `Regime State`, explicit **`BTC Inventory Action`** & **`USDT Inventory Action`**, `Confidence /100`).",
        "- **2. DATA HYGIENE AUDIT** (Exact `OK/UNAVAILABLE/STALE/PROXY` tally, headless WS clarification, any `PARTIAL_VENUE` anomalies, degraded-signal list).",
        "- **3. MULTI-TIMEFRAME REGIME & ROUGH PATH FLOW SYNTHESIS** (Price/EMA/ADX + `4H ATR% Pctile / RelVol` vs `4H A_SP` Lévy area, intraday & `7D/14D` Spot CVD, Coinbase Premium, and `4H` SQLite Section `7` + `7A/7B` trajectory).",
        "- **4. DERIVATIVES, LIQUIDATION MAGNETS & MACRO BACKDROP** (CEX `3/3` + `Hyperliquid DEX` OI/funding, funding `90D Pct`, options skew, `6-tier Liq Ladder (7C)` upper vs lower squeeze magnets, Farside `1D/3D/5D` ETF flows, `USD Macro Calendar (7C)` event window, and macro backdrop).",
        "- **5. BIDIRECTIONAL LEVELS MAP** (`Rail A` Supply/Conversion Zones, `Rail B` Demand/Rebuy Zones, `7C` modeled liquidation shelves, and Structural Buy-Back / Stop Invalidation Levels tied to `7A/7B` & `SLSP`).",
        "- **6. DUAL-INVENTORY EXECUTION PLAN (`RAIL A` & `RAIL B`)** (**Rail A (`BTC -> USDT`):** Exact Conversion Trigger Zone, Suggested % of Active BTC Inventory, Upper Buy-Back Invalidation Stop, Lower Target Rebuy Zone; **Rail B (`USDT -> BTC`):** Exact Entry Trigger / Confirmation Gate, Stop Loss at `<= 0.75%` portfolio risk, Take Profit Targets, and Macro Event Timing Constraint).",
        "",
    ])

    return sanitize_data_only_text("\n".join(lines))


def copy_tab_data_only_report_to_clipboard(
    tab_id: int,
    config: Optional[EngineConfig],
    store: StateStore,
) -> Tuple[bool, str, int]:
    """Builds and copies the DATA-ONLY report for the given primary tab ID."""
    cfg = config or DEFAULT_CONFIG
    dispatch: Dict[int, Tuple[Callable[[Optional[EngineConfig], StateStore], str], str]] = {
        13: (build_tab_p_data_only_report, "btc_structure_latest.md"),
        15: (build_tab_g_data_only_report, "grok_master_prompt_latest.md"),
        16: (build_tab_r_data_only_report, "ssrn_research_brief_latest.md"),
        17: (build_tab_m_data_only_report, "btc_magnet_latest.md"),
        18: (build_tab_a_data_only_report, "btc_trend_pullback_latest.md"),
        19: (build_tab_q_data_only_report, "btc_four_gate_latest.md"),
        11: (build_tab_f_data_only_report, "btc_footprint_latest.md"),
        12: (build_tab_w_data_only_report, "btc_waterfall_latest.md"),
        0: (build_tab_0_data_only_report, "btc_spot_swing_latest.md"),
        10: (build_tab_l_data_only_report, "btc_master_latest.md"),
        20: (build_tab_x_data_only_report, "btc_futures_v4_latest.md"),
        21: (build_tab_d_data_only_report, "btc_data_hub_latest.md"),
    }
    if tab_id not in dispatch:
        text = build_global_data_only_packet(cfg, store)
        return copy_text_to_clipboard_and_log(text, "latest_ai_data_packet.md", store, also_write_root_and_downloads=True)

    builder, filename = dispatch[tab_id]
    text = builder(cfg, store)
    if tab_id == 21:
        from analytics.data_hub_engine import _is_test_runner

        if not _is_test_runner():
            downloads_dir = pathlib.Path.home() / "Downloads"
            if downloads_dir.exists():
                try:
                    (downloads_dir / filename).write_text(text, encoding="utf-8")
                except Exception:
                    pass
    return copy_text_to_clipboard_and_log(text, filename, store)
