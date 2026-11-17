# TAB [D: DATA HUB] | CONSOLIDATED DATA-ONLY TELEMETRY REPORT
**Retrieval Time (UTC):** `2026-11-17 04:04:14 UTC`  |  **Retrieval Time (SGT):** `2026-11-17 12:04:14 SGT (UTC+8)`
**Spot Price (BTCUSDT):** `$64,973.33`  |  **Coverage:** `OK=67/71 | UNAVAILABLE=2 | STALE=1 (Genuine=0, Expected_Headless_WS_Offline=1) | PROXY/STATIC=1`
**24H Range:** `$63,905.01 - $65,696.16`  |  **Returns (24H / 7D / 30D):** `+0.23% / -11.96% / -20.88%`
**Archive (SQLite):** `14 closed-4H snapshots (Last: 2026-11-17 04:00:00 UTC)`

## 0. HARD DOWNTREND MARKET VETO (PRE-ENTRY CAPITAL PRESERVATION GATE)
| Gate Field | Value | Rule / Threshold |
|---|---|---|
| Latest Closed 1D Candle Close | `$64,882.87 (1D bar 2026-11-16 · closed 2026-11-17 00:00 UTC)` | `Same closed Binance Spot 1D series only (live candle excluded)` |
| Current 1D SMA 200 | `$72,921.15` | `200-bar SMA of same closed Binance Spot 1D series` |
| Distance vs 1D SMA 200 | `-11.02% (-$8,038.28)` | `(Closed 1D Close - 1D SMA 200) / 1D SMA 200` |
| 1D SMA 200 Position | `BELOW` | `BELOW if Closed 1D Close < 1D SMA 200 else ABOVE` |
| Closed 4H Market Structure (`7A`) | `DOWNTREND (LH/LL)` | `UPTREND / DOWNTREND / MIXED (500 closed 4H bars)` |
| 4H Downside BOS Status (`7A`) | `YES (BOS Down < $72,727.27 (11-12 12:00))` | `YES if latest closed 4H BOS is BOS Down else NO` |
| Timestamp & Candle Closed Status | `2026-11-17 04:04:14 UTC | 2026-11-17 12:04:14 SGT (UTC+8) · Closed-Candle Inputs Only` | `Strict closed-bar verification gate` |

**HARD DOWNTREND MARKET VETO STATUS:**
- **Veto Status:** `ACTIVE`
- **Condition A (Closed 1D Close < 1D SMA 200):** `YES`
- **Condition B (4H Downside Structure / BOS Down):** `YES`
- **Portfolio Status:** `100% USDT CASH`
- **New BTC Entry:** `PROHIBITED`

## 1. PRICE, TREND & MARKET STRUCTURE
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| Binance Spot / Perp ($) | `$64,973.33 / $64,942.40` | `All Tabs` | `OK` |
| Coinbase Spot ($) | `$64,907.49` | `1,11,15,17` | `OK` |
| 1D SMA 200 / Slope | `$72,921.15 (-0.34%)` | `0,2,3,11,15,18` | `OK` |
| 1D SMA 50 / EMA 50 | `$79,451.99 / $76,233.15` | `0,2,4,15,18,20` | `OK` |
| 1D EMA 21 / 1W EMA 50 | `$72,616.07 / $77,795.19` | `3,18` | `OK` |
| 4H EMA 50 / EMA 200 | `$69,142.64 / $75,665.84` | `7,13,18,20` | `OK` |
| Grok EMA 9/21 & 1H SMA200 | `9:$64,885.48 · 21:$64,866.34 · 1H:$70,034.08` | `5,15` | `OK` |
| Daily / Weekly VWAP (Z) | `D:$64,705.56 (+1.65σ) | W:$68,184.24` | `4,11,15` | `OK` |
| RSI(14) 1D / 4H & 4H ROC12 | `1D:24.1 · 4H:36.4 · ROC:+0.36%` | `3,7,20` | `OK` |
| ADX(14) 1D/4H & ATR(14) 1D/4H/1H | `ADX 1D:36.6 4H:56.8 | ATR:$2,628.90/$1,237.54/$503.89` | `0,1,2,8,13,18,20` | `OK` |
| 4H ATR(14)% Pctile & RelVol(20) | `ATR%:1.92% (89th pct/120b) · RelVol:0.76x` | `0,1,2,20` | `OK` |
| Macro 30D VAH / POC / VAL | `$83,276.48 / $80,605.75 / $73,356.62` | `1,3,6,11,19` | `OK` |
| Structure (L20/H20, PW, Asia) | `4H:$62,006.00-$81,971.00 | PW:$62,006.00-$75,599.22 | Asia:$64,385.99-$65,200.00` | `0,8,11,19` | `OK` |

