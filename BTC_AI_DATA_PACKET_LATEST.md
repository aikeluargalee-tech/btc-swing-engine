# BTC-USD LIVE QUANTITATIVE TELEMETRY PACKET & MASTER AI AUDITOR PROMPT
**Snapshot Timestamp:** `2026-11-08 09:53:08 UTC` (`UTC 2026-11-08 09:53:08 • SGP (Asia) 17:53:08 SGT`)  
**Active Global Market Session:** `LONDON / EU SESSION (EUROPEAN INSTITUTIONAL FLOW)`  
**Mandate:** Strictly Long-Only Spot BTC Swing & Positional Trading (Zero Leverage, Zero Shorting)  
**Reference Portfolio Equity:** `$100,000.00` (Standard Risk: `1.00%` | Counter-Trend Risk Cap: `0.50%` | Hard Single-Trade Notional Cap: `<= 50% Equity`)

## MASTER SYSTEM PROMPT & RULEBOOK FOR GEMINI ARGON / EXTERNAL AI AUDITOR
You are the **Independent Chief Quantitative Strategist & Risk Officer** auditing a live real-time telemetry packet exported from the **`BTC-USD Spot Swing Engine`** (`17-Desk Rich Live Terminal: Tab [0] Master & Desks [1]–[9]`).

### 1. Rule #0 — Strict Anti-Sycophancy & Chief Engineer Authority
* **Do NOT blindly agree with the Python engine's benchmark verdict in Section 6.** Deterministic code evaluates fixed mathematical thresholds and can miss subtle cross-venue divergences (e.g., negative Coinbase Premium while Binance ticks up, 5-minute perp sell bursts, nearby unflushed long-liquidation magnets within 1%, or over-concentrated single-fill entries).
* You have **full Chief Engineer authority** to confirm, refine, split into multiple limit tranches, or override the Python engine's conclusion based on the raw telemetry across all specialist desks (**Desks [1]–[9]**).

### 2. How to Interpret & Audit Sections 0–16 (The Complete 17-Desk Quantitative Playbook)
0. **Section 0 Audit (`Tab [0] BTC Spot Swing Screener, 1:3 RRR Magnet Protocol & Footprint Gate`)**:
   * **1D Macro Squeeze & Weekly PWL Sweep**: Evaluates `Close > EMA50 > EMA200`, `20-BBW 180D Percentile <= 30%`, and `4H Sweep & Reclaim of Previous Week Low (PWL)`.
   * **1:3 RRR Liquidation Magnet Law (Section 0D)**: Requires `>= 3.0R` reward-to-risk to the nearest Short-Liquidation Magnet before authorizing market entries; if `Live R:R < 3.0R`, enforce `Do Nothing` at market and stage limit bids at or below `Max 3R Entry`.
1. **Section 1 Audit (`Cross-Exchange Spot, Basis & Derivatives`)**:
   * **Coinbase Premium (`CPI`)**: `CPI > +0.02%` (`Z >= +0.5σ`) = US institutional spot buying. `CPI < -0.05%` (Coinbase at a deep discount to Binance) = warning that US spot is lagging or selling into offshore USDT moves.
   * **Open Interest (`Strict BTC Coins`) & `dOI %`**: `AGGRESSIVE_SHORT_BUILD` (`Price Down/Flat + OI Up`) is bullish squeeze fuel *only* if `Spot CVD` is positive (passive spot absorbing shorts). `LEVERAGED_LONG_EXPANSION` (`Price Up + OI Up + High Funding > +0.012%`) is a long-trap warning. `LONG_LIQUIDATION_FLUSH` (`Price Down + OI Down`) clears excess leverage.
   * **5m Taker L/S Ratio & 5m Perp Delta**: If `5m Taker L/S < 0.50` with heavy negative `5m Perp Delta`, sellers are actively pressing the tape right now -> prefer staged limit bids over market orders.
