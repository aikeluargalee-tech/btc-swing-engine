"""BTC Trend-Pullback Strategy v1.0 — Independent Spot Swing Research Engine.

Classification:
- BTCUSDT Spot Swing Trading (Long-Only, No Leverage, No Shorting, No Auto-Execution)
- Holding Horizon: Several days to several weeks
- Status: UNVALIDATED — RESEARCH / PAPER MODE
- Default Decision: NO TRADE

Strictly uses closed (completed) candles for signal generation, fails closed on
missing/stale/corrupt data, and calculates its verdict independently of all other
specialist tabs.
"""

from __future__ import annotations

import logging
import math
import os
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from config.settings import EngineConfig
from core.models import KlineBar, TrendPullbackEvaluation
from core.state_store import StateStore

logger = logging.getLogger("strategy_trend_pullback")

TF_1H_MS = 3_600_000
TF_4H_MS = 4 * TF_1H_MS
TF_1D_MS = 24 * TF_1H_MS

MYT_TZ = timezone(timedelta(hours=8))


@dataclass
class TrendPullbackConfig:
    """Configurable parameters for BTC Trend-Pullback v1.0 (Section 13 defaults)."""
    daily_sma_period: int = 200
    daily_sma_slope_period: int = 20
    ema_fast: int = 50
    ema_slow: int = 200
    ema_slope_period: int = 6
    atr_period: int = 14
    pullback_upper_atr: float = 0.25
    pullback_lower_atr: float = 0.50
    recovery_max_extension_atr: float = 1.00
    limit_entry_upper_atr: float = 0.10
    stop_lookback: int = 5
    stop_buffer_atr: float = 0.25
    minimum_stop_atr: float = 0.75
    maximum_stop_atr: float = 3.00
    risk_per_trade: float = 0.005
    initial_simulation_equity: float = 100_000.0
    setup_expiry_4h_bars: int = 3
    entry_fee_pct: float = 0.0010
    exit_fee_pct: float = 0.0010
    entry_slippage_pct: float = 0.0005
    exit_slippage_pct: float = 0.0005
    max_daily_stale_hours: float = 48.0
    max_4h_stale_hours: float = 8.5

    @classmethod
    def from_yaml(cls, path: Optional[os.PathLike] = None) -> "TrendPullbackConfig":
        """Loads configuration from YAML if available; falls back to locked defaults."""
        cfg = cls()
        if path is None:
            path = Path(__file__).resolve().parent.parent / "config" / "trend_pullback_config.yaml"
        else:
            path = Path(path)
        if not path.is_file():
            return cfg
        try:
            with open(path, "r", encoding="utf-8") as fh:
                for raw_line in fh:
                    line = raw_line.split("#", 1)[0].strip()
                    if not line or ":" not in line:
                        continue
                    k, v = [x.strip().strip('"').strip("'") for x in line.split(":", 1)]
                    if hasattr(cfg, k):
                        cur_val = getattr(cfg, k)
                        if isinstance(cur_val, int):
                            setattr(cfg, k, int(float(v)))
                        elif isinstance(cur_val, float):
                            setattr(cfg, k, float(v))
        except Exception as exc:
            logger.debug("Using default TrendPullbackConfig (YAML load skipped: %s)", exc)
        return cfg


# ============================================================================
# INDICATOR & DATA INTEGRITY UTILITIES
# ============================================================================

def compute_sma_series(values: Sequence[float], period: int) -> List[float]:
    """Computes simple moving average series. Indices < period - 1 are NaN."""
    n = len(values)
    if n < period or period <= 0:
        return [float("nan")] * n
    out = [float("nan")] * n
    running_sum = sum(values[:period])
    out[period - 1] = running_sum / period
    for i in range(period, n):
        running_sum += values[i] - values[i - period]
        out[i] = running_sum / period
    return out


def compute_ema_series(values: Sequence[float], period: int) -> List[float]:
    """Computes standard Exponential Moving Average series seeded with SMA(period)."""
    n = len(values)
    if n < period or period <= 0:
        return [float("nan")] * n
    out = [float("nan")] * n
    sma_seed = sum(values[:period]) / period
    out[period - 1] = sma_seed
    mult = 2.0 / (period + 1.0)
    for i in range(period, n):
        out[i] = (values[i] - out[i - 1]) * mult + out[i - 1]
    return out


def compute_atr_series(bars: Sequence[KlineBar], period: int = 14) -> List[float]:
    """Computes Wilder's ATR series over completed bars."""
    n = len(bars)
    if n < period + 1 or period <= 0:
        return [float("nan")] * n
    tr = [0.0] * n
    tr[0] = bars[0].high - bars[0].low
    for i in range(1, n):
        prev_c = bars[i - 1].close
        tr[i] = max(
            bars[i].high - bars[i].low,
            abs(bars[i].high - prev_c),
            abs(bars[i].low - prev_c),
        )
    out = [float("nan")] * n
    first_atr = sum(tr[1 : period + 1]) / period
    out[period] = first_atr
    for i in range(period + 1, n):
        out[i] = (out[i - 1] * (period - 1) + tr[i]) / period
    return out


