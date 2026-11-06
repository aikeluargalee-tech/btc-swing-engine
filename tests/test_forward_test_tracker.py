"""Unit tests for the 3-Variant Parallel Forward Test Tracking & Paper Lifecycle Engine."""

import os
import shutil
import tempfile
import unittest
from unittest.mock import MagicMock

from analytics.forward_test_tracker import ForwardTestTracker
from core.models import (
    FootprintBarData,
    FootprintClusterRow,
    FootprintEvaluation,
    VariantScorecard,
)


class TestForwardTestTracker(unittest.TestCase):
    """Verifies paper execution, triple-barrier lifecycle, and metric calculations across 3 variants."""

    def setUp(self) -> None:
        self.test_dir = tempfile.mkdtemp()
        self.tracker = ForwardTestTracker(logs_dir=self.test_dir, reference_equity_usd=100000.0)

    def tearDown(self) -> None:
        try:
            shutil.rmtree(self.test_dir)
        except Exception:
            pass

    def test_initial_zero_state(self) -> None:
        """Verifies clean initial zero state across all 3 variants at minute zero."""
        cards = self.tracker.scorecards
        self.assertEqual(len(cards), 3)

        for vid in ("OPT_1_PURE_FP", "OPT_2_4GATE", "OPT_3_INSTITUTIONAL"):
            self.assertIn(vid, cards)
            sc = cards[vid]
            self.assertEqual(sc.total_trades, 0)
            self.assertEqual(sc.winning_trades, 0)
            self.assertEqual(sc.losing_trades, 0)
            self.assertEqual(sc.win_rate_pct, 0.0)
            self.assertEqual(sc.realized_pnl_usd, 0.0)
            self.assertEqual(sc.max_drawdown_usd, 0.0)
            self.assertEqual(sc.status, "OBSERVING")
            self.assertIsNone(sc.active_trade)

    def test_variant_1_pure_footprint_entry_and_stop_out(self) -> None:
        """Verifies Option 1 (15m scalp) enters on wick absorption + delta flip and stops out cleanly."""
        active_bar = FootprintBarData(
            start_ts_ms=1000,
            end_ts_ms=901000,
            open=80000.0,
            high=80100.0,
            low=79900.0,
            close=80050.0,
            net_delta=12.0,
            has_wick_absorption=True,
            wick_absorption_price=79900.0,
        )
        completed_bars = []
        eval_res = FootprintEvaluation(
            timestamp_utc="2026-11-05 12:00:00 UTC",
            current_price=80050.0,
            active_bar_delta=12.0,
            prev_bar_delta=-8.0,
            delta_flipped_bullish=True,
        )

        mock_store = MagicMock()
        mock_store.tactical_profile = None

        # Update 1: Triggers Entry
        cards = self.tracker.update(80050.0, eval_res, active_bar, completed_bars, mock_store)
        sc1 = cards["OPT_1_PURE_FP"]
        self.assertIsNotNone(sc1.active_trade)
        self.assertTrue(sc1.status.startswith("IN_POSITION"))
        trade = sc1.active_trade
        self.assertEqual(trade.entry_price, 80050.0)
        # Stop is active_bar.low (79900) - 25 = 79875 -> stop dist = $175
        self.assertEqual(trade.stop_loss, 79875.0)

        # Update 2: Price drops to Stop Loss ($79,875) -> Triggers Stop Exit
        cards = self.tracker.update(79870.0, eval_res, active_bar, completed_bars, mock_store)
        sc1 = cards["OPT_1_PURE_FP"]
        self.assertIsNone(sc1.active_trade)
        self.assertEqual(sc1.total_trades, 1)
        self.assertEqual(sc1.losing_trades, 1)
        self.assertEqual(sc1.win_rate_pct, 0.0)
        self.assertLess(sc1.realized_pnl_usd, 0.0)
        self.assertGreater(sc1.max_drawdown_usd, 0.0)
        self.assertIn(sc1.status, ("COOLDOWN", "OBSERVING"))

        # Verify atomic log exists
        ledger_path = os.path.join(self.test_dir, "forward_test_footprint.jsonl")
        self.assertTrue(os.path.exists(ledger_path))

    def test_variant_2_tp1_trim_and_tp2_harvest(self) -> None:
        """Verifies Option 2 (4-Gate) enters at macro support, trims 50% at TP1 with BE stop, and closes at TP2."""
        active_bar = FootprintBarData(
            start_ts_ms=1000,
            end_ts_ms=901000,
            open=80000.0,
            high=80100.0,
            low=79900.0,
            close=80050.0,
            net_delta=15.0,
            has_wick_absorption=True,
        )
        completed_bars = []
        eval_res = FootprintEvaluation(
            timestamp_utc="2026-11-05 12:00:00 UTC",
            current_price=80050.0,
            active_bar_delta=15.0,
            prev_bar_delta=-10.0,
            delta_flipped_bullish=True,
            gate1_macro_tap=True,
            gate1_tapped_level_name="30D cVAL",
            gate2_positioning_crowded=True,
            gate3_wick_absorption=True,
            gate4_delta_flip=True,
        )
        mock_store = MagicMock()
        mock_store.tactical_profile = None

        # Step 1: Entry
        cards = self.tracker.update(80050.0, eval_res, active_bar, completed_bars, mock_store)
        sc2 = cards["OPT_2_4GATE"]
        self.assertIsNotNone(sc2.active_trade)
        trade = sc2.active_trade
        tp1 = trade.tp1_price
        tp2 = trade.tp2_price

        # Step 2: Price hits TP1
        cards = self.tracker.update(tp1 + 10.0, eval_res, active_bar, completed_bars, mock_store)
        trade = cards["OPT_2_4GATE"].active_trade
        self.assertTrue(trade.tp1_hit)
        self.assertEqual(trade.state, "TP1_HIT")
        self.assertEqual(trade.stop_loss, round(trade.entry_price * 1.001, 2))  # Fee-adjusted break-even stop applied
        self.assertGreater(cards["OPT_2_4GATE"].realized_pnl_usd, 0.0)

        # Step 3: Price hits TP2
        cards = self.tracker.update(tp2 + 10.0, eval_res, active_bar, completed_bars, mock_store)
        sc2 = cards["OPT_2_4GATE"]
        self.assertIsNone(sc2.active_trade)
        self.assertEqual(sc2.total_trades, 1)
        self.assertEqual(sc2.winning_trades, 1)
        self.assertEqual(sc2.win_rate_pct, 100.0)
        self.assertGreater(sc2.realized_pnl_usd, 0.0)

    def test_state_persistence_and_resume(self) -> None:
        """Verifies saving state to JSON and reloading preserves scorecard telemetry across restarts."""
        sc = self.tracker.scorecards["OPT_3_INSTITUTIONAL"]
        sc.total_trades = 5
        sc.winning_trades = 4
        sc.losing_trades = 1
        sc.win_rate_pct = 80.0
        sc.realized_pnl_usd = 4250.0
        sc.max_drawdown_usd = 350.0
        sc.max_drawdown_pct = 0.35
        sc.last_closed_trade_summary = "SELL @ $84,200 • Win +$340.50"
        self.tracker.save_state()

        # Create new tracker instance pointing to same directory
        reloaded = ForwardTestTracker(logs_dir=self.test_dir, reference_equity_usd=100000.0)
        sc3 = reloaded.scorecards["OPT_3_INSTITUTIONAL"]
        self.assertEqual(sc3.total_trades, 5)
        self.assertEqual(sc3.winning_trades, 4)
        self.assertEqual(sc3.win_rate_pct, 80.0)
        self.assertEqual(sc3.realized_pnl_usd, 4250.0)
        self.assertEqual(sc3.last_closed_trade_summary, "SELL @ $84,200 • Win +$340.50")

    def test_variant_1_pure_footprint_sell_entry_and_tp2_harvest(self) -> None:
        """Verifies Option 1 (15m scalp) enters SELL on upper-wick exhaustion + negative delta flip, trims TP1, and harvests TP2."""
        active_bar = FootprintBarData(
            start_ts_ms=1000,
            end_ts_ms=901000,
            open=83900.0,
            high=84100.0,
            low=83850.0,
            close=83950.0,
            net_delta=-18.0,
            has_upper_wick_exhaustion=True,
            upper_wick_exhaustion_price=84100.0,
        )
        completed_bars = []
        eval_res = FootprintEvaluation(
            timestamp_utc="2026-11-05 14:00:00 UTC",
            current_price=83950.0,
            active_bar_delta=-18.0,
            prev_bar_delta=10.0,
            delta_flipped_bearish=True,
            direction="DISTRIBUTE_SELL",
        )
        mock_store = MagicMock()
        mock_store.tactical_profile = None

        # Step 1: Entry
        cards = self.tracker.update(83950.0, eval_res, active_bar, completed_bars, mock_store)
        sc1 = cards["OPT_1_PURE_FP"]
        self.assertIsNotNone(sc1.active_trade)
        trade = sc1.active_trade
        self.assertEqual(trade.direction, "SELL")
        self.assertEqual(trade.entry_price, 83950.0)
        # Bar high is 84100 -> stop_loss is 84125 -> stop_dist = 175
        self.assertEqual(trade.stop_loss, 84125.0)
        self.assertLess(trade.tp1_price, trade.entry_price)
        self.assertLess(trade.tp2_price, trade.tp1_price)

        # Step 2: Price drops to TP1 (e.g. 83950 - 350 = 83600)
        tp1 = trade.tp1_price
        cards = self.tracker.update(tp1 - 5.0, eval_res, active_bar, completed_bars, mock_store)
        trade = cards["OPT_1_PURE_FP"].active_trade
        self.assertTrue(trade.tp1_hit)
        self.assertEqual(trade.stop_loss, trade.entry_price)  # Ratchet stop to breakeven
        self.assertGreater(cards["OPT_1_PURE_FP"].realized_pnl_usd, 0.0)

        # Step 3: Price drops to TP2
        tp2 = trade.tp2_price
        cards = self.tracker.update(tp2 - 5.0, eval_res, active_bar, completed_bars, mock_store)
        sc1 = cards["OPT_1_PURE_FP"]
        self.assertIsNone(sc1.active_trade)
        self.assertEqual(sc1.total_trades, 1)
        self.assertEqual(sc1.winning_trades, 1)
        self.assertIn("SELL @ $83,950 • Win", sc1.last_closed_trade_summary)

    def test_variant_3_institutional_distribution_sell_lifecycle(self) -> None:
        """Verifies Option 3 (Institutional) enters SELL on TRIGGERED_DISTRIBUTE and manages stop out."""
        active_bar = FootprintBarData(
            start_ts_ms=1000,
            end_ts_ms=901000,
            open=85000.0,
            high=85300.0,
            low=84900.0,
            close=85100.0,
            net_delta=-25.0,
        )
        completed_bars = []
        eval_res = FootprintEvaluation(
            timestamp_utc="2026-11-05 15:00:00 UTC",
            current_price=85100.0,
            all_gates_pass=True,
            signal_status="TRIGGERED_DISTRIBUTE",
            direction="DISTRIBUTE_SELL",
            entry_price=85100.0,
            stop_loss=85325.0,
            tp1_1to2=84650.0,
            tp2_1to3=84200.0,
            rebuy_target_price=84200.0,
            final_position_btc=0.5,
            final_notional_usd=42550.0,
            effective_risk_usd=112.5,
            target_coin_yield_pct=1.07,
        )
        mock_store = MagicMock()

        # Step 1: Entry
        cards = self.tracker.update(85100.0, eval_res, active_bar, completed_bars, mock_store)
        sc3 = cards["OPT_3_INSTITUTIONAL"]
        self.assertIsNotNone(sc3.active_trade)
        trade = sc3.active_trade
        self.assertEqual(trade.direction, "SELL")
        self.assertEqual(trade.entry_price, 85100.0)

        # Step 2: Price pumps up to Stop Loss ($85,325) -> Triggers Stop Out
        cards = self.tracker.update(85330.0, eval_res, active_bar, completed_bars, mock_store)
        sc3 = cards["OPT_3_INSTITUTIONAL"]
        self.assertIsNone(sc3.active_trade)
        self.assertEqual(sc3.total_trades, 1)
        self.assertEqual(sc3.losing_trades, 1)
        self.assertLess(sc3.realized_pnl_usd, 0.0)
        self.assertIn("SELL @ $85,100 • Loss", sc3.last_closed_trade_summary)

    def test_hierarchy_law_enforcement(self) -> None:
        """Verifies Variant 3 can never enter unless Variant 2 qualifies + Pillar 2/3 pass."""
        active_bar = FootprintBarData(
            start_ts_ms=1000,
            end_ts_ms=901000,
            open=76000.0,
            high=76200.0,
            low=75900.0,
            close=76100.0,
            net_delta=15.0,
            has_wick_absorption=True,
        )
        completed_bars = []
        # Case A: Variant 2 fails (e.g. gate1_macro_tap is False). Variant 3 must be blocked!
        eval_res = FootprintEvaluation(
            timestamp_utc="2026-11-06 00:00:00 UTC",
            current_price=76100.0,
            gate1_macro_tap=False,  # V2 Gate 1 fails
            gate2_positioning_crowded=True,
            gate3_wick_absorption=True,
            gate4_delta_flip=True,
            all_gates_pass=True,  # Raw signal might say true, but V2 prerequisite fails
            signal_status="TRIGGERED_ACCUMULATE",
        )
        mock_store = MagicMock()
        mock_store.hard_veto = False
        mock_store.gate_state = "BALANCED"

        cards = self.tracker.update(76100.0, eval_res, active_bar, completed_bars, mock_store)
        self.assertIsNone(cards["OPT_2_4GATE"].active_trade)
        self.assertIsNone(cards["OPT_3_INSTITUTIONAL"].active_trade)
        self.assertIn("OBSERVING", cards["OPT_3_INSTITUTIONAL"].status)

        # Case B: V2 passes, but Pillar 3 fails (CPI in heavy distribution: -0.20%, Z = -1.5)
        eval_res.gate1_macro_tap = True
        eval_res.gate1_tapped_level_name = "30D Support HVN"
        eval_res.gate1_tapped_level_price = 76000.0
        eval_res.cpi_pct = -0.20
        eval_res.cpi_zscore = -1.5

        cards = self.tracker.update(76100.0, eval_res, active_bar, completed_bars, mock_store)
        # Variant 2 enters!
        self.assertIsNotNone(cards["OPT_2_4GATE"].active_trade)
        # Variant 3 is strictly VETOED by Pillar 3!
        self.assertIsNone(cards["OPT_3_INSTITUTIONAL"].active_trade)
        self.assertIn("VETOED (Pillar 3", cards["OPT_3_INSTITUTIONAL"].status)

    def test_level_lockout_and_reclaim_rule(self) -> None:
        """Verifies 4-hour level lockout prevents machine-gunning entries at the same stopped-out level."""
        active_bar = FootprintBarData(
            start_ts_ms=1000,
            end_ts_ms=901000,
            open=77500.0,
            high=77600.0,
            low=77300.0,
            close=77450.0,
            net_delta=20.0,
            has_wick_absorption=True,
        )
        completed_bars = []
        eval_res = FootprintEvaluation(
            timestamp_utc="2026-11-06 01:00:00 UTC",
            current_price=77450.0,
            gate1_macro_tap=True,
            gate1_tapped_level_name="30D HVN",
            gate1_tapped_level_price=77400.0,
            gate2_positioning_crowded=True,
            gate3_wick_absorption=True,
            gate4_delta_flip=True,
            cpi_pct=0.01,
            cpi_zscore=0.5,
            rr_to_tp2=3.5,
        )
        mock_store = MagicMock()
        mock_store.hard_veto = False
        mock_store.gate_state = "BALANCED"

        # Step 1: Entry at 30D HVN
        cards = self.tracker.update(77450.0, eval_res, active_bar, completed_bars, mock_store)
        self.assertIsNotNone(cards["OPT_2_4GATE"].active_trade)
        stop_price = cards["OPT_2_4GATE"].active_trade.stop_loss

        # Step 2: Waterfall crash hits stop loss
        cards = self.tracker.update(stop_price - 10.0, eval_res, active_bar, completed_bars, mock_store)
        self.assertIsNone(cards["OPT_2_4GATE"].active_trade)
        # Level "30D HVN" must now be locked out!
        self.assertIn("30D HVN", self.tracker.level_lockouts)

        # Step 3: Fast re-attempt at same level (price hovering near stopped price) -> MUST BE LOCKED OUT!
        # Reset exit cooldown to test level lockout specifically
        self.tracker._last_exit_ts["OPT_2_4GATE"] = 0.0
        cards = self.tracker.update(77350.0, eval_res, active_bar, completed_bars, mock_store)
        self.assertIsNone(cards["OPT_2_4GATE"].active_trade)
        self.assertIn("LOCKED_OUT", cards["OPT_2_4GATE"].status)

        # Step 4: Intra-bar falling knife below level without reclaim (current_price < level_price)
        eval_res.gate1_tapped_level_name = "7D cVAL"
        eval_res.gate1_tapped_level_price = 75500.0
        # Price is 75400 (below level, candle falling)
        cards = self.tracker.update(75400.0, eval_res, active_bar, completed_bars, mock_store)
        self.assertIsNone(cards["OPT_2_4GATE"].active_trade)
        self.assertIn("AWAITING 15M RECLAIM", cards["OPT_2_4GATE"].status)

    def test_2r_fee_adjusted_breakeven_ratchet(self) -> None:
        """Verifies Variants 2 and 3 automatically ratchet stop_loss to entry_price * 1.001 at >= +2.0R."""
        active_bar = FootprintBarData(
            start_ts_ms=1000,
            end_ts_ms=901000,
            open=75300.0,
            high=75500.0,
            low=75208.42,
            close=75438.38,
            net_delta=20.0,
            has_wick_absorption=True,
        )
        completed_bars = [active_bar]
        eval_res = FootprintEvaluation(
            timestamp_utc="2026-11-05 23:15:03 UTC",
            current_price=75438.38,
            active_bar_delta=20.0,
            prev_bar_delta=-5.0,
            delta_flipped_bullish=True,
            gate1_macro_tap=True,
            gate1_tapped_level_name="7D HVN",
            gate1_tapped_level_price=75400.0,
            gate2_positioning_crowded=True,
            gate3_wick_absorption=True,
            gate4_delta_flip=True,
            auction_completed=True,
            bar_poc_reclaimed=True,
            cpi_pct=0.02,
            cpi_zscore=0.4,
            rr_to_tp1=2.5,
            rr_to_tp2=3.5,
            entry_price=75438.38,
            stop_loss=75183.42,
            tp1_fair_value_poc=76529.0,
            tp2_short_liq_magnet=79646.0,
            final_position_btc=0.6628,
            final_notional_usd=50000.0,
            effective_risk_usd=168.99,
        )
        mock_store = MagicMock()
        mock_store.hard_veto = False
        mock_store.gate_state = "BALANCED"
        mock_store.tactical_profile = MagicMock(c_poc=77983.0)

        # 1. Enter at $75,438.38 with SL $75,183.42 (1R = $254.96/BTC)
        cards = self.tracker.update(75438.38, eval_res, active_bar, completed_bars, mock_store)
        t2 = cards["OPT_2_4GATE"].active_trade
        t3 = cards["OPT_3_INSTITUTIONAL"].active_trade
        self.assertIsNotNone(t2)
        self.assertIsNotNone(t3)
        self.assertLess(t2.tp1_price, t2.tp2_price)
        self.assertLess(t3.tp1_price, t3.tp2_price)

        # 2. Price rises to $76,269.11 (+3.26R, above +2.0R threshold $75,948.30, below TP1 $76,529)
        cards = self.tracker.update(76269.11, eval_res, active_bar, completed_bars, mock_store)
        self.assertEqual(cards["OPT_2_4GATE"].active_trade.stop_loss, 75513.82)
        self.assertEqual(cards["OPT_3_INSTITUTIONAL"].active_trade.stop_loss, 75513.82)

    def test_price_floor_waterfall_no_inverted_bids(self) -> None:
        """Verifies Tab [1] _build_trade_plan cascades bid zone below spot when 30D HVN is breached."""
        from config.settings import EngineConfig
        from analytics.signal_detector import SignalDetector

        detector = SignalDetector(EngineConfig())
        bars = [MagicMock(low=75438.0) for _ in range(10)]
        tact_vp = MagicMock(
            horizon_label="7D Tactical",
            c_vah=79500.0,
            c_poc=77983.0,
            c_val=76529.0,
            primary_lvn_below_val=76000.0,
            support_hvn_below_val=75591.0,
        )
        pev = MagicMock(daily_support=75736.0, long_liq_magnet_usd=75190.16, downside_ref_1d_atr=73700.0)
        mev = MagicMock(ema_200_1d=74250.0)

        plan = detector._build_trade_plan(
            current_price=75958.0,
            c_val=79893.0,
            c_poc=81724.0,
            c_vah=84500.0,
            primary_lvn=78500.0,
            support_hvn=77369.0,  # Breached 30D HVN ($1,411 above spot $75,958)
            atr_1h=450.0,
            recent_bars_1h=bars,
            tactical_vp=tact_vp,
            session_vp=None,
            protocol_ev=pev,
            macro_ev=mev,
        )
        # Entry zone must NEVER be inverted above current_price ($75,958)
        self.assertLessEqual(plan.entry_zone_high, 75958.0)
        self.assertAlmostEqual(plan.entry_zone_low, 75591.0, places=1)
        # Breached 30D HVN ($77,369) becomes TP1 overhead resistance
        self.assertEqual(plan.tp1_poc, 77369.0)
        # Hard stop must not sit on top of $75,190.16 long liquidation magnet
        self.assertLess(plan.stop_loss, 74500.0)


if __name__ == "__main__":
    unittest.main()
