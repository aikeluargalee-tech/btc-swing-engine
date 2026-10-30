"""Zero-cold-start historical backfill for Spot/Perp klines, Open Interest, and Coinbase Premium."""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, List, Optional

import aiohttp

from config.settings import EngineConfig
from core.models import KlineBar
from core.state_store import StateStore

logger = logging.getLogger(__name__)


def _parse_binance_kline(raw: List[Any]) -> KlineBar:
    """Converts a Binance REST kline array into a typed KlineBar.

    Binance kline format:
    [0] Open time (ms), [1] Open, [2] High, [3] Low, [4] Close, [5] Volume,
    [6] Close time, [7] Quote asset vol, [8] Number of trades,
    [9] Taker buy base asset volume, ...
    """
    return KlineBar(
        timestamp_ms=int(raw[0]),
        open=float(raw[1]),
        high=float(raw[2]),
        low=float(raw[3]),
        close=float(raw[4]),
        volume=float(raw[5]),
        taker_buy_volume=float(raw[9]),
    )


async def fetch_binance_spot_klines(
    session: aiohttp.ClientSession,
    config: EngineConfig,
    interval: str = "1h",
    limit: int = 750,
) -> List[KlineBar]:
    """Fetches historical Binance Spot klines across fallback endpoints."""
    params = {"symbol": config.binance_symbol, "interval": interval, "limit": limit}
    for base_url in config.binance_spot_rest_urls:
        url = f"{base_url}/api/v3/klines"
        try:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=12)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if isinstance(data, list) and len(data) > 0:
                        return [_parse_binance_kline(row) for row in data]
        except Exception as exc:
            logger.debug("Spot kline fetch failed on %s: %s", base_url, exc)
    return []


async def fetch_binance_perp_klines(
    session: aiohttp.ClientSession,
    config: EngineConfig,
    interval: str = "1h",
    limit: int = 750,
) -> List[KlineBar]:
    """Fetches historical Binance USDT-M Perpetual klines (with Bybit fallback if geo-restricted)."""
    params = {"symbol": config.binance_symbol, "interval": interval, "limit": limit}
    for base_url in config.binance_perp_rest_urls:
        url = f"{base_url}/fapi/v1/klines"
        try:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=12)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if isinstance(data, list) and len(data) > 0:
                        return [_parse_binance_kline(row) for row in data]
        except Exception as exc:
            logger.debug("Perp kline fetch failed on %s: %s", base_url, exc)

    # Geo-resilient fallback: Bybit V5 Linear klines (approximating taker buy via candle body direction/ratio)
    interval_map = {"1h": "60", "15m": "15", "1d": "D", "1w": "W"}
    bybit_interval = interval_map.get(interval, "60")
    url = f"{config.bybit_rest_url}/v5/market/kline"
    try:
        async with session.get(
            url,
            params={"category": "linear", "symbol": config.binance_symbol, "interval": bybit_interval, "limit": min(limit, 200)},
            timeout=aiohttp.ClientTimeout(total=12),
        ) as resp:
            if resp.status == 200:
                payload = await resp.json()
                rows = payload.get("result", {}).get("list", [])
                bars: List[KlineBar] = []
                for row in reversed(rows):
                    o, h, l, c, v = float(row[1]), float(row[2]), float(row[3]), float(row[4]), float(row[5])
                    rng = max(h - l, 1e-6)
                    buy_ratio = 0.5 + 0.4 * ((c - o) / rng)
                    buy_ratio = min(0.95, max(0.05, buy_ratio))
                    bars.append(
                        KlineBar(
                            timestamp_ms=int(row[0]),
                            open=o,
                            high=h,
                            low=l,
                            close=c,
                            volume=v,
                            taker_buy_volume=v * buy_ratio,
                        )
                    )
                return bars
    except Exception as exc:
        logger.debug("Fallback Bybit perp kline fetch failed: %s", exc)

    return []


