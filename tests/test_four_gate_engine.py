"""Unit tests for the 4-Gate Quantitative Protocol Engine (Tab 19 / [Q])."""

import json
import unittest
from unittest.mock import MagicMock, patch

import numpy as np

from analytics.four_gate_engine import FourGateEngine, copy_four_gate_to_clipboard
from analytics.data_only_reports import build_tab_q_data_only_report
from config.settings import DEFAULT_CONFIG
from core.models import FourGateEvaluation
from core.state_store import StateStore


def _generate_synthetic_4h_bars(n_bars: int = 240, base_price: float = 70000.0):
    """Generates deterministic 4H bars for offline unit testing."""
    bars_spot = []
    bars_perp = []
    t_start = 1700000000000
    tf_4h = 14400 * 1000

    for i in range(n_bars):
        t_open = t_start + (i * tf_4h)
        t_close = t_open + tf_4h - 1
        px = base_price + (i * 20.0) + (15.0 * np.sin(i / 5.0))
        h = px + 100.0
        l = px - 100.0
        tot_vol = 1000.0
        buy_vol = 600.0  # Net positive delta: 2*600 - 1000 = +200

        # Spot format: [open_time, open, high, low, close, vol, close_time, quote_vol, trades, taker_buy_vol]
        s_bar = [t_open, str(px - 10.0), str(h), str(l), str(px), str(tot_vol), t_close, "1000000", 100, str(buy_vol)]
        p_bar = [t_open, str(px - 10.0), str(h), str(l), str(px), str(tot_vol), t_close, "1000000", 100, str(400.0)]  # Perp net negative: 2*400 - 1000 = -200

        bars_spot.append(s_bar)
        bars_perp.append(p_bar)

    funding_prints = []
    for i in range(120):
        funding_prints.append({"fundingTime": t_start + (i * 8 * 3600 * 1000), "fundingRate": "0.00005000"})

    return bars_spot, bars_perp, funding_prints


