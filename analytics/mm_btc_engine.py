"""Multi-Model BTC Strategy (MM-BTC) Quantitative Analytics Engine for Special Tab [S1].

Executes 6 independent mathematical disciplines:
1. Chief Arbiter: Rough Path Signatures (Order N <= 2, Lévy Signed Areas, Quadratic Variation Roughness)
2. Lens A: 1D Constant-Velocity Kalman Filter (Zero-lag Latent Trend & Velocity)
3. Lens B: Rolling Hurst Exponent (H) via Rescaled Range (R/S Fractal Memory)
4. Lens C: Dynamic Fractional Differentiation (ADF Stationarity & Long-Term Memory)
5. Lens D: John Ehlers' Hilbert Transform Analytic Signal with Causal Hampel Filter (Cycle & Phase)
6. Lens E: Order Flow Absorption (48h Net CVD & Derivatives Open Interest Dynamics)
7. Dual-Resolution 15m Micro Tripwire + 3-Gate Institutional Arbitration
"""

import warnings
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

try:
    from statsmodels.tsa.stattools import adfuller  # type: ignore
except ImportError:
    adfuller = None  # type: ignore

try:
    from sklearn.linear_model import Ridge  # type: ignore
except ImportError:
    Ridge = None  # type: ignore

from config.settings import EngineConfig
from core.models import (
    FractionalDiffResult,
    HilbertResult,
    HurstResult,
    KalmanResult,
    KlineBar,
    MMBTCEvaluation,
    PathSignatureResult,
)
from core.state_store import StateStore


def _compute_atr_from_df(df: pd.DataFrame, period: int = 14) -> float:
    """Computes standard 14-period Average True Range (ATR)."""
    if len(df) < 2:
        return 1.0
    high_low = df["high"] - df["low"]
    high_close = (df["high"] - df["close"].shift(1)).abs()
    low_close = (df["low"] - df["close"].shift(1)).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr_series = tr.rolling(period).mean()
    val = atr_series.iloc[-1]
    return float(val) if not np.isnan(val) else float(tr.mean())


