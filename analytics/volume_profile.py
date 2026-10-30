"""Composite Volume Profile engine: 70% Value Area, Gaussian HVN/LVN solver, and ATR."""

from typing import List, Optional, Sequence

import numpy as np

from core.models import KlineBar, VolumeProfileResult


def _gaussian_smooth_1d(values: np.ndarray, sigma: float = 1.5) -> np.ndarray:
    """Applies a 1D Gaussian smoothing kernel with reflection padding."""
    if len(values) < 5 or sigma <= 0:
        return values.copy()
    radius = max(1, int(round(3.0 * sigma)))
    x = np.arange(-radius, radius + 1, dtype=float)
    kernel = np.exp(-0.5 * (x / sigma) ** 2)
    kernel /= np.sum(kernel)
    padded = np.pad(values, pad_width=radius, mode="reflect")
    return np.convolve(padded, kernel, mode="valid")


def compute_composite_profile(
    bars: Sequence[KlineBar],
    horizon_label: str = "30D Macro",
    num_bins: int = 120,
    value_area_pct: float = 0.70,
    gaussian_sigma: float = 1.5,
    lvn_rel_threshold: float = 0.55,
    hvn_rel_threshold: float = 1.20,
) -> Optional[VolumeProfileResult]:
    """Constructs a high-resolution Composite Volume Profile from OHLCV klines.

    Distributes each candle's volume across intersected price bins weighted by a
    triangular kernel centered at the candle's typical price (H + L + C) / 3.
    Computes the CME-standard 70% Value Area (cVAH, cPOC, cVAL) and identifies
    High Volume Nodes (HVNs) and Low Volume Nodes (LVNs).
    """
    if not bars or len(bars) < 2:
        return None

    range_low = min(b.low for b in bars)
    range_high = max(b.high for b in bars)
    if range_high <= range_low:
        return None

    bin_edges = np.linspace(range_low, range_high, num_bins + 1)
    bin_centers = 0.5 * (bin_edges[:-1] + bin_edges[1:])
    bin_width = float(bin_edges[1] - bin_edges[0])
    bin_volumes = np.zeros(num_bins, dtype=float)

    # Distribute each bar's volume across intersected bins
    for bar in bars:
        if bar.volume <= 0:
            continue
        idx_start = int(np.searchsorted(bin_edges, bar.low, side="right")) - 1
        idx_end = int(np.searchsorted(bin_edges, bar.high, side="left"))
        idx_start = max(0, min(num_bins - 1, idx_start))
        idx_end = max(idx_start, min(num_bins - 1, idx_end))

        if idx_start == idx_end:
            bin_volumes[idx_start] += bar.volume
        else:
            centers_slice = bin_centers[idx_start : idx_end + 1]
            half_span = max(0.5 * (bar.high - bar.low), bin_width)
            dist = np.abs(centers_slice - bar.typical_price)
            weights = np.maximum(0.15, 1.0 - (dist / (1.25 * half_span)))
            weights_sum = float(np.sum(weights))
            if weights_sum > 0:
                bin_volumes[idx_start : idx_end + 1] += bar.volume * (weights / weights_sum)
            else:
                count = idx_end - idx_start + 1
                bin_volumes[idx_start : idx_end + 1] += bar.volume / count

    total_vol = float(np.sum(bin_volumes))
    if total_vol <= 0:
        return None

    # 1. Point of Control (cPOC)
    poc_idx = int(np.argmax(bin_volumes))
    c_poc = float(bin_centers[poc_idx])

    # 2. CME-Standard 70% Value Area Expansion
    target_va_vol = total_vol * value_area_pct
    acc_vol = float(bin_volumes[poc_idx])
    low_idx = poc_idx
    high_idx = poc_idx

    while acc_vol < target_va_vol and (low_idx > 0 or high_idx < num_bins - 1):
        # Evaluate 2-bin steps above vs below (standard Market Profile dual-TPO step)
        up_step_indices = [i for i in (high_idx + 1, high_idx + 2) if i < num_bins]
        down_step_indices = [i for i in (low_idx - 1, low_idx - 2) if i >= 0]

        up_vol = sum(float(bin_volumes[i]) for i in up_step_indices) if up_step_indices else -1.0
        down_vol = sum(float(bin_volumes[i]) for i in down_step_indices) if down_step_indices else -1.0

        if up_step_indices and down_step_indices and abs(up_vol - down_vol) <= 1e-9:
            # Symmetric tie-break: expand 1 bin up and 1 bin down
            high_idx = up_step_indices[0]
            acc_vol += float(bin_volumes[high_idx])
            if acc_vol < target_va_vol:
                low_idx = down_step_indices[0]
                acc_vol += float(bin_volumes[low_idx])
        elif up_vol > down_vol and up_step_indices:
            for i in up_step_indices:
                high_idx = i
                acc_vol += float(bin_volumes[i])
                if acc_vol >= target_va_vol:
                    break
        elif down_step_indices:
            for i in down_step_indices:
                low_idx = i
                acc_vol += float(bin_volumes[i])
                if acc_vol >= target_va_vol:
                    break
        elif up_step_indices:
            for i in up_step_indices:
                high_idx = i
                acc_vol += float(bin_volumes[i])
                if acc_vol >= target_va_vol:
                    break
        else:
            break

    c_val = float(bin_centers[low_idx])
    c_vah = float(bin_centers[high_idx])

    # 3. Gaussian-Smoothed Topology for HVN and LVN Detection
    smoothed = _gaussian_smooth_1d(bin_volumes, sigma=gaussian_sigma)
    mean_bin_vol = float(np.mean(smoothed))

    lvn_levels: List[float] = []
    hvn_levels: List[float] = []

    for i in range(1, num_bins - 1):
        val = float(smoothed[i])
        prev_v = float(smoothed[i - 1])
        next_v = float(smoothed[i + 1])

        # Local minimum -> candidate LVN
        if val < prev_v and val < next_v and val <= lvn_rel_threshold * mean_bin_vol:
            lvn_levels.append(float(bin_centers[i]))

        # Local maximum -> candidate HVN
        if val > prev_v and val > next_v and val >= hvn_rel_threshold * mean_bin_vol:
            hvn_levels.append(float(bin_centers[i]))

    # 4. Identify Primary LVN Below cVAL (sweep liquidity void) & Support HVN Below cVAL
    lvns_below_val = [lvl for lvl in lvn_levels if lvl < c_val]
    primary_lvn_below_val: Optional[float] = None
    if lvns_below_val:
        # Closest significant LVN immediately below cVAL
        primary_lvn_below_val = max(lvns_below_val)
    elif low_idx > 2:
        # Fallback: minimum volume bin in the lower tail below cVAL
        tail_slice = smoothed[max(0, low_idx - 20) : low_idx]
        if len(tail_slice) > 0:
            min_rel_idx = max(0, low_idx - 20) + int(np.argmin(tail_slice))
            primary_lvn_below_val = float(bin_centers[min_rel_idx])

    ref_ceiling = primary_lvn_below_val if primary_lvn_below_val is not None else c_val
    hvns_below_val = [lvl for lvl in hvn_levels if lvl < ref_ceiling]
    support_hvn_below_val: Optional[float] = None
    if hvns_below_val:
        support_hvn_below_val = max(hvns_below_val)
    elif low_idx > 1:
        # Fallback: lower Value Area tail support shelf below primary LVN
        ref_idx = int(np.searchsorted(bin_centers, ref_ceiling))
        support_hvn_below_val = float(bin_centers[max(0, ref_idx // 2)])

    return VolumeProfileResult(
        horizon_label=horizon_label,
        c_vah=c_vah,
        c_poc=c_poc,
        c_val=c_val,
        range_high=range_high,
        range_low=range_low,
        total_volume=total_vol,
        bin_width=bin_width,
        lvn_levels=lvn_levels,
        hvn_levels=hvn_levels,
        primary_lvn_below_val=primary_lvn_below_val,
        support_hvn_below_val=support_hvn_below_val,
        bin_centers=[float(x) for x in bin_centers],
        bin_volumes=[float(x) for x in bin_volumes],
    )


def synthesize_4h_bars(bars_1h: Sequence[KlineBar]) -> List[KlineBar]:
    """Aggregates 1H klines into aligned 4H UTC klines."""
    if not bars_1h:
        return []
    buckets: dict[int, List[KlineBar]] = {}
    four_hours_ms = 4 * 3600 * 1000
    for b in bars_1h:
        b_key = (b.timestamp_ms // four_hours_ms) * four_hours_ms
        buckets.setdefault(b_key, []).append(b)

    result: List[KlineBar] = []
    for b_key in sorted(buckets.keys()):
        group = buckets[b_key]
        result.append(
            KlineBar(
                timestamp_ms=b_key,
                open=group[0].open,
                high=max(x.high for x in group),
                low=min(x.low for x in group),
                close=group[-1].close,
                volume=sum(x.volume for x in group),
                taker_buy_volume=sum(x.taker_buy_volume for x in group),
            )
        )
    return result


def compute_atr(bars: Sequence[KlineBar], period: int = 14) -> float:
    """Computes Wilder's Average True Range (ATR) over `period` bars."""
    if not bars:
        return 0.0
    if len(bars) == 1:
        return max(1.0, bars[0].high - bars[0].low)

    trs: List[float] = []
    for i in range(1, len(bars)):
        cur = bars[i]
        prev_close = bars[i - 1].close
        tr = max(
            cur.high - cur.low,
            abs(cur.high - prev_close),
            abs(cur.low - prev_close),
        )
        trs.append(tr)

    if len(trs) <= period:
        return float(np.mean(trs))

    # Wilder smoothing
    atr = float(np.mean(trs[:period]))
    for tr in trs[period:]:
        atr = (atr * (period - 1) + tr) / period
    return atr
