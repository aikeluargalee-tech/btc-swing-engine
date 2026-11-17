# TAB [D: DATA HUB] | CONSOLIDATED DATA-ONLY TELEMETRY REPORT
**Retrieval Time (UTC):** `2026-11-17 05:25:20 UTC`  |  **Retrieval Time (SGT):** `2026-11-17 13:25:20 SGT (UTC+8)`
**Spot Price (BTCUSDT):** `$65,011.70`  |  **Coverage:** `OK=67/71 | UNAVAILABLE=2 | STALE=1 (Genuine=0, Expected_Headless_WS_Offline=1) | PROXY/STATIC=1`
**24H Range:** `$63,905.01 - $65,696.16`  |  **Returns (24H / 7D / 30D):** `+0.83% / -11.90% / -20.83%`
**Archive (SQLite):** `14 closed-4H snapshots (Last: 2026-11-17 04:00:00 UTC)`

## 0. BIDIRECTIONAL REGIME ROUTER (GATE 0 — DUAL-INVENTORY SPOT WORKSTATION)
| Router Field | Value | Rule / Threshold |
|---|---|---|
| Latest Closed 1D Candle Close | `$64,882.87 (1D bar 2026-11-16 · closed 2026-11-17 00:00 UTC)` | `Same closed Binance Spot 1D series only (live candle excluded)` |
| Current 1D SMA 200 | `$72,921.15` | `200-bar SMA of same closed Binance Spot 1D series` |
| Distance vs 1D SMA 200 | `-11.02% (-$8,038.28)` | `(Closed 1D Close - 1D SMA 200) / 1D SMA 200` |
| 1D SMA 200 Position | `BELOW` | `BELOW if Closed 1D Close < 1D SMA 200 else ABOVE` |
| Closed 4H Market Structure (`7A`) | `DOWNTREND (LH/LL)` | `UPTREND / DOWNTREND / MIXED (500 closed 4H bars)` |
| 4H Downside BOS Status (`7A`) | `YES (BOS Down < $72,727.27 (11-12 12:00))` | `YES if latest closed 4H BOS is BOS Down else NO` |
| Upcoming Macro Event Caution (`7C`) | `CAUTION (<24h: Core Retail Sales m/m in 8.1h)` | `CAUTION (<24h USD high-impact event) else CLEAR` |
| Timestamp & Candle Closed Status | `2026-11-17 05:25:20 UTC | 2026-11-17 13:25:20 SGT (UTC+8) · Closed-Candle Inputs Only` | `Strict closed-bar verification gate` |

**BIDIRECTIONAL REGIME ROUTER STATUS:**
- **Active Route:** `MACRO_DOWNTREND_DISTRIBUTION`
- **Primary Active Rail:** `RAIL A — BTC -> USDT CONVERSION (DEFENSIVE / SELL RALLIES)`
- **Active BTC Inventory (`Rail A: BTC -> USDT`):** `ACTIVE (RAIL A) — CONVERT INTO OVERHEAD RESISTANCE`
- **Active USDT Inventory (`Rail B: USDT -> BTC`):** `RESTRICTED (RAIL B) — HOLD PENDING VALIDATED SWEEP & RECLAIM`
- **Condition A (`1D Close < 1D SMA 200`):** `YES`  |  **Condition B (`4H Downside Structure / BOS`):** `YES`

