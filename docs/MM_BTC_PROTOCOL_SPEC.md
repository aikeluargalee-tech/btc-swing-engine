# MM-BTC: The Rough Path Arbitrator
## Multi-Model Stochastic Path Geometry & Dynamic Invariance Protocol

**Protocol Classification:** Institutional-Grade Mathematical Radar & Path Signature Execution System  
**Target Asset & Mandate:** Bitcoin (`BTC-USD` / `BTCUSDT`) — **Strictly Long-Only Spot Swing & Positional Trading** (Zero Leverage, Zero Shorting)  
**Terminal Integration:** Tab `[S1]` (`[S1: MM-BTC QUANT RADAR]`) in the `BTC-USD Spot Swing Engine`  
**Hotkey Access:** Press **`S`**, **`s`**, or **`6`** in the Live Rich Terminal HUD | CLI Flag: `--tab s1`  

---

## 1. Executive Summary & Core Philosophy

Modern crypto markets are dominated by high-frequency algorithmic market makers, cross-venue latency arbitrage, and engineered derivative sweeps. In this environment, classical retail technical indicators—such as RSI, MACD, Stochastics, and simple moving average crossovers—fail systematically for three structural reasons:

1. **Phase Lag & Historical Distortion**: Indicators built from simple rolling price windows lag the market and generate false breakout signals at the exact moment institutional liquidity providers are engineering an exit.
2. **Blindness to Path Geometry**: A price that rises \$2,000 via a clean, persistent institutional accumulation drift looks identical on an RSI chart to a price that whipsaws \$2,000 via a violent, Brownian liquidation squeeze. Classical indicators cannot measure the *roughness* or *geometric curvature* of the trajectory.
3. **Symmetric Assumptions in Asymmetric Markets**: Standard indicators treat upward and downward volatility identically, ignoring whether a price pump is fueled by thin retail taker leverage or genuine cross-exchange spot absorption.

**MM-BTC (The Rough Path Arbitrator)** solves these structural failures by replacing discretionary charting with **six orthogonal mathematical disciplines** drawn from stochastic calculus, fractal geometry, spectral signal processing, and Terry Lyons' theory of Rough Paths. 

Instead of asking *"Is BTC overbought or oversold?"*, MM-BTC answers three rigorous institutional questions:
* **Is the continuous price trajectory mathematically clean, or is it dominated by toxic Brownian chop?**
* **Does the path geometry reveal an engineered liquidation pump designed to trap late buyers?**
* **Do independent state-space, fractal, spectral, and memory models concur with enough statistical edge to justify allocating capital above the dust threshold?**

---

## 2. The 6 Orthogonal Mathematical Dimensions

