"""Special Tab [S3]: Gartley 222 Harmonics & 5-Strategy Spot Swing Confluence Engine.

Faithfully implements the multi-horizon quantitative radar ported from Pine Script:
- S1: 20-bar Donchian Channel Breakout
- S2: 200 SMA Structural Gatekeeper
- S3: EMA 20 / 50 Golden / Death Cross
- S4: 14-period RSI Reversal (30 oversold / 50 reclaim)
- S5: 20-period 2-Sigma Bollinger Bands Mean Reversion
- S6: Bullish Gartley 222 Harmonic (L-H-L-H-L: X < B < D < A, Fibonacci PRZ)
- S7: Bearish Gartley 222 Harmonic (H-L-H-L-H: X > B > D > A, Fibonacci PRZ)

Dual Horizon Architecture:
- 1D Macro Trend: Establishes overall regime (HOLD, NO TRADE, BULL CONFLUENCE)
- 4H Tactical Swing: Generates execution triggers and risk containment
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

from config.settings import EngineConfig
from core.models import Gartley5StrategyEvaluation, GartleyTimeframeResult, KlineBar
from core.state_store import StateStore
from .volume_profile import synthesize_4h_bars


def check_gartley_ratios(
    X: float, A: float, B: float, C: float, D: float
) -> Tuple[bool, Dict[str, float]]:
    """Validates Gartley 222 harmonic Fibonacci retracement and projection ratios.

    Target Ratios:
    - B / XA: 0.618 (acceptable range: [0.55, 0.72])
    - C / AB: 0.382 - 0.886 (acceptable range: [0.382, 0.886])
    - D / XA: 0.786 (acceptable range: [0.68, 0.86])
    - AB / CD: 0.70 - 1.50 (acceptable range: [0.70, 1.50])
    """
    XA = abs(A - X)
    AB = abs(B - A)
    BC = abs(C - B)
    CD = abs(D - C)
    AD = abs(A - D)

    if min(XA, AB, BC, CD) == 0:
        return False, {}

    br = AB / XA
    cr = BC / AB
    dr = AD / XA
    abcd = AB / CD

    ok = (
        (0.55 <= br <= 0.72)
        and (0.382 <= cr <= 0.886)
        and (0.68 <= dr <= 0.86)
        and (0.70 <= abcd <= 1.50)
    )

    ratios = {
        "B/XA": round(br, 2),
        "C/AB": round(cr, 2),
        "D/XA": round(dr, 2),
        "AB/CD": round(abcd, 2),
    }
    return ok, ratios


def compute_quant_horizon(
    bars: Sequence[KlineBar],
    tf: str = "4h",
) -> Optional[GartleyTimeframeResult]:
    """Evaluates the 5-strategy state machine + Gartley 222 harmonics for a specific horizon."""
    if len(bars) < 25:
        return None

    high = np.array([b.high for b in bars], dtype=float)
    low = np.array([b.low for b in bars], dtype=float)
    close = np.array([b.close for b in bars], dtype=float)
    n = len(bars)

    s_high = pd.Series(high)
    s_low = pd.Series(low)
    s_close = pd.Series(close)

    # --- S1: 20-bar Breakout ---
    hh20 = s_high.shift(1).rolling(20, min_periods=10).max().values
    ll20 = s_low.shift(1).rolling(20, min_periods=10).min().values
    s1E = s_close > hh20
    s1X = s_close < ll20

    # --- S2: 200 SMA ---
    sma200 = s_close.rolling(200, min_periods=20).mean().values
    s_sma200 = pd.Series(sma200)
    s2E = (s_close.shift(1) <= s_sma200.shift(1)) & (s_close > sma200)
    s2X = (s_close.shift(1) >= s_sma200.shift(1)) & (s_close < sma200)

    # --- S3: EMA 20/50 ---
    ema20 = s_close.ewm(span=20, adjust=False).mean().values
    ema50 = s_close.ewm(span=50, adjust=False).mean().values
    s_ema20 = pd.Series(ema20)
    s_ema50 = pd.Series(ema50)
    s3E = (s_ema20.shift(1) <= s_ema50.shift(1)) & (ema20 > ema50)
    s3X = (s_ema20.shift(1) >= s_ema50.shift(1)) & (ema20 < ema50)

    # --- S4: 14 RSI ---
    delta = s_close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / 14, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / 14, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, 1e-9)
    rsi = (100 - (100 / (1 + rs))).values
    s_rsi = pd.Series(rsi)
    s4E = (s_rsi.shift(1) >= 30) & (s_rsi < 30)
    s4X = (s_rsi.shift(1) <= 50) & (s_rsi > 50)

    # --- S5: Bollinger Bands (20, 2) ---
    sma20 = s_close.rolling(20, min_periods=10).mean().values
    stdev20 = s_close.rolling(20, min_periods=10).std().values
    lower_bb = sma20 - 2 * stdev20
    s_lower_bb = pd.Series(lower_bb)
    s_sma20 = pd.Series(sma20)
    s5E = (s_close.shift(1) >= s_lower_bb.shift(1)) & (s_close < lower_bb)
    s5X = (s_close.shift(1) <= s_sma20.shift(1)) & (s_close > sma20)

    # --- S6 & S7: Gartley 222 Harmonics ---
    lenG = 12 if tf.lower() == "4h" else 7
    highsG: List[float] = []
    lowsG: List[float] = []
    bullX: Optional[float] = None
    bullA: Optional[float] = None
    bullD: Optional[float] = None
    bearX: Optional[float] = None
    bearA: Optional[float] = None
    bearD: Optional[float] = None
    bull_ratios: Dict[str, float] = {}
    bear_ratios: Dict[str, float] = {}
    bars_since_bull = 999
    bars_since_bear = 999

    long1 = long2 = long3 = long4 = long5 = long6 = long7 = False

    isNew1 = isNew2 = isNew3 = isNew4 = isNew5 = isNew6 = isNew7 = False
    isExit1 = isExit2 = isExit3 = isExit4 = isExit5 = isExit6 = isExit7 = False

    for i in range(n):
        # Update swing pivots
        if i >= lenG * 2:
            p = i - lenG
            window_high = high[p - lenG : p + lenG + 1]
            window_low = low[p - lenG : p + lenG + 1]
            if len(window_high) > 0 and high[p] == np.max(window_high):
                highsG.append(float(high[p]))
                if len(highsG) > 30:
                    highsG.pop(0)
            if len(window_low) > 0 and low[p] == np.min(window_low):
                lowsG.append(float(low[p]))
                if len(lowsG) > 30:
                    lowsG.pop(0)

        # Bullish Gartley L-H-L-H-L
        bullSignal = False
        if len(lowsG) >= 3 and len(highsG) >= 2:
            X_pt, A_pt, B_pt, C_pt, D_pt = lowsG[-3], highsG[-2], lowsG[-2], highsG[-1], lowsG[-1]
            ok, ratios = check_gartley_ratios(X_pt, A_pt, B_pt, C_pt, D_pt)
            if ok and X_pt < B_pt and B_pt < D_pt and D_pt < A_pt:
                bullSignal = True
                bullX, bullA, bullD = X_pt, A_pt, D_pt
                bull_ratios = ratios
                bars_since_bull = 0

        # Bearish Gartley H-L-H-L-H
        bearSignal = False
        if len(highsG) >= 3 and len(lowsG) >= 2:
            X_pt, A_pt, B_pt, C_pt, D_pt = highsG[-3], lowsG[-2], highsG[-2], lowsG[-1], highsG[-1]
            ok, ratios = check_gartley_ratios(X_pt, A_pt, B_pt, C_pt, D_pt)
            if ok and X_pt > B_pt and B_pt > D_pt and D_pt > A_pt:
                bearSignal = True
                bearX, bearA, bearD = X_pt, A_pt, D_pt
                bear_ratios = ratios
                bars_since_bear = 0

        bars_since_bull += 1
        bars_since_bear += 1

        s6E = bullSignal
        s6X = (
            (bullA is not None and close[i] > bullA)
            or (bullX is not None and close[i] < bullX)
            or (bars_since_bull > 40)
        )
        s7E = bearSignal
        s7X = (
            (bearA is not None and close[i] < bearA)
            or (bearX is not None and close[i] > bearX)
            or (bars_since_bear > 40)
        )

        p1, p2, p3, p4, p5, p6, p7 = long1, long2, long3, long4, long5, long6, long7

        if s1E.iloc[i] and not long1:
            long1 = True
        if s1X.iloc[i] and long1:
            long1 = False

        if s2E.iloc[i] and not long2:
            long2 = True
        if s2X.iloc[i] and long2:
            long2 = False

        if s3E.iloc[i] and not long3:
            long3 = True
        if s3X.iloc[i] and long3:
            long3 = False

        if s4E.iloc[i] and not long4:
            long4 = True
        if s4X.iloc[i] and long4:
            long4 = False

        if s5E.iloc[i] and not long5:
            long5 = True
        if s5X.iloc[i] and long5:
            long5 = False

        if s6E and not long6:
            long6 = True
        if s6X and long6:
            long6 = False

        if s7E and not long7:
            long7 = True
        if s7X and long7:
            long7 = False

        if i == n - 1:
            isNew1 = bool(s1E.iloc[i] and not p1)
            isExit1 = bool(s1X.iloc[i] and p1)
            isNew2 = bool(s2E.iloc[i] and not p2)
            isExit2 = bool(s2X.iloc[i] and p2)
            isNew3 = bool(s3E.iloc[i] and not p3)
            isExit3 = bool(s3X.iloc[i] and p3)
            isNew4 = bool(s4E.iloc[i] and not p4)
            isExit4 = bool(s4X.iloc[i] and p4)
            isNew5 = bool(s5E.iloc[i] and not p5)
            isExit5 = bool(s5X.iloc[i] and p5)
            isNew6 = bool(s6E and not p6)
            isExit6 = bool(s6X and p6)
            isNew7 = bool(s7E and not p7)
            isExit7 = bool(s7X and p7)

    v1 = "NEW" if isNew1 else "EXIT" if isExit1 else "HOLD" if long1 else "FLAT"
    v2 = "NEW" if isNew2 else "EXIT" if isExit2 else "HOLD" if long2 else "FLAT"
    v3 = "NEW" if isNew3 else "EXIT" if isExit3 else "HOLD" if long3 else "FLAT"
    v4 = "NEW" if isNew4 else "EXIT" if isExit4 else "HOLD" if long4 else "FLAT"
    v5 = "NEW" if isNew5 else "EXIT" if isExit5 else "HOLD" if long5 else "FLAT"
    v6 = "NEW LONG" if isNew6 else "EXIT" if isExit6 else "HOLD" if long6 else "FLAT"
    v7 = "SELL USDT" if isNew7 else "DONE" if isExit7 else "USDT" if long7 else "FLAT"

    new_entries = sum([isNew1, isNew2, isNew3, isNew4, isNew5, isNew6])
    exits = sum([isExit1, isExit2, isExit3, isExit4, isExit5, isExit6])
    trend_entries = sum([isNew1, isNew2, isNew3])
    gartley_buy = 1 if isNew6 else 0
    gartley_sell = 1 if isNew7 else 0

    verdict = "NO TRADE"
    if new_entries == 0 and (long1 or long2 or long3 or long4 or long5 or long6):
        verdict = "HOLD"
    if gartley_sell >= 1 and (long1 or long2 or long3 or long6):
        verdict = "GARTLEY SELL TO USDT"
    elif gartley_buy >= 1 and new_entries >= 2:
        verdict = "CONFLUENCE + GARTLEY BUY"
    elif gartley_buy >= 1:
        verdict = "GARTLEY BUY"
    elif exits >= 2:
        verdict = "EXIT PRESSURE"
    elif exits >= 1 and new_entries >= 1:
        verdict = "CONFLICT"
    elif exits == 1 and new_entries == 0:
        verdict = "EXIT WARNING"
    elif new_entries >= 2 and trend_entries >= 1:
        verdict = "CONFLUENCE BUY"
    elif new_entries >= 1:
        verdict = "ENTRY WATCH"

    return GartleyTimeframeResult(
        timeframe=tf.upper(),
        close=float(close[-1]),
        verdict=verdict,
        v1_breakout=v1,
        v2_sma200=v2,
        sma200_val=float(sma200[-1]) if not np.isnan(sma200[-1]) else 0.0,
        v3_ema=v3,
        ema20_val=float(ema20[-1]),
        ema50_val=float(ema50[-1]),
        v4_rsi=v4,
        rsi_val=float(rsi[-1]) if not np.isnan(rsi[-1]) else 50.0,
        v5_bb=v5,
        v6_gartley_bull=v6,
        v7_gartley_bear=v7,
        bull_d=float(bullD) if bullD is not None else None,
        bear_d=float(bearD) if bearD is not None else None,
        bull_ratios=bull_ratios,
        bear_ratios=bear_ratios,
        is_new1=isNew1,
        is_new2=isNew2,
        is_new3=isNew3,
        is_new4=isNew4,
        is_new5=isNew5,
        is_new6=isNew6,
        is_new7=isNew7,
        is_exit1=isExit1,
        is_exit2=isExit2,
        is_exit3=isExit3,
        is_exit4=isExit4,
        is_exit5=isExit5,
        is_exit6=isExit6,
        is_exit7=isExit7,
    )


class GartleyEngine:
    """Evaluates Special Tab [S3]: Gartley 222 & 5-Strategy Confluence Radar."""

    def __init__(self, config: EngineConfig) -> None:
        self.config = config

    def evaluate(self, store: StateStore) -> Optional[Gartley5StrategyEvaluation]:
        """Calculates 1D Daily Trend & 4H Tactical Swing confluence and updates StateStore."""
        # 1. 1D Daily Series
        bars_1d: Sequence[KlineBar] = list(store.spot_klines_1d)
        if len(bars_1d) < 20:
            return None

        # 2. 4H Tactical Series
        # Prefer dedicated spot_klines_4h; fallback to synthesizing from spot_klines_1h
        if len(store.spot_klines_4h) >= 20:
            bars_4h: Sequence[KlineBar] = list(store.spot_klines_4h)
        elif len(store.spot_klines_1h) >= 20:
            bars_4h = synthesize_4h_bars(list(store.spot_klines_1h))
        else:
            bars_4h = bars_1d  # Offline fallback

        res_1d = compute_quant_horizon(bars_1d, tf="1d")
        res_4h = compute_quant_horizon(bars_4h, tf="4h")

        if res_1d is None or res_4h is None:
            return None

        close_price = store.binance_spot_price or res_4h.close
        v_1d = res_1d.verdict
        v_4h = res_4h.verdict

        # Combined multi-timeframe verdict synthesis
        if v_1d == "HOLD" and v_4h in ("GARTLEY BUY", "CONFLUENCE BUY", "CONFLUENCE + GARTLEY BUY"):
            combo_verdict = f"🔥 CONFLUENCE BUY ({v_4h})"
        elif v_4h == "GARTLEY SELL TO USDT":
            combo_verdict = "⚠️ GARTLEY SELL TO USDT"
        elif v_1d == "HOLD" and v_4h == "HOLD":
            combo_verdict = "💎 FULL HOLD (1D Trend + 4H Swing)"
        elif v_1d == "HOLD":
            combo_verdict = "HOLD (1D Trend Strong, 4H Waiting for Trigger)"
        else:
            combo_verdict = f"1D: {v_1d} | 4H: {v_4h}"

        # Plain English summary
        if "FULL HOLD" in combo_verdict:
            summary = (
                f"Both 1D Macro Trend and 4H Tactical Swing are in confirmed HOLD status above the 200 SMA (${res_1d.sma200_val:,.0f}). "
                "Maintain existing spot swing allocations. No new risk deployment required."
            )
        elif "CONFLUENCE BUY" in combo_verdict:
            summary = (
                f"1D Macro Trend confirms structural strength while 4H Tactical Swing triggered a valid buy entry ({v_4h}). "
                "Spot swing accumulation is favored."
            )
        elif "GARTLEY SELL" in combo_verdict:
            summary = (
                "Bearish Gartley 222 harmonic or multi-strategy exit pressure triggered on 4H horizon. "
                "Rotate swing capital into USDT to protect principal."
            )
        elif v_1d == "HOLD":
            summary = (
                f"1D Macro Trend remains bullish/HOLD (Spot > SMA200 ${res_1d.sma200_val:,.0f}), "
                f"while 4H Tactical Swing is currently waiting for a fresh confluence trigger ({v_4h}). Maintain core spot position."
            )
        else:
            summary = (
                f"Multi-timeframe state is mixed (1D: {v_1d}, 4H: {v_4h}). "
                "Observe support levels and wait for alignment."
            )

        evaluation = Gartley5StrategyEvaluation(
            timestamp_utc=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            close_price=round(close_price, 2),
            overall_verdict=combo_verdict,
            res_1d=res_1d,
            res_4h=res_4h,
            plain_english_summary=summary,
        )

        store.gartley_evaluation = evaluation
        return evaluation
