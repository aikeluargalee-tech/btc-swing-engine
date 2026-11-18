# TAB [D: DATA HUB] | CONSOLIDATED DATA-ONLY TELEMETRY REPORT
**Retrieval Time (UTC):** `2026-11-18 02:48:38 UTC`  |  **Retrieval Time (SGT):** `2026-11-18 10:48:38 SGT (UTC+8)`
**Spot Price (BTCUSDT):** `$64,200.35`  |  **Coverage:** `OK=67/71 | UNAVAILABLE=2 | STALE=1 (Genuine=0, Expected_Headless_WS_Offline=1) | PROXY/STATIC=1`
**24H Range:** `$63,336.00 - $65,447.00`  |  **Returns (24H / 7D / 30D):** `-0.47% / -13.26% / -21.65%`
**Archive (SQLite):** `18 closed-4H snapshots (Last: 2026-11-18 00:00:00 UTC)`

## 0. BIDIRECTIONAL REGIME ROUTER (GATE 0 — DUAL-INVENTORY SPOT WORKSTATION)
| Router Field | Value | Rule / Threshold |
|---|---|---|
| Latest Closed 1D Candle Close | `$64,947.35 (1D bar 2026-11-17 · closed 2026-11-18 00:00 UTC)` | `Same closed Binance Spot 1D series only (live candle excluded)` |
| Current 1D SMA 200 | `$72,854.74` | `200-bar SMA of same closed Binance Spot 1D series` |
| Distance vs 1D SMA 200 | `-10.85% (-$7,907.39)` | `(Closed 1D Close - 1D SMA 200) / 1D SMA 200` |
| 1D SMA 200 Position | `BELOW` | `BELOW if Closed 1D Close < 1D SMA 200 else ABOVE` |
| Closed 4H Market Structure (`7A`) | `MIXED (LH/HL)` | `UPTREND / DOWNTREND / MIXED (500 closed 4H bars)` |
| 4H Downside BOS Status (`7A`) | `YES (BOS Down < $63,905.01 (11-17 16:00))` | `YES if latest closed 4H BOS is BOS Down else NO` |
| Upcoming Macro Event Caution (`7C`) | `CAUTION (<24h: FOMC Meeting Minutes in 16.2h)` | `CAUTION (<24h USD high-impact event) else CLEAR` |
| Timestamp & Candle Closed Status | `2026-11-18 02:48:38 UTC | 2026-11-18 10:48:38 SGT (UTC+8) · Closed-Candle Inputs Only` | `Strict closed-bar verification gate` |

**BIDIRECTIONAL REGIME ROUTER STATUS:**
- **Active Route:** `MACRO_DOWNTREND_DISTRIBUTION`
- **Primary Active Rail:** `RAIL A — BTC -> USDT CONVERSION (DEFENSIVE / SELL RALLIES)`
- **Active BTC Inventory (`Rail A: BTC -> USDT`):** `ACTIVE (RAIL A) — CONVERT INTO OVERHEAD RESISTANCE`
- **Active USDT Inventory (`Rail B: USDT -> BTC`):** `RESTRICTED (RAIL B) — HOLD PENDING VALIDATED SWEEP & RECLAIM`
- **Condition A (`1D Close < 1D SMA 200`):** `YES`  |  **Condition B (`4H Downside Structure / BOS`):** `YES`