MM-BTC evaluates 300 hours of synchronized 1-hour and 15-minute multi-exchange market data across six mathematically independent dimensions:

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                MM-BTC SIX MATHEMATICAL DIMENSIONS                                      │
├────────────────────────────────┬────────────────────────────────┬──────────────────────────────────────┤
│ 1. State-Space Velocity        │ 2. Fractal Memory Geometry     │ 3. Memory-Preserving FracDiff        │
│    1D Constant-Velocity Kalman │    Rolling 128-Bar Hurst (H)   │    Dynamic ADF Stationarity (p<0.05) │
│    Latent Price & True $/hr    │    Persistence vs. Random Walk │    12-Bar Fractional Momentum        │
├────────────────────────────────┼────────────────────────────────┼──────────────────────────────────────┤
│ 4. Spectral Analytic Signal    │ 5. Microstructure Flow Dynamics│ 6. THE CHIEF ARBITER (ROUGH PATHS)   │
│    Ehlers Hilbert + Hampel MAD │    48h Net Spot/Perp CVD & OI  │    Terry Lyons' Signatures (N <= 2)  │
│    Phase 0°–360° (Trough/Peak) │    Passive Absorption vs. Trap │    Roughness R & Lévy Areas A_(X,Y)  │
└────────────────────────────────┴────────────────────────────────┴──────────────────────────────────────┘
```

---

### Dimension 1 (Lens A): State-Space Velocity (1D Constant-Velocity Kalman Filter)

Microstructure noise, exchange bid-ask bounce, and low-volume wick spikes contaminate observed closing prices. Lens A deploys a **1D Constant-Velocity Kalman Filter** to estimate the unobservable latent state vector:

$$x_t = \begin{bmatrix} p_t \\ v_t \end{bmatrix}$$

where $p_t$ is the true underlying price and $v_t$ is the instantaneous drift velocity in $\$ / \text{hr}$.

* **State Transition & Covariance Equations**:
  $$x_{t|t-1} = F x_{t-1|t-1}, \quad F = \begin{bmatrix} 1 & \Delta t \\ 0 & 1 \end{bmatrix}$$
  $$P_{t|t-1} = F P_{t-1|t-1} F^T + Q$$
  where $Q$ represents the process noise covariance matrix tuned for Bitcoin's hourly drift volatility.
* **Measurement & Innovation Update**:
  $$\tilde{y}_t = z_t - H x_{t|t-1}, \quad H = \begin{bmatrix} 1 & 0 \end{bmatrix}$$
  $$K_t = P_{t|t-1} H^T (H P_{t|t-1} H^T + R)^{-1}$$
  $$x_{t|t} = x_{t|t-1} + K_t \tilde{y}_t$$
* **Operational Output**:
  * **Filtered Price $\hat{p}_t$**: The true noise-free reference price.
  * **Velocity $v_t$**: Quantifies real buying speed without indicator lag. $v_t > +\$50 / \text{hr}$ confirms positive drift momentum; $v_t < -\$50 / \text{hr}$ warns of active selling.

---

### Dimension 2 (Lens B): Fractal Memory & Trend Persistence (Rolling Hurst Exponent $H$)

Markets alternate between directional trending states and mean-reverting chop regimes. Applying breakout strategies inside a mean-reverting regime causes severe drawdowns. Lens B computes the **Hurst Exponent ($H$)** over a rolling 128-bar window using dyadic **Rescaled Range ($R/S$) Analysis**:

1. Subdivide the rolling 128-bar return series into dyadic intervals $\tau \in \{16, 32, 64, 128\}$.
2. For each lag $\tau$, compute the cumulative deviation from the interval mean and calculate the range:
   $$R(\tau) = \max_{1 \le k \le \tau} \sum_{i=1}^k (r_i - \bar{r}) - \min_{1 \le k \le \tau} \sum_{i=1}^k (r_i - \bar{r})$$
3. Normalize by the sample standard deviation $S(\tau)$ to obtain the rescaled range $R(\tau) / S(\tau)$.
4. Extract $H$ via ordinary least squares regression:
   $$\log\left(\frac{R(\tau)}{S(\tau)}\right) = H \cdot \log(\tau) + C$$

* **Regime Classification**:
  * **$H > 0.55$ (Persistent Trend Regime)**: Price steps exhibit positive autocorrelation. Favorable environment for breakout expansion and swing continuation.
  * **$0.45 \le H \le 0.55$ (Geometric Brownian Motion / Random Walk)**: Returns are uncorrelated. Market is unpredictable; position sizing must be heavily discounted.
  * **$H < 0.45$ (Mean-Reverting Chop Regime)**: Price steps exhibit negative autocorrelation. Breakouts fail; mandate restricts trades to fading range extremes.

---

### Dimension 3 (Lens C): Memory-Preserving Fractional Differentiation (Dynamic FFD)

Standard financial analysis differentiates prices by integer order $d=1$ ($\Delta p_t = p_t - p_{t-1}$) to achieve stationarity for statistical testing. However, integer differentiation completely erases long-term structural memory (macro support levels, cycle pivots, historical cost basis).

Lens C applies **Fixed-Width Window Fractional Differentiation (FFD)** via binomial expansion:

$$(1 - L)^d = \sum_{k=0}^{\infty} (-1)^k \binom{d}{k} L^k = 1 - dL + \frac{d(d-1)}{2!} L^2 - \frac{d(d-1)(d-2)}{3!} L^3 + \dots$$

Weights $w_k$ are truncated when $|w_k| < \tau = 10^{-4}$ to maintain a fixed historical lookback window without memory distortion.

* **Dynamic Augmented Dickey-Fuller (ADF) Iteration**:
  Instead of hardcoding a fixed $d$, Lens C searches $d \in [0.05, 0.80]$ in steps of 0.05 to locate the **minimum critical order $d^*$** that satisfies stationarity:
  $$\text{ADF } p\text{-value}(d^*) < 0.05$$
* **Operational Output**:
  * **Optimal Order $d^*$**: Lowest order preserving maximal price history while passing unit root rejection.
  * **12-Bar Fractional Momentum**: Clean, stationary rate-of-change indicating structural drift without lag or memory loss.

---

### Dimension 4 (Lens D): Spectral Cycles & Instantaneous Phase (Ehlers Hilbert Transform + Causal Hampel Filter)

Financial series contain cyclical oscillations driven by global liquidity sessions, derivative expiry cycles, and funding windows. Lens D utilizes John Ehlers' **Hilbert Transform Analytic Signal** to decompose price into instantaneous cycle period and phase angle.

1. **Causal Hampel Filter (Median Absolute Deviation Outlier Clipping)**:
   Liquidation wicks distort classical Fourier and Hilbert phase calculations. A rolling 12-bar window applies causal median clipping:
   $$\text{MAD}_t = 1.4826 \cdot \text{median}(|p_{t-k} - \tilde{p}_t|)$$
   If $|p_t - \tilde{p}_t| > 3 \cdot \text{MAD}_t$, $p_t$ is clamped to the rolling median $\tilde{p}_t$ before computing analytic transforms.
2. **Analytic Signal Decomposition**:
   Constructs the complex analytic signal $Z_t = I_t + j Q_t$, where $I_t$ is the detrended In-Phase component and $Q_t$ is the $90^\circ$ phase-shifted Quadrature component.
3. **Instantaneous Phase Angle & Cycle Period**:
   $$\theta_t = \arctan\left(\frac{Q_t}{I_t}\right) \in [0^\circ, 360^\circ], \quad T_t = \frac{360^\circ}{\Delta \theta_t}$$

* **Cycle Quadrant Mapping**:
  * **Quadrant 1 ($0^\circ–90^\circ$ & $315^\circ–360^\circ$) — Cycle Trough / Reversal**: Price has completed its cyclical descent; optimal accumulation window.
  * **Quadrant 2 ($90^\circ–180^\circ$) — Markup Expansion**: Upward cyclical acceleration.
  * **Quadrant 3 ($180^\circ–270^\circ$) — Cycle Peak / Distribution**: Cyclical exhaustion; **strict veto against initiating new long entries**.
  * **Quadrant 4 ($270^\circ–315^\circ$) — Markdown Decline**: Downward cyclical trajectory.

---

### Dimension 5 (Lens E): Microstructure Order Flow Dynamics (48h Spot CVD vs. Perp CVD & OI)

Price movement without volume verification is deceptive. Lens E aggregates continuous tick trades across Binance Spot, Binance Perpetual Futures, and Coinbase Spot over a rolling 48-hour horizon:

* **Spot Cumulative Volume Delta ($\Delta \text{CVD}_{\text{spot}}$)**: Measures net market taker buying of physical spot Bitcoin.
* **Perp Cumulative Volume Delta ($\Delta \text{CVD}_{\text{perp}}$)**: Measures speculative leverage aggression.
* **Open Interest Delta ($\Delta \text{OI}$)**: Tracks capital entering or exiting the perpetual derivatives ecosystem.

* **Diagnostic Rules**:
  * **Spot Absorption**: $\Delta \text{CVD}_{\text{spot}} > 0$ while $\Delta \text{CVD}_{\text{perp}} \le 0$ confirms passive institutional buying absorbing retail short selling.
  * **Leveraged Trap**: Price rising while $\Delta \text{CVD}_{\text{spot}} \le 0$ and $\Delta \text{OI} \gg 0$ warns of an imminent long liquidation cascade.

---

### Dimension 6: The Chief Arbiter — Rough Path Signatures (Order $N \le 2$)

The **Chief Arbiter** is the foundational breakthrough of the MM-BTC architecture. Originating in Terry Lyons' rough path theory (stochastic analysis of non-smooth trajectories), Path Signatures map a continuous multi-channel stream into an infinite-dimensional series of iterated integrals that uniquely encode the geometric shape of the trajectory independently of time parametrization.

MM-BTC defines the 4-channel path:
$$X_t = \begin{bmatrix} t \\ \log(P_t) \\ \text{CVD}_t \\ \text{OI}_t \end{bmatrix}, \quad t \in [0, T]$$

#### 1. Level 1 Signatures (Net Coordinate Drifts)
The first-order signatures measure the total net displacement along each coordinate axis over the 48-hour window:
$$S^{(P)} = \int_0^T d\log(P_t) = \log(P_T) - \log(P_0)$$
$$S^{(V)} = \int_0^T d\text{CVD}_t = \text{CVD}_T - \text{CVD}_0$$
$$S^{(O)} = \int_0^T d\text{OI}_t = \text{OI}_T - \text{OI}_0$$

#### 2. Level 2 Signatures — Quadratic Variation Path Roughness ($\mathcal{R}$)
The Chief Arbiter measures the "roughness" or toxic noise of the price path by comparing realized quadratic variation to linear net displacement:
$$\mathcal{R} = \frac{\sum_{i=1}^T (\Delta \log P_i)^2}{\left(\log P_T - \log P_0\right)^2 + \epsilon}$$

* **Anti-Chop Circuit Breaker Law**:
  $$\text{If } \mathcal{R} > 4.50 \implies \mathbf{HARD\ VETO\ (CHOP\ CIRCUIT\ BREAKER)}$$
  When $\mathcal{R} > 4.50$, price motion is dominated by Brownian random walk and erratic whipsaws. The Chief Arbiter overrides all other models and forces the system into **100% Cash**.

#### 3. Level 2 Signatures — Lévy Signed Areas ($A_{(X, Y)}$)
The second-order iterated integral between channels $X$ and $Y$ defines the **Lévy Signed Area**, representing the area enclosed by the trajectory in the $X\text{-}Y$ plane:
$$A_{(X, Y)} = \frac{1}{2} \int_0^T \left(X_t dY_t - Y_t dX_t\right)$$

* **Time-Price Area $A_{(t, P)}$ (Sweep / Exhaustion Pump Detector)**:
  * Measures the convexity of the price curve against time.
  * If price creeps slowly upward and then spikes violently into the end of the window, $A_{(t, P)}$ prints a large positive value ($> +0.15$).
  * **Anti-Sweep Law**:
    $$\text{If } A_{(t, P)} > +0.15 \implies \mathbf{BULL\ TRAP\ VETO\ (CONVEX\ PUMP\ DETECTED)}$$
    This mathematical condition flags engineered breakout traps where algorithmic market makers push price higher to trigger retail buy-stops into passive limit sell orders.
  * If $A_{(t, P)} < -0.15$, price exhibits a concave bottoming spring—signaling that sellers pushed hard early but lost momentum, establishing a high-probability accumulation base.
* **Price-Flow Area $A_{(P, V)}$ (Institutional Absorption vs. Retail Push)**:
  * Measures the geometric correlation between price advancement and cumulative volume delta.
  * $A_{(P, V)} > 0$: Price is supported by cumulative spot buying (Institutional Accumulation).
  * $A_{(P, V)} < 0$: Price is rising on negative or thinning volume (Retail Exhaustion Push).
* **Price-OI Area $A_{(P, O)}$ (Short Squeeze vs. Leverage Overhang)**:
  * Measures the correlation between price advancement and open interest.
  * $A_{(P, O)} > 0$: Price rising as open interest contracts confirms short squeeze fuel and leverage clearing.
  * $A_{(P, O)} < 0$: Price rising while open interest expands rapidly warns of an over-leveraged long trap.

---

## 3. The 3-Gate Institutional Arbitration Gauntlet

The live telemetry outputs from the six dimensions do not enter a simple weighted average. Instead, they must survive a **strict 3-gate hierarchical gauntlet**:

```
                         ┌──────────────────────────────────┐
                         │   RAW MULTI-MODEL TELEMETRY      │
                         └─────────────────┬────────────────┘
                                           │
                                           ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│ GATE 1: STRUCTURAL INVARIANCE & SUPREME VETO GATE                                   │