## 2. ORDER FLOW, FOOTPRINT & LIQUIDITY
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| Spot/Perp CVD (15m / 1h) | `15m:-6.7/+14.7 | 1h:+103.6/-42.1 BTC` | `1,8,15` | `OK` |
| Spot/Perp CVD (4h / 24h) | `4h:+248.0/+211.1 | 24h:+1113.5/+957.4 BTC` | `0,1,15,16,17` | `OK` |
| Spot CVD Slopes (7D / 14D) | `7D:-4,899.1 BTC | 14D:-3,515.9 BTC` | `17` | `OK` |
| Session / UTC-Day CVD | `Sess S:+0.0 P:+0.0 | Day S:+266.9 P:+55.8` | `REST 15m` | `OK` |
| 24H Z-Scores (z_S / z_F / D) | `z_S:+0.70 · z_F:+0.72 · D:-0.02` | `1,19` | `OK` |
| 15m Footprint Delta / Stack | `Δ:-6.7 BTC (Prev:+16.0) · Stacks:0` | `1,11` | `OK` |
| Coinbase Premium ($ / % / Z) | `-65.8$ (-0.101%, Z=-0.09)` | `1,11,15` | `OK` |
| Cross-Exch 24H Spot Vol (BN/CB) | `BN:20,825 · CB:13,418 · Tot:34,243 BTC` | `1,11,Macro` | `OK` |
| L2 Depth ±1%/±2%, OBI & Spread | `1%:0.97x · 2%:1.65x · Spr:0.0015bps · OBI:-1.5%` | `16,Macro` | `OK` |
| Tactical 7D / Session 24H VP | `7D:$70,611.88/$64,982.88/$62,384.88 | 24H:$65,114.04/$64,576.69/$64,457.28` | `1,11` | `OK` |
| 30D VA Pos% & Dist to VAL | `-84.5% | -11.43% (-16.64 ATR)` | `1` | `OK` |
| SLSP Support / Resistance | `Sup:$64,742.09 | Res:$65,575.31` | `13` | `OK` |

## 3. DERIVATIVES, OPTIONS & LIQUIDATIONS
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| BN Open Interest (BTC / USD) | `93,130 BTC ($6.04B)` | `0,1,4,15,17` | `OK` |
| Cross-Exch Perp OI & Funding | `160,075 BTC ($10.39B) · F:+0.0054% [BN+BYB+OKX 3/3]` | `Macro,15` | `OK` |
| Hyperliquid Perp OI & Funding | `37,732 BTC ($2.45B) · F:+0.0061% [HL DEX]` | `Macro,15` | `OK` |
| OI Δ% (15m/1h/4h/24h) & Quad | `+0.02%/-0.42%/+0.02%/-6.59% | SHORT_COVERING_BOUNCE (Price Up / OI Down)` | `1,4,8,11,12,15,17` | `OK` |
| Funding 8H% / Ann% / 90D Pct | `+0.0048% (+5.2%/yr) · 90D Pct:37.4%` | `0,4,9,11,15,16,19,20` | `OK` |
| Perp Basis ($ / Ann %) | `-30.9$ (-0.048% | Carry:+4.60%/yr)` | `1,4` | `OK` |
| 5m Taker L/S & Top/Glb Acct | `5m:1.317 (Δ:+9.8) | Top:1.64(62L) · Glb:2.62` | `1,2,15,16` | `OK` |
| Options OI & Put/Call (Deribit) | `P/C:0.773 · TotOI:388,985 BTC` | `Macro,19` | `OK` |
| Options IV Term & Skew (Deribit) | `F:42.9% · B:40.9% · 25dSk:+6.0%` | `Macro,6,19` | `OK` |
| Vol: DVOL, RV20, GK & BBW% | `DVOL:43.7 · RV20:48.4% · GK:73.8% · BBW:86% · Sk20:-0.40` | `0,4,6,16,19` | `OK` |
| Upper / Lower Liq Magnet | `Up:$76,334.44 | Dn:$63,803.81` | `0,2,13,17` | `OK` |
| Magnet Ratios & LSCE | `Imm:1.81x · Ladder:1.79x · Pull:0.55x · LSCE:UNTESTED` | `13,17` | `OK` |
| Modeled Liq Ladder (10x-100x) | `Up[10x:$67,685.16($102M) / 25x:$66,684.89($136M) / 50-100x:$66,024.64($194M)] | Dn[100x:$63,803.81($350M) / 25x:$63,138.15($314M) / 10x:$62,191.08($220M)] [Modeled]` | `17` | `OK` |
| Liquidations (1H / 24H) & Flush | `DATA UNAVAILABLE` | `0,8,12,13` | `UNAVAILABLE` |