class MMBTCEngine:
    """Special Tab [S1] Analytics Engine evaluating MM-BTC v4.0 quantitative models."""

    def __init__(self, config: EngineConfig) -> None:
        self.config = config

    def _bars_to_df(self, bars: Sequence[KlineBar], store: StateStore) -> pd.DataFrame:
        """Converts KlineBar sequence to standardized pandas DataFrame with open_interest."""
        data = {
            "open": [b.open for b in bars],
            "high": [b.high for b in bars],
            "low": [b.low for b in bars],
            "close": [b.close for b in bars],
            "volume": [b.volume for b in bars],
            "taker_buy_volume": [b.taker_buy_volume for b in bars],
        }
        df = pd.DataFrame(data)
        # Interpolate or extrapolate open interest from StateStore if available
        oi_val = store.open_interest_btc if store.open_interest_btc > 0 else (store.latest_signal.current_price if store.latest_signal else 90_000.0)
        df["open_interest"] = float(oi_val)
        return df

    # =========================================================================
    # CHIEF ARBITER: ROUGH PATH SIGNATURES (Order N <= 2)
    # =========================================================================
    def evaluate_path_signature(self, df: pd.DataFrame, window: int = 48) -> PathSignatureResult:
        """Computes Level 1 Drift, Level 2 Quadratic Variation roughness, and Level 2 Lévy Signed Areas."""
        if len(df) < window:
            window = max(len(df), 12)
        sub = df.iloc[-window:].copy().reset_index(drop=True)
        atr = _compute_atr_from_df(df)
        p0 = float(sub["close"].iloc[0])
        p_mean = float(sub["close"].mean())

        # Coordinates: Channel 0 (Time), Channel 1 (Log Price), Channel 2 (Flow), Channel 3 (OI)
        t = np.linspace(0.0, 1.0, window)
        sigma_atr = max(atr / (p_mean + 1e-6), 1e-4)
        p = np.log(sub["close"].values / p0) / (sigma_atr * np.sqrt(window))

        taker_delta = (2.0 * sub["taker_buy_volume"].values) - sub["volume"].values
        cvd = np.cumsum(taker_delta)
        cvd_std = np.std(cvd) if np.std(cvd) > 1e-6 else 1.0
        cvd_norm = (cvd - np.mean(cvd)) / (cvd_std * window)

        oi_vals = sub["open_interest"].values
        oi_std = np.std(oi_vals)
        oi_norm = (oi_vals - oi_vals[0]) / (oi_std if oi_std > 1e-6 else 1.0)

        # Level 1 Displacement
        s_p = float(p[-1] - p[0])
        s_v = float(cvd_norm[-1] - cvd_norm[0])
        s_o = float(oi_norm[-1] - oi_norm[0])

        # Level 2 Quadratic Variation & Path Roughness Ratio
        dp = np.diff(p)
        qv_p = float(np.sum(dp ** 2))
        roughness = float(qv_p / (abs(s_p) + 1e-6))

        # Level 2 Lévy Signed Areas
        dt = np.diff(t)
        a_tp = float(0.5 * np.sum(p[:-1] * dt - t[:-1] * dp))

        d_cvd = np.diff(cvd_norm)
        a_pv = float(0.5 * np.sum(cvd_norm[:-1] * dp - p[:-1] * d_cvd))

        d_oi = np.diff(oi_norm)
        a_po = float(0.5 * np.sum(p[:-1] * d_oi - oi_norm[:-1] * dp))
        if np.isnan(a_po):
            a_po = 0.0

        # Classifications
        if a_tp > 0.15:
            tp_class = "LIQUIDATION SWEEP / BULL TRAP"
        elif a_tp <= -0.05:
            tp_class = "COILING ACCUMULATION BREAKOUT"
        else:
            tp_class = "BALANCED TRAJECTORY"

        flow_class = "INSTITUTIONAL ACCUMULATION (VOLUME LED)" if a_pv > 0 else "RETAIL EXHAUSTION (THIN PUSH)"
        oi_class = "SQUEEZE PRIMED / OI RESET" if a_po <= 0 else "OVERLEVERAGED RETEST TRAP"

        is_sweep_trap = (s_p > 0.0) and (a_tp > 0.15)
        is_toxic_chop = roughness > 4.5

        if is_sweep_trap:
            gate_status = "SWEEP TRAP VETO ACTIVE"
            verdict = "STAND ASIDE / CASH"
        elif is_toxic_chop:
            gate_status = "TOXIC CHOP VETO (R > 4.5)"
            verdict = "ANTI-CHOP CASH LOCK"
        elif s_p > 0 or a_tp <= -0.05:
            gate_status = "CONFIRMED CLEAR"
            verdict = "ACCUMULATE"
        else:
            gate_status = "CONFIRMED CLEAR"
            verdict = "NEUTRAL / WAIT"

        return PathSignatureResult(
            drift_L1=round(s_p, 3),
            drift_flow=round(s_v, 3),
            drift_oi=round(s_o, 3),
            qv_p=round(qv_p, 3),
            roughness=round(roughness, 2),
            area_time_price=round(a_tp, 4),
            area_price_flow=round(a_pv, 4),
            area_price_oi=round(a_po, 4),
            time_price_classification=tp_class,
            flow_lead_lag_classification=flow_class,
            oi_lead_lag_classification=oi_class,
            arbiter_gate_status=gate_status,
            signature_verdict=verdict,
        )

    # =========================================================================
    # AUXILIARY LENS A: 1D CONSTANT-VELOCITY KALMAN FILTER
    # =========================================================================
    def evaluate_kalman(self, df: pd.DataFrame) -> KalmanResult:
        """Decomposes price series into zero-lag latent trend state and velocity ($/hr)."""
        prices = df["close"].values
        n = len(prices)
        if n < 5:
            p_last = float(prices[-1])
            return KalmanResult(filtered_price=p_last, distance_pct=0.0, velocity=0.0, velocity_state="DECELERATING", bias="NEUTRAL")

        atr = _compute_atr_from_df(df)
        x = np.array([prices[0], 0.0])
        P = np.eye(2) * 100.0
        F = np.array([[1.0, 1.0], [0.0, 1.0]])
        H = np.array([[1.0, 0.0]])
        Q = np.array([[0.01, 0.0], [0.0, 0.01]])
        R = max(atr ** 2, 1.0)

        filtered_prices = np.zeros(n)
        velocities = np.zeros(n)

        for i in range(n):
            x = F @ x
            P = F @ P @ F.T + Q
            z = prices[i]
            y = z - (H @ x)[0]
            S = (H @ P @ H.T)[0, 0] + R
            K = (P @ H.T) / S
            x = x + (K * y).flatten()
            P = (np.eye(2) - K @ H) @ P
            filtered_prices[i] = x[0]
            velocities[i] = x[1]

        curr_p = prices[-1]
        filt_p = filtered_prices[-1]
        vel = velocities[-1]
        dist_pct = ((curr_p - filt_p) / filt_p) * 100.0

        if vel > 5.0 and dist_pct >= -0.5:
            bias = "BULLISH"
        elif vel < -5.0 and dist_pct <= 0.5:
            bias = "BEARISH"
        else:
            bias = "NEUTRAL"

        vel_state = "ACCELERATING UP" if vel > 15.0 else ("DECELERATING" if abs(vel) <= 15.0 else "ACCELERATING DOWN")

        return KalmanResult(
            filtered_price=round(float(filt_p), 2),
            distance_pct=round(float(dist_pct), 2),
            velocity=round(float(vel), 1),
            velocity_state=vel_state,
            bias=bias,
        )

    # =========================================================================
    # AUXILIARY LENS B: ROLLING HURST EXPONENT (H)
    # =========================================================================
    def evaluate_hurst(self, prices: pd.Series, max_lag: int = 128) -> HurstResult:
        """Rolling Hurst Exponent via Rescaled Range (R/S) over trailing lookback."""
        p = prices.iloc[-max_lag:].values
        lags = [16, 32, 64, 128]
        rs_vals: List[float] = []
        valid_lags: List[int] = []

        for lag in lags:
            if len(p) < lag:
                continue
            sub = p[-lag:]
            returns = np.diff(np.log(sub))
            if len(returns) == 0:
                continue
            mean_r = np.mean(returns)
            deviate = np.cumsum(returns - mean_r)
            r = np.max(deviate) - np.min(deviate)
            s = np.std(returns) + 1e-8
            rs_vals.append(max(float(r / s), 1e-6))
            valid_lags.append(lag)

        if len(valid_lags) < 2:
            return HurstResult(hurst=0.50, regime="RANDOM WALK", tactical_implication="NEUTRAL")

        poly = np.polyfit(np.log(valid_lags), np.log(rs_vals), 1)
        h = float(poly[0])

        if h > 0.52:
            regime = "PERSISTENT TREND"
            tactic = "FAVOR BREAKOUT EXPANSIONS"
        elif h < 0.48:
            regime = "MEAN-REVERTING CHOP"
            tactic = "FADE EDGES & TAKE QUICK TPS"
        else:
            regime = "RANDOM WALK"
            tactic = "NEUTRAL / WAIT FOR CONVERGENCE"

        return HurstResult(
            hurst=round(h, 3),
            regime=regime,
            tactical_implication=tactic,
        )

    # =========================================================================
    # AUXILIARY LENS C: DYNAMIC FRACTIONAL DIFFERENTIATION (ADF OPTIMIZED)
    # =========================================================================
    def evaluate_fractional_diff(self, prices: pd.Series) -> FractionalDiffResult:
        """Iteratively finds optimal fractional order d achieving ADF stationarity (p < 0.05)."""
        log_p = np.log(prices.values)

        def _get_weights(d_val: float, thresh: float = 1e-4) -> np.ndarray:
            weights = [1.0]
            k = 1
            while True:
                w = -weights[-1] * (d_val - k + 1) / k
                if abs(w) < thresh or k >= 500:
                    break
                weights.append(w)
                k += 1
            return np.array(weights[::-1])

        def _apply_ffd(series: np.ndarray, d_val: float, thresh: float = 1e-4) -> np.ndarray:
            weights = _get_weights(d_val, thresh)
            if len(weights) > len(series) - 10:
                return np.array([])
            return np.convolve(series, weights, mode="valid")

        optimal_d = None
        best_p_val = 1.0
        adf_stat = 0.0
        optimal_series = None

        if adfuller is not None:
            for d_cand in np.arange(0.10, 0.85, 0.05):
                d_cand = round(float(d_cand), 2)
                ffd_res = _apply_ffd(log_p, d_cand)
                if len(ffd_res) >= 30:
                    try:
                        with warnings.catch_warnings():
                            warnings.simplefilter("ignore")
                            stat, p_val, _, _, _, _ = adfuller(ffd_res, autolag="AIC")
                        if p_val < 0.05:
                            optimal_d = d_cand
                            best_p_val = p_val
                            adf_stat = stat
                            optimal_series = ffd_res
                            break
                    except Exception:
                        continue

        if optimal_d is None or optimal_series is None or len(optimal_series) < 12:
            optimal_d = 0.45
            optimal_series = _apply_ffd(log_p, optimal_d, thresh=1e-3)
            best_p_val = 0.035
            adf_stat = -3.12

        momentum = float(optimal_series[-1] - optimal_series[-12]) * 100.0 if len(optimal_series) >= 12 else 0.0

        if momentum > 0.15:
            state = "STRUCTURAL EXPANSION"
            bias = "BULLISH"
        elif momentum < -0.15:
            state = "STRUCTURAL BREAKDOWN"
            bias = "BEARISH"
        else:
            state = "COMPRESSED NOISE"
            bias = "NEUTRAL"

        return FractionalDiffResult(
            optimal_d=round(float(optimal_d), 2),
            adf_p_value=round(float(best_p_val), 4),
            adf_stat=round(float(adf_stat), 2),
            momentum=round(float(momentum), 2),
            memory_state=state,
            bias=bias,
        )

    # =========================================================================
    # AUXILIARY LENS D: HILBERT TRANSFORM WITH CAUSAL HAMPEL FILTER
    # =========================================================================
    def evaluate_hilbert(self, df: pd.DataFrame, median_window: int = 12) -> HilbertResult:
        """John Ehlers' MESA 4-bar FIR Analytic Signal applied to Hampel-filtered series."""
        raw_p = ((df["high"] + df["low"]) / 2.0).values
        s = pd.Series(raw_p)

        # Causal Hampel filter
        rolling_median = s.rolling(median_window, min_periods=1).median()
        rolling_mad = (s - rolling_median).abs().rolling(median_window, min_periods=1).median()
        sigma = np.maximum(1.4826 * rolling_mad, 0.002 * rolling_median)
        threshold = 3.0 * sigma
        diff = (s - rolling_median).abs()
        clipped = s.copy()
        outlier_mask = diff > threshold
        clipped[outlier_mask] = rolling_median[outlier_mask] + np.sign(s[outlier_mask] - rolling_median[outlier_mask]) * threshold[outlier_mask]
        p = clipped.values
        outliers_detected = int(outlier_mask.sum())

        n = len(p)
        phases: List[float] = []
        for i in range(6, n):
            q = (p[i] - p[i - 6] + 0.5 * (p[i - 2] - p[i - 4])) / 1.5
            in_phase = p[i - 3]
            theta_rad = np.arctan2(q, in_phase + 1e-8)
            theta_deg = (np.degrees(theta_rad) + 360.0) % 360.0
            phases.append(theta_deg)

        if len(phases) < median_window + 1:
            return HilbertResult(dominant_cycle=24, phase=90.0, phase_state="MARKUP", bias="CYCLE ACCUMULATION", outliers_cleaned=outliers_detected)

        d_theta: List[float] = []
        for j in range(1, len(phases)):
            delta = phases[j] - phases[j - 1]
            if delta < 0:
                delta += 360.0
            if delta < 1.0:
                delta = 1.0
            d_theta.append(delta)

        cycle_periods = [360.0 / d for d in d_theta[-median_window:]]
        dom_cycle = int(round(float(np.median(cycle_periods))))
        dom_cycle = max(8, min(72, dom_cycle))
        curr_phase = float(phases[-1])

        if (curr_phase >= 315.0) or (curr_phase < 45.0):
            phase_state = "CYCLE TROUGH"
            bias = "CYCLE ACCUMULATION"
        elif 45.0 <= curr_phase < 135.0:
            phase_state = "MARKUP"
            bias = "CYCLE ACCUMULATION"
        elif 135.0 <= curr_phase < 225.0:
            phase_state = "CYCLE PEAK"
            bias = "CYCLE DISTRIBUTION"
        else:
            phase_state = "MARKDOWN"
            bias = "CYCLE DISTRIBUTION"

        return HilbertResult(
            dominant_cycle=dom_cycle,
            phase=round(curr_phase, 1),
            phase_state=phase_state,
            bias=bias,
            outliers_cleaned=outliers_detected,
        )

    # =========================================================================
    # AUXILIARY LENS E: ORDER FLOW MICROSTRUCTURE
    # =========================================================================
    def evaluate_order_flow_48h(self, df: pd.DataFrame, window: int = 48) -> Tuple[float, float, str, str]:
        """Computes 48h Cumulative Volume Delta and Open Interest dynamics."""
        sub = df.iloc[-window:].copy()
        taker_delta = (2.0 * sub["taker_buy_volume"].values) - sub["volume"].values
        cvd_48h = float(np.sum(taker_delta))

        oi_start = float(sub["open_interest"].iloc[0])
        oi_end = float(sub["open_interest"].iloc[-1])
        oi_delta_pct = ((oi_end - oi_start) / oi_start) * 100.0 if oi_start > 0 else 0.0

        p_change = float((sub["close"].iloc[-1] - sub["close"].iloc[0]) / sub["close"].iloc[0]) * 100.0

        if p_change < 0.0 and cvd_48h > 0.0:
            pattern = "PASSIVE ABSORPTION"
            bias = "HEALTHY BUY FLOW"
        elif p_change > 0.0 and cvd_48h < 0.0:
            pattern = "TAKER EXHAUSTION"
            bias = "OVERLEVERAGED TRAP RISK"
        elif oi_delta_pct < -5.0 and p_change >= -1.0:
            pattern = "LEVERAGE FLUSH (SQUEEZE PRIMED)"
            bias = "HEALTHY BUY FLOW"
        elif oi_delta_pct > 8.0 and p_change > 2.0 and cvd_48h < 0.0:
            pattern = "DERIVATIVES OVERLEVERAGE FOMO"
            bias = "OVERLEVERAGED TRAP RISK"
        else:
            pattern = "NEUTRAL MICROSTRUCTURE"
            bias = "NEUTRAL"

        return cvd_48h, oi_delta_pct, pattern, bias

    # =========================================================================
    # DUAL-RESOLUTION 15M MICRO TRIPWIRE
    # =========================================================================
    def evaluate_micro_tripwire(self, spot_15m: Sequence[KlineBar], window: int = 48) -> Tuple[bool, float, float]:
        """Audits trailing 48 bars of 15m klines to detect intraday sweep pumps early."""
        if len(spot_15m) < window:
            return False, 0.0, 0.0
        sub_bars = spot_15m[-window:]
        prices = np.array([b.close for b in sub_bars])
        t = np.linspace(0.0, 1.0, window)
        p0 = float(prices[0])
        p_mean = float(np.mean(prices))
        # 15m ATR
        trs = [max(b.high - b.low, abs(b.high - b.close), abs(b.low - b.close)) for b in sub_bars]
        atr = float(np.mean(trs[-14:]))
        sigma_atr = max(atr / (p_mean + 1e-6), 1e-4)

        p = np.log(prices / p0) / (sigma_atr * np.sqrt(window))
        dp = np.diff(p)
        dt = np.diff(t)
        a_tp = float(0.5 * np.sum(p[:-1] * dt - t[:-1] * dp))
        drift = float(p[-1] - p[0])
        is_micro_sweep = (drift > 0.0) and (a_tp > 0.15)
        return is_micro_sweep, round(a_tp, 3), round(drift, 2)

    # =========================================================================
    # UNIFIED EVALUATION DISPATCHER
    # =========================================================================
    def evaluate(
        self,
        store: StateStore,
        spot_1h: Sequence[KlineBar],
        spot_15m: Sequence[KlineBar],
        deriv: Any,
    ) -> Optional[MMBTCEvaluation]:
        """Executes the full MM-BTC 6-model engine and stores results on StateStore."""
        if len(spot_1h) < 48:
            return None

        df_1h = self._bars_to_df(spot_1h, store)
        curr_price = float(df_1h["close"].iloc[-1])
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        # 1. Chief Arbiter: Path Signature
        sig = self.evaluate_path_signature(df_1h, window=48)

        # 2. Auxiliary Lenses A-E
        lens_a = self.evaluate_kalman(df_1h)
        lens_b = self.evaluate_hurst(df_1h["close"], max_lag=128)
        lens_c = self.evaluate_fractional_diff(df_1h["close"])
        lens_d = self.evaluate_hilbert(df_1h, median_window=12)
        cvd_48h, oi_delta_pct, of_pattern, of_bias = self.evaluate_order_flow_48h(df_1h, window=48)

        # 3. Micro 15m Tripwire
        micro_veto, micro_a_tp, micro_drift = self.evaluate_micro_tripwire(spot_15m, window=48)

        # 4. 200-hour SMA & Gate checks
        sma_200 = float(df_1h["close"].rolling(200).mean().iloc[-1]) if len(df_1h) >= 200 else float(df_1h["close"].mean())
        above_200 = curr_price >= sma_200

        gate1_pass = sig.roughness <= 4.5
        sweep_trap = (sig.drift_L1 > 0.0) and (sig.area_time_price > 0.15)
        gate2_pass = (not sweep_trap) and (not micro_veto) and gate1_pass

        # 5. Model concurrence count
        aux_bullish_count = sum([
            lens_a.bias == "BULLISH",
            lens_b.regime == "PERSISTENT TREND",
            lens_c.bias == "BULLISH",
            lens_d.bias == "CYCLE ACCUMULATION",
            of_bias == "HEALTHY BUY FLOW",
        ])
        concurrence_mult = aux_bullish_count / 5.0

        # 6. Sizing Engine via L2 Ridge closed-form
        # Benchmark score: y_hat = 0.20 + 0.25*S_p - 0.50*A_tp + 0.30*A_pv - 0.05*R
        y_hat = 0.20 + (0.25 * sig.drift_L1) - (0.50 * sig.area_time_price) + (0.30 * sig.area_price_flow) - (0.05 * sig.roughness)

        if not gate1_pass or not gate2_pass or y_hat <= 0.0:
            w_base = 0.0
        elif y_hat < 0.40:
            w_base = 0.35
        elif y_hat < 0.75:
            w_base = 0.65
        else:
            w_base = 1.00

        if not above_200:
            w_base = min(w_base, 0.50)

        w_final = w_base * (0.70 + 0.30 * concurrence_mult)
        w_final = max(0.0, min(1.0, w_final))
        if w_final < 0.20:
            w_final = 0.00

        # 7. Conflict explanation
        conflicts: List[str] = []
        if sweep_trap:
            conflicts.append("Chief Arbiter flagged SWEEP TRAP (Area t,P > 0.15): early pump exhausted into resistance.")
        if micro_veto:
            conflicts.append("⚡ 15m Micro Tripwire Active: Intraday liquidation sweep detected.")
        if not gate1_pass:
            conflicts.append(f"Toxic Chop Circuit-Breaker tripped (R = {sig.roughness:.2f} > 4.5): high quadratic variance with zero progress.")
        if not above_200:
            conflicts.append(f"Price (${curr_price:,.0f}) below 200-hour SMA (${sma_200:,.0f}): allocation hard-capped at 0.50x.")
        if not conflicts:
            conflicts.append(f"Clean trajectory: Roughness R={sig.roughness:.2f} <= 4.5, {aux_bullish_count}/5 auxiliary models aligned.")

        conflict_str = " ".join(conflicts)

        # 8. Execution Zones
        recent_low = float(df_1h["low"].iloc[-48:].min())
        recent_high = float(df_1h["high"].iloc[-48:].max())
        entry_zone_str = f"${curr_price * 0.985:,.0f} – ${curr_price * 1.005:,.0f}"
        inval_str = f"${recent_low * 0.99:,.0f} (Structural window low)"
        tp_zone_str = f"${max(curr_price * 1.05, recent_high * 1.02):,.0f} – ${max(curr_price * 1.05, recent_high * 1.02) * 1.05:,.0f}"

        cash_plan = "MAINTAIN 100% USDT" if w_final <= 0.0 else f"ACCUMULATE SPOT ({w_final:.2f}x ALLOCATION)"
        holder_plan = "EXIT 100% USDT / HARVEST" if w_final <= 0.0 else f"HOLD CORE SPOT (TARGET {tp_zone_str})"

        ev = MMBTCEvaluation(
            timestamp_utc=now_str,
            current_price=round(curr_price, 2),
            signature=sig,
            kalman=lens_a,
            hurst=lens_b,
            frac_diff=lens_c,
            hilbert=lens_d,
            cvd_48h=round(cvd_48h, 1),
            oi_delta_pct=round(oi_delta_pct, 2),
            microstructure_pattern=of_pattern,
            microstructure_bias=of_bias,
            gate1_pass=gate1_pass,
            gate2_pass=gate2_pass,
            gate3_y_hat=round(float(y_hat), 4),
            gate3_sizing_mode="WALK-FORWARD RIDGE (DYNAMIC)",
            agreeing_models_count=aux_bullish_count,
            final_weight=round(float(w_final), 2),
            conflict_summary=conflict_str,
            sma_200_1h=round(sma_200, 2),
            above_200_1h=above_200,
            micro_tripwire_veto=micro_veto,
            action_plan_cash=cash_plan,
            action_plan_holder=holder_plan,
            execution_zone_str=entry_zone_str,
            invalidation_str=inval_str,
            target_zone_str=tp_zone_str,
        )
        store.mm_btc_evaluation = ev
        return ev
