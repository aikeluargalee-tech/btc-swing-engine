"""Unit tests for FuturesV4Engine and Tab [20 / X] Rich HUD inside btc_swing_engine."""

from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone
from io import StringIO
from types import SimpleNamespace

from rich.console import Console

from analytics.ai_packet_exporter import build_ai_telemetry_packet
from analytics.data_only_reports import build_global_data_only_packet, build_tab_x_data_only_report
from analytics.futures_v4_engine import FuturesV4Engine, build_futures_v4_view
from collectors.macro_collector import MacroIntermarketSnapshot
from config.settings import EngineConfig
from core.models import KlineBar
from core.state_store import StateStore
from ui.terminal_hud import build_dashboard_renderable


def _bars(count: int, start_price: float, step_pct: float, interval: str, step_ms: int, vol: float = 1200.0):
    base_ts = 1700000000000
    out = []
    p = start_price
    for i in range(count):
        wave = math.sin(i * 0.55) * 0.018
        op = p
        cl = p * (1.0 + step_pct + wave * 0.35)
        hi = max(op, cl) * 1.0025
        lo = min(op, cl) * 0.9975
        out.append(
            KlineBar(
                timestamp_ms=base_ts + i * step_ms,
                open=op,
                high=hi,
                low=lo,
                close=cl,
                volume=vol,
                taker_buy_volume=vol * 0.55,
            )
        )
        p = cl
    return out


def _populated_store(trend: str = "bull") -> StateStore:
    store = StateStore()
    if trend == "bull":
        d1 = _bars(250, 50000.0, 0.003, "1d", 86_400_000)
        h4 = _bars(180, d1[-30].close, 0.0042, "4h", 14_400_000)
        h4[-1].open = h4[-2].close
        h4[-1].close = max(b.high for b in h4[-10:-1]) * 1.003
        h4[-1].high = h4[-1].close * 1.001
        h4[-1].volume = 2000.0
    elif trend == "bear":
        d1 = _bars(250, 95000.0, -0.003, "1d", 86_400_000)
        h4 = _bars(180, d1[-30].close, -0.0042, "4h", 14_400_000)
        h4[-1].open = h4[-2].close
        h4[-1].close = min(b.low for b in h4[-10:-1]) * 0.997
        h4[-1].low = h4[-1].close * 0.999
        h4[-1].volume = 2000.0
    else:
        d1 = _bars(250, 70000.0, 0.0, "1d", 86_400_000)
        h4 = _bars(180, 70000.0, 0.0, "4h", 14_400_000)

    store.spot_klines_1d.extend(d1)
    store.spot_klines_4h.extend(h4)
    store.binance_spot_price = h4[-1].close
    store.binance_perp_price = h4[-1].close
    store.funding_rate_pct = 0.005
    return store


def test_v4_engine_regime_and_checklist(tmp_path):
    cfg = EngineConfig(futures_v4_ledger_path=tmp_path / "v4_ledger.json")
    wkday = datetime(2026, 11, 12, 14, 0, tzinfo=timezone.utc)

    eng_bull = FuturesV4Engine(cfg, read_only=True)
    ev_bull = eng_bull.evaluate(_populated_store("bull"), now_utc=wkday)
    assert ev_bull.regime_score >= 68.0
    assert ev_bull.regime_bias == "LONG"
    assert len(ev_bull.checklist) == 9

    eng_bear = FuturesV4Engine(cfg, read_only=True)
    ev_bear = eng_bear.evaluate(_populated_store("bear"), now_utc=wkday)
    assert ev_bear.regime_score <= 32.0
    assert ev_bear.regime_bias == "SHORT"
    assert ev_bear.sell_inventory_active is True
    assert ev_bear.sell_inventory_btc == 0.4  # 20% of 2.0 BTC

    eng_flat = FuturesV4Engine(cfg, read_only=True)
    ev_flat = eng_flat.evaluate(_populated_store("flat"), now_utc=wkday)
    assert 32.0 < ev_flat.regime_score < 68.0
    assert ev_flat.futures_status == "FLAT"
    assert ev_flat.sell_inventory_active is False


