# BTC SWING ENGINE | GLOBAL DATA-ONLY TELEMETRY PACKET ([C: AI PACKET])
**Retrieval Time (UTC):** `2026-11-08 15:08:13 UTC`  |  **Retrieval Time (MYT):** `2026-11-08 23:08:13 MYT (UTC+8)`
**Spot Price (BTCUSDT):** `$76,074.00`
**Output Specification:** `DATA-ONLY (Raw Measurements, Reference Formulas & True/False Conditions Only — Zero Interpretive Prose)`

---

# BTC TREND-PULLBACK v1.0 | DATA-ONLY REPORT (RESEARCH / PAPER MODE)
**STATUS:** `UNVALIDATED`  |  **Retrieval Time (UTC):** `2026-11-08 15:08:13 UTC`  |  **Retrieval Time (MYT):** `2026-11-08 23:08:13 MYT (UTC+8)`
**Spot Price (BTCUSDT):** `$76,074.00`

## 1. DAILY (1D)
- **Completed 1D Candle Window:** `Open 2026-11-07 00:00 UTC -> Close 2026-11-08 00:00 UTC`
- **Last Completed 1D Close:** `$75,867.59` (Open `$75,844.00`, High `$76,249.99`, Low `$75,571.08`)
- **Daily SMA50:** `$81,949.60`
- **Daily SMA200:** `$73,240.19` (20D Prior SMA200: `$72,534.48`)
- **Daily SMA200 20D Slope (`SMA200_now - SMA200_20d_ago`):** `$+705.71`
- **Close vs SMA200 (`Close - SMA200`):** `$+2,627.40` (`+3.59%`)
- **Close vs SMA50 (`Close - SMA50`):** `$-6,082.01` (`-7.42%`)
- **Close > SMA200:** `True`
- **Close > SMA50:** `False`
- **SMA200 Rising Over 20D (`SMA200_now > SMA200_20d_ago`):** `True`

## 2. 4H TREND METRICS
- **Completed 4H Candle Window:** `Open 2026-11-08 08:00 UTC -> Close 2026-11-08 12:00 UTC`
- **Last Completed 4H Close:** `$75,981.09`
- **4H EMA50:** `$77,367.94`
- **4H EMA200:** `$80,238.99`
- **4H ATR14:** `$681.13`
- **4H EMA50 - EMA200:** `$-2,871.05`
- **4H EMA50 Now vs 6 Bars Ago:** Now `$77,367.94` vs 6 Bars Ago `$77,768.93` (`-400.99` USD)
- **Last 4H Close vs 4H EMA50 (`Close - EMA50`):** `$-1,386.85` (`-2.0361 ATR` / `-2.04 ATR`)
- **Last 4H Close vs 4H EMA200 (`Close - EMA200`):** `$-4,257.90` (`-6.2512 ATR` / `-6.25 ATR`)
- **4H EMA50 > 4H EMA200:** `False`
- **4H EMA50 Rising Over 6 Bars (`EMA50_now > EMA50_6bars_ago`):** `False`
- **Last 4H Close > 4H EMA200:** `False`

## 3. PULLBACK ZONE
- **Pullback Zone Formula:** `Zone Lower = 4H EMA50 - 0.50 * 4H ATR14` | `Zone Upper = 4H EMA50 + 0.25 * 4H ATR14` | `Max Extension = 4H EMA50 + 1.00 * 4H ATR14`
- **Zone Lower (`EMA50 - 0.50 * ATR14`):** `$77,027.38`
- **Zone Upper (`EMA50 + 0.25 * ATR14`):** `$77,538.22`
- **Max Extension (`EMA50 + 1.00 * ATR14`):** `$78,049.07`
- **Spot Minus Zone Lower (`Spot - Zone Lower`):** `$-953.38` (`-1.3997 ATR` / `-1.40 ATR`)
- **Spot Minus Zone Upper (`Spot - Zone Upper`):** `$-1,464.22` (`-2.1497 ATR` / `-2.15 ATR`)
- **Last Completed 4H Candle OHLC:** Open `$75,975.64`, High `$76,037.07`, Low `$75,803.75`, Close `$75,981.09`
- **Candle Low < Zone Lower:** `True`
- **Candle Low > Zone Upper:** `False`
- **Recovery Candle Sub-Conditions (Last Completed 4H Candle):**
  - `Candle Low >= Zone Lower`: `False`
  - `Candle Low <= Zone Upper`: `True`
  - `Candle Close > 4H EMA50`: `False`
  - `Candle Close > Candle Open`: `True`
  - `Candle Close <= 4H EMA50 + 1.00 * 4H ATR14`: `True`
  - `All 5 Recovery Sub-Conditions True`: `False`