2. **Section 2 Audit (`Composite Volume Profile 30D/7D/24H, Multi-Horizon CVD & 15m Footprint`)**:
   * **Value Area & Mid-Range Chop Law**: `cVAL` = lower 70% Value Area support; `cPOC` = fair-value magnet (`TP1`); `cVAH` = upper resistance (`TP2`). If `Value Area Position %` is inside `30%–70%` OR price is floating mid-gap between `Support HVN Floor` and `cVAL` outside the `0.5x ATR` edge (`Mid-Range Chop Flag: True`), **never chase at market**; wait for `cVAL` or `Support HVN Floor`.
   * **Spot vs. Perp CVD Divergence**: True institutional accumulation requires `Spot CVD > 0` (`4H B/S Ratio > 1.05`) while `Perp CVD < 0` (`Spot-Perp Divergence Z > +1.5σ`, `Passive Absorption Index >= 0.85`).
   * **SweepRetestFSM Gate 4 Law**: Never enter on first touch of `cVAL`. Require rejection, candle reclaim, and an orderly retest inside the `±0.20%` retest band (`PENDING_RETEST -> TRIGGERED`). Hard stop is anchored below the sweep wick with a +0.15% buffer.
   * **3-EMA Industrial Confluence Law**: Daily 200 EMA slope and price location form an absolute gatekeeper (No spot buys if price < falling Daily 200 EMA). In bull regimes (`STRONG_BULL` / `WEAK_BULL`), pullback into the 4H 50-EMA zone with >= 2 of 3 positioning confirmations (stable OI, neutral funding <= +0.010%, positive Spot CVD) validates tactical execution.
   * **Bidirectional 15m Footprint 3-Gate Playbook (Section 2C — Symmetrical Accumulation & Distribution)**:
     - **Mode A — Spot Accumulation (Buy Low at Support to Sell Higher)**: `Gate 1` = Lower Support Tap (`30D/7D cVAL`, `Support HVN`, or `Demand POC`); `Gate 2` = Lower-wick trapped seller absorption (aggressive sells absorbed in lower 25% wick with candle bounce) or Battle Zone churn; `Gate 3` = 15m candle delta flipped positive (`BULLISH FLIP CONFIRMED`). All 3 gates authorize spot accumulation with hard stop `-0.15%` below wick and `1:2` / `1:3 R:R` targets.
     - **Mode B — Spot Distribution / Profit Harvest (Sell High to USDT at Resistance & Rebuy Lower)**: `Gate 1` = Upper Resistance Tap (`30D/7D cVAH`, `Range High`, or `Supply POC`); `Gate 2` = Upper-wick trapped buyer exhaustion (aggressive buys absorbed in upper 25% wick with rejection) or Stacked Sell Imbalances; `Gate 3` = 15m candle delta flipped negative (`BEARISH FLIP CONFIRMED`). All 3 gates trigger a `50% Staged Spot Profit Harvest to USDT` with breakout invalidation stop (`+0.15%` above upper wick) and a designated lower support `Rebuy Target` to compound total BTC coin count without leverage.
3. **Section 3 Audit (`Protocol v1.3, CoinGlass 6-Panel in Strict BTC & Liquidation Magnets`)**:
   * **Candle Hygiene**: Separate `1D Completed [-2]` (closed daily bar) from `1D Forming [-1]` (live unclosed bar).
   * **Supreme Veto Gates**: Any `TRIGGERED` Non-Trade Zone (`8A–8F`) or `CONFIRMED` Spot Sell Trigger (`1–4`) locks new buying (`RED LIGHT`).
   * **Liquidation Magnet Law**: In a range regime, price is magnetized toward dense liquidation pools (`Nearest Short-Liq Magnet Above` vs. `Nearest Long-Liq Magnet Below`). If the `Long-Liq Magnet` sits within `~1%` below current support while OI is `>90,000 BTC`, recommend splitting spot buys into **2 tranches** (Tranche 1 at `cVAL`/`Support HVN`, Tranche 2 resting at the `Long-Liq Magnet` / `1D Support` sweep).
4. **Section 4 Audit (`Macro Quant, Power-Law & Cycle Radar`)**:
   * **Rule 1 Gatekeeper (`1D 200 SMA` + 5D Slope)**: Above a rising `200D SMA` authorizes `1.00%` base risk; below the `200D SMA` caps counter-trend risk at `0.50%` (targeting `21D EMA` / `200D SMA`), unless a `-25%` to `-65%` **Cycle Crash Rung** + **`4H Liquidation Wick Flush` (`>= 45%` lower wick)** triggers a deep-value sniper override.
   * **Genesis Power-Law Valuation**: Strictly `[BIAS ONLY — NOT TIMING]` for long-horizon valuation context.
5. **Section 5 & 6 Audit (`Regime Matrix A–J & Sizing Guardrail`)**:
   * Scale base risk by the dominant `Config A–J` multiplier (`1.0x` Config A/J, `0.75x` Config C/F, `0.0x` Config B/D/E/G/H/I) and enforce a **strict `<= 50%` Portfolio Equity Notional Cap** (`$37,500` max at `0.75x` on `$100k` equity).
6. **Section 7 Audit (`MM-BTC: The Rough Path Arbitrator — Tab [5] Raw Desk`)**:
   * **Rough Path Signatures (Order N <= 2)**: Path Roughness R <= 4.50 ensures persistent drift over Brownian noise. Time-Price Levy Area A_(t,P) <= +0.15 guards against convex sweep pump exhaustion. A_(P,V) > 0 verifies institutional absorption.
   * **Orthogonal Lenses (A–E)**: Latent zero-lag Kalman velocity ($/hr), rolling Hurst exponent H (> 0.55 persistent vs. < 0.45 chop), memory-preserving FracDiff d* momentum, and Ehlers Hilbert phase angle (trough vs. peak).
   * **Arbitration & Tripwire**: 3-Gate verdict and 15m micro tripwire must clear for high-conviction spot entries.
