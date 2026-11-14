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
    # Depth & Spread
    orderbook_depth_ratio_1pct: Optional[float] = None
    orderbook_depth_ratio_2pct: Optional[float] = None
    orderbook_spread_bps: Optional[float] = None
    coinbase_spot_vol_24h_btc: Optional[float] = None
    # On-Chain (CoinMetrics Community)
    onchain_mvrv_cur: Optional[float] = None
    onchain_mvrv_date: Optional[str] = None
    onchain_exch_inflow_btc: Optional[float] = None
    onchain_exch_outflow_btc: Optional[float] = None
    onchain_exch_netflow_btc: Optional[float] = None
    onchain_exch_netflow_usd: Optional[float] = None
    onchain_exch_supply_btc: Optional[float] = None
    # Stablecoin Liquidity (DefiLlama)
    stablecoin_usdt_b: Optional[float] = None
    stablecoin_usdc_b: Optional[float] = None
    stablecoin_total_b: Optional[float] = None
    stablecoin_7d_delta_b: Optional[float] = None
    stablecoin_30d_delta_b: Optional[float] = None
    # Options Positioning (Deribit)
    options_put_call_oi_ratio: Optional[float] = None
    options_total_oi_btc: Optional[float] = None
    options_iv_front: Optional[float] = None
    options_iv_back: Optional[float] = None
    options_skew_25d_proxy: Optional[float] = None
    # Cross-Exchange Perps (Binance + Bybit + OKX)
    agg_perp_oi_btc: Optional[float] = None
    agg_perp_oi_usd: Optional[float] = None
    agg_perp_funding_8h_pct: Optional[float] = None
    agg_perp_venues_str: Optional[str] = None
    # ETF Flows (Farside + Yahoo IBIT/FBTC proxy)
    etf_daily_net_flow_usd: Optional[float] = None
    etf_daily_net_flow_status: str = "unavailable"
    etf_3d_cumulative_flow_usd: Optional[float] = None
    etf_3d_cumulative_flow_status: str = "unavailable"
    etf_proxy_vol_1d_usd: Optional[float] = None
    etf_proxy_flow_5d_usd: Optional[float] = None
    # US Liquidity & Credit Spreads
    us_sofr_rate_pct: Optional[float] = None
    us_sofr_vol_b: Optional[float] = None
    us_rrp_balance_b: Optional[float] = None
    credit_hyg_lqd_ratio: Optional[float] = None
    credit_hyg_lqd_5d_chg_pct: Optional[float] = None


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
        "hyg": "HYG",
        "lqd": "LQD",
        "ibit": "IBIT",
        "fbtc": "FBTC",
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
                    vols = indicators.get("volume", [])
                    valid_closes = [c for c in closes if c is not None]
                    valid_highs = [h for h in highs if h is not None]
                    valid_lows = [l for l in lows if l is not None]
                    cv_pairs = [
                        (float(c), float(v))
                        for c, v in zip(closes, vols)
                        if c is not None and v is not None
                    ]
                    results[key] = {
                        "price": meta.get("regularMarketPrice"),
                        "prev_close": meta.get("chartPreviousClose"),
                        "closes": valid_closes,
                        "highs": valid_highs,
                        "lows": valid_lows,
                        "cv_pairs": cv_pairs,
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


async def _fetch_binance_depth_ratios(
    session: aiohttp.ClientSession,
) -> Tuple[Optional[float], Optional[float], Optional[float]]:
    """Fetches Binance Spot L2 depth and computes +/-1%, +/-2% bid/ask ratios and spread (bps)."""
    for base in ("https://data-api.binance.vision", "https://api.binance.com", "https://api1.binance.com"):
        for limit in (5000, 1000):
            res = await _fetch_depth_from(session, f"{base}/api/v3/depth?symbol=BTCUSDT&limit={limit}")
            if res[0] is not None:
                return res
    return None, None, None


async def _fetch_depth_from(
    session: aiohttp.ClientSession, url: str
) -> Tuple[Optional[float], Optional[float], Optional[float]]:
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=4.0)) as r:
            if r.status == 200:
                d = await r.json()
                bids = [(float(p), float(q)) for p, q in d.get("bids", [])]
                asks = [(float(p), float(q)) for p, q in d.get("asks", [])]
                if bids and asks:
                    mid = (bids[0][0] + asks[0][0]) / 2.0
                    spread_bps = round(((asks[0][0] - bids[0][0]) / mid) * 10000.0, 2) if mid > 0 else None
                    bids_1pct = sum(q for p, q in bids if p >= mid * 0.99)
                    asks_1pct = sum(q for p, q in asks if p <= mid * 1.01)
                    ratio_1pct = (bids_1pct / asks_1pct) if asks_1pct > 0 else 1.0

                    bids_2pct = sum(q for p, q in bids if p >= mid * 0.98)
                    asks_2pct = sum(q for p, q in asks if p <= mid * 1.02)
                    ratio_2pct = (bids_2pct / asks_2pct) if asks_2pct > 0 else 1.0

                    return round(ratio_1pct, 3), round(ratio_2pct, 3), spread_bps
    except Exception as e:
        logger.debug("Failed Binance depth fetch: %s", e)
    return None, None, None