def test_v4_macro_60m_and_circuit_breakers(tmp_path):
    cfg = EngineConfig(futures_v4_ledger_path=tmp_path / "v4_ledger.json")
    wkday = datetime(2026, 11, 12, 14, 0, tzinfo=timezone.utc)
    eng = FuturesV4Engine(cfg, read_only=False)
    st = _populated_store("bear")

    # 60m macro blocks futures Rule 9, but Sell Inventory STILL works!
    ev_macro = eng.evaluate(st, now_utc=wkday, macro_minutes_away=45.0)
    assert ev_macro.futures_status == "FLAT"
    assert ev_macro.checklist[8].passed is False
    assert ev_macro.sell_inventory_active is True

    # Trigger -1.2% intraday & -6% DD Tier 1
    eng._ledger["realized_equity"] = 93500.0
    ev_dd = eng.evaluate(st, now_utc=wkday + timedelta(minutes=15))
    assert ev_dd.breakers["intraday_halted"] is True
    assert ev_dd.breakers["dd_tier1_active"] is True
    assert ev_dd.long_threshold == 75.0
    assert ev_dd.short_threshold == 25.0


def test_tab20_hud_renderable(tmp_path):
    cfg = EngineConfig(futures_v4_ledger_path=tmp_path / "v4_ledger.json")
    st = _populated_store("bull")
    FuturesV4Engine(cfg, read_only=True).evaluate(st)
    ren = build_dashboard_renderable(cfg, st, tab_override=20)
    assert ren is not None


def _render_tab20_text(cfg: EngineConfig, st: StateStore) -> str:
    con = Console(file=StringIO(), record=True, width=180, force_terminal=False)
    ren = build_dashboard_renderable(cfg, st, tab_override=20)
    con.print(ren)
    return con.export_text()


def test_task1_spot_only_boundary_and_read_only_isolation(tmp_path):
    cfg = EngineConfig(futures_v4_ledger_path=tmp_path / "v4_ledger.json")
    wkday = datetime(2026, 11, 12, 14, 0, tzinfo=timezone.utc)
    st = _populated_store("bull")
    st.macro_intermarket = SimpleNamespace(macro_calendar_fetched=True, macro_calendar_events=[])

    # read_only=True must not mutate disk or in-memory ledger across cycles
    eng = FuturesV4Engine(cfg, read_only=True)
    ev1 = eng.evaluate(st, now_utc=wkday)
    ev2 = eng.evaluate(st, now_utc=wkday + timedelta(minutes=5))
    assert ev1.read_only is True
    assert ev2.read_only is True
    assert eng._ledger["open_positions"] == []
    assert not (tmp_path / "v4_ledger.json").exists()

    # Active signal in read_only mode must label every order-shaped line hypothetical/paper
    hud_active = _render_tab20_text(cfg, st)
    assert "SPOT-ONLY OPERATOR: NO LEVERAGE" in hud_active
    assert "NO SHORTS" in hud_active
    assert "READ-ONLY HYPOTHETICAL / PAPER ONLY" in hud_active
    if ev2.futures_status in ("LONG", "SHORT"):
        assert "HYPOTHETICAL / PAPER ONLY (NOT AN ORDER)" in hud_active
        assert "Hypothetical Size / Lev" in hud_active
        assert "HYPOTHETICAL/PAPER:" in hud_active

    # FLAT state must NOT render an order-shaped sizing line beside FLAT
    st_flat = _populated_store("flat")
    st_flat.macro_intermarket = SimpleNamespace(macro_calendar_fetched=True, macro_calendar_events=[])
    FuturesV4Engine(cfg, read_only=True).evaluate(st_flat, now_utc=wkday)
    hud_flat = _render_tab20_text(cfg, st_flat)
    assert "FLAT — NO HYPOTHETICAL FUTURES POSITION" in hud_flat
    assert "Hypothetical Size / Lev" not in hud_flat
    assert "Risk Sizing / Lev" not in hud_flat


