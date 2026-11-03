"""Periodic async REST poller for Open Interest, Funding Rates, Taker Ratios, and Kline synchronization."""

import asyncio
import logging
import time

import aiohttp

from config.settings import EngineConfig
from core.state_store import StateStore
from .warmup_loader import fetch_binance_perp_klines, fetch_binance_spot_klines

logger = logging.getLogger(__name__)


async def _poll_binance_futures_metrics(
    session: aiohttp.ClientSession,
    config: EngineConfig,
    store: StateStore,
) -> bool:
    """Polls Binance USD-M Futures Open Interest, Funding Rate, and 5m Taker Ratio."""
    base_url = config.binance_perp_rest_urls[0]
    success = False

    # 1. Open Interest
    try:
        async with session.get(
            f"{base_url}/fapi/v1/openInterest",
            params={"symbol": config.binance_symbol},
            timeout=aiohttp.ClientTimeout(total=8),
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                oi_btc = float(data.get("openInterest", 0.0))
                if oi_btc > 0:
                    store.record_oi_sample(oi_btc)
                    success = True
    except Exception as exc:
        logger.debug("OI poll error: %s", exc)

    # 2. Funding Rate & Mark Price
    try:
        async with session.get(
            f"{base_url}/fapi/v1/premiumIndex",
            params={"symbol": config.binance_symbol},
            timeout=aiohttp.ClientTimeout(total=8),
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                store.funding_rate_pct = float(data.get("lastFundingRate", 0.0)) * 100.0
                mark_p = float(data.get("markPrice", 0.0))
                if mark_p > 0 and store.binance_perp_price == 0.0:
                    store.binance_perp_price = mark_p
                success = True
    except Exception as exc:
        logger.debug("PremiumIndex poll error: %s", exc)

    # 3. 5m Taker Long/Short Ratio
    try:
        async with session.get(
            f"{base_url}/futures/data/takerlongshortRatio",
            params={"symbol": config.binance_symbol, "period": "5m", "limit": 1},
            timeout=aiohttp.ClientTimeout(total=8),
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                if isinstance(data, list) and len(data) > 0:
                    latest = data[0]
                    store.taker_long_short_ratio_5m = float(latest.get("buySellRatio", 1.0))
                    buy_v = float(latest.get("buyVol", 0.0))
                    sell_v = float(latest.get("sellVol", 0.0))
                    store.perp_5m_delta_btc = buy_v - sell_v
    except Exception as exc:
        logger.debug("Taker ratio poll error: %s", exc)

    return success


async def _poll_bybit_futures_fallback(
    session: aiohttp.ClientSession,
    config: EngineConfig,
    store: StateStore,
) -> None:
    """Fallback Open Interest and Funding Rate poller via Bybit V5 Linear API."""
    try:
        async with session.get(
            f"{config.bybit_rest_url}/v5/market/tickers",
            params={"category": "linear", "symbol": config.binance_symbol},
            timeout=aiohttp.ClientTimeout(total=8),
        ) as resp:
            if resp.status == 200:
                payload = await resp.json()
                items = payload.get("result", {}).get("list", [])
                if items:
                    ticker = items[0]
                    oi_btc = float(ticker.get("openInterest", 0.0))
                    funding = float(ticker.get("fundingRate", 0.0)) * 100.0
                    last_p = float(ticker.get("lastPrice", 0.0))
                    if last_p > 0 and store.binance_perp_price == 0.0:
                        store.binance_perp_price = last_p
                    if oi_btc > 0:
                        store.record_oi_sample(oi_btc)
                    store.funding_rate_pct = funding
    except Exception as exc:
        logger.debug("Bybit fallback poll error: %s", exc)


async def poll_rest_metrics(config: EngineConfig, store: StateStore) -> None:
    """Periodically polls derivatives metrics (15s) and synchronizes kline buffers (60s)."""
    last_kline_sync = time.time()
    last_macro_sync = time.time()

    async with aiohttp.ClientSession() as session:
        while True:
            try:
                ok = await _poll_binance_futures_metrics(session, config, store)
                if not ok:
                    await _poll_bybit_futures_fallback(session, config, store)

                # If Coinbase WS hasn't ticked recently, refresh via REST
                if time.time() - store.last_cb_tick_ts > 20.0:
                    try:
                        async with session.get(
                            f"{config.coinbase_rest_url}/products/{config.coinbase_symbol}/ticker",
                            timeout=aiohttp.ClientTimeout(total=6),
                        ) as cb_resp:
                            if cb_resp.status == 200:
                                cb_data = await cb_resp.json()
                                if "price" in cb_data:
                                    store.record_coinbase_price(float(cb_data["price"]))
                    except Exception:
                        pass

                now = time.time()
                # Periodic Macro & Intermarket Telemetry Sync (every 5 min)
                if now - last_macro_sync >= 300.0:
                    last_macro_sync = now
                    try:
                        from .macro_collector import fetch_macro_and_intermarket_snapshot
                        daily_closes = [b.close for b in store.spot_klines_1d]
                        store.macro_intermarket = await fetch_macro_and_intermarket_snapshot(session, daily_closes)
                    except Exception as mexc:
                        logger.debug("Periodic macro sync error: %s", mexc)

                # Periodic Kline Sync (every 60s)
                if now - last_kline_sync >= config.kline_sync_interval_sec:
                    last_kline_sync = now
                    (
                        spot_1w,
                        spot_1d,
                        perp_1d,
                        spot_1h,
                        perp_1h,
                        spot_15m,
                        perp_15m,
                    ) = await asyncio.gather(
                        fetch_binance_spot_klines(
                            session, config, interval="1w", limit=config.weekly_kline_limit
                        ),
                        fetch_binance_spot_klines(
                            session, config, interval="1d", limit=config.daily_kline_limit
                        ),
                        fetch_binance_perp_klines(
                            session, config, interval="1d", limit=config.daily_kline_limit
                        ),
                        fetch_binance_spot_klines(
                            session, config, interval="1h", limit=config.macro_profile_days * 24
                        ),
                        fetch_binance_perp_klines(
                            session, config, interval="1h", limit=config.macro_profile_days * 24
                        ),
                        fetch_binance_spot_klines(session, config, interval="15m", limit=240),
                        fetch_binance_perp_klines(session, config, interval="15m", limit=240),
                    )
                    if spot_1w:
                        await store.set_klines("spot", "1w", spot_1w)
                    if spot_1d:
                        await store.set_klines("spot", "1d", spot_1d)
                    if perp_1d:
                        await store.set_klines("perp", "1d", perp_1d)
                    if spot_1h:
                        await store.set_klines("spot", "1h", spot_1h)
                    if perp_1h:
                        await store.set_klines("perp", "1h", perp_1h)
                    if spot_15m:
                        await store.set_klines("spot", "15m", spot_15m)
                    if perp_15m:
                        await store.set_klines("perp", "15m", perp_15m)

                await asyncio.sleep(config.rest_poll_interval_sec)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.debug("REST poller loop error: %s", exc)
                await asyncio.sleep(5.0)
