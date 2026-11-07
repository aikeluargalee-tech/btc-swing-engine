# BTC SWING MOBILE APP (SETUP B) — MASTER HANDOFF BRIEFING

**Source Session**: `3.3 BTC Swing Screener Technical Discussion` (`b724e489-311f-48ff-ac10-aae884c7d07b`)  
**Target Session**: `3.4 BTC Swing Mobile App` (`d7e346aa-2266-4255-a2c5-b348b70c3fd6`)  
**Project Path**: `C:\Users\aikel\.gemini\antigravity\scratch\btc_swing_engine`  
**Current Commit**: `be86f74` (`main`)  
**Test Suite**: 172 / 172 unit tests passing  
**Date**: November 7, 2026  

---

## 1. Current State & Deliverables Completed

1. **Spot-Only Quant Core**:
   - Zero leverage, zero shorting, mathematically capped 0.75% equity risk ($750 max risk on a $100k account).
   - All 4 confluence pillars active (Structure & Order Flow, Derivatives & Liquidity, Macro & Intermarket, Volatility & Exhaustion).
   - 172 unit tests running green in 1.87 seconds.
2. **Classic Chart Patterns (Desk [B])**:
   - Integrated native pattern detector (Triangles, Wedges, Head & Shoulders, Double Bottoms, ASCII & HTML candlestick charts).
   - Hotkey `B` added and verified.
3. **Master Backup**:
   - Complete project packaged and verified: `BTC_SWING_ENGINE_COMPLETE_BACKUP_20261107.zip` (7.91 MB, 464 files) on Desktop and GitHub.
4. **Data Stream Ready**:
   - `btc_metrics_latest.json` is exported on every tick, providing a clean structured JSON snapshot for the mobile frontend.

---

## 2. Grok Review & Setup B Architectural Mandates

Following independent quantitative and UX critique by Grok, the mobile app (Setup B) must adhere to these strict rules:

### A. Screen 1: Primary Mobile Cockpit Dashboard
- **Hero Confluence Gauge**: Score 0–100 (e.g. `82/100 HIGH CONFLUENCE`) with current regime (`ACCUMULATION`, `BALANCED`, `FROZEN_CASH`, etc.).
- **Deterministic Trade Plan Card** (Only visible when Confluence $\ge 70$):
  - Entry Range
  - Invalidation Floor ($) and % distance
  - Take-Profit 1 (1:2.5) & Take-Profit 2 (1:5.0)
  - Max Risk ($750 / 0.75%)
  - Position Size in BTC: $\frac{\text{Risk}}{\text{Entry} - \text{Invalidation}}$
- **4-Pillar Visual Health Bars** (Tap to expand plain English accordion):
  1. Structure & Order Flow
  2. Derivatives & Liquidity
  3. Macro & Intermarket
  4. Volatility & Exhaustion
- **One-Tap Action Buttons**:
  - `[Copy AI Audit Packet]` (Copies ready-to-paste markdown to phone clipboard for Grok / Claude).

### B. Strict Exclusions (Do NOT Include on Mobile)
- **NO** dense terminal text grids or raw footprint order book ladders.
- **NO** retro terminal green-on-black monospace styling for the primary view (must look like a modern, clean financial app).
- **NO** complex multi-pane chart overlays.
- **NO** leverage, margin, or shorting toggles (Spot BTC only).
- **NO** unthrottled 50 Hz WebSockets (throttle mobile stream to 1 Hz to save phone battery).

---

## 3. Recommended Implementation Architecture

Given the user's Windows environment (Python 3.11 active; Flutter/Node.js not installed):

1. **Backend Server (`api/mobile_server.py`)**:
   - Uses `fastapi` and `uvicorn`.
   - Serves `GET /api/v1/metrics/latest` (instant snapshot).
   - Serves WebSocket `/ws/metrics` (throttled at 1 Hz).
   - Serves the static mobile PWA frontend.
2. **Frontend Client (`ui/mobile_pwa/`)**:
   - Standalone modern Responsive Mobile Web App (PWA).
   - Touch-optimized, beautiful dark mode, animated SVG gauge, accordion cards.
   - When opened in Safari or Chrome on the phone, the user taps **"Add to Home Screen"** to install it as an app icon with full-screen native feel.
   - Fully ready to be wrapped in Flutter or Capacitor if native app-store binary is desired later.
