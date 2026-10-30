"""Tab [2] Analytics Engine: BTC Spot Swing Protocol v1.3 & CoinGlass 6-Panel Audit.

Strictly obeys Protocol v1.3 rules:
- Long-Only Spot discipline.
- No Hidden Indicators on this tab (no RSI, MACD, or EMA calculations used here).
- 1D timeframe controls directional bias (strictly separating completed [-2] vs forming [-1] candle).
- 4H timeframe controls short-term structure and entry timing.
- Fixed 6-Panel CoinGlass order with Open Interest strictly in BTC coins (never USD notional).
- Section 8 Non-Trade Zones (8A-8F), Section 10 Buy Decision, and Section 11 Sell Triggers (1-4).
"""

import json
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Sequence, Tuple

import numpy as np

from config.settings import EngineConfig
from core.models import (
    CoinGlassPanelRow,
    DerivativesSnapshot,
    FlowSnapshot,
    KlineBar,
    ProtocolNonTradeZoneItem,
    ProtocolSellTriggerItem,
    ProtocolV13Evaluation,
)
from core.state_store import StateStore
from .volume_profile import compute_atr, synthesize_4h_bars


# Built-in 2026 FOMC & US CPI release dates (YYYY-MM-DD UTC) for automatic 8D window detection
FOMC_CPI_DATES_2026 = {
    # 2026 FOMC Decision Dates
    "2026-01-28", "2026-03-18", "2026-05-06", "2026-06-17",
    "2026-07-29", "2026-09-16", "2026-10-28", "2026-12-09",
    # 2026 US CPI Release Dates
    "2026-01-14", "2026-02-11", "2026-03-11", "2026-04-14",
    "2026-05-12", "2026-06-10", "2026-07-14", "2026-08-12",
    "2026-09-11", "2026-10-14", "2026-11-12", "2026-12-10",
}


