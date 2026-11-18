# TAB [D: DATA HUB] | CONSOLIDATED DATA-ONLY TELEMETRY REPORT
**Retrieval Time (UTC):** `2026-11-18 10:04:40 UTC`  |  **Retrieval Time (SGT):** `2026-11-18 18:04:40 SGT (UTC+8)`
**Spot Price (BTCUSDT):** `$64,571.19`  |  **Coverage:** `OK=67/71 | UNAVAILABLE=2 | STALE=1 (Genuine=0, Expected_Headless_WS_Offline=1) | PROXY/STATIC=1`
**24H Range:** `$63,336.00 - $65,447.00`  |  **Returns (24H / 7D / 30D):** `+0.71% / -12.76% / -21.20%`
**Archive (SQLite):** `20 closed-4H snapshots (Last: 2026-11-18 08:00:00 UTC)`

## 0. BIDIRECTIONAL REGIME ROUTER (GATE 0 — DUAL-INVENTORY SPOT WORKSTATION)
| Router Field | Value | Rule / Threshold |
|---|---|---|
| Latest Closed 1D Candle Close | `$64,947.35 (1D bar 2026-11-17 · closed 2026-11-18 00:00 UTC)` | `Same closed Binance Spot 1D series only (live candle excluded)` |
| Current 1D SMA 200 | `$72,854.74` | `200-bar SMA of same closed Binance Spot 1D series` |
| Distance vs 1D SMA 200 | `-10.85% (-$7,907.39)` | `(Closed 1D Close - 1D SMA 200) / 1D SMA 200` |
| 1D SMA 200 Position | `BELOW` | `BELOW if Closed 1D Close < 1D SMA 200 else ABOVE` |
| Closed 4H Market Structure (`7A`) | `MIXED (LH/HL)` | `UPTREND / DOWNTREND / MIXED (500 closed 4H bars)` |
| 4H Downside BOS Status (`7A`) | `YES (BOS Down < $63,905.01 (11-17 16:00))` | `YES if latest closed 4H BOS is BOS Down else NO` |
| Upcoming Macro Event Caution (`7C`) | `CAUTION (<24h: FOMC Meeting Minutes in 8.9h)` | `CAUTION (<24h USD high-impact event) else CLEAR` |
| Timestamp & Candle Closed Status | `2026-11-18 10:04:40 UTC | 2026-11-18 18:04:40 SGT (UTC+8) · Closed-Candle Inputs Only` | `Strict closed-bar verification gate` |

**BIDIRECTIONAL REGIME ROUTER STATUS:**
- **Active Route:** `MACRO_DOWNTREND_DISTRIBUTION`
- **Primary Active Rail:** `RAIL A — BTC -> USDT CONVERSION (DEFENSIVE / SELL RALLIES)`
- **Active BTC Inventory (`Rail A: BTC -> USDT`):** `ACTIVE (RAIL A) — CONVERT INTO OVERHEAD RESISTANCE`
- **Active USDT Inventory (`Rail B: USDT -> BTC`):** `RESTRICTED (RAIL B) — HOLD PENDING VALIDATED SWEEP & RECLAIM`
- **Condition A (`1D Close < 1D SMA 200`):** `YES`  |  **Condition B (`4H Downside Structure / BOS`):** `YES`

## 1. PRICE, TREND & MARKET STRUCTURE
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| Binance Spot / Perp ($) | `$64,571.19 / $64,536.00` | `All Tabs` | `OK` |
| Coinbase Spot ($) | `$64,494.60` | `1,11,15,17` | `OK` |
| 1D SMA 200 / Slope | `$72,854.74 (-0.39%)` | `0,2,3,11,15,18` | `OK` |
| 1D SMA 50 / EMA 50 | `$79,080.93 / $75,774.84` | `0,2,4,15,18,20` | `OK` |
| 1D EMA 21 / 1W EMA 50 | `$71,882.57 / $77,779.42` | `3,18` | `OK` |
| 4H EMA 50 / EMA 200 | `$68,022.87 / $74,910.74` | `7,13,18,20` | `OK` |
| Grok EMA 9/21 & 1H SMA200 | `9:$64,604.18 · 21:$64,555.42 · 1H:$68,488.71` | `5,15` | `OK` |
| Daily / Weekly VWAP (Z) | `D:$64,589.76 (-0.12σ) | W:$66,799.85` | `4,11,15` | `OK` |
| RSI(14) 1D / 4H & 4H ROC12 | `1D:23.5 · 4H:42.6 · ROC:-0.17%` | `3,7,20` | `OK` |
| ADX(14) 1D/4H & ATR(14) 1D/4H/1H | `ADX 1D:39.0 4H:49.4 | ATR:$2,603.21/$1,178.33/$443.47` | `0,1,2,8,13,18,20` | `OK` |
| 4H ATR(14)% Pctile & RelVol(20) | `ATR%:1.85% (82th pct/120b) · RelVol:0.45x` | `0,1,2,20` | `OK` |
| Macro 30D VAH / POC / VAL | `$79,842.68 / $64,962.88 / $62,292.15` | `1,3,6,11,19` | `OK` |
| Structure (L20/H20, PW, Asia) | `4H:$62,006.00-$81,971.00 | PW:$62,006.00-$75,599.22 | Asia:$64,136.00-$65,002.00` | `0,8,11,19` | `OK` |

