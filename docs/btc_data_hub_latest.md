# TAB [D: DATA HUB] | CONSOLIDATED DATA-ONLY TELEMETRY REPORT
**Retrieval Time (UTC):** `2026-11-16 18:09:32 UTC`  |  **Retrieval Time (SGT):** `2026-11-17 02:09:32 SGT (UTC+8)`
**Spot Price (BTCUSDT):** `$64,885.01`  |  **Coverage:** `OK=67/71 | UNAVAILABLE=2 | STALE=1 (Genuine=0, Expected_Headless_WS_Offline=1) | PROXY/STATIC=1`
**24H Range:** `$63,905.01 - $65,696.16`  |  **Returns (24H / 7D / 30D):** `+0.24% / -13.91% / -20.38%`
**Archive (SQLite):** `12 closed-4H snapshots (Last: 2026-11-16 16:00:00 UTC)`

## 0. HARD DOWNTREND MARKET VETO (PRE-ENTRY CAPITAL PRESERVATION GATE)
| Gate Field | Value | Rule / Threshold |
|---|---|---|
| Latest Closed 1D Candle Close | `$65,351.05 (1D bar 2026-11-15 · closed 2026-11-16 00:00 UTC)` | `Same closed Binance Spot 1D series only (live candle excluded)` |
| Current 1D SMA 200 | `$72,978.47` | `200-bar SMA of same closed Binance Spot 1D series` |
| Distance vs 1D SMA 200 | `-10.45% (-$7,627.42)` | `(Closed 1D Close - 1D SMA 200) / 1D SMA 200` |
| 1D SMA 200 Position | `BELOW` | `BELOW if Closed 1D Close < 1D SMA 200 else ABOVE` |
| Closed 4H Market Structure (`7A`) | `DOWNTREND (LH/LL)` | `UPTREND / DOWNTREND / MIXED (500 closed 4H bars)` |
| 4H Downside BOS Status (`7A`) | `YES (BOS Down < $72,727.27 (11-12 12:00))` | `YES if latest closed 4H BOS is BOS Down else NO` |
| Timestamp & Candle Closed Status | `2026-11-16 18:09:32 UTC | 2026-11-17 02:09:32 SGT (UTC+8) · Closed-Candle Inputs Only` | `Strict closed-bar verification gate` |

**HARD DOWNTREND MARKET VETO STATUS:**
- **Veto Status:** `ACTIVE`
- **Condition A (Closed 1D Close < 1D SMA 200):** `YES`
- **Condition B (4H Downside Structure / BOS Down):** `YES`
- **Portfolio Status:** `100% USDT CASH`
- **New BTC Entry:** `PROHIBITED`

## 1. PRICE, TREND & MARKET STRUCTURE
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| Binance Spot / Perp ($) | `$64,885.01 / $64,850.10` | `All Tabs` | `OK` |
| Coinbase Spot ($) | `$64,824.34` | `1,11,15,17` | `OK` |
| 1D SMA 200 / Slope | `$72,978.47 (-0.29%)` | `0,2,3,11,15,18` | `OK` |
| 1D SMA 50 / EMA 50 | `$79,843.77 / $76,692.81` | `0,2,4,15,18,20` | `OK` |
| 1D EMA 21 / 1W EMA 50 | `$73,380.54 / $77,791.73` | `3,18` | `OK` |
| 4H EMA 50 / EMA 200 | `$69,670.59 / $75,992.85` | `7,13,18,20` | `OK` |
| Grok EMA 9/21 & 1H SMA200 | `9:$64,738.16 · 21:$64,756.79 · 1H:$70,581.25` | `5,15` | `OK` |
| Daily / Weekly VWAP (Z) | `D:$64,694.58 (+0.60σ) | W:$68,532.98` | `4,11,15` | `OK` |
| RSI(14) 1D / 4H & 4H ROC12 | `1D:23.7 · 4H:30.2 · ROC:-1.94%` | `3,7,20` | `OK` |
| ADX(14) 1D/4H & ATR(14) 1D/4H/1H | `ADX 1D:34.1 4H:60.8 | ATR:$2,664.81/$1,354.77/$596.19` | `0,1,2,8,13,18,20` | `OK` |
| 4H ATR(14)% Pctile & RelVol(20) | `ATR%:2.10% (94th pct/120b) · RelVol:1.05x` | `0,1,2,20` | `OK` |
| Macro 30D VAH / POC / VAL | `$83,276.48 / $80,605.75 / $73,738.15` | `1,3,6,11,19` | `OK` |
| Structure (L20/H20, PW, Asia) | `4H:$62,006.00-$81,971.00 | PW:$62,006.00-$75,599.22 | Asia:$64,294.11-$65,392.01` | `0,8,11,19` | `OK` |