## 1. PRICE, TREND & MARKET STRUCTURE
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| Binance Spot / Perp ($) | `$64,200.35 / $64,174.90` | `All Tabs` | `OK` |
| Coinbase Spot ($) | `$64,122.66` | `1,11,15,17` | `OK` |
| 1D SMA 200 / Slope | `$72,854.74 (-0.39%)` | `0,2,3,11,15,18` | `OK` |
| 1D SMA 50 / EMA 50 | `$79,080.93 / $75,760.29` | `0,2,4,15,18,20` | `OK` |
| 1D EMA 21 / 1W EMA 50 | `$71,848.86 / $77,764.88` | `3,18` | `OK` |
| 4H EMA 50 / EMA 200 | `$68,301.72 / $75,119.16` | `7,13,18,20` | `OK` |
| Grok EMA 9/21 & 1H SMA200 | `9:$64,402.24 · 21:$64,457.01 · 1H:$68,905.55` | `5,15` | `OK` |
| Daily / Weekly VWAP (Z) | `D:$64,559.44 (-2.13σ) | W:$67,059.18` | `4,11,15` | `OK` |
| RSI(14) 1D / 4H & 4H ROC12 | `1D:23.0 · 4H:41.8 · ROC:-0.62%` | `3,7,20` | `OK` |
| ADX(14) 1D/4H & ATR(14) 1D/4H/1H | `ADX 1D:39.0 4H:52.2 | ATR:$2,603.21/$1,285.68/$532.06` | `0,1,2,8,13,18,20` | `OK` |
| 4H ATR(14)% Pctile & RelVol(20) | `ATR%:1.95% (88th pct/120b) · RelVol:0.81x` | `0,1,2,20` | `OK` |
| Macro 30D VAH / POC / VAL | `$80,033.45 / $64,962.88 / $62,292.15` | `1,3,6,11,19` | `OK` |
| Structure (L20/H20, PW, Asia) | `4H:$62,006.00-$81,971.00 | PW:$62,006.00-$75,599.22 | Asia:$64,136.00-$65,002.00` | `0,8,11,19` | `OK` |

## 2. ORDER FLOW, FOOTPRINT & LIQUIDITY
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| Spot/Perp CVD (15m / 1h) | `15m:-4.4/+184.5 | 1h:-31.6/+386.5 BTC` | `1,8,15` | `OK` |
| Spot/Perp CVD (4h / 24h) | `4h:+55.2/+157.2 | 24h:+2603.9/-43.2 BTC` | `0,1,15,16,17` | `OK` |
| Spot CVD Slopes (7D / 14D) | `7D:-2,489.8 BTC | 14D:-412.6 BTC` | `17` | `OK` |
| Session / UTC-Day CVD | `Sess S:+0.0 P:+0.0 | Day S:-142.4 P:+22.8` | `REST 15m` | `OK` |
| 24H Z-Scores (z_S / z_F / D) | `z_S:+1.88 · z_F:+0.56 · D:+1.32` | `1,19` | `OK` |
| 15m Footprint Delta / Stack | `Δ:-4.4 BTC (Prev:-18.1) · Stacks:0` | `1,11` | `OK` |
| Coinbase Premium ($ / % / Z) | `-77.7$ (-0.121%, Z=-0.52)` | `1,11,15` | `OK` |
| Cross-Exch 24H Spot Vol (BN/CB) | `BN:27,652 · CB:11,483 · Tot:39,135 BTC` | `1,11,Macro` | `OK` |
| L2 Depth ±1%/±2%, OBI & Spread | `1%:1.30x · 2%:1.54x · Spr:0.0016bps · OBI:+13.0%` | `16,Macro` | `OK` |
| Tactical 7D / Session 24H VP | `7D:$68,782.22/$65,047.29/$63,339.90 | 24H:$65,147.94/$65,007.21/$64,197.99` | `1,11` | `OK` |
| 30D VA Pos% & Dist to VAL | `10.8% | +3.06% (+3.59 ATR)` | `1` | `OK` |
| SLSP Support / Resistance | `Sup:$63,288.75 | Res:$65,192.25` | `13` | `OK` |