## 2. ORDER FLOW, FOOTPRINT & LIQUIDITY
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| Spot/Perp CVD (15m / 1h) | `15m:+0.4/+18.6 | 1h:+5.8/+63.9 BTC` | `1,8,15` | `OK` |
| Spot/Perp CVD (4h / 24h) | `4h:-59.7/-160.3 | 24h:+1253.0/-1116.7 BTC` | `0,1,15,16,17` | `OK` |
| Spot CVD Slopes (7D / 14D) | `7D:-2,489.8 BTC | 14D:-412.6 BTC` | `17` | `OK` |
| Session / UTC-Day CVD | `Sess S:+0.0 P:+0.0 | Day S:-22.8 P:-423.0` | `REST 15m` | `OK` |
| 24H Z-Scores (z_S / z_F / D) | `z_S:+1.70 · z_F:+0.46 · D:+1.24` | `1,19` | `OK` |
| 15m Footprint Delta / Stack | `Δ:+0.4 BTC (Prev:+19.0) · Stacks:0` | `1,11` | `OK` |
| Coinbase Premium ($ / % / Z) | `-76.6$ (-0.119%, Z=+0.08)` | `1,11,15` | `OK` |
| Cross-Exch 24H Spot Vol (BN/CB) | `BN:20,515 · CB:10,187 · Tot:30,702 BTC` | `1,11,Macro` | `OK` |
| L2 Depth ±1%/±2%, OBI & Spread | `1%:0.93x · 2%:1.13x · Spr:0.0015bps · OBI:-3.7%` | `16,Macro` | `OK` |
| Tactical 7D / Session 24H VP | `7D:$68,675.51/$65,047.29/$63,339.90 | 24H:$65,183.12/$64,620.19/$64,057.26` | `1,11` | `OK` |
| 30D VA Pos% & Dist to VAL | `13.0% | +3.66% (+5.14 ATR)` | `1` | `OK` |
| SLSP Support / Resistance | `Sup:$63,288.75 | Res:$65,192.25` | `13` | `OK` |

## 3. DERIVATIVES, OPTIONS & LIQUIDATIONS
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| BN Open Interest (BTC / USD) | `92,092 BTC ($5.94B)` | `0,1,4,15,17` | `OK` |
| Cross-Exch Perp OI & Funding | `158,240 BTC ($10.21B) · F:+0.0020% [BN+BYB+OKX 3/3]` | `Macro,15` | `OK` |
| Hyperliquid Perp OI & Funding | `40,461 BTC ($2.61B) · F:+0.0100% [HL DEX]` | `Macro,15` | `OK` |
| OI Δ% (15m/1h/4h/24h) & Quad | `-0.00%/-0.04%/+1.10%/-1.64% | NEUTRAL_CHURN` | `1,4,8,11,12,15,17` | `OK` |
| Funding 8H% / Ann% / 90D Pct | `+0.0006% (+0.7%/yr) · 90D Pct:19.3%` | `0,4,9,11,15,16,19,20` | `OK` |
| Perp Basis ($ / Ann %) | `-35.2$ (-0.054% | Carry:+0.10%/yr)` | `1,4` | `OK` |
| 5m Taker L/S & Top/Glb Acct | `5m:0.846 (Δ:-4.8) | Top:1.70(63L) · Glb:2.69` | `1,2,15,16` | `OK` |
| Options OI & Put/Call (Deribit) | `P/C:0.775 · TotOI:393,540 BTC` | `Macro,19` | `OK` |
| Options IV Term & Skew (Deribit) | `F:41.7% · B:41.2% · 25dSk:+6.3%` | `Macro,6,19` | `OK` |
| Vol: DVOL, RV20, GK & BBW% | `DVOL:44.3 · RV20:46.5% · GK:51.8% · BBW:87% · Sk20:-0.57` | `0,4,6,16,19` | `OK` |
| Upper / Lower Liq Magnet | `Up:$76,334.44 | Dn:$63,408.91` | `0,2,13,17` | `OK` |
| Magnet Ratios & LSCE | `Imm:1.81x · Ladder:1.79x · Pull:0.55x · LSCE:UNTESTED` | `13,17` | `OK` |
| Modeled Liq Ladder (10x-100x) | `Up[10x:$67,428.45($100M) / 25x:$66,431.97($134M) / 50-100x:$65,774.23($194M)] | Dn[100x:$63,408.91($350M) / 25x:$62,575.97($309M) / 10x:$61,637.33($216M)] [Modeled]` | `17` | `OK` |
| Liquidations (1H / 24H) & Flush | `DATA UNAVAILABLE` | `0,8,12,13` | `UNAVAILABLE` |

