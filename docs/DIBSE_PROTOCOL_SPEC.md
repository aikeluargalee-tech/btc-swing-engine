# DIBSE: Dual-Inventory Bidirectional Swing Engine
## Official Protocol Specification & Architecture Blueprint v1.0

---

## 1. Executive Summary & Mandate

The **Dual-Inventory Bidirectional Swing Engine (DIBSE)** is a quantitative, spot-only trading protocol designed to harvest structural volatility continuously from both upward and downward market swings without leverage, debt, margin, liquidation risk, or directional dependence.

Unlike traditional directional trading strategies that force a binary choice (holding 100% cash or 100% Bitcoin) or rely on leveraged shorting on perpetual futures, DIBSE operates on a **permanent dual-asset spot inventory (BTC + USDT)** within a ring-fenced sandbox.

---

## 2. Capital Architecture & Sandbox Isolation

| Capital Tier | Allocation | Operational Mandate |
| :--- | :---: | :--- |
| **Core Reserve (Untouched)** | **80.0%** | Held permanently in cold storage. Completely insulated from active trading. |
| **DIBSE Active Sandbox** | **20.0%** | The total maximum capital deployed across both swing loops. |
| **• Tranche 1: USDT Sleeve** | **10.0%** | Dry powder reserved exclusively for **Swing Loop A** (accumulating dips). |
| **• Tranche 2: BTC Sleeve** | **10.0%** | Spot inventory reserved exclusively for **Swing Loop B** (distributing rips). |

---

## 3. The Five Core Pillars (Locked Working Blueprint)

### Pillar 1: Two-Way Spot Volatility Harvesting (Not Directional Betting)
DIBSE does not attempt to forecast whether Bitcoin is in a macro bull or bear trend. Instead, it treats price as an oscillating ergodic process between structural support and resistance levels. By maintaining permanent inventory of both assets, the protocol extracts yield from volatility in both directions.

### Pillar 2: Swing Loop A (USDT → BTC → USDT) — The Dip Harvester
- **Trigger:** High-conviction washout into institutional support (30D Value Area Low $VAL_{30}$ or 20-Day Low $L_{20}$, accompanied by positive spot CVD absorption and exhausted funding).
- **Execution:** Deploy the **10% USDT Sleeve** to purchase spot BTC at a structural discount.
- **Exit:** When price recovers toward the 30D Point of Control ($POC_{30}$) or Value Area High ($VAH_{30}$), rotate the acquired BTC back into USDT.
- **Harvest Outcome:** Realizes **pure USDT cash profit**, increasing the cash balance of the USDT sleeve.

### Pillar 3: Swing Loop B (BTC → USDT → BTC) — The Rip Harvester & Stack Accumulator
- **Trigger:** High-conviction rally into institutional resistance (30D Value Area High $VAH_{30}$ or 20-Day High $H_{20}$, accompanied by whale spot distribution and euphoric retail perpetual funding $>75\%$).
- **Execution:** Sell the **10% BTC Sleeve** into spot USDT at a premium price.
- **Exit:** When price subsequently retraces toward support ($POC_{30}$ or $VAL_{30}$), deploy the proceeds to repurchase spot BTC.
- **Harvest Outcomes (Two Positive Paths):**
  1. **Satoshi Compounding:** The exact same USDT proceeds purchase **more BTC units (+Free Satoshis)** than were originally sold, permanently growing the Bitcoin stack.
  2. **Surplus Cash Lock:** Repurchase the exact original BTC quantity and lock the price differential as surplus USDT cash.

### Pillar 4: Zero Leverage, Zero Liquidation, Zero Forced Stop-Losses
- 100% of all transactions take place on the spot market.
- No borrow fees, no margin interest, no negative funding squeeze bleed.
- **Zero forced stop-loss liquidations:** Traditional stop-loss hunting mechanisms cannot wipe out capital because there is no counterparty loan to liquidate.

