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

SGT_TZ = timezone(timedelta(hours=8))


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

    @staticmethod
    def _numeric_rules() -> Dict[str, Tuple[float, float, bool, bool, type]]:
        return {
            "daily_sma_period": (10.0, 500.0, True, True, int),
            "daily_sma_slope_period": (1.0, 250.0, True, True, int),
            "ema_fast": (2.0, 500.0, True, True, int),
            "ema_slow": (5.0, 1000.0, True, True, int),
            "ema_slope_period": (1.0, 100.0, True, True, int),
            "atr_period": (2.0, 100.0, True, True, int),
            "pullback_upper_atr": (0.0, 3.0, True, True, float),
            "pullback_lower_atr": (0.0, 3.0, True, True, float),
            "recovery_max_extension_atr": (0.1, 5.0, True, True, float),
            "limit_entry_upper_atr": (0.0, 2.0, True, True, float),
            "stop_lookback": (1.0, 50.0, True, True, int),
            "stop_buffer_atr": (0.0, 2.0, True, True, float),
            "minimum_stop_atr": (0.0, 5.0, False, True, float),
            "maximum_stop_atr": (0.0, 10.0, False, True, float),
            "risk_per_trade": (0.0, 0.02, False, True, float),
            "initial_simulation_equity": (100.0, 100_000_000.0, True, True, float),
            "setup_expiry_4h_bars": (1.0, 30.0, True, True, int),
            "entry_fee_pct": (0.0, 0.02, True, True, float),
            "exit_fee_pct": (0.0, 0.02, True, True, float),
            "entry_slippage_pct": (0.0, 0.02, True, True, float),
            "exit_slippage_pct": (0.0, 0.02, True, True, float),
            "max_daily_stale_hours": (0.0, 168.0, False, True, float),
            "max_4h_stale_hours": (0.0, 48.0, False, True, float),
        }

    @classmethod
    def _validate_numeric_field(cls, key: str, raw_val: Any) -> Any:
        rules = cls._numeric_rules()
        lo, hi, lo_inc, hi_inc, expected_type = rules[key]
        if isinstance(raw_val, bool):
            raise ValueError(f"Config key '{key}' must be numeric, got bool {raw_val!r}")
        try:
            num = float(raw_val)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Config key '{key}' has non-numeric value {raw_val!r}") from exc
        if not math.isfinite(num):
            raise ValueError(f"Config key '{key}' must be finite, got {raw_val!r}")
        if expected_type is int and not num.is_integer():
            raise ValueError(f"Config key '{key}' must be an integer, got {raw_val!r}")
        lo_ok = (num >= lo) if lo_inc else (num > lo)
        hi_ok = (num <= hi) if hi_inc else (num < hi)
        if not (lo_ok and hi_ok):
            lo_br = "[" if lo_inc else "("
            hi_br = "]" if hi_inc else ")"
            raise ValueError(
                f"Config key '{key}'={num!r} is outside allowed range {lo_br}{lo}, {hi}{hi_br}"
            )
        return int(num) if expected_type is int else num

    def validate(self) -> None:
        """Validates all numeric config parameters and cross-field relationships."""
        for key in self._numeric_rules():
            coerced = self._validate_numeric_field(key, getattr(self, key))
            object.__setattr__(self, key, coerced)

        if self.ema_fast >= self.ema_slow:
            raise ValueError(
                f"Config key 'ema_fast' ({self.ema_fast}) must be < 'ema_slow' ({self.ema_slow})"
            )
        if self.minimum_stop_atr >= self.maximum_stop_atr:
            raise ValueError(
                f"Config key 'minimum_stop_atr' ({self.minimum_stop_atr}) must be < 'maximum_stop_atr' ({self.maximum_stop_atr})"
            )
        if self.recovery_max_extension_atr < self.pullback_upper_atr:
            raise ValueError(
                f"Config key 'recovery_max_extension_atr' ({self.recovery_max_extension_atr}) must be >= 'pullback_upper_atr' ({self.pullback_upper_atr})"
            )
        if self.limit_entry_upper_atr > self.recovery_max_extension_atr:
            raise ValueError(
                f"Config key 'limit_entry_upper_atr' ({self.limit_entry_upper_atr}) must be <= 'recovery_max_extension_atr' ({self.recovery_max_extension_atr})"
            )

    def __post_init__(self) -> None:
        self.validate()

    @classmethod
    def from_yaml(cls, path: Optional[os.PathLike] = None) -> "TrendPullbackConfig":
        """Loads and strictly validates configuration from YAML; rejects invalid values."""
        explicit_path = path is not None
        if path is None:
            path = Path(__file__).resolve().parent.parent / "config" / "trend_pullback_config.yaml"
        else:
            path = Path(path)
        if not path.is_file():
            if explicit_path:
                logger.warning("TrendPullbackConfig YAML file not found: %s", path)
                raise FileNotFoundError(f"TrendPullbackConfig YAML file not found: {path}")
            logger.warning("Default TrendPullbackConfig YAML not found at %s; using locked defaults", path)
            return cls()

        rules = cls._numeric_rules()
        metadata_keys = {"strategy_name", "strategy_status", "mode"}
        parsed_kwargs: Dict[str, Any] = {}
        try:
            with open(path, "r", encoding="utf-8") as fh:
                for line_no, raw_line in enumerate(fh, 1):
                    line = raw_line.split("#", 1)[0].strip()
                    if not line:
                        continue
                    if ":" not in line:
                        raise ValueError(f"Malformed YAML line {line_no} (missing ':'): {raw_line.strip()!r}")
                    k, v = [x.strip().strip('"').strip("'") for x in line.split(":", 1)]
                    if k in metadata_keys:
                        continue
                    if k not in rules:
                        raise ValueError(f"Unknown config key '{k}' at line {line_no}")
                    if v.lower() in ("true", "false"):
                        raise ValueError(f"Config key '{k}' must be numeric, got boolean {v!r}")
                    parsed_kwargs[k] = cls._validate_numeric_field(k, v)
            cfg = cls(**parsed_kwargs)
            cfg.validate()
            return cfg
        except Exception as exc:
            logger.warning("Invalid TrendPullbackConfig YAML '%s': %s", path, exc)
            raise ValueError(f"Invalid TrendPullbackConfig YAML '{path}': {exc}") from exc


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
        if getattr(b, "timestamp_ms", None) is None:
            continue
        ts = int(b.timestamp_ms)
        if getattr(b, "is_closed", None) is False or (ts + TF_1H_MS > now_ms):
            continue
        b_key = (ts // TF_4H_MS) * TF_4H_MS
        buckets.setdefault(b_key, []).append(b)

    sorted_keys = sorted(buckets.keys())
    out: List[KlineBar] = []
    for idx, b_key in enumerate(sorted_keys):
        grp = sorted(buckets[b_key], key=lambda x: int(x.timestamp_ms))
        distinct_ts = {int(x.timestamp_ms) for x in grp}
        # A 4H bucket is complete only if its close boundary has passed (or a successor bucket exists)
        # and it has all 4 distinct closed constituent 1H candles.
        has_successor = idx < len(sorted_keys) - 1
        is_past_close = now_ms >= (b_key + TF_4H_MS)
        if (has_successor or is_past_close) and len(grp) == 4 and len(distinct_ts) == 4:
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
        if getattr(b, "timestamp_ms", None) is None:
            return False, "UNAVAILABLE", [], f"{label} contains missing timestamp."
        vals = (b.open, b.high, b.low, b.close, b.volume)
        if any(v is None or not math.isfinite(float(v)) for v in vals):
            return False, "UNAVAILABLE", [], f"{label} contains NaN or non-finite values."
        if b.open <= 0 or b.high <= 0 or b.low <= 0 or b.close <= 0 or b.volume < 0:
            return False, "UNAVAILABLE", [], f"{label} contains non-positive OHLC prices or negative volume."
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
    min_bars = max(cfg.ema_slow, cfg.ema_fast + cfg.ema_slope_period)
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
    """Evaluates whether a single completed 4H candle satisfies all 5 pullback recovery criteria."""
    if not (
        math.isfinite(ema50)
        and math.isfinite(atr14)
        and ema50 > 0
        and atr14 > 0
        and math.isfinite(bar.open)
        and math.isfinite(bar.low)
        and math.isfinite(bar.close)
    ):
        return False, "Invalid or non-finite EMA50/ATR14/OHLC inputs for recovery check"

    upper_bound = ema50 + (cfg.pullback_upper_atr * atr14)
    lower_bound = ema50 - (cfg.pullback_lower_atr * atr14)
    max_ext = ema50 + (cfg.recovery_max_extension_atr * atr14)

    # 1. Low >= lower bound of pullback zone [EMA50 - pullback_lower_atr*ATR, EMA50 + pullback_upper_atr*ATR]
    if bar.low < lower_bound:
        return False, f"Deep pullback rejected: candle low (${bar.low:,.2f}) fell below lower zone (${lower_bound:,.2f})"
    # 2. Low <= upper bound of pullback zone
    if bar.low > upper_bound:
        return False, f"No pullback: candle low (${bar.low:,.2f}) remained above pullback zone (${upper_bound:,.2f})"

    # 3. Close is above EMA50
    if bar.close <= ema50:
        return False, f"No recovery: candle close (${bar.close:,.2f}) <= EMA50 (${ema50:,.2f})"

    # 4. Close is above Open (bullish candle)
    if bar.close <= bar.open:
        return False, f"Bearish/doji candle rejected: close (${bar.close:,.2f}) <= open (${bar.open:,.2f})"

    # 5. Close is not more than recovery_max_extension_atr * ATR above EMA50 (anti-breakout-chasing)
    if bar.close > max_ext:
        return False, (
            f"Breakout chasing rejected: close (${bar.close:,.2f}) > "
            f"EMA50 + {cfg.recovery_max_extension_atr:.2f} ATR (${max_ext:,.2f})"
        )

    return True, "Valid 4H pullback & recovery candle confirmed"


def detect_pullback(
    completed_4h_bars: Sequence[KlineBar],
    ema50_series: Sequence[float],
    atr14_series: Sequence[float],
    cfg: Optional[TrendPullbackConfig] = None,
) -> Dict[str, Any]:
    """Section 4C & 4D: Evaluates Pullback Zone, Recovery Candle, and N-Bar Setup Expiry."""
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
    if not (math.isfinite(ema50_now) and math.isfinite(atr14_now) and ema50_now > 0 and atr14_now > 0):
        return {
            "pullback_zone_lower": 0.0,
            "pullback_zone_upper": 0.0,
            "max_extension_price": 0.0,
            "recovery_candle": "NOT CONFIRMED",
            "setup_status": "WAIT",
            "bars_since_recovery": -1,
            "reason": "Invalid or non-finite 4H EMA50/ATR14 for pullback detection",
        }

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

    # Check trailing completed 4H bars to determine if an active setup is still within the expiry window or has expired
    n_avail = min(len(completed_4h_bars), len(ema50_series), len(atr14_series))
    max_lookback = min(n_avail, cfg.setup_expiry_4h_bars + 4)
    for offset in range(1, max_lookback):
        idx = n_avail - 1 - offset
        b = completed_4h_bars[idx]
        e50 = float(ema50_series[idx])
        a14 = float(atr14_series[idx])
        if not (math.isfinite(e50) and math.isfinite(a14) and e50 > 0 and a14 > 0):
            continue
        ok_hist, _ = _check_single_bar_recovery(b, e50, a14, cfg)
        if ok_hist:
            # Verify subsequent bars have not invalidated structure by closing below EMA50
            subsequent_bars = completed_4h_bars[idx + 1 : n_avail]
            subsequent_emas = ema50_series[idx + 1 : n_avail]
            broken = any(
                not math.isfinite(se) or sb.close < se
                for sb, se in zip(subsequent_bars, subsequent_emas)
            )
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
    """Section 4D: Calculates suggested manual limit-entry zone [EMA50, EMA50 + cfg.limit_entry_upper_atr*ATR14]."""
    cfg = cfg or TrendPullbackConfig()
    if not (math.isfinite(ema50_4h) and math.isfinite(atr14_4h)) or ema50_4h <= 0 or atr14_4h <= 0:
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
    """Section 5: Calculates initial structural stop and validates [cfg.minimum_stop_atr, cfg.maximum_stop_atr] bounds.

    Formula:
      lowest_low_Nbars = round(min(low of last cfg.stop_lookback completed 4H candles), 2)
      stop_buffer_usd  = round(cfg.stop_buffer_atr * ATR14, 2)
      stop_price       = round(lowest_low_Nbars - stop_buffer_usd, 2)
      stop_distance_usd = round(round(entry_price, 2) - stop_price, 2)
      stop_distance_atr_exact = stop_distance_usd / ATR14
    """
    cfg = cfg or TrendPullbackConfig()
    if (
        len(completed_4h_bars) < cfg.stop_lookback
        or not (math.isfinite(atr14_4h) and math.isfinite(entry_price))
        or atr14_4h <= 0
        or entry_price <= 0
    ):
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
    lows = [float(b.low) for b in recent]
    if any(not math.isfinite(lo) or lo <= 0 for lo in lows):
        return {
            "lowest_low_5bars": 0.0,
            "atr14_used": 0.0,
            "stop_buffer_usd": 0.0,
            "stop_price": 0.0,
            "stop_distance_usd": 0.0,
            "stop_distance_atr": 0.0,
            "stop_distance_atr_exact": 0.0,
            "valid": False,
            "reason": "Non-finite or non-positive candle low in stop lookback window",
        }
    lowest_low = round(min(lows), 2)
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

    if not math.isfinite(stop_dist_atr_exact):
        return {
            **base_out,
            "valid": False,
            "reason": "Stop rejected: non-finite stop distance",
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
    """Section 6: Calculates simulated unleveraged spot position size with full fee & slippage audit breakdown.

    Uses the fictional reference simulation account (`cfg.initial_simulation_equity`) and configured
    risk fraction (`cfg.risk_per_trade`) — NOT sized to the operator's live account equity.
    Guarantees:
      1. Total estimated loss (gross price risk + entry/exit fees + entry/exit slippage) <= risk_budget_usd
         (`round(cfg.initial_simulation_equity * cfg.risk_per_trade, 2)`).
      2. Position notional <= equity_usd (`cfg.initial_simulation_equity`, 0.0x leverage, spot only).
      3. All displayed per-BTC and USD risk components reconcile to the cent.
    """
    cfg = cfg or TrendPullbackConfig()
    equity = round(float(cfg.initial_simulation_equity), 2)
    risk_budget = round(equity * float(cfg.risk_per_trade), 2)
    entry_px = round(float(entry_price), 2) if math.isfinite(float(entry_price)) else 0.0
    stop_px = round(float(stop_price), 2) if math.isfinite(float(stop_price)) else 0.0

    if not (math.isfinite(entry_px) and math.isfinite(stop_px)) or entry_px <= 0 or stop_px <= 0 or stop_px >= entry_px:
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
    if not data_integrity_ok or not math.isfinite(current_price) or current_price <= 0:
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

    # User is in CASH (Default): evaluate entry filter gates in strict priority order (veto-only; never authorizes)
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

    # Validate structural stop distance (configured [minimum_stop_atr, maximum_stop_atr] bounds)
    if not stop_valid:
        return {
            "decision_state": "WAIT FOR PULLBACK",
            "trade_decision": "NO TRADE",
            "strategy_verdict": "NO TRADE",
            "setup_status": "WAIT",
            "explanation": f"NO ENTRY: Recovery candle printed, but {stop_reason}.",
        }

    if (
        not (math.isfinite(limit_entry_low) and math.isfinite(limit_entry_high))
        or limit_entry_low <= 0
        or limit_entry_high <= 0
    ):
        return {
            "decision_state": "DATA UNAVAILABLE",
            "trade_decision": "NO TRADE",
            "strategy_verdict": "NO TRADE",
            "setup_status": "WAIT",
            "explanation": "DATA UNAVAILABLE: Invalid reference limit-entry zone bounds.",
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

    # Priority 6: ENTRY SETUP CONFIRMED (setup state only — veto-only stack never authorizes or instructs orders)
    return {
        "decision_state": "ENTRY SETUP CONFIRMED",
        "trade_decision": "ENTRY READY",
        "strategy_verdict": "ENTRY READY",
        "setup_status": "CONFIRMED",
        "explanation": (
            f"SETUP STATE ONLY (ENTRY READY — NOT an instruction or permission to place an order; operator decides): "
            f"Daily regime BULLISH, 4H trend CONFIRMED, 4H recovery candle CONFIRMED. "
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
        now_dt_sgt = now_dt_utc.astimezone(SGT_TZ)
        ts_utc_str = now_dt_utc.strftime("%Y-%m-%d %H:%M:%S UTC")
        ts_sgt_str = now_dt_sgt.strftime("%Y-%m-%d %H:%M:%S SGT (UTC+8)")

        # 1. Spot Price resolution
        raw_1d = list(getattr(store, "spot_klines_1d", []) or [])
        raw_4h = list(getattr(store, "spot_klines_4h", []) or [])
        raw_1h = list(getattr(store, "spot_klines_1h", []) or [])
        raw_1w = list(getattr(store, "spot_klines_1w", []) or [])

        def _safe_pos_float(val: Any) -> float:
            try:
                f = float(val)
                return f if (math.isfinite(f) and f > 0.0) else 0.0
            except (TypeError, ValueError):
                return 0.0

        def _fresh_bar_close(bars: Sequence[KlineBar], tf_ms: int, max_stale_hours: float) -> float:
            if not bars:
                return 0.0
            b = bars[-1]
            if getattr(b, "timestamp_ms", None) is None:
                return 0.0
            px = _safe_pos_float(getattr(b, "close", 0.0))
            if px <= 0.0:
                return 0.0
            age_h = (now_ms - (int(b.timestamp_ms) + tf_ms)) / 3_600_000.0
            return px if age_h <= max_stale_hours else 0.0

        spot_price = (
            _safe_pos_float(getattr(store, "binance_spot_price", 0.0))
            or _safe_pos_float(getattr(store, "spot_price", 0.0))
            or _fresh_bar_close(raw_1h, TF_1H_MS, cfg.max_4h_stale_hours)
            or _fresh_bar_close(raw_4h, TF_4H_MS, cfg.max_4h_stale_hours)
            or _fresh_bar_close(raw_1d, TF_1D_MS, cfg.max_daily_stale_hours)
        )

        # Prefer dedicated 4H buffer; synthesize closed 4H bars from 1H only when dedicated 4H history is short
        min_1d = cfg.daily_sma_period + cfg.daily_sma_slope_period
        min_4h = max(cfg.ema_slow, cfg.ema_fast + cfg.ema_slope_period)
        synth_4h = synthesize_closed_4h_from_1h(raw_1h, now_ms=now_ms) if raw_1h else []
        if not raw_4h:
            candidate_4h = synth_4h
        else:
            ok_raw4h, status_raw4h, comp_raw4h, err_raw4h = verify_and_extract_completed_candles(
                raw_4h,
                tf_ms=TF_4H_MS,
                min_required=min_4h,
                now_ms=now_ms,
                max_stale_hours=cfg.max_4h_stale_hours,
                label="4H",
            )
            if ok_raw4h:
                candidate_4h = raw_4h
            elif (len(raw_4h) < min_4h or (status_raw4h == "UNAVAILABLE" and "Insufficient completed" in err_raw4h)) and len(synth_4h) > len(comp_raw4h):
                candidate_4h = synth_4h
            else:
                candidate_4h = raw_4h

        # 2. Verify Data Integrity & Extract Strictly Completed Candles
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
            integrity_errors.append("Spot price is missing, stale, or non-positive.")
        integrity_failure_reason = " | ".join(integrity_errors)

        # Supplementary Macro 1D & 1W EMA50 + Daily SMA50 (only from verified non-stale closed bars)
        ema50_1d_val = 0.0
        sma50_1d_val = 0.0
        if ok_1d and len(comp_1d) >= 50:
            c1d_closes = [float(b.close) for b in comp_1d]
            e50_1d_s = compute_ema_series(c1d_closes, 50)
            s50_1d_s = compute_sma_series(c1d_closes, 50)
            ema50_1d_val = round(e50_1d_s[-1], 2) if math.isfinite(e50_1d_s[-1]) else 0.0
            sma50_1d_val = round(s50_1d_s[-1], 2) if math.isfinite(s50_1d_s[-1]) else 0.0
        ema50_1w_val = 0.0
        ok_1w, _status_1w, comp_1w, _err_1w = verify_and_extract_completed_candles(
            raw_1w,
            tf_ms=7 * TF_1D_MS,
            min_required=50,
            now_ms=now_ms,
            max_stale_hours=(7 * 24.0) + cfg.max_daily_stale_hours,
            label="Weekly (1W)",
        )
        if ok_1w and len(comp_1w) >= 50:
            e50_1w_s = compute_ema_series([float(b.close) for b in comp_1w], 50)
            ema50_1w_val = round(e50_1w_s[-1], 2) if math.isfinite(e50_1w_s[-1]) else 0.0

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

        # Round core 1D & 4H reference indicators to $0.01 so all derived $ / % / ATR metrics reconcile to the cent
        last_1d_bar = comp_1d[-1] if comp_1d else KlineBar(0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        last_4h_bar = comp_4h[-1] if comp_4h else KlineBar(0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

        spot_px = round(float(spot_price), 2) if (spot_price > 0 and math.isfinite(spot_price)) else 0.0
        daily_close_val = round(float(reg_res["last_close"]), 2)
        daily_sma200_val = round(float(reg_res["sma200"]), 2)
        daily_sma200_prev20_val = round(float(reg_res["sma200_prev20"]), 2)
        daily_sma200_slope_val = round(daily_sma200_val - daily_sma200_prev20_val, 2) if daily_sma200_val > 0 else 0.0

        daily_close_vs_sma200_usd = round(daily_close_val - daily_sma200_val, 2) if daily_sma200_val > 0 else 0.0
        daily_close_vs_sma200_pct = (
            round((daily_close_vs_sma200_usd / daily_sma200_val) * 100.0, 2)
            if daily_sma200_val > 0
            else 0.0
        )
        daily_close_vs_sma50_usd = round(daily_close_val - sma50_1d_val, 2) if sma50_1d_val > 0 else 0.0
        daily_close_vs_sma50_pct = (
            round((daily_close_vs_sma50_usd / sma50_1d_val) * 100.0, 2)
            if sma50_1d_val > 0
            else 0.0
        )
        daily_close_above_sma50 = bool(sma50_1d_val > 0 and daily_close_val > sma50_1d_val)

        ema50_4h_val = round(float(trd_res["ema50"]), 2)
        ema50_4h_prev6_val = round(float(trd_res["ema50_prev6"]), 2)
        ema50_4h_slope_val = round(ema50_4h_val - ema50_4h_prev6_val, 2) if ema50_4h_val > 0 else 0.0
        ema200_4h_val = round(float(trd_res["ema200"]), 2)
        atr14_4h_val = round(float(trd_res["atr14"]), 2)

        open_4h_val = round(float(last_4h_bar.open), 2)
        high_4h_val = round(float(last_4h_bar.high), 2)
        low_4h_val = round(float(last_4h_bar.low), 2)
        close_4h_val = round(float(last_4h_bar.close), 2)

        ema50_minus_ema200_4h_usd = (
            round(ema50_4h_val - ema200_4h_val, 2)
            if (ema50_4h_val > 0 and ema200_4h_val > 0)
            else 0.0
        )
        close_4h_vs_ema50_usd = round(close_4h_val - ema50_4h_val, 2) if ema50_4h_val > 0 else 0.0
        close_4h_vs_ema50_atr = round(close_4h_vs_ema50_usd / atr14_4h_val, 4) if atr14_4h_val > 0 else 0.0
        close_4h_vs_ema200_usd = round(close_4h_val - ema200_4h_val, 2) if ema200_4h_val > 0 else 0.0
        close_4h_vs_ema200_atr = round(close_4h_vs_ema200_usd / atr14_4h_val, 4) if atr14_4h_val > 0 else 0.0
        close_4h_above_ema50 = bool(ema50_4h_val > 0 and close_4h_val > ema50_4h_val)

        # 4. Pullback Detection & Sub-condition Measurements
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

        zone_lower_val = round(ema50_4h_val - cfg.pullback_lower_atr * atr14_4h_val, 2) if atr14_4h_val > 0 else 0.0
        zone_upper_val = round(ema50_4h_val + cfg.pullback_upper_atr * atr14_4h_val, 2) if atr14_4h_val > 0 else 0.0
        max_ext_val = round(ema50_4h_val + cfg.recovery_max_extension_atr * atr14_4h_val, 2) if atr14_4h_val > 0 else 0.0

        spot_minus_zone_lower_usd = round(spot_px - zone_lower_val, 2) if (spot_px > 0 and zone_lower_val > 0) else 0.0
        spot_minus_zone_lower_atr = round(spot_minus_zone_lower_usd / atr14_4h_val, 4) if atr14_4h_val > 0 else 0.0
        spot_minus_zone_upper_usd = round(spot_px - zone_upper_val, 2) if (spot_px > 0 and zone_upper_val > 0) else 0.0
        spot_minus_zone_upper_atr = round(spot_minus_zone_upper_usd / atr14_4h_val, 4) if atr14_4h_val > 0 else 0.0

        candle_4h_low_below_zone_lower = bool(zone_lower_val > 0 and low_4h_val < zone_lower_val)
        candle_4h_low_above_zone_upper = bool(zone_upper_val > 0 and low_4h_val > zone_upper_val)
        rec_cond1_low_ge_zone_lower = bool(zone_lower_val > 0 and low_4h_val >= zone_lower_val)
        rec_cond2_low_le_zone_upper = bool(zone_upper_val > 0 and low_4h_val <= zone_upper_val)
        rec_cond3_close_gt_ema50 = bool(ema50_4h_val > 0 and close_4h_val > ema50_4h_val)
        rec_cond4_close_gt_open = bool(open_4h_val > 0 and close_4h_val > open_4h_val)
        rec_cond5_close_le_max_ext = bool(max_ext_val > 0 and close_4h_val <= max_ext_val)
        rec_all_conditions_met = bool(
            rec_cond1_low_ge_zone_lower
            and rec_cond2_low_le_zone_upper
            and rec_cond3_close_gt_ema50
            and rec_cond4_close_gt_open
            and rec_cond5_close_le_max_ext
        )

        # 5. Reference Levels, Structural Stop & Position Sizing (using exact $0.01-rounded 4H EMA50 & ATR14)
        ez_res = calculate_entry_zone(ema50_4h_val, atr14_4h_val, cfg) if ok_4h else {
            "entry_low": 0.0,
            "entry_high": 0.0,
            "reference_entry": 0.0,
        }

        pos_status = str(getattr(store, "trend_pullback_position_status", "CASH") or "CASH").upper()
        hold_entry = float(getattr(store, "trend_pullback_entry_price", 0.0) or 0.0)
        hold_stop = float(getattr(store, "trend_pullback_stop_price", 0.0) or 0.0)

        ref_entry = round(hold_entry, 2) if (pos_status == "HOLDING" and hold_entry > 0) else ez_res["reference_entry"]
        stp_res = calculate_stop(comp_4h, atr14_4h_val, ref_entry, cfg) if (ok_4h and ref_entry > 0) else {
            "lowest_low_5bars": 0.0,
            "atr14_used": 0.0,
            "stop_buffer_usd": 0.0,
            "stop_price": round(hold_stop, 2) if hold_stop > 0 else 0.0,
            "stop_distance_usd": 0.0,
            "stop_distance_atr": 0.0,
            "stop_distance_atr_exact": 0.0,
            "valid": False,
            "reason": "Data unavailable for stop calculation",
        }

        active_stop = round(hold_stop, 2) if (pos_status == "HOLDING" and hold_stop > 0) else stp_res["stop_price"]

        sz_res = (
            calculate_position_size(ref_entry, active_stop, cfg)
            if data_integrity_ok
            else calculate_position_size(0.0, 0.0, cfg)
        )

        spot_to_ref_entry_usd = round(spot_px - ref_entry, 2) if (spot_px > 0 and ref_entry > 0) else 0.0
        spot_to_ref_entry_pct = (
            round((spot_to_ref_entry_usd / ref_entry) * 100.0, 2)
            if (spot_px > 0 and ref_entry > 0)
            else 0.0
        )
        stop_dist_ge_min_atr = bool(round(stp_res["stop_distance_atr_exact"], 8) >= cfg.minimum_stop_atr) if stp_res["stop_distance_atr_exact"] > 0 else False
        stop_dist_le_max_atr = bool(0 < round(stp_res["stop_distance_atr_exact"], 8) <= cfg.maximum_stop_atr)
        fee_slippage_buffer_usd = round(
            sz_res["entry_fee_usd"]
            + sz_res["exit_fee_usd"]
            + sz_res["entry_slippage_usd"]
            + sz_res["exit_slippage_usd"],
            2,
        )
        total_risk_le_budget = bool(0 < sz_res["total_estimated_risk_usd"] <= sz_res["risk_budget_usd"])

        # 6. Exit Rule Inputs (Last 2 Completed 4H Bars vs EMA50, Last 2 Completed 1D Bars vs SMA200, Consecutive Counts)
        e50_4h_series = trd_res.get("ema50_series", [])
        s200_1d_series = reg_res.get("sma200_series", [])

        prev_4h_open_utc = "N/A"
        prev_4h_close_utc = "N/A"
        prev_4h_close = 0.0
        prev_4h_ema50 = 0.0
        prev_4h_close_lt_ema50 = False
        last_4h_close_lt_ema50 = bool(ema50_4h_val > 0 and close_4h_val < ema50_4h_val)
        if len(comp_4h) >= 2 and len(e50_4h_series) >= 2 and math.isfinite(e50_4h_series[-2]):
            b_prev4h = comp_4h[-2]
            prev_4h_open_utc = datetime.fromtimestamp(int(b_prev4h.timestamp_ms) / 1000.0, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
            prev_4h_close_utc = datetime.fromtimestamp((int(b_prev4h.timestamp_ms) + TF_4H_MS) / 1000.0, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
            prev_4h_close = round(float(b_prev4h.close), 2)
            prev_4h_ema50 = round(float(e50_4h_series[-2]), 2)
            prev_4h_close_lt_ema50 = bool(prev_4h_close < prev_4h_ema50)

        consec_4h_below = 0
        if comp_4h and e50_4h_series:
            for b_item, e_val in zip(reversed(comp_4h), reversed(e50_4h_series)):
                if not math.isfinite(e_val):
                    break
                if round(float(b_item.close), 2) < round(float(e_val), 2):
                    consec_4h_below += 1
                else:
                    break

        prev_1d_open_utc = "N/A"
        prev_1d_close_utc = "N/A"
        prev_1d_close = 0.0
        prev_1d_sma200 = 0.0
        prev_1d_close_lt_sma200 = False
        last_1d_close_lt_sma200 = bool(daily_sma200_val > 0 and daily_close_val < daily_sma200_val)
        if len(comp_1d) >= 2 and len(s200_1d_series) >= 2 and math.isfinite(s200_1d_series[-2]):
            b_prev1d = comp_1d[-2]
            prev_1d_open_utc = datetime.fromtimestamp(int(b_prev1d.timestamp_ms) / 1000.0, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
            prev_1d_close_utc = datetime.fromtimestamp((int(b_prev1d.timestamp_ms) + TF_1D_MS) / 1000.0, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
            prev_1d_close = round(float(b_prev1d.close), 2)
            prev_1d_sma200 = round(float(s200_1d_series[-2]), 2)
            prev_1d_close_lt_sma200 = bool(prev_1d_close < prev_1d_sma200)

        consec_1d_below = 0
        if comp_1d and s200_1d_series:
            for b_item, s_val in zip(reversed(comp_1d), reversed(s200_1d_series)):
                if not math.isfinite(s_val):
                    break
                if round(float(b_item.close), 2) < round(float(s_val), 2):
                    consec_1d_below += 1
                else:
                    break

        exit_res = evaluate_exit(
            current_price=spot_px,
            stop_price=active_stop,
            completed_4h_bars=comp_4h,
            ema50_4h_series=e50_4h_series,
            completed_1d_bars=comp_1d,
            sma200_1d_series=s200_1d_series,
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
            current_price=spot_px,
            limit_entry_low=ez_res["entry_low"],
            limit_entry_high=ez_res["entry_high"],
            position_status=pos_status,
            exit_eval=exit_res,
        )

        if pos_status == "HOLDING":
            entry_elig_str = "IN POSITION (Managing open BTC spot holding; new entries paused)"
        elif verdict_res["strategy_verdict"] == "ENTRY READY":
            entry_elig_str = (
                "SETUP READY (All 1D Regime, 4H Trend, Pullback Recovery, and Stop gates passed — "
                "setup state only, NOT an order instruction or authorization; operator decides)"
            )
        else:
            entry_elig_str = f"BLOCKED ({verdict_res['decision_state']})"

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
            timestamp_sgt=ts_sgt_str,
            spot_price=spot_px,
            daily_regime=reg_res["regime"],
            daily_close_completed=daily_close_val,
            daily_open_completed=round(float(last_1d_bar.open), 2),
            daily_high_completed=round(float(last_1d_bar.high), 2),
            daily_low_completed=round(float(last_1d_bar.low), 2),
            daily_sma200=daily_sma200_val,
            daily_sma200_prev20=daily_sma200_prev20_val,
            daily_sma200_slope_20d=daily_sma200_slope_val,
            daily_close_above_sma200=bool(daily_sma200_val > 0 and daily_close_val > daily_sma200_val),
            daily_sma200_rising=bool(daily_sma200_val > 0 and daily_sma200_val > daily_sma200_prev20_val),
            trend_4h=trd_res["trend"],
            close_4h_completed=close_4h_val,
            open_4h_completed=open_4h_val,
            high_4h_completed=high_4h_val,
            low_4h_completed=low_4h_val,
            ema50_4h=ema50_4h_val,
            ema50_4h_prev6=ema50_4h_prev6_val,
            ema50_4h_slope_6bars=ema50_4h_slope_val,
            ema200_4h=ema200_4h_val,
            atr14_4h=atr14_4h_val,
            ema50_above_ema200=bool(ema50_4h_val > 0 and ema50_4h_val > ema200_4h_val),
            ema50_rising_6bars=bool(ema50_4h_val > 0 and ema50_4h_val > ema50_4h_prev6_val),
            close_4h_above_ema200=bool(ema200_4h_val > 0 and close_4h_val > ema200_4h_val),
            ema50_1d=ema50_1d_val,
            ema50_1w=ema50_1w_val,
            pullback_zone_lower=zone_lower_val,
            pullback_zone_upper=zone_upper_val,
            max_extension_price=max_ext_val,
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
            daily_sma50=sma50_1d_val,
            daily_close_vs_sma200_usd=daily_close_vs_sma200_usd,
            daily_close_vs_sma200_pct=daily_close_vs_sma200_pct,
            daily_close_vs_sma50_usd=daily_close_vs_sma50_usd,
            daily_close_vs_sma50_pct=daily_close_vs_sma50_pct,
            daily_close_above_sma50=daily_close_above_sma50,
            ema50_minus_ema200_4h_usd=ema50_minus_ema200_4h_usd,
            close_4h_vs_ema50_usd=close_4h_vs_ema50_usd,
            close_4h_vs_ema50_atr=close_4h_vs_ema50_atr,
            close_4h_vs_ema200_usd=close_4h_vs_ema200_usd,
            close_4h_vs_ema200_atr=close_4h_vs_ema200_atr,
            close_4h_above_ema50=close_4h_above_ema50,
            spot_minus_zone_lower_usd=spot_minus_zone_lower_usd,
            spot_minus_zone_lower_atr=spot_minus_zone_lower_atr,
            spot_minus_zone_upper_usd=spot_minus_zone_upper_usd,
            spot_minus_zone_upper_atr=spot_minus_zone_upper_atr,
            candle_4h_low_below_zone_lower=candle_4h_low_below_zone_lower,
            candle_4h_low_above_zone_upper=candle_4h_low_above_zone_upper,
            rec_cond1_low_ge_zone_lower=rec_cond1_low_ge_zone_lower,
            rec_cond2_low_le_zone_upper=rec_cond2_low_le_zone_upper,
            rec_cond3_close_gt_ema50=rec_cond3_close_gt_ema50,
            rec_cond4_close_gt_open=rec_cond4_close_gt_open,
            rec_cond5_close_le_max_ext=rec_cond5_close_le_max_ext,
            rec_all_conditions_met=rec_all_conditions_met,
            spot_to_ref_entry_usd=spot_to_ref_entry_usd,
            spot_to_ref_entry_pct=spot_to_ref_entry_pct,
            stop_dist_ge_min_atr=stop_dist_ge_min_atr,
            stop_dist_le_max_atr=stop_dist_le_max_atr,
            fee_slippage_buffer_usd=fee_slippage_buffer_usd,
            total_risk_le_budget=total_risk_le_budget,
            prev_4h_open_utc=prev_4h_open_utc,
            prev_4h_close_utc=prev_4h_close_utc,
            prev_4h_close=prev_4h_close,
            prev_4h_ema50=prev_4h_ema50,
            prev_4h_close_lt_ema50=prev_4h_close_lt_ema50,
            last_4h_close_lt_ema50=last_4h_close_lt_ema50,
            consecutive_4h_closes_below_ema50=consec_4h_below,
            prev_1d_open_utc=prev_1d_open_utc,
            prev_1d_close_utc=prev_1d_close_utc,
            prev_1d_close=prev_1d_close,
            prev_1d_sma200=prev_1d_sma200,
            prev_1d_close_lt_sma200=prev_1d_close_lt_sma200,
            last_1d_close_lt_sma200=last_1d_close_lt_sma200,
            consecutive_1d_closes_below_sma200=consec_1d_below,
            completed_1d_count=len(comp_1d),
            completed_4h_count=len(comp_4h),
            evaluation_origin="ENGINE_EVALUATE",
            cfg_daily_sma_period=cfg.daily_sma_period,
            cfg_daily_sma_slope_period=cfg.daily_sma_slope_period,
            cfg_ema_fast=cfg.ema_fast,
            cfg_ema_slow=cfg.ema_slow,
            cfg_ema_slope_period=cfg.ema_slope_period,
            cfg_atr_period=cfg.atr_period,
            cfg_pullback_upper_atr=cfg.pullback_upper_atr,
            cfg_pullback_lower_atr=cfg.pullback_lower_atr,
            cfg_recovery_max_extension_atr=cfg.recovery_max_extension_atr,
            cfg_limit_entry_upper_atr=cfg.limit_entry_upper_atr,
            cfg_stop_lookback=cfg.stop_lookback,
            cfg_stop_buffer_atr=cfg.stop_buffer_atr,
            cfg_minimum_stop_atr=cfg.minimum_stop_atr,
            cfg_maximum_stop_atr=cfg.maximum_stop_atr,
            cfg_entry_fee_pct=cfg.entry_fee_pct,
            cfg_exit_fee_pct=cfg.exit_fee_pct,
            cfg_entry_slippage_pct=cfg.entry_slippage_pct,
            cfg_exit_slippage_pct=cfg.exit_slippage_pct,
            cfg_max_daily_stale_hours=cfg.max_daily_stale_hours,
            cfg_max_4h_stale_hours=cfg.max_4h_stale_hours,
        )
        ev.summary_markdown = self._build_markdown_summary(ev)
        store.trend_pullback_evaluation = ev
        return ev

    @staticmethod
    def _build_markdown_summary(ev: TrendPullbackEvaluation) -> str:
        """Builds a strictly DATA-ONLY metrics & boolean conditions report.

        Contains zero interpretive verdicts, recommendations, or forbidden keywords
        (verdict, trade, wait, bullish, bearish, confirmed, rejected, recommend).
        """
        prev_4h_diff = round(ev.prev_4h_close - ev.prev_4h_ema50, 2) if ev.prev_4h_ema50 > 0 else 0.0
        prev_1d_diff = round(ev.prev_1d_close - ev.prev_1d_sma200, 2) if ev.prev_1d_sma200 > 0 else 0.0
        spot_le_stop = bool(ev.structural_stop > 0 and ev.spot_price > 0 and ev.spot_price <= ev.structural_stop)

        d_sma = int(getattr(ev, "cfg_daily_sma_period", 200))
        d_slp = int(getattr(ev, "cfg_daily_sma_slope_period", 20))
        e_fast = int(getattr(ev, "cfg_ema_fast", 50))
        e_slow = int(getattr(ev, "cfg_ema_slow", 200))
        e_slp = int(getattr(ev, "cfg_ema_slope_period", 6))
        atr_p = int(getattr(ev, "cfg_atr_period", 14))
        pb_lo = float(getattr(ev, "cfg_pullback_lower_atr", 0.50))
        pb_hi = float(getattr(ev, "cfg_pullback_upper_atr", 0.25))
        max_ext = float(getattr(ev, "cfg_recovery_max_extension_atr", 1.00))
        lim_hi = float(getattr(ev, "cfg_limit_entry_upper_atr", 0.10))
        stp_lb = int(getattr(ev, "cfg_stop_lookback", 5))
        stp_buf = float(getattr(ev, "cfg_stop_buffer_atr", 0.25))
        min_stp = float(getattr(ev, "cfg_minimum_stop_atr", 0.75))
        max_stp = float(getattr(ev, "cfg_maximum_stop_atr", 3.00))
        ef_pct = float(getattr(ev, "cfg_entry_fee_pct", 0.0010)) * 100.0
        xf_pct = float(getattr(ev, "cfg_exit_fee_pct", 0.0010)) * 100.0
        es_pct = float(getattr(ev, "cfg_entry_slippage_pct", 0.0005)) * 100.0
        xs_pct = float(getattr(ev, "cfg_exit_slippage_pct", 0.0005)) * 100.0
        max_1d_stale = float(getattr(ev, "cfg_max_daily_stale_hours", 48.0))
        max_4h_stale = float(getattr(ev, "cfg_max_4h_stale_hours", 8.5))
        eval_origin = getattr(ev, "evaluation_origin", "STORED")

        lines = [
            f"# {ev.strategy_name} | DATA-ONLY REPORT ({ev.mode_label} | SPOT ONLY)",
            f"**STATUS:** `{ev.strategy_status}` (NOT VALIDATED FOR LIVE CAPITAL)  |  **Origin:** `{eval_origin}`  |  **Retrieval Time (UTC):** `{ev.timestamp_utc}`  |  **Retrieval Time (SGT):** `{ev.timestamp_sgt}`",
            f"**Spot Price (BTCUSDT):** `${ev.spot_price:,.2f}`",
            "",
            "## 1. DAILY (1D)",
            f"- **Completed 1D Candle Window:** `Open {ev.daily_open_time_utc} -> Close {ev.daily_close_time_utc}`",
            f"- **Last Completed 1D Close:** `${ev.daily_close_completed:,.2f}` (Open `${ev.daily_open_completed:,.2f}`, High `${ev.daily_high_completed:,.2f}`, Low `${ev.daily_low_completed:,.2f}`)",
            f"- **Daily SMA50:** `${ev.daily_sma50:,.2f}`",
            f"- **Daily SMA{d_sma}:** `${ev.daily_sma200:,.2f}` ({d_slp}D Prior SMA{d_sma}: `${ev.daily_sma200_prev20:,.2f}`)",
            f"- **Daily SMA{d_sma} {d_slp}D Slope (`SMA{d_sma}_now - SMA{d_sma}_{d_slp}d_ago`):** `${ev.daily_sma200_slope_20d:+,.2f}`",
            f"- **Close vs SMA{d_sma} (`Close - SMA{d_sma}`):** `${ev.daily_close_vs_sma200_usd:+,.2f}` (`{ev.daily_close_vs_sma200_pct:+.2f}%`)",
            f"- **Close vs SMA50 (`Close - SMA50`):** `${ev.daily_close_vs_sma50_usd:+,.2f}` (`{ev.daily_close_vs_sma50_pct:+.2f}%`)",
            f"- **Close > SMA{d_sma}:** `{ev.daily_close_above_sma200}`",
            f"- **Close > SMA50:** `{ev.daily_close_above_sma50}`",
            f"- **SMA{d_sma} Rising Over {d_slp}D (`SMA{d_sma}_now > SMA{d_sma}_{d_slp}d_ago`):** `{ev.daily_sma200_rising}`",
            "",
            "## 2. 4H TREND METRICS",
            f"- **Completed 4H Candle Window:** `Open {ev.candle_4h_open_time_utc} -> Close {ev.candle_4h_close_time_utc}`",
            f"- **Last Completed 4H Close:** `${ev.close_4h_completed:,.2f}`",
            f"- **4H EMA{e_fast}:** `${ev.ema50_4h:,.2f}`",
            f"- **4H EMA{e_slow}:** `${ev.ema200_4h:,.2f}`",
            f"- **4H ATR{atr_p}:** `${ev.atr14_4h:,.2f}`",
            f"- **4H EMA{e_fast} - EMA{e_slow}:** `${ev.ema50_minus_ema200_4h_usd:+,.2f}`",
            f"- **4H EMA{e_fast} Now vs {e_slp} Bars Ago:** Now `${ev.ema50_4h:,.2f}` vs {e_slp} Bars Ago `${ev.ema50_4h_prev6:,.2f}` (`{ev.ema50_4h_slope_6bars:+,.2f}` USD)",
            f"- **Last 4H Close vs 4H EMA{e_fast} (`Close - EMA{e_fast}`):** `${ev.close_4h_vs_ema50_usd:+,.2f}` (`{ev.close_4h_vs_ema50_atr:+.4f} ATR` / `{ev.close_4h_vs_ema50_atr:+.2f} ATR`)",
            f"- **Last 4H Close vs 4H EMA{e_slow} (`Close - EMA{e_slow}`):** `${ev.close_4h_vs_ema200_usd:+,.2f}` (`{ev.close_4h_vs_ema200_atr:+.4f} ATR` / `{ev.close_4h_vs_ema200_atr:+.2f} ATR`)",
            f"- **4H EMA{e_fast} > 4H EMA{e_slow}:** `{ev.ema50_above_ema200}`",
            f"- **4H EMA{e_fast} Rising Over {e_slp} Bars (`EMA{e_fast}_now > EMA{e_fast}_{e_slp}bars_ago`):** `{ev.ema50_rising_6bars}`",
            f"- **Last 4H Close > 4H EMA{e_slow}:** `{ev.close_4h_above_ema200}`",
            "",
            "## 3. PULLBACK ZONE",
            f"- **Pullback Zone Formula:** `Zone Lower = 4H EMA{e_fast} - {pb_lo:.2f} * 4H ATR{atr_p}` | `Zone Upper = 4H EMA{e_fast} + {pb_hi:.2f} * 4H ATR{atr_p}` | `Max Extension = 4H EMA{e_fast} + {max_ext:.2f} * 4H ATR{atr_p}`",
            f"- **Zone Lower (`EMA{e_fast} - {pb_lo:.2f} * ATR{atr_p}`):** `${ev.pullback_zone_lower:,.2f}`",
            f"- **Zone Upper (`EMA{e_fast} + {pb_hi:.2f} * ATR{atr_p}`):** `${ev.pullback_zone_upper:,.2f}`",
            f"- **Max Extension (`EMA{e_fast} + {max_ext:.2f} * ATR{atr_p}`):** `${ev.max_extension_price:,.2f}`",
            f"- **Spot Minus Zone Lower (`Spot - Zone Lower`):** `${ev.spot_minus_zone_lower_usd:+,.2f}` (`{ev.spot_minus_zone_lower_atr:+.4f} ATR` / `{ev.spot_minus_zone_lower_atr:+.2f} ATR`)",
            f"- **Spot Minus Zone Upper (`Spot - Zone Upper`):** `${ev.spot_minus_zone_upper_usd:+,.2f}` (`{ev.spot_minus_zone_upper_atr:+.4f} ATR` / `{ev.spot_minus_zone_upper_atr:+.2f} ATR`)",
            f"- **Last Completed 4H Candle OHLC:** Open `${ev.open_4h_completed:,.2f}`, High `${ev.high_4h_completed:,.2f}`, Low `${ev.low_4h_completed:,.2f}`, Close `${ev.close_4h_completed:,.2f}`",
            f"- **Candle Low < Zone Lower:** `{ev.candle_4h_low_below_zone_lower}`",
            f"- **Candle Low > Zone Upper:** `{ev.candle_4h_low_above_zone_upper}`",
            "- **Recovery Candle Sub-Conditions (Last Completed 4H Candle):**",
            f"  - `Candle Low >= Zone Lower`: `{ev.rec_cond1_low_ge_zone_lower}`",
            f"  - `Candle Low <= Zone Upper`: `{ev.rec_cond2_low_le_zone_upper}`",
            f"  - `Candle Close > 4H EMA{e_fast}`: `{ev.rec_cond3_close_gt_ema50}`",
            f"  - `Candle Close > Candle Open`: `{ev.rec_cond4_close_gt_open}`",
            f"  - `Candle Close <= 4H EMA{e_fast} + {max_ext:.2f} * 4H ATR{atr_p}`: `{ev.rec_cond5_close_le_max_ext}`",
            f"  - `All 5 Recovery Sub-Conditions True`: `{ev.rec_all_conditions_met}`",
            "",
            f"## 4. REFERENCE LEVELS (Reference calculation if entered at ${ev.reference_entry_price:,.2f}. Not an order. Simulated on ${ev.simulation_equity_usd:,.0f} reference paper account — NOT sized to operator's account.)",
            f"- **Reference Entry Zone (`[4H EMA{e_fast}, 4H EMA{e_fast} + {lim_hi:.2f} * 4H ATR{atr_p}]`):** `${ev.limit_entry_low:,.2f} - ${ev.limit_entry_high:,.2f}`",
            f"- **Reference Entry Price Used (`4H EMA{e_fast} + {lim_hi:.2f} * 4H ATR{atr_p}`):** `${ev.reference_entry_price:,.2f}`",
            f"- **Distance From Spot To Reference Entry (`Spot - Reference Entry`):** `${ev.spot_to_ref_entry_usd:+,.2f}` (`{ev.spot_to_ref_entry_pct:+.2f}%`)",
            f"- **Stop Level (`min(low of last {stp_lb} completed 4H bars) - {stp_buf:.2f} * 4H ATR{atr_p}`):** `${ev.structural_stop:,.2f}` ({stp_lb}-Bar Lowest Low `${ev.stop_lowest_low_5bars:,.2f}` - Buffer `${ev.stop_buffer_usd:,.2f}`)",
            f"- **Stop Distance From Reference Entry (`Reference Entry ${ev.reference_entry_price:,.2f} - Stop Level ${ev.structural_stop:,.2f}`):** `${ev.stop_distance_usd:,.2f}` (`{ev.stop_distance_atr_exact:.4f} ATR` / `{ev.stop_distance_atr:.2f} ATR`)",
            f"- **Stop Distance >= {min_stp:.2f} ATR:** `{ev.stop_dist_ge_min_atr}`",
            f"- **Stop Distance <= {max_stp:.2f} ATR:** `{ev.stop_dist_le_max_atr}`",
            f"- **Reference Simulation Equity (Fictional Paper Account, NOT Operator Equity):** `${ev.simulation_equity_usd:,.2f}`",
            f"- **Simulated Risk Budget (`{ev.risk_per_trade_pct:.2f}%` of `${ev.simulation_equity_usd:,.0f}` reference account, NOT operator account):** `${ev.risk_budget_usd:,.2f}`",
            f"- **Simulated Position Size (on `${ev.simulation_equity_usd:,.0f}` reference account, NOT operator account):** `{ev.position_size_btc:.5f} BTC`",
            f"- **Simulated Position Notional (`Position Size * Reference Entry ${ev.reference_entry_price:,.2f}`, on `${ev.simulation_equity_usd:,.0f}` reference account, NOT operator account):** `${ev.position_value_usd:,.2f}`",
            f"- **Computed Price Risk (`Position Size * Stop Distance ${ev.stop_distance_usd:,.2f}`):** `${ev.gross_price_risk_usd:,.2f}` (`${ev.gross_price_risk_per_btc:,.2f}/BTC`)",
            f"- **Fee & Slippage Buffer (`{ef_pct:.2f}%` Entry Fee + `{xf_pct:.2f}%` Exit Fee + `{es_pct:.2f}%` Entry Slippage + `{xs_pct:.2f}%` Exit Slippage):** `${ev.fee_slippage_buffer_usd:,.2f}` (`${ev.cost_allowance_per_btc:,.2f}/BTC`: Entry Fee `${ev.entry_fee_usd:,.2f}` + Exit Fee `${ev.exit_fee_usd:,.2f}` + Entry Slippage `${ev.entry_slippage_usd:,.2f}` + Exit Slippage `${ev.exit_slippage_usd:,.2f}`)",
            f"- **Total Estimated Risk (`Computed Price Risk + Fee & Slippage Buffer`):** `${ev.total_estimated_risk_usd:,.2f}` (`${ev.total_risk_per_btc:,.2f}/BTC`)",
            f"- **Total Estimated Risk <= Simulated Risk Budget (`${ev.total_estimated_risk_usd:,.2f} <= ${ev.risk_budget_usd:,.2f}`):** `{ev.total_risk_le_budget}`",
            "",
            "## 5. EXIT RULE INPUTS",
            f"- **Position Mode Setting:** `{ev.position_status}`",
            f"- **Completed 4H Candle (t-1) (`Open {ev.prev_4h_open_utc} -> Close {ev.prev_4h_close_utc}`):** Close `${ev.prev_4h_close:,.2f}` vs 4H EMA{e_fast} `${ev.prev_4h_ema50:,.2f}` (`{prev_4h_diff:+,.2f}` USD) | `Close < 4H EMA{e_fast}`: `{ev.prev_4h_close_lt_ema50}`",
            f"- **Completed 4H Candle (t) (`Open {ev.candle_4h_open_time_utc} -> Close {ev.candle_4h_close_time_utc}`):** Close `${ev.close_4h_completed:,.2f}` vs 4H EMA{e_fast} `${ev.ema50_4h:,.2f}` (`{ev.close_4h_vs_ema50_usd:+,.2f}` USD) | `Close < 4H EMA{e_fast}`: `{ev.last_4h_close_lt_ema50}`",
            f"- **Consecutive Completed 4H Closes Below 4H EMA{e_fast}:** `{ev.consecutive_4h_closes_below_ema50}`",
            f"- **Completed 1D Candle (t-1) (`Open {ev.prev_1d_open_utc} -> Close {ev.prev_1d_close_utc}`):** Close `${ev.prev_1d_close:,.2f}` vs 1D SMA{d_sma} `${ev.prev_1d_sma200:,.2f}` (`{prev_1d_diff:+,.2f}` USD) | `Close < 1D SMA{d_sma}`: `{ev.prev_1d_close_lt_sma200}`",
            f"- **Completed 1D Candle (t) (`Open {ev.daily_open_time_utc} -> Close {ev.daily_close_time_utc}`):** Close `${ev.daily_close_completed:,.2f}` vs 1D SMA{d_sma} `${ev.daily_sma200:,.2f}` (`{ev.daily_close_vs_sma200_usd:+,.2f}` USD) | `Close < 1D SMA{d_sma}`: `{ev.last_1d_close_lt_sma200}`",
            f"- **Consecutive Completed 1D Closes Below 1D SMA{d_sma}:** `{ev.consecutive_1d_closes_below_sma200}`",
            f"- **Spot <= Stop Level (`${ev.spot_price:,.2f} <= ${ev.structural_stop:,.2f}`):** `{spot_le_stop}`",
            "",
            "## 6. DATA INTEGRITY",
            f"- **Data Retrieval Time (UTC):** `{ev.timestamp_utc}`",
            f"- **Data Retrieval Time (SGT):** `{ev.timestamp_sgt}`",
            f"- **Data Integrity Pass:** `{ev.data_integrity_ok}`",
            f"- **Completed 1D Candles Available:** `{ev.completed_1d_count}` | **Last Completed 1D Status:** `{ev.daily_candle_status}` (Stale Limit `<= {max_1d_stale:.1f}h`) | **Forming 1D Candle Excluded:** `{ev.daily_forming_excluded}` (`{ev.daily_forming_open_utc}`)",
            f"- **Completed 4H Candles Available:** `{ev.completed_4h_count}` | **Last Completed 4H Status:** `{ev.candle_4h_status}` (Stale Limit `<= {max_4h_stale:.1f}h`) | **Forming 4H Candle Excluded:** `{ev.candle_4h_forming_excluded}` (`{ev.candle_4h_forming_open_utc}`)",
        ]
        if ev.integrity_failure_reason:
            lines.append(f"- **Data Integrity Failure Reason:** `{ev.integrity_failure_reason}`")
        return "\n".join(lines)


def get_or_recompute_trend_pullback(
    config: Optional[EngineConfig],
    store: StateStore,
    *,
    recompute: bool = False,
) -> Tuple[Optional[TrendPullbackEvaluation], bool]:
    """Returns the stored TrendPullbackEvaluation; only recomputes when explicitly requested."""
    stored = getattr(store, "trend_pullback_evaluation", None)
    if stored is not None:
        return stored, False
    if not recompute:
        return None, False
    ev = TrendPullbackEngine(config).evaluate(store)
    ev.evaluation_origin = "EXPLICIT_RECOMPUTE"
    ev.summary_markdown = TrendPullbackEngine._build_markdown_summary(ev)
    return ev, True


def copy_trend_pullback_to_clipboard(
    store: StateStore,
    *,
    recompute: bool = False,
) -> Tuple[bool, str, int]:
    """Copies BTC Trend-Pullback v1.0 brief to system clipboard and saves to logs/."""
    from analytics.data_only_reports import build_tab_a_data_only_report

    text = build_tab_a_data_only_report(None, store, recompute=recompute)
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
