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
        # Seed deterministic liqmap cache so unit tests are fast and offline-safe
        self.engine._last_fetch_ts = 1e12
        self.engine._cached_liq_data = {
            "levels": {
                "above": [{"price": 78_422.0, "dist_pct": 3.19, "usd": 215_400_000}],
                "below": [{"price": 74_525.0, "dist_pct": -1.94, "usd": 354_300_000}],
            }
        }
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
        """Verify locked text templates from docs/status-templates.md for both SPEAK and WAIT."""
        res = self.engine.evaluate(self.store)
        self.assertEqual(res.verdict, "SPEAK")
        self.assertEqual(res.pull_direction, "LOWER")
        self.assertTrue(res.headline.startswith("Strong magnet below at $74,525."))
        self.assertIn("Watch for sweep.", res.body)

        # Now force WAIT condition (opposing trend / sharp move)
        self.store.high_24h = 82_000.0
        self.store.low_24h = 74_000.0
        self.store.price_change_24h_pct = 8.5  # Fails Rule 5 & Regime is TrendUp while magnet is below
        res_wait = self.engine.evaluate(self.store)
        self.assertEqual(res_wait.verdict, "WAIT")
        self.assertEqual(res_wait.headline, "No clear edge - wait.")
        self.assertIn("conditions incomplete. No clear edge - wait.", res_wait.body)
        self.assertIn("spends most days correctly saying 'wait.'", res_wait.rule_subtitle)

    def test_exhaustion_pattern_template(self) -> None:
        """Verify Pattern #4 (Exhaustion) triggers on dense magnet + extreme funding + declining OI."""
        self.store.funding_rate_pct = 0.04  # ~43.8% annual (> 28% limit)
        self.store.oi_delta_4h_pct = -1.8   # Declining OI (< -0.5% limit)
        res = self.engine.evaluate(self.store)

        self.assertEqual(res.verdict, "WAIT")
        self.assertIn("with extreme funding and declining OI.", res.headline)
        self.assertEqual(res.body, "Possible exhaustion. High caution - wait for confirmation.")

    def test_trend_aligned_pattern_template(self) -> None:
        """Verify Pattern #3 (Trend-aligned) triggers when regime is TrendUp and magnet is above."""
        self.engine._cached_liq_data = {
            "levels": {
                "above": [{"price": 78_200.0, "dist_pct": 2.89, "usd": 420_000_000}],
                "below": [{"price": 74_200.0, "dist_pct": -2.37, "usd": 150_000_000}],
            }
        }
        self.store.high_24h = 78_000.0
        self.store.low_24h = 73_500.0  # > 4.8% range spread
        self.store.price_change_24h_pct = 3.8  # TrendUp, < 6.5%
        res = self.engine.evaluate(self.store)

        self.assertEqual(res.verdict, "SPEAK")
        self.assertEqual(res.market_regime, "TrendUp")
        self.assertEqual(res.pull_direction, "UPPER")
        self.assertEqual(res.headline, "Magnet at $78,200 aligns with trend.")
        self.assertIn("Edge present - monitor for entry zone.", res.body)

    def test_small_funding_and_live_oi_history_accuracy(self) -> None:
        """Verify small 8h funding rates (e.g. 0.0005%) do not get multiplied by 100x and live OI history works."""
        self.store.funding_rate_pct = 0.0005  # 0.0005% per 8h -> +0.5475%/yr
        self.store.record_oi_sample(80_000.0, ts_sec=1000.0)
        self.store.record_oi_sample(78_400.0, ts_sec=15400.0)  # -2.0% over 4h
        self.store.derivatives_snapshot.oi_change_4h_pct = -2.0

        res = self.engine.evaluate(self.store)
        self.assertAlmostEqual(res.funding_rate_annual_pct, 0.5475, places=2)
        self.assertAlmostEqual(res.oi_delta_4h_pct, -2.0, places=2)
        self.assertFalse(res.rule_checks[1].passed)  # Rule 2 (OI) fails on -2.0%

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

    def test_5_regime_radar_majority_voting(self) -> None:
        """Verify 5-Regime Radar majority voting engine (>= 3 of 4 matches)."""
        res = self.engine.evaluate(self.store)
        self.assertIn(res.regime_id, (
            "SPOT_LED_EXPANSION",
            "LEVERAGED_FRAGILE_UPSIDE",
            "RANGE_LIQUIDATION_MAGNET",
            "CASCADE_FORCED_DELEVERAGING",
            "DISTRIBUTION_BEAR_CONTINUATION",
            "TRANSITION_MIXED",
        ))
        self.assertTrue(len(res.majority_score) > 0)
        self.assertGreaterEqual(res.majority_matches_count, 1)
        self.assertTrue(len(res.all_observations) >= 4)
        for obs_desc, obs_pass in res.all_observations:
            self.assertIsInstance(obs_desc, str)
            self.assertIsInstance(obs_pass, bool)

    def test_lsce_state_machine(self) -> None:
        """Verify Liquidation Sweep Confirmation Engine (LSCE) 4-state engine."""
        res = self.engine.evaluate(self.store)
        self.assertIn(res.lsce_status, (
            "UNTESTED",
            "SWEEP_IN_PROGRESS",
            "SWEEP_FAILED_BREAKDOWN",
            "SWEEP_AND_RECLAIM_CONFIRMED",
        ))
        self.assertGreater(res.lsce_reclaim_level, 0.0)
        self.assertIsNotNone(res.lsce_action_verdict)

    def test_dual_ladder_and_six_factors(self) -> None:
        """Verify immediate vs total ladder ratios and 6-factor decision hierarchy."""
        res = self.engine.evaluate(self.store)
        self.assertGreater(res.immediate_ratio, 0.0)
        self.assertGreater(res.total_ladder_ratio, 0.0)
        self.assertEqual(len(res.six_factors), 6)
        self.assertIn("factor_1_size", res.six_factors)
        self.assertIn("factor_6_atr_volatility", res.six_factors)

    def test_dual_inviolable_stops_and_sizing(self) -> None:
        """Verify structural stop and disaster hard stop below 200 SMA & 25x shelf."""
        res = self.engine.evaluate(self.store)
        self.assertGreater(res.structural_stop_price, 0.0)
        self.assertGreater(res.disaster_stop_price, 0.0)
        self.assertLess(res.disaster_stop_price, res.spot_price)
        self.assertLessEqual(res.disaster_stop_price, res.structural_stop_price)
        self.assertIn(res.rotation, ("USDT -> BTC", "BTC -> USDT", "Remain USDT"))
        self.assertGreaterEqual(res.sizing_factor, 0.0)
        self.assertLessEqual(res.sizing_factor, 1.0)


if __name__ == "__main__":
    unittest.main()
