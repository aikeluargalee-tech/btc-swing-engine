"""BTC Short-Term Futures + Inventory Protocol v4.0 Engine (Tab 20 / [X]).

Implements:
- 4H / Day-Trade Only (4-24h intended hold, 1:2 max leverage)
- Three directional actions: LONG futures, SHORT futures, SELL INVENTORY (spot reduction), plus FLAT
- 4H Multi-Factor Regime Engine (Trend Structure 30%, Momentum 25%, Volatility & Liquidity 25%, Session/Context 20%)
- 9-Point Futures Qualification Checklist (68/32 thresholds, strict 33-67 Flat zone, <= 2.2% stop, >= 1.6:1 R:R, 60m blackout)
- Independent Sell Inventory option on score <= 32 with 4H structural reference (15-25%, default 20%, 0% futures heat)
- Full trade management (BE @ 1R, 45% partial @ 1.5R, 8h/12h time stops, 24h max hold, daily close rule, weekend 80/20 half-size)
- 5-Tier Circuit Breakers (-1.2% intraday, -2.0% daily, -4.0% weekly flatten, -6.0% DD tier1, -10.0% DD tier2 flatten/lock)
"""

from __future__ import annotations

import json
import math
import statistics
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from config.settings import EngineConfig
from core.models import KlineBar
from core.state_store import StateStore
from .volume_profile import synthesize_4h_bars


def _clamp(v: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, v))


def _map_linear(val: float, low_in: float, high_in: float, low_out: float = 0.0, high_out: float = 100.0) -> float:
    if high_in == low_in:
        return 50.0
    t = (val - low_in) / (high_in - low_in)
    return _clamp(low_out + t * (high_out - low_out), min(low_out, high_out), max(low_out, high_out))


def _ema_series(values: Sequence[float], period: int) -> List[float]:
    if len(values) < period or period <= 0:
        return []
    k = 2.0 / (period + 1)
    out = [sum(values[:period]) / period]
    for v in values[period:]:
        out.append(v * k + out[-1] * (1.0 - k))
    return out


def _rsi(closes: Sequence[float], period: int = 14) -> Optional[float]:
    if len(closes) <= period:
        return None
    deltas = [b - a for a, b in zip(closes, closes[1:])]
    gains = [max(d, 0.0) for d in deltas]
    losses = [abs(min(d, 0.0)) for d in deltas]
    avg_g = sum(gains[:period]) / period
    avg_l = sum(losses[:period]) / period
    for g, l in zip(gains[period:], losses[period:]):
        avg_g = (avg_g * (period - 1) + g) / period
        avg_l = (avg_l * (period - 1) + l) / period
    if avg_l == 0.0:
        return 100.0
    rs = avg_g / avg_l
    return round(100.0 - 100.0 / (1.0 + rs), 2)


def _roc(closes: Sequence[float], period: int) -> Optional[float]:
    if len(closes) <= period or closes[-period - 1] <= 0:
        return None
    return (closes[-1] / closes[-period - 1] - 1.0) * 100.0


def _atr_series(bars: Sequence[Dict[str, float]], period: int = 14) -> List[float]:
    if len(bars) <= period:
        return []
    trs = [
        max(
            cur["high"] - cur["low"],
            abs(cur["high"] - prev["close"]),
            abs(cur["low"] - prev["close"]),
        )
        for prev, cur in zip(bars, bars[1:])
    ]
    if len(trs) < period:
        return []
    val = sum(trs[:period]) / period
    out = [val]
    for tr in trs[period:]:
        val = (val * (period - 1) + tr) / period
        out.append(val)
    return out


def _percentile_rank(value: float, history: Sequence[float]) -> Optional[float]:
    if not history:
        return None
    le = sum(1 for x in history if x <= value)
    return round(le / len(history) * 100.0, 2)