## 2. ORDER FLOW, FOOTPRINT & LIQUIDITY
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| Spot/Perp CVD (15m / 1h) | `15m:+9.9/+211.3 | 1h:+182.9/-63.5 BTC` | `1,8,15` | `OK` |
| Spot/Perp CVD (4h / 24h) | `4h:+562.7/+185.9 | 24h:-448.1/-157.3 BTC` | `0,1,15,16,17` | `OK` |
| Spot CVD Slopes (7D / 14D) | `7D:-3,835.8 BTC | 14D:-2,589.1 BTC` | `17` | `OK` |
| Session / UTC-Day CVD | `Sess S:+0.0 P:+0.0 | Day S:+249.3 P:-771.1` | `REST 15m` | `OK` |
| 24H Z-Scores (z_S / z_F / D) | `z_S:-1.26 · z_F:+0.70 · D:-1.96` | `1,19` | `OK` |
| 15m Footprint Delta / Stack | `Δ:+9.9 BTC (Prev:+38.7) · Stacks:0` | `1,11` | `OK` |
| Coinbase Premium ($ / % / Z) | `-60.7$ (-0.094%, Z=+0.46)` | `1,11,15` | `OK` |
| Cross-Exch 24H Spot Vol (BN/CB) | `BN:20,366 · CB:11,784 · Tot:32,151 BTC` | `1,11,Macro` | `OK` |
| L2 Depth ±1%/±2%, OBI & Spread | `1%:0.91x · 2%:1.37x · Spr:0.0015bps · OBI:-4.6%` | `16,Macro` | `OK` |
| Tactical 7D / Session 24H VP | `7D:$71,579.16/$64,637.22/$62,173.95 | 24H:$65,173.74/$64,964.77/$64,487.13` | `1,11` | `OK` |
| 30D VA Pos% & Dist to VAL | `-92.8% | -12.01% (-14.85 ATR)` | `1` | `OK` |
| SLSP Support / Resistance | `Sup:$64,742.09 | Res:$65,575.31` | `13` | `OK` |

## 3. DERIVATIVES, OPTIONS & LIQUIDATIONS
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| BN Open Interest (BTC / USD) | `93,556 BTC ($6.06B)` | `0,1,4,15,17` | `OK` |
| Cross-Exch Perp OI & Funding | `159,896 BTC ($10.36B) · F:+0.0076% [BN+BYB+OKX 3/3]` | `Macro,15` | `OK` |
| Hyperliquid Perp OI & Funding | `36,313 BTC ($2.36B) · F:+0.0100% [HL DEX]` | `Macro,15` | `OK` |
| OI Δ% (15m/1h/4h/24h) & Quad | `-0.00%/-1.27%/-2.99%/-3.06% | NEUTRAL_CHURN` | `1,4,8,11,12,15,17` | `OK` |
| Funding 8H% / Ann% / 90D Pct | `+0.0079% (+8.6%/yr) · 90D Pct:54.1%` | `0,4,9,11,15,16,19,20` | `OK` |
| Perp Basis ($ / Ann %) | `-34.9$ (-0.054% | Carry:+8.00%/yr)` | `1,4` | `OK` |
| 5m Taker L/S & Top/Glb Acct | `5m:2.479 (Δ:+98.1) | Top:1.69(63L) · Glb:2.69` | `1,2,15,16` | `OK` |
| Options OI & Put/Call (Deribit) | `P/C:0.760 · TotOI:381,064 BTC` | `Macro,19` | `OK` |
| Options IV Term & Skew (Deribit) | `F:42.1% · B:40.5% · 25dSk:+5.6%` | `Macro,6,19` | `OK` |
| Vol: DVOL, RV20, GK & BBW% | `DVOL:42.9 · RV20:48.7% · GK:75.8% · BBW:84% · Sk20:-0.41` | `0,4,6,16,19` | `OK` |
| Upper / Lower Liq Magnet | `Up:$76,334.44 | Dn:$63,717.08` | `0,2,13,17` | `OK` |
| Magnet Ratios & LSCE | `Imm:1.81x · Ladder:1.79x · Pull:0.55x · LSCE:UNTESTED` | `13,17` | `OK` |
| Modeled Liq Ladder (10x-100x) | `Up[10x:$67,685.16($102M) / 25x:$66,684.89($136M) / 50-100x:$66,024.64($194M)] | Dn[100x:$63,717.08($350M) / 25x:$63,079.91($315M) / 10x:$62,133.71($221M)] [Modeled]` | `17` | `OK` |
| Liquidations (1H / 24H) & Flush | `DATA UNAVAILABLE` | `0,8,12,13` | `UNAVAILABLE` |

