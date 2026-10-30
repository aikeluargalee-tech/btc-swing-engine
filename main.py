"""Main asyncio orchestrator for the Long-Only BTC-USD Spot Swing Microstructure & Auction Engine."""

import argparse
import asyncio
import logging
import sys
from typing import List

from rich.console import Console

from analytics.ai_packet_exporter import copy_ai_packet_to_clipboard_and_disk
from analytics.signal_detector import SignalDetector
from collectors import (
    poll_rest_metrics,
    run_initial_warmup,
    stream_binance_perp,
    stream_binance_spot,
    stream_coinbase_spot,
)
from config.settings import DEFAULT_CONFIG, EngineConfig
from core.state_store import StateStore
from ui.terminal_hud import print_dry_run_report, run_terminal_hud


def _configure_stdio() -> None:
    """Ensures UTF-8 console encoding on Windows terminals."""
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    if hasattr(sys.stderr, "reconfigure"):
        try:
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass


async def _run_engine(
    config: EngineConfig,
    dry_run: bool = False,
    duration: float = 15.0,
    tab_arg: str = "1",
    copy_packet: bool = False,
) -> None:
    """Initializes historical backfill, starts concurrent WebSocket/REST streams, and runs the HUD."""
    console = Console(force_terminal=True)
    store = StateStore()
    if tab_arg in ("1", "2", "3", "4", "5", "6", "7", "8", "9"):
        store.active_tab = int(tab_arg)
    elif tab_arg in ("0", "10"):
        store.active_tab = 10
    elif tab_arg.lower() in ("s1", "s"):
        store.active_tab = 6
    elif tab_arg.lower() in ("s2", "v"):
        store.active_tab = 7
    elif tab_arg.lower() in ("s3", "g"):
        store.active_tab = 8
    elif tab_arg.lower() in ("s4", "t"):
        store.active_tab = 9
    elif tab_arg.lower() in ("s5", "e"):
        store.active_tab = 10
    detector = SignalDetector(config)

    console.print(
        "[bold cyan][1/3] Running Zero-Cold-Start Historical Backfill "
        "(1W/1D Macro & Protocol Candles, 30D/7D Spot & Perp Klines, 4H OI, Funding & Coinbase Basis)...[/bold cyan]"
    )
    await run_initial_warmup(config, store)
    detector.evaluate(store)

    console.print(
        f"[bold green][2/3] Warmup complete![/bold green] "
        f"Loaded {len(store.spot_klines_1w)}x 1W bars, "
        f"{len(store.spot_klines_1d)}x 1D bars, "
        f"{len(store.spot_klines_1h)}x 1H Spot bars, "
        f"{len(store.perp_klines_1h)}x 1H Perp bars, "
        f"{len(store.spot_klines_15m)}x 15m bars."
    )

    background_tasks: List[asyncio.Task] = [
        asyncio.create_task(stream_binance_spot(config, store), name="binance_spot_ws"),
        asyncio.create_task(stream_binance_perp(config, store), name="binance_perp_ws"),
        asyncio.create_task(stream_coinbase_spot(config, store), name="coinbase_spot_ws"),
        asyncio.create_task(poll_rest_metrics(config, store), name="rest_metrics_poller"),
    ]

    try:
        if dry_run:
            console.print(
                f"[bold yellow][3/3] Dry-Run Mode: Streaming live WebSocket order flow "
                f"(Binance Spot, Perp & Coinbase) for {duration:.0f} seconds...[/bold yellow]"
            )
            steps = max(1, int(duration))
            for _ in range(steps):
                await asyncio.sleep(1.0)
                detector.evaluate(store)

            if copy_packet:
                copy_ai_packet_to_clipboard_and_disk(config, store)

            print_dry_run_report(config, store, tab_arg=tab_arg)
            console.print(
                f"\n[bold green]Verification Complete![/bold green] "
                f"Structured JSONL signal state written to: [underline]{config.signal_log_path}[/underline]"
            )
        else:
            console.print(
                "[bold green][3/3] Launching Unified Live Terminal HUD "
                "(Press [bold cyan]1[/bold cyan]=Swing Engine, [bold yellow]2[/bold yellow]=Protocol v1.3, "
                "[bold magenta]3[/bold magenta]=Macro Radar, [bold green]4[/bold green]=Regime Matrix A–J, "
                "[bold blue]5[/bold blue]=Master Conclusion, [bold white]S/6[/bold white]=MM-BTC Quant Radar, "
                "[bold bright_yellow]V/7[/bold bright_yellow]=72H Volatility Cone, [bold yellow]C[/bold yellow]=Copy AI Data Packet)...[/bold green]"
            )
            await run_terminal_hud(config, store, detector)
    finally:
        for task in background_tasks:
            task.cancel()
        await asyncio.gather(*background_tasks, return_exceptions=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Long-Only Bitcoin (BTC-USD) Spot Swing Microstructure & Auction Engine"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Connect to all REST/WebSocket feeds, stream live order flow for 15s, print full audit report, and exit.",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=15.0,
        help="Duration in seconds for --dry-run live stream verification (default: 15).",
    )
    parser.add_argument(
        "--tab",
        type=str,
        default="1",
        choices=["1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "10", "s1", "S1", "s2", "S2", "s3", "S3", "s4", "S4", "s5", "S5", "v", "V", "g", "G", "t", "T", "e", "E", "all"],
        help="Initial active HUD tab (1=Swing Engine, 2=Protocol v1.3, 3=Macro Radar, 4=Regime Matrix A-J, 5=Master Conclusion, 6/s1=MM-BTC, 7/s2=72H Cone, 8/s3=Gartley, 9/s4=SFP Trap, 0/s5=Terminal Exhaustion, or 'all').",
    )
    parser.add_argument(
        "--copy-packet",
        action="store_true",
        help="Copy the full Raw Telemetry & AI Audit Packet (Tabs 1-4) to the Windows Clipboard during --dry-run.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable verbose debug logging.",
    )
    return parser.parse_args()


def main() -> None:
    _configure_stdio()
    args = parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.WARNING,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    try:
        asyncio.run(
            _run_engine(
                DEFAULT_CONFIG,
                dry_run=args.dry_run,
                duration=args.duration,
                tab_arg=args.tab,
                copy_packet=args.copy_packet,
            )
        )
    except KeyboardInterrupt:
        print("\nBTC Swing Engine terminated by user.")
        sys.exit(0)


if __name__ == "__main__":
    main()
