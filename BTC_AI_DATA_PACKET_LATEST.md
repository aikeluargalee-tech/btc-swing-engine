# BTC SWING ENGINE | GLOBAL DATA-ONLY TELEMETRY PACKET ([C: AI PACKET])
**Retrieval Time (UTC):** `2026-11-09 00:28:41 UTC`  |  **Retrieval Time (MYT):** `2026-11-09 08:28:41 MYT (UTC+8)`
**Spot Price (BTCUSDT):** `$0.00`
**Output Specification:** `DATA-ONLY (Raw Measurements, Reference Formulas & True/False Conditions Only — Zero Interpretive Prose)`

---

# BTC TREND-PULLBACK v1.0 | DATA-ONLY REPORT (RESEARCH / PAPER MODE)
**STATUS:** `UNVALIDATED`  |  **Retrieval Time (UTC):** `2026-11-09 00:28:41 UTC`  |  **Retrieval Time (MYT):** `2026-11-09 08:28:41 MYT (UTC+8)`
**Spot Price (BTCUSDT):** `$0.00`

## 1. DAILY (1D)
- **Completed 1D Candle Window:** `Open N/A -> Close N/A`
- **Last Completed 1D Close:** `$0.00` (Open `$0.00`, High `$0.00`, Low `$0.00`)
- **Daily SMA50:** `$0.00`
- **Daily SMA200:** `$0.00` (20D Prior SMA200: `$0.00`)
- **Daily SMA200 20D Slope (`SMA200_now - SMA200_20d_ago`):** `$+0.00`
- **Close vs SMA200 (`Close - SMA200`):** `$+0.00` (`+0.00%`)
- **Close vs SMA50 (`Close - SMA50`):** `$+0.00` (`+0.00%`)
- **Close > SMA200:** `False`
- **Close > SMA50:** `False`
- **SMA200 Rising Over 20D (`SMA200_now > SMA200_20d_ago`):** `False`

## 2. 4H TREND METRICS
- **Completed 4H Candle Window:** `Open N/A -> Close N/A`
- **Last Completed 4H Close:** `$0.00`
- **4H EMA50:** `$0.00`
- **4H EMA200:** `$0.00`
- **4H ATR14:** `$0.00`
- **4H EMA50 - EMA200:** `$+0.00`
- **4H EMA50 Now vs 6 Bars Ago:** Now `$0.00` vs 6 Bars Ago `$0.00` (`+0.00` USD)
- **Last 4H Close vs 4H EMA50 (`Close - EMA50`):** `$+0.00` (`+0.0000 ATR` / `+0.00 ATR`)
- **Last 4H Close vs 4H EMA200 (`Close - EMA200`):** `$+0.00` (`+0.0000 ATR` / `+0.00 ATR`)
- **4H EMA50 > 4H EMA200:** `False`
- **4H EMA50 Rising Over 6 Bars (`EMA50_now > EMA50_6bars_ago`):** `False`
- **Last 4H Close > 4H EMA200:** `False`

## 3. PULLBACK ZONE
- **Pullback Zone Formula:** `Zone Lower = 4H EMA50 - 0.50 * 4H ATR14` | `Zone Upper = 4H EMA50 + 0.25 * 4H ATR14` | `Max Extension = 4H EMA50 + 1.00 * 4H ATR14`
- **Zone Lower (`EMA50 - 0.50 * ATR14`):** `$0.00`
- **Zone Upper (`EMA50 + 0.25 * ATR14`):** `$0.00`
- **Max Extension (`EMA50 + 1.00 * ATR14`):** `$0.00`
- **Spot Minus Zone Lower (`Spot - Zone Lower`):** `$+0.00` (`+0.0000 ATR` / `+0.00 ATR`)
- **Spot Minus Zone Upper (`Spot - Zone Upper`):** `$+0.00` (`+0.0000 ATR` / `+0.00 ATR`)
- **Last Completed 4H Candle OHLC:** Open `$0.00`, High `$0.00`, Low `$0.00`, Close `$0.00`
- **Candle Low < Zone Lower:** `False`
- **Candle Low > Zone Upper:** `False`
- **Recovery Candle Sub-Conditions (Last Completed 4H Candle):**
  - `Candle Low >= Zone Lower`: `False`
  - `Candle Low <= Zone Upper`: `False`
  - `Candle Close > 4H EMA50`: `False`
  - `Candle Close > Candle Open`: `False`
  - `Candle Close <= 4H EMA50 + 1.00 * 4H ATR14`: `False`
  - `All 5 Recovery Sub-Conditions True`: `False`

