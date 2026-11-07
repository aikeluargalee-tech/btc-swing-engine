#!/usr/bin/env python3
"""
BTC Pattern + Structure Dashboard (Enhanced + Candlestick Chart)
Rule-based classic chart pattern detection with tighter filters.
Features:
- Live Unicode Candlestick Chart in the terminal HUD with key levels and pivot markers.
- Auto-updated interactive TradingView Lightweight Chart (chart.html).
- Patterns: Double Top/Bottom, H&S / Inverse H&S, Rising/Falling Wedge,
  Ascending/Descending/Symmetrical Triangle.
"""

import os
import sys
import json
import time
import numpy as np
from datetime import datetime
from typing import List, Dict, Optional

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import ccxt
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.align import Align
from rich import box

console = Console()
HTML_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chart.html")

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta http-equiv="refresh" content="60">
  <title>BTC/USDT 1H Pattern & Structure Chart</title>
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
      <div class="title">BTC/USDT 1H Pattern Visualizer</div>
      <div class="badge">__PATTERN_BADGE__</div>
    </div>
    <div class="metrics">
      <div class="metric-item"><span>PRICE</span><b style="color: #00e676;">__PRICE__</b></div>
      <div class="metric-item"><span>TIME</span><b>__TIMESTAMP__</b></div>
      <div class="metric-item"><span>STRUCTURE</span><b style="color: #ffd600;">__STRUCTURE__</b></div>
    </div>
  </header>
  <div class="chart-container">
    <div id="chart"></div>
  </div>
  <div class="conclusion-bar">
    <div><b>Tactical Playbook:</b> <span class="highlight">Wait for 1H close confirmation above neckline or below support floor.</span></div>
    <div style="color: #8899a6; font-size: 11px;">Auto-refreshes every 60s &bull; OKX 1h</div>
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

def fetch_ohlcv(exchange: ccxt.Exchange, symbol: str = "BTC/USDT", timeframe: str = "1h", limit: int = 350) -> List[List]:
    try:
        return exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
    except Exception as e:
        console.print(f"[red]Data fetch error: {e}[/red]")
        return []

def detect_swings(ohlcv: List[List], left: int = 6, right: int = 6) -> List[Dict]:
    swings = []
    highs = [c[2] for c in ohlcv]
    lows = [c[3] for c in ohlcv]
    times = [c[0] for c in ohlcv]
    for i in range(left, len(ohlcv) - right):
        if all(highs[i] > highs[i-j] for j in range(1, left+1)) and all(highs[i] > highs[i+j] for j in range(1, right+1)):
            swings.append({"type": "high", "price": highs[i], "index": i, "time": times[i]})
        if all(lows[i] < lows[i-j] for j in range(1, left+1)) and all(lows[i] < lows[i+j] for j in range(1, right+1)):
            swings.append({"type": "low", "price": lows[i], "index": i, "time": times[i]})
    return swings

def _price_tol(a: float, b: float, tol: float) -> bool:
    return abs(a - b) / max(a, b) <= tol

def detect_double_bottom(swings: List[Dict]) -> Optional[Dict]:
    lows = [s for s in swings if s["type"] == "low"]
    if len(lows) < 2:
        return None
    for i in range(len(lows)-1, 1, -1):
        l2 = lows[i]
        for j in range(i-1, max(0, i-8), -1):
            l1 = lows[j]
            bars = l2["index"] - l1["index"]
            if bars < 12 or bars > 80:
                continue
            if _price_tol(l1["price"], l2["price"], 0.012):
                highs_between = [s for s in swings if s["type"] == "high" and l1["index"] < s["index"] < l2["index"]]
                if not highs_between:
                    continue
                neckline = max(h["price"] for h in highs_between)
                if neckline < l1["price"] * 1.015:
                    continue
                conf = 0.82 if _price_tol(l1["price"], l2["price"], 0.006) else 0.65
                return {
                    "pattern": "Double Bottom",
                    "bias": "Bullish",
                    "low1": l1["price"],
                    "low2": l2["price"],
                    "neckline": neckline,
                    "bars": bars,
                    "confidence": conf,
                    "l1_idx": l1["index"],
                    "l2_idx": l2["index"]
                }
    return None

