"""Unit tests for Tab [G] Grok Dual-Horizon Flow & VWAP SD Matrix desk."""

import unittest
from datetime import datetime, timezone
from typing import List
import numpy as np

from analytics.grok_quant_engine import (
    GrokQuantEngine,
    copy_grok_prompt_to_clipboard,
)
from config.settings import DEFAULT_CONFIG
from core.models import (
    KlineBar,
    DerivativesSnapshot,
    SLSPEvaluation,
    SLSPKeyLevel,
)
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


class TestGrokQuantDesk(unittest.TestCase):
    """Verifies Anchored VWAP SD math, CoinGlass crowding, CVD divergence, and Tab [G] HUD rendering."""

    def setUp(self) -> None:
        self.config = DEFAULT_CONFIG
        self.engine = GrokQuantEngine(self.config)
        self.store = StateStore()

    def test_compute_anchored_vwap_sd_today(self) -> None:
        """Verify VWAP, SD bands, and Z-score calculation on recent bars."""
        bars_1h = _create_synthetic_bars(count=48, base_price=68000.0, step_minutes=60)
        bars_15m = _create_synthetic_bars(count=96, base_price=68000.0, step_minutes=15)
        vwap, sd1_u, sd2_u, sd1_l, sd2_l, sigma, z_score, band_status = (
            self.engine.compute_anchored_vwap_sd(bars_15m, bars_1h, 68500.0)
        )

        self.assertGreater(vwap, 0.0)
        self.assertGreater(sigma, 0.0)
        self.assertAlmostEqual(sd1_u, vwap + sigma, delta=0.05)
        self.assertAlmostEqual(sd1_l, vwap - sigma, delta=0.05)
        self.assertAlmostEqual(sd2_u, vwap + 2.0 * sigma, delta=0.05)
        self.assertAlmostEqual(sd2_l, vwap - 2.0 * sigma, delta=0.05)
        self.assertTrue(sd2_l < sd1_l < vwap < sd1_u < sd2_u)
        self.assertIsInstance(z_score, float)
        self.assertIsInstance(band_status, str)

    def test_compute_anchored_vwap_sd_empty(self) -> None:
        """Verify graceful fallback with empty bars."""
        vwap, sd1_u, sd2_u, sd1_l, sd2_l, sigma, z_score, band_status = (
            self.engine.compute_anchored_vwap_sd([], [], 67000.0)
        )
        self.assertEqual(vwap, 67000.0)
        self.assertAlmostEqual(sigma, 67000.0 * 0.015, places=1)
        self.assertEqual(z_score, 0.0)
        self.assertEqual(band_status, "FAIR_VALUE_ROTATION")

    def test_grok_quant_engine_evaluate(self) -> None:
        """Verify complete evaluation pipeline and state store enrichment."""
        self.store.binance_spot_price = 68_500.0

        # Populate klines
        bars_1h = _create_synthetic_bars(count=72, base_price=68_000.0, step_minutes=60)
        for b in bars_1h:
            self.store.spot_klines_1h.append(b)

        bars_4h = _create_synthetic_bars(count=60, base_price=67_500.0, step_minutes=240)
        for b in bars_4h:
            self.store.spot_klines_4h.append(b)

        bars_1d = _create_synthetic_bars(count=120, base_price=65_000.0, step_minutes=1440)
        for b in bars_1d:
            self.store.spot_klines_1d.append(b)

        # Populate derivatives snapshot & crowding metrics
        deriv = DerivativesSnapshot(
            coinbase_premium_usd=18.5,
            coinbase_premium_pct=0.0270,
            coinbase_premium_zscore=1.45,
        )
        self.store.derivatives_snapshot = deriv
        self.store.top_trader_long_pct = 65.2
        self.store.top_trader_short_pct = 34.8
        self.store.top_trader_ls_ratio = 1.87
        self.store.global_account_ls_ratio = 3.10
        self.store.open_interest_btc = 78_500.0
        self.store.open_interest_usd = 5_377_250_000.0
        self.store.funding_rate_pct = 0.0095

        # Populate SLSPEvaluation
        self.store.slsp_evaluation = SLSPEvaluation(
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
            spot_price=68_500.0,
            regime="BULLISH_TREND",
            regime_reason="Above EMA",
            key_levels=[],
            nearest_support=SLSPKeyLevel(
                price_min=67_200.0,
                price_max=67_300.0,
                center_price=67_250.0,
                level_type="SUPPORT",
                strength=3,
                touch_count=4,
                is_round_number=False,
                is_hvn=True,
                is_swing_pivot=True,
                description="H1 HVN",
            ),
            nearest_resistance=SLSPKeyLevel(
                price_min=70_400.0,
                price_max=70_600.0,
                center_price=70_500.0,
                level_type="RESISTANCE",
                strength=4,
                touch_count=5,
                is_round_number=True,
                is_hvn=True,
                is_swing_pivot=True,
                description="Daily Pivot",
            ),
            active_setup=None,
            trade_state="SCANNING",
            mode="CONSERVATIVE",
            circuit_breaker_active=False,
            circuit_breaker_reason="",
            daily_loss_pct=0.0,
            weekly_loss_pct=0.0,
            ema_3_regime="BULLISH",
            ema_3_slope_200=0.04,
            ema_3_value_zone_active=False,
            ema_3_adx=26.4,
            ema_3_positioning_met=3,
            tell_tale_status="NORMAL",
            tell_tale_veto=False,
            tell_tale_relvol_15m=1.05,
            tell_tale_relvol_5m=0.98,
            liq_flush_status="CLEAR",
            liq_flush_detected=False,
            liq_flush_wick_ratio=0.0,
            liq_flush_oi_delta=0.0,
            liq_detector_report=None,
            confluence_score=78,
            plain_english_summary="Bullish trend structure intact.",
            decision_log=[],
        )

        res = self.engine.evaluate(self.store)

        self.assertIsNotNone(res)
        self.assertIsNotNone(self.store.grok_quant_evaluation)
        self.assertGreater(res.vwap_daily, 0.0)
        self.assertGreater(res.vwap_sd1_upper, res.vwap_daily)
        self.assertLess(res.vwap_sd1_lower, res.vwap_daily)
        self.assertEqual(res.top_trader_long_pct, 65.2)
        self.assertEqual(res.top_trader_short_pct, 34.8)
        self.assertEqual(res.top_trader_ls_ratio, 1.87)
        self.assertEqual(res.global_account_ls_ratio, 3.10)
        self.assertIn("US_SPOT_PREMIUM", res.coinbase_premium_status)
        self.assertGreater(len(res.grok_master_prompt_text), 100)
        self.assertIn("## GROK BTC MARKET ANALYSIS", res.grok_master_prompt_text)
        self.assertIn("Positioning", res.grok_master_prompt_text)
        self.assertIn("Engine Bottomline Verdict", res.grok_master_prompt_text)
        self.assertIsNotNone(res.bottomline_verdict)
        self.assertGreater(len(res.bottomline_verdict), 3)
        self.assertGreater(len(res.bottomline_rationale), 10)
        self.assertGreater(len(res.bottomline_buy_trigger), 5)

    def test_tab15_terminal_hud_render(self) -> None:
        """Verify Tab 15 [G: GROK FLOW] builds cleanly without rendering exceptions."""
        self.store.binance_spot_price = 68_500.0
        bars_1h = _create_synthetic_bars(count=48, base_price=68_000.0, step_minutes=60)
        for b in bars_1h:
            self.store.spot_klines_1h.append(b)

        self.engine.evaluate(self.store)
        self.store.active_tab = 15

        # Render dashboard
        renderable = build_dashboard_renderable(self.config, self.store, tab_override=15)
        self.assertIsNotNone(renderable)

    def test_copy_grok_prompt_to_clipboard(self) -> None:
        """Verify clipboard helper extracts markdown without crashing."""
        self.store.binance_spot_price = 68_500.0
        bars_1h = _create_synthetic_bars(count=24, base_price=68_000.0, step_minutes=60)
        for b in bars_1h:
            self.store.spot_klines_1h.append(b)

        self.engine.evaluate(self.store)
        copied_ok, msg, char_count = copy_grok_prompt_to_clipboard(self.store)
        self.assertIsInstance(msg, str)
        self.assertGreater(char_count, 50)
        self.assertIn("chars", msg)


if __name__ == "__main__":
    unittest.main()