## 4. REFERENCE LEVELS (Reference calculation if entered at $0.00. Not an order.)
- **Reference Entry Zone (`[4H EMA50, 4H EMA50 + 0.10 * 4H ATR14]`):** `$0.00 - $0.00`
- **Reference Entry Price Used (`4H EMA50 + 0.10 * 4H ATR14`):** `$0.00`
- **Distance From Spot To Reference Entry (`Spot - Reference Entry`):** `$+0.00` (`+0.00%`)
- **Stop Level (`min(low of last 5 completed 4H bars) - 0.25 * 4H ATR14`):** `$0.00` (5-Bar Lowest Low `$0.00` - Buffer `$0.00`)
- **Stop Distance From Reference Entry (`Reference Entry $0.00 - Stop Level $0.00`):** `$0.00` (`0.0000 ATR` / `0.00 ATR`)
- **Stop Distance >= 0.75 ATR:** `False`
- **Stop Distance <= 3.00 ATR:** `False`
- **Reference Simulation Equity:** `$100,000.00`
- **Risk Budget (`0.50%` of Reference Equity):** `$500.00`
- **Position Size:** `0.00000 BTC`
- **Position Notional (`Position Size * Reference Entry $0.00`):** `$0.00`
- **Computed Price Risk (`Position Size * Stop Distance $0.00`):** `$0.00` (`$0.00/BTC`)
- **Fee & Slippage Buffer (`0.10%` Entry Fee + `0.10%` Exit Fee + `0.05%` Entry Slippage + `0.05%` Exit Slippage):** `$0.00` (`$0.00/BTC`: Entry Fee `$0.00` + Exit Fee `$0.00` + Entry Slippage `$0.00` + Exit Slippage `$0.00`)
- **Total Estimated Risk (`Computed Price Risk + Fee & Slippage Buffer`):** `$0.00` (`$0.00/BTC`)
- **Total Estimated Risk <= Risk Budget (`$0.00 <= $500.00`):** `False`

## 5. EXIT RULE INPUTS
- **Position Mode Setting:** `CASH`
- **Completed 4H Candle (t-1) (`Open N/A -> Close N/A`):** Close `$0.00` vs 4H EMA50 `$0.00` (`+0.00` USD) | `Close < 4H EMA50`: `False`
- **Completed 4H Candle (t) (`Open N/A -> Close N/A`):** Close `$0.00` vs 4H EMA50 `$0.00` (`+0.00` USD) | `Close < 4H EMA50`: `False`
- **Consecutive Completed 4H Closes Below 4H EMA50:** `0`
- **Completed 1D Candle (t-1) (`Open N/A -> Close N/A`):** Close `$0.00` vs 1D SMA200 `$0.00` (`+0.00` USD) | `Close < 1D SMA200`: `False`
- **Completed 1D Candle (t) (`Open N/A -> Close N/A`):** Close `$0.00` vs 1D SMA200 `$0.00` (`+0.00` USD) | `Close < 1D SMA200`: `False`
- **Consecutive Completed 1D Closes Below 1D SMA200:** `0`
- **Spot <= Stop Level (`$0.00 <= $0.00`):** `False`

## 6. DATA INTEGRITY
- **Data Retrieval Time (UTC):** `2026-11-09 00:28:41 UTC`
- **Data Retrieval Time (MYT):** `2026-11-09 08:28:41 MYT (UTC+8)`
- **Data Integrity Pass:** `False`
- **Completed 1D Candles Available:** `0` | **Last Completed 1D Status:** `UNAVAILABLE` | **Forming 1D Candle Excluded:** `False` (`None`)
- **Completed 4H Candles Available:** `0` | **Last Completed 4H Status:** `UNAVAILABLE` | **Forming 4H Candle Excluded:** `False` (`None`)

---

# TAB [M: MAGNET] | DATA-ONLY METRICS REPORT
**Retrieval Time (UTC):** `2026-11-09 00:28:41 UTC`  |  **Retrieval Time (MYT):** `2026-11-09 08:28:41 MYT (UTC+8)`
**Spot Price (BTCUSDT):** `$76,000.00` (`24H Change: +0.00%`)

## 1. LIQUIDATION GRAVITATIONAL HORIZON
- **Upper Liquidation Cluster (Short Liquidations):** `$77,024.20` (`+1.35%` / `$+1,024.20` from Spot) | Volume: `$233.23M`
- **Center Spot Price:** `$76,000.00`
- **Lower Liquidation Cluster (Long Liquidations):** `$73,196.32` (`-3.69%` / `$-2,803.68` from Spot) | Volume: `$435.36M`
- **Upper-to-Lower Cluster Weight Ratio:** `0.54x` (`Higher Weight Side`: `UPPER`)