## 3. DERIVATIVES, OPTIONS & LIQUIDATIONS
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| BN Open Interest (BTC / USD) | `92,618 BTC ($5.95B)` | `0,1,4,15,17` | `OK` |
| Cross-Exch Perp OI & Funding | `158,990 BTC ($10.22B) · F:+0.0036% [BN+BYB+OKX 3/3]` | `Macro,15` | `OK` |
| Hyperliquid Perp OI & Funding | `39,908 BTC ($2.56B) · F:+0.0100% [HL DEX]` | `Macro,15` | `OK` |
| OI Δ% (15m/1h/4h/24h) & Quad | `+0.02%/-0.04%/-1.44%/+0.73% | NEUTRAL_CHURN` | `1,4,8,11,12,15,17` | `OK` |
| Funding 8H% / Ann% / 90D Pct | `+0.0073% (+8.0%/yr) · 90D Pct:3.7%` | `0,4,9,11,15,16,19,20` | `OK` |
| Perp Basis ($ / Ann %) | `-25.4$ (-0.040% | Carry:+7.50%/yr)` | `1,4` | `OK` |
| 5m Taker L/S & Top/Glb Acct | `5m:94.252 (Δ:+66.9) | Top:1.77(64L) · Glb:2.78` | `1,2,15,16` | `OK` |
| Options OI & Put/Call (Deribit) | `P/C:0.781 · TotOI:396,208 BTC` | `Macro,19` | `OK` |
| Options IV Term & Skew (Deribit) | `F:42.4% · B:41.2% · 25dSk:+6.8%` | `Macro,6,19` | `OK` |
| Vol: DVOL, RV20, GK & BBW% | `DVOL:44.1 · RV20:46.5% · GK:57.9% · BBW:87% · Sk20:-0.54` | `0,4,6,16,19` | `OK` |
| Upper / Lower Liq Magnet | `Up:$76,334.44 | Dn:$63,044.74` | `0,2,13,17` | `OK` |
| Magnet Ratios & LSCE | `Imm:1.81x · Ladder:1.79x · Pull:0.55x · LSCE:UNTESTED` | `13,17` | `OK` |
| Modeled Liq Ladder (10x-100x) | `Up[10x:$67,428.45($100M) / 25x:$66,431.97($134M) / 50-100x:$65,774.23($194M)] | Dn[100x:$63,044.74($350M) / 25x:$62,414.29($309M) / 10x:$61,478.08($216M)] [Modeled]` | `17` | `OK` |
| Liquidations (1H / 24H) & Flush | `DATA UNAVAILABLE` | `0,8,12,13` | `UNAVAILABLE` |

## 4. ON-CHAIN, ETF & STABLECOIN FLOWS
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| MVRV Ratio (On-Chain / Proxy) | `1.212 [CoinMetrics 2026-11-17]` | `Macro,16` | `OK` |
| On-Chain SOPR / aSOPR | `DATA UNAVAILABLE` | `16` | `UNAVAILABLE` |
| Exchange Netflow 24H (CM) | `Net:-4,374.7 BTC (-$284.0M) | In:28,668 Out:33,043` | `Macro,16` | `OK` |
| BTC Exchange Reserves (CM) | `2,707,552 BTC (2026-11-17)` | `Macro,16` | `OK` |
| Stablecoins USDT+USDC Supply | `$244.50B (USDT:$175.21B · USDC:$69.28B)` | `Macro` | `OK` |
| Stablecoin Net Issuance (7D/30D) | `7D:-1.39B · 30D:-11.47B` | `Macro` | `OK` |
| US Spot ETF Flow (Farside 1D/3D) | `1D:-$30.4M | 3D:-$207.9M | 5D:-$791.8M` | `2,13` | `OK` |
| US ETF Tape Proxy (IBIT+FBTC) | `1DVol:$1.98B · 5D:-$7.40B [PROXY]` | `Macro,2,13` | `PROXY` |
| Power-Law Fair & ATH DD% | `$149,622.00 (-57.1%) | DD:-49.1%` | `3` | `OK` |
| MTF MACD (1D / 1H Status) | `1D=negative_slope (Macro Whipsaw Veto) | 1H=positive_slope CROSS` | `13,16,18` | `OK` |

## 5. MACRO, CREDIT & US LIQUIDITY
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| US SOFR Rate & Vol (NY Fed) | `3.93% (Vol:$3,170B)` | `Macro` | `OK` |
| Fed ON RRP Balance (NY Fed) | `$0.35B` | `Macro` | `OK` |
| Credit Spread HYG/LQD & 5D% | `0.7459 (+0.39% 5D)` | `Macro,3` | `OK` |
| DXY / US 10Y (^TNX) | `103.61 (RISING (+0.44 over 5d)) | 10Y:5.10%` | `3,13` | `OK` |
| TIPS Real (DFII10) / BEI | `Real:+2.89% | BEI:2.21%` | `3,13` | `OK` |
| S&P 500 / Nasdaq (1D%) | `SPX:7,341 (-1.03%) | NDX:24,328` | `3,13` | `OK` |
| VIX / Brent Crude (BZ=F) | `VIX:25.46 | Brent:$92.77` | `3,13` | `OK` |
| BTC-SPX Corr (20D / 60D) | `20D:+0.55 | 60D:+0.56` | `3` | `OK` |
| Fear & Greed / BTC Dom% | `F&G:11 (Extreme Fear) | Dom:58.40%` | `3,13` | `OK` |
| USD Macro Calendar (High) | `FOMC Meeting Minutes (in 16.2h)` | `Macro` | `OK` |
| Manual Context Overrides | `Legacy_200D_Veto_Override: IGNORED (Tab1_Flag=False) · Filter=NONE_SIGNIFICANT` | `2,13` | `OK` |

