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
from datetime import datetime, timedelta, timezone
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
from rich.table import Table

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

    t1 = (
        "[bold black on cyan] [1: SWING] [/bold black on cyan]"
        if active_tab == 1
        else "[dim white][1: SWING][/dim white]"
    )
    t2 = (
        "[bold black on yellow] [2: PROTOCOL] [/bold black on yellow]"
        if active_tab == 2
        else "[dim white][2: PROTOCOL][/dim white]"
    )
    t3 = (
        "[bold black on magenta] [3: MACRO] [/bold black on magenta]"
        if active_tab == 3
        else "[dim white][3: MACRO][/dim white]"
    )
    t4 = (
        "[bold black on green] [4: REGIME] [/bold black on green]"
        if active_tab == 4
        else "[dim white][4: REGIME][/dim white]"
    )
    t5 = (
        "[bold white on blue] [5: MASTER] [/bold white on blue]"
        if active_tab == 5
        else "[dim white][5: MASTER][/dim white]"
    )
    ts1 = (
        "[bold black on white] [S1: MM-BTC] [/bold black on white]"
        if active_tab == 6
        else "[dim white][S1: MM-BTC][/dim white]"
    )
    ts2 = (
        "[bold black on bright_yellow] [S2: 72H CONE] [/bold black on bright_yellow]"
        if active_tab == 7
        else "[dim white][S2: 72H CONE][/dim white]"
    )
    ts3 = (
        "[bold black on magenta] [S3: GARTLEY] [/bold black on magenta]"
        if active_tab == 8
        else "[dim white][S3: GARTLEY][/dim white]"
    )
    ts4 = (
        "[bold black on bright_cyan] [S4: SFP TRAP] [/bold black on bright_cyan]"
        if active_tab == 9
        else "[dim white][S4: SFP TRAP][/dim white]"
    )
    ts5 = (
        "[bold black on bright_yellow] [S5: EXHAUST] [/bold black on bright_yellow]"
        if active_tab == 10
        else "[dim white][S5: EXHAUST][/dim white]"
    )

    regime_str = _regime_badge(sig.regime) if sig else "[dim]WARMING UP[/dim]"
    score_str = f"[bold]{sig.confluence_score:.1f}/100[/bold]" if sig else "0.0/100"

    # --- Panel 1: Desk Navigation & Quantitative Health ---
    nav_grid = Table.grid(expand=True)
    nav_grid.add_column(justify="left", no_wrap=True)
    nav_grid.add_column(justify="right", no_wrap=True)
    nav_grid.add_row(
        f"[bold white]BTC-USD[/bold white] | Spot: [bold cyan]${spot_px:,.2f}[/bold cyan] | Regime: {regime_str} ({score_str}) | Feeds: Spot {spot_ws_dot} • Perp {perp_ws_dot} • CB {cb_ws_dot}",
        f"[bold white]{now_utc.strftime('%Y-%m-%d %H:%M:%S UTC')}[/bold white]  •  [dim]Keys: 1-5 Core • 6-0 Spec • C: Copy[/dim]",
    )

    tab_grid = Table.grid(expand=True)
    tab_grid.add_column(justify="left", no_wrap=True)
    tab_grid.add_row(
        f"{t1}•{t2}•{t3}•{t4}•{t5}   |   {ts1}•{ts2}•{ts3}•{ts4}•{ts5}"
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
        title="[bold white]5. Executive Bottom Line (Plain-English Quick Glance — Press 1/2/3/4/5 to Switch Tabs)[/bold white]",
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

    return Group(header_panel, intro_panel, top_row, flow_panel, signal_panel, bottom_panel)


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
        title="[bold white]5. Executive Bottom Line Verdict (Protocol Sections 12–14 — Press 1/2/3/4/5 to Switch Tabs)[/bold white]",
        border_style=border_style,
        box=box.ROUNDED,
    )

    return Group(header_panel, intro_panel, top_row, ntz_panel, decision_panel, bottom_panel)


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
        title="[bold white]5. Executive Bottom Line (Macro & Cycle Quick Glance — Press 1/2/3/4/5 to Switch Tabs)[/bold white]",
        border_style=border_style,
        box=box.ROUNDED,
    )

    return Group(header_panel, intro_panel, top_row, sniper_panel, arb_panel, bottom_panel)


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
        title="[bold white]5. Executive Bottom Line (Config A–J Quick Glance — Press 1/2/3/4/5 to Switch Tabs)[/bold white]",
        border_style=border_style,
        box=box.ROUNDED,
    )

    return Group(header_panel, intro_panel, top_row, matrix_panel, playbook_panel, bottom_panel)


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


