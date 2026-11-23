# TAB [D: DATA HUB] | CONSOLIDATED DATA-ONLY TELEMETRY REPORT
**Retrieval Time (UTC):** `2026-11-23 10:37:23 UTC`  |  **Retrieval Time (SGT):** `2026-11-23 18:37:23 SGT (UTC+8)`
**Spot Price (BTCUSDT):** `$61,448.12`  |  **Coverage:** `OK=67/71 | UNAVAILABLE=2 | STALE=1 (Genuine=0, Expected_Headless_WS_Offline=1) | PROXY/STATIC=1`
**24H Range:** `$60,386.00 - $61,959.93`  |  **Returns (24H / 7D / 30D):** `+0.94% / -5.29% / -24.03%`
**Archive (SQLite):** `47 closed-4H snapshots (Last: 2026-11-23 08:00:00 UTC)`

## 0. BIDIRECTIONAL REGIME ROUTER (GATE 0 — DUAL-INVENTORY SPOT WORKSTATION)
| Router Field | Value | Rule / Threshold |
|---|---|---|
| Latest Closed 1D Candle Close | `$61,271.08 (1D bar 2026-11-22 · closed 2026-11-23 00:00 UTC)` | `Same closed Binance Spot 1D series only (live candle excluded)` |
| Current 1D SMA 200 | `$72,384.86` | `200-bar SMA of same closed Binance Spot 1D series` |
| Distance vs 1D SMA 200 | `-15.35% (-$11,113.78)` | `(Closed 1D Close - 1D SMA 200) / 1D SMA 200` |
| 1D SMA 200 Position | `BELOW` | `BELOW if Closed 1D Close < 1D SMA 200 else ABOVE` |
| Closed 4H Market Structure (`7A`) | `DOWNTREND (LH/LL)` | `UPTREND / DOWNTREND / MIXED (500 closed 4H bars)` |
| 4H Downside BOS Status (`7A`) | `YES (BOS Down < $62,062.97 (11-19 20:00))` | `YES if latest closed 4H BOS is BOS Down else NO` |
| Upcoming Macro Event Caution (`7C`) | `CLEAR (>24h / NONE)` | `CAUTION (<24h USD high-impact event) else CLEAR` |
| Timestamp & Candle Closed Status | `2026-11-23 10:37:23 UTC | 2026-11-23 18:37:23 SGT (UTC+8) · Closed-Candle Inputs Only` | `Strict closed-bar verification gate` |

**BIDIRECTIONAL REGIME ROUTER STATUS:**
- **Active Route:** `MACRO_DOWNTREND_DISTRIBUTION`
- **Primary Active Rail:** `RAIL A — BTC -> USDT CONVERSION (DEFENSIVE / SELL RALLIES)`
- **Active BTC Inventory (`Rail A: BTC -> USDT`):** `ACTIVE (RAIL A) — CONVERT INTO OVERHEAD RESISTANCE`
- **Active USDT Inventory (`Rail B: USDT -> BTC`):** `RESTRICTED (RAIL B) — HOLD PENDING VALIDATED SWEEP & RECLAIM`
- **Condition A (`1D Close < 1D SMA 200`):** `YES`  |  **Condition B (`4H Downside Structure / BOS`):** `YES`

## 1. PRICE, TREND & MARKET STRUCTURE
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| Binance Spot / Perp ($) | `$61,448.12 / $61,417.80` | `All Tabs` | `OK` |
| Coinbase Spot ($) | `$61,370.78` | `1,11,15,17` | `OK` |
| 1D SMA 200 / Slope | `$72,384.86 (-0.65%)` | `0,2,3,11,15,18` | `OK` |
| 1D SMA 50 / EMA 50 | `$76,762.02 / $73,009.16` | `0,2,4,15,18,20` | `OK` |
| 1D EMA 21 / 1W EMA 50 | `$67,597.96 / $77,712.30` | `3,18` | `OK` |
| 4H EMA 50 / EMA 200 | `$62,963.90 / $71,293.55` | `7,13,18,20` | `OK` |
| Grok EMA 9/21 & 1H SMA200 | `9:$61,369.66 · 21:$61,103.46 · 1H:$62,561.82` | `5,15` | `OK` |
| Daily / Weekly VWAP (Z) | `D:$61,327.34 (+0.43σ) | W:$61,283.22` | `4,11,15` | `OK` |
| RSI(14) 1D / 4H & 4H ROC12 | `1D:27.3 · 4H:51.7 · ROC:+5.97%` | `3,7,20` | `OK` |
| ADX(14) 1D/4H & ATR(14) 1D/4H/1H | `ADX 1D:50.6 4H:36.7 | ATR:$3,011.32/$1,295.94/$528.50` | `0,1,2,8,13,18,20` | `OK` |
| 4H ATR(14)% Pctile & RelVol(20) | `ATR%:2.19% (85th pct/120b) · RelVol:0.45x` | `0,1,2,20` | `OK` |
| Macro 30D VAH / POC / VAL | `$76,714.64 / $64,859.86 / $55,912.86` | `1,3,6,11,19` | `OK` |
| Structure (L20/H20, PW, Asia) | `4H:$55,130.00-$81,196.01 | PW:$55,130.00-$65,696.16 | Asia:$60,386.00-$61,959.93` | `0,8,11,19` | `OK` |