## 6. QUANT FEATURES, FEED HEALTH & ARCHIVE
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| Rough Path Lévy (A_SP / MM) | `4H A_SP:+1.4874 | MM PriceFlow:+0.0035 · Rough:1.500` | `5,19` | `OK` |
| Hurst / Kalman Vel / FracDiff | `H:0.466 · KVel:-56.90 · d:0.25` | `5,6` | `OK` |
| Hilbert Cycle / TD9 / TellTale | `Cyc:8.0b · TD(1H/4H):2/1 · RV(15m/5m):0.19/N/A` | `5,9,13` | `OK` |
| VCR 72H & TSFM Disp% | `VCR:5.41 | Disp:1.28%` | `6` | `OK` |
| Open FVGs & Sweep FSM | `FVGs:4 | FSM:None (0/12)` | `1,8` | `OK` |
| WebSocket Feeds & Warmup | `Spot:SYNC (no tick) | Perp:SYNC (no tick) | CB:SYNC (11s ago) | Warm:YES` | `Live Feeds` | `STALE` |
| Spot Klines (1W/1D/4H/1H/15m) | `1W:100 1D:500 bars · 11-18 00:00 UTC | 4H:500 1H:720 15m:240` | `All Tabs` | `OK` |
| Perp Klines / Est. Excluded | `1D:101 · 1H:720 · 15m:240 (Excl=399)` | `1,4,11,15,19` | `OK` |
| Closed 4H Anchor (Tab 19/20) | `2026-11-18 00:00:00 UTC` | `18,19,20` | `OK` |
| B1/B2 Rec & Companion Liq | `Rec:PASS (0s delta) | Liq:N/A` | `8,13,17` | `OK` |
| Telemetry History Archive (SQLite) | `18 bars logged (Last: 2026-11-18 00:00:00 UTC)` | `DB Archive` | `OK` |

## 7. RECENT CLOSED-4H SNAPSHOT TRAJECTORY (SQLITE ARCHIVE)
| Closed 4H Bar (UTC) | Spot ($) | 24H Spot/Perp CVD | Cross-Exch Perp OI & Funding | Funding 8H% / 90D Pct | MVRV Ratio |
|---|---|---|---|---|---|
| `2026-11-18 00:00:00 UTC` | `$64,200.35` | `24h:+2603.9/-43.2 BTC` | `158,990 BTC ($10.22B) · F:+0.0036% [BN+BYB+OKX 3/3]` | `+0.0073% (+8.0%/yr) · 90D Pct:3.7%` | `1.212 [CoinMetrics 2026-11-17]` |
| `2026-11-17 20:00:00 UTC` | `$64,059.17` | `24h:+2287.0/+569.4 BTC` | `158,611 BTC ($10.14B) · F:+0.0031% [BN+BYB+OKX 3/3]` | `+0.0033% (+3.6%/yr) · 90D Pct:5.6%` | `1.212 [CoinMetrics 2026-11-16]` |
| `2026-11-17 12:00:00 UTC` | `$64,196.98` | `24h:+2974.3/-37.7 BTC` | `159,255 BTC ($10.29B) · F:+0.0036% [BN+BYB+OKX 3/3]` | `+0.0042% (+4.6%/yr) · 90D Pct:13.7%` | `1.212 [CoinMetrics 2026-11-16]` |
| `2026-11-17 08:00:00 UTC` | `$64,544.10` | `24h:+3118.1/+2008.9 BTC` | `160,724 BTC ($10.35B) · F:-0.0030% [BN+BYB+OKX 3/3]` | `-0.0032% (-3.5%/yr) · 90D Pct:13.7%` | `1.212 [CoinMetrics 2026-11-16]` |
| `2026-11-17 04:00:00 UTC` | `$64,973.33` | `24h:+1113.5/+957.4 BTC` | `160,075 BTC ($10.39B) · F:+0.0054% [BN+BYB+OKX 3/3]` | `+0.0048% (+5.2%/yr) · 90D Pct:37.4%` | `1.212 [CoinMetrics 2026-11-16]` |
| `2026-11-17 00:00:00 UTC` | `$64,629.18` | `24h:+995.2/+491.3 BTC` | `158,085 BTC ($10.23B) · F:+0.0049% [BN+BYB+OKX 3/3]` | `+0.0037% (+4.1%/yr) · 90D Pct:37.4%` | `1.214 [CoinMetrics 2026-11-15]` |