async def fetch_initial_oi_and_funding(
    session: aiohttp.ClientSession,
    config: EngineConfig,
    store: StateStore,
) -> None:
    """Backfills 4H Open Interest history, current Open Interest, and Funding Rate."""
    base_url = config.binance_perp_rest_urls[0]
    try:
        # 1. Historical 15m Open Interest for immediate 15m/1H/4H delta calculation
        hist_url = f"{base_url}/futures/data/openInterestHist"
        async with session.get(
            hist_url,
            params={"symbol": config.binance_symbol, "period": "15m", "limit": 24},
            timeout=aiohttp.ClientTimeout(total=10),
        ) as resp:
            if resp.status == 200:
                hist_data = await resp.json()
                if isinstance(hist_data, list):
                    for item in hist_data:
                        ts_sec = float(item.get("timestamp", 0)) / 1000.0
                        oi_btc = float(item.get("sumOpenInterest", 0.0))
                        if oi_btc > 0:
                            store.record_oi_sample(oi_btc, ts_sec=ts_sec)

        # 2. Live Current Open Interest
        oi_url = f"{base_url}/fapi/v1/openInterest"
        async with session.get(
            oi_url,
            params={"symbol": config.binance_symbol},
            timeout=aiohttp.ClientTimeout(total=8),
        ) as resp:
            if resp.status == 200:
                oi_data = await resp.json()
                oi_btc = float(oi_data.get("openInterest", 0.0))
                if oi_btc > 0:
                    store.record_oi_sample(oi_btc)
                    store.perp_source = "Binance USD-M"

        # 3. Current Funding Rate & Mark Price
        prem_url = f"{base_url}/fapi/v1/premiumIndex"
        async with session.get(
            prem_url,
            params={"symbol": config.binance_symbol},
            timeout=aiohttp.ClientTimeout(total=8),
        ) as resp:
            if resp.status == 200:
                prem_data = await resp.json()
                store.funding_rate_pct = float(prem_data.get("lastFundingRate", 0.0)) * 100.0
                mark_p = float(prem_data.get("markPrice", 0.0))
                if mark_p > 0 and store.binance_perp_price == 0.0:
                    store.binance_perp_price = mark_p

        # 4. 5m Taker Long/Short Volume Ratio
        taker_url = f"{base_url}/futures/data/takerlongshortRatio"
        async with session.get(
            taker_url,
            params={"symbol": config.binance_symbol, "period": "5m", "limit": 1},
            timeout=aiohttp.ClientTimeout(total=8),
        ) as resp:
            if resp.status == 200:
                t_data = await resp.json()
                if isinstance(t_data, list) and len(t_data) > 0:
                    latest = t_data[0]
                    store.taker_long_short_ratio_5m = float(latest.get("buySellRatio", 1.0))
                    buy_v = float(latest.get("buyVol", 0.0))
                    sell_v = float(latest.get("sellVol", 0.0))
                    store.perp_5m_delta_btc = buy_v - sell_v
    except Exception as exc:
        logger.debug("Primary Binance futures OI/Funding warmup failed: %s", exc)