## 4. REFERENCE LEVELS (Reference calculation if entered at $77,436.05. Not an order.)
- **Reference Entry Zone (`[4H EMA50, 4H EMA50 + 0.10 * 4H ATR14]`):** `$77,367.94 - $77,436.05`
- **Reference Entry Price Used (`4H EMA50 + 0.10 * 4H ATR14`):** `$77,436.05`
- **Distance From Spot To Reference Entry (`Spot - Reference Entry`):** `$-1,362.05` (`-1.76%`)
- **Stop Level (`min(low of last 5 completed 4H bars) - 0.25 * 4H ATR14`):** `$75,400.80` (5-Bar Lowest Low `$75,571.08` - Buffer `$170.28`)
- **Stop Distance From Reference Entry (`Reference Entry $77,436.05 - Stop Level $75,400.80`):** `$2,035.25` (`2.9880 ATR` / `2.99 ATR`)
- **Stop Distance >= 0.75 ATR:** `True`
- **Stop Distance <= 3.00 ATR:** `True`
- **Reference Simulation Equity:** `$100,000.00`
- **Risk Budget (`0.50%` of Reference Equity):** `$500.00`
- **Position Size:** `0.22079 BTC`
- **Position Notional (`Position Size * Reference Entry $77,436.05`):** `$17,097.11`
- **Computed Price Risk (`Position Size * Stop Distance $2,035.25`):** `$449.36` (`$2,035.25/BTC`)
- **Fee & Slippage Buffer (`0.10%` Entry Fee + `0.10%` Exit Fee + `0.05%` Entry Slippage + `0.05%` Exit Slippage):** `$50.62` (`$229.26/BTC`: Entry Fee `$17.10` + Exit Fee `$16.65` + Entry Slippage `$8.55` + Exit Slippage `$8.32`)
- **Total Estimated Risk (`Computed Price Risk + Fee & Slippage Buffer`):** `$499.98` (`$2,264.51/BTC`)
- **Total Estimated Risk <= Risk Budget (`$499.98 <= $500.00`):** `True`

## 5. EXIT RULE INPUTS
- **Position Mode Setting:** `CASH`
- **Completed 4H Candle (t-1) (`Open 2026-11-08 04:00 UTC -> Close 2026-11-08 08:00 UTC`):** Close `$75,975.64` vs 4H EMA50 `$77,424.54` (`-1,448.90` USD) | `Close < 4H EMA50`: `True`
- **Completed 4H Candle (t) (`Open 2026-11-08 08:00 UTC -> Close 2026-11-08 12:00 UTC`):** Close `$75,981.09` vs 4H EMA50 `$77,367.94` (`-1,386.85` USD) | `Close < 4H EMA50`: `True`
- **Consecutive Completed 4H Closes Below 4H EMA50:** `18`
- **Completed 1D Candle (t-1) (`Open 2026-11-06 00:00 UTC -> Close 2026-11-07 00:00 UTC`):** Close `$75,844.00` vs 1D SMA200 `$73,242.53` (`+2,601.47` USD) | `Close < 1D SMA200`: `False`
- **Completed 1D Candle (t) (`Open 2026-11-07 00:00 UTC -> Close 2026-11-08 00:00 UTC`):** Close `$75,867.59` vs 1D SMA200 `$73,240.19` (`+2,627.40` USD) | `Close < 1D SMA200`: `False`
- **Consecutive Completed 1D Closes Below 1D SMA200:** `0`
- **Spot <= Stop Level (`$76,074.00 <= $75,400.80`):** `False`

