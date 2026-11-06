"""SLSP Trade Lifecycle & Risk Execution Manager (SLSP Sections 6, 7, 8).

Manages active positions, stop ratcheting, scale-outs, circuit breakers,
and trade persistence for Tab [13]: Structure + Level Swing Protocol.

Rules strictly implemented:
- Stop Loss: Below swing low (longs) or above swing high (shorts), outside level zone.
- Breakeven Ratchet: Move stop to Entry (+ 0.1% fee) strictly after price reaches +1.0R.
- Take Profit 1: Harvest 50% of position size at +1.5R.
- Take Profit 2: Target / trail remaining 50% at +2.5R or behind 4H higher-lows.
- 4H Invalidation: Immediate exit if a 4H bar closes beyond the stop loss.
- Daily Structure Invalidation: Immediate exit if Daily structure breaks against the trade.
- Circuit Breakers: Max 2.0% daily loss, max 4.0% weekly loss.
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class SLSPActiveTrade:
    """Represents an active or recent SLSP trade."""

    trade_id: str
    direction: str  # "LONG" or "SHORT"
    entry_time_utc: str
    entry_price: float
    initial_stop: float
    current_stop: float
    tp1_price: float
    tp2_price: float
    initial_size_btc: float
    remaining_size_btc: float
    risk_usd: float
    notional_usd: float
    state: str = "OPEN"  # "OPEN", "TP1_HARVESTED", "CLOSED_STOP", "CLOSED_TP2", "CLOSED_INVALIDATED"
    be_ratcheted: bool = False
    tp1_harvested: bool = False
    realized_pnl_usd: float = 0.0
    unrealized_pnl_usd: float = 0.0
    exit_time_utc: str = ""
    exit_price: float = 0.0
    exit_reason: str = ""
    notes: List[str] = field(default_factory=list)


class SLSPTradeManager:
    """Manages SLSP execution state, stop ratcheting, circuit breakers, and persistence."""

    def __init__(
        self,
        state_path: Optional[Path] = None,
        account_equity: float = 100_000.0,
        risk_pct: float = 0.75,
        max_daily_loss_pct: float = 2.0,
        max_weekly_loss_pct: float = 4.0,
    ) -> None:
        self.state_path = state_path or Path("data/slsp_trade_state.json")
        self.account_equity = account_equity
        self.risk_pct = min(risk_pct, 1.0)  # Capped at 1.0% hard rule
        self.max_daily_loss_pct = max_daily_loss_pct
        self.max_weekly_loss_pct = max_weekly_loss_pct

        self.active_trade: Optional[SLSPActiveTrade] = None
        self.daily_realized_loss_usd: float = 0.0
        self.weekly_realized_loss_usd: float = 0.0
        self.last_daily_reset_date: str = ""
        self.last_weekly_reset_week: str = ""
        self.closed_trades_history: List[Dict[str, Any]] = []

        self._load_state()

    def _get_utc_date_str(self) -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")

    def _get_utc_week_str(self) -> str:
        now = datetime.now(timezone.utc)
        return f"{now.year}-W{now.isocalendar().week:02d}"

    def _check_and_reset_circuit_breakers(self) -> None:
        """Resets daily loss tracker at 00:00 UTC and weekly loss tracker on Monday 00:00 UTC."""
        cur_date = self._get_utc_date_str()
        cur_week = self._get_utc_week_str()

        if not self.last_daily_reset_date:
            self.last_daily_reset_date = cur_date
        elif self.last_daily_reset_date != cur_date:
            self.daily_realized_loss_usd = 0.0
            self.last_daily_reset_date = cur_date

        if not self.last_weekly_reset_week:
            self.last_weekly_reset_week = cur_week
        elif self.last_weekly_reset_week != cur_week:
            self.weekly_realized_loss_usd = 0.0
            self.last_weekly_reset_week = cur_week

    def is_circuit_breaker_active(self) -> Tuple[bool, str]:
        """Checks if daily or weekly circuit breaker is currently breached."""
        self._check_and_reset_circuit_breakers()

        daily_loss_pct = (self.daily_realized_loss_usd / max(self.account_equity, 1.0)) * 100.0
        weekly_loss_pct = (self.weekly_realized_loss_usd / max(self.account_equity, 1.0)) * 100.0

        if daily_loss_pct >= self.max_daily_loss_pct:
            return True, f"DAILY LOSS LOCKOUT ({daily_loss_pct:.2f}% >= {self.max_daily_loss_pct:.1f}% MAX)"
        if weekly_loss_pct >= self.max_weekly_loss_pct:
            return True, f"WEEKLY LOSS LOCKOUT ({weekly_loss_pct:.2f}% >= {self.max_weekly_loss_pct:.1f}% MAX)"

        return False, ""

    def calculate_sizing(
        self,
        entry_price: float,
        stop_price: float,
        equity: Optional[float] = None,
        risk_pct_override: Optional[float] = None,
    ) -> Tuple[float, float, float]:
        """Calculates exact risk USD, position size in BTC, and notional USD."""
        eq = equity or self.account_equity
        r_pct = min(risk_pct_override or self.risk_pct, 1.0)
        risk_usd = eq * (r_pct / 100.0)

        risk_per_coin = abs(entry_price - stop_price)
        if risk_per_coin <= 0:
            return 0.0, 0.0, 0.0

        size_btc = round(risk_usd / risk_per_coin, 4)
        notional_usd = round(size_btc * entry_price, 2)

        # Institutional safeguard: Cap notional to 100% equity (zero-leverage spot rule)
        if notional_usd > eq:
            size_btc = round(eq / entry_price, 4)
            notional_usd = round(size_btc * entry_price, 2)
            risk_usd = round(size_btc * risk_per_coin, 2)

        return risk_usd, size_btc, notional_usd

    def open_trade(
        self,
        trade_id: str,
        direction: str,
        entry_price: float,
        stop_loss: float,
        size_btc: float,
        tp1_price: float,
        tp2_price: float,
        notes: Optional[List[str]] = None,
    ) -> bool:
        """Opens a new SLSP position if no trade is active and circuit breaker is clear."""
        cb_active, cb_reason = self.is_circuit_breaker_active()
        if cb_active:
            logger.warning("SLSP Trade rejected by Circuit Breaker: %s", cb_reason)
            return False

        if self.active_trade and self.active_trade.state in ("OPEN", "TP1_HARVESTED"):
            logger.warning("SLSP Trade already active: %s", self.active_trade.trade_id)
            return False

        risk_usd = abs(entry_price - stop_loss) * size_btc
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        self.active_trade = SLSPActiveTrade(
            trade_id=trade_id,
            direction=direction.upper(),
            entry_time_utc=now_str,
            entry_price=entry_price,
            initial_stop=stop_loss,
            current_stop=stop_loss,
            tp1_price=tp1_price,
            tp2_price=tp2_price,
            initial_size_btc=size_btc,
            remaining_size_btc=size_btc,
            risk_usd=risk_usd,
            notional_usd=round(size_btc * entry_price, 2),
            state="OPEN",
            notes=notes or [],
        )
        self._save_state()
        return True

    def update_tick(
        self,
        current_price: float,
        last_4h_close: Optional[float] = None,
        daily_regime: str = "UPTREND",
    ) -> Optional[SLSPActiveTrade]:
        """Evaluates active trade tick, checking stops, 1.0R BE ratchet, 1.5R TP1, 2.5R TP2."""
        trade = self.active_trade
        if not trade or trade.state not in ("OPEN", "TP1_HARVESTED"):
            return trade

        self._check_and_reset_circuit_breakers()

        risk_per_coin = abs(trade.entry_price - trade.initial_stop)
        is_long = trade.direction == "LONG"

        # 1. Calculate Unrealized PnL
        if is_long:
            trade.unrealized_pnl_usd = round(
                (current_price - trade.entry_price) * trade.remaining_size_btc, 2
            )
        else:
            trade.unrealized_pnl_usd = round(
                (trade.entry_price - current_price) * trade.remaining_size_btc, 2
            )

        # 2. Check Breakeven Ratchet (+1.0R Rule)
        # Move stop to Entry + 0.1% (fees) once price reaches +1.0R
        if not trade.be_ratcheted and risk_per_coin > 0:
            one_r_target = (
                trade.entry_price + risk_per_coin
                if is_long
                else trade.entry_price - risk_per_coin
            )
            if (is_long and current_price >= one_r_target) or (
                not is_long and current_price <= one_r_target
            ):
                # Set stop to breakeven + fee buffer (0.10%)
                be_stop = (
                    round(trade.entry_price * 1.001, 2)
                    if is_long
                    else round(trade.entry_price * 0.999, 2)
                )
                trade.current_stop = be_stop
                trade.be_ratcheted = True
                trade.notes.append(
                    f"RATCHETED TO BREAKEVEN @ {be_stop:,.2f} (+1.0R hit at {current_price:,.2f})"
                )

        # 3. Check Take Profit 1 (+1.5R Scale-out 50%)
        if not trade.tp1_harvested and trade.state == "OPEN":
            if (is_long and current_price >= trade.tp1_price) or (
                not is_long and current_price <= trade.tp1_price
            ):
                harvest_btc = round(trade.initial_size_btc * 0.5, 4)
                trade.remaining_size_btc = round(trade.initial_size_btc - harvest_btc, 4)
                pnl_harvest = (
                    (trade.tp1_price - trade.entry_price) * harvest_btc
                    if is_long
                    else (trade.entry_price - trade.tp1_price) * harvest_btc
                )
                trade.realized_pnl_usd += round(pnl_harvest, 2)
                trade.tp1_harvested = True
                trade.state = "TP1_HARVESTED"
                trade.notes.append(
                    f"TP1 HARVESTED: 50% ({harvest_btc:.4f} BTC) scaled out at {trade.tp1_price:,.2f} (+${pnl_harvest:.2f})"
                )

        # 4. Check Take Profit 2 (+2.5R Runner Exit)
        if trade.state in ("OPEN", "TP1_HARVESTED"):
            if (is_long and current_price >= trade.tp2_price) or (
                not is_long and current_price <= trade.tp2_price
            ):
                pnl_tp2 = (
                    (trade.tp2_price - trade.entry_price) * trade.remaining_size_btc
                    if is_long
                    else (trade.entry_price - trade.tp2_price) * trade.remaining_size_btc
                )
                trade.realized_pnl_usd += round(pnl_tp2, 2)
                trade.remaining_size_btc = 0.0
                trade.unrealized_pnl_usd = 0.0
                trade.state = "CLOSED_TP2"
                trade.exit_price = trade.tp2_price
                trade.exit_time_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
                trade.exit_reason = f"TP2 HIT @ {trade.tp2_price:,.2f} (+2.5R Completed)"
                self._record_closed_trade(trade)
                self._save_state()
                return trade

        # 5. Check Hard Stop Loss Exit
        hit_stop = (
            (current_price <= trade.current_stop)
            if is_long
            else (current_price >= trade.current_stop)
        )
        if hit_stop:
            loss_pnl = (
                (trade.current_stop - trade.entry_price) * trade.remaining_size_btc
                if is_long
                else (trade.entry_price - trade.current_stop) * trade.remaining_size_btc
            )
            trade.realized_pnl_usd += round(loss_pnl, 2)
            trade.remaining_size_btc = 0.0
            trade.unrealized_pnl_usd = 0.0
            trade.state = "CLOSED_STOP"
            trade.exit_price = trade.current_stop
            trade.exit_time_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            trade.exit_reason = f"STOP HIT @ {trade.current_stop:,.2f}"
            self._update_circuit_breakers_on_loss(loss_pnl)
            self._record_closed_trade(trade)
            self._save_state()
            return trade

        # 6. Check 4H Invalidation Close (SLSP Section 6 Rule)
        # If price closes beyond the stop level on the 4H, exit immediately.
        if last_4h_close is not None:
            four_h_breached = (
                (last_4h_close < trade.initial_stop)
                if is_long
                else (last_4h_close > trade.initial_stop)
            )
            if four_h_breached:
                inval_pnl = (
                    (current_price - trade.entry_price) * trade.remaining_size_btc
                    if is_long
                    else (trade.entry_price - current_price) * trade.remaining_size_btc
                )
                trade.realized_pnl_usd += round(inval_pnl, 2)
                trade.remaining_size_btc = 0.0
                trade.unrealized_pnl_usd = 0.0
                trade.state = "CLOSED_INVALIDATED"
                trade.exit_price = current_price
                trade.exit_time_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
                trade.exit_reason = f"4H CLOSE INVALIDATION @ {last_4h_close:,.2f}"
                if inval_pnl < 0:
                    self._update_circuit_breakers_on_loss(inval_pnl)
                self._record_closed_trade(trade)
                self._save_state()
                return trade

        # 7. Check Daily Regime Invalidation (SLSP Section 8 Rule)
        # If regime changes while in trade (e.g. daily structure breaks), exit on next 4H close.
        if (is_long and daily_regime == "DOWNTREND") or (
            not is_long and daily_regime == "UPTREND"
        ):
            if last_4h_close is not None:
                reg_pnl = (
                    (current_price - trade.entry_price) * trade.remaining_size_btc
                    if is_long
                    else (trade.entry_price - current_price) * trade.remaining_size_btc
                )
                trade.realized_pnl_usd += round(reg_pnl, 2)
                trade.remaining_size_btc = 0.0
                trade.unrealized_pnl_usd = 0.0
                trade.state = "CLOSED_INVALIDATED"
                trade.exit_price = current_price
                trade.exit_time_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
                trade.exit_reason = f"DAILY REGIME FLIP ({daily_regime})"
                if reg_pnl < 0:
                    self._update_circuit_breakers_on_loss(reg_pnl)
                self._record_closed_trade(trade)
                self._save_state()
                return trade

        self._save_state()
        return trade

    def _update_circuit_breakers_on_loss(self, pnl: float) -> None:
        """Accrues losses towards daily and weekly circuit breakers."""
        if pnl < 0:
            loss_amount = abs(pnl)
            self.daily_realized_loss_usd += loss_amount
            self.weekly_realized_loss_usd += loss_amount

    def _record_closed_trade(self, trade: SLSPActiveTrade) -> None:
        """Appends closed trade summary to rolling history."""
        record = asdict(trade)
        self.closed_trades_history.append(record)
        if len(self.closed_trades_history) > 50:
            self.closed_trades_history = self.closed_trades_history[-50:]

    def _save_state(self) -> None:
        """Safely persists state to disk using atomic rename."""
        try:
            self.state_path.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "active_trade": asdict(self.active_trade) if self.active_trade else None,
                "daily_realized_loss_usd": self.daily_realized_loss_usd,
                "weekly_realized_loss_usd": self.weekly_realized_loss_usd,
                "last_daily_reset_date": self.last_daily_reset_date,
                "last_weekly_reset_week": self.last_weekly_reset_week,
                "closed_trades_history": self.closed_trades_history,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            tmp = tempfile.NamedTemporaryFile("w", dir=self.state_path.parent, delete=False)
            json.dump(data, tmp, indent=2)
            tmp_path = tmp.name
            tmp.close()
            os.replace(tmp_path, self.state_path)
        except Exception as e:
            logger.error("Failed to save SLSP trade state: %s", e)

    def _load_state(self) -> None:
        """Loads state from disk if available."""
        if not self.state_path.exists():
            return
        try:
            with open(self.state_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            t_data = data.get("active_trade")
            if t_data:
                self.active_trade = SLSPActiveTrade(**t_data)
            self.daily_realized_loss_usd = float(data.get("daily_realized_loss_usd", 0.0))
            self.weekly_realized_loss_usd = float(data.get("weekly_realized_loss_usd", 0.0))
            self.last_daily_reset_date = str(data.get("last_daily_reset_date", ""))
            self.last_weekly_reset_week = str(data.get("last_weekly_reset_week", ""))
            self.closed_trades_history = data.get("closed_trades_history", [])
        except Exception as e:
            logger.warning("Failed to load SLSP trade state: %s", e)
