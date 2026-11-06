# Termius Mobile SSH Setup Guide (Founder Quant Cockpit)

This guide walks you through setting up **Termius** (available for iOS and Android) to monitor and control your **BTC Swing Engine** 24/7 on the Google Cloud Free Tier VM (`e2-micro`).

---

## 1. Why Setup A (Termius Mobile Landscape) is Optimal

```
┌────────────────────────────────────────────────────────────────────────┐
│                        TERMIUS MOBILE LANDSCAPE                        │
│                                                                        │
│   [P: STRUCTURE]  [F: FOOTPRINT]  [W: WATERFALL]  [0: SCREENER] [L]    │
│   BTC Spot: $76,144 │ Regime: BALANCED (39/100) │ Feeds: Spot ON Perp  │
│   ──────────────────────────────────────────────────────────────────   │
│   [1] SLSP v1.0        [2] Industrial 3-EMA    [3] Liq Flush           │
│   Shelf: $76,121 (4★)  Slope: +21.5% (4H Band) Quiet ($1.5M/24h)      │
│   Obstacle: 2.7R       3/3 Confluence: YES     Demand: +0.54% Floor    │
│   ──────────────────────────────────────────────────────────────────   │
│   BOTTOM LINE: DO NOT BUY YET — STAY PATIENT IN 100% CASH              │
│                                                                        │
│   [ P ]     [ F ]     [ W ]     [ 0 ]     [ L ]     [ C: PACKET ]      │
│   <──────────────── One-Thumb Mobile Action Bar ───────────────>      │
└────────────────────────────────────────────────────────────────────────┘
```

1. **Zero Latency**: Direct SSH connection to Google Cloud datacenter backbone.
2. **True Bloomberg Feel**: Full Rich 256-color TUI renders at 60 FPS in landscape mode.
3. **One-Thumb Switching**: Instant hotkey buttons on your phone screen cycle desks in 0.0 seconds.
4. **Zero Battery Drain**: The computation runs on Google Cloud, not on your phone battery.

---

## 2. Termius Connection Configuration

### Step 1: Add New Host in Termius
1. Open **Termius** on your phone.
2. Tap **+** -> **New Host**.
3. Fill in the connection parameters:
   - **Label**: `GCP-BTC-Engine`
   - **Hostname (IP)**: Your Google Cloud VM External IP (e.g. `34.122.xx.xx`)
   - **Port**: `22`
   - **Username**: `ubuntu`
   - **Key / Password**: Select your SSH key or enter password.

### Step 2: Terminal Settings (For Best Visuals)
Under the host's **Terminal** settings:
- **Terminal Type**: `xterm-256color`
- **Font Size**: `10` or `11` (ensures 120+ columns in landscape mode without zooming)
- **Font Family**: `Menlo`, `Fira Code`, or `DejaVu Sans Mono`
- **Auto-Capitalization**: OFF

---

## 3. Configuring the "One-Thumb" Quick-Action Bar

Termius allows you to add custom on-screen snippet buttons so you never have to pull up the full on-screen keyboard.

Go to **Termius Settings** -> **Snippets / Quick Access** (or tap the customize icon on the active terminal bar) and add these 6 buttons:

| Button Label | Keystroke Sent | Description |
|:---|:---:|:---|
| **`[ P ]`** | `p` | **Tab [P]**: Structure & SLSP v1.0 (Primary Execution Desk) |
| **`[ F ]`** | `f` | **Tab [F]**: Footprint & Delta Absorptions (Intraday Tape) |
| **`[ W ]`** | `w` | **Tab [W]**: Waterfall & CoinGlass Liquidation Depth |
| **`[ 0 ]`** | `0` | **Tab [0]**: Spot Swing Macro Screener & 1:3 RRR |
| **`[ L ]`** | `l` | **Tab [L]**: Master Multi-Desk Rollup Command Center |
| **`[ C ]`** | `c` | **AI Export**: Instant generation of Section 13 AI Packet |

---

## 4. How to Connect & Re-Attach on Mobile

1. Open Termius and tap **`GCP-BTC-Engine`**.
2. Run the persistent runner script:
   ```bash
   bash deploy/run_tmux.sh
   ```
3. The engine TUI will immediately take over the screen.
4. Rotate your phone into **Landscape Mode**.
5. Tap **`[P]`**, **`[F]`**, **`[W]`**, **`[0]`**, or **`[L]`** at any time to switch views.
6. When done, you can safely swipe the Termius app away or disconnect. The engine continues running 24/7 inside `tmux` on Google Cloud!
7. When you open Termius later, simply tap your host and run:
   ```bash
   tmux attach -t btc_engine
   ```
   You will instantly resume exactly where you left off.