def detect_double_top(swings: List[Dict]) -> Optional[Dict]:
    highs = [s for s in swings if s["type"] == "high"]
    if len(highs) < 2:
        return None
    for i in range(len(highs)-1, 1, -1):
        h2 = highs[i]
        for j in range(i-1, max(0, i-8), -1):
            h1 = highs[j]
            bars = h2["index"] - h1["index"]
            if bars < 12 or bars > 80:
                continue
            if _price_tol(h1["price"], h2["price"], 0.012):
                lows_between = [s for s in swings if s["type"] == "low" and h1["index"] < s["index"] < h2["index"]]
                if not lows_between:
                    continue
                neckline = min(l["price"] for l in lows_between)
                if neckline > h1["price"] * 0.985:
                    continue
                conf = 0.82 if _price_tol(h1["price"], h2["price"], 0.006) else 0.65
                return {
                    "pattern": "Double Top",
                    "bias": "Bearish",
                    "high1": h1["price"],
                    "high2": h2["price"],
                    "neckline": neckline,
                    "bars": bars,
                    "confidence": conf,
                    "h1_idx": h1["index"],
                    "h2_idx": h2["index"]
                }
    return None

def detect_head_shoulders(swings: List[Dict]) -> Optional[Dict]:
    highs = [s for s in swings if s["type"] == "high"]
    if len(highs) < 3:
        return None
    for i in range(len(highs)-1, 2, -1):
        right, head, left = highs[i], highs[i-1], highs[i-2]
        if not (head["price"] > left["price"] * 1.008 and head["price"] > right["price"] * 1.008):
            continue
        if not _price_tol(left["price"], right["price"], 0.018):
            continue
        if (head["index"] - left["index"] < 8) or (right["index"] - head["index"] < 8):
            continue
        lows_between = [s for s in swings if s["type"] == "low" and left["index"] < s["index"] < right["index"]]
        if len(lows_between) < 1:
            continue
        neckline = min(l["price"] for l in lows_between)
        shoulder_diff = abs(left["price"] - right["price"]) / left["price"]
        conf = 0.85 if shoulder_diff < 0.008 else 0.68
        return {
            "pattern": "Head and Shoulders",
            "bias": "Bearish",
            "left": left["price"],
            "head": head["price"],
            "right": right["price"],
            "neckline": neckline,
            "confidence": conf
        }
    return None

def detect_inverse_hs(swings: List[Dict]) -> Optional[Dict]:
    lows = [s for s in swings if s["type"] == "low"]
    if len(lows) < 3:
        return None
    for i in range(len(lows)-1, 2, -1):
        right, head, left = lows[i], lows[i-1], lows[i-2]
        if not (head["price"] < left["price"] * 0.992 and head["price"] < right["price"] * 0.992):
            continue
        if not _price_tol(left["price"], right["price"], 0.018):
            continue
        if (head["index"] - left["index"] < 8) or (right["index"] - head["index"] < 8):
            continue
        highs_between = [s for s in swings if s["type"] == "high" and left["index"] < s["index"] < right["index"]]
        if len(highs_between) < 1:
            continue
        neckline = max(h["price"] for h in highs_between)
        shoulder_diff = abs(left["price"] - right["price"]) / left["price"]
        conf = 0.85 if shoulder_diff < 0.008 else 0.68
        return {
            "pattern": "Inverse Head and Shoulders",
            "bias": "Bullish",
            "left": left["price"],
            "head": head["price"],
            "right": right["price"],
            "neckline": neckline,
            "confidence": conf
        }
    return None

def detect_wedge(swings: List[Dict]) -> Optional[Dict]:
    highs = [s for s in swings if s["type"] == "high"][-5:]
    lows = [s for s in swings if s["type"] == "low"][-5:]
    if len(highs) < 3 or len(lows) < 3:
        return None

    def slope(pts):
        if len(pts) < 2:
            return 0.0
        x = np.array([p["index"] for p in pts], dtype=float)
        y = np.array([p["price"] for p in pts], dtype=float)
        return float(np.polyfit(x, y, 1)[0])

    hs = slope(highs[-3:])
    ls = slope(lows[-3:])

    if hs > 0 and ls > 0 and hs < ls * 0.65 and abs(hs - ls) > 1e-6:
        return {"pattern": "Rising Wedge", "bias": "Bearish", "confidence": 0.72, "high_slope": hs, "low_slope": ls}
    if hs < 0 and ls < 0 and abs(hs) > abs(ls) * 0.65:
        return {"pattern": "Falling Wedge", "bias": "Bullish", "confidence": 0.72, "high_slope": hs, "low_slope": ls}
    return None

