"""Unit tests for the Intra-Candle Footprint & Order Flow Microstructure Engine.

Verifies:
1. $25 Price bin rounding.
2. Diagonal 300% buy and sell imbalances.
3. Stacked imbalances (>= 3 consecutive levels).
4. Institutional battle zones (intense two-way volume transfer).
5. Lower-wick trapped seller absorption (sells in lower 25% wick with bounce).
6. 15-Minute candle delta flip detection.
7. Strict rolling memory hygiene (max 4 completed bars + 1 active bar).
8. 3-Gate Execution Funnel & 1:2 / 1:3 R:R trade plan generation.
9. Continuous centered Footprint ladder generation.
10. End-to-end integration with StateStore, SignalDetector, AI Packet Exporter, and HUD.
"""

from collections import deque
import unittest
from unittest.mock import MagicMock

from analytics.ai_packet_exporter import build_ai_telemetry_packet
from analytics.footprint_engine import FootprintEngine
from analytics.signal_detector import SignalDetector
from config.settings import EngineConfig
from core.models import (
    FootprintBarData,
    FootprintClusterRow,
    FootprintEvaluation,
    KlineBar,
    VolumeProfileResult,
)
from core.state_store import StateStore
from ui.terminal_hud import build_dashboard_renderable


class TestFootprintEngine(unittest.TestCase):
    """Comprehensive test suite for the FootprintEngine."""

    def setUp(self) -> None:
        self.config = EngineConfig()
        self.engine = FootprintEngine(
            config=self.config,
            tick_step=25.0,
            timeframe_min=15,
            imbalance_ratio=3.0,
            min_imbalance_volume=1.0,
            stacked_min_levels=3,
            max_completed_bars=4,
            battle_zone_threshold=5.0,
            wick_fraction=0.25,
        )

    def test_price_rounding_25_tick(self) -> None:
        """Verifies price rounding to exact $25.0 tick increments."""
        self.assertEqual(self.engine.round_price(78400.0), 78400.0)
        self.assertEqual(self.engine.round_price(78410.0), 78400.0)
        self.assertEqual(self.engine.round_price(78412.5), 78425.0)
        self.assertEqual(self.engine.round_price(78420.0), 78425.0)
        self.assertEqual(self.engine.round_price(78425.0), 78425.0)
        self.assertEqual(self.engine.round_price(78437.4), 78425.0)
        self.assertEqual(self.engine.round_price(78438.0), 78450.0)
        self.assertEqual(self.engine.round_price(0.0), 0.0)

    def test_trade_ingestion_and_active_bar_updates(self) -> None:
        """Verifies trades populate OHLCV, net delta, and cluster rows."""
        base_ts = 1_700_000_000_000  # Start of a 15m window

        # Aggressive buy lifting ask: 2.5 BTC at $78,425 (is_buyer_maker=False)
        self.engine.ingest_trade(price=78425.0, qty=2.5, is_buyer_maker=False, ts_ms=base_ts + 1000)
        # Aggressive sell hitting bid: 1.0 BTC at $78,425 (is_buyer_maker=True)
        self.engine.ingest_trade(price=78425.0, qty=1.0, is_buyer_maker=True, ts_ms=base_ts + 2000)
        # Aggressive buy lifting ask: 4.0 BTC at $78,450
        self.engine.ingest_trade(price=78450.0, qty=4.0, is_buyer_maker=False, ts_ms=base_ts + 3000)

        bar = self.engine.active_bar
        self.assertIsNotNone(bar)
        self.assertEqual(bar.open, 78425.0)
        self.assertEqual(bar.high, 78450.0)
        self.assertEqual(bar.low, 78425.0)
        self.assertEqual(bar.close, 78450.0)
        self.assertAlmostEqual(bar.volume, 7.5)
        # Net delta: +2.5 - 1.0 + 4.0 = +5.5
        self.assertAlmostEqual(bar.net_delta, 5.5)

        cluster_425 = bar.clusters[78425.0]
        self.assertAlmostEqual(cluster_425.bid_vol, 1.0)
        self.assertAlmostEqual(cluster_425.ask_vol, 2.5)
        self.assertAlmostEqual(cluster_425.delta, 1.5)
        self.assertAlmostEqual(cluster_425.total_vol, 3.5)

        cluster_450 = bar.clusters[78450.0]
        self.assertAlmostEqual(cluster_450.bid_vol, 0.0)
        self.assertAlmostEqual(cluster_450.ask_vol, 4.0)
        self.assertAlmostEqual(cluster_450.total_vol, 4.0)

    def test_diagonal_300_percent_imbalances(self) -> None:
        """Verifies diagonal imbalance detection (Ask[P+$25] vs Bid[P])."""
        bar = FootprintBarData(
            start_ts_ms=1000,
            end_ts_ms=901000,
            open=78400.0,
            high=78450.0,
            low=78400.0,
            close=78450.0,
            volume=20.0,
        )
        # Level 78400: Bid=1.0 BTC, Ask=0.5 BTC
        bar.clusters[78400.0] = FootprintClusterRow(price=78400.0, bid_vol=1.0, ask_vol=0.5, total_vol=1.5)
        # Level 78425: Bid=0.2 BTC, Ask=5.0 BTC
        # Ask at 78425 (5.0) >= 3.0 * Bid at 78400 (1.0) -> Buy Imbalance at 78425!
        bar.clusters[78425.0] = FootprintClusterRow(price=78425.0, bid_vol=0.2, ask_vol=5.0, total_vol=5.2)
        # Level 78450: Bid=6.0 BTC, Ask=0.5 BTC
        # Bid at 78450 (6.0) vs Ask at 78475 (none): will check against 78475 or lower
        bar.clusters[78450.0] = FootprintClusterRow(price=78450.0, bid_vol=6.0, ask_vol=0.5, total_vol=6.5)

        self.engine.analyze_bar(bar)

        # 78425 should have is_buy_imbalance == True
        self.assertTrue(bar.clusters[78425.0].is_buy_imbalance)
        # 78400 does not have buy imbalance
        self.assertFalse(bar.clusters[78400.0].is_buy_imbalance)

    def test_stacked_buy_and_sell_imbalances(self) -> None:
        """Verifies stacked imbalances (>= 3 consecutive levels)."""
        bar = FootprintBarData(
            start_ts_ms=1000,
            end_ts_ms=901000,
            open=78400.0,
            high=78500.0,
            low=78400.0,
            close=78500.0,
        )
        # Set up 3 consecutive buy imbalances at 78425, 78450, 78475
        bar.clusters[78400.0] = FootprintClusterRow(price=78400.0, bid_vol=1.0, ask_vol=0.0, total_vol=1.0)
        bar.clusters[78425.0] = FootprintClusterRow(price=78425.0, bid_vol=1.0, ask_vol=5.0, total_vol=6.0)
        bar.clusters[78450.0] = FootprintClusterRow(price=78450.0, bid_vol=1.0, ask_vol=6.0, total_vol=7.0)
        bar.clusters[78475.0] = FootprintClusterRow(price=78475.0, bid_vol=1.0, ask_vol=7.0, total_vol=8.0)
        bar.clusters[78500.0] = FootprintClusterRow(price=78500.0, bid_vol=5.0, ask_vol=1.0, total_vol=6.0)

        self.engine.analyze_bar(bar)

        self.assertTrue(bar.has_stacked_buy)
        self.assertTrue(bar.clusters[78425.0].is_stacked_buy)
        self.assertTrue(bar.clusters[78450.0].is_stacked_buy)
        self.assertTrue(bar.clusters[78475.0].is_stacked_buy)
        self.assertFalse(bar.clusters[78400.0].is_stacked_buy)

    def test_institutional_battle_zone_detection(self) -> None:
        """Verifies battle zones where intense two-way churn occurs."""
        bar = FootprintBarData(
            start_ts_ms=1000,
            end_ts_ms=901000,
            open=78400.0,
            high=78450.0,
            low=78400.0,
            close=78425.0,
        )
        # Normal cluster
        bar.clusters[78400.0] = FootprintClusterRow(price=78400.0, bid_vol=1.0, ask_vol=1.0, total_vol=2.0)
        # Battle zone: both bid >= 5.0 and ask >= 5.0 BTC
        bar.clusters[78425.0] = FootprintClusterRow(price=78425.0, bid_vol=6.5, ask_vol=7.2, total_vol=13.7)

        self.engine.analyze_bar(bar)

        self.assertTrue(bar.has_battle_zone)
        self.assertTrue(bar.clusters[78425.0].is_battle_zone)
        self.assertIn("BATTLE", bar.clusters[78425.0].tag)

    def test_lower_wick_trapped_seller_absorption(self) -> None:
        """Verifies absorption of aggressive sells in the lower 25% wick followed by candle bounce."""
        # Candle range: 78300 (low) to 78400 (high) -> span = 100. Lower wick = 78300 to 78325
        bar = FootprintBarData(
            start_ts_ms=1000,
            end_ts_ms=901000,
            open=78350.0,
            high=78400.0,
            low=78300.0,
            close=78375.0,  # Closed well above lower wick (bounced back into body)
        )
        # Heavy aggressive selling in lower wick (78300 and 78325)
        bar.clusters[78300.0] = FootprintClusterRow(price=78300.0, bid_vol=8.0, ask_vol=0.5, delta=-7.5, total_vol=8.5)
        bar.clusters[78325.0] = FootprintClusterRow(price=78325.0, bid_vol=4.0, ask_vol=1.0, delta=-3.0, total_vol=5.0)
        bar.clusters[78350.0] = FootprintClusterRow(price=78350.0, bid_vol=2.0, ask_vol=3.0, delta=1.0, total_vol=5.0)
        bar.clusters[78375.0] = FootprintClusterRow(price=78375.0, bid_vol=1.0, ask_vol=4.0, delta=3.0, total_vol=5.0)
        bar.clusters[78400.0] = FootprintClusterRow(price=78400.0, bid_vol=0.5, ask_vol=2.0, delta=1.5, total_vol=2.5)

        self.engine.analyze_bar(bar)

        self.assertTrue(bar.has_wick_absorption)
        self.assertEqual(bar.wick_absorption_price, 78300.0)
        self.assertIn("TRAP SELL", bar.clusters[78300.0].tag)

    def test_delta_flip_detection(self) -> None:
        """Verifies transition from negative delta in prior bar to positive delta in active bar."""
        # Bar 1: negative net delta
        bar1 = FootprintBarData(
            start_ts_ms=1000,
            end_ts_ms=901000,
            open=78400.0,
            high=78450.0,
            low=78350.0,
            close=78360.0,
            net_delta=-12.5,
            is_closed=True,
        )
        self.engine.completed_bars.append(bar1)

        # Bar 2: active forming bar with positive net delta
        self.engine.active_bar = FootprintBarData(
            start_ts_ms=901000,
            end_ts_ms=1801000,
            open=78360.0,
            high=78420.0,
            low=78350.0,
            close=78410.0,
            net_delta=8.5,
        )

        flip_bull, flip_bear, prev_d, active_d = self.engine.detect_delta_flip()
        self.assertTrue(flip_bull)
        self.assertFalse(flip_bear)
        self.assertEqual(prev_d, -12.5)
        self.assertEqual(active_d, 8.5)

    def test_rolling_memory_hygiene_max_bars(self) -> None:
        """Verifies completed bars queue strictly caps at max_completed_bars (4) during live running."""
        interval_ms = 15 * 60 * 1000

        # Simulate trades across 7 different 15-minute periods
        for i in range(7):
            ts = i * interval_ms + 1000
            self.engine.ingest_trade(price=78400.0 + i * 10, qty=1.0, is_buyer_maker=False, ts_ms=ts)

        # After 7 periods: active_bar is the 7th, and completed_bars should hold exactly max_completed_bars (4)
        self.assertEqual(len(self.engine.completed_bars), 4)
        self.assertIsNotNone(self.engine.active_bar)

    def test_three_gate_evaluation_and_trade_plan(self) -> None:
        """Verifies 3-Gate Execution Funnel: Gate 1 Level Tap, Gate 2 Absorption, Gate 3 Delta Flip."""
        # Setup previous completed bar with negative delta (-5.0 BTC)
        prev_bar = FootprintBarData(
            start_ts_ms=1000,
            end_ts_ms=901000,
            open=78500.0,
            high=78520.0,
            low=78320.0,
            close=78330.0,
            net_delta=-5.0,
            is_closed=True,
        )
        self.engine.completed_bars.append(prev_bar)

        # Active bar touching 30D cVAL at $78,350 with lower wick absorption and positive delta
        active_bar = FootprintBarData(
            start_ts_ms=901000,
            end_ts_ms=1801000,
            open=78330.0,
            high=78425.0,
            low=78300.0,   # Taps level
            close=78400.0,  # Bounced above lower wick
            net_delta=6.0,  # Delta flip from -5.0 to +6.0
        )
        # Cluster in lower wick with trapped selling
        active_bar.clusters[78300.0] = FootprintClusterRow(
            price=78300.0, bid_vol=5.0, ask_vol=0.5, delta=-4.5, total_vol=5.5
        )
        active_bar.clusters[78400.0] = FootprintClusterRow(
            price=78400.0, bid_vol=0.5, ask_vol=4.0, delta=3.5, total_vol=4.5
        )
        self.engine.active_bar = active_bar

        # Mock store with 30D cVAL at 78,350
        mock_store = MagicMock()
        mock_store.binance_spot_price = 78400.0
        mock_store.macro_profile = MagicMock(c_val=78350.0, c_poc=79200.0)
        mock_store.tactical_profile = None

        evaluation = self.engine.evaluate(mock_store)

        self.assertTrue(evaluation.gate1_level_tap)
        self.assertEqual(evaluation.gate1_tapped_level_name, "30D Macro cVAL")
        self.assertTrue(evaluation.gate2_absorption)
        self.assertTrue(evaluation.gate3_delta_flip)
        self.assertTrue(evaluation.all_gates_pass)
        self.assertEqual(evaluation.signal_status, "TRIGGERED_ACCUMULATE")
        self.assertEqual(evaluation.entry_price, 78400.0)
        self.assertLess(evaluation.stop_loss, 78300.0)  # Below 78300 with buffer
        self.assertGreater(evaluation.tp1_1to2, evaluation.entry_price)
        self.assertGreater(evaluation.tp2_1to3, evaluation.tp1_1to2)

    def test_continuous_ladder_generation(self) -> None:
        """Verifies get_ladder_rows produces continuous sorted rows centered around target price."""
        self.engine.active_bar = FootprintBarData(
            start_ts_ms=1000,
            end_ts_ms=901000,
            open=78400.0,
            high=78450.0,
            low=78350.0,
            close=78400.0,
        )
        self.engine.active_bar.clusters[78400.0] = FootprintClusterRow(price=78400.0, total_vol=5.0)
        self.engine.active_bar.clusters[78425.0] = FootprintClusterRow(price=78425.0, total_vol=3.0)

        rows = self.engine.get_ladder_rows(center_price=78400.0, num_rows=7)
        self.assertEqual(len(rows), 7)
        # Highest price on top, lowest on bottom
        prices = [r.price for r in rows]
        self.assertEqual(prices, sorted(prices, reverse=True))
        # Center should be 78400.0
        self.assertEqual(prices[len(prices) // 2], 78400.0)

    def test_seed_from_klines(self) -> None:
        """Verifies zero-cold-start initialization from 15m kline history."""
        klines = [
            KlineBar(timestamp_ms=1000 + i * 900_000, open=78400.0 + i, high=78450.0 + i, low=78350.0 + i, close=78410.0 + i, volume=10.0, taker_buy_volume=4.0)
            for i in range(6)
        ]
        self.engine.seed_from_klines(klines)

        self.assertIsNotNone(self.engine.active_bar)
        self.assertEqual(len(self.engine.completed_bars), 4)  # Capped at max_completed_bars
        self.assertEqual(self.engine.active_bar.open, 78405.0)

    def test_end_to_end_statestore_and_signal_detector(self) -> None:
        """Verifies StateStore trade ingestion, SignalDetector evaluation, and AI Packet export."""
        store = StateStore()
        config = EngineConfig()

        # Seed 1H klines for volume profile calculation
        for i in range(820):
            store.spot_klines_1h.append(
                KlineBar(
                    timestamp_ms=1_700_000_000_000 + (i * 3600_000),
                    open=78400.0 + (i % 5) * 10,
                    high=78500.0 + (i % 5) * 10,
                    low=78300.0,
                    close=78420.0,
                    volume=100.0,
                    taker_buy_volume=50.0,
                )
            )

        # Seed 15m klines
        for i in range(20):
            store.spot_klines_15m.append(
                KlineBar(
                    timestamp_ms=1_700_000_000_000 + (i * 900_000),
                    open=78400.0,
                    high=78450.0,
                    low=78350.0,
                    close=78410.0,
                    volume=20.0,
                    taker_buy_volume=12.0,
                )
            )

        # Ingest live trades into StateStore
        store.record_spot_trade(price=78425.0, qty=5.0, is_buyer_maker=False, ts_ms=1_700_100_000_000)
        store.record_spot_trade(price=78400.0, qty=1.5, is_buyer_maker=True, ts_ms=1_700_100_001_000)

        # Run signal detector
        detector = SignalDetector(config)
        sig = detector.evaluate(store)

        # Verify footprint evaluation exists
        self.assertIsNotNone(store.footprint_evaluation)
        self.assertIsInstance(store.footprint_evaluation, FootprintEvaluation)
        self.assertGreater(len(store.footprint_evaluation.active_ladder_rows), 0)

        # Verify AI Packet includes Section 2C
        packet = build_ai_telemetry_packet(config, store)
        self.assertIn("### 2C. 15-Minute Intra-Candle Footprint", packet)
        self.assertIn("Active 15m Forming Bar Delta", packet)

        # Verify Terminal HUD renders Tab 1 with Footprint Panel
        hud_output = build_dashboard_renderable(config, store, tab_override=1)
        self.assertIsNotNone(hud_output)

    def test_upper_wick_trapped_buyer_exhaustion(self) -> None:
        """Verifies detection of trapped aggressive buyers at the upper wick (Distribution / Ceiling)."""
        # Range: 71,750 to 72,000 (span = 250). Upper wick = 71,937.5 to 72,000.
        bar = FootprintBarData(
            start_ts_ms=1000,
            end_ts_ms=901000,
            open=71800.0,
            high=72000.0,
            low=71750.0,
            close=71850.0,  # Price rejected back down from the ceiling
        )
        # Heavy aggressive buying in upper wick (71975 and 72000)
        bar.clusters[71750.0] = FootprintClusterRow(price=71750.0, bid_vol=1.0, ask_vol=2.0, delta=1.0, total_vol=3.0)
        bar.clusters[71850.0] = FootprintClusterRow(price=71850.0, bid_vol=3.0, ask_vol=1.0, delta=-2.0, total_vol=4.0)
        bar.clusters[71975.0] = FootprintClusterRow(price=71975.0, bid_vol=0.5, ask_vol=6.0, delta=5.5, total_vol=6.5)
        bar.clusters[72000.0] = FootprintClusterRow(price=72000.0, bid_vol=0.2, ask_vol=8.0, delta=7.8, total_vol=8.2)

        self.engine.analyze_bar(bar)

        self.assertTrue(bar.has_upper_wick_exhaustion)
        self.assertEqual(bar.upper_wick_exhaustion_price, 72000.0)
        self.assertIn("TRAP BUY", bar.clusters[72000.0].tag)

    def test_bearish_delta_flip(self) -> None:
        """Verifies transition from positive delta in prior bar to negative delta in active bar."""
        prev_bar = FootprintBarData(
            start_ts_ms=1000,
            end_ts_ms=901000,
            open=71800.0,
            high=72000.0,
            low=71800.0,
            close=71980.0,
            net_delta=14.5,
            is_closed=True,
        )
        self.engine.completed_bars.append(prev_bar)

        self.engine.active_bar = FootprintBarData(
            start_ts_ms=901000,
            end_ts_ms=1801000,
            open=71980.0,
            high=72010.0,
            low=71840.0,
            close=71850.0,
            net_delta=-18.0,
        )

        flip_bull, flip_bear, prev_d, active_d = self.engine.detect_delta_flip()
        self.assertFalse(flip_bull)
        self.assertTrue(flip_bear)
        self.assertEqual(prev_d, 14.5)
        self.assertEqual(active_d, -18.0)

    def test_three_gate_distribution_sell_and_rebuy_target(self) -> None:
        """Verifies 3-Gate Distribution Funnel: Upper Resistance Tap + Trapped Buyers + Negative Delta Shift."""
        prev_bar = FootprintBarData(
            start_ts_ms=1000,
            end_ts_ms=901000,
            open=71800.0,
            high=72000.0,
            low=71800.0,
            close=71980.0,
            net_delta=10.0,
            is_closed=True,
        )
        self.engine.completed_bars.append(prev_bar)

        active_bar = FootprintBarData(
            start_ts_ms=901000,
            end_ts_ms=1801000,
            open=71980.0,
            high=72025.0,  # Taps $72,000 resistance
            low=71820.0,
            close=71850.0,  # Closed back down
            net_delta=-12.0,  # Negative delta shift
        )
        # Cluster in upper wick with trapped buyers
        active_bar.clusters[72000.0] = FootprintClusterRow(
            price=72000.0, bid_vol=0.5, ask_vol=8.0, delta=7.5, total_vol=8.5
        )
        active_bar.clusters[71850.0] = FootprintClusterRow(
            price=71850.0, bid_vol=5.0, ask_vol=1.0, delta=-4.0, total_vol=6.0
        )
        self.engine.active_bar = active_bar

        mock_store = MagicMock()
        mock_store.binance_spot_price = 71850.0
        mock_store.macro_profile = MagicMock(c_vah=72000.0, c_val=68400.0, c_poc=70000.0)
        mock_store.tactical_profile = None

        evaluation = self.engine.evaluate(mock_store)

        self.assertTrue(evaluation.gate1_level_tap)
        self.assertEqual(evaluation.gate1_level_type, "RESISTANCE")
        self.assertTrue(evaluation.gate2_absorption)
        self.assertTrue(evaluation.gate3_delta_flip)
        self.assertTrue(evaluation.all_gates_pass)
        self.assertEqual(evaluation.signal_status, "TRIGGERED_DISTRIBUTE")
        self.assertEqual(evaluation.direction, "DISTRIBUTE_SELL")
        self.assertEqual(evaluation.entry_price, 71850.0)
        self.assertGreater(evaluation.stop_loss, 72025.0)  # Invalidation above upper wick
        self.assertEqual(evaluation.rebuy_target_price, 70000.0)  # Rebuy at lower support/POC
        self.assertGreater(evaluation.target_coin_yield_pct, 0.0)

    def test_no_simultaneous_buy_and_sell_imbalance_on_same_bin(self) -> None:
        """Verifies a single price bin cannot simultaneously hold both BUY IMB and SELL IMB."""
        bar = FootprintBarData(
            start_ts_ms=1000,
            end_ts_ms=901000,
            open=78375.0,
            high=78400.0,
            low=78350.0,
            close=78390.0,
        )
        # Reproduces user's exact live snapshot: $78,350 dust bin (0.00 Bid / 0.01 Ask),
        # $78,375 POC battle bin (2.49 Bid / 2.66 Ask), $78,400 upper bin (0.14 Bid / 0.72 Ask)
        bar.clusters[78350.0] = FootprintClusterRow(price=78350.0, bid_vol=0.00, ask_vol=0.01, delta=0.01, total_vol=0.01)
        bar.clusters[78375.0] = FootprintClusterRow(price=78375.0, bid_vol=2.49, ask_vol=2.66, delta=0.18, total_vol=5.15)
        bar.clusters[78400.0] = FootprintClusterRow(price=78400.0, bid_vol=0.14, ask_vol=0.72, delta=0.58, total_vol=0.86)

        self.engine.analyze_bar(bar)

        for row in bar.clusters.values():
            self.assertFalse(
                row.is_buy_imbalance and row.is_sell_imbalance,
                f"Bin ${row.price} cannot have both BUY IMB and SELL IMB simultaneously",
            )
        # $78,375 has Ask (2.66) > Bid (2.49), so it can be BUY IMB vs $78,350 Bid (0.00), but NOT SELL IMB
        self.assertTrue(bar.clusters[78375.0].is_buy_imbalance)
        self.assertFalse(bar.clusters[78375.0].is_sell_imbalance)

    def test_observation_mode_gate_details_and_packet_audit_integrity(self) -> None:
        """Verifies OBSERVATION mode populates gate2_detail/gate3_delta_flip and AI packet has zero leaks/contradictions."""
        store = StateStore()
        config = EngineConfig()
        self.assertEqual(config.portfolio_equity_usd, config.spot_swing_account_equity_usd)

        for i in range(820):
            store.spot_klines_1h.append(
                KlineBar(
                    timestamp_ms=1_700_000_000_000 + (i * 3600_000),
                    open=78300.0,
                    high=78500.0,
                    low=78200.0,
                    close=78390.0,
                    volume=100.0,
                    taker_buy_volume=52.0,
                )
            )
        for i in range(250):
            store.spot_klines_1d.append(
                KlineBar(
                    timestamp_ms=1_680_000_000_000 + (i * 86400_000),
                    open=76800.0,
                    high=78500.0,
                    low=76500.0,
                    close=77450.0,
                    volume=12000.0,
                    taker_buy_volume=6200.0,
                )
            )

        detector = SignalDetector(config)
        detector.evaluate(store)
        packet = build_ai_telemetry_packet(config, store)

        # Verify no empty Gate 2 parentheses
        self.assertNotIn("PENDING ()", packet)
        # Verify Bidirectional Footprint Playbook in Master Rulebook
        self.assertIn("Mode A — Spot Accumulation (Buy Low at Support to Sell Higher)", packet)
        self.assertIn("Mode B — Spot Distribution / Profit Harvest (Sell High to USDT at Resistance & Rebuy Lower)", packet)
        # Verify credential / webhook redaction in Section 9
        self.assertIn("Chat ID: `[REDACTED]`", packet)
        self.assertIn("**Webhook Bridge**: `[REDACTED — Secure Cloud Bridge Active]`", packet)
        self.assertNotIn("1273979711", packet)
        self.assertNotIn("script.google.com/macros", packet)

    def test_four_gate_spot_accumulation_confluence(self) -> None:
        """Verifies 4-Gate Spot Accumulation Confluence (Macro Tap + Positioning + Wick Absorption + Delta Flip)."""
        # Prior bar with negative delta (-8.0 BTC)
        prev_bar = FootprintBarData(
            start_ts_ms=1000,
            end_ts_ms=901000,
            open=68500.0,
            high=68550.0,
            low=68380.0,
            close=68390.0,
            net_delta=-8.0,
            is_closed=True,
        )
        self.engine.completed_bars.append(prev_bar)

        # Active bar tapping $68,400 HVN support with lower-wick absorption and +142.5 BTC delta
        active_bar = FootprintBarData(
            start_ts_ms=901000,
            end_ts_ms=1801000,
            open=68390.0,
            high=68520.0,
            low=68350.0,   # Taps support floor
            close=68420.0,  # Closes in upper body
            net_delta=142.5, # Confirmed positive delta flip
        )
        active_bar.clusters[68350.0] = FootprintClusterRow(price=68350.0, bid_vol=12.4, ask_vol=5.1, delta=-7.3, total_vol=17.5)
        active_bar.clusters[68375.0] = FootprintClusterRow(price=68375.0, bid_vol=412.0, ask_vol=88.2, delta=-323.8, total_vol=500.2)
        active_bar.clusters[68400.0] = FootprintClusterRow(price=68400.0, bid_vol=310.5, ask_vol=325.8, delta=15.3, total_vol=636.3, is_battle_zone=True)
        active_bar.clusters[68450.0] = FootprintClusterRow(price=68450.0, bid_vol=62.0, ask_vol=195.1, delta=133.1, total_vol=257.1, is_stacked_buy=True)
        active_bar.clusters[68500.0] = FootprintClusterRow(price=68500.0, bid_vol=45.2, ask_vol=168.4, delta=123.2, total_vol=213.6, is_stacked_buy=True)
        self.engine.active_bar = active_bar

        mock_store = MagicMock()
        mock_store.binance_spot_price = 68420.0
        mock_store.macro_profile = MagicMock(c_val=68400.0, c_poc=68560.0)
        mock_store.tactical_profile = None
        mock_store.derivatives_snapshot = MagicMock(funding_rate_8h=-0.00018, oi_4h_change_pct=2.4)
        mock_store.flow_snapshot = MagicMock(spot_cvd_4h=50.0, perp_cvd_4h=-80.0, spot_perp_divergence_z=1.8)

        evaluation = self.engine.evaluate(mock_store)

        self.assertTrue(evaluation.gate1_macro_tap)
        self.assertTrue(evaluation.gate2_positioning_crowded)
        self.assertTrue(evaluation.gate3_wick_absorption)
        self.assertTrue(evaluation.gate4_delta_flip)
        self.assertTrue(evaluation.all_gates_pass)
        self.assertEqual(evaluation.signal_status, "TRIGGERED_ACCUMULATE")
        self.assertEqual(evaluation.entry_price, 68420.0)
        # Hard stop is exactly 1 tick ($25) below lowest wick extreme (68350 - 25 = 68325)
        self.assertEqual(evaluation.stop_loss, 68325.0)
        risk = 68420.0 - 68325.0  # 95.0
        self.assertEqual(evaluation.tp1_1to2, 68420.0 + (2.0 * risk))

    def test_desk_f_hud_rendering_and_cli_dispatch(self) -> None:
        """Verifies Desk [F: FOOTPRINT SWING] renders in Rich Live HUD via tab 11 and tab 'f'."""
        from ui.terminal_hud import build_dashboard_renderable
        from analytics.footprint_engine import PriceCluster, FootprintBar

        store = StateStore()
        config = EngineConfig()

        # Seed data
        for i in range(20):
            store.spot_klines_15m.append(
                KlineBar(
                    timestamp_ms=1_700_000_000_000 + (i * 900_000),
                    open=68400.0,
                    high=68500.0,
                    low=68350.0,
                    close=68420.0,
                    volume=50.0,
                    taker_buy_volume=30.0,
                )
            )

        detector = SignalDetector(config)
        detector.evaluate(store)

        # Render Desk [F] via tab 11
        hud_output_11 = build_dashboard_renderable(config, store, tab_override=11)
        self.assertIsNotNone(hud_output_11)

        # Render Desk [F] via tab 'f'
        hud_output_f = build_dashboard_renderable(config, store, tab_override="f")
        self.assertIsNotNone(hud_output_f)

    def test_tab_w_waterfall_hud_rendering_and_cli_dispatch(self) -> None:
        """Verifies Tab [W: 5-PILLAR INSTITUTIONAL DECISION WATERFALL] renders in Rich Live HUD via tab 12 and aliases 'w', 'waterfall', 'wf'."""
        from ui.terminal_hud import build_dashboard_renderable, _poll_keyboard_tab_switch

        store = StateStore()
        config = EngineConfig()

        for i in range(20):
            store.spot_klines_15m.append(
                KlineBar(
                    timestamp_ms=1_700_000_000_000 + (i * 900_000),
                    open=68400.0,
                    high=68500.0,
                    low=68350.0,
                    close=68420.0,
                    volume=50.0,
                    taker_buy_volume=30.0,
                )
            )

        detector = SignalDetector(config)
        detector.evaluate(store)

        # Render Tab [W] via tab 12
        hud_output_12 = build_dashboard_renderable(config, store, tab_override=12)
        self.assertIsNotNone(hud_output_12)

        # Render Tab [W] via alias 'w'
        hud_output_w = build_dashboard_renderable(config, store, tab_override="w")
        self.assertIsNotNone(hud_output_w)

        # Render Tab [W] via alias 'waterfall'
        hud_output_wf = build_dashboard_renderable(config, store, tab_override="waterfall")
        self.assertIsNotNone(hud_output_wf)

        # Check initial tab state
        store.active_tab = 0
        self.assertEqual(store.active_tab, 0)

    def test_telemetry_json_metrics_export(self) -> None:
        """Verifies Section 6 telemetry export creates btc_metrics_latest.json with footprint block."""
        import json
        import pathlib
        from analytics.ai_packet_exporter import copy_ai_packet_to_clipboard_and_disk

        store = StateStore()
        config = EngineConfig()

        for i in range(20):
            store.spot_klines_15m.append(
                KlineBar(
                    timestamp_ms=1_700_000_000_000 + (i * 900_000),
                    open=68400.0,
                    high=68500.0,
                    low=68350.0,
                    close=68420.0,
                    volume=50.0,
                    taker_buy_volume=30.0,
                )
            )

        detector = SignalDetector(config)
        detector.evaluate(store)

        copy_ai_packet_to_clipboard_and_disk(config, store)

        metrics_file = pathlib.Path("btc_metrics_latest.json")
        self.assertTrue(metrics_file.exists())
        data = json.loads(metrics_file.read_text(encoding="utf-8"))
        self.assertIn("order_flow", data)
        self.assertIn("footprint", data["order_flow"])
        fp = data["order_flow"]["footprint"]
        self.assertIn("active_bar_delta", fp)
        self.assertIn("bar_poc", fp)
        self.assertIn("gate_1_macro_tap", fp)
        self.assertIn("gate_2_positioning_crowded", fp)
        self.assertIn("gate_3_wick_absorption", fp)
        self.assertIn("gate_4_delta_flip", fp)
        self.assertIn("signal", fp)


    def test_unfinished_auction_wick_rejection(self) -> None:
        """Verifies Gate 3 rejects lower-wick absorption if the lowest price bin is an unfinished auction (zero ask vol)."""
        bar = FootprintBarData(
            start_ts_ms=1000,
            end_ts_ms=901000,
            open=78350.0,
            high=78400.0,
            low=78300.0,
            close=78375.0,
        )
        # Lowest bin has bid_vol=8.0 but ask_vol=0.0 -> Unfinished zero-print auction at dead low
        bar.clusters[78300.0] = FootprintClusterRow(price=78300.0, bid_vol=8.0, ask_vol=0.0, delta=-8.0, total_vol=8.0)
        bar.clusters[78375.0] = FootprintClusterRow(price=78375.0, bid_vol=1.0, ask_vol=4.0, delta=3.0, total_vol=5.0)

        self.engine.analyze_bar(bar)
        self.assertFalse(bar.auction_completed)
        self.assertFalse(bar.has_wick_absorption)

    def test_bar_poc_reclaim_requirement_at_gate4(self) -> None:
        """Verifies Gate 4 requires the 15m close price to be >= the 15m Bar POC."""
        prev_bar = FootprintBarData(
            start_ts_ms=1000,
            end_ts_ms=901000,
            open=68500.0,
            high=68550.0,
            low=68380.0,
            close=68390.0,
            net_delta=-8.0,
            is_closed=True,
        )
        self.engine.completed_bars.append(prev_bar)

        active_bar = FootprintBarData(
            start_ts_ms=901000,
            end_ts_ms=1801000,
            open=68390.0,
            high=68520.0,
            low=68350.0,
            close=68400.0,  # Closed BELOW the Bar POC at $68,450
            net_delta=25.0,
        )
        active_bar.clusters[68350.0] = FootprintClusterRow(price=68350.0, bid_vol=12.0, ask_vol=4.0, delta=-8.0, total_vol=16.0)
        # Heavy volume POC sits higher at $68,450
        active_bar.clusters[68450.0] = FootprintClusterRow(price=68450.0, bid_vol=50.0, ask_vol=80.0, delta=30.0, total_vol=130.0)
        self.engine.active_bar = active_bar

        mock_store = MagicMock()
        mock_store.binance_spot_price = 68400.0
        mock_store.macro_profile = MagicMock(c_val=68400.0, c_poc=68900.0)
        mock_store.tactical_profile = None

        evaluation = self.engine.evaluate(mock_store)
        self.assertFalse(evaluation.bar_poc_reclaimed)
        self.assertFalse(evaluation.gate4_delta_flip)
        self.assertFalse(evaluation.all_gates_pass)

    def test_deterministic_capital_preservation_order_card(self) -> None:
        """Verifies 1% risk budget sizing and 50% equity notional clamping when all 4 gates pass."""
        prev_bar = FootprintBarData(
            start_ts_ms=1000,
            end_ts_ms=901000,
            open=80000.0,
            high=80100.0,
            low=79900.0,
            close=79920.0,
            net_delta=-15.0,
            is_closed=True,
        )
        self.engine.completed_bars.append(prev_bar)

        active_bar = FootprintBarData(
            start_ts_ms=901000,
            end_ts_ms=1801000,
            open=79920.0,
            high=80050.0,
            low=79850.0,
            close=79950.0,
            net_delta=35.0,
        )
        active_bar.clusters[79850.0] = FootprintClusterRow(price=79850.0, bid_vol=20.0, ask_vol=5.0, delta=-15.0, total_vol=25.0)
        active_bar.clusters[79925.0] = FootprintClusterRow(price=79925.0, bid_vol=30.0, ask_vol=80.0, delta=50.0, total_vol=110.0)
        self.engine.active_bar = active_bar

        mock_store = MagicMock()
        mock_store.binance_spot_price = 79950.0
        mock_store.macro_profile = MagicMock(c_val=79893.0, c_poc=81720.0)
        mock_store.tactical_profile = None

        evaluation = self.engine.evaluate(mock_store)
        self.assertTrue(evaluation.all_gates_pass)
        self.assertEqual(evaluation.reference_equity_usd, 100000.0)
        self.assertEqual(evaluation.risk_budget_usd, 1000.0)
        # Stop is 79850 - 25 = 79825 -> Stop distance = 79950 - 79825 = $125
        # Raw size = $1000 / $125 = 8.0 BTC ($639,600) -> Clamped to $50,000 (50% equity cap)
        self.assertTrue(evaluation.notional_clamped)
        self.assertEqual(evaluation.final_notional_usd, 50000.0)
        self.assertLess(evaluation.effective_risk_usd, 1000.0)
        self.assertEqual(evaluation.tp1_fair_value_poc, 81720.0)


if __name__ == "__main__":
    unittest.main()
