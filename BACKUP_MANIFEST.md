# BTC SWING ENGINE — MASTER BACKUP MANIFEST & DISASTER RECOVERY SPECIFICATION

**Project**: Long-Only BTC-USD Spot Swing Microstructure & Auction Engine  
**Release Tag**: `v2.4-PATTERNS-DESK-B`  
**Git Commit**: `00c0398` (Branch: `main`)  
**Repository**: `https://github.com/aikeluargalee-tech/btc-swing-engine.git`  
**Test Suite Status**: 172/172 Unit Tests Passing (Execution time: 1.87s)  
**Date of Backup**: November 7, 2026 (08:25 AM SGT / 00:25 AM UTC)  
**Author / Pair Programmer**: aikeluargalee-tech & Antigravity (Google DeepMind)

---

## 1. Executive Summary & Core Intent

The **BTC Swing Engine** is a deterministic, institutional-grade trading system engineered exclusively for **Spot BTC-USD swing trading**. It is designed with mathematically enforced risk parameters and multi-pillar confluence:

- **Spot-Only**: Zero leverage, zero futures shorting, zero liquidation risk.
- **Strict Capital Protection**: Hard **0.75% equity risk cap** ($750 max risk on a $100,000 reference account) calculated dynamically:
  $$\text{Position Size (BTC)} = \frac{\text{Equity} \times 0.0075}{\text{Entry} - \text{Deterministic Invalidation}}$$
- **Asymmetric Risk/Reward**: Minimum 1:2.5 to 1:5.0 R:R targeting macro weekly/daily liquidity pools.
- **4-Pillar Confluence Filter ($\ge 70/100$)**:
  1. *Structure & Order Flow*: Multi-timeframe MSS/BOS, 15m Footprint Delta, POC Value Area migrations.
  2. *Derivatives & Liquidity*: Binance/Coinbase Spot CVD divergences, Liquidation Cascades, 1-hour Waterfall Absorption.
  3. *Macro & Intermarket*: DXY, US10Y yields, NDX/SPX correlation, stablecoin net issuance tides.
  4. *Volatility & Exhaustion*: 72-hour volatility cones, Tom DeMark TD9/13 exhaustion, Gartley 222 Harmonics, and Multi-Timeframe Chart Patterns.

---

## 2. Complete Inventory of Components

