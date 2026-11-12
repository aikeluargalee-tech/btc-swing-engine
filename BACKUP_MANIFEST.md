# BTC SWING ENGINE — MASTER BACKUP MANIFEST & DISASTER RECOVERY SPECIFICATION

**Project**: Spot BTC-USD Dual-Inventory Bidirectional Swing Engine (DIBSE) & Microstructure Terminal
**Release Label**: `v3.0-DIBSE-G1` (Branch: `main`)
**Repository**: `https://github.com/aikeluargalee-tech/btc-swing-engine.git`
**Archive Package**: `BTC_SWING_ENGINE_COMPLETE_BACKUP_20261112.zip` (paired `.sha256` checksum alongside archive)
**Test Suite Status**: 216/216 Unit Tests Passing (`python -m unittest discover -s tests`)
**Date of Backup**: November 12, 2026
**Author / Pair Programmer**: aikeluargalee-tech & Antigravity (Google DeepMind)

---

## 1. Disaster Recovery & Full Reconstruction Procedure

The complete backup archive (`BTC_SWING_ENGINE_COMPLETE_BACKUP_20261112.zip`) is self-contained and preserves both full `.git/` commit history and gitignored local research caches (`data/cache/binance_4h_2020_present.npz` and `logs/`). To restore from bare metal on Windows or Linux/macOS:

### Option A — Restore from Complete Backup Archive (Full Repo + Git History + Local Cache/Logs)

```powershell
# 1. Extract archive into destination workspace
Expand-Archive -Path .\BTC_SWING_ENGINE_COMPLETE_BACKUP_20261112.zip -DestinationPath .\btc_swing_engine
Set-Location .\btc_swing_engine

# 2. Create fresh Python 3.11+ virtual environment & restore dependencies
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-freeze.txt   # Exact pinned snapshot
# OR: pip install -r requirements.txt  # Semver ranges

# 3. Verify offline historical validator & unit test suite (216 tests)
python -m unittest discover -s tests
python -m analytics.dibse_g1_validator

# 4. Launch Terminal HUD (live, dry-run, or DIBSE Tab [Q]) or Mobile API Cockpit
python main.py --dry-run --tab dibse
python main.py
uvicorn api.mobile_server:app --host 0.0.0.0 --port 8080
```

### Option B — Clone Cleanly from GitHub

```bash
git clone https://github.com/aikeluargalee-tech/btc-swing-engine.git
cd btc_swing_engine
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-freeze.txt
python -m unittest discover -s tests
```

---

## 2. Repository Inventory (Source, Validation, Docs & Deployment)

### Core Architecture & Entrypoints
- **`main.py`** — Async orchestrator (Binance Spot/Perp + Coinbase WS, REST metrics, dry-run / `--tab` CLI routing, Rich Live TUI HUD)
- **`grok_runner.py`** — Standalone Grok quant telemetry runner
- **`core/`** — `models.py` (state dataclasses, enums, execution gate states), `state_store.py` (in-memory deques & rolling buffers)
- **`collectors/`** — `binance_spot_ws.py`, `binance_perp_ws.py`, `coinbase_ws.py`, `rest_metrics.py`, `warmup_loader.py`, `macro_collector.py`
- **`config/`** — `settings.py`, `protocol_context.json`, `trend_pullback_config.yaml`, `tsfm_benchmarks.json`
- **`ui/`** — `terminal_hud.py` (20-desk Rich Live TUI HUD), `mobile_cockpit/`, `mobile_pwa/` (PWA cockpit & retro CRT assets)
- **`api/`** — `mobile_server.py` (FastAPI + WebSocket server for mobile cockpit / PWA)

### Quantitative Analytics & Validation (`analytics/`)
- **`four_gate_engine.py`** — Tab `[Q: DIBSE]` engine (20% active sandbox: 10% Loop A USDT Sleeve + 10% Loop B BTC Sleeve, 80% Core Reserve; 4-Gate closed-4H evaluation + G1 active-sleeve gating)
- **`dibse_g1_validator.py`** — Multi-year offline Binance 4H (`klines`) historical G1 validator, buy-and-hold/SMA/MACD benchmarks, and gate ablation runner
- **`reconciliation_engine.py`** — Upstream B1 vs B2 data integrity audit & fail-closed telemetry reconciliation gate
- **Flagship & Quant Desks**: `spot_swing_engine.py`, `slsp_engine.py`, `slsp_trade_manager.py`, `footprint_engine.py`, `liquidation_reader.py`, `btc_magnet_engine.py`, `strategy_trend_pullback.py`, `grok_quant_engine.py`, `ssrn_research_engine.py`, `master_synthesis.py`, `mm_btc_engine.py`, `volatility_cone_engine.py`, `gartley_engine.py`, `trap_engine.py`, `exhaustion_engine.py`, `regime_matrix.py`, `macro_radar.py`, `ema_strategy_engine.py`, `sweep_retest_fsm.py`, `cvd_engine.py`, `volume_profile.py`, `tell_tale_engine.py`, `signal_detector.py`, `forward_test_tracker.py`, `protocol_v13.py`, `protocol_dossier.py`, `spot_swing_notifier.py`, `ai_packet_exporter.py`, `data_only_reports.py`

