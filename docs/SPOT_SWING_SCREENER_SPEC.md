# TAB [0]: BTC Spot Swing Screening & Daily Liquidation Magnet Engine
## Daily Liquidation Magnet Protocol (Steps 1–4), Tight RRR >= 1:3 Money Management, 1D Macro Gate & Weekly Sweep/Reclaim

**Protocol Classification:** Primary Spot Swing Screener, Daily Liquidation Magnet Protocol & Alert Dispatcher  
**Target Asset & Mandate:** Bitcoin (`BTC-USD` / `BTCUSDT`) — Non-Leveraged Spot Swing Trading (3-day to 3-week holding horizon)  
**Core Law:** *"In a range-bound regime, immediate price pumps are driven by the mechanics of forced liquidations and positioning imbalances—not by fundamental news headlines. Trading the headline gets you trapped; trading the liquidation magnet gives you the edge."*  
**Terminal Integration:** Tab `[0]` (`[0: SPOT SWING]`, default startup desk) in the `BTC-USD Spot Swing Engine`  
**Hotkey Access:** Press **`0`** in the Live Rich Terminal HUD | CLI Flag: `--tab 0` or `--tab spot`  
**Master Command Desk:** Press **`L`** or **`M`** for Tab `[L]` (Master Supreme Command Center)  

---

## 1. Objective & Operational Scope

Tab `[0]` unifies the **Daily Liquidation Magnet Protocol** (Master Prompt 1 & Operating Protocol Prompt 2) with the **Closed-Bar BTC Spot Swing Screener** and **Tight Money Management (`RRR >= 1:3`)**:

1. **The Liquidation Magnet & Positioning Edge (Core Law):** Audits the nearest dense Short-Liquidation Cluster above price and Long-Liquidation Cluster below price alongside 24H Open Interest trend, 8H Perp Funding Rate, and Spot CVD vs. Perp CVD ("truth serum") to distinguish forced short-covering squeezes from genuine spot accumulation.
2. **Tight Money Management (`RRR >= 1:3` Mandate):** Enforces a hard minimum Reward-to-Risk ratio of **1:3 (`>= 3.0R`)** from entry to the upper Short-Liquidation Magnet against the hard structural invalidation stop. Automatically computes the **Maximum Allowable Entry Price for 1:3 RRR** ($E_{\max} = \frac{T + 3S}{4}$) so mid-range entries with poor payoff are automatically rejected (`Do Nothing`).
3. **The Regime Edge (Avoiding the Chop Tax):** Classifies `[Range / Possible Transition / Trend]` using 30–45D swing boundaries, 50-day MA (`SMA50` & `EMA50`), and daily `HH+HL` structure, paired with the 1D Macro Gate (`close > EMA50 > EMA200` and 20-period BBW 180D Rank $\le 30\%$).
4. **The Structural Liquidity Edge (Trading Absorption):** Enters only after sell-side stops below the Previous Week's Low (`PWL`) have been swept and price is reclaimed on above-average volume (`volume > SMA_vol(3)`).
5. **The Sizing & Tail-Risk Edge (Volatility-Adjusted Capital Protection):** Sizes unit exposure dynamically from an ATR-based invalidation stop, strictly enforcing a 1.0% equity risk budget and a hard 100% spot ceiling (zero leverage).

---

## 2. Core Modules & Mathematical Architecture

### Module A: Closed-Bar Data Ingestion & Hygiene (`spot_swing_engine.py`)
- **Feed Source:** Continuous 1H spot klines synthesized into UTC-aligned 4H bars + closed 1D daily bars.
- **Repainting Prevention:** Metrics are evaluated strictly on finalized, closed bars with successor proof (a bar is final only if a subsequent bar exists in the series).
- **Freshness Guard:** Suspends screening if the latest closed candle is stale, preventing calculations on lagging offline data.

### Module B: Macro Regime Gate (1D Horizon)
1. **Trend Baseline:**
   $$\text{trend\_pass} = (\text{close} > \text{EMA}_{50}) \land (\text{EMA}_{50} > \text{EMA}_{200})$$
