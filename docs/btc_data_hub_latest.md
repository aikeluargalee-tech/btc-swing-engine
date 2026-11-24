# TAB [D: DATA HUB] | CONSOLIDATED DATA-ONLY TELEMETRY REPORT
**Retrieval Time (UTC):** `2026-11-24 06:51:53 UTC`  |  **Retrieval Time (SGT):** `2026-11-24 14:51:53 SGT (UTC+8)`
**Spot Price (BTCUSDT):** `$60,607.20`  |  **Coverage:** `OK=67/71 | UNAVAILABLE=2 | STALE=1 (Genuine=0, Expected_Headless_WS_Offline=1) | PROXY/STATIC=1`
**24H Range:** `$59,455.31 - $64,603.12`  |  **Returns (24H / 7D / 30D):** `-1.41% / -6.68% / -24.39%`
**Archive (SQLite):** `51 closed-4H snapshots (Last: 2026-11-24 04:00:00 UTC)`

## 0. BIDIRECTIONAL REGIME ROUTER (GATE 0 — DUAL-INVENTORY SPOT WORKSTATION)
| Router Field | Value | Rule / Threshold |
|---|---|---|
| Latest Closed 1D Candle Close | `$61,270.93 (1D bar 2026-11-23 · closed 2026-11-24 00:00 UTC)` | `Same closed Binance Spot 1D series only (live candle excluded)` |
| Current 1D SMA 200 | `$72,291.18` | `200-bar SMA of same closed Binance Spot 1D series` |
| Distance vs 1D SMA 200 | `-15.24% (-$11,020.25)` | `(Closed 1D Close - 1D SMA 200) / 1D SMA 200` |
| 1D SMA 200 Position | `BELOW` | `BELOW if Closed 1D Close < 1D SMA 200 else ABOVE` |
| Closed 4H Market Structure (`7A`) | `DOWNTREND (LH/LL)` | `UPTREND / DOWNTREND / MIXED (500 closed 4H bars)` |
| 4H Downside BOS Status (`7A`) | `YES (BOS Down < $62,062.97 (11-19 20:00))` | `YES if latest closed 4H BOS is BOS Down else NO` |
| Upcoming Macro Event Caution (`7C`) | `CLEAR (>24h / NONE)` | `CAUTION (<24h USD high-impact event) else CLEAR` |
| Timestamp & Candle Closed Status | `2026-11-24 06:51:53 UTC | 2026-11-24 14:51:53 SGT (UTC+8) · Closed-Candle Inputs Only` | `Strict closed-bar verification gate` |

**BIDIRECTIONAL REGIME ROUTER STATUS:**
- **Active Route:** `MACRO_DOWNTREND_DISTRIBUTION`
- **Primary Active Rail:** `RAIL A — BTC -> USDT CONVERSION (DEFENSIVE / SELL RALLIES)`
- **Active BTC Inventory (`Rail A: BTC -> USDT`):** `ACTIVE (RAIL A) — CONVERT INTO OVERHEAD RESISTANCE`
- **Active USDT Inventory (`Rail B: USDT -> BTC`):** `RESTRICTED (RAIL B) — HOLD PENDING VALIDATED SWEEP & RECLAIM`
- **Condition A (`1D Close < 1D SMA 200`):** `YES`  |  **Condition B (`4H Downside Structure / BOS`):** `YES`

## 1. PRICE, TREND & MARKET STRUCTURE
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| Binance Spot / Perp ($) | `$60,607.20 / $60,578.50` | `All Tabs` | `OK` |
| Coinbase Spot ($) | `$60,541.22` | `1,11,15,17` | `OK` |
| 1D SMA 200 / Slope | `$72,291.18 (-0.67%)` | `0,2,3,11,15,18` | `OK` |
| 1D SMA 50 / EMA 50 | `$76,256.84 / $72,516.13` | `0,2,4,15,18,20` | `OK` |
| 1D EMA 21 / 1W EMA 50 | `$66,947.79 / $77,712.30` | `3,18` | `OK` |
| 4H EMA 50 / EMA 200 | `$62,681.70 / $70,810.29` | `7,13,18,20` | `OK` |
| Grok EMA 9/21 & 1H SMA200 | `9:$60,767.97 · 21:$61,074.77 · 1H:$62,208.97` | `5,15` | `OK` |
| Daily / Weekly VWAP (Z) | `D:$60,535.56 (+0.14σ) | W:$61,021.10` | `4,11,15` | `OK` |
| RSI(14) 1D / 4H & 4H ROC12 | `1D:25.6 · 4H:44.7 · ROC:+1.65%` | `3,7,20` | `OK` |
| ADX(14) 1D/4H & ATR(14) 1D/4H/1H | `ADX 1D:49.3 4H:28.9 | ATR:$3,097.45/$1,483.43/$660.96` | `0,1,2,8,13,18,20` | `OK` |
| 4H ATR(14)% Pctile & RelVol(20) | `ATR%:2.49% (97th pct/120b) · RelVol:0.87x` | `0,1,2,20` | `OK` |
| Macro 30D VAH / POC / VAL | `$76,043.61 / $64,859.86 / $55,912.86` | `1,3,6,11,19` | `OK` |
| Structure (L20/H20, PW, Asia) | `4H:$55,130.00-$81,196.01 | PW:$55,130.00-$65,696.16 | Asia:$59,455.31-$61,682.01` | `0,8,11,19` | `OK` |

