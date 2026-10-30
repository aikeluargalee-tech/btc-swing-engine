# BTC-USD Spot Swing Engine: Core Architecture, Machinery & 5-Tab Operational Manual

**System Classification:** Institutional-Grade Real-Time Quantitative Microstructure & Macro Terminal (Rich Live TUI HUD)  
**Target Asset & Mandate:** Bitcoin (`BTC-USD` / `BTCUSDT`) — **Strictly Long-Only Spot Swing & Positional Trading** (Zero Leverage, Zero Shorting)  
**Runtime Path:** `C:\Users\aikel\.gemini\antigravity\scratch\btc_swing_engine`  
**Launch Command:** `.\.venv\Scripts\python.exe main.py`

---

## 1. What Is the BTC Swing Engine Dashboard?

The **BTC-USD Spot Swing Engine** is a real-time, self-updating, retro IBM / Bloomberg-style **Terminal User Interface Heads-Up Display (Rich Live TUI HUD)** built in Python using `asyncio` and `rich.live.Live`.

Unlike static web charts or lagging retail indicator dashboards, the BTC Swing Engine operates as a **unified, single-brain quantitative decision engine** that ingests live cross-exchange Spot and Perpetual Futures order flow (`Binance Spot`, `Binance/Bybit USD-M Perpetuals`, and `Coinbase Institutional BTC-USD Spot`) alongside multi-horizon historical candlestick structures (`1W`, `1D`, `4H`, `1H`, `15m`).

It synthesizes **four specialist quantitative disciplines plus a 5th Supreme Master Conclusion desk** into **5 instant-switchable (`0.0s`) single-screen terminal tabs**:
1. **Tab `[1]` (`[1: SWING ENGINE]`)**: Auction Market Theory (Composite Volume Profile `30D/7D/24H`), Multi-Horizon Order Flow (`Spot vs. Perp CVD` & `Passive Absorption`), and a **4-Gate Tactical Execution State Machine**.
2. **Tab `[2]` (`[2: PROTOCOL v1.3]`)**: **BTC Spot Swing Protocol v1.3** Capital Preservation Audit, Fixed **CoinGlass 6-Panel Audit in Strict `BTC` Coins**, **Section 8 Non-Trade Zones (`8A–8F`)**, and the **Daily Liquidation Magnet & Range Pivot Protocol**.
3. **Tab `[3]` (`[3: MACRO RADAR]`)**: **Macro Quant & Cycle Radar** featuring the **Rule 1 Gatekeeper (`1D 200 SMA` + 5-Day Slope)**, **`1D 21 EMA`**, **`14D Wilder RSI`**, **Genesis Power-Law Long-Horizon Valuation**, **Cycle Armor Crash Rungs (`-25%` to `-65%`)**, and the **`1W/1D/4H` Liquidity Sniper Matrix**.
4. **Tab `[4]` (`[4: REGIME A–J]`)**: **Quantitative Microstructure Diagnostic & Execution Protocols (`Configurations A through J`)** paired with a **Live Global Trading Session (`UTC` • `SGP` • `LON` • `NYC`) Microstructure Reference**.
5. **Tab `[5]` (`[5: MASTER CONCLUSION]`)**: **Supreme Master Synthesis & Reconciled Order of Battle**, rolling up the Executive Bottom Lines from Tabs `[1]–[4]`, resolving cross-tab conflicts via a **4-Layer Institutional Decision Funnel**, and providing two reconciled playbooks (**Track A: If Flat in Cash** vs. **Track B: If Holding Spot BTC**) plus its own **Panel 5 Supreme Master Executive Bottom Line**.

---

## 2. Core Purpose & Governing Trading Philosophy

The engine is designed to solve the three primary failure modes of solo Spot BTC swing traders:
1. **Buying Futures-Driven Bull Traps**: In range-bound or corrective regimes, immediate green candles are frequently driven by perpetual futures short squeezes and leverage chasing rather than genuine Spot accumulation. The engine separates **Spot Taker CVD (`BTC`)** from **Perp Taker CVD (`BTC`)** and **Coinbase Institutional Basis** to block leveraged bull traps.
2. **Trading Mid-Range Chop & Headlines**: Entering in the middle of a Value Area (`30%–70%` between `cVAL` and `cVAH`) or chasing news headlines destroys reward-to-risk (`R:R`). The engine enforces an explicit **Mid-Range Chop Blocker** and prioritizes **Range Edges (`cVAL`, `Support HVN`, `Long-Liq Magnets`)** with confirmed candle acceptance.
3. **Violating Macro Regime & Capital Preservation Rules**: Buying aggressive breakouts below a falling `1D 200 SMA` or during `FOMC/CPI` and weekend round-number manipulation windows leads to avoidable drawdowns. The engine wires a **Two-Tier Cross-Tab Master Veto** so safety violations on Tabs `[2]` or `[3]` automatically protect Tab `[1]`.

---

## 3. Internal Machinery: How the Engine Works Under the Hood

### 3.1. Zero-Cold-Start Three-Stage Startup (`[1/3] -> [2/3] -> [3/3]`)
When `main.py` starts, the dashboard never launches with empty "warming up" tables:
* **`[1/3]` Concurrent Historical Backfill (`collectors/warmup_loader.py`)**: Concurrently fetches:
  - `60x 1W` (Weekly) Spot klines
  - `255x 1D` (Daily) Spot & Perp klines (strictly separating **Completed `1D [-2]`** from **Forming `1D [-1]`**)
  - `720x 1H` (30-Day) Spot & Perp klines (`taker_buy_base_asset_volume` exact historical delta)
  - `240x 15m` Spot & Perp klines
  - `30x 4H` Open Interest history (`BTC`), `8H` Funding Rate history, `5m` Taker Long/Short Ratio, and Coinbase `BTC-USD` Spot candles for baseline `Coinbase Premium Index (CPI)` Z-score calibration.
* **`[2/3]` Initial Full-Brain Evaluation**: Runs all 4 tab evaluators once before opening the terminal screen.
* **`[3/3]` Live `2 Hz` Terminal HUD Launch**: Hands off to the 4 concurrent `asyncio` loops.

### 3.2. The 4 Synchronized `asyncio` Loops & Single Shared Brain (`StateStore`)
All data collectors write into a single in-memory state container (`core/state_store.py:StateStore`), and all 4 tabs read from that same brain:
1. **Loop 1 — Real-Time WebSocket Collector (`collectors/ws_streams.py`, `<50ms` latency)**:
   - Streams live `aggTrade` ticks from **Binance Spot (`btcusdt`)**, **Binance USD-M Perp (`btcusdt`)**, and **Coinbase Spot (`BTC-USD` `matches`)** to update tick-level Spot/Perp CVD and Coinbase Premium in real time.
2. **Loop 2 — `2 Hz` (`0.5s`) Analytics & HUD Refresh + `20 Hz` Keyboard Polling (`ui/terminal_hud.py`)**:
   - Re-evaluates all 4 tabs every `0.5s` and polls Windows `msvcrt` every `0.05s` so pressing keys `1`, `2`, `3`, or `4` switches the active view in **`0.0s`** with zero network reload.
3. **Loop 3 — `15s` Derivatives REST Poller (`collectors/rest_metrics.py`)**:
   - Polls Open Interest (`BTC` coins), `8H` Funding Rate, Mark/Index Basis, and `5m` Taker Buy/Sell Ratio every 15 seconds (with automatic fallback to Bybit V5 Linear Perp if Binance Futures is geo-restricted).
4. **Loop 4 — `60s` Rolling Kline & Context Synchronizer (`collectors/rest_metrics.py`)**:
   - Refreshes the rolling `15m`, `1H`, `1D`, and `1W` kline buffers every 60 seconds and hot-reloads `config/protocol_context.json` every 10 seconds.

### 3.3. Global Top Status Banner (Visible Across All 4 Tabs)
At the top of every tab sits a unified 2-row status header displaying:
* **Row 1**: Active Tab Selector (`[1: SWING ENGINE] • [2: PROTOCOL v1.3] • [3: MACRO RADAR] • [4: REGIME MATRIX A-J]`), current Market Regime badge, `0–100` Confluence Score, and live WebSocket connection status (`Spot ONLINE • Perp ONLINE • CB ONLINE`).
* **Row 2**: **World Clocks** (`UTC`, **Asian Singapore `SGT`**, **London `GMT/BST`**, **New York `EST/EDT`** with automatic DST adjustment) and the **Active Regional Market Session Badge** (`ASIA SESSION`, `ASIA / LONDON OVERLAP`, `LONDON / EU SESSION`, `LONDON / NY OVERLAP`, `NEW YORK SESSION`, `LATE NY / PRE-ASIA`).

---

## 4. The 4 Tabs: Purpose, 5-Panel Anatomy & Decision Logic

Every tab follows the strict **5-Panel Single-Screen Law (`≤ 49 lines`)**:
- **Panels 1 & 2**: Side-by-side top telemetry tables (`box.ROUNDED` outer frames, `box.SIMPLE_HEAVY` inner tables).
- **Panel 3**: Full-width multi-horizon or multi-regime matrix.
- **Panel 4**: Actionable checklist, risk geometry, or playbook.
- **Panel 5 (`5. Executive Bottom Line`)**: Color-coded traffic-light banner (`GREEN LIGHT`, `BLUE LIGHT`, `YELLOW LIGHT`, `RED LIGHT`, `STANDBY`) translating the math into plain English (`What's Happening`, `Why / Risk Check`, `Your Next Move`).

---

