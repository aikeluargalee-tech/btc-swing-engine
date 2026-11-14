"""Tab [21: D] Unified Data Hub Engine (DD v2).

Aggregates all canonical raw market feeds, multi-timeframe technical indicators,
volume profile/liquidation anchors, order flow & quant math metrics, derivatives
& options positioning, on-chain/ETF/stablecoin flows, macro/credit/US liquidity,
and historical SQLite archiving across Tabs 0-20 into one neutral repository.

Zero-Hallucination & Read-Only Rules:
- Performs zero network I/O and mutates zero upstream trading state.
- Missing/offline metrics emit explicit "DATA UNAVAILABLE" with status "UNAVAILABLE".
- Synthetic/placeholder values (e.g. 200D SMA MVRV fallback or Yahoo ETF tape
  volume proxy) are explicitly tagged "PROXY" so they are never mistaken for
  primary feeds; static SOPR=1.02 fallbacks are retired to "UNAVAILABLE".
"""

from __future__ import annotations

import json
import math
import os
import pathlib
import sqlite3
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence, Tuple

from config.settings import DEFAULT_CONFIG, EngineConfig
from core.state_store import StateStore


UNAVAILABLE = "DATA UNAVAILABLE"
DEFAULT_ARCHIVE_DB_PATH = (
    pathlib.Path(__file__).resolve().parent.parent / "data" / "dd_telemetry_history.sqlite"
)
_LAST_ARCHIVED_STATE_BY_DB: Dict[str, Tuple[str, int, str]] = {}


@dataclass
class DataMetricRow:
    """Single canonical telemetry row rendered inside a Data Hub panel."""

    label: str
    value: str
    tabs: str
    status: str = "OK"  # OK | UNAVAILABLE | STALE | PROXY | STATIC


@dataclass
class DataHubEvaluation:
    """Complete 6-panel consolidated telemetry snapshot for Tab [21: D]."""

    timestamp_utc: str = ""
    spot_price: float = 0.0
    total_metrics: int = 0
    ok_count: int = 0
    unavailable_count: int = 0
    stale_count: int = 0
    proxy_or_static_count: int = 0
    panel_1_feeds: List[DataMetricRow] = field(default_factory=list)
    panel_2_trend_vol: List[DataMetricRow] = field(default_factory=list)
    panel_3_structure_magnets: List[DataMetricRow] = field(default_factory=list)
    panel_4_flow_quant: List[DataMetricRow] = field(default_factory=list)
    panel_5_derivs_liq: List[DataMetricRow] = field(default_factory=list)
    panel_6_macro_onchain: List[DataMetricRow] = field(default_factory=list)
    archive_snapshots_count: int = 0
    archive_last_bar_utc: str = ""


def _valid_num(val: Any, allow_zero: bool = True) -> bool:
    if val is None or isinstance(val, bool):
        return False
    try:
        f = float(val)
    except (TypeError, ValueError):
        return False
    if math.isnan(f) or math.isinf(f):
        return False
    return allow_zero or f != 0.0


def _fmt_price(val: Any) -> Optional[str]:
    return f"${float(val):,.2f}" if _valid_num(val, allow_zero=False) else None


def _fmt_num(val: Any, fmt: str = "+,.2f", allow_zero: bool = True, suffix: str = "") -> Optional[str]:
    if not _valid_num(val, allow_zero=allow_zero):
        return None
    return f"{float(val):{fmt}}{suffix}"


def _row(label: str, val: Optional[str], tabs: str, status: str = "OK") -> DataMetricRow:
    if val is None:
        return DataMetricRow(label=label, value=UNAVAILABLE, tabs=tabs, status="UNAVAILABLE")
    return DataMetricRow(label=label, value=val, tabs=tabs, status=status)


def _first_num(*vals: Any, allow_zero: bool = True) -> Optional[float]:
    for v in vals:
        if _valid_num(v, allow_zero=allow_zero):
            return float(v)
    return None


def _bar_meta(bars: Sequence[Any]) -> str:
    if not bars:
        return "0 bars (UNAVAILABLE)"
    last = bars[-1]
    ts_ms = getattr(last, "timestamp_ms", 0) or 0
    dt_str = datetime.fromtimestamp(ts_ms / 1000.0, tz=timezone.utc).strftime("%m-%d %H:%M UTC") if ts_ms else "?"
    return f"{len(bars)} bars · {dt_str}"


def _tick_age_str(connected: bool, ts: float, now_ts: float) -> Tuple[str, str]:
    state = "ON" if connected else "SYNC"
    if not ts or ts <= 0:
        return f"{state} (no tick)", "OK" if connected else "STALE"
    age = max(0.0, now_ts - ts)
    status = "STALE" if (not connected or age > 30.0) else "OK"
    return f"{state} ({age:.0f}s ago)", status


def _compute_4h_rsi_roc(store: StateStore) -> Tuple[Optional[float], Optional[float]]:
    """Computes closed-4H Wilder RSI(14) and ROC(12) across available 4H history."""
    bars = list(getattr(store, "spot_klines_4h", []) or [])
    if len(bars) < 20:
        return None, None
    closes = [float(b.close) for b in bars[:-1] if getattr(b, "close", 0) > 0]
    if len(closes) < 16:
        return None, None
    deltas = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
    gains = [max(d, 0.0) for d in deltas]
    losses = [max(-d, 0.0) for d in deltas]
    avg_g = sum(gains[:14]) / 14.0
    avg_l = sum(losses[:14]) / 14.0
    for g, l in zip(gains[14:], losses[14:]):
        avg_g = (avg_g * 13.0 + g) / 14.0
        avg_l = (avg_l * 13.0 + l) / 14.0
    rsi = 100.0 if avg_l == 0.0 else round(100.0 - (100.0 / (1.0 + (avg_g / avg_l))), 2)
    roc12 = ((closes[-1] / closes[-13]) - 1.0) * 100.0 if len(closes) >= 13 and closes[-13] > 0 else None
    return rsi, roc12


def _fmt_usd_compact(val: Any, signed: bool = False) -> Optional[str]:
    """Formats large USD values in compact $B / $M notation."""
    if not _valid_num(val):
        return None
    v = float(val)
    sign = ("+" if v >= 0 else "-") if signed else ("-" if v < 0 else "")
    av = abs(v)
    if av >= 1e9:
        return f"{sign}${av / 1e9:.2f}B"
    if av >= 1e6:
        return f"{sign}${av / 1e6:.1f}M"
    return f"{sign}${av:,.0f}"


def _is_test_runner() -> bool:
    """True under unittest/pytest so unconfigured calls avoid polluting the live DB."""
    if os.environ.get("BTC_DISABLE_TELEMETRY_ARCHIVE") == "1":
        return True
    if "pytest" in sys.modules:
        return True
    main_mod = sys.modules.get("__main__")
    spec_name = getattr(getattr(main_mod, "__spec__", None), "name", "") or ""
    if spec_name.startswith(("unittest", "pytest")):
        return True
    main_file = os.path.basename(str(getattr(main_mod, "__file__", "") or ""))
    return main_file.startswith("test_")


