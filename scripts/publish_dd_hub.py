"""Headless Tab [21: D] Unified Data Hub publisher for GitHub Actions, GitHub Pages, and Telegram.

Executes a zero-cold-start REST/macro warmup, evaluates all upstream signal engines
in read-only mode, persists closed-4H snapshots into `data/dd_telemetry_history.sqlite`,
publishes static dashboard artifacts under `docs/` (`index.html`, `dd_latest.json`,
`btc_data_hub_latest.md`), and optionally delivers split reports + `.md` attachment to Telegram.
"""

from __future__ import annotations

import argparse
import asyncio
import html
import json
import logging
import os
import pathlib
import shutil
import socket
import sqlite3
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Sequence, Tuple

import aiohttp

BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from analytics.data_hub_engine import (  # noqa: E402
    DEFAULT_ARCHIVE_DB_PATH,
    DataHubEngine,
    DataHubEvaluation,
    DataMetricRow,
)
from analytics.data_only_reports import (  # noqa: E402
    _summarize_kline_structure,
    build_tab_d_data_only_report,
    evaluate_hard_market_veto,
)
from analytics.signal_detector import SignalDetector  # noqa: E402
from collectors.warmup_loader import run_initial_warmup  # noqa: E402
from config.settings import DEFAULT_CONFIG, EngineConfig  # noqa: E402
from core.state_store import StateStore  # noqa: E402

logger = logging.getLogger("publish_dd_hub")
SGT_TZ = timezone(timedelta(hours=8))
TELEGRAM_MAX_LEN = 3900

PANEL_SPECS: Tuple[Tuple[str, str, str], ...] = (
    ("1_price_trend_structure", "1. PRICE, TREND & MARKET STRUCTURE", "panel_1_feeds"),
    ("2_order_flow_liquidity", "2. ORDER FLOW, FOOTPRINT & LIQUIDITY", "panel_2_trend_vol"),
    ("3_derivatives_options_liq", "3. DERIVATIVES, OPTIONS & LIQUIDATIONS", "panel_3_structure_magnets"),
    ("4_onchain_etf_stablecoins", "4. ON-CHAIN, ETF & STABLECOIN FLOWS", "panel_4_flow_quant"),
    ("5_macro_credit_liquidity", "5. MACRO, CREDIT & US LIQUIDITY", "panel_5_derivs_liq"),
    ("6_quant_feeds_archive", "6. QUANT FEATURES, FEED HEALTH & ARCHIVE", "panel_6_macro_onchain"),
)


def query_recent_archive(db_path: pathlib.Path, limit: int = 30) -> List[Dict[str, Any]]:
    """Reads the latest closed-4H snapshots from the SQLite archive (fail-soft)."""
    if not db_path.exists():
        return []
    conn: Optional[sqlite3.Connection] = None
    try:
        conn = sqlite3.connect(str(db_path), timeout=2.0)
        rows = conn.execute(
            """
            SELECT closed_4h_bar_utc, retrieval_utc, spot_price,
                   ok_count, unavailable_count, stale_count, proxy_or_static_count
            FROM telemetry_snapshots
            ORDER BY closed_4h_bar_utc DESC
            LIMIT ?
            """,
            (int(limit),),
        ).fetchall()
        return [
            {
                "closed_4h_bar_utc": str(r[0]),
                "retrieval_utc": str(r[1]),
                "spot_price": float(r[2]),
                "ok_count": int(r[3]),
                "unavailable_count": int(r[4]),
                "stale_count": int(r[5]),
                "proxy_or_static_count": int(r[6]),
            }
            for r in rows
        ]
    except sqlite3.Error as exc:
        logger.debug("Archive query skipped: %s", exc)
        return []
    finally:
        if conn is not None:
            conn.close()


def _serialize_rows(rows: Sequence[DataMetricRow]) -> List[Dict[str, str]]:
    return [
        {"label": r.label, "value": r.value, "tabs": r.tabs, "status": r.status}
        for r in rows
    ]


def _compute_stale_breakdown(ev: DataHubEvaluation) -> Dict[str, int]:
    """Splits total stale count into genuine staleness vs expected headless WS offline."""
    ws_row = next(
        (r for r in (getattr(ev, "panel_6_macro_onchain", None) or []) if r.label == "WebSocket Feeds & Warmup"),
        None,
    )
    expected_ws_offline = (
        1
        if (
            ws_row is not None
            and ws_row.status == "STALE"
            and "Warm:YES" in str(ws_row.value)
            and "no tick" in str(ws_row.value)
        )
        else 0
    )
    total_stale = int(ev.stale_count)
    return {
        "total": total_stale,
        "genuine": max(0, total_stale - expected_ws_offline),
        "expected_headless_ws_offline": expected_ws_offline,
    }


def _build_section_7a_rows(store: Optional[StateStore], spot_px: float) -> List[Dict[str, str]]:
    """Extracts 500-bar Swing Structure & S/R clusters for 1D / 4H / 1H."""
    if store is None:
        return []
    return [
        _summarize_kline_structure(list(getattr(store, "spot_klines_1d", []) or []), spot_px, "1D", 86_400_000, lookback=500),
        _summarize_kline_structure(list(getattr(store, "spot_klines_4h", []) or []), spot_px, "4H", 14_400_000, lookback=500),
        _summarize_kline_structure(list(getattr(store, "spot_klines_1h", []) or []), spot_px, "1H", 3_600_000, lookback=500),
    ]


def _build_section_7c_data(store: Optional[StateStore]) -> Dict[str, Any]:
    """Extracts 6-tier modeled liquidation ladder and USD high-impact macro calendar events."""
    if store is None:
        return {
            "liquidation_ladder": [],
            "macro_calendar_fetched": False,
            "macro_calendar": [],
        }
    mag = getattr(store, "btc_magnet_evaluation", None)
    tiers_raw = (getattr(mag, "levels_ladder", None) or {}).get("tiers_6") if mag is not None else None
    ladder: List[Dict[str, Any]] = []
    if isinstance(tiers_raw, list):
        for t in tiers_raw:
            px = t.get("price")
            dp = t.get("distance_pct")
            vm = t.get("estimated_vol_m")
            ladder.append({
                "tier": str(t.get("tier") or "N/A"),
                "side": str(t.get("side") or "N/A").upper(),
                "price": round(float(px), 2) if isinstance(px, (int, float)) else None,
                "distance_pct": round(float(dp), 2) if isinstance(dp, (int, float)) else None,
                "estimated_vol_m": round(float(vm), 2) if isinstance(vm, (int, float)) else None,
            })

    mi = getattr(store, "macro_intermarket", None)
    cal_raw = (getattr(mi, "macro_calendar_events", None) or []) if mi is not None else []
    cal_fetched = bool(getattr(mi, "macro_calendar_fetched", False)) if mi is not None else False
    events: List[Dict[str, Any]] = []
    if isinstance(cal_raw, list):
        for cev in cal_raw[:6]:
            mins = cev.get("minutes_away")
            if isinstance(mins, (int, float)):
                cd_s = f"{abs(mins):.0f}m ago" if mins < 0 else (f"in {mins:.0f}m" if mins < 120 else f"in {mins / 60.0:.1f}h")
            else:
                cd_s = "N/A"
            events.append({
                "title": str(cev.get("title") or "USD Event"),
                "time_utc": str(cev.get("time_utc") or "N/A"),
                "minutes_away": round(float(mins), 1) if isinstance(mins, (int, float)) else None,
                "countdown": cd_s,
                "forecast": str(cev.get("forecast") or "-"),
                "previous": str(cev.get("previous") or "-"),
            })
    return {
        "liquidation_ladder": ladder,
        "macro_calendar_fetched": cal_fetched,
        "macro_calendar": events,
    }


def _build_section_0_veto(
    store: Optional[StateStore],
    spot_px: float,
    struct_7a: List[Dict[str, str]],
    utc_str: str,
    sgt_str: str,
) -> Dict[str, str]:
    """Builds the structured Section 0 Bidirectional Regime Router (Gate 0) object."""
    if store is None:
        return {
            "last_1d_close_str": "UNAVAILABLE",
            "sma200_1d_str": "UNAVAILABLE",
            "dist_vs_sma200_str": "UNAVAILABLE",
            "sma200_pos": "UNAVAILABLE",
            "struct_4h_str": "UNAVAILABLE",
            "bos_4h_str": "UNAVAILABLE",
            "cond_a": "UNAVAILABLE",
            "cond_b": "UNAVAILABLE",
            "macro_caution": "UNAVAILABLE",
            "active_route": "UNDETERMINED",
            "primary_rail": "HOLD_BOTH_RAILS (FAIL-CLOSED — VERIFY DATA)",
            "btc_sleeve_posture": "HOLD BTC (FAIL-CLOSED — VERIFY DATA)",
            "usdt_sleeve_posture": "HOLD USDT (FAIL-CLOSED — VERIFY DATA)",
            "veto_status": "UNDETERMINED",
            "portfolio_status": "HOLD CURRENT INVENTORY (FAIL-CLOSED — VERIFY DATA)",
            "new_entry": "PROHIBITED",
            "timestamp_status": f"{utc_str} | {sgt_str} · Closed-Candle Inputs Only",
        }
    s4h = struct_7a[1] if len(struct_7a) > 1 else None
    veto = dict(evaluate_hard_market_veto(store, spot_px=spot_px, struct_4h=s4h))
    veto["timestamp_status"] = f"{utc_str} | {sgt_str} · Closed-Candle Inputs Only"
    return veto


