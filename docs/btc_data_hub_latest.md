# TAB [D: DATA HUB] | CONSOLIDATED DATA-ONLY TELEMETRY REPORT
**Retrieval Time (UTC):** `2026-11-19 00:10:37 UTC`  |  **Retrieval Time (SGT):** `2026-11-19 08:10:37 SGT (UTC+8)`
**Spot Price (BTCUSDT):** `$62,748.01`  |  **Coverage:** `OK=67/71 | UNAVAILABLE=2 | STALE=1 (Genuine=0, Expected_Headless_WS_Offline=1) | PROXY/STATIC=1`
**24H Range:** `$62,062.97 - $64,952.92`  |  **Returns (24H / 7D / 30D):** `-3.15% / -12.19% / -24.43%`
**Archive (SQLite):** `23 closed-4H snapshots (Last: 2026-11-19 00:00:00 UTC)`

## 0. BIDIRECTIONAL REGIME ROUTER (GATE 0 — DUAL-INVENTORY SPOT WORKSTATION)
| Router Field | Value | Rule / Threshold |
|---|---|---|
| Latest Closed 1D Candle Close | `$63,068.22 (1D bar 2026-11-18 · closed 2026-11-19 00:00 UTC)` | `Same closed Binance Spot 1D series only (live candle excluded)` |
| Current 1D SMA 200 | `$72,776.64` | `200-bar SMA of same closed Binance Spot 1D series` |
| Distance vs 1D SMA 200 | `-13.34% (-$9,708.42)` | `(Closed 1D Close - 1D SMA 200) / 1D SMA 200` |
| 1D SMA 200 Position | `BELOW` | `BELOW if Closed 1D Close < 1D SMA 200 else ABOVE` |
| Closed 4H Market Structure (`7A`) | `DOWNTREND (LH/LL)` | `UPTREND / DOWNTREND / MIXED (500 closed 4H bars)` |
| 4H Downside BOS Status (`7A`) | `YES (BOS Down < $63,336.00 (11-18 12:00))` | `YES if latest closed 4H BOS is BOS Down else NO` |
| Upcoming Macro Event Caution (`7C`) | `CLEAR (>24h / NONE)` | `CAUTION (<24h USD high-impact event) else CLEAR` |
| Timestamp & Candle Closed Status | `2026-11-19 00:10:37 UTC | 2026-11-19 08:10:37 SGT (UTC+8) · Closed-Candle Inputs Only` | `Strict closed-bar verification gate` |

**BIDIRECTIONAL REGIME ROUTER STATUS:**
- **Active Route:** `MACRO_DOWNTREND_DISTRIBUTION`
- **Primary Active Rail:** `RAIL A — BTC -> USDT CONVERSION (DEFENSIVE / SELL RALLIES)`
- **Active BTC Inventory (`Rail A: BTC -> USDT`):** `ACTIVE (RAIL A) — CONVERT INTO OVERHEAD RESISTANCE`
- **Active USDT Inventory (`Rail B: USDT -> BTC`):** `RESTRICTED (RAIL B) — HOLD PENDING VALIDATED SWEEP & RECLAIM`
- **Condition A (`1D Close < 1D SMA 200`):** `YES`  |  **Condition B (`4H Downside Structure / BOS`):** `YES`

## 1. PRICE, TREND & MARKET STRUCTURE
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| Binance Spot / Perp ($) | `$62,748.01 / $62,708.80` | `All Tabs` | `OK` |
| Coinbase Spot ($) | `$62,660.70` | `1,11,15,17` | `OK` |
| 1D SMA 200 / Slope | `$72,776.64 (-0.43%)` | `0,2,3,11,15,18` | `OK` |
| 1D SMA 50 / EMA 50 | `$78,669.02 / $75,207.35` | `0,2,4,15,18,20` | `OK` |
| 1D EMA 21 / 1W EMA 50 | `$70,927.95 / $77,707.92` | `3,18` | `OK` |
| 4H EMA 50 / EMA 200 | `$67,320.54 / $74,452.02` | `7,13,18,20` | `OK` |
| Grok EMA 9/21 & 1H SMA200 | `9:$62,888.46 · 21:$63,376.00 · 1H:$67,706.19` | `5,15` | `OK` |
| Daily / Weekly VWAP (Z) | `D:$63,538.95 (-1.00σ) | W:$66,154.87` | `4,11,15` | `OK` |
| RSI(14) 1D / 4H & 4H ROC12 | `1D:21.2 · 4H:34.8 · ROC:-2.80%` | `3,7,20` | `OK` |
| ADX(14) 1D/4H & ATR(14) 1D/4H/1H | `ADX 1D:41.6 4H:50.4 | ATR:$2,662.71/$1,186.04/$530.38` | `0,1,2,8,13,18,20` | `OK` |
| 4H ATR(14)% Pctile & RelVol(20) | `ATR%:1.89% (84th pct/120b) · RelVol:0.83x` | `0,1,2,20` | `OK` |
| Macro 30D VAH / POC / VAL | `$79,651.92 / $64,962.88 / $62,292.15` | `1,3,6,11,19` | `OK` |
| Structure (L20/H20, PW, Asia) | `4H:$62,006.00-$81,971.00 | PW:$62,006.00-$75,599.22 | Asia:$62,748.01-$63,070.00` | `0,8,11,19` | `OK` |