2. **Volatility Squeeze:**
   Calculate 20-period Bollinger Band Width:
   $$\text{BBW} = \frac{\text{Upper Band} - \text{Lower Band}}{\text{SMA}_{20}} = \frac{4 \times \sigma_{20}}{\text{SMA}_{20}}$$
   Compute the rolling 180-day percentile rank of current BBW:
   $$\text{compression\_pass} = \text{percentile\_rank}_{180}(\text{BBW}) \le 0.30$$
3. **Macro Permission:**
   $$\text{macro\_approved} = \text{trend\_pass} \land \text{compression\_pass}$$
   If `False`, spot allocation is frozen at 100% Cash.

### Module C: Structural Liquidity Setup (4H Horizon) & Safety Guards
1. **Weekly Anchor Levels:** Evaluated on completed Monday-to-Sunday UTC calendar weeks (`PWL` and `PWH`).
2. **Sweep & Reclaim Detection:**
   - **Sweep:** Rolling 12-bar window (~48h) checks for low wick breaching below `PWL` (`low < PWL`). Tracks lowest sweep wick (`sweep_low`).
   - **Reclaim:** Most recently closed 4H candle closes strictly above `PWL` (`close > PWL`).
   - **Volume Confirmation:** Reclaim candle volume exceeds 3-period SMA of volume (`volume > SMA_vol(3)`).
3. **Signal Trigger:**
   $$\text{signal\_active} = \text{sweep\_detected} \land \text{reclaim\_confirmed} \land \text{volume\_confirmed}$$
4. **Pre-Flight Safety Guards (Liquidation Flush & Tell-Tale Sensor):**
   - **Liquidation Cascade Check (Tab 8 companion feed):** Checks whether an un-stabilized `EXTREME FLUSH` is in progress (`btc_liquidation_detector`).
   - **Tell-Tale Capitulation Sensor (Tab 9 companion check):** Checks whether an active 5x volume disruption dump printed without an orderly reclaim bar.

### Module D: Risk & Triple-Barrier Position Sizing (`compute_risk`)
1. **Invalidation Level ($P_{\text{stop}}$):**
   $$P_{\text{stop}} = \text{sweep\_low} - (0.5 \times \text{ATR}_{14})$$
   $$\text{Stop Distance} = P_{\text{entry}} - P_{\text{stop}}$$
2. **Volatility-Adjusted Allocation (with 100% Spot Ceiling):**
   $$\text{Position Size (BTC)} = \min\left(\frac{\text{Account Equity} \times 0.01}{\text{Stop Distance}}, \frac{\text{Account Equity}}{P_{\text{entry}}}\right)$$
3. **Triple-Barrier Targets & 1:3 RRR Geometry:**
   - **Barrier 1 (Stop Loss):** $P_{\text{stop}}$ (moved to $P_{\text{entry}}$ upon hitting TP1).
   - **Barrier 2a (Partial Take Profit):** $+2.0R = P_{\text{entry}} + 2 \times \text{Stop Distance}$ (Sell 50%, move stop to breakeven).
   - **Mandatory 3R Target:** $+3.0R = P_{\text{entry}} + 3 \times \text{Stop Distance}$.
   - **Barrier 2b (Structural Runner Target):** `PWH` / `Short-Liq Magnet`.
   - **Barrier 3 (Time Stop):** Maximum holding horizon of 10 trading days (60 closed 4H bars).

### Module E: State Persistence & Alert Dispatcher (`spot_swing_notifier.py`)
- **State Persistence:** Atomic write to `spot_swing_state.json` tracks trade status (`OPEN_FULL` $\rightarrow$ `TP1_HIT_RUNNER` $\rightarrow$ `CLOSED`), preventing duplicate alerts across restarts.

