"""Unit tests for Tab [M] BTC Magnet Liquidation Gravity Deck & Mechanics-First Edge Detector."""

import unittest
from datetime import datetime, timezone
from typing import List

from analytics.ai_packet_exporter import build_ai_telemetry_packet
from analytics.btc_magnet_engine import BTCMagnetEngine, copy_btc_magnet_card_to_clipboard
from config.settings import DEFAULT_CONFIG
from core.models import BTCMagnetLevel, KlineBar
from core.state_store import StateStore
from ui.terminal_hud import build_dashboard_renderable


def _create_synthetic_bars(count: int = 48, base_price: float = 75_000.0) -> List[KlineBar]:
    end_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    bars: List[KlineBar] = []
    step_ms = 60 * 60 * 1000  # 1 hour
    start_ms = end_ms - (count * step_ms)

    for i in range(count):
        ts = start_ms + i * step_ms
        p = base_price + (i * 15.0)
        vol = 800.0 + (i % 5) * 50.0
        bars.append(
            KlineBar(
                timestamp_ms=ts,
                open=p - 10.0,
                high=p + 80.0,
                low=p - 80.0,
                close=p + 10.0,
                volume=vol,
                taker_buy_volume=vol * 0.52,
            )
        )
    return bars


class TestBTCMagnetEngine(unittest.TestCase):
    """Verifies BTC Magnet rules engine, locked status templates, TUI rendering, and clipboard export."""

    def setUp(self) -> None:
        self.config = DEFAULT_CONFIG
        self.engine = BTCMagnetEngine(self.config)
        self.store = StateStore()
        self.store.binance_spot_price = 76_000.0
        self.store.funding_rate_pct = 0.0055  # ~6.0% annual
        self.store.high_24h = 76_800.0
        self.store.low_24h = 75_200.0

        for b in _create_synthetic_bars(count=48, base_price=75_000.0):
            self.store.spot_klines_1h.append(b)

    def test_evaluate_populates_state_store(self) -> None:
        """Verify evaluation populates store.btc_magnet_evaluation with complete telemetry."""
        res = self.engine.evaluate(self.store)

        self.assertIsNotNone(res)
        self.assertIsNotNone(self.store.btc_magnet_evaluation)
        self.assertEqual(res.spot_price, 76_000.0)
        self.assertGreater(res.upper_magnet.price, res.spot_price)
        self.assertLess(res.lower_magnet.price, res.spot_price)
        self.assertGreater(res.upper_magnet.usd_volume, 0)
        self.assertGreater(res.lower_magnet.usd_volume, 0)
        self.assertIn(res.pull_direction, ("UPPER", "LOWER", "NEUTRAL"))
        self.assertIn(res.verdict, ("WAIT", "SPEAK"))
        self.assertEqual(len(res.rule_checks), 7)
        self.assertIn("BTC MAGNET", res.magnet_summary_markdown)
        self.assertIn("7 INTERNAL SPEAKING RULES AUDIT", res.magnet_summary_markdown)

    def test_speaking_rules_locked_templates(self) -> None:
        """Verify locked text templates from docs/status-templates.md."""
        res = self.engine.evaluate(self.store)

        if res.verdict == "SPEAK":
            self.assertTrue(
                res.headline.startswith("Strong magnet")
                or res.headline.startswith("Magnet at")
            )
            self.assertTrue("Watch for sweep" in res.body or "Edge present" in res.body)
        else:
            self.assertEqual(res.headline, "No clear edge — wait.")
            self.assertIn("wait", res.body.lower())
            self.assertIn("spends most days correctly saying 'wait'", res.rule_subtitle)

    def test_tab17_tui_render(self) -> None:
        """Verify Desk 17 renders cleanly without errors in the terminal HUD."""
        self.engine.evaluate(self.store)

        renderable = build_dashboard_renderable(self.config, self.store, tab_override=17)
        self.assertIsNotNone(renderable)

    def test_copy_magnet_card_to_clipboard(self) -> None:
        """Verify clipboard helper extracts Magnet Card brief without error."""
        self.engine.evaluate(self.store)

        ok, msg, char_count = copy_btc_magnet_card_to_clipboard(self.store)
        self.assertGreater(char_count, 100)
        self.assertIn("chars", msg)

    def test_ai_telemetry_packet_incorporates_section_17(self) -> None:
        """Verify master AI telemetry packet (Key C) incorporates Section 17."""
        self.engine.evaluate(self.store)

        packet = build_ai_telemetry_packet(self.config, self.store)
        self.assertIn("## SECTION 17: TAB [M] BTC MAGNET", packet)
        self.assertIn("### 17A. Liquidation Gravitational Horizon", packet)
        self.assertIn("### 17B. 7 Internal Speaking Rules Audit", packet)


if __name__ == "__main__":
    unittest.main()