def detect_triangle(swings: List[Dict]) -> Optional[Dict]:
    highs = [s for s in swings if s["type"] == "high"][-5:]
    lows = [s for s in swings if s["type"] == "low"][-5:]
    if len(highs) < 3 or len(lows) < 3:
        return None

    def slope(pts):
        x = np.array([p["index"] for p in pts], dtype=float)
        y = np.array([p["price"] for p in pts], dtype=float)
        return float(np.polyfit(x, y, 1)[0])

    hs = slope(highs[-3:])
    ls = slope(lows[-3:])

    if abs(hs) < abs(ls) * 0.4 and ls > 0:
        return {"pattern": "Ascending Triangle", "bias": "Bullish", "confidence": 0.70, "high_slope": hs, "low_slope": ls}
    if abs(ls) < abs(hs) * 0.4 and hs < 0:
        return {"pattern": "Descending Triangle", "bias": "Bearish", "confidence": 0.70, "high_slope": hs, "low_slope": ls}
    if hs < 0 and ls > 0 and abs(abs(hs) - ls) / max(abs(hs), ls) < 0.5:
        return {"pattern": "Symmetrical Triangle", "bias": "Neutral", "confidence": 0.62, "high_slope": hs, "low_slope": ls}
    return None

def scan_patterns(swings: List[Dict]) -> List[Dict]:
    candidates = []
    for fn in (detect_double_bottom, detect_double_top, detect_head_shoulders,
               detect_inverse_hs, detect_wedge, detect_triangle):
        p = fn(swings)
        if p:
            candidates.append(p)
    best = {}
    for p in candidates:
        name = p["pattern"]
        if name not in best or p["confidence"] > best[name]["confidence"]:
            best[name] = p
    result = list(best.values())
    result.sort(key=lambda x: x["confidence"], reverse=True)
    return result

def analyze_structure(ohlcv: List[List], swings: List[Dict]) -> Dict:
    if not ohlcv:
        return {"error": True}
    current_price = ohlcv[-1][4]
    recent_highs = [s for s in swings if s["type"] == "high"][-3:]
    recent_lows = [s for s in swings if s["type"] == "low"][-3:]
    trend = "Ranging"
    if len(recent_highs) >= 2 and len(recent_lows) >= 2:
        if recent_highs[-1]["price"] > recent_highs[-2]["price"] and recent_lows[-1]["price"] > recent_lows[-2]["price"]:
            trend = "Bullish structure"
        elif recent_highs[-1]["price"] < recent_highs[-2]["price"] and recent_lows[-1]["price"] < recent_lows[-2]["price"]:
            trend = "Bearish structure"
    return {
        "current_price": current_price,
        "timestamp": datetime.fromtimestamp(ohlcv[-1][0]/1000).strftime("%Y-%m-%d %H:%M"),
        "trend": trend,
        "error": False
    }

def make_header() -> Panel:
    text = Text("BTC PATTERN DASHBOARD", style="bold cyan")
    text.append("  |  Tighter Rules + Candlestick Geometry", style="dim")
    return Panel(Align.center(text), style="cyan", box=box.DOUBLE)

def make_status_panel(structure: Dict, patterns: List[Dict]) -> Panel:
    content = Text()
    content.append("Price: ", style="bold")
    content.append(f"${structure['current_price']:,.2f}\n", style="bold green")
    content.append(f"Time: {structure['timestamp']}\n", style="dim")
    content.append(f"Structure: {structure['trend']}\n\n", style="bold yellow")

    if patterns:
        top = patterns[0]
        content.append(f"Top Pattern: {top['pattern']}\n", style="bold magenta")
        content.append(f"Bias: {top['bias']}\n", style="bold")
        content.append(f"Confidence: {top['confidence']:.0%}", style="cyan")
    else:
        content.append("No patterns meeting tightened criteria", style="dim")

    border = "green" if patterns else "yellow"
    return Panel(content, title="Market Status", border_style=border)