def _build_tab5_master_synthesis_hud(store: StateStore, header_panel: Panel) -> Group:
    """Renders Tab [5]: Master Synthesis & Supreme Order of Battle across Tabs [1]-[4]."""
    msev = store.master_synthesis_evaluation
    if msev is None:
        return Group(
            header_panel,
            Panel(
                "Warming up 4-Tab Master Synthesis Engine...",
                title="Tab [5]: Master Conclusion",
                box=box.ROUNDED,
            ),
        )

    # --- Introduction Card: Beginner Context & Methodology ---
    intro_lines = [
        "[bold cyan]▶ PURPOSE & SCOPE:[/bold cyan] Supreme command center harmonizing Tabs 1–4 into an institutional capital allocation verdict.",
        "[bold cyan]▶ CORE MODELS & FEEDS:[/bold cyan] Confluence Scoring Engine (0–100) • 4-Tab Arbiter Consensus • Dual-Track Allocation (Track A: Cash / Track B: In-Position).",
        "[bold cyan]▶ EXECUTION MANDATE:[/bold cyan] [bold green]The Supreme Signal Light[/bold green]: GREEN (Full Aggression), BLUE (Accumulate Support), AMBER (Caution / Tight Stops), RED (Risk-Off Liquidation).",
    ]
    intro_panel = Panel(
        "\n".join(intro_lines),
        title="[bold cyan]WELCOME TO TAB [5]: MASTER SYNTHESIS & SUPREME ORDER OF BATTLE DESK[/bold cyan]",
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
            "[bold black on yellow] [PRESS 'C' KEY: COPY RAW TELEMETRY PACKET (TABS 1–4) TO CLIPBOARD FOR GEMINI ARGON AI SECOND OPINION] [/bold black on yellow]"
        )

    p5_lines = [
        f"{headline}  {copy_btn_badge}",
        f"  [bold white]Master Synthesis :[/bold white] {msev.master_what_is_happening}",
        f"  [bold white]Conflict Ruling  :[/bold white] {msev.master_why_resolution}",
        f"  [bold white]Final Command    :[/bold white] [bold]{msev.master_final_command}[/bold]",
    ]
    bottom_panel = Panel(
        "\n".join(p5_lines),
        title="[bold white]5. Executive Bottom Line — Supreme Master Conclusion (Press 1/2/3/4/5 to Switch Tabs • Press C to Copy AI Data Packet)[/bold white]",
        border_style=border_style,
        box=box.ROUNDED,
    )

    return Group(header_panel, intro_panel, top_row, mid_row, bottom_panel)


# ============================================================================
# SPECIAL TAB [S1]: MULTI-MODEL BTC QUANT RADAR (MM-BTC)
# ============================================================================

def _build_tab_s1_mm_btc_hud(store: StateStore, header_panel: Panel) -> Group:
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
        title="[bold cyan]WELCOME TO SATELLITE TAB [S1]: MM-BTC ROUGH PATH SIGNATURES & 5 SENSORY LENSES[/bold cyan]",
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
        title="[bold white]5. MM-BTC Executive Action Plan (Press S/6 to Stay • 1/2/3/4/5 to Switch Tabs • Press C to Copy AI Data Packet)[/bold white]",
        border_style=p5_color,
        box=box.ROUNDED,
    )

    return Group(header_panel, intro_panel, top_row, mid_row, bottom_panel)


# ============================================================================
# SPECIAL TAB [S2]: 72-HOUR FORWARD VOLATILITY CONE & AI BENCHMARK RADAR
# ============================================================================

