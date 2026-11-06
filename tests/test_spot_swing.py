"""Unit tests for Tab [0]: BTC Spot Swing Screening & Alert Engine (Modules A-E) and Tab [L] routing."""

import contextlib
import io
import json
import math
import os
import re
import tempfile
import unittest
import urllib.error
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from unittest import mock

import pandas as pd
from rich.console import Console

from analytics.spot_swing_engine import (
    TF_1D_MS,
    TF_1H_MS,
    TF_4H_MS,
    SpotSwingEngine,
    advance_trade,
    bars_to_frame,
    build_closed_4h_from_1h,
    compute_macro_gate,
    compute_risk,
    compute_weekly_anchors,
    current_week_start_ms,
    detect_setup,
    finalized_bars,
    is_series_fresh,
    load_state,
    save_state,
)
from analytics.spot_swing_notifier import SpotSwingNotifier, format_telegram_message
from config.settings import DEFAULT_CONFIG
from core.models import KlineBar, SpotSwingSetup, SpotSwingTrade
from core.state_store import StateStore
from ui import terminal_hud
from ui.terminal_hud import build_dashboard_renderable, print_dry_run_report

# Wednesday 2026-10-28 12:00:30 UTC. Current week starts Mon 10-26; previous week is Mon 10-19 .. Sun 10-25.
NOW = datetime(2026, 10, 28, 12, 0, 30, tzinfo=timezone.utc)
NOW_MS = int(NOW.timestamp() * 1000)
PWL_T = 100_000.0
PWH_T = 108_000.0
N_4H = 190

CONFIG = replace(DEFAULT_CONFIG, spot_swing_account_equity_usd=10_000.0)


# ----------------------------------------------------------------------------
# Synthetic data builders
# ----------------------------------------------------------------------------

def _bar(ts: int, o: float, h: float, l: float, c: float, v: float) -> KlineBar:
    return KlineBar(timestamp_ms=ts, open=o, high=h, low=l, close=c, volume=v, taker_buy_volume=v * 0.5)


def make_daily_bars(
    drift: float = 0.0015,
    early_noise: float = 0.03,
    late_noise: float = 0.002,
    n_closed: int = 262,
    jump_last: float = 0.0,
) -> List[KlineBar]:
    """Closed daily bars up to Tue 10-27 plus the forming 10-28 bar. Prev-week lows/highs are pinned."""
    forming_ts = int(datetime(2026, 10, 28, tzinfo=timezone.utc).timestamp() * 1000)
    n_total = n_closed + 1
    p_end = 102_000.0
    cur_week = current_week_start_ms(NOW_MS)
    prev_week = cur_week - 7 * TF_1D_MS
    bars: List[KlineBar] = []
    for i in range(n_total):
        ts = forming_ts - (n_total - 1 - i) * TF_1D_MS
        amp = late_noise if i >= n_total - 36 else early_noise
        noise = amp * math.sin(i * 1.9) + amp * 0.6 * math.cos(i * 0.77)
        close = p_end * (1.0 + drift) ** (i - (n_total - 2)) * (1.0 + noise)
        if jump_last and i == n_total - 2:
            close *= 1.0 + jump_last
        high, low = close * 1.01, close * 0.99
        if prev_week <= ts < cur_week:
            k = (ts - prev_week) // TF_1D_MS  # 0..6, Monday..Sunday
            low = PWL_T + 700.0 * abs(k - 1)  # Tuesday 10-20 holds the exact PWL
            high = PWH_T - 300.0 * abs(k - 3)  # Thursday 10-22 holds the exact PWH
        bars.append(_bar(ts, close, high, low, close, 50_000.0))
    return bars


def four_hour_rows(kind: str = "signal") -> List[Tuple[int, float, float, float, float, float]]:
    """(ts, o, h, l, c, v) rows ending with the 08:00 UTC bucket of 10-28 (the last CLOSED 4H bar at NOW)."""
    last_ts = int(datetime(2026, 10, 28, 8, tzinfo=timezone.utc).timestamp() * 1000)
    rows = []
    for i in range(N_4H):
        ts = last_ts - (N_4H - 1 - i) * TF_4H_MS
        p = 102_500.0 + 150.0 * math.sin(i * 0.7)
        rows.append([ts, p, p + 300.0, p - 300.0, p + 50.0, 100.0 + 10.0 * (i % 3)])
    if kind in ("signal", "sweep_no_reclaim", "sweep_low_volume"):
        t = [r[0] for r in rows[-4:]]
        rows[-4] = [t[0], 102_000.0, 102_100.0, 99_200.0, 100_300.0, 130.0]
        rows[-3] = [t[1], 100_300.0, 101_000.0, 100_200.0, 100_800.0, 100.0]
        rows[-2] = [t[2], 100_800.0, 101_100.0, 100_500.0, 100_900.0, 100.0]
        rows[-1] = [t[3], 100_900.0, 101_400.0, 100_600.0, 101_200.0, 160.0]
        if kind == "sweep_no_reclaim":
            rows[-1] = [t[3], 100_900.0, 101_000.0, 99_500.0, 99_800.0, 160.0]
        if kind == "sweep_low_volume":
            rows[-1][5] = 90.0
    return [tuple(r) for r in rows]


def explode_to_1h(rows: List[Tuple[int, float, float, float, float, float]], forming_1h_ts: int) -> List[KlineBar]:
    """Four hourly bars per 4H row that aggregate back to exactly the row (+ one forming 1H bar)."""
    out: List[KlineBar] = []
    for ts, o, h, l, c, v in rows:
        q = v / 4.0
        out.append(_bar(ts, o, o, o, o, q))
        out.append(_bar(ts + TF_1H_MS, o, o, l, l, q))
        out.append(_bar(ts + 2 * TF_1H_MS, l, h, l, h, q))
        out.append(_bar(ts + 3 * TF_1H_MS, h, h, min(h, c), c, q))
    out.append(_bar(forming_1h_ts, out[-1].close, out[-1].close, out[-1].close, out[-1].close, 1.0))
    return out


