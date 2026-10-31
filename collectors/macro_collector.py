"""Macro & Intermarket Collector.

Fetches non-exchange macro, sentiment, order book depth, and intermarket data:
1. Yahoo Finance (Brent Crude, DXY, S&P 500, Nasdaq, VIX, US 10Y Yield)
2. Alternative.me (Fear & Greed Index)
3. CoinGecko (BTC Market Cap Dominance)
4. Binance Spot L2 Depth (Order Book +/-1% and +/-2% Depth Ratio)
5. FRED (10Y TIPS Real Yield & 10Y Breakeven Inflation Rate - with strict fallback)
6. BTC-Equity Rolling Pearson Correlation (20-day and 60-day windows)
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import aiohttp
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class MacroIntermarketSnapshot:
    """Typed container for external macro, intermarket, sentiment, and depth metrics."""

    timestamp_utc: str = ""
    # Macro Intermarket
    brent_crude_price: Optional[float] = None
    brent_crude_range_5_10d: Optional[str] = None
    us_10y_treasury_yield: Optional[float] = None
    us_10y_yield_change_5d: Optional[float] = None
    us_10y_real_yield_tips: Optional[float] = None
    us_10y_real_yield_source: str = "FRED (`DFII10`)"
    us_10y_tips_direction_5_10d: Optional[str] = None
    us_10y_breakeven_inflation: Optional[float] = None
    us_10y_breakeven_source: str = "FRED (`T10YIE`)"
    us_10y_breakeven_change: Optional[str] = None
    dxy_index: Optional[float] = None
    dxy_direction_5_10d: Optional[str] = None
    sp500_price: Optional[float] = None
    sp500_change_1d_pct: Optional[float] = None
    sp500_change_5d_pct: Optional[float] = None
    nasdaq_price: Optional[float] = None
    nasdaq_change_1d_pct: Optional[float] = None
    nasdaq_change_5d_pct: Optional[float] = None
    vix_index: Optional[float] = None
    vix_change_1d: Optional[float] = None
    vix_change_5d: Optional[float] = None
    btc_spx_corr_20d: Optional[float] = None
    btc_spx_corr_60d: Optional[float] = None
    # Sentiment
    fear_and_greed_score: Optional[int] = None
    fear_and_greed_classification: Optional[str] = None
    btc_dominance_pct: Optional[float] = None
    # Depth
    orderbook_depth_ratio_1pct: Optional[float] = None
    orderbook_depth_ratio_2pct: Optional[float] = None
    # ETF Flows
    etf_daily_net_flow_usd: Optional[float] = None
    etf_daily_net_flow_status: str = "unavailable"
    etf_3d_cumulative_flow_usd: Optional[float] = None
    etf_3d_cumulative_flow_status: str = "unavailable"


async def _fetch_yahoo_quotes(
    session: aiohttp.ClientSession,
) -> Dict[str, Any]:
    """Fetches macro quotes from Yahoo Finance v8 chart API."""
    symbols = {
        "brent": "BZ=F",
        "dxy": "DX-Y.NYB",
        "spx": "%5EGSPC",
        "nasdaq": "%5EIXIC",
        "vix": "%5EVIX",
        "tnx": "%5ETNX",
    }
    results = {}
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    async def _fetch_one(key: str, sym: str):
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?interval=1d&range=3mo"
        try:
            async with session.get(
                url, headers=headers, timeout=aiohttp.ClientTimeout(total=5.0)
            ) as r:
                if r.status == 200:
                    data = await r.json()
                    chart = data.get("chart", {}).get("result", [{}])[0]
                    meta = chart.get("meta", {})
                    indicators = chart.get("indicators", {}).get("quote", [{}])[0]
                    closes = indicators.get("close", [])
                    highs = indicators.get("high", [])
                    lows = indicators.get("low", [])
                    valid_closes = [c for c in closes if c is not None]
                    valid_highs = [h for h in highs if h is not None]
                    valid_lows = [l for l in lows if l is not None]
                    results[key] = {
                        "price": meta.get("regularMarketPrice"),
                        "prev_close": meta.get("chartPreviousClose"),
                        "closes": valid_closes,
                        "highs": valid_highs,
                        "lows": valid_lows,
                    }
        except Exception as e:
            logger.debug("Failed Yahoo fetch for %s: %s", key, e)

    tasks = [_fetch_one(k, s) for k, s in symbols.items()]
    await asyncio.gather(*tasks, return_exceptions=True)
    return results


async def _fetch_alternative_me_fng(session: aiohttp.ClientSession) -> Tuple[Optional[int], Optional[str]]:
    """Fetches Crypto Fear & Greed Index from Alternative.me."""
    url = "https://api.alternative.me/fng/?limit=1"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=4.0)) as r:
            if r.status == 200:
                data = await r.json()
                items = data.get("data", [])
                if items:
                    score = int(items[0].get("value", 0))
                    classification = str(items[0].get("value_classification", "Neutral"))
                    return score, classification
    except Exception as e:
        logger.debug("Failed Fear & Greed fetch: %s", e)
    return None, None


async def _fetch_coingecko_dominance(session: aiohttp.ClientSession) -> Optional[float]:
    """Fetches BTC Market Cap Dominance % from CoinGecko."""
    url = "https://api.coingecko.com/api/v3/global"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=4.0)) as r:
            if r.status == 200:
                data = await r.json()
                pct = data.get("data", {}).get("market_cap_percentage", {}).get("btc")
                if pct is not None:
                    return float(pct)
    except Exception as e:
        logger.debug("Failed CoinGecko dominance fetch: %s", e)
    return None


def _fetch_farside_etf_flows_sync() -> Optional[Tuple[str, float, float]]:
    """Fetches US Spot Bitcoin ETF flows from Farside Investors (total net flow across all issuers)."""
    import re
    import urllib.request

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
    }
    url = "https://farside.co.uk/btc/"
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=5.0) as resp:
            if resp.status != 200:
                return None
            html = resp.read().decode("utf-8", errors="ignore")

        rows = re.findall(r"<tr[^>]*>(.*?)</tr>", html, re.DOTALL)
        parsed_rows = []
        months = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
        for row_html in rows:
            cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row_html, re.DOTALL)
            cleaned = [re.sub(r"<[^>]+>", "", c).strip().replace("\xa0", " ") for c in cells]
            if cleaned and any(mo in cleaned[0] for mo in months):
                parsed_rows.append(cleaned)

        def _parse_val(v: str) -> Optional[float]:
            v = v.strip().replace("$", "").replace(",", "")
            if not v or v in ("-", "0.0", "0"):
                return 0.0
            if v.startswith("(") and v.endswith(")"):
                return -float(v[1:-1])
            try:
                return float(v)
            except ValueError:
                return None

        valid_totals = []
        for pr in parsed_rows:
            val = _parse_val(pr[-1])
            if val is not None:
                valid_totals.append((pr[0], val))

        if valid_totals:
            last_date, daily_net_m = valid_totals[-1]
            cum_3d_m = sum(v for _, v in valid_totals[-3:])
            return last_date, daily_net_m * 1_000_000.0, cum_3d_m * 1_000_000.0
    except Exception as e:
        logger.debug("Failed Farside ETF flow fetch: %s", e)
    return None


async def _fetch_binance_depth_ratios(session: aiohttp.ClientSession) -> Tuple[Optional[float], Optional[float]]:
    """Fetches Binance Spot L2 depth and computes +/-1% and +/-2% bid/ask ratios."""
    for base in ("https://data-api.binance.vision", "https://api.binance.com", "https://api1.binance.com"):
        for limit in (5000, 1000):
            res = await _fetch_depth_from(session, f"{base}/api/v3/depth?symbol=BTCUSDT&limit={limit}")
            if res[0] is not None:
                return res
    return None, None


async def _fetch_depth_from(session: aiohttp.ClientSession, url: str) -> Tuple[Optional[float], Optional[float]]:
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=4.0)) as r:
            if r.status == 200:
                d = await r.json()
                bids = [(float(p), float(q)) for p, q in d.get("bids", [])]
                asks = [(float(p), float(q)) for p, q in d.get("asks", [])]
                if bids and asks:
                    mid = (bids[0][0] + asks[0][0]) / 2.0
                    bids_1pct = sum(q for p, q in bids if p >= mid * 0.99)
                    asks_1pct = sum(q for p, q in asks if p <= mid * 1.01)
                    ratio_1pct = (bids_1pct / asks_1pct) if asks_1pct > 0 else 1.0

                    bids_2pct = sum(q for p, q in bids if p >= mid * 0.98)
                    asks_2pct = sum(q for p, q in asks if p <= mid * 1.02)
                    ratio_2pct = (bids_2pct / asks_2pct) if asks_2pct > 0 else 1.0

                    return round(ratio_1pct, 3), round(ratio_2pct, 3)
    except Exception as e:
        logger.debug("Failed Binance depth fetch: %s", e)
    return None, None


async def _fetch_fred_series(session: aiohttp.ClientSession, series_id: str) -> Optional[float]:
    """Fetches latest observation for a FRED series with strict timeout and fallback."""
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=3.0)) as r:
            if r.status == 200:
                text = await r.text()
                lines = [ln.strip() for ln in text.splitlines() if ln.strip() and not ln.startswith("DATE")]
                for line in reversed(lines):
                    parts = line.split(",")
                    if len(parts) >= 2 and parts[1] != ".":
                        val = float(parts[1])
                        return val
    except Exception as e:
        logger.debug("Failed FRED fetch for %s: %s", series_id, e)
    return None


async def _fetch_treasury_real_yield_10y(session: aiohttp.ClientSession) -> Optional[float]:
    """Fallback for DFII10: US Treasury daily real yield curve CSV ("10 YR" column, newest row first)."""
    headers = {"User-Agent": "Mozilla/5.0"}
    year = datetime.now(timezone.utc).year
    for y in (year, year - 1):
        url = (
            "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/"
            f"daily-treasury-rates.csv/{y}/all?type=daily_treasury_real_yield_curve&field_tdr_date_value={y}"
        )
        try:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=8.0)) as r:
                if r.status != 200:
                    continue
                lines = [ln.strip() for ln in (await r.text()).splitlines() if ln.strip()]
                if len(lines) < 2:
                    continue
                cols = [c.strip().strip('"') for c in lines[0].split(",")]
                if "10 YR" not in cols:
                    continue
                idx = cols.index("10 YR")
                for line in lines[1:]:
                    parts = [p.strip().strip('"') for p in line.split(",")]
                    if len(parts) > idx and parts[idx]:
                        return float(parts[idx])
        except Exception as e:
            logger.debug("Failed Treasury real-yield fetch (%s): %s", y, e)
    return None


def _compute_rolling_correlation(
    btc_closes: List[float], equity_closes: List[float], window: int
) -> Optional[float]:
    """Computes Pearson correlation coefficient between BTC and equity daily closes."""
    if len(btc_closes) < window or len(equity_closes) < window:
        return None
    b = np.array(btc_closes[-window:], dtype=float)
    e = np.array(equity_closes[-window:], dtype=float)
    if np.std(b) <= 1e-9 or np.std(e) <= 1e-9:
        return 0.0
    r = float(np.corrcoef(b, e)[0, 1])
    return round(r, 3) if not np.isnan(r) else None


async def fetch_macro_and_intermarket_snapshot(
    session: aiohttp.ClientSession, btc_daily_closes: List[float]
) -> MacroIntermarketSnapshot:
    """Orchestrates concurrent fetching of macro, sentiment, depth, and correlation data."""
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    snap = MacroIntermarketSnapshot(timestamp_utc=now_utc)

    # 1. Dispatch concurrent network tasks
    yahoo_task = _fetch_yahoo_quotes(session)
    fng_task = _fetch_alternative_me_fng(session)
    coingecko_task = _fetch_coingecko_dominance(session)
    depth_task = _fetch_binance_depth_ratios(session)
    fred_tips_task = _fetch_fred_series(session, "DFII10")
    fred_breakeven_task = _fetch_fred_series(session, "T10YIE")
    farside_task = asyncio.to_thread(_fetch_farside_etf_flows_sync)

    (
        yahoo_data,
        (fng_score, fng_class),
        btc_dom,
        (depth_1pct, depth_2pct),
        fred_tips,
        fred_breakeven,
        farside_res,
    ) = await asyncio.gather(
        yahoo_task,
        fng_task,
        coingecko_task,
        depth_task,
        fred_tips_task,
        fred_breakeven_task,
        farside_task,
        return_exceptions=True,
    )

    # Populate Sentiment & Depth
    if isinstance(fng_score, int):
        snap.fear_and_greed_score = fng_score
        snap.fear_and_greed_classification = fng_class
    if isinstance(btc_dom, float):
        snap.btc_dominance_pct = round(btc_dom, 1)
    if isinstance(depth_1pct, float):
        snap.orderbook_depth_ratio_1pct = depth_1pct
        snap.orderbook_depth_ratio_2pct = depth_2pct

    # Populate Yahoo Data
    if isinstance(yahoo_data, dict):
        # Brent Crude
        brent = yahoo_data.get("brent", {})
        if brent.get("price") is not None:
            snap.brent_crude_price = round(float(brent["price"]), 2)
            highs = brent.get("highs", [])[-10:]
            lows = brent.get("lows", [])[-10:]
            if highs and lows:
                snap.brent_crude_range_5_10d = f"${min(lows):.2f} - ${max(highs):.2f}"

        # US 10Y Treasury Yield
        tnx = yahoo_data.get("tnx", {})
        if tnx.get("price") is not None:
            snap.us_10y_treasury_yield = round(float(tnx["price"]), 3)
            closes = tnx.get("closes", [])
            if len(closes) >= 5:
                snap.us_10y_yield_change_5d = round(float(closes[-1] - closes[-5]), 3)

        # DXY
        dxy = yahoo_data.get("dxy", {})
        if dxy.get("price") is not None:
            snap.dxy_index = round(float(dxy["price"]), 3)
            closes = dxy.get("closes", [])
            if len(closes) >= 5:
                diff_5d = closes[-1] - closes[-5]
                dir_str = "RISING" if diff_5d > 0.3 else ("FALLING" if diff_5d < -0.3 else "NEUTRAL / FLAT")
                snap.dxy_direction_5_10d = f"{dir_str} ({diff_5d:+.2f} over 5d)"

        # S&P 500
        spx = yahoo_data.get("spx", {})
        if spx.get("price") is not None:
            snap.sp500_price = round(float(spx["price"]), 2)
            closes = spx.get("closes", [])
            if len(closes) >= 2:
                snap.sp500_change_1d_pct = round((closes[-1] - closes[-2]) / closes[-2] * 100.0, 2)
            if len(closes) >= 5:
                snap.sp500_change_5d_pct = round((closes[-1] - closes[-5]) / closes[-5] * 100.0, 2)

            # Rolling correlation with BTC
            if btc_daily_closes and closes:
                snap.btc_spx_corr_20d = _compute_rolling_correlation(btc_daily_closes, closes, 20)
                snap.btc_spx_corr_60d = _compute_rolling_correlation(btc_daily_closes, closes, 60)

        # Nasdaq
        nasdaq = yahoo_data.get("nasdaq", {})
        if nasdaq.get("price") is not None:
            snap.nasdaq_price = round(float(nasdaq["price"]), 2)
            closes = nasdaq.get("closes", [])
            if len(closes) >= 2:
                snap.nasdaq_change_1d_pct = round((closes[-1] - closes[-2]) / closes[-2] * 100.0, 2)
            if len(closes) >= 5:
                snap.nasdaq_change_5d_pct = round((closes[-1] - closes[-5]) / closes[-5] * 100.0, 2)

        # VIX
        vix = yahoo_data.get("vix", {})
        if vix.get("price") is not None:
            snap.vix_index = round(float(vix["price"]), 2)
            closes = vix.get("closes", [])
            if len(closes) >= 2:
                snap.vix_change_1d = round(closes[-1] - closes[-2], 2)
            if len(closes) >= 5:
                snap.vix_change_5d = round(closes[-1] - closes[-5], 2)

    # Populate FRED & Treasury Fallbacks
    if isinstance(fred_tips, float):
        snap.us_10y_real_yield_tips = round(fred_tips, 3)
    else:
        treas = await _fetch_treasury_real_yield_10y(session)
        if treas is not None:
            snap.us_10y_real_yield_tips = round(treas, 3)
            snap.us_10y_real_yield_source = "US Treasury real yield curve (10 YR)"

    if isinstance(fred_breakeven, float):
        snap.us_10y_breakeven_inflation = round(fred_breakeven, 3)
        snap.us_10y_breakeven_source = "FRED (`T10YIE`)"
    elif snap.us_10y_treasury_yield is not None and snap.us_10y_real_yield_tips is not None:
        # Nominal 10Y Yield minus 10Y TIPS Real Yield gives theoretical breakeven inflation
        snap.us_10y_breakeven_inflation = round(snap.us_10y_treasury_yield - snap.us_10y_real_yield_tips, 3)
        snap.us_10y_breakeven_source = "Treasury Yield Spread (Nominal - TIPS)"

    # Populate ETF Flows (Farside Fallback)
    if isinstance(farside_res, tuple) and len(farside_res) == 3:
        last_date, daily_net, cum_3d = farside_res
        snap.etf_daily_net_flow_usd = round(daily_net, 2)
        snap.etf_daily_net_flow_status = f"CONFIRMED (Farside {last_date})"
        snap.etf_3d_cumulative_flow_usd = round(cum_3d, 2)
        snap.etf_3d_cumulative_flow_status = f"CONFIRMED (Farside 3D to {last_date})"

    return snap
