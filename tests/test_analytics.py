"""Unit tests for Volume Profile topology, Multi-Horizon CVD normalization, and the 4-Gate FSM."""

from dataclasses import replace
from pathlib import Path
import tempfile
import unittest
from typing import List

from analytics.cvd_engine import compute_derivatives_snapshot, compute_flow_snapshot
from analytics.signal_detector import SignalDetector
from analytics.volume_profile import compute_atr, compute_composite_profile, synthesize_4h_bars
from config.settings import DEFAULT_CONFIG
from core.models import ExecutionGateState, KlineBar, MarketRegime
from core.state_store import StateStore

TEST_CONFIG = replace(
    DEFAULT_CONFIG,
    signal_log_path=Path(tempfile.gettempdir()) / "btc_swing_test_signals.jsonl",
)


def _generate_synthetic_consolidation_bars(count: int = 240) -> List[KlineBar]:
    """Generates a realistic smooth consolidation range centered at $90,000 with cVAL ~$88,200."""
    bars: List[KlineBar] = []
    base_ts = 1_720_000_000_000
    # Smooth multi-bar blocks across the auction range so 1H ATR (~$250) << (cPOC - cVAL) (~$1,800)
    schedule = (
        [-3500.0] * 15
        + [2800.0] * 15
        + [1800.0] * 25
        + [900.0] * 35
        + [0.0] * 90
        + [-1800.0] * 25
        + [-900.0] * 35
    )

    for i in range(count):
        ts = base_ts + i * 3_600_000
        offset = schedule[i % len(schedule)]
        center = 90_000.0 + offset
        vol = 400.0 if abs(offset) <= 900.0 else 180.0

        bars.append(
            KlineBar(
                timestamp_ms=ts,
                open=center - 60.0,
                high=center + 120.0,
                low=center - 120.0,
                close=center + 60.0,
                volume=vol,
                taker_buy_volume=vol * 0.50,
            )
        )
    return bars