async def _fetch_coinmetrics_onchain(session: aiohttp.ClientSession) -> Dict[str, Any]:
    """Fetches free daily BTC MVRV and exchange inflows/outflows/reserves from CoinMetrics Community API."""
    url = (
        "https://community-api.coinmetrics.io/v4/timeseries/asset-metrics"
        "?assets=btc&metrics=CapMVRVCur,FlowInExNtv,FlowOutExNtv,FlowInExUSD,FlowOutExUSD,SplyExNtv&page_size=5"
    )
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=5.0)) as r:
            if r.status == 200:
                rows = (await r.json()).get("data", [])
                for row in reversed(rows):
                    mvrv = row.get("CapMVRVCur")
                    in_btc = row.get("FlowInExNtv")
                    out_btc = row.get("FlowOutExNtv")
                    if mvrv is not None or in_btc is not None:
                        in_b = float(in_btc) if in_btc is not None else None
                        out_b = float(out_btc) if out_btc is not None else None
                        in_u = float(row["FlowInExUSD"]) if row.get("FlowInExUSD") is not None else None
                        out_u = float(row["FlowOutExUSD"]) if row.get("FlowOutExUSD") is not None else None
                        sply = float(row["SplyExNtv"]) if row.get("SplyExNtv") is not None else None
                        return {
                            "mvrv": round(float(mvrv), 3) if mvrv is not None else None,
                            "date": str(row.get("time", ""))[:10] or None,
                            "inflow_btc": round(in_b, 1) if in_b is not None else None,
                            "outflow_btc": round(out_b, 1) if out_b is not None else None,
                            "netflow_btc": round(in_b - out_b, 1) if (in_b is not None and out_b is not None) else None,
                            "netflow_usd": round(in_u - out_u, 0) if (in_u is not None and out_u is not None) else None,
                            "supply_btc": round(sply, 0) if sply is not None else None,
                        }
    except Exception as e:
        logger.debug("Failed CoinMetrics on-chain fetch: %s", e)
    return {}