## 6. DATA INTEGRITY
- **Data Retrieval Time (UTC):** `2026-11-08 15:08:13 UTC`
- **Data Retrieval Time (MYT):** `2026-11-08 23:08:13 MYT (UTC+8)`
- **Data Integrity Pass:** `True`
- **Completed 1D Candles Available:** `254` | **Last Completed 1D Status:** `LAST CLOSE (Open 2026-11-07 00:00 UTC -> Close 2026-11-08 00:00 UTC)` | **Forming 1D Candle Excluded:** `True` (`2026-11-08 00:00 UTC`)
- **Completed 4H Candles Available:** `299` | **Last Completed 4H Status:** `LAST CLOSE (Open 2026-11-08 08:00 UTC -> Close 2026-11-08 12:00 UTC)` | **Forming 4H Candle Excluded:** `True` (`2026-11-08 12:00 UTC`)

---

# TAB [M: MAGNET] | DATA-ONLY METRICS REPORT
**Retrieval Time (UTC):** `2026-11-08 15:08:13 UTC`  |  **Retrieval Time (MYT):** `2026-11-08 23:08:13 MYT (UTC+8)`
**Spot Price (BTCUSDT):** `$76,074.00` (`24H Change: +0.42%`)

## 1. LIQUIDATION GRAVITATIONAL HORIZON
- **Upper Liquidation Cluster (Short Liquidations):** `$78,657.99` (`+3.40%` / `$+2,583.99` from Spot) | Volume: `$318.21M`
- **Center Spot Price:** `$76,074.00`
- **Lower Liquidation Cluster (Long Liquidations):** `$74,525.12` (`-2.04%` / `$-1,548.88` from Spot) | Volume: `$351.40M`
- **Upper-to-Lower Cluster Weight Ratio:** `0.91x` (`Higher Weight Side`: `LOWER`)

## 2. DERIVATIVES & VOLATILITY INPUTS
- **Annualized Perpetual Funding Rate:** `+4.09%/yr`
- **4H Open Interest Delta:** `+0.15%`
- **24H Classification Label:** `Range`

## 3. 7 INTERNAL CONDITION BOOLEANS (TRUE/FALSE)
- **Rule 1 (`Clear Magnet Present`):** `True` (`Magnet BELOW: $74,525 (-2.0%, $351M)`)
- **Rule 2 (`Open-Interest Confirmation`):** `True` (`OI velocity supportive (+0.1% 4h delta)`)
- **Rule 3 (`Funding Non-Contradictory`):** `True` (`Borrow rate calm (+4.1%/yr carry)`)
- **Rule 4 (`Regime Conduciveness`):** `True` (`Market in Range mode (conducive to magnet sweep)`)
- **Rule 5 (`Spot Flow & Structure Alignment`):** `True` (`Structure intact (24h change: +0.42%, 4h Spot CVD: +74.8 BTC)`)
- **Rule 6 (`Not Already Swept`):** `True` (`Target cluster intact and unswept`)
- **Rule 7 (`Conviction Threshold`):** `True` (`6/6 internal filters passed cleanly`)
- **Conditions 1-6 True Count:** `6 / 6`

---

# TAB [G: GROK FLOW] | DATA-ONLY METRICS REPORT
**Retrieval Time (UTC):** `2026-11-08 15:08:13 UTC`  |  **Retrieval Time (MYT):** `2026-11-08 23:08:13 MYT (UTC+8)`
**Spot Price (BTCUSDT):** `$76,074.00`

## 1. 00:00 UTC ANCHORED VWAP & STANDARD DEVIATION BANDS
- **00:00 UTC Anchored VWAP:** `$75,877.07`
- **1.0 SD Dispersion (`Sigma`):** `$85.22`
- **Spot Minus VWAP (`Spot - VWAP`):** `$+196.93` (`+0.26%` | Stretch Z-Score: `+2.31 SD`)
- **+2.0 SD Upper Band:** `$76,047.52` | **Spot > +2.0 SD:** `True`
- **+1.0 SD Upper Band:** `$75,962.30` | **Spot > +1.0 SD:** `True`
- **-1.0 SD Lower Band:** `$75,791.85` | **Spot < -1.0 SD:** `False`
- **-2.0 SD Lower Band:** `$75,706.63` | **Spot < -2.0 SD:** `False`
- **Spot Inside [-1.0 SD, +1.0 SD] Band:** `False`