## 2. ORDER FLOW, FOOTPRINT & LIQUIDITY
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| Spot/Perp CVD (15m / 1h) | `15m:+0.0/+270.3 | 1h:-33.4/+159.3 BTC` | `1,8,15` | `OK` |
| Spot/Perp CVD (4h / 24h) | `4h:+60.9/+451.6 | 24h:+252.4/+1807.7 BTC` | `0,1,15,16,17` | `OK` |
| Spot CVD Slopes (7D / 14D) | `7D:-4,470.0 BTC | 14D:-8,305.8 BTC` | `17` | `OK` |
| Session / UTC-Day CVD | `Sess S:+0.0 P:+0.0 | Day S:+70.5 P:+1120.1` | `REST 15m` | `OK` |
| 24H Z-Scores (z_S / z_F / D) | `z_S:+0.47 · z_F:+1.69 · D:-1.22` | `1,19` | `OK` |
| 15m Footprint Delta / Stack | `Δ:+0.0 BTC (Prev:+0.0) · Stacks:0` | `1,11` | `OK` |
| Coinbase Premium ($ / % / Z) | `-77.3$ (-0.126%, Z=+1.75)` | `1,11,15` | `OK` |
| Cross-Exch 24H Spot Vol (BN/CB) | `BN:17,363 · CB:8,996 · Tot:26,360 BTC` | `1,11,Macro` | `OK` |
| L2 Depth ±1%/±2%, OBI & Spread | `1%:0.66x · 2%:0.56x · Spr:0.0016bps · OBI:-20.8%` | `16,Macro` | `OK` |
| Tactical 7D / Session 24H VP | `7D:$65,299.93/$64,947.72/$59,488.54 | 24H:$61,500.87/$60,976.22/$60,792.60` | `1,11` | `OK` |
| 30D VA Pos% & Dist to VAL | `26.6% | +9.90% (+10.47 ATR)` | `1` | `OK` |
| SLSP Support / Resistance | `Sup:$61,065.63 | Res:$62,371.96` | `13` | `OK` |

## 3. DERIVATIVES, OPTIONS & LIQUIDATIONS
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| BN Open Interest (BTC / USD) | `92,599 BTC ($5.67B)` | `0,1,4,15,17` | `OK` |
| Cross-Exch Perp OI & Funding | `158,012 BTC ($9.69B) · F:+0.0016% [BN+BYB+OKX 3/3]` | `Macro,15` | `OK` |
| Hyperliquid Perp OI & Funding | `37,897 BTC ($2.33B) · F:+0.0100% [HL DEX]` | `Macro,15` | `OK` |
| OI Δ% (15m/1h/4h/24h) & Quad | `+0.05%/+0.09%/-1.17%/-0.70% | NEUTRAL_CHURN` | `1,4,8,11,12,15,17` | `OK` |
| Funding 8H% / Ann% / 90D Pct | `+0.0030% (+3.3%/yr) · 90D Pct:9.6%` | `0,4,9,11,15,16,19,20` | `OK` |
| Perp Basis ($ / Ann %) | `-30.3$ (-0.049% | Carry:+2.70%/yr)` | `1,4` | `OK` |
| 5m Taker L/S & Top/Glb Acct | `5m:3.264 (Δ:+3.9) | Top:1.63(62L) · Glb:2.18` | `1,2,15,16` | `OK` |
| Options OI & Put/Call (Deribit) | `P/C:0.809 · TotOI:418,329 BTC` | `Macro,19` | `OK` |
| Options IV Term & Skew (Deribit) | `F:49.8% · B:46.4% · 25dSk:+7.1%` | `Macro,6,19` | `OK` |
| Vol: DVOL, RV20, GK & BBW% | `DVOL:51.7 · RV20:51.9% · GK:87.4% · BBW:97% · Sk20:-0.27` | `0,4,6,16,19` | `OK` |
| Upper / Lower Liq Magnet | `Up:$76,334.44 | Dn:$60,342.05` | `0,2,13,17` | `OK` |
| Magnet Ratios & LSCE | `Imm:1.81x · Ladder:1.38x · Pull:0.55x · LSCE:UNTESTED` | `13,17` | `OK` |
| Modeled Liq Ladder (10x-100x) | `Up[10x:$67,592.93($86M) / 25x:$63,906.04($114M) / 50-100x:$62,062.60($194M)] | Dn[100x:$60,833.64($350M) / 25x:$58,990.20($312M) / 10x:$55,303.31($218M)] [Modeled] (L/S:global_account_ls_ratio)` | `17` | `OK` |
| Liquidations (1H / 24H) & Flush | `DATA UNAVAILABLE` | `0,8,12,13` | `UNAVAILABLE` |

