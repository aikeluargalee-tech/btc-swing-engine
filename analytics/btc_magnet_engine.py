import json
import logging
import time
import urllib.request
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from config.settings import EngineConfig, RISK_BUDGET_MAX_PCT
from core.models import BTCMagnetEvaluation, BTCMagnetLevel, BTCMagnetRuleCheck
from analytics.reconciliation_engine import ReconciliationEngine
from core.state_store import StateStore

logger = logging.getLogger(__name__)


def _compute_ema(closes: List[float], period: int) -> Optional[float]:
    """Computes an exponential moving average when at least `period` closes exist."""
    if len(closes) < period or period <= 0:
        return None
    sma = sum(closes[:period]) / float(period)
    k = 2.0 / (period + 1.0)
    ema = sma
    for price in closes[period:]:
        ema = (price - ema) * k + ema
    return round(ema, 2)


def _compute_sma(closes: List[float], period: int) -> Optional[float]:
    """Computes a simple moving average when at least `period` closes exist."""
    if len(closes) < period or period <= 0:
        return None
    return round(sum(closes[-period:]) / float(period), 2)


def _compute_vwap(bars: List[Any]) -> Optional[float]:
    """Computes volume-weighted typical price across the supplied bars."""
    if not bars:
        return None
    total_pv = 0.0
    total_v = 0.0
    for b in bars:
        vol = float(getattr(b, "volume", 0.0) or 0.0)
        if vol <= 0.0:
            continue
        hi = float(getattr(b, "high", 0.0) or 0.0)
        lo = float(getattr(b, "low", 0.0) or 0.0)
        cl = float(getattr(b, "close", 0.0) or 0.0)
        tp = (hi + lo + cl) / 3.0 if (hi > 0.0 and lo > 0.0 and cl > 0.0) else cl
        total_pv += tp * vol
        total_v += vol
    if total_v <= 0.0:
        return None
    return round(total_pv / total_v, 2)


def _compute_atr_and_compression(bars_1h: List[Any]) -> Tuple[Optional[float], Optional[float]]:
    """Computes 14-period 1H ATR and 72h ATR compression % when sufficient bars exist."""
    if len(bars_1h) < 15:
        return None, None
    trs: List[float] = []
    for idx in range(1, len(bars_1h)):
        cur = bars_1h[idx]
        prev_c = float(getattr(bars_1h[idx - 1], "close", 0.0) or 0.0)
        hi = float(getattr(cur, "high", 0.0) or 0.0)
        lo = float(getattr(cur, "low", 0.0) or 0.0)
        tr = max(hi - lo, abs(hi - prev_c), abs(lo - prev_c))
        trs.append(max(0.0, tr))
    if len(trs) < 14:
        return None, None
    atr_series = [sum(trs[i - 14:i]) / 14.0 for i in range(14, len(trs) + 1)]
    cur_atr = atr_series[-1]
    if len(bars_1h) < 72 or len(atr_series) < 2:
        return round(cur_atr, 2), None
    peak_atr = max(atr_series[-58:])
    if peak_atr <= 0.0:
        return round(cur_atr, 2), None
    comp = max(0.0, ((peak_atr - cur_atr) / peak_atr) * 100.0)
    return round(cur_atr, 2), round(comp, 1)


def compute_spot_cvd_slopes(bars_1d: Any) -> Tuple[Optional[float], Optional[float]]:
    """Computes 7D and 14D cumulative spot taker-delta slopes (BTC) from closed 1D bars."""
    bars = list(bars_1d or [])
    if not bars:
        return None, None
    now_ms = int(time.time() * 1000)
    last_ts = int(getattr(bars[-1], "timestamp_ms", 0) or 0)
    closed = bars[:-1] if (len(bars) > 1 and last_ts > 0 and (last_ts + 86_400_000) > now_ms) else bars

    def _bar_delta(b: Any) -> float:
        vol = float(getattr(b, "volume", 0.0) or 0.0)
        tb = getattr(b, "taker_buy_volume", None)
        if tb is not None and float(tb) > 0.0:
            return 2.0 * float(tb) - vol
        return float(getattr(b, "delta", 0.0) or 0.0)

    deltas = [_bar_delta(b) for b in closed]
    s7 = round(sum(deltas[-7:]), 2) if len(deltas) >= 7 else None
    s14 = round(sum(deltas[-14:]), 2) if len(deltas) >= 14 else None
    return s7, s14


def get_or_recompute_btc_magnet(
    config: Optional[EngineConfig],
    store: StateStore,
    *,
    recompute: bool = False,
) -> Tuple[Optional[BTCMagnetEvaluation], bool]:
    """Returns the stored BTCMagnetEvaluation; only recomputes when explicitly requested."""
    stored = getattr(store, "btc_magnet_evaluation", None)
    if stored is not None:
        return stored, False
    if not recompute:
        return None, False
    ev = BTCMagnetEngine(config).evaluate(store)
    ev.evaluation_origin = "EXPLICIT_RECOMPUTE"
    return ev, True


def _gate_wait_action(
    verdict: str,
    reconciliation_auth: str,
    sizing_factor: float,
    action: str,
    rotation: str,
    entry_instruction: str,
) -> Tuple[float, str, str, str]:
    """Enforces spot-only cap (<= 1.0x) and prevents entry instructions next to WAIT."""
    clamped = max(0.0, min(1.0, float(sizing_factor or 0.0)))
    if reconciliation_auth == "DENIED":
        return 0.0, action, rotation, entry_instruction
    if verdict != "SPEAK":
        safe_rot = rotation if rotation == "BTC -> USDT" else "Remain USDT"
        safe_action = (
            "Defensive Trim / Cash Only (0.00x)"
            if safe_rot == "BTC -> USDT"
            else "Wait / Cash Only (0.00x)"
        )
        return 0.0, safe_action, safe_rot, "NO ENTRY DIRECTIVE (Verdict: WAIT). Stand aside in cash."
    return clamped, action, rotation, entry_instruction