## 2. DERIVATIVES & VOLATILITY INPUTS
- **Annualized Perpetual Funding Rate:** `+0.00%/yr`
- **4H Open Interest Delta:** `+0.80%`
- **24H Classification Label:** `Range`

## 3. 7 INTERNAL CONDITION BOOLEANS (TRUE/FALSE)
- **Rule 1 (`Clear Magnet Present`):** `True` (`Magnet ABOVE: $77,024 (+1.3%, $233M)`)
- **Rule 2 (`Open-Interest Confirmation`):** `True` (`OI velocity supportive (+0.8% 4h delta)`)
- **Rule 3 (`Funding Non-Contradictory`):** `True` (`Borrow rate calm (+0.0%/yr carry)`)
- **Rule 4 (`Regime Conduciveness`):** `True` (`Market in Range mode (conducive to magnet sweep)`)
- **Rule 5 (`Spot Flow & Structure Alignment`):** `True` (`Structure intact (24h change: +0.00%)`)
- **Rule 6 (`Not Already Swept`):** `True` (`Target cluster intact and unswept`)
- **Rule 7 (`Conviction Threshold`):** `True` (`6/6 internal filters passed cleanly`)
- **Conditions 1-6 True Count:** `6 / 6`

---

# TAB [G: GROK FLOW] | DATA-ONLY METRICS REPORT
**Retrieval Time (UTC):** `2026-11-09 00:28:42 UTC`  |  **Retrieval Time (MYT):** `2026-11-09 08:28:42 MYT (UTC+8)`
**Spot Price (BTCUSDT):** `$0.00`

## 1. 00:00 UTC ANCHORED VWAP & STANDARD DEVIATION BANDS
- **00:00 UTC Anchored VWAP:** `$68,423.33`
- **1.0 SD Dispersion (`Sigma`):** `$0.00`
- **Spot Minus VWAP (`Spot - VWAP`):** `$-68,423.33` (`-100.00%` | Stretch Z-Score: `-4702015663199572.00 SD`)
- **+2.0 SD Upper Band:** `$68,423.33` | **Spot > +2.0 SD:** `False`
- **+1.0 SD Upper Band:** `$68,423.33` | **Spot > +1.0 SD:** `False`
- **-1.0 SD Lower Band:** `$68,423.33` | **Spot < -1.0 SD:** `True`
- **-2.0 SD Lower Band:** `$68,423.33` | **Spot < -2.0 SD:** `True`
- **Spot Inside [-1.0 SD, +1.0 SD] Band:** `False`

## 2. DAILY & INTRADAY MOVING AVERAGES & SESSION EXTREMES
- **1H EMA9 / 1H EMA21:** `$0.00` / `$0.00` | **1H EMA9 > 1H EMA21:** `False`
- **1D EMA50:** `$0.00` | **Spot Minus 1D EMA50:** `$+0.00` (`+0.00%`) | **Spot > 1D EMA50:** `False`
- **1D SMA200:** `$0.00` | **Spot Minus 1D SMA200:** `$+0.00` (`+0.00%`) | **Spot > 1D SMA200:** `False`
- **Current Day High / Low:** `$0.00` / `$0.00`
- **Previous Day High / Low:** `$0.00` / `$0.00`

## 3. DERIVATIVES POSITIONING & LIQUIDATION CLUSTERS
- **Open Interest:** `0.00 BTC` (`$0`)
- **OI Change (`1H / 4H`):** `+0.00%` / `+0.00%` | **4H OI Change > 0:** `False`
- **8H Perpetual Funding Rate:** `+0.0000%` | **Funding Rate <= 0.0100%:** `True`
- **Top Participant L/S Ratio:** `1.00` (`50.0%` Long / `50.0%` Short)
- **Global Account L/S Ratio:** `1.00` | **Global L/S >= 2.00:** `False`
- **Overhead Short Liquidation Cluster:** `$0.00` (`$234.0M`)
- **Downside Long Liquidation Cluster:** `$0.00` (`$329.0M`)

## 4. MULTI-HORIZON CVD & COINBASE PREMIUM
- **24H CVD (`Spot vs Perp`):** Spot `+0.00 BTC` | Perp `+0.00 BTC` | `Spot CVD 24H > 0`: `False` | `Spot CVD 24H > Perp CVD 24H`: `False`
- **4H CVD (`Spot vs Perp`):** Spot `+0.00 BTC` | Perp `+0.00 BTC` | `Spot CVD 4H > 0`: `False`
- **15m CVD (`Spot vs Perp`):** Spot `+0.00 BTC` | Perp `+0.00 BTC` | `Spot CVD 15m > 0`: `False`
- **Coinbase Premium (`USD / % / Z-Score`):** `$+0.00` (`+0.0000%` | `Z = +0.00`) | **Coinbase Premium > 0:** `False`

