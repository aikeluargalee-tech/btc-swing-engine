"""Unit tests for Liquidation Reader and companion telemetry integration."""

import json
import tempfile
import time
import unittest
from pathlib import Path

from analytics.liquidation_reader import (
    read_latest_liquidation_report,
    reset_liquidation_cache,
)
from core.models import LiquidationDetectorReport


class TestLiquidationReader(unittest.TestCase):
    """Verifies reading, caching, and fallback behavior of the liquidation detector telemetry."""

    def setUp(self) -> None:
        reset_liquidation_cache()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.report_path = Path(self.temp_dir.name) / "latest_detector_report.json"

    def tearDown(self) -> None:
        self.temp_dir.cleanup()
        reset_liquidation_cache()

    def test_missing_report_file_returns_offline(self) -> None:
        """When report file does not exist, returns safe offline report without error."""
        non_existent = Path(self.temp_dir.name) / "does_not_exist.json"
        rep = read_latest_liquidation_report(non_existent)
        self.assertIsInstance(rep, LiquidationDetectorReport)
        self.assertFalse(rep.is_available)
        self.assertEqual(rep.verdict, "DETECTOR OFFLINE")

    def test_valid_report_file_parsing_and_caching(self) -> None:
        """When valid report file exists, parses all windows, Q-multiple, and post-flush structure."""
        now_ms = int(time.time() * 1000)
        sample_data = {
            "timestamp_utc": "2026-11-04 00:00:00 UTC",
            "timestamp_ms": now_ms,
            "symbol": "BTCUSDT",
            "verdict": "QUIET -- NO ANOMALY",
            "verdict_detail": "No cascade detected",
            "primary_classification": "NORMAL",
            "magnitude_tier": "NORMAL",
            "directional_classification": "LONG_LIQUIDATION_FLUSH",
            "liquidation_multiple_24h": 0.42,
            "windows": {
                "15m": {"long_usd": 100_000.0, "short_usd": 0.0, "total_usd": 100_000.0, "long_count": 5, "short_count": 0, "dominant_side": "LONG"},
                "1h": {"long_usd": 500_000.0, "short_usd": 50_000.0, "total_usd": 550_000.0, "long_count": 12, "short_count": 2, "dominant_side": "LONG"},
                "4h": {"long_usd": 2_000_000.0, "short_usd": 100_000.0, "total_usd": 2_100_000.0, "long_count": 40, "short_count": 5, "dominant_side": "LONG"},
                "24h": {"long_usd": 12_000_000.0, "short_usd": 500_000.0, "total_usd": 12_500_000.0, "long_count": 150, "short_count": 20, "dominant_side": "LONG"},
            },
            "post_flush_price_structure": {
                "status": "STABILISATION_DEVELOPING",
                "stabilisation_confirmed": False,
                "stopped_making_lower_lows": True,
                "higher_low_formed": True,
                "break_prior_structure_high": False,
                "spot_volume_expanded": True,
                "details": {"volume_ratio": 1.95},
            },
        }
        self.report_path.write_text(json.dumps(sample_data), encoding="utf-8")

        rep = read_latest_liquidation_report(self.report_path)
        self.assertTrue(rep.is_available)
        self.assertFalse(rep.is_stale)
        self.assertEqual(rep.verdict, "QUIET -- NO ANOMALY")
        self.assertAlmostEqual(rep.liquidation_multiple_24h, 0.42)
        self.assertEqual(rep.windows["24h"].total_usd, 12_500_000.0)
        self.assertIsNotNone(rep.post_flush_price_structure)
        self.assertTrue(rep.post_flush_price_structure.higher_low_formed)
        self.assertAlmostEqual(rep.post_flush_price_structure.volume_ratio, 1.95)

    def test_corrupted_json_handled_gracefully(self) -> None:
        """When report file contains invalid JSON (mid-write race condition), returns glitch report."""
        self.report_path.write_text("{\"unterminated_json: ", encoding="utf-8")
        rep = read_latest_liquidation_report(self.report_path)
        self.assertFalse(rep.is_available)
        self.assertEqual(rep.verdict, "FEED READ GLITCH")


if __name__ == "__main__":
    unittest.main()
