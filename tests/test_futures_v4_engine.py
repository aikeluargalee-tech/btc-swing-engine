"""Unit tests for FuturesV4Engine and Tab [20 / X] Rich HUD inside btc_swing_engine."""

from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone

from analytics.futures_v4_engine import FuturesV4Engine
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
