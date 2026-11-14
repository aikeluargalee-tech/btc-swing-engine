# BTC SWING ENGINE | GLOBAL DATA-ONLY TELEMETRY PACKET ([C: AI PACKET])
**Retrieval Time (UTC):** `2026-11-14 15:38:52 UTC`  |  **Retrieval Time (MYT):** `2026-11-14 23:38:52 MYT (UTC+8)`
**Spot Price (BTCUSDT):** `$65,268.01`
**Output Specification:** `DATA-ONLY (Raw Measurements, Reference Formulas & True/False Conditions Only — Zero Interpretive Prose)`

---

# BTC TREND-PULLBACK v1.0 | DATA-ONLY REPORT (RESEARCH / PAPER MODE)
**STATUS:** `UNVALIDATED`  |  **Retrieval Time (UTC):** `2026-11-14 15:38:52 UTC`  |  **Retrieval Time (MYT):** `2026-11-14 23:38:52 MYT (UTC+8)`
**Spot Price (BTCUSDT):** `$65,268.01`

## 1. DAILY (1D)
- **Completed 1D Candle Window:** `Open 2026-11-13 00:00 UTC -> Close 2026-11-14 00:00 UTC`
- **Last Completed 1D Close:** `$68,314.00` (Open `$71,460.00`, High `$71,514.01`, Low `$67,568.00`)
- **Daily SMA50:** `$80,624.41`
- **Daily SMA200:** `$73,091.58` (20D Prior SMA200: `$72,942.35`)
- **Daily SMA200 20D Slope (`SMA200_now - SMA200_20d_ago`):** `$+149.23`
- **Close vs SMA200 (`Close - SMA200`):** `$-4,777.58` (`-6.54%`)
- **Close vs SMA50 (`Close - SMA50`):** `$-12,310.41` (`-15.27%`)
- **Close > SMA200:** `False`
- **Close > SMA50:** `False`
- **SMA200 Rising Over 20D (`SMA200_now > SMA200_20d_ago`):** `True`

## 2. 4H TREND METRICS
- **Completed 4H Candle Window:** `Open 2026-11-14 08:00 UTC -> Close 2026-11-14 12:00 UTC`
- **Last Completed 4H Close:** `$67,272.79`
- **4H EMA50:** `$72,930.73`
- **4H EMA200:** `$77,544.01`
- **4H ATR14:** `$1,143.15`
- **4H EMA50 - EMA200:** `$-4,613.28`
- **4H EMA50 Now vs 6 Bars Ago:** Now `$72,930.73` vs 6 Bars Ago `$74,306.22` (`-1,375.49` USD)
- **Last 4H Close vs 4H EMA50 (`Close - EMA50`):** `$-5,657.94` (`-4.9494 ATR` / `-4.95 ATR`)
- **Last 4H Close vs 4H EMA200 (`Close - EMA200`):** `$-10,271.22` (`-8.9850 ATR` / `-8.98 ATR`)
- **4H EMA50 > 4H EMA200:** `False`
- **4H EMA50 Rising Over 6 Bars (`EMA50_now > EMA50_6bars_ago`):** `False`
- **Last 4H Close > 4H EMA200:** `False`

## 3. PULLBACK ZONE
- **Pullback Zone Formula:** `Zone Lower = 4H EMA50 - 0.50 * 4H ATR14` | `Zone Upper = 4H EMA50 + 0.25 * 4H ATR14` | `Max Extension = 4H EMA50 + 1.00 * 4H ATR14`
- **Zone Lower (`EMA50 - 0.50 * ATR14`):** `$72,359.15`
- **Zone Upper (`EMA50 + 0.25 * ATR14`):** `$73,216.52`
- **Max Extension (`EMA50 + 1.00 * ATR14`):** `$74,073.88`
- **Spot Minus Zone Lower (`Spot - Zone Lower`):** `$-7,091.14` (`-6.2032 ATR` / `-6.20 ATR`)
- **Spot Minus Zone Upper (`Spot - Zone Upper`):** `$-7,948.51` (`-6.9532 ATR` / `-6.95 ATR`)
- **Last Completed 4H Candle OHLC:** Open `$67,165.42`, High `$67,523.05`, Low `$66,966.79`, Close `$67,272.79`
- **Candle Low < Zone Lower:** `True`
- **Candle Low > Zone Upper:** `False`
- **Recovery Candle Sub-Conditions (Last Completed 4H Candle):**
  - `Candle Low >= Zone Lower`: `False`
  - `Candle Low <= Zone Upper`: `True`
  - `Candle Close > 4H EMA50`: `False`
  - `Candle Close > Candle Open`: `True`
  - `Candle Close <= 4H EMA50 + 1.00 * 4H ATR14`: `True`
  - `All 5 Recovery Sub-Conditions True`: `False`

