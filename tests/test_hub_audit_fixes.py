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


if __name__ == "__main__":
    unittest.main()