7. **Section 8 Audit (`72-Hour Forward Volatility Cone & AI Benchmark Radar — Tab [6] Raw Desk`)**:
   * **Garman-Klass Volatility & Hurst Expansion**: 1σ and 2σ Mandelbrot cones (t^H) map true expected price dispersion over 72 hours. VCR ratio > 2.0x indicates severe variance compression.
   * **Church vs. State Separation**: Quarantined TSFM AI forecasts (0.0% capital weight) vs. institutional order flow execution.
8. **Section 9 Audit (`Gartley 222 & 5-Strategy Confluence Radar — Tab [7] Raw Desk`)**:
   * **Dual-Horizon Confluence**: 1D Macro Trend regime gate + 4H Tactical Swing triggers with exact TradingView Pine Script parity.
   * **Harmonic Geometry**: Bullish & Bearish Gartley 222 Fibonacci ratios (B/XA 0.618, C/AB 0.382-0.886, D/XA 0.786, AB/CD 0.70-1.50) and PRZ levels.
9. **Section 10 Audit (`Pattern Invalidation, Liquidity Sweep & SFP Trap Radar — Tab [8] Raw Desk`)**:
   * **Liquidity Hunting Mechanics**: Classical pattern boundaries (H&S necklines, double tops/bottoms, range extremes) serve as predictable stop-liquidity targets, not invariant barriers.
   * **Absorption & SFP Confirmation**: Negative Perp CVD absorbed by passive spot bids + 15m/1H candle close back inside boundary = confirmed Bear Trap (Long squeeze setup with R:R >= 1:3).
10. **Section 11 Audit (`Terminal Exhaustion & Delta Divergence Radar — Tab [9] Raw Desk`)**:
   * **Objective Turnpoint Detection**: Tom DeMark TD-9 sequential setups (perfected when bar 8/9 extremes exceed bars 6/7) replace subjective Elliott Wave counting with deterministic math.
   * **CVD Divergence & Climax Stress**: Multi-horizon delta exhaustion (Price HH vs CVD LH) + OI and funding climax identifies institutional distribution and exhaustion tops/bottoms.
11. **Section 12 Audit (`Consolidated Protocol Metrics Dossier & Intermarket Cross-Check`)**:
   * **Prior Day/Week Auction & ETF/Macro Context**: Cross-verify Prior Day/Week POC/VAH/VAL location, L2 Order-Book Depth (`±1%`/`±2%`), US Spot ETF net flows, DXY/TIPS real yields, and 14D Wilder RSI / Log-Spread Z-score.
12. **Section 13 Audit (`Tab [P] Price Action & Structure Protocol — SLSP v1.0, Industrial 3-EMA & Tell-Tale Climax`)**:
   * **SLSP v1.0 Swing Liquidity**: Evaluates 4H/1H Industrial 3-EMA trend regime (`EMA21 > EMA55 > EMA200`), 4H Liquidation Wick Flushes (`>= 45%` lower wick), and climax volume absorption.
13. **Section 14 Audit (`Tab [B] Classic Chart Patterns & Candlestick Geometry`)**:
   * **Deterministic Pattern Recognition**: Audits 4H macro and 1H tactical patterns (Double Bottom/Top, Head & Shoulders, Bull/Bear Flags, Triangles, Pinbars/Engulfing candles), neckline breakouts, and invalidation floors.
14. **Section 15 Audit (`Tab [G] Grok Dual-Horizon Flow & 00:00 UTC Anchored VWAP SD Matrix`)**:
   * **Grok Dual-Horizon Analysis**: Cross-checks 4A Swing Context (Daily/4H) vs. 4B Day Context (1H/15m), 00:00 UTC Anchored VWAP ±1σ/±2σ bands, CoinGlass crowding, multi-horizon Spot/Perp CVD divergence, overhead short-liquidation magnets vs. downside long traps, and the Engine Bottomline Verdict.
15. **Section 16 Audit (`Tab [R] SSRN Quantitative Alpha Deck & Academic Empirical Research`)**:
   * **Academic Empirical Foundations**: 5 peer-reviewed SSRN domains (Market Microstructure & Order Book Depth, Time-Series Momentum, Systematic Factor Pricing, On-Chain Structural Metrics, Alternative Data & Machine Learning Friction Hurdles).
   * **5 Operational Academic Risk Gates**: Mesíček & Vojtko (SSRN 5748642) 1D/1H MACD gate, Zarattini et al. (SSRN 5209907) 20D volatility targeting, Karassavidis et al. (SSRN 5821842) 8H ATR dynamic stops, Chan (SSRN 5292305) +30% annualized funding ceiling, and Bysik & Ślepaczuk (SSRN 6795938) 18 bps round-trip cost hurdle.