## 4. ON-CHAIN, ETF & STABLECOIN FLOWS
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| MVRV Ratio (On-Chain / Proxy) | `1.212 [CoinMetrics 2026-11-16]` | `Macro,16` | `OK` |
| On-Chain SOPR / aSOPR | `DATA UNAVAILABLE` | `16` | `UNAVAILABLE` |
| Exchange Netflow 24H (CM) | `Net:+2,561.0 BTC (+$166.3M) | In:28,743 Out:26,182` | `Macro,16` | `OK` |
| BTC Exchange Reserves (CM) | `2,711,617 BTC (2026-11-16)` | `Macro,16` | `OK` |
| Stablecoins USDT+USDC Supply | `$244.70B (USDT:$175.24B · USDC:$69.46B)` | `Macro` | `OK` |
| Stablecoin Net Issuance (7D/30D) | `7D:-1.96B · 30D:-11.29B` | `Macro` | `OK` |
| US Spot ETF Flow (Farside 1D/3D) | `1D:-$68.6M | 3D:-$538.1M | 5D:-$932.9M` | `2,13` | `OK` |
| US ETF Tape Proxy (IBIT+FBTC) | `1DVol:$2.56B · 5D:-$7.25B [PROXY]` | `Macro,2,13` | `PROXY` |
| Power-Law Fair & ATH DD% | `$149,498.69 (-56.5%) | DD:-48.5%` | `3` | `OK` |
| MTF MACD (1D / 1H Status) | `1D=negative_slope (Macro Whipsaw Veto) | 1H=positive_slope CROSS` | `13,16,18` | `OK` |

## 5. MACRO, CREDIT & US LIQUIDITY
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| US SOFR Rate & Vol (NY Fed) | `3.90% (Vol:$3,092B)` | `Macro` | `OK` |
| Fed ON RRP Balance (NY Fed) | `$0.18B` | `Macro` | `OK` |
| Credit Spread HYG/LQD & 5D% | `0.7464 (+0.79% 5D)` | `Macro,3` | `OK` |
| DXY / US 10Y (^TNX) | `103.52 (RISING (+0.61 over 5d)) | 10Y:5.12%` | `3,13` | `OK` |
| TIPS Real (DFII10) / BEI | `Real:+2.92% | BEI:2.20%` | `3,13` | `OK` |
| S&P 500 / Nasdaq (1D%) | `SPX:7,417 (-1.92%) | NDX:24,510` | `3,13` | `OK` |
| VIX / Brent Crude (BZ=F) | `VIX:22.91 | Brent:$91.58` | `3,13` | `OK` |
| BTC-SPX Corr (20D / 60D) | `20D:+0.48 | 60D:+0.50` | `3` | `OK` |
| Fear & Greed / BTC Dom% | `F&G:12 (Extreme Fear) | Dom:58.50%` | `3,13` | `OK` |
| USD Macro Calendar (High) | `Core Retail Sales m/m (in 9.4h Fc:0.4%) | Retail Sales m/m (in 9.4h Fc:0.1%) (+1 more)` | `Macro` | `OK` |
| Manual Context Overrides | `Legacy_200D_Veto_Override: IGNORED (Tab1_Flag=False) · Filter=NONE_SIGNIFICANT` | `2,13` | `OK` |

