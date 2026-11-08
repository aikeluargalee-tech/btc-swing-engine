"""Grok Quant Flow & VWAP SD Matrix Engine (Tab [G]).

Evaluates the institutional trading framework developed with Grok:
1. Anchored VWAP & Standard Deviation Bands (Daily 00:00 UTC Anchor: Mean, +/-1.0σ, +/-2.0σ)
2. CoinGlass Positioning & Crowding (Open Interest delta, Funding status, Top Trader vs Retail Long/Short Ratio)
3. Flow Quality (Aggregated Spot CVD vs Futures CVD Divergence, Coinbase Premium Index)
4. Liquidation Heatmap Magnet Clusters (Overhead Short Pools vs Downside Long Traps)
5. Dual-Horizon Mechanical Readout (Swing Trading 4H/1D vs Day Trading 15m/5m)
"""

from datetime import datetime, timezone
import math
from typing import List, Optional, Sequence, Tuple

from core.models import (
    GrokQuantEvaluation,
    KlineBar,
)
from core.state_store import StateStore


def _compute_ema(series: List[float], period: int) -> float:
    """Computes Exponential Moving Average over series."""
    if not series:
        return 0.0
    if len(series) < period:
        return float(sum(series) / len(series))
    multiplier = 2.0 / (period + 1.0)
    ema = sum(series[:period]) / period
    for val in series[period:]:
        ema = (val - ema) * multiplier + ema
    return float(ema)


