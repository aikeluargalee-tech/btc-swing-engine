"""Offline unit tests for analytics/dibse_g1_validator.py."""

from __future__ import annotations

import math
from pathlib import Path
import sys
import tempfile
import unittest

import numpy as np

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from analytics.dibse_g1_validator import (
    DAY_MS,
    FOUR_HOURS_MS,
    ArchiveData,
    CausalSignalTable,
    align_closed_archives,
    compute_performance_metrics,
    compute_psr_dsr,
    extract_causal_signals,
    load_archive_npz,
    save_archive_npz,
    simulate_benchmarks,
    simulate_dibse_fsm,
)
from analytics.four_gate_engine import FourGateEngine


def _make_synthetic_payloads(
    n_bars: int = 260,
    start_ms: int = 1700006400000,  # aligned 4h boundary (00:00 UTC)
    seed: int = 42,
):
    rng = np.random.default_rng(seed)
    spot_rows = []
    perp_rows = []
    funding_rows = []

    price = 50000.0
    for i in range(n_bars):
        ts = start_ms + i * FOUR_HOURS_MS
        # Inject washout and euphoria segments to exercise gates
        drift = 0.0
        if 195 <= i <= 202:
            drift = -0.025
        elif 203 <= i <= 212:
            drift = 0.015
        elif 220 <= i <= 228:
            drift = 0.025
        elif 229 <= i <= 240:
            drift = -0.015
        ret = drift + float(rng.normal(0.0, 0.008))
        o = price
        c = max(1000.0, o * (1.0 + ret))
        h = max(o, c) * (1.0 + abs(float(rng.normal(0.0, 0.004))))
        l = min(o, c) * (1.0 - abs(float(rng.normal(0.0, 0.004))))
        vol = 1000.0 + float(rng.uniform(0.0, 500.0))
        buy_ratio = 0.55 if ret > 0 else 0.45
        if 200 <= i <= 205:
            buy_ratio = 0.65  # spot accumulation
        s_buy = vol * buy_ratio
        p_buy = vol * (0.40 if 200 <= i <= 205 else (0.65 if 224 <= i <= 230 else buy_ratio))

        spot_rows.append([ts, f"{o:.2f}", f"{h:.2f}", f"{l:.2f}", f"{c:.2f}", f"{vol:.2f}", ts + FOUR_HOURS_MS - 1, "0", 10, f"{s_buy:.2f}", "0", "0"])
        perp_rows.append([ts, f"{o:.2f}", f"{h:.2f}", f"{l:.2f}", f"{c:.2f}", f"{vol:.2f}", ts + FOUR_HOURS_MS - 1, "0", 10, f"{p_buy:.2f}", "0", "0"])
        price = c

        # 8H funding print every 2 bars
        if i % 2 == 0:
            fr = 0.0001 + float(rng.normal(0.0, 0.00005))
            if 196 <= i <= 204:
                fr = -0.00025  # negative flush
            elif 222 <= i <= 230:
                fr = 0.00035  # euphoric crowd
            funding_rows.append({"fundingTime": ts, "fundingRate": f"{fr:.6f}"})

    return spot_rows, perp_rows, funding_rows