## 4. ON-CHAIN, ETF & STABLECOIN FLOWS
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| MVRV Ratio (On-Chain / Proxy) | `1.214 [CoinMetrics 2026-11-15]` | `Macro,16` | `OK` |
| On-Chain SOPR / aSOPR | `DATA UNAVAILABLE` | `16` | `UNAVAILABLE` |
| Exchange Netflow 24H (CM) | `Net:-12,011.9 BTC (-$783.0M) | In:17,219 Out:29,231` | `Macro,16` | `OK` |
| BTC Exchange Reserves (CM) | `2,708,826 BTC (2026-11-15)` | `Macro,16` | `OK` |
| Stablecoins USDT+USDC Supply | `$244.46B (USDT:$175.27B · USDC:$69.19B)` | `Macro` | `OK` |
| Stablecoin Net Issuance (7D/30D) | `7D:-2.97B · 30D:-11.79B` | `Macro` | `OK` |
| US Spot ETF Flow (Farside 1D/3D) | `1D:+$0 | 3D:-$469.5M | 5D:-$864.3M` | `2,13` | `OK` |
| US ETF Tape Proxy (IBIT+FBTC) | `1DVol:$1.74B · 5D:-$6.42B [PROXY]` | `Macro,2,13` | `PROXY` |
| Power-Law Fair & ATH DD% | `$149,444.97 (-56.6%) | DD:-48.6%` | `3` | `OK` |
| MTF MACD (1D / 1H Status) | `1D=negative_slope (Macro Whipsaw Veto) | 1H=positive_slope CROSS` | `13,16,18` | `OK` |

## 5. MACRO, CREDIT & US LIQUIDITY
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| US SOFR Rate & Vol (NY Fed) | `3.90% (Vol:$3,092B)` | `Macro` | `OK` |
| Fed ON RRP Balance (NY Fed) | `$0.33B` | `Macro` | `OK` |
| Credit Spread HYG/LQD & 5D% | `0.7468 (+0.85% 5D)` | `Macro,3` | `OK` |
| DXY / US 10Y (^TNX) | `103.54 (RISING (+1.31 over 5d)) | 10Y:5.13%` | `3,13` | `OK` |
| TIPS Real (DFII10) / BEI | `Real:+2.91% | BEI:2.23%` | `3,13` | `OK` |
| S&P 500 / Nasdaq (1D%) | `SPX:7,441 (-1.60%) | NDX:24,586` | `3,13` | `OK` |
| VIX / Brent Crude (BZ=F) | `VIX:21.74 | Brent:$93.00` | `3,13` | `OK` |
| BTC-SPX Corr (20D / 60D) | `20D:+0.47 | 60D:+0.50` | `3` | `OK` |
| Fear & Greed / BTC Dom% | `F&G:10 (Extreme Fear) | Dom:58.60%` | `3,13` | `OK` |
| USD Macro Calendar (High) | `Core Retail Sales m/m (in 19.3h Fc:0.4%) | Retail Sales m/m (in 19.3h Fc:0.2%) (+1 more)` | `Macro` | `OK` |
| Manual Context Overrides | `Legacy_200D_Veto_Override: IGNORED (Tab1_Flag=False) · Filter=NONE_SIGNIFICANT` | `2,13` | `OK` |

## 6. QUANT FEATURES, FEED HEALTH & ARCHIVE
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| Rough Path Lévy (A_SP / MM) | `4H A_SP:+3.8647 | MM PriceFlow:-0.0133 · Rough:4.150` | `5,19` | `OK` |
| Hurst / Kalman Vel / FracDiff | `H:0.911 · KVel:-60.60 · d:0.20` | `5,6` | `OK` |
| Hilbert Cycle / TD9 / TellTale | `Cyc:72.0b · TD(1H/4H):1/3 · RV(15m/5m):0.45/N/A` | `5,9,13` | `OK` |
| VCR 72H & TSFM Disp% | `VCR:16.09 | Disp:1.28%` | `6` | `OK` |
| Open FVGs & Sweep FSM | `FVGs:0 | FSM:None (0/12)` | `1,8` | `OK` |
| WebSocket Feeds & Warmup | `Spot:SYNC (no tick) | Perp:SYNC (no tick) | CB:SYNC (11s ago) | Warm:YES` | `Live Feeds` | `STALE` |
| Spot Klines (1W/1D/4H/1H/15m) | `1W:100 1D:500 bars · 11-16 00:00 UTC | 4H:500 1H:720 15m:240` | `All Tabs` | `OK` |
| Perp Klines / Est. Excluded | `1D:100 · 1H:720 · 15m:240 (Excl=400)` | `1,4,11,15,19` | `OK` |
| Closed 4H Anchor (Tab 19/20) | `2026-11-16 16:00:00 UTC` | `18,19,20` | `OK` |
| B1/B2 Rec & Companion Liq | `Rec:PASS (0s delta) | Liq:N/A` | `8,13,17` | `OK` |
| Telemetry History Archive (SQLite) | `12 bars logged (Last: 2026-11-16 16:00:00 UTC)` | `DB Archive` | `OK` |

