# TAB [S3]: Gartley 222 Harmonics & 5-Strategy Spot Swing Confluence Desk
## Mathematical Microstructure, Dual-Horizon Macro Trend & Fibonacci Harmonic Execution

**Protocol Classification:** Dual-Horizon Confluence Radar & Harmonic Pattern Execution Desk  
**Target Asset & Mandate:** Bitcoin (`BTC-USD` / `BTCUSDT`) — Non-Leveraged Spot Swing Trading  
**Terminal Integration:** Special Tab `[S3]` (`[S3: GARTLEY 222 & 5-STRATEGY CONFLUENCE]`) in the `BTC-USD Spot Swing Engine`  
**Hotkey Access:** Press **`8`**, **`G`**, or **`g`** in the Live Rich Terminal HUD | CLI Flag: `--tab s3`  
**Cloud Deployment:** GitHub Actions (`.github/workflows/btc_scanner.yml`) on `aikeluargalee-tech/btc-spot-verdict-bot`  
**Telegram Bot:** `@Gartleyy_bot` (Chat ID: `1273979711`) with On-Demand `/now` Google Apps Script Webhook  

---

## 1. Executive Summary & Architecture

The **Gartley 222 & 5-Strategy Spot Swing Desk (Tab [S3])** is a complete, production-grade port of the TradingView Pine Script (`btc_5strategy_plus_gartley_merged.pine`). It unites 5 classic trend and mean-reversion quantitative strategies with H.M. Gartley's 1935 Fibonacci harmonic pattern recognition across two complementary horizons:

1. **1D Daily Macro Trend**: Acts as the overarching structural regime gate (establishing whether Bitcoin is in a verified macro bull run, holding trend, or undergoing broad distribution).
2. **4H Tactical Swing**: Evaluates localized exhaustion, channel breakouts, and Fibonacci reversal clusters to trigger high-probability entry and exit execution.
3. **Dual Telegram Bot Ecosystem**: Operates both as a local real-time analytical desk in the `btc_swing_engine` terminal and as an autonomous cloud bot running on GitHub Actions that delivers rich dual-chart (4H + 1D) swipeable albums to `@Gartleyy_bot` and responds instantly to on-demand `/now` user requests via Google Apps Script.

---

## 2. Mathematical Formulations & Indicator Strategy Suite

