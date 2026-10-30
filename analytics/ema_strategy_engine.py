"""Industrial 3-EMA Bidirectional Strategy Engine (Daily & 4H) with Positioning & ADX Filters.

Strategy Rules:
1. Regime & Bias (Daily):
   - Strong Bull: Price > rising 200 EMA and 20 > 50 > 200 -> Longs only (full size 0.75%)
   - Weak Bull: Price > 200 EMA but not fully aligned -> Longs only (reduced size) or cash
   - Strong Bear: Price < falling 200 EMA and 20 < 50 < 200 -> Stand aside / 100% Cash (Spot Mandate)
   - Weak Bear: Price < 200 EMA but tangled -> Stand aside / 100% Cash
   - Neutral: Flat 200 EMA or price chopping around it -> No new trades
2. Trend Quality Filter:
   - ADX(14) on Daily or 4H must be >= 20.
3. Pullback Location:
   - Price pulls back to 50 EMA (Daily) or 21-50 EMA zone (4H).
4. Positioning Confirmation (at least 2 of 3):
   - Open Interest declining or stable during pullback.
   - Funding Rate neutral or negative (<= +0.010%).
   - Spot CVD rising or diverging positively vs Perp.
5. Trigger:
   - 4H candle closes back above 9 EMA or 20 EMA + Rejection.
"""

from typing import List, Optional, Sequence
import numpy as np

from config.settings import EngineConfig
from core.models import (
    DerivativesSnapshot,
    EMAStrategySnapshot,
    FlowSnapshot,
    KlineBar,
    OIPositioningQuadrant,
)
from core.state_store import StateStore


def compute_ema_series(values: Sequence[float], period: int) -> List[float]:
    """Computes standard Exponential Moving Average series with SMA seed."""
    if len(values) < period:
        return [float(v) for v in values]
    
    ema = [0.0] * len(values)
    # Seed with SMA
    sma_seed = sum(values[:period]) / period
    for i in range(period - 1):
        ema[i] = values[i]
    ema[period - 1] = sma_seed
    
    multiplier = 2.0 / (period + 1.0)
    for i in range(period, len(values)):
        ema[i] = (values[i] - ema[i - 1]) * multiplier + ema[i - 1]
    
    return ema


def compute_adx(
    highs: Sequence[float],
    lows: Sequence[float],
    closes: Sequence[float],
    period: int = 14,
) -> float:
    """Computes Wilder's Average Directional Index (ADX) over specified period."""
    n = len(closes)
    if n < period * 2:
        return 15.0  # Default neutral/low ADX if insufficient data

    tr_list = [0.0] * n
    plus_dm = [0.0] * n
    minus_dm = [0.0] * n

    for i in range(1, n):
        h_diff = highs[i] - highs[i - 1]
        l_diff = lows[i - 1] - lows[i]

        plus_dm[i] = h_diff if (h_diff > l_diff and h_diff > 0) else 0.0
        minus_dm[i] = l_diff if (l_diff > h_diff and l_diff > 0) else 0.0

        tr_list[i] = max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i - 1]),
            abs(lows[i] - closes[i - 1]),
        )

    # Wilder's smoothing
    tr_smooth = sum(tr_list[1 : period + 1])
    plus_dm_smooth = sum(plus_dm[1 : period + 1])
    minus_dm_smooth = sum(minus_dm[1 : period + 1])

    dx_list = []
    for i in range(period + 1, n):
        tr_smooth = tr_smooth - (tr_smooth / period) + tr_list[i]
        plus_dm_smooth = plus_dm_smooth - (plus_dm_smooth / period) + plus_dm[i]
        minus_dm_smooth = minus_dm_smooth - (minus_dm_smooth / period) + minus_dm[i]

        plus_di = (100.0 * plus_dm_smooth / tr_smooth) if tr_smooth > 0 else 0.0
        minus_di = (100.0 * minus_dm_smooth / tr_smooth) if tr_smooth > 0 else 0.0

        di_sum = plus_di + minus_di
        dx = (100.0 * abs(plus_di - minus_di) / di_sum) if di_sum > 0 else 0.0
        dx_list.append(dx)

    if len(dx_list) < period:
        return float(np.mean(dx_list)) if dx_list else 15.0

    # Wilder's smoothing for ADX
    adx = sum(dx_list[:period]) / period
    for dx in dx_list[period:]:
        adx = (adx * (period - 1) + dx) / period

    return float(round(adx, 1))


