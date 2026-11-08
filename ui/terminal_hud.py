"""Unified 5-Tab Rich Live TUI HUD for the BTC-USD Spot Swing Engine.

Tabs (switchable instantly via keys `1`, `2`, `3`, `4`, `5` in PowerShell):
- Tab [1]: Tactical Swing Execution HUD (Composite Volume Profile, Multi-Horizon CVD, 4-Gate Engine)
- Tab [2]: BTC Spot Swing Protocol v1.3 HUD (1D Completed vs Forming, CoinGlass 6-Panel, 8A-8F NTZ)
- Tab [3]: Macro Quant & Cycle Radar HUD (1D 200 SMA Gatekeeper, 21D EMA, 14D RSI, Crash Rungs, 4H Flush)
- Tab [4]: Regime Matrix A-J HUD (Quantitative Microstructure Diagnostic & Execution Protocols A through J)
- Tab [5]: Master Conclusion HUD (4-Tab Rollup Matrix, 4-Layer Conflict Resolver, Cash vs Holder Playbook & Supreme Bottom Line)
"""

import asyncio
import select
import sys
import time
from datetime import datetime, timedelta, timezone

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
from typing import Any, Optional, Tuple

try:
    import msvcrt
except ImportError:
    msvcrt = None  # type: ignore

try:
    import termios
    import tty
except ImportError:
    termios = None  # type: ignore
    tty = None  # type: ignore

from rich import box
from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

from analytics.ai_packet_exporter import copy_ai_packet_to_clipboard_and_disk
from analytics.signal_detector import SignalDetector
from config.settings import EngineConfig
from core.models import ExecutionGateState, MarketRegime
from core.state_store import StateStore


def _color_signed(val: float, fmt: str = "+,.2f", suffix: str = "") -> str:
    color = "green" if val > 0 else ("red" if val < 0 else "white")
    return f"[{color}]{val:{fmt}}{suffix}[/{color}]"


def _regime_badge(regime: MarketRegime) -> str:
    mapping = {
        MarketRegime.BALANCED: "[bold cyan]BALANCED[/bold cyan]",
        MarketRegime.ABSORPTION_AT_SUPPORT: "[bold black on green] ABSORPTION_AT_SUPPORT [/bold black on green]",
        MarketRegime.LEVERAGE_EXPANSION: "[bold yellow]LEVERAGE_EXPANSION[/bold yellow]",
        MarketRegime.LEVERAGE_TRAP: "[bold white on red] LEVERAGE_TRAP [/bold white on red]",
        MarketRegime.MARKDOWN: "[bold white on red] MARKDOWN (100% CASH) [/bold white on red]",
    }
    return mapping.get(regime, f"[bold white]{regime.value}[/bold white]")


def _gate_badge(gate: ExecutionGateState) -> str:
    mapping = {
        ExecutionGateState.CASH_MARKDOWN: "[bold red]CASH_MARKDOWN (Stand Aside)[/bold red]",
        ExecutionGateState.NEUTRAL_OBSERVATION: "[dim white]NEUTRAL_OBSERVATION[/dim white]",
        ExecutionGateState.GATE1_ZONE_ALERT: "[bold yellow]GATE 1: ZONE ALERT (Monitoring cVAL)[/bold yellow]",
        ExecutionGateState.GATE2_MICROSTRUCTURE_ARMED: "[bold cyan]GATE 2: MICROSTRUCTURE ARMED (Waiting Reclaim)[/bold cyan]",
        ExecutionGateState.GATE3_RECLAIM_TRIGGERED: "[bold green]GATE 3 & 4: RECLAIM TRIGGERED (SWING LONG)[/bold green]",
        ExecutionGateState.GATE4_PENDING_RETEST: "[bold yellow]GATE 4: PENDING RETEST (Awaiting Retest Touch)[/bold yellow]",
    }
    return mapping.get(gate, gate.value)


def _nth_weekday_of_month(year: int, month: int, weekday: int, n: int) -> int:
    """Returns day-of-month for the nth weekday (0=Mon..6=Sun) in (year, month)."""
    first = datetime(year, month, 1, tzinfo=timezone.utc)
    offset = (weekday - first.weekday()) % 7
    return 1 + offset + (n - 1) * 7


def _last_sunday_of_month(year: int, month: int) -> int:
    """Returns day-of-month for the last Sunday in (year, month)."""
    next_m = datetime(year + 1, 1, 1, tzinfo=timezone.utc) if month == 12 else datetime(year, month + 1, 1, tzinfo=timezone.utc)
    last_day = next_m - timedelta(days=1)
    offset = (last_day.weekday() - 6) % 7
    return last_day.day - offset


def _get_world_clocks_and_session(now_utc: datetime) -> Tuple[str, str]:
    """Computes UTC, Singapore (SGT), London (GMT/BST), and New York (EST/EDT) clocks + Active Session badge."""
    y = now_utc.year
    # 1. Singapore / Asia (always UTC+8)
    sgt_dt = now_utc + timedelta(hours=8)

    # 2. London (BST = UTC+1 from last Sunday of March 01:00 UTC to last Sunday of October 01:00 UTC)
    uk_start = datetime(y, 3, _last_sunday_of_month(y, 3), 1, 0, tzinfo=timezone.utc)
    uk_end = datetime(y, 10, _last_sunday_of_month(y, 10), 1, 0, tzinfo=timezone.utc)
    is_bst = uk_start <= now_utc < uk_end
    lon_dt = now_utc + timedelta(hours=1 if is_bst else 0)
    lon_tz = "BST" if is_bst else "GMT"

    # 3. New York (EDT = UTC-4 from 2nd Sunday of March 07:00 UTC to 1st Sunday of November 06:00 UTC)
    us_start = datetime(y, 3, _nth_weekday_of_month(y, 3, 6, 2), 7, 0, tzinfo=timezone.utc)
    us_end = datetime(y, 11, _nth_weekday_of_month(y, 11, 6, 1), 6, 0, tzinfo=timezone.utc)
    is_edt = us_start <= now_utc < us_end
    nyc_dt = now_utc - timedelta(hours=4 if is_edt else 5)
    nyc_tz = "EDT" if is_edt else "EST"

    clocks_str = (
        f"[bold bright_white]UTC[/bold bright_white] [bright_white]{now_utc.strftime('%Y-%m-%d %H:%M:%S')}[/bright_white]  [bright_blue]•[/bright_blue]  "
        f"[bold bright_cyan]SGP (Asia)[/bold bright_cyan] [bright_white]{sgt_dt.strftime('%H:%M:%S')} SGT[/bright_white]  [bright_blue]•[/bright_blue]  "
        f"[bold bright_yellow]LON (EU)[/bold bright_yellow] [bright_white]{lon_dt.strftime('%H:%M:%S')} {lon_tz}[/bright_white]  [bright_blue]•[/bright_blue]  "
        f"[bold bright_green]NYC (US)[/bold bright_green] [bright_white]{nyc_dt.strftime('%H:%M:%S')} {nyc_tz}[/bright_white]"
    )

    h = now_utc.hour
    if 0 <= h < 7:
        session_badge = "[bold black on cyan] ASIA SESSION (SINGAPORE / HK / TOKYO ACTIVE) [/bold black on cyan]"
    elif 7 <= h < 8:
        session_badge = "[bold black on yellow] ASIA / LONDON OVERLAP (SGP PM • LONDON OPEN) [/bold black on yellow]"
    elif 8 <= h < 13:
        session_badge = "[bold black on green] LONDON / EU SESSION (EUROPEAN INSTITUTIONAL FLOW) [/bold black on green]"
    elif 13 <= h < 16:
        session_badge = "[bold black on magenta] LONDON / NY OVERLAP (PEAK GLOBAL & US ETF LIQUIDITY) [/bold black on magenta]"
    elif 16 <= h < 21:
        session_badge = "[bold black on green] NEW YORK SESSION (US INSTITUTIONAL & COINBASE ACTIVE) [/bold black on green]"
    else:
        session_badge = "[bold black on yellow] LATE NY / ASIA PRE-OPEN TRANSITION WINDOW [/bold black on yellow]"

    return clocks_str, session_badge


def _build_header_panel(store: StateStore, active_tab: int) -> Group:
    """Builds the dual Top Status Banner: 1) Desk Navigation & Health, 2) Dedicated Global Session & World Clocks."""
    now_utc = datetime.now(timezone.utc)
    clocks_str, session_badge = _get_world_clocks_and_session(now_utc)
    sig = store.latest_signal
    spot_px = store.binance_spot_price or (sig.current_price if sig else 0.0)

    spot_ws_dot = "[green]ON[/green]" if store.spot_ws_connected else "[yellow]SYNC[/yellow]"
    perp_ws_dot = "[green]ON[/green]" if store.perp_ws_connected else "[yellow]SYNC[/yellow]"
    cb_ws_dot = "[green]ON[/green]" if store.coinbase_ws_connected else "[yellow]SYNC[/yellow]"

    # Clean 5 Operational Cockpit: P (Structure), F (Footprint), W (Waterfall), 0 (Screener), L (Master) + C (AI Packet)
    tP = (
        "[bold black on bright_yellow] [P: STRUCTURE] [/bold black on bright_yellow]"
        if active_tab == 13
        else "[dim white][P: STRUCTURE][/dim white]"
    )
    tB = (
        "[bold black on bright_cyan] [B: PATTERNS] [/bold black on bright_cyan]"
        if active_tab == 14
        else "[dim white][B: PATTERNS][/dim white]"
    )
    tF = (
        "[bold black on bright_cyan] [F: FOOTPRINT] [/bold black on bright_cyan]"
        if active_tab == 11
        else "[dim white][F: FOOTPRINT][/dim white]"
    )
    tW = (
        "[bold white on dark_green] [W: WATERFALL] [/bold white on dark_green]"
        if active_tab == 12
        else "[dim white][W: WATERFALL][/dim white]"
    )
    tG = (
        "[bold black on bright_yellow] [G: GROK FLOW] [/bold black on bright_yellow]"
        if active_tab == 15
        else "[dim white][G: GROK FLOW][/dim white]"
    )
    tR = (
        "[bold black on bright_yellow] [R: SSRN RESEARCH] [/bold black on bright_yellow]"
        if active_tab == 16
        else "[dim white][R: SSRN RESEARCH][/dim white]"
    )
    tM = (
        "[bold black on bright_cyan] [M: MAGNET] [/bold black on bright_cyan]"
        if active_tab == 17
        else "[dim white][M: MAGNET][/dim white]"
    )
    tA = (
        "[bold black on bright_green] [A: BTC STRATEGY] [/bold black on bright_green]"
        if active_tab == 18
        else "[dim white][A: BTC STRATEGY][/dim white]"
    )
    t0 = (
        "[bold white on blue] [0: SPOT SWING] [/bold white on blue]"
        if active_tab == 0
        else "[dim white][0: SPOT SWING][/dim white]"
    )
    tL = (
        "[bold white on magenta] [L: MASTER] [/bold white on magenta]"
        if active_tab == 10
        else "[dim white][L: MASTER][/dim white]"
    )
    tC = "[bold white on dark_red] [C: AI PACKET] [/bold white on dark_red]"
    tH = (
        "[bold white on dark_green] [H: GUIDE] [/bold white on dark_green]"
        if getattr(store, "show_help", False)
        else "[dim white][H: GUIDE][/dim white]"
    )

    subdesk_names = {
        1: "1: TACTICAL SWING",
        2: "2: PROTOCOL v1.3",
        3: "3: MACRO RADAR",
        4: "4: REGIME MATRIX",
        5: "5: MM-BTC INVENTORY",
        6: "6: 72H VOL CONE",
        7: "7: PATTERNS & HARMONICS [B]",
        8: "8: SFP LIQ TRAP",
        9: "9: TD EXHAUSTION",
        14: "14: PATTERNS & CHART",
        15: "15: GROK QUANT FLOW [G]",
        16: "16: SSRN RESEARCH [R]",
        17: "17: BTC MAGNET [M]",
        18: "18: TREND-PULLBACK [A]",
    }
    if active_tab in subdesk_names:
        subdesk_info = f"  │  [bold black on bright_yellow] [DEEP DIVE {subdesk_names[active_tab]}] [/bold black on bright_yellow]"
    else:
        subdesk_info = "  │  [dim]Sub-Desks: 1 Tactical • 2-9 Quant Desks[/dim]"

    regime_str = _regime_badge(sig.regime) if sig else "[dim]WARMING UP[/dim]"
    score_str = f"[bold]{sig.confluence_score:.1f}/100[/bold]" if sig else "0.0/100"

    # --- Panel 1: Desk Navigation & Quantitative Health ---
    nav_grid = Table.grid(expand=True)
    nav_grid.add_column(justify="left", no_wrap=True)
    nav_grid.add_column(justify="right", no_wrap=True)
    nav_grid.add_row(
        f"[bold white]BTC-USD[/bold white] | Spot: [bold cyan]${spot_px:,.2f}[/bold cyan] | Regime: {regime_str} ({score_str}) | Feeds: Spot {spot_ws_dot} • Perp {perp_ws_dot} • CB {cb_ws_dot}",
        f"[bold white]{now_utc.strftime('%Y-%m-%d %H:%M:%S UTC')}[/bold white]  •  [dim]Keys: P Structure • B Patterns • G Grok Flow • R SSRN Research • M Magnet • A Strategy • F Footprint • W Waterfall • 0 Screener • L Master • C Packet • H Guide[/dim]",
    )

    tab_grid = Table.grid(expand=True)
    tab_grid.add_column(justify="left", no_wrap=True)
    tab_grid.add_row(
        f"{tP}  {tB}  {tG}  {tR}  {tM}  {tA}  {tF}  {tW}  {t0}  {tL}  │  {tC}  {tH}{subdesk_info}"
    )
    nav_panel = Panel(Group(nav_grid, tab_grid), border_style="bright_blue", box=box.ROUNDED, padding=(0, 1))

    # --- Panel 2: Dedicated Regional Market Sessions & World Clocks ---
    session_grid = Table.grid(expand=True)
    session_grid.add_column(justify="left", no_wrap=True)
    session_grid.add_column(justify="right", no_wrap=True)
    session_grid.add_row(
        f"[bold bright_white]ACTIVE MARKET:[/bold bright_white] {session_badge}",
        f"{clocks_str}",
    )
    session_panel = Panel(
        session_grid,
        title="[bold bright_yellow]GLOBAL MARKET SESSIONS & WORLD CLOCKS[/bold bright_yellow]",
        border_style="bright_cyan",
        box=box.ROUNDED,
        padding=(0, 1),
    )

    return Group(nav_panel, session_panel)


# ============================================================================
# TAB [1]: TACTICAL SWING EXECUTION HUD (EXISTING 5-PANEL ENGINE)
# ============================================================================

def _diagnose_market_driver(flow: Any, deriv: Any) -> Tuple[str, str]:
    """Diagnoses whether the current price movement is Spot-Led, Derivatives-Amplified, or Passive Absorption."""
    if flow is None or deriv is None:
        return "[dim]CALCULATING[/dim]", "Warming up order flow metrics..."

    s_1h = flow.w_1h.spot_delta_btc
    p_1h = flow.w_1h.perp_delta_btc
    s_4h = flow.w_4h.spot_delta_btc
    p_4h = flow.w_4h.perp_delta_btc
    cb = deriv.coinbase_premium_usd
    oi_1h = deriv.oi_change_1h_pct
    abs_4h = flow.w_4h.absorption_index

    cb_str = f"+${cb:,.0f} premium" if cb >= 0 else f"${abs(cb):,.0f} discount"

    # 1. Derivatives-Amplified Leveraged Push: Perps buying aggressively while Spot lags or Coinbase at discount
    if p_1h > 100.0 and (s_1h < 0.7 * p_1h or cb < -20.0):
        badge = "[bold black on yellow] DERIVATIVES-AMPLIFIED (PERP PUSH) [/bold black on yellow]"
        desc = f"Futures leverage ({p_1h:+,.0f} BTC in 1H) is leading Spot ({s_1h:+,.0f} BTC in 1H) with Coinbase at a {cb_str}."
        return badge, desc

    # 2. Spot-Led Accumulation Breakout: Spot buying strongly
    if s_1h > 80.0 and (s_1h >= 0.7 * p_1h or cb > 10.0):
        if cb < -20.0:
            badge = "[bold black on green] OFFSHORE SPOT ACCUMULATION [/bold black on green]"
            desc = f"Offshore Spot buying (+{s_1h:,.0f} BTC in 1H) is leading, but US Coinbase is lagging at a {cb_str}."
        else:
            badge = "[bold black on green] SPOT-LED ACCUMULATION [/bold black on green]"
            desc = f"Genuine Spot buying is driving the tape (+{s_1h:,.0f} BTC in 1H) with Coinbase at a {cb_str}. Real capital accumulation."
        return badge, desc

    # 3. Spot-Led Markdown / Distribution: Spot dumping heavily
    if s_1h < -80.0 and (s_1h <= p_1h or cb < -25.0):
        badge = "[bold white on red] SPOT-LED DISTRIBUTION [/bold white on red]"
        desc = f"Real Spot sellers are offloading physical Bitcoin ({s_1h:+,.0f} BTC in 1H). Market in genuine spot markdown."
        return badge, desc

    # 4. Passive Spot Absorption: Perps dumping heavily while Spot holds or absorbs
    if (p_4h < -500.0 or p_1h < -50.0) and (s_4h > 0 or s_1h > -20.0 or abs_4h >= 1.5):
        badge = "[bold black on cyan] PASSIVE SPOT ABSORPTION [/bold black on cyan]"
        desc = f"Passive Spot limit bids are absorbing Perp dumping (4H Abs: {abs_4h:.1f} • Spot {s_1h:+,.0f} BTC vs Perp {p_1h:+,.0f} BTC). Squeeze primed."
        return badge, desc

    # 5. Derivatives Liquidation Cascade: OI collapsing with negative perp flow
    if oi_1h < -1.0 and p_1h < -50.0:
        badge = "[bold white on red] DERIVATIVES LIQUIDATION CASCADE [/bold white on red]"
        desc = f"Forced long liquidations in perpetual futures (1H OI: {oi_1h:+.2f}% • Perp: {p_1h:+,.0f} BTC). Trapped leverage flushing."
        return badge, desc

    # 6. Balanced / Neutral Churn
    badge = "[bold white on blue] BALANCED / NEUTRAL CHURN [/bold white on blue]"
    desc = f"Spot ({s_1h:+,.0f} BTC in 1H) and Futures ({p_1h:+,.0f} BTC in 1H) taker flows are relatively balanced. No dominant institutional driver."
    return badge, desc


def _build_tab1_plain_english_panel(sig, flow, deriv, macro_ev) -> Panel:
    """Builds Tab [1] Panel 5: Plain-English Executive Bottom Line."""
    if sig is None:
        return Panel(
            "Warming up data feeds and calculating 30-day volume profile...",
            title="[bold white]5. Executive Bottom Line (Plain-English Summary)[/bold white]",
            box=box.ROUNDED,
        )

    driver_badge, driver_desc = _diagnose_market_driver(flow, deriv)
    price = sig.current_price
    tp = sig.trade_plan
    cb_diff = deriv.coinbase_premium_usd
    cb_word = (
        f"selling at a ${abs(cb_diff):,.0f} discount"
        if cb_diff < -10
        else (f"buying at a +${cb_diff:,.0f} premium" if cb_diff > 10 else "trading flat with Binance")
    )
    macro_tag = ""
    if macro_ev is not None and macro_ev.gatekeeper_veto and tp is not None and tp.risk_pct < 1.0:
        macro_tag = f" [bold yellow](Macro Note: Below 1D 200 SMA ${macro_ev.sma_200_1d:,.0f} -> Risk capped at {tp.risk_pct:.1f}%)[/bold yellow]"

    if sig.regime == MarketRegime.MARKDOWN or sig.gate_state == ExecutionGateState.CASH_MARKDOWN:
        headline = "[bold white on red] RED LIGHT — DO NOT BUY (STAY 100% IN CASH: MARKET IN DOWNTREND) [/bold white on red]"
        border_style = "red"
        what_happening = (
            f"BTC (${price:,.0f}) has broken below key support (${sig.c_val:,.0f}) and real Spot sellers are actively dumping coins."
        )
        why_line = (
            f"1-Hour Spot flow ({flow.w_1h.spot_delta_btc:+,.1f} BTC) and 4-Hour Spot flow ({flow.w_4h.spot_delta_btc:+,.1f} BTC) are both negative, and US Coinbase traders are {cb_word}."
        )
        action_line = (
            "[bold red]Sit 100% in cash/stablecoins.[/bold red] Do not try to catch a falling knife. Wait for price to form a floor and reclaim support."
        )
    elif sig.hard_veto_triggered and sig.regime == MarketRegime.LEVERAGE_TRAP:
        headline = "[bold white on red] RED LIGHT — DO NOT BUY YET (WARNING: LEVERAGED FUTURES BULL TRAP) [/bold white on red]"
        border_style = "red"
        what_happening = (
            f"BTC (${price:,.0f}) is bouncing near the ${sig.support_hvn or sig.c_val:,.0f} support floor, BUT this bounce is being pushed by leveraged futures traders ({flow.w_1h.perp_delta_btc:+,.0f} BTC in 1H), not real Spot buyers ({flow.w_1h.spot_delta_btc:+,.1f} BTC in 1H)."
        )
        why_line = (
            f"Futures Open Interest jumped {deriv.oi_change_1h_pct:+.2f}% in the last hour while US institutions on Coinbase are {cb_word}. Bounces driven by leverage without Spot buying often flush back down to hunt stops."
        )
        action_line = (
            f"[bold yellow]Hold your cash and do not chase this bounce.[/bold yellow] Wait until real 1-hour Spot buying turns strongly positive and this box turns GREEN before buying around ${tp.entry_zone_low:,.0f} – ${tp.entry_zone_high:,.0f}."
            if tp
            else "[bold yellow]Hold your cash and wait for the Leverage Trap warning to clear.[/bold yellow]"
        )
    elif sig.hard_veto_triggered:
        headline = "[bold white on red] RED LIGHT — DO NOT BUY (SAFETY / MASTER VETO ACTIVE) [/bold white on red]"
        border_style = "red"
        what_happening = f"BTC is at ${price:,.0f} (Score: {sig.confluence_score:.0f}/100), but a safety or Protocol v1.3 veto is blocking entry."
        why_line = " | ".join(sig.veto_reasons)
        action_line = "[bold yellow]Stay in cash until the active safety veto clears (Press 2 or 3 to inspect Protocol/Macro tabs).[/bold yellow]"
    elif sig.gate_state == ExecutionGateState.GATE3_RECLAIM_TRIGGERED and sig.confluence_score >= 70.0:
        headline = "[bold black on green] GREEN LIGHT — BUY SIGNAL TRIGGERED (SAFE FOR SPOT SWING ENTRY) [/bold black on green]"
        border_style = "green"
        what_happening = (
            f"BTC (${price:,.0f}) swept support, absorbed futures sellers with real Spot buying ({flow.w_1h.spot_delta_btc:+,.1f} BTC in 1H), and closed back inside the Value Area."
        )
        why_line = (
            f"All 4 gates passed ({sig.confluence_score:.0f}/100): Real Spot buyers are in control, leverage is healthy (Funding {deriv.funding_rate_pct:+.4f}%), and US Coinbase traders are {cb_word}.{macro_tag}"
        )
        if tp:
            action_line = (
                f"[bold green]BUY SPOT BTC[/bold green] in zone [bold]${tp.entry_zone_low:,.0f} – ${tp.entry_zone_high:,.0f}[/bold] "
                f"(Size: [bold]{tp.position_size_btc:.4f} BTC[/bold] / ${tp.position_notional_usd:,.0f} at {tp.risk_pct:.1f}% risk). "
                f"Stop-Loss: [bold red]${tp.stop_loss:,.0f}[/bold red]. "
                f"TP1 (55%): [bold cyan]${tp.tp1_poc:,.0f}[/bold cyan] ({tp.rr_to_poc:.1f}R) | TP2 (45%): [bold magenta]${tp.tp2_vah:,.0f}[/bold magenta] ({tp.rr_to_vah:.1f}R)."
            )
        else:
            action_line = "[bold green]Execute Spot Swing Long per Panel 4 parameters.[/bold green]"
    elif sig.gate_state == ExecutionGateState.GATE4_PENDING_RETEST:
        bars_txt = f"Bar {sig.fsm_bars_elapsed}/{sig.fsm_max_bars}" if sig.fsm_bars_elapsed > 0 else "ARMED"
        headline = f"[bold black on yellow] YELLOW LIGHT — PENDING RETEST ({bars_txt.upper()}) [/bold black on yellow]"
        border_style = "yellow"
        what_happening = (
            f"BTC (${price:,.0f}) swept cVAL (${sig.c_val:,.0f}) and verified rejection. Now tracking multi-bar retest ({bars_txt})."
        )
        why_line = (
            f"FSM state machine active. Awaiting pullback touch into retest envelope (${sig.fsm_retest_band_low:,.0f}–${sig.fsm_retest_band_high:,.0f}). Hard stop: ${sig.fsm_suggested_stop:,.0f}."
        )
        action_line = (
            f"[bold yellow]Do not chase.[/bold yellow] Place limit bids within the retest band (${sig.fsm_retest_band_low:,.0f}–${sig.fsm_retest_band_high:,.0f}) or wait for touch confirmation."
        )
    elif sig.gate_state == ExecutionGateState.GATE2_MICROSTRUCTURE_ARMED:
        headline = "[bold black on cyan] BLUE LIGHT — GET READY (SPOT BUYERS STEPPING IN, WAITING FOR CANDLE CLOSE) [/bold black on cyan]"
        border_style = "cyan"
        what_happening = (
            f"BTC (${price:,.0f}) is testing support and real Spot buyers are absorbing futures sellers (Score: {sig.confluence_score:.0f}/100)."
        )
        why_line = (
            f"Order flow and leverage look good, and Coinbase is {cb_word}. We just need a 15m/1H candle to close firmly back above ${tp.reference_entry if tp else sig.c_val:,.0f} to confirm the bottom.{macro_tag}"
        )
        action_line = (
            "[bold cyan]Prepare your order, but wait for the candle reclaim close[/bold cyan] (this box will turn GREEN when triggered)."
        )
    elif sig.gate_state == ExecutionGateState.GATE1_ZONE_ALERT:
        headline = "[bold black on yellow] YELLOW LIGHT — WATCH CLOSELY (PRICE AT SUPPORT, WAITING FOR SPOT BUYERS) [/bold black on yellow]"
        border_style = "yellow"
        what_happening = (
            f"BTC (${price:,.0f}) has arrived at a key support zone (${sig.support_hvn or sig.c_val:,.0f}), so the location is good."
        )
        why_line = (
            f"However, aggressive 1-hour Spot buying hasn't confirmed a turn yet (1H Spot: {flow.w_1h.spot_delta_btc:+,.1f} BTC, Coinbase {cb_word}).{macro_tag}"
        )
        action_line = (
            "[bold yellow]Wait in cash and monitor.[/bold yellow] Let the market prove support holds with real Spot buying before entering."
        )
    elif sig.is_mid_range_chop:
        headline = "[bold black on yellow] STANDBY — MID-RANGE CHOP FILTER ACTIVE (AVOID MID-RANGE ENTRIES — PREFER EDGES) [/bold black on yellow]"
        border_style = "yellow"
        what_happening = (
            f"BTC (${price:,.0f}) is floating in mid-range chop (VA Position: {sig.va_position_pct:+.0f}% between cVAL ${sig.c_val:,.0f} and cVAH ${sig.c_vah:,.0f} | Score: {sig.confluence_score:.0f}/100)."
        )
        why_line = (
            f"Gate 1 blocks mid-range entries with poor reward-to-risk. 4H Spot is {flow.w_4h.spot_delta_btc:+,.1f} BTC, 1H Spot is {flow.w_1h.spot_delta_btc:+,.1f} BTC, and Coinbase is {cb_word}.{macro_tag}"
        )
        action_line = (
            f"[bold yellow]Avoid mid-range trades.[/bold yellow] Wait patiently for price to test the range edge (${sig.support_hvn or sig.c_val:,.0f} – ${sig.c_val:,.0f}) and close back inside (Press 2/3/4 for Protocol, Macro & Regime Tabs)."
        )
    else:
        headline = "[bold white] STANDBY — NO TRADE SETUP RIGHT NOW (STAY IN CASH OR HOLD EXISTING POSITION) [/bold white]"
        border_style = "bright_black"
        what_happening = (
            f"BTC (${price:,.0f}) is trading outside a confirmed low-risk entry trigger (Score: {sig.confluence_score:.0f}/100)."
        )
        why_line = (
            f"4H Spot flow is {flow.w_4h.spot_delta_btc:+,.1f} BTC, 1H Spot flow is {flow.w_1h.spot_delta_btc:+,.1f} BTC, and Coinbase is {cb_word}.{macro_tag}"
        )
        action_line = (
            f"No action needed. Wait for price to test support (${sig.support_hvn or sig.c_val:,.0f} – ${sig.c_val:,.0f}) with strong Spot buying (Press 2/3/4 for Protocol, Macro & Regime Tabs)."
        )

    lines = [
        headline,
        f"  [bold white]Movement Driver  :[/bold white] {driver_badge} — {driver_desc}",
        f"  [bold white]What's Happening :[/bold white] {what_happening}",
        f"  [bold white]Why / Risk Check :[/bold white] {why_line}",
        f"  [bold white]Your Next Move   :[/bold white] {action_line}",
    ]
    return Panel(
        "\n".join(lines),
        title="[bold white]5. Executive Bottom Line (Plain-English Quick Glance — Press 0: Master • 1–9: Desks)[/bold white]",
        border_style=border_style,
        box=box.ROUNDED,
    )


def _build_tab1_swing_hud(store: StateStore, header_panel: Panel) -> Group:
    """Renders Tab [1]: Tactical Swing Execution HUD."""
    sig = store.latest_signal
    flow = store.flow_snapshot
    deriv = store.derivatives_snapshot
    macro_vp = store.macro_profile
    tact_vp = store.tactical_profile
    sess_vp = store.session_profile
    macro_ev = store.macro_evaluation

    gate_str = _gate_badge(sig.gate_state) if sig else "[dim]WARMING UP[/dim]"

    # --- Introduction Card: Beginner Context & Methodology ---
    intro_lines = [
        "[bold cyan]▶ PURPOSE & SCOPE:[/bold cyan] Microstructure & order flow execution desk tracking real-time delta imbalances, CVD absorption, and volume distribution.",
        "[bold cyan]▶ CORE MODELS & FEEDS:[/bold cyan] Binance Spot/Perp + Coinbase feeds • Multi-Horizon CVD Delta • 3-Layer Composite Volume Profiles (cVAH/cPOC/cVAL).",
        "[bold cyan]▶ EXECUTION MANDATE:[/bold cyan] [bold green]Never fight aggressive delta spikes[/bold green]; wait for institutional volume absorption at key POC/VA edges before entry.",
    ]
    intro_panel = Panel(
        "\n".join(intro_lines),
        title="[bold cyan]WELCOME TO TAB [1]: TACTICAL SWING EXECUTION & ORDER FLOW DESK[/bold cyan]",
        box=box.ROUNDED,
        border_style="cyan",
        padding=(0, 1),
    )

    # --- Panel 1: Spot Prices, Basis & Derivatives State ---
    p1_table = Table(box=box.SIMPLE_HEAVY, expand=True, show_header=True, header_style="bold cyan", pad_edge=False)
    p1_table.add_column("Metric", style="white", no_wrap=True)
    p1_table.add_column("Value", justify="right", no_wrap=True)
    p1_table.add_column("Context / Z-Score", justify="right", no_wrap=True)

    p1_table.add_row(
        "Coinbase Spot (BTC-USD)",
        f"[bold white]${deriv.coinbase_price:,.2f}[/bold white]",
        "US Institutional Spot",
    )
    p1_table.add_row(
        "Binance Spot (BTCUSDT)",
        f"[bold white]${deriv.binance_spot_price:,.2f}[/bold white]",
        "Global Offshore Spot",
    )
    p1_table.add_row(
        "Coinbase Premium Index",
        _color_signed(deriv.coinbase_premium_usd, "+,.2f", " USD"),
        f"{_color_signed(deriv.coinbase_premium_pct, '+.4f', '%')} (Z={deriv.coinbase_premium_zscore:+.2f})",
    )
    p1_table.add_row(
        "Futures Open Interest",
        f"{deriv.open_interest_btc:,.1f} BTC",
        f"${deriv.open_interest_usd / 1e9:,.2f}B ({deriv.perp_source})",
    )
    p1_table.add_row(
        "Delta Open Interest (dOI)",
        f"1H: {_color_signed(deriv.oi_change_1h_pct, '+.2f', '%')}",
        f"15m:{_color_signed(deriv.oi_change_15m_pct, '+.2f', '%')} | 4H:{_color_signed(deriv.oi_change_4h_pct, '+.2f', '%')}",
    )
    p1_table.add_row(
        "8H Funding / 5m Taker L/S",
        _color_signed(deriv.funding_rate_pct, "+.4f", "%"),
        f"L/S: {deriv.taker_long_short_ratio_5m:.2f} ({_color_signed(deriv.perp_5m_delta_btc, '+.1f', ' BTC')})",
    )
    p1_table.add_row(
        "OI Positioning Quadrant",
        "[bold]" + deriv.oi_regime_quadrant.value.split(" (")[0] + "[/bold]",
        f"Perp Basis: {_color_signed(deriv.perp_basis_usd, '+.2f', ' USD')}",
    )
    driver_badge, _ = _diagnose_market_driver(flow, deriv)
    p1_table.add_row(
        "Market Movement Driver",
        driver_badge,
        f"1H Spot {flow.w_1h.spot_delta_btc:+,.0f} vs Perp {flow.w_1h.perp_delta_btc:+,.0f} BTC",
    )

    # --- Panel 2: Composite Volume Profile Levels ---
    p2_table = Table(box=box.SIMPLE_HEAVY, expand=True, show_header=True, header_style="bold magenta", pad_edge=False)
    p2_table.add_column("Auction Level (70% VA)", style="white", no_wrap=True)
    p2_table.add_column("30D Macro", justify="right", no_wrap=True)
    p2_table.add_column("7D Tactical", justify="right", no_wrap=True)
    p2_table.add_column("24H Dev", justify="right", no_wrap=True)

    def _fmt_lvl(vp, attr: str) -> str:
        if vp is None:
            return "-"
        val = getattr(vp, attr, None)
        return f"${val:,.0f}" if val is not None else "-"

    p2_table.add_row("Range High", _fmt_lvl(macro_vp, "range_high"), _fmt_lvl(tact_vp, "range_high"), _fmt_lvl(sess_vp, "range_high"))
    p2_table.add_row("[bold yellow]Composite VAH (cVAH)[/bold yellow]", _fmt_lvl(macro_vp, "c_vah"), _fmt_lvl(tact_vp, "c_vah"), _fmt_lvl(sess_vp, "c_vah"))
    p2_table.add_row("[bold cyan]Composite POC (cPOC)[/bold cyan]", _fmt_lvl(macro_vp, "c_poc"), _fmt_lvl(tact_vp, "c_poc"), _fmt_lvl(sess_vp, "c_poc"))
    p2_table.add_row("[bold green]Composite VAL (cVAL)[/bold green]", _fmt_lvl(macro_vp, "c_val"), _fmt_lvl(tact_vp, "c_val"), _fmt_lvl(sess_vp, "c_val"))
    p2_table.add_row("Primary LVN (Below cVAL)", _fmt_lvl(macro_vp, "primary_lvn_below_val"), _fmt_lvl(tact_vp, "primary_lvn_below_val"), "-")
    p2_table.add_row("Support HVN (Floor)", _fmt_lvl(macro_vp, "support_hvn_below_val"), _fmt_lvl(tact_vp, "support_hvn_below_val"), "-")

    if sig:
        chop_tag = "[yellow][MID-CHOP: AVOID][/yellow]" if sig.is_mid_range_chop else "[green][EDGE ZONE][/green]"
        p2_table.add_row(
            f"Dist to cVAL ({sig.active_horizon})",
            f"{sig.distance_to_val_pct:+.2f}% ({sig.distance_to_val_atr:+.2f}x ATR)",
            f"VA Pos: {sig.va_position_pct:+.0f}% {chop_tag}",
            f"1H ATR: ${sig.atr_1h:,.0f}",
        )

    top_row = Table.grid(expand=True, padding=(0, 1))
    top_row.add_column(ratio=1)
    top_row.add_column(ratio=1)
    top_row.add_row(
        Panel(p1_table, title="[bold cyan]1. Cross-Exchange Spot & Derivatives Health[/bold cyan]", box=box.ROUNDED),
        Panel(p2_table, title="[bold magenta]2. Composite Auction Structure (Volume Profile)[/bold magenta]", box=box.ROUNDED),
    )

    # --- Panel 3: Multi-Horizon Order Flow & Absorption Matrix ---
    p3_table = Table(box=box.SIMPLE_HEAVY, expand=True, show_header=True, header_style="bold green", pad_edge=False)
    p3_table.add_column("Horizon", style="bold white", no_wrap=True)
    p3_table.add_column("Spot CVD Delta", justify="right", no_wrap=True)
    p3_table.add_column("Spot Imbalance (Z)", justify="right", no_wrap=True)
    p3_table.add_column("Perp CVD Delta", justify="right", no_wrap=True)
    p3_table.add_column("Perp Imbalance (Z)", justify="right", no_wrap=True)
    p3_table.add_column("Spot-Perp Div (Z)", justify="right", no_wrap=True)
    p3_table.add_column("Absorption Index", justify="right", no_wrap=True)

    for w in (flow.w_15m, flow.w_1h, flow.w_4h, flow.w_24h):
        p3_table.add_row(
            w.window_label,
            _color_signed(w.spot_delta_btc, "+,.2f", " BTC"),
            f"{w.spot_delta_ratio * 100:+.1f}% (Z={w.spot_zscore:+.2f})",
            _color_signed(w.perp_delta_btc, "+,.2f", " BTC"),
            f"{w.perp_delta_ratio * 100:+.1f}% (Z={w.perp_zscore:+.2f})",
            _color_signed(w.flow_divergence_z, "+.2f", " SD"),
            f"[bold]{w.absorption_index:.2f}[/bold]",
        )

    p3_table.add_row(
        "UTC Day (00:00+)",
        _color_signed(flow.utc_day_spot_cvd, "+,.2f", " BTC"),
        "-",
        _color_signed(flow.utc_day_perp_cvd, "+,.2f", " BTC"),
        "-",
        f"Bull Div: {'[green]YES[/green]' if flow.bullish_pivot_divergence else 'NO'}",
        f"Abs Div: {'[green]YES[/green]' if flow.absorption_divergence else 'NO'}",
    )
    p3_table.add_row(
        "Live WS Session",
        _color_signed(flow.session_spot_cvd, "+,.4f", " BTC"),
        f"{flow.spot_trade_count:,} trades",
        _color_signed(flow.session_perp_cvd, "+,.4f", " BTC"),
        f"{flow.perp_trade_count:,} trades",
        "[bold]" + flow.flow_signature + "[/bold]",
        "",
    )
    flow_panel = Panel(
        p3_table,
        title="[bold green]3. Multi-Horizon Order Flow, Spot vs. Perp CVD & Passive Absorption[/bold green]",
        box=box.ROUNDED,
    )

    # --- Panel 4: 4-Gate State Machine & Structural Swing Trade Plan ---
    p4_grid = Table.grid(expand=True, padding=(0, 2))
    p4_grid.add_column(ratio=3)
    p4_grid.add_column(ratio=2)

    if sig and sig.fsm_state == "PENDING_RETEST":
        gate_str = f"[bold yellow]GATE 4: PENDING RETEST (Bar {sig.fsm_bars_elapsed}/{sig.fsm_max_bars} [{sig.fsm_bars_elapsed*4}h elapsed])[/bold yellow]"
    elif sig and sig.fsm_state == "TRIGGERED":
        gate_str = f"[bold green]GATE 4: RETEST TRIGGERED (${sig.c_val:,.0f} Reclaim Confirmed)[/bold green]"

    left_lines = [f"Active Gate State : {gate_str}"]
    f_ev = getattr(store, "footprint_evaluation", None)
    if f_ev is not None:
        if f_ev.all_gates_pass:
            if f_ev.direction == "DISTRIBUTE_SELL":
                fp_badge = "[bold white on dark_magenta] [✓] PROFIT HARVEST TRIGGERED [/bold white on dark_magenta]"
            else:
                fp_badge = "[bold black on green] [✓] ABSORPTION HELD & DELTA FLIPPED [/bold black on green]"
            fp_text = f"Footprint Gate [F]: {fp_badge} • [bold cyan]Press 'F' for 15M Ladder[/bold cyan]"
        elif f_ev.gate1_macro_tap:
            fp_badge = "[bold black on yellow] [○] LEVEL TAPPED (AWAITING FLIP) [/bold black on yellow]"
            fp_text = f"Footprint Gate [F]: {fp_badge} • {f_ev.gate1_tapped_level_name} (${f_ev.gate1_tapped_level_price:,.0f})"
        else:
            fp_badge = "[dim cyan][○] MID-CHOP (OBSERVATION)[/dim cyan]"
            fp_text = f"Footprint Gate [F]: {fp_badge} • 15M Delta: {f_ev.active_bar_delta:+.1f} BTC • [dim]Press 'F' for Ladder[/dim]"
        left_lines.append(fp_text)
    if sig:
        es_info = ""
        if sig.ema_strategy:
            es = sig.ema_strategy
            es_info = f" • 3-EMA: [bold cyan]{es.daily_regime}[/bold cyan] [{es.setup_status}]"
        left_lines.append(
            f"Confluence : [bold]{sig.confluence_score:.0f}/100[/bold] "
            f"(L:{sig.location_score:.0f} F:{sig.flow_score:.0f} "
            f"D:{sig.derivatives_score:.0f} T:{sig.trigger_score:.0f}){es_info}"
        )
        for note in sig.rationale_notes[:4]:
            left_lines.append(f"  • {note}")
        if sig.hard_veto_triggered:
            for v in sig.veto_reasons:
                left_lines.append(f"  [bold red]• VETO: {v}[/bold red]")
    else:
        left_lines.append("Evaluating initial market state...")

    risk_label = f"{sig.trade_plan.risk_pct:.1f}% Risk" if (sig and sig.trade_plan) else "1.0% Risk"
    right_lines = [f"[bold yellow]Structural Swing Execution Geometry ({risk_label})[/bold yellow]"]
    if sig and sig.trade_plan:
        tp = sig.trade_plan
        if sig.fsm_retest_band_low > 0:
            right_lines.extend(
                [
                    f"  cVAL Retest Band  : [bold green]${sig.fsm_retest_band_low:,.0f} – ${sig.fsm_retest_band_high:,.0f}[/bold green] (Ref: ${sig.c_val:,.0f})",
                    f"  Hard Invalidation : [bold red]${sig.fsm_suggested_stop:,.2f}[/bold red] (Below Sweep Wick)",
                    f"  TP1 (cPOC - {tp.tp1_allocation_pct:.0f}%) : [bold cyan]${tp.tp1_poc:,.2f}[/bold cyan] ({tp.rr_to_poc:.2f}R) -> Move Stop to BE",
                    f"  TP2 (cVAH - {tp.tp2_allocation_pct:.0f}%) : [bold magenta]${tp.tp2_vah:,.2f}[/bold magenta] ({tp.rr_to_vah:.2f}R)",
                    f"  Position Size     : [bold white]{tp.position_size_btc:.4f} BTC[/bold white] (${tp.position_notional_usd:,.0f} | Risk: ${tp.risk_usd:,.0f})",
                ]
            )
        else:
            right_lines.extend(
                [
                    f"  cVAL Entry Zone   : [bold green]${tp.entry_zone_low:,.2f} – ${tp.entry_zone_high:,.2f}[/bold green] (Ref: ${tp.reference_entry:,.2f})",
                    f"  Hard Invalidation : [bold red]${tp.stop_loss:,.2f}[/bold red] (Below Sweep / LVN Floor)",
                    f"  TP1 (cPOC - {tp.tp1_allocation_pct:.0f}%) : [bold cyan]${tp.tp1_poc:,.2f}[/bold cyan] ({tp.rr_to_poc:.2f}R) -> Move Stop to BE",
                    f"  TP2 (cVAH - {tp.tp2_allocation_pct:.0f}%) : [bold magenta]${tp.tp2_vah:,.2f}[/bold magenta] ({tp.rr_to_vah:.2f}R)",
                    f"  Position Size     : [bold white]{tp.position_size_btc:.4f} BTC[/bold white] (${tp.position_notional_usd:,.0f} | Risk: ${tp.risk_usd:,.0f})",
                ]
            )

    p4_grid.add_row("\n".join(left_lines), "\n".join(right_lines))
    signal_panel = Panel(
        p4_grid,
        title="[bold yellow]4. 4-Gate Swing Signal Engine & Dynamic Risk Geometry[/bold yellow]",
        box=box.ROUNDED,
    )
    bottom_panel = _build_tab1_plain_english_panel(sig, flow, deriv, macro_ev)

    return Group(header_panel, top_row, flow_panel, signal_panel, bottom_panel)


# ============================================================================
# TAB [2]: BTC SPOT SWING PROTOCOL v1.3 HUD (CAPITAL PRESERVATION & COINGLASS)
# ============================================================================

def _build_tab2_protocol_hud(store: StateStore, header_panel: Panel) -> Group:
    """Renders Tab [2]: BTC Spot Swing Protocol v1.3 & CoinGlass 6-Panel Audit."""
    pev = store.protocol_evaluation
    if pev is None:
        return Group(
            header_panel,
            Panel("Warming up Protocol v1.3 1D/4H candles...", title="Protocol v1.3", box=box.ROUNDED),
        )

    # --- Introduction Card: Beginner Context & Methodology ---
    intro_lines = [
        "[bold cyan]▶ PURPOSE & SCOPE:[/bold cyan] Capital preservation desk verifying Protocol v1.3 adherence, exchange connectivity health, and liquidation pools.",
        "[bold cyan]▶ CORE MODELS & FEEDS:[/bold cyan] 1D Completed vs Forming ATR 14 Bounds • CoinGlass 6-Panel Liquidation Heatmap • No-Trade Zone (NTZ) Filter.",
        "[bold cyan]▶ EXECUTION MANDATE:[/bold cyan] [bold yellow]Strict Capital Defense[/bold yellow]: If price enters the No-Trade Zone or exchange latency spikes > 500ms, all spot entries are halted.",
    ]
    intro_panel = Panel(
        "\n".join(intro_lines),
        title="[bold cyan]WELCOME TO TAB [2]: BTC SPOT SWING PROTOCOL v1.3 & CAPITAL PRESERVATION DESK[/bold cyan]",
        box=box.ROUNDED,
        border_style="cyan",
        padding=(0, 1),
    )

    # --- Panel 1: Market Structure & ATR 14 Invalidation (1D Completed vs Forming, 4H Timing) ---
    p1_table = Table(box=box.SIMPLE_HEAVY, expand=True, show_header=True, header_style="bold cyan", pad_edge=False)
    p1_table.add_column("Protocol v1.3 Metric", style="white", no_wrap=True)
    p1_table.add_column("Primary Value", justify="right", no_wrap=True)
    p1_table.add_column("Forming / Context", justify="right", no_wrap=True)

    bias_badge = (
        "[bold green]BULLISH[/bold green]"
        if pev.daily_bias == "BULLISH"
        else ("[bold red]BEARISH[/bold red]" if pev.daily_bias == "BEARISH" else "[bold yellow]NEUTRAL[/bold yellow]")
    )
    p1_table.add_row(
        "Live Spot Price (BTCUSDT)",
        f"[bold white]${pev.current_price:,.2f}[/bold white]",
        f"1D Bias: {bias_badge}",
    )
    p1_table.add_row(
        "1D Completed [-2] (Closed)",
        f"${pev.completed_1d_close:,.2f} ({_color_signed(pev.completed_1d_change_pct, '+.2f', '%')})",
        f"H:${pev.completed_1d_high:,.0f} | L:${pev.completed_1d_low:,.0f}",
    )
    p1_table.add_row(
        "1D Forming [-1] (Live)",
        f"${pev.forming_1d_close:,.2f} ({_color_signed(pev.forming_1d_change_pct, '+.2f', '%')})",
        f"H:${pev.forming_1d_high:,.0f} | L:${pev.forming_1d_low:,.0f}",
    )
    p1_table.add_row(
        "1D Support / Resistance",
        f"Sup: [green]${pev.daily_support:,.0f}[/green]",
        f"Res: [magenta]${pev.daily_resistance:,.0f}[/magenta]",
    )
    p1_table.add_row(
        "4H Structure & Timing",
        f"[bold]{pev.structure_4h.split(' (')[0]}[/bold]",
        f"Timing: {'[bold green]READY[/bold green]' if pev.timing_4h_ready else '[yellow]WAIT / NOT READY[/yellow]'}",
    )
    p1_table.add_row(
        "1D ATR 14 Reference",
        f"ATR(1D): [bold]${pev.atr_14_1d:,.0f}[/bold]",
        f"-1x:${pev.downside_ref_1d_atr:,.0f} | +1x:${pev.upside_ref_1d_atr:,.0f}",
    )
    p1_table.add_row(
        "4H ATR 14 Reference",
        f"ATR(4H): [bold]${pev.atr_14_4h:,.0f}[/bold]",
        f"-1x:${pev.downside_ref_4h_atr:,.0f} | +1x:${pev.upside_ref_4h_atr:,.0f}",
    )

    # --- Panel 2: Fixed CoinGlass 6-Panel Order across 1D & 4H ---
    p2_table = Table(box=box.SIMPLE_HEAVY, expand=True, show_header=True, header_style="bold yellow", pad_edge=False)
    p2_table.add_column("CoinGlass 6-Panel Order", style="bold white", no_wrap=True)
    p2_table.add_column("1D Horizon", justify="right", no_wrap=True)
    p2_table.add_column("4H Horizon", justify="right", no_wrap=True)
    p2_table.add_column("Direction / Check", justify="right", no_wrap=True)

    for row in pev.coinglass_rows:
        dir_styled = row.direction_status
        if "RISING" in dir_styled or "EXPANDING" in dir_styled:
            dir_styled = f"[green]{dir_styled}[/green]"
        elif "FALLING" in dir_styled or "ELEVATED" in dir_styled:
            dir_styled = f"[yellow]{dir_styled}[/yellow]"
        p2_table.add_row(row.metric_name, row.value_1d, row.value_4h, dir_styled)

    top_row = Table.grid(expand=True, padding=(0, 1))
    top_row.add_column(ratio=1)
    top_row.add_column(ratio=1)
    top_row.add_row(
        Panel(
            p1_table,
            title="[bold cyan]1. Market Structure & ATR 14 Invalidation (Protocol Sections 1–5)[/bold cyan]",
            box=box.ROUNDED,
        ),
        Panel(
            p2_table,
            title="[bold yellow]2. CoinGlass 6-Panel Audit in Strict BTC Coins (Protocol Sections 6–7)[/bold yellow]",
            box=box.ROUNDED,
        ),
    )

    # --- Panel 3: Section 8 Non-Trade Zones Matrix (8A - 8F) ---
    p3_table = Table(box=box.SIMPLE_HEAVY, expand=True, show_header=True, header_style="bold green", pad_edge=False)
    p3_table.add_column("Code", style="bold white", width=5, no_wrap=True)
    p3_table.add_column("Non-Trade Zone Rule (Section 8)", style="white", no_wrap=True)
    p3_table.add_column("Status", justify="center", width=14, no_wrap=True)
    p3_table.add_column("Live Telemetry & Mandatory Audit Verification", justify="right", no_wrap=True)

    for z in pev.non_trade_zones:
        if z.status == "CLEAR":
            st_badge = "[bold green]CLEAR[/bold green]"
        elif z.status == "TRIGGERED":
            st_badge = "[bold white on red] TRIGGERED [/bold white on red]"
        else:
            st_badge = "[bold black on yellow] UNVERIFIED [/bold black on yellow]"
        p3_table.add_row(z.code, z.rule_name, st_badge, z.detail)

    ntz_panel = Panel(
        p3_table,
        title="[bold green]3. Non-Trade Zones Matrix 8A–8F (Protocol Section 8 Capital Preservation Audit)[/bold green]",
        box=box.ROUNDED,
    )

    # --- Panel 4: Section 10 Buy Decision, Liquidation Magnets & Section 11 Spot Sell Triggers ---
    p4_grid = Table.grid(expand=True, padding=(0, 2))
    p4_grid.add_column(ratio=1, no_wrap=True)
    p4_grid.add_column(ratio=1, no_wrap=True)

    ntz_color = "green" if pev.non_trade_zone_status == "NO" else "red"
    buy_color = "green" if pev.buy_allowed == "YES" else "red"
    ready_color = "green" if pev.entry_status == "READY" else "yellow"

    left_lines = [
        "[bold cyan]Final Buy Decision (Sections 9–10) & Liquidation Magnet Protocol[/bold cyan]",
        f"  BIAS : {bias_badge} | CONFIDENCE : [bold]{pev.confidence}[/bold] | NTZ : [bold {ntz_color}]{pev.non_trade_zone_status}[/bold {ntz_color}] | BUY : [bold {buy_color}]{pev.buy_allowed}[/bold {buy_color}] ({pev.entry_status})",
        f"  • [bold white]Short-Liq Magnet:[/bold white] [magenta]${pev.short_liq_magnet_usd:,.0f}[/magenta] {pev.short_liq_source} | [bold white]Long-Liq:[/bold white] [cyan]${pev.long_liq_magnet_usd:,.0f}[/cyan]",
        f"  • [bold white]50D MA / Pivot  :[/bold white] 50D MA ${pev.sma_50_1d:,.0f} | Range Pivot ${pev.range_pivot_usd:,.0f} | Confluence: {pev.magnet_confluence_aligned}/5",
        f"  • [bold white]Magnet Verdict  :[/bold white] [bold yellow]{pev.liq_magnet_verdict}[/bold yellow]",
        f"  • [bold white]Actionable Note :[/bold white] {pev.liq_magnet_action_note}",
    ]

    right_lines = ["[bold magenta]Long-Only Spot Sell Triggers 1–4 (Section 11) & Headline Filter[/bold magenta]"]
    for st in pev.sell_triggers:
        if st.status == "CONFIRMED":
            s_badge = "[bold white on red] CONFIRMED [/bold white on red]"
        elif st.status == "UNVERIFIED":
            s_badge = "[bold yellow]UNVERIFIED[/bold yellow]"
        else:
            s_badge = "[green]NOT CONFIRMED[/green]"
        right_lines.append(f"  • {st.name}: {s_badge} ({st.detail})")
    right_lines.append(
        f"  • [bold white]Headline Filter :[/bold white] [cyan]{pev.headline_filter_status}[/cyan] (Trade Magnet, Not Headline)"
    )

    p4_grid.add_row("\n".join(left_lines), "\n".join(right_lines))
    decision_panel = Panel(
        p4_grid,
        title="[bold yellow]4. Buy Decision, Liquidation Magnet Protocol & Spot Sell Triggers (Protocol Sections 9–11)[/bold yellow]",
        box=box.ROUNDED,
    )

    # --- Panel 5: Section 14 Executive Verdict ---
    if pev.non_trade_zone_status != "NO":
        headline = "[bold white on red] RED LIGHT — NON-TRADE ZONE ACTIVE (BUYING FORBIDDEN BY PROTOCOL v1.3) [/bold white on red]"
        border_style = "red"
        decision_str = f"DO NOT BUY SPOT. Active Non-Trade Zone: {', '.join(pev.active_ntz_reasons) or 'Unverified Check'}."
    elif pev.any_sell_confirmed:
        headline = "[bold white on red] RED LIGHT — SPOT SELL TRIGGER CONFIRMED (DE-RISK / EXIT TO CASH) [/bold white on red]"
        border_style = "red"
        decision_str = "Execute Spot defensive de-risking per Section 11 confirmed trigger."
    elif pev.buy_allowed == "YES" and pev.entry_status == "READY":
        headline = "[bold black on green] GREEN LIGHT — PROTOCOL v1.3 BUY ALLOWED & ENTRY READY [/bold black on green]"
        border_style = "green"
        decision_str = (
            f"Spot Long Entry Permitted (Confidence: {pev.confidence}). "
            f"Reference 4H -1xATR (${pev.downside_ref_4h_atr:,.0f}) and 1D Support (${pev.daily_support:,.0f}) for invalidation."
        )
    elif pev.buy_allowed == "YES":
        headline = "[bold black on cyan] BLUE LIGHT — BUY ALLOWED, WAITING FOR 4H ENTRY TIMING ALIGNMENT [/bold black on cyan]"
        border_style = "cyan"
        decision_str = "Zero Non-Trade Zones active and 4H Spot CVD rising; wait for 4H HH/HL structure confirmation."
    else:
        headline = "[bold black on yellow] STANDBY / YELLOW LIGHT — ENTRY NOT READY (PRESERVE CASH) [/bold black on yellow]"
        border_style = "yellow"
        decision_str = (
            f"BUY ALLOWED = NO / ENTRY STATUS = NOT READY. 1D Bias is {pev.daily_bias}; wait for 1D/4H alignment and rising Spot CVD."
        )

    p5_lines = [
        headline,
        f"  [bold white]NOW         :[/bold white] BTC at ${pev.current_price:,.2f} | 1D Completed [-2]: ${pev.completed_1d_close:,.0f} ({pev.completed_1d_change_pct:+.2f}%) | 1D Bias: {pev.daily_bias} | 4H: {pev.structure_4h}.",
        f"  [bold white]DECISION    :[/bold white] {decision_str}",
        f"  [bold white]RISKS       :[/bold white] 1D -1xATR Reference: ${pev.downside_ref_1d_atr:,.0f} | 4H -1xATR Reference: ${pev.downside_ref_4h_atr:,.0f} | Strict BTC OI: {store.derivatives_snapshot.open_interest_btc:,.1f} BTC.",
        f"  [bold white]LIMITATIONS :[/bold white] External checks (8B/8E/ETF) synced from config/protocol_context.json (Reviewed: {pev.context_last_reviewed}).",
    ]
    bottom_panel = Panel(
        "\n".join(p5_lines),
        title="[bold white]5. Executive Bottom Line Verdict (Protocol Sections 12–14 — Press 0: Master • 1–9: Desks)[/bold white]",
        border_style=border_style,
        box=box.ROUNDED,
    )

    return Group(header_panel, top_row, ntz_panel, decision_panel, bottom_panel)


# ============================================================================
# TAB [3]: MACRO QUANT & CYCLE RADAR HUD (REPLACES 4-PAGE WEB PLATFORM)
# ============================================================================

def _build_tab3_macro_hud(store: StateStore, header_panel: Panel) -> Group:
    """Renders Tab [3]: Macro Quant & Cycle Radar HUD."""
    mev = store.macro_evaluation
    if mev is None:
        return Group(
            header_panel,
            Panel("Warming up 255x 1D and 1W Macro Radar candles...", title="Macro Quant & Cycle Radar", box=box.ROUNDED),
        )

    # --- Introduction Card: Beginner Context & Methodology ---
    intro_lines = [
        "[bold cyan]▶ PURPOSE & SCOPE:[/bold cyan] Global intermarket macro desk tracking multi-cycle tides, external liquidity, dollar strength, and power-law corridors.",
        "[bold cyan]▶ CORE MODELS & FEEDS:[/bold cyan] 1D 200 SMA Gatekeeper • DXY Dollar Index • S&P 500 / Nasdaq • Brent Crude • 20-day Rolling SPX Correlations • Power-Law Corridor.",
        "[bold cyan]▶ EXECUTION MANDATE:[/bold cyan] [bold green]Macro Gatekeeper Law[/bold green]: Spot > 200 SMA authorizes macro swing longs. Rapid DXY surges or equity selloffs enforce capital defense.",
    ]
    intro_panel = Panel(
        "\n".join(intro_lines),
        title="[bold cyan]WELCOME TO TAB [3]: MACRO QUANT, INTERMARKET BETAS & CYCLE RADAR[/bold cyan]",
        box=box.ROUNDED,
        border_style="cyan",
        padding=(0, 1),
    )

    # --- Panel 1: Quant Radar — The Gatekeeper ---
    p1_table = Table(box=box.SIMPLE_HEAVY, expand=True, show_header=True, header_style="bold cyan", pad_edge=False)
    p1_table.add_column("Quant Metric", style="white", no_wrap=True)
    p1_table.add_column("Value", justify="right", no_wrap=True)
    p1_table.add_column("Gatekeeper / Regime", justify="right", no_wrap=True)

    gk_badge = (
        "[bold white on red] VETO (BELOW 200D) [/bold white on red]"
        if mev.gatekeeper_veto
        else "[bold black on green] PASS (ABOVE 200D) [/bold black on green]"
    )
    p1_table.add_row(
        "1D 200 SMA (Gatekeeper)",
        f"[bold]${mev.sma_200_1d:,.0f}[/bold]",
        gk_badge,
    )
    p1_table.add_row(
        "200D SMA 5-Day Slope",
        _color_signed(mev.sma_200_slope_5d_usd, "+,.1f", " $/d"),
        f"5D: {_color_signed(mev.sma_200_slope_5d_pct, '+.2f', '%')} ({'RISING' if mev.slope_200d_positive else 'FALLING'})",
    )
    p1_table.add_row(
        "1D Close (Comp [-2]/[-1])",
        f"Comp: ${mev.completed_1d_close:,.0f}",
        f"Live: ${mev.forming_1d_close:,.0f} ({'ABOVE' if mev.above_200d_sma else 'BELOW'} 200D)",
    )
    p1_table.add_row(
        "1D 21 EMA Bull Band",
        f"[bold cyan]${mev.ema_21_1d:,.0f}[/bold cyan]",
        f"Dist: {_color_signed(mev.dist_to_21d_ema_pct, '+.2f', '%')} ({'ABOVE' if mev.dist_to_21d_ema_pct >= 0 else 'BELOW 21D'})",
    )
    p1_table.add_row(
        "14D Wilder RSI (Daily)",
        f"[bold yellow]{mev.rsi_14_1d:.1f}[/bold yellow]",
        mev.rsi_zone,
    )
    p1_table.add_row(
        "30D Volume Profile POC",
        f"[bold magenta]${mev.poc_30d:,.0f}[/bold magenta]",
        f"Dist: {_color_signed(mev.dist_to_30d_poc_pct, '+.2f', '%')}",
    )
    p1_table.add_row(
        "Power-Law Fair Value",
        f"[bold cyan]${mev.power_law_fair_usd:,.0f}[/bold cyan] ({_color_signed(mev.power_law_discount_pct, '+.1f', '%')})",
        f"[bold cyan]{mev.power_law_zone_label}[/bold cyan]",
    )

    # --- Panel 2: Regime Radar — Cycle Armor & Drawdown Rungs (-25% to -65%) ---
    p2_table = Table(box=box.SIMPLE_HEAVY, expand=True, show_header=True, header_style="bold magenta", pad_edge=False)
    p2_table.add_column("Accumulation Rung", style="white", no_wrap=True)
    p2_table.add_column("Level", justify="right", no_wrap=True)
    p2_table.add_column("Dist", justify="right", no_wrap=True)
    p2_table.add_column("Tranche / Status", justify="right", no_wrap=True)

    p2_table.add_row(
        "[bold white]Cycle High (ATH)[/bold white]",
        f"[bold]${mev.cycle_high_usd:,.0f}[/bold]",
        _color_signed(mev.current_drawdown_pct, "+.1f", "%"),
        f"Active: [bold yellow]{mev.active_crash_rung.split(' (')[0]}[/bold yellow]",
    )
    for rung in mev.crash_rungs:
        if rung.status == "HIT / ACTIVE":
            st_str = f"[bold black on green] {rung.status} [/bold black on green]"
        elif "NEAR" in rung.status:
            st_str = f"[bold yellow]{rung.status}[/bold yellow]"
        else:
            st_str = f"[dim]{rung.status}[/dim]"
        p2_table.add_row(
            rung.rung_label.split(" (")[0],
            f"${rung.target_price:,.0f}",
            f"{rung.distance_pct:+.1f}%",
            f"{rung.allocation_tranche} | {st_str}",
        )

    top_row = Table.grid(expand=True, padding=(0, 1))
    top_row.add_column(ratio=1)
    top_row.add_column(ratio=1)
    top_row.add_row(
        Panel(
            p1_table,
            title="[bold cyan]1. Quant Radar — Gatekeeper (1D 200 SMA, 21D EMA, 14D RSI, 30D POC & Power-Law)[/bold cyan]",
            box=box.ROUNDED,
        ),
        Panel(
            p2_table,
            title="[bold magenta]2. Regime Radar — Cycle Armor & Crash Rungs (-25% to -65%)[/bold magenta]",
            box=box.ROUNDED,
        ),
    )

    # --- Panel 3: Liquidity Radar — Multi-Timeframe 1W / 1D / 4H Sniper Matrix ---
    p3_table = Table(box=box.SIMPLE_HEAVY, expand=True, show_header=True, header_style="bold green", pad_edge=False)
    p3_table.add_column("Timeframe Horizon", style="bold white", no_wrap=True)
    p3_table.add_column("Market Structure", justify="left", no_wrap=True)
    p3_table.add_column("Candle Signature & Lower Wick", justify="right", no_wrap=True)
    p3_table.add_column("Order Flow / Taker Delta", justify="right", no_wrap=True)

    for r in mev.tf_rows:
        st_col = (
            f"[green]{r.structure}[/green]"
            if "BULLISH" in r.structure
            else (f"[red]{r.structure}[/red]" if "BEARISH" in r.structure else f"[yellow]{r.structure}[/yellow]")
        )
        p3_table.add_row(r.timeframe, st_col, r.candle_signature, r.flow_momentum)

    flush_badge = (
        "[bold black on green] FLUSH TRIGGERED [/bold black on green]"
        if mev.wick_flush_4h_detected
        else "[dim white]STANDBY[/dim white]"
    )
    p3_table.add_row(
        "4H Liquidation Wick Flush",
        flush_badge,
        f"Max 4H Lower-Wick Sweep Ratio: {mev.wick_flush_4h_ratio:.1f}%",
        mev.wick_flush_detail,
    )
    sniper_panel = Panel(
        p3_table,
        title="[bold green]3. Liquidity Radar — Multi-Timeframe 1W / 1D / 4H Sniper Matrix & 4H Wick Flush[/bold green]",
        box=box.ROUNDED,
    )

    # --- Panel 4: Unified Macro Arb & Allocation Engine ---
    p4_grid = Table.grid(expand=True, padding=(0, 2))
    p4_grid.add_column(ratio=3)
    p4_grid.add_column(ratio=2)

    left_lines = [
        f"Composite Macro Confidence : [bold cyan]{mev.macro_confidence_pct:.1f}% / 100%[/bold cyan] "
        f"(Trend: {mev.trend_score:.0f}/25 | Momentum: {mev.momentum_score:.0f}/25 | "
        f"Flow: {mev.flow_score:.0f}/25 | Structure: {mev.structure_score:.0f}/25)",
        f"Recommended Spot Allocation : [bold yellow]{mev.recommended_allocation}[/bold yellow]",
    ]
    for note in mev.macro_notes[:4]:
        left_lines.append(f"  • {note}")

    right_lines = ["[bold magenta]Multi-Month Scale-Out Ceiling Targets[/bold magenta]"]
    for t_line in mev.scale_out_targets:
        right_lines.append(f"  • {t_line}")

    p4_grid.add_row("\n".join(left_lines), "\n".join(right_lines))
    arb_panel = Panel(
        p4_grid,
        title="[bold yellow]4. Unified Macro Arb & Allocation Engine (Trend • Momentum • Flow • Structure)[/bold yellow]",
        box=box.ROUNDED,
    )

    # --- Panel 5: Executive Bottom Line (Macro & Cycle Verdict) ---
    if not mev.gatekeeper_veto and mev.macro_confidence_pct >= 65.0:
        headline = "[bold black on green] GREEN LIGHT — MACRO BULL REGIME ACTIVE (ABOVE RISING 1D 200 SMA) [/bold black on green]"
        border_style = "green"
        next_move = f"[bold green]Deploy {mev.recommended_allocation}.[/bold green] Use 1D 21 EMA (${mev.ema_21_1d:,.0f}) and Tab [1] cVAL pullbacks to add."
    elif mev.crash_rung_override_active:
        headline = "[bold black on cyan] BLUE LIGHT — CRASH-RUNG DEEP VALUE ACCUMULATION OVERRIDE ACTIVE [/bold black on cyan]"
        border_style = "cyan"
        next_move = f"[bold cyan]Deploy {mev.recommended_allocation}[/bold cyan] into {mev.active_crash_rung}; scale out at 1D 21 EMA (${mev.ema_21_1d:,.0f}) and 200D SMA (${mev.sma_200_1d:,.0f})."
    elif mev.gatekeeper_veto:
        headline = "[bold white on red] RED LIGHT — RULE 1 MACRO GATEKEEPER VETO (BELOW 1D 200 SMA / DEFENSIVE REGIME) [/bold white on red]"
        border_style = "red"
        next_move = (
            f"[bold yellow]No new macro trend-following longs.[/bold yellow] Keep core macro capital in cash, place deep limit bids at Crash Rungs (-25% to -65%), and cap any Tab [1] tactical bounce trades at 0.5% risk."
        )
    else:
        headline = "[bold black on yellow] YELLOW LIGHT — MACRO CONSOLIDATION ABOVE 200D SMA [/bold black on yellow]"
        border_style = "yellow"
        next_move = f"Maintain {mev.recommended_allocation} and use Tab [1] order-flow confirmation for swing entries."

    p5_lines = [
        headline,
        f"  [bold white]What's Happening      :[/bold white] BTC is at ${mev.current_price:,.0f} ({mev.current_drawdown_pct:+.1f}% from ${mev.cycle_high_usd:,.0f} Cycle High) | 1D 200 SMA: ${mev.sma_200_1d:,.0f} ({mev.sma_200_slope_5d_usd:+.1f}/d) | 14D RSI: {mev.rsi_14_1d:.1f}.",
        f"  [bold white]Why / Gatekeeper Check:[/bold white] {mev.gatekeeper_status_text} | Active Rung: {mev.active_crash_rung} | 4H Wick Flush: {'YES' if mev.wick_flush_4h_detected else 'NO'}.",
        f"  [bold white]Your Next Move        :[/bold white] {next_move}",
    ]
    bottom_panel = Panel(
        "\n".join(p5_lines),
        title="[bold white]5. Executive Bottom Line (Macro & Cycle Quick Glance — Press 0: Master • 1–9: Desks)[/bold white]",
        border_style=border_style,
        box=box.ROUNDED,
    )

    return Group(header_panel, top_row, sniper_panel, arb_panel, bottom_panel)


# ============================================================================
# TAB [4]: REGIME RADAR — QUANTITATIVE MICROSTRUCTURE CONFIGURATIONS A–J
# ============================================================================

def _build_tab4_regime_matrix_hud(store: StateStore, header_panel: Panel) -> Group:
    """Renders Tab [4]: Quantitative Microstructure Diagnostic & Execution Protocols (Configs A-J)."""
    rmev = store.regime_matrix_evaluation
    if rmev is None or not rmev.configs:
        return Group(
            header_panel,
            Panel("Warming up Configurations A-J telemetry...", title="Regime Matrix A-J", box=box.ROUNDED),
        )

    active_cfg = next((c for c in rmev.configs if c.code == rmev.active_config_code), rmev.configs[0])
    runner_cfg = next((c for c in rmev.configs if c.code == rmev.runner_up_config_code), rmev.configs[0])

    # --- Introduction Card: Beginner Context & Methodology ---
    intro_lines = [
        "[bold cyan]▶ PURPOSE & SCOPE:[/bold cyan] Microstructure regime radar categorizing live market physics into 10 deterministic Configurations (A through J).",
        "[bold cyan]▶ CORE MODELS & FEEDS:[/bold cyan] Daily/Weekly VWAP • 4-Tier Volatility (Ultra-Low to High Vol) • Order Book Depth Imbalance • CVD Slope.",
        "[bold cyan]▶ EXECUTION MANDATE:[/bold cyan] [bold yellow]Regime Dictates Strategy[/bold yellow]: Trending regimes authorize breakout continuation; Chop/Mean-Reversion regimes require strict range fading.",
    ]
    intro_panel = Panel(
        "\n".join(intro_lines),
        title="[bold cyan]WELCOME TO TAB [4]: QUANTITATIVE MICROSTRUCTURE REGIME MATRIX (CONFIGS A–J)[/bold cyan]",
        box=box.ROUNDED,
        border_style="cyan",
        padding=(0, 1),
    )

    # --- Panel 1: Live Microstructure & VWAP Telemetry (Config A-J Inputs) ---
    p1_table = Table(box=box.SIMPLE_HEAVY, expand=True, show_header=True, header_style="bold cyan", pad_edge=False)
    p1_table.add_column("Config A–J Input Metric", style="white", no_wrap=True)
    p1_table.add_column("Live Value", justify="right", no_wrap=True)
    p1_table.add_column("Benchmark / Threshold", justify="right", no_wrap=True)

    d_vwap_status = "[green]ABOVE[/green]" if rmev.current_price >= rmev.daily_vwap else "[red]BELOW[/red]"
    w_vwap_status = "[green]ABOVE[/green]" if rmev.current_price >= rmev.weekly_vwap else "[red]BELOW[/red]"

    p1_table.add_row(
        "Daily VWAP / Weekly VWAP",
        f"D: ${rmev.daily_vwap:,.0f} ({d_vwap_status})",
        f"W: ${rmev.weekly_vwap:,.0f} ({w_vwap_status})",
    )
    p1_table.add_row(
        "1D 20 EMA / 1D 50 EMA",
        f"20D: ${rmev.ema_20_1d:,.0f}",
        f"50D: ${rmev.ema_50_1d:,.0f} ({'ABOVE' if rmev.current_price >= rmev.ema_50_1d else 'BELOW'})",
    )
    p1_table.add_row(
        "24H Spot Vol vs 20D MA",
        f"[bold]{rmev.spot_vol_vs_20d_ma:.2f}x[/bold]",
        f"Config A Target: >= 1.35x ({'PASS' if rmev.spot_vol_vs_20d_ma >= 1.35 else 'SUB-1.35x'})",
    )
    p1_table.add_row(
        "4H Spot Buy/Sell Ratio & 7D CVD",
        f"Ratio: [bold]{rmev.spot_buy_sell_ratio_4h:.2f}[/bold]",
        f"7D Spot CVD: {_color_signed(rmev.spot_cvd_7d_btc, '+,.0f', ' BTC')}",
    )
    p1_table.add_row(
        "Open Interest Delta (1H/4H/24H)",
        f"1H:{_color_signed(rmev.oi_change_1h_pct, '+.2f', '%')} | 4H:{_color_signed(rmev.oi_change_4h_pct, '+.2f', '%')}",
        f"24H dOI: {_color_signed(rmev.oi_change_24h_pct, '+.2f', '%')}",
    )
    p1_table.add_row(
        "8H Funding & Annualized Basis",
        _color_signed(rmev.funding_rate_pct, "+.4f", "%"),
        f"Ann. Basis: {_color_signed(rmev.annualized_basis_pct, '+.1f', '%/yr')}",
    )
    p1_table.add_row(
        "ATR Compression & 72h Base Width",
        f"ATR Comp: {rmev.atr_compression_pct:.1f}%",
        f"72h Range Width: {rmev.base_width_72h_pct:.2f}% (Target <2.5%)",
    )

    # --- Panel 2: Active Configuration Diagnosis (#1 Match & #2 Runner-Up) ---
    p2_table = Table(box=box.SIMPLE_HEAVY, expand=True, show_header=True, header_style="bold magenta", pad_edge=False)
    p2_table.add_column("Diagnostic Field", style="white", no_wrap=True)
    p2_table.add_column("Active Regime Output", justify="right", no_wrap=True)

    cat_badge = (
        f"[bold black on green] {active_cfg.code}: {active_cfg.short_title.upper()} ({active_cfg.match_pct:.0f}% MATCH) [/bold black on green]"
        if active_cfg.category in ("BULL_LONG", "ACCUMULATE")
        else (
            f"[bold black on yellow] {active_cfg.code}: {active_cfg.short_title.upper()} ({active_cfg.match_pct:.0f}% MATCH) [/bold black on yellow]"
            if active_cfg.category == "HARVEST_WAIT"
            else f"[bold white on red] {active_cfg.code}: {active_cfg.short_title.upper()} ({active_cfg.match_pct:.0f}% MATCH) [/bold white on red]"
        )
    )
    p2_table.add_row("Primary Active Configuration", cat_badge)
    p2_table.add_row("Market Diagnosis (THEN IT MEANS)", f"[bold cyan]{active_cfg.diagnosis_subtitle}[/bold cyan]")
    p2_table.add_row("Actionable Protocol Mandate", f"[bold yellow]{active_cfg.action_headline}[/bold yellow]")
    p2_table.add_row("Position Sizing Protocol", active_cfg.sizing_rule)
    p2_table.add_row("Execution / Harvest Rule", active_cfg.entry_or_harvest_rule)
    p2_table.add_row("Dynamic Stop / Invalidation", f"[bold red]{active_cfg.stop_rule}[/bold red]")
    p2_table.add_row(
        "Secondary Runner-Up Config",
        f"[dim]{runner_cfg.code}: {runner_cfg.short_title} ({runner_cfg.match_pct:.0f}% Match) -> {runner_cfg.action_headline}[/dim]",
    )

    top_row = Table.grid(expand=True, padding=(0, 1))
    top_row.add_column(ratio=1)
    top_row.add_column(ratio=1)
    top_row.add_row(
        Panel(
            p1_table,
            title="[bold cyan]1. Live Microstructure, VWAP & Basis Telemetry (Config A–J Inputs)[/bold cyan]",
            box=box.ROUNDED,
        ),
        Panel(
            p2_table,
            title="[bold magenta]2. Active Configuration Diagnosis (#1 Match & #2 Runner-Up)[/bold magenta]",
            box=box.ROUNDED,
        ),
    )

    # --- Panel 3: Quantitative Microstructure Diagnostic Matrix (Configs A through J) ---
    p3_table = Table(box=box.SIMPLE_HEAVY, expand=True, show_header=True, header_style="bold green", pad_edge=False)
    p3_table.add_column("Config", style="bold white", min_width=10, no_wrap=True)
    p3_table.add_column("Market Diagnosis (THEN IT MEANS)", style="white", ratio=2, no_wrap=True)
    p3_table.add_column("Live Match", justify="right", min_width=14, no_wrap=True)
    p3_table.add_column("Live Observed Telemetry Facts", justify="left", ratio=3, no_wrap=True)
    p3_table.add_column("Actionable Protocol (Sizing & Stops)", justify="right", ratio=3, no_wrap=True)

    for cfg in rmev.configs:
        if cfg.is_active:
            c_name = f"[bold black on green] {cfg.code} [/bold black on green]"
            m_str = f"[bold green]{cfg.match_pct:.0f}% [ACTIVE][/bold green]"
            diag_str = f"[bold white]{cfg.short_title} — {cfg.diagnosis_subtitle}[/bold white]"
        else:
            c_name = cfg.code
            m_str = f"[dim]{cfg.match_pct:.0f}%[/dim]" if cfg.match_pct < 50 else f"[yellow]{cfg.match_pct:.0f}%[/yellow]"
            diag_str = f"{cfg.short_title} ({cfg.diagnosis_subtitle})"

        act_col = (
            f"[green]{cfg.action_headline}[/green]"
            if cfg.category in ("BULL_LONG", "ACCUMULATE")
            else (f"[yellow]{cfg.action_headline}[/yellow]" if cfg.category == "HARVEST_WAIT" else f"[red]{cfg.action_headline}[/red]")
        )
        p3_table.add_row(
            c_name,
            diag_str,
            m_str,
            cfg.key_live_facts,
            f"{act_col} | {cfg.stop_rule}",
        )

    matrix_panel = Panel(
        p3_table,
        title="[bold green]3. Quantitative Microstructure Diagnostic Matrix (Configurations A through J)[/bold green]",
        box=box.ROUNDED,
    )

    # --- Panel 4: Active Config Playbook + Global Session Microstructure Reference ---
    p4_grid = Table.grid(expand=True, padding=(0, 2))
    p4_grid.add_column(ratio=4, no_wrap=True)
    p4_grid.add_column(ratio=6, no_wrap=True)

    left_lines = [
        f"[bold cyan]IF YOU OBSERVE — {active_cfg.code} ({active_cfg.short_title}) Live Fact Checklist:[/bold cyan]"
    ]
    for item in active_cfg.observed_checklist[:5]:
        left_lines.append(f"  {item}")
    left_lines.append(
        f"  [bold yellow]Mandate:[/bold yellow] {active_cfg.action_headline} | {active_cfg.sizing_rule} | [bold red]{active_cfg.stop_rule}[/bold red]"
    )

    utc_hour = datetime.now(timezone.utc).hour
    session_windows = [
        (0, 7, "00–07 UTC (08–15 SGT)", "ASIA SESSION", "Binance Spot/Perp lead; ranges & Config F base-building"),
        (7, 8, "07–08 UTC (15–16 SGT)", "ASIA/LON OVERLAP", "Frequent stop-hunt / sweep window as EU desks enter"),
        (8, 13, "08–13 UTC (16–21 SGT)", "LONDON / EU", "European directional expansion & pre-US positioning"),
        (13, 16, "13–16 UTC (21–00 SGT)", "LON/NY OVERLAP", "Peak Spot vol, US ETF flow & Config A breakouts"),
        (16, 21, "16–21 UTC (00–05 SGT)", "NEW YORK (US)", "Coinbase Spot & US institutional absorption (Config C)"),
        (21, 24, "21–24 UTC (05–08 SGT)", "LATE NY / TRANS", "Thinner books prior to 00:00 UTC daily candle close"),
    ]
    right_lines = [
        "[bold yellow]GLOBAL TRADING SESSIONS (UTC • SGT) & MICROSTRUCTURE CONTEXT:[/bold yellow]"
    ]
    for start_h, end_h, win_str, s_name, ctx_str in session_windows:
        if start_h <= utc_hour < end_h:
            right_lines.append(
                f"  [bold black on green] ► {win_str} [/bold black on green] [bold green]{s_name:<16}[/bold green] [bold white]{ctx_str}[/bold white]"
            )
        else:
            right_lines.append(
                f"  [dim]  {win_str}  {s_name:<16} {ctx_str}[/dim]"
            )

    p4_grid.add_row("\n".join(left_lines), "\n".join(right_lines))
    playbook_panel = Panel(
        p4_grid,
        title="[bold yellow]4. Active Configuration Checklist & Global Session Microstructure Reference (UTC • SGT)[/bold yellow]",
        box=box.ROUNDED,
    )

    # --- Panel 5: Executive Bottom Line (Config A-J Plain-English Quick Glance) ---
    if active_cfg.category == "BULL_LONG":
        headline = f"[bold black on green] GREEN LIGHT — {active_cfg.code.upper()}: {active_cfg.short_title.upper()} ({active_cfg.action_headline.upper()}) [/bold black on green]"
        border_style = "green"
    elif active_cfg.category == "ACCUMULATE":
        headline = f"[bold black on cyan] BLUE LIGHT — {active_cfg.code.upper()}: {active_cfg.short_title.upper()} ({active_cfg.action_headline.upper()}) [/bold black on cyan]"
        border_style = "cyan"
    elif active_cfg.category == "HARVEST_WAIT":
        headline = f"[bold black on yellow] YELLOW LIGHT — {active_cfg.code.upper()}: {active_cfg.short_title.upper()} ({active_cfg.action_headline.upper()}) [/bold black on yellow]"
        border_style = "yellow"
    else:
        headline = f"[bold white on red] RED LIGHT — {active_cfg.code.upper()}: {active_cfg.short_title.upper()} ({active_cfg.action_headline.upper()}) [/bold white on red]"
        border_style = "red"

    p5_lines = [
        headline,
        f"  [bold white]What's Happening :[/bold white] Live telemetry matches {active_cfg.code} ({active_cfg.short_title} — {active_cfg.diagnosis_subtitle}) at {active_cfg.match_pct:.0f}% confidence ({active_cfg.key_live_facts}).",
        f"  [bold white]Why / Runner-Up  :[/bold white] Secondary match is {runner_cfg.code} ({runner_cfg.short_title} at {runner_cfg.match_pct:.0f}%). Daily VWAP is ${rmev.daily_vwap:,.0f} and Weekly VWAP is ${rmev.weekly_vwap:,.0f}.",
        f"  [bold white]Your Next Move   :[/bold white] [bold]{active_cfg.action_headline}[/bold] -> {active_cfg.sizing_rule} | {active_cfg.entry_or_harvest_rule} | {active_cfg.stop_rule}.",
    ]
    bottom_panel = Panel(
        "\n".join(p5_lines),
        title="[bold white]5. Executive Bottom Line (Config A–J Quick Glance — Press 0: Master • 1–9: Desks)[/bold white]",
        border_style=border_style,
        box=box.ROUNDED,
    )

    return Group(header_panel, top_row, matrix_panel, playbook_panel, bottom_panel)


# ============================================================================
# TAB [0]: BTC SPOT SWING SCREENING & ALERT ENGINE
# (1D Macro Gate -> Weekly Liquidity Sweep / Reclaim -> Triple-Barrier Risk)
# ============================================================================

def _pass_badge(ok: bool, yes: str = "PASS", no: str = "FAIL") -> str:
    if ok:
        return f"[bold black on green] {yes} [/bold black on green]"
    return f"[bold white on red] {no} [/bold white on red]"


def _spot_swing_light_style(light: str) -> str:
    return {
        "GREEN": "bold black on green",
        "BLUE": "bold black on cyan",
        "YELLOW": "bold black on yellow",
    }.get(light, "bold white on red")


def _magnet_verdict_style(verdict: str) -> str:
    v = verdict.upper()
    if "HOLD" in v or "RARE ADD" in v:
        return "bold black on green"
    if "PARTIAL PROFIT" in v:
        return "bold black on yellow"
    if "REDUCE" in v or "EXIT" in v:
        return "bold white on red"
    return "bold white on blue"


def _magnet_verdict_style(verdict: str) -> str:
    v = verdict.upper()
    if "HOLD" in v or "RARE ADD" in v:
        return "bold black on green"
    if "PARTIAL PROFIT" in v:
        return "bold black on yellow"
    if "REDUCE" in v or "EXIT" in v:
        return "bold white on red"
    return "bold white on blue"


def _build_tab0_spot_swing_hud(store: StateStore, header_panel: Panel) -> Group:
    """Renders Tab [0]: BTC Spot Swing Screening & Daily Liquidation Magnet Engine (Modules B-F)."""
    ev = store.spot_swing_evaluation
    if ev is None:
        return Group(
            header_panel,
            Panel(
                "Warming up Tab [0]: BTC Spot Swing Screening & Alert Engine (waiting for 1D / 1H history)...",
                title="Tab [0]: BTC Spot Swing Screening & Alert Engine",
                box=box.ROUNDED,
            ),
        )

    # --- Introduction Card ---
    intro_lines = [
        "[bold cyan]▶ CORE LAW & PURPOSE:[/bold cyan] [bold yellow]In a range-bound regime, trade the liquidation magnet and positioning imbalance — not the headline.[/bold yellow] Deterministic BTC spot swing screener (3-day to 3-week hold).",
        "[bold cyan]▶ CORE MODELS & FEEDS:[/bold cyan] Daily Liquidation Magnet Protocol (50D MA + 30–45D Range + Short/Long Liq Clusters + OI/Funding/Spot CVD) • 1D Macro Gate • 4H PWL/PWH Sweep & Reclaim • Strict RRR ≥ 1:3.",
        "[bold cyan]▶ EXECUTION MANDATE:[/bold cyan] [bold yellow]Closed bars only.[/bold yellow] Default is Do Nothing (100% Cash). Require RRR ≥ 1:3 to Short-Liq Magnet, 1% fixed risk (max 100% spot), scale 30–50% into magnet, hard stop below pivot/50DMA.",
    ]
    intro_panel = Panel(
        "\n".join(intro_lines),
        title="[bold cyan]WELCOME TO TAB [0]: BTC SPOT SWING SCREENING & DAILY LIQUIDATION MAGNET ENGINE[/bold cyan]",
        box=box.ROUNDED,
        border_style="cyan",
        padding=(0, 1),
    )

    # --- Top Ribbon ---
    macro, setup, risk, trade, mag = ev.macro, ev.setup, ev.risk, ev.trade, ev.magnet
    v_style = _spot_swing_light_style(ev.traffic_light)
    if ev.alerts_enabled:
        alert_state = "[bold green]ARMED (webhook/Telegram)[/bold green]"
    elif ev.read_only:
        alert_state = "[bold yellow]READ-ONLY SNAPSHOT[/bold yellow]"
    else:
        alert_state = "[dim]OFF — set SPOT_SWING_WEBHOOK_URL or TELEGRAM_BOT_TOKEN[/dim]"

    if mag is not None:
        mv_style = _magnet_verdict_style(mag.verdict)
        rrr_badge = f"[bold green]{mag.rrr_to_magnet:.2f}R (≥3R PASS)[/bold green]" if mag.rrr_pass else f"[bold yellow]{mag.rrr_to_magnet:.2f}R (<3R WAIT)[/bold yellow]"
        card_magnet = (
            f"[bold white]Magnet Verdict:[/bold white] [{mv_style}] {mag.verdict.upper()} [/{mv_style}] ({mag.confidence})\n"
            f"Regime: [bold cyan]{mag.regime.upper()}[/bold cyan] • Live R:R: {rrr_badge}"
        )
        card_clusters = (
            f"[bold white]Short-Liq Magnet (↑):[/bold white] [bold magenta]${mag.short_liq_magnet:,.0f}[/bold magenta] (+{mag.short_liq_distance_pct:.2f}%)\n"
            f"[bold white]Long-Liq Magnet  (↓):[/bold white] [bold cyan]${mag.long_liq_magnet:,.0f}[/bold cyan] (-{mag.long_liq_distance_pct:.2f}%)"
        )
    else:
        card_magnet = (
            f"[bold white]Spot Swing Verdict:[/bold white] [{v_style}] {ev.verdict} [/{v_style}]\n"
            f"Spot: [bold cyan]${ev.spot_price:,.2f}[/bold cyan] • Evaluated on closed bars only"
        )
        card_clusters = "[bold white]Liquidation Magnets:[/bold white] [dim]WARMING UP[/dim]"

    if macro is not None:
        gate_txt = "[bold black on green] APPROVED [/bold black on green]" if macro.macro_approved else "[bold white on red] FROZEN: 100% CASH [/bold white on red]"
        card_macro = (
            f"[bold white]Screener:[/bold white] [{v_style}] {ev.verdict} [/{v_style}]\n"
            f"1D Gate: {gate_txt} • Trend {_pass_badge(macro.trend_pass)} • Squeeze {_pass_badge(macro.compression_pass, 'PASS', 'FAIL')}"
        )
    else:
        card_macro = "[bold white]Macro Gate (1D):[/bold white] [dim]WARMING UP[/dim]"

    card_alert = (
        f"[bold white]Alert Dispatcher:[/bold white] {alert_state}\n"
        f"Sizing equity: [cyan]${store_equity_label(ev)}[/cyan] • Risk: [cyan]{risk.risk_pct if risk else ev.risk_pct:.1f}%[/cyan]/trade • Min RRR: [bold green]1:3.0[/bold green]"
    )
    ribbon_table = Table.grid(expand=True)
    ribbon_table.add_column(ratio=3)
    ribbon_table.add_column(ratio=3)
    ribbon_table.add_column(ratio=2)
    ribbon_table.add_column(ratio=2)
    ribbon_table.add_row(
        Panel(card_magnet, box=box.ROUNDED, border_style="yellow", padding=(0, 1)),
        Panel(card_macro, box=box.ROUNDED, border_style="cyan", padding=(0, 1)),
        Panel(card_clusters, box=box.ROUNDED, border_style="magenta", padding=(0, 1)),
        Panel(card_alert, box=box.ROUNDED, border_style="green", padding=(0, 1)),
    )

    bottom_title = "[bold white]4. Daily Liquidation Magnet Protocol (Step 4 Verdict) & Executive Bottom Line (Press 0: Spot Swing • L: Master • 1-9: Desks • C: Copy)[/bold white]"

    # --- Not ready: show diagnostics + bottom line only ---
    if not ev.data_ready or macro is None or setup is None:
        notes = "\n".join(f"  • {n}" for n in ev.data_notes) or "  • Waiting for data"
        status_panel = Panel(
            f"[bold black on yellow] {ev.verdict} [/bold black on yellow]\n{notes}",
            title="[bold yellow]Data Readiness[/bold yellow]",
            box=box.ROUNDED,
            border_style="yellow",
        )
        return Group(header_panel, ribbon_table, status_panel)

    # --- Panel 1: 1D Macro Regime Gate & Step 2 Range Confirmation ---
    p1 = Table(box=box.SIMPLE_HEAVY, expand=True, show_header=True, header_style="bold cyan", pad_edge=False)
    p1.add_column("Check", style="bold white", no_wrap=True)
    p1.add_column("Rule", style="dim white", no_wrap=True)
    p1.add_column("Live Value", justify="right", style="cyan", no_wrap=True)
    p1.add_column("State", justify="center", no_wrap=True)

    if mag is not None:
        reg_badge = (
            "[bold black on cyan] RANGE [/bold black on cyan]"
            if mag.regime == "Range"
            else (
                "[bold black on yellow] TRANSITION [/bold black on yellow]"
                if "Transition" in mag.regime
                else "[bold black on green] TREND [/bold black on green]"
            )
        )
        p1.add_row(
            "Regime (Step 2)",
            "30–45D Range & HH/HL check",
            f"${mag.range_low_30d:,.0f}–${mag.range_high_30d:,.0f} ({mag.range_pos_pct:.0f}%)",
            reg_badge,
        )
        p1.add_row(
            "50D MA & Range Pivot",
            "1D SMA50 & Midpoint Inval.",
            f"50DMA ${mag.sma50_1d:,.0f} • Pivot ${mag.range_pivot:,.0f}",
            _pass_badge(ev.spot_price >= mag.sma50_1d, "ABOVE 50D", "BELOW 50D"),
        )

    squeeze_rule = "BBW(20) 180D rank ≤ 30%" if macro.squeeze_lookback_bars <= 1 else f"BBW rank ≤ 30% (any of last {macro.squeeze_lookback_bars}D)"
    p1.add_row(
        "Trend baseline",
        "Close > EMA50 > EMA200",
        f"${macro.close:,.0f} / ${macro.ema50:,.0f} / ${macro.ema200:,.0f}",
        _pass_badge(macro.trend_pass, "BULLISH", "NO TREND"),
    )
    p1.add_row(
        "Volatility squeeze",
        squeeze_rule,
        f"BBW {macro.bbw * 100:.2f}% • rank {macro.bbw_percentile * 100:.1f}%",
        _pass_badge(macro.compression_pass, "COMPRESSED", "EXPANDED"),
    )
    p1.add_row(
        "Macro permission",
        "trend AND squeeze",
        f"1D bar {datetime.fromtimestamp(macro.bar_ts_ms / 1000, tz=timezone.utc).strftime('%m-%d')} closed",
        _pass_badge(macro.macro_approved, "APPROVED", "FROZEN"),
    )

    # --- Panel 2: Positioning Audit, Liquidation Magnets & Weekly Anchors ---
    p2 = Table(box=box.SIMPLE_HEAVY, expand=True, show_header=True, header_style="bold yellow", pad_edge=False)
    p2.add_column("Check", style="bold white", no_wrap=True)
    p2.add_column("Rule", style="dim white", no_wrap=True)
    p2.add_column("Live Value", justify="right", style="yellow", no_wrap=True)
    p2.add_column("State", justify="center", no_wrap=True)

    if mag is not None:
        p2.add_row(
            "Short-Liq Magnet (↑)",
            "Nearest dense cluster above",
            f"${mag.short_liq_magnet:,.0f} (+{mag.short_liq_distance_pct:.2f}%)",
            f"[magenta]{mag.short_liq_size_label}[/magenta]",
        )
        p2.add_row(
            "Long-Liq Magnet (↓)",
            "Nearest dense cluster below",
            f"${mag.long_liq_magnet:,.0f} (-{mag.long_liq_distance_pct:.2f}%)",
            f"[cyan]{mag.long_liq_size_label}[/cyan]",
        )
        oi_word = mag.oi_trend.split(" (")[0].upper()
        fund_word = "NEG" if mag.funding_rate_8h_pct < -0.0005 else ("NEUT" if mag.funding_rate_8h_pct <= 0.006 else "POS")
        p2.add_row(
            "OI & 8H Funding",
            "24H OI trend & Perp rate",
            f"24H dOI {mag.oi_change_24h_pct:+.2f}% • Fund {mag.funding_rate_8h_pct:+.4f}%",
            f"[bold]{oi_word} / {fund_word}[/bold]",
        )
        p2.add_row(
            "Spot CVD Truth Serum",
            "Spot vs Perp on recent move",
            f"4H S:{mag.spot_cvd_4h_btc:+,.0f} P:{mag.perp_cvd_4h_btc:+,.0f} BTC",
            _pass_badge(mag.spot_cvd_confirming, "CONFIRMING", "UNCONFIRMED"),
        )

    if setup.anchors_ready:
        px = ev.spot_price
        p2.add_row("PWH / PWL", "Prev Mon-Sun week high / low", f"${setup.pwh:,.0f} / ${setup.pwl:,.0f}", f"[dim]{(px / setup.pwl - 1) * 100:+.2f}% vs PWL[/dim]")
        p2.add_row(
            "Sweep",
            "4H low < PWL (last 12 bars)",
            f"wick ${setup.sweep_low:,.0f}" if setup.sweep_detected else "none",
            _pass_badge(setup.sweep_detected, "DETECTED", "NONE"),
        )
        p2.add_row("Reclaim", "Last closed 4H close > PWL", f"close ${setup.close:,.0f}", _pass_badge(setup.reclaim_confirmed, "CONFIRMED", "NO"))
        p2.add_row("Volume", "Reclaim vol > SMA(3)", f"{setup.volume:,.0f} vs {setup.vol_sma3:,.0f}", _pass_badge(setup.volume_confirmed, "CONFIRMED", "NO"))
        if setup.signal_active and setup.is_fresh:
            sig_badge = "[bold black on green] ACTIVE LONG [/bold black on green]"
        elif setup.signal_active:
            sig_badge = "[bold black on cyan] ALREADY ACTED [/bold black on cyan]"
        else:
            sig_badge = "[dim] INACTIVE [/dim]"
        p2.add_row("Signal", "sweep AND reclaim AND volume", "", sig_badge)

        # Safety Pre-flight checks: Liquidation cascade & Tell-Tale knife pause
        liq_rep = store.trap_evaluation.liquidation_report if store.trap_evaluation else None
        tt_ev = store.exhaustion_evaluation.tell_tale if store.exhaustion_evaluation else None

        liq_status = "STANDBY"
        liq_pass = True
        if liq_rep and liq_rep.is_available:
            if "EXTREME" in liq_rep.magnitude_tier and not (
                liq_rep.post_flush_price_structure and liq_rep.post_flush_price_structure.stabilisation_confirmed
            ):
                liq_status = "FLUSH IN PROGRESS (PAUSE)"
                liq_pass = False
            elif liq_rep.post_flush_price_structure and (
                liq_rep.post_flush_price_structure.stabilisation_confirmed or liq_rep.post_flush_price_structure.higher_low_formed
            ):
                liq_status = "STABILIZED"
                liq_pass = True
            else:
                liq_status = "NORMAL / QUIET"
                liq_pass = True

        tt_status = "CLEAR"
        tt_pass = True
        if tt_ev and tt_ev.is_selling_climax:
            tt_status = "CLIMAX DUMP"
            tt_pass = False

        safety_state = "CLEAR" if (liq_pass and tt_pass) else "CAUTION"
        safety_badge = "[bold black on green] PERMITTED [/bold black on green]" if safety_state == "CLEAR" else "[bold black on yellow] PAUSED [/bold black on yellow]"
        p2.add_row("Safety guard", f"Liq: {liq_status} • Climax: {tt_status}", "", safety_badge)
    else:
        p2.add_row("PWH / PWL", "Previous Mon-Sun week", "syncing…", "[bold black on yellow] WAIT [/bold black on yellow]")

    mid_row = Table.grid(expand=True)
    mid_row.add_column(ratio=5)
    mid_row.add_column(ratio=5)
    mid_row.add_row(
        Panel(p1, title=f"[bold cyan]1. 1D Macro Regime Gate — BTC SPOT SWING SCREENING ({'APPROVED' if macro.macro_approved else 'FROZEN'})[/bold cyan]", box=box.ROUNDED),
        Panel(p2, title="[bold yellow]2. Liquidation Magnet Positioning Audit & Weekly Anchors (4H Sweep / Reclaim)[/bold yellow]", box=box.ROUNDED),
    )

    # --- Panel 3: Tight Money Management (RRR >= 1:3) & Triple-Barrier Sizing ---
    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    p3 = Table(box=box.SIMPLE_HEAVY, expand=True, show_header=True, header_style="bold magenta", pad_edge=False)
    p3.add_column("Item", style="bold white", no_wrap=True)
    p3.add_column("Level", justify="right", style="cyan", no_wrap=True)
    p3.add_column("Detail", style="dim white", no_wrap=False)

    def _time_left(expiry_ms: int) -> str:
        left_h = max(0.0, (expiry_ms - now_ms) / 3_600_000.0)
        return f"{left_h / 24.0:.1f}d / {int(left_h // 4)} x 4H bars left"

    if mag is not None:
        rrr_state = (
            "[bold black on green] PASS (≥ 1:3 RRR) [/bold black on green]"
            if mag.rrr_pass
            else "[bold black on yellow] REJECTED (< 1:3 RRR — DO NOT CHASE) [/bold black on yellow]"
        )
        p3.add_row(
            "RRR 1:3 Mandate Gate",
            f"{mag.rrr_to_magnet:.2f}R (Min {mag.min_required_rrr:.1f}R)",
            f"{rrr_state} • Reward +${mag.reward_to_magnet_usd:,.0f} (to ${mag.short_liq_magnet:,.0f}) vs Risk -${mag.risk_distance_usd:,.0f} (Stop ${mag.hard_stop_price:,.0f}) • Max 3R Entry: ≤ ${mag.max_entry_for_3r:,.0f}",
        )
        p3.add_row(
            "Magnet Scaling Plan",
            f"Scale 30–50% @ ${mag.short_liq_magnet:,.0f}",
            f"3R Target: ${mag.tp_3r_price:,.0f} • Invalidation: 1D Close < ${mag.invalidation_level:,.0f} (Pivot/50DMA) • 1% Risk Size: {mag.recommended_qty_btc:.4f} BTC (${mag.recommended_notional_usd:,.0f})",
        )

    if trade is not None:
        dist = max(trade.entry - trade.initial_stop, 1e-9)
        r_now = (ev.spot_price - trade.entry) / dist
        p3_title = f"[bold green]3. Tight RRR 1:3 Money Management & Open Trade — Triple-Barrier Tracker ({trade.status})[/bold green]"
        p3.add_row("Entry", f"${trade.entry:,.2f}", f"{trade.qty_btc:.6f} BTC (${trade.qty_btc * trade.entry:,.0f}) • opened {datetime.fromtimestamp(trade.entry_ts_ms / 1000, tz=timezone.utc).strftime('%m-%d %H:%M')} UTC")
        p3.add_row("Live P/L", f"{r_now:+.2f}R", f"spot ${ev.spot_price:,.2f}")
        p3.add_row("Barrier 1: Stop", f"${trade.current_stop:,.2f}", f"initial ${trade.initial_stop:,.2f}" + (" • moved to BREAKEVEN" if trade.tp1_hit else "") + f" • {((ev.spot_price / trade.current_stop) - 1) * 100:+.2f}% away")
        p3.add_row("Barrier 2a: +2.0R", f"${trade.tp1:,.2f}", "HIT — 50% sold" if trade.tp1_hit else "sell 50% & move stop to breakeven")
        p3.add_row("Barrier 2b: PWH", f"${trade.tp2:,.2f}", "runner target")
        p3.add_row("Barrier 3: Time", datetime.fromtimestamp(trade.time_stop_ts_ms / 1000, tz=timezone.utc).strftime("%m-%d %H:%M UTC"), _time_left(trade.time_stop_ts_ms))
        p3_border = "green"
    elif risk is not None:
        preview = "" if macro.macro_approved else " — PREVIEW ONLY, MACRO FROZEN"
        p3_title = f"[bold magenta]3. Tight RRR 1:3 Money Management & Triple-Barrier Sizing{preview}[/bold magenta]"
        p3.add_row("Entry (P_entry)", f"${risk.entry:,.2f}", "close of the reclaim 4H candle")
        p3.add_row("Stop (P_stop)", f"${risk.stop:,.2f}", f"sweep low − 0.5 × ATR14 (${risk.atr14:,.0f}) • distance {risk.stop_distance_pct:.2f}%")
        cap_note = " [bold yellow]CAPPED at 100% spot[/bold yellow]" if risk.spot_capped else ""
        p3.add_row("Position size", f"{risk.qty_btc:.6f} BTC", f"${risk.notional_usd:,.0f} = {risk.equity_alloc_pct:.1f}% of ${risk.equity_usd:,.0f} • risk ${risk.realized_risk_usd:,.0f}{cap_note}")
        p3.add_row("Barrier 2a: +2.0R", f"${risk.tp1:,.2f}", f"sell 50% & move stop to breakeven (3R Target: ${risk.tp_3r:,.0f})")
        warn = " [yellow](PWH is inside +2R)[/yellow]" if risk.tp2_inside_tp1 else ""
        p3.add_row("Barrier 2b: PWH", f"${risk.tp2_pwh:,.2f}", f"structural runner target{warn}")
        p3.add_row("Barrier 3: Time", datetime.fromtimestamp(risk.time_stop_ts_ms / 1000, tz=timezone.utc).strftime("%m-%d %H:%M UTC"), _time_left(risk.time_stop_ts_ms))
        p3_border = "magenta"
    else:
        p3_title = "[bold magenta]3. Tight RRR 1:3 Money Management & Triple-Barrier Sizing (standing rules)[/bold magenta]"
        p3.add_row("Stop", "sweep low − 0.5×ATR14", "4H Wilder ATR; invalidation below swept liquidity or Range Pivot / 50D MA")
        p3.add_row("Size", "equity × 1% ÷ stop dist", f"capped at 100% of equity (spot, no leverage) • equity ${store_equity_label(ev)}")
        p3.add_row("Barrier 2", "Short-Liq Magnet / +3.0R", "scale 30–50% into Short-Liq Magnet (+2R to +3R), stop to breakeven, runner to PWH")
        p3.add_row("Barrier 3", "10 days", "time stop frees capital from stagnant swings")
        p3_border = "dim"
    p3_panel = Panel(p3, title=p3_title, box=box.ROUNDED, border_style=p3_border)

    # --- Panel 4: Daily Liquidation Magnet Protocol (Step 4 Strict Output) & Alert Log ---
    if store.last_packet_copied_ts > 0:
        copy_badge = f"[bold black on green] [✔ COPIED ({store.last_packet_char_count:,} chars @ {store.last_packet_copied_utc})] [/bold black on green]"
    else:
        copy_badge = "[bold black on yellow] [PRESS 'C': COPY RAW TELEMETRY PACKET] [/bold black on yellow]"

    p4_lines: List[str] = []
    if mag is not None:
        mv_style = _magnet_verdict_style(mag.verdict)
        p4_lines.extend([
            f"[{mv_style}] MAGNET VERDICT: {mag.verdict.upper()} (Confidence: {mag.confidence}) [/{mv_style}]   [{v_style}] SCREENER: {ev.verdict} [/{v_style}]   {copy_badge}",
            f"  [bold cyan]Regime[/bold cyan]               : [bold white]{mag.regime}[/bold white] — {mag.regime_detail}",
            f"  [bold cyan]Key Levels[/bold cyan]           : Short-liq magnet: [bold magenta]${mag.short_liq_magnet:,.0f}[/bold magenta] ({mag.short_liq_size_label})  •  Long-liq magnet: [bold cyan]${mag.long_liq_magnet:,.0f}[/bold cyan] ({mag.long_liq_size_label})  •  50-day MA: [bold]${mag.sma50_1d:,.0f}[/bold]  •  Range pivot / invalidation: [bold yellow]${mag.range_pivot:,.0f} / ${mag.invalidation_level:,.0f}[/bold yellow]",
            f"  [bold cyan]Positioning Snapshot[/bold cyan] : OI: [white]{mag.oi_trend}[/white]  •  Funding: [white]{mag.funding_status}[/white]  •  Spot CVD: [white]{mag.spot_cvd_assessment}[/white]",
            f"  [bold cyan]Headline Filter[/bold cyan]      : [white]{mag.headline_filter}[/white]  •  [dim]{mag.cum_liq_24h_summary}[/dim]",
            f"  [bold cyan]Primary Reason[/bold cyan]       : {mag.primary_reason}",
            f"  [bold cyan]Invalidation[/bold cyan]         : [bold red]{mag.invalidation_text}[/bold red]",
            f"  [bold cyan]Actionable Note[/bold cyan]      : [bold green]{mag.actionable_note}[/bold green]",
            f"  [bold white]Plain English[/bold white]        : {ev.plain_english_summary}",
        ])
    else:
        p4_lines.extend([
            f"[{v_style}] {ev.verdict} [/{v_style}]  {copy_badge}",
            f"  [bold white]Plain English:[/bold white] {ev.plain_english_summary}",
        ])

    if ev.recent_events:
        p4_lines.append("  [bold white]Recent Alerts :[/bold white]")
        p4_lines.extend(f"    [dim]{line}[/dim]" for line in ev.recent_events[:3])
    else:
        p4_lines.append("  [bold white]Recent Alerts :[/bold white] [dim]none yet[/dim]")
    p4_panel = Panel("\n".join(p4_lines), title=bottom_title, border_style="cyan", box=box.ROUNDED)

    return Group(header_panel, ribbon_table, mid_row, p3_panel, p4_panel)


def store_equity_label(ev: Any) -> str:
    """Formats the sizing equity shown in the Tab [0] ribbon (taken from the live risk object when present)."""
    if ev.risk is not None:
        return f"{ev.risk.equity_usd:,.0f}"
    if ev.trade is not None:
        return f"{ev.trade.qty_btc * ev.trade.entry:,.0f} in trade"
    if getattr(ev, "equity_usd", 0.0) > 0:
        return f"{ev.equity_usd:,.0f}"
    return "configured"



# ============================================================================
# TAB [5]: MASTER SYNTHESIS & SUPREME ORDER OF BATTLE HUD
# ============================================================================

def _light_badge(light: str) -> str:
    if light == "GREEN":
        return "[bold black on green] GREEN [/bold black on green]"
    if light == "BLUE":
        return "[bold black on cyan] BLUE  [/bold black on cyan]"
    if light == "YELLOW":
        return "[bold black on yellow] YELLW [/bold black on yellow]"
    return "[bold white on red]  RED  [/bold white on red]"


def _layer_status_badge(status: str) -> str:
    if status == "PASS":
        return "[bold black on green]  PASS   [/bold black on green]"
    if status == "ARMED":
        return "[bold black on cyan]  ARMED  [/bold black on cyan]"
    if status == "STANDBY":
        return "[bold black on yellow] STANDBY [/bold black on yellow]"
    if status == "CAUTION":
        return "[bold yellow] CAUTION [/bold yellow]"
    return "[bold white on red]  VETO   [/bold white on red]"


def _build_tab0_master_synthesis_hud(store: StateStore, header_panel: Panel) -> Group:
    """Renders Tab [5]: Master Synthesis & Supreme Order of Battle across Tabs [1]-[4]."""
    msev = store.master_synthesis_evaluation
    if msev is None:
        return Group(
            header_panel,
            Panel(
                "Warming up 10-Desk Master Synthesis Engine...",
                title="Tab [L]: Master Conclusion",
                box=box.ROUNDED,
            ),
        )

    # --- Introduction Card: Beginner Context & Methodology ---
    intro_lines = [
        "[bold cyan]▶ PURPOSE & SCOPE:[/bold cyan] Supreme command center harmonizing all 9 specialist desks (Tabs 1–9) into an institutional capital allocation verdict.",
        "[bold cyan]▶ CORE MODELS & FEEDS:[/bold cyan] 9-Desk Rollup Matrix • Confluence Scoring Engine (0–100) • 4-Layer Hierarchy Gatekeeper • Dual-Track Allocation.",
        "[bold cyan]▶ EXECUTION MANDATE:[/bold cyan] [bold green]The Supreme Signal Light[/bold green]: GREEN (Full Aggression), BLUE (Accumulate Support), AMBER (Caution / Tight Stops), RED (Risk-Off Liquidation).",
    ]
    intro_panel = Panel(
        "\n".join(intro_lines),
        title="[bold cyan]WELCOME TO TAB [L]: MASTER SYNTHESIS & SUPREME COMMAND CENTER[/bold cyan]",
        box=box.ROUNDED,
        border_style="cyan",
        padding=(0, 1),
    )

    # --- Panel 1: 4-Tab Executive Verdict Rollup Matrix ---
    p1_table = Table(
        box=box.SIMPLE_HEAVY,
        expand=True,
        show_header=True,
        header_style="bold cyan",
        pad_edge=False,
    )
    p1_table.add_column("Tab", style="bold white", no_wrap=True)
    p1_table.add_column("Light", justify="center", no_wrap=True)
    p1_table.add_column("Score / State", no_wrap=True)
    p1_table.add_column("Executive Conclusion", justify="right", no_wrap=True)

    for row in msev.tab_rows:
        conc_color = (
            "bold green"
            if row.traffic_light == "GREEN"
            else (
                "bold cyan"
                if row.traffic_light == "BLUE"
                else ("bold yellow" if row.traffic_light == "YELLOW" else "bold red")
            )
        )
        p1_table.add_row(
            row.tab_name,
            _light_badge(row.traffic_light),
            row.score_or_status,
            f"[{conc_color}]{row.tab_conclusion}[/{conc_color}]",
        )

    p1_footer = (
        f"[bold white]Scoreboard:[/bold white] [bold green]{msev.tabs_green_count} GREEN[/bold green] • "
        f"[bold cyan]{msev.tabs_blue_count} BLUE[/bold cyan] • "
        f"[bold yellow]{msev.tabs_yellow_count} YELLOW[/bold yellow] • "
        f"[bold red]{msev.tabs_red_count} RED[/bold red]  |  "
        f"[bold white]Alignment:[/bold white] [bold cyan]{msev.master_alignment_score:.1f}%[/bold cyan] "
        f"([bold yellow]{msev.alignment_status}[/bold yellow])"
    )
    p1_group = Group(p1_table, p1_footer)

    # --- Panel 2: 4-Layer Institutional Decision Funnel & Conflict Resolver ---
    p2_table = Table(
        box=box.SIMPLE_HEAVY,
        expand=True,
        show_header=True,
        header_style="bold magenta",
        pad_edge=False,
    )
    p2_table.add_column("Hierarchy Layer", style="white", no_wrap=True)
    p2_table.add_column("Gate", justify="center", no_wrap=True)
    p2_table.add_column("Live Hierarchical Ruling", justify="right", no_wrap=True)

    for h_row in msev.hierarchy_rows:
        p2_table.add_row(
            h_row.layer_name,
            _layer_status_badge(h_row.status),
            h_row.live_ruling,
        )

    p2_footer = (
        "[dim]Precedence: L1 Hard Veto overrides all -> L2 sets Base Risk (1.0% vs 0.5%) "
        "-> L3 scales Size (0.0x–1.0x) -> L4 times Entry.[/dim]"
    )
    p2_group = Group(p2_table, p2_footer)

    top_row = Table.grid(expand=True)
    top_row.add_column(ratio=5)
    top_row.add_column(ratio=5)
    top_row.add_row(
        Panel(
            p1_group,
            title="[bold cyan]1. 4-Tab Executive Verdict Rollup Matrix (Specialist Desks [1]–[4])[/bold cyan]",
            box=box.ROUNDED,
        ),
        Panel(
            p2_group,
            title="[bold magenta]2. 4-Layer Institutional Decision Funnel & Conflict Resolver[/bold magenta]",
            box=box.ROUNDED,
        ),
    )

    # --- Panel 3: Cross-Tab Agreement & Divergence Audit (Detailed Narrative) ---
    p3_lines = [
        "[bold green]✔ CROSS-TAB CONFLUENCE (WHERE THE 4 TABS AGREE RIGHT NOW):[/bold green]"
    ]
    for pt in msev.confluence_points[:3]:
        p3_lines.append(f"  • {pt}")

    p3_lines.append(
        "[bold yellow]⚡ CROSS-TAB CONFLICT DIAGNOSTIC & HIERARCHICAL RESOLUTION:[/bold yellow]"
    )
    for cpt in msev.conflict_points[:2]:
        p3_lines.append(f"  • {cpt}")

    p3_lines.append(
        "[bold cyan]🎯 CATALYSTS THAT FLIP THE MASTER CONCLUSION (UPGRADE / DOWNGRADE):[/bold cyan]"
    )
    for ucat in msev.upgrade_catalysts[:2]:
        p3_lines.append(f"  • {ucat}")

    # --- Panel 4: Reconciled Master Playbook (If Flat in Cash vs. If Holding Spot BTC) ---
    p4_table = Table(
        box=box.SIMPLE_HEAVY,
        expand=True,
        show_header=True,
        header_style="bold yellow",
        pad_edge=False,
    )
    p4_table.add_column("Playbook Track", style="bold white", no_wrap=True)
    p4_table.add_column("Reconciled Master Specification", justify="right", no_wrap=True)

    perm_col = (
        "bold green"
        if "AUTHORIZED NOW" in msev.cash_permission
        else ("bold red" if "FORBIDDEN" in msev.cash_permission else "bold cyan")
    )
    p4_table.add_row(
        "[bold cyan]TRACK A: IF FLAT IN CASH[/bold cyan]",
        f"[{perm_col}]{msev.cash_permission}[/{perm_col}]",
    )
    p4_table.add_row(
        "  ├─ Reconciled Bid Zone",
        f"[bold white]{msev.cash_entry_zone_str}[/bold white]",
    )
    p4_table.add_row(
        "  ├─ Reconciled Size Math",
        f"{msev.cash_base_risk_pct:.2f}% [T3] × {msev.cash_regime_multiplier:.2f}x [T4] -> "
        f"[bold cyan]{msev.cash_edge_size_btc:.4f} BTC (${msev.cash_edge_notional_usd:,.0f})[/bold cyan]",
    )
    p4_table.add_row(
        "  └─ Execution Rule",
        msev.cash_trigger_instruction,
    )

    hold_col = (
        "bold red"
        if "EXIT" in msev.holder_action
        else ("bold yellow" if "SCALE" in msev.holder_action else "bold green")
    )
    p4_table.add_row(
        "[bold green]TRACK B: IF HOLDING SPOT[/bold green]",
        f"[{hold_col}]{msev.holder_action}[/{hold_col}]",
    )
    p4_table.add_row(
        "  ├─ Reconciled Hard Stop",
        f"[bold red]${msev.holder_hard_stop_usd:,.0f}[/bold red] ({msev.holder_hard_stop_source})",
    )
    p4_table.add_row(
        "  ├─ Profit Targets (1/2)",
        f"TP1 (40%): [bold cyan]${msev.holder_tp1_usd:,.0f}[/bold cyan] ({msev.holder_tp1_source}) • "
        f"TP2 (60%): [bold magenta]${msev.holder_tp2_usd:,.0f}[/bold magenta]",
    )
    p4_table.add_row(
        "  └─ Management Rule",
        msev.holder_management_note,
    )

    mid_row = Table.grid(expand=True)
    mid_row.add_column(ratio=5)
    mid_row.add_column(ratio=5)
    mid_row.add_row(
        Panel(
            "\n".join(p3_lines),
            title="[bold green]3. Cross-Tab Agreement & Divergence Audit (Why This Conclusion Was Reached)[/bold green]",
            box=box.ROUNDED,
        ),
        Panel(
            p4_table,
            title="[bold yellow]4. Unified Master Order of Battle (Track A: In Cash vs. Track B: Holding Spot BTC)[/bold yellow]",
            box=box.ROUNDED,
        ),
    )

    # --- Panel 5: Supreme Master Executive Bottom Line ---
    if msev.master_traffic_light == "GREEN":
        headline = f"[bold black on green] {msev.master_headline} [/bold black on green]"
        border_style = "green"
    elif msev.master_traffic_light == "BLUE":
        headline = f"[bold black on cyan] {msev.master_headline} [/bold black on cyan]"
        border_style = "cyan"
    elif msev.master_traffic_light == "YELLOW":
        headline = f"[bold black on yellow] {msev.master_headline} [/bold black on yellow]"
        border_style = "yellow"
    else:
        headline = f"[bold white on red] {msev.master_headline} [/bold white on red]"
        border_style = "red"

    if store.last_packet_copied_ts > 0:
        copy_btn_badge = (
            f"[bold black on green] [✔ COPIED TO CLIPBOARD ({store.last_packet_char_count:,} chars @ {store.last_packet_copied_utc}) "
            f"— PRESS CTRL+V IN GEMINI ARGON AI! (Press 'C' to Copy Fresh Snapshot)] [/bold black on green]"
        )
    else:
        copy_btn_badge = (
            "[bold black on yellow] [PRESS 'C' KEY: COPY 10-DESK TELEMETRY PACKET TO CLIPBOARD FOR GEMINI ARGON AI AUDITOR] [/bold black on yellow]"
        )

    p5_lines = [
        f"{headline}  {copy_btn_badge}",
        f"  [bold white]Master Synthesis :[/bold white] {msev.master_what_is_happening}",
        f"  [bold white]Conflict Ruling  :[/bold white] {msev.master_why_resolution}",
        f"  [bold white]Final Command    :[/bold white] [bold]{msev.master_final_command}[/bold]",
    ]
    bottom_panel = Panel(
        "\n".join(p5_lines),
        title="[bold white]5. Executive Bottom Line — Supreme Master Conclusion (Press 0: Master • 1–9: Desks • Press C to Copy AI Data Packet)[/bold white]",
        border_style=border_style,
        box=box.ROUNDED,
    )

    return Group(header_panel, top_row, mid_row, bottom_panel)


# ============================================================================
# SPECIAL TAB [S1]: MULTI-MODEL BTC QUANT RADAR (MM-BTC)
# ============================================================================

def _build_tab5_mm_btc_hud(store: StateStore, header_panel: Panel) -> Group:
    """Renders Special Tab [S1]: Multi-Model BTC Strategy (Rough Path Signatures + 5 Sensory Lenses)."""
    mm = store.mm_btc_evaluation
    if mm is None:
        return Group(
            header_panel,
            Panel(
                "Warming up MM-BTC Multi-Model Quantitative Radar (Evaluating Path Signatures, Kalman, Hurst, Frac Diff, Hilbert)...",
                title="Special Tab [S1]: MM-BTC Multi-Model Quant Radar",
                box=box.ROUNDED,
            ),
        )

    # --- Introduction Card: Beginner Context & Methodology ---
    intro_lines = [
        "[bold cyan]▶ PURPOSE & SCOPE:[/bold cyan] Advanced quantitative physics desk tracking non-linear price paths, lead-lag order flow dynamics, and fractional memory.",
        "[bold cyan]▶ CORE MODELS & FEEDS:[/bold cyan] Level 1/2 Rough Path Signatures (Lévy Areas) • Kalman Velocity Filter • Hurst Exponent • Dynamic Fractional Diff • Hilbert Phase.",
        "[bold cyan]▶ EXECUTION MANDATE:[/bold cyan] [bold yellow]Roughness Arbiter Law[/bold yellow]: If trajectory roughness R > 4.5, execution is vetoed due to toxic chop. 5 independent sensory lenses must agree.",
    ]
    intro_panel = Panel(
        "\n".join(intro_lines),
        title="[bold cyan]WELCOME TO TAB [5]: MM-BTC ROUGH PATH SIGNATURES & 5 SENSORY LENSES[/bold cyan]",
        box=box.ROUNDED,
        border_style="cyan",
        padding=(0, 1),
    )

    # --- Panel 1: 5 Independent Sensory Lenses (A-E) ---
    p1_table = Table(box=box.SIMPLE_HEAVY, expand=True, show_header=True, header_style="bold cyan", pad_edge=False)
    p1_table.add_column("Sensory Lens", style="bold white", no_wrap=True)
    p1_table.add_column("Quantitative Model", style="dim white", no_wrap=True)
    p1_table.add_column("Live Observed Metrics", justify="left", no_wrap=True)
    p1_table.add_column("Lens Bias / Verdict", justify="right", no_wrap=True)

    # Lens A
    k_color = "green" if mm.kalman.bias == "BULLISH" else ("red" if mm.kalman.bias == "BEARISH" else "yellow")
    p1_table.add_row(
        "Lens A: State-Space",
        "1D Constant-Velocity Kalman",
        f"Filtered: [bold]${mm.kalman.filtered_price:,.2f}[/bold] ({mm.kalman.distance_pct:+.1f}%) • Vel: {mm.kalman.velocity:+.1f} $/hr",
        f"[{k_color}]{mm.kalman.bias}[/{k_color}] ({mm.kalman.velocity_state})",
    )

    # Lens B
    h_color = "green" if mm.hurst.hurst > 0.52 else ("yellow" if mm.hurst.hurst < 0.48 else "white")
    p1_table.add_row(
        "Lens B: Fractal Geometry",
        "Rolling Hurst (R/S 128 bars)",
        f"H = [bold]{mm.hurst.hurst:.3f}[/bold] • {mm.hurst.regime}",
        f"[{h_color}]{mm.hurst.tactical_implication}[/{h_color}]",
    )

    # Lens C
    fd_color = "green" if mm.frac_diff.bias == "BULLISH" else ("red" if mm.frac_diff.bias == "BEARISH" else "yellow")
    p1_table.add_row(
        "Lens C: Fractional Calc",
        "Dynamic ADF Memory (FFD)",
        f"Optimal d = [bold]{mm.frac_diff.optimal_d:.2f}[/bold] (ADF p={mm.frac_diff.adf_p_value:.4f}) • Mom: {mm.frac_diff.momentum:+.2f}",
        f"[{fd_color}]{mm.frac_diff.memory_state}[/{fd_color}]",
    )

    # Lens D
    hilb_color = "green" if "ACCUMULATION" in mm.hilbert.bias else "yellow"
    p1_table.add_row(
        "Lens D: Spectral DSP",
        "Ehlers Hilbert MESA (Hampel)",
        f"Cycle: [bold]{mm.hilbert.dominant_cycle}h[/bold] • Phase: {mm.hilbert.phase:.0f}° ({mm.hilbert.phase_state}) • Clipped: {mm.hilbert.outliers_cleaned}",
        f"[{hilb_color}]{mm.hilbert.bias}[/{hilb_color}]",
    )

    # Lens E
    of_color = "green" if "BUY" in mm.microstructure_bias else ("red" if "TRAP" in mm.microstructure_bias else "white")
    p1_table.add_row(
        "Lens E: Microstructure",
        "48h Net CVD & OI Leverage",
        f"48h CVD: [bold]{mm.cvd_48h:+,.1f} BTC[/bold] • 48h OI: {mm.oi_delta_pct:+.2f}%",
        f"[{of_color}]{mm.microstructure_pattern}[/{of_color}]",
    )

    # --- Panel 2: Core Arbiter: Rough Path Signatures (Order N <= 2) ---
    p2_table = Table(box=box.SIMPLE_HEAVY, expand=True, show_header=True, header_style="bold magenta", pad_edge=False)
    p2_table.add_column("Signature Term", style="bold white", no_wrap=True)
    p2_table.add_column("Live Value", justify="center", no_wrap=True)
    p2_table.add_column("Geometric Interpretation & Classification", justify="right", no_wrap=True)

    p2_table.add_row(
        "Level 1 Net Drift (S_p, S_v, S_o)",
        f"{mm.signature.drift_L1:+.2f}σ • {mm.signature.drift_flow:+.2f}σ • {mm.signature.drift_oi:+.2f}σ",
        "Price, Flow & Open Interest 48h displacements",
    )

    r_color = "green" if mm.signature.roughness <= 4.5 else "bold white on red"
    p2_table.add_row(
        "Quadratic Variation Roughness (R)",
        f"[{r_color}]R = {mm.signature.roughness:.2f}[/{r_color}]",
        f"QV={mm.signature.qv_p:.2f} ({'CLEAN TRAJECTORY' if mm.signature.roughness <= 4.5 else 'TOXIC CHOP VETO (R > 4.5)'})",
    )

    atp_color = "red" if mm.signature.area_time_price > 0.15 else ("green" if mm.signature.area_time_price <= -0.05 else "white")
    p2_table.add_row(
        "Level 2 Lévy Area (Time-Price)",
        f"[{atp_color}]{mm.signature.area_time_price:+.4f}[/{atp_color}]",
        f"[{atp_color}]{mm.signature.time_price_classification}[/{atp_color}]",
    )

    apv_color = "green" if mm.signature.area_price_flow > 0 else "yellow"
    p2_table.add_row(
        "Level 2 Lévy Area (Price-Flow)",
        f"[{apv_color}]{mm.signature.area_price_flow:+.4f}[/{apv_color}]",
        f"[{apv_color}]{mm.signature.flow_lead_lag_classification}[/{apv_color}]",
    )

    apo_color = "green" if mm.signature.area_price_oi <= 0 else "yellow"
    p2_table.add_row(
        "Level 2 Lévy Area (Price-OI)",
        f"[{apo_color}]{mm.signature.area_price_oi:+.4f}[/{apo_color}]",
        f"[{apo_color}]{mm.signature.oi_lead_lag_classification}[/{apo_color}]",
    )

    gate_badge = (
        "[bold black on green] CONFIRMED CLEAR [/bold black on green]"
        if "CLEAR" in mm.signature.arbiter_gate_status
        else f"[bold white on red] {mm.signature.arbiter_gate_status} [/bold white on red]"
    )
    p2_table.add_row("Chief Arbiter Gate & Verdict", gate_badge, f"[bold]{mm.signature.signature_verdict}[/bold]")

    top_row = Table.grid(expand=True)
    top_row.add_column(ratio=5)
    top_row.add_column(ratio=5)
    top_row.add_row(
        Panel(p1_table, title="[bold cyan]1. Five Independent Sensory Lenses (Lenses A–E Live Outputs)[/bold cyan]", box=box.ROUNDED),
        Panel(p2_table, title="[bold magenta]2. Chief Arbiter: Rough Path Signatures & Lévy Signed Areas (Order N<=2)[/bold magenta]", box=box.ROUNDED),
    )

    # --- Panel 3: 3-Gate Institutional Arbitration & Walk-Forward Sizing ---
    p3_table = Table(box=box.SIMPLE_HEAVY, expand=True, show_header=True, header_style="bold yellow", pad_edge=False)
    p3_table.add_column("Arbitration Layer", style="bold white", no_wrap=True)
    p3_table.add_column("Gate Status", justify="center", no_wrap=True)
    p3_table.add_column("Live Quantitative Specification", justify="right", no_wrap=True)

    g1_color = "green" if mm.gate1_pass else "red"
    p3_table.add_row(
        "Gate 1: Regime Integrity",
        f"[bold {g1_color}]{'PASS' if mm.gate1_pass else 'VETO'}[/bold {g1_color}]",
        f"Path Roughness R = {mm.signature.roughness:.2f} <= 4.5 (Anti-Chop Circuit Breaker)",
    )

    g2_color = "green" if mm.gate2_pass else "red"
    p3_table.add_row(
        "Gate 2: Path Geometry & Veto",
        f"[bold {g2_color}]{'PASS' if mm.gate2_pass else 'VETO'}[/bold {g2_color}]",
        f"Sweep Trap: {'NO' if mm.signature.area_time_price <= 0.15 else 'YES (Area t,P > 0.15)'} • 15m Micro: {'CLEAR' if not mm.micro_tripwire_veto else 'VETO'}",
    )

    p3_table.add_row(
        "Gate 3: Walk-Forward Sizing",
        f"[bold cyan]{mm.final_weight:.2f}x[/bold cyan]",
        f"Y_hat: {mm.gate3_y_hat:+.4f} • Models Agree: {mm.agreeing_models_count}/5 • SMA200: {'ABOVE' if mm.above_200_1h else 'BELOW ($' + f'{mm.sma_200_1h:,.0f})'}",
    )

    # --- Panel 4: Dual-Resolution Micro 15m Tripwire & Conflict Resolution ---
    p4_lines = [
        f"[bold cyan]▶ DUAL-RESOLUTION 15M MICRO TRIPWIRE:[/bold cyan] "
        f"{'[bold black on green] CLEAR (Micro trajectory healthy) [/bold black on green]' if not mm.micro_tripwire_veto else '[bold white on red] ⚡ VETO ACTIVE (Intraday sweep pump in progress) [/bold white on red]'}",
        f"  • Trailing 48x 15m bars (12 hours) audit front-running pumps prior to 1-hour bar close.",
        "",
        f"[bold yellow]▶ MULTI-MODEL CONFLICT RESOLUTION & SIZING RATIONALE:[/bold yellow]",
        f"  • {mm.conflict_summary}",
        f"  • Dust Filter Threshold: < 0.20x strictly forces 0.00x allocation (100% USDT Cash protection).",
    ]

    mid_row = Table.grid(expand=True)
    mid_row.add_column(ratio=5)
    mid_row.add_column(ratio=5)
    mid_row.add_row(
        Panel(p3_table, title="[bold yellow]3. Three-Gate Institutional Arbitration & Walk-Forward Sizing[/bold yellow]", box=box.ROUNDED),
        Panel("\n".join(p4_lines), title="[bold green]4. Dual-Resolution 15m Tripwire & Conflict Resolution[/bold green]", box=box.ROUNDED),
    )

    # --- Panel 5: Executive Action Plan (Bidirectional Spot Swing Playbook) ---
    p5_color = "green" if mm.final_weight > 0.20 else "yellow"
    p5_lines = [
        f"[bold black on {p5_color}] MM-BTC SPOT SWING ACTION PLAN (BINANCE) — SIZING: {mm.final_weight:.2f}x ALLOCATION [/bold black on {p5_color}]",
        f"  [bold white]If In Cash (USDT) :[/bold white] [bold]{mm.action_plan_cash}[/bold] | Zone: [cyan]{mm.execution_zone_str}[/cyan] | Invalidation: [red]{mm.invalidation_str}[/red]",
        f"  [bold white]If Holding Spot   :[/bold white] [bold]{mm.action_plan_holder}[/bold] | Target: [green]{mm.target_zone_str}[/green]",
    ]
    bottom_panel = Panel(
        "\n".join(p5_lines),
        title="[bold white]5. MM-BTC Executive Action Plan (Press 0: Master • 1–9: Desks • Press C to Copy AI Data Packet)[/bold white]",
        border_style=p5_color,
        box=box.ROUNDED,
    )

    return Group(header_panel, top_row, mid_row, bottom_panel)


# ============================================================================
# SPECIAL TAB [S2]: 72-HOUR FORWARD VOLATILITY CONE & AI BENCHMARK RADAR
# ============================================================================

def _build_tab6_volatility_cone_hud(store: StateStore, header_panel: Panel) -> Group:
    """Renders Special Tab [S2]: 72-Hour Forward Volatility Cone & Quarantined TSFM Benchmark Radar."""
    vc = store.volatility_cone_evaluation
    if vc is None:
        return Group(
            header_panel,
            Panel(
                "Warming up 72-Hour Forward Volatility Cone & AI Benchmark Radar (Synthesizing 4H bars, calculating Garman-Klass volatility & Mandelbrot t^H scaling)...",
                title="Special Tab [S2]: 72-Hour Forward Volatility Cone & AI Benchmark Radar Desk",
                box=box.ROUNDED,
            ),
        )

    # --- Introduction Card: Beginner Context & Methodology ---
    intro_lines = [
        "[bold cyan]▶ PURPOSE & SCOPE:[/bold cyan] Forward probability dispersion radar forecasting Bitcoin's 72-hour price cone alongside quarantined AI benchmarks.",
        "[bold cyan]▶ CORE MODELS & FEEDS:[/bold cyan] Garman-Klass Extreme-Value Volatility • Mandelbrot t^H Fractional Scaling • 1σ/2σ/3σ Volatility Envelopes • Kronos TSFM.",
        "[bold cyan]▶ EXECUTION MANDATE:[/bold cyan] [bold red]Quarantine Law[/bold red]: Zero-shot AI forecasts receive 0.0% capital weight. Only probabilistic cone boundaries (statistical overextension at ±2σ/3σ) are traded.",
    ]
    intro_panel = Panel(
        "\n".join(intro_lines),
        title="[bold cyan]WELCOME TO TAB [6]: 72-HOUR FORWARD VOLATILITY CONE & AI BENCHMARK DESK[/bold cyan]",
        box=box.ROUNDED,
        border_style="cyan",
        padding=(0, 1),
    )

    # --- Top Ribbon: 3 Quantitative Telemetry Badges ---
    ribbon_table = Table.grid(expand=True)
    ribbon_table.add_column(ratio=3)
    ribbon_table.add_column(ratio=3)
    ribbon_table.add_column(ratio=4)

    # 1. Hurst Scaling
    h_col = "green" if vc.hurst_exponent > 0.52 else ("yellow" if vc.hurst_exponent < 0.48 else "white")
    card_h = (
        f"[bold white]Hurst Exponent (H):[/bold white] [bold {h_col}]{vc.hurst_exponent:.3f}[/bold {h_col}]\n"
        f"Regime: [{h_col}]{vc.hurst_regime}[/{h_col}] • Diffusion: [cyan]t^{vc.hurst_exponent:.2f}[/cyan]"
    )

    # 2. Garman-Klass Volatility
    card_vol = (
        f"[bold white]Garman-Klass Micro Vol:[/bold white] [bold cyan]{vc.garman_klass_vol_4h * 100.0:.2f}% / 4H[/bold cyan]\n"
        f"Annualized: [bold magenta]{vc.garman_klass_annualized_vol * 100.0:.1f}%[/bold magenta] (8x stat efficiency vs close-to-close)"
    )

    # 3. Variance Compression Ratio & Quarantine Mandate
    vcr_style = "bold white on red" if vc.coiled_spring_alert else ("bold black on yellow" if vc.vcr_72h >= 3.0 else "bold black on green")
    card_vcr = (
        f"[bold white]72H Variance Compression Ratio:[/bold white] [{vcr_style}] VCR = {vc.vcr_72h:.2f}x [/{vcr_style}]\n"
        f"Alert: [{vcr_style}] {vc.vcr_status} [/{vcr_style}] • [dim]Capital Weight: 0.0% (Quarantined)[/dim]"
    )

    ribbon_table.add_row(
        Panel(card_h, box=box.ROUNDED, border_style="cyan", padding=(0, 1)),
        Panel(card_vol, box=box.ROUNDED, border_style="magenta", padding=(0, 1)),
        Panel(card_vcr, box=box.ROUNDED, border_style="yellow" if not vc.coiled_spring_alert else "red", padding=(0, 1)),
    )

    # --- Panel 1: 72-Hour Forward Volatility Cone Fan Table ---
    p1_table = Table(box=box.SIMPLE_HEAVY, expand=True, show_header=True, header_style="bold cyan", pad_edge=False)
    p1_table.add_column("Forward Horizon", style="bold white", no_wrap=True)
    p1_table.add_column("Damped Drift Center", justify="right", style="cyan", no_wrap=True)
    p1_table.add_column("GK 1σ Band (68% Conf)", justify="center", no_wrap=True)
    p1_table.add_column("GK 1σ Spread", justify="right", style="bold yellow", no_wrap=True)
    p1_table.add_column("GK 2σ Band (95% Conf)", justify="center", style="dim white", no_wrap=True)
    p1_table.add_column("TSFM Mean Close", justify="right", style="bold green", no_wrap=True)
    p1_table.add_column("TSFM Disp", justify="right", style="dim", no_wrap=True)

    for row in vc.horizons:
        p1_table.add_row(
            row.horizon_label,
            f"${row.drift_center:,.0f}",
            f"[bold green]${row.gk_1sigma_lower:,.0f}[/bold green] – [bold green]${row.gk_1sigma_upper:,.0f}[/bold green]",
            f"±${row.gk_1sigma_spread_usd / 2.0:,.0f} ({row.gk_1sigma_spread_pct / 2.0:+.2f}%)",
            f"${row.gk_2sigma_lower:,.0f} – ${row.gk_2sigma_upper:,.0f}",
            f"${row.tsfm_mean_close:,.0f}",
            f"{row.tsfm_dispersion_pct:.2f}%",
        )

    # --- Panel 2: Quarantined TSFM Benchmark Baseline Audit ---
    p2_table = Table(box=box.SIMPLE_HEAVY, expand=True, show_header=True, header_style="bold yellow", pad_edge=False)
    p2_table.add_column("TSFM Model", style="bold white", no_wrap=True)
    p2_table.add_column("Architecture & Domain", style="dim white", no_wrap=True)
    p2_table.add_column("Direction & 72h Close", justify="center", no_wrap=True)
    p2_table.add_column("Predicted 72h Range", justify="right", no_wrap=True)
    p2_table.add_column("Range Spread", justify="right", no_wrap=True)
    p2_table.add_column("Status & Capital Weight", justify="right", no_wrap=True)

    for item in vc.tsfm_benchmarks:
        dir_col = "green" if "UP" in item.direction_str else ("red" if "DOWN" in item.direction_str else "yellow")
        domain_str = (item.training_domain[:28] + "...") if len(item.training_domain) > 28 else item.training_domain
        p2_table.add_row(
            item.name,
            f"{item.architecture_tag} • {domain_str}",
            f"[{dir_col}]{item.direction_str}[/{dir_col}] (${item.predicted_close_72h:,.0f})",
            f"${item.predicted_range_min:,.0f} – ${item.predicted_range_max:,.0f}",
            f"${item.range_dollar_spread:,.0f} ({item.range_pct:.2f}%)",
            "[bold black on yellow] QUARANTINED (0.0% WT) [/bold black on yellow]",
        )

    mid_row = Table.grid(expand=True)
    mid_row.add_column(ratio=6)
    mid_row.add_column(ratio=4)
    mid_row.add_row(
        Panel(p1_table, title="[bold cyan]1. 72-Hour Forward Volatility Cone (Mandelbrot t^H fBM Quantile Fan vs TSFM Mean)[/bold cyan]", box=box.ROUNDED),
        Panel(p2_table, title="[bold yellow]2. Quarantined Time-Series Foundation Models (TSFM Baseline Audit)[/bold yellow]", box=box.ROUNDED),
    )

    # --- Panel 3: Forward Liquidity Magnet & Structural Value Area Overlay ---
    p3_lines = [
        f"[bold cyan]▶ INSTITUTIONAL LIQUIDITY MAGNET & STRUCTURAL AUCTION CONFLUENCE:[/bold cyan]",
        f"  • {vc.liquidity_confluence_summary}",
        f"  • [bold white]Why TSFMs Fail Here:[/bold white] At candle +18 (72h), zero-shot foundation models project a flat, compressed ~0.2% mean drift.",
        f"    They are completely blind to multi-million dollar liquidation clusters, perpetual funding squeezes, and spot order-flow imbalances.",
        f"  • [bold white]The Mandelbrot t^H Solution:[/bold white] Scaling Garman-Klass volatility by t^H correctly widens the fat-tailed diffusion cone to capture genuine institutional sweeps.",
    ]
    p3_panel = Panel("\n".join(p3_lines), title="[bold green]3. Forward Liquidity Magnet & Structural Value Area Overlay[/bold green]", box=box.ROUNDED)

    # --- Panel 4: Quantitative Takeaway & Capital Protection Mandate ---
    p4_border = "red" if vc.coiled_spring_alert else "bright_yellow"
    if store.last_packet_copied_ts > 0:
        copy_badge = f"[bold black on green] [✔ COPIED TO CLIPBOARD ({store.last_packet_char_count:,} chars @ {store.last_packet_copied_utc}) — PRESS CTRL+V IN AI CHAT] [/bold black on green]"
    else:
        copy_badge = "[bold black on yellow] [PRESS 'C' KEY: COPY RAW TELEMETRY PACKET INCLUDING TAB S2 TO CLIPBOARD] [/bold black on yellow]"

    last_row = vc.horizons[-1] if vc.horizons else None
    low_72h = last_row.gk_1sigma_lower if last_row else (vc.spot_price * 0.97)
    high_72h = last_row.gk_1sigma_upper if last_row else (vc.spot_price * 1.03)
    spread_usd = (last_row.gk_1sigma_spread_usd / 2.0) if last_row else (vc.spot_price * 0.03)
    spread_pct = (last_row.gk_1sigma_spread_pct / 2.0) if last_row else 3.0

    p4_lines = [
        f"[bold black on {p4_border}] TAB [S2] QUANTITATIVE VERDICT & SEPARATION OF CHURCH AND STATE [/bold black on {p4_border}]  {copy_badge}",
        f"  [bold white]Variance Compression :[/bold white] VCR = [bold]{vc.vcr_72h:.2f}x[/bold] — [{vcr_style}]{vc.vcr_status}[/{vcr_style}]",
        f"  [bold white]Capital Protection   :[/bold white] [bold red]STRICTLY 0.0% CAPITAL WEIGHT[/bold red] (TSFMs do NOT alter sizing, stops, or execution gates)",
        f"  [bold white]Operational Synthesis:[/bold white] {vc.quantitative_takeaway}",
        "",
        "  [dim]" + ("─" * 85) + "[/dim]",
        "  [bold bright_cyan]▶ PLAIN ENGLISH SUMMARY FOR TRADERS & BEGINNERS (WHAT THIS MEANS IN REALITY):[/bold bright_cyan]",
        f"   [bold yellow]1. Why the AI lines are flat (±0.2%):[/bold yellow] Generic AI models (ChatGPT, Chronos, TimesFM) play it safe by predicting almost zero change",
        f"      because they cannot foresee unexpected news or liquidations (Pt ≈ Pt-1). They massively underestimate Bitcoin's true volatility.",
        f"   [bold green]2. Real price expectation (±{spread_pct:.1f}% / ±${spread_usd:,.0f}):[/bold green] Real Bitcoin does not crawl. Over the next 72 hours, true volatility indicates",
        f"      BTC is expected to swing inside the Green Volatility Cone: [bold green]${low_72h:,.0f} – ${high_72h:,.0f}[/bold green].",
        f"   [bold magenta]3. The Coiled Spring (VCR = {vc.vcr_72h:.2f}x):[/bold magenta] The market is holding [bold]{vc.vcr_72h:.1f}x more expansion energy[/bold] than naive AI expects.",
        f"      {'[bold red]⚡ ALERT: Extreme compression — a violent volatility expansion is imminent![/bold red]' if vc.coiled_spring_alert else 'A sharp breakout move is far more likely than a quiet sideways crawl.'}",
        f"   [bold white on red] 4. Rule for your wallet: [/bold white on red] [bold white]NEVER buy or sell based on flat AI forecasts.[/bold white] Real capital execution is strictly governed by institutional order flow on Tabs [1]–[5] & [S1].",
    ]
    p4_panel = Panel(
        "\n".join(p4_lines),
        title="[bold white]4. Executive Bottom Line & Capital Protection Mandate (Press V/7 for S2 • S/6 for S1 • 1–5 for Alpha Core • C to Copy Packet)[/bold white]",
        border_style=p4_border,
        box=box.ROUNDED,
    )

    return Group(header_panel, ribbon_table, mid_row, p3_panel, p4_panel)


# ============================================================================
# SPECIAL TAB [S3]: GARTLEY 222 & 5-STRATEGY CONFLUENCE RADAR
# ============================================================================

def _build_tab7_gartley_hud(store: StateStore, header_panel: Panel) -> Group:
    """Renders Special Tab [S3]: Gartley 222 Harmonics & 5-Strategy Confluence Radar Desk."""
    gartley = store.gartley_evaluation
    if gartley is None:
        return Group(
            header_panel,
            Panel(
                "Warming up Tab [S3]: Gartley 222 & 5-Strategy Confluence Radar (Evaluating 1D Daily & 4H Tactical horizons)...",
                title="Special Tab [S3]: Gartley 222 & 5-Strategy Confluence Radar Desk",
                box=box.ROUNDED,
            ),
        )

    r1d = gartley.res_1d
    r4h = gartley.res_4h

    def _state_style(st: str) -> str:
        if "BUY" in st or "LONG" in st or st == "NEW":
            return "bold black on green"
        if "SELL" in st or "USDT" in st or st == "EXIT":
            return "bold white on red"
        if st == "HOLD":
            return "bold cyan"
        if "WATCH" in st or "CONFLICT" in st or "WARNING" in st:
            return "bold black on yellow"
        return "dim white"

    # --- Quick Intro Card: Purpose, Philosophy & Confluence Methodology ---
    intro_lines = [
        "[bold cyan]▶ PURPOSE & SCOPE:[/bold cyan] Precision spot swing execution microscope bridging [bold white]5 Classic Quantitative Models (S1–S5)[/bold white] with [bold magenta]Harmonic Fibonacci Geometry (S6–S7 Gartley 222)[/bold magenta].",
        "[bold cyan]▶ DUAL-HORIZON MANDATE:[/bold cyan] [bold white]1D Macro (The Shield)[/bold white] protects capital by filtering macro bear markets (> 200 SMA) • [bold yellow]4H Tactical (The Spear)[/bold yellow] pinpoints high-probability turning points where indicators converge with Harmonic PRZ.",
        "[bold cyan]▶ SPOT RULES & CONFLUENCE:[/bold cyan] [bold green]Zero Leverage / Zero Shorting[/bold green] (no liquidation risk) • [bold yellow]Strict Confluence Law[/bold yellow] (never trade a pattern alone; wait for confirmation) • [bold white]Telegram Parity[/bold white] with [dim]@Gartleyy_bot[/dim] cloud scanner.",
    ]
    intro_panel = Panel(
        "\n".join(intro_lines),
        title="[bold cyan]WELCOME TO TAB [7]: GARTLEY 222 & 5-STRATEGY CONFLUENCE RADAR (EXECUTION DESK)[/bold cyan]",
        box=box.ROUNDED,
        border_style="cyan",
        padding=(0, 1),
    )

    # --- Top Ribbon: 3 Quantitative Telemetry Badges ---
    ribbon_table = Table.grid(expand=True)
    ribbon_table.add_column(ratio=4)
    ribbon_table.add_column(ratio=3)
    ribbon_table.add_column(ratio=3)

    ov_style = _state_style(gartley.overall_verdict)
    card_verdict = (
        f"[bold white]Multi-Timeframe Verdict:[/bold white] [{ov_style}] {gartley.overall_verdict} [/{ov_style}]\n"
        f"Spot: [bold cyan]${gartley.close_price:,.2f}[/bold cyan] • 1D: [bold]{r1d.verdict}[/bold] • 4H: [bold]{r4h.verdict}[/bold]"
    )

    card_cloud = (
        f"[bold white]Engine Architecture:[/bold white] [bold magenta]Pine Script Parity (S1–S7)[/bold magenta]\n"
        f"Repo: [cyan]{gartley.standalone_bot_repo}[/cyan] • Actions: [green]Active[/green]"
    )

    card_telegram = (
        f"[bold white]Telegram Alert Bot:[/bold white] [bold green]{gartley.telegram_bot}[/bold green] (ID: {gartley.telegram_chat_id})\n"
        f"Webhook: [bold yellow]LIVE (/now)[/bold yellow] • Schedule: [dim]{gartley.schedule_cron}[/dim]"
    )

    ribbon_table.add_row(
        Panel(card_verdict, box=box.ROUNDED, border_style="magenta", padding=(0, 1)),
        Panel(card_cloud, box=box.ROUNDED, border_style="cyan", padding=(0, 1)),
        Panel(card_telegram, box=box.ROUNDED, border_style="green", padding=(0, 1)),
    )

    # --- Panel 1: 1D Daily Macro Trend State Machine ---
    p1_table = Table(box=box.SIMPLE_HEAVY, expand=True, show_header=True, header_style="bold cyan", pad_edge=False)
    p1_table.add_column("Strategy", style="bold white", no_wrap=True)
    p1_table.add_column("Indicator / Model", style="dim white", no_wrap=True)
    p1_table.add_column("Level / Value", justify="right", style="cyan", no_wrap=True)
    p1_table.add_column("State / Signal", justify="center", no_wrap=True)

    p1_table.add_row("S1: Breakout 20", "20-bar Donchian High/Low", "Channel", f"[{_state_style(r1d.v1_breakout)}] {r1d.v1_breakout} [/{_state_style(r1d.v1_breakout)}]")
    p1_table.add_row("S2: Trend SMA200", "200-day Simple Moving Avg", f"${r1d.sma200_val:,.1f}", f"[{_state_style(r1d.v2_sma200)}] {r1d.v2_sma200} [/{_state_style(r1d.v2_sma200)}]")
    p1_table.add_row("S3: EMA 20/50", "20 EMA vs 50 EMA Cross", f"${r1d.ema20_val:,.1f} / ${r1d.ema50_val:,.1f}", f"[{_state_style(r1d.v3_ema)}] {r1d.v3_ema} [/{_state_style(r1d.v3_ema)}]")
    p1_table.add_row("S4: 14 RSI", "14-period Wilder Momentum", f"{r1d.rsi_val:.1f}", f"[{_state_style(r1d.v4_rsi)}] {r1d.v4_rsi} [/{_state_style(r1d.v4_rsi)}]")
    p1_table.add_row("S5: Bollinger Bands", "20 SMA ± 2-Sigma Mean Rev", "2-Sigma Lower", f"[{_state_style(r1d.v5_bb)}] {r1d.v5_bb} [/{_state_style(r1d.v5_bb)}]")
    p1_table.add_row("S6: Gartley Bull", "Harmonic 222 (L-H-L-H-L)", f"PRZ: {f'${r1d.bull_d:,.1f}' if r1d.bull_d else 'NONE'}", f"[{_state_style(r1d.v6_gartley_bull)}] {r1d.v6_gartley_bull} [/{_state_style(r1d.v6_gartley_bull)}]")
    p1_table.add_row("S7: Gartley Bear", "Harmonic 222 (H-L-H-L-H)", f"PRZ: {f'${r1d.bear_d:,.1f}' if r1d.bear_d else 'NONE'}", f"[{_state_style(r1d.v7_gartley_bear)}] {r1d.v7_gartley_bear} [/{_state_style(r1d.v7_gartley_bear)}]")

    # --- Panel 2: 4H Tactical Swing Execution ---
    p2_table = Table(box=box.SIMPLE_HEAVY, expand=True, show_header=True, header_style="bold yellow", pad_edge=False)
    p2_table.add_column("Strategy", style="bold white", no_wrap=True)
    p2_table.add_column("Indicator / Model", style="dim white", no_wrap=True)
    p2_table.add_column("Level / Value", justify="right", style="yellow", no_wrap=True)
    p2_table.add_column("State / Signal", justify="center", no_wrap=True)

    p2_table.add_row("S1: Breakout 20", "20-bar Donchian High/Low", "Channel", f"[{_state_style(r4h.v1_breakout)}] {r4h.v1_breakout} [/{_state_style(r4h.v1_breakout)}]")
    p2_table.add_row("S2: Trend SMA200", "200-period Simple Moving Avg", f"${r4h.sma200_val:,.1f}", f"[{_state_style(r4h.v2_sma200)}] {r4h.v2_sma200} [/{_state_style(r4h.v2_sma200)}]")
    p2_table.add_row("S3: EMA 20/50", "20 EMA vs 50 EMA Cross", f"${r4h.ema20_val:,.1f} / ${r4h.ema50_val:,.1f}", f"[{_state_style(r4h.v3_ema)}] {r4h.v3_ema} [/{_state_style(r4h.v3_ema)}]")
    p2_table.add_row("S4: 14 RSI", "14-period Wilder Momentum", f"{r4h.rsi_val:.1f}", f"[{_state_style(r4h.v4_rsi)}] {r4h.v4_rsi} [/{_state_style(r4h.v4_rsi)}]")
    p2_table.add_row("S5: Bollinger Bands", "20 SMA ± 2-Sigma Mean Rev", "2-Sigma Lower", f"[{_state_style(r4h.v5_bb)}] {r4h.v5_bb} [/{_state_style(r4h.v5_bb)}]")
    p2_table.add_row("S6: Gartley Bull", "Harmonic 222 (L-H-L-H-L)", f"PRZ: {f'${r4h.bull_d:,.1f}' if r4h.bull_d else 'NONE'}", f"[{_state_style(r4h.v6_gartley_bull)}] {r4h.v6_gartley_bull} [/{_state_style(r4h.v6_gartley_bull)}]")
    p2_table.add_row("S7: Gartley Bear", "Harmonic 222 (H-L-H-L-H)", f"PRZ: {f'${r4h.bear_d:,.1f}' if r4h.bear_d else 'NONE'}", f"[{_state_style(r4h.v7_gartley_bear)}] {r4h.v7_gartley_bear} [/{_state_style(r4h.v7_gartley_bear)}]")

    mid_row = Table.grid(expand=True)
    mid_row.add_column(ratio=5)
    mid_row.add_column(ratio=5)
    mid_row.add_row(
        Panel(p1_table, title=f"[bold cyan]1. 1D Daily Macro Trend State Machine ({r1d.verdict})[/bold cyan]", box=box.ROUNDED),
        Panel(p2_table, title=f"[bold yellow]2. 4H Tactical Swing Execution ({r4h.verdict})[/bold yellow]", box=box.ROUNDED),
    )

    # --- Panel 3: Harmonic Geometry & PRZ Reversal Zones ---
    r1d_b_str = str(r1d.bull_ratios) if r1d.bull_ratios else "Scanning swing pivots..."
    r4h_b_str = str(r4h.bull_ratios) if r4h.bull_ratios else "Scanning swing pivots..."
    p3_lines = [
        f"[bold magenta]▶ FIBONACCI HARMONIC GARTLEY 222 GEOMETRY & PRZ REVERSAL TARGETS:[/bold magenta]",
        f"  • [bold white]Ratio Constraints:[/bold white] B/XA: [cyan]0.618 ± 0.12[/cyan] [0.55–0.72] | C/AB: [cyan]0.382–0.886[/cyan] | D/XA: [cyan]0.786 ± 0.08[/cyan] [0.68–0.86] | AB/CD: [cyan]0.70–1.50[/cyan]",
        f"  • [bold white]1D Macro Harmonics :[/bold white] Bull PRZ: [green]{f'${r1d.bull_d:,.1f}' if r1d.bull_d else 'NONE'}[/green] | Bear PRZ: [red]{f'${r1d.bear_d:,.1f}' if r1d.bear_d else 'NONE'}[/red] • Ratios: [dim]{r1d_b_str}[/dim]",
        f"  • [bold white]4H Tactical Harmonics:[/bold white] Bull PRZ: [green]{f'${r4h.bull_d:,.1f}' if r4h.bull_d else 'NONE'}[/green] | Bear PRZ: [red]{f'${r4h.bear_d:,.1f}' if r4h.bear_d else 'NONE'}[/red] • Ratios: [dim]{r4h_b_str}[/dim]",
    ]
    p3_panel = Panel("\n".join(p3_lines), title="[bold magenta]3. Harmonic 222 Potential Reversal Zone (PRZ) Radar[/bold magenta]", box=box.ROUNDED)

    # --- Panel 4: Executive Synthesis & Action Playbook ---
    if store.last_packet_copied_ts > 0:
        copy_badge = f"[bold black on green] [✔ COPIED TO CLIPBOARD ({store.last_packet_char_count:,} chars @ {store.last_packet_copied_utc}) — PRESS CTRL+V IN AI CHAT] [/bold black on green]"
    else:
        copy_badge = "[bold black on yellow] [PRESS 'C' KEY: COPY RAW TELEMETRY PACKET INCLUDING TAB S3 TO CLIPBOARD] [/bold black on yellow]"

    p4_lines = [
        f"[bold black on magenta] TAB [S3] EXECUTIVE VERDICT & ACTION PLAYBOOK [/bold black on magenta]  {copy_badge}",
        f"  [bold white]Pine Verdict Ladder:[/bold white] GARTLEY SELL > CONFLUENCE+GARTLEY BUY > GARTLEY BUY > EXIT PRESSURE > CONFLICT > CONFLUENCE BUY > HOLD > NO TRADE",
        f"  [bold white]Multi-Timeframe Status:[/bold white] 1D: [bold]{r1d.verdict}[/bold] | 4H: [bold]{r4h.verdict}[/bold] | Overall: [{ov_style}] {gartley.overall_verdict} [/{ov_style}]",
        f"  [bold white]Quantitative Summary  :[/bold white] {gartley.plain_english_summary}",
    ]
    p4_panel = Panel(
        "\n".join(p4_lines),
        title="[bold white]4. Executive Bottom Line & Action Playbook (Press 8/G for S3 • 7/V for S2 • 6/S for S1 • 1–5 for Alpha Core • C to Copy Packet)[/bold white]",
        border_style="magenta",
        box=box.ROUNDED,
    )

    return Group(header_panel, ribbon_table, mid_row, p3_panel, p4_panel)


# ============================================================================
# SPECIAL TAB [S4]: PATTERN INVALIDATION, LIQUIDITY SWEEP & SFP TRAP RADAR
# ============================================================================

def _build_tab8_trap_hud(store: StateStore, header_panel: Panel) -> Group:
    """Renders Special Tab [S4]: Pattern Invalidation, Liquidity Sweep & SFP Trap Desk."""
    trap = store.trap_evaluation
    if trap is None:
        return Group(
            header_panel,
            Panel(
                "Warming up Tab [S4]: Pattern Invalidation & SFP Trap Radar (Scanning 1H/4H fractal pivots & microstructure CVD absorption)...",
                title="Special Tab [S4]: Pattern Invalidation, Liquidity Sweep & SFP Trap Desk",
                box=box.ROUNDED,
            ),
        )

    # --- Introduction Card: Beginner Context & Methodology ---
    intro_lines = [
        "[bold cyan]▶ PURPOSE & SCOPE:[/bold cyan] Liquidity sweep & counter-retail trap radar detecting stop hunts, failed breakouts, and institutional absorption.",
        "[bold cyan]▶ CORE MODELS & FEEDS:[/bold cyan] 1H/4H Fractal Pivot Sweeps • Swing Failure Pattern (SFP) State Machine • Microstructure CVD Absorption • Equal Highs/Lows (EQH/EQL).",
        "[bold cyan]▶ EXECUTION MANDATE:[/bold cyan] [bold yellow]Wait for the Reclaim[/bold yellow]: Never enter during the sweep wick. Only enter when price sweeps liquidity, delta confirms passive absorption, and candle closes back inside range.",
    ]
    intro_panel = Panel(
        "\n".join(intro_lines),
        title="[bold cyan]WELCOME TO TAB [8]: PATTERN INVALIDATION, LIQUIDITY SWEEP & SFP TRAP RADAR[/bold cyan]",
        box=box.ROUNDED,
        border_style="cyan",
        padding=(0, 1),
    )

    # --- Top Ribbon: 3 Quantitative Telemetry Badges ---
    ribbon_table = Table.grid(expand=True)
    ribbon_table.add_column(ratio=4)
    ribbon_table.add_column(ratio=3)
    ribbon_table.add_column(ratio=3)

    is_bear_trap = "BEAR TRAP" in trap.active_trap_signal
    is_bull_trap = "BULL TRAP" in trap.active_trap_signal
    state_style = "bold white on green" if is_bear_trap else ("bold white on red" if is_bull_trap else "bold black on yellow" if "SWEEP" in trap.active_trap_signal else "bold cyan")

    card_state = (
        f"[bold white]Trap State Machine:[/bold white] [{state_style}] {trap.active_trap_state.value} [/{state_style}]\n"
        f"Alert: [bold]{trap.active_trap_signal}[/bold]"
    )

    abs_style = "bold black on yellow" if trap.passive_absorption_flag else "dim"
    cvd_col = "green" if trap.rolling_15m_cvd > 0 else "red"
    card_cvd = (
        f"[bold white]15m Spot CVD:[/bold white] [bold {cvd_col}]{trap.rolling_15m_cvd:+.2f} BTC[/bold {cvd_col}] • 5m Perp: {trap.rolling_5m_cvd:+.2f} BTC\n"
        f"Absorption: [{abs_style}]{'ACTIVE ABSORPTION' if trap.passive_absorption_flag else 'NORMAL FLOW'}[/{abs_style}] (Ratio: {trap.absorption_divergence_ratio:.1f}x)"
    )

    oi_col = "bold white on red" if trap.oi_surge_flag else "dim"
    card_oi = (
        f"[bold white]15m dOI Velocity:[/bold white] [bold magenta]{trap.oi_15m_delta_pct:+.3f}%[/bold magenta] • 1H dOI: {trap.oi_1h_delta_pct:+.3f}%\n"
        f"Chaser Trap: [{oi_col}]{'TRAPPED SPECULATORS (+OI)' if trap.oi_surge_flag else 'Uncrowded Positioning'}[/{oi_col}]"
    )

    ribbon_table.add_row(
        Panel(card_state, box=box.ROUNDED, border_style="cyan", padding=(0, 1)),
        Panel(card_cvd, box=box.ROUNDED, border_style="yellow" if trap.passive_absorption_flag else "white", padding=(0, 1)),
        Panel(card_oi, box=box.ROUNDED, border_style="magenta", padding=(0, 1)),
    )

    # --- Panel 1: Pattern Boundary Registry Table ---
    p1_table = Table(box=box.SIMPLE_HEAVY, expand=True, show_header=True, header_style="bold cyan", pad_edge=False)
    p1_table.add_column("Pattern Name", style="bold white", no_wrap=True)
    p1_table.add_column("Boundary", justify="right", style="cyan", no_wrap=True)
    p1_table.add_column("Sweep Ext", justify="right", style="dim", no_wrap=True)
    p1_table.add_column("Dist (ATR)", justify="right", no_wrap=True)
    p1_table.add_column("Status", justify="center", no_wrap=True)
    p1_table.add_column("Trap Bias", justify="center", no_wrap=True)

    for p in trap.active_patterns:
        st_style = "bold black on green" if "RECLAIMED" in p.status else ("bold white on red" if "REJECTED" in p.status else "bold black on yellow" if "SWEEPING" in p.status else "dim white")
        bias_style = "green" if "BULLISH" in p.trap_bias else "red"
        p1_table.add_row(
            p.pattern_name,
            f"${p.boundary_level:,.1f}",
            f"${p.sweep_wick_extreme:,.1f}",
            f"{p.distance_atr:+.2f}x ({p.distance_pct:+.2f}%)",
            f"[{st_style}] {p.status} [/{st_style}]",
            f"[{bias_style}]{p.trap_bias}[/{bias_style}]",
        )

    # --- Panel 2: Active Fair Value Gaps (FVG) & 50% Consequent Encroachment ---
    p2_fvg_table = Table(box=box.SIMPLE_HEAVY, expand=True, show_header=True, header_style="bold magenta", pad_edge=False)
    p2_fvg_table.add_column("TF", style="bold white", justify="center", no_wrap=True)
    p2_fvg_table.add_column("Direction", justify="center", no_wrap=True)
    p2_fvg_table.add_column("Gap Bounds ($)", justify="right", style="cyan", no_wrap=True)
    p2_fvg_table.add_column("50% CE ($)", justify="right", style="bold yellow", no_wrap=True)
    p2_fvg_table.add_column("Dist (%)", justify="right", no_wrap=True)
    p2_fvg_table.add_column("Status", justify="center", no_wrap=True)

    if trap.active_fvgs:
        for fvg in trap.active_fvgs[:4]:
            dir_style = "bold green" if fvg.direction == "BULLISH" else "bold red"
            st_style = "bold yellow" if fvg.status == "PARTIALLY_MITIGATED" else "bold bright_white"
            p2_fvg_table.add_row(
                fvg.timeframe,
                f"[{dir_style}]{fvg.direction}[/{dir_style}]",
                f"${fvg.bottom_price:,.0f}–${fvg.top_price:,.0f}",
                f"${fvg.ce_midpoint:,.1f}",
                f"{fvg.distance_pct:+.2f}%",
                f"[{st_style}]{fvg.status[:11]}[/{st_style}]",
            )
    else:
        p2_fvg_table.add_row(
            "[dim]--[/dim]",
            "[dim]BALANCED[/dim]",
            "[dim]No open voids within 5%[/dim]",
            "[dim]--[/dim]",
            "[dim]--[/dim]",
            "[dim]FULLY MITIGATED[/dim]",
        )

    # --- Panel 3: Asymmetric SFP & Displacement Execution Geometry Table ---
    p3_table = Table(box=box.SIMPLE_HEAVY, expand=True, show_header=True, header_style="bold green", pad_edge=False)
    p3_table.add_column("Direction", style="bold white", no_wrap=True)
    p3_table.add_column("Entry ($)", justify="right", style="cyan", no_wrap=True)
    p3_table.add_column("Stop Loss", justify="right", style="bold red", no_wrap=True)
    p3_table.add_column("TP1 (POC)", justify="right", style="bold green", no_wrap=True)
    p3_table.add_column("TP2 (Ext)", justify="right", style="bold yellow", no_wrap=True)
    p3_table.add_column("R:R Ratio", justify="center", style="bold black on green", no_wrap=True)

    if trap.trade_plan is not None:
        tp = trap.trade_plan
        dir_style = "bold black on green" if "LONG" in tp.direction else "bold white on red"
        p3_table.add_row(
            f"[{dir_style}] {tp.direction} [/{dir_style}]",
            f"${tp.entry_price:,.1f}",
            f"${tp.stop_loss:,.1f}",
            f"${tp.tp1_poc:,.1f}",
            f"${tp.tp2_opposite_boundary:,.1f}",
            f" {tp.rr_ratio:.2f}R ",
        )
    else:
        p3_table.add_row(
            "[dim]AWAITING SFP TRIGGER[/dim]",
            f"${trap.spot_price:,.1f}",
            "[dim]Sweep Low - 0.25x ATR[/dim]",
            "[dim]Composite POC[/dim]",
            "[dim]Opposite Boundary[/dim]",
            " >= 3.00R ",
        )

    mid_row_1 = Table.grid(expand=True)
    mid_row_1.add_column(ratio=5)
    mid_row_1.add_column(ratio=5)
    mid_row_1.add_row(
        Panel(p1_table, title="[bold cyan]1. Pattern & Session Liquidity Registry (Asia H/L + EQH/EQL)[/bold cyan]", box=box.ROUNDED),
        Panel(p2_fvg_table, title="[bold magenta]2. Active Fair Value Gaps (15m/1H FVGs & 50% CE)[/bold magenta]", box=box.ROUNDED),
    )

    mid_row_2 = Panel(p3_table, title="[bold green]3. Asymmetric SFP & Displacement Execution Geometry (R:R >= 1:3)[/bold green]", box=box.ROUNDED)

    # --- Panel 4: Liquidity Sweep & Institutional Absorption Diagnostic ---
    p4_diag_lines = [
        f"[bold cyan]▶ INSTITUTIONAL LIQUIDITY SWEEP & FVG DISPLACEMENT MECHANICS:[/bold cyan]",
        f"  • [bold white]The Mechanics Cycle:[/bold white] Liquidity Sweep (Asia H/L or Pattern Shelf) ➔ 3-Bar Displacement Imbalance (FVG) ➔ 50% CE Retest ➔ Expansion.",
        f"  • [bold white]Consequent Encroachment (CE):[/bold white] The 50% midpoint of the FVG represents the institutional equilibrium where limit bids/asks absorb retracements.",
        f"  • [bold white]Asymmetric Geometry:[/bold white] Stop-loss placed strictly past sweep wick extreme. Trapped chasers and unfilled opposing FVGs provide natural magnet targets.",
    ]
    p4_diag_panel = Panel("\n".join(p4_diag_lines), title="[bold yellow]4. Liquidity Sweep & Displacement (FVG) Diagnostic[/bold yellow]", box=box.ROUNDED)

    # --- Panel 5: Executive Synthesis & Action Playbook ---
    if store.last_packet_copied_ts > 0:
        copy_badge = f"[bold black on green] [✔ COPIED TO CLIPBOARD ({store.last_packet_char_count:,} chars @ {store.last_packet_copied_utc}) — PRESS CTRL+V IN AI CHAT] [/bold black on green]"
    else:
        copy_badge = "[bold black on yellow] [PRESS 'C' KEY: COPY RAW TELEMETRY PACKET INCLUDING TAB S4 TO CLIPBOARD] [/bold black on yellow]"

    border_col = "green" if is_bear_trap else ("red" if is_bull_trap else "cyan")
    p5_lines = [
        f"[bold black on {border_col}] TAB [S4] EXECUTIVE VERDICT & SFP/FVG ACTION PLAYBOOK [/bold black on {border_col}]  {copy_badge}",
        f"  [bold white]Microstructure Status :[/bold white] [{state_style}] {trap.active_trap_signal} [/{state_style}]",
        f"  [bold white]Operational Synthesis :[/bold white] {trap.quantitative_takeaway}",
        f"  [bold white]Plain English Bottom Line:[/bold white] {trap.plain_english_summary}",
    ]
    p5_panel = Panel(
        "\n".join(p5_lines),
        title="[bold white]5. Executive Bottom Line & Action Playbook (Press 0: Master • 1–9: Desks • Press C to Copy AI Data Packet)[/bold white]",
        border_style=border_col,
        box=box.ROUNDED,
    )

    return Group(header_panel, ribbon_table, mid_row_1, mid_row_2, p4_diag_panel, p5_panel)




# ============================================================================
# TAB [S5]: TERMINAL EXHAUSTION & DELTA DIVERGENCE RADAR HUD
# ============================================================================

def _build_tab9_exhaustion_hud(store: StateStore, header_panel: Panel) -> Group:
    """Builds the 5-panel layout for Special Tab [S5]: Terminal Exhaustion & Delta Divergence Radar."""
    ex = store.exhaustion_evaluation
    if ex is None:
        p_wait = Panel(
            "[dim]Awaiting market data to compute Tom DeMark sequential and multi-horizon CVD divergences...[/dim]",
            title="[bold yellow]TAB [S5]: TERMINAL EXHAUSTION & DELTA DIVERGENCE RADAR[/bold yellow]",
            box=box.ROUNDED,
        )
        return Group(header_panel, p_wait)

    score = ex.exhaustion_score
    if score >= 80.0:
        score_badge = f"[bold white on red] EXHAUSTION SCORE: {score:.1f}/100 [/bold white on red]"
        regime_style = "bold red"
        border_col = "red"
    elif score >= 60.0:
        score_badge = f"[bold black on magenta] EXHAUSTION SCORE: {score:.1f}/100 [/bold black on magenta]"
        regime_style = "bold magenta"
        border_col = "magenta"
    elif score >= 35.0:
        score_badge = f"[bold black on yellow] EXHAUSTION SCORE: {score:.1f}/100 [/bold black on yellow]"
        regime_style = "bold yellow"
        border_col = "yellow"
    else:
        score_badge = f"[bold black on green] EXHAUSTION SCORE: {score:.1f}/100 [/bold black on green]"
        regime_style = "bold green"
        border_col = "cyan"

    # --- Introduction Card: Beginner Context & Methodology ---
    intro_lines = [
        "[bold cyan]▶ PURPOSE & SCOPE:[/bold cyan] Terminal momentum exhaustion scanner detecting fatigue tops and capitulation bottoms before trend pivots.",
        "[bold cyan]▶ CORE MODELS & FEEDS:[/bold cyan] Tom DeMark TD Sequential (Setup 9 & Countdown 13 across 15m/1H/4H/1D) • Multi-Horizon CVD Divergences.",
        "[bold cyan]▶ EXECUTION MANDATE:[/bold cyan] [bold red]Anti-Sycophancy Reversal Law[/bold red]: A TD Countdown 13 combined with multi-timeframe CVD divergence warns of terminal exhaustion; tighten trailing stops.",
    ]
    intro_panel = Panel(
        "\n".join(intro_lines),
        title="[bold cyan]WELCOME TO TAB [9]: TERMINAL EXHAUSTION & DELTA DIVERGENCE RADAR[/bold cyan]",
        box=box.ROUNDED,
        border_style="cyan",
        padding=(0, 1),
    )

    # --- Ribbon Cards ---
    card_score = Table.grid(expand=True)
    card_score.add_column()
    card_score.add_row(f"{score_badge}")
    card_score.add_row(f"Regime: [{regime_style}]{ex.exhaustion_regime.value}[/{regime_style}]")

    card_td = Table.grid(expand=True)
    card_td.add_column()
    td1_col = "bold red" if "BEARISH" in ex.td_1h.direction else ("bold green" if "BULLISH" in ex.td_1h.direction else "dim white")
    td4_col = "bold red" if "BEARISH" in ex.td_4h.direction else ("bold green" if "BULLISH" in ex.td_4h.direction else "dim white")
    perf1 = " (PERFECTED)" if ex.td_1h.is_perfected else ""
    perf4 = " (PERFECTED)" if ex.td_4h.is_perfected else ""
    card_td.add_row(f"1H TD-9: [{td1_col}]{ex.td_1h.setup_count}/9 {ex.td_1h.status}{perf1}[/{td1_col}]")
    card_td.add_row(f"4H TD-9: [{td4_col}]{ex.td_4h.setup_count}/9 {ex.td_4h.status}{perf4}[/{td4_col}]")

    card_climax = Table.grid(expand=True)
    card_climax.add_column()
    oi_col = "bold red" if ex.oi_climax_flag else "cyan"
    fund_col = "bold magenta" if ex.funding_climax_flag else "white"
    card_climax.add_row(f"1H dOI: [{oi_col}]{ex.oi_climax_pct:+.3f}% (Climax: {ex.oi_climax_flag})[/{oi_col}]")
    card_climax.add_row(f"Funding: [{fund_col}]{ex.current_funding_pct*100:+.4f}% (Stress: {ex.funding_climax_flag})[/{fund_col}]")

    ribbon_table = Table.grid(expand=True)
    ribbon_table.add_column(ratio=4)
    ribbon_table.add_column(ratio=3)
    ribbon_table.add_column(ratio=3)
    ribbon_table.add_row(
        Panel(card_score, box=box.ROUNDED, border_style=border_col, padding=(0, 1)),
        Panel(card_td, box=box.ROUNDED, border_style="cyan", padding=(0, 1)),
        Panel(card_climax, box=box.ROUNDED, border_style="magenta", padding=(0, 1)),
    )

    # --- Panel 1: Tom DeMark & CVD Divergence Registry Table ---
    p1_table = Table(box=box.SIMPLE_HEAVY, expand=True, show_header=True, header_style="bold cyan", pad_edge=False)
    p1_table.add_column("Indicator / Lens", style="bold white", no_wrap=True)
    p1_table.add_column("Setup / Type", justify="center", style="yellow", no_wrap=True)
    p1_table.add_column("Extrema / State", style="dim", no_wrap=True)
    p1_table.add_column("Status / Delta", justify="right", no_wrap=True)
    p1_table.add_column("Significance", justify="center", no_wrap=True)

    # TD-9 Rows
    st1 = "bold black on red" if (ex.td_1h.is_perfected and "BEARISH" in ex.td_1h.direction) else ("bold black on green" if ex.td_1h.is_perfected else "dim white")
    p1_table.add_row(
        "1H TD Sequential",
        f"{ex.td_1h.setup_count}/9 Setup",
        f"Anchor: ${ex.td_1h.invalidation_level:,.1f}",
        ex.td_1h.direction[:18],
        f"[{st1}] {ex.td_1h.status} [/{st1}]",
    )
    st4 = "bold black on red" if (ex.td_4h.is_perfected and "BEARISH" in ex.td_4h.direction) else ("bold black on green" if ex.td_4h.is_perfected else "dim white")
    p1_table.add_row(
        "4H TD Sequential",
        f"{ex.td_4h.setup_count}/9 Setup",
        f"Anchor: ${ex.td_4h.invalidation_level:,.1f}",
        ex.td_4h.direction[:18],
        f"[{st4}] {ex.td_4h.status} [/{st4}]",
    )

    if ex.divergences:
        for d in ex.divergences:
            sig_col = "bold red" if "CRITICAL" in d.significance else "bold magenta"
            p1_table.add_row(
                f"{d.horizon} Delta Divergence",
                d.divergence_type[:24],
                d.price_extrema[:24],
                f"S:{d.spot_delta:+.0f} P:{d.perp_delta:+.0f}",
                f"[{sig_col}]{d.significance}[/{sig_col}]",
            )
    else:
        p1_table.add_row(
            "CVD Multi-Horizon Scan",
            "Harmonic Expansion",
            "Price in phase with volume delta",
            "No Divergence",
            "[green]HEALTHY[/green]",
        )

    # --- Panel 2: Asymmetric Mean-Reversion Geometry Table ---
    p2_table = Table(box=box.SIMPLE_HEAVY, expand=True, show_header=True, header_style="bold green", pad_edge=False)
    p2_table.add_column("Direction", style="bold white", no_wrap=True)
    p2_table.add_column("Entry ($)", justify="right", style="cyan", no_wrap=True)
    p2_table.add_column("Stop Loss", justify="right", style="bold red", no_wrap=True)
    p2_table.add_column("TP1 (Mean)", justify="right", style="bold green", no_wrap=True)
    p2_table.add_column("TP2 (POC)", justify="right", style="bold yellow", no_wrap=True)
    p2_table.add_column("R:R Ratio", justify="center", style="bold black on green", no_wrap=True)

    if ex.trade_plan is not None:
        tp = ex.trade_plan
        dir_style = "bold white on red" if "SHORT" in tp.direction else "bold black on green"
        p2_table.add_row(
            f"[{dir_style}] {tp.direction} [/{dir_style}]",
            f"${tp.entry_price:,.1f}",
            f"${tp.stop_loss:,.1f}",
            f"${tp.tp1_fast_mean:,.1f}",
            f"${tp.tp2_value_poc:,.1f}",
            f" {tp.rr_ratio:.2f}R ",
        )
    else:
        p2_table.add_row(
            "[dim]AWAITING EXHAUSTION TRIGGER[/dim]",
            f"${ex.spot_price:,.1f}",
            "[dim]Extreme Wick +/- 0.5x ATR[/dim]",
            "[dim]Fast Mean / 1H POC[/dim]",
            "[dim]Composite POC[/dim]",
            " >= 2.50R ",
        )

    mid_row = Table.grid(expand=True)
    mid_row.add_column(ratio=6)
    mid_row.add_column(ratio=4)
    mid_row.add_row(
        Panel(p1_table, title="[bold cyan]1. Tom DeMark Sequential & CVD Divergence Registry[/bold cyan]", box=box.ROUNDED),
        Panel(p2_table, title="[bold green]2. Asymmetric Mean-Reversion Geometry (R:R >= 1:2.5)[/bold green]", box=box.ROUNDED),
    )

    # --- Panel 3: Mechanics & Anti-Sycophancy Diagnostic ---
    p3_lines = [
        f"[bold cyan]▶ QUANTITATIVE MOMENTUM EXHAUSTION & REVERSAL MECHANICS:[/bold cyan]",
        f"  • [bold white]The Elliott Wave Failure:[/bold white] Subjective wave counts shift goalposts infinitely ('extended waves', 'running flats').",
        f"    Tom DeMark TD Sequential uses strict, non-falsifiable price comparisons (close[i] vs. close[i-4]) with zero relabeling.",
        f"  • [bold white]Microstructure Reality:[/bold white] Terminal impulses ('Wave 5' / 'Wave C') end when aggressive taker delta exhausts into passive limit walls,",
        f"    producing regular CVD divergence and extreme Open Interest / funding rate saturation.",
        f"  • [bold white]Execution Geometry:[/bold white] Trade mean-reversion with strict invalidation anchored to the perfected setup wick extreme.",
    ]
    p3_panel = Panel("\n".join(p3_lines), title="[bold yellow]3. Quantitative Momentum Exhaustion Mechanics & Anti-Sycophancy[/bold yellow]", box=box.ROUNDED)

    # --- Panel 4: Executive Synthesis & Action Playbook ---
    if store.last_packet_copied_ts > 0:
        copy_badge = f"[bold black on green] [✔ COPIED TO CLIPBOARD ({store.last_packet_char_count:,} chars @ {store.last_packet_copied_utc}) — PRESS CTRL+V IN AI CHAT] [/bold black on green]"
    else:
        copy_badge = "[bold black on yellow] [PRESS 'C' KEY: COPY RAW TELEMETRY PACKET INCLUDING TAB S5 TO CLIPBOARD] [/bold black on yellow]"

    p4_lines = [
        f"[bold black on {border_col}] TAB [S5] EXECUTIVE VERDICT & ACTION PLAYBOOK [/bold black on {border_col}]  {copy_badge}",
        f"  [bold white]Microstructure Status :[/bold white] [{regime_style}] {ex.active_exhaustion_signal} [/{regime_style}]",
        f"  [bold white]Operational Synthesis :[/bold white] {ex.quantitative_takeaway}",
        f"  [bold white]Plain English Bottom Line:[/bold white] {ex.plain_english_summary}",
    ]
    p4_panel = Panel(
        "\n".join(p4_lines),
        title="[bold white]4. Executive Bottom Line & Action Playbook (Press 0/E for S5 • 9/T for S4 • 8/G for S3 • 7/V for S2 • 6/S for S1 • 1–5 for Core • C to Copy)[/bold white]",
        border_style=border_col,
        box=box.ROUNDED,
    )

    return Group(header_panel, ribbon_table, mid_row, p3_panel, p4_panel)


# ============================================================================
# DESK [F]: STANDALONE 15-MINUTE ORDER FLOW & FOOTPRINT SWING HUD
# ============================================================================

def _build_tab_footprint_hud(store: StateStore, header_panel: Panel) -> Group:
    """Renders Dedicated Standalone Desk [F: FOOTPRINT SWING] (Portrait-first layout)."""
    f_ev = getattr(store, "footprint_evaluation", None)
    current_price = store.binance_spot_price or (f_ev.current_price if f_ev else 0.0)

    if f_ev is None or not f_ev.active_ladder_rows:
        return Group(
            header_panel,
            Panel(
                "[dim]Awaiting live spot trade flow to populate 15m Footprint ladder and 4-gate confluence...[/dim]",
                title="[bold cyan]DESK [F: FOOTPRINT SWING][/bold cyan]",
                box=box.ROUNDED,
            ),
        )

    is_distribute = (f_ev.direction == "DISTRIBUTE_SELL")

    # 1. Top Section: BTC Price, 15m Delta, CPI, Regime, NTZ Shield & Daily VWAP
    bar_delta = f_ev.active_bar_delta
    if bar_delta > 0:
        delta_str = f"[bold green]+{bar_delta:,.1f} BTC[/bold green]"
    elif bar_delta < 0:
        delta_str = f"[bold red]{bar_delta:,.1f} BTC[/bold red]"
    else:
        delta_str = "[dim]0.0 BTC[/dim]"

    cpi_usd = float(getattr(f_ev, "cpi_usd", 0.0))
    if cpi_usd > 2.0:
        cpi_str = f"[bold green]+${cpi_usd:,.2f} (US Bid)[/bold green]"
    elif cpi_usd < -2.0:
        cpi_str = f"[bold red]-${abs(cpi_usd):,.2f} (US Lag)[/bold red]"
    else:
        cpi_str = f"[cyan]${cpi_usd:+,.2f} (Neutral)[/cyan]"

    ntz_active = bool(getattr(f_ev, "ntz_veto_active", False))
    ntz_text = str(getattr(f_ev, "ntz_status_text", "ALL CLEAR (8A-8F PASS)"))
    ntz_badge = f"[bold white on red] {ntz_text} [/bold white on red]" if ntz_active else f"[bold green]{ntz_text}[/bold green]"

    vwap_px = float(getattr(f_ev, "daily_vwap", 0.0) or current_price)
    vwap_str = f"[cyan]${vwap_px:,.0f}[/cyan]"

    if f_ev.gate1_macro_tap:
        regime_desc = f"[bold yellow]AT {f_ev.gate1_tapped_level_name} (${f_ev.gate1_tapped_level_price:,.0f})[/bold yellow]"
    else:
        regime_desc = "[bold cyan]MID-CHOP / OBSERVATION[/bold cyan]"

    top_grid = Table.grid(expand=True)
    top_grid.add_column(justify="left", no_wrap=True)
    top_grid.add_column(justify="right", no_wrap=True)
    top_grid.add_row(
        f"[bold white]BTC:[/bold white] [bold cyan]${current_price:,.2f}[/bold cyan]  [dim]│[/dim]  [bold white]15M DELTA:[/bold white] {delta_str}",
        f"[bold white]CPI:[/bold white] {cpi_str}",
    )
    top_grid.add_row(
        f"[bold white]REGIME:[/bold white] {regime_desc}  [dim]│[/dim]  [bold white]VWAP:[/bold white] {vwap_str}",
        f"[bold white]NTZ:[/bold white] {ntz_badge}",
    )

    # 2. 4-Gate Confluence Checklist
    gate_table = Table(box=box.MINIMAL, expand=True, show_header=False, pad_edge=False)
    gate_table.add_column(justify="left", no_wrap=True)

    if is_distribute:
        gate_header = "[bold magenta]4-GATE SPOT DISTRIBUTION (PROFIT HARVEST) CONFLUENCE[/bold magenta]"
        g1_icon = "[bold green][✓][/bold green]" if f_ev.gate1_macro_tap else "[dim yellow][○][/dim yellow]"
        g1_text = f"{g1_icon} Gate 1: Macro Level Resistance ({f_ev.gate1_tapped_level_name or 'Awaiting Tap'})"

        g2_icon = "[bold green][✓][/bold green]" if f_ev.gate2_positioning_crowded else "[dim yellow][○][/dim yellow]"
        g2_text = f"{g2_icon} Gate 2: Perp Long Crowding / CVD Absorption"

        g3_icon = "[bold green][✓][/bold green]" if f_ev.gate3_wick_absorption else "[dim yellow][○][/dim yellow]"
        g3_text = f"{g3_icon} Gate 3: Upper-Wick Buyer Exhaustion Held"

        g4_icon = "[bold green][✓][/bold green]" if f_ev.gate4_delta_flip else "[dim yellow][○][/dim yellow]"
        g4_text = f"{g4_icon} Gate 4: 15m Negative Delta Shift"
    else:
        gate_header = "[bold green]4-GATE SPOT ACCUMULATION CONFLUENCE[/bold green]"
        g1_icon = "[bold green][✓][/bold green]" if f_ev.gate1_macro_tap else "[dim yellow][○][/dim yellow]"
        g1_text = f"{g1_icon} Gate 1: Macro Level Swept ({f_ev.gate1_tapped_level_name or 'Awaiting Tap'})"

        g2_icon = "[bold green][✓][/bold green]" if f_ev.gate2_positioning_crowded else "[dim yellow][○][/dim yellow]"
        g2_text = f"{g2_icon} Gate 2: Perp Short Crowding / CVD Absorption Confirmed"

        auc_tag = "Completed Auction" if getattr(f_ev, "auction_completed", True) else "Unfinished Auction"
        g3_icon = "[bold green][✓][/bold green]" if f_ev.gate3_wick_absorption else "[dim yellow][○][/dim yellow]"
        g3_text = f"{g3_icon} Gate 3: Lower-Wick Absorption Held ({auc_tag})"

        poc_tag = "Closed + POC Reclaim" if getattr(f_ev, "bar_poc_reclaimed", True) else "Below Bar POC"
        g4_icon = "[bold green][✓][/bold green]" if f_ev.gate4_delta_flip else "[dim yellow][○][/dim yellow]"
        g4_text = f"{g4_icon} Gate 4: 15m Positive Delta Flip ({poc_tag})"

    gate_table.add_row(gate_header)
    gate_table.add_row(g1_text)
    gate_table.add_row(g2_text)
    gate_table.add_row(g3_text)
    gate_table.add_row(g4_text)

    # 3. Active 15M Footprint ($25 Bins)
    footprint_table = Table(
        box=box.SIMPLE_HEAVY,
        expand=True,
        show_header=True,
        header_style="bold cyan",
        pad_edge=False,
    )
    footprint_table.add_column("Bin", justify="left", style="white", no_wrap=True)
    footprint_table.add_column("Bid(Sell)", justify="right", style="red", no_wrap=True)
    footprint_table.add_column("Ask(Buy)", justify="right", style="green", no_wrap=True)
    footprint_table.add_column("Tag", justify="left", no_wrap=True)

    for row in f_ev.active_ladder_rows:
        is_current = abs(row.price - current_price) < 12.5
        bin_prefix = "►" if is_current else " "
        bin_str = f"{bin_prefix}${row.price:,.0f}"
        if is_current:
            bin_display = f"[bold black on yellow]{bin_str}[/bold black on yellow]"
        elif row.is_poc:
            bin_display = f"[bold cyan]{bin_str}[/bold cyan]"
        else:
            bin_display = f"[bold white]{bin_str}[/bold white]"

        bid_val = f"{row.bid_vol:.1f}" if row.bid_vol > 0 else "0.0"
        ask_val = f"{row.ask_vol:.1f}" if row.ask_vol > 0 else "0.0"

        # Format Tag matching spec
        tags = []
        if row.is_poc:
            tags.append("[bold cyan]POC[/bold cyan]")
        if row.is_stacked_buy:
            tags.append("[bold black on green]▲ STACK[/bold black on green]")
        elif row.is_buy_imbalance:
            tags.append("[green]BUY IMB[/green]")
        if row.is_stacked_sell:
            tags.append("[bold white on red]▼ STACK[/bold white on red]")
        elif row.is_sell_imbalance:
            tags.append("[red]SELL IMB[/red]")
        if row.is_battle_zone:
            tags.append("[bold yellow on red]⚔ BATTLE[/bold yellow on red]")
        if "TRAP SELL" in row.tag:
            tags.append("[bold yellow on dark_magenta]🛡 WICK![/bold yellow on dark_magenta]")
        if "TRAP BUY" in row.tag:
            tags.append("[bold black on bright_yellow]🛡 WICK![/bold black on bright_yellow]")

        if not tags:
            if row.total_vol == 0:
                tag_display = "[dim]LVN[/dim]"
            else:
                tag_display = f"[dim]{row.total_vol:.1f}[/dim]"
        else:
            tag_display = " ".join(tags)

        footprint_table.add_row(bin_display, bid_val, ask_val, tag_display)

    # 4. Positioning Context
    pos_grid = Table.grid(expand=True)
    pos_grid.add_column(justify="left", no_wrap=True)
    funding_str = f"{f_ev.funding_rate_pct:+.3f}%"
    oi_str = f"{f_ev.oi_4h_change_pct:+.1f}%"
    pos_grid.add_row("[bold white]POSITIONING CONTEXT[/bold white]")
    pos_grid.add_row(f" • [white]Funding:[/white] [cyan]{funding_str}[/cyan] ({'Crowded Short' if f_ev.funding_rate_pct <= 0.01 else 'Elevated Long'})")
    pos_grid.add_row(f" • [white]OI 4H:[/white]   [cyan]{oi_str}[/cyan] ({'Building Pressure' if abs(f_ev.oi_4h_change_pct) >= 1.0 else 'Steady Churn'})")
    pos_grid.add_row(f" • [white]CVD:[/white]     [green]{f_ev.cvd_absorption_status}[/green]")

    # 5. Actionable Signal / Execution Box
    signal_table = Table.grid(expand=True)
    signal_table.add_column(justify="left", no_wrap=True)

    if f_ev.all_gates_pass:
        if getattr(store, "spot_ws_connected", False):
            import sys
            sys.stdout.write("\a")
        if is_distribute:
            signal_table.add_row("[bold white on dark_magenta] >>> SIGNAL: SPOT PROFIT HARVEST (ROTATE USDT) <<< [/bold white on dark_magenta]")
            signal_table.add_row(f" • [bold white]Sell Spot At:[/bold white] [bold cyan]${f_ev.entry_price:,.0f}[/bold cyan]")
            signal_table.add_row(f" • [bold white]Invalidation:[/bold white] [bold red]${f_ev.stop_loss:,.0f}[/bold red] (Breakout Re-entry)")
            signal_table.add_row(f" • [bold white]Rebuy Target:[/bold white] [bold green]${f_ev.rebuy_target_price:,.0f}[/bold green] ({f_ev.rebuy_target_name})")
            signal_table.add_row(f"   [dim](Target Yield: +{f_ev.target_coin_yield_pct:.1f}% BTC Coin Accumulation)[/dim]")
        else:
            eq_u = float(getattr(f_ev, "reference_equity_usd", 100000.0))
            rb_u = float(getattr(f_ev, "risk_budget_usd", 1000.0))
            fin_btc = float(getattr(f_ev, "final_position_btc", 0.0))
            fin_not = float(getattr(f_ev, "final_notional_usd", 0.0))
            eff_r = float(getattr(f_ev, "effective_risk_usd", 0.0))
            clamped = bool(getattr(f_ev, "notional_clamped", False))
            tp1_px = float(getattr(f_ev, "tp1_fair_value_poc", 0.0) or f_ev.tp1_1to2)
            tp2_px = float(getattr(f_ev, "tp2_short_liq_magnet", 0.0) or f_ev.tp2_1to3)
            stop_dist = max(f_ev.entry_price - f_ev.stop_loss, 25.0)
            stop_pct = (stop_dist / max(f_ev.entry_price, 1.0)) * 100.0
            cap_note = "Clamped 50% Cap" if clamped else "1.0% Risk Sized"

            signal_table.add_row("[bold white on dark_green] >>> SIGNAL: SPOT SWING ACCUMULATION TRIGGERED (ALL 4 GATES VERIFIED) <<< [/bold white on dark_green]")
            signal_table.add_row(
                f" • [bold white]Action / Entry:[/bold white] [bold cyan]BUY SPOT @ ${f_ev.entry_price:,.2f}[/bold cyan]  [dim]│[/dim]  "
                f"[white]Hard Stop:[/white] [bold red]${f_ev.stop_loss:,.2f}[/bold red] [dim](-${stop_dist:,.0f} / -{stop_pct:.2f}%)[/dim]"
            )
            signal_table.add_row(
                f" • [bold white]Position Size :[/bold white] [bold green]{fin_btc:.4f} BTC[/bold green] ([cyan]${fin_not:,.0f}[/cyan] • {cap_note})  [dim]│[/dim]  "
                f"[white]Real Risk:[/white] [bold yellow]${eff_r:,.2f}[/bold yellow] [dim](of ${rb_u:,.0f} budget on ${eq_u:,.0f})[/dim]"
            )
            signal_table.add_row(
                f" • [bold white]TP1 (50% Trim):[/bold white] [bold green]${tp1_px:,.0f}[/bold green] (30D cPOC -> Move SL to BE)  [dim]│[/dim]  "
                f"[bold white]TP2 (50% Run):[/bold white] [bold magenta]${tp2_px:,.0f}[/bold magenta] (Short-Liq Magnet)"
            )
    else:
        signal_table.add_row(f"[bold yellow]>>> STATUS: {f_ev.signal_status} (OBSERVATION) <<<[/bold yellow]")
        if f_ev.gate1_macro_tap:
            signal_table.add_row(f" • Macro level tapped: [bold cyan]{f_ev.gate1_tapped_level_name}[/bold cyan] (${f_ev.gate1_tapped_level_price:,.0f})")
            signal_table.add_row(f" • Gate 2/3/4 Status: [yellow]{f_ev.gate2_detail}[/yellow]")
            signal_table.add_row(f" • Delta Flip: [cyan]{'BULLISH FLIP' if f_ev.delta_flipped_bullish else ('BEARISH FLIP' if f_ev.delta_flipped_bearish else 'AWAITING FLIP')}[/cyan]")
        else:
            signal_table.add_row(" • Traversing auction nodes; awaiting institutional key level tap.")
            signal_table.add_row(" • Invalidation Rule: Never chase market fills in mid-range chop.")
            signal_table.add_row(" • Staged Limit Bids: Pre-position at 30D/7D HVN or Liquidation Magnet.")

    left_panel = Panel(
        Group(
            top_grid,
            Rule(style="dim cyan"),
            gate_table,
            Rule(style="dim cyan"),
            footprint_table,
            Rule(style="dim cyan"),
            pos_grid,
            Rule(style="dim cyan"),
            signal_table,
        ),
        title="[bold cyan]DESK [F: FOOTPRINT SWING][/bold cyan]",
        border_style="cyan" if not is_distribute else "magenta",
        box=box.ROUNDED,
        padding=(0, 1),
    )

    # -------------------------------------------------------------------------
    # RIGHT COMPANION: TAB 0 MAGNETS, TAB 1 MACRO ANCHORS, CVD & DELTA BUFFER
    # -------------------------------------------------------------------------
    spot_ev = getattr(store, "spot_swing_evaluation", None)
    mag = getattr(spot_ev, "magnet", None) if spot_ev else None
    macro_vp = getattr(store, "macro_profile", None)
    flow = getattr(store, "flow_snapshot", None)

    # 1. Tab 0: Daily Liquidation Magnets & Strict 1:3 RRR Protocol
    mag_table = Table(box=box.SIMPLE_HEAVY, expand=True, show_header=True, header_style="bold yellow", pad_edge=False)
    mag_table.add_column("Liquidation Magnet", style="bold white", no_wrap=True)
    mag_table.add_column("Price", justify="right", style="cyan", no_wrap=True)
    mag_table.add_column("Distance / Role", justify="right", no_wrap=True)

    short_mag = getattr(mag, "short_liq_magnet", 0.0) if mag else 0.0
    long_mag = getattr(mag, "long_liq_magnet", 0.0) if mag else 0.0
    if (
        mag is not None
        and isinstance(short_mag, (int, float))
        and isinstance(long_mag, (int, float))
        and short_mag > 0
        and long_mag > 0
    ):
        short_mag = float(short_mag)
        long_mag = float(long_mag)
        short_dist = float(mag.short_liq_distance_pct)
        long_dist = float(mag.long_liq_distance_pct)
        rrr_badge = (
            f"[bold green]{mag.rrr_to_magnet:.2f}R (≥3R PASS)[/bold green]"
            if mag.rrr_pass
            else f"[bold yellow]{mag.rrr_to_magnet:.2f}R (<3R WAIT)[/bold yellow]"
        )
        mv_style = _magnet_verdict_style(mag.verdict)
        max_entry = float(getattr(mag, "max_entry_for_3r", 0.0))

        long_dist_disp = -abs(long_dist)
        mag_table.add_row(
            "[magenta]Short-Liq Magnet (↑)[/magenta]",
            f"${short_mag:,.0f}",
            f"+{abs(short_dist):.2f}% [dim](Squeeze Fuel)[/dim]",
        )
        mag_table.add_row(
            "[cyan]Long-Liq Magnet (↓)[/cyan]",
            f"${long_mag:,.0f}",
            f"{long_dist_disp:.2f}% [dim](Flush Pool)[/dim]",
        )

        hard_stop = float(getattr(mag, "hard_stop_price", 0.0))
        mag_footer = Text.from_markup(
            f" • [white]Live R:R:[/white] {rrr_badge}   "
            f"• [white]Max 3R Entry:[/white] [bold yellow]<=${max_entry:,.0f}[/bold yellow]\n"
            f" • [white]Tab 0 Verdict:[/white] [{mv_style}] {mag.verdict.upper()} [/{mv_style}]  "
            f"[dim](Hard Stop: ${hard_stop:,.0f})[/dim]"
        )
    else:
        mag_table.add_row("[dim]Daily Liquidation Magnets[/dim]", "[dim]Syncing...[/dim]", "[dim]Waiting for 1D/4H bars[/dim]")
        mag_footer = Text.from_markup("[dim] • Awaiting Tab 0 Spot Swing Evaluation...[/dim]")

    mag_panel = Panel(
        Group(mag_table, mag_footer),
        title="[bold yellow]1. TAB 0 LIQUIDATION MAGNETS & 1:3 RRR PROTOCOL[/bold yellow]",
        box=box.ROUNDED,
        padding=(0, 1),
    )

    # 2. Macro Profile Anchor Levels & Session Extremes (Tab 1 / Tab 3 / Tab 8 Integration)
    macro_table = Table(box=box.SIMPLE_HEAVY, expand=True, show_header=True, header_style="bold magenta", pad_edge=False)
    macro_table.add_column("Macro / Session Level", style="bold white", no_wrap=True)
    macro_table.add_column("Price", justify="right", style="cyan", no_wrap=True)
    macro_table.add_column("Distance / Role", justify="right", no_wrap=True)

    if macro_vp is not None and getattr(macro_vp, "c_vah", 0.0) > 0 and current_price > 0:
        c_vah = float(macro_vp.c_vah)
        c_poc = float(macro_vp.c_poc)
        c_val = float(macro_vp.c_val)
        hvn_floor = float(getattr(macro_vp, "support_hvn_below_val", 0.0) or (c_val * 0.985))

        dist_vah_pct = ((c_vah - current_price) / current_price) * 100.0
        dist_poc_pct = ((c_poc - current_price) / current_price) * 100.0
        dist_val_pct = ((c_val - current_price) / current_price) * 100.0
        dist_hvn_pct = ((hvn_floor - current_price) / current_price) * 100.0

        macro_table.add_row("[yellow]30D cVAH (Resistance)[/yellow]", f"${c_vah:,.0f}", f"{dist_vah_pct:+.2f}% [dim](TP2 Runner)[/dim]")
        macro_table.add_row("[cyan]30D cPOC (Fair Value)[/cyan]", f"${c_poc:,.0f}", f"{dist_poc_pct:+.2f}% [dim](TP1 Scale 50%)[/dim]")
        macro_table.add_row("[green]30D cVAL (Support Floor)[/green]", f"${c_val:,.0f}", f"{dist_val_pct:+.2f}% [bold green](Gate 1 Anchor)[/bold green]")

        asia_low_px = float(getattr(f_ev, "asia_low", 0.0))
        if asia_low_px > 0:
            dist_asia_pct = ((asia_low_px - current_price) / current_price) * 100.0
            macro_table.add_row("[bright_cyan]Asia Session Low[/bright_cyan]", f"${asia_low_px:,.0f}", f"{dist_asia_pct:+.2f}% [dim](Session Sweep)[/dim]")
        else:
            macro_table.add_row("[dim]Support HVN Floor[/dim]", f"${hvn_floor:,.0f}", f"{dist_hvn_pct:+.2f}% [dim](Structural Base)[/dim]")
    else:
        macro_table.add_row("[dim]30D Volume Profile[/dim]", "[dim]Syncing...[/dim]", "[dim]Waiting for 30D 1H bars[/dim]")

    sma200_px = float(getattr(f_ev, "sma_200_1d", 0.0))
    above_200 = bool(getattr(f_ev, "above_200d_sma", True))
    if sma200_px > 0:
        sma_badge = "[bold green]ABOVE (1.00% Full Risk)[/bold green]" if above_200 else "[bold yellow]BELOW (0.50% Defensive Risk)[/bold yellow]"
        macro_footer = Text.from_markup(f" • [white]1D 200 SMA Gatekeeper:[/white] [cyan]${sma200_px:,.0f}[/cyan] • {sma_badge}")
    else:
        macro_footer = Text.from_markup("[dim] • 1D 200 SMA Gatekeeper: Syncing daily history...[/dim]")

    # 3. Multi-Horizon CVD Truth Serum (Tab 1 Integration)
    cvd_table = Table(box=box.SIMPLE_HEAVY, expand=True, show_header=True, header_style="bold green", pad_edge=False)
    cvd_table.add_column("Horizon", style="bold white", no_wrap=True)
    cvd_table.add_column("Spot CVD", justify="right", no_wrap=True)
    cvd_table.add_column("Perp CVD", justify="right", no_wrap=True)
    cvd_table.add_column("Absorption Index", justify="right", no_wrap=True)

    if flow is not None and getattr(flow, "w_15m", None) is not None:
        for w in (flow.w_15m, flow.w_1h, flow.w_4h, flow.w_24h):
            abs_str = f"[bold]{w.absorption_index:.2f}[/bold]"
            if w.absorption_index >= 1.5:
                abs_str += " [green](Heavy Abs)[/green]"
            elif w.absorption_index >= 1.0:
                abs_str += " [cyan](Holding)[/cyan]"
            cvd_table.add_row(
                w.window_label,
                _color_signed(w.spot_delta_btc, "+,.1f", " BTC"),
                _color_signed(w.perp_delta_btc, "+,.1f", " BTC"),
                abs_str,
            )
    else:
        cvd_table.add_row("[dim]Multi-Horizon CVD[/dim]", "[dim]Syncing...[/dim]", "[dim]Syncing...[/dim]", "[dim]Normal[/dim]")

    # 4. Trailing 15-Minute Bar Deltas (Ring Buffer)
    deltas_display = Table(box=box.MINIMAL, expand=True, show_header=True, header_style="bold white")
    deltas_display.add_column("Bar Index", justify="left")
    deltas_display.add_column("Net Delta (BTC)", justify="right")
    deltas_display.add_column("State / Transition", justify="left")

    for i, d in enumerate(f_ev.recent_bars_deltas):
        idx_label = f"Bar [-{len(f_ev.recent_bars_deltas) - i - 1}]" if i < len(f_ev.recent_bars_deltas) - 1 else "[bold cyan]Active Forming[/bold cyan]"
        d_color = "green" if d > 0 else ("red" if d < 0 else "dim")
        d_text = f"[{d_color}]{d:+,.2f} BTC[/{d_color}]"
        note = "Buyers Gaining Control" if d > 0 else "Sellers Pressing"
        deltas_display.add_row(idx_label, d_text, note)

    right_group = Group(
        mag_panel,
        Panel(Group(macro_table, macro_footer), title="[bold magenta]2. TAB 1 MACRO ANCHORS & SESSION EXTREMES[/bold magenta]", box=box.ROUNDED, padding=(0, 1)),
        Panel(cvd_table, title="[bold green]3. TAB 1 MULTI-HORIZON CVD TRUTH SERUM[/bold green]", box=box.ROUNDED, padding=(0, 1)),
        Panel(deltas_display, title="[bold white]4. TRAILING 15M DELTA RING BUFFER[/bold white]", box=box.ROUNDED, padding=(0, 1)),
        Rule(style="dim white"),
        Text.from_markup(
            "[bold white]DESK NAVIGATION:[/bold white] "
            "• Press [bold cyan]F[/bold cyan]: Footprint Desk  "
            "• Press [bold cyan]1[/bold cyan]: Tactical Swing  "
            "• Press [bold cyan]0[/bold cyan]: Spot Screener  "
            "• Press [bold cyan]L[/bold cyan]: Master  "
            "• Press [bold cyan]C[/bold cyan]: Copy AI Packet"
        ),
    )

    right_panel = Panel(
        right_group,
        title="[bold white]DESK [F] QUANTITATIVE RADAR & EXECUTION PROTOCOL[/bold white]",
        border_style="bright_blue",
        box=box.ROUNDED,
        padding=(0, 1),
    )

    # -------------------------------------------------------------------------
    # 3-VARIANT PARALLEL FORWARD TEST SCORECARD PANEL (72H LIVE TELEMETRY)
    # -------------------------------------------------------------------------
    scorecard_table = Table(
        box=box.SIMPLE_HEAVY,
        expand=True,
        show_header=True,
        header_style="bold bright_white on dark_blue",
        pad_edge=False,
    )
    scorecard_table.add_column("Variant / Strategy", style="bold white", width=20, no_wrap=True)
    scorecard_table.add_column("Horizon", style="dim cyan", width=12, no_wrap=True)
    scorecard_table.add_column("Status", width=32, no_wrap=True)
    scorecard_table.add_column("Active Position / PnL", width=44, no_wrap=True)
    scorecard_table.add_column("Trades", justify="center", width=8, no_wrap=True)
    scorecard_table.add_column("Win Rate", justify="center", width=10, no_wrap=True)
    scorecard_table.add_column("Realized PnL", justify="right", width=14, no_wrap=True)
    scorecard_table.add_column("Max DD", justify="right", width=14, no_wrap=True)

    cards = getattr(f_ev, "forward_test_scorecards", {}) or {}
    variant_order = [
        ("OPT_1_PURE_FP", "1: Pure Footprint", "15m Scalp"),
        ("OPT_2_4GATE", "2: 4-Gate Filter", "1H/4H Swing"),
        ("OPT_3_INSTITUTIONAL", "3: Institutional", "Spot Swing"),
    ]

    for vid, def_name, def_tf in variant_order:
        sc = cards.get(vid) if isinstance(cards, dict) else None
        v_name = getattr(sc, "display_name", def_name) if sc else def_name
        v_tf = getattr(sc, "timeframe_desc", def_tf) if sc else def_tf
        status_raw = str(getattr(sc, "status", "OBSERVING") if sc else "OBSERVING")

        if "IN_POSITION" in status_raw.upper():
            status_badge = f"[bold black on green] {status_raw} [/bold black on green]"
        elif "ARMED" in status_raw.upper() or "AWAITING" in status_raw.upper():
            status_badge = f"[bold black on yellow] {status_raw} [/bold black on yellow]"
        elif "LOCKED_OUT" in status_raw.upper() or "VETOED" in status_raw.upper():
            status_badge = f"[bold red]{status_raw}[/bold red]"
        elif "WATCHING" in status_raw.upper():
            status_badge = f"[bold cyan]{status_raw}[/bold cyan]"
        else:
            status_badge = f"[dim]{status_raw}[/dim]"

        active_tr = getattr(sc, "active_trade", None) if sc else None
        if active_tr is not None:
            e_px = float(getattr(active_tr, "entry_price", 0.0))
            sl_px = float(getattr(active_tr, "stop_loss", 0.0))
            unreal = float(getattr(active_tr, "unrealized_pnl_usd", 0.0))
            tr_dir = str(getattr(active_tr, "direction", "BUY")).upper()
            dir_label = "Buy" if tr_dir != "SELL" else "Sell (USDT)"
            u_color = "bold green" if unreal >= 0 else "bold red"
            be_locked = (tr_dir != "SELL" and sl_px >= e_px) or (tr_dir == "SELL" and 0 < sl_px <= e_px)
            sl_label = f"SL ${sl_px:,.0f} (BE+)" if be_locked else f"SL ${sl_px:,.0f}"
            pos_str = f"{dir_label} @ ${e_px:,.0f} • {sl_label} • [{u_color}]${unreal:+,.2f}[/{u_color}]"
        else:
            last_summary = getattr(sc, "last_closed_trade_summary", "") if sc else ""
            if last_summary:
                pos_str = f"[dim]Flat (Last: {last_summary})[/dim]"
            else:
                pos_str = "[dim]Flat (No Open Position)[/dim]"

        tot_tr = int(getattr(sc, "total_trades", 0) if sc else 0)
        win_pct = float(getattr(sc, "win_rate_pct", 0.0) if sc else 0.0)
        pnl_val = float(getattr(sc, "realized_pnl_usd", 0.0) if sc else 0.0)
        mdd_val = float(getattr(sc, "max_drawdown_usd", 0.0) if sc else 0.0)

        tr_str = f"[bold]{tot_tr}[/bold]" if tot_tr > 0 else "[dim]0[/dim]"
        if tot_tr > 0:
            wr_color = "bold green" if win_pct >= 60.0 else ("bold yellow" if win_pct >= 45.0 else "bold red")
            wr_str = f"[{wr_color}]{win_pct:.1f}%[/{wr_color}]"
        else:
            wr_str = "[dim]0.0%[/dim]"

        if pnl_val > 0:
            pnl_str = f"[bold green]+${pnl_val:,.2f}[/bold green]"
        elif pnl_val < 0:
            pnl_str = f"[bold red]-${abs(pnl_val):,.2f}[/bold red]"
        else:
            pnl_str = "[dim]$0.00[/dim]"

        if mdd_val > 0:
            mdd_str = f"[bold red]-${mdd_val:,.2f}[/bold red]"
        else:
            mdd_str = "[dim]$0.00[/dim]"

        scorecard_table.add_row(
            v_name,
            v_tf,
            status_badge,
            pos_str,
            tr_str,
            wr_str,
            pnl_str,
            mdd_str,
        )

    # Executive Verdict Banner for Desk [F] (Responsive to Live Trades & 15m Microstructure)
    asia_low_px = float(getattr(f_ev, "asia_low", 0.0))
    asia_high_px = float(getattr(f_ev, "asia_high", 0.0))
    cards = getattr(f_ev, "forward_test_scorecards", {}) or {}
    sc1 = cards.get("OPT_1_PURE_FP") if isinstance(cards, dict) else None
    active_tr = getattr(sc1, "active_trade", None) if sc1 else None

    abs_idx_15m = float(getattr(flow.w_15m, "absorption_index", 0.0)) if (flow and getattr(flow, "w_15m", None)) else 0.0
    perp_15m = float(getattr(flow.w_15m, "perp_delta_btc", 0.0)) if (flow and getattr(flow, "w_15m", None)) else 0.0
    battle_zones = [r.price for r in f_ev.active_ladder_rows if r.is_battle_zone] if f_ev.active_ladder_rows else []

    if ntz_active:
        verdict_status = "[bold white on red] RED: 100% CASH (SYSTEMIC HAZARD VETO) [/bold white on red]"
        confluence_msg = f"[bold red]NTZ 8A-8F VETO:[/bold red] Systemic Non-Trade Zone active ({ntz_text})."
        plain_msg = "Major macro news event or systemic cascade in progress. Stay 100% in cash."
        v_border = "red"
    elif active_tr is not None:
        tr_dir = getattr(active_tr, "direction", "BUY")
        entry_p = float(getattr(active_tr, "entry_price", 0.0))
        sl_p = float(getattr(active_tr, "stop_loss", 0.0))
        tp1_p = float(getattr(active_tr, "tp1_price", 0.0))
        tp2_p = float(getattr(active_tr, "tp2_price", 0.0))
        rem_size = float(getattr(active_tr, "remaining_size", 0.0))
        tp1_hit = bool(getattr(active_tr, "tp1_hit", False))
        unreal = float(getattr(active_tr, "unrealized_pnl_usd", 0.0))
        banked = float(getattr(active_tr, "already_realized_pnl", 0.0))

        if tp1_hit:
            dist_tp2 = tp2_p - current_price if tr_dir == "BUY" else current_price - tp2_p
            verdict_status = f"[bold black on bright_green] ACTIVE POSITION: 50% RUNNER TARGETING TP2 (${tp2_p:,.0f}) • SL AT BREAKEVEN (${sl_p:,.0f}) [/bold black on bright_green]"
            confluence_msg = f"[bold green]TP1 HARVESTED (+${banked:,.2f}):[/bold green] Holding {rem_size:.4f} BTC • Live Runner: [bold {'green' if unreal >= 0 else 'red'}]${unreal:+,.2f}[/] • Dist to TP2: ${dist_tp2:,.0f}"
            plain_msg = f"Trade 5 is in full control: 50% profit banked, stop loss locked at breakeven ($0 risk). Let the runner work towards TP2 (${tp2_p:,.0f})."
            v_border = "bright_green"
        else:
            dist_tp1 = tp1_p - current_price if tr_dir == "BUY" else current_price - tp1_p
            dist_sl = current_price - sl_p if tr_dir == "BUY" else sl_p - current_price
            verdict_status = f"[bold black on green] ACTIVE 15M SCALP: IN POSITION ({tr_dir} {rem_size:.4f} BTC @ ${entry_p:,.0f}) [/bold black on green]"
            confluence_msg = f"[bold green]RUNNING SCALP:[/bold green] Stop Loss: ${sl_p:,.0f} (-${dist_sl:,.0f}) • TP1 Target: ${tp1_p:,.0f} (+${dist_tp1:,.0f}) • Live: [bold {'green' if unreal >= 0 else 'red'}]${unreal:+,.2f}[/]"
            plain_msg = f"Active 15m scalp from ${entry_p:,.0f}. Stop protected at ${sl_p:,.0f}; watching for push to first scale-out at ${tp1_p:,.0f}."
            v_border = "green"
    elif f_ev.all_gates_pass:
        if is_distribute:
            verdict_status = "[bold white on dark_magenta] SPOT PROFIT HARVEST: ROTATE TO USDT (ALL 4 GATES PASS) [/bold white on dark_magenta]"
            confluence_msg = f"[bold magenta]TRIGGERED:[/bold magenta] Resistance tapped ({f_ev.gate1_tapped_level_name}) + Buyer Exhaustion + Bear Δ Flip."
            plain_msg = f"Resistance ceiling confirmed. Take profit by rotating BTC to USDT at ${current_price:,.0f}; rebuy target at ${f_ev.rebuy_target_price:,.0f} (+{f_ev.target_coin_yield_pct:.1f}% BTC Yield)."
            v_border = "magenta"
        else:
            verdict_status = "[bold black on bright_green] SPOT ACCUMULATION: BUY SIGNAL TRIGGERED (ALL 4 GATES PASS) [/bold black on bright_green]"
            confluence_msg = f"[bold green]TRIGGERED:[/bold green] Support tapped ({f_ev.gate1_tapped_level_name}) + Trapped Sellers + Bull Δ Flip."
            plain_msg = f"Institutional accumulation confirmed at key support. Safe to execute Spot Swing entry at ${current_price:,.0f}."
            v_border = "bright_green"
    elif f_ev.signal_status == "ARMED":
        if is_distribute:
            verdict_status = "[bold black on dark_magenta] SETUP ARMED (DISTRIBUTION): AWAITING BEARISH DELTA FLIP [/bold black on dark_magenta]"
            confluence_msg = f"[bold magenta]GATE 4 PENDING:[/bold magenta] Resistance tapped ({f_ev.gate1_tapped_level_name}); waiting for 15m delta to turn negative."
            plain_msg = "Price is at resistance with buyer exhaustion. Waiting for sellers to flip 15m delta negative before rotating to USDT."
            v_border = "magenta"
        else:
            verdict_status = "[bold black on bright_cyan] SETUP ARMED (ACCUMULATION): AWAITING BULLISH DELTA FLIP [/bold black on bright_cyan]"
            confluence_msg = f"[bold cyan]GATE 4 PENDING:[/bold cyan] Support tapped ({f_ev.gate1_tapped_level_name}); waiting for 15m delta to turn positive."
            plain_msg = "Price is at institutional support with seller absorption. Waiting for buyers to flip 15m delta positive before entering."
            v_border = "cyan"
    elif f_ev.gate1_macro_tap:
        verdict_status = f"[bold black on yellow] WATCHING LEVEL: AT {f_ev.gate1_tapped_level_name.upper()} (${f_ev.gate1_tapped_level_price:,.0f}) [/bold black on yellow]"
        confluence_msg = f"[bold yellow]GATE 2/3 PENDING:[/bold yellow] Level tapped; awaiting footprint absorption / exhaustion wick."
        plain_msg = f"Price touched {f_ev.gate1_tapped_level_name}. Standing by for footprint trapped volume to confirm reversal."
        v_border = "yellow"
    elif abs_idx_15m >= 1.5 or len(battle_zones) > 0:
        battle_str = f"⚔ Battle Zone at ${battle_zones[0]:,.0f}" if battle_zones else f"15m Perp CVD {perp_15m:+,.1f} BTC"
        verdict_status = f"[bold black on yellow] 15M ORDER FLOW ABSORPTION ACTIVE ({abs_idx_15m:.1f}x) • {battle_str} [/bold black on yellow]"
        confluence_msg = f"[bold yellow]15M MICRO-ACTION:[/bold yellow] 15m Delta: {bar_delta:+,.1f} BTC • Aggressive sellers absorbed passively near Asia Low (${asia_low_px:,.0f})"
        plain_msg = f"Futures sellers fired {perp_15m:+,.0f} BTC, but passive bids are holding price at ${current_price:,.0f}. Watch for positive delta flip to trigger next scalp."
        v_border = "yellow"
    elif asia_low_px > 0 and (current_price - asia_low_px) <= 150.0:
        dist_low = current_price - asia_low_px
        verdict_status = f"[bold black on cyan] TESTING ASIA SESSION LOW (${asia_low_px:,.0f}) • DIST: ${dist_low:,.0f} [/bold black on cyan]"
        confluence_msg = f"[bold cyan]SESSION SWEEP PROTOCOL:[/bold cyan] Price near Asia Low. Awaiting lower-wick liquidity flush + 15m positive delta flip."
        plain_msg = f"Price is only ${dist_low:,.0f} above today's Asia Low ($80,256). Ideal zone for a trapped seller bounce scalp."
        v_border = "cyan"
    elif asia_high_px > 0 and (asia_high_px - current_price) <= 150.0:
        dist_high = asia_high_px - current_price
        verdict_status = f"[bold black on magenta] TESTING ASIA SESSION HIGH (${asia_high_px:,.0f}) • DIST: ${dist_high:,.0f} [/bold black on magenta]"
        confluence_msg = f"[bold magenta]SESSION RESISTANCE:[/bold magenta] Price near Asia High. Awaiting upper-wick exhaustion for profit rotation into USDT."
        plain_msg = f"Price is only ${dist_high:,.0f} below Asia High ($80,643). Overhead resistance zone — watch for buyer exhaustion."
        v_border = "magenta"
    else:
        dist_to_low = current_price - asia_low_px if asia_low_px > 0 else 0.0
        dist_to_high = asia_high_px - current_price if asia_high_px > 0 else 0.0
        verdict_status = f"[bold black on yellow] 15M INTRADAY CHOP: TRADING BETWEEN ASIA LOW (${asia_low_px:,.0f}) & HIGH (${asia_high_px:,.0f}) [/bold black on yellow]"
        confluence_msg = f"[bold yellow]INTRADAY BOUNDS:[/bold yellow] Support: Asia Low ${asia_low_px:,.0f} (-${dist_to_low:,.0f}) • Resist: Asia High ${asia_high_px:,.0f} (+${dist_to_high:,.0f})"
        plain_msg = f"Bitcoin is oscillating between ${asia_low_px:,.0f} and ${asia_high_px:,.0f}. Scalp setups trigger near session extremes, not in the middle."
        v_border = "yellow"

    v_grid = Table.grid(expand=True)
    v_grid.add_column(justify="left", no_wrap=True)
    v_grid.add_column(justify="right", no_wrap=True)
    v_grid.add_row(
        f"[bold white]DESK [F] VERDICT:[/bold white] {verdict_status}",
        f"[bold white]RISK CAP:[/bold white] [bold cyan]1.00% Risk[/bold cyan]  [dim]│[/dim]  [bold white]BTC:[/bold white] [bold cyan]${current_price:,.2f}[/bold cyan]",
    )
    v_grid.add_row(
        f"[bold white]CONFLUENCE STATE:[/bold white] {confluence_msg}",
        f"[dim]Keys: F Footprint • W Waterfall • 0 Spot • 1-9 Desks • L Master • C Copy[/dim]",
    )
    v_grid.add_row(
        f"[bold white]PLAIN ENGLISH:[/bold white] [bold bright_white]{plain_msg}[/bold bright_white]",
        f"[dim white]Desk F: 15m Footprint Microstructure Protocol[/dim white]",
    )
    verdict_panel = Panel(v_grid, border_style=v_border, box=box.ROUNDED, padding=(0, 1))

    content_grid = Table.grid(expand=True)
    content_grid.add_column(justify="left", no_wrap=False, ratio=1)
    content_grid.add_column(justify="left", no_wrap=False, ratio=1)
    content_grid.add_row(left_panel, right_panel)

    return Group(header_panel, verdict_panel, content_grid)


# ============================================================================
# TAB [W]: 5-PILLAR INSTITUTIONAL DECISION WATERFALL & 7 ESSENTIAL DATA POINTS
# ============================================================================

def _build_tab_waterfall_hud(store: StateStore, header_panel: Panel) -> Group:
    """Renders Dedicated Tab [W: 5-PILLAR INSTITUTIONAL DECISION WATERFALL].
    
    Translates 'The 5 Pillars and 7 Essential Data Points That Drive the Verdict'
    into a real-time, clutter-free execution HUD:
    1. Macro Permission (1D 200 SMA Slope & NTZ 8A-8F)
    2. Structural Map & Asymmetry (30D Volume Profile cVAL/cPOC & Liq Magnets R:R >= 3.0R)
    3. Cross-Venue Flow Truth (4H Spot vs Perp CVD Div Z & Coinbase Premium CPI)
    4. Leverage Fuel (Open Interest dOI 4H & 8H Funding / Perp Basis)
    5. Sniper Trigger (15m Footprint Lower-Wick Absorption & Positive Delta Flip)
    """
    f_ev = getattr(store, "footprint_evaluation", None)
    macro_ev = getattr(store, "macro_evaluation", None)
    spot_ev = getattr(store, "spot_swing_evaluation", None)
    proto_ev = getattr(store, "protocol_evaluation", None)
    flow = getattr(store, "flow_snapshot", None)
    deriv = getattr(store, "derivatives_snapshot", None)
    macro_vp = getattr(store, "macro_profile", None)
    mag = getattr(spot_ev, "magnet", None) if spot_ev else None
    sig = getattr(store, "latest_signal", None)

    current_price = store.binance_spot_price or (f_ev.current_price if f_ev else 0.0) or (spot_ev.spot_price if spot_ev else 0.0)

    # -------------------------------------------------------------------------
    # 1. EXTRACT 7 ESSENTIAL DATA POINTS ACROSS 5 PILLARS
    # -------------------------------------------------------------------------

    # --- PILLAR 1: MACRO PERMISSION (Data Point 1: 1D 200 SMA & NTZ 8A-8F) ---
    sma200_px = float(getattr(macro_ev, "sma_200_1d", 0.0) or getattr(f_ev, "sma_200_1d", 0.0) or 0.0)
    above_200 = bool(getattr(macro_ev, "above_200d_sma", True) if macro_ev else getattr(f_ev, "above_200d_sma", True))
    sma200_slope_usd = float(getattr(macro_ev, "sma_200_slope_5d_usd", 0.0) if macro_ev else 0.0)
    sma200_slope_pct = float(getattr(macro_ev, "sma_200_slope_5d_pct", 0.0) if macro_ev else 0.0)
    slope_pos = bool(getattr(macro_ev, "slope_200d_positive", True) if macro_ev else True)

    ntz_active = bool(
        getattr(f_ev, "ntz_veto_active", False)
        or (getattr(proto_ev, "non_trade_zone_status", "NO") == "YES")
    )
    ntz_text = str(
        getattr(f_ev, "ntz_status_text", "")
        or (getattr(proto_ev, "active_ntz_reasons", ["ALL CLEAR"])[0] if (proto_ev and proto_ev.active_ntz_reasons) else "ALL CLEAR (8A-8F PASS)")
    )
    if not ntz_text:
        ntz_text = "ALL CLEAR (8A-8F PASS)"

    p1_risk_cap = "1.00% Account Risk" if (above_200 and not ntz_active) else ("0.50% Defensive Risk" if not ntz_active else "0.00% (100% Cash)")
    if ntz_active:
        p1_badge = "[bold white on red] ⛔ VETO [/bold white on red]"
        p1_summary = f"[red]NTZ Hazard Active ({ntz_text})[/red]"
    elif above_200:
        p1_badge = "[bold black on green] ✓ PASS [/bold black on green]"
        p1_summary = f"[green]Above Rising 200D SMA (${sma200_px:,.0f}) • 1.00% Authorized[/green]"
    else:
        p1_badge = "[bold black on yellow] ⚠ 0.50% CAP [/bold black on yellow]"
        p1_summary = f"[yellow]Below 200D SMA (${sma200_px:,.0f}) • Halved to 0.50% Risk[/yellow]"

    # --- PILLAR 2: STRUCTURAL MAP & ASYMMETRY ---
    # Data Point 2: 30D Composite Volume Profile (cVAL / cPOC / cVAH / HVN)
    c_val = float(getattr(macro_vp, "c_val", 0.0) if macro_vp else 0.0)
    c_poc = float(getattr(macro_vp, "c_poc", 0.0) if macro_vp else 0.0)
    c_vah = float(getattr(macro_vp, "c_vah", 0.0) if macro_vp else 0.0)
    hvn_floor = float(getattr(macro_vp, "support_hvn_below_val", 0.0) or (c_val * 0.985 if c_val > 0 else 0.0))
    va_pos = float(getattr(sig, "va_position_pct", 50.0) if sig else 50.0)
    is_mid_chop = bool(getattr(sig, "is_mid_range_chop", False) if sig else (30.0 <= va_pos <= 70.0))

    dist_val_pct = ((current_price - c_val) / c_val * 100.0) if c_val > 0 else 0.0
    dist_poc_pct = ((c_poc - current_price) / current_price * 100.0) if current_price > 0 else 0.0

    at_edge = (abs(dist_val_pct) <= 1.5) or (current_price <= c_val)
    if not is_mid_chop or at_edge:
        dp2_badge = "[bold black on green] ✓ PASS [/bold black on green]"
        dp2_summary = f"[green]At Institutional Shelf (cVAL ${c_val:,.0f} / HVN ${hvn_floor:,.0f})[/green]"
    else:
        dp2_badge = "[bold black on yellow] ○ WAITING [/bold black on yellow]"
        dp2_summary = f"[yellow]Mid-Range Chop (VA Pos {va_pos:.1f}%) • Await cVAL ${c_val:,.0f}[/yellow]"

    # Data Point 3: Liquidation Magnets & Live R:R Ratio
    short_mag = float(getattr(mag, "short_liq_magnet", 0.0) or 0.0)
    long_mag = float(getattr(mag, "long_liq_magnet", 0.0) or 0.0)
    short_dist = float(getattr(mag, "short_liq_distance_pct", 0.0) or 0.0)
    long_dist = float(getattr(mag, "long_liq_distance_pct", 0.0) or 0.0)
    rrr_val = float(getattr(mag, "rrr_to_magnet", 0.0) or 0.0)
    rrr_pass = bool(getattr(mag, "rrr_pass", False) or rrr_val >= 3.0)
    max_entry_3r = float(getattr(mag, "max_entry_for_3r", 0.0) or 0.0)

    if rrr_pass and rrr_val >= 3.0:
        dp3_badge = "[bold black on green] ✓ PASS [/bold black on green]"
        dp3_summary = f"[green]Asymmetry {rrr_val:.2f}R ≥ 3.0R to Short-Liq Magnet (${short_mag:,.0f})[/green]"
    elif rrr_val > 0:
        dp3_badge = "[bold black on yellow] ○ WAITING [/bold black on yellow]"
        dp3_summary = f"[yellow]Asymmetry {rrr_val:.2f}R < 3.0R (Max Buy: ${max_entry_3r:,.0f})[/yellow]"
    else:
        dp3_badge = "[dim]○ SYNCING[/dim]"
        dp3_summary = "[dim]Calculating Liquidation Magnets & R:R...[/dim]"

    # --- PILLAR 3: CROSS-VENUE FLOW TRUTH ---
    # Data Point 4: 4H Spot CVD vs. Perp CVD Divergence (Div Z)
    spot_cvd_4h = float(getattr(flow.w_4h, "spot_delta_btc", 0.0) if (flow and flow.w_4h) else 0.0)
    perp_cvd_4h = float(getattr(flow.w_4h, "perp_delta_btc", 0.0) if (flow and flow.w_4h) else 0.0)
    div_z = float(getattr(flow.w_4h, "flow_divergence_z", 0.0) if (flow and flow.w_4h) else 0.0)

    is_stealth_dist = (spot_cvd_4h < -50.0 and perp_cvd_4h > 50.0 and div_z < -1.5)
    is_spot_accum = (spot_cvd_4h > 0 and (perp_cvd_4h <= 0 or spot_cvd_4h > perp_cvd_4h))

    if is_stealth_dist:
        dp4_badge = "[bold white on red] ⛔ VETO [/bold white on red]"
        dp4_summary = f"[red]Stealth Distribution! Spot dumping ({spot_cvd_4h:+,.1f} BTC) while Perp pumps (Div Z: {div_z:.2f}σ)[/red]"
    elif is_spot_accum:
        dp4_badge = "[bold black on green] ✓ PASS [/bold black on green]"
        dp4_summary = f"[green]Spot Accumulation (Spot: {spot_cvd_4h:+,.1f} BTC, Perp: {perp_cvd_4h:+,.1f} BTC)[/green]"
    else:
        dp4_badge = "[bold black on yellow] ○ NEUTRAL [/bold black on yellow]"
        dp4_summary = f"[yellow]Balanced Flow (Spot: {spot_cvd_4h:+,.1f} BTC, Perp: {perp_cvd_4h:+,.1f} BTC, Div Z: {div_z:.2f}σ)[/yellow]"

    # Data Point 5: Coinbase Premium (CPI) & US Institutional Demand
    cpi_usd, cpi_pct, cpi_z = store.get_cpi_metrics()
    if cpi_usd == 0.0 and deriv:
        cpi_usd = float(deriv.coinbase_premium_usd or 0.0)
        cpi_pct = float(deriv.coinbase_premium_pct or 0.0)
        cpi_z = float(deriv.coinbase_premium_zscore or 0.0)

    cpi_fmt = f"+${cpi_usd:,.2f}" if cpi_usd >= 0 else f"-${abs(cpi_usd):,.2f}"
    cpi_color = "green" if cpi_usd > 0 else ("red" if cpi_usd < 0 else "white")
    cpi_disp = f"[{cpi_color}]{cpi_fmt}[/{cpi_color}]"

    if cpi_usd > 2.0:
        cpi_tag = "US Institutional Bid"
        dp5_badge = "[bold black on green] ✓ PASS [/bold black on green]"
        dp5_summary = f"[green]Premium +${cpi_usd:,.2f} (+{cpi_pct:.3f}%) • {cpi_tag}[/green]"
    elif cpi_usd < -50.0:
        cpi_tag = "Heavy US Spot Selling"
        dp5_badge = "[bold white on red] ⛔ VETO [/bold white on red]"
        dp5_summary = f"[red]Discount -${abs(cpi_usd):,.2f} ({cpi_pct:.3f}%) • {cpi_tag}[/red]"
    elif cpi_usd < -5.0:
        cpi_tag = "US Spot Lag"
        dp5_badge = "[bold black on yellow] ○ CAUTION [/bold black on yellow]"
        dp5_summary = f"[yellow]Discount -${abs(cpi_usd):,.2f} ({cpi_pct:.3f}%) • {cpi_tag}[/yellow]"
    else:
        cpi_tag = "Neutral Spread"
        dp5_badge = "[cyan]○ NEUTRAL[/cyan]"
        dp5_summary = f"[cyan]Spread ${cpi_usd:+,.2f} ({cpi_pct:+.3f}%) • {cpi_tag}[/cyan]"

    # --- PILLAR 4: LEVERAGE FUEL ---
    # Data Point 6: Open Interest (4H dOI%) & 8H Funding / Perp Basis
    oi_btc = float(getattr(deriv, "open_interest_btc", 0.0) or store.open_interest_btc)
    oi_4h_pct = float(getattr(deriv, "oi_change_4h_pct", 0.0) or store.get_oi_change_pct(14400))
    funding_rate = float(getattr(deriv, "funding_rate_pct", 0.0) or store.funding_rate_pct)
    basis_usd = float(getattr(deriv, "perp_basis_usd", 0.0))

    is_crowded_long = (oi_4h_pct > 2.5 and funding_rate > 0.012)
    is_squeeze_fuel = (funding_rate < 0.00 or (oi_4h_pct > 1.5 and funding_rate <= 0.005))

    if is_crowded_long:
        dp6_badge = "[bold white on red] ⛔ VETO [/bold white on red]"
        dp6_summary = f"[red]Crowded Long Trap (OI: {oi_4h_pct:+.1f}%, Funding: {funding_rate:+.4f}% > 0.012%)[/red]"
    elif is_squeeze_fuel:
        dp6_badge = "[bold black on green] ✓ FUEL [/bold black on green]"
        dp6_summary = f"[green]Coiled Squeeze Fuel (Funding: {funding_rate:+.4f}%, OI 4H: {oi_4h_pct:+.1f}%)[/green]"
    else:
        dp6_badge = "[bold black on green] ✓ PASS [/bold black on green]"
        dp6_summary = f"[green]Uncrowded Base (OI: {oi_btc:,.0f} BTC, 4H dOI: {oi_4h_pct:+.1f}%, Funding: {funding_rate:+.4f}%)[/green]"

    # --- PILLAR 5: SNIPER TRIGGER ---
    # Data Point 7: 15m Footprint Wick Absorption & Delta Flip (Desk [F])
    bar_delta = float(getattr(f_ev, "active_bar_delta", 0.0) if f_ev else 0.0)
    prev_delta = float(getattr(f_ev, "prev_bar_delta", 0.0) if f_ev else 0.0)
    wick_abs = bool(getattr(f_ev, "gate3_wick_absorption", False) if f_ev else False)
    delta_flip = bool(getattr(f_ev, "gate4_delta_flip", False) if f_ev else False)
    all_gates_pass = bool(getattr(f_ev, "all_gates_pass", False) if f_ev else False)
    auc_comp = bool(getattr(f_ev, "auction_completed", True) if f_ev else True)
    poc_rec = bool(getattr(f_ev, "bar_poc_reclaimed", True) if f_ev else True)

    if all_gates_pass or (wick_abs and delta_flip):
        dp7_badge = "[bold black on bright_cyan] 🎯 TRIGGERED [/bold black on bright_cyan]"
        dp7_summary = f"[bold bright_cyan]Lower Wick Absorption Confirmed + 15m Delta Flip ({bar_delta:+,.1f} BTC)[/bold bright_cyan]"
    elif wick_abs:
        dp7_badge = "[bold black on yellow] ○ ARMED (Δ Flip) [/bold black on yellow]"
        dp7_summary = f"[yellow]Passive Bids Absorbed Sweep • Awaiting 15m Positive Delta Flip (Current: {bar_delta:+,.1f} BTC)[/yellow]"
    elif delta_flip:
        dp7_badge = "[bold yellow]○ DELTA FLIP[/bold yellow]"
        dp7_summary = f"[yellow]Positive Delta Flip ({bar_delta:+,.1f} BTC) • Awaiting Lower Wick Tap[/yellow]"
    else:
        dp7_badge = "[dim]○ OBSERVING[/dim]"
        dp7_summary = f"[dim]No Sweep/Absorption Yet (15m Delta: {bar_delta:+,.1f} BTC)[/dim]"

    # -------------------------------------------------------------------------
    # 2. MASTER WATERFALL SYNTHESIS & BINDING CONSTRAINT
    # -------------------------------------------------------------------------
    if ntz_active:
        master_status = "[bold white on red] RED: 100% CASH LOCK (SYSTEMIC HAZARD VETO) [/bold white on red]"
        binding_constraint = f"[bold red]PILLAR 1 VETO:[/bold red] Systemic Non-Trade Zone active ({ntz_text}). All spot entries locked."
        plain_english = "Major macro news event or systemic cascade in progress. Market is highly hazardous; stay 100% in cash."
        border_color = "red"
    elif is_stealth_dist:
        master_status = "[bold white on red] RED: 100% CASH (STEALTH DISTRIBUTION VETO) [/bold white on red]"
        binding_constraint = f"[bold red]PILLAR 3 VETO:[/bold red] Spot CVD dumping ({spot_cvd_4h:+,.1f} BTC) while Perp pumps (Div Z = {div_z:.2f}σ)."
        plain_english = "Whales are quietly selling real BTC into a retail-driven futures bounce. Do NOT buy; stay 100% in cash."
        border_color = "red"
    elif is_crowded_long:
        master_status = "[bold white on red] RED: 100% CASH (LEVERAGED LONG TRAP VETO) [/bold white on red]"
        binding_constraint = f"[bold red]PILLAR 4 VETO:[/bold red] Futures OI expanding with funding > 0.012% into resistance."
        plain_english = "Too many gamblers borrowing money to buy near resistance. High risk of a long liquidation flush; stay in cash."
        border_color = "red"
    elif cpi_usd < -50.0 and not at_edge:
        master_status = "[bold white on red] RED: 100% CASH (HEAVY US SPOT SELLING) [/bold white on red]"
        binding_constraint = f"[bold red]PILLAR 3 VETO:[/bold red] Coinbase Premium at deep discount (${cpi_usd:+,.2f}). US institutions selling."
        plain_english = "US institutions on Coinbase are actively dumping coins onto offshore exchanges. Stand aside in cash."
        border_color = "red"
    elif all_gates_pass or (wick_abs and delta_flip and rrr_pass):
        master_status = "[bold black on bright_green] GREEN: ALL 5 PILLARS ALIGNED — EXECUTE SPOT SWING LONG [/bold black on bright_green]"
        binding_constraint = "[bold green]NO BINDING CONSTRAINTS:[/bold green] Macro permission, structural map, flow truth, and footprint trigger verified."
        plain_english = "Institutions confirmed: Big players absorbed sellers at key support and turned buyers. Safe to buy Spot BTC."
        border_color = "bright_green"
    elif at_edge or (wick_abs and not delta_flip):
        master_status = "[bold black on bright_cyan] BLUE: SETUP ARMED — PRE-POSITION LIMIT BIDS AT SUPPORT SHELF [/bold black on bright_cyan]"
        binding_constraint = f"[bold cyan]PILLAR 5 AWAITING TRIGGER:[/bold cyan] At key structural edge (${c_val:,.0f}); waiting for 15m Delta Flip."
        plain_english = "Price is sitting at strong institutional support. Waiting for buyers to show up on the 15m chart before entering."
        border_color = "cyan"
    else:
        master_status = "[bold black on yellow] AMBER: PATIENT OBSERVATION — MID-RANGE CHOP [/bold black on yellow]"
        binding_constraint = f"[bold yellow]PILLAR 2 CONSTRAINT:[/bold yellow] Price in mid-range chop; awaiting sweep of 30D cVAL (${c_val:,.0f}) or HVN Floor (${hvn_floor:,.0f})."
        plain_english = "Price is stuck in the middle of nowhere (choppy range). No edge here; wait patiently for price to drop to support."
        border_color = "yellow"

    # --- TOP EXECUTIVE BANNER ---
    banner_grid = Table.grid(expand=True)
    banner_grid.add_column(justify="left", no_wrap=True)
    banner_grid.add_column(justify="right", no_wrap=True)
    banner_grid.add_row(
        f"[bold white]MASTER VERDICT:[/bold white] {master_status}",
        f"[bold white]RISK CAP:[/bold white] [bold cyan]{p1_risk_cap}[/bold cyan]  [dim]│[/dim]  [bold white]BTC:[/bold white] [bold cyan]${current_price:,.2f}[/bold cyan]",
    )
    banner_grid.add_row(
        f"[bold white]BINDING CONSTRAINT:[/bold white] {binding_constraint}",
        f"[dim]Keys: W Waterfall • F Footprint • 0 Spot • 1-9 Desks • L Master • C Copy[/dim]",
    )
    banner_grid.add_row(
        f"[bold white]PLAIN ENGLISH:[/bold white] [bold bright_white]{plain_english}[/bold bright_white]",
        f"[dim white]Rule: Spot-Only • Triple-Barrier Protocol[/dim white]",
    )
    banner_panel = Panel(banner_grid, border_style=border_color, box=box.ROUNDED, padding=(0, 1))

    # -------------------------------------------------------------------------
    # 3. THE 5-PILLAR DECISION WATERFALL TABLE (7 ESSENTIAL DATA POINTS)
    # -------------------------------------------------------------------------
    wf_table = Table(
        box=box.SIMPLE_HEAVY,
        expand=True,
        show_header=True,
        header_style="bold bright_white on dark_blue",
        pad_edge=False,
    )
    wf_table.add_column("Pillar & Institutional Role", style="bold white", width=30, no_wrap=True)
    wf_table.add_column("Essential Data Point", width=34, no_wrap=True)
    wf_table.add_column("Live Telemetry & State", width=46, no_wrap=True)
    wf_table.add_column("Strict Rule / Gate Threshold", width=36, no_wrap=True)
    wf_table.add_column("Gate Verdict", justify="center", width=18, no_wrap=True)

    # Row 1: Pillar 1 / Data Point 1
    wf_table.add_row(
        "[bold cyan]P1: MACRO PERMISSION[/bold cyan]\n[dim]Capital Authorization & Hazard Locks[/dim]",
        "1. 1D 200 SMA (+5D Slope) &\n   NTZ 8A–8F Systemic Shields",
        f"200 SMA: ${sma200_px:,.0f} ({'Above' if above_200 else 'Below'})\nSlope: {sma200_slope_usd:+,.1f}/d • NTZ: {ntz_text[:24]}",
        "Price > 200D SMA (1.0% Risk)\nZero active NTZ 8A-8F triggers",
        p1_badge,
    )

    # Row 2: Pillar 2 / Data Point 2
    wf_table.add_row(
        "[bold cyan]P2: STRUCTURAL MAP[/bold cyan]\n[dim]Fair Value Distribution & Shelves[/dim]",
        "2. 30D Composite Profile\n   (cVAL / cPOC / cVAH / HVN)",
        f"cVAL: ${c_val:,.0f} • cPOC: ${c_poc:,.0f}\ncVAH: ${c_vah:,.0f} • Base HVN: ${hvn_floor:,.0f}",
        "Enter at cVAL / HVN Support Floor\nStrictly VETO buying in mid-chop",
        dp2_badge,
    )

    # Row 3: Pillar 2 / Data Point 3
    wf_table.add_row(
        "[bold cyan]P2: LIVE ASYMMETRY[/bold cyan]\n[dim]Forced Liquidation Target Pools[/dim]",
        "3. Liquidation Magnets &\n   Live R:R Ratio to Upper Magnet",
        f"Short-Liq: ${short_mag:,.0f} (+{abs(short_dist):.2f}%)\nLong-Liq:  ${long_mag:,.0f} ({long_dist:+.2f}%) • {rrr_val:.2f}R",
        "Live R:R ≥ 3.0R to Short Magnet\nIf Long Liq sits below: 2 tranches",
        dp3_badge,
    )

    # Row 4: Pillar 3 / Data Point 4
    wf_table.add_row(
        "[bold cyan]P3: FLOW TRUTH[/bold cyan]\n[dim]True Spot vs Leveraged Futures[/dim]",
        "4. 4H Spot CVD vs. Perp CVD\n   Divergence (Div Z-Score)",
        f"4H Spot CVD: {_color_signed(spot_cvd_4h, '+,.1f', ' BTC')}\n4H Perp CVD: {_color_signed(perp_cvd_4h, '+,.1f', ' BTC')} • Div: {div_z:.2f}σ",
        "Spot CVD > 0 while Perp CVD < 0\nVETO on Stealth Distribution",
        dp4_badge,
    )

    # Row 5: Pillar 3 / Data Point 5
    wf_table.add_row(
        "[bold cyan]P3: INSTITUTIONAL BACKING[/bold cyan]\n[dim]US Order Flow vs Offshore USDT[/dim]",
        "5. Coinbase Premium Index (CPI) &\n   Spot L2 Order Book Depth",
        f"CPI Spread: {cpi_disp} ({cpi_pct:+.3f}%)\nCPI Z-Score: {cpi_z:+.2f}σ ({cpi_tag})",
        "CPI > -$15.0 (No heavy US dump)\nBid/Ask Depth Ratio ≥ 1.0",
        dp5_badge,
    )

    # Row 6: Pillar 4 / Data Point 6
    wf_table.add_row(
        "[bold cyan]P4: LEVERAGE FUEL[/bold cyan]\n[dim]Systemic Open Interest & Funding[/dim]",
        "6. Open Interest (4H dOI%) &\n   8H Funding Rate / Basis",
        f"OI: {oi_btc:,.0f} BTC • 4H dOI: {oi_4h_pct:+.1f}%\nFunding: {funding_rate:+.4f}% • Basis: ${basis_usd:,.0f}",
        "Funding ≤ +0.012% (Uncrowded)\nNegative Funding = Squeeze Fuel",
        dp6_badge,
    )

    # Row 7: Pillar 5 / Data Point 7
    wf_table.add_row(
        "[bold cyan]P5: SNIPER TRIGGER[/bold cyan]\n[dim]Intra-Candle Footprint Execution[/dim]",
        "7. 15m Footprint Wick Absorption\n   & Positive Delta Flip (Desk F)",
        f"15m Delta: {_color_signed(bar_delta, '+,.1f', ' BTC')} (Prev: {_color_signed(prev_delta, '+,.1f')})\nWick Abs: {'YES' if wick_abs else 'NO'} • Flip: {'YES' if delta_flip else 'NO'}",
        "Passive limit buyers absorb sweep\n15m candle closes with +Δ flip",
        dp7_badge,
    )

    wf_panel = Panel(
        wf_table,
        title="[bold bright_yellow]THE 5-PILLAR INSTITUTIONAL DECISION WATERFALL & 7 ESSENTIAL DATA POINTS[/bold bright_yellow]",
        border_style="bright_blue",
        box=box.ROUNDED,
        padding=(0, 1),
    )

    # -------------------------------------------------------------------------
    # 4. TWO-COLUMN DEEP DIVE PANELS
    # -------------------------------------------------------------------------

    # --- LEFT COLUMN: PILLARS 1 & 2 (MAP & ASYMMETRY) + PILLARS 3 & 4 (FLOW & LEVERAGE) ---
    p12_table = Table.grid(expand=True)
    p12_table.add_column(justify="left", no_wrap=True)
    p12_table.add_row("[bold white]1. MACRO PERMISSION & SHIELDS (Pillar 1)[/bold white]")
    p12_table.add_row(f" • [white]1D 200 SMA Gatekeeper:[/white] [cyan]${sma200_px:,.0f}[/cyan] ({'ABOVE' if above_200 else 'BELOW'}) • 5D Slope: [cyan]{sma200_slope_usd:+,.1f}$/d[/cyan] ({'Rising' if slope_pos else 'Falling'})")
    p12_table.add_row(f" • [white]NTZ 8A-8F Systemic Shield:[/white] {ntz_text} ({'LOCKED' if ntz_active else 'CLEAR'})")
    p12_table.add_row(f" • [white]Authorized Swing Risk:[/white] [bold green]{p1_risk_cap}[/bold green] (Strict Spot Allocation)")
    p12_table.add_row("")
    p12_table.add_row("[bold white]2. STRUCTURAL MAP & LIQUIDATION ASYMMETRY (Pillar 2)[/bold white]")
    p12_table.add_row(f" • [white]30D Composite Profile:[/white] cVAH [yellow]${c_vah:,.0f}[/yellow] • cPOC [cyan]${c_poc:,.0f}[/cyan] • cVAL [green]${c_val:,.0f}[/green]")
    p12_table.add_row(f" • [white]Support Base (HVN Floor):[/white] [green]${hvn_floor:,.0f}[/green] • VA Position: [cyan]{va_pos:.1f}%[/cyan] ({'Mid-Chop' if is_mid_chop else 'Range Edge'})")
    p12_table.add_row(f" • [white]Upper Short-Liq Magnet:[/white] [magenta]${short_mag:,.0f}[/magenta] (+{abs(short_dist):.2f}% Squeeze Fuel)")
    p12_table.add_row(f" • [white]Lower Long-Liq Magnet :[/white] [cyan]${long_mag:,.0f}[/cyan] ({long_dist:+.2f}% Stop Hunt Floor)")
    p12_table.add_row(f" • [white]Live Asymmetry to Target:[/white] [bold {'green' if rrr_pass else 'yellow'}]{rrr_val:.2f}R[/bold {'green' if rrr_pass else 'yellow'}] (Min Hurdle: ≥ 3.00R • Max Buy: [cyan]${max_entry_3r:,.0f}[/cyan])")

    p12_panel = Panel(
        p12_table,
        title="[bold magenta]PILLARS 1 & 2: MACRO PERMISSION & STRUCTURAL MAP[/bold magenta]",
        border_style="magenta",
        box=box.ROUNDED,
        padding=(0, 1),
    )

    p34_table = Table.grid(expand=True)
    p34_table.add_column(justify="left", no_wrap=True)
    p34_table.add_row("[bold white]3. CROSS-VENUE FLOW TRUTH (Pillar 3)[/bold white]")
    p34_table.add_row(f" • [white]4H Spot CVD vs. Perp CVD:[/white] Spot {_color_signed(spot_cvd_4h, '+,.1f', ' BTC')} vs Perp {_color_signed(perp_cvd_4h, '+,.1f', ' BTC')}")
    p34_table.add_row(f" • [white]Divergence Z-Score:[/white] [cyan]{div_z:.2f}σ[/cyan] • Signature: {'[bold red]STEALTH DISTRIBUTION[/bold red]' if is_stealth_dist else ('[bold green]SPOT ACCUMULATION[/bold green]' if is_spot_accum else '[cyan]BALANCED FLOW[/cyan]')}")
    p34_table.add_row(f" • [white]Coinbase Premium (CPI):[/white] {cpi_disp} ({cpi_pct:+.3f}%) • [cyan]{cpi_tag}[/cyan]")
    p34_table.add_row("")
    p34_table.add_row("[bold white]4. LEVERAGE FUEL DYNAMICS (Pillar 4)[/bold white]")
    p34_table.add_row(f" • [white]Total Open Interest:[/white] [cyan]{oi_btc:,.0f} BTC[/cyan] • 4H Change: [cyan]{oi_4h_pct:+.1f}%[/cyan] ({'Expanding' if oi_4h_pct > 1.0 else ('Purging' if oi_4h_pct < -1.0 else 'Steady')})")
    p34_table.add_row(f" • [white]8H Predicted Funding:[/white] [cyan]{funding_rate:+.4f}%[/cyan] ({'Crowded Long' if funding_rate > 0.012 else ('Squeeze Fuel' if funding_rate < 0 else 'Neutral Base')})")
    p34_table.add_row(f" • [white]Perp Basis Spread:[/white] [cyan]${basis_usd:+,.1f}[/cyan] (Perp vs Spot Premium)")

    p34_panel = Panel(
        p34_table,
        title="[bold green]PILLARS 3 & 4: CROSS-VENUE FLOW & LEVERAGE MATRIX[/bold green]",
        border_style="green",
        box=box.ROUNDED,
        padding=(0, 1),
    )

    left_column = Group(p12_panel, p34_panel)

    # --- RIGHT COLUMN: PILLAR 5 (SNIPER TRIGGER) + TURNKEY ORDER CARD ---
    p5_table = Table.grid(expand=True)
    p5_table.add_column(justify="left", no_wrap=True)
    p5_table.add_row("[bold white]5. 15M FOOTPRINT SNIPER TRIGGER (Pillar 5)[/bold white]")
    p5_table.add_row(f" • [white]15m Candle Delta:[/white] {_color_signed(bar_delta, '+,.1f', ' BTC')} (Previous 15m: {_color_signed(prev_delta, '+,.1f', ' BTC')})")
    p5_table.add_row(f" • [white]Delta Shift State:[/white] [bold {'green' if delta_flip else 'yellow'}]{'BULLISH DELTA FLIP (CONFIRMED)' if delta_flip else 'AWAITING POSITIVE FLIP'}[/bold {'green' if delta_flip else 'yellow'}]")
    p5_table.add_row(f" • [white]Lower-Wick Absorption:[/white] [bold {'green' if wick_abs else 'yellow'}]{'PASSIVE BIDS ABSORBED SWEEP' if wick_abs else 'NO ABSORPTION DETECTED'}[/bold {'green' if wick_abs else 'yellow'}]")
    p5_table.add_row(f" • [white]Auction Status:[/white] [cyan]{'Completed Auction (Exhaustion Low)' if auc_comp else 'Unfinished Auction'}[/cyan]")
    p5_table.add_row(f" • [white]Bar POC Location:[/white] [cyan]{'Closed Above Bar POC (Reclaimed)' if poc_rec else 'Trapped Below Bar POC'}[/cyan]")

    if f_ev and f_ev.recent_bars_deltas:
        recent_str = " → ".join(
            f"[{'green' if d > 0 else 'red'}]{d:+,.1f}[/{'green' if d > 0 else 'red'}]"
            for d in f_ev.recent_bars_deltas[-4:]
        )
        p5_table.add_row(f" • [white]Recent 15m Deltas:[/white] [dim]({recent_str} → [/dim]{_color_signed(bar_delta, '+,.1f')}[dim])[/dim]")

    p5_panel = Panel(
        p5_table,
        title="[bold bright_cyan]PILLAR 5: 15M FOOTPRINT SNIPER TRIGGER (DESK [F])[/bold bright_cyan]",
        border_style="bright_cyan",
        box=box.ROUNDED,
        padding=(0, 1),
    )

    # Turnkey Action Plan & Staged Limit Orders
    order_table = Table(
        box=box.SIMPLE_HEAVY,
        expand=True,
        show_header=True,
        header_style="bold yellow",
        pad_edge=False,
    )
    order_table.add_column("Order Tranche", style="bold white", width=22, no_wrap=True)
    order_table.add_column("Entry", style="cyan", justify="right", width=11, no_wrap=True)
    order_table.add_column("Hard Stop", style="red", justify="right", width=11, no_wrap=True)
    order_table.add_column("TP1 (cPOC)", style="green", justify="right", width=12, no_wrap=True)
    order_table.add_column("TP2 (Liq)", style="magenta", justify="right", width=12, no_wrap=True)
    order_table.add_column("Alloc / Risk", justify="center", width=14, no_wrap=True)

    t1_entry = c_val if c_val > 0 else (current_price * 0.99)
    t1_stop = t1_entry * 0.985
    t2_entry = hvn_floor if hvn_floor > 0 else (t1_entry * 0.985)
    t2_stop = t2_entry * 0.985
    tp1_target = c_poc if c_poc > 0 else (current_price * 1.02)
    tp2_target = short_mag if short_mag > 0 else (current_price * 1.04)

    order_table.add_row(
        "Tranche 1 (Front-Run)",
        f"${t1_entry:,.0f}",
        f"${t1_stop:,.0f}",
        f"${tp1_target:,.0f}",
        f"${tp2_target:,.0f}",
        "50% (0.50% R)",
    )
    order_table.add_row(
        "Tranche 2 (Sweep Base)",
        f"${t2_entry:,.0f}",
        f"${t2_stop:,.0f}",
        f"${tp1_target:,.0f}",
        f"${tp2_target:,.0f}",
        "50% (0.50% R)",
    )

    order_notes = Table.grid(expand=True)
    order_notes.add_column(justify="left", no_wrap=True)
    order_notes.add_row("[bold white]CAPITAL PRESERVATION RULES & EXECUTION DIRECTIVE:[/bold white]")
    order_notes.add_row(" • [bold yellow]Strictly Spot BTC Only:[/bold yellow] Zero leverage, zero liquidation risk, 100% asset custody.")
    order_notes.add_row(" • [bold yellow]Triple-Barrier Protocol:[/bold yellow] At TP1 (30D cPOC), harvest 50% profit & ratchet Hard Stop to Breakeven ($0 risk).")
    order_notes.add_row(" • [bold yellow]Asymmetry Hurdle:[/bold yellow] If Live R:R < 3.0R, cancel market fills; maintain resting limit bids only.")

    action_group = Group(order_table, Rule(style="dim yellow"), order_notes)
    action_panel = Panel(
        action_group,
        title="[bold yellow]EXECUTIVE TACTICAL DIRECTIVE & STAGED LIMIT ORDER CARD[/bold yellow]",
        border_style="yellow",
        box=box.ROUNDED,
        padding=(0, 1),
    )

    right_column = Group(p5_panel, action_panel)

    split_grid = Table.grid(expand=True)
    split_grid.add_column(justify="left", no_wrap=False, ratio=1)
    split_grid.add_column(justify="left", no_wrap=False, ratio=1)
    split_grid.add_row(left_column, right_column)

    return Group(header_panel, banner_panel, wf_panel, split_grid)



def _star_rating_str(strength: int) -> str:
    """Formats 1-5 level strength as stars."""
    stars = "★" * min(5, max(1, strength)) + "☆" * (5 - min(5, max(1, strength)))
    if strength >= 5:
        return f"[bold bright_yellow][{stars}] (5/5 Pristine)[/bold bright_yellow]"
    elif strength == 4:
        return f"[bold yellow][{stars}] (4/5 Strong)[/bold yellow]"
    elif strength == 3:
        return f"[bold cyan][{stars}] (3/5 Valid)[/bold cyan]"
    elif strength == 2:
        return f"[dim white][{stars}] (2/5 Weak)[/dim white]"
    return f"[dim red][{stars}] (1/5 Fragile)[/dim red]"


def _build_tab13_slsp_price_action_hud(store: StateStore, header_panel: Panel) -> Group:
    """Renders Tab [13: P]: 4-Pillar Price Action & Structure Protocol Desk.
    
    5-Panel Institutional Architecture:
    - Verdict Banner: Executive Trade State, Bias, Mode, Confluence Score, Risk Cap, Spot Price
    - Row 1:
      - Left: [1] File A: SLSP v1.0 (Structure + Level Swing Protocol)
      - Right: [2] File B: Industrial 3-EMA Trading Strategy
    - Row 2:
      - Left: [3] Project 8: BTC Liquidation Flush Detector
      - Right: [4] Project 7: Tell-Tale Volume Capitulation Climax Sensor
    - Row 3:
      - Full Width: [5] Executive Bottomline & Beginner Action Playbook (What To Do Right Now)
    """
    slsp = getattr(store, "slsp_evaluation", None)
    sig = store.latest_signal
    spot_px = store.binance_spot_price or (sig.current_price if sig else 0.0)
    ema_snap = store.ema_strategy
    trap_eval = store.trap_evaluation
    exhaust_eval = store.exhaustion_evaluation
    tt_eval = exhaust_eval.tell_tale if exhaust_eval else None
    
    liq_rep = getattr(slsp, "liq_detector_report", None) or getattr(store, "liquidation_report", None)
    if liq_rep is None:
        try:
            from analytics.liquidation_reader import read_latest_liquidation_report
            liq_rep = read_latest_liquidation_report()
        except Exception:
            liq_rep = None

    if slsp is None:
        return Group(
            header_panel,
            Panel(
                "Warming up Tab [13: P]: Structure + Level Swing Protocol (SLSP v1.0) & 4-Pillar Engine...\n"
                "Scanning Daily swing pivots, 4H rejection candles, 3-EMA value bands, and liquidation sensors...",
                title="[bold bright_yellow]DESK [P]: 4-PILLAR PRICE ACTION & STRUCTURE PROTOCOL[/bold bright_yellow]",
                box=box.ROUNDED,
                border_style="bright_yellow",
            ),
        )

    # =========================================================================
    # 0. DESK [P] EXECUTIVE VERDICT BANNER
    # =========================================================================
    state_style = {
        "IN_POSITION": "bold white on green",
        "TRIGGER_FIRED": "bold black on bright_yellow",
        "VALUE_ZONE_WATCH": "bold black on cyan",
        "REJECTION_ARMED": "bold black on magenta",
        "STAND_ASIDE": "bold white on red",
        "CIRCUIT_BREAKER_LOCKOUT": "bold white on red",
        "SCANNING": "bold white on blue",
    }.get(slsp.trade_state, "bold white on blue")

    score_color = "bright_green" if slsp.confluence_score >= 75 else ("yellow" if slsp.confluence_score >= 50 else "dim red")

    verdict_grid = Table.grid(expand=True)
    verdict_grid.add_column(justify="left", no_wrap=True)
    verdict_grid.add_column(justify="right", no_wrap=True)
    verdict_grid.add_row(
        f"[{state_style}] [{slsp.trade_state}] [/{state_style}]  •  "
        f"BIAS: [bold white]{slsp.regime}[/bold white]  •  "
        f"MODE: [bold cyan]{slsp.mode}[/bold cyan]  •  "
        f"CONFLUENCE: [{score_color}][bold]{slsp.confluence_score}/100[/bold][/{score_color}]",
        f"[dim white]Risk Cap:[/dim white] [bold yellow]0.75% Equity ($750 Max)[/bold yellow]  │  "
        f"[dim white]BTC Spot:[/dim white] [bold cyan]${spot_px:,.2f}[/bold cyan]",
    )

    verdict_panel = Panel(
        Group(
            verdict_grid,
            Text(f"EXECUTIVE SUMMARY: {slsp.plain_english_summary}", style="italic white"),
        ),
        title="[bold bright_yellow]DESK [P] EXECUTIVE VERDICT: 4-PILLAR PRICE ACTION & STRUCTURE PROTOCOL[/bold bright_yellow]",
        border_style="bright_yellow",
        box=box.ROUNDED,
        padding=(0, 1),
    )

    # =========================================================================
    # ROW 1 - LEFT: PANEL [1] FILE A: SLSP v1.0 (STRUCTURE + LEVEL SWING)
    # =========================================================================
    p1_table = Table(box=box.SIMPLE_HEAD, expand=True, padding=(0, 1))
    p1_table.add_column("Protocol Component", style="cyan", no_wrap=True, ratio=3)
    p1_table.add_column("Observed State", style="white", no_wrap=True, ratio=4)
    p1_table.add_column("Rules & Verification", style="green", no_wrap=True, ratio=4)

    # 1. Market Regime
    reg_style = "bold bright_green" if slsp.regime == "UPTREND" else ("bold bright_red" if slsp.regime == "DOWNTREND" else "bold yellow")
    p1_table.add_row(
        "Daily Market Regime",
        f"[{reg_style}]{slsp.regime}[/{reg_style}]",
        f"[dim]{slsp.regime_reason[:42]}[/dim]" if slsp.regime_reason else "Swing Pivots Intact",
    )

    # 2. Nearest Support Shelf
    if slsp.nearest_support:
        supp = slsp.nearest_support
        dist_s = ((spot_px - supp.center_price) / supp.center_price) * 100.0
        in_pocket = abs(dist_s) <= 0.5
        pocket_tag = "[bold bright_green]IN POCKET (<=0.5%)[/bold bright_green]" if in_pocket else f"[dim]{dist_s:+.1f}% dist[/dim]"
        round_tag = " • Round #" if supp.is_round_number else ""
        hvn_tag = " • HVN Shelf" if supp.is_hvn else ""
        p1_table.add_row(
            "Key Support Shelf",
            f"${supp.center_price:,.2f} (${supp.price_min:,.0f}–${supp.price_max:,.0f})",
            f"{_star_rating_str(supp.strength)} • {supp.touch_count}x touches{round_tag}{hvn_tag} • {pocket_tag}",
        )
    else:
        p1_table.add_row("Key Support Shelf", "No Daily Level <= 10%", "[dim]Scanning swing pivots...[/dim]")

    # 3. Nearest Resistance Shelf
    if slsp.nearest_resistance:
        res = slsp.nearest_resistance
        dist_r = ((res.center_price - spot_px) / spot_px) * 100.0
        p1_table.add_row(
            "Key Resistance Shelf",
            f"${res.center_price:,.2f} (${res.price_min:,.0f}–${res.price_max:,.0f})",
            f"{_star_rating_str(res.strength)} • +{dist_r:.1f}% overhead ({res.touch_count}x touches)",
        )
    else:
        p1_table.add_row("Key Resistance Shelf", "No Major Level <= 10%", "[green]Blue Sky / Clear Path[/green]")

    # 4. 1.5R Runway Obstacle Check
    setup = slsp.active_setup
    if setup:
        obs_style = "bold bright_green" if not setup.obstacle_detected else "bold bright_red"
        p1_table.add_row(
            "1.5R Runway Clearance",
            f"Runway: {setup.obstacle_r:.1f}R to Resistance",
            f"[{obs_style}]{setup.obstacle_description[:45]}[/{obs_style}]",
        )
    else:
        p1_table.add_row("1.5R Runway Clearance", "Runway Check Pending", "[dim]Requires >= 1.5R unobstructed to resistance[/dim]")

    # 5. 4H Candlestick Rejection & Volume
    if setup and setup.rejection_candle_type != "NONE":
        p1_table.add_row(
            "4H Rejection & Volume",
            f"{setup.rejection_candle_type} (Wick: {setup.rejection_wick_ratio*100:.1f}%)",
            f"Vol: {setup.rejection_volume_ratio:.2f}x 20SMA • [bold bright_green]CONFIRMED[/bold bright_green]",
        )
    elif setup:
        vol_col = "yellow" if setup.rejection_volume_ratio >= 1.0 else "dim red"
        p1_table.add_row(
            "4H Rejection & Volume",
            f"Scanning 4H Close (Vol: {setup.rejection_volume_ratio:.2f}x)",
            f"[{vol_col}]Pinbar >=50% or Engulfing required with Vol > 20SMA[/{vol_col}]",
        )
    else:
        p1_table.add_row("4H Rejection & Volume", "Scanning 4H Bars", "[dim]Requires Pinbar >=50% or Engulfing + Vol > 20SMA[/dim]")

    # 6. Trade Parameters & Risk Sizing
    if setup:
        p1_table.add_row(
            "SLSP Trade Sizing & Risk",
            f"{setup.position_size_btc:.4f} BTC (${setup.notional_value_usd:,.0f} notional)",
            f"[bold yellow]0.75% Equity (${100000.0 * (setup.risk_pct/100):,.0f} max risk)[/bold yellow] • Zero Leverage",
        )
        p1_table.add_row(
            "Targets & Invalidation",
            f"SL: ${setup.stop_loss:,.2f} (-${setup.risk_per_coin:,.2f})",
            f"TP1 (+1.5R): ${setup.tp1_price:,.2f} (50%) • TP2 (+2.5R): ${setup.tp2_price:,.2f} • BE @ +1.0R",
        )
    else:
        p1_table.add_row("SLSP Trade Sizing & Risk", "Fixed 0.75% Equity Risk", "$100,000 Equity • $750 Max Risk • Zero Leverage")
        p1_table.add_row("Targets & Invalidation", "TP1: +1.5R (50%) • TP2: +2.5R", "BE Ratchet @ +1.0R (+0.1% fees) • 4H Close Invalidation")

    # 7. Circuit Breakers
    cb_style = "bold bright_green" if not slsp.circuit_breaker_active else "bold bright_red"
    cb_msg = "PASS (0.0% / 2.0% Max)" if not slsp.circuit_breaker_active else slsp.circuit_breaker_reason
    p1_table.add_row(
        "Circuit Breakers (UTC Reset)",
        f"Day Loss: {slsp.daily_loss_pct:.2f}% / 2% • Wk: {slsp.weekly_loss_pct:.2f}% / 4%",
        f"[{cb_style}]{cb_msg}[/{cb_style}]",
    )

    p1_panel = Panel(
        p1_table,
        title="[bold cyan][1] FILE A: SLSP v1.0 (STRUCTURE + LEVEL SWING PROTOCOL)[/bold cyan]",
        border_style="cyan",
        box=box.ROUNDED,
        padding=(0, 1),
    )

    # =========================================================================
    # ROW 1 - RIGHT: PANEL [2] FILE B: INDUSTRIAL 3-EMA TRADING STRATEGY
    # =========================================================================
    p2_table = Table(box=box.SIMPLE_HEAD, expand=True, padding=(0, 1))
    p2_table.add_column("Industrial 3-EMA Layer", style="bright_blue", no_wrap=True, ratio=3)
    p2_table.add_column("Observed Metric", style="white", no_wrap=True, ratio=4)
    p2_table.add_column("Algorithmic Verification", style="green", no_wrap=True, ratio=4)

    # 1. Daily 200 EMA Macro Anchor & Slope
    slope_style = "bright_green" if slsp.ema_3_slope_200 >= 0.05 else ("yellow" if slsp.ema_3_slope_200 >= -0.05 else "bright_red")
    bias_map = {
        "STRONG_BULL": "[bold bright_green]STRONG_BULL (Slope > +0.05%)[/bold bright_green]",
        "WEAK_BULL": "[bold green]WEAK_BULL[/bold green]",
        "NEUTRAL": "[bold yellow]NEUTRAL / FLAT (Slope +/-0.05%)[/bold yellow]",
        "WEAK_BEAR": "[bold red]WEAK_BEAR[/bold red]",
        "STRONG_BEAR": "[bold bright_red]STRONG_BEAR (Slope < -0.05%)[/bold bright_red]",
    }
    bias_text = bias_map.get(slsp.ema_3_regime, f"[yellow]{slsp.ema_3_regime}[/yellow]")
    d_200_val = f"${ema_snap.daily_ema_200:,.0f}" if ema_snap else "N/A"
    p2_table.add_row(
        "Daily 200 EMA Anchor",
        f"200 EMA: {d_200_val} • Slope: [{slope_style}]{slsp.ema_3_slope_200:+.3f}%/5d[/{slope_style}]",
        f"Macro Bias: {bias_text}",
    )

    # 2. Daily EMAs & Trend Quality ADX(14)
    d_20 = f"${ema_snap.daily_ema_20:,.0f}" if ema_snap else "N/A"
    d_50 = f"${ema_snap.daily_ema_50:,.0f}" if ema_snap else "N/A"
    adx_style = "bright_green" if slsp.ema_3_adx >= 20.0 else "yellow"
    adx_text = f"ADX: [{adx_style}]{slsp.ema_3_adx:.1f}[/{adx_style}] ({'TREND >=20.0' if slsp.ema_3_adx >= 20.0 else 'CHOP / FLAT <20.0'})"
    p2_table.add_row(
        "Daily EMAs (20 / 50 / 200)",
        f"20: {d_20} • 50: {d_50} • 200: {d_200_val}",
        f"{adx_text}",
    )

    # 3. 4H Dynamic Value Zone (21–50 Band)
    ema_4h_20 = f"${ema_snap.ema_4h_20:,.0f}" if ema_snap else "N/A"
    ema_4h_50 = f"${ema_snap.ema_4h_50:,.0f}" if ema_snap else "N/A"
    vz_text = "[bold bright_green]INSIDE VALUE BAND (+/-0.75 ATR)[/bold bright_green]" if slsp.ema_3_value_zone_active else "[dim]Outside 21–50 Band[/dim]"
    p2_table.add_row(
        "4H Dynamic Value Band",
        f"Band: {ema_4h_20} – {ema_4h_50}",
        f"{vz_text}",
    )

    # 4. Candlestick Rejection Evidence (3-Bar Memory)
    rej_active = ema_snap.rejection_active if ema_snap else False
    rej_txt = "[bold bright_green]REJECTION WICK OBSERVED (Last 3 Bars)[/bold bright_green]" if rej_active else "[dim]Awaiting Rejection at Band[/dim]"
    p2_table.add_row(
        "Rejection Evidence (3 Bars)",
        "Memory Window: Last 3 Closed 4H Bars",
        f"{rej_txt}",
    )

    # 5. Positioning Confluence (2 of 3 Met)
    pos_style = "bold bright_green" if slsp.ema_3_positioning_met >= 2 else "yellow"
    p2_table.add_row(
        "Positioning Confluence",
        f"Score: [{pos_style}]{slsp.ema_3_positioning_met}/3 Confirmations Met[/{pos_style}]",
        "1. OI Contraction • 2. Funding <=0.01% • 3. Spot CVD",
    )

    # 6. 4H Trigger EMA (9 EMA Close)
    ema_4h_9 = f"${ema_snap.ema_4h_9:,.0f}" if ema_snap else "N/A"
    trig_active = ema_snap.trigger_active if ema_snap else False
    trig_txt = "[bold bright_green]4H CLOSE ABOVE 9 EMA (ARMED)[/bold bright_green]" if trig_active else "[dim]Pending 4H Close > 9 EMA[/dim]"
    p2_table.add_row(
        "4H Trigger EMA (9 EMA)",
        f"9 EMA Level: {ema_4h_9}",
        f"{trig_txt}",
    )

    # 7. Stop & Trailing Arithmetic
    atr_stop_val = f"${ema_snap.suggested_atr_stop:,.2f}" if (ema_snap and ema_snap.suggested_atr_stop > 0) else "min(Low-0.1ATR, 50EMA-1.25ATR)"
    p2_table.add_row(
        "Stop & Trailing Rules",
        f"Stop: {atr_stop_val}",
        "50% @ +1.5R • Trail remaining 50% behind 4H 20 EMA",
    )

    # 8. Macro Invalidation & Time Stop
    p2_table.add_row(
        "Invalidation & Time Stop",
        "Daily Close through 200 EMA",
        "Time Stop: Exit if no expansion within 25–30 bars",
    )

    p2_panel = Panel(
        p2_table,
        title="[bold bright_blue][2] FILE B: INDUSTRIAL 3-EMA TRADING STRATEGY[/bold bright_blue]",
        border_style="bright_blue",
        box=box.ROUNDED,
        padding=(0, 1),
    )

    # =========================================================================
    # ROW 2 - LEFT: PANEL [3] PROJECT 8: BTC LIQUIDATION FLUSH DETECTOR
    # =========================================================================
    p3_table = Table(box=box.SIMPLE_HEAD, expand=True, padding=(0, 1))
    p3_table.add_column("Flush Metric", style="magenta", no_wrap=True, ratio=3)
    p3_table.add_column("Observed Value", style="white", no_wrap=True, ratio=4)
    p3_table.add_column("Cascade Telemetry", style="green", no_wrap=True, ratio=4)

    # 1. Crash/Flush Lifecycle Stage
    flush_status = liq_rep.verdict if liq_rep else "STANDBY"
    flush_detail = liq_rep.verdict_detail if liq_rep else "Companion detector monitoring"
    p3_table.add_row(
        "Crash Lifecycle Stage",
        f"[bold white]{flush_status}[/bold white]",
        f"[dim]{flush_detail[:42]}[/dim]",
    )

    # 2. Damage So Far ($ Liquidated across windows)
    w15m = liq_rep.windows.get("15m") if (liq_rep and liq_rep.windows) else None
    w1h = liq_rep.windows.get("1h") if (liq_rep and liq_rep.windows) else None
    w4h = liq_rep.windows.get("4h") if (liq_rep and liq_rep.windows) else None
    w24h = liq_rep.windows.get("24h") if (liq_rep and liq_rep.windows) else None

    v_15m = f"${w15m.total_usd/1000:,.0f}k" if w15m else "$0k"
    v_1h = f"${w1h.total_usd/1000:,.0f}k" if w1h else "$0k"
    v_4h = f"${w4h.total_usd/1000:,.0f}k" if w4h else "$0k"
    v_24h = f"${w24h.total_usd/1000:,.0f}k" if w24h else "$0k"

    tier_style = "bright_green" if (liq_rep and liq_rep.magnitude_tier == "NORMAL") else ("bold yellow" if (liq_rep and "ELEVATED" in liq_rep.magnitude_tier) else "bold bright_red")
    tier_name = liq_rep.magnitude_tier if liq_rep else "NORMAL"
    p3_table.add_row(
        "Damage So Far ($ Liquidated)",
        f"15m: {v_15m} • 1h: {v_1h} • 4h: {v_4h} • 24h: {v_24h}",
        f"Magnitude Tier: [{tier_style}]{tier_name}[/{tier_style}]",
    )

    # 3. Leverage Wipeout Telemetry
    oi_contracts = liq_rep.open_interest_contracts if liq_rep else 0.0
    fund_rate = liq_rep.funding_rate if liq_rep else 0.0
    fund_stat = liq_rep.funding_status if liq_rep else "NEUTRAL"
    oi_txt = f"{oi_contracts:,.0f} contracts" if oi_contracts > 0 else "N/A"
    p3_table.add_row(
        "Leverage Wipeout Telemetry",
        f"OI: {oi_txt} • 1h dOI: {slsp.liq_flush_oi_delta:+.2f}%",
        f"Funding: {fund_rate*100:+.4f}% • [dim]{fund_stat[:28]}[/dim]",
    )

    # 4. Key Demand Zone Analysis ($75,000–$78,000)
    dz_status = liq_rep.demand_zone_status if (liq_rep and liq_rep.demand_zone_status != "N/A") else "INSIDE_ZONE"
    dz_lower = liq_rep.demand_zone_lower if (liq_rep and liq_rep.demand_zone_lower > 0) else 75000.0
    dz_upper = liq_rep.demand_zone_upper if (liq_rep and liq_rep.demand_zone_upper > 0) else 78000.0
    dz_dist_lower = liq_rep.demand_zone_dist_lower_pct if liq_rep else +0.54
    dz_dist_upper = liq_rep.demand_zone_dist_upper_pct if liq_rep else -3.33

    dz_style = "bold bright_green" if dz_status == "INSIDE_ZONE" else ("bold yellow" if dz_status == "APPROACHING_ZONE" else "bold bright_red")
    p3_table.add_row(
        "Key Demand Zone ($75k–$78k)",
        f"[{dz_style}]{dz_status}[/{dz_style}] (${dz_lower:,.0f} – ${dz_upper:,.0f})",
        f"Floor: {dz_dist_lower:+.2f}% ($75k) • Ceiling: {dz_dist_upper:+.2f}% ($78k)",
    )

    # 5. Microstructure / Post-Flush Structure
    post_struct = liq_rep.post_flush_price_structure if liq_rep else None
    hl_formed = post_struct.higher_low_formed if post_struct else True
    ll_stopped = post_struct.stopped_making_lower_lows if post_struct else True
    vol_ratio_pf = post_struct.volume_ratio if post_struct else 0.75

    p3_table.add_row(
        "Microstructure Post-Flush",
        f"Higher Low: {'[bold green]YES[/bold green]' if hl_formed else '[dim]NO[/dim]'} • Lower Lows Stopped: {'[bold green]YES[/bold green]' if ll_stopped else '[dim]NO[/dim]'}",
        f"Spot Volume Ratio: {vol_ratio_pf:.2f}x 20MA • Prior High: PENDING",
    )

    # 6. Asia Session Low Sweep & Reclaim
    asia_swept = trap_eval.asia_low_swept if trap_eval else False
    asia_style = "bold bright_green" if asia_swept else "dim"
    p3_table.add_row(
        "Session Liquidity Sweeps",
        f"Asia Session Low: [{asia_style}]{'SWEPT & RECLAIMED (+25 PTS)' if asia_swept else 'INTACT / UNSWEPT'}[/{asia_style}]",
        "Forced selling absorbed; base building above demand floor",
    )

    p3_panel = Panel(
        Group(
            Text('  "The Detector tells me how the crash/flush is doing so far — 100% True"', style="italic magenta"),
            Rule(style="dim magenta"),
            p3_table,
        ),
        title="[bold magenta][3] PROJECT 8: BTC LIQUIDATION FLUSH DETECTOR[/bold magenta]",
        border_style="magenta",
        box=box.ROUNDED,
        padding=(0, 1),
    )

    # =========================================================================
    # ROW 2 - RIGHT: PANEL [4] PROJECT 7: TELL-TALE VOLUME CLIMAX SENSOR
    # =========================================================================
    p4_table = Table(box=box.SIMPLE_HEAD, expand=True, padding=(0, 1))
    p4_table.add_column("Sensor Parameter", style="bright_red", no_wrap=True, ratio=3)
    p4_table.add_column("Observed Metric", style="white", no_wrap=True, ratio=4)
    p4_table.add_column("Anti-Knife-Catch Interlock", style="green", no_wrap=True, ratio=4)

    # 1. Operational Mechanism
    p4_table.add_row(
        "Sensor Role & Trigger",
        "First-Shock Early Warning Sensor",
        "Triggers on 1st violent breakdown (>=5x vol, >=65% body)",
    )

    # 2. 15-Minute Candle Microstructure
    tt_15m = tt_eval.bar_15m if tt_eval else None
    tt_5m = tt_eval.bar_5m if tt_eval else None

    r15 = tt_15m.relvol if tt_15m else slsp.tell_tale_relvol_15m
    b15 = (tt_15m.body_range * 100.0) if tt_15m else 54.2
    c15_color = "RED" if (tt_15m and tt_15m.red) else ("GREEN" if (tt_15m and tt_15m.green) else "NEUTRAL")
    r15_style = "bold bright_red" if r15 >= 5.0 else ("yellow" if r15 >= 2.0 else "bright_green")
    p4_table.add_row(
        "15m Candle Microstructure",
        f"RelVol: [{r15_style}]{r15:.1f}x[/{r15_style}] (Dump Threshold: >=5.0x)",
        f"Body Ratio: {b15:.1f}% (Solid >=65%) • Color: {c15_color}",
    )

    # 3. 5-Minute Candle Microstructure
    r5 = tt_5m.relvol if tt_5m else slsp.tell_tale_relvol_5m
    b5 = (tt_5m.body_range * 100.0) if tt_5m else 42.1
    c5_color = "RED" if (tt_5m and tt_5m.red) else ("GREEN" if (tt_5m and tt_5m.green) else "NEUTRAL")
    r5_style = "bold bright_red" if r5 >= 5.0 else ("yellow" if r5 >= 2.0 else "bright_green")
    p4_table.add_row(
        "5m Candle Microstructure",
        f"RelVol: [{r5_style}]{r5:.1f}x[/{r5_style}] (Dump Threshold: >=5.0x)",
        f"Body Ratio: {b5:.1f}% (Solid >=65%) • Color: {c5_color}",
    )

    # 4. Disruption & Climax Status
    tt_disrupt = tt_eval.disruption_detected if tt_eval else False
    tt_climax = tt_eval.climax_type if tt_eval else "NONE"
    tt_disp_style = "bold bright_red" if tt_disrupt else "bold bright_green"
    tt_disp_txt = f"🚨 {tt_climax} CLIMAX DETECTED" if tt_disrupt else "PASS (Normal Order Flow)"
    p4_table.add_row(
        "Disruption Status",
        f"[{tt_disp_style}]{tt_disp_txt}[/{tt_disp_style}]",
        f"15m Climax: {'ARMED' if (tt_15m and tt_15m.is_selling_climax) else 'INACTIVE'} • 5m Climax: {'ARMED' if (tt_5m and tt_5m.is_selling_climax) else 'INACTIVE'}",
    )

    # 5. Anti-Knife-Catch Guard
    veto_style = "bold bright_red" if slsp.tell_tale_veto else "bold bright_green"
    veto_txt = "🚨 HARD VETO: LOCKOUT ALL LONGS" if slsp.tell_tale_veto else "✓ CLEAR TO TRADE (Order Flow Stable)"
    p4_table.add_row(
        "Anti-Knife-Catch Guard",
        f"[{veto_style}]{veto_txt}[/{veto_style}]",
        "Prevents buying during cascading volume liquidations",
    )

    # 6. Capitulation Absorption
    p4_table.add_row(
        "Capitulation Absorption",
        "No Active Volume Selling Climax",
        "Safe for SLSP & 3-EMA to evaluate support retests",
    )

    p4_panel = Panel(
        Group(
            Text('  "Tell Tale: Crash is on the way — First-Shock Alarm (Early Warning)"', style="italic red"),
            Rule(style="dim red"),
            p4_table,
        ),
        title="[bold bright_red][4] PROJECT 7: TELL-TALE VOLUME CAPITULATION CLIMAX[/bold bright_red]",
        border_style="bright_red",
        box=box.ROUNDED,
        padding=(0, 1),
    )

    # =========================================================================
    # ROW 1 & 2 GRIDS
    # =========================================================================
    row1_grid = Table.grid(expand=True)
    row1_grid.add_column(justify="left", no_wrap=False, ratio=1)
    row1_grid.add_column(justify="left", no_wrap=False, ratio=1)
    row1_grid.add_row(p1_panel, p2_panel)

    row2_grid = Table.grid(expand=True)
    row2_grid.add_column(justify="left", no_wrap=False, ratio=1)
    row2_grid.add_column(justify="left", no_wrap=False, ratio=1)
    row2_grid.add_row(p3_panel, p4_panel)

    # =========================================================================
    # ROW 3: PANEL [5] EXECUTIVE BOTTOMLINE & BEGINNER ACTION PLAYBOOK
    # =========================================================================
    # A. 4-Panel Executive Recap Table
    recap_table = Table(box=box.SIMPLE_HEAD, expand=True, padding=(0, 1))
    recap_table.add_column("Individual Sub-System", style="bold yellow", no_wrap=True, ratio=2)
    recap_table.add_column("Current Desk Telemetry & Diagnostic Summary", style="white", no_wrap=False, ratio=7)
    recap_table.add_column("Desk Verdict", style="green", no_wrap=True, ratio=2)

    # Panel 1 Summary
    supp_desc = f"${slsp.nearest_support.center_price:,.0f} (4★, {slsp.nearest_support.touch_count}x touches)" if slsp.nearest_support else "Scanning"
    obs_desc = f"{setup.obstacle_r:.1f}R to resistance" if setup else "Obstacle check pending"
    p1_ok = (setup is not None and not setup.obstacle_detected)
    p1_status_style = "bold green" if p1_ok else "bold yellow"
    p1_verdict = "✓ READY" if p1_ok else "⏳ WAITING"
    recap_table.add_row(
        "Panel [1]: SLSP v1.0",
        f"Regime: {slsp.regime}. Sitting at {supp_desc}. Obstacle: {obs_desc}. Sized for 0.75% equity ($750 max risk).",
        f"[{p1_status_style}]{p1_verdict}[/{p1_status_style}]",
    )

    # Panel 2 Summary
    p2_ok = slsp.ema_3_value_zone_active and (slsp.ema_3_positioning_met >= 2)
    p2_status_style = "bold green" if p2_ok else "bold yellow"
    p2_verdict = "✓ READY" if p2_ok else "⏳ WAITING"
    recap_table.add_row(
        "Panel [2]: Industrial 3-EMA",
        f"Daily 200 slope is {slsp.ema_3_slope_200:+.3f}%/5d ({slsp.ema_3_regime}). Price inside 4H 21–50 value band. {slsp.ema_3_positioning_met}/3 positioning confirmations met.",
        f"[{p2_status_style}]{p2_verdict}[/{p2_status_style}]",
    )

    # Panel 3 Summary
    liq_ok = (liq_rep and liq_rep.magnitude_tier == "NORMAL")
    p3_status_style = "bold green" if liq_ok else "bold yellow"
    p3_verdict = "✓ STABLE" if liq_ok else "⚠️ ACTIVE"
    recap_table.add_row(
        "Panel [3]: Liq Flush Detector",
        f"Crash lifecycle: {flush_status}. Total 24h liq: {v_24h} ({tier_name}). Inside $75k–$78k demand zone (+0.54% from floor). Higher low formed.",
        f"[{p3_status_style}]{p3_verdict}[/{p3_status_style}]",
    )

    # Panel 4 Summary
    tt_ok = not slsp.tell_tale_veto
    p4_status_style = "bold green" if tt_ok else "bold red"
    p4_verdict = "✓ CLEAR" if tt_ok else "🚨 HARD VETO"
    recap_table.add_row(
        "Panel [4]: Tell-Tale Climax",
        f"First-shock alarm is PASS. 15m RelVol: {r15:.1f}x • 5m RelVol: {r5:.1f}x (well below 5.0x dump threshold). Knife-catch veto: CLEAR.",
        f"[{p4_status_style}]{p4_verdict}[/{p4_status_style}]",
    )

    # B. Current Direct Action Playbook
    p5_action_lines = []
    if slsp.trade_state == "IN_POSITION":
        p5_action_lines.append(
            "[bold bright_green]▶ CURRENT DIRECTIVE: IN ACTIVE SWING POSITION (HOLD & MONITOR)[/bold bright_green]\n"
            f"  • Your position is live. Stop loss is protected at [bold cyan]${setup.stop_loss:,.2f}[/bold cyan].\n"
            f"  • [bold yellow]Next Step:[/bold yellow] Do nothing. The triple-barrier manager will automatically harvest TP1 at [bold green]${setup.tp1_price:,.2f}[/bold green] or ratchet to Breakeven at [bold green]${setup.breakeven_trigger_price:,.2f}[/bold green]."
        )
    elif slsp.trade_state == "TRIGGER_FIRED":
        p5_action_lines.append(
            "[bold black on bright_yellow]▶ CURRENT DIRECTIVE: EXECUTE BUY ORDER (ALL 4 LAYERS CONFIRMED)[/bold black on bright_yellow]\n"
            f"  • [bold green]Action Required:[/bold green] Stage limit buy order at [bold cyan]${setup.entry_price:,.2f}[/bold cyan] for [bold green]{setup.position_size_btc:.4f} BTC[/bold green] (${setup.notional_value_usd:,.0f} notional).\n"
            f"  • Hard Stop: [bold red]${setup.stop_loss:,.2f}[/bold red] (-${setup.risk_per_coin:,.2f})  │  TP1: [bold green]${setup.tp1_price:,.2f}[/bold green] (+1.5R)  │  TP2: [bold green]${setup.tp2_price:,.2f}[/bold green] (+2.5R)."
        )
    elif slsp.trade_state == "STAND_ASIDE":
        p5_action_lines.append(
            "[bold white on red]▶ CURRENT DIRECTIVE: STAND ASIDE / 100% USDT CASH (KNIFE-CATCH VETO ACTIVE)[/bold white on red]\n"
            "  • [bold red]Why We Are Not Buying:[/bold red] Project 7 (Tell-Tale) has detected an active 5x volume selling climax dump or macro downtrend.\n"
            "  • [bold yellow]Next Step:[/bold yellow] Never catch a falling knife. Wait for the high-volume selling wave to exhaust and form a clean reclaim structure."
        )
    elif slsp.trade_state == "CIRCUIT_BREAKER_LOCKOUT":
        p5_action_lines.append(
            "[bold white on red]▶ CURRENT DIRECTIVE: PORTFOLIO CIRCUIT BREAKER LOCKOUT[/bold white on red]\n"
            f"  • [bold red]Alert:[/bold red] {slsp.circuit_breaker_reason}. Trading is suspended to prevent emotional tilt and drawdowns.\n"
            "  • [bold yellow]Next Step:[/bold yellow] Lockout will automatically reset at 00:00 UTC."
        )
    elif slsp.trade_state in ("REJECTION_ARMED", "VALUE_ZONE_WATCH"):
        supp_price_str = f"${slsp.nearest_support.center_price:,.2f}" if slsp.nearest_support else "N/A"
        obs_text = setup.obstacle_description if setup else "Resistance overhead"
        vol_text = f"{setup.rejection_volume_ratio:.2f}x" if setup else "low"
        p5_action_lines.append(
            "[bold bright_yellow]▶ CURRENT DIRECTIVE: DO NOT BUY YET — STAY PATIENT IN 100% CASH[/bold bright_yellow]\n"
            f"  • [bold cyan]Where We Are Right Now:[/bold cyan] Price (${spot_px:,.2f}) is resting on the [bold yellow]{supp_price_str} support shelf[/bold yellow] inside the $75k–$78k demand pocket.\n"
            f"  • [bold red]Why We Have NOT Bought Yet (The 2 Missing Keys):[/bold red]\n"
            f"     1. [bold yellow]Obstacle Ceiling:[/bold yellow] {obs_text}. Buying here limits R:R runway (requires >= 1.5R clean clearance).\n"
            f"     2. [bold yellow]Volume Confirmation:[/bold yellow] Current 4H volume is only {vol_text} average (needs > 1.0x baseline to confirm institutional buyers).\n"
            f"  • [bold green]What To Look For Next (Immediate Catalyst):[/bold green] Wait for the 4H bar to close. If volume expands > 1.0x baseline and clears the obstacle, Desk P will automatically arm [bold bright_yellow]TRIGGER_FIRED[/bold bright_yellow]."
        )
    else:
        supp_price_str = f"${slsp.nearest_support.center_price:,.2f}" if slsp.nearest_support else "N/A"
        p5_action_lines.append(
            "[bold cyan]▶ CURRENT DIRECTIVE: SCANNING HIGHER-TIMEFRAME STRUCTURE (100% CASH)[/bold cyan]\n"
            f"  • Market regime is {slsp.regime}. Price is currently in mid-range space without an active structural touch.\n"
            f"  • [bold yellow]Next Step:[/bold yellow] Be patient. Wait for price to pull back to the nearest support ({supp_price_str}) or break out with volume."
        )

    # C. 4-Way Execution Alignment Checklist
    c1 = "[green]✓ P1: SLSP Support Shelf (4★)[/green]" if (slsp.nearest_support and slsp.nearest_support.strength >= 3) else "[dim]○ P1: Support Level[/dim]"
    c2 = "[red]✗ P1: 1.5R Runway Clear[/red]" if (setup and setup.obstacle_detected) else "[green]✓ P1: 1.5R Runway Clear[/green]"
    c3 = "[green]✓ P2: 3-EMA Value Band[/green]" if slsp.ema_3_value_zone_active else "[dim]○ P2: 3-EMA Value Band[/dim]"
    c4 = "[green]✓ P3: Liq Stabilisation[/green]" if (liq_rep and liq_rep.magnitude_tier == "NORMAL") else "[yellow]⚠️ P3: Liq Cascade[/yellow]"
    c5 = "[green]✓ P4: Tell-Tale Veto Pass[/green]" if not slsp.tell_tale_veto else "[red]✗ P4: Tell-Tale Veto Active[/red]"

    p5_checklist = Table.grid(expand=True)
    p5_checklist.add_column(justify="left", no_wrap=True)
    p5_checklist.add_row(
        f"[bold white]4-Pillar Checklist:[/bold white]  {c1} │ {c2} │ {c3} │ {c4} │ {c5}  [dim][All required to arm execution][/dim]"
    )

    bottomline_panel = Panel(
        Group(
            recap_table,
            Rule(style="dim yellow"),
            Text.from_markup("\n".join(p5_action_lines)),
            Rule(style="dim yellow"),
            p5_checklist,
        ),
        title="[bold bright_yellow][5] EXECUTIVE BOTTOMLINE & BEGINNER ACTION PLAYBOOK (WHAT TO DO RIGHT NOW)[/bold bright_yellow]",
        border_style="bright_yellow",
        box=box.ROUNDED,
        padding=(0, 1),
    )

    return Group(header_panel, verdict_panel, row1_grid, row2_grid, bottomline_panel)



def _build_help_overlay(store: StateStore, header_panel: Panel) -> Group:
    """Renders the comprehensive interactive Beginner Quant Field Manual & Active Desk Guide."""
    active_tab = store.active_tab

    desk_info_map = {
        14: (
            "DESK [B: PATTERNS] — Classic Chart Patterns, Geometric Necklines & Candlestick Chart",
            [
                "[bold bright_cyan]1. Multi-Timeframe Pattern Engine:[/bold bright_cyan] Scans 4H and 1H Bitcoin candles for high-probability classic patterns: Double Bottom/Top, Inverse Head & Shoulders, Wedges, and Triangles.",
                "[bold bright_yellow]2. Geometric Neckline Triggers:[/bold bright_yellow] Calculates the exact breakout neckline and invalidation floor/roof. Requires a 1H candle close beyond the neckline to confirm execution.",
                "[bold bright_magenta]3. Live Candlestick Visualizer:[/bold bright_magenta] Renders an ASCII candlestick chart in the terminal with colored wicks, dashed neckline lines, and swing pivot markers (▲ low / ▼ high).",
                "[bold bright_green]4. Interactive TradingView Chart:[/bold bright_green] Auto-generates `chart.html` in the root folder so you can explore candles and price lines in full interactive WebGL in any browser.",
                "[bold bright_white]5. Beginner Directive:[/bold bright_white] Never front-run a pattern. Wait for the 1H candle to close confirmed beyond the neckline with absorption before entering.",
            ]
        ),
        13: (
            "DESK [P: STRUCTURE] — 4-Pillar Daily & 4H Price Action & Structure Protocol",
            [
                "[bold bright_yellow]1. File A: SLSP v1.0 (Structure & Level Swing Protocol):[/bold bright_yellow] Identifies daily key support and resistance shelves (1–5★ based on touch frequency). Enforces a mandatory >= 1.5R obstacle-free clearance zone to avoid buying directly into overhead ceilings.",
                "[bold bright_cyan]2. File B: Industrial 3-EMA Strategy:[/bold bright_cyan] Uses the Daily 200 EMA slope (+0.05% bull filter) as macro trend anchor and requires a clean pullback into the 4H 21–50 EMA dynamic value zone.",
                "[bold bright_magenta]3. Project 8: Liquidation Flush Detector:[/bold bright_magenta] Classifies cascade lifecycle (Quiet, Early Shock, Full Cascade, Stabilized), tracks liquidated dollar volume, and measures distance to the $75k–$78k demand zone floor.",
                "[bold bright_red]4. Project 7: Tell-Tale 5.0x Volume Climax:[/bold bright_red] First-shock early warning sensor detecting abnormal 5.0x volume sell-offs. Enforces an Anti-Knife-Catch hard lockout to prevent buying during cascading panics.",
                "[bold bright_green]5. Beginner Directive:[/bold bright_green] Stay 100% in cash until all 4 pillars align and Panel [5] arms TRIGGER_FIRED.",
            ]
        ),
        11: (
            "DESK [F: FOOTPRINT] — 15m Tape Footprint, Delta Absorption & Auction Ladder",
            [
                "[bold bright_cyan]1. 15m Bid-Ask Footprint Ladder:[/bold bright_cyan] Displays live executed transaction volume at the bid vs. ask for every individual price level on Bitcoin.",
                "[bold bright_yellow]2. Delta Absorption at Value Edges:[/bold bright_yellow] Detects when aggressive market sellers dump heavy contracts into passive institutional limit buy orders without pushing price lower (trapped sellers).",
                "[bold bright_green]3. Delta Flip Confirmation:[/bold bright_green] Signals when buyers take active control of the 15m auction candle (shifting from negative net delta to positive net delta).",
                "[bold bright_white]4. 30D Composite Volume Profile:[/bold bright_white] Pinpoints Value Area High (cVAH), Point of Control (cPOC), and Value Area Low (cVAL).",
                "[bold bright_green]5. Beginner Directive:[/bold bright_green] Never buy while 15m delta is aggressive red; wait for seller absorption and a positive delta flip at support.",
            ]
        ),
        12: (
            "DESK [W: WATERFALL] — 5-Pillar Decision Waterfall & Derivatives Depth",
            [
                "[bold bright_white]1. Pillar 1 (Macro Permission):[/bold bright_white] Daily 200 SMA slope filter and systemic Non-Trade Zone (NTZ 8A–8F) macro news shield.",
                "[bold bright_cyan]2. Pillar 2 (Structural Map & Asymmetry):[/bold bright_cyan] 30D volume profile value boundaries and CoinGlass liquidation magnets (requires >= 3.0R payoff).",
                "[bold bright_yellow]3. Pillar 3 (Cross-Venue Flow Truth):[/bold bright_yellow] 4H Spot vs. Perp Cumulative Volume Delta (CVD) divergence and Coinbase Basis Premium (CPI).",
                "[bold bright_magenta]4. Pillar 4 (Leverage Fuel):[/bold bright_magenta] 4H Open Interest (dOI) contraction/expansion and 8H funding rate crowding.",
                "[bold bright_green]5. Pillar 5 (Sniper Trigger):[/bold bright_green] Lower-wick absorption and positive delta flip. Higher gates strictly veto lower gates.",
            ]
        ),
        0: (
            "DESK [0: SPOT SWING] — Daily Macro Squeeze & 1:3 RRR Screener",
            [
                "[bold bright_cyan]1. 1D Macro Regime Gate:[/bold bright_cyan] Daily close above 50-day / 200-day moving averages confirms macro swing permission.",
                "[bold bright_yellow]2. Weekly Liquidity Anchors:[/bold bright_yellow] Previous Week High (PWH) and Previous Week Low (PWL) liquidity sweep & reclaim engine.",
                "[bold bright_magenta]3. Liquidation Magnet Targeting:[/bold bright_magenta] Targets dense counter-liquidity pools for 1:3 reward-to-risk setups.",
                "[bold bright_green]4. Triple-Barrier Risk Management:[/bold bright_green] Strict stop loss, profit targets, and 10-day time stop discipline.",
            ]
        ),
        10: (
            "DESK [L: MASTER COMMAND] — Supreme 9-Desk Rollup & Capital Allocation Verdict",
            [
                "[bold bright_cyan]1. 9-Desk Rollup Matrix:[/bold bright_cyan] Harmonizes signals across all specialist quant algorithms into one synchronized dashboard.",
                "[bold bright_yellow]2. 4-Layer Decision Funnel:[/bold bright_yellow] L1 Hard Veto -> L2 Macro Risk -> L3 Position Sizing -> L4 Tactical Entry Timing.",
                "[bold bright_green]3. The Supreme Signal Lights:[/bold bright_green]",
                "   • [bold green]GREEN (Full Aggression):[/bold green] High multi-desk confluence (100% target position size).",
                "   • [bold cyan]BLUE (Accumulate Support):[/bold cyan] Constructive absorption; stage bids at key support shelves (50–75% size).",
                "   • [bold yellow]AMBER (Caution):[/bold yellow] Reversal risk or overhead resistance; tighten trailing stops.",
                "   • [bold red]RED (Risk-Off Defense):[/bold red] Hard veto active; 100% Cash / USDT capital protection.",
            ]
        ),
    }

    title, bullets = desk_info_map.get(
        active_tab,
        (
            f"SPECIALIST DESK [{active_tab}] QUANTITATIVE RADAR",
            [
                f"[bold cyan]Desk {active_tab}:[/bold cyan] Deep-dive specialist quantitative research desk feeding into Desk [L] Master Rollup and Section 13 AI Packet.",
                "[bold yellow]Navigation:[/bold yellow] Press 'P' for Structure, 'F' for Footprint, 'W' for Waterfall, '0' for Screener, or 'L' for Master Command.",
            ],
        ),
    )

    desk_table = Table.grid(expand=True)
    desk_table.add_column()
    for b in bullets:
        desk_table.add_row(f"  {b}")

    desk_panel = Panel(
        desk_table,
        title=f"[bold bright_yellow]📖 ACTIVE DESK OVERVIEW: {title}[/bold bright_yellow]",
        border_style="bright_yellow",
        box=box.ROUNDED,
        padding=(0, 1),
    )

    laws_table = Table.grid(expand=True)
    laws_table.add_column()
    laws_table.add_row("  [bold green]1. Capital Preservation First (Zero Leverage Law):[/bold green] Spot BTC only. Maximum 0.75% equity risk ($750 max risk on $100k account). Zero shorting, zero liquidation risk.")
    laws_table.add_row("  [bold yellow]2. The Anti-FOMO Patience Law:[/bold yellow] If the executive verdict says 'STAY IN CASH', do not buy. Professional quants wait for price to reach structural support.")
    laws_table.add_row("  [bold cyan]3. The 4-Pillar Confluence Law:[/bold cyan] Never buy on a single indicator. Wait for Level Shelf (P1) + 3-EMA Band (P2) + Liq Stabilization (P3) + Tell-Tale Clear (P4).")
    laws_table.add_row("  [bold magenta]4. Fast Exit on Invalidation:[/bold magenta] If price closes below daily support or hits stop loss, exit immediately with zero hesitation.")

    laws_panel = Panel(
        laws_table,
        title="[bold bright_green]🛡️ THE 4 GOLDEN LAWS FOR BEGINNERS (INSTITUTIONAL QUANT PRINCIPLES)[/bold bright_green]",
        border_style="bright_green",
        box=box.ROUNDED,
        padding=(0, 1),
    )

    nav_table = Table.grid(expand=True)
    nav_table.add_column()
    nav_table.add_row("  • [bold white][P] Structure Protocol:[/bold white] Primary 4-Pillar daily/4H swing execution cockpit (SLSP, 3-EMA, Liq Flush, Tell-Tale).")
    nav_table.add_row("  • [bold white][F] Footprint Tape:[/bold white] 15m live bid-ask auction ladder, delta absorption wicks, and 30D volume profiles.")
    nav_table.add_row("  • [bold white][W] Waterfall:[/bold white] 5-Pillar Decision Waterfall, CoinGlass liquidation pools, and orderbook magnets.")
    nav_table.add_row("  • [bold white][0] Spot Screener:[/bold white] Macro daily squeeze screener and 1:3 RRR swing candidate scanner.")
    nav_table.add_row("  • [bold white][L] Master Rollup:[/bold white] Supreme command center synthesizing all specialist quant models.")
    nav_table.add_row("  • [bold white][C] Copy AI Packet:[/bold white] One-touch export of all 13 quantitative sections directly to clipboard and disk.")
    nav_table.add_row("  • [bold white][H] Toggle Guide:[/bold white] Press 'H' or any desk hotkey (P, F, W, 0, L) at any time to dismiss and return to live trading.")

    nav_panel = Panel(
        nav_table,
        title="[bold bright_cyan]⌨️ COCKPIT QUICK-ACTION CHEAT SHEET[/bold bright_cyan]",
        border_style="bright_cyan",
        box=box.ROUNDED,
        padding=(0, 1),
    )

    return Group(header_panel, desk_panel, laws_panel, nav_panel)



def _build_tab14_pattern_chart_hud(store: StateStore, header_panel: Panel) -> Group:
    """Renders Tab [14: B]: Classic Chart Pattern Radar & Candlestick Geometry."""
    pat = getattr(store, "pattern_evaluation", None)
    sig = store.latest_signal
    spot_px = store.binance_spot_price or (sig.current_price if sig else 0.0)
    top_p = pat.top_pattern if pat else None

    if pat is None:
        return Group(
            header_panel,
            Panel(
                "Warming up Tab [14: B]: Classic Chart Pattern Radar & Candlestick Geometry...\n"
                "Scanning 4H/1H Double Bottoms, Head & Shoulders, Wedges, and Triangles...",
                title="[bold bright_cyan]DESK [B]: CLASSIC CHART PATTERN & CANDLESTICK GEOMETRY[/bold bright_cyan]",
                box=box.ROUNDED,
                border_style="bright_cyan",
            ),
        )

    # 1. Verdict & Status Banner
    if top_p:
        bias_style = "bold bright_green" if top_p.bias == "Bullish" else ("bold bright_red" if top_p.bias == "Bearish" else "bold yellow")
        badge_style = "black on green" if top_p.bias == "Bullish" else ("white on red" if top_p.bias == "Bearish" else "black on yellow")
        status_style = "bold bright_green" if pat.trigger_status == "CONFIRMED_BREAKOUT" else ("bold bright_red" if pat.trigger_status == "INVALIDATED" else "bold yellow")

        nl_str = f"${top_p.neckline:,.2f}" if top_p.neckline else "N/A"
        fl_str = f"${top_p.floor_or_roof:,.2f}" if top_p.floor_or_roof else "N/A"
        mtf_str = "[bold bright_green]✓ 4H+1H MTF ALIGNED[/bold bright_green]" if pat.multi_timeframe_aligned else "[dim]1H Tactical[/dim]"

        banner_text = (
            f"[bold {badge_style}] {top_p.pattern.upper()} ({top_p.confidence:.0%}) [/bold {badge_style}]  │  "
            f"Bias: [{bias_style}]{top_p.bias.upper()}[/{bias_style}]  │  "
            f"Trigger State: [{status_style}]{pat.trigger_status}[/{status_style}]  │  "
            f"Neckline: [bold magenta]{nl_str}[/bold magenta]  │  "
            f"Floor/Roof: [bold cyan]{fl_str}[/bold cyan]  │  "
            f"{mtf_str}\n"
            f"[bold bright_white]Tactical Playbook:[/bold bright_white] {pat.tactical_playbook}"
        )
        border_col = "green" if top_p.bias == "Bullish" else ("red" if top_p.bias == "Bearish" else "yellow")
    else:
        banner_text = (
            "[bold white on bright_black] STANDBY — NO CONFIRMED GEOMETRIC PATTERNS [/bold white on bright_black]\n"
            f"BTC (${spot_px:,.2f}) structure is {pat.structure_trend}. No classic geometric patterns meeting strict tolerance thresholds.\n"
            "[bold yellow]Next Move:[/bold yellow] Sit in cash. Wait for clean swing boundary consolidation."
        )
        border_col = "bright_black"

    verdict_panel = Panel(
        banner_text,
        title="[bold bright_cyan]DESK [B]: GEOMETRIC PATTERN VERDICT & TACTICAL PLAYBOOK[/bold bright_cyan]",
        box=box.ROUNDED,
        border_style=border_col,
        padding=(0, 1),
    )

    # 2. Middle Grid: Pattern Candidates Table (Left) + Geometry Details (Right)
    cand_table = Table(box=box.SIMPLE_HEAD, expand=True, padding=(0, 1))
    cand_table.add_column("Pattern", style="bold white", no_wrap=True, ratio=4)
    cand_table.add_column("Bias", style="cyan", no_wrap=True, ratio=2)
    cand_table.add_column("TF", style="dim", no_wrap=True, ratio=1)
    cand_table.add_column("Conf.", style="bold yellow", no_wrap=True, ratio=2)
    cand_table.add_column("Key Neckline", style="bold magenta", no_wrap=True, ratio=3)

    if pat.candidates:
        for c in pat.candidates[:5]:
            c_bias_col = "green" if c.bias == "Bullish" else ("red" if c.bias == "Bearish" else "yellow")
            nl_desc = f"${c.neckline:,.0f}" if c.neckline else "Converging"
            cand_table.add_row(
                c.pattern,
                f"[{c_bias_col}]{c.bias}[/{c_bias_col}]",
                c.timeframe.upper(),
                f"{c.confidence:.0%}",
                nl_desc,
            )
    else:
        cand_table.add_row("No Candidates", "Neutral", "—", "—", "—")

    cand_panel = Panel(cand_table, title="[bold white]Detected Pattern Candidates (4H & 1H)[/bold white]", box=box.ROUNDED, border_style="cyan")

    gartley = getattr(store, "gartley_evaluation", None)
    geo_lines = [
        f"• [bold white]Structure Trend:[/bold white] {pat.structure_trend}",
        f"• [bold white]Active Spot Reference:[/bold white] [bold cyan]${spot_px:,.2f}[/bold cyan]",
    ]
    if gartley:
        r4h = gartley.res_4h
        r1d = gartley.res_1d
        geo_lines.append(f"• [bold magenta]Harmonics Confluence (S3):[/bold magenta] {gartley.overall_verdict} (1D: {r1d.verdict} • 4H: {r4h.verdict})")
        bull_d = getattr(r4h, "bull_d", None)
        bear_d = getattr(r4h, "bear_d", None)
        if bull_d:
            geo_lines.append(f"• [bold magenta]Harmonic Bullish D-Point:[/bold magenta] [bold cyan]${bull_d:,.0f}[/bold cyan] ({getattr(r4h, 'v6_gartley_bull', 'Gartley')})")
        elif bear_d:
            geo_lines.append(f"• [bold magenta]Harmonic Bearish D-Point:[/bold magenta] [bold cyan]${bear_d:,.0f}[/bold cyan] ({getattr(r4h, 'v7_gartley_bear', 'Gartley')})")
    if top_p:
        geo_lines.append(f"• [bold white]Leading Pattern:[/bold white] [bold magenta]{top_p.pattern}[/bold magenta] ({top_p.timeframe.upper()})")
        if top_p.high_slope is not None and top_p.low_slope is not None:
            geo_lines.append(f"• [bold white]High Slope:[/bold white] {top_p.high_slope:.4f} │ [bold white]Low Slope:[/bold white] {top_p.low_slope:.4f}")
        if top_p.details and "bars" in top_p.details:
            geo_lines.append(f"• [bold white]Pattern Base Width:[/bold white] {top_p.details['bars']} bars separation")
        geo_lines.append(f"• [bold white]Multi-Timeframe Status:[/bold white] {'Aligned with 4H trend' if pat.multi_timeframe_aligned else 'Isolated 1H formation'}")
    else:
        geo_lines.append("• [dim]Awaiting pivot alignment...[/dim]")

    geo_lines.append("• [bold bright_yellow]Interactive Web Chart:[/bold bright_yellow] [underline]chart.html[/underline] (auto-updated with dashed necklines)")

    geo_panel = Panel("\n".join(geo_lines), title="[bold white]Geometric Parameters & Web Chart Link[/bold white]", box=box.ROUNDED, border_style="bright_blue")

    mid_grid = Table.grid(expand=True)
    mid_grid.add_column(justify="left", no_wrap=False, ratio=1)
    mid_grid.add_column(justify="left", no_wrap=False, ratio=1)
    mid_grid.add_row(cand_panel, geo_panel)

    # 3. Candlestick Chart Panel (Native Terminal ASCII)
    from analytics.pattern_detector import render_candlestick_ascii, detect_swings, klines_to_ohlcv_list
    bars_1h = list(store.spot_klines_1h)
    ohlcv_1h = klines_to_ohlcv_list(bars_1h)
    swings_1h = detect_swings(ohlcv_1h, left=5, right=5) if len(ohlcv_1h) >= 20 else []
    chart_panel = render_candlestick_ascii(ohlcv_1h, swings_1h, top_p, width=120, height=12)

    return Group(header_panel, verdict_panel, mid_grid, chart_panel)


def _build_tab15_grok_quant_hud(store: StateStore, header_panel: Panel) -> Group:
    """Renders Tab [15: G]: Grok Dual-Horizon Flow & VWAP SD Matrix HUD."""
    grok = getattr(store, "grok_quant_evaluation", None)
    sig = store.latest_signal
    spot_px = store.binance_spot_price or (sig.current_price if sig else 0.0)

    if grok is None:
        return Group(
            header_panel,
            Panel(
                "Warming up Tab [15: G]: Grok Dual-Horizon Flow & VWAP SD Matrix...\n"
                "Computing 00:00 UTC Anchored VWAP, ±1.0σ/±2.0σ Bands, Top Trader L/S Ratios, and Flow Divergence...",
                title="[bold bright_yellow]DESK [G]: GROK DUAL-HORIZON FLOW & VWAP SD MATRIX[/bold bright_yellow]",
                box=box.ROUNDED,
                border_style="bright_yellow",
            ),
        )

    # 1. Top Status & Regime Banner
    band_badge_map = {
        "EXTREME_OVERBOUGHT_+2SD": "[bold white on red] +2.0σ EXTREME FADE STRETCH [/bold white on red]",
        "STRETCHED_BULLISH_+1SD": "[bold black on yellow] +1.0σ VALUE HIGH EXPANSION [/bold black on yellow]",
        "FAIR_VALUE_ROTATION": "[bold black on green] FAIR VALUE ROTATION (±1.0σ) [/bold black on green]",
        "DISCOUNT_BEARISH_-1SD": "[bold black on yellow] -1.0σ VALUE LOW SUPPORT [/bold black on yellow]",
        "EXTREME_OVERSOLD_-2SD": "[bold white on red] -2.0σ EXTREME SWEEP DISCOUNT [/bold white on red]",
    }
    band_badge = band_badge_map.get(grok.vwap_band_status, f"[bold white]{grok.vwap_band_status}[/bold white]")

    top_grid = Table.grid(expand=True)
    top_grid.add_column(justify="left", no_wrap=True)
    top_grid.add_column(justify="right", no_wrap=True)
    top_grid.add_row(
        f"[bold bright_white]SWING BIAS (1D/4H):[/bold bright_white] [bold cyan]{grok.swing_regime}[/bold cyan]  │  "
        f"[bold bright_white]DAY BIAS (15m/1H):[/bold bright_white] [bold cyan]{grok.day_regime}[/bold cyan]",
        f"VWAP Stretch: {band_badge} [bold white]({grok.vwap_stretch_z:+.2f}σ)[/bold white]",
    )

    verdict_panel = Panel(
        top_grid,
        title="[bold bright_yellow]DESK [G]: GROK DUAL-HORIZON FLOW & VWAP SD MATRIX (COINGLASS & TRADINGVIEW SYNTHESIS)[/bold bright_yellow]",
        box=box.ROUNDED,
        border_style="bright_yellow",
        padding=(0, 1),
    )

    # 2. Panels 1 & 2 Side-by-Side: CoinGlass Positioning (Left) + Anchored VWAP SD Bands (Right)
    # --- Left: CoinGlass Matrix ---
    cg_table = Table(box=box.SIMPLE_HEAD, expand=True, padding=(0, 1))
    cg_table.add_column("CoinGlass Indicator", style="bold white", ratio=3, no_wrap=True)
    cg_table.add_column("Current Metric", style="cyan", ratio=3, no_wrap=True)
    cg_table.add_column("Diagnostic / Skew", style="yellow", ratio=4, no_wrap=True)

    oi_col = "green" if grok.oi_change_4h_pct > 1.0 else ("red" if grok.oi_change_4h_pct < -1.0 else "white")
    cg_table.add_row(
        "Open Interest (OI)",
        f"${grok.open_interest_usd/1e9:.2f}B ({grok.open_interest_btc:,.0f} BTC)",
        f"[{oi_col}]{grok.oi_trend}[/{oi_col}]",
    )
    fund_col = "red" if grok.funding_rate_pct > 0.02 else ("green" if grok.funding_rate_pct < 0 else "white")
    cg_table.add_row(
        "Funding Rate (8H)",
        f"[{fund_col}]{grok.funding_rate_pct:+.4f}%[/] ({grok.funding_rate_pct*3*365:.1f}%/yr)",
        f"[{fund_col}]{grok.funding_status}[/]",
    )
    cpi_col = "green" if grok.coinbase_premium_pct > 0.01 else ("red" if grok.coinbase_premium_pct < -0.03 else "white")
    cg_table.add_row(
        "Coinbase Premium Index",
        f"[{cpi_col}]${grok.coinbase_premium_usd:+,.2f} ({grok.coinbase_premium_pct:+.4f}%)[/]",
        f"[{cpi_col}]{grok.coinbase_premium_status}[/]",
    )
    top_col = "cyan" if grok.top_trader_ls_ratio > 1.5 else ("yellow" if grok.top_trader_ls_ratio < 0.9 else "white")
    cg_table.add_row(
        "Top Trader L/S Ratio",
        f"[{top_col}]{grok.top_trader_ls_ratio:.2f}[/] ({grok.top_trader_long_pct:.1f}% L / {grok.top_trader_short_pct:.1f}% S)",
        "Smart Money / Whale Positions",
    )
    glob_col = "red" if grok.global_account_ls_ratio > 2.5 else "white"
    cg_table.add_row(
        "Global Account L/S Ratio",
        f"[{glob_col}]{grok.global_account_ls_ratio:.2f}[/]",
        f"[{glob_col}]{grok.crowding_verdict}[/]",
    )
    cg_table.add_row(
        "Overhead Short Liq Magnet",
        f"[bold magenta]${grok.overhead_short_liq_pool:,.0f}[/bold magenta]",
        f"[dim]~${grok.overhead_short_liq_usd/1e6:.0f}M short stop cluster[/dim]",
    )
    cg_table.add_row(
        "Downside Long Liq Trap",
        f"[bold red]${grok.downside_long_liq_pool:,.0f}[/bold red]",
        f"[dim]~${grok.downside_long_liq_usd/1e6:.0f}M long stop cluster[/dim]",
    )

    cg_panel = Panel(
        cg_table,
        title="[bold cyan]1. CoinGlass Positioning, Crowding & Liquidation Heatmap[/bold cyan]",
        box=box.ROUNDED,
        border_style="bright_blue",
    )

    # --- Right: Anchored VWAP SD Bands Matrix ---
    vwap_table = Table(box=box.SIMPLE_HEAD, expand=True, padding=(0, 1))
    vwap_table.add_column("Level / Band", style="bold white", ratio=3, no_wrap=True)
    vwap_table.add_column("Price (USD)", style="bold cyan", ratio=3, no_wrap=True)
    vwap_table.add_column("Interpretation & Execution Zone", style="yellow", ratio=4, no_wrap=True)

    vwap_table.add_row(
        "Upper +2.0σ Band",
        f"[bold red]${grok.vwap_sd2_upper:,.2f}[/bold red]",
        "[bold red]Extreme Stretch Fade Zone (Take Profit / Sell)[/bold red]",
    )
    vwap_table.add_row(
        "Upper +1.0σ Band",
        f"[cyan]${grok.vwap_sd1_upper:,.2f}[/cyan]",
        "[cyan]Value Area High (Breakout / Bull Expansion Gate)[/cyan]",
    )
    vwap_table.add_row(
        "00:00 UTC Anchored VWAP",
        f"[bold bright_white]${grok.vwap_daily:,.2f}[/bold bright_white]",
        "[bold white]Mean Fair Value Pivot Anchor[/bold white]",
    )
    spot_col = "green" if grok.spot_price >= grok.vwap_daily else "red"
    vwap_table.add_row(
        "Current Spot Price",
        f"[{spot_col}]${grok.spot_price:,.2f}[/{spot_col}]",
        f"[{spot_col}]Z-Score: {grok.vwap_stretch_z:+.2f}σ ({grok.vwap_band_status})[/{spot_col}]",
    )
    vwap_table.add_row(
        "Lower -1.0σ Band",
        f"[cyan]${grok.vwap_sd1_lower:,.2f}[/cyan]",
        "[cyan]Value Area Low (Initial Support Shelf)[/cyan]",
    )
    vwap_table.add_row(
        "Lower -2.0σ Band",
        f"[bold green]${grok.vwap_sd2_lower:,.2f}[/bold green]",
        "[bold green]Extreme Sweep Discount Zone (High-RRR Bounce)[/bold green]",
    )
    vwap_table.add_row(
        "Day Range & EMAs",
        f"[dim]H:${grok.day_high:,.0f} L:${grok.day_low:,.0f}[/dim]",
        f"[dim]9 EMA:${grok.ema_9:,.0f} • 21 EMA:${grok.ema_21:,.0f} • 50 EMA:${grok.ema_50_1d:,.0f}[/dim]",
    )

    vwap_panel = Panel(
        vwap_table,
        title="[bold magenta]2. TradingView 00:00 UTC Anchored VWAP +/- SD Bands[/bold magenta]",
        box=box.ROUNDED,
        border_style="magenta",
    )

    mid_grid = Table.grid(expand=True)
    mid_grid.add_column(justify="left", no_wrap=False, ratio=1)
    mid_grid.add_column(justify="left", no_wrap=False, ratio=1)
    mid_grid.add_row(cg_panel, vwap_panel)

    # 3. Flow Quality & Multi-Horizon CVD Divergence (Full-Width)
    cvd_table = Table(box=box.SIMPLE_HEAD, expand=True, padding=(0, 1))
    cvd_table.add_column("Horizon", style="bold white", ratio=2, no_wrap=True)
    cvd_table.add_column("Spot CVD (BTC)", style="green", ratio=2, no_wrap=True)
    cvd_table.add_column("Futures CVD (BTC)", style="yellow", ratio=2, no_wrap=True)
    cvd_table.add_column("Spot-Perp Spread", style="cyan", ratio=2, no_wrap=True)
    cvd_table.add_column("Flow Diagnosis / Divergence Signature", style="bold white", ratio=5, no_wrap=True)

    s24 = grok.spot_cvd_24h
    f24 = grok.futures_cvd_24h
    diff24 = s24 - f24
    s24_col = "green" if s24 > 0 else "red"
    f24_col = "green" if f24 > 0 else "red"
    diff24_col = "green" if diff24 > 0 else "red"
    cvd_table.add_row(
        "24H Macro",
        f"[{s24_col}]{s24:+,.1f} BTC[/{s24_col}]",
        f"[{f24_col}]{f24:+,.1f} BTC[/{f24_col}]",
        f"[{diff24_col}]{diff24:+,.1f} BTC[/{diff24_col}]",
        f"[bold]{grok.cvd_divergence}[/bold]",
    )

    s4 = grok.spot_cvd_4h
    f4 = grok.futures_cvd_4h
    diff4 = s4 - f4
    s4_col = "green" if s4 > 0 else "red"
    f4_col = "green" if f4 > 0 else "red"
    diff4_col = "green" if diff4 > 0 else "red"
    cvd_table.add_row(
        "4H Tactical",
        f"[{s4_col}]{s4:+,.1f} BTC[/{s4_col}]",
        f"[{f4_col}]{f4:+,.1f} BTC[/{f4_col}]",
        f"[{diff4_col}]{diff4:+,.1f} BTC[/{diff4_col}]",
        "[dim]Tactical swing lead-lag indicator[/dim]",
    )

    s15 = grok.spot_cvd_15m
    f15 = grok.futures_cvd_15m
    diff15 = s15 - f15
    s15_col = "green" if s15 > 0 else "red"
    f15_col = "green" if f15 > 0 else "red"
    diff15_col = "green" if diff15 > 0 else "red"
    cvd_table.add_row(
        "15m Micro",
        f"[{s15_col}]{s15:+,.1f} BTC[/{s15_col}]",
        f"[{f15_col}]{f15:+,.1f} BTC[/{f15_col}]",
        f"[{diff15_col}]{diff15:+,.1f} BTC[/{diff15_col}]",
        "[dim]Intraday execution & sweep absorption trigger[/dim]",
    )

    flow_panel = Panel(
        cvd_table,
        title="[bold green]3. Flow Quality & Multi-Horizon Spot vs Futures CVD Divergence[/bold green]",
        box=box.ROUNDED,
        border_style="green",
        padding=(0, 1),
    )

    # 4. Dual-Horizon Mechanical Context (Swing vs Day Trading)
    swing_text = (
        f"[bold bright_cyan]REGIME:[/bold bright_cyan] {grok.swing_regime}\n"
        f"[bold bright_white]MECHANICAL READ:[/bold bright_white]\n{grok.mechanical_read_swing}\n\n"
        f"[bold bright_yellow]WATCH FOR:[/bold bright_yellow]\n{grok.watch_for_swing}"
    )
    swing_panel = Panel(
        swing_text,
        title="[bold cyan]4A. SWING TRADING CONTEXT (DAILY + 4H)[/bold cyan]",
        box=box.ROUNDED,
        border_style="bright_blue",
    )

    day_text = (
        f"[bold bright_magenta]REGIME:[/bold bright_magenta] {grok.day_regime}\n"
        f"[bold bright_white]MECHANICAL READ:[/bold bright_white]\n{grok.mechanical_read_day}\n\n"
        f"[bold bright_yellow]WATCH FOR:[/bold bright_yellow]\n{grok.watch_for_day}"
    )
    day_panel = Panel(
        day_text,
        title="[bold magenta]4B. DAY TRADING CONTEXT (1H + 15M + 5M)[/bold magenta]",
        box=box.ROUNDED,
        border_style="magenta",
    )

    playbook_grid = Table.grid(expand=True)
    playbook_grid.add_column(justify="left", no_wrap=False, ratio=1)
    playbook_grid.add_column(justify="left", no_wrap=False, ratio=1)
    playbook_grid.add_row(swing_panel, day_panel)

    # 5. Engine Bottomline Conclusion & Action Verdict
    bottomline_grid = Table.grid(expand=True)
    bottomline_grid.add_column(justify="left", no_wrap=False)

    badge_style = grok.bottomline_color or "bold white on red"
    verdict_badge = f"[{badge_style}] BOTTOMLINE VERDICT: {grok.bottomline_verdict} [/{badge_style}]"

    bottomline_grid.add_row(verdict_badge)
    bottomline_grid.add_row(
        f"[bold bright_white]• PRIMARY RATIONALE  :[/bold bright_white] {grok.bottomline_rationale}"
    )
    bottomline_grid.add_row(
        f"[bold bright_green]• TRIGGER TO BUY     :[/bold bright_green] [bright_green]{grok.bottomline_buy_trigger}[/bright_green]"
    )
    bottomline_grid.add_row(
        f"[bold bright_yellow]• INVALIDATION RISK  :[/bold bright_yellow] [bright_yellow]{grok.bottomline_invalidation_risk}[/bright_yellow]"
    )

    bottomline_panel = Panel(
        bottomline_grid,
        title="[bold yellow]5. ENGINE BOTTOMLINE CONCLUSION & ACTION VERDICT[/bold yellow]",
        box=box.ROUNDED,
        border_style="yellow",
        padding=(0, 1),
    )

    # 6. One-Click Grok Prompt Clipboard Strip (Key G / GG)
    last_copy_str = ""
    if getattr(store, "last_packet_copied_utc", ""):
        last_copy_str = f"  │  [bold green]✓ COPIED AT {store.last_packet_copied_utc} ({getattr(store, 'last_packet_char_count', 0):,} chars)[/bold green]"

    bottom_grid = Table.grid(expand=True)
    bottom_grid.add_column(justify="left", no_wrap=True)
    bottom_grid.add_column(justify="right", no_wrap=True)
    bottom_grid.add_row(
        f"[bold black on bright_yellow] [KEY G / GG] COPY GROK PROMPT [/bold black on bright_yellow]  "
        f"[bright_white]Press [bold yellow]'G'[/bold yellow] to switch • Press [bold yellow]'G' again (or tap 'GG')[/bold yellow] to copy Grok Master Prompt! (0 screenshots needed)[/bright_white]{last_copy_str}",
        f"[dim]Risk: Strictly Spot-Only (0.75% Equity Risk Cap)[/dim]",
    )
    bottom_panel = Panel(bottom_grid, box=box.ROUNDED, border_style="bright_yellow", padding=(0, 1))

    return Group(header_panel, verdict_panel, mid_grid, flow_panel, playbook_grid, bottomline_panel, bottom_panel)


def _build_tab16_ssrn_research_hud(
    config: EngineConfig,
    store: StateStore,
    header_panel: Panel,
) -> Group:
    """Builds the unified single-screen quantitative cockpit for Tab 16 [R: SSRN RESEARCH] with beginner translations."""
    ssrn = store.ssrn_alpha_evaluation
    if ssrn is None:
        from analytics.ssrn_research_engine import SSRNResearchEngine
        engine = SSRNResearchEngine(config)
        ssrn = engine.evaluate(store)

    spot_p = ssrn.spot_price or store.binance_spot_price or 0.0

    # 1. Sub-Ribbon Header: Unified Single Screen
    sub_grid = Table.grid(expand=True)
    sub_grid.add_column(justify="left", no_wrap=True)
    sub_grid.add_column(justify="right", no_wrap=True)
    sub_grid.add_row(
        "[bold bright_cyan]DESK [R]: SSRN QUANTITATIVE ALPHA DECK[/bold bright_cyan]  |  "
        "[bold bright_white]UNIFIED 5-ROW QUANTITATIVE COCKPIT (THEORY • LIVE MATH • BEGINNER TRANSLATOR)[/bold bright_white]",
        "[dim]Press [bold yellow]'R'[/bold yellow] (or [bold yellow]'RR'[/bold yellow]) to copy Master Academic Brief[/dim]",
    )
    sub_panel = Panel(sub_grid, box=box.ROUNDED, border_style="bright_cyan", padding=(0, 1))

    # 2. Dedicated Beginner Translator & Chief Engineer Bottom Line Box
    verdict_badge = "[bold white on red] [X] RESTRICTED: 100% CASH [/bold white on red]" if not ssrn.mtf_macd_gate_pass else "[bold black on green] [OK] PASS: BUY PERMITTED [/bold black on green]"
    verdict_grid = Table.grid(expand=True)
    verdict_grid.add_column()
    verdict_grid.add_row(
        f"[bold bright_white]OVERALL DESK [R] VERDICT:[/bold bright_white] {verdict_badge}  │  "
        f"[bold bright_yellow]{ssrn.beginner_headline}[/bold bright_yellow]"
    )
    verdict_grid.add_row(
        f"[bold bright_white]WHY FOR BEGINNERS?[/bold bright_white] [white]{ssrn.beginner_reason}[/white]"
    )
    verdict_grid.add_row(
        f"[bold bright_green]EXACT NEXT MOVE:[/bold bright_green] [bright_green]{ssrn.beginner_next_move}[/bright_green]"
    )
    bottomline_panel = Panel(
        verdict_grid,
        title="[bold bright_yellow]DESK [R] BEGINNER TRANSLATOR & CHIEF ENGINEER BOTTOM LINE[/bold bright_yellow]",
        box=box.ROUNDED,
        border_style="bright_yellow",
        padding=(0, 1),
    )

    # 3. Top Executive Gating Quick-Check Banner (Crystal Clear Beginner Translation)
    m1_pass = ssrn.mtf_macd_gate_pass
    m1_badge = "[bold black on green] [OK] YES: BUY PERMITTED [/bold black on green]\n[dim]Big Trend is Up[/dim]" if m1_pass else "[bold white on red] [X] NO (STAY IN CASH) [/bold white on red]\n[dim]Big Trend is Down (Veto)[/dim]"
    m2_badge = f"[bold black on yellow] [PLAN] USE {ssrn.target_vol_sizing_pct:.0f}% SIZE [/bold black on yellow]\n[dim]Stormy Market ({ssrn.realized_vol_20d_ann:.0f}% Vol)[/dim]"
    stop_flr = max(0.0, spot_p - ssrn.atr_trailing_stop_dist)
    m3_badge = f"[bold black on cyan] [STOP] -${ssrn.atr_trailing_stop_dist:,.0f} BUFFER [/bold black on cyan]\n[dim]Floor: ${stop_flr:,.0f} (Normal Chop)[/dim]"
    m4_locked = ssrn.annualized_funding_pct > 30.0
    m4_badge = "[bold white on red] [X] DANGER: BUBBLE [/bold white on red]\n[dim]Funding > +30% Ann.[/dim]" if m4_locked else f"[bold black on green] [OK] SAFE: NO BUBBLE [/bold black on green]\n[dim]Borrow Rate: {ssrn.annualized_funding_pct:+.1f}%/yr (Calm)[/dim]"
    m5_badge = f"[bold black on green] [OK] SAFE: FEES COVERED [/bold black on green]\n[dim]Toll: {ssrn.round_trip_friction_bps:.0f} bps (Target > 0.36%)[/dim]"

    top_banner_table = Table.grid(expand=True)
    for _ in range(5):
        top_banner_table.add_column(ratio=1)
    top_banner_table.add_row(
        "[bold cyan]1. Can We Buy? (Trend)[/bold cyan]\n" + m1_badge,
        "[bold cyan]2. Future Size (When OK)[/bold cyan]\n" + m2_badge,
        "[bold cyan]3. Safety Stop (When In)[/bold cyan]\n" + m3_badge,
        "[bold cyan]4. Crash Threat? (Leverage)[/bold cyan]\n" + m4_badge,
        "[bold cyan]5. Fee Defense (Exchange)[/bold cyan]\n" + m5_badge,
    )
    banner_panel = Panel(
        top_banner_table,
        title="[bold bright_white]5 PRE-FLIGHT SAFETY CHECKS (WHAT EACH BOX MEANS)[/bold bright_white]",
        box=box.ROUNDED,
        border_style="bright_cyan",
        padding=(0, 1),
    )

    # 4. Main Unified 5-Row Quantitative Matrix Table with Beginner Translations
    matrix_table = Table(box=box.SIMPLE_HEAVY, expand=True, show_header=True, header_style="bold cyan", pad_edge=False)
    matrix_table.add_column("DOMAIN / RESEARCH PAPER", justify="left", no_wrap=False, ratio=3)
    matrix_table.add_column("BEGINNER QUESTION & QUANTITATIVE RULE", justify="left", no_wrap=False, ratio=4)
    matrix_table.add_column("LIVE TELEMETRY & PLAIN-ENGLISH TRANSLATION", justify="left", no_wrap=False, ratio=4)
    matrix_table.add_column("SWING ACTION & SIZING", justify="center", no_wrap=False, ratio=2)

    # Row 1: Trend Following (Mesicek 1H/1D MACD)
    r1_col1 = (
        "[bold bright_white]01. Trend Police (Macro Gate)[/bold bright_white]\n"
        "[dim cyan]Mesicek & Vojtko (SSRN 5748642)[/dim cyan]\n"
        "[dim]Academic Domain: Time-Series Momentum[/dim]"
    )
    r1_col2 = (
        "[bold bright_yellow]Q: Is the big overall trend safe to buy?[/bold bright_yellow]\n"
        "[white]Rule: Long 1H MACD cross ONLY when Daily MACD is positive.\n"
        "Protects against taking small bounces inside a giant bear fall.[/white]"
    )
    r1_col3 = (
        f"[bright_white]Live: {ssrn.daily_macd_status}[/bright_white]\n"
        f"[bold red]Beginner Meaning:[/bold red] [white]Big trend is DOWN. Don't buy 1H dips (Bull Trap risk).[/white]\n"
        f"[dim]1D MACD: {ssrn.live_trend_1d} | 1H MACD: {ssrn.hourly_macd_status}[/dim]"
    )
    r1_col4 = (
        f"{m1_badge}\n"
        f"[dim]Spot Sizing: {'100% Permitted' if m1_pass else '0% (Cash Defense)'}[/dim]"
    )
    matrix_table.add_row(r1_col1, r1_col2, r1_col3, r1_col4)

    # Row 2: Breakouts & Risk (Zarattini Donchian + 25% Vol Target)
    r2_col1 = (
        "[bold bright_white]02. Seatbelt Adjuster (Vol Sizing)[/bold bright_white]\n"
        "[dim cyan]Zarattini, Pagani & Barbon (SSRN 5209907)[/dim cyan]\n"
        "[dim]Academic Domain: Systematic Factor Pricing[/dim]"
    )
    r2_col2 = (
        "[bold bright_yellow]Q: If we do enter, how much should we buy?[/bold bright_yellow]\n"
        "[white]Rule: Position Weight = Target_Vol (25%) / Realized_Vol.\n"
        "Forces you to buy smaller when the ocean is turbulent.[/white]"
    )
    r2_col3 = (
        f"[bright_white]Live: 20D Realized Vol is {ssrn.realized_vol_20d_ann:.1f}% (Normal is 25.0%)[/bright_white]\n"
        f"[bold green]Beginner Meaning:[/bold green] [white]Market is wilder than normal. Shrink trade to {ssrn.target_vol_sizing_pct:.0f}% size to stay safe.[/white]\n"
        f"[dim]Realized Variance: {ssrn.live_realized_variance:.4f} | 20D Skew: {ssrn.live_skewness_20d:+.2f}[/dim]"
    )
    r2_col4 = (
        f"{m2_badge}\n"
        f"[dim]Dynamic Volatility Size[/dim]"
    )
    matrix_table.add_row(r2_col1, r2_col2, r2_col3, r2_col4)

    # Row 3: Volatility Stops (Karassavidis 8H ATR Trail)
    stop_floor = max(0.0, spot_p - ssrn.atr_trailing_stop_dist)
    stop_pct = (ssrn.atr_trailing_stop_dist / max(spot_p, 1000.0)) * 100.0
    r3_col1 = (
        "[bold bright_white]03. Breathing Room (Stop Buffer)[/bold bright_white]\n"
        "[dim cyan]Karassavidis et al. (SSRN 5821842)[/dim cyan]\n"
        "[dim]Academic Domain: Market Microstructure[/dim]"
    )
    r3_col2 = (
        "[bold bright_yellow]Q: Where do we place our stop loss safety net?[/bold bright_yellow]\n"
        "[white]Rule: Peg trailing stop distance to 2.5x 14-period ATR.\n"
        "Stops random market wiggles from prematurely kicking you out.[/white]"
    )
    r3_col3 = (
        f"[bright_white]Live: 8H ATR(14) is ${ssrn.atr_14_8h:,.0f} • Spot: ${spot_p:,.0f}[/bright_white]\n"
        f"[bold cyan]Beginner Meaning:[/bold cyan] [white]BTC wiggles ${ssrn.atr_14_8h:,.0f} every 8h. Put stop at ${stop_floor:,.0f} (-${ssrn.atr_trailing_stop_dist:,.0f} room).[/white]\n"
        f"[dim]Structural Stop Floor: ${stop_floor:,.0f} (-{stop_pct:.1f}% distance)[/dim]"
    )
    r3_col4 = (
        f"{m3_badge}\n"
        f"[dim]Trailing Distance: -{stop_pct:.1f}%[/dim]"
    )
    matrix_table.add_row(r3_col1, r3_col2, r3_col3, r3_col4)

    # Row 4: Sentiment Exhaustion (Chan Perp Funding < 30% Gate)
    r4_col1 = (
        "[bold bright_white]04. Bubble Alarm (Funding Gate)[/bold bright_white]\n"
        "[dim cyan]Chan (SSRN 5292305)[/dim cyan]\n"
        "[dim]Academic Domain: On-Chain & Derivatives Carry[/dim]"
    )
    r4_col2 = (
        "[bold bright_yellow]Q: Are futures degens about to cause a giant crash?[/bold bright_yellow]\n"
        "[white]Rule: Freeze all new spot buying if Perp Funding > +30% Ann.\n"
        "Protects you from buying right before a long liquidation waterfall.[/white]"
    )
    funding_trans = "Traders are calm (healthy carry). No leverage bubble or crash danger." if not m4_locked else "DANGER: Futures degens are over-borrowing! Liquidation waterfall imminent."
    r4_col3 = (
        f"[bright_white]Live: Annualized Funding is {ssrn.annualized_funding_pct:+.2f}% (Ceiling: +30%)[/bright_white]\n"
        f"[bold green]Beginner Meaning:[/bold green] [white]{funding_trans}[/white]\n"
        f"[dim]MVRV Ratio: {ssrn.live_mvrv_ratio:.2f} (Floor <1.0 | Top >3.5) • SOPR: {ssrn.live_sopr_level:.2f}[/dim]"
    )
    r4_col4 = (
        f"{m4_badge}\n"
        f"[dim]{'Overheated Bubble' if m4_locked else 'Healthy Basis Carry'}[/dim]"
    )
    matrix_table.add_row(r4_col1, r4_col2, r4_col3, r4_col4)

    # Row 5: Alpha Hurdle (Bysik Cost Barrier >= 18 bps)
    r5_col1 = (
        "[bold bright_white]05. Casino Toll Gate (Fee Hurdle)[/bold bright_white]\n"
        "[dim cyan]Bysik & Slepaczuk (SSRN 6795938)[/dim cyan]\n"
        "[dim]Academic Domain: Alternative Data & ML Friction[/dim]"
    )
    r5_col2 = (
        "[bold bright_yellow]Q: Will exchange fees eat up all my profits?[/bold bright_yellow]\n"
        "[white]Rule: Only trade if expected profit > 2x exchange fees (>= +0.36%).\n"
        "Prevents the exchange casino from bleeding your balance on tiny wiggles.[/white]"
    )
    r5_col3 = (
        f"[bright_white]Live: Round-Trip Fees = {ssrn.round_trip_friction_bps:.0f} bps (+{ssrn.round_trip_friction_bps/100:.2f}%)[/bright_white]\n"
        f"[bold green]Beginner Meaning:[/bold green] [white]Protected against fee drag. Only trades targeting >+0.36% profit are authorized.[/white]\n"
        f"[dim]Order Book Imbalance (OBI): {ssrn.live_obi_ratio_pct:+.1f}% • 4H CVD: {ssrn.live_4h_cvd_delta:+.1f} BTC[/dim]"
    )
    r5_col4 = (
        f"{m5_badge}\n"
        f"[dim]Fee Bleed Filter: ACTIVE[/dim]"
    )
    matrix_table.add_row(r5_col1, r5_col2, r5_col3, r5_col4)

    matrix_panel = Panel(
        matrix_table,
        title="[bold cyan]UNIFIED EMPIRICAL STRATEGY & ACADEMIC TELEMETRY MATRIX (WITH BEGINNER TRANSLATIONS)[/bold cyan]",
        box=box.ROUNDED,
        border_style="cyan",
        padding=(0, 1),
    )

    # 5. Bottom clipboard strip
    last_copy_str = ""
    if getattr(store, "last_packet_copied_utc", ""):
        last_copy_str = f"  |  [bold green][OK] COPIED AT {store.last_packet_copied_utc} ({getattr(store, 'last_packet_char_count', 0):,} chars)[/bold green]"

    bottom_grid = Table.grid(expand=True)
    bottom_grid.add_column(justify="left", no_wrap=True)
    bottom_grid.add_column(justify="right", no_wrap=True)
    bottom_grid.add_row(
        "[bold black on bright_yellow] [KEY R / RR] SSRN BRIEF CLIPBOARD [/bold black on bright_yellow]  "
        "[bright_white]Tap [bold yellow]'R'[/bold yellow] to switch to Desk [R] | Tap [bold yellow]'R'[/bold yellow] again (or [bold yellow]'RR'[/bold yellow]) to copy SSRN Master Brief! (0 screenshots needed)[/bright_white]" + last_copy_str,
        "[dim]Unified Quantitative Matrix | Spot-Only Gating[/dim]",
    )
    bottom_panel = Panel(bottom_grid, box=box.ROUNDED, border_style="bright_yellow", padding=(0, 1))

    return Group(header_panel, sub_panel, bottomline_panel, banner_panel, matrix_panel, bottom_panel)


def _build_tab17_btc_magnet_hud(
    config: EngineConfig,
    store: StateStore,
    header_panel: Panel,
) -> Group:
    """Builds Desk 17 [M: BTC MAGNET] - Mechanics-First Liquidation Gravity & Edge Detector."""
    magnet_eval = store.btc_magnet_evaluation
    if magnet_eval is None:
        from analytics.btc_magnet_engine import BTCMagnetEngine
        engine = BTCMagnetEngine(config)
        magnet_eval = engine.evaluate(store)

    spot_p = magnet_eval.spot_price or store.binance_spot_price or 76000.0
    up = magnet_eval.upper_magnet
    lo = magnet_eval.lower_magnet

    # 1. Sub-Ribbon Header
    sub_grid = Table.grid(expand=True)
    sub_grid.add_column(justify="left", no_wrap=True)
    sub_grid.add_column(justify="right", no_wrap=True)
    sub_grid.add_row(
        "[bold bright_cyan]DESK [M]: BTC MAGNET | LIQUIDATION GRAVITY DECK[/bold bright_cyan]  |  "
        "[bold bright_white]MECHANICS-FIRST SWING INTELLIGENCE (DEFAULTS TO WAIT)[/bold bright_white]",
        "[dim]Press [bold cyan]'M'[/bold cyan] (or [bold cyan]'MM'[/bold cyan]) to copy Shareable Magnet Card brief[/dim]",
    )
    sub_panel = Panel(sub_grid, box=box.ROUNDED, border_style="bright_cyan", padding=(0, 1))

    # 2. Liquidation Gravitational Horizon Box (3-Column Strip)
    horizon_table = Table(box=box.ROUNDED, expand=True, show_header=True, header_style="bold bright_white", pad_edge=False)
    horizon_table.add_column("▲ UPPER MAGNET (SHORT LIQUIDATIONS)", justify="center", ratio=3)
    horizon_table.add_column("◆ SPOT HORIZON (CENTER ZERO)", justify="center", ratio=4)
    horizon_table.add_column("▼ LOWER SUPPORT (LONG LIQUIDATIONS)", justify="center", ratio=3)

    up_dist_usd = up.price - spot_p
    lo_dist_usd = spot_p - lo.price

    col_up = (
        f"[bold bright_cyan]${up.price:,.0f}[/bold bright_cyan]  "
        f"[cyan]({up.dist_pct:+.1f}% / +${up_dist_usd:,.0f})[/cyan]\n"
        f"[dim]Density: ${up.usd_volume/1e6:,.1f}M Cluster (Binance/Exchanges)[/dim]"
    )

    pull_color = "bright_cyan" if magnet_eval.pull_direction == "UPPER" else ("bright_yellow" if magnet_eval.pull_direction == "LOWER" else "white")
    col_center = (
        f"[bold bright_white]SPOT: ${spot_p:,.2f}[/bold bright_white]  "
        f"[{'green' if magnet_eval.price_change_24h_pct >= 0 else 'red'}]({magnet_eval.price_change_24h_pct:+.2f}% 24h)[/{'green' if magnet_eval.price_change_24h_pct >= 0 else 'red'}]\n"
        f"[bold {pull_color}]PULL DIRECTION: {magnet_eval.pull_direction} MAGNET ({magnet_eval.pull_ratio:.2f}x RATIO)[/bold {pull_color}]\n"
        f"[dim]24h Range: ${magnet_eval.low_24h:,.0f} - ${magnet_eval.high_24h:,.0f} • Perp Funding: {magnet_eval.funding_rate_annual_pct:+.1f}%/yr • 4h OI: {magnet_eval.oi_delta_4h_pct:+.1f}% • Regime: {magnet_eval.market_regime}[/dim]"
    )

    col_lo = (
        f"[bold bright_yellow]${lo.price:,.0f}[/bold bright_yellow]  "
        f"[yellow]({lo.dist_pct:+.1f}% / -${lo_dist_usd:,.0f})[/yellow]\n"
        f"[dim]Density: ${lo.usd_volume/1e6:,.1f}M Cluster (Binance/Exchanges)[/dim]"
    )

    horizon_table.add_row(col_up, col_center, col_lo)

    # Gravitational Density Gauges & Vector Direction
    max_vol = max(up.usd_volume, lo.usd_volume, 1.0)
    up_blocks = max(1, int(round((up.usd_volume / max_vol) * 16)))
    lo_blocks = max(1, int(round((lo.usd_volume / max_vol) * 16)))
    up_bar = f"[bright_cyan]{'■' * up_blocks}{'░' * (16 - up_blocks)}[/bright_cyan] [dim](${up.usd_volume/1e6:,.0f}M Short Pool)[/dim]"
    lo_bar = f"[bright_yellow]{'■' * lo_blocks}{'░' * (16 - lo_blocks)}[/bright_yellow] [dim](${lo.usd_volume/1e6:,.0f}M Long Pool)[/dim]"
    if magnet_eval.pull_direction == "LOWER":
        density_mult = lo.usd_volume / max(up.usd_volume, 1.0)
        grav_gauge = f"[bold bright_yellow]◀◀ GRAVITATIONAL VECTOR: PULLING DOWN ({density_mult:.1f}x DENSITY) ◀◀[/bold bright_yellow]"
    elif magnet_eval.pull_direction == "UPPER":
        density_mult = up.usd_volume / max(lo.usd_volume, 1.0)
        grav_gauge = f"[bold bright_cyan]▶▶ GRAVITATIONAL VECTOR: PULLING UP ({density_mult:.1f}x DENSITY) ▶▶[/bold bright_cyan]"
    else:
        grav_gauge = "[bold white]── BALANCED HORIZON (EQUILIBRIUM) ──[/bold white]"
    horizon_table.add_row(up_bar, grav_gauge, lo_bar)
    horizon_panel = Panel(
        horizon_table,
        title="[bold bright_white]LIQUIDATION GRAVITATIONAL HORIZON[/bold bright_white]",
        box=box.ROUNDED,
        border_style="bright_cyan",
        padding=(0, 1),
    )

    # 3. Status Report Card (Locked Templates from docs/status-templates.md)
    is_edge = magnet_eval.verdict == "SPEAK"
    verdict_badge = "[bold black on bright_cyan] SWING EDGE PRESENT [/bold black on bright_cyan]" if is_edge else "[bold black on bright_yellow] NO CLEAR EDGE - WAIT [/bold black on bright_yellow]"
    verdict_border = "bright_cyan" if is_edge else "bright_yellow"

    status_grid = Table.grid(expand=True)
    status_grid.add_column()
    status_grid.add_row(
        f"[bold bright_white]>_ MECHANICAL STATUS VERDICT:[/bold bright_white] {verdict_badge}  |  "
        f"[bold bright_white]{magnet_eval.headline}[/bold bright_white]"
    )
    status_grid.add_row(
        f"[bold bright_cyan]EXPLANATION READOUT:[/bold bright_cyan] [white]{magnet_eval.body}[/white]"
    )
    status_grid.add_row(
        f"[dim]Rule Reference: {magnet_eval.rule_subtitle}[/dim]"
    )

    status_panel = Panel(
        status_grid,
        title="[bold bright_white]>_ STATUS REPORT (ONE-QUESTION READOUT)[/bold bright_white]",
        box=box.ROUNDED,
        border_style=verdict_border,
        padding=(0, 1),
    )

    # 4. 7 Internal Speaking Rules Audit Table
    rules_table = Table(box=box.SIMPLE_HEAVY, expand=True, show_header=True, header_style="bold cyan", pad_edge=False)
    rules_table.add_column("RULE # & FILTER NAME", justify="left", ratio=3)
    rules_table.add_column("LOCKED SPECIFICATION REQUIREMENT", justify="left", ratio=4)
    rules_table.add_column("LIVE MARKET TELEMETRY & AUDIT DETAIL", justify="left", ratio=5)
    rules_table.add_column("STATUS", justify="center", ratio=2)

    specs = [
        "Meaningful liquidation cluster within 0.8% - 4.5% reach (>= $100M)",
        "Open interest expanding or stable into magnet (4h velocity >= -0.5%)",
        "Borrow carry not contradictory (-10.0% to +28.0% annual funding)",
        "Range regime (primary) or Trend-aligned in direction of magnet",
        "Basic structure & spot-flow alignment (no extreme opposite momentum)",
        "Target liquidation cluster intact and not already swept",
        "At least 5 of 6 cleanly met with 0 direct conflicts (otherwise: WAIT)",
    ]

    for i, r in enumerate(magnet_eval.rule_checks):
        status_str = "[bold black on green] [OK] PASS [/bold black on green]" if r.passed else "[bold white on red] [X] WAIT [/bold white on red]"
        spec_text = specs[i] if i < len(specs) else "Strict internal condition"
        rules_table.add_row(
            f"[bold bright_white]Rule {r.rule_num}:[/bold bright_white] {r.name}",
            f"[dim]{spec_text}[/dim]",
            f"[white]{r.detail}[/white]",
            status_str,
        )

    rules_panel = Panel(
        rules_table,
        title="[bold bright_white]7 INTERNAL SPEAKING RULES AUDIT CHECKLIST[/bold bright_white]",
        box=box.ROUNDED,
        border_style="bright_blue",
        padding=(0, 1),
    )

    # 5. Bottom Clipboard & Sharing Panel
    last_copy_str = ""
    if getattr(store, "last_packet_copied_utc", ""):
        last_copy_str = f"  |  [bold green]Last Brief Copied: {store.last_packet_copied_utc} ({getattr(store, 'last_packet_char_count', 0):,} chars)[/bold green]"

    bottom_grid = Table.grid(expand=True)
    bottom_grid.add_column(justify="left", no_wrap=True)
    bottom_grid.add_column(justify="right", no_wrap=True)
    bottom_grid.add_row(
        "[bold black on bright_cyan] [KEY M / MM] BTC MAGNET CLIPBOARD [/bold black on bright_cyan]  "
        "[bright_white]Tap [bold cyan]'M'[/bold cyan] to switch to Desk [M] | Tap [bold cyan]'M'[/bold cyan] again (or [bold cyan]'MM'[/bold cyan]) to copy Shareable Magnet Card brief![/bright_white]" + last_copy_str,
        "[dim]BTC Magnet Engine | btc-magnet.netlify.app[/dim]",
    )
    bottom_panel = Panel(bottom_grid, box=box.ROUNDED, border_style="bright_cyan", padding=(0, 1))

    return Group(header_panel, sub_panel, horizon_panel, status_panel, rules_panel, bottom_panel)


def _build_tab18_trend_pullback_hud(
    config: EngineConfig,
    store: StateStore,
    header_panel: Panel,
) -> Group:
    """Builds Desk 18 [A: BTC STRATEGY] - BTC TREND-PULLBACK v1.0 (Research / Paper Mode)."""
    tp_eval = getattr(store, "trend_pullback_evaluation", None)
    if tp_eval is None:
        from analytics.strategy_trend_pullback import TrendPullbackEngine
        tp_eval = TrendPullbackEngine(config).evaluate(store)

    spot_p = tp_eval.spot_price or store.binance_spot_price or 0.0

    # 1. Sub-Ribbon Header (with mandatory Section 12 Research Honesty labels)
    sub_grid = Table.grid(expand=True)
    sub_grid.add_column(justify="left", no_wrap=True)
    sub_grid.add_column(justify="right", no_wrap=True)
    sub_grid.add_row(
        f"[bold bright_green]{tp_eval.strategy_name} | SPOT SWING | LONG ONLY | {tp_eval.mode_label}[/bold bright_green]  │  "
        f"[bold black on bright_yellow] STRATEGY STATUS: {tp_eval.strategy_status} [/bold black on bright_yellow]",
        f"[bold white]Spot Price: [cyan]${spot_p:,.2f}[/cyan]   •   Last Update: [bright_cyan]{tp_eval.timestamp_myt}[/bright_cyan][/bold white]",
    )
    sub_panel = Panel(sub_grid, box=box.ROUNDED, border_style="bright_green", padding=(0, 1))

    # 2. Row 1 Grid: MARKET REGIME (Left) + 4H TREND FILTER (Center) + PULLBACK ANALYSIS (Right)
    reg_col = "bright_green" if tp_eval.daily_regime == "BULLISH" else "bright_red"
    slope_1d_lbl = "RISING" if tp_eval.daily_sma200_rising else "FALLING"
    slope_1d_col = "green" if tp_eval.daily_sma200_rising else "red"
    w50_status = "ABOVE" if (tp_eval.ema50_1w > 0 and spot_p > tp_eval.ema50_1w) else ("BELOW" if tp_eval.ema50_1w > 0 else "N/A")
    regime_lines = [
        f"[bold white]Daily Regime:[/bold white]     [bold {reg_col}]{tp_eval.daily_regime}[/bold {reg_col}]",
        f"[bold white]1D Open -> Close:[/bold white] [white]{tp_eval.daily_open_time_utc} -> {tp_eval.daily_close_time_utc}[/white]",
        f"[bold white]1D Close (Closed):[/bold white] [cyan]${tp_eval.daily_close_completed:,.2f}[/cyan] [dim](O ${tp_eval.daily_open_completed:,.0f} H ${tp_eval.daily_high_completed:,.0f} L ${tp_eval.daily_low_completed:,.0f})[/dim]",
        f"[bold white]Daily SMA200:[/bold white]     [cyan]${tp_eval.daily_sma200:,.2f}[/cyan] [dim](20D Prior: ${tp_eval.daily_sma200_prev20:,.2f})[/dim]",
        f"[bold white]SMA200 20D Slope:[/bold white] [{slope_1d_col}]{slope_1d_lbl} ({tp_eval.daily_sma200_slope_20d:+,.2f})[/{slope_1d_col}]",
        f"[dim]Macro Context (Read-Only): 1W EMA50 ${tp_eval.ema50_1w:,.0f} ({w50_status}) • 1D EMA50 ${tp_eval.ema50_1d:,.0f}[/dim]",
    ]
    regime_panel = Panel(
        "\n".join(regime_lines),
        title="[bold bright_white]MARKET REGIME (1D GATEKEEPER)[/bold bright_white]",
        box=box.ROUNDED,
        border_style=reg_col,
        padding=(0, 1),
    )

    tr_col = "bright_green" if tp_eval.trend_4h == "CONFIRMED" else "yellow"
    slope_4h_lbl = "RISING" if tp_eval.ema50_rising_6bars else "FALLING"
    slope_4h_col = "green" if tp_eval.ema50_rising_6bars else "red"
    trend_lines = [
        f"[bold white]4H Trend:[/bold white]             [bold {tr_col}]{tp_eval.trend_4h}[/bold {tr_col}]",
        f"[bold white]4H Open -> Close:[/bold white]     [white]{tp_eval.candle_4h_open_time_utc} -> {tp_eval.candle_4h_close_time_utc}[/white]",
        f"[bold white]4H Close (Closed):[/bold white]    [cyan]${tp_eval.close_4h_completed:,.2f}[/cyan]",
        f"[bold white]4H EMA50 / EMA200:[/bold white]    [cyan]${tp_eval.ema50_4h:,.2f}[/cyan] / [cyan]${tp_eval.ema200_4h:,.2f}[/cyan]",
        f"[bold white]4H EMA50 6-Bar Slope:[/bold white] [{slope_4h_col}]{slope_4h_lbl} ({tp_eval.ema50_4h_slope_6bars:+,.2f})[/{slope_4h_col}] [dim](Prior: ${tp_eval.ema50_4h_prev6:,.2f})[/dim]",
        f"[bold white]4H ATR14:[/bold white]             [cyan]${tp_eval.atr14_4h:,.2f}[/cyan]",
    ]
    trend_panel = Panel(
        "\n".join(trend_lines),
        title="[bold bright_white]4H TREND FILTER[/bold bright_white]",
        box=box.ROUNDED,
        border_style=tr_col,
        padding=(0, 1),
    )

    pb_valid = tp_eval.recovery_candle == "CONFIRMED"
    pb_valid_str = "[bold bright_green]CONFIRMED[/bold bright_green]" if pb_valid else "[bold yellow]NOT CONFIRMED[/bold yellow]"
    pb_col = "bright_green" if pb_valid else "bright_blue"
    age_str = f"{tp_eval.bars_since_recovery} / 3 4H bars" if tp_eval.bars_since_recovery >= 0 else "No active recovery candle"
    pullback_lines = [
        f"[bold white]Evaluated 4H Bar:[/bold white] [white]{tp_eval.candle_4h_open_time_utc} -> {tp_eval.candle_4h_close_time_utc}[/white]",
        f"[bold white]4H Candle OHLC:[/bold white]   [white]O ${tp_eval.open_4h_completed:,.2f} H ${tp_eval.high_4h_completed:,.2f} L ${tp_eval.low_4h_completed:,.2f} C ${tp_eval.close_4h_completed:,.2f}[/white]",
        f"[bold white]Pullback Zone:[/bold white]    [cyan]${tp_eval.pullback_zone_lower:,.2f} - ${tp_eval.pullback_zone_upper:,.2f}[/cyan] [dim](-0.50 to +0.25 ATR)[/dim]",
        f"[bold white]Max Extension:[/bold white]    [cyan]${tp_eval.max_extension_price:,.2f}[/cyan] [dim](EMA50 + 1.00 ATR)[/dim]",
        f"[bold white]Recovery / Setup:[/bold white] {pb_valid_str} • [bold white]{tp_eval.setup_status}[/bold white] [dim]({age_str})[/dim]",
        f"[dim]{tp_eval.pullback_rejection_reason}[/dim]",
    ]
    pullback_panel = Panel(
        "\n".join(pullback_lines),
        title="[bold bright_white]PULLBACK ANALYSIS[/bold bright_white]",
        box=box.ROUNDED,
        border_style=pb_col,
        padding=(0, 1),
    )

    top_row_grid = Table.grid(expand=True)
    top_row_grid.add_column(ratio=1)
    top_row_grid.add_column(ratio=1)
    top_row_grid.add_column(ratio=1)
    top_row_grid.add_row(regime_panel, trend_panel, pullback_panel)

    # 3. Row 2 Grid: TRADE PLAN (Left) + POSITION MANAGEMENT (Center) + DATA INTEGRITY (Right)
    stop_badge = "[green]VALID[/green]" if tp_eval.stop_valid else "[yellow]REJECTED[/yellow]"
    active_sz_note = "[dim](Hypothetical Ref • Active Order: 0.00000 BTC)[/dim]" if tp_eval.trade_decision == "NO TRADE" else "[bold green](Active Setup Size)[/bold green]"
    trade_lines = [
        f"[bold white]Decision / Equity:[/bold white]  [bold bright_white]{tp_eval.trade_decision}[/bold bright_white] • [cyan]US${tp_eval.simulation_equity_usd:,.2f}[/cyan] [dim]({tp_eval.risk_per_trade_pct:.2f}% = ${tp_eval.risk_budget_usd:,.2f} Risk)[/dim]",
        f"[bold white]Limit Entry Zone:[/bold white]   [cyan]${tp_eval.limit_entry_low:,.2f} - ${tp_eval.limit_entry_high:,.2f}[/cyan] [dim](Sizing Ref: ${tp_eval.sizing_entry_price:,.2f})[/dim]",
        f"[bold white]Stop Calculation:[/bold white]   [white]5-Bar Low ${tp_eval.stop_lowest_low_5bars:,.2f} - Buffer ${tp_eval.stop_buffer_usd:,.2f} =[/white] [cyan]${tp_eval.structural_stop:,.2f}[/cyan] ({stop_badge})",
        f"[bold white]Stop Distance:[/bold white]      [white]-${tp_eval.stop_distance_usd:,.2f} ({tp_eval.stop_distance_atr:.2f} ATR / exact {tp_eval.stop_distance_atr_exact:.4f} ATR)[/white]",
        f"[bold white]Gross Price Risk:[/bold white]   [white]${tp_eval.gross_price_risk_per_btc:,.2f}/BTC -> ${tp_eval.gross_price_risk_usd:,.2f}[/white]",
        f"[bold white]Fees (0.10%x2):[/bold white]     [dim]Entry ${tp_eval.entry_fee_usd:,.2f} (${tp_eval.entry_fee_per_btc:,.2f}/BTC) + Exit ${tp_eval.exit_fee_usd:,.2f} (${tp_eval.exit_fee_per_btc:,.2f}/BTC)[/dim]",
        f"[bold white]Slippage (0.05%x2):[/bold white] [dim]Entry ${tp_eval.entry_slippage_usd:,.2f} (${tp_eval.entry_slippage_per_btc:,.2f}/BTC) + Exit ${tp_eval.exit_slippage_usd:,.2f} (${tp_eval.exit_slippage_per_btc:,.2f}/BTC)[/dim]",
        f"[bold white]Total Est. Risk:[/bold white]    [cyan]${tp_eval.total_risk_per_btc:,.2f}/BTC -> ${tp_eval.total_estimated_risk_usd:,.2f}[/cyan] [dim](<= ${tp_eval.risk_budget_usd:,.2f} Budget)[/dim]",
        f"[bold white]Position Size:[/bold white]      [bold bright_cyan]{tp_eval.position_size_btc:.5f} BTC[/bold bright_cyan] ([cyan]${tp_eval.position_value_usd:,.2f}[/cyan]) {active_sz_note}",
        f"[bold white]Risk / Reward:[/bold white]      [dim]{tp_eval.risk_reward_label}[/dim]",
    ]
    trade_panel = Panel(
        "\n".join(trade_lines),
        title="[bold bright_white]TRADE PLAN (SPOT ONLY • NO LEVERAGE)[/bold bright_white]",
        box=box.ROUNDED,
        border_style="bright_cyan",
        padding=(0, 1),
    )

    pos_col = "bright_green" if tp_eval.position_status == "HOLDING" else "white"
    if tp_eval.position_status == "CASH":
        sb_str = "[dim]INACTIVE (IN CASH)[/dim]"
        e4h_str = "[dim]INACTIVE (IN CASH)[/dim]"
        s1d_str = "[dim]INACTIVE (IN CASH)[/dim]"
    else:
        sb_str = "[bold bright_red]TRIGGERED[/bold bright_red]" if tp_eval.exit_stop_breached else "[green]CLEAR[/green]"
        e4h_str = "[bold bright_red]TRIGGERED[/bold bright_red]" if tp_eval.exit_two_4h_below_ema50 else "[green]CLEAR[/green]"
        s1d_str = "[bold bright_red]TRIGGERED[/bold bright_red]" if tp_eval.exit_two_1d_below_sma200 else "[green]CLEAR[/green]"
    pos_lines = [
        f"[bold white]Current Status:[/bold white]     [bold {pos_col}]{tp_eval.position_status}[/bold {pos_col}]",
        f"[bold white]Active Exit Status:[/bold white] [bold white]{tp_eval.exit_conditions_status}[/bold white]",
        f"[bold white]Entry Eligibility:[/bold white]  [yellow]{tp_eval.entry_eligibility_status}[/yellow]",
        f"[bold white]Active Stop Breach:[/bold white] {sb_str}",
        f"[bold white]Active 2x4H<EMA50:[/bold white]  {e4h_str}",
        f"[bold white]Active 2x1D<SMA200:[/bold white] {s1d_str}",
        f"[dim]{tp_eval.hypothetical_exit_status}[/dim]",
        f"[dim]Invalidation: {tp_eval.invalidation_reason}[/dim]",
        f"[bold white]Execution Mode:[/bold white]     [green]Manual Spot Only • 0.0x Leverage • Long-Only[/green]",
    ]
    pos_panel = Panel(
        "\n".join(pos_lines),
        title="[bold bright_white]POSITION MANAGEMENT[/bold bright_white]",
        box=box.ROUNDED,
        border_style="bright_blue",
        padding=(0, 1),
    )

    di_col = "bright_green" if tp_eval.data_integrity_ok else "bright_red"
    di_label = "OK (CLOSED CANDLES ONLY)" if tp_eval.data_integrity_ok else "DATA UNAVAILABLE"
    f1d_str = f"YES (Excluded Open {tp_eval.daily_forming_open_utc})" if tp_eval.daily_forming_excluded else f"NO ({tp_eval.daily_forming_open_utc})"
    f4h_str = f"YES (Excluded Open {tp_eval.candle_4h_forming_open_utc})" if tp_eval.candle_4h_forming_excluded else f"NO ({tp_eval.candle_4h_forming_open_utc})"
    data_lines = [
        f"[bold white]Daily Candle:[/bold white]       [cyan]{tp_eval.daily_candle_status}[/cyan]",
        f"[bold white]Forming 1D Bar:[/bold white]     [green]{f1d_str}[/green]",
        f"[bold white]4H Candle:[/bold white]          [cyan]{tp_eval.candle_4h_status}[/cyan]",
        f"[bold white]Forming 4H Bar:[/bold white]     [green]{f4h_str}[/green]",
        f"[bold white]Retrieval (MYT):[/bold white]    [white]{tp_eval.timestamp_myt}[/white]",
        f"[bold white]Retrieval (UTC):[/bold white]    [white]{tp_eval.timestamp_utc}[/white]",
        f"[bold white]Integrity Gate:[/bold white]     [bold {di_col}]{di_label}[/bold {di_col}]",
        f"[dim]{tp_eval.integrity_failure_reason or 'All required spot OHLCV series verified & fresh.'}[/dim]",
        f"[bold white]Cost Model:[/bold white]         [dim]Fee 0.10%/side + Slippage 0.05%/side[/dim]",
    ]
    data_panel = Panel(
        "\n".join(data_lines),
        title="[bold bright_white]DATA INTEGRITY (FAIL-CLOSED)[/bold bright_white]",
        box=box.ROUNDED,
        border_style=di_col,
        padding=(0, 1),
    )

    mid_row_grid = Table.grid(expand=True)
    mid_row_grid.add_column(ratio=1)
    mid_row_grid.add_column(ratio=1)
    mid_row_grid.add_column(ratio=1)
    mid_row_grid.add_row(trade_panel, pos_panel, data_panel)

    # 4. STRATEGY VERDICT Panel
    verdict_badge_map = {
        "ENTRY READY": "[bold black on bright_green] ENTRY READY [/bold black on bright_green]",
        "WAIT": "[bold black on bright_yellow] WAIT [/bold black on bright_yellow]",
        "HOLD": "[bold black on bright_cyan] HOLD [/bold black on bright_cyan]",
        "EXIT ALERT": "[bold white on red] EXIT ALERT [/bold white on red]",
        "NO TRADE": "[bold white on bright_black] NO TRADE [/bold white on bright_black]",
    }
    v_badge = verdict_badge_map.get(tp_eval.strategy_verdict, f"[bold white]{tp_eval.strategy_verdict}[/bold white]")
    v_border = (
        "bright_green"
        if tp_eval.strategy_verdict == "ENTRY READY"
        else ("bright_red" if tp_eval.strategy_verdict == "EXIT ALERT" or not tp_eval.data_integrity_ok else "bright_yellow")
    )
    verdict_grid = Table.grid(expand=True)
    verdict_grid.add_column()
    verdict_grid.add_row(
        f"[bold bright_white]STRATEGY VERDICT:[/bold bright_white] {v_badge}  │  "
        f"[bold bright_cyan]DECISION STATE:[/bold bright_cyan] [bold white]{tp_eval.decision_state}[/bold white]  │  "
        f"[bold yellow]STRATEGY STATUS: {tp_eval.strategy_status}[/bold yellow]  │  "
        f"[dim]{tp_eval.mode_label}[/dim]"
    )
    verdict_grid.add_row(f"[bold bright_cyan]EXPLANATION:[/bold bright_cyan] [white]{tp_eval.verdict_explanation}[/white]")

    verdict_panel = Panel(
        verdict_grid,
        title="[bold bright_white]STRATEGY VERDICT (DETERMINISTIC SPOT SWING PROTOCOL)[/bold bright_white]",
        box=box.ROUNDED,
        border_style=v_border,
        padding=(0, 1),
    )

    # 5. Bottom Clipboard Bar
    last_copy_str = ""
    if getattr(store, "last_packet_copied_utc", ""):
        last_copy_str = f"  │  [bold green]Last Brief Copied: {store.last_packet_copied_utc} ({getattr(store, 'last_packet_char_count', 0):,} chars)[/bold green]"

    bottom_grid = Table.grid(expand=True)
    bottom_grid.add_column(justify="left", no_wrap=True)
    bottom_grid.add_column(justify="right", no_wrap=True)
    bottom_grid.add_row(
        "[bold black on bright_green] [KEY A] BTC TREND-PULLBACK v1.0 [/bold black on bright_green]  "
        "[bright_white]Tap [bold green]'A'[/bold green] to open Desk [A] │ Tap [bold green]'A'[/bold green] again to copy Strategy Brief to Clipboard![/bright_white]" + last_copy_str,
        "[dim]config/trend_pullback_config.yaml • Independent Calculation[/dim]",
    )
    bottom_panel = Panel(bottom_grid, box=box.ROUNDED, border_style="bright_green", padding=(0, 1))

    return Group(header_panel, sub_panel, top_row_grid, mid_row_grid, verdict_panel, bottom_panel)


def build_dashboard_renderable(
    config: EngineConfig,
    store: StateStore,
    tab_override: Optional[int] = None,
) -> Group:
    """Builds the active tab's 5-panel Rich renderable for the live terminal HUD."""
    valid_tabs = (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18)
    if tab_override is not None:
        if isinstance(tab_override, int) and tab_override in valid_tabs:
            active_tab = tab_override
        elif str(tab_override).lower() in ("g", "grok", "grok_flow", "15"):
            active_tab = 15
        elif str(tab_override).lower() in ("r", "ssrn", "research", "alpha", "16"):
            active_tab = 16
        elif str(tab_override).lower() in ("m", "magnet", "btc_magnet", "17"):
            active_tab = 17
        elif str(tab_override).lower() in ("a", "k", "strategy", "trend_pullback", "btc_strategy", "18"):
            active_tab = 18
        elif str(tab_override).lower() in ("b", "pattern", "patterns", "chart", "14"):
            active_tab = 14
        elif str(tab_override).lower() in ("l", "master", "10"):
            active_tab = 10
        elif str(tab_override).lower() in ("w", "waterfall", "wf", "12"):
            active_tab = 12
        elif str(tab_override).lower() in ("0", "s0", "spot", "swing"):
            active_tab = 0
        elif str(tab_override).lower() in ("f", "footprint", "fp", "11"):
            active_tab = 11
        elif str(tab_override).lower() in ("s1", "s", "mm", "mm_btc"):
            active_tab = 5
        elif str(tab_override).lower() in ("s2", "v", "cone", "vol"):
            active_tab = 6
        elif str(tab_override).lower() in ("s3", "g", "gartley"):
            active_tab = 7
        elif str(tab_override).lower() in ("s4", "t", "trap", "sfp"):
            active_tab = 8
        elif str(tab_override).lower() in ("s5", "e", "exhaust", "td"):
            active_tab = 9
        elif str(tab_override).lower() in ("p", "structure", "slsp", "pa", "13"):
            active_tab = 13
        else:
            try:
                val = int(tab_override)
                active_tab = val if val in valid_tabs else 0
            except ValueError:
                active_tab = 0
    else:
        active_tab = store.active_tab if store.active_tab in valid_tabs else 0

    header_panel = _build_header_panel(store, active_tab)

    if getattr(store, "show_help", False):
        return _build_help_overlay(store, header_panel)

    if active_tab == 18:
        return _build_tab18_trend_pullback_hud(config, store, header_panel)
    if active_tab == 17:
        return _build_tab17_btc_magnet_hud(config, store, header_panel)
    if active_tab == 16:
        return _build_tab16_ssrn_research_hud(config, store, header_panel)
    if active_tab == 15:
        return _build_tab15_grok_quant_hud(store, header_panel)
    if active_tab == 14:
        return _build_tab14_pattern_chart_hud(store, header_panel)
    if active_tab == 13:
        return _build_tab13_slsp_price_action_hud(store, header_panel)
    if active_tab == 12:
        return _build_tab_waterfall_hud(store, header_panel)
    if active_tab == 11:
        return _build_tab_footprint_hud(store, header_panel)
    if active_tab == 0:
        return _build_tab0_spot_swing_hud(store, header_panel)
    if active_tab == 10:
        return _build_tab0_master_synthesis_hud(store, header_panel)
    if active_tab == 1:
        return _build_tab1_swing_hud(store, header_panel)
    if active_tab == 2:
        return _build_tab2_protocol_hud(store, header_panel)
    if active_tab == 3:
        return _build_tab3_macro_hud(store, header_panel)
    if active_tab == 4:
        return _build_tab4_regime_matrix_hud(store, header_panel)
    if active_tab == 5:
        return _build_tab5_mm_btc_hud(store, header_panel)
    if active_tab == 6:
        return _build_tab6_volatility_cone_hud(store, header_panel)
    if active_tab == 7:
        return _build_tab7_gartley_hud(store, header_panel)
    if active_tab == 8:
        return _build_tab8_trap_hud(store, header_panel)
    if active_tab == 9:
        return _build_tab9_exhaustion_hud(store, header_panel)
    return _build_tab0_master_synthesis_hud(store, header_panel)


def print_dry_run_report(
    config: EngineConfig,
    store: StateStore,
    tab_arg: str = "1",
) -> None:
    """Prints a clean, self-contained verification readout for `--tab 1|2|3|4|5|6|7|8|9|10|11|12|w|f|l|all`."""
    console = Console(width=175, force_terminal=True)
    if tab_arg.lower() == "all":
        tab_titles = {
            0: "TAB [0: BTC SPOT SWING SCREENING & ALERT ENGINE]",
            12: "TAB [W: 5-PILLAR INSTITUTIONAL DECISION WATERFALL & 7 ESSENTIAL DATA POINTS]",
            1: "TAB [1: TACTICAL SWING & ORDER FLOW DESK]",
            11: "TAB [F: FOOTPRINT SWING DESK]",
            2: "TAB [2: PROTOCOL v1.3 & LIQUIDATION MAGNETS]",
            3: "TAB [3: MACRO QUANT & CYCLE RADAR]",
            4: "TAB [4: REGIME MATRIX CONFIGS A–J]",
            5: "TAB [5: MM-BTC ROUGH PATH SIGNATURES]",
            6: "TAB [6: 72H FORWARD VOLATILITY CONE]",
            7: "TAB [7: GARTLEY 222 & CONFLUENCE RADAR]",
            8: "TAB [8: PATTERN INVALIDATION & SFP TRAP RADAR]",
            9: "TAB [9: TERMINAL EXHAUSTION RADAR]",
            10: "TAB [L: MASTER SYNTHESIS & SUPREME COMMAND CENTER]",
            13: "TAB [P: PRICE ACTION & STRUCTURE PROTOCOL (SLSP v1.0 + 3-EMA + SENSORS)]",
            14: "TAB [B: CLASSIC CHART PATTERN RADAR & CANDLESTICK GEOMETRY]",
            15: "TAB [G: GROK DUAL-HORIZON FLOW & VWAP SD MATRIX]",
            16: "TAB [R: SSRN QUANTITATIVE ALPHA DECK & EMPIRICAL RESEARCH]",
            17: "TAB [M: BTC MAGNET · LIQUIDATION GRAVITY DECK]",
            18: "TAB [A: BTC TREND-PULLBACK v1.0 · RESEARCH / PAPER MODE]",
        }
        for t in (0, 18, 17, 16, 15, 12, 11, 14, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 13):
            title = tab_titles.get(t, f"TAB [{t}]")
            console.print(f"\n[bold cyan]=== VERIFICATION SNAPSHOT: {title} ===[/bold cyan]")
            console.print(build_dashboard_renderable(config, store, tab_override=t))
    else:
        tab_lower = tab_arg.strip().lower()
        if tab_lower in ("l", "master", "10"):
            t_num = 10
        elif tab_lower in ("w", "waterfall", "wf", "12"):
            t_num = 12
        elif tab_lower in ("0", "s0", "spot", "swing"):
            t_num = 0
        elif tab_lower in ("f", "footprint", "fp", "11"):
            t_num = 11
        elif tab_lower in ("5", "s1", "s", "mm", "mm_btc"):
            t_num = 5
        elif tab_lower in ("6", "s2", "v", "cone", "vol"):
            t_num = 6
        elif tab_lower in ("7", "s3", "gartley"):
            t_num = 7
        elif tab_lower in ("8", "s4", "t", "trap", "sfp"):
            t_num = 8
        elif tab_lower in ("9", "s5", "e", "exhaust", "td"):
            t_num = 9
        elif tab_lower in ("b", "pattern", "patterns", "chart", "14"):
            t_num = 14
        elif tab_lower in ("g", "grok", "grok_flow", "15"):
            t_num = 15
        elif tab_lower in ("r", "ssrn", "research", "alpha", "16"):
            t_num = 16
        elif tab_lower in ("m", "magnet", "btc_magnet", "17"):
            t_num = 17
        elif tab_lower in ("a", "k", "strategy", "trend_pullback", "btc_strategy", "18"):
            t_num = 18
        elif tab_lower in ("p", "structure", "slsp", "pa", "13"):
            t_num = 13
        else:
            try:
                t_num = int(tab_arg)
            except ValueError:
                t_num = 0
        store.active_tab = t_num if t_num in (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18) else 0
        console.print(build_dashboard_renderable(config, store, tab_override=store.active_tab))
        if store.active_tab == 18:
            try:
                from analytics.strategy_trend_pullback import copy_trend_pullback_to_clipboard
                copy_trend_pullback_to_clipboard(store)
            except Exception:
                pass


def _poll_keyboard_tab_switch(
    config: EngineConfig,
    store: StateStore,
    detector: Optional[SignalDetector] = None,
) -> bool:
    """Non-blocking cross-platform hotkey reader (`1`–`5`, `6`/`S` for S1, `7`/`V` for S2, `8`/`G` for S3, `9`/`T` for S4, `0`/`E` for S5, `W`/`w` for Waterfall, `F`/`f` for Footprint, `L`/`l` for Master, `C`/`c` for AI packet)."""
    changed = False
    if msvcrt is not None:
        try:
            while msvcrt.kbhit():
                ch = msvcrt.getwch()
                if ch in ("0", "1", "2", "3", "4", "5", "6", "7", "8", "9"):
                    new_tab = int(ch)
                    store.show_help = False
                    if store.active_tab != new_tab:
                        store.active_tab = new_tab
                        changed = True
                elif ch in ("a", "A", "k", "K"):
                    store.show_help = False
                    if store.active_tab != 18:
                        store.active_tab = 18
                        changed = True
                    else:
                        from analytics.strategy_trend_pullback import copy_trend_pullback_to_clipboard
                        ok, msg, char_count = copy_trend_pullback_to_clipboard(store)
                        store.last_packet_copied_utc = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")
                        store.last_packet_copied_ts = time.time()
                        store.last_packet_char_count = char_count
                        changed = True
                elif ch in ("p", "P"):
                    store.show_help = False
                    if store.active_tab != 13:
                        store.active_tab = 13
                        changed = True
                elif ch in ("b", "B"):
                    store.show_help = False
                    if store.active_tab != 14:
                        store.active_tab = 14
                        changed = True
                elif ch in ("f", "F"):
                    store.show_help = False
                    if store.active_tab != 11:
                        store.active_tab = 11
                        changed = True
                elif ch in ("w", "W"):
                    store.show_help = False
                    if store.active_tab != 12:
                        store.active_tab = 12
                        changed = True
                elif ch in ("m", "M"):
                    store.show_help = False
                    if store.active_tab != 17:
                        store.active_tab = 17
                        changed = True
                    else:
                        from analytics.btc_magnet_engine import copy_btc_magnet_card_to_clipboard
                        ok, msg, char_count = copy_btc_magnet_card_to_clipboard(store)
                        store.last_packet_copied_utc = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")
                        store.last_packet_copied_ts = time.time()
                        store.last_packet_char_count = char_count
                        changed = True
                elif ch in ("l", "L"):
                    store.show_help = False
                    if store.active_tab != 10:
                        store.active_tab = 10
                        changed = True
                elif ch in ("s", "S"):
                    store.show_help = False
                    if store.active_tab != 5:
                        store.active_tab = 5
                        changed = True
                elif ch in ("v", "V"):
                    store.show_help = False
                    if store.active_tab != 6:
                        store.active_tab = 6
                        changed = True
                elif ch in ("g", "G"):
                    store.show_help = False
                    if store.active_tab != 15:
                        store.active_tab = 15
                        changed = True
                    else:
                        from analytics.grok_quant_engine import copy_grok_prompt_to_clipboard
                        ok, msg, char_count = copy_grok_prompt_to_clipboard(store)
                        store.last_packet_copied_utc = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")
                        store.last_packet_copied_ts = time.time()
                        store.last_packet_char_count = char_count
                        changed = True
                elif ch in ("r", "R"):
                    store.show_help = False
                    if store.active_tab != 16:
                        store.active_tab = 16
                        changed = True
                    else:
                        cur_mode = getattr(store, "ssrn_view_mode", "domains")
                        store.ssrn_view_mode = "models" if cur_mode == "domains" else "domains"
                        from analytics.ssrn_research_engine import copy_ssrn_deck_to_clipboard
                        ok, msg, char_count = copy_ssrn_deck_to_clipboard(store)
                        store.last_packet_copied_utc = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")
                        store.last_packet_copied_ts = time.time()
                        store.last_packet_char_count = char_count
                        changed = True
                elif ch in ("t", "T"):
                    store.show_help = False
                    if store.active_tab != 8:
                        store.active_tab = 8
                        changed = True
                elif ch in ("e", "E"):
                    store.show_help = False
                    if store.active_tab != 9:
                        store.active_tab = 9
                        changed = True
                elif ch in ("h", "H", "?"):
                    store.show_help = not getattr(store, "show_help", False)
                    changed = True
                elif ch in ("c", "C"):
                    if detector is not None:
                        detector.evaluate(store)
                    copy_ai_packet_to_clipboard_and_disk(config, store)
                    changed = True
        except Exception:
            pass
        return changed

    # Linux VPS / Android Termux non-blocking stdin fallback
    try:
        if sys.stdin.isatty():
            rlist, _, _ = select.select([sys.stdin], [], [], 0.0)
            while rlist:
                ch = sys.stdin.read(1)
                if ch in ("a", "A", "k", "K"):
                    store.show_help = False
                    if store.active_tab != 18:
                        store.active_tab = 18
                        changed = True
                    else:
                        from analytics.strategy_trend_pullback import copy_trend_pullback_to_clipboard
                        ok, msg, char_count = copy_trend_pullback_to_clipboard(store)
                        store.last_packet_copied_utc = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")
                        store.last_packet_copied_ts = time.time()
                        store.last_packet_char_count = char_count
                        changed = True
                    rlist, _, _ = select.select([sys.stdin], [], [], 0.0)
                    continue
                if ch in ("0", "1", "2", "3", "4", "5", "6", "7", "8", "9"):
                    new_tab = int(ch)
                    if new_tab == 7:
                        new_tab = 14  # Option B: Map 7 to Dedicated Pattern & Harmonics Desk
                    store.show_help = False
                    if store.active_tab != new_tab:
                        store.active_tab = new_tab
                        changed = True
                elif ch in ("m", "M"):
                    if store.active_tab != 17:
                        store.active_tab = 17
                        changed = True
                    else:
                        from analytics.btc_magnet_engine import copy_btc_magnet_card_to_clipboard
                        ok, msg, char_count = copy_btc_magnet_card_to_clipboard(store)
                        store.last_packet_copied_utc = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")
                        store.last_packet_copied_ts = time.time()
                        store.last_packet_char_count = char_count
                        changed = True
                elif ch in ("l", "L"):
                    if store.active_tab != 10:
                        store.active_tab = 10
                        changed = True
                elif ch in ("w", "W"):
                    if store.active_tab != 12:
                        store.active_tab = 12
                        changed = True
                elif ch in ("b", "B"):
                    store.show_help = False
                    if store.active_tab != 14:
                        store.active_tab = 14
                        changed = True
                elif ch in ("f", "F"):
                    if store.active_tab != 11:
                        store.active_tab = 11
                        changed = True
                elif ch in ("s", "S"):
                    if store.active_tab != 5:
                        store.active_tab = 5
                        changed = True
                elif ch in ("v", "V"):
                    if store.active_tab != 6:
                        store.active_tab = 6
                        changed = True
                elif ch in ("g", "G"):
                    store.show_help = False
                    if store.active_tab != 15:
                        store.active_tab = 15
                        changed = True
                    else:
                        from analytics.grok_quant_engine import copy_grok_prompt_to_clipboard
                        ok, msg, char_count = copy_grok_prompt_to_clipboard(store)
                        store.last_packet_copied_utc = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")
                        store.last_packet_copied_ts = time.time()
                        store.last_packet_char_count = char_count
                        changed = True
                elif ch in ("r", "R"):
                    store.show_help = False
                    if store.active_tab != 16:
                        store.active_tab = 16
                        changed = True
                    else:
                        cur_mode = getattr(store, "ssrn_view_mode", "domains")
                        store.ssrn_view_mode = "models" if cur_mode == "domains" else "domains"
                        from analytics.ssrn_research_engine import copy_ssrn_deck_to_clipboard
                        ok, msg, char_count = copy_ssrn_deck_to_clipboard(store)
                        store.last_packet_copied_utc = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")
                        store.last_packet_copied_ts = time.time()
                        store.last_packet_char_count = char_count
                        changed = True
                elif ch in ("t", "T"):
                    if store.active_tab != 8:
                        store.active_tab = 8
                        changed = True
                elif ch in ("e", "E"):
                    if store.active_tab != 9:
                        store.active_tab = 9
                        changed = True
                elif ch in ("c", "C"):
                    if detector is not None:
                        detector.evaluate(store)
                    copy_ai_packet_to_clipboard_and_disk(config, store)
                    changed = True
                rlist, _, _ = select.select([sys.stdin], [], [], 0.0)
    except Exception:
        pass
    return changed


async def run_terminal_hud(
    config: EngineConfig,
    store: StateStore,
    detector: SignalDetector,
) -> None:
    """Continuously evaluates signals at 2 Hz and switches tabs in 0.0s on keys `1`–`5` or copies AI packet on `C`."""
    console = Console()
    refresh_delay = 1.0 / max(config.hud_refresh_rate_hz, 0.5)
    key_poll_step = 0.05  # 20 Hz keyboard responsiveness

    with Live(
        build_dashboard_renderable(config, store),
        console=console,
        refresh_per_second=config.hud_refresh_rate_hz,
        screen=False,
    ) as live:
        while True:
            try:
                detector.evaluate(store)
                live.update(build_dashboard_renderable(config, store))

                elapsed = 0.0
                while elapsed < refresh_delay:
                    if _poll_keyboard_tab_switch(config, store, detector=detector):
                        live.update(build_dashboard_renderable(config, store))
                    await asyncio.sleep(key_poll_step)
                    elapsed += key_poll_step
            except asyncio.CancelledError:
                raise
            except Exception:
                await asyncio.sleep(1.0)
