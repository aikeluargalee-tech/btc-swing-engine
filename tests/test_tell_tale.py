"""Unit tests for Tell-Tale Candle & Volume Capitulation Climax Sensor."""

import unittest
from datetime import datetime, timezone
from typing import List

from analytics.tell_tale_engine import TellTaleEngine
from config.settings import DEFAULT_CONFIG
from core.models import KlineBar


def _create_synthetic_bars(
    num_bars: int = 25,
    last_volume_multiplier: float = 1.0,
    is_red: bool = True,
    body_range_ratio: float = 0.50,
) -> List[KlineBar]:
    """Generates synthetic closed bars for Tell-Tale evaluation."""
    bars: List[KlineBar] = []
    base_ts = 1_720_000_000_000
    base_price = 80_000.0

    for i in range(num_bars):
        ts = base_ts + i * 900 * 1000  # 15m intervals
        is_last = (i == num_bars - 1)
        vol = 100.0 if not is_last else (100.0 * last_volume_multiplier)

        # Baseline: normal movement
        if not is_last:
            o = base_price + i * 10.0
            c = o + 5.0
            h = c + 10.0
            l = o - 10.0
        else:
            # Custom candle shape
            o = base_price + i * 10.0
            rng = 500.0
            body = rng * body_range_ratio
            if is_red:
                c = o - body
                h = o + (rng - body) * 0.5
                l = c - (rng - body) * 0.5
            else:
                c = o + body
                h = c + (rng - body) * 0.5
                l = o - (rng - body) * 0.5

        bars.append(
            KlineBar(
                timestamp_ms=ts,
                open=o,
                high=h,
                low=l,
                close=c,
                volume=vol,
                taker_buy_volume=vol * 0.5,
            )
        )
    return bars


class TestTellTaleEngine(unittest.TestCase):
    """Verifies Tell-Tale volume baseline, relative volume thresholds, and climax flags."""

    def setUp(self) -> None:
        self.engine = TellTaleEngine(DEFAULT_CONFIG)

    def test_normal_order_flow_no_climax(self) -> None:
        """When volume is normal (e.g. 1.2x baseline), flags NORMAL ORDER FLOW."""
        bars = _create_synthetic_bars(25, last_volume_multiplier=1.2, is_red=True, body_range_ratio=0.70)
        ev = self.engine.evaluate(bars)
        self.assertFalse(ev.disruption_detected)
        self.assertFalse(ev.is_selling_climax)
        self.assertFalse(ev.is_buying_climax)
        self.assertEqual(ev.climax_type, "NONE")
        self.assertIn("NORMAL", ev.plain_status)

    def test_selling_climax_detected_at_5x_volume(self) -> None:
        """When red candle has 6x volume and 0.80 body/range, flags SELLING CLIMAX."""
        bars = _create_synthetic_bars(25, last_volume_multiplier=6.0, is_red=True, body_range_ratio=0.80)
        ev = self.engine.evaluate(bars)
        self.assertTrue(ev.disruption_detected)
        self.assertTrue(ev.is_selling_climax)
        self.assertFalse(ev.is_buying_climax)
        self.assertEqual(ev.climax_type, "SELLING_CLIMAX")
        self.assertIn("SELLING CLIMAX", ev.plain_status)
        self.assertGreaterEqual(ev.bar_15m.relvol, 5.0)
        self.assertGreaterEqual(ev.bar_15m.body_range, 0.65)

    def test_buying_climax_detected_at_5x_volume(self) -> None:
        """When green candle has 5.5x volume and 0.75 body/range, flags BUYING CLIMAX."""
        bars = _create_synthetic_bars(25, last_volume_multiplier=5.5, is_red=False, body_range_ratio=0.75)
        ev = self.engine.evaluate(bars)
        self.assertTrue(ev.disruption_detected)
        self.assertFalse(ev.is_selling_climax)
        self.assertTrue(ev.is_buying_climax)
        self.assertEqual(ev.climax_type, "BUYING_CLIMAX")
        self.assertIn("BUYING CLIMAX", ev.plain_status)

    def test_high_volume_wicky_candle_not_climax(self) -> None:
        """High volume but wicky body (body/range < 0.65) is absorbed churn, not directional climax."""
        bars = _create_synthetic_bars(25, last_volume_multiplier=7.0, is_red=True, body_range_ratio=0.30)
        ev = self.engine.evaluate(bars)
        self.assertFalse(ev.disruption_detected)
        self.assertFalse(ev.is_selling_climax)

    def test_insufficient_bars_handled_gracefully(self) -> None:
        """When fewer than 21 bars available, returns safe fallback."""
        bars = _create_synthetic_bars(10)
        ev = self.engine.evaluate(bars)
        self.assertFalse(ev.disruption_detected)
        self.assertIn("INSUFFICIENT", ev.plain_status)


if __name__ == "__main__":
    unittest.main()