## 4. REFERENCE LEVELS (Reference calculation if entered at $73,045.04. Not an order.)
- **Reference Entry Zone (`[4H EMA50, 4H EMA50 + 0.10 * 4H ATR14]`):** `$72,930.73 - $73,045.04`
- **Reference Entry Price Used (`4H EMA50 + 0.10 * 4H ATR14`):** `$73,045.04`
- **Distance From Spot To Reference Entry (`Spot - Reference Entry`):** `$-7,777.03` (`-10.65%`)
- **Stop Level (`min(low of last 5 completed 4H bars) - 0.25 * 4H ATR14`):** `$66,170.21` (5-Bar Lowest Low `$66,456.00` - Buffer `$285.79`)
- **Stop Distance From Reference Entry (`Reference Entry $73,045.04 - Stop Level $66,170.21`):** `$6,874.83` (`6.0139 ATR` / `6.01 ATR`)
- **Stop Distance >= 0.75 ATR:** `True`
- **Stop Distance <= 3.00 ATR:** `False`
- **Reference Simulation Equity:** `$100,000.00`
- **Risk Budget (`0.50%` of Reference Equity):** `$500.00`
- **Position Size:** `0.07058 BTC`
- **Position Notional (`Position Size * Reference Entry $73,045.04`):** `$5,155.52`
- **Computed Price Risk (`Position Size * Stop Distance $6,874.83`):** `$485.23` (`$6,874.83/BTC`)
- **Fee & Slippage Buffer (`0.10%` Entry Fee + `0.10%` Exit Fee + `0.05%` Entry Slippage + `0.05%` Exit Slippage):** `$14.75` (`$208.82/BTC`: Entry Fee `$5.16` + Exit Fee `$4.67` + Entry Slippage `$2.58` + Exit Slippage `$2.34`)
- **Total Estimated Risk (`Computed Price Risk + Fee & Slippage Buffer`):** `$499.98` (`$7,083.65/BTC`)
- **Total Estimated Risk <= Risk Budget (`$499.98 <= $500.00`):** `True`

## 5. EXIT RULE INPUTS
- **Position Mode Setting:** `CASH`
- **Completed 4H Candle (t-1) (`Open 2026-11-14 04:00 UTC -> Close 2026-11-14 08:00 UTC`):** Close `$67,165.42` vs 4H EMA50 `$73,161.66` (`-5,996.24` USD) | `Close < 4H EMA50`: `True`
- **Completed 4H Candle (t) (`Open 2026-11-14 08:00 UTC -> Close 2026-11-14 12:00 UTC`):** Close `$67,272.79` vs 4H EMA50 `$72,930.73` (`-5,657.94` USD) | `Close < 4H EMA50`: `True`
- **Consecutive Completed 4H Closes Below 4H EMA50:** `54`
- **Completed 1D Candle (t-1) (`Open 2026-11-12 00:00 UTC -> Close 2026-11-13 00:00 UTC`):** Close `$71,460.00` vs 1D SMA200 `$73,136.87` (`-1,676.87` USD) | `Close < 1D SMA200`: `True`
- **Completed 1D Candle (t) (`Open 2026-11-13 00:00 UTC -> Close 2026-11-14 00:00 UTC`):** Close `$68,314.00` vs 1D SMA200 `$73,091.58` (`-4,777.58` USD) | `Close < 1D SMA200`: `True`
- **Consecutive Completed 1D Closes Below 1D SMA200:** `2`
- **Spot <= Stop Level (`$65,268.01 <= $66,170.21`):** `True`

## 6. DATA INTEGRITY
- **Data Retrieval Time (UTC):** `2026-11-14 15:38:52 UTC`
- **Data Retrieval Time (MYT):** `2026-11-14 23:38:52 MYT (UTC+8)`
- **Data Integrity Pass:** `True`
- **Completed 1D Candles Available:** `499` | **Last Completed 1D Status:** `LAST CLOSE (Open 2026-11-13 00:00 UTC -> Close 2026-11-14 00:00 UTC)` | **Forming 1D Candle Excluded:** `True` (`2026-11-14 00:00 UTC`)
- **Completed 4H Candles Available:** `499` | **Last Completed 4H Status:** `LAST CLOSE (Open 2026-11-14 08:00 UTC -> Close 2026-11-14 12:00 UTC)` | **Forming 4H Candle Excluded:** `True` (`2026-11-14 12:00 UTC`)

---

# TAB [M: MAGNET] | DATA-ONLY METRICS REPORT
**Retrieval Time (UTC):** `2026-11-14 15:38:52 UTC`  |  **Retrieval Time (MYT):** `2026-11-14 23:38:52 MYT (UTC+8)`
**Spot Price (BTCUSDT):** `$65,268.01` (`24H Change: -5.27%`)

