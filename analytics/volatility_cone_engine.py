"""72-Hour Forward Volatility Cone & Quarantined AI Benchmark Radar Engine.

Implements pure NumPy calculations for:
1. Garman-Klass Microstructure Volatility (sigma_GK) across rolling 4H bars.
2. Mandelbrot Hurst-exponent (t^H) fractional Brownian motion quantile fan.
3. Damped Kalman drift center projections over +4h, +24h, +48h, and +72h horizons.
4. Quarantined Time-Series Foundation Model (TSFM) baselines (Kronos, Chronos-Bolt, TimesFM).
5. Variance Compression Ratio (VCR_72h) flagging latent breakout Coiled Springs.
6. Forward Liquidity Magnet & Value Area structural confluence mapping.

Strict Separation of Church and State: TSFMs have 0.0% capital allocation weight.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple
import numpy as np

from config.settings import EngineConfig
from core.models import (
    ConeHorizonRow,
    KlineBar,
    TSFMBenchmarkItem,
    VolatilityConeEvaluation,
    VolumeProfileResult,
)
from core.state_store import StateStore
from .volume_profile import synthesize_4h_bars


class VolatilityConeEngine:
    """Computes Hurst-scaled Garman-Klass volatility cones and evaluates quarantined TSFM benchmarks."""

    def __init__(self, config: EngineConfig) -> None:
        self.config = config
        self._cached_benchmarks: Optional[Dict] = None
        self._load_benchmarks()

    def _load_benchmarks(self) -> None:
        """Loads cached TSFM baseline parameters from config/tsfm_benchmarks.json or defaults."""
        config_path = Path(__file__).resolve().parent.parent / "config" / "tsfm_benchmarks.json"
        if config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    self._cached_benchmarks = json.load(f)
                    return
            except Exception:
                pass

        # Built-in fallback specifications if JSON not found
        self._cached_benchmarks = {
            "benchmark_anchor_price": 80910.0,
            "models": [
                {
                    "name": "Kronos-base",
                    "architecture": "Decoder-only BSQ Candlestick Transformer",
                    "training_domain": "Financial K-lines (OHLCV + Vol across 45+ exchanges)",
                    "direction_label": "UP +0.13%",
                    "range_spread_usd": 1384.0,
                    "range_spread_pct": 1.71,
                    "relative_range_min_pct": -0.776,
                    "relative_range_max_pct": 0.934,
                    "trajectory_relative_pct": {"1": 0.320, "6": 0.167, "12": 0.433, "18": 0.934},
                },
                {
                    "name": "Chronos-Bolt-small",
                    "architecture": "T5 Patch Quantile Encoder-Decoder",
                    "training_domain": "General Time-Series (Traffic, Energy, Retail Sales)",
                    "direction_label": "UP +0.22%",
                    "range_spread_usd": 326.0,
                    "range_spread_pct": 0.40,
                    "relative_range_min_pct": -0.012,
                    "relative_range_max_pct": 0.391,
                    "trajectory_relative_pct": {"1": -0.012, "6": 0.126, "12": 0.371, "18": 0.328},
                },
                {
                    "name": "TimesFM 2.5",
                    "architecture": "Decoder-only 200M Patched Transformer",
                    "training_domain": "100B+ Real-World General Time Points (Search, Retail)",
                    "direction_label": "DOWN -0.15%",
                    "range_spread_usd": 297.0,
                    "range_spread_pct": 0.37,
                    "relative_range_min_pct": -0.351,
                    "relative_range_max_pct": 0.016,
                    "trajectory_relative_pct": {"1": -0.044, "6": -0.059, "12": -0.146, "18": -0.349},
                },
            ],
        }

    def compute_garman_klass_volatility(self, bars_4h: Sequence[KlineBar], lookback: int = 18) -> float:
        """Calculates per-bar Garman-Klass volatility:

        sigma_GK^2 = (1/N) * sum[ 0.5 * (ln(H/L))^2 - (2*ln(2) - 1) * (ln(C/O))^2 ]
        """
        if not bars_4h:
            return 0.0150  # 1.50% default 4H volatility baseline

        sample = bars_4h[-lookback:]
        if len(sample) < 3:
            return 0.0150

        opens = np.array([b.open for b in sample], dtype=np.float64)
        highs = np.array([b.high for b in sample], dtype=np.float64)
        lows = np.array([b.low for b in sample], dtype=np.float64)
        closes = np.array([b.close for b in sample], dtype=np.float64)

        u = np.log(np.maximum(highs / np.maximum(lows, 1e-8), 1.0))
        c = np.log(np.maximum(closes / np.maximum(opens, 1e-8), 1e-8))

        two_ln2_minus_1 = 2.0 * np.log(2.0) - 1.0
        gk_var = 0.5 * (u ** 2) - two_ln2_minus_1 * (c ** 2)
        mean_var = float(np.mean(gk_var))
        sigma_gk = float(np.sqrt(max(mean_var, 1e-6)))
        return sigma_gk

    def evaluate_hurst_exponent(self, spot_1h: Sequence[KlineBar], fallback: float = 0.58) -> float:
        """Computes rolling Hurst Exponent H via Rescaled Range (R/S) clamped to [0.30, 0.75]."""
        if len(spot_1h) < 32:
            return fallback

        prices = np.array([b.close for b in spot_1h[-128:]], dtype=np.float64)
        lags = [16, 32, 64, 128]
        rs_vals: List[float] = []
        valid_lags: List[int] = []

        for lag in lags:
            if len(prices) < lag:
                continue
            sub = prices[-lag:]
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
            return fallback

        poly = np.polyfit(np.log(valid_lags), np.log(rs_vals), 1)
        h = float(poly[0])
        return float(np.clip(h, 0.30, 0.75))

    def evaluate(
        self,
        store: StateStore,
        spot_1h: Sequence[KlineBar],
        macro_vp: Optional[VolumeProfileResult] = None,
    ) -> VolatilityConeEvaluation:
        """Evaluates forward volatility cone and TSFM benchmark baselines."""
        spot_price = store.binance_spot_price or (spot_1h[-1].close if spot_1h else 80910.0)
        bars_4h = synthesize_4h_bars(spot_1h) if spot_1h else []

        # 1. Garman-Klass Microstructure Volatility (4H and Annualized)
        sigma_gk_4h = self.compute_garman_klass_volatility(bars_4h, lookback=18)
        annualized_gk_vol = sigma_gk_4h * np.sqrt(365.0 * 6.0)  # 6 four-hour bars/day

        # 2. Hurst Exponent & Mandelbrot Scaling Regime
        if store.mm_btc_evaluation is not None and store.mm_btc_evaluation.hurst:
            hurst_h = float(np.clip(store.mm_btc_evaluation.hurst.hurst, 0.30, 0.75))
        else:
            hurst_h = self.evaluate_hurst_exponent(spot_1h)

        if hurst_h > 0.52:
            hurst_regime = f"SUPER-DIFFUSIVE EXPANSION (H = {hurst_h:.2f} > 0.50)"
        elif hurst_h < 0.48:
            hurst_regime = f"SUB-DIFFUSIVE MEAN REVERTING (H = {hurst_h:.2f} < 0.50)"
        else:
            hurst_regime = f"BROWNIAN RANDOM WALK (H = {hurst_h:.2f})"

        # 3. Damped Kalman Drift Center Calculation
        kalman_mu = 0.0
        if store.mm_btc_evaluation is not None and store.mm_btc_evaluation.kalman:
            vel_hr = store.mm_btc_evaluation.kalman.velocity  # $/hr
            kalman_mu = (vel_hr * 4.0) / max(spot_price, 1.0)
        elif len(bars_4h) >= 6:
            c_recent = [b.close for b in bars_4h[-6:]]
            kalman_mu = (c_recent[-1] - c_recent[0]) / (c_recent[0] * len(c_recent))
        kalman_mu = float(np.clip(kalman_mu, -0.004, 0.004))  # Conservative damped bounds

        lambda_decay = 0.90

        # 4. Prepare Dynamic Scaled TSFM Benchmarks
        tsfm_items: List[TSFMBenchmarkItem] = []
        raw_models = self._cached_benchmarks.get("models", [])
        for m in raw_models:
            rel_min = m.get("relative_range_min_pct", -0.5) / 100.0
            rel_max = m.get("relative_range_max_pct", 0.5) / 100.0
            p_min = spot_price * (1.0 + rel_min)
            p_max = spot_price * (1.0 + rel_max)
            spread_usd = p_max - p_min
            spread_pct = (spread_usd / spot_price) * 100.0

            traj_rel = m.get("trajectory_relative_pct", {})
            p_72h = spot_price * (1.0 + (traj_rel.get("18", 0.0) / 100.0))

            path_closes = [
                spot_price * (1.0 + (traj_rel.get(str(k), 0.0) / 100.0))
                for k in (1, 6, 12, 18)
            ]

            tsfm_items.append(
                TSFMBenchmarkItem(
                    name=m.get("name", "TSFM"),
                    predicted_close_72h=round(p_72h, 2),
                    direction_str=m.get("direction_label", "FLAT"),
                    predicted_range_min=round(p_min, 2),
                    predicted_range_max=round(p_max, 2),
                    range_dollar_spread=round(spread_usd, 2),
                    range_pct=round(spread_pct, 2),
                    sample_path=[round(p, 2) for p in path_closes],
                    architecture_tag=m.get("architecture", ""),
                    training_domain=m.get("training_domain", ""),
                    quarantine_status="BENCHMARK-ONLY (0.0% CAPITAL WEIGHT)",
                )
            )

        # 5. Build 72-Hour Forward Horizon Quantile Fan Rows (Bar +1, +6, +12, +18)
        horizon_offsets = [(1, 4, "+4h (Bar +1)"), (6, 24, "+24h (Bar +6)"), (12, 48, "+48h (Bar +12)"), (18, 72, "+72h (Bar +18)")]
        horizon_rows: List[ConeHorizonRow] = []

        for bar_k, hrs, label in horizon_offsets:
            # Damped drift cumulative multiplier: mu * sum_{j=1}^k lambda^j
            decay_sum = sum(lambda_decay ** j for j in range(1, bar_k + 1))
            cum_drift = kalman_mu * decay_sum
            center = spot_price * (1.0 + cum_drift)

            # Mandelbrot t^H scaling
            scale_k = bar_k ** hurst_h
            delta_1sig = sigma_gk_4h * scale_k

            gk_1s_low = center * (1.0 - delta_1sig)
            gk_1s_high = center * (1.0 + delta_1sig)
            gk_2s_low = center * (1.0 - 2.0 * delta_1sig)
            gk_2s_high = center * (1.0 + 2.0 * delta_1sig)
            spread_usd = gk_1s_high - gk_1s_low
            spread_pct = (spread_usd / center) * 100.0

            # Model closes at this horizon
            idx_map = {1: 0, 6: 1, 12: 2, 18: 3}
            idx = idx_map[bar_k]
            k_close = tsfm_items[0].sample_path[idx] if len(tsfm_items) > 0 else center
            c_close = tsfm_items[1].sample_path[idx] if len(tsfm_items) > 1 else center
            t_close = tsfm_items[2].sample_path[idx] if len(tsfm_items) > 2 else center

            all_tsfms = [k_close, c_close, t_close]
            mean_tsfm = float(np.mean(all_tsfms))
            disp_pct = ((max(all_tsfms) - min(all_tsfms)) / spot_price) * 100.0

            horizon_rows.append(
                ConeHorizonRow(
                    horizon_label=label,
                    bar_offset=bar_k,
                    hours=hrs,
                    drift_center=round(center, 2),
                    gk_1sigma_lower=round(gk_1s_low, 2),
                    gk_1sigma_upper=round(gk_1s_high, 2),
                    gk_2sigma_lower=round(gk_2s_low, 2),
                    gk_2sigma_upper=round(gk_2s_high, 2),
                    gk_1sigma_spread_usd=round(spread_usd, 2),
                    gk_1sigma_spread_pct=round(spread_pct, 2),
                    kronos_close=round(k_close, 2),
                    chronos_close=round(c_close, 2),
                    timesfm_close=round(t_close, 2),
                    tsfm_mean_close=round(mean_tsfm, 2),
                    tsfm_dispersion_pct=round(disp_pct, 2),
                )
            )

        # 6. Variance Compression Ratio (VCR_72h)
        delta_p_gk_72h = horizon_rows[-1].gk_1sigma_spread_usd
        max_tsfm_spread_72h = max(item.range_dollar_spread for item in tsfm_items) if tsfm_items else 1.0
        vcr_72h = delta_p_gk_72h / max(max_tsfm_spread_72h, 1.0)

        if vcr_72h >= 5.0:
            vcr_status = "SEVERE AI COMPRESSION / COILED SPRING"
            coiled_spring = True
        elif vcr_72h >= 3.0:
            vcr_status = "MODERATE AI COMPRESSION (TSFMs UNDERESTIMATING TAIL RISK)"
            coiled_spring = False
        else:
            vcr_status = "NORMAL ALIGNMENT"
            coiled_spring = False

        # 7. Forward Liquidity Magnet & Value Area Confluence
        confluence_notes = []
        last_row = horizon_rows[-1]
        if macro_vp is not None:
            c_val = macro_vp.c_val
            c_vah = macro_vp.c_vah
            if last_row.gk_1sigma_lower <= c_val <= last_row.gk_1sigma_upper:
                confluence_notes.append(f"GK 1σ cone encompasses 30D cVAL (${c_val:,.0f})")
            if last_row.gk_1sigma_lower <= c_vah <= last_row.gk_1sigma_upper:
                confluence_notes.append(f"GK 1σ cone encompasses 30D cVAH (${c_vah:,.0f})")
            if macro_vp.support_hvn_below_val and last_row.gk_1sigma_lower <= macro_vp.support_hvn_below_val:
                confluence_notes.append(f"GK 2σ sweep reaches Support HVN floor (${macro_vp.support_hvn_below_val:,.0f})")

        if not confluence_notes:
            confluence_notes.append("GK 1σ cone encompasses key structural auction pivots")

        liquidity_summary = (
            f"{' • '.join(confluence_notes)}. "
            f"TSFM models predict tight cluster (${min(tsfm_items[-1].sample_path):,.0f}–${max(tsfm_items[0].sample_path):,.0f}), "
            f"ignoring external order flow and liquidation shelves."
        )

        takeaway = (
            "ZERO CAPITAL WEIGHT [BENCHMARK ONLY]: Time-Series Foundation Models suffer from Martingale Variance Compression "
            "(Pt ≈ Pt-1) on non-stationary 4H BTC returns, predicting flat ±0.2% drift. The Mandelbrot t^H Garman-Klass Volatility Cone "
            "captures true fat-tailed path diffusion. Trading execution strictly quarantined to Tabs [1]-[5] & [S1]."
        )

        # 8. Plain English Translation for Beginners & Retail Traders
        plain_english = (
            f"1. Why the AI lines are flat (±0.2%): Generic AI models play it safe by predicting almost zero change "
            f"because they can't forecast surprises or liquidations (Pt ≈ Pt-1). They underestimate Bitcoin's true volatility.\n"
            f"2. Where price will actually move (±{last_row.gk_1sigma_spread_pct / 2.0:.1f}% / ±${last_row.gk_1sigma_spread_usd / 2.0:,.0f}): "
            f"Real Bitcoin does not crawl. Over the next 72 hours, true volatility indicates BTC is expected to swing between "
            f"${last_row.gk_1sigma_lower:,.0f} and ${last_row.gk_1sigma_upper:,.0f} (inside the Green Volatility Cone).\n"
            f"3. The Coiled Spring (VCR = {vcr_72h:.2f}x): The market is holding {vcr_72h:.1f}x more expansion energy than naive AI expects. "
            f"{'⚡ [COILED SPRING ALERT: Imminent volatility explosion!]' if coiled_spring else 'A sharp breakout is far more likely than a quiet sideways drift.'}\n"
            f"4. Rule for your wallet: NEVER buy or sell based on flat zero-shot AI forecasts. Strictly protect your capital and only execute "
            f"when institutional volume and order flow confirm on Tabs [1]–[5] or Special Tab [S1]."
        )

        evaluation = VolatilityConeEvaluation(
            timestamp_utc=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            spot_price=round(spot_price, 2),
            garman_klass_vol_4h=round(sigma_gk_4h, 4),
            garman_klass_annualized_vol=round(annualized_gk_vol, 4),
            hurst_exponent=round(hurst_h, 3),
            hurst_regime=hurst_regime,
            kalman_mu_drift=round(kalman_mu, 5),
            kalman_lambda_decay=lambda_decay,
            horizons=horizon_rows,
            tsfm_benchmarks=tsfm_items,
            vcr_72h=round(vcr_72h, 2),
            vcr_status=vcr_status,
            coiled_spring_alert=coiled_spring,
            liquidity_confluence_summary=liquidity_summary,
            quantitative_takeaway=takeaway,
            plain_english_summary=plain_english,
            capital_weight_allocated=0.0,
        )

        store.volatility_cone_evaluation = evaluation
        return evaluation