## 4. ON-CHAIN, ETF & STABLECOIN FLOWS
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| MVRV Ratio (On-Chain / Proxy) | `1.148 [CoinMetrics 2026-11-22]` | `Macro,16` | `OK` |
| On-Chain SOPR / aSOPR | `DATA UNAVAILABLE` | `16` | `UNAVAILABLE` |
| Exchange Netflow 24H (CM) | `Net:+924.4 BTC (+$56.5M) | In:14,442 Out:13,517` | `Macro,16` | `OK` |
| BTC Exchange Reserves (CM) | `2,699,121 BTC (2026-11-22)` | `Macro,16` | `OK` |
| Stablecoins USDT+USDC Supply | `$243.35B (USDT:$174.62B · USDC:$68.72B)` | `Macro` | `OK` |
| Stablecoin Net Issuance (7D/30D) | `7D:-1.25B · 30D:-10.89B` | `Macro` | `OK` |
| US Spot ETF Flow (Farside 1D/3D) | `1D:-$669.2M | 3D:-$1.56B | 5D:-$1.79B` | `2,13` | `OK` |
| US ETF Tape Proxy (IBIT+FBTC) | `1DVol:$4.02B · 5D:-$13.65B [PROXY]` | `Macro,2,13` | `PROXY` |
| Power-Law Fair & ATH DD% | `$150,316.62 (-59.1%) | DD:-51.3%` | `3` | `OK` |
| MTF MACD (1D / 1H Status) | `1D=negative_slope (Macro Whipsaw Veto) | 1H=negative_slope / NEUTRAL` | `13,16,18` | `OK` |

## 5. MACRO, CREDIT & US LIQUIDITY
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| US SOFR Rate & Vol (NY Fed) | `3.91% (Vol:$3,161B)` | `Macro` | `OK` |
| Fed ON RRP Balance (NY Fed) | `$0.40B` | `Macro` | `OK` |
| Credit Spread HYG/LQD & 5D% | `0.7361 (-1.63% 5D)` | `Macro,3` | `OK` |
| DXY / US 10Y (^TNX) | `103.88 (RISING (+0.33 over 5d)) | 10Y:4.91%` | `3,13` | `OK` |
| TIPS Real (DFII10) / BEI | `Real:+2.77% | BEI:2.14%` | `3,13` | `OK` |
| S&P 500 / Nasdaq (1D%) | `SPX:6,910 (-3.70%) | NDX:22,618` | `3,13` | `OK` |
| VIX / Brent Crude (BZ=F) | `VIX:30.07 | Brent:$89.27` | `3,13` | `OK` |
| BTC-SPX Corr (20D / 60D) | `20D:+0.67 | 60D:+0.71` | `3` | `OK` |
| Fear & Greed / BTC Dom% | `F&G:11 (Extreme Fear) | Dom:58.90%` | `3,13` | `OK` |
| USD Macro Calendar (High) | `Core PCE Price Index m/m (in 50.9h Fc:0.3%) | Prelim GDP q/q (in 50.9h Fc:3.5%)` | `Macro` | `OK` |
| Manual Context Overrides | `Legacy_200D_Veto_Override: IGNORED (Tab1_Flag=True) · Filter=NONE_SIGNIFICANT` | `2,13` | `OK` |