## 7. RECENT CLOSED-4H SNAPSHOT TRAJECTORY (SQLITE ARCHIVE)
| Closed 4H Bar (UTC) | Spot ($) | 24H Spot/Perp CVD | Cross-Exch Perp OI & Funding | Funding 8H% / 90D Pct | MVRV Ratio |
|---|---|---|---|---|---|
| `2026-11-16 16:00:00 UTC` | `$64,885.01` | `24h:-448.1/-157.3 BTC` | `159,896 BTC ($10.36B) · F:+0.0076% [BN+BYB+OKX 3/3]` | `+0.0079% (+8.6%/yr) · 90D Pct:54.1%` | `1.214 [CoinMetrics 2026-11-15]` |
| `2026-11-16 08:00:00 UTC` | `$64,644.70` | `24h:-2105.7/-1447.0 BTC` | `161,580 BTC ($10.43B) · F:+0.0017% [BN+BYB+OKX 3/3]` | `+0.0007% (+0.8%/yr) · 90D Pct:5.9%` | `1.214 [CoinMetrics 2026-11-15]` |
| `2026-11-16 04:00:00 UTC` | `$64,925.69` | `24h:-2000.7/-2017.8 BTC` | `160,648 BTC ($10.42B) · F:-0.0001% [BN+BYB+OKX 3/3]` | `+0.0000% (+0.1%/yr) · 90D Pct:3.3%` | `1.214 [CoinMetrics 2026-11-15]` |
| `2026-11-16 00:00:00 UTC` | `$65,096.00` | `24h:-2825.0/+2036.9 BTC` | `160,961 BTC ($10.50B) · F:+0.0001% [BN+BYB+OKX 3/3]` | `-0.0012% (-1.3%/yr) · 90D Pct:3.3%` | `1.188 [CoinMetrics 2026-11-14]` |
| `2026-11-15 20:00:00 UTC` | `$65,110.00` | `24h:-2138.5/-607.9 BTC` | `161,015 BTC ($10.46B) · F:+0.0022% [BN+BYB+OKX 3/3]` | `+0.0006% (+0.6%/yr) · 90D Pct:12.2%` | `1.188 [CoinMetrics 2026-11-14]` |
| `2026-11-15 12:00:00 UTC` | `$64,913.29` | `24h:-1914.1/-3765.8 BTC` | `163,854 BTC ($10.60B) · F:-0.0003% [BN+BYB+OKX 3/3]` | `+0.0000% (+0.1%/yr) · 90D Pct:8.9%` | `1.188 [CoinMetrics 2026-11-14]` |

### 7A. 500-BAR MARKET STRUCTURE & HISTORICAL S/R ZONES (`1D / 4H / 1H`)
| TF (Bars) | Swing Structure | Last Swing Pivots | Latest BOS | Resistance Zones (Above Spot) | Support Zones (Below Spot) |
|---|---|---|---|---|---|
| `1D (499)` | `DOWNTREND (LH/LL)` | `SH:$81,196.01 (11-04) · SL:$79,800.00 (10-15)` | `BOS Down < $79,800.00 (10-29)` | `$65,182.19 (5x), $67,124.15 (2x), $70,983.00 (1x)` | `$62,440.17 (3x), $60,000.00 (1x), $59,130.91 (1x)` |
| `4H (499)` | `DOWNTREND (LH/LL)` | `SH:$74,811.45 (11-11 20:00) · SL:$62,006.00 (11-15 00:00)` | `BOS Down < $72,727.27 (11-12 12:00)` | `$72,727.27 (1x), $73,510.00 (1x), $75,173.28 (6x)` | `$62,006.00 (1x)` |
| `1H (500)` | `DOWNTREND (LH/LL)` | `SH:$65,508.86 (11-15 23:00) · SL:$63,905.01 (11-16 12:00)` | `BOS Down < $66,456.00 (11-14 14:00)` | `$65,745.55 (3x), $66,456.00 (1x), $67,731.35 (3x)` | `$64,081.33 (2x), $62,006.00 (1x)` |