---

# TAB [R: SSRN RESEARCH] | DATA-ONLY METRICS REPORT
**Retrieval Time (UTC):** `2026-11-09 00:28:42 UTC`  |  **Retrieval Time (MYT):** `2026-11-09 08:28:42 MYT (UTC+8)`
**Spot Price (BTCUSDT):** `$0.00`

## 1. EMPIRICAL FACTOR & GATE METRICS
- **1D MACD Gate Pass (`1D MACD > Signal or Hist > 0`):** `False`
- **20-Day Annualized Realized Volatility (%):** `39.20%`
- **20-Day Realized Variance:** `0.1537`
- **20-Day Log-Return Skewness:** `-0.15`
- **25% Volatility-Target Reference Weight (%):** `63.8%`
- **8H Equivalent ATR14 (`ATR14_4H * sqrt(2)`):** `$667.00`
- **2.5x 8H ATR Reference Stop Distance:** `$1,667.50`
- **Annualized Perpetual Funding Rate (%/yr):** `+0.00%/yr`
- **Annualized Funding <= 30.0%/yr:** `True`
- **Round-Trip Friction Assumption:** `18.0 bps` (`Cost Hurdle Pass`: `True`)
- **Order Book Imbalance (`1% Depth Ratio`):** `+0.0%`
- **4H Spot CVD Delta:** `-142.50 BTC`
- **MVRV Proxy Ratio (`Spot / (0.62 * 1D SMA200)`):** `1.63`
- **SOPR Proxy Ratio:** `1.0200`

## 2. 5 SSRN MODEL CONDITION BOOLEANS
- **Multi-Timeframe Trend Following (`Mesicek & Vojtko (SSRN 5748642)` | `1H Execution / 1D Trend Filter`):** Condition Pass: `False` | Measured Value: `1D: +0/+0 | 1H: +0/+0`
- **Ensemble Donchian + Volatility Target (`Zarattini, Pagani & Barbon (SSRN 5209907)` | `Daily / Multi-Horizon (5-360 Days)`):** Condition Pass: `True` | Measured Value: `20D Vol: 39.2% | Target Vol: 25.0%`
- **Volatility-Adaptive Multi-Horizon Trend (`Karassavidis et al. (SSRN 5821842)` | `8-Hour Candles`):** Condition Pass: `True` | Measured Value: `8H ATR(14): $667 | Stop Buffer: -$1,668`
- **Funding Rate Exhaustion Gate (`Chan (SSRN 5292305)` | `8H Funding Settlement Intervals`):** Condition Pass: `True` | Measured Value: `Ann: +0.00%/yr | Ceiling: 30.0%`
- **Cost-Aware Alpha Hurdle Filter (`Bysik & Slepaczuk (SSRN 6795938)` | `Hourly / Multi-Hour`):** Condition Pass: `True` | Measured Value: `Fee Hurdle: 18 bps | Min Edge: >= +0.36%`

## 3. 5 EMPIRICAL DOMAIN TELEMETRY
- **01. Market Microstructure & Order Flow:** `OBI: +0.0% | 4H CVD: -142.5 BTC` (Core Metrics: `Order Book Imbalance (OBI), Cumulative Volume Delta (CVD), Spread Dynamics`)
- **02. Time-Series Momentum & Technical Rules:** `1D: CHOP (RANGING) | 4H: CHOP | 1H: BEAR CHOP` (Core Metrics: `Variable Moving Averages (VMA), Time-Series Momentum (TSMOM), Breakout Ensembles`)
- **03. Systematic Factor Pricing (Liu-Tsyvinski):** `Var: 0.1537 | 20D Skew: -0.15` (Core Metrics: `Crypto Market Factor (MKT_crypto), Size/Illiquidity Premium, Downside Risk Semi-Variance`)
- **04. On-Chain Structural Metrics:** `MVRV: 1.63 | SOPR: 1.02` (Core Metrics: `MVRV Ratio, Spent Output Profit Ratio (SOPR), Entity-Adjusted Realized Price`)
- **05. Alternative Data & Machine Learning Hurdles:** `Hurdle: 18 bps (+0.18%)` (Core Metrics: `Search Volume Index (SVI), Cost-Aware Gradient Boosted Trees, Regime Classifiers`)

