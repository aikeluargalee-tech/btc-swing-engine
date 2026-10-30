"""Unit tests for Tab [S3] Gartley 222 Harmonics & 5-Strategy Spot Swing Confluence Desk."""

import unittest
from typing import List
import numpy as np

from analytics.ai_packet_exporter import build_ai_telemetry_packet
from analytics.gartley_engine import (
    GartleyEngine,
    check_gartley_ratios,
    compute_quant_horizon,
)
from config.settings import DEFAULT_CONFIG
from core.models import KlineBar
from core.state_store import StateStore
from ui.terminal_hud import build_dashboard_renderable


def _create_synthetic_bars(count: int = 120, base_price: float = 84_000.0, step_minutes: int = 240) -> List[KlineBar]:
    bars: List[KlineBar] = []
    base_ts = 1_720_000_000_000
    for i in range(count):
        ts = base_ts + i * step_minutes * 60_000
        swing = 400.0 * np.sin(i * 0.15)
        price = base_price + (i * 25.0) + swing
        high = price + 250.0 + (i % 6) * 15.0
        low = price - 250.0 - (i % 8) * 12.0
        vol = 600.0 + (i % 20) * 30.0
        bars.append(
            KlineBar(
                timestamp_ms=ts,
                open=price - 30.0,
                high=high,
                low=low,
                close=price + 30.0,
                volume=vol,
                taker_buy_volume=vol * 0.52,
            )
        )
    return bars


