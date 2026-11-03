"""Unit tests for Tab [S1] MM-BTC Multi-Model Engine, Rough Path Signatures, and HUD rendering."""

import unittest
from typing import List

from analytics.ai_packet_exporter import build_ai_telemetry_packet
from analytics.mm_btc_engine import MMBTCEngine
from analytics.signal_detector import SignalDetector
from config.settings import DEFAULT_CONFIG
from core.models import DerivativesSnapshot, KlineBar, OIPositioningQuadrant
from core.state_store import StateStore
from ui.terminal_hud import build_dashboard_renderable


def _create_synthetic_bars(count: int = 200, base_price: float = 90_000.0, step_minutes: int = 60) -> List[KlineBar]:
    bars: List[KlineBar] = []
    base_ts = 1_720_000_000_000
    for i in range(count):
        ts = base_ts + i * step_minutes * 60_000
        # Mild upward drift with small cycle fluctuation
        price = base_price + (i * 15.0) + (150.0 if (i % 8) < 4 else -150.0)
        vol = 300.0 + (i % 20) * 10.0
        bars.append(
            KlineBar(
                timestamp_ms=ts,
                open=price - 20.0,
                high=price + 50.0,
                low=price - 50.0,
                close=price + 20.0,
                volume=vol,
                taker_buy_volume=vol * 0.52,
            )
        )
    return bars


class TestMMBTCEngine(unittest.TestCase):
    """Verifies Rough Path Signatures, 5 stochastic lenses, 3-gate arbitration, and Tab S1 HUD."""

    def setUp(self) -> None:
        self.config = DEFAULT_CONFIG
        self.engine = MMBTCEngine(self.config)
        self.store = StateStore()

    def test_mm_btc_evaluation_metrics(self) -> None:
        bars_1h = _create_synthetic_bars(count=200, base_price=90_000.0, step_minutes=60)
        bars_15m = _create_synthetic_bars(count=60, base_price=93_000.0, step_minutes=15)
        self.store.spot_klines_1h = bars_1h
        self.store.perp_klines_1h = bars_1h
        self.store.spot_klines_15m = bars_15m
        self.store.binance_spot_price = bars_1h[-1].close
        self.store.binance_perp_price = bars_1h[-1].close + 10.0
        self.store.coinbase_spot_price = bars_1h[-1].close + 5.0

        deriv = DerivativesSnapshot(
            open_interest_btc=95000.0,
            open_interest_usd=95000.0 * bars_1h[-1].close,
            oi_change_15m_pct=0.1,
            oi_change_1h_pct=0.5,
            oi_change_4h_pct=1.2,
            oi_regime_quadrant=OIPositioningQuadrant.AGGRESSIVE_SHORT_BUILD,
            funding_rate_pct=0.005,
            taker_long_short_ratio_5m=1.05,
            perp_5m_delta_btc=25.0,
            coinbase_price=bars_1h[-1].close + 5.0,
            binance_spot_price=bars_1h[-1].close,
            binance_perp_price=bars_1h[-1].close + 10.0,
            coinbase_premium_usd=5.0,
            coinbase_premium_pct=0.005,
            coinbase_premium_zscore=0.4,
            perp_basis_usd=10.0,
            perp_source="binance_perp",
        )
        self.store.derivatives_snapshot = deriv

        ev = self.engine.evaluate(self.store, bars_1h, bars_15m, deriv)
        self.assertIsNotNone(ev)
        assert ev is not None

        # Verify Path Signatures
        self.assertIsInstance(ev.signature.roughness, float)
        self.assertGreaterEqual(ev.signature.roughness, 0.0)
        self.assertIsInstance(ev.signature.area_time_price, float)
        self.assertIsInstance(ev.signature.area_price_flow, float)
        self.assertIsInstance(ev.signature.area_price_oi, float)

        # Verify Lens A Kalman
        self.assertAlmostEqual(ev.kalman.filtered_price, bars_1h[-1].close, delta=1500.0)
        self.assertIsInstance(ev.kalman.velocity, float)

        # Verify Lens B Hurst
        self.assertGreaterEqual(ev.hurst.hurst, 0.0)
        self.assertLessEqual(ev.hurst.hurst, 1.0)

        # Verify Lens C FracDiff
        self.assertGreaterEqual(ev.frac_diff.optimal_d, 0.05)
        self.assertLessEqual(ev.frac_diff.optimal_d, 1.0)
        self.assertIsInstance(ev.frac_diff.momentum, float)

        # Verify Lens D Hilbert
        self.assertGreaterEqual(ev.hilbert.dominant_cycle, 8.0)
        self.assertLessEqual(ev.hilbert.dominant_cycle, 72.0)
        self.assertGreaterEqual(ev.hilbert.phase, 0.0)
        self.assertLessEqual(ev.hilbert.phase, 360.0)

        # Verify 3-Gate arbitration
        self.assertIsInstance(ev.gate1_pass, bool)
        self.assertIsInstance(ev.gate2_pass, bool)
        self.assertIsInstance(ev.gate3_y_hat, float)
        self.assertIsInstance(ev.action_plan_cash, str)

    def test_tab_s1_hud_rendering(self) -> None:
        bars_1h = _create_synthetic_bars(count=200, base_price=90_000.0, step_minutes=60)
        bars_15m = _create_synthetic_bars(count=60, base_price=93_000.0, step_minutes=15)
        self.store.spot_klines_1h = bars_1h
        self.store.spot_klines_15m = bars_15m
        self.store.binance_spot_price = bars_1h[-1].close

        detector = SignalDetector(self.config)
        detector.evaluate(self.store)

        renderable = build_dashboard_renderable(self.config, self.store, tab_override=5)
        self.assertIsNotNone(renderable)

    def test_ai_packet_exporter_includes_section_7(self) -> None:
        bars_1h = _create_synthetic_bars(count=200, base_price=90_000.0, step_minutes=60)
        bars_15m = _create_synthetic_bars(count=60, base_price=93_000.0, step_minutes=15)
        self.store.spot_klines_1h = bars_1h
        self.store.spot_klines_15m = bars_15m
        self.store.binance_spot_price = bars_1h[-1].close

        detector = SignalDetector(self.config)
        detector.evaluate(self.store)

        packet = build_ai_telemetry_packet(self.config, self.store)
        self.assertIn("## SECTION 7: MM-BTC — THE ROUGH PATH ARBITRATOR", packet)
        self.assertIn("7A. Rough Path Signatures", packet)
        self.assertIn("7B. Orthogonal Mathematical Lenses (A–E)", packet)
        self.assertIn("7C. 3-Gate Institutional Arbitration", packet)


if __name__ == "__main__":
    unittest.main()