## 6. QUANT FEATURES, FEED HEALTH & ARCHIVE
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| Rough Path Lévy (A_SP / MM) | `4H A_SP:+2.6877 | MM PriceFlow:+0.0009 · Rough:4.180` | `5,19` | `OK` |
| Hurst / Kalman Vel / FracDiff | `H:0.753 · KVel:-63.70 · d:0.20` | `5,6` | `OK` |
| Hilbert Cycle / TD9 / TellTale | `Cyc:72.0b · TD(1H/4H):2/2 · RV(15m/5m):0.12/N/A` | `5,9,13` | `OK` |
| VCR 72H & TSFM Disp% | `VCR:15.63 | Disp:1.28%` | `6` | `OK` |
| Open FVGs & Sweep FSM | `FVGs:4 | FSM:None (0/12)` | `1,8` | `OK` |
| WebSocket Feeds & Warmup | `Spot:SYNC (no tick) | Perp:SYNC (no tick) | CB:SYNC (11s ago) | Warm:YES` | `Live Feeds` | `STALE` |
| Spot Klines (1W/1D/4H/1H/15m) | `1W:100 1D:500 bars · 11-17 00:00 UTC | 4H:500 1H:720 15m:240` | `All Tabs` | `OK` |
| Perp Klines / Est. Excluded | `1D:101 · 1H:720 · 15m:240 (Excl=399)` | `1,4,11,15,19` | `OK` |
| Closed 4H Anchor (Tab 19/20) | `2026-11-17 04:00:00 UTC` | `18,19,20` | `OK` |
| B1/B2 Rec & Companion Liq | `Rec:PASS (0s delta) | Liq:N/A` | `8,13,17` | `OK` |
| Telemetry History Archive (SQLite) | `14 bars logged (Last: 2026-11-17 04:00:00 UTC)` | `DB Archive` | `OK` |

## 7. RECENT CLOSED-4H SNAPSHOT TRAJECTORY (SQLITE ARCHIVE)
| Closed 4H Bar (UTC) | Spot ($) | 24H Spot/Perp CVD | Cross-Exch Perp OI & Funding | Funding 8H% / 90D Pct | MVRV Ratio |
|---|---|---|---|---|---|
| `2026-11-17 04:00:00 UTC` | `$64,973.33` | `24h:+1113.5/+957.4 BTC` | `160,075 BTC ($10.39B) · F:+0.0054% [BN+BYB+OKX 3/3]` | `+0.0048% (+5.2%/yr) · 90D Pct:37.4%` | `1.212 [CoinMetrics 2026-11-16]` |
| `2026-11-17 00:00:00 UTC` | `$64,629.18` | `24h:+995.2/+491.3 BTC` | `158,085 BTC ($10.23B) · F:+0.0049% [BN+BYB+OKX 3/3]` | `+0.0037% (+4.1%/yr) · 90D Pct:37.4%` | `1.214 [CoinMetrics 2026-11-15]` |
| `2026-11-16 16:00:00 UTC` | `$64,885.01` | `24h:-448.1/-157.3 BTC` | `159,896 BTC ($10.36B) · F:+0.0076% [BN+BYB+OKX 3/3]` | `+0.0079% (+8.6%/yr) · 90D Pct:54.1%` | `1.214 [CoinMetrics 2026-11-15]` |
| `2026-11-16 08:00:00 UTC` | `$64,644.70` | `24h:-2105.7/-1447.0 BTC` | `161,580 BTC ($10.43B) · F:+0.0017% [BN+BYB+OKX 3/3]` | `+0.0007% (+0.8%/yr) · 90D Pct:5.9%` | `1.214 [CoinMetrics 2026-11-15]` |
| `2026-11-16 04:00:00 UTC` | `$64,925.69` | `24h:-2000.7/-2017.8 BTC` | `160,648 BTC ($10.42B) · F:-0.0001% [BN+BYB+OKX 3/3]` | `+0.0000% (+0.1%/yr) · 90D Pct:3.3%` | `1.214 [CoinMetrics 2026-11-15]` |
| `2026-11-16 00:00:00 UTC` | `$65,096.00` | `24h:-2825.0/+2036.9 BTC` | `160,961 BTC ($10.50B) · F:+0.0001% [BN+BYB+OKX 3/3]` | `-0.0012% (-1.3%/yr) · 90D Pct:3.3%` | `1.188 [CoinMetrics 2026-11-14]` |