def record_and_query_telemetry_archive(
    ev: DataHubEvaluation,
    closed_4h_utc: Optional[str],
    db_path: Optional[pathlib.Path] = None,
    write_enabled: bool = True,
) -> Tuple[int, str]:
    """Persists one deduplicated telemetry snapshot per closed 4H bar into SQLite.

    Returns `(total_snapshots, latest_closed_4h_bar_utc)`. Fail-soft on I/O errors
    so the 2 Hz HUD loop never stalls.
    """
    db = pathlib.Path(db_path) if db_path is not None else DEFAULT_ARCHIVE_DB_PATH
    db_key = str(db.resolve())
    bar_key = (closed_4h_utc or "").strip()
    can_write = bool(write_enabled and bar_key and ev.spot_price > 0.0)

    cached = _LAST_ARCHIVED_STATE_BY_DB.get(db_key)
    if can_write and cached is not None and cached[0] == bar_key and db.exists():
        return cached[1], cached[2]

    if not db.exists() and not can_write:
        return 0, ""

    conn: Optional[sqlite3.Connection] = None
    try:
        if can_write:
            db.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(db), timeout=2.0)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS telemetry_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                closed_4h_bar_utc TEXT NOT NULL UNIQUE,
                retrieval_utc TEXT NOT NULL,
                spot_price REAL NOT NULL,
                ok_count INTEGER NOT NULL,
                unavailable_count INTEGER NOT NULL,
                stale_count INTEGER NOT NULL,
                proxy_or_static_count INTEGER NOT NULL,
                payload_json TEXT NOT NULL
            )
            """
        )
        if can_write:
            payload = {
                "schema_version": "dd_v2",
                "instrument": "BTCUSDT",
                "closed_4h_bar_utc": bar_key,
                "retrieval_utc": ev.timestamp_utc,
                "spot_price": ev.spot_price,
                "panels": {
                    name: [
                        {"label": r.label, "value": r.value, "tabs": r.tabs, "status": r.status}
                        for r in rows
                    ]
                    for name, rows in (
                        ("1_price_trend_structure", ev.panel_1_feeds),
                        ("2_order_flow_liquidity", ev.panel_2_trend_vol),
                        ("3_derivatives_options_liq", ev.panel_3_structure_magnets),
                        ("4_onchain_etf_stablecoins", ev.panel_4_flow_quant),
                        ("5_macro_credit_liquidity", ev.panel_5_derivs_liq),
                        ("6_quant_feeds_archive", ev.panel_6_macro_onchain),
                    )
                },
            }
            conn.execute(
                """
                INSERT OR IGNORE INTO telemetry_snapshots (
                    closed_4h_bar_utc,
                    retrieval_utc,
                    spot_price,
                    ok_count,
                    unavailable_count,
                    stale_count,
                    proxy_or_static_count,
                    payload_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    bar_key,
                    ev.timestamp_utc,
                    float(ev.spot_price),
                    int(ev.ok_count),
                    int(ev.unavailable_count),
                    int(ev.stale_count),
                    int(ev.proxy_or_static_count),
                    json.dumps(payload, separators=(",", ":")),
                ),
            )
            conn.commit()

        row = conn.execute(
            "SELECT COUNT(*), COALESCE(MAX(closed_4h_bar_utc), '') FROM telemetry_snapshots"
        ).fetchone()
        cnt = int(row[0]) if row else 0
        last_bar = str(row[1]) if row and row[1] else ""
        if can_write:
            _LAST_ARCHIVED_STATE_BY_DB[db_key] = (bar_key, cnt, last_bar)
        return cnt, last_bar
    except sqlite3.Error:
        return 0, ""
    finally:
        if conn is not None:
            conn.close()


