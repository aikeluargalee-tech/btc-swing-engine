"""Multi-horizon Spot vs. Perpetual CVD normalization, Z-score divergence, and Absorption math."""

from typing import List, Sequence, Tuple

import numpy as np

from config.settings import EngineConfig
from core.models import (
    DerivativesSnapshot,
    FlowSnapshot,
    HorizonFlowMetrics,
    KlineBar,
    OIPositioningQuadrant,
)
from core.state_store import StateStore
from .volume_profile import compute_atr


def _compute_window_metrics(
    window_label: str,
    spot_bars: Sequence[KlineBar],
    perp_bars: Sequence[KlineBar],
    window_size: int,
    lookback_windows: int = 48,
) -> HorizonFlowMetrics:
    """Computes normalized delta ratio, Z-scores, divergence, and Effort-vs-Result absorption."""
    metrics = HorizonFlowMetrics(window_label=window_label)
    if len(spot_bars) < window_size or len(perp_bars) < window_size:
        return metrics

    # Current window slices
    cur_spot = spot_bars[-window_size:]
    cur_perp = perp_bars[-window_size:]

    spot_vol = sum(b.volume for b in cur_spot)
    spot_delta = sum(b.delta for b in cur_spot)
    spot_ratio = (spot_delta / spot_vol) if spot_vol > 0 else 0.0

    perp_vol = sum(b.volume for b in cur_perp)
    perp_delta = sum(b.delta for b in cur_perp)
    perp_ratio = (perp_delta / perp_vol) if perp_vol > 0 else 0.0

    open_p = cur_spot[0].open
    close_p = cur_spot[-1].close
    price_chg_pct = ((close_p - open_p) / open_p) * 100.0 if open_p > 0 else 0.0

    # Trailing rolling windows for Z-score standardization
    spot_ratios: List[float] = []
    perp_ratios: List[float] = []
    perp_sell_vols: List[float] = []

    max_start_spot = len(spot_bars) - window_size
    max_start_perp = len(perp_bars) - window_size
    steps = min(lookback_windows, max_start_spot, max_start_perp)

    for k in range(steps + 1):
        s_slice = spot_bars[max_start_spot - k : len(spot_bars) - k]
        p_slice = perp_bars[max_start_perp - k : len(perp_bars) - k]
        sv = sum(b.volume for b in s_slice)
        pv = sum(b.volume for b in p_slice)
        if sv > 0:
            spot_ratios.append(sum(b.delta for b in s_slice) / sv)
        if pv > 0:
            p_del = sum(b.delta for b in p_slice)
            perp_ratios.append(p_del / pv)
            perp_sell_vols.append(max(0.0, -p_del))

    spot_z = 0.0
    if len(spot_ratios) >= 5:
        s_arr = np.array(spot_ratios, dtype=float)
        s_std = float(np.std(s_arr))
        if s_std > 1e-6:
            spot_z = (spot_ratio - float(np.mean(s_arr))) / s_std

    perp_z = 0.0
    if len(perp_ratios) >= 5:
        p_arr = np.array(perp_ratios, dtype=float)
        p_std = float(np.std(p_arr))
        if p_std > 1e-6:
            perp_z = (perp_ratio - float(np.mean(p_arr))) / p_std

    # Effort-vs-Result Passive Absorption Index:
    # High when aggressive perp net selling occurs with compressed downward price displacement
    atr_bar = compute_atr(spot_bars[-min(len(spot_bars), 30) :], period=14)
    window_atr = max(atr_bar * np.sqrt(window_size), 1.0)
    price_disp_norm = max(abs(close_p - open_p) / window_atr, 0.15)

    mean_perp_vol = float(np.mean([sum(b.volume for b in perp_bars[max_start_perp - k : len(perp_bars) - k]) for k in range(max(1, steps))]))
    mean_perp_vol = max(mean_perp_vol, 1.0)
    perp_net_sell_effort = max(0.0, -perp_delta) / (0.10 * mean_perp_vol)
    absorption_idx = float(perp_net_sell_effort / price_disp_norm)

    metrics.spot_delta_btc = float(spot_delta)
    metrics.spot_volume_btc = float(spot_vol)
    metrics.spot_delta_ratio = float(spot_ratio)
    metrics.spot_zscore = float(spot_z)
    metrics.perp_delta_btc = float(perp_delta)
    metrics.perp_volume_btc = float(perp_vol)
    metrics.perp_delta_ratio = float(perp_ratio)
    metrics.perp_zscore = float(perp_z)
    metrics.flow_divergence_z = float(spot_z - perp_z)
    metrics.absorption_index = float(absorption_idx)
    metrics.price_change_pct = float(price_chg_pct)
    return metrics


