"""Regression tests for the data-hub audit findings (F1-F6).

Each test pins a defect that published a confident number the engine could not justify:

  F1  no open interest -> a fabricated $5,000M baseline ladder
  F2  tier names (10x-100x) on prices derived from swing multiples
  F5  a hardcoded band set (45M/85M/110M) reachable as a fallback
  F4  ATR(14) computed on a 25-bar window -> value moved +/-3% with the window
  F3  support/resistance defaulting to spot +/-5% and quoted as structure
"""
import unittest
from datetime import datetime, timezone

from analytics.btc_magnet_engine import BTCMagnetEngine
from analytics.data_hub_engine import _format_modeled_liq_ladder
from analytics.protocol_v13 import ProtocolV13Evaluator
from config.settings import DEFAULT_CONFIG
from core.models import BTCMagnetLevel, DerivativesSnapshot, FlowSnapshot, KlineBar
from core.state_store import StateStore


class TestLadderDoesNotFabricateOpenInterest(unittest.TestCase):
    SPOT = 61_950.0

    def _build(self, oi_btc, ls=1.2):
        store = StateStore()
        store.open_interest_btc = oi_btc
        engine = BTCMagnetEngine(DEFAULT_CONFIG)
        return engine._build_six_tier_ladder(
            spot_price=self.SPOT,
            swing_high_4h=self.SPOT * 1.03,
            swing_low_4h=self.SPOT * 0.97,
            upper=BTCMagnetLevel(price=self.SPOT * 1.01, dist_pct=1.0, usd_volume=5_000_000.0),
            lower=BTCMagnetLevel(price=self.SPOT * 0.99, dist_pct=-1.0, usd_volume=5_000_000.0),
            long_short_ratio=ls,
            store=store,
        )

    def test_no_open_interest_means_no_ladder(self):
        tiers = self._build(oi_btc=0.0)
        self.assertEqual([], tiers,
                         "a ladder was published from an assumed baseline with no OI")

    def test_tier_prices_follow_leverage_geometry(self):
        tiers = self._build(oi_btc=97_000.0)
        self.assertTrue(tiers, "ladder is empty with a measured OI")
        by_lev = {}
        for t in tiers:
            if t["side"] == "upper":
                by_lev[t["leverage"]] = t["price"]
        # 1/leverage: 100x ~1%, 25x ~4%, 10x ~10%. The nearest tier is published as the
        # merged "50-100x" band and represents the 100x distance.
        self.assertAlmostEqual(by_lev["50-100x"] / self.SPOT, 1.01, places=3)
        self.assertAlmostEqual(by_lev["25x"] / self.SPOT, 1.04, places=3)
        self.assertAlmostEqual(by_lev["10x"] / self.SPOT, 1.10, places=3)
        self.assertLess(by_lev["50-100x"], by_lev["25x"],
                        "the nearest tier must sit closer to spot than the 25x tier")
        self.assertLess(by_lev["25x"], by_lev["10x"])

    def test_band_volumes_scale_with_open_interest(self):
        small = {t["leverage"]: t["estimated_vol_m"] for t in self._build(oi_btc=50_000.0)}
        large = {t["leverage"]: t["estimated_vol_m"] for t in self._build(oi_btc=100_000.0)}
        self.assertGreater(large["25x"], small["25x"] * 1.5,
                           "volumes did not scale with OI, so they are not OI-derived")

    def test_tiers_record_whether_long_short_was_measured(self):
        measured = self._build(oi_btc=97_000.0, ls=1.2)[0]
        assumed = self._build(oi_btc=97_000.0, ls=0.0)[0]
        self.assertEqual("MEASURED", measured.get("ls_source"))
        self.assertEqual("ASSUMED_1.0", assumed.get("ls_source"))

    def test_crowding_weight_is_not_a_constant(self):
        def _eval_with_ls(**attrs):
            store = StateStore()
            store.binance_spot_price = self.SPOT
            store.open_interest_btc = 97_000.0
            for k, v in attrs.items():
                setattr(store, k, v)
            engine = BTCMagnetEngine(DEFAULT_CONFIG)
            engine._last_fetch_ts = 1e12
            engine._cached_liq_data = {
                "levels": {
                    "above": [{"price": self.SPOT * 1.01, "dist_pct": 1.0, "usd": 5_000_000.0}],
                    "below": [{"price": self.SPOT * 0.99, "dist_pct": -1.0, "usd": 5_000_000.0}],
                }
            }
            return engine.evaluate(store)

        # Unmeasured defaults must NOT be dressed as MEASURED and must publish raw OI shares
        ev_unmeasured = _eval_with_ls()
        tiers_unm = ev_unmeasured.levels_ladder["tiers_6"]
        self.assertEqual("ASSUMED_1.0", tiers_unm[0]["ls_source"])
        self.assertFalse(tiers_unm[0]["split_measured"])
        self.assertIn("not measured", tiers_unm[0]["ls_observable"].lower())
        oi_m = (97_000.0 * self.SPOT) / 1e6
        u25_unm = next(t["estimated_vol_m"] for t in tiers_unm if t["tier"] == "25x Shorts")
        l25_unm = next(t["estimated_vol_m"] for t in tiers_unm if t["tier"] == "25x Longs")
        self.assertAlmostEqual(u25_unm, round(oi_m * 0.032, 1), places=1)
        self.assertAlmostEqual(l25_unm, round(oi_m * 0.040, 1), places=1)

        # Observable taker / top-trader / global L/S must actively move band volumes
        ev_low_ls = _eval_with_ls(taker_long_short_ratio_5m=0.60, perp_5m_delta_btc=-50.0)
        ev_high_ls = _eval_with_ls(taker_long_short_ratio_5m=2.50, perp_5m_delta_btc=50.0)
        tiers_low = ev_low_ls.levels_ladder["tiers_6"]
        tiers_high = ev_high_ls.levels_ladder["tiers_6"]
        self.assertEqual("MEASURED", tiers_low[0]["ls_source"])
        self.assertTrue(tiers_low[0]["split_measured"])
        self.assertEqual("taker_long_short_ratio_5m", tiers_low[0]["ls_observable"])
        l25_low = next(t["estimated_vol_m"] for t in tiers_low if t["tier"] == "25x Longs")
        l25_high = next(t["estimated_vol_m"] for t in tiers_high if t["tier"] == "25x Longs")
        u25_low = next(t["estimated_vol_m"] for t in tiers_low if t["tier"] == "25x Shorts")
        u25_high = next(t["estimated_vol_m"] for t in tiers_high if t["tier"] == "25x Shorts")
        self.assertGreater(l25_high, l25_low)
        self.assertGreater(u25_low, u25_high)


