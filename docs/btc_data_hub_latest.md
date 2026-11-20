# TAB [D: DATA HUB] | CONSOLIDATED DATA-ONLY TELEMETRY REPORT
**Retrieval Time (UTC):** `2026-11-20 02:08:44 UTC`  |  **Retrieval Time (SGT):** `2026-11-20 10:08:44 SGT (UTC+8)`
**Spot Price (BTCUSDT):** `$61,416.72`  |  **Coverage:** `OK=65/71 | UNAVAILABLE=4 | STALE=1 (Genuine=0, Expected_Headless_WS_Offline=1) | PROXY/STATIC=1`
**24H Range:** `$61,295.00 - $64,080.80`  |  **Returns (24H / 7D / 30D):** `-1.88% / -10.10% / -26.97%`
**Archive (SQLite):** `28 closed-4H snapshots (Last: 2026-11-20 00:00:00 UTC)`

## 0. BIDIRECTIONAL REGIME ROUTER (GATE 0 — DUAL-INVENTORY SPOT WORKSTATION)
| Router Field | Value | Rule / Threshold |
|---|---|---|
| Latest Closed 1D Candle Close | `$61,986.73 (1D bar 2026-11-19 · closed 2026-11-20 00:00 UTC)` | `Same closed Binance Spot 1D series only (live candle excluded)` |
| Current 1D SMA 200 | `$72,693.73` | `200-bar SMA of same closed Binance Spot 1D series` |
| Distance vs 1D SMA 200 | `-14.73% (-$10,707.00)` | `(Closed 1D Close - 1D SMA 200) / 1D SMA 200` |
| 1D SMA 200 Position | `BELOW` | `BELOW if Closed 1D Close < 1D SMA 200 else ABOVE` |
| Closed 4H Market Structure (`7A`) | `DOWNTREND (LH/LL)` | `UPTREND / DOWNTREND / MIXED (500 closed 4H bars)` |
| 4H Downside BOS Status (`7A`) | `YES (BOS Down < $62,062.97 (11-19 20:00))` | `YES if latest closed 4H BOS is BOS Down else NO` |
| Upcoming Macro Event Caution (`7C`) | `CLEAR (>24h / NONE)` | `CAUTION (<24h USD high-impact event) else CLEAR` |
| Timestamp & Candle Closed Status | `2026-11-20 02:08:44 UTC | 2026-11-20 10:08:44 SGT (UTC+8) · Closed-Candle Inputs Only` | `Strict closed-bar verification gate` |

**BIDIRECTIONAL REGIME ROUTER STATUS:**
- **Active Route:** `MACRO_DOWNTREND_DISTRIBUTION`
- **Primary Active Rail:** `RAIL A — BTC -> USDT CONVERSION (DEFENSIVE / SELL RALLIES)`
- **Active BTC Inventory (`Rail A: BTC -> USDT`):** `ACTIVE (RAIL A) — CONVERT INTO OVERHEAD RESISTANCE`
- **Active USDT Inventory (`Rail B: USDT -> BTC`):** `RESTRICTED (RAIL B) — HOLD PENDING VALIDATED SWEEP & RECLAIM`
- **Condition A (`1D Close < 1D SMA 200`):** `YES`  |  **Condition B (`4H Downside Structure / BOS`):** `YES`