async def _fetch_defillama_stablecoins(session: aiohttp.ClientSession) -> Dict[str, Optional[float]]:
    """Fetches USDT & USDC circulating supply and 7D/30D net issuance from DefiLlama ($B)."""
    url = "https://stablecoins.llama.fi/stablecoins?includePrices=false"
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=5.0)) as r:
            if r.status == 200:
                assets = (await r.json()).get("peggedAssets", [])
                targets = {a.get("symbol"): a for a in assets if a.get("symbol") in ("USDT", "USDC")}
                usdt = targets.get("USDT")
                usdc = targets.get("USDC")
                if usdt and usdc:
                    def _g(obj: dict, key: str) -> float:
                        return float((obj.get(key) or {}).get("peggedUSD") or 0.0) / 1e9

                    u_now, c_now = _g(usdt, "circulating"), _g(usdc, "circulating")
                    u_7d, c_7d = _g(usdt, "circulatingPrevWeek"), _g(usdc, "circulatingPrevWeek")
                    u_30d, c_30d = _g(usdt, "circulatingPrevMonth"), _g(usdc, "circulatingPrevMonth")
                    tot_now = u_now + c_now
                    return {
                        "usdt_b": round(u_now, 2),
                        "usdc_b": round(c_now, 2),
                        "total_b": round(tot_now, 2),
                        "delta_7d_b": round(tot_now - (u_7d + c_7d), 2) if (u_7d and c_7d) else None,
                        "delta_30d_b": round(tot_now - (u_30d + c_30d), 2) if (u_30d and c_30d) else None,
                    }
    except Exception as e:
        logger.debug("Failed DefiLlama stablecoins fetch: %s", e)
    return {}


async def _fetch_deribit_options_summary(session: aiohttp.ClientSession) -> Dict[str, Optional[float]]:
    """Fetches Deribit BTC option book summary: Put/Call OI, ATM IV term structure, and 25d skew proxy."""
    url = "https://www.deribit.com/api/v2/public/get_book_summary_by_currency?currency=BTC&kind=option"
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=5.0)) as r:
            if r.status != 200:
                return {}
            items = (await r.json()).get("result", [])
            now_dt = datetime.now(timezone.utc)
            put_oi = 0.0
            call_oi = 0.0
            front_ivs: List[float] = []
            back_ivs: List[float] = []
            skew_put_ivs: List[float] = []
            skew_call_ivs: List[float] = []

            for it in items:
                name = str(it.get("instrument_name", ""))
                parts = name.split("-")
                if len(parts) != 4:
                    continue
                cp = parts[3]
                oi = float(it.get("open_interest") or 0.0)
                if cp == "P":
                    put_oi += oi
                elif cp == "C":
                    call_oi += oi
                iv = float(it.get("mark_iv") or 0.0)
                spot = float(it.get("underlying_price") or 0.0)
                if iv <= 0.0 or spot <= 0.0:
                    continue
                try:
                    strike = float(parts[2])
                    exp_dt = datetime.strptime(parts[1], "%d%b%y").replace(tzinfo=timezone.utc)
                except ValueError:
                    continue
                dte = (exp_dt - now_dt).total_seconds() / 86400.0
                if dte < 1.0:
                    continue
                mny = strike / spot
                if 7.0 <= dte <= 35.0 and abs(mny - 1.0) <= 0.04:
                    front_ivs.append(iv)
                elif dte > 35.0 and abs(mny - 1.0) <= 0.05:
                    back_ivs.append(iv)
                if 7.0 <= dte <= 60.0:
                    if cp == "P" and 0.90 <= mny <= 0.96:
                        skew_put_ivs.append(iv)
                    elif cp == "C" and 1.04 <= mny <= 1.10:
                        skew_call_ivs.append(iv)

            tot_oi = put_oi + call_oi
            pc_ratio = round(put_oi / call_oi, 3) if call_oi > 0 else None
            iv_front = round(sum(front_ivs) / len(front_ivs), 1) if front_ivs else None
            iv_back = round(sum(back_ivs) / len(back_ivs), 1) if back_ivs else None
            skew_proxy = (
                round((sum(skew_put_ivs) / len(skew_put_ivs)) - (sum(skew_call_ivs) / len(skew_call_ivs)), 1)
                if (skew_put_ivs and skew_call_ivs)
                else None
            )
            return {
                "pc_oi_ratio": pc_ratio,
                "total_oi_btc": round(tot_oi, 0) if tot_oi > 0 else None,
                "iv_front": iv_front,
                "iv_back": iv_back,
                "skew_25d_proxy": skew_proxy,
            }
    except Exception as e:
        logger.debug("Failed Deribit options summary fetch: %s", e)
    return {}