def synthesize_1d_bars_from_1h(bars_1h: Sequence[KlineBar]) -> List[KlineBar]:
    """Fallback synthesizer for 1D bars when only 1H bars are loaded (e.g., in synthetic unit tests)."""
    if not bars_1h:
        return []
    buckets: Dict[int, List[KlineBar]] = {}
    day_ms = 86_400_000
    for b in bars_1h:
        b_key = (b.timestamp_ms // day_ms) * day_ms
        buckets.setdefault(b_key, []).append(b)

    out: List[KlineBar] = []
    for b_key in sorted(buckets.keys()):
        grp = buckets[b_key]
        out.append(
            KlineBar(
                timestamp_ms=b_key,
                open=grp[0].open,
                high=max(x.high for x in grp),
                low=min(x.low for x in grp),
                close=grp[-1].close,
                volume=sum(x.volume for x in grp),
                taker_buy_volume=sum(x.taker_buy_volume for x in grp),
            )
        )
    return out


class ProtocolV13Evaluator:
    """Evaluates Protocol v1.3 Market Structure, CoinGlass 6-Panel Audit, and Non-Trade Zones."""

    def __init__(self, config: EngineConfig) -> None:
        self.config = config
        self._cached_context: Dict[str, Any] = {}
        self._last_context_load_ts: float = 0.0

    def _load_protocol_context(self) -> Dict[str, Any]:
        """Hot-reloads `config/protocol_context.json` every 10 seconds."""
        now = time.time()
        if self._cached_context and (now - self._last_context_load_ts) < 10.0:
            return self._cached_context

        self._last_context_load_ts = now
        defaults: Dict[str, Any] = {
            "last_reviewed_utc": "AUTO",
            "liq_cascade_72h_over_300m": "CONFIRMED_CLEAR",
            "liq_cascade_reclaimed_within_24h": "CONFIRMED_CLEAR",
            "fomc_cpi_window_override": "AUTO",
            "s2_risk_level": "LOW",
            "etf_net_outflow_weakness": "NOT_CONFIRMED",
            "catalyst_technical_breakdown": "NOT_CONFIRMED",
            "enforce_200d_hard_veto_on_tab1": False,
            "cycle_ath_override_usd": self.config.default_cycle_ath_usd,
        }
        try:
            if self.config.protocol_context_path.exists():
                with open(self.config.protocol_context_path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    if isinstance(loaded, dict):
                        defaults.update(loaded)
        except Exception:
            pass

        self._cached_context = defaults
        return defaults

    @staticmethod
    def _classify_cvd_direction(bars: Sequence[KlineBar], lookback: int = 3) -> Tuple[float, str]:
        """Computes cumulative delta over `lookback` bars and classifies direction."""
        if not bars:
            return 0.0, "FLAT"
        window = bars[-lookback:]
        net_delta = sum(b.delta for b in window)
        total_vol = max(sum(b.volume for b in window), 1e-6)
        ratio = net_delta / total_vol
        if ratio >= 0.025:
            return net_delta, "RISING"
        if ratio <= -0.025:
            return net_delta, "FALLING"
        return net_delta, "FLAT"

    def evaluate(
        self,
        store: StateStore,
        flow: FlowSnapshot,
        deriv: DerivativesSnapshot,
    ) -> ProtocolV13Evaluation:
        """Runs full Protocol v1.3 evaluation across 1D (Completed vs Forming) and 4H timeframes."""
        ctx = self._load_protocol_context()
        spot_1h = list(store.spot_klines_1h)
        perp_1h = list(store.perp_klines_1h)
        spot_1d = list(store.spot_klines_1d) or synthesize_1d_bars_from_1h(spot_1h)
        perp_1d = list(store.perp_klines_1d) or synthesize_1d_bars_from_1h(perp_1h)

        bars_4h = synthesize_4h_bars(spot_1h)
        perp_bars_4h = synthesize_4h_bars(perp_1h)

        current_price = store.binance_spot_price or (spot_1h[-1].close if spot_1h else 0.0)

        # 1. Strictly separate Completed 1D candle [-2] from Forming 1D candle [-1]
        if len(spot_1d) >= 2:
            comp_1d = spot_1d[-2]
            form_1d = spot_1d[-1]
        elif len(spot_1d) == 1:
            comp_1d = spot_1d[0]
            form_1d = spot_1d[0]
        else:
            comp_1d = KlineBar(0, current_price, current_price, current_price, current_price, 0.0, 0.0)
            form_1d = comp_1d

        comp_1d_chg = ((comp_1d.close - comp_1d.open) / max(comp_1d.open, 1.0)) * 100.0
        form_1d_chg = ((form_1d.close - form_1d.open) / max(form_1d.open, 1.0)) * 100.0

        # 2. Compute 1D Structural Support & Resistance from Completed 1D Candles (last 14 completed days)
        completed_window = spot_1d[:-1][-14:] if len(spot_1d) >= 3 else spot_1d
        daily_support = min((b.low for b in completed_window), default=current_price * 0.95)
        daily_resistance = max((b.high for b in completed_window), default=current_price * 1.05)

        # 3. 1D Directional Bias (Pure price structure of Completed [-2] & 7D structure, no hidden indicators)
        recent_3d = spot_1d[:-1][-3:] if len(spot_1d) >= 4 else completed_window
        higher_lows_1d = len(recent_3d) >= 2 and recent_3d[-1].low >= recent_3d[0].low
        higher_closes_1d = len(recent_3d) >= 2 and recent_3d[-1].close >= recent_3d[0].close

        if comp_1d.close > comp_1d.open and higher_closes_1d and current_price >= daily_support:
            daily_bias = "BULLISH"
        elif comp_1d.close < daily_support or (comp_1d.close < comp_1d.open and not higher_lows_1d):
            daily_bias = "BEARISH"
        else:
            daily_bias = "NEUTRAL"

        # 4. 4H Short-Term Structure & Entry Timing
        if len(bars_4h) >= 4:
            b4_prev = bars_4h[-3]
            b4_comp = bars_4h[-2]
            b4_form = bars_4h[-1]
            if b4_comp.close > b4_prev.close and b4_comp.low >= b4_prev.low:
                structure_4h = "BULLISH HH/HL (Higher Lows Holding)"
                timing_4h_ready = b4_form.close >= b4_comp.low and flow.w_4h.spot_delta_btc > 0
            elif b4_comp.close < b4_prev.low and flow.w_4h.spot_delta_btc < 0:
                structure_4h = "BEARISH LH/LL (Lower Lows Active)"
                timing_4h_ready = False
            else:
                structure_4h = "RANGE / BASE CONSOLIDATION"
                timing_4h_ready = b4_form.close > b4_form.open and flow.w_4h.spot_delta_btc > 0
        else:
            structure_4h = "WARMING UP"
            timing_4h_ready = False

        # 5. ATR 14 on 1D (completed bars) and 4H (completed bars)
        atr_14_1d = max(compute_atr(spot_1d[:-1][-25:] if len(spot_1d) > 2 else spot_1d, period=14), 1.0)
        atr_14_4h = max(compute_atr(bars_4h[:-1][-25:] if len(bars_4h) > 2 else bars_4h, period=14), 1.0)

        down_1d_atr = current_price - atr_14_1d
        up_1d_atr = current_price + atr_14_1d
        down_4h_atr = current_price - atr_14_4h
        up_4h_atr = current_price + atr_14_4h

        # 6. Fixed 6-Panel CoinGlass Order across 1D & 4H
        # Panel 1: Volume SMA 9
        vol_1d_bars = spot_1d[:-1][-9:] if len(spot_1d) >= 2 else spot_1d[-9:]
        vol_sma9_1d = float(np.mean([b.volume for b in vol_1d_bars])) if vol_1d_bars else 0.0
        vol_4h_bars = bars_4h[:-1][-9:] if len(bars_4h) >= 2 else bars_4h[-9:]
        vol_sma9_4h = float(np.mean([b.volume for b in vol_4h_bars])) if vol_4h_bars else 0.0
        cur_vol_4h = bars_4h[-2].volume if len(bars_4h) >= 2 else (bars_4h[-1].volume if bars_4h else 0.0)
        vol_trend = (
            "EXPANDING (Above SMA9)"
            if cur_vol_4h > vol_sma9_4h * 1.05
            else ("CONTRACTING (Below SMA9)" if cur_vol_4h < vol_sma9_4h * 0.85 else "FLAT / IN-LINE")
        )

        # Panel 2: Aggregated Spot CVD
        spot_cvd_1d_val, spot_cvd_1d_dir = self._classify_cvd_direction(spot_1d[:-1] or spot_1d, lookback=3)
        spot_cvd_4h_val = flow.w_4h.spot_delta_btc
        spot_cvd_4h_dir = (
            "RISING" if spot_cvd_4h_val > 15.0 else ("FALLING" if spot_cvd_4h_val < -15.0 else "FLAT")
        )

        # Panel 3: Aggregated Futures CVD
        perp_cvd_1d_val, perp_cvd_1d_dir = self._classify_cvd_direction(perp_1d[:-1] or perp_1d, lookback=3)
        perp_cvd_4h_val = flow.w_4h.perp_delta_btc
        perp_cvd_4h_dir = (
            "RISING" if perp_cvd_4h_val > 40.0 else ("FALLING" if perp_cvd_4h_val < -40.0 else "FLAT")
        )

        # Panel 4: Open Interest (Strict BTC Coins - NEVER USD Notional)
        oi_btc = deriv.open_interest_btc
        oi_dir = (
            "RISING"
            if deriv.oi_change_4h_pct >= 0.35
            else ("FALLING" if deriv.oi_change_4h_pct <= -0.35 else "FLAT")
        )
        oi_above_90k = oi_btc > self.config.protocol_oi_high_threshold_btc
        oi_status_str = (
            f"{oi_dir} | {'[ ELEVATED > 90,000 BTC ]' if oi_above_90k else 'BELOW 90,000 BTC CAP'}"
        )

        # Panel 5: Funding Rates
        fund_pct = deriv.funding_rate_pct
        fund_dir = (
            "POSITIVE (Longs Pay)"
            if fund_pct > 0.002
            else ("NEGATIVE (Shorts Pay)" if fund_pct < -0.001 else "NEUTRAL / FLAT")
        )

        # Panel 6: ATR 14
        atr_1d_pct = (atr_14_1d / max(current_price, 1.0)) * 100.0
        atr_4h_pct = (atr_14_4h / max(current_price, 1.0)) * 100.0

        coinglass_rows = [
            CoinGlassPanelRow(
                panel_num=1,
                metric_name="1. Volume SMA 9 (BTC)",
                value_1d=f"{vol_sma9_1d:,.0f} BTC (1D: {comp_1d.volume:,.0f})",
                value_4h=f"{vol_sma9_4h:,.0f} BTC (4H: {cur_vol_4h:,.0f})",
                direction_status=vol_trend,
            ),
            CoinGlassPanelRow(
                panel_num=2,
                metric_name="2. Aggregated Spot CVD",
                value_1d=f"{spot_cvd_1d_val:+,.0f} BTC [{spot_cvd_1d_dir}]",
                value_4h=f"{spot_cvd_4h_val:+,.1f} BTC [{spot_cvd_4h_dir}]",
                direction_status=f"1D:{spot_cvd_1d_dir} | 4H:{spot_cvd_4h_dir}",
            ),
            CoinGlassPanelRow(
                panel_num=3,
                metric_name="3. Aggregated Futures CVD",
                value_1d=f"{perp_cvd_1d_val:+,.0f} BTC [{perp_cvd_1d_dir}]",
                value_4h=f"{perp_cvd_4h_val:+,.1f} BTC [{perp_cvd_4h_dir}]",
                direction_status=f"1D:{perp_cvd_1d_dir} | 4H:{perp_cvd_4h_dir}",
            ),
            CoinGlassPanelRow(
                panel_num=4,
                metric_name="4. Open Interest (BTC)",
                value_1d=f"{oi_btc:,.1f} BTC (Coins)",
                value_4h=f"4H:{deriv.oi_change_4h_pct:+.2f}% | 1H:{deriv.oi_change_1h_pct:+.2f}%",
                direction_status=f"{oi_dir} ({'>90k BTC' if oi_above_90k else '<=90k BTC'})",
            ),
            CoinGlassPanelRow(
                panel_num=5,
                metric_name="5. Funding Rates (8H)",
                value_1d=f"{fund_pct:+.4f}% / 8h",
                value_4h=f"{fund_pct * 3:+.4f}% / 24h",
                direction_status=fund_dir,
            ),
            CoinGlassPanelRow(
                panel_num=6,
                metric_name="6. ATR 14 (Volatility)",
                value_1d=f"${atr_14_1d:,.0f} ({atr_1d_pct:.2f}%)",
                value_4h=f"${atr_14_4h:,.0f} ({atr_4h_pct:.2f}%)",
                direction_status=f"-1xATR: ${down_4h_atr:,.0f} / ${down_1d_atr:,.0f}",
            ),
        ]

        # 7. Section 8 Non-Trade Zones (8A - 8F)
        if store.warmup_complete:
            now_utc = datetime.now(timezone.utc)
        elif spot_1h:
            now_utc = datetime.fromtimestamp(spot_1h[-1].timestamp_ms / 1000.0, tz=timezone.utc)
        else:
            now_utc = datetime.now(timezone.utc)
        is_weekend = now_utc.weekday() >= 5  # Saturday=5, Sunday=6
        nearest_round = min(
            self.config.protocol_round_numbers_usd,
            key=lambda lvl: abs(current_price - lvl),
        )
        dist_round_pct = abs(current_price - nearest_round) / max(nearest_round, 1.0) * 100.0
        within_round_2pct = dist_round_pct <= self.config.protocol_round_proximity_pct

        # 8A: Weekend/Holiday + within 2.0% of $80k/$85k/$100k + OI > 90,000 BTC (ALL 3 required)
        ntz_8a_triggered = is_weekend and within_round_2pct and oi_above_90k
        ntz_8a = ProtocolNonTradeZoneItem(
            code="8A",
            rule_name="Weekend + <=2% of $80k/$85k/$100k + OI>90k BTC",
            status="TRIGGERED" if ntz_8a_triggered else "CLEAR",
            detail=(
                f"{'Weekend' if is_weekend else 'Weekday'} | "
                f"{dist_round_pct:.2f}% from ${nearest_round:,.0f} "
                f"({'<=2%' if within_round_2pct else '>2%'}) | "
                f"OI {oi_btc:,.0f} BTC ({'>90k' if oi_above_90k else '<=90k'})"
            ),
        )

        # 8B: Recent 72h Liquidation Cascade > $300M
        raw_8b = str(ctx.get("liq_cascade_72h_over_300m", "CONFIRMED_CLEAR")).upper()
        auto_liq_cascade = deriv.oi_change_4h_pct <= -6.0
        if auto_liq_cascade or raw_8b in ("TRIGGERED", "YES", "ACTIVE"):
            status_8b = "TRIGGERED"
            detail_8b = "Active >$300M 72h liquidation cascade (Wait for 24h structural reclaim)"
        elif raw_8b == "UNVERIFIED":
            status_8b = "UNVERIFIED"
            detail_8b = "72h Liquidation Cascade status marked UNVERIFIED in protocol_context.json"
        else:
            status_8b = "CLEAR"
            detail_8b = f"No >$300M 72h cascade active (4H dOI: {deriv.oi_change_4h_pct:+.2f}%)"
        ntz_8b = ProtocolNonTradeZoneItem(
            code="8B",
            rule_name="72h Liquidation Cascade > $300M",
            status=status_8b,
            detail=detail_8b,
        )

        # 8C: Positive Funding + Flat/Rising OI + Falling Price (Live check)
        price_falling = flow.w_4h.price_change_pct <= -0.35 and flow.w_1h.price_change_pct <= -0.20
        oi_flat_or_rising = deriv.oi_change_4h_pct >= 0.0 or deriv.oi_change_1h_pct >= 0.20
        funding_positive = deriv.funding_rate_pct > 0.0105 or (
            deriv.funding_rate_pct > 0.005 and flow.w_4h.price_change_pct <= -1.0
        )
        ntz_8c_triggered = funding_positive and oi_flat_or_rising and price_falling
        ntz_8c = ProtocolNonTradeZoneItem(
            code="8C",
            rule_name="Positive Funding + Flat/Rising OI + Falling Price",
            status="TRIGGERED" if ntz_8c_triggered else "CLEAR",
            detail=(
                f"Funding {deriv.funding_rate_pct:+.4f}% | "
                f"1H/4H dOI {deriv.oi_change_1h_pct:+.2f}%/{deriv.oi_change_4h_pct:+.2f}% | "
                f"1H/4H Price {flow.w_1h.price_change_pct:+.2f}%/{flow.w_4h.price_change_pct:+.2f}%"
            ),
        )

        # 8D: FOMC / CPI Macro Window
        today_str = now_utc.strftime("%Y-%m-%d")
        raw_8d = str(ctx.get("fomc_cpi_window_override", "AUTO")).upper()
        if raw_8d in ("TRIGGERED", "YES", "ACTIVE"):
            status_8d = "TRIGGERED"
            detail_8d = "Manual FOMC/CPI Macro Window override ACTIVE"
        elif raw_8d == "UNVERIFIED":
            status_8d = "UNVERIFIED"
            detail_8d = "FOMC/CPI calendar check marked UNVERIFIED"
        elif raw_8d == "AUTO" and today_str in FOMC_CPI_DATES_2026:
            status_8d = "TRIGGERED"
            detail_8d = f"Today ({today_str}) is a scheduled 2026 FOMC / US CPI event date"
        else:
            status_8d = "CLEAR"
            detail_8d = f"Clear of FOMC/CPI release window ({today_str} UTC)"
        ntz_8d = ProtocolNonTradeZoneItem(
            code="8D",
            rule_name="FOMC / CPI High-Volatility Macro Window",
            status=status_8d,
            detail=detail_8d,
        )

        # 8E: S2 Risk Assessment
        s2_level = str(ctx.get("s2_risk_level", "LOW")).upper()
        if s2_level in ("HIGH", "CRITICAL"):
            status_8e = "TRIGGERED"
        elif s2_level == "UNVERIFIED":
            status_8e = "UNVERIFIED"
        else:
            status_8e = "CLEAR"
        ntz_8e = ProtocolNonTradeZoneItem(
            code="8E",
            rule_name="Section 8E S2 Systemic Risk Assessment",
            status=status_8e,
            detail=f"S2 Systemic Risk Level: {s2_level} (Clear when LOW/MED)",
        )

        # 8F: Unverified Mandatory Check Override
        prior_checks = [ntz_8a, ntz_8b, ntz_8c, ntz_8d, ntz_8e]
        unverified_codes = [c.code for c in prior_checks if c.status == "UNVERIFIED"]
        ntz_8f = ProtocolNonTradeZoneItem(
            code="8F",
            rule_name="Unverified Mandatory Check Safety Lock",
            status="TRIGGERED" if unverified_codes else "CLEAR",
            detail=(
                f"Unverified checks locking desk: {', '.join(unverified_codes)}"
                if unverified_codes
                else "All mandatory 8A–8E safety inputs verified"
            ),
        )

        non_trade_zones = [ntz_8a, ntz_8b, ntz_8c, ntz_8d, ntz_8e, ntz_8f]
        triggered_ntz = [z for z in non_trade_zones if z.status == "TRIGGERED"]
        if unverified_codes:
            ntz_status = "UNVERIFIED"
        elif triggered_ntz:
            ntz_status = "YES"
        else:
            ntz_status = "NO"

        active_ntz_reasons = [f"Protocol v1.3 [{z.code}]: {z.rule_name}" for z in triggered_ntz]

        # 8. Section 11 Long-Only Spot Sell Triggers (1 - 4)
        # Sell Trigger 1: Confirmed 1D close < support + flat/rising OI + falling CVD
        st1_confirmed = (
            comp_1d.close < daily_support
            and (deriv.oi_change_4h_pct >= 0.0 or deriv.oi_change_1h_pct >= 0.0)
            and spot_cvd_4h_dir == "FALLING"
        )
        st1 = ProtocolSellTriggerItem(
            trigger_num=1,
            name="1. 1D Close < Support + Rising OI + Falling CVD",
            status="CONFIRMED" if st1_confirmed else "NOT CONFIRMED",
            detail=f"1D Close ${comp_1d.close:,.0f} vs Sup ${daily_support:,.0f} | 4H CVD {spot_cvd_4h_dir}",
        )

        # Sell Trigger 2: Liquidation cascade fails 24h reclaim
        raw_reclaim = str(ctx.get("liq_cascade_reclaimed_within_24h", "CONFIRMED_CLEAR")).upper()
        st2_status = (
            "CONFIRMED"
            if raw_reclaim in ("FAILED", "CONFIRMED")
            else ("UNVERIFIED" if raw_reclaim == "UNVERIFIED" else "NOT CONFIRMED")
        )
        st2 = ProtocolSellTriggerItem(
            trigger_num=2,
            name="2. Liq Cascade Fails 24h Structural Reclaim",
            status=st2_status,
            detail=f"Cascade 24h status: {raw_reclaim}",
        )

        # Sell Trigger 3: Large ETF outflows + price weakness
        raw_etf = str(ctx.get("etf_net_outflow_weakness", "NOT_CONFIRMED")).upper()
        st3_status = (
            "CONFIRMED"
            if raw_etf == "CONFIRMED"
            else ("UNVERIFIED" if raw_etf == "UNVERIFIED" else "NOT CONFIRMED")
        )
        st3 = ProtocolSellTriggerItem(
            trigger_num=3,
            name="3. Large Spot ETF Outflows + Price Weakness",
            status=st3_status,
            detail=f"ETF flow status: {raw_etf}",
        )

        # Sell Trigger 4: Catalyst + technical breakdown
        raw_cat = str(ctx.get("catalyst_technical_breakdown", "NOT_CONFIRMED")).upper()
        st4_status = (
            "CONFIRMED"
            if raw_cat == "CONFIRMED"
            else ("UNVERIFIED" if raw_cat == "UNVERIFIED" else "NOT CONFIRMED")
        )
        st4 = ProtocolSellTriggerItem(
            trigger_num=4,
            name="4. Adverse Macro Catalyst + Technical Breakdown",
            status=st4_status,
            detail=f"Catalyst breakdown status: {raw_cat}",
        )

        sell_triggers = [st1, st2, st3, st4]
        any_sell_confirmed = any(s.status == "CONFIRMED" for s in sell_triggers)

        # 9. Section 10 Final Buy Decision & Readiness
        readiness_notes: List[str] = []
        if ntz_status != "NO":
            buy_allowed = "NO"
            entry_status = "NOT READY"
            confidence = "LOW"
            readiness_notes.append(f"Blocked by Section 8 Non-Trade Zone ({', '.join(z.code for z in triggered_ntz)}).")
        elif any_sell_confirmed:
            buy_allowed = "NO"
            entry_status = "NOT READY"
            confidence = "LOW"
            readiness_notes.append("Blocked by active Section 11 Spot Sell Trigger.")
        elif daily_bias == "BULLISH" and timing_4h_ready and spot_cvd_4h_dir == "RISING":
            buy_allowed = "YES"
            entry_status = "READY"
            confidence = "HIGH" if spot_cvd_1d_dir == "RISING" else "MEDIUM"
            readiness_notes.append("1D Bias BULLISH + 4H structure aligned + Spot CVD RISING + Zero Non-Trade Zones.")
        elif daily_bias in ("BULLISH", "NEUTRAL") and spot_cvd_4h_dir == "RISING" and not ntz_8c_triggered:
            buy_allowed = "YES"
            entry_status = "NOT READY" if not timing_4h_ready else "READY"
            confidence = "MEDIUM"
            readiness_notes.append(
                f"1D Bias {daily_bias}; 4H Spot CVD RISING, awaiting 4H HH/HL close confirmation."
            )
        else:
            buy_allowed = "NO"
            entry_status = "NOT READY"
            confidence = "LOW"
            readiness_notes.append(
                f"Stand aside: 1D Bias is {daily_bias}, 4H Spot CVD is {spot_cvd_4h_dir}, 4H Timing={'READY' if timing_4h_ready else 'WAIT'}."
            )

        readiness_notes.append(
            f"1D Completed [-2]: ${comp_1d.close:,.0f} ({comp_1d_chg:+.2f}%) | 1D Forming [-1]: ${form_1d.close:,.0f} ({form_1d_chg:+.2f}%)"
        )
        readiness_notes.append(
            f"ATR 14 Reference Bounds -> 4H [-1xATR]: ${down_4h_atr:,.0f} | 1D [-1xATR]: ${down_1d_atr:,.0f}"
        )

        # 10. Liquidation Magnet & Range Predisposition Protocol (T1 + T2 Integration)
        closes_50d = [b.close for b in spot_1d[-50:]] if spot_1d else [current_price]
        sma_50_1d = float(np.mean(closes_50d)) if closes_50d else current_price
        range_pivot_usd = (daily_support + daily_resistance) / 2.0

        manual_short_liq = float(ctx.get("short_liq_magnet_override_usd", 0.0) or 0.0)
        if manual_short_liq > 0.0:
            short_liq_magnet_usd = manual_short_liq
            short_liq_source = "[COINGLASS MANUAL]"
        else:
            swing_high_14d = max((b.high for b in spot_1d[-14:]), default=daily_resistance)
            ref_high = swing_high_14d if swing_high_14d > current_price * 1.005 else max(daily_resistance, current_price * 1.02)
            short_liq_magnet_usd = ref_high * 1.005
            short_liq_source = "[EST. SWING LIQ POOL]"

        manual_long_liq = float(ctx.get("long_liq_magnet_override_usd", 0.0) or 0.0)
        if manual_long_liq > 0.0:
            long_liq_magnet_usd = manual_long_liq
            long_liq_source = "[COINGLASS MANUAL]"
        else:
            swing_low_14d = min((b.low for b in spot_1d[-14:]), default=daily_support)
            ref_low = swing_low_14d if swing_low_14d < current_price * 0.995 else min(daily_support, current_price * 0.98)
            long_liq_magnet_usd = ref_low * 0.995
            long_liq_source = "[EST. SWING LIQ POOL]"

        headline_filter_status = str(ctx.get("headline_classification", "NONE_SIGNIFICANT")).upper()

        dist_short_liq_pct = ((short_liq_magnet_usd - current_price) / max(current_price, 1.0)) * 100.0
        dist_long_liq_pct = ((current_price - long_liq_magnet_usd) / max(current_price, 1.0)) * 100.0

        # T2 5-Factor Confluence Count
        aligned_factors = 0
        if min(dist_short_liq_pct, dist_long_liq_pct) <= 4.5:
            aligned_factors += 1
        if deriv.funding_rate_pct <= 0.0100:
            aligned_factors += 1
        if abs(deriv.oi_change_4h_pct) >= 0.30:
            aligned_factors += 1
        if spot_cvd_4h_dir == "RISING":
            aligned_factors += 1
        if timing_4h_ready or current_price >= range_pivot_usd:
            aligned_factors += 1

        # T1 4-Way Range-Regime Decision Rules
        if comp_1d.close > short_liq_magnet_usd and spot_cvd_1d_dir == "RISING" and deriv.oi_change_4h_pct >= -0.5:
            liq_magnet_verdict = "RARE ADD ON RETEST (Breakout Confirmed)"
            liq_magnet_action_note = (
                f"1D closed above ${short_liq_magnet_usd:,.0f} wall with rising Spot CVD; consider adding on retest."
            )
        elif (
            dist_short_liq_pct <= 3.0
            and deriv.funding_rate_pct <= 0.0105
            and flow.w_1h.spot_delta_btc <= 0
        ):
            liq_magnet_verdict = "PARTIAL PROFIT INTO MAGNET (Scale 30–50%)"
            liq_magnet_action_note = (
                f"Scale 30–50% into ${short_liq_magnet_usd:,.0f} short-liq cluster; do NOT chase futures-driven bounce."
            )
        elif (
            current_price < range_pivot_usd
            and current_price < sma_50_1d
            and spot_cvd_4h_dir == "FALLING"
        ):
            liq_magnet_verdict = "REDUCE / ROTATE DEFENSIVE (Below Pivot & 50D MA)"
            liq_magnet_action_note = (
                f"Below Range Pivot (${range_pivot_usd:,.0f}) & 50D MA (${sma_50_1d:,.0f}); watch ${long_liq_magnet_usd:,.0f} long-liq pool."
            )
        elif dist_long_liq_pct <= 2.5 and spot_cvd_4h_dir == "RISING" and aligned_factors >= 3:
            liq_magnet_verdict = "HOLD / ACCUMULATE AT RANGE LOW (Target Short-Liq Magnet)"
            liq_magnet_action_note = (
                f"Spot absorbing near ${long_liq_magnet_usd:,.0f} long-liq pool; target 30–50% partial at ${short_liq_magnet_usd:,.0f}."
            )
        else:
            liq_magnet_verdict = "DO NOTHING (Default Range Inaction — Wait for Magnet Edge)"
            liq_magnet_action_note = (
                f"Scale 30–50% into ${short_liq_magnet_usd:,.0f} if reached; Invalidation: 1D close < ${min(range_pivot_usd, sma_50_1d):,.0f}."
            )

        ev = ProtocolV13Evaluation(
            timestamp_utc=now_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
            current_price=round(current_price, 2),
            completed_1d_open=round(comp_1d.open, 2),
            completed_1d_high=round(comp_1d.high, 2),
            completed_1d_low=round(comp_1d.low, 2),
            completed_1d_close=round(comp_1d.close, 2),
            completed_1d_change_pct=round(comp_1d_chg, 2),
            forming_1d_open=round(form_1d.open, 2),
            forming_1d_high=round(form_1d.high, 2),
            forming_1d_low=round(form_1d.low, 2),
            forming_1d_close=round(form_1d.close, 2),
            forming_1d_change_pct=round(form_1d_chg, 2),
            daily_support=round(daily_support, 2),
            daily_resistance=round(daily_resistance, 2),
            daily_bias=daily_bias,
            structure_4h=structure_4h,
            timing_4h_ready=timing_4h_ready,
            atr_14_1d=round(atr_14_1d, 2),
            atr_14_4h=round(atr_14_4h, 2),
            downside_ref_1d_atr=round(down_1d_atr, 2),
            upside_ref_1d_atr=round(up_1d_atr, 2),
            downside_ref_4h_atr=round(down_4h_atr, 2),
            upside_ref_4h_atr=round(up_4h_atr, 2),
            coinglass_rows=coinglass_rows,
            non_trade_zones=non_trade_zones,
            non_trade_zone_status=ntz_status,
            active_ntz_reasons=active_ntz_reasons,
            confidence=confidence,
            buy_allowed=buy_allowed,
            entry_status=entry_status,
            readiness_notes=readiness_notes,
            sell_triggers=sell_triggers,
            any_sell_confirmed=any_sell_confirmed,
            enforce_200d_hard_veto_on_tab1=bool(ctx.get("enforce_200d_hard_veto_on_tab1", False)),
            context_last_reviewed=str(ctx.get("last_reviewed_utc", "AUTO")),
            sma_50_1d=round(sma_50_1d, 2),
            range_pivot_usd=round(range_pivot_usd, 2),
            short_liq_magnet_usd=round(short_liq_magnet_usd, 2),
            short_liq_source=short_liq_source,
            long_liq_magnet_usd=round(long_liq_magnet_usd, 2),
            long_liq_source=long_liq_source,
            headline_filter_status=headline_filter_status,
            magnet_confluence_aligned=aligned_factors,
            liq_magnet_verdict=liq_magnet_verdict,
            liq_magnet_action_note=liq_magnet_action_note,
        )
        store.protocol_evaluation = ev
        return ev
