"""Resilient Perpetual Futures aggTrade WebSocket consumer for real-time Perp CVD."""

import asyncio
import json
import logging
import time

import websockets

from config.settings import EngineConfig
from core.state_store import StateStore

logger = logging.getLogger(__name__)


async def _stream_bybit_perp_fallback(config: EngineConfig, store: StateStore) -> None:
    """Streams Bybit USDT Perpetual trades if Binance Futures WS is unreachable."""
    async with websockets.connect(
        config.bybit_perp_ws_url,
        ping_interval=config.ws_ping_interval,
        ping_timeout=config.ws_ping_timeout,
        close_timeout=5,
    ) as ws:
        sub_msg = {"op": "subscribe", "args": [f"publicTrade.{config.binance_symbol}"]}
        await ws.send(json.dumps(sub_msg))
        store.perp_ws_connected = True
        store.perp_source = "Bybit USDT-Perp (Fallback)"
        async for raw_msg in ws:
            payload = json.loads(raw_msg)
            trades = payload.get("data", [])
            if isinstance(trades, list):
                for tr in trades:
                    qty = float(tr.get("v", 0.0))
                    price = float(tr.get("p", 0.0))
                    side = tr.get("S", "Buy")
                    # is_buyer_maker == True when taker sold ("Sell")
                    is_buyer_maker = side == "Sell"
                    ts_ms = int(tr.get("T", int(time.time() * 1000)))
                    if qty > 0 and price > 0:
                        store.record_perp_trade(price, qty, is_buyer_maker, ts_ms)


async def stream_binance_perp(config: EngineConfig, store: StateStore) -> None:
    """Streams live Binance USDT-M Perpetual `btcusdt@aggTrade` events with fast stall detection & fallback."""
    attempt = 0

    while True:
        ws_url = config.binance_perp_ws_urls[attempt % len(config.binance_perp_ws_urls)]
        try:
            if attempt >= 1 and store.perp_trade_count == 0:
                await _stream_bybit_perp_fallback(config, store)
                continue

            async with websockets.connect(
                ws_url,
                ping_interval=config.ws_ping_interval,
                ping_timeout=config.ws_ping_timeout,
                open_timeout=5,
                close_timeout=3,
            ) as ws:
                store.perp_ws_connected = True
                store.perp_source = "Binance USD-M"
                while True:
                    raw_msg = await asyncio.wait_for(ws.recv(), timeout=5.0)
                    data = json.loads(raw_msg)
                    if "q" in data and "p" in data:
                        qty = float(data["q"])
                        price = float(data["p"])
                        is_buyer_maker = bool(data.get("m", False))
                        ts_ms = int(data.get("T", int(time.time() * 1000)))
                        store.record_perp_trade(price, qty, is_buyer_maker, ts_ms)
                        attempt = 0
        except asyncio.CancelledError:
            store.perp_ws_connected = False
            raise
        except Exception as exc:
            store.perp_ws_connected = False
            attempt += 1
            delay = 0.5 if attempt == 1 else min(
                config.ws_reconnect_max_delay,
                config.ws_reconnect_base_delay * (1.5 ** min(attempt, 8)),
            )
            logger.debug("Perp WS (%s) disconnected/stalled: %s. Switching/reconnecting in %.1fs...", ws_url, exc, delay)
            await asyncio.sleep(delay)
