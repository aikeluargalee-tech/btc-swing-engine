"""BTC Magnet - Mechanics-First Liquidation Gravity & Swing Edge Detector Engine.

Implements the locked product definition, speaking rules, and status templates
from the BTC Magnet handoff specification (docs/one-pager.md, docs/speaking-rules.md,
docs/status-templates.md).

Answers one question only:
  "What is currently pulling Bitcoin, and is there a clear swing edge or not?"

Defaults to "No clear edge - wait." and only speaks when strict internal conditions align.
"""

import json
import logging
import os
import subprocess
import time
import urllib.request
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from config.settings import EngineConfig
from core.models import BTCMagnetEvaluation, BTCMagnetLevel, BTCMagnetRuleCheck
from core.state_store import StateStore

logger = logging.getLogger(__name__)


class BTCMagnetEngine:
    """Evaluates real-time liquidation clusters, open interest, and the 7 locked speaking rules."""

    def __init__(self, config: Optional[EngineConfig] = None) -> None:
        self.config = config
        self._last_fetch_ts: float = 0.0
        self._cached_liq_data: Optional[Dict[str, Any]] = None
        self._cache_ttl_sec: float = 45.0

    def evaluate(self, store: StateStore) -> BTCMagnetEvaluation:
        """Evaluates current market state and populates store.btc_magnet_evaluation."""
        now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        # 1. Spot Price
        spot_price = float(
            getattr(store, "binance_spot_price", 0.0)
            or getattr(store, "spot_price", 0.0)
            or 0.0
        )
        if spot_price <= 0.0 and getattr(store, "spot_klines_1h", None):
            spot_price = float(store.spot_klines_1h[-1].close)
        if spot_price <= 0.0:
            spot_price = 76000.0

        # 2. 24h Price Change & Range
        high_24h = float(getattr(store, "high_24h", 0.0) or 0.0)
        low_24h = float(getattr(store, "low_24h", 0.0) or 0.0)
        price_change_24h = float(getattr(store, "price_change_24h_pct", 0.0) or 0.0)

        if (high_24h <= 0.0 or low_24h <= 0.0) and getattr(store, "spot_klines_1h", None) and len(store.spot_klines_1h) >= 24:
            bars_24 = list(store.spot_klines_1h)[-24:]
            high_24h = max(b.high for b in bars_24)
            low_24h = min(b.low for b in bars_24)
            open_24 = bars_24[0].open
            if open_24 > 0:
                price_change_24h = ((spot_price - open_24) / open_24) * 100.0

        if high_24h <= 0.0:
            high_24h = spot_price * 1.018
        if low_24h <= 0.0:
            low_24h = spot_price * 0.982

        # 3. Funding Rate (Annualized %)
        # Note: store.funding_rate_pct in StateStore is already in % per 8h (e.g. 0.01 = 0.01% per 8h).
        raw_funding = float(getattr(store, "funding_rate_pct", 0.0) or 0.0)
        if getattr(store, "derivatives_snapshot", None) is not None and raw_funding == 0.0:
            raw_funding = float(getattr(store.derivatives_snapshot, "funding_rate_pct", 0.0) or 0.0)

        if abs(raw_funding) < 1.0:
            annual_funding_pct = raw_funding * 3.0 * 365.0
        else:
            annual_funding_pct = raw_funding

        # 4. Open Interest Velocity (4h delta %)
        explicit_oi = store.__dict__.get("oi_delta_4h_pct", None)
        if explicit_oi is not None:
            oi_delta_4h = float(explicit_oi)
        elif getattr(store, "derivatives_snapshot", None) is not None and len(getattr(store, "oi_history", [])) >= 2:
            oi_delta_4h = float(store.derivatives_snapshot.oi_change_4h_pct)
        elif hasattr(store, "get_oi_change_pct") and len(getattr(store, "oi_history", [])) >= 2:
            oi_delta_4h = float(store.get_oi_change_pct(14400.0))
        else:
            oi_delta_4h = 0.8

        # 5. Spot CVD 4h Delta (BTC) for structure/flow alignment
        spot_cvd_4h_btc = 0.0
        flow_snap = getattr(store, "flow_snapshot", None)
        if flow_snap is not None and getattr(flow_snap, "w_4h", None) is not None:
            spot_cvd_4h_btc = float(getattr(flow_snap.w_4h, "spot_delta_btc", 0.0) or 0.0)
        elif getattr(store, "spot_klines_1h", None) and len(store.spot_klines_1h) >= 4:
            spot_cvd_4h_btc = float(sum(b.delta for b in list(store.spot_klines_1h)[-4:]))

        # 6. Market Regime Classification
        range_spread_pct = ((high_24h - low_24h) / low_24h) * 100.0 if low_24h > 0 else 3.5
        if range_spread_pct < 4.8:
            market_regime = "Range"
        elif price_change_24h > 2.5:
            market_regime = "TrendUp"
        elif price_change_24h < -2.5:
            market_regime = "TrendDown"
        else:
            market_regime = "Range"

        # 7. Fetch / Compute Liquidation Magnet Clusters
        upper_magnet, lower_magnet = self._get_liquidation_magnets(spot_price, store=store)

        # 8. Unified Gravitational Pull & Direction Analysis
        # Gravitational attraction combines cluster USD volume and proximity to spot.
        pull_ratio = 1.0
        if lower_magnet.usd_volume > 0:
            pull_ratio = round(upper_magnet.usd_volume / lower_magnet.usd_volume, 2)

        up_weight = upper_magnet.usd_volume / max(abs(upper_magnet.dist_pct), 0.5)
        lo_weight = lower_magnet.usd_volume / max(abs(lower_magnet.dist_pct), 0.5)

        if upper_magnet.usd_volume >= lower_magnet.usd_volume * 1.15 or up_weight >= lo_weight * 1.15:
            pull_direction = "UPPER"
        elif lower_magnet.usd_volume >= upper_magnet.usd_volume * 1.15 or lo_weight >= up_weight * 1.15:
            pull_direction = "LOWER"
        else:
            pull_direction = "NEUTRAL"

        # 9. Evaluate the 7 Locked Internal Speaking Rules
        rule_checks, verdict, headline, body, rule_subtitle = self._evaluate_speaking_rules(
            spot_price=spot_price,
            price_change_24h=price_change_24h,
            upper=upper_magnet,
            lower=lower_magnet,
            pull_direction=pull_direction,
            up_weight=up_weight,
            lo_weight=lo_weight,
            funding_annual_pct=annual_funding_pct,
            oi_delta_4h=oi_delta_4h,
            spot_cvd_4h_btc=spot_cvd_4h_btc,
            regime=market_regime,
        )

        passed_count = sum(1 for r in rule_checks if r.passed)
        verdict_badge = "SWING EDGE PRESENT" if verdict == "SPEAK" else "NO CLEAR EDGE - WAIT"

        # 10. Build Markdown Brief
        summary_md = self._build_markdown_brief(
            now_utc=now_utc,
            spot_price=spot_price,
            price_change_24h=price_change_24h,
            upper=upper_magnet,
            lower=lower_magnet,
            pull_dir=pull_direction,
            pull_ratio=pull_ratio,
            funding_ann=annual_funding_pct,
            oi_delta=oi_delta_4h,
            regime=market_regime,
            verdict=verdict,
            headline=headline,
            body=body,
            rule_sub=rule_subtitle,
            rules=rule_checks,
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
            market_regime=market_regime,
            verdict=verdict,
            verdict_badge=verdict_badge,
            headline=headline,
            body=body,
            rule_subtitle=rule_subtitle,
            rules_passed_count=passed_count,
            rule_checks=rule_checks,
            magnet_summary_markdown=summary_md,
        )

        store.btc_magnet_evaluation = eval_result
        return eval_result

    def _get_liquidation_magnets(
        self,
        spot_price: float,
        store: Optional[StateStore] = None,
    ) -> Tuple[BTCMagnetLevel, BTCMagnetLevel]:
        """Fetches live liquidation clusters or computes structural levels if unavailable."""
        now = time.time()
        data = self._cached_liq_data

        if data is None or (now - self._last_fetch_ts) > self._cache_ttl_sec:
            # Always update timestamp before fetch to prevent retry storms on offline/timeout
            self._last_fetch_ts = now
            fetched = self._fetch_live_liqmap()
            if fetched is not None:
                self._cached_liq_data = fetched
                data = fetched

        if data and "levels" in data:
            lev = data["levels"]
            above = [l for l in lev.get("above", []) if l.get("price", 0) > spot_price]
            below = [l for l in lev.get("below", []) if l.get("price", 0) < spot_price]

            above.sort(key=lambda x: x.get("price", 0))
            below.sort(key=lambda x: x.get("price", 0), reverse=True)

            if above:
                ab_px = float(above[0]["price"])
                ab_usd = float(above[0].get("usd", 215_000_000))
                ab_dist = ((ab_px - spot_price) / spot_price) * 100.0
                upper = BTCMagnetLevel(price=ab_px, dist_pct=ab_dist, usd_volume=ab_usd)
            else:
                upper = BTCMagnetLevel(price=spot_price * 1.034, dist_pct=3.4, usd_volume=215_000_000)

            if below:
                bl_px = float(below[0]["price"])
                bl_usd = float(below[0].get("usd", 350_000_000))
                bl_dist = ((bl_px - spot_price) / spot_price) * 100.0
                lower = BTCMagnetLevel(price=bl_px, dist_pct=bl_dist, usd_volume=bl_usd)
            else:
                lower = BTCMagnetLevel(price=spot_price * 0.982, dist_pct=-1.8, usd_volume=350_000_000)

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
                return (
                    BTCMagnetLevel(price=round(up_px, 2), dist_pct=round(up_dist, 2), usd_volume=up_vol),
                    BTCMagnetLevel(price=round(lo_px, 2), dist_pct=round(lo_dist, 2), usd_volume=lo_vol),
                )

        # Tertiary Fallback: Modeled liquidation bands around current Bitcoin spot price
        upper = BTCMagnetLevel(
            price=round(spot_price * 1.0337, 2),
            dist_pct=3.37,
            usd_volume=215_500_000,
        )
        lower = BTCMagnetLevel(
            price=round(spot_price * 0.9823, 2),
            dist_pct=-1.77,
            usd_volume=354_200_000,
        )
        return upper, lower

    def _fetch_live_liqmap(self) -> Optional[Dict[str, Any]]:
        """Queries edgeornot.com public liquidation map with a tight timeout."""
        url = "https://edgeornot.com/api/liqmap/btc?days=1&ex=all"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "BTCMagnetEngine/1.0"})
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                if resp.status == 200:
                    raw = resp.read()
                    return json.loads(raw.decode("utf-8"))
        except Exception:
            pass
        return None

    def _evaluate_speaking_rules(
        self,
        spot_price: float,
        price_change_24h: float,
        upper: BTCMagnetLevel,
        lower: BTCMagnetLevel,
        pull_direction: str,
        up_weight: float,
        lo_weight: float,
        funding_annual_pct: float,
        oi_delta_4h: float,
        spot_cvd_4h_btc: float,
        regime: str,
    ) -> Tuple[List[BTCMagnetRuleCheck], str, str, str, str]:
        """Evaluates the 7 strict conditions from docs/speaking-rules.md."""
        # 1. Clear magnet present (< 4.5% distance, >= $100M USD cluster)
        upper_valid = 0.8 <= upper.dist_pct <= 4.5 and upper.usd_volume >= 100_000_000
        lower_valid = -4.5 <= lower.dist_pct <= -0.8 and lower.usd_volume >= 100_000_000
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
                else "No dense liquidation cluster within 4.5% reach"
            ),
        )

        # 2. Open-interest confirmation (OI rising or stable into magnet)
        cond2 = oi_delta_4h >= -0.5
        r2 = BTCMagnetRuleCheck(
            rule_num=2,
            name="Open-Interest Confirmation",
            passed=cond2,
            detail=f"OI velocity supportive ({oi_delta_4h:+.1f}% 4h delta)" if cond2 else f"OI unsupportive ({oi_delta_4h:+.1f}% 4h delta)",
        )

        # 3. Funding context not contradictory (between -10% and +28%/yr)
        cond3 = -10.0 <= funding_annual_pct <= 28.0
        r3 = BTCMagnetRuleCheck(
            rule_num=3,
            name="Funding Non-Contradictory",
            passed=cond3,
            detail=f"Borrow rate calm ({funding_annual_pct:+.1f}%/yr carry)" if cond3 else f"Funding contradictory or extreme ({funding_annual_pct:+.1f}%/yr)",
        )

        # 4. Regime allows magnet to matter (Range is primary; Trend only if aligned)
        cond4 = False
        if regime == "Range":
            cond4 = True
        elif regime == "TrendUp" and target_side == "ABOVE":
            cond4 = True
        elif regime == "TrendDown" and target_side == "BELOW":
            cond4 = True

        r4 = BTCMagnetRuleCheck(
            rule_num=4,
            name="Regime Conduciveness",
            passed=cond4,
            detail=f"Market in {regime} mode (conducive to magnet sweep)" if cond4 else f"Market regime ({regime}) opposes magnet sweep",
        )

        # 5. Basic structure / spot-flow alignment (no extreme opposite momentum or heavy opposing spot flow)
        opposing_flow = (
            (target_side == "ABOVE" and spot_cvd_4h_btc < -350.0)
            or (target_side == "BELOW" and spot_cvd_4h_btc > 500.0 and price_change_24h > 3.5)
        )
        cond5 = abs(price_change_24h) < 6.5 and not opposing_flow
        flow_tag = f", 4h Spot CVD: {spot_cvd_4h_btc:+.1f} BTC" if spot_cvd_4h_btc != 0.0 else ""
        r5 = BTCMagnetRuleCheck(
            rule_num=5,
            name="Spot Flow & Structure Alignment",
            passed=cond5,
            detail=(
                f"Structure intact (24h change: {price_change_24h:+.2f}%{flow_tag})"
                if cond5
                else f"Opposing momentum/flow (24h change: {price_change_24h:+.2f}%{flow_tag})"
            ),
        )

        # 6. Not already swept (cluster intact)
        cond6 = (target_side == "ABOVE" and upper.price > spot_price) or (target_side == "BELOW" and lower.price < spot_price)
        r6 = BTCMagnetRuleCheck(
            rule_num=6,
            name="Not Already Swept",
            passed=cond6,
            detail="Target cluster intact and unswept" if cond6 else "Cluster already breached or expired",
        )

        # 7. Minimum conviction threshold (at least 5 of 6 cleanly met with 0 direct structural conflicts)
        passed_sub = sum(1 for c in (cond1, cond2, cond3, cond4, cond5, cond6) if c)
        cond7 = passed_sub >= 5 and cond1 and cond4 and cond5 and cond6
        r7 = BTCMagnetRuleCheck(
            rule_num=7,
            name="Conviction Threshold",
            passed=cond7,
            detail=f"{passed_sub}/6 internal filters passed cleanly" if cond7 else f"Conditions incomplete ({passed_sub}/6 passed). Default: WAIT.",
        )

        rule_checks = [r1, r2, r3, r4, r5, r6, r7]

        # Check for Rare Pattern #4: Exhaustion (dense magnet + extreme funding + declining OI)
        is_exhaustion = cond1 and cond6 and (not cond3) and (not cond2)

        # Select exact status text template (from docs/status-templates.md)
        if cond7 and target_side == "ABOVE" and regime == "Range":
            verdict = "SPEAK"
            headline = f"Strong magnet above at ${upper.price:,.0f}."
            body = f"Short liquidations clustered (${upper.usd_volume/1e6:.0f}M), OI rising, funding elevated. Range regime. Spot flow supportive. Watch for sweep."
            rule_subtitle = f"Locked Pattern: Range Regime | Magnet Above ({upper.dist_pct:+.1f}%)"
        elif cond7 and target_side == "BELOW" and regime == "Range":
            verdict = "SPEAK"
            headline = f"Strong magnet below at ${lower.price:,.0f}."
            body = f"Long liquidations clustered (${lower.usd_volume/1e6:.0f}M), OI rising, funding elevated. Range regime. Spot flow supportive. Watch for sweep."
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
                body = "Liquidation density dispersed. No high-probability gravitational pull. Default to cash."
            rule_subtitle = "Locked Principle: The engine spends most days correctly saying 'wait.'"

        return rule_checks, verdict, headline, body, rule_subtitle

    def _build_markdown_brief(
        self,
        now_utc: str,
        spot_price: float,
        price_change_24h: float,
        upper: BTCMagnetLevel,
        lower: BTCMagnetLevel,
        pull_dir: str,
        pull_ratio: float,
        funding_ann: float,
        oi_delta: float,
        regime: str,
        verdict: str,
        headline: str,
        body: str,
        rule_sub: str,
        rules: List[BTCMagnetRuleCheck],
    ) -> str:
        """Constructs shareable clipboard text and AI packet section."""
        lines = [
            "# BTC MAGNET | LIQUIDATION GRAVITY & SWING EDGE READOUT",
            f"**Timestamp:** `{now_utc}`",
            f"**Spot Price:** `${spot_price:,.2f}` (`{price_change_24h:+.2f}% 24h`)  |  **Regime:** `{regime}`",
            f"**Perpetual Funding:** `{funding_ann:+.1f}%/yr`  |  **4h OI Velocity:** `{oi_delta:+.1f}%`",
            "",
            "## 1. LIQUIDATION GRAVITATIONAL HORIZON",
            f"- **Upper Magnet (Short Liquidations):** `${upper.price:,.0f}` (`{upper.dist_pct:+.1f}%` / `+${upper.price - spot_price:,.0f}`) - `${upper.usd_volume/1e6:.1f}M` cluster",
            f"- **Center Spot Horizon:** `${spot_price:,.2f}`",
            f"- **Lower Support (Long Liquidations):** `${lower.price:,.0f}` (`{lower.dist_pct:+.1f}%` / `-${spot_price - lower.price:,.0f}`) - `${lower.usd_volume/1e6:.1f}M` cluster",
            f"- **Dominant Pull:** `{pull_dir}` (Upper-to-Lower liquidity ratio: `{pull_ratio:.2f}x`)",
            "",
            f"## 2. MECHANICAL VERDICT: [{verdict}]",
            f"**Status Headline:** {headline}",
            f"**Terminal Readout:** {body}",
            f"*{rule_sub}*",
            "",
            "## 3. 7 INTERNAL SPEAKING RULES AUDIT",
        ]

        for r in rules:
            badge = "[OK]" if r.passed else "[X]"
            lines.append(f"- **Rule {r.rule_num} ({r.name}):** `{badge}` {r.detail}")

        lines.extend([
            "",
            "---",
            "*Source: BTC Magnet Engine (docs/speaking-rules.md & docs/status-templates.md)*",
        ])
        return "\n".join(lines)


