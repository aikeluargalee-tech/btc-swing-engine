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
import os
import pathlib
import re
import subprocess
import time
from typing import Dict, List, Optional, Tuple

from config.settings import DEFAULT_CONFIG, EngineConfig
from core.state_store import StateStore

MYT_TZ = timezone(timedelta(hours=8))

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


def _timestamps_utc_myt() -> Tuple[str, str]:
    now_utc = datetime.now(timezone.utc)
    now_myt = now_utc.astimezone(MYT_TZ)
    return (
        now_utc.strftime("%Y-%m-%d %H:%M:%S UTC"),
        now_myt.strftime("%Y-%m-%d %H:%M:%S MYT (UTC+8)"),
    )


def _spot_price(store: StateStore) -> float:
    px = float(getattr(store, "binance_spot_price", 0.0) or getattr(store, "spot_price", 0.0) or 0.0)
    if px <= 0 and getattr(store, "spot_klines_1h", None):
        px = float(store.spot_klines_1h[-1].close)
    return round(px, 2)


# ==============================================================================
# 1. TAB [P: STRUCTURE] DATA-ONLY REPORT
# ==============================================================================
def build_tab_p_data_only_report(config: Optional[EngineConfig], store: StateStore) -> str:
    cfg = config or DEFAULT_CONFIG
    ts_utc, ts_myt = _timestamps_utc_myt()
    spot_px = _spot_price(store)
    slsp = getattr(store, "slsp_evaluation", None)
    if slsp is None:
        from analytics.slsp_engine import SLSPEngine
        spot_1d = getattr(store, "spot_klines_1d", []) or []
        bars_4h = getattr(store, "spot_klines_4h", []) or []
        slsp = SLSPEngine(cfg).evaluate(store, spot_1d, bars_4h, current_price=spot_px)
    ema_snap = getattr(store, "ema_strategy", None)
    liq_rep = getattr(slsp, "liq_detector_report", None) if slsp else getattr(store, "liquidation_report", None)

    lines = [
        "# TAB [P: STRUCTURE] | DATA-ONLY METRICS REPORT",
        f"**Retrieval Time (UTC):** `{ts_utc}`  |  **Retrieval Time (MYT):** `{ts_myt}`",
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
        f"- **Trade State:** `{slsp.trade_state}`",
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
            f"- **Support Liquidation Volume USD:** `${supp.liquidation_volume_usd:,.2f}`",
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
            f"- **Resistance Liquidation Volume USD:** `${res.liquidation_volume_usd:,.2f}`",
        ])
    else:
        lines.append("- **Nearest Resistance Shelf Center:** `0.00` (No shelf within 10% scan window)")

    lines.extend([
        "",
        "## 3. LIQUIDATION GRAVITATIONAL HORIZON & LSCE SWEEP ENGINE",
        f"- **Dominant Gravitational Pull:** `{slsp.dominant_pull_dir}`",
        f"- **Immediate Tier (100x) Imbalance Ratio:** `{slsp.immediate_ratio:.2f}x`",
        f"- **Total Ladder (10x-100x) Imbalance Ratio:** `{slsp.total_ladder_ratio:.2f}x`",
        f"- **Upper Liquidation Magnet Cluster:** `${slsp.upper_magnet_price:,.2f}` (`{slsp.upper_magnet_dist_pct:+.2f}%` from Spot) | Volume: `${slsp.upper_magnet_vol_usd / 1e6:.2f}M`",
        f"- **Lower Liquidation Magnet Cluster:** `${slsp.lower_magnet_price:,.2f}` (`{slsp.lower_magnet_dist_pct:+.2f}%` from Spot) | Volume: `${slsp.lower_magnet_vol_usd / 1e6:.2f}M`",
        f"- **LSCE Sweep State:** `[{slsp.lsce_status}]`",
        f"- **LSCE Cluster Tested:** `{slsp.lsce_cluster_tested}`",
        f"- **LSCE Action Verdict:** `{slsp.lsce_action_verdict}`",
    ])

    setup = slsp.active_setup
    ref_entry = round(float(setup.entry_price), 2) if (setup and setup.entry_price > 0) else spot_px
    ref_stop = round(float(setup.stop_loss), 2) if (setup and setup.stop_loss > 0) else round(spot_px * 0.98, 2)
    stop_dist = round(ref_entry - ref_stop, 2)
    ref_1_5r = round(ref_entry + 1.5 * stop_dist, 2) if stop_dist > 0 else 0.0
    ref_2_5r = round(ref_entry + 2.5 * stop_dist, 2) if stop_dist > 0 else 0.0
    obs_r = round(float(setup.obstacle_r), 2) if setup else 0.0
    clearance_ok = bool(not setup.obstacle_detected) if setup else False
    sized_btc = round(float(setup.position_size_btc), 4) if setup else 0.0
    notional_usd = round(float(setup.notional_value_usd), 2) if setup else 0.0

    lines.extend([
        "",
        f"## 4. REFERENCE LEVELS & DUAL INVIOLABLE STOPS (Reference calculation if entered at ${ref_entry:,.2f})",
        f"- **Reference Entry Price:** `${ref_entry:,.2f}`",
        f"- **Structural Stop Loss (1H Close):** `${slsp.structural_stop_price:,.2f}` (`{slsp.structural_stop_dist_pct:.2f}%` from Spot)",
        f"- **Disaster Hard Stop (Below 200 SMA & 25x Shelf):** `${slsp.disaster_stop_price:,.2f}` (`{slsp.disaster_stop_dist_pct:.2f}%` from Spot)",
        f"- **Risk Budget Compliance Pass (<= 4.5%):** `{bool(slsp.disaster_stop_dist_pct <= 4.5)}`",
        f"- **Stop Distance (`Reference Entry - Structural Stop`):** `${stop_dist:,.2f}`",
        f"- **1.5R Reference Level (`Entry + 1.5 * Stop Distance`):** `${ref_1_5r:,.2f}`",
        f"- **2.5R Reference Level (`Entry + 2.5 * Stop Distance`):** `${ref_2_5r:,.2f}`",
        f"- **Distance to Overhead Resistance in R (`Obstacle R`):** `{obs_r:.2f}R`",
        f"- **Clearance >= 1.50R (`Obstacle R >= 1.50`):** `{clearance_ok}`",
        f"- **Sized Position (Macro Sized {slsp.macro_sizing_factor:.2f}x):** `{sized_btc:.4f} BTC` (`${notional_usd:,.2f}` notional)",
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
        f"- **15m Relative Volume (`RelVol vs 20-bar SMA`):** `{slsp.tell_tale_relvol_15m:.2f}x` | **15m RelVol >= 5.0x:** `{bool(slsp.tell_tale_relvol_15m >= 5.0)}`",
        f"- **5m Relative Volume (`RelVol vs 20-bar SMA`):** `{slsp.tell_tale_relvol_5m:.2f}x` | **5m RelVol >= 5.0x:** `{bool(slsp.tell_tale_relvol_5m >= 5.0)}`",
        f"- **Volume Climax Interlock Active:** `{bool(slsp.tell_tale_veto)}`",
    ])
    if liq_rep is not None:
        w15 = liq_rep.windows.get("15m")
        w1h = liq_rep.windows.get("1h")
        w4h = liq_rep.windows.get("4h")
        w24h = liq_rep.windows.get("24h")
        lines.extend([
            f"- **Liquidated USD (`15m / 1h / 4h / 24h`):** `${(w15.total_usd if w15 else 0.0):,.0f}` / `${(w1h.total_usd if w1h else 0.0):,.0f}` / `${(w4h.total_usd if w4h else 0.0):,.0f}` / `${(w24h.total_usd if w24h else 0.0):,.0f}`",
            f"- **24H Liquidation Multiple:** `{liq_rep.liquidation_multiple_24h:.2f}x`",
            f"- **Reference Zone (`$75,000 - $78,000`) Distance to Lower / Upper:** `{liq_rep.demand_zone_dist_lower_pct:+.2f}%` / `{liq_rep.demand_zone_dist_upper_pct:+.2f}%`",
        ])

    recon_eval = getattr(store, "reconciliation_evaluation", None)
    if recon_eval is not None:
        lines.extend([
            "",
            "## 7. UPSTREAM DATA INTEGRITY RECONCILIATION GATE",
            f"- **Reconciliation Verdict:** `{recon_eval.verdict}`",
            f"- **Execution Authorization:** `{recon_eval.execution_authorization}`",
            f"- **Trading Status:** `{recon_eval.trading_status}`",
            f"- **Prescribed Capital Allocation:** `{recon_eval.capital_allocation:.2f}x` (`{recon_eval.target_allocation}`)",
            f"- **Portfolio Rotation Directive:** `{recon_eval.portfolio_rotation}`",
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
    ts_utc, ts_myt = _timestamps_utc_myt()
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
        f"**Retrieval Time (UTC):** `{ts_utc}`  |  **Retrieval Time (MYT):** `{ts_myt}`",
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
    ts_utc, ts_myt = _timestamps_utc_myt()
    ssrn = getattr(store, "ssrn_alpha_evaluation", None)
    if ssrn is None:
        from analytics.ssrn_research_engine import SSRNResearchEngine
        ssrn = SSRNResearchEngine(config or DEFAULT_CONFIG).evaluate(store)

    spot_px = round(float(ssrn.spot_price), 2)
    lines = [
        "# TAB [R: SSRN RESEARCH] | DATA-ONLY METRICS REPORT",
        f"**Retrieval Time (UTC):** `{ts_utc}`  |  **Retrieval Time (MYT):** `{ts_myt}`",
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
def build_tab_m_data_only_report(config: Optional[EngineConfig], store: StateStore) -> str:
    ts_utc, ts_myt = _timestamps_utc_myt()
    mag = getattr(store, "btc_magnet_evaluation", None)
    if mag is None:
        from analytics.btc_magnet_engine import BTCMagnetEngine
        mag = BTCMagnetEngine(config or DEFAULT_CONFIG).evaluate(store)

    spot_px = round(float(mag.spot_price), 2)
    up_px = round(float(mag.upper_magnet.price), 2)
    lo_px = round(float(mag.lower_magnet.price), 2)
    up_diff_usd = round(up_px - spot_px, 2)
    lo_diff_usd = round(lo_px - spot_px, 2)
    passed_count = sum(1 for r in mag.rule_checks[:6] if r.passed)

    lines = [
        "# TAB [M: MAGNET] | DATA-ONLY METRICS REPORT",
        f"**Retrieval Time (UTC):** `{ts_utc}`  |  **Retrieval Time (MYT):** `{ts_myt}`",
        f"**Spot Price (BTCUSDT):** `${spot_px:,.2f}` (`24H Change: {mag.price_change_24h_pct:+.2f}%`)",
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

    lines.extend([
        "",
        "## 2. LIQUIDATION GRAVITATIONAL HORIZON & DUAL-LADDER DEPTH",
        f"- **Upper Liquidation Cluster (Short Liquidations):** `${up_px:,.2f}` (`{mag.upper_magnet.dist_pct:+.2f}%` / `${up_diff_usd:+,.2f}` from Spot) | Volume: `${mag.upper_magnet.usd_volume/1e6:.2f}M`",
        f"- **Center Spot Price:** `${spot_px:,.2f}`",
        f"- **Lower Liquidation Cluster (Long Liquidations):** `${lo_px:,.2f}` (`{mag.lower_magnet.dist_pct:+.2f}%` / `${lo_diff_usd:+,.2f}` from Spot) | Volume: `${mag.lower_magnet.usd_volume/1e6:.2f}M`",
        f"- **Immediate Tier (100x) Imbalance Ratio:** `{mag.immediate_ratio:.2f}x` (${mag.immediate_l_vol:.1f}M Lower vs ${mag.immediate_u_vol:.1f}M Upper)",
        f"- **Total Ladder (10x-100x) Imbalance Ratio:** `{mag.total_ladder_ratio:.2f}x` (${mag.total_l_vol:.1f}M Lower vs ${mag.total_u_vol:.1f}M Upper)",
        f"- **Dominant Pull Direction:** `{mag.pull_direction}`",
        "",
        "## 3. LIQUIDATION SWEEP CONFIRMATION ENGINE (LSCE)",
        f"- **LSCE State:** `[{mag.lsce_status}]`",
        f"- **Cluster Tested:** `{mag.lsce_cluster_tested}`",
        f"- **Sweep Depth Pct:** `{mag.lsce_sweep_depth_pct:+.2f}%`",
        f"- **Reclaim Target Level:** `${mag.lsce_reclaim_level:,.2f}`",
        f"- **Spot Absorption Readout:** `{mag.lsce_spot_absorption}`",
        f"- **LSCE Action Verdict:** `{mag.lsce_action_verdict}`",
        "",
        "## 4. INVIOLABLE RISK DIRECTIVES & CAPITAL SIZING",
        f"- **Recommended Spot Sizing:** `{mag.sizing_factor:.2f}x` ({mag.action})",
        f"- **Capital Rotation Directive:** `{mag.rotation}`",
        f"- **Entry Instruction:** `{mag.entry_instruction}`",
        f"- **Structural Invalidation Stop:** `${mag.structural_stop_price:,.2f}` (`{mag.structural_stop_dist_pct:.2f}%` from Spot)",
        f"- **Disaster Hard Stop (Below 200 SMA & 25x Shelf):** `${mag.disaster_stop_price:,.2f}` (`{mag.disaster_stop_dist_pct:.2f}%` from Spot)",
        f"- **Risk Budget Compliance Pass (<= 4.5%):** `{mag.risk_budget_pass}`",
        "",
        "## 5. DERIVATIVES & VOLATILITY INPUTS",
        f"- **Annualized Perpetual Funding Rate:** `{mag.funding_rate_annual_pct:+.2f}%/yr`",
        f"- **4H Open Interest Delta:** `{mag.oi_delta_4h_pct:+.2f}%`",
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
        lines.extend([
            "",
            "## 7. B1 vs B2 DATA INTEGRITY RECONCILIATION AUDIT",
            f"- **Reconciliation Verdict:** `{recon_eval.verdict}`",
            f"- **Execution Authorization:** `{recon_eval.execution_authorization}`",
            f"- **Prescribed Capital Sizing:** `{recon_eval.capital_allocation:.2f}x` ({recon_eval.trading_status})",
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


def build_tab_a_data_only_report(config: Optional[EngineConfig], store: StateStore) -> str:
    tp_ev = getattr(store, "trend_pullback_evaluation", None)
    if tp_ev is None:
        from analytics.strategy_trend_pullback import TrendPullbackEngine
        tp_ev = TrendPullbackEngine(config or DEFAULT_CONFIG).evaluate(store)
    return sanitize_data_only_text(tp_ev.summary_markdown)


def build_tab_q_data_only_report(config: Optional[EngineConfig], store: StateStore) -> str:
    ev = getattr(store, "four_gate_evaluation", None)
    if ev is None:
        from analytics.four_gate_engine import FourGateEngine
        ev = FourGateEngine(config).evaluate(store)
    if ev is None:
        return "# BTC 4-GATE QUANTITATIVE PROTOCOL TELEMETRY\nSTATUS: DATA UNAVAILABLE"

    es = ev.event_study_results or {}
    lines = [
        "# BTC 4-GATE QUANTITATIVE PROTOCOL TELEMETRY PACKET (TAB 19 / [Q])",
        f"TIMESTAMP_UTC: {ev.timestamp_utc}",
        f"LIVE_SPOT_PRICE_USD: {ev.live_spot_price:,.2f}",
        f"LAST_CLOSED_4H_BAR_UTC: {ev.last_closed_bar_utc}",
        f"STATUS: {ev.status}",
        f"VERDICT: {ev.verdict}",
        f"CONFLUENCE_SCORE: {ev.score}/4",
        "",
        "## 1. 4-GATE TELEMETRY METRICS",
        f"GATE_1_LEVY_SIGNED_AREA_PASS: {ev.gate_1_levy}",
        f"GATE_1_A_SP: {ev.gate_1_val:+.4f}",
        f"GATE_1_DETAILS: {ev.gate_1_details}",
        f"GATE_2_SPOT_PERP_ZFLOW_PASS: {ev.gate_2_zflow}",
        f"GATE_2_D_FLOW: {ev.gate_2_val:+.2f}",
        f"GATE_2_Z_SPOT: {ev.gate_2_z_s:+.2f}",
        f"GATE_2_Z_PERP: {ev.gate_2_z_f:+.2f}",
        f"GATE_2_SPOT_24H_DELTA_BTC: {ev.gate_2_ds_24h:+,.1f}",
        f"GATE_3_30D_VOLUME_PROFILE_PASS: {ev.gate_3_structure}",
        f"GATE_3_ACTIVE_STATE: {ev.gate_3_state}",
        f"GATE_3_POC_30_USD: {ev.gate_3_poc:,.2f}",
        f"GATE_3_VAL_30_USD: {ev.gate_3_val:,.2f}",
        f"GATE_3_VAH_30_USD: {ev.gate_3_vah:,.2f}",
        f"GATE_3_L20_20D_LOW_USD: {ev.gate_3_l20:,.2f}",
        f"GATE_4_POSITIONING_FILTER_PASS: {ev.gate_4_positioning}",
        f"GATE_4_PERP_FUNDING_RATE_PCT: {ev.gate_4_funding_rate * 100:+.4f}%",
        f"GATE_4_FUNDING_90D_PERCENTILE: {ev.gate_4_funding_p90:.2f}%",
        f"GATE_4_ACTIVE_RULE: {ev.gate_4_details}",
        "",
        "## 2. 0.75% RISK SHIELD & SIZING TICKET",
        f"ENTRY_PRICE_USD: {ev.entry_price:,.2f}",
        f"HARD_STOP_PRICE_USD: {ev.stop_price:,.2f}",
        f"STOP_DISTANCE_PCT: {ev.stop_pct * 100:.2f}%",
        f"TARGET_1_PRICE_USD: {ev.target_1_price:,.2f}",
        f"DERIBIT_30D_DVOL: {f'{ev.dvol_current:.2f}%' if ev.dvol_current else 'DATA UNAVAILABLE'}",
        f"NOTIONAL_RISK_USD: {ev.notional_risk_usd:,.2f}",
        f"NOTIONAL_VOL_CAP_USD: {ev.notional_vol_usd:,.2f}",
        f"FINAL_SPOT_ALLOCATION_USD: {ev.final_notional_usd:,.2f}",
        f"POSITION_SIZE_BTC: {ev.btc_size:.4f}",
        "",
        "## 3. 90-DAY DE-CLUSTERED IN-SAMPLE EVENT STUDY (5D EMBARGO)",
        f"HISTORICAL_TRIGGERS_N: {ev.event_study_triggers_count}",
        f"SMALL_SAMPLE_CAVEAT: {ev.event_study_small_sample}",
        f"WIN_RATE_1D_PCT: {es.get('win_rate_1d', 0.0):.1f}%",
        f"MEAN_RETURN_1D_PCT: {es.get('mean_ret_1d', 0.0):+.2f}%",
        f"BASELINE_MEAN_1D_PCT: {es.get('baseline_mean_1d', 0.0):+.2f}%",
        f"ALPHA_1D_PCT: {es.get('alpha_1d', 0.0):+.2f}%",
        f"WIN_RATE_3D_PCT: {es.get('win_rate_3d', 0.0):.1f}%",
        f"MEAN_RETURN_3D_PCT: {es.get('mean_ret_3d', 0.0):+.2f}%",
        f"BASELINE_MEAN_3D_PCT: {es.get('baseline_mean_3d', 0.0):+.2f}%",
        f"ALPHA_3D_PCT: {es.get('alpha_3d', 0.0):+.2f}%",
        f"WIN_RATE_5D_PCT: {es.get('win_rate_5d', 0.0):.1f}%",
        f"MEAN_RETURN_5D_PCT: {es.get('mean_ret_5d', 0.0):+.2f}%",
        f"BASELINE_MEAN_5D_PCT: {es.get('baseline_mean_5d', 0.0):+.2f}%",
        f"ALPHA_5D_PCT: {es.get('alpha_5d', 0.0):+.2f}%",
        f"WIN_RATE_10D_PCT: {es.get('win_rate_10d', 0.0):.1f}%",
        f"MEAN_RETURN_10D_PCT: {es.get('mean_ret_10d', 0.0):+.2f}%",
        f"BASELINE_MEAN_10D_PCT: {es.get('baseline_mean_10d', 0.0):+.2f}%",
        f"ALPHA_10D_PCT: {es.get('alpha_10d', 0.0):+.2f}%",
    ]
    return sanitize_data_only_text("\n".join(lines))


# ==============================================================================
# 7. TAB [F: FOOTPRINT] DATA-ONLY REPORT
# ==============================================================================
def build_tab_f_data_only_report(config: Optional[EngineConfig], store: StateStore) -> str:
    ts_utc, ts_myt = _timestamps_utc_myt()
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
        f"**Retrieval Time (UTC):** `{ts_utc}`  |  **Retrieval Time (MYT):** `{ts_myt}`",
        f"**Spot Price (BTCUSDT):** `${spot_px:,.2f}`",
        "",
        "## 1. 15-MINUTE INTRA-CANDLE FOOTPRINT METRICS",
    ]
    if f_ev is not None:
        ref_entry = round(float(f_ev.entry_price or spot_px), 2)
        ref_stop = round(float(f_ev.stop_loss or 0.0), 2)
        stop_dist = round(abs(ref_entry - ref_stop), 2) if ref_stop > 0 else 0.0
        lines.extend([
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
    ts_utc, ts_myt = _timestamps_utc_myt()
    spot_px = _spot_price(store)
    sig = getattr(store, "latest_signal", None)
    mp = getattr(store, "macro_profile", None)
    deriv = getattr(store, "derivatives_snapshot", None)
    flow = getattr(store, "flow_snapshot", None)
    f_ev = getattr(store, "footprint_evaluation", None)

    c_val = round(float(mp.c_val), 2) if mp else 0.0
    c_poc = round(float(mp.c_poc), 2) if mp else 0.0
    c_vah = round(float(mp.c_vah), 2) if mp else 0.0

    conf_score = float(getattr(sig, "confluence_score", 0.0) or 0.0) if sig else 0.0
    loc_score = float(getattr(sig, "location_score", 0.0) or 0.0) if sig else 0.0
    p1_pass = bool(conf_score >= 50.0)
    p2_pass = bool(sig and not getattr(sig, "is_mid_range_chop", False) and loc_score >= 12.0)
    p3_pass = bool(deriv and getattr(deriv, "funding_rate_pct", 0.0) <= 0.01)
    p4_pass = bool(flow and getattr(flow, "w_4h", None) and flow.w_4h.spot_delta_btc > 0)
    p5_pass = bool(f_ev and getattr(f_ev, "all_gates_pass", False))
    true_count = sum(1 for x in (p1_pass, p2_pass, p3_pass, p4_pass, p5_pass) if x)

    lines = [
        "# TAB [W: WATERFALL] | DATA-ONLY METRICS REPORT",
        f"**Retrieval Time (UTC):** `{ts_utc}`  |  **Retrieval Time (MYT):** `{ts_myt}`",
        f"**Spot Price (BTCUSDT):** `${spot_px:,.2f}`",
        "",
        "## 1. 5-PILLAR CONDITION BOOLEANS & RAW INPUTS",
        f"- **Pillar 1 (`Confluence Score >= 50.0`):** `{p1_pass}` (Confluence Score: `{conf_score:.2f}`)",
        f"- **Pillar 2 (`Value Area Edge & Not Mid-Range`):** `{p2_pass}` (`30D cVAL ${c_val:,.2f}` | `30D cPOC ${c_poc:,.2f}` | `30D cVAH ${c_vah:,.2f}` | `VA Position`: `{float(getattr(sig, 'va_position_pct', 0.0) if sig else 0.0):.1f}%` | `Mid-Range`: `{bool(getattr(sig, 'is_mid_range_chop', False)) if sig else False}`)",
        f"- **Pillar 3 (`8H Funding <= 0.0100%`):** `{p3_pass}` (`8H Funding`: `{float(getattr(deriv, 'funding_rate_pct', 0.0) if deriv else 0.0):+.4f}%` | `4H OI Change`: `{float(getattr(deriv, 'oi_change_4h_pct', 0.0) if deriv else 0.0):+.2f}%`)",
        f"- **Pillar 4 (`4H Spot Delta > 0 BTC`):** `{p4_pass}` (`4H Spot Delta`: `{ (flow.w_4h.spot_delta_btc if (flow and getattr(flow, 'w_4h', None)) else 0.0):+.2f} BTC` | `4H Perp Delta`: `{ (flow.w_4h.perp_delta_btc if (flow and getattr(flow, 'w_4h', None)) else 0.0):+.2f} BTC`)",
        f"- **Pillar 5 (`15m Footprint 4-Gate Pass`):** `{p5_pass}` (`15m Active Delta`: `{float(getattr(f_ev, 'active_bar_delta', 0.0) if f_ev else 0.0):+.2f} BTC`)",
        f"- **Total Pillars True:** `{true_count} / 5`",
    ]
    return sanitize_data_only_text("\n".join(lines))


# ==============================================================================
# 9. TAB [0: SPOT SWING] DATA-ONLY REPORT
# ==============================================================================
def build_tab_0_data_only_report(config: Optional[EngineConfig], store: StateStore) -> str:
    ts_utc, ts_myt = _timestamps_utc_myt()
    spot_px = _spot_price(store)
    sw = getattr(store, "spot_swing_evaluation", None)

    lines = [
        "# TAB [0: SPOT SWING] | DATA-ONLY METRICS REPORT",
        f"**Retrieval Time (UTC):** `{ts_utc}`  |  **Retrieval Time (MYT):** `{ts_myt}`",
        f"**Spot Price (BTCUSDT):** `${spot_px:,.2f}`",
        "",
        "## 1. SPOT SWING SCREENER METRICS & GATE BOOLEANS",
    ]
    if sw is not None:
        ref_entry = round(float(getattr(sw, "entry_price", 0.0) or spot_px), 2)
        ref_stop = round(float(getattr(sw, "stop_loss_price", 0.0) or (spot_px * 0.975)), 2)
        stop_dist = round(ref_entry - ref_stop, 2)
        lines.extend([
            f"- **Composite Confluence Score (`0 - 100`):** `{getattr(sw, 'confluence_score', 0.0):.1f}`",
            f"- **Gate 1 (`Macro Filter`):** `{bool(getattr(sw, 'gate1_macro_pass', False))}`",
            f"- **Gate 2 (`Structure / Location`):** `{bool(getattr(sw, 'gate2_location_pass', False))}`",
            f"- **Gate 3 (`Derivatives / Funding`):** `{bool(getattr(sw, 'gate3_derivatives_pass', False))}`",
            f"- **Gate 4 (`Spot Order Flow`):** `{bool(getattr(sw, 'gate4_flow_pass', False))}`",
            f"- **All Screener Gates True:** `{bool(getattr(sw, 'all_gates_pass', False))}`",
            "",
            f"## 2. REFERENCE LEVELS (Reference calculation if entered at ${ref_entry:,.2f}. Not an order.)",
            f"- **Reference Entry Price:** `${ref_entry:,.2f}`",
            f"- **Reference Stop Level:** `${ref_stop:,.2f}`",
            f"- **Stop Distance (`Reference Entry - Stop Level`):** `${stop_dist:,.2f}`",
            f"- **Reference Level 1 (`TP1`):** `${float(getattr(sw, 'tp1_price', 0.0) or 0.0):,.2f}`",
            f"- **Reference Level 2 (`TP2`):** `${float(getattr(sw, 'tp2_price', 0.0) or 0.0):,.2f}`",
            f"- **Reference Level 3 (`3R`):** `${float(getattr(sw, 'tp3_price', 0.0) or 0.0):,.2f}`",
        ])
    else:
        lines.append("- **Spot Swing Screener Evaluation Available:** `False`")

    return sanitize_data_only_text("\n".join(lines))


# ==============================================================================
# 10. TAB [L: MASTER] DATA-ONLY REPORT (9-FLAGSHIP TOP-RIBBON MATRIX)
# ==============================================================================
def build_tab_l_data_only_report(config: Optional[EngineConfig], store: StateStore) -> str:
    ts_utc, ts_myt = _timestamps_utc_myt()
    spot_px = _spot_price(store)
    ms = getattr(store, "master_synthesis_evaluation", None)
    tpb = getattr(store, "trend_pullback_evaluation", None)
    slsp = getattr(store, "slsp_evaluation", None)
    sw = getattr(store, "spot_swing_evaluation", None)

    lines = [
        "# TAB [L: MASTER] | 8-FLAGSHIP DESK DATA-ONLY METRICS REPORT",
        f"**Retrieval Time (UTC):** `{ts_utc}`  |  **Retrieval Time (MYT):** `{ts_myt}`",
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
                f"- **Desk [A] Trend-Pullback v1.0 Reference:** Entry `${tpb.reference_entry_price:,.2f}` | "
                f"Stop `${tpb.structural_stop:,.2f}` (`-${tpb.stop_distance_usd:,.2f}` / `{tpb.stop_distance_atr:.2f} ATR`) | "
                f"Size `{tpb.position_size_btc:.6f} BTC` | Reconciled Risk `${tpb.total_estimated_risk_usd:,.2f}`"
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
# 11. GLOBAL [C: AI PACKET] MASTER DATA-ONLY PACKET
# ==============================================================================
def build_global_data_only_packet(config: Optional[EngineConfig], store: StateStore) -> str:
    """Combines all 10 primary top-ribbon DATA-ONLY reports into a single master packet."""
    cfg = config or DEFAULT_CONFIG
    ts_utc, ts_myt = _timestamps_utc_myt()
    spot_px = _spot_price(store)

    sections = [
        "# BTC SWING ENGINE | GLOBAL DATA-ONLY TELEMETRY PACKET ([C: AI PACKET])",
        f"**Retrieval Time (UTC):** `{ts_utc}`  |  **Retrieval Time (MYT):** `{ts_myt}`",
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


def copy_tab_data_only_report_to_clipboard(
    tab_id: int,
    config: Optional[EngineConfig],
    store: StateStore,
) -> Tuple[bool, str, int]:
    """Builds and copies the DATA-ONLY report for the given primary tab ID."""
    cfg = config or DEFAULT_CONFIG
    dispatch: Dict[int, Tuple[str, str]] = {
        13: (build_tab_p_data_only_report(cfg, store), "btc_structure_latest.md"),
        15: (build_tab_g_data_only_report(cfg, store), "grok_master_prompt_latest.md"),
        16: (build_tab_r_data_only_report(cfg, store), "ssrn_research_brief_latest.md"),
        17: (build_tab_m_data_only_report(cfg, store), "btc_magnet_latest.md"),
        18: (build_tab_a_data_only_report(cfg, store), "btc_trend_pullback_latest.md"),
        19: (build_tab_q_data_only_report(cfg, store), "btc_four_gate_latest.md"),
        11: (build_tab_f_data_only_report(cfg, store), "btc_footprint_latest.md"),
        12: (build_tab_w_data_only_report(cfg, store), "btc_waterfall_latest.md"),
        0: (build_tab_0_data_only_report(cfg, store), "btc_spot_swing_latest.md"),
        10: (build_tab_l_data_only_report(cfg, store), "btc_master_latest.md"),
    }
    if tab_id not in dispatch:
        text = build_global_data_only_packet(cfg, store)
        return copy_text_to_clipboard_and_log(text, "latest_ai_data_packet.md", store, also_write_root_and_downloads=True)

    text, filename = dispatch[tab_id]
    return copy_text_to_clipboard_and_log(text, filename, store)
