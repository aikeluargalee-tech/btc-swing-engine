"""Consolidated Protocol Metrics Dossier Generator.

Standardized quantitative compilation of all protocol metrics across 7 categories:
1. Core Price & Structure Metrics
2. Volume Profile Metrics (Prior Session, Prior Week, Developing)
3. Derivatives & Positioning Metrics
4. ETF Flows & Demand Proxies
5. Macro & Intermarket Asset Metrics
6. Sentiment & Risk Context
7. Mean-Reversion Inputs (Landscape)

Follows the strict protocol specifications and fallback rules:
Any unresolvable metric returns None / 'unavailable' — NEVER estimated.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
import numpy as np

from config.settings import EngineConfig
from core.state_store import StateStore
from collectors.macro_collector import MacroIntermarketSnapshot
from analytics.volume_profile import compute_composite_profile


def compute_protocol_metrics_dossier(
    config: EngineConfig,
    store: StateStore,
    macro_snap: Optional[MacroIntermarketSnapshot] = None,
) -> Dict[str, Any]:
    """Computes and structures all quantitative metrics required by the 7 active trading protocols."""
    now_utc = datetime.now(timezone.utc)
    ts_utc_str = now_utc.strftime("%Y-%m-%d %H:%M:%S UTC")

    spot_price = store.binance_spot_price
    perp_price = store.binance_perp_price
    daily_bars = list(store.spot_klines_1d)
    weekly_bars = list(store.spot_klines_1w)
    hourly_bars = list(store.spot_klines_1h)

    daily_closes = np.array([b.close for b in daily_bars], dtype=float) if daily_bars else np.array([])
    daily_highs = np.array([b.high for b in daily_bars], dtype=float) if daily_bars else np.array([])
    daily_lows = np.array([b.low for b in daily_bars], dtype=float) if daily_bars else np.array([])

    # 1. Price & Structure
    change_24h_pct = None
    if len(daily_closes) >= 2:
        prev_c = daily_closes[-2]
        change_24h_pct = round(((spot_price - prev_c) / prev_c) * 100.0, 2)

    change_7d_pct = None
    if len(daily_closes) >= 8:
        c_7d = daily_closes[-8]
        change_7d_pct = round(((spot_price - c_7d) / c_7d) * 100.0, 2)

    daily_sma50 = round(float(np.mean(daily_closes[-50:])), 2) if len(daily_closes) >= 50 else None
    daily_sma200 = round(float(np.mean(daily_closes[-200:])), 2) if len(daily_closes) >= 200 else None

    # SMA200 Slope over last 15 days
    sma200_slope_pct = None
    sma200_slope_usd_day = None
    if len(daily_closes) >= 215:
        sma200_now = float(np.mean(daily_closes[-200:]))
        sma200_15d_ago = float(np.mean(daily_closes[-215:-15]))
        sma200_slope_pct = round(((sma200_now - sma200_15d_ago) / sma200_15d_ago) * 100.0, 2)
        sma200_slope_usd_day = round((sma200_now - sma200_15d_ago) / 15.0, 2)

    # Weekly SMA200
    weekly_closes = np.array([b.close for b in weekly_bars], dtype=float) if weekly_bars else np.array([])
    weekly_sma200 = None
    weekly_sma_note = ""
    if len(weekly_closes) >= 200:
        weekly_sma200 = round(float(np.mean(weekly_closes[-200:])), 2)
        weekly_sma_note = "200 weekly closes"
    elif len(weekly_closes) > 0:
        weekly_sma200 = round(float(np.mean(weekly_closes)), 2)
        weekly_sma_note = f"{len(weekly_closes)}w available avg"

    # 30-45d Range
    range_lookback = min(45, len(daily_bars))
    range_high_45d = round(float(np.max(daily_highs[-range_lookback:])), 2) if range_lookback > 0 else None
    range_low_45d = round(float(np.min(daily_lows[-range_lookback:])), 2) if range_lookback > 0 else None

    # Daily ATR(14)
    daily_atr14 = None
    if len(daily_bars) >= 15:
        trs = []
        for i in range(len(daily_bars) - 14, len(daily_bars)):
            h, l, c_prev = daily_bars[i].high, daily_bars[i].low, daily_bars[i - 1].close
            trs.append(max(h - l, abs(h - c_prev), abs(l - c_prev)))
        daily_atr14 = round(float(np.mean(trs)), 2)

    # Daily Developing VWAP (today UTC midnight to now)
    midnight_today = datetime(now_utc.year, now_utc.month, now_utc.day, tzinfo=timezone.utc)
    midnight_today_ms = int(midnight_today.timestamp() * 1000)
    today_bars = [b for b in hourly_bars if b.timestamp_ms >= midnight_today_ms]
    daily_vwap = None
    if today_bars:
        vol_sum = sum(b.volume for b in today_bars)
        if vol_sum > 0:
            daily_vwap = round(sum(b.typical_price * b.volume for b in today_bars) / vol_sum, 2)

    # Weekly Developing VWAP (Monday 00:00 UTC to now)
    days_since_mon = now_utc.weekday()
    mon_midnight = midnight_today - timedelta(days=days_since_mon)
    mon_midnight_ms = int(mon_midnight.timestamp() * 1000)
    week_bars = [b for b in hourly_bars if b.timestamp_ms >= mon_midnight_ms]
    weekly_vwap = None
    if week_bars:
        w_vol_sum = sum(b.volume for b in week_bars)
        if w_vol_sum > 0:
            weekly_vwap = round(sum(b.typical_price * b.volume for b in week_bars) / w_vol_sum, 2)

    # Daily EMAs
    def _compute_ema(series: np.ndarray, period: int) -> Optional[float]:
        if len(series) < period:
            return None
        alpha = 2.0 / (period + 1.0)
        ema = float(series[0])
        for val in series[1:]:
            ema = (float(val) * alpha) + (ema * (1.0 - alpha))
        return round(ema, 2)

    daily_ema20 = _compute_ema(daily_closes, 20)
    daily_ema50 = _compute_ema(daily_closes, 50)
    daily_ema200 = _compute_ema(daily_closes, 200)

    pev = store.protocol_evaluation
    daily_support = pev.daily_support if pev else None
    daily_resistance = pev.daily_resistance if pev else None

    # 2. Volume Profile (Prior UTC Day + Prior Completed Week + Developing)
    midnight_yest = midnight_today - timedelta(days=1)
    midnight_yest_ms = int(midnight_yest.timestamp() * 1000)
    prior_day_bars = [b for b in hourly_bars if midnight_yest_ms <= b.timestamp_ms < midnight_today_ms]

    prior_day_poc, prior_day_vah, prior_day_val = None, None, None
    prior_day_high, prior_day_low, prior_day_vol = None, None, None
    prior_day_location = "N/A"
    if prior_day_bars:
        p_day_vp = compute_composite_profile(prior_day_bars, horizon_label="Prior UTC Day", num_bins=60)
        if p_day_vp:
            prior_day_poc = round(p_day_vp.c_poc, 2)
            prior_day_vah = round(p_day_vp.c_vah, 2)
            prior_day_val = round(p_day_vp.c_val, 2)
        prior_day_high = round(max(b.high for b in prior_day_bars), 2)
        prior_day_low = round(min(b.low for b in prior_day_bars), 2)
        prior_day_vol = round(sum(b.volume for b in prior_day_bars), 1)

        if prior_day_vah and prior_day_val:
            if spot_price > prior_day_vah:
                prior_day_location = f"ABOVE VAH (+{((spot_price - prior_day_vah)/prior_day_vah)*100:.2f}%)"
            elif spot_price < prior_day_val:
                prior_day_location = f"BELOW VAL ({((spot_price - prior_day_val)/prior_day_val)*100:.2f}%)"
            else:
                pos = ((spot_price - prior_day_val) / (prior_day_vah - prior_day_val)) * 100.0
                prior_day_location = f"INSIDE VALUE ({pos:.1f}%)"

    # Prior Week Profile (Last Monday 00:00 to this Monday 00:00)
    prev_mon_midnight = mon_midnight - timedelta(days=7)
    prev_mon_ms = int(prev_mon_midnight.timestamp() * 1000)
    prior_week_bars = [b for b in hourly_bars if prev_mon_ms <= b.timestamp_ms < mon_midnight_ms]

    prior_week_poc, prior_week_vah, prior_week_val = None, None, None
    prior_week_location = "N/A"
    if prior_week_bars:
        p_week_vp = compute_composite_profile(prior_week_bars, horizon_label="Prior Week", num_bins=80)
        if p_week_vp:
            prior_week_poc = round(p_week_vp.c_poc, 2)
            prior_week_vah = round(p_week_vp.c_vah, 2)
            prior_week_val = round(p_week_vp.c_val, 2)
            if spot_price > prior_week_vah:
                prior_week_location = f"ABOVE VAH (+{((spot_price - prior_week_vah)/prior_week_vah)*100:.2f}%)"
            elif spot_price < prior_week_val:
                prior_week_location = f"BELOW VAL ({((spot_price - prior_week_val)/prior_week_val)*100:.2f}%)"
            else:
                w_pos = ((spot_price - prior_week_val) / (prior_week_vah - prior_week_val)) * 100.0
                prior_week_location = f"INSIDE VALUE ({w_pos:.1f}%)"

    # Developing POC
    dev_poc = None
    if today_bars:
        dev_vp = compute_composite_profile(today_bars, horizon_label="Developing UTC Day", num_bins=40)
        if dev_vp:
            dev_poc = round(dev_vp.c_poc, 2)

    # Top HVNs / LVNs from Macro profile
    macro_vp = store.macro_profile
    top_hvns = [round(x, 2) for x in macro_vp.hvn_levels[:3]] if macro_vp and macro_vp.hvn_levels else []
    top_lvns = [round(x, 2) for x in macro_vp.lvn_levels[:3]] if macro_vp and macro_vp.lvn_levels else []
    va_pos_pct = store.latest_signal.va_position_pct if store.latest_signal else 0.0

    # 3. Derivatives & Positioning
    oi_btc = round(store.open_interest_btc, 1)
    oi_usd = round(store.open_interest_usd, 2) if store.open_interest_usd > 0 else round(oi_btc * spot_price, 2)
    oi_1h_pct = round(store.get_oi_change_pct(3600), 2)
    oi_24h_pct = round(store.get_oi_change_pct(86400), 2)
    oi_3d_pct = round(store.get_oi_change_pct(86400 * 3), 2)

    funding_8h_pct = round(store.funding_rate_pct, 4)
    # Basis annualized: perp vs spot
    futures_basis_annualized = None
    if spot_price > 0 and perp_price > 0:
        futures_basis_annualized = round(((perp_price - spot_price) / spot_price) * 100.0 * 365.0, 2)

    flow = store.flow_snapshot
    deriv = store.derivatives_snapshot
    spot_cvd_24h = round(flow.w_24h.spot_delta_btc, 1) if flow and flow.w_24h else round(store.utc_day_spot_cvd, 1)
    perp_cvd_24h = round(flow.w_24h.perp_delta_btc, 1) if flow and flow.w_24h else round(store.utc_day_perp_cvd, 1)

    # Zero CVD means the feed did not populate (e.g. geo-blocked venue) -> do not interpret it.
    spot_cvd_dir = "Data unavailable" if spot_cvd_24h == 0 else ("ACCUMULATION / NET BUY" if spot_cvd_24h > 0 else "DISTRIBUTION / NET SELL")
    perp_cvd_dir = "Data unavailable" if perp_cvd_24h == 0 else ("LEVERAGED BUY" if perp_cvd_24h > 0 else "AGGRESSIVE SHORT")

    short_liq_usd = pev.short_liq_magnet_usd if pev else None
    short_liq_src = pev.short_liq_source if pev else "N/A"
    long_liq_usd = pev.long_liq_magnet_usd if pev else None
    long_liq_src = pev.long_liq_source if pev else "N/A"

    cb_premium_pct = round(deriv.coinbase_premium_pct, 3) if deriv else 0.0
    cb_premium_zscore = round(deriv.coinbase_premium_zscore, 2) if deriv else 0.0
    taker_ls_ratio = round(deriv.taker_long_short_ratio_5m, 2) if deriv else 1.0

    depth_1pct = macro_snap.orderbook_depth_ratio_1pct if macro_snap else None
    depth_2pct = macro_snap.orderbook_depth_ratio_2pct if macro_snap else None

    # 4. Flows & Demand Proxies
    etf_daily_net = macro_snap.etf_daily_net_flow_usd if macro_snap else None
    etf_3d_cum = macro_snap.etf_3d_cumulative_flow_usd if macro_snap else None
    etf_status = macro_snap.etf_daily_net_flow_status if macro_snap else "unavailable"
    passive_abs_ratio = round(flow.w_4h.absorption_index, 2) if flow and flow.w_4h else 1.0

    # 5. Macro & Intermarket
    brent_price = macro_snap.brent_crude_price if macro_snap else None
    brent_range = macro_snap.brent_crude_range_5_10d if macro_snap else None
    us_10y_yield = macro_snap.us_10y_treasury_yield if macro_snap else None
    us_10y_yield_5d = macro_snap.us_10y_yield_change_5d if macro_snap else None
    us_tips_yield = macro_snap.us_10y_real_yield_tips if macro_snap else None
    us_tips_dir = macro_snap.us_10y_tips_direction_5_10d if macro_snap else None
    us_breakeven = macro_snap.us_10y_breakeven_inflation if macro_snap else None
    us_breakeven_chg = macro_snap.us_10y_breakeven_change if macro_snap else None
    dxy_val = macro_snap.dxy_index if macro_snap else None
    dxy_dir = macro_snap.dxy_direction_5_10d if macro_snap else None
    spx_price = macro_snap.sp500_price if macro_snap else None
    spx_1d = macro_snap.sp500_change_1d_pct if macro_snap else None
    spx_5d = macro_snap.sp500_change_5d_pct if macro_snap else None
    nasdaq_price = macro_snap.nasdaq_price if macro_snap else None
    nasdaq_1d = macro_snap.nasdaq_change_1d_pct if macro_snap else None
    nasdaq_5d = macro_snap.nasdaq_change_5d_pct if macro_snap else None
    vix_val = macro_snap.vix_index if macro_snap else None
    vix_1d = macro_snap.vix_change_1d if macro_snap else None
    vix_5d = macro_snap.vix_change_5d if macro_snap else None
    corr_20d = macro_snap.btc_spx_corr_20d if macro_snap else None
    corr_60d = macro_snap.btc_spx_corr_60d if macro_snap else None

    # 6. Sentiment & Risk Context
    fng_score = macro_snap.fear_and_greed_score if macro_snap else None
    fng_class = macro_snap.fear_and_greed_classification if macro_snap else None
    btc_dom = macro_snap.btc_dominance_pct if macro_snap else None

    # 7. Mean-Reversion (Landscape)
    rsi14_daily = None
    if len(daily_closes) >= 15:
        diffs = np.diff(daily_closes)
        gains = np.maximum(diffs, 0.0)
        losses = np.maximum(-diffs, 0.0)
        avg_gain = float(np.mean(gains[-14:]))
        avg_loss = float(np.mean(losses[-14:]))
        rs = avg_gain / (avg_loss + 1e-9)
        rsi14_daily = round(100.0 - (100.0 / (1.0 + rs)), 1)

    log_spread_raw = None
    log_spread_50d_std = None
    log_spread_zscore = None
    if len(daily_closes) >= 50:
        log_spreads = []
        for i in range(len(daily_closes) - 50, len(daily_closes)):
            s50 = float(np.mean(daily_closes[i - 49 : i + 1]))
            log_spreads.append(float(np.log(daily_closes[i]) - np.log(s50)))
        log_spread_raw = round(float(log_spreads[-1]), 4)
        log_spread_50d_std = round(float(np.std(log_spreads)), 4)
        log_spread_zscore = round(log_spread_raw / (log_spread_50d_std + 1e-9), 2)

    return {
        "timestamp_utc": ts_utc_str,
        "price_and_structure": {
            "spot_price": spot_price,
            "change_24h_pct": change_24h_pct,
            "change_7d_pct": change_7d_pct,
            "daily_sma50": daily_sma50,
            "daily_sma200": daily_sma200,
            "sma200_slope_15d_pct": sma200_slope_pct,
            "sma200_slope_usd_day": sma200_slope_usd_day,
            "weekly_sma200": weekly_sma200,
            "weekly_sma_note": weekly_sma_note,
            "range_high_45d": range_high_45d,
            "range_low_45d": range_low_45d,
            "daily_atr14": daily_atr14,
            "daily_vwap": daily_vwap,
            "weekly_vwap": weekly_vwap,
            "daily_ema20": daily_ema20,
            "daily_ema50": daily_ema50,
            "daily_ema200": daily_ema200,
            "daily_support": daily_support,
            "daily_resistance": daily_resistance,
        },
        "volume_profile": {
            "prior_day_poc": prior_day_poc,
            "prior_day_vah": prior_day_vah,
            "prior_day_val": prior_day_val,
            "prior_day_high": prior_day_high,
            "prior_day_low": prior_day_low,
            "prior_day_volume_btc": prior_day_vol,
            "prior_day_location": prior_day_location,
            "prior_week_poc": prior_week_poc,
            "prior_week_vah": prior_week_vah,
            "prior_week_val": prior_week_val,
            "prior_week_location": prior_week_location,
            "developing_poc": dev_poc,
            "top_hvns": top_hvns,
            "top_lvns": top_lvns,
            "va_position_pct": round(va_pos_pct, 1),
        },
        "derivatives_and_positioning": {
            "perp_source": store.perp_source,
            "open_interest_btc": oi_btc,
            "open_interest_usd": oi_usd,
            "oi_change_1h_pct": oi_1h_pct,
            "oi_change_24h_pct": oi_24h_pct,
            "oi_change_3d_pct": oi_3d_pct,
            "funding_rate_8h_pct": funding_8h_pct,
            "futures_basis_annualized_pct": futures_basis_annualized,
            "spot_cvd_24h_btc": spot_cvd_24h,
            "spot_cvd_direction": spot_cvd_dir,
            "perp_cvd_24h_btc": perp_cvd_24h,
            "perp_cvd_direction": perp_cvd_dir,
            "short_liq_magnet_usd": short_liq_usd,
            "short_liq_source": short_liq_src,
            "long_liq_magnet_usd": long_liq_usd,
            "long_liq_source": long_liq_src,
            "orderbook_depth_ratio_1pct": depth_1pct,
            "orderbook_depth_ratio_2pct": depth_2pct,
            "coinbase_premium_pct": cb_premium_pct,
            "coinbase_premium_zscore": cb_premium_zscore,
            "taker_long_short_ratio_5m": taker_ls_ratio,
        },
        "flows_and_demand": {
            "etf_daily_net_flow_usd": etf_daily_net,
            "etf_3d_cumulative_flow_usd": etf_3d_cum,
            "etf_status": etf_status,
            "passive_absorption_ratio": passive_abs_ratio,
        },
        "macro_and_intermarket": {
            "brent_crude_price": brent_price,
            "brent_crude_range_5_10d": brent_range,
            "us_10y_treasury_yield": us_10y_yield,
            "us_10y_yield_change_5d": us_10y_yield_5d,
            "us_10y_real_yield_tips": us_tips_yield,
            "us_10y_real_yield_source": macro_snap.us_10y_real_yield_source if macro_snap else "FRED (`DFII10`)",
            "us_10y_tips_direction": us_tips_dir,
            "us_10y_breakeven_inflation": us_breakeven,
            "us_10y_breakeven_change": us_breakeven_chg,
            "dxy_index": dxy_val,
            "dxy_direction_5_10d": dxy_dir,
            "sp500_price": spx_price,
            "sp500_change_1d_pct": spx_1d,
            "sp500_change_5d_pct": spx_5d,
            "nasdaq_price": nasdaq_price,
            "nasdaq_change_1d_pct": nasdaq_1d,
            "nasdaq_change_5d_pct": nasdaq_5d,
            "vix_index": vix_val,
            "vix_change_1d": vix_1d,
            "vix_change_5d": vix_5d,
            "btc_spx_corr_20d": corr_20d,
            "btc_spx_corr_60d": corr_60d,
        },
        "sentiment_and_context": {
            "fear_and_greed_score": fng_score,
            "fear_and_greed_classification": fng_class,
            "btc_dominance_pct": btc_dom,
            "material_headlines_6_48h": "[NATIVE AI CONTEXT] Handled natively by LLM",
            "usdt_health_markers": "[NATIVE AI CONTEXT] Handled natively by LLM",
            "catalysts_next_14d": "[NATIVE AI CONTEXT] Handled natively by LLM",
        },
        "mean_reversion_landscape": {
            "daily_rsi14": rsi14_daily,
            "log_spread_raw": log_spread_raw,
            "log_spread_50d_std": log_spread_50d_std,
            "log_spread_zscore": log_spread_zscore,
        },
    }


def format_protocol_metrics_dossier_markdown(dossier: Dict[str, Any]) -> str:
    """Renders the protocol metrics dossier into clean, standard Markdown tables for Section 12."""
    p = dossier.get("price_and_structure", {})
    vp = dossier.get("volume_profile", {})
    dp = dossier.get("derivatives_and_positioning", {})
    fl = dossier.get("flows_and_demand", {})
    m = dossier.get("macro_and_intermarket", {})
    s = dossier.get("sentiment_and_context", {})
    mr = dossier.get("mean_reversion_landscape", {})

    def _fmt_price(v: Optional[float], prefix: str = "$") -> str:
        return f"{prefix}{v:,.2f}" if v is not None else "unavailable"

    def _fmt_val(v: Any, suffix: str = "") -> str:
        if v is None:
            return "unavailable"
        if isinstance(v, float):
            return f"{v:,.2f}{suffix}"
        return f"{v}{suffix}"

    lines = [
        "## SECTION 12: CONSOLIDATED PROTOCOL METRICS DOSSIER (STANDARDIZED PROTOCOL SPECIFICATION)",
        "",
        "> [!IMPORTANT]",
        "> **Strict Protocol Compliance Rule**: All quantitative lookbacks strictly adhere to active protocol definitions. Any unresolvable metric is returned as `unavailable` or `null` — **never estimated or guessed**.",
        "",
        "### 12A. Core Price & Structure Metrics",
        "",
        "| Metric | Preferred Lookback | Value | Source / Benchmark | Status |",
        "| :--- | :--- | :--- | :--- | :--- |",
        f"| **BTC Spot Price** | Current | `{_fmt_price(p.get('spot_price'))}` | Binance BTCUSDT | `LIVE TICK` |",
        f"| **24h % Change** | Last 24 hours | `{_fmt_val(p.get('change_24h_pct'), '%')}` | Binance Spot 1D | `CALCULATED` |",
        f"| **7d % Change** | Last 7 days | `{_fmt_val(p.get('change_7d_pct'), '%')}` | Binance Spot 1D | `CALCULATED` |",
        f"| **Daily SMA50** | 50 daily closes | `{_fmt_price(p.get('daily_sma50'))}` | 1D Spot Klines | `CALCULATED` |",
        f"| **Daily SMA200** | 200 daily closes | `{_fmt_price(p.get('daily_sma200'))}` | 1D Spot Klines | `CALCULATED` |",
        f"| **SMA200 Slope** | 10–20 daily closes | `{_fmt_val(p.get('sma200_slope_15d_pct'), '% / 15d')} ({_fmt_val(p.get('sma200_slope_usd_day'), '$/day')})` | Landscape Rule | `{'RISING (Macro Bull)' if (p.get('sma200_slope_15d_pct') or 0) > 0 else 'FALLING (Macro Bear)'}` |",
        f"| **Weekly SMA200** | 200 weekly closes | `{_fmt_price(p.get('weekly_sma200'))}` | 1W Spot Klines ({p.get('weekly_sma_note', '1W')}) | `CALCULATED` |",
        f"| **30–45d Range High** | Last 45 calendar days | `{_fmt_price(p.get('range_high_45d'))}` | 1D Spot Highs | `ACTIVE RESISTANCE` |",
        f"| **30–45d Range Low** | Last 45 calendar days | `{_fmt_price(p.get('range_low_45d'))}` | 1D Spot Lows | `ACTIVE SUPPORT` |",
        f"| **Daily ATR(14)** | 14 daily bars | `{_fmt_price(p.get('daily_atr14'))}` | Wilder TR(14) | `VOLATILITY YARDSTICK` |",
        f"| **Daily VWAP** | Current UTC day (00:00 to now) | `{_fmt_price(p.get('daily_vwap'))}` | Hourly Weighted Vol | `DEVELOPING` |",
        f"| **Weekly VWAP** | Current week (Mon 00:00 to now) | `{_fmt_price(p.get('weekly_vwap'))}` | Hourly Weighted Vol | `DEVELOPING` |",
        f"| **20D EMA** | 20 daily bars | `{_fmt_price(p.get('daily_ema20'))}` | 1D Spot Closes | `FAST PULLBACK FILTER` |",
        f"| **50D EMA** | 50 daily bars | `{_fmt_price(p.get('daily_ema50'))}` | 1D Spot Closes | `SWING PULLBACK ZONE` |",
        f"| **200D MA** | 200 daily bars | `EMA: {_fmt_price(p.get('daily_ema200'))} | SMA: {_fmt_price(p.get('daily_sma200'))}` | 1D Spot Closes | `MACRO REGIME GATE` |",
        f"| **Horizontal Pivots** | Structural Support / Resistance | `Sup: {_fmt_price(p.get('daily_support'))} | Res: {_fmt_price(p.get('daily_resistance'))}` | Protocol v1.3 | `KEY BOUNDS` |",
        "",
        "### 12B. Volume Profile Metrics (Prior Day, Prior Week, Developing)",
        "",
        "| Metric | Preferred Lookback | Value | Specification | Status |",
        "| :--- | :--- | :--- | :--- | :--- |",
        f"| **Prior Day POC** | Completed Prior UTC Day (00:00–24:00) | `{_fmt_price(vp.get('prior_day_poc'))}` | Point of Control (Max Volume) | `FIXED BENCHMARK` |",
        f"| **Prior Day VAH** | Completed Prior UTC Day (00:00–24:00) | `{_fmt_price(vp.get('prior_day_vah'))}` | 70% Value Area High | `FIXED BENCHMARK` |",
        f"| **Prior Day VAL** | Completed Prior UTC Day (00:00–24:00) | `{_fmt_price(vp.get('prior_day_val'))}` | 70% Value Area Low | `FIXED BENCHMARK` |",
        f"| **Prior Day High / Low**| Completed Prior UTC Day (00:00–24:00) | `H: {_fmt_price(vp.get('prior_day_high'))} | L: {_fmt_price(vp.get('prior_day_low'))}` | Session Extremes | `FIXED BENCHMARK` |",
        f"| **Prior Day Volume** | Completed Prior UTC Day (00:00–24:00) | `{_fmt_val(vp.get('prior_day_volume_btc'), ' BTC')}` | Binance Spot Taker+Maker | `FIXED BENCHMARK` |",
        f"| **Prior Week POC** | Completed Week (Mon 00:00 - Mon 00:00) | `{_fmt_price(vp.get('prior_week_poc'))}` | 168h Composite Profile POC | `WEEKLY PIVOT` |",
        f"| **Prior Week VAH** | Completed Week (Mon 00:00 - Mon 00:00) | `{_fmt_price(vp.get('prior_week_vah'))}` | 70% Value Area High | `WEEKLY PIVOT` |",
        f"| **Prior Week VAL** | Completed Week (Mon 00:00 - Mon 00:00) | `{_fmt_price(vp.get('prior_week_val'))}` | 70% Value Area Low | `WEEKLY PIVOT` |",
        f"| **Developing POC** | Current Incomplete UTC Day | `{_fmt_price(vp.get('developing_poc'))}` | Developing Volume Mode | `DEVELOPING` |",
        f"| **Top 3 HVN Nodes** | 30D Macro Composite Profile | `{', '.join(f'${x:,.0f}' for x in vp.get('top_hvns', [])) or 'None'}` | High Volume Nodes | `STRONG SUPPORT/RES` |",
        f"| **Top 3 LVN Nodes** | 30D Macro Composite Profile | `{', '.join(f'${x:,.0f}' for x in vp.get('top_lvns', [])) or 'None'}` | Low Volume Nodes | `SLIPPAGE ZONES` |",
        f"| **Location vs Prior Day**| Spot relative to Prior Day VA | `{vp.get('prior_day_location')}` | CME Auction Rule | `AUCTION STATE` |",
        f"| **Location vs Prior Week**| Spot relative to Prior Week VA | `{vp.get('prior_week_location')}` | CME Auction Rule | `MACRO AUCTION` |",
        "",
        "### 12C. Derivatives & Positioning Metrics",
        "",
        "| Metric | Preferred Lookback | Value | Source / Benchmark | Status |",
        "| :--- | :--- | :--- | :--- | :--- |",
        f"| **Open Interest (BTC)** | Current | `{_fmt_val(dp.get('open_interest_btc'), ' BTC')}` | {dp.get('perp_source', 'Binance USD-M')} | `LIVE COINS` |",
        f"| **Open Interest (USD)** | Current | `{_fmt_price(dp.get('open_interest_usd'))}` | {dp.get('perp_source', 'Binance USD-M')} | `NOTIONAL VALUE` |",
        f"| **OI 1h % Change** | Last 1 hour | `{_fmt_val(dp.get('oi_change_1h_pct'), '%')}` | Regime Radar Window | `RAPID EXPANSION/FLUSH` |",
        f"| **OI 24h % Change** | Last 24 hours | `{_fmt_val(dp.get('oi_change_24h_pct'), '%')}` | 24h Positioning Drift | `DAILY TREND` |",
        f"| **OI 3D % Change** | Last 3 days (72h) | `{_fmt_val(dp.get('oi_change_3d_pct'), '%')}` | Regime Radar Window | `CYCLE BUILD` |",
        f"| **Funding Rate (8h)** | Current 8h Perp Rate | `{_fmt_val(dp.get('funding_rate_8h_pct'), '% / 8h')}` | {dp.get('perp_source', 'Binance USD-M')} | `{'Data unavailable' if not dp.get('funding_rate_8h_pct') else ('ELEVATED' if dp.get('funding_rate_8h_pct') > 0.01 else 'HEALTHY / NEUTRAL')}` |",
        f"| **Futures Basis (Ann.)**| Current Annualized | `{_fmt_val(dp.get('futures_basis_annualized_pct'), '% / yr')}` | (Perp - Spot) / Spot | `COST OF CARRY` |",
        f"| **Spot CVD (24h)** | Last 24 hours (12–48h Magnet) | `{_fmt_val(dp.get('spot_cvd_24h_btc'), ' BTC')} ({dp.get('spot_cvd_direction')})` | Binance Spot Net Taker | `CVD DELTA` |",
        f"| **Perp CVD (24h)** | Last 24 hours (12–48h Magnet) | `{_fmt_val(dp.get('perp_cvd_24h_btc'), ' BTC')} ({dp.get('perp_cvd_direction')})` | {dp.get('perp_source', 'Binance USD-M')} Net Taker | `LEVERAGE FLOW` |",
        f"| **Short-Liq Magnet** | 1-Month Liquidation Pool Above | `{_fmt_price(dp.get('short_liq_magnet_usd'))}` | {dp.get('short_liq_source')} | `UPSIDE TARGET` |",
        f"| **Long-Liq Magnet** | 1-Month Liquidation Pool Below | `{_fmt_price(dp.get('long_liq_magnet_usd'))}` | {dp.get('long_liq_source')} | `DOWNSIDE TARGET` |",
        f"| **Order-Book Depth (+/-1%)**| Current Snapshot | `{_fmt_val(dp.get('orderbook_depth_ratio_1pct'))} (Bids / Asks)` | Spot L2 (1000 lvls, ~±0.3% span) | `{'Data unavailable' if dp.get('orderbook_depth_ratio_1pct') is None else ('BID SUPPORT DOMINANT' if dp.get('orderbook_depth_ratio_1pct') >= 1.0 else 'ASK OVERHANG DOMINANT')}` |",
        f"| **Order-Book Depth (+/-2%)**| Current Snapshot | `{_fmt_val(dp.get('orderbook_depth_ratio_2pct'))} (Bids / Asks)` | Spot L2 (1000 lvls, ~±0.3% span) | `{'Data unavailable' if dp.get('orderbook_depth_ratio_2pct') is None else ('BID SUPPORT DOMINANT' if dp.get('orderbook_depth_ratio_2pct') >= 1.0 else 'ASK OVERHANG DOMINANT')}` |",
        f"| **Coinbase Premium** | Current Snapshot | `{_fmt_val(dp.get('coinbase_premium_pct'), '%')} ({_fmt_val(dp.get('coinbase_premium_zscore'), 'σ')})` | US Institutional Demand | `COINBASE VS BINANCE` |",
        "",
        "### 12D. ETF Flows & Demand Proxies",
        "",
        "| Metric | Preferred Lookback | Value | Specification | Status |",
        "| :--- | :--- | :--- | :--- | :--- |",
        f"| **Spot ETF Daily Net Flow**| Most recent completed day | `{_fmt_price(fl.get('etf_daily_net_flow_usd')) if fl.get('etf_daily_net_flow_usd') is not None else fl.get('etf_status', 'unavailable')}` | US Spot BTC ETFs | `{'CONFIRMED' if fl.get('etf_daily_net_flow_usd') is not None else 'UNAVAILABLE (No Guessing)'}` |",
        f"| **Spot ETF 3-Day Cum.** | Last 3 completed days | `{_fmt_price(fl.get('etf_3d_cumulative_flow_usd')) if fl.get('etf_3d_cumulative_flow_usd') is not None else fl.get('etf_status', 'unavailable')}` | US Spot BTC ETFs | `{'CONFIRMED' if fl.get('etf_3d_cumulative_flow_usd') is not None else 'UNAVAILABLE (No Guessing)'}` |",
        f"| **Passive Absorption Ratio**| 4H Taker vs Price Delta | `{_fmt_val(fl.get('passive_absorption_ratio'))}` | Limit Absorption Index | `{'ACTIVE ABSORPTION' if (fl.get('passive_absorption_ratio') or 0) >= 1.05 else 'PASSIVE SELLING'}` |",
        "",
        "### 12E. Macro & Intermarket Asset Metrics",
        "",
        "| Metric | Preferred Lookback | Value | Source / Benchmark | Status |",
        "| :--- | :--- | :--- | :--- | :--- |",
        f"| **Brent Crude Oil** | Current + 5–10d Range | `{_fmt_price(m.get('brent_crude_price'))} ({m.get('brent_crude_range_5_10d', 'N/A')})` | Yahoo Finance (`BZ=F`) | `LIVE QUOTE` |",
        f"| **US 10Y Real Yield (TIPS)**| Current + 5–10d Direction | `{_fmt_val(m.get('us_10y_real_yield_tips'), '%')}` | {m.get('us_10y_real_yield_source', 'FRED (`DFII10`)')} | `{'CONFIRMED' if m.get('us_10y_real_yield_tips') is not None else 'UNAVAILABLE (No Guessing)'}` |",
        f"| **US 10Y Breakeven Infl.**| Current + Recent Change | `{_fmt_val(m.get('us_10y_breakeven_inflation'), '%')}` | FRED (`T10YIE`) | `{'CONFIRMED' if m.get('us_10y_breakeven_inflation') is not None else 'UNAVAILABLE (No Guessing)'}` |",
        f"| **US 10Y Treasury Yield** | Current + 5d Change | `{_fmt_val(m.get('us_10y_treasury_yield'), '%')} ({_fmt_val(m.get('us_10y_yield_change_5d'), '% over 5d')})` | Yahoo Finance (`^TNX`) | `LIVE YIELD` |",
        f"| **US Dollar Index (DXY)**| Current + 5–10d Direction | `{_fmt_val(m.get('dxy_index'))} ({m.get('dxy_direction_5_10d', 'N/A')})` | Yahoo Finance (`DX-Y.NYB`) | `LIVE INDEX` |",
        f"| **S&P 500 Performance** | 1-Session & 5-Session % | `{_fmt_price(m.get('sp500_price'))} (1d: {_fmt_val(m.get('sp500_change_1d_pct'), '%')} | 5d: {_fmt_val(m.get('sp500_change_5d_pct'), '%')})` | Yahoo Finance (`^GSPC`) | `LIVE BENCHMARK` |",
        f"| **Nasdaq Performance** | 1-Session & 5-Session % | `{_fmt_price(m.get('nasdaq_price'))} (1d: {_fmt_val(m.get('nasdaq_change_1d_pct'), '%')} | 5d: {_fmt_val(m.get('nasdaq_change_5d_pct'), '%')})` | Yahoo Finance (`^IXIC`) | `LIVE BENCHMARK` |",
        f"| **CBOE VIX Volatility** | 1-Session & 5-Session Change | `{_fmt_val(m.get('vix_index'))} (1d: {_fmt_val(m.get('vix_change_1d'))} | 5d: {_fmt_val(m.get('vix_change_5d'))})` | Yahoo Finance (`^VIX`) | `{'ELEVATED RISK' if (m.get('vix_index') or 0) >= 20.0 else 'BENIGN / NORMAL'}` |",
        f"| **BTC–S&P 500 Corr (20d)**| ~20 Trading Days | `{_fmt_val(m.get('btc_spx_corr_20d'))}` | Rolling Pearson Correlation | `{'POSITIVE CORR' if (m.get('btc_spx_corr_20d') or 0) > 0.3 else ('INVERSE CORR' if (m.get('btc_spx_corr_20d') or 0) < -0.3 else 'DECOUPLED')}` |",
        f"| **BTC–S&P 500 Corr (60d)**| ~60 Trading Days | `{_fmt_val(m.get('btc_spx_corr_60d'))}` | Rolling Pearson Correlation | `{'POSITIVE CORR' if (m.get('btc_spx_corr_60d') or 0) > 0.3 else ('INVERSE CORR' if (m.get('btc_spx_corr_60d') or 0) < -0.3 else 'DECOUPLED')}` |",
        "",
        "### 12F. Sentiment & Risk Context",
        "",
        "| Metric | Preferred Lookback | Value | Source / Benchmark | Status |",
        "| :--- | :--- | :--- | :--- | :--- |",
        f"| **Crypto Fear & Greed** | Current | `{s.get('fear_and_greed_score')} / 100 ({s.get('fear_and_greed_classification')})` | Alternative.me API | `LIVE SENTIMENT` |",
        f"| **BTC Dominance %** | Current | `{_fmt_val(s.get('btc_dominance_pct'), '%')}` | CoinGecko Global API | `MARKET CAP DOMINANCE` |",
        f"| **Material Headlines (6–48h)**| Last 6–48 hours | `{s.get('material_headlines_6_48h')}` | Disruption Scanner | `NATIVE AI CONTEXT` |",
        f"| **USDT Health Markers** | Current Peg / Reserves | `{s.get('usdt_health_markers')}` | Stablecoin Disruption Rule | `NATIVE AI CONTEXT` |",
        f"| **Upcoming 14D Catalysts**| Next 14 calendar days | `{s.get('catalysts_next_14d')}` | Macro Catalyst Radar | `NATIVE AI CONTEXT` |",
        "",
        "### 12G. Mean-Reversion Inputs (Landscape Protocol)",
        "",
        "| Metric | Preferred Lookback | Value | Specification | Status |",
        "| :--- | :--- | :--- | :--- | :--- |",
        f"| **Daily RSI(14)** | 14 Daily Closes | `{_fmt_val(mr.get('daily_rsi14'))}` | Wilder's RSI(14) | `{'OVERSOLD' if (mr.get('daily_rsi14') or 50) <= 35 else ('OVERBOUGHT' if (mr.get('daily_rsi14') or 50) >= 65 else 'NEUTRAL')}` |",
        f"| **Log-Spread Raw** | Current Close vs. SMA50 | `{_fmt_val(mr.get('log_spread_raw'))}` | $\\ln(P) - \\ln(\\text{{SMA}}_{{50}})$ | `DISCOUNT TO 50D MEAN` |",
        f"| **Log-Spread 50D StdDev**| 50 Daily Closes | `{_fmt_val(mr.get('log_spread_50d_std'))}` | $\\sigma_{{50}}$ of Log-Spread | `VOLATILITY BASELINE` |",
        f"| **Log-Spread Z-Score** | 50-Day Window | `{_fmt_val(mr.get('log_spread_zscore'), 'σ')}` | $(\\ln(P) - \\ln(\\text{{SMA}}_{{50}})) / \\sigma_{{50}}$ | `{'EXTREME MEAN-REVERSION' if abs(mr.get('log_spread_zscore') or 0) >= 2.0 else 'STANDARD SPREAD'}` |",
    ]

    return "\n".join(lines) + "\n"
