"""Four-Gate Quantitative Protocol Engine (Tab 19 / [Q]).

Classification:
- Non-Lagging 4H BTC Spot Swing Radar (Long/Flat, Zero Leverage, Zero Shorting)
- 4 Primary Public REST Feeds (Zero Vendor-Dependent On-Chain Heuristics)
- 4 Deterministic Mathematical Gates (Rough Path Lévy Signed Area, Z-Score CVD Spread,
  30D Executed Volume Profile, 90D Funding Rate Percentile)
- 0.75% Equity Loss Safety Shield & DVOL Forward-Implied Volatility Sizing Cap
- In-Sample 90-Day Event Study & Expectancy Validation
"""

from __future__ import annotations

import json
import logging
import math
import os
import pathlib
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import numpy as np

from config.settings import EngineConfig
from core.models import FourGateEvaluation

logger = logging.getLogger("four_gate_engine")

BASE_DIR = pathlib.Path(__file__).resolve().parent.parent


class FourGateEngine:
    """Computes the 4-Gate Quantitative Protocol metrics, sizing ticket, and event study."""

    def __init__(self, config: Optional[EngineConfig] = None) -> None:
        self.config = config
        self._last_fetch_ts: float = 0.0
        self._cache_duration_sec: float = 25.0  # Throttle REST calls to avoid 429
        self._cached_eval: Optional[FourGateEvaluation] = None

    def fetch_primary_feeds(
        self, timeout_sec: float = 6.0
    ) -> Tuple[Optional[List[Any]], Optional[List[Any]], Optional[List[Any]], Optional[float]]:
        """Pulls the 4 public REST endpoints directly from primary exchanges.
        
        Returns:
            (spot_klines, perp_klines, funding_prints, dvol_current) or None on failure.
        """
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) BTC-4Gate/1.0"}

        # 1. Binance Spot 4H Klines (limit=780: 180 warmup + 540 90D eval + 60 forward horizon)
        spot_url = "https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=4h&limit=780"
        spot_klines: Optional[List[Any]] = None
        try:
            req = urllib.request.Request(spot_url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
                if resp.status == 200:
                    spot_klines = json.loads(resp.read().decode("utf-8"))
        except Exception as exc:
            logger.warning("Failed fetching Binance Spot 4H: %s", exc)
            return None, None, None, None

        # 2. Binance USD-M Perp 4H Klines (limit=780)
        perp_url = "https://fapi.binance.com/fapi/v1/klines?symbol=BTCUSDT&interval=4h&limit=780"
        perp_klines: Optional[List[Any]] = None
        try:
            req = urllib.request.Request(perp_url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
                if resp.status == 200:
                    perp_klines = json.loads(resp.read().decode("utf-8"))
        except Exception as exc:
            logger.warning("Failed fetching Binance Perp 4H: %s", exc)
            return None, None, None, None

        # 3. Binance Perp Funding History (paginated: 500 + 100 to get ~600 prints / 200 days)
        fund_url = "https://fapi.binance.com/fapi/v1/fundingRate?symbol=BTCUSDT&limit=500"
        funding_prints: Optional[List[Any]] = None
        try:
            req = urllib.request.Request(fund_url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
                if resp.status == 200:
                    p1 = json.loads(resp.read().decode("utf-8"))
                    funding_prints = p1
                    if p1 and len(p1) > 0:
                        t0 = p1[0]["fundingTime"]
                        fund_url2 = f"https://fapi.binance.com/fapi/v1/fundingRate?symbol=BTCUSDT&limit=100&endTime={t0 - 1}"
                        try:
                            req2 = urllib.request.Request(fund_url2, headers=headers)
                            with urllib.request.urlopen(req2, timeout=timeout_sec) as resp2:
                                if resp2.status == 200:
                                    p2 = json.loads(resp2.read().decode("utf-8"))
                                    funding_prints = p2 + p1
                        except Exception:
                            pass
        except Exception as exc:
            logger.warning("Failed fetching Binance Funding Rate: %s", exc)
            return None, None, None, None

        # 4. Deribit BTC DVOL Index Data
        now_ms = int(time.time() * 1000)
        start_ms = now_ms - (3 * 86400 * 1000)
        dvol_url = (
            f"https://www.deribit.com/api/v2/public/get_volatility_index_data"
            f"?currency=BTC&resolution=3600&start_timestamp={start_ms}&end_timestamp={now_ms}"
        )
        dvol_current: Optional[float] = None
        try:
            req = urllib.request.Request(dvol_url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    cand = data.get("result", {}).get("data", [])
                    if cand and len(cand[-1]) >= 5:
                        dvol_current = float(cand[-1][4])
        except Exception as exc:
            logger.warning("Failed fetching Deribit DVOL: %s", exc)
            # If DVOL fails, we fail-closed per zero-hallucination directive
            return None, None, None, None

        if not spot_klines or not perp_klines or not funding_prints or dvol_current is None:
            return None, None, None, None

        return spot_klines, perp_klines, funding_prints, dvol_current

    def calculate_evaluation(
        self,
        spot_raw: List[Any],
        perp_raw: List[Any],
        funding_raw: List[Any],
        dvol_current: float,
        equity_usd: float = 100000.0,
    ) -> FourGateEvaluation:
        """Runs the deterministic 4-Gate calculation and 90-day event study."""
        now_utc = datetime.now(timezone.utc)
        live_spot_px = float(spot_raw[-1][4]) if spot_raw and len(spot_raw[-1]) >= 5 else 0.0

        # Audit Fix 1: Lock Signal Evaluation strictly to CLOSED 4H Bars (klines[:-1])
        # Binance klines return the incomplete open candle as the last element [-1]
        if spot_raw and len(spot_raw) > 1:
            spot_bars = spot_raw[:-1]
            perp_bars = perp_raw[:-1]
        else:
            spot_bars = spot_raw
            perp_bars = perp_raw

        N = min(len(spot_bars), len(perp_bars))
        if N < 186:
            ev = FourGateEvaluation(
                timestamp_utc=now_utc.strftime("%Y-%m-%d %H:%M:%S UTC"),
                status="HALT: DATA UNAVAILABLE",
                verdict="HALT: DATA UNAVAILABLE",
                score=0,
                live_spot_price=live_spot_px,
                raw_data_available=False,
                error_message=f"Insufficient closed bars: {N} < 186 required.",
            )
            return ev

        spot_bars = spot_bars[-N:]
        perp_bars = perp_bars[-N:]

        # Verify timestamp alignment
        spot_ts = [b[0] for b in spot_bars]
        perp_ts = [b[0] for b in perp_bars]
        if spot_ts[-1] != perp_ts[-1]:
            ev = FourGateEvaluation(
                timestamp_utc=now_utc.strftime("%Y-%m-%d %H:%M:%S UTC"),
                status="HALT: DATA UNAVAILABLE",
                verdict="HALT: DATA UNAVAILABLE",
                score=0,
                live_spot_price=live_spot_px,
                raw_data_available=False,
                error_message="Spot and Perp 4H timestamp alignment failed.",
            )
            return ev

        last_closed_bar_utc = datetime.fromtimestamp(
            spot_ts[-1] / 1000, tz=timezone.utc
        ).strftime("%Y-%m-%d %H:00:00 UTC")

        closes = np.array([float(b[4]) for b in spot_bars])
        highs = np.array([float(b[2]) for b in spot_bars])
        lows = np.array([float(b[3]) for b in spot_bars])
        s_vols = np.array([float(b[5]) for b in spot_bars])
        s_buys = np.array([float(b[9]) for b in spot_bars])
        p_vols = np.array([float(b[5]) for b in perp_bars])
        p_buys = np.array([float(b[9]) for b in perp_bars])
        open_times = np.array([b[0] for b in spot_bars])

        # Pre-computation: Bar Deltas
        dS = (2.0 * s_buys) - s_vols
        dF = (2.0 * p_buys) - p_vols

        # -------------------------------------------------------------
        # GATE 1: Rough Path Signature Engine (Lévy Signed Area A_SP)
        # Window: latest 6 closed 4H bars (24H), 7-point paths starting at 0
        # -------------------------------------------------------------
        C_S = np.zeros(7)
        C_S[1:] = np.cumsum(dS[-6:])
        L_P = np.zeros(7)
        L_P[1:] = np.log(closes[-6:] / closes[-7])

        std_CS = np.std(C_S)
        std_LP = np.std(L_P)
        X = C_S / (std_CS if std_CS > 1e-9 else 1.0)
        Y = L_P / (std_LP if std_LP > 1e-9 else 1.0)

        A_SP = 0.5 * sum(X[j - 1] * (Y[j] - Y[j - 1]) - Y[j - 1] * (X[j] - X[j - 1]) for j in range(1, 7))
        gate_1_pass = bool(A_SP > 0.0)
        gate_1_details = (
            f"A_SP={A_SP:+.4f} > 0.0 (Spot accumulation leads price markup)"
            if gate_1_pass
            else f"A_SP={A_SP:+.4f} <= 0.0 (Spot path lagging or drag)"
        )

        # -------------------------------------------------------------
        # GATE 2: Spot vs Perp CVD Z-Score Divergence (D_flow)
        # Window: 24H rolling sums over trailing 180 bars (30 days baseline)
        # -------------------------------------------------------------
        dS_24h = np.array([np.sum(dS[i - 5 : i + 1]) for i in range(N - 180, N)])
        dF_24h = np.array([np.sum(dF[i - 5 : i + 1]) for i in range(N - 180, N)])

        std_ds = np.std(dS_24h)
        std_df = np.std(dF_24h)
        z_S = (dS_24h[-1] - np.mean(dS_24h)) / (std_ds if std_ds > 1e-9 else 1.0)
        z_F = (dF_24h[-1] - np.mean(dF_24h)) / (std_df if std_df > 1e-9 else 1.0)
        D_flow = z_S - z_F
        last_ds_24h = float(dS_24h[-1])

        gate_2_pass = bool(D_flow >= 1.0 and last_ds_24h > 0)
        gate_2_details = (
            f"D_flow={D_flow:+.2f} >= +1.0 & 24h Spot CVD={last_ds_24h:+,.1f} > 0"
            if gate_2_pass
            else f"D_flow={D_flow:+.2f} (z_S={z_S:+.2f}, z_F={z_F:+.2f}, Spot24h={last_ds_24h:+,.1f})"
        )

        # -------------------------------------------------------------
        # GATE 3: 30-Day Executed Volume Profile Structure
        # Trailing 180 4H bars partitioned into 50 equal price bins
        # -------------------------------------------------------------
        w_h = highs[-180:]
        w_l = lows[-180:]
        w_c = closes[-180:]
        w_v = s_vols[-180:]

        p_min, p_max = float(np.min(w_l)), float(np.max(w_h))
        bins = np.linspace(p_min, p_max, 51)
        vol_bins = np.zeros(50)
        tp_arr = (w_h + w_l + w_c) / 3.0

        for tp, v in zip(tp_arr, w_v):
            b_idx = int((tp - p_min) / (p_max - p_min + 1e-9) * 50)
            b_idx = min(49, max(0, b_idx))
            vol_bins[b_idx] += v

        poc_idx = int(np.argmax(vol_bins))
        poc_30 = float((bins[poc_idx] + bins[poc_idx + 1]) / 2.0)

        cum_vol = np.cumsum(vol_bins)
        tot_vol = cum_vol[-1]
        val_idx = int(np.searchsorted(cum_vol, tot_vol * 0.15))
        val_30 = float((bins[val_idx] + bins[min(49, val_idx + 1)]) / 2.0)
        vah_idx = int(np.searchsorted(cum_vol, tot_vol * 0.85))
        vah_30 = float((bins[vah_idx] + bins[min(49, vah_idx + 1)]) / 2.0)

        l_20 = float(np.min(lows[-121:-1]))

        state_a = bool((lows[-1] < l_20 and closes[-1] > l_20) or (lows[-1] < val_30 and closes[-1] > val_30))
        state_b = bool((closes[-1] > poc_30) and (abs(lows[-1] - poc_30) / poc_30 <= 0.005) and (closes[-2] > poc_30))
        gate_3_pass = state_a or state_b
        active_state = "STATE_A" if state_a else ("STATE_B" if state_b else "NONE")

        if state_a:
            gate_3_details = f"State A (Sweep Reclaim): Swept Low (${lows[-1]:,.1f} < L20/VAL) Reclaimed (${closes[-1]:,.1f})"
        elif state_b:
            gate_3_details = f"State B (POC Node Hold): Price tested within 0.5% of POC (${poc_30:,.1f}) and closed above"
        else:
            gate_3_details = f"No Structural Trigger: POC=${poc_30:,.1f}, VAL=${val_30:,.1f}, L20=${l_20:,.1f}"

        # -------------------------------------------------------------
        # Audit Fix 3: GATE 4 - Context-Aware Positioning & Anti-Crowding Filter
        # Trailing 270 funding prints (90 days)
        # -------------------------------------------------------------
        rates = [float(f["fundingRate"]) for f in funding_raw]
        curr_funding = float(rates[-1]) if rates else 0.0
        recent_rates = rates[-270:] if len(rates) >= 270 else rates
        p90_f = (sum(r < curr_funding for r in recent_rates) / len(recent_rates)) * 100.0 if recent_rates else 50.0

        is_sweep_zone = (active_state == "STATE_A") or (active_state == "NONE" and closes[-1] < val_30)

        if is_sweep_zone:
            gate_4_pass = bool(curr_funding <= 0.0 or p90_f < 25.0)
            zone_desc = "State A (Sweep Reclaim)" if active_state == "STATE_A" else f"Below VAL_30 (${val_30:,.1f}) [Sweep Zone]"
            gate_4_details = f"{zone_desc}: Funding={curr_funding * 100:+.4f}%, Rank={p90_f:.1f}% (<25.0% or negative required)"
        else:
            gate_4_pass = bool(p90_f <= 75.0)
            zone_desc = "State B (POC Node Hold)" if active_state == "STATE_B" else f"Above VAL_30 (${val_30:,.1f}) [Node Zone]"
            gate_4_details = f"{zone_desc}: Funding={curr_funding * 100:+.4f}%, Rank={p90_f:.1f}% (<=75.0% required)"

        # Confluence Score
        score = int(gate_1_pass) + int(gate_2_pass) + int(gate_3_pass) + int(gate_4_pass)
        is_long = score == 4
        verdict = "EXECUTE SPOT LONG" if is_long else "STANDBY / CASH"
        status = "LIVE" if is_long else "STANDBY"

        # -------------------------------------------------------------
        # Audit Fix 2: POSITION SIZING & 0.75% SAFETY SHIELD (Fix min() Stop Bug)
        # -------------------------------------------------------------
        p_entry = float(closes[-1])
        raw_stop = float(np.min(lows[-3:])) - (0.0015 * p_entry)
        raw_stop_pct = (p_entry - raw_stop) / p_entry
        stop_pct = max(0.0125, min(0.0400, raw_stop_pct))
        p_stop = p_entry * (1.0 - stop_pct)
        notional_risk = (equity_usd * 0.0075) / stop_pct
        notional_vol = equity_usd * min(1.0, 55.0 / dvol_current) if dvol_current > 0 else equity_usd
        final_notional = min(notional_risk, notional_vol, equity_usd)
        btc_size = final_notional / p_entry if p_entry > 0 else 0.0

        if vah_30 > p_entry:
            target_1 = min(p_entry + 2.0 * (p_entry - p_stop), vah_30)
        else:
            target_1 = p_entry + 2.0 * (p_entry - p_stop)

        # -------------------------------------------------------------
        # Audit Fix 4 & 5: DE-CLUSTERED 90-DAY IN-SAMPLE EVENT STUDY
        # -------------------------------------------------------------
        event_study = self._run_historical_event_study(
            closes=closes,
            highs=highs,
            lows=lows,
            s_vols=s_vols,
            dS=dS,
            dF=dF,
            open_times=open_times,
            funding_raw=funding_raw,
            N=N,
        )

        ev = FourGateEvaluation(
            timestamp_utc=now_utc.strftime("%Y-%m-%d %H:%M:%S UTC"),
            status=status,
            verdict=verdict,
            score=score,
            live_spot_price=live_spot_px,
            last_closed_bar_utc=last_closed_bar_utc,
            gate_1_levy=gate_1_pass,
            gate_1_val=float(A_SP),
            gate_1_details=gate_1_details,
            gate_2_zflow=gate_2_pass,
            gate_2_val=float(D_flow),
            gate_2_z_s=float(z_S),
            gate_2_z_f=float(z_F),
            gate_2_ds_24h=last_ds_24h,
            gate_2_details=gate_2_details,
            gate_3_structure=gate_3_pass,
            gate_3_state=active_state,
            gate_3_poc=poc_30,
            gate_3_val=val_30,
            gate_3_vah=vah_30,
            gate_3_l20=l_20,
            gate_3_details=gate_3_details,
            gate_4_positioning=gate_4_pass,
            gate_4_funding_rate=curr_funding,
            gate_4_funding_p90=p90_f,
            gate_4_details=gate_4_details,
            dvol_current=dvol_current,
            entry_price=p_entry,
            stop_price=p_stop,
            stop_pct=stop_pct,
            target_1_price=target_1,
            notional_risk_usd=float(notional_risk),
            notional_vol_usd=float(notional_vol),
            final_notional_usd=float(final_notional),
            btc_size=float(btc_size),
            event_study_triggers_count=event_study.get("count", 0),
            event_study_small_sample=event_study.get("small_sample", True),
            event_study_results=event_study,
            raw_data_available=True,
            error_message="",
        )
        return ev

    def _run_historical_event_study(
        self,
        closes: np.ndarray,
        highs: np.ndarray,
        lows: np.ndarray,
        s_vols: np.ndarray,
        dS: np.ndarray,
        dF: np.ndarray,
        open_times: np.ndarray,
        funding_raw: List[Any],
        N: int,
    ) -> Dict[str, Any]:
        """Calculates forward return expectancy and benchmark alpha of de-clustered 4/4 triggers (5D Embargo)."""
        fund_times = np.array([f["fundingTime"] for f in funding_raw])
        fund_rates = np.array([float(f["fundingRate"]) for f in funding_raw])

        # Evaluate trailing 540 bars (~90 days) with 180 bars warmup and 60 bars forward horizon
        start_idx = max(180, N - 60 - 540)
        end_idx = N - 60

        # Unconditional baseline forward returns across the exact same evaluation window
        base_1d = [(closes[k + 6] - closes[k]) / closes[k] for k in range(start_idx, end_idx)]
        base_3d = [(closes[k + 18] - closes[k]) / closes[k] for k in range(start_idx, end_idx)]
        base_5d = [(closes[k + 30] - closes[k]) / closes[k] for k in range(start_idx, end_idx)]
        base_10d = [(closes[k + 60] - closes[k]) / closes[k] for k in range(start_idx, end_idx)]

        baseline_mean_1d = float(np.mean(base_1d) * 100.0) if base_1d else 0.0
        baseline_mean_3d = float(np.mean(base_3d) * 100.0) if base_3d else 0.0
        baseline_mean_5d = float(np.mean(base_5d) * 100.0) if base_5d else 0.0
        baseline_mean_10d = float(np.mean(base_10d) * 100.0) if base_10d else 0.0

        triggers: List[Dict[str, Any]] = []
        last_trigger_bar = -999

        for k in range(start_idx, end_idx):
            # Audit Fix 4: 30-bar (5-day) cooldown embargo to de-cluster consecutive signals
            if k < last_trigger_bar + 30:
                continue

            # Gate 1: Rough Path Signature Engine (Lévy Signed Area)
            C_S = np.zeros(7)
            C_S[1:] = np.cumsum(dS[k - 5 : k + 1])
            L_P = np.zeros(7)
            L_P[1:] = np.log(closes[k - 5 : k + 1] / closes[k - 6])
            s_cs = np.std(C_S)
            s_lp = np.std(L_P)
            X = C_S / (s_cs if s_cs > 1e-9 else 1.0)
            Y = L_P / (s_lp if s_lp > 1e-9 else 1.0)
            A_SP = 0.5 * sum(X[j - 1] * (Y[j] - Y[j - 1]) - Y[j - 1] * (X[j] - X[j - 1]) for j in range(1, 7))
            if A_SP <= 0.0:
                continue

            # Gate 2: Spot vs Perp CVD Z-Spread
            idx_start = k - 179
            dS_win = [np.sum(dS[i - 5 : i + 1]) for i in range(idx_start, k + 1)]
            dF_win = [np.sum(dF[i - 5 : i + 1]) for i in range(idx_start, k + 1)]
            if dS_win[-1] <= 0:
                continue
            std_dsw = np.std(dS_win)
            std_dfw = np.std(dF_win)
            z_S = (dS_win[-1] - np.mean(dS_win)) / (std_dsw if std_dsw > 1e-9 else 1.0)
            z_F = (dF_win[-1] - np.mean(dF_win)) / (std_dfw if std_dfw > 1e-9 else 1.0)
            if (z_S - z_F) < 1.0:
                continue

            # Gate 3: 30D Executed Volume Profile Structure
            w_h = highs[idx_start : k + 1]
            w_l = lows[idx_start : k + 1]
            w_c = closes[idx_start : k + 1]
            w_v = s_vols[idx_start : k + 1]
            p_min, p_max = float(np.min(w_l)), float(np.max(w_h))
            bins = np.linspace(p_min, p_max, 51)
            vol_bins = np.zeros(50)
            for tp, v in zip((w_h + w_l + w_c) / 3.0, w_v):
                vol_bins[min(49, max(0, int((tp - p_min) / (p_max - p_min + 1e-9) * 50)))] += v
            poc_idx = np.argmax(vol_bins)
            poc_30 = (bins[poc_idx] + bins[poc_idx + 1]) / 2.0
            c_vol = np.cumsum(vol_bins)
            val_30 = (bins[np.searchsorted(c_vol, c_vol[-1] * 0.15)] + bins[min(49, np.searchsorted(c_vol, c_vol[-1] * 0.15) + 1)]) / 2.0
            l_20 = np.min(lows[max(0, k - 120) : k])

            state_a = (lows[k] < l_20 and closes[k] > l_20) or (lows[k] < val_30 and closes[k] > val_30)
            state_b = (closes[k] > poc_30) and (abs(lows[k] - poc_30) / poc_30 <= 0.005) and (closes[k - 1] > poc_30)
            if not (state_a or state_b):
                continue

            # Audit Fix 4: Zero Look-Ahead strictly from funding prints <= bar_close_time
            bar_close_ms = int(open_times[k] + (4 * 3600 * 1000) - 1)
            past_rates = fund_rates[fund_times <= bar_close_ms]
            if len(past_rates) == 0:
                continue
            win_rates = past_rates[-270:] if len(past_rates) >= 270 else past_rates
            curr_f = win_rates[-1]
            p90 = (np.sum(win_rates < curr_f) / len(win_rates)) * 100.0

            # Audit Fix 3: Context-aware Gate 4
            if state_a:
                if not (curr_f <= 0.0 or p90 < 25.0):
                    continue
            else:
                if not (p90 <= 75.0):
                    continue

            # Trigger fired -> log and activate 30-bar embargo
            r1d = float((closes[k + 6] - closes[k]) / closes[k])
            r3d = float((closes[k + 18] - closes[k]) / closes[k])
            r5d = float((closes[k + 30] - closes[k]) / closes[k])
            r10d = float((closes[k + 60] - closes[k]) / closes[k])

            triggers.append(
                {
                    "bar_idx": int(k),
                    "entry_price": float(closes[k]),
                    "state": "STATE_A" if state_a else "STATE_B",
                    "ret_1d": r1d,
                    "ret_3d": r3d,
                    "ret_5d": r5d,
                    "ret_10d": r10d,
                }
            )
            last_trigger_bar = k

        count = len(triggers)
        if count == 0:
            return {
                "count": 0,
                "small_sample": True,
                "win_rate_1d": 0.0,
                "mean_ret_1d": 0.0,
                "median_ret_1d": 0.0,
                "baseline_mean_1d": baseline_mean_1d,
                "alpha_1d": 0.0 - baseline_mean_1d,
                "win_rate_3d": 0.0,
                "mean_ret_3d": 0.0,
                "median_ret_3d": 0.0,
                "baseline_mean_3d": baseline_mean_3d,
                "alpha_3d": 0.0 - baseline_mean_3d,
                "win_rate_5d": 0.0,
                "mean_ret_5d": 0.0,
                "median_ret_5d": 0.0,
                "baseline_mean_5d": baseline_mean_5d,
                "alpha_5d": 0.0 - baseline_mean_5d,
                "win_rate_10d": 0.0,
                "mean_ret_10d": 0.0,
                "median_ret_10d": 0.0,
                "baseline_mean_10d": baseline_mean_10d,
                "alpha_10d": 0.0 - baseline_mean_10d,
                "triggers": [],
            }

        r1 = [t["ret_1d"] * 100.0 for t in triggers]
        r3 = [t["ret_3d"] * 100.0 for t in triggers]
        r5 = [t["ret_5d"] * 100.0 for t in triggers]
        r10 = [t["ret_10d"] * 100.0 for t in triggers]

        mean_1d = float(np.mean(r1))
        mean_3d = float(np.mean(r3))
        mean_5d = float(np.mean(r5))
        mean_10d = float(np.mean(r10))

        return {
            "count": count,
            "small_sample": bool(count < 30),
            "win_rate_1d": float(sum(x > 0 for x in r1) / count * 100.0),
            "mean_ret_1d": mean_1d,
            "median_ret_1d": float(np.median(r1)),
            "baseline_mean_1d": baseline_mean_1d,
            "alpha_1d": mean_1d - baseline_mean_1d,
            "win_rate_3d": float(sum(x > 0 for x in r3) / count * 100.0),
            "mean_ret_3d": mean_3d,
            "median_ret_3d": float(np.median(r3)),
            "baseline_mean_3d": baseline_mean_3d,
            "alpha_3d": mean_3d - baseline_mean_3d,
            "win_rate_5d": float(sum(x > 0 for x in r5) / count * 100.0),
            "mean_ret_5d": mean_5d,
            "median_ret_5d": float(np.median(r5)),
            "baseline_mean_5d": baseline_mean_5d,
            "alpha_5d": mean_5d - baseline_mean_5d,
            "win_rate_10d": float(sum(x > 0 for x in r10) / count * 100.0),
            "mean_ret_10d": mean_10d,
            "median_ret_10d": float(np.median(r10)),
            "baseline_mean_10d": baseline_mean_10d,
            "alpha_10d": mean_10d - baseline_mean_10d,
            "triggers": triggers,
        }

    def evaluate(self, store: Any) -> Optional[FourGateEvaluation]:
        """Evaluates live data or returns cached evaluation, persisting to state file."""
        now = time.time()
        if self._cached_eval and (now - self._last_fetch_ts) < self._cache_duration_sec:
            store.four_gate_evaluation = self._cached_eval
            return self._cached_eval

        # Pull primary endpoints
        spot_k, perp_k, fund_p, dvol_v = self.fetch_primary_feeds()
        if not spot_k or not perp_k or not fund_p or dvol_v is None:
            # Check if we have previous evaluation to avoid flashing on single timeout
            if self._cached_eval and (now - self._last_fetch_ts) < 120.0:
                store.four_gate_evaluation = self._cached_eval
                return self._cached_eval

            now_utc = datetime.now(timezone.utc)
            fail_ev = FourGateEvaluation(
                timestamp_utc=now_utc.strftime("%Y-%m-%d %H:%M:%S UTC"),
                status="HALT: DATA UNAVAILABLE",
                verdict="HALT: DATA UNAVAILABLE",
                raw_data_available=False,
                error_message="Primary REST endpoint timeout or connection failure.",
            )
            self._cached_eval = fail_ev
            self._last_fetch_ts = now
            store.four_gate_evaluation = fail_ev
            self.persist_state(fail_ev)
            return fail_ev

        # Compute full evaluation
        ev = self.calculate_evaluation(spot_k, perp_k, fund_p, dvol_v)
        self._cached_eval = ev
        self._last_fetch_ts = now
        store.four_gate_evaluation = ev
        self.persist_state(ev)
        return ev

    def persist_state(self, ev: FourGateEvaluation) -> None:
        """Saves four_gate_state.json for mobile API and daemon monitoring."""
        try:
            data = {
                "timestamp_utc": ev.timestamp_utc,
                "live_spot_price": ev.live_spot_price,
                "last_closed_bar_utc": ev.last_closed_bar_utc,
                "status": ev.status,
                "verdict": ev.verdict,
                "score": ev.score,
                "gate_1": {
                    "passed": ev.gate_1_levy,
                    "A_SP": ev.gate_1_val,
                    "details": ev.gate_1_details,
                },
                "gate_2": {
                    "passed": ev.gate_2_zflow,
                    "D_flow": ev.gate_2_val,
                    "z_S": ev.gate_2_z_s,
                    "z_F": ev.gate_2_z_f,
                    "dS_24h": ev.gate_2_ds_24h,
                    "details": ev.gate_2_details,
                },
                "gate_3": {
                    "passed": ev.gate_3_structure,
                    "state": ev.gate_3_state,
                    "poc_30": ev.gate_3_poc,
                    "val_30": ev.gate_3_val,
                    "vah_30": ev.gate_3_vah,
                    "l_20": ev.gate_3_l20,
                    "details": ev.gate_3_details,
                },
                "gate_4": {
                    "passed": ev.gate_4_positioning,
                    "funding_rate": ev.gate_4_funding_rate,
                    "funding_p90": ev.gate_4_funding_p90,
                    "details": ev.gate_4_details,
                },
                "sizing": {
                    "dvol": ev.dvol_current,
                    "entry_price": ev.entry_price,
                    "stop_price": ev.stop_price,
                    "stop_pct": ev.stop_pct,
                    "target_1_price": ev.target_1_price,
                    "notional_risk_usd": ev.notional_risk_usd,
                    "notional_vol_usd": ev.notional_vol_usd,
                    "final_notional_usd": ev.final_notional_usd,
                    "btc_size": ev.btc_size,
                },
                "event_study": ev.event_study_results,
                "raw_data_available": ev.raw_data_available,
                "error_message": ev.error_message,
            }
            json_text = json.dumps(data, indent=2)
            (BASE_DIR / "four_gate_state.json").write_text(json_text, encoding="utf-8")
            log_dir = BASE_DIR / "logs"
            if log_dir.exists():
                (log_dir / "four_gate_state.json").write_text(json_text, encoding="utf-8")
        except Exception as exc:
            logger.debug("Failed writing four_gate_state.json: %s", exc)


def copy_four_gate_to_clipboard(store: Any) -> Tuple[bool, str, int]:
    """Formats and copies the pure DATA-ONLY markdown telemetry packet for Tab 19."""
    ev: Optional[FourGateEvaluation] = getattr(store, "four_gate_evaluation", None)
    if not ev:
        return False, "Four-Gate evaluation not yet available.", 0

    lines = [
        "# BTC 4-GATE QUANTITATIVE PROTOCOL TELEMETRY PACKET (TAB 19 / [Q])",
        f"**Timestamp UTC**: {ev.timestamp_utc}",
        f"**Live Spot**: ${ev.live_spot_price:,.2f} | **Last Closed 4H Bar**: {ev.last_closed_bar_utc}",
        f"**Status**: {ev.status} | **Verdict**: {ev.verdict} | **Confluence Score**: {ev.score}/4",
        "",
        "## 1. DETERMINISTIC 4-GATE TELEMETRY READOUT",
        f"- Gate 1 [Rough Path Levy Area A_SP]: {'PASS' if ev.gate_1_levy else 'FAIL'} | Value: {ev.gate_1_val:+.4f} (Rule: A_SP > 0.0)",
        f"- Gate 2 [Spot-Perp CVD Z-Spread]:    {'PASS' if ev.gate_2_zflow else 'FAIL'} | Value: {ev.gate_2_val:+.2f} (Rule: D_flow >= 1.0 & Spot24h > 0)",
        f"  - Details: z_S={ev.gate_2_z_s:+.2f}, z_F={ev.gate_2_z_f:+.2f}, Spot24h_Delta={ev.gate_2_ds_24h:+,.1f} BTC",
        f"- Gate 3 [30D Volume Profile Structure]: {'PASS' if ev.gate_3_structure else 'FAIL'} | Active State: {ev.gate_3_state}",
        f"  - POC_30: ${ev.gate_3_poc:,.1f} | VAL_30: ${ev.gate_3_val:,.1f} | VAH_30: ${ev.gate_3_vah:,.1f} | L20: ${ev.gate_3_l20:,.1f}",
        f"- Gate 4 [90D Funding Anti-Crowding]: {'PASS' if ev.gate_4_positioning else 'FAIL'} | Rate: {ev.gate_4_funding_rate * 100:+.4f}% | Percentile: {ev.gate_4_funding_p90:.1f}%",
        f"  - Active Rule: {ev.gate_4_details}",
        "",
        "## 2. 0.75% SAFETY SHIELD & EXECUTION TICKET",
        f"- Entry Reference Price: ${ev.entry_price:,.2f}",
        f"- Hard Stop Loss Price:  ${ev.stop_price:,.2f} ({ev.stop_pct * 100:.2f}% distance)",
        f"- Take-Profit 1 (+2R / VAH): ${ev.target_1_price:,.2f}",
        f"- Deribit 30D DVOL:      {ev.dvol_current:.2f}%" if ev.dvol_current else "- Deribit 30D DVOL: DATA UNAVAILABLE",
        f"- 0.75% Risk Notional:   ${ev.notional_risk_usd:,.2f}",
        f"- DVOL Vol-Capped Size:  ${ev.notional_vol_usd:,.2f}",
        f"- Final Spot Allocation: ${ev.final_notional_usd:,.2f} (~{ev.btc_size:.4f} BTC)",
        "",
        "## 3. 90-DAY DE-CLUSTERED IN-SAMPLE EVENT STUDY (5D EMBARGO)",
        f"- De-Clustered Triggers (N): {ev.event_study_triggers_count}",
        f"- Small Sample Notice: {'ACTIVE (N < 30)' if ev.event_study_small_sample else 'PASSED (N >= 30)'}",
    ]

    es = ev.event_study_results
    if es and es.get("count", 0) > 0:
        lines.extend([
            f"- 1D Forward Return: Win Rate={es.get('win_rate_1d', 0.0):.1f}%, Mean={es.get('mean_ret_1d', 0.0):+.2f}% (vs Baseline {es.get('baseline_mean_1d', 0.0):+.2f}%: Alpha {es.get('alpha_1d', 0.0):+.2f}%)",
            f"- 3D Forward Return: Win Rate={es.get('win_rate_3d', 0.0):.1f}%, Mean={es.get('mean_ret_3d', 0.0):+.2f}% (vs Baseline {es.get('baseline_mean_3d', 0.0):+.2f}%: Alpha {es.get('alpha_3d', 0.0):+.2f}%)",
            f"- 5D Forward Return: Win Rate={es.get('win_rate_5d', 0.0):.1f}%, Mean={es.get('mean_ret_5d', 0.0):+.2f}% (vs Baseline {es.get('baseline_mean_5d', 0.0):+.2f}%: Alpha {es.get('alpha_5d', 0.0):+.2f}%)",
            f"- 10D Forward Return: Win Rate={es.get('win_rate_10d', 0.0):.1f}%, Mean={es.get('mean_ret_10d', 0.0):+.2f}% (vs Baseline {es.get('baseline_mean_10d', 0.0):+.2f}%: Alpha {es.get('alpha_10d', 0.0):+.2f}%)",
        ])
    else:
        lines.append("- No 4/4 triggers registered in trailing lookback window.")

    packet = "\n".join(lines)
    char_count = len(packet)

    # Windows clipboard copy
    try:
        proc = subprocess.Popen(["clip"], stdin=subprocess.PIPE, shell=True)
        proc.communicate(input=packet.encode("utf-8"))
    except Exception:
        pass

    return True, "Copied Tab 19 4-Gate packet to clipboard.", char_count


if __name__ == "__main__":
    print("Testing FourGateEngine live fetch & math...")
    engine = FourGateEngine()
    spot_k, perp_k, fund_p, dvol_v = engine.fetch_primary_feeds()
    if spot_k and perp_k and fund_p and dvol_v is not None:
        ev = engine.calculate_evaluation(spot_k, perp_k, fund_p, dvol_v)
        engine.persist_state(ev)
        print(f"SUCCESS! Timestamp: {ev.timestamp_utc}")
        print(f"Score: {ev.score}/4 | Verdict: {ev.verdict}")
        print(f"Gate 1 (Lévy A_SP): {ev.gate_1_val:+.4f} ({ev.gate_1_levy})")
        print(f"Gate 2 (D_flow):    {ev.gate_2_val:+.2f} ({ev.gate_2_zflow})")
        print(f"Gate 3 (Profile):   {ev.gate_3_state} ({ev.gate_3_structure})")
        print(f"Gate 4 (Funding):   {ev.gate_4_funding_p90:.1f}% ({ev.gate_4_positioning})")
        print(f"Event Study Count:  {ev.event_study_triggers_count} (Small sample: {ev.event_study_small_sample})")
    else:
        print("API Fetch Failed -> DATA UNAVAILABLE")
