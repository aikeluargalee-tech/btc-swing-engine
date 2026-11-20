"""Cross-tab agreement tests.

Every defect found in this audit was a case of two components describing the same
concept differently:

  * Tab 4 said NO_MATCH while Tab 10 named "Config A" (the aggregator fell back to configs[0])
  * Tab 1 computed its own light from a hardcoded 70.0 while the engine used config
  * Tab M invented a $76,000 spot while its own provenance said MEASURED
  * Tab 11 reported a completed auction from a one-bin synthetic ladder
  * Section 19 printed AUTHORIZED while the architecture is veto-only

Unit tests cannot catch these: each component is internally consistent. Only a test that
reads two outputs and compares them can. These are those tests.

They cover the relationships that exist today. When a new desk starts consuming another,
add its agreement here rather than waiting for the next audit to find it.
"""
import io
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from rich.console import Console

from analytics.ai_packet_exporter import build_ai_telemetry_packet
from analytics.data_only_reports import build_tab_l_data_only_report
from analytics.signal_detector import SignalDetector
from analytics.master_synthesis import (
    SETUP_TRIGGER_KEY,
    VETO_GATE_KEY,
    tab_z_precedence,
)
from config.settings import DEFAULT_CONFIG
from core.models import KlineBar
from core.state_store import StateStore
from dataclasses import replace
from ui.terminal_hud import build_dashboard_renderable


def _fresh_context() -> Path:
    """A freshly-reviewed protocol context, so the vetoes are armed but not stale."""
    p = Path(tempfile.gettempdir()) / "cross_tab_protocol_context.json"
    p.write_text(json.dumps({
        "last_reviewed_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "liq_cascade_72h_over_300m": "CONFIRMED_CLEAR",
        "liq_cascade_reclaimed_within_24h": "CONFIRMED_CLEAR",
        "fomc_cpi_window_override": "AUTO",
        "s2_risk_level": "LOW",
        "etf_net_outflow_weakness": "NOT_CONFIRMED",
        "catalyst_technical_breakdown": "NOT_CONFIRMED",
        "enforce_200d_hard_veto_on_tab1": False,
    }), encoding="utf-8")
    return p


def _config():
    return replace(
        DEFAULT_CONFIG,
        protocol_context_path=_fresh_context(),
        signal_log_path=Path(tempfile.gettempdir()) / "cross_tab_signals.jsonl",
    )


def _flat_store() -> StateStore:
    """A flat tape: no regime qualifies, so Tab 4 reports NO_MATCH. That is the case the
    Tab 4 -> Tab 10 bug lived in, so keep it in the suite."""
    st = StateStore()
    now = int(datetime.now(timezone.utc).timestamp() * 1000)
    for d in range(255):
        st.spot_klines_1d.append(KlineBar(
            timestamp_ms=now - (255 - d) * 86_400_000, open=90_000.0, high=90_050.0,
            low=89_950.0, close=90_000.0, volume=100.0, taker_buy_volume=50.0))
    bars = [KlineBar(timestamp_ms=now - (240 - i) * 3_600_000, open=90_000.0, high=90_010.0,
                     low=89_990.0, close=90_000.0, volume=10.0, taker_buy_volume=5.0)
            for i in range(240)]
    st.spot_klines_1h.extend(bars)
    st.spot_klines_15m.extend(bars[-80:])
    st.binance_spot_price = 90_000.0
    st.binance_perp_price = 90_000.0
    st.coinbase_spot_price = 90_000.0
    return st