## 6. QUANT FEATURES, FEED HEALTH & ARCHIVE
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| Rough Path Lévy (A_SP / MM) | `4H A_SP:-0.5453 | MM PriceFlow:-0.9097 · Rough:0.710` | `5,19` | `OK` |
| Hurst / Kalman Vel / FracDiff | `H:0.697 · KVel:-37.70 · d:0.15` | `5,6` | `OK` |
| Hilbert Cycle / TD9 / TellTale | `Cyc:13.0b · TD(1H/4H):2/7 · RV(15m/5m):0.31/N/A` | `5,9,13` | `OK` |
| VCR 72H & TSFM Disp% | `VCR:16.06 | Disp:1.28%` | `6` | `OK` |
| Open FVGs & Sweep FSM | `FVGs:4 | FSM:None (0/12)` | `1,8` | `OK` |
| WebSocket Feeds & Warmup | `Spot:SYNC (no tick) | Perp:SYNC (no tick) | CB:SYNC (11s ago) | Warm:YES` | `Live Feeds` | `STALE` |
| Spot Klines (1W/1D/4H/1H/15m) | `1W:100 1D:500 bars · 11-23 00:00 UTC | 4H:500 1H:720 15m:240` | `All Tabs` | `OK` |
| Perp Klines / Est. Excluded | `1D:101 · 1H:720 · 15m:240 (Excl=399)` | `1,4,11,15,19` | `OK` |
| Closed 4H Anchor (Tab 19/20) | `2026-11-23 08:00:00 UTC` | `18,19,20` | `OK` |
| B1/B2 Rec & Companion Liq | `Rec:PASS (0s delta) | Liq:N/A` | `8,13,17` | `OK` |
| Telemetry History Archive (SQLite) | `47 bars logged (Last: 2026-11-23 08:00:00 UTC)` | `DB Archive` | `OK` |

## 7. RECENT CLOSED-4H SNAPSHOT TRAJECTORY (SQLITE ARCHIVE)
| Closed 4H Bar (UTC) | Spot ($) | 24H Spot/Perp CVD | Cross-Exch Perp OI & Funding | Funding 8H% / 90D Pct | MVRV Ratio |
|---|---|---|---|---|---|
| `2026-11-23 08:00:00 UTC` | `$61,488.01` | `24h:+492.9/+2793.6 BTC` | `158,177 BTC ($9.71B) · F:+0.0024% [BN+BYB+OKX 3/3]` | `+0.0035% (+3.8%/yr) · 90D Pct:9.6%` | `1.148 [CoinMetrics 2026-11-22]` |
| `2026-11-23 04:00:00 UTC` | `$61,260.01` | `24h:+719.3/+4846.5 BTC` | `156,913 BTC ($9.59B) · F:+0.0036% [BN+BYB+OKX 3/3]` | `+0.0034% (+3.7%/yr) · 90D Pct:17.8%` | `1.148 [CoinMetrics 2026-11-22]` |
| `2026-11-23 00:00:00 UTC` | `$61,209.38` | `24h:+346.3/+3356.7 BTC` | `159,028 BTC ($9.73B) · F:+0.0018% [BN+BYB+OKX 3/3]` | `+0.0026% (+2.8%/yr) · 90D Pct:17.8%` | `1.130 [CoinMetrics 2026-11-21]` |
| `2026-11-22 20:00:00 UTC` | `$60,715.96` | `24h:+57.3/+2761.9 BTC` | `159,257 BTC ($9.66B) · F:+0.0017% [BN+BYB+OKX 3/3]` | `+0.0024% (+2.6%/yr) · 90D Pct:21.5%` | `1.130 [CoinMetrics 2026-11-21]` |
| `2026-11-22 16:00:00 UTC` | `$60,912.18` | `24h:+375.5/+3168.4 BTC` | `159,936 BTC ($9.73B) · F:-0.0001% [BN+BYB+OKX 3/3]` | `-0.0008% (-0.8%/yr) · 90D Pct:21.5%` | `1.130 [CoinMetrics 2026-11-21]` |
| `2026-11-22 12:00:00 UTC` | `$60,790.52` | `24h:+533.1/+3830.1 BTC` | `159,713 BTC ($9.71B) · F:+0.0032% [BN+BYB+OKX 3/3]` | `+0.0035% (+3.9%/yr) · 90D Pct:33.0%` | `1.130 [CoinMetrics 2026-11-21]` |

