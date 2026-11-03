"""Unit tests for Special Tab [S5]: Terminal Exhaustion & Delta Divergence Radar."""

import unittest
from typing import List

from analytics.ai_packet_exporter import build_ai_telemetry_packet
from analytics.exhaustion_engine import ExhaustionEngine
from config.settings import DEFAULT_CONFIG
from core.models import (
    DerivativesSnapshot,
    ExhaustionRegime,
    FlowSnapshot,
    KlineBar,
    VolumeProfileResult,
)
from core.state_store import StateStore
from ui.terminal_hud import build_dashboard_renderable


def _create_synthetic_td9_bars(direction: str = "BEARISH") -> List[KlineBar]:
    """Generates synthetic 1H bars with a perfected Tom DeMark TD-9 setup."""
    bars: List[KlineBar] = []
    base_ts = 1_720_000_000_000

    if direction == "BEARISH":
        # Price rising: close[i] > close[i-4] for consecutive bars
        prices = [
            79_600, 79_700, 79_800, 79_900,          # Baseline 4 bars
            80_000, 80_100, 80_200, 80_300, 80_400,  # Bars 4-8
            80_600, 80_800, 81_000, 81_300, 81_700,  # Bars 9-13
            82_000, 82_400, 82_900, 83_500,          # Bars 14-17 (Bar 17 highest -> perfected)
        ]
    else:
        # Price falling: close[i] < close[i-4] for consecutive bars
        prices = [
            83_900, 83_800, 83_700, 83_600,
            83_500, 83_400, 83_300, 83_200, 83_100,
            82_900, 82_700, 82_500, 82_200, 81_800,
            81_500, 81_100, 80_600, 80_000,
        ]

    n_bars = len(prices)
    for i, p in enumerate(prices):
        ts = base_ts + i * 3600 * 1000
        bars.append(
            KlineBar(
                timestamp_ms=ts,
                open=p - 50.0,
                high=p + 150.0 if (i == n_bars - 1 and direction == "BEARISH") else p + 80.0,
                low=p - 150.0 if (i == n_bars - 1 and direction == "BULLISH") else p - 80.0,
                close=p,
                volume=1000.0,
                taker_buy_volume=650.0 if i < 10 else 400.0,  # Delta exhaustion on late bars
            )
        )
    return bars


