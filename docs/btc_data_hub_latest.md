# TAB [D: DATA HUB] | CONSOLIDATED DATA-ONLY TELEMETRY REPORT
**Retrieval Time (UTC):** `2026-11-15 00:44:58 UTC`  |  **Retrieval Time (MYT):** `2026-11-15 08:44:58 MYT (UTC+8)`
**Spot Price (BTCUSDT):** `$63,807.68`  |  **Coverage:** `OK=61/66 | UNAVAILABLE=3 | STALE=1 | PROXY/STATIC=1`
**24H Range:** `$63,320.00 - $68,410.01`  |  **Returns (24H / 7D / 30D):** `-6.64% / -14.75% / -21.82%`
**Archive (SQLite):** `4 closed-4H snapshots (Last: 2026-11-15 00:00:00 UTC)`

## 1. PRICE, TREND & MARKET STRUCTURE
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| Binance Spot / Perp ($) | `$63,807.68 / $63,782.00` | `All Tabs` | `OK` |
| Coinbase Spot ($) | `$63,802.64` | `1,11,15,17` | `OK` |
| 1D SMA 200 / Slope | `$73,030.62 (-0.24%)` | `0,2,3,11,15,18` | `OK` |
| 1D SMA 50 / EMA 50 | `$80,225.41 / $77,114.24` | `0,2,4,15,18,20` | `OK` |
| 1D EMA 21 / 1W EMA 50 | `$74,089.79 / $78,205.27` | `3,18` | `OK` |
| 4H EMA 50 / EMA 200 | `$72,054.75 / $77,177.43` | `7,13,18,20` | `OK` |
| Grok EMA 9/21 & 1H SMA200 | `9:$64,721.18 · 21:$65,815.89 · 1H:$72,914.88` | `5,15` | `OK` |
| Daily / Weekly VWAP (Z) | `D:$65,838.47 (-1.57σ) | W:$70,913.16` | `4,11,15` | `OK` |
| RSI(14) 1D / 4H & 4H ROC12 | `1D:19.3 · 4H:15.9 · ROC:-10.23%` | `3,7,20` | `OK` |
| ADX(14) 1D/4H & ATR(14) | `ADX 1D:31.3 4H:62.5 | ATR:$2,599.11/$1,305.45/$762.95` | `0,1,2,8,13,18,20` | `OK` |
| Macro 30D VAH / POC / VAL | `$83,369.56 / $81,571.39 / $74,918.17` | `1,3,6,11,19` | `OK` |
| Structure (L20/H20, PW, Asia) | `4H:$66,456.00-$81,971.00 | PW:$73,510.00-$81,196.01 | Asia:$63,567.61-$64,574.27` | `0,8,11,19` | `OK` |

## 2. ORDER FLOW, FOOTPRINT & LIQUIDITY
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| Spot/Perp CVD (15m / 1h) | `15m:-8.0/+81.7 | 1h:+406.8/+232.4 BTC` | `1,8,15` | `OK` |
| Spot/Perp CVD (4h / 24h) | `4h:+368.9/-2305.3 | 24h:-2277.2/-8040.4 BTC` | `0,1,15,16,17` | `OK` |
| Session / UTC-Day CVD | `Sess S:+0.0 P:+0.0 | Day S:+76.5 P:-106.0` | `REST 15m` | `OK` |
| 24H Z-Scores (z_S / z_F / D) | `z_S:-2.05 · z_F:-2.03 · D:-0.02` | `1,19` | `OK` |
| 15m Footprint Delta / Stack | `Δ:-8.0 BTC (Prev:-31.2) · Stacks:0` | `1,11` | `OK` |
| Coinbase Premium ($ / % / Z) | `-5.0$ (-0.008%, Z=+4.47)` | `1,11,15` | `OK` |
| Cross-Exch 24H Spot Vol (BN/CB) | `BN:33,112 · CB:16,611 · Tot:49,723 BTC` | `1,11,Macro` | `OK` |
| L2 Depth ±1%/±2%, OBI & Spread | `1%:1.33x · 2%:2.73x · Spr:0.00bps · OBI:+14.1%` | `16,Macro` | `OK` |
| Tactical 7D / Session 24H VP | `7D:$76,146.33/$73,785.00/$68,633.00 | 24H:$67,604.09/$67,264.76/$64,719.75` | `1,11` | `OK` |
| VA Pos% & Dist to VAL | `-131.5% | -14.83% (-14.56 ATR)` | `1` | `OK` |
| SLSP Support / Resistance | `Sup:$63,349.44 | Res:$64,742.09` | `13` | `OK` |