---

# TAB [P: STRUCTURE] | DATA-ONLY METRICS REPORT
**Retrieval Time (UTC):** `2026-11-09 00:28:42 UTC`  |  **Retrieval Time (MYT):** `2026-11-09 08:28:42 MYT (UTC+8)`
**Spot Price (BTCUSDT):** `$0.00`

## 1. DAILY SWING STRUCTURE & KEY SHELVES (SLSP v1.0)
- **SLSP Evaluation Data Available:** `False`

---

# TAB [F: FOOTPRINT] | DATA-ONLY METRICS REPORT
**Retrieval Time (UTC):** `2026-11-09 00:28:42 UTC`  |  **Retrieval Time (MYT):** `2026-11-09 08:28:42 MYT (UTC+8)`
**Spot Price (BTCUSDT):** `$0.00`

## 1. 15-MINUTE INTRA-CANDLE FOOTPRINT METRICS
- **Active 15m Bar Net Delta:** `+10.00 BTC`
- **Previous Completed 15m Bar Net Delta:** `+10.00 BTC`
- **Active Battle Zone Price:** `$68,425.00`
- **Stacked Imbalances Count:** `0`

## 2. 4 GATE CONDITION BOOLEANS (TRUE/FALSE)
- **Gate 1 (`Macro/Tactical Level Tap`):** `False` (Level: `` at `$0.00`)
- **Gate 2 (`Positioning Filter`):** `True`
- **Gate 3 (`Wick Absorption`):** `False`
- **Gate 4 (`15m Net Delta Flip`):** `False`
- **All Gates True:** `False`

## 3. REFERENCE LEVELS (Reference calculation if entered at $0.00. Not an order.)
- **Reference Entry Price:** `$0.00`
- **Reference Stop Level:** `$0.00`
- **Stop Distance (`|Entry - Stop|`):** `$0.00`
- **1:2 Reference Level:** `$0.00`
- **1:3 Reference Level:** `$0.00`

---

# TAB [W: WATERFALL] | DATA-ONLY METRICS REPORT
**Retrieval Time (UTC):** `2026-11-09 00:28:42 UTC`  |  **Retrieval Time (MYT):** `2026-11-09 08:28:42 MYT (UTC+8)`
**Spot Price (BTCUSDT):** `$0.00`

## 1. 5-PILLAR CONDITION BOOLEANS & RAW INPUTS
- **Pillar 1 (`Confluence Score >= 50.0`):** `False` (Confluence Score: `0.00`)
- **Pillar 2 (`Value Area Edge & Not Mid-Range`):** `False` (`30D cVAL $0.00` | `30D cPOC $0.00` | `30D cVAH $0.00` | `VA Position`: `0.0%` | `Mid-Range`: `False`)
- **Pillar 3 (`8H Funding <= 0.0100%`):** `True` (`8H Funding`: `+0.0000%` | `4H OI Change`: `+0.00%`)
- **Pillar 4 (`4H Spot Delta > 0 BTC`):** `False` (`4H Spot Delta`: `+0.00 BTC` | `4H Perp Delta`: `+0.00 BTC`)
- **Pillar 5 (`15m Footprint 4-Gate Pass`):** `False` (`15m Active Delta`: `+10.00 BTC`)
- **Total Pillars True:** `1 / 5`

---

# TAB [0: SPOT SWING] | DATA-ONLY METRICS REPORT
**Retrieval Time (UTC):** `2026-11-09 00:28:42 UTC`  |  **Retrieval Time (MYT):** `2026-11-09 08:28:42 MYT (UTC+8)`
**Spot Price (BTCUSDT):** `$0.00`

## 1. SPOT SWING SCREENER METRICS & GATE BOOLEANS
- **Spot Swing Screener Evaluation Available:** `False`

---

# TAB [L: MASTER] | 8-FLAGSHIP DESK DATA-ONLY METRICS REPORT
**Retrieval Time (UTC):** `2026-11-09 00:28:42 UTC`  |  **Retrieval Time (MYT):** `2026-11-09 08:28:42 MYT (UTC+8)`
**Spot Price (BTCUSDT):** `$0.00`
**Desk Purpose & Scope:** `Single-screen 8-Flagship-Desk Telemetry Matrix (P, G, R, M, A, F, W, 0) & 4-Domain Readiness Overview. Keeps each strategy's reference entry, stop, and sizing calculations strictly unblended.`

## 1. 8-FLAGSHIP TOP-RIBBON DESK READINESS METRICS (`P, G, R, M, A, F, W, 0`)
- **Master Synthesis Evaluation Available:** `False`