def make_store(
    kind: str = "signal",
    daily: Optional[List[KlineBar]] = None,
    extra_rows: Optional[List[Tuple[int, float, float, float, float, float]]] = None,
    price: float = 101_300.0,
) -> StateStore:
    rows = four_hour_rows(kind) + (extra_rows or [])
    forming = rows[-1][0] + TF_4H_MS
    store = StateStore()
    store.spot_klines_1d.extend(daily if daily is not None else make_daily_bars())
    store.spot_klines_1h.extend(explode_to_1h(rows, forming))
    store.binance_spot_price = price
    return store


class FakeNotifier(SpotSwingNotifier):
    """Captures dispatched payloads and pretends a channel is configured."""

    def __init__(self) -> None:
        super().__init__(webhook_url="https://example.invalid/hook", synchronous=True)
        self.sent: List[Dict[str, Any]] = []

    def dispatch(self, payload: Dict[str, Any]) -> None:
        self.sent.append(payload)


def _frame(kind: str = "signal") -> pd.DataFrame:
    rows = four_hour_rows(kind)
    return pd.DataFrame(rows, columns=["ts", "open", "high", "low", "close", "volume"])


class SpotSwingBase(unittest.TestCase):
    def setUp(self) -> None:
        os.environ.pop("SPOT_SWING_EQUITY_USD", None)
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.state_path = Path(self._tmp.name) / "spot_swing_state.json"

    def engine(self, notifier: Optional[FakeNotifier] = None, read_only: bool = False) -> SpotSwingEngine:
        return SpotSwingEngine(CONFIG, notifier=notifier or FakeNotifier(), state_path=self.state_path, read_only=read_only)


# ----------------------------------------------------------------------------
# Module A: data hygiene
# ----------------------------------------------------------------------------

class TestDataHygiene(unittest.TestCase):
    def test_finalized_bars_drops_only_the_newest(self) -> None:
        df = bars_to_frame(make_daily_bars(n_closed=10))
        self.assertEqual(len(finalized_bars(df)), len(df) - 1)
        self.assertEqual(int(finalized_bars(df)["ts"].iloc[-1]), int(df["ts"].iloc[-2]))
        self.assertTrue(finalized_bars(df.iloc[:1]).empty)

    def test_bars_to_frame_dedupes_and_sorts(self) -> None:
        b = [_bar(2000, 1, 1, 1, 1, 1), _bar(1000, 1, 1, 1, 1, 1), _bar(2000, 2, 2, 2, 2, 2)]
        df = bars_to_frame(b)
        self.assertEqual(list(df["ts"]), [1000, 2000])
        self.assertEqual(float(df["close"].iloc[-1]), 2.0)

    def test_4h_requires_successor_and_four_hourly_bars(self) -> None:
        base = int(datetime(2026, 10, 28, 0, tzinfo=timezone.utc).timestamp() * 1000)
        hours = [_bar(base + h * TF_1H_MS, 10, 11, 9, 10, 1) for h in range(0, 8)]
        # 00:00 bucket complete, 04:00 bucket complete but it is the newest bucket -> no successor
        df = build_closed_4h_from_1h(hours)
        self.assertEqual(list(df["ts"]), [base])
        # Add one 1H bar of the next bucket: now 04:00 has a successor
        hours.append(_bar(base + 8 * TF_1H_MS, 10, 11, 9, 10, 1))
        self.assertEqual(list(build_closed_4h_from_1h(hours)["ts"]), [base, base + TF_4H_MS])
        # Leading partial bucket (starts at 01:00) must be dropped
        partial = [b for b in hours if b.timestamp_ms != base]
        self.assertEqual(list(build_closed_4h_from_1h(partial)["ts"]), [base + TF_4H_MS])

    def test_4h_aggregation_matches_source_row(self) -> None:
        rows = four_hour_rows("signal")
        df = build_closed_4h_from_1h(explode_to_1h(rows, rows[-1][0] + TF_4H_MS))
        self.assertEqual(len(df), len(rows))
        last = rows[-1]
        r = df.iloc[-1]
        self.assertEqual((r["open"], r["high"], r["low"], r["close"], round(r["volume"], 6)), (last[1], last[2], last[3], last[4], last[5]))

    def test_freshness_guard(self) -> None:
        df = pd.DataFrame({"ts": [NOW_MS - 2 * TF_4H_MS]})  # last closed bar opened 8h ago -> exactly one bar behind
        self.assertTrue(is_series_fresh(df, TF_4H_MS, NOW_MS, 600_000))
        stale = pd.DataFrame({"ts": [NOW_MS - 3 * TF_4H_MS]})
        self.assertFalse(is_series_fresh(stale, TF_4H_MS, NOW_MS, 600_000))
        self.assertFalse(is_series_fresh(df.iloc[0:0], TF_4H_MS, NOW_MS, 600_000))


# ----------------------------------------------------------------------------
# Module B: macro gate
# ----------------------------------------------------------------------------

def _closed_daily(**kw: Any) -> pd.DataFrame:
    return finalized_bars(bars_to_frame(make_daily_bars(**kw)))


class TestMacroGate(unittest.TestCase):
    def test_uptrend_with_compression_is_approved(self) -> None:
        gate = compute_macro_gate(_closed_daily())
        self.assertIsNotNone(gate)
        self.assertTrue(gate.trend_pass)
        self.assertLessEqual(gate.bbw_percentile, 0.30)
        self.assertTrue(gate.compression_pass)
        self.assertTrue(gate.macro_approved)
        self.assertGreater(gate.ema50, gate.ema200)

    def test_downtrend_freezes_even_when_compressed(self) -> None:
        gate = compute_macro_gate(_closed_daily(drift=-0.0015))
        self.assertFalse(gate.trend_pass)
        self.assertFalse(gate.macro_approved)

    def test_expanded_volatility_freezes_even_in_uptrend(self) -> None:
        gate = compute_macro_gate(_closed_daily(early_noise=0.002, late_noise=0.04))
        self.assertGreater(gate.bbw_percentile, 0.30)
        self.assertFalse(gate.compression_pass)
        self.assertFalse(gate.macro_approved)

    def test_bbw_and_percentile_match_independent_computation(self) -> None:
        df = _closed_daily()
        gate = compute_macro_gate(df)
        close = df["close"]
        sma = close.rolling(20).mean()
        sd = close.rolling(20).std(ddof=0)
        bbw = ((sma + 2 * sd) - (sma - 2 * sd)) / sma
        window = bbw.iloc[-180:]
        self.assertAlmostEqual(gate.bbw, float(bbw.iloc[-1]), places=12)
        self.assertAlmostEqual(gate.bbw_percentile, float((window <= window.iloc[-1]).mean()), places=12)

    def test_insufficient_history_returns_none(self) -> None:
        self.assertIsNone(compute_macro_gate(_closed_daily(n_closed=150)))

    def test_squeeze_lookback_allows_recent_compression(self) -> None:
        df = _closed_daily(jump_last=0.15)  # volatility pops on the very last closed day
        strict = compute_macro_gate(df, squeeze_lookback_bars=1)
        loose = compute_macro_gate(df, squeeze_lookback_bars=5)
        self.assertFalse(strict.compression_pass)
        self.assertTrue(loose.compression_pass)