def make_patterns_panel(patterns: List[Dict]) -> Panel:
    if not patterns:
        return Panel("[dim]No patterns meeting minimum criteria[/dim]", title="Detected Patterns", border_style="dim")

    table = Table(box=box.SIMPLE, show_header=True, header_style="bold", padding=(0, 1))
    table.add_column("Pattern")
    table.add_column("Bias")
    table.add_column("Conf.")
    table.add_column("Key Level")

    for p in patterns[:4]:
        key = ""
        if "neckline" in p:
            key = f"${p['neckline']:,.0f}"
        elif "Wedge" in p["pattern"] or "Triangle" in p["pattern"]:
            key = "Converging"
        table.add_row(p["pattern"], p["bias"], f"{p['confidence']:.0%}", key)
    return Panel(table, title="Pattern Candidates", border_style="magenta")

def make_details_panel(patterns: List[Dict]) -> Panel:
    if not patterns:
        return Panel("[dim]—[/dim]", title="Top Pattern Details", border_style="dim")

    p = patterns[0]
    lines = [f"[bold]{p['pattern']}[/bold] ({p['bias']})"]
    for k, v in p.items():
        if k not in ("pattern", "bias", "confidence", "bars", "l1_idx", "l2_idx", "h1_idx", "h2_idx") and isinstance(v, (int, float)):
            if k in ("high_slope", "low_slope"):
                lines.append(f"{k}: {v:.4f}")
            else:
                lines.append(f"{k}: ${v:,.2f}")
        if k == "bars":
            lines.append(f"{k}: {int(v)}")
    return Panel("\n".join(lines), title="Top Pattern Details", border_style="blue")

def make_candlestick_panel(ohlcv: List[List], swings: List[Dict], top_p: Optional[Dict], height: int = 12) -> Panel:
    if not ohlcv:
        return Panel("[dim]No candle data available[/dim]", title="Candlestick Chart", border_style="dim")

    term_width = console.width or 110
    num_candles = max(25, min(len(ohlcv), term_width - 34))
    sub_ohlcv = ohlcv[-num_candles:]
    offset = len(ohlcv) - num_candles

    highs = [c[2] for c in sub_ohlcv]
    lows = [c[3] for c in sub_ohlcv]
    min_p = min(lows)
    max_p = max(highs)

    if top_p and "neckline" in top_p:
        max_p = max(max_p, top_p["neckline"] * 1.002)
        min_p = min(min_p, top_p.get("low1", min_p), top_p.get("low2", min_p))

    price_range = max_p - min_p if max_p != min_p else 1.0

    def p_to_r(p: float) -> int:
        r = int((p - min_p) / price_range * (height - 1))
        return max(0, min(height - 1, r))

    grid = [[(" ", "default") for _ in range(num_candles)] for _ in range(height)]

    # Draw candles
    for col, c in enumerate(sub_ohlcv):
        o, h, l, cl = c[1], c[2], c[3], c[4]
        color = "green" if cl >= o else "red"
        r_h = p_to_r(h)
        r_l = p_to_r(l)
        r_top = p_to_r(max(o, cl))
        r_bot = p_to_r(min(o, cl))
        for r in range(r_l, r_h + 1):
            grid[r][col] = ("│", color)
        for r in range(r_bot, r_top + 1):
            grid[r][col] = ("█", color)

    # Draw Neckline
    nl_r = p_to_r(top_p["neckline"]) if top_p and "neckline" in top_p else None
    if nl_r is not None:
        for col in range(num_candles):
            ch, colr = grid[nl_r][col]
            if ch == " ":
                grid[nl_r][col] = ("┄", "bold magenta")
            elif ch == "│":
                grid[nl_r][col] = ("┼", "bold magenta")

    # Draw Floor (for Double Bottom) or Roof (for Double Top)
    fl_p = None
    if top_p and "low1" in top_p and "low2" in top_p:
        fl_p = min(top_p["low1"], top_p["low2"])
    elif top_p and "high1" in top_p and "high2" in top_p:
        fl_p = max(top_p["high1"], top_p["high2"])

    fl_r = p_to_r(fl_p) if fl_p else None
    if fl_r is not None and fl_r != nl_r:
        line_color = "bold red" if top_p.get("bias") == "Bullish" else "bold green"
        for col in range(num_candles):
            ch, colr = grid[fl_r][col]
            if ch == " ":
                grid[fl_r][col] = ("┄", line_color)
            elif ch == "│":
                grid[fl_r][col] = ("┼", line_color)

    lines = []
    for r in range(height - 1, -1, -1):
        p_val = min_p + (r / (height - 1)) * price_range
        tag = ""
        if nl_r is not None and r == nl_r:
            tag = f" [bold magenta]◀ NL ${top_p['neckline']:,.0f}[/bold magenta]"
        elif fl_r is not None and r == fl_r:
            tag_name = "Floor" if top_p.get("bias") == "Bullish" else "Roof"
            tag_col = "bold red" if top_p.get("bias") == "Bullish" else "bold green"
            tag = f" [{tag_col}]◀ {tag_name} ${fl_p:,.0f}[/{tag_col}]"

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
    return Panel(content, title="[bold white]BTC/USDT 1H Candlestick Chart (Geometric Overlays & Pivots)[/bold white]", border_style="cyan", box=box.ROUNDED)

