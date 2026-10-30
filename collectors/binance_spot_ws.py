"""Resilient Binance Spot aggTrade WebSocket consumer for real-time Spot CVD."""

import asyncio
import json
import logging
import time

import websockets

from config.settings import EngineConfig
from core.state_store import StateStore

logger = logging.getLogger(__name__)


async def stream_binance_spot(config: EngineConfig, store: StateStore) -> None:
    """Streams live Binance Spot `btcusdt@aggTrade` events with exponential backoff & endpoint fallback."""
    attempt = 0
    url_idx = 0

    while True:
        ws_url = config.binance_spot_ws_urls[url_idx % len(config.binance_spot_ws_urls)]
        try:
            async with websockets.connect(
                ws_url,
                ping_interval=config.ws_ping_interval,
                ping_timeout=config.ws_ping_timeout,
                close_timeout=5,
            ) as ws:
                store.spot_ws_connected = True
                attempt = 0
                async for raw_msg in ws:
                    data = json.loads(raw_msg)
                    if "q" in data and "p" in data:
                        qty = float(data["q"])
                        price = float(data["p"])
                        is_buyer_maker = bool(data.get("m", False))
                        ts_ms = int(data.get("T", int(time.time() * 1000)))
                        store.record_spot_trade(price, qty, is_buyer_maker, ts_ms)
        except asyncio.CancelledError:
            store.spot_ws_connected = False
            raise
        except Exception as exc:
            store.spot_ws_connected = False
            attempt += 1
            url_idx += 1
            delay = min(
                config.ws_reconnect_max_delay,
                config.ws_reconnect_base_delay * (1.5 ** min(attempt, 8)),
            )
            logger.debug("Spot WS (%s) disconnected: %s. Reconnecting in %.1fs...", ws_url, exc, delay)
            await asyncio.sleep(delay)