class TestRegimeAgreement(unittest.TestCase):
    """Tab 10 must describe the same regime as Tab 4, or say it has none."""

    @classmethod
    def setUpClass(cls):
        cls.cfg = _config()
        cls.store = _flat_store()
        SignalDetector(cls.cfg).evaluate(cls.store)
        cls.rm = cls.store.regime_matrix_evaluation
        cls.ms = cls.store.master_synthesis_evaluation

    def test_both_evaluations_exist(self):
        self.assertIsNotNone(self.rm)
        self.assertIsNotNone(self.ms)

    def test_master_headline_never_names_a_regime_tab4_refused(self):
        code = str(getattr(self.rm, "active_config_code", ""))
        headline = str(getattr(self.ms, "master_headline", ""))
        if code == "NO_MATCH" or not code.startswith("Config "):
            self.assertNotIn("Config A", headline,
                             "Tab 4 refused a regime but Tab 10 named Config A")
            self.assertNotIn("Config B", headline)
            self.assertIn("MATCH", headline.upper())
        else:
            self.assertIn(code, headline,
                          f"Tab 10 headline does not state Tab 4's regime {code}")

    def test_master_light_is_not_green_without_a_named_regime(self):
        code = str(getattr(self.rm, "active_config_code", ""))
        light = str(getattr(self.ms, "master_traffic_light", ""))
        if code == "NO_MATCH" or not code.startswith("Config "):
            self.assertNotEqual(light, "GREEN",
                                "a refused regime must not produce a GREEN master light")

    def test_tab_z_verdict_is_derivable_from_printed_states(self):
        # Recompute from the table the operator can see. No hidden argument may be needed:
        # the trigger and veto gate are reserved keys IN that table.
        states = dict(self.ms.input_states)
        self.assertIn(SETUP_TRIGGER_KEY, states,
                      "the setup trigger is not printed, so the verdict is not derivable")
        expected = tab_z_precedence(states)
        self.assertEqual(self.ms.decision_verdict, expected)
        self.assertEqual(self.ms.regime_code, getattr(self.rm, "active_config_code", "NO_MATCH"))

    def test_blocking_desk_always_yields_no_trade(self):
        self.assertEqual(
            tab_z_precedence({"desk": "LIVE", VETO_GATE_KEY: "REFUSED",
                              SETUP_TRIGGER_KEY: "OBSERVED"}), "NO_TRADE")

    def test_synthetic_and_unavailable_cannot_raise_verdict(self):
        for state in ("SYNTHETIC", "UNAVAILABLE"):
            self.assertEqual(
                tab_z_precedence({"desk": state, SETUP_TRIGGER_KEY: "OBSERVED"}), "NO_TRADE")
        # a clean table with an observed setup is the only path above NO_TRADE
        self.assertEqual(
            tab_z_precedence({"desk": "LIVE", SETUP_TRIGGER_KEY: "OBSERVED"}),
            "SETUP_STATE_OPERATOR_DECIDES")


class TestPacketAgreement(unittest.TestCase):
    """The exported packet must contain the verdicts the screen shows."""

    @classmethod
    def setUpClass(cls):
        cls.cfg = _config()
        cls.store = _flat_store()
        SignalDetector(cls.cfg).evaluate(cls.store)
        cls.packet = build_ai_telemetry_packet(cls.cfg, cls.store)

    def test_packet_carries_tab1_verdict(self):
        sig = getattr(self.store, "latest_signal", None)
        self.assertIsNotNone(sig, "no signal evaluation was stored")
        verdict = getattr(sig, "tab1_verdict", None)
        self.assertIsNotNone(verdict, "Tab 1 verdict is not on the evaluation")
        self.assertIn(str(verdict.light), self.packet,
                      "the packet does not contain Tab 1's verdict light")

    def test_packet_carries_master_headline(self):
        headline = str(getattr(self.store.master_synthesis_evaluation, "master_headline", ""))
        key = headline[:40]
        self.assertIn(key, self.packet, "the packet omits the master headline shown on screen")

    def test_packet_contains_no_authorisation_claims(self):
        upper = self.packet.upper()
        self.assertNotIn("AUTHORIZED", upper)
        self.assertNotIn("EXECUTION AUTHORIZATION", upper)