## 2. ORDER FLOW, FOOTPRINT & LIQUIDITY
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| Spot/Perp CVD (15m / 1h) | `15m:-56.0/-203.2 | 1h:-38.0/-232.2 BTC` | `1,8,15` | `OK` |
| Spot/Perp CVD (4h / 24h) | `4h:-3.8/-3153.9 | 24h:+164.5/-2742.3 BTC` | `0,1,15,16,17` | `OK` |
| Spot CVD Slopes (7D / 14D) | `7D:-2,711.1 BTC | 14D:-2,051.8 BTC` | `17` | `OK` |
| Session / UTC-Day CVD | `Sess S:+0.0 P:+0.0 | Day S:-56.0 P:-203.2` | `REST 15m` | `OK` |
| 24H Z-Scores (z_S / z_F / D) | `z_S:-0.04 · z_F:-0.27 · D:+0.23` | `1,19` | `OK` |
| 15m Footprint Delta / Stack | `Δ:-56.0 BTC (Prev:-5.0) · Stacks:0` | `1,11` | `OK` |
| Coinbase Premium ($ / % / Z) | `-87.3$ (-0.139%, Z=-0.40)` | `1,11,15` | `OK` |
| Cross-Exch 24H Spot Vol (BN/CB) | `BN:18,346 · CB:12,431 · Tot:30,777 BTC` | `1,11,Macro` | `OK` |
| L2 Depth ±1%/±2%, OBI & Spread | `1%:1.21x · 2%:2.54x · Spr:0.0016bps · OBI:+9.5%` | `16,Macro` | `OK` |
| Tactical 7D / Session 24H VP | `7D:$67,092.30/$64,977.20/$62,157.08 | 24H:$64,832.51/$64,639.84/$62,905.87` | `1,11` | `OK` |
| 30D VA Pos% & Dist to VAL | `2.6% | +0.73% (+0.86 ATR)` | `1` | `OK` |
| SLSP Support / Resistance | `Sup:$62,339.56 | Res:$63,276.94` | `13` | `OK` |