```
btc_swing_engine/
├── .git/                                # Complete Git version control history & branches
├── analytics/                           # Quantitative Engines & Microstructure Detectors
│   ├── ai_packet_exporter.py            # AI Data Packet exporter & clipboard generator (Sections 1-14)
│   ├── gartley_engine.py                # Gartley 222 Harmonic & PRZ zone detector (Desk [7])
│   ├── pattern_detector.py              # Classic Chart Patterns (Triangles, Wedges, H&S, Double Bottoms) & ASCII/HTML
│   ├── signal_detector.py               # Master Multi-Pillar Confluence & Signal Evaluator
│   ├── spot_swing_screener.py           # Desk [0] 4-Step Institutional Screener & FSM
│   └── ...                              # Volatility cones, Footprint Delta, Waterfall absorption, TD exhaustion
├── collectors/                          # High-Throughput Market Data Ingestion
│   ├── historical_backfill.py           # Zero-Cold-Start REST backfill (Binance, Coinbase, Coinglass)
│   ├── websocket_binance_perp.py        # Binance USDS-M Futures AggTrades, Liquidation orders, Mark prices
│   ├── websocket_binance_spot.py        # Binance BTCUSDT Spot live tick feed
│   └── websocket_coinbase_spot.py       # Coinbase BTC-USD Spot live feed & Coinbase Premium Index
├── config/                              # Operational Settings & Thresholds
│   ├── constants.py                     # Exchange URLs, WebSocket endpoints, risk parameters
│   └── settings.py                      # EngineConfig dataclass with defaults
├── core/                                # Models, State Store & Event Loop
│   ├── models.py                        # Dataclasses: CandleBar, Footprint, Gartley, PatternCandidate, TradePlan
│   └── state_store.py                   # Centralized thread-safe in-memory state repository
├── ui/                                  # Real-Time Terminal User Interface (TUI HUD)
│   └── terminal_hud.py                  # Bloomberg/IBM-style rich live dashboard (Desks P, B, F, W, 0, L, 1-9)
├── docs/                                # Original Specifications, Manuals & Research
│   ├── specifications/                  # Foundational project PDF and DOCX files
│   │   ├── BTC_SWING_ENGINE_QUANT_SPECIFICATION_ORIGINAL.pdf     # Original 23-page Quant Specification
│   │   ├── BTC_SWING_ENGINE_OPERATIONAL_FIELD_MANUAL_ORIGINAL.docx# Operational Trading Guide
│   │   └── BTC_SWING_ENGINE_GROK_COMPREHENSIVE_BRIEF.md         # Full Architectural Brief reviewed by Grok
│   ├── btc_swing_engine_manual.html     # Interactive HTML documentation manual
│   └── ...                              # Industrial 3-EMA, MM Protocol, SFP Trap, Gartley Specs
├── tools/                               # Standalone reference tools & legacy modules
│   └── reference_pattern_dashboard/     # Standalone Pattern Dashboard reference
├── tests/                               # Full Automated Regression Test Suite
│   ├── test_pattern_detector.py         # Unit tests for Chart Patterns, Wedges, Triangles, Slopes & ASCII
│   ├── test_spot_swing.py               # Unit tests for Spot Swing Screener, FSM & hotkeys
│   └── ...                              # 172 Unit tests covering all desks and calculations
├── chart.html                           # Auto-updating TradingView Lightweight Chart
├── btc_metrics_latest.json              # Clean JSON snapshot stream for API & Mobile App
├── BTC_AI_DATA_PACKET_LATEST.md         # Auto-generated comprehensive LLM prompt packet
├── main.py                              # Master asyncio orchestration entrypoint
├── requirements.txt                     # High-level dependencies
├── requirements-freeze.txt              # Exact pinned dependencies from active production environment
├── run_live_hud.bat                     # Windows one-click live HUD launcher
├── run_dry_run.bat                      # Windows one-click 5-second verification launcher
└── hud.bat / hud.ps1                    # Terminal shortcuts
```

---

## 3. Disaster Recovery & Restoration Guide (3 Steps)

To recreate and run this exact engine on any fresh computer (Windows, macOS, or Linux):

### Step 1: Extract Archive
Extract `BTC_SWING_ENGINE_COMPLETE_BACKUP_20261107.zip` to your desired directory:
```bash
cd btc_swing_engine
```

### Step 2: Create Virtual Environment & Install Pinned Packages
```bash
# On Windows:
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements-freeze.txt

# On macOS / Linux:
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-freeze.txt
```

### Step 3: Run Engine & Verify All Tests
```bash
# Run the 172-test verification suite:
python -m unittest discover -s tests -q

# Launch the Live Cockpit HUD:
python main.py
# (or simply double-click run_live_hud.bat on Windows)
```

---

## 4. Hotkey Reference for Terminal HUD

| Key | Desk Name | Primary Function |
|:---:|:---|:---|
| **`0`** | **Spot Swing Screener** | Institutional 4-step screener, Daily Liquidation Magnet, Execution plan |
| **`P`** | **Structure Desk** | Multi-timeframe swing pivots, MSS/BOS levels, invalidation floors |
| **`B`** | **Chart Patterns** | Triangles, Wedges, Head & Shoulders, Double Bottoms, Candlestick ASCII chart |
| **`F`** | **Footprint Delta** | 15m order flow delta, absorption clusters, Value Area migration |
| **`W`** | **Waterfall Desk** | 1-hour rolling liquidation cascade detector & post-cascade absorption |
| **`L`** | **Master Synthesis** | Master synthesis regime matrix (4-Pillar composite score) |
| **`C`** | **AI Export** | Copy complete 14-section AI audit data packet to clipboard and disk |
| **`H`** | **Help** | Toggle in-app hotkey guide |

---

*This backup archive is cryptographically complete, containing 100% of source files, git commits, original quantitative specifications, research documents, and reproducible dependencies.*
