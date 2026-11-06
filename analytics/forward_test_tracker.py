"""Triple-Variant Parallel Forward Test Tracking & Paper Lifecycle Engine.

Tracks performance concurrently across 3 distinct trading architectures:
1. OPT_1_PURE_FP: Pure 15-Minute Footprint Microstructure (Intraday Scalp / Day Trade)
   - Triggers on lower-wick seller absorption OR stacked buy imbalances + positive delta flip.
   - Ignores macro anchors, funding rates, CVD divergence, NTZ shield, 200 SMA.
2. OPT_2_4GATE: Standard 4-Gate Macro Confluence (1H / 4H Tactical Swing)
   - Gate 1 (Macro Anchor Tap) + Gate 2 (Funding/CVD Positioning) + Gate 3 (Wick Absorption) + Gate 4 (Delta Flip).
3. OPT_3_INSTITUTIONAL: Hardened Institutional Cockpit (3D - 3W Spot Swing)
   - Standard 4-Gate + Finished Auction Check + Bar POC Reclaim + Cascade Velocity Dampener + NTZ Master Shield.
   - Deterministic 1.0% / 0.5% capital preservation sizing clamped to 50% equity cap.

Persists atomic trade events to logs/forward_test_footprint.jsonl and state to logs/forward_test_state.json.
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
import time
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence

from core.models import (
    FootprintBarData,
    FootprintEvaluation,
    ForwardTestTrade,
    VariantScorecard,
)

logger = logging.getLogger("forward_test")


class ForwardTestTracker:
    """Simulates paper executions, triple-barrier lifecycles, and comparative metrics across 3 variants."""

    def __init__(
        self,
        logs_dir: str = "logs",
        reference_equity_usd: float = 100000.0,
        enable_persistence: bool = True,
    ) -> None:
        self.logs_dir = logs_dir
        self.reference_equity_usd = float(reference_equity_usd)
        self.enable_persistence = enable_persistence
        self.state_file = os.path.join(self.logs_dir, "forward_test_state.json")
        self.ledger_file = os.path.join(self.logs_dir, "forward_test_footprint.jsonl")

        self.scorecards: Dict[str, VariantScorecard] = {
            "OPT_1_PURE_FP": VariantScorecard(
                variant_id="OPT_1_PURE_FP",
                display_name="1: Pure Footprint",
                timeframe_desc="15m Scalp",
                status="OBSERVING",
            ),
            "OPT_2_4GATE": VariantScorecard(
                variant_id="OPT_2_4GATE",
                display_name="2: 4-Gate Filter",
                timeframe_desc="1H/4H Swing",
                status="OBSERVING",
            ),
            "OPT_3_INSTITUTIONAL": VariantScorecard(
                variant_id="OPT_3_INSTITUTIONAL",
                display_name="3: Institutional",
                timeframe_desc="Spot Swing",
                status="OBSERVING",
            ),
        }

        # Track exit cooldowns (ts_ms) to prevent instantaneous re-entry on same bar
        self._last_exit_ts: Dict[str, float] = {
            "OPT_1_PURE_FP": 0.0,
            "OPT_2_4GATE": 0.0,
            "OPT_3_INSTITUTIONAL": 0.0,
        }

        # Structural level lockout tracker: level_id -> unlock_timestamp_utc (4-hour lockout)
        self.level_lockouts: Dict[str, float] = {}
        # Level stopped-out prices: level_id -> stop_loss_price
        self.level_stop_prices: Dict[str, float] = {}
        self._last_state_mtime: float = 0.0

        self._ensure_logs_dir()
        self.load_state()

    def _ensure_logs_dir(self) -> None:
        """Ensures logs directory exists."""
        try:
            os.makedirs(self.logs_dir, exist_ok=True)
        except Exception:
            pass

    def load_state(self) -> None:
        """Loads persistent forward test state if it exists."""
        if not self.enable_persistence or not os.path.exists(self.state_file):
            return

        try:
            self._last_state_mtime = os.path.getmtime(self.state_file)
            with open(self.state_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            meta = data.get("_meta", {})
            if isinstance(meta, dict):
                self.level_lockouts = {str(k): float(v) for k, v in meta.get("level_lockouts", {}).items()}
                self.level_stop_prices = {str(k): float(v) for k, v in meta.get("level_stop_prices", {}).items()}

            for vid, vdata in data.items():
                if vid.startswith("_"):
                    continue
                if vid in self.scorecards:
                    sc = self.scorecards[vid]
                    sc.total_trades = int(vdata.get("total_trades", 0))
                    sc.winning_trades = int(vdata.get("winning_trades", 0))
                    sc.losing_trades = int(vdata.get("losing_trades", 0))
                    sc.win_rate_pct = float(vdata.get("win_rate_pct", 0.0))
                    sc.realized_pnl_usd = float(vdata.get("realized_pnl_usd", 0.0))
                    sc.peak_pnl_usd = float(vdata.get("peak_pnl_usd", 0.0))
                    sc.max_drawdown_usd = float(vdata.get("max_drawdown_usd", 0.0))
                    sc.max_drawdown_pct = float(vdata.get("max_drawdown_pct", 0.0))
                    sc.last_closed_trade_summary = str(vdata.get("last_closed_trade_summary", ""))

                    trade_dict = vdata.get("active_trade")
                    if trade_dict:
                        sc.active_trade = ForwardTestTrade(**trade_dict)
                        sc.status = "IN_POSITION"
        except Exception as e:
            logger.warning(f"Could not load forward test state: {e}")

    def save_state(self) -> None:
        """Atomically saves forward test state."""
        if not self.enable_persistence:
            return
        self._ensure_logs_dir()
        try:
            dump_data: Dict[str, Any] = {}
            for vid, sc in self.scorecards.items():
                sc_dict = asdict(sc)
                dump_data[vid] = sc_dict

            dump_data["_meta"] = {
                "level_lockouts": self.level_lockouts,
                "level_stop_prices": self.level_stop_prices,
            }

            dir_name = os.path.dirname(self.state_file) or "."
            with tempfile.NamedTemporaryFile("w", dir=dir_name, delete=False, encoding="utf-8") as tf:
                json.dump(dump_data, tf, indent=2)
                temp_path = tf.name

            os.replace(temp_path, self.state_file)
            self._last_state_mtime = os.path.getmtime(self.state_file)
        except Exception as e:
            logger.warning(f"Could not save forward test state: {e}")

    def reset_state(self) -> None:
        """Resets all 3 scorecards back to clean minute-zero state and wipes previous forward test ledger."""
        for vid in ("OPT_1_PURE_FP", "OPT_2_4GATE", "OPT_3_INSTITUTIONAL"):
            sc = self.scorecards[vid]
            sc.total_trades = 0
            sc.winning_trades = 0
            sc.losing_trades = 0
            sc.win_rate_pct = 0.0
            sc.realized_pnl_usd = 0.0
            sc.unrealized_pnl_usd = 0.0
            sc.peak_pnl_usd = 0.0
            sc.max_drawdown_usd = 0.0
            sc.max_drawdown_pct = 0.0
            sc.status = "OBSERVING"
            sc.active_trade = None
            sc.last_closed_trade_summary = ""
            self._last_exit_ts[vid] = 0.0
        self.level_lockouts.clear()
        self.level_stop_prices.clear()
        self.save_state()
        try:
            if os.path.exists(self.ledger_file):
                os.remove(self.ledger_file)
        except Exception:
            pass

    def get_structural_level(
        self,
        eval_res: FootprintEvaluation,
        current_price: float,
        is_buy: bool,
    ) -> Tuple[str, float]:
        """Resolves the structural level name and anchor price for lockout tracking."""
        name = (eval_res.gate1_tapped_level_name or "").strip()
        price = float(eval_res.gate1_tapped_level_price or 0.0)

        if name:
            clean_name = name.split(" [VETO:")[0].strip()
            if price <= 0:
                price = current_price
            return (clean_name, price)

        bucket_price = round(current_price / 250.0) * 250.0
        dir_tag = "SUPPORT" if is_buy else "RESISTANCE"
        return (f"{dir_tag}_SHELF_${int(bucket_price)}", bucket_price)

    def is_level_locked(
        self,
        level_name: str,
        current_price: float,
        is_buy: bool,
        now_ts: float,
    ) -> bool:
        """Enforces 4-Hour Lockout per structural level (Max 1 attempt per level).
        
        If a trade was stopped out at this level within 4 hours (14,400s),
        re-entry at this level is prohibited unless price drops to the NEXT lower macro support shelf
        (at least $200 below the previous stop loss).
        """
        if not level_name:
            return False

        unlock_ts = self.level_lockouts.get(level_name, 0.0)
        if now_ts < unlock_ts:
            stop_price = self.level_stop_prices.get(level_name, current_price)
            if is_buy:
                # Still hovering near the stopped out level -> locked out
                if current_price >= (stop_price - 200.0):
                    return True
            else:
                # Still hovering near the stopped out ceiling -> locked out
                if current_price <= (stop_price + 200.0):
                    return True
        return False

    def is_reclaim_confirmed(
        self,
        level_price: float,
        current_price: float,
        is_buy: bool,
        eval_res: FootprintEvaluation,
        active_bar: Optional[FootprintBarData],
        completed_bars: Sequence[FootprintBarData],
    ) -> bool:
        """Requires a 15m candle close or POC reclaim above the swept level (no intra-bar knife catching)."""
        if eval_res.all_gates_pass:
            return True
        if level_price <= 0:
            return True

        if is_buy:
            # 1. Price must be at or above the level (no catching below level)
            if current_price < (level_price - 25.0):
                return False

            # 2. Check if reclaim is confirmed by completed bar or active bar
            if completed_bars:
                last_c = completed_bars[-1]
                if last_c.close >= (level_price - 25.0) or (last_c.close >= last_c.open and last_c.net_delta > 0):
                    return True

            if active_bar and active_bar.close >= active_bar.open and eval_res.bar_poc_reclaimed:
                return True

            return bool(eval_res.bar_poc_reclaimed and current_price >= level_price)
        else:
            if current_price > (level_price + 25.0):
                return False
            if completed_bars:
                last_c = completed_bars[-1]
                if last_c.close <= (level_price + 25.0) or (last_c.close <= last_c.open and last_c.net_delta < 0):
                    return True
            if active_bar and active_bar.close <= active_bar.open:
                return True
            return current_price <= level_price

    def _append_ledger(self, record: Dict[str, Any]) -> None:
        """Appends an atomic trade execution or update event to the JSONL log."""
        if not self.enable_persistence:
            return
        self._ensure_logs_dir()
        try:
            line = json.dumps(record) + "\n"
            with open(self.ledger_file, "a", encoding="utf-8") as f:
                f.write(line)
        except Exception as e:
            logger.warning(f"Could not append to forward test ledger: {e}")

    def update(
        self,
        current_price: float,
        eval_res: FootprintEvaluation,
        active_bar: Optional[FootprintBarData],
        completed_bars: Sequence[FootprintBarData],
        store: Any,
    ) -> Dict[str, VariantScorecard]:
        """Evaluates live trade lifecycle and entry conditions across all 3 variants."""
        if current_price <= 0:
            return self.scorecards

        if self.enable_persistence and os.path.exists(self.state_file):
            try:
                disk_mtime = os.path.getmtime(self.state_file)
                if disk_mtime > self._last_state_mtime + 0.05:
                    self.load_state()
            except Exception:
                pass

        now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        now_ts = time.time()

        # =========================================================================
        # PHASE 1: MANAGE OPEN TRADES (TRIPLE-BARRIER EVALUATION)
        # =========================================================================
        for vid, sc in self.scorecards.items():
            trade = sc.active_trade
            if trade is None:
                continue

            is_buy = (trade.direction.upper() != "SELL")

            # Update live unrealized PnL (Spot Bidirectional: Long vs USDT Rotation)
            if is_buy:
                unrealized_gain = (current_price - trade.entry_price) * trade.remaining_size
            else:
                unrealized_gain = (trade.entry_price - current_price) * trade.remaining_size

            trade.unrealized_pnl_usd = round(trade.already_realized_pnl + unrealized_gain, 2)
            sc.unrealized_pnl_usd = trade.unrealized_pnl_usd
            dir_label = "BUY" if is_buy else "SELL"
            sc.status = f"IN_POSITION ({dir_label} {trade.remaining_size:.4f} BTC)"

            # 1. Stop Loss Hit
            sl_hit = (current_price <= trade.stop_loss) if is_buy else (current_price >= trade.stop_loss)
            if sl_hit:
                if is_buy:
                    loss = (trade.stop_loss - trade.entry_price) * trade.remaining_size
                else:
                    loss = (trade.entry_price - trade.stop_loss) * trade.remaining_size

                trade.total_realized_pnl = round(trade.already_realized_pnl + loss, 2)
                sc.realized_pnl_usd = round(sc.realized_pnl_usd + loss, 2)
                trade.state = "CLOSED_STOP"
                trade.exit_price = trade.stop_loss
                trade.exit_time_utc = now_utc
                sc.total_trades += 1

                if trade.total_realized_pnl > 0:
                    sc.winning_trades += 1
                    outcome_str = "Win"
                else:
                    sc.losing_trades += 1
                    outcome_str = "Loss"

                sc.win_rate_pct = round((sc.winning_trades / sc.total_trades) * 100.0, 1)

                # Drawdown calculation
                dd = max(0.0, sc.peak_pnl_usd - sc.realized_pnl_usd)
                sc.max_drawdown_usd = max(sc.max_drawdown_usd, dd)
                sc.max_drawdown_pct = round((sc.max_drawdown_usd / self.reference_equity_usd) * 100.0, 2)

                sc.last_closed_trade_summary = f"{trade.direction} @ ${trade.entry_price:,.0f} • {outcome_str} ${trade.total_realized_pnl:+,.2f}"

                self._append_ledger({
                    "timestamp_utc": now_utc,
                    "event": "EXIT_STOP_LOSS",
                    "variant_id": vid,
                    "trade": asdict(trade),
                    "exit_price": trade.exit_price,
                    "realized_pnl_usd": trade.total_realized_pnl,
                })

                # Lockout the structural level for Variants 2 and 3 for 4 hours (14,400 seconds / 16 bars)
                if vid in ("OPT_2_4GATE", "OPT_3_INSTITUTIONAL"):
                    lvl_name = getattr(trade, "level_name", "") or eval_res.gate1_tapped_level_name
                    if not lvl_name:
                        lvl_name, _ = self.get_structural_level(eval_res, trade.entry_price, is_buy)
                    clean_lvl_name = lvl_name.split(" [VETO:")[0].strip()
                    self.level_lockouts[clean_lvl_name] = now_ts + (4.0 * 3600.0)
                    self.level_stop_prices[clean_lvl_name] = trade.stop_loss
                    logger.info(f"[{vid}] Engaged 4-Hour Level Lockout on {clean_lvl_name} until {now_ts + 14400.0}")

                self._last_exit_ts[vid] = now_ts
                sc.active_trade = None
                sc.unrealized_pnl_usd = 0.0
                sc.status = "OBSERVING"
                self.save_state()
                continue

            # Normalize any inverted TP1 / TP2 ordering on open positions
            if is_buy and trade.tp1_price > trade.tp2_price and trade.tp2_price > trade.entry_price:
                trade.tp1_price, trade.tp2_price = trade.tp2_price, trade.tp1_price
            elif (not is_buy) and trade.tp1_price < trade.tp2_price and 0 < trade.tp2_price < trade.entry_price:
                trade.tp1_price, trade.tp2_price = trade.tp2_price, trade.tp1_price

            # 1b. +2.0R Fee-Adjusted Breakeven Ratchet (Protects +2.0R+ open winners before TP1)
            one_r_dist = (
                (trade.risk_usd / trade.size_btc)
                if (trade.risk_usd > 0 and trade.size_btc > 0)
                else max(abs(trade.entry_price - trade.stop_loss), 1.0)
            )
            if vid in ("OPT_2_4GATE", "OPT_3_INSTITUTIONAL"):
                if is_buy and current_price >= (trade.entry_price + 2.0 * one_r_dist):
                    be_plus_fees = round(trade.entry_price * 1.001, 2)
                    if trade.stop_loss < be_plus_fees:
                        trade.stop_loss = be_plus_fees
                        self.save_state()
                elif (not is_buy) and current_price <= (trade.entry_price - 2.0 * one_r_dist):
                    be_plus_fees = round(trade.entry_price * 0.999, 2)
                    if trade.stop_loss > be_plus_fees:
                        trade.stop_loss = be_plus_fees
                        self.save_state()

            # 2. TP1 Hit (50% Trim + Move SL to Breakeven / 1H Higher Low)
            tp1_hit = (current_price >= trade.tp1_price) if is_buy else (current_price <= trade.tp1_price)
            if tp1_hit and not trade.tp1_hit:
                trim_qty = trade.size_btc * 0.5
                if is_buy:
                    gain = (trade.tp1_price - trade.entry_price) * trim_qty
                else:
                    gain = (trade.entry_price - trade.tp1_price) * trim_qty

                trade.already_realized_pnl = round(trade.already_realized_pnl + gain, 2)
                trade.remaining_size = round(trade.remaining_size - trim_qty, 4)
                sc.realized_pnl_usd = round(sc.realized_pnl_usd + gain, 2)
                sc.peak_pnl_usd = max(sc.peak_pnl_usd, sc.realized_pnl_usd)
                trade.tp1_hit = True
                trade.state = "TP1_HIT"
                # Move stop loss to fee-adjusted breakeven or recent 1H higher low (Variants 2 & 3)
                if vid in ("OPT_2_4GATE", "OPT_3_INSTITUTIONAL"):
                    if is_buy:
                        be_floor = round(trade.entry_price * 1.001, 2)
                        klines_1h = getattr(store, "spot_klines_1h", None)
                        recent_1h_hl = 0.0
                        if isinstance(klines_1h, (list, tuple)) and len(klines_1h) >= 2:
                            lows = [getattr(b, "low", 0.0) for b in klines_1h[-3:] if isinstance(getattr(b, "low", 0.0), (int, float))]
                            valid_hls = [round(lw - 15.0, 2) for lw in lows if be_floor < lw < current_price]
                            if valid_hls:
                                recent_1h_hl = max(valid_hls)
                        trade.stop_loss = max(trade.stop_loss, be_floor, recent_1h_hl)
                    else:
                        trade.stop_loss = min(trade.stop_loss, round(trade.entry_price * 0.999, 2))
                else:
                    trade.stop_loss = trade.entry_price

                self._append_ledger({
                    "timestamp_utc": now_utc,
                    "event": "TP1_50PCT_TRIM",
                    "variant_id": vid,
                    "trade": asdict(trade),
                    "tp1_price": trade.tp1_price,
                    "trimmed_qty_btc": trim_qty,
                    "gain_usd": gain,
                })
                self.save_state()

            # 3. TP2 Hit (100% Final Target Harvest)
            tp2_hit = (current_price >= trade.tp2_price) if is_buy else (current_price <= trade.tp2_price)
            if tp2_hit and trade.tp1_hit:
                if is_buy:
                    gain = (trade.tp2_price - trade.entry_price) * trade.remaining_size
                else:
                    gain = (trade.entry_price - trade.tp2_price) * trade.remaining_size

                trade.already_realized_pnl = round(trade.already_realized_pnl + gain, 2)
                trade.total_realized_pnl = trade.already_realized_pnl
                trade.remaining_size = 0.0
                sc.realized_pnl_usd = round(sc.realized_pnl_usd + gain, 2)
                sc.peak_pnl_usd = max(sc.peak_pnl_usd, sc.realized_pnl_usd)
                trade.state = "CLOSED_TP2"
                trade.exit_price = trade.tp2_price
                trade.exit_time_utc = now_utc
                sc.total_trades += 1
                sc.winning_trades += 1
                sc.win_rate_pct = round((sc.winning_trades / sc.total_trades) * 100.0, 1)

                sc.last_closed_trade_summary = f"{trade.direction} @ ${trade.entry_price:,.0f} • Win ${trade.total_realized_pnl:+,.2f}"

                self._append_ledger({
                    "timestamp_utc": now_utc,
                    "event": "EXIT_TP2_FULL_HARVEST",
                    "variant_id": vid,
                    "trade": asdict(trade),
                    "exit_price": trade.exit_price,
                    "realized_pnl_usd": trade.total_realized_pnl,
                })

                self._last_exit_ts[vid] = now_ts
                sc.active_trade = None
                sc.unrealized_pnl_usd = 0.0
                sc.status = "OBSERVING"
                self.save_state()
                continue

        # =========================================================================
        # PHASE 2: EVALUATE NEW ENTRIES (FOR VARIANTS WITHOUT OPEN TRADES)
        # =========================================================================

        # Helper calculations for BUY entries (Support accumulation)
        bar_low = active_bar.low if active_bar else current_price
        lowest_ref = min(bar_low, completed_bars[-1].low if completed_bars else bar_low)
        stop_loss_buy = round(lowest_ref - 25.0, 2)
        stop_dist_buy = max(current_price - stop_loss_buy, 50.0)

        # Helper calculations for SELL entries (Resistance ceiling / Spot USDT rotation)
        bar_high = active_bar.high if active_bar else current_price
        highest_ref = max(bar_high, completed_bars[-1].high if completed_bars else bar_high)
        stop_loss_sell = round(highest_ref + 25.0, 2)
        stop_dist_sell = max(stop_loss_sell - current_price, 50.0)

        # 1.0% risk budget on $100k equity ($1,000), clamped to $50k notional
        risk_budget = self.reference_equity_usd * 0.01
        max_notional = self.reference_equity_usd * 0.50
        max_btc = max_notional / max(current_price, 1.0)

        # Sizing for BUY
        raw_btc_buy = risk_budget / stop_dist_buy
        sized_btc_buy = round(min(raw_btc_buy, max_btc), 4)
        notional_usd_buy = round(sized_btc_buy * current_price, 2)
        eff_risk_usd_buy = round(sized_btc_buy * stop_dist_buy, 2)

        # Sizing for SELL
        raw_btc_sell = risk_budget / stop_dist_sell
        sized_btc_sell = round(min(raw_btc_sell, max_btc), 4)
        notional_usd_sell = round(sized_btc_sell * current_price, 2)
        eff_risk_usd_sell = round(sized_btc_sell * stop_dist_sell, 2)

        has_micro_absorption = False
        if active_bar and (active_bar.has_wick_absorption or active_bar.has_stacked_buy):
            has_micro_absorption = True
        elif completed_bars and (completed_bars[-1].has_wick_absorption or completed_bars[-1].has_stacked_buy):
            has_micro_absorption = True

        has_micro_exhaustion = False
        if active_bar and (active_bar.has_upper_wick_exhaustion or active_bar.has_stacked_sell):
            has_micro_exhaustion = True
        elif completed_bars and (completed_bars[-1].has_upper_wick_exhaustion or completed_bars[-1].has_stacked_sell):
            has_micro_exhaustion = True

        raw_delta_flip_bull = eval_res.delta_flipped_bullish or (
            eval_res.active_bar_delta > 0 and (not completed_bars or eval_res.prev_bar_delta <= 0)
        )
        raw_delta_flip_bear = eval_res.delta_flipped_bearish or (
            eval_res.active_bar_delta < 0 and (not completed_bars or eval_res.prev_bar_delta >= 0)
        )

        # -------------------------------------------------------------------------
        # VARIANT 1: OPT_1_PURE_FP (Pure Footprint Microstructure - 15m Scalp)
        # -------------------------------------------------------------------------
        sc1 = self.scorecards["OPT_1_PURE_FP"]
        if sc1.active_trade is None:
            # 60s cooldown after previous exit to avoid same-tick re-entry
            cooldown_active = (now_ts - self._last_exit_ts["OPT_1_PURE_FP"]) < 60.0
            if cooldown_active:
                sc1.status = "COOLDOWN"
            elif has_micro_absorption and raw_delta_flip_bull:
                trade_id = f"FP15M_{int(now_ts)}"
                tp1 = round(current_price + (2.0 * stop_dist_buy), 2)
                tp2 = round(current_price + (3.0 * stop_dist_buy), 2)
                trade = ForwardTestTrade(
                    trade_id=trade_id,
                    variant_id="OPT_1_PURE_FP",
                    direction="BUY",
                    entry_time_utc=now_utc,
                    entry_price=current_price,
                    stop_loss=stop_loss_buy,
                    tp1_price=tp1,
                    tp2_price=tp2,
                    size_btc=sized_btc_buy,
                    remaining_size=sized_btc_buy,
                    notional_usd=notional_usd_buy,
                    risk_usd=eff_risk_usd_buy,
                    state="OPEN",
                    notes="Pure 15m lower-wick absorption + delta flip bull (Spot Accumulate)",
                )
                sc1.active_trade = trade
                sc1.status = f"IN_POSITION (BUY {sized_btc_buy:.4f} BTC)"
                self._append_ledger({
                    "timestamp_utc": now_utc,
                    "event": "ENTRY_SIGNAL",
                    "variant_id": "OPT_1_PURE_FP",
                    "trade": asdict(trade),
                })
                self.save_state()
            elif has_micro_exhaustion and raw_delta_flip_bear:
                trade_id = f"FP15M_{int(now_ts)}"
                tp1 = round(current_price - (2.0 * stop_dist_sell), 2)
                tp2 = round(current_price - (3.0 * stop_dist_sell), 2)
                trade = ForwardTestTrade(
                    trade_id=trade_id,
                    variant_id="OPT_1_PURE_FP",
                    direction="SELL",
                    entry_time_utc=now_utc,
                    entry_price=current_price,
                    stop_loss=stop_loss_sell,
                    tp1_price=tp1,
                    tp2_price=tp2,
                    size_btc=sized_btc_sell,
                    remaining_size=sized_btc_sell,
                    notional_usd=notional_usd_sell,
                    risk_usd=eff_risk_usd_sell,
                    state="OPEN",
                    notes="Pure 15m upper-wick exhaustion + delta flip bear (Spot USDT Rotation)",
                )
                sc1.active_trade = trade
                sc1.status = f"IN_POSITION (SELL {sized_btc_sell:.4f} BTC)"
                self._append_ledger({
                    "timestamp_utc": now_utc,
                    "event": "ENTRY_SIGNAL",
                    "variant_id": "OPT_1_PURE_FP",
                    "trade": asdict(trade),
                })
                self.save_state()
            elif has_micro_absorption:
                sc1.status = "ARMED (Awaiting Δ Flip)"
            elif has_micro_exhaustion:
                sc1.status = "ARMED (Awaiting Bear Δ Flip)"
            else:
                sc1.status = "OBSERVING"

        # Resolve structural levels, lockouts, and reclaim status
        lvl_name_buy, lvl_price_buy = self.get_structural_level(eval_res, current_price, is_buy=True)
        lvl_name_sell, lvl_price_sell = self.get_structural_level(eval_res, current_price, is_buy=False)

        buy_level_locked = self.is_level_locked(lvl_name_buy, current_price, is_buy=True, now_ts=now_ts)
        sell_level_locked = self.is_level_locked(lvl_name_sell, current_price, is_buy=False, now_ts=now_ts)

        buy_reclaimed = self.is_reclaim_confirmed(lvl_price_buy, current_price, True, eval_res, active_bar, completed_bars)
        sell_reclaimed = self.is_reclaim_confirmed(lvl_price_sell, current_price, False, eval_res, active_bar, completed_bars)

        # -------------------------------------------------------------------------
        # VARIANT 2: OPT_2_4GATE (Standard 4-Gate Confluence - 1H/4H Swing)
        # -------------------------------------------------------------------------
        sc2 = self.scorecards["OPT_2_4GATE"]
        cooldown_active_2 = (now_ts - self._last_exit_ts["OPT_2_4GATE"]) < 900.0

        gate1_ok = eval_res.gate1_macro_tap
        gate2_ok = eval_res.gate2_positioning_crowded
        gate3_ok = eval_res.gate3_wick_absorption
        gate4_ok = raw_delta_flip_bull or eval_res.gate4_delta_flip

        tact_vp = getattr(store, "tactical_profile", None)
        t_poc = getattr(tact_vp, "c_poc", 0.0) if tact_vp else 0.0

        res_tap = eval_res.gate1_level_tap and (eval_res.gate1_level_type == "RESISTANCE" or eval_res.direction == "DISTRIBUTE_SELL")
        sell_gate1_ok = res_tap or eval_res.direction == "DISTRIBUTE_SELL"
        sell_gate2_ok = eval_res.gate2_positioning_crowded or eval_res.cvd_absorption_status != "" or eval_res.funding_rate_pct >= 0.01 or eval_res.all_gates_pass
        sell_gate3_ok = has_micro_exhaustion or eval_res.gate2_absorption or eval_res.all_gates_pass
        sell_gate4_ok = raw_delta_flip_bear or eval_res.all_gates_pass

        # Confluence qualifications
        v2_buy_conditions_met = bool(
            gate1_ok
            and gate2_ok
            and gate3_ok
            and gate4_ok
            and not buy_level_locked
            and buy_reclaimed
        )

        v2_sell_conditions_met = bool(
            sell_gate1_ok
            and sell_gate2_ok
            and sell_gate3_ok
            and sell_gate4_ok
            and not sell_level_locked
            and sell_reclaimed
        )

        if sc2.active_trade is None:
            if cooldown_active_2:
                sc2.status = "COOLDOWN (15m)"
            elif buy_level_locked and gate1_ok:
                sc2.status = f"LOCKED_OUT ({lvl_name_buy[:12]} 4h CD)"
            elif not buy_reclaimed and gate1_ok and gate2_ok and gate3_ok:
                sc2.status = f"AWAITING 15M RECLAIM (${lvl_price_buy:,.0f})"
            elif v2_buy_conditions_met:
                trade_id = f"4GATE_{int(now_ts)}"
                # Target: 7D cPOC or 1:2 R:R for TP1, 30D cPOC or 1:3 for TP2 (always enforce tp1 < tp2)
                raw_tp1 = float(t_poc) if (isinstance(t_poc, (int, float)) and t_poc > current_price) else round(current_price + (2.0 * stop_dist_buy), 2)
                raw_tp2 = round(current_price + (3.0 * stop_dist_buy), 2)
                tp1 = min(raw_tp1, raw_tp2)
                tp2 = max(raw_tp1, raw_tp2)
                if tp2 <= tp1:
                    tp2 = round(tp1 + stop_dist_buy, 2)

                trade = ForwardTestTrade(
                    trade_id=trade_id,
                    variant_id="OPT_2_4GATE",
                    direction="BUY",
                    entry_time_utc=now_utc,
                    entry_price=current_price,
                    stop_loss=stop_loss_buy,
                    tp1_price=tp1,
                    tp2_price=tp2,
                    size_btc=sized_btc_buy,
                    remaining_size=sized_btc_buy,
                    notional_usd=notional_usd_buy,
                    risk_usd=eff_risk_usd_buy,
                    state="OPEN",
                    notes="Standard 4-Gate (Macro Anchor + Positioning + Wick + Delta Flip)",
                    level_name=lvl_name_buy,
                )
                sc2.active_trade = trade
                sc2.status = f"IN_POSITION (BUY {sized_btc_buy:.4f} BTC)"
                self._append_ledger({
                    "timestamp_utc": now_utc,
                    "event": "ENTRY_SIGNAL",
                    "variant_id": "OPT_2_4GATE",
                    "trade": asdict(trade),
                })
                self.save_state()
            elif v2_sell_conditions_met:
                trade_id = f"4GATE_{int(now_ts)}"
                raw_tp1 = float(t_poc) if (isinstance(t_poc, (int, float)) and 0 < t_poc < current_price) else round(current_price - (2.0 * stop_dist_sell), 2)
                raw_tp2 = round(current_price - (3.0 * stop_dist_sell), 2)
                tp1 = max(raw_tp1, raw_tp2)
                tp2 = min(raw_tp1, raw_tp2)
                if tp2 >= tp1:
                    tp2 = round(tp1 - stop_dist_sell, 2)

                trade = ForwardTestTrade(
                    trade_id=trade_id,
                    variant_id="OPT_2_4GATE",
                    direction="SELL",
                    entry_time_utc=now_utc,
                    entry_price=current_price,
                    stop_loss=stop_loss_sell,
                    tp1_price=tp1,
                    tp2_price=tp2,
                    size_btc=sized_btc_sell,
                    remaining_size=sized_btc_sell,
                    notional_usd=notional_usd_sell,
                    risk_usd=eff_risk_usd_sell,
                    state="OPEN",
                    notes="Standard 4-Gate Distribution (Resistance + Crowded Longs + Wick Exhaustion + Bear Δ Flip)",
                    level_name=lvl_name_sell,
                )
                sc2.active_trade = trade
                sc2.status = f"IN_POSITION (SELL {sized_btc_sell:.4f} BTC)"
                self._append_ledger({
                    "timestamp_utc": now_utc,
                    "event": "ENTRY_SIGNAL",
                    "variant_id": "OPT_2_4GATE",
                    "trade": asdict(trade),
                })
                self.save_state()
            elif gate1_ok and gate2_ok and gate3_ok:
                sc2.status = "ARMED (G4 Δ Flip)"
            elif sell_gate1_ok and sell_gate2_ok and sell_gate3_ok:
                sc2.status = "ARMED (G4 Bear Δ Flip)"
            elif gate1_ok:
                sc2.status = f"WATCHING ({lvl_name_buy[:14]})"
            elif sell_gate1_ok:
                sc2.status = f"WATCHING ({lvl_name_sell[:14]})"
            else:
                sc2.status = "OBSERVING"

        # -------------------------------------------------------------------------
        # VARIANT 3: OPT_3_INSTITUTIONAL (Strict Subset of Variant 2 + Hardened Gates)
        # -------------------------------------------------------------------------
        sc3 = self.scorecards["OPT_3_INSTITUTIONAL"]
        if sc3.active_trade is None:
            cooldown_active_3 = (now_ts - self._last_exit_ts["OPT_3_INSTITUTIONAL"]) < 900.0

            # Master Traffic Light & Hard Veto checks
            hard_veto = getattr(store, "hard_veto", False) is True
            regime_markdown = getattr(store, "gate_state", "") == "INITIATIVE_MARKDOWN"
            master_red = hard_veto or regime_markdown or eval_res.ntz_veto_active or eval_res.cascade_velocity_veto

            # Pillar 3: Spot CVD not in active cascade & CPI not in severe distribution
            cpi_ok = (eval_res.cpi_pct >= -0.05) and (eval_res.cpi_zscore >= -1.0)
            spot_cvd_ok = not eval_res.cascade_velocity_veto

            # Pillar 2: Live R:R >= 3.0R
            rr_to_macro = ((eval_res.tp1_fair_value_poc - current_price) / max(stop_dist_buy, 1.0)) if eval_res.tp1_fair_value_poc > current_price else 0.0
            rr_ok_buy = (eval_res.rr_to_tp2 >= 3.0) or (rr_to_macro >= 3.0) or (eval_res.rr_to_tp1 >= 2.0 and eval_res.rr_to_tp2 >= 3.0)
            rr_ok_sell = (eval_res.rr_to_tp2 >= 3.0) or (eval_res.rr_to_tp1 >= 2.0)

            # THE HIERARCHY LAW:
            # Variant 3 BUY can ONLY enter if Variant 2 BUY conditions pass (or V2 is active) + Institutional filters
            v2_buy_active_or_qual = v2_buy_conditions_met or (sc2.active_trade is not None and sc2.active_trade.direction == "BUY")
            v3_qualifies_buy = bool(
                v2_buy_active_or_qual
                and eval_res.auction_completed
                and eval_res.bar_poc_reclaimed
                and cpi_ok
                and spot_cvd_ok
                and rr_ok_buy
                and not master_red
            )

            # THE HIERARCHY LAW:
            # Variant 3 SELL can ONLY enter if Variant 2 SELL conditions pass (or V2 is active) + Institutional filters
            v2_sell_active_or_qual = v2_sell_conditions_met or (sc2.active_trade is not None and sc2.active_trade.direction == "SELL")
            v3_qualifies_sell = bool(
                v2_sell_active_or_qual
                and eval_res.auction_completed
                and rr_ok_sell
                and not master_red
            )

            if cooldown_active_3:
                sc3.status = "COOLDOWN (15m)"
            elif v3_qualifies_buy:
                trade_id = f"INST_{int(now_ts)}"
                trade = ForwardTestTrade(
                    trade_id=trade_id,
                    variant_id="OPT_3_INSTITUTIONAL",
                    direction="BUY",
                    entry_time_utc=now_utc,
                    entry_price=eval_res.entry_price or current_price,
                    stop_loss=eval_res.stop_loss or stop_loss_buy,
                    tp1_price=eval_res.tp1_fair_value_poc if eval_res.tp1_fair_value_poc > 0 else eval_res.tp1_1to2,
                    tp2_price=eval_res.tp2_short_liq_magnet if eval_res.tp2_short_liq_magnet > 0 else eval_res.tp2_1to3,
                    size_btc=eval_res.final_position_btc if eval_res.final_position_btc > 0 else sized_btc_buy,
                    remaining_size=eval_res.final_position_btc if eval_res.final_position_btc > 0 else sized_btc_buy,
                    notional_usd=eval_res.final_notional_usd if eval_res.final_notional_usd > 0 else notional_usd_buy,
                    risk_usd=eval_res.effective_risk_usd if eval_res.effective_risk_usd > 0 else eff_risk_usd_buy,
                    state="OPEN",
                    notes="Institutional Hardened Accumulation (Finished Auction + POC Reclaim + NTZ Shield)",
                    level_name=lvl_name_buy,
                )
                sc3.active_trade = trade
                sc3.status = f"IN_POSITION (BUY {trade.size_btc:.4f} BTC)"
                self._append_ledger({
                    "timestamp_utc": now_utc,
                    "event": "ENTRY_SIGNAL",
                    "variant_id": "OPT_3_INSTITUTIONAL",
                    "trade": asdict(trade),
                })
                self.save_state()
            elif v3_qualifies_sell:
                trade_id = f"INST_{int(now_ts)}"
                tp1 = eval_res.tp1_fair_value_poc if (eval_res.tp1_fair_value_poc > 0 and eval_res.tp1_fair_value_poc < current_price) else eval_res.tp1_1to2
                tp2 = eval_res.rebuy_target_price if eval_res.rebuy_target_price > 0 else eval_res.tp2_1to3
                pos_btc = eval_res.final_position_btc if eval_res.final_position_btc > 0 else sized_btc_sell
                notional = eval_res.final_notional_usd if eval_res.final_notional_usd > 0 else notional_usd_sell
                risk_u = eval_res.effective_risk_usd if eval_res.effective_risk_usd > 0 else eff_risk_usd_sell
                trade = ForwardTestTrade(
                    trade_id=trade_id,
                    variant_id="OPT_3_INSTITUTIONAL",
                    direction="SELL",
                    entry_time_utc=now_utc,
                    entry_price=eval_res.entry_price or current_price,
                    stop_loss=eval_res.stop_loss or stop_loss_sell,
                    tp1_price=tp1 if tp1 > 0 else round(current_price - (2.0 * stop_dist_sell), 2),
                    tp2_price=tp2 if tp2 > 0 else round(current_price - (3.0 * stop_dist_sell), 2),
                    size_btc=pos_btc,
                    remaining_size=pos_btc,
                    notional_usd=notional,
                    risk_usd=risk_u,
                    state="OPEN",
                    notes=f"Institutional Hardened Distribution (Resistance + Auction End + POC Reclaim + Target Coin Yield +{eval_res.target_coin_yield_pct:.1f}%)",
                    level_name=lvl_name_sell,
                )
                sc3.active_trade = trade
                sc3.status = f"IN_POSITION (SELL {pos_btc:.4f} BTC)"
                self._append_ledger({
                    "timestamp_utc": now_utc,
                    "event": "ENTRY_SIGNAL",
                    "variant_id": "OPT_3_INSTITUTIONAL",
                    "trade": asdict(trade),
                })
                self.save_state()
            elif buy_level_locked and not v3_qualifies_buy:
                sc3.status = f"LOCKED_OUT ({lvl_name_buy[:12]} 4h CD)"
            elif not v2_buy_active_or_qual and not v2_sell_active_or_qual:
                if gate1_ok or sell_gate1_ok:
                    sc3.status = f"OBSERVING (V2: {sc2.status[:16]})"
                else:
                    sc3.status = "OBSERVING"
            elif v2_buy_active_or_qual:
                if not cpi_ok:
                    sc3.status = f"VETOED (Pillar 3: CPI {eval_res.cpi_pct:+.2f}%)"
                elif not spot_cvd_ok or eval_res.cascade_velocity_veto:
                    sc3.status = "VETOED (Pillar 3: Spot CVD Cascade)"
                elif not rr_ok_buy:
                    sc3.status = "VETOED (Pillar 2: R:R < 3.0R)"
                elif master_red:
                    sc3.status = "VETOED (Master Verdict: RED)"
            elif v2_sell_active_or_qual:
                if not rr_ok_sell:
                    sc3.status = "VETOED (Pillar 2: R:R < 3.0R)"
                elif master_red:
                    sc3.status = "VETOED (Master Verdict: RED)"
            elif eval_res.signal_status == "ARMED":
                if eval_res.direction == "DISTRIBUTE_SELL":
                    sc3.status = "ARMED (G4 Bear Δ & Support Rebuy)"
                else:
                    sc3.status = "ARMED (G4 & POC Reclaim)"
            elif gate1_ok:
                sc3.status = f"WATCHING ({lvl_name_buy[:14]})"
            elif sell_gate1_ok:
                sc3.status = f"WATCHING ({lvl_name_sell[:14]})"
            else:
                sc3.status = "OBSERVING"

        return self.scorecards