class TestGartley5StrategyEngine(unittest.TestCase):
    """Verifies Fibonacci harmonic math, 5-strategy state machine, and Tab [S3] HUD rendering."""

    def setUp(self) -> None:
        self.config = DEFAULT_CONFIG
        self.engine = GartleyEngine(self.config)
        self.store = StateStore()

    def test_check_gartley_ratios_ideal_and_out_of_bounds(self) -> None:
        """Verifies Gartley 222 Fibonacci ratio constraints (B/XA 0.618, C/AB 0.382-0.886, D/XA 0.786, AB/CD 0.7-1.5)."""
        # Ideal Bullish Gartley points
        X = 80_000.0
        A = 85_000.0  # XA = 5000
        B = 81_910.0  # AB = 3090, B/XA = 0.618
        C = 83_820.0  # BC = 1910, C/AB = 0.618
        D = 81_070.0  # AD = 3930, D/XA = 0.786, CD = 2750, AB/CD = 1.124

        ok, ratios = check_gartley_ratios(X, A, B, C, D)
        self.assertTrue(ok)
        self.assertAlmostEqual(ratios["B/XA"], 0.62, places=2)
        self.assertAlmostEqual(ratios["C/AB"], 0.62, places=2)
        self.assertAlmostEqual(ratios["D/XA"], 0.79, places=2)
        self.assertAlmostEqual(ratios["AB/CD"], 1.12, places=2)

        # Out-of-bounds B point (e.g. B retraces too shallowly: 0.30 instead of [0.55, 0.72])
        bad_B = 83_500.0
        bad_ok, _ = check_gartley_ratios(X, A, bad_B, C, D)
        self.assertFalse(bad_ok)

        # Zero distance division protection
        zero_ok, zero_ratios = check_gartley_ratios(X, X, B, C, D)
        self.assertFalse(zero_ok)
        self.assertEqual(zero_ratios, {})

    def test_compute_quant_horizon_state_machine(self) -> None:
        """Verifies S1-S5 indicator calculations and S6-S7 harmonic scan across bars."""
        bars = _create_synthetic_bars(count=80, base_price=80_000.0)
        res = compute_quant_horizon(bars, tf="4h")
        self.assertIsNotNone(res)
        assert res is not None

        self.assertEqual(res.timeframe, "4H")
        self.assertIn(res.verdict, [
            "NO TRADE", "HOLD", "GARTLEY BUY", "CONFLUENCE BUY",
            "CONFLUENCE + GARTLEY BUY", "GARTLEY SELL TO USDT",
            "EXIT PRESSURE", "CONFLICT", "EXIT WARNING", "ENTRY WATCH"
        ])
        self.assertIn(res.v1_breakout, ["NEW", "HOLD", "EXIT", "FLAT"])
        self.assertIn(res.v2_sma200, ["NEW", "HOLD", "EXIT", "FLAT"])
        self.assertIn(res.v3_ema, ["NEW", "HOLD", "EXIT", "FLAT"])
        self.assertIn(res.v4_rsi, ["NEW", "HOLD", "EXIT", "FLAT"])
        self.assertIn(res.v5_bb, ["NEW", "HOLD", "EXIT", "FLAT"])
        self.assertIn(res.v6_gartley_bull, ["NEW LONG", "HOLD", "EXIT", "FLAT"])
        self.assertIn(res.v7_gartley_bear, ["SELL USDT", "USDT", "DONE", "FLAT"])

    def test_gartley_engine_evaluation_and_store_integration(self) -> None:
        """Verifies GartleyEngine produces unified 1D + 4H evaluation and stores in StateStore."""
        bars_1d = _create_synthetic_bars(count=60, base_price=78_000.0, step_minutes=1440)
        bars_1h = _create_synthetic_bars(count=200, base_price=82_000.0, step_minutes=60)

        self.store.spot_klines_1d.extend(bars_1d)
        self.store.spot_klines_1h.extend(bars_1h)
        self.store.binance_spot_price = bars_1h[-1].close

        ev = self.engine.evaluate(self.store)
        self.assertIsNotNone(ev)
        self.assertIsNotNone(self.store.gartley_evaluation)
        assert ev is not None

        self.assertEqual(ev.telegram_bot, "@Gartleyy_bot")
        self.assertEqual(ev.telegram_chat_id, "1273979711")
        self.assertIn("aikeluargalee-tech/btc-spot-verdict-bot", ev.standalone_bot_repo)
        self.assertGreater(ev.close_price, 0.0)
        self.assertIsNotNone(ev.res_1d)
        self.assertIsNotNone(ev.res_4h)
        self.assertTrue(len(ev.plain_english_summary) > 10)

    def test_tab_s3_hud_rendering(self) -> None:
        """Verifies Tab [S3] 5-panel layout renders into Rich renderable without exceptions."""
        bars_1d = _create_synthetic_bars(count=50, base_price=79_000.0, step_minutes=1440)
        bars_1h = _create_synthetic_bars(count=150, base_price=83_000.0, step_minutes=60)
        self.store.spot_klines_1d.extend(bars_1d)
        self.store.spot_klines_1h.extend(bars_1h)
        self.store.binance_spot_price = bars_1h[-1].close

        self.engine.evaluate(self.store)
        renderable = build_dashboard_renderable(self.config, self.store, tab_override=8)
        self.assertIsNotNone(renderable)

    def test_ai_packet_exporter_includes_section_9(self) -> None:
        """Verifies AI Telemetry Packet appends SECTION 9 with Tables 9A, 9B, 9C, and 9D."""
        bars_1d = _create_synthetic_bars(count=50, base_price=79_000.0, step_minutes=1440)
        bars_1h = _create_synthetic_bars(count=150, base_price=83_000.0, step_minutes=60)
        self.store.spot_klines_1d.extend(bars_1d)
        self.store.spot_klines_1h.extend(bars_1h)
        self.store.binance_spot_price = bars_1h[-1].close

        self.engine.evaluate(self.store)
        packet = build_ai_telemetry_packet(self.config, self.store)

        self.assertIn("## SECTION 9: TAB [S3] GARTLEY 222 & 5-STRATEGY CONFLUENCE RADAR", packet)
        self.assertIn("### 9A. 1D Daily Macro Trend State Machine", packet)
        self.assertIn("### 9B. 4H Tactical Swing Execution State Machine", packet)
        self.assertIn("### 9C. Harmonic Pattern Geometry & Fibonacci Verification", packet)
        self.assertIn("### 9D. Pine Script Verdict Priority Ladder", packet)
        self.assertIn("@Gartleyy_bot", packet)
        self.assertIn("aikeluargalee-tech/btc-spot-verdict-bot", packet)


if __name__ == "__main__":
    unittest.main()