## 1. PRICE, TREND & MARKET STRUCTURE
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| Binance Spot / Perp ($) | `$65,011.70 / $64,983.10` | `All Tabs` | `OK` |
| Coinbase Spot ($) | `$64,944.90` | `1,11,15,17` | `OK` |
| 1D SMA 200 / Slope | `$72,921.15 (-0.34%)` | `0,2,3,11,15,18` | `OK` |
| 1D SMA 50 / EMA 50 | `$79,451.99 / $76,234.65` | `0,2,4,15,18,20` | `OK` |
| 1D EMA 21 / 1W EMA 50 | `$72,619.56 / $77,796.69` | `3,18` | `OK` |
| 4H EMA 50 / EMA 200 | `$69,142.64 / $75,665.84` | `7,13,18,20` | `OK` |
| Grok EMA 9/21 & 1H SMA200 | `9:$64,922.38 · 21:$64,885.57 · 1H:$69,988.82` | `5,15` | `OK` |
| Daily / Weekly VWAP (Z) | `D:$64,835.06 (+0.94σ) | W:$68,119.10` | `4,11,15` | `OK` |
| RSI(14) 1D / 4H & 4H ROC12 | `1D:24.2 · 4H:36.4 · ROC:+0.36%` | `3,7,20` | `OK` |
| ADX(14) 1D/4H & ATR(14) 1D/4H/1H | `ADX 1D:36.6 4H:56.8 | ATR:$2,628.90/$1,251.54/$485.88` | `0,1,2,8,13,18,20` | `OK` |
| 4H ATR(14)% Pctile & RelVol(20) | `ATR%:1.92% (89th pct/120b) · RelVol:0.76x` | `0,1,2,20` | `OK` |
| Macro 30D VAH / POC / VAL | `$83,467.25 / $80,605.75 / $73,356.62` | `1,3,6,11,19` | `OK` |
| Structure (L20/H20, PW, Asia) | `4H:$62,006.00-$81,971.00 | PW:$62,006.00-$75,599.22 | Asia:$64,385.99-$65,200.00` | `0,8,11,19` | `OK` |

## 2. ORDER FLOW, FOOTPRINT & LIQUIDITY
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| Spot/Perp CVD (15m / 1h) | `15m:+173.7/+102.9 | 1h:+65.8/+48.2 BTC` | `1,8,15` | `OK` |
| Spot/Perp CVD (4h / 24h) | `4h:+220.6/-364.6 | 24h:+1312.9/+798.8 BTC` | `0,1,15,16,17` | `OK` |
| Spot CVD Slopes (7D / 14D) | `7D:-4,899.1 BTC | 14D:-3,515.9 BTC` | `17` | `OK` |
| Session / UTC-Day CVD | `Sess S:+0.0 P:+0.0 | Day S:+397.2 P:-346.7` | `REST 15m` | `OK` |
| 24H Z-Scores (z_S / z_F / D) | `z_S:+0.70 · z_F:+0.72 · D:-0.02` | `1,19` | `OK` |
| 15m Footprint Delta / Stack | `Δ:+173.7 BTC (Prev:-151.1) · Stacks:0` | `1,11` | `OK` |
| Coinbase Premium ($ / % / Z) | `-66.8$ (-0.103%, Z=-0.01)` | `1,11,15` | `OK` |
| Cross-Exch 24H Spot Vol (BN/CB) | `BN:22,682 · CB:13,341 · Tot:36,023 BTC` | `1,11,Macro` | `OK` |
| L2 Depth ±1%/±2%, OBI & Spread | `1%:1.40x · 2%:1.80x · Spr:0.0015bps · OBI:+16.7%` | `16,Macro` | `OK` |
| Tactical 7D / Session 24H VP | `7D:$70,287.13/$64,982.88/$62,384.88 | 24H:$65,084.18/$65,024.48/$64,457.28` | `1,11` | `OK` |
| 30D VA Pos% & Dist to VAL | `-82.5% | -11.38% (-17.17 ATR)` | `1` | `OK` |
| SLSP Support / Resistance | `Sup:$64,742.09 | Res:$65,575.31` | `13` | `OK` |