## 2. ORDER FLOW, FOOTPRINT & LIQUIDITY
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| Spot/Perp CVD (15m / 1h) | `15m:+9.2/-71.8 | 1h:+16.7/-238.7 BTC` | `1,8,15` | `OK` |
| Spot/Perp CVD (4h / 24h) | `4h:+201.5/-419.6 | 24h:+178.3/+1639.3 BTC` | `0,1,15,16,17` | `OK` |
| Spot CVD Slopes (7D / 14D) | `7D:-5,031.0 BTC | 14D:-9,930.1 BTC` | `17` | `OK` |
| Session / UTC-Day CVD | `Sess S:+0.0 P:+0.0 | Day S:+153.8 P:-1603.6` | `REST 15m` | `OK` |
| 24H Z-Scores (z_S / z_F / D) | `z_S:+0.05 · z_F:+0.74 · D:-0.69` | `1,19` | `OK` |
| 15m Footprint Delta / Stack | `Δ:+9.2 BTC (Prev:+0.0) · Stacks:0` | `1,11` | `OK` |
| Coinbase Premium ($ / % / Z) | `-66.0$ (-0.109%, Z=+0.59)` | `1,11,15` | `OK` |
| Cross-Exch 24H Spot Vol (BN/CB) | `BN:28,427 · CB:16,979 · Tot:45,406 BTC` | `1,11,Macro` | `OK` |
| L2 Depth ±1%/±2%, OBI & Spread | `1%:0.90x · 2%:1.11x · Spr:0.0016bps · OBI:-5.1%` | `16,Macro` | `OK` |
| Tactical 7D / Session 24H VP | `7D:$64,802.19/$61,363.19/$59,385.76 | 24H:$63,530.66/$61,385.74/$61,042.55` | `1,11` | `OK` |
| 30D VA Pos% & Dist to VAL | `23.3% | +8.40% (+7.10 ATR)` | `1` | `OK` |
| SLSP Support / Resistance | `Sup:$60,000.00 | Res:$61,065.63` | `13` | `OK` |

## 3. DERIVATIVES, OPTIONS & LIQUIDATIONS
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| BN Open Interest (BTC / USD) | `96,389 BTC ($5.82B)` | `0,1,4,15,17` | `OK` |
| Cross-Exch Perp OI & Funding | `160,946 BTC ($9.72B) · F:+0.0046% [BN+BYB+OKX 3/3]` | `Macro,15` | `OK` |
| Hyperliquid Perp OI & Funding | `37,336 BTC ($2.26B) · F:+0.0050% [HL DEX]` | `Macro,15` | `OK` |
| OI Δ% (15m/1h/4h/24h) & Quad | `+0.03%/+0.29%/+0.61%/-5.23% | NEUTRAL_CHURN` | `1,4,8,11,12,15,17` | `OK` |
| Funding 8H% / Ann% / 90D Pct | `+0.0072% (+7.9%/yr) · 90D Pct:53.7%` | `0,4,9,11,15,16,19,20` | `OK` |
| Perp Basis ($ / Ann %) | `-28.7$ (-0.047% | Carry:+7.30%/yr)` | `1,4` | `OK` |
| 5m Taker L/S & Top/Glb Acct | `5m:1.000 (Δ:+1.5) | Top:1.83(65L) · Glb:2.57` | `1,2,15,16` | `OK` |
| Options OI & Put/Call (Deribit) | `P/C:0.809 · TotOI:436,252 BTC` | `Macro,19` | `OK` |
| Options IV Term & Skew (Deribit) | `F:50.7% · B:46.3% · 25dSk:+9.1%` | `Macro,6,19` | `OK` |
| Vol: DVOL, RV20, GK & BBW% | `DVOL:52.9 · RV20:46.8% · GK:77.4% · BBW:97% · Sk20:-0.49` | `0,4,6,16,19` | `OK` |
| Upper / Lower Liq Magnet | `Up:$76,334.44 | Dn:$59,516.27` | `0,2,13,17` | `OK` |
| Magnet Ratios & LSCE | `Imm:1.81x · Ladder:1.38x · Pull:0.55x · LSCE:UNTESTED` | `13,17` | `OK` |
| Modeled Liq Ladder (10x-100x) | `Up[10x:$66,667.92($78M) / 25x:$63,031.49($105M) / 50-100x:$61,213.27($194M)] | Dn[100x:$60,001.13($350M) / 25x:$58,182.91($336M) / 10x:$54,546.48($236M)] [Modeled] (L/S:global_account_ls_ratio)` | `17` | `OK` |
| Liquidations (1H / 24H) & Flush | `DATA UNAVAILABLE` | `0,8,12,13` | `UNAVAILABLE` |

