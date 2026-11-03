"""Raw Telemetry & Independent AI Audit Packet Exporter (Hotkey `C` across Tab [0] Master & Desks [1]–[9]).

Collects 100% of the live quantitative telemetry across Supreme Master Tab [0] & Specialist Desks [1]–[9]
into a structured, self-contained Markdown packet and copies it directly to the
Windows Clipboard (`Ctrl+V` ready) as well as saving to disk (`Downloads` and `logs/`).
"""

import base64
import os
import pathlib
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

from config.settings import EngineConfig
from core.state_store import StateStore


def _compute_plain_world_clocks_and_session(now_utc: datetime) -> Tuple[str, str]:
    """Computes plain-text UTC, SGP (SGT), LON (GMT/BST), NYC (EST/EDT) clocks and active market session."""
    sgt_dt = now_utc + timedelta(hours=8)
    h = now_utc.hour
    if 0 <= h < 7:
        session_str = "ASIA SESSION (SINGAPORE / HK / TOKYO ACTIVE)"
    elif 7 <= h < 8:
        session_str = "ASIA / LONDON OVERLAP (SGP PM • LONDON OPEN)"
    elif 8 <= h < 13:
        session_str = "LONDON / EU SESSION (EUROPEAN INSTITUTIONAL FLOW)"
    elif 13 <= h < 16:
        session_str = "LONDON / NY OVERLAP (PEAK GLOBAL & US ETF LIQUIDITY)"
    elif 16 <= h < 21:
        session_str = "NEW YORK SESSION (US INSTITUTIONAL & COINBASE ACTIVE)"
    else:
        session_str = "LATE NY / ASIA PRE-OPEN TRANSITION WINDOW"

    clocks_plain = (
        f"UTC {now_utc.strftime('%Y-%m-%d %H:%M:%S')} • "
        f"SGP (Asia) {sgt_dt.strftime('%H:%M:%S')} SGT"
    )
    return clocks_plain, session_str


