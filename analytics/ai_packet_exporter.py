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

        "You are the **Independent Chief Quantitative Strategist & Risk Officer** auditing a live real-time telemetry packet exported from the **`BTC-USD Spot Swing Engine`** (`17-Desk Rich Live Terminal: Tab [0] Master & Desks [1]–[9]`).",

        "",

        "### 1. Rule #0 — Strict Anti-Sycophancy & Chief Engineer Authority",

        "* **Do NOT blindly agree with the Python engine's benchmark verdict in Section 6.** Deterministic code evaluates fixed mathematical thresholds and can miss subtle cross-venue divergences (e.g., negative Coinbase Premium while Binance ticks up, 5-minute perp sell bursts, nearby unflushed long-liquidation magnets within 1%, or over-concentrated single-fill entries).",

        "* You have **full Chief Engineer authority** to confirm, refine, split into multiple limit tranches, or override the Python engine's conclusion based on the raw telemetry across all specialist desks (**Desks [1]–[9]**).",

        "",

        "### 2. How to Interpret & Audit Sections 0–16 (The Complete 17-Desk Quantitative Playbook)",

        "0. **Section 0 Audit (`Tab [0] BTC Spot Swing Screener, 1:3 RRR Magnet Protocol & Footprint Gate`)**:",

        "   * **1D Macro Squeeze & Weekly PWL Sweep**: Evaluates `Close > EMA50 > EMA200`, `20-BBW 180D Percentile <= 30%`, and `4H Sweep & Reclaim of Previous Week Low (PWL)`.",

        "   * **1:3 RRR Liquidation Magnet Law (Section 0D)**: Requires `>= 3.0R` reward-to-risk to the nearest Short-Liquidation Magnet before authorizing market entries; if `Live R:R < 3.0R`, enforce `Do Nothing` at market and stage limit bids at or below `Max 3R Entry`.",

        "1. **Section 1 Audit (`Cross-Exchange Spot, Basis & Derivatives`)**:",

        "   * **Coinbase Premium (`CPI`)**: `CPI > +0.02%` (`Z >= +0.5σ`) = US institutional spot buying. `CPI < -0.05%` (Coinbase at a deep discount to Binance) = warning that US spot is lagging or selling into offshore USDT moves.",

        "   * **Open Interest (`Strict BTC Coins`) & `dOI %`**: `AGGRESSIVE_SHORT_BUILD` (`Price Down/Flat + OI Up`) is bullish squeeze fuel *only* if `Spot CVD` is positive (passive spot absorbing shorts). `LEVERAGED_LONG_EXPANSION` (`Price Up + OI Up + High Funding > +0.012%`) is a long-trap warning. `LONG_LIQUIDATION_FLUSH` (`Price Down + OI Down`) clears excess leverage.",

        "   * **5m Taker L/S Ratio & 5m Perp Delta**: If `5m Taker L/S < 0.50` with heavy negative `5m Perp Delta`, sellers are actively pressing the tape right now -> prefer staged limit bids over market orders.",

        "2. **Section 2 Audit (`Composite Volume Profile 30D/7D/24H, Multi-Horizon CVD & 15m Footprint`)**:",

        "   * **Value Area & Mid-Range Chop Law**: `cVAL` = lower 70% Value Area support; `cPOC` = fair-value magnet (`TP1`); `cVAH` = upper resistance (`TP2`). If `Value Area Position %` is inside `30%–70%` OR price is floating mid-gap between `Support HVN Floor` and `cVAL` outside the `0.5x ATR` edge (`Mid-Range Chop Flag: True`), **never chase at market**; wait for `cVAL` or `Support HVN Floor`.",

        "   * **Spot vs. Perp CVD Divergence**: True institutional accumulation requires `Spot CVD > 0` (`4H B/S Ratio > 1.05`) while `Perp CVD < 0` (`Spot-Perp Divergence Z > +1.5σ`, `Passive Absorption Index >= 0.85`).",

        "   * **SweepRetestFSM Gate 4 Law**: Never enter on first touch of `cVAL`. Require rejection, candle reclaim, and an orderly retest inside the `±0.20%` retest band (`PENDING_RETEST -> TRIGGERED`). Hard stop is anchored below the sweep wick with a +0.15% buffer.",

        "   * **3-EMA Industrial Confluence Law**: Daily 200 EMA slope and price location form an absolute gatekeeper (No spot buys if price < falling Daily 200 EMA). In bull regimes (`STRONG_BULL` / `WEAK_BULL`), pullback into the 4H 50-EMA zone with >= 2 of 3 positioning confirmations (stable OI, neutral funding <= +0.010%, positive Spot CVD) validates tactical execution.",

        "   * **Bidirectional 15m Footprint 3-Gate Playbook (Section 2C — Symmetrical Accumulation & Distribution)**:",

        "     - **Mode A — Spot Accumulation (Buy Low at Support to Sell Higher)**: `Gate 1` = Lower Support Tap (`30D/7D cVAL`, `Support HVN`, or `Demand POC`); `Gate 2` = Lower-wick trapped seller absorption (aggressive sells absorbed in lower 25% wick with candle bounce) or Battle Zone churn; `Gate 3` = 15m candle delta flipped positive (`BULLISH FLIP CONFIRMED`). All 3 gates authorize spot accumulation with hard stop `-0.15%` below wick and `1:2` / `1:3 R:R` targets.",

        "     - **Mode B — Spot Distribution / Profit Harvest (Sell High to USDT at Resistance & Rebuy Lower)**: `Gate 1` = Upper Resistance Tap (`30D/7D cVAH`, `Range High`, or `Supply POC`); `Gate 2` = Upper-wick trapped buyer exhaustion (aggressive buys absorbed in upper 25% wick with rejection) or Stacked Sell Imbalances; `Gate 3` = 15m candle delta flipped negative (`BEARISH FLIP CONFIRMED`). All 3 gates trigger a `50% Staged Spot Profit Harvest to USDT` with breakout invalidation stop (`+0.15%` above upper wick) and a designated lower support `Rebuy Target` to compound total BTC coin count without leverage.",

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

        "11. **Section 12 Audit (`Consolidated Protocol Metrics Dossier & Intermarket Cross-Check`)**:",

        "   * **Prior Day/Week Auction & ETF/Macro Context**: Cross-verify Prior Day/Week POC/VAH/VAL location, L2 Order-Book Depth (`±1%`/`±2%`), US Spot ETF net flows, DXY/TIPS real yields, and 14D Wilder RSI / Log-Spread Z-score.",

        "12. **Section 13 Audit (`Tab [P] Price Action & Structure Protocol — SLSP v1.0, Industrial 3-EMA & Tell-Tale Climax`)**:",

        "   * **SLSP v1.0 Swing Liquidity**: Evaluates 4H/1H Industrial 3-EMA trend regime (`EMA21 > EMA55 > EMA200`), 4H Liquidation Wick Flushes (`>= 45%` lower wick), and climax volume absorption.",

        "14. **Section 15 Audit (`Tab [G] Grok Dual-Horizon Flow & 00:00 UTC Anchored VWAP SD Matrix`)**:",

        "   * **Grok Dual-Horizon Analysis**: Cross-checks 4A Swing Context (Daily/4H) vs. 4B Day Context (1H/15m), 00:00 UTC Anchored VWAP ±1σ/±2σ bands, CoinGlass crowding, multi-horizon Spot/Perp CVD divergence, overhead short-liquidation magnets vs. downside long traps, and the Engine Bottomline Verdict.",

        "15. **Section 16 Audit (`Tab [R] SSRN Quantitative Alpha Deck & Academic Empirical Research`)**:",

        "   * **Academic Empirical Foundations**: 5 peer-reviewed SSRN domains (Market Microstructure & Order Book Depth, Time-Series Momentum, Systematic Factor Pricing, On-Chain Structural Metrics, Alternative Data & Machine Learning Friction Hurdles).",

        "   * **5 Operational Academic Risk Gates**: Mesíček & Vojtko (SSRN 5748642) 1D/1H MACD gate, Zarattini et al. (SSRN 5209907) 20D volatility targeting, Karassavidis et al. (SSRN 5821842) 8H ATR dynamic stops, Chan (SSRN 5292305) +30% annualized funding ceiling, and Bysik & Ślepaczuk (SSRN 6795938) 18 bps round-trip cost hurdle.",

        "16. **Section 17 Audit (`Tab [M] BTC Magnet · Liquidation Gravity & Swing Edge Detector`)**:",

        "   * **Liquidation Gravitational Horizon & Speaking Rules**: Real-time upper short liquidation cluster vs. lower long support cluster, dominant pull ratio, and the 7 locked internal speaking rules (defaults to 'wait').",

        "",

        "### 3. Mandatory 5-Part Response Format",

        "Structure your audit into:",

        "1. **Independent Cross-Tab Telemetry Audit** (Bullish Confluence vs. Hidden Friction/Risk Flags across Tab [0] & Specialist Desks [1]–[9], Tab [G], and Tab [R])",

        "2. **Critique of Python Engine Benchmark** (Where you **AGREE** vs. **DISAGREE / REFINE** Section 6)",

        "3. **Independent AI Traffic-Light Verdict & Conviction %** (`GREEN`, `BLUE`, `YELLOW`, or `RED`)",

        "4. **Reconciled Master Order of Battle** (**Track A: If Flat in Cash** with exact Tranche 1/2 `$` zones, `BTC`/`$` sizes, Hard Stop, `TP1`/`TP2` vs. **Track B: If Already Holding Spot BTC** with Hard Stop, `TP1`/`TP2` Profit Harvest levels, and Lower Support Rebuy Target to grow total BTC coin count)",

        "5. **Plain-English Executive Bottom Line** (`What's Happening`, `Why`, `Your Exact Next Move`)",

    ]



    # --- SECTION 0: TAB [0] BTC SPOT SWING SCREENING & ALERT ENGINE ---

    sw_ev = store.spot_swing_evaluation

    if sw_ev is not None:
        f_ev_s0 = getattr(store, "footprint_evaluation", None)
        if f_ev_s0 is not None:
            if f_ev_s0.all_gates_pass and f_ev_s0.direction == "DISTRIBUTE_SELL":
                fp_s0_str = f"[✓] BUYER EXHAUSTION — PROFIT HARVEST (Sell {f_ev_s0.harvest_tranche_pct:.0f}% @ ${f_ev_s0.entry_price:,.0f} -> Rebuy @ ${f_ev_s0.rebuy_target_price:,.0f})"
            elif f_ev_s0.all_gates_pass:
                fp_s0_str = f"[✓] ABSORPTION HELD & DELTA FLIPPED (Spot Buy @ ${f_ev_s0.entry_price:,.0f} | Stop ${f_ev_s0.stop_loss:,.0f})"
            elif f_ev_s0.signal_status == "ARMED":
                fp_s0_str = f"[!] ARMED ({f_ev_s0.direction}) — Level Tapped ({f_ev_s0.gate1_tapped_level_name}) + {f_ev_s0.gate2_detail}"
            else:
                fp_s0_str = f"[○] MID-CHOP (OBSERVATION) • 15m Delta: {f_ev_s0.active_bar_delta:+,.2f} BTC ({f_ev_s0.gate2_detail or 'Awaiting key level tap'})"
        else:
            fp_s0_str = "[○] WARMING UP"

        lines.extend([

            "",

            "---",

            "",

            "## SECTION 0: TAB [0] BTC SPOT SWING SCREENING & ALERT ENGINE (MACRO SQUEEZE • WEEKLY LIQUIDITY SWEEP • TRIPLE-BARRIER RISK)",

            "",

            f"* **Live Verdict & Traffic Light**: `{sw_ev.verdict}` (`{sw_ev.traffic_light}`)",

            f"* **Plain-English Summary**: {sw_ev.plain_english_summary}",

            f"* **15m Microstructure Footprint Gate**: `{fp_s0_str}`",

            f"* **Alerting & Execution State**: Alerts: `{'ARMED' if sw_ev.alerts_enabled else 'OFF'}` • Read-Only: `{sw_ev.read_only}` • Equity: `${sw_ev.equity_usd:,.0f}` • Risk Budget: `{sw_ev.risk_pct:.1f}%`",

            "",

            "### 0A. 1D Macro Regime Gate",

            "",

            "| Macro Gate Check | Metric / Formula | Live Value | Gate State |",

            "| :--- | :--- | :--- | :--- |",

        ])

        if sw_ev.macro is not None:

            m = sw_ev.macro
            bar_dt_str = (
                datetime.fromtimestamp(m.bar_ts_ms / 1000.0, tz=timezone.utc).strftime("%Y-%m-%d UTC")
                if m.bar_ts_ms > 0
                else str(m.bar_ts_ms)
            )

            lines.extend([

                f"| **Trend Baseline** | `Close > EMA50 > EMA200` | Close: `${m.close:,.2f}` • EMA50: `${m.ema50:,.2f}` • EMA200: `${m.ema200:,.2f}` | `{'PASS (BULLISH)' if m.trend_pass else 'FAIL (NO TREND)'}` |",

                f"| **Volatility Squeeze** | `20 BBW 180D Rank <= 30%` | BBW: `{m.bbw * 100:.2f}%` • Percentile Rank: `{m.bbw_percentile * 100:.1f}%` (Lookback: `{m.squeeze_lookback_bars}D`) | `{'PASS (COMPRESSED)' if m.compression_pass else 'FAIL (EXPANDED)'}` |",

                f"| **Macro Gate Permission** | `Trend AND Squeeze` | Finalized 1D Bar: `{bar_dt_str}` (`{m.bar_ts_ms}`) | `{'APPROVED (SPOT ALLOCATION PERMITTED)' if m.macro_approved else 'FROZEN (100% CASH)'}` |",

            ])

        else:

            lines.append("| **Macro Gate** | 1D Klines Syncing | Warming up... | `INITIALIZING` |")



        lines.extend([

            "",

            "### 0B. 4H Weekly Anchors & Structural Liquidity Setup",

            "",

            "| Structural Check | Rule / Timeframe | Live Measurement | Signal Confirmation |",

            "| :--- | :--- | :--- | :--- |",

        ])

        if sw_ev.setup is not None and sw_ev.setup.anchors_ready:

            s = sw_ev.setup

            lines.extend([

                f"| **Previous Week High / Low** | Mon–Sun Weekly Anchor | PWH: `${s.pwh:,.2f}` • PWL: `${s.pwl:,.2f}` | `READY` |",

                f"| **Rolling 12-Bar 4H Sweep** | `4H Low < PWL` | Lowest Wick: `${s.sweep_low:,.2f}` | `{'SWEEP DETECTED' if s.sweep_detected else 'NO SWEEP'}` |",

                f"| **Finalized 4H Reclaim** | `4H Close > PWL` | Closed Candle: `${s.close:,.2f}` | `{'RECLAIM CONFIRMED' if s.reclaim_confirmed else 'NO RECLAIM'}` |",

                f"| **Volume Expansion** | `4H Volume > SMA_vol(3)` | Bar Vol: `{s.volume:,.1f}` vs SMA3: `{s.vol_sma3:,.1f}` | `{'VOLUME CONFIRMED' if s.volume_confirmed else 'LOW VOLUME'}` |",

                f"| **Signal Trigger Status** | `Sweep AND Reclaim AND Vol` | Freshness: `{'FRESH' if s.is_fresh else 'ALREADY ACTED'}` | `{'ACTIVE LONG SETUP' if s.signal_active else 'STANDBY'}` |",

            ])

        else:

            lines.append("| **Weekly Anchors** | Mon–Sun Weekly Anchor | Syncing previous week klines... | `INITIALIZING` |")



        lines.extend([

            "",

            "### 0C. Volatility-Adjusted Risk Engine & Triple-Barrier Order Card",

            "",

        ])

        if sw_ev.trade is not None:

            t = sw_ev.trade

            dist = max(t.entry - t.initial_stop, 1.0)

            cur_r = (atomic_spot_price - t.entry) / dist

            lines.extend([

                f"* **Active Trade Status**: `{t.status}` (Setup ID: `{t.setup_id}`)",

                f"* **Execution Price**: `${t.entry:,.2f}` | **Position Size**: `{t.qty_btc:.6f} BTC` (${t.qty_btc * t.entry:,.2f})",

                f"* **Live Unrealized Multiple**: `{cur_r:+.2f}R` (Spot: `${atomic_spot_price:,.2f}`)",

                f"* **Barrier 1 (Stop Loss)**: Current Stop: `${t.current_stop:,.2f}` (Initial: `${t.initial_stop:,.2f}` • `{'STOP AT BREAKEVEN' if t.tp1_hit else 'INITIAL STOP'}`)",

                f"* **Barrier 2a (+2.0R Take Profit)**: `${t.tp1:,.2f}` (`{'50% SOLD' if t.tp1_hit else 'PENDING'}`)",

                f"* **Barrier 2b (PWH Structural Target)**: `${t.tp2:,.2f}`",

                f"* **Barrier 3 (Time Stop Expiry)**: 10 Trading Days Expiry (`{t.time_stop_ts_ms}`)",

            ])

        elif sw_ev.risk is not None:

            rk = sw_ev.risk

            lines.extend([

                f"* **Entry Reference (P_entry)**: `${rk.entry:,.2f}`",

                f"* **Stop Loss (P_stop)**: `${rk.stop:,.2f}` (Sweep Low − 0.5 × 14-ATR `${rk.atr14:,.2f}` • Distance: `${rk.stop_distance:,.2f}` / `{rk.stop_distance_pct:.2f}%`)",

                f"* **Position Sizing**: `{rk.qty_btc:.6f} BTC` (${rk.notional_usd:,.2f} USD notional • `{rk.equity_alloc_pct:.1f}%` of `${rk.equity_usd:,.0f}` Equity • `{'CAPPED AT 100% SPOT' if rk.spot_capped else '1.0% RISK COMPLIANT'}`)",

                f"* **Barrier 2a Target (+2.0R)**: `${rk.tp1:,.2f}` (Sell 50%, move stop to breakeven)",

                f"* **Barrier 2b Target (PWH Runner)**: `${rk.tp2_pwh:,.2f}`" + (" *(Warning: PWH <= +2.0R)*" if rk.tp2_inside_tp1 else ""),

                f"* **Barrier 3 (Time Stop)**: 10 Trading Days Expiry",

            ])

        else:

            lines.append("* **Standing Risk Protocol**: 1.0% Equity Risk, 14-period ATR buffer below sweep low, 100% Spot ceiling, +2.0R / PWH dual targets, 10-day time barrier.")



        liq_rep = store.trap_evaluation.liquidation_report if store.trap_evaluation else None

        tt_ev = store.exhaustion_evaluation.tell_tale if store.exhaustion_evaluation else None

        liq_str = f"{liq_rep.verdict} (Q={liq_rep.liquidation_multiple_24h:.2f}x)" if (liq_rep and liq_rep.is_available) else "STANDBY / OFFLINE"

        tt_str = tt_ev.plain_status if tt_ev else "NORMAL"

        lines.append(f"* **Pre-Flight Safety Guard**: Liquidation Cascade: `{liq_str}` | Tell-Tale Climax: `{tt_str}`")

        if sw_ev.magnet is not None:
            mg = sw_ev.magnet
            lines.extend([
                "",
                "### 0D. Daily Liquidation Magnet Protocol & RRR 1:3 Verdict (Master Prompt Output)",
                "",
                f"* **Regime**: `{mg.regime}` ({mg.regime_detail})",
                "* **Key Levels**:",
                f"  * **Short-liq magnet**: `${mg.short_liq_magnet:,.2f}` (`+{mg.short_liq_distance_pct:.2f}%` • `{mg.short_liq_size_label}` • `{mg.short_liq_source}`)",
                f"  * **Long-liq magnet**: `${mg.long_liq_magnet:,.2f}` (`-{mg.long_liq_distance_pct:.2f}%` • `{mg.long_liq_size_label}` • `{mg.long_liq_source}`)",
                f"  * **50-day MA**: `${mg.sma50_1d:,.2f}` (EMA50: `${mg.ema50_1d:,.2f}` • 5D Slope: `{mg.sma50_slope_5d_pct:+.2f}%`)",
                f"  * **Range pivot / invalidation**: `${mg.range_pivot:,.2f}` / `${mg.invalidation_level:,.2f}` (30–45D Range: `${mg.range_low_30d:,.2f} – ${mg.range_high_30d:,.2f}`)",
                "* **Positioning Snapshot**:",
                f"  * **OI**: `{mg.oi_trend}`",
                f"  * **Funding**: `{mg.funding_status}`",
                f"  * **Spot CVD on recent move**: `{mg.spot_cvd_assessment}`",
                f"  * **24H Cumulative Liquidations**: `{mg.cum_liq_24h_summary}`",
                f"* **Headline Filter**: `{mg.headline_filter}`",
                f"* **RRR 1:3 Money Management Check**: Live R:R = `{mg.rrr_to_magnet:.2f}R` (`{'PASS >= 3.0R' if mg.rrr_pass else 'REJECTED < 3.0R'}`) | Hard Stop: `${mg.hard_stop_price:,.2f}` | 3R Target: `${mg.tp_3r_price:,.2f}` | Max 3R Entry: `<=${mg.max_entry_for_3r:,.2f}` | 1% Risk Size: `{mg.recommended_qty_btc:.6f} BTC` (`${mg.recommended_notional_usd:,.2f}`)",
                f"* **Verdict**: **`{mg.verdict}`**",
                f"* **Confidence**: `{mg.confidence}`",
                f"* **Primary Reason**: {mg.primary_reason}",
                f"* **Invalidation**: {mg.invalidation_text}",
                f"* **Actionable Note**: {mg.actionable_note}",
            ])



    lines.extend([

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

    ])



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

        chop_desc = (
            f"Mid-Range Chop Flag: {sig.is_mid_range_chop} [Lower-Gap Chop: Support HVN to cVAL]"
            if (sig.is_mid_range_chop and sig.va_position_pct < 0)
            else f"Mid-Range Chop Flag: {sig.is_mid_range_chop}"
        )
        lines.extend([

            "",

            f"* **Active Structural Profile**: `{sig.active_horizon}` | **Distance to cVAL**: `{sig.distance_to_val_pct:+.2f}%` (`{sig.distance_to_val_atr:+.2f} ATR`) | **Value Area Position (`0%=cVAL, 100%=cVAH`)**: `{sig.va_position_pct:+.1f}%` (`{chop_desc}`) | **1H ATR**: `${sig.atr_1h:,.0f}` | **4H ATR**: `${sig.atr_4h:,.0f}` | **Recent Reclaim Candle**: `{sig.is_reclaim_candle}`",

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



    f_ev = getattr(store, "footprint_evaluation", None)
    if f_ev is not None:
        if f_ev.delta_flipped_bullish:
            flip_str = "BULLISH FLIP CONFIRMED (Prev < 0 -> Active > 0)"
        elif getattr(f_ev, "delta_flipped_bearish", False):
            flip_str = "BEARISH FLIP CONFIRMED (Prev > 0 -> Active < 0)"
        else:
            flip_str = "PENDING / NO FLIP"
        g2_detail_str = f_ev.gate2_detail if f_ev.gate2_detail else "Awaiting key structural level tap"
        lines.extend([
            "",
            "### 2C. 15-Minute Intra-Candle Footprint ($25 Tick Ladder & 3-Gate Microstructure)",
            "",
            f"* **Active 15m Forming Bar Delta**: `{f_ev.active_bar_delta:+,.2f} BTC` | **Preceding Bar Delta**: `{f_ev.prev_bar_delta:+,.2f} BTC`",
            f"* **15m Delta Flip**: `{flip_str}`",
            (f"* **Gate 1 (Key Level Tap)**: `PASS` ({f_ev.gate1_tapped_level_name} at `${f_ev.gate1_tapped_level_price:,.0f}` [{f_ev.gate1_level_type}])" if f_ev.gate1_level_tap else "* **Gate 1 (Key Level Tap)**: `PENDING` (Monitoring Support: 30D/7D cVAL, cPOC, HVN | Resistance: cVAH, Range High)"),
            f"* **Gate 2 (Footprint Absorption / Exhaustion)**: `{'PASS' if f_ev.gate2_absorption else 'PENDING'}` ({g2_detail_str})",
            f"* **Gate 3 (Delta Flip / Expansion)**: `{'PASS' if f_ev.gate3_delta_flip else 'PENDING'}`",
            f"* **Footprint Execution Status**: `{f_ev.signal_status}` (`Direction: {f_ev.direction}` | `All 3 Gates Pass: {f_ev.all_gates_pass}`)",
        ])
        if f_ev.direction == "DISTRIBUTE_SELL" and f_ev.all_gates_pass:
            lines.append(
                f"* **Triggered Spot Profit Harvest (Rotate to USDT)**: Action: Sell Spot BTC at `${f_ev.entry_price:,.2f}` ({f_ev.harvest_tranche_pct:.0f}% Staged Trim) | Invalidation Stop: `${f_ev.stop_loss:,.2f}` (Above Upper Wick) | Rebuy Target: `${f_ev.rebuy_target_price:,.0f}` ({f_ev.rebuy_target_name}) [Target Yield: +{f_ev.target_coin_yield_pct:.1f}% BTC Coin Accumulation]"
            )
        elif f_ev.all_gates_pass:
            lines.append(
                f"* **Triggered Spot Swing Plan**: Entry: `${f_ev.entry_price:,.2f}` | Stop Loss: `${f_ev.stop_loss:,.2f}` (Below Wick) | TP1 (1:2 R:R): `${f_ev.tp1_1to2:,.2f}` | TP2 (1:3 R:R): `${f_ev.tp2_1to3:,.2f}`"
            )
        if f_ev.active_ladder_rows:
            lines.extend([
                "",
                "| Bid Volume (BTC) | Price Bin ($25) | Ask Volume (BTC) | Cluster Delta (BTC) | Microstructure Signatures |",
                "| :--- | :--- | :--- | :--- | :--- |",
            ])
            for r in f_ev.active_ladder_rows:
                lines.append(
                    f"| `{r.bid_vol:,.2f}` | `${r.price:,.0f}` | `{r.ask_vol:,.2f}` | `{r.delta:+,.2f}` | `{r.tag or '-'}` |"
                )


    if pev is not None:
        comp_1d_rel = "Completed 1D Close >= Open" if pev.completed_1d_close >= pev.completed_1d_open else "Completed 1D Close < Open"
        lines.extend([

            "",

            "---",

            "",

            "## SECTION 3: PROTOCOL v1.3, COINGLASS 6-PANEL (BTC) & LIQUIDATION MAGNETS (TAB [2] RAW METRICS)",

            "",

            "### 3A. Daily Completed `[-2]` vs. Forming `[-1]` & ATR 14 Reference Bounds",

            f"* **1D Completed Candle `[-2]` (Closed)**: Open `${pev.completed_1d_open:,.2f}` • High `${pev.completed_1d_high:,.2f}` • Low `${pev.completed_1d_low:,.2f}` • Close `${pev.completed_1d_close:,.2f}` (`{pev.completed_1d_change_pct:+.2f}%`)",

            f"* **1D Forming Candle `[-1]` (Live)**: Open `${pev.forming_1d_open:,.2f}` • High `${pev.forming_1d_high:,.2f}` • Low `${pev.forming_1d_low:,.2f}` • Close `${pev.forming_1d_close:,.2f}` (`{pev.forming_1d_change_pct:+.2f}%`)",

            f"* **1D Support / Resistance**: Support `${pev.daily_support:,.0f}` • Resistance `${pev.daily_resistance:,.0f}` • **Daily Candlestick Bias (Single 1D Bar)**: `{pev.daily_bias}` ({comp_1d_rel}) • **4H Structure**: `{pev.structure_4h}` (`4H Ready: {pev.timing_4h_ready}`)",

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

            "## SECTION 6: PYTHON ENGINE BENCHMARK VERDICT (TAB [L] SUPREME COMMAND CENTER 9-DESK MIRROR)",

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

            f"| **Lens A** | Constant-Velocity Kalman Filter | Latent Price: `${mm_ev.kalman.filtered_price:,.2f}` (Spot `{mm_ev.kalman.distance_pct:+.2f}%` vs Latent) | Velocity: `{mm_ev.kalman.velocity:+,.2f} $/hr` | State: `{mm_ev.kalman.velocity_state}` • Bias: `{mm_ev.kalman.bias}` |",

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

            f"* **Telegram Delivery**: Bot: `{gartley.telegram_bot}` | Chat ID: `[REDACTED]` | Schedule: `{gartley.schedule_cron}`",

            f"* **Webhook Bridge**: `[REDACTED — Secure Cloud Bridge Active]` (Google Apps Script /now trigger)",

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

        ])

        if trap.liquidation_report and trap.liquidation_report.is_available:

            lr = trap.liquidation_report

            w24 = lr.windows.get("24h")

            w24_tot = w24.total_usd if w24 else 0.0

            w24_long = w24.long_usd if w24 else 0.0

            ps = lr.post_flush_price_structure

            ps_desc = ps.status if ps else "N/A"
            is_sub_threshold = lr.liquidation_multiple_24h < 0.50
            dir_note = f"{lr.directional_classification} [Sub-Threshold Quiet Baseline — No Active Cascade]" if is_sub_threshold else lr.directional_classification
            ps_note = f"{ps_desc} [Baseline Noise — Q={lr.liquidation_multiple_24h:.2f}x < 0.50x Flush Threshold]" if is_sub_threshold else ps_desc

            lines.extend([

                f"* **Binance ForceOrder Liquidation Telemetry**: Verdict: `{lr.verdict}` | Direction: `{dir_note}` | Magnitude: `{lr.magnitude_tier}`",

                f"* **Liquidation Volume & Multiple**: 24H Total: `${w24_tot/1e6:.2f}M` (Longs: `${w24_long/1e6:.2f}M`) | **`{lr.liquidation_multiple_24h:.2f}x` Daily Baseline Multiple (Q)**",

                f"* **Post-Flush Price Structure**: `{ps_note}` (Stabilization Confirmed: `{ps.stabilisation_confirmed if ps else False}` • Higher Low: `{ps.higher_low_formed if ps else False}`)",

            ])

        lines.extend([

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

        ])

        if ex.tell_tale and ex.tell_tale.bar_15m:

            tt = ex.tell_tale

            b15 = tt.bar_15m

            b5_str = f" • 5m RelVol: `{tt.bar_5m.relvol:.1f}x`" if tt.bar_5m else ""

            lines.extend([

                f"* **Tell-Tale Volume Climax Sensor**: Status: `{tt.plain_status}` | Disruption Detected: **`{tt.disruption_detected}`**",

                f"* **Tell-Tale Metrics**: 15m RelVol: `{b15.relvol:.1f}x` (Threshold >=5.0x){b5_str} | 15m Body/Range: `{b15.body_range:.2f}` (Threshold >=0.65)",

            ])

        lines.extend([

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



    dossier = compute_protocol_metrics_dossier(config, store, store.macro_intermarket)
    store.protocol_dossier = dossier



    dossier_text = format_protocol_metrics_dossier_markdown(dossier)

    lines.extend([

        "",

        dossier_text.strip(),

    ])




    # --- SECTION 13: TAB [P] PRICE ACTION & STRUCTURE PROTOCOL ---
    slsp = getattr(store, "slsp_evaluation", None)
    if slsp is not None:
        setup = slsp.active_setup
        ema_snap = store.ema_strategy
        trap_eval = store.trap_evaluation
        exhaust_eval = store.exhaustion_evaluation
        tt_eval = exhaust_eval.tell_tale if exhaust_eval else None
        liq_rep = getattr(slsp, "liq_detector_report", None) or getattr(store, "liquidation_report", None)
        if liq_rep is None:
            try:
                from analytics.liquidation_reader import read_latest_liquidation_report
                liq_rep = read_latest_liquidation_report()
            except Exception:
                liq_rep = None

        macro_lock_str = f" | **Macro Hard-Lock**: `LOCKED 100% CASH` ({slsp.macro_lock_reason})" if slsp.macro_hard_lock_cash else ""
        lines.extend([
            "",
            "---",
            "",
            "## SECTION 13: TAB [P] PRICE ACTION & STRUCTURE PROTOCOL (SLSP v1.0, INDUSTRIAL 3-EMA, BTC LIQUIDATION FLUSH & TELL-TALE CLIMAX)",
            "",
            "> [!NOTE]",
            "> **THE 4-PILLAR PRICE ACTION & STRUCTURE CONFLUENCE LAW**",
            "> Integrates File A (SLSP v1.0 swing structure and 1.5R obstacle law), File B (Industrial 3-EMA 200D slope anchor and 4H value zone), Project 8 (BTC Liquidation Flush Detector cascade lifecycle, gravitational depth and LSCE sweep machine), and Project 7 (Tell-Tale 5.0x volume capitulation climax first-shock alarm).",
            "",
            f"* **Step 1 Macro Regime Radar**: **`{slsp.macro_regime_name}`** (`{slsp.macro_regime_score}` Confirmed) | Diagnosis: `{slsp.macro_regime_diagnosis}` | Macro Sizing: `{slsp.macro_sizing_factor:.2f}x` ({slsp.macro_rotation}){macro_lock_str}",
            f"* **Desk [P] Trade State**: **`{slsp.trade_state}`** | **Confluence Score**: **`{slsp.confluence_score}/100`** | **Bias**: **`{slsp.regime}`** | **Mode**: **`{slsp.mode}`**",
            f"* **Executive Bottomline Summary**: {slsp.plain_english_summary}",
            "",
            "### 13A. Panel [1] File A: SLSP v1.0 Structure + Level Swing Protocol",
            f"* **Daily Market Regime**: `{slsp.regime}` ({slsp.regime_reason or 'Intact swing pivots'})",
        ])

        if slsp.nearest_support:
            supp = slsp.nearest_support
            dist_s = ((atomic_spot_price - supp.center_price) / supp.center_price) * 100.0 if atomic_spot_price else 0.0
            round_txt = "Yes" if supp.is_round_number else "No"
            hvn_txt = "Yes" if supp.is_hvn else "No"
            liq_tag_s = f" | Liquidation Pool: `{supp.liquidation_cluster_tag}` (${supp.liquidation_volume_usd/1e6:.1f}M)" if supp.liquidation_cluster_tag else ""
            lines.append(
                f"* **Nearest Key Support Shelf**: `${supp.center_price:,.2f}` (Range: `${supp.price_min:,.0f}–${supp.price_max:,.0f}` | Distance: `{dist_s:+.2f}%` | Strength: `{supp.strength}/5★` | Touches: `{supp.touch_count}x` | Round Number: `{round_txt}` | HVN: `{hvn_txt}`{liq_tag_s})"
            )
        else:
            lines.append("* **Nearest Key Support Shelf**: None within 10% (Scanning swing pivots)")

        if slsp.nearest_resistance:
            res = slsp.nearest_resistance
            dist_r = ((res.center_price - atomic_spot_price) / atomic_spot_price) * 100.0 if atomic_spot_price else 0.0
            liq_tag_r = f" | Liquidation Pool: `{res.liquidation_cluster_tag}` (${res.liquidation_volume_usd/1e6:.1f}M)" if res.liquidation_cluster_tag else ""
            lines.append(
                f"* **Nearest Key Resistance Shelf**: `${res.center_price:,.2f}` (Range: `${res.price_min:,.0f}–${res.price_max:,.0f}` | Distance: `{dist_r:+.2f}%` overhead | Strength: `{res.strength}/5★` | Touches: `{res.touch_count}x`{liq_tag_r})"
            )
        else:
            lines.append("* **Nearest Key Resistance Shelf**: Blue Sky / Clear Path (No major daily resistance within 10%)")

        if setup:
            obs_flag = "OBSTACLE DETECTED (VETO)" if setup.obstacle_detected else "CLEAR RUNWAY"
            lines.extend([
                f"* **1.5R Runway Obstacle Check**: `{setup.obstacle_r:.2f}R` clearance to resistance | Status: **`{obs_flag}`** ({setup.obstacle_description})",
                f"* **4H Candlestick Rejection**: Type: `{setup.rejection_candle_type}` (Lower Wick Ratio: `{setup.rejection_wick_ratio*100:.1f}%`) | 4H Volume vs 20 SMA: `{setup.rejection_volume_ratio:.2f}x`",
                f"* **Macro Sizing & Risk Allocation**: Sized: `{setup.position_size_btc:.4f} BTC` (`${setup.notional_value_usd:,.2f}` notional | Macro Factor: `{slsp.macro_sizing_factor:.2f}x` | Zero Leverage Spot) | Max Risk: `${100000.0 * (setup.risk_pct/100):,.2f}`",
                f"* **Execution Geometry & Dual Stops**: Entry: `${setup.entry_price:,.2f}` | Structural Stop (1H Close): `${slsp.structural_stop_price:,.2f}` ({slsp.structural_stop_dist_pct:.2f}%) | Disaster Hard Stop (Below 200 SMA & 25x Shelf): `${slsp.disaster_stop_price:,.2f}` ({slsp.disaster_stop_dist_pct:.2f}%) | Risk Budget Pass: `{bool(slsp.disaster_stop_dist_pct <= 4.5)}` | TP1 (+1.5R): `${setup.tp1_price:,.2f}` | TP2 (+2.5R): `${setup.tp2_price:,.2f}` | Breakeven Ratchet (+1.0R): `${setup.breakeven_trigger_price:,.2f}`",
            ])
        else:
            lines.append("* **Active Setup Parameters**: Scanning for structural touch and 4H rejection candle")

        cb_stat = "ACTIVE LOCKOUT" if slsp.circuit_breaker_active else "PASS"
        d_200 = f"${ema_snap.daily_ema_200:,.2f}" if ema_snap else "N/A"
        d_20 = f"${ema_snap.daily_ema_20:,.2f}" if ema_snap else "N/A"
        d_50 = f"${ema_snap.daily_ema_50:,.2f}" if ema_snap else "N/A"
        vz_band = f"${ema_snap.ema_4h_20:,.0f}–${ema_snap.ema_4h_50:,.0f}" if ema_snap else "N/A"
        trig_9 = f"${ema_snap.ema_4h_9:,.2f}" if ema_snap else "N/A"
        rej_act = ema_snap.rejection_active if ema_snap else False
        trig_act = ema_snap.trigger_active if ema_snap else False

        lines.extend([
            f"* **Portfolio Circuit Breakers**: Daily Loss: `{slsp.daily_loss_pct:.2f}%` (Limit: 2.0%) | Weekly Loss: `{slsp.weekly_loss_pct:.2f}%` (Limit: 4.0%) | Status: **`{cb_stat}`** ({slsp.circuit_breaker_reason or 'Within risk caps'})",
            "",
            "### 13B. Panel [2] File B: Industrial 3-EMA Trading Strategy",
            f"* **Daily 200 EMA Macro Anchor**: 200 EMA Price: `{d_200}` | 5-Day Slope: `{slsp.ema_3_slope_200:+.3f}%/5d` (Threshold: ±0.05%) | Macro Bias: **`{slsp.ema_3_regime}`**",
            f"* **Daily EMAs & Trend Quality**: 20 EMA: `{d_20}` | 50 EMA: `{d_50}` | ADX(14): `{slsp.ema_3_adx:.1f}` ({'TREND >=20.0' if slsp.ema_3_adx >= 20.0 else 'CHOP / FLAT <20.0'})",
            f"* **4H Dynamic Value Band**: 21–50 EMA Range: `{vz_band}` | In Value Band: **`{slsp.ema_3_value_zone_active}`**",
            f"* **Candlestick Rejection Memory**: Rejection in last 3 closed 4H bars: **`{rej_act}`**",
            f"* **Positioning Confluence**: `{slsp.ema_3_positioning_met}/3 Confirmations Met` (OI contraction, Funding <=0.01%, Spot CVD absorption)",
            f"* **4H Trigger EMA**: 9 EMA Level: `{trig_9}` | Trigger Active: **`{trig_act}`**",
            "",
            "### 13C. Panel [3] Project 8: BTC Liquidation Flush Detector",
        ])

        if liq_rep:
            w15 = liq_rep.windows.get("15m")
            w1h = liq_rep.windows.get("1h")
            w4h = liq_rep.windows.get("4h")
            w24h = liq_rep.windows.get("24h")
            t15 = f"${w15.total_usd:,.0f}" if w15 else "$0"
            t1h = f"${w1h.total_usd:,.0f}" if w1h else "$0"
            t4h = f"${w4h.total_usd:,.0f}" if w4h else "$0"
            t24h = f"${w24h.total_usd:,.0f}" if w24h else "$0"
            lines.extend([
                f"* **Liquidation Horizon & Depth Ladder**: Dominant Pull: **`{slsp.dominant_pull_dir}`** | Imbalance Ratios: Immediate (100x): `{slsp.immediate_ratio:.2f}x`, Total Ladder (10x-100x): `{slsp.total_ladder_ratio:.2f}x`",
                f"* **Liquidation Magnet Pools**: Upper (Shorts): `${slsp.upper_magnet_price:,.2f}` ({slsp.upper_magnet_dist_pct:+.2f}%, `${slsp.upper_magnet_vol_usd / 1e6:.1f}M`) | Lower (Longs): `${slsp.lower_magnet_price:,.2f}` ({slsp.lower_magnet_dist_pct:+.2f}%, `${slsp.lower_magnet_vol_usd / 1e6:.1f}M`)",
                f"* **LSCE Sweep State Machine**: Status: **`[{slsp.lsce_status}]`** | Tested: `{slsp.lsce_cluster_tested}` | Action Verdict: {slsp.lsce_action_verdict}",
                f"* **Crash Lifecycle Stage**: **`{liq_rep.verdict}`** (`{liq_rep.primary_classification}`) | Detail: {liq_rep.verdict_detail}",
                f"* **Damage So Far ($ Liquidated)**: 15m: `{t15}` | 1h: `{t1h}` | 4h: `{t4h}` | 24h: `{t24h}` | Magnitude Tier: **`{liq_rep.magnitude_tier}`** (24h Multiple: `{liq_rep.liquidation_multiple_24h:.2f}x`)",
                f"* **Leverage Wipeout Telemetry**: Open Interest: `{liq_rep.open_interest_contracts:,.0f} contracts` | 1H dOI: `{slsp.liq_flush_oi_delta:+.2f}%` | Funding Rate: `{liq_rep.funding_rate*100:+.4f}%` ({liq_rep.funding_status})",
                f"* **Key Demand Zone Analysis ($75k–$78k)**: Status: **`{liq_rep.demand_zone_status}`** (`${liq_rep.demand_zone_lower:,.0f}–${liq_rep.demand_zone_upper:,.0f}`) | Distance to Floor: `{liq_rep.demand_zone_dist_lower_pct:+.2f}%` | Distance to Ceiling: `{liq_rep.demand_zone_dist_upper_pct:+.2f}%`",
            ])
            if liq_rep.post_flush_price_structure:
                pf = liq_rep.post_flush_price_structure
                lines.append(
                    f"* **Post-Flush Price Structure**: Status: `{pf.status}` | Higher Low Formed: **`{pf.higher_low_formed}`** | Lower Lows Stopped: **`{pf.stopped_making_lower_lows}`** | Spot Volume Ratio: `{pf.volume_ratio:.2f}x` 20MA"
                )
        else:
            lines.append("* **Liquidation Detector Feed**: Companion detector standby / offline")

        lines.extend([
            "",
            "### 13D. Panel [4] Project 7: Tell-Tale Volume Capitulation Climax Sensor",
            f"* **Sensor Mission**: First-Shock Early Warning Alarm & Anti-Knife-Catch Interlock",
            f"* **Disruption Status**: `{slsp.tell_tale_status}` | Long Veto Active: **`{slsp.tell_tale_veto}`**",
            f"* **15-Minute Candle Microstructure**: RelVol: `{slsp.tell_tale_relvol_15m:.1f}x` vs 20-period baseline (Threshold: >=5.0x)",
            f"* **5-Minute Candle Microstructure**: RelVol: `{slsp.tell_tale_relvol_5m:.1f}x` vs 20-period baseline (Threshold: >=5.0x)",
            f"* **Anti-Knife-Catch Guard Interlock**: **`{'🚨 HARD VETO: LOCKOUT ALL LONGS' if slsp.tell_tale_veto else '✓ CLEAR TO TRADE (Order Flow Stable)'}`**",
            "",
            "### 13E. Panel [5] Executive Alignment & Beginner Action Playbook",
            f"* **Current Direct Directive**: **`{slsp.trade_state}`**",
            f"* **4-Pillar Alignment Status**: SLSP Support: `{'✓' if slsp.nearest_support and slsp.nearest_support.strength >= 3 else '○'}` | 1.5R Runway: `{'✓' if (setup and not setup.obstacle_detected) else '✗'}` | 3-EMA Value Band: `{'✓' if slsp.ema_3_value_zone_active else '○'}` | Liq Stable: `{'✓' if (liq_rep and liq_rep.magnitude_tier == 'NORMAL') else '⚠️'}` | Tell-Tale Pass: `{'✓' if not slsp.tell_tale_veto else '✗'}`",
        ])
    else:
        lines.extend([
            "",
            "---",
            "",
            "## SECTION 13: TAB [P] PRICE ACTION & STRUCTURE PROTOCOL (SLSP v1.0, INDUSTRIAL 3-EMA, BTC LIQUIDATION FLUSH & TELL-TALE CLIMAX)",
            "",
            "> [!NOTE]",
            "> **THE 4-PILLAR PRICE ACTION & STRUCTURE CONFLUENCE LAW**",
            "> Integrates File A (SLSP v1.0 swing structure and 1.5R obstacle law), File B (Industrial 3-EMA 200D slope anchor and 4H value zone), Project 8 (BTC Liquidation Flush Detector cascade lifecycle and $75k–$78k demand zone), and Project 7 (Tell-Tale 5.0x volume capitulation climax first-shock alarm).",
            "",
            "* **Desk [P] Trade State**: `WARMING_UP / INITIALIZING`",
            "* **Status**: Engine initializing higher-timeframe swing pivots, 4H rejection candles, and liquidation sensor streams.",
        ])

    # --- SECTION 15: TAB [G] GROK DUAL-HORIZON FLOW & VWAP SD MATRIX ---
    grok = getattr(store, "grok_quant_evaluation", None)
    if grok is None:
        try:
            from analytics.grok_quant_engine import GrokQuantEngine
            grok = GrokQuantEngine().evaluate(store)
        except Exception:
            grok = None

    if grok is not None:
        lines.extend([
            "",
            "---",
            "",
            "## SECTION 15: TAB [G] GROK DUAL-HORIZON FLOW & 00:00 UTC ANCHORED VWAP SD MATRIX",
            "",
            f"* **00:00 UTC Anchored VWAP**: `${grok.vwap_daily:,.2f}` | **Stretch Z-Score**: `{grok.vwap_stretch_z:+.2f}σ` (`{grok.vwap_band_status}`)",
            f"* **VWAP Dispersion (1σ / 2σ)**: `+2.0σ: ${grok.vwap_sd2_upper:,.2f}` | `+1.0σ: ${grok.vwap_sd1_upper:,.2f}` | `-1.0σ: ${grok.vwap_sd1_lower:,.2f}` | `-2.0σ: ${grok.vwap_sd2_lower:,.2f}`",
            f"* **CoinGlass Crowding & Positioning**: Top Traders `{grok.top_trader_ls_ratio:.2f}` ({grok.top_trader_long_pct}% L) vs Retail Accounts `{grok.global_account_ls_ratio:.2f}` (`{grok.crowding_verdict}`)",
            f"* **Coinbase Premium Index**: `${grok.coinbase_premium_usd:+,.2f}` (`{grok.coinbase_premium_pct:+.4f}%`, Z=`{grok.coinbase_premium_zscore:+.2f}σ`, `{grok.coinbase_premium_status}`)",
            f"* **Multi-Horizon CVD Divergence**: 24H Spot `{grok.spot_cvd_24h:+,.1f} BTC` vs Perp `{grok.futures_cvd_24h:+,.1f} BTC` (`{grok.cvd_divergence}`) | 4H Spot `{grok.spot_cvd_4h:+,.1f} BTC` | 15m Spot `{grok.spot_cvd_15m:+,.1f} BTC`",
            f"* **Liquidation Pool Magnets**: Overhead Short Magnet `${grok.overhead_short_liq_pool:,.0f}` (~${grok.overhead_short_liq_usd/1e6:.0f}M) vs Downside Long Trap `${grok.downside_long_liq_pool:,.0f}` (~${grok.downside_long_liq_usd/1e6:.0f}M)",
            f"* **4A. Swing Context (Daily/4H)**: {grok.mechanical_read_swing}",
            f"* **4B. Day Context (1H/15m)**: {grok.mechanical_read_day}",
            f"* **Engine Bottomline Verdict**: `{grok.bottomline_verdict}`",
            f"  * **Rationale**: {grok.bottomline_rationale}",
            f"  * **Trigger to Buy**: {grok.bottomline_buy_trigger}",
            f"  * **Invalidation Risk**: {grok.bottomline_invalidation_risk}",
        ])

    # --- SECTION 16: TAB [R] SSRN QUANTITATIVE ALPHA DECK & EMPIRICAL RESEARCH ---
    ssrn = getattr(store, "ssrn_alpha_evaluation", None)
    if ssrn is None:
        try:
            from analytics.ssrn_research_engine import SSRNResearchEngine
            ssrn = SSRNResearchEngine().evaluate(store)
        except Exception:
            ssrn = None

    if ssrn is not None:
        lines.extend([
            "",
            "---",
            "",
            "## SECTION 16: TAB [R] SSRN QUANTITATIVE ALPHA DECK & EMPIRICAL RESEARCH",
            "",
            "### 16A. 5 Academic Empirical Domains (Theoretical Foundation)",
        ])
        for d in ssrn.domains:
            lines.append(f"* **{d.title}**: {d.key_finding} | *Spot Swing Role:* `{d.spot_swing_role}`")

        lines.extend([
            "",
            "### 16B. 5 Verified Operational Strategy Models & Live Gate Status",
        ])
        for m in ssrn.models:
            gate_badge = "PASS" if m.is_gate_pass else "RESTRICTED"
            lines.append(
                f"* **{m.name}** (`{m.ssrn_citation}` • `{m.timeframe}`): {m.logic} | "
                f"**Benchmark:** `{m.performance}` | **Live Condition:** `[{gate_badge}: {m.live_status}]` ({m.live_value})"
            )


    # --- SECTION 17: TAB [M] BTC MAGNET — LIQUIDATION GRAVITY & SWING EDGE DETECTOR ---
    magnet = getattr(store, "btc_magnet_evaluation", None)
    if magnet is None:
        try:
            from analytics.btc_magnet_engine import BTCMagnetEngine
            magnet = BTCMagnetEngine(config).evaluate(store)
        except Exception:
            magnet = None

    if magnet is not None:
        lines.extend([
            "",
            "---",
            "",
            "## SECTION 17: TAB [M] BTC MAGNET — LIQUIDATION GRAVITY & SWING EDGE DETECTOR",
            "",
            f"* **Mechanical Status Verdict**: `[{magnet.verdict_badge}]`",
            f"* **Status Headline**: {magnet.headline}",
            f"* **Explanation Readout**: {magnet.body}",
            f"* **Rule Subtitle**: *{magnet.rule_subtitle}*",
            "",
            f"* **5-Regime Radar**: `{getattr(magnet, 'regime_name', 'Range / Liquidation Magnet')}` (`{getattr(magnet, 'majority_score', '3/4')}` confirmed)",
            f"* **Regime Diagnosis**: {getattr(magnet, 'regime_diagnosis', '')}",
            f"* **Recommended Sizing**: `{getattr(magnet, 'sizing_factor', 0.0):.2f}x` ({getattr(magnet, 'action', '')}) | Rotation: `{getattr(magnet, 'rotation', 'Remain USDT')}`",
            f"* **LSCE Sweep State**: `[{getattr(magnet, 'lsce_status', 'UNTESTED')}]` — {getattr(magnet, 'lsce_action_verdict', '')}",
            f"* **Dual Stops**: Structural `${getattr(magnet, 'structural_stop_price', 0.0):,.2f}` | Disaster Hard Stop `${getattr(magnet, 'disaster_stop_price', 0.0):,.2f}` (-{getattr(magnet, 'disaster_stop_dist_pct', 0.0):.2f}%)",
            "",
            "### 17A. Liquidation Gravitational Horizon",
            f"* **Upper Magnet (Short Liquidations)**: `${magnet.upper_magnet.price:,.0f}` (`{magnet.upper_magnet.dist_pct:+.1f}%`) — `${magnet.upper_magnet.usd_volume/1e6:.1f}M` cluster",
            f"* **Center Spot Horizon**: `${magnet.spot_price:,.2f}` (`{magnet.price_change_24h_pct:+.2f}% 24h`)",
            f"* **Lower Support (Long Liquidations)**: `${magnet.lower_magnet.price:,.0f}` (`{magnet.lower_magnet.dist_pct:+.1f}%`) — `${magnet.lower_magnet.usd_volume/1e6:.1f}M` cluster",
            f"* **Gravitational Pull**: `{magnet.pull_direction} MAGNET` (Immediate 100x: `{getattr(magnet, 'immediate_ratio', 1.0):.1f}x` | Total Ladder: `{getattr(magnet, 'total_ladder_ratio', 1.0):.2f}x`)",
            f"* **Perpetual Funding**: `{magnet.funding_rate_annual_pct:+.1f}%/yr` | **4h OI Velocity**: `{magnet.oi_delta_4h_pct:+.1f}%` | **Regime**: `{magnet.market_regime}`",
            "",
            "### 17B. 7 Internal Speaking Rules Audit",
        ])
        for r in magnet.rule_checks:
            badge = "PASS" if r.passed else "WAIT"
            lines.append(f"* **Rule {r.rule_num} ({r.name})**: `[{badge}]` {r.detail}")

    # --- SECTION 18: TAB [A] BTC TREND-PULLBACK v1.0 · RESEARCH / PAPER MODE ---
    tp_ev = getattr(store, "trend_pullback_evaluation", None)
    if tp_ev is None:
        try:
            from analytics.strategy_trend_pullback import TrendPullbackEngine
            tp_ev = TrendPullbackEngine(config).evaluate(store)
        except Exception:
            tp_ev = None

    if tp_ev is not None:
        lines.extend([
            "",
            "---",
            "",
            "## SECTION 18: TAB [A] BTC TREND-PULLBACK v1.0 · DATA-ONLY METRICS REPORT",
            "",
            f"* **Strategy Name**: `{tp_ev.strategy_name}` | **Mode**: `{tp_ev.mode_label}` | **Status**: `{tp_ev.strategy_status}`",
            f"* **Spot BTCUSDT**: `${tp_ev.spot_price:,.2f}` | **Retrieval (MYT)**: `{tp_ev.timestamp_myt}` | **Retrieval (UTC)**: `{tp_ev.timestamp_utc}`",
            f"* **1. Daily (1D)**: `Open {tp_ev.daily_open_time_utc} -> Close {tp_ev.daily_close_time_utc}` | `1D Close ${tp_ev.daily_close_completed:,.2f}` | `SMA50 ${tp_ev.daily_sma50:,.2f}` | `SMA200 ${tp_ev.daily_sma200:,.2f}` | `20D Slope ${tp_ev.daily_sma200_slope_20d:+,.2f}` | `Close vs SMA200: ${tp_ev.daily_close_vs_sma200_usd:+,.2f} ({tp_ev.daily_close_vs_sma200_pct:+.2f}%)` | `Close > SMA200: {tp_ev.daily_close_above_sma200}` | `Close > SMA50: {tp_ev.daily_close_above_sma50}` | `SMA200 Rising: {tp_ev.daily_sma200_rising}`",
            f"* **2. 4H Trend**: `Open {tp_ev.candle_4h_open_time_utc} -> Close {tp_ev.candle_4h_close_time_utc}` | `4H Close ${tp_ev.close_4h_completed:,.2f}` | `EMA50 ${tp_ev.ema50_4h:,.2f}` | `EMA200 ${tp_ev.ema200_4h:,.2f}` | `ATR14 ${tp_ev.atr14_4h:,.2f}` | `6-Bar Slope ${tp_ev.ema50_4h_slope_6bars:+,.2f}` | `EMA50 > EMA200: {tp_ev.ema50_above_ema200}` | `EMA50 Rising 6B: {tp_ev.ema50_rising_6bars}` | `Close > EMA200: {tp_ev.close_4h_above_ema200}`",
            f"* **3. Pullback Zone**: `Lower ${tp_ev.pullback_zone_lower:,.2f}` | `Upper ${tp_ev.pullback_zone_upper:,.2f}` | `Max Ext ${tp_ev.max_extension_price:,.2f}` | `Spot Minus Lower ${tp_ev.spot_minus_zone_lower_usd:+,.2f} ({tp_ev.spot_minus_zone_lower_atr:+.4f} ATR)` | `Low < Zone Lower: {tp_ev.candle_4h_low_below_zone_lower}` | `All 5 Recovery Conditions Met: {tp_ev.rec_all_conditions_met}`",
            f"* **4. Reference Levels (`Reference calculation if entered at ${tp_ev.sizing_entry_price:,.2f}. Not an order.`)**: `Ref Entry ${tp_ev.sizing_entry_price:,.2f}` | `Stop ${tp_ev.structural_stop:,.2f}` | `Stop Distance ${tp_ev.stop_distance_usd:,.2f} ({tp_ev.stop_distance_atr:.2f} ATR / exact {tp_ev.stop_distance_atr_exact:.4f} ATR)` | `Budget ${tp_ev.risk_budget_usd:,.2f}` | `Size {tp_ev.position_size_btc:.5f} BTC (${tp_ev.position_value_usd:,.2f})` | `Computed Price Risk ${tp_ev.gross_price_risk_usd:,.2f} + Fee/Slippage Buffer ${tp_ev.fee_slippage_buffer_usd:,.2f} = ${tp_ev.total_estimated_risk_usd:,.2f}` | `Spot to Ref Entry ${tp_ev.spot_to_ref_entry_usd:+,.2f} ({tp_ev.spot_to_ref_entry_pct:+.2f}%)`",
            f"* **5. Exit Rule Inputs**: `Position {tp_ev.position_status}` | `Consecutive 4H Closes < EMA50: {tp_ev.consecutive_4h_closes_below_ema50}` | `Consecutive 1D Closes < SMA200: {tp_ev.consecutive_1d_closes_below_sma200}`",
            f"* **6. Data Integrity**: `Data Integrity OK: {tp_ev.data_integrity_ok}` (`1D Count: {tp_ev.completed_1d_count}` [Forming Excl: `{tp_ev.daily_forming_excluded}`] • `4H Count: {tp_ev.completed_4h_count}` [Forming Excl: `{tp_ev.candle_4h_forming_excluded}`])",
        ])

    return "\n".join(lines) + "\n"





def copy_ai_packet_to_clipboard_and_disk(config: EngineConfig, store: StateStore) -> Tuple[bool, str, int]:

    """Builds the DATA-ONLY AI telemetry packet, copies it to the clipboard, and writes it to Downloads & logs/."""
    from analytics.data_only_reports import build_global_data_only_packet

    packet_text = build_global_data_only_packet(config, store)

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



    # 1b. Export structured telemetry metrics to btc_metrics_latest.json (Section 6 Specification)

    f_ev = getattr(store, "footprint_evaluation", None)
    if f_ev is None and hasattr(store, "footprint_engine") and store.footprint_engine is not None:
        try:
            f_ev = store.footprint_engine.evaluate(store)
            store.footprint_evaluation = f_ev
        except Exception:
            pass

    if f_ev is not None:

        bar_poc_p = f_ev.current_price

        if hasattr(store, "footprint_engine") and store.footprint_engine and store.footprint_engine.active_bar:

            bar_poc_p = store.footprint_engine.active_bar.poc_price or f_ev.current_price

        footprint_metrics = {

            "order_flow": {

                "footprint": {

                    "active_bar_delta": round(f_ev.active_bar_delta, 2),

                    "bar_poc": round(bar_poc_p, 2),

                    "gate_1_macro_tap": bool(f_ev.gate1_macro_tap),

                    "gate_2_positioning_crowded": bool(f_ev.gate2_positioning_crowded),

                    "gate_3_wick_absorption": bool(f_ev.gate3_wick_absorption),

                    "gate_4_delta_flip": bool(f_ev.gate4_delta_flip),

                    "stacked_imbalances_count": int(f_ev.stacked_imbalances_count),

                    "active_battle_zone": round(f_ev.active_battle_zone, 2),

                    "signal": str(f_ev.signal_status),

                    "suggested_entry": round(f_ev.entry_price, 2),

                    "suggested_stop": round(f_ev.stop_loss, 2),

                    "target_1_to_2": round(f_ev.tp1_1to2, 2),

                }

            }

        }

        try:

            import json

            json_text = json.dumps(footprint_metrics, indent=2)

            pathlib.Path("btc_metrics_latest.json").write_text(json_text, encoding="utf-8")

            (log_file.parent / "btc_metrics_latest.json").write_text(json_text, encoding="utf-8")

            if downloads_dir.exists():

                (downloads_dir / "btc_metrics_latest.json").write_text(json_text, encoding="utf-8")

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

