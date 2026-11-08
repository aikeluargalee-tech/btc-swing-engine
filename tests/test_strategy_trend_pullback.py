"""Unit tests for BTC TREND-PULLBACK v1.0 (Tab 18 / Desk [A: BTC STRATEGY]).

Covers all 17 mandatory test scenarios specified in Section 11:
1. Bullish daily regime
2. Non-bullish daily regime
3. Confirmed 4H trend
4. Failed 4H trend
5. Valid pullback recovery
6. Deep pullback rejection
7. Breakout-chasing rejection
8. Invalid stop distance
9. Correct position sizing
10. Stop-loss breach
11. Two-candle 4H EMA50 exit
12. Two-day 1D SMA200 exit
13. Incomplete candle rejection
14. Missing data rejection
15. Stale data rejection
16. Setup expiry
17. Cash vs. holding decision logic
Plus TUI HUD rendering and AI Packet Section 18 integration.
"""

from typing import List
from rich.console import Console

from config.settings import EngineConfig
from core.models import KlineBar
from core.state_store import StateStore
from strategy_trend_pullback import (
    TrendPullbackConfig,
    TrendPullbackEngine,
    calculate_entry_zone,
    calculate_position_size,
    calculate_regime,
    calculate_stop,
    calculate_trend,
    detect_pullback,
    evaluate_exit,
    generate_strategy_verdict,
    verify_and_extract_completed_candles,
)
from ui.terminal_hud import build_dashboard_renderable
from analytics.ai_packet_exporter import build_ai_telemetry_packet


NOW_MS = 1_794_139_200_000  # Fixed UTC reference aligned to 4H & 1D boundaries
DAY_MS = 86_400_000
FOUR_H_MS = 14_400_000
ONE_H_MS = 3_600_000


def _make_bar(
    open_ms: int,
    open_p: float,
    high_p: float,
    low_p: float,
    close_p: float,
    is_closed: bool = True,
) -> KlineBar:
    bar = KlineBar(
        timestamp_ms=open_ms,
        open=open_p,
        high=high_p,
        low=low_p,
        close=close_p,
        volume=100.0,
        taker_buy_volume=55.0,
    )
    if not is_closed:
        setattr(bar, "is_closed", False)
    return bar


def _build_bullish_1d_bars(count: int = 230, now_ms: int = NOW_MS) -> List[KlineBar]:
    """Generates `count` completed 1D candles in a steady uptrend so Close > SMA200 and 20D SMA200 slope > 0."""
    bars: List[KlineBar] = []
    start_ms = now_ms - count * DAY_MS
    for i in range(count):
        open_ms = start_ms + i * DAY_MS
        px = 60_000.0 + i * 100.0  # Rises from $60k to $82.9k
        bars.append(_make_bar(open_ms, px - 50.0, px + 150.0, px - 150.0, px, is_closed=True))
    return bars


def _build_bullish_4h_bars(count: int = 220, now_ms: int = NOW_MS) -> List[KlineBar]:
    """Generates `count` completed 4H candles in a steady uptrend with a valid recovery candle at the end."""
    bars: List[KlineBar] = []
    start_ms = now_ms - count * FOUR_H_MS
    for i in range(count - 1):
        open_ms = start_ms + i * FOUR_H_MS
        px = 70_000.0 + i * 50.0
        bars.append(_make_bar(open_ms, px - 40.0, px + 120.0, px - 120.0, px, is_closed=True))

    cfg = TrendPullbackConfig()
    trend_res = calculate_trend(bars, cfg)
    ema50 = trend_res["ema50"]
    atr14 = trend_res["atr14"]

    # Last completed 4H candle: dips into [EMA50 - 0.50*ATR, EMA50 + 0.25*ATR] and closes bullishly above EMA50
    last_open_ms = start_ms + (count - 1) * FOUR_H_MS
    rec_low = ema50 - 0.15 * atr14
    rec_open = ema50 - 0.05 * atr14
    rec_close = ema50 + 0.20 * atr14
    rec_high = ema50 + 0.35 * atr14
    bars.append(_make_bar(last_open_ms, rec_open, rec_high, rec_low, rec_close, is_closed=True))
    return bars