## 4. ON-CHAIN, ETF & STABLECOIN FLOWS
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| MVRV Ratio (On-Chain / Proxy) | `1.212 [CoinMetrics 2026-11-17]` | `Macro,16` | `OK` |
| On-Chain SOPR / aSOPR | `DATA UNAVAILABLE` | `16` | `UNAVAILABLE` |
| Exchange Netflow 24H (CM) | `Net:-4,374.7 BTC (-$284.0M) | In:28,668 Out:33,043` | `Macro,16` | `OK` |
| BTC Exchange Reserves (CM) | `2,707,552 BTC (2026-11-17)` | `Macro,16` | `OK` |
| Stablecoins USDT+USDC Supply | `$244.37B (USDT:$175.22B · USDC:$69.16B)` | `Macro` | `OK` |
| Stablecoin Net Issuance (7D/30D) | `7D:-1.52B · 30D:-11.60B` | `Macro` | `OK` |
| US Spot ETF Flow (Farside 1D/3D) | `1D:-$239.9M | 3D:-$417.4M | 5D:-$1.00B` | `2,13` | `OK` |
| US ETF Tape Proxy (IBIT+FBTC) | `1DVol:$1.98B · 5D:-$7.40B [PROXY]` | `Macro,2,13` | `PROXY` |
| Power-Law Fair & ATH DD% | `$149,661.42 (-56.9%) | DD:-48.8%` | `3` | `OK` |
| MTF MACD (1D / 1H Status) | `1D=negative_slope (Macro Whipsaw Veto) | 1H=positive_slope CROSS` | `13,16,18` | `OK` |

## 5. MACRO, CREDIT & US LIQUIDITY
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| US SOFR Rate & Vol (NY Fed) | `3.93% (Vol:$3,170B)` | `Macro` | `OK` |
| Fed ON RRP Balance (NY Fed) | `$0.35B` | `Macro` | `OK` |
| Credit Spread HYG/LQD & 5D% | `0.7459 (+0.39% 5D)` | `Macro,3` | `OK` |
| DXY / US 10Y (^TNX) | `103.76 (RISING (+0.59 over 5d)) | 10Y:5.10%` | `3,13` | `OK` |
| TIPS Real (DFII10) / BEI | `Real:+2.89% | BEI:2.21%` | `3,13` | `OK` |
| S&P 500 / Nasdaq (1D%) | `SPX:7,341 (-1.03%) | NDX:24,328` | `3,13` | `OK` |
| VIX / Brent Crude (BZ=F) | `VIX:23.60 | Brent:$89.17` | `3,13` | `OK` |
| BTC-SPX Corr (20D / 60D) | `20D:+0.54 | 60D:+0.56` | `3` | `OK` |
| Fear & Greed / BTC Dom% | `F&G:11 (Extreme Fear) | Dom:59.10%` | `3,13` | `OK` |
| USD Macro Calendar (High) | `FOMC Meeting Minutes (in 8.9h)` | `Macro` | `OK` |
| Manual Context Overrides | `Legacy_200D_Veto_Override: IGNORED (Tab1_Flag=False) · Filter=NONE_SIGNIFICANT` | `2,13` | `OK` |

