"""Grok Bot Cloud Runner — Bitcoin Quantitative Swing Engine.

Autonomous on-demand CLI entrypoint for Grok Bot / cloud containers.
Fetches public market telemetry (Binance + Coinbase), evaluates all 10 desks
(Tabs 1-5 + Satellites S1-S5), and exports the full quantitative audit packet.
"""

import argparse
import asyncio
import os
import pathlib
import sys
import time

from config.settings import DEFAULT_CONFIG
from core.state_store import StateStore
from collectors.warmup_loader import run_initial_warmup
from analytics.signal_detector import SignalDetector
from analytics.ai_packet_exporter import build_ai_telemetry_packet


async def execute_engine(print_packet: bool = False, output_file: str = "BTC_AI_DATA_PACKET_LATEST.md") -> int:
    t0 = time.perf_counter()
    config = DEFAULT_CONFIG
    store = StateStore()

    print("[1/3] Fetching public market telemetry (Binance Spot, Binance Perp, Coinbase Spot)...")
    await run_initial_warmup(config, store)

    print("[2/3] Evaluating 10-Desk Quantitative Brain (Tabs 1-5 & Satellites S1-S5)...")
    detector = SignalDetector(config)
    sig = detector.evaluate(store)

    packet_md = build_ai_telemetry_packet(config, store)

    out_path = pathlib.Path(output_file)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(packet_md)

    elapsed = time.perf_counter() - t0

    msev = store.master_synthesis_evaluation
    spot_price = store.binance_spot_price
    traffic_light = msev.master_traffic_light if msev else "BLUE"
    score = sig.confluence_score if sig else 0.0
    gate = sig.gate_state.value if sig else "N/A"
    regime = sig.regime.value if sig else "ROTATION"
    track_a = msev.cash_permission if msev else "MONITOR"
    track_b = msev.holder_action if msev else "HOLD"

    print("\n" + "=" * 80)
    print("  BTC QUANTITATIVE SWING DESK — ON-DEMAND ENGINE RUN COMPLETE")
    print("=" * 80)
    print(f"  Execution Time    : {elapsed:.2f} seconds")
    print(f"  Bitcoin Spot Price: ${spot_price:,.2f}")
    print(f"  Market Regime     : {regime}")
    print(f"  Tab 1 Confluence  : {score:.1f}/100 | Gate: {gate}")
    print(f"  Tab 5 Verdict     : [{traffic_light}] LIGHT — {msev.master_headline if msev else 'READY'}")
    print(f"  Track A (In Cash) : {track_a}")
    print(f"  Track B (Holding) : {track_b}")
    print(f"  Telemetry Packet  : Saved to {out_path.resolve()} ({len(packet_md.splitlines())} lines)")
    print("=" * 80 + "\n")

    if print_packet:
        print(packet_md)

    return 0


def main():
    parser = argparse.ArgumentParser(description="Grok Bot On-Demand Quantitative Runner")
    parser.add_argument("--output", type=str, default="BTC_AI_DATA_PACKET_LATEST.md", help="Output Markdown path")
    parser.add_argument("--print", action="store_true", help="Print full telemetry packet to stdout")
    args = parser.parse_args()

    sys.exit(asyncio.run(execute_engine(print_packet=args.print, output_file=args.output)))


if __name__ == "__main__":
    main()