### 3. Mandatory 5-Part Response Format
Structure your audit into:
1. **Independent Cross-Tab Telemetry Audit** (Bullish Confluence vs. Hidden Friction/Risk Flags across Tab [0] & Specialist Desks [1]–[9], Tab [G], and Tab [R])
2. **Critique of Python Engine Benchmark** (Where you **AGREE** vs. **DISAGREE / REFINE** Section 6)
3. **Independent AI Traffic-Light Verdict & Conviction %** (`GREEN`, `BLUE`, `YELLOW`, or `RED`)
4. **Reconciled Master Order of Battle** (**Track A: If Flat in Cash** with exact Tranche 1/2 `$` zones, `BTC`/`$` sizes, Hard Stop, `TP1`/`TP2` vs. **Track B: If Already Holding Spot BTC** with Hard Stop, `TP1`/`TP2` Profit Harvest levels, and Lower Support Rebuy Target to grow total BTC coin count)
5. **Plain-English Executive Bottom Line** (`What's Happening`, `Why`, `Your Exact Next Move`)

---

## SECTION 1: CROSS-EXCHANGE SPOT, BASIS & DERIVATIVES TELEMETRY (TAB [1] & TAB [4] RAW INPUTS)

| Metric | Live Value | Context / Benchmark |
| :--- | :--- | :--- |
| **Binance Spot Price (`BTCUSDT`)** | `$0.00` | Primary Spot Reference |
| **Coinbase Spot Price (`BTC-USD`)** | `$0.00` | US Institutional Spot Reference |
| **Perp Price (Binance USD-M)** | `Data unavailable` | Perpetual Futures Reference (`Binance USD-M`) |
| **Coinbase Premium Index (CPI)** | `$+0.00` (`+0.0000%`) | Rolling Z-Score: `+0.00σ` |
| **Open Interest (Strict BTC Coins)** | `0.00 BTC` | Notional: `$0` |
| **Open Interest Delta (`15m / 1H / 4H / 24H`)** | `15m: +0.00%` • `1H: +0.00%` • `4H: +0.00%` | `24H dOI: +0.00%` |
| **OI Positioning Quadrant** | `NEUTRAL_CHURN` | Price vs. OI Classification |
| **8H Perpetual Funding Rate** | `+0.0000%` | Neutral Cap: `+0.0120%` • Veto: `+0.0350%` |
| **Annualized Perp Basis** | `+0.00% / yr` | Perp vs. Spot Annualized Carry |
| **5m Taker Long/Short Ratio** | `1.000` | `5m Perp Delta: +0.00 BTC` |

---

## SECTION 2: COMPOSITE VOLUME PROFILE & MULTI-HORIZON ORDER FLOW (TAB [1] RAW METRICS)

### 2A. Gaussian-Smoothed Composite Volume Profiles (120 Bins, 70% Value Area)

| Profile Horizon | Range High | cVAH (Upper VA) | cPOC (Fair Value) | cVAL (Lower VA) | Primary LVN (<cVAL) | Support HVN Floor |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |

### 2B. Multi-Horizon Order Flow, Spot vs. Perp CVD & Passive Absorption

| Horizon | Price Δ% | Spot CVD Delta (BTC) | Spot Z-Score | Perp CVD Delta (BTC) | Perp Z-Score | Spot-Perp Div Z | Passive Absorption Index |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`15m`** | `+0.00%` | `+0.00 BTC` (`+0.0%`) | `+0.00σ` | `Data unavailable` | `Data unavailable` | `Data unavailable` | `0.00` |
| **`1H`** | `+0.00%` | `+0.00 BTC` (`+0.0%`) | `+0.00σ` | `Data unavailable` | `Data unavailable` | `Data unavailable` | `0.00` |
| **`4H`** | `+0.00%` | `+0.00 BTC` (`+0.0%`) | `+0.00σ` | `Data unavailable` | `Data unavailable` | `Data unavailable` | `0.00` |
| **`24H`** | `+0.00%` | `+0.00 BTC` (`+0.0%`) | `+0.00σ` | `Data unavailable` | `Data unavailable` | `Data unavailable` | `0.00` |
| **`UTC Day (00:00)`** | `N/A` | `+0.00 BTC` | `N/A` | `+0.00 BTC` | `N/A` | `N/A` | `N/A` |

## SECTION 12: CONSOLIDATED PROTOCOL METRICS DOSSIER (STANDARDIZED PROTOCOL SPECIFICATION)

> [!IMPORTANT]
> **Strict Protocol Compliance Rule**: All quantitative lookbacks strictly adhere to active protocol definitions. Any unresolvable metric is returned as `unavailable` or `null` — **never estimated or guessed**.

### 12A. Core Price & Structure Metrics