## 1. PRICE, TREND & MARKET STRUCTURE
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| Binance Spot / Perp ($) | `$61,416.72 / $61,393.00` | `All Tabs` | `OK` |
| Coinbase Spot ($) | `$61,328.79` | `1,11,15,17` | `OK` |
| 1D SMA 200 / Slope | `$72,693.73 (-0.46%)` | `0,2,3,11,15,18` | `OK` |
| 1D SMA 50 / EMA 50 | `$78,236.29 / $74,637.86` | `0,2,4,15,18,20` | `OK` |
| 1D EMA 21 / 1W EMA 50 | `$70,000.37 / $77,655.71` | `3,18` | `OK` |
| 4H EMA 50 / EMA 200 | `$66,403.10 / $73,784.16` | `7,13,18,20` | `OK` |
| Grok EMA 9/21 & 1H SMA200 | `9:$62,044.12 · 21:$62,571.35 · 1H:$66,295.30` | `5,15` | `OK` |
| Daily / Weekly VWAP (Z) | `D:$61,983.93 (-1.94σ) | W:$65,119.28` | `4,11,15` | `OK` |
| RSI(14) 1D / 4H & 4H ROC12 | `1D:19.7 · 4H:32.1 · ROC:-4.56%` | `3,7,20` | `OK` |
| ADX(14) 1D/4H & ATR(14) 1D/4H/1H | `ADX 1D:43.9 4H:48.7 | ATR:$2,691.33/$1,088.09/$643.76` | `0,1,2,8,13,18,20` | `OK` |
| 4H ATR(14)% Pctile & RelVol(20) | `ATR%:1.79% (76th pct/120b) · RelVol:1.37x` | `0,1,2,20` | `OK` |
| Macro 30D VAH / POC / VAL | `BIMODAL (Peaks: $80,472.44 & $64,737.10 — single VA UNAVAILABLE)` | `1,3,6,11,19` | `UNAVAILABLE` |
| Structure (L20/H20, PW, Asia) | `4H:$62,006.00-$81,196.01 | PW:$62,006.00-$75,599.22 | Asia:$61,295.00-$62,639.52` | `0,8,11,19` | `OK` |

## 2. ORDER FLOW, FOOTPRINT & LIQUIDITY
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| Spot/Perp CVD (15m / 1h) | `15m:-26.6/-16.9 | 1h:-240.5/-2261.4 BTC` | `1,8,15` | `OK` |
| Spot/Perp CVD (4h / 24h) | `4h:-468.5/-2443.8 | 24h:-1333.8/-4120.5 BTC` | `0,1,15,16,17` | `OK` |
| Spot CVD Slopes (7D / 14D) | `7D:-3,615.7 BTC | 14D:-492.3 BTC` | `17` | `OK` |
| Session / UTC-Day CVD | `Sess S:+0.0 P:+0.0 | Day S:-287.1 P:-2190.4` | `REST 15m` | `OK` |
| 24H Z-Scores (z_S / z_F / D) | `z_S:-0.93 · z_F:-0.29 · D:-0.65` | `1,19` | `OK` |
| 15m Footprint Delta / Stack | `Δ:-26.6 BTC (Prev:-164.5) · Stacks:0` | `1,11` | `OK` |
| Coinbase Premium ($ / % / Z) | `-87.9$ (-0.143%, Z=-0.95)` | `1,11,15` | `OK` |
| Cross-Exch 24H Spot Vol (BN/CB) | `BN:20,168 · CB:13,073 · Tot:33,241 BTC` | `1,11,Macro` | `OK` |
| L2 Depth ±1%/±2%, OBI & Spread | `1%:2.67x · 2%:2.87x · Spr:0.0016bps · OBI:+45.5%` | `16,Macro` | `OK` |
| Tactical 7D / Session 24H VP | `7D:$65,699.14/$64,946.30/$62,386.63 | 24H:$63,964.73/$63,779.01/$62,153.96` | `1,11` | `OK` |
| 30D VA Pos% & Dist to VAL | `BIMODAL — DATA UNAVAILABLE` | `1` | `UNAVAILABLE` |
| SLSP Support / Resistance | `Sup:$61,065.63 | Res:$62,373.29` | `13` | `OK` |