## 1. 5-REGIME RADAR DIAGNOSIS & MAJORITY VOTING
- **Active Market Regime:** `Range / Liquidation Magnet` (ID: `RANGE_LIQUIDATION_MAGNET`)
- **Majority Voting Score:** `3/4` (`3/4 Observations true`)
- **Regime Diagnosis:** `Positioning imbalance and forced liquidations dominate`
- **Conflicted Signal Demoted to Mixed:** `False`
- **Verified On-Exchange Positioning Observations:**
  * `Defined range (6.23% width) & ATR compressed 74.4%`: `True`
  * `Spot CVD neutral/balanced (Ratio -0.08)`: `False`
  * `Positioning crowded (L/S 1.85, funding +0.0041%/8h)`: `True`
  * `Clear liquidation clusters active above and below price`: `True`

## 2. LIQUIDATION GRAVITATIONAL HORIZON & DUAL-LADDER DEPTH
- **Upper Liquidation Cluster (Short Liquidations):** `$76,334.44` (`+16.96%` / `$+11,066.43` from Spot) | Volume: `$193.80M`
- **Center Spot Price:** `$65,268.01`
- **Lower Liquidation Cluster (Long Liquidations):** `$64,093.19` (`-1.80%` / `$-1,174.82` from Spot) | Volume: `$350.00M`
- **Immediate Tier (100x) Imbalance Ratio:** `1.81x` ($350.0M Lower vs $193.8M Upper)
- **Total Ladder (10x-100x) Imbalance Ratio:** `1.79x` ($775.0M Lower vs $433.8M Upper)
- **Dominant Pull Direction:** `LOWER`

## 3. LIQUIDATION SWEEP CONFIRMATION ENGINE (LSCE)
- **LSCE State:** `[UNTESTED]`
- **Cluster Tested:** `Lower Longs ($64,093)`
- **Sweep Depth Pct:** `+1.80%`
- **Reclaim Target Level:** `$64,093.19`
- **Spot Absorption Readout:** `Pending`
- **LSCE Action status:** `Lower pool ($64,093) is +1.80% away and untested. Maintain cash reserve.`

## 4. INVIOLABLE RISK DIRECTIVES & CAPITAL SIZING
- **reported Spot Sizing:** `0.50x` (Range / Liquidation Magnet: Stand Aside or Selective (0.50x))
- **Capital Rotation Directive:** `Remain USDT`
- **Entry Instruction:** `Price oscillating in range. pending liquidation sweep confirmation before full allocation.`
- **Structural Invalidation Stop:** `$64,936.53` (`0.51%` from Spot)
- **Disaster Hard Stop (Below 200 SMA & 25x Shelf):** `$62,413.12` (`4.37%` from Spot)
- **Risk Budget Compliance Pass (<= 4.5%):** `True`

## 5. DERIVATIVES & VOLATILITY INPUTS
- **Annualized Perpetual Funding Rate:** `+4.53%/yr`
- **4H Open Interest Delta:** `+1.02%`
- **24H Classification Label:** `TrendDown`

## 6. 7 INTERNAL CONDITION BOOLEANS (TRUE/FALSE)
- **Rule 1 (`Clear Magnet Present`):** `True` (`Magnet BELOW: $64,093 (-1.8%, $350M)`)
- **Rule 2 (`Open-Interest Confirmation`):** `True` (`OI velocity supportive (+1.0% 4h delta)`)
- **Rule 3 (`Funding Non-Contradictory`):** `True` (`Borrow rate calm (+4.5%/yr carry)`)
- **Rule 4 (`Regime Conduciveness`):** `True` (`Market in TrendDown mode (conducive to magnet sweep)`)
- **Rule 5 (`Spot Flow & Structure Alignment`):** `True` (`Structure intact (24h change: -5.27%, 4h Spot CVD: -1084.4 BTC)`)
- **Rule 6 (`Not Already Swept`):** `True` (`Target cluster intact and unswept`)
- **Rule 7 (`Conviction Threshold`):** `True` (`6/6 internal filters passed cleanly`)
- **Conditions 1-6 True Count:** `6 / 6`

## 7. B1 vs B2 DATA INTEGRITY RECONCILIATION AUDIT
- **Reconciliation status:** `PASS`
- **Execution Authorization:** `AUTHORIZED`
- **Prescribed Capital Sizing:** `0.50x` (EXECUTION AUTHORIZED)
- **Portfolio Rotation Directive:** `Remain USDT`
- **Target Capital Allocation:** `Range / Liquidation Magnet: Stand Aside or Selective (0.50x)`
- **Mandatory Module Verification:**
  * `Module A (Ladder Math Consistency)`: `PASS` (B2 Internal Ladder Math Consistent: Total ($775.0M) >= Imm ($350.0M).)
  * `Module B (Funding Carry Normalization)`: `PASS` (Normalized 8H Carry: B1=+0.0100%/8h | B2=+0.0041%/8h. Baseline Calm.)
  * `Module C (Cluster Geometry & Horizon)`: `PASS` (Cluster Geometry Aligned within MACRO_HORIZON (>1.5%).)
  * `Module D (LSCE Sweep Proof & Rotation)`: `PASS` (LSCE State Aligned: [UNTESTED].)
  * `Module E (Snapshot Synchronization)`: `PASS` (Snapshots Synchronized (0.0m delta <= 15.0m).)