## 3. DERIVATIVES, OPTIONS & LIQUIDATIONS
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| BN Open Interest (BTC / USD) | `96,834 BTC ($6.09B)` | `0,1,4,15,17` | `OK` |
| Cross-Exch Perp OI & Funding | `165,337 BTC ($10.39B) · F:+0.0065% [BN+BYB+OKX 3/3]` | `Macro,15` | `OK` |
| Hyperliquid Perp OI & Funding | `38,558 BTC ($2.42B) · F:+0.0029% [HL DEX]` | `Macro,15` | `OK` |
| OI Δ% (15m/1h/4h/24h) & Quad | `+0.01%/+0.08%/-3.22%/+5.66% | NEUTRAL_CHURN` | `1,4,8,11,12,15,17` | `OK` |
| Funding 8H% / Ann% / 90D Pct | `+0.0094% (+10.3%/yr) · 90D Pct:4.8%` | `0,4,9,11,15,16,19,20` | `OK` |
| Perp Basis ($ / Ann %) | `-39.2$ (-0.062% | Carry:+9.60%/yr)` | `1,4` | `OK` |
| 5m Taker L/S & Top/Glb Acct | `5m:0.909 (Δ:-13.9) | Top:2.09(68L) · Glb:3.47` | `1,2,15,16` | `OK` |
| Options OI & Put/Call (Deribit) | `P/C:0.777 · TotOI:400,692 BTC` | `Macro,19` | `OK` |
| Options IV Term & Skew (Deribit) | `F:45.4% · B:42.4% · 25dSk:+7.9%` | `Macro,6,19` | `OK` |
| Vol: DVOL, RV20, GK & BBW% | `DVOL:45.6 · RV20:47.3% · GK:52.8% · BBW:88% · Sk20:-0.45` | `0,4,6,16,19` | `OK` |
| Upper / Lower Liq Magnet | `Up:$76,334.44 | Dn:$61,618.55` | `0,2,13,17` | `OK` |
| Magnet Ratios & LSCE | `Imm:1.81x · Ladder:1.79x · Pull:0.55x · LSCE:UNTESTED` | `13,17` | `OK` |
| Modeled Liq Ladder (10x-100x) | `Up[10x:$66,919.42($102M) / 25x:$65,930.46($136M) / 50-100x:$65,277.68($194M)] | Dn[100x:$61,618.55($350M) / 25x:$61,002.36($316M) / 10x:$60,087.32($221M)] [Modeled]` | `17` | `OK` |
| Liquidations (1H / 24H) & Flush | `DATA UNAVAILABLE` | `0,8,12,13` | `UNAVAILABLE` |

## 4. ON-CHAIN, ETF & STABLECOIN FLOWS
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| MVRV Ratio (On-Chain / Proxy) | `1.212 [CoinMetrics 2026-11-17]` | `Macro,16` | `OK` |
| On-Chain SOPR / aSOPR | `DATA UNAVAILABLE` | `16` | `UNAVAILABLE` |
| Exchange Netflow 24H (CM) | `Net:-4,374.7 BTC (-$284.0M) | In:28,668 Out:33,043` | `Macro,16` | `OK` |
| BTC Exchange Reserves (CM) | `2,707,552 BTC (2026-11-17)` | `Macro,16` | `OK` |
| Stablecoins USDT+USDC Supply | `$243.49B (USDT:$175.09B · USDC:$68.39B)` | `Macro` | `OK` |
| Stablecoin Net Issuance (7D/30D) | `7D:-2.36B · 30D:-12.44B` | `Macro` | `OK` |
| US Spot ETF Flow (Farside 1D/3D) | `1D:-$86.7M | 3D:-$318.7M | 5D:-$788.2M` | `2,13` | `OK` |
| US ETF Tape Proxy (IBIT+FBTC) | `1DVol:$2.23B · 5D:-$11.67B [PROXY]` | `Macro,2,13` | `PROXY` |
| Power-Law Fair & ATH DD% | `$149,737.93 (-58.1%) | DD:-50.3%` | `3` | `OK` |
| MTF MACD (1D / 1H Status) | `1D=negative_slope (Macro Whipsaw Veto) | 1H=negative_slope / NEUTRAL` | `13,16,18` | `OK` |

## 5. MACRO, CREDIT & US LIQUIDITY
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| US SOFR Rate & Vol (NY Fed) | `3.92% (Vol:$3,173B)` | `Macro` | `OK` |
| Fed ON RRP Balance (NY Fed) | `$0.33B` | `Macro` | `OK` |
| Credit Spread HYG/LQD & 5D% | `0.7431 (-0.13% 5D)` | `Macro,3` | `OK` |
| DXY / US 10Y (^TNX) | `103.81 (RISING (+0.64 over 5d)) | 10Y:5.07%` | `3,13` | `OK` |
| TIPS Real (DFII10) / BEI | `Real:+2.88% | BEI:2.19%` | `3,13` | `OK` |
| S&P 500 / Nasdaq (1D%) | `SPX:7,324 (-0.23%) | NDX:24,430` | `3,13` | `OK` |
| VIX / Brent Crude (BZ=F) | `VIX:24.56 | Brent:$88.73` | `3,13` | `OK` |
| BTC-SPX Corr (20D / 60D) | `20D:+0.60 | 60D:+0.62` | `3` | `OK` |
| Fear & Greed / BTC Dom% | `F&G:10 (Extreme Fear) | Dom:58.10%` | `3,13` | `OK` |
| USD Macro Calendar (High) | `NONE (next 7d)` | `Macro` | `OK` |
| Manual Context Overrides | `Legacy_200D_Veto_Override: IGNORED (Tab1_Flag=False) · Filter=NONE_SIGNIFICANT` | `2,13` | `OK` |

