"""Tab [0] alert dispatcher: webhook (Google Apps Script / Discord-style JSON) and Telegram.

Design rules:
- Opt-in only. With no environment configuration the notifier is DISABLED and never touches the network.
- Never blocks the 2 Hz HUD loop: delivery runs on a short-lived daemon thread.
- Never raises into the caller. Failures are retried with exponential backoff (honouring HTTP 429
  `Retry-After`) and then logged. Secrets (webhook URL / bot token) are never logged.

Environment variables:
    SPOT_SWING_WEBHOOK_URL   Generic JSON webhook (Google Apps Script `/exec`, n8n, Make, ...).
    TELEGRAM_BOT_TOKEN       Telegram bot token from @BotFather.
    TELEGRAM_CHAT_ID         Destination chat id.
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

logger = logging.getLogger("spot_swing.notifier")

_EVENT_HEADLINES: Dict[str, str] = {
    "NEW_SETUP": "NEW LONG SETUP",
    "TP1_HIT": "BARRIER 2: +2.0R PARTIAL TAKE-PROFIT",
    "TP2_HIT": "BARRIER 2: PWH STRUCTURAL TARGET",
    "STOP_LOSS": "BARRIER 1: STOP LOSS",
    "BREAKEVEN_STOP": "BARRIER 1: RUNNER STOPPED AT BREAKEVEN",
    "TIME_STOP": "BARRIER 3: 10-DAY TIME STOP",
    "MACRO_FROZEN": "MACRO GATE FROZEN - 100% CASH",
}


def _fmt_usd(value: Any) -> str:
    try:
        return f"${float(value):,.2f}"
    except (TypeError, ValueError):
        return "n/a"


def format_telegram_message(payload: Dict[str, Any]) -> str:
    """Renders a compact plain-text alert (no Markdown, so no escaping hazards)."""
    event = str(payload.get("event", "EVENT"))
    lines: List[str] = [f"BTC SPOT SWING | {_EVENT_HEADLINES.get(event, event)}"]
    lines.append(f"Time: {payload.get('timestamp_utc', 'n/a')}  Price: {_fmt_usd(payload.get('price'))}")
    trade = payload.get("trade") or {}
    if event == "NEW_SETUP":
        lines += [
            f"Entry: {_fmt_usd(trade.get('entry'))}   Stop: {_fmt_usd(trade.get('initial_stop'))}",
            f"Size: {trade.get('qty_btc', 0):.6f} BTC ({_fmt_usd(trade.get('notional_usd'))}, "
            f"{trade.get('equity_alloc_pct', 0):.1f}% of equity)"
            + ("  [CAPPED AT 100% SPOT]" if trade.get("spot_capped") else ""),
            f"TP1 +2R: {_fmt_usd(trade.get('tp1'))} (sell {trade.get('tp1_fraction', 0.5) * 100:.0f}%, stop -> breakeven)",
            f"TP2 PWH: {_fmt_usd(trade.get('tp2'))}",
            f"Time stop: {trade.get('time_stop_utc', 'n/a')}",
        ]
    elif event in ("TP1_HIT", "TP2_HIT", "STOP_LOSS", "BREAKEVEN_STOP", "TIME_STOP"):
        lines += [
            f"Barrier price: {_fmt_usd(payload.get('barrier_price'))}",
            f"Trade status: {trade.get('status', 'n/a')}  Stop now: {_fmt_usd(trade.get('current_stop'))}",
        ]
        if trade.get("status") == "CLOSED":
            lines.append(f"Realized: {trade.get('realized_r', 0.0):+.2f}R")
    elif event == "MACRO_FROZEN":
        macro = payload.get("macro") or {}
        lines += [
            f"Trend pass: {macro.get('trend_pass')}  Compression pass: {macro.get('compression_pass')}",
            f"BBW percentile: {macro.get('bbw_percentile', 0.0) * 100:.1f}%",
            "Spot allocation frozen: stay 100% cash.",
        ]
    lines.append("Decision support only - not financial advice.")
    return "\n".join(lines)


class SpotSwingNotifier:
    """Fire-and-forget multi-channel alert sender."""

    def __init__(
        self,
        webhook_url: Optional[str] = None,
        telegram_token: Optional[str] = None,
        telegram_chat_id: Optional[str] = None,
        timeout_sec: float = 10.0,
        max_retries: int = 3,
        backoff_base_sec: float = 1.5,
        synchronous: bool = False,
    ) -> None:
        self.webhook_url = (webhook_url or "").strip()
        self.telegram_token = (telegram_token or "").strip()
        self.telegram_chat_id = (telegram_chat_id or "").strip()
        self.timeout_sec = timeout_sec
        self.max_retries = max(1, max_retries)
        self.backoff_base_sec = backoff_base_sec
        self.synchronous = synchronous
        self.sent_count = 0
        self.failed_count = 0

    @classmethod
    def from_env(cls) -> "SpotSwingNotifier":
        return cls(
            webhook_url=os.getenv("SPOT_SWING_WEBHOOK_URL"),
            telegram_token=os.getenv("TELEGRAM_BOT_TOKEN"),
            telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID"),
        )

    @property
    def telegram_enabled(self) -> bool:
        return bool(self.telegram_token and self.telegram_chat_id)

    @property
    def webhook_enabled(self) -> bool:
        return bool(self.webhook_url)

    @property
    def enabled(self) -> bool:
        return self.telegram_enabled or self.webhook_enabled

    def describe_channels(self) -> str:
        parts = []
        if self.webhook_enabled:
            parts.append("Webhook")
        if self.telegram_enabled:
            parts.append("Telegram")
        return " + ".join(parts) if parts else "NONE"

    # ------------------------------------------------------------------ dispatch
    def dispatch(self, payload: Dict[str, Any]) -> None:
        """Queues `payload` for delivery on every configured channel. Never raises."""
        if not self.enabled:
            return
        try:
            if self.synchronous:
                self._deliver(payload)
            else:
                threading.Thread(
                    target=self._deliver, args=(payload,), name="spot_swing_alert", daemon=True
                ).start()
        except Exception:  # pragma: no cover - defensive
            logger.exception("Spot swing alert dispatch failed to start")

    def _deliver(self, payload: Dict[str, Any]) -> None:
        try:
            if self.webhook_enabled:
                ok = self._post_json(self.webhook_url, payload, channel="webhook")
                self._count(ok)
            if self.telegram_enabled:
                url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
                body = {
                    "chat_id": self.telegram_chat_id,
                    "text": format_telegram_message(payload),
                    "disable_web_page_preview": True,
                }
                ok = self._post_json(url, body, channel="telegram")
                self._count(ok)
        except Exception:  # pragma: no cover - defensive
            logger.exception("Spot swing alert delivery crashed")

    def _count(self, ok: bool) -> None:
        if ok:
            self.sent_count += 1
        else:
            self.failed_count += 1

    def _post_json(self, url: str, body: Dict[str, Any], channel: str) -> bool:
        """POSTs JSON with retry/backoff for rate limits (429), 5xx and network failures."""
        data = json.dumps(body, default=str).encode("utf-8")
        for attempt in range(1, self.max_retries + 1):
            delay = self.backoff_base_sec * (2 ** (attempt - 1))
            try:
                request = urllib.request.Request(
                    url,
                    data=data,
                    headers={"Content-Type": "application/json", "User-Agent": "btc-spot-swing-engine/1.0"},
                    method="POST",
                )
                with urllib.request.urlopen(request, timeout=self.timeout_sec) as response:
                    if 200 <= response.status < 400:
                        return True
                    logger.warning("Spot swing %s alert: HTTP %s", channel, response.status)
            except urllib.error.HTTPError as exc:
                if exc.code == 429:
                    try:
                        delay = max(delay, float(exc.headers.get("Retry-After", delay)))
                    except (TypeError, ValueError):
                        pass
                    logger.warning("Spot swing %s alert rate-limited (429); retrying in %.1fs", channel, delay)
                elif 500 <= exc.code < 600:
                    logger.warning("Spot swing %s alert server error %s; retrying", channel, exc.code)
                else:
                    logger.error("Spot swing %s alert rejected: HTTP %s (not retried)", channel, exc.code)
                    return False
            except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as exc:
                logger.warning("Spot swing %s alert network error (%s); retrying", channel, type(exc).__name__)
            if attempt < self.max_retries:
                time.sleep(delay)
        logger.error("Spot swing %s alert failed after %d attempts", channel, self.max_retries)
        return False