# ----------------------------------------------------------------------------
# Module C: weekly anchors + setup
# ----------------------------------------------------------------------------

class TestSetup(unittest.TestCase):
    def test_week_start_is_monday_utc(self) -> None:
        self.assertEqual(current_week_start_ms(NOW_MS), int(datetime(2026, 10, 26, tzinfo=timezone.utc).timestamp() * 1000))
        sunday = int(datetime(2026, 11, 1, 23, 59, tzinfo=timezone.utc).timestamp() * 1000)
        self.assertEqual(current_week_start_ms(sunday), int(datetime(2026, 10, 26, tzinfo=timezone.utc).timestamp() * 1000))

    def test_weekly_anchors_use_monday_sunday_week(self) -> None:
        df = _closed_daily()
        pwl, pwh, week_start, ready = compute_weekly_anchors(df, NOW_MS)
        self.assertTrue(ready)
        self.assertEqual((pwl, pwh), (PWL_T, PWH_T))
        self.assertEqual(week_start, current_week_start_ms(NOW_MS))

    def test_weekly_anchors_exclude_current_week_and_include_sunday(self) -> None:
        df = _closed_daily().copy()
        cur = current_week_start_ms(NOW_MS)
        # A Monday-of-current-week bar with a lower low / higher high must NOT leak into the anchors
        df.loc[df["ts"] == cur, ["low", "high"]] = [1.0, 9_999_999.0]
        # Sunday of the previous week (cur - 1 day) is part of the previous week
        df.loc[df["ts"] == cur - TF_1D_MS, "low"] = 95_000.0
        pwl, pwh, _, ready = compute_weekly_anchors(df, NOW_MS)
        self.assertTrue(ready)
        self.assertEqual(pwl, 95_000.0)
        self.assertEqual(pwh, PWH_T)

    def test_weekly_anchors_not_ready_when_a_day_is_missing(self) -> None:
        df = _closed_daily()
        df = df[df["ts"] != current_week_start_ms(NOW_MS) - TF_1D_MS]
        self.assertFalse(compute_weekly_anchors(df, NOW_MS)[3])

    def _detect(self, kind: str, last_traded: int = 0) -> SpotSwingSetup:
        return detect_setup(_frame(kind), PWL_T, PWH_T, current_week_start_ms(NOW_MS), last_traded_sweep_ts_ms=last_traded)

    def test_full_signal(self) -> None:
        s = self._detect("signal")
        self.assertTrue(s.sweep_detected and s.reclaim_confirmed and s.volume_confirmed)
        self.assertTrue(s.signal_active and s.is_fresh)
        self.assertEqual(s.sweep_low, 99_200.0)
        self.assertAlmostEqual(s.vol_sma3, (100.0 + 100.0 + 160.0) / 3.0)

    def test_no_sweep_no_signal(self) -> None:
        s = self._detect("no_sweep")
        self.assertFalse(s.sweep_detected or s.signal_active)

    def test_sweep_without_reclaim(self) -> None:
        s = self._detect("sweep_no_reclaim")
        self.assertTrue(s.sweep_detected)
        self.assertFalse(s.reclaim_confirmed or s.signal_active)

    def test_sweep_reclaim_without_volume(self) -> None:
        s = self._detect("sweep_low_volume")
        self.assertTrue(s.sweep_detected and s.reclaim_confirmed)
        self.assertFalse(s.volume_confirmed or s.signal_active)

    def test_sweep_outside_12_bar_window_is_ignored(self) -> None:
        df = _frame("signal")
        df.loc[df.index[-4], "low"] = 102_000.0  # remove the sweep
        df.loc[df.index[-14], "low"] = 99_000.0  # 14 bars ago -> outside the 12-bar window
        s = detect_setup(df, PWL_T, PWH_T, 0)
        self.assertFalse(s.sweep_detected)

    def test_same_sweep_cannot_retrigger(self) -> None:
        first = self._detect("signal")
        again = self._detect("signal", last_traded=first.sweep_bar_ts_ms)
        self.assertTrue(again.signal_active)  # raw spec signal is still true
        self.assertFalse(again.is_fresh)  # but it is not a NEW setup
        newer = self._detect("signal", last_traded=first.sweep_bar_ts_ms - TF_4H_MS)
        self.assertTrue(newer.is_fresh)


# ----------------------------------------------------------------------------
# Module D: risk
# ----------------------------------------------------------------------------