class TestExhaustionRadarEngine(unittest.TestCase):
    """Verifies TD-9 Sequential, multi-horizon CVD divergences, exhaustion scoring, and Tab S5 HUD."""

    def setUp(self) -> None:
        self.config = DEFAULT_CONFIG
        self.engine = ExhaustionEngine(self.config)
        self.store = StateStore()

    def test_td_sequential_bearish_and_bullish_perfection(self) -> None:
        """Verifies Tom DeMark 9-count price sequential and perfection detection."""
        # 1. Bearish Setup (Price rising into top)
        bars_up = _create_synthetic_td9_bars("BEARISH")
        td_bearish = self.engine._compute_td_sequential(bars_up, "1H")
        self.assertEqual(td_bearish.setup_count, 9)
        self.assertIn("BEARISH", td_bearish.direction)
        self.assertTrue(td_bearish.is_perfected)
        self.assertIn("PERFECTED", td_bearish.status)
        self.assertGreater(td_bearish.invalidation_level, 83_000.0)

        # 2. Bullish Setup (Price falling into bottom)
        bars_down = _create_synthetic_td9_bars("BULLISH")
        td_bullish = self.engine._compute_td_sequential(bars_down, "1H")
        self.assertEqual(td_bullish.setup_count, 9)
        self.assertIn("BULLISH", td_bullish.direction)
        self.assertTrue(td_bullish.is_perfected)
        self.assertIn("PERFECTED", td_bullish.status)
        self.assertLess(td_bullish.invalidation_level, 80_500.0)

    def test_cvd_divergence_detection(self) -> None:
        """Verifies detection of price Higher High with CVD Delta deceleration."""
        bars = _create_synthetic_td9_bars("BEARISH")
        divs = self.engine._detect_cvd_divergences(
            bars, horizon_label="1H", spot_delta=-15.0, perp_delta=45.0
        )
        self.assertGreaterEqual(len(divs), 1)
        types = [d.divergence_type for d in divs]
        self.assertTrue(any("REGULAR_BEARISH" in t or "DERIVATIVES TRAP" in t for t in types))

    def test_exhaustion_engine_evaluation_and_trade_plan(self) -> None:
        """Verifies unified ExhaustionEngine produces 0-100 score, regime state, and trade plan."""
        bars_1h = _create_synthetic_td9_bars("BEARISH")
        bars_4h = bars_1h[-6:]
        bars_15m = bars_1h[-4:]

        self.store.spot_klines_1h.extend(bars_1h)
        self.store.spot_klines_15m.extend(bars_15m)
        self.store.binance_spot_price = bars_1h[-1].close

        deriv = DerivativesSnapshot(
            perp_5m_delta_btc=35.0,
            oi_change_15m_pct=0.45,  # OI Climax surge
            oi_change_1h_pct=1.40,
            funding_rate_pct=0.030,  # Funding stress
        )
        flow = FlowSnapshot()
        flow.w_15m.spot_delta_btc = -10.0
        flow.w_1h.spot_delta_btc = -25.0
        flow.w_1h.perp_delta_btc = 60.0

        vp = VolumeProfileResult(
            horizon_label="30D Macro",
            c_vah=84_000.0,
            c_poc=81_500.0,
            c_val=80_000.0,
            range_high=85_000.0,
            range_low=79_000.0,
            total_volume=50_000.0,
            bin_width=100.0,
        )

        ev = self.engine.evaluate(
            self.store, bars_1h, bars_4h, bars_15m, deriv, flow, active_vp=vp
        )
        self.assertIsNotNone(ev)
        self.assertIsNotNone(self.store.exhaustion_evaluation)
        assert ev is not None

        # Check Exhaustion Regime and Score
        self.assertGreaterEqual(ev.exhaustion_score, 60.0)
        self.assertIn(
            ev.exhaustion_regime,
            (ExhaustionRegime.TERMINAL_EXHAUSTION_ARMED, ExhaustionRegime.ACTIVE_REVERSAL_TRIGGER),
        )
        self.assertTrue(ev.oi_climax_flag)
        self.assertTrue(ev.funding_climax_flag)

        # Check Trade Plan
        self.assertIsNotNone(ev.trade_plan)
        assert ev.trade_plan is not None
        self.assertIn("SHORT", ev.trade_plan.direction)
        self.assertGreaterEqual(ev.trade_plan.rr_ratio, 2.0)
        self.assertGreater(ev.trade_plan.stop_loss, ev.trade_plan.entry_price)
        self.assertLess(ev.trade_plan.tp1_fast_mean, ev.trade_plan.entry_price)

    def test_tab_s5_hud_rendering(self) -> None:
        """Verifies Tab [S5] 5-panel layout renders into Rich renderable without exceptions."""
        bars_1h = _create_synthetic_td9_bars("BEARISH")
        bars_4h = bars_1h[-6:]
        bars_15m = bars_1h[-4:]
        self.store.spot_klines_1h.extend(bars_1h)
        self.store.spot_klines_15m.extend(bars_15m)
        self.store.binance_spot_price = bars_1h[-1].close

        deriv = DerivativesSnapshot(
            perp_5m_delta_btc=25.0,
            oi_change_15m_pct=0.35,
            oi_change_1h_pct=1.10,
            funding_rate_pct=0.022,
        )
        flow = FlowSnapshot()

        self.engine.evaluate(self.store, bars_1h, bars_4h, bars_15m, deriv, flow)

        renderable = build_dashboard_renderable(self.config, self.store, tab_override=9)
        self.assertIsNotNone(renderable)

    def test_ai_packet_exporter_includes_section_11(self) -> None:
        """Verifies AI Telemetry Packet appends SECTION 11 with Tables 11A, 11B, and 11C."""
        bars_1h = _create_synthetic_td9_bars("BEARISH")
        bars_4h = bars_1h[-6:]
        bars_15m = bars_1h[-4:]
        self.store.spot_klines_1h.extend(bars_1h)
        self.store.spot_klines_15m.extend(bars_15m)
        self.store.binance_spot_price = bars_1h[-1].close

        deriv = DerivativesSnapshot(
            perp_5m_delta_btc=30.0,
            oi_change_15m_pct=0.45,
            oi_change_1h_pct=1.30,
            funding_rate_pct=0.028,
        )
        flow = FlowSnapshot()

        self.engine.evaluate(self.store, bars_1h, bars_4h, bars_15m, deriv, flow)

        packet = build_ai_telemetry_packet(self.config, self.store)
        self.assertIn("SECTION 11: TAB [9] TERMINAL EXHAUSTION & DELTA DIVERGENCE RADAR", packet)
        self.assertIn("11A. Tom DeMark (TD) Sequential Setup Audit", packet)
        self.assertIn("11B. Multi-Horizon CVD Divergence", packet)


if __name__ == "__main__":
    unittest.main()