## 3. DERIVATIVES, OPTIONS & LIQUIDATIONS
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| BN Open Interest (BTC / USD) | `92,830 BTC ($6.01B)` | `0,1,4,15,17` | `OK` |
| Cross-Exch Perp OI & Funding | `159,287 BTC ($10.32B) · F:+0.0048% [BN+BYB+OKX 3/3]` | `Macro,15` | `OK` |
| Hyperliquid Perp OI & Funding | `37,668 BTC ($2.45B) · F:+0.0046% [HL DEX]` | `Macro,15` | `OK` |
| OI Δ% (15m/1h/4h/24h) & Quad | `+0.01%/+0.17%/+1.29%/-5.92% | NEUTRAL_CHURN` | `1,4,8,11,12,15,17` | `OK` |
| Funding 8H% / Ann% / 90D Pct | `+0.0039% (+4.3%/yr) · 90D Pct:37.4%` | `0,4,9,11,15,16,19,20` | `OK` |
| Perp Basis ($ / Ann %) | `-28.6$ (-0.044% | Carry:+3.80%/yr)` | `1,4` | `OK` |
| 5m Taker L/S & Top/Glb Acct | `5m:1.517 (Δ:+54.4) | Top:1.64(62L) · Glb:2.60` | `1,2,15,16` | `OK` |
| Options OI & Put/Call (Deribit) | `P/C:0.775 · TotOI:389,313 BTC` | `Macro,19` | `OK` |
| Options IV Term & Skew (Deribit) | `F:42.7% · B:40.9% · 25dSk:+5.6%` | `Macro,6,19` | `OK` |
| Vol: DVOL, RV20, GK & BBW% | `DVOL:43.6 · RV20:48.5% · GK:73.9% · BBW:86% · Sk20:-0.40` | `0,4,6,16,19` | `OK` |
| Upper / Lower Liq Magnet | `Up:$76,334.44 | Dn:$63,841.49` | `0,2,13,17` | `OK` |
| Magnet Ratios & LSCE | `Imm:1.81x · Ladder:1.79x · Pull:0.55x · LSCE:UNTESTED` | `13,17` | `OK` |
| Modeled Liq Ladder (10x-100x) | `Up[10x:$67,685.16($102M) / 25x:$66,684.89($136M) / 50-100x:$66,024.64($194M)] | Dn[100x:$63,841.49($350M) / 25x:$63,138.15($313M) / 10x:$62,191.08($219M)] [Modeled]` | `17` | `OK` |
| Liquidations (1H / 24H) & Flush | `DATA UNAVAILABLE` | `0,8,12,13` | `UNAVAILABLE` |

## 4. ON-CHAIN, ETF & STABLECOIN FLOWS
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| MVRV Ratio (On-Chain / Proxy) | `1.212 [CoinMetrics 2026-11-16]` | `Macro,16` | `OK` |
| On-Chain SOPR / aSOPR | `DATA UNAVAILABLE` | `16` | `UNAVAILABLE` |
| Exchange Netflow 24H (CM) | `Net:+2,561.0 BTC (+$166.3M) | In:28,743 Out:26,182` | `Macro,16` | `OK` |
| BTC Exchange Reserves (CM) | `2,711,617 BTC (2026-11-16)` | `Macro,16` | `OK` |
| Stablecoins USDT+USDC Supply | `$244.74B (USDT:$175.26B · USDC:$69.49B)` | `Macro` | `OK` |
| Stablecoin Net Issuance (7D/30D) | `7D:-1.94B · 30D:-11.27B` | `Macro` | `OK` |
| US Spot ETF Flow (Farside 1D/3D) | `1D:-$68.6M | 3D:-$538.1M | 5D:-$932.9M` | `2,13` | `OK` |
| US ETF Tape Proxy (IBIT+FBTC) | `1DVol:$2.56B · 5D:-$7.25B [PROXY]` | `Macro,2,13` | `PROXY` |
| Power-Law Fair & ATH DD% | `$149,506.02 (-56.5%) | DD:-48.5%` | `3` | `OK` |
| MTF MACD (1D / 1H Status) | `1D=negative_slope (Macro Whipsaw Veto) | 1H=positive_slope CROSS` | `13,16,18` | `OK` |

## 5. MACRO, CREDIT & US LIQUIDITY
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| US SOFR Rate & Vol (NY Fed) | `3.90% (Vol:$3,092B)` | `Macro` | `OK` |
| Fed ON RRP Balance (NY Fed) | `$0.18B` | `Macro` | `OK` |
| Credit Spread HYG/LQD & 5D% | `0.7464 (+0.79% 5D)` | `Macro,3` | `OK` |
| DXY / US 10Y (^TNX) | `103.49 (RISING (+0.58 over 5d)) | 10Y:5.12%` | `3,13` | `OK` |
| TIPS Real (DFII10) / BEI | `Real:+2.92% | BEI:2.20%` | `3,13` | `OK` |
| S&P 500 / Nasdaq (1D%) | `SPX:7,417 (-1.92%) | NDX:24,510` | `3,13` | `OK` |
| VIX / Brent Crude (BZ=F) | `VIX:22.91 | Brent:$91.72` | `3,13` | `OK` |
| BTC-SPX Corr (20D / 60D) | `20D:+0.48 | 60D:+0.50` | `3` | `OK` |
| Fear & Greed / BTC Dom% | `F&G:12 (Extreme Fear) | Dom:58.50%` | `3,13` | `OK` |
| USD Macro Calendar (High) | `Core Retail Sales m/m (in 8.1h Fc:0.4%) | Retail Sales m/m (in 8.1h Fc:0.1%) (+1 more)` | `Macro` | `OK` |
| Manual Context Overrides | `Legacy_200D_Veto_Override: IGNORED (Tab1_Flag=False) · Filter=NONE_SIGNIFICANT` | `2,13` | `OK` |