Tab `[S3]` evaluates seven distinct quantitative models simultaneously on both horizons:

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                              TAB [S3] 5-STRATEGY + GARTLEY ARCHITECTURE                                │
├────────────────────────────────┬────────────────────────────────┬──────────────────────────────────────┤
│ S1. 20-bar Donchian Breakout   │ S2. 200 SMA Trend Gatekeeper   │ S3. EMA 20 / 50 Moving Avg Cross     │
│     Channel Trend Following    │     Macro Cycle Bull/Bear Filter │   Dynamic Intermediate Momentum      │
│     High[1].rolling(20).max()  │     Close > SMA200 Gate        │     Golden Cross / Death Cross       │
├────────────────────────────────┼────────────────────────────────┼──────────────────────────────────────┤
│ S4. 14-period Wilder RSI       │ S5. 2-Sigma Bollinger Bands    │ S6. Bullish Gartley 222 (L-H-L-H-L)  │
│     30 Oversold / 50 Reclaim   │     20 SMA ± 2σ Lower Sweep    │     X < B < D < A Fibonacci PRZ       │
│     Momentum Mean-Reversion    │     Exhaustion Bounce Trigger  │     Entry: D Reversal Point          │
├────────────────────────────────┴────────────────────────────────┼──────────────────────────────────────┤
│ S7. Bearish Gartley 222 (H-L-H-L-H)                             │ Multi-Timeframe Confluence Synthesis │
│     X > B > D > A Fibonacci PRZ                                 │ 1D Macro Gate + 4H Tactical Triggers │
│     Exit / Hedge: Profit Taking into USDT                       │ Telegram Swipeable Dual-Chart Albums │
└─────────────────────────────────────────────────────────────────┴──────────────────────────────────────┘
```

### 2.1. S1: 20-Bar Donchian Channel Breakout
- **Entry (`s1E`)**: $Close_t > \max(High_{t-20 \dots t-1})$
- **Exit (`s1X`)**: $Close_t < \min(Low_{t-20 \dots t-1})$
- **State Machine**: Stays in `HOLD` until trailing 20-bar channel low is violated.

### 2.2. S2: 200 SMA Macro Gatekeeper
- **Indicator**: $SMA_{200}(t) = \frac{1}{200} \sum_{i=0}^{199} Close_{t-i}$
- **Entry (`s2E`)**: $Close_{t-1} \le SMA_{200}(t-1)$ and $Close_t > SMA_{200}(t)$
- **Exit (`s2X`)**: $Close_{t-1} \ge SMA_{200}(t-1)$ and $Close_t < SMA_{200}(t)$
- **State Machine**: Authorizes bullish swing continuation as long as spot price remains above the institutional 200-day/200-period moving average.

### 2.3. S3: EMA 20 / 50 Dynamic Trend Cross
- **Indicators**:
  $$EMA_k(t) = Close_t \times \alpha_k + EMA_k(t-1) \times (1 - \alpha_k), \quad \alpha_k = \frac{2}{k+1}$$
- **Entry (`s3E`)**: $EMA_{20}(t-1) \le EMA_{50}(t-1)$ and $EMA_{20}(t) > EMA_{50}(t)$
- **Exit (`s3X`)**: $EMA_{20}(t-1) \ge EMA_{50}(t-1)$ and $EMA_{20}(t) < EMA_{50}(t)$

### 2.4. S4: 14-Period Wilder RSI Reversal
- **Formula**: $RSI = 100 - \frac{100}{1 + RS}$, where $RS = \frac{EMA(Gains, 14)}{EMA(Losses, 14)}$
- **Entry (`s4E`)**: $RSI_{t-1} \ge 30$ and $RSI_t < 30$ (Oversold Dip Sweep)
- **Exit (`s4X`)**: $RSI_{t-1} \le 50$ and $RSI_t > 50$ (Reversion into Bullish Momentum)

### 2.5. S5: 20-Period 2-Sigma Bollinger Bands
- **Bands**: $Basis = SMA_{20}$, $Lower = Basis - 2 \times \sigma_{20}$
- **Entry (`s5E`)**: $Close_{t-1} \ge Lower_{t-1}$ and $Close_t < Lower_t$
- **Exit (`s5X`)**: $Close_{t-1} \le Basis_{t-1}$ and $Close_t > Basis_t$

### 2.6. S6 & S7: Gartley 222 Harmonic Ratios & Potential Reversal Zones (PRZ)
The Gartley 222 harmonic pattern searches for a 5-point price oscillation ($X \to A \to B \to C \to D$) using pivot lookback length $lenG = 12$ on 4H and $lenG = 7$ on 1D:

- **Bullish Gartley (L-H-L-H-L)**:
  - Structural constraint: $X < B < D < A$
  - Points: $X$ (Swing Low 3), $A$ (Swing High 2), $B$ (Swing Low 2), $C$ (Swing High 1), $D$ (Swing Low 1)
- **Bearish Gartley (H-L-H-L-H)**:
  - Structural constraint: $X > B > D > A$
  - Points: $X$ (Swing High 3), $A$ (Swing Low 2), $B$ (Swing High 2), $C$ (Swing Low 1), $D$ (Swing High 1)
- **Fibonacci Ratio Validation**:
  $$\frac{AB}{XA} \in [0.55, 0.72] \quad (\text{Target: } 0.618)$$
  $$\frac{BC}{AB} \in [0.382, 0.886]$$
  $$\frac{AD}{XA} \in [0.68, 0.86] \quad (\text{Target: } 0.786)$$
  $$\frac{AB}{CD} \in [0.70, 1.50]$$
- **PRZ Invalidation**: Pattern exits when price closes beyond point $X$, crosses target $A$, or after 40 bars without follow-through.

---

## 3. Pine Script Verdict Priority Ladder

When evaluating a single timeframe, the engine calculates the count of new active triggers (`newEntries`), ongoing positions (`long1..long6`), and active exit signals (`exits`). The verdict is resolved through the exact Pine priority ladder:

1. **`GARTLEY SELL TO USDT`**: Triggered when a Bearish Gartley confirms while any long strategy is active. Mandates rotating capital into cash/USDT.
2. **`CONFLUENCE + GARTLEY BUY`**: Bullish Gartley triggered concurrently with $\ge 2$ additional breakout or trend strategies. Highest conviction spot entry.
3. **`GARTLEY BUY`**: Standalone Bullish Gartley harmonic confirmation at Fibonacci PRZ point D.
4. **`EXIT PRESSURE`**: $\ge 2$ simultaneous exit signals.
5. **`CONFLICT`**: Simultaneous entry and exit triggers on different sub-strategies.
6. **`EXIT WARNING`**: Exactly 1 exit signal with 0 new entries.
7. **`CONFLUENCE BUY`**: $\ge 2$ new entries including at least 1 primary trend strategy (S1 Breakout, S2 SMA200, or S3 EMA cross).
8. **`ENTRY WATCH`**: Exactly 1 new entry signal.
9. **`HOLD`**: 0 new entries, but at least 1 strategy remains actively long.
10. **`NO TRADE`**: All strategies flat.

### Multi-Timeframe Horizon Synthesis
- If 1D is `HOLD` and 4H triggers `GARTLEY BUY` or `CONFLUENCE BUY`: **`🔥 CONFLUENCE BUY (Tactical Trigger)`**
- If 4H triggers `GARTLEY SELL TO USDT`: **`⚠️ GARTLEY SELL TO USDT`**
- If 1D is `HOLD` and 4H is `HOLD`: **`💎 FULL HOLD (1D Trend + 4H Swing)`**
- If 1D is `HOLD` and 4H is `NO TRADE`: **`HOLD (1D Trend Strong, 4H Waiting for Trigger)`**

---

## 4. Standalone Bot Architecture & On-Demand Webhook

The standalone scanner operates independently in GitHub Actions and integrates directly with Telegram:

- **Repository**: `aikeluargalee-tech/btc-spot-verdict-bot`
- **Schedule**: Cron `0 0,4,8,12,16,20 * * *` (every 4 hours at standard candle closes UTC)
- **Telegram Channel / Chat**: `@Gartleyy_bot` (Chat ID: `1273979711`)
- **Swipeable Media Group Albums**: Leverages `sendMediaGroup` to transmit both the 4H Tactical and 1D Daily candlestick charts in a single swipeable post.
- **On-Demand `/now` Webhook Bridge**:
  ```
  User sends /now to @Gartleyy_bot
          │
          ▼
  Telegram Webhook URL
  (Google Apps Script Executable)
          │
          ▼
  GitHub Actions workflow_dispatch API
  (Dispatches btc_scanner.yml run)
          │
          ▼
  Runner fetches Binance Vision public klines,
  evaluates Pine quant engine, generates dual charts,
  and sends album back to @Gartleyy_bot
  ```
- **Webhook URL**: `https://script.google.com/macros/s/AKfycbx0M21chsQ_k-a5SWbM6KbZmzlN81I32DZBO520ylh9iriUtlS-WUlkxsXlkjdR7hUE/exec`