## 3. DERIVATIVES, OPTIONS & LIQUIDATIONS
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| BN Open Interest (BTC / USD) | `97,795 BTC ($6.01B)` | `0,1,4,15,17` | `OK` |
| Cross-Exch Perp OI & Funding | `167,823 BTC ($10.30B) · F:-0.0006% [BN+BYB+OKX 3/3]` | `Macro,15` | `OK` |
| Hyperliquid Perp OI & Funding | `38,278 BTC ($2.35B) · F:+0.0015% [HL DEX]` | `Macro,15` | `OK` |
| OI Δ% (15m/1h/4h/24h) & Quad | `+0.25%/+1.87%/+4.79%/+4.43% | AGGRESSIVE_SHORT_BUILD (Price Down/Flat / OI Up)` | `1,4,8,11,12,15,17` | `OK` |
| Funding 8H% / Ann% / 90D Pct | `-0.0022% (-2.4%/yr) · 90D Pct:3.0%` | `0,4,9,11,15,16,19,20` | `OK` |
| Perp Basis ($ / Ann %) | `-23.7$ (-0.039% | Carry:-2.90%/yr)` | `1,4` | `OK` |
| 5m Taker L/S & Top/Glb Acct | `5m:0.736 (Δ:-72.3) | Top:2.03(67L) · Glb:3.40` | `1,2,15,16` | `OK` |
| Options OI & Put/Call (Deribit) | `P/C:0.790 · TotOI:411,178 BTC` | `Macro,19` | `OK` |
| Options IV Term & Skew (Deribit) | `F:46.5% · B:43.4% · 25dSk:+7.5%` | `Macro,6,19` | `OK` |
| Vol: DVOL, RV20, GK & BBW% | `DVOL:48.0 · RV20:46.9% · GK:52.8% · BBW:90% · Sk20:-0.32` | `0,4,6,16,19` | `OK` |
| Upper / Lower Liq Magnet | `Up:$76,334.44 | Dn:$60,311.22` | `0,2,13,17` | `OK` |
| Magnet Ratios & LSCE | `Imm:1.81x · Ladder:1.79x · Pull:0.55x · LSCE:UNTESTED` | `13,17` | `OK` |
| Modeled Liq Ladder (10x-100x) | `Up[10x:$66,020.89($101M) / 25x:$65,045.21($135M) / 50-100x:$64,401.20($194M)] | Dn[100x:$60,311.22($350M) / 25x:$59,708.11($312M) / 10x:$58,812.49($218M)] [Modeled]` | `17` | `OK` |
| Liquidations (1H / 24H) & Flush | `DATA UNAVAILABLE` | `0,8,12,13` | `UNAVAILABLE` |

## 4. ON-CHAIN, ETF & STABLECOIN FLOWS
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| MVRV Ratio (On-Chain / Proxy) | `1.176 [CoinMetrics 2026-11-18]` | `Macro,16` | `OK` |
| On-Chain SOPR / aSOPR | `DATA UNAVAILABLE` | `16` | `UNAVAILABLE` |
| Exchange Netflow 24H (CM) | `Net:-5,306.9 BTC (-$333.8M) | In:27,469 Out:32,776` | `Macro,16` | `OK` |
| BTC Exchange Reserves (CM) | `2,711,760 BTC (2026-11-18)` | `Macro,16` | `OK` |
| Stablecoins USDT+USDC Supply | `$243.90B (USDT:$175.06B · USDC:$68.83B)` | `Macro` | `OK` |
| Stablecoin Net Issuance (7D/30D) | `7D:-1.06B · 30D:-11.06B` | `Macro` | `OK` |
| US Spot ETF Flow (Farside 1D/3D) | `1D:-$41.2M | 3D:-$587.6M | 5D:-$765.1M` | `2,13` | `OK` |
| US ETF Tape Proxy (IBIT+FBTC) | `1DVol:$2.26B · 5D:-$11.70B [PROXY]` | `Macro,2,13` | `PROXY` |
| Power-Law Fair & ATH DD% | `$149,878.94 (-59.0%) | DD:-51.3%` | `3` | `OK` |
| MTF MACD (1D / 1H Status) | `1D=negative_slope (Macro Whipsaw Veto) | 1H=negative_slope / NEUTRAL` | `13,16,18` | `OK` |

## 5. MACRO, CREDIT & US LIQUIDITY
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| US SOFR Rate & Vol (NY Fed) | `3.90% (Vol:$3,134B)` | `Macro` | `OK` |
| Fed ON RRP Balance (NY Fed) | `$0.41B` | `Macro` | `OK` |
| Credit Spread HYG/LQD & 5D% | `0.7431 (-0.13% 5D)` | `Macro,3` | `OK` |
| DXY / US 10Y (^TNX) | `103.94 (RISING (+0.53 over 5d)) | 10Y:5.05%` | `3,13` | `OK` |
| TIPS Real (DFII10) / BEI | `Real:+2.88% | BEI:2.17%` | `3,13` | `OK` |
| S&P 500 / Nasdaq (1D%) | `SPX:7,176 (-2.02%) | NDX:23,879` | `3,13` | `OK` |
| VIX / Brent Crude (BZ=F) | `VIX:28.44 | Brent:$89.78` | `3,13` | `OK` |
| BTC-SPX Corr (20D / 60D) | `20D:+0.66 | 60D:+0.68` | `3` | `OK` |
| Fear & Greed / BTC Dom% | `F&G:12 (Extreme Fear) | Dom:57.90%` | `3,13` | `OK` |
| USD Macro Calendar (High) | `NONE (next 7d)` | `Macro` | `OK` |
| Manual Context Overrides | `Legacy_200D_Veto_Override: IGNORED (Tab1_Flag=False) · Filter=NONE_SIGNIFICANT` | `2,13` | `OK` |

