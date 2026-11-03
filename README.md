# BTC-USD Spot Swing Microstructure & Auction Engine (`btc_swing_engine`)

A modular, institutional-grade quantitative Python terminal for **Long-Only BTC-USD Spot Swing Trading** (Zero Leverage, Zero Shorting). 

It combines **Auction Market Theory (Multi-Horizon Volume Profiles)**, **Multi-Exchange Spot vs. Perpetual Order Flow (CVD)**, **CoinGlass 6-Panel Derivatives Audit & Liquidation Magnets (Protocol v1.3)**, **Macro 200D SMA & Cycle Crash Armor Rungs**, **Microstructure Regime Matrix A–J**, and the **MM-BTC Rough Path Arbitrator**.

---

## The 10 Terminal Desks (Instant `0.0s` Tab Switching)

| Tab | Hotkey | Specialized Focus | Core Technical Machinery |
| :--- | :--- | :--- | :--- |
| **Tab `[1]`** | `1` | **Tactical Swing Engine** | Gaussian Volume Profile (30D/7D/24H `cVAL`, `cPOC`, `cVAH`), Multi-Horizon CVD (`15m`, `1H`, `4H`, `24H`, `UTC Day`), Passive Absorption Index, and 4-Gate State Machine. |
| **Tab `[2]`** | `2` | **Protocol v1.3 & Liquidation Magnets** | Strict BTC CoinGlass 6-Panel Audit, Daily Completed `[-2]` vs. Forming `[-1]` candles, Section 8 Non-Trade Zones (`8A–8F`), and Nearest Liquidation Magnets Above/Below. |
| **Tab `[3]`** | `3` | **Macro Quant & Cycle Radar** | Rule 1 Gatekeeper (`1D 200 SMA` + 5D Slope), `1D 21 EMA`, `14D Wilder RSI`, Genesis Power-Law Valuation, Cycle Armor Crash Rungs (`-25%` to `-65%`), and 4H Liquidation Wick Flush Detector. |
| **Tab `[4]`** | `4` | **Regime Matrix A–J & Sessions** | 10 Quantitative Microstructure Match Configurations (Configs A through J) paired with real-time Global Market Sessions (`UTC`, `SGP`, `LON`, `NYC`). |
| **Tab `[5]`** | `5` | **Master Synthesis & Order of Battle** | 4-Layer Institutional Decision Funnel resolving cross-tab conflicts into two clear playbooks: **Track A: If Flat in Cash** vs. **Track B: If Holding Spot BTC**. |
| **Tab `[S1]`** | `S` / `6` | **MM-BTC: The Rough Path Arbitrator** | Terry Lyons' Rough Path Signatures (Order $N \le 2$), Level 2 Quadratic Roughness $\mathcal{R}$, Lévy Signed Areas $A_{(t, P)}, A_{(P, V)}, A_{(P, O)}$, 5 Stochastic Lenses (Kalman, Hurst, FracDiff, Hilbert, Flow), and 15m Micro Order Flow Tripwire. |
| **Tab `[S2]`** | `V` / `7` | **72H Forward Volatility Cone & AI Benchmark** | Hurst-scaled Mandelbrot $t^H$ Garman-Klass Volatility Cones (1σ & 2σ bounds), Variance Compression Ratio (VCR), and Quarantined TSFM Benchmarks (Kronos, Chronos-Bolt, TimesFM 2.5 with 0.0% capital weight). |
| **Tab `[S3]`** | `G` / `8` | **Gartley 222 & 5-Strategy Confluence Radar** | TradingView Pine Script Parity: S1 Donchian Breakout, S2 200 SMA, S3 EMA 20/50, S4 14 RSI, S5 Bollinger Bands, S6 Bull Gartley & S7 Bear Gartley with Fibonacci PRZ levels and Telegram `@Gartleyy_bot` alert delivery. |
| **Tab `[S4]`** | `T` / `9` | **Pattern Invalidation & SFP Trap Radar** | Exploits failed classical patterns (H&S Necklines, Double Bottoms/Tops, Range Extremes), 3-State Trap FSM, CVD Absorption Elasticity, ΔOI Velocity, and Asymmetric SFP Reclaims (R:R >= 1:3). |
| **Tab `[S5]`** | `E` / `0` | **Terminal Exhaustion & Delta Divergence Radar** | Replaces subjective Elliott Wave counts with deterministic Tom DeMark TD-9 / TD-13 Setups, Multi-Horizon CVD Divergences (Spot vs. Perp), and Open Interest / Funding Climax Stress ($R:R \ge 1:2.5$). |

> [!TIP]
> **Unified Operator Experience:** Every desk across Tabs `[1]`–`[5]` and `[S1]`–`[S5]` features a standardized, compact **Beginner Context & Execution Mandate** banner (`▶ PURPOSE & SCOPE`, `▶ CORE MODELS & FEEDS`, `▶ EXECUTION MANDATE`) placed directly at the top of the HUD to anchor operator decision-making within seconds without terminal overflow.

---

## Detailed Documentation & Specifications

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
* Press **`1`**–**`5`** to switch between core specialist tabs in `0.0s`.
* Press **`S`**, **`s`**, or **`6`** to switch to Tab **`[S1: MM-BTC QUANT RADAR]`**.
* Press **`V`**, **`v`**, or **`7`** to switch to Tab **`[S2: 72H CONE]`**.
* Press **`G`**, **`g`**, or **`8`** to switch to Tab **`[S3: GARTLEY]`**.
* Press **`T`**, **`t`**, or **`9`** to switch to Tab **`[S4: SFP TRAP]`**.
* Press **`E`**, **`e`**, or **`0`** to switch to Tab **`[S5: EXHAUST]`**.
* Press **`C`** on any tab to export the full quantitative telemetry packet (Sections 1–11) directly to your clipboard and `Downloads/BTC_AI_DATA_PACKET_LATEST.md`.