│ • Path Roughness: R <= 4.50? (If > 4.50 -> Toxic Chop Veto -> 0.00x Allocation)     │
│ • Time-Price Convexity: A_(t,P) <= +0.15? (If > +0.15 -> Sweep Trap Veto -> 0.00x)  │
└──────────────────────────────────────────┬──────────────────────────────────────────┘
                                           │ PASS
                                           ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│ GATE 2: DYNAMIC MOMENTUM & MULTI-MODEL CONCURRENCE GATE                             │
│ • Model Agreement Count: How many of the 5 Lenses agree on bullish drift?           │
│ • Dual-Resolution 15m Micro Tripwire: Are trailing 15m bars dumping? (If Yes->Veto) │
└──────────────────────────────────────────┬──────────────────────────────────────────┘
                                           │ PASS
                                           ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│ GATE 3: WALK-FORWARD RIDGE SIZING & DUST FILTER                                     │
│ • Compute Expected Return Y_hat via Walk-Forward Ridge Regression                   │
│ • Apply 200-Hour SMA Gatekeeper: Price < SMA_200h -> Hard-Cap Size at 0.50x         │
│ • Apply 0.20x Dust Filter: If final size < 0.20x -> Force 0.00x (100% Cash)         │
└──────────────────────────────────────────┬──────────────────────────────────────────┘
                                           │
                                           ▼
                         ┌──────────────────────────────────┐
                         │    RECONCILED EXECUTION ORDER    │
                         │    Size: 0.20x to 1.00x Spot     │
                         └──────────────────────────────────┘
