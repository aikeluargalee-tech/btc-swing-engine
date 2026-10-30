"""Unit tests for the Industrial 3-EMA Strategy Engine (Daily/4H), ADX, and Tab 1 Gate Confluence."""

import unittest
from datetime import datetime, timezone
from typing import List

from config.settings import EngineConfig
from core.models import (
    DerivativesSnapshot,
    FlowSnapshot,
    KlineBar,
    OIPositioningQuadrant,
)
from core.state_store import StateStore
from analytics.ema_strategy_engine import (
    EMAStrategyEngine,
    compute_adx,
    compute_ema_series,
)
from analytics.signal_detector import SignalDetector


def make_mock_kline(
    timestamp_ms: int,
    open_: float,
    high: float,
    low: float,
    close: float,
    volume: float = 1000.0,
    taker_buy_volume: float = 500.0,
) -> KlineBar:
    return KlineBar(
        timestamp_ms=timestamp_ms,
        open=open_,
        high=high,
        low=low,
        close=close,
        volume=volume,
        taker_buy_volume=taker_buy_volume,
    )


class TestEMAStrategyEngine(unittest.TestCase):
    def setUp(self) -> None:
        self.config = EngineConfig()
        self.engine = EMAStrategyEngine(self.config)
        self.store = StateStore()

    def test_ema_series_calculation(self) -> None:
        """Verifies EMA calculation seeds with SMA and applies multiplier correctly."""
        prices = [10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0]
        ema_3 = compute_ema_series(prices, 3)
        # SMA of first 3 is (10+11+12)/3 = 11.0
        self.assertAlmostEqual(ema_3[2], 11.0, places=4)
        # 4th bar: multiplier = 2/(3+1) = 0.5; ema = (13 - 11)*0.5 + 11 = 12.0
        self.assertAlmostEqual(ema_3[3], 12.0, places=4)
        # 5th bar: ema = (14 - 12)*0.5 + 12 = 13.0
        self.assertAlmostEqual(ema_3[4], 13.0, places=4)

    def test_adx_calculation(self) -> None:
        """Verifies Wilder's ADX returns a positive value reflecting trend strength."""
        highs = [100.0 + i * 2.0 for i in range(50)]
        lows = [95.0 + i * 2.0 for i in range(50)]
        closes = [98.0 + i * 2.0 for i in range(50)]
        adx = compute_adx(highs, lows, closes, period=14)
        # In a persistent steep upward trend, ADX should be strong (>= 25)
        self.assertGreater(adx, 25.0)

    def test_daily_regime_classification_strong_bull(self) -> None:
        """Verifies Strong Bull classification when Price > rising 200 EMA and 20 > 50 > 200."""
        # 250 daily bars sloping upward
        base_price = 50000.0
        daily_bars = []
        for i in range(250):
            p = base_price + i * 150.0
            daily_bars.append(make_mock_kline(i * 86400000, p - 50, p + 100, p - 100, p))

        # 4H bars
        bars_4h = []
        for i in range(100):
            p = daily_bars[-1].close - 500.0 + i * 10.0
            bars_4h.append(make_mock_kline(i * 14400000, p - 20, p + 50, p - 50, p))

        flow = FlowSnapshot()
        deriv = DerivativesSnapshot()

        snap = self.engine.evaluate(
            store=self.store,
            spot_1d=daily_bars,
            bars_4h=bars_4h,
            current_price=daily_bars[-1].close,
            flow=flow,
            deriv=deriv,
            atr_4h=600.0,
        )

        self.assertEqual(snap.daily_regime, "STRONG_BULL")
        self.assertGreater(snap.daily_ema_20, snap.daily_ema_50)
        self.assertGreater(snap.daily_ema_50, snap.daily_ema_200)
        self.assertGreater(snap.daily_ema_200_slope, 0.0)
        self.assertEqual(snap.suggested_risk_pct, 0.75)

    def test_pullback_and_positioning_confirmation(self) -> None:
        """Verifies pullback into 4H 50-EMA zone with 2-of-3 positioning confirmation."""
        daily_bars = []
        for i in range(250):
            p = 60000.0 + i * 100.0
            daily_bars.append(make_mock_kline(i * 86400000, p, p + 100, p - 100, p))

        bars_4h = []
        for i in range(100):
            p = 80000.0 + (i * 20.0)
            bars_4h.append(make_mock_kline(i * 14400000, p, p + 50, p - 50, p))

        # Test price pulled back to 50 EMA
        ema_4h_50 = compute_ema_series([b.close for b in bars_4h], 50)[-1]
        current_price = ema_4h_50 - 100.0

        flow = FlowSnapshot()
        flow.w_1h.spot_zscore = 0.8  # Condition 3 met (Spot CVD positive)
        deriv = DerivativesSnapshot()
        deriv.funding_rate_pct = 0.0050  # Condition 2 met (Funding <= 0.010%)
        deriv.oi_change_1h_pct = 0.10  # Condition 1 met (OI stable <= 0.25%)

        snap = self.engine.evaluate(
            store=self.store,
            spot_1d=daily_bars,
            bars_4h=bars_4h,
            current_price=current_price,
            flow=flow,
            deriv=deriv,
            atr_4h=500.0,
        )

        self.assertTrue(snap.pullback_zone_active)
        self.assertEqual(snap.positioning_confirmations_met, 3)
        self.assertTrue(snap.positioning_pass)

    def test_full_signal_detector_integration(self) -> None:
        """Verifies SignalDetector populates store.ema_strategy and SignalEvaluation.ema_strategy."""
        detector = SignalDetector(self.config)

        # Populate store with bars
        spot_1h = []
        for i in range(720):
            p = 80000.0 + (i % 20) * 10.0
            spot_1h.append(make_mock_kline(i * 3600000, p, p + 20, p - 20, p, 100.0, 50.0))

        spot_1d = []
        for i in range(250):
            p = 75000.0 + i * 30.0
            spot_1d.append(make_mock_kline(i * 86400000, p, p + 100, p - 100, p, 1000.0, 500.0))

        self.store.spot_klines_1h = spot_1h
        self.store.spot_klines_15m = spot_1h[-40:]
        self.store.spot_klines_1d = spot_1d
        self.store.binance_spot_price = spot_1h[-1].close

        eval_res = detector.evaluate(self.store)

        self.assertIsNotNone(eval_res)
        self.assertIsNotNone(eval_res.ema_strategy)
        self.assertIsNotNone(self.store.ema_strategy)
        self.assertIn(eval_res.ema_strategy.daily_regime, ["STRONG_BULL", "WEAK_BULL", "NEUTRAL", "STRONG_BEAR", "WEAK_BEAR"])


if __name__ == "__main__":
    unittest.main()
