"""G1 Historical Validation, Benchmark & Ablation Engine for DIBSE.

Performs strictly point-in-time historical validation across multi-year Binance
Spot 4H, USD-M Perp 4H, and 8H Funding archives (warmup from 2019-06/09, common
evaluation horizon 2020-01-01 UTC through latest closed bar).

Key guarantees:
  - Strictly closed 4H bar alignment (open_time + 4h <= now_utc_ms)
  - Strict Spot/Perp open_time intersection (spot_ts[k] == perp_ts[k])
  - Strictly causal funding history (fundingTime <= bar_close_ms)
  - Zero optimization/tuning of frozen live DIBSE protocol thresholds
  - Honest PSR / Deflated Sharpe Ratio (Bailey & Lopez de Prado 2014) reporting
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import sys
import time
from typing import Any, Dict, List, Optional, Sequence, Tuple
import urllib.error
import urllib.request

import numpy as np
from scipy.stats import kurtosis, norm, skew

_ROOT_DIR = Path(__file__).resolve().parent.parent
if str(_ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(_ROOT_DIR))

FOUR_HOURS_MS = 4 * 3600 * 1000
DAY_MS = 24 * 3600 * 1000
EVAL_START_2020_MS = 1577836800000  # 2020-01-01 00:00:00 UTC
SPOT_WARMUP_START_MS = 1559347200000  # 2019-06-01 00:00:00 UTC (>200d before 2020-01-01)
PERP_WARMUP_START_MS = 1567900800000  # 2019-09-08 00:00:00 UTC (Binance USD-M launch)

DEFAULT_CACHE_PATH = _ROOT_DIR / "data" / "cache" / "binance_4h_2020_present.npz"
DEFAULT_REPORT_PATH = _ROOT_DIR / "docs" / "DIBSE_G1_VALIDATION_REPORT.md"

EULER_GAMMA = 0.5772156649015329
INITIAL_SANDBOX_USD = 20_000.0  # 20% active sandbox ($10k USDT + $10k BTC)


@dataclass
class ArchiveData:
    """Aligned closed-bar market history and causal funding archive."""

    # Aligned Spot+Perp arrays (intersection of Spot and Perp closed 4H bars)
    open_times: np.ndarray  # int64 ms
    opens: np.ndarray
    highs: np.ndarray
    lows: np.ndarray
    closes: np.ndarray
    s_vols: np.ndarray
    s_buys: np.ndarray
    p_vols: np.ndarray
    p_buys: np.ndarray

    # Full Spot 4H arrays from 2019-06-01 onward for 200d SMA warmup before 2020-01-01
    spot_full_open_times: np.ndarray
    spot_full_closes: np.ndarray

    # Funding history (sorted ascending)
    fund_times: np.ndarray  # int64 ms
    fund_rates: np.ndarray

    # Metadata & data integrity summary
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CausalSignalTable:
    """Point-in-time boolean gate matrices and volume profile anchors."""

    valid_mask: np.ndarray
    a_g1: np.ndarray
    a_g2: np.ndarray
    a_g3: np.ndarray
    a_g4: np.ndarray
    b_g1: np.ndarray
    b_g2: np.ndarray
    b_g3: np.ndarray
    b_g4: np.ndarray
    poc_30: np.ndarray
    val_30: np.ndarray
    vah_30: np.ndarray


@dataclass
class StrategyResult:
    """Simulation output + institutional risk metrics for a single strategy/benchmark."""

    name: str
    category: str  # "DIBSE" | "ABLATION" | "BENCHMARK" | "STRESS"
    cost_bps: float
    exit_mode: str
    daily_days_ms: np.ndarray
    daily_equity: np.ndarray
    metrics: Dict[str, float]
    diagnostics: Dict[str, Any] = field(default_factory=dict)


def _http_get_json(url: str, timeout_sec: float = 20.0, max_retries: int = 4) -> Any:
    """Fetch JSON over HTTPS with polite backoff on transient/429 failures."""
    headers = {"User-Agent": "BTC-Swing-Engine-G1-Validator/1.0"}
    last_err: Optional[Exception] = None
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
                if resp.status == 200:
                    return json.loads(resp.read().decode("utf-8"))
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            last_err = exc
            time.sleep(0.4 * (2 ** attempt))
    raise RuntimeError(f"Failed fetching {url}: {last_err}")


def fetch_paginated_klines(
    base_url: str,
    symbol: str,
    interval: str,
    start_ms: int,
    end_ms: int,
    limit: int = 1000,
    pause_sec: float = 0.06,
) -> List[List[Any]]:
    """Paginate Binance Spot or Perp klines strictly forward in [start_ms, end_ms]."""
    rows: List[List[Any]] = []
    cursor = int(start_ms)
    while cursor <= end_ms:
        url = (
            f"{base_url}?symbol={symbol}&interval={interval}"
            f"&startTime={cursor}&endTime={end_ms}&limit={limit}"
        )
        batch = _http_get_json(url)
        if not batch:
            break
        rows.extend(batch)
        last_open = int(batch[-1][0])
        if last_open < cursor:
            break
        cursor = last_open + FOUR_HOURS_MS
        if len(batch) < limit:
            break
        time.sleep(pause_sec)
    return rows


def fetch_paginated_funding(
    start_ms: int,
    end_ms: int,
    symbol: str = "BTCUSDT",
    limit: int = 1000,
    pause_sec: float = 0.06,
) -> List[Dict[str, Any]]:
    """Paginate Binance USD-M historical funding rates in [start_ms, end_ms]."""
    base_url = "https://fapi.binance.com/fapi/v1/fundingRate"
    rows: List[Dict[str, Any]] = []
    cursor = int(start_ms)
    while cursor <= end_ms:
        url = (
            f"{base_url}?symbol={symbol}&startTime={cursor}"
            f"&endTime={end_ms}&limit={limit}"
        )
        batch = _http_get_json(url)
        if not batch:
            break
        rows.extend(batch)
        last_ts = int(batch[-1]["fundingTime"])
        if last_ts < cursor:
            break
        cursor = last_ts + 1
        if len(batch) < limit:
            break
        time.sleep(pause_sec)
    return rows


def align_closed_archives(
    spot_rows: Sequence[Sequence[Any]],
    perp_rows: Sequence[Sequence[Any]],
    funding_rows: Sequence[Dict[str, Any]],
    now_ms: Optional[int] = None,
) -> ArchiveData:
    """Build strictly closed, timestamp-aligned arrays from raw Binance payloads."""
    if now_ms is None:
        now_ms = int(time.time() * 1000)

    def _is_closed(open_ms: int) -> bool:
        return (open_ms + FOUR_HOURS_MS) <= now_ms

    spot_map: Dict[int, Sequence[Any]] = {}
    for r in spot_rows:
        ts = int(r[0])
        if _is_closed(ts):
            spot_map[ts] = r

    perp_map: Dict[int, Sequence[Any]] = {}
    for r in perp_rows:
        ts = int(r[0])
        if _is_closed(ts):
            perp_map[ts] = r

    spot_sorted_ts = sorted(spot_map.keys())
    common_ts = sorted(set(spot_map.keys()) & set(perp_map.keys()))
    if not common_ts:
        raise RuntimeError("Zero overlapping closed 4H timestamps between Spot and Perp.")

    open_times = np.array(common_ts, dtype=np.int64)
    opens = np.array([float(spot_map[t][1]) for t in common_ts], dtype=np.float64)
    highs = np.array([float(spot_map[t][2]) for t in common_ts], dtype=np.float64)
    lows = np.array([float(spot_map[t][3]) for t in common_ts], dtype=np.float64)
    closes = np.array([float(spot_map[t][4]) for t in common_ts], dtype=np.float64)
    s_vols = np.array([float(spot_map[t][5]) for t in common_ts], dtype=np.float64)
    s_buys = np.array([float(spot_map[t][9]) for t in common_ts], dtype=np.float64)
    p_vols = np.array([float(perp_map[t][5]) for t in common_ts], dtype=np.float64)
    p_buys = np.array([float(perp_map[t][9]) for t in common_ts], dtype=np.float64)

    spot_full_open_times = np.array(spot_sorted_ts, dtype=np.int64)
    spot_full_closes = np.array([float(spot_map[t][4]) for t in spot_sorted_ts], dtype=np.float64)

    # Deduplicate and sort funding prints ascending
    fund_map: Dict[int, float] = {}
    for f in funding_rows:
        ts = int(f["fundingTime"])
        if ts <= now_ms:
            fund_map[ts] = float(f["fundingRate"])
    sorted_ft = sorted(fund_map.keys())
    fund_times = np.array(sorted_ft, dtype=np.int64)
    fund_rates = np.array([fund_map[t] for t in sorted_ft], dtype=np.float64)

    # Data integrity diagnostics (maintenance gaps in 4H lattice)
    diffs = np.diff(open_times)
    gap_indices = np.where(diffs != FOUR_HOURS_MS)[0]
    gap_details = [
        {
            "from_utc": datetime.fromtimestamp(open_times[i] / 1000.0, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            "to_utc": datetime.fromtimestamp(open_times[i + 1] / 1000.0, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            "missing_bars": int(diffs[i] // FOUR_HOURS_MS) - 1,
        }
        for i in gap_indices
    ]

    meta = {
        "aligned_bars": int(len(open_times)),
        "spot_full_bars": int(len(spot_full_open_times)),
        "funding_prints": int(len(fund_times)),
        "aligned_start_utc": datetime.fromtimestamp(open_times[0] / 1000.0, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "aligned_end_close_utc": datetime.fromtimestamp((open_times[-1] + FOUR_HOURS_MS) / 1000.0, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "spot_start_utc": datetime.fromtimestamp(spot_full_open_times[0] / 1000.0, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "gap_events": len(gap_details),
        "total_missing_4h_bars": sum(g["missing_bars"] for g in gap_details),
        "gap_details": gap_details[:15],
        "spot_only_dropped": len(set(spot_map.keys()) - set(perp_map.keys())),
        "perp_only_dropped": len(set(perp_map.keys()) - set(spot_map.keys())),
    }

    return ArchiveData(
        open_times=open_times,
        opens=opens,
        highs=highs,
        lows=lows,
        closes=closes,
        s_vols=s_vols,
        s_buys=s_buys,
        p_vols=p_vols,
        p_buys=p_buys,
        spot_full_open_times=spot_full_open_times,
        spot_full_closes=spot_full_closes,
        fund_times=fund_times,
        fund_rates=fund_rates,
        meta=meta,
    )


def save_archive_npz(archive: ArchiveData, cache_path: Path = DEFAULT_CACHE_PATH) -> None:
    """Persist aligned archive arrays + JSON metadata atomically to .npz."""
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = cache_path.with_suffix(".tmp.npz")
    np.savez_compressed(
        tmp_path,
        open_times=archive.open_times,
        opens=archive.opens,
        highs=archive.highs,
        lows=archive.lows,
        closes=archive.closes,
        s_vols=archive.s_vols,
        s_buys=archive.s_buys,
        p_vols=archive.p_vols,
        p_buys=archive.p_buys,
        spot_full_open_times=archive.spot_full_open_times,
        spot_full_closes=archive.spot_full_closes,
        fund_times=archive.fund_times,
        fund_rates=archive.fund_rates,
        meta_json=np.array([json.dumps(archive.meta)], dtype=object),
    )
    tmp_path.replace(cache_path)


def load_archive_npz(cache_path: Path = DEFAULT_CACHE_PATH) -> ArchiveData:
    """Load cached ArchiveData from .npz."""
    with np.load(cache_path, allow_pickle=True) as z:
        meta = json.loads(str(z["meta_json"][0]))
        return ArchiveData(
            open_times=z["open_times"],
            opens=z["opens"],
            highs=z["highs"],
            lows=z["lows"],
            closes=z["closes"],
            s_vols=z["s_vols"],
            s_buys=z["s_buys"],
            p_vols=z["p_vols"],
            p_buys=z["p_buys"],
            spot_full_open_times=z["spot_full_open_times"],
            spot_full_closes=z["spot_full_closes"],
            fund_times=z["fund_times"],
            fund_rates=z["fund_rates"],
            meta=meta,
        )


def load_or_fetch_archive(
    cache_path: Path = DEFAULT_CACHE_PATH,
    force_refresh: bool = False,
    max_stale_hours: float = 8.0,
) -> ArchiveData:
    """Load local Binance 4H archive cache or fetch live from primary endpoints."""
    now_ms = int(time.time() * 1000)
    if cache_path.exists() and not force_refresh:
        arch = load_archive_npz(cache_path)
        if len(arch.open_times) > 0:
            last_close_ms = int(arch.open_times[-1]) + FOUR_HOURS_MS
            stale_hours = (now_ms - last_close_ms) / 3_600_000.0
            if stale_hours <= max_stale_hours:
                return arch

    end_ms = now_ms
    spot_rows = fetch_paginated_klines(
        "https://api.binance.com/api/v3/klines",
        "BTCUSDT",
        "4h",
        SPOT_WARMUP_START_MS,
        end_ms,
        limit=1000,
    )
    perp_rows = fetch_paginated_klines(
        "https://fapi.binance.com/fapi/v1/klines",
        "BTCUSDT",
        "4h",
        PERP_WARMUP_START_MS,
        end_ms,
        limit=1500,
    )
    funding_rows = fetch_paginated_funding(
        PERP_WARMUP_START_MS,
        end_ms,
        symbol="BTCUSDT",
        limit=1000,
    )
    arch = align_closed_archives(spot_rows, perp_rows, funding_rows, now_ms=now_ms)
    save_archive_npz(arch, cache_path)
    return arch


def extract_causal_signals(archive: ArchiveData) -> CausalSignalTable:
    """Compute bit-exact causal Gate 1-4 signals matching FourGateEngine."""
    closes = archive.closes
    highs = archive.highs
    lows = archive.lows
    s_vols = archive.s_vols
    s_buys = archive.s_buys
    p_vols = archive.p_vols
    p_buys = archive.p_buys
    open_times = archive.open_times
    fund_times = archive.fund_times
    fund_rates = archive.fund_rates

    N = len(closes)
    valid_mask = np.zeros(N, dtype=bool)
    a_g1 = np.zeros(N, dtype=bool)
    a_g2 = np.zeros(N, dtype=bool)
    a_g3 = np.zeros(N, dtype=bool)
    a_g4 = np.zeros(N, dtype=bool)
    b_g1 = np.zeros(N, dtype=bool)
    b_g2 = np.zeros(N, dtype=bool)
    b_g3 = np.zeros(N, dtype=bool)
    b_g4 = np.zeros(N, dtype=bool)
    poc_arr = np.zeros(N, dtype=np.float64)
    val_arr = np.zeros(N, dtype=np.float64)
    vah_arr = np.zeros(N, dtype=np.float64)

    if N < 186:
        return CausalSignalTable(
            valid_mask, a_g1, a_g2, a_g3, a_g4, b_g1, b_g2, b_g3, b_g4, poc_arr, val_arr, vah_arr
        )

    dS = (2.0 * s_buys) - s_vols
    dF = (2.0 * p_buys) - p_vols

    # O(1) prefix sums for 24H (6-bar) Spot and Perp CVD
    cs_ds = np.concatenate(([0.0], np.cumsum(dS)))
    cs_df = np.concatenate(([0.0], np.cumsum(dF)))
    dS_24h_all = np.zeros(N, dtype=np.float64)
    dF_24h_all = np.zeros(N, dtype=np.float64)
    dS_24h_all[5:] = cs_ds[6:] - cs_ds[:-6]
    dF_24h_all[5:] = cs_df[6:] - cs_df[:-6]

    tp_all = (highs + lows + closes) / 3.0
    C_S = np.zeros(7, dtype=np.float64)
    L_P = np.zeros(7, dtype=np.float64)

    # Pre-compute causal funding slice end indices via searchsorted
    bar_close_ms_all = open_times + FOUR_HOURS_MS - 1
    fund_end_indices = np.searchsorted(fund_times, bar_close_ms_all, side="right")

    for k in range(185, N):
        end_f = int(fund_end_indices[k])
        if end_f == 0:
            continue

        valid_mask[k] = True

        # --- GATE 1: Rough Path Signature Engine (Levy Signed Area A_SP) ---
        C_S[1:] = np.cumsum(dS[k - 5 : k + 1])
        L_P[1:] = np.log(closes[k - 5 : k + 1] / closes[k - 6])
        std_cs = float(np.std(C_S))
        std_lp = float(np.std(L_P))
        X = C_S / (std_cs if std_cs > 1e-9 else 1.0)
        Y = L_P / (std_lp if std_lp > 1e-9 else 1.0)
        dx = X[1:] - X[:-1]
        dy = Y[1:] - Y[:-1]
        A_SP = 0.5 * float(np.sum(X[:-1] * dy - Y[:-1] * dx))

        a_g1[k] = A_SP > 0.0
        b_g1[k] = A_SP < 0.0

        # --- GATE 2: Spot vs Perp CVD Z-Score Divergence (D_flow) ---
        ds_win = dS_24h_all[k - 179 : k + 1]
        df_win = dF_24h_all[k - 179 : k + 1]
        std_ds = float(np.std(ds_win))
        std_df = float(np.std(df_win))
        last_ds = float(ds_win[-1])
        last_df = float(df_win[-1])
        z_S = (last_ds - float(np.mean(ds_win))) / (std_ds if std_ds > 1e-9 else 1.0)
        z_F = (last_df - float(np.mean(df_win))) / (std_df if std_df > 1e-9 else 1.0)
        D_flow = z_S - z_F

        a_g2[k] = (D_flow >= 1.0) and (last_ds > 0.0)
        b_g2[k] = (D_flow <= -1.0) and (last_ds < 0.0)

        # --- GATE 3: 30-Day Volume Profile + 12H Sweep/Rejection Memory ---
        w_start = k - 179
        w_h = highs[w_start : k + 1]
        w_l = lows[w_start : k + 1]
        w_v = s_vols[w_start : k + 1]
        tp_arr = tp_all[w_start : k + 1]

        p_min = float(np.min(w_l))
        p_max = float(np.max(w_h))
        bins = np.linspace(p_min, p_max, 51)
        b_idx = np.clip(((tp_arr - p_min) / (p_max - p_min + 1e-9) * 50.0).astype(np.int64), 0, 49)
        vol_bins = np.bincount(b_idx, weights=w_v, minlength=50)

        poc_idx = int(np.argmax(vol_bins))
        poc_30 = float((bins[poc_idx] + bins[poc_idx + 1]) / 2.0)

        cum_vol = np.cumsum(vol_bins)
        tot_vol = float(cum_vol[-1])
        val_idx = int(np.searchsorted(cum_vol, tot_vol * 0.15))
        val_30 = float((bins[val_idx] + bins[min(49, val_idx + 1)]) / 2.0)
        vah_idx = int(np.searchsorted(cum_vol, tot_vol * 0.85))
        vah_30 = float((bins[vah_idx] + bins[min(49, vah_idx + 1)]) / 2.0)

        poc_arr[k] = poc_30
        val_arr[k] = val_30
        vah_arr[k] = vah_30

        # Anchored 20D range strictly prior to latest 3 bars
        anchor_start = max(0, k - 122)
        anchor_end = k - 2
        l_20 = float(np.min(lows[anchor_start:anchor_end]))
        h_20 = float(np.max(highs[anchor_start:anchor_end]))
        window_low = float(np.min(lows[k - 2 : k + 1]))
        window_high = float(np.max(highs[k - 2 : k + 1]))

        ck = float(closes[k])
        ck_prev = float(closes[k - 1])
        lk = float(lows[k])
        hk = float(highs[k])
        low_2bar = float(min(lows[k - 1], lk))
        high_2bar = float(max(highs[k - 1], hk))

        # Loop A Gate 3
        sweep_L20 = (window_low < l_20) and (ck > l_20) and (lk >= window_low)
        sweep_VAL = (window_low < val_30) and (ck > val_30) and (lk >= window_low)
        state_a_a = sweep_L20 or sweep_VAL
        state_b_a = (ck > poc_30) and (abs(low_2bar - poc_30) / poc_30 <= 0.005) and (ck_prev > poc_30)
        a_g3[k] = state_a_a or state_b_a

        # Loop B Gate 3
        sweep_H20 = (window_high > h_20) and (ck < h_20) and (hk <= window_high)
        sweep_VAH = (window_high > vah_30) and (ck < vah_30) and (hk <= window_high)
        state_a_b = sweep_H20 or sweep_VAH
        state_b_b = (ck < vah_30) and (abs(high_2bar - vah_30) / vah_30 <= 0.005) and (ck_prev < vah_30)
        b_g3[k] = state_a_b or state_b_b

        # --- GATE 4: 90D Funding Memory ---
        f_start = max(0, end_f - 270)
        win_rates = fund_rates[f_start:end_f]
        n_f = len(win_rates)
        curr_f = float(win_rates[-1])
        prev_f = float(win_rates[-2]) if n_f >= 2 else curr_f
        p90_curr = (int(np.sum(win_rates < curr_f)) / n_f) * 100.0
        p90_prev = (int(np.sum(win_rates < prev_f)) / n_f) * 100.0

        f_rec_a = min(prev_f, curr_f)
        p90_rec_a = min(p90_prev, p90_curr)
        is_sweep_a = state_a_a or (not state_b_a and ck < val_30)
        if is_sweep_a:
            a_g4[k] = ((f_rec_a <= 0.0) or (p90_rec_a < 25.0)) and (p90_curr <= 50.0)
        else:
            a_g4[k] = p90_curr <= 75.0

        f_rec_b = max(prev_f, curr_f)
        p90_rec_b = max(p90_prev, p90_curr)
        is_res_b = state_a_b or (not state_b_b and ck > vah_30)
        if is_res_b:
            b_g4[k] = ((f_rec_b > 0.00015) or (p90_rec_b >= 75.0)) and (curr_f > 0.00010)
        else:
            b_g4[k] = (p90_curr >= 75.0) and (curr_f > 0.00010)

    return CausalSignalTable(
        valid_mask=valid_mask,
        a_g1=a_g1,
        a_g2=a_g2,
        a_g3=a_g3,
        a_g4=a_g4,
        b_g1=b_g1,
        b_g2=b_g2,
        b_g3=b_g3,
        b_g4=b_g4,
        poc_30=poc_arr,
        val_30=val_arr,
        vah_30=vah_arr,
    )


def get_triggers_for_ablation(
    sig: CausalSignalTable,
    ablation: str,
) -> Tuple[np.ndarray, np.ndarray]:
    """Return (loop_a_triggers, loop_b_triggers) boolean masks for an ablation variant."""
    mapping = {
        "FULL_4GATE": (
            sig.valid_mask & sig.a_g1 & sig.a_g2 & sig.a_g3 & sig.a_g4,
            sig.valid_mask & sig.b_g1 & sig.b_g2 & sig.b_g3 & sig.b_g4,
        ),
        "G3_ONLY": (
            sig.valid_mask & sig.a_g3,
            sig.valid_mask & sig.b_g3,
        ),
        "G3_G1": (
            sig.valid_mask & sig.a_g3 & sig.a_g1,
            sig.valid_mask & sig.b_g3 & sig.b_g1,
        ),
        "G3_G2": (
            sig.valid_mask & sig.a_g3 & sig.a_g2,
            sig.valid_mask & sig.b_g3 & sig.b_g2,
        ),
        "G3_G4": (
            sig.valid_mask & sig.a_g3 & sig.a_g4,
            sig.valid_mask & sig.b_g3 & sig.b_g4,
        ),
        "LOOP_A_ONLY": (
            sig.valid_mask & sig.a_g1 & sig.a_g2 & sig.a_g3 & sig.a_g4,
            np.zeros_like(sig.valid_mask, dtype=bool),
        ),
        "LOOP_B_ONLY": (
            np.zeros_like(sig.valid_mask, dtype=bool),
            sig.valid_mask & sig.b_g1 & sig.b_g2 & sig.b_g3 & sig.b_g4,
        ),
    }
    if ablation not in mapping:
        raise ValueError(f"Unknown ablation preset: {ablation}")
    return mapping[ablation]


def resample_daily_utc(
    open_times: np.ndarray,
    equity_4h: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray]:
    """Resample 4H close mark-to-market equity to one observation per UTC day close.

    Bar closing at (open_time + 4h) belongs to the UTC day containing (close_ms - 1),
    Wait: a bar [20:00 Day D, 00:00 Day D+1) closes at 00:00 Day D+1, so (close_ms - 1)
    places it as the last 4H bar of Day D. We record its ending equity as Day D's close.
    """
    close_ms = open_times + FOUR_HOURS_MS
    day_buckets = ((close_ms - 1) // DAY_MS) * DAY_MS
    # Pick last bar inside each UTC day bucket (vectorized run-end detection)
    change_idx = np.where(day_buckets[:-1] != day_buckets[1:])[0]
    pick_idx = np.concatenate((change_idx, [len(day_buckets) - 1]))
    return day_buckets[pick_idx] + DAY_MS, equity_4h[pick_idx]


def compute_performance_metrics(
    daily_days_ms: np.ndarray,
    daily_equity: np.ndarray,
    annual_days: float = 365.0,
) -> Dict[str, float]:
    """Compute CAGR, Sharpe, Sortino, MaxDD, Calmar, t-stat, skewness, kurtosis."""
    if len(daily_equity) < 3:
        return {
            "total_return_pct": 0.0,
            "cagr_pct": 0.0,
            "ann_vol_pct": 0.0,
            "max_dd_pct": 0.0,
            "calmar": 0.0,
            "sharpe": 0.0,
            "sortino": 0.0,
            "t_stat": 0.0,
            "daily_sharpe": 0.0,
            "skew": 0.0,
            "kurtosis_pearson": 3.0,
            "n_days": float(len(daily_equity)),
        }

    eq = np.asarray(daily_equity, dtype=np.float64)
    rets = eq[1:] / eq[:-1] - 1.0
    n_rets = len(rets)
    days_elapsed = max(1.0, float(daily_days_ms[-1] - daily_days_ms[0]) / float(DAY_MS))

    total_ret = (eq[-1] / eq[0]) - 1.0
    cagr = ((eq[-1] / eq[0]) ** (annual_days / days_elapsed) - 1.0) if eq[-1] > 0 else -1.0

    mu_d = float(np.mean(rets))
    sd_d = float(np.std(rets, ddof=1))
    ann_vol = sd_d * math.sqrt(annual_days)
    daily_sharpe = (mu_d / sd_d) if sd_d > 1e-12 else 0.0
    sharpe = daily_sharpe * math.sqrt(annual_days)

    downside = np.minimum(rets, 0.0)
    down_dev = float(np.sqrt(np.mean(downside ** 2)))
    sortino = (mu_d / down_dev) * math.sqrt(annual_days) if down_dev > 1e-12 else 0.0

    peaks = np.maximum.accumulate(eq)
    dd = (eq / peaks) - 1.0
    max_dd = float(np.min(dd))
    calmar = (cagr / abs(max_dd)) if abs(max_dd) > 1e-12 else 0.0
    t_stat = (mu_d / (sd_d / math.sqrt(n_rets))) if sd_d > 1e-12 else 0.0

    sk = float(skew(rets, bias=False)) if sd_d > 1e-12 and n_rets > 3 else 0.0
    ku = float(kurtosis(rets, fisher=False, bias=False)) if sd_d > 1e-12 and n_rets > 4 else 3.0

    return {
        "total_return_pct": total_ret * 100.0,
        "cagr_pct": cagr * 100.0,
        "ann_vol_pct": ann_vol * 100.0,
        "max_dd_pct": max_dd * 100.0,
        "calmar": calmar,
        "sharpe": sharpe,
        "sortino": sortino,
        "t_stat": t_stat,
        "daily_sharpe": daily_sharpe,
        "skew": sk,
        "kurtosis_pearson": ku,
        "n_days": float(n_rets),
    }


def compute_psr_dsr(
    daily_returns: np.ndarray,
    all_annual_sharpes: Sequence[float],
    annual_days: float = 365.0,
) -> Tuple[float, float, float]:
    """Compute Probabilistic Sharpe Ratio PSR(0) and Deflated Sharpe Ratio DSR.

    Follows Bailey & Lopez de Prado (2012, 2014). Returns (psr, dsr, sr0_ann).
    """
    T = len(daily_returns)
    if T < 10:
        return 0.5, 0.5, 0.0

    mu_d = float(np.mean(daily_returns))
    sd_d = float(np.std(daily_returns, ddof=1))
    if sd_d <= 1e-12:
        return 0.5, 0.5, 0.0

    sr_d = mu_d / sd_d
    g3 = float(skew(daily_returns, bias=False)) if T > 3 else 0.0
    g4 = float(kurtosis(daily_returns, fisher=False, bias=False)) if T > 4 else 3.0

    denom_var = (1.0 - g3 * sr_d + ((g4 - 1.0) / 4.0) * (sr_d ** 2)) / max(1, T - 1)
    sigma_sr = math.sqrt(max(1e-12, denom_var))

    psr = float(norm.cdf(sr_d / sigma_sr))

    M = len(all_annual_sharpes)
    if M <= 1:
        return psr, psr, 0.0

    var_ann = float(np.var(all_annual_sharpes, ddof=1))
    var_d = max(0.0, var_ann / annual_days)
    if var_d <= 1e-15:
        return psr, psr, 0.0

    z1 = float(norm.ppf(1.0 - 1.0 / M))
    z2 = float(norm.ppf(1.0 - 1.0 / (M * math.e)))
    sr0_d = math.sqrt(var_d) * ((1.0 - EULER_GAMMA) * z1 + EULER_GAMMA * z2)
    dsr = float(norm.cdf((sr_d - sr0_d) / sigma_sr))
    return psr, dsr, sr0_d * math.sqrt(annual_days)


def simulate_dibse_fsm(
    archive: ArchiveData,
    signals: CausalSignalTable,
    start_bar: int,
    end_bar: Optional[int] = None,
    ablation: str = "FULL_4GATE",
    cost_bps: float = 10.0,
    exit_mode: str = "close",
    init_capital: float = INITIAL_SANDBOX_USD,
    name: Optional[str] = None,
    category: str = "DIBSE",
) -> StrategyResult:
    """Simulate DIBSE Dual-Inventory Split-Sleeve FSM on [start_bar, end_bar)."""
    N = len(archive.closes)
    if end_bar is None or end_bar > N:
        end_bar = N
    if start_bar >= end_bar:
        raise ValueError(f"Empty simulation window: start_bar={start_bar}, end_bar={end_bar}")

    fee_rate = cost_bps / 10_000.0
    trig_a, trig_b = get_triggers_for_ablation(signals, ablation)

    opens = archive.opens
    highs = archive.highs
    lows = archive.lows
    closes = archive.closes
    poc_arr = signals.poc_30
    val_arr = signals.val_30
    vah_arr = signals.vah_30

    p0 = float(closes[start_bar])
    half_cap = init_capital * 0.5

    # Sleeve A (USDT -> BTC -> USDT)
    usdt_a = half_cap
    btc_a = 0.0
    state_a = "READY_USDT"
    target_a = 0.0
    entry_bar_a = -1
    a_entries = 0
    a_completed = 0
    a_bars_holding_btc = 0
    a_curr_stuck = 0
    a_max_stuck = 0

    # Sleeve B (BTC -> USDT -> BTC)
    btc_b_init = half_cap / p0
    btc_b = btc_b_init
    usdt_b = 0.0
    state_b = "HOLDING_BTC"
    buyback_b = 0.0
    sell_bar_b = -1
    b_sells = 0
    b_completed = 0
    b_bars_holding_usdt = 0
    b_curr_stuck = 0
    b_max_stuck = 0

    total_fees_usd = 0.0
    total_notional_usd = 0.0
    win_len = end_bar - start_bar
    equity_4h = np.zeros(win_len, dtype=np.float64)

    for idx, k in enumerate(range(start_bar, end_bar)):
        ok = float(opens[k])
        hk = float(highs[k])
        lk = float(lows[k])
        ck = float(closes[k])

        # --- Sleeve A FSM ---
        if state_a == "HOLDING_BTC":
            exited_a = False
            exec_px_a = ck
            if k > entry_bar_a:
                if exit_mode == "close" and ck >= target_a:
                    exited_a = True
                    exec_px_a = ck
                elif exit_mode == "limit" and hk > target_a:
                    exited_a = True
                    exec_px_a = max(ok, target_a)

            if exited_a:
                gross_usd = btc_a * exec_px_a
                fee_usd = gross_usd * fee_rate
                usdt_a = gross_usd - fee_usd
                btc_a = 0.0
                total_fees_usd += fee_usd
                total_notional_usd += gross_usd
                state_a = "READY_USDT"
                a_completed += 1
                a_curr_stuck = 0
            else:
                a_bars_holding_btc += 1
                a_curr_stuck += 1
                if a_curr_stuck > a_max_stuck:
                    a_max_stuck = a_curr_stuck
        elif state_a == "READY_USDT" and trig_a[k]:
            notional = usdt_a
            fee_usd = notional * fee_rate
            btc_a = (notional - fee_usd) / ck
            usdt_a = 0.0
            total_fees_usd += fee_usd
            total_notional_usd += notional
            poc = float(poc_arr[k])
            vah = float(vah_arr[k])
            if ck < poc * 0.98:
                target_a = poc
            elif ck < vah * 0.98:
                target_a = vah
            else:
                target_a = ck * 1.04
            entry_bar_a = k
            state_a = "HOLDING_BTC"
            a_entries += 1
            a_curr_stuck = 0

        # --- Sleeve B FSM ---
        if state_b == "HOLDING_USDT":
            rebought_b = False
            exec_px_b = ck
            if k > sell_bar_b:
                if exit_mode == "close" and ck <= buyback_b:
                    rebought_b = True
                    exec_px_b = ck
                elif exit_mode == "limit" and lk < buyback_b:
                    rebought_b = True
                    exec_px_b = min(ok, buyback_b)

            if rebought_b:
                notional = usdt_b
                fee_usd = notional * fee_rate
                btc_b = (notional - fee_usd) / exec_px_b
                usdt_b = 0.0
                total_fees_usd += fee_usd
                total_notional_usd += notional
                state_b = "HOLDING_BTC"
                b_completed += 1
                b_curr_stuck = 0
            else:
                b_bars_holding_usdt += 1
                b_curr_stuck += 1
                if b_curr_stuck > b_max_stuck:
                    b_max_stuck = b_curr_stuck
        elif state_b == "HOLDING_BTC" and trig_b[k]:
            gross_usd = btc_b * ck
            fee_usd = gross_usd * fee_rate
            usdt_b = gross_usd - fee_usd
            btc_b = 0.0
            total_fees_usd += fee_usd
            total_notional_usd += gross_usd
            poc = float(poc_arr[k])
            val = float(val_arr[k])
            if ck > poc * 1.02:
                buyback_b = poc
            elif ck > val * 1.02:
                buyback_b = val
            else:
                buyback_b = ck * 0.96
            sell_bar_b = k
            state_b = "HOLDING_USDT"
            b_sells += 1
            b_curr_stuck = 0

        equity_4h[idx] = (usdt_a + btc_a * ck) + (usdt_b + btc_b * ck)

    days_ms, daily_eq = resample_daily_utc(archive.open_times[start_bar:end_bar], equity_4h)
    metrics = compute_performance_metrics(days_ms, daily_eq)
    last_close = float(closes[end_bar - 1])
    final_a_usd = usdt_a + btc_a * last_close
    final_b_usd = usdt_b + btc_b * last_close
    final_b_btc_equiv = final_b_usd / last_close

    diagnostics = {
        "a_entries": a_entries,
        "a_completed": a_completed,
        "a_open_end": state_a == "HOLDING_BTC",
        "a_pct_bars_holding_btc": (a_bars_holding_btc / win_len) * 100.0,
        "a_max_stuck_days": (a_max_stuck * 4.0) / 24.0,
        "a_final_usd": final_a_usd,
        "a_return_pct": (final_a_usd / half_cap - 1.0) * 100.0,
        "b_sells": b_sells,
        "b_completed": b_completed,
        "b_open_end": state_b == "HOLDING_USDT",
        "b_pct_bars_holding_usdt": (b_bars_holding_usdt / win_len) * 100.0,
        "b_max_stuck_days": (b_max_stuck * 4.0) / 24.0,
        "b_initial_btc": btc_b_init,
        "b_final_btc_held": btc_b,
        "b_final_btc_equiv": final_b_btc_equiv,
        "b_btc_alpha_pct": (final_b_btc_equiv / btc_b_init - 1.0) * 100.0,
        "b_final_usd": final_b_usd,
        "b_return_pct": (final_b_usd / half_cap - 1.0) * 100.0,
        "total_fees_usd": total_fees_usd,
        "turnover_x": total_notional_usd / init_capital,
        "final_equity_usd": float(equity_4h[-1]),
    }

    return StrategyResult(
        name=name or f"DIBSE_{ablation}",
        category=category,
        cost_bps=cost_bps,
        exit_mode=exit_mode,
        daily_days_ms=days_ms,
        daily_equity=daily_eq,
        metrics=metrics,
        diagnostics=diagnostics,
    )


def simulate_benchmarks(
    archive: ArchiveData,
    start_bar: int,
    end_bar: Optional[int] = None,
    cost_bps: float = 10.0,
    init_capital: float = INITIAL_SANDBOX_USD,
) -> List[StrategyResult]:
    """Run 4 apples-to-apples baselines on exact same window and starting capital."""
    N = len(archive.closes)
    if end_bar is None or end_bar > N:
        end_bar = N
    fee_rate = cost_bps / 10_000.0
    closes = archive.closes[start_bar:end_bar]
    times = archive.open_times[start_bar:end_bar]
    p0 = float(closes[0])

    results: List[StrategyResult] = []

    # 1. 100% BTC Buy & Hold
    eq_bh = (init_capital / p0) * closes
    d_ms, d_eq = resample_daily_utc(times, eq_bh)
    results.append(
        StrategyResult(
            name="BENCH_BH_100_BTC",
            category="BENCHMARK",
            cost_bps=cost_bps,
            exit_mode="hold",
            daily_days_ms=d_ms,
            daily_equity=d_eq,
            metrics=compute_performance_metrics(d_ms, d_eq),
            diagnostics={"final_equity_usd": float(eq_bh[-1]), "turnover_x": 0.0, "total_fees_usd": 0.0},
        )
    )

    # 2. Passive 50/50 Untouched Hold (isolates permanent 50% cash drag)
    eq_50_hold = (init_capital * 0.5) + (init_capital * 0.5 / p0) * closes
    d_ms, d_eq = resample_daily_utc(times, eq_50_hold)
    results.append(
        StrategyResult(
            name="BENCH_50_50_HOLD",
            category="BENCHMARK",
            cost_bps=cost_bps,
            exit_mode="hold",
            daily_days_ms=d_ms,
            daily_equity=d_eq,
            metrics=compute_performance_metrics(d_ms, d_eq),
            diagnostics={"final_equity_usd": float(eq_50_hold[-1]), "turnover_x": 0.0, "total_fees_usd": 0.0},
        )
    )

    # 3a. Passive 50/50 Weekly Rebalancer (Shannon's Demon)
    usdt = init_capital * 0.5
    btc = (init_capital * 0.5) / p0
    eq_reb_wk = np.zeros(len(closes), dtype=np.float64)
    fees_wk = 0.0
    notional_wk = 0.0
    trades_wk = 0
    for idx in range(len(closes)):
        ck = float(closes[idx])
        if idx > 0 and idx % 42 == 0:
            tot = usdt + btc * ck
            target_btc_val = tot * 0.5
            diff = target_btc_val - (btc * ck)
            if abs(diff) > 1e-6:
                fee = abs(diff) * fee_rate
                if diff > 0:
                    # Buy BTC with USDT
                    spend = min(usdt, diff)
                    fee = spend * fee_rate
                    usdt -= spend
                    btc += (spend - fee) / ck
                    notional_wk += spend
                else:
                    # Sell BTC to USDT
                    sell_val = min(btc * ck, -diff)
                    fee = sell_val * fee_rate
                    btc -= sell_val / ck
                    usdt += sell_val - fee
                    notional_wk += sell_val
                fees_wk += fee
                trades_wk += 1
        eq_reb_wk[idx] = usdt + btc * ck
    d_ms, d_eq = resample_daily_utc(times, eq_reb_wk)
    results.append(
        StrategyResult(
            name="BENCH_50_50_REBAL_WK",
            category="BENCHMARK",
            cost_bps=cost_bps,
            exit_mode="weekly",
            daily_days_ms=d_ms,
            daily_equity=d_eq,
            metrics=compute_performance_metrics(d_ms, d_eq),
            diagnostics={
                "final_equity_usd": float(eq_reb_wk[-1]),
                "rebalances": trades_wk,
                "total_fees_usd": fees_wk,
                "turnover_x": notional_wk / init_capital,
            },
        )
    )

    # 3b. Passive 50/50 Band (+/-5% weight drift -> rebalance to 50%)
    usdt = init_capital * 0.5
    btc = (init_capital * 0.5) / p0
    eq_reb_band = np.zeros(len(closes), dtype=np.float64)
    fees_band = 0.0
    notional_band = 0.0
    trades_band = 0
    for idx in range(len(closes)):
        ck = float(closes[idx])
        tot = usdt + btc * ck
        w_btc = (btc * ck) / tot if tot > 0 else 0.0
        if idx > 0 and abs(w_btc - 0.5) >= 0.05:
            diff = (tot * 0.5) - (btc * ck)
            if diff > 0:
                spend = min(usdt, diff)
                fee = spend * fee_rate
                usdt -= spend
                btc += (spend - fee) / ck
                notional_band += spend
            else:
                sell_val = min(btc * ck, -diff)
                fee = sell_val * fee_rate
                btc -= sell_val / ck
                usdt += sell_val - fee
                notional_band += sell_val
            fees_band += fee
            trades_band += 1
        eq_reb_band[idx] = usdt + btc * ck
    d_ms, d_eq = resample_daily_utc(times, eq_reb_band)
    results.append(
        StrategyResult(
            name="BENCH_50_50_REBAL_5PCT",
            category="BENCHMARK",
            cost_bps=cost_bps,
            exit_mode="band5pct",
            daily_days_ms=d_ms,
            daily_equity=d_eq,
            metrics=compute_performance_metrics(d_ms, d_eq),
            diagnostics={
                "final_equity_usd": float(eq_reb_band[-1]),
                "rebalances": trades_band,
                "total_fees_usd": fees_band,
                "turnover_x": notional_band / init_capital,
            },
        )
    )

    # 4. Detzel-style Daily 200d SMA (100% BTC when Daily Close > 200d SMA, else USDT)
    spot_mask = archive.spot_full_open_times <= archive.open_times[-1]
    full_d_days, full_d_closes = resample_daily_utc(
        archive.spot_full_open_times[spot_mask], archive.spot_full_closes[spot_mask]
    )
    eval_days, eval_d_closes = resample_daily_utc(times, closes)
    day_to_full_idx = {int(d): i for i, d in enumerate(full_d_days)}

    eq_detzel = np.zeros(len(eval_days), dtype=np.float64)
    in_btc = False
    usdt_d = init_capital
    btc_d = 0.0
    fees_d = 0.0
    notional_d = 0.0
    switches_d = 0

    # Initialize exposure from the last closed daily bar strictly preceding eval_days[0]
    first_full_idx = day_to_full_idx.get(int(eval_days[0]), -1)
    if first_full_idx >= 200:
        prev_px = float(full_d_closes[first_full_idx - 1])
        prev_sma = float(np.mean(full_d_closes[first_full_idx - 200 : first_full_idx]))
        if prev_px > prev_sma:
            btc_d = usdt_d / p0
            usdt_d = 0.0
            in_btc = True

    for j, d_ms_val in enumerate(eval_days):
        fi = day_to_full_idx.get(int(d_ms_val))
        px = float(eval_d_closes[j])
        if fi is None or fi < 199:
            eq_detzel[j] = usdt_d + btc_d * px
            continue
        sma200 = float(np.mean(full_d_closes[fi - 199 : fi + 1]))
        want_btc = px > sma200
        if want_btc and not in_btc:
            notional = usdt_d
            fee = notional * fee_rate
            btc_d = (notional - fee) / px
            usdt_d = 0.0
            fees_d += fee
            notional_d += notional
            in_btc = True
            switches_d += 1
        elif not want_btc and in_btc:
            gross = btc_d * px
            fee = gross * fee_rate
            usdt_d = gross - fee
            btc_d = 0.0
            fees_d += fee
            notional_d += gross
            in_btc = False
            switches_d += 1
        eq_detzel[j] = usdt_d + btc_d * px

    results.append(
        StrategyResult(
            name="BENCH_DETZEL_200D_SMA",
            category="BENCHMARK",
            cost_bps=cost_bps,
            exit_mode="daily_close",
            daily_days_ms=eval_days,
            daily_equity=eq_detzel,
            metrics=compute_performance_metrics(eval_days, eq_detzel),
            diagnostics={
                "final_equity_usd": float(eq_detzel[-1]),
                "switches": switches_d,
                "total_fees_usd": fees_d,
                "turnover_x": notional_d / init_capital,
            },
        )
    )

    return results


def run_multiyear_event_study(
    archive: ArchiveData,
    signals: CausalSignalTable,
    start_bar: int,
    embargo_bars: int = 30,
) -> Dict[str, Any]:
    """Run full-sample 5D-embargoed independent event study for Loop A and Loop B."""
    closes = archive.closes
    N = len(closes)
    end_idx = N - 60  # Require 10D (60 bars) forward observability

    base_r: Dict[int, List[float]] = {6: [], 18: [], 30: [], 60: []}
    for k in range(start_bar, end_idx):
        ck = closes[k]
        for h in (6, 18, 30, 60):
            base_r[h].append((closes[k + h] - ck) / ck)

    trig_a = signals.valid_mask & signals.a_g1 & signals.a_g2 & signals.a_g3 & signals.a_g4
    trig_b = signals.valid_mask & signals.b_g1 & signals.b_g2 & signals.b_g3 & signals.b_g4

    def _collect(mask: np.ndarray, is_loop_b: bool) -> Dict[str, Any]:
        last_k = -9999
        events: Dict[int, List[float]] = {6: [], 18: [], 30: [], 60: []}
        for k in range(start_bar, end_idx):
            if k < last_k + embargo_bars:
                continue
            if mask[k]:
                last_k = k
                ck = closes[k]
                for h in (6, 18, 30, 60):
                    r = (ck - closes[k + h]) / ck if is_loop_b else (closes[k + h] - ck) / ck
                    events[h].append(float(r))
        count = len(events[6])
        summary: Dict[str, Any] = {"count": count}
        for h, label in ((6, "1d"), (18, "3d"), (30, "5d"), (60, "10d")):
            arr = np.array(events[h], dtype=np.float64) * 100.0
            base_arr = (
                -np.array(base_r[h], dtype=np.float64) * 100.0
                if is_loop_b
                else np.array(base_r[h], dtype=np.float64) * 100.0
            )
            base_mean = float(np.mean(base_arr)) if len(base_arr) else 0.0
            if count == 0:
                summary[label] = {
                    "mean_pct": 0.0,
                    "median_pct": 0.0,
                    "win_rate_pct": 0.0,
                    "baseline_mean_pct": base_mean,
                    "alpha_pct": 0.0,
                    "t_stat": 0.0,
                }
            else:
                mu = float(np.mean(arr))
                sd = float(np.std(arr, ddof=1)) if count > 1 else 0.0
                t_val = (mu / (sd / math.sqrt(count))) if sd > 1e-12 else 0.0
                summary[label] = {
                    "mean_pct": mu,
                    "median_pct": float(np.median(arr)),
                    "win_rate_pct": float(np.mean(arr > 0.0) * 100.0),
                    "baseline_mean_pct": base_mean,
                    "alpha_pct": mu - base_mean,
                    "t_stat": t_val,
                }
        return summary

    return {
        "eval_bars": max(0, end_idx - start_bar),
        "embargo_bars": embargo_bars,
        "loop_a": _collect(trig_a, is_loop_b=False),
        "loop_b": _collect(trig_b, is_loop_b=True),
    }


def compute_subperiod_attribution(
    results: Sequence[StrategyResult],
) -> List[Dict[str, Any]]:
    """Slice continuous daily equity curves into market regimes (2020-21, 2022, 2023-24, 2025+)."""
    regimes = [
        ("2020-2021 (Bull/Cycle)", "2020-01-01", "2022-01-01"),
        ("2022 (Bear/Crash)", "2022-01-01", "2023-01-01"),
        ("2023-2024 (Recovery/ETF)", "2023-01-01", "2025-01-01"),
        ("2025-Present (Late Cycle)", "2025-01-01", "2099-01-01"),
    ]

    rows: List[Dict[str, Any]] = []
    for label, s_date, e_date in regimes:
        s_ms = int(datetime.strptime(s_date, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp() * 1000)
        e_ms = int(datetime.strptime(e_date, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp() * 1000)
        regime_data: Dict[str, Any] = {"regime": label, "strategies": []}
        for res in results:
            mask = (res.daily_days_ms >= s_ms) & (res.daily_days_ms < e_ms)
            if int(np.sum(mask)) < 10:
                continue
            m = compute_performance_metrics(res.daily_days_ms[mask], res.daily_equity[mask])
            regime_data["strategies"].append({"name": res.name, **m})
        if regime_data["strategies"]:
            rows.append(regime_data)
    return rows


def find_eval_start_bar(archive: ArchiveData, start_ms: int = EVAL_START_2020_MS) -> int:
    """Return first bar index >= start_ms with valid causal signals (>=185)."""
    idx = int(np.searchsorted(archive.open_times, start_ms, side="left"))
    return max(185, idx)


def run_full_validation_suite(
    cache_path: Path = DEFAULT_CACHE_PATH,
    force_refresh: bool = False,
) -> Dict[str, Any]:
    """Execute complete G1 validation, benchmarks, ablations, stress tests, and PSR/DSR."""
    archive = load_or_fetch_archive(cache_path=cache_path, force_refresh=force_refresh)
    signals = extract_causal_signals(archive)
    start_bar = find_eval_start_bar(archive, EVAL_START_2020_MS)

    # 1. Core Benchmarks (1x = 10 bps/side)
    benchmarks_1x = simulate_benchmarks(archive, start_bar=start_bar, cost_bps=10.0)

    # 2. DIBSE + Gate Ablation Matrix (1x = 10 bps/side, bar-close exits)
    ablation_keys = [
        ("DIBSE_FULL_4GATE", "FULL_4GATE", "DIBSE"),
        ("DIBSE_LOOP_A_ONLY", "LOOP_A_ONLY", "ABLATION"),
        ("DIBSE_LOOP_B_ONLY", "LOOP_B_ONLY", "ABLATION"),
        ("ABL_G3_ONLY", "G3_ONLY", "ABLATION"),
        ("ABL_G3_G1", "G3_G1", "ABLATION"),
        ("ABL_G3_G2", "G3_G2", "ABLATION"),
        ("ABL_G3_G4", "G3_G4", "ABLATION"),
    ]
    dibse_and_ablations: List[StrategyResult] = [
        simulate_dibse_fsm(
            archive, signals, start_bar=start_bar, ablation=abl, cost_bps=10.0, exit_mode="close", name=nm, category=cat
        )
        for nm, abl, cat in ablation_keys
    ]

    # 3. Cost Stress (2x = 20 bps/side) & Resting Limit Sensitivity Check
    stress_results: List[StrategyResult] = [
        simulate_dibse_fsm(
            archive, signals, start_bar=start_bar, ablation="FULL_4GATE", cost_bps=20.0, exit_mode="close", name="DIBSE_FULL_20BPS", category="STRESS"
        ),
        simulate_dibse_fsm(
            archive, signals, start_bar=start_bar, ablation="FULL_4GATE", cost_bps=10.0, exit_mode="limit", name="DIBSE_FULL_LIMIT_10BPS", category="STRESS"
        ),
        simulate_dibse_fsm(
            archive, signals, start_bar=start_bar, ablation="FULL_4GATE", cost_bps=20.0, exit_mode="limit", name="DIBSE_FULL_LIMIT_20BPS", category="STRESS"
        ),
    ]
    benchmarks_2x = simulate_benchmarks(archive, start_bar=start_bar, cost_bps=20.0)

    # Deflated Sharpe Ratio across all DIBSE + Ablation + Stress active trials
    # (Benchmarks are passive references; M counts active rule variants tested)
    active_variants = dibse_and_ablations + stress_results
    sharpe_pool = [r.metrics["sharpe"] for r in active_variants]

    all_main = [dibse_and_ablations[0]] + benchmarks_1x + dibse_and_ablations[1:] + stress_results
    psr_dsr_map: Dict[str, Dict[str, float]] = {}
    for res in all_main:
        d_rets = res.daily_equity[1:] / res.daily_equity[:-1] - 1.0
        psr, dsr, sr0_ann = compute_psr_dsr(d_rets, sharpe_pool)
        psr_dsr_map[res.name] = {"psr": psr, "dsr": dsr, "sr0_ann": sr0_ann}

    # Sub-period attribution on Full DIBSE, Loop A Only, Loop B Only, and 4 Benchmarks
    subperiod_targets = [
        dibse_and_ablations[0],
        dibse_and_ablations[1],
        dibse_and_ablations[2],
        benchmarks_1x[0],
        benchmarks_1x[1],
        benchmarks_1x[2],
        benchmarks_1x[4],
    ]
    subperiods = compute_subperiod_attribution(subperiod_targets)
    event_study = run_multiyear_event_study(archive, signals, start_bar=start_bar, embargo_bars=30)

    return {
        "archive": archive,
        "start_bar": start_bar,
        "eval_start_utc": datetime.fromtimestamp(archive.open_times[start_bar] / 1000.0, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "eval_end_utc": datetime.fromtimestamp((archive.open_times[-1] + FOUR_HOURS_MS) / 1000.0, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "n_trials_dsr": len(active_variants),
        "dibse_and_ablations": dibse_and_ablations,
        "benchmarks_1x": benchmarks_1x,
        "benchmarks_2x": benchmarks_2x,
        "stress_results": stress_results,
        "psr_dsr_map": psr_dsr_map,
        "subperiods": subperiods,
        "event_study": event_study,
    }


def format_markdown_report(suite: Dict[str, Any]) -> str:
    """Format full empirical G1 validation results into an honest Markdown report."""
    arch: ArchiveData = suite["archive"]
    meta = arch.meta
    psr_map = suite["psr_dsr_map"]
    dibse_full: StrategyResult = suite["dibse_and_ablations"][0]
    ablations: List[StrategyResult] = suite["dibse_and_ablations"]
    benches: List[StrategyResult] = suite["benchmarks_1x"]
    stresses: List[StrategyResult] = suite["stress_results"]
    benches_2x: List[StrategyResult] = suite["benchmarks_2x"]
    es = suite["event_study"]

    lines: List[str] = []
    lines.append("# DIBSE G1 Historical Validation & Ablation Report")
    lines.append("")
    lines.append(f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}  ")
    lines.append(f"**Evaluation Horizon:** `{suite['eval_start_utc']}` -> `{suite['eval_end_utc']}`  ")
    lines.append("**Starting Active Sandbox:** \$20,000.00 (\$10,000.00 USDT Sleeve A + \$10,000.00 BTC Sleeve B; untouched 80% Core excluded)  ")
    lines.append("**Methodology:** Strictly closed 4H Binance Spot & Perp klines, causal 8H funding (`<= bar_close`), frozen G0 thresholds (no tuning), daily 00:00 UTC return resampling (`sqrt(365)` annualization), BAILEY-LdP DSR across `M = %d` active variants." % suite["n_trials_dsr"])
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 1. Data Integrity & Coverage Audit")
    lines.append("")
    lines.append(f"- **Aligned Spot + Perp Closed 4H Bars:** `{meta['aligned_bars']:,}` (`{meta['aligned_start_utc']}` -> `{meta['aligned_end_close_utc']}`)")
    lines.append(f"- **Full Spot Warmup Archive (for 200d SMA):** `{meta['spot_full_bars']:,}` bars (from `{meta['spot_start_utc']}`)")
    lines.append(f"- **Causal 8H Funding Prints:** `{meta['funding_prints']:,}` prints")
    lines.append(f"- **Timestamp Mismatches Dropped:** Spot-only=`{meta['spot_only_dropped']}`, Perp-only=`{meta['perp_only_dropped']}`")
    lines.append(f"- **Exchange Maintenance Gaps (>4h step):** `{meta['gap_events']}` gap events (`{meta['total_missing_4h_bars']}` missing 4H bars)")
    lines.append("")

    def _perf_table(title: str, items: Sequence[StrategyResult]) -> None:
        lines.append(f"## {title}")
        lines.append("")
        lines.append("| Strategy / Benchmark | Cost (bps) | Final Eq | Tot Ret | CAGR | Ann Vol | Max DD | Sharpe | Sortino | Calmar | t-stat | PSR(0) | DSR |")
        lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
        for r in items:
            m = r.metrics
            p = psr_map.get(r.name, {"psr": 0.0, "dsr": 0.0})
            lines.append(
                f"| `{r.name}` | {r.cost_bps:.0f} | \${m and r.diagnostics.get('final_equity_usd', 0):,.0f} | "
                f"{m['total_return_pct']:+.1f}% | {m['cagr_pct']:+.2f}% | {m['ann_vol_pct']:.1f}% | "
                f"{m['max_dd_pct']:.1f}% | {m['sharpe']:.2f} | {m['sortino']:.2f} | {m['calmar']:.2f} | "
                f"{m['t_stat']:.2f} | {p['psr']*100:.1f}% | {p['dsr']*100:.1f}% |"
            )
        lines.append("")

    _perf_table("2. Headline Performance: DIBSE vs. Four Apples-to-Apples Benchmarks (10 bps/side)", [dibse_full] + benches)

    lines.append("## 3. Dual-Sleeve Cycle & Inventory Mechanics Diagnostics (Full 4-Gate, 10 bps)")
    lines.append("")
    d = dibse_full.diagnostics
    lines.append("| Sleeve | Triggers | Completed Cycles | Open at End | % Time Exposed / Parked | Max Stuck Wait | Sleeve Ending USD | Sleeve Return |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    lines.append(
        f"| **Loop A (`USDT -> BTC -> USDT`)** | {d['a_entries']} | {d['a_completed']} | "
        f"{'YES (BTC)' if d['a_open_end'] else 'NO (USDT)'} | {d['a_pct_bars_holding_btc']:.1f}% holding BTC | "
        f"{d['a_max_stuck_days']:.1f} days | \${d['a_final_usd']:,.2f} | {d['a_return_pct']:+.2f}% |"
    )
    lines.append(
        f"| **Loop B (`BTC -> USDT -> BTC`)** | {d['b_sells']} | {d['b_completed']} | "
        f"{'YES (USDT)' if d['b_open_end'] else 'NO (BTC)'} | {d['b_pct_bars_holding_usdt']:.1f}% parked USDT | "
        f"{d['b_max_stuck_days']:.1f} days | \${d['b_final_usd']:,.2f} | {d['b_return_pct']:+.2f}% |"
    )
    lines.append("")
    lines.append(f"- **Loop B Satoshi Stack Audit:** Initial BTC=`{d['b_initial_btc']:.5f} BTC` -> Ending BTC-Equivalent=`{d['b_final_btc_equiv']:.5f} BTC` (`{d['b_btc_alpha_pct']:+.2f}%` vs passively holding Sleeve B's initial BTC!)")
    lines.append(f"- **Total Trading Fees Paid (10 bps/side):** \${d['total_fees_usd']:,.2f} (`{d['turnover_x']:.2f}x` sandbox notional turnover)")
    lines.append("")

    _perf_table("4. Gate Ablation & Sleeve Isolation Matrix (10 bps/side, Bar-Close Exits)", ablations)

    lines.append("| Variant | Loop A Ent / Done | Loop B Sell / Done | Loop A Time in BTC | Loop B Time in USDT | Loop B BTC Alpha | Fees USD |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|")
    for r in ablations:
        dd = r.diagnostics
        lines.append(
            f"| `{r.name}` | {dd['a_entries']} / {dd['a_completed']} | {dd['b_sells']} / {dd['b_completed']} | "
            f"{dd['a_pct_bars_holding_btc']:.1f}% | {dd['b_pct_bars_holding_usdt']:.1f}% | "
            f"{dd['b_btc_alpha_pct']:+.2f}% | \${dd['total_fees_usd']:,.0f} |"
        )
    lines.append("")

    _perf_table("5. Transaction Cost Stress (2x = 20 bps) & Resting Limit Exit Sensitivity", [dibse_full] + stresses + [benches_2x[2], benches_2x[3], benches_2x[4]])

    lines.append("## 6. Sub-Period Regime Attribution (Continuous Daily Equity Slices)")
    lines.append("")
    for reg in suite["subperiods"]:
        lines.append(f"### {reg['regime']}")
        lines.append("")
        lines.append("| Strategy | Tot Ret | CAGR | Max DD | Sharpe | Sortino |")
        lines.append("|---|---:|---:|---:|---:|---:|")
        for s in reg["strategies"]:
            lines.append(
                f"| `{s['name']}` | {s['total_return_pct']:+.1f}% | {s['cagr_pct']:+.1f}% | "
                f"{s['max_dd_pct']:.1f}% | {s['sharpe']:.2f} | {s['sortino']:.2f} |"
            )
        lines.append("")

    lines.append(f"## 7. Multi-Year De-Clustered Forward Event Study ({es['embargo_bars']}-Bar / 5D Embargo, N={es['eval_bars']:,} bars)")
    lines.append("")
    lines.append(f"- **Loop A Independent Buy Triggers (`N_A`):** `{es['loop_a']['count']}`")
    lines.append(f"- **Loop B Independent Sell Triggers (`N_B`):** `{es['loop_b']['count']}`")
    lines.append("")
    lines.append("| Loop & Horizon | N | Mean Ret | Median Ret | Win Rate | Uncond Baseline | Alpha vs Base | t-stat |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for loop_lbl, key in (("Loop A (Forward +Ret)", "loop_a"), ("Loop B (Price Drop / Discount)", "loop_b")):
        obj = es[key]
        cnt = obj["count"]
        for h_lbl in ("1d", "3d", "5d", "10d"):
            st = obj[h_lbl]
            lines.append(
                f"| {loop_lbl} **{h_lbl.upper()}** | {cnt} | {st['mean_pct']:+.2f}% | {st['median_pct']:+.2f}% | "
                f"{st['win_rate_pct']:.1f}% | {st['baseline_mean_pct']:+.2f}% | {st['alpha_pct']:+.2f}% | {st['t_stat']:.2f} |"
            )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    print("Fetching / loading Binance 4H historical archives (2019-2026)...")
    suite = run_full_validation_suite()
    report_md = format_markdown_report(suite)
    DEFAULT_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    DEFAULT_REPORT_PATH.write_text(report_md, encoding="utf-8")
    print(f"Wrote validation report to: {DEFAULT_REPORT_PATH}")
    print(f"Archive cached at: {DEFAULT_CACHE_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
