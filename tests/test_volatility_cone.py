"""Unit tests for Tab [S2] 72-Hour Forward Volatility Cone & Quarantined TSFM Benchmark Desk."""

import unittest
from typing import List
import numpy as np

from analytics.ai_packet_exporter import build_ai_telemetry_packet
from analytics.signal_detector import SignalDetector
from analytics.volatility_cone_engine import VolatilityConeEngine
from config.settings import DEFAULT_CONFIG
from core.models import KlineBar
from core.state_store import StateStore
from ui.terminal_hud import build_dashboard_renderable


def _create_synthetic_bars(count: int = 150, base_price: float = 85_000.0, step_minutes: int = 60) -> List[KlineBar]:
    bars: List[KlineBar] = []
    base_ts = 1_720_000_000_000
    for i in range(count):
        ts = base_ts + i * step_minutes * 60_000
        # Volatile oscillatory pattern to exercise Garman-Klass variance
        swing = 350.0 * np.sin(i * 0.25)
        price = base_price + (i * 20.0) + swing
        high = price + 220.0 + (i % 5) * 20.0
        low = price - 220.0 - (i % 7) * 15.0
        vol = 500.0 + (i % 15) * 25.0
        bars.append(
            KlineBar(
                timestamp_ms=ts,
                open=price - 40.0,
                high=high,
                low=low,
                close=price + 40.0,
                volume=vol,
                taker_buy_volume=vol * 0.51,
            )
        )
    return bars