## 6. QUANT FEATURES, FEED HEALTH & ARCHIVE
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| Rough Path Lévy (A_SP / MM) | `4H A_SP:+2.6877 | MM PriceFlow:+0.0016 · Rough:3.920` | `5,19` | `OK` |
| Hurst / Kalman Vel / FracDiff | `H:0.775 · KVel:-65.00 · d:0.25` | `5,6` | `OK` |
| Hilbert Cycle / TD9 / TellTale | `Cyc:72.0b · TD(1H/4H):3/2 · RV(15m/5m):1.30/N/A` | `5,9,13` | `OK` |
| VCR 72H & TSFM Disp% | `VCR:15.64 | Disp:1.28%` | `6` | `OK` |
| Open FVGs & Sweep FSM | `FVGs:3 | FSM:None (0/12)` | `1,8` | `OK` |
| WebSocket Feeds & Warmup | `Spot:SYNC (no tick) | Perp:SYNC (no tick) | CB:SYNC (12s ago) | Warm:YES` | `Live Feeds` | `STALE` |
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
| `2026-11-17 04:00` | `$65,056.53` | `$65,094.60` | `$64,915.37` | `$65,046.17` | `-0.02%` | `2,130` |
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

### 7C. MODELED LIQUIDATION LADDER (`10x-100x`) & USD MACRO CALENDAR
**6-Tier Modeled Liquidation Ladder:**
| Tier | Side | Level ($) | Dist% | Est Pool ($M) |
|---|---|---|---|---|
| `10x Shorts` | `UPPER` | `$67,685.16` | `+4.11%` | `$101.6M` |
| `25x Shorts` | `UPPER` | `$66,684.89` | `+2.57%` | `$135.5M` |
| `50-100x Shorts` | `UPPER` | `$66,024.64` | `+1.56%` | `$193.8M` |
| `100x Longs` | `LOWER` | `$63,841.49` | `-1.80%` | `$350.0M` |
| `25x Longs` | `LOWER` | `$63,138.15` | `-2.88%` | `$313.4M` |
| `10x Longs` | `LOWER` | `$62,191.08` | `-4.34%` | `$219.4M` |

**Upcoming USD High-Impact Macro Events (`-60m` to `+7d`):**
| Event | Time (UTC) | Countdown | Forecast | Previous |
|---|---|---|---|---|
| `Core Retail Sales m/m` | `2026-11-17T13:30:00Z` | `in 8.1h` | `0.4%` | `0.9%` |
| `Retail Sales m/m` | `2026-11-17T13:30:00Z` | `in 8.1h` | `0.1%` | `0.8%` |
| `FOMC Meeting Minutes` | `2026-11-18T19:00:00Z` | `in 37.6h` | `-` | `-` |