---

## 5. Terminal HUD Specification (The 5-Panel Single-Screen Law)

In `btc_swing_engine`, Tab `[S3]` adheres strictly to the **5-Panel Single-Screen Law** ($\le 49$ terminal lines):

1. **Panel 1: Global Header Panel**: Displays multi-venue prices (Binance Spot, Perp, Coinbase), active market session badge, world clocks, and tab selector:
   `BTC-USD | [1]•[2]•[3]•[4]•[5]•[S1: MM-BTC]•[S2: 72H CONE]•[S3: GARTLEY]`
2. **Panel 2: Top Ribbon (3 Cards)**:
   - Card 1: Multi-Timeframe Overall Verdict & Spot Price.
   - Card 2: Engine Architecture & GitHub Actions Status.
   - Card 3: Telegram Bot (`@Gartleyy_bot`), Webhook status, and cron schedule.
3. **Panel 3: Side-by-Side State Machine Tables**:
   - Table 1 (Left): **1D Daily Macro Trend State Machine (S1–S7)**.
   - Table 2 (Right): **4H Tactical Swing Execution (S1–S7)**.
4. **Panel 4: Harmonic 222 Potential Reversal Zone (PRZ) Radar**:
   - Fibonacci ratio validation tolerances ($B/XA$, $C/AB$, $D/XA$, $AB/CD$).
   - Current Bullish PRZ and Bearish PRZ target price levels for both horizons.
5. **Panel 5: Executive Synthesis & Action Playbook**:
   - Pine verdict ladder explanation.
   - Plain English trader summary.
   - AI Telemetry Packet clipboard copy badge (`[✔ COPIED TO CLIPBOARD]` on key `C`).
   - Hotkey guide (`8`/`G` for Tab S3, `7`/`V` for S2, `6`/`S` for S1, `1`–`5` for Core, `C` to copy).

---

## 6. Verification & CLI Usage

Run Tab `[S3]` in dry-run mode:
```powershell
python main.py --dry-run --duration 3 --tab s3 --copy-packet
```

Switch to Tab `[S3]` during live operation:
- Press key **`8`**, **`G`**, or **`g`** at any time. Tab switches instantaneously in 0.0 seconds without redrawing or dropping WebSocket frames.