## 6. QUANT FEATURES, FEED HEALTH & ARCHIVE
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| Rough Path Lévy (A_SP / MM) | `4H A_SP:+1.3082 | MM PriceFlow:-0.0015 · Rough:15.570` | `5,19` | `OK` |
| Hurst / Kalman Vel / FracDiff | `H:0.487 · KVel:-55.80 · d:0.20` | `5,6` | `OK` |
| Hilbert Cycle / TD9 / TellTale | `Cyc:8.0b · TD(1H/4H):2/2 · RV(15m/5m):0.14/N/A` | `5,9,13` | `OK` |
| VCR 72H & TSFM Disp% | `VCR:5.15 | Disp:1.28%` | `6` | `OK` |
| Open FVGs & Sweep FSM | `FVGs:3 | FSM:None (0/12)` | `1,8` | `OK` |
| WebSocket Feeds & Warmup | `Spot:SYNC (no tick) | Perp:SYNC (no tick) | CB:SYNC (12s ago) | Warm:YES` | `Live Feeds` | `STALE` |
| Spot Klines (1W/1D/4H/1H/15m) | `1W:100 1D:500 bars · 11-18 00:00 UTC | 4H:500 1H:720 15m:240` | `All Tabs` | `OK` |
| Perp Klines / Est. Excluded | `1D:101 · 1H:720 · 15m:240 (Excl=399)` | `1,4,11,15,19` | `OK` |
| Closed 4H Anchor (Tab 19/20) | `2026-11-18 08:00:00 UTC` | `18,19,20` | `OK` |
| B1/B2 Rec & Companion Liq | `Rec:PASS (0s delta) | Liq:N/A` | `8,13,17` | `OK` |
| Telemetry History Archive (SQLite) | `20 bars logged (Last: 2026-11-18 08:00:00 UTC)` | `DB Archive` | `OK` |

## 7. RECENT CLOSED-4H SNAPSHOT TRAJECTORY (SQLITE ARCHIVE)
| Closed 4H Bar (UTC) | Spot ($) | 24H Spot/Perp CVD | Cross-Exch Perp OI & Funding | Funding 8H% / 90D Pct | MVRV Ratio |
|---|---|---|---|---|---|
| `2026-11-18 08:00:00 UTC` | `$64,571.19` | `24h:+1253.0/-1116.7 BTC` | `158,240 BTC ($10.21B) · F:+0.0020% [BN+BYB+OKX 3/3]` | `+0.0006% (+0.7%/yr) · 90D Pct:19.3%` | `1.212 [CoinMetrics 2026-11-17]` |
| `2026-11-18 04:00:00 UTC` | `$64,644.90` | `24h:+2890.4/+126.7 BTC` | `158,764 BTC ($10.25B) · F:+0.0043% [BN+BYB+OKX 3/3]` | `+0.0054% (+5.9%/yr) · 90D Pct:3.7%` | `1.212 [CoinMetrics 2026-11-17]` |
| `2026-11-18 00:00:00 UTC` | `$64,200.35` | `24h:+2603.9/-43.2 BTC` | `158,990 BTC ($10.22B) · F:+0.0036% [BN+BYB+OKX 3/3]` | `+0.0073% (+8.0%/yr) · 90D Pct:3.7%` | `1.212 [CoinMetrics 2026-11-17]` |
| `2026-11-17 20:00:00 UTC` | `$64,059.17` | `24h:+2287.0/+569.4 BTC` | `158,611 BTC ($10.14B) · F:+0.0031% [BN+BYB+OKX 3/3]` | `+0.0033% (+3.6%/yr) · 90D Pct:5.6%` | `1.212 [CoinMetrics 2026-11-16]` |
| `2026-11-17 12:00:00 UTC` | `$64,196.98` | `24h:+2974.3/-37.7 BTC` | `159,255 BTC ($10.29B) · F:+0.0036% [BN+BYB+OKX 3/3]` | `+0.0042% (+4.6%/yr) · 90D Pct:13.7%` | `1.212 [CoinMetrics 2026-11-16]` |
| `2026-11-17 08:00:00 UTC` | `$64,544.10` | `24h:+3118.1/+2008.9 BTC` | `160,724 BTC ($10.35B) · F:-0.0030% [BN+BYB+OKX 3/3]` | `-0.0032% (-3.5%/yr) · 90D Pct:13.7%` | `1.212 [CoinMetrics 2026-11-16]` |

