"""Unit tests for Macro Collector and Protocol Metrics Dossier (Section 12)."""

import unittest
from datetime import datetime, timezone
import numpy as np

from config.settings import DEFAULT_CONFIG
from core.models import KlineBar
from core.state_store import StateStore
from collectors.macro_collector import (
    MacroIntermarketSnapshot,
    _compute_rolling_correlation,
)
from analytics.protocol_dossier import (
    compute_protocol_metrics_dossier,
    format_protocol_metrics_dossier_markdown,
)
from analytics.ai_packet_exporter import build_ai_telemetry_packet


class TestMacroAndProtocolDossier(unittest.TestCase):
    """Test suite verifying macro collection, correlation math, and Section 12 rendering."""

    def test_rolling_correlation_computation(self):
        # Perfectly correlated
        x = [10.0 + i for i in range(30)]
        y = [20.0 + 2.0 * i for i in range(30)]
        r = _compute_rolling_correlation(x, y, 20)
        self.assertIsNotNone(r)
        self.assertAlmostEqual(r, 1.0, places=2)

        # Perfectly inversely correlated
        z = [100.0 - i for i in range(30)]
        r_inv = _compute_rolling_correlation(x, z, 20)
        self.assertIsNotNone(r_inv)
        self.assertAlmostEqual(r_inv, -1.0, places=2)

        # Insufficient data
        self.assertIsNone(_compute_rolling_correlation([1.0], [2.0], 20))

    def test_macro_snapshot_defaults_and_fallback(self):
        snap = MacroIntermarketSnapshot()
        self.assertIsNone(snap.brent_crude_price)
        self.assertIsNone(snap.us_10y_real_yield_tips)
        self.assertIsNone(snap.us_10y_breakeven_inflation)
        self.assertEqual(snap.etf_daily_net_flow_status, "unavailable")
        self.assertEqual(snap.etf_3d_cumulative_flow_status, "unavailable")

    def test_dossier_generation_and_formatting(self):
        config = DEFAULT_CONFIG
        store = StateStore()
        store.binance_spot_price = 77500.0
        store.binance_perp_price = 77480.0
        store.open_interest_btc = 95000.0
        store.funding_rate_pct = 0.0050

        # Seed synthetic daily bars
        now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        daily_bars = []
        for i in range(60):
            ts = now_ms - (60 - i) * 86400 * 1000
            price = 75000.0 + i * 50.0
            daily_bars.append(
                KlineBar(
                    timestamp_ms=ts,
                    open=price - 10.0,
                    high=price + 20.0,
                    low=price - 20.0,
                    close=price,
                    volume=1000.0,
                    taker_buy_volume=500.0,
                )
            )
        store.spot_klines_1d.extend(daily_bars)

        macro_snap = MacroIntermarketSnapshot(
            timestamp_utc="2026-10-31 04:00:00 UTC",
            brent_crude_price=112.50,
            brent_crude_range_5_10d="$105.00 - $115.00",
            us_10y_treasury_yield=4.92,
            dxy_index=102.10,
            sp500_price=7550.0,
            sp500_change_1d_pct=-1.5,
            vix_index=18.5,
            btc_spx_corr_20d=0.45,
            fear_and_greed_score=35,
            fear_and_greed_classification="Fear",
            btc_dominance_pct=59.1,
            orderbook_depth_ratio_1pct=1.25,
            orderbook_depth_ratio_2pct=1.28,
        )

        dossier = compute_protocol_metrics_dossier(config, store, macro_snap)
        self.assertIn("price_and_structure", dossier)
        self.assertIn("volume_profile", dossier)
        self.assertIn("derivatives_and_positioning", dossier)
        self.assertIn("flows_and_demand", dossier)
        self.assertIn("macro_and_intermarket", dossier)
        self.assertIn("sentiment_and_context", dossier)
        self.assertIn("mean_reversion_landscape", dossier)

        md = format_protocol_metrics_dossier_markdown(dossier)
        self.assertIn("## SECTION 12: CONSOLIDATED PROTOCOL METRICS DOSSIER", md)
        self.assertIn("### 12A. Core Price & Structure Metrics", md)
        self.assertIn("### 12B. Volume Profile Metrics", md)
        self.assertIn("### 12C. Derivatives & Positioning Metrics", md)
        self.assertIn("### 12D. ETF Flows & Demand Proxies", md)
        self.assertIn("### 12E. Macro & Intermarket Asset Metrics", md)
        self.assertIn("### 12F. Sentiment & Risk Context", md)
        self.assertIn("### 12G. Mean-Reversion Inputs", md)
        self.assertIn("$112.50", md)
        self.assertIn("35 / 100 (Fear)", md)
        self.assertIn("unavailable", md)

    def test_build_ai_telemetry_packet_includes_section_12(self):
        config = DEFAULT_CONFIG
        store = StateStore()
        store.binance_spot_price = 77000.0
        packet = build_ai_telemetry_packet(config, store)
        self.assertIn("## SECTION 12: CONSOLIDATED PROTOCOL METRICS DOSSIER", packet)
        self.assertIn("### 12A. Core Price & Structure Metrics", packet)


if __name__ == "__main__":
    unittest.main()