### 7A. 500-BAR MARKET STRUCTURE & HISTORICAL S/R ZONES (`1D / 4H / 1H`)
| TF (Bars) | Swing Structure | Last Swing Pivots | Latest BOS | Resistance Zones (Above Spot) | Support Zones (Below Spot) |
|---|---|---|---|---|---|
| `1D (499)` | `DOWNTREND (LH/LL)` | `SH:$81,196.01 (11-04) · SL:$79,800.00 (10-15)` | `BOS Down < $79,800.00 (10-29)` | `$62,440.17 (3x), $65,182.19 (5x), $67,124.15 (2x)` | `$60,000.00 (1x), $59,130.91 (1x), $57,957.60 (2x)` |
| `4H (499)` | `DOWNTREND (LH/LL)` | `SH:$65,696.16 (11-16 12:00) · SL:$55,130.00 (11-21 04:00)` | `BOS Down < $62,062.97 (11-19 20:00)` | `$62,034.49 (2x), $63,620.51 (2x), $65,696.16 (1x)` | `$55,130.00 (1x)` |
| `1H (500)` | `UPTREND (HH/HL)` | `SH:$61,959.93 (11-23 03:00) · SL:$60,386.00 (11-23 02:00)` | `BOS Up > $60,568.01 (11-22 09:00)` | `$61,944.40 (7x), $62,639.52 (1x), $63,894.86 (4x)` | `$60,650.00 (3x), $58,768.51 (1x), $57,778.35 (1x)` |

### 7B. RECENT CLOSED KLINES — OHLCV PRICE ACTION (`1D`×7, `4H`×12, `1H`×12)
**1D Closed Candles (Last 7 of 499 available, Newest First):**
| Open Time (UTC) | Open | High | Low | Close | Chg% | Vol (BTC) |
|---|---|---|---|---|---|---|
| `2026-11-22` | `$60,215.78` | `$61,669.99` | `$58,768.51` | `$61,271.08` | `+1.75%` | `20,137` |
| `2026-11-21` | `$58,951.51` | `$60,996.00` | `$55,130.00` | `$60,215.77` | `+2.14%` | `48,558` |
| `2026-11-20` | `$61,986.73` | `$62,639.52` | `$57,778.35` | `$58,951.51` | `-4.90%` | `38,126` |
| `2026-11-19` | `$63,068.21` | `$64,080.80` | `$61,428.26` | `$61,986.73` | `-1.71%` | `19,880` |
| `2026-11-18` | `$64,947.36` | `$65,002.00` | `$62,062.97` | `$63,068.22` | `-2.89%` | `18,700` |
| `2026-11-17` | `$64,882.88` | `$65,447.00` | `$63,336.00` | `$64,947.35` | `+0.10%` | `28,317` |
| `2026-11-16` | `$65,351.05` | `$65,696.16` | `$63,905.01` | `$64,882.87` | `-0.72%` | `21,929` |

**4H Closed Candles (Last 12 of 499 available, Newest First):**
| Open Time (UTC) | Open | High | Low | Close | Chg% | Vol (BTC) |
|---|---|---|---|---|---|---|
| `2026-11-23 04:00` | `$61,285.93` | `$61,830.00` | `$61,060.00` | `$61,459.50` | `+0.28%` | `2,606` |
| `2026-11-23 00:00` | `$61,271.09` | `$61,959.93` | `$60,386.00` | `$61,285.93` | `+0.02%` | `3,722` |
| `2026-11-22 20:00` | `$60,737.12` | `$61,407.99` | `$60,581.04` | `$61,271.08` | `+0.88%` | `2,261` |
| `2026-11-22 16:00` | `$60,894.90` | `$61,411.34` | `$60,537.43` | `$60,737.12` | `-0.26%` | `2,583` |
| `2026-11-22 12:00` | `$61,062.73` | `$61,669.99` | `$60,464.01` | `$60,894.91` | `-0.27%` | `3,833` |
| `2026-11-22 08:00` | `$59,170.03` | `$61,365.24` | `$59,086.00` | `$61,062.74` | `+3.20%` | `5,842` |
| `2026-11-22 04:00` | `$59,359.99` | `$59,668.02` | `$58,768.51` | `$59,170.02` | `-0.32%` | `2,846` |
| `2026-11-22 00:00` | `$60,215.78` | `$60,352.16` | `$59,129.99` | `$59,359.98` | `-1.42%` | `2,771` |
| `2026-11-21 20:00` | `$60,364.02` | `$60,568.01` | `$59,988.00` | `$60,215.77` | `-0.25%` | `2,134` |
| `2026-11-21 16:00` | `$59,940.17` | `$60,477.98` | `$59,783.45` | `$60,364.02` | `+0.71%` | `2,518` |
| `2026-11-21 12:00` | `$58,206.10` | `$60,996.00` | `$58,140.00` | `$59,943.70` | `+2.99%` | `9,702` |
| `2026-11-21 08:00` | `$57,997.00` | `$58,637.49` | `$57,381.45` | `$58,206.10` | `+0.36%` | `6,503` |