class TestRisk(unittest.TestCase):
    def test_sizing_and_barriers(self) -> None:
        df = _frame("signal")
        setup = detect_setup(df, PWL_T, PWH_T, 0)
        r = compute_risk(setup, df, equity_usd=10_000.0)
        self.assertIsNotNone(r)
        self.assertAlmostEqual(r.stop, setup.sweep_low - 0.5 * r.atr14)
        self.assertAlmostEqual(r.stop_distance, r.entry - r.stop)
        self.assertAlmostEqual(r.qty_btc, 100.0 / r.stop_distance, places=9)
        self.assertFalse(r.spot_capped)
        self.assertAlmostEqual(r.realized_risk_usd, 100.0, places=6)
        self.assertAlmostEqual(r.tp1, r.entry + 2.0 * r.stop_distance)
        self.assertEqual(r.tp2_pwh, PWH_T)
        self.assertEqual(r.time_stop_ts_ms, setup.bar_ts_ms + TF_4H_MS + 10 * TF_1D_MS)

    def test_spot_cap_binds_for_tight_stops(self) -> None:
        rows = [(i * TF_4H_MS, 100_000.0, 100_005.0, 99_995.0, 100_000.0, 100.0) for i in range(60)]
        df = pd.DataFrame(rows, columns=["ts", "open", "high", "low", "close", "volume"])
        setup = SpotSwingSetup(bar_ts_ms=int(df["ts"].iloc[-1]), close=100_000.0, pwl=100_050.0, pwh=104_000.0, sweep_low=99_900.0, anchors_ready=True)
        r = compute_risk(setup, df, equity_usd=10_000.0)
        self.assertTrue(r.spot_capped)
        self.assertAlmostEqual(r.qty_btc, 10_000.0 / 100_000.0)
        self.assertAlmostEqual(r.equity_alloc_pct, 100.0)
        self.assertLess(r.realized_risk_usd, r.risk_budget_usd)  # capped size risks LESS than 1%
        self.assertGreater(r.qty_btc_uncapped, r.qty_btc)

    def test_pwh_inside_two_r_is_flagged(self) -> None:
        df = _frame("signal")
        setup = detect_setup(df, PWL_T, 101_500.0, 0)  # PWH barely above entry
        self.assertTrue(compute_risk(setup, df, equity_usd=10_000.0).tp2_inside_tp1)


class TestTripleBarrier(unittest.TestCase):
    def _trade(self, time_stop: int = 10**15) -> SpotSwingTrade:
        return SpotSwingTrade(
            setup_id="t", status="OPEN_FULL", entry_ts_ms=0, entry=100.0, initial_stop=98.0, current_stop=98.0,
            tp1=104.0, tp2=108.0, qty_btc=1.0, time_stop_ts_ms=time_stop, sweep_bar_ts_ms=0, last_processed_bar_ts_ms=0,
        )

    @staticmethod
    def _bars(*hl: Tuple[float, float]) -> pd.DataFrame:
        rows = [((i + 1) * TF_4H_MS, 100.0, h, l, 100.0, 1.0) for i, (h, l) in enumerate(hl)]
        return pd.DataFrame(rows, columns=["ts", "open", "high", "low", "close", "volume"])

    def test_stop_loss(self) -> None:
        t = self._trade()
        ev = advance_trade(t, self._bars((101, 97.9)))
        self.assertEqual([e["event"] for e in ev], ["STOP_LOSS"])
        self.assertEqual((t.status, t.closed_reason), ("CLOSED", "STOP_LOSS"))
        self.assertAlmostEqual(t.realized_r, -1.0)

    def test_tp1_then_breakeven(self) -> None:
        t = self._trade()
        ev = advance_trade(t, self._bars((104.5, 99.0), (101.0, 99.9)))
        self.assertEqual([e["event"] for e in ev], ["TP1_HIT", "BREAKEVEN_STOP"])
        self.assertEqual(t.closed_reason, "BREAKEVEN_STOP")
        self.assertAlmostEqual(t.realized_r, 0.5 * 2.0)  # half sold at +2R, runner out at entry

    def test_tp1_then_pwh_target(self) -> None:
        t = self._trade()
        ev = advance_trade(t, self._bars((105.0, 99.5), (108.5, 103.0)))
        self.assertEqual([e["event"] for e in ev], ["TP1_HIT", "TP2_HIT"])
        self.assertAlmostEqual(t.realized_r, 0.5 * 2.0 + 0.5 * 4.0)

    def test_stop_wins_when_one_bar_touches_stop_and_target(self) -> None:
        t = self._trade()
        ev = advance_trade(t, self._bars((105.0, 97.0)))
        self.assertEqual([e["event"] for e in ev], ["STOP_LOSS"])

    def test_time_stop(self) -> None:
        t = self._trade(time_stop=2 * TF_4H_MS)
        ev = advance_trade(t, self._bars((101, 99.5), (101, 99.5), (101, 99.5)))
        self.assertEqual([e["event"] for e in ev], ["TIME_STOP"])
        self.assertEqual(t.exit_ts_ms, 2 * TF_4H_MS)

    def test_replaying_the_same_bars_is_idempotent(self) -> None:
        t = self._trade()
        bars = self._bars((104.5, 99.0))
        self.assertEqual(len(advance_trade(t, bars)), 1)
        self.assertEqual(advance_trade(t, bars), [])
        self.assertEqual(t.status, "TP1_HIT_RUNNER")
        self.assertEqual(t.current_stop, 100.0)


# ----------------------------------------------------------------------------
# Module E: persistence + engine end-to-end
# ----------------------------------------------------------------------------

class TestPersistence(SpotSwingBase):
    def test_roundtrip_and_atomic_write(self) -> None:
        state = load_state(self.state_path)
        state["last_macro_approved"] = True
        save_state(self.state_path, state)
        self.assertTrue(load_state(self.state_path)["last_macro_approved"])
        self.assertEqual([p.name for p in self.state_path.parent.iterdir()], [self.state_path.name])  # no temp leftovers

    def test_corrupt_file_falls_back_to_clean_state(self) -> None:
        self.state_path.write_text("{not json", encoding="utf-8")
        self.assertIsNone(load_state(self.state_path)["last_macro_approved"])


