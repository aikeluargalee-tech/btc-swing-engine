"""Grok Bot Cloud Runner — Bitcoin Quantitative Swing Engine.

Autonomous on-demand CLI entrypoint for Grok Bot / cloud containers.
Fetches public market telemetry (Binance + Coinbase), gathers macro/intermarket data,
evaluates all 10 desks (Tabs 1-5 + Satellites S1-S5), and exports the full quantitative
audit packet including Section 12 Consolidated Protocol Metrics Dossier.

Overhaul v1 (2026-11-07): Also emits a stable machine-readable verdict contract
at state/verdict.json (and root mirror) for reliable Grok Bot consumption.
"""

import argparse
import asyncio
import json
import logging
import os
import pathlib
import sys
import time
from datetime import datetime, timezone

import aiohttp

from config.settings import DEFAULT_CONFIG
from core.state_store import StateStore
from collectors.warmup_loader import run_initial_warmup
from collectors.macro_collector import fetch_macro_and_intermarket_snapshot
from analytics.signal_detector import SignalDetector
from analytics.protocol_dossier import compute_protocol_metrics_dossier
from analytics.ai_packet_exporter import build_ai_telemetry_packet


def _assess_data_quality(store, macro_snap) -> str:
    """Simple first-pass data quality flag for the verdict contract."""
    issues = []
    if not store.binance_spot_price or store.binance_spot_price <= 0:
        issues.append("no_spot_price")
    if not getattr(store, "spot_klines_1d", None) or len(store.spot_klines_1d) < 50:
        issues.append("insufficient_daily_bars")
    if macro_snap is None or macro_snap.fear_and_greed_score is None:
        issues.append("macro_partial")
    if len(issues) >= 2:
        return "insufficient"
    if issues:
        return "degraded"
    return "good"