## 4. ON-CHAIN, ETF & STABLECOIN FLOWS
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| MVRV Ratio (On-Chain / Proxy) | `1.152 [CoinMetrics 2026-11-23]` | `Macro,16` | `OK` |
| On-Chain SOPR / aSOPR | `DATA UNAVAILABLE` | `16` | `UNAVAILABLE` |
| Exchange Netflow 24H (CM) | `Net:+9,379.1 BTC (+$574.5M) | In:40,663 Out:31,284` | `Macro,16` | `OK` |
| BTC Exchange Reserves (CM) | `2,708,749 BTC (2026-11-23)` | `Macro,16` | `OK` |
| Stablecoins USDT+USDC Supply | `$243.77B (USDT:$174.64B · USDC:$69.13B)` | `Macro` | `OK` |
| Stablecoin Net Issuance (7D/30D) | `7D:-0.88B · 30D:-10.38B` | `Macro` | `OK` |
| US Spot ETF Flow (Farside 1D/3D) | `1D:-$569.7M | 3D:-$1.82B | 5D:-$2.37B` | `2,13` | `OK` |
| US ETF Tape Proxy (IBIT+FBTC) | `1DVol:$3.01B · 5D:-$8.08B [PROXY]` | `Macro,2,13` | `PROXY` |
| Power-Law Fair & ATH DD% | `$150,426.87 (-59.7%) | DD:-52.0%` | `3` | `OK` |
| MTF MACD (1D / 1H Status) | `1D=negative_slope (Macro Whipsaw Veto) | 1H=negative_slope / NEUTRAL` | `13,16,18` | `OK` |

## 5. MACRO, CREDIT & US LIQUIDITY
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| US SOFR Rate & Vol (NY Fed) | `3.92% (Vol:$3,141B)` | `Macro` | `OK` |
| Fed ON RRP Balance (NY Fed) | `$0.35B` | `Macro` | `OK` |
| Credit Spread HYG/LQD & 5D% | `0.7363 (-1.36% 5D)` | `Macro,3` | `OK` |
| DXY / US 10Y (^TNX) | `104.31 (RISING (+0.82 over 5d)) | 10Y:4.92%` | `3,13` | `OK` |
| TIPS Real (DFII10) / BEI | `Real:+2.79% | BEI:2.13%` | `3,13` | `OK` |
| S&P 500 / Nasdaq (1D%) | `SPX:7,237 (+4.73%) | NDX:24,090` | `3,13` | `OK` |
| VIX / Brent Crude (BZ=F) | `VIX:26.62 | Brent:$86.32` | `3,13` | `OK` |
| BTC-SPX Corr (20D / 60D) | `20D:+0.68 | 60D:+0.74` | `3` | `OK` |
| Fear & Greed / BTC Dom% | `F&G:11 (Extreme Fear) | Dom:57.80%` | `3,13` | `OK` |
| USD Macro Calendar (High) | `Core PCE Price Index m/m (in 30.6h Fc:0.3%) | Prelim GDP q/q (in 30.6h Fc:3.5%)` | `Macro` | `OK` |
| Manual Context Overrides | `Legacy_200D_Veto_Override: IGNORED (Tab1_Flag=True) · Filter=NONE_SIGNIFICANT` | `2,13` | `OK` |

