# BTC-USD Spot Swing Microstructure & Auction Engine (`btc_swing_engine`)

A modular, institutional-grade quantitative Python terminal for **Long-Only BTC-USD Spot Swing Trading** (Zero Leverage, Zero Shorting). 

It combines **Auction Market Theory (Multi-Horizon Volume Profiles)**, **Multi-Exchange Spot vs. Perpetual Order Flow (CVD)**, **CoinGlass 6-Panel Derivatives Audit & Liquidation Magnets (Protocol v1.3)**, **Macro 200D SMA & Cycle Crash Armor Rungs**, **Microstructure Regime Matrix A–J**, and the **MM-BTC Rough Path Arbitrator**.

---

## The 11 Terminal Desks (Instant `0.0s` Tab Switching)

| Tab | Hotkey | Specialized Focus | Core Technical Machinery |
| :--- | :--- | :--- | :--- |
| **Tab `[0]`** | **`0`** | **BTC Spot Swing Screening & Daily Liquidation Magnet Engine** | Daily Liquidation Magnet Protocol (Master Prompt Steps 1–4: Short/Long Liq Clusters, 50D MA, 30–45D Range & Pivot, OI Trend, 8H Funding, Spot CVD Truth Serum, Headline Filter), **Strict RRR $\ge$ 1:3 Money Management** ($E_{\max}$ 3R Calculator), 1D Macro Gate (`close > EMA50 > EMA200` + BBW 180D Rank $\le$ 30%), Weekly Anchors (`PWL`/`PWH`), 4H Sweep & Reclaim, 1% Fixed-Risk Spot Sizing (100% Equity Ceiling), and Triple Barrier (+2.0R/+3.0R, PWH, 10-day time stop). |
| **Tab `[1]`** | **`1`** | **Tactical Swing & Order Flow Desk** | Gaussian Volume Profile (30D/7D/24H `cVAL`, `cPOC`, `cVAH`), Multi-Horizon CVD (`15m`, `1H`, `4H`, `24H`, `UTC Day`), Passive Absorption Index, 4-Gate State Machine, and 3-EMA Industrial Trend System. |
| **Tab `[2]`** | **`2`** | **Protocol v1.3 & Liquidation Magnets** | Strict BTC CoinGlass 6-Panel Audit, Daily Completed `[-2]` vs. Forming `[-1]` candles, Section 8 Non-Trade Zones (`8A–8F`), and Nearest Liquidation Magnets Above/Below. |
| **Tab `[3]`** | **`3`** | **Macro Quant & Cycle Radar** | Rule 1 Gatekeeper (`1D 200 SMA` + 5D Slope), `1D 21 EMA`, `14D Wilder RSI`, Genesis Power-Law Valuation, Cycle Armor Crash Rungs (`-25%` to `-65%`), and 4H Liquidation Wick Flush Detector. |
| **Tab `[4]`** | **`4`** | **Regime Matrix A–J & Sessions** | 10 Quantitative Microstructure Match Configurations (Configs A through J) paired with real-time Global Market Sessions (`UTC`, `SGP`, `LON`, `NYC`). |
| **Tab `[5]`** | **`5`** / **`S`** | **MM-BTC: The Rough Path Arbitrator** | Terry Lyons' Rough Path Signatures (Order $N \le 2$), Level 2 Quadratic Roughness $\mathcal{R}$, Lévy Signed Areas $A_{(t, P)}, A_{(P, V)}, A_{(P, O)}$, 5 Stochastic Lenses (Kalman, Hurst, FracDiff, Hilbert, Flow), and 15m Micro Order Flow Tripwire. |
| **Tab `[6]`** | **`6`** / **`V`** | **72H Forward Volatility Cone & AI Benchmark** | Hurst-scaled Mandelbrot $t^H$ Garman-Klass Volatility Cones (1σ & 2σ bounds), Variance Compression Ratio (VCR), and Quarantined TSFM Benchmarks (Kronos, Chronos-Bolt, TimesFM 2.5 with 0.0% capital weight). |
| **Tab `[7]`** | **`7`** / **`G`** | **Gartley 222 & 5-Strategy Confluence Radar** | TradingView Pine Script Parity: S1 Donchian Breakout, S2 200 SMA, S3 EMA 20/50, S4 14 RSI, S5 Bollinger Bands, S6 Bull Gartley & S7 Bear Gartley with Fibonacci PRZ levels and Telegram `@Gartleyy_bot` alert delivery. |
| **Tab `[8]`** | **`8`** / **`T`** | **Pattern Invalidation & SFP Trap Radar** | Exploits failed classical patterns (H&S Necklines, Double Bottoms/Tops, Range Extremes), 3-State Trap FSM, CVD Absorption Elasticity, ΔOI Velocity, Asymmetric SFP Reclaims (R:R >= 1:3), and Ingests Live `btc_liquidation_detector` Telemetry (Dollar totals, Q-multiple, and post-flush structure). |
| **Tab `[9]`** | **`9`** / **`E`** | **Terminal Exhaustion & Delta Divergence Radar** | Replaces subjective Elliott Wave counts with deterministic Tom DeMark TD-9 / TD-13 Setups, Multi-Horizon CVD Divergences, OI / Funding Climax Stress ($R:R \ge 1:2.5$), and the Tell-Tale Capitulation Climax Sensor (`tell_tale_candle`: 5x Relative Volume + 0.65 Solid Body). |
| **Tab `[L]`** | **`L`** / **`M`** | **Master Synthesis & Supreme Command Center** | 9-Desk Rollup Matrix synthesizing Tabs `[1]`–`[9]`, 4-Layer Hierarchy Gatekeeper, Confluence Score (0–100), and Dual-Track Allocation (**Track A: Cash** vs. **Track B: Holding**). |