## 2. DAILY & INTRADAY MOVING AVERAGES & SESSION EXTREMES
- **1H EMA9 / 1H EMA21:** `$75,972.21` / `$75,928.32` | **1H EMA9 > 1H EMA21:** `True`
- **1D EMA50:** `$79,529.56` | **Spot Minus 1D EMA50:** `$-3,455.56` (`-4.35%`) | **Spot > 1D EMA50:** `False`
- **1D SMA200:** `$73,240.19` | **Spot Minus 1D SMA200:** `$+2,833.81` (`+3.87%`) | **Spot > 1D SMA200:** `True`
- **Current Day High / Low:** `$76,200.00` / `$75,655.76`
- **Previous Day High / Low:** `$76,249.99` / `$75,571.08`

## 3. DERIVATIVES POSITIONING & LIQUIDATION CLUSTERS
- **Open Interest:** `96,128.31 BTC` (`$7,309,231,329`)
- **OI Change (`1H / 4H`):** `+0.07%` / `+0.15%` | **4H OI Change > 0:** `True`
- **8H Perpetual Funding Rate:** `+0.0037%` | **Funding Rate <= 0.0100%:** `True`
- **Top Participant L/S Ratio:** `1.87` (`65.2%` Long / `34.8%` Short)
- **Global Account L/S Ratio:** `3.06` | **Global L/S >= 2.00:** `True`
- **Overhead Short Liquidation Cluster:** `$76,120.93` (`$234.0M`)
- **Downside Long Liquidation Cluster:** `$75,067.83` (`$329.0M`)

## 4. MULTI-HORIZON CVD & COINBASE PREMIUM
- **24H CVD (`Spot vs Perp`):** Spot `+206.20 BTC` | Perp `+1,024.70 BTC` | `Spot CVD 24H > 0`: `True` | `Spot CVD 24H > Perp CVD 24H`: `False`
- **4H CVD (`Spot vs Perp`):** Spot `+74.80 BTC` | Perp `+113.40 BTC` | `Spot CVD 4H > 0`: `True`
- **15m CVD (`Spot vs Perp`):** Spot `-1.70 BTC` | Perp `+42.90 BTC` | `Spot CVD 15m > 0`: `False`
- **Coinbase Premium (`USD / % / Z-Score`):** `$-111.70` (`-0.1468%` | `Z = +0.03`) | **Coinbase Premium > 0:** `False`

---

# TAB [R: SSRN RESEARCH] | DATA-ONLY METRICS REPORT
**Retrieval Time (UTC):** `2026-11-08 15:08:13 UTC`  |  **Retrieval Time (MYT):** `2026-11-08 23:08:13 MYT (UTC+8)`
**Spot Price (BTCUSDT):** `$76,074.00`

## 1. EMPIRICAL FACTOR & GATE METRICS
- **1D MACD Gate Pass (`1D MACD > Signal or Hist > 0`):** `False`
- **20-Day Annualized Realized Volatility (%):** `39.21%`
- **20-Day Realized Variance:** `0.1537`
- **20-Day Log-Return Skewness:** `-0.80`
- **25% Volatility-Target Reference Weight (%):** `63.8%`
- **8H Equivalent ATR14 (`ATR14_4H * sqrt(2)`):** `$648.97`
- **2.5x 8H ATR Reference Stop Distance:** `$1,622.44`
- **Annualized Perpetual Funding Rate (%/yr):** `+4.09%/yr`
- **Annualized Funding <= 30.0%/yr:** `True`
- **Round-Trip Friction Assumption:** `18.0 bps` (`Cost Hurdle Pass`: `True`)
- **Order Book Imbalance (`1% Depth Ratio`):** `+3.3%`
- **4H Spot CVD Delta:** `+74.83 BTC`
- **MVRV Proxy Ratio (`Spot / (0.62 * 1D SMA200)`):** `1.68`
- **SOPR Proxy Ratio:** `1.0200`

## 2. 5 SSRN MODEL CONDITION BOOLEANS
- **Multi-Timeframe Trend Following (`Mesicek & Vojtko (SSRN 5748642)` | `1H Execution / 1D Trend Filter`):** Condition Pass: `False` | Measured Value: `1D: -1513/-1218 | 1H: +22/-9`
- **Ensemble Donchian + Volatility Target (`Zarattini, Pagani & Barbon (SSRN 5209907)` | `Daily / Multi-Horizon (5-360 Days)`):** Condition Pass: `True` | Measured Value: `20D Vol: 39.2% | Target Vol: 25.0%`
- **Volatility-Adaptive Multi-Horizon Trend (`Karassavidis et al. (SSRN 5821842)` | `8-Hour Candles`):** Condition Pass: `True` | Measured Value: `8H ATR(14): $649 | Stop Buffer: -$1,622`
- **Funding Rate Exhaustion Gate (`Chan (SSRN 5292305)` | `8H Funding Settlement Intervals`):** Condition Pass: `True` | Measured Value: `Ann: +4.09%/yr | Ceiling: 30.0%`
- **Cost-Aware Alpha Hurdle Filter (`Bysik & Slepaczuk (SSRN 6795938)` | `Hourly / Multi-Hour`):** Condition Pass: `True` | Measured Value: `Fee Hurdle: 18 bps | Min Edge: >= +0.36%`