## 8. METRIC FORMULA LEGEND & CORTEX DIBSE BIDIRECTIONAL PROTOCOL
- **Rough Path Lévy (`4H A_SP`)**: Lévy signed area over 6 closed 4H bars (`> 0`: Spot path leads price markup; `< 0`: Spot path lags price / distribution).
- **24H Z-Scores (`z_S / z_F / D`)**: 30-day rolling Z-scores of 24H Spot (`z_S`) and Perp (`z_F`) cumulative delta; `D = z_S - z_F` (`D > 0` = Spot buying divergence vs Perps).
- **Spot CVD Slopes (`7D / 14D`) & 4H Vol Context**: Cumulative spot taker-delta over last `7`/`14` closed `1D` bars; `4H ATR(14)% Pctile` ranks current closed `4H` ATR% against the trailing `120` closed `4H` bars, paired with `RelVol(20)` (`closed 4H volume / 20-bar SMA`).
- **Volume Profile & Structure**: `30D VA Pos% = (Spot - VAL) / (VAH - VAL) * 100` (Macro 30D Value Area); `ATR(14) 1D/4H/1H`; `L20/H20` = 20-bar (80H) 4H range boundaries; `SLSP` = structural liquidity pool S/R; `7A` scans up to 500 closed bars per TF (`1D ~499d`, `4H ~83d`, `1H ~21d`) using `5x5` pivots for `HH/HL/LH/LL`, `BOS`, and `1%`-clustered S/R zones (deep prior-quarter supports appear on `1D` even if outside the `83d` `4H` window).
- **Derivatives, Modeled Ladder & Quant**: `90D Pct` = 0-100 rolling 90-day percentile rank of 8H funding; `[... X/3 PARTIAL_VENUE]` suppresses OI quadrant tagging when `<3` venues report; `Hyperliquid Perp` reports DEX OI and 8H-normalized funding independently; `Modeled Liq Ladder (7C)` estimates 10x-100x leverage shelves (not private exchange orderbooks); `USD Macro Calendar` tracks high-impact USD releases; `H` = Hurst exponent (`>0.5` trending, `<0.5` mean-reverting); `VCR 72H` = Volatility Compression Ratio; `TSFM Disp%` = horizon dispersion; `LSCE` = liquidation sweep state.
- **Headless Snapshot Note**: Scheduled/GitHub Actions runs execute a one-shot REST warmup (`Warm:YES`) without a persistent WebSocket loop, so `WebSocket Feeds & Warmup` reporting `STALE` (`no tick`) is isolated in `Coverage` as `Expected_Headless_WS_Offline=1` and does not indicate stale REST, orderbook, CVD, or derivatives data.

### DIRECT AI EXECUTION PROTOCOL: CORTEX DIBSE BIDIRECTIONAL DESK v1.0
Analyze BTC using the telemetry snapshot above. Operate as **CORTEX DIBSE BIDIRECTIONAL DESK v1.0** — a Spot-Only Dual-Inventory (Active BTC Inventory & Active USDT Inventory, zero leverage, user-agnostic allocation) Bidirectional Swing Workstation. Apply strict **zero-hallucination** rules using only metrics explicitly reported above (`0`, `1-6`, `7`, `7A`, `7B`, `7C`).

**Gate 0 — BIDIRECTIONAL REGIME ROUTER (EVALUATE FIRST, BEFORE ALL OTHER SIGNALS):**
- Verify Section `0` (`1D Close vs 1D SMA 200`, `4H Structure / BOS`, and `Upcoming Macro Event Caution (7C)`) BEFORE scoring lower-timeframe setups.
- **Regime Routing Logic (closed Binance Spot candles only):**
  - **MACRO_DOWNTREND_DISTRIBUTION (`1D Close < 1D SMA 200` AND (`4H DOWNTREND` OR `4H BOS Down = YES`)):**
    - **Primary Active Rail:** `RAIL A — BTC -> USDT CONVERSION` (sell/trim active BTC inventory into overhead resistance or failing rebounds with defined buy-back invalidation and lower rebuy targets).
    - **Secondary Rail:** `RAIL B — USDT -> BTC ACCUMULATION` is **RESTRICTED** to validated capitulation sweeps (`3-Gate Reversal`: sweep of major `1D/4H` support or `7C` long liquidation tier + closed-candle reclaim + positive `Spot CVD` / `4H A_SP > 0` absorption) — zero blind falling-knife buying.
  - **MACRO_UPTREND_MARKUP (`1D Close > 1D SMA 200` AND `4H UPTREND (HH/HL)` AND `4H BOS Down = NO`):**
    - **Primary Active Rail:** `RAIL B — USDT -> BTC ACCUMULATION` (deploy USDT on validated `4H HL` pullbacks with `<= 0.75%` max portfolio risk).
    - **Secondary Rail:** `RAIL A — BTC -> USDT TRIM` activates selectively only at major `1D/4H` resistance or upper `7C` short liquidation shelves when `RSI(14) > 70` and `z_S` / `4H A_SP` show distribution divergence.
  - **TRANSITIONAL_RANGE (Mixed `1D` vs `4H`):**
    - **Active Rail:** `TWO_WAY_RANGE_HARVEST` — Convert `BTC -> USDT` at `7A/SLSP` resistance, `30D VAH`, or upper `7C` short clusters; deploy `USDT -> BTC` at `7A/SLSP` support, `30D VAL`, or lower `7C` long sweeps.
  - **FAIL-CLOSED (`UNDETERMINED`):** If `1D Close`, `1D SMA 200`, or `4H Structure` is `UNAVAILABLE`, hold both rails (`HOLD BTC / HOLD USDT — NO EXECUTION`) until data is verified.