| Metric | Preferred Lookback | Value | Source / Benchmark | Status |
| :--- | :--- | :--- | :--- | :--- |
| **BTC Spot Price** | Current | `$0.00` | Binance BTCUSDT | `LIVE TICK` |
| **24h % Change** | Last 24 hours | `unavailable` | Binance Spot 1D | `CALCULATED` |
| **7d % Change** | Last 7 days | `unavailable` | Binance Spot 1D | `CALCULATED` |
| **Daily SMA50** | 50 daily closes | `unavailable` | 1D Spot Klines | `CALCULATED` |
| **Daily SMA200** | 200 daily closes | `unavailable` | 1D Spot Klines | `CALCULATED` |
| **SMA200 Slope** | 10–20 daily closes | `unavailable (unavailable)` | Landscape Rule | `FALLING (Macro Bear)` |
| **Weekly SMA200** | 200 weekly closes | `unavailable` | 1W Spot Klines () | `CALCULATED` |
| **30–45d Range High** | Last 45 calendar days | `unavailable` | 1D Spot Highs | `ACTIVE RESISTANCE` |
| **30–45d Range Low** | Last 45 calendar days | `unavailable` | 1D Spot Lows | `ACTIVE SUPPORT` |
| **Daily ATR(14)** | 14 daily bars | `unavailable` | Wilder TR(14) | `VOLATILITY YARDSTICK` |
| **Daily VWAP** | Current UTC day (00:00 to now) | `unavailable` | Hourly Weighted Vol | `DEVELOPING` |
| **Weekly VWAP** | Current week (Mon 00:00 to now) | `unavailable` | Hourly Weighted Vol | `DEVELOPING` |
| **20D EMA** | 20 daily bars | `unavailable` | 1D Spot Closes | `FAST PULLBACK FILTER` |
| **50D EMA** | 50 daily bars | `unavailable` | 1D Spot Closes | `SWING PULLBACK ZONE` |
| **200D MA** | 200 daily bars | `EMA: unavailable | SMA: unavailable` | 1D Spot Closes | `MACRO REGIME GATE` |
| **Horizontal Pivots** | Structural Support / Resistance | `Sup: unavailable | Res: unavailable` | Protocol v1.3 | `KEY BOUNDS` |

### 12B. Volume Profile Metrics (Prior Day, Prior Week, Developing)

| Metric | Preferred Lookback | Value | Specification | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Prior Day POC** | Completed Prior UTC Day (00:00–24:00) | `unavailable` | Point of Control (Max Volume) | `FIXED BENCHMARK` |
| **Prior Day VAH** | Completed Prior UTC Day (00:00–24:00) | `unavailable` | 70% Value Area High | `FIXED BENCHMARK` |
| **Prior Day VAL** | Completed Prior UTC Day (00:00–24:00) | `unavailable` | 70% Value Area Low | `FIXED BENCHMARK` |
| **Prior Day High / Low**| Completed Prior UTC Day (00:00–24:00) | `H: unavailable | L: unavailable` | Session Extremes | `FIXED BENCHMARK` |
| **Prior Day Volume** | Completed Prior UTC Day (00:00–24:00) | `unavailable` | Binance Spot Taker+Maker | `FIXED BENCHMARK` |
| **Prior Week POC** | Completed Week (Mon 00:00 - Mon 00:00) | `unavailable` | 168h Composite Profile POC | `WEEKLY PIVOT` |
| **Prior Week VAH** | Completed Week (Mon 00:00 - Mon 00:00) | `unavailable` | 70% Value Area High | `WEEKLY PIVOT` |
| **Prior Week VAL** | Completed Week (Mon 00:00 - Mon 00:00) | `unavailable` | 70% Value Area Low | `WEEKLY PIVOT` |
| **Developing POC** | Current Incomplete UTC Day | `unavailable` | Developing Volume Mode | `DEVELOPING` |
| **Top 3 HVN Nodes** | 30D Macro Composite Profile | `None` | High Volume Nodes | `STRONG SUPPORT/RES` |
| **Top 3 LVN Nodes** | 30D Macro Composite Profile | `None` | Low Volume Nodes | `SLIPPAGE ZONES` |
| **Location vs Prior Day**| Spot relative to Prior Day VA | `N/A` | CME Auction Rule | `AUCTION STATE` |
| **Location vs Prior Week**| Spot relative to Prior Week VA | `N/A` | CME Auction Rule | `MACRO AUCTION` |

### 12C. Derivatives & Positioning Metrics