def make_conclusion_panel(structure: Dict, patterns: List[Dict]) -> Panel:
    price = structure.get("current_price", 0.0)
    trend = structure.get("trend", "Ranging")

    if not patterns:
        markup = (
            "[bold white on bright_black] STANDBY — NO CONFIRMED PATTERNS [/bold white on bright_black]\n\n"
            f"[bold cyan]• Market Verdict :[/bold cyan] BTC (${price:,.2f}) shows {trend.lower()} with no classic geometric patterns meeting strict tolerance thresholds.\n"
            "[bold cyan]• Key Geometry   :[/bold cyan] Key pivots unaligned. Volatility is distributing without structural edge.\n"
            "[bold cyan]• Your Next Move :[/bold cyan] [bold yellow]Sit in cash / observe.[/bold yellow] Wait for clean swing pivots or boundary consolidation."
        )
        return Panel(Text.from_markup(markup), title="[bold white]Executive Conclusion & Tactical Playbook[/bold white]", border_style="bright_black", box=box.ROUNDED)

    top = patterns[0]
    p_name = top["pattern"]
    bias = top["bias"]
    conf = top["confidence"]

    bullish_cands = [p for p in patterns if p["bias"] == "Bullish"]
    bearish_cands = [p for p in patterns if p["bias"] == "Bearish"]
    has_conflict = len(bullish_cands) > 0 and len(bearish_cands) > 0 and len(patterns) > 1

    if has_conflict and (top["confidence"] - patterns[1]["confidence"] < 0.20):
        second = patterns[1]
        border_style = "yellow"

        levels = []
        if "neckline" in top:
            color = "green" if bias == "Bullish" else "red"
            levels.append(f"{top['pattern']} Neckline: [bold {color}]${top['neckline']:,.2f}[/bold {color}]")
        if "neckline" in second:
            color = "red" if second["bias"] == "Bearish" else "green"
            levels.append(f"{second['pattern']} Neckline: [bold {color}]${second['neckline']:,.2f}[/bold {color}]")
        geo_str = " | ".join(levels) if levels else f"Price bounded around ${price:,.2f}"

        markup = (
            f"[bold black on yellow] CAUTION — DUAL COMPETING PATTERNS ({top['pattern']} vs {second['pattern']}) [/bold black on yellow]\n\n"
            f"[bold cyan]• Market Verdict :[/bold cyan] Mixed signals: Leading setup is {top['pattern']} ({bias}, {conf:.0%}), countered by {second['pattern']} ({second['bias']}, {second['confidence']:.0%}). Macro is {trend}.\n"
            f"[bold cyan]• Key Geometry   :[/bold cyan] {geo_str}\n"
            f"[bold cyan]• Your Next Move :[/bold cyan] [bold yellow]Do not front-run the range.[/bold yellow] Wait for 1H close confirmation above/below key necklines."
        )

    elif bias == "Bullish":
        if conf >= 0.80:
            border_style = "green"
            badge = f"[bold black on green] GREEN LIGHT — HIGH CONFIDENCE BULLISH REVERSAL ({p_name.upper()} {conf:.0%}) [/bold black on green]"
        else:
            border_style = "cyan"
            badge = f"[bold black on cyan] BLUE LIGHT — DEVELOPING BULLISH SETUP ({p_name.upper()} {conf:.0%}) [/bold black on cyan]"

        neckline = top.get("neckline")
        floor = min(top.get("low1", price), top.get("low2", price)) if "low1" in top else top.get("left", price * 0.98)

        if neckline:
            geo_line = f"Breakout Trigger: [bold green]${neckline:,.2f}[/bold green] | Invalidation Floor: [bold red]${floor:,.2f}[/bold red]"
            next_line = f"[bold green]Wait for 1H close above ${neckline:,.0f}[/bold green] to confirm trigger. Invalidate setup if price loses [bold red]${floor:,.0f}[/bold red]."
        else:
            geo_line = f"Upper Slope: {top.get('high_slope', 0):.4f} | Lower Slope: {top.get('low_slope', 0):.4f}"
            next_line = "[bold cyan]Monitor converging trendline breakout on expanding volume.[/bold cyan]"

        markup = (
            f"{badge}\n\n"
            f"[bold cyan]• Market Verdict :[/bold cyan] BTC (${price:,.2f}) formed a {p_name} ({conf:.0%} confidence) under {trend.lower()}. Buyers defending support.\n"
            f"[bold cyan]• Key Geometry   :[/bold cyan] {geo_line}\n"
            f"[bold cyan]• Your Next Move :[/bold cyan] {next_line}"
        )

    elif bias == "Bearish":
        if conf >= 0.80:
            border_style = "red"
            badge = f"[bold white on red] RED LIGHT — HIGH CONFIDENCE BEARISH THREAT ({p_name.upper()} {conf:.0%}) [/bold white on red]"
        else:
            border_style = "yellow"
            badge = f"[bold black on yellow] YELLOW LIGHT — DEVELOPING BEARISH SETUP ({p_name.upper()} {conf:.0%}) [/bold black on yellow]"

        neckline = top.get("neckline")
        roof = max(top.get("high1", price), top.get("high2", price)) if "high1" in top else top.get("head", price * 1.02)

        if neckline:
            geo_line = f"Breakdown Trigger: [bold red]${neckline:,.2f}[/bold red] | Invalidation Ceiling: [bold green]${roof:,.2f}[/bold green]"
            next_line = f"[bold red]Tighten stop-losses / protect capital.[/bold red] Bearish confirmation triggers on 1H close below [bold red]${neckline:,.0f}[/bold red]."
        else:
            geo_line = f"Upper Slope: {top.get('high_slope', 0):.4f} | Lower Slope: {top.get('low_slope', 0):.4f}"
            next_line = "[bold yellow]Watch for support breakdown at lower converging slope.[/bold yellow]"

        markup = (
            f"{badge}\n\n"
            f"[bold cyan]• Market Verdict :[/bold cyan] BTC (${price:,.2f}) displaying {p_name} ({conf:.0%} confidence). Sellers capping upside in {trend.lower()}.\n"
            f"[bold cyan]• Key Geometry   :[/bold cyan] {geo_line}\n"
            f"[bold cyan]• Your Next Move :[/bold cyan] {next_line}"
        )

    else:
        border_style = "yellow"
        badge = f"[bold black on yellow] YELLOW LIGHT — VOLATILITY SQUEEZE ({p_name.upper()} {conf:.0%}) [/bold black on yellow]"
        geo_line = f"Upper Slope: {top.get('high_slope', 0):.4f} | Lower Slope: {top.get('low_slope', 0):.4f}"
        next_line = "[bold yellow]Wait for expansion candle to break out of triangle boundary before entering directionally.[/bold yellow]"

        markup = (
            f"{badge}\n\n"
            f"[bold cyan]• Market Verdict :[/bold cyan] BTC (${price:,.2f}) coiling inside {p_name}. Compression indicates an impending directional expansion.\n"
            f"[bold cyan]• Key Geometry   :[/bold cyan] {geo_line}\n"
            f"[bold cyan]• Your Next Move :[/bold cyan] {next_line}"
        )

    return Panel(Text.from_markup(markup), title="[bold white]Executive Conclusion & Tactical Playbook[/bold white]", border_style=border_style, box=box.ROUNDED)