## 6. QUANT FEATURES, FEED HEALTH & ARCHIVE
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| Rough Path Lévy (A_SP / MM) | `4H A_SP:-1.2586 | MM PriceFlow:-0.0126 · Rough:0.320` | `5,19` | `OK` |
| Hurst / Kalman Vel / FracDiff | `H:0.582 · KVel:-50.20 · d:0.15` | `5,6` | `OK` |
| Hilbert Cycle / TD9 / TellTale | `Cyc:72.0b · TD(1H/4H):1/3 · RV(15m/5m):0.70/N/A` | `5,9,13` | `OK` |
| VCR 72H & TSFM Disp% | `VCR:6.92 | Disp:1.28%` | `6` | `OK` |
| Open FVGs & Sweep FSM | `FVGs:7 | FSM:None (0/12)` | `1,8` | `OK` |
| WebSocket Feeds & Warmup | `Spot:SYNC (no tick) | Perp:SYNC (no tick) | CB:SYNC (12s ago) | Warm:YES` | `Live Feeds` | `STALE` |
| Spot Klines (1W/1D/4H/1H/15m) | `1W:100 1D:500 bars · 11-20 00:00 UTC | 4H:500 1H:720 15m:240` | `All Tabs` | `OK` |
| Perp Klines / Est. Excluded | `1D:101 · 1H:720 · 15m:240 (Excl=399)` | `1,4,11,15,19` | `OK` |
| Closed 4H Anchor (Tab 19/20) | `2026-11-20 00:00:00 UTC` | `18,19,20` | `OK` |
| B1/B2 Rec & Companion Liq | `Rec:PASS (0s delta) | Liq:N/A` | `8,13,17` | `OK` |
| Telemetry History Archive (SQLite) | `28 bars logged (Last: 2026-11-20 00:00:00 UTC)` | `DB Archive` | `OK` |

## 7. RECENT CLOSED-4H SNAPSHOT TRAJECTORY (SQLITE ARCHIVE)
| Closed 4H Bar (UTC) | Spot ($) | 24H Spot/Perp CVD | Cross-Exch Perp OI & Funding | Funding 8H% / 90D Pct | MVRV Ratio |
|---|---|---|---|---|---|
| `2026-11-20 00:00:00 UTC` | `$62,018.40` | `24h:-1185.0/-2692.8 BTC` | `165,941 BTC ($10.28B) · F:+0.0022% [BN+BYB+OKX 3/3]` | `+0.0020% (+2.2%/yr) · 90D Pct:3.0%` | `1.176 [CoinMetrics 2026-11-18]` |
| `2026-11-19 20:00:00 UTC` | `$62,298.01` | `24h:-290.5/-5701.5 BTC` | `165,648 BTC ($10.29B) · F:+0.0083% [BN+BYB+OKX 3/3]` | `+0.0100% (+10.9%/yr) · 90D Pct:2.6%` | `1.176 [CoinMetrics 2026-11-18]` |
| `2026-11-19 12:00:00 UTC` | `$63,884.76` | `24h:-63.3/-5535.8 BTC` | `163,955 BTC ($10.47B) · F:+0.0007% [BN+BYB+OKX 3/3]` | `+0.0009% (+1.0%/yr) · 90D Pct:7.0%` | `1.176 [CoinMetrics 2026-11-18]` |
| `2026-11-19 08:00:00 UTC` | `$63,815.54` | `24h:+109.8/-2860.3 BTC` | `163,185 BTC ($10.41B) · F:+0.0042% [BN+BYB+OKX 3/3]` | `+0.0057% (+6.2%/yr) · 90D Pct:7.0%` | `1.176 [CoinMetrics 2026-11-18]` |
| `2026-11-19 04:00:00 UTC` | `$63,640.43` | `24h:+188.8/-2307.2 BTC` | `164,592 BTC ($10.45B) · F:+0.0024% [BN+BYB+OKX 3/3]` | `+0.0032% (+3.5%/yr) · 90D Pct:4.8%` | `1.176 [CoinMetrics 2026-11-18]` |
| `2026-11-19 00:00:00 UTC` | `$62,748.01` | `24h:+164.5/-2742.3 BTC` | `165,337 BTC ($10.39B) · F:+0.0065% [BN+BYB+OKX 3/3]` | `+0.0094% (+10.3%/yr) · 90D Pct:4.8%` | `1.212 [CoinMetrics 2026-11-17]` |

