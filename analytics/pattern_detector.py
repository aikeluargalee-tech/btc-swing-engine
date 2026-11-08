"""BTC Classic Chart Pattern & Candlestick Geometry Engine (Desk [B] & Desk [P] Integration).

Rule-based geometric pattern detection with multi-timeframe confirmation (4H & 1H),
tight tolerance filters, neckline trigger status, ASCII terminal chart rendering,
and auto-updating interactive TradingView Lightweight Charts (chart.html).

Patterns Supported:
- Double Bottom / Double Top
- Head and Shoulders / Inverse Head and Shoulders
- Rising Wedge / Falling Wedge
- Ascending Triangle / Descending Triangle / Symmetrical Triangle
"""

from __future__ import annotations

import json
import logging
import os
import pathlib
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np
from rich import box
from rich.align import Align
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from config.settings import EngineConfig
from core.models import KlineBar, PatternCandidate, PatternEvaluation
from core.state_store import StateStore

logger = logging.getLogger(__name__)

HTML_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "chart.html"
)

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta http-equiv="refresh" content="30">
  <title>BTC/USDT Pattern & Structure Chart</title>
  <script src="https://unpkg.com/lightweight-charts@4.1.3/dist/lightweight-charts.standalone.production.js"></script>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      background-color: #0b0e14;
      color: #e0e6ed;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      display: flex;
      flex-direction: column;
      height: 100vh;
      overflow: hidden;
    }
    header {
      background-color: #121824;
      padding: 12px 24px;
      border-bottom: 1px solid #1f293d;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 12px;
    }
    .title-group { display: flex; align-items: center; gap: 14px; }
    .title { font-size: 18px; font-weight: 700; color: #00e5ff; letter-spacing: 0.5px; }
    .badge {
      padding: 4px 10px;
      border-radius: 4px;
      font-size: 12px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      background-color: #ffd600;
      color: #000;
    }
    .metrics { display: flex; gap: 24px; font-size: 13px; }
    .metric-item span { color: #8899a6; font-size: 11px; display: block; }
    .metric-item b { font-size: 15px; font-weight: 600; color: #fff; }
    .chart-container { flex: 1; position: relative; width: 100%; }
    #chart { width: 100%; height: 100%; }
    .conclusion-bar {
      background-color: #121824;
      border-top: 1px solid #1f293d;
      padding: 10px 24px;
      font-size: 13px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .highlight { color: #ffd600; font-weight: 600; }
  </style>
</head>
<body>
  <header>
    <div class="title-group">
      <div class="title">BTC Swing Engine &bull; Geometric Pattern Chart</div>
      <div class="badge">__PATTERN_BADGE__</div>
    </div>
    <div class="metrics">
      <div class="metric-item"><span>SPOT PRICE</span><b style="color: #00e676;">__PRICE__</b></div>
      <div class="metric-item"><span>UPDATED (UTC)</span><b>__TIMESTAMP__</b></div>
      <div class="metric-item"><span>STRUCTURE</span><b style="color: #ffd600;">__STRUCTURE__</b></div>
      <div class="metric-item"><span>TRIGGER</span><b style="color: #00e5ff;">__TRIGGER__</b></div>
    </div>
  </header>
  <div class="chart-container">
    <div id="chart"></div>
  </div>
  <div class="conclusion-bar">
    <div><b>Tactical Playbook:</b> <span class="highlight">__TACTICAL_PLAYBOOK__</span></div>
    <div style="color: #8899a6; font-size: 11px;">Auto-refreshes every 30s &bull; Binance Spot 1H/4H</div>
  </div>
  <script>
    const chart = LightweightCharts.createChart(document.getElementById('chart'), {
      layout: {
        background: { color: '#0b0e14' },
        textColor: '#8899a6',
      },
      grid: {
        vertLines: { color: '#161d2b' },
        horzLines: { color: '#161d2b' },
      },
      crosshair: {
        mode: LightweightCharts.CrosshairMode.Normal,
      },
      rightPriceScale: {
        borderColor: '#1f293d',
      },
      timeScale: {
        borderColor: '#1f293d',
        timeVisible: true,
        secondsVisible: false,
      },
    });

    const candleSeries = chart.addCandlestickSeries({
      upColor: '#00e676',
      downColor: '#ef5350',
      borderUpColor: '#00e676',
      borderDownColor: '#ef5350',
      wickUpColor: '#00e676',
      wickDownColor: '#ef5350',
    });

    const candleData = __CANDLE_DATA__;
    candleSeries.setData(candleData);

    const priceLines = __PRICE_LINES__;
    priceLines.forEach(pl => {
      candleSeries.createPriceLine({
        price: pl.price,
        color: pl.color,
        lineWidth: 2,
        lineStyle: LightweightCharts.LineStyle.Dashed,
        axisLabelVisible: true,
        title: pl.title,
      });
    });

    const markers = __MARKERS__;
    if (markers.length > 0) {
      candleSeries.setMarkers(markers);
    }

    chart.timeScale().fitContent();

    window.addEventListener('resize', () => {
      chart.applyOptions({
        width: document.getElementById('chart').clientWidth,
        height: document.getElementById('chart').clientHeight,
      });
    });
  </script>
</body>
</html>
"""


def _price_tol(a: float, b: float, tol: float = 0.012) -> bool:
    """Returns True if price a and b are within relative tolerance."""
    mx = max(abs(a), abs(b))
    if mx == 0:
        return False
    return abs(a - b) / mx <= tol


def klines_to_ohlcv_list(klines: Sequence[KlineBar]) -> List[List[float]]:
    """Converts a sequence of KlineBar objects into standard [[ts_ms, o, h, l, c, v], ...]."""
    return [
        [
            float(k.timestamp_ms),
            float(k.open),
            float(k.high),
            float(k.low),
            float(k.close),
            float(k.volume),
        ]
        for k in klines
    ]


def detect_swings(ohlcv: List[List[float]], left: int = 5, right: int = 5) -> List[Dict[str, Any]]:
    """Detects swing highs and swing lows across OHLCV bars using a local peak/trough window."""
    swings: List[Dict[str, Any]] = []
    if len(ohlcv) < (left + right + 1):
        return swings

    highs = [c[2] for c in ohlcv]
    lows = [c[3] for c in ohlcv]
    times = [c[0] for c in ohlcv]

    for i in range(left, len(ohlcv) - right):
        if all(highs[i] >= highs[i - j] for j in range(1, left + 1)) and all(
            highs[i] >= highs[i + j] for j in range(1, right + 1)
        ):
            swings.append({"type": "high", "price": highs[i], "index": i, "time": times[i]})
        if all(lows[i] <= lows[i - j] for j in range(1, left + 1)) and all(
            lows[i] <= lows[i + j] for j in range(1, right + 1)
        ):
            swings.append({"type": "low", "price": lows[i], "index": i, "time": times[i]})

    return swings


def detect_double_bottom(
    swings: List[Dict[str, Any]],
    total_bars: int = 0,
    spot_price: float = 0.0,
    max_bars_ago: int = 30,
) -> Optional[Dict[str, Any]]:
    """Detects W-formation / Double Bottom with neckline peak and min 8 bars separation."""
    lows = [s for s in swings if s["type"] == "low"]
    if len(lows) < 2:
        return None

    for i in range(len(lows) - 1, 0, -1):
        l2 = lows[i]
        if total_bars > 0 and (total_bars - l2["index"]) > max_bars_ago:
            continue
        for j in range(i - 1, max(-1, i - 8), -1):
            l1 = lows[j]
            bars = l2["index"] - l1["index"]
            if bars < 8 or bars > 80:
                continue
            if _price_tol(l1["price"], l2["price"], 0.015):
                highs_between = [
                    s for s in swings if s["type"] == "high" and l1["index"] < s["index"] < l2["index"]
                ]
                if not highs_between:
                    continue
                neckline = max(h["price"] for h in highs_between)
                if neckline < l1["price"] * 1.012:
                    continue
                measured_move = neckline - min(l1["price"], l2["price"])
                if spot_price > 0 and spot_price > (neckline + 1.25 * measured_move):
                    continue
                conf = 0.84 if _price_tol(l1["price"], l2["price"], 0.007) else 0.70
                return {
                    "pattern": "Double Bottom",
                    "bias": "Bullish",
                    "low1": l1["price"],
                    "low2": l2["price"],
                    "neckline": neckline,
                    "floor_or_roof": min(l1["price"], l2["price"]),
                    "bars": bars,
                    "confidence": conf,
                    "l1_idx": l1["index"],
                    "l2_idx": l2["index"],
                }
    return None


def detect_double_top(
    swings: List[Dict[str, Any]],
    total_bars: int = 0,
    spot_price: float = 0.0,
    max_bars_ago: int = 30,
) -> Optional[Dict[str, Any]]:
    """Detects M-formation / Double Top with neckline valley and min 8 bars separation."""
    highs = [s for s in swings if s["type"] == "high"]
    if len(highs) < 2:
        return None

    for i in range(len(highs) - 1, 0, -1):
        h2 = highs[i]
        if total_bars > 0 and (total_bars - h2["index"]) > max_bars_ago:
            continue
        for j in range(i - 1, max(-1, i - 8), -1):
            h1 = highs[j]
            bars = h2["index"] - h1["index"]
            if bars < 8 or bars > 80:
                continue
            if _price_tol(h1["price"], h2["price"], 0.015):
                lows_between = [
                    s for s in swings if s["type"] == "low" and h1["index"] < s["index"] < h2["index"]
                ]
                if not lows_between:
                    continue
                neckline = min(l["price"] for l in lows_between)
                if neckline > h1["price"] * 0.988:
                    continue
                measured_move = max(h1["price"], h2["price"]) - neckline
                if spot_price > 0 and spot_price < (neckline - 1.25 * measured_move):
                    continue
                conf = 0.84 if _price_tol(h1["price"], h2["price"], 0.007) else 0.70
                return {
                    "pattern": "Double Top",
                    "bias": "Bearish",
                    "high1": h1["price"],
                    "high2": h2["price"],
                    "neckline": neckline,
                    "floor_or_roof": max(h1["price"], h2["price"]),
                    "bars": bars,
                    "confidence": conf,
                    "h1_idx": h1["index"],
                    "h2_idx": h2["index"],
                }
    return None


def detect_head_shoulders(
    swings: List[Dict[str, Any]],
    total_bars: int = 0,
    spot_price: float = 0.0,
    max_bars_ago: int = 30,
) -> Optional[Dict[str, Any]]:
    """Detects classic Head and Shoulders bearish top reversal.
    
    Strict structural requirements:
    1. Head must be clearly higher than left and right shoulders (> 0.8%).
    2. Left and right shoulders must be within 2.0% price tolerance.
    3. Minimum bar separation: left to head >= 6 bars, head to right >= 6 bars.
    4. Dual distinct troughs: Trough 1 between left & head, Trough 2 between head & right.
    5. Neckline symmetry: Trough 1 and Trough 2 within 3.5% price tolerance.
    6. Recency check: right shoulder must be within max_bars_ago (default 30 bars).
    7. Measured-move exhaustion: if spot has dropped > 1.25x measured move past neckline, pattern is exhausted.
    """
    highs = [s for s in swings if s["type"] == "high"]
    if len(highs) < 3:
        return None

    for i in range(len(highs) - 1, 1, -1):
        right, head, left = highs[i], highs[i - 1], highs[i - 2]
        if total_bars > 0 and (total_bars - right["index"]) > max_bars_ago:
            continue
        if not (head["price"] > left["price"] * 1.008 and head["price"] > right["price"] * 1.008):
            continue
        if not _price_tol(left["price"], right["price"], 0.020):
            continue
        if (head["index"] - left["index"] < 6) or (right["index"] - head["index"] < 6):
            continue

        troughs_1 = [
            s for s in swings if s["type"] == "low" and left["index"] < s["index"] < head["index"]
        ]
        troughs_2 = [
            s for s in swings if s["type"] == "low" and head["index"] < s["index"] < right["index"]
        ]
        if not troughs_1 or not troughs_2:
            continue

        t1 = min(troughs_1, key=lambda s: s["price"])
        t2 = min(troughs_2, key=lambda s: s["price"])

        if not _price_tol(t1["price"], t2["price"], 0.035):
            continue

        neckline = min(t1["price"], t2["price"])
        height = head["price"] - neckline
        if spot_price > 0 and spot_price < (neckline - 1.25 * height):
            continue

        shoulder_diff = abs(left["price"] - right["price"]) / left["price"]
        conf = 0.86 if shoulder_diff < 0.009 else 0.72
        return {
            "pattern": "Head and Shoulders",
            "bias": "Bearish",
            "left": left["price"],
            "head": head["price"],
            "right": right["price"],
            "trough1": t1["price"],
            "trough2": t2["price"],
            "neckline": neckline,
            "floor_or_roof": head["price"],
            "confidence": conf,
            "right_idx": right["index"],
        }
    return None


def detect_inverse_hs(
    swings: List[Dict[str, Any]],
    total_bars: int = 0,
    spot_price: float = 0.0,
    max_bars_ago: int = 30,
) -> Optional[Dict[str, Any]]:
    """Detects Inverse Head and Shoulders bullish bottom reversal.
    
    Strict structural requirements:
    1. Head must be clearly lower than left and right shoulders (< -0.8%).
    2. Left and right shoulders must be within 2.0% price tolerance.
    3. Minimum bar separation: left to head >= 6 bars, head to right >= 6 bars.
    4. Dual distinct peaks: Peak 1 between left & head, Peak 2 between head & right.
    5. Neckline symmetry: Peak 1 and Peak 2 within 3.5% price tolerance.
    6. Recency check: right shoulder must be within max_bars_ago (default 30 bars).
    7. Measured-move exhaustion: if spot has risen > 1.25x measured move past neckline, pattern is exhausted.
    """
    lows = [s for s in swings if s["type"] == "low"]
    if len(lows) < 3:
        return None

    for i in range(len(lows) - 1, 1, -1):
        right, head, left = lows[i], lows[i - 1], lows[i - 2]
        if total_bars > 0 and (total_bars - right["index"]) > max_bars_ago:
            continue
        if not (head["price"] < left["price"] * 0.992 and head["price"] < right["price"] * 0.992):
            continue
        if not _price_tol(left["price"], right["price"], 0.020):
            continue
        if (head["index"] - left["index"] < 6) or (right["index"] - head["index"] < 6):
            continue

        peaks_1 = [
            s for s in swings if s["type"] == "high" and left["index"] < s["index"] < head["index"]
        ]
        peaks_2 = [
            s for s in swings if s["type"] == "high" and head["index"] < s["index"] < right["index"]
        ]
        if not peaks_1 or not peaks_2:
            continue

        p1 = max(peaks_1, key=lambda s: s["price"])
        p2 = max(peaks_2, key=lambda s: s["price"])

        if not _price_tol(p1["price"], p2["price"], 0.035):
            continue

        neckline = max(p1["price"], p2["price"])
        height = neckline - head["price"]
        if spot_price > 0 and spot_price > (neckline + 1.25 * height):
            continue

        shoulder_diff = abs(left["price"] - right["price"]) / left["price"]
        conf = 0.86 if shoulder_diff < 0.009 else 0.72
        return {
            "pattern": "Inverse Head and Shoulders",
            "bias": "Bullish",
            "left": left["price"],
            "head": head["price"],
            "right": right["price"],
            "peak1": p1["price"],
            "peak2": p2["price"],
            "neckline": neckline,
            "floor_or_roof": head["price"],
            "confidence": conf,
            "right_idx": right["index"],
        }
    return None


def detect_wedge(
    swings: List[Dict[str, Any]],
    total_bars: int = 0,
    spot_price: float = 0.0,
    max_bars_ago: int = 30,
) -> Optional[Dict[str, Any]]:
    """Detects Rising Wedge (bearish) and Falling Wedge (bullish) from converging slopes."""
    highs = [s for s in swings if s["type"] == "high"][-5:]
    lows = [s for s in swings if s["type"] == "low"][-5:]
    if len(highs) < 3 or len(lows) < 3:
        return None

    last_pivot_idx = max(highs[-1]["index"], lows[-1]["index"])
    if total_bars > 0 and (total_bars - last_pivot_idx) > max_bars_ago:
        return None

    def _calc_slope(pts: List[Dict[str, Any]]) -> float:
        if len(pts) < 2:
            return 0.0
        x = np.array([p["index"] for p in pts], dtype=float)
        y = np.array([p["price"] for p in pts], dtype=float)
        return float(np.polyfit(x, y, 1)[0])

    hs = _calc_slope(highs[-3:])
    ls = _calc_slope(lows[-3:])

    # Rising Wedge: both slopes up, but highs slope is less than lows slope (converging upward)
    if hs > 0 and ls > 0 and hs < ls * 0.70 and abs(hs - ls) > 1e-5:
        return {
            "pattern": "Rising Wedge",
            "bias": "Bearish",
            "confidence": 0.74,
            "high_slope": hs,
            "low_slope": ls,
            "floor_or_roof": highs[-1]["price"],
            "neckline": lows[-1]["price"],
        }
    # Falling Wedge: both slopes down, highs slope dropping faster than lows slope (converging downward)
    if hs < 0 and ls < 0 and abs(hs) > abs(ls) * 0.70 and abs(hs - ls) > 1e-5:
        return {
            "pattern": "Falling Wedge",
            "bias": "Bullish",
            "confidence": 0.74,
            "high_slope": hs,
            "low_slope": ls,
            "floor_or_roof": lows[-1]["price"],
            "neckline": highs[-1]["price"],
        }
    return None


def detect_triangle(
    swings: List[Dict[str, Any]],
    total_bars: int = 0,
    spot_price: float = 0.0,
    max_bars_ago: int = 30,
) -> Optional[Dict[str, Any]]:
    """Detects Ascending Triangle (bullish), Descending Triangle (bearish), and Symmetrical Triangle (compression)."""
    highs = [s for s in swings if s["type"] == "high"][-5:]
    lows = [s for s in swings if s["type"] == "low"][-5:]
    if len(highs) < 3 or len(lows) < 3:
        return None

    last_pivot_idx = max(highs[-1]["index"], lows[-1]["index"])
    if total_bars > 0 and (total_bars - last_pivot_idx) > max_bars_ago:
        return None

    def _calc_slope(pts: List[Dict[str, Any]]) -> float:
        x = np.array([p["index"] for p in pts], dtype=float)
        y = np.array([p["price"] for p in pts], dtype=float)
        return float(np.polyfit(x, y, 1)[0])

    hs = _calc_slope(highs[-3:])
    ls = _calc_slope(lows[-3:])

    # Ascending: flat ceiling, rising lows
    if abs(hs) < max(abs(ls) * 0.35, 1e-4) and ls > 0:
        return {
            "pattern": "Ascending Triangle",
            "bias": "Bullish",
            "confidence": 0.72,
            "high_slope": hs,
            "low_slope": ls,
            "neckline": highs[-1]["price"],
            "floor_or_roof": lows[-1]["price"],
        }
    # Descending: flat floor, descending highs
    if abs(ls) < max(abs(hs) * 0.35, 1e-4) and hs < 0:
        return {
            "pattern": "Descending Triangle",
            "bias": "Bearish",
            "confidence": 0.72,
            "high_slope": hs,
            "low_slope": ls,
            "neckline": lows[-1]["price"],
            "floor_or_roof": highs[-1]["price"],
        }
    # Symmetrical: descending highs, ascending lows converging
    if hs < 0 and ls > 0 and abs(abs(hs) - ls) / max(abs(hs), ls) < 0.6:
        return {
            "pattern": "Symmetrical Triangle",
            "bias": "Neutral",
            "confidence": 0.65,
            "high_slope": hs,
            "low_slope": ls,
            "neckline": highs[-1]["price"],
            "floor_or_roof": lows[-1]["price"],
        }
    return None


def scan_patterns(
    swings: List[Dict[str, Any]],
    timeframe: str = "1h",
    total_bars: int = 0,
    spot_price: float = 0.0,
) -> List[PatternCandidate]:
    """Scans all pattern detectors against swings and returns ranked PatternCandidate objects."""
    max_bars = 30 if timeframe == "4h" else 50
    candidates_raw: List[Dict[str, Any]] = []
    for fn in (
        detect_double_bottom,
        detect_double_top,
        detect_head_shoulders,
        detect_inverse_hs,
        detect_wedge,
        detect_triangle,
    ):
        p = fn(swings, total_bars=total_bars, spot_price=spot_price, max_bars_ago=max_bars)
        if p:
            candidates_raw.append(p)

    best_by_name: Dict[str, Dict[str, Any]] = {}
    for p in candidates_raw:
        name = p["pattern"]
        if name not in best_by_name or p["confidence"] > best_by_name[name]["confidence"]:
            best_by_name[name] = p

    sorted_p = sorted(best_by_name.values(), key=lambda x: x["confidence"], reverse=True)

    result: List[PatternCandidate] = []
    for p in sorted_p:
        cand = PatternCandidate(
            pattern=p["pattern"],
            bias=p.get("bias", "Neutral"),
            confidence=p.get("confidence", 0.5),
            timeframe=timeframe,
            neckline=p.get("neckline"),
            floor_or_roof=p.get("floor_or_roof"),
            details=p,
            high_slope=p.get("high_slope"),
            low_slope=p.get("low_slope"),
        )
        result.append(cand)
    return result


def analyze_structure(ohlcv: List[List[float]], swings: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Evaluates high-level structure trend (HH/HL vs LH/LL)."""
    if not ohlcv:
        return {"current_price": 0.0, "timestamp": "", "trend": "Ranging"}

    current_price = ohlcv[-1][4]
    recent_highs = [s for s in swings if s["type"] == "high"][-3:]
    recent_lows = [s for s in swings if s["type"] == "low"][-3:]
    trend = "Ranging"
    if len(recent_highs) >= 2 and len(recent_lows) >= 2:
        if (
            recent_highs[-1]["price"] > recent_highs[-2]["price"]
            and recent_lows[-1]["price"] > recent_lows[-2]["price"]
        ):
            trend = "Bullish structure (HH/HL)"
        elif (
            recent_highs[-1]["price"] < recent_highs[-2]["price"]
            and recent_lows[-1]["price"] < recent_lows[-2]["price"]
        ):
            trend = "Bearish structure (LH/LL)"

    ts_str = datetime.fromtimestamp(ohlcv[-1][0] / 1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return {"current_price": current_price, "timestamp": ts_str, "trend": trend}


def export_chart_html(
    ohlcv: List[List[float]],
    swings: List[Dict[str, Any]],
    top_p: Optional[PatternCandidate],
    structure: Dict[str, Any],
    trigger_status: str,
    tactical_playbook: str,
    filepath: str = HTML_PATH,
) -> None:
    """Exports interactive TradingView Lightweight Chart HTML with candles, dashed neckline, and pivot markers."""
    try:
        candle_data = [
            {
                "time": int(c[0] / 1000),
                "open": float(c[1]),
                "high": float(c[2]),
                "low": float(c[3]),
                "close": float(c[4]),
            }
            for c in ohlcv
        ]

        markers: List[Dict[str, Any]] = []
        times_map = {s["index"]: int(s["time"] / 1000) for s in swings}

        if top_p and top_p.details:
            dtl = top_p.details
            if "l1_idx" in dtl and "low1" in dtl:
                t1 = times_map.get(dtl["l1_idx"])
                if t1:
                    markers.append({
                        "time": t1,
                        "position": "belowBar",
                        "color": "#00e676",
                        "shape": "arrowUp",
                        "text": f"Low 1 (${dtl['low1']:,.0f})",
                    })
            if "l2_idx" in dtl and "low2" in dtl:
                t2 = times_map.get(dtl["l2_idx"])
                if t2:
                    markers.append({
                        "time": t2,
                        "position": "belowBar",
                        "color": "#00e676",
                        "shape": "arrowUp",
                        "text": f"Low 2 (${dtl['low2']:,.0f})",
                    })
            if "h1_idx" in dtl and "high1" in dtl:
                t1 = times_map.get(dtl["h1_idx"])
                if t1:
                    markers.append({
                        "time": t1,
                        "position": "aboveBar",
                        "color": "#ef5350",
                        "shape": "arrowDown",
                        "text": f"High 1 (${dtl['high1']:,.0f})",
                    })
            if "h2_idx" in dtl and "high2" in dtl:
                t2 = times_map.get(dtl["h2_idx"])
                if t2:
                    markers.append({
                        "time": t2,
                        "position": "aboveBar",
                        "color": "#ef5350",
                        "shape": "arrowDown",
                        "text": f"High 2 (${dtl['high2']:,.0f})",
                    })

        price_lines: List[Dict[str, Any]] = []
        if top_p and top_p.neckline:
            price_lines.append({
                "price": float(top_p.neckline),
                "color": "#e040fb",
                "title": f"{top_p.pattern} Neckline (${top_p.neckline:,.0f})",
            })
        if top_p and top_p.floor_or_roof:
            fl_color = "#00e676" if top_p.bias == "Bullish" else "#ef5350"
            fl_title = "Support Floor" if top_p.bias == "Bullish" else "Resistance Roof"
            price_lines.append({
                "price": float(top_p.floor_or_roof),
                "color": fl_color,
                "title": f"{fl_title} (${top_p.floor_or_roof:,.0f})",
            })

        badge = f"{top_p.pattern} ({top_p.confidence:.0%})" if top_p else "NO PATTERN"
        price_str = f"${structure.get('current_price', 0):,.2f}"
        time_str = structure.get("timestamp", "N/A")
        trend_str = structure.get("trend", "Ranging")

        clean_playbook = tactical_playbook.replace('"', "'")

        html = (
            HTML_TEMPLATE.replace("__PATTERN_BADGE__", badge)
            .replace("__PRICE__", price_str)
            .replace("__TIMESTAMP__", time_str)
            .replace("__STRUCTURE__", trend_str)
            .replace("__TRIGGER__", trigger_status)
            .replace("__TACTICAL_PLAYBOOK__", clean_playbook)
            .replace("__CANDLE_DATA__", json.dumps(candle_data))
            .replace("__PRICE_LINES__", json.dumps(price_lines))
            .replace("__MARKERS__", json.dumps(markers))
        )

        pathlib.Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)
    except Exception as exc:
        logger.debug("Failed to export chart.html: %s", exc)


def render_candlestick_ascii(
    ohlcv: List[List[float]],
    swings: List[Dict[str, Any]],
    top_p: Optional[PatternCandidate],
    width: int = 95,
    height: int = 12,
) -> Panel:
    """Renders a high-density terminal ASCII candlestick chart with neckline overlay and pivot markers."""
    if not ohlcv:
        return Panel("[dim]No candlestick data available[/dim]", title="Candlestick Chart", box=box.ROUNDED)

    num_candles = max(20, min(len(ohlcv), width - 30))
    sub_ohlcv = ohlcv[-num_candles:]
    offset = len(ohlcv) - num_candles

    highs = [c[2] for c in sub_ohlcv]
    lows = [c[3] for c in sub_ohlcv]
    min_p = min(lows) if lows else 0.0
    max_p = max(highs) if highs else 1.0

    if top_p and top_p.neckline:
        max_p = max(max_p, top_p.neckline * 1.002)
        min_p = min(min_p, top_p.neckline * 0.998)
    if top_p and top_p.floor_or_roof:
        max_p = max(max_p, top_p.floor_or_roof * 1.002)
        min_p = min(min_p, top_p.floor_or_roof * 0.998)

    price_range = max_p - min_p if max_p != min_p else 1.0

    def _p_to_r(p: float) -> int:
        r = int((p - min_p) / price_range * (height - 1))
        return max(0, min(height - 1, r))

    grid = [[(" ", "default") for _ in range(num_candles)] for _ in range(height)]

    # Draw candle bodies and wicks
    for col, c in enumerate(sub_ohlcv):
        o, h, l, cl = c[1], c[2], c[3], c[4]
        color = "green" if cl >= o else "red"
        r_h = _p_to_r(h)
        r_l = _p_to_r(l)
        r_top = _p_to_r(max(o, cl))
        r_bot = _p_to_r(min(o, cl))
        for r in range(r_l, r_h + 1):
            grid[r][col] = ("│", color)
        for r in range(r_bot, r_top + 1):
            grid[r][col] = ("█", color)

    # Draw Neckline
    nl_r = _p_to_r(top_p.neckline) if top_p and top_p.neckline else None
    if nl_r is not None:
        for col in range(num_candles):
            ch, colr = grid[nl_r][col]
            grid[nl_r][col] = ("┼" if ch == "│" else "┄", "bold magenta")

    # Draw Floor or Roof
    fl_r = _p_to_r(top_p.floor_or_roof) if top_p and top_p.floor_or_roof else None
    if fl_r is not None and fl_r != nl_r:
        line_color = "bold red" if (top_p and top_p.bias == "Bullish") else "bold green"
        for col in range(num_candles):
            ch, colr = grid[fl_r][col]
            grid[fl_r][col] = ("┼" if ch == "│" else "┄", line_color)

    lines: List[Text] = []
    for r in range(height - 1, -1, -1):
        p_val = min_p + (r / (height - 1)) * price_range
        tag = ""
        if nl_r is not None and r == nl_r and top_p and top_p.neckline:
            tag = f" [bold magenta]◀ NL ${top_p.neckline:,.0f}[/bold magenta]"
        elif fl_r is not None and r == fl_r and top_p and top_p.floor_or_roof:
            tag_name = "Floor" if top_p.bias == "Bullish" else "Roof"
            tag_col = "bold red" if top_p.bias == "Bullish" else "bold green"
            tag = f" [{tag_col}]◀ {tag_name} ${top_p.floor_or_roof:,.0f}[/{tag_col}]"

        row_text = Text(f"${p_val:>7,.0f} │ ", style="dim")
        for col in range(num_candles):
            ch, colr = grid[r][col]
            row_text.append(ch, style=colr)
        if tag:
            row_text.append_text(Text.from_markup(tag))
        lines.append(row_text)

    # Pivot annotation row
    pivot_row = Text(" " * 10 + "│ ")
    pivot_chars = [" "] * num_candles
    for s in swings:
        if s["index"] >= offset:
            c_idx = s["index"] - offset
            if 0 <= c_idx < num_candles:
                pivot_chars[c_idx] = "▲" if s["type"] == "low" else "▼"

    for ch in pivot_chars:
        if ch == "▲":
            pivot_row.append("▲", style="bold green")
        elif ch == "▼":
            pivot_row.append("▼", style="bold red")
        else:
            pivot_row.append(" ")
    lines.append(pivot_row)

    content = Text("\n").join(lines)
    return Panel(
        content,
        title="[bold white]BTC/USDT Native Candlestick Chart (Geometric Overlays & Pivots)[/bold white]",
        border_style="cyan",
        box=box.ROUNDED,
    )


class PatternEngine:
    """Evaluates multi-timeframe classic chart patterns, triggers, and auto-exports chart.html."""

    def __init__(self, config: Optional[EngineConfig] = None) -> None:
        self.config = config or EngineConfig()

    def evaluate(
        self,
        store: StateStore,
        spot_1h: Optional[Sequence[KlineBar]] = None,
        spot_4h: Optional[Sequence[KlineBar]] = None,
    ) -> PatternEvaluation:
        """Runs full geometric scan across Binance Spot 1H and 4H klines."""
        bars_1h = list(spot_1h if spot_1h is not None else store.spot_klines_1h)
        bars_4h = list(spot_4h if spot_4h is not None else store.spot_klines_4h)

        ohlcv_1h = klines_to_ohlcv_list(bars_1h)
        ohlcv_4h = klines_to_ohlcv_list(bars_4h)

        spot_px = store.binance_spot_price or (bars_1h[-1].close if bars_1h else 0.0)

        # 1. Detect swings on 1H (tactical) and 4H (macro)
        swings_1h = detect_swings(ohlcv_1h, left=5, right=5) if len(ohlcv_1h) >= 20 else []
        swings_4h = detect_swings(ohlcv_4h, left=3, right=3) if len(ohlcv_4h) >= 15 else []

        # 2. Scan patterns on both timeframes
        patterns_1h = scan_patterns(
            swings_1h,
            timeframe="1h",
            total_bars=len(ohlcv_1h),
            spot_price=spot_px,
        )
        patterns_4h = scan_patterns(
            swings_4h,
            timeframe="4h",
            total_bars=len(ohlcv_4h),
            spot_price=spot_px,
        )

        # 3. Analyze 1H structure trend
        struct = analyze_structure(ohlcv_1h, swings_1h)

        # 4. Multi-timeframe synthesis
        # Prioritize 4H pattern if confidence >= 70%, otherwise use 1H pattern
        top_pattern: Optional[PatternCandidate] = None
        all_candidates: List[PatternCandidate] = []

        if patterns_4h and patterns_4h[0].confidence >= 0.70:
            top_pattern = patterns_4h[0]
            all_candidates.extend(patterns_4h)
            all_candidates.extend(patterns_1h)
        elif patterns_1h:
            top_pattern = patterns_1h[0]
            all_candidates.extend(patterns_1h)
            all_candidates.extend(patterns_4h)
        elif patterns_4h:
            top_pattern = patterns_4h[0]
            all_candidates.extend(patterns_4h)

        # Multi-timeframe alignment check
        mtf_aligned = False
        if patterns_4h and patterns_1h:
            if patterns_4h[0].bias == patterns_1h[0].bias and patterns_4h[0].bias != "Neutral":
                mtf_aligned = True
                if top_pattern:
                    top_pattern.confidence = min(0.95, top_pattern.confidence + 0.10)

        # 5. Determine Trigger Status & Tactical Playbook
        trigger_status = "STANDBY"
        tactical_playbook = "Observe price action; waiting for confirmed geometric pattern formation."

        if top_pattern:
            bias = top_pattern.bias
            nl = top_pattern.neckline
            fl_rf = top_pattern.floor_or_roof

            if bias == "Bullish":
                if nl and spot_px >= nl:
                    trigger_status = "CONFIRMED_BREAKOUT"
                    tactical_playbook = f"Confirmed 1H close above neckline (${nl:,.0f}). Buyers active; trail stop at ${fl_rf:,.0f}."
                elif fl_rf and spot_px < fl_rf:
                    trigger_status = "INVALIDATED"
                    tactical_playbook = f"Price lost invalidation floor (${fl_rf:,.0f}). Pattern thesis dead; stand aside in cash."
                elif nl:
                    trigger_status = "PENDING_BREAKOUT"
                    dist_pct = (nl - spot_px) / spot_px * 100.0
                    tactical_playbook = f"Watch neckline breakout at ${nl:,.0f} (+{dist_pct:.1f}%). Invalidation floor at ${fl_rf:,.0f}."
            elif bias == "Bearish":
                if nl and spot_px <= nl:
                    trigger_status = "CONFIRMED_BREAKDOWN"
                    tactical_playbook = f"Confirmed breakdown below neckline (${nl:,.0f}). Sellers in control; protect capital."
                elif fl_rf and spot_px > fl_rf:
                    trigger_status = "INVALIDATED"
                    tactical_playbook = f"Price reclaimed invalidation roof (${fl_rf:,.0f}). Bearish pattern invalidated."
                elif nl:
                    trigger_status = "PENDING_BREAKDOWN"
                    dist_pct = (spot_px - nl) / spot_px * 100.0
                    tactical_playbook = f"Caution: ${nl:,.0f} neckline support tested (-{dist_pct:.1f}%). Stop-losses should sit at ${fl_rf:,.0f}."
            else:
                trigger_status = "CONSOLIDATING"
                tactical_playbook = "Volatility compressing inside triangle boundaries. Wait for expansion candle."

        evaluation = PatternEvaluation(
            timestamp_utc=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            spot_price=spot_px,
            structure_trend=struct.get("trend", "Ranging"),
            top_pattern=top_pattern,
            candidates=all_candidates,
            multi_timeframe_aligned=mtf_aligned,
            active_bias=top_pattern.bias if top_pattern else "Neutral",
            neckline_trigger=top_pattern.neckline if top_pattern else None,
            invalidation_level=top_pattern.floor_or_roof if top_pattern else None,
            trigger_status=trigger_status,
            tactical_playbook=tactical_playbook,
            html_chart_path=HTML_PATH,
        )

        store.pattern_evaluation = evaluation

        # 6. Auto-export interactive chart.html
        if ohlcv_1h:
            export_chart_html(
                ohlcv=ohlcv_1h,
                swings=swings_1h,
                top_p=top_pattern,
                structure=struct,
                trigger_status=trigger_status,
                tactical_playbook=tactical_playbook,
                filepath=HTML_PATH,
            )

        return evaluation