### Module F: Daily Liquidation Magnet Protocol (`compute_magnet_protocol`)
1. **Step 1 (Data Gathering & Positioning Audit):**
   - **Current BTC Price**, **50-Day MA (`SMA50` & `EMA50`)**, **30–45D Range High/Low & Range Pivot**.
   - **Short-Liq Magnet Above Price** & **Long-Liq Magnet Below Price**: Derived from `PWH`/`PWL`, 7D/14D/30D swing liquidity pools, and Volume Profile `cVAH`/`cVAL`, with optional manual CoinGlass 1M heatmap overrides via `protocol_context.json` or `SHORT_LIQ_MAGNET_USD` / `LONG_LIQ_MAGNET_USD`.
   - **24H Cumulative ForceOrders:** Live feed from companion `btc_liquidation_detector`.
   - **OI Trend (24H & 4H):** Classifies `Rising + Price Falling` (new shorts / squeeze fuel), `Rising + Price Rising` (new longs / trap risk), or `Falling` (covering / de-leveraging).
   - **8H Perp Funding Rate:** Classifies `Negative` (shorts paying / squeeze primed), `Neutral`, `Positive`, or `Strongly Positive` (crowded longs).
   - **Spot CVD Truth Serum:** Evaluates 4H & 24H Spot CVD vs. Perp CVD (`Confirming`, `Not confirming — Futures-driven`, or `Mixed`).
   - **Headline Filter:** Classifies news as `None significant`, `Structural / Delayed`, `Recurring Rumor`, or `Immediate Flow Event`.
2. **Step 2 (Regime Confirmation):**
   - Classifies `Range`, `Possible Transition`, or `Trend` based on 30–45D range position, 50-day MA oscillation, and daily `HH+HL` / `LH+LL` structure.
3. **Step 3 (Protocol Rules + Tight RRR 1:3 Money Management):**
   - Computes $\text{RRR}_{\text{magnet}} = \frac{P_{\text{short\_magnet}} - P_{\text{entry}}}{P_{\text{entry}} - P_{\text{stop}}}$ and maximum 3R entry $E_{\max} = \frac{P_{\text{short\_magnet}} + 3 P_{\text{stop}}}{4}$.
   - **Rule 1 (`Partial Profit into Magnet`):** Price near upper short-liq cluster + negative/near-zero funding + weak/flat Spot CVD $\rightarrow$ Hold existing longs, scale 30–50% into the magnet, do NOT chase.
   - **Rule 2 (`Reduce or Exit`):** Price swept into short-liq cluster, momentum exhausted, and price rejected below Range Pivot or 50-day MA $\rightarrow$ Reduce or exit spot longs immediately.
   - **Rule 3 (`Rare Add Consideration`):** Daily close above short-liq wall + rising Spot CVD + OI not collapsing $\rightarrow$ Consider adds on retest only if $\text{RRR} \ge 1:3$ holds.
   - **Rule 4 (`Hold`):** Swept lower liquidity & reclaimed with Spot confirmation and $\text{RRR}_{\text{magnet}} \ge 3.0\text{R}$ $\rightarrow$ Hold/enter spot long, scale 30–50% at magnet, move stop to breakeven.
   - **Rule 5 (`Do Nothing`):** All other conditions or any setup where $\text{RRR}_{\text{magnet}} < 3.0\text{R}$ $\rightarrow$ Sit in cash / do nothing and wait for pullback $\le E_{\max}$.
4. **Step 4 (Strict Structured Output):**
   - Rendered in Panel 4 of Tab `[0]` and exported in Section `0D` of the AI Telemetry Packet (`C` hotkey): `Regime`, `Key Levels`, `Positioning Snapshot`, `Headline Filter`, `Verdict`, `Confidence`, `Primary Reason`, `Invalidation`, and `Actionable Note`.

---

## 3. Terminal Navigation & Hotkeys

- **Press `0`**: Tab `[0: SPOT SWING]` (Daily Liquidation Magnet Protocol, 1D Macro Gate, 4H Weekly Anchors, RRR 1:3 Order Card).
- **Press `L` or `M`**: Tab `[L: MASTER]` (Master Synthesis & Supreme Command Center).
- **Press `1` through `9`**: Specialist Desks (Tactical Flow, Protocol v1.3, Macro Radar, Regime A–J, MM-BTC, Vol Cone, Gartley 222, SFP Trap, Exhaustion).
- **Press `C`**: Copy unified quantitative telemetry packet (including Section 0A–0D) to clipboard and `Downloads/BTC_AI_DATA_PACKET_LATEST.md`.