def _build_1h_bars(count: int = 900, now_ms: int = NOW_MS, base_px: float = 80_000.0) -> List[KlineBar]:
    bars: List[KlineBar] = []
    start_ms = now_ms - count * ONE_H_MS
    for i in range(count):
        open_ms = start_ms + i * ONE_H_MS
        px = base_px + (i - count) * 10.0
        bars.append(_make_bar(open_ms, px - 10.0, px + 30.0, px - 30.0, px, is_closed=True))
    return bars


def test_01_bullish_daily_regime() -> None:
    """1. Bullish daily regime requires Close > SMA200 AND SMA200 > SMA200[-20]."""
    cfg = TrendPullbackConfig()
    bars_1d = _build_bullish_1d_bars(230)
    res = calculate_regime(bars_1d, cfg)
    assert res["regime"] == "BULLISH"
    assert res["last_close"] > res["sma200"]
    assert res["sma200_slope_20d"] > 0.0
    assert res["sma200_rising"] is True


def test_02_non_bullish_daily_regime() -> None:
    """2. Non-bullish daily regime when Close <= SMA200 or SMA200 slope <= 0."""
    cfg = TrendPullbackConfig()
    bars_1d = _build_bullish_1d_bars(230)
    last = bars_1d[-1]
    bars_1d[-1] = _make_bar(last.timestamp_ms, 65_000.0, 65_500.0, 64_000.0, 64_500.0)
    res = calculate_regime(bars_1d, cfg)
    assert res["regime"] == "NOT BULLISH"

    # Falling 20D SMA200 slope even if last close spikes above SMA200
    falling_bars: List[KlineBar] = []
    for i in range(230):
        px = 90_000.0 - i * 100.0
        falling_bars.append(_make_bar(NOW_MS - (230 - i) * DAY_MS, px, px + 100, px - 100, px))
    falling_bars[-1] = _make_bar(NOW_MS - DAY_MS, 85_000.0, 86_000.0, 84_000.0, 85_500.0)
    res_falling = calculate_regime(falling_bars, cfg)
    assert res_falling["sma200_slope_20d"] < 0.0
    assert res_falling["regime"] == "NOT BULLISH"


def test_03_confirmed_4h_trend() -> None:
    """3. Confirmed 4H trend requires EMA50 > EMA200, EMA50 > EMA50[-6], and Close > EMA200."""
    cfg = TrendPullbackConfig()
    bars_4h = _build_bullish_4h_bars(220)
    res = calculate_trend(bars_4h, cfg)
    assert res["trend"] == "CONFIRMED"
    assert res["ema50"] > res["ema200"]
    assert res["ema50_slope_6bars"] > 0.0
    assert res["last_close"] > res["ema200"]


def test_04_failed_4h_trend() -> None:
    """4. Failed 4H trend when EMA50 <= EMA200, EMA50 slope <= 0, or Close <= EMA200."""
    cfg = TrendPullbackConfig()
    bars_4h: List[KlineBar] = []
    for i in range(220):
        px = 85_000.0 - i * 40.0
        bars_4h.append(_make_bar(NOW_MS - (220 - i) * FOUR_H_MS, px, px + 50, px - 50, px))
    res = calculate_trend(bars_4h, cfg)
    assert res["trend"] == "NOT CONFIRMED"
    assert res["ema50"] < res["ema200"]


def test_05_valid_pullback_recovery() -> None:
    """5. Valid pullback recovery candle inside [EMA50 - 0.50*ATR, EMA50 + 0.25*ATR] closing bullishly above EMA50."""
    cfg = TrendPullbackConfig()
    bars_4h = _build_bullish_4h_bars(220)
    tr = calculate_trend(bars_4h, cfg)
    pb = detect_pullback(bars_4h, tr["ema50_series"], tr["atr14_series"], cfg)
    assert pb["recovery_candle"] == "CONFIRMED"
    assert pb["setup_status"] == "CONFIRMED"
    assert pb["bars_since_recovery"] == 0