class TestDibseG1Validator(unittest.TestCase):
    def test_signal_parity_with_four_gate_engine(self):
        spot_rows, perp_rows, funding_rows = _make_synthetic_payloads(n_bars=260)
        end_closed_ms = spot_rows[-1][0] + FOUR_HOURS_MS
        arch = align_closed_archives(spot_rows, perp_rows, funding_rows, now_ms=end_closed_ms)
        sig = extract_causal_signals(arch)
        engine = FourGateEngine()

        dummy_open_s = [spot_rows[-1][0] + FOUR_HOURS_MS, "1", "1", "1", "1", "1", 0, "0", 0, "0.5", "0", "0"]
        dummy_open_p = list(dummy_open_s)

        test_indices = [185, 190, 200, 202, 204, 210, 224, 228, 232, 245, 255, 259]
        for k in test_indices:
            bar_close_ms = int(arch.open_times[k]) + FOUR_HOURS_MS - 1
            causal_f = [f for f in funding_rows if int(f["fundingTime"]) <= bar_close_ms]
            ev = engine.calculate_evaluation(
                spot_rows[: k + 1] + [dummy_open_s],
                perp_rows[: k + 1] + [dummy_open_p],
                causal_f,
                dvol_current=50.0,
                equity_usd=100_000.0,
            )
            self.assertTrue(sig.valid_mask[k], f"k={k} should be valid")
            self.assertTrue(ev.raw_data_available, f"k={k} failed: {ev.error_message}")
            self.assertEqual(bool(sig.a_g1[k]), ev.loop_a_g1_levy, f"Loop A G1 mismatch at k={k}")
            self.assertEqual(bool(sig.a_g2[k]), ev.loop_a_g2_zflow, f"Loop A G2 mismatch at k={k}")
            self.assertEqual(bool(sig.a_g3[k]), ev.loop_a_g3_structure, f"Loop A G3 mismatch at k={k}")
            self.assertEqual(bool(sig.a_g4[k]), ev.loop_a_g4_positioning, f"Loop A G4 mismatch at k={k}")
            self.assertEqual(bool(sig.b_g1[k]), ev.loop_b_g1_levy, f"Loop B G1 mismatch at k={k}")
            self.assertEqual(bool(sig.b_g2[k]), ev.loop_b_g2_zflow, f"Loop B G2 mismatch at k={k}")
            self.assertEqual(bool(sig.b_g3[k]), ev.loop_b_g3_structure, f"Loop B G3 mismatch at k={k}")
            self.assertEqual(bool(sig.b_g4[k]), ev.loop_b_g4_positioning, f"Loop B G4 mismatch at k={k}")
            self.assertAlmostEqual(sig.poc_30[k], ev.gate_3_poc, places=7)
            self.assertAlmostEqual(sig.val_30[k], ev.gate_3_val, places=7)
            self.assertAlmostEqual(sig.vah_30[k], ev.gate_3_vah, places=7)

    def test_strict_causality_and_closed_alignment(self):
        spot_rows, perp_rows, funding_rows = _make_synthetic_payloads(n_bars=230)
        # Drop one perp bar to verify intersection alignment
        perp_dropped = perp_rows[:50] + perp_rows[51:]
        # Make final spot/perp bar unclosed
        last_ts = int(spot_rows[-1][0])
        now_ms = last_ts + FOUR_HOURS_MS - 1000
        arch_base = align_closed_archives(spot_rows, perp_dropped, funding_rows, now_ms=now_ms)
        self.assertNotIn(last_ts, arch_base.open_times)
        self.assertEqual(arch_base.meta["spot_only_dropped"], 1)
        sig_base = extract_causal_signals(arch_base)

        # Corrupt all future bars after index 205 in a copy
        mutated = ArchiveData(
            open_times=arch_base.open_times.copy(),
            opens=arch_base.opens.copy(),
            highs=arch_base.highs.copy(),
            lows=arch_base.lows.copy(),
            closes=arch_base.closes.copy(),
            s_vols=arch_base.s_vols.copy(),
            s_buys=arch_base.s_buys.copy(),
            p_vols=arch_base.p_vols.copy(),
            p_buys=arch_base.p_buys.copy(),
            spot_full_open_times=arch_base.spot_full_open_times.copy(),
            spot_full_closes=arch_base.spot_full_closes.copy(),
            fund_times=arch_base.fund_times.copy(),
            fund_rates=arch_base.fund_rates.copy(),
            meta=dict(arch_base.meta),
        )
        mutated.closes[206:] *= 5.0
        mutated.highs[206:] *= 6.0
        mutated.s_vols[206:] *= 20.0
        mutated.fund_rates[mutated.fund_times > arch_base.open_times[205] + FOUR_HOURS_MS - 1] = -0.05

        sig_mut = extract_causal_signals(mutated)
        np.testing.assert_array_equal(sig_base.a_g1[:206], sig_mut.a_g1[:206])
        np.testing.assert_array_equal(sig_base.a_g2[:206], sig_mut.a_g2[:206])
        np.testing.assert_array_equal(sig_base.a_g3[:206], sig_mut.a_g3[:206])
        np.testing.assert_array_equal(sig_base.a_g4[:206], sig_mut.a_g4[:206])
        np.testing.assert_array_equal(sig_base.b_g1[:206], sig_mut.b_g1[:206])
        np.testing.assert_array_equal(sig_base.b_g2[:206], sig_mut.b_g2[:206])
        np.testing.assert_array_equal(sig_base.b_g3[:206], sig_mut.b_g3[:206])
        np.testing.assert_array_equal(sig_base.b_g4[:206], sig_mut.b_g4[:206])
        np.testing.assert_allclose(sig_base.poc_30[:206], sig_mut.poc_30[:206])

    def test_split_sleeve_fsm_watermark_no_stoploss_and_fee_stress(self):
        # Controlled price path: Loop A buys at 100, endures 50% crash WITHOUT stop-loss, exits at 110;
        # Loop B sells at 120, endures rally to 150 WITHOUT stop-buy, rebuys at 105 (gaining BTC units).
        N = 40
        start_ms = 1700006400000
        open_times = np.array([start_ms + i * FOUR_HOURS_MS for i in range(N)], dtype=np.int64)
        closes = np.full(N, 100.0, dtype=np.float64)
        # Sleeve A sequence
        closes[2] = 100.0   # Loop A trigger -> buy @ 100 (target defaults to 104 when close >= poc*0.98)
        closes[5:10] = 50.0 # Deep underwater crash -> must NOT stop out
        closes[12] = 110.0  # Loop A profitable exit @ 110 (>= 104)
        # Sleeve B sequence
        closes[15] = 120.0  # Loop B sell @ 120 (buyback defaults to 120*0.96 = 115.2 if poc/val not matched)
        closes[18:22] = 150.0  # Rally above sell price -> must stay parked in USDT without stop-buy
        closes[25] = 105.0  # Pullback -> Loop B rebuys BTC @ 105 (< 115.2)

        arch = ArchiveData(
            open_times=open_times,
            opens=closes.copy(),
            highs=closes.copy(),
            lows=closes.copy(),
            closes=closes.copy(),
            s_vols=np.ones(N),
            s_buys=np.full(N, 0.5),
            p_vols=np.ones(N),
            p_buys=np.full(N, 0.5),
            spot_full_open_times=open_times,
            spot_full_closes=closes,
            fund_times=np.array([start_ms]),
            fund_rates=np.array([0.0]),
        )
        f = np.zeros(N, dtype=bool)
        sig = CausalSignalTable(
            valid_mask=np.ones(N, dtype=bool),
            a_g1=f.copy(),
            a_g2=f.copy(),
            a_g3=f.copy(),
            a_g4=f.copy(),
            b_g1=f.copy(),
            b_g2=f.copy(),
            b_g3=f.copy(),
            b_g4=f.copy(),
            poc_30=np.full(N, 100.0),
            val_30=np.full(N, 99.0),
            vah_30=np.full(N, 101.0),
        )
        sig.a_g1[2] = sig.a_g2[2] = sig.a_g3[2] = sig.a_g4[2] = True
        sig.b_g1[15] = sig.b_g2[15] = sig.b_g3[15] = sig.b_g4[15] = True

        res_1x = simulate_dibse_fsm(arch, sig, start_bar=0, cost_bps=10.0, init_capital=20_000.0)
        res_2x = simulate_dibse_fsm(arch, sig, start_bar=0, cost_bps=20.0, init_capital=20_000.0)

        d = res_1x.diagnostics
        self.assertEqual(d["a_entries"], 1)
        self.assertEqual(d["a_completed"], 1)
        self.assertFalse(d["a_open_end"])
        self.assertGreater(d["a_final_usd"], 10_950.0)  # +10% minus 2x10bps fee

        self.assertEqual(d["b_sells"], 1)
        self.assertEqual(d["b_completed"], 1)
        self.assertFalse(d["b_open_end"])
        self.assertGreater(d["b_btc_alpha_pct"], 13.0)  # 120/105 - 1 minus fees (~14.0%)

        # Higher transaction costs strictly reduce ending equity when trades execute
        self.assertLess(res_2x.diagnostics["final_equity_usd"], d["final_equity_usd"])
        self.assertGreater(res_2x.diagnostics["total_fees_usd"], d["total_fees_usd"])

    def test_benchmarks_accounting_invariants(self):
        # Daily grid for 240 days so Detzel 200d SMA is active
        n_days = 240
        n_bars = n_days * 6
        start_ms = 1700006400000
        open_times = np.array([start_ms + i * FOUR_HOURS_MS for i in range(n_bars)], dtype=np.int64)
        # First 200 days flat at 100; then doubles to 200 for days 200..239
        closes = np.full(n_bars, 100.0, dtype=np.float64)
        closes[200 * 6 :] = 200.0

        arch = ArchiveData(
            open_times=open_times,
            opens=closes.copy(),
            highs=closes.copy(),
            lows=closes.copy(),
            closes=closes.copy(),
            s_vols=np.ones(n_bars),
            s_buys=np.full(n_bars, 0.5),
            p_vols=np.ones(n_bars),
            p_buys=np.full(n_bars, 0.5),
            spot_full_open_times=open_times,
            spot_full_closes=closes,
            fund_times=np.array([start_ms]),
            fund_rates=np.array([0.0]),
        )
        start_bar = 200 * 6
        benches = {b.name: b for b in simulate_benchmarks(arch, start_bar=start_bar, cost_bps=10.0, init_capital=20_000.0)}

        # Start price at bar start_bar is 200.0, ending price is 200.0 -> zero move in [start_bar:]
        self.assertAlmostEqual(benches["BENCH_BH_100_BTC"].diagnostics["final_equity_usd"], 20_000.0)
        self.assertAlmostEqual(benches["BENCH_50_50_HOLD"].diagnostics["final_equity_usd"], 20_000.0)
        # Verify Detzel 200d SMA triggers entry once price steps to 200 above ~100 SMA
        self.assertEqual(benches["BENCH_DETZEL_200D_SMA"].diagnostics["switches"], 1)

        # Now start at day 195 so start price is 100 and ends at 200 (doubles!)
        benches_double = {b.name: b for b in simulate_benchmarks(arch, start_bar=195 * 6, cost_bps=10.0, init_capital=20_000.0)}
        self.assertAlmostEqual(benches_double["BENCH_BH_100_BTC"].diagnostics["final_equity_usd"], 40_000.0)
        self.assertAlmostEqual(benches_double["BENCH_50_50_HOLD"].diagnostics["final_equity_usd"], 30_000.0)
        self.assertEqual(benches_double["BENCH_50_50_REBAL_5PCT"].diagnostics["rebalances"], 1)

    def test_psr_dsr_and_npz_roundtrip(self):
        rng = np.random.default_rng(7)
        d_rets = np.full(365, 0.002) + rng.normal(0.0, 0.005, size=365)
        eq = 20_000.0 * np.cumprod(np.concatenate(([1.0], 1.0 + d_rets)))
        days = np.array([1700006400000 + i * DAY_MS for i in range(len(eq))], dtype=np.int64)
        metrics = compute_performance_metrics(days, eq)
        self.assertGreater(metrics["sharpe"], 2.0)
        self.assertLessEqual(metrics["max_dd_pct"], 0.0)

        psr_single, dsr_single, _ = compute_psr_dsr(d_rets, [metrics["sharpe"]])
        psr_multi, dsr_multi, sr0 = compute_psr_dsr(d_rets, [metrics["sharpe"], 0.5, -0.3, 1.1, 3.0])
        self.assertGreater(psr_single, 0.99)
        self.assertAlmostEqual(psr_single, dsr_single, places=9)
        self.assertGreater(sr0, 0.0)
        self.assertLess(dsr_multi, psr_multi)

        spot_rows, perp_rows, funding_rows = _make_synthetic_payloads(n_bars=50)
        arch = align_closed_archives(spot_rows, perp_rows, funding_rows, now_ms=spot_rows[-1][0] + FOUR_HOURS_MS)
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir) / "test_cache.npz"
            save_archive_npz(arch, p)
            loaded = load_archive_npz(p)
            np.testing.assert_array_equal(arch.open_times, loaded.open_times)
            np.testing.assert_allclose(arch.closes, loaded.closes)
            np.testing.assert_array_equal(arch.fund_times, loaded.fund_times)
            self.assertEqual(arch.meta["aligned_bars"], loaded.meta["aligned_bars"])


if __name__ == "__main__":
    unittest.main()