> [!TIP]
> **Unified Operator Experience:** Every desk across Tabs `[0]` through `[L]` features a standardized, compact **Beginner Context & Execution Mandate** banner (`▶ PURPOSE & SCOPE`, `▶ CORE MODELS & FEEDS`, `▶ EXECUTION MANDATE`) placed directly at the top of the HUD to anchor operator decision-making within seconds without terminal overflow.

---

## Detailed Documentation & Specifications

* **[Tab 0 Spot Swing Screener Formal Protocol Specification](file:///C:/Users/aikel/.gemini/antigravity/scratch/btc_swing_engine/docs/SPOT_SWING_SCREENER_SPEC.md)**
* **[Whitepaper & 5-Tab Operational Manual](file:///C:/Users/aikel/.gemini/antigravity/scratch/btc_swing_engine/BTC_SWING_ENGINE_WHITEPAPER.md)**
* **[MM-BTC: The Rough Path Arbitrator Formal Protocol Specification](file:///C:/Users/aikel/.gemini/antigravity/scratch/btc_swing_engine/docs/MM_BTC_PROTOCOL_SPEC.md)**
* **[72-Hour Forward Volatility Cone & TSFM Benchmark Formal Specification](file:///C:/Users/aikel/.gemini/antigravity/scratch/btc_swing_engine/docs/VOLATILITY_CONE_TSFM_SPEC.md)**
* **[Gartley 222 & 5-Strategy Confluence Radar Formal Specification](file:///C:/Users/aikel/.gemini/antigravity/scratch/btc_swing_engine/docs/GARTLEY_5STRATEGY_SPEC.md)**
* **[Pattern Invalidation & SFP Trap Radar Formal Specification](file:///C:/Users/aikel/.gemini/antigravity/scratch/btc_swing_engine/docs/PATTERN_TRAP_SFP_SPEC.md)**
* **[Terminal Exhaustion & Delta Divergence Radar Formal Specification](file:///C:/Users/aikel/.gemini/antigravity/scratch/btc_swing_engine/docs/TERMINAL_EXHAUSTION_SPEC.md)**
* **[Master AI Auditor Rulebook & System Prompt](file:///C:/Users/aikel/.gemini/antigravity/scratch/btc_swing_engine/BTC_AI_AUDITOR_MASTER_PROMPT.md)**

---

## Setup & Quickstart

```powershell
cd C:\Users\aikel\.gemini\antigravity\scratch\btc_swing_engine

# 1. Activate virtual environment and install dependencies
.\.venv\Scripts\pip install -r requirements.txt

# 2. Run Comprehensive Unit Test Suite
.\.venv\Scripts\python -m unittest discover -s tests -v

# 3. Run Self-Contained Verification Dry-Run
.\.venv\Scripts\python main.py --dry-run --duration 3 --tab s5 --copy-packet

# 4. Launch Full Live Interactive Terminal HUD
.\.venv\Scripts\python main.py
```

### Interactive HUD Hotkeys:
* Press **`0`** to switch to Tab **`[0: SPOT SWING]`** (BTC Spot Swing Screening & Alert Engine).
* Press **`L`** or **`M`** to switch to Tab **`[L: MASTER]`** (Master Supreme Command Center).
* Press **`1`** through **`9`** to jump instantly to any of the 9 specialist radar desks in `0.0s`.
* Secondary letter hotkeys: **`S`** (Tab 5: MM-BTC), **`V`** (Tab 6: Volatility Cone), **`G`** (Tab 7: Gartley 222), **`T`** (Tab 8: SFP Trap), **`E`** (Tab 9: Exhaustion).
* Press **`C`** on any tab to export the full quantitative telemetry packet (Sections 0–12) directly to your clipboard and `Downloads/BTC_AI_DATA_PACKET_LATEST.md`.