| Metric | Preferred Lookback | Value | Source / Benchmark | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Open Interest (BTC)** | Current | `0.00 BTC` | Binance USD-M | `LIVE COINS` |
| **Open Interest (USD)** | Current | `$0.00` | Binance USD-M | `NOTIONAL VALUE` |
| **OI 1h % Change** | Last 1 hour | `0.00%` | Regime Radar Window | `STABLE / CHURN` |
| **OI 24h % Change** | Last 24 hours | `0.00%` | 24h Positioning Drift | `STEADY DRIFT` |
| **OI 3D % Change** | Last 3 days (72h) | `0.00%` | Regime Radar Window | `RANGE CHURN` |
| **Funding Rate (8h)** | Current 8h Perp Rate | `0.00% / 8h` | Binance USD-M | `Data unavailable` |
| **Futures Basis (Ann.)**| Current Annualized Carry | `0.00% / yr` | Perp vs. Spot Carry | `HEALTHY CARRY` |
| **Spot CVD (24h)** | Last 24 hours (12–48h Magnet) | `0.00 BTC (Data unavailable)` | Binance Spot Net Taker | `CVD DELTA` |
| **Perp CVD (24h)** | Last 24 hours (12–48h Magnet) | `0.00 BTC (Data unavailable)` | Binance USD-M Net Taker | `LEVERAGE FLOW` |
| **Short-Liq Magnet** | 1-Month Liquidation Pool Above | `unavailable` | N/A | `UPSIDE TARGET` |
| **Long-Liq Magnet** | 1-Month Liquidation Pool Below | `unavailable` | N/A | `DOWNSIDE TARGET` |
| **Order-Book Depth (+/-1%)**| Current Snapshot | `unavailable (Bids / Asks)` | Spot L2 (5000 lvls, ~±1.3% span) | `Data unavailable` |
| **Order-Book Depth (+/-2%)**| Current Snapshot | `unavailable (Bids / Asks)` | Spot L2 (5000 lvls, ~±1.3% span) | `Data unavailable` |
| **Coinbase Premium** | Current Snapshot | `0.00% (0.00σ)` | US Institutional Demand | `COINBASE VS BINANCE` |

### 12D. ETF Flows & Demand Proxies

| Metric | Preferred Lookback | Value | Specification | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Spot ETF Daily Net Flow**| Most recent completed day | `unavailable` | US Spot BTC ETFs | `UNAVAILABLE (No Guessing)` |
| **Spot ETF 3-Day Cum.** | Last 3 completed days | `unavailable` | US Spot BTC ETFs | `UNAVAILABLE (No Guessing)` |
| **Passive Absorption Ratio**| 4H Taker vs Price Delta | `0.00` | Limit Absorption Index | `BALANCED / NO ABSORPTION` |

### 12E. Macro & Intermarket Asset Metrics

| Metric | Preferred Lookback | Value | Source / Benchmark | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Brent Crude Oil** | Current + 5–10d Range | `unavailable (None)` | Yahoo Finance (`BZ=F`) | `LIVE QUOTE` |
| **US 10Y Real Yield (TIPS)**| Current + 5–10d Direction | `unavailable` | FRED (`DFII10`) | `UNAVAILABLE (No Guessing)` |
| **US 10Y Breakeven Infl.**| Current + Recent Change | `unavailable` | FRED (`T10YIE`) | `UNAVAILABLE (No Guessing)` |
| **US 10Y Treasury Yield** | Current + 5d Change | `unavailable (unavailable)` | Yahoo Finance (`^TNX`) | `LIVE YIELD` |
| **US Dollar Index (DXY)**| Current + 5–10d Direction | `unavailable (None)` | Yahoo Finance (`DX-Y.NYB`) | `LIVE INDEX` |
| **S&P 500 Performance** | 1-Session & 5-Session % | `unavailable (1d: unavailable | 5d: unavailable)` | Yahoo Finance (`^GSPC`) | `LIVE BENCHMARK` |
| **Nasdaq Performance** | 1-Session & 5-Session % | `unavailable (1d: unavailable | 5d: unavailable)` | Yahoo Finance (`^IXIC`) | `LIVE BENCHMARK` |
| **CBOE VIX Volatility** | 1-Session & 5-Session Change | `unavailable (1d: unavailable | 5d: unavailable)` | Yahoo Finance (`^VIX`) | `BENIGN / NORMAL` |
| **BTC–S&P 500 Corr (20d)**| ~20 Trading Days | `unavailable` | Rolling Pearson Correlation | `DECOUPLED` |
| **BTC–S&P 500 Corr (60d)**| ~60 Trading Days | `unavailable` | Rolling Pearson Correlation | `DECOUPLED` |

### 12F. Sentiment & Risk Context

| Metric | Preferred Lookback | Value | Source / Benchmark | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Crypto Fear & Greed** | Current | `None / 100 (None)` | Alternative.me API | `LIVE SENTIMENT` |
| **BTC Dominance %** | Current | `unavailable` | CoinGecko Global API | `MARKET CAP DOMINANCE` |
| **Material Headlines (6–48h)**| Last 6–48 hours | `[NATIVE AI CONTEXT] Handled natively by LLM` | Disruption Scanner | `NATIVE AI CONTEXT` |
| **USDT Health Markers** | Current Peg / Reserves | `[NATIVE AI CONTEXT] Handled natively by LLM` | Stablecoin Disruption Rule | `NATIVE AI CONTEXT` |
| **Upcoming 14D Catalysts**| Next 14 calendar days | `[NATIVE AI CONTEXT] Handled natively by LLM` | Macro Catalyst Radar | `NATIVE AI CONTEXT` |