### Discrepancy & Reconciliation Table
| Metric | B1 Value | B2 Value | Difference | Severity | Explanation |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Lower Ladder Math Consistency | Total: $520.0M | Total: $775.0M | Valid (Total >= Imm) | `INFO` | Cumulative 10x-100x ladder correctly encompasses immediate 100x component. |
| Total Ladder Imbalance Ratio | 1.65x | 1.79x | +0.14x (Confluent) | `INFO` | Both engines confirm downside liquidation skew (>1.50x). |
| Funding Rate Normalization | +0.0100%/8h (+10.95%/yr) | +0.0041%/8h (+4.53%/yr) | 6.42%/yr delta | `INFO` | Both feeds confirm calm/neutral carry within +0.0100%/8h baseline. |
| Lower Magnet Target Geometry | $64,288.99 | $64,093.19 | $195.80 | `INFO` | Cluster horizons reconciled. |
| LSCE Sweep Confirmation State | UNTESTED | [UNTESTED] | Aligned | `INFO` | Both engines confirm current sweep state. |
| Snapshot Synchronization | 2026-11-14 15:38:52 UTC | 2026-11-14 15:38:52 UTC | 0.0m delta (Synchronized) | `INFO` | Both telemetry feeds retrieved within acceptable synchronization window. |

---

# TAB [G: GROK FLOW] | DATA-ONLY METRICS REPORT
**Retrieval Time (UTC):** `2026-11-14 15:38:52 UTC`  |  **Retrieval Time (MYT):** `2026-11-14 23:38:52 MYT (UTC+8)`
**Spot Price (BTCUSDT):** `$65,268.01`

## 1. 00:00 UTC ANCHORED VWAP & STANDARD DEVIATION BANDS
- **00:00 UTC Anchored VWAP:** `$66,873.12`
- **1.0 SD Dispersion (`Sigma`):** `$723.17`
- **Spot Minus VWAP (`Spot - VWAP`):** `$-1,605.11` (`-2.40%` | Stretch Z-Score: `-2.22 SD`)
- **+2.0 SD Upper Band:** `$68,319.46` | **Spot > +2.0 SD:** `False`
- **+1.0 SD Upper Band:** `$67,596.29` | **Spot > +1.0 SD:** `False`
- **-1.0 SD Lower Band:** `$66,149.94` | **Spot < -1.0 SD:** `True`
- **-2.0 SD Lower Band:** `$65,426.77` | **Spot < -2.0 SD:** `True`
- **Spot Inside [-1.0 SD, +1.0 SD] Band:** `False`

## 2. DAILY & INTRADAY MOVING AVERAGES & SESSION EXTREMES
- **1H EMA9 / 1H EMA21:** `$66,616.66` / `$67,381.87` | **1H EMA9 > 1H EMA21:** `False`
- **1D EMA50:** `$77,701.21` | **Spot Minus 1D EMA50:** `$-12,433.20` (`-16.00%`) | **Spot > 1D EMA50:** `False`
- **1D SMA200:** `$73,091.58` | **Spot Minus 1D SMA200:** `$-7,823.57` (`-10.70%`) | **Spot > 1D SMA200:** `False`
- **Current Day High / Low:** `$68,446.21` / `$65,066.66`
- **Previous Day High / Low:** `$71,514.01` / `$67,568.00`

## 3. DERIVATIVES POSITIONING & LIQUIDATION CLUSTERS
- **Open Interest:** `97,335.82 BTC` (`$6,355,289,034`)
- **OI Change (`1H / 4H`):** `+0.73%` / `+1.02%` | **4H OI Change > 0:** `True`
- **8H Perpetual Funding Rate:** `+0.0041%` | **Funding Rate <= 0.0100%:** `True`
- **Top Participant L/S Ratio:** `1.87` (`65.2%` Long / `34.8%` Short)
- **Global Account L/S Ratio:** `3.01` | **Global L/S >= 2.00:** `True`
- **Overhead Short Liquidation Cluster:** `$65,575.31` (`$234.0M`)
- **Downside Long Liquidation Cluster:** `$64,742.09` (`$329.0M`)

## 4. MULTI-HORIZON CVD & COINBASE PREMIUM
- **24H CVD (`Spot vs Perp`):** Spot `-2,392.80 BTC` | Perp `-10,375.50 BTC` | `Spot CVD 24H > 0`: `False` | `Spot CVD 24H > Perp CVD 24H`: `True`
- **4H CVD (`Spot vs Perp`):** Spot `-1,084.40 BTC` | Perp `-4,484.70 BTC` | `Spot CVD 4H > 0`: `False`
- **15m CVD (`Spot vs Perp`):** Spot `-143.80 BTC` | Perp `+130.70 BTC` | `Spot CVD 15m > 0`: `False`
- **Coinbase Premium (`USD / % / Z-Score`):** `$-23.11` (`-0.0354%` | `Z = +2.80`) | **Coinbase Premium > 0:** `False`