### 7A. 500-BAR MARKET STRUCTURE & HISTORICAL S/R ZONES (`1D / 4H / 1H`)
| TF (Bars) | Swing Structure | Last Swing Pivots | Latest BOS | Resistance Zones (Above Spot) | Support Zones (Below Spot) |
|---|---|---|---|---|---|
| `1D (499)` | `DOWNTREND (LH/LL)` | `SH:$81,196.01 (11-04) · SL:$79,800.00 (10-15)` | `BOS Down < $79,800.00 (10-29)` | `$62,440.17 (3x), $65,182.19 (5x), $67,124.15 (2x)` | `$60,000.00 (1x), $59,130.91 (1x), $57,957.60 (2x)` |
| `4H (499)` | `DOWNTREND (LH/LL)` | `SH:$65,696.16 (11-16 12:00) · SL:$62,062.97 (11-18 20:00)` | `BOS Down < $62,062.97 (11-19 20:00)` | `$62,034.49 (2x), $63,620.51 (2x), $65,696.16 (1x)` | `None below in lookback` |
| `1H (500)` | `DOWNTREND (LH/LL)` | `SH:$64,080.80 (11-19 11:00) · SL:$62,062.97 (11-18 22:00)` | `BOS Down < $62,062.97 (11-19 21:00)` | `$62,116.11 (3x), $63,894.86 (4x), $65,429.09 (7x)` | `None below in lookback` |

### 7B. RECENT CLOSED KLINES — OHLCV PRICE ACTION (`1D`×7, `4H`×12, `1H`×12)
**1D Closed Candles (Last 7 of 499 available, Newest First):**
| Open Time (UTC) | Open | High | Low | Close | Chg% | Vol (BTC) |
|---|---|---|---|---|---|---|
| `2026-11-19` | `$63,068.21` | `$64,080.80` | `$61,428.26` | `$61,986.73` | `-1.71%` | `19,880` |
| `2026-11-18` | `$64,947.36` | `$65,002.00` | `$62,062.97` | `$63,068.22` | `-2.89%` | `18,700` |
| `2026-11-17` | `$64,882.88` | `$65,447.00` | `$63,336.00` | `$64,947.35` | `+0.10%` | `28,317` |
| `2026-11-16` | `$65,351.05` | `$65,696.16` | `$63,905.01` | `$64,882.87` | `-0.72%` | `21,929` |
| `2026-11-15` | `$64,150.01` | `$66,132.01` | `$62,006.00` | `$65,351.05` | `+1.87%` | `29,231` |
| `2026-11-14` | `$68,314.01` | `$68,446.21` | `$63,320.00` | `$64,150.00` | `-6.10%` | `32,675` |
| `2026-11-13` | `$71,460.00` | `$71,514.01` | `$67,568.00` | `$68,314.00` | `-4.40%` | `29,649` |

