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

        # Refinement 2: Display 4H bar CLOSE time (+4h / 14,400,000 ms) rather than open time
        last_closed_bar_utc = datetime.fromtimestamp(
            (spot_ts[-1] + 14400000) / 1000, tz=timezone.utc
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

        # Refinement 1: Anchor L_20 and H_20 strictly prior to the 3-bar (12H) window
        l_20 = float(np.min(lows[-123:-3])) if len(lows) >= 123 else (float(np.min(lows[:-3])) if len(lows) > 3 else float(np.min(lows)))
        h_20 = float(np.max(highs[-123:-3])) if len(highs) >= 123 else (float(np.max(highs[:-3])) if len(highs) > 3 else float(np.max(highs)))
        window_low = float(np.min(lows[-3:]))
        window_high = float(np.max(highs[-3:]))

        # Gate 3 — Loop A: State A (12H Sweep & Hold Reclaim of VAL or L20)
        sweep_L20 = bool((window_low < l_20) and (closes[-1] > l_20) and (lows[-1] >= window_low))
        sweep_VAL = bool((window_low < val_30) and (closes[-1] > val_30) and (lows[-1] >= window_low))
        state_a = sweep_L20 or sweep_VAL

        # Gate 3 — Loop A: State B (POC Node Hold)
        state_b = bool((closes[-1] > poc_30) and (abs(float(np.min(lows[-2:])) - poc_30) / poc_30 <= 0.005) and (closes[-2] > poc_30))
        gate_3_pass = state_a or state_b
        active_state = "STATE_A" if state_a else ("STATE_B" if state_b else "NONE")

        if state_a:
            target_swept = "L20" if sweep_L20 else "VAL30"
            gate_3_details = f"State A (12H Sweep {target_swept}): Low=${window_low:,.0f} Reclaimed Close=${closes[-1]:,.0f}"
        elif state_b:
            gate_3_details = f"State B (POC Hold): Low=${float(np.min(lows[-2:])):,.0f} tested POC=${poc_30:,.0f}"
        else:
            gate_3_details = f"No Trigger: POC=${poc_30:,.0f} | VAL=${val_30:,.0f} | L20=${l_20:,.0f}"

        # Gate 3 — Loop B: Resistance Sweep & Rejection of VAH or H20
        sweep_H20 = bool((window_high > h_20) and (closes[-1] < h_20) and (highs[-1] <= window_high))
        sweep_VAH = bool((window_high > vah_30) and (closes[-1] < vah_30) and (highs[-1] <= window_high))
        state_a_b = sweep_H20 or sweep_VAH
        state_b_b = bool((closes[-1] < vah_30) and (abs(float(np.max(highs[-2:])) - vah_30) / vah_30 <= 0.005) and (closes[-2] < vah_30))
        gate_3_b_pass = state_a_b or state_b_b
        active_state_b = "STATE_A" if state_a_b else ("STATE_B" if state_b_b else "NONE")

        if state_a_b:
            target_swept_b = "H20" if sweep_H20 else "VAH30"
            gate_3_b_details = f"State A (12H Rejection {target_swept_b}): High=${window_high:,.0f} Rejected Close=${closes[-1]:,.0f}"
        elif state_b_b:
            gate_3_b_details = f"State B (VAH Rejection): High=${float(np.max(highs[-2:])):,.0f} tested VAH=${vah_30:,.0f}"
        else:
            gate_3_b_details = f"No Trigger: VAH=${vah_30:,.0f} | POC=${poc_30:,.0f} | H20=${h_20:,.0f}"

        # -------------------------------------------------------------
        # GATE 4: 90D Funding Anti-Crowding & Euphoria (Trailing 270 Prints)
        # -------------------------------------------------------------
        rates = [float(f["fundingRate"]) for f in funding_raw]
        curr_funding = float(rates[-1]) if rates else 0.0
        recent_rates = rates[-270:] if len(rates) >= 270 else rates
        p90_f = (sum(r < curr_funding for r in recent_rates) / len(recent_rates)) * 100.0 if recent_rates else 50.0

        prev_funding = float(rates[-2]) if len(rates) >= 2 else curr_funding
        p90_prev = (sum(r < prev_funding for r in recent_rates) / len(recent_rates)) * 100.0 if recent_rates else 50.0

        f_recent = min(prev_funding, curr_funding)
        p90_recent = min(p90_prev, p90_f)

        # Loop A: Flush Memory (<25% or Neg required in Sweep Zone, <=75% in Node Zone)
        is_sweep_zone = (active_state == "STATE_A") or (active_state == "NONE" and closes[-1] < val_30)
        if is_sweep_zone:
            gate_4_pass = bool(((f_recent <= 0.0) or (p90_recent < 25.0)) and (p90_f <= 50.0))
            gate_4_details = f"Sweep Zone (<VAL): F={curr_funding * 100:+.4f}% | P90={p90_f:.1f}% (Req <25%/Neg)"
        else:
            gate_4_pass = bool(p90_f <= 75.0)
            gate_4_details = f"Node Zone (>=VAL): F={curr_funding * 100:+.4f}% | P90={p90_f:.1f}% (Req <=75.0%)"

        # Loop B: Euphoria Memory (>=75% or >0.015% in Resistance Zone, >=75% in Node Zone)
        is_res_zone_b = (active_state_b == "STATE_A") or (active_state_b == "NONE" and closes[-1] > vah_30)
        f_recent_b = max(prev_funding, curr_funding)
        p90_recent_b = max(p90_prev, p90_f)
        if is_res_zone_b:
            gate_4_b_pass = bool(((f_recent_b > 0.00015) or (p90_recent_b >= 75.0)) and (curr_funding > 0.00010))
            gate_4_b_details = f"Res Zone (>VAH): F={curr_funding * 100:+.4f}% | P90={p90_f:.1f}% (Req >=75% / >0.015%)"
        else:
            gate_4_b_pass = bool((p90_f >= 75.0) and (curr_funding > 0.00010))
            gate_4_b_details = f"Node Zone (<=VAH): F={curr_funding * 100:+.4f}% | P90={p90_f:.1f}% (Req >=75.0%)"

        # Loop B Gate 1: Signed Area Negative (Spot dragging / unbacked retail markup)
        gate_1_b_pass = bool(A_SP < 0.0)
        gate_1_b_details = (
            f"A_SP={A_SP:+.4f} < 0.0 (Spot path lagging / unbacked retail markup)"
            if gate_1_b_pass
            else f"A_SP={A_SP:+.4f} >= 0.0 (Spot accumulation is backing price)"
        )

        # Loop B Gate 2: CVD Z-Spread <= -1.0 & 24H Spot CVD < 0 (Whales distributing spot into perp longs)
        gate_2_b_pass = bool(D_flow <= -1.0 and last_ds_24h < 0)
        gate_2_b_details = (
            f"D_flow={D_flow:+.2f} <= -1.0 & 24h Spot CVD={last_ds_24h:+,.1f} < 0"
            if gate_2_b_pass
            else f"D_flow={D_flow:+.2f} (z_S={z_S:+.2f}, z_F={z_F:+.2f}, Spot24h={last_ds_24h:+,.1f})"
        )

        # -------------------------------------------------------------
        # CAPITAL SANDBOX & DUAL-INVENTORY SLEEVE ALLOCATION
        # -------------------------------------------------------------
        portfolio_equity = float(equity_usd)
        active_sandbox = portfolio_equity * 0.20
        core_reserve = portfolio_equity * 0.80
        usdt_sleeve = portfolio_equity * 0.10
        btc_sleeve = portfolio_equity * 0.10
        btc_sleeve_units = btc_sleeve / live_spot_px if live_spot_px > 0 else 0.0

        # Loop A Confluence & Execution Ticket (Dip Harvester)
        score_a = int(gate_1_pass) + int(gate_2_pass) + int(gate_3_pass) + int(gate_4_pass)
        loop_a_is_trigger = (score_a == 4)
        loop_a_verdict = "EXECUTE: DEPLOY USDT → BUY BTC" if loop_a_is_trigger else "STANDBY IN USDT CASH"
        loop_a_status = "EXECUTE_BUY" if loop_a_is_trigger else "READY_USDT"
        p_entry_a = float(closes[-1])
        if p_entry_a < poc_30 * 0.98:
            target_a = poc_30
        elif p_entry_a < vah_30 * 0.98:
            target_a = vah_30
        else:
            target_a = p_entry_a * 1.04
        target_a_pct = (target_a - p_entry_a) / p_entry_a if p_entry_a > 0 else 0.0
        expected_profit_usd_a = usdt_sleeve * target_a_pct

        # Loop B Confluence & Diagnostic Telemetry (G1 Gate: binary auto-sell disabled)
        # Empirically failed 2020-2026 G1 validation (N=2 triggers, -79.08% BTC stack dilution).
        score_b = int(gate_1_b_pass) + int(gate_2_b_pass) + int(gate_3_b_pass) + int(gate_4_b_pass)
        loop_b_execution_enabled = False
        loop_b_is_trigger = bool(loop_b_execution_enabled and (score_b == 4))
        loop_b_verdict = (
            "4/4 DIST ALERT (G1 GATED OFF — HOLD BTC)"
            if score_b == 4
            else "HOLD BTC INVENTORY (G1 GATE: AUTO-SELL OFF)"
        )
        loop_b_status = "GATED_OFF_HOLD_BTC"
        loop_b_stop_rule = "G1 GATE: PASSIVE BTC HOLD (LOOP B AUTO-SELL DISABLED AFTER N=2 / -79.1% BTC LOSS)"
        p_sell_b = float(closes[-1])
        if p_sell_b > poc_30 * 1.02:
            buyback_target_b = poc_30
        elif p_sell_b > val_30 * 1.02:
            buyback_target_b = val_30
        else:
            buyback_target_b = p_sell_b * 0.96
        discount_pct_b = (p_sell_b - buyback_target_b) / p_sell_b if p_sell_b > 0 else 0.0
        free_satoshis_btc = btc_sleeve_units * ((p_sell_b / buyback_target_b) - 1.0) if buyback_target_b > 0 else 0.0
        free_satoshis_pct = ((p_sell_b / buyback_target_b) - 1.0) * 100.0 if buyback_target_b > 0 else 0.0
        surplus_cash_usd = btc_sleeve_units * (p_sell_b - buyback_target_b) if buyback_target_b > 0 else 0.0

        if loop_a_is_trigger:
            inventory_state = "LOOP_A_TRIGGER (BUY BTC)"
        else:
            inventory_state = "G1: LOOP A ACTIVE / SLEEVE B HOLD"

        # Legacy Confluence Score & Verdict (Loop A / Spot Long)
        score = score_a
        verdict = "EXECUTE SPOT LONG" if loop_a_is_trigger else "STANDBY / CASH"
        status = "LIVE" if loop_a_is_trigger else "STANDBY"

        # -------------------------------------------------------------
        # Audit Fix 2: POSITION SIZING & 0.75% SAFETY SHIELD (Legacy Reference)
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
        # DE-CLUSTERED 90-DAY IN-SAMPLE EVENT STUDY (DUAL-LOOP)
        # -------------------------------------------------------------
        event_study_a, event_study_b = self._run_historical_event_study(
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
            account_equity_usd=portfolio_equity,
            active_sandbox_usd=active_sandbox,
            core_reserve_usd=core_reserve,
            usdt_sleeve_usd=usdt_sleeve,
            btc_sleeve_usd=btc_sleeve,
            btc_sleeve_units=btc_sleeve_units,
            inventory_state=inventory_state,
            # Loop A
            loop_a_score=score_a,
            loop_a_verdict=loop_a_verdict,
            loop_a_status=loop_a_status,
            loop_a_g1_levy=gate_1_pass,
            loop_a_g1_val=float(A_SP),
            loop_a_g1_details=gate_1_details,
            loop_a_g2_zflow=gate_2_pass,
            loop_a_g2_val=float(D_flow),
            loop_a_g2_z_s=float(z_S),
            loop_a_g2_z_f=float(z_F),
            loop_a_g2_ds_24h=last_ds_24h,
            loop_a_g2_details=gate_2_details,
            loop_a_g3_structure=gate_3_pass,
            loop_a_g3_state=active_state,
            loop_a_g3_details=gate_3_details,
            loop_a_g4_positioning=gate_4_pass,
            loop_a_g4_funding_rate=curr_funding,
            loop_a_g4_funding_p90=p90_f,
            loop_a_g4_details=gate_4_details,
            loop_a_entry_price=p_entry_a,
            loop_a_target_price=target_a,
            loop_a_target_pct=target_a_pct,
            loop_a_expected_profit_usd=expected_profit_usd_a,
            # Loop B
            loop_b_score=score_b,
            loop_b_verdict=loop_b_verdict,
            loop_b_status=loop_b_status,
            loop_b_g1_levy=gate_1_b_pass,
            loop_b_g1_val=float(A_SP),
            loop_b_g1_details=gate_1_b_details,
            loop_b_g2_zflow=gate_2_b_pass,
            loop_b_g2_val=float(D_flow),
            loop_b_g2_z_s=float(z_S),
            loop_b_g2_z_f=float(z_F),
            loop_b_g2_ds_24h=last_ds_24h,
            loop_b_g2_details=gate_2_b_details,
            loop_b_g3_structure=gate_3_b_pass,
            loop_b_g3_state=active_state_b,
            loop_b_g3_details=gate_3_b_details,
            loop_b_g3_h20=h_20,
            loop_b_g4_positioning=gate_4_b_pass,
            loop_b_g4_funding_rate=curr_funding,
            loop_b_g4_funding_p90=p90_f,
            loop_b_g4_details=gate_4_b_details,
            loop_b_sell_price=p_sell_b,
            loop_b_buyback_price=buyback_target_b,
            loop_b_discount_pct=discount_pct_b,
            loop_b_free_satoshis_btc=free_satoshis_btc,
            loop_b_free_satoshis_pct=free_satoshis_pct,
            loop_b_surplus_cash_usd=surplus_cash_usd,
            loop_b_stop_rule=loop_b_stop_rule,
            # Legacy Fields
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
            event_study_triggers_count=event_study_a.get("count", 0),
            event_study_small_sample=event_study_a.get("small_sample", True),
            event_study_results=event_study_a,
            event_study_loop_b_triggers_count=event_study_b.get("count", 0),
            event_study_loop_b_small_sample=event_study_b.get("small_sample", True),
            event_study_loop_b_results=event_study_b,
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
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Calculates forward return expectancy and benchmark alpha of de-clustered triggers for Loop A and Loop B (5D Embargo)."""
        fund_times = np.array([f["fundingTime"] for f in funding_raw])
        fund_rates = np.array([float(f["fundingRate"]) for f in funding_raw])

        # Evaluate trailing 540 bars (~90 days) with 180 bars warmup and 60 bars forward horizon
        start_idx = max(180, N - 60 - 540)
        end_idx = N - 60

        # Unconditional baseline forward returns across the exact same evaluation window
        base_1d_a = [(closes[k + 6] - closes[k]) / closes[k] for k in range(start_idx, end_idx)]
        base_3d_a = [(closes[k + 18] - closes[k]) / closes[k] for k in range(start_idx, end_idx)]
        base_5d_a = [(closes[k + 30] - closes[k]) / closes[k] for k in range(start_idx, end_idx)]
        base_10d_a = [(closes[k + 60] - closes[k]) / closes[k] for k in range(start_idx, end_idx)]

        # Baseline for Loop B: price drop / buyback discount
        base_1d_b = [(closes[k] - closes[k + 6]) / closes[k] for k in range(start_idx, end_idx)]
        base_3d_b = [(closes[k] - closes[k + 18]) / closes[k] for k in range(start_idx, end_idx)]
        base_5d_b = [(closes[k] - closes[k + 30]) / closes[k] for k in range(start_idx, end_idx)]
        base_10d_b = [(closes[k] - closes[k + 60]) / closes[k] for k in range(start_idx, end_idx)]

        baseline_mean_1d_a = float(np.mean(base_1d_a) * 100.0) if base_1d_a else 0.0
        baseline_mean_3d_a = float(np.mean(base_3d_a) * 100.0) if base_3d_a else 0.0
        baseline_mean_5d_a = float(np.mean(base_5d_a) * 100.0) if base_5d_a else 0.0
        baseline_mean_10d_a = float(np.mean(base_10d_a) * 100.0) if base_10d_a else 0.0

        baseline_mean_1d_b = float(np.mean(base_1d_b) * 100.0) if base_1d_b else 0.0
        baseline_mean_3d_b = float(np.mean(base_3d_b) * 100.0) if base_3d_b else 0.0
        baseline_mean_5d_b = float(np.mean(base_5d_b) * 100.0) if base_5d_b else 0.0
        baseline_mean_10d_b = float(np.mean(base_10d_b) * 100.0) if base_10d_b else 0.0

        triggers_a: List[Dict[str, Any]] = []
        triggers_b: List[Dict[str, Any]] = []
        last_trigger_bar_a = -999
        last_trigger_bar_b = -999

        for k in range(start_idx, end_idx):
            # Compute common indicators for bar k
            C_S = np.zeros(7)
            C_S[1:] = np.cumsum(dS[k - 5 : k + 1])
            L_P = np.zeros(7)
            L_P[1:] = np.log(closes[k - 5 : k + 1] / closes[k - 6])
            s_cs = np.std(C_S)
            s_lp = np.std(L_P)
            X = C_S / (s_cs if s_cs > 1e-9 else 1.0)
            Y = L_P / (s_lp if s_lp > 1e-9 else 1.0)
            A_SP = 0.5 * sum(X[j - 1] * (Y[j] - Y[j - 1]) - Y[j - 1] * (X[j] - X[j - 1]) for j in range(1, 7))

            idx_start = k - 179
            dS_win = [np.sum(dS[i - 5 : i + 1]) for i in range(idx_start, k + 1)]
            dF_win = [np.sum(dF[i - 5 : i + 1]) for i in range(idx_start, k + 1)]
            std_dsw = np.std(dS_win)
            std_dfw = np.std(dF_win)
            z_S = (dS_win[-1] - np.mean(dS_win)) / (std_dsw if std_dsw > 1e-9 else 1.0)
            z_F = (dF_win[-1] - np.mean(dF_win)) / (std_dfw if std_dfw > 1e-9 else 1.0)
            d_flow = z_S - z_F

            # Volume Profile on trailing 180 bars
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
            vah_30 = (bins[np.searchsorted(c_vol, c_vol[-1] * 0.85)] + bins[min(49, np.searchsorted(c_vol, c_vol[-1] * 0.85) + 1)]) / 2.0

            l_20 = float(np.min(lows[max(0, k - 122) : max(0, k - 2)]))
            h_20 = float(np.max(highs[max(0, k - 122) : max(0, k - 2)]))
            window_low = float(np.min(lows[k - 2 : k + 1]))
            window_high = float(np.max(highs[k - 2 : k + 1]))

            # Funding rate memory for bar k
            bar_close_ms = int(open_times[k] + (4 * 3600 * 1000) - 1)
            past_rates = fund_rates[fund_times <= bar_close_ms]
            if len(past_rates) == 0:
                continue
            win_rates = past_rates[-270:] if len(past_rates) >= 270 else past_rates
            curr_f = win_rates[-1]
            prev_f = win_rates[-2] if len(win_rates) >= 2 else curr_f
            p90_curr = (np.sum(win_rates < curr_f) / len(win_rates)) * 100.0
            p90_prev = (np.sum(win_rates < prev_f) / len(win_rates)) * 100.0
            f_rec = min(prev_f, curr_f)
            p90_rec = min(p90_prev, p90_curr)

            # ---------------------------------------------------------
            # EVALUATE LOOP A (Dip Harvester)
            # ---------------------------------------------------------
            if k >= last_trigger_bar_a + 30:
                if A_SP > 0.0 and dS_win[-1] > 0 and d_flow >= 1.0:
                    sweep_L20 = (window_low < l_20) and (closes[k] > l_20) and (lows[k] >= window_low)
                    sweep_VAL = (window_low < val_30) and (closes[k] > val_30) and (lows[k] >= window_low)
                    state_a_a = sweep_L20 or sweep_VAL
                    state_b_a = (closes[k] > poc_30) and (abs(float(np.min(lows[k - 1 : k + 1])) - poc_30) / poc_30 <= 0.005) and (closes[k - 1] > poc_30)

                    if state_a_a or state_b_a:
                        is_sweep_a = state_a_a or (not state_b_a and closes[k] < val_30)
                        pass_g4_a = False
                        if is_sweep_a:
                            pass_g4_a = (((f_rec <= 0.0) or (p90_rec < 25.0)) and (p90_curr <= 50.0))
                        else:
                            pass_g4_a = (p90_curr <= 75.0)

                        if pass_g4_a:
                            r1d = float((closes[k + 6] - closes[k]) / closes[k])
                            r3d = float((closes[k + 18] - closes[k]) / closes[k])
                            r5d = float((closes[k + 30] - closes[k]) / closes[k])
                            r10d = float((closes[k + 60] - closes[k]) / closes[k])
                            triggers_a.append({
                                "bar_idx": int(k),
                                "entry_price": float(closes[k]),
                                "state": "STATE_A" if state_a_a else "STATE_B",
                                "ret_1d": r1d,
                                "ret_3d": r3d,
                                "ret_5d": r5d,
                                "ret_10d": r10d,
                            })
                            last_trigger_bar_a = k

            # ---------------------------------------------------------
            # EVALUATE LOOP B (Rip Harvester & Satoshi Accumulator)
            # ---------------------------------------------------------
            if k >= last_trigger_bar_b + 30:
                if A_SP < 0.0 and dS_win[-1] < 0 and d_flow <= -1.0:
                    sweep_H20 = (window_high > h_20) and (closes[k] < h_20) and (highs[k] <= window_high)
                    sweep_VAH = (window_high > vah_30) and (closes[k] < vah_30) and (highs[k] <= window_high)
                    state_a_b = sweep_H20 or sweep_VAH
                    state_b_b = (closes[k] < vah_30) and (abs(float(np.max(highs[k - 1 : k + 1])) - vah_30) / vah_30 <= 0.005) and (closes[k - 1] < vah_30)

                    if state_a_b or state_b_b:
                        is_res_b = state_a_b or (not state_b_b and closes[k] > vah_30)
                        f_rec_b = max(prev_f, curr_f)
                        p90_rec_b = max(p90_prev, p90_curr)
                        pass_g4_b = False
                        if is_res_b:
                            pass_g4_b = (((f_rec_b > 0.00015) or (p90_rec_b >= 75.0)) and (curr_f > 0.00010))
                        else:
                            pass_g4_b = (p90_curr >= 75.0 and curr_f > 0.00010)

                        if pass_g4_b:
                            r1d_b = float((closes[k] - closes[k + 6]) / closes[k])
                            r3d_b = float((closes[k] - closes[k + 18]) / closes[k])
                            r5d_b = float((closes[k] - closes[k + 30]) / closes[k])
                            r10d_b = float((closes[k] - closes[k + 60]) / closes[k])
                            triggers_b.append({
                                "bar_idx": int(k),
                                "sell_price": float(closes[k]),
                                "state": "STATE_A" if state_a_b else "STATE_B",
                                "ret_1d": r1d_b,
                                "ret_3d": r3d_b,
                                "ret_5d": r5d_b,
                                "ret_10d": r10d_b,
                            })
                            last_trigger_bar_b = k

        def _summarize_study(triggers: List[Dict[str, Any]], b1: float, b3: float, b5: float, b10: float) -> Dict[str, Any]:
            count = len(triggers)
            if count == 0:
                return {
                    "count": 0,
                    "small_sample": True,
                    "win_rate_1d": 0.0,
                    "mean_ret_1d": 0.0,
                    "median_ret_1d": 0.0,
                    "baseline_mean_1d": b1,
                    "alpha_1d": 0.0 - b1,
                    "win_rate_3d": 0.0,
                    "mean_ret_3d": 0.0,
                    "median_ret_3d": 0.0,
                    "baseline_mean_3d": b3,
                    "alpha_3d": 0.0 - b3,
                    "win_rate_5d": 0.0,
                    "mean_ret_5d": 0.0,
                    "median_ret_5d": 0.0,
                    "baseline_mean_5d": b5,
                    "alpha_5d": 0.0 - b5,
                    "win_rate_10d": 0.0,
                    "mean_ret_10d": 0.0,
                    "median_ret_10d": 0.0,
                    "baseline_mean_10d": b10,
                    "alpha_10d": 0.0 - b10,
                    "triggers": [],
                }
            r1 = [t["ret_1d"] * 100.0 for t in triggers]
            r3 = [t["ret_3d"] * 100.0 for t in triggers]
            r5 = [t["ret_5d"] * 100.0 for t in triggers]
            r10 = [t["ret_10d"] * 100.0 for t in triggers]

            m1, m3, m5, m10 = float(np.mean(r1)), float(np.mean(r3)), float(np.mean(r5)), float(np.mean(r10))
            return {
                "count": count,
                "small_sample": bool(count < 30),
                "win_rate_1d": float(sum(x > 0 for x in r1) / count * 100.0),
                "mean_ret_1d": m1,
                "median_ret_1d": float(np.median(r1)),
                "baseline_mean_1d": b1,
                "alpha_1d": m1 - b1,
                "win_rate_3d": float(sum(x > 0 for x in r3) / count * 100.0),
                "mean_ret_3d": m3,
                "median_ret_3d": float(np.median(r3)),
                "baseline_mean_3d": b3,
                "alpha_3d": m3 - b3,
                "win_rate_5d": float(sum(x > 0 for x in r5) / count * 100.0),
                "mean_ret_5d": m5,
                "median_ret_5d": float(np.median(r5)),
                "baseline_mean_5d": b5,
                "alpha_5d": m5 - b5,
                "win_rate_10d": float(sum(x > 0 for x in r10) / count * 100.0),
                "mean_ret_10d": m10,
                "median_ret_10d": float(np.median(r10)),
                "baseline_mean_10d": b10,
                "alpha_10d": m10 - b10,
                "triggers": triggers,
            }

        study_a = _summarize_study(triggers_a, baseline_mean_1d_a, baseline_mean_3d_a, baseline_mean_5d_a, baseline_mean_10d_a)
        study_b = _summarize_study(triggers_b, baseline_mean_1d_b, baseline_mean_3d_b, baseline_mean_5d_b, baseline_mean_10d_b)
        return study_a, study_b

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
        """Saves four_gate_state.json and dibse_state.json for mobile API and daemon monitoring."""
        try:
            data = {
                "timestamp_utc": ev.timestamp_utc,
                "protocol": "DIBSE v1.0",
                "live_spot_price": ev.live_spot_price,
                "last_closed_bar_utc": ev.last_closed_bar_utc,
                "status": ev.status,
                "verdict": ev.verdict,
                "score": ev.score,
                "capital_sandbox": {
                    "account_equity_usd": ev.account_equity_usd,
                    "active_sandbox_usd": ev.active_sandbox_usd,
                    "core_reserve_usd": ev.core_reserve_usd,
                    "usdt_sleeve_usd": ev.usdt_sleeve_usd,
                    "btc_sleeve_usd": ev.btc_sleeve_usd,
                    "btc_sleeve_units": ev.btc_sleeve_units,
                    "inventory_state": ev.inventory_state,
                },
                "loop_a": {
                    "score": ev.loop_a_score,
                    "verdict": ev.loop_a_verdict,
                    "status": ev.loop_a_status,
                    "entry_price": ev.loop_a_entry_price,
                    "target_price": ev.loop_a_target_price,
                    "target_pct": ev.loop_a_target_pct,
                    "expected_profit_usd": ev.loop_a_expected_profit_usd,
                    "stop_rule": ev.loop_a_stop_rule,
                    "g1_levy": {"passed": ev.loop_a_g1_levy, "val": ev.loop_a_g1_val, "details": ev.loop_a_g1_details},
                    "g2_zflow": {"passed": ev.loop_a_g2_zflow, "val": ev.loop_a_g2_val, "details": ev.loop_a_g2_details},
                    "g3_structure": {"passed": ev.loop_a_g3_structure, "state": ev.loop_a_g3_state, "details": ev.loop_a_g3_details},
                    "g4_positioning": {"passed": ev.loop_a_g4_positioning, "rate": ev.loop_a_g4_funding_rate, "p90": ev.loop_a_g4_funding_p90, "details": ev.loop_a_g4_details},
                },
                "loop_b": {
                    "score": ev.loop_b_score,
                    "verdict": ev.loop_b_verdict,
                    "status": ev.loop_b_status,
                    "sell_price": ev.loop_b_sell_price,
                    "buyback_price": ev.loop_b_buyback_price,
                    "discount_pct": ev.loop_b_discount_pct,
                    "free_satoshis_btc": ev.loop_b_free_satoshis_btc,
                    "free_satoshis_pct": ev.loop_b_free_satoshis_pct,
                    "surplus_cash_usd": ev.loop_b_surplus_cash_usd,
                    "stop_rule": ev.loop_b_stop_rule,
                    "g1_levy": {"passed": ev.loop_b_g1_levy, "val": ev.loop_b_g1_val, "details": ev.loop_b_g1_details},
                    "g2_zflow": {"passed": ev.loop_b_g2_zflow, "val": ev.loop_b_g2_val, "details": ev.loop_b_g2_details},
                    "g3_structure": {"passed": ev.loop_b_g3_structure, "state": ev.loop_b_g3_state, "h20": ev.loop_b_g3_h20, "details": ev.loop_b_g3_details},
                    "g4_positioning": {"passed": ev.loop_b_g4_positioning, "rate": ev.loop_b_g4_funding_rate, "p90": ev.loop_b_g4_funding_p90, "details": ev.loop_b_g4_details},
                },
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
                "event_study_loop_b": ev.event_study_loop_b_results,
                "raw_data_available": ev.raw_data_available,
                "error_message": ev.error_message,
            }
            json_text = json.dumps(data, indent=2)
            (BASE_DIR / "four_gate_state.json").write_text(json_text, encoding="utf-8")
            (BASE_DIR / "dibse_state.json").write_text(json_text, encoding="utf-8")
            log_dir = BASE_DIR / "logs"
            if log_dir.exists():
                (log_dir / "four_gate_state.json").write_text(json_text, encoding="utf-8")
                (log_dir / "dibse_state.json").write_text(json_text, encoding="utf-8")
        except Exception as exc:
            logger.debug("Failed writing four_gate_state.json: %s", exc)


def copy_four_gate_to_clipboard(store: Any) -> Tuple[bool, str, int]:
    """Formats and copies the pure DATA-ONLY markdown telemetry packet for Tab 19 / DIBSE."""
    ev: Optional[FourGateEvaluation] = getattr(store, "four_gate_evaluation", None)
    if not ev:
        return False, "DIBSE evaluation not yet available.", 0

    lines = [
        "# BTC DIBSE QUANTITATIVE PROTOCOL TELEMETRY PACKET (TAB 19 / [Q])",
        f"**Protocol**: DUAL-INVENTORY BIDIRECTIONAL SWING ENGINE (DIBSE) | SPOT-ONLY",
        f"**Capital Sandbox**: ${ev.active_sandbox_usd:,.2f} (10% USDT Sleeve + 10% BTC Sleeve) | 80% Core Reserve (${ev.core_reserve_usd:,.2f})",
        f"**Timestamp UTC**: {ev.timestamp_utc}",
        f"**Live Spot**: ${ev.live_spot_price:,.2f} | **Last Closed 4H Bar**: {ev.last_closed_bar_utc}",
        f"**Active Inventory State**: {ev.inventory_state}",
        "",
        "## 1. SWING LOOP A: USDT SLEEVE (DIP HARVESTER — BUY LOW, SELL HIGH)",
        f"- Loop A Status: {ev.loop_a_status} | Verdict: {ev.loop_a_verdict} | Confluence: {ev.loop_a_score}/4",
        f"- Gate 1 [Rough Path Lévy Area A_SP]: {'PASS' if ev.loop_a_g1_levy else 'FAIL'} | Value: {ev.loop_a_g1_val:+.4f} (Rule: A_SP > 0.0)",
        f"- Gate 2 [Spot-Perp CVD Z-Spread]:    {'PASS' if ev.loop_a_g2_zflow else 'FAIL'} | Value: {ev.loop_a_g2_val:+.2f} (Rule: D_flow >= 1.0 & Spot24h > 0)",
        f"  - Details: z_S={ev.loop_a_g2_z_s:+.2f}, z_F={ev.loop_a_g2_z_f:+.2f}, Spot24h_Delta={ev.loop_a_g2_ds_24h:+,.1f} BTC",
        f"- Gate 3 [30D Volume Profile Support]: {'PASS' if ev.loop_a_g3_structure else 'FAIL'} | Active State: {ev.loop_a_g3_state}",
        f"  - POC_30: ${ev.gate_3_poc:,.1f} | VAL_30: ${ev.gate_3_val:,.1f} | VAH_30: ${ev.gate_3_vah:,.1f} | L20: ${ev.gate_3_l20:,.1f}",
        f"- Gate 4 [90D Funding Anti-Crowding]: {'PASS' if ev.loop_a_g4_positioning else 'FAIL'} | Rate: {ev.loop_a_g4_funding_rate * 100:+.4f}% | Percentile: {ev.loop_a_g4_funding_p90:.1f}%",
        f"  - Active Rule: {ev.loop_a_g4_details}",
        f"- Execution Ticket: Deploy ${ev.usdt_sleeve_usd:,.2f} USDT → Buy Spot BTC at ${ev.loop_a_entry_price:,.2f}",
        f"- Profit Target: ${ev.loop_a_target_price:,.2f} (+{ev.loop_a_target_pct * 100:.2f}%) | Projected Gain: +${ev.loop_a_expected_profit_usd:,.2f} USDT Cash",
        f"- Risk Mandate: {ev.loop_a_stop_rule}",
        "",
        "## 2. SWING LOOP B: BTC SLEEVE (DIAGNOSTIC TELEMETRY ONLY — G1 AUTO-SELL GATED OFF)",
        f"- Loop B Status: {ev.loop_b_status} | Verdict: {ev.loop_b_verdict} | Telemetry: {ev.loop_b_score}/4",
        f"- Gate 1 [Rough Path Lévy Area A_SP]: {'PASS' if ev.loop_b_g1_levy else 'FAIL'} | Value: {ev.loop_b_g1_val:+.4f} (Rule: A_SP < 0.0)",
        f"- Gate 2 [Spot-Perp CVD Z-Spread]:    {'PASS' if ev.loop_b_g2_zflow else 'FAIL'} | Value: {ev.loop_b_g2_val:+.2f} (Rule: D_flow <= -1.0 & Spot24h < 0)",
        f"  - Details: z_S={ev.loop_b_g2_z_s:+.2f}, z_F={ev.loop_b_g2_z_f:+.2f}, Spot24h_Delta={ev.loop_b_g2_ds_24h:+,.1f} BTC",
        f"- Gate 3 [30D Volume Profile Resistance]: {'PASS' if ev.loop_b_g3_structure else 'FAIL'} | Active State: {ev.loop_b_g3_state}",
        f"  - POC_30: ${ev.gate_3_poc:,.1f} | VAL_30: ${ev.gate_3_val:,.1f} | VAH_30: ${ev.gate_3_vah:,.1f} | H20: ${ev.loop_b_g3_h20:,.1f}",
        f"- Gate 4 [90D Funding Euphoria]:      {'PASS' if ev.loop_b_g4_positioning else 'FAIL'} | Rate: {ev.loop_b_g4_funding_rate * 100:+.4f}% | Percentile: {ev.loop_b_g4_funding_p90:.1f}%",
        f"  - Active Rule: {ev.loop_b_g4_details}",
        f"- Execution Ticket: Sell ~{ev.btc_sleeve_units:.4f} BTC (${ev.btc_sleeve_usd:,.2f}) at ${ev.loop_b_sell_price:,.2f}",
        f"- Buyback Target: ${ev.loop_b_buyback_price:,.2f} (-{ev.loop_b_discount_pct * 100:.2f}% discount)",
        f"- Satoshi Compounding: +{ev.loop_b_free_satoshis_btc:.6f} BTC (+{ev.loop_b_free_satoshis_pct:.2f}% Stack) OR +${ev.loop_b_surplus_cash_usd:,.2f} Surplus USDT Cash",
        f"- Risk Mandate: {ev.loop_b_stop_rule}",
        "",
        "## 3. IN-SAMPLE 90-DAY DE-CLUSTERED EVENT STUDY (5D EMBARGO)",
        f"- Loop A (Support Washouts): Triggers (N)={ev.event_study_triggers_count} | Small Sample: {'ACTIVE' if ev.event_study_small_sample else 'PASSED'}",
    ]

    esa = ev.event_study_results
    if esa and esa.get("count", 0) > 0:
        lines.extend([
            f"  - 1D Forward Return: Win Rate={esa.get('win_rate_1d', 0.0):.1f}%, Mean={esa.get('mean_ret_1d', 0.0):+.2f}% (Alpha {esa.get('alpha_1d', 0.0):+.2f}%)",
            f"  - 3D Forward Return: Win Rate={esa.get('win_rate_3d', 0.0):.1f}%, Mean={esa.get('mean_ret_3d', 0.0):+.2f}% (Alpha {esa.get('alpha_3d', 0.0):+.2f}%)",
            f"  - 5D Forward Return: Win Rate={esa.get('win_rate_5d', 0.0):.1f}%, Mean={esa.get('mean_ret_5d', 0.0):+.2f}% (Alpha {esa.get('alpha_5d', 0.0):+.2f}%)",
            f"  - 10D Forward Return: Win Rate={esa.get('win_rate_10d', 0.0):.1f}%, Mean={esa.get('mean_ret_10d', 0.0):+.2f}% (Alpha {esa.get('alpha_10d', 0.0):+.2f}%)",
        ])
    else:
        lines.append("  - No Loop A 4/4 triggers registered in lookback window.")

    esb = ev.event_study_loop_b_results
    lines.append(f"- Loop B (Resistance Rallies): Triggers (N)={ev.event_study_loop_b_triggers_count} | Small Sample: {'ACTIVE' if ev.event_study_loop_b_small_sample else 'PASSED'}")
    if esb and esb.get("count", 0) > 0:
        lines.extend([
            f"  - 1D Forward Buyback Yield: Win Rate={esb.get('win_rate_1d', 0.0):.1f}%, Mean={esb.get('mean_ret_1d', 0.0):+.2f}% (Alpha {esb.get('alpha_1d', 0.0):+.2f}%)",
            f"  - 3D Forward Buyback Yield: Win Rate={esb.get('win_rate_3d', 0.0):.1f}%, Mean={esb.get('mean_ret_3d', 0.0):+.2f}% (Alpha {esb.get('alpha_3d', 0.0):+.2f}%)",
            f"  - 5D Forward Buyback Yield: Win Rate={esb.get('win_rate_5d', 0.0):.1f}%, Mean={esb.get('mean_ret_5d', 0.0):+.2f}% (Alpha {esb.get('alpha_5d', 0.0):+.2f}%)",
            f"  - 10D Forward Buyback Yield: Win Rate={esb.get('win_rate_10d', 0.0):.1f}%, Mean={esb.get('mean_ret_10d', 0.0):+.2f}% (Alpha {esb.get('alpha_10d', 0.0):+.2f}%)",
        ])
    else:
        lines.append("  - No Loop B 4/4 triggers registered in lookback window.")

    packet = "\n".join(lines)
    char_count = len(packet)

    # Windows clipboard copy
    try:
        proc = subprocess.Popen(["clip"], stdin=subprocess.PIPE, shell=True)
        proc.communicate(input=packet.encode("utf-8"))
    except Exception:
        pass

    return True, "Copied Tab 19 DIBSE packet to clipboard.", char_count


# Canonical Aliases
copy_dibse_to_clipboard = copy_four_gate_to_clipboard
DibseEngine = FourGateEngine


if __name__ == "__main__":
    print("Testing FourGateEngine / DIBSE live fetch & math...")
    engine = FourGateEngine()
    spot_k, perp_k, fund_p, dvol_v = engine.fetch_primary_feeds()
    if spot_k and perp_k and fund_p and dvol_v is not None:
        ev = engine.calculate_evaluation(spot_k, perp_k, fund_p, dvol_v)
        engine.persist_state(ev)
        print(f"SUCCESS! Timestamp: {ev.timestamp_utc}")
        print(f"Capital: Active Sandbox=${ev.active_sandbox_usd:,.2f} | Reserve=${ev.core_reserve_usd:,.2f}")
        print(f"Loop A (Dip Harvester):  Score={ev.loop_a_score}/4 | Verdict={ev.loop_a_verdict}")
        print(f"Loop B (Rip Harvester):  Score={ev.loop_b_score}/4 | Verdict={ev.loop_b_verdict}")
        print(f"Loop A Triggers: {ev.event_study_triggers_count} | Loop B Triggers: {ev.event_study_loop_b_triggers_count}")
    else:
        print("API Fetch Failed -> DATA UNAVAILABLE")