class TestEngineEndToEnd(SpotSwingBase):
    def test_new_setup_alert_fires_once_and_survives_restart(self) -> None:
        notifier = FakeNotifier()
        eng = self.engine(notifier)
        store = make_store("signal")
        ev = eng.evaluate(store, now_ms=NOW_MS)
        self.assertTrue(ev.data_ready)
        self.assertTrue(ev.macro.macro_approved)
        self.assertEqual(ev.verdict, "NEW LONG SETUP")
        self.assertEqual(ev.traffic_light, "GREEN")
        self.assertEqual([p["event"] for p in notifier.sent], ["NEW_SETUP"])
        self.assertEqual(ev.trade.status, "OPEN_FULL")
        self.assertAlmostEqual(ev.risk.qty_btc * ev.risk.stop_distance, 100.0, places=6)
        self.assertIs(store.spot_swing_evaluation, ev)

        # Same closed bars again (HUD runs at 2 Hz): no duplicate alert
        ev2 = eng.evaluate(store, now_ms=NOW_MS + 1_000)
        self.assertTrue(ev2.verdict.startswith("IN TRADE"))
        self.assertEqual(len(notifier.sent), 1)

        # Engine restart: persisted trade is reloaded, still no duplicate
        n2 = FakeNotifier()
        eng2 = self.engine(n2)
        ev3 = eng2.evaluate(make_store("signal"), now_ms=NOW_MS + 2_000)
        self.assertTrue(ev3.verdict.startswith("IN TRADE"))
        self.assertEqual(n2.sent, [])
        saved = json.loads(self.state_path.read_text(encoding="utf-8"))
        self.assertEqual(saved["trade"]["status"], "OPEN_FULL")

    def test_stop_loss_barrier_alert_and_new_signal_requires_new_sweep(self) -> None:
        notifier = FakeNotifier()
        eng = self.engine(notifier)
        first = eng.evaluate(make_store("signal"), now_ms=NOW_MS)
        stop = first.trade.initial_stop
        crash_ts = int(datetime(2026, 10, 28, 12, tzinfo=timezone.utc).timestamp() * 1000)
        crash = [(crash_ts, 101_200.0, 101_300.0, stop - 50.0, stop - 20.0, 140.0)]
        later = int(datetime(2026, 10, 28, 16, 0, 30, tzinfo=timezone.utc).timestamp() * 1000)
        ev = eng.evaluate(make_store("signal", extra_rows=crash), now_ms=later)
        self.assertEqual([p["event"] for p in notifier.sent], ["NEW_SETUP", "STOP_LOSS"])
        self.assertIsNone(ev.trade)
        saved = json.loads(self.state_path.read_text(encoding="utf-8"))
        self.assertIsNone(saved["trade"])
        self.assertEqual(saved["history"][-1]["closed_reason"], "STOP_LOSS")
        self.assertNotEqual(ev.verdict, "NEW LONG SETUP")

    def test_macro_freeze_alert_fires_once(self) -> None:
        notifier = FakeNotifier()
        eng = self.engine(notifier)
        eng.evaluate(make_store("no_sweep"), now_ms=NOW_MS)
        self.assertEqual(notifier.sent, [])  # first run only records the baseline
        # the next daily close crashes through EMA50: Approved -> Frozen
        crash_day = make_daily_bars(jump_last=-0.08)
        frozen = eng.evaluate(make_store("no_sweep", daily=crash_day), now_ms=NOW_MS + 5_000)
        self.assertEqual(frozen.verdict, "FROZEN (100% CASH)")
        self.assertEqual(frozen.traffic_light, "RED")
        self.assertEqual([p["event"] for p in notifier.sent], ["MACRO_FROZEN"])
        eng.evaluate(make_store("no_sweep", daily=crash_day), now_ms=NOW_MS + 10_000)
        self.assertEqual(len(notifier.sent), 1)

    def test_frozen_macro_blocks_new_setups(self) -> None:
        notifier = FakeNotifier()
        ev = self.engine(notifier).evaluate(make_store("signal", daily=make_daily_bars(drift=-0.0015)), now_ms=NOW_MS)
        self.assertIsNone(ev.trade)
        self.assertEqual(ev.verdict, "FROZEN (100% CASH)")
        self.assertTrue(ev.setup.signal_active)  # raw setup visible, but not actionable
        self.assertEqual(notifier.sent, [])

    def test_scanning_and_sweep_states(self) -> None:
        eng = self.engine()
        self.assertEqual(eng.evaluate(make_store("no_sweep"), now_ms=NOW_MS).verdict, "MACRO APPROVED - SCANNING")
        self.state_path.unlink(missing_ok=True)
        eng2 = self.engine()
        ev = eng2.evaluate(make_store("sweep_no_reclaim"), now_ms=NOW_MS)
        self.assertEqual(ev.verdict, "SWEEP DETECTED - AWAITING RECLAIM")
        self.assertEqual(ev.traffic_light, "YELLOW")

    def test_stale_feed_suspends_screening(self) -> None:
        notifier = FakeNotifier()
        ev = self.engine(notifier).evaluate(make_store("signal"), now_ms=NOW_MS + 3 * TF_1D_MS)
        self.assertFalse(ev.data_ready)
        self.assertEqual(ev.verdict, "STALE DATA - SUSPENDED")
        self.assertEqual(notifier.sent, [])
        self.assertFalse(self.state_path.exists())

    def test_warmup_when_history_is_short(self) -> None:
        store = StateStore()
        ev = self.engine().evaluate(store, now_ms=NOW_MS)
        self.assertFalse(ev.data_ready)
        self.assertEqual(ev.verdict, "WARMING UP")

    def test_read_only_mode_has_no_side_effects(self) -> None:
        notifier = FakeNotifier()
        ev = self.engine(notifier, read_only=True).evaluate(make_store("signal"), now_ms=NOW_MS)
        self.assertEqual(ev.verdict, "NEW LONG SETUP")
        self.assertTrue(ev.read_only)
        self.assertFalse(ev.alerts_enabled)
        self.assertEqual(notifier.sent, [])
        self.assertFalse(self.state_path.exists())

    def test_equity_env_override(self) -> None:
        with mock.patch.dict(os.environ, {"SPOT_SWING_EQUITY_USD": "50000"}):
            ev = self.engine().evaluate(make_store("signal"), now_ms=NOW_MS)
        self.assertEqual(ev.risk.equity_usd, 50_000.0)
        self.assertAlmostEqual(ev.risk.qty_btc * ev.risk.stop_distance, 500.0, places=6)


# ----------------------------------------------------------------------------
# Notifier
# ----------------------------------------------------------------------------