## 6. QUANT FEATURES, FEED HEALTH & ARCHIVE
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| Rough Path Lévy (A_SP / MM) | `4H A_SP:+2.6726 | MM PriceFlow:+0.0014 · Rough:0.640` | `5,19` | `OK` |
| Hurst / Kalman Vel / FracDiff | `H:0.573 · KVel:-54.40 · d:0.20` | `5,6` | `OK` |
| Hilbert Cycle / TD9 / TellTale | `Cyc:72.0b · TD(1H/4H):2/4 · RV(15m/5m):0.61/N/A` | `5,9,13` | `OK` |
| VCR 72H & TSFM Disp% | `VCR:6.73 | Disp:1.28%` | `6` | `OK` |
| Open FVGs & Sweep FSM | `FVGs:7 | FSM:None (0/12)` | `1,8` | `OK` |
| WebSocket Feeds & Warmup | `Spot:SYNC (no tick) | Perp:SYNC (no tick) | CB:SYNC (11s ago) | Warm:YES` | `Live Feeds` | `STALE` |
| Spot Klines (1W/1D/4H/1H/15m) | `1W:100 1D:500 bars · 11-19 00:00 UTC | 4H:500 1H:720 15m:240` | `All Tabs` | `OK` |
| Perp Klines / Est. Excluded | `1D:101 · 1H:720 · 15m:240 (Excl=399)` | `1,4,11,15,19` | `OK` |
| Closed 4H Anchor (Tab 19/20) | `2026-11-19 00:00:00 UTC` | `18,19,20` | `OK` |
| B1/B2 Rec & Companion Liq | `Rec:PASS (0s delta) | Liq:N/A` | `8,13,17` | `OK` |
| Telemetry History Archive (SQLite) | `23 bars logged (Last: 2026-11-19 00:00:00 UTC)` | `DB Archive` | `OK` |

## 7. RECENT CLOSED-4H SNAPSHOT TRAJECTORY (SQLITE ARCHIVE)
| Closed 4H Bar (UTC) | Spot ($) | 24H Spot/Perp CVD | Cross-Exch Perp OI & Funding | Funding 8H% / 90D Pct | MVRV Ratio |
|---|---|---|---|---|---|
| `2026-11-19 00:00:00 UTC` | `$62,748.01` | `24h:+164.5/-2742.3 BTC` | `165,337 BTC ($10.39B) · F:+0.0065% [BN+BYB+OKX 3/3]` | `+0.0094% (+10.3%/yr) · 90D Pct:4.8%` | `1.212 [CoinMetrics 2026-11-17]` |
| `2026-11-18 20:00:00 UTC` | `$62,732.21` | `24h:+502.1/+1518.8 BTC` | `165,771 BTC ($10.39B) · F:+0.0064% [BN+BYB+OKX 3/3]` | `+0.0077% (+8.4%/yr) · 90D Pct:57.0%` | `1.212 [CoinMetrics 2026-11-17]` |
| `2026-11-18 12:00:00 UTC` | `$63,913.72` | `24h:+864.9/+729.5 BTC` | `161,131 BTC ($10.29B) · F:+0.0027% [BN+BYB+OKX 3/3]` | `+0.0026% (+2.9%/yr) · 90D Pct:19.3%` | `1.212 [CoinMetrics 2026-11-17]` |
| `2026-11-18 08:00:00 UTC` | `$64,571.19` | `24h:+1253.0/-1116.7 BTC` | `158,240 BTC ($10.21B) · F:+0.0020% [BN+BYB+OKX 3/3]` | `+0.0006% (+0.7%/yr) · 90D Pct:19.3%` | `1.212 [CoinMetrics 2026-11-17]` |
| `2026-11-18 04:00:00 UTC` | `$64,644.90` | `24h:+2890.4/+126.7 BTC` | `158,764 BTC ($10.25B) · F:+0.0043% [BN+BYB+OKX 3/3]` | `+0.0054% (+5.9%/yr) · 90D Pct:3.7%` | `1.212 [CoinMetrics 2026-11-17]` |
| `2026-11-18 00:00:00 UTC` | `$64,200.35` | `24h:+2603.9/-43.2 BTC` | `158,990 BTC ($10.22B) · F:+0.0036% [BN+BYB+OKX 3/3]` | `+0.0073% (+8.0%/yr) · 90D Pct:3.7%` | `1.212 [CoinMetrics 2026-11-17]` |