## 6. QUANT FEATURES, FEED HEALTH & ARCHIVE
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| Rough Path Lévy (A_SP / MM) | `4H A_SP:-0.2273 | MM PriceFlow:-1.6221 · Rough:2.170` | `5,19` | `OK` |
| Hurst / Kalman Vel / FracDiff | `H:0.768 · KVel:-30.60 · d:0.15` | `5,6` | `OK` |
| Hilbert Cycle / TD9 / TellTale | `Cyc:9.0b · TD(1H/4H):1/4 · RV(15m/5m):0.28/N/A` | `5,9,13` | `OK` |
| VCR 72H & TSFM Disp% | `VCR:16.64 | Disp:1.28%` | `6` | `OK` |
| Open FVGs & Sweep FSM | `FVGs:6 | FSM:None (0/12)` | `1,8` | `OK` |
| WebSocket Feeds & Warmup | `Spot:SYNC (no tick) | Perp:SYNC (no tick) | CB:SYNC (12s ago) | Warm:YES` | `Live Feeds` | `STALE` |
| Spot Klines (1W/1D/4H/1H/15m) | `1W:100 1D:500 bars · 11-24 00:00 UTC | 4H:500 1H:720 15m:240` | `All Tabs` | `OK` |
| Perp Klines / Est. Excluded | `1D:101 · 1H:720 · 15m:240 (Excl=399)` | `1,4,11,15,19` | `OK` |
| Closed 4H Anchor (Tab 19/20) | `2026-11-24 04:00:00 UTC` | `18,19,20` | `OK` |
| B1/B2 Rec & Companion Liq | `Rec:PASS (0s delta) | Liq:N/A` | `8,13,17` | `OK` |
| Telemetry History Archive (SQLite) | `51 bars logged (Last: 2026-11-24 04:00:00 UTC)` | `DB Archive` | `OK` |

## 7. RECENT CLOSED-4H SNAPSHOT TRAJECTORY (SQLITE ARCHIVE)
| Closed 4H Bar (UTC) | Spot ($) | 24H Spot/Perp CVD | Cross-Exch Perp OI & Funding | Funding 8H% / 90D Pct | MVRV Ratio |
|---|---|---|---|---|---|
| `2026-11-24 04:00:00 UTC` | `$60,590.63` | `24h:+91.8/+1542.6 BTC` | `160,011 BTC ($9.68B) · F:+0.0037% [BN+BYB+OKX 3/3]` | `+0.0064% (+7.0%/yr) · 90D Pct:53.7%` | `1.152 [CoinMetrics 2026-11-23]` |
| `2026-11-24 00:00:00 UTC` | `$61,264.47` | `24h:+137.8/+4242.8 BTC` | `156,193 BTC ($9.55B) · F:+0.0046% [BN+BYB+OKX 3/3]` | `+0.0028% (+3.0%/yr) · 90D Pct:53.7%` | `1.148 [CoinMetrics 2026-11-22]` |
| `2026-11-23 20:00:00 UTC` | `$61,236.49` | `24h:+199.3/+4098.4 BTC` | `156,190 BTC ($9.54B) · F:+0.0057% [BN+BYB+OKX 3/3]` | `+0.0065% (+7.2%/yr) · 90D Pct:31.9%` | `1.148 [CoinMetrics 2026-11-22]` |
| `2026-11-23 12:00:00 UTC` | `$61,435.55` | `24h:+179.9/+2659.2 BTC` | `158,351 BTC ($9.71B) · F:+0.0016% [BN+BYB+OKX 3/3]` | `+0.0026% (+2.9%/yr) · 90D Pct:9.6%` | `1.148 [CoinMetrics 2026-11-22]` |
| `2026-11-23 08:00:00 UTC` | `$61,488.01` | `24h:+492.9/+2793.6 BTC` | `158,177 BTC ($9.71B) · F:+0.0024% [BN+BYB+OKX 3/3]` | `+0.0035% (+3.8%/yr) · 90D Pct:9.6%` | `1.148 [CoinMetrics 2026-11-22]` |
| `2026-11-23 04:00:00 UTC` | `$61,260.01` | `24h:+719.3/+4846.5 BTC` | `156,913 BTC ($9.59B) · F:+0.0036% [BN+BYB+OKX 3/3]` | `+0.0034% (+3.7%/yr) · 90D Pct:17.8%` | `1.148 [CoinMetrics 2026-11-22]` |