class _OkResponse:
    status = 200

    def __enter__(self) -> "_OkResponse":
        return self

    def __exit__(self, *a: Any) -> None:
        return None


class TestNotifier(unittest.TestCase):
    def test_disabled_by_default_never_touches_network(self) -> None:
        n = SpotSwingNotifier()
        self.assertFalse(n.enabled)
        with mock.patch("urllib.request.urlopen") as urlopen:
            n.dispatch({"event": "NEW_SETUP"})
        urlopen.assert_not_called()

    def test_from_env(self) -> None:
        env = {"SPOT_SWING_WEBHOOK_URL": "https://x.invalid/h", "TELEGRAM_BOT_TOKEN": "t", "TELEGRAM_CHAT_ID": "1"}
        with mock.patch.dict(os.environ, env):
            n = SpotSwingNotifier.from_env()
        self.assertTrue(n.webhook_enabled and n.telegram_enabled)
        self.assertEqual(n.describe_channels(), "Webhook + Telegram")

    def test_retries_on_429_then_succeeds(self) -> None:
        n = SpotSwingNotifier(webhook_url="https://x.invalid/h", synchronous=True, max_retries=3)
        err = urllib.error.HTTPError("https://x.invalid/h", 429, "Too Many Requests", {"Retry-After": "0"}, None)
        with mock.patch("urllib.request.urlopen", side_effect=[err, _OkResponse()]) as urlopen, mock.patch("time.sleep"):
            self.assertTrue(n._post_json(n.webhook_url, {"a": 1}, "webhook"))
        self.assertEqual(urlopen.call_count, 2)

    def test_client_error_is_not_retried(self) -> None:
        n = SpotSwingNotifier(webhook_url="https://x.invalid/h", synchronous=True)
        err = urllib.error.HTTPError("https://x.invalid/h", 404, "Not Found", {}, None)
        with mock.patch("urllib.request.urlopen", side_effect=err) as urlopen, mock.patch("time.sleep"):
            self.assertFalse(n._post_json(n.webhook_url, {}, "webhook"))
        self.assertEqual(urlopen.call_count, 1)

    def test_network_failure_exhausts_retries_without_raising(self) -> None:
        n = SpotSwingNotifier(webhook_url="https://x.invalid/h", synchronous=True, max_retries=3)
        with mock.patch("urllib.request.urlopen", side_effect=urllib.error.URLError("down")) as urlopen, mock.patch("time.sleep"):
            self.assertFalse(n._post_json(n.webhook_url, {}, "webhook"))
        self.assertEqual(urlopen.call_count, 3)

    def test_dispatch_hits_both_channels(self) -> None:
        n = SpotSwingNotifier(webhook_url="https://x.invalid/h", telegram_token="TOK", telegram_chat_id="42", synchronous=True)
        calls: List[Tuple[str, Dict[str, Any]]] = []
        with mock.patch.object(SpotSwingNotifier, "_post_json", lambda self, url, body, channel: calls.append((channel, body)) or True):
            n.dispatch({"event": "MACRO_FROZEN", "timestamp_utc": "t", "price": 1.0, "macro": {"bbw_percentile": 0.5}})
        self.assertEqual([c for c, _ in calls], ["webhook", "telegram"])
        self.assertEqual(calls[1][1]["chat_id"], "42")
        self.assertIn("FROZEN", calls[1][1]["text"])
        self.assertEqual(n.sent_count, 2)

    def test_telegram_message_for_new_setup(self) -> None:
        msg = format_telegram_message(
            {
                "event": "NEW_SETUP", "timestamp_utc": "now", "price": 101_300.0,
                "trade": {"entry": 101_200.0, "initial_stop": 98_900.0, "qty_btc": 0.0435, "notional_usd": 4_400.0,
                          "equity_alloc_pct": 44.0, "spot_capped": True, "tp1": 105_800.0, "tp2": 108_000.0,
                          "tp1_fraction": 0.5, "time_stop_utc": "2026-11-07 12:00 UTC"},
            }
        )
        for needle in ("NEW LONG SETUP", "$101,200.00", "$98,900.00", "CAPPED", "TP1 +2R", "TP2 PWH", "Time stop"):
            self.assertIn(needle, msg)


# ----------------------------------------------------------------------------
# HUD routing: Tab [0] Spot Swing, Tab [L] Master
# ----------------------------------------------------------------------------

_ANSI = re.compile(r"\x1b\[[0-9;]*m")


def _render(renderable: Any) -> str:
    console = Console(width=175, record=True, force_terminal=False, file=io.StringIO())
    console.print(renderable)
    return console.export_text()


class _FakeMsvcrt:
    def __init__(self, keys: str) -> None:
        self.keys = list(keys)

    def kbhit(self) -> bool:
        return bool(self.keys)

    def getwch(self) -> str:
        return self.keys.pop(0)