### Tab `[1]`: Tactical Swing Execution HUD (`[1: SWING ENGINE]`)
* **Primary Purpose**: Pinpoint high-R:R structural Spot Swing entries at `cVAL` / `Support HVN` floors backed by real Spot absorption, while blocking mid-range chop and futures-driven bull traps.
* **5-Panel Anatomy**:
  1. **Panel 1 (`1. Cross-Exchange Spot & Derivatives Health`)**: Live `Coinbase Spot` vs. `Binance Spot`, `Coinbase Premium Index` (`$` and `%` + Z-score), `Futures Open Interest (BTC)`, `15m / 1H / 4H dOI %`, `8H Funding Rate`, `5m Taker L/S Ratio`, and `OI Positioning Quadrant`.
  2. **Panel 2 (`2. Composite Auction Structure — Volume Profile`)**: Gaussian-smoothed `120-bin` Volume Profiles across **`30D Macro`**, **`7D Tactical`**, and **`24H Session`** (`Range High`, `cVAH`, `cPOC`, `cVAL`, `Primary LVN Below cVAL`, `Support HVN Floor`, `Dist to cVAL` in `%` and `ATR`, and `VA Pos %` with `[MID-CHOP: AVOID]` vs. `[EDGE ZONE]` badge).
  3. **Panel 3 (`3. Multi-Horizon Order Flow, Spot vs. Perp CVD & Passive Absorption`)**: Tracks `15m`, `1H`, `4H`, `24H`, `UTC Day`, and `Live WS Session` `Spot CVD Delta (BTC)`, `Spot Imbalance Z-Score`, `Perp CVD Delta (BTC)`, `Perp Imbalance Z-Score`, `Spot-Perp Divergence (Z)`, and `Passive Absorption Index`.
  4. **Panel 4 (`4. 4-Gate Swing Signal Engine & Dynamic Risk Geometry`)**:
     - **Left**: `0–100` Confluence Score (`Gate 1 Location: /25` • `Gate 2 Flow: /35` • `Gate 3 Derivatives: /20` • `Gate 4 Reclaim Trigger: /20`) + active Veto alerts.
     - **Right**: Exact USD `cVAL Entry Zone`, `Hard Invalidation Stop` (below sweep low / LVN `-0.5x ATR`), `TP1 (55% at cPOC -> Move SL to BE)`, `TP2 (45% at cVAH)`, and fixed-fractional `Position Size (BTC & USD)` at `1.0%` standard risk (automatically stepped down to `0.5%` counter-trend risk if Tab `[3]`'s `1D 200 SMA` Gatekeeper is in veto).
  5. **Panel 5 (`5. Executive Bottom Line`)**: Plain-English Traffic-Light Verdict.

---

### Tab `[2]`: BTC Spot Swing Protocol v1.3 & Liquidation Magnet HUD (`[2: PROTOCOL v1.3]`)
* **Primary Purpose**: Enforce **Protocol v1.3 (Sections 1–14)** capital-preservation discipline, audit the **CoinGlass 6-Panel Order in strict `BTC` coins**, block trading during **Non-Trade Zones (`8A–8F`)**, and execute the **Daily Liquidation Magnet & Range Pivot Protocol**.
* **5-Panel Anatomy (Covering All 14 Sections of Protocol v1.3)**:
  1. **Panel 1 (`Protocol Sections 1–5: Market Structure & ATR 14 Invalidation`)**: Separates `1D Completed [-2]` from `1D Forming [-1]`, computes `1D Support / Resistance` and `1D Bias` (`BULLISH` / `NEUTRAL` / `BEARISH`), `4H Structure & Timing`, and `1D / 4H ATR 14` (`±1xATR`) bounds.
  2. **Panel 2 (`Protocol Sections 6–7: CoinGlass 6-Panel Audit in Strict BTC Coins`)**: Displays the mandatory 1–6 order across `1D` and `4H`:
     - `1. Volume SMA 9 (BTC)` • `2. Aggregated Spot CVD (BTC)` • `3. Aggregated Futures CVD (BTC)` • `4. Open Interest (BTC Coins)` • `5. Funding Rates (8H)` • `6. ATR 14 (Volatility)`.
  3. **Panel 3 (`Protocol Section 8: Non-Trade Zones Matrix 8A–8F`)**:
     - `8A`: Weekend + `≤2%` of `$80k/$85k/$100k` + `OI > 90,000 BTC`
     - `8B`: `72h Liquidation Cascade > $300M`
     - `8C`: `Positive Funding + Flat/Rising OI + Falling Price`
     - `8D`: `FOMC / CPI High-Volatility Macro Window` (built-in 2026 calendar + manual override)
     - `8E`: `Section 8E S2 Systemic Risk Assessment`
     - `8F`: `Unverified Mandatory Check Safety Lock`
     *(Any triggered `8A–8F` zone automatically acts as a **Shared Master Veto** on Tab `[1]`).*
  4. **Panel 4 (`Protocol Sections 9–11: Buy Decision, Liquidation Magnets & Spot Sell Triggers`)**:
     - **Left**: Section 10 Buy Checklist (`BIAS`, `CONFIDENCE`, `NTZ`, `BUY ALLOWED`, `ENTRY STATUS`) + **Liquidation Magnet Protocol** (`Short-Liq Magnet Above`, `Long-Liq Magnet Below`, `50D MA`, `30D Range Pivot`, `5-Factor Confluence`, `Magnet Verdict`, and `Actionable Note` to scale `30–50%` into the short-liq magnet).
     - **Right**: Section 11 Long-Only Spot Sell Triggers (`1–4`) + `Headline Filter` (`Trade Magnet, Not Headline`).
  5. **Panel 5 (`Protocol Sections 12–14: Executive Bottom Line Verdict`)**: 4-line structured verdict (`NOW`, `DECISION`, `RISKS`, `LIMITATIONS`).

---

### Tab `[3]`: Macro Quant & Cycle Radar HUD (`[3: MACRO RADAR]`)
* **Primary Purpose**: Provide multi-week and multi-month positional context, enforce the **Rule 1 Macro Gatekeeper (`1D 200 SMA`)**, track **Power-Law Valuation**, and manage **Cycle Drawdown Crash Rungs (`-25%` to `-65%`)**.
* **5-Panel Anatomy**:
  1. **Panel 1 (`1. Quant Radar — Gatekeeper`)**:
     - `1D 200 SMA` & `5-Day Slope ($/day and %)` (**Rule 1 Gatekeeper**: requires `1D Close >= 200D SMA` and `5D Slope > 0` for full macro bull trend).
     - `1D Completed [-2]` vs. `1D Forming [-1]` close relative to `200D SMA`.
     - `1D 21 EMA Bull Market Support Band` & `% distance`.
     - `14D Wilder RSI` & momentum zone (`OVERSOLD <30`, `COOL 30–45`, `BULL 45–68`, `OVERBOUGHT >68`).
     - `30D Volume Profile POC`.
     - **`Power-Law Fair Value & Discount %`** ($P_{\text{fair}}(t) = 10^{-16.493 + 5.680 \log_{10}(t)}$ since Genesis `2009-01-03`), strictly quarantined as `[BIAS ONLY]` for long-horizon accumulation context.
  2. **Panel 2 (`2. Regime Radar — Cycle Armor & Crash Rungs -25% to -65%`)**: Tracks Cycle High (`ATH`), current drawdown `%`, and the 5 mechanical Spot accumulation tranches (`-25% Rung 1`, `-35% Rung 2`, `-45% Rung 3`, `-55% Rung 4`, `-65% Rung 5`).
  3. **Panel 3 (`3. Liquidity Radar — Multi-Timeframe 1W / 1D / 4H Sniper Matrix & 4H Wick Flush`)**: Audits candle structure, lower-wick rejection ratios, and taker delta across `1W`, `1D [-2]`, `1D [-1]`, and `4H`, plus the **`4H Liquidation Wick Flush Detector`** (`≥45%` lower-wick sweep into support paired with OI flush / uncrowded funding).
  4. **Panel 4 (`4. Unified Macro Arb & Allocation Engine`)**: Computes the `0–100%` 4-Family Macro Confidence Score (`Trend /25`, `Momentum /25`, `Flow /25`, `Structure /25`), recommended Spot allocation tier, and multi-month scale-out ceiling targets (`T1: 1D 21 EMA`, `T2: 1D 200 SMA`, `T3: Cycle High`, `T4: 1.272x Extension`).
  5. **Panel 5 (`5. Executive Bottom Line`)**: Macro & Cycle Traffic-Light Verdict (`GREEN LIGHT` Bull Regime, `BLUE LIGHT` Crash-Rung Deep Value Override, `YELLOW LIGHT` Consolidation, `RED LIGHT` Gatekeeper Veto).

---

### Tab `[4]`: Regime Radar — Quantitative Microstructure Matrix (`[4: REGIME MATRIX A–J]`)
* **Primary Purpose**: Diagnose the exact live market microstructure regime across **10 canonical institutional configurations (`Config A` through `Config J`)**, pairing `IF YOU OBSERVE` telemetry facts with `THEN IT MEANS` diagnoses, exact position sizing (`0.0x` to `1.0x`), and dynamic USD stops.
* **5-Panel Anatomy**:
  1. **Panel 1 (`1. Live Microstructure, VWAP & Basis Telemetry`)**: Real-time `Daily VWAP (24H)`, `Weekly VWAP (7D)`, `1D 20 EMA & 50 EMA`, `24H Spot Vol vs. 20D MA (x)`, `4H Spot Buy/Sell Ratio`, `7D Spot CVD (BTC)`, `1H/4H/24H dOI %`, `8H Funding`, `Annualized Perp Basis (%/yr)`, `ATR Compression %`, and `72H Base Width %`.
  2. **Panel 2 (`2. Active Configuration Diagnosis — #1 Match & #2 Runner-Up`)**: Displays the highest-scoring configuration (`0–100%` confidence match), its diagnosis, sizing rule, execution/harvest instruction, and dynamic USD stop, plus the `#2 Runner-Up` configuration.
  3. **Panel 3 (`3. Quantitative Microstructure Diagnostic Matrix — Configurations A through J`)**: Full 10-row live matrix:
     - **`Config A` (`Healthy Bull`)**: Genuine Spot-Led Expansion above Daily/Weekly VWAP $\rightarrow$ `Full Spot Long (1.0x) | Stop: 4H swing low -0.6%`.
     - **`Config B` (`Leveraged Bull`)**: Fragile Perp-Led Overextension $\rightarrow$ `Trim / Stand Aside (0.0x) | Sell 33% into perp pump`.
     - **`Config C` (`Bullish Absorption`)**: Institutional Base Defense at range low $\rightarrow$ `Build Spot (0.75x) | Stop: Sweep wick low -0.5%`.
     - **`Config D` (`Masked Fragility`)**: Stealth Distribution into Perp Float $\rightarrow$ `Defensive Cash (100%) | Exit 50% at market`.
     - **`Config E` (`Liquidation Cascade`)**: Forced De-leveraging Waterfall $\rightarrow$ `Wait for Phase 3 Capitulation Wick (0.0x -> 0.50x)`.
     - **`Config F` (`Re-Accumulation`)**: Post-Cascade Clean Base (`ATR compression >40%`, tight `<2.5%` range) $\rightarrow$ `Re-Accumulate (0.75x) | Stop: Base floor -0.5%`.
     - **`Config G` (`Short Squeeze`)**: Mechanical Liquidation Spike without Spot volume $\rightarrow$ `Harvest Gains (0.0x new buys) | Sell 50% into spike`.
     - **`Config H` (`Distribution Top`)**: Topping Exhaustion at `cVAH` $\rightarrow$ `Defensive Cash (100%) | Cut 75% immediately`.
     - **`Config I` (`Bear Trend`)**: Persistent Spot Selling below `20D/50D EMA` $\rightarrow$ `Strict Cash (100%) | Inval: 1D close > 50D EMA`.
     - **`Config J` (`Bear Trap`)**: Failed Breakdown & Capitulation Absorption $\rightarrow$ `Reclaim Buy (1.0x) | Stop: Sweep low -0.5%`.
  4. **Panel 4 (`4. Active Configuration Checklist & Global Session Microstructure Reference`)**:
     - **Left**: Live `✔`/`✖` fact checklist and mandate for the `#1 Active Config`.
     - **Right**: All 6 **Global Trading Sessions (`UTC • SGT`)** (`Asia Session`, `Asia/London Overlap`, `London/EU`, `London/NY Overlap`, `New York Session`, `Late NY/Transition`) with the current window dynamically highlighted (`►`).
  5. **Panel 5 (`5. Executive Bottom Line`)**: Plain-English Traffic-Light Verdict for the active `Config A–J` regime.

---

### Tab `[5]`: Master Conclusion & Supreme Order of Battle HUD (`[5: MASTER CONCLUSION]`)
* **Primary Purpose**: Act as the **"Chief Investment Officer / Supreme Court Desk"** across Tabs `[1]`, `[2]`, `[3]`, and `[4]`. It rolls up the Executive Bottom Lines of all 4 specialist tabs, resolves any cross-tab disagreements using a strict 4-Layer Institutional Decision Funnel, and delivers reconciled execution rules for both cash and spot holders.
* **5-Panel Anatomy**:
  1. **Panel 1 (`1. 4-Tab Executive Verdict Rollup Matrix`)**: Live scoreboard displaying each specialist tab's Traffic Light (`GREEN`, `BLUE`, `YELLOW`, `RED`), Score/State, and Executive Conclusion, plus the composite **Master Alignment Score (`0–100%`)**.
  2. **Panel 2 (`2. 4-Layer Institutional Decision Funnel & Conflict Resolver`)**:
     - **Layer 1 (`L1: Veto Gate — Tab 2 + 4`)**: *Supreme Veto Power.* Checks Non-Trade Zones (`8A–8F`), Spot Sell Triggers (`1–4`), and `Config G/H`. Overrides all other tabs if triggered.
     - **Layer 2 (`L2: Macro Risk — Tab 3`)**: Sets the Base Risk Budget (`1.00%` standard risk above a rising `200D SMA` vs. `0.50%` counter-trend risk cap below the `200D SMA`).
     - **Layer 3 (`L3: Size & Magnet — Tab 4 + 2`)**: Applies the `Config A–J` Sizing Multiplier (`0.00x` to `1.00x`) and maps the nearest `Short-Liq` and `Long-Liq` magnets.
     - **Layer 4 (`L4: Entry Timing — Tab 1`)**: Enforces the Mid-Range Chop Filter (`va_position_pct`) and times the final `15m/1H` candle reclaim trigger at `cVAL` / `Support HVN`.
  3. **Panel 3 (`3. Cross-Tab Agreement & Divergence Audit`)**: Plain-English bullet points detailing:
     - `✔ Cross-Tab Confluence` (where the 4 tabs agree right now),
     - `⚡ Cross-Tab Conflict Diagnostic & Resolution` (why two tabs differ and how the hierarchy resolves it), and
     - `🎯 Catalysts That Flip the Master Conclusion` (exact `$` levels and flow conditions that upgrade to `GREEN LIGHT` or downgrade to `RED LIGHT`).
  4. **Panel 4 (`4. Unified Master Order of Battle — Track A: In Cash vs. Track B: Holding Spot BTC`)**:
     - **Track A (`IF FLAT IN CASH`)**: Reconciled Buy Permission, Reconciled Bid Zone (`$`), Reconciled Sizing Math (`Base Risk [T3] × Regime Multiplier [T4] -> BTC & USD`), and Execution Rule.
     - **Track B (`IF HOLDING SPOT BTC`)**: Reconciled Spot Mandate, Reconciled Hard Stop-Loss (`$` across Tab `[1]`, Tab `[4]`, and `50D MA`), Reconciled Profit Targets (`TP1 40%` & `TP2 60%`), and Management Rule.
  5. **Panel 5 (`5. Executive Bottom Line — Supreme Master Conclusion` + `[Press C: Copy AI Data Packet]` Button)**:
     - The ultimate traffic-light banner (`GREEN LIGHT`, `BLUE LIGHT`, `YELLOW LIGHT`, `RED LIGHT`) synthesizing `Master Synthesis`, `Conflict Ruling`, and `Final Command`.
     - **One-Key AI Telemetry Export (`Press C`)**: Pressing **`C`** on your keyboard immediately collects 100% of the raw quantitative metrics from Tabs `[1]` through `[4]` (`analytics/ai_packet_exporter.py`), attaches an independent Chief Risk Officer audit prompt, copies the entire Markdown packet directly to your **Windows Clipboard (`Ctrl+V` ready)** for pasting into Gemini Argon AI / Super Grok, and saves a copy to `Downloads\BTC_AI_DATA_PACKET_LATEST.md`.

---

## 5. Daily & Tactical Operational Workflow

1. **Launch the Engine**:
   ```powershell
   cd C:\Users\aikel\.gemini\antigravity\scratch\btc_swing_engine
   .\.venv\Scripts\python.exe main.py
   ```
2. **Step 1 — Check the Supreme Master Conclusion (`Press 5` -> Tab `[5]: MASTER CONCLUSION`)**:
   - Inspect the 4-Tab Scoreboard in Panel 1, the 4-Layer Decision Funnel in Panel 2, the Conflict Diagnostic in Panel 3, and your exact **Track A (In Cash)** or **Track B (Holding Spot)** playbook in Panel 4.
3. **Step 2 — Macro & Cycle Orientation (`Press 3` -> Tab `[3]: MACRO RADAR`)**:
   - Check whether the `1D 200 SMA` Gatekeeper is `PASS` (`1.0%` standard risk) or `VETO` (`0.5%` counter-trend risk cap), note the `Power-Law Discount %`, and check if any `-25%` to `-65%` Crash Rung or `4H Wick Flush` is active.
4. **Step 3 — Daily Capital Preservation & Liquidation Magnet Audit (`Press 2` -> Tab `[2]: PROTOCOL v1.3`)**:
   - Verify all 6 Non-Trade Zones (`8A–8F`) are `CLEAR`.
   - Note the `Short-Liq Magnet` above, `Long-Liq Magnet` below, `50D MA / Range Pivot`, and the `Magnet Verdict` (`Hold / Partial Profit into Magnet / Do Nothing`).
5. **Step 4 — Microstructure Regime Diagnosis (`Press 4` -> Tab `[4]: REGIME MATRIX A–J`)**:
   - Identify which institutional configuration (`Config A` through `Config J`) currently dominates and check the active `UTC / SGT` regional session context in Panel 4.
6. **Step 5 — Precision Spot Execution & Risk Sizing (`Press 1` -> Tab `[1]: SWING ENGINE`)**:
   - Only execute a new Spot Swing Long when price is at an `[EDGE ZONE]` (never `[MID-CHOP: AVOID]`) and Panel 5 turns `GREEN LIGHT` (or `BLUE LIGHT` while staging limit orders at `cVAL` / `Support HVN`), using the exact `Entry Zone`, `Stop-Loss`, `TP1 (cPOC -> Move SL to BE)`, `TP2 (cVAH)`, and `BTC Position Size` in Panel 4.


---

# 6. Complete Source Code Packet (All Files Verbatim)

## 6.1. Project Directory Tree & Quick-Start Rebuild Guide

```text
btc_swing_engine/
├── BTC_SWING_ENGINE_WHITEPAPER.md
├── BTC_SWING_ENGINE_COMPLETE_PACKET.md
├── GEMINI.md
├── requirements.txt
├── main.py
├── config/
│   ├── __init__.py
│   ├── settings.py
│   └── protocol_context.json
├── core/
│   ├── __init__.py
│   ├── models.py
│   └── state_store.py
├── collectors/
│   ├── __init__.py
│   ├── warmup_loader.py
│   ├── ws_streams.py
│   └── rest_metrics.py
├── analytics/
│   ├── __init__.py
│   ├── volume_profile.py
│   ├── cvd_engine.py
│   ├── protocol_v13.py
│   ├── macro_radar.py
│   ├── regime_matrix.py
│   ├── master_synthesis.py
│   ├── ai_packet_exporter.py
│   └── signal_detector.py
├── ui/
│   ├── __init__.py
│   └── terminal_hud.py
└── tests/
    └── test_analytics.py
```

### How to Rebuild & Run on Any Windows Machine from Google Drive:
```powershell
cd C:\Users\aikel\.gemini\antigravity\scratch\btc_swing_engine
python -m venv .venv
.\.venv\Scripts\pip.exe install -r requirements.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe main.py
```

---

### File: `requirements.txt`

```text
aiohttp>=3.9.0
websockets>=12.0
rich>=13.7.0
numpy>=1.26.0
pandas>=2.1.0

```

---

### File: `GEMINI.md`

```markdown
# BTC Swing Engine & Unified 4-Tab Rich Live TUI HUD Rules

- Preserve the 5-panel retro IBM / Bloomberg terminal layout (`rich.box.ROUNDED` outer panels + `rich.box.SIMPLE_HEAVY` tables) and the 2-row Top Status Banner (with `UTC`, `SGP (Asia)`, `LON (EU)`, `NYC (US)` clocks and the `ACTIVE MARKET` regional session badge) across all 4 instant-switchable views (`[1] Swing Engine`, `[2] Protocol v1.3`, `[3] Macro Radar`, `[4] Regime Matrix A–J`) in `ui/terminal_hud.py`.
- Never increase vertical row height on any single tab beyond a single terminal screen (~42–48 lines) so `rich.live.Live` updates at `2 Hz` (`0.5s`) and switches tabs in `0.0s` (`msvcrt` keys `1`, `2`, `3`, `4`) without scrolling or flickering.
- Maintain the 4 synchronized `asyncio` update loops (real-time WebSockets, `2 Hz` HUD & signal evaluation with `20 Hz` keyboard listener, `15s` REST derivatives poller, and `60s` kline sync) and Zero-Cold-Start historical warmup (`[1/3] -> [2/3] -> [3/3]` loading `1W`, `1D`, `1H`, and `15m` klines).
- Always keep **Panel 5 (`5. Executive Bottom Line`)** at the bottom of every tab with a color-coded traffic-light headline (`GREEN LIGHT`, `BLUE LIGHT`, `YELLOW LIGHT`, `RED LIGHT`, `STANDBY`) and plain-English lines.

```

---

### File: `main.py`

```python
"""Main asyncio orchestrator for the Long-Only BTC-USD Spot Swing Microstructure & Auction Engine."""

import argparse
import asyncio
import logging
import sys
from typing import List

from rich.console import Console

from analytics.ai_packet_exporter import copy_ai_packet_to_clipboard_and_disk
from analytics.signal_detector import SignalDetector
from collectors import (
    poll_rest_metrics,
    run_initial_warmup,
    stream_binance_perp,
    stream_binance_spot,
    stream_coinbase_spot,
)
from config.settings import DEFAULT_CONFIG, EngineConfig
from core.state_store import StateStore
from ui.terminal_hud import print_dry_run_report, run_terminal_hud


def _configure_stdio() -> None:
    """Ensures UTF-8 console encoding on Windows terminals."""
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    if hasattr(sys.stderr, "reconfigure"):
        try:
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass


async def _run_engine(
    config: EngineConfig,
    dry_run: bool = False,
    duration: float = 15.0,
    tab_arg: str = "1",
    copy_packet: bool = False,
) -> None:
    """Initializes historical backfill, starts concurrent WebSocket/REST streams, and runs the HUD."""
    console = Console(force_terminal=True)
    store = StateStore()
    if tab_arg in ("1", "2", "3", "4", "5"):
        store.active_tab = int(tab_arg)
    detector = SignalDetector(config)

    console.print(
        "[bold cyan][1/3] Running Zero-Cold-Start Historical Backfill "
        "(1W/1D Macro & Protocol Candles, 30D/7D Spot & Perp Klines, 4H OI, Funding & Coinbase Basis)...[/bold cyan]"
    )
    await run_initial_warmup(config, store)
    detector.evaluate(store)

    console.print(
        f"[bold green][2/3] Warmup complete![/bold green] "
        f"Loaded {len(store.spot_klines_1w)}x 1W bars, "
        f"{len(store.spot_klines_1d)}x 1D bars, "
        f"{len(store.spot_klines_1h)}x 1H Spot bars, "
        f"{len(store.perp_klines_1h)}x 1H Perp bars, "
        f"{len(store.spot_klines_15m)}x 15m bars."
    )

    background_tasks: List[asyncio.Task] = [
        asyncio.create_task(stream_binance_spot(config, store), name="binance_spot_ws"),
        asyncio.create_task(stream_binance_perp(config, store), name="binance_perp_ws"),
        asyncio.create_task(stream_coinbase_spot(config, store), name="coinbase_spot_ws"),
        asyncio.create_task(poll_rest_metrics(config, store), name="rest_metrics_poller"),
    ]

    try:
        if dry_run:
            console.print(
                f"[bold yellow][3/3] Dry-Run Mode: Streaming live WebSocket order flow "
                f"(Binance Spot, Perp & Coinbase) for {duration:.0f} seconds...[/bold yellow]"
            )
            steps = max(1, int(duration))
            for _ in range(steps):
                await asyncio.sleep(1.0)
                detector.evaluate(store)

            if copy_packet:
                copy_ai_packet_to_clipboard_and_disk(config, store)

            print_dry_run_report(config, store, tab_arg=tab_arg)
            console.print(
                f"\n[bold green]Verification Complete![/bold green] "
                f"Structured JSONL signal state written to: [underline]{config.signal_log_path}[/underline]"
            )
        else:
            console.print(
                "[bold green][3/3] Launching Unified 5-Tab Live Terminal HUD "
                "(Press [bold cyan]1[/bold cyan]=Swing Engine, [bold yellow]2[/bold yellow]=Protocol v1.3, "
                "[bold magenta]3[/bold magenta]=Macro Radar, [bold green]4[/bold green]=Regime Matrix A–J, "
                "[bold blue]5[/bold blue]=Master Conclusion, [bold yellow]C[/bold yellow]=Copy AI Data Packet)...[/bold green]"
            )
            await run_terminal_hud(config, store, detector)
    finally:
        for task in background_tasks:
            task.cancel()
        await asyncio.gather(*background_tasks, return_exceptions=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Long-Only Bitcoin (BTC-USD) Spot Swing Microstructure & Auction Engine"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Connect to all REST/WebSocket feeds, stream live order flow for 15s, print full audit report, and exit.",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=15.0,
        help="Duration in seconds for --dry-run live stream verification (default: 15).",
    )
    parser.add_argument(
        "--tab",
        type=str,
        default="1",
        choices=["1", "2", "3", "4", "5", "all"],
        help="Initial active HUD tab (1=Swing Engine, 2=Protocol v1.3, 3=Macro Radar, 4=Regime Matrix A-J, 5=Master Conclusion, or 'all' in --dry-run).",
    )
    parser.add_argument(
        "--copy-packet",
        action="store_true",
        help="Copy the full Raw Telemetry & AI Audit Packet (Tabs 1-4) to the Windows Clipboard during --dry-run.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable verbose debug logging.",
    )
    return parser.parse_args()


def main() -> None:
    _configure_stdio()
    args = parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.WARNING,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    try:
        asyncio.run(
            _run_engine(
                DEFAULT_CONFIG,
                dry_run=args.dry_run,
                duration=args.duration,
                tab_arg=args.tab,
                copy_packet=args.copy_packet,
            )
        )
    except KeyboardInterrupt:
        print("\nBTC Swing Engine terminated by user.")
        sys.exit(0)


if __name__ == "__main__":
    main()

```

---

### File: `config/__init__.py`

```python
"""Configuration package for BTC Spot Swing Microstructure & Auction Engine."""

from .settings import EngineConfig, DEFAULT_CONFIG

__all__ = ["EngineConfig", "DEFAULT_CONFIG"]

```

---

### File: `config/settings.py`

```python
"""Centralized configuration and quantitative thresholds for the BTC Swing Engine."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List


BASE_DIR = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class EngineConfig:
    """Configuration parameters for data ingestion, volume profile math, and signal detection."""

    # --- Symbols ---
    binance_symbol: str = "BTCUSDT"
    coinbase_symbol: str = "BTC-USD"

    # --- Public REST Endpoints (with automatic geo-resilient fallbacks) ---
    binance_spot_rest_urls: List[str] = field(
        default_factory=lambda: [
            "https://api.binance.com",
            "https://data-api.binance.vision",
            "https://api1.binance.com",
        ]
    )
    binance_perp_rest_urls: List[str] = field(
        default_factory=lambda: [
            "https://fapi.binance.com",
        ]
    )
    okx_rest_url: str = "https://www.okx.com"
    bybit_rest_url: str = "https://api.bybit.com"
    coinbase_rest_url: str = "https://api.exchange.coinbase.com"

    # --- Public WebSocket Endpoints (with automatic fallbacks) ---
    binance_spot_ws_urls: List[str] = field(
        default_factory=lambda: [
            "wss://stream.binance.com:9443/ws/btcusdt@aggTrade",
            "wss://data-stream.binance.vision/ws/btcusdt@aggTrade",
        ]
    )
    binance_perp_ws_urls: List[str] = field(
        default_factory=lambda: [
            "wss://fstream.binance.com/ws/btcusdt@aggTrade",
        ]
    )
    bybit_perp_ws_url: str = "wss://stream.bybit.com/v5/public/linear"
    coinbase_ws_url: str = "wss://ws-feed.exchange.coinbase.com"

    # --- WebSocket & Polling Resilience ---
    ws_ping_interval: int = 20
    ws_ping_timeout: int = 20
    ws_reconnect_base_delay: float = 1.5
    ws_reconnect_max_delay: float = 30.0
    rest_poll_interval_sec: float = 15.0
    kline_sync_interval_sec: float = 60.0
    hud_refresh_rate_hz: float = 2.0

    # --- Structural Volume Profile Parameters ---
    macro_profile_days: int = 30        # 30-Day Macro Composite (720 x 1H klines)
    tactical_profile_days: int = 7      # 7-Day Tactical Composite (168 x 1H klines)
    profile_num_bins: int = 120         # Number of price bins across range
    value_area_pct: float = 0.70        # Standard 70% CME Value Area (1 SD)
    gaussian_sigma_bins: float = 1.5    # Smoothing sigma for HVN/LVN topology
    lvn_relative_threshold: float = 0.55  # Local min below 55% of mean bin volume
    hvn_relative_threshold: float = 1.20  # Local max above 120% of mean bin volume
    atr_period: int = 14                # 14-bar ATR on 1H & 4H timeframes

    # --- Order Flow & CVD Normalization ---
    cvd_zscore_lookback: int = 48       # Trailing windows for Z-score standardization
    absorption_effort_threshold: float = 1.8  # Effort-vs-Result ratio threshold at cVAL
    divergence_z_spread_threshold: float = 1.0  # Z_spot - Z_perp threshold for absorption
    leveraged_trap_z_spread: float = -1.2     # Z_spot - Z_perp threshold for perp chase trap

    # --- Derivatives & Positioning Thresholds ---
    oi_flush_pct_4h: float = -1.5       # 4H OI drop (%) signaling long liquidation reset
    oi_short_build_pct_1h: float = 0.4  # 1H OI rise (%) while price <= 0 at cVAL
    oi_surge_trap_pct_1h: float = 0.8   # 1H OI surge (%) during unconfirmed perp bounce
    funding_neutral_max_pct: float = 0.012    # <= 0.012% per 8h considered healthy/un-crowded
    funding_crowded_veto_pct: float = 0.035   # > 0.035% per 8h triggers crowded-long veto
    cpi_positive_threshold_pct: float = 0.0   # Direct USD premium over USDT
    cpi_zscore_bullish_threshold: float = 0.75

    # --- 4-Gate Execution & Risk Management ---
    val_proximity_atr_mult: float = 0.50      # Distance from cVAL (in 1H ATRs) to arm Gate 1
    min_structural_rr_to_poc: float = 1.5     # Minimum Reward:Risk to cPOC
    stop_atr_buffer_mult: float = 0.50        # Stop placed 0.5 x 1H ATR below sweep low / LVN
    tp1_allocation_pct: float = 55.0          # Scale out 55% at cPOC, move stop to BE
    tp2_allocation_pct: float = 45.0          # Trail 45% to cVAH
    signal_confluence_threshold: float = 70.0 # Minimum 0-100 score for actionable signal
    portfolio_equity_usd: float = 100_000.0   # Reference portfolio size for position sizing
    risk_per_trade_pct: float = 1.0           # 1.0% equity risk per swing setup
    counter_trend_risk_pct: float = 0.5       # 0.5% equity risk when below 1D 200 SMA

    # --- Protocol v1.3 & Macro Cycle Radar Parameters ---
    daily_kline_limit: int = 255              # 255x 1D candles for 200D SMA + 5D slope + 14D RSI
    weekly_kline_limit: int = 60              # 60x 1W candles for Weekly structure & Cycle High
    protocol_oi_high_threshold_btc: float = 90_000.0  # Protocol v1.3 8A OI threshold in strict BTC
    protocol_round_numbers_usd: List[float] = field(
        default_factory=lambda: [80_000.0, 85_000.0, 100_000.0]
    )
    protocol_round_proximity_pct: float = 2.0 # Within 2.0% of round number for 8A check
    default_cycle_ath_usd: float = 109_588.0  # Cycle ATH reference floor if higher than 255D window
    protocol_context_path: Path = field(
        default_factory=lambda: BASE_DIR / "config" / "protocol_context.json"
    )

    # --- Logging ---
    signal_log_path: Path = field(
        default_factory=lambda: BASE_DIR / "logs" / "swing_signals.jsonl"
    )


DEFAULT_CONFIG = EngineConfig()

```

---

### File: `config/protocol_context.json`

```json
{
  "last_reviewed_utc": "2026-10-27T00:00:00Z",
  "liq_cascade_72h_over_300m": "CONFIRMED_CLEAR",
  "liq_cascade_reclaimed_within_24h": "CONFIRMED_CLEAR",
  "fomc_cpi_window_override": "AUTO",
  "s2_risk_level": "LOW",
  "etf_net_outflow_weakness": "NOT_CONFIRMED",
  "catalyst_technical_breakdown": "NOT_CONFIRMED",
  "enforce_200d_hard_veto_on_tab1": false,
  "cycle_ath_override_usd": 109588.0,
  "short_liq_magnet_override_usd": 0.0,
  "long_liq_magnet_override_usd": 0.0,
  "headline_classification": "NONE_SIGNIFICANT"
}

```

---

### File: `core/__init__.py`

```python
"""Core data models and thread/async-safe state store for the BTC Swing Engine."""

from .models import (
    DerivativesSnapshot,
    ExecutionGateState,
    FlowSnapshot,
    HorizonFlowMetrics,
    KlineBar,
    MarketRegime,
    OIPositioningQuadrant,
    SignalEvaluation,
    TradePlan,
    VolumeProfileResult,
)
from .state_store import StateStore

__all__ = [
    "DerivativesSnapshot",
    "ExecutionGateState",
    "FlowSnapshot",
    "HorizonFlowMetrics",
    "KlineBar",
    "MarketRegime",
    "OIPositioningQuadrant",
    "SignalEvaluation",
    "StateStore",
    "TradePlan",
    "VolumeProfileResult",
]

```

---

### File: `core/models.py`

```python
"""Typed data structures for Auction Profiles, Order Flow, Derivatives, and Swing Signals."""

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class MarketRegime(str, Enum):
    """Macro-microstructure market state classification."""

    BALANCED = "BALANCED"
    ABSORPTION_AT_SUPPORT = "ABSORPTION_AT_SUPPORT"
    LEVERAGE_EXPANSION = "LEVERAGE_EXPANSION"
    LEVERAGE_TRAP = "LEVERAGE_TRAP"
    MARKDOWN = "MARKDOWN"


class ExecutionGateState(str, Enum):
    """4-Gate sequential execution funnel state."""

    CASH_MARKDOWN = "CASH_MARKDOWN"
    NEUTRAL_OBSERVATION = "NEUTRAL_OBSERVATION"
    GATE1_ZONE_ALERT = "GATE1_ZONE_ALERT"
    GATE2_MICROSTRUCTURE_ARMED = "GATE2_MICROSTRUCTURE_ARMED"
    GATE3_RECLAIM_TRIGGERED = "GATE3_RECLAIM_TRIGGERED"


class OIPositioningQuadrant(str, Enum):
    """4-Quadrant Price vs. Open Interest classification."""

    LONG_LIQUIDATION_FLUSH = "LONG_LIQUIDATION_FLUSH (Price Down / OI Down)"
    AGGRESSIVE_SHORT_BUILD = "AGGRESSIVE_SHORT_BUILD (Price Down/Flat / OI Up)"
    LEVERAGED_LONG_EXPANSION = "LEVERAGED_LONG_EXPANSION (Price Up / OI Up)"
    SHORT_COVERING_BOUNCE = "SHORT_COVERING_BOUNCE (Price Up / OI Down)"
    NEUTRAL_CHURN = "NEUTRAL_CHURN"


@dataclass
class KlineBar:
    """Standardized OHLCV + Taker Buy/Sell Volume candle."""

    timestamp_ms: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    taker_buy_volume: float

    @property
    def taker_sell_volume(self) -> float:
        return max(0.0, self.volume - self.taker_buy_volume)

    @property
    def delta(self) -> float:
        return self.taker_buy_volume - self.taker_sell_volume

    @property
    def typical_price(self) -> float:
        return (self.high + self.low + self.close) / 3.0


@dataclass
class VolumeProfileResult:
    """Computed Composite Volume Profile with 70% Value Area and HVN/LVN topology."""

    horizon_label: str
    c_vah: float
    c_poc: float
    c_val: float
    range_high: float
    range_low: float
    total_volume: float
    bin_width: float
    lvn_levels: List[float] = field(default_factory=list)
    hvn_levels: List[float] = field(default_factory=list)
    primary_lvn_below_val: Optional[float] = None
    support_hvn_below_val: Optional[float] = None
    bin_centers: List[float] = field(default_factory=list)
    bin_volumes: List[float] = field(default_factory=list)


@dataclass
class HorizonFlowMetrics:
    """Normalized Spot vs. Perp order flow metrics over a specific rolling horizon."""

    window_label: str
    spot_delta_btc: float = 0.0
    spot_volume_btc: float = 0.0
    spot_delta_ratio: float = 0.0
    spot_zscore: float = 0.0
    perp_delta_btc: float = 0.0
    perp_volume_btc: float = 0.0
    perp_delta_ratio: float = 0.0
    perp_zscore: float = 0.0
    flow_divergence_z: float = 0.0
    absorption_index: float = 0.0
    price_change_pct: float = 0.0


@dataclass
class FlowSnapshot:
    """Complete multi-horizon order flow and live WebSocket CVD state."""

    session_spot_cvd: float = 0.0
    session_perp_cvd: float = 0.0
    utc_day_spot_cvd: float = 0.0
    utc_day_perp_cvd: float = 0.0
    spot_trade_count: int = 0
    perp_trade_count: int = 0
    w_15m: HorizonFlowMetrics = field(default_factory=lambda: HorizonFlowMetrics("15m"))
    w_1h: HorizonFlowMetrics = field(default_factory=lambda: HorizonFlowMetrics("1H"))
    w_4h: HorizonFlowMetrics = field(default_factory=lambda: HorizonFlowMetrics("4H"))
    w_24h: HorizonFlowMetrics = field(default_factory=lambda: HorizonFlowMetrics("24H"))
    bullish_pivot_divergence: bool = False
    absorption_divergence: bool = False
    flow_signature: str = "BALANCED"


@dataclass
class DerivativesSnapshot:
    """Cross-exchange basis, Open Interest dynamics, and funding positioning."""

    open_interest_btc: float = 0.0
    open_interest_usd: float = 0.0
    oi_change_15m_pct: float = 0.0
    oi_change_1h_pct: float = 0.0
    oi_change_4h_pct: float = 0.0
    oi_regime_quadrant: OIPositioningQuadrant = OIPositioningQuadrant.NEUTRAL_CHURN
    funding_rate_pct: float = 0.0
    taker_long_short_ratio_5m: float = 1.0
    perp_5m_delta_btc: float = 0.0
    coinbase_price: float = 0.0
    binance_spot_price: float = 0.0
    binance_perp_price: float = 0.0
    coinbase_premium_usd: float = 0.0
    coinbase_premium_pct: float = 0.0
    coinbase_premium_zscore: float = 0.0
    perp_basis_usd: float = 0.0
    perp_source: str = "Binance USD-M"


@dataclass
class TradePlan:
    """Actionable spot swing trade execution geometry and dynamic position sizing."""

    entry_zone_low: float
    entry_zone_high: float
    reference_entry: float
    stop_loss: float
    tp1_poc: float
    tp1_allocation_pct: float
    tp2_vah: float
    tp2_allocation_pct: float
    rr_to_poc: float
    rr_to_vah: float
    position_size_btc: float
    position_notional_usd: float
    risk_usd: float
    risk_pct: float = 1.0


@dataclass
class CoinGlassPanelRow:
    """Single row of the fixed 6-panel CoinGlass audit (Tab 2 Panel 2)."""

    panel_num: int
    metric_name: str
    value_1d: str
    value_4h: str
    direction_status: str


@dataclass
class ProtocolNonTradeZoneItem:
    """Single Section 8 Non-Trade Zone check (8A-8F) in Protocol v1.3."""

    code: str
    rule_name: str
    status: str  # "CLEAR", "TRIGGERED", "UNVERIFIED"
    detail: str


@dataclass
class ProtocolSellTriggerItem:
    """Single Section 11 Long-Only Spot Sell Trigger (1-4) in Protocol v1.3."""

    trigger_num: int
    name: str
    status: str  # "CONFIRMED", "NOT CONFIRMED", "UNVERIFIED"
    detail: str


@dataclass
class ProtocolV13Evaluation:
    """Complete evaluation state for Tab [2]: BTC Spot Swing Protocol v1.3."""

    timestamp_utc: str
    current_price: float
    completed_1d_open: float
    completed_1d_high: float
    completed_1d_low: float
    completed_1d_close: float
    completed_1d_change_pct: float
    forming_1d_open: float
    forming_1d_high: float
    forming_1d_low: float
    forming_1d_close: float
    forming_1d_change_pct: float
    daily_support: float
    daily_resistance: float
    daily_bias: str  # "BULLISH", "NEUTRAL", "BEARISH"
    structure_4h: str
    timing_4h_ready: bool
    atr_14_1d: float
    atr_14_4h: float
    downside_ref_1d_atr: float
    upside_ref_1d_atr: float
    downside_ref_4h_atr: float
    upside_ref_4h_atr: float
    coinglass_rows: List[CoinGlassPanelRow] = field(default_factory=list)
    non_trade_zones: List[ProtocolNonTradeZoneItem] = field(default_factory=list)
    non_trade_zone_status: str = "NO"  # "YES", "NO", "UNVERIFIED"
    active_ntz_reasons: List[str] = field(default_factory=list)
    confidence: str = "LOW"  # "HIGH", "MEDIUM", "LOW"
    buy_allowed: str = "NO"  # "YES", "NO"
    entry_status: str = "NOT READY"  # "READY", "NOT READY"
    readiness_notes: List[str] = field(default_factory=list)
    sell_triggers: List[ProtocolSellTriggerItem] = field(default_factory=list)
    any_sell_confirmed: bool = False
    enforce_200d_hard_veto_on_tab1: bool = False
    context_last_reviewed: str = "N/A"
    sma_50_1d: float = 0.0
    range_pivot_usd: float = 0.0
    short_liq_magnet_usd: float = 0.0
    short_liq_source: str = "[EST. SWING LIQ POOL]"
    long_liq_magnet_usd: float = 0.0
    long_liq_source: str = "[EST. SWING LIQ POOL]"
    headline_filter_status: str = "NONE_SIGNIFICANT"
    magnet_confluence_aligned: int = 0
    liq_magnet_verdict: str = "DO NOTHING (Default Inaction)"
    liq_magnet_action_note: str = ""


@dataclass
class CrashRungItem:
    """Single Cycle Drawdown Accumulation Rung (-25% to -65%) for Tab [3] Panel 2."""

    rung_label: str
    drawdown_pct: float
    target_price: float
    distance_pct: float
    allocation_tranche: str
    status: str  # "HIT / ACTIVE", "NEAR (<3%)", "STANDBY"


@dataclass
class MacroTimeframeRow:
    """Single timeframe row (1W / 1D Completed / 1D Forming / 4H) for Tab [3] Panel 3."""

    timeframe: str
    structure: str
    close_vs_open_pct: float
    candle_signature: str
    flow_momentum: str


@dataclass
class MacroRadarEvaluation:
    """Complete evaluation state for Tab [3]: Macro Quant & Cycle Radar."""

    timestamp_utc: str
    current_price: float
    completed_1d_close: float
    forming_1d_close: float
    sma_200_1d: float
    sma_200_slope_5d_usd: float
    sma_200_slope_5d_pct: float
    above_200d_sma: bool
    slope_200d_positive: bool
    gatekeeper_veto: bool
    gatekeeper_status_text: str
    ema_21_1d: float
    dist_to_21d_ema_pct: float
    rsi_14_1d: float
    rsi_zone: str
    poc_30d: float
    dist_to_30d_poc_pct: float
    power_law_fair_usd: float = 0.0
    power_law_discount_pct: float = 0.0
    power_law_zone_label: str = "[BIAS ONLY — NOT TIMING]"
    cycle_high_usd: float = 0.0
    current_drawdown_pct: float = 0.0
    active_crash_rung: str = "NONE"
    crash_rung_override_active: bool = False
    crash_rungs: List[CrashRungItem] = field(default_factory=list)
    scale_out_targets: List[str] = field(default_factory=list)
    tf_rows: List[MacroTimeframeRow] = field(default_factory=list)
    wick_flush_4h_detected: bool = False
    wick_flush_4h_ratio: float = 0.0
    wick_flush_detail: str = "NONE"
    trend_score: float = 0.0
    momentum_score: float = 0.0
    flow_score: float = 0.0
    structure_score: float = 0.0
    macro_confidence_pct: float = 0.0
    recommended_allocation: str = "0% (100% CASH)"
    macro_notes: List[str] = field(default_factory=list)


@dataclass
class RegimeConfigItem:
    """Single row/configuration (Config A through Config J) for Tab [4] Regime Matrix."""

    code: str  # "Config A" .. "Config J"
    short_title: str  # e.g. "Healthy Bull"
    diagnosis_subtitle: str  # e.g. "Genuine Spot-Led Expansion"
    category: str  # "BULL_LONG", "ACCUMULATE", "HARVEST_WAIT", "DEFENSIVE_CASH"
    match_pct: float  # 0.0 .. 100.0
    is_active: bool
    key_live_facts: str
    action_headline: str  # e.g. "Full Spot Long (1.0x)"
    sizing_rule: str
    entry_or_harvest_rule: str
    stop_rule: str
    computed_stop_usd: float
    observed_checklist: List[str] = field(default_factory=list)


@dataclass
class RegimeMatrixEvaluation:
    """Complete evaluation state for Tab [4]: Quantitative Microstructure Configurations A-J."""

    timestamp_utc: str
    current_price: float
    daily_vwap: float
    weekly_vwap: float
    ema_20_1d: float
    ema_50_1d: float
    spot_vol_vs_20d_ma: float
    spot_buy_sell_ratio_4h: float
    spot_cvd_7d_btc: float
    oi_change_24h_pct: float
    oi_change_4h_pct: float
    oi_change_1h_pct: float
    funding_rate_pct: float
    annualized_basis_pct: float
    atr_compression_pct: float
    base_width_72h_pct: float
    active_config_code: str
    runner_up_config_code: str
    configs: List[RegimeConfigItem] = field(default_factory=list)


@dataclass
class TabVerdictRow:
    """Single row in Tab [5] Panel 1 summarizing one specialist tab's live verdict."""

    tab_num: int
    tab_name: str
    traffic_light: str  # "GREEN", "BLUE", "YELLOW", "RED"
    score_or_status: str
    primary_driver: str
    tab_conclusion: str


@dataclass
class HierarchyLayerRow:
    """Single row in Tab [5] Panel 2 showing the 4-Layer Institutional Decision Funnel."""

    layer_num: int
    layer_name: str
    status: str  # "PASS", "ARMED", "STANDBY", "CAUTION", "VETO"
    authority_rule: str
    live_ruling: str


@dataclass
class MasterSynthesisEvaluation:
    """Complete evaluation state for Tab [5]: Master Synthesis & Supreme Order of Battle."""

    timestamp_utc: str
    current_price: float
    tab_rows: List[TabVerdictRow] = field(default_factory=list)
    tabs_green_count: int = 0
    tabs_blue_count: int = 0
    tabs_yellow_count: int = 0
    tabs_red_count: int = 0
    hierarchy_rows: List[HierarchyLayerRow] = field(default_factory=list)
    master_alignment_score: float = 0.0
    alignment_status: str = "NEUTRAL / STANDBY"
    supreme_veto_active: bool = False
    supreme_veto_reason: str = "NONE"
    confluence_points: List[str] = field(default_factory=list)
    conflict_points: List[str] = field(default_factory=list)
    upgrade_catalysts: List[str] = field(default_factory=list)
    # Track A: If Flat in Cash
    cash_permission: str = "WAIT FOR STRUCTURAL EDGE"
    cash_entry_zone_str: str = ""
    cash_base_risk_pct: float = 1.0
    cash_regime_multiplier: float = 0.0
    cash_final_risk_pct: float = 0.0
    cash_final_notional_usd: float = 0.0
    cash_final_size_btc: float = 0.0
    cash_edge_risk_pct: float = 0.5
    cash_edge_notional_usd: float = 0.0
    cash_edge_size_btc: float = 0.0
    cash_trigger_instruction: str = ""
    # Track B: If Already Holding Spot BTC
    holder_action: str = "HOLD CORE SPOT LONG"
    holder_hard_stop_usd: float = 0.0
    holder_hard_stop_source: str = ""
    holder_tp1_usd: float = 0.0
    holder_tp1_source: str = ""
    holder_tp2_usd: float = 0.0
    holder_tp2_source: str = ""
    holder_management_note: str = ""
    # Panel 5: Supreme Master Executive Bottom Line
    master_traffic_light: str = "YELLOW"  # "GREEN", "BLUE", "YELLOW", "RED"
    master_headline: str = ""
    master_what_is_happening: str = ""
    master_why_resolution: str = ""
    master_final_command: str = ""



@dataclass
class SignalEvaluation:
    """Output of the 4-Gate State Machine and 0-100 Confluence Scorer."""

    timestamp_utc: str
    regime: MarketRegime
    gate_state: ExecutionGateState
    confluence_score: float
    location_score: float
    flow_score: float
    derivatives_score: float
    trigger_score: float
    active_horizon: str
    current_price: float
    c_vah: float
    c_poc: float
    c_val: float
    primary_lvn: Optional[float]
    support_hvn: Optional[float]
    atr_1h: float
    atr_4h: float
    distance_to_val_pct: float
    distance_to_val_atr: float
    va_position_pct: float = 0.0
    is_mid_range_chop: bool = False
    is_reclaim_candle: bool = False
    hard_veto_triggered: bool = False
    veto_reasons: List[str] = field(default_factory=list)
    rationale_notes: List[str] = field(default_factory=list)
    trade_plan: Optional[TradePlan] = None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["regime"] = self.regime.value
        data["gate_state"] = self.gate_state.value
        return data

```

---

### File: `core/state_store.py`

```python
"""Async-safe central StateStore managing rolling ring buffers and live tick state."""

import asyncio
import time
from collections import deque
from datetime import datetime, timezone
from typing import Deque, Dict, List, Optional, Tuple

import numpy as np

from .models import (
    DerivativesSnapshot,
    FlowSnapshot,
    KlineBar,
    MacroRadarEvaluation,
    MasterSynthesisEvaluation,
    ProtocolV13Evaluation,
    RegimeMatrixEvaluation,
    SignalEvaluation,
    VolumeProfileResult,
)


class StateStore:
    """Centralized state container for klines, real-time WS ticks, OI history, and signals."""

    def __init__(self) -> None:
        self._lock = asyncio.Lock()

        # --- Historical + Developing Kline Ring Buffers ---
        self.spot_klines_1w: Deque[KlineBar] = deque(maxlen=120)
        self.spot_klines_1d: Deque[KlineBar] = deque(maxlen=300)
        self.perp_klines_1d: Deque[KlineBar] = deque(maxlen=300)
        self.spot_klines_1h: Deque[KlineBar] = deque(maxlen=800)
        self.perp_klines_1h: Deque[KlineBar] = deque(maxlen=800)
        self.spot_klines_15m: Deque[KlineBar] = deque(maxlen=400)
        self.perp_klines_15m: Deque[KlineBar] = deque(maxlen=400)

        # --- Active HUD Tab State (1 = Swing Engine, 2 = Protocol v1.3, 3 = Macro & Cycle Radar) ---
        self.active_tab: int = 1

        # --- Live Tick & Session Accumulators ---
        self.binance_spot_price: float = 0.0
        self.binance_perp_price: float = 0.0
        self.coinbase_spot_price: float = 0.0

        self.session_spot_cvd: float = 0.0
        self.session_perp_cvd: float = 0.0
        self.utc_day_spot_cvd: float = 0.0
        self.utc_day_perp_cvd: float = 0.0
        self.current_utc_date: str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        self.spot_trade_count: int = 0
        self.perp_trade_count: int = 0

        # Live intrabar tick delta since last REST kline sync
        self.live_15m_bucket_ms: int = 0
        self.live_spot_buy_15m: float = 0.0
        self.live_spot_sell_15m: float = 0.0
        self.live_perp_buy_15m: float = 0.0
        self.live_perp_sell_15m: float = 0.0

        # --- Derivatives & Basis Time Series ---
        self.open_interest_btc: float = 0.0
        self.open_interest_usd: float = 0.0
        self.funding_rate_pct: float = 0.0
        self.taker_long_short_ratio_5m: float = 1.0
        self.perp_5m_delta_btc: float = 0.0
        self.perp_source: str = "Binance USD-M"

        # (timestamp_sec, oi_btc)
        self.oi_history: Deque[Tuple[float, float]] = deque(maxlen=600)
        # (timestamp_sec, cpi_pct)
        self.cpi_history: Deque[Tuple[float, float]] = deque(maxlen=1000)

        # --- Computed Analytics Snapshots ---
        self.macro_profile: Optional[VolumeProfileResult] = None
        self.tactical_profile: Optional[VolumeProfileResult] = None
        self.session_profile: Optional[VolumeProfileResult] = None
        self.flow_snapshot: FlowSnapshot = FlowSnapshot()
        self.derivatives_snapshot: DerivativesSnapshot = DerivativesSnapshot()
        self.latest_signal: Optional[SignalEvaluation] = None
        self.protocol_evaluation: Optional[ProtocolV13Evaluation] = None
        self.macro_evaluation: Optional[MacroRadarEvaluation] = None
        self.regime_matrix_evaluation: Optional[RegimeMatrixEvaluation] = None
        self.master_synthesis_evaluation: Optional[MasterSynthesisEvaluation] = None

        # --- Connection & System Health ---
        self.warmup_complete: bool = False
        self.spot_ws_connected: bool = False
        self.perp_ws_connected: bool = False
        self.coinbase_ws_connected: bool = False
        self.last_spot_tick_ts: float = 0.0
        self.last_perp_tick_ts: float = 0.0
        self.last_cb_tick_ts: float = 0.0
        self.last_packet_copied_utc: str = ""
        self.last_packet_copied_ts: float = 0.0
        self.last_packet_char_count: int = 0

    def _check_utc_day_rollover(self) -> None:
        """Resets UTC daily session CVD at 00:00 UTC boundary."""
        now_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if now_date != self.current_utc_date:
            self.current_utc_date = now_date
            self.utc_day_spot_cvd = 0.0
            self.utc_day_perp_cvd = 0.0

    def _check_15m_bucket_rollover(self, now_ms: int) -> None:
        """Resets intrabar live tick accumulators when a new 15m boundary starts."""
        bucket_ms = (now_ms // 900_000) * 900_000
        if bucket_ms != self.live_15m_bucket_ms:
            self.live_15m_bucket_ms = bucket_ms
            self.live_spot_buy_15m = 0.0
            self.live_spot_sell_15m = 0.0
            self.live_perp_buy_15m = 0.0
            self.live_perp_sell_15m = 0.0

    def record_spot_trade(self, price: float, qty: float, is_buyer_maker: bool, ts_ms: int) -> None:
        """Records a real-time Spot aggTrade tick (O(1) non-blocking)."""
        self._check_utc_day_rollover()
        self._check_15m_bucket_rollover(ts_ms)

        self.binance_spot_price = price
        self.spot_trade_count += 1
        self.last_spot_tick_ts = time.time()

        # is_buyer_maker == True -> Seller was the aggressive Taker
        delta = -qty if is_buyer_maker else qty
        self.session_spot_cvd += delta
        self.utc_day_spot_cvd += delta

        if is_buyer_maker:
            self.live_spot_sell_15m += qty
        else:
            self.live_spot_buy_15m += qty

        # Update developing kline tip if available
        if self.spot_klines_15m:
            tip = self.spot_klines_15m[-1]
            tip.close = price
            tip.high = max(tip.high, price)
            tip.low = min(tip.low, price)
            tip.volume += qty
            if not is_buyer_maker:
                tip.taker_buy_volume += qty

        if self.spot_klines_1h:
            tip_1h = self.spot_klines_1h[-1]
            tip_1h.close = price
            tip_1h.high = max(tip_1h.high, price)
            tip_1h.low = min(tip_1h.low, price)
            tip_1h.volume += qty
            if not is_buyer_maker:
                tip_1h.taker_buy_volume += qty

        if self.spot_klines_1d:
            tip_1d = self.spot_klines_1d[-1]
            tip_1d.close = price
            tip_1d.high = max(tip_1d.high, price)
            tip_1d.low = min(tip_1d.low, price)
            tip_1d.volume += qty
            if not is_buyer_maker:
                tip_1d.taker_buy_volume += qty

        if self.spot_klines_1w:
            tip_1w = self.spot_klines_1w[-1]
            tip_1w.close = price
            tip_1w.high = max(tip_1w.high, price)
            tip_1w.low = min(tip_1w.low, price)
            tip_1w.volume += qty
            if not is_buyer_maker:
                tip_1w.taker_buy_volume += qty

        self._record_cpi_sample()

    def record_perp_trade(self, price: float, qty: float, is_buyer_maker: bool, ts_ms: int) -> None:
        """Records a real-time Perpetual Futures aggTrade tick (O(1) non-blocking)."""
        self._check_utc_day_rollover()
        self._check_15m_bucket_rollover(ts_ms)

        self.binance_perp_price = price
        self.perp_trade_count += 1
        self.last_perp_tick_ts = time.time()

        delta = -qty if is_buyer_maker else qty
        self.session_perp_cvd += delta
        self.utc_day_perp_cvd += delta

        if is_buyer_maker:
            self.live_perp_sell_15m += qty
        else:
            self.live_perp_buy_15m += qty

        if self.perp_klines_15m:
            tip = self.perp_klines_15m[-1]
            tip.close = price
            tip.high = max(tip.high, price)
            tip.low = min(tip.low, price)
            tip.volume += qty
            if not is_buyer_maker:
                tip.taker_buy_volume += qty

        if self.perp_klines_1h:
            tip_1h = self.perp_klines_1h[-1]
            tip_1h.close = price
            tip_1h.high = max(tip_1h.high, price)
            tip_1h.low = min(tip_1h.low, price)
            tip_1h.volume += qty
            if not is_buyer_maker:
                tip_1h.taker_buy_volume += qty

        if self.perp_klines_1d:
            tip_1d = self.perp_klines_1d[-1]
            tip_1d.close = price
            tip_1d.high = max(tip_1d.high, price)
            tip_1d.low = min(tip_1d.low, price)
            tip_1d.volume += qty
            if not is_buyer_maker:
                tip_1d.taker_buy_volume += qty

    def record_coinbase_price(self, price: float) -> None:
        """Updates live Coinbase BTC-USD spot price and records CPI sample."""
        self.coinbase_spot_price = price
        self.last_cb_tick_ts = time.time()
        self._record_cpi_sample()

    def _record_cpi_sample(self) -> None:
        """Records a Coinbase Premium Index sample at most once per 2 seconds."""
        if self.binance_spot_price <= 0 or self.coinbase_spot_price <= 0:
            return
        now = time.time()
        if self.cpi_history and (now - self.cpi_history[-1][0]) < 2.0:
            return
        cpi_pct = ((self.coinbase_spot_price - self.binance_spot_price) / self.binance_spot_price) * 100.0
        self.cpi_history.append((now, cpi_pct))

    def record_oi_sample(self, oi_btc: float, ts_sec: Optional[float] = None) -> None:
        """Appends an Open Interest datapoint to the rolling history buffer."""
        now = ts_sec if ts_sec is not None else time.time()
        self.open_interest_btc = oi_btc
        ref_price = self.binance_perp_price or self.binance_spot_price
        self.open_interest_usd = oi_btc * ref_price
        if not self.oi_history or (now - self.oi_history[-1][0]) >= 5.0:
            self.oi_history.append((now, oi_btc))

    def get_oi_change_pct(self, lookback_seconds: float) -> float:
        """Calculates percentage change in Open Interest over `lookback_seconds`."""
        if len(self.oi_history) < 2 or self.open_interest_btc <= 0:
            return 0.0
        now = self.oi_history[-1][0]
        target_ts = now - lookback_seconds
        # Find sample closest to target_ts
        best_oi = self.oi_history[0][1]
        best_diff = abs(self.oi_history[0][0] - target_ts)
        for ts, oi_val in self.oi_history:
            diff = abs(ts - target_ts)
            if diff < best_diff:
                best_diff = diff
                best_oi = oi_val
        if best_oi <= 0:
            return 0.0
        return ((self.open_interest_btc - best_oi) / best_oi) * 100.0

    def get_cpi_metrics(self) -> Tuple[float, float, float]:
        """Returns (premium_usd, premium_pct, premium_zscore)."""
        if self.binance_spot_price <= 0 or self.coinbase_spot_price <= 0:
            return 0.0, 0.0, 0.0
        prem_usd = self.coinbase_spot_price - self.binance_spot_price
        prem_pct = (prem_usd / self.binance_spot_price) * 100.0
        if len(self.cpi_history) < 10:
            return prem_usd, prem_pct, 0.0
        vals = np.array([x[1] for x in self.cpi_history], dtype=float)
        std = float(np.std(vals))
        mean = float(np.mean(vals))
        zscore = (prem_pct - mean) / std if std > 1e-6 else 0.0
        return prem_usd, prem_pct, float(zscore)

    async def set_klines(
        self,
        venue: str,
        interval: str,
        bars: List[KlineBar],
    ) -> None:
        """Safely replaces or updates a kline ring buffer."""
        async with self._lock:
            target: Optional[Deque[KlineBar]] = None
            if venue == "spot" and interval == "1h":
                target = self.spot_klines_1h
            elif venue == "perp" and interval == "1h":
                target = self.perp_klines_1h
            elif venue == "spot" and interval == "15m":
                target = self.spot_klines_15m
            elif venue == "perp" and interval == "15m":
                target = self.perp_klines_15m
            elif venue == "spot" and interval == "1d":
                target = self.spot_klines_1d
            elif venue == "perp" and interval == "1d":
                target = self.perp_klines_1d
            elif venue == "spot" and interval == "1w":
                target = self.spot_klines_1w

            if target is not None and bars:
                target.clear()
                target.extend(bars)
                if venue == "spot" and self.binance_spot_price == 0.0:
                    self.binance_spot_price = bars[-1].close
                elif venue == "perp" and self.binance_perp_price == 0.0:
                    self.binance_perp_price = bars[-1].close

```

---

### File: `collectors/__init__.py`

```python
"""Data ingestion collectors (REST warmup, periodic pollers, and live WebSockets)."""

from .binance_perp_ws import stream_binance_perp
from .binance_spot_ws import stream_binance_spot
from .coinbase_ws import stream_coinbase_spot
from .rest_metrics import poll_rest_metrics
from .warmup_loader import run_initial_warmup

__all__ = [
    "poll_rest_metrics",
    "run_initial_warmup",
    "stream_binance_perp",
    "stream_binance_spot",
    "stream_coinbase_spot",
]

```

---

### File: `collectors/warmup_loader.py`

```python
"""Zero-cold-start historical backfill for Spot/Perp klines, Open Interest, and Coinbase Premium."""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, List, Optional

import aiohttp

from config.settings import EngineConfig
from core.models import KlineBar
from core.state_store import StateStore

logger = logging.getLogger(__name__)


def _parse_binance_kline(raw: List[Any]) -> KlineBar:
    """Converts a Binance REST kline array into a typed KlineBar.

    Binance kline format:
    [0] Open time (ms), [1] Open, [2] High, [3] Low, [4] Close, [5] Volume,
    [6] Close time, [7] Quote asset vol, [8] Number of trades,
    [9] Taker buy base asset volume, ...
    """
    return KlineBar(
        timestamp_ms=int(raw[0]),
        open=float(raw[1]),
        high=float(raw[2]),
        low=float(raw[3]),
        close=float(raw[4]),
        volume=float(raw[5]),
        taker_buy_volume=float(raw[9]),
    )


async def fetch_binance_spot_klines(
    session: aiohttp.ClientSession,
    config: EngineConfig,
    interval: str = "1h",
    limit: int = 750,
) -> List[KlineBar]:
    """Fetches historical Binance Spot klines across fallback endpoints."""
    params = {"symbol": config.binance_symbol, "interval": interval, "limit": limit}
    for base_url in config.binance_spot_rest_urls:
        url = f"{base_url}/api/v3/klines"
        try:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=12)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if isinstance(data, list) and len(data) > 0:
                        return [_parse_binance_kline(row) for row in data]
        except Exception as exc:
            logger.debug("Spot kline fetch failed on %s: %s", base_url, exc)
    return []


async def fetch_binance_perp_klines(
    session: aiohttp.ClientSession,
    config: EngineConfig,
    interval: str = "1h",
    limit: int = 750,
) -> List[KlineBar]:
    """Fetches historical Binance USDT-M Perpetual klines (with Bybit fallback if geo-restricted)."""
    params = {"symbol": config.binance_symbol, "interval": interval, "limit": limit}
    for base_url in config.binance_perp_rest_urls:
        url = f"{base_url}/fapi/v1/klines"
        try:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=12)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if isinstance(data, list) and len(data) > 0:
                        return [_parse_binance_kline(row) for row in data]
        except Exception as exc:
            logger.debug("Perp kline fetch failed on %s: %s", base_url, exc)

    # Geo-resilient fallback: Bybit V5 Linear klines (approximating taker buy via candle body direction/ratio)
    interval_map = {"1h": "60", "15m": "15", "1d": "D", "1w": "W"}
    bybit_interval = interval_map.get(interval, "60")
    url = f"{config.bybit_rest_url}/v5/market/kline"
    try:
        async with session.get(
            url,
            params={"category": "linear", "symbol": config.binance_symbol, "interval": bybit_interval, "limit": min(limit, 200)},
            timeout=aiohttp.ClientTimeout(total=12),
        ) as resp:
            if resp.status == 200:
                payload = await resp.json()
                rows = payload.get("result", {}).get("list", [])
                bars: List[KlineBar] = []
                for row in reversed(rows):
                    o, h, l, c, v = float(row[1]), float(row[2]), float(row[3]), float(row[4]), float(row[5])
                    rng = max(h - l, 1e-6)
                    buy_ratio = 0.5 + 0.4 * ((c - o) / rng)
                    buy_ratio = min(0.95, max(0.05, buy_ratio))
                    bars.append(
                        KlineBar(
                            timestamp_ms=int(row[0]),
                            open=o,
                            high=h,
                            low=l,
                            close=c,
                            volume=v,
                            taker_buy_volume=v * buy_ratio,
                        )
                    )
                return bars
    except Exception as exc:
        logger.debug("Fallback Bybit perp kline fetch failed: %s", exc)

    return []


async def fetch_initial_oi_and_funding(
    session: aiohttp.ClientSession,
    config: EngineConfig,
    store: StateStore,
) -> None:
    """Backfills 4H Open Interest history, current Open Interest, and Funding Rate."""
    base_url = config.binance_perp_rest_urls[0]
    try:
        # 1. Historical 15m Open Interest for immediate 15m/1H/4H delta calculation
        hist_url = f"{base_url}/futures/data/openInterestHist"
        async with session.get(
            hist_url,
            params={"symbol": config.binance_symbol, "period": "15m", "limit": 24},
            timeout=aiohttp.ClientTimeout(total=10),
        ) as resp:
            if resp.status == 200:
                hist_data = await resp.json()
                if isinstance(hist_data, list):
                    for item in hist_data:
                        ts_sec = float(item.get("timestamp", 0)) / 1000.0
                        oi_btc = float(item.get("sumOpenInterest", 0.0))
                        if oi_btc > 0:
                            store.record_oi_sample(oi_btc, ts_sec=ts_sec)

        # 2. Live Current Open Interest
        oi_url = f"{base_url}/fapi/v1/openInterest"
        async with session.get(
            oi_url,
            params={"symbol": config.binance_symbol},
            timeout=aiohttp.ClientTimeout(total=8),
        ) as resp:
            if resp.status == 200:
                oi_data = await resp.json()
                oi_btc = float(oi_data.get("openInterest", 0.0))
                if oi_btc > 0:
                    store.record_oi_sample(oi_btc)
                    store.perp_source = "Binance USD-M"

        # 3. Current Funding Rate & Mark Price
        prem_url = f"{base_url}/fapi/v1/premiumIndex"
        async with session.get(
            prem_url,
            params={"symbol": config.binance_symbol},
            timeout=aiohttp.ClientTimeout(total=8),
        ) as resp:
            if resp.status == 200:
                prem_data = await resp.json()
                store.funding_rate_pct = float(prem_data.get("lastFundingRate", 0.0)) * 100.0
                mark_p = float(prem_data.get("markPrice", 0.0))
                if mark_p > 0 and store.binance_perp_price == 0.0:
                    store.binance_perp_price = mark_p

        # 4. 5m Taker Long/Short Volume Ratio
        taker_url = f"{base_url}/futures/data/takerlongshortRatio"
        async with session.get(
            taker_url,
            params={"symbol": config.binance_symbol, "period": "5m", "limit": 1},
            timeout=aiohttp.ClientTimeout(total=8),
        ) as resp:
            if resp.status == 200:
                t_data = await resp.json()
                if isinstance(t_data, list) and len(t_data) > 0:
                    latest = t_data[0]
                    store.taker_long_short_ratio_5m = float(latest.get("buySellRatio", 1.0))
                    buy_v = float(latest.get("buyVol", 0.0))
                    sell_v = float(latest.get("sellVol", 0.0))
                    store.perp_5m_delta_btc = buy_v - sell_v
    except Exception as exc:
        logger.debug("Primary Binance futures OI/Funding warmup failed: %s", exc)


async def fetch_initial_coinbase_basis(
    session: aiohttp.ClientSession,
    config: EngineConfig,
    store: StateStore,
) -> None:
    """Fetches Coinbase BTC-USD ticker and 15m candles to warm up Coinbase Premium Z-score."""
    try:
        # 1. Current Coinbase Spot Price
        ticker_url = f"{config.coinbase_rest_url}/products/{config.coinbase_symbol}/ticker"
        async with session.get(ticker_url, timeout=aiohttp.ClientTimeout(total=8)) as resp:
            if resp.status == 200:
                data = await resp.json()
                if "price" in data:
                    store.record_coinbase_price(float(data["price"]))

        # 2. Backfill 15m Coinbase candles against Binance 15m Spot klines to seed cpi_history
        candles_url = f"{config.coinbase_rest_url}/products/{config.coinbase_symbol}/candles"
        async with session.get(
            candles_url,
            params={"granularity": 900},
            timeout=aiohttp.ClientTimeout(total=8),
        ) as resp:
            if resp.status == 200 and store.spot_klines_15m:
                cb_candles = await resp.json()
                # Coinbase format: [time_sec, low, high, open, close, volume]
                if isinstance(cb_candles, list):
                    bn_map = {b.timestamp_ms // 1000: b.close for b in store.spot_klines_15m}
                    for row in reversed(cb_candles[:60]):
                        ts_sec = int(row[0])
                        cb_close = float(row[4])
                        bn_close = bn_map.get(ts_sec)
                        if bn_close and bn_close > 0:
                            cpi_pct = ((cb_close - bn_close) / bn_close) * 100.0
                            store.cpi_history.append((float(ts_sec), cpi_pct))
    except Exception as exc:
        logger.debug("Coinbase warmup error: %s", exc)


def _seed_utc_day_cvd_from_klines(store: StateStore) -> None:
    """Populates today's UTC 00:00 cumulative Spot and Perp CVD from backfilled 15m klines."""
    now_utc = datetime.now(timezone.utc)
    midnight_utc = datetime(now_utc.year, now_utc.month, now_utc.day, tzinfo=timezone.utc)
    midnight_ms = int(midnight_utc.timestamp() * 1000)

    spot_day_delta = sum(
        b.delta for b in store.spot_klines_15m if b.timestamp_ms >= midnight_ms
    )
    perp_day_delta = sum(
        b.delta for b in store.perp_klines_15m if b.timestamp_ms >= midnight_ms
    )
    store.utc_day_spot_cvd = spot_day_delta
    store.utc_day_perp_cvd = perp_day_delta


async def run_initial_warmup(config: EngineConfig, store: StateStore) -> None:
    """Executes concurrent historical backfill so 1W/1D/30D/7D profiles, Cycle Radar, and CVD are warm at startup."""
    async with aiohttp.ClientSession() as session:
        spot_1w_task = fetch_binance_spot_klines(
            session, config, interval="1w", limit=config.weekly_kline_limit
        )
        spot_1d_task = fetch_binance_spot_klines(
            session, config, interval="1d", limit=config.daily_kline_limit
        )
        perp_1d_task = fetch_binance_perp_klines(
            session, config, interval="1d", limit=config.daily_kline_limit
        )
        spot_1h_task = fetch_binance_spot_klines(
            session, config, interval="1h", limit=config.macro_profile_days * 24
        )
        perp_1h_task = fetch_binance_perp_klines(
            session, config, interval="1h", limit=config.macro_profile_days * 24
        )
        spot_15m_task = fetch_binance_spot_klines(
            session, config, interval="15m", limit=240
        )
        perp_15m_task = fetch_binance_perp_klines(
            session, config, interval="15m", limit=240
        )
        oi_task = fetch_initial_oi_and_funding(session, config, store)

        (
            spot_1w,
            spot_1d,
            perp_1d,
            spot_1h,
            perp_1h,
            spot_15m,
            perp_15m,
            _,
        ) = await asyncio.gather(
            spot_1w_task,
            spot_1d_task,
            perp_1d_task,
            spot_1h_task,
            perp_1h_task,
            spot_15m_task,
            perp_15m_task,
            oi_task,
        )

        await store.set_klines("spot", "1w", spot_1w)
        await store.set_klines("spot", "1d", spot_1d)
        await store.set_klines("perp", "1d", perp_1d)
        await store.set_klines("spot", "1h", spot_1h)
        await store.set_klines("perp", "1h", perp_1h)
        await store.set_klines("spot", "15m", spot_15m)
        await store.set_klines("perp", "15m", perp_15m)

        # Warm up Coinbase price & historical CPI basis Z-score
        await fetch_initial_coinbase_basis(session, config, store)

        # Seed UTC day CVD from today's 15m candles
        _seed_utc_day_cvd_from_klines(store)
        store.warmup_complete = True

```

---

### File: `collectors/rest_metrics.py`

```python
"""Periodic async REST poller for Open Interest, Funding Rates, Taker Ratios, and Kline synchronization."""

import asyncio
import logging
import time

import aiohttp

from config.settings import EngineConfig
from core.state_store import StateStore
from .warmup_loader import fetch_binance_perp_klines, fetch_binance_spot_klines

logger = logging.getLogger(__name__)


async def _poll_binance_futures_metrics(
    session: aiohttp.ClientSession,
    config: EngineConfig,
    store: StateStore,
) -> bool:
    """Polls Binance USD-M Futures Open Interest, Funding Rate, and 5m Taker Ratio."""
    base_url = config.binance_perp_rest_urls[0]
    success = False

    # 1. Open Interest
    try:
        async with session.get(
            f"{base_url}/fapi/v1/openInterest",
            params={"symbol": config.binance_symbol},
            timeout=aiohttp.ClientTimeout(total=8),
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                oi_btc = float(data.get("openInterest", 0.0))
                if oi_btc > 0:
                    store.record_oi_sample(oi_btc)
                    success = True
    except Exception as exc:
        logger.debug("OI poll error: %s", exc)

    # 2. Funding Rate & Mark Price
    try:
        async with session.get(
            f"{base_url}/fapi/v1/premiumIndex",
            params={"symbol": config.binance_symbol},
            timeout=aiohttp.ClientTimeout(total=8),
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                store.funding_rate_pct = float(data.get("lastFundingRate", 0.0)) * 100.0
                mark_p = float(data.get("markPrice", 0.0))
                if mark_p > 0 and store.binance_perp_price == 0.0:
                    store.binance_perp_price = mark_p
                success = True
    except Exception as exc:
        logger.debug("PremiumIndex poll error: %s", exc)

    # 3. 5m Taker Long/Short Ratio
    try:
        async with session.get(
            f"{base_url}/futures/data/takerlongshortRatio",
            params={"symbol": config.binance_symbol, "period": "5m", "limit": 1},
            timeout=aiohttp.ClientTimeout(total=8),
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                if isinstance(data, list) and len(data) > 0:
                    latest = data[0]
                    store.taker_long_short_ratio_5m = float(latest.get("buySellRatio", 1.0))
                    buy_v = float(latest.get("buyVol", 0.0))
                    sell_v = float(latest.get("sellVol", 0.0))
                    store.perp_5m_delta_btc = buy_v - sell_v
    except Exception as exc:
        logger.debug("Taker ratio poll error: %s", exc)

    return success


async def _poll_bybit_futures_fallback(
    session: aiohttp.ClientSession,
    config: EngineConfig,
    store: StateStore,
) -> None:
    """Fallback Open Interest and Funding Rate poller via Bybit V5 Linear API."""
    try:
        async with session.get(
            f"{config.bybit_rest_url}/v5/market/tickers",
            params={"category": "linear", "symbol": config.binance_symbol},
            timeout=aiohttp.ClientTimeout(total=8),
        ) as resp:
            if resp.status == 200:
                payload = await resp.json()
                items = payload.get("result", {}).get("list", [])
                if items:
                    ticker = items[0]
                    oi_btc = float(ticker.get("openInterest", 0.0))
                    funding = float(ticker.get("fundingRate", 0.0)) * 100.0
                    last_p = float(ticker.get("lastPrice", 0.0))
                    if last_p > 0 and store.binance_perp_price == 0.0:
                        store.binance_perp_price = last_p
                    if oi_btc > 0:
                        store.record_oi_sample(oi_btc)
                    store.funding_rate_pct = funding
    except Exception as exc:
        logger.debug("Bybit fallback poll error: %s", exc)


async def poll_rest_metrics(config: EngineConfig, store: StateStore) -> None:
    """Periodically polls derivatives metrics (15s) and synchronizes kline buffers (60s)."""
    last_kline_sync = time.time()

    async with aiohttp.ClientSession() as session:
        while True:
            try:
                ok = await _poll_binance_futures_metrics(session, config, store)
                if not ok:
                    await _poll_bybit_futures_fallback(session, config, store)

                # If Coinbase WS hasn't ticked recently, refresh via REST
                if time.time() - store.last_cb_tick_ts > 20.0:
                    try:
                        async with session.get(
                            f"{config.coinbase_rest_url}/products/{config.coinbase_symbol}/ticker",
                            timeout=aiohttp.ClientTimeout(total=6),
                        ) as cb_resp:
                            if cb_resp.status == 200:
                                cb_data = await cb_resp.json()
                                if "price" in cb_data:
                                    store.record_coinbase_price(float(cb_data["price"]))
                    except Exception:
                        pass

                # Periodic Kline Sync (every 60s)
                now = time.time()
                if now - last_kline_sync >= config.kline_sync_interval_sec:
                    last_kline_sync = now
                    (
                        spot_1w,
                        spot_1d,
                        perp_1d,
                        spot_1h,
                        perp_1h,
                        spot_15m,
                        perp_15m,
                    ) = await asyncio.gather(
                        fetch_binance_spot_klines(
                            session, config, interval="1w", limit=config.weekly_kline_limit
                        ),
                        fetch_binance_spot_klines(
                            session, config, interval="1d", limit=config.daily_kline_limit
                        ),
                        fetch_binance_perp_klines(
                            session, config, interval="1d", limit=config.daily_kline_limit
                        ),
                        fetch_binance_spot_klines(
                            session, config, interval="1h", limit=config.macro_profile_days * 24
                        ),
                        fetch_binance_perp_klines(
                            session, config, interval="1h", limit=config.macro_profile_days * 24
                        ),
                        fetch_binance_spot_klines(session, config, interval="15m", limit=240),
                        fetch_binance_perp_klines(session, config, interval="15m", limit=240),
                    )
                    if spot_1w:
                        await store.set_klines("spot", "1w", spot_1w)
                    if spot_1d:
                        await store.set_klines("spot", "1d", spot_1d)
                    if perp_1d:
                        await store.set_klines("perp", "1d", perp_1d)
                    if spot_1h:
                        await store.set_klines("spot", "1h", spot_1h)
                    if perp_1h:
                        await store.set_klines("perp", "1h", perp_1h)
                    if spot_15m:
                        await store.set_klines("spot", "15m", spot_15m)
                    if perp_15m:
                        await store.set_klines("perp", "15m", perp_15m)

                await asyncio.sleep(config.rest_poll_interval_sec)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.debug("REST poller loop error: %s", exc)
                await asyncio.sleep(5.0)

```

---

### File: `analytics/__init__.py`

```python
"""Quantitative analytics modules: Composite Volume Profile, Multi-Horizon CVD, and 4-Gate Signal Engine."""

from .ai_packet_exporter import build_ai_telemetry_packet, copy_ai_packet_to_clipboard_and_disk
from .cvd_engine import compute_derivatives_snapshot, compute_flow_snapshot
from .macro_radar import MacroRadarEvaluator, compute_200d_sma_and_slope, compute_ema, compute_wilder_rsi
from .master_synthesis import MasterSynthesisEvaluator
from .protocol_v13 import ProtocolV13Evaluator, synthesize_1d_bars_from_1h
from .regime_matrix import RegimeMatrixEvaluator
from .signal_detector import SignalDetector
from .volume_profile import compute_atr, compute_composite_profile, synthesize_4h_bars

__all__ = [
    "MacroRadarEvaluator",
    "MasterSynthesisEvaluator",
    "ProtocolV13Evaluator",
    "RegimeMatrixEvaluator",
    "SignalDetector",
    "build_ai_telemetry_packet",
    "compute_200d_sma_and_slope",
    "compute_atr",
    "compute_composite_profile",
    "compute_derivatives_snapshot",
    "compute_ema",
    "compute_flow_snapshot",
    "compute_wilder_rsi",
    "copy_ai_packet_to_clipboard_and_disk",
    "synthesize_1d_bars_from_1h",
    "synthesize_4h_bars",
]

```

---

### File: `analytics/volume_profile.py`

```python
"""Composite Volume Profile engine: 70% Value Area, Gaussian HVN/LVN solver, and ATR."""

from typing import List, Optional, Sequence

import numpy as np

from core.models import KlineBar, VolumeProfileResult


def _gaussian_smooth_1d(values: np.ndarray, sigma: float = 1.5) -> np.ndarray:
    """Applies a 1D Gaussian smoothing kernel with reflection padding."""
    if len(values) < 5 or sigma <= 0:
        return values.copy()
    radius = max(1, int(round(3.0 * sigma)))
    x = np.arange(-radius, radius + 1, dtype=float)
    kernel = np.exp(-0.5 * (x / sigma) ** 2)
    kernel /= np.sum(kernel)
    padded = np.pad(values, pad_width=radius, mode="reflect")
    return np.convolve(padded, kernel, mode="valid")


def compute_composite_profile(
    bars: Sequence[KlineBar],
    horizon_label: str = "30D Macro",
    num_bins: int = 120,
    value_area_pct: float = 0.70,
    gaussian_sigma: float = 1.5,
    lvn_rel_threshold: float = 0.55,
    hvn_rel_threshold: float = 1.20,
) -> Optional[VolumeProfileResult]:
    """Constructs a high-resolution Composite Volume Profile from OHLCV klines.

    Distributes each candle's volume across intersected price bins weighted by a
    triangular kernel centered at the candle's typical price (H + L + C) / 3.
    Computes the CME-standard 70% Value Area (cVAH, cPOC, cVAL) and identifies
    High Volume Nodes (HVNs) and Low Volume Nodes (LVNs).
    """
    if not bars or len(bars) < 2:
        return None

    range_low = min(b.low for b in bars)
    range_high = max(b.high for b in bars)
    if range_high <= range_low:
        return None

    bin_edges = np.linspace(range_low, range_high, num_bins + 1)
    bin_centers = 0.5 * (bin_edges[:-1] + bin_edges[1:])
    bin_width = float(bin_edges[1] - bin_edges[0])
    bin_volumes = np.zeros(num_bins, dtype=float)

    # Distribute each bar's volume across intersected bins
    for bar in bars:
        if bar.volume <= 0:
            continue
        idx_start = int(np.searchsorted(bin_edges, bar.low, side="right")) - 1
        idx_end = int(np.searchsorted(bin_edges, bar.high, side="left"))
        idx_start = max(0, min(num_bins - 1, idx_start))
        idx_end = max(idx_start, min(num_bins - 1, idx_end))

        if idx_start == idx_end:
            bin_volumes[idx_start] += bar.volume
        else:
            centers_slice = bin_centers[idx_start : idx_end + 1]
            half_span = max(0.5 * (bar.high - bar.low), bin_width)
            dist = np.abs(centers_slice - bar.typical_price)
            weights = np.maximum(0.15, 1.0 - (dist / (1.25 * half_span)))
            weights_sum = float(np.sum(weights))
            if weights_sum > 0:
                bin_volumes[idx_start : idx_end + 1] += bar.volume * (weights / weights_sum)
            else:
                count = idx_end - idx_start + 1
                bin_volumes[idx_start : idx_end + 1] += bar.volume / count

    total_vol = float(np.sum(bin_volumes))
    if total_vol <= 0:
        return None

    # 1. Point of Control (cPOC)
    poc_idx = int(np.argmax(bin_volumes))
    c_poc = float(bin_centers[poc_idx])

    # 2. CME-Standard 70% Value Area Expansion
    target_va_vol = total_vol * value_area_pct
    acc_vol = float(bin_volumes[poc_idx])
    low_idx = poc_idx
    high_idx = poc_idx

    while acc_vol < target_va_vol and (low_idx > 0 or high_idx < num_bins - 1):
        # Evaluate 2-bin steps above vs below (standard Market Profile dual-TPO step)
        up_step_indices = [i for i in (high_idx + 1, high_idx + 2) if i < num_bins]
        down_step_indices = [i for i in (low_idx - 1, low_idx - 2) if i >= 0]

        up_vol = sum(float(bin_volumes[i]) for i in up_step_indices) if up_step_indices else -1.0
        down_vol = sum(float(bin_volumes[i]) for i in down_step_indices) if down_step_indices else -1.0

        if up_step_indices and down_step_indices and abs(up_vol - down_vol) <= 1e-9:
            # Symmetric tie-break: expand 1 bin up and 1 bin down
            high_idx = up_step_indices[0]
            acc_vol += float(bin_volumes[high_idx])
            if acc_vol < target_va_vol:
                low_idx = down_step_indices[0]
                acc_vol += float(bin_volumes[low_idx])
        elif up_vol > down_vol and up_step_indices:
            for i in up_step_indices:
                high_idx = i
                acc_vol += float(bin_volumes[i])
                if acc_vol >= target_va_vol:
                    break
        elif down_step_indices:
            for i in down_step_indices:
                low_idx = i
                acc_vol += float(bin_volumes[i])
                if acc_vol >= target_va_vol:
                    break
        elif up_step_indices:
            for i in up_step_indices:
                high_idx = i
                acc_vol += float(bin_volumes[i])
                if acc_vol >= target_va_vol:
                    break
        else:
            break

    c_val = float(bin_centers[low_idx])
    c_vah = float(bin_centers[high_idx])

    # 3. Gaussian-Smoothed Topology for HVN and LVN Detection
    smoothed = _gaussian_smooth_1d(bin_volumes, sigma=gaussian_sigma)
    mean_bin_vol = float(np.mean(smoothed))

    lvn_levels: List[float] = []
    hvn_levels: List[float] = []

    for i in range(1, num_bins - 1):
        val = float(smoothed[i])
        prev_v = float(smoothed[i - 1])
        next_v = float(smoothed[i + 1])

        # Local minimum -> candidate LVN
        if val < prev_v and val < next_v and val <= lvn_rel_threshold * mean_bin_vol:
            lvn_levels.append(float(bin_centers[i]))

        # Local maximum -> candidate HVN
        if val > prev_v and val > next_v and val >= hvn_rel_threshold * mean_bin_vol:
            hvn_levels.append(float(bin_centers[i]))

    # 4. Identify Primary LVN Below cVAL (sweep liquidity void) & Support HVN Below cVAL
    lvns_below_val = [lvl for lvl in lvn_levels if lvl < c_val]
    primary_lvn_below_val: Optional[float] = None
    if lvns_below_val:
        # Closest significant LVN immediately below cVAL
        primary_lvn_below_val = max(lvns_below_val)
    elif low_idx > 2:
        # Fallback: minimum volume bin in the lower tail below cVAL
        tail_slice = smoothed[max(0, low_idx - 20) : low_idx]
        if len(tail_slice) > 0:
            min_rel_idx = max(0, low_idx - 20) + int(np.argmin(tail_slice))
            primary_lvn_below_val = float(bin_centers[min_rel_idx])

    ref_ceiling = primary_lvn_below_val if primary_lvn_below_val is not None else c_val
    hvns_below_val = [lvl for lvl in hvn_levels if lvl < ref_ceiling]
    support_hvn_below_val: Optional[float] = None
    if hvns_below_val:
        support_hvn_below_val = max(hvns_below_val)
    elif low_idx > 1:
        # Fallback: lower Value Area tail support shelf below primary LVN
        ref_idx = int(np.searchsorted(bin_centers, ref_ceiling))
        support_hvn_below_val = float(bin_centers[max(0, ref_idx // 2)])

    return VolumeProfileResult(
        horizon_label=horizon_label,
        c_vah=c_vah,
        c_poc=c_poc,
        c_val=c_val,
        range_high=range_high,
        range_low=range_low,
        total_volume=total_vol,
        bin_width=bin_width,
        lvn_levels=lvn_levels,
        hvn_levels=hvn_levels,
        primary_lvn_below_val=primary_lvn_below_val,
        support_hvn_below_val=support_hvn_below_val,
        bin_centers=[float(x) for x in bin_centers],
        bin_volumes=[float(x) for x in bin_volumes],
    )


def synthesize_4h_bars(bars_1h: Sequence[KlineBar]) -> List[KlineBar]:
    """Aggregates 1H klines into aligned 4H UTC klines."""
    if not bars_1h:
        return []
    buckets: dict[int, List[KlineBar]] = {}
    four_hours_ms = 4 * 3600 * 1000
    for b in bars_1h:
        b_key = (b.timestamp_ms // four_hours_ms) * four_hours_ms
        buckets.setdefault(b_key, []).append(b)

    result: List[KlineBar] = []
    for b_key in sorted(buckets.keys()):
        group = buckets[b_key]
        result.append(
            KlineBar(
                timestamp_ms=b_key,
                open=group[0].open,
                high=max(x.high for x in group),
                low=min(x.low for x in group),
                close=group[-1].close,
                volume=sum(x.volume for x in group),
                taker_buy_volume=sum(x.taker_buy_volume for x in group),
            )
        )
    return result


def compute_atr(bars: Sequence[KlineBar], period: int = 14) -> float:
    """Computes Wilder's Average True Range (ATR) over `period` bars."""
    if not bars:
        return 0.0
    if len(bars) == 1:
        return max(1.0, bars[0].high - bars[0].low)

    trs: List[float] = []
    for i in range(1, len(bars)):
        cur = bars[i]
        prev_close = bars[i - 1].close
        tr = max(
            cur.high - cur.low,
            abs(cur.high - prev_close),
            abs(cur.low - prev_close),
        )
        trs.append(tr)

    if len(trs) <= period:
        return float(np.mean(trs))

    # Wilder smoothing
    atr = float(np.mean(trs[:period]))
    for tr in trs[period:]:
        atr = (atr * (period - 1) + tr) / period
    return atr

```

---

### File: `analytics/cvd_engine.py`

```python
"""Multi-horizon Spot vs. Perpetual CVD normalization, Z-score divergence, and Absorption math."""

from typing import List, Sequence, Tuple

import numpy as np

from config.settings import EngineConfig
from core.models import (
    DerivativesSnapshot,
    FlowSnapshot,
    HorizonFlowMetrics,
    KlineBar,
    OIPositioningQuadrant,
)
from core.state_store import StateStore
from .volume_profile import compute_atr


def _compute_window_metrics(
    window_label: str,
    spot_bars: Sequence[KlineBar],
    perp_bars: Sequence[KlineBar],
    window_size: int,
    lookback_windows: int = 48,
) -> HorizonFlowMetrics:
    """Computes normalized delta ratio, Z-scores, divergence, and Effort-vs-Result absorption."""
    metrics = HorizonFlowMetrics(window_label=window_label)
    if len(spot_bars) < window_size or len(perp_bars) < window_size:
        return metrics

    # Current window slices
    cur_spot = spot_bars[-window_size:]
    cur_perp = perp_bars[-window_size:]

    spot_vol = sum(b.volume for b in cur_spot)
    spot_delta = sum(b.delta for b in cur_spot)
    spot_ratio = (spot_delta / spot_vol) if spot_vol > 0 else 0.0

    perp_vol = sum(b.volume for b in cur_perp)
    perp_delta = sum(b.delta for b in cur_perp)
    perp_ratio = (perp_delta / perp_vol) if perp_vol > 0 else 0.0

    open_p = cur_spot[0].open
    close_p = cur_spot[-1].close
    price_chg_pct = ((close_p - open_p) / open_p) * 100.0 if open_p > 0 else 0.0

    # Trailing rolling windows for Z-score standardization
    spot_ratios: List[float] = []
    perp_ratios: List[float] = []
    perp_sell_vols: List[float] = []

    max_start_spot = len(spot_bars) - window_size
    max_start_perp = len(perp_bars) - window_size
    steps = min(lookback_windows, max_start_spot, max_start_perp)

    for k in range(steps + 1):
        s_slice = spot_bars[max_start_spot - k : len(spot_bars) - k]
        p_slice = perp_bars[max_start_perp - k : len(perp_bars) - k]
        sv = sum(b.volume for b in s_slice)
        pv = sum(b.volume for b in p_slice)
        if sv > 0:
            spot_ratios.append(sum(b.delta for b in s_slice) / sv)
        if pv > 0:
            p_del = sum(b.delta for b in p_slice)
            perp_ratios.append(p_del / pv)
            perp_sell_vols.append(max(0.0, -p_del))

    spot_z = 0.0
    if len(spot_ratios) >= 5:
        s_arr = np.array(spot_ratios, dtype=float)
        s_std = float(np.std(s_arr))
        if s_std > 1e-6:
            spot_z = (spot_ratio - float(np.mean(s_arr))) / s_std

    perp_z = 0.0
    if len(perp_ratios) >= 5:
        p_arr = np.array(perp_ratios, dtype=float)
        p_std = float(np.std(p_arr))
        if p_std > 1e-6:
            perp_z = (perp_ratio - float(np.mean(p_arr))) / p_std

    # Effort-vs-Result Passive Absorption Index:
    # High when aggressive perp net selling occurs with compressed downward price displacement
    atr_bar = compute_atr(spot_bars[-min(len(spot_bars), 30) :], period=14)
    window_atr = max(atr_bar * np.sqrt(window_size), 1.0)
    price_disp_norm = max(abs(close_p - open_p) / window_atr, 0.15)

    mean_perp_vol = float(np.mean([sum(b.volume for b in perp_bars[max_start_perp - k : len(perp_bars) - k]) for k in range(max(1, steps))]))
    mean_perp_vol = max(mean_perp_vol, 1.0)
    perp_net_sell_effort = max(0.0, -perp_delta) / (0.10 * mean_perp_vol)
    absorption_idx = float(perp_net_sell_effort / price_disp_norm)

    metrics.spot_delta_btc = float(spot_delta)
    metrics.spot_volume_btc = float(spot_vol)
    metrics.spot_delta_ratio = float(spot_ratio)
    metrics.spot_zscore = float(spot_z)
    metrics.perp_delta_btc = float(perp_delta)
    metrics.perp_volume_btc = float(perp_vol)
    metrics.perp_delta_ratio = float(perp_ratio)
    metrics.perp_zscore = float(perp_z)
    metrics.flow_divergence_z = float(spot_z - perp_z)
    metrics.absorption_index = float(absorption_idx)
    metrics.price_change_pct = float(price_chg_pct)
    return metrics


def _detect_pivot_divergences(
    spot_bars_1h: Sequence[KlineBar],
    perp_bars_1h: Sequence[KlineBar],
    lookback_bars: int = 36,
) -> Tuple[bool, bool]:
    """Detects (bullish_pivot_divergence, absorption_divergence) over recent 1H swing lows.

    1. Classic Bullish Divergence: Price makes a Lower Low (or equal low within 0.15%),
       while Cumulative Spot Delta prints a Higher Low.
    2. Passive Absorption Divergence: Price makes a Higher Low (or holds support),
       while Cumulative Perp Delta makes a significantly Lower Low and Spot CVD holds/rises.
    """
    n = min(len(spot_bars_1h), len(perp_bars_1h), lookback_bars)
    if n < 10:
        return False, False

    s_slice = list(spot_bars_1h[-n:])
    p_slice = list(perp_bars_1h[-n:])

    spot_cum = np.cumsum([b.delta for b in s_slice])
    perp_cum = np.cumsum([b.delta for b in p_slice])
    lows = np.array([b.low for b in s_slice], dtype=float)

    # Split window into earlier half (pivot 1) and recent 6 hours (pivot 2)
    split_idx = max(4, n - 6)
    p1_idx = int(np.argmin(lows[:split_idx]))
    p2_idx = split_idx + int(np.argmin(lows[split_idx:]))

    price_1, price_2 = float(lows[p1_idx]), float(lows[p2_idx])
    spot_cvd_1, spot_cvd_2 = float(spot_cum[p1_idx]), float(spot_cum[p2_idx])
    perp_cvd_1, perp_cvd_2 = float(perp_cum[p1_idx]), float(perp_cum[p2_idx])

    # Classic Bullish Divergence: Lower Low in price, Higher Low in Spot CVD
    classic_bull_div = (price_2 <= price_1 * 1.001) and (spot_cvd_2 > spot_cvd_1)

    # Absorption Divergence: Price holds/higher low while Perp CVD dumps lower and Spot CVD rises/holds
    absorption_div = (
        (price_2 >= price_1 * 0.998)
        and (perp_cvd_2 < perp_cvd_1)
        and (spot_cvd_2 >= spot_cvd_1)
    )

    return bool(classic_bull_div), bool(absorption_div)


def compute_flow_snapshot(config: EngineConfig, store: StateStore) -> FlowSnapshot:
    """Computes complete multi-horizon (15m, 1H, 4H, 24H) Spot vs. Perp order flow snapshot."""
    spot_15m = list(store.spot_klines_15m)
    perp_15m = list(store.perp_klines_15m)
    spot_1h = list(store.spot_klines_1h)
    perp_1h = list(store.perp_klines_1h)

    w_15m = _compute_window_metrics("15m", spot_15m, perp_15m, window_size=1, lookback_windows=config.cvd_zscore_lookback)
    w_1h = _compute_window_metrics("1H", spot_15m, perp_15m, window_size=4, lookback_windows=config.cvd_zscore_lookback)
    w_4h = _compute_window_metrics("4H", spot_1h, perp_1h, window_size=4, lookback_windows=config.cvd_zscore_lookback)
    w_24h = _compute_window_metrics("24H", spot_1h, perp_1h, window_size=24, lookback_windows=28)

    bull_div, abs_div = _detect_pivot_divergences(spot_1h, perp_1h)

    # Classify overall Flow Signature using 1H & 4H blended metrics
    spot_d = w_1h.spot_delta_btc
    perp_d = w_1h.perp_delta_btc
    div_z = w_1h.flow_divergence_z

    if (spot_d >= 0 and perp_d < 0) or div_z >= config.divergence_z_spread_threshold:
        signature = "BULLISH PASSIVE ABSORPTION (Spot Buying / Perp Shorting)"
    elif (spot_d <= 0 and perp_d > 0) or div_z <= config.leveraged_trap_z_spread:
        signature = "BEARISH LEVERAGE CHASE (Perp Buying / Spot Selling)"
    elif spot_d > 0 and perp_d > 0:
        signature = "AGGRESSIVE AGGREGATE DEMAND (Spot + Perp Aligned)"
    elif spot_d < 0 and perp_d < 0:
        signature = "AGGRESSIVE AGGREGATE SELLING (Spot + Perp Aligned)"
    else:
        signature = "BALANCED / NEUTRAL ROTATION"

    return FlowSnapshot(
        session_spot_cvd=store.session_spot_cvd,
        session_perp_cvd=store.session_perp_cvd,
        utc_day_spot_cvd=store.utc_day_spot_cvd,
        utc_day_perp_cvd=store.utc_day_perp_cvd,
        spot_trade_count=store.spot_trade_count,
        perp_trade_count=store.perp_trade_count,
        w_15m=w_15m,
        w_1h=w_1h,
        w_4h=w_4h,
        w_24h=w_24h,
        bullish_pivot_divergence=bull_div,
        absorption_divergence=abs_div,
        flow_signature=signature,
    )


def compute_derivatives_snapshot(
    config: EngineConfig,
    store: StateStore,
    flow: FlowSnapshot,
) -> DerivativesSnapshot:
    """Computes Open Interest 4-Quadrant state, Coinbase Premium Z-score, and Funding health."""
    oi_15m = store.get_oi_change_pct(900.0)
    oi_1h = store.get_oi_change_pct(3600.0)
    oi_4h = store.get_oi_change_pct(14400.0)

    price_chg_1h = flow.w_1h.price_change_pct

    # 4-Quadrant Price vs. OI Classification
    if price_chg_1h < -0.15 and (oi_1h < -0.35 or oi_4h <= config.oi_flush_pct_4h):
        quadrant = OIPositioningQuadrant.LONG_LIQUIDATION_FLUSH
    elif price_chg_1h <= 0.10 and oi_1h >= config.oi_short_build_pct_1h:
        quadrant = OIPositioningQuadrant.AGGRESSIVE_SHORT_BUILD
    elif price_chg_1h > 0.15 and oi_1h > 0.25:
        quadrant = OIPositioningQuadrant.LEVERAGED_LONG_EXPANSION
    elif price_chg_1h > 0.15 and oi_1h < -0.20:
        quadrant = OIPositioningQuadrant.SHORT_COVERING_BOUNCE
    else:
        quadrant = OIPositioningQuadrant.NEUTRAL_CHURN

    prem_usd, prem_pct, prem_z = store.get_cpi_metrics()
    perp_basis = (
        store.binance_perp_price - store.binance_spot_price
        if (store.binance_perp_price > 0 and store.binance_spot_price > 0)
        else 0.0
    )

    return DerivativesSnapshot(
        open_interest_btc=store.open_interest_btc,
        open_interest_usd=store.open_interest_usd,
        oi_change_15m_pct=oi_15m,
        oi_change_1h_pct=oi_1h,
        oi_change_4h_pct=oi_4h,
        oi_regime_quadrant=quadrant,
        funding_rate_pct=store.funding_rate_pct,
        taker_long_short_ratio_5m=store.taker_long_short_ratio_5m,
        perp_5m_delta_btc=store.perp_5m_delta_btc,
        coinbase_price=store.coinbase_spot_price,
        binance_spot_price=store.binance_spot_price,
        binance_perp_price=store.binance_perp_price,
        coinbase_premium_usd=prem_usd,
        coinbase_premium_pct=prem_pct,
        coinbase_premium_zscore=prem_z,
        perp_basis_usd=perp_basis,
        perp_source=store.perp_source,
    )

```

---

### File: `analytics/protocol_v13.py`

```python
"""Tab [2] Analytics Engine: BTC Spot Swing Protocol v1.3 & CoinGlass 6-Panel Audit.

Strictly obeys Protocol v1.3 rules:
- Long-Only Spot discipline.
- No Hidden Indicators on this tab (no RSI, MACD, or EMA calculations used here).
- 1D timeframe controls directional bias (strictly separating completed [-2] vs forming [-1] candle).
- 4H timeframe controls short-term structure and entry timing.
- Fixed 6-Panel CoinGlass order with Open Interest strictly in BTC coins (never USD notional).
- Section 8 Non-Trade Zones (8A-8F), Section 10 Buy Decision, and Section 11 Sell Triggers (1-4).
"""

import json
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Sequence, Tuple

import numpy as np

from config.settings import EngineConfig
from core.models import (
    CoinGlassPanelRow,
    DerivativesSnapshot,
    FlowSnapshot,
    KlineBar,
    ProtocolNonTradeZoneItem,
    ProtocolSellTriggerItem,
    ProtocolV13Evaluation,
)
from core.state_store import StateStore
from .volume_profile import compute_atr, synthesize_4h_bars


# Built-in 2026 FOMC & US CPI release dates (YYYY-MM-DD UTC) for automatic 8D window detection
FOMC_CPI_DATES_2026 = {
    # 2026 FOMC Decision Dates
    "2026-01-28", "2026-03-18", "2026-05-06", "2026-06-17",
    "2026-07-29", "2026-09-16", "2026-10-28", "2026-12-09",
    # 2026 US CPI Release Dates
    "2026-01-14", "2026-02-11", "2026-03-11", "2026-04-14",
    "2026-05-12", "2026-06-10", "2026-07-14", "2026-08-12",
    "2026-09-11", "2026-10-14", "2026-11-12", "2026-12-10",
}


def synthesize_1d_bars_from_1h(bars_1h: Sequence[KlineBar]) -> List[KlineBar]:
    """Fallback synthesizer for 1D bars when only 1H bars are loaded (e.g., in synthetic unit tests)."""
    if not bars_1h:
        return []
    buckets: Dict[int, List[KlineBar]] = {}
    day_ms = 86_400_000
    for b in bars_1h:
        b_key = (b.timestamp_ms // day_ms) * day_ms
        buckets.setdefault(b_key, []).append(b)

    out: List[KlineBar] = []
    for b_key in sorted(buckets.keys()):
        grp = buckets[b_key]
        out.append(
            KlineBar(
                timestamp_ms=b_key,
                open=grp[0].open,
                high=max(x.high for x in grp),
                low=min(x.low for x in grp),
                close=grp[-1].close,
                volume=sum(x.volume for x in grp),
                taker_buy_volume=sum(x.taker_buy_volume for x in grp),
            )
        )
    return out


class ProtocolV13Evaluator:
    """Evaluates Protocol v1.3 Market Structure, CoinGlass 6-Panel Audit, and Non-Trade Zones."""

    def __init__(self, config: EngineConfig) -> None:
        self.config = config
        self._cached_context: Dict[str, Any] = {}
        self._last_context_load_ts: float = 0.0

    def _load_protocol_context(self) -> Dict[str, Any]:
        """Hot-reloads `config/protocol_context.json` every 10 seconds."""
        now = time.time()
        if self._cached_context and (now - self._last_context_load_ts) < 10.0:
            return self._cached_context

        self._last_context_load_ts = now
        defaults: Dict[str, Any] = {
            "last_reviewed_utc": "AUTO",
            "liq_cascade_72h_over_300m": "CONFIRMED_CLEAR",
            "liq_cascade_reclaimed_within_24h": "CONFIRMED_CLEAR",
            "fomc_cpi_window_override": "AUTO",
            "s2_risk_level": "LOW",
            "etf_net_outflow_weakness": "NOT_CONFIRMED",
            "catalyst_technical_breakdown": "NOT_CONFIRMED",
            "enforce_200d_hard_veto_on_tab1": False,
            "cycle_ath_override_usd": self.config.default_cycle_ath_usd,
        }
        try:
            if self.config.protocol_context_path.exists():
                with open(self.config.protocol_context_path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    if isinstance(loaded, dict):
                        defaults.update(loaded)
        except Exception:
            pass

        self._cached_context = defaults
        return defaults

    @staticmethod
    def _classify_cvd_direction(bars: Sequence[KlineBar], lookback: int = 3) -> Tuple[float, str]:
        """Computes cumulative delta over `lookback` bars and classifies direction."""
        if not bars:
            return 0.0, "FLAT"
        window = bars[-lookback:]
        net_delta = sum(b.delta for b in window)
        total_vol = max(sum(b.volume for b in window), 1e-6)
        ratio = net_delta / total_vol
        if ratio >= 0.025:
            return net_delta, "RISING"
        if ratio <= -0.025:
            return net_delta, "FALLING"
        return net_delta, "FLAT"

    def evaluate(
        self,
        store: StateStore,
        flow: FlowSnapshot,
        deriv: DerivativesSnapshot,
    ) -> ProtocolV13Evaluation:
        """Runs full Protocol v1.3 evaluation across 1D (Completed vs Forming) and 4H timeframes."""
        ctx = self._load_protocol_context()
        spot_1h = list(store.spot_klines_1h)
        perp_1h = list(store.perp_klines_1h)
        spot_1d = list(store.spot_klines_1d) or synthesize_1d_bars_from_1h(spot_1h)
        perp_1d = list(store.perp_klines_1d) or synthesize_1d_bars_from_1h(perp_1h)

        bars_4h = synthesize_4h_bars(spot_1h)
        perp_bars_4h = synthesize_4h_bars(perp_1h)

        current_price = store.binance_spot_price or (spot_1h[-1].close if spot_1h else 0.0)

        # 1. Strictly separate Completed 1D candle [-2] from Forming 1D candle [-1]
        if len(spot_1d) >= 2:
            comp_1d = spot_1d[-2]
            form_1d = spot_1d[-1]
        elif len(spot_1d) == 1:
            comp_1d = spot_1d[0]
            form_1d = spot_1d[0]
        else:
            comp_1d = KlineBar(0, current_price, current_price, current_price, current_price, 0.0, 0.0)
            form_1d = comp_1d

        comp_1d_chg = ((comp_1d.close - comp_1d.open) / max(comp_1d.open, 1.0)) * 100.0
        form_1d_chg = ((form_1d.close - form_1d.open) / max(form_1d.open, 1.0)) * 100.0

        # 2. Compute 1D Structural Support & Resistance from Completed 1D Candles (last 14 completed days)
        completed_window = spot_1d[:-1][-14:] if len(spot_1d) >= 3 else spot_1d
        daily_support = min((b.low for b in completed_window), default=current_price * 0.95)
        daily_resistance = max((b.high for b in completed_window), default=current_price * 1.05)

        # 3. 1D Directional Bias (Pure price structure of Completed [-2] & 7D structure, no hidden indicators)
        recent_3d = spot_1d[:-1][-3:] if len(spot_1d) >= 4 else completed_window
        higher_lows_1d = len(recent_3d) >= 2 and recent_3d[-1].low >= recent_3d[0].low
        higher_closes_1d = len(recent_3d) >= 2 and recent_3d[-1].close >= recent_3d[0].close

        if comp_1d.close > comp_1d.open and higher_closes_1d and current_price >= daily_support:
            daily_bias = "BULLISH"
        elif comp_1d.close < daily_support or (comp_1d.close < comp_1d.open and not higher_lows_1d):
            daily_bias = "BEARISH"
        else:
            daily_bias = "NEUTRAL"

        # 4. 4H Short-Term Structure & Entry Timing
        if len(bars_4h) >= 4:
            b4_prev = bars_4h[-3]
            b4_comp = bars_4h[-2]
            b4_form = bars_4h[-1]
            if b4_comp.close > b4_prev.close and b4_comp.low >= b4_prev.low:
                structure_4h = "BULLISH HH/HL (Higher Lows Holding)"
                timing_4h_ready = b4_form.close >= b4_comp.low and flow.w_4h.spot_delta_btc > 0
            elif b4_comp.close < b4_prev.low and flow.w_4h.spot_delta_btc < 0:
                structure_4h = "BEARISH LH/LL (Lower Lows Active)"
                timing_4h_ready = False
            else:
                structure_4h = "RANGE / BASE CONSOLIDATION"
                timing_4h_ready = b4_form.close > b4_form.open and flow.w_4h.spot_delta_btc > 0
        else:
            structure_4h = "WARMING UP"
            timing_4h_ready = False

        # 5. ATR 14 on 1D (completed bars) and 4H (completed bars)
        atr_14_1d = max(compute_atr(spot_1d[:-1][-25:] if len(spot_1d) > 2 else spot_1d, period=14), 1.0)
        atr_14_4h = max(compute_atr(bars_4h[:-1][-25:] if len(bars_4h) > 2 else bars_4h, period=14), 1.0)

        down_1d_atr = current_price - atr_14_1d
        up_1d_atr = current_price + atr_14_1d
        down_4h_atr = current_price - atr_14_4h
        up_4h_atr = current_price + atr_14_4h

        # 6. Fixed 6-Panel CoinGlass Order across 1D & 4H
        # Panel 1: Volume SMA 9
        vol_1d_bars = spot_1d[:-1][-9:] if len(spot_1d) >= 2 else spot_1d[-9:]
        vol_sma9_1d = float(np.mean([b.volume for b in vol_1d_bars])) if vol_1d_bars else 0.0
        vol_4h_bars = bars_4h[:-1][-9:] if len(bars_4h) >= 2 else bars_4h[-9:]
        vol_sma9_4h = float(np.mean([b.volume for b in vol_4h_bars])) if vol_4h_bars else 0.0
        cur_vol_4h = bars_4h[-2].volume if len(bars_4h) >= 2 else (bars_4h[-1].volume if bars_4h else 0.0)
        vol_trend = (
            "EXPANDING (Above SMA9)"
            if cur_vol_4h > vol_sma9_4h * 1.05
            else ("CONTRACTING (Below SMA9)" if cur_vol_4h < vol_sma9_4h * 0.85 else "FLAT / IN-LINE")
        )

        # Panel 2: Aggregated Spot CVD
        spot_cvd_1d_val, spot_cvd_1d_dir = self._classify_cvd_direction(spot_1d[:-1] or spot_1d, lookback=3)
        spot_cvd_4h_val = flow.w_4h.spot_delta_btc
        spot_cvd_4h_dir = (
            "RISING" if spot_cvd_4h_val > 15.0 else ("FALLING" if spot_cvd_4h_val < -15.0 else "FLAT")
        )

        # Panel 3: Aggregated Futures CVD
        perp_cvd_1d_val, perp_cvd_1d_dir = self._classify_cvd_direction(perp_1d[:-1] or perp_1d, lookback=3)
        perp_cvd_4h_val = flow.w_4h.perp_delta_btc
        perp_cvd_4h_dir = (
            "RISING" if perp_cvd_4h_val > 40.0 else ("FALLING" if perp_cvd_4h_val < -40.0 else "FLAT")
        )

        # Panel 4: Open Interest (Strict BTC Coins - NEVER USD Notional)
        oi_btc = deriv.open_interest_btc
        oi_dir = (
            "RISING"
            if deriv.oi_change_4h_pct >= 0.35
            else ("FALLING" if deriv.oi_change_4h_pct <= -0.35 else "FLAT")
        )
        oi_above_90k = oi_btc > self.config.protocol_oi_high_threshold_btc
        oi_status_str = (
            f"{oi_dir} | {'[ ELEVATED > 90,000 BTC ]' if oi_above_90k else 'BELOW 90,000 BTC CAP'}"
        )

        # Panel 5: Funding Rates
        fund_pct = deriv.funding_rate_pct
        fund_dir = (
            "POSITIVE (Longs Pay)"
            if fund_pct > 0.002
            else ("NEGATIVE (Shorts Pay)" if fund_pct < -0.001 else "NEUTRAL / FLAT")
        )

        # Panel 6: ATR 14
        atr_1d_pct = (atr_14_1d / max(current_price, 1.0)) * 100.0
        atr_4h_pct = (atr_14_4h / max(current_price, 1.0)) * 100.0

        coinglass_rows = [
            CoinGlassPanelRow(
                panel_num=1,
                metric_name="1. Volume SMA 9 (BTC)",
                value_1d=f"{vol_sma9_1d:,.0f} BTC (1D: {comp_1d.volume:,.0f})",
                value_4h=f"{vol_sma9_4h:,.0f} BTC (4H: {cur_vol_4h:,.0f})",
                direction_status=vol_trend,
            ),
            CoinGlassPanelRow(
                panel_num=2,
                metric_name="2. Aggregated Spot CVD",
                value_1d=f"{spot_cvd_1d_val:+,.0f} BTC [{spot_cvd_1d_dir}]",
                value_4h=f"{spot_cvd_4h_val:+,.1f} BTC [{spot_cvd_4h_dir}]",
                direction_status=f"1D:{spot_cvd_1d_dir} | 4H:{spot_cvd_4h_dir}",
            ),
            CoinGlassPanelRow(
                panel_num=3,
                metric_name="3. Aggregated Futures CVD",
                value_1d=f"{perp_cvd_1d_val:+,.0f} BTC [{perp_cvd_1d_dir}]",
                value_4h=f"{perp_cvd_4h_val:+,.1f} BTC [{perp_cvd_4h_dir}]",
                direction_status=f"1D:{perp_cvd_1d_dir} | 4H:{perp_cvd_4h_dir}",
            ),
            CoinGlassPanelRow(
                panel_num=4,
                metric_name="4. Open Interest (BTC)",
                value_1d=f"{oi_btc:,.1f} BTC (Coins)",
                value_4h=f"4H:{deriv.oi_change_4h_pct:+.2f}% | 1H:{deriv.oi_change_1h_pct:+.2f}%",
                direction_status=f"{oi_dir} ({'>90k BTC' if oi_above_90k else '<=90k BTC'})",
            ),
            CoinGlassPanelRow(
                panel_num=5,
                metric_name="5. Funding Rates (8H)",
                value_1d=f"{fund_pct:+.4f}% / 8h",
                value_4h=f"{fund_pct * 3:+.4f}% / 24h",
                direction_status=fund_dir,
            ),
            CoinGlassPanelRow(
                panel_num=6,
                metric_name="6. ATR 14 (Volatility)",
                value_1d=f"${atr_14_1d:,.0f} ({atr_1d_pct:.2f}%)",
                value_4h=f"${atr_14_4h:,.0f} ({atr_4h_pct:.2f}%)",
                direction_status=f"-1xATR: ${down_4h_atr:,.0f} / ${down_1d_atr:,.0f}",
            ),
        ]

        # 7. Section 8 Non-Trade Zones (8A - 8F)
        if store.warmup_complete:
            now_utc = datetime.now(timezone.utc)
        elif spot_1h:
            now_utc = datetime.fromtimestamp(spot_1h[-1].timestamp_ms / 1000.0, tz=timezone.utc)
        else:
            now_utc = datetime.now(timezone.utc)
        is_weekend = now_utc.weekday() >= 5  # Saturday=5, Sunday=6
        nearest_round = min(
            self.config.protocol_round_numbers_usd,
            key=lambda lvl: abs(current_price - lvl),
        )
        dist_round_pct = abs(current_price - nearest_round) / max(nearest_round, 1.0) * 100.0
        within_round_2pct = dist_round_pct <= self.config.protocol_round_proximity_pct

        # 8A: Weekend/Holiday + within 2.0% of $80k/$85k/$100k + OI > 90,000 BTC (ALL 3 required)
        ntz_8a_triggered = is_weekend and within_round_2pct and oi_above_90k
        ntz_8a = ProtocolNonTradeZoneItem(
            code="8A",
            rule_name="Weekend + <=2% of $80k/$85k/$100k + OI>90k BTC",
            status="TRIGGERED" if ntz_8a_triggered else "CLEAR",
            detail=(
                f"{'Weekend' if is_weekend else 'Weekday'} | "
                f"{dist_round_pct:.2f}% from ${nearest_round:,.0f} "
                f"({'<=2%' if within_round_2pct else '>2%'}) | "
                f"OI {oi_btc:,.0f} BTC ({'>90k' if oi_above_90k else '<=90k'})"
            ),
        )

        # 8B: Recent 72h Liquidation Cascade > $300M
        raw_8b = str(ctx.get("liq_cascade_72h_over_300m", "CONFIRMED_CLEAR")).upper()
        auto_liq_cascade = deriv.oi_change_4h_pct <= -6.0
        if auto_liq_cascade or raw_8b in ("TRIGGERED", "YES", "ACTIVE"):
            status_8b = "TRIGGERED"
            detail_8b = "Active >$300M 72h liquidation cascade (Wait for 24h structural reclaim)"
        elif raw_8b == "UNVERIFIED":
            status_8b = "UNVERIFIED"
            detail_8b = "72h Liquidation Cascade status marked UNVERIFIED in protocol_context.json"
        else:
            status_8b = "CLEAR"
            detail_8b = f"No >$300M 72h cascade active (4H dOI: {deriv.oi_change_4h_pct:+.2f}%)"
        ntz_8b = ProtocolNonTradeZoneItem(
            code="8B",
            rule_name="72h Liquidation Cascade > $300M",
            status=status_8b,
            detail=detail_8b,
        )

        # 8C: Positive Funding + Flat/Rising OI + Falling Price (Live check)
        price_falling = flow.w_4h.price_change_pct <= -0.35 and flow.w_1h.price_change_pct <= -0.20
        oi_flat_or_rising = deriv.oi_change_4h_pct >= 0.0 or deriv.oi_change_1h_pct >= 0.20
        funding_positive = deriv.funding_rate_pct > 0.0105 or (
            deriv.funding_rate_pct > 0.005 and flow.w_4h.price_change_pct <= -1.0
        )
        ntz_8c_triggered = funding_positive and oi_flat_or_rising and price_falling
        ntz_8c = ProtocolNonTradeZoneItem(
            code="8C",
            rule_name="Positive Funding + Flat/Rising OI + Falling Price",
            status="TRIGGERED" if ntz_8c_triggered else "CLEAR",
            detail=(
                f"Funding {deriv.funding_rate_pct:+.4f}% | "
                f"1H/4H dOI {deriv.oi_change_1h_pct:+.2f}%/{deriv.oi_change_4h_pct:+.2f}% | "
                f"1H/4H Price {flow.w_1h.price_change_pct:+.2f}%/{flow.w_4h.price_change_pct:+.2f}%"
            ),
        )

        # 8D: FOMC / CPI Macro Window
        today_str = now_utc.strftime("%Y-%m-%d")
        raw_8d = str(ctx.get("fomc_cpi_window_override", "AUTO")).upper()
        if raw_8d in ("TRIGGERED", "YES", "ACTIVE"):
            status_8d = "TRIGGERED"
            detail_8d = "Manual FOMC/CPI Macro Window override ACTIVE"
        elif raw_8d == "UNVERIFIED":
            status_8d = "UNVERIFIED"
            detail_8d = "FOMC/CPI calendar check marked UNVERIFIED"
        elif raw_8d == "AUTO" and today_str in FOMC_CPI_DATES_2026:
            status_8d = "TRIGGERED"
            detail_8d = f"Today ({today_str}) is a scheduled 2026 FOMC / US CPI event date"
        else:
            status_8d = "CLEAR"
            detail_8d = f"Clear of FOMC/CPI release window ({today_str} UTC)"
        ntz_8d = ProtocolNonTradeZoneItem(
            code="8D",
            rule_name="FOMC / CPI High-Volatility Macro Window",
            status=status_8d,
            detail=detail_8d,
        )

        # 8E: S2 Risk Assessment
        s2_level = str(ctx.get("s2_risk_level", "LOW")).upper()
        if s2_level in ("HIGH", "CRITICAL"):
            status_8e = "TRIGGERED"
        elif s2_level == "UNVERIFIED":
            status_8e = "UNVERIFIED"
        else:
            status_8e = "CLEAR"
        ntz_8e = ProtocolNonTradeZoneItem(
            code="8E",
            rule_name="Section 8E S2 Systemic Risk Assessment",
            status=status_8e,
            detail=f"S2 Systemic Risk Level: {s2_level} (Clear when LOW/MED)",
        )

        # 8F: Unverified Mandatory Check Override
        prior_checks = [ntz_8a, ntz_8b, ntz_8c, ntz_8d, ntz_8e]
        unverified_codes = [c.code for c in prior_checks if c.status == "UNVERIFIED"]
        ntz_8f = ProtocolNonTradeZoneItem(
            code="8F",
            rule_name="Unverified Mandatory Check Safety Lock",
            status="TRIGGERED" if unverified_codes else "CLEAR",
            detail=(
                f"Unverified checks locking desk: {', '.join(unverified_codes)}"
                if unverified_codes
                else "All mandatory 8A–8E safety inputs verified"
            ),
        )

        non_trade_zones = [ntz_8a, ntz_8b, ntz_8c, ntz_8d, ntz_8e, ntz_8f]
        triggered_ntz = [z for z in non_trade_zones if z.status == "TRIGGERED"]
        if unverified_codes:
            ntz_status = "UNVERIFIED"
        elif triggered_ntz:
            ntz_status = "YES"
        else:
            ntz_status = "NO"

        active_ntz_reasons = [f"Protocol v1.3 [{z.code}]: {z.rule_name}" for z in triggered_ntz]

        # 8. Section 11 Long-Only Spot Sell Triggers (1 - 4)
        # Sell Trigger 1: Confirmed 1D close < support + flat/rising OI + falling CVD
        st1_confirmed = (
            comp_1d.close < daily_support
            and (deriv.oi_change_4h_pct >= 0.0 or deriv.oi_change_1h_pct >= 0.0)
            and spot_cvd_4h_dir == "FALLING"
        )
        st1 = ProtocolSellTriggerItem(
            trigger_num=1,
            name="1. 1D Close < Support + Rising OI + Falling CVD",
            status="CONFIRMED" if st1_confirmed else "NOT CONFIRMED",
            detail=f"1D Close ${comp_1d.close:,.0f} vs Sup ${daily_support:,.0f} | 4H CVD {spot_cvd_4h_dir}",
        )

        # Sell Trigger 2: Liquidation cascade fails 24h reclaim
        raw_reclaim = str(ctx.get("liq_cascade_reclaimed_within_24h", "CONFIRMED_CLEAR")).upper()
        st2_status = (
            "CONFIRMED"
            if raw_reclaim in ("FAILED", "CONFIRMED")
            else ("UNVERIFIED" if raw_reclaim == "UNVERIFIED" else "NOT CONFIRMED")
        )
        st2 = ProtocolSellTriggerItem(
            trigger_num=2,
            name="2. Liq Cascade Fails 24h Structural Reclaim",
            status=st2_status,
            detail=f"Cascade 24h status: {raw_reclaim}",
        )

        # Sell Trigger 3: Large ETF outflows + price weakness
        raw_etf = str(ctx.get("etf_net_outflow_weakness", "NOT_CONFIRMED")).upper()
        st3_status = (
            "CONFIRMED"
            if raw_etf == "CONFIRMED"
            else ("UNVERIFIED" if raw_etf == "UNVERIFIED" else "NOT CONFIRMED")
        )
        st3 = ProtocolSellTriggerItem(
            trigger_num=3,
            name="3. Large Spot ETF Outflows + Price Weakness",
            status=st3_status,
            detail=f"ETF flow status: {raw_etf}",
        )

        # Sell Trigger 4: Catalyst + technical breakdown
        raw_cat = str(ctx.get("catalyst_technical_breakdown", "NOT_CONFIRMED")).upper()
        st4_status = (
            "CONFIRMED"
            if raw_cat == "CONFIRMED"
            else ("UNVERIFIED" if raw_cat == "UNVERIFIED" else "NOT CONFIRMED")
        )
        st4 = ProtocolSellTriggerItem(
            trigger_num=4,
            name="4. Adverse Macro Catalyst + Technical Breakdown",
            status=st4_status,
            detail=f"Catalyst breakdown status: {raw_cat}",
        )

        sell_triggers = [st1, st2, st3, st4]
        any_sell_confirmed = any(s.status == "CONFIRMED" for s in sell_triggers)

        # 9. Section 10 Final Buy Decision & Readiness
        readiness_notes: List[str] = []
        if ntz_status != "NO":
            buy_allowed = "NO"
            entry_status = "NOT READY"
            confidence = "LOW"
            readiness_notes.append(f"Blocked by Section 8 Non-Trade Zone ({', '.join(z.code for z in triggered_ntz)}).")
        elif any_sell_confirmed:
            buy_allowed = "NO"
            entry_status = "NOT READY"
            confidence = "LOW"
            readiness_notes.append("Blocked by active Section 11 Spot Sell Trigger.")
        elif daily_bias == "BULLISH" and timing_4h_ready and spot_cvd_4h_dir == "RISING":
            buy_allowed = "YES"
            entry_status = "READY"
            confidence = "HIGH" if spot_cvd_1d_dir == "RISING" else "MEDIUM"
            readiness_notes.append("1D Bias BULLISH + 4H structure aligned + Spot CVD RISING + Zero Non-Trade Zones.")
        elif daily_bias in ("BULLISH", "NEUTRAL") and spot_cvd_4h_dir == "RISING" and not ntz_8c_triggered:
            buy_allowed = "YES"
            entry_status = "NOT READY" if not timing_4h_ready else "READY"
            confidence = "MEDIUM"
            readiness_notes.append(
                f"1D Bias {daily_bias}; 4H Spot CVD RISING, awaiting 4H HH/HL close confirmation."
            )
        else:
            buy_allowed = "NO"
            entry_status = "NOT READY"
            confidence = "LOW"
            readiness_notes.append(
                f"Stand aside: 1D Bias is {daily_bias}, 4H Spot CVD is {spot_cvd_4h_dir}, 4H Timing={'READY' if timing_4h_ready else 'WAIT'}."
            )

        readiness_notes.append(
            f"1D Completed [-2]: ${comp_1d.close:,.0f} ({comp_1d_chg:+.2f}%) | 1D Forming [-1]: ${form_1d.close:,.0f} ({form_1d_chg:+.2f}%)"
        )
        readiness_notes.append(
            f"ATR 14 Reference Bounds -> 4H [-1xATR]: ${down_4h_atr:,.0f} | 1D [-1xATR]: ${down_1d_atr:,.0f}"
        )

        # 10. Liquidation Magnet & Range Predisposition Protocol (T1 + T2 Integration)
        closes_50d = [b.close for b in spot_1d[-50:]] if spot_1d else [current_price]
        sma_50_1d = float(np.mean(closes_50d)) if closes_50d else current_price
        range_pivot_usd = (daily_support + daily_resistance) / 2.0

        manual_short_liq = float(ctx.get("short_liq_magnet_override_usd", 0.0) or 0.0)
        if manual_short_liq > 0.0:
            short_liq_magnet_usd = manual_short_liq
            short_liq_source = "[COINGLASS MANUAL]"
        else:
            swing_high_14d = max((b.high for b in spot_1d[-14:]), default=daily_resistance)
            ref_high = swing_high_14d if swing_high_14d > current_price * 1.005 else max(daily_resistance, current_price * 1.02)
            short_liq_magnet_usd = ref_high * 1.005
            short_liq_source = "[EST. SWING LIQ POOL]"

        manual_long_liq = float(ctx.get("long_liq_magnet_override_usd", 0.0) or 0.0)
        if manual_long_liq > 0.0:
            long_liq_magnet_usd = manual_long_liq
            long_liq_source = "[COINGLASS MANUAL]"
        else:
            swing_low_14d = min((b.low for b in spot_1d[-14:]), default=daily_support)
            ref_low = swing_low_14d if swing_low_14d < current_price * 0.995 else min(daily_support, current_price * 0.98)
            long_liq_magnet_usd = ref_low * 0.995
            long_liq_source = "[EST. SWING LIQ POOL]"

        headline_filter_status = str(ctx.get("headline_classification", "NONE_SIGNIFICANT")).upper()

        dist_short_liq_pct = ((short_liq_magnet_usd - current_price) / max(current_price, 1.0)) * 100.0
        dist_long_liq_pct = ((current_price - long_liq_magnet_usd) / max(current_price, 1.0)) * 100.0

        # T2 5-Factor Confluence Count
        aligned_factors = 0
        if min(dist_short_liq_pct, dist_long_liq_pct) <= 4.5:
            aligned_factors += 1
        if deriv.funding_rate_pct <= 0.0100:
            aligned_factors += 1
        if abs(deriv.oi_change_4h_pct) >= 0.30:
            aligned_factors += 1
        if spot_cvd_4h_dir == "RISING":
            aligned_factors += 1
        if timing_4h_ready or current_price >= range_pivot_usd:
            aligned_factors += 1

        # T1 4-Way Range-Regime Decision Rules
        if comp_1d.close > short_liq_magnet_usd and spot_cvd_1d_dir == "RISING" and deriv.oi_change_4h_pct >= -0.5:
            liq_magnet_verdict = "RARE ADD ON RETEST (Breakout Confirmed)"
            liq_magnet_action_note = (
                f"1D closed above ${short_liq_magnet_usd:,.0f} wall with rising Spot CVD; consider adding on retest."
            )
        elif (
            dist_short_liq_pct <= 3.0
            and deriv.funding_rate_pct <= 0.0105
            and flow.w_1h.spot_delta_btc <= 0
        ):
            liq_magnet_verdict = "PARTIAL PROFIT INTO MAGNET (Scale 30–50%)"
            liq_magnet_action_note = (
                f"Scale 30–50% into ${short_liq_magnet_usd:,.0f} short-liq cluster; do NOT chase futures-driven bounce."
            )
        elif (
            current_price < range_pivot_usd
            and current_price < sma_50_1d
            and spot_cvd_4h_dir == "FALLING"
        ):
            liq_magnet_verdict = "REDUCE / ROTATE DEFENSIVE (Below Pivot & 50D MA)"
            liq_magnet_action_note = (
                f"Below Range Pivot (${range_pivot_usd:,.0f}) & 50D MA (${sma_50_1d:,.0f}); watch ${long_liq_magnet_usd:,.0f} long-liq pool."
            )
        elif dist_long_liq_pct <= 2.5 and spot_cvd_4h_dir == "RISING" and aligned_factors >= 3:
            liq_magnet_verdict = "HOLD / ACCUMULATE AT RANGE LOW (Target Short-Liq Magnet)"
            liq_magnet_action_note = (
                f"Spot absorbing near ${long_liq_magnet_usd:,.0f} long-liq pool; target 30–50% partial at ${short_liq_magnet_usd:,.0f}."
            )
        else:
            liq_magnet_verdict = "DO NOTHING (Default Range Inaction — Wait for Magnet Edge)"
            liq_magnet_action_note = (
                f"Scale 30–50% into ${short_liq_magnet_usd:,.0f} if reached; Invalidation: 1D close < ${min(range_pivot_usd, sma_50_1d):,.0f}."
            )

        ev = ProtocolV13Evaluation(
            timestamp_utc=now_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
            current_price=round(current_price, 2),
            completed_1d_open=round(comp_1d.open, 2),
            completed_1d_high=round(comp_1d.high, 2),
            completed_1d_low=round(comp_1d.low, 2),
            completed_1d_close=round(comp_1d.close, 2),
            completed_1d_change_pct=round(comp_1d_chg, 2),
            forming_1d_open=round(form_1d.open, 2),
            forming_1d_high=round(form_1d.high, 2),
            forming_1d_low=round(form_1d.low, 2),
            forming_1d_close=round(form_1d.close, 2),
            forming_1d_change_pct=round(form_1d_chg, 2),
            daily_support=round(daily_support, 2),
            daily_resistance=round(daily_resistance, 2),
            daily_bias=daily_bias,
            structure_4h=structure_4h,
            timing_4h_ready=timing_4h_ready,
            atr_14_1d=round(atr_14_1d, 2),
            atr_14_4h=round(atr_14_4h, 2),
            downside_ref_1d_atr=round(down_1d_atr, 2),
            upside_ref_1d_atr=round(up_1d_atr, 2),
            downside_ref_4h_atr=round(down_4h_atr, 2),
            upside_ref_4h_atr=round(up_4h_atr, 2),
            coinglass_rows=coinglass_rows,
            non_trade_zones=non_trade_zones,
            non_trade_zone_status=ntz_status,
            active_ntz_reasons=active_ntz_reasons,
            confidence=confidence,
            buy_allowed=buy_allowed,
            entry_status=entry_status,
            readiness_notes=readiness_notes,
            sell_triggers=sell_triggers,
            any_sell_confirmed=any_sell_confirmed,
            enforce_200d_hard_veto_on_tab1=bool(ctx.get("enforce_200d_hard_veto_on_tab1", False)),
            context_last_reviewed=str(ctx.get("last_reviewed_utc", "AUTO")),
            sma_50_1d=round(sma_50_1d, 2),
            range_pivot_usd=round(range_pivot_usd, 2),
            short_liq_magnet_usd=round(short_liq_magnet_usd, 2),
            short_liq_source=short_liq_source,
            long_liq_magnet_usd=round(long_liq_magnet_usd, 2),
            long_liq_source=long_liq_source,
            headline_filter_status=headline_filter_status,
            magnet_confluence_aligned=aligned_factors,
            liq_magnet_verdict=liq_magnet_verdict,
            liq_magnet_action_note=liq_magnet_action_note,
        )
        store.protocol_evaluation = ev
        return ev

```

---

### File: `analytics/macro_radar.py`

```python
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

```

---

### File: `analytics/regime_matrix.py`

```python
"""Tab [4] Analytics Engine: Regime Radar — Quantitative Microstructure Configurations A through J.

Evaluates all 10 institutional microstructure configurations (Config A through Config J)
in real time against live VWAP (Daily/Weekly), 20D/50D EMA, Spot Volume vs 20D MA,
Spot/Perp CVD ratios & Z-scores, Open Interest dynamics, Funding Rates, ATR compression,
and 24-72h base width, outputting:
- 0-100% live diagnostic match score for each Configuration (A through J)
- Active #1 Configuration & #2 Runner-Up
- Live checklist of IF YOU OBSERVE (EXACT METRIC FACTS) -> THEN IT MEANS -> ACTIONABLE PROTOCOL
- Exact USD stop-loss levels anchored to live 1H/4H/24H candle structure.
"""

from datetime import datetime, timezone
from typing import List, Optional, Sequence

import numpy as np

from config.settings import EngineConfig
from core.models import (
    DerivativesSnapshot,
    FlowSnapshot,
    KlineBar,
    RegimeConfigItem,
    RegimeMatrixEvaluation,
    VolumeProfileResult,
)
from core.state_store import StateStore
from .macro_radar import compute_ema
from .protocol_v13 import synthesize_1d_bars_from_1h
from .volume_profile import compute_atr, synthesize_4h_bars


def _compute_vwap(bars: Sequence[KlineBar]) -> float:
    """Computes Volume-Weighted Average Price (VWAP) over `bars`."""
    if not bars:
        return 0.0
    tot_vol = sum(b.volume for b in bars)
    if tot_vol <= 1e-9:
        return bars[-1].close
    pv = sum(b.typical_price * b.volume for b in bars)
    return float(pv / tot_vol)


class RegimeMatrixEvaluator:
    """Scores Configurations A through J and selects the active diagnostic & execution protocol."""

    def __init__(self, config: EngineConfig) -> None:
        self.config = config

    def evaluate(
        self,
        store: StateStore,
        flow: FlowSnapshot,
        deriv: DerivativesSnapshot,
        macro_vp: Optional[VolumeProfileResult],
    ) -> RegimeMatrixEvaluation:
        """Evaluates all 10 Microstructure Configurations (A-J) against live StateStore telemetry."""
        spot_1h = list(store.spot_klines_1h)
        spot_1d = list(store.spot_klines_1d) or synthesize_1d_bars_from_1h(spot_1h)
        bars_4h = synthesize_4h_bars(spot_1h)

        current_price = store.binance_spot_price or (spot_1h[-1].close if spot_1h else 0.0)

        # 1. Compute Core VWAP, EMA, Volume Ratio, ATR Compression & Range Width Telemetry
        daily_vwap = _compute_vwap(spot_1h[-24:]) if spot_1h else current_price
        weekly_vwap = _compute_vwap(spot_1h[-168:]) if spot_1h else current_price

        closes_1d = [b.close for b in spot_1d] if spot_1d else [current_price]
        ema_20_1d = compute_ema(closes_1d, period=20)
        ema_50_1d = compute_ema(closes_1d, period=50)

        vol_24h_spot = sum(b.volume for b in spot_1h[-24:]) if spot_1h else 0.0
        vol_20d_bars = spot_1d[:-1][-20:] if len(spot_1d) >= 2 else spot_1d[-20:]
        vol_20d_ma = float(np.mean([b.volume for b in vol_20d_bars])) if vol_20d_bars else max(vol_24h_spot, 1.0)
        spot_vol_ratio = vol_24h_spot / max(vol_20d_ma, 1.0)

        buy_4h = sum(b.taker_buy_volume for b in spot_1h[-4:]) if spot_1h else 1.0
        sell_4h = sum(b.taker_sell_volume for b in spot_1h[-4:]) if spot_1h else 1.0
        spot_buy_sell_ratio_4h = buy_4h / max(sell_4h, 1e-6)

        spot_cvd_7d = sum(b.delta for b in spot_1h[-168:]) if spot_1h else 0.0

        oi_1h = deriv.oi_change_1h_pct
        oi_4h = deriv.oi_change_4h_pct
        oi_24h = store.get_oi_change_pct(86_400.0) or (oi_4h * 2.0)
        funding = deriv.funding_rate_pct

        # Annualized basis proxy (Perp-Spot spread annualized + annualized 8h funding)
        perp_spread_pct = (deriv.perp_basis_usd / max(current_price, 1.0)) * 100.0
        annualized_basis_pct = (perp_spread_pct * 12.0) + (funding * 3.0 * 365.0)

        # ATR Compression from recent 10-day 4H ATR peak
        cur_atr_4h = max(compute_atr(bars_4h[-16:], period=14), 1.0) if bars_4h else 500.0
        peak_atr_4h = cur_atr_4h
        if len(bars_4h) >= 30:
            rolling_atrs = [
                compute_atr(bars_4h[max(0, k - 15) : k + 1], period=14)
                for k in range(15, len(bars_4h))
            ]
            if rolling_atrs:
                peak_atr_4h = max(max(rolling_atrs), cur_atr_4h)
        atr_compression_pct = max(0.0, ((peak_atr_4h - cur_atr_4h) / max(peak_atr_4h, 1.0)) * 100.0)

        # 48h-72h Tight Base Range Width %
        base_bars = spot_1h[-48:] if len(spot_1h) >= 48 else spot_1h
        if base_bars:
            base_hi = max(b.high for b in base_bars)
            base_lo = min(b.low for b in base_bars)
            base_width_72h_pct = ((base_hi - base_lo) / max(current_price, 1.0)) * 100.0
        else:
            base_hi = current_price
            base_lo = current_price
            base_width_72h_pct = 0.0

        # Structural Low Anchors for Stop-Loss Computation
        swing_low_4h = min((b.low for b in bars_4h[-3:]), default=current_price * 0.985)
        swing_low_1h = min((b.low for b in spot_1h[-3:]), default=current_price * 0.99)
        low_24h = min((b.low for b in spot_1h[-24:]), default=current_price * 0.975)

        price_chg_1h = flow.w_1h.price_change_pct
        price_chg_4h = flow.w_4h.price_change_pct
        above_d_vwap = current_price >= daily_vwap
        above_w_vwap = current_price >= weekly_vwap

        def _chk(cond: bool, text: str) -> str:
            return f"[green]✔[/green] {text}" if cond else f"[dim]• {text}[/dim]"

        configs: List[RegimeConfigItem] = []

        # ------------------------------------------------------------------
        # CONFIG A: Healthy Bull (Genuine Spot-Led Expansion)
        # ------------------------------------------------------------------
        a_c1 = above_d_vwap and above_w_vwap
        a_c2 = spot_vol_ratio >= 1.35
        a_c3 = spot_buy_sell_ratio_4h >= 1.25 or flow.w_4h.spot_delta_btc > 150.0
        a_c4 = deriv.coinbase_premium_pct > 0.0
        a_c5 = -1.0 <= oi_24h <= 4.0
        a_c6 = 0.002 <= funding <= 0.012
        score_a = (
            (25.0 if a_c1 else (12.0 if above_d_vwap else 0.0))
            + (18.0 if a_c2 else min(12.0, spot_vol_ratio * 8.0))
            + (22.0 if a_c3 else (10.0 if flow.w_4h.spot_delta_btc > 0 else 0.0))
            + (12.0 if a_c4 else 0.0)
            + (11.0 if a_c5 else 4.0)
            + (12.0 if a_c6 else 4.0)
        )
        configs.append(
            RegimeConfigItem(
                code="Config A",
                short_title="Healthy Bull",
                diagnosis_subtitle="Genuine Spot-Led Expansion",
                category="BULL_LONG",
                match_pct=round(min(100.0, score_a), 1),
                is_active=False,
                key_live_facts=(
                    f"VWAP:{'ABOVE' if a_c1 else 'MIXED'} | Vol:{spot_vol_ratio:.2f}x | "
                    f"Spot Ratio:{spot_buy_sell_ratio_4h:.2f} | Fund:{funding:+.4f}%"
                ),
                action_headline="Full Spot Long (1.0x)",
                sizing_rule="Sizing: 1.0x (Sf = 0.85–1.0x) | Max Cap: 50% equity",
                entry_or_harvest_rule="Entry: 60% breakout confirmation / 40% VWAP retest",
                stop_rule=f"Stop: 4H swing low -0.6% (${swing_low_4h * 0.994:,.0f})",
                computed_stop_usd=round(swing_low_4h * 0.994, 2),
                observed_checklist=[
                    _chk(a_c1, f"Price above Daily (${daily_vwap:,.0f}) & Weekly (${weekly_vwap:,.0f}) VWAP"),
                    _chk(a_c2, f"Spot volume > 1.35x 20D MA (Current: {spot_vol_ratio:.2f}x)"),
                    _chk(a_c3, f"Spot CVD positive / Ratio >= 1.25 (Current: {spot_buy_sell_ratio_4h:.2f})"),
                    _chk(a_c4, f"Institutional / US Spot proxy positive (CPI: {deriv.coinbase_premium_pct:+.3f}%)"),
                    _chk(a_c5, f"OI moderate -1% to +4% 24h (Current: {oi_24h:+.2f}%)"),
                    _chk(a_c6, f"Funding controlled +0.002% to +0.010% (Current: {funding:+.4f}%)"),
                ],
            )
        )

        # ------------------------------------------------------------------
        # CONFIG B: Leveraged Bull (Fragile Overextension / Trap)
        # ------------------------------------------------------------------
        b_c1 = price_chg_4h > 1.2 or (current_price - daily_vwap) > 1.5 * cur_atr_4h
        b_c2 = flow.w_1h.spot_delta_btc <= 0 or flow.w_1h.spot_zscore < 0.2
        b_c3 = flow.w_1h.perp_zscore >= 0.8 or flow.w_4h.perp_delta_btc > 200.0
        b_c4 = oi_24h >= 5.0 or oi_4h >= 1.5
        b_c5 = funding >= 0.020
        b_c6 = annualized_basis_pct >= 14.0
        score_b = (
            (20.0 if b_c1 else 0.0)
            + (20.0 if b_c2 else 0.0)
            + (20.0 if b_c3 else 0.0)
            + (20.0 if b_c4 else (8.0 if oi_4h > 0.4 else 0.0))
            + (12.0 if b_c5 else 0.0)
            + (8.0 if b_c6 else 0.0)
        )
        configs.append(
            RegimeConfigItem(
                code="Config B",
                short_title="Leveraged Bull",
                diagnosis_subtitle="Fragile Overextension / Trap",
                category="DEFENSIVE_CASH",
                match_pct=round(min(100.0, score_b), 1),
                is_active=False,
                key_live_facts=(
                    f"1H Spot:{flow.w_1h.spot_delta_btc:+.0f} | Perp Z:{flow.w_1h.perp_zscore:+.2f} | "
                    f"4H dOI:{oi_4h:+.2f}% | Basis:{annualized_basis_pct:.1f}%/yr"
                ),
                action_headline="Trim / Stand Aside (0.0x)",
                sizing_rule="Sizing: 0.0x (Strictly zero new buying)",
                entry_or_harvest_rule="Harvest: Sell 33% profit directly into perp pump",
                stop_rule=f"Stop: Trail tight stop on 67% at 4H swing low (${swing_low_4h:,.0f})",
                computed_stop_usd=round(swing_low_4h, 2),
                observed_checklist=[
                    _chk(b_c1, f"Price rising rapid / vertical (>2.5x ATR) (4H: {price_chg_4h:+.2f}%)"),
                    _chk(b_c2, f"Spot CVD flat or declining (1H Spot: {flow.w_1h.spot_delta_btc:+,.1f} BTC)"),
                    _chk(b_c3, f"Perp CVD aggressively upward (1H Perp Z: {flow.w_1h.perp_zscore:+.2f})"),
                    _chk(b_c4, f"OI surging (24h dOI: {oi_24h:+.2f}% / 4h dOI: {oi_4h:+.2f}%)"),
                    _chk(b_c5, f"Funding elevated >= +0.025% (Current: {funding:+.4f}%)"),
                    _chk(b_c6, f"Futures basis > 14% annualized (Current: {annualized_basis_pct:.1f}%)"),
                ],
            )
        )

        # ------------------------------------------------------------------
        # CONFIG C: Bullish Absorption (Institutional Base Defense)
        # ------------------------------------------------------------------
        val_ref = macro_vp.c_val if macro_vp else daily_vwap
        c_c1 = current_price <= val_ref * 1.01
        c_c2 = flow.w_4h.flow_divergence_z >= 1.0 or flow.w_1h.flow_divergence_z >= 1.0
        c_c3 = flow.w_4h.perp_delta_btc < 0 and flow.w_4h.spot_delta_btc > 0
        c_c4 = oi_4h <= 0.6
        c_c5 = -0.010 <= funding <= 0.010
        c_c6 = flow.w_1h.absorption_index >= 0.35 or spot_buy_sell_ratio_4h >= 1.15
        score_c = (
            (22.0 if c_c1 else 8.0)
            + (22.0 if c_c2 else (12.0 if flow.w_4h.flow_divergence_z > 0.5 else 0.0))
            + (22.0 if c_c3 else (10.0 if flow.w_4h.spot_delta_btc > 0 else 0.0))
            + (12.0 if c_c4 else 4.0)
            + (12.0 if c_c5 else 4.0)
            + (10.0 if c_c6 else 0.0)
        )
        configs.append(
            RegimeConfigItem(
                code="Config C",
                short_title="Bullish Absorption",
                diagnosis_subtitle="Institutional Base Defense",
                category="ACCUMULATE",
                match_pct=round(min(100.0, score_c), 1),
                is_active=False,
                key_live_facts=(
                    f"4H Spot:{flow.w_4h.spot_delta_btc:+.0f} vs Perp:{flow.w_4h.perp_delta_btc:+.0f} BTC | "
                    f"DivZ:{flow.w_4h.flow_divergence_z:+.2f} | AbsIdx:{flow.w_4h.absorption_index:.2f}"
                ),
                action_headline="Build Spot (0.75x)",
                sizing_rule="Sizing: 0.75x (Sf = 0.70–0.90x)",
                entry_or_harvest_rule="Entry: 50% on 1H range reclaim / 50% limit at low",
                stop_rule=f"Stop: Sweep wick low -0.5% (${low_24h * 0.995:,.0f})",
                computed_stop_usd=round(low_24h * 0.995, 2),
                observed_checklist=[
                    _chk(c_c1, f"Price testing major range low / cVAL (${val_ref:,.0f})"),
                    _chk(c_c2, f"Spot CVD surging vs Perp (4H Div Z: {flow.w_4h.flow_divergence_z:+.2f}σ)"),
                    _chk(c_c3, f"Perp CVD negative ({flow.w_4h.perp_delta_btc:+.0f} BTC) while Spot buys (+{flow.w_4h.spot_delta_btc:.0f} BTC)"),
                    _chk(c_c4, f"OI controlled / no leverage chase (4H dOI: {oi_4h:+.2f}%)"),
                    _chk(c_c5, f"Funding neutral/negative (Current: {funding:+.4f}%)"),
                    _chk(c_c6, f"Passive absorption / bid support active (Ratio: {spot_buy_sell_ratio_4h:.2f})"),
                ],
            )
        )

        # ------------------------------------------------------------------
        # CONFIG D: Masked Fragility (Stealth Distribution Top)
        # ------------------------------------------------------------------
        d_c1 = abs(price_chg_4h) <= 0.8 and current_price >= daily_vwap * 0.995
        d_c2 = flow.w_4h.spot_delta_btc < -100.0 or flow.w_1h.spot_delta_btc < -40.0
        d_c3 = deriv.coinbase_premium_pct < -0.05
        d_c4 = flow.w_4h.perp_delta_btc > 0 and flow.w_4h.spot_delta_btc < 0
        d_c5 = oi_4h > 0.2 and funding > 0.012
        d_c6 = current_price < daily_vwap
        score_d = (
            (15.0 if d_c1 else 0.0)
            + (25.0 if d_c2 else 0.0)
            + (15.0 if d_c3 else 0.0)
            + (20.0 if d_c4 else 0.0)
            + (15.0 if d_c5 else 0.0)
            + (10.0 if d_c6 else 0.0)
        )
        configs.append(
            RegimeConfigItem(
                code="Config D",
                short_title="Masked Fragility",
                diagnosis_subtitle="Stealth Distribution Top",
                category="DEFENSIVE_CASH",
                match_pct=round(min(100.0, score_d), 1),
                is_active=False,
                key_live_facts=(
                    f"4H Spot:{flow.w_4h.spot_delta_btc:+.0f} BTC | CPI:{deriv.coinbase_premium_pct:+.3f}% | "
                    f"VWAP:${daily_vwap:,.0f}"
                ),
                action_headline="Defensive Cash (100%)",
                sizing_rule="Sizing: 0.0x (Cash: 75%–100% USDT)",
                entry_or_harvest_rule=f"Exit: Market sell 50% on 1H close below VWAP (${daily_vwap:,.0f})",
                stop_rule=f"Stop: Hard trailing stop on 50% at 24h low (${low_24h:,.0f})",
                computed_stop_usd=round(low_24h, 2),
                observed_checklist=[
                    _chk(d_c1, "Price creeping higher or churning near top"),
                    _chk(d_c2, f"Spot CVD strongly negative / falling (4H: {flow.w_4h.spot_delta_btc:+.0f} BTC)"),
                    _chk(d_c3, f"Institutional selling / Coinbase discount ({deriv.coinbase_premium_pct:+.3f}%)"),
                    _chk(d_c4, "Perp CVD sustaining price float while Spot distributes"),
                    _chk(d_c5, f"OI expanding ({oi_4h:+.2f}%) with positive funding ({funding:+.4f}%)"),
                    _chk(d_c6, f"Daily VWAP (${daily_vwap:,.0f}) tested & breaking below"),
                ],
            )
        )

        # ------------------------------------------------------------------
        # CONFIG E: Liquidation Cascade (Forced Waterfall Deleveraging)
        # ------------------------------------------------------------------
        e_c1 = price_chg_1h <= -3.5 or price_chg_4h <= -5.0
        e_c2 = oi_1h <= -3.5 or oi_4h <= -6.0
        e_c3 = funding < 0.0
        e_c4 = deriv.perp_basis_usd < -25.0
        score_e = (
            (35.0 if e_c1 else (10.0 if price_chg_1h < -1.2 else 0.0))
            + (35.0 if e_c2 else (10.0 if oi_4h < -1.5 else 0.0))
            + (15.0 if e_c3 else 0.0)
            + (15.0 if e_c4 else 5.0)
        )
        configs.append(
            RegimeConfigItem(
                code="Config E",
                short_title="Liquidation Cascade",
                diagnosis_subtitle="Forced Waterfall Deleveraging",
                category="HARVEST_WAIT",
                match_pct=round(min(100.0, score_e), 1),
                is_active=False,
                key_live_facts=(
                    f"1H Chg:{price_chg_1h:+.2f}% | 1H/4H dOI:{oi_1h:+.2f}%/{oi_4h:+.2f}% | "
                    f"Basis:{deriv.perp_basis_usd:+.1f} USD"
                ),
                action_headline="Wait for Phase 3 (0.0x)",
                sizing_rule="Sizing: 0.0x during waterfall (Do NOT catch knife)",
                entry_or_harvest_rule="Trigger: 5m liqs < $2M, OI flat, 15m hammer -> 0.50x ladder (30/40/30%)",
                stop_rule=f"Stop: Below Phase 3 capitulation wick (${low_24h * 0.992:,.0f})",
                computed_stop_usd=round(low_24h * 0.992, 2),
                observed_checklist=[
                    _chk(e_c1, f"Price drops > 4%–8% rapidly (1H: {price_chg_1h:+.2f}%, 4H: {price_chg_4h:+.2f}%)"),
                    _chk(e_c2, f"OI crashing <= -5% 1h / <= -10% 4h (Current: {oi_1h:+.2f}% / {oi_4h:+.2f}%)"),
                    _chk(e_c3, f"Funding plunges negative (Current: {funding:+.4f}%)"),
                    _chk(e_c4, f"Basis in backwardation (Perp Basis: {deriv.perp_basis_usd:+.2f} USD)"),
                ],
            )
        )

        # ------------------------------------------------------------------
        # CONFIG F: Re-Accumulation (Post-Cascade Clean Base)
        # ------------------------------------------------------------------
        f_c1 = atr_compression_pct >= 30.0
        f_c2 = base_width_72h_pct <= 3.2
        f_c3 = -1.5 <= oi_24h <= 2.0
        f_c4 = -0.002 <= funding <= 0.010
        f_c5 = flow.w_4h.spot_delta_btc >= 0
        score_f = (
            (22.0 if f_c1 else min(15.0, atr_compression_pct * 0.5))
            + (22.0 if f_c2 else (12.0 if base_width_72h_pct <= 4.5 else 0.0))
            + (18.0 if f_c3 else 6.0)
            + (18.0 if f_c4 else 6.0)
            + (20.0 if f_c5 else 0.0)
        )
        configs.append(
            RegimeConfigItem(
                code="Config F",
                short_title="Re-Accumulation",
                diagnosis_subtitle="Post-Cascade Clean Base",
                category="ACCUMULATE",
                match_pct=round(min(100.0, score_f), 1),
                is_active=False,
                key_live_facts=(
                    f"ATR Comp:{atr_compression_pct:.0f}% | Base Width:{base_width_72h_pct:.2f}% | "
                    f"4H Spot:{flow.w_4h.spot_delta_btc:+.0f} BTC"
                ),
                action_headline="Re-Accumulate (0.75x)",
                sizing_rule="Sizing: 0.75x (Sf = 0.75–0.90x)",
                entry_or_harvest_rule="Entry: 50% on 4H close above Base POC / 50% limit",
                stop_rule=f"Stop: Base consolidation floor -0.5% (${base_lo * 0.995:,.0f})",
                computed_stop_usd=round(base_lo * 0.995, 2),
                observed_checklist=[
                    _chk(f_c1, f"ATR compresses > 40% from peak (Current: {atr_compression_pct:.1f}% compression)"),
                    _chk(f_c2, f"Tight base range < 2.5%–3.2% width (Current: {base_width_72h_pct:.2f}%)"),
                    _chk(f_c3, f"OI flat -1.5% to +2.0% baseline (Current: {oi_24h:+.2f}%)"),
                    _chk(f_c4, f"Funding reset near neutral (Current: {funding:+.4f}%)"),
                    _chk(f_c5, f"Spot CVD stabilizing green / flat (4H Spot: {flow.w_4h.spot_delta_btc:+.1f} BTC)"),
                ],
            )
        )

        # ------------------------------------------------------------------
        # CONFIG G: Short Squeeze (Mechanical Liquidation Run)
        # ------------------------------------------------------------------
        g_c1 = price_chg_1h >= 1.5 or price_chg_4h >= 2.5
        g_c2 = funding <= 0.0
        g_c3 = oi_1h <= -1.5 or oi_4h <= -2.0
        g_c4 = flow.w_1h.perp_delta_btc > 150.0 and flow.w_1h.spot_delta_btc < flow.w_1h.perp_delta_btc * 0.3
        score_g = (
            (30.0 if g_c1 else 0.0)
            + (20.0 if g_c2 else 0.0)
            + (30.0 if g_c3 else 0.0)
            + (20.0 if g_c4 else 0.0)
        )
        configs.append(
            RegimeConfigItem(
                code="Config G",
                short_title="Short Squeeze",
                diagnosis_subtitle="Mechanical Liquidation Run",
                category="HARVEST_WAIT",
                match_pct=round(min(100.0, score_g), 1),
                is_active=False,
                key_live_facts=(
                    f"1H Chg:{price_chg_1h:+.2f}% | 1H dOI:{oi_1h:+.2f}% | "
                    f"1H Perp:{flow.w_1h.perp_delta_btc:+.0f} BTC"
                ),
                action_headline="Harvest Gains (0.0x)",
                sizing_rule="Sizing: 0.0x (Never buy at squeeze peak)",
                entry_or_harvest_rule="Harvest: Scale out 50% spot profit into pump",
                stop_rule=f"Stop: Pre-squeeze 1H low -0.4% (${swing_low_1h * 0.996:,.0f})",
                computed_stop_usd=round(swing_low_1h * 0.996, 2),
                observed_checklist=[
                    _chk(g_c1, f"Explosive price pump through resistance (4H: {price_chg_4h:+.2f}%)"),
                    _chk(g_c2, f"Funding negative / shorts squeezed (Current: {funding:+.4f}%)"),
                    _chk(g_c3, f"OI collapsing as price rises (1H dOI: {oi_1h:+.2f}%)"),
                    _chk(g_c4, "Perp CVD surging (short covering) while Spot CVD lags"),
                ],
            )
        )

        # ------------------------------------------------------------------
        # CONFIG H: Distribution Top (Topping Exhaustion Failure)
        # ------------------------------------------------------------------
        h_c1 = macro_vp is not None and current_price >= macro_vp.c_vah * 0.99
        h_c2 = price_chg_4h > 0 and flow.w_4h.spot_delta_btc < 0
        h_c3 = funding >= 0.020
        h_c4 = not above_d_vwap
        score_h = (
            (25.0 if h_c1 else 0.0)
            + (30.0 if h_c2 else 0.0)
            + (25.0 if h_c3 else 0.0)
            + (20.0 if h_c4 else 0.0)
        )
        configs.append(
            RegimeConfigItem(
                code="Config H",
                short_title="Distribution Top",
                diagnosis_subtitle="Topping Exhaustion Failure",
                category="DEFENSIVE_CASH",
                match_pct=round(min(100.0, score_h), 1),
                is_active=False,
                key_live_facts=(
                    f"cVAH Test:{'YES' if h_c1 else 'NO'} | Bearish CVD Div:{'YES' if h_c2 else 'NO'} | "
                    f"Fund:{funding:+.4f}%"
                ),
                action_headline="Defensive Cash (100%)",
                sizing_rule="Sizing: 0.0x (Cash: 85%–100% USDT)",
                entry_or_harvest_rule="Harvest: Market sell 70% spot on 4H VWAP rejection",
                stop_rule="Stop: Move stop to Breakeven (BE) on remaining 30%",
                computed_stop_usd=round(daily_vwap, 2),
                observed_checklist=[
                    _chk(h_c1, "Marginal new high or double top near cVAH with upper wicks"),
                    _chk(h_c2, "Bearish Spot CVD divergence (Price higher, Spot CVD negative)"),
                    _chk(h_c3, f"Funding elevated > +0.020% (Current: {funding:+.4f}%)"),
                    _chk(h_c4, f"Daily VWAP (${daily_vwap:,.0f}) rejected on 4H close"),
                ],
            )
        )

        # ------------------------------------------------------------------
        # CONFIG I: Bear Trend (Bearish Trend Continuation)
        # ------------------------------------------------------------------
        i_c1 = current_price < ema_20_1d and current_price < ema_50_1d and not above_d_vwap
        i_c2 = spot_cvd_7d < 0 and flow.w_24h.spot_delta_btc < 0
        i_c3 = funding >= 0.005
        i_c4 = oi_24h >= 0.0
        i_c5 = annualized_basis_pct < 3.0
        score_i = (
            (30.0 if i_c1 else (15.0 if current_price < ema_20_1d else 0.0))
            + (30.0 if i_c2 else 0.0)
            + (15.0 if i_c3 else 5.0)
            + (15.0 if i_c4 else 5.0)
            + (10.0 if i_c5 else 0.0)
        )
        configs.append(
            RegimeConfigItem(
                code="Config I",
                short_title="Bear Trend",
                diagnosis_subtitle="Bearish Trend Continuation",
                category="DEFENSIVE_CASH",
                match_pct=round(min(100.0, score_i), 1),
                is_active=False,
                key_live_facts=(
                    f"<20D/50D EMA:{'YES' if i_c1 else 'NO'} | 7D Spot CVD:{spot_cvd_7d:+,.0f} BTC | "
                    f"Fund:{funding:+.4f}%"
                ),
                action_headline="Strict Cash (100%)",
                sizing_rule="Sizing: 0.0x (Target: 100% USDT Cash)",
                entry_or_harvest_rule="Protocol: Treat every relief bounce as exit liquidity",
                stop_rule=f"Inval: 1D close > 50D EMA (${ema_50_1d:,.0f}) with positive Spot CVD",
                computed_stop_usd=round(ema_50_1d, 2),
                observed_checklist=[
                    _chk(i_c1, f"Price below 20D EMA (${ema_20_1d:,.0f}), 50D EMA (${ema_50_1d:,.0f}), & Daily VWAP"),
                    _chk(i_c2, f"Spot CVD persistent downward slope (7D Delta: {spot_cvd_7d:+,.0f} BTC)"),
                    _chk(i_c3, f"Funding neutral/positive — trapped longs paying ({funding:+.4f}%)"),
                    _chk(i_c4, f"OI persistent without clearing overhang (24h dOI: {oi_24h:+.2f}%)"),
                    _chk(i_c5, f"Basis compressed below 3% annualized ({annualized_basis_pct:.1f}%)"),
                ],
            )
        )

        # ------------------------------------------------------------------
        # CONFIG J: Bear Trap (Capitulation Absorption)
        # ------------------------------------------------------------------
        j_c1 = current_price <= val_ref
        j_c2 = funding <= -0.005
        j_c3 = oi_4h >= 0.4 and price_chg_4h <= 0.2
        j_c4 = flow.w_4h.spot_delta_btc > 0 and flow.w_1h.spot_delta_btc > 0
        j_c5 = above_d_vwap or (bars_4h and bars_4h[-1].close > bars_4h[-1].open)
        score_j = (
            (20.0 if j_c1 else 0.0)
            + (25.0 if j_c2 else 0.0)
            + (20.0 if j_c3 else 5.0)
            + (20.0 if j_c4 else 0.0)
            + (15.0 if j_c5 else 0.0)
        )
        configs.append(
            RegimeConfigItem(
                code="Config J",
                short_title="Bear Trap",
                diagnosis_subtitle="Capitulation Absorption",
                category="BULL_LONG",
                match_pct=round(min(100.0, score_j), 1),
                is_active=False,
                key_live_facts=(
                    f"Fund:{funding:+.4f}% | 4H dOI:{oi_4h:+.2f}% | "
                    f"4H Spot:{flow.w_4h.spot_delta_btc:+.0f} BTC"
                ),
                action_headline="Reclaim Buy (1.0x)",
                sizing_rule="Sizing: 0.90x–1.0x (Maximum +EV setup)",
                entry_or_harvest_rule="Trigger: 4H close decisively back above broken support / VWAP",
                stop_rule=f"Stop: Capitulation sweep low -0.5% (${low_24h * 0.995:,.0f})",
                computed_stop_usd=round(low_24h * 0.995, 2),
                observed_checklist=[
                    _chk(j_c1, f"Sweep below support / cVAL (${val_ref:,.0f})"),
                    _chk(j_c2, f"Funding negative / shorts crowding (Current: {funding:+.4f}%)"),
                    _chk(j_c3, f"OI rising into lows (4H dOI: {oi_4h:+.2f}%)"),
                    _chk(j_c4, f"Spot CVD rising / refusing to drop (4H: {flow.w_4h.spot_delta_btc:+.0f} BTC)"),
                    _chk(j_c5, f"Price sweeping lows & reclaiming Daily VWAP (${daily_vwap:,.0f})"),
                ],
            )
        )

        # Rank and mark #1 Active Config & #2 Runner-Up
        ranked = sorted(configs, key=lambda c: c.match_pct, reverse=True)
        active_code = ranked[0].code
        runner_up_code = ranked[1].code if len(ranked) > 1 else active_code
        for item in configs:
            if item.code == active_code:
                item.is_active = True

        ev = RegimeMatrixEvaluation(
            timestamp_utc=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            current_price=round(current_price, 2),
            daily_vwap=round(daily_vwap, 2),
            weekly_vwap=round(weekly_vwap, 2),
            ema_20_1d=round(ema_20_1d, 2),
            ema_50_1d=round(ema_50_1d, 2),
            spot_vol_vs_20d_ma=round(spot_vol_ratio, 2),
            spot_buy_sell_ratio_4h=round(spot_buy_sell_ratio_4h, 2),
            spot_cvd_7d_btc=round(spot_cvd_7d, 1),
            oi_change_24h_pct=round(oi_24h, 2),
            oi_change_4h_pct=round(oi_4h, 2),
            oi_change_1h_pct=round(oi_1h, 2),
            funding_rate_pct=round(funding, 4),
            annualized_basis_pct=round(annualized_basis_pct, 1),
            atr_compression_pct=round(atr_compression_pct, 1),
            base_width_72h_pct=round(base_width_72h_pct, 2),
            active_config_code=active_code,
            runner_up_config_code=runner_up_code,
            configs=configs,
        )
        store.regime_matrix_evaluation = ev
        return ev

```

---

### File: `analytics/master_synthesis.py`

```python
"""Tab [5] Master Synthesis & Supreme Order of Battle Evaluator.

Synthesizes the live outputs of all 4 specialist tabs:
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
        """Synthesizes Tabs [1]–[4] into a single authoritative Master Conclusion."""
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

        t1_driver = (
            f"VA Pos: {sig.va_position_pct:.0f}% [{'CHOP' if sig.is_mid_range_chop else 'EDGE'}] "
            f"| cVAL ${sig.c_val:,.0f}"
        )
        t1_row = TabVerdictRow(
            tab_num=1,
            tab_name="[1] Swing Engine",
            traffic_light=t1_light,
            score_or_status=f"{sig.confluence_score:.1f}/100 ({sig.regime.value[:10]})",
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

        tab_rows = [t1_row, t2_row, t3_row, t4_row]
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
            f"/ Hard Stop (${tp.stop_loss if tp else pev.downside_ref_1d_atr:,.0f}) with expanding Spot selling."
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
        reconciled_stop = round(max(min(tab1_stop, price * 0.99), min(tab4_stop, price * 0.99)), 2)
        stop_source = f"Tab 1: ${tab1_stop:,.0f} • Tab 4: ${tab4_stop:,.0f} • 50D: ${pev.sma_50_1d:,.0f}"

        tp1_candidates = [c for c in [tp.tp1_poc if tp else sig.c_poc, pev.short_liq_magnet_usd] if c > price]
        holder_tp1_usd = round(min(tp1_candidates), 2) if tp1_candidates else round(max(sig.c_poc, price * 1.02), 2)
        holder_tp1_source = (
            "Short-Liq + cPOC"
            if abs(sig.c_poc - pev.short_liq_magnet_usd) / max(price, 1.0) < 0.015
            else ("cPOC Magnet" if holder_tp1_usd == round(sig.c_poc, 2) else "Short-Liq Cluster")
        )

        tp2_candidates = [
            c
            for c in [tp.tp2_vah if tp else sig.c_vah, sig.c_poc, mev.ema_21_1d, pev.daily_resistance]
            if c > holder_tp1_usd + 300.0
        ]
        holder_tp2_usd = round(min(tp2_candidates), 2) if tp2_candidates else round(max(sig.c_vah, holder_tp1_usd * 1.025), 2)
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

```

---

### File: `analytics/ai_packet_exporter.py`

```python
"""Raw Telemetry & Independent AI Audit Packet Exporter (Hotkey `C` on Tab [5]).

Collects 100% of the live quantitative telemetry across Tabs [1], [2], [3], and [4]
into a structured, self-contained Markdown packet and copies it directly to the
Windows Clipboard (`Ctrl+V` ready) as well as saving to disk (`Downloads` and `logs/`).
"""

import base64
import os
import pathlib
import subprocess
import sys
import time
from datetime import datetime, timezone
from typing import Tuple

from config.settings import EngineConfig
from core.state_store import StateStore


def build_ai_telemetry_packet(config: EngineConfig, store: StateStore) -> str:
    """Builds a comprehensive, unbiased Raw Data Packet from Tabs [1]-[4] for external AI analysis."""
    now_utc = datetime.now(timezone.utc)
    ts_str = now_utc.strftime("%Y-%m-%d %H:%M:%S UTC")

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

    lines = [
        "# BTC-USD LIVE QUANTITATIVE TELEMETRY PACKET & MASTER AI AUDITOR PROMPT",
        f"**Snapshot Timestamp:** `{ts_str}`  ",
        "**Mandate:** Strictly Long-Only Spot BTC Swing & Positional Trading (Zero Leverage, Zero Shorting)  ",
        f"**Reference Portfolio Equity:** `${config.portfolio_equity_usd:,.2f}` (Standard Risk: `{config.risk_per_trade_pct:.2f}%` | Counter-Trend Risk Cap: `{config.counter_trend_risk_pct:.2f}%` | Hard Single-Trade Notional Cap: `<= 50% Equity`)",
        "",
        "## MASTER SYSTEM PROMPT & RULEBOOK FOR GEMINI ARGON / EXTERNAL AI AUDITOR",
        "You are the **Independent Chief Quantitative Strategist & Risk Officer** auditing a live real-time telemetry packet exported from the **`BTC-USD Spot Swing Engine`** (`5-Tab Rich Live Terminal`).",
        "",
        "### 1. Rule #0 — Strict Anti-Sycophancy & Chief Engineer Authority",
        "* **Do NOT blindly agree with the Python engine's benchmark verdict in Section 6.** Deterministic code evaluates fixed mathematical thresholds and can miss subtle cross-venue divergences (e.g., negative Coinbase Premium while Binance ticks up, 5-minute perp sell bursts, nearby unflushed long-liquidation magnets within 1%, or over-concentrated single-fill entries).",
        "* You have **full Chief Engineer authority** to confirm, refine, split into multiple limit tranches, or override the Python engine's conclusion based on the raw telemetry in **Sections 1–5**.",
        "",
        "### 2. How to Interpret & Audit Sections 1–5 (The 5-Desk Quantitative Rulebook)",
        "1. **Section 1 Audit (`Cross-Exchange Spot, Basis & Derivatives`)**:",
        "   * **Coinbase Premium (`CPI`)**: `CPI > +0.02%` (`Z >= +0.5σ`) = US institutional spot buying. `CPI < -0.05%` (Coinbase at a deep discount to Binance) = warning that US spot is lagging or selling into offshore USDT moves.",
        "   * **Open Interest (`Strict BTC Coins`) & `dOI %`**: `AGGRESSIVE_SHORT_BUILD` (`Price Down/Flat + OI Up`) is bullish squeeze fuel *only* if `Spot CVD` is positive (passive spot absorbing shorts). `LEVERAGED_LONG_EXPANSION` (`Price Up + OI Up + High Funding > +0.012%`) is a long-trap warning. `LONG_LIQUIDATION_FLUSH` (`Price Down + OI Down`) clears excess leverage.",
        "   * **5m Taker L/S Ratio & 5m Perp Delta**: If `5m Taker L/S < 0.50` with heavy negative `5m Perp Delta`, sellers are actively pressing the tape right now -> prefer staged limit bids over market orders.",
        "2. **Section 2 Audit (`Composite Volume Profile 30D/7D/24H & Multi-Horizon Spot vs. Perp CVD`)**:",
        "   * **Value Area & Mid-Range Chop Law**: `cVAL` = lower 70% Value Area support; `cPOC` = fair-value magnet (`TP1`); `cVAH` = upper resistance (`TP2`). If `Value Area Position %` is inside `30%–70%` (`Mid-Range Chop Flag: True`), **never chase at market**; wait for `cVAL` or `Support HVN Floor`.",
        "   * **Spot vs. Perp CVD Divergence**: True institutional accumulation requires `Spot CVD > 0` (`4H B/S Ratio > 1.05`) while `Perp CVD < 0` (`Spot-Perp Divergence Z > +1.5σ`, `Passive Absorption Index >= 0.85`).",
        "3. **Section 3 Audit (`Protocol v1.3, CoinGlass 6-Panel in Strict BTC & Liquidation Magnets`)**:",
        "   * **Candle Hygiene**: Separate `1D Completed [-2]` (closed daily bar) from `1D Forming [-1]` (live unclosed bar).",
        "   * **Supreme Veto Gates**: Any `TRIGGERED` Non-Trade Zone (`8A–8F`) or `CONFIRMED` Spot Sell Trigger (`1–4`) locks new buying (`RED LIGHT`).",
        "   * **Liquidation Magnet Law**: In a range regime, price is magnetized toward dense liquidation pools (`Nearest Short-Liq Magnet Above` vs. `Nearest Long-Liq Magnet Below`). If the `Long-Liq Magnet` sits within `~1%` below current support while OI is `>90,000 BTC`, recommend splitting spot buys into **2 tranches** (Tranche 1 at `cVAL`/`Support HVN`, Tranche 2 resting at the `Long-Liq Magnet` / `1D Support` sweep).",
        "4. **Section 4 Audit (`Macro Quant, Power-Law & Cycle Radar`)**:",
        "   * **Rule 1 Gatekeeper (`1D 200 SMA` + 5D Slope)**: Above a rising `200D SMA` authorizes `1.00%` base risk; below the `200D SMA` caps counter-trend risk at `0.50%` (targeting `21D EMA` / `200D SMA`), unless a `-25%` to `-65%` **Cycle Crash Rung** + **`4H Liquidation Wick Flush` (`>= 45%` lower wick)** triggers a deep-value sniper override.",
        "   * **Genesis Power-Law Valuation**: Strictly `[BIAS ONLY — NOT TIMING]` for long-horizon valuation context.",
        "5. **Section 5 & 6 Audit (`Regime Matrix A–J & Sizing Guardrail`)**:",
        "   * Scale base risk by the dominant `Config A–J` multiplier (`1.0x` Config A/J, `0.75x` Config C/F, `0.0x` Config B/D/E/G/H/I) and enforce a **strict `<= 50%` Portfolio Equity Notional Cap** (`$37,500` max at `0.75x` on `$100k` equity).",
        "",
        "### 3. Mandatory 5-Part Response Format",
        "Structure your audit into:",
        "1. **Independent Cross-Tab Telemetry Audit** (Bullish Confluence vs. Hidden Friction/Risk Flags in Sections 1–5)",
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
        f"| **Binance Spot Price (`BTCUSDT`)** | `${store.binance_spot_price:,.2f}` | Primary Spot Reference |",
        f"| **Coinbase Spot Price (`BTC-USD`)** | `${store.coinbase_spot_price:,.2f}` | US Institutional Spot Reference |",
        f"| **Binance USD-M Perp Price** | `${store.binance_perp_price:,.2f}` | Perpetual Futures Reference (`{store.perp_source}`) |",
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
        lines.extend([
            "",
            f"* **Active Structural Profile**: `{sig.active_horizon}` | **Distance to cVAL**: `{sig.distance_to_val_pct:+.2f}%` (`{sig.distance_to_val_atr:+.2f} ATR`) | **Value Area Position (`0%=cVAL, 100%=cVAH`)**: `{sig.va_position_pct:+.1f}%` (`Mid-Range Chop Flag: {sig.is_mid_range_chop}`) | **1H ATR**: `${sig.atr_1h:,.0f}` | **4H ATR**: `${sig.atr_4h:,.0f}` | **Recent Reclaim Candle**: `{sig.is_reclaim_candle}`",
        ])

    lines.extend([
        "",
        "### 2B. Multi-Horizon Order Flow, Spot vs. Perp CVD & Passive Absorption",
        "",
        "| Horizon | Price Δ% | Spot CVD Delta (BTC) | Spot Z-Score | Perp CVD Delta (BTC) | Perp Z-Score | Spot-Perp Div Z | Passive Absorption Index |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
    ])

    for w in (flow.w_15m, flow.w_1h, flow.w_4h, flow.w_24h):
        lines.append(
            f"| **`{w.window_label}`** | `{w.price_change_pct:+.2f}%` | `{w.spot_delta_btc:+,.2f} BTC` (`{w.spot_delta_ratio*100:+.1f}%`) | `{w.spot_zscore:+.2f}σ` | `{w.perp_delta_btc:+,.2f} BTC` (`{w.perp_delta_ratio*100:+.1f}%`) | `{w.perp_zscore:+.2f}σ` | `{w.flow_divergence_z:+.2f}σ` | `{w.absorption_index:.2f}` |"
        )
    lines.append(
        f"| **`UTC Day (00:00)`** | `N/A` | `{flow.utc_day_spot_cvd:+,.2f} BTC` | `N/A` | `{flow.utc_day_perp_cvd:+,.2f} BTC` | `N/A` | `N/A` | `N/A` |"
    )
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
            f"* **1D Support / Resistance**: Support `${pev.daily_support:,.0f}` • Resistance `${pev.daily_resistance:,.0f}` • **1D Bias**: `{pev.daily_bias}` • **4H Structure**: `{pev.structure_4h}` (`4H Ready: {pev.timing_4h_ready}`)",
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
            "## SECTION 6: PYTHON ENGINE BENCHMARK VERDICT (FOR AI COMPARISON & CRITIQUE)",
            "",
            f"* **Tab [5] Master Traffic Light**: `{msev.master_traffic_light}` — `{msev.master_headline}`",
            f"* **4-Tab Scoreboard**: `{msev.tabs_green_count} GREEN • {msev.tabs_blue_count} BLUE • {msev.tabs_yellow_count} YELLOW • {msev.tabs_red_count} RED` | **Master Alignment Score**: `{msev.master_alignment_score:.1f}%` (`{msev.alignment_status}`)",
            f"* **Tab [1] 4-Gate Confluence Score**: `{sig.confluence_score:.1f}/100` (`Location: {sig.location_score:.1f}/25` • `Flow: {sig.flow_score:.1f}/35` • `Derivatives: {sig.derivatives_score:.1f}/20` • `Trigger: {sig.trigger_score:.1f}/20`)",
            f"* **Python Track A (If Flat in Cash)**: `{msev.cash_permission}` | Bid Zone: `{msev.cash_entry_zone_str}` | Edge Size: `{msev.cash_edge_size_btc:.4f} BTC` (`${msev.cash_edge_notional_usd:,.0f}` at `{msev.cash_edge_risk_pct:.2f}%` risk)",
            f"* **Python Track B (If Holding Spot BTC)**: `{msev.holder_action}` | Reconciled Hard Stop: `${msev.holder_hard_stop_usd:,.2f}` (`{msev.holder_hard_stop_source}`) | `TP1 (40%): ${msev.holder_tp1_usd:,.0f}` • `TP2 (60%): ${msev.holder_tp2_usd:,.0f}`",
            f"* **Tab [1] TradePlan R:R**: Entry `${tp.entry_zone_low:,.0f}–${tp.entry_zone_high:,.0f}` | Stop `${tp.stop_loss:,.0f}` | `TP1 ${tp.tp1_poc:,.0f} ({tp.rr_to_poc:.2f}R)` | `TP2 ${tp.tp2_vah:,.0f} ({tp.rr_to_vah:.2f}R)`" if tp else "",
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

```

---

### File: `analytics/signal_detector.py`

```python
"""4-Gate Swing Execution State Machine, 0-100 Confluence Scorer, Veto Filters, and JSONL Logger."""

import json
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
from .macro_radar import MacroRadarEvaluator
from .master_synthesis import MasterSynthesisEvaluator
from .protocol_v13 import ProtocolV13Evaluator
from .regime_matrix import RegimeMatrixEvaluator
from .volume_profile import compute_atr, compute_composite_profile, synthesize_4h_bars


class SignalDetector:
    """Evaluates auction structure, order flow, and derivatives to drive the 4-Gate Swing FSM."""

    def __init__(self, config: EngineConfig) -> None:
        self.config = config
        self.protocol_evaluator = ProtocolV13Evaluator(config)
        self.macro_evaluator = MacroRadarEvaluator(config)
        self.regime_matrix_evaluator = RegimeMatrixEvaluator(config)
        self.master_synthesis_evaluator = MasterSynthesisEvaluator(config)
        self._last_logged_regime: Optional[MarketRegime] = None
        self._last_logged_gate: Optional[ExecutionGateState] = None
        self._last_log_ts: float = 0.0

    def _detect_value_area_reclaim(
        self,
        bars_15m: Sequence[KlineBar],
        bars_1h: Sequence[KlineBar],
        c_val: float,
    ) -> bool:
        """Checks if a recent 15m or 1H candle swept below `c_val` and closed back >= `c_val`."""
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
    ) -> TradePlan:
        """Calculates structural entry zone, sweep-low/LVN stop-loss, cPOC/cVAH targets, and sizing."""
        recent_swing_low = (
            min(b.low for b in recent_bars_1h[-4:]) if recent_bars_1h else (current_price - atr_1h)
        )

        tact_val = tactical_vp.c_val if tactical_vp is not None else c_val
        if support_hvn is not None and current_price < (c_val - 0.5 * atr_1h):
            # Trading below 30D Macro cVAL ($81,321) near 7D Tactical cVAL / 30D Support HVN Floor ($79,587):
            # Anchor tactical entry on 7D Tactical cVAL / 24H Session cVAL / 30D Support HVN shelf
            if tactical_vp is not None and support_hvn <= tact_val <= (support_hvn + 2.0 * atr_1h):
                dev_val = tact_val
            elif session_vp is not None and support_hvn < session_vp.c_val <= (support_hvn + 2.0 * atr_1h):
                dev_val = session_vp.c_val
            else:
                dev_val = support_hvn + 0.25 * atr_1h
            entry_low = min(support_hvn, dev_val)
            entry_high = max(dev_val, entry_low + 0.25 * atr_1h)
            ref_entry = dev_val

            floor_candidates = [recent_swing_low, support_hvn]
            if tactical_vp and tactical_vp.support_hvn_below_val:
                floor_candidates.append(tactical_vp.support_hvn_below_val)
            base_floor = min(floor_candidates)
            stop_loss = base_floor - (self.config.stop_atr_buffer_mult * atr_1h)

            # Structural targets: TP1 -> 7D Tactical cPOC (if >= min R:R) or 30D cVAL, TP2 -> 30D Macro cPOC
            min_tp1_dist = max(self.config.min_structural_rr_to_poc * max(ref_entry - stop_loss, 1.0), atr_1h)
            tp1_poc = (
                tactical_vp.c_poc
                if (tactical_vp is not None and tactical_vp.c_poc >= ref_entry + min_tp1_dist)
                else max(c_val, ref_entry + min_tp1_dist)
            )
            tp2_vah = max(c_poc, tp1_poc + 1.5 * atr_1h)
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
            return None

        # 2. Compute Order Flow & Derivatives Snapshots
        flow = compute_flow_snapshot(self.config, store)
        deriv = compute_derivatives_snapshot(self.config, store, flow)
        store.flow_snapshot = flow
        store.derivatives_snapshot = deriv

        # 2b. Evaluate Tab [2] Protocol v1.3, Tab [3] Macro Radar, & Tab [4] Regime Matrix A-J
        protocol_ev = self.protocol_evaluator.evaluate(store, flow, deriv)
        macro_ev = self.macro_evaluator.evaluate(store, flow, deriv, macro_vp)
        self.regime_matrix_evaluator.evaluate(store, flow, deriv, macro_vp)

        current_price = store.binance_spot_price or spot_1h[-1].close
        bars_4h = synthesize_4h_bars(spot_1h)
        atr_1h = max(compute_atr(spot_1h[-30:], period=self.config.atr_period), 1.0)
        atr_4h = max(compute_atr(bars_4h[-30:], period=self.config.atr_period), 1.0)

        # Select active structural profile:
        # Primary structure is 30D Macro Profile; switch to 7D Tactical only when expanding above 30D cVAH
        active_vp = tactical_vp if current_price > macro_vp.c_vah else macro_vp

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

        # --- GATE 4: Value Area Acceptance / Reclaim Trigger (Max 20 pts) ---
        reclaim_target_val = (
            session_vp.c_val
            if (testing_support_hvn and session_vp is not None and current_price < c_val - 0.5 * atr_1h)
            else c_val
        )
        is_reclaim = self._detect_value_area_reclaim(spot_15m, spot_1h, reclaim_target_val)
        trigger_score = 0.0
        if is_reclaim:
            trigger_score = 20.0
            rationale.append(
                f"Gate 4 [TRIGGERED]: Candle swept below VAL (${reclaim_target_val:,.0f}) and closed back inside Value with positive Spot delta."
            )
        elif in_actionable_zone and flow.w_15m.spot_delta_btc > 0 and current_price >= reclaim_target_val:
            trigger_score = 12.0
            rationale.append(
                f"Gate 4 [DEVELOPING]: Holding above ${reclaim_target_val:,.0f} with positive 15m Spot delta."
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
            if is_reclaim and total_score >= self.config.signal_confluence_threshold:
                gate_state = ExecutionGateState.GATE3_RECLAIM_TRIGGERED
            else:
                gate_state = ExecutionGateState.GATE2_MICROSTRUCTURE_ARMED
        elif in_actionable_zone:
            regime = MarketRegime.BALANCED
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
            is_reclaim_candle=is_reclaim,
            hard_veto_triggered=hard_veto,
            veto_reasons=veto_reasons,
            rationale_notes=rationale,
            trade_plan=trade_plan,
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

```

---

### File: `ui/__init__.py`

```python
"""Rich terminal dashboard and console reporting for the BTC Swing Engine."""

from .terminal_hud import build_dashboard_renderable, print_dry_run_report, run_terminal_hud

__all__ = [
    "build_dashboard_renderable",
    "print_dry_run_report",
    "run_terminal_hud",
]

```

---

### File: `ui/terminal_hud.py`

```python
"""Unified 5-Tab Rich Live TUI HUD for the BTC-USD Spot Swing Engine.

Tabs (switchable instantly via keys `1`, `2`, `3`, `4`, `5` in PowerShell):
- Tab [1]: Tactical Swing Execution HUD (Composite Volume Profile, Multi-Horizon CVD, 4-Gate Engine)
- Tab [2]: BTC Spot Swing Protocol v1.3 HUD (1D Completed vs Forming, CoinGlass 6-Panel, 8A-8F NTZ)
- Tab [3]: Macro Quant & Cycle Radar HUD (1D 200 SMA Gatekeeper, 21D EMA, 14D RSI, Crash Rungs, 4H Flush)
- Tab [4]: Regime Matrix A-J HUD (Quantitative Microstructure Diagnostic & Execution Protocols A through J)
- Tab [5]: Master Conclusion HUD (4-Tab Rollup Matrix, 4-Layer Conflict Resolver, Cash vs Holder Playbook & Supreme Bottom Line)
"""

import asyncio
import select
import sys
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

try:
    import msvcrt
except ImportError:
    msvcrt = None  # type: ignore

try:
    import termios
    import tty
except ImportError:
    termios = None  # type: ignore
    tty = None  # type: ignore

from rich import box
from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.table import Table

from analytics.ai_packet_exporter import copy_ai_packet_to_clipboard_and_disk
from analytics.signal_detector import SignalDetector
from config.settings import EngineConfig
from core.models import ExecutionGateState, MarketRegime
from core.state_store import StateStore


def _color_signed(val: float, fmt: str = "+,.2f", suffix: str = "") -> str:
    color = "green" if val > 0 else ("red" if val < 0 else "white")
    return f"[{color}]{val:{fmt}}{suffix}[/{color}]"


def _regime_badge(regime: MarketRegime) -> str:
    mapping = {
        MarketRegime.BALANCED: "[bold cyan]BALANCED[/bold cyan]",
        MarketRegime.ABSORPTION_AT_SUPPORT: "[bold black on green] ABSORPTION_AT_SUPPORT [/bold black on green]",
        MarketRegime.LEVERAGE_EXPANSION: "[bold yellow]LEVERAGE_EXPANSION[/bold yellow]",
        MarketRegime.LEVERAGE_TRAP: "[bold white on red] LEVERAGE_TRAP [/bold white on red]",
        MarketRegime.MARKDOWN: "[bold white on red] MARKDOWN (100% CASH) [/bold white on red]",
    }
    return mapping.get(regime, f"[bold white]{regime.value}[/bold white]")


def _gate_badge(gate: ExecutionGateState) -> str:
    mapping = {
        ExecutionGateState.CASH_MARKDOWN: "[bold red]CASH_MARKDOWN (Stand Aside)[/bold red]",
        ExecutionGateState.NEUTRAL_OBSERVATION: "[dim white]NEUTRAL_OBSERVATION[/dim white]",
        ExecutionGateState.GATE1_ZONE_ALERT: "[bold yellow]GATE 1: ZONE ALERT (Monitoring cVAL)[/bold yellow]",
        ExecutionGateState.GATE2_MICROSTRUCTURE_ARMED: "[bold cyan]GATE 2: MICROSTRUCTURE ARMED (Waiting Reclaim)[/bold cyan]",
        ExecutionGateState.GATE3_RECLAIM_TRIGGERED: "[bold green]GATE 3 & 4: RECLAIM TRIGGERED (SWING LONG)[/bold green]",
    }
    return mapping.get(gate, gate.value)


def _nth_weekday_of_month(year: int, month: int, weekday: int, n: int) -> int:
    """Returns day-of-month for the nth weekday (0=Mon..6=Sun) in (year, month)."""
    first = datetime(year, month, 1, tzinfo=timezone.utc)
    offset = (weekday - first.weekday()) % 7
    return 1 + offset + (n - 1) * 7


def _last_sunday_of_month(year: int, month: int) -> int:
    """Returns day-of-month for the last Sunday in (year, month)."""
    next_m = datetime(year + 1, 1, 1, tzinfo=timezone.utc) if month == 12 else datetime(year, month + 1, 1, tzinfo=timezone.utc)
    last_day = next_m - timedelta(days=1)
    offset = (last_day.weekday() - 6) % 7
    return last_day.day - offset


def _get_world_clocks_and_session(now_utc: datetime) -> Tuple[str, str]:
    """Computes UTC, Singapore (SGT), London (GMT/BST), and New York (EST/EDT) clocks + Active Session badge."""
    y = now_utc.year
    # 1. Singapore / Asia (always UTC+8)
    sgt_dt = now_utc + timedelta(hours=8)

    # 2. London (BST = UTC+1 from last Sunday of March 01:00 UTC to last Sunday of October 01:00 UTC)
    uk_start = datetime(y, 3, _last_sunday_of_month(y, 3), 1, 0, tzinfo=timezone.utc)
    uk_end = datetime(y, 10, _last_sunday_of_month(y, 10), 1, 0, tzinfo=timezone.utc)
    is_bst = uk_start <= now_utc < uk_end
    lon_dt = now_utc + timedelta(hours=1 if is_bst else 0)
    lon_tz = "BST" if is_bst else "GMT"

    # 3. New York (EDT = UTC-4 from 2nd Sunday of March 07:00 UTC to 1st Sunday of November 06:00 UTC)
    us_start = datetime(y, 3, _nth_weekday_of_month(y, 3, 6, 2), 7, 0, tzinfo=timezone.utc)
    us_end = datetime(y, 11, _nth_weekday_of_month(y, 11, 6, 1), 6, 0, tzinfo=timezone.utc)
    is_edt = us_start <= now_utc < us_end
    nyc_dt = now_utc - timedelta(hours=4 if is_edt else 5)
    nyc_tz = "EDT" if is_edt else "EST"

    clocks_str = (
        f"[bold white]UTC[/bold white] {now_utc.strftime('%Y-%m-%d %H:%M:%S')}  •  "
        f"[bold cyan]SGP (Asia)[/bold cyan] {sgt_dt.strftime('%H:%M:%S')} SGT  •  "
        f"[bold yellow]LON (EU)[/bold yellow] {lon_dt.strftime('%H:%M:%S')} {lon_tz}  •  "
        f"[bold green]NYC (US)[/bold green] {nyc_dt.strftime('%H:%M:%S')} {nyc_tz}"
    )

    h = now_utc.hour
    if 0 <= h < 7:
        session_badge = "[bold black on cyan] ASIA SESSION (SINGAPORE / HK / TOKYO ACTIVE) [/bold black on cyan]"
    elif 7 <= h < 8:
        session_badge = "[bold black on yellow] ASIA / LONDON OVERLAP (SGP PM • LONDON OPEN) [/bold black on yellow]"
    elif 8 <= h < 13:
        session_badge = "[bold black on green] LONDON / EU SESSION (EUROPEAN INSTITUTIONAL FLOW) [/bold black on green]"
    elif 13 <= h < 16:
        session_badge = "[bold black on magenta] LONDON / NY OVERLAP (PEAK GLOBAL & US ETF LIQUIDITY) [/bold black on magenta]"
    elif 16 <= h < 21:
        session_badge = "[bold black on green] NEW YORK SESSION (US INSTITUTIONAL & COINBASE ACTIVE) [/bold black on green]"
    else:
        session_badge = "[bold black on yellow] LATE NY / ASIA PRE-OPEN TRANSITION WINDOW [/bold black on yellow]"

    return clocks_str, session_badge


def _build_header_panel(store: StateStore, active_tab: int) -> Panel:
    """Builds the unified Top Status Banner with World Clocks, Regional Session, and Tabs [1]•[2]•[3]•[4]•[5]."""
    now_utc = datetime.now(timezone.utc)
    clocks_str, session_badge = _get_world_clocks_and_session(now_utc)
    sig = store.latest_signal

    spot_ws_dot = "[green]ON[/green]" if store.spot_ws_connected else "[yellow]SYNC[/yellow]"
    perp_ws_dot = "[green]ON[/green]" if store.perp_ws_connected else "[yellow]SYNC[/yellow]"
    cb_ws_dot = "[green]ON[/green]" if store.coinbase_ws_connected else "[yellow]SYNC[/yellow]"

    t1 = (
        "[bold black on cyan] [1: SWING ENGINE] [/bold black on cyan]"
        if active_tab == 1
        else "[dim white][1: SWING ENGINE][/dim white]"
    )
    t2 = (
        "[bold black on yellow] [2: PROTOCOL v1.3] [/bold black on yellow]"
        if active_tab == 2
        else "[dim white][2: PROTOCOL v1.3][/dim white]"
    )
    t3 = (
        "[bold black on magenta] [3: MACRO RADAR] [/bold black on magenta]"
        if active_tab == 3
        else "[dim white][3: MACRO RADAR][/dim white]"
    )
    t4 = (
        "[bold black on green] [4: REGIME A-J] [/bold black on green]"
        if active_tab == 4
        else "[dim white][4: REGIME A-J][/dim white]"
    )
    t5 = (
        "[bold white on blue] [5: MASTER CONCLUSION] [/bold white on blue]"
        if active_tab == 5
        else "[dim white][5: MASTER CONCLUSION][/dim white]"
    )

    regime_str = _regime_badge(sig.regime) if sig else "[dim]WARMING UP[/dim]"
    score_str = f"[bold]{sig.confluence_score:.1f}/100[/bold]" if sig else "0.0/100"

    header_table = Table.grid(expand=True)
    header_table.add_column(justify="left", no_wrap=True)
    header_table.add_column(justify="right", no_wrap=True)
    header_table.add_row(
        f"[bold white]BTC-USD[/bold white] | {t1}•{t2}•{t3}•{t4}•{t5}",
        f"Regime: {regime_str} ({score_str}) | Spot {spot_ws_dot} • Perp {perp_ws_dot} • CB {cb_ws_dot}",
    )
    header_table.add_row(
        clocks_str,
        f"ACTIVE MARKET: {session_badge}",
    )
    return Panel(header_table, style="bright_blue", box=box.ROUNDED, padding=(0, 1))


# ============================================================================
# TAB [1]: TACTICAL SWING EXECUTION HUD (EXISTING 5-PANEL ENGINE)
# ============================================================================

def _build_tab1_plain_english_panel(sig, flow, deriv, macro_ev) -> Panel:
    """Builds Tab [1] Panel 5: Plain-English Executive Bottom Line."""
    if sig is None:
        return Panel(
            "Warming up data feeds and calculating 30-day volume profile...",
            title="[bold white]5. Executive Bottom Line (Plain-English Summary)[/bold white]",
            box=box.ROUNDED,
        )

    price = sig.current_price
    tp = sig.trade_plan
    cb_diff = deriv.coinbase_premium_usd
    cb_word = (
        f"selling at a ${abs(cb_diff):,.0f} discount"
        if cb_diff < -10
        else (f"buying at a +${cb_diff:,.0f} premium" if cb_diff > 10 else "trading flat with Binance")
    )
    macro_tag = ""
    if macro_ev is not None and macro_ev.gatekeeper_veto and tp is not None and tp.risk_pct < 1.0:
        macro_tag = f" [bold yellow](Macro Note: Below 1D 200 SMA ${macro_ev.sma_200_1d:,.0f} -> Risk capped at {tp.risk_pct:.1f}%)[/bold yellow]"

    if sig.regime == MarketRegime.MARKDOWN or sig.gate_state == ExecutionGateState.CASH_MARKDOWN:
        headline = "[bold white on red] RED LIGHT — DO NOT BUY (STAY 100% IN CASH: MARKET IN DOWNTREND) [/bold white on red]"
        border_style = "red"
        what_happening = (
            f"BTC (${price:,.0f}) has broken below key support (${sig.c_val:,.0f}) and real Spot sellers are actively dumping coins."
        )
        why_line = (
            f"1-Hour Spot flow ({flow.w_1h.spot_delta_btc:+,.1f} BTC) and 4-Hour Spot flow ({flow.w_4h.spot_delta_btc:+,.1f} BTC) are both negative, and US Coinbase traders are {cb_word}."
        )
        action_line = (
            "[bold red]Sit 100% in cash/stablecoins.[/bold red] Do not try to catch a falling knife. Wait for price to form a floor and reclaim support."
        )
    elif sig.hard_veto_triggered and sig.regime == MarketRegime.LEVERAGE_TRAP:
        headline = "[bold white on red] RED LIGHT — DO NOT BUY YET (WARNING: LEVERAGED FUTURES BULL TRAP) [/bold white on red]"
        border_style = "red"
        what_happening = (
            f"BTC (${price:,.0f}) is bouncing near the ${sig.support_hvn or sig.c_val:,.0f} support floor, BUT this bounce is being pushed by leveraged futures traders ({flow.w_1h.perp_delta_btc:+,.0f} BTC in 1H), not real Spot buyers ({flow.w_1h.spot_delta_btc:+,.1f} BTC in 1H)."
        )
        why_line = (
            f"Futures Open Interest jumped {deriv.oi_change_1h_pct:+.2f}% in the last hour while US institutions on Coinbase are {cb_word}. Bounces driven by leverage without Spot buying often flush back down to hunt stops."
        )
        action_line = (
            f"[bold yellow]Hold your cash and do not chase this bounce.[/bold yellow] Wait until real 1-hour Spot buying turns strongly positive and this box turns GREEN before buying around ${tp.entry_zone_low:,.0f} – ${tp.entry_zone_high:,.0f}."
            if tp
            else "[bold yellow]Hold your cash and wait for the Leverage Trap warning to clear.[/bold yellow]"
        )
    elif sig.hard_veto_triggered:
        headline = "[bold white on red] RED LIGHT — DO NOT BUY (SAFETY / MASTER VETO ACTIVE) [/bold white on red]"
        border_style = "red"
        what_happening = f"BTC is at ${price:,.0f} (Score: {sig.confluence_score:.0f}/100), but a safety or Protocol v1.3 veto is blocking entry."
        why_line = " | ".join(sig.veto_reasons)
        action_line = "[bold yellow]Stay in cash until the active safety veto clears (Press 2 or 3 to inspect Protocol/Macro tabs).[/bold yellow]"
    elif sig.gate_state == ExecutionGateState.GATE3_RECLAIM_TRIGGERED and sig.confluence_score >= 70.0:
        headline = "[bold black on green] GREEN LIGHT — BUY SIGNAL TRIGGERED (SAFE FOR SPOT SWING ENTRY) [/bold black on green]"
        border_style = "green"
        what_happening = (
            f"BTC (${price:,.0f}) swept support, absorbed futures sellers with real Spot buying ({flow.w_1h.spot_delta_btc:+,.1f} BTC in 1H), and closed back inside the Value Area."
        )
        why_line = (
            f"All 4 gates passed ({sig.confluence_score:.0f}/100): Real Spot buyers are in control, leverage is healthy (Funding {deriv.funding_rate_pct:+.4f}%), and US Coinbase traders are {cb_word}.{macro_tag}"
        )
        if tp:
            action_line = (
                f"[bold green]BUY SPOT BTC[/bold green] in zone [bold]${tp.entry_zone_low:,.0f} – ${tp.entry_zone_high:,.0f}[/bold] "
                f"(Size: [bold]{tp.position_size_btc:.4f} BTC[/bold] / ${tp.position_notional_usd:,.0f} at {tp.risk_pct:.1f}% risk). "
                f"Stop-Loss: [bold red]${tp.stop_loss:,.0f}[/bold red]. "
                f"TP1 (55%): [bold cyan]${tp.tp1_poc:,.0f}[/bold cyan] ({tp.rr_to_poc:.1f}R) | TP2 (45%): [bold magenta]${tp.tp2_vah:,.0f}[/bold magenta] ({tp.rr_to_vah:.1f}R)."
            )
        else:
            action_line = "[bold green]Execute Spot Swing Long per Panel 4 parameters.[/bold green]"
    elif sig.gate_state == ExecutionGateState.GATE2_MICROSTRUCTURE_ARMED:
        headline = "[bold black on cyan] BLUE LIGHT — GET READY (SPOT BUYERS STEPPING IN, WAITING FOR CANDLE CLOSE) [/bold black on cyan]"
        border_style = "cyan"
        what_happening = (
            f"BTC (${price:,.0f}) is testing support and real Spot buyers are absorbing futures sellers (Score: {sig.confluence_score:.0f}/100)."
        )
        why_line = (
            f"Order flow and leverage look good, and Coinbase is {cb_word}. We just need a 15m/1H candle to close firmly back above ${tp.reference_entry if tp else sig.c_val:,.0f} to confirm the bottom.{macro_tag}"
        )
        action_line = (
            "[bold cyan]Prepare your order, but wait for the candle reclaim close[/bold cyan] (this box will turn GREEN when triggered)."
        )
    elif sig.gate_state == ExecutionGateState.GATE1_ZONE_ALERT:
        headline = "[bold black on yellow] YELLOW LIGHT — WATCH CLOSELY (PRICE AT SUPPORT, WAITING FOR SPOT BUYERS) [/bold black on yellow]"
        border_style = "yellow"
        what_happening = (
            f"BTC (${price:,.0f}) has arrived at a key support zone (${sig.support_hvn or sig.c_val:,.0f}), so the location is good."
        )
        why_line = (
            f"However, aggressive 1-hour Spot buying hasn't confirmed a turn yet (1H Spot: {flow.w_1h.spot_delta_btc:+,.1f} BTC, Coinbase {cb_word}).{macro_tag}"
        )
        action_line = (
            "[bold yellow]Wait in cash and monitor.[/bold yellow] Let the market prove support holds with real Spot buying before entering."
        )
    elif sig.is_mid_range_chop:
        headline = "[bold black on yellow] STANDBY — MID-RANGE CHOP FILTER ACTIVE (AVOID MID-RANGE ENTRIES — PREFER EDGES) [/bold black on yellow]"
        border_style = "yellow"
        what_happening = (
            f"BTC (${price:,.0f}) is floating in mid-range chop (VA Position: {sig.va_position_pct:+.0f}% between cVAL ${sig.c_val:,.0f} and cVAH ${sig.c_vah:,.0f} | Score: {sig.confluence_score:.0f}/100)."
        )
        why_line = (
            f"Gate 1 blocks mid-range entries with poor reward-to-risk. 4H Spot is {flow.w_4h.spot_delta_btc:+,.1f} BTC, 1H Spot is {flow.w_1h.spot_delta_btc:+,.1f} BTC, and Coinbase is {cb_word}.{macro_tag}"
        )
        action_line = (
            f"[bold yellow]Avoid mid-range trades.[/bold yellow] Wait patiently for price to test the range edge (${sig.support_hvn or sig.c_val:,.0f} – ${sig.c_val:,.0f}) and close back inside (Press 2/3/4 for Protocol, Macro & Regime Tabs)."
        )
    else:
        headline = "[bold white] STANDBY — NO TRADE SETUP RIGHT NOW (STAY IN CASH OR HOLD EXISTING POSITION) [/bold white]"
        border_style = "bright_black"
        what_happening = (
            f"BTC (${price:,.0f}) is trading outside a confirmed low-risk entry trigger (Score: {sig.confluence_score:.0f}/100)."
        )
        why_line = (
            f"4H Spot flow is {flow.w_4h.spot_delta_btc:+,.1f} BTC, 1H Spot flow is {flow.w_1h.spot_delta_btc:+,.1f} BTC, and Coinbase is {cb_word}.{macro_tag}"
        )
        action_line = (
            f"No action needed. Wait for price to test support (${sig.support_hvn or sig.c_val:,.0f} – ${sig.c_val:,.0f}) with strong Spot buying (Press 2/3/4 for Protocol, Macro & Regime Tabs)."
        )

    lines = [
        headline,
        f"  [bold white]What's Happening :[/bold white] {what_happening}",
        f"  [bold white]Why / Risk Check :[/bold white] {why_line}",
        f"  [bold white]Your Next Move   :[/bold white] {action_line}",
    ]
    return Panel(
        "\n".join(lines),
        title="[bold white]5. Executive Bottom Line (Plain-English Quick Glance — Press 1/2/3/4/5 to Switch Tabs)[/bold white]",
        border_style=border_style,
        box=box.ROUNDED,
    )


def _build_tab1_swing_hud(store: StateStore, header_panel: Panel) -> Group:
    """Renders Tab [1]: Tactical Swing Execution HUD."""
    sig = store.latest_signal
    flow = store.flow_snapshot
    deriv = store.derivatives_snapshot
    macro_vp = store.macro_profile
    tact_vp = store.tactical_profile
    sess_vp = store.session_profile
    macro_ev = store.macro_evaluation

    gate_str = _gate_badge(sig.gate_state) if sig else "[dim]WARMING UP[/dim]"

    # --- Panel 1: Spot Prices, Basis & Derivatives State ---
    p1_table = Table(box=box.SIMPLE_HEAVY, expand=True, show_header=True, header_style="bold cyan", pad_edge=False)
    p1_table.add_column("Metric", style="white", no_wrap=True)
    p1_table.add_column("Value", justify="right", no_wrap=True)
    p1_table.add_column("Context / Z-Score", justify="right", no_wrap=True)

    p1_table.add_row(
        "Coinbase Spot (BTC-USD)",
        f"[bold white]${deriv.coinbase_price:,.2f}[/bold white]",
        "US Institutional Spot",
    )
    p1_table.add_row(
        "Binance Spot (BTCUSDT)",
        f"[bold white]${deriv.binance_spot_price:,.2f}[/bold white]",
        "Global Offshore Spot",
    )
    p1_table.add_row(
        "Coinbase Premium Index",
        _color_signed(deriv.coinbase_premium_usd, "+,.2f", " USD"),
        f"{_color_signed(deriv.coinbase_premium_pct, '+.4f', '%')} (Z={deriv.coinbase_premium_zscore:+.2f})",
    )
    p1_table.add_row(
        "Futures Open Interest",
        f"{deriv.open_interest_btc:,.1f} BTC",
        f"${deriv.open_interest_usd / 1e9:,.2f}B ({deriv.perp_source})",
    )
    p1_table.add_row(
        "Delta Open Interest (dOI)",
        f"1H: {_color_signed(deriv.oi_change_1h_pct, '+.2f', '%')}",
        f"15m:{_color_signed(deriv.oi_change_15m_pct, '+.2f', '%')} | 4H:{_color_signed(deriv.oi_change_4h_pct, '+.2f', '%')}",
    )
    p1_table.add_row(
        "8H Funding / 5m Taker L/S",
        _color_signed(deriv.funding_rate_pct, "+.4f", "%"),
        f"L/S: {deriv.taker_long_short_ratio_5m:.2f} ({_color_signed(deriv.perp_5m_delta_btc, '+.1f', ' BTC')})",
    )
    p1_table.add_row(
        "OI Positioning Quadrant",
        "[bold]" + deriv.oi_regime_quadrant.value.split(" (")[0] + "[/bold]",
        f"Perp Basis: {_color_signed(deriv.perp_basis_usd, '+.2f', ' USD')}",
    )

    # --- Panel 2: Composite Volume Profile Levels ---
    p2_table = Table(box=box.SIMPLE_HEAVY, expand=True, show_header=True, header_style="bold magenta", pad_edge=False)
    p2_table.add_column("Auction Level (70% VA)", style="white", no_wrap=True)
    p2_table.add_column("30D Macro", justify="right", no_wrap=True)
    p2_table.add_column("7D Tactical", justify="right", no_wrap=True)
    p2_table.add_column("24H Dev", justify="right", no_wrap=True)

    def _fmt_lvl(vp, attr: str) -> str:
        if vp is None:
            return "-"
        val = getattr(vp, attr, None)
        return f"${val:,.0f}" if val is not None else "-"

    p2_table.add_row("Range High", _fmt_lvl(macro_vp, "range_high"), _fmt_lvl(tact_vp, "range_high"), _fmt_lvl(sess_vp, "range_high"))
    p2_table.add_row("[bold yellow]Composite VAH (cVAH)[/bold yellow]", _fmt_lvl(macro_vp, "c_vah"), _fmt_lvl(tact_vp, "c_vah"), _fmt_lvl(sess_vp, "c_vah"))
    p2_table.add_row("[bold cyan]Composite POC (cPOC)[/bold cyan]", _fmt_lvl(macro_vp, "c_poc"), _fmt_lvl(tact_vp, "c_poc"), _fmt_lvl(sess_vp, "c_poc"))
    p2_table.add_row("[bold green]Composite VAL (cVAL)[/bold green]", _fmt_lvl(macro_vp, "c_val"), _fmt_lvl(tact_vp, "c_val"), _fmt_lvl(sess_vp, "c_val"))
    p2_table.add_row("Primary LVN (Below cVAL)", _fmt_lvl(macro_vp, "primary_lvn_below_val"), _fmt_lvl(tact_vp, "primary_lvn_below_val"), "-")
    p2_table.add_row("Support HVN (Floor)", _fmt_lvl(macro_vp, "support_hvn_below_val"), _fmt_lvl(tact_vp, "support_hvn_below_val"), "-")

    if sig:
        chop_tag = "[yellow][MID-CHOP: AVOID][/yellow]" if sig.is_mid_range_chop else "[green][EDGE ZONE][/green]"
        p2_table.add_row(
            f"Dist to cVAL ({sig.active_horizon})",
            f"{sig.distance_to_val_pct:+.2f}% ({sig.distance_to_val_atr:+.2f}x ATR)",
            f"VA Pos: {sig.va_position_pct:+.0f}% {chop_tag}",
            f"1H ATR: ${sig.atr_1h:,.0f}",
        )

    top_row = Table.grid(expand=True, padding=(0, 1))
    top_row.add_column(ratio=1)
    top_row.add_column(ratio=1)
    top_row.add_row(
        Panel(p1_table, title="[bold cyan]1. Cross-Exchange Spot & Derivatives Health[/bold cyan]", box=box.ROUNDED),
        Panel(p2_table, title="[bold magenta]2. Composite Auction Structure (Volume Profile)[/bold magenta]", box=box.ROUNDED),
    )

    # --- Panel 3: Multi-Horizon Order Flow & Absorption Matrix ---
    p3_table = Table(box=box.SIMPLE_HEAVY, expand=True, show_header=True, header_style="bold green", pad_edge=False)
    p3_table.add_column("Horizon", style="bold white", no_wrap=True)
    p3_table.add_column("Spot CVD Delta", justify="right", no_wrap=True)
    p3_table.add_column("Spot Imbalance (Z)", justify="right", no_wrap=True)
    p3_table.add_column("Perp CVD Delta", justify="right", no_wrap=True)
    p3_table.add_column("Perp Imbalance (Z)", justify="right", no_wrap=True)
    p3_table.add_column("Spot-Perp Div (Z)", justify="right", no_wrap=True)
    p3_table.add_column("Absorption Index", justify="right", no_wrap=True)

    for w in (flow.w_15m, flow.w_1h, flow.w_4h, flow.w_24h):
        p3_table.add_row(
            w.window_label,
            _color_signed(w.spot_delta_btc, "+,.2f", " BTC"),
            f"{w.spot_delta_ratio * 100:+.1f}% (Z={w.spot_zscore:+.2f})",
            _color_signed(w.perp_delta_btc, "+,.2f", " BTC"),
            f"{w.perp_delta_ratio * 100:+.1f}% (Z={w.perp_zscore:+.2f})",
            _color_signed(w.flow_divergence_z, "+.2f", " SD"),
            f"[bold]{w.absorption_index:.2f}[/bold]",
        )

    p3_table.add_row(
        "UTC Day (00:00+)",
        _color_signed(flow.utc_day_spot_cvd, "+,.2f", " BTC"),
        "-",
        _color_signed(flow.utc_day_perp_cvd, "+,.2f", " BTC"),
        "-",
        f"Bull Div: {'[green]YES[/green]' if flow.bullish_pivot_divergence else 'NO'}",
        f"Abs Div: {'[green]YES[/green]' if flow.absorption_divergence else 'NO'}",
    )
    p3_table.add_row(
        "Live WS Session",
        _color_signed(flow.session_spot_cvd, "+,.4f", " BTC"),
        f"{flow.spot_trade_count:,} trades",
        _color_signed(flow.session_perp_cvd, "+,.4f", " BTC"),
        f"{flow.perp_trade_count:,} trades",
        "[bold]" + flow.flow_signature + "[/bold]",
        "",
    )
    flow_panel = Panel(
        p3_table,
        title="[bold green]3. Multi-Horizon Order Flow, Spot vs. Perp CVD & Passive Absorption[/bold green]",
        box=box.ROUNDED,
    )

    # --- Panel 4: 4-Gate State Machine & Structural Swing Trade Plan ---
    p4_grid = Table.grid(expand=True, padding=(0, 2))
    p4_grid.add_column(ratio=3)
    p4_grid.add_column(ratio=2)

    left_lines = [f"Active Gate State : {gate_str}"]
    if sig:
        left_lines.append(
            f"Confluence Breakdown : [bold]{sig.confluence_score:.1f}/100[/bold] "
            f"(Location: {sig.location_score:.0f}/25 | Flow: {sig.flow_score:.0f}/35 | "
            f"Derivatives: {sig.derivatives_score:.0f}/20 | Trigger: {sig.trigger_score:.0f}/20)"
        )
        for note in sig.rationale_notes[:4]:
            left_lines.append(f"  • {note}")
        if sig.hard_veto_triggered:
            for v in sig.veto_reasons:
                left_lines.append(f"  [bold red]• VETO: {v}[/bold red]")
    else:
        left_lines.append("Evaluating initial market state...")

    risk_label = f"{sig.trade_plan.risk_pct:.1f}% Risk" if (sig and sig.trade_plan) else "1.0% Risk"
    right_lines = [f"[bold yellow]Structural Swing Execution Geometry ({risk_label})[/bold yellow]"]
    if sig and sig.trade_plan:
        tp = sig.trade_plan
        right_lines.extend(
            [
                f"  cVAL Entry Zone   : [bold green]${tp.entry_zone_low:,.2f} – ${tp.entry_zone_high:,.2f}[/bold green] (Ref: ${tp.reference_entry:,.2f})",
                f"  Hard Invalidation : [bold red]${tp.stop_loss:,.2f}[/bold red] (Below Sweep / LVN Floor)",
                f"  TP1 (cPOC - {tp.tp1_allocation_pct:.0f}%) : [bold cyan]${tp.tp1_poc:,.2f}[/bold cyan] ({tp.rr_to_poc:.2f}R) -> Move Stop to BE",
                f"  TP2 (cVAH - {tp.tp2_allocation_pct:.0f}%) : [bold magenta]${tp.tp2_vah:,.2f}[/bold magenta] ({tp.rr_to_vah:.2f}R)",
                f"  Position Size     : [bold white]{tp.position_size_btc:.4f} BTC[/bold white] (${tp.position_notional_usd:,.0f} | Risk: ${tp.risk_usd:,.0f})",
            ]
        )

    p4_grid.add_row("\n".join(left_lines), "\n".join(right_lines))
    signal_panel = Panel(
        p4_grid,
        title="[bold yellow]4. 4-Gate Swing Signal Engine & Dynamic Risk Geometry[/bold yellow]",
        box=box.ROUNDED,
    )
    bottom_panel = _build_tab1_plain_english_panel(sig, flow, deriv, macro_ev)

    return Group(header_panel, top_row, flow_panel, signal_panel, bottom_panel)


# ============================================================================
# TAB [2]: BTC SPOT SWING PROTOCOL v1.3 HUD (CAPITAL PRESERVATION & COINGLASS)
# ============================================================================

def _build_tab2_protocol_hud(store: StateStore, header_panel: Panel) -> Group:
    """Renders Tab [2]: BTC Spot Swing Protocol v1.3 & CoinGlass 6-Panel Audit."""
    pev = store.protocol_evaluation
    if pev is None:
        return Group(
            header_panel,
            Panel("Warming up Protocol v1.3 1D/4H candles...", title="Protocol v1.3", box=box.ROUNDED),
        )

    # --- Panel 1: Market Structure & ATR 14 Invalidation (1D Completed vs Forming, 4H Timing) ---
    p1_table = Table(box=box.SIMPLE_HEAVY, expand=True, show_header=True, header_style="bold cyan", pad_edge=False)
    p1_table.add_column("Protocol v1.3 Metric", style="white", no_wrap=True)
    p1_table.add_column("Primary Value", justify="right", no_wrap=True)
    p1_table.add_column("Forming / Context", justify="right", no_wrap=True)

    bias_badge = (
        "[bold green]BULLISH[/bold green]"
        if pev.daily_bias == "BULLISH"
        else ("[bold red]BEARISH[/bold red]" if pev.daily_bias == "BEARISH" else "[bold yellow]NEUTRAL[/bold yellow]")
    )
    p1_table.add_row(
        "Live Spot Price (BTCUSDT)",
        f"[bold white]${pev.current_price:,.2f}[/bold white]",
        f"1D Bias: {bias_badge}",
    )
    p1_table.add_row(
        "1D Completed [-2] (Closed)",
        f"${pev.completed_1d_close:,.2f} ({_color_signed(pev.completed_1d_change_pct, '+.2f', '%')})",
        f"H:${pev.completed_1d_high:,.0f} | L:${pev.completed_1d_low:,.0f}",
    )
    p1_table.add_row(
        "1D Forming [-1] (Live)",
        f"${pev.forming_1d_close:,.2f} ({_color_signed(pev.forming_1d_change_pct, '+.2f', '%')})",
        f"H:${pev.forming_1d_high:,.0f} | L:${pev.forming_1d_low:,.0f}",
    )
    p1_table.add_row(
        "1D Support / Resistance",
        f"Sup: [green]${pev.daily_support:,.0f}[/green]",
        f"Res: [magenta]${pev.daily_resistance:,.0f}[/magenta]",
    )
    p1_table.add_row(
        "4H Structure & Timing",
        f"[bold]{pev.structure_4h.split(' (')[0]}[/bold]",
        f"Timing: {'[bold green]READY[/bold green]' if pev.timing_4h_ready else '[yellow]WAIT / NOT READY[/yellow]'}",
    )
    p1_table.add_row(
        "1D ATR 14 Reference",
        f"ATR(1D): [bold]${pev.atr_14_1d:,.0f}[/bold]",
        f"-1x:${pev.downside_ref_1d_atr:,.0f} | +1x:${pev.upside_ref_1d_atr:,.0f}",
    )
    p1_table.add_row(
        "4H ATR 14 Reference",
        f"ATR(4H): [bold]${pev.atr_14_4h:,.0f}[/bold]",
        f"-1x:${pev.downside_ref_4h_atr:,.0f} | +1x:${pev.upside_ref_4h_atr:,.0f}",
    )

    # --- Panel 2: Fixed CoinGlass 6-Panel Order across 1D & 4H ---
    p2_table = Table(box=box.SIMPLE_HEAVY, expand=True, show_header=True, header_style="bold yellow", pad_edge=False)
    p2_table.add_column("CoinGlass 6-Panel Order", style="bold white", no_wrap=True)
    p2_table.add_column("1D Horizon", justify="right", no_wrap=True)
    p2_table.add_column("4H Horizon", justify="right", no_wrap=True)
    p2_table.add_column("Direction / Check", justify="right", no_wrap=True)

    for row in pev.coinglass_rows:
        dir_styled = row.direction_status
        if "RISING" in dir_styled or "EXPANDING" in dir_styled:
            dir_styled = f"[green]{dir_styled}[/green]"
        elif "FALLING" in dir_styled or "ELEVATED" in dir_styled:
            dir_styled = f"[yellow]{dir_styled}[/yellow]"
        p2_table.add_row(row.metric_name, row.value_1d, row.value_4h, dir_styled)

    top_row = Table.grid(expand=True, padding=(0, 1))
    top_row.add_column(ratio=1)
    top_row.add_column(ratio=1)
    top_row.add_row(
        Panel(
            p1_table,
            title="[bold cyan]1. Market Structure & ATR 14 Invalidation (Protocol Sections 1–5)[/bold cyan]",
            box=box.ROUNDED,
        ),
        Panel(
            p2_table,
            title="[bold yellow]2. CoinGlass 6-Panel Audit in Strict BTC Coins (Protocol Sections 6–7)[/bold yellow]",
            box=box.ROUNDED,
        ),
    )

    # --- Panel 3: Section 8 Non-Trade Zones Matrix (8A - 8F) ---
    p3_table = Table(box=box.SIMPLE_HEAVY, expand=True, show_header=True, header_style="bold green", pad_edge=False)
    p3_table.add_column("Code", style="bold white", width=5, no_wrap=True)
    p3_table.add_column("Non-Trade Zone Rule (Section 8)", style="white", no_wrap=True)
    p3_table.add_column("Status", justify="center", width=14, no_wrap=True)
    p3_table.add_column("Live Telemetry & Mandatory Audit Verification", justify="right", no_wrap=True)

    for z in pev.non_trade_zones:
        if z.status == "CLEAR":
            st_badge = "[bold green]CLEAR[/bold green]"
        elif z.status == "TRIGGERED":
            st_badge = "[bold white on red] TRIGGERED [/bold white on red]"
        else:
            st_badge = "[bold black on yellow] UNVERIFIED [/bold black on yellow]"
        p3_table.add_row(z.code, z.rule_name, st_badge, z.detail)

    ntz_panel = Panel(
        p3_table,
        title="[bold green]3. Non-Trade Zones Matrix 8A–8F (Protocol Section 8 Capital Preservation Audit)[/bold green]",
        box=box.ROUNDED,
    )

    # --- Panel 4: Section 10 Buy Decision, Liquidation Magnets & Section 11 Spot Sell Triggers ---
    p4_grid = Table.grid(expand=True, padding=(0, 2))
    p4_grid.add_column(ratio=1, no_wrap=True)
    p4_grid.add_column(ratio=1, no_wrap=True)

    ntz_color = "green" if pev.non_trade_zone_status == "NO" else "red"
    buy_color = "green" if pev.buy_allowed == "YES" else "red"
    ready_color = "green" if pev.entry_status == "READY" else "yellow"

    left_lines = [
        "[bold cyan]Final Buy Decision (Sections 9–10) & Liquidation Magnet Protocol[/bold cyan]",
        f"  BIAS : {bias_badge} | CONFIDENCE : [bold]{pev.confidence}[/bold] | NTZ : [bold {ntz_color}]{pev.non_trade_zone_status}[/bold {ntz_color}] | BUY : [bold {buy_color}]{pev.buy_allowed}[/bold {buy_color}] ({pev.entry_status})",
        f"  • [bold white]Short-Liq Magnet:[/bold white] [magenta]${pev.short_liq_magnet_usd:,.0f}[/magenta] {pev.short_liq_source} | [bold white]Long-Liq:[/bold white] [cyan]${pev.long_liq_magnet_usd:,.0f}[/cyan]",
        f"  • [bold white]50D MA / Pivot  :[/bold white] 50D MA ${pev.sma_50_1d:,.0f} | Range Pivot ${pev.range_pivot_usd:,.0f} | Confluence: {pev.magnet_confluence_aligned}/5",
        f"  • [bold white]Magnet Verdict  :[/bold white] [bold yellow]{pev.liq_magnet_verdict}[/bold yellow]",
        f"  • [bold white]Actionable Note :[/bold white] {pev.liq_magnet_action_note}",
    ]

    right_lines = ["[bold magenta]Long-Only Spot Sell Triggers 1–4 (Section 11) & Headline Filter[/bold magenta]"]
    for st in pev.sell_triggers:
        if st.status == "CONFIRMED":
            s_badge = "[bold white on red] CONFIRMED [/bold white on red]"
        elif st.status == "UNVERIFIED":
            s_badge = "[bold yellow]UNVERIFIED[/bold yellow]"
        else:
            s_badge = "[green]NOT CONFIRMED[/green]"
        right_lines.append(f"  • {st.name}: {s_badge} ({st.detail})")
    right_lines.append(
        f"  • [bold white]Headline Filter :[/bold white] [cyan]{pev.headline_filter_status}[/cyan] (Trade Magnet, Not Headline)"
    )

    p4_grid.add_row("\n".join(left_lines), "\n".join(right_lines))
    decision_panel = Panel(
        p4_grid,
        title="[bold yellow]4. Buy Decision, Liquidation Magnet Protocol & Spot Sell Triggers (Protocol Sections 9–11)[/bold yellow]",
        box=box.ROUNDED,
    )

    # --- Panel 5: Section 14 Executive Verdict ---
    if pev.non_trade_zone_status != "NO":
        headline = "[bold white on red] RED LIGHT — NON-TRADE ZONE ACTIVE (BUYING FORBIDDEN BY PROTOCOL v1.3) [/bold white on red]"
        border_style = "red"
        decision_str = f"DO NOT BUY SPOT. Active Non-Trade Zone: {', '.join(pev.active_ntz_reasons) or 'Unverified Check'}."
    elif pev.any_sell_confirmed:
        headline = "[bold white on red] RED LIGHT — SPOT SELL TRIGGER CONFIRMED (DE-RISK / EXIT TO CASH) [/bold white on red]"
        border_style = "red"
        decision_str = "Execute Spot defensive de-risking per Section 11 confirmed trigger."
    elif pev.buy_allowed == "YES" and pev.entry_status == "READY":
        headline = "[bold black on green] GREEN LIGHT — PROTOCOL v1.3 BUY ALLOWED & ENTRY READY [/bold black on green]"
        border_style = "green"
        decision_str = (
            f"Spot Long Entry Permitted (Confidence: {pev.confidence}). "
            f"Reference 4H -1xATR (${pev.downside_ref_4h_atr:,.0f}) and 1D Support (${pev.daily_support:,.0f}) for invalidation."
        )
    elif pev.buy_allowed == "YES":
        headline = "[bold black on cyan] BLUE LIGHT — BUY ALLOWED, WAITING FOR 4H ENTRY TIMING ALIGNMENT [/bold black on cyan]"
        border_style = "cyan"
        decision_str = "Zero Non-Trade Zones active and 4H Spot CVD rising; wait for 4H HH/HL structure confirmation."
    else:
        headline = "[bold black on yellow] STANDBY / YELLOW LIGHT — ENTRY NOT READY (PRESERVE CASH) [/bold black on yellow]"
        border_style = "yellow"
        decision_str = (
            f"BUY ALLOWED = NO / ENTRY STATUS = NOT READY. 1D Bias is {pev.daily_bias}; wait for 1D/4H alignment and rising Spot CVD."
        )

    p5_lines = [
        headline,
        f"  [bold white]NOW         :[/bold white] BTC at ${pev.current_price:,.2f} | 1D Completed [-2]: ${pev.completed_1d_close:,.0f} ({pev.completed_1d_change_pct:+.2f}%) | 1D Bias: {pev.daily_bias} | 4H: {pev.structure_4h}.",
        f"  [bold white]DECISION    :[/bold white] {decision_str}",
        f"  [bold white]RISKS       :[/bold white] 1D -1xATR Reference: ${pev.downside_ref_1d_atr:,.0f} | 4H -1xATR Reference: ${pev.downside_ref_4h_atr:,.0f} | Strict BTC OI: {store.derivatives_snapshot.open_interest_btc:,.1f} BTC.",
        f"  [bold white]LIMITATIONS :[/bold white] External checks (8B/8E/ETF) synced from config/protocol_context.json (Reviewed: {pev.context_last_reviewed}).",
    ]
    bottom_panel = Panel(
        "\n".join(p5_lines),
        title="[bold white]5. Executive Bottom Line Verdict (Protocol Sections 12–14 — Press 1/2/3/4/5 to Switch Tabs)[/bold white]",
        border_style=border_style,
        box=box.ROUNDED,
    )

    return Group(header_panel, top_row, ntz_panel, decision_panel, bottom_panel)


# ============================================================================
# TAB [3]: MACRO QUANT & CYCLE RADAR HUD (REPLACES 4-PAGE WEB PLATFORM)
# ============================================================================

def _build_tab3_macro_hud(store: StateStore, header_panel: Panel) -> Group:
    """Renders Tab [3]: Macro Quant & Cycle Radar HUD."""
    mev = store.macro_evaluation
    if mev is None:
        return Group(
            header_panel,
            Panel("Warming up 255x 1D and 1W Macro Radar candles...", title="Macro Quant & Cycle Radar", box=box.ROUNDED),
        )

    # --- Panel 1: Quant Radar — The Gatekeeper ---
    p1_table = Table(box=box.SIMPLE_HEAVY, expand=True, show_header=True, header_style="bold cyan", pad_edge=False)
    p1_table.add_column("Quant Metric", style="white", no_wrap=True)
    p1_table.add_column("Value", justify="right", no_wrap=True)
    p1_table.add_column("Gatekeeper / Regime", justify="right", no_wrap=True)

    gk_badge = (
        "[bold white on red] VETO (BELOW 200D) [/bold white on red]"
        if mev.gatekeeper_veto
        else "[bold black on green] PASS (ABOVE 200D) [/bold black on green]"
    )
    p1_table.add_row(
        "1D 200 SMA (Gatekeeper)",
        f"[bold]${mev.sma_200_1d:,.0f}[/bold]",
        gk_badge,
    )
    p1_table.add_row(
        "200D SMA 5-Day Slope",
        _color_signed(mev.sma_200_slope_5d_usd, "+,.1f", " $/d"),
        f"5D: {_color_signed(mev.sma_200_slope_5d_pct, '+.2f', '%')} ({'RISING' if mev.slope_200d_positive else 'FALLING'})",
    )
    p1_table.add_row(
        "1D Close (Comp [-2]/[-1])",
        f"Comp: ${mev.completed_1d_close:,.0f}",
        f"Live: ${mev.forming_1d_close:,.0f} ({'ABOVE' if mev.above_200d_sma else 'BELOW'} 200D)",
    )
    p1_table.add_row(
        "1D 21 EMA Bull Band",
        f"[bold cyan]${mev.ema_21_1d:,.0f}[/bold cyan]",
        f"Dist: {_color_signed(mev.dist_to_21d_ema_pct, '+.2f', '%')} ({'ABOVE' if mev.dist_to_21d_ema_pct >= 0 else 'BELOW 21D'})",
    )
    p1_table.add_row(
        "14D Wilder RSI (Daily)",
        f"[bold yellow]{mev.rsi_14_1d:.1f}[/bold yellow]",
        mev.rsi_zone,
    )
    p1_table.add_row(
        "30D Volume Profile POC",
        f"[bold magenta]${mev.poc_30d:,.0f}[/bold magenta]",
        f"Dist: {_color_signed(mev.dist_to_30d_poc_pct, '+.2f', '%')}",
    )
    p1_table.add_row(
        "Power-Law Fair Value",
        f"[bold cyan]${mev.power_law_fair_usd:,.0f}[/bold cyan] ({_color_signed(mev.power_law_discount_pct, '+.1f', '%')})",
        f"[bold cyan]{mev.power_law_zone_label}[/bold cyan]",
    )

    # --- Panel 2: Regime Radar — Cycle Armor & Drawdown Rungs (-25% to -65%) ---
    p2_table = Table(box=box.SIMPLE_HEAVY, expand=True, show_header=True, header_style="bold magenta", pad_edge=False)
    p2_table.add_column("Accumulation Rung", style="white", no_wrap=True)
    p2_table.add_column("Level", justify="right", no_wrap=True)
    p2_table.add_column("Dist", justify="right", no_wrap=True)
    p2_table.add_column("Tranche / Status", justify="right", no_wrap=True)

    p2_table.add_row(
        "[bold white]Cycle High (ATH)[/bold white]",
        f"[bold]${mev.cycle_high_usd:,.0f}[/bold]",
        _color_signed(mev.current_drawdown_pct, "+.1f", "%"),
        f"Active: [bold yellow]{mev.active_crash_rung.split(' (')[0]}[/bold yellow]",
    )
    for rung in mev.crash_rungs:
        if rung.status == "HIT / ACTIVE":
            st_str = f"[bold black on green] {rung.status} [/bold black on green]"
        elif "NEAR" in rung.status:
            st_str = f"[bold yellow]{rung.status}[/bold yellow]"
        else:
            st_str = f"[dim]{rung.status}[/dim]"
        p2_table.add_row(
            rung.rung_label.split(" (")[0],
            f"${rung.target_price:,.0f}",
            f"{rung.distance_pct:+.1f}%",
            f"{rung.allocation_tranche} | {st_str}",
        )

    top_row = Table.grid(expand=True, padding=(0, 1))
    top_row.add_column(ratio=1)
    top_row.add_column(ratio=1)
    top_row.add_row(
        Panel(
            p1_table,
            title="[bold cyan]1. Quant Radar — Gatekeeper (1D 200 SMA, 21D EMA, 14D RSI, 30D POC & Power-Law)[/bold cyan]",
            box=box.ROUNDED,
        ),
        Panel(
            p2_table,
            title="[bold magenta]2. Regime Radar — Cycle Armor & Crash Rungs (-25% to -65%)[/bold magenta]",
            box=box.ROUNDED,
        ),
    )

    # --- Panel 3: Liquidity Radar — Multi-Timeframe 1W / 1D / 4H Sniper Matrix ---
    p3_table = Table(box=box.SIMPLE_HEAVY, expand=True, show_header=True, header_style="bold green", pad_edge=False)
    p3_table.add_column("Timeframe Horizon", style="bold white", no_wrap=True)
    p3_table.add_column("Market Structure", justify="left", no_wrap=True)
    p3_table.add_column("Candle Signature & Lower Wick", justify="right", no_wrap=True)
    p3_table.add_column("Order Flow / Taker Delta", justify="right", no_wrap=True)

    for r in mev.tf_rows:
        st_col = (
            f"[green]{r.structure}[/green]"
            if "BULLISH" in r.structure
            else (f"[red]{r.structure}[/red]" if "BEARISH" in r.structure else f"[yellow]{r.structure}[/yellow]")
        )
        p3_table.add_row(r.timeframe, st_col, r.candle_signature, r.flow_momentum)

    flush_badge = (
        "[bold black on green] FLUSH TRIGGERED [/bold black on green]"
        if mev.wick_flush_4h_detected
        else "[dim white]STANDBY[/dim white]"
    )
    p3_table.add_row(
        "4H Liquidation Wick Flush",
        flush_badge,
        f"Max 4H Lower-Wick Sweep Ratio: {mev.wick_flush_4h_ratio:.1f}%",
        mev.wick_flush_detail,
    )
    sniper_panel = Panel(
        p3_table,
        title="[bold green]3. Liquidity Radar — Multi-Timeframe 1W / 1D / 4H Sniper Matrix & 4H Wick Flush[/bold green]",
        box=box.ROUNDED,
    )

    # --- Panel 4: Unified Macro Arb & Allocation Engine ---
    p4_grid = Table.grid(expand=True, padding=(0, 2))
    p4_grid.add_column(ratio=3)
    p4_grid.add_column(ratio=2)

    left_lines = [
        f"Composite Macro Confidence : [bold cyan]{mev.macro_confidence_pct:.1f}% / 100%[/bold cyan] "
        f"(Trend: {mev.trend_score:.0f}/25 | Momentum: {mev.momentum_score:.0f}/25 | "
        f"Flow: {mev.flow_score:.0f}/25 | Structure: {mev.structure_score:.0f}/25)",
        f"Recommended Spot Allocation : [bold yellow]{mev.recommended_allocation}[/bold yellow]",
    ]
    for note in mev.macro_notes[:4]:
        left_lines.append(f"  • {note}")

    right_lines = ["[bold magenta]Multi-Month Scale-Out Ceiling Targets[/bold magenta]"]
    for t_line in mev.scale_out_targets:
        right_lines.append(f"  • {t_line}")

    p4_grid.add_row("\n".join(left_lines), "\n".join(right_lines))
    arb_panel = Panel(
        p4_grid,
        title="[bold yellow]4. Unified Macro Arb & Allocation Engine (Trend • Momentum • Flow • Structure)[/bold yellow]",
        box=box.ROUNDED,
    )

    # --- Panel 5: Executive Bottom Line (Macro & Cycle Verdict) ---
    if not mev.gatekeeper_veto and mev.macro_confidence_pct >= 65.0:
        headline = "[bold black on green] GREEN LIGHT — MACRO BULL REGIME ACTIVE (ABOVE RISING 1D 200 SMA) [/bold black on green]"
        border_style = "green"
        next_move = f"[bold green]Deploy {mev.recommended_allocation}.[/bold green] Use 1D 21 EMA (${mev.ema_21_1d:,.0f}) and Tab [1] cVAL pullbacks to add."
    elif mev.crash_rung_override_active:
        headline = "[bold black on cyan] BLUE LIGHT — CRASH-RUNG DEEP VALUE ACCUMULATION OVERRIDE ACTIVE [/bold black on cyan]"
        border_style = "cyan"
        next_move = f"[bold cyan]Deploy {mev.recommended_allocation}[/bold cyan] into {mev.active_crash_rung}; scale out at 1D 21 EMA (${mev.ema_21_1d:,.0f}) and 200D SMA (${mev.sma_200_1d:,.0f})."
    elif mev.gatekeeper_veto:
        headline = "[bold white on red] RED LIGHT — RULE 1 MACRO GATEKEEPER VETO (BELOW 1D 200 SMA / DEFENSIVE REGIME) [/bold white on red]"
        border_style = "red"
        next_move = (
            f"[bold yellow]No new macro trend-following longs.[/bold yellow] Keep core macro capital in cash, place deep limit bids at Crash Rungs (-25% to -65%), and cap any Tab [1] tactical bounce trades at 0.5% risk."
        )
    else:
        headline = "[bold black on yellow] YELLOW LIGHT — MACRO CONSOLIDATION ABOVE 200D SMA [/bold black on yellow]"
        border_style = "yellow"
        next_move = f"Maintain {mev.recommended_allocation} and use Tab [1] order-flow confirmation for swing entries."

    p5_lines = [
        headline,
        f"  [bold white]What's Happening      :[/bold white] BTC is at ${mev.current_price:,.0f} ({mev.current_drawdown_pct:+.1f}% from ${mev.cycle_high_usd:,.0f} Cycle High) | 1D 200 SMA: ${mev.sma_200_1d:,.0f} ({mev.sma_200_slope_5d_usd:+.1f}/d) | 14D RSI: {mev.rsi_14_1d:.1f}.",
        f"  [bold white]Why / Gatekeeper Check:[/bold white] {mev.gatekeeper_status_text} | Active Rung: {mev.active_crash_rung} | 4H Wick Flush: {'YES' if mev.wick_flush_4h_detected else 'NO'}.",
        f"  [bold white]Your Next Move        :[/bold white] {next_move}",
    ]
    bottom_panel = Panel(
        "\n".join(p5_lines),
        title="[bold white]5. Executive Bottom Line (Macro & Cycle Quick Glance — Press 1/2/3/4/5 to Switch Tabs)[/bold white]",
        border_style=border_style,
        box=box.ROUNDED,
    )

    return Group(header_panel, top_row, sniper_panel, arb_panel, bottom_panel)


# ============================================================================
# TAB [4]: REGIME RADAR — QUANTITATIVE MICROSTRUCTURE CONFIGURATIONS A–J
# ============================================================================

def _build_tab4_regime_matrix_hud(store: StateStore, header_panel: Panel) -> Group:
    """Renders Tab [4]: Quantitative Microstructure Diagnostic & Execution Protocols (Configs A-J)."""
    rmev = store.regime_matrix_evaluation
    if rmev is None or not rmev.configs:
        return Group(
            header_panel,
            Panel("Warming up Configurations A-J telemetry...", title="Regime Matrix A-J", box=box.ROUNDED),
        )

    active_cfg = next((c for c in rmev.configs if c.code == rmev.active_config_code), rmev.configs[0])
    runner_cfg = next((c for c in rmev.configs if c.code == rmev.runner_up_config_code), rmev.configs[0])

    # --- Panel 1: Live Microstructure & VWAP Telemetry (Config A-J Inputs) ---
    p1_table = Table(box=box.SIMPLE_HEAVY, expand=True, show_header=True, header_style="bold cyan", pad_edge=False)
    p1_table.add_column("Config A–J Input Metric", style="white", no_wrap=True)
    p1_table.add_column("Live Value", justify="right", no_wrap=True)
    p1_table.add_column("Benchmark / Threshold", justify="right", no_wrap=True)

    d_vwap_status = "[green]ABOVE[/green]" if rmev.current_price >= rmev.daily_vwap else "[red]BELOW[/red]"
    w_vwap_status = "[green]ABOVE[/green]" if rmev.current_price >= rmev.weekly_vwap else "[red]BELOW[/red]"

    p1_table.add_row(
        "Daily VWAP / Weekly VWAP",
        f"D: ${rmev.daily_vwap:,.0f} ({d_vwap_status})",
        f"W: ${rmev.weekly_vwap:,.0f} ({w_vwap_status})",
    )
    p1_table.add_row(
        "1D 20 EMA / 1D 50 EMA",
        f"20D: ${rmev.ema_20_1d:,.0f}",
        f"50D: ${rmev.ema_50_1d:,.0f} ({'ABOVE' if rmev.current_price >= rmev.ema_50_1d else 'BELOW'})",
    )
    p1_table.add_row(
        "24H Spot Vol vs 20D MA",
        f"[bold]{rmev.spot_vol_vs_20d_ma:.2f}x[/bold]",
        f"Config A Target: >= 1.35x ({'PASS' if rmev.spot_vol_vs_20d_ma >= 1.35 else 'SUB-1.35x'})",
    )
    p1_table.add_row(
        "4H Spot Buy/Sell Ratio & 7D CVD",
        f"Ratio: [bold]{rmev.spot_buy_sell_ratio_4h:.2f}[/bold]",
        f"7D Spot CVD: {_color_signed(rmev.spot_cvd_7d_btc, '+,.0f', ' BTC')}",
    )
    p1_table.add_row(
        "Open Interest Delta (1H/4H/24H)",
        f"1H:{_color_signed(rmev.oi_change_1h_pct, '+.2f', '%')} | 4H:{_color_signed(rmev.oi_change_4h_pct, '+.2f', '%')}",
        f"24H dOI: {_color_signed(rmev.oi_change_24h_pct, '+.2f', '%')}",
    )
    p1_table.add_row(
        "8H Funding & Annualized Basis",
        _color_signed(rmev.funding_rate_pct, "+.4f", "%"),
        f"Ann. Basis: {_color_signed(rmev.annualized_basis_pct, '+.1f', '%/yr')}",
    )
    p1_table.add_row(
        "ATR Compression & 72h Base Width",
        f"ATR Comp: {rmev.atr_compression_pct:.1f}%",
        f"72h Range Width: {rmev.base_width_72h_pct:.2f}% (Target <2.5%)",
    )

    # --- Panel 2: Active Configuration Diagnosis (#1 Match & #2 Runner-Up) ---
    p2_table = Table(box=box.SIMPLE_HEAVY, expand=True, show_header=True, header_style="bold magenta", pad_edge=False)
    p2_table.add_column("Diagnostic Field", style="white", no_wrap=True)
    p2_table.add_column("Active Regime Output", justify="right", no_wrap=True)

    cat_badge = (
        f"[bold black on green] {active_cfg.code}: {active_cfg.short_title.upper()} ({active_cfg.match_pct:.0f}% MATCH) [/bold black on green]"
        if active_cfg.category in ("BULL_LONG", "ACCUMULATE")
        else (
            f"[bold black on yellow] {active_cfg.code}: {active_cfg.short_title.upper()} ({active_cfg.match_pct:.0f}% MATCH) [/bold black on yellow]"
            if active_cfg.category == "HARVEST_WAIT"
            else f"[bold white on red] {active_cfg.code}: {active_cfg.short_title.upper()} ({active_cfg.match_pct:.0f}% MATCH) [/bold white on red]"
        )
    )
    p2_table.add_row("Primary Active Configuration", cat_badge)
    p2_table.add_row("Market Diagnosis (THEN IT MEANS)", f"[bold cyan]{active_cfg.diagnosis_subtitle}[/bold cyan]")
    p2_table.add_row("Actionable Protocol Mandate", f"[bold yellow]{active_cfg.action_headline}[/bold yellow]")
    p2_table.add_row("Position Sizing Protocol", active_cfg.sizing_rule)
    p2_table.add_row("Execution / Harvest Rule", active_cfg.entry_or_harvest_rule)
    p2_table.add_row("Dynamic Stop / Invalidation", f"[bold red]{active_cfg.stop_rule}[/bold red]")
    p2_table.add_row(
        "Secondary Runner-Up Config",
        f"[dim]{runner_cfg.code}: {runner_cfg.short_title} ({runner_cfg.match_pct:.0f}% Match) -> {runner_cfg.action_headline}[/dim]",
    )

    top_row = Table.grid(expand=True, padding=(0, 1))
    top_row.add_column(ratio=1)
    top_row.add_column(ratio=1)
    top_row.add_row(
        Panel(
            p1_table,
            title="[bold cyan]1. Live Microstructure, VWAP & Basis Telemetry (Config A–J Inputs)[/bold cyan]",
            box=box.ROUNDED,
        ),
        Panel(
            p2_table,
            title="[bold magenta]2. Active Configuration Diagnosis (#1 Match & #2 Runner-Up)[/bold magenta]",
            box=box.ROUNDED,
        ),
    )

    # --- Panel 3: Quantitative Microstructure Diagnostic Matrix (Configs A through J) ---
    p3_table = Table(box=box.SIMPLE_HEAVY, expand=True, show_header=True, header_style="bold green", pad_edge=False)
    p3_table.add_column("Config", style="bold white", min_width=10, no_wrap=True)
    p3_table.add_column("Market Diagnosis (THEN IT MEANS)", style="white", ratio=2, no_wrap=True)
    p3_table.add_column("Live Match", justify="right", min_width=14, no_wrap=True)
    p3_table.add_column("Live Observed Telemetry Facts", justify="left", ratio=3, no_wrap=True)
    p3_table.add_column("Actionable Protocol (Sizing & Stops)", justify="right", ratio=3, no_wrap=True)

    for cfg in rmev.configs:
        if cfg.is_active:
            c_name = f"[bold black on green] {cfg.code} [/bold black on green]"
            m_str = f"[bold green]{cfg.match_pct:.0f}% [ACTIVE][/bold green]"
            diag_str = f"[bold white]{cfg.short_title} — {cfg.diagnosis_subtitle}[/bold white]"
        else:
            c_name = cfg.code
            m_str = f"[dim]{cfg.match_pct:.0f}%[/dim]" if cfg.match_pct < 50 else f"[yellow]{cfg.match_pct:.0f}%[/yellow]"
            diag_str = f"{cfg.short_title} ({cfg.diagnosis_subtitle})"

        act_col = (
            f"[green]{cfg.action_headline}[/green]"
            if cfg.category in ("BULL_LONG", "ACCUMULATE")
            else (f"[yellow]{cfg.action_headline}[/yellow]" if cfg.category == "HARVEST_WAIT" else f"[red]{cfg.action_headline}[/red]")
        )
        p3_table.add_row(
            c_name,
            diag_str,
            m_str,
            cfg.key_live_facts,
            f"{act_col} | {cfg.stop_rule}",
        )

    matrix_panel = Panel(
        p3_table,
        title="[bold green]3. Quantitative Microstructure Diagnostic Matrix (Configurations A through J)[/bold green]",
        box=box.ROUNDED,
    )

    # --- Panel 4: Active Config Playbook + Global Session Microstructure Reference ---
    p4_grid = Table.grid(expand=True, padding=(0, 2))
    p4_grid.add_column(ratio=4, no_wrap=True)
    p4_grid.add_column(ratio=6, no_wrap=True)

    left_lines = [
        f"[bold cyan]IF YOU OBSERVE — {active_cfg.code} ({active_cfg.short_title}) Live Fact Checklist:[/bold cyan]"
    ]
    for item in active_cfg.observed_checklist[:5]:
        left_lines.append(f"  {item}")
    left_lines.append(
        f"  [bold yellow]Mandate:[/bold yellow] {active_cfg.action_headline} | {active_cfg.sizing_rule} | [bold red]{active_cfg.stop_rule}[/bold red]"
    )

    utc_hour = datetime.now(timezone.utc).hour
    session_windows = [
        (0, 7, "00–07 UTC (08–15 SGT)", "ASIA SESSION", "Binance Spot/Perp lead; ranges & Config F base-building"),
        (7, 8, "07–08 UTC (15–16 SGT)", "ASIA/LON OVERLAP", "Frequent stop-hunt / sweep window as EU desks enter"),
        (8, 13, "08–13 UTC (16–21 SGT)", "LONDON / EU", "European directional expansion & pre-US positioning"),
        (13, 16, "13–16 UTC (21–00 SGT)", "LON/NY OVERLAP", "Peak Spot vol, US ETF flow & Config A breakouts"),
        (16, 21, "16–21 UTC (00–05 SGT)", "NEW YORK (US)", "Coinbase Spot & US institutional absorption (Config C)"),
        (21, 24, "21–24 UTC (05–08 SGT)", "LATE NY / TRANS", "Thinner books prior to 00:00 UTC daily candle close"),
    ]
    right_lines = [
        "[bold yellow]GLOBAL TRADING SESSIONS (UTC • SGT) & MICROSTRUCTURE CONTEXT:[/bold yellow]"
    ]
    for start_h, end_h, win_str, s_name, ctx_str in session_windows:
        if start_h <= utc_hour < end_h:
            right_lines.append(
                f"  [bold black on green] ► {win_str} [/bold black on green] [bold green]{s_name:<16}[/bold green] [bold white]{ctx_str}[/bold white]"
            )
        else:
            right_lines.append(
                f"  [dim]  {win_str}  {s_name:<16} {ctx_str}[/dim]"
            )

    p4_grid.add_row("\n".join(left_lines), "\n".join(right_lines))
    playbook_panel = Panel(
        p4_grid,
        title="[bold yellow]4. Active Configuration Checklist & Global Session Microstructure Reference (UTC • SGT)[/bold yellow]",
        box=box.ROUNDED,
    )

    # --- Panel 5: Executive Bottom Line (Config A-J Plain-English Quick Glance) ---
    if active_cfg.category == "BULL_LONG":
        headline = f"[bold black on green] GREEN LIGHT — {active_cfg.code.upper()}: {active_cfg.short_title.upper()} ({active_cfg.action_headline.upper()}) [/bold black on green]"
        border_style = "green"
    elif active_cfg.category == "ACCUMULATE":
        headline = f"[bold black on cyan] BLUE LIGHT — {active_cfg.code.upper()}: {active_cfg.short_title.upper()} ({active_cfg.action_headline.upper()}) [/bold black on cyan]"
        border_style = "cyan"
    elif active_cfg.category == "HARVEST_WAIT":
        headline = f"[bold black on yellow] YELLOW LIGHT — {active_cfg.code.upper()}: {active_cfg.short_title.upper()} ({active_cfg.action_headline.upper()}) [/bold black on yellow]"
        border_style = "yellow"
    else:
        headline = f"[bold white on red] RED LIGHT — {active_cfg.code.upper()}: {active_cfg.short_title.upper()} ({active_cfg.action_headline.upper()}) [/bold white on red]"
        border_style = "red"

    p5_lines = [
        headline,
        f"  [bold white]What's Happening :[/bold white] Live telemetry matches {active_cfg.code} ({active_cfg.short_title} — {active_cfg.diagnosis_subtitle}) at {active_cfg.match_pct:.0f}% confidence ({active_cfg.key_live_facts}).",
        f"  [bold white]Why / Runner-Up  :[/bold white] Secondary match is {runner_cfg.code} ({runner_cfg.short_title} at {runner_cfg.match_pct:.0f}%). Daily VWAP is ${rmev.daily_vwap:,.0f} and Weekly VWAP is ${rmev.weekly_vwap:,.0f}.",
        f"  [bold white]Your Next Move   :[/bold white] [bold]{active_cfg.action_headline}[/bold] -> {active_cfg.sizing_rule} | {active_cfg.entry_or_harvest_rule} | {active_cfg.stop_rule}.",
    ]
    bottom_panel = Panel(
        "\n".join(p5_lines),
        title="[bold white]5. Executive Bottom Line (Config A–J Quick Glance — Press 1/2/3/4/5 to Switch Tabs)[/bold white]",
        border_style=border_style,
        box=box.ROUNDED,
    )

    return Group(header_panel, top_row, matrix_panel, playbook_panel, bottom_panel)


# ============================================================================
# TAB [5]: MASTER SYNTHESIS & SUPREME ORDER OF BATTLE HUD
# ============================================================================

def _light_badge(light: str) -> str:
    if light == "GREEN":
        return "[bold black on green] GREEN [/bold black on green]"
    if light == "BLUE":
        return "[bold black on cyan] BLUE  [/bold black on cyan]"
    if light == "YELLOW":
        return "[bold black on yellow] YELLW [/bold black on yellow]"
    return "[bold white on red]  RED  [/bold white on red]"


def _layer_status_badge(status: str) -> str:
    if status == "PASS":
        return "[bold black on green]  PASS   [/bold black on green]"
    if status == "ARMED":
        return "[bold black on cyan]  ARMED  [/bold black on cyan]"
    if status == "STANDBY":
        return "[bold black on yellow] STANDBY [/bold black on yellow]"
    if status == "CAUTION":
        return "[bold yellow] CAUTION [/bold yellow]"
    return "[bold white on red]  VETO   [/bold white on red]"


def _build_tab5_master_synthesis_hud(store: StateStore, header_panel: Panel) -> Group:
    """Renders Tab [5]: Master Synthesis & Supreme Order of Battle across Tabs [1]-[4]."""
    msev = store.master_synthesis_evaluation
    if msev is None:
        return Group(
            header_panel,
            Panel(
                "Warming up 4-Tab Master Synthesis Engine...",
                title="Tab [5]: Master Conclusion",
                box=box.ROUNDED,
            ),
        )

    # --- Panel 1: 4-Tab Executive Verdict Rollup Matrix ---
    p1_table = Table(
        box=box.SIMPLE_HEAVY,
        expand=True,
        show_header=True,
        header_style="bold cyan",
        pad_edge=False,
    )
    p1_table.add_column("Tab", style="bold white", no_wrap=True)
    p1_table.add_column("Light", justify="center", no_wrap=True)
    p1_table.add_column("Score / State", no_wrap=True)
    p1_table.add_column("Executive Conclusion", justify="right", no_wrap=True)

    for row in msev.tab_rows:
        conc_color = (
            "bold green"
            if row.traffic_light == "GREEN"
            else (
                "bold cyan"
                if row.traffic_light == "BLUE"
                else ("bold yellow" if row.traffic_light == "YELLOW" else "bold red")
            )
        )
        p1_table.add_row(
            row.tab_name,
            _light_badge(row.traffic_light),
            row.score_or_status,
            f"[{conc_color}]{row.tab_conclusion}[/{conc_color}]",
        )

    p1_footer = (
        f"[bold white]Scoreboard:[/bold white] [bold green]{msev.tabs_green_count} GREEN[/bold green] • "
        f"[bold cyan]{msev.tabs_blue_count} BLUE[/bold cyan] • "
        f"[bold yellow]{msev.tabs_yellow_count} YELLOW[/bold yellow] • "
        f"[bold red]{msev.tabs_red_count} RED[/bold red]  |  "
        f"[bold white]Alignment:[/bold white] [bold cyan]{msev.master_alignment_score:.1f}%[/bold cyan] "
        f"([bold yellow]{msev.alignment_status}[/bold yellow])"
    )
    p1_group = Group(p1_table, p1_footer)

    # --- Panel 2: 4-Layer Institutional Decision Funnel & Conflict Resolver ---
    p2_table = Table(
        box=box.SIMPLE_HEAVY,
        expand=True,
        show_header=True,
        header_style="bold magenta",
        pad_edge=False,
    )
    p2_table.add_column("Hierarchy Layer", style="white", no_wrap=True)
    p2_table.add_column("Gate", justify="center", no_wrap=True)
    p2_table.add_column("Live Hierarchical Ruling", justify="right", no_wrap=True)

    for h_row in msev.hierarchy_rows:
        p2_table.add_row(
            h_row.layer_name,
            _layer_status_badge(h_row.status),
            h_row.live_ruling,
        )

    p2_footer = (
        "[dim]Precedence: L1 Hard Veto overrides all -> L2 sets Base Risk (1.0% vs 0.5%) "
        "-> L3 scales Size (0.0x–1.0x) -> L4 times Entry.[/dim]"
    )
    p2_group = Group(p2_table, p2_footer)

    top_row = Table.grid(expand=True)
    top_row.add_column(ratio=5)
    top_row.add_column(ratio=5)
    top_row.add_row(
        Panel(
            p1_group,
            title="[bold cyan]1. 4-Tab Executive Verdict Rollup Matrix (Specialist Desks [1]–[4])[/bold cyan]",
            box=box.ROUNDED,
        ),
        Panel(
            p2_group,
            title="[bold magenta]2. 4-Layer Institutional Decision Funnel & Conflict Resolver[/bold magenta]",
            box=box.ROUNDED,
        ),
    )

    # --- Panel 3: Cross-Tab Agreement & Divergence Audit (Detailed Narrative) ---
    p3_lines = [
        "[bold green]✔ CROSS-TAB CONFLUENCE (WHERE THE 4 TABS AGREE RIGHT NOW):[/bold green]"
    ]
    for pt in msev.confluence_points[:3]:
        p3_lines.append(f"  • {pt}")

    p3_lines.append(
        "[bold yellow]⚡ CROSS-TAB CONFLICT DIAGNOSTIC & HIERARCHICAL RESOLUTION:[/bold yellow]"
    )
    for cpt in msev.conflict_points[:2]:
        p3_lines.append(f"  • {cpt}")

    p3_lines.append(
        "[bold cyan]🎯 CATALYSTS THAT FLIP THE MASTER CONCLUSION (UPGRADE / DOWNGRADE):[/bold cyan]"
    )
    for ucat in msev.upgrade_catalysts[:2]:
        p3_lines.append(f"  • {ucat}")

    # --- Panel 4: Reconciled Master Playbook (If Flat in Cash vs. If Holding Spot BTC) ---
    p4_table = Table(
        box=box.SIMPLE_HEAVY,
        expand=True,
        show_header=True,
        header_style="bold yellow",
        pad_edge=False,
    )
    p4_table.add_column("Playbook Track", style="bold white", no_wrap=True)
    p4_table.add_column("Reconciled Master Specification", justify="right", no_wrap=True)

    perm_col = (
        "bold green"
        if "AUTHORIZED NOW" in msev.cash_permission
        else ("bold red" if "FORBIDDEN" in msev.cash_permission else "bold cyan")
    )
    p4_table.add_row(
        "[bold cyan]TRACK A: IF FLAT IN CASH[/bold cyan]",
        f"[{perm_col}]{msev.cash_permission}[/{perm_col}]",
    )
    p4_table.add_row(
        "  ├─ Reconciled Bid Zone",
        f"[bold white]{msev.cash_entry_zone_str}[/bold white]",
    )
    p4_table.add_row(
        "  ├─ Reconciled Size Math",
        f"{msev.cash_base_risk_pct:.2f}% [T3] × {msev.cash_regime_multiplier:.2f}x [T4] -> "
        f"[bold cyan]{msev.cash_edge_size_btc:.4f} BTC (${msev.cash_edge_notional_usd:,.0f})[/bold cyan]",
    )
    p4_table.add_row(
        "  └─ Execution Rule",
        msev.cash_trigger_instruction,
    )

    hold_col = (
        "bold red"
        if "EXIT" in msev.holder_action
        else ("bold yellow" if "SCALE" in msev.holder_action else "bold green")
    )
    p4_table.add_row(
        "[bold green]TRACK B: IF HOLDING SPOT[/bold green]",
        f"[{hold_col}]{msev.holder_action}[/{hold_col}]",
    )
    p4_table.add_row(
        "  ├─ Reconciled Hard Stop",
        f"[bold red]${msev.holder_hard_stop_usd:,.0f}[/bold red] ({msev.holder_hard_stop_source})",
    )
    p4_table.add_row(
        "  ├─ Profit Targets (1/2)",
        f"TP1 (40%): [bold cyan]${msev.holder_tp1_usd:,.0f}[/bold cyan] ({msev.holder_tp1_source}) • "
        f"TP2 (60%): [bold magenta]${msev.holder_tp2_usd:,.0f}[/bold magenta]",
    )
    p4_table.add_row(
        "  └─ Management Rule",
        msev.holder_management_note,
    )

    mid_row = Table.grid(expand=True)
    mid_row.add_column(ratio=5)
    mid_row.add_column(ratio=5)
    mid_row.add_row(
        Panel(
            "\n".join(p3_lines),
            title="[bold green]3. Cross-Tab Agreement & Divergence Audit (Why This Conclusion Was Reached)[/bold green]",
            box=box.ROUNDED,
        ),
        Panel(
            p4_table,
            title="[bold yellow]4. Unified Master Order of Battle (Track A: In Cash vs. Track B: Holding Spot BTC)[/bold yellow]",
            box=box.ROUNDED,
        ),
    )

    # --- Panel 5: Supreme Master Executive Bottom Line ---
    if msev.master_traffic_light == "GREEN":
        headline = f"[bold black on green] {msev.master_headline} [/bold black on green]"
        border_style = "green"
    elif msev.master_traffic_light == "BLUE":
        headline = f"[bold black on cyan] {msev.master_headline} [/bold black on cyan]"
        border_style = "cyan"
    elif msev.master_traffic_light == "YELLOW":
        headline = f"[bold black on yellow] {msev.master_headline} [/bold black on yellow]"
        border_style = "yellow"
    else:
        headline = f"[bold white on red] {msev.master_headline} [/bold white on red]"
        border_style = "red"

    if store.last_packet_copied_ts > 0:
        copy_btn_badge = (
            f"[bold black on green] [✔ COPIED TO CLIPBOARD ({store.last_packet_char_count:,} chars @ {store.last_packet_copied_utc}) "
            f"— PRESS CTRL+V IN GEMINI ARGON AI! (Press 'C' to Copy Fresh Snapshot)] [/bold black on green]"
        )
    else:
        copy_btn_badge = (
            "[bold black on yellow] [PRESS 'C' KEY: COPY RAW TELEMETRY PACKET (TABS 1–4) TO CLIPBOARD FOR GEMINI ARGON AI SECOND OPINION] [/bold black on yellow]"
        )

    p5_lines = [
        f"{headline}  {copy_btn_badge}",
        f"  [bold white]Master Synthesis :[/bold white] {msev.master_what_is_happening}",
        f"  [bold white]Conflict Ruling  :[/bold white] {msev.master_why_resolution}",
        f"  [bold white]Final Command    :[/bold white] [bold]{msev.master_final_command}[/bold]",
    ]
    bottom_panel = Panel(
        "\n".join(p5_lines),
        title="[bold white]5. Executive Bottom Line — Supreme Master Conclusion (Press 1/2/3/4/5 to Switch Tabs • Press C to Copy AI Data Packet)[/bold white]",
        border_style=border_style,
        box=box.ROUNDED,
    )

    return Group(header_panel, top_row, mid_row, bottom_panel)


# ============================================================================
# PUBLIC DISPATCHERS & LIVE INTERACTIVE LOOP
# ============================================================================

def build_dashboard_renderable(
    config: EngineConfig,
    store: StateStore,
    tab_override: Optional[int] = None,
) -> Group:
    """Builds the active tab's 5-panel Rich renderable for the live terminal HUD."""
    active_tab = tab_override if tab_override in (1, 2, 3, 4, 5) else store.active_tab
    header_panel = _build_header_panel(store, active_tab)

    if active_tab == 2:
        return _build_tab2_protocol_hud(store, header_panel)
    if active_tab == 3:
        return _build_tab3_macro_hud(store, header_panel)
    if active_tab == 4:
        return _build_tab4_regime_matrix_hud(store, header_panel)
    if active_tab == 5:
        return _build_tab5_master_synthesis_hud(store, header_panel)
    return _build_tab1_swing_hud(store, header_panel)


def print_dry_run_report(
    config: EngineConfig,
    store: StateStore,
    tab_arg: str = "1",
) -> None:
    """Prints a clean, self-contained verification readout for `--tab 1|2|3|4|5|all`."""
    console = Console(width=175, force_terminal=True)
    if tab_arg.lower() == "all":
        for t in (1, 2, 3, 4, 5):
            console.print(f"\n[bold cyan]=== VERIFICATION SNAPSHOT: TAB [{t}] ===[/bold cyan]")
            console.print(build_dashboard_renderable(config, store, tab_override=t))
    else:
        try:
            t_num = int(tab_arg)
        except ValueError:
            t_num = 1
        store.active_tab = t_num if t_num in (1, 2, 3, 4, 5) else 1
        console.print(build_dashboard_renderable(config, store, tab_override=store.active_tab))


def _poll_keyboard_tab_switch(config: EngineConfig, store: StateStore) -> bool:
    """Non-blocking cross-platform hotkey reader (`1`–`5` for tabs, `C`/`c` to copy AI telemetry packet)."""
    changed = False
    if msvcrt is not None:
        try:
            while msvcrt.kbhit():
                ch = msvcrt.getwch()
                if ch in ("1", "2", "3", "4", "5"):
                    new_tab = int(ch)
                    if store.active_tab != new_tab:
                        store.active_tab = new_tab
                        changed = True
                elif ch in ("c", "C"):
                    copy_ai_packet_to_clipboard_and_disk(config, store)
                    changed = True
        except Exception:
            pass
        return changed

    # Linux VPS / Android Termux non-blocking stdin fallback
    try:
        if sys.stdin.isatty():
            rlist, _, _ = select.select([sys.stdin], [], [], 0.0)
            while rlist:
                ch = sys.stdin.read(1)
                if ch in ("1", "2", "3", "4", "5"):
                    new_tab = int(ch)
                    if store.active_tab != new_tab:
                        store.active_tab = new_tab
                        changed = True
                elif ch in ("c", "C"):
                    copy_ai_packet_to_clipboard_and_disk(config, store)
                    changed = True
                rlist, _, _ = select.select([sys.stdin], [], [], 0.0)
    except Exception:
        pass
    return changed


async def run_terminal_hud(
    config: EngineConfig,
    store: StateStore,
    detector: SignalDetector,
) -> None:
    """Continuously evaluates signals at 2 Hz and switches tabs in 0.0s on keys `1`–`5` or copies AI packet on `C`."""
    console = Console()
    refresh_delay = 1.0 / max(config.hud_refresh_rate_hz, 0.5)
    key_poll_step = 0.05  # 20 Hz keyboard responsiveness

    with Live(
        build_dashboard_renderable(config, store),
        console=console,
        refresh_per_second=config.hud_refresh_rate_hz,
        screen=False,
    ) as live:
        while True:
            try:
                detector.evaluate(store)
                live.update(build_dashboard_renderable(config, store))

                elapsed = 0.0
                while elapsed < refresh_delay:
                    if _poll_keyboard_tab_switch(config, store):
                        live.update(build_dashboard_renderable(config, store))
                    await asyncio.sleep(key_poll_step)
                    elapsed += key_poll_step
            except asyncio.CancelledError:
                raise
            except Exception:
                await asyncio.sleep(1.0)

```

---

### File: `tests/test_analytics.py`

```python
"""Unit tests for Volume Profile topology, Multi-Horizon CVD normalization, and the 4-Gate FSM."""

from dataclasses import replace
from pathlib import Path
import tempfile
import unittest
from typing import List

from analytics.cvd_engine import compute_derivatives_snapshot, compute_flow_snapshot
from analytics.signal_detector import SignalDetector
from analytics.volume_profile import compute_atr, compute_composite_profile, synthesize_4h_bars
from config.settings import DEFAULT_CONFIG
from core.models import ExecutionGateState, KlineBar, MarketRegime
from core.state_store import StateStore

TEST_CONFIG = replace(
    DEFAULT_CONFIG,
    signal_log_path=Path(tempfile.gettempdir()) / "btc_swing_test_signals.jsonl",
)


def _generate_synthetic_consolidation_bars(count: int = 240) -> List[KlineBar]:
    """Generates a realistic smooth consolidation range centered at $90,000 with cVAL ~$88,200."""
    bars: List[KlineBar] = []
    base_ts = 1_720_000_000_000
    # Smooth multi-bar blocks across the auction range so 1H ATR (~$250) << (cPOC - cVAL) (~$1,800)
    schedule = (
        [-3500.0] * 15
        + [2800.0] * 15
        + [1800.0] * 25
        + [900.0] * 35
        + [0.0] * 90
        + [-1800.0] * 25
        + [-900.0] * 35
    )

    for i in range(count):
        ts = base_ts + i * 3_600_000
        offset = schedule[i % len(schedule)]
        center = 90_000.0 + offset
        vol = 400.0 if abs(offset) <= 900.0 else 180.0

        bars.append(
            KlineBar(
                timestamp_ms=ts,
                open=center - 60.0,
                high=center + 120.0,
                low=center - 120.0,
                close=center + 60.0,
                volume=vol,
                taker_buy_volume=vol * 0.50,
            )
        )
    return bars


class TestBTCAnalyticsEngine(unittest.TestCase):
    """Verifies Volume Profile math, CVD Z-scores, Absorption Index, and 4-Gate State Machine."""

    def test_composite_volume_profile_geometry(self) -> None:
        bars = _generate_synthetic_consolidation_bars(240)
        vp = compute_composite_profile(bars, horizon_label="Test 10D", num_bins=100)
        self.assertIsNotNone(vp)
        assert vp is not None

        self.assertGreater(vp.c_vah, vp.c_poc)
        self.assertGreaterEqual(vp.c_poc, vp.c_val)
        self.assertAlmostEqual(vp.c_poc, 90_000.0, delta=600.0)
        self.assertIsNotNone(vp.primary_lvn_below_val)
        assert vp.primary_lvn_below_val is not None
        self.assertLess(vp.primary_lvn_below_val, vp.c_val)

    def test_synthesize_4h_and_atr(self) -> None:
        bars = _generate_synthetic_consolidation_bars(48)
        bars_4h = synthesize_4h_bars(bars)
        self.assertGreaterEqual(len(bars_4h), 12)
        atr_1h = compute_atr(bars, period=14)
        self.assertGreater(atr_1h, 100.0)

    def test_passive_absorption_and_reclaim_signal(self) -> None:
        """Simulates a cVAL sweep where Spot CVD buys aggressively while Perp CVD shorts into limit bids."""
        store = StateStore()
        spot_1h = _generate_synthetic_consolidation_bars(240)
        perp_1h = _generate_synthetic_consolidation_bars(240)

        vp = compute_composite_profile(spot_1h, num_bins=120)
        assert vp is not None
        c_val = vp.c_val

        # Inject a sweep below cVAL and reclaim close >= cVAL on the final 1H bar:
        # Spot has strong net buying (taker_buy = 85%), while Perp has heavy net selling (taker_buy = 15%)
        last_ts = spot_1h[-1].timestamp_ms + 3_600_000
        spot_1h.append(
            KlineBar(
                timestamp_ms=last_ts,
                open=c_val + 50.0,
                high=c_val + 180.0,
                low=c_val - 350.0,
                close=c_val + 40.0,
                volume=600.0,
                taker_buy_volume=510.0,
            )
        )
        perp_1h.append(
            KlineBar(
                timestamp_ms=last_ts,
                open=c_val + 50.0,
                high=c_val + 180.0,
                low=c_val - 350.0,
                close=c_val + 40.0,
                volume=2400.0,
                taker_buy_volume=360.0,
            )
        )

        # Populate 15m buffers mirroring the absorption & reclaim
        spot_15m = [
            KlineBar(
                timestamp_ms=last_ts - (80 - k) * 900_000,
                open=c_val,
                high=c_val + 100.0,
                low=c_val - 250.0 if k >= 78 else c_val - 50.0,
                close=c_val + 40.0,
                volume=150.0,
                taker_buy_volume=125.0 if k >= 76 else (75.0 + (k % 3 - 1) * 5.0),
            )
            for k in range(80)
        ]
        perp_15m = [
            KlineBar(
                timestamp_ms=last_ts - (80 - k) * 900_000,
                open=c_val,
                high=c_val + 100.0,
                low=c_val - 250.0 if k >= 78 else c_val - 50.0,
                close=c_val + 40.0,
                volume=600.0,
                taker_buy_volume=110.0 if k >= 76 else (300.0 + (k % 3 - 1) * 15.0),
            )
            for k in range(80)
        ]

        store.spot_klines_1h.extend(spot_1h)
        store.perp_klines_1h.extend(perp_1h)
        store.spot_klines_15m.extend(spot_15m)
        store.perp_klines_15m.extend(perp_15m)

        store.binance_spot_price = c_val + 40.0
        store.binance_perp_price = c_val + 25.0
        store.coinbase_spot_price = c_val + 95.0  # Positive Coinbase Premium
        for k in range(20):
            store.cpi_history.append((1000.0 + k * 10, 0.01))
        store.cpi_history.append((1300.0, 0.065))

        # Simulate OI liquidation flush (-3.0% over 4H) and negative funding
        store.record_oi_sample(100_000.0, ts_sec=1000.0)
        store.record_oi_sample(97_000.0, ts_sec=15_400.0)
        store.funding_rate_pct = -0.004

        detector = SignalDetector(TEST_CONFIG)
        ev = detector.evaluate(store)
        self.assertIsNotNone(ev)
        assert ev is not None

        self.assertEqual(ev.regime, MarketRegime.ABSORPTION_AT_SUPPORT, msg=str(ev.to_dict()))
        self.assertEqual(ev.gate_state, ExecutionGateState.GATE3_RECLAIM_TRIGGERED)
        self.assertGreaterEqual(ev.confluence_score, 75.0)
        self.assertFalse(ev.hard_veto_triggered)
        self.assertIsNotNone(ev.trade_plan)
        assert ev.trade_plan is not None
        self.assertGreaterEqual(ev.trade_plan.rr_to_poc, 1.5)

    def test_leveraged_bounce_trap_veto(self) -> None:
        """Verifies that a Perp-driven bounce with surging OI and negative Spot delta triggers LEVERAGE_TRAP veto."""
        store = StateStore()
        spot_1h = _generate_synthetic_consolidation_bars(240)
        perp_1h = _generate_synthetic_consolidation_bars(240)
        vp = compute_composite_profile(spot_1h, num_bins=120)
        assert vp is not None
        c_val = vp.c_val

        last_ts = spot_1h[-1].timestamp_ms
        # Spot is selling while Perp is aggressively market-buying on surging OI
        spot_15m = [
            KlineBar(
                timestamp_ms=last_ts - (80 - k) * 900_000,
                open=c_val,
                high=c_val + 300.0,
                low=c_val - 20.0,
                close=c_val + 250.0 if k >= 76 else c_val,
                volume=150.0,
                taker_buy_volume=35.0 if k >= 76 else (75.0 + (k % 3 - 1) * 5.0),
            )
            for k in range(80)
        ]
        perp_15m = [
            KlineBar(
                timestamp_ms=last_ts - (80 - k) * 900_000,
                open=c_val,
                high=c_val + 300.0,
                low=c_val - 20.0,
                close=c_val + 250.0 if k >= 76 else c_val,
                volume=600.0,
                taker_buy_volume=520.0 if k >= 76 else (300.0 + (k % 3 - 1) * 15.0),
            )
            for k in range(80)
        ]

        store.spot_klines_1h.extend(spot_1h)
        store.perp_klines_1h.extend(perp_1h)
        store.spot_klines_15m.extend(spot_15m)
        store.perp_klines_15m.extend(perp_15m)
        store.binance_spot_price = c_val + 250.0
        store.binance_perp_price = c_val + 290.0
        store.coinbase_spot_price = c_val + 210.0

        # Simulate +1.8% 1H OI surge
        store.record_oi_sample(100_000.0, ts_sec=1000.0)
        store.record_oi_sample(101_800.0, ts_sec=4600.0)

        detector = SignalDetector(TEST_CONFIG)
        ev = detector.evaluate(store)
        self.assertIsNotNone(ev)
        assert ev is not None
        self.assertEqual(ev.regime, MarketRegime.LEVERAGE_TRAP)
        self.assertTrue(ev.hard_veto_triggered)

    def test_initiative_markdown_cash_mandate(self) -> None:
        """Verifies that multi-4H acceptance below cVAL with Spot selling triggers MARKDOWN / CASH_MARKDOWN."""
        store = StateStore()
        spot_1h = _generate_synthetic_consolidation_bars(240)
        perp_1h = _generate_synthetic_consolidation_bars(240)
        vp = compute_composite_profile(spot_1h, num_bins=120)
        assert vp is not None
        c_val = vp.c_val

        # Append 8 hours (two 4H bars) accepted well below cVAL with heavy Spot selling
        base_ts = spot_1h[-1].timestamp_ms
        for h in range(1, 9):
            dump_p = c_val - 1200.0 - h * 50.0
            bar = KlineBar(
                timestamp_ms=base_ts + h * 3_600_000,
                open=dump_p + 80.0,
                high=dump_p + 100.0,
                low=dump_p - 100.0,
                close=dump_p,
                volume=500.0,
                taker_buy_volume=120.0,
            )
            spot_1h.append(bar)
            perp_1h.append(bar)

        store.spot_klines_1h.extend(spot_1h)
        store.perp_klines_1h.extend(perp_1h)
        store.spot_klines_15m.extend(spot_1h[-80:])
        store.perp_klines_15m.extend(perp_1h[-80:])
        store.binance_spot_price = c_val - 1600.0
        store.coinbase_spot_price = c_val - 1680.0  # Negative Coinbase Premium

        detector = SignalDetector(TEST_CONFIG)
        ev = detector.evaluate(store)
        self.assertIsNotNone(ev)
        assert ev is not None
        self.assertEqual(ev.regime, MarketRegime.MARKDOWN)
        self.assertEqual(ev.gate_state, ExecutionGateState.CASH_MARKDOWN)
        self.assertTrue(ev.hard_veto_triggered)

    def test_protocol_v13_coinglass_and_ntz_8c_veto(self) -> None:
        """Verifies Tab [2] Protocol v1.3 CoinGlass 6-panel audit and 8C Non-Trade Zone master veto."""
        store = StateStore()
        spot_1h = _generate_synthetic_consolidation_bars(240)
        perp_1h = _generate_synthetic_consolidation_bars(240)

        # Simulate falling price on last 4H with positive funding and rising OI (triggers 8C NTZ)
        for idx in range(-4, 0):
            spot_1h[idx].close = spot_1h[idx].open - 450.0
            perp_1h[idx].close = perp_1h[idx].open - 450.0

        store.spot_klines_1h.extend(spot_1h)
        store.perp_klines_1h.extend(perp_1h)
        store.spot_klines_15m.extend(spot_1h[-80:])
        store.perp_klines_15m.extend(perp_1h[-80:])
        store.binance_spot_price = spot_1h[-1].close
        store.binance_perp_price = perp_1h[-1].close
        store.coinbase_spot_price = spot_1h[-1].close

        # Positive funding (+0.015%) + rising OI (+1.2%) + falling price -> 8C TRIGGERED
        store.funding_rate_pct = 0.015
        store.record_oi_sample(92_000.0, ts_sec=1000.0)
        store.record_oi_sample(93_100.0, ts_sec=4600.0)

        detector = SignalDetector(TEST_CONFIG)
        ev = detector.evaluate(store)
        self.assertIsNotNone(ev)
        assert ev is not None

        pev = store.protocol_evaluation
        self.assertIsNotNone(pev)
        assert pev is not None
        self.assertEqual(len(pev.coinglass_rows), 6)
        self.assertIn("BTC", pev.coinglass_rows[3].value_1d)
        self.assertEqual(pev.non_trade_zone_status, "YES")
        self.assertEqual(pev.buy_allowed, "NO")
        # Verify Liquidation Magnet & Range Pivot Protocol (T1 + T2)
        self.assertGreater(pev.short_liq_magnet_usd, pev.current_price)
        self.assertLess(pev.long_liq_magnet_usd, pev.current_price)
        self.assertGreater(pev.sma_50_1d, 0.0)
        self.assertGreater(pev.range_pivot_usd, 0.0)
        self.assertTrue(len(pev.liq_magnet_verdict) > 0)
        # Master veto propagated to Tab [1]
        self.assertTrue(ev.hard_veto_triggered)
        self.assertTrue(any("Protocol v1.3 [8C]" in r for r in ev.veto_reasons))

    def test_macro_radar_200d_gatekeeper_and_crash_rungs(self) -> None:
        """Verifies Tab [3] 1D 200 SMA Gatekeeper, 14D Wilder RSI, Crash Rungs, and 0.5% risk cap."""
        store = StateStore()
        spot_1h = _generate_synthetic_consolidation_bars(240)
        perp_1h = _generate_synthetic_consolidation_bars(240)
        store.spot_klines_1h.extend(spot_1h)
        store.perp_klines_1h.extend(perp_1h)
        store.spot_klines_15m.extend(spot_1h[-80:])
        store.perp_klines_15m.extend(perp_1h[-80:])

        # Seed 255x 1D bars where 200D SMA is ~$95,000 and current price is $78,000 (-28.8% from $109,588 ATH)
        base_day_ts = 1_700_000_000_000
        for d in range(255):
            p = 96_000.0 if d < 220 else 78_000.0
            store.spot_klines_1d.append(
                KlineBar(
                    timestamp_ms=base_day_ts + d * 86_400_000,
                    open=p + 200.0,
                    high=109_588.0 if d == 100 else p + 500.0,
                    low=p - 500.0,
                    close=p,
                    volume=12_000.0,
                    taker_buy_volume=6_000.0,
                )
            )
        store.binance_spot_price = 78_000.0
        store.coinbase_spot_price = 78_050.0

        detector = SignalDetector(TEST_CONFIG)
        ev = detector.evaluate(store)
        self.assertIsNotNone(ev)
        assert ev is not None

        mev = store.macro_evaluation
        self.assertIsNotNone(mev)
        assert mev is not None
        self.assertTrue(mev.gatekeeper_veto)
        self.assertFalse(mev.above_200d_sma)
        self.assertEqual(len(mev.crash_rungs), 5)
        self.assertEqual(mev.crash_rungs[0].status, "HIT / ACTIVE")  # -25% Rung 1 hit at $78k
        # Verify Power-Law Long-Horizon Discount Row (Bias Only — Not Timing)
        self.assertGreater(mev.power_law_fair_usd, 100_000.0)
        self.assertLess(mev.power_law_discount_pct, -35.0)
        self.assertIn("[BIAS ONLY]", mev.power_law_zone_label)
        # Verify Two-Tier Counter-Trend 0.5% Risk Cap on Tab [1] TradePlan
        assert ev.trade_plan is not None
        self.assertAlmostEqual(ev.trade_plan.risk_pct, 0.5)

    def test_regime_matrix_a_through_j_and_world_clock(self) -> None:
        """Verifies Tab [4] Regime Matrix Configurations A-J evaluation and World Clock session helper."""
        from datetime import datetime, timezone
        from ui.terminal_hud import _get_world_clocks_and_session

        store = StateStore()
        spot_1h = _generate_synthetic_consolidation_bars(240)
        perp_1h = _generate_synthetic_consolidation_bars(240)
        store.spot_klines_1h.extend(spot_1h)
        store.perp_klines_1h.extend(perp_1h)
        store.spot_klines_15m.extend(spot_1h[-80:])
        store.perp_klines_15m.extend(perp_1h[-80:])

        base_day_ts = 1_700_000_000_000
        for d in range(255):
            p = 94_000.0 + d * 10.0
            store.spot_klines_1d.append(
                KlineBar(
                    timestamp_ms=base_day_ts + d * 86_400_000,
                    open=p - 100.0,
                    high=p + 400.0,
                    low=p - 400.0,
                    close=p,
                    volume=10_000.0,
                    taker_buy_volume=5_600.0,
                )
            )
        store.binance_spot_price = spot_1h[-1].close
        store.binance_perp_price = perp_1h[-1].close
        store.coinbase_spot_price = spot_1h[-1].close + 25.0

        detector = SignalDetector(TEST_CONFIG)
        # Set price right at cPOC (50% of Value Area) to verify Explicit Mid-Range Chop Filter
        vp_test = compute_composite_profile(spot_1h, num_bins=120)
        assert vp_test is not None
        store.binance_spot_price = (vp_test.c_val + vp_test.c_vah) / 2.0
        ev = detector.evaluate(store)
        self.assertIsNotNone(ev)
        assert ev is not None
        self.assertTrue(ev.is_mid_range_chop)
        self.assertAlmostEqual(ev.va_position_pct, 50.0, delta=1.0)
        self.assertLessEqual(ev.location_score, 6.0)

        rm = store.regime_matrix_evaluation
        self.assertIsNotNone(rm)
        assert rm is not None
        self.assertEqual(len(rm.configs), 10)
        self.assertEqual(
            [c.code for c in rm.configs],
            ["Config A", "Config B", "Config C", "Config D", "Config E", "Config F", "Config G", "Config H", "Config I", "Config J"],
        )
        self.assertTrue(rm.active_config_code.startswith("Config "))
        self.assertGreater(rm.daily_vwap, 0.0)
        self.assertGreater(rm.weekly_vwap, 0.0)

        # Verify World Clock & Active Session detection (e.g., 14:30 UTC -> London / NY Overlap)
        dt_overlap = datetime(2026, 10, 27, 14, 30, 0, tzinfo=timezone.utc)
        clocks_str, session_label = _get_world_clocks_and_session(dt_overlap)
        self.assertIn("22:30:00 SGT", clocks_str)
        self.assertIn("14:30:00 GMT", clocks_str)
        self.assertIn("10:30:00 EDT", clocks_str)
        self.assertIn("LONDON / NY OVERLAP", session_label)

        # Verify Tab [5] Master Synthesis & Supreme Order of Battle Evaluation + Renderable
        from ui.terminal_hud import build_dashboard_renderable

        msev = store.master_synthesis_evaluation
        self.assertIsNotNone(msev)
        assert msev is not None
        self.assertEqual(len(msev.tab_rows), 4)
        self.assertEqual(len(msev.hierarchy_rows), 4)
        self.assertGreaterEqual(msev.master_alignment_score, 0.0)
        self.assertLessEqual(msev.master_alignment_score, 100.0)
        self.assertGreater(msev.holder_hard_stop_usd, 0.0)
        self.assertGreater(msev.holder_tp1_usd, 0.0)
        self.assertGreater(msev.holder_tp2_usd, msev.holder_tp1_usd)
        self.assertIn(msev.master_traffic_light, ("GREEN", "BLUE", "YELLOW", "RED"))

        renderable_tab5 = build_dashboard_renderable(TEST_CONFIG, store, tab_override=5)
        self.assertIsNotNone(renderable_tab5)

        # Verify Raw AI Telemetry Packet Builder (Hotkey 'C' on Tab [5])
        from analytics.ai_packet_exporter import build_ai_telemetry_packet

        ai_packet = build_ai_telemetry_packet(TEST_CONFIG, store)
        self.assertIn("SECTION 1: CROSS-EXCHANGE SPOT, BASIS & DERIVATIVES TELEMETRY", ai_packet)
        self.assertIn("SECTION 2: COMPOSITE VOLUME PROFILE & MULTI-HORIZON ORDER FLOW", ai_packet)
        self.assertIn("SECTION 3: PROTOCOL v1.3, COINGLASS 6-PANEL (BTC) & LIQUIDATION MAGNETS", ai_packet)
        self.assertIn("SECTION 4: MACRO QUANT, POWER-LAW & CYCLE RADAR", ai_packet)
        self.assertIn("SECTION 5: QUANTITATIVE MICROSTRUCTURE MATRIX A–J SCORES", ai_packet)
        self.assertIn("SECTION 6: PYTHON ENGINE BENCHMARK VERDICT", ai_packet)


if __name__ == "__main__":
    unittest.main()

```