### 7A. 500-BAR MARKET STRUCTURE & HISTORICAL S/R ZONES (`1D / 4H / 1H`)
| TF (Bars) | Swing Structure | Last Swing Pivots | Latest BOS | Resistance Zones (Above Spot) | Support Zones (Below Spot) |
|---|---|---|---|---|---|
| `1D (499)` | `DOWNTREND (LH/LL)` | `SH:$81,196.01 (11-04) · SL:$79,800.00 (10-15)` | `BOS Down < $79,800.00 (10-29)` | `$65,182.19 (5x), $67,124.15 (2x), $70,983.00 (1x)` | `$62,440.17 (3x), $60,000.00 (1x), $59,130.91 (1x)` |
| `4H (499)` | `DOWNTREND (LH/LL)` | `SH:$65,696.16 (11-16 12:00) · SL:$63,336.00 (11-17 12:00)` | `BOS Down < $63,336.00 (11-18 12:00)` | `$63,620.51 (2x), $65,696.16 (1x), $72,727.27 (1x)` | `$62,006.00 (1x)` |
| `1H (500)` | `DOWNTREND (LH/LL)` | `SH:$64,952.92 (11-18 07:00) · SL:$62,279.36 (11-18 16:00)` | `BOS Down < $62,279.36 (11-18 22:00)` | `$63,620.51 (2x), $64,257.65 (1x), $65,429.09 (7x)` | `$62,142.68 (2x)` |

### 7B. RECENT CLOSED KLINES — OHLCV PRICE ACTION (`1D`×7, `4H`×12, `1H`×12)
**1D Closed Candles (Last 7 of 499 available, Newest First):**
| Open Time (UTC) | Open | High | Low | Close | Chg% | Vol (BTC) |
|---|---|---|---|---|---|---|
| `2026-11-18` | `$64,947.36` | `$65,002.00` | `$62,062.97` | `$63,068.22` | `-2.89%` | `18,700` |
| `2026-11-17` | `$64,882.88` | `$65,447.00` | `$63,336.00` | `$64,947.35` | `+0.10%` | `28,317` |
| `2026-11-16` | `$65,351.05` | `$65,696.16` | `$63,905.01` | `$64,882.87` | `-0.72%` | `21,929` |
| `2026-11-15` | `$64,150.01` | `$66,132.01` | `$62,006.00` | `$65,351.05` | `+1.87%` | `29,231` |
| `2026-11-14` | `$68,314.01` | `$68,446.21` | `$63,320.00` | `$64,150.00` | `-6.10%` | `32,675` |
| `2026-11-13` | `$71,460.00` | `$71,514.01` | `$67,568.00` | `$68,314.00` | `-4.40%` | `29,649` |
| `2026-11-12` | `$74,015.20` | `$74,217.49` | `$71,113.06` | `$71,460.00` | `-3.45%` | `15,228` |

**4H Closed Candles (Last 12 of 499 available, Newest First):**
| Open Time (UTC) | Open | High | Low | Close | Chg% | Vol (BTC) |
|---|---|---|---|---|---|---|
| `2026-11-18 20:00` | `$62,747.22` | `$63,300.00` | `$62,062.97` | `$63,068.22` | `+0.51%` | `3,102` |
| `2026-11-18 16:00` | `$63,122.53` | `$63,537.89` | `$62,279.36` | `$62,747.22` | `-0.59%` | `4,704` |
| `2026-11-18 12:00` | `$64,231.53` | `$64,392.01` | `$63,000.07` | `$63,122.53` | `-1.73%` | `4,472` |
| `2026-11-18 08:00` | `$64,884.00` | `$64,884.00` | `$64,120.00` | `$64,231.52` | `-1.01%` | `1,904` |
| `2026-11-18 04:00` | `$64,457.68` | `$64,952.92` | `$64,312.72` | `$64,884.01` | `+0.66%` | `2,059` |
| `2026-11-18 00:00` | `$64,947.36` | `$65,002.00` | `$64,136.00` | `$64,457.96` | `-0.75%` | `2,459` |
| `2026-11-17 20:00` | `$63,753.74` | `$65,268.00` | `$63,685.96` | `$64,947.35` | `+1.87%` | `3,925` |
| `2026-11-17 16:00` | `$64,115.08` | `$64,483.33` | `$63,455.71` | `$63,753.75` | `-0.56%` | `3,718` |
| `2026-11-17 12:00` | `$64,995.54` | `$65,447.00` | `$63,336.00` | `$64,115.09` | `-1.35%` | `6,076` |
| `2026-11-17 08:00` | `$64,740.13` | `$65,004.98` | `$64,079.83` | `$64,995.54` | `+0.39%` | `6,538` |
| `2026-11-17 04:00` | `$65,056.53` | `$65,094.60` | `$64,303.64` | `$64,740.14` | `-0.49%` | `4,742` |
| `2026-11-17 00:00` | `$64,882.88` | `$65,200.00` | `$64,385.99` | `$65,056.52` | `+0.27%` | `3,319` |

