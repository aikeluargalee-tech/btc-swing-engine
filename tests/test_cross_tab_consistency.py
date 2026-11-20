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


if __name__ == "__main__":
    unittest.main()