---

# TAB [R: SSRN RESEARCH] | DATA-ONLY METRICS REPORT
**Retrieval Time (UTC):** `2026-11-14 15:38:52 UTC`  |  **Retrieval Time (MYT):** `2026-11-14 23:38:52 MYT (UTC+8)`
**Spot Price (BTCUSDT):** `$65,268.01`

## 1. EMPIRICAL FACTOR & GATE METRICS
- **1D MACD Gate Pass (`1D MACD > Signal or Hist > 0`):** `False`
- **20-Day Annualized Realized Volatility (%):** `45.05%`
- **20-Day Realized Variance:** `0.2029`
- **20-Day Log-Return Skewness:** `-0.30`
- **25% Volatility-Target Reference Weight (%):** `55.5%`
- **8H Equivalent ATR14 (`ATR14_4H * sqrt(2)`):** `$1,998.68`
- **2.5x 8H ATR Reference Stop Distance:** `$4,996.71`
- **Annualized Perpetual Funding Rate (%/yr):** `+4.53%/yr`
- **Annualized Funding <= 30.0%/yr:** `True`
- **Round-Trip Friction Assumption:** `18.0 bps` (`Cost Hurdle Pass`: `True`)
- **Order Book Imbalance (`1% Depth Ratio`):** `+26.6%`
- **4H Spot CVD Delta:** `-1084.38 BTC`
- **MVRV Proxy Ratio (`Spot / (0.62 * 1D SMA200)`):** `1.44`
- **SOPR Proxy Ratio:** `1.0200`

## 2. 5 SSRN MODEL CONDITION BOOLEANS
- **Multi-Timeframe Trend Following (`Mesicek & Vojtko (SSRN 5748642)` | `1H Execution / 1D Trend Filter`):** Condition Pass: `False` | Measured Value: `1D: -3068/-2061 | 1H: -832/-745`
- **Ensemble Donchian + Volatility Target (`Zarattini, Pagani & Barbon (SSRN 5209907)` | `Daily / Multi-Horizon (5-360 Days)`):** Condition Pass: `True` | Measured Value: `20D Vol: 45.0% | Target Vol: 25.0%`
- **Volatility-Adaptive Multi-Horizon Trend (`Karassavidis et al. (SSRN 5821842)` | `8-Hour Candles`):** Condition Pass: `True` | Measured Value: `8H ATR(14): $1,999 | Stop Buffer: -$4,997`
- **Funding Rate Exhaustion Gate (`Chan (SSRN 5292305)` | `8H Funding Settlement Intervals`):** Condition Pass: `True` | Measured Value: `Ann: +4.53%/yr | Ceiling: 30.0%`
- **Cost-Aware Alpha Hurdle Filter (`Bysik & Slepaczuk (SSRN 6795938)` | `Hourly / Multi-Hour`):** Condition Pass: `True` | Measured Value: `Fee Hurdle: 18 bps | Min Edge: >= +0.36%`

## 3. 5 EMPIRICAL DOMAIN TELEMETRY
- **01. Market Microstructure & Order Flow:** `OBI: +26.6% | 4H CVD: -1084.4 BTC` (Core Metrics: `Order Book Imbalance (OBI), Cumulative Volume Delta (CVD), Spread Dynamics`)
- **02. Time-Series Momentum & Technical Rules:** `1D: CHOP (RANGING) | 4H: BEAR / CHOP | 1H: BEAR CHOP` (Core Metrics: `Variable Moving Averages (VMA), Time-Series Momentum (TSMOM), Breakout Ensembles`)
- **03. Systematic Factor Pricing (Liu-Tsyvinski):** `Var: 0.2029 | 20D Skew: -0.30` (Core Metrics: `Crypto Market Factor (MKT_crypto), Size/Illiquidity Premium, Downside Risk Semi-Variance`)
- **04. On-Chain Structural Metrics:** `MVRV: 1.44 | SOPR: 1.02` (Core Metrics: `MVRV Ratio, Spent Output Profit Ratio (SOPR), Entity-Adjusted Realized Price`)
- **05. Alternative Data & Machine Learning Hurdles:** `Hurdle: 18 bps (+0.18%)` (Core Metrics: `Search Volume Index (SVI), Cost-Aware Gradient Boosted Trees, Regime Classifiers`)

---

# TAB [P: STRUCTURE] | DATA-ONLY METRICS REPORT
**Retrieval Time (UTC):** `2026-11-14 15:38:52 UTC`  |  **Retrieval Time (MYT):** `2026-11-14 23:38:52 MYT (UTC+8)`
**Spot Price (BTCUSDT):** `$65,268.01`