## 3. 5 EMPIRICAL DOMAIN TELEMETRY
- **01. Market Microstructure & Order Flow:** `OBI: +3.3% | 4H CVD: +74.8 BTC` (Core Metrics: `Order Book Imbalance (OBI), Cumulative Volume Delta (CVD), Spread Dynamics`)
- **02. Time-Series Momentum & Technical Rules:** `1D: CHOP (RANGING) | 4H: BEAR / CHOP | 1H: BULL CROSS` (Core Metrics: `Variable Moving Averages (VMA), Time-Series Momentum (TSMOM), Breakout Ensembles`)
- **03. Systematic Factor Pricing (Liu-Tsyvinski):** `Var: 0.1537 | 20D Skew: -0.80` (Core Metrics: `Crypto Market Factor (MKT_crypto), Size/Illiquidity Premium, Downside Risk Semi-Variance`)
- **04. On-Chain Structural Metrics:** `MVRV: 1.68 | SOPR: 1.02` (Core Metrics: `MVRV Ratio, Spent Output Profit Ratio (SOPR), Entity-Adjusted Realized Price`)
- **05. Alternative Data & Machine Learning Hurdles:** `Hurdle: 18 bps (+0.18%)` (Core Metrics: `Search Volume Index (SVI), Cost-Aware Gradient Boosted Trees, Regime Classifiers`)

---

# TAB [P: STRUCTURE] | DATA-ONLY METRICS REPORT
**Retrieval Time (UTC):** `2026-11-08 15:08:13 UTC`  |  **Retrieval Time (MYT):** `2026-11-08 23:08:13 MYT (UTC+8)`
**Spot Price (BTCUSDT):** `$76,074.00`

## 1. DAILY SWING STRUCTURE & KEY SHELVES (SLSP v1.0)
- **Nearest Support Shelf Center:** `$75,067.83` (Band: `$74,888.00 - $75,545.67`)
- **Spot Minus Support Center (`Spot - Support`):** `$+1,006.17` (`+1.34%`)
- **Support Strength / Touches:** `4/5` | Touches: `28`
- **Support Is Round Number:** `True` | **Support Is HVN:** `False`
- **Nearest Resistance Shelf Center:** `$76,120.93` (Band: `$76,000.00 - $76,325.98`)
- **Resistance Center Minus Spot (`Resistance - Spot`):** `$+46.93` (`+0.06%`)
- **Resistance Strength / Touches:** `3/5` | Touches: `45`

## 2. REFERENCE LEVELS (Reference calculation if entered at $76,074.00. Not an order.)
- **Reference Entry Price:** `$76,074.00`
- **Reference Stop Level:** `$74,814.93`
- **Stop Distance (`Reference Entry - Stop Level`):** `$1,259.07`
- **1.5R Reference Level (`Entry + 1.5 * Stop Distance`):** `$77,962.60`
- **2.5R Reference Level (`Entry + 2.5 * Stop Distance`):** `$79,221.68`
- **Distance to Overhead Resistance in R (`Obstacle R`):** `0.04R`
- **Clearance >= 1.50R (`Obstacle R >= 1.50`):** `False`

## 3. DAILY & 4H 3-EMA METRICS
- **1D EMA20 / EMA50 / EMA200:** `$78,632.78` / `$79,529.56` / `$74,883.92`
- **1D EMA200 5-Day Slope (%):** `+8.850%`
- **1D ADX(14):** `18.90` | **ADX(14) >= 20.0:** `False`
- **4H EMA9 / EMA20 / EMA50:** `$76,009.08` / `$76,385.23` / `$77,317.72`
- **Spot Inside 4H [EMA20, EMA50] Value Band:** `True`
- **4H Wick Condition Met (Last 3 Closed 4H Bars):** `False`
- **4H Close > 4H EMA9:** `True`
- **Positioning Sub-Conditions Met Count:** `2 / 3`