class TestHudRouting(SpotSwingBase):
    def _store_with_eval(self) -> StateStore:
        store = make_store("signal")
        self.engine().evaluate(store, now_ms=NOW_MS)
        return store

    def test_tab0_renders_spot_swing_screener(self) -> None:
        store = self._store_with_eval()
        text = _render(build_dashboard_renderable(CONFIG, store, tab_override=0))
        for needle in ("BTC SPOT SWING SCREENING", "1D Macro Regime Gate", "Weekly Anchors", "Triple-Barrier", "NEW LONG SETUP", "[0: SPOT SWING]"):
            self.assertIn(needle, text)

    def test_tab0_renders_frozen_and_warmup_states(self) -> None:
        text = _render(build_dashboard_renderable(CONFIG, StateStore(), tab_override=0))
        self.assertIn("Warming up Tab [0]", text)
        store = make_store("no_sweep", daily=make_daily_bars(drift=-0.0015))
        self.engine().evaluate(store, now_ms=NOW_MS)
        self.assertIn("FROZEN", _render(build_dashboard_renderable(CONFIG, store, tab_override=0)))
        stale = make_store("signal")
        self.engine().evaluate(stale, now_ms=NOW_MS + 3 * TF_1D_MS)
        self.assertIn("STALE DATA", _render(build_dashboard_renderable(CONFIG, stale, tab_override=0)))

    def test_master_moved_to_tab_l(self) -> None:
        store = StateStore()
        for override in (10, "l", "L", "m", "master"):
            text = _render(build_dashboard_renderable(CONFIG, store, tab_override=override))
            self.assertIn("Tab [L]: Master Conclusion", text, override)
        self.assertNotIn("Tab [L]: Master Conclusion", _render(build_dashboard_renderable(CONFIG, store, tab_override=0)))

    def test_default_active_tab_is_spot_swing(self) -> None:
        store = StateStore()
        self.assertEqual(store.active_tab, 0)
        self.assertIn("Warming up Tab [0]", _render(build_dashboard_renderable(CONFIG, store)))

    def test_hotkeys(self) -> None:
        store = StateStore()
        for keys, expected in (("l", 10), ("L", 10), ("m", 10), ("0", 0), ("5", 5), ("g", 7), ("e", 9), ("f", 11), ("F", 11)):
            store.active_tab = 3
            with mock.patch.object(terminal_hud, "msvcrt", _FakeMsvcrt(keys)):
                terminal_hud._poll_keyboard_tab_switch(CONFIG, store)
            self.assertEqual(store.active_tab, expected, keys)

    def test_ai_packet_exporter_includes_section_0(self) -> None:
        from analytics.ai_packet_exporter import build_ai_telemetry_packet
        store = self._store_with_eval()
        packet = build_ai_telemetry_packet(CONFIG, store)
        self.assertIn("## SECTION 0: TAB [0] BTC SPOT SWING SCREENING & ALERT ENGINE", packet)
        self.assertIn("### 0A. 1D Macro Regime Gate", packet)
        self.assertIn("### 0B. 4H Weekly Anchors & Structural Liquidity Setup", packet)
        self.assertIn("### 0C. Volatility-Adjusted Risk Engine & Triple-Barrier Order Card", packet)
        self.assertIn("NEW LONG SETUP", packet)

    def test_master_synthesis_confluence_includes_tab0(self) -> None:
        from analytics.signal_detector import SignalDetector
        store = self._store_with_eval()
        detector = SignalDetector(CONFIG)
        with mock.patch("time.time", return_value=NOW_MS / 1000.0):
            detector.evaluate(store)
        msev = store.master_synthesis_evaluation
        self.assertIsNotNone(msev)
        has_tab0_confluence = any("Spot Swing Protocol [Tab 0]" in cp for cp in msev.confluence_points)
        self.assertTrue(has_tab0_confluence)

    def test_dry_run_report_accepts_new_tab_arguments(self) -> None:
        store = self._store_with_eval()
        for arg, needle in (("0", "BTC SPOT SWING SCREENING"), ("l", "Master"), ("all", "TAB [L: MASTER")):
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                print_dry_run_report(CONFIG, store, tab_arg=arg)
            self.assertIn(needle, _ANSI.sub("", buf.getvalue()), arg)


# ----------------------------------------------------------------------------
# Module F: Daily Liquidation Magnet Protocol & Tight RRR 1:3 Money Management
# ----------------------------------------------------------------------------