### 7A. 500-BAR MARKET STRUCTURE & HISTORICAL S/R ZONES (`1D / 4H / 1H`)
| TF (Bars) | Swing Structure | Last Swing Pivots | Latest BOS | Resistance Zones (Above Spot) | Support Zones (Below Spot) |
|---|---|---|---|---|---|
| `1D (499)` | `DOWNTREND (LH/LL)` | `SH:$81,196.01 (11-04) · SL:$79,800.00 (10-15)` | `BOS Down < $79,800.00 (10-29)` | `$65,182.19 (5x), $67,124.15 (2x), $70,983.00 (1x)` | `$62,440.17 (3x), $60,000.00 (1x), $59,130.91 (1x)` |
| `4H (499)` | `DOWNTREND (LH/LL)` | `SH:$74,811.45 (11-11 20:00) · SL:$62,006.00 (11-15 00:00)` | `BOS Down < $72,727.27 (11-12 12:00)` | `$72,727.27 (1x), $73,510.00 (1x), $75,173.28 (6x)` | `$62,006.00 (1x)` |
| `1H (500)` | `DOWNTREND (LH/LL)` | `SH:$65,534.94 (11-16 22:00) · SL:$63,905.01 (11-16 12:00)` | `BOS Down < $66,456.00 (11-14 14:00)` | `$65,693.55 (5x), $66,456.00 (1x), $67,731.35 (3x)` | `$64,081.33 (2x), $62,006.00 (1x)` |

### 7B. RECENT CLOSED KLINES — OHLCV PRICE ACTION (`1D`×7, `4H`×12, `1H`×12)
**1D Closed Candles (Last 7 of 499 available, Newest First):**
| Open Time (UTC) | Open | High | Low | Close | Chg% | Vol (BTC) |
|---|---|---|---|---|---|---|
| `2026-11-16` | `$65,351.05` | `$65,696.16` | `$63,905.01` | `$64,882.87` | `-0.72%` | `21,929` |
| `2026-11-15` | `$64,150.01` | `$66,132.01` | `$62,006.00` | `$65,351.05` | `+1.87%` | `29,231` |
| `2026-11-14` | `$68,314.01` | `$68,446.21` | `$63,320.00` | `$64,150.00` | `-6.10%` | `32,675` |
| `2026-11-13` | `$71,460.00` | `$71,514.01` | `$67,568.00` | `$68,314.00` | `-4.40%` | `29,649` |
| `2026-11-12` | `$74,015.20` | `$74,217.49` | `$71,113.06` | `$71,460.00` | `-3.45%` | `15,228` |
| `2026-11-11` | `$73,796.06` | `$74,811.45` | `$73,209.12` | `$74,015.19` | `+0.30%` | `16,146` |
| `2026-11-10` | `$75,368.41` | `$75,442.01` | `$72,727.27` | `$73,796.06` | `-2.09%` | `16,466` |

**4H Closed Candles (Last 12 of 499 available, Newest First):**
| Open Time (UTC) | Open | High | Low | Close | Chg% | Vol (BTC) |
|---|---|---|---|---|---|---|
| `2026-11-17 00:00` | `$64,882.88` | `$65,200.00` | `$64,385.99` | `$65,056.52` | `+0.27%` | `3,319` |
| `2026-11-16 20:00` | `$65,068.00` | `$65,534.94` | `$64,788.11` | `$64,882.87` | `-0.28%` | `3,028` |
| `2026-11-16 16:00` | `$64,467.00` | `$65,190.08` | `$64,228.01` | `$65,068.01` | `+0.93%` | `4,001` |
| `2026-11-16 12:00` | `$64,448.32` | `$65,696.16` | `$63,905.01` | `$64,467.00` | `+0.03%` | `4,865` |
| `2026-11-16 08:00` | `$64,995.13` | `$64,995.28` | `$64,128.00` | `$64,448.32` | `-0.84%` | `3,169` |
| `2026-11-16 04:00` | `$65,113.93` | `$65,190.00` | `$64,294.11` | `$64,995.12` | `-0.18%` | `3,052` |
| `2026-11-16 00:00` | `$65,351.05` | `$65,392.01` | `$64,530.12` | `$65,113.92` | `-0.36%` | `3,814` |
| `2026-11-15 20:00` | `$64,947.43` | `$65,508.86` | `$64,700.00` | `$65,351.05` | `+0.62%` | `2,895` |
| `2026-11-15 16:00` | `$64,748.30` | `$65,230.23` | `$64,257.65` | `$64,947.43` | `+0.31%` | `3,108` |
| `2026-11-15 12:00` | `$65,351.00` | `$65,800.75` | `$64,456.01` | `$64,748.30` | `-0.92%` | `3,212` |
| `2026-11-15 08:00` | `$64,012.59` | `$66,132.01` | `$63,873.26` | `$65,351.00` | `+2.09%` | `5,254` |
| `2026-11-15 04:00` | `$64,826.00` | `$65,169.23` | `$63,777.00` | `$64,012.60` | `-1.25%` | `3,302` |