def test_06_deep_pullback_rejection() -> None:
    """6. Deep pullback rejection when candle low drops below EMA50 - 0.50*ATR14."""
    cfg = TrendPullbackConfig()
    bars_4h = _build_bullish_4h_bars(220)
    tr = calculate_trend(bars_4h[:-1], cfg)
    ema50 = tr["ema50"]
    atr14 = tr["atr14"]
    last_ms = bars_4h[-1].timestamp_ms
    bars_4h[-1] = _make_bar(
        last_ms,
        ema50 - 0.10 * atr14,
        ema50 + 0.30 * atr14,
        ema50 - 0.80 * atr14,
        ema50 + 0.15 * atr14,
    )
    tr_full = calculate_trend(bars_4h, cfg)
    pb = detect_pullback(bars_4h, tr_full["ema50_series"], tr_full["atr14_series"], cfg)
    assert pb["recovery_candle"] == "NOT CONFIRMED"
    assert "Deep pullback rejected" in pb["reason"]


def test_07_breakout_chasing_rejection() -> None:
    """7. Breakout-chasing rejection when recovery candle closes > EMA50 + 1.0*ATR14."""
    cfg = TrendPullbackConfig()
    bars_4h = _build_bullish_4h_bars(220)
    tr = calculate_trend(bars_4h[:-1], cfg)
    ema50 = tr["ema50"]
    atr14 = tr["atr14"]
    last_ms = bars_4h[-1].timestamp_ms
    bars_4h[-1] = _make_bar(
        last_ms,
        ema50,
        ema50 + 2.0 * atr14,
        ema50 - 0.10 * atr14,
        ema50 + 1.80 * atr14,
    )
    tr_full = calculate_trend(bars_4h, cfg)
    pb = detect_pullback(bars_4h, tr_full["ema50_series"], tr_full["atr14_series"], cfg)
    assert pb["recovery_candle"] == "NOT CONFIRMED"
    assert "Breakout chasing rejected" in pb["reason"]


def test_08_invalid_stop_distance() -> None:
    """8. Invalid stop distance rejection when stop distance < 0.75 ATR, > 3.0 ATR, or stop >= entry."""
    cfg = TrendPullbackConfig()
    atr14 = 1_000.0
    ref_entry = 80_000.0

    # Case A: Stop too tight (< 0.75 ATR = $750)
    bars_tight = [
        _make_bar(NOW_MS - (5 - j) * FOUR_H_MS, 79_900, 80_200, 79_850, 80_000)
        for j in range(5)
    ]
    res_tight = calculate_stop(bars_tight, atr14, ref_entry, cfg)
    assert res_tight["valid"] is False
    assert "< minimum 0.75 ATR" in res_tight["reason"]

    # Case B: Stop too wide (> 3.0 ATR = $3,000)
    bars_wide = [
        _make_bar(NOW_MS - (5 - j) * FOUR_H_MS, 79_000, 80_200, 75_500, 79_500)
        for j in range(5)
    ]
    res_wide = calculate_stop(bars_wide, atr14, ref_entry, cfg)
    assert res_wide["valid"] is False
    assert "> maximum 3.00 ATR" in res_wide["reason"]

    # Case C: Valid stop distance (between 0.75 ATR and 3.0 ATR)
    bars_valid = [
        _make_bar(NOW_MS - (5 - j) * FOUR_H_MS, 79_200, 80_200, 78_800, 79_500)
        for j in range(5)
    ]
    res_valid = calculate_stop(bars_valid, atr14, ref_entry, cfg)
    assert res_valid["valid"] is True
    assert 0.75 <= res_valid["stop_distance_atr"] <= 3.00


def test_09_correct_position_sizing() -> None:
    """9. Correct position sizing with $100,000 reference equity, 0.50% risk ($500), fee+slippage, and 100% spot cap."""
    cfg = TrendPullbackConfig()
    sz = calculate_position_size(80_000.0, 78_500.0, cfg)
    assert sz["equity_usd"] == 100_000.0
    assert sz["risk_budget_usd"] == 500.0
    assert sz["position_size_btc"] > 0.0
    assert sz["position_value_usd"] <= 100_000.0
    # Verify round-trip fee + slippage is included (size < raw 500 / 1500 = 0.33333 BTC)
    assert sz["position_size_btc"] < (500.0 / 1_500.0)

    # Cap test: if stop is very close, notional must never exceed $100,000
    sz_cap = calculate_position_size(80_000.0, 79_900.0, cfg)
    assert sz_cap["position_value_usd"] <= 100_000.0
    assert sz_cap["position_size_btc"] <= (100_000.0 / 80_000.0)