def _build_bidirectional_rails(
    store: Optional[StateStore],
    router: Dict[str, str],
    spot_px: float,
    struct_7a: Sequence[Dict[str, str]],
    sec_7c: Dict[str, Any],
) -> Dict[str, Dict[str, str]]:
    """Builds deterministic Rail A (BTC->USDT) and Rail B (USDT->BTC) reference card payloads."""
    route = str(router.get("active_route") or "UNDETERMINED").upper()
    macro_caution = str(router.get("macro_caution") or "UNAVAILABLE")
    btc_posture = str(router.get("btc_sleeve_posture") or "HOLD BTC")
    usdt_posture = str(router.get("usdt_sleeve_posture") or "HOLD USDT")

    if store is None:
        return {
            "rail_a": {
                "name": "RAIL A · BTC → USDT (SELL / CONVERT)",
                "posture": btc_posture,
                "supply_zone": "UNAVAILABLE",
                "invalidation_buyback": "UNAVAILABLE",
                "rebuy_target": "UNAVAILABLE",
            },
            "rail_b": {
                "name": "RAIL B · USDT → BTC (BUY / ACCUMULATE)",
                "posture": usdt_posture,
                "demand_zone": "UNAVAILABLE",
                "flow_gate": "UNAVAILABLE",
                "risk_and_macro": f"<= 0.75% max portfolio risk · Macro: {macro_caution}",
            },
        }

    slsp = getattr(store, "slsp_evaluation", None)
    nres = getattr(getattr(slsp, "nearest_resistance", None), "center_price", None)
    nsup = getattr(getattr(slsp, "nearest_support", None), "center_price", None)
    s_1d = struct_7a[0] if len(struct_7a) > 0 else {}
    s_4h = struct_7a[1] if len(struct_7a) > 1 else {}

    ladder = sec_7c.get("liquidation_ladder") or []
    up_tiers = [t for t in ladder if str(t.get("side", "")).upper() == "UPPER" and isinstance(t.get("price"), (int, float))]
    dn_tiers = [t for t in ladder if str(t.get("side", "")).upper() == "LOWER" and isinstance(t.get("price"), (int, float))]

    sup_parts: List[str] = []
    res_parts: List[str] = []
    if isinstance(nres, (int, float)) and float(nres) > 0.0:
        res_parts.append(f"SLSP Res ${float(nres):,.2f}")
    if s_1d.get("res") and "None" not in str(s_1d.get("res")):
        res_parts.append(f"1D: {s_1d['res']}")
    if up_tiers:
        near_up = min(up_tiers, key=lambda x: float(x["price"]))
        far_up = max(up_tiers, key=lambda x: float(x["price"]))
        res_parts.append(f"7C Shorts: ${float(near_up['price']):,.0f}–${float(far_up['price']):,.0f}")

    if isinstance(nsup, (int, float)) and float(nsup) > 0.0:
        sup_parts.append(f"SLSP Sup ${float(nsup):,.2f}")
    if s_1d.get("sup") and "None" not in str(s_1d.get("sup")):
        sup_parts.append(f"1D: {s_1d['sup']}")
    if s_4h.get("sup") and "None" not in str(s_4h.get("sup")):
        sup_parts.append(f"4H: {s_4h['sup']}")
    if dn_tiers:
        near_dn = max(dn_tiers, key=lambda x: float(x["price"]))
        far_dn = min(dn_tiers, key=lambda x: float(x["price"]))
        sup_parts.append(f"7C Longs: ${float(far_dn['price']):,.0f}–${float(near_dn['price']):,.0f}")

    pivots_4h = str(s_4h.get("pivots") or "N/A")
    res_4h = str(s_4h.get("res") or "N/A")
    if route == "MACRO_DOWNTREND_DISTRIBUTION":
        inval_s = f"Closed 4H reclaim above {res_4h if 'None' not in res_4h else pivots_4h}"
    elif route == "MACRO_UPTREND_MARKUP":
        inval_s = "Selective euphoria trim only (re-enter on 4H HL hold)"
    else:
        inval_s = f"Closed 4H breakout above boundary ({res_4h})"

    fg = getattr(store, "four_gate_evaluation", None)
    asp = getattr(fg, "loop_a_g1_val", None)
    d_spr = getattr(fg, "loop_a_g2_val", None)
    flow_bits: List[str] = []
    if isinstance(asp, (int, float)):
        flow_bits.append(f"4H A_SP:{float(asp):+.3f}")
    if isinstance(d_spr, (int, float)):
        flow_bits.append(f"D(z_S-z_F):{float(d_spr):+.2f}")
    flow_prefix = (" · ".join(flow_bits) + " · ") if flow_bits else ""

    if route == "MACRO_UPTREND_MARKUP":
        gate_req = f"{flow_prefix}Buy 4H Higher-Low pullback + Spot CVD / A_SP > 0"
    else:
        gate_req = f"{flow_prefix}Require closed sweep reclaim + Spot CVD / A_SP > 0"

    tp_ref = f"Targets: {', '.join(res_parts[:2])}" if res_parts else "Targets: 7A Overhead Resistance"
    return {
        "rail_a": {
            "name": "RAIL A · BTC → USDT (SELL / CONVERT)",
            "posture": btc_posture,
            "supply_zone": " · ".join(res_parts) if res_parts else "7A Resistance / Upper 7C Shorts",
            "invalidation_buyback": inval_s,
            "rebuy_target": " · ".join(sup_parts[:2]) if sup_parts else "Lower 7C Long Pools / 7A Support",
        },
        "rail_b": {
            "name": "RAIL B · USDT → BTC (BUY / ACCUMULATE)",
            "posture": usdt_posture,
            "demand_zone": " · ".join(sup_parts) if sup_parts else "7A Support / Lower 7C Longs",
            "flow_gate": gate_req,
            "risk_and_macro": f"<= 0.75% max portfolio risk · {tp_ref} · Macro: {macro_caution}",
        },
    }


def build_dd_json_payload(
    ev: DataHubEvaluation,
    md_report: str,
    recent_archive: List[Dict[str, Any]],
    utc_str: str,
    sgt_str: str,
    store: Optional[StateStore] = None,
) -> Dict[str, Any]:
    """Builds the structured `dd_latest.json` payload for GitHub Pages and downstream bots."""
    panels: Dict[str, Any] = {}
    for key, title, attr in PANEL_SPECS:
        rows = getattr(ev, attr, []) or []
        panels[key] = {
            "title": title,
            "rows": _serialize_rows(rows),
        }

    spot_px = float(ev.spot_price or 0.0)
    stale_breakdown = _compute_stale_breakdown(ev)
    struct_7a = _build_section_7a_rows(store, spot_px)
    veto_0 = _build_section_0_veto(store, spot_px, struct_7a, utc_str, sgt_str)
    sec_7c = _build_section_7c_data(store)
    rails_0 = _build_bidirectional_rails(store, veto_0, spot_px, struct_7a, sec_7c)

    return {
        "schema_version": "dd_v2",
        "instrument": "BTCUSDT",
        "retrieval_utc": utc_str,
        "retrieval_sgt": sgt_str,
        "spot_price": spot_px,
        "total_metrics": int(ev.total_metrics),
        "ok_count": int(ev.ok_count),
        "unavailable_count": int(ev.unavailable_count),
        "stale_count": int(ev.stale_count),
        "stale_breakdown": stale_breakdown,
        "proxy_or_static_count": int(ev.proxy_or_static_count),
        "archive_snapshots_count": int(ev.archive_snapshots_count),
        "archive_last_bar_utc": ev.archive_last_bar_utc or "",
        "section_0_veto": veto_0,
        "bidirectional_rails": rails_0,
        "panels": panels,
        "section_7a_structure": struct_7a,
        "section_7c": sec_7c,
        "recent_archive": recent_archive,
        "markdown_report": md_report,
    }


def _status_badge_class(status: str) -> str:
    st = (status or "").upper()
    if st == "OK":
        return "badge-ok"
    if st == "PROXY":
        return "badge-proxy"
    if st == "STALE":
        return "badge-stale"
    return "badge-unavail"


