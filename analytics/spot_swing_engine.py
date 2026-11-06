"""Tab [0]: BTC Spot Swing Screening & Alert Engine.

Deterministic, rule-based screener for BTC spot swings (3 day - 3 week horizon):

    Module B  Macro regime gate   (1D)  EMA50 > EMA200 trend + Bollinger-width squeeze percentile
    Module C  Structural setup    (4H)  Previous-week low sweep -> reclaim -> volume confirmation
    Module D  Risk engine               ATR invalidation stop, fixed-risk spot sizing, triple barrier
    Module E  State + alerts            Persistent trade lifecycle, de-duplicated webhook/Telegram alerts

Engineering rules that differ from a naive reading of the spec (all deliberate):

1. Closed bars only, proven by successor. A bar is treated as final only if a LATER bar exists in the
   series (not by blindly using `iloc[-2]`). A stale feed (newest closed bar too old) suspends the
   screener instead of evaluating hours-old candles.
2. 4H bars are built from the continuously-synced 1H buffer. The dedicated 4H buffer is only loaded at
   warmup and would freeze, so it is deliberately not used.
3. Weekly anchors use Monday-00:00-UTC weeks. (`resample("W-MON")` with pandas defaults bins Tue-Mon,
   which would silently shift PWL/PWH by a day.)
4. De-duplication: a setup can only fire for a sweep bar NEWER than the sweep that produced the last
   trade, so hovering above PWL after a reclaim cannot re-trigger on every 4H close.
5. Spot has no leverage: 1%-risk size is capped at 100% of equity (flagged when the cap binds).
6. Barrier checks run on closed 4H bars; when a single bar touches both the stop and a target the stop
   is assumed to have been hit first (conservative).
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
import time
from dataclasses import asdict, fields
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

from config.settings import EngineConfig
from core.models import (
    KlineBar,
    SpotSwingEvaluation,
    SpotSwingMacroGate,
    SpotSwingMagnetProtocol,
    SpotSwingRisk,
    SpotSwingSetup,
    SpotSwingTrade,
)
from core.state_store import StateStore

from .spot_swing_notifier import SpotSwingNotifier

logger = logging.getLogger("spot_swing")

TF_1H_MS = 3_600_000
TF_4H_MS = 4 * TF_1H_MS
TF_1D_MS = 24 * TF_1H_MS

STATE_VERSION = 1
MAX_EVENTS = 50
MAX_HISTORY = 30


# ============================================================================
# DATA PREPARATION
# ============================================================================

def bars_to_frame(bars: Sequence[KlineBar]) -> pd.DataFrame:
    """Converts KlineBars into a de-duplicated, time-sorted OHLCV frame (column `ts` = open time, ms)."""
    if not bars:
        return pd.DataFrame(columns=["ts", "open", "high", "low", "close", "volume"])
    df = pd.DataFrame(
        {
            "ts": [int(b.timestamp_ms) for b in bars],
            "open": [float(b.open) for b in bars],
            "high": [float(b.high) for b in bars],
            "low": [float(b.low) for b in bars],
            "close": [float(b.close) for b in bars],
            "volume": [float(b.volume) for b in bars],
        }
    )
    return df.drop_duplicates("ts", keep="last").sort_values("ts").reset_index(drop=True)


def finalized_bars(df: pd.DataFrame) -> pd.DataFrame:
    """Drops the newest bar: it is the only one that can still be forming (or stale-forming)."""
    if len(df) <= 1:
        return df.iloc[0:0].reset_index(drop=True)
    return df.iloc[:-1].reset_index(drop=True)


def build_closed_4h_from_1h(bars_1h: Sequence[KlineBar]) -> pd.DataFrame:
    """Aggregates 1H bars into UTC-aligned 4H bars and returns only FINAL, COMPLETE ones.

    A bucket is final only if (a) a later bucket exists (successor proof) and (b) it contains all four
    1H bars (no leading partial bucket, no gaps).
    """
    df = bars_to_frame(bars_1h)
    if df.empty:
        return df
    df["bucket"] = (df["ts"] // TF_4H_MS) * TF_4H_MS
    grouped = df.groupby("bucket", sort=True)
    agg = grouped.agg(
        open=("open", "first"),
        high=("high", "max"),
        low=("low", "min"),
        close=("close", "last"),
        volume=("volume", "sum"),
        n=("ts", "count"),
    ).reset_index()
    agg = agg.rename(columns={"bucket": "ts"})
    agg = finalized_bars(agg)  # successor proof
    agg = agg[agg["n"] == 4].drop(columns=["n"]).reset_index(drop=True)
    return agg


def is_series_fresh(df_closed: pd.DataFrame, tf_ms: int, now_ms: int, grace_ms: int) -> bool:
    """True when the newest closed bar is at most one timeframe (+grace) behind the latest possible close."""
    if df_closed.empty:
        return False
    newest_open = int(df_closed["ts"].iloc[-1])
    return newest_open + 2 * tf_ms + grace_ms >= now_ms


def wilder_atr(df: pd.DataFrame, period: int = 14) -> float:
    """Wilder ATR (RMA) of the last bar of `df`."""
    if len(df) < 2:
        return 0.0
    prev_close = df["close"].shift(1)
    tr = pd.concat(
        [df["high"] - df["low"], (df["high"] - prev_close).abs(), (df["low"] - prev_close).abs()],
        axis=1,
    ).max(axis=1)
    return float(tr.ewm(alpha=1.0 / period, adjust=False).mean().iloc[-1])


# ============================================================================
# MODULE B: MACRO REGIME GATE
# ============================================================================

def compute_macro_gate(
    df_1d_closed: pd.DataFrame,
    ema_fast: int = 50,
    ema_slow: int = 200,
    bbw_period: int = 20,
    rank_window: int = 180,
    max_percentile: float = 0.30,
    squeeze_lookback_bars: int = 1,
) -> Optional[SpotSwingMacroGate]:
    """Trend baseline (close > EMA50 > EMA200) AND volatility squeeze (BBW rank <= 30%).

    BBW = (upper - lower) / SMA20 with 2-sigma population-stdev bands, i.e. 4*sigma / SMA20.
    The percentile rank is the share of the trailing `rank_window` BBW values (current included) that
    are <= the current BBW. Returns None while there is not enough history for a valid rank.
    """
    min_rows = bbw_period + rank_window - 1
    if len(df_1d_closed) < min_rows:
        return None

    close = df_1d_closed["close"]
    ema_f = close.ewm(span=ema_fast, adjust=False).mean()
    ema_s = close.ewm(span=ema_slow, adjust=False).mean()
    sma = close.rolling(bbw_period).mean()
    std = close.rolling(bbw_period).std(ddof=0)
    bbw = (4.0 * std) / sma
    pct = bbw.rolling(rank_window).apply(lambda w: float((w <= w[-1]).mean()), raw=True)

    last_pct = pct.iloc[-1]
    if not np.isfinite(last_pct):
        return None

    lookback = max(1, int(squeeze_lookback_bars))
    recent = pct.iloc[-lookback:]
    compression_pass = bool((recent <= max_percentile).any())

    last_close = float(close.iloc[-1])
    trend_pass = bool(last_close > ema_f.iloc[-1] and ema_f.iloc[-1] > ema_s.iloc[-1])
    return SpotSwingMacroGate(
        bar_ts_ms=int(df_1d_closed["ts"].iloc[-1]),
        close=last_close,
        ema50=float(ema_f.iloc[-1]),
        ema200=float(ema_s.iloc[-1]),
        trend_pass=trend_pass,
        bbw=float(bbw.iloc[-1]),
        bbw_percentile=float(last_pct),
        compression_pass=compression_pass,
        squeeze_lookback_bars=lookback,
        macro_approved=bool(trend_pass and compression_pass),
    )


# ============================================================================
# MODULE C: WEEKLY ANCHORS + SWEEP / RECLAIM / VOLUME
# ============================================================================

def current_week_start_ms(now_ms: int) -> int:
    """Monday 00:00 UTC of the week containing `now_ms`."""
    now = datetime.fromtimestamp(now_ms / 1000.0, tz=timezone.utc)
    monday = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    return int(monday.timestamp() * 1000)


def compute_weekly_anchors(df_1d_closed: pd.DataFrame, now_ms: int) -> Tuple[float, float, int, bool]:
    """Previous Week Low / High from the last COMPLETED Monday-Sunday week.

    Returns (pwl, pwh, current_week_start_ms, ready). `ready` is False unless all 7 daily bars of the
    previous week are present.
    """
    cur_ms = current_week_start_ms(now_ms)
    prev_ms = cur_ms - 7 * TF_1D_MS
    wk = df_1d_closed[(df_1d_closed["ts"] >= prev_ms) & (df_1d_closed["ts"] < cur_ms)]
    if len(wk) != 7:
        return 0.0, 0.0, cur_ms, False
    return float(wk["low"].min()), float(wk["high"].max()), cur_ms, True


def detect_setup(
    df_4h_closed: pd.DataFrame,
    pwl: float,
    pwh: float,
    week_start_ms: int,
    window_bars: int = 12,
    vol_sma_period: int = 3,
    last_traded_sweep_ts_ms: int = 0,
) -> SpotSwingSetup:
    """Sweep (low < PWL in last 12 bars) + Reclaim (last close > PWL) + Volume (> SMA3)."""
    last = df_4h_closed.iloc[-1]
    window = df_4h_closed.iloc[-window_bars:]
    swept = window[window["low"] < pwl]
    sweep_detected = not swept.empty

    sweep_low = 0.0
    sweep_bar_ts = 0
    if sweep_detected:
        idx = swept["low"].idxmin()
        sweep_low = float(swept.loc[idx, "low"])
        sweep_bar_ts = int(swept.loc[idx, "ts"])

    vol_sma = float(df_4h_closed["volume"].rolling(vol_sma_period).mean().iloc[-1])
    reclaim = bool(last["close"] > pwl)
    volume_ok = bool(np.isfinite(vol_sma) and last["volume"] > vol_sma)
    raw_signal = bool(sweep_detected and reclaim and volume_ok)

    return SpotSwingSetup(
        bar_ts_ms=int(last["ts"]),
        close=float(last["close"]),
        volume=float(last["volume"]),
        vol_sma3=vol_sma if np.isfinite(vol_sma) else 0.0,
        pwl=pwl,
        pwh=pwh,
        week_start_ms=week_start_ms,
        sweep_detected=sweep_detected,
        sweep_low=sweep_low,
        sweep_bar_ts_ms=sweep_bar_ts,
        reclaim_confirmed=reclaim,
        volume_confirmed=volume_ok,
        signal_active=raw_signal,
        is_fresh=bool(raw_signal and sweep_bar_ts > last_traded_sweep_ts_ms),
        anchors_ready=True,
    )


# ============================================================================
# MODULE D: RISK & TRIPLE-BARRIER POSITION SIZING
# ============================================================================

def compute_risk(
    setup: SpotSwingSetup,
    df_4h_closed: pd.DataFrame,
    equity_usd: float,
    risk_pct: float = 1.0,
    atr_period: int = 14,
    stop_atr_mult: float = 0.5,
    tp1_r_multiple: float = 2.0,
    tp1_fraction: float = 0.5,
    time_stop_days: int = 10,
    short_liq_magnet: float = 0.0,
    min_rrr: float = 3.0,
) -> Optional[SpotSwingRisk]:
    """ATR invalidation stop, fixed-risk spot size (capped at 100% equity), 1:3 RRR check, and triple-barrier levels."""
    atr = wilder_atr(df_4h_closed, atr_period)
    entry = setup.close
    stop = setup.sweep_low - stop_atr_mult * atr
    distance = entry - stop
    if not (np.isfinite(atr) and atr > 0 and np.isfinite(distance) and distance > 0 and entry > 0):
        return None

    budget = equity_usd * risk_pct / 100.0
    qty_uncapped = budget / distance
    qty_max_spot = equity_usd / entry
    qty = min(qty_uncapped, qty_max_spot)
    notional = qty * entry
    tp1 = entry + tp1_r_multiple * distance
    tp_3r = entry + min_rrr * distance
    target_mag = short_liq_magnet if short_liq_magnet > 0 else (setup.pwh * 1.005 if setup.pwh > 0 else tp_3r)
    rrr_to_pwh = max(0.0, setup.pwh - entry) / distance if setup.pwh > 0 else 0.0
    rrr_to_magnet = max(0.0, target_mag - entry) / distance
    max_entry_3r = (target_mag + min_rrr * stop) / (1.0 + min_rrr)
    entry_close_ts = setup.bar_ts_ms + TF_4H_MS  # signal bar close == entry time
    return SpotSwingRisk(
        entry=entry,
        stop=stop,
        atr14=atr,
        stop_distance=distance,
        stop_distance_pct=distance / entry * 100.0,
        equity_usd=equity_usd,
        risk_pct=risk_pct,
        risk_budget_usd=budget,
        qty_btc_uncapped=qty_uncapped,
        qty_btc=qty,
        notional_usd=notional,
        equity_alloc_pct=notional / equity_usd * 100.0 if equity_usd > 0 else 0.0,
        spot_capped=bool(qty_uncapped > qty_max_spot),
        realized_risk_usd=qty * distance,
        tp1=tp1,
        tp2_pwh=setup.pwh,
        tp2_inside_tp1=bool(setup.pwh <= tp1),
        tp1_fraction=tp1_fraction,
        time_stop_ts_ms=entry_close_ts + time_stop_days * TF_1D_MS,
        tp_3r=tp_3r,
        rrr_to_pwh=rrr_to_pwh,
        rrr_to_magnet=rrr_to_magnet,
        rrr_meets_min=bool(rrr_to_magnet >= min_rrr),
        max_entry_for_3r=max_entry_3r,
        short_liq_magnet=target_mag,
    )


# ============================================================================
# MODULE F: DAILY LIQUIDATION MAGNET PROTOCOL (STEPS 1-4 + RRR 1:3)
# ============================================================================

def _load_magnet_overrides(config: Optional[EngineConfig]) -> Dict[str, Any]:
    """Reads optional Coinglass magnet overrides and headline status from protocol_context.json."""
    out: Dict[str, Any] = {
        "short_liq_magnet_override_usd": 0.0,
        "long_liq_magnet_override_usd": 0.0,
        "short_liq_size_override_usd": 0.0,
        "long_liq_size_override_usd": 0.0,
        "headline_classification": "NONE_SIGNIFICANT",
    }
    try:
        if config is not None and config.protocol_context_path.exists():
            with open(config.protocol_context_path, "r", encoding="utf-8") as fh:
                raw = json.load(fh)
                if isinstance(raw, dict):
                    out.update(raw)
    except Exception:
        pass
    if os.getenv("SHORT_LIQ_MAGNET_USD"):
        try:
            out["short_liq_magnet_override_usd"] = float(os.environ["SHORT_LIQ_MAGNET_USD"])
        except ValueError:
            pass
    if os.getenv("LONG_LIQ_MAGNET_USD"):
        try:
            out["long_liq_magnet_override_usd"] = float(os.environ["LONG_LIQ_MAGNET_USD"])
        except ValueError:
            pass
    return out


def compute_magnet_protocol(
    df_1d_closed: pd.DataFrame,
    df_4h_closed: pd.DataFrame,
    price: float,
    macro: SpotSwingMacroGate,
    setup: SpotSwingSetup,
    store: Optional[StateStore] = None,
    config: Optional[EngineConfig] = None,
    equity_usd: float = 10_000.0,
    risk_pct: float = 1.0,
    min_rrr: float = 3.0,
    range_lookback_days: int = 35,
    trade: Optional[SpotSwingTrade] = None,
) -> SpotSwingMagnetProtocol:
    """Executes the Daily Liquidation Magnet Protocol (Master Prompt Steps 1-4) with tight 1:3 RRR Money Management."""
    closes_1d = df_1d_closed["close"]
    last_close_1d = float(closes_1d.iloc[-1])
    sma50_1d = float(closes_1d.iloc[-50:].mean())
    ema50_1d = float(macro.ema50)
    sma50_5d_ago = float(closes_1d.iloc[-55:-5].mean()) if len(closes_1d) >= 55 else sma50_1d
    sma50_slope_5d_pct = ((sma50_1d - sma50_5d_ago) / max(sma50_5d_ago, 1.0)) * 100.0

    lb = min(max(30, int(range_lookback_days)), len(df_1d_closed))
    win_range = df_1d_closed.iloc[-lb:]
    range_high_30d = float(win_range["high"].max())
    range_low_30d = float(win_range["low"].min())
    range_pivot = (range_high_30d + range_low_30d) / 2.0
    range_span = max(range_high_30d - range_low_30d, 1.0)
    range_pos_pct = ((price - range_low_30d) / range_span) * 100.0

    # --- Step 1: Liquidation Heatmap Magnets (Short-Liq Above & Long-Liq Below) ---
    ctx = _load_magnet_overrides(config)
    manual_short = float(
        ctx.get("short_liq_magnet_override_usd")
        or ctx.get("short_liq_magnet_price")
        or 0.0
    )
    manual_long = float(
        ctx.get("long_liq_magnet_override_usd")
        or ctx.get("long_liq_magnet_price")
        or 0.0
    )
    manual_short_sz = float(
        ctx.get("short_liq_size_override_usd")
        or ctx.get("short_liq_magnet_size_usd")
        or 0.0
    )
    manual_long_sz = float(
        ctx.get("long_liq_size_override_usd")
        or ctx.get("long_liq_magnet_size_usd")
        or 0.0
    )

    if manual_short > 0.0:
        short_liq_magnet = manual_short
        short_liq_source = "[COINGLASS MANUAL]"
    else:
        sh_7d = float(df_1d_closed["high"].iloc[-7:].max())
        sh_14d = float(df_1d_closed["high"].iloc[-14:].max())
        c_vah = store.macro_profile.c_vah if (store is not None and store.macro_profile is not None) else 0.0
        cands_up = [
            lvl * 1.005
            for lvl in (setup.pwh, sh_7d, sh_14d, range_high_30d, c_vah)
            if lvl and lvl * 1.005 > price * 1.004
        ]
        cands_1pct = [c for c in cands_up if c >= price * 1.01]
        short_liq_magnet = (
            min(cands_1pct)
            if cands_1pct
            else (min(cands_up) if cands_up else max(range_high_30d, price) * 1.025)
        )
        short_liq_source = "[EST. SWING LIQ POOL]"

    if manual_long > 0.0:
        long_liq_magnet = manual_long
        long_liq_source = "[COINGLASS MANUAL]"
    else:
        sl_7d = float(df_1d_closed["low"].iloc[-7:].min())
        sl_14d = float(df_1d_closed["low"].iloc[-14:].min())
        c_val = store.macro_profile.c_val if (store is not None and store.macro_profile is not None) else 0.0
        cands_dn = [
            lvl * 0.995
            for lvl in (setup.pwl, sl_7d, sl_14d, range_low_30d, c_val)
            if lvl and 0 < lvl * 0.995 < price * 0.996
        ]
        cands_dn_1pct = [c for c in cands_dn if c <= price * 0.99]
        long_liq_magnet = (
            max(cands_dn_1pct)
            if cands_dn_1pct
            else (max(cands_dn) if cands_dn else min(range_low_30d, price) * 0.975)
        )
        long_liq_source = "[EST. SWING LIQ POOL]"

    short_liq_distance_pct = ((short_liq_magnet - price) / max(price, 1.0)) * 100.0
    long_liq_distance_pct = ((price - long_liq_magnet) / max(price, 1.0)) * 100.0

    # --- Positioning Snapshot (OI, Funding, Spot CVD, Executed Liquidations) ---
    deriv = store.derivatives_snapshot if store is not None else None
    flow = store.flow_snapshot if store is not None else None

    oi_btc = float(deriv.open_interest_btc if deriv is not None else (store.open_interest_btc if store is not None else 0.0))
    oi_usd = float(deriv.open_interest_usd if deriv is not None else (store.open_interest_usd if store is not None else 0.0))
    if oi_usd <= 0.0 and oi_btc > 0.0:
        oi_usd = oi_btc * price
    oi_24h = float(store.get_oi_change_pct(86400)) if store is not None else 0.0
    oi_4h = float(deriv.oi_change_4h_pct if deriv is not None else (store.get_oi_change_pct(14400) if store is not None else 0.0))
    fund_8h = float(deriv.funding_rate_pct if deriv is not None else (store.funding_rate_pct if store is not None else 0.0))

    if manual_short_sz > 0.0:
        short_liq_size_label = f"${manual_short_sz / 1e6:,.0f}M (Coinglass)"
    elif oi_usd > 0.0:
        est_s = oi_usd * (0.045 if fund_8h < 0 else 0.032)
        short_liq_size_label = f"~${est_s / 1e6:,.0f}M est. pool"
    else:
        short_liq_size_label = "Est. Swing Pool"

    if manual_long_sz > 0.0:
        long_liq_size_label = f"${manual_long_sz / 1e6:,.0f}M (Coinglass)"
    elif oi_usd > 0.0:
        est_l = oi_usd * (0.045 if fund_8h > 0.005 else 0.035)
        long_liq_size_label = f"~${est_l / 1e6:,.0f}M est. pool"
    else:
        long_liq_size_label = "Est. Swing Pool"

    liq_rep = store.trap_evaluation.liquidation_report if (store is not None and store.trap_evaluation is not None) else None
    if liq_rep is not None and liq_rep.is_available and "24h" in liq_rep.windows:
        w24 = liq_rep.windows["24h"]
        cum_liq_24h_summary = (
            f"24H ForceOrders: ${w24.total_usd / 1e6:.2f}M "
            f"(Long: ${w24.long_usd / 1e6:.2f}M • Short: ${w24.short_usd / 1e6:.2f}M • {liq_rep.liquidation_multiple_24h:.2f}x Med)"
        )
    else:
        cum_liq_24h_summary = "Data unavailable (companion detector standby)"

    prev_1d_close = float(closes_1d.iloc[-2]) if len(closes_1d) >= 2 else last_close_1d
    price_chg_24h = ((price - prev_1d_close) / max(prev_1d_close, 1.0)) * 100.0
    if oi_24h >= 1.0 or oi_4h >= 0.35:
        oi_dir = "Rising"
        oi_interp = "New shorts entering (squeeze fuel)" if price_chg_24h <= -0.20 else "New longs entering (trap risk)"
    elif oi_24h <= -1.0 or oi_4h <= -0.35:
        oi_dir = "Falling"
        oi_interp = "Covering / de-leveraging"
    else:
        oi_dir = "Flat"
        oi_interp = "Balanced positioning"
    oi_trend_str = f"{oi_dir} (24H {oi_24h:+.2f}% • 4H {oi_4h:+.2f}% • {oi_interp})"

    if fund_8h < -0.0005:
        funding_status = f"Negative ({fund_8h:+.4f}% / 8h — Shorts paying, squeeze primed)"
    elif fund_8h <= 0.0060:
        funding_status = f"Neutral ({fund_8h:+.4f}% / 8h — Uncrowded)"
    elif fund_8h <= 0.0150:
        funding_status = f"Positive ({fund_8h:+.4f}% / 8h — Longs paying)"
    else:
        funding_status = f"Strongly Positive ({fund_8h:+.4f}% / 8h — Crowded longs, trap risk)"

    if flow is not None and (flow.w_24h.spot_delta_btc != 0.0 or flow.w_4h.spot_delta_btc != 0.0):
        s_24h, p_24h = float(flow.w_24h.spot_delta_btc), float(flow.w_24h.perp_delta_btc)
        s_4h, p_4h = float(flow.w_4h.spot_delta_btc), float(flow.w_4h.perp_delta_btc)
    elif store is not None and store.spot_klines_1h:
        s1h = list(store.spot_klines_1h)
        p1h = list(store.perp_klines_1h)
        s_24h = float(sum(b.delta for b in s1h[-24:]))
        p_24h = float(sum(b.delta for b in p1h[-24:])) if p1h else 0.0
        s_4h = float(sum(b.delta for b in s1h[-4:]))
        p_4h = float(sum(b.delta for b in p1h[-4:])) if p1h else 0.0
    else:
        s_24h = p_24h = s_4h = p_4h = 0.0

    last_4h_bullish = bool(float(df_4h_closed["close"].iloc[-1]) > float(df_4h_closed["open"].iloc[-1]))
    if s_4h > 15.0 and (s_24h >= 0.0 or s_4h >= 0.5 * max(p_4h, 1.0)):
        spot_cvd_confirming = True
        spot_cvd_assessment = f"Confirming (4H Spot {s_4h:+,.0f} BTC • 24H {s_24h:+,.0f} BTC)"
    elif s_4h == 0.0 and s_24h == 0.0 and setup.reclaim_confirmed and setup.volume_confirmed and last_4h_bullish:
        spot_cvd_confirming = True
        spot_cvd_assessment = f"Confirming (4H Reclaim Vol {setup.volume:,.0f} > SMA3 {setup.vol_sma3:,.0f})"
    elif s_4h <= 0.0 and p_4h > 20.0:
        spot_cvd_confirming = False
        spot_cvd_assessment = f"Not confirming — Futures-driven (4H Spot {s_4h:+,.0f} vs Perp {p_4h:+,.0f} BTC)"
    elif s_4h < -15.0:
        spot_cvd_confirming = False
        spot_cvd_assessment = f"Not confirming — Spot selling (4H Spot {s_4h:+,.0f} BTC)"
    else:
        spot_cvd_confirming = False
        spot_cvd_assessment = f"Mixed / Flat (4H Spot {s_4h:+,.0f} BTC • 24H {s_24h:+,.0f} BTC)"

    raw_hl = str(ctx.get("headline_filter") or ctx.get("headline_classification") or "NONE_SIGNIFICANT")
    raw_hl_key = raw_hl.upper().replace(" ", "_").replace("/", "_")
    headline_map = {
        "NONE_SIGNIFICANT": "None significant (Trade Magnet, Ignore Noise)",
        "STRUCTURAL_DELAYED": "Structural / Delayed (Ignore for immediate swing)",
        "RECURRING_RUMOR": "Recurring Rumor (Treat as trap fuel)",
        "IMMEDIATE_FLOW_EVENT": "Immediate Flow Event (Confirmed sustained spot flow)",
    }
    headline_filter = headline_map.get(raw_hl_key, raw_hl)

    # --- Step 2: Regime Confirmation (Range / Possible Transition / Trend) ---
    w30 = df_1d_closed.iloc[-30:]
    s1, s2, s3 = w30.iloc[:10], w30.iloc[10:20], w30.iloc[20:]
    hh_hl = bool(
        s3["high"].max() > s2["high"].max() > s1["high"].max()
        and s3["low"].min() > s2["low"].min() > s1["low"].min()
    )
    lh_ll = bool(
        s3["high"].max() < s2["high"].max() < s1["high"].max()
        and s3["low"].min() < s2["low"].min() < s1["low"].min()
    )
    prior_high = float(df_1d_closed["high"].iloc[-31:-1].max())
    prior_low = float(df_1d_closed["low"].iloc[-31:-1].min())

    if last_close_1d > prior_high and hh_hl and last_close_1d > sma50_1d:
        regime = "Trend"
        regime_detail = f"Bullish Daily HH+HL breakout above ${prior_high:,.0f} & 50DMA (${sma50_1d:,.0f})"
    elif last_close_1d < prior_low and lh_ll and last_close_1d < sma50_1d:
        regime = "Trend"
        regime_detail = f"Bearish Daily LH+LL breakdown below ${prior_low:,.0f} & 50DMA (${sma50_1d:,.0f})"
    elif range_pos_pct >= 92.0 or range_pos_pct <= 8.0:
        regime = "Possible Transition"
        regime_detail = f"Testing range boundary ({range_pos_pct:.0f}% of ${range_low_30d:,.0f}–${range_high_30d:,.0f}); watch for breakout vs sweep trap"
    else:
        regime = "Range"
        regime_detail = f"Oscillating at {range_pos_pct:.0f}% of ${range_low_30d:,.0f}–${range_high_30d:,.0f} around 50DMA (${sma50_1d:,.0f})"

    # --- Step 3: Tight Money Management (RRR >= 1:3) & Protocol Decision Rules ---
    atr_4h = max(wilder_atr(df_4h_closed, 14), 1.0)
    invalidation_level = min(range_pivot, sma50_1d)

    entry_ref = (
        trade.entry
        if trade is not None
        else (
            setup.close
            if (setup.signal_active and setup.close > 0 and abs(price - setup.close) / max(setup.close, 1.0) <= 0.015)
            else price
        )
    )
    if setup.sweep_detected and setup.sweep_low > 0 and setup.sweep_low < entry_ref:
        hard_stop_price = setup.sweep_low - 0.5 * atr_4h
    elif setup.anchors_ready and setup.pwl > 0 and setup.pwl < entry_ref:
        hard_stop_price = setup.pwl - 0.5 * atr_4h
    else:
        hard_stop_price = min(invalidation_level, long_liq_magnet) - 0.5 * atr_4h
    if entry_ref - hard_stop_price < 0.25 * atr_4h:
        hard_stop_price = entry_ref - 1.0 * atr_4h

    risk_distance_usd = max(entry_ref - hard_stop_price, 1.0)
    risk_distance_pct = (risk_distance_usd / max(entry_ref, 1.0)) * 100.0
    target_magnet = short_liq_magnet if manual_short > 0.0 else max(
        short_liq_magnet,
        setup.pwh if (setup.anchors_ready and setup.pwh > entry_ref) else short_liq_magnet,
    )
    reward_to_magnet_usd = max(0.0, target_magnet - entry_ref)
    reward_to_magnet_pct = (reward_to_magnet_usd / max(entry_ref, 1.0)) * 100.0
    rrr_to_magnet = reward_to_magnet_usd / risk_distance_usd
    rrr_pass = bool(rrr_to_magnet >= min_rrr)
    tp_3r_price = entry_ref + min_rrr * risk_distance_usd
    max_entry_for_3r = (target_magnet + min_rrr * hard_stop_price) / (1.0 + min_rrr)

    budget = equity_usd * (risk_pct / 100.0)
    qty_uncapped = budget / risk_distance_usd
    qty_max_spot = equity_usd / max(entry_ref, 1.0)
    rec_qty = min(qty_uncapped, qty_max_spot)
    rec_notional = rec_qty * entry_ref
    rec_risk = rec_qty * risk_distance_usd
    alloc_pct = (rec_notional / equity_usd * 100.0) if equity_usd > 0 else 0.0
    spot_capped = bool(qty_uncapped > qty_max_spot)

    recent_4h_high = float(df_4h_closed["high"].iloc[-6:].max())
    swept_upper_cluster = recent_4h_high >= short_liq_magnet * 0.992 or recent_4h_high >= range_high_30d * 0.995
    rejected_below_pivot = price < range_pivot or price < sma50_1d

    if swept_upper_cluster and rejected_below_pivot and not spot_cvd_confirming:
        verdict = "Reduce or Exit"
        confidence = "High"
        primary_reason = (
            f"Price swept into upper short-liq zone (${recent_4h_high:,.0f}), exhausted momentum, and rejected below pivot/50DMA."
        )
        invalidation_text = f"Daily close reclaiming above ${max(range_pivot, sma50_1d):,.0f} with confirming Spot CVD."
        actionable_note = (
            f"Reduce or exit spot longs immediately. Keep capital safe. Action playbook:\n"
            f"• Short-squeeze fuel exhausted at upper cluster; price rejected below Range Pivot (${range_pivot:,.0f}) / 50DMA (${sma50_1d:,.0f}).\n"
            f"• Prepare for rotation lower toward ${long_liq_magnet:,.0f} long-liquidation pool."
        )
    elif last_close_1d > short_liq_magnet and spot_cvd_confirming and oi_24h >= -1.0:
        verdict = "Rare Add Consideration"
        confidence = "High" if rrr_pass else "Medium"
        primary_reason = (
            f"Daily close (${last_close_1d:,.0f}) cleared short-liq wall (${short_liq_magnet:,.0f}) with confirming Spot CVD and resilient OI."
        )
        invalidation_text = f"Daily close back below ${short_liq_magnet:,.0f} or 50-day MA (${sma50_1d:,.0f})."
        actionable_note = (
            f"Rare confirmed breakout above ${short_liq_magnet:,.0f} with confirming Spot CVD. Action playbook:\n"
            f"• Consider adds on retest of ${short_liq_magnet:,.0f} ONLY if R:R >= 1:3 holds (Stop ${hard_stop_price:,.0f}, 3R Target ${tp_3r_price:,.0f}).\n"
            f"• Invalidation: Daily close falling back below ${short_liq_magnet:,.0f} or 50-day MA (${sma50_1d:,.0f}) voids breakout."
        )
    elif (short_liq_distance_pct <= 3.5 or range_pos_pct >= 72.0) and fund_8h <= 0.008 and not spot_cvd_confirming:
        verdict = "Partial Profit into Magnet"
        confidence = "High"
        primary_reason = (
            f"Short-liq magnet sits {short_liq_distance_pct:.2f}% above (${short_liq_magnet:,.0f}) with negative/neutral funding ({fund_8h:+.4f}%) and unconfirmed Spot CVD."
        )
        invalidation_text = f"Daily close below Range Pivot (${range_pivot:,.0f}) or 50-day MA (${sma50_1d:,.0f})."
        actionable_note = (
            f"Scale 30–50% profit into ${short_liq_magnet:,.0f} Short-Liq Magnet now. Do NOT chase green candles. Action playbook:\n"
            f"• Lock in gains into short-covering liquidity; move trailing stop on runner to Range Pivot (${range_pivot:,.0f}).\n"
            f"• No new long adds until a daily close confirms above ${short_liq_magnet:,.0f} with rising Spot CVD."
        )
    elif (
        trade is not None
        or (setup.signal_active and macro.macro_approved)
        or (long_liq_distance_pct <= 3.0 and spot_cvd_confirming and macro.trend_pass)
    ) and rrr_pass:
        verdict = "Hold"
        confidence = "High" if (spot_cvd_confirming and macro.macro_approved) else "Medium"
        primary_reason = (
            f"Liquidity sweep reclaimed with Spot confirmation and asymmetric {rrr_to_magnet:.2f}R payoff (>= 3.0R) toward ${target_magnet:,.0f} magnet."
        )
        invalidation_text = f"Daily close below ${invalidation_level:,.0f} (Pivot/50DMA) or hard stop at ${hard_stop_price:,.0f}."
        actionable_note = (
            f"Hold spot long position ({rec_qty:.4f} BTC @ 1% risk). Action playbook:\n"
            f"• Scale 30–50% into ${target_magnet:,.0f} Short-Liq Magnet, then immediately move stop to breakeven (${entry_ref:,.0f}).\n"
            f"• Trail remaining runner toward structural target PWH (${setup.pwh:,.0f}); exit on 10-day time stop or daily close < ${invalidation_level:,.0f}."
        )
    else:
        verdict = "Do Nothing"
        confidence = "High"
        if setup.signal_active and not macro.macro_approved:
            primary_reason = (
                f"4H Sweep/Reclaim printed, but 1D Macro Gate is FROZEN (close ${macro.close:,.0f} vs EMA50 ${macro.ema50:,.0f}, BBW rank {macro.bbw_percentile * 100:.0f}%); protocol defaults to cash."
            )
            actionable_note = (
                "Do not chase this bounce. Keep your capital in stablecoins. Wait for:\n"
                "• Physical Spot CVD to flip positive (+Spot BTC absorbing perps).\n"
                f"• Daily price structure to reclaim the Range Pivot / 50-Day MA (${range_pivot:,.0f} / ${sma50_1d:,.0f}), OR a deeper sweep that provides clear absorption."
            )
        elif setup.signal_active and not rrr_pass:
            primary_reason = (
                f"Setup reclaimed PWL, but R:R to ${target_magnet:,.0f} magnet is {rrr_to_magnet:.2f}R (rejected by strict >= 3.0R rule; max 3R entry is ${max_entry_for_3r:,.0f})."
            )
            actionable_note = (
                f"Setup reclaimed PWL, but live R:R is {rrr_to_magnet:.2f}R (< 3.0R). Do not chase. Wait for:\n"
                f"• Limit pullback <= ${max_entry_for_3r:,.0f} to secure mandatory >= 1:3 RRR.\n"
                f"• Short-covering squeeze to sweep into ${short_liq_magnet:,.0f} before considering reversal."
            )
        elif not rrr_pass:
            primary_reason = (
                f"Price in mid-range with {rrr_to_magnet:.2f}R to ${target_magnet:,.0f} magnet (below mandatory 1:3 RRR; max 3R entry is ${max_entry_for_3r:,.0f})."
            )
            actionable_note = (
                "Price in mid-range chop with poor reward-to-risk. Sit 100% in cash. Wait for:\n"
                f"• Deeper sweep below range low (${range_low_30d:,.0f}) or long-liq magnet (${long_liq_magnet:,.0f}).\n"
                f"• Pullback price <= ${max_entry_for_3r:,.0f} that guarantees >= 1:3 RRR to ${target_magnet:,.0f}."
            )
        elif not macro.macro_approved:
            primary_reason = (
                f"1D Macro Gate is FROZEN (close ${macro.close:,.0f} vs EMA50 ${macro.ema50:,.0f}, BBW rank {macro.bbw_percentile * 100:.0f}%); protocol defaults to cash."
            )
            actionable_note = (
                "1D Macro Gate is FROZEN (market in macro downtrend / volatility expansion). Stay 100% in cash. Wait for:\n"
                f"• Daily close to reclaim 50-day EMA (${macro.ema50:,.0f}) and SMA (${sma50_1d:,.0f}).\n"
                f"• Volatility compression back into bottom 30% (BBW rank currently {macro.bbw_percentile * 100:.1f}%)."
            )
        else:
            primary_reason = (
                f"No positioning imbalance or confirmed range-low reclaim trigger at ${price:,.0f} (R:R {rrr_to_magnet:.2f}R); default is inaction."
            )
            actionable_note = (
                "Sit 100% in cash. No actionable setup at current price. Wait for:\n"
                f"• 4H sweep below PWL (${setup.pwl:,.0f}) or Long-Liq pool (${long_liq_magnet:,.0f}).\n"
                f"• Volume reclaim and Spot CVD confirmation with entry <= ${max_entry_for_3r:,.0f} (>= 1:3 RRR)."
            )
        invalidation_text = f"Daily close below Range Pivot (${range_pivot:,.0f}) or 50-day MA (${sma50_1d:,.0f})."

    return SpotSwingMagnetProtocol(
        current_price=price,
        sma50_1d=sma50_1d,
        ema50_1d=ema50_1d,
        sma50_slope_5d_pct=sma50_slope_5d_pct,
        range_high_30d=range_high_30d,
        range_low_30d=range_low_30d,
        range_pivot=range_pivot,
        range_pos_pct=range_pos_pct,
        short_liq_magnet=short_liq_magnet,
        short_liq_distance_pct=short_liq_distance_pct,
        short_liq_size_label=short_liq_size_label,
        short_liq_source=short_liq_source,
        long_liq_magnet=long_liq_magnet,
        long_liq_distance_pct=long_liq_distance_pct,
        long_liq_size_label=long_liq_size_label,
        long_liq_source=long_liq_source,
        cum_liq_24h_summary=cum_liq_24h_summary,
        oi_trend=oi_trend_str,
        oi_change_24h_pct=oi_24h,
        oi_change_4h_pct=oi_4h,
        oi_btc=oi_btc,
        oi_interpretation=oi_interp,
        funding_rate_8h_pct=fund_8h,
        funding_status=funding_status,
        spot_cvd_24h_btc=s_24h,
        perp_cvd_24h_btc=p_24h,
        spot_cvd_4h_btc=s_4h,
        perp_cvd_4h_btc=p_4h,
        spot_cvd_assessment=spot_cvd_assessment,
        spot_cvd_confirming=spot_cvd_confirming,
        headline_filter=headline_filter,
        regime=regime,
        regime_detail=regime_detail,
        has_daily_hh_hl=hh_hl,
        has_daily_lh_ll=lh_ll,
        min_required_rrr=min_rrr,
        entry_ref=entry_ref,
        invalidation_level=invalidation_level,
        hard_stop_price=hard_stop_price,
        risk_distance_usd=risk_distance_usd,
        risk_distance_pct=risk_distance_pct,
        reward_to_magnet_usd=reward_to_magnet_usd,
        reward_to_magnet_pct=reward_to_magnet_pct,
        rrr_to_magnet=rrr_to_magnet,
        rrr_pass=rrr_pass,
        tp_3r_price=tp_3r_price,
        max_entry_for_3r=max_entry_for_3r,
        recommended_qty_btc=rec_qty,
        recommended_notional_usd=rec_notional,
        recommended_risk_usd=rec_risk,
        equity_alloc_pct=alloc_pct,
        spot_capped=spot_capped,
        verdict=verdict,
        confidence=confidence,
        primary_reason=primary_reason,
        invalidation_text=invalidation_text,
        actionable_note=actionable_note,
    )


def _realized_r(trade: SpotSwingTrade, exit_price: float, tp1_fraction: float) -> float:
    """Weighted R multiple: partial at TP1 plus the remainder at `exit_price`."""
    dist = trade.entry - trade.initial_stop
    if dist <= 0:
        return 0.0
    if trade.tp1_hit:
        tp1_r = (trade.tp1 - trade.entry) / dist
        return tp1_fraction * tp1_r + (1.0 - tp1_fraction) * (exit_price - trade.entry) / dist
    return (exit_price - trade.entry) / dist


def advance_trade(
    trade: SpotSwingTrade,
    df_4h_closed: pd.DataFrame,
    tp1_fraction: float = 0.5,
) -> List[Dict[str, Any]]:
    """Replays closed 4H bars after `last_processed_bar_ts_ms` through the triple barrier.

    Mutates `trade` in place and returns the barrier events (dicts) in chronological order.
    Stop is checked before targets within the same bar (conservative).
    """
    events: List[Dict[str, Any]] = []
    if trade.status == "CLOSED":
        return events

    new_bars = df_4h_closed[df_4h_closed["ts"] > trade.last_processed_bar_ts_ms]
    for row in new_bars.itertuples(index=False):
        bar_close_ts = int(row.ts) + TF_4H_MS
        trade.last_processed_bar_ts_ms = int(row.ts)
        low, high, close = float(row.low), float(row.high), float(row.close)

        def _close(reason: str, price: float, event: str) -> None:
            trade.status = "CLOSED"
            trade.closed_reason = reason
            trade.exit_price = price
            trade.exit_ts_ms = bar_close_ts
            trade.realized_r = _realized_r(trade, price, tp1_fraction)
            events.append({"event": event, "ts_ms": bar_close_ts, "price": price})

        if low <= trade.current_stop:
            if trade.tp1_hit:
                _close("BREAKEVEN_STOP", trade.current_stop, "BREAKEVEN_STOP")
            else:
                _close("STOP_LOSS", trade.current_stop, "STOP_LOSS")
            break

        if trade.status == "OPEN_FULL" and high >= trade.tp1:
            trade.status = "TP1_HIT_RUNNER"
            trade.tp1_hit = True
            trade.current_stop = trade.entry  # move stop to breakeven
            events.append({"event": "TP1_HIT", "ts_ms": bar_close_ts, "price": trade.tp1})

        if trade.status == "TP1_HIT_RUNNER" and high >= trade.tp2:
            _close("TP2_PWH", trade.tp2, "TP2_HIT")
            break

        if bar_close_ts >= trade.time_stop_ts_ms:
            _close("TIME_STOP", close, "TIME_STOP")
            break
    return events


# ============================================================================
# STATE PERSISTENCE
# ============================================================================

def _empty_state() -> Dict[str, Any]:
    return {
        "version": STATE_VERSION,
        "last_macro_approved": None,
        "last_traded_sweep_ts_ms": 0,
        "trade": None,
        "history": [],
        "events": [],
    }


def _trade_from_dict(data: Dict[str, Any]) -> Optional[SpotSwingTrade]:
    try:
        allowed = {f.name for f in fields(SpotSwingTrade)}
        return SpotSwingTrade(**{k: v for k, v in data.items() if k in allowed})
    except Exception:
        logger.warning("Ignoring unreadable spot swing trade in state file")
        return None


def load_state(path: os.PathLike) -> Dict[str, Any]:
    """Loads state.json; any corruption falls back to a clean state (never raises)."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            raw = json.load(fh)
        state = _empty_state()
        state.update({k: raw[k] for k in state if k in raw})
        return state
    except FileNotFoundError:
        return _empty_state()
    except Exception:
        logger.warning("Spot swing state file unreadable; starting from a clean state")
        return _empty_state()