def _swing_pivots(
    bars: Sequence[Dict[str, float]], left: int = 3, right: int = 3
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    highs: List[Dict[str, Any]] = []
    lows: List[Dict[str, Any]] = []
    n = len(bars)
    for i in range(left, n - right):
        hi = bars[i]["high"]
        lo = bars[i]["low"]
        if all(hi >= bars[j]["high"] for j in range(i - left, i + right + 1) if j != i):
            highs.append({"idx": i, "ts": bars[i]["ts"], "price": hi})
        if all(lo <= bars[j]["low"] for j in range(i - left, i + right + 1) if j != i):
            lows.append({"idx": i, "ts": bars[i]["ts"], "price": lo})
    return highs, lows


def _analyze_structure(bars: Sequence[Dict[str, float]], left: int = 3, right: int = 3) -> Dict[str, Any]:
    highs, lows = _swing_pivots(bars, left=left, right=right)
    if len(highs) < 2 or len(lows) < 2:
        if len(bars) >= 10:
            chg = (bars[-1]["close"] / max(bars[-10]["close"], 1.0) - 1.0) * 100.0
            return {
                "state": "BULL_SLOPE" if chg > 1.5 else ("BEAR_SLOPE" if chg < -1.5 else "RANGE"),
                "score": _map_linear(chg, -6.0, 6.0, 20.0, 80.0),
                "last_swing_high": highs[-1]["price"] if highs else None,
                "last_swing_low": lows[-1]["price"] if lows else None,
            }
        return {"state": "UNKNOWN", "score": 50.0, "last_swing_high": None, "last_swing_low": None}

    hh = highs[-1]["price"] > highs[-2]["price"]
    hl = lows[-1]["price"] > lows[-2]["price"]
    lh = highs[-1]["price"] < highs[-2]["price"]
    ll = lows[-1]["price"] < lows[-2]["price"]

    if hh and hl:
        state, sc = "BULLISH_HH_HL", 88.0
    elif lh and ll:
        state, sc = "BEARISH_LH_LL", 12.0
    elif hl and not hh:
        state, sc = "BULLISH_CONSOLIDATION", 65.0
    elif lh and not ll:
        state, sc = "BEARISH_CONSOLIDATION", 35.0
    else:
        state, sc = "MIXED_CHOP", 50.0
    return {
        "state": state,
        "score": sc,
        "last_swing_high": highs[-1]["price"],
        "last_swing_low": lows[-1]["price"],
    }


def _synthesize_daily_bars(h4_bars: Sequence[Dict[str, float]]) -> List[Dict[str, float]]:
    """Aggregate 4H bars into UTC daily bars as a fallback if 1D cache is sparse."""
    buckets: Dict[int, List[Dict[str, float]]] = {}
    day_ms = 86_400_000
    for b in h4_bars:
        key = (int(b["ts"]) // day_ms) * day_ms
        buckets.setdefault(key, []).append(b)
    out: List[Dict[str, float]] = []
    for ts in sorted(buckets.keys()):
        grp = buckets[ts]
        out.append(
            {
                "ts": ts,
                "open": grp[0]["open"],
                "high": max(x["high"] for x in grp),
                "low": min(x["low"] for x in grp),
                "close": grp[-1]["close"],
                "volume": sum(x["volume"] for x in grp),
            }
        )
    return out


def _score_rsi_4h(val: Optional[float]) -> float:
    if val is None:
        return 50.0
    if 54.0 <= val <= 72.0:
        return _map_linear(val, 54.0, 72.0, 68.0, 90.0)
    if val > 72.0:
        return _map_linear(val, 72.0, 90.0, 90.0, 68.0)
    if 28.0 <= val < 46.0:
        return _map_linear(val, 28.0, 46.0, 10.0, 32.0)
    if val < 28.0:
        return _map_linear(val, 10.0, 28.0, 32.0, 10.0)
    return _map_linear(val, 46.0, 54.0, 32.0, 68.0)


@dataclass
class FuturesV4ChecklistItem:
    id: int
    rule: str
    passed: bool
    detail: str


@dataclass
class FuturesV4Evaluation:
    protocol_version: str = "4.0"
    regime_score: float = 50.0
    regime_bias: str = "FLAT"          # LONG | SHORT | FLAT
    daily_bias: str = "NEUTRAL"        # BULL | BEAR | NEUTRAL
    futures_status: str = "FLAT"       # LONG | SHORT | FLAT
    active_signals: List[str] = field(default_factory=lambda: ["FLAT"])
    long_threshold: float = 68.0
    short_threshold: float = 32.0
    is_weekend_utc: bool = False
    last_4h_close_utc: str = "—"
    dominant_factors: List[str] = field(default_factory=list)
    factor_scores: Dict[str, float] = field(default_factory=dict)
    factor_summaries: Dict[str, str] = field(default_factory=dict)
    checklist: List[FuturesV4ChecklistItem] = field(default_factory=list)
    rejection_reasons: List[str] = field(default_factory=list)
    # Futures sizing proposal
    eval_direction: str = "FLAT"
    entry_method: str = "—"
    entry_price: float = 0.0
    stop_price: float = 0.0
    target1_price: float = 0.0
    target1_label: str = "—"
    stop_distance_pct: float = 0.0
    raw_rr: float = 0.0
    funding_adj_rr: float = 0.0
    size_btc: float = 0.0
    notional_usd: float = 0.0
    leverage: float = 0.0
    leverage_capped: bool = False
    actual_risk_pct: float = 0.0
    actual_risk_usd: float = 0.0
    weekend_halved: bool = False
    # Sell Inventory option
    sell_inventory_active: bool = False
    sell_inventory_pct: float = 20.0
    sell_inventory_btc: float = 0.0
    sell_inventory_usd: float = 0.0
    sell_inventory_ref: str = "—"
    sell_inventory_reason: str = "—"
    # Ledger & Circuit Breakers
    equity_usd: float = 100000.0
    realized_equity_usd: float = 100000.0
    drawdown_pct: float = 0.0
    intraday_pnl_pct: float = 0.0
    daily_pnl_pct: float = 0.0
    weekly_pnl_pct: float = 0.0
    open_heat_pct: float = 0.0
    max_heat_pct: float = 1.5
    breakers: Dict[str, bool] = field(default_factory=dict)
    open_positions: List[Dict[str, Any]] = field(default_factory=list)
    closed_trades: List[Dict[str, Any]] = field(default_factory=list)
    audit_log: List[Dict[str, Any]] = field(default_factory=list)
    review_win_rate_pct: float = 0.0
    review_profit_factor: float = 0.0
    review_expectancy_r: float = 0.0
    total_closed_legs: int = 0
    evaluated_utc: str = ""


class FuturesV4Engine:
    """Configurable Version 4.0 engine integrated with btc_swing_engine's StateStore."""

    def __init__(self, config: EngineConfig, read_only: bool = True) -> None:
        self.config = config
        self.read_only = read_only
        self._ledger: Dict[str, Any] = self._load_or_init_ledger(datetime.now(timezone.utc))

    def set_read_only(self, read_only: bool) -> None:
        self.read_only = read_only

    def reset_review_lock(self, now: Optional[datetime] = None) -> None:
        now = now or datetime.now(timezone.utc)
        b = self._ledger["breakers"]
        b["dd_tier2_locked"] = False
        b["dd_tier1_active"] = False
        eq = float(self._ledger["equity"])
        self._ledger["high_water_mark"] = eq
        self._ledger["drawdown_pct"] = 0.0
        self._ledger["day_start_equity"] = eq
        self._ledger["intraday_peak_equity"] = eq
        self._ledger["week_start_equity"] = eq
        self._append_audit(now, "MANUAL_REVIEW_UNLOCK", f"Cleared -10% DD lock at ${eq:,.2f}")
        self._save_ledger()

    def _init_ledger(self, now: datetime) -> Dict[str, Any]:
        eq = float(self.config.futures_v4_equity_usd)
        iso = now.isocalendar()
        return {
            "protocol_version": "4.0",
            "initial_equity": eq,
            "realized_equity": eq,
            "equity": eq,
            "high_water_mark": eq,
            "drawdown_pct": 0.0,
            "spot_inventory_btc": float(self.config.futures_v4_spot_inventory_btc),
            "day_key": now.strftime("%Y-%m-%d"),
            "day_start_equity": eq,
            "intraday_peak_equity": eq,
            "week_key": f"{iso.year}-W{iso.week:02d}",
            "week_start_equity": eq,
            "breakers": {
                "intraday_halted": False,
                "daily_halted": False,
                "weekly_halted": False,
                "dd_tier1_active": False,
                "dd_tier2_locked": False,
            },
            "last_sell_inventory_4h_ts": None,
            "open_positions": [],
            "closed_trades": [],
            "audit_log": [
                {
                    "ts": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "event": "LEDGER_INIT_V4",
                    "detail": f"Initialized v4.0 paper ledger ${eq:,.2f} / {self.config.futures_v4_spot_inventory_btc:.2f} BTC spot",
                }
            ],
        }

    def _load_or_init_ledger(self, now: datetime) -> Dict[str, Any]:
        path: Path = self.config.futures_v4_ledger_path
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(data, dict) and "equity" in data and "breakers" in data:
                    return data
            except Exception:
                pass
        return self._init_ledger(now)

    def _save_ledger(self) -> None:
        if self.read_only:
            return
        path: Path = self.config.futures_v4_ledger_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self._ledger, indent=2), encoding="utf-8")

    def _append_audit(self, now: datetime, event: str, detail: str) -> None:
        self._ledger["audit_log"].append(
            {"ts": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "event": event, "detail": detail}
        )
        self._ledger["audit_log"] = self._ledger["audit_log"][-80:]

    @staticmethod
    def _to_bars(klines: Sequence[KlineBar]) -> List[Dict[str, float]]:
        return [
            {
                "ts": float(b.timestamp_ms),
                "open": float(b.open),
                "high": float(b.high),
                "low": float(b.low),
                "close": float(b.close),
                "volume": float(b.volume),
            }
            for b in klines
            if b.close > 0
        ]

    def _identify_levels(self, d1: List[Dict[str, float]], h4: List[Dict[str, float]]) -> List[Dict[str, Any]]:
        levels: List[Dict[str, Any]] = []
        last_d = d1[-1]
        levels.append({"price": round(last_d["high"], 1), "label": "Prior 1D High", "kind": "resistance"})
        levels.append({"price": round(last_d["low"], 1), "label": "Prior 1D Low", "kind": "support"})
        levels.append({"price": round(last_d["open"], 1), "label": "Daily Open", "kind": "pivot"})

        last_4h = h4[-1]
        levels.append({"price": round(last_4h["high"], 1), "label": "Prior 4H High", "kind": "resistance"})
        levels.append({"price": round(last_4h["low"], 1), "label": "Prior 4H Low", "kind": "support"})

        h4_hi, h4_lo = _swing_pivots(h4[-120:], left=3, right=3)
        for idx, sh in enumerate(h4_hi[-3:], 1):
            levels.append({"price": round(sh["price"], 1), "label": f"4H Swing High #{idx}", "kind": "resistance"})
        for idx, sl in enumerate(h4_lo[-3:], 1):
            levels.append({"price": round(sl["price"], 1), "label": f"4H Swing Low #{idx}", "kind": "support"})

        # Simple 30D volume profile POC/VAH/VAL
        slice_d = d1[-30:]
        if slice_d:
            lo_p = min(c["low"] for c in slice_d)
            hi_p = max(c["high"] for c in slice_d)
            bw = 100.0
            n_bins = max(1, int((hi_p - lo_p) / bw) + 1)
            bins = [0.0] * n_bins
            for c in slice_d:
                typ = (c["high"] + c["low"] + c["close"]) / 3.0
                idx = min(n_bins - 1, max(0, int((typ - lo_p) / bw)))
                bins[idx] += c["volume"]
            poc_i = max(range(n_bins), key=lambda i: bins[i])
            total_v = sum(bins)
            if total_v > 0:
                target = 0.70 * total_v
                acc = bins[poc_i]
                l_i = r_i = poc_i
                while acc < target and (l_i > 0 or r_i < n_bins - 1):
                    lv = bins[l_i - 1] if l_i > 0 else -1.0
                    rv = bins[r_i + 1] if r_i < n_bins - 1 else -1.0
                    if rv >= lv and r_i < n_bins - 1:
                        r_i += 1
                        acc += bins[r_i]
                    elif l_i > 0:
                        l_i -= 1
                        acc += bins[l_i]
                    else:
                        break
                levels.append({"price": round(lo_p + (poc_i + 0.5) * bw, 1), "label": "30D VPOC", "kind": "volume"})
                levels.append({"price": round(lo_p + (r_i + 0.5) * bw, 1), "label": "30D VAH", "kind": "volume"})
                levels.append({"price": round(lo_p + (l_i + 0.5) * bw, 1), "label": "30D VAL", "kind": "volume"})

        levels.sort(key=lambda x: x["price"])
        deduped: List[Dict[str, Any]] = []
        for lv in levels:
            if deduped and abs(lv["price"] - deduped[-1]["price"]) / max(lv["price"], 1.0) < 0.0012:
                continue
            deduped.append(lv)
        return deduped

    @staticmethod
    def _detect_confirmation(h4: List[Dict[str, float]], direction: str, level_price: Optional[float]) -> Dict[str, Any]:
        if len(h4) < 25:
            return {"confirmed": False, "type": None, "reason": "Need >= 25 4H bars"}
        last = h4[-1]
        vols = [c["volume"] for c in h4[-21:-1]]
        avg_v = sum(vols) / len(vols) if vols else 1.0
        vol_ratio = last["volume"] / avg_v if avg_v > 0 else 1.0
        rng = max(last["high"] - last["low"], 1e-6)
        lower_wick = min(last["open"], last["close"]) - last["low"]
        upper_wick = last["high"] - max(last["open"], last["close"])
        body = abs(last["close"] - last["open"])

        if direction == "LONG":
            prior_high = max(c["high"] for c in h4[-10:-1])
            bos = last["close"] > prior_high and vol_ratio >= 0.90
            wick_ok = lower_wick >= max(body * 1.5, rng * 0.40) and last["close"] > last["open"] and vol_ratio >= 0.90
            if level_price and last["low"] <= level_price <= last["close"] and wick_ok:
                return {"confirmed": True, "type": "REJECTION_CANDLE", "detail": f"4H bullish rejection @ {level_price:,.1f} (vol {vol_ratio:.2f}x)"}
            if bos:
                return {"confirmed": True, "type": "STRUCTURE_BREAK", "detail": f"4H BOS close {last['close']:,.1f} > {prior_high:,.1f} (vol {vol_ratio:.2f}x)"}
            if wick_ok:
                return {"confirmed": True, "type": "REJECTION_CANDLE", "detail": f"4H bullish hammer wick (vol {vol_ratio:.2f}x)"}
            return {"confirmed": False, "type": None, "reason": f"No 4H LONG BOS/rejection+vol (vol {vol_ratio:.2f}x)"}

        prior_low = min(c["low"] for c in h4[-10:-1])
        bos = last["close"] < prior_low and vol_ratio >= 0.90
        wick_ok = upper_wick >= max(body * 1.5, rng * 0.40) and last["close"] < last["open"] and vol_ratio >= 0.90
        if level_price and last["high"] >= level_price >= last["close"] and wick_ok:
            return {"confirmed": True, "type": "REJECTION_CANDLE", "detail": f"4H bearish rejection @ {level_price:,.1f} (vol {vol_ratio:.2f}x)"}
        if bos:
            return {"confirmed": True, "type": "STRUCTURE_BREAK", "detail": f"4H BOS close {last['close']:,.1f} < {prior_low:,.1f} (vol {vol_ratio:.2f}x)"}
        if wick_ok:
            return {"confirmed": True, "type": "REJECTION_CANDLE", "detail": f"4H bearish shooting-star wick (vol {vol_ratio:.2f}x)"}
        return {"confirmed": False, "type": None, "reason": f"No 4H SHORT BOS/rejection+vol (vol {vol_ratio:.2f}x)"}

    def _close_fraction(
        self, pos: Dict[str, Any], fraction: float, exit_price: float, reason: str, now: datetime
    ) -> float:
        close_btc = round(pos["size_btc"] * fraction, 6)
        if close_btc <= 0:
            return 0.0
        sign = 1.0 if pos["direction"] == "LONG" else -1.0
        pnl_usd = sign * (exit_price - pos["entry_price"]) * close_btc
        pnl_r = sign * (exit_price - pos["entry_price"]) / max(pos["initial_stop_dist"], 1e-9)
        self._ledger["realized_equity"] = round(self._ledger["realized_equity"] + pnl_usd, 2)
        pos["size_btc"] = round(pos["size_btc"] - close_btc, 6)
        pos["risk_pct"] = round(pos["risk_pct"] * max(0.0, 1.0 - fraction), 4)
        opened_ms = float(pos.get("opened_at_ms", now.timestamp() * 1000.0))
        hold_h = max(0.0, (now.timestamp() * 1000.0 - opened_ms) / 3_600_000.0)
        self._ledger["closed_trades"].append(
            {
                "trade_id": pos["id"],
                "direction": pos["direction"],
                "entry_price": pos["entry_price"],
                "exit_price": round(exit_price, 2),
                "size_btc": close_btc,
                "pnl_usd": round(pnl_usd, 2),
                "r_multiple": round(pnl_r, 3),
                "reason": reason,
                "hold_hours": round(hold_h, 2),
                "closed_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
        )
        self._append_audit(
            now,
            f"CLOSE_{pos['direction']}",
            f"{reason} @ ${exit_price:,.1f} ({close_btc:.4f} BTC, {pnl_r:+.2f}R, ${pnl_usd:+,.2f})",
        )
        return pnl_usd

    def _manage_positions_and_breakers(
        self, price: float, score: float, h4: List[Dict[str, float]], now: datetime
    ) -> None:
        cfg = self.config
        day_key = now.strftime("%Y-%m-%d")
        iso = now.isocalendar()
        wk_key = f"{iso.year}-W{iso.week:02d}"
        b = self._ledger["breakers"]

        if self._ledger.get("day_key") != day_key:
            self._ledger["day_key"] = day_key
            self._ledger["day_start_equity"] = self._ledger["equity"]
            self._ledger["intraday_peak_equity"] = self._ledger["equity"]
            b["intraday_halted"] = False
            b["daily_halted"] = False
        if self._ledger.get("week_key") != wk_key:
            self._ledger["week_key"] = wk_key
            self._ledger["week_start_equity"] = self._ledger["equity"]
            b["weekly_halted"] = False

        ema20 = _ema_series([c["close"] for c in h4], 20)
        trail_ema = ema20[-1] if ema20 else None
        long_th = cfg.futures_v4_dd_tier1_long if b["dd_tier1_active"] else cfg.futures_v4_long_threshold
        short_th = cfg.futures_v4_dd_tier1_short if b["dd_tier1_active"] else cfg.futures_v4_short_threshold
        is_weekend = now.weekday() >= 5

        for pos in list(self._ledger["open_positions"]):
            sign = 1.0 if pos["direction"] == "LONG" else -1.0
            dist = max(pos["initial_stop_dist"], 1e-9)
            cur_r = sign * (price - pos["entry_price"]) / dist
            pos["current_r"] = round(cur_r, 3)
            pos["max_favorable_r"] = round(max(float(pos.get("max_favorable_r", 0.0)), cur_r), 3)
            hours_open = max(0.0, (now.timestamp() * 1000.0 - float(pos.get("opened_at_ms", 0.0))) / 3_600_000.0)
            pos["hold_hours"] = round(hours_open, 2)

            if (price <= pos["stop_price"]) if pos["direction"] == "LONG" else (price >= pos["stop_price"]):
                self._close_fraction(pos, 1.0, pos["stop_price"], "HARD_OR_TRAIL_STOP", now)
                continue
            if hours_open >= cfg.futures_v4_max_hold_hours:
                self._close_fraction(pos, 1.0, price, "MAX_HOLD_24H_EXIT", now)
                continue
            if is_weekend:
                ext_ok = (pos["direction"] == "LONG" and score >= cfg.futures_v4_weekend_long) or (
                    pos["direction"] == "SHORT" and score <= cfg.futures_v4_weekend_short
                )
                if not ext_ok:
                    self._close_fraction(pos, 1.0, price, "WEEKEND_NON_EXTREME_EXIT", now)
                    continue
                if not pos.get("weekend_halved"):
                    self._close_fraction(pos, 0.50, price, "WEEKEND_EXTREME_HALF_REDUCE", now)
                    pos["weekend_halved"] = True

            opened_day = pos.get("opened_utc_day")
            if opened_day and day_key > opened_day and pos.get("daily_close_checked_day") != day_key:
                pos["daily_close_checked_day"] = day_key
                entry_sc = float(pos.get("entry_regime_score", score))
                improved = (score > entry_sc) if pos["direction"] == "LONG" else (score < entry_sc)
                if not improved:
                    self._close_fraction(pos, 0.50, price, "DAILY_CLOSE_NO_IMPROVEMENT_REDUCE", now)
                    if pos["size_btc"] <= 1e-6:
                        continue

            if (pos["direction"] == "LONG" and score <= short_th) or (pos["direction"] == "SHORT" and score >= long_th):
                self._close_fraction(pos, 1.0, price, "REGIME_OPPOSING_EXIT", now)
                continue

            best_r = float(pos.get("max_favorable_r", cur_r))
            if hours_open >= cfg.futures_v4_time_exit_hours and best_r < 1.0:
                self._close_fraction(pos, 1.0, price, "TIME_STOP_12H_EXIT", now)
                continue
            if hours_open >= cfg.futures_v4_time_reduce_hours and best_r < 1.0 and not pos.get("time_stop_8h_reduced"):
                self._close_fraction(pos, 0.50, price, "TIME_STOP_8H_REDUCE", now)
                pos["time_stop_8h_reduced"] = True

            if cur_r >= cfg.futures_v4_be_r and not pos.get("breakeven_moved"):
                pos["stop_price"] = pos["entry_price"]
                pos["breakeven_moved"] = True
                self._append_audit(now, "STOP_TO_BE", f"{pos['direction']} +1.0R -> BE ${pos['entry_price']:,.1f}")

            if pos.get("breakeven_moved") and trail_ema:
                if pos["direction"] == "LONG" and pos["stop_price"] < trail_ema < price:
                    pos["stop_price"] = round(trail_ema, 1)
                elif pos["direction"] == "SHORT" and price < trail_ema < pos["stop_price"]:
                    pos["stop_price"] = round(trail_ema, 1)

            if cur_r >= cfg.futures_v4_partial_r and not pos.get("partial_taken"):
                self._close_fraction(pos, cfg.futures_v4_partial_pct, price, "PARTIAL_TP_1.5R", now)
                pos["partial_taken"] = True

        self._ledger["open_positions"] = [p for p in self._ledger["open_positions"] if p["size_btc"] > 1e-6]

        unreal = 0.0
        for p in self._ledger["open_positions"]:
            sign = 1.0 if p["direction"] == "LONG" else -1.0
            u = sign * (price - p["entry_price"]) * p["size_btc"]
            p["unrealized_pnl_usd"] = round(u, 2)
            unreal += u

        eq = round(self._ledger["realized_equity"] + unreal, 2)
        self._ledger["equity"] = eq
        if eq > self._ledger["high_water_mark"]:
            self._ledger["high_water_mark"] = eq
        if eq > self._ledger.get("intraday_peak_equity", eq):
            self._ledger["intraday_peak_equity"] = eq

        dd = (eq - self._ledger["high_water_mark"]) / max(self._ledger["high_water_mark"], 1.0)
        self._ledger["drawdown_pct"] = round(dd * 100.0, 3)

        intra_pk = max(self._ledger.get("intraday_peak_equity", eq), 1.0)
        intra_pnl = (eq - intra_pk) / intra_pk
        day_pnl = (eq - max(self._ledger["day_start_equity"], 1.0)) / max(self._ledger["day_start_equity"], 1.0)
        wk_pnl = (eq - max(self._ledger["week_start_equity"], 1.0)) / max(self._ledger["week_start_equity"], 1.0)

        if intra_pnl <= cfg.futures_v4_intraday_loss_pct and not b["intraday_halted"]:
            b["intraday_halted"] = True
            self._append_audit(now, "BREAKER_INTRADAY", f"Intraday {intra_pnl*100:.2f}% <= {cfg.futures_v4_intraday_loss_pct*100:.1f}%")
        if day_pnl <= cfg.futures_v4_daily_loss_pct and not b["daily_halted"]:
            b["daily_halted"] = True
            self._append_audit(now, "BREAKER_DAILY", f"Daily {day_pnl*100:.2f}% <= {cfg.futures_v4_daily_loss_pct*100:.1f}%")
        if wk_pnl <= cfg.futures_v4_weekly_loss_pct and not b["weekly_halted"]:
            b["weekly_halted"] = True
            for p in list(self._ledger["open_positions"]):
                self._close_fraction(p, 1.0, price, "WEEKLY_LOSS_FLATTEN", now)
            self._ledger["open_positions"] = []
            self._append_audit(now, "BREAKER_WEEKLY", f"Weekly {wk_pnl*100:.2f}% -> flattened futures")
        if dd <= cfg.futures_v4_dd_tier2_pct and not b["dd_tier2_locked"]:
            b["dd_tier2_locked"] = True
            b["dd_tier1_active"] = True
            for p in list(self._ledger["open_positions"]):
                self._close_fraction(p, 1.0, price, "DD_TIER2_FLATTEN", now)
            self._ledger["open_positions"] = []
            self._append_audit(now, "BREAKER_DD_10", f"Drawdown {dd*100:.2f}% -> locked pending manual review")
        elif dd <= cfg.futures_v4_dd_tier1_pct:
            if not b["dd_tier1_active"]:
                b["dd_tier1_active"] = True
                self._append_audit(now, "BREAKER_DD_6", f"Drawdown {dd*100:.2f}% -> 0.2% risk & 75/25 thresholds")
        elif not b["dd_tier2_locked"] and dd > cfg.futures_v4_dd_tier1_pct * 0.5:
            b["dd_tier1_active"] = False

    def evaluate(
        self,
        store: StateStore,
        now_utc: Optional[datetime] = None,
        macro_minutes_away: Optional[float] = None,
    ) -> FuturesV4Evaluation:
        """Compute Version 4.0 Regime + 9-Point Futures Checklist + Sell Inventory + Paper Ledger."""
        now = now_utc or datetime.now(timezone.utc)
        cfg = self.config

        h4_klines = list(store.spot_klines_4h)
        if len(h4_klines) < 30 and len(store.spot_klines_1h) >= 120:
            h4_klines = synthesize_4h_bars(list(store.spot_klines_1h))
        h4 = self._to_bars(h4_klines)

        d1_klines = list(store.spot_klines_1d)
        d1 = self._to_bars(d1_klines) if len(d1_klines) >= 30 else _synthesize_daily_bars(h4)

        price = float(
            store.binance_perp_price
            or store.binance_spot_price
            or store.coinbase_spot_price
            or (h4[-1]["close"] if h4 else 0.0)
        )

        ev = FuturesV4Evaluation(
            long_threshold=cfg.futures_v4_long_threshold,
            short_threshold=cfg.futures_v4_short_threshold,
            is_weekend_utc=now.weekday() >= 5,
            max_heat_pct=round(cfg.futures_v4_max_heat_pct * 100.0, 2),
            evaluated_utc=now.strftime("%Y-%m-%d %H:%M:%S UTC"),
        )

        if len(h4) < 30 or len(d1) < 15 or price <= 0:
            ev.rejection_reasons = [f"Warming up 4H/1D OHLCV buffers (4H={len(h4)}/30, 1D={len(d1)}/15)"]
            ev.breakers = dict(self._ledger["breakers"])
            store.futures_v4_evaluation = ev
            return ev

        # 1. Trend Structure (30%)
        h4_closes = [c["close"] for c in h4]
        d_closes = [c["close"] for c in d1]
        h4_struct = _analyze_structure(h4[-120:], left=3, right=3)
        d_struct = _analyze_structure(d1[-90:], left=3, right=3)
        e20_4h = _ema_series(h4_closes, 20)
        e50_4h = _ema_series(h4_closes, 50)
        e50_d = _ema_series(d_closes, 50)
        e200_d = _ema_series(d_closes, 200)

        h4_ema_sc = 50.0
        if e20_4h and e50_4h:
            p4 = 50.0 + (18.0 if price > e20_4h[-1] else -18.0) + (16.0 if price > e50_4h[-1] else -16.0) + (16.0 if e20_4h[-1] > e50_4h[-1] else -16.0)
            h4_ema_sc = _clamp(p4)
        d_ema_sc = 50.0
        if e50_d and e200_d:
            pd = 50.0 + (18.0 if price > e50_d[-1] else -18.0) + (16.0 if price > e200_d[-1] else -16.0) + (16.0 if e50_d[-1] > e200_d[-1] else -16.0)
            d_ema_sc = _clamp(pd)
        elif e50_d:
            d_ema_sc = 72.0 if price > e50_d[-1] else 28.0

        daily_bias_sc = 0.50 * d_struct["score"] + 0.50 * d_ema_sc
        daily_bias = "BULL" if daily_bias_sc >= 58.0 else ("BEAR" if daily_bias_sc <= 42.0 else "NEUTRAL")
        s_trend = round(0.40 * h4_struct["score"] + 0.25 * h4_ema_sc + 0.35 * daily_bias_sc, 2)

        # 2. Momentum 4H (25%)
        rsi4 = _rsi(h4_closes, 14)
        rsid = _rsi(d_closes, 14)
        osc_sc = 0.70 * _score_rsi_4h(rsi4) + 0.30 * _score_rsi_4h(rsid)
        roc_parts = [
            _map_linear(r, -lim, lim)
            for p, lim in ((6, 4.5), (12, 6.5), (20, 9.0))
            if (r := _roc(h4_closes, p)) is not None
        ]
        roc_sc = sum(roc_parts) / len(roc_parts) if roc_parts else 50.0
        s_mom = round(0.45 * osc_sc + 0.55 * roc_sc, 2)

        # 3. Volatility & Liquidity 4H (25%)
        atrs_4h = _atr_series(h4, 14)
        atr_4h = atrs_4h[-1] if atrs_4h else (price * 0.012)
        atr_pct = atr_4h / price * 100.0
        atr_pct_hist = [a / max(c["close"], 1.0) * 100.0 for c, a in zip(h4[-len(atrs_4h):], atrs_4h)] if atrs_4h else []
        atr_pctile = _percentile_rank(atr_pct, atr_pct_hist[-120:]) if atr_pct_hist else None
        if atr_pctile is None:
            atr_q = 50.0
        elif 20.0 <= atr_pctile <= 65.0:
            atr_q = 78.0
        elif atr_pctile < 20.0:
            atr_q = _map_linear(atr_pctile, 0.0, 20.0, 35.0, 74.0)
        elif atr_pctile <= 85.0:
            atr_q = _map_linear(atr_pctile, 65.0, 85.0, 78.0, 48.0)
        else:
            atr_q = _map_linear(atr_pctile, 85.0, 100.0, 48.0, 15.0)

        vols = [c["volume"] for c in h4]
        vol_sma = statistics.mean(vols[-21:-1]) if len(vols) >= 21 else (statistics.mean(vols) if vols else 1.0)
        vol_ratio = vols[-1] / max(vol_sma, 1e-9)
        if 0.85 <= vol_ratio <= 2.0:
            vol_q = _map_linear(vol_ratio, 0.85, 2.0, 58.0, 84.0)
        elif vol_ratio < 0.85:
            vol_q = _map_linear(vol_ratio, 0.30, 0.85, 22.0, 58.0)
        else:
            vol_q = _map_linear(vol_ratio, 2.0, 4.0, 76.0, 36.0)

        fund = getattr(store, "funding_rate_pct", None)
        fund_q = 68.0 if (fund is not None and -0.005 <= fund <= 0.015) else (55.0 if fund is None else 35.0)
        vol_quality = 0.45 * atr_q + 0.35 * vol_q + 0.20 * fund_q

        # 4. Session / Context (20%)
        hr = now.hour + now.minute / 60.0
        is_wk = now.weekday() >= 5
        if is_wk:
            sess_name, sess_q = "WEEKEND", 38.0
        elif 13.0 <= hr < 17.0:
            sess_name, sess_q = "LONDON_NY_OVERLAP", 82.0
        elif 8.0 <= hr < 13.0 or 17.0 <= hr < 21.0:
            sess_name, sess_q = "LONDON_OR_NY", 72.0
        else:
            sess_name, sess_q = "ASIA_OFFHOURS", 58.0

        ev_min = macro_minutes_away
        if ev_min is None and getattr(store, "macro_evaluation", None) is not None:
            ev_min = getattr(store.macro_evaluation, "next_event_minutes", None)
        event_q = 15.0 if (ev_min is not None and 0.0 <= ev_min <= cfg.futures_v4_macro_blackout_min) else (
            45.0 if (ev_min is not None and ev_min <= 180.0) else 72.0
        )
        sess_quality = 0.55 * sess_q + 0.45 * event_q

        dir_core = (0.30 * s_trend + 0.25 * s_mom) / 0.55
        lean = max(-1.0, min(1.0, (dir_core - 50.0) / 14.0))
        s_vol = round(50.0 + lean * (vol_quality - 50.0), 2)
        s_sess = round(50.0 + lean * (sess_quality - 50.0), 2)

        score = round(0.30 * s_trend + 0.25 * s_mom + 0.25 * s_vol + 0.20 * s_sess, 2)

        # Manage ledger & breakers first (uses updated score)
        self._manage_positions_and_breakers(price, score, h4, now)
        b = self._ledger["breakers"]
        dd_tier1 = bool(b["dd_tier1_active"])
        long_th = cfg.futures_v4_dd_tier1_long if dd_tier1 else cfg.futures_v4_long_threshold
        short_th = cfg.futures_v4_dd_tier1_short if dd_tier1 else cfg.futures_v4_short_threshold
        bias = "LONG" if score >= long_th else ("SHORT" if score <= short_th else "FLAT")

        # 9-Point Futures Checklist
        levels = self._identify_levels(d1, h4)
        prox_limit = min(atr_4h * 0.75, price * 0.01)
        nearest_level = min(levels, key=lambda l: abs(l["price"] - price)) if levels else None
        lvl_dist = abs(nearest_level["price"] - price) if nearest_level else float("inf")

        candidate_dir = bias if bias in ("LONG", "SHORT") else None
        eval_dir = candidate_dir or ("LONG" if score >= 50.0 else "SHORT")
        checklist: List[FuturesV4ChecklistItem] = []
        rejections: List[str] = []

        # Rule 1
        if candidate_dir is None:
            r1_ok, r1_det = False, f"Score {score:.1f} in Flat Zone ({short_th:.0f}-{long_th:.0f}); no exceptions"
        elif is_wk and ((candidate_dir == "LONG" and score < cfg.futures_v4_weekend_long) or (candidate_dir == "SHORT" and score > cfg.futures_v4_weekend_short)):
            r1_ok, r1_det = False, f"Weekend UTC requires extreme ≥{cfg.futures_v4_weekend_long:.0f}/≤{cfg.futures_v4_weekend_short:.0f} (now {score:.1f})"
        else:
            r1_ok, r1_det = True, f"Score {score:.1f} qualifies {candidate_dir}" + (" (Weekend 0.5x)" if is_wk else "")
        checklist.append(FuturesV4ChecklistItem(1, "Regime Score Threshold", r1_ok, r1_det))
        if not r1_ok:
            rejections.append(r1_det)

        # Rule 2
        daily_ok = (eval_dir == "LONG" and daily_bias != "BEAR") or (eval_dir == "SHORT" and daily_bias != "BULL")
        lvl_ok = nearest_level is not None and lvl_dist <= prox_limit
        r2_ok = daily_ok and lvl_ok
        r2_det = (
            f"Opposes Daily Bias ({daily_bias})"
            if not daily_ok
            else (
                f"At {nearest_level['label']} (${nearest_level['price']:,.1f}) w/ Daily {daily_bias}"
                if lvl_ok
                else f"Nearest 4H level ${nearest_level['price']:,.1f} is ${lvl_dist:,.0f} away (> ±${prox_limit:,.0f})"
            )
        )
        checklist.append(FuturesV4ChecklistItem(2, "4H Level Aligned Daily Bias", r2_ok, r2_det))
        if not r2_ok:
            rejections.append(r2_det)

        # Rule 3
        conf = self._detect_confirmation(h4, eval_dir, nearest_level["price"] if nearest_level else None)
        r3_ok = bool(conf["confirmed"]) and r1_ok
        r3_det = str(conf.get("detail") if conf["confirmed"] else conf.get("reason", "No 4H BOS/rejection"))
        checklist.append(FuturesV4ChecklistItem(3, "4H Confirmation + Volume", r3_ok, r3_det))
        if not r3_ok:
            rejections.append(r3_det)

        # Stop, Target, R:R (Rules 4 & 5)
        h4_hi, h4_lo = _swing_pivots(h4[-80:], left=2, right=2)
        entry_price = round(nearest_level["price"], 1) if (nearest_level and conf.get("type") == "REJECTION_CANDLE") else round(price, 1)
        entry_method = "LIMIT_AT_LEVEL" if conf.get("type") != "STRUCTURE_BREAK" else "MARKET_AFTER_BOS"

        if eval_dir == "LONG":
            sw_cands = [s["price"] * 0.9985 for s in h4_lo if s["price"] < entry_price]
            atr_stop = entry_price - atr_4h
            stop_price = round(max(max(sw_cands) if sw_cands else atr_stop, atr_stop), 1)
            if stop_price >= entry_price * 0.997:
                stop_price = round(atr_stop, 1)
            targets = sorted([l for l in levels if l["price"] > entry_price * 1.004], key=lambda x: x["price"])
            target1 = targets[0]["price"] if targets else round(entry_price + 2.0 * abs(entry_price - stop_price), 1)
            target1_label = targets[0]["label"] if targets else "Projected 2.0R"
        else:
            sw_cands = [s["price"] * 1.0015 for s in h4_hi if s["price"] > entry_price]
            atr_stop = entry_price + atr_4h
            stop_price = round(min(min(sw_cands) if sw_cands else atr_stop, atr_stop), 1)
            if stop_price <= entry_price * 1.003:
                stop_price = round(atr_stop, 1)
            targets = sorted([l for l in levels if l["price"] < entry_price * 0.996], key=lambda x: x["price"], reverse=True)
            target1 = targets[0]["price"] if targets else round(entry_price - 2.0 * abs(stop_price - entry_price), 1)
            target1_label = targets[0]["label"] if targets else "Projected 2.0R"

        stop_dist = abs(entry_price - stop_price)
        stop_dist_pct = stop_dist / max(entry_price, 1.0)
        raw_rr = round(abs(target1 - entry_price) / max(stop_dist, 1e-9), 2)
        f8h = float(fund or 0.0)
        f_drag = max(0.0, ((f8h / 100.0) * 3.0) if eval_dir == "LONG" else (-(f8h / 100.0) * 3.0))
        adj_rr = round(max(0.0, (abs(target1 - entry_price) / max(entry_price, 1.0)) - f_drag) / max(stop_dist_pct, 1e-9), 2)

        r4_ok = raw_rr >= cfg.futures_v4_min_rr and adj_rr >= cfg.futures_v4_min_rr
        r4_det = f"R:R {raw_rr:.2f}:1 (adj {adj_rr:.2f}:1) vs {cfg.futures_v4_min_rr:.1f}:1 min"
        checklist.append(FuturesV4ChecklistItem(4, f"Risk-Reward ≥ {cfg.futures_v4_min_rr:.1f}:1", r4_ok, r4_det))
        if not r4_ok:
            rejections.append(r4_det)

        r5_ok = stop_dist_pct <= cfg.futures_v4_max_stop_pct
        r5_det = f"Stop {stop_dist_pct*100:.2f}% vs {cfg.futures_v4_max_stop_pct*100:.1f}% max"
        checklist.append(FuturesV4ChecklistItem(5, f"Stop Distance ≤ {cfg.futures_v4_max_stop_pct*100:.1f}%", r5_ok, r5_det))
        if not r5_ok:
            rejections.append(r5_det)

        open_pos = self._ledger["open_positions"]
        r6_ok = len(open_pos) < cfg.futures_v4_max_concurrent
        r6_det = "No open/opposing futures" if r6_ok else f"Open {open_pos[0]['direction']} futures active (max 1)"
        checklist.append(FuturesV4ChecklistItem(6, "No Opposing / Max 1 Futures", r6_ok, r6_det))
        if not r6_ok:
            rejections.append(r6_det)

        equity = float(self._ledger["equity"])
        risk_pct = cfg.futures_v4_dd_tier1_risk_pct if dd_tier1 else cfg.futures_v4_risk_per_trade_pct
        if is_wk:
            risk_pct *= cfg.futures_v4_weekend_size_mult
        raw_btc = (equity * risk_pct) / max(stop_dist, 1e-9)
        max_btc = (equity * cfg.futures_v4_max_leverage) / max(entry_price, 1.0)
        lev_capped = raw_btc > max_btc
        size_btc = round(min(raw_btc, max_btc), 6)
        notional = round(size_btc * entry_price, 2)
        leverage = round(notional / max(equity, 1.0), 3)
        act_risk_usd = round(size_btc * stop_dist, 2)
        act_risk_pct = round(act_risk_usd / max(equity, 1.0) * 100.0, 4)

        cur_heat = sum(float(p.get("risk_pct", 0.0)) for p in open_pos)
        max_heat = cfg.futures_v4_max_heat_pct * 100.0
        r7_ok = size_btc > 0 and (cur_heat + act_risk_pct) <= max_heat + 1e-9
        r7_det = f"Post-trade heat {cur_heat + act_risk_pct:.2f}% ≤ {max_heat:.2f}%"
        checklist.append(FuturesV4ChecklistItem(7, f"Portfolio Heat ≤ {max_heat:.1f}%", r7_ok, r7_det))
        if not r7_ok:
            rejections.append(r7_det)

        active_cbs = [k for k in ("intraday_halted", "daily_halted", "weekly_halted", "dd_tier2_locked") if b.get(k)]
        r8_ok = len(active_cbs) == 0
        r8_det = "All 5 circuit breakers clear" if r8_ok else f"Active: {', '.join(active_cbs)}"
        checklist.append(FuturesV4ChecklistItem(8, "No Circuit Breaker Active", r8_ok, r8_det))
        if not r8_ok:
            rejections.append(r8_det)

        macro_blk = ev_min is not None and 0.0 <= ev_min <= cfg.futures_v4_macro_blackout_min
        r9_ok = not macro_blk
        r9_det = f"Blocked: macro release in {ev_min:.0f}m" if macro_blk else f"No major release ≤ {int(cfg.futures_v4_macro_blackout_min)}m"
        checklist.append(FuturesV4ChecklistItem(9, f"No Release ≤ {int(cfg.futures_v4_macro_blackout_min)}m", r9_ok, r9_det))
        if not r9_ok:
            rejections.append(r9_det)

        futures_status = candidate_dir if (candidate_dir and all(c.passed for c in checklist)) else "FLAT"

        # Sell Inventory (score <= short_th & 4H ref, exempt from checks 3-9 & futures halts)
        inv_active = (score <= short_th) and (nearest_level is not None)
        inv_pct = cfg.futures_v4_sell_inv_default_pct
        spot_inv = float(self._ledger.get("spot_inventory_btc", cfg.futures_v4_spot_inventory_btc))
        sell_btc = round(spot_inv * inv_pct, 6) if inv_active else 0.0
        sell_usd = round(sell_btc * price, 2) if inv_active else 0.0
        sell_ref = f"{nearest_level['label']} @ ${nearest_level['price']:,.1f}" if nearest_level else "—"
        sell_reason = (
            f"Score {score:.1f} ≤ {short_th:.0f} w/ {sell_ref} — trim {inv_pct*100:.0f}% spot ({sell_btc:.4f} BTC)"
            if inv_active
            else f"Hold spot (requires score ≤ {short_th:.0f}; now {score:.1f})"
        )

        # Auto paper entry / audit once per 4H bar
        last_4h_ts = h4[-1]["ts"]
        if futures_status in ("LONG", "SHORT") and size_btc > 0:
            self._ledger["open_positions"].append(
                {
                    "id": f"V4-{now.strftime('%Y%m%d%H%M')}-{uuid.uuid4().hex[:4].upper()}",
                    "direction": futures_status,
                    "entry_price": entry_price,
                    "stop_price": stop_price,
                    "initial_stop_dist": stop_dist,
                    "target1_price": target1,
                    "size_btc": size_btc,
                    "notional_usd": notional,
                    "leverage": leverage,
                    "risk_pct": act_risk_pct,
                    "opened_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "opened_at_ms": int(now.timestamp() * 1000),
                    "opened_utc_day": now.strftime("%Y-%m-%d"),
                    "entry_regime_score": score,
                    "weekend_halved": is_wk,
                    "breakeven_moved": False,
                    "partial_taken": False,
                    "time_stop_8h_reduced": False,
                    "current_r": 0.0,
                    "max_favorable_r": 0.0,
                    "hold_hours": 0.0,
                    "unrealized_pnl_usd": 0.0,
                }
            )
            self._append_audit(
                now,
                f"OPEN_{futures_status}",
                f"{size_btc:.4f} BTC @ ${entry_price:,.1f} | Stop ${stop_price:,.1f} ({stop_dist_pct*100:.2f}%) | TP ${target1:,.1f} ({leverage:.2f}x)",
            )
        if inv_active and self._ledger.get("last_sell_inventory_4h_ts") != last_4h_ts:
            self._ledger["last_sell_inventory_4h_ts"] = last_4h_ts
            self._append_audit(now, "SELL_INVENTORY_SIGNAL", f"Reduce {inv_pct*100:.0f}% spot ({sell_btc:.4f} BTC ≈ ${sell_usd:,.0f}) @ {sell_ref}")

        self._save_ledger()

        active_sigs: List[str] = []
        if futures_status in ("LONG", "SHORT"):
            active_sigs.append(futures_status)
        if inv_active:
            active_sigs.append("SELL_INVENTORY")
        if not active_sigs:
            active_sigs.append("FLAT")

        closed = self._ledger["closed_trades"]
        wins = [t for t in closed if t["pnl_usd"] > 0]
        losses = [t for t in closed if t["pnl_usd"] < 0]
        gw = sum(t["pnl_usd"] for t in wins)
        gl = abs(sum(t["pnl_usd"] for t in losses))
        intra_pk = max(self._ledger.get("intraday_peak_equity", equity), 1.0)
        ds = max(self._ledger["day_start_equity"], 1.0)
        ws = max(self._ledger["week_start_equity"], 1.0)

        ev.regime_score = score
        ev.regime_bias = bias
        ev.daily_bias = daily_bias
        ev.futures_status = futures_status
        ev.active_signals = active_sigs
        ev.long_threshold = long_th
        ev.short_threshold = short_th
        ev.last_4h_close_utc = datetime.fromtimestamp(last_4h_ts / 1000.0, tz=timezone.utc).strftime("%Y-%m-%d %H:%MZ")
        ev.factor_scores = {
            "trend_structure": s_trend,
            "momentum": s_mom,
            "volatility_liquidity": s_vol,
            "session_context": s_sess,
        }
        ev.factor_summaries = {
            "trend_structure": f"4H={h4_struct['state']}, 1D={daily_bias}",
            "momentum": f"RSI4H={rsi4}, ROC={_roc(h4_closes, 6):.2f}%" if _roc(h4_closes, 6) is not None else f"RSI4H={rsi4}",
            "volatility_liquidity": f"ATRp={atr_pctile}, RelV={vol_ratio:.2f}x",
            "session_context": f"{sess_name}",
        }
        contribs = sorted(
            [
                ("Trend Structure", 0.30, s_trend),
                ("Momentum 4H", 0.25, s_mom),
                ("Vol & Liquidity 4H", 0.25, s_vol),
                ("Session / Context", 0.20, s_sess),
            ],
            key=lambda x: abs(x[1] * (x[2] - 50.0)),
            reverse=True,
        )
        ev.dominant_factors = [f"{lbl} ({sc:.1f})" for lbl, _, sc in contribs[:2]]
        ev.checklist = checklist
        ev.rejection_reasons = [] if futures_status != "FLAT" else rejections
        ev.eval_direction = eval_dir
        ev.entry_method = entry_method
        ev.entry_price = entry_price
        ev.stop_price = stop_price
        ev.target1_price = target1
        ev.target1_label = target1_label
        ev.stop_distance_pct = round(stop_dist_pct * 100.0, 2)
        ev.raw_rr = raw_rr
        ev.funding_adj_rr = adj_rr
        ev.size_btc = size_btc
        ev.notional_usd = notional
        ev.leverage = leverage
        ev.leverage_capped = lev_capped
        ev.actual_risk_pct = act_risk_pct
        ev.actual_risk_usd = act_risk_usd
        ev.weekend_halved = is_wk
        ev.sell_inventory_active = inv_active
        ev.sell_inventory_pct = round(inv_pct * 100.0, 1)
        ev.sell_inventory_btc = sell_btc
        ev.sell_inventory_usd = sell_usd
        ev.sell_inventory_ref = sell_ref
        ev.sell_inventory_reason = sell_reason
        ev.equity_usd = equity
        ev.realized_equity_usd = float(self._ledger["realized_equity"])
        ev.drawdown_pct = float(self._ledger["drawdown_pct"])
        ev.intraday_pnl_pct = round((equity - intra_pk) / intra_pk * 100.0, 2)
        ev.daily_pnl_pct = round((equity - ds) / ds * 100.0, 2)
        ev.weekly_pnl_pct = round((equity - ws) / ws * 100.0, 2)
        ev.open_heat_pct = round(sum(float(p.get("risk_pct", 0.0)) for p in self._ledger["open_positions"]), 2)
        ev.breakers = dict(b)
        ev.open_positions = list(self._ledger["open_positions"])
        ev.closed_trades = list(closed[-10:])
        ev.audit_log = list(reversed(self._ledger["audit_log"][-10:]))
        ev.total_closed_legs = len(closed)
        ev.review_win_rate_pct = round(len(wins) / len(closed) * 100.0, 1) if closed else 0.0
        ev.review_profit_factor = round(gw / gl, 2) if gl > 0 else (99.0 if gw > 0 else 0.0)
        ev.review_expectancy_r = round(sum(t["r_multiple"] for t in closed) / len(closed), 2) if closed else 0.0

        store.futures_v4_evaluation = ev
        return ev