class EMAStrategyEngine:
    """Evaluates the 3-EMA Industrial system and generates a compact confluence snapshot."""

    def __init__(self, config: EngineConfig) -> None:
        self.config = config

    def evaluate(
        self,
        store: StateStore,
        spot_1d: Sequence[KlineBar],
        bars_4h: Sequence[KlineBar],
        current_price: float,
        flow: FlowSnapshot,
        deriv: DerivativesSnapshot,
        atr_4h: float,
    ) -> EMAStrategySnapshot:
        """Runs the complete 3-EMA Industrial evaluation cycle."""
        # 1. Daily EMAs & ADX
        daily_closes = [b.close for b in spot_1d]
        daily_highs = [b.high for b in spot_1d]
        daily_lows = [b.low for b in spot_1d]

        d_ema_20 = 0.0
        d_ema_50 = 0.0
        d_ema_200 = 0.0
        d_ema_200_slope = 0.0
        daily_adx = 0.0

        if len(daily_closes) >= 50:
            ema20_series = compute_ema_series(daily_closes, 20)
            ema50_series = compute_ema_series(daily_closes, 50)
            d_ema_20 = ema20_series[-1]
            d_ema_50 = ema50_series[-1]

            if len(daily_closes) >= 200:
                ema200_series = compute_ema_series(daily_closes, 200)
                d_ema_200 = ema200_series[-1]
                if len(ema200_series) >= 5:
                    d_ema_200_slope = (ema200_series[-1] - ema200_series[-5]) / 5.0
            else:
                # Approximate 200 EMA if slightly fewer bars available
                d_ema_200 = float(np.mean(daily_closes[-len(daily_closes):]))
                d_ema_200_slope = 0.0

            daily_adx = compute_adx(daily_highs, daily_lows, daily_closes, period=14)

        # 2. 4H EMAs & ADX
        closes_4h = [b.close for b in bars_4h]
        highs_4h = [b.high for b in bars_4h]
        lows_4h = [b.low for b in bars_4h]

        ema_4h_9 = 0.0
        ema_4h_20 = 0.0
        ema_4h_50 = 0.0
        ema_4h_200 = 0.0
        adx_4h = 0.0

        if len(closes_4h) >= 50:
            ema_4h_9 = compute_ema_series(closes_4h, 9)[-1]
            ema_4h_20 = compute_ema_series(closes_4h, 20)[-1]
            ema_4h_50 = compute_ema_series(closes_4h, 50)[-1]
            if len(closes_4h) >= 200:
                ema_4h_200 = compute_ema_series(closes_4h, 200)[-1]
            else:
                ema_4h_200 = float(np.mean(closes_4h))
            adx_4h = compute_adx(highs_4h, lows_4h, closes_4h, period=14)

        # 3. Classify Daily Regime & Bias Filter
        daily_regime = "NEUTRAL"
        if d_ema_200 > 0:
            dist_to_200_pct = abs(current_price - d_ema_200) / d_ema_200 * 100.0
            is_flat_200 = abs(d_ema_200_slope) < (d_ema_200 * 0.0001)

            if is_flat_200 or dist_to_200_pct < 0.4:
                daily_regime = "NEUTRAL"
            elif current_price > d_ema_200:
                if d_ema_200_slope > 0 and (d_ema_20 > d_ema_50 > d_ema_200):
                    daily_regime = "STRONG_BULL"
                else:
                    daily_regime = "WEAK_BULL"
            else:
                if d_ema_200_slope < 0 and (d_ema_20 < d_ema_50 < d_ema_200):
                    daily_regime = "STRONG_BEAR"
                else:
                    daily_regime = "WEAK_BEAR"

        # 4. Trend Quality Filter: ADX >= 20
        trend_quality_pass = (daily_adx >= 20.0 or adx_4h >= 20.0)

        # 5. Location: Pullback into 50 EMA / 21-50 EMA Zone
        pullback_zone_active = False
        if ema_4h_50 > 0:
            # 50 EMA zone on 4H: within 1.2 ATR of 50 EMA, or between 20 EMA and 50 EMA
            zone_low = min(ema_4h_20, ema_4h_50) - 1.2 * atr_4h
            zone_high = max(ema_4h_20, ema_4h_50) + 0.5 * atr_4h
            if zone_low <= current_price <= zone_high:
                pullback_zone_active = True
        elif d_ema_50 > 0:
            # Daily 50 EMA fallback
            if abs(current_price - d_ema_50) <= (1.2 * atr_4h):
                pullback_zone_active = True

        # Rejection Evidence: Check recent 4H candle wick or close
        rejection_active = False
        if bars_4h:
            last_4h = bars_4h[-1]
            body = abs(last_4h.close - last_4h.open)
            candle_range = max(last_4h.high - last_4h.low, 1.0)
            lower_wick = min(last_4h.open, last_4h.close) - last_4h.low
            if (lower_wick / candle_range) >= 0.30 or (last_4h.close > last_4h.open and body / candle_range >= 0.50):
                rejection_active = True

        # 6. Positioning Confirmation (at least 2 of 3)
        # Condition 1: Open Interest declining or stable during pullback
        c1_oi = (
            deriv.oi_change_1h_pct <= 0.25
            or deriv.oi_change_4h_pct <= 0.50
            or deriv.oi_regime_quadrant == OIPositioningQuadrant.LONG_LIQUIDATION_FLUSH
            or deriv.oi_regime_quadrant == OIPositioningQuadrant.AGGRESSIVE_SHORT_BUILD
        )

        # Condition 2: Funding Rate neutral or negative (<= +0.010%)
        c2_funding = deriv.funding_rate_pct <= self.config.funding_neutral_max_pct

        # Condition 3: Spot CVD supportive or diverging positively vs Perp
        c3_cvd = (
            flow.w_1h.spot_zscore >= 0.20
            or flow.w_1h.flow_divergence_z >= 1.0
            or flow.w_1h.absorption_index >= 0.70
            or flow.session_spot_cvd > 0
            or flow.bullish_pivot_divergence
        )

        positioning_confirmations = sum([bool(c1_oi), bool(c2_funding), bool(c3_cvd)])
        positioning_pass = positioning_confirmations >= 2

        # 7. Trigger: 4H close back above 9 EMA or 20 EMA
        trigger_active = False
        if ema_4h_9 > 0 or ema_4h_20 > 0:
            trigger_active = (current_price >= ema_4h_9 or current_price >= ema_4h_20)

        # 8. Setup Status Classification
        if daily_regime in ("STRONG_BULL", "WEAK_BULL"):
            if pullback_zone_active and positioning_pass:
                if trigger_active and trend_quality_pass:
                    setup_status = "LONG_TRIGGERED"
                else:
                    setup_status = "LONG_WATCH"
            elif pullback_zone_active:
                setup_status = "PULLBACK_TESTING"
            else:
                setup_status = "BULL_TREND_HOLDING"
        elif daily_regime in ("STRONG_BEAR", "WEAK_BEAR"):
            setup_status = "BEAR_REGIME (STAY CASH)"
        else:
            setup_status = "NEUTRAL_CHOP (AVOID)"

        # 9. Stop Loss Math (1.2 - 1.5 x ATR below 50 EMA)
        ref_50 = ema_4h_50 if ema_4h_50 > 0 else d_ema_50
        suggested_atr_stop = round(max(0.0, ref_50 - 1.35 * atr_4h), 2)
        suggested_risk = 0.75 if daily_regime == "STRONG_BULL" else 0.50

        summary_text = (
            f"Daily {daily_regime} (200 EMA ${d_ema_200:,.0f} | ADX {daily_adx:.1f}) • "
            f"4H 50-EMA ${ema_4h_50:,.0f} • Pos: {positioning_confirmations}/3 • Status: {setup_status}"
        )

        return EMAStrategySnapshot(
            daily_regime=daily_regime,
            daily_ema_20=round(d_ema_20, 2),
            daily_ema_50=round(d_ema_50, 2),
            daily_ema_200=round(d_ema_200, 2),
            daily_ema_200_slope=round(d_ema_200_slope, 2),
            daily_adx=round(daily_adx, 1),
            ema_4h_9=round(ema_4h_9, 2),
            ema_4h_20=round(ema_4h_20, 2),
            ema_4h_50=round(ema_4h_50, 2),
            ema_4h_200=round(ema_4h_200, 2),
            adx_4h=round(adx_4h, 1),
            trend_quality_pass=trend_quality_pass,
            pullback_zone_active=pullback_zone_active,
            rejection_active=rejection_active,
            positioning_confirmations_met=positioning_confirmations,
            positioning_pass=positioning_pass,
            trigger_active=trigger_active,
            setup_status=setup_status,
            suggested_atr_stop=suggested_atr_stop,
            suggested_risk_pct=suggested_risk,
            summary_text=summary_text,
        )