class BTCMagnetEngine:
    """Evaluates real-time liquidation clusters, 5-Regime Radar with majority voting,
    Liquidation Sweep Confirmation Engine (LSCE), and the 7 locked speaking rules.
    """

    def __init__(self, config: Optional[EngineConfig] = None) -> None:
        self.config = config
        self._last_fetch_ts: float = 0.0
        self._cached_liq_data: Optional[Dict[str, Any]] = None
        self._cache_ttl_sec: float = 45.0
        self._last_liqmap_source: str = "UNAVAILABLE"
        self._last_liqmap_error: str = ""

    def evaluate(self, store: StateStore) -> BTCMagnetEvaluation:
        """Evaluates current market state and populates store.btc_magnet_evaluation."""
        now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        provenance: Dict[str, str] = {}

        # 1. Spot Price (no hardcoded fallback)
        bin_spot = float(getattr(store, "binance_spot_price", 0.0) or 0.0)
        gen_spot = float(getattr(store, "spot_price", 0.0) or 0.0)
        bars_1h = list(getattr(store, "spot_klines_1h", None) or [])
        bars_4h = list(getattr(store, "spot_klines_4h", None) or [])
        bars_1d = list(getattr(store, "spot_klines_1d", None) or [])

        if bin_spot > 0.0:
            spot_price = bin_spot
            spot_available = True
            provenance["spot_price"] = "MEASURED_BINANCE_SPOT"
        elif gen_spot > 0.0:
            spot_price = gen_spot
            spot_available = True
            provenance["spot_price"] = "MEASURED_STORE_SPOT"
        elif bars_1h and float(getattr(bars_1h[-1], "close", 0.0) or 0.0) > 0.0:
            spot_price = float(bars_1h[-1].close)
            spot_available = True
            provenance["spot_price"] = "DERIVED_1H_CLOSE"
        else:
            spot_price = 0.0
            spot_available = False
            provenance["spot_price"] = "UNAVAILABLE"

        if not spot_available:
            return self._build_unavailable_spot_eval(now_utc, provenance, store)

        # 2. 24h Price Change & Range (no invented *1.018 / *0.982 skeleton)
        high_24h = float(getattr(store, "high_24h", 0.0) or 0.0)
        low_24h = float(getattr(store, "low_24h", 0.0) or 0.0)
        range_24h_available = high_24h > 0.0 and low_24h > 0.0 and high_24h >= low_24h
        if range_24h_available:
            provenance["range_24h"] = "MEASURED_24H"
        elif len(bars_1h) >= 24:
            bars_24 = bars_1h[-24:]
            high_24h = max(float(b.high) for b in bars_24)
            low_24h = min(float(b.low) for b in bars_24)
            range_24h_available = high_24h > 0.0 and low_24h > 0.0 and high_24h >= low_24h
            provenance["range_24h"] = "DERIVED_1H_24B" if range_24h_available else "UNAVAILABLE"
        else:
            high_24h = 0.0
            low_24h = 0.0
            provenance["range_24h"] = "UNAVAILABLE"

        explicit_chg_24h = store.__dict__.get("price_change_24h_pct", None)
        if explicit_chg_24h is not None:
            price_change_24h = float(explicit_chg_24h)
            price_change_24h_available = True
            provenance["price_change_24h"] = "MEASURED_24H"
        elif len(bars_1h) >= 24 and float(bars_1h[-24].open) > 0.0:
            open_24 = float(bars_1h[-24].open)
            price_change_24h = ((spot_price - open_24) / open_24) * 100.0
            price_change_24h_available = True
            provenance["price_change_24h"] = "DERIVED_1H_24B"
        else:
            price_change_24h = 0.0
            price_change_24h_available = False
            provenance["price_change_24h"] = "UNAVAILABLE"

        # 1h Price Change
        price_change_1h: Optional[float] = None
        if len(bars_1h) >= 2 and float(bars_1h[-1].open) > 0.0:
            last_b = bars_1h[-1]
            price_change_1h = ((spot_price - float(last_b.open)) / float(last_b.open)) * 100.0
            provenance["price_change_1h"] = "DERIVED_1H"
        else:
            provenance["price_change_1h"] = "UNAVAILABLE"

        # 3. Funding Rate (Annualized %) - distinguish 0.0 default from measured
        deriv = getattr(store, "derivatives_snapshot", None)
        deriv_populated = bool(
            deriv is not None
            and (
                float(getattr(deriv, "open_interest_btc", 0.0) or 0.0) > 0.0
                or float(getattr(deriv, "open_interest_usd", 0.0) or 0.0) > 0.0
                or float(getattr(deriv, "funding_rate_pct", 0.0) or 0.0) != 0.0
                or float(getattr(deriv, "oi_change_4h_pct", 0.0) or 0.0) != 0.0
            )
        )
        store_funding = float(getattr(store, "funding_rate_pct", 0.0) or 0.0)
        deriv_funding = float(getattr(deriv, "funding_rate_pct", 0.0) or 0.0) if deriv is not None else 0.0
        has_oi_btc = float(getattr(store, "open_interest_btc", 0.0) or 0.0) > 0.0

        if store_funding != 0.0:
            raw_funding = store_funding
            funding_available = True
            provenance["funding_rate"] = "MEASURED_STORE"
        elif deriv_populated:
            raw_funding = deriv_funding
            funding_available = True
            provenance["funding_rate"] = "MEASURED_DERIV"
        elif has_oi_btc:
            raw_funding = 0.0
            funding_available = True
            provenance["funding_rate"] = "MEASURED_STORE_ZERO"
        else:
            raw_funding = 0.0
            funding_available = False
            provenance["funding_rate"] = "UNAVAILABLE"

        if not funding_available:
            annual_funding_pct = 0.0
        elif abs(raw_funding) < 1.0:
            annual_funding_pct = raw_funding * 3.0 * 365.0
        else:
            annual_funding_pct = raw_funding

        # 4. Open Interest Velocity (no hardcoded 0.8 fallback)
        oi_hist_len = len(getattr(store, "oi_history", []) or [])
        explicit_oi = store.__dict__.get("oi_delta_4h_pct", None)
        if explicit_oi is not None:
            oi_delta_4h = float(explicit_oi)
            oi_available = True
            provenance["oi_delta_4h"] = "MEASURED_EXPLICIT"
        elif deriv is not None and oi_hist_len >= 2:
            oi_delta_4h = float(getattr(deriv, "oi_change_4h_pct", 0.0) or 0.0)
            oi_available = True
            provenance["oi_delta_4h"] = "MEASURED_DERIV"
        elif deriv_populated and float(getattr(deriv, "oi_change_4h_pct", 0.0) or 0.0) != 0.0:
            oi_delta_4h = float(deriv.oi_change_4h_pct)
            oi_available = True
            provenance["oi_delta_4h"] = "MEASURED_DERIV"
        elif hasattr(store, "get_oi_change_pct") and oi_hist_len >= 2:
            oi_delta_4h = float(store.get_oi_change_pct(14400.0))
            oi_available = True
            provenance["oi_delta_4h"] = "MEASURED_OI_HISTORY"
        else:
            oi_delta_4h = 0.0
            oi_available = False
            provenance["oi_delta_4h"] = "UNAVAILABLE"

        oi_delta_1h: Optional[float] = None
        if store.__dict__.get("oi_delta_1h_pct") is not None:
            oi_delta_1h = float(store.__dict__["oi_delta_1h_pct"])
        elif deriv is not None and (oi_hist_len >= 2 or float(getattr(deriv, "oi_change_1h_pct", 0.0) or 0.0) != 0.0):
            oi_delta_1h = float(getattr(deriv, "oi_change_1h_pct", 0.0) or 0.0)
        elif hasattr(store, "get_oi_change_pct") and oi_hist_len >= 2:
            oi_delta_1h = float(store.get_oi_change_pct(3600.0))

        oi_delta_24h: Optional[float] = None
        if store.__dict__.get("oi_delta_24h_pct") is not None:
            oi_delta_24h = float(store.__dict__["oi_delta_24h_pct"])
        elif hasattr(store, "get_oi_change_pct") and oi_hist_len >= 2:
            oi_delta_24h = float(store.get_oi_change_pct(86400.0))

        # 5. Spot CVD & Perp Flow Metrics
        spot_cvd_4h_btc = 0.0
        spot_cvd_ratio = 0.0
        flow_available = False
        s7, s14 = compute_spot_cvd_slopes(bars_1d)
        spot_cvd_slope_7d = float(s7) if s7 is not None else 0.0
        spot_cvd_slope_14d = float(s14) if s14 is not None else 0.0
        provenance["spot_cvd_7d"] = "DERIVED_1D_7B" if s7 is not None else "UNAVAILABLE"
        provenance["spot_cvd_14d"] = "DERIVED_1D_14B" if s14 is not None else "UNAVAILABLE"

        flow_snap = getattr(store, "flow_snapshot", None)
        flow_snap_populated = bool(
            flow_snap is not None
            and (
                float(getattr(flow_snap.w_4h, "spot_delta_btc", 0.0) or 0.0) != 0.0
                or float(getattr(flow_snap.w_24h, "spot_delta_btc", 0.0) or 0.0) != 0.0
                or float(getattr(flow_snap.w_4h, "perp_delta_btc", 0.0) or 0.0) != 0.0
                or float(getattr(flow_snap.w_24h, "perp_delta_btc", 0.0) or 0.0) != 0.0
            )
        )
        if flow_snap_populated:
            spot_cvd_4h_btc = float(getattr(flow_snap.w_4h, "spot_delta_btc", 0.0) or 0.0)
            s_vol_4h = float(getattr(flow_snap.w_4h, "spot_volume_btc", 0.0) or 0.0)
            if s_vol_4h > 0.0:
                buy_v = max(0.0, 0.5 * (s_vol_4h + spot_cvd_4h_btc))
                sell_v = max(1.0, 0.5 * (s_vol_4h - spot_cvd_4h_btc))
                spot_cvd_ratio = round(buy_v / sell_v, 2)
            else:
                spot_cvd_ratio = round(max(0.05, 1.0 + (spot_cvd_4h_btc / 1000.0)), 2)
            flow_available = True
            provenance["spot_cvd"] = "MEASURED_FLOW_SNAP"
        elif len(bars_1h) >= 4:
            bars_4 = bars_1h[-4:]
            has_real_flow = all(not getattr(b, "estimated", False) for b in bars_4) and any(
                float(getattr(b, "taker_buy_volume", 0.0) or 0.0) > 0.0
                and abs(float(getattr(b, "delta", 0.0) or 0.0)) > 1e-9
                for b in bars_4
            )
            if has_real_flow:
                taker_buy = sum(float(getattr(b, "taker_buy_volume", 0.0) or 0.0) for b in bars_4)
                tot_vol = sum(float(getattr(b, "volume", 0.0) or 0.0) for b in bars_4)
                taker_sell = max(tot_vol - taker_buy, 1.0)
                spot_cvd_ratio = round(taker_buy / taker_sell, 2)
                spot_cvd_4h_btc = float(sum(float(getattr(b, "delta", 0.0) or 0.0) for b in bars_4))
                flow_available = True
                provenance["spot_cvd"] = "DERIVED_1H_4B"
            else:
                provenance["spot_cvd"] = "UNAVAILABLE"
        else:
            provenance["spot_cvd"] = "UNAVAILABLE"

        perp_flow_available = False
        perp_cvd_trend = "UNAVAILABLE"
        perp_bars_1h = list(getattr(store, "perp_klines_1h", None) or [])
        if flow_snap_populated and float(getattr(flow_snap.w_4h, "perp_delta_btc", 0.0) or 0.0) != 0.0:
            p4 = float(flow_snap.w_4h.perp_delta_btc)
            perp_flow_available = True
            perp_cvd_trend = "Positive" if p4 > 15.0 else ("Negative" if p4 < -15.0 else "Neutral")
            provenance["perp_cvd"] = "MEASURED_FLOW_SNAP"
        elif len(perp_bars_1h) >= 4:
            pb4 = perp_bars_1h[-4:]
            if all(not getattr(b, "estimated", False) for b in pb4) and any(
                float(getattr(b, "taker_buy_volume", 0.0) or 0.0) > 0.0
                and abs(float(getattr(b, "delta", 0.0) or 0.0)) > 1e-9
                for b in pb4
            ):
                p4 = sum(float(getattr(b, "delta", 0.0) or 0.0) for b in pb4)
                perp_flow_available = True
                perp_cvd_trend = "Positive" if p4 > 15.0 else ("Negative" if p4 < -15.0 else "Neutral")
                provenance["perp_cvd"] = "DERIVED_1H_4B"
            else:
                provenance["perp_cvd"] = "UNAVAILABLE"
        else:
            provenance["perp_cvd"] = "UNAVAILABLE"

        # 6. Technical Anchors (VWAPs, EMAs, 200 SMA, Swing Extremes) - NO fabricated multipliers
        rm_eval = getattr(store, "regime_matrix_evaluation", None)
        ema_snap = getattr(store, "ema_strategy", None)

        daily_vwap: Optional[float] = float(getattr(store, "daily_vwap", 0.0) or 0.0) or None
        if daily_vwap is not None:
            provenance["daily_vwap"] = "MEASURED_STORE"
        elif rm_eval is not None and float(getattr(rm_eval, "daily_vwap", 0.0) or 0.0) > 0.0:
            daily_vwap = float(rm_eval.daily_vwap)
            provenance["daily_vwap"] = "DERIVED_REGIME_MATRIX"
        elif len(bars_1h) >= 24:
            daily_vwap = _compute_vwap(bars_1h[-24:])
            provenance["daily_vwap"] = "DERIVED_1H_24B" if daily_vwap is not None else "UNAVAILABLE"
        else:
            provenance["daily_vwap"] = "UNAVAILABLE"

        weekly_vwap: Optional[float] = float(getattr(store, "weekly_vwap", 0.0) or 0.0) or None
        if weekly_vwap is not None:
            provenance["weekly_vwap"] = "MEASURED_STORE"
        elif rm_eval is not None and float(getattr(rm_eval, "weekly_vwap", 0.0) or 0.0) > 0.0:
            weekly_vwap = float(rm_eval.weekly_vwap)
            provenance["weekly_vwap"] = "DERIVED_REGIME_MATRIX"
        elif len(bars_1h) >= 168:
            weekly_vwap = _compute_vwap(bars_1h[-168:])
            provenance["weekly_vwap"] = "DERIVED_1H_168B" if weekly_vwap is not None else "UNAVAILABLE"
        else:
            provenance["weekly_vwap"] = "UNAVAILABLE"

        vwap_available = daily_vwap is not None and weekly_vwap is not None

        closes_1d = [float(b.close) for b in bars_1d if float(getattr(b, "close", 0.0) or 0.0) > 0.0]

        ema_20d: Optional[float] = float(getattr(store, "ema_20d", 0.0) or 0.0) or None
        if ema_20d is not None:
            provenance["ema_20d"] = "MEASURED_STORE"
        elif ema_snap is not None and float(getattr(ema_snap, "daily_ema_20", 0.0) or 0.0) > 0.0:
            ema_20d = float(ema_snap.daily_ema_20)
            provenance["ema_20d"] = "DERIVED_EMA_SNAP"
        else:
            ema_20d = _compute_ema(closes_1d, 20)
            provenance["ema_20d"] = "DERIVED_1D_EMA20" if ema_20d is not None else "UNAVAILABLE"
        ema_20d_available = ema_20d is not None

        ema_50d: Optional[float] = float(getattr(store, "ema_50d", 0.0) or 0.0) or None
        if ema_50d is not None:
            provenance["ema_50d"] = "MEASURED_STORE"
        elif ema_snap is not None and float(getattr(ema_snap, "daily_ema_50", 0.0) or 0.0) > 0.0:
            ema_50d = float(ema_snap.daily_ema_50)
            provenance["ema_50d"] = "DERIVED_EMA_SNAP"
        elif rm_eval is not None and float(getattr(rm_eval, "ema_50_1d", 0.0) or 0.0) > 0.0:
            ema_50d = float(rm_eval.ema_50_1d)
            provenance["ema_50d"] = "DERIVED_REGIME_MATRIX"
        else:
            ema_50d = _compute_ema(closes_1d, 50)
            provenance["ema_50d"] = "DERIVED_1D_EMA50" if ema_50d is not None else "UNAVAILABLE"
        ema_50d_available = ema_50d is not None

        ma_200d: Optional[float] = (
            float(getattr(store, "daily_sma_200", 0.0) or getattr(store, "ma_200d", 0.0) or 0.0) or None
        )
        if ma_200d is not None:
            provenance["ma_200d"] = "MEASURED_STORE"
        else:
            ma_200d = _compute_sma(closes_1d, 200)
            provenance["ma_200d"] = "DERIVED_1D_SMA200" if ma_200d is not None else "UNAVAILABLE"
        ma_200d_available = ma_200d is not None

        # 4H swing extremes (from 1H bars, explicit 24h range, or 4H bars - never invented)
        swing_high_4h: Optional[float] = None
        swing_low_4h: Optional[float] = None
        capitulation_wick_low: Optional[float] = None
        if len(bars_1h) >= 24:
            bars_24 = bars_1h[-24:]
            swing_high_4h = max(float(b.high) for b in bars_24)
            swing_low_4h = min(float(b.low) for b in bars_24)
            capitulation_wick_low = swing_low_4h
            provenance["swing_24h"] = "DERIVED_1H_24B"
        elif range_24h_available:
            swing_high_4h = high_24h
            swing_low_4h = low_24h
            capitulation_wick_low = low_24h
            provenance["swing_24h"] = "MEASURED_24H"
        elif len(bars_4h) >= 6:
            bars_4_24 = bars_4h[-6:]
            swing_high_4h = max(float(b.high) for b in bars_4_24)
            swing_low_4h = min(float(b.low) for b in bars_4_24)
            capitulation_wick_low = swing_low_4h
            provenance["swing_24h"] = "DERIVED_4H_6B"
        else:
            provenance["swing_24h"] = "UNAVAILABLE"

        # ATR & ATR compression (no hardcoded 74.4 or spot*0.012)
        atr_14_explicit = float(getattr(store, "atr_14_1h", 0.0) or 0.0) or None
        atr_comp_explicit = store.__dict__.get("atr_compression_pct", None)
        calc_atr, calc_comp = _compute_atr_and_compression(bars_1h)
        atr = atr_14_explicit if atr_14_explicit is not None else calc_atr
        if atr_comp_explicit is not None:
            atr_compression_pct: Optional[float] = float(atr_comp_explicit)
            provenance["atr_compression"] = "MEASURED_STORE"
        elif rm_eval is not None and float(getattr(rm_eval, "atr_compression_pct", 0.0) or 0.0) > 0.0:
            atr_compression_pct = float(rm_eval.atr_compression_pct)
            provenance["atr_compression"] = "DERIVED_REGIME_MATRIX"
        elif calc_comp is not None:
            atr_compression_pct = calc_comp
            provenance["atr_compression"] = "DERIVED_1H_ATR"
        else:
            atr_compression_pct = None
            provenance["atr_compression"] = "UNAVAILABLE"
        atr_available = atr_compression_pct is not None

        # Positioning ratios (no hardcoded 1.85 / 0.45 / -1.3)
        explicit_ls = getattr(store, "long_short_ratio", None)
        if explicit_ls is not None and float(explicit_ls) > 0.0:
            long_short_ratio: Optional[float] = float(explicit_ls)
            ls_ratio_available = True
            provenance["long_short_ratio"] = "MEASURED_STORE"
        else:
            g_ls = float(getattr(store, "global_account_ls_ratio", 1.0) or 1.0)
            t_ls = float(getattr(store, "top_trader_ls_ratio", 1.0) or 1.0)
            if deriv_populated or g_ls != 1.0:
                long_short_ratio = g_ls if g_ls != 1.0 else t_ls
                ls_ratio_available = True
                provenance["long_short_ratio"] = "MEASURED_STORE_ACCOUNT_LS"
            else:
                long_short_ratio = None
                ls_ratio_available = False
                provenance["long_short_ratio"] = "UNAVAILABLE"

        explicit_depth = getattr(store, "bids_asks_depth_ratio", None)
        if explicit_depth is not None and float(explicit_depth) > 0.0:
            bids_asks_depth_ratio: Optional[float] = float(explicit_depth)
            depth_ratio_available = True
            provenance["bids_asks_depth_ratio"] = "MEASURED_STORE"
        else:
            bids_asks_depth_ratio = None
            depth_ratio_available = False
            provenance["bids_asks_depth_ratio"] = "UNAVAILABLE"

        explicit_basis = store.__dict__.get("futures_basis_annualized", None)
        perp_px = float(getattr(store, "binance_perp_price", 0.0) or 0.0)
        if explicit_basis is not None:
            futures_basis_annual: Optional[float] = float(explicit_basis)
            basis_available = True
            provenance["futures_basis_annual"] = "MEASURED_STORE"
        elif rm_eval is not None and hasattr(rm_eval, "annualized_basis_pct") and float(getattr(rm_eval, "annualized_basis_pct", 0.0) or 0.0) != 0.0:
            futures_basis_annual = float(rm_eval.annualized_basis_pct)
            basis_available = True
            provenance["futures_basis_annual"] = "DERIVED_REGIME_MATRIX"
        elif perp_px > 0.0 and spot_price > 0.0 and funding_available:
            futures_basis_annual = round(((perp_px - spot_price) / spot_price) * 100.0 * 12.0 + annual_funding_pct, 2)
            basis_available = True
            provenance["futures_basis_annual"] = "DERIVED_PERP_SPOT"
        else:
            futures_basis_annual = None
            basis_available = False
            provenance["futures_basis_annual"] = "UNAVAILABLE"

        # 7. Liquidation Clusters & Multi-Tier Ladder
        upper_magnet, lower_magnet, ladder = self._get_liquidation_magnets_and_ladder(spot_price, store=store)
        liqmap_source = str(ladder.get("liqmap_source", self._last_liqmap_source) or "UNAVAILABLE")
        liqmap_error = str(ladder.get("liqmap_error", self._last_liqmap_error) or "")
        provenance["liqmap"] = liqmap_source
        provenance["ladder_bands"] = str(ladder.get("ladder_source", "MODELLED_STATIC"))

        ladder["tiers_6"] = self._build_six_tier_ladder(
            spot_price=spot_price,
            swing_high_4h=swing_high_4h if swing_high_4h is not None else spot_price,
            swing_low_4h=swing_low_4h if swing_low_4h is not None else spot_price,
            upper=upper_magnet,
            lower=lower_magnet,
            long_short_ratio=long_short_ratio if long_short_ratio is not None else 1.0,
            store=store,
        )

        # 8. Dual Imbalance Accounting (Immediate vs Total Ladder)
        imm_u = ladder.get("immediate_upper_usd", upper_magnet.usd_volume) / 1e6
        imm_l = ladder.get("immediate_lower_usd", lower_magnet.usd_volume) / 1e6
        tot_u = ladder.get("total_upper_usd", 0.0) / 1e6
        tot_l = ladder.get("total_lower_usd", 0.0) / 1e6

        immediate_ratio = round(imm_l / max(imm_u, 0.1), 2) if (imm_u > 0 or imm_l > 0) else 0.0
        total_ladder_ratio = round(tot_l / max(tot_u, 0.1), 2) if (tot_u > 0 or tot_l > 0) else 0.0

        # Gravitational attraction & Direction
        up_weight = upper_magnet.usd_volume / max(abs(upper_magnet.dist_pct), 0.5) if upper_magnet.price > 0 else 0.0
        lo_weight = lower_magnet.usd_volume / max(abs(lower_magnet.dist_pct), 0.5) if lower_magnet.price > 0 else 0.0

        if upper_magnet.usd_volume >= lower_magnet.usd_volume * 1.15 or up_weight >= lo_weight * 1.15:
            pull_direction = "UPPER"
        elif lower_magnet.usd_volume >= upper_magnet.usd_volume * 1.15 or lo_weight >= up_weight * 1.15:
            pull_direction = "LOWER"
        else:
            pull_direction = "NEUTRAL"

        pull_ratio = round(upper_magnet.usd_volume / max(lower_magnet.usd_volume, 1.0), 2)

        # 9. Six-Factor Decision Hierarchy
        six_factors = self._evaluate_six_factors(
            imm_ratio=immediate_ratio,
            tot_ratio=total_ladder_ratio,
            imm_u=imm_u,
            imm_l=imm_l,
            tot_u=tot_u,
            tot_l=tot_l,
            liqmap_source=liqmap_source,
            spot_cvd_ratio=spot_cvd_ratio if flow_available else None,
            perp_cvd_trend=perp_cvd_trend,
            raw_funding=raw_funding if funding_available else None,
            ls_ratio=long_short_ratio,
            dist_l=abs(lower_magnet.dist_pct),
            dist_u=abs(upper_magnet.dist_pct),
            atr_comp=atr_compression_pct,
            range_24h_available=range_24h_available,
        )

        # 10. Liquidation Sweep Confirmation Engine (LSCE)
        lsce = self._evaluate_lsce(
            spot_price=spot_price,
            lower_magnet=lower_magnet,
            upper_magnet=upper_magnet,
            capitulation_wick_low=capitulation_wick_low,
            swing_low_4h=swing_low_4h,
            spot_cvd_ratio=spot_cvd_ratio if flow_available else None,
            bids_asks_depth_ratio=bids_asks_depth_ratio,
            liqmap_source=liqmap_source,
        )

        # 11. 5-Regime Radar Framework (Majority Voting >= 3 of 4)
        regime_result = self._evaluate_5_regimes(
            spot_price=spot_price,
            spot_available=spot_available,
            daily_vwap=daily_vwap,
            weekly_vwap=weekly_vwap,
            ema_20d=ema_20d,
            ema_50d=ema_50d,
            high_24h=high_24h,
            low_24h=low_24h,
            range_24h_available=range_24h_available,
            swing_high_4h=swing_high_4h,
            swing_low_4h=swing_low_4h,
            price_change_1h=price_change_1h,
            price_change_24h=price_change_24h if price_change_24h_available else None,
            spot_cvd_ratio=spot_cvd_ratio if flow_available else None,
            spot_cvd_4h_btc=spot_cvd_4h_btc if flow_available else None,
            raw_funding=raw_funding if funding_available else None,
            annual_funding_pct=annual_funding_pct if funding_available else None,
            oi_delta_1h=oi_delta_1h,
            oi_delta_4h=oi_delta_4h if oi_available else None,
            oi_delta_24h=oi_delta_24h,
            long_short_ratio=long_short_ratio,
            bids_asks_depth_ratio=bids_asks_depth_ratio,
            futures_basis_annual=futures_basis_annual,
            atr_compression_pct=atr_compression_pct,
            upper_magnet=upper_magnet,
            lower_magnet=lower_magnet,
            liqmap_source=liqmap_source,
            pull_direction=pull_direction,
            lsce=lsce,
        )

        # 12. Dual Inviolable Stops (no invented ma_200d or swing_low_4h)
        if swing_low_4h is not None and swing_low_4h > 0.0:
            structural_stop = round(swing_low_4h * 0.998, 2)
            structural_dist_pct = round(abs(spot_price - structural_stop) / spot_price * 100.0, 2)
        else:
            structural_stop = 0.0
            structural_dist_pct = 0.0

        deep_candidates: List[float] = []
        if ma_200d is not None and ma_200d > 0.0:
            deep_candidates.append(ma_200d)
        if swing_low_4h is not None and swing_low_4h > 0.0:
            deep_candidates.append(swing_low_4h * 0.985)
        if lower_magnet.price > 0.0:
            deep_candidates.append(lower_magnet.price * 0.99)

        if deep_candidates:
            deep_shelf = min(deep_candidates)
            disaster_stop = round(deep_shelf * 0.993, 2)
            disaster_dist_pct = round(abs(spot_price - disaster_stop) / spot_price * 100.0, 2)
            risk_budget_pass = bool(disaster_dist_pct <= RISK_BUDGET_MAX_PCT)
        else:
            disaster_stop = 0.0
            disaster_dist_pct = 0.0
            risk_budget_pass = False

        # Simple 3-way regime label (fail closed to UNAVAILABLE when range_24h missing)
        if not range_24h_available or low_24h <= 0.0:
            simple_regime = "UNAVAILABLE"
        else:
            range_spread_pct = ((high_24h - low_24h) / low_24h) * 100.0
            if range_spread_pct < 4.8:
                simple_regime = "Range"
            elif price_change_24h_available and price_change_24h > 2.5:
                simple_regime = "TrendUp"
            elif price_change_24h_available and price_change_24h < -2.5:
                simple_regime = "TrendDown"
            else:
                simple_regime = "Range"

        # 13. Evaluate the 7 Locked Internal Speaking Rules (all gates fail-closed)
        liqmap_is_live = liqmap_source in ("LIVE_EDGEORNOT", "CACHED_LIQMAP")
        rule_checks, verdict, headline, body, rule_subtitle = self._evaluate_speaking_rules(
            spot_price=spot_price,
            spot_available=spot_available,
            price_change_24h=price_change_24h if price_change_24h_available else None,
            upper=upper_magnet,
            lower=lower_magnet,
            liqmap_is_live=liqmap_is_live,
            liqmap_source=liqmap_source,
            pull_direction=pull_direction,
            up_weight=up_weight,
            lo_weight=lo_weight,
            funding_annual_pct=annual_funding_pct if funding_available else None,
            oi_delta_4h=oi_delta_4h if oi_available else None,
            spot_cvd_4h_btc=spot_cvd_4h_btc if flow_available else None,
            regime=simple_regime,
        )

        passed_count = sum(1 for r in rule_checks if r.passed)
        verdict_badge = "SWING EDGE PRESENT" if verdict == "SPEAK" else "NO CLEAR EDGE - WAIT"

        gated_sizing, gated_action, gated_rotation, gated_entry = _gate_wait_action(
            verdict=verdict,
            reconciliation_auth="AUTHORIZED",
            sizing_factor=regime_result["sizing_factor"],
            action=regime_result["action"],
            rotation=regime_result["rotation"],
            entry_instruction=regime_result.get("entry_instruction", ""),
        )

        eval_result = BTCMagnetEvaluation(
            timestamp_utc=now_utc,
            spot_price=spot_price,
            price_change_24h_pct=price_change_24h,
            high_24h=high_24h,
            low_24h=low_24h,
            upper_magnet=upper_magnet,
            lower_magnet=lower_magnet,
            pull_direction=pull_direction,
            pull_ratio=pull_ratio,
            funding_rate_annual_pct=annual_funding_pct,
            oi_delta_4h_pct=oi_delta_4h,
            market_regime=simple_regime,
            verdict=verdict,
            verdict_badge=verdict_badge,
            headline=headline,
            body=body,
            rule_subtitle=rule_subtitle,
            rules_passed_count=passed_count,
            rule_checks=rule_checks,
            magnet_summary_markdown="",
            # Institutional 5-Regime Radar
            regime_id=regime_result["regime_id"],
            regime_name=regime_result["regime_name"],
            regime_diagnosis=regime_result["regime_diagnosis"],
            majority_score=regime_result["majority_score"],
            majority_matches_count=regime_result["matches_count"],
            matched_observations=regime_result["matched"],
            all_observations=regime_result["all_observations"],
            is_conflicted=regime_result["is_conflicted"],
            conflict_reason=regime_result.get("conflict_reason", ""),
            # LSCE
            lsce_status=lsce["status"],
            lsce_cluster_tested=lsce["cluster_tested"],
            lsce_sweep_depth_pct=lsce["sweep_depth_pct"],
            lsce_reclaim_level=lsce["reclaim_level"],
            lsce_spot_absorption=lsce["spot_absorption"],
            lsce_action_verdict=lsce["action_verdict"],
            # Multi-tier & Dual Imbalance
            immediate_ratio=immediate_ratio,
            immediate_l_vol=imm_l,
            immediate_u_vol=imm_u,
            total_ladder_ratio=total_ladder_ratio,
            total_l_vol=tot_l,
            total_u_vol=tot_u,
            spot_cvd_slope_7d=spot_cvd_slope_7d,
            spot_cvd_slope_14d=spot_cvd_slope_14d,
            six_factors=six_factors,
            levels_ladder=ladder,
            # Capital Sizing & Stops (spot-only capped <= 1.0x & WAIT-gated)
            sizing_factor=gated_sizing,
            action=gated_action,
            rotation=gated_rotation,
            entry_instruction=gated_entry,
            stop_rule=regime_result.get("stop_rule", ""),
            structural_stop_price=structural_stop,
            structural_stop_dist_pct=structural_dist_pct,
            disaster_stop_price=disaster_stop,
            disaster_stop_dist_pct=disaster_dist_pct,
            risk_budget_pass=risk_budget_pass,
            # Provenance & Data Availability Metadata
            evaluation_origin="ENGINE_EVALUATE",
            liqmap_source=liqmap_source,
            liqmap_error=liqmap_error,
            spot_available=spot_available,
            range_24h_available=range_24h_available,
            price_change_24h_available=price_change_24h_available,
            oi_available=oi_available,
            funding_available=funding_available,
            flow_available=flow_available,
            perp_flow_available=perp_flow_available,
            vwap_available=vwap_available,
            ema_20d_available=ema_20d_available,
            ema_50d_available=ema_50d_available,
            ma_200d_available=ma_200d_available,
            atr_available=atr_available,
            ls_ratio_available=ls_ratio_available,
            depth_ratio_available=depth_ratio_available,
            basis_available=basis_available,
            input_provenance=provenance,
        )

        # 14. Upstream B1 vs B2 Reconciliation & Data Integrity Audit Gate
        b1_input = getattr(store, "b1_telemetry_snapshot", None) or getattr(store, "b1_raw_telemetry", None)
        recon_engine = ReconciliationEngine()
        recon_result = recon_engine.reconcile(b1_input, eval_result, store=store)

        eval_result.reconciliation_verdict = recon_result.verdict
        eval_result.reconciliation_auth = recon_result.execution_authorization
        eval_result.reconciliation_fail_reasons = recon_result.fail_reasons
        eval_result.reconciliation_warnings = recon_result.warnings
        eval_result.reconciliation_table = [
            {
                "metric": item.metric,
                "b1_value": item.b1_value,
                "b2_value": item.b2_value,
                "difference": item.difference,
                "severity": item.severity,
                "explanation": item.explanation,
            }
            for item in recon_result.discrepancy_table
        ]

        # Inviolable Gate Override: If DENIED, enforce Fail-Closed Law (100% USDT / 0.00x)
        if recon_result.execution_authorization == "DENIED":
            eval_result.action = "Execution Denied: Data Integrity Failure (0.00x)"
            eval_result.sizing_factor = 0.00
            eval_result.rotation = "BTC -> USDT"
            eval_result.verdict = "WAIT"
            eval_result.verdict_badge = "DATA INTEGRITY LOCKOUT"
            fail_msg = recon_result.fail_reasons[0] if recon_result.fail_reasons else "Critical data integrity failure."
            eval_result.entry_instruction = (
                f"FAIL-CLOSED LOCKOUT: {fail_msg} "
                f"Capital allocation locked to 0.00x (100% USDT Cash). Stand aside."
            )
            if len(eval_result.rule_checks) >= 7:
                eval_result.rule_checks[6].passed = False
                eval_result.rule_checks[6].detail = "OVERRIDDEN TO WAIT: Reconciliation Gate DENIED (Fail-Closed Lockout)"
                eval_result.rules_passed_count = sum(1 for r in eval_result.rule_checks if r.passed)

        # 15. Build Markdown Brief AFTER final verdict/lockout/gating so brief & state never diverge
        eval_result.magnet_summary_markdown = self._build_markdown_brief(eval_result)

        if store is not None:
            store.btc_magnet_evaluation = eval_result
            store.reconciliation_evaluation = recon_result

        return eval_result

    def _build_unavailable_spot_eval(
        self,
        now_utc: str,
        provenance: Dict[str, str],
        store: Optional[StateStore],
    ) -> BTCMagnetEvaluation:
        """Builds a fail-closed UNAVAILABLE evaluation when spot price is missing."""
        rules = [
            BTCMagnetRuleCheck(1, "Clear Magnet Present", False, "Spot price UNAVAILABLE"),
            BTCMagnetRuleCheck(2, "Open-Interest Confirmation", False, "Spot price UNAVAILABLE"),
            BTCMagnetRuleCheck(3, "Funding Non-Contradictory", False, "Spot price UNAVAILABLE"),
            BTCMagnetRuleCheck(4, "Regime Conduciveness", False, "Spot price UNAVAILABLE"),
            BTCMagnetRuleCheck(5, "Spot Flow & Structure Alignment", False, "Spot price UNAVAILABLE"),
            BTCMagnetRuleCheck(6, "Not Already Swept", False, "Spot price UNAVAILABLE"),
            BTCMagnetRuleCheck(7, "Conviction Threshold", False, "0/6 passed (Spot price UNAVAILABLE). Default: WAIT."),
        ]
        ev = BTCMagnetEvaluation(
            timestamp_utc=now_utc,
            spot_price=0.0,
            upper_magnet=BTCMagnetLevel(source="UNAVAILABLE"),
            lower_magnet=BTCMagnetLevel(source="UNAVAILABLE"),
            pull_direction="NEUTRAL",
            pull_ratio=1.0,
            market_regime="UNAVAILABLE",
            verdict="WAIT",
            verdict_badge="DATA UNAVAILABLE - WAIT",
            headline="No clear edge - wait.",
            body="Spot price UNAVAILABLE. No liquidation horizon can be anchored. Default to cash.",
            rule_subtitle="Locked Principle: Missing spot telemetry fails closed to WAIT.",
            rules_passed_count=0,
            rule_checks=rules,
            regime_id="TRANSITION_MIXED",
            regime_name="Unavailable / No Spot Feed",
            regime_diagnosis="Spot price UNAVAILABLE - fail-closed cash posture",
            majority_score="0/4",
            majority_matches_count=0,
            all_observations=[
                ("Spot price telemetry present", False),
                ("24h range telemetry present", False),
                ("Derivatives / flow telemetry present", False),
                ("Live liquidation map present", False),
            ],
            lsce_status="UNTESTED",
            lsce_cluster_tested="UNAVAILABLE",
            lsce_action_verdict="Spot price UNAVAILABLE. Maintain 100% USDT cash.",
            sizing_factor=0.0,
            action="Wait / Cash Only (0.00x)",
            rotation="Remain USDT",
            entry_instruction="NO ENTRY DIRECTIVE (Spot price UNAVAILABLE). Stand aside in cash.",
            stop_rule="UNAVAILABLE (no spot price)",
            risk_budget_pass=False,
            reconciliation_verdict="FAIL",
            reconciliation_auth="DENIED",
            reconciliation_fail_reasons=["Spot price UNAVAILABLE"],
            evaluation_origin="ENGINE_EVALUATE",
            liqmap_source="UNAVAILABLE",
            input_provenance=provenance,
        )
        ev.magnet_summary_markdown = self._build_markdown_brief(ev)
        if store is not None:
            store.btc_magnet_evaluation = ev
        return ev

    def _get_liquidation_magnets_and_ladder(
        self,
        spot_price: float,
        store: Optional[StateStore] = None,
    ) -> Tuple[BTCMagnetLevel, BTCMagnetLevel, Dict[str, Any]]:
        """Fetches live liquidation clusters or computes structural levels and modeled ladder.

        Guarantees Mathematical Consistency: Total ladder is dynamically calculated
        as the cumulative sum of all leverage bands (10x-100x) and is strictly >= the immediate tier.
        """
        upper, lower = self._get_liquidation_magnets(spot_price, store=store)

        # Scale 100x band to the immediate cluster volume if higher
        imm_short_usd = max(upper.usd_volume, 4_200_000.0)
        imm_long_usd = max(lower.usd_volume, 102_800_000.0)

        short_bands = {
            "100x_short": {"price": round(spot_price * 1.008, 2), "usd": imm_short_usd},
            "50x_short": {"price": round(spot_price * 1.018, 2), "usd": 45_000_000.0},
            "25x_short": {"price": round(spot_price * 1.034, 2), "usd": 85_000_000.0},
            "10x_short": {"price": round(spot_price * 1.075, 2), "usd": 110_000_000.0},
        }
        long_bands = {
            "100x_long": {"price": round(spot_price * 0.994, 2), "usd": imm_long_usd},
            "50x_long": {"price": round(spot_price * 0.982, 2), "usd": 95_000_000.0},
            "25x_long": {"price": round(spot_price * 0.965, 2), "usd": 140_000_000.0},
            "10x_long": {"price": round(spot_price * 0.915, 2), "usd": 190_000_000.0},
        }

        # Dynamic sum of bands guarantees total >= immediate
        tot_upper_usd = round(sum(b["usd"] for b in short_bands.values()), 2)
        tot_lower_usd = round(sum(b["usd"] for b in long_bands.values()), 2)

        is_live = self._last_liqmap_source in ("LIVE_EDGEORNOT", "CACHED_LIQMAP")
        ladder_source = "MODELLED_HYBRID_LIVE_100X" if is_live else "MODELLED_STATIC"

        bands = {**short_bands, **long_bands}
        ladder = {
            "immediate_upper_usd": imm_short_usd,
            "immediate_lower_usd": imm_long_usd,
            "total_upper_usd": tot_upper_usd,
            "total_lower_usd": tot_lower_usd,
            "bands": bands,
            "modeled": True,
            "ladder_source": ladder_source,
            "liqmap_source": self._last_liqmap_source,
            "liqmap_error": self._last_liqmap_error,
        }
        return upper, lower, ladder

    def _build_six_tier_ladder(
        self,
        spot_price: float,
        swing_high_4h: float,
        swing_low_4h: float,
        upper: BTCMagnetLevel,
        lower: BTCMagnetLevel,
        long_short_ratio: float,
        store: Optional[StateStore] = None,
    ) -> List[Dict[str, Any]]:
        """Builds canonical 6-tier modeled liquidation ladder (10x/25x/50-100x upper & lower)."""
        cur_p = max(spot_price, 1.0)
        oi_btc = 0.0
        if store is not None:
            oi_btc = float(getattr(store, "open_interest_btc", 0.0) or 0.0)
            if oi_btc <= 0.0 and getattr(store, "derivatives_snapshot", None) is not None:
                oi_btc = float(getattr(store.derivatives_snapshot, "open_interest_btc", 0.0) or 0.0)
        oi_source = "MEASURED_OI" if oi_btc > 0.0 else "ESTIMATED_BASELINE"
        oi_notional_m = max(10.0, (oi_btc * cur_p) / 1e6) if oi_btc > 0.0 else 5000.0
        ls = long_short_ratio if long_short_ratio > 0.0 else 1.0
        long_share = ls / (1.0 + ls)
        l_crowd_w = max(0.50, long_share / 0.50)
        u_crowd_w = max(0.50, (1.0 - long_share) / 0.50)

        u_near_vol = round(upper.usd_volume / 1e6, 1)
        l_near_vol = round(lower.usd_volume / 1e6, 1)
        u_25_vol = round(max(1.0, oi_notional_m * 0.032 * u_crowd_w), 1)
        u_10_vol = round(max(1.0, oi_notional_m * 0.024 * u_crowd_w), 1)
        l_25_vol = round(max(1.0, oi_notional_m * 0.040 * l_crowd_w), 1)
        l_10_vol = round(max(1.0, oi_notional_m * 0.028 * l_crowd_w), 1)

        hi_ref = max(swing_high_4h, cur_p)
        lo_ref = min(swing_low_4h, cur_p)
        use_up_near = (cur_p * 1.002) <= upper.price <= (hi_ref * 1.035)
        use_lo_near = (lo_ref * 0.965) <= lower.price <= (cur_p * 0.998)
        u_near_p = round(upper.price, 2) if use_up_near else round(max(swing_high_4h * 1.005, cur_p * 1.008), 2)
        s25_p = round(max(swing_high_4h * 1.012, u_near_p * 1.010), 2)
        s10_p = round(max(swing_high_4h * 1.025, s25_p * 1.015), 2)
        l_near_p = round(lower.price, 2) if use_lo_near else round(min(swing_low_4h * 0.995, cur_p * 0.992), 2)
        l25_p = round(min(swing_low_4h * 0.988, l_near_p * 0.990), 2)
        l10_p = round(min(swing_low_4h * 0.975, l25_p * 0.985), 2)

        def _tier(tier: str, lev: str, side: str, lvl: float, vol_m: float, dist_override: Optional[float] = None, is_nearest: bool = False) -> Dict[str, Any]:
            signed_pct = ((lvl - cur_p) / cur_p) * 100.0
            if dist_override is not None:
                signed_pct = abs(float(dist_override)) if side == "upper" else -abs(float(dist_override))
            return {
                "tier": tier,
                "leverage": lev,
                "side": side,
                "price": lvl,
                "distance_pct": round(signed_pct, 2),
                "estimated_vol_m": round(vol_m, 1),
                "modeled": True,
                "oi_source": oi_source,
                "is_nearest": is_nearest,
            }

        return [
            _tier("10x Shorts", "10x", "upper", s10_p, u_10_vol),
            _tier("25x Shorts", "25x", "upper", s25_p, u_25_vol),
            _tier("50-100x Shorts", "50-100x", "upper", u_near_p, u_near_vol, upper.dist_pct if use_up_near else None, is_nearest=True),
            _tier("100x Longs", "100x", "lower", l_near_p, l_near_vol, lower.dist_pct if use_lo_near else None, is_nearest=True),
            _tier("25x Longs", "25x", "lower", l25_p, l_25_vol),
            _tier("10x Longs", "10x", "lower", l10_p, l_10_vol),
        ]

    def _evaluate_six_factors(
        self,
        imm_ratio: float,
        tot_ratio: float,
        imm_u: float,
        imm_l: float,
        tot_u: float,
        tot_l: float,
        liqmap_source: str,
        spot_cvd_ratio: Optional[float],
        perp_cvd_trend: str,
        raw_funding: Optional[float],
        ls_ratio: Optional[float],
        dist_l: float,
        dist_u: float,
        atr_comp: Optional[float],
        range_24h_available: bool,
    ) -> Dict[str, str]:
        """Evaluates the 6 descriptive hierarchy factors with explicit UNAVAILABLE/MODELLED tags."""
        src_tag = "LIVE" if liqmap_source in ("LIVE_EDGEORNOT", "CACHED_LIQMAP") else "MODELLED"
        f1 = (
            f"[{src_tag} 100x / MODELLED Ladder] Immediate: LOWER {imm_ratio:.1f}x (${imm_l:.1f}M vs ${imm_u:.1f}M) | "
            f"Total Ladder: LOWER {tot_ratio:.2f}x (${tot_l:.1f}M vs ${tot_u:.1f}M)"
        )
        spot_str = f"{spot_cvd_ratio:.2f}" if spot_cvd_ratio is not None else "UNAVAILABLE"
        f2 = f"Spot CVD ratio {spot_str} vs Perp CVD {perp_cvd_trend}"
        fund_str = f"{raw_funding:+.4f}%/8h" if raw_funding is not None else "UNAVAILABLE"
        if ls_ratio is not None and ls_ratio > 0:
            long_pct = round((ls_ratio / (1.0 + ls_ratio)) * 100.0, 1)
            ls_str = f"{ls_ratio:.2f} ({long_pct}% net long)"
        else:
            ls_str = "UNAVAILABLE"
        f3 = f"Funding {fund_str}, Retail L/S {ls_str}"
        if not range_24h_available:
            f4 = "UNAVAILABLE (missing 24h range telemetry)"
        elif atr_comp is not None and atr_comp >= 25.0:
            f4 = f"Range compression ({atr_comp:.1f}% ATR compressed) with magnet asymmetry"
        else:
            f4 = "24h range structure measured (see 5-Regime Radar)"
        f5 = f"[{src_tag}] LOWER is {dist_l:.2f}% away vs UPPER {dist_u:.2f}% away"
        f6 = f"ATR compressed {atr_comp:.1f}% of 72h peak" if atr_comp is not None else "UNAVAILABLE (insufficient 1H ATR history)"

        return {
            "factor_1_size": f1,
            "factor_2_spot_leadership": f2,
            "factor_3_crowding_fuel": f3,
            "factor_4_regime_structure": f4,
            "factor_5_asymmetry": f5,
            "factor_6_atr_volatility": f6,
        }

    def _evaluate_lsce(
        self,
        spot_price: float,
        lower_magnet: BTCMagnetLevel,
        upper_magnet: BTCMagnetLevel,
        capitulation_wick_low: Optional[float],
        swing_low_4h: Optional[float],
        spot_cvd_ratio: Optional[float],
        bids_asks_depth_ratio: Optional[float],
        liqmap_source: str,
    ) -> Dict[str, Any]:
        """Liquidation Sweep Confirmation Engine (LSCE) 4-state machine (fail-closed)."""
        l_price = lower_magnet.price
        if spot_price <= 0.0 or l_price <= 0.0:
            return {
                "status": "UNTESTED",
                "cluster_tested": "UNAVAILABLE",
                "sweep_depth_pct": 0.0,
                "reclaim_level": 0.0,
                "spot_absorption": "UNAVAILABLE",
                "action_verdict": "Lower cluster or spot price UNAVAILABLE. Maintain 100% USDT cash.",
            }

        dist_pct = round((spot_price - l_price) / spot_price * 100.0, 2)
        cvd_str = f"{spot_cvd_ratio:.2f}" if spot_cvd_ratio is not None else "UNAVAILABLE"
        src_note = "" if liqmap_source in ("LIVE_EDGEORNOT", "CACHED_LIQMAP") else f" [{liqmap_source}]"

        # 1. Sweep and Reclaim Confirmed (fail-closed: requires live liqmap, wick, CVD, and depth)
        if (
            liqmap_source in ("LIVE_EDGEORNOT", "CACHED_LIQMAP")
            and capitulation_wick_low is not None
            and spot_cvd_ratio is not None
            and bids_asks_depth_ratio is not None
            and capitulation_wick_low <= l_price * 1.002
            and spot_price > l_price
            and spot_cvd_ratio >= 1.05
            and bids_asks_depth_ratio >= 0.50
        ):
            return {
                "status": "SWEEP_AND_RECLAIM_CONFIRMED",
                "cluster_tested": f"Lower Longs (${l_price:,.0f}){src_note}",
                "sweep_depth_pct": dist_pct,
                "reclaim_level": round(l_price, 2),
                "spot_absorption": f"Strong (CVD {cvd_str})",
                "action_verdict": f"Lower liquidation shelf (${l_price:,.0f}) swept and reclaimed with positive spot absorption.",
            }

        # 2. Active Sweep in Progress
        if abs(spot_price - l_price) / spot_price <= 0.0020 or (l_price * 0.990 <= spot_price < l_price):
            return {
                "status": "SWEEP_IN_PROGRESS",
                "cluster_tested": f"Lower Longs (${l_price:,.0f}){src_note}",
                "sweep_depth_pct": dist_pct,
                "reclaim_level": round(l_price, 2),
                "spot_absorption": f"Testing (CVD {cvd_str})",
                "action_verdict": f"Price is actively piercing the ${l_price:,.0f} liquidation shelf. Do NOT buy active liquidations.",
            }

        # 3. Sweep Failed Breakdown
        failed_depth = (
            swing_low_4h is not None
            and bids_asks_depth_ratio is not None
            and spot_price < swing_low_4h
            and bids_asks_depth_ratio < 0.35
        )
        if spot_price < l_price * 0.990 or failed_depth:
            reclaim_lvl = round(swing_low_4h, 2) if swing_low_4h is not None else round(l_price, 2)
            return {
                "status": "SWEEP_FAILED_BREAKDOWN",
                "cluster_tested": f"Lower Longs (${l_price:,.0f}){src_note}",
                "sweep_depth_pct": dist_pct,
                "reclaim_level": reclaim_lvl,
                "spot_absorption": "Collapsed",
                "action_verdict": f"Liquidation shelf at ${l_price:,.0f} failed to hold. Hold 100% USDT cash.",
            }

        # 4. Untested
        return {
            "status": "UNTESTED",
            "cluster_tested": f"Lower Longs (${l_price:,.0f}){src_note}",
            "sweep_depth_pct": dist_pct,
            "reclaim_level": round(l_price, 2),
            "spot_absorption": "Pending" if spot_cvd_ratio is not None else "Pending (CVD UNAVAILABLE)",
            "action_verdict": f"Lower pool (${l_price:,.0f}{src_note}) is {dist_pct:+.2f}% away and untested. Maintain cash reserve.",
        }

    def _evaluate_5_regimes(
        self,
        spot_price: float,
        spot_available: bool,
        daily_vwap: Optional[float],
        weekly_vwap: Optional[float],
        ema_20d: Optional[float],
        ema_50d: Optional[float],
        high_24h: float,
        low_24h: float,
        range_24h_available: bool,
        swing_high_4h: Optional[float],
        swing_low_4h: Optional[float],
        price_change_1h: Optional[float],
        price_change_24h: Optional[float],
        spot_cvd_ratio: Optional[float],
        spot_cvd_4h_btc: Optional[float],
        raw_funding: Optional[float],
        annual_funding_pct: Optional[float],
        oi_delta_1h: Optional[float],
        oi_delta_4h: Optional[float],
        oi_delta_24h: Optional[float],
        long_short_ratio: Optional[float],
        bids_asks_depth_ratio: Optional[float],
        futures_basis_annual: Optional[float],
        atr_compression_pct: Optional[float],
        upper_magnet: BTCMagnetLevel,
        lower_magnet: BTCMagnetLevel,
        liqmap_source: str,
        pull_direction: str,
        lsce: Dict[str, Any],
    ) -> Dict[str, Any]:
        """5-Regime Radar with Majority-Voting (>= 3 of 4 matches); missing inputs fail closed."""
        candidates: List[Dict[str, Any]] = []

        # --- CANDIDATE 1: CASCADE / FORCED DELEVERAGING (Priority 1) ---
        c_casc: List[str] = []
        c_casc_all: List[Tuple[str, bool]] = []
        if price_change_1h is None and price_change_24h is None:
            b1 = False
            c_casc_all.append(("Sharp price drop: UNAVAILABLE (no 1h/24h price change)", b1))
        else:
            b1 = (
                (price_change_1h is not None and price_change_1h <= -2.8)
                or (price_change_24h is not None and price_change_24h <= -6.0)
            )
            p1_s = f"{price_change_1h:+.2f}%" if price_change_1h is not None else "UNAVAILABLE"
            p24_s = f"{price_change_24h:+.2f}%" if price_change_24h is not None else "UNAVAILABLE"
            c_casc_all.append((f"Sharp price drop ({p1_s} 1h / {p24_s} 24h)", b1))
        if b1:
            c_casc.append(c_casc_all[-1][0])

        if oi_delta_1h is None and oi_delta_4h is None:
            b2 = False
            c_casc_all.append(("OI crashing: UNAVAILABLE (no OI velocity telemetry)", b2))
        else:
            b2 = (
                (oi_delta_1h is not None and oi_delta_1h <= -3.5)
                or (oi_delta_4h is not None and oi_delta_4h <= -7.0)
            )
            o1_s = f"{oi_delta_1h:+.1f}%" if oi_delta_1h is not None else "UNAVAILABLE"
            o4_s = f"{oi_delta_4h:+.1f}%" if oi_delta_4h is not None else "UNAVAILABLE"
            c_casc_all.append((f"OI crashing ({o1_s} 1h / {o4_s} 4h)", b2))
        if b2:
            c_casc.append(c_casc_all[-1][0])

        if raw_funding is None:
            b3 = False
            c_casc_all.append(("Funding deeply negative: UNAVAILABLE (no funding telemetry)", b3))
        else:
            b3 = raw_funding <= -0.020
            c_casc_all.append((f"Funding plunged deeply negative ({raw_funding:+.4f}%/8h)", b3))
        if b3:
            c_casc.append(c_casc_all[-1][0])

        if futures_basis_annual is None:
            b4 = False
            c_casc_all.append(("Basis compressed / backwardation (< +1.0%/yr): UNAVAILABLE", b4))
        else:
            b4 = futures_basis_annual < 1.0
            c_casc_all.append((f"Basis compressed / backwardation (< +1.0%/yr: {futures_basis_annual:+.1f}%)", b4))
        if b4:
            c_casc.append(c_casc_all[-1][0])

        candidates.append({
            "regime_id": "CASCADE_FORCED_DELEVERAGING",
            "regime_name": "Cascade / Forced Deleveraging",
            "regime_diagnosis": "Forced long unwind in progress",
            "priority": 1,
            "matches_count": len(c_casc),
            "matched": c_casc,
            "all_observations": c_casc_all,
            "sizing_factor": 0.0,
            "action": "Wait / Cash Only (0.0x)",
            "rotation": "Remain USDT",
            "entry_instruction": "Hold 100% cash. Wait for stabilization (OI flat, liquidations drop, local low reclaim).",
            "stop_rule": "Capitulation wick low - 1.0% (No active trade)",
            "is_conflicted": False,
        })

        # --- CANDIDATE 2: LEVERAGED / FRAGILE UPSIDE (Priority 2) ---
        c_lev: List[str] = []
        c_lev_all: List[Tuple[str, bool]] = []
        if price_change_24h is None or spot_cvd_ratio is None:
            b1 = False
            c_lev_all.append(("Price rising but Spot CVD lagging: UNAVAILABLE", b1))
        else:
            b1 = price_change_24h > 1.8 and spot_cvd_ratio <= 1.02
            c_lev_all.append((f"Price rising ({price_change_24h:+.2f}%) but Spot CVD lagging (Ratio {spot_cvd_ratio:.2f})", b1))
        if b1:
            c_lev.append(c_lev_all[-1][0])

        if oi_delta_4h is None and oi_delta_24h is None:
            b2 = False
            c_lev_all.append(("Perp OI surging: UNAVAILABLE (no OI telemetry)", b2))
        else:
            b2 = (
                (oi_delta_4h is not None and oi_delta_4h >= 4.0)
                or (oi_delta_24h is not None and oi_delta_24h >= 8.0)
            )
            o4_s = f"{oi_delta_4h:+.1f}% 4h" if oi_delta_4h is not None else "UNAVAILABLE 4h"
            o24_s = f"{oi_delta_24h:+.1f}% 24h" if oi_delta_24h is not None else "UNAVAILABLE 24h"
            c_lev_all.append((f"Perp OI surging rapidly ({o4_s} / {o24_s})", b2))
        if b2:
            c_lev.append(c_lev_all[-1][0])

        if raw_funding is None:
            b3 = False
            c_lev_all.append(("Funding rate overheated: UNAVAILABLE", b3))
        else:
            b3 = raw_funding >= 0.025
            c_lev_all.append((f"Funding rate overheated ({raw_funding:+.4f}%/8h)", b3))
        if b3:
            c_lev.append(c_lev_all[-1][0])

        if long_short_ratio is None:
            b4 = False
            c_lev_all.append(("Extreme retail long crowding: UNAVAILABLE", b4))
        else:
            b4 = long_short_ratio >= 2.1
            c_lev_all.append((f"Extreme retail long crowding (Ratio {long_short_ratio:.2f})", b4))
        if b4:
            c_lev.append(c_lev_all[-1][0])

        candidates.append({
            "regime_id": "LEVERAGED_FRAGILE_UPSIDE",
            "regime_name": "Leveraged / Fragile Upside",
            "regime_diagnosis": "Derivatives-driven rally without spot backing",
            "priority": 2,
            "matches_count": len(c_lev),
            "matched": c_lev,
            "all_observations": c_lev_all,
            "sizing_factor": 0.0,
            "action": "Trim to Cash (0.0x)",
            "rotation": "BTC -> USDT",
            "entry_instruction": "Harvest profits into USDT cash. Do NOT buy breakout without spot confirmation.",
            "stop_rule": "Tight trailing stop at 4H EMA21",
            "is_conflicted": False,
        })

        # --- CANDIDATE 3: DISTRIBUTION / BEAR CONTINUATION (Priority 3) ---
        c_dist: List[str] = []
        c_dist_all: List[Tuple[str, bool]] = []
        if not spot_available or daily_vwap is None or ema_20d is None or ema_50d is None:
            b1 = False
            c_dist_all.append(("Price below Daily VWAP, 20D EMA, and 50D EMA: UNAVAILABLE", b1))
        else:
            b1 = spot_price < daily_vwap and spot_price < ema_20d and spot_price < ema_50d
            c_dist_all.append(("Price below Daily VWAP, 20D EMA, and 50D EMA", b1))
        if b1:
            c_dist.append(c_dist_all[-1][0])

        if spot_cvd_4h_btc is None or spot_cvd_ratio is None:
            b2 = False
            c_dist_all.append(("Spot CVD persistently negative: UNAVAILABLE", b2))
        else:
            b2 = spot_cvd_4h_btc < -100.0 or spot_cvd_ratio <= 0.88
            c_dist_all.append((f"Spot CVD persistently negative (Delta {spot_cvd_4h_btc:+.1f} BTC / Ratio {spot_cvd_ratio:.2f})", b2))
        if b2:
            c_dist.append(c_dist_all[-1][0])

        if raw_funding is None and futures_basis_annual is None:
            b3 = False
            c_dist_all.append(("Trapped longs paying funding / compressed basis: UNAVAILABLE", b3))
        else:
            b3 = (
                (raw_funding is not None and raw_funding >= 0.005)
                or (futures_basis_annual is not None and futures_basis_annual < 4.0)
            )
            f_s = f"{raw_funding:+.4f}%/8h" if raw_funding is not None else "UNAVAILABLE"
            b_s = f"{futures_basis_annual:.1f}%" if futures_basis_annual is not None else "UNAVAILABLE"
            c_dist_all.append((f"Trapped longs paying funding ({f_s}) / compressed basis ({b_s})", b3))
        if b3:
            c_dist.append(c_dist_all[-1][0])

        if bids_asks_depth_ratio is None:
            b4 = False
            c_dist_all.append(("Order book bid depth thin (< 0.35): UNAVAILABLE", b4))
        else:
            b4 = bids_asks_depth_ratio < 0.35
            c_dist_all.append((f"Order book bid depth thin ({bids_asks_depth_ratio:.2f})", b4))
        if b4:
            c_dist.append(c_dist_all[-1][0])

        candidates.append({
            "regime_id": "DISTRIBUTION_BEAR_CONTINUATION",
            "regime_name": "Distribution / Bear Continuation",
            "regime_diagnosis": "Weak demand or active distribution",
            "priority": 3,
            "matches_count": len(c_dist),
            "matched": c_dist,
            "all_observations": c_dist_all,
            "sizing_factor": 0.0,
            "action": "Defensive Cash (0.0x)",
            "rotation": "Remain USDT",
            "entry_instruction": "Strict Cash (100% USDT). Treat bounces as exit liquidity. Only reverse on structure + Spot CVD reclaim.",
            "stop_rule": "Invalidation: 1D close > 50D EMA with positive Spot CVD",
            "is_conflicted": False,
        })

        # --- CANDIDATE 4: RANGE / LIQUIDATION MAGNET (Priority 4 - Core Operating Zone) ---
        c_rng: List[str] = []
        c_rng_all: List[Tuple[str, bool]] = []
        has_swing_range = swing_high_4h is not None and swing_low_4h is not None and spot_price > 0
        range_width_pct = ((swing_high_4h - swing_low_4h) / spot_price * 100.0) if has_swing_range else None
        if range_width_pct is None and atr_compression_pct is None:
            b1 = False
            c_rng_all.append(("Defined range (<= 5.2%) & ATR compressed (>= 25%): UNAVAILABLE", b1))
        else:
            b1 = (
                (range_width_pct is not None and range_width_pct <= 5.2)
                or (atr_compression_pct is not None and atr_compression_pct >= 25.0)
            )
            rw_s = f"{range_width_pct:.2f}% width" if range_width_pct is not None else "UNAVAILABLE"
            ac_s = f"{atr_compression_pct:.1f}%" if atr_compression_pct is not None else "UNAVAILABLE"
            c_rng_all.append((f"Defined range ({rw_s}) & ATR compressed ({ac_s})", b1))
        if b1:
            c_rng.append(c_rng_all[-1][0])

        if spot_cvd_ratio is None:
            b2 = False
            c_rng_all.append(("Spot CVD neutral/balanced (0.88 - 1.30): UNAVAILABLE", b2))
        else:
            b2 = 0.88 <= spot_cvd_ratio <= 1.30
            c_rng_all.append((f"Spot CVD neutral/balanced (Ratio {spot_cvd_ratio:.2f})", b2))
        if b2:
            c_rng.append(c_rng_all[-1][0])

        if long_short_ratio is None and raw_funding is None:
            b3 = False
            c_rng_all.append(("Positioning crowded / balanced funding: UNAVAILABLE", b3))
        else:
            b3 = (
                (long_short_ratio is not None and long_short_ratio >= 1.55)
                or (raw_funding is not None and abs(raw_funding) <= 0.020)
            )
            ls_s = f"{long_short_ratio:.2f}" if long_short_ratio is not None else "UNAVAILABLE"
            rf_s = f"{raw_funding:+.4f}%/8h" if raw_funding is not None else "UNAVAILABLE"
            c_rng_all.append((f"Positioning crowded (L/S {ls_s}, funding {rf_s})", b3))
        if b3:
            c_rng.append(c_rng_all[-1][0])

        liqmap_is_live = liqmap_source in ("LIVE_EDGEORNOT", "CACHED_LIQMAP")
        b4 = bool(
            liqmap_is_live
            and spot_available
            and upper_magnet.price > spot_price
            and 0.0 < lower_magnet.price < spot_price
            and upper_magnet.usd_volume >= 100_000_000
            and lower_magnet.usd_volume >= 100_000_000
        )
        if liqmap_is_live:
            c_rng_all.append(("Clear live liquidation clusters active above and below price", b4))
        else:
            c_rng_all.append((f"Clear live liquidation clusters active: UNAVAILABLE (source: {liqmap_source})", False))
        if b4:
            c_rng.append(c_rng_all[-1][0])

        # Action and Sizing governed strictly by LSCE state
        if lsce["status"] == "SWEEP_AND_RECLAIM_CONFIRMED":
            rng_sizing = 0.75
            rng_action = "Trade the Magnet: Buy Spot (0.75x)"
            rng_rotation = "USDT -> BTC"
            rng_entry = "Confirmed sweep & reclaim: 50% market spot / 50% limit at reclaimed range floor."
        elif lsce["status"] == "SWEEP_IN_PROGRESS":
            rng_sizing = 0.0
            rng_action = "Wait / Active Sweep in Progress (0.0x)"
            rng_rotation = "Remain USDT"
            rng_entry = "Active liquidation sweep underway. Do NOT front-run. Wait for 1H close reclaim above cluster."
        elif swing_high_4h is not None and range_24h_available and spot_price >= swing_high_4h * 0.990:
            rng_sizing = 0.0
            rng_action = "Range Resistance: Trim to Cash (0.0x)"
            rng_rotation = "BTC -> USDT"
            rng_entry = "Price testing range ceiling and lower magnet dominates. Harvest profit to USDT cash."
        else:
            rng_sizing = 0.50
            rng_action = "Range / Liquidation Magnet: Stand Aside or Selective (0.50x)"
            rng_rotation = "Remain USDT"
            rng_entry = "Price oscillating in range. Await liquidation sweep confirmation before full allocation."

        candidates.append({
            "regime_id": "RANGE_LIQUIDATION_MAGNET",
            "regime_name": "Range / Liquidation Magnet",
            "regime_diagnosis": "Positioning imbalance and forced liquidations dominate",
            "priority": 4,
            "matches_count": len(c_rng),
            "matched": c_rng,
            "all_observations": c_rng_all,
            "sizing_factor": rng_sizing,
            "action": rng_action,
            "rotation": rng_rotation,
            "entry_instruction": rng_entry,
            "stop_rule": "Disaster stop safely below 200D SMA and 25x liquidation shelf",
            "is_conflicted": False,
        })

        # --- CANDIDATE 5: SPOT-LED EXPANSION (Priority 5) ---
        c_spot: List[str] = []
        c_spot_all: List[Tuple[str, bool]] = []
        if not spot_available or daily_vwap is None or weekly_vwap is None:
            b1 = False
            c_spot_all.append(("Price holding above Daily and Weekly VWAP: UNAVAILABLE", b1))
        else:
            b1 = spot_price > daily_vwap and spot_price > weekly_vwap
            c_spot_all.append(("Price holding above Daily and Weekly VWAP", b1))
        if b1:
            c_spot.append(c_spot_all[-1][0])

        if spot_cvd_ratio is None or spot_cvd_4h_btc is None:
            b2 = False
            c_spot_all.append(("Spot CVD leading: UNAVAILABLE", b2))
        else:
            b2 = spot_cvd_ratio >= 1.10 and spot_cvd_4h_btc > 250.0
            c_spot_all.append((f"Spot CVD leading (Ratio {spot_cvd_ratio:.2f}, 4h Delta {spot_cvd_4h_btc:+.1f} BTC)", b2))
        if b2:
            c_spot.append(c_spot_all[-1][0])

        if raw_funding is None or oi_delta_24h is None:
            b3 = False
            c_spot_all.append(("Funding and OI controlled: UNAVAILABLE", b3))
        else:
            b3 = raw_funding <= 0.015 and oi_delta_24h <= 4.0
            c_spot_all.append((f"Funding and OI controlled (Funding {raw_funding:+.4f}%/8h, OI 24h {oi_delta_24h:+.1f}%)", b3))
        if b3:
            c_spot.append(c_spot_all[-1][0])

        if price_change_24h is None:
            b4 = False
            c_spot_all.append(("Price momentum positive (>= +2.0% 24h): UNAVAILABLE", b4))
        else:
            b4 = price_change_24h >= 2.0
            c_spot_all.append((f"Price momentum positive ({price_change_24h:+.2f}% 24h)", b4))
        if b4:
            c_spot.append(c_spot_all[-1][0])

        candidates.append({
            "regime_id": "SPOT_LED_EXPANSION",
            "regime_name": "Spot-Led Expansion",
            "regime_diagnosis": "Genuine spot demand leading higher",
            "priority": 5,
            "matches_count": len(c_spot),
            "matched": c_spot,
            "all_observations": c_spot_all,
            "sizing_factor": 1.0,
            "action": "Full Spot Long (0.75x - 1.0x)",
            "rotation": "USDT -> BTC",
            "entry_instruction": "Trend-following spot entry on pullbacks to Daily VWAP or 4H EMA21.",
            "stop_rule": "Trailing stop under 4H swing low",
            "is_conflicted": False,
        })

        # Filter candidates meeting majority threshold (>= 3 matches)
        valid = [c for c in candidates if c["matches_count"] >= 3]

        # Check for Conflicted Signals (only when required inputs are genuinely measured)
        is_conflicted = (
            spot_available
            and daily_vwap is not None
            and weekly_vwap is not None
            and futures_basis_annual is not None
            and bids_asks_depth_ratio is not None
            and spot_price < daily_vwap
            and spot_price < weekly_vwap
            and futures_basis_annual < 0.0
            and bids_asks_depth_ratio < 0.35
            and lsce["status"] != "SWEEP_AND_RECLAIM_CONFIRMED"
        )

        if is_conflicted and any(c["regime_id"] == "RANGE_LIQUIDATION_MAGNET" for c in valid):
            best = {
                "regime_id": "TRANSITION_MIXED",
                "regime_name": "Transition / Mixed",
                "regime_diagnosis": "Conflicted signals: positive Spot CVD countered by sub-VWAP price weakness and thin bids",
                "priority": 6,
                "matches_count": 2,
                "matched": ["Conflicted signals: sub-VWAP price weakness countered by thin bids and futures backwardation"],
                "all_observations": [
                    ("Sub-VWAP price weakness", True),
                    ("Futures backwardation (< 0%)", True),
                    ("Thin order book bid depth (< 0.35)", True),
                    ("Downside sweep reclaim confirmed", False),
                ],
                "sizing_factor": 0.0,
                "action": "Defensive / Stand Aside in Cash (0.0x)",
                "rotation": "Remain USDT",
                "entry_instruction": "Stand aside. Wait for price to reclaim Daily VWAP or complete confirmed liquidation sweep.",
                "stop_rule": "Disaster stop safely below 200D SMA",
                "is_conflicted": True,
                "conflict_reason": "Price trading below Daily & Weekly VWAP with negative basis and thin bids. Range fragile; capital preservation active.",
            }
        elif valid:
            valid.sort(key=lambda x: (x["priority"], -x["matches_count"]))
            best = valid[0]
        else:
            top_cand = max(candidates, key=lambda x: x["matches_count"])
            best = {
                "regime_id": "TRANSITION_MIXED",
                "regime_name": "Transition / Mixed",
                "regime_diagnosis": "No clean majority on-exchange positioning regime (signals mixed or unavailable)",
                "priority": 6,
                "matches_count": top_cand["matches_count"],
                "matched": top_cand["matched"],
                "all_observations": top_cand["all_observations"],
                "sizing_factor": 0.0,
                "action": "Wait / Cash (0.0x)",
                "rotation": "Remain USDT",
                "entry_instruction": "Wait for clear market regime majority confirmation.",
                "stop_rule": "Disaster stop safely below 200D SMA",
                "is_conflicted": False,
            }

        best["majority_score"] = f"{best['matches_count']}/4"
        return best

    def _get_liquidation_magnets(
        self,
        spot_price: float,
        store: Optional[StateStore] = None,
    ) -> Tuple[BTCMagnetLevel, BTCMagnetLevel]:
        """Fetches live liquidation clusters or falls back with explicit provenance labels."""
        if spot_price <= 0.0:
            self._last_liqmap_source = "UNAVAILABLE"
            self._last_liqmap_error = "Spot price UNAVAILABLE"
            return BTCMagnetLevel(source="UNAVAILABLE"), BTCMagnetLevel(source="UNAVAILABLE")

        now = time.time()
        data = self._cached_liq_data
        from_live_fetch = False

        if data is None or (now - self._last_fetch_ts) > self._cache_ttl_sec:
            self._last_fetch_ts = now
            fetched = self._fetch_live_liqmap()
            if fetched is not None:
                self._cached_liq_data = fetched
                data = fetched
                from_live_fetch = True
        else:
            # Either live cache within TTL or test-seeded _cached_liq_data
            from_live_fetch = self._last_liqmap_source == "LIVE_EDGEORNOT"

        if data and "levels" in data:
            lev = data["levels"]
            above = [l for l in lev.get("above", []) if l.get("price", 0) > spot_price]
            below = [l for l in lev.get("below", []) if l.get("price", 0) < spot_price]

            above.sort(key=lambda x: x.get("price", 0))
            below.sort(key=lambda x: x.get("price", 0), reverse=True)

            live_tag = "LIVE_EDGEORNOT" if from_live_fetch else "CACHED_LIQMAP"
            lvl_tag = "MEASURED_LIQMAP" if from_live_fetch else "CACHED_LIQMAP"

            if above:
                ab_px = float(above[0]["price"])
                ab_usd = float(above[0].get("usd", 0.0) or 0.0)
                ab_dist = ((ab_px - spot_price) / spot_price) * 100.0
                upper = BTCMagnetLevel(price=ab_px, dist_pct=ab_dist, usd_volume=ab_usd, source=lvl_tag)
            else:
                upper = BTCMagnetLevel(
                    price=round(spot_price * 1.034, 2),
                    dist_pct=3.4,
                    usd_volume=215_000_000,
                    source="MODELLED_FALLBACK",
                )

            if below:
                bl_px = float(below[0]["price"])
                bl_usd = float(below[0].get("usd", 0.0) or 0.0)
                bl_dist = ((bl_px - spot_price) / spot_price) * 100.0
                lower = BTCMagnetLevel(price=bl_px, dist_pct=bl_dist, usd_volume=bl_usd, source=lvl_tag)
            else:
                lower = BTCMagnetLevel(
                    price=round(spot_price * 0.982, 2),
                    dist_pct=-1.8,
                    usd_volume=350_000_000,
                    source="MODELLED_FALLBACK",
                )

            if above and below:
                self._last_liqmap_source = live_tag
            else:
                self._last_liqmap_source = "PARTIAL_LIQMAP_WITH_MODELLED"
            return upper, lower

        # Secondary Fallback: Structural Swing High / Low Liquidation Pools from StateStore
        if store is not None:
            ss_ev = getattr(store, "spot_swing_evaluation", None)
            mp = getattr(ss_ev, "magnet_protocol", None) if ss_ev is not None else None
            if mp is not None and mp.short_liq_magnet > spot_price and 0 < mp.long_liq_magnet < spot_price:
                up_px = float(mp.short_liq_magnet)
                lo_px = float(mp.long_liq_magnet)
                up_dist = ((up_px - spot_price) / spot_price) * 100.0
                lo_dist = ((lo_px - spot_price) / spot_price) * 100.0
                oi_usd = float(getattr(store, "open_interest_usd", 0.0) or 0.0)
                up_vol = max(150_000_000.0, oi_usd * 0.035) if oi_usd > 0 else 215_500_000.0
                lo_vol = max(180_000_000.0, oi_usd * 0.042) if oi_usd > 0 else 354_200_000.0
                self._last_liqmap_source = "ESTIMATED_SWING_POOL"
                return (
                    BTCMagnetLevel(price=round(up_px, 2), dist_pct=round(up_dist, 2), usd_volume=up_vol, source="ESTIMATED_SWING_POOL"),
                    BTCMagnetLevel(price=round(lo_px, 2), dist_pct=round(lo_dist, 2), usd_volume=lo_vol, source="ESTIMATED_SWING_POOL"),
                )

        # Tertiary Fallback: Modeled liquidation bands around current Bitcoin spot price
        self._last_liqmap_source = "MODELLED_FALLBACK"
        upper = BTCMagnetLevel(
            price=round(spot_price * 1.0337, 2),
            dist_pct=3.37,
            usd_volume=215_500_000,
            source="MODELLED_FALLBACK",
        )
        lower = BTCMagnetLevel(
            price=round(spot_price * 0.9823, 2),
            dist_pct=-1.77,
            usd_volume=354_200_000,
            source="MODELLED_FALLBACK",
        )
        return upper, lower

    def _fetch_live_liqmap(self) -> Optional[Dict[str, Any]]:
        """Queries edgeornot.com public liquidation map with a tight timeout and logs errors."""
        url = "https://edgeornot.com/api/liqmap/btc?days=1&ex=all"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "BTCMagnetEngine/1.0"})
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                if resp.status == 200:
                    raw = resp.read()
                    parsed = json.loads(raw.decode("utf-8"))
                    self._last_liqmap_error = ""
                    self._last_liqmap_source = "LIVE_EDGEORNOT"
                    return parsed
                self._last_liqmap_error = f"HTTP {resp.status}"
                logger.warning("edgeornot.com liqmap returned non-200 status: %s", resp.status)
        except Exception as exc:
            self._last_liqmap_error = f"{type(exc).__name__}: {exc}"
            logger.warning("Failed to fetch live liqmap from %s: %s", url, self._last_liqmap_error)
        return None

    def _evaluate_speaking_rules(
        self,
        spot_price: float,
        spot_available: bool,
        price_change_24h: Optional[float],
        upper: BTCMagnetLevel,
        lower: BTCMagnetLevel,
        liqmap_is_live: bool,
        liqmap_source: str,
        pull_direction: str,
        up_weight: float,
        lo_weight: float,
        funding_annual_pct: Optional[float],
        oi_delta_4h: Optional[float],
        spot_cvd_4h_btc: Optional[float],
        regime: str,
    ) -> Tuple[List[BTCMagnetRuleCheck], str, str, str, str]:
        """Evaluates the 7 strict conditions; all missing telemetry fails closed."""
        upper_valid = liqmap_is_live and 0.8 <= upper.dist_pct <= 4.5 and upper.usd_volume >= 100_000_000
        lower_valid = liqmap_is_live and -4.5 <= lower.dist_pct <= -0.8 and lower.usd_volume >= 100_000_000
        cond1 = upper_valid or lower_valid

        if upper_valid and lower_valid:
            if pull_direction == "UPPER":
                target_side = "ABOVE"
            elif pull_direction == "LOWER":
                target_side = "BELOW"
            else:
                target_side = "ABOVE" if up_weight >= lo_weight else "BELOW"
        elif upper_valid:
            target_side = "ABOVE"
        elif lower_valid:
            target_side = "BELOW"
        else:
            target_side = "NONE"

        target_magnet = upper if target_side == "ABOVE" else lower

        r1 = BTCMagnetRuleCheck(
            rule_num=1,
            name="Clear Magnet Present",
            passed=cond1,
            detail=(
                f"Magnet {target_side}: ${target_magnet.price:,.0f} ({target_magnet.dist_pct:+.1f}%, ${target_magnet.usd_volume/1e6:.0f}M)"
                if cond1
                else (
                    f"Live liquidation map UNAVAILABLE (source: {liqmap_source})"
                    if not liqmap_is_live
                    else "No dense liquidation cluster within 0.8%-4.5% reach (>= $100M)"
                )
            ),
        )

        if oi_delta_4h is None:
            cond2 = False
            r2_detail = "OI velocity UNAVAILABLE (no OI telemetry)"
        else:
            cond2 = oi_delta_4h >= -0.5
            r2_detail = f"OI velocity supportive ({oi_delta_4h:+.1f}% 4h delta)" if cond2 else f"OI unsupportive ({oi_delta_4h:+.1f}% 4h delta)"
        r2 = BTCMagnetRuleCheck(
            rule_num=2,
            name="Open-Interest Confirmation",
            passed=cond2,
            detail=r2_detail,
        )

        if funding_annual_pct is None:
            cond3 = False
            r3_detail = "Funding carry UNAVAILABLE (no funding telemetry)"
        else:
            cond3 = -10.0 <= funding_annual_pct <= 28.0
            r3_detail = (
                f"Perpetual funding calm ({funding_annual_pct:+.1f}%/yr carry)"
                if cond3
                else f"Funding contradictory or extreme ({funding_annual_pct:+.1f}%/yr)"
            )
        r3 = BTCMagnetRuleCheck(
            rule_num=3,
            name="Funding Non-Contradictory",
            passed=cond3,
            detail=r3_detail,
        )

        cond4 = False
        if regime == "Range" and target_side != "NONE":
            cond4 = True
        elif regime == "Range" and target_side == "NONE" and liqmap_is_live:
            cond4 = True
        elif regime == "TrendUp" and target_side == "ABOVE":
            cond4 = True
        elif regime == "TrendDown" and target_side == "BELOW":
            cond4 = True

        r4 = BTCMagnetRuleCheck(
            rule_num=4,
            name="Regime Conduciveness",
            passed=cond4,
            detail=(
                "Market regime UNAVAILABLE (missing 24h range telemetry)"
                if regime == "UNAVAILABLE"
                else (
                    f"Market in {regime} mode (conducive to magnet sweep)"
                    if cond4
                    else f"Market regime ({regime}) opposes magnet sweep"
                )
            ),
        )

        if price_change_24h is None or spot_cvd_4h_btc is None:
            cond5 = False
            missing_parts = []
            if price_change_24h is None:
                missing_parts.append("24h price change")
            if spot_cvd_4h_btc is None:
                missing_parts.append("4h Spot CVD")
            r5_detail = f"Structure/flow UNAVAILABLE (missing {', '.join(missing_parts)})"
        else:
            opposing_flow = (
                (target_side == "ABOVE" and spot_cvd_4h_btc < -350.0)
                or (target_side == "BELOW" and spot_cvd_4h_btc > 500.0 and price_change_24h > 3.5)
            )
            cond5 = abs(price_change_24h) < 6.5 and not opposing_flow
            flow_tag = f", 4h Spot CVD: {spot_cvd_4h_btc:+.1f} BTC"
            r5_detail = (
                f"Structure intact (24h change: {price_change_24h:+.2f}%{flow_tag})"
                if cond5
                else f"Opposing momentum/flow (24h change: {price_change_24h:+.2f}%{flow_tag})"
            )
        r5 = BTCMagnetRuleCheck(
            rule_num=5,
            name="Spot Flow & Structure Alignment",
            passed=cond5,
            detail=r5_detail,
        )

        cond6 = spot_available and (
            (target_side == "ABOVE" and upper.price > spot_price)
            or (target_side == "BELOW" and lower.price < spot_price)
        )
        r6 = BTCMagnetRuleCheck(
            rule_num=6,
            name="Not Already Swept",
            passed=cond6,
            detail="Target cluster intact and unswept" if cond6 else "Cluster unavailable, already breached, or expired",
        )

        passed_sub = sum(1 for c in (cond1, cond2, cond3, cond4, cond5, cond6) if c)
        cond7 = passed_sub >= 5 and cond1 and cond4 and cond5 and cond6
        r7 = BTCMagnetRuleCheck(
            rule_num=7,
            name="Conviction Threshold",
            passed=cond7,
            detail=f"{passed_sub}/6 internal filters passed cleanly" if cond7 else f"Conditions incomplete ({passed_sub}/6 passed). Default: WAIT.",
        )

        rule_checks = [r1, r2, r3, r4, r5, r6, r7]

        is_exhaustion = cond1 and cond6 and (not cond3) and (not cond2) and oi_delta_4h is not None and funding_annual_pct is not None

        if cond7 and target_side == "ABOVE" and regime == "Range":
            verdict = "SPEAK"
            headline = f"Strong magnet above at ${upper.price:,.0f}."
            body = f"Short liquidations clustered (${upper.usd_volume/1e6:.0f}M), Range regime. Spot flow supportive. Watch for sweep."
            rule_subtitle = f"Locked Pattern: Range Regime | Magnet Above ({upper.dist_pct:+.1f}%)"
        elif cond7 and target_side == "BELOW" and regime == "Range":
            verdict = "SPEAK"
            headline = f"Strong magnet below at ${lower.price:,.0f}."
            body = f"Long liquidations clustered (${lower.usd_volume/1e6:.0f}M), Range regime. Spot flow supportive. Watch for sweep."
            rule_subtitle = f"Locked Pattern: Range Regime | Magnet Below ({lower.dist_pct:+.1f}%)"
        elif cond7 and (regime in ("TrendUp", "TrendDown")):
            verdict = "SPEAK"
            headline = f"Magnet at ${target_magnet.price:,.0f} aligns with trend."
            body = "OI and funding confirm. Structure supportive. Edge present - monitor for entry zone."
            rule_subtitle = f"Locked Pattern: Trend-Aligned Acceleration ({regime})"
        elif is_exhaustion:
            verdict = "WAIT"
            headline = f"Dense magnet at ${target_magnet.price:,.0f} with extreme funding and declining OI."
            body = "Possible exhaustion. High caution - wait for confirmation."
            rule_subtitle = "Locked Pattern: Exhaustion Regime (Extreme Funding + Declining OI)"
        else:
            verdict = "WAIT"
            headline = "No clear edge - wait."
            if cond1:
                body = f"Magnet present at ${target_magnet.price:,.0f} but conditions incomplete. No clear edge - wait."
            else:
                body = "Liquidation density dispersed or live map unavailable. No high-probability gravitational pull. Default to cash."
            rule_subtitle = "Locked Principle: The engine spends most days correctly saying 'wait.'"

        return rule_checks, verdict, headline, body, rule_subtitle

    def _build_markdown_brief(self, ev: BTCMagnetEvaluation) -> str:
        """Constructs shareable clipboard text and AI packet section from finalized evaluation."""
        spot_s = f"${ev.spot_price:,.2f}" if ev.spot_available and ev.spot_price > 0 else "UNAVAILABLE"
        chg_s = f"{ev.price_change_24h_pct:+.2f}% 24h" if ev.price_change_24h_available else "UNAVAILABLE 24h"
        fund_s = f"{ev.funding_rate_annual_pct:+.1f}%/yr" if ev.funding_available else "UNAVAILABLE"
        oi_s = f"{ev.oi_delta_4h_pct:+.1f}%" if ev.oi_available else "UNAVAILABLE"

        prov_counts: Dict[str, int] = {"MEASURED": 0, "DERIVED": 0, "MODELLED/EST": 0, "UNAVAILABLE": 0}
        for val in (ev.input_provenance or {}).values():
            if val.startswith("MEASURED") or val in ("LIVE_EDGEORNOT", "CACHED_LIQMAP"):
                prov_counts["MEASURED"] += 1
            elif val.startswith("DERIVED"):
                prov_counts["DERIVED"] += 1
            elif "MODELLED" in val or "ESTIMATED" in val:
                prov_counts["MODELLED/EST"] += 1
            else:
                prov_counts["UNAVAILABLE"] += 1

        lines = [
            "# BTC MAGNET | LIQUIDATION GRAVITATIONAL RADAR REPORT",
            f"**Timestamp:** `{ev.timestamp_utc}`  |  **Origin:** `{ev.evaluation_origin}`",
            f"**Spot Price:** `{spot_s}` (`{chg_s}`)  |  **Regime:** `{ev.regime_name}`",
            f"**Perpetual Funding:** `{fund_s}`  |  **4h OI Velocity:** `{oi_s}`",
            (
                f"**Data Provenance:** `LiqMap={ev.liqmap_source}` | "
                f"`Measured={prov_counts['MEASURED']}` `Derived={prov_counts['DERIVED']}` "
                f"`Modelled/Est={prov_counts['MODELLED/EST']}` `Unavailable={prov_counts['UNAVAILABLE']}`"
            ),
        ]
        if ev.liqmap_error:
            lines.append(f"**LiqMap Fallback Reason:** `{ev.liqmap_error}`")

        lines.extend([
            "",
            "## 1. STEP 1 - 5-REGIME RADAR DIAGNOSIS (MAJORITY VOTING)",
            f"- **Active Market Regime:** `{ev.regime_name}` ({ev.majority_score} observations confirmed)",
            f"- **Diagnosis:** {ev.regime_diagnosis}",
            "- **Verified On-Exchange Positioning Observations:**",
        ])
        for obs, passed in ev.all_observations:
            mark = "[[TRUE]] PASS" if passed else "[[FALSE]] FAIL"
            lines.append(f"  * `{mark}`: {obs}")
        if ev.is_conflicted:
            lines.append(f"- **Conflicted Reason:** {ev.conflict_reason}")

        up_s = (
            f"`${ev.upper_magnet.price:,.0f}` (`{ev.upper_magnet.dist_pct:+.1f}%` / `+${ev.upper_magnet.price - ev.spot_price:,.0f}`) - `${ev.upper_magnet.usd_volume/1e6:.1f}M` [{ev.upper_magnet.source}]"
            if ev.upper_magnet.price > 0 and ev.spot_price > 0
            else "`UNAVAILABLE`"
        )
        lo_s = (
            f"`${ev.lower_magnet.price:,.0f}` (`{ev.lower_magnet.dist_pct:+.1f}%` / `-${ev.spot_price - ev.lower_magnet.price:,.0f}`) - `${ev.lower_magnet.usd_volume/1e6:.1f}M` [{ev.lower_magnet.source}]"
            if ev.lower_magnet.price > 0 and ev.spot_price > 0
            else "`UNAVAILABLE`"
        )

        lines.extend([
            "",
            "## 2. STEP 2 - LIQUIDATION GRAVITATIONAL HORIZON & DUAL-LADDER DEPTH",
            f"- **Upper Magnet (Short Liquidations):** {up_s}",
            f"- **Center Spot Horizon:** `{spot_s}`",
            f"- **Lower Support (Long Liquidations):** {lo_s}",
            f"- **Dominant Pull:** `{ev.pull_direction}` | Immediate 100x Skew: `{ev.immediate_ratio:.1f}x` | Total Ladder (10x-100x, MODELLED): `{ev.total_ladder_ratio:.2f}x`",
            "",
            "## 3. STEP 3 - LIQUIDATION SWEEP CONFIRMATION ENGINE (LSCE)",
            f"- **LSCE State:** `[{ev.lsce_status}]`",
            f"- **Cluster Tested:** `{ev.lsce_cluster_tested}`",
            f"- **Sweep Depth:** `{ev.lsce_sweep_depth_pct:+.2f}%` | **Reclaim Level:** `${ev.lsce_reclaim_level:,.2f}`",
            f"- **Spot Absorption Readout:** `{ev.lsce_spot_absorption}`",
            f"- **LSCE Readout:** {ev.lsce_action_verdict}",
            "",
            "## 4. STEP 4 - CAPITAL SIZING & INVIOLABLE RISK DIRECTIVES (SPOT ONLY, CAP <= 1.00x)",
            f"- **Recommended Spot Sizing:** `{ev.sizing_factor:.2f}x` ({ev.action})",
            f"- **Capital Rotation:** `{ev.rotation}`",
        ])
        if ev.verdict == "SPEAK" and ev.reconciliation_auth != "DENIED":
            lines.append(f"- **Entry Instruction:** {ev.entry_instruction}")
        else:
            lines.append(f"- **Entry Instruction:** NO ENTRY DIRECTIVE (Verdict: {ev.verdict})")

        if ev.disaster_stop_price > 0:
            sma_note = "200D SMA & shelf" if ev.ma_200d_available else "swing/liq shelf; 200D SMA UNAVAILABLE"
            lines.append(f"- **Disaster Hard Stop:** `${ev.disaster_stop_price:,.2f}` (`{ev.disaster_stop_dist_pct:.2f}%` from spot, {sma_note})")
        else:
            lines.append("- **Disaster Hard Stop:** `UNAVAILABLE`")
        lines.append(
            f"- **Risk Budget Compliance (<= {RISK_BUDGET_MAX_PCT}%):** `{'PASS' if ev.risk_budget_pass else 'FAIL'}`"
        )

        lines.extend([
            "",
            f"## 5. MECHANICAL VERDICT: [{ev.verdict}]",
            f"**Status Headline:** {ev.headline}",
            f"**Terminal Readout:** {ev.body}",
            f"*{ev.rule_subtitle}*",
            "",
            "## 6. 7 INTERNAL SPEAKING RULES AUDIT",
        ])

        for r in ev.rule_checks:
            badge = "[OK]" if r.passed else "[X]"
            lines.append(f"- **Rule {r.rule_num} ({r.name}):** `{badge}` {r.detail}")

        lines.extend([
            "",
            "---",
            "*Source: BTC Magnet Engine (Institutional 5-Regime Radar & LSCE | Spot-Only)*",
        ])
        return "\n".join(lines)


def copy_btc_magnet_card_to_clipboard(store: StateStore, *, recompute: bool = False) -> Tuple[bool, str, int]:
    """Copies BTC Magnet DATA-ONLY report to clipboard and writes to logs/btc_magnet_latest.md."""
    from analytics.data_only_reports import build_tab_m_data_only_report, copy_text_to_clipboard_and_log

    text = build_tab_m_data_only_report(None, store, recompute=recompute)
    copied, log_path, char_count = copy_text_to_clipboard_and_log(text, "btc_magnet_latest.md", store)
    if copied:
        return True, f"BTC Magnet DATA-ONLY report copied to clipboard ({char_count:,} chars)", char_count
    return False, f"Saved BTC Magnet DATA-ONLY report to {log_path} ({char_count:,} chars)", char_count