**1H Closed Candles (Last 12 of 719 available, Newest First):**
| Open Time (UTC) | Open | High | Low | Close | Chg% | Vol (BTC) |
|---|---|---|---|---|---|---|
| `2026-11-17 03:00` | `$64,503.63` | `$65,200.00` | `$64,484.79` | `$65,056.52` | `+0.86%` | `647` |
| `2026-11-17 02:00` | `$64,746.71` | `$64,879.48` | `$64,385.99` | `$64,503.63` | `-0.38%` | `679` |
| `2026-11-17 01:00` | `$64,632.26` | `$64,932.40` | `$64,537.52` | `$64,746.72` | `+0.18%` | `1,048` |
| `2026-11-17 00:00` | `$64,882.88` | `$64,932.04` | `$64,454.54` | `$64,632.25` | `-0.39%` | `944` |
| `2026-11-16 23:00` | `$65,319.64` | `$65,360.07` | `$64,788.11` | `$64,882.87` | `-0.67%` | `905` |
| `2026-11-16 22:00` | `$65,302.46` | `$65,534.94` | `$65,298.00` | `$65,319.65` | `+0.03%` | `784` |
| `2026-11-16 21:00` | `$65,068.58` | `$65,421.05` | `$64,956.00` | `$65,302.46` | `+0.36%` | `556` |
| `2026-11-16 20:00` | `$65,068.00` | `$65,229.09` | `$64,905.39` | `$65,068.57` | `+0.00%` | `783` |
| `2026-11-16 19:00` | `$65,052.01` | `$65,094.01` | `$64,768.46` | `$65,068.01` | `+0.02%` | `1,533` |
| `2026-11-16 18:00` | `$64,912.61` | `$65,190.08` | `$64,716.00` | `$65,052.00` | `+0.21%` | `870` |
| `2026-11-16 17:00` | `$64,927.21` | `$65,150.00` | `$64,799.00` | `$64,912.62` | `-0.02%` | `656` |
| `2026-11-16 16:00` | `$64,467.00` | `$64,949.21` | `$64,228.01` | `$64,927.22` | `+0.71%` | `942` |

### 7C. MODELED LIQUIDATION LADDER (`10x-100x`) & USD MACRO CALENDAR
**6-Tier Modeled Liquidation Ladder:**
| Tier | Side | Level ($) | Dist% | Est Pool ($M) |
|---|---|---|---|---|
| `10x Shorts` | `UPPER` | `$67,685.16` | `+4.17%` | `$101.9M` |
| `25x Shorts` | `UPPER` | `$66,684.89` | `+2.63%` | `$135.9M` |
| `50-100x Shorts` | `UPPER` | `$66,024.64` | `+1.62%` | `$193.8M` |
| `100x Longs` | `LOWER` | `$63,803.81` | `-1.80%` | `$350.0M` |
| `25x Longs` | `LOWER` | `$63,138.15` | `-2.82%` | `$314.2M` |
| `10x Longs` | `LOWER` | `$62,191.08` | `-4.28%` | `$220.0M` |

**Upcoming USD High-Impact Macro Events (`-60m` to `+7d`):**
| Event | Time (UTC) | Countdown | Forecast | Previous |
|---|---|---|---|---|
| `Core Retail Sales m/m` | `2026-11-17T13:30:00Z` | `in 9.4h` | `0.4%` | `0.9%` |
| `Retail Sales m/m` | `2026-11-17T13:30:00Z` | `in 9.4h` | `0.1%` | `0.8%` |
| `FOMC Meeting Minutes` | `2026-11-18T19:00:00Z` | `in 38.9h` | `-` | `-` |

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