### Protocol Specifications & Validation Reports (`docs/`)
- **`docs/DIBSE_PROTOCOL_SPEC.md`** — Locked DIBSE spot-only dual-inventory swing specification (Loop A active / Loop B gated pending G1 recovery pass)
- **`docs/DIBSE_G1_VALIDATION_REPORT.md`** — Multi-year 4H empirical G1 benchmark & ablation validation report
- **Engine & Desk Specs**: `MM_BTC_PROTOCOL_SPEC.md`, `SPOT_SWING_SCREENER_SPEC.md`, `GARTLEY_5STRATEGY_SPEC.md`, `INDUSTRIAL_3_EMA_STRATEGY_SPEC.md`, `PATTERN_TRAP_SFP_SPEC.md`, `TERMINAL_EXHAUSTION_SPEC.md`, `VOLATILITY_CONE_TSFM_SPEC.md`, `MOBILE_APP_HANDOFF.md`, `DEEPSEEK_INTEGRATION_HANDOFF.md`, `btc_swing_engine_manual.html`, `docs/specifications/`

### Verification, Deployment, Scripts & Data
- **`tests/`** — 23 unit test modules (`216` unit tests) including `test_dibse_g1_validator.py`, `test_four_gate_engine.py`, `test_reconciliation_engine.py`, `test_mobile_api.py`, `test_spot_swing.py`, `test_slsp_engine.py`, `test_btc_magnet.py`, `test_strategy_trend_pullback.py`, and core microstructure tests
- **`deploy/`** — `btc-swing-engine.service`, `run_tmux.sh`, `setup_gcp_vm.sh`, `sync_state.ps1`, `TERMIUS_MOBILE_SETUP.md`, `README.md`
- **`scripts/` & `tools/`** — `scripts/generate_nvg_crt_video.py`, `tools/reference_pattern_dashboard/`
- **`data/` (Archive-Included Local Cache)** — `data/cache/binance_4h_2020_present.npz` (cached multi-year 4H OHLCV archive for offline G1 re-runs), `data/ssrn_alpha_registry.json`, `data/protocol_metrics.json`, `data/btc_metrics_latest.json`
- **`logs/` (Archive-Included Runtime Snapshots)** — Latest markdown exports, telemetry snapshots, and JSONL event logs

### Deliberate Archive Exclusions
Excluded to keep the archive portable, clean, and secret-free:
- `.venv/`, `__pycache__/`, `.pytest_cache/` (regenerable Python virtualenv & bytecode)
- Existing `.zip` backup archives (`BTC_SWING_ENGINE_COMPLETE_BACKUP_*.zip`)
- No `.env`, API secret keys, private `.pem`/`.key`, or OAuth credential files exist in the archive or repository.

---

## 3. Terminal HUD Hotkey Reference

| Key | Desk / Action | Primary Function |
|:---:|:---|:---|
| **`P`** | **Structure Desk (`13`)** | Multi-timeframe swing pivots, Macro Radar, Liquidation Gravity & Invalidation Floors |
| **`G`** | **Grok Flow (`15`)** | 00:00 UTC Anchored VWAP, std-dev bands & Grok quant prompt export |
| **`R`** | **SSRN Research (`16`)** | Empirical quant factor domains, model registry & SSRN brief export |
| **`M`** | **BTC Magnet (`17`)** | Liquidation magnet gravity map, targets & 1:3 RRR framing |
| **`A`** / **`K`** | **BTC Strategy (`18`)** | Trend-Pullback Spot Swing strategy desk |
| **`Q`** | **DIBSE / 4-Gate (`19`)** | Dual-Inventory Bidirectional Swing Engine (10% Loop A USDT / 10% Loop B BTC / 80% Core; press `Q` again on tab to copy DIBSE packet) |
| **`F`** | **Footprint Delta (`11`)** | 15m intra-candle order flow delta, absorption clusters & Value Area |
| **`W`** | **Waterfall Desk (`12`)** | Rolling liquidation cascade detector & post-cascade absorption |
| **`0`** | **Spot Swing Screener (`0`)** | 4-step spot screener, Daily Liquidation Magnet & execution checklist |
| **`L`** | **Master Synthesis (`10`)** | 8-Flagship command matrix (`P, G, R, M, A, F, W, 0`) & 4-Domain Readiness |
| **`1`–`4`** | **Tactical / Quant (`1`–`4`)** | Tactical Swing (`1`), Protocol v1.3 (`2`), Macro Radar (`3`), Regime Matrix (`4`) |
| **`5`** / **`S`**, **`6`** / **`V`** | **MM-BTC (`5`) / Vol Cone (`6`)** | Rough-path sensory lenses (`5`/`S`) and 72H Forward Vol Cone (`6`/`V`) |
| **`7`**, **`8`** / **`T`**, **`9`** / **`E`** | **Patterns / SFP / Exhaustion** | Harmonics & Patterns (`7`), SFP Trap Radar (`8`/`T`), TD Exhaustion (`9`/`E`) |
| **`C`** | **AI Audit Export** | Copy complete multi-section AI audit data packet to clipboard & disk |
| **`H`** / **`?`** | **Guide** | Toggle in-app hotkey guide |

---

*This backup manifest describes the clean repository state pushed to `origin/main` and archived in `BTC_SWING_ENGINE_COMPLETE_BACKUP_20261112.zip`.*