### 12G. Mean-Reversion Inputs (Landscape Protocol)

| Metric | Preferred Lookback | Value | Specification | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Daily RSI(14)** | 14 Daily Closes | `unavailable` | Wilder's RSI(14) | `NEUTRAL` |
| **Log-Spread Raw** | Current Close vs. SMA50 | `unavailable` | $\ln(P) - \ln(\text{SMA}_{50})$ | `DISCOUNT TO 50D MEAN` |
| **Log-Spread 50D StdDev**| 50 Daily Closes | `unavailable` | $\sigma_{50}$ of Log-Spread | `VOLATILITY BASELINE` |
| **Log-Spread Z-Score** | 50-Day Window | `unavailable` | $(\ln(P) - \ln(\text{SMA}_{50})) / \sigma_{50}$ | `STANDARD SPREAD` |

---

## SECTION 13: TAB [P] PRICE ACTION & STRUCTURE PROTOCOL (SLSP v1.0, INDUSTRIAL 3-EMA, BTC LIQUIDATION FLUSH & TELL-TALE CLIMAX)

> [!NOTE]
> **THE 4-PILLAR PRICE ACTION & STRUCTURE CONFLUENCE LAW**
> Integrates File A (SLSP v1.0 swing structure and 1.5R obstacle law), File B (Industrial 3-EMA 200D slope anchor and 4H value zone), Project 8 (BTC Liquidation Flush Detector cascade lifecycle and $75k–$78k demand zone), and Project 7 (Tell-Tale 5.0x volume capitulation climax first-shock alarm).

* **Desk [P] Trade State**: `WARMING_UP / INITIALIZING`
* **Status**: Engine initializing higher-timeframe swing pivots, 4H rejection candles, and liquidation sensor streams.

---

## SECTION 14: TAB [B] CLASSIC CHART PATTERNS & CANDLESTICK GEOMETRY (4H MACRO & 1H BREAKOUT)

* **Top Geometric Pattern**: `None` (0%)
* **Pattern Bias**: `Neutral` | **Trigger State**: `STANDBY`
* **Neckline Breakout Price**: `N/A`
* **Invalidation Floor/Roof**: `N/A`
* **Multi-Timeframe Aligned**: `NO (1H ONLY)`
* **Tactical Playbook**: Awaiting geometric setup.
* **Interactive Chart**: `chart.html` (TradingView Lightweight Chart auto-synced)

---

## SECTION 15: TAB [G] GROK DUAL-HORIZON FLOW & 00:00 UTC ANCHORED VWAP SD MATRIX

* **00:00 UTC Anchored VWAP**: `$68,423.33` | **Stretch Z-Score**: `-4702015663199572.00σ` (`EXTREME_OVERSOLD_-2SD`)
* **VWAP Dispersion (1σ / 2σ)**: `+2.0σ: $68,423.33` | `+1.0σ: $68,423.33` | `-1.0σ: $68,423.33` | `-2.0σ: $68,423.33`
* **CoinGlass Crowding & Positioning**: Top Traders `1.00` (50.0% L) vs Retail Accounts `1.00` (`BALANCED_POSITIONING`)
* **Coinbase Premium Index**: `$+0.00` (`+0.0000%`, Z=`+0.00σ`, `NEUTRAL_BASIS (In-line with Binance Spot)`)
* **Multi-Horizon CVD Divergence**: 24H Spot `+0.0 BTC` vs Perp `+0.0 BTC` (`BALANCED_FLOW (No Dominant Delta Skew)`) | 4H Spot `+0.0 BTC` | 15m Spot `+0.0 BTC`
* **Liquidation Pool Magnets**: Overhead Short Magnet `$0` (~$234M) vs Downside Long Trap `$0` (~$329M)
* **4A. Swing Context (Daily/4H)**: Bitcoin has cleared its Daily 50 EMA ($0) and is trading in a constructive expansion regime. Spot CVD confirmation (+0 BTC) and positive Coinbase Premium (+0.000%) confirm institutional participation. Swing structure targets overhead short liquidation pools anchored at $0.
* **4B. Day Context (1H/15m)**: Intraday price is stretched down to -4702015663199572.00σ below 00:00 UTC VWAP ($68,423), testing the -2.0σ extreme discount shelf ($68,423). Downside liquidity sweeps into -2.0σ that absorb sell orders represent prime high-RRR intraday bounce zones back into value.
* **Engine Bottomline Verdict**: `BULLISH BIAS • CAUTION ON EXPANSION`
  * **Rationale**: Above 50 EMA but lagging spot CVD / negative CPI warns of derivative exhaustion into overhead short liquidations ($0).
  * **Trigger to Buy**: Re-bid at VWAP Value Area Low ($68,423) or confirmed CPI flip positive.
  * **Invalidation Risk**: SFP rejection at $0 falling back below 50 EMA.