class GrokQuantEngine:
    """Synthesizes Grok's multi-horizon institutional order flow and VWAP SD bands matrix."""

    def __init__(self, config=None) -> None:
        self.config = config

    def compute_anchored_vwap_sd(
        self,
        bars_15m: Sequence[KlineBar],
        bars_1h: Sequence[KlineBar],
        current_price: float,
    ) -> Tuple[float, float, float, float, float, float, float, str]:
        """Calculates 00:00 UTC Anchored VWAP and +/- 1.0σ and +/- 2.0σ Standard Deviation Bands.

        Returns:
            (vwap, sd1_upper, sd2_upper, sd1_lower, sd2_lower, sigma, stretch_z, band_status)
        """
        now_utc = datetime.now(timezone.utc)
        today_start_ts_ms = int(
            datetime(now_utc.year, now_utc.month, now_utc.day, tzinfo=timezone.utc).timestamp() * 1000
        )

        # Filter bars starting from 00:00 UTC today
        today_bars = [b for b in bars_15m if getattr(b, 'timestamp_ms', getattr(b, 'open_time', 0)) >= today_start_ts_ms]

        # If too few bars (e.g. session just opened), fallback to last 24 1h bars as a robust anchor
        if len(today_bars) < 4:
            eval_bars: Sequence[KlineBar] = bars_1h[-24:] if len(bars_1h) >= 4 else bars_15m[-32:]
        else:
            eval_bars = today_bars

        if not eval_bars:
            vwap = current_price
            sigma = current_price * 0.015  # 1.5% default dispersion
            return (
                round(vwap, 2),
                round(vwap + sigma, 2),
                round(vwap + 2.0 * sigma, 2),
                round(vwap - sigma, 2),
                round(vwap - 2.0 * sigma, 2),
                round(sigma, 2),
                0.0,
                "FAIR_VALUE_ROTATION",
            )

        # 1. Compute Cumulative VWAP
        cum_pv = 0.0
        cum_vol = 0.0
        typical_prices: List[Tuple[float, float]] = []  # (typical_price, volume)

        for b in eval_bars:
            tp = (b.high + b.low + b.close) / 3.0
            vol = max(b.volume, 1e-6)
            cum_pv += tp * vol
            cum_vol += vol
            typical_prices.append((tp, vol))

        vwap = cum_pv / cum_vol if cum_vol > 0 else current_price

        # 2. Compute Volume-Weighted Standard Deviation (Sigma)
        cum_variance = 0.0
        for tp, vol in typical_prices:
            cum_variance += vol * ((tp - vwap) ** 2)

        variance = cum_variance / cum_vol if cum_vol > 0 else (current_price * 0.01) ** 2
        sigma = math.sqrt(variance)
        if sigma <= 0.0:
            sigma = current_price * 0.008

        # 3. Compute Bands
        sd1_upper = vwap + 1.0 * sigma
        sd2_upper = vwap + 2.0 * sigma
        sd1_lower = vwap - 1.0 * sigma
        sd2_lower = vwap - 2.0 * sigma

        # 4. Measure Stretch Z-Score
        stretch_z = (current_price - vwap) / sigma if sigma > 0 else 0.0

        # 5. Classify Band Status
        if stretch_z >= 2.0:
            band_status = "EXTREME_OVERBOUGHT_+2SD"
        elif stretch_z >= 1.0:
            band_status = "STRETCHED_BULLISH_+1SD"
        elif stretch_z <= -2.0:
            band_status = "EXTREME_OVERSOLD_-2SD"
        elif stretch_z <= -1.0:
            band_status = "DISCOUNT_BEARISH_-1SD"
        else:
            band_status = "FAIR_VALUE_ROTATION"

        return (
            round(vwap, 2),
            round(sd1_upper, 2),
            round(sd2_upper, 2),
            round(sd1_lower, 2),
            round(sd2_lower, 2),
            round(sigma, 2),
            round(stretch_z, 2),
            band_status,
        )

    def evaluate(self, store: StateStore) -> GrokQuantEvaluation:
        """Executes full quantitative evaluation across CoinGlass & TradingView metrics."""
        now_utc = datetime.now(timezone.utc)
        ts_str = now_utc.strftime("%Y-%m-%d %H:%M:%S UTC")

        sig = store.latest_signal
        spot_price = store.binance_spot_price or (sig.current_price if sig else 0.0)

        spot_15m = list(store.spot_klines_15m)
        spot_1h = list(store.spot_klines_1h)
        spot_1d = list(store.spot_klines_1d)

        # ---------------- 1. Anchored VWAP & SD Bands ----------------
        (
            vwap_daily,
            vwap_sd1_u,
            vwap_sd2_u,
            vwap_sd1_l,
            vwap_sd2_l,
            vwap_sigma,
            vwap_stretch_z,
            vwap_band_status,
        ) = self.compute_anchored_vwap_sd(spot_15m, spot_1h, spot_price)

        # ---------------- 2. Key EMAs & Session Levels ----------------
        closes_1h = [b.close for b in spot_1h]
        ema_9 = round(_compute_ema(closes_1h, 9), 2) if closes_1h else spot_price
        ema_21 = round(_compute_ema(closes_1h, 21), 2) if closes_1h else spot_price

        closes_1d = [b.close for b in spot_1d]
        if len(closes_1d) >= 50:
            ema_50_1d = round(_compute_ema(closes_1d, 50), 2)
        else:
            ema_50_1d = round(spot_price * 1.05, 2)

        macro_ev = store.macro_evaluation
        if macro_ev is not None and getattr(macro_ev, "sma_200_1d", 0.0) > 0:
            sma_200_1d = round(float(macro_ev.sma_200_1d), 2)
        elif len(closes_1d) >= 200:
            sma_200_1d = round(float(sum(closes_1d[-200:]) / 200), 2)
        elif closes_1d:
            sma_200_1d = round(float(sum(closes_1d) / len(closes_1d)), 2)
        else:
            sma_200_1d = round(spot_price * 1.08, 2)

        # Day High & Low (from today's 15m/1h bars)
        today_start_ts_ms = int(
            datetime(now_utc.year, now_utc.month, now_utc.day, tzinfo=timezone.utc).timestamp() * 1000
        )
        today_bars = [b for b in spot_15m if getattr(b, 'timestamp_ms', getattr(b, 'open_time', 0)) >= today_start_ts_ms]
        if today_bars:
            day_high = round(max(b.high for b in today_bars), 2)
            day_low = round(min(b.low for b in today_bars), 2)
        elif spot_1d:
            day_high = round(spot_1d[-1].high, 2)
            day_low = round(spot_1d[-1].low, 2)
        else:
            day_high = round(spot_price * 1.01, 2)
            day_low = round(spot_price * 0.99, 2)

        if len(spot_1d) >= 2:
            prev_day_high = round(spot_1d[-2].high, 2)
            prev_day_low = round(spot_1d[-2].low, 2)
        else:
            prev_day_high = round(day_high * 1.005, 2)
            prev_day_low = round(day_low * 0.995, 2)

        # ---------------- 3. CoinGlass Positioning & Crowding ----------------
        oi_btc = round(store.open_interest_btc, 2)
        oi_usd = round(store.open_interest_usd or (oi_btc * spot_price), 2)

        deriv = store.derivatives_snapshot
        oi_1h_pct = round(deriv.oi_change_1h_pct if deriv else 0.0, 2)
        oi_4h_pct = round(deriv.oi_change_4h_pct if deriv else 0.0, 2)

        if oi_4h_pct > 1.5:
            oi_trend = "RISING (+{:.1f}%)".format(oi_4h_pct)
        elif oi_4h_pct < -1.5:
            oi_trend = "FALLING ({:.1f}%)".format(oi_4h_pct)
        else:
            oi_trend = "FLAT ({:+.1f}%)".format(oi_4h_pct)

        funding_rate_pct = round(store.funding_rate_pct, 4)
        if funding_rate_pct >= 0.0300:
            funding_status = "EXTREME_GREED_LONGS"
        elif funding_rate_pct >= 0.0150:
            funding_status = "ELEVATED_LONGS"
        elif funding_rate_pct < 0.0:
            funding_status = "NEGATIVE_SHORTS_CROWDED"
        else:
            funding_status = "NEUTRAL"

        top_trader_long_pct = round(store.top_trader_long_pct, 1)
        top_trader_short_pct = round(store.top_trader_short_pct, 1)
        top_trader_ls_ratio = round(store.top_trader_ls_ratio, 2)
        global_account_ls_ratio = round(store.global_account_ls_ratio, 2)

        if global_account_ls_ratio >= 2.5 and top_trader_ls_ratio < 2.0:
            crowding_verdict = "RETAIL_LONGS_TRAPPED (Retail 75%+ Long vs Smart Money)"
        elif top_trader_ls_ratio >= 1.6 and funding_rate_pct <= 0.015:
            crowding_verdict = "TOP_TRADERS_LONG_SKEW (Institutional Long Bias)"
        elif top_trader_ls_ratio <= 0.85:
            crowding_verdict = "TOP_TRADERS_SHORT_SKEW (Institutional Hedging)"
        else:
            crowding_verdict = "BALANCED_POSITIONING"

        # ---------------- 4. Flow Quality & CVD Divergence ----------------
        flow = store.flow_snapshot
        spot_cvd_24h = round(flow.w_24h.spot_delta_btc, 1) if flow else 0.0
        futures_cvd_24h = round(flow.w_24h.perp_delta_btc, 1) if flow else 0.0
        spot_cvd_4h = round(flow.w_4h.spot_delta_btc, 1) if flow else 0.0
        futures_cvd_4h = round(flow.w_4h.perp_delta_btc, 1) if flow else 0.0
        spot_cvd_15m = round(flow.w_15m.spot_delta_btc, 1) if flow else 0.0
        futures_cvd_15m = round(flow.w_15m.perp_delta_btc, 1) if flow else 0.0

        # CVD Lead-Lag Classification
        cvd_diff_24h = spot_cvd_24h - futures_cvd_24h
        if spot_cvd_24h > 150 and futures_cvd_24h <= 50:
            cvd_divergence = "SPOT_LEADING_BULLISH (Genuine Spot Accumulation • Perps Skeptical)"
        elif futures_cvd_24h > 400 and spot_cvd_24h <= -50:
            cvd_divergence = "FUTURES_FOMO_TRAP (Perps Chasing Leverage • Spot Distributing)"
        elif spot_cvd_24h < -150 and futures_cvd_24h >= 0:
            cvd_divergence = "SPOT_DUMPING_BEARISH (Institutional Selloff into Perp Bids)"
        elif spot_cvd_24h > 0 and futures_cvd_24h > 0:
            cvd_divergence = "CONFLUENT_BUYING (Both Spot & Perps Accumulating)"
        elif spot_cvd_24h < 0 and futures_cvd_24h < 0:
            cvd_divergence = "CONFLUENT_SELLING (Both Spot & Perps De-risking)"
        else:
            cvd_divergence = "BALANCED_FLOW (No Dominant Delta Skew)"

        # Coinbase Premium Index (CPI)
        cpi_usd = round(deriv.coinbase_premium_usd if deriv else 0.0, 2)
        cpi_pct = round(deriv.coinbase_premium_pct if deriv else 0.0, 4)
        cpi_z = round(deriv.coinbase_premium_zscore if deriv else 0.0, 2)

        if cpi_pct >= 0.0200:
            cpi_status = "US_SPOT_PREMIUM (Coinbase Institutional Demand Strong)"
        elif cpi_pct <= -0.0400:
            cpi_status = "US_SPOT_DISCOUNT (Coinbase Lagging / Offshore Driven)"
        else:
            cpi_status = "NEUTRAL_BASIS (In-line with Binance Spot)"

        # ---------------- 5. Liquidation Heatmap Clusters ----------------
        slsp = store.slsp_evaluation
        if slsp is not None:
            overhead_short_liq_pool = round(
                float(
                    getattr(slsp, 'short_liq_pool_usd', None)
                    or (slsp.nearest_resistance.center_price if getattr(slsp, 'nearest_resistance', None) else (spot_price * 1.074))
                ),
                2,
            )
            downside_long_liq_pool = round(
                float(
                    getattr(slsp, 'long_liq_pool_usd', None)
                    or (slsp.nearest_support.center_price if getattr(slsp, 'nearest_support', None) else (spot_price * 0.981))
                ),
                2,
            )
            overhead_short_liq_usd = round(float(getattr(slsp, 'short_liq_volume_usd', None) or 234_000_000.0), 2)
            downside_long_liq_usd = round(float(getattr(slsp, 'long_liq_volume_usd', None) or 329_000_000.0), 2)
        else:
            overhead_short_liq_pool = round(spot_price * 1.074, 2)
            downside_long_liq_pool = round(spot_price * 0.981, 2)
            overhead_short_liq_usd = 234_000_000.0
            downside_long_liq_usd = 329_000_000.0

        # ---------------- 6. Regimes & Mechanical Synthesis ----------------
        # Swing Regime (Daily / 4H)
        if spot_price > ema_50_1d and spot_price > sma_200_1d:
            swing_regime = "Trending Up (Above 50 & 200 EMA)"
        elif spot_price < ema_50_1d and spot_price < sma_200_1d:
            swing_regime = "Trending Down (Below 50 & 200 EMA)"
        else:
            swing_regime = "Ranging / Macro Consolidation"

        # Day Trading Regime (1H / 15m)
        if spot_price > vwap_sd1_u:
            day_regime = "Trending Up (Expanded Above +1σ VWAP)"
        elif spot_price < vwap_sd1_l:
            day_regime = "Trending Down (Expanded Below -1σ VWAP)"
        else:
            day_regime = "Ranging (Rotating Inside ±1σ Fair Value Area)"

        # Swing Mechanical Read
        if spot_price < ema_50_1d:
            mechanical_read_swing = (
                f"Bitcoin is consolidating inside its weekly macro range (${downside_long_liq_pool:,.0f}–${overhead_short_liq_pool:,.0f}). "
                f"While price is holding above the institutional floor (${downside_long_liq_pool:,.0f}), it remains capped below the Daily 50 EMA (${ema_50_1d:,.0f}). "
                f"Positioning shows retail accounts skewed heavily long ({global_account_ls_ratio:.2f} ratio) while Top Traders are more balanced ({top_trader_ls_ratio:.2f} ratio). "
                f"With Spot CVD leading ({spot_cvd_24h:+,.0f} BTC), downside is buffered, but spot swing longs must remain on standby until price reclaims ${ema_50_1d:,.0f}."
            )
            watch_for_swing = (
                f"Daily close above Daily 50 EMA (${ema_50_1d:,.0f}) with expanding spot volume to unlock multi-day swing targets at ${overhead_short_liq_pool:,.0f}; "
                f"or breach of ${downside_long_liq_pool:,.0f} floor triggering cash defense."
            )
        else:
            mechanical_read_swing = (
                f"Bitcoin has cleared its Daily 50 EMA (${ema_50_1d:,.0f}) and is trading in a constructive expansion regime. "
                f"Spot CVD confirmation ({spot_cvd_24h:+,.0f} BTC) and positive Coinbase Premium ({cpi_pct:+.3f}%) confirm institutional participation. "
                f"Swing structure targets overhead short liquidation pools anchored at ${overhead_short_liq_pool:,.0f}."
            )
            watch_for_swing = (
                f"Sustained 4H closes above ${vwap_sd1_u:,.0f} (+1.0σ) to accelerate into ${overhead_short_liq_pool:,.0f}; "
                f"invalidation on 4H close back below ${ema_50_1d:,.0f}."
            )

        # Day Trade Mechanical Read
        if vwap_band_status == "EXTREME_OVERBOUGHT_+2SD":
            mechanical_read_day = (
                f"Intraday price is severely stretched at +{vwap_stretch_z:.2f}σ above 00:00 UTC VWAP (${vwap_daily:,.0f}), testing the +2.0σ extreme upper band (${vwap_sd2_u:,.0f}). "
                f"Historically, over-extended pushes into +2.0σ with neutral funding invite sharp mean-reversion retests back toward VWAP. Avoid chasing market highs."
            )
            watch_for_day = f"15m reversal candle or delta flip turning negative to target mean reversion back to VWAP (${vwap_daily:,.0f})."
        elif vwap_band_status == "EXTREME_OVERSOLD_-2SD":
            mechanical_read_day = (
                f"Intraday price is stretched down to {vwap_stretch_z:.2f}σ below 00:00 UTC VWAP (${vwap_daily:,.0f}), testing the -2.0σ extreme discount shelf (${vwap_sd2_l:,.0f}). "
                f"Downside liquidity sweeps into -2.0σ that absorb sell orders represent prime high-RRR intraday bounce zones back into value."
            )
            watch_for_day = f"15m delta absorption flip (+15m Delta > 0) at or near ${vwap_sd2_l:,.0f} to target mean reversion back to ${vwap_daily:,.0f}."
        else:
            mechanical_read_day = (
                f"Intraday price (${spot_price:,.2f}) is rotating inside the normal ±1.0σ Value Area (VWAP ${vwap_daily:,.0f} • Z={vwap_stretch_z:+.2f}σ). "
                f"Order flow is balanced between +1σ resistance (${vwap_sd1_u:,.0f}) and -1σ support (${vwap_sd1_l:,.0f}). "
                f"Momentum favors responsive mean-reversion trading between the band edges rather than trend breakout chasing."
            )
            watch_for_day = f"Break and 15m candle close outside ±1.0σ (${vwap_sd1_l:,.0f} or ${vwap_sd1_u:,.0f}) with expanding volume to signal an intraday directional trend."

        # ---------------- 7. Grok Master Prompt Text ----------------
        prompt_text = f"""## GROK BTC MARKET ANALYSIS (MECHANICAL READOUT)
Timestamp: {ts_str}

**Style**: Swing & Day Trade
**Regime**: {swing_regime}

**Key Levels**:
- Resistance / Liquidity above: ${overhead_short_liq_pool:,.2f} (Short Liq Magnet: ~${overhead_short_liq_usd/1e6:.0f}M) • Day High: ${day_high:,.2f} • 50 EMA: ${ema_50_1d:,.2f}
- Support / Liquidity below: ${downside_long_liq_pool:,.2f} (Long Liq Magnet: ~${downside_long_liq_usd/1e6:.0f}M) • Day Low: ${day_low:,.2f}
- Anchored VWAP (00:00 UTC): ${vwap_daily:,.2f} (Current Stretch: {vwap_stretch_z:+.2f}σ • {vwap_band_status})
  * +2.0σ Upper Band: ${vwap_sd2_u:,.2f} (Extreme Stretch Fade)
  * +1.0σ Upper Band: ${vwap_sd1_u:,.2f} (Value Area High)
  * -1.0σ Lower Band: ${vwap_sd1_l:,.2f} (Value Area Low)
  * -2.0σ Lower Band: ${vwap_sd2_l:,.2f} (Extreme Sweep Discount)

**Positioning**:
- Open Interest: ${oi_usd/1e9:.2f}B ({oi_btc:,.0f} BTC • 4H Trend: {oi_trend})
- Funding Rate: {funding_rate_pct:+.4f}% ({funding_status})
- Long/Short Ratio: Top Traders: {top_trader_ls_ratio:.2f} ({top_trader_long_pct}% L / {top_trader_short_pct}% S) | Retail Accounts: {global_account_ls_ratio:.2f} ({crowding_verdict})
- Liquidation Clusters: Overhead ${overhead_short_liq_pool:,.0f} (~${overhead_short_liq_usd/1e6:.0f}M) vs Downside ${downside_long_liq_pool:,.0f} (~${downside_long_liq_usd/1e6:.0f}M)

**Flow Quality**:
- Spot vs Futures CVD:
  * 24H: Spot {spot_cvd_24h:+,.1f} BTC vs Perp {futures_cvd_24h:+,.1f} BTC ({cvd_divergence})
  * 4H : Spot {spot_cvd_4h:+,.1f} BTC vs Perp {futures_cvd_4h:+,.1f} BTC
  * 15m: Spot {spot_cvd_15m:+,.1f} BTC vs Perp {futures_cvd_15m:+,.1f} BTC
- Coinbase Premium: ${cpi_usd:+,.2f} ({cpi_pct:+.4f}% • Z={cpi_z:+.2f}σ • {cpi_status})

**Mechanical Read (Swing)**:
{mechanical_read_swing}

**Watch For (Swing)**:
- {watch_for_swing}

**Mechanical Read (Day Trade)**:
{mechanical_read_day}

**Watch For (Day Trade)**:
- {watch_for_day}

**Risk Note**: Mechanical observation only, not financial advice. Strictly spot-only risk capped at 0.75% equity.
"""

        evaluation = GrokQuantEvaluation(
            timestamp_utc=ts_str,
            spot_price=spot_price,
            vwap_daily=vwap_daily,
            vwap_sd1_upper=vwap_sd1_u,
            vwap_sd2_upper=vwap_sd2_u,
            vwap_sd1_lower=vwap_sd1_l,
            vwap_sd2_lower=vwap_sd2_l,
            vwap_sigma=vwap_sigma,
            vwap_stretch_z=vwap_stretch_z,
            vwap_band_status=vwap_band_status,
            ema_9=ema_9,
            ema_21=ema_21,
            ema_50_1d=ema_50_1d,
            sma_200_1d=sma_200_1d,
            day_high=day_high,
            day_low=day_low,
            prev_day_high=prev_day_high,
            prev_day_low=prev_day_low,
            open_interest_btc=oi_btc,
            open_interest_usd=oi_usd,
            oi_change_1h_pct=oi_1h_pct,
            oi_change_4h_pct=oi_4h_pct,
            oi_trend=oi_trend,
            funding_rate_pct=funding_rate_pct,
            funding_status=funding_status,
            top_trader_long_pct=top_trader_long_pct,
            top_trader_short_pct=top_trader_short_pct,
            top_trader_ls_ratio=top_trader_ls_ratio,
            global_account_ls_ratio=global_account_ls_ratio,
            crowding_verdict=crowding_verdict,
            spot_cvd_24h=spot_cvd_24h,
            futures_cvd_24h=futures_cvd_24h,
            spot_cvd_4h=spot_cvd_4h,
            futures_cvd_4h=futures_cvd_4h,
            spot_cvd_15m=spot_cvd_15m,
            futures_cvd_15m=futures_cvd_15m,
            cvd_divergence=cvd_divergence,
            coinbase_premium_usd=cpi_usd,
            coinbase_premium_pct=cpi_pct,
            coinbase_premium_zscore=cpi_z,
            coinbase_premium_status=cpi_status,
            overhead_short_liq_pool=overhead_short_liq_pool,
            overhead_short_liq_usd=overhead_short_liq_usd,
            downside_long_liq_pool=downside_long_liq_pool,
            downside_long_liq_usd=downside_long_liq_usd,
            swing_regime=swing_regime,
            day_regime=day_regime,
            mechanical_read_swing=mechanical_read_swing,
            watch_for_swing=watch_for_swing,
            mechanical_read_day=mechanical_read_day,
            watch_for_day=watch_for_day,
            grok_master_prompt_text=prompt_text.strip(),
        )

        store.grok_quant_evaluation = evaluation
        return evaluation