```

### Gate 1: Structural Invariance & Supreme Veto Gate
Gate 1 evaluates physical path geometry via the Chief Arbiter:
* If Path Roughness $\mathcal{R} > 4.50$, Gate 1 prints `FAIL` $\rightarrow$ Trade blocked.
* If Time-Price Area $A_{(t, P)} > +0.15$, Gate 1 prints `FAIL` $\rightarrow$ Trade blocked.
* Only when both structural conditions pass is the system authorized to proceed to Gate 2.

### Gate 2: Dynamic Momentum & 15m Micro Tripwire Gate
Gate 2 tests whether the internal models concur and checks high-resolution intraday flow:
* **Lens Concurrence**: Audits how many of the 5 lenses (Kalman velocity $>0$, Hurst $H > 0.50$, FracDiff momentum $>0$, Hilbert phase $\in [315^\circ, 135^\circ]$, 48h Spot CVD $>0$) corroborate the move.
* **Dual-Resolution 15m Micro Order Flow Tripwire**:
  * While the core models operate on 1-hour closes, the 15m Tripwire continuously monitors trailing 48x 15-minute bars (12 hours).
  * If a rapid sell volume burst or aggressive futures taker dumping occurs on the 15-minute timeframe, the Tripwire activates immediately, vetoing the trade before the 1-hour bar closes.

### Gate 3: Walk-Forward Ridge Sizing & Dust Filter
When Gates 1 and 2 pass, Gate 3 computes optimal position sizing:
1. **Walk-Forward Ridge Regression**:
   A regularized ridge regressor ($\lambda = 1.0$) trains on rolling historical feature vectors (drifts, Hurst, fracdiff, phase, CVD) to predict the 12-hour forward return $\hat{Y}_t$:
   $$\hat{\beta} = (X^T X + \lambda I)^{-1} X^T y, \quad \hat{Y}_t = X_t \hat{\beta}$$
2. **200-Hour SMA Gatekeeper**:
   * If current price is below the 200-hour SMA, the macro structural trend is defensive.
   * Maximum permitted sizing multiplier is strictly **hard-capped at $0.50\text{x}$**.
3. **The 0.20x Dust Filter**:
   * Sizing is penalized by thin volume ($A_{(P, V)} < 0$), low model concurrence ($< 3/5$), and below-SMA price action.
   * If the resulting sizing multiplier falls below **$0.20\text{x}$**, the engine rejects the trade as "dust" and mandates **100% Cash**:
     $$\text{If } \text{Size} < 0.20\text{x} \implies \mathbf{SIZE = 0.00x\ (100\%\ CASH\ PRESERVATION)}$$
   * This prevents taking taker execution fees and exchange slippage on low-conviction setups.

---

## 4. Reconciled Execution Playbooks

The engine outputs two distinct operational playbooks depending on user inventory:

### Track A: If Flat in Cash (USDT)
* **Allocation Sizing**: Dictated by Gate 3 ($0.20\text{x}$ to $1.00\text{x}$ of standard $1.0\%$ risk budget).
* **Limit Bid Entry Zone**: Bracketed between the lower structural anchor ($[P_t - 1.0 \times \text{ATR}]$) and current price. Chasing at market is strictly prohibited.
* **Hard Stop Loss**: Positioned strictly below the structural window low (invalidation anchor).

### Track B: If Holding Spot BTC
* **Hold Recommendation**: Authorizes holding core spot position when structural trajectory is sound.
* **Profit Targets (TP1 / TP2)**:
  * **TP1**: Fair-value mean reversion target (Kalman filtered price or structural mid-range).
  * **TP2**: Structural expansion target (upper window band or cycle resistance).

---

## 5. Architectural Synergy: Tab `[S1]` vs. Tabs `[1]–[5]`

MM-BTC does not replace or compete with the core engine tabs. It acts as an **orthogonal mathematical radar** that cross-examines the Auction Market Theory of Tabs `[1]–[5]`:

| Architecture Desk | Analytical Discipline | Core Question Answered |
| :--- | :--- | :--- |
| **Tab `[1]`: Tactical Swing Engine** | Volume Profile (cVAL, cPOC, cVAH) & Multi-Horizon CVD | *Where is the auction value area, and is spot absorbing perps at the edge?* |
| **Tab `[2]`: Protocol v1.3** | CoinGlass 6-Panel, Liquidation Magnets & NTZ Rules | *Is derivative leverage overheating, and are nearby liquidation pools flushed?* |
| **Tab `[3]`: Macro Quant Radar** | 1D 200 SMA Gatekeeper & Cycle Crash Rungs (-25% to -65%) | *What is the long-term cycle regime and base risk budget?* |
| **Tab `[4]`: Regime Matrix A–J** | 10 Microstructure Configurations & Global Market Sessions | *Which institutional trading playbook is active right now?* |
| **Tab `[5]`: Master Synthesis** | 4-Layer Decision Funnel & Supreme Order of Battle | *What is the reconciled command across all specialist desks?* |
| **Tab `[S1]`: MM-BTC Radar** | Rough Path Signatures, 5 Stochastic Lenses & Walk-Forward Ridge | *Is the continuous path geometry mathematically sound, or is it an engineered trap?* |

---

## 6. How to Run & Audit

### 1. Launching the Live Rich Terminal HUD
```powershell
python main.py
```
* **Switching Tabs**:
  * Press **`1`** for Tactical Swing Engine (Auction Volume Profile)
  * Press **`2`** for Protocol v1.3 (CoinGlass & Liquidation Magnets)
  * Press **`3`** for Macro Quant Radar (200D SMA & Crash Rungs)
  * Press **`4`** for Regime Matrix A–J (Microstructure Playbooks)
  * Press **`5`** for Master Synthesis & Final Order of Battle
  * Press **`S`**, **`s`**, or **`6`** for **`[S1: MM-BTC QUANT RADAR]`**
* **Copying the Master AI Telemetry Packet**:
  * Press **`C`** on any tab. The engine copies the full raw telemetry across all tabs (including Section 7 MM-BTC raw metrics) directly to the Windows clipboard and saves it to:
    `C:\Users\aikel\Downloads\BTC_AI_DATA_PACKET_LATEST.md`

### 2. Direct Verification & Dry-Run
```powershell
# Run self-contained verification of Tab [S1] and export AI packet
python main.py --dry-run --duration 3 --tab s1 --copy-packet

# Run full test suite covering all mathematical models
python -m unittest discover -s tests -v
```

---

*Document Author: Chief Quantitative Strategist & AI Architecture Team*  
*Classification: Institutional Trading System Specification — Production Ready*