def test_task2_thresholds_in_labels_match_config(tmp_path):
    cfg = EngineConfig(
        futures_v4_ledger_path=tmp_path / "v4_ledger.json",
        futures_v4_max_leverage=1.5,
        futures_v4_max_stop_pct=0.035,
        futures_v4_min_rr=2.1,
        futures_v4_max_concurrent=2,
        futures_v4_partial_pct=0.30,
        futures_v4_partial_r=2.0,
        futures_v4_be_r=0.8,
        futures_v4_time_reduce_hours=6.0,
        futures_v4_time_exit_hours=10.0,
        futures_v4_max_hold_hours=18.0,
        futures_v4_weekend_long=85.0,
        futures_v4_weekend_short=15.0,
        futures_v4_weekend_size_mult=0.25,
        futures_v4_intraday_loss_pct=-0.015,
        futures_v4_daily_loss_pct=-0.025,
        futures_v4_weekly_loss_pct=-0.050,
        futures_v4_dd_tier1_pct=-0.070,
        futures_v4_dd_tier1_risk_pct=0.001,
        futures_v4_dd_tier1_long=78.0,
        futures_v4_dd_tier1_short=22.0,
        futures_v4_dd_tier2_pct=-0.120,
        futures_v4_macro_blackout_min=45.0,
    )
    wknd = datetime(2026, 11, 14, 14, 0, tzinfo=timezone.utc)  # Saturday
    st = _populated_store("bull")
    st.macro_intermarket = MacroIntermarketSnapshot(macro_calendar_fetched=True, macro_calendar_events=[])
    eng = FuturesV4Engine(cfg, read_only=False)
    # Trigger -7.5% drawdown (> -12% tier2, <= -7% tier1)
    eng._ledger["realized_equity"] = 92500.0
    ev = eng.evaluate(st, now_utc=wknd)

    hud_txt = _render_tab20_text(cfg, st)
    exp_txt = build_tab_x_data_only_report(cfg, st)

    for txt in (hud_txt, exp_txt):
        assert "1.5" in txt
        assert "18h" in txt
        assert "3.5%" in txt
        assert "2.1:1" in txt
        assert "85" in txt and "15" in txt
        assert "0.25x" in txt
        assert "45m" in txt
        assert "+0.8R" in txt
        assert "6h -50%" in txt
        assert "10h Exit" in txt
        assert "-1.5%" in txt
        assert "-2.5%" in txt
        assert "-5%" in txt
        assert "-7%" in txt
        assert "0.1%/78-22" in txt
        assert "-12%" in txt
        assert "2.2%" not in txt
        assert "80/20" not in txt

    assert "85/15" in hud_txt
    assert "Max 2 Futures" in ev.checklist[5].rule