async def fetch_initial_coinbase_basis(
    session: aiohttp.ClientSession,
    config: EngineConfig,
    store: StateStore,
) -> None:
    """Fetches Coinbase BTC-USD ticker and 15m candles to warm up Coinbase Premium Z-score."""
    try:
        # 1. Current Coinbase Spot Price
        ticker_url = f"{config.coinbase_rest_url}/products/{config.coinbase_symbol}/ticker"
        async with session.get(ticker_url, timeout=aiohttp.ClientTimeout(total=8)) as resp:
            if resp.status == 200:
                data = await resp.json()
                if "price" in data:
                    store.record_coinbase_price(float(data["price"]))

        # 2. Backfill 15m Coinbase candles against Binance 15m Spot klines to seed cpi_history
        candles_url = f"{config.coinbase_rest_url}/products/{config.coinbase_symbol}/candles"
        async with session.get(
            candles_url,
            params={"granularity": 900},
            timeout=aiohttp.ClientTimeout(total=8),
        ) as resp:
            if resp.status == 200 and store.spot_klines_15m:
                cb_candles = await resp.json()
                # Coinbase format: [time_sec, low, high, open, close, volume]
                if isinstance(cb_candles, list):
                    bn_map = {b.timestamp_ms // 1000: b.close for b in store.spot_klines_15m}
                    for row in reversed(cb_candles[:60]):
                        ts_sec = int(row[0])
                        cb_close = float(row[4])
                        bn_close = bn_map.get(ts_sec)
                        if bn_close and bn_close > 0:
                            cpi_pct = ((cb_close - bn_close) / bn_close) * 100.0
                            store.cpi_history.append((float(ts_sec), cpi_pct))
    except Exception as exc:
        logger.debug("Coinbase warmup error: %s", exc)


def _seed_utc_day_cvd_from_klines(store: StateStore) -> None:
    """Populates today's UTC 00:00 cumulative Spot and Perp CVD from backfilled 15m klines."""
    now_utc = datetime.now(timezone.utc)
    midnight_utc = datetime(now_utc.year, now_utc.month, now_utc.day, tzinfo=timezone.utc)
    midnight_ms = int(midnight_utc.timestamp() * 1000)

    spot_day_delta = sum(
        b.delta for b in store.spot_klines_15m if b.timestamp_ms >= midnight_ms
    )
    perp_day_delta = sum(
        b.delta for b in store.perp_klines_15m if b.timestamp_ms >= midnight_ms
    )
    store.utc_day_spot_cvd = spot_day_delta
    store.utc_day_perp_cvd = perp_day_delta


async def run_initial_warmup(config: EngineConfig, store: StateStore) -> None:
    """Executes concurrent historical backfill so 1W/1D/30D/7D profiles, Cycle Radar, and CVD are warm at startup."""
    async with aiohttp.ClientSession() as session:
        spot_1w_task = fetch_binance_spot_klines(
            session, config, interval="1w", limit=config.weekly_kline_limit
        )
        spot_1d_task = fetch_binance_spot_klines(
            session, config, interval="1d", limit=config.daily_kline_limit
        )
        spot_4h_task = fetch_binance_spot_klines(
            session, config, interval="4h", limit=300
        )
        perp_1d_task = fetch_binance_perp_klines(
            session, config, interval="1d", limit=config.daily_kline_limit
        )
        spot_1h_task = fetch_binance_spot_klines(
            session, config, interval="1h", limit=config.macro_profile_days * 24
        )
        perp_1h_task = fetch_binance_perp_klines(
            session, config, interval="1h", limit=config.macro_profile_days * 24
        )
        spot_15m_task = fetch_binance_spot_klines(
            session, config, interval="15m", limit=240
        )
        perp_15m_task = fetch_binance_perp_klines(
            session, config, interval="15m", limit=240
        )
        oi_task = fetch_initial_oi_and_funding(session, config, store)

        (
            spot_1w,
            spot_1d,
            spot_4h,
            perp_1d,
            spot_1h,
            perp_1h,
            spot_15m,
            perp_15m,
            _,
        ) = await asyncio.gather(
            spot_1w_task,
            spot_1d_task,
            spot_4h_task,
            perp_1d_task,
            spot_1h_task,
            perp_1h_task,
            spot_15m_task,
            perp_15m_task,
            oi_task,
        )

        await store.set_klines("spot", "1w", spot_1w)
        await store.set_klines("spot", "1d", spot_1d)
        await store.set_klines("spot", "4h", spot_4h)
        await store.set_klines("perp", "1d", perp_1d)
        await store.set_klines("spot", "1h", spot_1h)
        await store.set_klines("perp", "1h", perp_1h)
        await store.set_klines("spot", "15m", spot_15m)
        await store.set_klines("perp", "15m", perp_15m)

        # Warm up Coinbase price & historical CPI basis Z-score
        await fetch_initial_coinbase_basis(session, config, store)

        # Seed UTC day CVD from today's 15m candles
        _seed_utc_day_cvd_from_klines(store)
        store.warmup_complete = True