class TestFourGateEngine(unittest.TestCase):
    """Test suite for FourGateEngine math, sizing, and fail-closed safety."""

    def setUp(self):
        self.engine = FourGateEngine(DEFAULT_CONFIG)
        self.store = StateStore()

    def test_init(self):
        self.assertIsNotNone(self.engine)
        self.assertIsNone(self.store.four_gate_evaluation)

    def test_deterministic_calculation_gates_evaluated(self):
        spot_k, perp_k, fund_p = _generate_synthetic_4h_bars(240, 75000.0)
        dvol_val = 45.0

        ev = self.engine.calculate_evaluation(spot_k, perp_k, fund_p, dvol_val, equity_usd=100000.0)
        self.assertIsInstance(ev, FourGateEvaluation)
        self.assertTrue(ev.raw_data_available)
        self.assertIn(ev.score, [0, 1, 2, 3, 4])
        self.assertIn(ev.status, ["LIVE", "STANDBY"])
        self.assertIn(ev.verdict, ["EXECUTE SPOT LONG", "STANDBY / CASH"])
        self.assertGreater(ev.live_spot_price, 0.0)
        self.assertIn("UTC", ev.last_closed_bar_utc)
        self.assertGreater(ev.entry_price, 0.0)
        self.assertGreater(ev.stop_price, 0.0)
        self.assertLess(ev.stop_price, ev.entry_price)
        self.assertGreater(ev.notional_risk_usd, 0.0)
        self.assertGreater(ev.notional_vol_usd, 0.0)
        self.assertGreater(ev.final_notional_usd, 0.0)
        self.assertGreater(ev.btc_size, 0.0)

    def test_gate1_levy_signed_area_math(self):
        spot_k, perp_k, fund_p = _generate_synthetic_4h_bars(240, 70000.0)
        ev = self.engine.calculate_evaluation(spot_k, perp_k, fund_p, 50.0)
        self.assertIsInstance(ev.gate_1_val, float)
        self.assertEqual(ev.gate_1_levy, ev.gate_1_val > 0.0)

    def test_gate2_zflow_divergence(self):
        spot_k, perp_k, fund_p = _generate_synthetic_4h_bars(240, 70000.0)
        ev = self.engine.calculate_evaluation(spot_k, perp_k, fund_p, 50.0)
        self.assertIsInstance(ev.gate_2_val, float)
        self.assertEqual(ev.gate_2_zflow, ev.gate_2_val >= 1.0 and ev.gate_2_ds_24h > 0)

    def test_gate3_volume_profile_poc_val_vah(self):
        spot_k, perp_k, fund_p = _generate_synthetic_4h_bars(240, 70000.0)
        ev = self.engine.calculate_evaluation(spot_k, perp_k, fund_p, 50.0)
        self.assertGreater(ev.gate_3_poc, 0.0)
        self.assertGreater(ev.gate_3_val, 0.0)
        self.assertGreater(ev.gate_3_vah, ev.gate_3_val)
        self.assertIn(ev.gate_3_state, ["STATE_A", "STATE_B", "NONE"])

    def test_gate4_funding_percentile(self):
        spot_k, perp_k, fund_p = _generate_synthetic_4h_bars(240, 70000.0)
        ev = self.engine.calculate_evaluation(spot_k, perp_k, fund_p, 50.0)
        self.assertGreaterEqual(ev.gate_4_funding_p90, 0.0)
        self.assertLessEqual(ev.gate_4_funding_p90, 100.0)

    def test_sizing_and_075_risk_cap(self):
        spot_k, perp_k, fund_p = _generate_synthetic_4h_bars(240, 80000.0)
        equity = 100000.0
        ev = self.engine.calculate_evaluation(spot_k, perp_k, fund_p, 55.0, equity_usd=equity)

        # Max dollar loss at stop must equal exactly equity * 0.0075 ($750)
        dollar_loss_at_stop = ev.final_notional_usd * ev.stop_pct
        self.assertLessEqual(dollar_loss_at_stop, 750.01)
        # Clamped between 1.25% and 4.00%
        self.assertGreaterEqual(ev.stop_pct, 0.0125)
        self.assertLessEqual(ev.stop_pct, 0.0401)

        # High DVOL throttles notional
        ev_high_dvol = self.engine.calculate_evaluation(spot_k, perp_k, fund_p, 110.0, equity_usd=equity)
        self.assertLessEqual(ev_high_dvol.notional_vol_usd, equity * 0.51)

    def test_fail_closed_on_missing_data(self):
        # Pass empty bars -> must return HALT: DATA UNAVAILABLE
        ev = self.engine.calculate_evaluation([], [], [], 0.0)
        self.assertFalse(ev.raw_data_available)
        self.assertEqual(ev.status, "HALT: DATA UNAVAILABLE")
        self.assertEqual(ev.verdict, "HALT: DATA UNAVAILABLE")
        self.assertEqual(ev.score, 0)

    def test_clipboard_and_data_only_report(self):
        spot_k, perp_k, fund_p = _generate_synthetic_4h_bars(240, 75000.0)
        ev = self.engine.calculate_evaluation(spot_k, perp_k, fund_p, 42.0)
        self.store.four_gate_evaluation = ev

        ok, msg, char_count = copy_four_gate_to_clipboard(self.store)
        self.assertTrue(ok)
        self.assertGreater(char_count, 100)

        report = build_tab_q_data_only_report(DEFAULT_CONFIG, self.store)
        self.assertIn("BTC 4-GATE QUANTITATIVE PROTOCOL TELEMETRY PACKET", report)
        self.assertIn("GATE_1_LEVY_SIGNED_AREA_PASS", report)
        self.assertIn("ENTRY_PRICE_USD", report)

    def test_dibse_dual_sleeve_capital_allocation(self):
        spot_k, perp_k, fund_p = _generate_synthetic_4h_bars(240, 75000.0)
        equity = 100000.0
        ev = self.engine.calculate_evaluation(spot_k, perp_k, fund_p, 45.0, equity_usd=equity)

        # 20% Sandbox / 80% Core Reserve
        self.assertEqual(ev.account_equity_usd, equity)
        self.assertEqual(ev.active_sandbox_usd, 20000.0)
        self.assertEqual(ev.core_reserve_usd, 80000.0)
        # 10% USDT Sleeve / 10% BTC Sleeve
        self.assertEqual(ev.usdt_sleeve_usd, 10000.0)
        self.assertEqual(ev.btc_sleeve_usd, 10000.0)
        self.assertGreater(ev.btc_sleeve_units, 0.0)
        self.assertAlmostEqual(ev.btc_sleeve_units * ev.live_spot_price, 10000.0, places=2)
        self.assertIn("NEUTRAL", ev.inventory_state)

    def test_dibse_loop_a_dip_harvester_math(self):
        spot_k, perp_k, fund_p = _generate_synthetic_4h_bars(240, 72000.0)
        ev = self.engine.calculate_evaluation(spot_k, perp_k, fund_p, 45.0)

        # Loop A properties
        self.assertIn(ev.loop_a_score, [0, 1, 2, 3, 4])
        self.assertIn(ev.loop_a_status, ["READY_USDT", "EXECUTE_BUY", "HOLDING_SPOT_BTC_INVENTORY"])
        self.assertIn(ev.loop_a_verdict, ["EXECUTE: DEPLOY USDT → BUY BTC", "STANDBY IN USDT CASH"])
        self.assertGreater(ev.loop_a_entry_price, 0.0)
        self.assertGreater(ev.loop_a_target_price, ev.loop_a_entry_price)
        self.assertGreater(ev.loop_a_target_pct, 0.0)
        self.assertGreater(ev.loop_a_expected_profit_usd, 0.0)
        self.assertIn("ZERO FORCED STOP-LOSS", ev.loop_a_stop_rule)

    def test_dibse_loop_b_rip_harvester_math(self):
        spot_k, perp_k, fund_p = _generate_synthetic_4h_bars(240, 78000.0)
        ev = self.engine.calculate_evaluation(spot_k, perp_k, fund_p, 45.0)

        # Loop B properties
        self.assertIn(ev.loop_b_score, [0, 1, 2, 3, 4])
        self.assertIn(ev.loop_b_status, ["HOLDING_BTC", "EXECUTE_SELL", "HOLDING_SPOT_USDT_INVENTORY"])
        self.assertIn(ev.loop_b_verdict, ["EXECUTE: DEPLOY BTC → SELL TO USDT", "HOLD BTC INVENTORY"])
        self.assertGreater(ev.loop_b_sell_price, 0.0)
        self.assertLess(ev.loop_b_buyback_price, ev.loop_b_sell_price)
        self.assertGreater(ev.loop_b_discount_pct, 0.0)
        self.assertGreater(ev.loop_b_free_satoshis_btc, 0.0)
        self.assertGreater(ev.loop_b_free_satoshis_pct, 0.0)
        self.assertGreater(ev.loop_b_surplus_cash_usd, 0.0)
        self.assertIn("ZERO FORCED STOP-BUY", ev.loop_b_stop_rule)

    def test_dibse_historical_event_study_dual_loop(self):
        spot_k, perp_k, fund_p = _generate_synthetic_4h_bars(240, 75000.0)
        ev = self.engine.calculate_evaluation(spot_k, perp_k, fund_p, 45.0)

        # Loop A and Loop B historical event studies
        self.assertIsInstance(ev.event_study_results, dict)
        self.assertIsInstance(ev.event_study_loop_b_results, dict)
        self.assertIn("win_rate_1d", ev.event_study_results)
        self.assertIn("win_rate_1d", ev.event_study_loop_b_results)
        self.assertIn("alpha_1d", ev.event_study_results)
        self.assertIn("alpha_1d", ev.event_study_loop_b_results)

    def test_dibse_clipboard_telemetry_packet(self):
        spot_k, perp_k, fund_p = _generate_synthetic_4h_bars(240, 75000.0)
        ev = self.engine.calculate_evaluation(spot_k, perp_k, fund_p, 42.0)
        self.store.four_gate_evaluation = ev

        ok, msg, char_count = copy_four_gate_to_clipboard(self.store)
        self.assertTrue(ok)
        self.assertGreater(char_count, 500)

        report = build_tab_q_data_only_report(DEFAULT_CONFIG, self.store)
        self.assertIn("DIBSE CAPITAL SANDBOX ALLOCATION", report)
        self.assertIn("SWING LOOP A: USDT SLEEVE", report)
        self.assertIn("SWING LOOP B: BTC SLEEVE", report)
        self.assertIn("LOOP_A_TARGET_PRICE_USD", report)
        self.assertIn("LOOP_B_BUYBACK_PRICE_USD", report)
        self.assertIn("LOOP_B_FREE_SATOSHIS_BTC", report)



if __name__ == "__main__":
    unittest.main()