### 7B. RECENT CLOSED KLINES — OHLCV PRICE ACTION (`1D`×7, `4H`×12, `1H`×12)
**1D Closed Candles (Last 7 of 499 available, Newest First):**
| Open Time (UTC) | Open | High | Low | Close | Chg% | Vol (BTC) |
|---|---|---|---|---|---|---|
| `2026-11-15` | `$64,150.01` | `$66,132.01` | `$62,006.00` | `$65,351.05` | `+1.87%` | `29,231` |
| `2026-11-14` | `$68,314.01` | `$68,446.21` | `$63,320.00` | `$64,150.00` | `-6.10%` | `32,675` |
| `2026-11-13` | `$71,460.00` | `$71,514.01` | `$67,568.00` | `$68,314.00` | `-4.40%` | `29,649` |
| `2026-11-12` | `$74,015.20` | `$74,217.49` | `$71,113.06` | `$71,460.00` | `-3.45%` | `15,228` |
| `2026-11-11` | `$73,796.06` | `$74,811.45` | `$73,209.12` | `$74,015.19` | `+0.30%` | `16,146` |
| `2026-11-10` | `$75,368.41` | `$75,442.01` | `$72,727.27` | `$73,796.06` | `-2.09%` | `16,466` |
| `2026-11-09` | `$74,851.44` | `$75,599.22` | `$73,750.00` | `$75,368.41` | `+0.69%` | `15,687` |

**4H Closed Candles (Last 12 of 499 available, Newest First):**
| Open Time (UTC) | Open | High | Low | Close | Chg% | Vol (BTC) |
|---|---|---|---|---|---|---|
| `2026-11-16 12:00` | `$64,448.32` | `$65,696.16` | `$63,905.01` | `$64,467.00` | `+0.03%` | `4,865` |
| `2026-11-16 08:00` | `$64,995.13` | `$64,995.28` | `$64,128.00` | `$64,448.32` | `-0.84%` | `3,169` |
| `2026-11-16 04:00` | `$65,113.93` | `$65,190.00` | `$64,294.11` | `$64,995.12` | `-0.18%` | `3,052` |
| `2026-11-16 00:00` | `$65,351.05` | `$65,392.01` | `$64,530.12` | `$65,113.92` | `-0.36%` | `3,814` |
| `2026-11-15 20:00` | `$64,947.43` | `$65,508.86` | `$64,700.00` | `$65,351.05` | `+0.62%` | `2,895` |
| `2026-11-15 16:00` | `$64,748.30` | `$65,230.23` | `$64,257.65` | `$64,947.43` | `+0.31%` | `3,108` |
| `2026-11-15 12:00` | `$65,351.00` | `$65,800.75` | `$64,456.01` | `$64,748.30` | `-0.92%` | `3,212` |
| `2026-11-15 08:00` | `$64,012.59` | `$66,132.01` | `$63,873.26` | `$65,351.00` | `+2.09%` | `5,254` |
| `2026-11-15 04:00` | `$64,826.00` | `$65,169.23` | `$63,777.00` | `$64,012.60` | `-1.25%` | `3,302` |
| `2026-11-15 00:00` | `$64,150.01` | `$65,595.77` | `$62,006.00` | `$64,825.99` | `+1.05%` | `11,461` |
| `2026-11-14 20:00` | `$65,727.61` | `$65,884.01` | `$63,320.00` | `$64,150.00` | `-2.40%` | `8,948` |
| `2026-11-14 16:00` | `$65,742.00` | `$66,189.88` | `$65,000.00` | `$65,727.61` | `-0.02%` | `4,554` |

**1H Closed Candles (Last 12 of 719 available, Newest First):**
| Open Time (UTC) | Open | High | Low | Close | Chg% | Vol (BTC) |
|---|---|---|---|---|---|---|
| `2026-11-16 17:00` | `$64,927.21` | `$65,150.00` | `$64,799.00` | `$64,912.62` | `-0.02%` | `656` |
| `2026-11-16 16:00` | `$64,467.00` | `$64,949.21` | `$64,228.01` | `$64,927.22` | `+0.71%` | `942` |
| `2026-11-16 15:00` | `$65,166.34` | `$65,172.78` | `$64,100.00` | `$64,467.00` | `-1.07%` | `1,282` |
| `2026-11-16 14:00` | `$64,186.27` | `$65,696.16` | `$64,013.62` | `$65,166.33` | `+1.53%` | `1,659` |
| `2026-11-16 13:00` | `$64,169.58` | `$64,484.01` | `$64,083.12` | `$64,186.27` | `+0.03%` | `1,003` |
| `2026-11-16 12:00` | `$64,448.32` | `$64,456.90` | `$63,905.01` | `$64,169.58` | `-0.43%` | `921` |
| `2026-11-16 11:00` | `$64,574.83` | `$64,796.01` | `$64,444.01` | `$64,448.32` | `-0.20%` | `1,074` |
| `2026-11-16 10:00` | `$64,327.77` | `$64,697.20` | `$64,290.00` | `$64,574.83` | `+0.38%` | `731` |
| `2026-11-16 09:00` | `$64,464.95` | `$64,540.01` | `$64,128.00` | `$64,327.77` | `-0.21%` | `841` |
| `2026-11-16 08:00` | `$64,995.13` | `$64,995.28` | `$64,430.00` | `$64,464.95` | `-0.82%` | `523` |
| `2026-11-16 07:00` | `$64,709.81` | `$65,078.01` | `$64,426.93` | `$64,995.12` | `+0.44%` | `721` |
| `2026-11-16 06:00` | `$64,474.70` | `$64,758.01` | `$64,294.11` | `$64,709.81` | `+0.36%` | `751` |

