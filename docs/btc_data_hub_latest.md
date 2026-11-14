# TAB [D: DATA HUB] | CONSOLIDATED DATA-ONLY TELEMETRY REPORT
**Retrieval Time (UTC):** `2026-11-14 15:40:07 UTC`  |  **Retrieval Time (MYT):** `2026-11-14 23:40:07 MYT (UTC+8)`
**Spot Price (BTCUSDT):** `$65,236.33`  |  **Coverage:** `OK=60/66 | UNAVAILABLE=2 | STALE=3 | PROXY/STATIC=1`
**Archive (SQLite):** `1 closed-4H snapshots (Last: 2026-11-14 12:00:00 UTC)`

## 1. PRICE, TREND & MARKET STRUCTURE
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| Binance Spot / Perp ($) | `$65,236.33 / $65,235.50` | `All Tabs` | `OK` |
| Coinbase Spot ($) | `$65,183.55` | `1,11,15,17` | `OK` |
| 1D SMA 200 / Slope | `$73,091.58 (-0.18%)` | `0,2,3,11,15,18` | `OK` |
| 1D SMA 50 / EMA 50 | `$80,624.41 / $77,699.97` | `0,2,4,15,18,20` | `OK` |
| 1D EMA 21 / 1W EMA 50 | `$75,216.76 / $78,261.29` | `3,18` | `OK` |
| 4H EMA 50 / EMA 200 | `$72,930.73 / $77,544.01` | `7,13,18,20` | `OK` |
| Grok EMA 9/21 & 1H SMA200 | `9:$66,610.32 · 21:$67,378.99 · 1H:$73,413.21` | `5,15` | `OK` |
| Daily / Weekly VWAP (Z) | `D:$66,867.06 (-2.24σ) | W:$71,759.59` | `4,11,15` | `OK` |
| RSI(14) 1D / 4H & 4H ROC12 | `1D:20.7 · 4H:23.4 · ROC:-7.79%` | `3,7,20` | `OK` |
| ADX(14) 1D/4H & ATR(14) | `ADX 1D:28.3 4H:58.5 | ATR:$2,416.71/$1,224.59/$583.43` | `0,1,2,8,13,18,20` | `OK` |
| Macro 30D VAH / POC / VAL | `$83,328.02 / $81,675.41 / $75,560.74` | `1,3,6,11,19` | `OK` |
| Structure (L20/H20, PW, Asia) | `4H:$67,568.00-$81,971.00 | PW:$73,510.00-$81,196.01 | Asia:$66,456.00-$68,446.21` | `0,8,11,19` | `OK` |

## 2. ORDER FLOW, FOOTPRINT & LIQUIDITY
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| Spot/Perp CVD (15m / 1h) | `15m:-139.7/+54.0 | 1h:-610.1/-1529.9 BTC` | `1,8,15` | `OK` |
| Spot/Perp CVD (4h / 24h) | `4h:-1080.3/-4566.1 | 24h:-2388.6/-10456.9 BTC` | `0,1,15,16,17` | `OK` |
| Session / UTC-Day CVD | `Sess S:+0.0 P:+0.0 | Day S:-2123.6 P:-9051.5` | `REST 15m` | `OK` |
| 24H Z-Scores (z_S / z_F / D) | `z_S:-0.94 · z_F:-1.58 · D:+0.64` | `1,19` | `OK` |
| 15m Footprint Delta / Stack | `Δ:-139.7 BTC (Prev:-295.9) · Stacks:0` | `1,11` | `OK` |
| Coinbase Premium ($ / % / Z) | `-52.8$ (-0.081%, Z=+0.33)` | `1,11,15` | `OK` |
| Cross-Exch 24H Spot Vol (BN/CB) | `BN:22,179 · CB:11,975 · Tot:34,154 BTC` | `1,11,Macro` | `OK` |
| L2 Depth ±1%/±2%, OBI & Spread | `1%:2.00x · 2%:2.12x · Spr:0.00bps · OBI:+33.4%` | `16,Macro` | `OK` |
| Tactical 7D / Session 24H VP | `7D:$76,153.61/$73,741.39/$69,195.27 | 24H:$68,083.28/$67,269.81/$65,778.45` | `1,11` | `OK` |
| VA Pos% & Dist to VAL | `-132.9% | -13.66% (-17.70 ATR)` | `1` | `OK` |
| SLSP Support / Resistance | `Sup:$64,742.09 | Res:$65,575.31` | `13` | `OK` |

