"""Tell-Tale Candle & Volume Capitulation Climax Sensor.

Implements the deterministic disruption detector from the companion
`tell_tale_candle` system:
- Flags extreme volume dislocation when a candle exhibits:
  1. Directional expansion: Red (Selling Climax) or Green (Buying Climax)
  2. Extreme Relative Volume: volume / 20-bar baseline >= 5.0x
  3. Solid candle body: |close - open| / (high - low) >= 0.65 (minimal wick deflection)
- Evaluates closed bars only to guarantee zero repainting.
"""

from datetime import datetime, timezone
from typing import Optional, Sequence

from config.settings import EngineConfig
from core.models import KlineBar, TellTaleBarResult, TellTaleEvaluation


class TellTaleEngine:
    """Evaluates Tell-Tale volume climax disruption across 15m and 5m horizons."""

    def __init__(self, config: Optional[EngineConfig] = None) -> None:
        self.lookback = getattr(config, "tell_tale_lookback", 20)
        self.min_relvol = getattr(config, "tell_tale_min_relvol", 5.0)
        self.min_body_range = getattr(config, "tell_tale_min_body_range", 0.65)

    def _analyze_bar_series(
        self,
        bars: Sequence[KlineBar],
        timeframe: str = "15m",
    ) -> Optional[TellTaleBarResult]:
        """Analyzes the latest closed bar against its prior 20-bar volume baseline."""
        if len(bars) < self.lookback + 1:
            return None

        # Exclude developing candle if timestamp is current, but in klines sequence
        # we consider bars[-1] as the latest closed bar if caller passes closed bars,
        # or bars[-2] if caller passes developing bar.
        # Following engine convention: caller passes closed bars or slice.
        prior = bars[-(self.lookback + 1) : -1]
        cur = bars[-1]

        o, h, l, c, v = cur.open, cur.high, cur.low, cur.close, cur.volume
        base_vol = sum(b.volume for b in prior) / len(prior) if prior else 1.0
        rng = h - l
        body = abs(c - o)

        relvol = round(v / base_vol, 3) if base_vol > 0 else 0.0
        body_range = round(body / rng, 3) if rng > 0 else 0.0
        is_red = c < o
        is_green = c > o

        is_selling = is_red and (relvol >= self.min_relvol) and (body_range >= self.min_body_range)
        is_elevated = relvol >= 3.0
        is_buying = is_green and (relvol >= self.min_relvol) and (body_range >= self.min_body_range)

        ts_dt = datetime.fromtimestamp(cur.timestamp_ms / 1000.0, tz=timezone.utc)
        open_time_str = ts_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

        return TellTaleBarResult(
            timeframe=timeframe,
            open_time=open_time_str,
            close=round(c, 2),
            open=round(o, 2),
            high=round(h, 2),
            low=round(l, 2),
            volume=round(v, 2),
            baseline_volume=round(base_vol, 2),
            red=is_red,
            green=is_green,
            relvol=relvol,
            body_range=body_range,
            is_selling_climax=is_selling,
            is_buying_climax=is_buying,
            is_elevated_volume=is_elevated,
        )

    def evaluate(
        self,
        bars_15m: Sequence[KlineBar],
        bars_5m: Optional[Sequence[KlineBar]] = None,
    ) -> TellTaleEvaluation:
        """Evaluates Tell-Tale Climax status on 15m and optional 5m closed bars."""
        res_15m = self._analyze_bar_series(bars_15m, timeframe="15m") if bars_15m else None
        res_5m = self._analyze_bar_series(bars_5m, timeframe="5m") if bars_5m else None

        now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        # Determine disruption status
        is_selling_climax = False
        is_buying_climax = False
        disruption_detected = False
        climax_type = "NONE"

        if res_15m and res_5m:
            if res_15m.is_selling_climax and res_5m.is_selling_climax:
                is_selling_climax = True
                disruption_detected = True
                climax_type = "SELLING_CLIMAX"
                plain = f"🚨 DUAL 5M+15M TELL-TALE SELLING CLIMAX (15m: {res_15m.relvol:.1f}x • 5m: {res_5m.relvol:.1f}x)"
            elif res_15m.is_buying_climax and res_5m.is_buying_climax:
                is_buying_climax = True
                disruption_detected = True
                climax_type = "BUYING_CLIMAX"
                plain = f"🚨 DUAL 5M+15M TELL-TALE BUYING CLIMAX (15m: {res_15m.relvol:.1f}x • 5m: {res_5m.relvol:.1f}x)"
            elif res_15m.is_selling_climax:
                is_selling_climax = True
                disruption_detected = True
                climax_type = "SELLING_CLIMAX"
                plain = f"⚠️ 15M TELL-TALE SELLING CLIMAX (Vol: {res_15m.relvol:.1f}x • Body: {res_15m.body_range:.2f})"
            elif res_15m.is_buying_climax:
                is_buying_climax = True
                disruption_detected = True
                climax_type = "BUYING_CLIMAX"
                plain = f"⚠️ 15M TELL-TALE BUYING CLIMAX (Vol: {res_15m.relvol:.1f}x • Body: {res_15m.body_range:.2f})"
            elif res_5m.is_selling_climax:
                disruption_detected = True
                climax_type = "SELLING_CLIMAX"
                plain = f"⚡ 5M HIGH-VOLUME FLUSH (Vol: {res_5m.relvol:.1f}x • Awaiting 15m bar close)"
            elif res_5m.is_buying_climax:
                disruption_detected = True
                climax_type = "BUYING_CLIMAX"
                plain = f"⚡ 5M HIGH-VOLUME SURGE (Vol: {res_5m.relvol:.1f}x • Awaiting 15m bar close)"
            else:
                rel_str = f"15m: {res_15m.relvol:.1f}x" if res_15m else "N/A"
                plain = f"NORMAL ORDER FLOW (RelVol {rel_str} < 5.0x • No Climax)"
        elif res_15m:
            if res_15m.is_selling_climax:
                is_selling_climax = True
                disruption_detected = True
                climax_type = "SELLING_CLIMAX"
                plain = f"🚨 15M TELL-TALE SELLING CLIMAX (Vol: {res_15m.relvol:.1f}x • Body: {res_15m.body_range:.2f})"
            elif res_15m.is_buying_climax:
                is_buying_climax = True
                disruption_detected = True
                climax_type = "BUYING_CLIMAX"
                plain = f"🚨 15M TELL-TALE BUYING CLIMAX (Vol: {res_15m.relvol:.1f}x • Body: {res_15m.body_range:.2f})"
            else:
                if res_15m.is_elevated_volume:
                    plain = f"ELEVATED VOLUME PULSE (15m RelVol: {res_15m.relvol:.1f}x • Approaching 5.0x climax)"
                else:
                    plain = f"NORMAL ORDER FLOW (15m RelVol: {res_15m.relvol:.1f}x • Body: {res_15m.body_range:.2f})"
        else:
            plain = "INSUFFICIENT BAR DATA FOR 20-PERIOD VOLUME BASELINE"

        return TellTaleEvaluation(
            timestamp_utc=now_utc,
            bar_15m=res_15m,
            bar_5m=res_5m,
            is_selling_climax=is_selling_climax,
            is_buying_climax=is_buying_climax,
            disruption_detected=disruption_detected,
            climax_type=climax_type,
            plain_status=plain,
        )