class TestFormatterRefusesHardcodedBands(unittest.TestCase):
    def test_bands_only_object_yields_no_ladder(self):
        class _Mag:
            levels_ladder = {"bands": {"100x_short": {"price": 62_446.0, "usd": 4_200_000.0}}}
        self.assertIsNone(_format_modeled_liq_ladder(_Mag()),
                          "the hardcoded band fallback still formats a ladder")


class TestProtocolSignalsAssumedStructure(unittest.TestCase):
    """F3/F4: empty window and short ATR history must be visible, not silent."""

    def _evaluate(self, n_1d_bars: int):
        store = StateStore()
        now = int(datetime.now(timezone.utc).timestamp() * 1000)
        for d in range(n_1d_bars):
            store.spot_klines_1d.append(KlineBar(
                timestamp_ms=now - (n_1d_bars - d) * 86_400_000,
                open=61_000.0, high=62_500.0, low=60_500.0, close=61_950.0,
                volume=1_000.0, taker_buy_volume=500.0))
        bars = [KlineBar(timestamp_ms=now - (240 - i) * 3_600_000, open=61_950.0,
                         high=62_100.0, low=61_800.0, close=61_950.0,
                         volume=10.0, taker_buy_volume=5.0) for i in range(240)]
        store.spot_klines_1h.extend(bars)
        store.spot_klines_15m.extend(bars[-80:])
        store.binance_spot_price = 61_950.0
        store.binance_perp_price = 61_900.0
        return ProtocolV13Evaluator(DEFAULT_CONFIG).evaluate(
            store, FlowSnapshot(), DerivativesSnapshot())

    def test_empty_window_is_labelled_assumed(self):
        ev = self._evaluate(0)
        self.assertEqual("ASSUMED_5PCT", getattr(ev, "structure_source", None),
                         "support/resistance invented at +/-5% were not labelled")

    def test_measured_window_is_labelled_measured(self):
        ev = self._evaluate(30)
        self.assertEqual("MEASURED_14D", getattr(ev, "structure_source", None))