- Section `5` `Legacy_200D_Veto_Override` is permanently `IGNORED` for Desk v1.0.

**Step 1 — Mandatory Data Hygiene Gate:**
- Verify `Coverage` distinguishing: (a) genuine stale market data (`Genuine=...`), (b) expected headless WS inactivity (`Expected_Headless_WS_Offline=...` when `Warm:YES` REST-only run), (c) `[PROXY]` feeds, and (d) `UNAVAILABLE` feeds.
- Never treat expected headless WebSocket inactivity (`Expected_Headless_WS_Offline=1`) as a genuine REST/derivatives/orderbook market-data failure.
- Flag `[... PARTIAL_VENUE]` on `Cross-Exch Perp OI & Funding` or Section `7` history — never treat partial venue counts (`< 3/3`) as genuine deleveraging.
- Read `90D Pct` strictly as a `0-100` rolling 90-day funding rank, `30D VA Pos%` strictly vs Macro 30D VAH/VAL, `ATR(14) 1D/4H/1H` across matching timeframes, and treat `Modeled Liq Ladder (7C)` as an algorithmic estimate (not private orderbook depth).
- Check `USD Macro Calendar (High)`: treat `NONE (next 7d)` as a clear schedule (`OK`) vs `UNAVAILABLE` as offline.
- Do not cite missing metrics or external prices outside this telemetry snapshot.

**Step 2 — 5-Function Bidirectional Synthesis:**
1. **Multi-Timeframe Regime Classifier:** Integrate Section `1`, `7A` (`1D/4H/1H` swing structure & BOS), `7B` closed OHLCV price action, `1D/4H` ADX, `RSI(14)`, `4H ATR(14)% Pctile` & `RelVol(20)` (volatility regime & volume participation), EMA/SMA stack, and Hurst `H` -> classify as `UPTREND`, `DOWNTREND`, `RANGE-BOUND`, or `TRANSITIONAL`.
2. **Spot Flow & Rough Path Inspector:** Evaluate `Spot/Perp CVD` across `15m/1h/4h/24h`, multi-day `Spot CVD Slopes (7D / 14D)`, `z_S / z_F / D`, `Rough Path Lévy (4H A_SP)` (`> 0` spot leads markup; `< 0` spot leads distribution), `Coinbase Premium`, `L2 Depth`, `OBI`, `Spr`, `30D VA Pos%`, `SLSP`, and `7A` S/R clusters -> classify true spot accumulation/absorption vs distribution/short-covering bounce.
3. **Derivatives & Squeeze Asymmetry Profiler:** Evaluate `BN OI`, `Cross-Exch OI` (only when `3/3` venues valid), `Hyperliquid Perp OI & Funding` (`[HL DEX]` vs CEX positioning), `OI Δ%` & Quad, `Funding 8H% / Ann% / 90D Pct`, `DVOL`, `25d RR Skew`, and `6-Tier Modeled Liq Ladder (7C)` (`10x-100x` upper/lower distance & `$M` asymmetry) -> identify whether `UPPER` shorts or `LOWER` longs form the primary liquidity magnet.
4. **Macro, On-Chain & ETF Gatekeeper:** Synthesize `MVRV`, `SOPR`, `Exchange Netflow 24H`, Farside `US Spot ETF Flow (1D / 3D / 5D)` (use `IBIT+FBTC` `[PROXY]` only as secondary context), `Stablecoin Supply / Net Issuance`, `DXY`, `US10Y`, `VIX`, `SPX`, `Net Liquidity`, and `USD Macro Calendar (High)` (`7C` event proximity within `24h` or `±30m` high-impact windows) -> assign macro backdrop (`Tailwind`, `Neutral`, or `Headwind`).
5. **Dual-Inventory Risk & Execution Arbiter:**
   - **Rail A (`BTC -> USDT` Conversion Rules):** Activate when price stalls or reverses at `4H/1D/SLSP` resistance or upper `7C` short liquidation shelves while `1D < SMA 200` or `4H A_SP < 0` / `7D Spot CVD < 0` (or euphoria extremes in `MACRO_UPTREND_MARKUP`). Output exact **Overhead Conversion Zone**, **Suggested % of Active BTC Inventory to Convert**, **Upper Buy-Back Invalidation Stop** (where converted BTC is repurchased if breakout invalidates downside thesis), and **Lower USDT Rebuy Targets** to compound BTC quantity.
   - **Rail B (`USDT -> BTC` Accumulation Rules):** Activate on validated `4H HL` pullbacks in uptrends, OR validated `1H/4H` sweep-and-reclaim reversals below `7A/SLSP` support or `7C` long liquidation shelves with positive `Spot CVD`, `z_S > 0`, and `4H A_SP > 0`. Enforce `<= 0.75%` max portfolio risk per qualified position and guard against unhedged entries inside `< 24h` USD high-impact macro windows.