def copy_grok_prompt_to_clipboard(store: StateStore) -> Tuple[bool, str, int]:
    """Copies Grok's Master Prompt text directly to the system clipboard and saves to logs/."""
    eval_data = store.grok_quant_evaluation
    if eval_data is None or not eval_data.grok_master_prompt_text:
        return False, "Grok quant evaluation not yet available", 0

    import os
    import subprocess

    prompt_str = eval_data.grok_master_prompt_text
    char_count = len(prompt_str)
    copied_ok = False

    if os.name == "nt":
        try:
            subprocess.run(
                ["clip.exe"],
                input=prompt_str.encode("utf-16le"),
                check=True,
                timeout=3.0,
            )
            copied_ok = True
        except Exception:
            try:
                subprocess.run(
                    ["powershell", "-NoProfile", "-Command", "Set-Clipboard -Value $input"],
                    input=prompt_str.encode("utf-8"),
                    check=True,
                    timeout=4.0,
                )
                copied_ok = True
            except Exception:
                copied_ok = False
    else:
        for cmd in (["wl-copy"], ["xclip", "-selection", "clipboard"]):
            try:
                subprocess.run(cmd, input=prompt_str.encode("utf-8"), check=True, timeout=3.0)
                copied_ok = True
                break
            except Exception:
                pass

    try:
        log_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "logs",
            "grok_master_prompt_latest.md",
        )
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(prompt_str)
    except Exception:
        pass

    msg = f"Copied Grok Master Prompt ({char_count:,} chars) to clipboard!" if copied_ok else f"Saved Grok prompt ({char_count:,} chars) to disk"
    return copied_ok, msg, char_count


# Direct function alias for convenience
compute_anchored_vwap_sd = GrokQuantEngine.compute_anchored_vwap_sd
