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
