"""Resilient Coinbase Exchange BTC-USD WebSocket consumer for real-time Coinbase Premium."""

import asyncio
import json
import logging

import websockets

from config.settings import EngineConfig
from core.state_store import StateStore

logger = logging.getLogger(__name__)


async def stream_coinbase_spot(config: EngineConfig, store: StateStore) -> None:
    """Streams live Coinbase Exchange `BTC-USD` ticker messages with ping/pong keepalive."""
    subscribe_payload = {
        "type": "subscribe",
        "product_ids": [config.coinbase_symbol],
        "channels": ["ticker"],
    }
    attempt = 0

    while True:
        try:
            async with websockets.connect(
                config.coinbase_ws_url,
                ping_interval=config.ws_ping_interval,
                ping_timeout=config.ws_ping_timeout,
                close_timeout=5,
            ) as ws:
                await ws.send(json.dumps(subscribe_payload))
                store.coinbase_ws_connected = True
                attempt = 0
                async for raw_msg in ws:
                    data = json.loads(raw_msg)
                    if data.get("type") == "ticker" and "price" in data:
                        price = float(data["price"])
                        if price > 0:
                            store.record_coinbase_price(price)
        except asyncio.CancelledError:
            store.coinbase_ws_connected = False
            raise
        except Exception as exc:
            store.coinbase_ws_connected = False
            attempt += 1
            delay = min(
                config.ws_reconnect_max_delay,
                config.ws_reconnect_base_delay * (1.5 ** min(attempt, 8)),
            )
            logger.debug("Coinbase WS disconnected: %s. Reconnecting in %.1fs...", exc, delay)
            await asyncio.sleep(delay)
