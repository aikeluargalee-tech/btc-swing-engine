import unittest

from analytics.signal_detector import build_tab1_verdict
from core.models import ExecutionGateState, MarketRegime


class Tab1VerdictTests(unittest.TestCase):
    def test_red_for_markdown_or_hard_veto(self):
        markdown = build_tab1_verdict(
            ExecutionGateState.CASH_MARKDOWN, MarketRegime.MARKDOWN, False, 90, 70
        )
        veto = build_tab1_verdict(
            ExecutionGateState.NEUTRAL_OBSERVATION, MarketRegime.BALANCED, True, 90, 70
        )
        self.assertEqual(markdown.light, "RED")
        self.assertEqual(veto.light, "RED")

    def test_yellow_for_watch_and_standby_states(self):
        watch = build_tab1_verdict(
            ExecutionGateState.GATE4_PENDING_RETEST, MarketRegime.BALANCED, False, 60, 70
        )
        standby = build_tab1_verdict(
            ExecutionGateState.NEUTRAL_OBSERVATION, MarketRegime.BALANCED, False, 60, 70
        )
        self.assertEqual(watch.light, "YELLOW")
        self.assertEqual(standby.light, "YELLOW")

    def test_blue_for_armed_microstructure(self):
        verdict = build_tab1_verdict(
            ExecutionGateState.GATE2_MICROSTRUCTURE_ARMED,
            MarketRegime.ABSORPTION_AT_SUPPORT,
            False,
            69,
            70,
        )
        self.assertEqual(verdict.light, "BLUE")

    def test_green_uses_configured_threshold_and_records_conditions(self):
        verdict = build_tab1_verdict(
            ExecutionGateState.GATE3_RECLAIM_TRIGGERED,
            MarketRegime.ABSORPTION_AT_SUPPORT,
            False,
            65,
            65,
        )
        self.assertEqual(verdict.light, "GREEN")
        self.assertIn("required threshold 65.0", verdict.conditions[3])
        self.assertTrue(verdict.reason)

    def test_reclaim_below_configured_threshold_is_not_green(self):
        verdict = build_tab1_verdict(
            ExecutionGateState.GATE3_RECLAIM_TRIGGERED,
            MarketRegime.ABSORPTION_AT_SUPPORT,
            False,
            74,
            75,
        )
        self.assertEqual(verdict.light, "YELLOW")


if __name__ == "__main__":
    unittest.main()