class TestTabZExportCarriesTheDecision(unittest.TestCase):
    """The exported Z packet is what the operator hands to a reviewer, so it must state the
    decision and the reasons - in vocabulary that survives the data-only sanitiser.

    The defect this locks down: the raw verdict went through sanitize_data_only_text(), a blunt
    substring pass, so "NO_TRADE" was published as "NO_position". It corrupted a state name,
    which is worse than either the verdict or a clean state.
    """

    BLOCKING = {"SYNTHETIC", "STALE", "UNAVAILABLE", "NO_MATCH", "REFUSED"}
    FORBIDDEN = ("verdict", "trade", "wait", "bullish", "bearish",
                 "confirmed", "rejected", "recommend")

    @classmethod
    def setUpClass(cls):
        cls.cfg = _config()
        cls.store = _flat_store()
        SignalDetector(cls.cfg).evaluate(cls.store)
        cls.ms = cls.store.master_synthesis_evaluation
        cls.report = build_tab_l_data_only_report(cls.cfg, cls.store)
        cls.states = dict(getattr(cls.ms, "input_states", {}) or {})

    def _expected_state(self) -> str:
        if any(s in self.BLOCKING for s in self.states.values()):
            return "BLOCKED"
        if self.states.get("[Setup Trigger]") == "OBSERVED":
            return "ELIGIBLE_FOR_OPERATOR_REVIEW"
        return "FORMING"

    def test_export_states_the_decision_and_agrees_with_the_engine(self):
        self.assertIn("## 0. DECISION STATE", self.report, "the export states no decision")
        expected = self._expected_state()
        self.assertIn(f"`{expected}`", self.report,
                      f"the exported decision state is not {expected}")
        self.assertEqual(expected == "BLOCKED", self.ms.decision_verdict == "NO_TRADE",
                         "exported decision state disagrees with the engine's verdict")

    def test_export_lists_every_desk_state(self):
        self.assertTrue(self.states, "no state table to export")
        for desk, state in self.states.items():
            self.assertIn(f"`{desk}`: `{state}`", self.report,
                          f"{desk} is missing from the exported state table")

    def test_export_keeps_the_data_only_contract(self):
        lower = self.report.lower()
        for word in self.FORBIDDEN:
            self.assertNotIn(word, lower,
                             f"forbidden interpretive word '{word}' in the data-only export")

    def test_unavailable_desk_cannot_create_a_setup_trigger(self):
        """A desk reporting UNAVAILABLE cannot be the source of an observed setup: its verdict
        field is stale by definition. Without this, Tab [0] read OBSERVED while its own row
        said UNAVAILABLE, because the trigger was taken from the same object."""
        for desk, state in self.states.items():
            if state == "UNAVAILABLE" and desk.endswith("Spot Swing"):
                self.assertNotEqual(self.states.get("[Setup Trigger]"), "OBSERVED",
                                    f"{desk} is UNAVAILABLE yet the setup trigger is OBSERVED")

    def test_export_does_not_corrupt_state_names(self):
        self.assertNotIn("NO_position", self.report,
                         "the sanitiser mangled a state name instead of stating it")


class TestNoImperativesInRenderedOutput(unittest.TestCase):
    """Veto-only: no rendered artefact may issue a trade instruction."""

    @classmethod
    def setUpClass(cls):
        cls.cfg = _config()
        cls.store = _flat_store()
        SignalDetector(cls.cfg).evaluate(cls.store)
        buf = io.StringIO()
        for tab in (0, 1, 2, 4, 10, 11, 13, 17, 18, 19, 20):
            Console(file=buf, width=180, force_terminal=False,
                    legacy_windows=False).print(
                build_dashboard_renderable(cls.cfg, cls.store, tab_override=tab))
        cls.screen = buf.getvalue()

    def test_screen_has_no_execute_imperative(self):
        for banned in ("EXECUTE ", "EXECUTION AUTHORIZED"):
            self.assertNotIn(banned, self.screen.upper(),
                             f"rendered output contains the imperative {banned!r}")

    def test_every_printed_desk_carries_its_own_explanation(self):
        """The source list promises 'evidence only', one line per desk. A desk that reports a
        state with no explanation is worse than no line at all: my first rewrite dropped the
        regime matrix's fallback and printed 'no reported conclusion' against a desk that was
        reporting LIVE."""
        self.assertNotIn("no reported conclusion", self.screen,
                         "a desk row printed without any explanation")


if __name__ == "__main__":
    unittest.main()