## 1. 5-REGIME RADAR DIAGNOSIS & MACRO SIZING
- **Active Market Regime:** `Range / Liquidation Magnet` (ID: `RANGE_LIQUIDATION_MAGNET`)
- **Majority Voting Score:** `3/4`
- **Regime Diagnosis:** `Positioning imbalance and forced liquidations dominate`
- **Macro Sizing Factor:** `0.50x`
- **Capital Rotation Directive:** `Remain USDT`
- **Macro Hard-Lock Cash Active:** `False`

## 2. DAILY SWING STRUCTURE & LIQUIDATION-BACKED KEY SHELVES (SLSP v1.0)
- **Daily Market Bias:** `UNCLEAR`
- **Confluence Score:** `25/100`
- **position State:** `SCANNING`
- **Nearest Support Shelf Center:** `$64,742.09` (Band: `$64,166.00 - $65,118.00`)
- **Spot Minus Support Center (`Spot - Support`):** `$+525.92` (`+0.81%`)
- **Support Strength / Touches:** `5/5` | Touches: `58`
- **Support Is Round Number:** `True` | **Support Is HVN:** `False`
- **Support Liquidation Cluster Tag:** `Lower Long Pool ($350.0M • -1.8%)`
- **Support Liquidation Volume USD:** `$350,000,000.00`
- **Nearest Resistance Shelf Center:** `$65,575.31` (Band: `$65,390.99 - $65,744.60`)
- **Resistance Center Minus Spot (`Resistance - Spot`):** `$+307.30` (`+0.47%`)
- **Resistance Strength / Touches:** `3/5` | Touches: `45`
- **Resistance Liquidation Cluster Tag:** `None`
- **Resistance Liquidation Volume USD:** `$0.00`

## 3. LIQUIDATION GRAVITATIONAL HORIZON & LSCE SWEEP ENGINE
- **Dominant Gravitational Pull:** `LOWER`
- **Immediate Tier (100x) Imbalance Ratio:** `1.81x`
- **Total Ladder (10x-100x) Imbalance Ratio:** `1.79x`
- **Upper Liquidation Magnet Cluster:** `$76,334.44` (`+16.97%` from Spot) | Volume: `$193.80M`
- **Lower Liquidation Magnet Cluster:** `$64,085.32` (`-1.80%` from Spot) | Volume: `$350.00M`
- **LSCE Sweep State:** `[UNTESTED]`
- **LSCE Cluster Tested:** `Lower Longs ($64,085)`
- **LSCE Action status:** `Lower pool ($64,085) is +1.80% away and untested. Maintain cash reserve.`

## 4. REFERENCE LEVELS & DUAL INVIOLABLE STOPS (Reference calculation if entered at $65,268.01)
- **Reference Entry Price:** `$65,268.01`
- **Structural Stop Loss (1H Close):** `$64,936.53` (`0.50%` from Spot)
- **Disaster Hard Stop (Below 200 SMA & 25x Shelf):** `$62,405.46` (`4.37%` from Spot)
- **Risk Budget Compliance Pass (<= 4.5%):** `True`
- **Stop Distance (`Reference Entry - Structural Stop`):** `$1,224.47`
- **1.5R Reference Level (`Entry + 1.5 * Stop Distance`):** `$67,104.71`
- **2.5R Reference Level (`Entry + 2.5 * Stop Distance`):** `$68,329.18`
- **Distance to Overhead Resistance in R (`Obstacle R`):** `0.25R`
- **Clearance >= 1.50R (`Obstacle R >= 1.50`):** `False`
- **Sized Position (Macro Sized 0.50x):** `0.3063 BTC` (`$19,988.33` notional)

## 5. DAILY & 4H 3-EMA METRICS
- **1D EMA20 / EMA50 / EMA200:** `$75,024.86` / `$77,701.21` / `$76,527.63`
- **1D EMA200 5-Day Slope (%):** `-55.500%`
- **1D ADX(14):** `28.30` | **ADX(14) >= 20.0:** `True`
- **4H EMA9 / EMA20 / EMA50:** `$67,852.47` / `$69,817.53` / `$72,629.44`
- **Spot Inside 4H [EMA20, EMA50] Value Band:** `False`
- **4H Wick Condition Met (Last 3 Closed 4H Bars):** `False`
- **4H Close > 4H EMA9:** `False`
- **Positioning Sub-Conditions Met Count:** `3 / 3`