def test_10_stop_loss_breach() -> None:
    """10. Stop-loss breach triggers EXIT ALERT when holding and spot <= stop."""
    cfg = TrendPullbackConfig()
    bars_1d = _build_bullish_1d_bars(230)
    bars_4h = _build_bullish_4h_bars(220)
    reg = calculate_regime(bars_1d, cfg)
    tr = calculate_trend(bars_4h, cfg)

    ex = evaluate_exit(
        current_price=77_900.0,
        stop_price=78_000.0,
        completed_4h_bars=bars_4h,
        ema50_4h_series=tr["ema50_series"],
        completed_1d_bars=bars_1d,
        sma200_1d_series=reg["sma200_series"],
        position_status="HOLDING",
    )
    assert ex["stop_breached"] is True
    assert ex["exit_conditions_status"] == "TRIGGERED"

    verdict = generate_strategy_verdict(
        data_integrity_ok=True,
        integrity_reason="",
        daily_regime="BULLISH",
        regime_reason="",
        trend_4h="CONFIRMED",
        trend_reason="",
        recovery_candle="NOT CONFIRMED",
        setup_status="WAIT",
        pullback_reason="",
        stop_valid=True,
        stop_reason="",
        current_price=77_900.0,
        limit_entry_low=79_000.0,
        limit_entry_high=79_100.0,
        position_status="HOLDING",
        exit_eval=ex,
    )
    assert verdict["strategy_verdict"] == "EXIT ALERT"
    assert verdict["decision_state"] == "EXIT CONDITION"


def test_11_two_candle_4h_ema50_exit() -> None:
    """11. Two consecutive completed 4H closes below 4H EMA50 triggers EXIT CONDITION."""
    cfg = TrendPullbackConfig()
    bars_1d = _build_bullish_1d_bars(230)
    bars_4h = _build_bullish_4h_bars(220)
    for idx in (-2, -1):
        b = bars_4h[idx]
        bars_4h[idx] = _make_bar(b.timestamp_ms, 72_000.0, 72_200.0, 71_500.0, 71_800.0)
    reg = calculate_regime(bars_1d, cfg)
    tr = calculate_trend(bars_4h, cfg)

    ex = evaluate_exit(
        current_price=71_800.0,
        stop_price=70_000.0,
        completed_4h_bars=bars_4h,
        ema50_4h_series=tr["ema50_series"],
        completed_1d_bars=bars_1d,
        sma200_1d_series=reg["sma200_series"],
        position_status="HOLDING",
    )
    assert ex["two_4h_below_ema50"] is True
    assert ex["exit_conditions_status"] == "TRIGGERED"


def test_12_two_day_1d_sma200_exit() -> None:
    """12. Two consecutive completed daily closes below 1D SMA200 triggers EXIT CONDITION."""
    cfg = TrendPullbackConfig()
    bars_1d = _build_bullish_1d_bars(230)
    bars_4h = _build_bullish_4h_bars(220)
    for idx in (-2, -1):
        b = bars_1d[idx]
        bars_1d[idx] = _make_bar(b.timestamp_ms, 62_000.0, 62_500.0, 61_000.0, 61_500.0)
    reg = calculate_regime(bars_1d, cfg)
    tr = calculate_trend(bars_4h, cfg)

    ex = evaluate_exit(
        current_price=80_000.0,
        stop_price=70_000.0,
        completed_4h_bars=bars_4h,
        ema50_4h_series=tr["ema50_series"],
        completed_1d_bars=bars_1d,
        sma200_1d_series=reg["sma200_series"],
        position_status="HOLDING",
    )
    assert ex["two_1d_below_sma200"] is True
    assert ex["exit_conditions_status"] == "TRIGGERED"