### 7A. 500-BAR MARKET STRUCTURE & HISTORICAL S/R ZONES (`1D / 4H / 1H`)
| TF (Bars) | Swing Structure | Last Swing Pivots | Latest BOS | Resistance Zones (Above Spot) | Support Zones (Below Spot) |
|---|---|---|---|---|---|
| `1D (499)` | `DOWNTREND (LH/LL)` | `SH:$81,196.01 (11-04) · SL:$79,800.00 (10-15)` | `BOS Down < $79,800.00 (10-29)` | `$65,182.19 (5x), $67,124.15 (2x), $70,983.00 (1x)` | `$62,440.17 (3x), $60,000.00 (1x), $59,130.91 (1x)` |
| `4H (499)` | `MIXED (LH/HL)` | `SH:$65,696.16 (11-16 12:00) · SL:$63,905.01 (11-16 12:00)` | `BOS Down < $63,905.01 (11-17 16:00)` | `$65,696.16 (1x), $72,727.27 (1x), $73,510.00 (1x)` | `$63,905.01 (1x), $62,006.00 (1x)` |
| `1H (500)` | `DOWNTREND (LH/LL)` | `SH:$65,447.00 (11-17 14:00) · SL:$63,336.00 (11-17 15:00)` | `BOS Down < $66,456.00 (11-14 14:00)` | `$65,652.46 (6x), $66,456.00 (1x), $67,731.35 (3x)` | `$63,620.51 (2x), $62,006.00 (1x)` |

### 7B. RECENT CLOSED KLINES — OHLCV PRICE ACTION (`1D`×7, `4H`×12, `1H`×12)
**1D Closed Candles (Last 7 of 499 available, Newest First):**
| Open Time (UTC) | Open | High | Low | Close | Chg% | Vol (BTC) |
|---|---|---|---|---|---|---|
| `2026-11-17` | `$64,882.88` | `$65,447.00` | `$63,336.00` | `$64,947.35` | `+0.10%` | `28,317` |
| `2026-11-16` | `$65,351.05` | `$65,696.16` | `$63,905.01` | `$64,882.87` | `-0.72%` | `21,929` |
| `2026-11-15` | `$64,150.01` | `$66,132.01` | `$62,006.00` | `$65,351.05` | `+1.87%` | `29,231` |
| `2026-11-14` | `$68,314.01` | `$68,446.21` | `$63,320.00` | `$64,150.00` | `-6.10%` | `32,675` |
| `2026-11-13` | `$71,460.00` | `$71,514.01` | `$67,568.00` | `$68,314.00` | `-4.40%` | `29,649` |
| `2026-11-12` | `$74,015.20` | `$74,217.49` | `$71,113.06` | `$71,460.00` | `-3.45%` | `15,228` |
| `2026-11-11` | `$73,796.06` | `$74,811.45` | `$73,209.12` | `$74,015.19` | `+0.30%` | `16,146` |

**4H Closed Candles (Last 12 of 499 available, Newest First):**
| Open Time (UTC) | Open | High | Low | Close | Chg% | Vol (BTC) |
|---|---|---|---|---|---|---|
| `2026-11-17 20:00` | `$63,753.74` | `$65,268.00` | `$63,685.96` | `$64,947.35` | `+1.87%` | `3,925` |
| `2026-11-17 16:00` | `$64,115.08` | `$64,483.33` | `$63,455.71` | `$63,753.75` | `-0.56%` | `3,718` |
| `2026-11-17 12:00` | `$64,995.54` | `$65,447.00` | `$63,336.00` | `$64,115.09` | `-1.35%` | `6,076` |
| `2026-11-17 08:00` | `$64,740.13` | `$65,004.98` | `$64,079.83` | `$64,995.54` | `+0.39%` | `6,538` |
| `2026-11-17 04:00` | `$65,056.53` | `$65,094.60` | `$64,303.64` | `$64,740.14` | `-0.49%` | `4,742` |
| `2026-11-17 00:00` | `$64,882.88` | `$65,200.00` | `$64,385.99` | `$65,056.52` | `+0.27%` | `3,319` |
| `2026-11-16 20:00` | `$65,068.00` | `$65,534.94` | `$64,788.11` | `$64,882.87` | `-0.28%` | `3,028` |
| `2026-11-16 16:00` | `$64,467.00` | `$65,190.08` | `$64,228.01` | `$65,068.01` | `+0.93%` | `4,001` |
| `2026-11-16 12:00` | `$64,448.32` | `$65,696.16` | `$63,905.01` | `$64,467.00` | `+0.03%` | `4,865` |
| `2026-11-16 08:00` | `$64,995.13` | `$64,995.28` | `$64,128.00` | `$64,448.32` | `-0.84%` | `3,169` |
| `2026-11-16 04:00` | `$65,113.93` | `$65,190.00` | `$64,294.11` | `$64,995.12` | `-0.18%` | `3,052` |
| `2026-11-16 00:00` | `$65,351.05` | `$65,392.01` | `$64,530.12` | `$65,113.92` | `-0.36%` | `3,814` |