**1H Closed Candles (Last 12 of 719 available, Newest First):**
| Open Time (UTC) | Open | High | Low | Close | Chg% | Vol (BTC) |
|---|---|---|---|---|---|---|
| `2026-11-23 09:00` | `$61,518.14` | `$61,941.38` | `$61,279.22` | `$61,442.16` | `-0.12%` | `686` |
| `2026-11-23 08:00` | `$61,460.01` | `$61,592.92` | `$61,139.36` | `$61,518.13` | `+0.09%` | `893` |
| `2026-11-23 07:00` | `$61,474.01` | `$61,581.24` | `$61,403.47` | `$61,459.50` | `-0.02%` | `678` |
| `2026-11-23 06:00` | `$61,685.44` | `$61,830.00` | `$61,400.96` | `$61,474.00` | `-0.34%` | `588` |
| `2026-11-23 05:00` | `$61,240.00` | `$61,830.00` | `$61,104.00` | `$61,685.44` | `+0.73%` | `651` |
| `2026-11-23 04:00` | `$61,285.93` | `$61,492.00` | `$61,060.00` | `$61,240.01` | `-0.07%` | `688` |
| `2026-11-23 03:00` | `$60,615.78` | `$61,959.93` | `$60,599.50` | `$61,285.93` | `+1.11%` | `1,591` |
| `2026-11-23 02:00` | `$60,873.21` | `$60,913.29` | `$60,386.00` | `$60,615.78` | `-0.42%` | `743` |
| `2026-11-23 01:00` | `$61,351.33` | `$61,357.61` | `$60,808.37` | `$60,873.20` | `-0.78%` | `527` |
| `2026-11-23 00:00` | `$61,271.09` | `$61,464.35` | `$61,050.04` | `$61,351.33` | `+0.13%` | `860` |
| `2026-11-22 23:00` | `$61,115.09` | `$61,407.99` | `$60,796.82` | `$61,271.08` | `+0.26%` | `897` |
| `2026-11-22 22:00` | `$60,953.86` | `$61,115.09` | `$60,773.56` | `$61,115.08` | `+0.26%` | `579` |

### 7C. MODELED LIQUIDATION LADDER (`10x-100x`) & USD MACRO CALENDAR
**6-Tier Modeled Liquidation Ladder (`global_account_ls_ratio`):**
| Tier | Side | Level ($) | Dist% | Est Pool ($M) |
|---|---|---|---|---|
| `10x Shorts` | `UPPER` | `$67,592.93` | `+10.00%` | `$85.9M` |
| `25x Shorts` | `UPPER` | `$63,906.04` | `+4.00%` | `$114.5M` |
| `50-100x Shorts` | `UPPER` | `$62,062.60` | `+1.00%` | `$193.8M` |
| `100x Longs` | `LOWER` | `$60,833.64` | `-1.00%` | `$350.0M` |
| `25x Longs` | `LOWER` | `$58,990.20` | `-4.00%` | `$312.1M` |
| `10x Longs` | `LOWER` | `$55,303.31` | `-10.00%` | `$218.4M` |

**Upcoming USD High-Impact Macro Events (`-60m` to `+7d`):**
| Event | Time (UTC) | Countdown | Forecast | Previous |
|---|---|---|---|---|
| `Core PCE Price Index m/m` | `2026-11-25T13:30:00Z` | `in 50.9h` | `0.3%` | `0.3%` |
| `Prelim GDP q/q` | `2026-11-25T13:30:00Z` | `in 50.9h` | `3.5%` | `3.4%` |

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