def save_state(path: os.PathLike, state: Dict[str, Any]) -> None:
    """Atomic write (temp file + replace) so a crash can never leave a half-written state.json."""
    directory = os.path.dirname(os.path.abspath(path))
    os.makedirs(directory, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=directory, prefix=".spot_swing_", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(state, fh, indent=2, default=str)
        os.replace(tmp_path, path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


# ============================================================================
# ENGINE
# ============================================================================

def _utc_str(ts_ms: int) -> str:
    return datetime.fromtimestamp(ts_ms / 1000.0, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


class SpotSwingEngine:
    """Evaluates Tab [0] on every HUD tick; heavy work only re-runs when a new closed bar appears."""

    def __init__(
        self,
        config: EngineConfig,
        notifier: Optional[SpotSwingNotifier] = None,
        state_path: Optional[os.PathLike] = None,
        read_only: bool = False,
    ) -> None:
        self.config = config
        self.notifier = notifier if notifier is not None else SpotSwingNotifier.from_env()
        self.state_path = state_path or config.spot_swing_state_path
        self.read_only = read_only
        self.state: Dict[str, Any] = load_state(self.state_path)
        try:
            self.equity_usd = float(os.getenv("SPOT_SWING_EQUITY_USD", config.spot_swing_account_equity_usd))
        except ValueError:
            self.equity_usd = config.spot_swing_account_equity_usd
        self._cache_key: Optional[Tuple[Any, ...]] = None
        self._cache: Optional[Tuple[SpotSwingMacroGate, SpotSwingSetup]] = None

    # ------------------------------------------------------------------ helpers
    def set_read_only(self, read_only: bool) -> None:
        """Read-only mode (dry-run / cloud snapshot): no state writes, no alerts."""
        self.read_only = read_only

    def _persist(self) -> None:
        if self.read_only:
            return
        try:
            save_state(self.state_path, self.state)
        except Exception:
            logger.exception("Could not persist spot swing state")

    def _record_event(self, event: str, ts_ms: int, detail: str, payload: Dict[str, Any]) -> None:
        self.state["events"].append(
            {"event": event, "ts_ms": int(ts_ms), "detail": detail, "channels": self.notifier.describe_channels()}
        )
        self.state["events"] = self.state["events"][-MAX_EVENTS:]
        if not self.read_only:
            self.notifier.dispatch(payload)

    def _trade_payload(self, trade: SpotSwingTrade, risk: Optional[SpotSwingRisk]) -> Dict[str, Any]:
        d = asdict(trade)
        d["time_stop_utc"] = _utc_str(trade.time_stop_ts_ms)
        d["tp1_fraction"] = self.config.spot_swing_tp1_fraction
        if risk is not None:
            d.update(
                notional_usd=risk.notional_usd,
                equity_alloc_pct=risk.equity_alloc_pct,
                spot_capped=risk.spot_capped,
                atr14=risk.atr14,
            )
        return d

    def _base_payload(
        self,
        event: str,
        price: float,
        macro: Optional[SpotSwingMacroGate],
        setup: Optional[SpotSwingSetup],
        trade: Optional[SpotSwingTrade],
        risk: Optional[SpotSwingRisk],
        barrier_price: Optional[float] = None,
    ) -> Dict[str, Any]:
        return {
            "source": "btc_swing_engine/tab0_spot_swing",
            "event": event,
            "symbol": self.config.binance_symbol,
            "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            "price": price,
            "barrier_price": barrier_price,
            "macro": asdict(macro) if macro else None,
            "setup": asdict(setup) if setup else None,
            "trade": self._trade_payload(trade, risk) if trade else None,
        }

    def _not_ready(self, store: StateStore, price: float, notes: List[str], verdict: str) -> SpotSwingEvaluation:
        ev = SpotSwingEvaluation(
            timestamp_utc=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            spot_price=price,
            verdict=verdict,
            traffic_light="YELLOW",
            data_ready=False,
            data_notes=notes,
            trade=self._open_trade(),
            recent_events=self._recent_events(),
            alerts_enabled=self.notifier.enabled and not self.read_only,
            read_only=self.read_only,
            plain_english_summary="; ".join(notes),
            equity_usd=self.equity_usd,
            risk_pct=self.config.spot_swing_risk_pct,
        )
        store.spot_swing_evaluation = ev
        return ev

    def _open_trade(self) -> Optional[SpotSwingTrade]:
        data = self.state.get("trade")
        if not data:
            return None
        trade = _trade_from_dict(data)
        return trade if trade and trade.status != "CLOSED" else None

    def _recent_events(self, n: int = 6) -> List[str]:
        lines = []
        for e in self.state.get("events", [])[-n:][::-1]:
            lines.append(f"{_utc_str(e['ts_ms'])}  {e['event']}  {e.get('detail', '')}")
        return lines

    # ------------------------------------------------------------------ evaluation
    def evaluate(self, store: StateStore, now_ms: Optional[int] = None) -> Optional[SpotSwingEvaluation]:
        cfg = self.config
        now_ms = int(time.time() * 1000) if now_ms is None else int(now_ms)
        grace_ms = cfg.spot_swing_stale_grace_sec * 1000
        price = float(store.binance_spot_price or 0.0)

        # --- 1. Closed, verified bars ---
        df_1d = finalized_bars(bars_to_frame(list(store.spot_klines_1d)))
        df_4h = build_closed_4h_from_1h(list(store.spot_klines_1h))

        notes: List[str] = []
        if len(df_1d) < cfg.spot_swing_min_daily_bars:
            notes.append(f"1D history {len(df_1d)}/{cfg.spot_swing_min_daily_bars} closed bars")
        if len(df_4h) < cfg.spot_swing_min_4h_bars:
            notes.append(f"4H history {len(df_4h)}/{cfg.spot_swing_min_4h_bars} closed bars")
        if notes:
            return self._not_ready(store, price, notes, "WARMING UP")
        if not is_series_fresh(df_1d, TF_1D_MS, now_ms, grace_ms) or not is_series_fresh(df_4h, TF_4H_MS, now_ms, grace_ms):
            return self._not_ready(
                store, price, ["Kline feed is stale: newest closed bar is too old to evaluate"], "STALE DATA - SUSPENDED"
            )
        if price <= 0:
            price = float(df_4h["close"].iloc[-1])

        # --- 2. Heavy computation only when a new closed bar appears ---
        pwl, pwh, week_start, anchors_ready = compute_weekly_anchors(df_1d, now_ms)
        key = (
            int(df_1d["ts"].iloc[-1]),
            float(df_1d["close"].iloc[-1]),
            int(df_4h["ts"].iloc[-1]),
            float(df_4h["close"].iloc[-1]),
            week_start,
            int(self.state["last_traded_sweep_ts_ms"]),
        )
        if key == self._cache_key and self._cache is not None:
            macro, setup = self._cache
        else:
            macro = compute_macro_gate(
                df_1d,
                ema_fast=cfg.spot_swing_ema_fast,
                ema_slow=cfg.spot_swing_ema_slow,
                bbw_period=cfg.spot_swing_bbw_period,
                rank_window=cfg.spot_swing_bbw_rank_window,
                max_percentile=cfg.spot_swing_bbw_max_percentile,
                squeeze_lookback_bars=cfg.spot_swing_squeeze_lookback_bars,
            )
            if macro is None:
                return self._not_ready(store, price, ["Insufficient daily history for BBW percentile rank"], "WARMING UP")
            if anchors_ready:
                setup = detect_setup(
                    df_4h,
                    pwl,
                    pwh,
                    week_start,
                    window_bars=cfg.spot_swing_sweep_window_bars,
                    vol_sma_period=cfg.spot_swing_vol_sma_period,
                    last_traded_sweep_ts_ms=int(self.state["last_traded_sweep_ts_ms"]),
                )
            else:
                setup = SpotSwingSetup(
                    bar_ts_ms=int(df_4h["ts"].iloc[-1]),
                    close=float(df_4h["close"].iloc[-1]),
                    week_start_ms=week_start,
                    anchors_ready=False,
                )
            self._cache_key, self._cache = key, (macro, setup)

        risk: Optional[SpotSwingRisk] = None
        if setup.anchors_ready and setup.signal_active:
            risk = compute_risk(
                setup,
                df_4h,
                equity_usd=self.equity_usd,
                risk_pct=cfg.spot_swing_risk_pct,
                atr_period=cfg.spot_swing_atr_period,
                stop_atr_mult=cfg.spot_swing_stop_atr_mult,
                tp1_r_multiple=cfg.spot_swing_tp1_r_multiple,
                tp1_fraction=cfg.spot_swing_tp1_fraction,
                time_stop_days=cfg.spot_swing_time_stop_days,
            )

        # --- 3. Module E: state transitions + alerts (idempotent across restarts) ---
        mutated = False
        new_setup_now = False

        prev_approved = self.state.get("last_macro_approved")
        if prev_approved is None or bool(prev_approved) != macro.macro_approved:
            if prev_approved is True and not macro.macro_approved:
                reason = "trend" if not macro.trend_pass else "squeeze"
                self._record_event(
                    "MACRO_FROZEN",
                    now_ms,
                    f"gate failed ({reason}): 100% cash",
                    self._base_payload("MACRO_FROZEN", price, macro, setup, self._open_trade(), None),
                )
            elif prev_approved is False and macro.macro_approved:
                self.state["events"].append(
                    {"event": "MACRO_APPROVED", "ts_ms": now_ms, "detail": "gate re-opened", "channels": "log-only"}
                )
                self.state["events"] = self.state["events"][-MAX_EVENTS:]
            self.state["last_macro_approved"] = bool(macro.macro_approved)
            mutated = True

        trade = self._open_trade()
        if trade is not None:
            before = (trade.status, trade.last_processed_bar_ts_ms)
            barrier_events = advance_trade(trade, df_4h, cfg.spot_swing_tp1_fraction)
            for be in barrier_events:
                label = {
                    "TP1_HIT": "+2.0R partial; stop -> breakeven",
                    "TP2_HIT": "PWH structural target",
                    "STOP_LOSS": "initial stop hit",
                    "BREAKEVEN_STOP": "runner stopped at entry",
                    "TIME_STOP": "10-day holding limit",
                }.get(be["event"], "")
                self._record_event(
                    be["event"],
                    be["ts_ms"],
                    f"{label} @ ${be['price']:,.0f}",
                    self._base_payload(be["event"], price, macro, setup, trade, risk, barrier_price=be["price"]),
                )
            if (trade.status, trade.last_processed_bar_ts_ms) != before:
                mutated = True
                if trade.status == "CLOSED":
                    self.state["history"].append(asdict(trade))
                    self.state["history"] = self.state["history"][-MAX_HISTORY:]
                    self.state["trade"] = None
                    trade = None
                else:
                    self.state["trade"] = asdict(trade)

        if trade is None and macro.macro_approved and setup.is_fresh and risk is not None:
            trade = SpotSwingTrade(
                setup_id=f"{setup.week_start_ms}:{setup.sweep_bar_ts_ms}",
                status="OPEN_FULL",
                entry_ts_ms=setup.bar_ts_ms + TF_4H_MS,
                entry=risk.entry,
                initial_stop=risk.stop,
                current_stop=risk.stop,
                tp1=risk.tp1,
                tp2=risk.tp2_pwh,
                qty_btc=risk.qty_btc,
                time_stop_ts_ms=risk.time_stop_ts_ms,
                sweep_bar_ts_ms=setup.sweep_bar_ts_ms,
                last_processed_bar_ts_ms=setup.bar_ts_ms,
            )
            self.state["trade"] = asdict(trade)
            self.state["last_traded_sweep_ts_ms"] = setup.sweep_bar_ts_ms
            new_setup_now = True
            mutated = True
            self._record_event(
                "NEW_SETUP",
                trade.entry_ts_ms,
                f"entry ${risk.entry:,.0f} stop ${risk.stop:,.0f} size {risk.qty_btc:.4f} BTC",
                self._base_payload("NEW_SETUP", price, macro, setup, trade, risk),
            )
            self._cache_key = None  # last_traded_sweep changed -> recompute freshness next tick

        if mutated:
            self._persist()

        # --- 4. Daily Liquidation Magnet Protocol (Master Prompt Steps 1-4 + RRR 1:3) & Verdict ---
        magnet = compute_magnet_protocol(
            df_1d_closed=df_1d,
            df_4h_closed=df_4h,
            price=price,
            macro=macro,
            setup=setup,
            store=store,
            config=cfg,
            equity_usd=self.equity_usd,
            risk_pct=cfg.spot_swing_risk_pct,
            min_rrr=getattr(cfg, "spot_swing_min_rrr", 3.0),
            range_lookback_days=getattr(cfg, "spot_swing_range_lookback_days", 35),
            trade=trade,
        )
        if risk is not None:
            risk.short_liq_magnet = magnet.short_liq_magnet
            risk.rrr_to_magnet = max(0.0, max(magnet.short_liq_magnet, setup.pwh) - risk.entry) / max(risk.stop_distance, 1e-9)
            risk.rrr_meets_min = bool(risk.rrr_to_magnet >= magnet.min_required_rrr)
            risk.max_entry_for_3r = (max(magnet.short_liq_magnet, setup.pwh) + magnet.min_required_rrr * risk.stop) / (1.0 + magnet.min_required_rrr)

        verdict, light, summary = self._compose_verdict(macro, setup, risk, trade, new_setup_now, price)
        ev = SpotSwingEvaluation(
            timestamp_utc=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            spot_price=price,
            verdict=verdict,
            traffic_light=light,
            data_ready=True,
            data_notes=[] if setup.anchors_ready else ["Previous-week anchors syncing (need all 7 daily bars)"],
            macro=macro,
            setup=setup,
            risk=risk,
            trade=trade,
            recent_events=self._recent_events(),
            alerts_enabled=self.notifier.enabled and not self.read_only,
            read_only=self.read_only,
            plain_english_summary=summary,
            equity_usd=self.equity_usd,
            risk_pct=cfg.spot_swing_risk_pct,
            magnet=magnet,
        )
        store.spot_swing_evaluation = ev
        return ev

    @staticmethod
    def _compose_verdict(
        macro: SpotSwingMacroGate,
        setup: SpotSwingSetup,
        risk: Optional[SpotSwingRisk],
        trade: Optional[SpotSwingTrade],
        new_setup_now: bool,
        price: float,
    ) -> Tuple[str, str, str]:
        if trade is not None:
            frozen_note = " Macro gate is now FROZEN: manage the open trade, open nothing new." if not macro.macro_approved else ""
            if new_setup_now:
                return (
                    "NEW LONG SETUP",
                    "GREEN",
                    f"Sweep of PWL ${setup.pwl:,.0f} reclaimed on volume. Entry ${trade.entry:,.0f}, stop ${trade.initial_stop:,.0f}, "
                    f"size {trade.qty_btc:.4f} BTC.{frozen_note}",
                )
            runner = "runner active, stop at breakeven" if trade.tp1_hit else "waiting for +2.0R"
            return (
                f"IN TRADE ({trade.status})",
                "GREEN",
                f"Open long from ${trade.entry:,.0f}; stop ${trade.current_stop:,.0f}; {runner}; PWH target ${trade.tp2:,.0f}.{frozen_note}",
            )
        if not macro.macro_approved:
            failed = []
            if not macro.trend_pass:
                failed.append("trend (close > EMA50 > EMA200) fails")
            if not macro.compression_pass:
                failed.append(f"volatility is not compressed (BBW rank {macro.bbw_percentile * 100:.0f}% > 30%)")
            return ("FROZEN (100% CASH)", "RED", "Macro gate closed: " + " and ".join(failed) + ". Stay in cash.")
        if not setup.anchors_ready:
            return ("MACRO APPROVED - ANCHORS SYNCING", "YELLOW", "Waiting for a complete previous-week range.")
        if setup.signal_active and not setup.is_fresh:
            return (
                "MACRO APPROVED - SETUP ALREADY ACTED",
                "BLUE",
                "The sweep that produced this reclaim was already traded; waiting for a fresh sweep of PWL.",
            )
        if setup.signal_active and risk is None:
            return ("SIGNAL BLOCKED - INVALID STOP", "YELLOW", "Reclaim confirmed but the ATR stop geometry is invalid.")
        if setup.sweep_detected:
            missing = []
            if not setup.reclaim_confirmed:
                missing.append("a 4H close back above PWL")
            if not setup.volume_confirmed:
                missing.append("reclaim-bar volume above SMA(3)")
            return ("SWEEP DETECTED - AWAITING RECLAIM", "YELLOW", "PWL was swept; still need " + " and ".join(missing) + ".")
        return (
            "MACRO APPROVED - SCANNING",
            "BLUE",
            f"Gate open. Waiting for a 4H wick below PWL ${setup.pwl:,.0f} followed by a volume-backed reclaim.",
        )