## 4. LIQUIDATION FLUSH & VOLUME CLIMAX SENSORS
- **1H OI Delta (%):** `+0.07%`
- **15m Relative Volume (`RelVol vs 20-bar SMA`):** `0.40x` | **15m RelVol >= 5.0x:** `False`
- **5m Relative Volume (`RelVol vs 20-bar SMA`):** `0.00x` | **5m RelVol >= 5.0x:** `False`
- **Volume Climax Interlock Active:** `False`
- **Liquidated USD (`15m / 1h / 4h / 24h`):** `$990,358` / `$1,345,573` / `$1,502,022` / `$1,502,022`
- **24H Liquidation Multiple:** `0.05x`
- **Reference Zone (`$75,000 - $78,000`) Distance to Lower / Upper:** `+1.00%` / `-2.89%`

---

# TAB [B: PATTERNS] | DATA-ONLY METRICS REPORT
**Retrieval Time (UTC):** `2026-11-08 15:08:13 UTC`  |  **Retrieval Time (MYT):** `2026-11-08 23:08:13 MYT (UTC+8)`
**Spot Price (BTCUSDT):** `$76,074.00`

## 1. PRIMARY GEOMETRIC STRUCTURE METRICS (4H & 1H)
- **Primary Structure Name:** `Head and Shoulders`
- **Timeframe:** `4h`
- **Geometric Fit Score (`0.00 - 1.00`):** `0.72`
- **Neckline Price:** `$80,939.54`
- **Spot Minus Neckline (`Spot - Neckline`):** `$-4,865.54` (`-6.01%`)
- **Boundary Level (`Floor / Roof`):** `$84,898.00`
- **Spot Minus Boundary (`Spot - Boundary`):** `$-8,824.00` (`-10.39%`)
- **4H & 1H Multi-Timeframe Aligned:** `False`
- **Spot > Neckline:** `False`
- **Spot > Boundary:** `False`

## 2. SCANNED 4H & 1H STRUCTURE CANDIDATES
- **Candidate Count:** `0`

---

# TAB [F: FOOTPRINT] | DATA-ONLY METRICS REPORT
**Retrieval Time (UTC):** `2026-11-08 15:08:13 UTC`  |  **Retrieval Time (MYT):** `2026-11-08 23:08:13 MYT (UTC+8)`
**Spot Price (BTCUSDT):** `$76,074.00`

## 1. 15-MINUTE INTRA-CANDLE FOOTPRINT METRICS
- **Active 15m Bar Net Delta:** `-1.67 BTC`
- **Previous Completed 15m Bar Net Delta:** `-14.37 BTC`
- **Active Battle Zone Price:** `$76,050.00`
- **Stacked Imbalances Count:** `0`

## 2. 4 GATE CONDITION BOOLEANS (TRUE/FALSE)
- **Gate 1 (`Macro/Tactical Level Tap`):** `True` (Level: `30D Macro Support HVN` at `$75,930.71`)
- **Gate 2 (`Positioning Filter`):** `True`
- **Gate 3 (`Wick Absorption`):** `True`
- **Gate 4 (`15m Net Delta Flip`):** `False`
- **All Gates True:** `False`

## 3. REFERENCE LEVELS (Reference calculation if entered at $76,074.00. Not an order.)
- **Reference Entry Price:** `$76,074.00`
- **Reference Stop Level:** `$0.00`
- **Stop Distance (`|Entry - Stop|`):** `$0.00`
- **1:2 Reference Level:** `$0.00`
- **1:3 Reference Level:** `$0.00`

---

# TAB [W: WATERFALL] | DATA-ONLY METRICS REPORT
**Retrieval Time (UTC):** `2026-11-08 15:08:13 UTC`  |  **Retrieval Time (MYT):** `2026-11-08 23:08:13 MYT (UTC+8)`
**Spot Price (BTCUSDT):** `$76,074.00`