def _render_veto_banner_html(veto: Dict[str, Any], rails: Optional[Dict[str, Any]] = None) -> str:
    """Renders the top Section 0 Bidirectional Regime Router and side-by-side Rail A / Rail B cards."""
    route = str(veto.get("active_route") or "").upper()
    st = str(veto.get("veto_status") or "UNDETERMINED").upper()
    if not route:
        route = "MACRO_DOWNTREND_DISTRIBUTION" if st == "ACTIVE" else ("UNDETERMINED" if st == "UNDETERMINED" else "TRANSITIONAL_RANGE")

    if route == "MACRO_DOWNTREND_DISTRIBUTION":
        cls = "veto-active"
        badge_cls = "badge-unavail"
    elif route == "MACRO_UPTREND_MARKUP":
        cls = "veto-inactive"
        badge_cls = "badge-ok"
    elif route == "TRANSITIONAL_RANGE":
        cls = "veto-range"
        badge_cls = "badge-proxy"
    else:
        cls = "veto-undetermined"
        badge_cls = "badge-stale"

    macro_s = str(veto.get("macro_caution") or "UNAVAILABLE")
    macro_cls = "badge-stale" if macro_s.startswith("CAUTION") else ("badge-ok" if macro_s.startswith("CLEAR") else "badge-unavail")
    btc_p = html.escape(str(veto.get("btc_sleeve_posture") or veto.get("portfolio_status") or "HOLD BTC"))
    usdt_p = html.escape(str(veto.get("usdt_sleeve_posture") or veto.get("new_entry") or "HOLD USDT"))
    cond_a = html.escape(str(veto.get("cond_a") or "UNAVAILABLE"))
    cond_b = html.escape(str(veto.get("cond_b") or "UNAVAILABLE"))
    close_1d = html.escape(str(veto.get("last_1d_close_str") or "UNAVAILABLE"))
    sma_200 = html.escape(str(veto.get("sma200_1d_str") or "UNAVAILABLE"))
    dist_200 = html.escape(str(veto.get("dist_vs_sma200_str") or "UNAVAILABLE"))
    struct_4h = html.escape(str(veto.get("struct_4h_str") or "UNAVAILABLE"))
    bos_4h = html.escape(str(veto.get("bos_4h_str") or "UNAVAILABLE"))

    rails_d = rails or {}
    ra = rails_d.get("rail_a") or {}
    rb = rails_d.get("rail_b") or {}

    return (
        f"<section id=\"veto\" class=\"veto-banner {cls}\">"
        f"<div class=\"veto-head\">"
        f"<div class=\"veto-title\">0. BIDIRECTIONAL REGIME ROUTER (DIBSE GATE 0): "
        f"<span class=\"badge {badge_cls}\" style=\"font-size:12px;padding:2px 8px;\">{html.escape(route)}</span> "
        f"<span class=\"badge {macro_cls}\" style=\"font-size:11px;padding:2px 7px;\">MACRO: {html.escape(macro_s)}</span></div>"
        f"<div class=\"veto-posture\">"
        f"<span>BTC Inventory (Rail A): <strong>{btc_p}</strong></span>"
        f"<span>USDT Inventory (Rail B): <strong>{usdt_p}</strong></span>"
        f"</div>"
        f"</div>"
        f"<div class=\"veto-grid\">"
        f"<div class=\"veto-cell\"><span class=\"dim\">Cond A (1D &lt; SMA200):</span> <code>{cond_a}</code> · <code>{close_1d}</code> vs <code>{sma_200}</code> (<code>{dist_200}</code>)</div>"
        f"<div class=\"veto-cell\"><span class=\"dim\">Cond B (4H Structure/BOS):</span> <code>{cond_b}</code> · <code>{struct_4h}</code> · <code>{bos_4h}</code></div>"
        f"</div>"
        f"<div id=\"rails-0\" class=\"rails-grid\">"
        f"<div class=\"rail-card rail-a\">"
        f"<div class=\"rail-title\">RAIL A · BTC &rarr; USDT (CONVERT / TRIM)</div>"
        f"<div class=\"rail-row\"><span class=\"dim\">Posture:</span> <code>{html.escape(str(ra.get('posture', btc_p)))}</code></div>"
        f"<div class=\"rail-row\"><span class=\"dim\">Supply / Sell Zone:</span> <code>{html.escape(str(ra.get('supply_zone', 'N/A')))}</code></div>"
        f"<div class=\"rail-row\"><span class=\"dim\">Buy-Back Invalidation:</span> <code>{html.escape(str(ra.get('invalidation_buyback', 'N/A')))}</code></div>"
        f"<div class=\"rail-row\"><span class=\"dim\">Lower Rebuy Zone:</span> <code>{html.escape(str(ra.get('rebuy_target', 'N/A')))}</code></div>"
        f"</div>"
        f"<div class=\"rail-card rail-b\">"
        f"<div class=\"rail-title\">RAIL B · USDT &rarr; BTC (ACCUMULATE)</div>"
        f"<div class=\"rail-row\"><span class=\"dim\">Posture:</span> <code>{html.escape(str(rb.get('posture', usdt_p)))}</code></div>"
        f"<div class=\"rail-row\"><span class=\"dim\">Demand / Rebuy Zone:</span> <code>{html.escape(str(rb.get('demand_zone', 'N/A')))}</code></div>"
        f"<div class=\"rail-row\"><span class=\"dim\">Confirmation Gate:</span> <code>{html.escape(str(rb.get('flow_gate', 'N/A')))}</code></div>"
        f"<div class=\"rail-row\"><span class=\"dim\">Risk &amp; Targets:</span> <code>{html.escape(str(rb.get('risk_and_macro', 'N/A')))}</code></div>"
        f"</div>"
        f"</div>"
        f"</section>"
    )


def _render_section_7a_card_html(rows_7a: Sequence[Dict[str, str]]) -> str:
    """Renders the 7A 500-Bar Market Structure & S/R Zones visual card."""
    body_rows: List[str] = []
    for sr in rows_7a:
        st_txt = str(sr.get("structure") or "")
        st_cls = "badge-ok" if st_txt.startswith("UPTREND") else ("badge-unavail" if st_txt.startswith("DOWNTREND") else "badge-stale")
        body_rows.append(
            f"<tr>"
            f"<td><code>{html.escape(str(sr.get('tf', '')))} ({html.escape(str(sr.get('bars', '0')))})</code></td>"
            f"<td><span class=\"badge {st_cls}\">{html.escape(st_txt)}</span></td>"
            f"<td><code>{html.escape(str(sr.get('pivots', 'N/A')))}</code></td>"
            f"<td><code>{html.escape(str(sr.get('bos', 'N/A')))}</code></td>"
            f"<td><code>{html.escape(str(sr.get('res', 'N/A')))}</code></td>"
            f"<td><code>{html.escape(str(sr.get('sup', 'N/A')))}</code></td>"
            f"</tr>"
        )
    if not body_rows:
        body_rows.append("<tr><td colspan=\"6\" class=\"dim\">Structure summary unavailable for this payload.</td></tr>")

    return (
        f"<section id=\"structure-7a\" class=\"section-extra panel-card\">"
        f"<h2>7A. 500-BAR MARKET STRUCTURE &amp; HISTORICAL S/R ZONES (1D / 4H / 1H)</h2>"
        f"<div class=\"table-wrap\"><table>"
        f"<thead><tr><th>TF (Bars)</th><th>Swing Structure</th><th>Last Swing Pivots</th>"
        f"<th>Latest BOS</th><th>Resistance Zones (Above)</th><th>Support Zones (Below)</th></tr></thead>"
        f"<tbody>{''.join(body_rows)}</tbody>"
        f"</table></div></section>"
    )