### Pillar 5: Asymmetric Self-Healing Inventory
Being early or "wrong" on short-term timing never destroys capital or forces realized losses:
- **Loop A Extension (Price drops after buying):** If BTC drops lower after deploying the USDT sleeve, you simply retain the spot BTC in your inventory. You earn organic holding value and wait until price recovers above your entry watermark.
- **Loop B Extension (Price rises after selling):** If BTC continues higher after deploying the BTC sleeve, you simply retain the spot USDT in your inventory. You hold safe cash dry powder and wait until price retraces below your sale watermark.

---

## 4. Finite State Machine (FSM)

```
                       ┌───────────────────────────────────────────────┐
                       │          STATE 0: NEUTRAL EQUILIBRIUM         │
                       │       [10% USDT Sleeve] + [10% BTC Sleeve]     │
                       └───────────────────────────────────────────────┘
                                       │               │
        [Loop A Trigger: Washout into VAL]             │ [Loop B Trigger: Pump into VAH]
        [Spot Absorption D_flow >= +1.0]               │ [Whale Dump D_flow <= -1.0]
        [Perp Funding Cleansed <25%]                   │ [Perp Euphoria Funding >75%]
                                       ▼               ▼
                       ┌────────────────────────┐     ┌────────────────────────┐
                       │ STATE 1A: LOOP A ACTIVE│     │ STATE 1B: LOOP B ACTIVE│
                       │ 10% USDT converted to  │     │ 10% BTC converted to   │
                       │ Spot BTC.              │     │ Spot USDT.             │
                       │ Total Inventory:       │     │ Total Inventory:       │
                       │ [20% BTC, 0% USDT]     │     │ [0% BTC, 20% USDT]     │
                       └────────────────────────┘     └────────────────────────┘
                                       │                               │
        [BTC rallies into Resistance]  │              [BTC retraces into Support]
        [Reaches Take-Profit Target]   │              [Reaches Buy-Back Target]
                                       ▼                               ▼
                       ┌────────────────────────┐     ┌────────────────────────┐
                       │ STATE 2A: LOOP A EXIT  │     │ STATE 2B: LOOP B EXIT  │
                       │ Sold BTC back to USDT. │     │ Bought back BTC w/ USDT│
                       │ Outcome: USDT Profits  │     │ Outcome: MORE SATOSHIS │
                       └────────────────────────┘     └────────────────────────┘
                                       │                               │
                                       └───────────────┬───────────────┘
                                                       ▼
                                       ┌───────────────────────────────┐
                                       │   RETURN TO STATE 0 (NEUTRAL) │
                                       │   [Compounded Inventory Base] │
                                       └───────────────────────────────┘
```

---

## 5. Quantitative Gate Mapping

| Engine Gate | Loop A Trigger (USDT ➔ BTC) | Loop B Trigger (BTC ➔ USDT) |
| :--- | :--- | :--- |
| **Gate 1: Lévy Signed Area ($A_{S,P}$)** | $A_{S,P} > 0.0$ (Spot accumulation leads price markup). | $A_{S,P} < 0.0$ (Price markup is unbacked / spot dragging). |
| **Gate 2: CVD Z-Spread ($D_{\text{flow}}$)** | $D_{\text{flow}} \ge +1.0$ (Spot buyers absorb perp selling). | $D_{\text{flow}} \le -1.0$ (Spot whales distributing to perp retail). |
| **Gate 3: Volume Profile Structure** | 12H Sweep & Reclaim of $VAL_{30}$ or $L_{20}$. | 12H Sweep & Rejection of $VAH_{30}$ or $H_{20}$. |
| **Gate 4: 90D Funding Percentile** | Flushed: $F \le 0.0\%$ or $P90 < 25.0\%$ (Clean slate). | Euphoric: $P90 > 75.0\%$ or $> 85.0\%$ (Crowded long trap). |

---

*Authored and verified for the BTC Swing Engine ecosystem.*