---

## SECTION 16: TAB [R] SSRN QUANTITATIVE ALPHA DECK & EMPIRICAL RESEARCH

### 16A. 5 Academic Empirical Domains (Theoretical Foundation)
* **01. Market Microstructure & Order Flow**: Multi-level book depth imbalance has statistically significant predictive power for short-horizon mid-price jumps; Level 1 top-of-book is contaminated by spoofing noise. | *Spot Swing Role:* `Confirms limit-order absorption at 4H/1D swing lows prior to triggering long spot entries.`
* **02. Time-Series Momentum & Technical Rules**: Single lookback moving averages suffer rapid alpha decay; higher-timeframe trend filters prevent whipsaws and preserve capital by holding cash in macro bear regimes. | *Spot Swing Role:* `Primary trend engine. Enforces 100% cash/stablecoin allocation when higher-timeframe momentum is negative.`
* **03. Systematic Factor Pricing (Liu-Tsyvinski)**: Bitcoin carries the primary systemic market beta; returns exhibit fat-tailed positive skewness during bull expansions and downside volatility clustering during liquidations. | *Spot Swing Role:* `Normalizes position risk against aggregate crypto market volatility; prevents over-allocation during volatility spikes.`
* **04. On-Chain Structural Metrics**: MVRV < 1.0 identifies generational macro accumulation; SOPR retests of 1.0 act as structural support during secular bull trends. | *Spot Swing Role:* `Macro floor/ceiling filter to prevent buying into exhausted on-chain distribution regimes.`
* **05. Alternative Data & Machine Learning Hurdles**: Direct price regression models consistently overfit; directional classification conditioned on transaction cost hurdles preserves real-world alpha. | *Spot Swing Role:* `Binary execution filter: signal magnitude must exceed 2x round-trip trading friction (fees + slippage + spread) before firing.`

### 16B. 5 Verified Operational Strategy Models & Live Gate Status
* **Multi-Timeframe Trend Following** (`Mesíček & Vojtko (SSRN 5748642)` • `1H Execution / 1D Trend Filter`): Long entry: 1H MACD line crosses above Signal ONLY when Daily MACD is positive. Exit: Trailing stop at prior 4H swing low or structural close below entry. | **Benchmark:** `Sharpe: 1.07 | Max Drawdown: -12.4% (vs -80% Buy & Hold)` | **Live Condition:** `[RESTRICTED: RESTRICTED (HOLD CASH)]` (1D: +0/+0 • 1H: +0/+0)
* **Ensemble Donchian + Volatility Target** (`Zarattini, Pagani & Barbon (SSRN 5209907)` • `Daily / Multi-Horizon (5–360 Days)`): Aggregates breakout signals across multiple lookback windows (5 to 360d). Position size scaled dynamically: Weight = Target_Vol (25%) / Realized_Vol. | **Benchmark:** `Sharpe: >1.50 | Max Drawdown: ~19% on BTC` | **Live Condition:** `[PASS: ALLOC: 56% EQUITY]` (20D Vol: 45.0% (Tgt: 25%))
* **Volatility-Adaptive Multi-Horizon Trend** (`Karassavidis et al. (SSRN 5821842)` • `8-Hour Candles`): Trend identified across 8H MA slope + RSI momentum filter. Dynamic position sizing and stop placement pegged to multiples of 14-period ATR. | **Benchmark:** `Sharpe: 1.54 | CAGR: ~20% | Max Drawdown: ~12.5%` | **Live Condition:** `[PASS: TRAIL: -$0]` (8H ATR(14): $0)
* **Funding Rate Exhaustion Gate** (`Chan (SSRN 5292305)` • `8H Funding Settlement Intervals`): Spot swing risk gate: When annualized perpetual funding rate exceeds +30% (extreme retail leverage), freeze new spot swing entries to avoid long liquidation cascades. | **Benchmark:** `Regime Protection: Filters out severe local market tops and leverage flushes` | **Live Condition:** `[PASS: PASS (< 30% CEILING)]` (Ann: +0.00%/yr)
* **Cost-Aware Alpha Hurdle Filter** (`Bysik & Ślepaczuk (SSRN 6795938)` • `Hourly / Multi-Hour`): Execute long trades ONLY if expected forward return > (Taker Fee + Slippage + Spread + Margin Hurdle). Suppresses churn during flat ranges. | **Benchmark:** `Sharpe: >1.0 | Eliminates overtrading fee drag` | **Live Condition:** `[PASS: HURDLE: >= +0.18%]` (Friction: 18 bps round-trip)