def _render_section_7c_card_html(sec_7c: Dict[str, Any]) -> str:
    """Renders the 7C Modeled Liquidation Ladder & USD Macro Calendar visual card."""
    ladder = sec_7c.get("liquidation_ladder") or []
    ladder_rows: List[str] = []
    for tier in ladder:
        side = str(tier.get("side") or "N/A").upper()
        s_cls = "badge-unavail" if side == "UPPER" else "badge-ok"
        px = tier.get("price")
        dp = tier.get("distance_pct")
        vm = tier.get("estimated_vol_m")
        px_s = f"${float(px):,.2f}" if isinstance(px, (int, float)) else "N/A"
        dp_s = f"{float(dp):+.2f}%" if isinstance(dp, (int, float)) else "N/A"
        vm_s = f"${float(vm):.1f}M" if isinstance(vm, (int, float)) else "N/A"
        ladder_rows.append(
            f"<tr>"
            f"<td><code>{html.escape(str(tier.get('tier', 'N/A')))}</code></td>"
            f"<td><span class=\"badge {s_cls}\">{html.escape(side)}</span></td>"
            f"<td><code>{px_s}</code></td>"
            f"<td><code>{dp_s}</code></td>"
            f"<td><code>{vm_s}</code></td>"
            f"</tr>"
        )
    if not ladder_rows:
        ladder_rows.append("<tr><td colspan=\"5\" class=\"dim\">DATA UNAVAILABLE</td></tr>")

    cal_events = sec_7c.get("macro_calendar") or []
    cal_fetched = bool(sec_7c.get("macro_calendar_fetched", False))
    cal_rows: List[str] = []
    if cal_events:
        for cev in cal_events:
            cal_rows.append(
                f"<tr>"
                f"<td><code>{html.escape(str(cev.get('title', 'USD Event')))}</code></td>"
                f"<td><code>{html.escape(str(cev.get('time_utc', 'N/A')))}</code></td>"
                f"<td><span class=\"badge badge-stale\">{html.escape(str(cev.get('countdown', 'N/A')))}</span></td>"
                f"<td><code>{html.escape(str(cev.get('forecast', '-')))}</code></td>"
                f"<td><code>{html.escape(str(cev.get('previous', '-')))}</code></td>"
                f"</tr>"
            )
    elif cal_fetched:
        cal_rows.append("<tr><td><code>NONE (next 7d)</code></td><td>-</td><td><span class=\"badge badge-ok\">CLEAR</span></td><td>-</td><td>-</td></tr>")
    else:
        cal_rows.append("<tr><td colspan=\"5\" class=\"dim\">DATA UNAVAILABLE</td></tr>")

    return (
        f"<section id=\"liq-macro-7c\" class=\"section-extra\" style=\"padding:0;overflow:hidden;\">"
        f"<div class=\"split-grid\">"
        f"<div class=\"split-pane\">"
        f"<h2 class=\"sub-h2\">7C-1. MODELED LIQUIDATION LADDER (10x-100x)</h2>"
        f"<div class=\"table-wrap\"><table>"
        f"<thead><tr><th>Tier</th><th>Side</th><th>Level ($)</th><th>Dist%</th><th>Est Pool ($M)</th></tr></thead>"
        f"<tbody>{''.join(ladder_rows)}</tbody>"
        f"</table></div></div>"
        f"<div class=\"split-pane\">"
        f"<h2 class=\"sub-h2\">7C-2. USD HIGH-IMPACT MACRO CALENDAR (-60m to +7d)</h2>"
        f"<div class=\"table-wrap\"><table>"
        f"<thead><tr><th>Event</th><th>Time (UTC)</th><th>Countdown</th><th>Forecast</th><th>Previous</th></tr></thead>"
        f"<tbody>{''.join(cal_rows)}</tbody>"
        f"</table></div></div>"
        f"</div></section>"
    )


