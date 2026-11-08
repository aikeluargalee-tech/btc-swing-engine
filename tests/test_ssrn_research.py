"""Unit tests for Tab [R] SSRN Quantitative Alpha Deck & Academic Research Engine."""

import unittest
from datetime import datetime, timezone
from typing import List
import numpy as np

from analytics.ssrn_research_engine import (
    SSRNResearchEngine,
    copy_ssrn_deck_to_clipboard,
    _compute_macd,
    _compute_atr,
)
from config.settings import DEFAULT_CONFIG
from core.models import KlineBar
from core.state_store import StateStore
from ui.terminal_hud import build_dashboard_renderable


def _create_synthetic_bars(
    count: int = 48,
    base_price: float = 67_000.0,
    step_minutes: int = 60,
    end_dt: datetime = None,
) -> List[KlineBar]:
    if end_dt is None:
        end_dt = datetime.now(timezone.utc)
    end_ms = int(end_dt.timestamp() * 1000)
    bars: List[KlineBar] = []
    step_ms = step_minutes * 60_000
    start_ms = end_ms - (count * step_ms)

    for i in range(count):
        ts = start_ms + i * step_ms
        swing = 150.0 * np.sin(i * 0.3)
        price = base_price + (i * 20.0) + swing
        high = price + 100.0 + (i % 5) * 10.0
        low = price - 100.0 - (i % 7) * 8.0
        vol = 500.0 + (i % 10) * 40.0
        bars.append(
            KlineBar(
                timestamp_ms=ts,
                open=price - 15.0,
                high=high,
                low=low,
                close=price + 15.0,
                volume=vol,
                taker_buy_volume=vol * 0.51,
            )
        )
    return bars


class TestSSRNResearchEngine(unittest.TestCase):
    """Verifies SSRN empirical registry loading, math indicators, and Tab [R] TUI rendering."""

    def setUp(self) -> None:
        self.config = DEFAULT_CONFIG
        self.engine = SSRNResearchEngine(self.config)
        self.store = StateStore()

    def test_registry_loading(self) -> None:
        """Verify registry contains 5 academic domains and 5 empirical strategy models."""
        reg = self.engine._load_registry()
        self.assertIn("domains", reg)
        self.assertIn("models", reg)
        self.assertEqual(len(reg["domains"]), 5)
        self.assertEqual(len(reg["models"]), 5)

        domain_ids = [d["id"] for d in reg["domains"]]
        self.assertIn("microstructure", domain_ids)
        self.assertIn("momentum", domain_ids)
        self.assertIn("factors", domain_ids)
        self.assertIn("onchain", domain_ids)
        self.assertIn("ml_sentiment", domain_ids)

        model_ids = [m["id"] for m in reg["models"]]
        self.assertIn("mtf_macd", model_ids)
        self.assertIn("ensemble_donchian", model_ids)
        self.assertIn("vol_adaptive_8h", model_ids)
        self.assertIn("funding_carry_filter", model_ids)
        self.assertIn("cost_aware_ml", model_ids)

    def test_math_helpers(self) -> None:
        """Verify MACD and ATR calculations."""
        prices = [100.0 + i * 2.0 for i in range(40)]
        macd, sig, hist = _compute_macd(prices)
        self.assertIsInstance(macd, float)
        self.assertIsInstance(sig, float)
        self.assertIsInstance(hist, float)

        highs = [p + 5.0 for p in prices]
        lows = [p - 5.0 for p in prices]
        atr = _compute_atr(highs, lows, prices, period=14)
        self.assertGreater(atr, 0.0)

    def test_evaluate_populates_state_store(self) -> None:
        """Verify evaluation pipeline enriches state store with live SSRN metrics."""
        self.store.binance_spot_price = 76_000.0
        self.store.funding_rate_pct = 0.0057  # ~6.2% annual

        bars_1d = _create_synthetic_bars(count=60, base_price=70_000.0, step_minutes=1440)
        for b in bars_1d:
            self.store.spot_klines_1d.append(b)

        bars_4h = _create_synthetic_bars(count=60, base_price=74_000.0, step_minutes=240)
        for b in bars_4h:
            self.store.spot_klines_4h.append(b)

        bars_1h = _create_synthetic_bars(count=72, base_price=75_000.0, step_minutes=60)
        for b in bars_1h:
            self.store.spot_klines_1h.append(b)

        res = self.engine.evaluate(self.store)

        self.assertIsNotNone(res)
        self.assertIsNotNone(self.store.ssrn_alpha_evaluation)
        self.assertEqual(len(res.domains), 5)
        self.assertEqual(len(res.models), 5)
        self.assertGreater(res.realized_vol_20d_ann, 0.0)
        self.assertGreater(res.target_vol_sizing_pct, 0.0)
        self.assertGreater(res.atr_14_8h, 0.0)
        self.assertGreater(res.atr_trailing_stop_dist, 0.0)
        self.assertIn("PASS", res.funding_gate_status)
        self.assertEqual(res.active_view_mode, "models")
        self.assertGreater(len(res.domains[0].live_metric_val), 0)
        self.assertGreater(len(res.domains[0].live_submetrics), 0)
        self.assertGreater(len(res.ssrn_summary_markdown), 200)
        self.assertIn("SSRN QUANTITATIVE ALPHA DECK", res.ssrn_summary_markdown)
        self.assertIn("Zarattini", res.ssrn_summary_markdown)

    def test_tab16_tui_render_both_views(self) -> None:
        """Verify Tab 16 builds cleanly for both View A (domains) and View B (models)."""
        self.store.binance_spot_price = 76_000.0
        bars_1h = _create_synthetic_bars(count=48, base_price=75_000.0, step_minutes=60)
        for b in bars_1h:
            self.store.spot_klines_1h.append(b)

        self.engine.evaluate(self.store)

        # View A: domains
        self.store.ssrn_view_mode = "domains"
        renderable_a = build_dashboard_renderable(self.config, self.store, tab_override=16)
        self.assertIsNotNone(renderable_a)

        # View B: models
        self.store.ssrn_view_mode = "models"
        renderable_b = build_dashboard_renderable(self.config, self.store, tab_override=16)
        self.assertIsNotNone(renderable_b)

    def test_copy_ssrn_deck_to_clipboard(self) -> None:
        """Verify clipboard helper extracts brief without error."""
        self.store.binance_spot_price = 76_000.0
        self.engine.evaluate(self.store)

        copied_ok, msg, char_count = copy_ssrn_deck_to_clipboard(self.store)
        self.assertIsInstance(msg, str)
        self.assertGreater(char_count, 100)
        self.assertIn("chars", msg)

    def test_ai_telemetry_packet_incorporates_tab_g_and_tab_r(self) -> None:
        """Verify master AI telemetry packet (Key C) incorporates Sections 15 & 16."""
        from analytics.ai_packet_exporter import build_ai_telemetry_packet

        self.store.binance_spot_price = 76_000.0
        packet = build_ai_telemetry_packet(self.config, self.store)

        self.assertIn("## SECTION 15: TAB [G]", packet)
        self.assertIn("## SECTION 16: TAB [R]", packet)
        self.assertIn("Mesíček", packet)
        self.assertIn("Zarattini", packet)
        self.assertIn("Anchored VWAP", packet)


if __name__ == "__main__":
    unittest.main()