def build_ai_telemetry_packet(config: EngineConfig, store: StateStore) -> str:
    """Builds a comprehensive, unbiased Raw Data Packet across Supreme Master Tab [0] & Specialist Desks [1]–[9] for external AI analysis."""
    now_utc = datetime.now(timezone.utc)
    ts_str = now_utc.strftime("%Y-%m-%d %H:%M:%S UTC")
    clocks_plain, active_session_str = _compute_plain_world_clocks_and_session(now_utc)

    sig = store.latest_signal
    flow = store.flow_snapshot
    deriv = store.derivatives_snapshot
    macro_vp = store.macro_profile
    tact_vp = store.tactical_profile
    sess_vp = store.session_profile
    pev = store.protocol_evaluation
    mev = store.macro_evaluation
    rmev = store.regime_matrix_evaluation
    msev = store.master_synthesis_evaluation
    mm_ev = store.mm_btc_evaluation

    # Use atomic price from latest evaluation if available so Section 1 and Section 3/6 never drift by 1 tick
    atomic_spot_price = msev.current_price if msev is not None else store.binance_spot_price

    lines = [
        "# BTC-USD LIVE QUANTITATIVE TELEMETRY PACKET & MASTER AI AUDITOR PROMPT",
        f"**Snapshot Timestamp:** `{ts_str}` (`{clocks_plain}`)  ",
        f"**Active Global Market Session:** `{active_session_str}`  ",
        "**Mandate:** Strictly Long-Only Spot BTC Swing & Positional Trading (Zero Leverage, Zero Shorting)  ",
        f"**Reference Portfolio Equity:** `${config.portfolio_equity_usd:,.2f}` (Standard Risk: `{config.risk_per_trade_pct:.2f}%` | Counter-Trend Risk Cap: `{config.counter_trend_risk_pct:.2f}%` | Hard Single-Trade Notional Cap: `<= 50% Equity`)",
        "",
        "## MASTER SYSTEM PROMPT & RULEBOOK FOR GEMINI ARGON / EXTERNAL AI AUDITOR",
        "You are the **Independent Chief Quantitative Strategist & Risk Officer** auditing a live real-time telemetry packet exported from the **`BTC-USD Spot Swing Engine`** (`10-Desk Rich Live Terminal: Tab [0] Master & Desks [1]–[9]`).",
        "",
        "### 1. Rule #0 — Strict Anti-Sycophancy & Chief Engineer Authority",
        "* **Do NOT blindly agree with the Python engine's benchmark verdict in Section 6.** Deterministic code evaluates fixed mathematical thresholds and can miss subtle cross-venue divergences (e.g., negative Coinbase Premium while Binance ticks up, 5-minute perp sell bursts, nearby unflushed long-liquidation magnets within 1%, or over-concentrated single-fill entries).",
        "* You have **full Chief Engineer authority** to confirm, refine, split into multiple limit tranches, or override the Python engine's conclusion based on the raw telemetry across all specialist desks (**Desks [1]–[9]**).",
        "",
        "### 2. How to Interpret & Audit Sections 1–5 & Sections 7–11 (The 9-Desk Quantitative Rulebook)",
        "1. **Section 1 Audit (`Cross-Exchange Spot, Basis & Derivatives`)**:",
        "   * **Coinbase Premium (`CPI`)**: `CPI > +0.02%` (`Z >= +0.5σ`) = US institutional spot buying. `CPI < -0.05%` (Coinbase at a deep discount to Binance) = warning that US spot is lagging or selling into offshore USDT moves.",
        "   * **Open Interest (`Strict BTC Coins`) & `dOI %`**: `AGGRESSIVE_SHORT_BUILD` (`Price Down/Flat + OI Up`) is bullish squeeze fuel *only* if `Spot CVD` is positive (passive spot absorbing shorts). `LEVERAGED_LONG_EXPANSION` (`Price Up + OI Up + High Funding > +0.012%`) is a long-trap warning. `LONG_LIQUIDATION_FLUSH` (`Price Down + OI Down`) clears excess leverage.",
        "   * **5m Taker L/S Ratio & 5m Perp Delta**: If `5m Taker L/S < 0.50` with heavy negative `5m Perp Delta`, sellers are actively pressing the tape right now -> prefer staged limit bids over market orders.",
        "2. **Section 2 Audit (`Composite Volume Profile 30D/7D/24H & Multi-Horizon Spot vs. Perp CVD`)**:",
        "   * **Value Area & Mid-Range Chop Law**: `cVAL` = lower 70% Value Area support; `cPOC` = fair-value magnet (`TP1`); `cVAH` = upper resistance (`TP2`). If `Value Area Position %` is inside `30%–70%` (`Mid-Range Chop Flag: True`), **never chase at market**; wait for `cVAL` or `Support HVN Floor`.",
        "   * **Spot vs. Perp CVD Divergence**: True institutional accumulation requires `Spot CVD > 0` (`4H B/S Ratio > 1.05`) while `Perp CVD < 0` (`Spot-Perp Divergence Z > +1.5σ`, `Passive Absorption Index >= 0.85`).",
        "   * **SweepRetestFSM Gate 4 Law**: Never enter on first touch of `cVAL`. Require rejection, candle reclaim, and an orderly retest inside the `±0.20%` retest band (`PENDING_RETEST -> TRIGGERED`). Hard stop is anchored below the sweep wick with a +0.15% buffer.",
        "   * **3-EMA Industrial Confluence Law**: Daily 200 EMA slope and price location form an absolute gatekeeper (No spot buys if price < falling Daily 200 EMA). In bull regimes (`STRONG_BULL` / `WEAK_BULL`), pullback into the 4H 50-EMA zone with >= 2 of 3 positioning confirmations (stable OI, neutral funding <= +0.010%, positive Spot CVD) validates tactical execution.",
        "3. **Section 3 Audit (`Protocol v1.3, CoinGlass 6-Panel in Strict BTC & Liquidation Magnets`)**:",
        "   * **Candle Hygiene**: Separate `1D Completed [-2]` (closed daily bar) from `1D Forming [-1]` (live unclosed bar).",
        "   * **Supreme Veto Gates**: Any `TRIGGERED` Non-Trade Zone (`8A–8F`) or `CONFIRMED` Spot Sell Trigger (`1–4`) locks new buying (`RED LIGHT`).",
        "   * **Liquidation Magnet Law**: In a range regime, price is magnetized toward dense liquidation pools (`Nearest Short-Liq Magnet Above` vs. `Nearest Long-Liq Magnet Below`). If the `Long-Liq Magnet` sits within `~1%` below current support while OI is `>90,000 BTC`, recommend splitting spot buys into **2 tranches** (Tranche 1 at `cVAL`/`Support HVN`, Tranche 2 resting at the `Long-Liq Magnet` / `1D Support` sweep).",
        "4. **Section 4 Audit (`Macro Quant, Power-Law & Cycle Radar`)**:",
        "   * **Rule 1 Gatekeeper (`1D 200 SMA` + 5D Slope)**: Above a rising `200D SMA` authorizes `1.00%` base risk; below the `200D SMA` caps counter-trend risk at `0.50%` (targeting `21D EMA` / `200D SMA`), unless a `-25%` to `-65%` **Cycle Crash Rung** + **`4H Liquidation Wick Flush` (`>= 45%` lower wick)** triggers a deep-value sniper override.",
        "   * **Genesis Power-Law Valuation**: Strictly `[BIAS ONLY — NOT TIMING]` for long-horizon valuation context.",
        "5. **Section 5 & 6 Audit (`Regime Matrix A–J & Sizing Guardrail`)**:",
        "   * Scale base risk by the dominant `Config A–J` multiplier (`1.0x` Config A/J, `0.75x` Config C/F, `0.0x` Config B/D/E/G/H/I) and enforce a **strict `<= 50%` Portfolio Equity Notional Cap** (`$37,500` max at `0.75x` on `$100k` equity).",
        "6. **Section 7 Audit (`MM-BTC: The Rough Path Arbitrator — Tab [5] Raw Desk`)**:",
        "   * **Rough Path Signatures (Order N <= 2)**: Path Roughness R <= 4.50 ensures persistent drift over Brownian noise. Time-Price Levy Area A_(t,P) <= +0.15 guards against convex sweep pump exhaustion. A_(P,V) > 0 verifies institutional absorption.",
        "   * **Orthogonal Lenses (A–E)**: Latent zero-lag Kalman velocity ($/hr), rolling Hurst exponent H (> 0.55 persistent vs. < 0.45 chop), memory-preserving FracDiff d* momentum, and Ehlers Hilbert phase angle (trough vs. peak).",
        "   * **Arbitration & Tripwire**: 3-Gate verdict and 15m micro tripwire must clear for high-conviction spot entries.",
        "7. **Section 8 Audit (`72-Hour Forward Volatility Cone & AI Benchmark Radar — Tab [6] Raw Desk`)**:",
        "   * **Garman-Klass Volatility & Hurst Expansion**: 1σ and 2σ Mandelbrot cones (t^H) map true expected price dispersion over 72 hours. VCR ratio > 2.0x indicates severe variance compression.",
        "   * **Church vs. State Separation**: Quarantined TSFM AI forecasts (0.0% capital weight) vs. institutional order flow execution.",
        "8. **Section 9 Audit (`Gartley 222 & 5-Strategy Confluence Radar — Tab [7] Raw Desk`)**:",
        "   * **Dual-Horizon Confluence**: 1D Macro Trend regime gate + 4H Tactical Swing triggers with exact TradingView Pine Script parity.",
        "   * **Harmonic Geometry**: Bullish & Bearish Gartley 222 Fibonacci ratios (B/XA 0.618, C/AB 0.382-0.886, D/XA 0.786, AB/CD 0.70-1.50) and PRZ levels.",
        "9. **Section 10 Audit (`Pattern Invalidation, Liquidity Sweep & SFP Trap Radar — Tab [8] Raw Desk`)**:",
        "   * **Liquidity Hunting Mechanics**: Classical pattern boundaries (H&S necklines, double tops/bottoms, range extremes) serve as predictable stop-liquidity targets, not invariant barriers.",
        "   * **Absorption & SFP Confirmation**: Negative Perp CVD absorbed by passive spot bids + 15m/1H candle close back inside boundary = confirmed Bear Trap (Long squeeze setup with R:R >= 1:3).",
        "10. **Section 11 Audit (`Terminal Exhaustion & Delta Divergence Radar — Tab [9] Raw Desk`)**:",
        "   * **Objective Turnpoint Detection**: Tom DeMark TD-9 sequential setups (perfected when bar 8/9 extremes exceed bars 6/7) replace subjective Elliott Wave counting with deterministic math.",
        "   * **CVD Divergence & Climax Stress**: Multi-horizon delta exhaustion (Price HH vs CVD LH) + OI and funding climax identifies institutional distribution and exhaustion tops/bottoms.",
        "",
        "### 3. Mandatory 5-Part Response Format",
        "Structure your audit into:",
        "1. **Independent Cross-Tab Telemetry Audit** (Bullish Confluence vs. Hidden Friction/Risk Flags across Specialist Desks [1]–[9])",
        "2. **Critique of Python Engine Benchmark** (Where you **AGREE** vs. **DISAGREE / REFINE** Section 6)",
        "3. **Independent AI Traffic-Light Verdict & Conviction %** (`GREEN`, `BLUE`, `YELLOW`, or `RED`)",
        "4. **Reconciled Master Order of Battle** (**Track A: If Flat in Cash** with exact Tranche 1/2 `$` zones, `BTC`/`$` sizes, Hard Stop, `TP1`/`TP2` vs. **Track B: If Already Holding Spot BTC**)",
        "5. **Plain-English Executive Bottom Line** (`What's Happening`, `Why`, `Your Exact Next Move`)",
        "",
        "---",
        "",
        "## SECTION 1: CROSS-EXCHANGE SPOT, BASIS & DERIVATIVES TELEMETRY (TAB [1] & TAB [4] RAW INPUTS)",
        "",
        "| Metric | Live Value | Context / Benchmark |",
        "| :--- | :--- | :--- |",
        f"| **Binance Spot Price (`BTCUSDT`)** | `${atomic_spot_price:,.2f}` | Primary Spot Reference |",
        f"| **Coinbase Spot Price (`BTC-USD`)** | `${store.coinbase_spot_price:,.2f}` | US Institutional Spot Reference |",
        f"| **Perp Price ({store.perp_source})** | `{f'${store.binance_perp_price:,.2f}' if store.binance_perp_price > 0 else 'Data unavailable'}` | Perpetual Futures Reference (`{store.perp_source}`) |",
        f"| **Coinbase Premium Index (CPI)** | `${deriv.coinbase_premium_usd:+,.2f}` (`{deriv.coinbase_premium_pct:+.4f}%`) | Rolling Z-Score: `{deriv.coinbase_premium_zscore:+.2f}σ` |",
        f"| **Open Interest (Strict BTC Coins)** | `{deriv.open_interest_btc:,.2f} BTC` | Notional: `${deriv.open_interest_usd:,.0f}` |",
        f"| **Open Interest Delta (`15m / 1H / 4H / 24H`)** | `15m: {deriv.oi_change_15m_pct:+.2f}%` • `1H: {deriv.oi_change_1h_pct:+.2f}%` • `4H: {deriv.oi_change_4h_pct:+.2f}%` | `24H dOI: {(rmev.oi_change_24h_pct if rmev else 0.0):+.2f}%` |",
        f"| **OI Positioning Quadrant** | `{deriv.oi_regime_quadrant.value}` | Price vs. OI Classification |",
        f"| **8H Perpetual Funding Rate** | `{deriv.funding_rate_pct:+.4f}%` | Neutral Cap: `{config.funding_neutral_max_pct:+.4f}%` • Veto: `{config.funding_crowded_veto_pct:+.4f}%` |",
        f"| **Annualized Perp Basis** | `{(rmev.annualized_basis_pct if rmev else 0.0):+.2f}% / yr` | Perp vs. Spot Annualized Carry |",
        f"| **5m Taker Long/Short Ratio** | `{deriv.taker_long_short_ratio_5m:.3f}` | `5m Perp Delta: {deriv.perp_5m_delta_btc:+,.2f} BTC` |",
    ]

    if rmev is not None:
        lines.extend([
            f"| **Daily VWAP (24H) / Weekly VWAP (7D)** | `Daily: ${rmev.daily_vwap:,.2f}` | `Weekly: ${rmev.weekly_vwap:,.2f}` |",
            f"| **1D 20 EMA / 1D 50 EMA** | `20D EMA: ${rmev.ema_20_1d:,.2f}` | `50D EMA: ${rmev.ema_50_1d:,.2f}` |",
            f"| **24H Spot Volume vs. 20D MA** | `{rmev.spot_vol_vs_20d_ma:.2f}x` | Breakout Expansion Threshold: `>= 1.35x` |",
            f"| **4H Spot Buy/Sell Ratio & 7D Spot CVD** | `4H B/S Ratio: {rmev.spot_buy_sell_ratio_4h:.2f}` | `7D Spot CVD: {rmev.spot_cvd_7d_btc:+,.1f} BTC` |",
            f"| **ATR Compression & 72H Base Width** | `ATR Comp: {rmev.atr_compression_pct:.1f}%` | `72H Range Width: {rmev.base_width_72h_pct:.2f}%` |",
        ])

    lines.extend([
        "",
        "---",
        "",
        "## SECTION 2: COMPOSITE VOLUME PROFILE & MULTI-HORIZON ORDER FLOW (TAB [1] RAW METRICS)",
        "",
        "### 2A. Gaussian-Smoothed Composite Volume Profiles (120 Bins, 70% Value Area)",
        "",
        "| Profile Horizon | Range High | cVAH (Upper VA) | cPOC (Fair Value) | cVAL (Lower VA) | Primary LVN (<cVAL) | Support HVN Floor |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
    ])

    for vp in (macro_vp, tact_vp, sess_vp):
        if vp is not None:
            lvn_s = f"${vp.primary_lvn_below_val:,.0f}" if vp.primary_lvn_below_val else "None"
            hvn_s = f"${vp.support_hvn_below_val:,.0f}" if vp.support_hvn_below_val else "None"
            lines.append(
                f"| **`{vp.horizon_label}`** | `${vp.range_high:,.0f}` (Low `${vp.range_low:,.0f}`) | `${vp.c_vah:,.0f}` | **`${vp.c_poc:,.0f}`** | **`${vp.c_val:,.0f}`** | `{lvn_s}` | `{hvn_s}` |"
            )

    if sig is not None:
        fsm_text = (
            f"• **SweepRetestFSM (Tab 1 Gate 4)**: `{sig.fsm_state}` (`{sig.fsm_status_summary}`) | "
            f"**Bars Elapsed**: `{sig.fsm_bars_elapsed}/{sig.fsm_max_bars}` | "
            f"**Retest Band**: `${sig.fsm_retest_band_low:,.0f} – ${sig.fsm_retest_band_high:,.0f}` | "
            f"**Hard Invalidation Stop**: `${sig.fsm_suggested_stop:,.0f}`"
            if sig.fsm_state
            else "• **SweepRetestFSM (Tab 1 Gate 4)**: `IDLE (Monitoring cVAL)`"
        )
        lines.extend([
            "",
            f"* **Active Structural Profile**: `{sig.active_horizon}` | **Distance to cVAL**: `{sig.distance_to_val_pct:+.2f}%` (`{sig.distance_to_val_atr:+.2f} ATR`) | **Value Area Position (`0%=cVAL, 100%=cVAH`)**: `{sig.va_position_pct:+.1f}%` (`Mid-Range Chop Flag: {sig.is_mid_range_chop}`) | **1H ATR**: `${sig.atr_1h:,.0f}` | **4H ATR**: `${sig.atr_4h:,.0f}` | **Recent Reclaim Candle**: `{sig.is_reclaim_candle}`",
            f"* {fsm_text}",
        ])
        if sig.ema_strategy is not None:
            es = sig.ema_strategy
            lines.append(
                f"* • **3-EMA Industrial Trend System (Macro Multi-Week Horizon)**: Macro Trend Regime:`{es.daily_regime}` "
                f"(200 EMA `${es.daily_ema_200:,.0f}`, Slope `{es.daily_ema_200_slope:+,.1f}$/day`, ADX `{es.daily_adx:.1f}`) | "
                f"4H 50-EMA: `${es.ema_4h_50:,.0f}` (Pullback Zone: `{es.pullback_zone_active}`) | "
                f"Positioning Confluence: `{es.positioning_confirmations_met}/3` | "
                f"Setup Status: `{es.setup_status}` | Suggested ATR Stop: `${es.suggested_atr_stop:,.0f}` (`{es.suggested_risk_pct:.2f}%` Risk)"
            )

    lines.extend([
        "",
        "### 2B. Multi-Horizon Order Flow, Spot vs. Perp CVD & Passive Absorption",
        "",
        "| Horizon | Price Δ% | Spot CVD Delta (BTC) | Spot Z-Score | Perp CVD Delta (BTC) | Perp Z-Score | Spot-Perp Div Z | Passive Absorption Index |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
    ])

    for w in (flow.w_15m, flow.w_1h, flow.w_4h, flow.w_24h):
        lines.append(
            f"| **`{w.window_label}`** | `{w.price_change_pct:+.2f}%` | `{w.spot_delta_btc:+,.2f} BTC` (`{w.spot_delta_ratio*100:+.1f}%`) | `{w.spot_zscore:+.2f}σ` | {(f'`{w.perp_delta_btc:+,.2f} BTC` (`{w.perp_delta_ratio*100:+.1f}%`) | `{w.perp_zscore:+.2f}σ` | `{w.flow_divergence_z:+.2f}σ`' if w.perp_volume_btc > 0 else '`Data unavailable` | `Data unavailable` | `Data unavailable`')} | `{w.absorption_index:.2f}` |"
        )
    _excl = getattr(store, "perp_estimated_bars_excluded", {}) or {}
    if any(_excl.values()):
        lines.append("")
        lines.append(
            f"> Perp CVD source `{store.perp_source}`: measured taker bars only. Candle-body-estimated bars EXCLUDED "
            f"from CVD, regime matching, scoring and divergences: "
            + ", ".join(f"{k}: {v}" for k, v in sorted(_excl.items()))
            + ". Windows without enough measured bars show `Data unavailable`."
        )
    lines.append(
        f"| **`UTC Day (00:00)`** | `N/A` | `{flow.utc_day_spot_cvd:+,.2f} BTC` | `N/A` | `{flow.utc_day_perp_cvd:+,.2f} BTC` | `N/A` | `N/A` | `N/A` |"
    )
    if flow.session_spot_cvd != 0 or flow.session_perp_cvd != 0:
        lines.append(
            f"| **`Live WS Session`** | `N/A` | `{flow.session_spot_cvd:+,.2f} BTC` | `N/A` | `{flow.session_perp_cvd:+,.2f} BTC` | `N/A` | `N/A` | `Bull Div: {flow.bullish_pivot_divergence} / Abs Div: {flow.absorption_divergence}` |"
        )

    if pev is not None:
        lines.extend([
            "",
            "---",
            "",
            "## SECTION 3: PROTOCOL v1.3, COINGLASS 6-PANEL (BTC) & LIQUIDATION MAGNETS (TAB [2] RAW METRICS)",
            "",
            "### 3A. Daily Completed `[-2]` vs. Forming `[-1]` & ATR 14 Reference Bounds",
            f"* **1D Completed Candle `[-2]` (Closed)**: Open `${pev.completed_1d_open:,.2f}` • High `${pev.completed_1d_high:,.2f}` • Low `${pev.completed_1d_low:,.2f}` • Close `${pev.completed_1d_close:,.2f}` (`{pev.completed_1d_change_pct:+.2f}%`)",
            f"* **1D Forming Candle `[-1]` (Live)**: Open `${pev.forming_1d_open:,.2f}` • High `${pev.forming_1d_high:,.2f}` • Low `${pev.forming_1d_low:,.2f}` • Close `${pev.forming_1d_close:,.2f}` (`{pev.forming_1d_change_pct:+.2f}%`)",
            f"* **1D Support / Resistance**: Support `${pev.daily_support:,.0f}` • Resistance `${pev.daily_resistance:,.0f}` • **Daily Candlestick Bias (Single 1D Bar)**: `{pev.daily_bias}` (Completed 1D Close < Open) • **4H Structure**: `{pev.structure_4h}` (`4H Ready: {pev.timing_4h_ready}`)",
            f"* **ATR 14 Volatility Bounds**: `1D ATR 14 = ${pev.atr_14_1d:,.0f}` (`-1xATR: ${pev.downside_ref_1d_atr:,.0f}` / `+1xATR: ${pev.upside_ref_1d_atr:,.0f}`) | `4H ATR 14 = ${pev.atr_14_4h:,.0f}` (`-1xATR: ${pev.downside_ref_4h_atr:,.0f}` / `+1xATR: ${pev.upside_ref_4h_atr:,.0f}`)",
            f"* **Daily Liquidation Magnet & Range Pivot Protocol**: `1D 50 SMA = ${pev.sma_50_1d:,.0f}` • `30D Range Pivot = ${pev.range_pivot_usd:,.0f}` • **Nearest Short-Liq Magnet Above**: `${pev.short_liq_magnet_usd:,.0f}` (`{pev.short_liq_source}`) • **Nearest Long-Liq Magnet Below**: `${pev.long_liq_magnet_usd:,.0f}` (`{pev.long_liq_source}`) • **Headline Filter**: `{pev.headline_filter_status}` • **5-Factor Magnet Confluence**: `{pev.magnet_confluence_aligned}/5`",
            "",
            "### 3B. CoinGlass 6-Panel Audit in Strict `BTC` Coins (`1D` vs. `4H`)",
            "",
            "| Panel # & Metric | 1D Horizon | 4H Horizon | Direction / Audit |",
            "| :--- | :--- | :--- | :--- |",
        ])
        for r in pev.coinglass_rows:
            lines.append(
                f"| **`{r.metric_name}`** | `{r.value_1d}` | `{r.value_4h}` | `{r.direction_status}` |"
            )

        lines.extend([
            "",
            "### 3C. Section 8 Non-Trade Zones (`8A–8F`) & Section 11 Spot Sell Triggers (`1–4`)",
            "",
            "| Rule Code / Trigger | Status | Live Detail |",
            "| :--- | :--- | :--- |",
        ])
        for z in pev.non_trade_zones:
            lines.append(f"| **`NTZ {z.code}: {z.rule_name}`** | `{z.status}` | {z.detail} |")
        for s in pev.sell_triggers:
            lines.append(f"| **`Sell Trigger {s.name}`** | `{s.status}` | {s.detail} |")

    if mev is not None:
        lines.extend([
            "",
            "---",
            "",
            "## SECTION 4: MACRO QUANT, POWER-LAW & CYCLE RADAR (TAB [3] RAW METRICS)",
            "",
            f"* **Rule 1 Gatekeeper (`1D 200 SMA` + 5D Slope)**: `1D 200 SMA = ${mev.sma_200_1d:,.2f}` | `5D Slope = {mev.sma_200_slope_5d_usd:+,.2f} $/day` (`{mev.sma_200_slope_5d_pct:+.3f}%`) | `Above 200D SMA: {mev.above_200d_sma}` | `Gatekeeper Veto Active: {mev.gatekeeper_veto}` (`{mev.gatekeeper_status_text}`)",
            f"* **1D 21 EMA (Bull Market Support Band)**: `${mev.ema_21_1d:,.2f}` (`Distance: {mev.dist_to_21d_ema_pct:+.2f}%`)",
            f"* **14D Wilder RSI (Daily)**: `{mev.rsi_14_1d:.2f}` (`{mev.rsi_zone}`)",
            f"* **30D Composite POC**: `${mev.poc_30d:,.2f}` (`Distance: {mev.dist_to_30d_poc_pct:+.2f}%`)",
            f"* **Genesis Power-Law Valuation (`[BIAS ONLY — NOT TIMING]`)**: Fair Value `${mev.power_law_fair_usd:,.0f}` | Live Discount/Premium: `{mev.power_law_discount_pct:+.2f}%` (`{mev.power_law_zone_label}`)",
            f"* **Cycle High (ATH) & Drawdown**: Cycle High `${mev.cycle_high_usd:,.0f}` | Current Drawdown: `{mev.current_drawdown_pct:+.2f}%` | Active Crash Rung: `{mev.active_crash_rung}` (`Override Active: {mev.crash_rung_override_active}`)",
            f"* **4H Liquidation Wick Flush Detector**: `Detected = {mev.wick_flush_4h_detected}` (`Max Lower Wick Ratio = {mev.wick_flush_4h_ratio:.1f}%` — `{mev.wick_flush_detail}`)",
            "",
            "### 4A. Cycle Drawdown Accumulation Rungs (`-25%` to `-65%`)",
            "",
            "| Rung | Target Price | Distance from Current | Tranche | Status |",
            "| :--- | :--- | :--- | :--- | :--- |",
        ])
        for rung in mev.crash_rungs:
            lines.append(
                f"| **`{rung.rung_label}`** | `${rung.target_price:,.0f}` | `{rung.distance_pct:+.1f}%` | `{rung.allocation_tranche}` | `{rung.status}` |"
            )

        lines.extend([
            "",
            "### 4B. Multi-Timeframe `1W / 1D / 4H` Liquidity Sniper Matrix",
            "",
            "| Timeframe | Structure | Close vs. Open % | Candle / Wick Signature | Flow & Momentum |",
            "| :--- | :--- | :--- | :--- | :--- |",
        ])
        for row in mev.tf_rows:
            lines.append(
                f"| **`{row.timeframe}`** | `{row.structure}` | `{row.close_vs_open_pct:+.2f}%` | `{row.candle_signature}` | `{row.flow_momentum}` |"
            )

    if rmev is not None:
        lines.extend([
            "",
            "---",
            "",
            "## SECTION 5: QUANTITATIVE MICROSTRUCTURE MATRIX A–J SCORES (TAB [4] RAW SCORES)",
            "",
            "| Config | Regime Title | Match % | Live Observed Telemetry | Protocol Mandate & Stop |",
            "| :--- | :--- | :--- | :--- | :--- |",
        ])
        for cfg in rmev.configs:
            act_mark = "★ ACTIVE" if cfg.is_active else ""
            lines.append(
                f"| **`{cfg.code}` {act_mark}** | {cfg.short_title} ({cfg.diagnosis_subtitle}) | **`{cfg.match_pct:.0f}%`** | `{cfg.key_live_facts}` | `{cfg.action_headline}` • `{cfg.sizing_rule}` • `{cfg.stop_rule}` |"
            )

    if msev is not None and sig is not None:
        tp = sig.trade_plan
        lines.extend([
            "",
            "---",
            "",
            "## SECTION 6: PYTHON ENGINE BENCHMARK VERDICT (TAB [0] SUPREME COMMAND CENTER 9-DESK MIRROR)",
            "",
            "### 6A. Panel 1 — 9-Desk Executive Verdict Rollup Matrix (Specialist Desks `[1]–[9]`)",
            "",
            "| Tab | Light | Score / State | Primary Driver | Executive Conclusion |",
            "| :--- | :--- | :--- | :--- | :--- |",
        ])
        for row in msev.tab_rows:
            lines.append(
                f"| **`{row.tab_name}`** | `{row.traffic_light}` | `{row.score_or_status}` | `{row.primary_driver}` | `{row.tab_conclusion}` |"
            )

        fsm_gate_info = f" • FSM: `{sig.fsm_state or 'IDLE'}` ({sig.fsm_status_summary})" if sig.fsm_state else ""
        lines.extend([
            "",
            f"* **9-Desk Scoreboard**: `{msev.tabs_green_count} GREEN • {msev.tabs_blue_count} BLUE • {msev.tabs_yellow_count} YELLOW • {msev.tabs_red_count} RED` | **Master Alignment Score**: `{msev.master_alignment_score:.1f}%` (`{msev.alignment_status}`)",
            f"* **Tab [1] 4-Gate Confluence Breakdown**: `{sig.confluence_score:.1f}/100` (`Location: {sig.location_score:.1f}/25` • `Flow: {sig.flow_score:.1f}/35` • `Derivatives: {sig.derivatives_score:.1f}/20` • `Trigger: {sig.trigger_score:.1f}/20`{fsm_gate_info})",
            "",
            "### 6B. Panel 2 — 4-Layer Institutional Decision Funnel & Conflict Resolver",
            "",
            "| Hierarchy Layer | Gate Status | Live Hierarchical Ruling |",
            "| :--- | :--- | :--- |",
        ])
        for h_row in msev.hierarchy_rows:
            lines.append(
                f"| **`{h_row.layer_name}`** | `{h_row.status}` | `{h_row.live_ruling}` |"
            )

        lines.extend([
            "",
            "### 6C. Panel 3 — Cross-Tab Agreement, Conflict Diagnostic & Flip Catalysts",
            "* **Cross-Tab Confluence (Where Specialist Desks Agree)**:",
        ])
        for pt in msev.confluence_points:
            lines.append(f"  - `{pt}`")
        lines.append("* **Cross-Tab Conflict Diagnostic & Hierarchical Resolution**:")
        for cpt in msev.conflict_points:
            lines.append(f"  - `{cpt}`")
        lines.append("* **Catalysts That Flip the Master Conclusion (Upgrade / Downgrade)**:")
        for ucat in msev.upgrade_catalysts:
            lines.append(f"  - `{ucat}`")

        lines.extend([
            "",
            "### 6D. Panel 4 — Unified Master Order of Battle (Track A: In Cash vs. Track B: Holding Spot BTC)",
            f"* **TRACK A (IF FLAT IN CASH)**: `{msev.cash_permission}`",
            f"  - **Reconciled Bid Zone**: `{msev.cash_entry_zone_str}`",
            f"  - **Reconciled Size Math**: `{msev.cash_base_risk_pct:.2f}% [T3] × {msev.cash_regime_multiplier:.2f}x [T4] -> {msev.cash_edge_size_btc:.4f} BTC (${msev.cash_edge_notional_usd:,.0f} at {msev.cash_edge_risk_pct:.2f}% risk)`",
            f"  - **Execution Rule**: `{msev.cash_trigger_instruction}`",
            f"* **TRACK B (IF HOLDING SPOT BTC — MACRO HORIZON)**: `{msev.holder_action}`",
            f"  - **Reconciled Hard Stop (Macro Floor)**: `${msev.holder_hard_stop_usd:,.0f}` (`${msev.holder_hard_stop_usd:,.2f}` exact | `{msev.holder_hard_stop_source}`)",
            f"  - **Profit Targets (1/2)**: `TP1 (40%): ${msev.holder_tp1_usd:,.0f} ({msev.holder_tp1_source}) • TP2 (60%): ${msev.holder_tp2_usd:,.0f} ({msev.holder_tp2_source})`",
            f"  - **Management Rule**: `{msev.holder_management_note}`",
            f"* **Tab [1] Tactical TradePlan (Intraday/Swing)**: Entry `${tp.entry_zone_low:,.0f}–${tp.entry_zone_high:,.0f}` | Tactical Stop `${tp.stop_loss:,.0f}` (ATR/Swing Low) | `Tactical TP1 ${tp.tp1_poc:,.0f} ({'7D cPOC' if tp.tp1_poc < sig.c_poc else '30D cPOC'})` | `Tactical TP2 ${tp.tp2_vah:,.0f} (30D cVAH Extreme)`" if tp else "",
            "",
            "### 6E. Panel 5 — Executive Bottom Line (Supreme Master Conclusion)",
            f"* **Master Traffic Light & Headline**: `{msev.master_traffic_light}` — `{msev.master_headline}`",
            f"* **Master Synthesis**: `{msev.master_what_is_happening}`",
            f"* **Conflict Ruling**: `{msev.master_why_resolution}`",
            f"* **Final Command**: `{msev.master_final_command}`",
        ])

    if mm_ev is not None:
        lines.extend([
            "",
            "---",
            "",
            "## SECTION 7: MM-BTC — THE ROUGH PATH ARBITRATOR (TAB [5] RAW RADAR)",
            "",
            f"* **Chief Arbiter Recommendation**: `{mm_ev.action_plan_cash}` (Weight: `{mm_ev.final_weight:.2f}x` • Consensus: `{mm_ev.agreeing_models_count}/5 Models Agree` • Microstructure: `{mm_ev.microstructure_pattern}` / `{mm_ev.microstructure_bias}`)",
            f"* **Walk-Forward Ridge Expected Return (Y_hat)**: `{mm_ev.gate3_y_hat:+.2f}%` | **Sizing Mode**: `{mm_ev.gate3_sizing_mode}` | **15m Micro Tripwire**: `{'VETO ACTIVE' if mm_ev.micro_tripwire_veto else 'CLEAR'}`",
            f"* **Execution Bounds**: Zone `{mm_ev.execution_zone_str}` • Invalidation `{mm_ev.invalidation_str}` • Target `{mm_ev.target_zone_str}`",
            "",
            "### 7A. Rough Path Signatures (Order N <= 2, Quadratic Variation Roughness & Levy Signed Areas)",
            "",
            "| Signature Term | Value | Operational Threshold / Boundary | Quantitative Interpretation |",
            "| :--- | :--- | :--- | :--- |",
            f"| **Price Net Drift S^(P)** | `{mm_ev.signature.drift_L1:+.4f}` | Level 1 Coordinate Drift | Net price coordinate displacement over rolling 48H |",
            f"| **Volume Net Drift S^(V)** | `{mm_ev.signature.drift_flow:+.4f}` | Level 1 Flow Drift | Net volume coordinate displacement over rolling 48H |",
            f"| **Open Interest Drift S^(O)** | `{mm_ev.signature.drift_oi:+.4f}` | Level 1 Leverage Drift | Net open interest displacement over rolling 48H |",
            f"| **Quadratic Path Roughness (R)** | `{mm_ev.signature.roughness:.2f}` | Max Cap: `<= 4.50` (`Pass={mm_ev.signature.roughness <= 4.50}`) | {'Smooth/Persistent Trend' if mm_ev.signature.roughness <= 4.50 else 'Brownian Chop/Excess Noise'} |",
            f"| **Time-Price Levy Area A_(t,P)** | `{mm_ev.signature.area_time_price:+.4f}` | Exhaustion Cap: `<= +0.15` | `{mm_ev.signature.time_price_classification}` |",
            f"| **Price-Flow Levy Area A_(P,V)** | `{mm_ev.signature.area_price_flow:+.4f}` | Area Enclosed by Price vs. CVD | `{mm_ev.signature.flow_lead_lag_classification}` |",
            f"| **Price-OI Levy Area A_(P,O)** | `{mm_ev.signature.area_price_oi:+.4f}` | Area Enclosed by Price vs. OI | `{mm_ev.signature.oi_lead_lag_classification}` |",
            f"| **Arbiter Status & Verdict** | `{mm_ev.signature.arbiter_gate_status}` | Gate Status | `{mm_ev.signature.signature_verdict}` |",
            "",
            "### 7B. Orthogonal Mathematical Lenses (A–E)",
            "",
            "| Lens | Model Name | Primary Metric | Secondary Metric | Diagnostic State |",
            "| :--- | :--- | :--- | :--- | :--- |",
            f"| **Lens A** | Constant-Velocity Kalman Filter | Latent Price: `${mm_ev.kalman.filtered_price:,.2f}` (`{mm_ev.kalman.distance_pct:+.2f}%`) | Velocity: `{mm_ev.kalman.velocity:+,.2f} $/hr` | State: `{mm_ev.kalman.velocity_state}` • Bias: `{mm_ev.kalman.bias}` |",
            f"| **Lens B** | Rolling 128-Bar Hurst Exponent | Hurst Exponent H: `{mm_ev.hurst.hurst:.3f}` | Regime: `{mm_ev.hurst.regime}` | Implication: `{mm_ev.hurst.tactical_implication}` |",
            f"| **Lens C** | Fixed-Width Window FracDiff | Optimal Order d*: `{mm_ev.frac_diff.optimal_d:.2f}` | ADF p-value: `{mm_ev.frac_diff.adf_p_value:.4f}` (t={mm_ev.frac_diff.adf_stat:.2f}) | 12-Bar Momentum: `{mm_ev.frac_diff.momentum:+.4f}` • Memory: `{mm_ev.frac_diff.memory_state}` • Bias: `{mm_ev.frac_diff.bias}` |",
            f"| **Lens D** | Hilbert Transform Analytic Signal | Cycle Period: `{mm_ev.hilbert.dominant_cycle:.1f}h` | Phase Angle: `{mm_ev.hilbert.phase:.1f}°` | Phase State: `{mm_ev.hilbert.phase_state}` • Bias: `{mm_ev.hilbert.bias}` (Cleaned {mm_ev.hilbert.outliers_cleaned} outliers) |",
            f"| **Lens E** | 48H Order Flow & OI Dynamics | 48H Net CVD: `{mm_ev.cvd_48h:+,.1f} BTC` | 48H OI Delta: `{mm_ev.oi_delta_pct:+.2f}%` | 1H 200 SMA: `${mm_ev.sma_200_1h:,.0f}` (Above: `{mm_ev.above_200_1h}`) |",
            "",
            "### 7C. 3-Gate Institutional Arbitration & Micro Tripwire",
            "",
            "| Gate # | Gate Name | Status | Quantitative Detail |",
            "| :--- | :--- | :--- | :--- |",
            f"| **Gate 1** | Structural Invariance Gate | `{'PASS' if mm_ev.gate1_pass else 'FAIL'}` | Roughness R={mm_ev.signature.roughness:.2f} (<=4.50), Area(t,P)={mm_ev.signature.area_time_price:+.3f} (<=+0.15) |",
            f"| **Gate 2** | Dynamic Invariance Gate | `{'PASS' if mm_ev.gate2_pass else 'FAIL'}` | Agreeing Models: {mm_ev.agreeing_models_count}/5 (Hurst, Kalman, FracDiff, Hilbert, Flow) |",
            f"| **Gate 3** | Walk-Forward Ridge & Sizing | `Y_hat = {mm_ev.gate3_y_hat:+.2f}%` | Mode: {mm_ev.gate3_sizing_mode} • Weight: {mm_ev.final_weight:.2f}x |",
            f"| **Tripwire** | 15m Micro Order Flow Tripwire | `{'TRIPPED (VETO)' if mm_ev.micro_tripwire_veto else 'CLEAR'}` | Real-time 15m volume & CVD delta check |",
            f"| **Conflict** | Consensus Conflict Summary | Conflict: `{mm_ev.conflict_summary}` | Action Holder: `{mm_ev.action_plan_holder}` |",
        ])

    vc = store.volatility_cone_evaluation
    if vc is not None:
        lines.extend([
            "",
            "---",
            "",
            "## SECTION 8: 72-HOUR FORWARD VOLATILITY CONE & AI BENCHMARK RADAR (TAB [6])",
            "",
            "> [!NOTE]",
            "> **BENCHMARK & VOLATILITY RADAR ONLY — 0.0% CAPITAL ALLOCATION WEIGHT (QUARANTINED)**  ",
            "> Zero-shot Time-Series Foundation Models (Kronos, Chronos-Bolt, TimesFM) serve strictly as public SaaS benchmarks. Alpha Core (Supreme Master Tab [0] & Specialist Desks [1]–[9]) remains the sole capital allocator.",
            "",
            f"* **Hurst Fractal Exponent (H)**: `{vc.hurst_exponent:.3f}` (`{vc.hurst_regime}` • Mandelbrot Diffusion `t^{vc.hurst_exponent:.2f}`)",
            f"* **Garman-Klass Volatility (4H)**: `{vc.garman_klass_vol_4h * 100.0:.2f}%` | **Annualized Volatility**: `{vc.garman_klass_annualized_vol * 100.0:.1f}%` (8x statistical efficiency over close-to-close standard deviation)",
            f"* **Variance Compression Ratio (VCR_72h)**: `{vc.vcr_72h:.2f}x` (`{vc.vcr_status}` • Coiled Spring Alert: `{'ACTIVE' if vc.coiled_spring_alert else 'NORMAL'}`)",
            f"* **Damped Kalman Drift Center (mu)**: `{vc.kalman_mu_drift:+.5f}` per 4H bar (`lambda={vc.kalman_lambda_decay}` exponential decay)",
            f"* **Forward Liquidity Confluence**: {vc.liquidity_confluence_summary}",
            f"* **Quantitative Takeaway**: {vc.quantitative_takeaway}",
            "",
            "### 8A. 72-Hour Forward Volatility Cone Fan Table (Mandelbrot t^H Quantile Fan vs TSFM Mean)",
            "",
            "| Horizon | Damped Drift Center | GK 1σ Band (68% Conf) | GK 1σ Spread ($ / %) | GK 2σ Band (95% Conf) | TSFM Mean Close | TSFM Disp % |",
            "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
        ])
        for row in vc.horizons:
            lines.append(
                f"| **`{row.horizon_label}`** | `${row.drift_center:,.0f}` | `${row.gk_1sigma_lower:,.0f} – ${row.gk_1sigma_upper:,.0f}` | `±${row.gk_1sigma_spread_usd / 2.0:,.0f}` (`{row.gk_1sigma_spread_pct / 2.0:+.2f}%`) | `${row.gk_2sigma_lower:,.0f} – ${row.gk_2sigma_upper:,.0f}` | `${row.tsfm_mean_close:,.0f}` | `{row.tsfm_dispersion_pct:.2f}%` |"
            )

        lines.extend([
            "",
            "### 8B. Quarantined Time-Series Foundation Models (TSFM Baseline Audit)",
            "",
            "| Model Name | Architecture & Training Domain | Direction & 72h Close | Predicted 72h Range | 72h Range Spread ($ / %) | Operational Quarantine Status |",
            "| :--- | :--- | :--- | :--- | :--- | :--- |",
        ])
        for item in vc.tsfm_benchmarks:
            lines.append(
                f"| **`{item.name}`** | {item.architecture_tag} ({item.training_domain}) | `{item.direction_str}` (`${item.predicted_close_72h:,.0f}`) | `${item.predicted_range_min:,.0f} – ${item.predicted_range_max:,.0f}` | `${item.range_dollar_spread:,.0f}` (`{item.range_pct:.2f}%`) | `{item.quarantine_status}` |"
            )

        lines.extend([
            "",
            "### 8C. Quantitative Variance Compression Analysis & Educational Value",
            "",
            f"* **The Martingale Variance Compression Trap**: Zero-shot TSFMs minimizing MSE on raw price series collapse to persistent random walks (P_t ≈ P_{{t-1}}), producing an artificially flat range of only ~0.2% to 0.4% over 72 hours.",
            f"* **VCR Metric**: `VCR_72h = {vc.vcr_72h:.2f}x` reveals that realized volatility expansion requires a `{vc.vcr_72h:.1f}x` wider envelope than naive AI estimates.",
            f"* **Actionable Execution Rule**: Never trade naive zero-shot predictions. Rely strictly on order-flow absorption, liquidation magnets, and rough path invariance (Supreme Master Tab [0] & Specialist Desks [1]–[9]).",
            "",
            "### 8D. Plain English Summary for Traders & Beginners (What This Means in Reality)",
            "",
            "> [!TIP]",
            "> **PLAIN ENGLISH TRANSLATION FOR TRADERS:**",
            f"> 1. **Why the AI lines look flat (±0.2%)**: Generic AI models play it safe by guessing tomorrow's price will equal today's price ($P_t ≈ P_{{t-1}}$), because they can't predict unexpected news or liquidations.",
            f"> 2. **Where price will actually move**: Real Bitcoin does not stay flat. Over the next 72 hours, true volatility indicates BTC is expected to swing inside the **Green Volatility Cone** (`${vc.horizons[-1].gk_1sigma_lower:,.0f} – ${vc.horizons[-1].gk_1sigma_upper:,.0f}`, `±${vc.horizons[-1].gk_1sigma_spread_usd/2.0:,.0f}` / `±{vc.horizons[-1].gk_1sigma_spread_pct/2.0:.1f}%`).",
            f"> 3. **The Coiled Spring (VCR = {vc.vcr_72h:.2f}x)**: The market is holding **{vc.vcr_72h:.1f}x more expansion energy** than naive AI models realize. {'⚡ **ALERT: Severe compression — a violent breakout is imminent!**' if vc.coiled_spring_alert else 'A sharp breakout is far more likely than a quiet sideways crawl.'}",
            "> 4. **Rule for your wallet**: **NEVER trade based on flat AI predictions.** Your money stays safe. Real trades are only triggered when institutional volume and order flow confirm on **Supreme Master Tab [0] & Specialist Desks [1]–[9]**.",
        ])

    gartley = store.gartley_evaluation
    if gartley is not None:
        r1d = gartley.res_1d
        r4h = gartley.res_4h
        lines.extend([
            "",
            "---",
            "",
            "## SECTION 9: TAB [7] GARTLEY 222 & 5-STRATEGY CONFLUENCE RADAR",
            "",
            "> [!NOTE]",
            "> **WELCOME TO TAB [7]: GARTLEY 222 & 5-STRATEGY CONFLUENCE RADAR**  ",
            "> **1. Purpose & Core Methodology:** Precision spot swing execution radar. Bridges two distinct schools of analysis into a single unified engine: **5 Classic Trend & Momentum Models (S1–S5: Donchian, 200 SMA, 20/50 EMA, 14 RSI, 2σ Bollinger Bands)** and **Harmonic Fibonacci Geometry (S6–S7: Gartley 222 L-H-L-H-L and H-L-H-L-H)**.  ",
            "> **2. Dual-Horizon Philosophy (The Shield & The Spear):**  ",
            "> • **1D Daily Macro (The Shield):** Monitors primary multi-month trend. As long as Bitcoin trades above its 200-day moving average, capital is protected against buying into a macro bear market.  ",
            "> • **4H Tactical (The Spear):** Monitors the intermediate swing cycle, ignoring intraday noise to search exclusively for high-probability turning points where multiple indicators converge with Harmonic Potential Reversal Zones (PRZ).  ",
            "> **3. Built for Disciplined Spot Swing Traders:** Zero leverage, zero shorting (eliminates liquidation wipes), no subjective guesswork (strict mathematical criteria), and 100% mathematical parity with the automated GitHub Actions cloud bot (`@Gartleyy_bot`).  ",
            "> **4. 5-Second Verdict Ladder:** `GARTLEY SELL` > `CONFLUENCE BUY` > `HOLD` > `NO TRADE`.", 
            "",
            f"* **Live Spot Price**: `${gartley.close_price:,.2f}` | **Overall Multi-Timeframe Verdict**: `{gartley.overall_verdict}`",
            f"* **Plain English Takeaway**: {gartley.plain_english_summary}",
            f"* **Standalone Bot Repository**: `{gartley.standalone_bot_repo}` (GitHub Actions workflow every 4H UTC)",
            f"* **Telegram Delivery**: Bot: `{gartley.telegram_bot}` | Chat ID: `{gartley.telegram_chat_id}` | Schedule: `{gartley.schedule_cron}`",
            f"* **Webhook Bridge**: `{gartley.webhook_url}` (Google Apps Script /now trigger)",
            "",
            "### 9A. 1D Daily Macro Trend State Machine (S1–S7)",
            "",
            f"**1D Daily Trend Verdict**: `{r1d.verdict}` (Close: `${r1d.close:,.2f}`)",
            "",
            "| Strategy | Indicator / Model | Signal / Level | State / Action | Role & Context |",
            "| :--- | :--- | :--- | :--- | :--- |",
            f"| **S1: Breakout 20** | 20-bar Donchian High/Low | 20-bar Channel | `{r1d.v1_breakout}` | Macro Channel Trend Following |",
            f"| **S2: Trend SMA200** | 200-day Simple Moving Average | `${r1d.sma200_val:,.1f}` | `{r1d.v2_sma200}` | Institutional Macro Gatekeeper |",
            f"| **S3: EMA 20/50** | 20 EMA vs 50 EMA | EMA20: `${r1d.ema20_val:,.1f}` / EMA50: `${r1d.ema50_val:,.1f}` | `{r1d.v3_ema}` | Dynamic Trend Cross |",
            f"| **S4: 14 RSI** | 14-period Wilder RSI | `{r1d.rsi_val:.1f}` (Oversold 30 / Reclaim 50) | `{r1d.v4_rsi}` | Momentum Mean-Reversion |",
            f"| **S5: Bollinger Bands** | 20 SMA ± 2-Sigma Envelope | 2-Sigma Lower Band Sweep | `{r1d.v5_bb}` | Volatility Exhaustion Bounce |",
            f"| **S6: Gartley Bull** | Harmonic 222 Bullish (L-H-L-H-L) | PRZ D: `{f'${r1d.bull_d:,.2f}' if r1d.bull_d else 'NONE'}` | `{r1d.v6_gartley_bull}` | Fibonacci Precision Reversal |",
            f"| **S7: Gartley Bear** | Harmonic 222 Bearish (H-L-H-L-H) | PRZ D: `{f'${r1d.bear_d:,.2f}' if r1d.bear_d else 'NONE'}` | `{r1d.v7_gartley_bear}` | Harmonic Profit Taking / USDT Hedge |",
            "",
            "### 9B. 4H Tactical Swing Execution State Machine (S1–S7)",
            "",
            f"**4H Tactical Swing Verdict**: `{r4h.verdict}` (Close: `${r4h.close:,.2f}`)",
            "",
            "| Strategy | Indicator / Model | Signal / Level | State / Action | Role & Context |",
            "| :--- | :--- | :--- | :--- | :--- |",
            f"| **S1: Breakout 20** | 20-bar Donchian High/Low | 20-bar Channel | `{r4h.v1_breakout}` | Swing Channel Breakout |",
            f"| **S2: Trend SMA200** | 200-period Simple Moving Average | `${r4h.sma200_val:,.1f}` | `{r4h.v2_sma200}` | Intermediate Cycle Filter |",
            f"| **S3: EMA 20/50** | 20 EMA vs 50 EMA | EMA20: `${r4h.ema20_val:,.1f}` / EMA50: `${r4h.ema50_val:,.1f}` | `{r4h.v3_ema}` | Tactical Trend Alignment |",
            f"| **S4: 14 RSI** | 14-period Wilder RSI | `{r4h.rsi_val:.1f}` (Oversold 30 / Reclaim 50) | `{r4h.v4_rsi}` | Swing Dip Exhaustion |",
            f"| **S5: Bollinger Bands** | 20 SMA ± 2-Sigma Envelope | 2-Sigma Lower Band Sweep | `{r4h.v5_bb}` | Tactical Mean Reversion |",
            f"| **S6: Gartley Bull** | Harmonic 222 Bullish (L-H-L-H-L) | PRZ D: `{f'${r4h.bull_d:,.2f}' if r4h.bull_d else 'NONE'}` | `{r4h.v6_gartley_bull}` | Tactical Long Entry |",
            f"| **S7: Gartley Bear** | Harmonic 222 Bearish (H-L-H-L-H) | PRZ D: `{f'${r4h.bear_d:,.2f}' if r4h.bear_d else 'NONE'}` | `{r4h.v7_gartley_bear}` | Tactical Exit to USDT |",
            "",
            "### 9C. Harmonic Pattern Geometry & Fibonacci Verification",
            "",
            "| Horizon | Pattern | Geometry (X-A-B-C-D) | Ratio Verification (Target / Actual) | PRZ Reversal Level ($) | Signal Status |",
            "| :--- | :--- | :--- | :--- | :--- | :--- |",
            f"| **1D Macro** | Bullish Gartley 222 | L-H-L-H-L (X < B < D < A) | `{r1d.bull_ratios if r1d.bull_ratios else 'Scanning pivots...'}` | `{f'${r1d.bull_d:,.2f}' if r1d.bull_d else 'N/A'}` | `{r1d.v6_gartley_bull}` |",
            f"| **1D Macro** | Bearish Gartley 222 | H-L-H-L-H (X > B > D > A) | `{r1d.bear_ratios if r1d.bear_ratios else 'Scanning pivots...'}` | `{f'${r1d.bear_d:,.2f}' if r1d.bear_d else 'N/A'}` | `{r1d.v7_gartley_bear}` |",
            f"| **4H Tactical** | Bullish Gartley 222 | L-H-L-H-L (X < B < D < A) | `{r4h.bull_ratios if r4h.bull_ratios else 'Scanning pivots...'}` | `{f'${r4h.bull_d:,.2f}' if r4h.bull_d else 'N/A'}` | `{r4h.v6_gartley_bull}` |",
            f"| **4H Tactical** | Bearish Gartley 222 | H-L-H-L-H (X > B > D > A) | `{r4h.bear_ratios if r4h.bear_ratios else 'Scanning pivots...'}` | `{f'${r4h.bear_d:,.2f}' if r4h.bear_d else 'N/A'}` | `{r4h.v7_gartley_bear}` |",
            "",
            "### 9D. Pine Script Verdict Priority Ladder & Action Rule",
            "",
            "* **Hierarchy**: `GARTLEY SELL TO USDT` > `CONFLUENCE + GARTLEY BUY` > `GARTLEY BUY` > `EXIT PRESSURE` > `CONFLICT` > `EXIT WARNING` > `CONFLUENCE BUY` > `ENTRY WATCH` > `HOLD` > `NO TRADE`.",
            f"* **Current Active Alignment**: Overall: **`{gartley.overall_verdict}`**.",
            "* **Capital Allocation**: Non-leveraged spot execution. Pairs harmoniously with Supreme Master Tab [0] and Specialist Desks [1]–[9].",
        ])

    trap = store.trap_evaluation
    if trap is not None:
        lines.extend([
            "",
            "---",
            "",
            "## SECTION 10: TAB [8] PATTERN INVALIDATION, LIQUIDITY SWEEP & SFP TRAP RADAR",
            "",
            "> [!NOTE]",
            "> **THE LIQUIDITY SWEEP & SFP RECLAIM ARBITRATION LAW**  ",
            "> Classical geometric chart patterns (Head & Shoulders, Double Bottoms/Tops, Wedges, Flags) fail ~50%–60% of the time in Bitcoin due to perpetual swap leverage and deliberate algorithmic stop-hunting. Tab [8] weaponizes retail predictability by identifying when pattern boundaries are swept and absorbed by passive institutional bids.",
            "",
            f"* **Live Spot Reference**: `${trap.spot_price:,.2f}` | **Active Trap State**: `{trap.active_trap_state.value}`",
            f"* **Primary Tactical Signal**: `{trap.active_trap_signal}`",
            f"* **Asia Session Range**: Asia High: `${trap.asia_high:,.1f}` (Swept: `{trap.asia_high_swept}`) | Asia Low: `${trap.asia_low:,.1f}` (Swept: `{trap.asia_low_swept}`)",
            f"* **Active Displacement Voids**: `{len(trap.active_fvgs)} active FVGs tracked within 5%`",
            f"* **Passive Absorption Flag**: `{'ACTIVE (Limit Bids/Offers Absorbing Takers)' if trap.passive_absorption_flag else 'NORMAL ORDER FLOW'}`",
            f"* **Open Interest Velocity**: 15m dOI: `{trap.oi_15m_delta_pct:+.3f}%` | 1H dOI: `{trap.oi_1h_delta_pct:+.3f}%` (Surge Flag: `{'TRUE (Trapped Chasers)' if trap.oi_surge_flag else 'FALSE'}`)",
            f"* **Rolling Volume Delta**: 1m CVD: `{trap.rolling_1m_cvd:+.2f} BTC` | 5m CVD: `{trap.rolling_5m_cvd:+.2f} BTC` | 15m CVD: `{trap.rolling_15m_cvd:+.2f} BTC`",
            f"* **Absorption Elasticity Ratio**: `{trap.absorption_divergence_ratio:.1f}x` (|CVD| / |ΔP%|)",
            f"* **Quantitative Takeaway**: {trap.quantitative_takeaway}",
            f"* **Plain English Summary**: {trap.plain_english_summary}",
            "",
            "### 10A. Active Classical Pattern Boundaries & Liquidity Proximity Registry",
            "",
            "| Pattern Name | Type | Boundary Level | Sweep Wick Extreme | Distance ($ / %) | Distance (ATR) | Status | Trap Bias | Liquidity Tier |",
            "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
        ])
        for p in trap.active_patterns:
            lines.append(
                f"| **`{p.pattern_name}`** | `{p.pattern_type.value}` | `${p.boundary_level:,.1f}` | `${p.sweep_wick_extreme:,.1f}` | `{p.distance_pct:+.2f}%` | `{p.distance_atr:+.2f}x` | `{p.status}` | `{p.trap_bias}` | {p.liquidation_tier} |"
            )

        if trap.trade_plan is not None:
            tp = trap.trade_plan
            lines.extend([
                "",
                "### 10B. Actionable Asymmetric SFP Execution Geometry (R:R >= 1:3)",
                "",
                "| Direction / Play | Entry Price | Invalidation Stop Loss | TP1 (Value POC) | TP2 (Opposite Boundary) | Risk ($) | Reward ($) | R:R Ratio |",
                "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
                f"| **`{tp.direction}`** | `${tp.entry_price:,.2f}` | `${tp.stop_loss:,.2f}` | `${tp.tp1_poc:,.2f}` | `${tp.tp2_opposite_boundary:,.2f}` | `${tp.risk_dollars:,.2f}` | `${tp.reward_dollars:,.2f}` | **`{tp.rr_ratio:.2f}R`** |",
                "",
                f"> [!TIP]",
                f"> **SFP Execution Protocol**: {tp.invalidation_summary}",
            ])

        if trap.active_fvgs:
            lines.extend([
                "",
                "### 10D. Active Fair Value Gaps (15m/1H FVGs) & Consequent Encroachment (50% CE) Registry",
                "",
                "| ID | TF | Direction | Imbalance Bounds ($) | 50% CE ($) | Gap Size (%) | Distance to CE | Mitigation Status |",
                "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
            ])
            for f in trap.active_fvgs[:6]:
                lines.append(
                    f"| `#{f.id}` | `{f.timeframe}` | **`{f.direction}`** | `${f.bottom_price:,.1f} – ${f.top_price:,.1f}` | **`${f.ce_midpoint:,.1f}`** | `{f.gap_pct:+.2f}%` | `{f.distance_pct:+.2f}%` | `{f.status}` |"
                )

        lines.extend([
            "",
            "### 10C. Anti-Sycophancy Rulebook for Classical Patterns (How to Avoid Retail Liquidity Traps)",
            "",
            "* **The Retail Flaw**: Buying flag breakouts or shorting H&S necklines puts your stop right where market makers want to fill size.",
            "* **The Institutional Reclaim Rule**: Never trade while price is outside the boundary. Enter ONLY when a 15m/1H candle body closes BACK INSIDE with passive absorption (negative Perp CVD but price resilient).",
            "* **Position Sizing**: Trapped participants' forced market orders provide the fuel. Size with standard risk and trail stop to breakeven at TP1.",
        ])

    # --- SECTION 11: TAB [9] TERMINAL EXHAUSTION & DELTA DIVERGENCE RADAR ---
    if store.exhaustion_evaluation is not None:
        ex = store.exhaustion_evaluation
        lines.extend([
            "",
            "---",
            "",
            "## SECTION 11: TAB [9] TERMINAL EXHAUSTION & DELTA DIVERGENCE RADAR",
            "",
            "> [!NOTE]",
            "> **THE DETERMINISTIC MOMENTUM EXHAUSTION LAW**  ",
            "> Replaces subjective, non-falsifiable Elliott Wave counts (Wave 5 tops and Wave C bottoms) with deterministic Tom DeMark (TD) 9-count setups, multi-horizon Cumulative Volume Delta (CVD) divergences, and Open Interest / Funding climax stress.",
            "",
            f"* **Live Spot Reference**: `${ex.spot_price:,.2f}` | **Composite Exhaustion Score**: **`{ex.exhaustion_score:.1f}/100`**",
            f"* **Exhaustion Regime**: **`{ex.exhaustion_regime.value}`**",
            f"* **Primary Tactical Signal**: **`{ex.active_exhaustion_signal}`**",
            f"* **Open Interest Velocity**: 1H dOI: `{ex.oi_climax_pct:+.3f}%` (Climax Flag: `{ex.oi_climax_flag}`)",
            f"* **Funding Rate Stress**: Live 8H Funding: `{ex.current_funding_pct:+.4f}%` (Funding Climax Flag: `{ex.funding_climax_flag}`)",
            f"* **Quantitative Takeaway**: {ex.quantitative_takeaway}",
            f"* **Plain English Summary**: {ex.plain_english_summary}",
            "",
            "### 11A. Tom DeMark (TD) Sequential Setup Audit (1H & 4H Horizons)",
            "",
            "| Horizon | Setup Count | Direction / Polarity | Status | Perfected (Bar 8/9 Extreme) | Invalidation Anchor ($) |",
            "| :--- | :--- | :--- | :--- | :--- | :--- |",
            f"| **1H Tactical** | `{ex.td_1h.setup_count}/9` | `{ex.td_1h.direction}` | `{ex.td_1h.status}` | **`{ex.td_1h.is_perfected}`** | `${ex.td_1h.invalidation_level:,.1f}` |",
            f"| **4H Trend** | `{ex.td_4h.setup_count}/9` | `{ex.td_4h.direction}` | `{ex.td_4h.status}` | **`{ex.td_4h.is_perfected}`** | `${ex.td_4h.invalidation_level:,.1f}` |",
            "",
            "### 11B. Multi-Horizon CVD Divergence & Absorption Matrix",
            "",
            "| Horizon | Divergence Classification | Price Extrema | Delta Extrema | Spot Delta (BTC) | Perp Delta (BTC) | Conviction / Significance |",
            "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
        ])
        if ex.divergences:
            for d in ex.divergences:
                lines.append(
                    f"| **`{d.horizon}`** | `{d.divergence_type}` | `{d.price_extrema}` | `{d.cvd_extrema}` | `{d.spot_delta:+.1f}` | `{d.perp_delta:+.1f}` | **`{d.significance}`** |"
                )
        else:
            lines.append(
                "| `15m/1H` | `NONE` | `Price expanding in phase with volume delta` | `No divergence detected` | `N/A` | `N/A` | `HEALTHY MOMENTUM` |"
            )

        if ex.trade_plan is not None:
            tp = ex.trade_plan
            lines.extend([
                "",
                "### 11C. Actionable Exhaustion Mean-Reversion Trade Plan (R:R >= 1:2.5)",
                "",
                "| Direction / Play | Entry Price | Invalidation Stop Loss | TP1 (Fast Mean / POC) | TP2 (Composite Value POC) | Risk ($) | Reward ($) | R:R Ratio |",
                "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
                f"| **`{tp.direction}`** | `${tp.entry_price:,.2f}` | `${tp.stop_loss:,.2f}` | `${tp.tp1_fast_mean:,.2f}` | `${tp.tp2_value_poc:,.2f}` | `${tp.risk_dollars:,.2f}` | `${tp.reward_dollars:,.2f}` | **`{tp.rr_ratio:.2f}R`** |",
                "",
                f"> [!TIP]",
                f"> **Exhaustion Execution Protocol**: {tp.invalidation_summary}",
            ])

        lines.extend([
            "",
            "### 11D. Quantitative Anti-Sycophancy Rulebook (Why EWT Fails vs. Deterministic Sequential)",
            "",
            "* **The Alternate Count Trap**: Classical Elliott Wave theorists endlessly re-label counts after getting stopped out. Quantitative desks never trade subjective labels.",
            "* **The Liquidity Absorption Reality**: Markets do not turn because 'Wave 5 is complete'; they turn when aggressive taker volume runs out of capital and is absorbed by passive limit orders.",
            "* **Sequential Invalidation**: A TD-9 setup is immediately invalidated if a subsequent candle body closes beyond the setup's true extreme price bar. Always enforce deterministic stops.",
        ])

    # --- SECTION 12: CONSOLIDATED PROTOCOL METRICS DOSSIER (SUPER GROK SPECIFICATION) ---
    from analytics.protocol_dossier import (
        compute_protocol_metrics_dossier,
        format_protocol_metrics_dossier_markdown,
    )

    dossier = store.protocol_dossier
    if dossier is None:
        dossier = compute_protocol_metrics_dossier(config, store, store.macro_intermarket)
        store.protocol_dossier = dossier

    dossier_text = format_protocol_metrics_dossier_markdown(dossier)
    lines.extend([
        "",
        dossier_text.strip(),
    ])

    return "\n".join(lines) + "\n"


