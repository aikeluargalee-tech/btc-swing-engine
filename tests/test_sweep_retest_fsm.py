"""Unit tests for SweepRetestFSM and its integration into Tab 1 Gate 4."""

import os
import tempfile
import unittest
from datetime import datetime, timezone

from analytics.sweep_retest_fsm import (
    Candle,
    FSMState,
    FSMStorageManager,
    SweepDirection,
    SweepInstance,
    SweepRetestFSM,
)
from analytics.signal_detector import SignalDetector
from config.settings import EngineConfig
from core.models import (
    DerivativesSnapshot,
    ExecutionGateState,
    FlowSnapshot,
    HorizonFlowMetrics,
    KlineBar,
    MarketRegime,
    OIPositioningQuadrant,
    VolumeProfileResult,
)
from core.state_store import StateStore


class TestSweepRetestFSM(unittest.TestCase):
    """Verifies state machine transitions, invalidations, persistence, and Tab 1 Gate 4 integration."""

    def setUp(self) -> None:
        self.fsm = SweepRetestFSM(
            rejection_window_bars=2,
            max_retest_bars=12,
            retest_tolerance_pct=0.002,  # 0.20%
            invalidation_buffer_pct=0.0015,  # 0.15%
        )

    def test_bullish_sweep_rejection_and_retest_trigger(self) -> None:
        """Verifies full lifecycle: Sweep -> Rejection -> Pending Retest -> Triggered."""
        key_level = 68000.0

        # Bar 1: Sweep (wicks below 68000 down to 67500, closes at 67800)
        c1 = Candle(timestamp=1700000000, open=68100, high=68150, low=67500, close=67800)
        setup = self.fsm.register_sweep(SweepDirection.BULLISH, key_level, c1)

        self.assertEqual(setup.current_state, FSMState.SEEKING_REJECTION)
        self.assertEqual(setup.key_level, 68000.0)
        self.assertEqual(setup.sweep_extreme, 67500.0)
        self.assertAlmostEqual(setup.invalidation_level, 67500.0 * (1 - 0.0015), places=2)
        self.assertAlmostEqual(setup.retest_band_high, 68000.0 * (1 + 0.002), places=2)
        self.assertAlmostEqual(setup.retest_band_low, 68000.0 * (1 - 0.002), places=2)

        # Bar 2: Rejection (closes back above 68000 at 68200)
        c2 = Candle(timestamp=1700003600, open=67800, high=68300, low=67750, close=68200)
        setup = self.fsm.transition(setup, c2)
        self.assertEqual(setup.current_state, FSMState.PENDING_RETEST)
        self.assertEqual(setup.bars_elapsed, 1)

        # Bar 3: Displacement away (moves up to 69000)
        c3 = Candle(timestamp=1700007200, open=68200, high=69100, low=68200, close=69000)
        setup = self.fsm.transition(setup, c3)
        self.assertEqual(setup.current_state, FSMState.PENDING_RETEST)
        self.assertEqual(setup.bars_elapsed, 2)

        # Bar 4: The Retest (dips into 68000 zone: low 67950, closes 68150)
        c4 = Candle(timestamp=1700010800, open=69000, high=69000, low=67950, close=68150)
        setup = self.fsm.transition(setup, c4)
        self.assertEqual(setup.current_state, FSMState.TRIGGERED)
        self.assertIsNotNone(setup.trigger_timestamp)

    def test_invalidation_when_closing_beyond_sweep_extreme(self) -> None:
        """Verifies hard invalidation if price accepts beyond the sweep extreme."""
        key_level = 68000.0
        c1 = Candle(timestamp=1700000000, open=68100, high=68150, low=67500, close=67800)
        setup = self.fsm.register_sweep(SweepDirection.BULLISH, key_level, c1)

        # Bar 2 closes below invalidation price (e.g. at 67300)
        c2 = Candle(timestamp=1700003600, open=67800, high=67800, low=67200, close=67300)
        setup = self.fsm.transition(setup, c2)
        self.assertEqual(setup.current_state, FSMState.INVALIDATED)

    def test_expiration_when_rejection_window_exceeded(self) -> None:
        """Verifies expiration if candle fails to close inside within rejection window."""
        key_level = 68000.0
        c1 = Candle(timestamp=1700000000, open=68100, high=68150, low=67500, close=67800)
        setup = self.fsm.register_sweep(SweepDirection.BULLISH, key_level, c1)

        # Bar 2 still below key level
        c2 = Candle(timestamp=1700003600, open=67800, high=67950, low=67600, close=67850)
        setup = self.fsm.transition(setup, c2)
        self.assertEqual(setup.current_state, FSMState.SEEKING_REJECTION)

        # Bar 3 still below key level (exceeds rejection_window_bars=2)
        c3 = Candle(timestamp=1700007200, open=67850, high=67900, low=67600, close=67700)
        setup = self.fsm.transition(setup, c3)
        self.assertEqual(setup.current_state, FSMState.EXPIRED)

    def test_storage_manager_atomic_persistence(self) -> None:
        """Verifies atomic write and loading of active non-terminal setups."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            fpath = os.path.join(tmp_dir, "test_fsm_db.json")
            mgr = FSMStorageManager(storage_path=fpath)

            c1 = Candle(timestamp=1700000000, open=68100, high=68150, low=67500, close=67800)
            setup = self.fsm.register_sweep(SweepDirection.BULLISH, 68000.0, c1)
            setup.current_state = FSMState.PENDING_RETEST

            mgr.commit({setup.instance_id: setup})

            self.assertTrue(os.path.exists(fpath))
            loaded = mgr.load_active_instances()
            self.assertIn(setup.instance_id, loaded)
            self.assertEqual(loaded[setup.instance_id].current_state, FSMState.PENDING_RETEST)

    def test_tab1_signal_detector_fsm_integration(self) -> None:
        """Verifies SignalDetector evaluates FSM and attaches telemetry to SignalEvaluation."""
        config = EngineConfig()
        detector = SignalDetector(config)

        store = StateStore()
        store.binance_spot_price = 80200.0

        # Construct synthetic bars
        base_ts = 1700000000000
        bars_1h = [
            KlineBar(
                timestamp_ms=base_ts + i * 3600000,
                open=80000.0 + i * 10,
                high=80500.0 + i * 10,
                low=79800.0 + i * 10,
                close=80200.0 + i * 10,
                volume=500.0,
                taker_buy_volume=250.0,
            )
            for i in range(50)
        ]
        store.spot_klines_1h = bars_1h
        store.spot_klines_15m = bars_1h[-20:]
        store.funding_rate_pct = 0.005
        store.record_oi_sample(90000.0, ts_sec=1000.0)
        store.record_oi_sample(90200.0, ts_sec=4600.0)
        store.coinbase_spot_price = 80205.0

        evaluation = detector.evaluate(store)

        self.assertIsNotNone(evaluation)
        self.assertIsNotNone(evaluation.fsm_status_summary)
        self.assertGreaterEqual(evaluation.fsm_max_bars, 12)


if __name__ == "__main__":
    unittest.main()