**4H Closed Candles (Last 12 of 499 available, Newest First):**
| Open Time (UTC) | Open | High | Low | Close | Chg% | Vol (BTC) |
|---|---|---|---|---|---|---|
| `2026-11-19 20:00` | `$62,372.01` | `$62,467.25` | `$61,428.26` | `$61,986.73` | `-0.62%` | `5,049` |
| `2026-11-19 16:00` | `$63,103.30` | `$63,408.62` | `$62,227.80` | `$62,372.01` | `-1.16%` | `4,149` |
| `2026-11-19 12:00` | `$63,947.59` | `$64,080.00` | `$62,780.07` | `$63,103.30` | `-1.32%` | `3,555` |
| `2026-11-19 08:00` | `$63,737.62` | `$64,080.80` | `$63,565.52` | `$63,947.59` | `+0.33%` | `2,108` |
| `2026-11-19 04:00` | `$63,205.65` | `$63,879.00` | `$63,204.00` | `$63,737.63` | `+0.84%` | `2,129` |
| `2026-11-19 00:00` | `$63,068.21` | `$63,299.99` | `$62,388.72` | `$63,205.64` | `+0.22%` | `2,889` |
| `2026-11-18 20:00` | `$62,747.22` | `$63,300.00` | `$62,062.97` | `$63,068.22` | `+0.51%` | `3,102` |
| `2026-11-18 16:00` | `$63,122.53` | `$63,537.89` | `$62,279.36` | `$62,747.22` | `-0.59%` | `4,704` |
| `2026-11-18 12:00` | `$64,231.53` | `$64,392.01` | `$63,000.07` | `$63,122.53` | `-1.73%` | `4,472` |
| `2026-11-18 08:00` | `$64,884.00` | `$64,884.00` | `$64,120.00` | `$64,231.52` | `-1.01%` | `1,904` |
| `2026-11-18 04:00` | `$64,457.68` | `$64,952.92` | `$64,312.72` | `$64,884.01` | `+0.66%` | `2,059` |
| `2026-11-18 00:00` | `$64,947.36` | `$65,002.00` | `$64,136.00` | `$64,457.96` | `-0.75%` | `2,459` |

**1H Closed Candles (Last 12 of 719 available, Newest First):**
| Open Time (UTC) | Open | High | Low | Close | Chg% | Vol (BTC) |
|---|---|---|---|---|---|---|
| `2026-11-20 01:00` | `$62,150.00` | `$62,639.52` | `$61,295.00` | `$61,579.09` | `-0.92%` | `1,474` |
| `2026-11-20 00:00` | `$61,986.73` | `$62,255.12` | `$61,950.00` | `$62,149.99` | `+0.26%` | `737` |
| `2026-11-19 23:00` | `$62,173.55` | `$62,238.00` | `$61,772.45` | `$61,986.73` | `-0.30%` | `844` |
| `2026-11-19 22:00` | `$61,542.01` | `$62,344.90` | `$61,526.00` | `$62,173.55` | `+1.03%` | `786` |
| `2026-11-19 21:00` | `$62,128.58` | `$62,170.01` | `$61,428.26` | `$61,542.01` | `-0.94%` | `1,543` |
| `2026-11-19 20:00` | `$62,372.01` | `$62,467.25` | `$61,760.25` | `$62,128.57` | `-0.39%` | `1,876` |
| `2026-11-19 19:00` | `$62,885.68` | `$62,917.69` | `$62,300.00` | `$62,372.01` | `-0.82%` | `680` |
| `2026-11-19 18:00` | `$62,748.95` | `$63,302.87` | `$62,662.19` | `$62,885.68` | `+0.22%` | `824` |
| `2026-11-19 17:00` | `$62,778.07` | `$63,408.62` | `$62,227.80` | `$62,748.96` | `-0.05%` | `1,475` |
| `2026-11-19 16:00` | `$63,103.30` | `$63,366.01` | `$62,606.57` | `$62,778.08` | `-0.52%` | `1,169` |
| `2026-11-19 15:00` | `$63,558.00` | `$63,916.01` | `$62,780.07` | `$63,103.30` | `-0.72%` | `1,213` |
| `2026-11-19 14:00` | `$64,038.01` | `$64,060.01` | `$63,462.00` | `$63,558.01` | `-0.75%` | `819` |

### 7C. MODELED LIQUIDATION LADDER (`10x-100x`) & USD MACRO CALENDAR
**6-Tier Modeled Liquidation Ladder:**
| Tier | Side | Level ($) | Dist% | Est Pool ($M) |
|---|---|---|---|---|
| `10x Shorts` | `UPPER` | `$66,020.89` | `+7.50%` | `$101.2M` |
| `25x Shorts` | `UPPER` | `$65,045.21` | `+5.91%` | `$134.9M` |
| `50-100x Shorts` | `UPPER` | `$64,401.20` | `+4.86%` | `$193.8M` |
| `100x Longs` | `LOWER` | `$60,311.22` | `-1.80%` | `$350.0M` |
| `25x Longs` | `LOWER` | `$59,708.11` | `-2.78%` | `$311.9M` |
| `10x Longs` | `LOWER` | `$58,812.49` | `-4.24%` | `$218.3M` |

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