class TestLiquidationMagnetProtocol(SpotSwingBase):
    def test_magnet_step1_to_step4_and_3r_geometry(self) -> None:
        store = make_store("signal")
        ev = self.engine().evaluate(store, now_ms=NOW_MS)
        self.assertIsNotNone(ev.magnet)
        m = ev.magnet
        self.assertGreater(m.sma50_1d, 0.0)
        self.assertGreater(m.range_high_30d, m.range_low_30d)
        self.assertGreater(m.short_liq_magnet, m.current_price)
        self.assertLess(m.long_liq_magnet, m.current_price)
        self.assertEqual(m.min_required_rrr, 3.0)
        self.assertAlmostEqual(
            m.tp_3r_price,
            m.entry_ref + 3.0 * m.risk_distance_usd,
            places=4,
        )
        self.assertAlmostEqual(
            m.max_entry_for_3r,
            (m.short_liq_magnet + 3.0 * m.hard_stop_price) / 4.0,
            places=4,
        )
        self.assertTrue(m.rrr_pass)
        self.assertEqual(m.verdict, "Hold")
        self.assertIn(m.regime, ("Range", "Possible Transition", "Trend"))

    def test_rule1_partial_profit_into_magnet_when_near_short_cluster_without_spot_cvd(self) -> None:
        from core.models import DerivativesSnapshot, FlowSnapshot, HorizonFlowMetrics, OIPositioningQuadrant
        store = make_store("no_sweep", price=107_200.0)
        store.derivatives_snapshot = DerivativesSnapshot(
            open_interest_btc=90_000.0,
            open_interest_usd=90_000.0 * 107_200.0,
            oi_change_1h_pct=0.2,
            oi_change_4h_pct=1.8,
            oi_regime_quadrant=OIPositioningQuadrant.AGGRESSIVE_SHORT_BUILD,
            funding_rate_pct=-0.0100,  # Negative funding (-0.0100% / 8h)
        )
        store.flow_snapshot = FlowSnapshot(
            w_4h=HorizonFlowMetrics(window_label="4H", spot_delta_btc=-250.0, perp_delta_btc=900.0),
            w_24h=HorizonFlowMetrics(window_label="24H", spot_delta_btc=-400.0, perp_delta_btc=1800.0),
        )
        override_file = Path(self._tmp.name) / "cg_override.json"
        override_file.write_text(json.dumps({
            "short_liq_magnet_price": 108_000.0,
            "short_liq_magnet_size_usd": 145_000_000,
            "long_liq_magnet_price": 99_500.0,
            "long_liq_magnet_size_usd": 110_000_000,
            "headline_filter": "RECURRING_RUMOR",
        }), encoding="utf-8")
        cfg = replace(CONFIG, protocol_context_path=override_file)
        eng = SpotSwingEngine(cfg, notifier=FakeNotifier(), state_path=self.state_path)
        ev = eng.evaluate(store, now_ms=NOW_MS)
        self.assertEqual(ev.magnet.verdict, "Partial Profit into Magnet")
        self.assertFalse(ev.magnet.spot_cvd_confirming)
        self.assertIn("Recurring Rumor", ev.magnet.headline_filter)
        self.assertIn("COINGLASS MANUAL", ev.magnet.short_liq_source)

    def test_rule2_reduce_or_exit_on_post_squeeze_rejection_below_pivot(self) -> None:
        # Recent 4H bar swept up to 108,250 (short_liq_magnet=108,000) then dumped to 100,500 (below pivot & 50DMA)
        spike_reject = [
            (int(datetime(2026, 10, 28, 8, tzinfo=timezone.utc).timestamp() * 1000), 106_500.0, 108_250.0, 100_200.0, 100_500.0, 240.0)
        ]
        store = make_store("no_sweep", extra_rows=spike_reject, price=100_500.0)
        override_file = Path(self._tmp.name) / "cg_reject.json"
        override_file.write_text(json.dumps({
            "short_liq_magnet_price": 108_000.0,
            "long_liq_magnet_price": 98_500.0,
        }), encoding="utf-8")
        cfg = replace(CONFIG, protocol_context_path=override_file)
        eng = SpotSwingEngine(cfg, notifier=FakeNotifier(), state_path=self.state_path)
        ev = eng.evaluate(store, now_ms=NOW_MS)
        self.assertEqual(ev.magnet.verdict, "Reduce or Exit")
        self.assertEqual(ev.magnet.confidence, "High")

    def test_rule3_rare_add_consideration_on_confirmed_breakout(self) -> None:
        from core.models import DerivativesSnapshot, FlowSnapshot, HorizonFlowMetrics, OIPositioningQuadrant
        # Daily close & current price above short-liq wall (104,500), rising Spot CVD, OI holding
        store = make_store("no_sweep", daily=make_daily_bars(jump_last=0.05), price=106_800.0)
        store.derivatives_snapshot = DerivativesSnapshot(
            open_interest_btc=95_000.0,
            open_interest_usd=95_000.0 * 106_800.0,
            oi_change_1h_pct=0.5,
            oi_change_4h_pct=1.2,
            oi_regime_quadrant=OIPositioningQuadrant.LEVERAGED_LONG_EXPANSION,
            funding_rate_pct=0.0050,
        )
        store.flow_snapshot = FlowSnapshot(
            w_4h=HorizonFlowMetrics(window_label="4H", spot_delta_btc=450.0, perp_delta_btc=200.0),
            w_24h=HorizonFlowMetrics(window_label="24H", spot_delta_btc=850.0, perp_delta_btc=400.0),
        )
        override_file = Path(self._tmp.name) / "cg_breakout.json"
        override_file.write_text(json.dumps({
            "short_liq_magnet_price": 104_500.0,
            "long_liq_magnet_price": 99_000.0,
        }), encoding="utf-8")
        cfg = replace(CONFIG, protocol_context_path=override_file)
        eng = SpotSwingEngine(cfg, notifier=FakeNotifier(), state_path=self.state_path)
        ev = eng.evaluate(store, now_ms=NOW_MS)
        self.assertEqual(ev.magnet.verdict, "Rare Add Consideration")
        self.assertTrue(ev.magnet.spot_cvd_confirming)

    def test_rrr_1_to_3_gate_enforces_do_nothing_vs_hold(self) -> None:
        # Case A: Short-liq magnet is close (104,000) -> RRR < 3.0 -> Do Nothing even on a valid sweep/reclaim signal
        store_low_r = make_store("signal", price=101_200.0)
        override_low = Path(self._tmp.name) / "cg_low_r.json"
        override_low.write_text(json.dumps({
            "short_liq_magnet_price": 104_000.0,
            "long_liq_magnet_price": 98_500.0,
        }), encoding="utf-8")
        cfg_low = replace(CONFIG, protocol_context_path=override_low)
        ev_low = SpotSwingEngine(cfg_low, notifier=FakeNotifier(), state_path=self.state_path).evaluate(store_low_r, now_ms=NOW_MS)
        self.assertFalse(ev_low.magnet.rrr_pass)
        self.assertLess(ev_low.magnet.rrr_to_magnet, 3.0)
        self.assertEqual(ev_low.magnet.verdict, "Do Nothing")

        # Case B: Short-liq magnet is far enough (110,500) -> RRR >= 3.0 -> Hold
        self.state_path.unlink(missing_ok=True)
        store_high_r = make_store("signal", price=101_200.0)
        override_high = Path(self._tmp.name) / "cg_high_r.json"
        override_high.write_text(json.dumps({
            "short_liq_magnet_price": 110_500.0,
            "long_liq_magnet_price": 98_500.0,
        }), encoding="utf-8")
        cfg_high = replace(CONFIG, protocol_context_path=override_high)
        ev_high = SpotSwingEngine(cfg_high, notifier=FakeNotifier(), state_path=self.state_path).evaluate(store_high_r, now_ms=NOW_MS)
        self.assertTrue(ev_high.magnet.rrr_pass)
        self.assertGreaterEqual(ev_high.magnet.rrr_to_magnet, 3.0)
        self.assertEqual(ev_high.magnet.verdict, "Hold")

    def test_hud_and_ai_packet_include_magnet_protocol_and_3r_fields(self) -> None:
        from analytics.ai_packet_exporter import build_ai_telemetry_packet
        store = make_store("signal")
        self.engine().evaluate(store, now_ms=NOW_MS)
        hud_text = _render(build_dashboard_renderable(CONFIG, store, tab_override=0))
        for needle in (
            "Daily Liquidation Magnet Protocol",
            "Short-Liq Magnet",
            "Long-Liq Magnet",
            "RRR 1:3 Mandate Gate",
            "Max 3R Entry:",
            "MAGNET VERDICT:",
        ):
            self.assertIn(needle, hud_text)
        packet = build_ai_telemetry_packet(CONFIG, store)
        self.assertIn("### 0D. Daily Liquidation Magnet Protocol & RRR 1:3 Verdict (Master Prompt Output)", packet)
        self.assertIn("Max 3R Entry:", packet)


if __name__ == "__main__":
    unittest.main()