### 7C. MODELED LIQUIDATION LADDER (`10x-100x`) & USD MACRO CALENDAR
**6-Tier Modeled Liquidation Ladder:**
| Tier | Side | Level ($) | Dist% | Est Pool ($M) |
|---|---|---|---|---|
| `10x Shorts` | `UPPER` | `$67,685.16` | `+4.32%` | `$102.2M` |
| `25x Shorts` | `UPPER` | `$66,684.89` | `+2.77%` | `$136.3M` |
| `50-100x Shorts` | `UPPER` | `$66,024.64` | `+1.76%` | `$193.8M` |
| `100x Longs` | `LOWER` | `$63,717.08` | `-1.80%` | `$350.0M` |
| `25x Longs` | `LOWER` | `$63,079.91` | `-2.78%` | `$315.2M` |
| `10x Longs` | `LOWER` | `$62,133.71` | `-4.24%` | `$220.7M` |

**Upcoming USD High-Impact Macro Events (`-60m` to `+7d`):**
| Event | Time (UTC) | Countdown | Forecast | Previous |
|---|---|---|---|---|
| `Core Retail Sales m/m` | `2026-11-17T13:30:00Z` | `in 19.3h` | `0.4%` | `0.9%` |
| `Retail Sales m/m` | `2026-11-17T13:30:00Z` | `in 19.3h` | `0.2%` | `0.8%` |
| `FOMC Meeting Minutes` | `2026-11-18T19:00:00Z` | `in 48.8h` | `-` | `-` |

## 8. METRIC FORMULA LEGEND & CORTEX DESK LITE PROTOCOL
- **Rough Path Lévy (`4H A_SP`)**: Lévy signed area over 6 closed 4H bars (`> 0`: Spot path leads price markup; `< 0`: Spot path lags price / distribution).
- **24H Z-Scores (`z_S / z_F / D`)**: 30-day rolling Z-scores of 24H Spot (`z_S`) and Perp (`z_F`) cumulative delta; `D = z_S - z_F` (`D > 0` = Spot buying divergence vs Perps).
- **Spot CVD Slopes (`7D / 14D`) & 4H Vol Context**: Cumulative spot taker-delta over last `7`/`14` closed `1D` bars; `4H ATR(14)% Pctile` ranks current closed `4H` ATR% against the trailing `120` closed `4H` bars, paired with `RelVol(20)` (`closed 4H volume / 20-bar SMA`).
- **Volume Profile & Structure**: `30D VA Pos% = (Spot - VAL) / (VAH - VAL) * 100` (Macro 30D Value Area); `ATR(14) 1D/4H/1H`; `L20/H20` = 20-bar (80H) 4H range boundaries; `SLSP` = structural liquidity pool S/R; `7A` scans up to 500 closed bars per TF (`1D ~499d`, `4H ~83d`, `1H ~21d`) using `5x5` pivots for `HH/HL/LH/LL`, `BOS`, and `1%`-clustered S/R zones (deep prior-quarter supports appear on `1D` even if outside the `83d` `4H` window).
- **Derivatives, Modeled Ladder & Quant**: `90D Pct` = 0-100 rolling 90-day percentile rank of 8H funding; `[... X/3 PARTIAL_VENUE]` suppresses OI quadrant tagging when `<3` venues report; `Hyperliquid Perp` reports DEX OI and 8H-normalized funding independently; `Modeled Liq Ladder (7C)` estimates 10x-100x leverage shelves (not private exchange orderbooks); `USD Macro Calendar` tracks high-impact USD releases; `H` = Hurst exponent (`>0.5` trending, `<0.5` mean-reverting); `VCR 72H` = Volatility Compression Ratio; `TSFM Disp%` = horizon dispersion; `LSCE` = liquidation sweep state.
- **Headless Snapshot Note**: Scheduled/GitHub Actions runs execute a one-shot REST warmup (`Warm:YES`) without a persistent WebSocket loop, so `WebSocket Feeds & Warmup` reporting `STALE` (`no tick`) is isolated in `Coverage` as `Expected_Headless_WS_Offline=1` and does not indicate stale REST, orderbook, CVD, or derivatives data.