## 6. LIQUIDATION FLUSH & VOLUME CLIMAX SENSORS
- **1H OI Delta (%):** `+0.73%`
- **15m Relative Volume (`RelVol vs 20-bar SMA`):** `1.43x` | **15m RelVol >= 5.0x:** `False`
- **5m Relative Volume (`RelVol vs 20-bar SMA`):** `0.00x` | **5m RelVol >= 5.0x:** `False`
- **Volume Climax Interlock Active:** `False`
- **Liquidated USD (`15m / 1h / 4h / 24h`):** `$990,358` / `$1,345,573` / `$1,502,022` / `$1,502,022`
- **24H Liquidation Multiple:** `0.05x`
- **Reference Zone (`$75,000 - $78,000`) Distance to Lower / Upper:** `+1.00%` / `-2.89%`

## 7. UPSTREAM DATA INTEGRITY RECONCILIATION GATE
- **Reconciliation status:** `PASS`
- **Execution Authorization:** `AUTHORIZED`
- **Trading Status:** `EXECUTION AUTHORIZED`
- **Prescribed Capital Allocation:** `0.50x` (`Range / Liquidation Magnet: Stand Aside or Selective (0.50x)`)
- **Portfolio Rotation Directive:** `Remain USDT`
- **Module A (Ladder Math):** `PASS` | **Module D (LSCE Proof):** `PASS`

---

# TAB [F: FOOTPRINT] | DATA-ONLY METRICS REPORT
**Retrieval Time (UTC):** `2026-11-14 15:38:52 UTC`  |  **Retrieval Time (MYT):** `2026-11-14 23:38:52 MYT (UTC+8)`
**Spot Price (BTCUSDT):** `$65,268.01`

## 1. 15-MINUTE INTRA-CANDLE FOOTPRINT METRICS
- **Active 15m Bar Net Delta:** `-143.79 BTC`
- **Previous Completed 15m Bar Net Delta:** `-295.88 BTC`
- **Active Battle Zone Price:** `$65,300.00`
- **Stacked Imbalances Count:** `0`

## 2. 4 GATE CONDITION BOOLEANS (TRUE/FALSE)
- **Gate 1 (`Macro/Tactical Level Tap`):** `False` (Level: `` at `$0.00`)
- **Gate 2 (`Positioning Filter`):** `True`
- **Gate 3 (`Wick Absorption`):** `False`
- **Gate 4 (`15m Net Delta Flip`):** `False`
- **All Gates True:** `False`

## 3. REFERENCE LEVELS (Reference calculation if entered at $65,268.01. Not an order.)
- **Reference Entry Price:** `$65,268.01`
- **Reference Stop Level:** `$0.00`
- **Stop Distance (`|Entry - Stop|`):** `$0.00`
- **1:2 Reference Level:** `$0.00`
- **1:3 Reference Level:** `$0.00`

---

# TAB [W: WATERFALL] | DATA-ONLY METRICS REPORT
**Retrieval Time (UTC):** `2026-11-14 15:38:52 UTC`  |  **Retrieval Time (MYT):** `2026-11-14 23:38:52 MYT (UTC+8)`
**Spot Price (BTCUSDT):** `$65,268.01`

## 1. 5-PILLAR CONDITION BOOLEANS & RAW INPUTS
- **Pillar 1 (`Confluence Score >= 50.0`):** `False` (Confluence Score: `35.00`)
- **Pillar 2 (`Value Area Edge & Not Mid-Range`):** `False` (`30D cVAL $75,560.74` | `30D cPOC $81,675.41` | `30D cVAH $83,328.02` | `VA Position`: `-132.5%` | `Mid-Range`: `False`)
- **Pillar 3 (`8H Funding <= 0.0100%`):** `True` (`8H Funding`: `+0.0041%` | `4H OI Change`: `+1.02%`)
- **Pillar 4 (`4H Spot Delta > 0 BTC`):** `False` (`4H Spot Delta`: `-1084.38 BTC` | `4H Perp Delta`: `-4484.69 BTC`)
- **Pillar 5 (`15m Footprint 4-Gate Pass`):** `False` (`15m Active Delta`: `-143.79 BTC`)
- **Total Pillars True:** `1 / 5`

---

# TAB [0: SPOT SWING] | DATA-ONLY METRICS REPORT
**Retrieval Time (UTC):** `2026-11-14 15:38:52 UTC`  |  **Retrieval Time (MYT):** `2026-11-14 23:38:52 MYT (UTC+8)`
**Spot Price (BTCUSDT):** `$65,268.01`

## 1. SPOT SWING SCREENER METRICS & GATE BOOLEANS
- **Composite Confluence Score (`0 - 100`):** `0.0`
- **Gate 1 (`Macro Filter`):** `False`
- **Gate 2 (`Structure / Location`):** `False`
- **Gate 3 (`Derivatives / Funding`):** `False`
- **Gate 4 (`Spot Order Flow`):** `False`
- **All Screener Gates True:** `False`

## 2. REFERENCE LEVELS (Reference calculation if entered at $65,268.01. Not an order.)
- **Reference Entry Price:** `$65,268.01`
- **Reference Stop Level:** `$63,636.31`
- **Stop Distance (`Reference Entry - Stop Level`):** `$1,631.70`
- **Reference Level 1 (`TP1`):** `$0.00`
- **Reference Level 2 (`TP2`):** `$0.00`
- **Reference Level 3 (`3R`):** `$0.00`