### 7A. 500-BAR MARKET STRUCTURE & HISTORICAL S/R ZONES (`1D / 4H / 1H`)
| TF (Bars) | Swing Structure | Last Swing Pivots | Latest BOS | Resistance Zones (Above Spot) | Support Zones (Below Spot) |
|---|---|---|---|---|---|
| `1D (499)` | `DOWNTREND (LH/LL)` | `SH:$81,196.01 (11-04) · SL:$79,800.00 (10-15)` | `BOS Down < $79,800.00 (10-29)` | `$62,440.17 (3x), $65,182.19 (5x), $67,124.15 (2x)` | `$60,000.00 (1x), $59,130.91 (1x), $57,957.60 (2x)` |
| `4H (499)` | `DOWNTREND (LH/LL)` | `SH:$65,696.16 (11-16 12:00) · SL:$55,130.00 (11-21 04:00)` | `BOS Down < $62,062.97 (11-19 20:00)` | `$62,034.49 (2x), $63,620.51 (2x), $65,696.16 (1x)` | `$55,130.00 (1x)` |
| `1H (500)` | `MIXED (HH/LL)` | `SH:$64,603.12 (11-23 14:00) · SL:$60,763.39 (11-23 19:00)` | `BOS Down < $60,763.39 (11-24 02:00)` | `$60,845.66 (6x), $62,137.10 (7x), $63,894.86 (4x)` | `$58,768.51 (1x), $57,778.35 (1x), $55,130.00 (1x)` |

### 7B. RECENT CLOSED KLINES — OHLCV PRICE ACTION (`1D`×7, `4H`×12, `1H`×12)
**1D Closed Candles (Last 7 of 499 available, Newest First):**
| Open Time (UTC) | Open | High | Low | Close | Chg% | Vol (BTC) |
|---|---|---|---|---|---|---|
| `2026-11-23` | `$61,271.09` | `$64,603.12` | `$60,386.00` | `$61,270.93` | `-0.00%` | `27,494` |
| `2026-11-22` | `$60,215.78` | `$61,669.99` | `$58,768.51` | `$61,271.08` | `+1.75%` | `20,137` |
| `2026-11-21` | `$58,951.51` | `$60,996.00` | `$55,130.00` | `$60,215.77` | `+2.14%` | `48,558` |
| `2026-11-20` | `$61,986.73` | `$62,639.52` | `$57,778.35` | `$58,951.51` | `-4.90%` | `38,126` |
| `2026-11-19` | `$63,068.21` | `$64,080.80` | `$61,428.26` | `$61,986.73` | `-1.71%` | `19,880` |
| `2026-11-18` | `$64,947.36` | `$65,002.00` | `$62,062.97` | `$63,068.22` | `-2.89%` | `18,700` |
| `2026-11-17` | `$64,882.88` | `$65,447.00` | `$63,336.00` | `$64,947.35` | `+0.10%` | `28,317` |

**4H Closed Candles (Last 12 of 499 available, Newest First):**
| Open Time (UTC) | Open | High | Low | Close | Chg% | Vol (BTC) |
|---|---|---|---|---|---|---|
| `2026-11-24 00:00` | `$61,270.92` | `$61,682.01` | `$59,455.31` | `$60,338.34` | `-1.52%` | `4,998` |
| `2026-11-23 20:00` | `$61,257.76` | `$61,608.48` | `$61,060.60` | `$61,270.93` | `+0.02%` | `2,034` |
| `2026-11-23 16:00` | `$62,897.79` | `$62,943.45` | `$60,763.39` | `$61,257.77` | `-2.61%` | `4,477` |
| `2026-11-23 12:00` | `$61,426.01` | `$64,603.12` | `$61,070.00` | `$62,897.79` | `+2.40%` | `12,166` |
| `2026-11-23 08:00` | `$61,460.01` | `$61,941.38` | `$61,139.36` | `$61,426.01` | `-0.06%` | `2,490` |
| `2026-11-23 04:00` | `$61,285.93` | `$61,830.00` | `$61,060.00` | `$61,459.50` | `+0.28%` | `2,606` |
| `2026-11-23 00:00` | `$61,271.09` | `$61,959.93` | `$60,386.00` | `$61,285.93` | `+0.02%` | `3,722` |
| `2026-11-22 20:00` | `$60,737.12` | `$61,407.99` | `$60,581.04` | `$61,271.08` | `+0.88%` | `2,261` |
| `2026-11-22 16:00` | `$60,894.90` | `$61,411.34` | `$60,537.43` | `$60,737.12` | `-0.26%` | `2,583` |
| `2026-11-22 12:00` | `$61,062.73` | `$61,669.99` | `$60,464.01` | `$60,894.91` | `-0.27%` | `3,833` |
| `2026-11-22 08:00` | `$59,170.03` | `$61,365.24` | `$59,086.00` | `$61,062.74` | `+3.20%` | `5,842` |
| `2026-11-22 04:00` | `$59,359.99` | `$59,668.02` | `$58,768.51` | `$59,170.02` | `-0.32%` | `2,846` |