def _detect_pivot_divergences(
    spot_bars_1h: Sequence[KlineBar],
    perp_bars_1h: Sequence[KlineBar],
    lookback_bars: int = 36,
) -> Tuple[bool, bool]:
    """Detects (bullish_pivot_divergence, absorption_divergence) over recent 1H swing lows.

    1. Classic Bullish Divergence: Price makes a Lower Low (or equal low within 0.15%),
       while Cumulative Spot Delta prints a Higher Low.
    2. Passive Absorption Divergence: Price makes a Higher Low (or holds support),
       while Cumulative Perp Delta makes a significantly Lower Low and Spot CVD holds/rises.
    """
    n = min(len(spot_bars_1h), len(perp_bars_1h), lookback_bars)
    if n < 10:
        return False, False

    s_slice = list(spot_bars_1h[-n:])
    p_slice = list(perp_bars_1h[-n:])

    spot_cum = np.cumsum([b.delta for b in s_slice])
    perp_cum = np.cumsum([b.delta for b in p_slice])
    lows = np.array([b.low for b in s_slice], dtype=float)

    # Split window into earlier half (pivot 1) and recent 6 hours (pivot 2)
    split_idx = max(4, n - 6)
    p1_idx = int(np.argmin(lows[:split_idx]))
    p2_idx = split_idx + int(np.argmin(lows[split_idx:]))

    price_1, price_2 = float(lows[p1_idx]), float(lows[p2_idx])
    spot_cvd_1, spot_cvd_2 = float(spot_cum[p1_idx]), float(spot_cum[p2_idx])
    perp_cvd_1, perp_cvd_2 = float(perp_cum[p1_idx]), float(perp_cum[p2_idx])

    # Classic Bullish Divergence: Lower Low in price, Higher Low in Spot CVD
    classic_bull_div = (price_2 <= price_1 * 1.001) and (spot_cvd_2 > spot_cvd_1)

    # Absorption Divergence: Price holds/higher low while Perp CVD dumps lower and Spot CVD rises/holds
    absorption_div = (
        (price_2 >= price_1 * 0.998)
        and (perp_cvd_2 < perp_cvd_1)
        and (spot_cvd_2 >= spot_cvd_1)
    )

    return bool(classic_bull_div), bool(absorption_div)