## 3. DERIVATIVES, OPTIONS & LIQUIDATIONS
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| BN Open Interest (BTC / USD) | `98,048 BTC ($6.24B)` | `0,1,4,15,17` | `OK` |
| Cross-Exch Perp OI & Funding | `167,816 BTC ($10.69B) · F:+0.0036% [BN+BYB+OKX]` | `Macro,15` | `OK` |
| OI Δ% (15m/1h/4h/24h) & Quad | `-0.00%/-0.46%/+0.88%/+0.25% | SHORT_COVERING_BOUNCE (Price Up / OI Down)` | `1,4,8,11,12,15,17` | `OK` |
| Funding 8H% / Ann% / P90 | `+0.0060% (+6.6%/yr) · P90:0.7%` | `0,4,9,11,15,16,19,20` | `OK` |
| Perp Basis ($ / Ann %) | `-25.7$ (-0.040% | Carry:+6.10%/yr)` | `1,4` | `OK` |
| 5m Taker L/S & Top/Glb Acct | `5m:1.361 (Δ:+29.8) | Top:1.80(64L) · Glb:2.74` | `1,2,15,16` | `OK` |
| Options OI & Put/Call (Deribit) | `P/C:0.743 · TotOI:365,469 BTC` | `Macro,19` | `OK` |
| Options IV Term & Skew (Deribit) | `F:50.7% · B:42.7% · 25dSk:+11.7%` | `Macro,6,19` | `OK` |
| Vol: DVOL, RV20, GK & BBW% | `DVOL:48.7 · RV20:47.8% · GK:63.8% · BBW:83% · Sk20:-0.44` | `0,4,6,16,19` | `OK` |
| Upper / Lower Liq Magnet | `Up:$76,334.44 | Dn:$62,659.14` | `0,2,13,17` | `OK` |
| Magnet Ratios & LSCE | `Imm:1.81x · Ladder:1.79x · Pull:0.55x · LSCE:UNTESTED` | `13,17` | `OK` |
| Liquidations (1H / 24H) & Flush | `DATA UNAVAILABLE` | `0,8,12,13` | `UNAVAILABLE` |

## 4. ON-CHAIN, ETF & STABLECOIN FLOWS
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| MVRV Ratio (On-Chain / Proxy) | `1.267 [CoinMetrics 2026-11-13]` | `Macro,16` | `OK` |
| On-Chain SOPR / aSOPR | `DATA UNAVAILABLE` | `16` | `UNAVAILABLE` |
| Exchange Netflow 24H (CM) | `Net:-2,129.5 BTC (-$145.0M) | In:26,738 Out:28,868` | `Macro,16` | `OK` |
| BTC Exchange Reserves (CM) | `2,723,962 BTC (2026-11-13)` | `Macro,16` | `OK` |
| Stablecoins USDT+USDC Supply | `$244.61B (USDT:$175.35B · USDC:$69.26B)` | `Macro` | `OK` |
| Stablecoin Net Issuance (7D/30D) | `7D:-2.86B · 30D:-12.07B` | `Macro` | `OK` |
| US Spot ETF Flow (Farside 1D/3D) | `DATA UNAVAILABLE` | `2,13` | `UNAVAILABLE` |
| US ETF Tape Proxy (IBIT+FBTC) | `1DVol:$2.28B · 5D:-$6.19B [PROXY]` | `Macro,2,13` | `PROXY` |
| Power-Law Fair & ATH DD% | `$149,220.71 (-57.2%) | DD:-49.4%` | `3` | `OK` |
| MTF MACD (1D / 1H Status) | `1D=negative_slope (Macro Whipsaw Veto) | 1H=negative_slope / NEUTRAL` | `13,16,18` | `OK` |

## 5. MACRO, CREDIT & US LIQUIDITY
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| US SOFR Rate & Vol (NY Fed) | `3.90% (Vol:$3,138B)` | `Macro` | `OK` |
| Fed ON RRP Balance (NY Fed) | `$0.33B` | `Macro` | `OK` |
| Credit Spread HYG/LQD & 5D% | `0.7484 (+1.29% 5D)` | `Macro,3` | `OK` |
| DXY / US 10Y (^TNX) | `103.41 (RISING (+1.76 over 5d)) | 10Y:5.15%` | `3,13` | `OK` |
| TIPS Real (DFII10) / BEI | `Real:+2.91% | BEI:2.24%` | `3,13` | `OK` |
| S&P 500 / Nasdaq (1D%) | `SPX:7,562 (-0.40%) | NDX:25,136` | `3,13` | `OK` |
| VIX / Brent Crude (BZ=F) | `VIX:19.30 | Brent:$95.84` | `3,13` | `OK` |
| BTC-SPX Corr (20D / 60D) | `20D:+0.40 | 60D:+0.43` | `3` | `OK` |
| Fear & Greed / BTC Dom% | `F&G:10 (Extreme Fear) | Dom:58.70%` | `3,13` | `OK` |
| Manual Context Overrides | `200D_Veto=False · Filter=NONE_SIGNIFICANT` | `2,13` | `OK` |

