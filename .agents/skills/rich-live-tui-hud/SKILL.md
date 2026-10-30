---
name: rich-live-tui-hud
description: >-
  Builds real-time, self-updating retro IBM/Bloomberg-style Terminal User Interface
  Heads-Up Displays (Rich Live TUI HUDs) in Python using asyncio and rich.live.Live.
  Activate whenever the user asks to build a live terminal dashboard, TUI monitor,
  real-time telemetry HUD, or asks for a dashboard that looks and operates like
  btc_swing_engine.
---

# Rich Live TUI HUD (Retro IBM / Bloomberg Mainframe Telemetry Standard)

## Overview

This skill codifies the user's preferred architecture and visual design for real-time terminal dashboards, modeled after the reference implementation at `C:\Users\aikel\.gemini\antigravity\scratch\btc_swing_engine` ([`ui/terminal_hud.py`](file:///C:/Users/aikel/.gemini/antigravity/scratch/btc_swing_engine/ui/terminal_hud.py) and [`main.py`](file:///C:/Users/aikel/.gemini/antigravity/scratch/btc_swing_engine/main.py)).

Whenever the user asks to build a live dashboard, market monitor, or telemetry HUD in this style, follow the four architectural rules below.

---

## 1. Startup Sequence: Zero-Cold-Start Historical Backfill (`[1/3] -> [2/3] -> [3/3]`)

Never launch a live dashboard with empty `0.0` rolling metrics. Always execute a 3-step startup sequence in `main.py`:

1. `[1/3] Running Zero-Cold-Start Historical Backfill...` — Concurrently fetch historical REST data to warm up all rolling windows, Z-scores, and structural levels from second zero.
2. `[2/3] Warmup complete! Loaded ...` — Print a summary of loaded historical bars/records and run an initial evaluation pass.
3. `[3/3] Launching Live Terminal HUD...` (or `--dry-run --duration 15` verification mode that streams live data for 15 seconds, prints a static full-width audit report via `Console(width=145, force_terminal=True)`, logs JSONL state, and exits cleanly).

Ensure Windows UTF-8 terminal compatibility at startup:
```python
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
```

---

## 2. Four Synchronized `asyncio` Update Loops (No Manual Refresh Needed)

The dashboard must continuously update itself in real time without user intervention by running four synchronized loops sharing a central `StateStore`:

1. **Loop 1 — Real-Time WebSocket Streamers (Millisecond Tick-by-Tick)**:
   - Resilient `websockets.connect(..., ping_interval=20, ping_timeout=20)` consumers with exponential backoff, stall watchdogs, and automatic mirror/fallback endpoints.
   - Update both session accumulators and the developing tip of rolling time-bucketed bars in `O(1)` memory.
2. **Loop 2 — Screen Redraw & Decision Brain (`2 Hz` / Every `0.5s`)**:
   - Uses `rich.live.Live(..., refresh_per_second=2.0, screen=False)` to evaluate the state machine and overwrite the terminal in-place twice per second without scrolling or flickering.
3. **Loop 3 — Periodic REST Poller (Every `15s`)**:
   - Polls snapshot metrics that are not streamed tick-by-tick (e.g., Open Interest, Funding Rates, positioning ratios) safely within rate limits.
4. **Loop 4 — Historical Candle/Window Sync (Every `60s`)**:
   - Re-synchronizes rolling historical bar buffers with official REST endpoints so structural boundaries never drift.

---

## 3. Five-Panel Retro IBM / Bloomberg Layout Geometry

Use `rich.box.ROUNDED` for outer `Panel` borders and `rich.box.SIMPLE_HEAVY` for inner `Table` grids. Keep vertical height compact (~35–42 rows) so `rich.live.Live` never overflows the terminal window:

1. **Top Status Banner (`Panel` with 3-column `Table.grid`)**:
   - Left: `[bold white]<SYSTEM TITLE>[/bold white] | YYYY-MM-DD HH:MM:SS UTC`
   - Center: `Regime: <COLORED BADGE> | Score: XX.X / 100`
   - Right: `Feeds: <Feed1> ONLINE • <Feed2> ONLINE • <Feed3> ONLINE`
2. **Panels 1 & 2 Side-by-Side (`Table.grid(expand=True, padding=(0, 1))` with two `ratio=1` columns)**:
   - **Panel 1 (Left — Cyan Title)**: Primary health, cross-venue pricing, basis spreads, and positioning state.
   - **Panel 2 (Right — Magenta Title)**: Multi-horizon structural levels (e.g., `30D Macro`, `7D Tactical`, `24H Developing`).
3. **Panel 3 (Full-Width — Green Title)**:
   - Multi-horizon quantitative matrix (`15m`, `1H`, `4H`, `24H`, `UTC Day`, `Live WS Session`) showing raw deltas, normalized Z-scores, divergence SDs, and flow signatures.
4. **Panel 4 (Full-Width — Yellow Title, 2-Column `Table.grid` with `ratio=3` and `ratio=2`)**:
   - Left Column: `Active Gate State`, `Confluence Breakdown` (`0–100` across sub-gates), bulleted gate rationales, and any red `[bold red]• VETO: ...[/bold red]` kill-switches.
   - Right Column: Exact execution & risk geometry (`Entry Zone`, `Hard Invalidation / Stop`, `TP1` & `TP2` with `R` multiples, and `Position Size`).
5. **Panel 5 (Full-Width — `5. Executive Bottom Line (Plain-English Quick Glance)`)**:
   - Translates all quantitative metrics into a 2-second plain-English readout with dynamic border color (`green`, `cyan`, `yellow`, `red`, or `bright_black`):
     - **Line 1 (Traffic-Light Banner)**:
       - `[bold black on green] GREEN LIGHT — ... [/bold black on green]`
       - `[bold black on cyan] BLUE LIGHT — ... [/bold black on cyan]`
       - `[bold black on yellow] YELLOW LIGHT — ... [/bold black on yellow]`
       - `[bold white on red] RED LIGHT — ... [/bold white on red]`
       - `[bold white] STANDBY — ... [/bold white]`
     - **Line 2 (`What's Happening :`)**: Plain-English summary of current price vs. structure and who is driving the move.
     - **Line 3 (`Why / Risk Check :`)**: Plain-English explanation of supporting flows or blocking vetoes.
     - **Line 4 (`Your Next Move   :`)**: Unambiguous instruction on what to do right now (sit in cash, wait for a specific level/turn, or execute with exact numbers).

---

## Reference Implementation Files

Before scaffolding a new dashboard in this style, inspect:
- Reference UI & Panel 5 builder: [`C:\Users\aikel\.gemini\antigravity\scratch\btc_swing_engine\ui\terminal_hud.py`](file:///C:/Users/aikel/.gemini/antigravity/scratch/btc_swing_engine/ui/terminal_hud.py)
- Reference Asyncio Orchestrator: [`C:\Users\aikel\.gemini\antigravity\scratch\btc_swing_engine\main.py`](file:///C:/Users/aikel/.gemini/antigravity/scratch/btc_swing_engine/main.py)
- Reference StateStore: [`C:\Users\aikel\.gemini\antigravity\scratch\btc_swing_engine\core\state_store.py`](file:///C:/Users/aikel/.gemini/antigravity/scratch/btc_swing_engine/core/state_store.py)
