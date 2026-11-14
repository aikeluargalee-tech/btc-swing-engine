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

    # Geo-resilient fallback #1: OKX BTC-USDT-SWAP
    okx_bars = await fetch_okx_perp_klines(session, config, interval=interval, limit=limit)
    if okx_bars:
        return okx_bars

    # Geo-resilient fallback #2: Bybit V5 Linear klines (approximating taker buy via candle body direction/ratio)
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
                            estimated=True,
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
        # 1. Current Funding Rate & Mark Price (first, so record_oi_sample computes USD OI accurately)
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

        # 2. Historical 15m Open Interest for immediate 15m/1H/4H delta calculation
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

        # 3. Live Current Open Interest
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

        # 5. Top Trader Long/Short Position Ratio
        try:
            async with session.get(
                f"{base_url}/futures/data/topLongShortPositionRatio",
                params={"symbol": config.binance_symbol, "period": "1h", "limit": 1},
                timeout=aiohttp.ClientTimeout(total=8),
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if isinstance(data, list) and len(data) > 0:
                        latest = data[0]
                        store.top_trader_ls_ratio = float(latest.get("longShortRatio", 1.0))
                        store.top_trader_long_pct = float(latest.get("longAccount", 0.5)) * 100.0
                        store.top_trader_short_pct = float(latest.get("shortAccount", 0.5)) * 100.0
        except Exception:
            pass

        # 6. Global Account Long/Short Ratio
        try:
            async with session.get(
                f"{base_url}/futures/data/globalLongShortAccountRatio",
                params={"symbol": config.binance_symbol, "period": "1h", "limit": 1},
                timeout=aiohttp.ClientTimeout(total=8),
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if isinstance(data, list) and len(data) > 0:
                        latest = data[0]
                        store.global_account_ls_ratio = float(latest.get("longShortRatio", 1.0))
        except Exception:
            pass
    except Exception as exc:
        logger.debug("Primary Binance futures OI/Funding warmup failed: %s", exc)

    if store.binance_perp_price == 0.0 or store.funding_rate_pct == 0.0:
        await fetch_okx_oi_and_funding(session, config, store)


# ---------------- OKX BTC-USDT-SWAP fallback (used when Binance USD-M / Bybit are geo-blocked) ----------------

OKX_SOURCE_LABEL = "OKX BTC-USDT-SWAP"
_OKX_BAR = {"15m": "15m", "1h": "1H", "4h": "4H", "1d": "1Dutc", "1w": "1Wutc"}
_OKX_TAKER_PERIOD = {"15m": "15m", "1h": "1H", "1d": "1D"}


async def _okx_get(session: aiohttp.ClientSession, config: EngineConfig, path: str, params: dict) -> Optional[list]:
    try:
        async with session.get(
            f"{config.okx_rest_url}{path}", params=params, timeout=aiohttp.ClientTimeout(total=10)
        ) as resp:
            if resp.status == 200:
                payload = await resp.json()
                if str(payload.get("code")) == "0":
                    return payload.get("data", [])
    except Exception as exc:
        logger.debug("OKX GET %s failed: %s", path, exc)
    return None


async def fetch_okx_perp_klines(
    session: aiohttp.ClientSession,
    config: EngineConfig,
    interval: str = "1h",
    limit: int = 750,
) -> List[KlineBar]:
    """OKX BTC-USDT-SWAP candles (volCcy = BTC) with taker-buy volume from rubik taker-volume-contract.

    Rubik returns at most 100 recent bars; older bars fall back to the candle-body taker approximation
    (same method the engine already uses for its Bybit fallback).
    """
    bar = _OKX_BAR.get(interval)
    if not bar:
        return []
    rows: List[list] = []
    after: Optional[str] = None
    while len(rows) < limit:
        params = {"instId": config.okx_perp_inst_id, "bar": bar, "limit": "100"}
        if after:
            params["after"] = after
        data = await _okx_get(session, config, "/api/v5/market/history-candles", params)
        if not data:
            break
        rows.extend(data)
        after = data[-1][0]
        if len(data) < 100:
            break
    if not rows:
        return []
    rows = rows[:limit]

    taker_buy: dict = {}
    period = _OKX_TAKER_PERIOD.get(interval)
    if period:
        target_tv = min(limit, 800)
        end_cursor: Optional[str] = None
        for _ in range(8):
            if len(taker_buy) >= target_tv:
                break
            tv_params = {"instId": config.okx_perp_inst_id, "period": period, "unit": "0", "limit": "100"}
            if end_cursor:
                tv_params["end"] = end_cursor
            tv = await _okx_get(
                session,
                config,
                "/api/v5/rubik/stat/taker-volume-contract",
                tv_params,
            )
            if not tv:
                break
            for r in tv:
                # [ts, sellVol, buyVol] in BTC -> measured buy share (rubik totals != candle volCcy,
                # so apply the measured buy/sell ratio to candle volume instead of raw buyVol)
                sell_v, buy_v = float(r[1]), float(r[2])
                if sell_v + buy_v > 0:
                    taker_buy[int(r[0])] = buy_v / (sell_v + buy_v)
            next_end = str(tv[-1][0])
            if len(tv) < 100 or (end_cursor is not None and int(next_end) >= int(end_cursor)):
                break
            end_cursor = next_end

    bars: List[KlineBar] = []
    for row in reversed(rows):  # oldest first
        ts = int(row[0])
        o, h, l, c = float(row[1]), float(row[2]), float(row[3]), float(row[4])
        v = float(row[6])  # volCcy = BTC
        estimated = ts not in taker_buy
        if not estimated:
            tb = v * taker_buy[ts]
        else:
            rng = max(h - l, 1e-6)
            buy_ratio = min(0.95, max(0.05, 0.5 + 0.4 * ((c - o) / rng)))
            tb = v * buy_ratio
        bars.append(
            KlineBar(timestamp_ms=ts, open=o, high=h, low=l, close=c, volume=v, taker_buy_volume=tb, estimated=estimated)
        )
    return bars


async def fetch_okx_oi_and_funding(
    session: aiohttp.ClientSession,
    config: EngineConfig,
    store: StateStore,
) -> bool:
    """OKX fallback for OI (BTC via oiCcy), OI history, funding, mark price and 5m taker ratio."""
    inst = config.okx_perp_inst_id
    ok = False
    tk = await _okx_get(session, config, "/api/v5/market/ticker", {"instId": inst})
    if tk and float(tk[0].get("last", 0.0)) > 0:
        store.binance_perp_price = float(tk[0]["last"])
    else:
        mp = await _okx_get(session, config, "/api/v5/public/mark-price", {"instType": "SWAP", "instId": inst})
        if mp and float(mp[0].get("markPx", 0.0)) > 0:
            store.binance_perp_price = float(mp[0]["markPx"])
    hist = await _okx_get(
        session, config, "/api/v5/rubik/stat/contracts/open-interest-history",
        {"instId": inst, "period": "15m", "limit": "300"},
    )
    for r in reversed(hist or []):  # [ts, oi_contracts, oiCcy(BTC), oiUsd]
        oi_btc = float(r[2])
        if oi_btc > 0:
            store.record_oi_sample(oi_btc, ts_sec=int(r[0]) / 1000.0)
    cur = await _okx_get(session, config, "/api/v5/public/open-interest", {"instType": "SWAP", "instId": inst})
    if cur:
        oi_btc = float(cur[0].get("oiCcy", 0.0))
        if oi_btc > 0:
            store.record_oi_sample(oi_btc)
            oi_usd = float(cur[0].get("oiUsd", 0.0) or 0.0)
            if oi_usd > 0:
                store.open_interest_usd = oi_usd
            ok = True
    fr = await _okx_get(session, config, "/api/v5/public/funding-rate", {"instId": inst})
    if fr:
        store.funding_rate_pct = float(fr[0].get("fundingRate", 0.0)) * 100.0
        ok = True
    tv = await _okx_get(
        session, config, "/api/v5/rubik/stat/taker-volume-contract",
        {"instId": inst, "period": "5m", "unit": "0", "limit": "1"},
    )
    if tv:
        sell_v, buy_v = float(tv[0][1]), float(tv[0][2])
        store.taker_long_short_ratio_5m = (buy_v / sell_v) if sell_v > 0 else 1.0
        store.perp_5m_delta_btc = buy_v - sell_v
    if ok:
        store.perp_source = OKX_SOURCE_LABEL
    return ok


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
            session, config, interval="4h", limit=getattr(config, "four_hour_kline_limit", 500)
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

        # Ensure open_interest_usd is populated once spot/perp reference prices are known
        if store.open_interest_btc > 0 and store.open_interest_usd <= 0:
            ref_px = store.binance_perp_price or store.binance_spot_price
            if ref_px > 0:
                store.open_interest_usd = store.open_interest_btc * ref_px

        # Warm up Coinbase price & historical CPI basis Z-score
        await fetch_initial_coinbase_basis(session, config, store)

        # Seed UTC day CVD from today's 15m candles
        _seed_utc_day_cvd_from_klines(store)

        # Warm up Macro & Intermarket Telemetry (Brent Crude, DXY, SPX, F&G, Tips, Depth)
        try:
            from .macro_collector import fetch_macro_and_intermarket_snapshot
            daily_closes = [b.close for b in store.spot_klines_1d]
            store.macro_intermarket = await fetch_macro_and_intermarket_snapshot(session, daily_closes)
        except Exception as exc:
            logger.debug("Initial macro warmup failed: %s", exc)

        store.warmup_complete = True