### 7A. 500-BAR MARKET STRUCTURE & HISTORICAL S/R ZONES (`1D / 4H / 1H`)
| TF (Bars) | Swing Structure | Last Swing Pivots | Latest BOS | Resistance Zones (Above Spot) | Support Zones (Below Spot) |
|---|---|---|---|---|---|
| `1D (499)` | `DOWNTREND (LH/LL)` | `SH:$81,196.01 (11-04) · SL:$79,800.00 (10-15)` | `BOS Down < $79,800.00 (10-29)` | `$65,182.19 (5x), $67,124.15 (2x), $70,983.00 (1x)` | `$62,440.17 (3x), $60,000.00 (1x), $59,130.91 (1x)` |
| `4H (499)` | `MIXED (LH/HL)` | `SH:$65,696.16 (11-16 12:00) · SL:$63,905.01 (11-16 12:00)` | `BOS Down < $63,905.01 (11-17 16:00)` | `$65,696.16 (1x), $72,727.27 (1x), $73,510.00 (1x)` | `$63,905.01 (1x), $62,006.00 (1x)` |
| `1H (500)` | `DOWNTREND (LH/LL)` | `SH:$65,268.00 (11-17 23:00) · SL:$63,336.00 (11-17 15:00)` | `BOS Down < $66,456.00 (11-14 14:00)` | `$65,597.53 (7x), $66,456.00 (1x), $67,731.35 (3x)` | `$64,257.65 (1x), $63,620.51 (2x), $62,006.00 (1x)` |

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
| `2026-11-18 04:00` | `$64,457.68` | `$64,952.92` | `$64,312.72` | `$64,884.01` | `+0.66%` | `2,059` |
| `2026-11-18 00:00` | `$64,947.36` | `$65,002.00` | `$64,136.00` | `$64,457.96` | `-0.75%` | `2,459` |
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

**1H Closed Candles (Last 12 of 719 available, Newest First):**
| Open Time (UTC) | Open | High | Low | Close | Chg% | Vol (BTC) |
|---|---|---|---|---|---|---|
| `2026-11-18 09:00` | `$64,685.33` | `$64,785.15` | `$64,562.00` | `$64,650.84` | `-0.05%` | `392` |
| `2026-11-18 08:00` | `$64,884.00` | `$64,884.00` | `$64,532.44` | `$64,685.33` | `-0.31%` | `438` |
| `2026-11-18 07:00` | `$64,608.01` | `$64,952.92` | `$64,475.89` | `$64,884.01` | `+0.43%` | `533` |
| `2026-11-18 06:00` | `$64,680.15` | `$64,734.01` | `$64,530.69` | `$64,608.01` | `-0.11%` | `374` |
| `2026-11-18 05:00` | `$64,425.16` | `$64,859.99` | `$64,343.96` | `$64,680.15` | `+0.40%` | `489` |
| `2026-11-18 04:00` | `$64,457.68` | `$64,693.23` | `$64,312.72` | `$64,425.17` | `-0.05%` | `664` |
| `2026-11-18 03:00` | `$64,325.49` | `$64,573.91` | `$64,318.64` | `$64,457.96` | `+0.21%` | `341` |
| `2026-11-18 02:00` | `$64,303.68` | `$64,619.28` | `$64,136.00` | `$64,325.49` | `+0.03%` | `871` |
| `2026-11-18 01:00` | `$64,790.79` | `$64,790.79` | `$64,300.01` | `$64,303.68` | `-0.75%` | `778` |
| `2026-11-18 00:00` | `$64,947.36` | `$65,002.00` | `$64,698.69` | `$64,790.78` | `-0.24%` | `470` |
| `2026-11-17 23:00` | `$64,731.92` | `$65,268.00` | `$64,731.92` | `$64,947.35` | `+0.33%` | `648` |
| `2026-11-17 22:00` | `$64,358.42` | `$64,892.75` | `$64,174.20` | `$64,731.92` | `+0.58%` | `707` |

### 7C. MODELED LIQUIDATION LADDER (`10x-100x`) & USD MACRO CALENDAR
**6-Tier Modeled Liquidation Ladder:**
| Tier | Side | Level ($) | Dist% | Est Pool ($M) |
|---|---|---|---|---|
| `10x Shorts` | `UPPER` | `$67,428.45` | `+4.42%` | `$100.2M` |
| `25x Shorts` | `UPPER` | `$66,431.97` | `+2.88%` | `$133.5M` |
| `50-100x Shorts` | `UPPER` | `$65,774.23` | `+1.86%` | `$193.8M` |
| `100x Longs` | `LOWER` | `$63,408.91` | `-1.80%` | `$350.0M` |
| `25x Longs` | `LOWER` | `$62,575.97` | `-3.09%` | `$308.8M` |
| `10x Longs` | `LOWER` | `$61,637.33` | `-4.54%` | `$216.2M` |

**Upcoming USD High-Impact Macro Events (`-60m` to `+7d`):**
| Event | Time (UTC) | Countdown | Forecast | Previous |
|---|---|---|---|---|
| `FOMC Meeting Minutes` | `2026-11-18T19:00:00Z` | `in 8.9h` | `-` | `-` |

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
