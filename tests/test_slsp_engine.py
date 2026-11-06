"""Unit tests for Tab [13]: Structure + Level Swing Protocol (SLSP v1.0) & 4-in-1 Integration Desk."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from typing import List

from config.settings import EngineConfig
from core.models import (
    EMAStrategySnapshot,
    KlineBar,
    SLSPEvaluation,
    SLSPKeyLevel,
    SLSPTradeSetup,
    TellTaleBarResult,
    TellTaleEvaluation,
    VolumeProfileResult,
)
from core.state_store import StateStore
from analytics.slsp_engine import SLSPEngine
from analytics.slsp_trade_manager import SLSPTradeManager
from ui.terminal_hud import build_dashboard_renderable


def make_kline(
    timestamp_ms: int,
    open_: float,
    high: float,
    low: float,
    close: float,
    volume: float = 100.0,
    taker_buy_volume: float = 50.0,
) -> KlineBar:
    return KlineBar(
        timestamp_ms=timestamp_ms,
        open=open_,
        high=high,
        low=low,
        close=close,
        volume=volume,
        taker_buy_volume=taker_buy_volume,
    )


class TestSLSPEngine(unittest.TestCase):
    """Verifies all rules in SLSP v1.0 and 4-in-1 component fusion."""

    def setUp(self) -> None:
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.state_path = Path(self.tmp_dir.name) / "slsp_trade_state.json"
        self.config = EngineConfig(
            slsp_risk_pct=0.75,
            slsp_max_risk_pct=1.00,
            slsp_min_rr=1.50,
            slsp_min_level_strength=3,
            slsp_state_path=self.state_path,
        )
        self.engine = SLSPEngine(self.config, read_only=True)
        self.store = StateStore()

    def tearDown(self) -> None:
        self.tmp_dir.cleanup()

    def test_daily_regime_detection_uptrend(self) -> None:
        """Verifies UPTREND classification on Higher Highs & Higher Lows with intact swing low."""
        bars: List[KlineBar] = []
        base_ts = 1700000000000
        # Build 12 daily bars with ascending swing structure
        # High 1 @ $75.5k, Low 1 @ $71.8k, High 2 @ $78.5k, Low 2 @ $75.0k
        prices = [
            (70000, 71000, 69500, 70500),  # 0
            (70500, 72000, 70200, 71800),  # 1
            (71800, 75500, 71500, 75000),  # 2 Swing High 1 (~$75.5k)
            (75000, 75200, 73000, 73500),  # 3
            (73500, 74000, 71800, 72200),  # 4 Swing Low 1 (~$71.8k)
            (72200, 76000, 72000, 75800),  # 5
            (75800, 78500, 75500, 78200),  # 6 Swing High 2 (~$78.5k > $75.5k)
            (78200, 78300, 76500, 77000),  # 7
            (77000, 77500, 75000, 76200),  # 8 Swing Low 2 (~$75.0k > $71.8k)
            (76200, 77000, 75800, 76500),  # 9
            (76500, 77200, 76000, 76800),  # 10
            (76800, 77500, 76200, 77000),  # 11
        ]
        for i, (o, h, l, c) in enumerate(prices):
            bars.append(make_kline(base_ts + i * 86400000, o, h, l, c, 1000.0))

        regime, reason, sh, sl = self.engine.detect_daily_regime(bars, current_price=76800.0)
        self.assertEqual(regime, "UPTREND")
        self.assertIn("Higher Highs", reason)

    def test_daily_regime_detection_downtrend(self) -> None:
        """Verifies DOWNTREND classification on Lower Highs & Lower Lows with intact swing high."""
        bars: List[KlineBar] = []
        base_ts = 1700000000000
        # Descending pivots: High 1 @ $84k, Low 1 @ $75k, High 2 @ $79k, Low 2 @ $71k
        prices = [
            (82000, 83000, 81000, 82500),  # 0
            (82500, 84000, 82000, 83500),  # 1 Swing High 1 (~$84k)
            (83500, 83800, 79000, 79500),  # 2
            (79500, 80000, 75000, 75500),  # 3 Swing Low 1 (~$75k)
            (75500, 78000, 75000, 77500),  # 4
            (77500, 79000, 77000, 78500),  # 5 Swing High 2 (~$79k < $84k)
            (78500, 78800, 73000, 73500),  # 6
            (73500, 74000, 71000, 71500),  # 7 Swing Low 2 (~$71k < $75k)
            (71500, 73500, 72000, 73000),  # 8 (bounce establishes swing low at 7)
            (73000, 73200, 71500, 71800),  # 9
            (71800, 72000, 70800, 71000),  # 10
        ]
        for i, (o, h, l, c) in enumerate(prices):
            bars.append(make_kline(base_ts + i * 86400000, o, h, l, c, 1000.0))

        regime, reason, sh, sl = self.engine.detect_daily_regime(bars, current_price=70000.0)
        self.assertEqual(regime, "DOWNTREND")
        self.assertIn("Lower Highs", reason)

    def test_key_level_identification_and_scoring(self) -> None:
        """Verifies horizontal levels are scored 1-5 stars based on touches, round numbers, and HVNs."""
        bars: List[KlineBar] = []
        base_ts = 1700000000000
        # Create daily bars touching $75,000 (a round number) multiple times
        for i in range(25):
            o = 76000.0
            h = 77000.0
            l = 74900.0 if i in (3, 8, 14, 20) else 75500.0  # 4 touches at $75k
            c = 76200.0
            bars.append(make_kline(base_ts + i * 86400000, o, h, l, c, 1000.0))

        vp = VolumeProfileResult(
            horizon_label="30D",
            c_vah=78000.0,
            c_poc=75000.0,  # Confluent POC at $75k
            c_val=72000.0,
            range_high=80000.0,
            range_low=70000.0,
            total_volume=50000.0,
            bin_width=100.0,
        )

        levels = self.engine.detect_key_levels(bars, current_price=76200.0, active_vp=vp)
        self.assertTrue(len(levels) > 0)
        # Find level near $75,000
        lvl_75k = next((lv for lv in levels if abs(lv.center_price - 75000.0) <= 500.0), None)
        self.assertIsNotNone(lvl_75k)
        self.assertGreaterEqual(lvl_75k.strength, 4)  # Multi-touches + Round number + HVN
        self.assertTrue(lvl_75k.is_round_number)
        self.assertEqual(lvl_75k.level_type, "SUPPORT")

    def test_4h_rejection_candle_pinbar_and_volume(self) -> None:
        """Verifies 4H rejection pinbar (>=50% lower wick) and volume > 20 SMA filter."""
        bars_4h: List[KlineBar] = []
        base_ts = 1700000000000
        # 20 baseline bars with volume 100.0
        for i in range(20):
            bars_4h.append(
                make_kline(
                    base_ts + i * 14400000,
                    76000.0,
                    76200.0,
                    75800.0,
                    76100.0,
                    volume=100.0,
                )
            )

        # 21st bar: Previous bar
        bars_4h.append(
            make_kline(
                base_ts + 20 * 14400000,
                76100.0,
                76300.0,
                75900.0,
                76000.0,
                volume=100.0,
            )
        )

        # 22nd bar: Bullish pinbar with 71.4% lower wick and volume 150.0 (1.5x baseline)
        bars_4h.append(
            make_kline(
                base_ts + 21 * 14400000,
                76000.0,
                76200.0,
                75500.0,
                76100.0,
                volume=150.0,
            )
        )

        confirmed, rej_type, wick_ratio, vol_ratio = self.engine.evaluate_4h_rejection(bars_4h)
        self.assertTrue(confirmed)
        self.assertEqual(rej_type, "PINBAR")
        self.assertGreaterEqual(wick_ratio, 0.50)
        self.assertGreaterEqual(vol_ratio, 1.0)

    def test_4h_rejection_fails_on_low_volume(self) -> None:
        """Verifies 4H rejection is rejected if volume is below the 20-period average."""
        bars_4h: List[KlineBar] = []
        base_ts = 1700000000000
        # 20 baseline bars with volume 200.0
        for i in range(21):
            bars_4h.append(
                make_kline(
                    base_ts + i * 14400000,
                    76000.0,
                    76200.0,
                    75800.0,
                    76100.0,
                    volume=200.0,
                )
            )

        # 22nd bar: Pinbar but low volume 50.0 (0.25x baseline)
        bars_4h.append(
            make_kline(
                base_ts + 21 * 14400000,
                76000.0,
                76200.0,
                75500.0,
                76100.0,
                volume=50.0,
            )
        )

        confirmed, rej_type, wick_ratio, vol_ratio = self.engine.evaluate_4h_rejection(bars_4h)
        self.assertFalse(confirmed)
        self.assertEqual(rej_type, "PINBAR_LOW_VOL")

    def test_obstacle_clearance_1_5r(self) -> None:
        """Verifies obstacle detection when major resistance sits within 1.5R."""
        entry = 76000.0
        stop = 75000.0  # 1R = $1,000. 1.5R target = $77,500
        # Case A: Obstacle at $77,000 (1.0R away < 1.5R hurdle)
        r_obstacle = [
            SLSPKeyLevel(
                price_min=76900.0,
                price_max=77100.0,
                center_price=77000.0,
                level_type="RESISTANCE",
                strength=4,
                touch_count=3,
                description="3x Touches",
            )
        ]
        clear, dist_r, msg = self.engine.check_obstacle_clearance(entry, stop, r_obstacle)
        self.assertFalse(clear)
        self.assertIn("OBSTACLE VETO", msg)
        self.assertAlmostEqual(dist_r, 1.0, places=1)

        # Case B: Clear runway (Resistance at $78,500 = 2.5R away > 1.5R hurdle)
        r_clear = [
            SLSPKeyLevel(
                price_min=78400.0,
                price_max=78600.0,
                center_price=78500.0,
                level_type="RESISTANCE",
                strength=4,
                touch_count=3,
                description="3x Touches",
            )
        ]
        clear_b, dist_b, msg_b = self.engine.check_obstacle_clearance(entry, stop, r_clear)
        self.assertTrue(clear_b)
        self.assertIn("RUNWAY CLEAR", msg_b)
        self.assertAlmostEqual(dist_b, 2.5, places=1)

    def test_tell_tale_anti_knife_veto(self) -> None:
        """Verifies Tell-Tale 5x volume selling climax triggers HARD VETO on long setups."""
        # Setup store with an active 5x selling climax
        tt_eval = TellTaleEvaluation(
            timestamp_utc="2026-11-06 12:00:00 UTC",
            is_selling_climax=True,  # 5x volume selling dump active!
            is_buying_climax=False,
            disruption_detected=True,
            climax_type="SELLING_CLIMAX",
            plain_status="🚨 5X SELLING CLIMAX DUMP",
            bar_15m=TellTaleBarResult(
                timeframe="15m",
                open_time="2026-11-06T12:00:00Z",
                close=75900.0,
                open=76500.0,
                high=76550.0,
                low=75850.0,
                volume=5000.0,
                baseline_volume=900.0,
                red=True,
                green=False,
                relvol=5.55,
                body_range=0.85,
                is_selling_climax=True,
                is_buying_climax=False,
                is_elevated_volume=True,
            ),
        )
        self.store.exhaustion_evaluation = SimpleNamespace(tell_tale=tt_eval)

        bars_1d = [
            make_kline(1700000000000 + i * 86400000, 75000, 77000, 74500, 76000)
            for i in range(15)
        ]
        bars_4h = [
            make_kline(1700000000000 + i * 14400000, 75800, 76200, 75500, 76000)
            for i in range(25)
        ]

        eval_res = self.engine.evaluate(self.store, bars_1d, bars_4h, current_price=76000.0)
        self.assertTrue(eval_res.tell_tale_veto)
        self.assertEqual(eval_res.trade_state, "STAND_ASIDE")
        self.assertIn("HARD VETO", " • ".join(eval_res.decision_log))

    def test_trade_manager_lifecycle_and_ratchet(self) -> None:
        """Verifies exact sizing, 1.0R breakeven ratchet, 1.5R TP1 harvest, and 2.5R TP2 exit."""
        mgr = SLSPTradeManager(
            state_path=self.state_path,
            account_equity=100_000.0,
            risk_pct=0.75,  # $750.00 dollar risk
        )

        entry = 75000.0
        stop = 74000.0  # $1,000 risk per coin. 1.0R = $76,000, 1.5R = $76,500, 2.5R = $77,500
        risk_usd, size_btc, notional_usd = mgr.calculate_sizing(entry, stop)

        self.assertAlmostEqual(risk_usd, 750.0, places=1)
        self.assertAlmostEqual(size_btc, 0.7500, places=3)
        self.assertAlmostEqual(notional_usd, 56250.0, places=1)

        opened = mgr.open_trade(
            trade_id="SLSP_TEST_01",
            direction="LONG",
            entry_price=entry,
            stop_loss=stop,
            size_btc=size_btc,
            tp1_price=76500.0,
            tp2_price=77500.0,
        )
        self.assertTrue(opened)
        self.assertEqual(mgr.active_trade.state, "OPEN")

        # 1. Price moves to $75,800 (+0.8R) -> BE ratchet NOT triggered yet
        t1 = mgr.update_tick(75800.0)
        self.assertFalse(t1.be_ratcheted)
        self.assertEqual(t1.current_stop, 74000.0)

        # 2. Price hits $76,050 (+1.05R) -> BE ratchet triggers! Stop moves to Entry * 1.001 ($75,075)
        t2 = mgr.update_tick(76050.0)
        self.assertTrue(t2.be_ratcheted)
        self.assertEqual(t2.current_stop, 75075.0)

        # 3. Price hits $76,500 (+1.5R) -> TP1 50% scale-out harvests 0.375 BTC
        t3 = mgr.update_tick(76500.0)
        self.assertTrue(t3.tp1_harvested)
        self.assertEqual(t3.state, "TP1_HARVESTED")
        self.assertAlmostEqual(t3.remaining_size_btc, 0.3750, places=3)
        self.assertGreater(t3.realized_pnl_usd, 500.0)

        # 4. Price hits $77,500 (+2.5R) -> TP2 closes trade fully
        t4 = mgr.update_tick(77500.0)
        self.assertEqual(t4.state, "CLOSED_TP2")
        self.assertEqual(t4.remaining_size_btc, 0.0)
        self.assertIn("TP2 HIT", t4.exit_reason)

    def test_circuit_breaker_lockout(self) -> None:
        """Verifies 2.0% daily loss triggers circuit breaker and locks out new trades."""
        mgr = SLSPTradeManager(
            state_path=self.state_path,
            account_equity=100_000.0,
            risk_pct=0.75,
            max_daily_loss_pct=2.0,  # $2,000 max daily loss
        )

        # Simulate consecutive stopped trades totaling -$2,250 loss
        mgr._update_circuit_breakers_on_loss(-2250.0)

        cb_active, cb_reason = mgr.is_circuit_breaker_active()
        self.assertTrue(cb_active)
        self.assertIn("DAILY LOSS LOCKOUT", cb_reason)

        # Attempt to open trade while locked out
        opened = mgr.open_trade(
            trade_id="SLSP_BLOCKED",
            direction="LONG",
            entry_price=76000.0,
            stop_loss=75000.0,
            size_btc=0.5,
            tp1_price=77500.0,
            tp2_price=78500.0,
        )
        self.assertFalse(opened)

    def test_terminal_hud_tab13_rendering(self) -> None:
        """Smoke test verifying Tab [13: P] renders cleanly via build_dashboard_renderable."""
        bars_1d = [
            make_kline(1700000000000 + i * 86400000, 74000, 77000, 73500, 76300)
            for i in range(20)
        ]
        bars_4h = [
            make_kline(1700000000000 + i * 14400000, 75800, 76500, 75500, 76323)
            for i in range(30)
        ]

        self.store.spot_klines_1d.extend(bars_1d)
        self.store.binance_spot_price = 76323.79

        self.store.ema_strategy = EMAStrategySnapshot(
            daily_regime="BULLISH",
            daily_ema_20=74500.0,
            daily_ema_50=72000.0,
            daily_ema_200=68500.0,
            daily_ema_200_slope=0.25,
            daily_adx=24.5,
            ema_4h_9=76100.0,
            ema_4h_20=75800.0,
            ema_4h_50=75200.0,
            ema_4h_200=71000.0,
            pullback_zone_active=True,
            trigger_active=True,
            positioning_confirmations_met=2,
        )

        self.engine.evaluate(self.store, bars_1d, bars_4h, current_price=76323.79)

        renderable = build_dashboard_renderable(self.config, self.store, tab_override=13)
        self.assertIsNotNone(renderable)

    def test_ai_telemetry_packet_section13_export(self) -> None:
        """Verifies that pressing 'C' copies Tab P data in Section 13 of the AI packet."""
        from analytics.ai_packet_exporter import build_ai_telemetry_packet

        bars_1d = [
            make_kline(1700000000000 + i * 86400000, 74000, 77000, 73500, 76300)
            for i in range(20)
        ]
        bars_4h = [
            make_kline(1700000000000 + i * 14400000, 75800, 76500, 75500, 76323)
            for i in range(30)
        ]
        self.store.spot_klines_1d.extend(bars_1d)
        self.store.binance_spot_price = 76323.79
        self.engine.evaluate(self.store, bars_1d, bars_4h, current_price=76323.79)

        packet = build_ai_telemetry_packet(self.config, self.store)
        self.assertIn("## SECTION 13: TAB [P] PRICE ACTION & STRUCTURE PROTOCOL", packet)
        self.assertIn("13A. Panel [1] File A: SLSP v1.0", packet)
        self.assertIn("13B. Panel [2] File B: Industrial 3-EMA", packet)
        self.assertIn("13C. Panel [3] Project 8: BTC Liquidation Flush", packet)
        self.assertIn("13D. Panel [4] Project 7: Tell-Tale", packet)
        self.assertIn("13E. Panel [5] Executive Alignment", packet)



if __name__ == "__main__":
    unittest.main()