def test_task3_fail_open_gates_closed(tmp_path):
    cfg = EngineConfig(futures_v4_ledger_path=tmp_path / "v4_ledger.json")
    wkday = datetime(2026, 11, 12, 14, 0, tzinfo=timezone.utc)
    st = _populated_store("bull")

    # 1) Macro calendar missing / None -> Rule 9 MUST fail closed
    eng_no_cal = FuturesV4Engine(cfg, read_only=True)
    ev_no_cal = eng_no_cal.evaluate(st, now_utc=wkday)
    assert ev_no_cal.checklist[8].passed is False
    assert "UNAVAILABLE" in ev_no_cal.checklist[8].detail
    assert ev_no_cal.futures_status == "FLAT"

    # 2) Macro calendar unfetched -> Rule 9 MUST fail closed
    st.macro_intermarket = SimpleNamespace(macro_calendar_fetched=False, macro_calendar_events=[])
    ev_unfetched = eng_no_cal.evaluate(st, now_utc=wkday)
    assert ev_unfetched.checklist[8].passed is False
    assert ev_unfetched.futures_status == "FLAT"

    # 3) Macro event within +-60m (including just released -15m) -> Rule 9 MUST fail
    st.macro_intermarket = SimpleNamespace(
        macro_calendar_fetched=True,
        macro_calendar_events=[{"title": "CPI", "minutes_away": -15.0}],
    )
    ev_recent = eng_no_cal.evaluate(st, now_utc=wkday)
    assert ev_recent.checklist[8].passed is False

    # 4) Rule 8 must test all 5 breakers including dd_tier1_active
    st.macro_intermarket = MacroIntermarketSnapshot(macro_calendar_fetched=True, macro_calendar_events=[])
    eng_dd1 = FuturesV4Engine(cfg, read_only=False)
    # Trigger -6.5% drawdown on day 1, then advance day so intraday/daily halts clear while dd_tier1_active stays True
    eng_dd1._ledger["realized_equity"] = 93500.0
    eng_dd1.evaluate(st, now_utc=wkday)
    ev_dd1 = eng_dd1.evaluate(st, now_utc=wkday + timedelta(days=1))
    assert ev_dd1.breakers["dd_tier1_active"] is True
    assert ev_dd1.breakers["intraday_halted"] is False
    assert ev_dd1.breakers["daily_halted"] is False
    assert ev_dd1.checklist[7].passed is False
    assert "dd_tier1_active" in ev_dd1.checklist[7].detail
    assert "All 5 circuit breakers clear" not in ev_dd1.checklist[7].detail
    assert ev_dd1.futures_status == "FLAT"

    # 5) Warmup / short buffer must not invent 50.0 factor scores in HUD or export
    st_warm = StateStore()
    FuturesV4Engine(cfg, read_only=True).evaluate(st_warm, now_utc=wkday)
    hud_warm = _render_tab20_text(cfg, st_warm)
    exp_warm = build_tab_x_data_only_report(cfg, st_warm)
    assert "UNAVAILABLE" in hud_warm
    assert "UNAVAILABLE" in exp_warm


def test_task4_export_matches_hud(tmp_path):
    cfg = EngineConfig(futures_v4_ledger_path=tmp_path / "v4_ledger.json")
    wkday = datetime(2026, 11, 12, 14, 0, tzinfo=timezone.utc)
    st = _populated_store("bear")
    st.macro_intermarket = MacroIntermarketSnapshot(macro_calendar_fetched=True, macro_calendar_events=[])
    FuturesV4Engine(cfg, read_only=True).evaluate(st, now_utc=wkday)

    view = build_futures_v4_view(cfg, st)
    ev = view.evaluation
    hud_txt = _render_tab20_futures_v4_text(cfg, st)
    tab_x_rep = build_tab_x_data_only_report(cfg, st)
    global_pkt = build_global_data_only_packet(cfg, st)
    ai_pkt = build_ai_telemetry_packet(cfg, st)

    for txt in (hud_txt, tab_x_rep, global_pkt, ai_pkt):
        assert f"{ev.regime_score:.1f}/100" in txt
        assert view.action_label in txt
        assert f"{view.checklist_passed}/{view.checklist_total}" in txt
        assert f"{ev.spot_inventory_btc:.2f} BTC" in txt
        assert f"${ev.equity_usd:,.2f}" in txt
        assert "SPOT-ONLY OPERATOR" in txt

    assert "SECTION 20: TAB [X / 20]" in ai_pkt
    assert "TAB [X / 20: 4H FUTURES + INVENTORY PROTOCOL v4.0]" in global_pkt


def _render_tab20_futures_v4_text(cfg: EngineConfig, st: StateStore) -> str:
    return _render_tab20_text(cfg, st)
