"""Unit tests for BTC Classic Chart Pattern & Candlestick Geometry Engine."""

import os
import pathlib
import unittest
from datetime import datetime, timezone
from typing import List

from analytics.pattern_detector import (
    PatternEngine,
    analyze_structure,
    detect_double_bottom,
    detect_double_top,
    detect_head_shoulders,
    detect_inverse_hs,
    detect_swings,
    detect_triangle,
    detect_wedge,
    export_chart_html,
    klines_to_ohlcv_list,
    render_candlestick_ascii,
    scan_patterns,
)
from config.settings import EngineConfig
from core.models import KlineBar, PatternCandidate, PatternEvaluation
from core.state_store import StateStore


class TestPatternDetector(unittest.TestCase):
    def setUp(self) -> None:
        self.config = EngineConfig()
        self.store = StateStore()

    def _make_dummy_klines(self, n: int = 50, base_price: float = 60000.0) -> List[KlineBar]:
        bars = []
        base_ms = 1700000000000
        for i in range(n):
            px = base_price + (i % 5) * 50.0
            bars.append(
                KlineBar(
                    timestamp_ms=base_ms + i * 3600_000,
                    open=px,
                    high=px + 100.0,
                    low=px - 100.0,
                    close=px + 20.0,
                    volume=100.0,
                    taker_buy_volume=50.0,
                )
            )
        return bars

    def test_klines_to_ohlcv_list(self) -> None:
        bars = self._make_dummy_klines(5)
        ohlcv = klines_to_ohlcv_list(bars)
        self.assertEqual(len(ohlcv), 5)
        self.assertEqual(len(ohlcv[0]), 6)
        self.assertEqual(ohlcv[0][1], bars[0].open)
        self.assertEqual(ohlcv[0][4], bars[0].close)

    def test_detect_swings(self) -> None:
        # Create an artificial sequence with clear peak and trough
        ohlcv = []
        prices = [100, 102, 105, 110, 115, 120, 115, 110, 105, 100, 95, 90, 85, 90, 95, 100, 105]
        for idx, p in enumerate(prices):
            ohlcv.append([1700000000000 + idx * 3600000, p, p + 5, p - 5, p, 10.0])

        swings = detect_swings(ohlcv, left=3, right=3)
        self.assertTrue(len(swings) >= 2)
        types = [s["type"] for s in swings]
        self.assertIn("high", types)
        self.assertIn("low", types)

    def test_detect_double_bottom(self) -> None:
        # Artificially construct swings for a Double Bottom
        swings = [
            {"type": "low", "price": 60000.0, "index": 5, "time": 1000},
            {"type": "high", "price": 63000.0, "index": 15, "time": 2000},
            {"type": "low", "price": 60100.0, "index": 25, "time": 3000},
        ]
        result = detect_double_bottom(swings)
        self.assertIsNotNone(result)
        self.assertEqual(result["pattern"], "Double Bottom")
        self.assertEqual(result["bias"], "Bullish")
        self.assertAlmostEqual(result["neckline"], 63000.0)
        self.assertTrue(result["confidence"] >= 0.70)

    def test_detect_double_top(self) -> None:
        # Artificially construct swings for a Double Top
        swings = [
            {"type": "high", "price": 70000.0, "index": 5, "time": 1000},
            {"type": "low", "price": 66000.0, "index": 15, "time": 2000},
            {"type": "high", "price": 69900.0, "index": 25, "time": 3000},
        ]
        result = detect_double_top(swings)
        self.assertIsNotNone(result)
        self.assertEqual(result["pattern"], "Double Top")
        self.assertEqual(result["bias"], "Bearish")
        self.assertAlmostEqual(result["neckline"], 66000.0)
        self.assertTrue(result["confidence"] >= 0.70)

    def test_detect_head_shoulders(self) -> None:
        swings = [
            {"type": "high", "price": 65000.0, "index": 5, "time": 1000},
            {"type": "low", "price": 63000.0, "index": 10, "time": 1500},
            {"type": "high", "price": 68000.0, "index": 16, "time": 2000},
            {"type": "low", "price": 63100.0, "index": 21, "time": 2500},
            {"type": "high", "price": 65100.0, "index": 27, "time": 3000},
        ]
        result = detect_head_shoulders(swings)
        self.assertIsNotNone(result)
        self.assertEqual(result["pattern"], "Head and Shoulders")
        self.assertEqual(result["bias"], "Bearish")
        self.assertAlmostEqual(result["neckline"], 63000.0)

    def test_detect_inverse_hs(self) -> None:
        swings = [
            {"type": "low", "price": 65000.0, "index": 5, "time": 1000},
            {"type": "high", "price": 67000.0, "index": 10, "time": 1500},
            {"type": "low", "price": 62000.0, "index": 16, "time": 2000},
            {"type": "high", "price": 67100.0, "index": 21, "time": 2500},
            {"type": "low", "price": 64900.0, "index": 27, "time": 3000},
        ]
        result = detect_inverse_hs(swings)
        self.assertIsNotNone(result)
        self.assertEqual(result["pattern"], "Inverse Head and Shoulders")
        self.assertEqual(result["bias"], "Bullish")
        self.assertAlmostEqual(result["neckline"], 67100.0)

    def test_detect_wedge(self) -> None:
        # Falling Wedge: both slopes dropping, highs dropping faster
        swings = [
            {"type": "high", "price": 70000.0, "index": 2, "time": 1000},
            {"type": "low", "price": 65000.0, "index": 4, "time": 1500},
            {"type": "high", "price": 68000.0, "index": 6, "time": 2000},
            {"type": "low", "price": 64000.0, "index": 8, "time": 2500},
            {"type": "high", "price": 65500.0, "index": 10, "time": 3000},
            {"type": "low", "price": 63200.0, "index": 12, "time": 3500},
        ]
        result = detect_wedge(swings)
        self.assertIsNotNone(result)
        self.assertIn("Wedge", result["pattern"])

    def test_detect_triangle(self) -> None:
        # Symmetrical triangle: highs dropping, lows rising
        swings = [
            {"type": "high", "price": 70000.0, "index": 2, "time": 1000},
            {"type": "low", "price": 60000.0, "index": 4, "time": 1500},
            {"type": "high", "price": 68000.0, "index": 6, "time": 2000},
            {"type": "low", "price": 62000.0, "index": 8, "time": 2500},
            {"type": "high", "price": 66000.0, "index": 10, "time": 3000},
            {"type": "low", "price": 64000.0, "index": 12, "time": 3500},
        ]
        result = detect_triangle(swings)
        self.assertIsNotNone(result)
        self.assertIn("Triangle", result["pattern"])

    def test_pattern_engine_evaluate(self) -> None:
        engine = PatternEngine(self.config)
        bars_1h = self._make_dummy_klines(40, base_price=65000.0)
        bars_4h = self._make_dummy_klines(30, base_price=65000.0)

        for b in bars_1h:
            self.store.spot_klines_1h.append(b)
        for b in bars_4h:
            self.store.spot_klines_4h.append(b)

        self.store.binance_spot_price = 65200.0

        ev = engine.evaluate(self.store)
        self.assertIsNotNone(ev)
        self.assertEqual(ev.spot_price, 65200.0)
        self.assertTrue(hasattr(self.store, "pattern_evaluation"))
        self.assertIsNotNone(self.store.pattern_evaluation)
        self.assertTrue(len(ev.tactical_playbook) > 0)

        # Check chart.html export
        chart_path = pathlib.Path(ev.html_chart_path)
        self.assertTrue(chart_path.exists())
        content = chart_path.read_text(encoding="utf-8")
        self.assertIn("lightweight-charts", content)
        self.assertIn("BTC Swing Engine", content)

    def test_render_candlestick_ascii(self) -> None:
        bars = self._make_dummy_klines(30, base_price=65000.0)
        ohlcv = klines_to_ohlcv_list(bars)
        swings = detect_swings(ohlcv, left=3, right=3)
        top_p = PatternCandidate(
            pattern="Double Bottom",
            bias="Bullish",
            confidence=0.85,
            neckline=66000.0,
            floor_or_roof=64500.0,
        )
        panel = render_candlestick_ascii(ohlcv, swings, top_p, width=100, height=10)
        self.assertIsNotNone(panel)


if __name__ == "__main__":
    unittest.main()