class DataHubEngine:
    """Builds a unified, deduplicated 6-panel Data Hub evaluation from StateStore."""

    def __init__(
        self,
        config: Optional[EngineConfig] = None,
        db_path: Optional[pathlib.Path] = None,
        write_archive: Optional[bool] = None,
    ) -> None:
        self.config = config or DEFAULT_CONFIG
        self._db_path = pathlib.Path(db_path) if db_path is not None else None
        if write_archive is not None:
            self._write_archive = bool(write_archive)
        elif self._db_path is not None:
            self._write_archive = True
        else:
            self._write_archive = not _is_test_runner()

    def evaluate(self, store: StateStore) -> DataHubEvaluation:
        """Collects canonical metrics across all active evaluations and raw feeds."""
        now_dt = datetime.now(timezone.utc)
        now_ts = time.time()

        sig = getattr(store, "latest_signal", None)
        proto = getattr(store, "protocol_evaluation", None)
        macro_ev = getattr(store, "macro_evaluation", None)
        rm = getattr(store, "regime_matrix_evaluation", None)
        mm = getattr(store, "mm_btc_evaluation", None)
        vc = getattr(store, "volatility_cone_evaluation", None)
        trap = getattr(store, "trap_evaluation", None)
        liq_rep = getattr(store, "liquidation_report", None)
        exh = getattr(store, "exhaustion_evaluation", None)
        fp = getattr(store, "footprint_evaluation", None)
        ss = getattr(store, "spot_swing_evaluation", None)
        slsp = getattr(store, "slsp_evaluation", None)
        grok = getattr(store, "grok_quant_evaluation", None)
        ssrn = getattr(store, "ssrn_alpha_evaluation", None)
        mag = getattr(store, "btc_magnet_evaluation", None)
        rec = getattr(store, "reconciliation_evaluation", None)
        tp = getattr(store, "trend_pullback_evaluation", None)
        fg = getattr(store, "four_gate_evaluation", None)
        fv4 = getattr(store, "futures_v4_evaluation", None)
        mi = getattr(store, "macro_intermarket", None)
        flow = getattr(store, "flow_snapshot", None)
        deriv = getattr(store, "derivatives_snapshot", None)

        spot_px = _first_num(store.binance_spot_price, getattr(sig, "current_price", None), allow_zero=False) or 0.0
        perp_px = _first_num(store.binance_perp_price, getattr(deriv, "binance_perp_price", None), allow_zero=False)
        cb_px = _first_num(store.coinbase_spot_price, getattr(deriv, "coinbase_price", None), allow_zero=False)

        # --- Extract upstream evaluations & structural inputs across all 6 domains ---
        sp_ws_s, sp_ws_st = _tick_age_str(bool(store.spot_ws_connected), store.last_spot_tick_ts, now_ts)
        pp_ws_s, pp_ws_st = _tick_age_str(bool(store.perp_ws_connected), store.last_perp_tick_ts, now_ts)
        cb_ws_s, cb_ws_st = _tick_age_str(bool(store.coinbase_ws_connected), store.last_cb_tick_ts, now_ts)
        closed_4h_utc = getattr(fg, "last_closed_bar_utc", None) or getattr(fv4, "last_4h_close_utc", None)

        excl_bars = getattr(store, "perp_estimated_bars_excluded", {}) or {}
        excl_total = sum(excl_bars.values()) if isinstance(excl_bars, dict) else 0

        liq_status_val: Optional[str] = None
        liq_status_tag = "UNAVAILABLE"
        if liq_rep is not None and getattr(liq_rep, "is_available", False):
            is_stale = bool(getattr(liq_rep, "is_stale", False))
            liq_status_val = "STALE (cached)" if is_stale else f"ONLINE ({getattr(liq_rep, 'magnitude_tier', 'OK')})"
            liq_status_tag = "STALE" if is_stale else "OK"

        rec_val: Optional[str] = None
        if rec is not None:
            td = getattr(rec, "time_delta_sec", None)
            td_s = f"{float(td):.0f}s delta" if _valid_num(td) else "synced"
            rec_val = f"{getattr(rec, 'verdict', 'UNKNOWN')} ({td_s})"

        # Domain 1: Price, Trend & Market Structure
        sma200_1d = _first_num(getattr(macro_ev, "sma_200_1d", None), getattr(tp, "daily_sma200", None), getattr(grok, "sma_200_1d", None), allow_zero=False)
        sma200_slope = _first_num(getattr(macro_ev, "sma_200_slope_5d_pct", None), getattr(tp, "daily_sma200_slope_20d", None))
        sma50_1d = _first_num(getattr(tp, "daily_sma50", None), getattr(getattr(ss, "macro", None), "ema50", None), getattr(proto, "sma_50_1d", None), allow_zero=False)
        ema21_1d = _first_num(getattr(macro_ev, "ema_21_1d", None), allow_zero=False)
        ema50_1d = _first_num(getattr(rm, "ema_50_1d", None), getattr(grok, "ema_50_1d", None), allow_zero=False)
        ema50_1w = _first_num(getattr(tp, "ema50_1w", None), allow_zero=False)
        ema50_4h = _first_num(getattr(tp, "ema50_4h", None), allow_zero=False)
        ema200_4h = _first_num(getattr(tp, "ema200_4h", None), allow_zero=False)
        ema9_g = _first_num(getattr(grok, "ema_9", None), allow_zero=False)
        ema21_g = _first_num(getattr(grok, "ema_21", None), allow_zero=False)
        sma200_1h = _first_num(getattr(mm, "sma_200_1h", None), allow_zero=False)

        grok_vwap = _first_num(getattr(grok, "vwap_daily", None), allow_zero=False)
        d_vwap = _first_num(grok_vwap, getattr(rm, "daily_vwap", None), getattr(fp, "daily_vwap", None), allow_zero=False)
        w_vwap = _first_num(getattr(rm, "weekly_vwap", None), allow_zero=False)
        vwap_z = _first_num(getattr(grok, "vwap_stretch_z", None)) if grok_vwap is not None else None

        rsi_1d = _first_num(getattr(macro_ev, "rsi_14_1d", None), allow_zero=False)
        rsi_4h, roc12_4h = _compute_4h_rsi_roc(store)
        adx_1d = _first_num(getattr(getattr(sig, "ema_strategy", None), "daily_adx", None), getattr(slsp, "ema_3_adx", None), allow_zero=False)
        adx_4h = _first_num(getattr(getattr(sig, "ema_strategy", None), "adx_4h", None), allow_zero=False)
        atr_1d = _first_num(getattr(proto, "atr_14_1d", None), allow_zero=False)
        atr_4h = _first_num(getattr(sig, "atr_4h", None), getattr(tp, "atr14_4h", None), getattr(proto, "atr_14_4h", None), allow_zero=False)
        atr_1h = _first_num(getattr(sig, "atr_1h", None), allow_zero=False)

        mv = store.macro_profile
        tv = store.tactical_profile
        sv = store.session_profile
        l20 = _first_num(getattr(fg, "gate_3_l20", None), allow_zero=False)
        h20 = _first_num(getattr(fg, "loop_b_g3_h20", None), allow_zero=False)
        pwh = _first_num(getattr(getattr(ss, "setup", None), "pwh", None), allow_zero=False)
        pwl = _first_num(getattr(getattr(ss, "setup", None), "pwl", None), allow_zero=False)
        asia_h = _first_num(getattr(trap, "asia_high", None), getattr(fp, "asia_high", None), allow_zero=False)
        asia_l = _first_num(getattr(trap, "asia_low", None), getattr(fp, "asia_low", None), allow_zero=False)
        nsup = getattr(getattr(slsp, "nearest_support", None), "center_price", None)
        nres = getattr(getattr(slsp, "nearest_resistance", None), "center_price", None)

        struct_any = any(v is not None for v in (l20, h20, pwl, pwh, asia_l, asia_h))
        struct_str = (
            f"4H:{_fmt_price(l20) or 'N/A'}-{_fmt_price(h20) or 'N/A'} | "
            f"PW:{_fmt_price(pwl) or 'N/A'}-{_fmt_price(pwh) or 'N/A'} | "
            f"Asia:{_fmt_price(asia_l) or 'N/A'}-{_fmt_price(asia_h) or 'N/A'}"
        ) if struct_any else None

        panel_1 = [
            _row("Binance Spot / Perp ($)", f"{_fmt_price(spot_px) or UNAVAILABLE} / {_fmt_price(perp_px) or UNAVAILABLE}", "All Tabs", "OK" if spot_px > 0 else "UNAVAILABLE"),
            _row("Coinbase Spot ($)", _fmt_price(cb_px), "1,11,15,17"),
            _row("1D SMA 200 / Slope", f"{_fmt_price(sma200_1d)} ({_fmt_num(sma200_slope, '+.2f', True, '%') or 'N/A'})" if sma200_1d else None, "0,2,3,11,15,18"),
            _row("1D SMA 50 / EMA 50", f"{_fmt_price(sma50_1d) or UNAVAILABLE} / {_fmt_price(ema50_1d) or UNAVAILABLE}" if (sma50_1d or ema50_1d) else None, "0,2,4,15,18,20"),
            _row("1D EMA 21 / 1W EMA 50", f"{_fmt_price(ema21_1d) or UNAVAILABLE} / {_fmt_price(ema50_1w) or UNAVAILABLE}" if (ema21_1d or ema50_1w) else None, "3,18"),
            _row("4H EMA 50 / EMA 200", f"{_fmt_price(ema50_4h) or UNAVAILABLE} / {_fmt_price(ema200_4h) or UNAVAILABLE}" if (ema50_4h or ema200_4h) else None, "7,13,18,20"),
            _row("Grok EMA 9/21 & 1H SMA200", f"9:{_fmt_price(ema9_g) or 'N/A'} · 21:{_fmt_price(ema21_g) or 'N/A'} · 1H:{_fmt_price(sma200_1h) or 'N/A'}" if (ema9_g or ema21_g or sma200_1h) else None, "5,15"),
            _row("Daily / Weekly VWAP (Z)", f"D:{_fmt_price(d_vwap) or 'N/A'} ({_fmt_num(vwap_z, '+.2f', True, 'σ') or 'N/A'}) | W:{_fmt_price(w_vwap) or 'N/A'}" if (d_vwap or w_vwap) else None, "4,11,15"),
            _row("RSI(14) 1D / 4H & 4H ROC12", f"1D:{_fmt_num(rsi_1d, '.1f') or 'N/A'} · 4H:{_fmt_num(rsi_4h, '.1f') or 'N/A'} · ROC:{_fmt_num(roc12_4h, '+.2f', True, '%') or 'N/A'}" if (rsi_1d is not None or rsi_4h is not None) else None, "3,7,20"),
            _row("ADX(14) 1D/4H & ATR(14)", f"ADX 1D:{_fmt_num(adx_1d, '.1f') or 'N/A'} 4H:{_fmt_num(adx_4h, '.1f') or 'N/A'} | ATR:{_fmt_price(atr_1d) or 'N/A'}/{_fmt_price(atr_4h) or 'N/A'}/{_fmt_price(atr_1h) or 'N/A'}" if (adx_1d or adx_4h or atr_1d or atr_4h or atr_1h) else None, "0,1,2,8,13,18,20"),
            _row("Macro 30D VAH / POC / VAL", f"{_fmt_price(mv.c_vah)} / {_fmt_price(mv.c_poc)} / {_fmt_price(mv.c_val)}" if mv else None, "1,3,6,11,19"),
            _row("Structure (L20/H20, PW, Asia)", struct_str, "0,8,11,19"),
        ]

        # Domain 2: Order Flow, Footprint & Liquidity (panel_2_trend_vol slot)
        w15 = getattr(flow, "w_15m", None)
        w1h = getattr(flow, "w_1h", None)
        w4h = getattr(flow, "w_4h", None)
        w24 = getattr(flow, "w_24h", None)

        d_flow = _first_num(getattr(fg, "loop_a_g2_val", None), getattr(w24, "flow_divergence_z", None))
        z_s_24 = _first_num(getattr(fg, "loop_a_g2_z_s", None), getattr(w24, "spot_zscore", None))
        z_f_24 = _first_num(getattr(fg, "loop_a_g2_z_f", None), getattr(w24, "perp_zscore", None))

        cpi_usd = _first_num(getattr(deriv, "coinbase_premium_usd", None), getattr(grok, "coinbase_premium_usd", None), getattr(fp, "cpi_usd", None))
        cpi_pct = _first_num(getattr(deriv, "coinbase_premium_pct", None), getattr(grok, "coinbase_premium_pct", None), getattr(fp, "cpi_pct", None))
        cpi_z = _first_num(getattr(deriv, "coinbase_premium_zscore", None), getattr(grok, "coinbase_premium_zscore", None), getattr(fp, "cpi_zscore", None))

        klines_1h = list(getattr(store, "spot_klines_1h", []) or [])
        bn_vol_24h = sum(float(b.volume) for b in klines_1h[-24:]) if len(klines_1h) >= 24 else None
        cb_vol_24h = _first_num(getattr(mi, "coinbase_spot_vol_24h_btc", None), allow_zero=False)
        tot_vol_24h = (bn_vol_24h or 0.0) + (cb_vol_24h or 0.0)
        xexch_vol_str = (
            f"BN:{_fmt_num(bn_vol_24h, ',.0f', False) or 'N/A'} · CB:{_fmt_num(cb_vol_24h, ',.0f', False) or 'N/A'} · Tot:{tot_vol_24h:,.0f} BTC"
            if (bn_vol_24h or cb_vol_24h) else None
        )

        depth_1p = _first_num(getattr(mi, "orderbook_depth_ratio_1pct", None))
        depth_2p = _first_num(getattr(mi, "orderbook_depth_ratio_2pct", None))
        spread_bps = _first_num(getattr(mi, "orderbook_spread_bps", None))
        obi_pct = _first_num(getattr(ssrn, "live_obi_ratio_pct", None))
        depth_ok = any(x is not None for x in (depth_1p, depth_2p, spread_bps, obi_pct))
        if spread_bps is not None and 0.0 < abs(spread_bps) < 0.01:
            spread_fmt: Optional[str] = f"{spread_bps:.4f}bps"
        else:
            spread_fmt = _fmt_num(spread_bps, '.2f', True, 'bps')
        depth_str = (
            f"1%:{_fmt_num(depth_1p, '.2f', False, 'x') or 'N/A'} · 2%:{_fmt_num(depth_2p, '.2f', False, 'x') or 'N/A'} · "
            f"Spr:{spread_fmt or 'N/A'} · OBI:{_fmt_num(obi_pct, '+.1f', True, '%') or 'N/A'}"
        ) if depth_ok else None

        vp_tact_s = f"{_fmt_price(tv.c_vah)}/{_fmt_price(tv.c_poc)}/{_fmt_price(tv.c_val)}" if tv else "N/A"
        vp_sess_s = f"{_fmt_price(sv.c_vah)}/{_fmt_price(sv.c_poc)}/{_fmt_price(sv.c_val)}" if sv else "N/A"
        vp_pair_str = f"7D:{vp_tact_s} | 24H:{vp_sess_s}" if (tv or sv) else None

        ws_trades_active = bool(store.spot_trade_count or store.perp_trade_count)
        day_cvd_seeded = bool(
            store.spot_klines_15m
            or store.perp_klines_15m
            or store.utc_day_spot_cvd != 0.0
            or store.utc_day_perp_cvd != 0.0
        )
        sess_cvd_tabs = "Live WS" if ws_trades_active else ("REST 15m" if day_cvd_seeded else "Live WS")
        sess_cvd_status = "OK" if (ws_trades_active or day_cvd_seeded) else "UNAVAILABLE"

        panel_2 = [
            _row("Spot/Perp CVD (15m / 1h)", f"15m:{_fmt_num(getattr(w15, 'spot_delta_btc', None), '+.1f')}/{_fmt_num(getattr(w15, 'perp_delta_btc', None), '+.1f')} | 1h:{_fmt_num(getattr(w1h, 'spot_delta_btc', None), '+.1f')}/{_fmt_num(getattr(w1h, 'perp_delta_btc', None), '+.1f')} BTC" if (w15 and w1h) else None, "1,8,15"),
            _row("Spot/Perp CVD (4h / 24h)", f"4h:{_fmt_num(getattr(w4h, 'spot_delta_btc', None), '+.1f')}/{_fmt_num(getattr(w4h, 'perp_delta_btc', None), '+.1f')} | 24h:{_fmt_num(getattr(w24, 'spot_delta_btc', None), '+.1f')}/{_fmt_num(getattr(w24, 'perp_delta_btc', None), '+.1f')} BTC" if (w4h and w24) else None, "0,1,15,16,17"),
            _row("Session / UTC-Day CVD", f"Sess S:{store.session_spot_cvd:+.1f} P:{store.session_perp_cvd:+.1f} | Day S:{store.utc_day_spot_cvd:+.1f} P:{store.utc_day_perp_cvd:+.1f}", sess_cvd_tabs, sess_cvd_status),
            _row("24H Z-Scores (z_S / z_F / D)", f"z_S:{_fmt_num(z_s_24, '+.2f') or 'N/A'} · z_F:{_fmt_num(z_f_24, '+.2f') or 'N/A'} · D:{_fmt_num(d_flow, '+.2f') or 'N/A'}", "1,19", "OK" if d_flow is not None else "UNAVAILABLE"),
            _row("15m Footprint Delta / Stack", f"Δ:{_fmt_num(getattr(fp, 'active_bar_delta', None), '+.1f', True, ' BTC')} (Prev:{_fmt_num(getattr(fp, 'prev_bar_delta', None), '+.1f')}) · Stacks:{getattr(fp, 'stacked_imbalances_count', 0)}" if fp else None, "1,11"),
            _row("Coinbase Premium ($ / % / Z)", f"{_fmt_num(cpi_usd, '+,.1f', True, '$') or 'N/A'} ({_fmt_num(cpi_pct, '+.3f', True, '%') or 'N/A'}, Z={_fmt_num(cpi_z, '+.2f') or 'N/A'})", "1,11,15", "OK" if cpi_usd is not None else "UNAVAILABLE"),
            _row("Cross-Exch 24H Spot Vol (BN/CB)", xexch_vol_str, "1,11,Macro"),
            _row("L2 Depth ±1%/±2%, OBI & Spread", depth_str, "16,Macro"),
            _row("Tactical 7D / Session 24H VP", vp_pair_str, "1,11"),
            _row("VA Pos% & Dist to VAL", f"{_fmt_num(getattr(sig, 'va_position_pct', None), '.1f', True, '%')} | {_fmt_num(getattr(sig, 'distance_to_val_pct', None), '+.2f', True, '%')} ({_fmt_num(getattr(sig, 'distance_to_val_atr', None), '+.2f', True, ' ATR')})" if sig else None, "1"),
            _row("SLSP Support / Resistance", f"Sup:{_fmt_price(nsup) or 'N/A'} | Res:{_fmt_price(nres) or 'N/A'}" if (nsup or nres) else None, "13"),
        ]

        # Domain 3: Derivatives, Options & Liquidations (panel_3_structure_magnets slot)
        oi_btc = _first_num(store.open_interest_btc, getattr(deriv, "open_interest_btc", None), allow_zero=False)
        oi_usd = _first_num(store.open_interest_usd, getattr(deriv, "open_interest_usd", None), allow_zero=False)
        agg_oi_b = _first_num(getattr(mi, "agg_perp_oi_btc", None), allow_zero=False)
        agg_oi_u = _first_num(getattr(mi, "agg_perp_oi_usd", None), allow_zero=False)
        agg_fund = _first_num(getattr(mi, "agg_perp_funding_8h_pct", None))
        agg_venues = getattr(mi, "agg_perp_venues_str", None) or "Agg"

        oi_15 = _first_num(getattr(deriv, "oi_change_15m_pct", None))
        oi_1h = _first_num(getattr(deriv, "oi_change_1h_pct", None))
        oi_4h = _first_num(getattr(deriv, "oi_change_4h_pct", None))
        oi_24h = _first_num(getattr(rm, "oi_change_24h_pct", None), getattr(getattr(ss, "magnet", None), "oi_change_24h_pct", None))
        quad_raw = getattr(deriv, "oi_regime_quadrant", None)
        quad_val = getattr(quad_raw, "value", getattr(quad_raw, "name", str(quad_raw))) if quad_raw is not None else None
        oi_deltas_ok = any(x is not None for x in (oi_15, oi_1h, oi_4h, oi_24h))

        fund_8h = _first_num(store.funding_rate_pct, getattr(deriv, "funding_rate_pct", None))
        fund_ann = _first_num(getattr(ssrn, "annualized_funding_pct", None), getattr(mag, "funding_rate_annual_pct", None))
        if fund_ann is None and fund_8h is not None:
            fund_ann = fund_8h * 3.0 * 365.0
        fund_p90 = _first_num(getattr(fg, "loop_a_g4_funding_p90", None))
        basis_usd = _first_num(getattr(deriv, "perp_basis_usd", None))
        basis_ann = _first_num(getattr(rm, "annualized_basis_pct", None))
        basis_raw_pct = (basis_usd / spot_px) * 100.0 if (basis_usd is not None and spot_px > 0) else None
        if basis_raw_pct is not None and basis_ann is not None:
            basis_str: Optional[str] = f"{_fmt_num(basis_usd, '+,.1f', True, '$')} ({basis_raw_pct:+.3f}% | Carry:{_fmt_num(basis_ann, '+.2f', True, '%/yr')})"
        elif basis_usd is not None or basis_ann is not None:
            basis_str = f"{_fmt_num(basis_usd, '+,.1f', True, '$') or 'N/A'} ({_fmt_num(basis_ann, '+.2f', True, '%') or 'N/A'})"
        else:
            basis_str = None

        t5_ok = store.open_interest_btc > 0 and _valid_num(store.taker_long_short_ratio_5m, False)
        top_ok = store.top_trader_ls_ratio > 0
        glob_ok = _valid_num(store.global_account_ls_ratio, False)
        acct_any = t5_ok or top_ok or glob_ok
        top_s = f"{store.top_trader_ls_ratio:.2f}({store.top_trader_long_pct:.0f}L)" if top_ok else "N/A"
        acct_str = (
            f"5m:{_fmt_num(store.taker_long_short_ratio_5m, '.3f', False) or 'N/A'} (Δ:{_fmt_num(store.perp_5m_delta_btc, '+.1f') or 'N/A'}) | "
            f"Top:{top_s} · Glb:{_fmt_num(store.global_account_ls_ratio, '.2f', False) or 'N/A'}"
        ) if acct_any else None

        pc_oi = _first_num(getattr(mi, "options_put_call_oi_ratio", None), allow_zero=False)
        opt_oi = _first_num(getattr(mi, "options_total_oi_btc", None), allow_zero=False)
        iv_front = _first_num(getattr(mi, "options_iv_front", None), allow_zero=False)
        iv_back = _first_num(getattr(mi, "options_iv_back", None), allow_zero=False)
        skew_25d = _first_num(getattr(mi, "options_skew_25d_proxy", None))

        dvol = _first_num(getattr(fg, "dvol_current", None), allow_zero=False)
        rv20 = _first_num(getattr(ssrn, "realized_vol_20d_ann", None), allow_zero=False)
        gk_ann = _first_num(getattr(vc, "garman_klass_annualized_vol", None), allow_zero=False)
        if gk_ann is not None and abs(gk_ann) <= 5.0:
            gk_ann = gk_ann * 100.0
        bbw_pct = _first_num(getattr(getattr(ss, "macro", None), "bbw_percentile", None))
        if bbw_pct is not None and 0.0 <= bbw_pct <= 1.5:
            bbw_pct = bbw_pct * 100.0
        skew20 = _first_num(getattr(ssrn, "live_skewness_20d", None))
        vol_any = any(x is not None for x in (dvol, rv20, gk_ann, bbw_pct, skew20))

        up_mag = _first_num(getattr(slsp, "upper_magnet_price", None), getattr(getattr(mag, "upper_magnet", None), "price", None), getattr(getattr(ss, "magnet", None), "short_liq_magnet", None), allow_zero=False)
        dn_mag = _first_num(getattr(slsp, "lower_magnet_price", None), getattr(getattr(mag, "lower_magnet", None), "price", None), getattr(getattr(ss, "magnet", None), "long_liq_magnet", None), allow_zero=False)
        imm_r = _first_num(getattr(slsp, "immediate_ratio", None), getattr(mag, "immediate_ratio", None))
        tot_r = _first_num(getattr(slsp, "total_ladder_ratio", None), getattr(mag, "total_ladder_ratio", None))
        pull_r = _first_num(getattr(mag, "pull_ratio", None))
        lsce_st = getattr(mag, "lsce_status", None) or getattr(slsp, "lsce_status", None)

        w_1h_liq = getattr(liq_rep, "windows", {}).get("1h") if liq_rep and getattr(liq_rep, "windows", None) else None
        w_24h_liq = getattr(liq_rep, "windows", {}).get("24h") if liq_rep and getattr(liq_rep, "windows", None) else None
        liq_1h_s = f"${w_1h_liq.total_usd/1e6:.2f}M (L:{w_1h_liq.long_usd/1e6:.1f} S:{w_1h_liq.short_usd/1e6:.1f})" if w_1h_liq else None
        liq_24h_s = f"${w_24h_liq.total_usd/1e6:.2f}M (x{getattr(liq_rep, 'liquidation_multiple_24h', 0.0):.2f})" if w_24h_liq else None
        pf_s = getattr(getattr(liq_rep, "post_flush_price_structure", None), "status", None) if liq_rep and getattr(liq_rep, "is_available", False) else None

        panel_3 = [
            _row("BN Open Interest (BTC / USD)", f"{oi_btc:,.0f} BTC ({_fmt_usd_compact(oi_usd) or 'N/A'})" if oi_btc else None, "0,1,4,15,17"),
            _row("Cross-Exch Perp OI & Funding", f"{_fmt_num(agg_oi_b, ',.0f', False, ' BTC') or 'N/A'} ({_fmt_usd_compact(agg_oi_u) or 'N/A'}) · F:{_fmt_num(agg_fund, '+.4f', True, '%') or 'N/A'} [{agg_venues}]" if (agg_oi_b or agg_fund is not None) else None, "Macro,15"),
            _row("OI Δ% (15m/1h/4h/24h) & Quad", f"{_fmt_num(oi_15, '+.2f', True, '%') or 'N/A'}/{_fmt_num(oi_1h, '+.2f', True, '%') or 'N/A'}/{_fmt_num(oi_4h, '+.2f', True, '%') or 'N/A'}/{_fmt_num(oi_24h, '+.2f', True, '%') or 'N/A'} | {quad_val or 'N/A'}" if (oi_deltas_ok or quad_val) else None, "1,4,8,11,12,15,17"),
            _row("Funding 8H% / Ann% / P90", f"{_fmt_num(fund_8h, '+.4f', True, '%') or 'N/A'} ({_fmt_num(fund_ann, '+.1f', True, '%/yr') or 'N/A'}) · P90:{_fmt_num(fund_p90, '.1f', True, '%') or 'N/A'}" if (fund_8h is not None or fund_p90 is not None) else None, "0,4,9,11,15,16,19,20"),
            _row("Perp Basis ($ / Ann %)", basis_str, "1,4"),
            _row("5m Taker L/S & Top/Glb Acct", acct_str, "1,2,15,16"),
            _row("Options OI & Put/Call (Deribit)", f"P/C:{_fmt_num(pc_oi, '.3f', False) or 'N/A'} · TotOI:{_fmt_num(opt_oi, ',.0f', False, ' BTC') or 'N/A'}" if (pc_oi is not None or opt_oi is not None) else None, "Macro,19"),
            _row("Options IV Term & Skew (Deribit)", f"F:{_fmt_num(iv_front, '.1f', False, '%') or 'N/A'} · B:{_fmt_num(iv_back, '.1f', False, '%') or 'N/A'} · 25dSk:{_fmt_num(skew_25d, '+.1f', True, '%') or 'N/A'}" if (iv_front or iv_back or skew_25d is not None) else None, "Macro,6,19"),
            _row("Vol: DVOL, RV20, GK & BBW%", f"DVOL:{_fmt_num(dvol, '.1f') or 'N/A'} · RV20:{_fmt_num(rv20, '.1f', True, '%') or 'N/A'} · GK:{_fmt_num(gk_ann, '.1f', True, '%') or 'N/A'} · BBW:{_fmt_num(bbw_pct, '.0f', True, '%') or 'N/A'} · Sk20:{_fmt_num(skew20, '+.2f') or 'N/A'}" if vol_any else None, "0,4,6,16,19"),
            _row("Upper / Lower Liq Magnet", f"Up:{_fmt_price(up_mag) or 'N/A'} | Dn:{_fmt_price(dn_mag) or 'N/A'}" if (up_mag or dn_mag) else None, "0,2,13,17"),
            _row("Magnet Ratios & LSCE", f"Imm:{_fmt_num(imm_r, '.2f', True, 'x') or 'N/A'} · Ladder:{_fmt_num(tot_r, '.2f', True, 'x') or 'N/A'} · Pull:{_fmt_num(pull_r, '.2f', True, 'x') or 'N/A'} · LSCE:{lsce_st or 'N/A'}" if (imm_r is not None or pull_r is not None or lsce_st) else None, "13,17"),
            _row("Liquidations (1H / 24H) & Flush", f"1H:{liq_1h_s or 'N/A'} | 24H:{liq_24h_s or 'N/A'} · {pf_s or 'N/A'}" if (liq_1h_s or liq_24h_s) else None, "0,8,12,13", liq_status_tag if (liq_1h_s or liq_24h_s) else "UNAVAILABLE"),
        ]

        # Domain 4: On-Chain, ETF & Stablecoin Flows (panel_4_flow_quant slot)
        cm_mvrv = _first_num(getattr(mi, "onchain_mvrv_cur", None), allow_zero=False)
        cm_date = getattr(mi, "onchain_mvrv_date", None)
        proxy_mvrv = _first_num(getattr(ssrn, "live_mvrv_ratio", None), allow_zero=False)
        if cm_mvrv is not None:
            mvrv_str, mvrv_status = f"{cm_mvrv:.3f} [CoinMetrics {cm_date or 'live'}]", "OK"
        elif proxy_mvrv is not None:
            mvrv_str, mvrv_status = f"{proxy_mvrv:.2f} [PROXY: Spot/(0.62*200SMA)]", "PROXY"
        else:
            mvrv_str, mvrv_status = None, "UNAVAILABLE"

        cm_in = _first_num(getattr(mi, "onchain_exch_inflow_btc", None))
        cm_out = _first_num(getattr(mi, "onchain_exch_outflow_btc", None))
        cm_net_b = _first_num(getattr(mi, "onchain_exch_netflow_btc", None))
        cm_net_u = _first_num(getattr(mi, "onchain_exch_netflow_usd", None))
        cm_sply = _first_num(getattr(mi, "onchain_exch_supply_btc", None), allow_zero=False)
        netflow_ok = any(x is not None for x in (cm_net_b, cm_in, cm_out))
        netflow_str = (
            f"Net:{_fmt_num(cm_net_b, '+,.1f', True, ' BTC') or 'N/A'} ({_fmt_usd_compact(cm_net_u, signed=True) or 'N/A'}) | "
            f"In:{_fmt_num(cm_in, ',.0f') or 'N/A'} Out:{_fmt_num(cm_out, ',.0f') or 'N/A'}"
        ) if netflow_ok else None

        sc_usdt = _first_num(getattr(mi, "stablecoin_usdt_b", None), allow_zero=False)
        sc_usdc = _first_num(getattr(mi, "stablecoin_usdc_b", None), allow_zero=False)
        sc_tot = _first_num(getattr(mi, "stablecoin_total_b", None), allow_zero=False)
        sc_7d = _first_num(getattr(mi, "stablecoin_7d_delta_b", None))
        sc_30d = _first_num(getattr(mi, "stablecoin_30d_delta_b", None))

        etf_1d = _first_num(getattr(mi, "etf_daily_net_flow_usd", None))
        etf_3d = _first_num(getattr(mi, "etf_3d_cumulative_flow_usd", None))
        etf_status = "UNAVAILABLE"
        etf_str = None
        if mi is not None and (etf_1d is not None or etf_3d is not None):
            if getattr(mi, "etf_daily_net_flow_status", "OK") == "OK":
                etf_status = "OK"
                etf_str = f"1D:{_fmt_usd_compact(etf_1d, signed=True) or 'N/A'} | 3D:{_fmt_usd_compact(etf_3d, signed=True) or 'N/A'}"

        etf_p_vol = _first_num(getattr(mi, "etf_proxy_vol_1d_usd", None), allow_zero=False)
        etf_p_flow = _first_num(getattr(mi, "etf_proxy_flow_5d_usd", None))
        etf_p_str = (
            f"1DVol:{_fmt_usd_compact(etf_p_vol) or 'N/A'} · 5D:{_fmt_usd_compact(etf_p_flow, signed=True) or 'N/A'} [PROXY]"
            if etf_p_vol is not None else None
        )

        pl_fair = _first_num(getattr(macro_ev, "power_law_fair_usd", None), allow_zero=False)
        pl_disc = _first_num(getattr(macro_ev, "power_law_discount_pct", None))
        ath_dd = _first_num(getattr(macro_ev, "current_drawdown_pct", None))
        macd_str = None
        if ssrn is not None and getattr(ssrn, "daily_macd_status", None):
            macd_str = f"1D={ssrn.daily_macd_status} | 1H={ssrn.hourly_macd_status}"

        panel_4 = [
            _row("MVRV Ratio (On-Chain / Proxy)", mvrv_str, "Macro,16", mvrv_status),
            # Zero-Hallucination: never emit static 1.02 placeholder for SOPR/aSOPR.
            _row("On-Chain SOPR / aSOPR", None, "16", "UNAVAILABLE"),
            _row("Exchange Netflow 24H (CM)", netflow_str, "Macro,16"),
            _row("BTC Exchange Reserves (CM)", f"{cm_sply:,.0f} BTC ({cm_date or 'latest'})" if cm_sply is not None else None, "Macro,16"),
            _row("Stablecoins USDT+USDC Supply", f"${sc_tot:.2f}B (USDT:${_fmt_num(sc_usdt, '.2f') or 'N/A'}B · USDC:${_fmt_num(sc_usdc, '.2f') or 'N/A'}B)" if sc_tot is not None else None, "Macro"),
            _row("Stablecoin Net Issuance (7D/30D)", f"7D:{_fmt_num(sc_7d, '+.2f', True, 'B') or 'N/A'} · 30D:{_fmt_num(sc_30d, '+.2f', True, 'B') or 'N/A'}" if (sc_7d is not None or sc_30d is not None) else None, "Macro"),
            _row("US Spot ETF Flow (Farside 1D/3D)", etf_str, "2,13", etf_status),
            _row("US ETF Tape Proxy (IBIT+FBTC)", etf_p_str, "Macro,2,13", "PROXY" if etf_p_str else "UNAVAILABLE"),
            _row("Power-Law Fair & ATH DD%", f"{_fmt_price(pl_fair) or 'N/A'} ({_fmt_num(pl_disc, '+.1f', True, '%') or 'N/A'}) | DD:{_fmt_num(ath_dd, '+.1f', True, '%') or 'N/A'}" if (pl_fair or ath_dd is not None) else None, "3"),
            _row("MTF MACD (1D / 1H Status)", macd_str, "13,16,18"),
        ]

        # Domain 5: Macro, Credit & US Liquidity (panel_5_derivs_liq slot)
        sofr_r = _first_num(getattr(mi, "us_sofr_rate_pct", None), allow_zero=False)
        sofr_v = _first_num(getattr(mi, "us_sofr_vol_b", None), allow_zero=False)
        rrp_b = _first_num(getattr(mi, "us_rrp_balance_b", None))
        hyg_lqd = _first_num(getattr(mi, "credit_hyg_lqd_ratio", None), allow_zero=False)
        hyg_lqd_5d = _first_num(getattr(mi, "credit_hyg_lqd_5d_chg_pct", None))

        dxy_v = _first_num(getattr(mi, "dxy_index", None), allow_zero=False)
        spx_v = _first_num(getattr(mi, "sp500_price", None), allow_zero=False)
        ndx_v = _first_num(getattr(mi, "nasdaq_price", None), allow_zero=False)
        vix_v = _first_num(getattr(mi, "vix_index", None), allow_zero=False)
        y10_v = _first_num(getattr(mi, "us_10y_treasury_yield", None), allow_zero=False)
        tips_v = _first_num(getattr(mi, "us_10y_real_yield_tips", None))
        bei_v = _first_num(getattr(mi, "us_10y_breakeven_inflation", None), allow_zero=False)
        brent_v = _first_num(getattr(mi, "brent_crude_price", None), allow_zero=False)
        corr20 = _first_num(getattr(mi, "btc_spx_corr_20d", None))
        corr60 = _first_num(getattr(mi, "btc_spx_corr_60d", None))
        fng_v = _first_num(getattr(mi, "fear_and_greed_score", None))
        dom_v = _first_num(getattr(mi, "btc_dominance_pct", None), allow_zero=False)

        fng_cls = getattr(mi, "fear_and_greed_classification", "") or ""
        fng_part = f"F&G:{int(fng_v)} ({fng_cls})" if fng_v is not None else "F&G:N/A"
        fng_str = (
            f"{fng_part} | Dom:{_fmt_num(dom_v, '.2f', False, '%') or 'N/A'}"
            if (fng_v is not None or dom_v is not None)
            else None
        )

        panel_5 = [
            _row("US SOFR Rate & Vol (NY Fed)", f"{sofr_r:.2f}% (Vol:${_fmt_num(sofr_v, ',.0f') or 'N/A'}B)" if sofr_r is not None else None, "Macro"),
            _row("Fed ON RRP Balance (NY Fed)", f"${rrp_b:.2f}B" if rrp_b is not None else None, "Macro"),
            _row("Credit Spread HYG/LQD & 5D%", f"{hyg_lqd:.4f} ({_fmt_num(hyg_lqd_5d, '+.2f', True, '%') or 'N/A'} 5D)" if hyg_lqd is not None else None, "Macro,3"),
            _row("DXY / US 10Y (^TNX)", f"{_fmt_num(dxy_v, '.2f', False) or 'N/A'} ({getattr(mi, 'dxy_direction_5_10d', 'N/A')}) | 10Y:{_fmt_num(y10_v, '.2f', False, '%') or 'N/A'}" if (dxy_v or y10_v) else None, "3,13"),
            _row("TIPS Real (DFII10) / BEI", f"Real:{_fmt_num(tips_v, '+.2f', True, '%') or 'N/A'} | BEI:{_fmt_num(bei_v, '.2f', False, '%') or 'N/A'}" if (tips_v is not None or bei_v is not None) else None, "3,13"),
            _row("S&P 500 / Nasdaq (1D%)", f"SPX:{_fmt_num(spx_v, ',.0f', False) or 'N/A'} ({_fmt_num(getattr(mi, 'sp500_change_1d_pct', None), '+.2f', True, '%') or 'N/A'}) | NDX:{_fmt_num(ndx_v, ',.0f', False) or 'N/A'}" if (spx_v or ndx_v) else None, "3,13"),
            _row("VIX / Brent Crude (BZ=F)", f"VIX:{_fmt_num(vix_v, '.2f', False) or 'N/A'} | Brent:{_fmt_price(brent_v) or 'N/A'}" if (vix_v or brent_v) else None, "3,13"),
            _row("BTC-SPX Corr (20D / 60D)", f"20D:{_fmt_num(corr20, '+.2f') or 'N/A'} | 60D:{_fmt_num(corr60, '+.2f') or 'N/A'}" if (corr20 is not None or corr60 is not None) else None, "3"),
            _row("Fear & Greed / BTC Dom%", fng_str, "3,13"),
            _row("Manual Context Overrides", f"200D_Veto={getattr(proto, 'enforce_200d_hard_veto_on_tab1', 'N/A')} · Filter={getattr(proto, 'headline_filter_status', 'N/A')}" if proto else None, "2,13"),
        ]

        # Domain 6: Quant Features, Feed Health & Archive (panel_6_macro_onchain slot)
        levy_a_sp = _first_num(getattr(fg, "loop_a_g1_val", None))
        mm_sig = getattr(mm, "signature", None)
        mm_pf = _first_num(getattr(mm_sig, "area_price_flow", None))
        mm_rgh = _first_num(getattr(mm_sig, "roughness", None))
        mm_kal = getattr(mm, "kalman", None)
        mm_kvel = _first_num(getattr(mm_kal, "velocity", None))
        mm_hur = getattr(mm, "hurst", None)
        hurst_v = _first_num(getattr(mm_hur, "hurst", None), getattr(vc, "hurst_exponent", None))
        mm_fd = getattr(mm, "frac_diff", None)
        frac_d = _first_num(getattr(mm_fd, "optimal_d", None))
        mm_hil = getattr(mm, "hilbert", None)
        hil_cyc = _first_num(getattr(mm_hil, "dominant_cycle", None), allow_zero=False)
        td1 = getattr(exh, "td_1h", None)
        td4 = getattr(exh, "td_4h", None)
        td1_cnt = getattr(td1, "setup_count", None)
        td4_cnt = getattr(td4, "setup_count", None)
        tt = getattr(exh, "tell_tale", None)
        tt_15 = _first_num(getattr(getattr(tt, "bar_15m", None), "relvol", None))
        tt_5 = _first_num(getattr(getattr(tt, "bar_5m", None), "relvol", None))
        vcr_v = _first_num(getattr(vc, "vcr_72h", None))
        tsfm_v = _first_num(
            getattr(vc.horizons[-1], "tsfm_dispersion_pct", None)
            if vc and getattr(vc, "horizons", None)
            else None
        )
        fvgs = getattr(trap, "active_fvgs", None)
        fvg_cnt = len(fvgs) if isinstance(fvgs, list) else None

        ws_stale = ("STALE" in (sp_ws_st, pp_ws_st, cb_ws_st)) or (not store.warmup_complete)
        spot_kl_ok = bool(store.spot_klines_1w and store.spot_klines_1d and store.spot_klines_4h and store.spot_klines_1h and store.spot_klines_15m)
        rec_liq_ok = bool(rec_val or liq_status_val)
        rec_liq_status = "STALE" if liq_status_tag == "STALE" else ("OK" if rec_liq_ok else "UNAVAILABLE")

        panel_6 = [
            _row("Rough Path Lévy (A_SP / MM)", f"4H A_SP:{_fmt_num(levy_a_sp, '+.4f') or 'N/A'} | MM PriceFlow:{_fmt_num(mm_pf, '+.4f') or 'N/A'} · Rough:{_fmt_num(mm_rgh, '.3f') or 'N/A'}" if any(v is not None for v in (levy_a_sp, mm_pf, mm_rgh)) else None, "5,19"),
            _row("Hurst / Kalman Vel / FracDiff", f"H:{_fmt_num(hurst_v, '.3f') or 'N/A'} · KVel:{_fmt_num(mm_kvel, '+.2f') or 'N/A'} · d:{_fmt_num(frac_d, '.2f') or 'N/A'}" if any(v is not None for v in (hurst_v, mm_kvel, frac_d)) else None, "5,6"),
            _row("Hilbert Cycle / TD9 / TellTale", f"Cyc:{_fmt_num(hil_cyc, '.1f', False, 'b') or 'N/A'} · TD(1H/4H):{td1_cnt if td1_cnt is not None else 'N/A'}/{td4_cnt if td4_cnt is not None else 'N/A'} · RV(15m/5m):{_fmt_num(tt_15, '.2f') or 'N/A'}/{_fmt_num(tt_5, '.2f') or 'N/A'}" if any(v is not None for v in (hil_cyc, td1_cnt, td4_cnt, tt_15, tt_5)) else None, "5,9,13"),
            _row("VCR 72H & TSFM Disp%", f"VCR:{_fmt_num(vcr_v, '.2f') or 'N/A'} | Disp:{_fmt_num(tsfm_v, '.2f', True, '%') or 'N/A'}" if (vcr_v is not None or tsfm_v is not None) else None, "6"),
            _row("Open FVGs & Sweep FSM", f"FVGs:{fvg_cnt if fvg_cnt is not None else 'N/A'} | FSM:{getattr(sig, 'fsm_state', 'N/A')} ({getattr(sig, 'fsm_bars_elapsed', 0)}/{getattr(sig, 'fsm_max_bars', 0)})" if (fvg_cnt is not None or sig) else None, "1,8"),
            _row("WebSocket Feeds & Warmup", f"Spot:{sp_ws_s} | Perp:{pp_ws_s} | CB:{cb_ws_s} | Warm:{'YES' if store.warmup_complete else 'NO'}", "Live Feeds", "STALE" if ws_stale else "OK"),
            _row("Spot Klines (1W/1D/4H/1H/15m)", f"1W:{len(store.spot_klines_1w)} 1D:{_bar_meta(store.spot_klines_1d)} | 4H:{len(store.spot_klines_4h)} 1H:{len(store.spot_klines_1h)} 15m:{len(store.spot_klines_15m)}" if spot_kl_ok else None, "All Tabs"),
            _row("Perp Klines / Est. Excluded", f"1D:{len(store.perp_klines_1d)} · 1H:{len(store.perp_klines_1h)} · 15m:{len(store.perp_klines_15m)} (Excl={excl_total})" if store.perp_klines_1h else None, "1,4,11,15,19"),
            _row("Closed 4H Anchor (Tab 19/20)", closed_4h_utc, "18,19,20"),
            _row("B1/B2 Rec & Companion Liq", f"Rec:{rec_val or 'N/A'} | Liq:{liq_status_val or 'N/A'}" if rec_liq_ok else None, "8,13,17", rec_liq_status),
        ]

        pre_rows = panel_1 + panel_2 + panel_3 + panel_4 + panel_5 + panel_6
        ev = DataHubEvaluation(
            timestamp_utc=now_dt.strftime("%Y-%m-%d %H:%M:%S UTC"),
            spot_price=spot_px,
            total_metrics=len(pre_rows),
            ok_count=sum(1 for r in pre_rows if r.status == "OK"),
            unavailable_count=sum(1 for r in pre_rows if r.status == "UNAVAILABLE"),
            stale_count=sum(1 for r in pre_rows if r.status == "STALE"),
            proxy_or_static_count=sum(1 for r in pre_rows if r.status in ("PROXY", "STATIC")),
            panel_1_feeds=panel_1,
            panel_2_trend_vol=panel_2,
            panel_3_structure_magnets=panel_3,
            panel_4_flow_quant=panel_4,
            panel_5_derivs_liq=panel_5,
            panel_6_macro_onchain=panel_6,
        )

        arch_cnt, arch_last = record_and_query_telemetry_archive(
            ev,
            closed_4h_utc,
            db_path=self._db_path,
            write_enabled=self._write_archive,
        )
        arch_row = _row(
            "Telemetry History Archive (SQLite)",
            f"{arch_cnt} bars logged (Last: {arch_last})" if arch_cnt > 0 else "0 snapshots (no closed 4H bar)",
            "DB Archive",
            "OK" if arch_cnt > 0 else "UNAVAILABLE",
        )
        panel_6.append(arch_row)

        all_rows = panel_1 + panel_2 + panel_3 + panel_4 + panel_5 + panel_6
        ev.total_metrics = len(all_rows)
        ev.ok_count = sum(1 for r in all_rows if r.status == "OK")
        ev.unavailable_count = sum(1 for r in all_rows if r.status == "UNAVAILABLE")
        ev.stale_count = sum(1 for r in all_rows if r.status == "STALE")
        ev.proxy_or_static_count = sum(1 for r in all_rows if r.status in ("PROXY", "STATIC"))
        ev.archive_snapshots_count = arch_cnt
        ev.archive_last_bar_utc = arch_last

        store.data_hub_evaluation = ev
        return ev