def render_dashboard_html(
    payload: Dict[str, Any],
    repo_url: str,
    pages_url: str,
) -> str:
    """Renders a self-contained retro-Bloomberg dark-mode HTML dashboard for GitHub Pages."""
    spot = float(payload.get("spot_price", 0.0) or 0.0)
    utc_raw = str(payload.get("retrieval_utc", ""))
    utc_s = html.escape(utc_raw)
    sgt_s = html.escape(str(payload.get("retrieval_sgt") or payload.get("retrieval_myt") or ""))
    ok_c = int(payload.get("ok_count", 0))
    tot_c = int(payload.get("total_metrics", 0))
    na_c = int(payload.get("unavailable_count", 0))
    st_c = int(payload.get("stale_count", 0))
    sb = payload.get("stale_breakdown") or {"total": st_c, "genuine": st_c, "expected_headless_ws_offline": 0}
    gen_c = int(sb.get("genuine", st_c))
    ws_off_c = int(sb.get("expected_headless_ws_offline", 0))
    px_c = int(payload.get("proxy_or_static_count", 0))
    issues_c = na_c + st_c + px_c
    arch_c = int(payload.get("archive_snapshots_count", 0))
    arch_last = html.escape(str(payload.get("archive_last_bar_utc") or "N/A"))
    md_report = str(payload.get("markdown_report", ""))
    md_json_safe = json.dumps(md_report).replace("</", "<\\/")
    trigger_url = html.escape(f"{repo_url.rstrip('/')}/actions/workflows/dd_hourly.yml")
    pages_esc = html.escape(pages_url)

    veto_html = _render_veto_banner_html(
        payload.get("section_0_veto") or {},
        payload.get("bidirectional_rails") or None,
    )
    sec_7a_html = _render_section_7a_card_html(payload.get("section_7a_structure") or [])
    sec_7c_html = _render_section_7c_card_html(payload.get("section_7c") or {})

    panel_cards: List[str] = []
    panels = payload.get("panels", {})
    for key, title, _ in PANEL_SPECS:
        p = panels.get(key, {})
        rows_html: List[str] = []
        for r in p.get("rows", []):
            lbl = html.escape(str(r.get("label", "")))
            val = html.escape(str(r.get("value", "")))
            tabs = html.escape(str(r.get("tabs", "")))
            status = str(r.get("status", "UNAVAILABLE")).upper()
            bcls = _status_badge_class(status)
            rows_html.append(
                f"<tr class=\"metric-row\" data-status=\"{html.escape(status)}\">"
                f"<td class=\"col-metric\">{lbl}<span class=\"tabs-tag\">[{tabs}]</span></td>"
                f"<td class=\"col-val\"><code>{val}</code></td>"
                f"<td class=\"col-st\"><span class=\"badge {bcls}\">{html.escape(status)}</span></td>"
                f"</tr>"
            )
        panel_cards.append(
            f"<section class=\"panel-card\">"
            f"<h2>{html.escape(str(p.get('title', title)))}</h2>"
            f"<div class=\"table-wrap\"><table>"
            f"<thead><tr><th>Metric</th><th>Value</th><th>Status</th></tr></thead>"
            f"<tbody>{''.join(rows_html)}</tbody>"
            f"</table></div></section>"
        )

    arch_rows_html: List[str] = []
    for snap in payload.get("recent_archive", []):
        arch_rows_html.append(
            f"<tr>"
            f"<td><code>{html.escape(str(snap['closed_4h_bar_utc']))}</code></td>"
            f"<td><code>${float(snap['spot_price']):,.2f}</code></td>"
            f"<td><span class=\"badge badge-ok\">{int(snap['ok_count'])}</span></td>"
            f"<td>{int(snap['unavailable_count'])}</td>"
            f"<td>{int(snap['stale_count'])}</td>"
            f"<td>{int(snap['proxy_or_static_count'])}</td>"
            f"<td class=\"dim\">{html.escape(str(snap['retrieval_utc']))}</td>"
            f"</tr>"
        )
    if not arch_rows_html:
        arch_rows_html.append(
            "<tr><td colspan=\"7\" class=\"dim\">No closed-4H snapshots archived yet.</td></tr>"
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>BTC Swing Engine — Tab [D: DATA HUB]</title>
<style>
  :root {{
    --bg: #070b10;
    --panel: #0d141d;
    --panel-alt: #111b27;
    --border: #1e2d3d;
    --text: #e2e8f0;
    --muted: #8b9bb4;
    --cyan: #38bdf8;
    --amber: #f59e0b;
    --green: #22c55e;
    --red: #f43f5e;
    --mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    background: var(--bg);
    color: var(--text);
    font-family: var(--mono);
    font-size: 13px;
    line-height: 1.45;
  }}
  header.topbar {{
    position: sticky;
    top: 0;
    z-index: 20;
    background: rgba(7, 11, 16, 0.96);
    backdrop-filter: blur(8px);
    border-bottom: 1px solid var(--border);
    padding: 12px 18px;
  }}
  .top-row {{
    max-width: 1600px;
    margin: 0 auto;
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    align-items: center;
    justify-content: space-between;
  }}
  .brand {{
    display: flex;
    flex-direction: column;
    gap: 4px;
  }}
  .brand-title {{
    font-size: 15px;
    font-weight: 700;
    color: var(--cyan);
    letter-spacing: 0.04em;
  }}
  .meta-line {{
    font-size: 12px;
    color: var(--muted);
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
  }}
  .meta-line strong {{ color: var(--text); }}
  .spot-pill {{
    color: var(--green);
    font-weight: 700;
  }}
  .actions {{
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    align-items: center;
  }}
  .btn {{
    appearance: none;
    border: 1px solid var(--border);
    background: var(--panel-alt);
    color: var(--text);
    font-family: var(--mono);
    font-size: 12px;
    font-weight: 600;
    padding: 8px 12px;
    border-radius: 6px;
    cursor: pointer;
    text-decoration: none;
    transition: border-color 0.15s, background 0.15s;
  }}
  .btn:hover {{
    border-color: var(--cyan);
    background: #162334;
  }}
  .btn-primary {{
    background: #0c4a6e;
    border-color: var(--cyan);
    color: #f0f9ff;
    font-size: 14px;
    padding: 11px 16px;
  }}
  .btn-primary:hover {{
    background: #0369a1;
  }}
  .btn-trigger {{
    border-color: rgba(245, 158, 11, 0.5);
    color: #fde68a;
  }}
  .copy-status {{
    font-size: 11px;
    color: var(--green);
    min-height: 16px;
    margin-top: 4px;
  }}
  main {{
    max-width: 1600px;
    margin: 0 auto;
    padding: 16px 18px 40px;
  }}
  .grid {{
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 14px;
  }}
  @media (max-width: 1080px) {{
    .grid {{ grid-template-columns: 1fr; }}
  }}
  .panel-card {{
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 8px;
    overflow: hidden;
  }}
  .panel-card h2 {{
    margin: 0;
    padding: 10px 14px;
    font-size: 13px;
    letter-spacing: 0.04em;
    color: var(--amber);
    background: var(--panel-alt);
    border-bottom: 1px solid var(--border);
  }}
  .table-wrap {{
    overflow-x: auto;
  }}
  table {{
    width: 100%;
    border-collapse: collapse;
  }}
  th, td {{
    padding: 6px 10px;
    border-bottom: 1px solid rgba(30, 45, 61, 0.55);
    text-align: left;
    vertical-align: top;
  }}
  th {{
    font-size: 11px;
    text-transform: uppercase;
    color: var(--muted);
    background: rgba(17, 27, 39, 0.5);
  }}
  tr:last-child td {{ border-bottom: none; }}
  .col-metric {{
    width: 34%;
    color: #cbd5e1;
  }}
  .tabs-tag {{
    display: inline-block;
    margin-left: 6px;
    font-size: 10px;
    color: var(--muted);
  }}
  .col-val {{
    width: 54%;
    word-break: break-word;
  }}
  .col-val code {{
    color: #f8fafc;
    font-family: var(--mono);
  }}
  .col-st {{
    width: 12%;
    text-align: right;
    white-space: nowrap;
  }}
  .badge {{
    display: inline-block;
    padding: 1px 6px;
    border-radius: 4px;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.03em;
  }}
  .badge-ok {{ background: rgba(34, 197, 94, 0.16); color: #4ade80; border: 1px solid rgba(34, 197, 94, 0.35); }}
  .badge-proxy {{ background: rgba(56, 189, 248, 0.16); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.35); }}
  .badge-stale {{ background: rgba(245, 158, 11, 0.16); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.35); }}
  .badge-unavail {{ background: rgba(244, 63, 94, 0.15); color: #fda4af; border: 1px solid rgba(244, 63, 94, 0.35); }}
  .section-extra {{
    margin-top: 16px;
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 12px 14px;
  }}
  details summary {{
    cursor: pointer;
    color: var(--cyan);
    font-weight: 700;
  }}
  textarea#raw-md {{
    width: 100%;
    min-height: 320px;
    margin-top: 10px;
    background: #05080c;
    color: #cbd5e1;
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 10px;
    font-family: var(--mono);
    font-size: 12px;
  }}
  .veto-banner {{
    margin-bottom: 14px;
    border-radius: 8px;
    border: 1px solid var(--border);
    padding: 12px 14px;
    background: var(--panel);
  }}
  .veto-active {{
    border-color: rgba(244, 63, 94, 0.6);
    background: linear-gradient(180deg, rgba(244, 63, 94, 0.12), rgba(13, 20, 29, 0.96));
  }}
  .veto-inactive {{
    border-color: rgba(34, 197, 94, 0.5);
    background: linear-gradient(180deg, rgba(34, 197, 94, 0.10), rgba(13, 20, 29, 0.96));
  }}
  .veto-undetermined {{
    border-color: rgba(245, 158, 11, 0.55);
    background: linear-gradient(180deg, rgba(245, 158, 11, 0.12), rgba(13, 20, 29, 0.96));
  }}
  .veto-range {{
    border-color: rgba(56, 189, 248, 0.55);
    background: linear-gradient(180deg, rgba(56, 189, 248, 0.11), rgba(13, 20, 29, 0.96));
  }}
  .rails-grid {{
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 10px;
    margin-top: 10px;
  }}
  @media (max-width: 960px) {{
    .rails-grid {{ grid-template-columns: 1fr; }}
  }}
  .rail-card {{
    background: rgba(5, 8, 12, 0.65);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 9px 11px;
    font-size: 12px;
  }}
  .rail-card.rail-a {{ border-left: 3px solid var(--red); }}
  .rail-card.rail-b {{ border-left: 3px solid var(--green); }}
  .rail-title {{
    font-weight: 700;
    font-size: 12px;
    letter-spacing: 0.04em;
    margin-bottom: 6px;
    color: var(--cyan);
  }}
  .rail-row {{
    margin-bottom: 4px;
    word-break: break-word;
  }}
  .rail-row:last-child {{ margin-bottom: 0; }}
  .veto-head {{
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 8px;
  }}
  .veto-title {{
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 0.04em;
    color: var(--text);
  }}
  .veto-posture {{
    display: flex;
    flex-wrap: wrap;
    gap: 14px;
    font-size: 12px;
  }}
  .veto-grid {{
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 8px;
    font-size: 12px;
  }}
  @media (max-width: 960px) {{
    .veto-grid {{ grid-template-columns: 1fr; }}
  }}
  .veto-cell {{
    background: rgba(5, 8, 12, 0.55);
    border: 1px solid rgba(30, 45, 61, 0.75);
    border-radius: 6px;
    padding: 6px 10px;
    word-break: break-word;
  }}
  .toolbar {{
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    align-items: center;
    margin-bottom: 14px;
  }}
  .btn-filter {{
    padding: 5px 10px;
    font-size: 11px;
  }}
  .btn-filter.is-active {{
    border-color: var(--cyan);
    background: #0c4a6e;
    color: #f0f9ff;
  }}
  .split-grid {{
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }}
  @media (max-width: 1080px) {{
    .split-grid {{ grid-template-columns: 1fr; }}
  }}
  .split-pane {{
    border-right: 1px solid var(--border);
  }}
  .split-pane:last-child {{
    border-right: none;
  }}
  @media (max-width: 1080px) {{
    .split-pane {{
      border-right: none;
      border-bottom: 1px solid var(--border);
    }}
    .split-pane:last-child {{
      border-bottom: none;
    }}
  }}
  h2.sub-h2 {{
    margin: 0;
    padding: 10px 14px;
    font-size: 13px;
    letter-spacing: 0.04em;
    color: var(--amber);
    background: var(--panel-alt);
    border-bottom: 1px solid var(--border);
  }}
  .age-ok {{ color: var(--green); font-weight: 700; }}
  .age-warn {{ color: var(--amber); font-weight: 700; }}
  .age-stale {{ color: var(--red); font-weight: 700; }}
  .dim {{ color: var(--muted); }}
  footer {{
    max-width: 1600px;
    margin: 0 auto 24px;
    padding: 0 18px;
    color: var(--muted);
    font-size: 11px;
  }}
</style>
</head>
<body>
<header class="topbar">
  <div class="top-row">
    <div class="brand">
      <div class="brand-title">BTC SWING ENGINE // CORTEX DIBSE BIDIRECTIONAL DESK v1.0 — TAB [D: {tot_c}-ROW MATRIX]</div>
      <div class="meta-line">
        <span>Spot: <span class="spot-pill">${spot:,.2f}</span></span>
        <span>UTC: <strong>{utc_s}</strong> <span id="snapshot-age"></span></span>
        <span>SGT: <strong>{sgt_s}</strong></span>
        <span>Coverage: <strong>OK={ok_c}/{tot_c}</strong> · N/A={na_c} · STALE={st_c} (Gen={gen_c}, WS_Off={ws_off_c}) · PROXY={px_c}</span>
        <span>SQLite 4H Archive: <strong>{arch_c}</strong> (Last: {arch_last})</span>
      </div>
    </div>
    <div>
      <div class="actions">
        <button id="copy-dd-btn" class="btn btn-primary" type="button">[ &#x1F4CB; COPY FULL DD REPORT FOR AI ]</button>
        <a class="btn" href="btc_data_hub_latest.md" download="btc_data_hub_latest.md">[ &#x2B07; DOWNLOAD .MD ]</a>
        <a class="btn" href="dd_latest.json" target="_blank" rel="noopener">[ {{ }} JSON ]</a>
        <a class="btn btn-trigger" href="{trigger_url}" target="_blank" rel="noopener">[ &#x26A1; TRIGGER ON-DEMAND RUN ]</a>
      </div>
      <div id="copy-status" class="copy-status"></div>
    </div>
  </div>
</header>

<main>
  {veto_html}

  <div class="toolbar">
    <button id="flt-all" class="btn btn-filter is-active" type="button">All Metrics ({tot_c})</button>
    <button id="flt-issues" class="btn btn-filter" type="button">Non-OK Only ({issues_c})</button>
    <a class="btn btn-filter" href="#rails-0">0A/0B Rails</a>
    <a class="btn btn-filter" href="#structure-7a">7A Structure &amp; S/R</a>
    <a class="btn btn-filter" href="#liq-macro-7c">7C Liq Ladder &amp; Macro</a>
    <a class="btn btn-filter" href="#archive-7">SQLite Archive</a>
  </div>

  <div class="grid">
    {''.join(panel_cards)}
  </div>

  {sec_7a_html}
  {sec_7c_html}

  <section class="section-extra">
    <details>
      <summary>Raw Markdown (AI Copy-Paste View — {len(md_report):,} chars)</summary>
      <textarea id="raw-md" readonly>{html.escape(md_report)}</textarea>
    </details>
  </section>

  <section id="archive-7" class="section-extra">
    <h2 style="margin:0 0 8px;font-size:13px;color:var(--amber);">RECENT 4H SQLITE ARCHIVE SNAPSHOTS</h2>
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Closed 4H Bar (UTC)</th>
            <th>Spot ($)</th>
            <th>OK</th>
            <th>N/A</th>
            <th>STALE</th>
            <th>PROXY</th>
            <th>Retrieved (UTC)</th>
          </tr>
        </thead>
        <tbody>{''.join(arch_rows_html)}</tbody>
      </table>
    </div>
  </section>
</main>

<footer>
  Dashboard URL: <a href="{pages_esc}" style="color:var(--cyan);">{pages_esc}</a> · CORTEX DIBSE BIDIRECTIONAL DESK v1.0 · Zero-Hallucination DATA-ONLY Telemetry (DD v2)
</footer>

<script type="application/json" id="dd-markdown-payload">{md_json_safe}</script>
<script>
(function () {{
  const btn = document.getElementById("copy-dd-btn");
  const statusEl = document.getElementById("copy-status");
  const payloadEl = document.getElementById("dd-markdown-payload");
  const rawBox = document.getElementById("raw-md");
  const mdText = payloadEl ? JSON.parse(payloadEl.textContent) : (rawBox ? rawBox.value : "");

  const retrievalUtcRaw = {json.dumps(utc_raw)};
  const ageEl = document.getElementById("snapshot-age");
  function updateAge() {{
    if (!ageEl || !retrievalUtcRaw) return;
    const m = /^(\\d{{4}}-\\d{{2}}-\\d{{2}})\\s+(\\d{{2}}:\\d{{2}}:\\d{{2}})\\s+UTC$/.exec(retrievalUtcRaw.trim());
    if (!m) return;
    const ts = Date.parse(m[1] + "T" + m[2] + "Z");
    if (!isFinite(ts)) return;
    const mins = Math.max(0, Math.floor((Date.now() - ts) / 60000));
    let cls = "age-ok";
    let label = "(" + mins + "m ago)";
    if (mins > 90) {{
      cls = "age-stale";
      label = "(" + mins + "m ago · STALE)";
    }} else if (mins > 70) {{
      cls = "age-warn";
      label = "(" + mins + "m ago · AGING)";
    }}
    ageEl.className = cls;
    ageEl.textContent = label;
  }}
  updateAge();
  setInterval(updateAge, 30000);

  const fltAll = document.getElementById("flt-all");
  const fltIssues = document.getElementById("flt-issues");
  const metricRows = Array.from(document.querySelectorAll("tr.metric-row"));
  function setFilter(mode) {{
    const onlyIssues = mode === "issues";
    metricRows.forEach(function (tr) {{
      const st = (tr.getAttribute("data-status") || "").toUpperCase();
      tr.style.display = (onlyIssues && st === "OK") ? "none" : "";
    }});
    if (fltAll) fltAll.classList.toggle("is-active", !onlyIssues);
    if (fltIssues) fltIssues.classList.toggle("is-active", onlyIssues);
  }}
  if (fltAll) fltAll.addEventListener("click", function () {{ setFilter("all"); }});
  if (fltIssues) fltIssues.addEventListener("click", function () {{ setFilter("issues"); }});

  btn.addEventListener("click", async function () {{
    let copied = false;
    if (navigator.clipboard && navigator.clipboard.writeText) {{
      try {{
        await navigator.clipboard.writeText(mdText);
        copied = true;
      }} catch (e) {{
        copied = false;
      }}
    }}
    if (!copied && rawBox) {{
      const details = rawBox.closest("details");
      if (details) details.open = true;
      rawBox.focus();
      rawBox.select();
      try {{
        copied = document.execCommand("copy");
      }} catch (e) {{
        copied = false;
      }}
    }}
    statusEl.textContent = copied
      ? "✓ COPIED " + mdText.length.toLocaleString() + " CHARS ({tot_c}-ROW DD REPORT) TO CLIPBOARD"
      : "Select & copy from the Raw Markdown box below.";
    setTimeout(function () {{ statusEl.textContent = ""; }}, 4500);
  }});
}})();
</script>
</body>
</html>
"""


def _format_telegram_panel_block(title: str, rows: Sequence[DataMetricRow]) -> str:
    lines = [f"[{title}]"]
    for r in rows:
        tag = f" [{r.status}]" if (r.status != "OK" and f"[{r.status}]" not in r.value) else ""
        lines.append(f"• {r.label}: {r.value}{tag}")
    return "\n".join(lines)


def build_telegram_messages(
    ev: DataHubEvaluation,
    utc_str: str,
    sgt_str: str,
    pages_url: str,
    repo_url: str,
    max_len: int = TELEGRAM_MAX_LEN,
) -> List[str]:
    """Builds split Telegram HTML messages guaranteed to stay below Telegram's 4,096-char limit."""
    header_1 = (
        f"<b>BTC TAB [D: DATA HUB] (1/2)</b>\n"
        f"Spot: <b>${ev.spot_price:,.2f}</b> | "
        f"OK=<code>{ev.ok_count}/{ev.total_metrics}</code> "
        f"(N/A={ev.unavailable_count}, STALE={ev.stale_count}, PROXY={ev.proxy_or_static_count})\n"
        f"UTC: <code>{html.escape(utc_str)}</code>\n"
        f"SGT: <code>{html.escape(sgt_str)}</code>\n"
        f"4H SQLite: <code>{ev.archive_snapshots_count}</code> bars "
        f"(Last: <code>{html.escape(ev.archive_last_bar_utc or 'N/A')}</code>)"
    )
    header_2 = (
        f"<b>BTC TAB [D: DATA HUB] (2/2)</b> — Spot: <b>${ev.spot_price:,.2f}</b> "
        f"(<code>{html.escape(sgt_str)}</code>)"
    )
    footer_2 = (
        f"<a href=\"{html.escape(pages_url)}\">Live Dashboard (1-Tap Copy)</a> | "
        f"<a href=\"{html.escape(repo_url.rstrip('/') + '/actions/workflows/dd_hourly.yml')}\">Trigger Fresh Run</a>\n"
        f"Full {ev.total_metrics}-row Markdown attached below (<code>btc_data_hub_latest.md</code>)."
    )

    p_blocks = [
        _format_telegram_panel_block(title, getattr(ev, attr, []) or [])
        for _, title, attr in PANEL_SPECS
    ]

    def _pack_html(head: str, blocks: List[str], foot: str = "") -> str:
        body = html.escape("\n\n".join(blocks))
        parts = [head, f"<pre>{body}</pre>"]
        if foot:
            parts.append(foot)
        return "\n".join(parts)

    msg1 = _pack_html(header_1, p_blocks[:3])
    msg2 = _pack_html(header_2, p_blocks[3:], footer_2)
    if len(msg1) <= max_len and len(msg2) <= max_len:
        return [msg1, msg2]

    # Fallback: dynamically split panels across as many messages as needed to honor max_len strictly
    messages: List[str] = []
    cur_blocks: List[str] = []
    cur_head = header_1
    for idx, blk in enumerate(p_blocks):
        candidate_blocks = cur_blocks + [blk]
        is_last = idx == len(p_blocks) - 1
        candidate = _pack_html(cur_head, candidate_blocks, footer_2 if is_last else "")
        if len(candidate) <= max_len or not cur_blocks:
            cur_blocks = candidate_blocks
        else:
            messages.append(_pack_html(cur_head, cur_blocks))
            cur_head = f"<b>BTC TAB [D: DATA HUB] (Part {len(messages) + 1})</b> — <b>${ev.spot_price:,.2f}</b>"
            cur_blocks = [blk]
    if cur_blocks:
        messages.append(_pack_html(cur_head, cur_blocks, footer_2))
    return messages


class _TelegramPermanentError(RuntimeError):
    """Non-retryable Telegram Bot API error (e.g. HTTP 400/401/403/404)."""


async def _curl_telegram_request(
    url: str,
    step_label: str,
    ip_flag: str = "--ipv4",
    json_payload: Optional[Dict[str, Any]] = None,
    form_fields: Optional[Dict[str, str]] = None,
    file_field: Optional[Tuple[str, pathlib.Path, str]] = None,
) -> None:
    """Executes a Telegram Bot API POST using curl (HTTP/1.1 without Expect: 100-continue)."""
    curl_bin = shutil.which("curl")
    if not curl_bin:
        raise RuntimeError("curl binary not available")

    tmp_json_path: Optional[pathlib.Path] = None
    try:
        cmd: List[str] = [
            curl_bin,
            "-sS",
            "--http1.1",
            ip_flag,
            "-H",
            "Expect:",
            "--connect-timeout",
            "10",
            "--max-time",
            "45",
        ]
        if json_payload is not None:
            with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".json") as tmp_f:
                tmp_f.write(json.dumps(json_payload, ensure_ascii=False).encode("utf-8"))
                tmp_json_path = pathlib.Path(tmp_f.name)
            cmd.extend(
                [
                    "-H",
                    "Content-Type: application/json",
                    "--data-binary",
                    f"@{tmp_json_path}",
                ]
            )
        else:
            for key, val in (form_fields or {}).items():
                cmd.extend(["--form-string", f"{key}={val}"])
            if file_field is not None:
                field_name, file_path, content_type = file_field
                cmd.extend(["-F", f"{field_name}=@{file_path};type={content_type}"])
        cmd.append(url)

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout_b, stderr_b = await asyncio.wait_for(proc.communicate(), timeout=50.0)
        except asyncio.TimeoutError as exc:
            proc.kill()
            await proc.communicate()
            raise RuntimeError(f"Telegram {step_label} curl ({ip_flag}) timed out") from exc

        stdout_s = stdout_b.decode("utf-8", errors="replace").strip()
        stderr_s = stderr_b.decode("utf-8", errors="replace").strip()
        if proc.returncode != 0:
            raise RuntimeError(
                f"Telegram {step_label} curl ({ip_flag}) exit={proc.returncode}: {stderr_s or stdout_s}"
            )
        try:
            parsed = json.loads(stdout_s) if stdout_s else {}
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"Telegram {step_label} curl ({ip_flag}) invalid JSON: {stdout_s[:200]}"
            ) from exc

        if not parsed.get("ok"):
            err_code = parsed.get("error_code")
            msg = f"Telegram {step_label} curl ({ip_flag}) error ({err_code}): {stdout_s[:300]}"
            if err_code is not None and err_code not in (429, 500, 502, 503, 504):
                raise _TelegramPermanentError(msg)
            raise RuntimeError(msg)
    finally:
        if tmp_json_path is not None and tmp_json_path.exists():
            try:
                tmp_json_path.unlink()
            except OSError:
                pass


async def _post_on_session(
    session: Any,
    timeout: aiohttp.ClientTimeout,
    url: str,
    step_label: str,
    json_payload: Optional[Dict[str, Any]] = None,
    form_fields: Optional[Dict[str, str]] = None,
    file_bytes: Optional[bytes] = None,
    file_name: Optional[str] = None,
) -> None:
    """Executes one Telegram Bot API POST on an existing Keep-Alive aiohttp session."""
    post_kwargs: Dict[str, Any] = {"timeout": timeout}
    if json_payload is not None:
        post_kwargs["json"] = json_payload
    else:
        form = aiohttp.FormData()
        for key, val in (form_fields or {}).items():
            form.add_field(key, val)
        if file_bytes is not None and file_name is not None:
            form.add_field(
                "document",
                file_bytes,
                filename=file_name,
                content_type="text/markdown",
            )
        post_kwargs["data"] = form

    async with session.post(url, **post_kwargs) as resp:
        if resp.status == 200:
            return
        err_body = await resp.text()
        msg = f"Telegram {step_label} failed ({resp.status}): {err_body}"
        if resp.status == 400 and json_payload is not None and "failed to get" in err_body.lower():
            raise RuntimeError(msg)
        if resp.status not in (429, 500, 502, 503, 504):
            raise _TelegramPermanentError(msg)
        raise RuntimeError(msg)


async def send_dd_to_telegram(
    token: str,
    chat_id: str,
    ev: DataHubEvaluation,
    md_path: pathlib.Path,
    utc_str: str,
    sgt_str: str,
    pages_url: str,
    repo_url: str,
) -> None:
    """Delivers split Tab D summary messages + `btc_data_hub_latest.md` over IPv4 Keep-Alive with URL fallback."""
    base_api = f"https://api.telegram.org/bot{token}"
    messages = build_telegram_messages(ev, utc_str, sgt_str, pages_url, repo_url)
    md_bytes = md_path.read_bytes()
    caption = (
        f"BTC Tab [D: DATA HUB] | Spot ${ev.spot_price:,.2f} | OK={ev.ok_count}/{ev.total_metrics} | {utc_str}"
    )
    timeout = aiohttp.ClientTimeout(total=45, connect=10, sock_connect=10, sock_read=40)
    has_curl = bool(shutil.which("curl"))
    raw_md_url = os.getenv("DD_RAW_MD_URL", "").strip()

    session: Any = None
    connector: Optional[aiohttp.TCPConnector] = None

    async def _ensure_session() -> Any:
        nonlocal session, connector
        if session is None:
            connector = aiohttp.TCPConnector(family=socket.AF_INET, force_close=False)
            raw_session = aiohttp.ClientSession(
                connector=connector,
                headers={"User-Agent": "curl/8.5.0"},
            )
            session = await raw_session.__aenter__()
        return session

    async def _reset_session() -> None:
        nonlocal session, connector
        cur_sess, cur_conn = session, connector
        session = None
        connector = None
        if cur_sess is not None:
            try:
                await cur_sess.__aexit__(None, None, None)
            except Exception:
                pass
        if cur_conn is not None and not cur_conn.closed:
            try:
                await cur_conn.close()
            except Exception:
                pass

    async def _run_attempts(step_label: str, attempts: List[Tuple[str, Any]]) -> None:
        last_exc: Optional[BaseException] = None
        total = len(attempts)
        for idx, (via, runner) in enumerate(attempts, 1):
            try:
                await runner()
                if idx > 1:
                    logger.info("Telegram %s succeeded on attempt %d/%d (%s)", step_label, idx, total, via)
                return
            except _TelegramPermanentError:
                raise
            except Exception as exc:
                last_exc = exc
                if via.startswith("aiohttp:"):
                    await _reset_session()
                if idx < total:
                    delay = 3.0 if idx == 1 else 5.0
                    logger.warning(
                        "Telegram %s attempt %d/%d (%s) failed (%s); waiting %.1fs before retry...",
                        step_label,
                        idx,
                        total,
                        via,
                        exc,
                        delay,
                    )
                    await asyncio.sleep(delay)
        if last_exc is not None:
            raise last_exc

    try:
        for i, text in enumerate(messages, 1):
            step_label = f"sendMessage part {i}"
            msg_payload = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            }
            msg_attempts: List[Tuple[str, Any]] = [
                (
                    f"aiohttp:ipv4#{attempt}",
                    lambda p=msg_payload, lbl=step_label: _post_step_via_session(
                        _ensure_session, timeout, f"{base_api}/sendMessage", lbl, json_payload=p
                    ),
                )
                for attempt in range(1, 3)
            ]
            if has_curl:
                msg_attempts.append(
                    (
                        "curl:--ipv4",
                        lambda p=msg_payload, lbl=step_label: _curl_telegram_request(
                            f"{base_api}/sendMessage", lbl, ip_flag="--ipv4", json_payload=p
                        ),
                    )
                )
            await _run_attempts(step_label, msg_attempts)
            await asyncio.sleep(1.2)

        doc_url = f"{base_api}/sendDocument"
        doc_fields = {"chat_id": chat_id, "caption": caption}
        doc_attempts: List[Tuple[str, Any]] = [
            (
                "aiohttp:multipart",
                lambda: _post_step_via_session(
                    _ensure_session,
                    timeout,
                    doc_url,
                    "sendDocument",
                    form_fields=doc_fields,
                    file_bytes=md_bytes,
                    file_name=md_path.name,
                ),
            )
        ]
        if raw_md_url:
            json_doc_payload = {"chat_id": chat_id, "document": raw_md_url, "caption": caption}
            doc_attempts.append(
                (
                    "aiohttp:json_url",
                    lambda jp=json_doc_payload: _post_step_via_session(
                        _ensure_session, timeout, doc_url, "sendDocument", json_payload=jp
                    ),
                )
            )
        else:
            doc_attempts.append(
                (
                    "aiohttp:multipart#2",
                    lambda: _post_step_via_session(
                        _ensure_session,
                        timeout,
                        doc_url,
                        "sendDocument",
                        form_fields=doc_fields,
                        file_bytes=md_bytes,
                        file_name=md_path.name,
                    ),
                )
            )
        if has_curl:
            doc_attempts.append(
                (
                    "curl:--ipv4",
                    lambda: _curl_telegram_request(
                        doc_url,
                        "sendDocument",
                        ip_flag="--ipv4",
                        form_fields=doc_fields,
                        file_field=("document", md_path, "text/markdown"),
                    ),
                )
            )
        await _run_attempts("sendDocument", doc_attempts)
    finally:
        await _reset_session()


async def _post_step_via_session(
    ensure_session_fn: Any,
    timeout: aiohttp.ClientTimeout,
    url: str,
    step_label: str,
    json_payload: Optional[Dict[str, Any]] = None,
    form_fields: Optional[Dict[str, str]] = None,
    file_bytes: Optional[bytes] = None,
    file_name: Optional[str] = None,
) -> None:
    active_session = await ensure_session_fn()
    await _post_on_session(
        active_session,
        timeout,
        url,
        step_label,
        json_payload=json_payload,
        form_fields=form_fields,
        file_bytes=file_bytes,
        file_name=file_name,
    )


def write_dashboard_artifacts(
    output_dir: pathlib.Path,
    ev: DataHubEvaluation,
    md_report: str,
    db_path: pathlib.Path,
    repo_url: str,
    pages_url: str,
    utc_str: str,
    sgt_str: str,
    also_write_logs: bool = True,
    store: Optional[StateStore] = None,
) -> Dict[str, pathlib.Path]:
    """Writes `btc_data_hub_latest.md`, `dd_latest.json`, and `index.html` into `output_dir`."""
    output_dir.mkdir(parents=True, exist_ok=True)
    md_path = output_dir / "btc_data_hub_latest.md"
    json_path = output_dir / "dd_latest.json"
    html_path = output_dir / "index.html"

    md_path.write_text(md_report, encoding="utf-8")
    if also_write_logs:
        logs_dir = BASE_DIR / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        (logs_dir / "btc_data_hub_latest.md").write_text(md_report, encoding="utf-8")
        downloads_dir = pathlib.Path.home() / "Downloads"
        if downloads_dir.exists():
            try:
                (downloads_dir / "btc_data_hub_latest.md").write_text(md_report, encoding="utf-8")
            except Exception:
                pass

    recent_archive = query_recent_archive(db_path, limit=30)
    payload = build_dd_json_payload(ev, md_report, recent_archive, utc_str, sgt_str, store=store)
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    html_path.write_text(render_dashboard_html(payload, repo_url=repo_url, pages_url=pages_url), encoding="utf-8")
    return {"md": md_path, "json": json_path, "html": html_path}


def load_evaluation_from_json(json_path: pathlib.Path) -> Tuple[DataHubEvaluation, str, str]:
    """Reconstructs a `DataHubEvaluation` and UTC/SGT timestamps from an existing `dd_latest.json`."""
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    panels = payload.get("panels") or {}
    kw: Dict[str, Any] = {
        "timestamp_utc": str(payload.get("retrieval_utc", "")),
        "spot_price": float(payload.get("spot_price", 0.0)),
        "total_metrics": int(payload.get("total_metrics", 0)),
        "ok_count": int(payload.get("ok_count", 0)),
        "unavailable_count": int(payload.get("unavailable_count", 0)),
        "stale_count": int(payload.get("stale_count", 0)),
        "proxy_or_static_count": int(payload.get("proxy_or_static_count", 0)),
        "archive_snapshots_count": int(payload.get("archive_snapshots_count", 0)),
        "archive_last_bar_utc": str(payload.get("archive_last_bar_utc", "")),
    }
    for panel_key, _, attr in PANEL_SPECS:
        rows = (panels.get(panel_key) or {}).get("rows") or []
        kw[attr] = [
            DataMetricRow(
                label=str(r["label"]),
                value=str(r["value"]),
                tabs=str(r.get("tabs", "")),
                status=str(r.get("status", "OK")),
            )
            for r in rows
        ]
    ev = DataHubEvaluation(**kw)
    return ev, str(payload.get("retrieval_utc", "")), str(payload.get("retrieval_sgt") or payload.get("retrieval_myt") or "")


async def run_publisher(
    output_dir: pathlib.Path,
    db_path: pathlib.Path,
    send_telegram: bool,
    no_telegram: bool,
    repo_url: str,
    pages_url: str,
    config: Optional[EngineConfig] = None,
    telegram_only: bool = False,
) -> DataHubEvaluation:
    """Runs one-shot warmup + read-only engine evaluation, publishes dashboard files, and notifies Telegram."""
    if telegram_only:
        json_path = output_dir / "dd_latest.json"
        md_path = output_dir / "btc_data_hub_latest.md"
        ev, utc_str, sgt_str = load_evaluation_from_json(json_path)
        paths: Dict[str, pathlib.Path] = {"md": md_path, "json": json_path}
    else:
        cfg = config or DEFAULT_CONFIG
        store = StateStore()
        detector = SignalDetector(cfg)
        detector.spot_swing_engine.set_read_only(True)
        detector.futures_v4_engine.set_read_only(True)
        # Defer archive write inside SignalDetector so custom --db-path receives the canonical write below
        detector.data_hub_engine = DataHubEngine(cfg, db_path=db_path, write_archive=False)

        logger.info("Running zero-cold-start REST & macro warmup...")
        await run_initial_warmup(cfg, store)
        detector.evaluate(store)

        ev = DataHubEngine(cfg, db_path=db_path, write_archive=True).evaluate(store)
        md_report = build_tab_d_data_only_report(cfg, store, db_path=db_path)

        now_utc = datetime.now(timezone.utc)
        utc_str = now_utc.strftime("%Y-%m-%d %H:%M:%S UTC")
        sgt_str = now_utc.astimezone(SGT_TZ).strftime("%Y-%m-%d %H:%M:%S SGT (UTC+8)")

        paths = write_dashboard_artifacts(
            output_dir=output_dir,
            ev=ev,
            md_report=md_report,
            db_path=db_path,
            repo_url=repo_url,
            pages_url=pages_url,
            utc_str=utc_str,
            sgt_str=sgt_str,
            store=store,
        )
        logger.info(
            "Published Tab [D]: Spot=$%.2f | OK=%d/%d | Archive=%d | Files=%s",
            ev.spot_price,
            ev.ok_count,
            ev.total_metrics,
            ev.archive_snapshots_count,
            ", ".join(p.name for p in paths.values()),
        )

    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    should_send_tg = (not no_telegram) and (send_telegram or telegram_only or (bool(token) and bool(chat_id)))
    if no_telegram:
        logger.info("Telegram delivery disabled (--no-telegram).")
    elif should_send_tg:
        if not token or not chat_id:
            logger.info("Telegram skipped (no TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID configured)")
        else:
            try:
                await send_dd_to_telegram(
                    token=token,
                    chat_id=chat_id,
                    ev=ev,
                    md_path=paths["md"],
                    utc_str=utc_str,
                    sgt_str=sgt_str,
                    pages_url=pages_url,
                    repo_url=repo_url,
                )
                logger.info("Delivered Tab [D] messages and %s to Telegram.", paths["md"].name)
            except Exception as exc:
                logger.warning(
                    "Telegram delivery failed after retries (%s); GitHub Pages artifacts preserved.",
                    exc,
                )
    else:
        logger.info("Telegram skipped (no TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID configured)")

    return ev


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Headless Tab [D: DATA HUB] publisher for GitHub Pages and Telegram."
    )
    parser.add_argument(
        "--output-dir",
        type=pathlib.Path,
        default=BASE_DIR / "docs",
        help="Directory for static GitHub Pages artifacts (default: docs/).",
    )
    parser.add_argument(
        "--db-path",
        type=pathlib.Path,
        default=DEFAULT_ARCHIVE_DB_PATH,
        help="Path to SQLite 4H telemetry archive (default: data/dd_telemetry_history.sqlite).",
    )
    parser.add_argument(
        "--send-telegram",
        action="store_true",
        help="Send split Tab D summary and .md document to Telegram (requires TELEGRAM_BOT_TOKEN & TELEGRAM_CHAT_ID).",
    )
    parser.add_argument(
        "--telegram-only",
        action="store_true",
        help="Skip warmup/artifact generation and deliver existing output-dir artifacts to Telegram.",
    )
    parser.add_argument(
        "--no-telegram",
        action="store_true",
        help="Skip Telegram delivery even if TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID are set.",
    )
    parser.add_argument(
        "--repo-url",
        type=str,
        default=os.getenv("GITHUB_REPOSITORY_URL", "https://github.com/aikeluargalee-tech/btc-swing-engine"),
        help="GitHub repository URL for on-demand workflow trigger button.",
    )
    parser.add_argument(
        "--pages-url",
        type=str,
        default=os.getenv("DD_DASHBOARD_URL", "https://aikeluargalee-tech.github.io/btc-swing-engine/"),
        help="Published GitHub Pages URL included in Telegram alerts.",
    )
    return parser.parse_args()


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    args = parse_args()
    asyncio.run(
        run_publisher(
            output_dir=args.output_dir,
            db_path=args.db_path,
            send_telegram=args.send_telegram,
            no_telegram=args.no_telegram,
            repo_url=args.repo_url,
            pages_url=args.pages_url,
            telegram_only=args.telegram_only,
        )
    )


if __name__ == "__main__":
    main()