class TestBTCAnalyticsEngine(unittest.TestCase):
    """Verifies Volume Profile math, CVD Z-scores, Absorption Index, and 4-Gate State Machine."""

    def test_composite_volume_profile_geometry(self) -> None:
        bars = _generate_synthetic_consolidation_bars(240)
        vp = compute_composite_profile(bars, horizon_label="Test 10D", num_bins=100)
        self.assertIsNotNone(vp)
        assert vp is not None

        self.assertGreater(vp.c_vah, vp.c_poc)
        self.assertGreaterEqual(vp.c_poc, vp.c_val)
        self.assertAlmostEqual(vp.c_poc, 90_000.0, delta=600.0)
        self.assertIsNotNone(vp.primary_lvn_below_val)
        assert vp.primary_lvn_below_val is not None
        self.assertLess(vp.primary_lvn_below_val, vp.c_val)

    def test_synthesize_4h_and_atr(self) -> None:
        bars = _generate_synthetic_consolidation_bars(48)
        bars_4h = synthesize_4h_bars(bars)
        self.assertGreaterEqual(len(bars_4h), 12)
        atr_1h = compute_atr(bars, period=14)
        self.assertGreater(atr_1h, 100.0)

    def test_passive_absorption_and_reclaim_signal(self) -> None:
        """Simulates a cVAL sweep where Spot CVD buys aggressively while Perp CVD shorts into limit bids."""
        store = StateStore()
        spot_1h = _generate_synthetic_consolidation_bars(240)
        perp_1h = _generate_synthetic_consolidation_bars(240)

        vp = compute_composite_profile(spot_1h, num_bins=120)
        assert vp is not None
        c_val = vp.c_val

        # Inject a sweep below cVAL and reclaim close >= cVAL on the final 1H bar:
        # Spot has strong net buying (taker_buy = 85%), while Perp has heavy net selling (taker_buy = 15%)
        last_ts = spot_1h[-1].timestamp_ms + 3_600_000
        spot_1h.append(
            KlineBar(
                timestamp_ms=last_ts,
                open=c_val + 50.0,
                high=c_val + 180.0,
                low=c_val - 350.0,
                close=c_val + 40.0,
                volume=600.0,
                taker_buy_volume=510.0,
            )
        )
        perp_1h.append(
            KlineBar(
                timestamp_ms=last_ts,
                open=c_val + 50.0,
                high=c_val + 180.0,
                low=c_val - 350.0,
                close=c_val + 40.0,
                volume=2400.0,
                taker_buy_volume=360.0,
            )
        )

        # Populate 15m buffers mirroring the absorption & reclaim
        spot_15m = [
            KlineBar(
                timestamp_ms=last_ts - (80 - k) * 900_000,
                open=c_val,
                high=c_val + 100.0,
                low=c_val - 250.0 if k >= 78 else c_val - 50.0,
                close=c_val + 40.0,
                volume=150.0,
                taker_buy_volume=125.0 if k >= 76 else (75.0 + (k % 3 - 1) * 5.0),
            )
            for k in range(80)
        ]
        perp_15m = [
            KlineBar(
                timestamp_ms=last_ts - (80 - k) * 900_000,
                open=c_val,
                high=c_val + 100.0,
                low=c_val - 250.0 if k >= 78 else c_val - 50.0,
                close=c_val + 40.0,
                volume=600.0,
                taker_buy_volume=110.0 if k >= 76 else (300.0 + (k % 3 - 1) * 15.0),
            )
            for k in range(80)
        ]

        store.spot_klines_1h.extend(spot_1h)
        store.perp_klines_1h.extend(perp_1h)
        store.spot_klines_15m.extend(spot_15m)
        store.perp_klines_15m.extend(perp_15m)

        store.binance_spot_price = c_val + 40.0
        store.binance_perp_price = c_val + 25.0
        store.coinbase_spot_price = c_val + 95.0  # Positive Coinbase Premium
        for k in range(20):
            store.cpi_history.append((1000.0 + k * 10, 0.01))
        store.cpi_history.append((1300.0, 0.065))

        # Simulate OI liquidation flush (-3.0% over 4H) and negative funding
        store.record_oi_sample(100_000.0, ts_sec=1000.0)
        store.record_oi_sample(97_000.0, ts_sec=15_400.0)
        store.funding_rate_pct = -0.004

        detector = SignalDetector(TEST_CONFIG)
        ev = detector.evaluate(store)
        self.assertIsNotNone(ev)
        assert ev is not None

        self.assertEqual(ev.regime, MarketRegime.ABSORPTION_AT_SUPPORT, msg=str(ev.to_dict()))
        self.assertEqual(ev.gate_state, ExecutionGateState.GATE3_RECLAIM_TRIGGERED)
        self.assertGreaterEqual(ev.confluence_score, 75.0)
        self.assertFalse(ev.hard_veto_triggered)
        self.assertIsNotNone(ev.trade_plan)
        assert ev.trade_plan is not None
        self.assertGreaterEqual(ev.trade_plan.rr_to_poc, 1.5)

    def test_leveraged_bounce_trap_veto(self) -> None:
        """Verifies that a Perp-driven bounce with surging OI and negative Spot delta triggers LEVERAGE_TRAP veto."""
        store = StateStore()
        spot_1h = _generate_synthetic_consolidation_bars(240)
        perp_1h = _generate_synthetic_consolidation_bars(240)
        vp = compute_composite_profile(spot_1h, num_bins=120)
        assert vp is not None
        c_val = vp.c_val

        last_ts = spot_1h[-1].timestamp_ms
        # Spot is selling while Perp is aggressively market-buying on surging OI
        spot_15m = [
            KlineBar(
                timestamp_ms=last_ts - (80 - k) * 900_000,
                open=c_val,
                high=c_val + 300.0,
                low=c_val - 20.0,
                close=c_val + 250.0 if k >= 76 else c_val,
                volume=150.0,
                taker_buy_volume=35.0 if k >= 76 else (75.0 + (k % 3 - 1) * 5.0),
            )
            for k in range(80)
        ]
        perp_15m = [
            KlineBar(
                timestamp_ms=last_ts - (80 - k) * 900_000,
                open=c_val,
                high=c_val + 300.0,
                low=c_val - 20.0,
                close=c_val + 250.0 if k >= 76 else c_val,
                volume=600.0,
                taker_buy_volume=520.0 if k >= 76 else (300.0 + (k % 3 - 1) * 15.0),
            )
            for k in range(80)
        ]

        store.spot_klines_1h.extend(spot_1h)
        store.perp_klines_1h.extend(perp_1h)
        store.spot_klines_15m.extend(spot_15m)
        store.perp_klines_15m.extend(perp_15m)
        store.binance_spot_price = c_val + 250.0
        store.binance_perp_price = c_val + 290.0
        store.coinbase_spot_price = c_val + 210.0

        # Simulate +1.8% 1H OI surge
        store.record_oi_sample(100_000.0, ts_sec=1000.0)
        store.record_oi_sample(101_800.0, ts_sec=4600.0)

        detector = SignalDetector(TEST_CONFIG)
        ev = detector.evaluate(store)
        self.assertIsNotNone(ev)
        assert ev is not None
        self.assertEqual(ev.regime, MarketRegime.LEVERAGE_TRAP)
        self.assertTrue(ev.hard_veto_triggered)

    def test_initiative_markdown_cash_mandate(self) -> None:
        """Verifies that multi-4H acceptance below cVAL with Spot selling triggers MARKDOWN / CASH_MARKDOWN."""
        store = StateStore()
        spot_1h = _generate_synthetic_consolidation_bars(240)
        perp_1h = _generate_synthetic_consolidation_bars(240)
        vp = compute_composite_profile(spot_1h, num_bins=120)
        assert vp is not None
        c_val = vp.c_val

        # Append 8 hours (two 4H bars) accepted well below cVAL with heavy Spot selling
        base_ts = spot_1h[-1].timestamp_ms
        for h in range(1, 9):
            dump_p = c_val - 1200.0 - h * 50.0
            bar = KlineBar(
                timestamp_ms=base_ts + h * 3_600_000,
                open=dump_p + 80.0,
                high=dump_p + 100.0,
                low=dump_p - 100.0,
                close=dump_p,
                volume=500.0,
                taker_buy_volume=120.0,
            )
            spot_1h.append(bar)
            perp_1h.append(bar)

        store.spot_klines_1h.extend(spot_1h)
        store.perp_klines_1h.extend(perp_1h)
        store.spot_klines_15m.extend(spot_1h[-80:])
        store.perp_klines_15m.extend(perp_1h[-80:])
        store.binance_spot_price = c_val - 1600.0
        store.coinbase_spot_price = c_val - 1680.0  # Negative Coinbase Premium

        detector = SignalDetector(TEST_CONFIG)
        ev = detector.evaluate(store)
        self.assertIsNotNone(ev)
        assert ev is not None
        self.assertEqual(ev.regime, MarketRegime.MARKDOWN)
        self.assertEqual(ev.gate_state, ExecutionGateState.CASH_MARKDOWN)
        self.assertTrue(ev.hard_veto_triggered)

    def test_protocol_v13_coinglass_and_ntz_8c_veto(self) -> None:
        """Verifies Tab [2] Protocol v1.3 CoinGlass 6-panel audit and 8C Non-Trade Zone master veto."""
        store = StateStore()
        spot_1h = _generate_synthetic_consolidation_bars(240)
        perp_1h = _generate_synthetic_consolidation_bars(240)

        # Simulate falling price on last 4H with positive funding and rising OI (triggers 8C NTZ)
        for idx in range(-4, 0):
            spot_1h[idx].close = spot_1h[idx].open - 450.0
            perp_1h[idx].close = perp_1h[idx].open - 450.0

        store.spot_klines_1h.extend(spot_1h)
        store.perp_klines_1h.extend(perp_1h)
        store.spot_klines_15m.extend(spot_1h[-80:])
        store.perp_klines_15m.extend(perp_1h[-80:])
        store.binance_spot_price = spot_1h[-1].close
        store.binance_perp_price = perp_1h[-1].close
        store.coinbase_spot_price = spot_1h[-1].close

        # Positive funding (+0.015%) + rising OI (+1.2%) + falling price -> 8C TRIGGERED
        store.funding_rate_pct = 0.015
        store.record_oi_sample(92_000.0, ts_sec=1000.0)
        store.record_oi_sample(93_100.0, ts_sec=4600.0)

        detector = SignalDetector(TEST_CONFIG)
        ev = detector.evaluate(store)
        self.assertIsNotNone(ev)
        assert ev is not None

        pev = store.protocol_evaluation
        self.assertIsNotNone(pev)
        assert pev is not None
        self.assertEqual(len(pev.coinglass_rows), 6)
        self.assertIn("BTC", pev.coinglass_rows[3].value_1d)
        self.assertEqual(pev.non_trade_zone_status, "YES")
        self.assertEqual(pev.buy_allowed, "NO")
        # Verify Liquidation Magnet & Range Pivot Protocol (T1 + T2)
        self.assertGreater(pev.short_liq_magnet_usd, pev.current_price)
        self.assertLess(pev.long_liq_magnet_usd, pev.current_price)
        self.assertGreater(pev.sma_50_1d, 0.0)
        self.assertGreater(pev.range_pivot_usd, 0.0)
        self.assertTrue(len(pev.liq_magnet_verdict) > 0)
        # Master veto propagated to Tab [1]
        self.assertTrue(ev.hard_veto_triggered)
        self.assertTrue(any("Protocol v1.3 [8C]" in r for r in ev.veto_reasons))

    def test_macro_radar_200d_gatekeeper_and_crash_rungs(self) -> None:
        """Verifies Tab [3] 1D 200 SMA Gatekeeper, 14D Wilder RSI, Crash Rungs, and 0.5% risk cap."""
        store = StateStore()
        spot_1h = _generate_synthetic_consolidation_bars(240)
        perp_1h = _generate_synthetic_consolidation_bars(240)
        store.spot_klines_1h.extend(spot_1h)
        store.perp_klines_1h.extend(perp_1h)
        store.spot_klines_15m.extend(spot_1h[-80:])
        store.perp_klines_15m.extend(perp_1h[-80:])

        # Seed 255x 1D bars where 200D SMA is ~$95,000 and current price is $78,000 (-28.8% from $109,588 ATH)
        base_day_ts = 1_700_000_000_000
        for d in range(255):
            p = 96_000.0 if d < 220 else 78_000.0
            store.spot_klines_1d.append(
                KlineBar(
                    timestamp_ms=base_day_ts + d * 86_400_000,
                    open=p + 200.0,
                    high=109_588.0 if d == 100 else p + 500.0,
                    low=p - 500.0,
                    close=p,
                    volume=12_000.0,
                    taker_buy_volume=6_000.0,
                )
            )
        store.binance_spot_price = 78_000.0
        store.coinbase_spot_price = 78_050.0

        detector = SignalDetector(TEST_CONFIG)
        ev = detector.evaluate(store)
        self.assertIsNotNone(ev)
        assert ev is not None

        mev = store.macro_evaluation
        self.assertIsNotNone(mev)
        assert mev is not None
        self.assertTrue(mev.gatekeeper_veto)
        self.assertFalse(mev.above_200d_sma)
        self.assertEqual(len(mev.crash_rungs), 5)
        self.assertEqual(mev.crash_rungs[0].status, "HIT / ACTIVE")  # -25% Rung 1 hit at $78k
        # Verify Power-Law Long-Horizon Discount Row (Bias Only — Not Timing)
        self.assertGreater(mev.power_law_fair_usd, 100_000.0)
        self.assertLess(mev.power_law_discount_pct, -35.0)
        self.assertIn("[BIAS ONLY]", mev.power_law_zone_label)
        # Verify Two-Tier Counter-Trend 0.5% Risk Cap on Tab [1] TradePlan
        assert ev.trade_plan is not None
        self.assertAlmostEqual(ev.trade_plan.risk_pct, 0.5)

    def test_regime_matrix_a_through_j_and_world_clock(self) -> None:
        """Verifies Tab [4] Regime Matrix Configurations A-J evaluation and World Clock session helper."""
        from datetime import datetime, timezone
        from ui.terminal_hud import _get_world_clocks_and_session

        store = StateStore()
        spot_1h = _generate_synthetic_consolidation_bars(240)
        perp_1h = _generate_synthetic_consolidation_bars(240)
        store.spot_klines_1h.extend(spot_1h)
        store.perp_klines_1h.extend(perp_1h)
        store.spot_klines_15m.extend(spot_1h[-80:])
        store.perp_klines_15m.extend(perp_1h[-80:])

        base_day_ts = 1_700_000_000_000
        for d in range(255):
            p = 94_000.0 + d * 10.0
            store.spot_klines_1d.append(
                KlineBar(
                    timestamp_ms=base_day_ts + d * 86_400_000,
                    open=p - 100.0,
                    high=p + 400.0,
                    low=p - 400.0,
                    close=p,
                    volume=10_000.0,
                    taker_buy_volume=5_600.0,
                )
            )
        store.binance_spot_price = spot_1h[-1].close
        store.binance_perp_price = perp_1h[-1].close
        store.coinbase_spot_price = spot_1h[-1].close + 25.0

        detector = SignalDetector(TEST_CONFIG)
        # Set price right at cPOC (50% of Value Area) to verify Explicit Mid-Range Chop Filter
        vp_test = compute_composite_profile(spot_1h, num_bins=120)
        assert vp_test is not None
        store.binance_spot_price = (vp_test.c_val + vp_test.c_vah) / 2.0
        ev = detector.evaluate(store)
        self.assertIsNotNone(ev)
        assert ev is not None
        self.assertTrue(ev.is_mid_range_chop)
        self.assertAlmostEqual(ev.va_position_pct, 50.0, delta=1.0)
        self.assertLessEqual(ev.location_score, 6.0)

        rm = store.regime_matrix_evaluation
        self.assertIsNotNone(rm)
        assert rm is not None
        self.assertEqual(len(rm.configs), 10)
        self.assertEqual(
            [c.code for c in rm.configs],
            ["Config A", "Config B", "Config C", "Config D", "Config E", "Config F", "Config G", "Config H", "Config I", "Config J"],
        )
        self.assertTrue(rm.active_config_code.startswith("Config "))
        self.assertGreater(rm.daily_vwap, 0.0)
        self.assertGreater(rm.weekly_vwap, 0.0)

        # Verify World Clock & Active Session detection (e.g., 14:30 UTC -> London / NY Overlap)
        dt_overlap = datetime(2026, 10, 27, 14, 30, 0, tzinfo=timezone.utc)
        clocks_str, session_label = _get_world_clocks_and_session(dt_overlap)
        self.assertIn("22:30:00 SGT", clocks_str)
        self.assertIn("14:30:00 GMT", clocks_str)
        self.assertIn("10:30:00 EDT", clocks_str)
        self.assertIn("LONDON / NY OVERLAP", session_label)

        # Verify Tab [0] Master Synthesis & Supreme Order of Battle Evaluation + Renderable
        from ui.terminal_hud import build_dashboard_renderable

        msev = store.master_synthesis_evaluation
        self.assertIsNotNone(msev)
        assert msev is not None
        self.assertEqual(len(msev.tab_rows), 8)
        self.assertEqual(len(msev.hierarchy_rows), 4)
        self.assertGreaterEqual(msev.master_alignment_score, 0.0)
        self.assertLessEqual(msev.master_alignment_score, 100.0)
        self.assertGreater(msev.holder_hard_stop_usd, 0.0)
        self.assertGreater(msev.holder_tp1_usd, 0.0)
        self.assertGreater(msev.holder_tp2_usd, msev.holder_tp1_usd)
        self.assertIn(msev.master_traffic_light, ("GREEN", "BLUE", "YELLOW", "RED"))

        renderable_tab0 = build_dashboard_renderable(TEST_CONFIG, store, tab_override=0)
        self.assertIsNotNone(renderable_tab0)
        renderable_tab5 = build_dashboard_renderable(TEST_CONFIG, store, tab_override=5)
        self.assertIsNotNone(renderable_tab5)

        # Verify Raw AI Telemetry Packet Builder (Hotkey 'C' on Tab [0])
        from analytics.ai_packet_exporter import build_ai_telemetry_packet

        ai_packet = build_ai_telemetry_packet(TEST_CONFIG, store)
        self.assertIn("SECTION 1: CROSS-EXCHANGE SPOT, BASIS & DERIVATIVES TELEMETRY", ai_packet)
        self.assertIn("SECTION 2: COMPOSITE VOLUME PROFILE & MULTI-HORIZON ORDER FLOW", ai_packet)
        self.assertIn("SECTION 3: PROTOCOL v1.3, COINGLASS 6-PANEL (BTC) & LIQUIDATION MAGNETS", ai_packet)
        self.assertIn("SECTION 4: MACRO QUANT, POWER-LAW & CYCLE RADAR", ai_packet)
        self.assertIn("SECTION 5: QUANTITATIVE MICROSTRUCTURE MATRIX A–J SCORES", ai_packet)
        self.assertIn("SECTION 6: PYTHON ENGINE BENCHMARK VERDICT", ai_packet)
        self.assertIn("6A. Panel 1 — 9-Desk Executive Verdict Rollup Matrix", ai_packet)
        self.assertIn("6B. Panel 2 — 4-Layer Institutional Decision Funnel", ai_packet)
        self.assertIn("6C. Panel 3 — Cross-Tab Agreement, Conflict Diagnostic & Flip Catalysts", ai_packet)
        self.assertIn("6D. Panel 4 — Unified Master Order of Battle", ai_packet)
        self.assertIn("6E. Panel 5 — Executive Bottom Line", ai_packet)
        self.assertIn(msev.master_headline, ai_packet)
        self.assertIn(msev.master_what_is_happening, ai_packet)
        self.assertIn(msev.master_why_resolution, ai_packet)
        self.assertIn(msev.master_final_command, ai_packet)


if __name__ == "__main__":
    unittest.main()
