"""Async-safe central StateStore managing rolling ring buffers and live tick state."""

import asyncio
import time
from collections import deque
from datetime import datetime, timezone
from typing import Deque, Dict, List, Optional, Tuple

import numpy as np

from .models import (
    DerivativesSnapshot,
    EMAStrategySnapshot,
    ExhaustionRadarEvaluation,
    FlowSnapshot,
    Gartley5StrategyEvaluation,
    KlineBar,
    MacroRadarEvaluation,
    MasterSynthesisEvaluation,
    MMBTCEvaluation,
    ProtocolV13Evaluation,
    RegimeMatrixEvaluation,
    SignalEvaluation,
    TrapRadarEvaluation,
    VolatilityConeEvaluation,
    VolumeProfileResult,
)


class StateStore:
    """Centralized state container for klines, real-time WS ticks, OI history, and signals."""

    def __init__(self) -> None:
        self._lock = asyncio.Lock()

        # --- Historical + Developing Kline Ring Buffers ---
        self.spot_klines_1w: Deque[KlineBar] = deque(maxlen=120)
        self.spot_klines_1d: Deque[KlineBar] = deque(maxlen=300)
        self.perp_klines_1d: Deque[KlineBar] = deque(maxlen=300)
        self.spot_klines_4h: Deque[KlineBar] = deque(maxlen=300)
        self.spot_klines_1h: Deque[KlineBar] = deque(maxlen=800)
        self.perp_klines_1h: Deque[KlineBar] = deque(maxlen=800)
        self.spot_klines_15m: Deque[KlineBar] = deque(maxlen=400)
        self.perp_klines_15m: Deque[KlineBar] = deque(maxlen=400)

        # --- Active HUD Tab State (1 = Swing Engine, 2 = Protocol v1.3, 3 = Macro & Cycle Radar) ---
        self.active_tab: int = 1

        # --- Live Tick & Session Accumulators ---
        self.binance_spot_price: float = 0.0
        self.binance_perp_price: float = 0.0
        self.coinbase_spot_price: float = 0.0

        self.session_spot_cvd: float = 0.0
        self.session_perp_cvd: float = 0.0
        self.utc_day_spot_cvd: float = 0.0
        self.utc_day_perp_cvd: float = 0.0
        self.current_utc_date: str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        self.spot_trade_count: int = 0
        self.perp_trade_count: int = 0

        # Live intrabar tick delta since last REST kline sync
        self.live_15m_bucket_ms: int = 0
        self.live_spot_buy_15m: float = 0.0
        self.live_spot_sell_15m: float = 0.0
        self.live_perp_buy_15m: float = 0.0
        self.live_perp_sell_15m: float = 0.0

        # --- Derivatives & Basis Time Series ---
        self.open_interest_btc: float = 0.0
        self.open_interest_usd: float = 0.0
        self.funding_rate_pct: float = 0.0
        self.taker_long_short_ratio_5m: float = 1.0
        self.perp_5m_delta_btc: float = 0.0
        self.perp_source: str = "Binance USD-M"
        # interval -> number of candle-body-estimated perp bars excluded from analytics
        self.perp_estimated_bars_excluded: Dict[str, int] = {}

        # (timestamp_sec, oi_btc)
        self.oi_history: Deque[Tuple[float, float]] = deque(maxlen=600)
        # (timestamp_sec, cpi_pct)
        self.cpi_history: Deque[Tuple[float, float]] = deque(maxlen=1000)

        # --- Computed Analytics Snapshots ---
        self.macro_profile: Optional[VolumeProfileResult] = None
        self.tactical_profile: Optional[VolumeProfileResult] = None
        self.session_profile: Optional[VolumeProfileResult] = None
        self.flow_snapshot: FlowSnapshot = FlowSnapshot()
        self.derivatives_snapshot: DerivativesSnapshot = DerivativesSnapshot()
        self.latest_signal: Optional[SignalEvaluation] = None
        self.protocol_evaluation: Optional[ProtocolV13Evaluation] = None
        self.macro_evaluation: Optional[MacroRadarEvaluation] = None
        self.regime_matrix_evaluation: Optional[RegimeMatrixEvaluation] = None
        self.master_synthesis_evaluation: Optional[MasterSynthesisEvaluation] = None
        self.mm_btc_evaluation: Optional[MMBTCEvaluation] = None
        self.volatility_cone_evaluation: Optional[VolatilityConeEvaluation] = None
        self.gartley_evaluation: Optional[Gartley5StrategyEvaluation] = None
        self.trap_evaluation: Optional[TrapRadarEvaluation] = None
        self.exhaustion_evaluation: Optional[ExhaustionRadarEvaluation] = None
        self.ema_strategy: Optional[EMAStrategySnapshot] = None
        self.macro_intermarket: Any = None
        self.protocol_dossier: Optional[Dict[str, Any]] = None

        # --- Connection & System Health ---
        self.warmup_complete: bool = False
        self.spot_ws_connected: bool = False
        self.perp_ws_connected: bool = False
        self.coinbase_ws_connected: bool = False
        self.last_spot_tick_ts: float = 0.0
        self.last_perp_tick_ts: float = 0.0
        self.last_cb_tick_ts: float = 0.0
        self.last_packet_copied_utc: str = ""
        self.last_packet_copied_ts: float = 0.0
        self.last_packet_char_count: int = 0

    def _check_utc_day_rollover(self) -> None:
        """Resets UTC daily session CVD at 00:00 UTC boundary."""
        now_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if now_date != self.current_utc_date:
            self.current_utc_date = now_date
            self.utc_day_spot_cvd = 0.0
            self.utc_day_perp_cvd = 0.0

    def _check_15m_bucket_rollover(self, now_ms: int) -> None:
        """Resets intrabar live tick accumulators when a new 15m boundary starts."""
        bucket_ms = (now_ms // 900_000) * 900_000
        if bucket_ms != self.live_15m_bucket_ms:
            self.live_15m_bucket_ms = bucket_ms
            self.live_spot_buy_15m = 0.0
            self.live_spot_sell_15m = 0.0
            self.live_perp_buy_15m = 0.0
            self.live_perp_sell_15m = 0.0

    def record_spot_trade(self, price: float, qty: float, is_buyer_maker: bool, ts_ms: int) -> None:
        """Records a real-time Spot aggTrade tick (O(1) non-blocking)."""
        self._check_utc_day_rollover()
        self._check_15m_bucket_rollover(ts_ms)

        self.binance_spot_price = price
        self.spot_trade_count += 1
        self.last_spot_tick_ts = time.time()

        # is_buyer_maker == True -> Seller was the aggressive Taker
        delta = -qty if is_buyer_maker else qty
        self.session_spot_cvd += delta
        self.utc_day_spot_cvd += delta

        if is_buyer_maker:
            self.live_spot_sell_15m += qty
        else:
            self.live_spot_buy_15m += qty

        # Update developing kline tip if available
        if self.spot_klines_15m:
            tip = self.spot_klines_15m[-1]
            tip.close = price
            tip.high = max(tip.high, price)
            tip.low = min(tip.low, price)
            tip.volume += qty
            if not is_buyer_maker:
                tip.taker_buy_volume += qty

        if self.spot_klines_1h:
            tip_1h = self.spot_klines_1h[-1]
            tip_1h.close = price
            tip_1h.high = max(tip_1h.high, price)
            tip_1h.low = min(tip_1h.low, price)
            tip_1h.volume += qty
            if not is_buyer_maker:
                tip_1h.taker_buy_volume += qty

        if self.spot_klines_4h:
            tip_4h = self.spot_klines_4h[-1]
            tip_4h.close = price
            tip_4h.high = max(tip_4h.high, price)
            tip_4h.low = min(tip_4h.low, price)
            tip_4h.volume += qty
            if not is_buyer_maker:
                tip_4h.taker_buy_volume += qty

        if self.spot_klines_1d:
            tip_1d = self.spot_klines_1d[-1]
            tip_1d.close = price
            tip_1d.high = max(tip_1d.high, price)
            tip_1d.low = min(tip_1d.low, price)
            tip_1d.volume += qty
            if not is_buyer_maker:
                tip_1d.taker_buy_volume += qty

        if self.spot_klines_1w:
            tip_1w = self.spot_klines_1w[-1]
            tip_1w.close = price
            tip_1w.high = max(tip_1w.high, price)
            tip_1w.low = min(tip_1w.low, price)
            tip_1w.volume += qty
            if not is_buyer_maker:
                tip_1w.taker_buy_volume += qty

        self._record_cpi_sample()

    def record_perp_trade(self, price: float, qty: float, is_buyer_maker: bool, ts_ms: int) -> None:
        """Records a real-time Perpetual Futures aggTrade tick (O(1) non-blocking)."""
        self._check_utc_day_rollover()
        self._check_15m_bucket_rollover(ts_ms)

        self.binance_perp_price = price
        self.perp_trade_count += 1
        self.last_perp_tick_ts = time.time()

        delta = -qty if is_buyer_maker else qty
        self.session_perp_cvd += delta
        self.utc_day_perp_cvd += delta

        if is_buyer_maker:
            self.live_perp_sell_15m += qty
        else:
            self.live_perp_buy_15m += qty

        if self.perp_klines_15m:
            tip = self.perp_klines_15m[-1]
            tip.close = price
            tip.high = max(tip.high, price)
            tip.low = min(tip.low, price)
            tip.volume += qty
            if not is_buyer_maker:
                tip.taker_buy_volume += qty

        if self.perp_klines_1h:
            tip_1h = self.perp_klines_1h[-1]
            tip_1h.close = price
            tip_1h.high = max(tip_1h.high, price)
            tip_1h.low = min(tip_1h.low, price)
            tip_1h.volume += qty
            if not is_buyer_maker:
                tip_1h.taker_buy_volume += qty

        if self.perp_klines_1d:
            tip_1d = self.perp_klines_1d[-1]
            tip_1d.close = price
            tip_1d.high = max(tip_1d.high, price)
            tip_1d.low = min(tip_1d.low, price)
            tip_1d.volume += qty
            if not is_buyer_maker:
                tip_1d.taker_buy_volume += qty

    def record_coinbase_price(self, price: float) -> None:
        """Updates live Coinbase BTC-USD spot price and records CPI sample."""
        self.coinbase_spot_price = price
        self.last_cb_tick_ts = time.time()
        self._record_cpi_sample()

    def _record_cpi_sample(self) -> None:
        """Records a Coinbase Premium Index sample at most once per 2 seconds."""
        if self.binance_spot_price <= 0 or self.coinbase_spot_price <= 0:
            return
        now = time.time()
        if self.cpi_history and (now - self.cpi_history[-1][0]) < 2.0:
            return
        cpi_pct = ((self.coinbase_spot_price - self.binance_spot_price) / self.binance_spot_price) * 100.0
        self.cpi_history.append((now, cpi_pct))

    def record_oi_sample(self, oi_btc: float, ts_sec: Optional[float] = None) -> None:
        """Appends an Open Interest datapoint to the rolling history buffer."""
        now = ts_sec if ts_sec is not None else time.time()
        self.open_interest_btc = oi_btc
        ref_price = self.binance_perp_price or self.binance_spot_price
        self.open_interest_usd = oi_btc * ref_price
        if not self.oi_history or (now - self.oi_history[-1][0]) >= 5.0:
            self.oi_history.append((now, oi_btc))

    def get_oi_change_pct(self, lookback_seconds: float) -> float:
        """Calculates percentage change in Open Interest over `lookback_seconds`."""
        if len(self.oi_history) < 2 or self.open_interest_btc <= 0:
            return 0.0
        now = self.oi_history[-1][0]
        target_ts = now - lookback_seconds
        # Find sample closest to target_ts
        best_oi = self.oi_history[0][1]
        best_diff = abs(self.oi_history[0][0] - target_ts)
        for ts, oi_val in self.oi_history:
            diff = abs(ts - target_ts)
            if diff < best_diff:
                best_diff = diff
                best_oi = oi_val
        if best_oi <= 0:
            return 0.0
        return ((self.open_interest_btc - best_oi) / best_oi) * 100.0

    def get_cpi_metrics(self) -> Tuple[float, float, float]:
        """Returns (premium_usd, premium_pct, premium_zscore)."""
        if self.binance_spot_price <= 0 or self.coinbase_spot_price <= 0:
            return 0.0, 0.0, 0.0
        prem_usd = self.coinbase_spot_price - self.binance_spot_price
        prem_pct = (prem_usd / self.binance_spot_price) * 100.0
        if len(self.cpi_history) < 10:
            return prem_usd, prem_pct, 0.0
        vals = np.array([x[1] for x in self.cpi_history], dtype=float)
        std = float(np.std(vals))
        mean = float(np.mean(vals))
        zscore = (prem_pct - mean) / std if std > 1e-6 else 0.0
        return prem_usd, prem_pct, float(zscore)

    async def set_klines(
        self,
        venue: str,
        interval: str,
        bars: List[KlineBar],
    ) -> None:
        """Safely replaces or updates a kline ring buffer."""
        async with self._lock:
            target: Optional[Deque[KlineBar]] = None
            if venue == "spot" and interval == "1h":
                target = self.spot_klines_1h
            elif venue == "perp" and interval == "1h":
                target = self.perp_klines_1h
            elif venue == "spot" and interval == "4h":
                target = self.spot_klines_4h
            elif venue == "spot" and interval == "15m":
                target = self.spot_klines_15m
            elif venue == "perp" and interval == "15m":
                target = self.perp_klines_15m
            elif venue == "spot" and interval == "1d":
                target = self.spot_klines_1d
            elif venue == "perp" and interval == "1d":
                target = self.perp_klines_1d
            elif venue == "spot" and interval == "1w":
                target = self.spot_klines_1w

            if target is not None and venue == "perp":
                measured = [b for b in bars if not getattr(b, "estimated", False)]
                self.perp_estimated_bars_excluded[interval] = len(bars) - len(measured)
                bars = measured
                if not bars:
                    target.clear()
            if target is not None and bars:
                target.clear()
                target.extend(bars)
                if venue == "spot" and self.binance_spot_price == 0.0:
                    self.binance_spot_price = bars[-1].close
                elif venue == "perp" and self.binance_perp_price == 0.0:
                    self.binance_perp_price = bars[-1].close