def synthesize_closed_4h_from_1h(
    bars_1h: Sequence[KlineBar],
    now_ms: int,
) -> List[KlineBar]:
    """Synthesizes completed 4H candles from 1H bars when dedicated 4H history is short."""
    if not bars_1h:
        return []
    buckets: Dict[int, List[KlineBar]] = {}
    for b in bars_1h:
        b_key = (int(b.timestamp_ms) // TF_4H_MS) * TF_4H_MS
        buckets.setdefault(b_key, []).append(b)

    sorted_keys = sorted(buckets.keys())
    out: List[KlineBar] = []
    for idx, b_key in enumerate(sorted_keys):
        grp = buckets[b_key]
        # A 4H bucket is complete only if its close boundary has passed (or a successor bucket exists)
        # and it has all 4 constituent 1H candles.
        has_successor = idx < len(sorted_keys) - 1
        is_past_close = now_ms >= (b_key + TF_4H_MS)
        if (has_successor or is_past_close) and len(grp) == 4:
            out.append(
                KlineBar(
                    timestamp_ms=b_key,
                    open=grp[0].open,
                    high=max(x.high for x in grp),
                    low=min(x.low for x in grp),
                    close=grp[-1].close,
                    volume=sum(x.volume for x in grp),
                    taker_buy_volume=sum(x.taker_buy_volume for x in grp),
                )
            )
    return out


def verify_and_extract_completed_candles(
    bars: Sequence[KlineBar],
    tf_ms: int,
    min_required: int,
    now_ms: int,
    max_stale_hours: float,
    label: str = "Candle",
) -> Tuple[bool, str, List[KlineBar], str]:
    """Verifies candle completeness, timestamps, duplicates, gaps, NaNs, and freshness.

    Never includes an incomplete (currently forming) candle in the returned completed list.
    Returns (is_valid, status_label, completed_bars, failure_reason).
    """
    if not bars:
        return False, "UNAVAILABLE", [], f"{label} series is empty or missing."

    # 1. Validate OHLCV numeric integrity and timestamp ordering
    seen_ts = set()
    for b in bars:
        vals = (b.open, b.high, b.low, b.close, b.volume)
        if any(v is None or not math.isfinite(float(v)) for v in vals):
            return False, "UNAVAILABLE", [], f"{label} contains NaN or non-finite values."
        if b.open <= 0 or b.high <= 0 or b.low <= 0 or b.close <= 0:
            return False, "UNAVAILABLE", [], f"{label} contains non-positive OHLC prices."
        if b.high < b.low or b.high < max(b.open, b.close) or b.low > min(b.open, b.close):
            return False, "UNAVAILABLE", [], f"{label} has inconsistent high/low candle bounds."
        ts = int(b.timestamp_ms)
        if ts in seen_ts:
            return False, "UNAVAILABLE", [], f"{label} contains duplicate timestamp ({ts})."
        seen_ts.add(ts)

    sorted_bars = sorted(bars, key=lambda x: int(x.timestamp_ms))

    # 2. Filter strictly to completed (closed) candles
    # A candle with open timestamp `ts` closes at `ts + tf_ms`.
    # If `now_ms < ts + tf_ms` or `getattr(b, 'is_closed', True) is False`, it is still forming!
    completed: List[KlineBar] = []
    for b in sorted_bars:
        explicit_closed = getattr(b, "is_closed", True)
        if not explicit_closed:
            continue
        if int(b.timestamp_ms) + tf_ms <= now_ms:
            completed.append(b)

    if len(completed) < min_required:
        return (
            False,
            "UNAVAILABLE",
            completed,
            f"Insufficient completed {label} bars ({len(completed)} available, {min_required} required).",
        )

    # 3. Check for missing candle gaps in the recent evaluation window (last 25 completed bars)
    check_window = completed[-min(len(completed), 25):]
    for i in range(1, len(check_window)):
        delta_ms = int(check_window[i].timestamp_ms) - int(check_window[i - 1].timestamp_ms)
        if delta_ms > int(tf_ms * 1.5):
            return (
                False,
                "UNAVAILABLE",
                completed,
                f"Missing {label} gap detected ({delta_ms // tf_ms} bars missing).",
            )

    # 4. Stale data check
    last_close_ms = int(completed[-1].timestamp_ms) + tf_ms
    age_hours = (now_ms - last_close_ms) / 3_600_000.0
    if age_hours > max_stale_hours:
        return (
            False,
            "STALE",
            completed,
            f"{label} data is stale (last completed close {age_hours:.1f}h ago > {max_stale_hours:.1f}h limit).",
        )

    return True, "LAST CLOSE", completed, ""


def _inspect_forming_candles(
    bars: Sequence[KlineBar],
    tf_ms: int,
    now_ms: int,
) -> Tuple[bool, str]:
    """Checks whether any incomplete/forming candle was present and excluded from completed bars."""
    if not bars:
        return False, "None"
    forming_ts: List[int] = []
    for b in bars:
        ts = int(b.timestamp_ms)
        explicit_closed = getattr(b, "is_closed", True)
        if not explicit_closed or (ts + tf_ms > now_ms):
            forming_ts.append(ts)
    if not forming_ts:
        return False, "None (all input bars already closed)"
    latest_forming = max(forming_ts)
    open_str = datetime.fromtimestamp(latest_forming / 1000.0, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return True, open_str



# ============================================================================
# CORE STRATEGY FUNCTIONS (SECTION 10 MODULAR SPECIFICATION)
# ============================================================================

def calculate_regime(
    completed_1d_bars: Sequence[KlineBar],
    cfg: Optional[TrendPullbackConfig] = None,
) -> Dict[str, Any]:
    """Section 4A: Evaluates Daily Regime Filter using completed 1D candles only.

    Bullish regime requires BOTH:
    1. Last completed daily close > Daily SMA200.
    2. Current Daily SMA200 > Daily SMA200 from 20 completed daily candles earlier.
    """
    cfg = cfg or TrendPullbackConfig()
    min_bars = cfg.daily_sma_period + cfg.daily_sma_slope_period
    if len(completed_1d_bars) < min_bars:
        return {
            "regime": "NOT BULLISH",
            "valid": False,
            "last_close": 0.0,
            "sma200": 0.0,
            "sma200_prev20": 0.0,
            "sma200_slope_20d": 0.0,
            "close_above_sma200": False,
            "sma200_rising": False,
            "sma200_series": [],
            "reason": f"Insufficient completed 1D candles ({len(completed_1d_bars)} < {min_bars})",
        }

    closes = [float(b.close) for b in completed_1d_bars]
    sma200_series = compute_sma_series(closes, cfg.daily_sma_period)
    sma200_now = sma200_series[-1]
    sma200_prev20 = sma200_series[-1 - cfg.daily_sma_slope_period]
    last_close = closes[-1]

    if not (math.isfinite(sma200_now) and math.isfinite(sma200_prev20)):
        return {
            "regime": "NOT BULLISH",
            "valid": False,
            "last_close": last_close,
            "sma200": 0.0,
            "sma200_prev20": 0.0,
            "sma200_slope_20d": 0.0,
            "close_above_sma200": False,
            "sma200_rising": False,
            "sma200_series": sma200_series,
            "reason": "Daily SMA200 series contains NaN",
        }

    close_above = bool(last_close > sma200_now)
    sma_rising = bool(sma200_now > sma200_prev20)
    is_bullish = bool(close_above and sma_rising)
    slope_20d = sma200_now - sma200_prev20

    reasons = []
    if not close_above:
        reasons.append(f"1D close (${last_close:,.2f}) <= SMA200 (${sma200_now:,.2f})")
    if not sma_rising:
        reasons.append(f"1D SMA200 (${sma200_now:,.2f}) <= 20d prior (${sma200_prev20:,.2f})")

    return {
        "regime": "BULLISH" if is_bullish else "NOT BULLISH",
        "valid": True,
        "last_close": last_close,
        "sma200": sma200_now,
        "sma200_prev20": sma200_prev20,
        "sma200_slope_20d": slope_20d,
        "close_above_sma200": close_above,
        "sma200_rising": sma_rising,
        "sma200_series": sma200_series,
        "reason": "Daily regime BULLISH (Close > rising SMA200)" if is_bullish else "; ".join(reasons),
    }


def calculate_trend(
    completed_4h_bars: Sequence[KlineBar],
    cfg: Optional[TrendPullbackConfig] = None,
) -> Dict[str, Any]:
    """Section 4B: Evaluates 4H Trend Filter using completed 4H candles only.

    All conditions required:
    1. EMA50 > EMA200.
    2. EMA50 > EMA50 six completed 4H candles earlier.
    3. Last completed 4H close > EMA200.
    """
    cfg = cfg or TrendPullbackConfig()
    min_bars = cfg.ema_slow + cfg.ema_slope_period
    if len(completed_4h_bars) < min_bars:
        return {
            "trend": "NOT CONFIRMED",
            "valid": False,
            "ema50": 0.0,
            "ema50_prev6": 0.0,
            "ema50_slope_6bars": 0.0,
            "ema200": 0.0,
            "atr14": 0.0,
            "last_close": 0.0,
            "ema50_above_ema200": False,
            "ema50_rising_6bars": False,
            "close_above_ema200": False,
            "ema50_series": [],
            "ema200_series": [],
            "atr14_series": [],
            "reason": f"Insufficient completed 4H candles ({len(completed_4h_bars)} < {min_bars})",
        }

    closes = [float(b.close) for b in completed_4h_bars]
    ema50_series = compute_ema_series(closes, cfg.ema_fast)
    ema200_series = compute_ema_series(closes, cfg.ema_slow)
    atr14_series = compute_atr_series(completed_4h_bars, cfg.atr_period)

    ema50_now = ema50_series[-1]
    ema50_prev6 = ema50_series[-1 - cfg.ema_slope_period]
    ema200_now = ema200_series[-1]
    atr14_now = atr14_series[-1]
    last_close = closes[-1]

    if not all(math.isfinite(x) and x > 0 for x in (ema50_now, ema50_prev6, ema200_now, atr14_now)):
        return {
            "trend": "NOT CONFIRMED",
            "valid": False,
            "ema50": 0.0,
            "ema50_prev6": 0.0,
            "ema50_slope_6bars": 0.0,
            "ema200": 0.0,
            "atr14": 0.0,
            "last_close": last_close,
            "ema50_above_ema200": False,
            "ema50_rising_6bars": False,
            "close_above_ema200": False,
            "ema50_series": ema50_series,
            "ema200_series": ema200_series,
            "atr14_series": atr14_series,
            "reason": "4H indicator series contains NaN or non-positive values",
        }

    c1 = bool(ema50_now > ema200_now)
    c2 = bool(ema50_now > ema50_prev6)
    c3 = bool(last_close > ema200_now)
    confirmed = bool(c1 and c2 and c3)

    reasons = []
    if not c1:
        reasons.append(f"4H EMA50 (${ema50_now:,.2f}) <= EMA200 (${ema200_now:,.2f})")
    if not c2:
        reasons.append(f"4H EMA50 not rising over 6 bars (${ema50_now:,.2f} <= ${ema50_prev6:,.2f})")
    if not c3:
        reasons.append(f"4H close (${last_close:,.2f}) <= EMA200 (${ema200_now:,.2f})")

    return {
        "trend": "CONFIRMED" if confirmed else "NOT CONFIRMED",
        "valid": True,
        "ema50": ema50_now,
        "ema50_prev6": ema50_prev6,
        "ema50_slope_6bars": ema50_now - ema50_prev6,
        "ema200": ema200_now,
        "atr14": atr14_now,
        "last_close": last_close,
        "ema50_above_ema200": c1,
        "ema50_rising_6bars": c2,
        "close_above_ema200": c3,
        "ema50_series": ema50_series,
        "ema200_series": ema200_series,
        "atr14_series": atr14_series,
        "reason": "4H trend CONFIRMED (EMA50 > EMA200, rising, Close > EMA200)" if confirmed else "; ".join(reasons),
    }


def _check_single_bar_recovery(
    bar: KlineBar,
    ema50: float,
    atr14: float,
    cfg: TrendPullbackConfig,
) -> Tuple[bool, str]:
    """Evaluates whether a single completed 4H candle satisfies all 4 pullback recovery criteria."""
    upper_bound = ema50 + (cfg.pullback_upper_atr * atr14)
    lower_bound = ema50 - (cfg.pullback_lower_atr * atr14)
    max_ext = ema50 + (cfg.recovery_max_extension_atr * atr14)

    # 1. Low enters acceptable pullback zone [EMA50 - 0.50*ATR, EMA50 + 0.25*ATR]
    if bar.low < lower_bound:
        return False, f"Deep pullback rejected: candle low (${bar.low:,.2f}) fell below lower zone (${lower_bound:,.2f})"
    if bar.low > upper_bound:
        return False, f"No pullback: candle low (${bar.low:,.2f}) remained above pullback zone (${upper_bound:,.2f})"

    # 2. Close is above EMA50
    if bar.close <= ema50:
        return False, f"No recovery: candle close (${bar.close:,.2f}) <= EMA50 (${ema50:,.2f})"

    # 3. Close is above Open (bullish candle)
    if bar.close <= bar.open:
        return False, f"Bearish/doji candle rejected: close (${bar.close:,.2f}) <= open (${bar.open:,.2f})"

    # 4. Close is not more than 1.0 ATR above EMA50 (anti-breakout-chasing)
    if bar.close > max_ext:
        return False, f"Breakout chasing rejected: close (${bar.close:,.2f}) > EMA50 + 1.0 ATR (${max_ext:,.2f})"

    return True, "Valid 4H pullback & recovery candle confirmed"


def detect_pullback(
    completed_4h_bars: Sequence[KlineBar],
    ema50_series: Sequence[float],
    atr14_series: Sequence[float],
    cfg: Optional[TrendPullbackConfig] = None,
) -> Dict[str, Any]:
    """Section 4C & 4D: Evaluates Pullback Zone, Recovery Candle, and 3-Bar Setup Expiry."""
    cfg = cfg or TrendPullbackConfig()
    if not completed_4h_bars or not ema50_series or not atr14_series:
        return {
            "pullback_zone_lower": 0.0,
            "pullback_zone_upper": 0.0,
            "max_extension_price": 0.0,
            "recovery_candle": "NOT CONFIRMED",
            "setup_status": "WAIT",
            "bars_since_recovery": -1,
            "reason": "Insufficient data for pullback detection",
        }

    ema50_now = float(ema50_series[-1])
    atr14_now = float(atr14_series[-1])
    upper_bound = ema50_now + (cfg.pullback_upper_atr * atr14_now)
    lower_bound = ema50_now - (cfg.pullback_lower_atr * atr14_now)
    max_ext = ema50_now + (cfg.recovery_max_extension_atr * atr14_now)

    # Check the last completed 4H candle first (offset = 0)
    last_bar = completed_4h_bars[-1]
    ok_now, reason_now = _check_single_bar_recovery(last_bar, ema50_now, atr14_now, cfg)
    if ok_now:
        return {
            "pullback_zone_lower": lower_bound,
            "pullback_zone_upper": upper_bound,
            "max_extension_price": max_ext,
            "recovery_candle": "CONFIRMED",
            "setup_status": "CONFIRMED",
            "bars_since_recovery": 0,
            "reason": reason_now,
        }

    # Check trailing completed 4H bars to determine if an active setup is still within the 3-bar window or has expired
    max_lookback = min(len(completed_4h_bars), cfg.setup_expiry_4h_bars + 4)
    for offset in range(1, max_lookback):
        idx = len(completed_4h_bars) - 1 - offset
        b = completed_4h_bars[idx]
        e50 = float(ema50_series[idx])
        a14 = float(atr14_series[idx])
        if not (math.isfinite(e50) and math.isfinite(a14) and a14 > 0):
            continue
        ok_hist, _ = _check_single_bar_recovery(b, e50, a14, cfg)
        if ok_hist:
            # Verify subsequent bars have not invalidated structure by closing below EMA50
            subsequent_bars = completed_4h_bars[idx + 1 :]
            subsequent_emas = ema50_series[idx + 1 :]
            broken = any(sb.close < se for sb, se in zip(subsequent_bars, subsequent_emas))
            if broken:
                break
            if offset <= cfg.setup_expiry_4h_bars:
                return {
                    "pullback_zone_lower": lower_bound,
                    "pullback_zone_upper": upper_bound,
                    "max_extension_price": max_ext,
                    "recovery_candle": "CONFIRMED",
                    "setup_status": "CONFIRMED",
                    "bars_since_recovery": offset,
                    "reason": f"Recovery candle confirmed {offset} bar(s) ago (valid up to {cfg.setup_expiry_4h_bars} bars)",
                }
            return {
                "pullback_zone_lower": lower_bound,
                "pullback_zone_upper": upper_bound,
                "max_extension_price": max_ext,
                "recovery_candle": "NOT CONFIRMED",
                "setup_status": "EXPIRED",
                "bars_since_recovery": offset,
                "reason": f"Setup expired: {offset} completed 4H bars elapsed since recovery (> {cfg.setup_expiry_4h_bars} bar limit)",
            }

    return {
        "pullback_zone_lower": lower_bound,
        "pullback_zone_upper": upper_bound,
        "max_extension_price": max_ext,
        "recovery_candle": "NOT CONFIRMED",
        "setup_status": "WAIT",
        "bars_since_recovery": -1,
        "reason": reason_now,
    }


def calculate_entry_zone(
    ema50_4h: float,
    atr14_4h: float,
    cfg: Optional[TrendPullbackConfig] = None,
) -> Dict[str, float]:
    """Section 4D: Calculates suggested manual limit-entry zone [EMA50, EMA50 + 0.10*ATR14]."""
    cfg = cfg or TrendPullbackConfig()
    if ema50_4h <= 0 or atr14_4h <= 0:
        return {"entry_low": 0.0, "entry_high": 0.0, "reference_entry": 0.0}
    low = float(ema50_4h)
    high = float(ema50_4h + cfg.limit_entry_upper_atr * atr14_4h)
    return {
        "entry_low": round(low, 2),
        "entry_high": round(high, 2),
        "reference_entry": round(high, 2),
    }


def calculate_stop(
    completed_4h_bars: Sequence[KlineBar],
    atr14_4h: float,
    entry_price: float,
    cfg: Optional[TrendPullbackConfig] = None,
) -> Dict[str, Any]:
    """Section 5: Calculates initial structural stop and validates [0.75 ATR, 3.00 ATR] bounds.

    Formula:
      lowest_low_5bars = round(min(low of last 5 completed 4H candles), 2)
      stop_buffer_usd  = round(0.25 * ATR14, 2)
      stop_price       = round(lowest_low_5bars - stop_buffer_usd, 2)
      stop_distance_usd = round(round(entry_price, 2) - stop_price, 2)
      stop_distance_atr_exact = stop_distance_usd / ATR14
    """
    cfg = cfg or TrendPullbackConfig()
    if len(completed_4h_bars) < cfg.stop_lookback or atr14_4h <= 0 or entry_price <= 0:
        return {
            "lowest_low_5bars": 0.0,
            "atr14_used": 0.0,
            "stop_buffer_usd": 0.0,
            "stop_price": 0.0,
            "stop_distance_usd": 0.0,
            "stop_distance_atr": 0.0,
            "stop_distance_atr_exact": 0.0,
            "valid": False,
            "reason": "Insufficient bars or invalid entry/ATR for stop calculation",
        }

    recent = completed_4h_bars[-cfg.stop_lookback :]
    lowest_low = round(min(float(b.low) for b in recent), 2)
    stop_buffer_usd = round(cfg.stop_buffer_atr * float(atr14_4h), 2)
    stop_price = round(lowest_low - stop_buffer_usd, 2)
    entry_px = round(float(entry_price), 2)
    stop_dist_usd = round(entry_px - stop_price, 2)
    stop_dist_atr_exact = stop_dist_usd / float(atr14_4h)
    stop_dist_atr_check = round(stop_dist_atr_exact, 8)
    stop_dist_atr = round(stop_dist_atr_exact, 2)

    base_out = {
        "lowest_low_5bars": lowest_low,
        "atr14_used": round(float(atr14_4h), 2),
        "stop_buffer_usd": stop_buffer_usd,
        "stop_price": stop_price,
        "stop_distance_usd": stop_dist_usd,
        "stop_distance_atr": stop_dist_atr,
        "stop_distance_atr_exact": round(stop_dist_atr_exact, 4),
    }

    if stop_price >= entry_px:
        return {
            **base_out,
            "valid": False,
            "reason": f"Stop rejected: structural stop (${stop_price:,.2f}) is at or above entry (${entry_px:,.2f})",
        }

    if stop_dist_atr_check < cfg.minimum_stop_atr:
        return {
            **base_out,
            "valid": False,
            "reason": (
                f"Stop rejected: distance ({stop_dist_atr:.2f} ATR / exact {stop_dist_atr_exact:.4f} ATR) "
                f"< minimum {cfg.minimum_stop_atr:.2f} ATR"
            ),
        }

    if stop_dist_atr_check > cfg.maximum_stop_atr:
        return {
            **base_out,
            "valid": False,
            "reason": (
                f"Stop rejected: distance ({stop_dist_atr:.2f} ATR / exact {stop_dist_atr_exact:.4f} ATR) "
                f"> maximum {cfg.maximum_stop_atr:.2f} ATR"
            ),
        }

    return {
        **base_out,
        "valid": True,
        "reason": (
            f"Stop valid ({stop_dist_atr:.2f} ATR / exact {stop_dist_atr_exact:.4f} ATR within "
            f"{cfg.minimum_stop_atr:.2f}-{cfg.maximum_stop_atr:.2f} ATR bounds)"
        ),
    }


def calculate_position_size(
    entry_price: float,
    stop_price: float,
    cfg: Optional[TrendPullbackConfig] = None,
) -> Dict[str, float]:
    """Section 6: Calculates unleveraged spot position size with full fee & slippage audit breakdown.

    Guarantees:
      1. Total estimated loss (gross price risk + entry/exit fees + entry/exit slippage) <= risk_budget_usd ($500.00).
      2. Position notional <= equity_usd ($100,000.00, 0.0x leverage).
      3. All displayed per-BTC and USD risk components reconcile to the cent.
    """
    cfg = cfg or TrendPullbackConfig()
    equity = round(float(cfg.initial_simulation_equity), 2)
    risk_budget = round(equity * float(cfg.risk_per_trade), 2)
    entry_px = round(float(entry_price), 2)
    stop_px = round(float(stop_price), 2)

    if entry_px <= 0 or stop_px <= 0 or stop_px >= entry_px:
        return {
            "equity_usd": equity,
            "risk_budget_usd": risk_budget,
            "sizing_entry_price": entry_px if entry_px > 0 else 0.0,
            "sizing_stop_price": stop_px if stop_px > 0 else 0.0,
            "gross_price_risk_per_btc": 0.0,
            "entry_fee_per_btc": 0.0,
            "exit_fee_per_btc": 0.0,
            "entry_slippage_per_btc": 0.0,
            "exit_slippage_per_btc": 0.0,
            "cost_allowance_per_btc": 0.0,
            "total_risk_per_btc": 0.0,
            "gross_price_risk_usd": 0.0,
            "entry_fee_usd": 0.0,
            "exit_fee_usd": 0.0,
            "entry_slippage_usd": 0.0,
            "exit_slippage_usd": 0.0,
            "total_estimated_risk_usd": 0.0,
            "position_size_btc": 0.0,
            "position_value_usd": 0.0,
        }

    gross_risk_per_btc = round(entry_px - stop_px, 2)
    entry_fee_per_btc = entry_px * float(cfg.entry_fee_pct)
    exit_fee_per_btc = stop_px * float(cfg.exit_fee_pct)
    entry_slip_per_btc = entry_px * float(cfg.entry_slippage_pct)
    exit_slip_per_btc = stop_px * float(cfg.exit_slippage_pct)
    cost_allowance_per_btc = entry_fee_per_btc + exit_fee_per_btc + entry_slip_per_btc + exit_slip_per_btc
    total_risk_per_btc = gross_risk_per_btc + cost_allowance_per_btc

    raw_qty = risk_budget / total_risk_per_btc
    max_spot_qty = equity / entry_px

    # Floor to 5 decimal places (0.00001 BTC step) so total loss never exceeds risk_budget
    final_qty = math.floor(min(raw_qty, max_spot_qty) * 100_000.0 + 1e-12) / 100_000.0

    def _compute_usd_breakdown(qty: float) -> Tuple[float, float, float, float, float, float, float]:
        val_usd = round(qty * entry_px, 2)
        g_usd = round(qty * gross_risk_per_btc, 2)
        ef_usd = round(qty * entry_fee_per_btc, 2)
        xf_usd = round(qty * exit_fee_per_btc, 2)
        es_usd = round(qty * entry_slip_per_btc, 2)
        xs_usd = round(qty * exit_slip_per_btc, 2)
        tot_usd = round(g_usd + ef_usd + xf_usd + es_usd + xs_usd, 2)
        return val_usd, g_usd, ef_usd, xf_usd, es_usd, xs_usd, tot_usd

    val_usd, g_usd, ef_usd, xf_usd, es_usd, xs_usd, tot_usd = _compute_usd_breakdown(final_qty)
    while final_qty > 0.0 and (tot_usd > risk_budget or val_usd > equity):
        final_qty = round(max(0.0, final_qty - 0.00001), 5)
        val_usd, g_usd, ef_usd, xf_usd, es_usd, xs_usd, tot_usd = _compute_usd_breakdown(final_qty)

    return {
        "equity_usd": equity,
        "risk_budget_usd": risk_budget,
        "sizing_entry_price": entry_px,
        "sizing_stop_price": stop_px,
        "gross_price_risk_per_btc": round(gross_risk_per_btc, 2),
        "entry_fee_per_btc": round(entry_fee_per_btc, 2),
        "exit_fee_per_btc": round(exit_fee_per_btc, 2),
        "entry_slippage_per_btc": round(entry_slip_per_btc, 2),
        "exit_slippage_per_btc": round(exit_slip_per_btc, 2),
        "cost_allowance_per_btc": round(cost_allowance_per_btc, 2),
        "total_risk_per_btc": round(total_risk_per_btc, 2),
        "gross_price_risk_usd": g_usd,
        "entry_fee_usd": ef_usd,
        "exit_fee_usd": xf_usd,
        "entry_slippage_usd": es_usd,
        "exit_slippage_usd": xs_usd,
        "total_estimated_risk_usd": tot_usd,
        "position_size_btc": round(final_qty, 5),
        "position_value_usd": val_usd,
    }


def evaluate_exit(
    current_price: float,
    stop_price: float,
    completed_4h_bars: Sequence[KlineBar],
    ema50_4h_series: Sequence[float],
    completed_1d_bars: Sequence[KlineBar],
    sma200_1d_series: Sequence[float],
    position_status: str = "CASH",
) -> Dict[str, Any]:
    """Section 5: Evaluates exit conditions for an existing position (`HOLDING`) vs `CASH`.

    When `position_status == "CASH"`:
      - Never reports an active position exit as `TRIGGERED` (`exit_conditions_status = "NONE (IN CASH)"`).
      - Active exit flags (`stop_breached`, `two_4h_below_ema50`, `two_1d_below_sma200`) are `False`.
      - Reports what the exit rules would say if a position were open under `hypothetical_exit_status`.
    When `position_status == "HOLDING"`:
      - Evaluates stop breach, 2 consecutive completed 4H closes < EMA50, and 2 consecutive completed 1D closes < SMA200.
    """
    pos_mode = position_status.strip().upper()
    raw_stop_breached = bool(stop_price > 0 and current_price > 0 and current_price <= stop_price)

    raw_two_4h_below = False
    raw_one_4h_below = False
    if len(completed_4h_bars) >= 2 and len(ema50_4h_series) >= 2:
        c_last = completed_4h_bars[-1].close < ema50_4h_series[-1]
        c_prev = completed_4h_bars[-2].close < ema50_4h_series[-2]
        raw_two_4h_below = bool(c_last and c_prev)
        raw_one_4h_below = bool(c_last and not c_prev)

    raw_two_1d_below = False
    raw_one_1d_below = False
    if len(completed_1d_bars) >= 2 and len(sma200_1d_series) >= 2:
        d_last = completed_1d_bars[-1].close < sma200_1d_series[-1]
        d_prev = completed_1d_bars[-2].close < sma200_1d_series[-2]
        raw_two_1d_below = bool(d_last and d_prev)
        raw_one_1d_below = bool(d_last and not d_prev)

    raw_reasons: List[str] = []
    if raw_stop_breached:
        raw_reasons.append(f"Current price (${current_price:,.2f}) <= structural stop (${stop_price:,.2f})")
    if raw_two_4h_below:
        raw_reasons.append(f"Two consecutive completed 4H closes below 4H EMA50 (${ema50_4h_series[-1]:,.2f})")
    if raw_two_1d_below:
        raw_reasons.append(f"Two consecutive completed 1D closes below Daily SMA200 (${sma200_1d_series[-1]:,.2f})")

    warn_parts: List[str] = []
    if raw_one_4h_below:
        warn_parts.append(f"1 completed 4H close (${completed_4h_bars[-1].close:,.2f}) below EMA50 (${ema50_4h_series[-1]:,.2f})")
    if raw_one_1d_below:
        warn_parts.append(f"1 completed 1D close (${completed_1d_bars[-1].close:,.2f}) below SMA200 (${sma200_1d_series[-1]:,.2f})")

    if pos_mode != "HOLDING":
        if raw_reasons:
            hyp_text = "HYPOTHETICAL ONLY (No Open Position): " + " | ".join(raw_reasons) + " would trigger exit if HOLDING"
        elif warn_parts:
            hyp_text = "HYPOTHETICAL ONLY (No Open Position): " + "; ".join(warn_parts) + " would warn if HOLDING"
        else:
            hyp_text = "HYPOTHETICAL ONLY (No Open Position): All exit rules clear"

        inv_rules = (
            f"No open position (100% USDT Cash). If entered later, exit triggers on: "
            f"Stop <= ${stop_price:,.2f} | 2x 4H close < EMA50 | 2x 1D close < SMA200"
            if stop_price > 0
            else "No open position (100% USDT Cash). Active exit rules apply only when HOLDING."
        )
        return {
            "exit_conditions_status": "NONE (IN CASH)",
            "stop_breached": False,
            "two_4h_below_ema50": False,
            "two_1d_below_sma200": False,
            "one_4h_below_ema50": False,
            "one_1d_below_sma200": False,
            "hypothetical_stop_breached": raw_stop_breached,
            "hypothetical_two_4h_below_ema50": raw_two_4h_below,
            "hypothetical_two_1d_below_sma200": raw_two_1d_below,
            "hypothetical_exit_status": hyp_text,
            "invalidation_reason": inv_rules,
        }

    # HOLDING mode: active position exit evaluation
    if raw_reasons:
        exit_status = "TRIGGERED"
        invalidation_text = "EXIT CONDITION TRIGGERED: " + " | ".join(raw_reasons)
    elif warn_parts:
        exit_status = "WARNING"
        invalidation_text = "EXIT WARNING: " + "; ".join(warn_parts)
    else:
        exit_status = "CLEAR"
        e50_str = f"${ema50_4h_series[-1]:,.2f}" if ema50_4h_series else "EMA50"
        s200_str = f"${sma200_1d_series[-1]:,.2f}" if sma200_1d_series else "SMA200"
        invalidation_text = f"Active position CLEAR. Exit triggers on: Stop <= ${stop_price:,.2f} | 2x 4H close < {e50_str} | 2x 1D close < {s200_str}"

    return {
        "exit_conditions_status": exit_status,
        "stop_breached": raw_stop_breached,
        "two_4h_below_ema50": raw_two_4h_below,
        "two_1d_below_sma200": raw_two_1d_below,
        "one_4h_below_ema50": raw_one_4h_below,
        "one_1d_below_sma200": raw_one_1d_below,
        "hypothetical_stop_breached": raw_stop_breached,
        "hypothetical_two_4h_below_ema50": raw_two_4h_below,
        "hypothetical_two_1d_below_sma200": raw_two_1d_below,
        "hypothetical_exit_status": f"ACTIVE POSITION MODE: {exit_status}",
        "invalidation_reason": invalidation_text,
    }


def generate_strategy_verdict(
    data_integrity_ok: bool,
    integrity_reason: str,
    daily_regime: str,
    regime_reason: str,
    trend_4h: str,
    trend_reason: str,
    recovery_candle: str,
    setup_status: str,
    pullback_reason: str,
    stop_valid: bool,
    stop_reason: str,
    current_price: float,
    limit_entry_low: float,
    limit_entry_high: float,
    position_status: str,
    exit_eval: Dict[str, Any],
) -> Dict[str, str]:
    """Section 7: Deterministic Priority Decision Engine.

    Priority Order:
    1. DATA UNAVAILABLE
    2. DEFENSIVE / BEARISH REGIME
    3. TREND NOT CONFIRMED
    4. WAIT FOR PULLBACK
    5. PULLBACK RECOVERY CONFIRMED
    6. ENTRY SETUP CONFIRMED
    7. HOLD / MANAGE POSITION
    8. EXIT WARNING
    9. EXIT CONDITION
    """
    pos_mode = position_status.strip().upper()

    # Priority 1: Fail Closed on Data Integrity Failure
    if not data_integrity_ok or current_price <= 0:
        return {
            "decision_state": "DATA UNAVAILABLE",
            "trade_decision": "NO TRADE",
            "strategy_verdict": "NO TRADE",
            "setup_status": "WAIT",
            "explanation": f"DATA UNAVAILABLE: {integrity_reason or 'Missing or stale market data'}. New entries disabled.",
        }

    # If user is currently HOLDING a position, prioritize position management & exit rules (States 7, 8, 9)
    if pos_mode == "HOLDING":
        exit_st = exit_eval.get("exit_conditions_status", "CLEAR")
        if exit_st == "TRIGGERED":
            return {
                "decision_state": "EXIT CONDITION",
                "trade_decision": "EXIT ALERT",
                "strategy_verdict": "EXIT ALERT",
                "setup_status": setup_status,
                "explanation": exit_eval.get("invalidation_reason", "Exit condition triggered."),
            }
        if exit_st == "WARNING":
            return {
                "decision_state": "EXIT WARNING",
                "trade_decision": "HOLD",
                "strategy_verdict": "HOLD",
                "setup_status": setup_status,
                "explanation": exit_eval.get("invalidation_reason", "Exit warning active — monitor next candle close."),
            }
        return {
            "decision_state": "HOLD / MANAGE POSITION",
            "trade_decision": "HOLD",
            "strategy_verdict": "HOLD",
            "setup_status": setup_status,
            "explanation": "Position active and above structural stop, 4H EMA50, and 1D SMA200. Hold and trail per rules.",
        }

    # User is in CASH (Default): evaluate entry permission gates in strict priority order
    # Priority 2: Daily Regime Filter
    if daily_regime != "BULLISH":
        return {
            "decision_state": "DEFENSIVE / BEARISH REGIME",
            "trade_decision": "NO TRADE",
            "strategy_verdict": "NO TRADE",
            "setup_status": "WAIT",
            "explanation": f"DEFENSIVE / BEARISH REGIME: {regime_reason}. Remain 100% in USDT.",
        }

    # Priority 3: 4H Trend Filter
    if trend_4h != "CONFIRMED":
        return {
            "decision_state": "TREND NOT CONFIRMED",
            "trade_decision": "NO TRADE",
            "strategy_verdict": "NO TRADE",
            "setup_status": "WAIT",
            "explanation": f"TREND NOT CONFIRMED: {trend_reason}. Wait for 4H trend alignment.",
        }

    # Priority 4: Pullback & Setup Expiry
    if setup_status == "EXPIRED":
        return {
            "decision_state": "WAIT FOR PULLBACK",
            "trade_decision": "NO TRADE",
            "strategy_verdict": "WAIT",
            "setup_status": "EXPIRED",
            "explanation": f"SETUP EXPIRED: {pullback_reason}. Do not chase; wait for fresh pullback.",
        }

    if recovery_candle != "CONFIRMED":
        return {
            "decision_state": "WAIT FOR PULLBACK",
            "trade_decision": "NO TRADE",
            "strategy_verdict": "WAIT",
            "setup_status": "WAIT",
            "explanation": f"WAIT FOR PULLBACK: Bullish regime & 4H trend active, but {pullback_reason}.",
        }

    # Validate structural stop distance (0.75 ATR - 3.00 ATR)
    if not stop_valid:
        return {
            "decision_state": "WAIT FOR PULLBACK",
            "trade_decision": "NO TRADE",
            "strategy_verdict": "NO TRADE",
            "setup_status": "WAIT",
            "explanation": f"NO ENTRY: Recovery candle printed, but {stop_reason}.",
        }

    # Priority 5 vs 6: Check if current price moved above the acceptable limit-entry zone
    if current_price > limit_entry_high:
        return {
            "decision_state": "PULLBACK RECOVERY CONFIRMED",
            "trade_decision": "WAIT FOR RETEST",
            "strategy_verdict": "WAIT",
            "setup_status": "WAIT FOR RETEST",
            "explanation": (
                f"WAIT FOR RETEST: Setup confirmed, but spot (${current_price:,.2f}) is above limit entry zone "
                f"(${limit_entry_low:,.2f}-${limit_entry_high:,.2f}). Do not chase."
            ),
        }

    # Priority 6: ENTRY SETUP CONFIRMED
    return {
        "decision_state": "ENTRY SETUP CONFIRMED",
        "trade_decision": "ENTRY READY",
        "strategy_verdict": "ENTRY READY",
        "setup_status": "CONFIRMED",
        "explanation": (
            f"ENTRY SETUP CONFIRMED: Daily regime BULLISH, 4H trend CONFIRMED, 4H recovery candle CONFIRMED. "
            f"Reference limit zone: ${limit_entry_low:,.2f} - ${limit_entry_high:,.2f}."
        ),
    }


# ============================================================================
# ENGINE ORCHESTRATOR & CLIPBOARD HELPER
# ============================================================================

class TrendPullbackEngine:
    """Evaluates BTC Trend-Pullback v1.0 using StateStore data without side effects."""

    def __init__(
        self,
        config: Optional[EngineConfig] = None,
        strategy_cfg: Optional[TrendPullbackConfig] = None,
    ) -> None:
        self.config = config
        self.strategy_cfg = strategy_cfg or TrendPullbackConfig.from_yaml()

    def evaluate(
        self,
        store: StateStore,
        now_ms: Optional[int] = None,
    ) -> TrendPullbackEvaluation:
        """Runs the complete BTC Trend-Pullback v1.0 pipeline and updates store.trend_pullback_evaluation."""
        cfg = self.strategy_cfg
        if now_ms is None:
            now_ms = int(time.time() * 1000)

        now_dt_utc = datetime.fromtimestamp(now_ms / 1000.0, tz=timezone.utc)
        now_dt_myt = now_dt_utc.astimezone(MYT_TZ)
        ts_utc_str = now_dt_utc.strftime("%Y-%m-%d %H:%M:%S UTC")
        ts_myt_str = now_dt_myt.strftime("%Y-%m-%d %H:%M:%S MYT (UTC+8)")

        # 1. Spot Price resolution
        raw_1d = list(getattr(store, "spot_klines_1d", []) or [])
        raw_4h = list(getattr(store, "spot_klines_4h", []) or [])
        raw_1h = list(getattr(store, "spot_klines_1h", []) or [])
        raw_1w = list(getattr(store, "spot_klines_1w", []) or [])

        spot_price = float(
            getattr(store, "binance_spot_price", 0.0)
            or getattr(store, "spot_price", 0.0)
            or 0.0
        )
        if spot_price <= 0.0 and raw_1h:
            spot_price = float(raw_1h[-1].close)
        elif spot_price <= 0.0 and raw_4h:
            spot_price = float(raw_4h[-1].close)
        elif spot_price <= 0.0 and raw_1d:
            spot_price = float(raw_1d[-1].close)

        # Synthesize 4H bars from 1H if dedicated 4H buffer is empty or has fewer bars than 1H synthesis
        synth_4h = synthesize_closed_4h_from_1h(raw_1h, now_ms=now_ms) if raw_1h else []
        candidate_4h = raw_4h if len(raw_4h) >= len(synth_4h) else synth_4h

        # 2. Verify Data Integrity & Extract Strictly Completed Candles
        min_1d = cfg.daily_sma_period + cfg.daily_sma_slope_period
        min_4h = cfg.ema_slow + cfg.ema_slope_period

        ok_1d, status_1d, comp_1d, err_1d = verify_and_extract_completed_candles(
            raw_1d,
            tf_ms=TF_1D_MS,
            min_required=min_1d,
            now_ms=now_ms,
            max_stale_hours=cfg.max_daily_stale_hours,
            label="Daily (1D)",
        )
        ok_4h, status_4h, comp_4h, err_4h = verify_and_extract_completed_candles(
            candidate_4h,
            tf_ms=TF_4H_MS,
            min_required=min_4h,
            now_ms=now_ms,
            max_stale_hours=cfg.max_4h_stale_hours,
            label="4H",
        )

        forming_1d_excl, forming_1d_open_utc = _inspect_forming_candles(raw_1d, TF_1D_MS, now_ms)
        forming_4h_excl, forming_4h_open_utc = _inspect_forming_candles(candidate_4h, TF_4H_MS, now_ms)
        if not forming_4h_excl and raw_1h:
            # Check if forming 1H bars exist for the current in-progress 4H bucket
            curr_4h_bucket = (now_ms // TF_4H_MS) * TF_4H_MS
            if any(int(b.timestamp_ms) >= curr_4h_bucket for b in raw_1h):
                forming_4h_excl = True
                forming_4h_open_utc = datetime.fromtimestamp(curr_4h_bucket / 1000.0, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

        open_1d_utc = (
            datetime.fromtimestamp(int(comp_1d[-1].timestamp_ms) / 1000.0, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
            if comp_1d
            else "N/A"
        )
        last_1d_utc = (
            datetime.fromtimestamp((int(comp_1d[-1].timestamp_ms) + TF_1D_MS) / 1000.0, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
            if comp_1d
            else "N/A"
        )
        open_4h_utc = (
            datetime.fromtimestamp(int(comp_4h[-1].timestamp_ms) / 1000.0, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
            if comp_4h
            else "N/A"
        )
        last_4h_utc = (
            datetime.fromtimestamp((int(comp_4h[-1].timestamp_ms) + TF_4H_MS) / 1000.0, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
            if comp_4h
            else "N/A"
        )

        data_integrity_ok = bool(ok_1d and ok_4h and spot_price > 0 and math.isfinite(spot_price))
        integrity_errors = [e for e in (err_1d, err_4h) if e]
        if spot_price <= 0 or not math.isfinite(spot_price):
            integrity_errors.append("Spot price is missing or non-positive.")
        integrity_failure_reason = " | ".join(integrity_errors)

        # Supplementary Macro 1D & 1W EMA50 (Read-Only Context)
        ema50_1d_val = 0.0
        if len(comp_1d) >= 50:
            e50_1d_s = compute_ema_series([b.close for b in comp_1d], 50)
            ema50_1d_val = e50_1d_s[-1] if math.isfinite(e50_1d_s[-1]) else 0.0
        ema50_1w_val = 0.0
        if len(raw_1w) >= 50:
            e50_1w_s = compute_ema_series([b.close for b in raw_1w], 50)
            ema50_1w_val = e50_1w_s[-1] if math.isfinite(e50_1w_s[-1]) else 0.0

        # 3. Calculate Daily Regime & 4H Trend
        reg_res = calculate_regime(comp_1d, cfg) if ok_1d else {
            "regime": "DATA UNAVAILABLE",
            "last_close": comp_1d[-1].close if comp_1d else 0.0,
            "sma200": 0.0,
            "sma200_prev20": 0.0,
            "sma200_slope_20d": 0.0,
            "close_above_sma200": False,
            "sma200_rising": False,
            "sma200_series": [],
            "reason": err_1d or "Daily data unavailable",
        }

        trd_res = calculate_trend(comp_4h, cfg) if ok_4h else {
            "trend": "DATA UNAVAILABLE",
            "ema50": 0.0,
            "ema50_prev6": 0.0,
            "ema50_slope_6bars": 0.0,
            "ema200": 0.0,
            "atr14": 0.0,
            "last_close": comp_4h[-1].close if comp_4h else 0.0,
            "ema50_above_ema200": False,
            "ema50_rising_6bars": False,
            "close_above_ema200": False,
            "ema50_series": [],
            "ema200_series": [],
            "atr14_series": [],
            "reason": err_4h or "4H data unavailable",
        }

        # 4. Pullback Detection
        if ok_4h and trd_res.get("ema50_series") and trd_res.get("atr14_series"):
            pb_res = detect_pullback(comp_4h, trd_res["ema50_series"], trd_res["atr14_series"], cfg)
        else:
            pb_res = {
                "pullback_zone_lower": 0.0,
                "pullback_zone_upper": 0.0,
                "max_extension_price": 0.0,
                "recovery_candle": "NOT CONFIRMED",
                "setup_status": "WAIT",
                "bars_since_recovery": -1,
                "reason": err_4h or "4H data unavailable",
            }

        # 5. Entry Zone, Structural Stop & Position Sizing
        ez_res = calculate_entry_zone(trd_res["ema50"], trd_res["atr14"], cfg) if ok_4h else {
            "entry_low": 0.0,
            "entry_high": 0.0,
            "reference_entry": 0.0,
        }

        pos_status = str(getattr(store, "trend_pullback_position_status", "CASH") or "CASH").upper()
        hold_entry = float(getattr(store, "trend_pullback_entry_price", 0.0) or 0.0)
        hold_stop = float(getattr(store, "trend_pullback_stop_price", 0.0) or 0.0)

        ref_entry = hold_entry if (pos_status == "HOLDING" and hold_entry > 0) else ez_res["reference_entry"]
        stp_res = calculate_stop(comp_4h, trd_res["atr14"], ref_entry, cfg) if (ok_4h and ref_entry > 0) else {
            "lowest_low_5bars": 0.0,
            "atr14_used": 0.0,
            "stop_buffer_usd": 0.0,
            "stop_price": hold_stop if hold_stop > 0 else 0.0,
            "stop_distance_usd": 0.0,
            "stop_distance_atr": 0.0,
            "stop_distance_atr_exact": 0.0,
            "valid": False,
            "reason": "Data unavailable for stop calculation",
        }

        active_stop = hold_stop if (pos_status == "HOLDING" and hold_stop > 0) else stp_res["stop_price"]

        sz_res = (
            calculate_position_size(ref_entry, active_stop, cfg)
            if (data_integrity_ok and stp_res["valid"])
            else calculate_position_size(0.0, 0.0, cfg)
        )

        # 6. Exit Evaluation & Deterministic Verdict
        exit_res = evaluate_exit(
            current_price=spot_price,
            stop_price=active_stop,
            completed_4h_bars=comp_4h,
            ema50_4h_series=trd_res.get("ema50_series", []),
            completed_1d_bars=comp_1d,
            sma200_1d_series=reg_res.get("sma200_series", []),
            position_status=pos_status,
        )

        verdict_res = generate_strategy_verdict(
            data_integrity_ok=data_integrity_ok,
            integrity_reason=integrity_failure_reason,
            daily_regime=reg_res["regime"],
            regime_reason=reg_res["reason"],
            trend_4h=trd_res["trend"],
            trend_reason=trd_res["reason"],
            recovery_candle=pb_res["recovery_candle"],
            setup_status=pb_res["setup_status"],
            pullback_reason=pb_res["reason"],
            stop_valid=stp_res["valid"],
            stop_reason=stp_res["reason"],
            current_price=spot_price,
            limit_entry_low=ez_res["entry_low"],
            limit_entry_high=ez_res["entry_high"],
            position_status=pos_status,
            exit_eval=exit_res,
        )

        if pos_status == "HOLDING":
            entry_elig_str = "IN POSITION (Managing open BTC spot holding; new entries paused)"
        elif verdict_res["strategy_verdict"] == "ENTRY READY":
            entry_elig_str = "ELIGIBLE (All 1D Regime, 4H Trend, Pullback Recovery, and Stop gates passed)"
        else:
            entry_elig_str = f"BLOCKED ({verdict_res['decision_state']})"

        last_1d_bar = comp_1d[-1] if comp_1d else KlineBar(0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        last_4h_bar = comp_4h[-1] if comp_4h else KlineBar(0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

        daily_status_str = (
            f"LAST CLOSE (Open {open_1d_utc} -> Close {last_1d_utc})"
            if status_1d == "LAST CLOSE"
            else status_1d
        )
        c4h_status_str = (
            f"LAST CLOSE (Open {open_4h_utc} -> Close {last_4h_utc})"
            if status_4h == "LAST CLOSE"
            else status_4h
        )

        ev = TrendPullbackEvaluation(
            strategy_name="BTC TREND-PULLBACK v1.0",
            strategy_status="UNVALIDATED",
            mode_label="RESEARCH / PAPER MODE",
            timestamp_utc=ts_utc_str,
            timestamp_myt=ts_myt_str,
            spot_price=spot_price,
            daily_regime=reg_res["regime"],
            daily_close_completed=reg_res["last_close"],
            daily_open_completed=last_1d_bar.open,
            daily_high_completed=last_1d_bar.high,
            daily_low_completed=last_1d_bar.low,
            daily_sma200=reg_res["sma200"],
            daily_sma200_prev20=reg_res["sma200_prev20"],
            daily_sma200_slope_20d=reg_res["sma200_slope_20d"],
            daily_close_above_sma200=reg_res["close_above_sma200"],
            daily_sma200_rising=reg_res["sma200_rising"],
            trend_4h=trd_res["trend"],
            close_4h_completed=last_4h_bar.close,
            open_4h_completed=last_4h_bar.open,
            high_4h_completed=last_4h_bar.high,
            low_4h_completed=last_4h_bar.low,
            ema50_4h=trd_res["ema50"],
            ema50_4h_prev6=trd_res["ema50_prev6"],
            ema50_4h_slope_6bars=trd_res["ema50_slope_6bars"],
            ema200_4h=trd_res["ema200"],
            atr14_4h=trd_res["atr14"],
            ema50_above_ema200=trd_res["ema50_above_ema200"],
            ema50_rising_6bars=trd_res["ema50_rising_6bars"],
            close_4h_above_ema200=trd_res["close_above_ema200"],
            ema50_1d=ema50_1d_val,
            ema50_1w=ema50_1w_val,
            pullback_zone_lower=pb_res["pullback_zone_lower"],
            pullback_zone_upper=pb_res["pullback_zone_upper"],
            max_extension_price=pb_res["max_extension_price"],
            recovery_candle=pb_res["recovery_candle"],
            setup_status=verdict_res["setup_status"],
            bars_since_recovery=pb_res["bars_since_recovery"],
            pullback_rejection_reason=pb_res["reason"],
            decision_state=verdict_res["decision_state"],
            trade_decision=verdict_res["trade_decision"],
            limit_entry_low=ez_res["entry_low"],
            limit_entry_high=ez_res["entry_high"],
            reference_entry_price=ref_entry,
            structural_stop=active_stop,
            stop_lowest_low_5bars=stp_res["lowest_low_5bars"],
            stop_buffer_usd=stp_res["stop_buffer_usd"],
            stop_distance_usd=stp_res["stop_distance_usd"],
            stop_distance_atr=stp_res["stop_distance_atr"],
            stop_distance_atr_exact=stp_res["stop_distance_atr_exact"],
            stop_valid=stp_res["valid"],
            stop_rejection_reason=stp_res["reason"],
            simulation_equity_usd=sz_res["equity_usd"],
            risk_per_trade_pct=cfg.risk_per_trade * 100.0,
            risk_budget_usd=sz_res["risk_budget_usd"],
            sizing_entry_price=sz_res["sizing_entry_price"],
            sizing_stop_price=sz_res["sizing_stop_price"],
            gross_price_risk_per_btc=sz_res["gross_price_risk_per_btc"],
            entry_fee_per_btc=sz_res["entry_fee_per_btc"],
            exit_fee_per_btc=sz_res["exit_fee_per_btc"],
            entry_slippage_per_btc=sz_res["entry_slippage_per_btc"],
            exit_slippage_per_btc=sz_res["exit_slippage_per_btc"],
            cost_allowance_per_btc=sz_res["cost_allowance_per_btc"],
            total_risk_per_btc=sz_res["total_risk_per_btc"],
            gross_price_risk_usd=sz_res["gross_price_risk_usd"],
            entry_fee_usd=sz_res["entry_fee_usd"],
            exit_fee_usd=sz_res["exit_fee_usd"],
            entry_slippage_usd=sz_res["entry_slippage_usd"],
            exit_slippage_usd=sz_res["exit_slippage_usd"],
            total_estimated_risk_usd=sz_res["total_estimated_risk_usd"],
            position_size_btc=sz_res["position_size_btc"],
            position_value_usd=sz_res["position_value_usd"],
            risk_reward_label="DATA UNAVAILABLE (No fixed target - trend-continuation research model)",
            position_status=pos_status,
            holding_entry_price=hold_entry,
            holding_stop_price=hold_stop,
            exit_conditions_status=exit_res["exit_conditions_status"],
            exit_stop_breached=exit_res["stop_breached"],
            exit_two_4h_below_ema50=exit_res["two_4h_below_ema50"],
            exit_two_1d_below_sma200=exit_res["two_1d_below_sma200"],
            invalidation_reason=exit_res["invalidation_reason"],
            entry_eligibility_status=entry_elig_str,
            hypothetical_exit_status=exit_res["hypothetical_exit_status"],
            data_integrity_ok=data_integrity_ok,
            daily_candle_status=daily_status_str,
            daily_open_time_utc=open_1d_utc,
            daily_close_time_utc=last_1d_utc,
            daily_last_close_utc=last_1d_utc,
            daily_forming_excluded=forming_1d_excl,
            daily_forming_open_utc=forming_1d_open_utc,
            candle_4h_status=c4h_status_str,
            candle_4h_open_time_utc=open_4h_utc,
            candle_4h_close_time_utc=last_4h_utc,
            candle_4h_last_close_utc=last_4h_utc,
            candle_4h_forming_excluded=forming_4h_excl,
            candle_4h_forming_open_utc=forming_4h_open_utc,
            integrity_failure_reason=integrity_failure_reason,
            strategy_verdict=verdict_res["strategy_verdict"],
            verdict_explanation=verdict_res["explanation"],
        )
        ev.summary_markdown = self._build_markdown_summary(ev)
        store.trend_pullback_evaluation = ev
        return ev

    @staticmethod
    def _build_markdown_summary(ev: TrendPullbackEvaluation) -> str:
        active_order_note = (
            " *(Hypothetical Sizing Audit at Ref Entry — Active Order: 0.00000 BTC / $0.00)*"
            if ev.trade_decision == "NO TRADE"
            else ""
        )
        lines = [
            f"# {ev.strategy_name} | {ev.mode_label}",
            f"**STRATEGY STATUS:** `{ev.strategy_status}`  |  **Retrieval Time (MYT):** `{ev.timestamp_myt}`  |  **Retrieval Time (UTC):** `{ev.timestamp_utc}`",
            f"**Spot Price:** `${ev.spot_price:,.2f}`  |  **Decision State:** `{ev.decision_state}`  |  **Verdict:** `{ev.strategy_verdict}`",
            "",
            "## 1. MARKET REGIME & 4H TREND",
            f"- **Daily Regime:** `{ev.daily_regime}` (Completed 1D Candle: `Open {ev.daily_open_time_utc} -> Close {ev.daily_close_time_utc}` | Close: `${ev.daily_close_completed:,.2f}` vs Daily SMA200: `${ev.daily_sma200:,.2f}`, 20D Slope: `{ev.daily_sma200_slope_20d:+,.2f}`)",
            f"- **4H Trend:** `{ev.trend_4h}` (Completed 4H Candle: `Open {ev.candle_4h_open_time_utc} -> Close {ev.candle_4h_close_time_utc}` | 4H EMA50: `${ev.ema50_4h:,.2f}`, 4H EMA200: `${ev.ema200_4h:,.2f}`, 6-Bar EMA50 Slope: `{ev.ema50_4h_slope_6bars:+,.2f}`, 4H ATR14: `${ev.atr14_4h:,.2f}`)",
            "",
            "## 2. PULLBACK ANALYSIS (LAST COMPLETED 4H CANDLE AUDIT)",
            f"- **Evaluated 4H Candle Window:** `Open {ev.candle_4h_open_time_utc} -> Close {ev.candle_4h_close_time_utc}`",
            f"- **Evaluated 4H Candle OHLC:** `Open ${ev.open_4h_completed:,.2f}` | `High ${ev.high_4h_completed:,.2f}` | `Low ${ev.low_4h_completed:,.2f}` | `Close ${ev.close_4h_completed:,.2f}`",
            f"- **4H Indicators Used:** `4H EMA50 = ${ev.ema50_4h:,.2f}`  |  `4H ATR14 = ${ev.atr14_4h:,.2f}`",
            f"- **Pullback Zone (`[EMA50 - 0.50*ATR, EMA50 + 0.25*ATR]`):** `${ev.pullback_zone_lower:,.2f} - ${ev.pullback_zone_upper:,.2f}`",
            f"- **Max Recovery Extension (`EMA50 + 1.00*ATR`):** `${ev.max_extension_price:,.2f}`",
            f"- **Recovery Candle:** `{ev.recovery_candle}`  |  **Setup Status:** `{ev.setup_status}`",
            f"- **Confirmation / Rejection Reason:** {ev.pullback_rejection_reason}",
            "",
            "## 3. TRADE PLAN & POSITION-SIZING AUDIT (SIMULATION EQUITY: US$100,000.00)",
            f"- **Decision:** `{ev.trade_decision}`  |  **Entry Eligibility:** `{ev.entry_eligibility_status}`",
            f"- **Limit Entry Zone (`[EMA50, EMA50 + 0.10*ATR]`):** `${ev.limit_entry_low:,.2f} - ${ev.limit_entry_high:,.2f}` (Sizing Reference Entry: `${ev.sizing_entry_price:,.2f}`)",
            f"- **Structural Stop Audit (`5-Bar Low - 0.25*ATR`):** 5-Bar Lowest Low `${ev.stop_lowest_low_5bars:,.2f}` - Buffer `${ev.stop_buffer_usd:,.2f}` (`0.25 * ${ev.atr14_4h:,.2f}`) = **Stop `${ev.structural_stop:,.2f}`**",
            f"- **Stop Distance & Boundary Check (`[0.75, 3.00] ATR`):** `-${ev.stop_distance_usd:,.2f}` from Ref Entry `${ev.sizing_entry_price:,.2f}` = **`{ev.stop_distance_atr:.2f} ATR`** (exact `{ev.stop_distance_atr_exact:.4f} ATR`) — `{ev.stop_rejection_reason}`",
            f"- **Position Sizing Breakdown (`0.50%` Risk Budget = `${ev.risk_budget_usd:,.2f}`):**",
            f"  - **Final BTC Quantity:** `{ev.position_size_btc:.5f} BTC`  |  **Position Notional:** `${ev.position_value_usd:,.2f}`{active_order_note}",
            f"  - **Gross Price Risk:** `${ev.gross_price_risk_per_btc:,.2f}/BTC` -> **`${ev.gross_price_risk_usd:,.2f}`**",
            f"  - **Entry Fee Allowance (`0.10%`):** `${ev.entry_fee_per_btc:,.2f}/BTC` -> **`${ev.entry_fee_usd:,.2f}`**",
            f"  - **Exit Fee Allowance (`0.10%`):** `${ev.exit_fee_per_btc:,.2f}/BTC` -> **`${ev.exit_fee_usd:,.2f}`**",
            f"  - **Entry Slippage Allowance (`0.05%`):** `${ev.entry_slippage_per_btc:,.2f}/BTC` -> **`${ev.entry_slippage_usd:,.2f}`**",
            f"  - **Exit Slippage Allowance (`0.05%`):** `${ev.exit_slippage_per_btc:,.2f}/BTC` -> **`${ev.exit_slippage_usd:,.2f}`**",
            f"  - **Total Estimated Loss (Gross + Fees + Slippage):** `${ev.total_risk_per_btc:,.2f}/BTC` -> **`${ev.total_estimated_risk_usd:,.2f}`** (<= `${ev.risk_budget_usd:,.2f}` budget)",
            f"- **Risk / Reward:** `{ev.risk_reward_label}`",
            "",
            "## 4. POSITION MANAGEMENT & DATA INTEGRITY",
            f"- **Current Position Status:** `{ev.position_status}`  |  **Active Position Exit Status:** `{ev.exit_conditions_status}`",
            f"- **Active Exit Rule Flags:** Stop Breach `{ev.exit_stop_breached}` | 2x 4H < EMA50 `{ev.exit_two_4h_below_ema50}` | 2x 1D < SMA200 `{ev.exit_two_1d_below_sma200}`",
            f"- **Position / Market Invalidation:** {ev.invalidation_reason}",
            f"- **Hypothetical Exit Check:** {ev.hypothetical_exit_status}",
            f"- **Last Completed 1D Candle:** `{ev.daily_candle_status}` (Forming 1D Excluded: `{ev.daily_forming_excluded}` — `{ev.daily_forming_open_utc}`)",
            f"- **Last Completed 4H Candle:** `{ev.candle_4h_status}` (Forming 4H Excluded: `{ev.candle_4h_forming_excluded}` — `{ev.candle_4h_forming_open_utc}`)",
            f"- **Verdict Explanation:** {ev.verdict_explanation}",
        ]
        return "\n".join(lines)


def copy_trend_pullback_to_clipboard(store: StateStore) -> Tuple[bool, str, int]:
    """Copies BTC Trend-Pullback v1.0 brief to system clipboard and saves to logs/."""
    ev = store.trend_pullback_evaluation
    if ev is None:
        ev = TrendPullbackEngine().evaluate(store)

    text = ev.summary_markdown
    char_count = len(text)

    try:
        os.makedirs("logs", exist_ok=True)
        with open(os.path.join("logs", "btc_trend_pullback_latest.md"), "w", encoding="utf-8") as fh:
            fh.write(text)
    except Exception:
        pass

    copied = False
    if os.name == "nt":
        crlf_text = text.replace("\r\n", "\n").replace("\n", "\r\n")
        try:
            subprocess.run(
                ["clip.exe"],
                input=crlf_text.encode("utf-16le"),
                check=True,
                timeout=3.0,
            )
            copied = True
        except Exception:
            try:
                proc = subprocess.Popen(
                    ["powershell", "-NoProfile", "-Command", "($input | Out-String) | Set-Clipboard"],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                proc.communicate(input=crlf_text.encode("utf-8"), timeout=3.0)
                copied = proc.returncode == 0
            except Exception:
                copied = False

    store.last_packet_copied_utc = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")
    store.last_packet_copied_ts = time.time()
    store.last_packet_char_count = char_count

    if copied:
        return True, f"BTC Trend-Pullback v1.0 brief copied ({char_count:,} chars)", char_count
    return False, f"Saved BTC Trend-Pullback v1.0 brief to logs/ ({char_count:,} chars)", char_count