async def _fetch_cross_exchange_perps_and_cb_vol(session: aiohttp.ClientSession) -> Dict[str, Any]:
    """Fetches Binance+Bybit+OKX perp OI/funding + Coinbase 24H Spot volume concurrently."""
    out: Dict[str, Any] = {}
    t_out = aiohttp.ClientTimeout(total=4.0)

    async def _bn():
        oi_btc = mark_px = fund_pct = None
        async with session.get("https://fapi.binance.com/fapi/v1/openInterest?symbol=BTCUSDT", timeout=t_out) as r:
            if r.status == 200:
                oi_btc = float((await r.json()).get("openInterest") or 0.0)
        async with session.get("https://fapi.binance.com/fapi/v1/premiumIndex?symbol=BTCUSDT", timeout=t_out) as r:
            if r.status == 200:
                d = await r.json()
                mark_px = float(d.get("markPrice") or 0.0)
                fund_pct = float(d.get("lastFundingRate") or 0.0) * 100.0
        if oi_btc and mark_px:
            return ("BN", oi_btc, oi_btc * mark_px, fund_pct)
        return None

    async def _byb():
        async with session.get("https://api.bybit.com/v5/market/tickers?category=linear&symbol=BTCUSDT", timeout=t_out) as r:
            if r.status == 200:
                lst = (await r.json()).get("result", {}).get("list", [])
                if lst:
                    it = lst[0]
                    oi_b = float(it.get("openInterest") or 0.0)
                    oi_u = float(it.get("openInterestValue") or 0.0)
                    f_p = float(it.get("fundingRate") or 0.0) * 100.0 if it.get("fundingRate") is not None else None
                    if oi_b > 0 and oi_u > 0:
                        return ("BYB", oi_b, oi_u, f_p)
        return None

    async def _okx():
        oi_b = oi_u = f_p = None
        async with session.get("https://www.okx.com/api/v5/public/open-interest?instType=SWAP&instId=BTC-USDT-SWAP", timeout=t_out) as r:
            if r.status == 200:
                d = (await r.json()).get("data", [])
                if d:
                    oi_b = float(d[0].get("oiCcy") or 0.0)
                    oi_u = float(d[0].get("oiUsd") or 0.0)
        async with session.get("https://www.okx.com/api/v5/public/funding-rate?instId=BTC-USDT-SWAP", timeout=t_out) as r:
            if r.status == 200:
                d = (await r.json()).get("data", [])
                if d and d[0].get("fundingRate") is not None:
                    f_p = float(d[0].get("fundingRate")) * 100.0
        if oi_b and oi_u:
            return ("OKX", oi_b, oi_u, f_p)
        return None

    async def _cb():
        async with session.get("https://api.exchange.coinbase.com/products/BTC-USD/stats", timeout=t_out) as r:
            if r.status == 200:
                v = (await r.json()).get("volume")
                return float(v) if v is not None else None
        return None

    bn_res, byb_res, okx_res, cb_vol = await asyncio.gather(_bn(), _byb(), _okx(), _cb(), return_exceptions=True)
    venues = [x for x in (bn_res, byb_res, okx_res) if isinstance(x, tuple)]
    if venues:
        out["agg_oi_btc"] = round(sum(v[1] for v in venues), 1)
        out["agg_oi_usd"] = round(sum(v[2] for v in venues), 0)
        out["venues_str"] = "+".join(v[0] for v in venues)
        w_num = sum(v[3] * v[2] for v in venues if v[3] is not None)
        w_den = sum(v[2] for v in venues if v[3] is not None)
        if w_den > 0:
            out["agg_funding_8h_pct"] = round(w_num / w_den, 5)
    if isinstance(cb_vol, float) and cb_vol > 0:
        out["cb_vol_24h_btc"] = round(cb_vol, 1)
    return out


