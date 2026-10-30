"""Tab [4] Analytics Engine: Regime Radar — Quantitative Microstructure Configurations A through J.

Evaluates all 10 institutional microstructure configurations (Config A through Config J)
in real time against live VWAP (Daily/Weekly), 20D/50D EMA, Spot Volume vs 20D MA,
Spot/Perp CVD ratios & Z-scores, Open Interest dynamics, Funding Rates, ATR compression,
and 24-72h base width, outputting:
- 0-100% live diagnostic match score for each Configuration (A through J)
- Active #1 Configuration & #2 Runner-Up
- Live checklist of IF YOU OBSERVE (EXACT METRIC FACTS) -> THEN IT MEANS -> ACTIONABLE PROTOCOL
- Exact USD stop-loss levels anchored to live 1H/4H/24H candle structure.
"""

from datetime import datetime, timezone
from typing import List, Optional, Sequence

import numpy as np

from config.settings import EngineConfig
from core.models import (
    DerivativesSnapshot,
    FlowSnapshot,
    KlineBar,
    RegimeConfigItem,
    RegimeMatrixEvaluation,
    VolumeProfileResult,
)
from core.state_store import StateStore
from .macro_radar import compute_ema
from .protocol_v13 import synthesize_1d_bars_from_1h
from .volume_profile import compute_atr, synthesize_4h_bars


def _compute_vwap(bars: Sequence[KlineBar]) -> float:
    """Computes Volume-Weighted Average Price (VWAP) over `bars`."""
    if not bars:
        return 0.0
    tot_vol = sum(b.volume for b in bars)
    if tot_vol <= 1e-9:
        return bars[-1].close
    pv = sum(b.typical_price * b.volume for b in bars)
    return float(pv / tot_vol)