def test_13_incomplete_candle_rejection() -> None:
    """13. Incomplete/forming candle is stripped and never used to generate a confirmed signal."""
    bars_1d = _build_bullish_1d_bars(225, now_ms=NOW_MS)
    # Append an incomplete daily candle (open at NOW_MS, closes at NOW_MS + DAY_MS) with a crash close
    bars_1d.append(_make_bar(NOW_MS, 82_000.0, 82_100.0, 50_000.0, 50_000.0, is_closed=False))
    ok, status, completed, err = verify_and_extract_completed_candles(
        bars_1d,
        tf_ms=DAY_MS,
        min_required=220,
        now_ms=NOW_MS + 1_000,
        max_stale_hours=48.0,
        label="Daily (1D)",
    )
    assert ok is True
    assert status == "LAST CLOSE"
    assert len(completed) == 225
    assert completed[-1].close > 80_000.0  # Unclosed crash candle was excluded


def test_14_missing_data_rejection() -> None:
    """14. Missing or insufficient candle count returns DATA UNAVAILABLE and blocks entries."""
    store = StateStore()
    store.binance_spot_price = 80_000.0
    engine = TrendPullbackEngine()
    ev = engine.evaluate(store, now_ms=NOW_MS)
    assert ev.data_integrity_ok is False
    assert ev.decision_state == "DATA UNAVAILABLE"
    assert ev.strategy_verdict == "NO TRADE"
    assert ev.daily_candle_status == "UNAVAILABLE"


def test_15_stale_data_rejection() -> None:
    """15. Stale candle timestamps return STALE and DATA UNAVAILABLE."""
    store = StateStore()
    store.binance_spot_price = 80_000.0
    old_ms = NOW_MS - 10 * DAY_MS
    store.spot_klines_1d.extend(_build_bullish_1d_bars(230, now_ms=old_ms))
    store.spot_klines_1h.extend(_build_1h_bars(900, now_ms=old_ms))
    engine = TrendPullbackEngine()
    ev = engine.evaluate(store, now_ms=NOW_MS)
    assert ev.daily_candle_status == "STALE"
    assert ev.data_integrity_ok is False
    assert ev.decision_state == "DATA UNAVAILABLE"
    assert ev.strategy_verdict == "NO TRADE"


def test_16_setup_expiry() -> None:
    """16. Setup expires when more than 3 completed 4H candles have elapsed without valid entry."""
    cfg = TrendPullbackConfig()
    bars_4h = _build_bullish_4h_bars(220)
    tr = calculate_trend(bars_4h, cfg)
    ema50 = tr["ema50"]
    atr14 = tr["atr14"]

    for j in range(1, 5):
        open_ms = NOW_MS + j * FOUR_H_MS
        high_px = ema50 + 0.80 * atr14
        low_px = ema50 + 0.40 * atr14
        bars_4h.append(_make_bar(open_ms, low_px + 10.0, high_px, low_px, high_px - 10.0))

    tr_after = calculate_trend(bars_4h, cfg)
    pb_after = detect_pullback(bars_4h, tr_after["ema50_series"], tr_after["atr14_series"], cfg)
    assert pb_after["recovery_candle"] == "NOT CONFIRMED"
    assert pb_after["setup_status"] == "EXPIRED"
    assert pb_after["bars_since_recovery"] > cfg.setup_expiry_4h_bars