## 1. 5-PILLAR CONDITION BOOLEANS & RAW INPUTS
- **Pillar 1 (`Confluence Score >= 50.0`):** `False` (Confluence Score: `30.00`)
- **Pillar 2 (`Value Area Edge & Not Mid-Range`):** `False` (`30D cVAL $79,100.54` | `30D cPOC $81,686.46` | `30D cVAH $84,689.46` | `VA Position`: `-54.2%` | `Mid-Range`: `True`)
- **Pillar 3 (`8H Funding <= 0.0100%`):** `True` (`8H Funding`: `+0.0037%` | `4H OI Change`: `+0.15%`)
- **Pillar 4 (`4H Spot Delta > 0 BTC`):** `True` (`4H Spot Delta`: `+74.83 BTC` | `4H Perp Delta`: `+113.35 BTC`)
- **Pillar 5 (`15m Footprint 4-Gate Pass`):** `False` (`15m Active Delta`: `-1.67 BTC`)
- **Total Pillars True:** `2 / 5`

---

# TAB [0: SPOT SWING] | DATA-ONLY METRICS REPORT
**Retrieval Time (UTC):** `2026-11-08 15:08:13 UTC`  |  **Retrieval Time (MYT):** `2026-11-08 23:08:13 MYT (UTC+8)`
**Spot Price (BTCUSDT):** `$76,074.00`

## 1. SPOT SWING SCREENER METRICS & GATE BOOLEANS
- **Composite Confluence Score (`0 - 100`):** `0.0`
- **Gate 1 (`Macro Filter`):** `False`
- **Gate 2 (`Structure / Location`):** `False`
- **Gate 3 (`Derivatives / Funding`):** `False`
- **Gate 4 (`Spot Order Flow`):** `False`
- **All Screener Gates True:** `False`

## 2. REFERENCE LEVELS (Reference calculation if entered at $76,074.00. Not an order.)
- **Reference Entry Price:** `$76,074.00`
- **Reference Stop Level:** `$74,172.15`
- **Stop Distance (`Reference Entry - Stop Level`):** `$1,901.85`
- **Reference Level 1 (`TP1`):** `$0.00`
- **Reference Level 2 (`TP2`):** `$0.00`
- **Reference Level 3 (`3R`):** `$0.00`

---

# TAB [L: MASTER] | DATA-ONLY METRICS REPORT
**Retrieval Time (UTC):** `2026-11-08 15:08:13 UTC`  |  **Retrieval Time (MYT):** `2026-11-08 23:08:13 MYT (UTC+8)`
**Spot Price (BTCUSDT):** `$76,074.00`

## 1. MULTI-DESK ALIGNMENT METRICS
- **Master Alignment Score (`0.0 - 100.0`):** `66.4`
- **Alignment Score >= 70.0:** `False`

## 2. 4-TIER HIERARCHY SCORES
- **Tier:** Score `0.0/100` | `Score >= 60.0`: `False` | Primary Metric: ``
- **Tier:** Score `0.0/100` | `Score >= 60.0`: `False` | Primary Metric: ``
- **Tier:** Score `0.0/100` | `Score >= 60.0`: `False` | Primary Metric: ``
- **Tier:** Score `0.0/100` | `Score >= 60.0`: `False` | Primary Metric: ``

## 3. SUB-DESK NUMERIC SCORES & PASS BOOLEANS
- **Desk ():** Score `0.0/100` | `Score >= 60.0`: `False` | Metric: ``
- **Desk ():** Score `0.0/100` | `Score >= 60.0`: `False` | Metric: ``
- **Desk ():** Score `0.0/100` | `Score >= 60.0`: `False` | Metric: ``
- **Desk ():** Score `0.0/100` | `Score >= 60.0`: `False` | Metric: ``
- **Desk ():** Score `0.0/100` | `Score >= 60.0`: `False` | Metric: ``
- **Desk ():** Score `0.0/100` | `Score >= 60.0`: `False` | Metric: ``
- **Desk ():** Score `0.0/100` | `Score >= 60.0`: `False` | Metric: ``
- **Desk ():** Score `0.0/100` | `Score >= 60.0`: `False` | Metric: ``
- **Desk ():** Score `0.0/100` | `Score >= 60.0`: `False` | Metric: ``

## 4. REFERENCE LEVELS (Reference calculation if entered at $76,074.00. Not an order.)
- **Reference Spot Price:** `$76,074.00`
- **Reference Hard Stop Level:** `$73,801.69`
- **Reference Upper Level 1:** `$78,732.41`
- **Reference Upper Level 2:** `$81,971.00`
