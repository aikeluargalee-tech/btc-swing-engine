# Special Tab [S5]: Terminal Exhaustion & Delta Divergence Radar Specification

## 1. Domain Rationale: Why Classical Elliott Wave Fails in Crypto

Classical Elliott Wave Theory (EWT), conceived by Ralph Nelson Elliott in the 1930s, posits that financial markets progress in 5-wave motive impulses followed by 3-wave corrective consolidations. While intuitive, hardcoding EWT into an automated crypto execution system introduces critical flaws:

1. **The "Alternate Count" Fallacy (Non-Falsifiability)**:
   In quantitative trading, a signal must have a deterministic invalidation point. Classical EWT is notoriously non-falsifiable in practice. When an anticipated "Wave 3 impulse" fails, wave theorists rarely accept invalidation; instead, they retroactively re-label the structure as an "extended wave," a "leading diagonal," or a "complex W-X-Y-X-Z corrective flat." An algorithm cannot execute cleanly when the underlying model can infinitely shift its goalposts.

2. **Combinatorial Explosion in Code**:
   Writing a parser for Elliott Wave requires tracking multiple degrees of trend (Subminuette up to Primary cycles), nesting sub-waves inside larger waves. Because corrective waves feature dozens of valid permutation rules (triangles, running flats, double zigzags), an automated script evaluating real-time tick data will frequently generate 10 to 30 conflicting "valid" counts simultaneously, paralyzing trade execution.

3. **Complete Microstructure Disconnect**:
   Waves are drawn on close prices or bar wicks without reference to the limit order book, open interest, or aggressive taker volume. A market does not reverse because a "Wave 5 target" was reached; it reverses because passive limit orders absorbed aggressive market buyers and perp funding became prohibitively expensive.

---

## 2. Quantitative Replacement: The 3 Objective Pillars of Tab [S5]

Special Tab `[S5]` strips away subjective wave labels and replaces them with 3 deterministic mathematical lenses:

### Pillar A: Tom DeMark (TD) Sequential (TD-9 / TD-13 Setup & Perfection)
* **Mathematical Invariant**: Compares each candle's close against the close 4 bars prior (`close[i]` vs. `close[i-4]`).
* **Bearish Setup (Exhaustion Top / "Wave 5")**: 9 consecutive closes where `close[i] > close[i-4]`.
  * **Perfection**: High of bar 8 or 9 $\ge$ high of bar 6 and bar 7.
  * **Invalidation Anchor**: True highest wick of bars 8 & 9 + $0.5\times\text{ATR}$.
* **Bullish Setup (Exhaustion Bottom / "Wave C")**: 9 consecutive closes where `close[i] < close[i-4]`.
  * **Perfection**: Low of bar 8 or 9 $\le$ low of bar 6 and bar 7.
  * **Invalidation Anchor**: True lowest wick of bars 8 & 9 - $0.5\times\text{ATR}$.

### Pillar B: Multi-Horizon Delta Divergence (Spot vs. Perp CVD)
* **Regular Bearish Divergence**: Price prints a higher high across fractal pivots, but volume delta prints lower highs (aggressive buyers exhausted into passive institutional limit resistance).
* **Regular Bullish Divergence**: Price prints a lower low, but volume delta prints higher lows (aggressive sellers absorbed by passive institutional limit bids).
* **Derivatives Chaser Trap**: Perp CVD aggressively expanding while Spot CVD decouples or is negative (perps chasing into wholesale distribution).


### Pillar D: Tell-Tale Candle Climax Sensor (tell_tale_candle Integration)
* **Mathematical Invariant**: Evaluates closed 15m (and 5m) bars against a 20-period volume baseline (lagged, excludes current bar).
* **Selling Climax (Capitulation Flush / Wave C Bottom)**:
  - Candle is Red (`close < open`)
  - Relative Volume $\ge 5.0\times$ baseline (`relvol >= 5.0`)
  - Solid Candle Body $\ge 0.65$ of range (`|close - open| / (high - low) >= 0.65`)
* **Buying Climax (Blow-Off Top / Wave 5 Peak)**:
  - Candle is Green (`close > open`)
  - Relative Volume $\ge 5.0\times$ baseline
  - Solid Candle Body $\ge 0.65$ of range
* **Score Impact**: Awards **+15 points** bonus to the composite Exhaustion Score upon disruption detection. When combined with a perfected TD-9 setup, it confirms extreme terminal capitulation where retail forced market orders exhaust directly into institutional limit liquidity.

### Pillar C: Open Interest & Funding Rate Climax Stress
* **$\Delta\text{OI}$ Climax**: Rapid surge in Open Interest ($\ge +1.20\%$ in 1H or $\ge +0.40\%$ in 15m) accompanied by stalled price progress indicates trapped chasers.
* **Funding Rate Saturation**: 8H funding $> +0.025\%$ (overheated longs) or $< -0.015\%$ (overcrowded shorts).

---

## 3. Composite Exhaustion Scoring & Regime Mapping

The engine computes an aggregate **Exhaustion Score** from 0.0 to 100.0:
* **TD Sequential Setup**: Up to 35 points (35 for perfected 9/9, 25 for unperfected 9/9, 15 for 7–8 count).
* **CVD Delta Divergences**: Up to 35 points (35 for critical multi-timeframe divergence, 25 for single-timeframe, 15 for absorption).
* **OI & Funding Climax**: Up to 30 points (30 for dual OI + funding stress, 15 for single stress flag).

| Score Range | Exhaustion Regime | Meaning & Action Playbook |
| :---: | :--- | :--- |
| **0 – 34** | `MOMENTUM HEALTHY` | Trend expanding in harmony. No terminal divergence. Let winners run. |
| **35 – 59** | `LATE CYCLE STRAIN` | Trend momentum decelerating. Tighten trailing stops; avoid fresh leverage. |
| **60 – 79** | `TERMINAL EXHAUSTION ARMED` | TD-9 active + delta divergence detected. Prepare mean-reversion order of battle. |
| **80 – 100** | `ACTIVE REVERSAL TRIGGER` | Perfected TD-9 + critical divergence + climax stress. Arm asymmetric counter-trend trade ($R:R \ge 1:2.5$). |

---

## 4. Asymmetric Execution Geometry ($R:R \ge 1:2.5$)

When terminal exhaustion triggers:
* **Entry**: Spot reference price at 15m candle close confirmation.
* **Invalidation Stop Loss**: Perfected TD-9 exhaustion wick extreme $\pm 0.5\times\text{ATR}_{1H}$.
* **Take Profit 1 (Fast Mean)**: Fast mean reversion target (1H POC or EMA-20).
* **Take Profit 2 (Composite Value)**: Composite POC or opposing Value Area boundary (`cVAL`/`cVAH`).
* **Strict Minimum R:R**: $2.50\text{R}$.

---

## 5. Hotkeys & CLI Invocation

* **Terminal HUD Key**: Press **`0`** (or **`E`** / **`e`**) to switch immediately to Tab `[S5]`.
* **CLI Flag**: `python main.py --tab s5` (or `--tab 0`, `--tab 10`, `--tab all`).
* **Telemetry Packet**: Appends **`SECTION 11: TAB [S5] TERMINAL EXHAUSTION & DELTA DIVERGENCE RADAR`** to `BTC_AI_DATA_PACKET_LATEST.md` and Windows clipboard on pressing **`C`**.