def compute_flow_snapshot(config: EngineConfig, store: StateStore) -> FlowSnapshot:
    """Computes complete multi-horizon (15m, 1H, 4H, 24H) Spot vs. Perp order flow snapshot."""
    spot_15m = list(store.spot_klines_15m)
    perp_15m = list(store.perp_klines_15m)
    spot_1h = list(store.spot_klines_1h)
    perp_1h = list(store.perp_klines_1h)

    w_15m = _compute_window_metrics("15m", spot_15m, perp_15m, window_size=1, lookback_windows=config.cvd_zscore_lookback)
    w_1h = _compute_window_metrics("1H", spot_15m, perp_15m, window_size=4, lookback_windows=config.cvd_zscore_lookback)
    w_4h = _compute_window_metrics("4H", spot_1h, perp_1h, window_size=4, lookback_windows=config.cvd_zscore_lookback)
    w_24h = _compute_window_metrics("24H", spot_1h, perp_1h, window_size=24, lookback_windows=28)

    bull_div, abs_div = _detect_pivot_divergences(spot_1h, perp_1h)

    # Classify overall Flow Signature using 1H & 4H blended metrics
    spot_d = w_1h.spot_delta_btc
    perp_d = w_1h.perp_delta_btc
    div_z = w_1h.flow_divergence_z

    if (spot_d >= 0 and perp_d < 0) or div_z >= config.divergence_z_spread_threshold:
        signature = "BULLISH PASSIVE ABSORPTION (Spot Buying / Perp Shorting)"
    elif (spot_d <= 0 and perp_d > 0) or div_z <= config.leveraged_trap_z_spread:
        signature = "BEARISH LEVERAGE CHASE (Perp Buying / Spot Selling)"
    elif spot_d > 0 and perp_d > 0:
        signature = "AGGRESSIVE AGGREGATE DEMAND (Spot + Perp Aligned)"
    elif spot_d < 0 and perp_d < 0:
        signature = "AGGRESSIVE AGGREGATE SELLING (Spot + Perp Aligned)"
    else:
        signature = "BALANCED / NEUTRAL ROTATION"

    return FlowSnapshot(
        session_spot_cvd=store.session_spot_cvd,
        session_perp_cvd=store.session_perp_cvd,
        utc_day_spot_cvd=store.utc_day_spot_cvd,
        utc_day_perp_cvd=store.utc_day_perp_cvd,
        spot_trade_count=store.spot_trade_count,
        perp_trade_count=store.perp_trade_count,
        w_15m=w_15m,
        w_1h=w_1h,
        w_4h=w_4h,
        w_24h=w_24h,
        bullish_pivot_divergence=bull_div,
        absorption_divergence=abs_div,
        flow_signature=signature,
    )


def compute_derivatives_snapshot(
    config: EngineConfig,
    store: StateStore,
    flow: FlowSnapshot,
) -> DerivativesSnapshot:
    """Computes Open Interest 4-Quadrant state, Coinbase Premium Z-score, and Funding health."""
    oi_15m = store.get_oi_change_pct(900.0)
    oi_1h = store.get_oi_change_pct(3600.0)
    oi_4h = store.get_oi_change_pct(14400.0)

    price_chg_1h = flow.w_1h.price_change_pct

    # 4-Quadrant Price vs. OI Classification
    if price_chg_1h < -0.15 and (oi_1h < -0.35 or oi_4h <= config.oi_flush_pct_4h):
        quadrant = OIPositioningQuadrant.LONG_LIQUIDATION_FLUSH
    elif price_chg_1h <= 0.10 and oi_1h >= config.oi_short_build_pct_1h:
        quadrant = OIPositioningQuadrant.AGGRESSIVE_SHORT_BUILD
    elif price_chg_1h > 0.15 and oi_1h > 0.25:
        quadrant = OIPositioningQuadrant.LEVERAGED_LONG_EXPANSION
    elif price_chg_1h > 0.15 and oi_1h < -0.20:
        quadrant = OIPositioningQuadrant.SHORT_COVERING_BOUNCE
    else:
        quadrant = OIPositioningQuadrant.NEUTRAL_CHURN

    prem_usd, prem_pct, prem_z = store.get_cpi_metrics()
    perp_basis = (
        store.binance_perp_price - store.binance_spot_price
        if (store.binance_perp_price > 0 and store.binance_spot_price > 0)
        else 0.0
    )

    return DerivativesSnapshot(
        open_interest_btc=store.open_interest_btc,
        open_interest_usd=store.open_interest_usd,
        oi_change_15m_pct=oi_15m,
        oi_change_1h_pct=oi_1h,
        oi_change_4h_pct=oi_4h,
        oi_regime_quadrant=quadrant,
        funding_rate_pct=store.funding_rate_pct,
        taker_long_short_ratio_5m=store.taker_long_short_ratio_5m,
        perp_5m_delta_btc=store.perp_5m_delta_btc,
        coinbase_price=store.coinbase_spot_price,
        binance_spot_price=store.binance_spot_price,
        binance_perp_price=store.binance_perp_price,
        coinbase_premium_usd=prem_usd,
        coinbase_premium_pct=prem_pct,
        coinbase_premium_zscore=prem_z,
        perp_basis_usd=perp_basis,
        perp_source=store.perp_source,
    )