def _build_verdict(store, sig, macro_snap, elapsed: float) -> dict:
    """Build the stable machine-readable verdict contract."""
    msev = store.master_synthesis_evaluation
    spot_price = store.binance_spot_price or 0.0
    traffic_light = msev.master_traffic_light if msev else "BLUE"
    score = sig.confluence_score if sig else 0.0
    gate = sig.gate_state.value if sig else "N/A"
    regime = sig.regime.value if sig else "ROTATION"
    track_a = msev.cash_permission if msev else "MONITOR"
    track_b = msev.holder_action if msev else "HOLD"
    headline = msev.master_headline if msev else "READY"

    def _first_positive(*values):
        for v in values:
            if v is None:
                continue
            try:
                f = float(v)
            except (TypeError, ValueError):
                continue
            if f > 0:
                return round(f, 2)
        return None

    def _attr_num(obj, *names):
        if obj is None:
            return None
        return _first_positive(*(getattr(obj, name, None) for name in names))

    # Extract key levels from TradePlan real field names
    # (entry_zone_low/high, reference_entry, stop_loss, tp1_poc, tp2_vah)
    entry_zone = None
    stop = None
    tp1 = None
    tp2 = None
    if sig and getattr(sig, "trade_plan", None):
        tp = sig.trade_plan
        low = _attr_num(tp, "entry_zone_low")
        high = _attr_num(tp, "entry_zone_high")
        ref = _attr_num(tp, "reference_entry", "entry_zone")
        if low is not None and high is not None:
            entry_zone = [low, high]
        else:
            entry_zone = ref
        stop = _attr_num(
            tp,
            "stop_loss",
            "hard_invalidation_stop",
            "hard_invalidation",
            "invalidation_stop",
            "stop",
        )
        tp1 = _attr_num(tp, "tp1_poc", "tp1_price", "take_profit_1", "tp1")
        tp2 = _attr_num(tp, "tp2_vah", "tp2_price", "take_profit_2", "tp2")

    data_quality = _assess_data_quality(store, macro_snap)

    # Confidence proxy: blend confluence score and data quality
    quality_mult = {"good": 1.0, "degraded": 0.7, "insufficient": 0.3}[data_quality]
    confidence = round(min(1.0, (score / 100.0) * quality_mult), 3)

    # Short action recommendation derived only from engine outputs
    if data_quality == "insufficient":
        action = "NO_TRADE — insufficient data quality"
    elif traffic_light in ("RED", "YELLOW") or track_a in ("MONITOR", "WAIT", "NO_TRADE"):
        action = f"WAIT / {track_a}"
    elif traffic_light == "GREEN":
        action = "CONSIDER ENTRY per Track A levels"
    else:
        action = f"MONITOR — {track_a}"

    return {
        "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "runtime_seconds": round(elapsed, 2),
        "price": round(spot_price, 2),
        "data_quality": data_quality,
        "traffic_light": traffic_light,
        "master_headline": headline,
        "regime": regime,
        "confluence_score": round(score, 1),
        "gate_state": gate,
        "track_a": track_a,
        "track_b": track_b,
        "key_levels": {
            "entry_zone": entry_zone,
            "stop": stop,
            "tp1": tp1,
            "tp2": tp2,
        },
        "confidence": confidence,
        "bot_action_recommendation": action,
        "macro_snapshot": {
            "fear_and_greed": getattr(macro_snap, "fear_and_greed_score", None),
            "sp500_change_1d_pct": getattr(macro_snap, "sp500_change_1d_pct", None),
            "btc_spx_corr_20d": getattr(macro_snap, "btc_spx_corr_20d", None),
            "dxy": getattr(macro_snap, "dxy_index", None),
            "brent": getattr(macro_snap, "brent_crude_price", None),
        },
    }


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

    print("[3/4] Evaluating 10-Desk Quantitative Brain (Tab 0 Master & Specialist Desks 1–9)...")
    detector = SignalDetector(config)
    detector.spot_swing_engine.set_read_only(True)  # cloud snapshot: no state writes, no alerts
    sig = detector.evaluate(store)

    print("[4/4] Compiling Consolidated Protocol Metrics Dossier & Exporting AI Packet...")
    dossier = compute_protocol_metrics_dossier(config, store, macro_snap)
    store.protocol_dossier = dossier

    # Export structured JSON metrics
    json_path = pathlib.Path(json_output)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as jf:
        json.dump(dossier, jf, indent=2)

    # Mirror to btc_metrics_latest.json for Bot A1–A14 Handover compatibility
    for alt_name in ("btc_metrics_latest.json", "data/btc_metrics_latest.json"):
        try:
            alt_path = pathlib.Path(alt_name)
            alt_path.parent.mkdir(parents=True, exist_ok=True)
            with open(alt_path, "w", encoding="utf-8") as ajf:
                json.dump(dossier, ajf, indent=2)
        except Exception:
            pass

    # Export full Markdown packet
    packet_md = build_ai_telemetry_packet(config, store)
    out_path = pathlib.Path(output_file)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(packet_md)

    elapsed = time.perf_counter() - t0

    # ---- New: stable machine-readable verdict contract ----
    verdict = _build_verdict(store, sig, macro_snap, elapsed)
    state_dir = pathlib.Path("state")
    state_dir.mkdir(parents=True, exist_ok=True)
    verdict_path = state_dir / "verdict.json"
    with open(verdict_path, "w", encoding="utf-8") as vf:
        json.dump(verdict, vf, indent=2)
    # Root mirror for easy bot discovery
    with open("verdict.json", "w", encoding="utf-8") as vf:
        json.dump(verdict, vf, indent=2)

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
    print(f"  Tab 0 Master Verdict: [{traffic_light}] LIGHT — {msev.master_headline if msev else 'READY'}")
    print(f"  Track A (In Cash)   : {track_a}")
    print(f"  Track B (Holding)   : {track_b}")
    print(f"  Data Quality        : {verdict['data_quality']} | Confidence: {verdict['confidence']}")
    print(f"  Bot Action          : {verdict['bot_action_recommendation']}")
    print("  " + "-" * 76)
    print("  MACRO & INTERMARKET TELEMETRY HIGHLIGHTS:")
    print(f"  * Crypto Fear & Greed : {fng_str}")
    print(f"  * S&P 500 Performance : {spx_str} | BTC-SPX Corr (20d): {corr_str}")
    print(f"  * DXY US Dollar Index : {dxy_str} | Brent Crude: {brent_str}")
    print("  " + "-" * 76)
    print(f"  Telemetry Packet    : Saved to {out_path.resolve()} ({len(packet_md.splitlines())} lines)")
    print(f"  JSON Metrics Dossier: Saved to {json_path.resolve()}")
    print(f"  Verdict Contract    : Saved to {verdict_path.resolve()} and ./verdict.json")
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