**1H Closed Candles (Last 12 of 719 available, Newest First):**
| Open Time (UTC) | Open | High | Low | Close | Chg% | Vol (BTC) |
|---|---|---|---|---|---|---|
| `2026-11-18 23:00` | `$62,254.71` | `$63,300.00` | `$62,248.83` | `$63,068.22` | `+1.31%` | `801` |
| `2026-11-18 22:00` | `$62,352.29` | `$62,658.82` | `$62,062.97` | `$62,254.71` | `-0.16%` | `797` |
| `2026-11-18 21:00` | `$62,628.00` | `$62,664.01` | `$62,313.00` | `$62,352.30` | `-0.44%` | `648` |
| `2026-11-18 20:00` | `$62,747.22` | `$62,801.48` | `$62,454.00` | `$62,628.01` | `-0.19%` | `855` |
| `2026-11-18 19:00` | `$63,170.24` | `$63,170.24` | `$62,570.45` | `$62,747.22` | `-0.67%` | `699` |
| `2026-11-18 18:00` | `$63,109.73` | `$63,286.22` | `$63,082.36` | `$63,168.31` | `+0.09%` | `426` |
| `2026-11-18 17:00` | `$62,760.01` | `$63,537.89` | `$62,600.00` | `$63,109.73` | `+0.56%` | `1,202` |
| `2026-11-18 16:00` | `$63,122.53` | `$63,128.61` | `$62,279.36` | `$62,760.01` | `-0.57%` | `2,377` |
| `2026-11-18 15:00` | `$63,674.61` | `$63,889.63` | `$63,000.07` | `$63,122.53` | `-0.87%` | `1,473` |
| `2026-11-18 14:00` | `$63,944.13` | `$64,090.73` | `$63,085.00` | `$63,675.47` | `-0.42%` | `1,897` |
| `2026-11-18 13:00` | `$64,088.45` | `$64,195.50` | `$63,922.66` | `$63,944.13` | `-0.23%` | `555` |
| `2026-11-18 12:00` | `$64,231.53` | `$64,392.01` | `$63,969.00` | `$64,088.45` | `-0.22%` | `546` |

### 7C. MODELED LIQUIDATION LADDER (`10x-100x`) & USD MACRO CALENDAR
**6-Tier Modeled Liquidation Ladder:**
| Tier | Side | Level ($) | Dist% | Est Pool ($M) |
|---|---|---|---|---|
| `10x Shorts` | `UPPER` | `$66,919.42` | `+6.65%` | `$102.3M` |
| `25x Shorts` | `UPPER` | `$65,930.46` | `+5.07%` | `$136.4M` |
| `50-100x Shorts` | `UPPER` | `$65,277.68` | `+4.03%` | `$193.8M` |
| `100x Longs` | `LOWER` | `$61,618.55` | `-1.80%` | `$350.0M` |
| `25x Longs` | `LOWER` | `$61,002.36` | `-2.78%` | `$315.5M` |
| `10x Longs` | `LOWER` | `$60,087.32` | `-4.24%` | `$220.9M` |

**Upcoming USD High-Impact Macro Events (`-60m` to `+7d`):**
| Event | Time (UTC) | Countdown | Forecast | Previous |
|---|---|---|---|---|
| `NONE (next 7d)` | `-` | `CLEAR` | `-` | `-` |

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