async def _fetch_nyfed_liquidity(session: aiohttp.ClientSession) -> Dict[str, Optional[float]]:
    """Fetches latest SOFR rate/volume and ON RRP balance from official NY Fed Markets JSON APIs."""
    out: Dict[str, Optional[float]] = {}
    t_out = aiohttp.ClientTimeout(total=4.0)

    async def _sofr():
        async with session.get("https://markets.newyorkfed.org/api/rates/all/latest.json", timeout=t_out) as r:
            if r.status == 200:
                for it in (await r.json()).get("refRates", []):
                    if it.get("type") == "SOFR" and it.get("percentRate") is not None:
                        return float(it["percentRate"]), float(it["volumeInBillions"]) if it.get("volumeInBillions") else None
        return None

    async def _rrp():
        async with session.get("https://markets.newyorkfed.org/api/rp/reverserepo/propositions/search.json?size=3", timeout=t_out) as r:
            if r.status == 200:
                ops = (await r.json()).get("repo", {}).get("operations", [])
                for op in ops:
                    if op.get("totalAmtAccepted") is not None:
                        return round(float(op["totalAmtAccepted"]) / 1e9, 2)
        return None

    sofr_res, rrp_res = await asyncio.gather(_sofr(), _rrp(), return_exceptions=True)
    if isinstance(sofr_res, tuple):
        out["sofr_rate_pct"] = sofr_res[0]
        out["sofr_vol_b"] = sofr_res[1]
    if isinstance(rrp_res, float):
        out["rrp_balance_b"] = rrp_res
    return out


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

    # 1. Dispatch concurrent network tasks (all bounded <=5s timeout)
    yahoo_task = _fetch_yahoo_quotes(session)
    fng_task = _fetch_alternative_me_fng(session)
    coingecko_task = _fetch_coingecko_dominance(session)
    depth_task = _fetch_binance_depth_ratios(session)
    fred_tips_task = _fetch_fred_series(session, "DFII10")
    fred_breakeven_task = _fetch_fred_series(session, "T10YIE")
    farside_task = asyncio.to_thread(_fetch_farside_etf_flows_sync)
    cm_task = _fetch_coinmetrics_onchain(session)
    dl_task = _fetch_defillama_stablecoins(session)
    opt_task = _fetch_deribit_options_summary(session)
    perp_task = _fetch_cross_exchange_perps_and_cb_vol(session)
    nyfed_task = _fetch_nyfed_liquidity(session)

    (
        yahoo_data,
        fng_res,
        btc_dom,
        depth_res,
        fred_tips,
        fred_breakeven,
        farside_res,
        cm_res,
        dl_res,
        opt_res,
        perp_res,
        nyfed_res,
    ) = await asyncio.gather(
        yahoo_task,
        fng_task,
        coingecko_task,
        depth_task,
        fred_tips_task,
        fred_breakeven_task,
        farside_task,
        cm_task,
        dl_task,
        opt_task,
        perp_task,
        nyfed_task,
        return_exceptions=True,
    )

    # Populate Sentiment & Depth
    if isinstance(fng_res, tuple) and len(fng_res) == 2 and isinstance(fng_res[0], int):
        snap.fear_and_greed_score = fng_res[0]
        snap.fear_and_greed_classification = fng_res[1]
    if isinstance(btc_dom, float):
        snap.btc_dominance_pct = round(btc_dom, 1)
    if isinstance(depth_res, tuple) and len(depth_res) == 3 and isinstance(depth_res[0], float):
        snap.orderbook_depth_ratio_1pct = depth_res[0]
        snap.orderbook_depth_ratio_2pct = depth_res[1]
        snap.orderbook_spread_bps = depth_res[2]

    # Populate On-Chain (CoinMetrics Community)
    if isinstance(cm_res, dict) and cm_res:
        snap.onchain_mvrv_cur = cm_res.get("mvrv")
        snap.onchain_mvrv_date = cm_res.get("date")
        snap.onchain_exch_inflow_btc = cm_res.get("inflow_btc")
        snap.onchain_exch_outflow_btc = cm_res.get("outflow_btc")
        snap.onchain_exch_netflow_btc = cm_res.get("netflow_btc")
        snap.onchain_exch_netflow_usd = cm_res.get("netflow_usd")
        snap.onchain_exch_supply_btc = cm_res.get("supply_btc")

    # Populate Stablecoins (DefiLlama)
    if isinstance(dl_res, dict) and dl_res:
        snap.stablecoin_usdt_b = dl_res.get("usdt_b")
        snap.stablecoin_usdc_b = dl_res.get("usdc_b")
        snap.stablecoin_total_b = dl_res.get("total_b")
        snap.stablecoin_7d_delta_b = dl_res.get("delta_7d_b")
        snap.stablecoin_30d_delta_b = dl_res.get("delta_30d_b")

    # Populate Deribit Options Summary
    if isinstance(opt_res, dict) and opt_res:
        snap.options_put_call_oi_ratio = opt_res.get("pc_oi_ratio")
        snap.options_total_oi_btc = opt_res.get("total_oi_btc")
        snap.options_iv_front = opt_res.get("iv_front")
        snap.options_iv_back = opt_res.get("iv_back")
        snap.options_skew_25d_proxy = opt_res.get("skew_25d_proxy")

    # Populate Cross-Exchange Perps & Coinbase Spot Vol
    if isinstance(perp_res, dict) and perp_res:
        snap.agg_perp_oi_btc = perp_res.get("agg_oi_btc")
        snap.agg_perp_oi_usd = perp_res.get("agg_oi_usd")
        snap.agg_perp_funding_8h_pct = perp_res.get("agg_funding_8h_pct")
        snap.agg_perp_venues_str = perp_res.get("venues_str")
        snap.coinbase_spot_vol_24h_btc = perp_res.get("cb_vol_24h_btc")

    # Populate NY Fed Liquidity
    if isinstance(nyfed_res, dict) and nyfed_res:
        snap.us_sofr_rate_pct = nyfed_res.get("sofr_rate_pct")
        snap.us_sofr_vol_b = nyfed_res.get("sofr_vol_b")
        snap.us_rrp_balance_b = nyfed_res.get("rrp_balance_b")

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

        # HYG/LQD Credit Spread Appetite
        hyg_c = yahoo_data.get("hyg", {}).get("closes", [])
        lqd_c = yahoo_data.get("lqd", {}).get("closes", [])
        if hyg_c and lqd_c and lqd_c[-1] > 0:
            ratio_now = hyg_c[-1] / lqd_c[-1]
            snap.credit_hyg_lqd_ratio = round(ratio_now, 4)
            if len(hyg_c) >= 6 and len(lqd_c) >= 6 and lqd_c[-6] > 0:
                ratio_5d = hyg_c[-6] / lqd_c[-6]
                if ratio_5d > 0:
                    snap.credit_hyg_lqd_5d_chg_pct = round(((ratio_now / ratio_5d) - 1.0) * 100.0, 2)

        # US Spot BTC ETF Proxy (IBIT + FBTC Dollar Volume & 5D Signed Flow)
        vol_1d_sum = 0.0
        flow_5d_sum = 0.0
        has_etf_proxy = False
        for sym_k in ("ibit", "fbtc"):
            pairs = yahoo_data.get(sym_k, {}).get("cv_pairs", [])
            if pairs:
                has_etf_proxy = True
                last_c, last_v = pairs[-1]
                vol_1d_sum += last_c * last_v
                start_i = max(1, len(pairs) - 5)
                for idx_p in range(start_i, len(pairs)):
                    c_i, v_i = pairs[idx_p]
                    c_prev, _ = pairs[idx_p - 1]
                    sign = 1.0 if c_i >= c_prev else -1.0
                    flow_5d_sum += sign * c_i * v_i
        if has_etf_proxy and vol_1d_sum > 0:
            snap.etf_proxy_vol_1d_usd = round(vol_1d_sum, 0)
            snap.etf_proxy_flow_5d_usd = round(flow_5d_sum, 0)

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