def test_17_cash_vs_holding_decision_logic() -> None:
    """17. Evaluates full CASH (ENTRY READY / WAIT / NO TRADE) vs HOLDING (HOLD / EXIT ALERT) state transitions."""
    cfg = TrendPullbackConfig()
    bars_1d = _build_bullish_1d_bars(230)
    bars_4h = _build_bullish_4h_bars(220)

    reg = calculate_regime(bars_1d, cfg)
    tr = calculate_trend(bars_4h, cfg)
    pb = detect_pullback(bars_4h, tr["ema50_series"], tr["atr14_series"], cfg)
    ez = calculate_entry_zone(tr["ema50"], tr["atr14"], cfg)

    # Ensure last 5 4H bars have a low that places stop inside [0.75, 3.00] ATR
    atr14 = tr["atr14"]
    ref_entry = ez["reference_entry"]
    bars_4h[-2] = _make_bar(
        bars_4h[-2].timestamp_ms,
        ref_entry - 0.5 * atr14,
        ref_entry,
        ref_entry - 1.2 * atr14,
        ref_entry - 0.3 * atr14,
    )
    st = calculate_stop(bars_4h, atr14, ref_entry, cfg)
    assert st["valid"] is True

    # Spot price inside limit entry zone -> ENTRY READY
    spot_in_zone = ez["entry_high"] - 5.0
    ex_cash = evaluate_exit(
        current_price=spot_in_zone,
        stop_price=st["stop_price"],
        completed_4h_bars=bars_4h,
        ema50_4h_series=tr["ema50_series"],
        completed_1d_bars=bars_1d,
        sma200_1d_series=reg["sma200_series"],
        position_status="CASH",
    )
    verdict_entry = generate_strategy_verdict(
        data_integrity_ok=True,
        integrity_reason="",
        daily_regime=reg["regime"],
        regime_reason=reg["reason"],
        trend_4h=tr["trend"],
        trend_reason=tr["reason"],
        recovery_candle=pb["recovery_candle"],
        setup_status=pb["setup_status"],
        pullback_reason=pb["reason"],
        stop_valid=st["valid"],
        stop_reason=st["reason"],
        current_price=spot_in_zone,
        limit_entry_low=ez["entry_low"],
        limit_entry_high=ez["entry_high"],
        position_status="CASH",
        exit_eval=ex_cash,
    )
    assert verdict_entry["decision_state"] == "ENTRY SETUP CONFIRMED"
    assert verdict_entry["strategy_verdict"] == "ENTRY READY"

    # Switch to HOLDING with healthy trend and price above stop -> HOLD
    ex_hold = evaluate_exit(
        current_price=spot_in_zone,
        stop_price=st["stop_price"],
        completed_4h_bars=bars_4h,
        ema50_4h_series=tr["ema50_series"],
        completed_1d_bars=bars_1d,
        sma200_1d_series=reg["sma200_series"],
        position_status="HOLDING",
    )
    verdict_hold = generate_strategy_verdict(
        data_integrity_ok=True,
        integrity_reason="",
        daily_regime=reg["regime"],
        regime_reason=reg["reason"],
        trend_4h=tr["trend"],
        trend_reason=tr["reason"],
        recovery_candle=pb["recovery_candle"],
        setup_status=pb["setup_status"],
        pullback_reason=pb["reason"],
        stop_valid=st["valid"],
        stop_reason=st["reason"],
        current_price=spot_in_zone,
        limit_entry_low=ez["entry_low"],
        limit_entry_high=ez["entry_high"],
        position_status="HOLDING",
        exit_eval=ex_hold,
    )
    assert verdict_hold["decision_state"] == "HOLD / MANAGE POSITION"
    assert verdict_hold["strategy_verdict"] == "HOLD"


def test_18_tui_and_ai_packet_integration() -> None:
    """Verifies Tab 18 ([A: BTC STRATEGY]) renders cleanly in Rich TUI and exports in Section 18 of AI Packet."""
    config = EngineConfig()
    store = StateStore()
    store.binance_spot_price = 80_500.0
    store.spot_klines_1d.extend(_build_bullish_1d_bars(230, now_ms=NOW_MS))
    store.spot_klines_1h.extend(_build_1h_bars(900, now_ms=NOW_MS, base_px=80_500.0))

    engine = TrendPullbackEngine(config)
    ev = engine.evaluate(store, now_ms=NOW_MS)
    assert ev.strategy_name == "BTC TREND-PULLBACK v1.0"
    assert ev.strategy_status == "UNVALIDATED"
    assert ev.mode_label == "RESEARCH / PAPER MODE"

    console = Console(width=175, record=True)
    renderable = build_dashboard_renderable(config, store, tab_override=18)
    console.print(renderable)
    output = console.export_text()

    assert "BTC TREND-PULLBACK v1.0" in output
    assert "STRATEGY STATUS: UNVALIDATED" in output
    assert "RESEARCH / PAPER MODE" in output
    assert "MARKET REGIME" in output
    assert "4H TREND FILTER" in output
    assert "PULLBACK ANALYSIS" in output
    assert "TRADE PLAN" in output
    assert "POSITION MANAGEMENT" in output
    assert "DATA INTEGRITY" in output
    assert "STRATEGY VERDICT" in output

    packet = build_ai_telemetry_packet(config, store)
    assert "SECTION 18: TAB [A] BTC TREND-PULLBACK v1.0" in packet