def copy_ai_packet_to_clipboard_and_disk(config: EngineConfig, store: StateStore) -> Tuple[bool, str, int]:
    """Builds the AI telemetry packet, copies it to the Windows clipboard, and writes it to Downloads & logs/."""
    packet_text = build_ai_telemetry_packet(config, store)
    char_count = len(packet_text)

    # 1. Save to logs/latest_ai_data_packet.md and C:\Users\aikel\Downloads\BTC_AI_DATA_PACKET_LATEST.md
    log_file = config.signal_log_path.parent / "latest_ai_data_packet.md"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    log_file.write_text(packet_text, encoding="utf-8")

    downloads_dir = pathlib.Path.home() / "Downloads"
    if downloads_dir.exists():
        try:
            (downloads_dir / "BTC_AI_DATA_PACKET_LATEST.md").write_text(packet_text, encoding="utf-8")
        except Exception:
            pass
    try:
        pathlib.Path("BTC_AI_DATA_PACKET_LATEST.md").write_text(packet_text, encoding="utf-8")
    except Exception:
        pass

    # 2. Copy to System Clipboard (Windows clip.exe / PowerShell, Android Termux, Linux, & SSH OSC-52)
    copied_ok = False
    if os.name == "nt":
        try:
            subprocess.run(
                ["clip.exe"],
                input=packet_text.encode("utf-16le"),
                check=True,
                timeout=3.0,
            )
            copied_ok = True
        except Exception:
            try:
                subprocess.run(
                    ["powershell", "-NoProfile", "-Command", "Set-Clipboard -Value $input"],
                    input=packet_text.encode("utf-8"),
                    check=True,
                    timeout=4.0,
                )
                copied_ok = True
            except Exception:
                copied_ok = False
    else:
        # Android Termux / Linux clipboard tools + OSC-52 SSH clipboard sequence (works on Termius/Android SSH)
        for cmd in (["termux-clipboard-set"], ["wl-copy"], ["xclip", "-selection", "clipboard"]):
            try:
                subprocess.run(cmd, input=packet_text.encode("utf-8"), check=True, timeout=3.0)
                copied_ok = True
                break
            except Exception:
                continue
        try:
            b64_data = base64.b64encode(packet_text.encode("utf-8")).decode("ascii")
            sys.stdout.write(f"\033]52;c;{b64_data}\a")
            sys.stdout.flush()
            copied_ok = True
        except Exception:
            pass

    now_sgt_str = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")
    store.last_packet_copied_utc = now_sgt_str
    store.last_packet_copied_ts = time.time()
    store.last_packet_char_count = char_count
    return copied_ok, str(log_file), char_count