---

# TAB [L: MASTER] | 8-FLAGSHIP DESK DATA-ONLY METRICS REPORT
**Retrieval Time (UTC):** `2026-11-14 15:38:52 UTC`  |  **Retrieval Time (MYT):** `2026-11-14 23:38:52 MYT (UTC+8)`
**Spot Price (BTCUSDT):** `$65,268.01`
**Desk Purpose & Scope:** `Single-screen 8-Flagship-Desk Telemetry Matrix (P, G, R, M, A, F, W, 0) & 4-Domain Readiness Overview. Keeps each strategy's reference entry, stop, and sizing calculations strictly unblended.`

## 1. 8-FLAGSHIP TOP-RIBBON DESK READINESS METRICS (`P, G, R, M, A, F, W, 0`)
- **8-Desk Readiness Index (`0.0 - 100.0`):** `25.0`
- **Readiness Index >= 70.0:** `False`
- **Hard Veto Active Across Desks:** `True`

## 2. 4 ORTHOGONAL DOMAIN PILLAR MEASUREMENTS
- **D1: Crash/Veto Guards [P,W] (`Tell-Tale 5x & NTZ 8A–8F`):** Pass=`False` | Armed=`False` | Telemetry: `LOCKED: Desk [W/4] Config I (Bear Trend); INITIATIVE`
- **D2: 1D/4H Trend [A,0,W] (`1D SMA200 & 4H EMA50/200`):** Pass=`False` | Armed=`False` | Telemetry: `1D Below 200SMA ($73,092) -> 0.50% Cap`
- **D3: Shelves & Magnets [P,M] (`SLSP Shelf & Liq Magnets`):** Pass=`False` | Armed=`False` | Telemetry: `Shelf $64,742 | Mag ↑$76,334 ↓$64,093`
- **D4: Flow & Triggers [G,F,R,A] (`CVD, Footprint & Triggers`):** Pass=`False` | Armed=`False` | Telemetry: `4H Spot -1,084 BTC | Pending Pullback & Trigger`

## 3. 8-FLAGSHIP DESK TELEMETRY MATRIX (`P, G, R, M, A, F, W, 0`)
- **[P] Structure:** Pass=`False` | Constructive=`False` | State=`UNCLEAR • 3EMA:WEAK_BEAR` | Telemetry=`Sup:$64,742 Res:$65,575 | TT:PASS`
- **[G] Grok Flow:** Pass=`False` | Constructive=`False` | State=`VWAP $66,873 (-2.22SD)` | Telemetry=`4H S:-1,084 P:-4,485 BTC | CPI:-0.035%`
- **[R] SSRN Alpha:** Pass=`False` | Constructive=`True` | State=`4/5 Models • 1D MACD:False` | Telemetry=`20D RVol:45.0% | VolTarget:56% | MVRV:1.44`
- **[M] Magnet:** Pass=`True` | Constructive=`True` | State=`6/6 Rules • Pull 0.55x (LOWER)` | Telemetry=`Up:$76,334 (+17.0%) | Low:$64,093 (-1.8%)`
- **[A] BTC Strategy:** Pass=`False` | Constructive=`False` | State=`1D:False • 4H:False • Rec:False` | Telemetry=`Zone $72,359–$73,217 | Stop $66,170`
- **[F] Footprint:** Pass=`False` | Constructive=`False` | State=`15m Δ:-143.8 BTC` | Telemetry=`Delta -143.8 BTC | State: OBSERVING`
- **[W] Waterfall:** Pass=`False` | Constructive=`False` | State=`2/5 Gates • Config I` | Telemetry=`Conf 35/100 | VA -132% | NTZ:NO`
- **[0] Spot Swing:** Pass=`False` | Constructive=`False` | State=`1D:standby • R:R 7.23R` | Telemetry=`50D:$80,248 | RRR:7.23R (req >=3.0R)`

## 4. INDEPENDENT STRATEGY REFERENCE LEVELS (Reference calculation if entered at $65,268.01. Not an order.)
- **Reference Spot Price:** `$65,268.01`
- **Desk [A] Trend-Pullback v1.0 Reference:** Entry `$73,045.04` | Stop `$66,170.21` (`-$6,874.83` / `6.01 ATR`) | Size `0.070580 BTC` | Reconciled Risk `$499.98`
- **Desk [P] SLSP v1.0 Reference:** Entry `$65,268.01` | Stop `$64,043.54` | Level 1 (`1.5R`) `$67,104.71` | Size `0.3063 BTC`
- **Spot Holder Reference Hard Stop Level:** `$62,801.30`
- **Spot Holder Reference Upper Level 1:** `$68,785.04`
- **Spot Holder Reference Upper Level 2:** `$81,196.01`