def _build_tab_s2_volatility_cone_hud(store: StateStore, header_panel: Panel) -> Group:
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
        title="[bold cyan]WELCOME TO SATELLITE TAB [S2]: 72-HOUR FORWARD VOLATILITY CONE & AI BENCHMARK DESK[/bold cyan]",
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

    return Group(header_panel, intro_panel, ribbon_table, mid_row, p3_panel, p4_panel)


# ============================================================================
# SPECIAL TAB [S3]: GARTLEY 222 & 5-STRATEGY CONFLUENCE RADAR
# ============================================================================

def _build_tab_s3_gartley_hud(store: StateStore, header_panel: Panel) -> Group:
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
        title="[bold cyan]WELCOME TO SATELLITE TAB [S3]: GARTLEY 222 & 5-STRATEGY CONFLUENCE RADAR (EXECUTION DESK)[/bold cyan]",
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

    return Group(header_panel, intro_panel, ribbon_table, mid_row, p3_panel, p4_panel)


# ============================================================================
# SPECIAL TAB [S4]: PATTERN INVALIDATION, LIQUIDITY SWEEP & SFP TRAP RADAR
# ============================================================================

def _build_tab_s4_trap_hud(store: StateStore, header_panel: Panel) -> Group:
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
        title="[bold cyan]WELCOME TO SATELLITE TAB [S4]: PATTERN INVALIDATION, LIQUIDITY SWEEP & SFP TRAP RADAR[/bold cyan]",
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
        title="[bold white]5. Executive Bottom Line & Action Playbook (Press 9/T for S4 • 8/G for S3 • 7/V for S2 • 6/S for S1 • 1–5 for Core • C to Copy)[/bold white]",
        border_style=border_col,
        box=box.ROUNDED,
    )

    return Group(header_panel, intro_panel, ribbon_table, mid_row_1, mid_row_2, p4_diag_panel, p5_panel)




# ============================================================================
# TAB [S5]: TERMINAL EXHAUSTION & DELTA DIVERGENCE RADAR HUD
# ============================================================================

def _build_tab_s5_exhaustion_hud(store: StateStore, header_panel: Panel) -> Group:
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
        title="[bold cyan]WELCOME TO SATELLITE TAB [S5]: TERMINAL EXHAUSTION & DELTA DIVERGENCE RADAR[/bold cyan]",
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

    return Group(header_panel, intro_panel, ribbon_table, mid_row, p3_panel, p4_panel)




# ============================================================================
# PUBLIC DISPATCHERS & LIVE INTERACTIVE LOOP
# ============================================================================

def build_dashboard_renderable(
    config: EngineConfig,
    store: StateStore,
    tab_override: Optional[int] = None,
) -> Group:
    """Builds the active tab's 5-panel Rich renderable for the live terminal HUD."""
    active_tab = tab_override if tab_override in (1, 2, 3, 4, 5, 6, 7, 8, 9, 10) else store.active_tab
    header_panel = _build_header_panel(store, active_tab)

    if active_tab == 2:
        return _build_tab2_protocol_hud(store, header_panel)
    if active_tab == 3:
        return _build_tab3_macro_hud(store, header_panel)
    if active_tab == 4:
        return _build_tab4_regime_matrix_hud(store, header_panel)
    if active_tab == 5:
        return _build_tab5_master_synthesis_hud(store, header_panel)
    if active_tab == 6:
        return _build_tab_s1_mm_btc_hud(store, header_panel)
    if active_tab == 7:
        return _build_tab_s2_volatility_cone_hud(store, header_panel)
    if active_tab == 8:
        return _build_tab_s3_gartley_hud(store, header_panel)
    if active_tab == 9:
        return _build_tab_s4_trap_hud(store, header_panel)
    if active_tab == 10:
        return _build_tab_s5_exhaustion_hud(store, header_panel)
    return _build_tab1_swing_hud(store, header_panel)