**Step 3 — Mandatory Bidirectional Output Contract:**
- **0. BIDIRECTIONAL REGIME ROUTER (`GATE 0`)** (`Active Route`, `Condition A (1D vs SMA 200)`, `Condition B (4H Structure/BOS)`, `Macro <24h Window`, **`BTC Inventory Action (Rail A: BTC -> USDT): SELL (CONVERT TO USDT) / HOLD BTC`**, **`USDT Inventory Action (Rail B: USDT -> BTC): BUY (DEPLOY TO BTC) / HOLD USDT`**).
- **1. EXECUTIVE SUMMARY & DUAL-INVENTORY POSTURE** (`Spot Price`, `Regime State`, explicit **`BTC Inventory Action`** & **`USDT Inventory Action`**, `Confidence /100`).
- **2. DATA HYGIENE AUDIT** (Exact `OK/UNAVAILABLE/STALE/PROXY` tally, headless WS clarification, any `PARTIAL_VENUE` anomalies, degraded-signal list).
- **3. MULTI-TIMEFRAME REGIME & ROUGH PATH FLOW SYNTHESIS** (Price/EMA/ADX + `4H ATR% Pctile / RelVol` vs `4H A_SP` Lévy area, intraday & `7D/14D` Spot CVD, Coinbase Premium, and `4H` SQLite Section `7` + `7A/7B` trajectory).
- **4. DERIVATIVES, LIQUIDATION MAGNETS & MACRO BACKDROP** (CEX `3/3` + `Hyperliquid DEX` OI/funding, funding `90D Pct`, options skew, `6-tier Liq Ladder (7C)` upper vs lower squeeze magnets, Farside `1D/3D/5D` ETF flows, `USD Macro Calendar (7C)` event window, and macro backdrop).
- **5. BIDIRECTIONAL LEVELS MAP** (`Rail A` Supply/Conversion Zones, `Rail B` Demand/Rebuy Zones, `7C` modeled liquidation shelves, and Structural Buy-Back / Stop Invalidation Levels tied to `7A/7B` & `SLSP`).
- **6. DUAL-INVENTORY EXECUTION PLAN (`RAIL A` & `RAIL B`)** (**Rail A (`BTC -> USDT`):** Exact Conversion Trigger Zone, Suggested % of Active BTC Inventory, Upper Buy-Back Invalidation Stop, Lower Target Rebuy Zone; **Rail B (`USDT -> BTC`):** Exact Entry Trigger / Confirmation Gate, Stop Loss at `<= 0.75%` portfolio risk, Take Profit Targets, and Macro Event Timing Constraint).