class TestVolatilityConeEngine(unittest.TestCase):
    """Verifies Garman-Klass math, Hurst t^H scaling, VCR ratio, and Tab S2 HUD rendering."""

    def setUp(self) -> None:
        self.config = DEFAULT_CONFIG
        self.engine = VolatilityConeEngine(self.config)
        self.store = StateStore()

    def test_garman_klass_volatility_math(self) -> None:
        """Verifies Garman-Klass variance formula returns non-zero, statistically efficient volatility."""
        bars_1h = _create_synthetic_bars(count=120, base_price=82_000.0)
        from analytics.volume_profile import synthesize_4h_bars
        bars_4h = synthesize_4h_bars(bars_1h)

        sigma_gk = self.engine.compute_garman_klass_volatility(bars_4h, lookback=18)
        self.assertIsInstance(sigma_gk, float)
        self.assertGreater(sigma_gk, 0.001)  # > 0.1%
        self.assertLess(sigma_gk, 0.10)     # < 10% per 4h bar

    def test_volatility_cone_evaluation_and_quarantine(self) -> None:
        """Verifies 4 forward horizons, t^H fan expansion, TSFM baselines, VCR calculation, and 0.0% capital quarantine."""
        bars_1h = _create_synthetic_bars(count=160, base_price=80_910.0)
        self.store.spot_klines_1h = bars_1h
        self.store.binance_spot_price = bars_1h[-1].close

        ev = self.engine.evaluate(self.store, bars_1h)
        self.assertIsNotNone(ev)
        assert ev is not None

        # 1. Check Hurst Exponent and Garman-Klass bounds
        self.assertGreaterEqual(ev.hurst_exponent, 0.30)
        self.assertLessEqual(ev.hurst_exponent, 0.75)
        self.assertGreater(ev.garman_klass_vol_4h, 0.0)
        self.assertGreater(ev.garman_klass_annualized_vol, 0.0)

        # 2. Check 4 forward horizons: +4h, +24h, +48h, +72h
        self.assertEqual(len(ev.horizons), 4)
        for row in ev.horizons:
            # 1σ and 2σ band ordering
            self.assertLess(row.gk_2sigma_lower, row.gk_1sigma_lower)
            self.assertLess(row.gk_1sigma_lower, row.drift_center)
            self.assertLess(row.drift_center, row.gk_1sigma_upper)
            self.assertLess(row.gk_1sigma_upper, row.gk_2sigma_upper)

        # 3. Check Mandelbrot t^H volatility fan expansion
        h1, h6, h12, h18 = ev.horizons
        self.assertLess(h1.gk_1sigma_spread_usd, h6.gk_1sigma_spread_usd)
        self.assertLess(h6.gk_1sigma_spread_usd, h12.gk_1sigma_spread_usd)
        self.assertLess(h12.gk_1sigma_spread_usd, h18.gk_1sigma_spread_usd)

        # 4. Check Quarantined TSFM Benchmarks
        self.assertEqual(len(ev.tsfm_benchmarks), 3)
        model_names = [m.name for m in ev.tsfm_benchmarks]
        self.assertIn("Kronos-base", model_names)
        self.assertIn("Chronos-Bolt-small", model_names)
        self.assertIn("TimesFM 2.5", model_names)

        # Separation of Church and State: Strictly 0.0% capital allocation
        self.assertEqual(ev.capital_weight_allocated, 0.0)
        for m in ev.tsfm_benchmarks:
            self.assertIn("0.0% CAPITAL WEIGHT", m.quarantine_status)

        # 5. Check Variance Compression Ratio (VCR_72h)
        self.assertGreater(ev.vcr_72h, 0.0)
        self.assertIn(ev.vcr_status, [
            "SEVERE AI COMPRESSION / COILED SPRING",
            "MODERATE AI COMPRESSION (TSFMs UNDERESTIMATING TAIL RISK)",
            "NORMAL ALIGNMENT",
        ])

        # 6. Check Plain English Summary for Beginners
        self.assertIsNotNone(ev.plain_english_summary)
        self.assertIn("Why the AI lines are flat", ev.plain_english_summary)
        self.assertIn("Where price will actually move", ev.plain_english_summary)
        self.assertIn("Rule for your wallet", ev.plain_english_summary)

    def test_tab_s2_hud_rendering(self) -> None:
        """Verifies Tab [S2] 5-panel layout renders into Rich renderable without exceptions."""
        bars_1h = _create_synthetic_bars(count=160, base_price=80_910.0)
        self.store.spot_klines_1h = bars_1h
        self.store.binance_spot_price = 80_910.0

        # Evaluate engine
        self.engine.evaluate(self.store, bars_1h)

        renderable = build_dashboard_renderable(self.config, self.store, tab_override=7)
        self.assertIsNotNone(renderable)

    def test_ai_packet_exporter_includes_section_8(self) -> None:
        """Verifies AI Telemetry Packet appends SECTION 8 with Tables 8A, 8B, and 8C."""
        bars_1h = _create_synthetic_bars(count=160, base_price=80_910.0)
        self.store.spot_klines_1h = bars_1h
        self.store.binance_spot_price = 80_910.0

        detector = SignalDetector(self.config)
        # Populate minimum state
        from analytics.volume_profile import compute_composite_profile
        self.store.macro_profile = compute_composite_profile(bars_1h[-720:], horizon_label="30D Macro Profile")
        self.store.tactical_profile = compute_composite_profile(bars_1h[-168:], horizon_label="7D Tactical Profile")
        self.engine.evaluate(self.store, bars_1h, self.store.macro_profile)

        packet = build_ai_telemetry_packet(self.config, self.store)
        self.assertIn("## SECTION 8: 72-HOUR FORWARD VOLATILITY CONE & AI BENCHMARK RADAR (TAB [S2])", packet)
        self.assertIn("### 8A. 72-Hour Forward Volatility Cone Fan Table", packet)
        self.assertIn("### 8B. Quarantined Time-Series Foundation Models", packet)
        self.assertIn("### 8C. Quantitative Variance Compression Analysis", packet)
        self.assertIn("### 8D. Plain English Summary for Traders & Beginners", packet)
        self.assertIn("Kronos-base", packet)
        self.assertIn("Chronos-Bolt-small", packet)
        self.assertIn("TimesFM 2.5", packet)
        self.assertIn("BENCHMARK & VOLATILITY RADAR ONLY — 0.0% CAPITAL ALLOCATION WEIGHT (QUARANTINED)", packet)


if __name__ == "__main__":
    unittest.main()
