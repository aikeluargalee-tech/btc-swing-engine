"""Grok Bot Cloud Runner — Bitcoin Quantitative Swing Engine.

Autonomous on-demand CLI entrypoint for Grok Bot / cloud containers.
Fetches public market telemetry (Binance + Coinbase), gathers macro/intermarket data,
evaluates all 10 desks (Tabs 1-5 + Satellites S1-S5), and exports the full quantitative
audit packet including Section 12 Consolidated Protocol Metrics Dossier.
"""

import argparse
import asyncio
import json
import logging
import os
import pathlib
import sys
import time

import aiohttp

from config.settings import DEFAULT_CONFIG
from core.state_store import StateStore
from collectors.warmup_loader import run_initial_warmup
from collectors.macro_collector import fetch_macro_and_intermarket_snapshot
from analytics.signal_detector import SignalDetector
from analytics.protocol_dossier import compute_protocol_metrics_dossier
from analytics.ai_packet_exporter import build_ai_telemetry_packet


async def execute_engine(
    print_packet: bool = False,
    output_file: str = "BTC_AI_DATA_PACKET_LATEST.md",
    json_output: str = "data/protocol_metrics.json",
) -> int:
    t0 = time.perf_counter()
    config = DEFAULT_CONFIG
    store = StateStore()

    print("[1/4] Fetching public crypto market telemetry (Binance Spot, Binance Perp, Coinbase Spot)...")
    await run_initial_warmup(config, store)

    print("[2/4] Fetching Macro & Intermarket Telemetry (Brent Crude, DXY, S&P 500, Nasdaq, VIX, F&G, Depth, Correlations)...")
    daily_closes = [b.close for b in store.spot_klines_1d]
    async with aiohttp.ClientSession() as session:
        macro_snap = await fetch_macro_and_intermarket_snapshot(session, daily_closes)
    store.macro_intermarket = macro_snap

    print("[3/4] Evaluating 10-Desk Quantitative Brain (Tabs 1-5 & Satellites S1-S5)...")
    detector = SignalDetector(config)
    sig = detector.evaluate(store)

    print("[4/4] Compiling Consolidated Protocol Metrics Dossier & Exporting AI Packet...")
    dossier = compute_protocol_metrics_dossier(config, store, macro_snap)
    store.protocol_dossier = dossier

    # Export structured JSON metrics
    json_path = pathlib.Path(json_output)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as jf:
        json.dump(dossier, jf, indent=2)

    # Export full Markdown packet
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

    fng_str = f"{macro_snap.fear_and_greed_score}/100 ({macro_snap.fear_and_greed_classification})" if macro_snap.fear_and_greed_score is not None else "N/A"
    spx_str = f"${macro_snap.sp500_price:,.2f} ({macro_snap.sp500_change_1d_pct:+.2f}%)" if macro_snap.sp500_price is not None else "N/A"
    corr_str = f"{macro_snap.btc_spx_corr_20d:+.3f}" if macro_snap.btc_spx_corr_20d is not None else "N/A"
    dxy_str = f"{macro_snap.dxy_index:.2f}" if macro_snap.dxy_index is not None else "N/A"
    brent_str = f"${macro_snap.brent_crude_price:.2f}" if macro_snap.brent_crude_price is not None else "N/A"

    print("\n" + "=" * 80)
    print("  BTC QUANTITATIVE SWING DESK — ON-DEMAND ENGINE RUN COMPLETE")
    print("=" * 80)
    print(f"  Execution Time      : {elapsed:.2f} seconds")
    print(f"  Bitcoin Spot Price  : ${spot_price:,.2f}")
    print(f"  Market Regime       : {regime}")
    print(f"  Tab 1 Confluence    : {score:.1f}/100 | Gate: {gate}")
    print(f"  Tab 5 Verdict       : [{traffic_light}] LIGHT — {msev.master_headline if msev else 'READY'}")
    print(f"  Track A (In Cash)   : {track_a}")
    print(f"  Track B (Holding)   : {track_b}")
    print("  " + "-" * 76)
    print("  MACRO & INTERMARKET TELEMETRY HIGHLIGHTS:")
    print(f"  * Crypto Fear & Greed : {fng_str}")
    print(f"  * S&P 500 Performance : {spx_str} | BTC-SPX Corr (20d): {corr_str}")
    print(f"  * DXY US Dollar Index : {dxy_str} | Brent Crude: {brent_str}")
    print("  " + "-" * 76)
    print(f"  Telemetry Packet    : Saved to {out_path.resolve()} ({len(packet_md.splitlines())} lines)")
    print(f"  JSON Metrics Dossier: Saved to {json_path.resolve()}")
    print("=" * 80 + "\n")

    if print_packet:
        print(packet_md)

    return 0


def main():
    parser = argparse.ArgumentParser(description="Grok Bot On-Demand Quantitative Runner")
    parser.add_argument("--output", type=str, default="BTC_AI_DATA_PACKET_LATEST.md", help="Output Markdown path")
    parser.add_argument("--json", type=str, default="data/protocol_metrics.json", help="Output JSON path")
    parser.add_argument("--print", action="store_true", help="Print full telemetry packet to stdout")
    args = parser.parse_args()

    sys.exit(asyncio.run(execute_engine(print_packet=args.print, output_file=args.output, json_output=args.json)))


if __name__ == "__main__":
    main()