class TestAtrUsesFullHistory(unittest.TestCase):
    def test_atr_window_is_not_the_old_25_bars(self):
        src = (__import__("pathlib").Path(__file__).resolve().parents[1]
               / "analytics" / "protocol_v13.py").read_text(encoding="utf-8")
        self.assertNotIn("[-25:]", src,
                         "ATR is seeded on a 25-bar window again, so its value moves with the window")
        self.assertIn("[-250:]", src)


class TestRequirement3SweepFixes(unittest.TestCase):
    """Regression tests for provable Requirement 2 audit findings fixed in Requirement 3."""

    def test_hilbert_recovers_cycle_period_on_sinusoid(self):
        import numpy as np
        import pandas as pd
        from analytics.mm_btc_engine import MMBTCEngine

        n = 160
        t = np.arange(n, dtype=float)
        # 20-bar cycle around $65,000 BTC spot; un-detrended in_phase pinned this to 72
        wave = 65_000.0 + 1_000.0 * np.sin(2.0 * np.pi * t / 20.0) + t * 5.0
        df = pd.DataFrame({
            "open": wave,
            "high": wave + 50.0,
            "low": wave - 50.0,
            "close": wave,
            "volume": np.full(n, 500.0),
            "taker_buy_volume": np.full(n, 260.0),
            "open_interest": np.full(n, 95_000.0),
        })
        res = MMBTCEngine(DEFAULT_CONFIG).evaluate_hilbert(df, median_window=12)
        self.assertLessEqual(abs(res.dominant_cycle - 20), 2,
                             f"Hilbert cycle saturated/drifted ({res.dominant_cycle}) instead of ~20")

    def test_rough_path_cvd_normalization_not_attenuated_by_window(self):
        import numpy as np
        import pandas as pd
        from analytics.mm_btc_engine import MMBTCEngine

        n = 64
        t = np.arange(n, dtype=float)
        # Flow leads price by quarter cycle -> signed Levy area A(P,V) should be non-trivial (~O(1))
        price = 65_000.0 + 600.0 * np.sin(2.0 * np.pi * t / 16.0 - np.pi / 2.0)
        flow_sig = 300.0 + 100.0 * np.cos(2.0 * np.pi * t / 16.0)
        df = pd.DataFrame({
            "open": price,
            "high": price + 80.0,
            "low": price - 80.0,
            "close": price,
            "volume": np.full(n, 1_000.0),
            "taker_buy_volume": flow_sig,
            "open_interest": np.full(n, 95_000.0),
        })
        sig = MMBTCEngine(DEFAULT_CONFIG).evaluate_path_signature(df, window=48)
        self.assertGreater(abs(sig.area_price_flow), 0.1,
                           f"area_price_flow={sig.area_price_flow} appears attenuated by window division")

    def test_five_day_macro_changes_use_five_trading_days(self):
        import asyncio
        from unittest.mock import AsyncMock, patch
        from collectors.macro_collector import fetch_macro_and_intermarket_snapshot

        # 7 daily closes: indices 0..6 -> 5 trading days ago from index 6 is index 1 (value 102.0), NOT index 2 (103.0)
        closes_7 = [100.0, 102.0, 103.0, 104.0, 105.0, 106.0, 108.0]
        fake_yahoo = {
            "dxy": {"price": 108.0, "closes": closes_7, "highs": closes_7, "lows": closes_7, "cv_pairs": []},
            "tnx": {"price": 4.80, "closes": [4.10, 4.20, 4.30, 4.40, 4.50, 4.60, 4.80], "highs": [], "lows": [], "cv_pairs": []},
            "spx": {"price": 7200.0, "closes": [7000.0, 7000.0, 7100.0, 7120.0, 7150.0, 7180.0, 7200.0], "highs": [], "lows": [], "cv_pairs": []},
            "nasdaq": {"price": 24000.0, "closes": [20000.0, 20000.0, 21000.0, 22000.0, 23000.0, 23500.0, 24000.0], "highs": [], "lows": [], "cv_pairs": []},
            "vix": {"price": 25.0, "closes": [18.0, 20.0, 21.0, 22.0, 23.0, 24.0, 25.0], "highs": [], "lows": [], "cv_pairs": []},
        }

        async def _run():
            with (
                patch("collectors.macro_collector._fetch_yahoo_quotes", new=AsyncMock(return_value=fake_yahoo)),
                patch("collectors.macro_collector._fetch_alternative_me_fng", new=AsyncMock(return_value=(None, None))),
                patch("collectors.macro_collector._fetch_coingecko_dominance", new=AsyncMock(return_value=None)),
                patch("collectors.macro_collector._fetch_binance_depth_ratios", new=AsyncMock(return_value=(None, None, None))),
                patch("collectors.macro_collector._fetch_fred_series", new=AsyncMock(return_value=None)),
                patch("collectors.macro_collector._fetch_treasury_real_yield_10y", new=AsyncMock(return_value=None)),
                patch("collectors.macro_collector._fetch_farside_etf_flows_sync", return_value=None),
                patch("collectors.macro_collector._fetch_coinmetrics_onchain", new=AsyncMock(return_value={})),
                patch("collectors.macro_collector._fetch_defillama_stablecoins", new=AsyncMock(return_value={})),
                patch("collectors.macro_collector._fetch_deribit_options_summary", new=AsyncMock(return_value={})),
                patch("collectors.macro_collector._fetch_cross_exchange_perps_and_cb_vol", new=AsyncMock(return_value={})),
                patch("collectors.macro_collector._fetch_nyfed_liquidity", new=AsyncMock(return_value={})),
                patch("collectors.macro_collector._fetch_hyperliquid_perp", new=AsyncMock(return_value=None)),
                patch("collectors.macro_collector._fetch_usd_macro_calendar", new=AsyncMock(return_value=(False, []))),
            ):
                return await fetch_macro_and_intermarket_snapshot(None, [])

        snap = asyncio.run(_run())
        self.assertIn("+6.00 over 5d", snap.dxy_direction_5_10d)
        self.assertAlmostEqual(snap.us_10y_yield_change_5d, 0.60, places=3)
        self.assertAlmostEqual(snap.vix_change_5d, 5.0, places=2)
        self.assertAlmostEqual(snap.sp500_change_5d_pct, round((7200.0 - 7000.0) / 7000.0 * 100.0, 2), places=2)
        self.assertAlmostEqual(snap.nasdaq_change_5d_pct, 20.0, places=2)

    def test_farside_dash_is_not_treated_as_zero_flow(self):
        from collectors.macro_collector import _parse_farside_total_m

        self.assertIsNone(_parse_farside_total_m("-"))
        self.assertIsNone(_parse_farside_total_m(""))
        self.assertEqual(_parse_farside_total_m("0.0"), 0.0)
        self.assertEqual(_parse_farside_total_m("(123.4)"), -123.4)

    def test_sqlite_archive_includes_all_71_metrics_and_matches_live_counts(self):
        import json
        import sqlite3
        import tempfile
        from pathlib import Path
        from analytics.data_hub_engine import DataHubEngine
        from core.models import FourGateEvaluation

        store = StateStore()
        store.binance_spot_price = 62_000.0
        store.four_gate_evaluation = FourGateEvaluation(last_closed_bar_utc="2026-11-20 08:00:00 UTC")
        with tempfile.TemporaryDirectory() as tmp:
            db_file = Path(tmp) / "hub.sqlite"
            ev = DataHubEngine(DEFAULT_CONFIG, db_path=db_file, write_archive=True).evaluate(store)
            conn = sqlite3.connect(str(db_file))
            try:
                ok_db, un_db, pj_raw = conn.execute(
                    "SELECT ok_count, unavailable_count, payload_json FROM telemetry_snapshots"
                ).fetchone()
            finally:
                conn.close()
            pj = json.loads(pj_raw)
            archived_total = sum(len(rows) for rows in pj["panels"].values())
            self.assertEqual(ev.total_metrics, 71)
            self.assertEqual(archived_total, ev.total_metrics)
            self.assertEqual(ok_db, ev.ok_count)
            self.assertEqual(un_db, ev.unavailable_count)


if __name__ == "__main__":
    unittest.main()