**1H Closed Candles (Last 12 of 719 available, Newest First):**
| Open Time (UTC) | Open | High | Low | Close | Chg% | Vol (BTC) |
|---|---|---|---|---|---|---|
| `2026-11-24 05:00` | `$60,379.65` | `$60,768.56` | `$60,322.49` | `$60,628.99` | `+0.41%` | `500` |
| `2026-11-24 04:00` | `$60,338.34` | `$60,691.02` | `$60,282.00` | `$60,379.66` | `+0.07%` | `608` |
| `2026-11-24 03:00` | `$60,074.90` | `$60,410.19` | `$59,455.31` | `$60,338.34` | `+0.44%` | `2,091` |
| `2026-11-24 02:00` | `$61,090.84` | `$61,120.00` | `$60,072.95` | `$60,074.90` | `-1.66%` | `1,444` |
| `2026-11-24 01:00` | `$61,333.76` | `$61,682.01` | `$61,070.59` | `$61,090.84` | `-0.40%` | `475` |
| `2026-11-24 00:00` | `$61,270.92` | `$61,374.04` | `$61,041.54` | `$61,333.77` | `+0.10%` | `988` |
| `2026-11-23 23:00` | `$61,251.69` | `$61,608.48` | `$61,144.43` | `$61,270.93` | `+0.03%` | `417` |
| `2026-11-23 22:00` | `$61,334.59` | `$61,393.38` | `$61,080.00` | `$61,251.70` | `-0.14%` | `371` |
| `2026-11-23 21:00` | `$61,239.01` | `$61,454.46` | `$61,065.40` | `$61,334.59` | `+0.16%` | `522` |
| `2026-11-23 20:00` | `$61,257.76` | `$61,466.88` | `$61,060.60` | `$61,239.00` | `-0.03%` | `724` |
| `2026-11-23 19:00` | `$61,375.96` | `$61,770.01` | `$60,763.39` | `$61,257.77` | `-0.19%` | `848` |
| `2026-11-23 18:00` | `$61,674.17` | `$61,757.36` | `$61,315.79` | `$61,375.96` | `-0.48%` | `617` |

### 7C. MODELED LIQUIDATION LADDER (`10x-100x`) & USD MACRO CALENDAR
**6-Tier Modeled Liquidation Ladder (`global_account_ls_ratio`):**
| Tier | Side | Level ($) | Dist% | Est Pool ($M) |
|---|---|---|---|---|
| `10x Shorts` | `UPPER` | `$66,667.92` | `+10.00%` | `$78.5M` |
| `25x Shorts` | `UPPER` | `$63,031.49` | `+4.00%` | `$104.7M` |
| `50-100x Shorts` | `UPPER` | `$61,213.27` | `+1.00%` | `$193.8M` |
| `100x Longs` | `LOWER` | `$60,001.13` | `-1.00%` | `$350.0M` |
| `25x Longs` | `LOWER` | `$58,182.91` | `-4.00%` | `$336.4M` |
| `10x Longs` | `LOWER` | `$54,546.48` | `-10.00%` | `$235.5M` |

**Upcoming USD High-Impact Macro Events (`-60m` to `+7d`):**
| Event | Time (UTC) | Countdown | Forecast | Previous |
|---|---|---|---|---|
| `Core PCE Price Index m/m` | `2026-11-25T13:30:00Z` | `in 30.6h` | `0.3%` | `0.3%` |
| `Prelim GDP q/q` | `2026-11-25T13:30:00Z` | `in 30.6h` | `3.5%` | `3.4%` |

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