### DIRECT AI EXECUTION PROTOCOL: CORTEX BTC DESK LITE v1.0
Analyze BTC using the telemetry snapshot above. Operate as **CORTEX BTC DESK LITE v1.0** — a Spot-Only Institutional Capital Preservation & Swing Execution Workstation. Apply strict **zero-hallucination** rules using only metrics explicitly reported above (`0`, `1-6`, `7`, `7A`, `7B`, `7C`).

**Gate 0 — HARD DOWNTREND MARKET VETO (EVALUATE FIRST, BEFORE ALL OTHER SIGNALS):**
- Verify Section `0` (`HARD DOWNTREND MARKET VETO`) BEFORE scoring RSI, MACD, lower-timeframe setups, or liquidation clusters.
- **Rule Conditions (`Condition A AND Condition B`):**
  - `Condition A`: Latest settled closed `1D` candle closes strictly below `1D SMA 200` (both computed from the same completed Binance Spot `1D` candle series; no live forming candle mixing).
  - `Condition B`: Closed `4H` market structure is `DOWNTREND` **OR** `4H Downside BOS Status` is `YES` (`BOS Down`).
- **Fail-Closed Rule (`UNDETERMINED`):** If either `Condition A` or `Condition B` is `UNAVAILABLE` (missing closed `1D` close, `< 200` closed `1D` bars for `1D SMA 200`, or insufficient closed `4H` data), DO NOT assume `INACTIVE` — set `Veto Status: UNDETERMINED`, `Portfolio Status: 100% USDT CASH`, and `New BTC Entry: PROHIBITED` until data is verified.
- **Mandatory Enforcement when `ACTIVE` (or `UNDETERMINED`):** Enforce `Portfolio Status: 100% USDT CASH` and `New BTC Entry: PROHIBITED`. No dip-buying and no averaging down. Lower-timeframe `UPTREND` bounces, oversold `RSI`, positive `1H` MACD crossovers, or upside liquidation clusters MUST NOT override this veto. (**Entry-protection only:** this rule MUST NOT automatically trigger selling existing BTC spot holdings; separate BTC-to-USDT exit rules govern open positions.)
- **Veto Removal Conditions:** Lift `ACTIVE` only when ALL recovery requirements are independently verified on closed candles (never inferred from a temporary intraday rebound): (1) a settled closed `1D` candle closes above `1D SMA 200` computed from the same completed `1D` series, AND (2) closed `4H` structure independently improves to `UPTREND (HH/HL)` with no active downside BOS, AND (3) subsequent `Step 2` full-market reassessment validates supporting spot-flow demand (`ELIGIBLE FOR FULL ASSESSMENT` permits evaluation, never an automatic buy). Section `5` `Legacy_200D_Veto_Override` is permanently `IGNORED` for Desk Lite.

**Step 1 — Mandatory Data Hygiene Gate:**
- Verify `Coverage` distinguishing: (a) genuine stale market data (`Genuine=...`), (b) expected headless WS inactivity (`Expected_Headless_WS_Offline=...` when `Warm:YES` REST-only run), (c) `[PROXY]` feeds, and (d) `UNAVAILABLE` feeds.
- Never treat expected headless WebSocket inactivity (`Expected_Headless_WS_Offline=1`) as a genuine REST/derivatives/orderbook market-data failure.
- Flag `[... PARTIAL_VENUE]` on `Cross-Exch Perp OI & Funding` or Section `7` history — never treat partial venue counts (`< 3/3`) as genuine deleveraging.
- Read `90D Pct` strictly as a `0-100` rolling 90-day funding rank, `30D VA Pos%` strictly vs Macro 30D VAH/VAL, `ATR(14) 1D/4H/1H` across matching timeframes, and treat `Modeled Liq Ladder (7C)` as an algorithmic estimate (not private orderbook depth).
- Check `USD Macro Calendar (High)`: treat `NONE (next 7d)` as a clear schedule (`OK`) vs `UNAVAILABLE` as offline.
- Do not cite missing metrics or external prices outside this telemetry snapshot.