## 6. QUANT FEATURES, FEED HEALTH & ARCHIVE
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| Rough Path Lévy (A_SP / MM) | `4H A_SP:+1.1637 | MM PriceFlow:-0.0131 · Rough:0.250` | `5,19` | `OK` |
| Hurst / Kalman Vel / FracDiff | `H:0.717 · KVel:-42.80 · d:0.20` | `5,6` | `OK` |
| Hilbert Cycle / TD9 / TellTale | `Cyc:8.0b · TD(1H/4H):9/8 · RV(15m/5m):0.55/N/A` | `5,9,13` | `OK` |
| VCR 72H & TSFM Disp% | `VCR:12.41 | Disp:1.28%` | `6` | `OK` |
| Open FVGs & Sweep FSM | `FVGs:7 | FSM:None (0/12)` | `1,8` | `OK` |
| WebSocket Feeds & Warmup | `Spot:SYNC (no tick) | Perp:SYNC (no tick) | CB:SYNC (11s ago) | Warm:YES` | `Live Feeds` | `STALE` |
| Spot Klines (1W/1D/4H/1H/15m) | `1W:100 1D:500 bars · 11-15 00:00 UTC | 4H:500 1H:720 15m:240` | `All Tabs` | `OK` |
| Perp Klines / Est. Excluded | `1D:101 · 1H:720 · 15m:240 (Excl=399)` | `1,4,11,15,19` | `OK` |
| Closed 4H Anchor (Tab 19/20) | `2026-11-15 00:00:00 UTC` | `18,19,20` | `OK` |
| B1/B2 Rec & Companion Liq | `Rec:PASS (0s delta) | Liq:N/A` | `8,13,17` | `OK` |
| Telemetry History Archive (SQLite) | `4 bars logged (Last: 2026-11-15 00:00:00 UTC)` | `DB Archive` | `OK` |

## 7. RECENT CLOSED-4H SNAPSHOT TRAJECTORY (SQLITE ARCHIVE)
| Closed 4H Bar (UTC) | Spot ($) | 24H Spot/Perp CVD | Cross-Exch Perp OI & Funding | Funding 8H% / P90 | MVRV Ratio |
|---|---|---|---|---|---|
| `2026-11-15 00:00:00 UTC` | `$64,272.01` | `24h:-2238.0/-7818.2 BTC` | `167,545 BTC ($10.73B) · F:+0.0033% [BN+BYB+OKX]` | `+0.0050% (+5.5%/yr) · P90:0.7%` | `1.267 [CoinMetrics 2026-11-13]` |
| `2026-11-14 20:00:00 UTC` | `$65,534.82` | `24h:-2470.9/-3413.1 BTC` | `167,154 BTC ($10.95B) · F:+0.0026% [BN+BYB+OKX]` | `+0.0029% (+3.2%/yr) · P90:39.3%` | `1.267 [CoinMetrics 2026-11-13]` |
| `2026-11-14 16:00:00 UTC` | `$65,484.09` | `24h:-2202.7/-9856.6 BTC` | `200,720 BTC ($13.14B) · F:+0.0059% [BN+BYB+OKX]` | `+0.0035% (+3.8%/yr) · P90:31.9%` | `1.267 [CoinMetrics 2026-11-13]` |
| `2026-11-14 12:00:00 UTC` | `$65,871.93` | `24h:-1587.1/-10846.6 BTC` | `201,340 BTC ($13.26B) · F:+0.0037% [BN+BYB+OKX]` | `+0.0031% (+3.4%/yr) · P90:35.6%` | `1.267 [CoinMetrics 2026-11-13]` |

## 8. METRIC FORMULA LEGEND & AI ANALYSIS PROMPT
- **Rough Path Lévy (`4H A_SP`)**: Lévy signed area over 6 closed 4H bars (`> 0`: Spot path leads price markup; `< 0`: Spot path lags price / distribution).
- **24H Z-Scores (`z_S / z_F / D`)**: 30-day rolling Z-scores of 24H Spot (`z_S`) and Perp (`z_F`) cumulative delta; `D = z_S - z_F` (`D > 0` = Spot buying divergence vs Perps).
- **Volume Profile & Structure**: `VA Pos% = (Spot - VAL) / (VAH - VAL) * 100`; `L20/H20` = 20-bar (80H) 4H range boundaries; `SLSP` = structural liquidity pool S/R.
- **Quant & Volatility**: `H` = Hurst exponent (`>0.5` trending, `<0.5` mean-reverting); `VCR 72H` = 72H Volatility Compression Ratio; `TSFM Disp%` = horizon dispersion; `LSCE` = liquidation sweep state.
- **AI Analysis Task (5-Part Framework)**: Synthesize all 6 domains + the 4H archive trajectory into: (1) Multi-Timeframe Regime & Structural Map (`1W/1D/4H/1H`), (2) Spot Absorption vs Perpetual Leverage Alignment, (3) Derivatives & Options Skew/IV Pricing, (4) On-Chain, Stablecoin & US Macro Liquidity Impulse, and (5) Concrete Upside/Downside Scenarios with Key Invalidation Levels.
- **Direct AI Instruction (Execute Immediately on Paste)**: Analyze BTC using the telemetry report above. Follow the 5-part analysis framework in Section 8 and give me a clear bull vs. bear probability, key support/resistance & liquidation levels, and actionable swing / intraday setups with invalidation levels.