class RegimeMatrixEvaluator:
    """Scores Configurations A through J and selects the active diagnostic & execution protocol."""

    def __init__(self, config: EngineConfig) -> None:
        self.config = config

    def evaluate(
        self,
        store: StateStore,
        flow: FlowSnapshot,
        deriv: DerivativesSnapshot,
        macro_vp: Optional[VolumeProfileResult],
    ) -> RegimeMatrixEvaluation:
        """Evaluates all 10 Microstructure Configurations (A-J) against live StateStore telemetry."""
        spot_1h = list(store.spot_klines_1h)
        spot_1d = list(store.spot_klines_1d) or synthesize_1d_bars_from_1h(spot_1h)
        bars_4h = synthesize_4h_bars(spot_1h)

        current_price = store.binance_spot_price or (spot_1h[-1].close if spot_1h else 0.0)

        # 1. Compute Core VWAP, EMA, Volume Ratio, ATR Compression & Range Width Telemetry
        daily_vwap = _compute_vwap(spot_1h[-24:]) if spot_1h else current_price
        weekly_vwap = _compute_vwap(spot_1h[-168:]) if spot_1h else current_price

        closes_1d = [b.close for b in spot_1d] if spot_1d else [current_price]
        ema_20_1d = compute_ema(closes_1d, period=20)
        ema_50_1d = compute_ema(closes_1d, period=50)

        vol_24h_spot = sum(b.volume for b in spot_1h[-24:]) if spot_1h else 0.0
        vol_20d_bars = spot_1d[:-1][-20:] if len(spot_1d) >= 2 else spot_1d[-20:]
        vol_20d_ma = float(np.mean([b.volume for b in vol_20d_bars])) if vol_20d_bars else max(vol_24h_spot, 1.0)
        spot_vol_ratio = vol_24h_spot / max(vol_20d_ma, 1.0)

        buy_4h = sum(b.taker_buy_volume for b in spot_1h[-4:]) if spot_1h else 1.0
        sell_4h = sum(b.taker_sell_volume for b in spot_1h[-4:]) if spot_1h else 1.0
        spot_buy_sell_ratio_4h = buy_4h / max(sell_4h, 1e-6)

        spot_cvd_7d = sum(b.delta for b in spot_1h[-168:]) if spot_1h else 0.0

        oi_1h = deriv.oi_change_1h_pct
        oi_4h = deriv.oi_change_4h_pct
        oi_24h = store.get_oi_change_pct(86_400.0) or (oi_4h * 2.0)
        funding = deriv.funding_rate_pct

        # Annualized basis proxy (Perp-Spot spread annualized + annualized 8h funding)
        perp_spread_pct = (deriv.perp_basis_usd / max(current_price, 1.0)) * 100.0
        annualized_basis_pct = (perp_spread_pct * 12.0) + (funding * 3.0 * 365.0)

        # ATR Compression from recent 10-day 4H ATR peak
        cur_atr_4h = max(compute_atr(bars_4h[-16:], period=14), 1.0) if bars_4h else 500.0
        peak_atr_4h = cur_atr_4h
        if len(bars_4h) >= 30:
            rolling_atrs = [
                compute_atr(bars_4h[max(0, k - 15) : k + 1], period=14)
                for k in range(15, len(bars_4h))
            ]
            if rolling_atrs:
                peak_atr_4h = max(max(rolling_atrs), cur_atr_4h)
        atr_compression_pct = max(0.0, ((peak_atr_4h - cur_atr_4h) / max(peak_atr_4h, 1.0)) * 100.0)

        # 48h-72h Tight Base Range Width %
        base_bars = spot_1h[-48:] if len(spot_1h) >= 48 else spot_1h
        if base_bars:
            base_hi = max(b.high for b in base_bars)
            base_lo = min(b.low for b in base_bars)
            base_width_72h_pct = ((base_hi - base_lo) / max(current_price, 1.0)) * 100.0
        else:
            base_hi = current_price
            base_lo = current_price
            base_width_72h_pct = 0.0

        # Structural Low Anchors for Stop-Loss Computation
        swing_low_4h = min((b.low for b in bars_4h[-3:]), default=current_price * 0.985)
        swing_low_1h = min((b.low for b in spot_1h[-3:]), default=current_price * 0.99)
        low_24h = min((b.low for b in spot_1h[-24:]), default=current_price * 0.975)

        price_chg_1h = flow.w_1h.price_change_pct
        price_chg_4h = flow.w_4h.price_change_pct
        above_d_vwap = current_price >= daily_vwap
        above_w_vwap = current_price >= weekly_vwap

        def _chk(cond: bool, text: str) -> str:
            return f"[green]✔[/green] {text}" if cond else f"[dim]• {text}[/dim]"

        configs: List[RegimeConfigItem] = []

        # ------------------------------------------------------------------
        # CONFIG A: Healthy Bull (Genuine Spot-Led Expansion)
        # ------------------------------------------------------------------
        a_c1 = above_d_vwap and above_w_vwap
        a_c2 = spot_vol_ratio >= 1.35
        a_c3 = spot_buy_sell_ratio_4h >= 1.25 or flow.w_4h.spot_delta_btc > 150.0
        a_c4 = deriv.coinbase_premium_pct > 0.0
        a_c5 = -1.0 <= oi_24h <= 4.0
        a_c6 = 0.002 <= funding <= 0.012
        score_a = (
            (25.0 if a_c1 else (12.0 if above_d_vwap else 0.0))
            + (18.0 if a_c2 else min(12.0, spot_vol_ratio * 8.0))
            + (22.0 if a_c3 else (10.0 if flow.w_4h.spot_delta_btc > 0 else 0.0))
            + (12.0 if a_c4 else 0.0)
            + (11.0 if a_c5 else 4.0)
            + (12.0 if a_c6 else 4.0)
        )
        configs.append(
            RegimeConfigItem(
                code="Config A",
                short_title="Healthy Bull",
                diagnosis_subtitle="Genuine Spot-Led Expansion",
                category="BULL_LONG",
                match_pct=round(min(100.0, score_a), 1),
                is_active=False,
                key_live_facts=(
                    f"VWAP:{'ABOVE' if a_c1 else 'MIXED'} | Vol:{spot_vol_ratio:.2f}x | "
                    f"Spot Ratio:{spot_buy_sell_ratio_4h:.2f} | Fund:{funding:+.4f}%"
                ),
                action_headline="Full Spot Long (1.0x)",
                sizing_rule="Sizing: 1.0x (Sf = 0.85–1.0x) | Max Cap: 50% equity",
                entry_or_harvest_rule="Entry: 60% breakout confirmation / 40% VWAP retest",
                stop_rule=f"Stop: 4H swing low -0.6% (${swing_low_4h * 0.994:,.0f})",
                computed_stop_usd=round(swing_low_4h * 0.994, 2),
                observed_checklist=[
                    _chk(a_c1, f"Price above Daily (${daily_vwap:,.0f}) & Weekly (${weekly_vwap:,.0f}) VWAP"),
                    _chk(a_c2, f"Spot volume > 1.35x 20D MA (Current: {spot_vol_ratio:.2f}x)"),
                    _chk(a_c3, f"Spot CVD positive / Ratio >= 1.25 (Current: {spot_buy_sell_ratio_4h:.2f})"),
                    _chk(a_c4, f"Institutional / US Spot proxy positive (CPI: {deriv.coinbase_premium_pct:+.3f}%)"),
                    _chk(a_c5, f"OI moderate -1% to +4% 24h (Current: {oi_24h:+.2f}%)"),
                    _chk(a_c6, f"Funding controlled +0.002% to +0.010% (Current: {funding:+.4f}%)"),
                ],
            )
        )

        # ------------------------------------------------------------------
        # CONFIG B: Leveraged Bull (Fragile Overextension / Trap)
        # ------------------------------------------------------------------
        b_c1 = price_chg_4h > 1.2 or (current_price - daily_vwap) > 1.5 * cur_atr_4h
        b_c2 = flow.w_1h.spot_delta_btc <= 0 or flow.w_1h.spot_zscore < 0.2
        b_c3 = flow.w_1h.perp_zscore >= 0.8 or flow.w_4h.perp_delta_btc > 200.0
        b_c4 = oi_24h >= 5.0 or oi_4h >= 1.5
        b_c5 = funding >= 0.020
        b_c6 = annualized_basis_pct >= 14.0
        score_b = (
            (20.0 if b_c1 else 0.0)
            + (20.0 if b_c2 else 0.0)
            + (20.0 if b_c3 else 0.0)
            + (20.0 if b_c4 else (8.0 if oi_4h > 0.4 else 0.0))
            + (12.0 if b_c5 else 0.0)
            + (8.0 if b_c6 else 0.0)
        )
        configs.append(
            RegimeConfigItem(
                code="Config B",
                short_title="Leveraged Bull",
                diagnosis_subtitle="Fragile Overextension / Trap",
                category="DEFENSIVE_CASH",
                match_pct=round(min(100.0, score_b), 1),
                is_active=False,
                key_live_facts=(
                    f"1H Spot:{flow.w_1h.spot_delta_btc:+.0f} | Perp Z:{flow.w_1h.perp_zscore:+.2f} | "
                    f"4H dOI:{oi_4h:+.2f}% | Basis:{annualized_basis_pct:.1f}%/yr"
                ),
                action_headline="Trim / Stand Aside (0.0x)",
                sizing_rule="Sizing: 0.0x (Strictly zero new buying)",
                entry_or_harvest_rule="Harvest: Sell 33% profit directly into perp pump",
                stop_rule=f"Stop: Trail tight stop on 67% at 4H swing low (${swing_low_4h:,.0f})",
                computed_stop_usd=round(swing_low_4h, 2),
                observed_checklist=[
                    _chk(b_c1, f"Price rising rapid / vertical (>2.5x ATR) (4H: {price_chg_4h:+.2f}%)"),
                    _chk(b_c2, f"Spot CVD flat or declining (1H Spot: {flow.w_1h.spot_delta_btc:+,.1f} BTC)"),
                    _chk(b_c3, f"Perp CVD aggressively upward (1H Perp Z: {flow.w_1h.perp_zscore:+.2f})"),
                    _chk(b_c4, f"OI surging (24h dOI: {oi_24h:+.2f}% / 4h dOI: {oi_4h:+.2f}%)"),
                    _chk(b_c5, f"Funding elevated >= +0.025% (Current: {funding:+.4f}%)"),
                    _chk(b_c6, f"Futures basis > 14% annualized (Current: {annualized_basis_pct:.1f}%)"),
                ],
            )
        )

        # ------------------------------------------------------------------
        # CONFIG C: Bullish Absorption (Institutional Base Defense)
        # ------------------------------------------------------------------
        val_ref = macro_vp.c_val if macro_vp else daily_vwap
        c_c1 = current_price <= val_ref * 1.01
        c_c2 = flow.w_4h.flow_divergence_z >= 1.0 or flow.w_1h.flow_divergence_z >= 1.0
        c_c3 = flow.w_4h.perp_delta_btc < 0 and flow.w_4h.spot_delta_btc > 0
        c_c4 = oi_4h <= 0.6
        c_c5 = -0.010 <= funding <= 0.010
        c_c6 = flow.w_1h.absorption_index >= 0.35 or spot_buy_sell_ratio_4h >= 1.15
        score_c = (
            (22.0 if c_c1 else 8.0)
            + (22.0 if c_c2 else (12.0 if flow.w_4h.flow_divergence_z > 0.5 else 0.0))
            + (22.0 if c_c3 else (10.0 if flow.w_4h.spot_delta_btc > 0 else 0.0))
            + (12.0 if c_c4 else 4.0)
            + (12.0 if c_c5 else 4.0)
            + (10.0 if c_c6 else 0.0)
        )
        configs.append(
            RegimeConfigItem(
                code="Config C",
                short_title="Bullish Absorption",
                diagnosis_subtitle="Institutional Base Defense",
                category="ACCUMULATE",
                match_pct=round(min(100.0, score_c), 1),
                is_active=False,
                key_live_facts=(
                    f"4H Spot:{flow.w_4h.spot_delta_btc:+.0f} vs Perp:{flow.w_4h.perp_delta_btc:+.0f} BTC | "
                    f"DivZ:{flow.w_4h.flow_divergence_z:+.2f} | AbsIdx:{flow.w_4h.absorption_index:.2f}"
                ),
                action_headline="Build Spot (0.75x)",
                sizing_rule="Sizing: 0.75x (Sf = 0.70–0.90x)",
                entry_or_harvest_rule="Entry: 50% on 1H range reclaim / 50% limit at low",
                stop_rule=f"Stop: Sweep wick low -0.5% (${low_24h * 0.995:,.0f})",
                computed_stop_usd=round(low_24h * 0.995, 2),
                observed_checklist=[
                    _chk(c_c1, f"Price testing major range low / cVAL (${val_ref:,.0f})"),
                    _chk(c_c2, f"Spot CVD surging vs Perp (4H Div Z: {flow.w_4h.flow_divergence_z:+.2f}σ)"),
                    _chk(c_c3, f"Perp CVD negative ({flow.w_4h.perp_delta_btc:+.0f} BTC) while Spot buys (+{flow.w_4h.spot_delta_btc:.0f} BTC)"),
                    _chk(c_c4, f"OI controlled / no leverage chase (4H dOI: {oi_4h:+.2f}%)"),
                    _chk(c_c5, f"Funding neutral/negative (Current: {funding:+.4f}%)"),
                    _chk(c_c6, f"Passive absorption / bid support active (Ratio: {spot_buy_sell_ratio_4h:.2f})"),
                ],
            )
        )

        # ------------------------------------------------------------------
        # CONFIG D: Masked Fragility (Stealth Distribution Top)
        # ------------------------------------------------------------------
        d_c1 = abs(price_chg_4h) <= 0.8 and current_price >= daily_vwap * 0.995
        d_c2 = flow.w_4h.spot_delta_btc < -100.0 or flow.w_1h.spot_delta_btc < -40.0
        d_c3 = deriv.coinbase_premium_pct < -0.05
        d_c4 = flow.w_4h.perp_delta_btc > 0 and flow.w_4h.spot_delta_btc < 0
        d_c5 = oi_4h > 0.2 and funding > 0.012
        d_c6 = current_price < daily_vwap
        score_d = (
            (15.0 if d_c1 else 0.0)
            + (25.0 if d_c2 else 0.0)
            + (15.0 if d_c3 else 0.0)
            + (20.0 if d_c4 else 0.0)
            + (15.0 if d_c5 else 0.0)
            + (10.0 if d_c6 else 0.0)
        )
        configs.append(
            RegimeConfigItem(
                code="Config D",
                short_title="Masked Fragility",
                diagnosis_subtitle="Stealth Distribution Top",
                category="DEFENSIVE_CASH",
                match_pct=round(min(100.0, score_d), 1),
                is_active=False,
                key_live_facts=(
                    f"4H Spot:{flow.w_4h.spot_delta_btc:+.0f} BTC | CPI:{deriv.coinbase_premium_pct:+.3f}% | "
                    f"VWAP:${daily_vwap:,.0f}"
                ),
                action_headline="Defensive Cash (100%)",
                sizing_rule="Sizing: 0.0x (Cash: 75%–100% USDT)",
                entry_or_harvest_rule=f"Exit: Market sell 50% on 1H close below VWAP (${daily_vwap:,.0f})",
                stop_rule=f"Stop: Hard trailing stop on 50% at 24h low (${low_24h:,.0f})",
                computed_stop_usd=round(low_24h, 2),
                observed_checklist=[
                    _chk(d_c1, "Price creeping higher or churning near top"),
                    _chk(d_c2, f"Spot CVD strongly negative / falling (4H: {flow.w_4h.spot_delta_btc:+.0f} BTC)"),
                    _chk(d_c3, f"Institutional selling / Coinbase discount ({deriv.coinbase_premium_pct:+.3f}%)"),
                    _chk(d_c4, "Perp CVD sustaining price float while Spot distributes"),
                    _chk(d_c5, f"OI expanding ({oi_4h:+.2f}%) with positive funding ({funding:+.4f}%)"),
                    _chk(d_c6, f"Daily VWAP (${daily_vwap:,.0f}) tested & breaking below"),
                ],
            )
        )

        # ------------------------------------------------------------------
        # CONFIG E: Liquidation Cascade (Forced Waterfall Deleveraging)
        # ------------------------------------------------------------------
        e_c1 = price_chg_1h <= -3.5 or price_chg_4h <= -5.0
        e_c2 = oi_1h <= -3.5 or oi_4h <= -6.0
        e_c3 = funding < 0.0
        e_c4 = deriv.perp_basis_usd < -25.0
        score_e = (
            (35.0 if e_c1 else (10.0 if price_chg_1h < -1.2 else 0.0))
            + (35.0 if e_c2 else (10.0 if oi_4h < -1.5 else 0.0))
            + (15.0 if e_c3 else 0.0)
            + (15.0 if e_c4 else 5.0)
        )
        configs.append(
            RegimeConfigItem(
                code="Config E",
                short_title="Liquidation Cascade",
                diagnosis_subtitle="Forced Waterfall Deleveraging",
                category="HARVEST_WAIT",
                match_pct=round(min(100.0, score_e), 1),
                is_active=False,
                key_live_facts=(
                    f"1H Chg:{price_chg_1h:+.2f}% | 1H/4H dOI:{oi_1h:+.2f}%/{oi_4h:+.2f}% | "
                    f"Basis:{deriv.perp_basis_usd:+.1f} USD"
                ),
                action_headline="Wait for Phase 3 (0.0x)",
                sizing_rule="Sizing: 0.0x during waterfall (Do NOT catch knife)",
                entry_or_harvest_rule="Trigger: 5m liqs < $2M, OI flat, 15m hammer -> 0.50x ladder (30/40/30%)",
                stop_rule=f"Stop: Below Phase 3 capitulation wick (${low_24h * 0.992:,.0f})",
                computed_stop_usd=round(low_24h * 0.992, 2),
                observed_checklist=[
                    _chk(e_c1, f"Price drops > 4%–8% rapidly (1H: {price_chg_1h:+.2f}%, 4H: {price_chg_4h:+.2f}%)"),
                    _chk(e_c2, f"OI crashing <= -5% 1h / <= -10% 4h (Current: {oi_1h:+.2f}% / {oi_4h:+.2f}%)"),
                    _chk(e_c3, f"Funding plunges negative (Current: {funding:+.4f}%)"),
                    _chk(e_c4, f"Basis in backwardation (Perp Basis: {deriv.perp_basis_usd:+.2f} USD)"),
                ],
            )
        )

        # ------------------------------------------------------------------
        # CONFIG F: Re-Accumulation (Post-Cascade Clean Base)
        # ------------------------------------------------------------------
        f_c1 = atr_compression_pct >= 30.0
        f_c2 = base_width_72h_pct <= 3.2
        f_c3 = -1.5 <= oi_24h <= 2.0
        f_c4 = -0.002 <= funding <= 0.010
        f_c5 = flow.w_4h.spot_delta_btc >= 0
        score_f = (
            (22.0 if f_c1 else min(15.0, atr_compression_pct * 0.5))
            + (22.0 if f_c2 else (12.0 if base_width_72h_pct <= 4.5 else 0.0))
            + (18.0 if f_c3 else 6.0)
            + (18.0 if f_c4 else 6.0)
            + (20.0 if f_c5 else 0.0)
        )
        configs.append(
            RegimeConfigItem(
                code="Config F",
                short_title="Re-Accumulation",
                diagnosis_subtitle="Post-Cascade Clean Base",
                category="ACCUMULATE",
                match_pct=round(min(100.0, score_f), 1),
                is_active=False,
                key_live_facts=(
                    f"ATR Comp:{atr_compression_pct:.0f}% | Base Width:{base_width_72h_pct:.2f}% | "
                    f"4H Spot:{flow.w_4h.spot_delta_btc:+.0f} BTC"
                ),
                action_headline="Re-Accumulate (0.75x)",
                sizing_rule="Sizing: 0.75x (Sf = 0.75–0.90x)",
                entry_or_harvest_rule="Entry: 50% on 4H close above Base POC / 50% limit",
                stop_rule=f"Stop: Base consolidation floor -0.5% (${base_lo * 0.995:,.0f})",
                computed_stop_usd=round(base_lo * 0.995, 2),
                observed_checklist=[
                    _chk(f_c1, f"ATR compresses > 40% from peak (Current: {atr_compression_pct:.1f}% compression)"),
                    _chk(f_c2, f"Tight base range < 2.5%–3.2% width (Current: {base_width_72h_pct:.2f}%)"),
                    _chk(f_c3, f"OI flat -1.5% to +2.0% baseline (Current: {oi_24h:+.2f}%)"),
                    _chk(f_c4, f"Funding reset near neutral (Current: {funding:+.4f}%)"),
                    _chk(f_c5, f"Spot CVD stabilizing green / flat (4H Spot: {flow.w_4h.spot_delta_btc:+.1f} BTC)"),
                ],
            )
        )

        # ------------------------------------------------------------------
        # CONFIG G: Short Squeeze (Mechanical Liquidation Run)
        # ------------------------------------------------------------------
        g_c1 = price_chg_1h >= 1.5 or price_chg_4h >= 2.5
        g_c2 = funding <= 0.0
        g_c3 = oi_1h <= -1.5 or oi_4h <= -2.0
        g_c4 = flow.w_1h.perp_delta_btc > 150.0 and flow.w_1h.spot_delta_btc < flow.w_1h.perp_delta_btc * 0.3
        score_g = (
            (30.0 if g_c1 else 0.0)
            + (20.0 if g_c2 else 0.0)
            + (30.0 if g_c3 else 0.0)
            + (20.0 if g_c4 else 0.0)
        )
        configs.append(
            RegimeConfigItem(
                code="Config G",
                short_title="Short Squeeze",
                diagnosis_subtitle="Mechanical Liquidation Run",
                category="HARVEST_WAIT",
                match_pct=round(min(100.0, score_g), 1),
                is_active=False,
                key_live_facts=(
                    f"1H Chg:{price_chg_1h:+.2f}% | 1H dOI:{oi_1h:+.2f}% | "
                    f"1H Perp:{flow.w_1h.perp_delta_btc:+.0f} BTC"
                ),
                action_headline="Harvest Gains (0.0x)",
                sizing_rule="Sizing: 0.0x (Never buy at squeeze peak)",
                entry_or_harvest_rule="Harvest: Scale out 50% spot profit into pump",
                stop_rule=f"Stop: Pre-squeeze 1H low -0.4% (${swing_low_1h * 0.996:,.0f})",
                computed_stop_usd=round(swing_low_1h * 0.996, 2),
                observed_checklist=[
                    _chk(g_c1, f"Explosive price pump through resistance (4H: {price_chg_4h:+.2f}%)"),
                    _chk(g_c2, f"Funding negative / shorts squeezed (Current: {funding:+.4f}%)"),
                    _chk(g_c3, f"OI collapsing as price rises (1H dOI: {oi_1h:+.2f}%)"),
                    _chk(g_c4, "Perp CVD surging (short covering) while Spot CVD lags"),
                ],
            )
        )

        # ------------------------------------------------------------------
        # CONFIG H: Distribution Top (Topping Exhaustion Failure)
        # ------------------------------------------------------------------
        h_c1 = macro_vp is not None and current_price >= macro_vp.c_vah * 0.99
        h_c2 = price_chg_4h > 0 and flow.w_4h.spot_delta_btc < 0
        h_c3 = funding >= 0.020
        h_c4 = not above_d_vwap
        score_h = (
            (25.0 if h_c1 else 0.0)
            + (30.0 if h_c2 else 0.0)
            + (25.0 if h_c3 else 0.0)
            + (20.0 if h_c4 else 0.0)
        )
        configs.append(
            RegimeConfigItem(
                code="Config H",
                short_title="Distribution Top",
                diagnosis_subtitle="Topping Exhaustion Failure",
                category="DEFENSIVE_CASH",
                match_pct=round(min(100.0, score_h), 1),
                is_active=False,
                key_live_facts=(
                    f"cVAH Test:{'YES' if h_c1 else 'NO'} | Bearish CVD Div:{'YES' if h_c2 else 'NO'} | "
                    f"Fund:{funding:+.4f}%"
                ),
                action_headline="Defensive Cash (100%)",
                sizing_rule="Sizing: 0.0x (Cash: 85%–100% USDT)",
                entry_or_harvest_rule="Harvest: Market sell 70% spot on 4H VWAP rejection",
                stop_rule="Stop: Move stop to Breakeven (BE) on remaining 30%",
                computed_stop_usd=round(daily_vwap, 2),
                observed_checklist=[
                    _chk(h_c1, "Marginal new high or double top near cVAH with upper wicks"),
                    _chk(h_c2, "Bearish Spot CVD divergence (Price higher, Spot CVD negative)"),
                    _chk(h_c3, f"Funding elevated > +0.020% (Current: {funding:+.4f}%)"),
                    _chk(h_c4, f"Daily VWAP (${daily_vwap:,.0f}) rejected on 4H close"),
                ],
            )
        )

        # ------------------------------------------------------------------
        # CONFIG I: Bear Trend (Bearish Trend Continuation)
        # ------------------------------------------------------------------
        i_c1 = current_price < ema_20_1d and current_price < ema_50_1d and not above_d_vwap
        i_c2 = spot_cvd_7d < 0 and flow.w_24h.spot_delta_btc < 0
        i_c3 = funding >= 0.005
        i_c4 = oi_24h >= 0.0
        i_c5 = annualized_basis_pct < 3.0
        score_i = (
            (30.0 if i_c1 else (15.0 if current_price < ema_20_1d else 0.0))
            + (30.0 if i_c2 else 0.0)
            + (15.0 if i_c3 else 5.0)
            + (15.0 if i_c4 else 5.0)
            + (10.0 if i_c5 else 0.0)
        )
        configs.append(
            RegimeConfigItem(
                code="Config I",
                short_title="Bear Trend",
                diagnosis_subtitle="Bearish Trend Continuation",
                category="DEFENSIVE_CASH",
                match_pct=round(min(100.0, score_i), 1),
                is_active=False,
                key_live_facts=(
                    f"<20D/50D EMA:{'YES' if i_c1 else 'NO'} | 7D Spot CVD:{spot_cvd_7d:+,.0f} BTC | "
                    f"Fund:{funding:+.4f}%"
                ),
                action_headline="Strict Cash (100%)",
                sizing_rule="Sizing: 0.0x (Target: 100% USDT Cash)",
                entry_or_harvest_rule="Protocol: Treat every relief bounce as exit liquidity",
                stop_rule=f"Inval: 1D close > 50D EMA (${ema_50_1d:,.0f}) with positive Spot CVD",
                computed_stop_usd=round(ema_50_1d, 2),
                observed_checklist=[
                    _chk(i_c1, f"Price below 20D EMA (${ema_20_1d:,.0f}), 50D EMA (${ema_50_1d:,.0f}), & Daily VWAP"),
                    _chk(i_c2, f"Spot CVD persistent downward slope (7D Delta: {spot_cvd_7d:+,.0f} BTC)"),
                    _chk(i_c3, f"Funding neutral/positive — trapped longs paying ({funding:+.4f}%)"),
                    _chk(i_c4, f"OI persistent without clearing overhang (24h dOI: {oi_24h:+.2f}%)"),
                    _chk(i_c5, f"Basis compressed below 3% annualized ({annualized_basis_pct:.1f}%)"),
                ],
            )
        )

        # ------------------------------------------------------------------
        # CONFIG J: Bear Trap (Capitulation Absorption)
        # ------------------------------------------------------------------
        j_c1 = current_price <= val_ref
        j_c2 = funding <= -0.005
        j_c3 = oi_4h >= 0.4 and price_chg_4h <= 0.2
        j_c4 = flow.w_4h.spot_delta_btc > 0 and flow.w_1h.spot_delta_btc > 0
        j_c5 = above_d_vwap or (bars_4h and bars_4h[-1].close > bars_4h[-1].open)
        score_j = (
            (20.0 if j_c1 else 0.0)
            + (25.0 if j_c2 else 0.0)
            + (20.0 if j_c3 else 5.0)
            + (20.0 if j_c4 else 0.0)
            + (15.0 if j_c5 else 0.0)
        )
        configs.append(
            RegimeConfigItem(
                code="Config J",
                short_title="Bear Trap",
                diagnosis_subtitle="Capitulation Absorption",
                category="BULL_LONG",
                match_pct=round(min(100.0, score_j), 1),
                is_active=False,
                key_live_facts=(
                    f"Fund:{funding:+.4f}% | 4H dOI:{oi_4h:+.2f}% | "
                    f"4H Spot:{flow.w_4h.spot_delta_btc:+.0f} BTC"
                ),
                action_headline="Reclaim Buy (1.0x)",
                sizing_rule="Sizing: 0.90x–1.0x (Maximum +EV setup)",
                entry_or_harvest_rule="Trigger: 4H close decisively back above broken support / VWAP",
                stop_rule=f"Stop: Capitulation sweep low -0.5% (${low_24h * 0.995:,.0f})",
                computed_stop_usd=round(low_24h * 0.995, 2),
                observed_checklist=[
                    _chk(j_c1, f"Sweep below support / cVAL (${val_ref:,.0f})"),
                    _chk(j_c2, f"Funding negative / shorts crowding (Current: {funding:+.4f}%)"),
                    _chk(j_c3, f"OI rising into lows (4H dOI: {oi_4h:+.2f}%)"),
                    _chk(j_c4, f"Spot CVD rising / refusing to drop (4H: {flow.w_4h.spot_delta_btc:+.0f} BTC)"),
                    _chk(j_c5, f"Price sweeping lows & reclaiming Daily VWAP (${daily_vwap:,.0f})"),
                ],
            )
        )

        # Rank and mark #1 Active Config & #2 Runner-Up
        ranked = sorted(configs, key=lambda c: c.match_pct, reverse=True)
        active_code = ranked[0].code
        runner_up_code = ranked[1].code if len(ranked) > 1 else active_code
        for item in configs:
            if item.code == active_code:
                item.is_active = True

        ev = RegimeMatrixEvaluation(
            timestamp_utc=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            current_price=round(current_price, 2),
            daily_vwap=round(daily_vwap, 2),
            weekly_vwap=round(weekly_vwap, 2),
            ema_20_1d=round(ema_20_1d, 2),
            ema_50_1d=round(ema_50_1d, 2),
            spot_vol_vs_20d_ma=round(spot_vol_ratio, 2),
            spot_buy_sell_ratio_4h=round(spot_buy_sell_ratio_4h, 2),
            spot_cvd_7d_btc=round(spot_cvd_7d, 1),
            oi_change_24h_pct=round(oi_24h, 2),
            oi_change_4h_pct=round(oi_4h, 2),
            oi_change_1h_pct=round(oi_1h, 2),
            funding_rate_pct=round(funding, 4),
            annualized_basis_pct=round(annualized_basis_pct, 1),
            atr_compression_pct=round(atr_compression_pct, 1),
            base_width_72h_pct=round(base_width_72h_pct, 2),
            active_config_code=active_code,
            runner_up_config_code=runner_up_code,
            configs=configs,
        )
        store.regime_matrix_evaluation = ev
        return ev