**Step 2 — 5-Function Deterministic Synthesis:**
1. **Multi-Timeframe Regime Classifier:** Integrate Section `1`, `7A` (`1D/4H/1H` swing structure & BOS), `7B` closed OHLCV price action, `1D/4H` ADX, `RSI(14)`, `4H ATR(14)% Pctile` & `RelVol(20)` (volatility regime & volume participation), EMA/SMA stack, and Hurst `H` -> classify as `UPTREND`, `DOWNTREND`, `RANGE-BOUND`, or `TRANSITIONAL`.
2. **Spot Flow & Liquidity Inspector:** Evaluate `Spot/Perp CVD` across `15m/1h/4h/24h`, multi-day `Spot CVD Slopes (7D / 14D)`, `z_S / z_F / D`, `Coinbase Premium`, `L2 Depth`, `OBI`, `Spr`, `30D VA Pos%`, `SLSP`, and `7A` S/R clusters -> classify true spot accumulation vs distribution or passive absorption.
3. **Derivatives & Squeeze Risk Profiler:** Evaluate `BN OI`, `Cross-Exch OI` (only when `3/3` venues valid), `Hyperliquid Perp OI & Funding` (`[HL DEX]` vs CEX positioning), `OI Δ%` & Quad, `Funding 8H% / Ann% / 90D Pct`, `DVOL`, `25d RR Skew`, and `6-Tier Modeled Liq Ladder (7C)` (`10x-100x` upper/lower distance & `$M` asymmetry) -> classify leverage fragility and squeeze asymmetry.
4. **Macro, On-Chain & ETF Gatekeeper:** Synthesize `MVRV`, `SOPR`, Farside `US Spot ETF Flow (1D / 3D / 5D)` (use `IBIT+FBTC` `[PROXY]` only as secondary context), `Stablecoin Supply`, `DXY`, `US10Y`, `VIX`, `SPX`, `Net Liquidity`, and `USD Macro Calendar (High)` (`7C` event proximity within `24h` or `±30m` high-impact windows) -> assign macro backdrop (`Tailwind`, `Neutral`, or `Headwind`).
5. **Spot-Only Risk & Decision Arbiter:** Respect `Gate 0` (`HARD DOWNTREND MARKET VETO`) first: if `ACTIVE` or `UNDETERMINED`, hold `100% USDT CASH` with `New BTC Entry: PROHIBITED` (entry-protection only; do not auto-sell existing BTC holdings). Only when `Veto Status` is `INACTIVE` may you evaluate spot longs; still never force an entry in chop (`ADX < 20` or `TRANSITIONAL`) or inside `< 24h` high-impact USD macro event risk, and cap maximum portfolio risk at `0.75%` per qualified spot position.

**Step 3 — Mandatory Output Contract:**
- **0. HARD DOWNTREND MARKET VETO** (`Veto Status: ACTIVE / INACTIVE / UNDETERMINED`, `Condition A (1D below SMA 200): YES / NO / UNAVAILABLE`, `Condition B (4H downside structure): YES / NO / UNAVAILABLE`, `Portfolio Status: 100% USDT CASH / NORMAL ASSESSMENT REQUIRED`, `New BTC Entry: PROHIBITED / ELIGIBLE FOR FULL ASSESSMENT`).
- **1. EXECUTIVE SUMMARY & DESK POSTURE** (Spot Price, Regime State, Posture: `ACTIVE SPOT LONG` or `100% USDT CASH — NO ENTRY`, Confidence `/100`).
- **2. DATA HYGIENE AUDIT** (Exact `OK/UNAVAILABLE/STALE/PROXY` tally, headless WS clarification, any `PARTIAL_VENUE` anomalies, degraded-signal list).
- **3. MULTI-TIMEFRAME REGIME & FLOW SYNTHESIS** (Price/EMA/ADX + `4H ATR% Pctile / RelVol` structure vs intraday & `7D/14D` Spot CVD, Coinbase Premium, and 4H SQLite Section `7` + `7A/7B` trajectory).
- **4. DERIVATIVES, LIQUIDITY & MACRO CONTEXT** (CEX `3/3` + `Hyperliquid DEX` OI/funding, funding `90D Pct`, options skew, `6-tier Liq Ladder (7C)`, Farside `1D/3D/5D` ETF flows, `USD Macro Calendar (7C)` event window, and macro backdrop).
- **5. CRITICAL LEVELS MAP** (Immediate & Major Support, Immediate & Major Resistance, `7C` modeled liquidation shelves, and Hard Invalidation Levels tied to `7A/7B` & `SLSP`).
- **6. SPOT EXECUTION PLAN (OR NO-ENTRY GATE)** (Exact Entry Zone or `NO ENTRY — VETO ACTIVE/UNDETERMINED`, Stop Loss, Take Profit Targets, Position Size at `<= 0.75%` portfolio risk, event-window timing constraints, and explicit Multi-Gate Validation Triggers required to shift posture).