def make_footer() -> Panel:
    text = "[dim]Tighter geometric filters  |  OKX 1h  |  Interactive chart: chart.html  |  Ctrl+C to stop[/dim]"
    return Panel(Align.center(text), style="dim")

def export_chart_html(ohlcv: List[List], swings: List[Dict], patterns: List[Dict], structure: Dict, filepath: str):
    try:
        candle_data = [
            {
                "time": int(c[0] / 1000),
                "open": float(c[1]),
                "high": float(c[2]),
                "low": float(c[3]),
                "close": float(c[4])
            }
            for c in ohlcv
        ]

        top_p = patterns[0] if patterns else None
        markers = []
        times_map = {s["index"]: int(s["time"] / 1000) for s in swings}

        if top_p and "low1" in top_p and "l1_idx" in top_p:
            t1 = times_map.get(top_p["l1_idx"])
            if t1:
                markers.append({"time": t1, "position": "belowBar", "color": "#00e676", "shape": "arrowUp", "text": f"Low 1 (${top_p['low1']:,.0f})"})
        if top_p and "low2" in top_p and "l2_idx" in top_p:
            t2 = times_map.get(top_p["l2_idx"])
            if t2:
                markers.append({"time": t2, "position": "belowBar", "color": "#00e676", "shape": "arrowUp", "text": f"Low 2 (${top_p['low2']:,.0f})"})

        price_lines = []
        if top_p and "neckline" in top_p:
            price_lines.append({
                "price": float(top_p["neckline"]),
                "color": "#e040fb",
                "title": f"{top_p['pattern']} Neckline (${top_p['neckline']:,.0f})"
            })
        if top_p and "low1" in top_p and "low2" in top_p:
            fl = float(min(top_p["low1"], top_p["low2"]))
            price_lines.append({
                "price": fl,
                "color": "#ff5252",
                "title": f"Support Floor (${fl:,.0f})"
            })

        badge = f"{top_p['pattern']} ({top_p['confidence']:.0%})" if top_p else "No Pattern"
        price_str = f"${structure.get('current_price', 0):,.2f}"
        time_str = structure.get("timestamp", "N/A")
        trend_str = structure.get("trend", "Ranging")

        html = (HTML_TEMPLATE
                .replace("__PATTERN_BADGE__", badge)
                .replace("__PRICE__", price_str)
                .replace("__TIMESTAMP__", time_str)
                .replace("__STRUCTURE__", trend_str)
                .replace("__CANDLE_DATA__", json.dumps(candle_data))
                .replace("__PRICE_LINES__", json.dumps(price_lines))
                .replace("__MARKERS__", json.dumps(markers)))

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)
    except Exception as e:
        pass