## 3. DERIVATIVES, OPTIONS & LIQUIDATIONS
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| BN Open Interest (BTC / USD) | `97,353 BTC ($6.35B)` | `0,1,4,15,17` | `OK` |
| Cross-Exch Perp OI & Funding | `201,825 BTC ($13.16B) · F:+0.0044% [BN+BYB+OKX]` | `Macro,15` | `OK` |
| OI Δ% (15m/1h/4h/24h) & Quad | `-0.16%/+0.75%/+1.04%/+0.75% | AGGRESSIVE_SHORT_BUILD (Price Down/Flat / OI Up)` | `1,4,8,11,12,15,17` | `OK` |
| Funding 8H% / Ann% / P90 | `+0.0041% (+4.5%/yr) · P90:35.6%` | `0,4,9,11,15,16,19,20` | `OK` |
| Perp Basis ($ / Ann %) | `-0.8$ (-0.001% | Carry:+4.40%/yr)` | `1,4` | `OK` |
| 5m Taker L/S & Top/Glb Acct | `5m:0.894 (Δ:-171.7) | Top:1.87(65L) · Glb:3.01` | `1,2,15,16` | `OK` |
| Options OI & Put/Call (Deribit) | `P/C:0.729 · TotOI:357,471 BTC` | `Macro,19` | `OK` |
| Options IV Term & Skew (Deribit) | `F:46.2% · B:42.3% · 25dSk:+8.2%` | `Macro,6,19` | `OK` |
| Vol: DVOL, RV20, GK & BBW% | `DVOL:46.2 · RV20:45.1% · GK:56.1% · BBW:77% · Sk20:-0.30` | `0,4,6,16,19` | `OK` |
| Upper / Lower Liq Magnet | `Up:$76,334.44 | Dn:$64,062.08` | `0,2,13,17` | `OK` |
| Magnet Ratios & LSCE | `Imm:1.81x · Ladder:1.79x · Pull:0.55x · LSCE:UNTESTED` | `13,17` | `OK` |
| Liquidations (1H / 24H) & Flush | `1H:$1.35M (L:1.2 S:0.1) | 24H:$1.50M (x0.05) · STABILISATION_DEVELOPING (Early higher-low formed; pending structure break)` | `0,8,12,13` | `STALE` |

## 4. ON-CHAIN, ETF & STABLECOIN FLOWS
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| MVRV Ratio (On-Chain / Proxy) | `1.267 [CoinMetrics 2026-11-13]` | `Macro,16` | `OK` |
| On-Chain SOPR / aSOPR | `DATA UNAVAILABLE` | `16` | `UNAVAILABLE` |
| Exchange Netflow 24H (CM) | `Net:-2,129.5 BTC (-$145.0M) | In:26,738 Out:28,868` | `Macro,16` | `OK` |
| BTC Exchange Reserves (CM) | `2,723,962 BTC (2026-11-13)` | `Macro,16` | `OK` |
| Stablecoins USDT+USDC Supply | `$244.49B (USDT:$175.25B · USDC:$69.24B)` | `Macro` | `OK` |
| Stablecoin Net Issuance (7D/30D) | `7D:-2.95B · 30D:-12.16B` | `Macro` | `OK` |
| US Spot ETF Flow (Farside 1D/3D) | `DATA UNAVAILABLE` | `2,13` | `UNAVAILABLE` |
| US ETF Tape Proxy (IBIT+FBTC) | `1DVol:$2.28B · 5D:-$6.19B [PROXY]` | `Macro,2,13` | `PROXY` |
| Power-Law Fair & ATH DD% | `$149,171.57 (-56.3%) | DD:-48.3%` | `3` | `OK` |
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
| BTC-SPX Corr (20D / 60D) | `20D:+0.42 | 60D:+0.44` | `3` | `OK` |
| Fear & Greed / BTC Dom% | `F&G:13 (Extreme Fear) | Dom:58.60%` | `3,13` | `OK` |
| Manual Context Overrides | `200D_Veto=False · Filter=NONE_SIGNIFICANT` | `2,13` | `OK` |

## 6. QUANT FEATURES, FEED HEALTH & ARCHIVE
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| Rough Path Lévy (A_SP / MM) | `4H A_SP:-2.5434 | MM PriceFlow:-0.0318 · Rough:0.280` | `5,19` | `OK` |
| Hurst / Kalman Vel / FracDiff | `H:0.513 · KVel:-42.70 · d:0.20` | `5,6` | `OK` |
| Hilbert Cycle / TD9 / TellTale | `Cyc:72.0b · TD(1H/4H):4/5 · RV(15m/5m):1.60/N/A` | `5,9,13` | `OK` |
| VCR 72H & TSFM Disp% | `VCR:6.06 | Disp:1.28%` | `6` | `OK` |
| Open FVGs & Sweep FSM | `FVGs:9 | FSM:None (0/12)` | `1,8` | `OK` |
| WebSocket Feeds & Warmup | `Spot:SYNC (no tick) | Perp:SYNC (no tick) | CB:SYNC (10s ago) | Warm:YES` | `Live Feeds` | `STALE` |
| Spot Klines (1W/1D/4H/1H/15m) | `1W:100 1D:500 bars · 11-14 00:00 UTC | 4H:500 1H:720 15m:240` | `All Tabs` | `OK` |
| Perp Klines / Est. Excluded | `1D:500 · 1H:720 · 15m:240 (Excl=0)` | `1,4,11,15,19` | `OK` |
| Closed 4H Anchor (Tab 19/20) | `2026-11-14 12:00:00 UTC` | `18,19,20` | `OK` |
| B1/B2 Rec & Companion Liq | `Rec:PASS (0s delta) | Liq:STALE (cached)` | `8,13,17` | `STALE` |
| Telemetry History Archive (SQLite) | `1 bars logged (Last: 2026-11-14 12:00:00 UTC)` | `DB Archive` | `OK` |