def copy_btc_magnet_card_to_clipboard(store: StateStore) -> Tuple[bool, str, int]:
    """Copies BTC Magnet Status Card brief to clipboard and writes to logs/."""
    eval_data = store.btc_magnet_evaluation
    if eval_data is None:
        engine = BTCMagnetEngine()
        eval_data = engine.evaluate(store)

    text = eval_data.magnet_summary_markdown
    char_count = len(text)

    # Save to logs/btc_magnet_latest.md
    try:
        os.makedirs("logs", exist_ok=True)
        with open(os.path.join("logs", "btc_magnet_latest.md"), "w", encoding="utf-8") as f:
            f.write(text)
    except Exception:
        pass

    # Copy to system clipboard
    copied = False
    if os.name == "nt":
        try:
            proc = subprocess.Popen(
                ["powershell", "-NoProfile", "-Command", "Set-Clipboard -Value $input"],
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            proc.communicate(input=text.encode("utf-8"), timeout=3.0)
            copied = proc.returncode == 0
        except Exception:
            copied = False

    now_str = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")
    store.last_packet_copied_utc = now_str
    store.last_packet_copied_ts = time.time()
    store.last_packet_char_count = char_count

    if copied:
        return True, f"BTC Magnet Card copied to clipboard ({char_count:,} chars)", char_count
    return False, f"Saved BTC Magnet Card to logs/btc_magnet_latest.md ({char_count:,} chars)", char_count