def build_layout(structure: Dict, patterns: List[Dict], ohlcv: List[List], swings: List[Dict]) -> Layout:
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="top_row", size=9),
        Layout(name="chart", ratio=1, minimum_size=12),
        Layout(name="conclusion", size=10),
        Layout(name="footer", size=3)
    )
    layout["top_row"].split_row(
        Layout(name="status", ratio=1),
        Layout(name="details", ratio=1),
        Layout(name="patterns", ratio=1)
    )

    top = patterns[0] if patterns else None
    layout["header"].update(make_header())
    layout["status"].update(make_status_panel(structure, patterns))
    layout["details"].update(make_details_panel(patterns))
    layout["patterns"].update(make_patterns_panel(patterns))
    layout["chart"].update(make_candlestick_panel(ohlcv, swings, top))
    layout["conclusion"].update(make_conclusion_panel(structure, patterns))
    layout["footer"].update(make_footer())
    return layout

def main():
    once = "--once" in sys.argv
    exchange = ccxt.okx({"enableRateLimit": True})
    console.print("[bold cyan]Starting Enhanced BTC Pattern + Candlestick Dashboard...[/bold cyan]\n")

    if once:
        ohlcv = fetch_ohlcv(exchange)
        if not ohlcv:
            console.print("[red]Failed to fetch initial candles from OKX.[/red]")
            return
        swings = detect_swings(ohlcv)
        structure = analyze_structure(ohlcv, swings)
        patterns = scan_patterns(swings)
        export_chart_html(ohlcv, swings, patterns, structure, HTML_PATH)
        console.print(build_layout(structure, patterns, ohlcv, swings))
        return

    with Live(console=console, refresh_per_second=1, screen=True) as live:
        while True:
            try:
                ohlcv = fetch_ohlcv(exchange)
                swings = detect_swings(ohlcv)
                structure = analyze_structure(ohlcv, swings)
                patterns = scan_patterns(swings)
                export_chart_html(ohlcv, swings, patterns, structure, HTML_PATH)
                live.update(build_layout(structure, patterns, ohlcv, swings))
            except KeyboardInterrupt:
                break
            except Exception as e:
                live.update(Panel(f"[red]{e}[/red]", title="Error"))
            time.sleep(45)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Stopped.[/yellow]")