def print_dry_run_report(
    config: EngineConfig,
    store: StateStore,
    tab_arg: str = "1",
) -> None:
    """Prints a clean, self-contained verification readout for `--tab 1|2|3|4|5|6|7|8|9|10|s1|s2|s3|s4|s5|all`."""
    console = Console(width=175, force_terminal=True)
    if tab_arg.lower() == "all":
        for t in (1, 2, 3, 4, 5, 6, 7, 8, 9, 10):
            if t <= 5:
                title = f"TAB [{t}]"
            elif t == 6:
                title = "TAB [S1: MM-BTC QUANT RADAR]"
            elif t == 7:
                title = "TAB [S2: 72-HOUR VOLATILITY CONE & AI BENCHMARK]"
            elif t == 8:
                title = "TAB [S3: GARTLEY 222 & 5-STRATEGY CONFLUENCE]"
            elif t == 9:
                title = "TAB [S4: PATTERN INVALIDATION & SFP TRAP RADAR]"
            else:
                title = "TAB [S5: TERMINAL EXHAUSTION & DELTA DIVERGENCE RADAR]"
            console.print(f"\n[bold cyan]=== VERIFICATION SNAPSHOT: {title} ===[/bold cyan]")
            console.print(build_dashboard_renderable(config, store, tab_override=t))
    else:
        tab_lower = tab_arg.strip().lower()
        if tab_lower in ("s1", "s", "6"):
            t_num = 6
        elif tab_lower in ("s2", "v", "7"):
            t_num = 7
        elif tab_lower in ("s3", "g", "8"):
            t_num = 8
        elif tab_lower in ("s4", "t", "9"):
            t_num = 9
        elif tab_lower in ("s5", "e", "0", "10"):
            t_num = 10
        else:
            try:
                t_num = int(tab_arg)
            except ValueError:
                t_num = 1
        store.active_tab = t_num if t_num in (1, 2, 3, 4, 5, 6, 7, 8, 9, 10) else 1
        console.print(build_dashboard_renderable(config, store, tab_override=store.active_tab))


def _poll_keyboard_tab_switch(
    config: EngineConfig,
    store: StateStore,
    detector: Optional[SignalDetector] = None,
) -> bool:
    """Non-blocking cross-platform hotkey reader (`1`–`5`, `6`/`S` for S1, `7`/`V` for S2, `8`/`G` for S3, `9`/`T` for S4, `0`/`E` for S5, `C`/`c` for AI packet)."""
    changed = False
    if msvcrt is not None:
        try:
            while msvcrt.kbhit():
                ch = msvcrt.getwch()
                if ch in ("1", "2", "3", "4", "5", "6", "7", "8", "9"):
                    new_tab = int(ch)
                    if store.active_tab != new_tab:
                        store.active_tab = new_tab
                        changed = True
                elif ch == "0":
                    if store.active_tab != 10:
                        store.active_tab = 10
                        changed = True
                elif ch in ("s", "S"):
                    if store.active_tab != 6:
                        store.active_tab = 6
                        changed = True
                elif ch in ("v", "V"):
                    if store.active_tab != 7:
                        store.active_tab = 7
                        changed = True
                elif ch in ("g", "G"):
                    if store.active_tab != 8:
                        store.active_tab = 8
                        changed = True
                elif ch in ("t", "T"):
                    if store.active_tab != 9:
                        store.active_tab = 9
                        changed = True
                elif ch in ("e", "E"):
                    if store.active_tab != 10:
                        store.active_tab = 10
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
                if ch in ("1", "2", "3", "4", "5", "6", "7", "8", "9"):
                    new_tab = int(ch)
                    if store.active_tab != new_tab:
                        store.active_tab = new_tab
                        changed = True
                elif ch == "0":
                    if store.active_tab != 10:
                        store.active_tab = 10
                        changed = True
                elif ch in ("s", "S"):
                    if store.active_tab != 6:
                        store.active_tab = 6
                        changed = True
                elif ch in ("v", "V"):
                    if store.active_tab != 7:
                        store.active_tab = 7
                        changed = True
                elif ch in ("g", "G"):
                    if store.active_tab != 8:
                        store.active_tab = 8
                        changed = True
                elif ch in ("t", "T"):
                    if store.active_tab != 9:
                        store.active_tab = 9
                        changed = True
                elif ch in ("e", "E"):
                    if store.active_tab != 10:
                        store.active_tab = 10
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