**1H Closed Candles (Last 12 of 719 available, Newest First):**
| Open Time (UTC) | Open | High | Low | Close | Chg% | Vol (BTC) |
|---|---|---|---|---|---|---|
| `2026-11-18 01:00` | `$64,790.79` | `$64,790.79` | `$64,300.01` | `$64,303.68` | `-0.75%` | `778` |
| `2026-11-18 00:00` | `$64,947.36` | `$65,002.00` | `$64,698.69` | `$64,790.78` | `-0.24%` | `470` |
| `2026-11-17 23:00` | `$64,731.92` | `$65,268.00` | `$64,731.92` | `$64,947.35` | `+0.33%` | `648` |
| `2026-11-17 22:00` | `$64,358.42` | `$64,892.75` | `$64,174.20` | `$64,731.92` | `+0.58%` | `707` |
| `2026-11-17 21:00` | `$63,997.13` | `$64,664.00` | `$63,954.79` | `$64,358.42` | `+0.56%` | `776` |
| `2026-11-17 20:00` | `$63,753.74` | `$64,120.35` | `$63,685.96` | `$63,997.13` | `+0.38%` | `1,793` |
| `2026-11-17 19:00` | `$63,774.52` | `$63,921.89` | `$63,664.13` | `$63,753.75` | `-0.03%` | `414` |
| `2026-11-17 18:00` | `$63,827.64` | `$64,094.94` | `$63,648.35` | `$63,774.53` | `-0.08%` | `804` |
| `2026-11-17 17:00` | `$63,747.09` | `$64,126.98` | `$63,535.96` | `$63,827.64` | `+0.13%` | `998` |
| `2026-11-17 16:00` | `$64,115.08` | `$64,483.33` | `$63,455.71` | `$63,747.09` | `-0.57%` | `1,502` |
| `2026-11-17 15:00` | `$65,018.00` | `$65,168.01` | `$63,336.00` | `$64,115.09` | `-1.39%` | `2,366` |
| `2026-11-17 14:00` | `$65,144.69` | `$65,447.00` | `$64,800.00` | `$65,018.01` | `-0.19%` | `1,710` |

### 7C. MODELED LIQUIDATION LADDER (`10x-100x`) & USD MACRO CALENDAR
**6-Tier Modeled Liquidation Ladder:**
| Tier | Side | Level ($) | Dist% | Est Pool ($M) |
|---|---|---|---|---|
| `10x Shorts` | `UPPER` | `$67,428.45` | `+5.03%` | `$100.1M` |
| `25x Shorts` | `UPPER` | `$66,431.97` | `+3.48%` | `$133.5M` |
| `50-100x Shorts` | `UPPER` | `$65,774.23` | `+2.45%` | `$193.8M` |
| `100x Longs` | `LOWER` | `$63,044.74` | `-1.80%` | `$350.0M` |
| `25x Longs` | `LOWER` | `$62,414.29` | `-2.78%` | `$308.8M` |
| `10x Longs` | `LOWER` | `$61,478.08` | `-4.24%` | `$216.1M` |

**Upcoming USD High-Impact Macro Events (`-60m` to `+7d`):**
| Event | Time (UTC) | Countdown | Forecast | Previous |
|---|---|---|---|---|
| `FOMC Meeting Minutes` | `2026-11-18T19:00:00Z` | `in 16.2h` | `-` | `-` |

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
