# TAB [D: DATA HUB] | CONSOLIDATED DATA-ONLY TELEMETRY REPORT
**Retrieval Time (UTC):** `2026-11-26 23:35:35 UTC`  |  **Retrieval Time (SGT):** `2026-11-27 07:35:35 SGT (UTC+8)`
**Spot Price (BTCUSDT):** `$60,445.82`  |  **Coverage:** `OK=67/71 | UNAVAILABLE=2 | STALE=1 (Genuine=0, Expected_Headless_WS_Offline=1) | PROXY/STATIC=1`
**24H Range:** `$59,915.00 - $61,622.38`  |  **Returns (24H / 7D / 30D):** `-0.02% / -2.49% / -25.29%`
**Archive (SQLite):** `66 closed-4H snapshots (Last: 2026-11-26 20:00:00 UTC)`

## 0. BIDIRECTIONAL REGIME ROUTER (GATE 0 — DUAL-INVENTORY SPOT WORKSTATION)
| Router Field | Value | Rule / Threshold |
|---|---|---|
| Latest Closed 1D Candle Close | `$60,458.01 (1D bar 2026-11-25 · closed 2026-11-26 00:00 UTC)` | `Same closed Binance Spot 1D series only (live candle excluded)` |
| Current 1D SMA 200 | `$72,088.27` | `200-bar SMA of same closed Binance Spot 1D series` |
| Distance vs 1D SMA 200 | `-16.13% (-$11,630.26)` | `(Closed 1D Close - 1D SMA 200) / 1D SMA 200` |
| 1D SMA 200 Position | `BELOW` | `BELOW if Closed 1D Close < 1D SMA 200 else ABOVE` |
| Closed 4H Market Structure (`7A`) | `MIXED (LH/HL)` | `UPTREND / DOWNTREND / MIXED (500 closed 4H bars)` |
| 4H Downside BOS Status (`7A`) | `YES (BOS Down < $62,062.97 (11-19 20:00))` | `YES if latest closed 4H BOS is BOS Down else NO` |
| Upcoming Macro Event Caution (`7C`) | `CLEAR (>24h / NONE)` | `CAUTION (<24h USD high-impact event) else CLEAR` |
| Timestamp & Candle Closed Status | `2026-11-26 23:35:35 UTC | 2026-11-27 07:35:35 SGT (UTC+8) · Closed-Candle Inputs Only` | `Strict closed-bar verification gate` |

**BIDIRECTIONAL REGIME ROUTER STATUS:**
- **Active Route:** `MACRO_DOWNTREND_DISTRIBUTION`
- **Primary Active Rail:** `RAIL A — BTC -> USDT CONVERSION (DEFENSIVE / SELL RALLIES)`
- **Active BTC Inventory (`Rail A: BTC -> USDT`):** `ACTIVE (RAIL A) — CONVERT INTO OVERHEAD RESISTANCE`
- **Active USDT Inventory (`Rail B: USDT -> BTC`):** `RESTRICTED (RAIL B) — HOLD PENDING VALIDATED SWEEP & RECLAIM`
- **Condition A (`1D Close < 1D SMA 200`):** `YES`  |  **Condition B (`4H Downside Structure / BOS`):** `YES`

## 1. PRICE, TREND & MARKET STRUCTURE
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| Binance Spot / Perp ($) | `$60,445.82 / $60,420.00` | `All Tabs` | `OK` |
| Coinbase Spot ($) | `$60,360.79` | `1,11,15,17` | `OK` |
| 1D SMA 200 / Slope | `$72,088.27 (-0.69%)` | `0,2,3,11,15,18` | `OK` |
| 1D SMA 50 / EMA 50 | `$75,236.31 / $71,560.40` | `0,2,4,15,18,20` | `OK` |
| 1D EMA 21 / 1W EMA 50 | `$65,762.11 / $77,712.30` | `3,18` | `OK` |
| 4H EMA 50 / EMA 200 | `$61,409.31 / $69,199.51` | `7,13,18,20` | `OK` |
| Grok EMA 9/21 & 1H SMA200 | `9:$60,619.40 · 21:$60,548.44 · 1H:$60,713.46` | `5,15` | `OK` |
| Daily / Weekly VWAP (Z) | `D:$60,730.03 (-1.43σ) | W:$59,875.52` | `4,11,15` | `OK` |
| RSI(14) 1D / 4H & 4H ROC12 | `1D:27.2 · 4H:52.6 · ROC:+1.74%` | `3,7,20` | `OK` |
| ADX(14) 1D/4H & ATR(14) 1D/4H/1H | `ADX 1D:49.8 4H:16.2 | ATR:$3,064.80/$1,098.10/$378.61` | `0,1,2,8,13,18,20` | `OK` |
| 4H ATR(14)% Pctile & RelVol(20) | `ATR%:1.89% (52th pct/120b) · RelVol:0.51x` | `0,1,2,20` | `OK` |
| Macro 30D VAH / POC / VAL | `$74,925.24 / $64,859.86 / $55,912.86` | `1,3,6,11,19` | `OK` |
| Structure (L20/H20, PW, Asia) | `4H:$55,130.00-$76,378.00 | PW:$55,130.00-$65,696.16 | Asia:$60,377.37-$61,622.38` | `0,8,11,19` | `OK` |

## 2. ORDER FLOW, FOOTPRINT & LIQUIDITY
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| Spot/Perp CVD (15m / 1h) | `15m:+2.5/+75.4 | 1h:-34.1/+42.5 BTC` | `1,8,15` | `OK` |
| Spot/Perp CVD (4h / 24h) | `4h:+5.0/+389.8 | 24h:+963.0/+933.7 BTC` | `0,1,15,16,17` | `OK` |
| Spot CVD Slopes (7D / 14D) | `7D:-7,238.0 BTC | 14D:-9,949.1 BTC` | `17` | `OK` |
| Session / UTC-Day CVD | `Sess S:+0.0 P:+0.0 | Day S:+963.0 P:+947.5` | `REST 15m` | `OK` |
| 24H Z-Scores (z_S / z_F / D) | `z_S:+0.46 · z_F:+0.79 · D:-0.32` | `1,19` | `OK` |
| 15m Footprint Delta / Stack | `Δ:+2.5 BTC (Prev:+0.0) · Stacks:0` | `1,11` | `OK` |
| Coinbase Premium ($ / % / Z) | `-85.0$ (-0.141%, Z=-1.16)` | `1,11,15` | `OK` |
| Cross-Exch 24H Spot Vol (BN/CB) | `BN:16,324 · CB:5,800 · Tot:22,124 BTC` | `1,11,Macro` | `OK` |
| L2 Depth ±1%/±2%, OBI & Spread | `1%:0.97x · 2%:0.88x · Spr:0.0017bps · OBI:-1.3%` | `16,Macro` | `OK` |
| Tactical 7D / Session 24H VP | `7D:$61,563.83/$60,774.40/$58,248.24 | 24H:$60,953.66/$60,839.83/$60,526.81` | `1,11` | `OK` |
| 30D VA Pos% & Dist to VAL | `23.8% | +8.11% (+11.97 ATR)` | `1` | `OK` |
| SLSP Support / Resistance | `Sup:$60,000.00 | Res:$61,065.63` | `13` | `OK` |

## 3. DERIVATIVES, OPTIONS & LIQUIDATIONS
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| BN Open Interest (BTC / USD) | `98,433 BTC ($5.95B)` | `0,1,4,15,17` | `OK` |
| Cross-Exch Perp OI & Funding | `165,342 BTC ($9.99B) · F:+0.0062% [BN+BYB+OKX 3/3]` | `Macro,15` | `OK` |
| Hyperliquid Perp OI & Funding | `34,519 BTC ($2.09B) · F:-0.0022% [HL DEX]` | `Macro,15` | `OK` |
| OI Δ% (15m/1h/4h/24h) & Quad | `+0.05%/+0.02%/-0.59%/+0.80% | NEUTRAL_CHURN` | `1,4,8,11,12,15,17` | `OK` |
| Funding 8H% / Ann% / 90D Pct | `+0.0097% (+10.6%/yr) · 90D Pct:43.7%` | `0,4,9,11,15,16,19,20` | `OK` |
| Perp Basis ($ / Ann %) | `-25.8$ (-0.043% | Carry:+10.10%/yr)` | `1,4` | `OK` |
| 5m Taker L/S & Top/Glb Acct | `5m:4.615 (Δ:+58.0) | Top:1.80(64L) · Glb:2.44` | `1,2,15,16` | `OK` |
| Options OI & Put/Call (Deribit) | `P/C:0.799 · TotOI:443,903 BTC` | `Macro,19` | `OK` |
| Options IV Term & Skew (Deribit) | `F:50.9% · B:46.4% · 25dSk:+6.7%` | `Macro,6,19` | `OK` |
| Vol: DVOL, RV20, GK & BBW% | `DVOL:52.5 · RV20:44.5% · GK:59.0% · BBW:94% · Sk20:-0.58` | `0,4,6,16,19` | `OK` |
| Upper / Lower Liq Magnet | `Up:$76,334.44 | Dn:$59,357.80` | `0,2,13,17` | `OK` |
| Magnet Ratios & LSCE | `Imm:1.81x · Ladder:1.38x · Pull:0.55x · LSCE:UNTESTED` | `13,17` | `OK` |
| Modeled Liq Ladder (10x-100x) | `Up[10x:$66,490.40($83M) / 25x:$62,863.65($111M) / 50-100x:$61,050.28($194M)] | Dn[100x:$59,841.36($350M) / 25x:$58,027.99($338M) / 10x:$54,401.24($236M)] [Modeled] (L/S:global_account_ls_ratio)` | `17` | `OK` |
| Liquidations (1H / 24H) & Flush | `DATA UNAVAILABLE` | `0,8,12,13` | `UNAVAILABLE` |

## 4. ON-CHAIN, ETF & STABLECOIN FLOWS
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| MVRV Ratio (On-Chain / Proxy) | `1.136 [CoinMetrics 2026-11-25]` | `Macro,16` | `OK` |
| On-Chain SOPR / aSOPR | `DATA UNAVAILABLE` | `16` | `UNAVAILABLE` |
| Exchange Netflow 24H (CM) | `Net:+2,340.2 BTC (+$141.0M) | In:29,540 Out:27,200` | `Macro,16` | `OK` |
| BTC Exchange Reserves (CM) | `2,712,502 BTC (2026-11-25)` | `Macro,16` | `OK` |
| Stablecoins USDT+USDC Supply | `$242.76B (USDT:$173.55B · USDC:$69.21B)` | `Macro` | `OK` |
| Stablecoin Net Issuance (7D/30D) | `7D:-0.80B · 30D:-10.35B` | `Macro` | `OK` |
| US Spot ETF Flow (Farside 1D/3D) | `1D:-$453.0M | 3D:-$1.25B | 5D:-$2.51B` | `2,13` | `OK` |
| US ETF Tape Proxy (IBIT+FBTC) | `1DVol:$2.71B · 5D:-$3.30B [PROXY]` | `Macro,2,13` | `PROXY` |
| Power-Law Fair & ATH DD% | `$150,779.87 (-59.9%) | DD:-52.1%` | `3` | `OK` |
| MTF MACD (1D / 1H Status) | `1D=negative_slope (Macro Whipsaw Veto) | 1H=negative_slope / NEUTRAL` | `13,16,18` | `OK` |

## 5. MACRO, CREDIT & US LIQUIDITY
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| US SOFR Rate & Vol (NY Fed) | `3.94% (Vol:$3,158B)` | `Macro` | `OK` |
| Fed ON RRP Balance (NY Fed) | `$0.30B` | `Macro` | `OK` |
| Credit Spread HYG/LQD & 5D% | `0.7337 (-1.26% 5D)` | `Macro,3` | `OK` |
| DXY / US 10Y (^TNX) | `103.78 (NEUTRAL / FLAT (-0.12 over 5d)) | 10Y:4.85%` | `3,13` | `OK` |
| TIPS Real (DFII10) / BEI | `Real:+2.73% | BEI:2.12%` | `3,13` | `OK` |
| S&P 500 / Nasdaq (1D%) | `SPX:7,183 (-0.25%) | NDX:23,586` | `3,13` | `OK` |
| VIX / Brent Crude (BZ=F) | `VIX:26.80 | Brent:$91.59` | `3,13` | `OK` |
| BTC-SPX Corr (20D / 60D) | `20D:+0.66 | 60D:+0.78` | `3` | `OK` |
| Fear & Greed / BTC Dom% | `F&G:11 (Extreme Fear) | Dom:57.90%` | `3,13` | `OK` |
| USD Macro Calendar (High) | `NONE (next 7d)` | `Macro` | `OK` |
| Manual Context Overrides | `Legacy_200D_Veto_Override: IGNORED (Tab1_Flag=True) · Filter=NONE_SIGNIFICANT` | `2,13` | `OK` |

## 6. QUANT FEATURES, FEED HEALTH & ARCHIVE
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| Rough Path Lévy (A_SP / MM) | `4H A_SP:-3.0430 | MM PriceFlow:-0.3842 · Rough:2.130` | `5,19` | `OK` |
| Hurst / Kalman Vel / FracDiff | `H:0.630 · KVel:-6.90 · d:0.20` | `5,6` | `OK` |
| Hilbert Cycle / TD9 / TellTale | `Cyc:10.0b · TD(1H/4H):1/2 · RV(15m/5m):0.16/N/A` | `5,9,13` | `OK` |
| VCR 72H & TSFM Disp% | `VCR:9.08 | Disp:1.28%` | `6` | `OK` |
| Open FVGs & Sweep FSM | `FVGs:4 | FSM:None (0/12)` | `1,8` | `OK` |
| WebSocket Feeds & Warmup | `Spot:SYNC (no tick) | Perp:SYNC (no tick) | CB:SYNC (11s ago) | Warm:YES` | `Live Feeds` | `STALE` |
| Spot Klines (1W/1D/4H/1H/15m) | `1W:100 1D:500 bars · 11-26 00:00 UTC | 4H:500 1H:720 15m:240` | `All Tabs` | `OK` |
| Perp Klines / Est. Excluded | `1D:100 · 1H:720 · 15m:240 (Excl=400)` | `1,4,11,15,19` | `OK` |
| Closed 4H Anchor (Tab 19/20) | `2026-11-26 20:00:00 UTC` | `18,19,20` | `OK` |
| B1/B2 Rec & Companion Liq | `Rec:PASS (0s delta) | Liq:N/A` | `8,13,17` | `OK` |
| Telemetry History Archive (SQLite) | `66 bars logged (Last: 2026-11-26 20:00:00 UTC)` | `DB Archive` | `OK` |

## 7. RECENT CLOSED-4H SNAPSHOT TRAJECTORY (SQLITE ARCHIVE)
| Closed 4H Bar (UTC) | Spot ($) | 24H Spot/Perp CVD | Cross-Exch Perp OI & Funding | Funding 8H% / 90D Pct | MVRV Ratio |
|---|---|---|---|---|---|
| `2026-11-26 20:00:00 UTC` | `$60,445.82` | `24h:+963.0/+933.7 BTC` | `165,342 BTC ($9.99B) · F:+0.0062% [BN+BYB+OKX 3/3]` | `+0.0097% (+10.6%/yr) · 90D Pct:43.7%` | `1.136 [CoinMetrics 2026-11-25]` |
| `2026-11-26 16:00:00 UTC` | `$60,460.57` | `24h:+612.0/+2492.4 BTC` | `165,394 BTC ($10.01B) · F:+0.0053% [BN+BYB+OKX 3/3]` | `+0.0048% (+5.3%/yr) · 90D Pct:43.7%` | `1.136 [CoinMetrics 2026-11-25]` |
| `2026-11-26 12:00:00 UTC` | `$60,850.00` | `24h:+1029.2/+4219.6 BTC` | `164,510 BTC ($10.00B) · F:+0.0065% [BN+BYB+OKX 3/3]` | `+0.0059% (+6.5%/yr) · 90D Pct:65.6%` | `1.136 [CoinMetrics 2026-11-25]` |
| `2026-11-26 08:00:00 UTC` | `$60,668.01` | `24h:+1051.2/+2614.5 BTC` | `163,989 BTC ($9.93B) · F:+0.0086% [BN+BYB+OKX 3/3]` | `+0.0085% (+9.3%/yr) · 90D Pct:65.6%` | `1.136 [CoinMetrics 2026-11-25]` |
| `2026-11-26 04:00:00 UTC` | `$61,036.21` | `24h:+858.7/+1909.7 BTC` | `163,487 BTC ($9.97B) · F:+0.0091% [BN+BYB+OKX 3/3]` | `+0.0089% (+9.8%/yr) · 90D Pct:84.4%` | `1.136 [CoinMetrics 2026-11-25]` |
| `2026-11-26 00:00:00 UTC` | `$60,788.01` | `24h:+349.0/+2225.7 BTC` | `162,810 BTC ($9.89B) · F:+0.0085% [BN+BYB+OKX 3/3]` | `+0.0074% (+8.1%/yr) · 90D Pct:84.4%` | `1.126 [CoinMetrics 2026-11-24]` |

### 7A. 500-BAR MARKET STRUCTURE & HISTORICAL S/R ZONES (`1D / 4H / 1H`)
| TF (Bars) | Swing Structure | Last Swing Pivots | Latest BOS | Resistance Zones (Above Spot) | Support Zones (Below Spot) |
|---|---|---|---|---|---|
| `1D (499)` | `DOWNTREND (LH/LL)` | `SH:$81,196.01 (11-04) · SL:$79,800.00 (10-15)` | `BOS Down < $79,800.00 (10-29)` | `$62,440.17 (3x), $65,182.19 (5x), $67,124.15 (2x)` | `$60,000.00 (1x), $59,130.91 (1x), $57,957.60 (2x)` |
| `4H (499)` | `MIXED (LH/HL)` | `SH:$64,603.12 (11-23 12:00) · SL:$57,300.38 (11-25 12:00)` | `BOS Down < $62,062.97 (11-19 20:00)` | `$62,034.49 (2x), $63,620.51 (2x), $64,603.12 (1x)` | `$57,300.38 (1x), $55,130.00 (1x)` |
| `1H (500)` | `MIXED (HH/LL)` | `SH:$61,622.38 (11-26 00:00) · SL:$59,915.00 (11-26 15:00)` | `BOS Down < $59,260.00 (11-25 02:00)` | `$60,595.74 (8x), $61,879.46 (9x), $62,639.52 (1x)` | `$59,218.67 (4x), $57,539.36 (2x), $55,130.00 (1x)` |

### 7B. RECENT CLOSED KLINES — OHLCV PRICE ACTION (`1D`×7, `4H`×12, `1H`×12)
**1D Closed Candles (Last 7 of 499 available, Newest First):**
| Open Time (UTC) | Open | High | Low | Close | Chg% | Vol (BTC) |
|---|---|---|---|---|---|---|
| `2026-11-25` | `$59,832.00` | `$60,568.01` | `$57,300.38` | `$60,458.01` | `+1.05%` | `26,999` |
| `2026-11-24` | `$61,270.92` | `$61,682.01` | `$59,260.00` | `$59,832.00` | `-2.35%` | `19,707` |
| `2026-11-23` | `$61,271.09` | `$64,603.12` | `$60,386.00` | `$61,270.93` | `-0.00%` | `27,494` |
| `2026-11-22` | `$60,215.78` | `$61,669.99` | `$58,768.51` | `$61,271.08` | `+1.75%` | `20,137` |
| `2026-11-21` | `$58,951.51` | `$60,996.00` | `$55,130.00` | `$60,215.77` | `+2.14%` | `48,558` |
| `2026-11-20` | `$61,986.73` | `$62,639.52` | `$57,778.35` | `$58,951.51` | `-4.90%` | `38,126` |
| `2026-11-19` | `$63,068.21` | `$64,080.80` | `$61,428.26` | `$61,986.73` | `-1.71%` | `19,880` |

**4H Closed Candles (Last 12 of 499 available, Newest First):**
| Open Time (UTC) | Open | High | Low | Close | Chg% | Vol (BTC) |
|---|---|---|---|---|---|---|
| `2026-11-26 16:00` | `$60,618.80` | `$60,860.35` | `$60,348.04` | `$60,718.59` | `+0.16%` | `2,053` |
| `2026-11-26 12:00` | `$60,714.00` | `$60,989.07` | `$59,915.00` | `$60,618.79` | `-0.16%` | `2,664` |
| `2026-11-26 08:00` | `$60,521.78` | `$61,070.01` | `$60,466.00` | `$60,714.01` | `+0.32%` | `2,748` |
| `2026-11-26 04:00` | `$60,779.98` | `$61,126.33` | `$60,380.01` | `$60,521.78` | `-0.42%` | `3,866` |
| `2026-11-26 00:00` | `$60,458.00` | `$61,622.38` | `$60,377.37` | `$60,779.98` | `+0.53%` | `4,079` |
| `2026-11-25 20:00` | `$59,879.23` | `$60,568.01` | `$59,795.23` | `$60,458.01` | `+0.97%` | `2,755` |
| `2026-11-25 16:00` | `$58,344.01` | `$60,405.44` | `$58,103.21` | `$59,879.23` | `+2.63%` | `5,682` |
| `2026-11-25 12:00` | `$58,640.34` | `$58,922.16` | `$57,300.38` | `$58,344.01` | `-0.51%` | `6,295` |
| `2026-11-25 08:00` | `$58,738.33` | `$59,489.63` | `$58,456.25` | `$58,640.34` | `-0.17%` | `4,899` |
| `2026-11-25 04:00` | `$59,421.85` | `$59,421.85` | `$58,633.12` | `$58,738.33` | `-1.15%` | `3,259` |
| `2026-11-25 00:00` | `$59,832.00` | `$59,835.38` | `$58,952.48` | `$59,421.85` | `-0.69%` | `4,109` |
| `2026-11-24 20:00` | `$59,679.19` | `$60,106.00` | `$59,481.33` | `$59,832.00` | `+0.26%` | `1,631` |

**1H Closed Candles (Last 12 of 719 available, Newest First):**
| Open Time (UTC) | Open | High | Low | Close | Chg% | Vol (BTC) |
|---|---|---|---|---|---|---|
| `2026-11-26 22:00` | `$60,820.76` | `$60,820.76` | `$60,462.60` | `$60,548.01` | `-0.45%` | `351` |
| `2026-11-26 21:00` | `$60,766.01` | `$61,006.00` | `$60,762.91` | `$60,820.77` | `+0.09%` | `235` |
| `2026-11-26 20:00` | `$60,718.59` | `$60,828.66` | `$60,675.75` | `$60,766.00` | `+0.08%` | `202` |
| `2026-11-26 19:00` | `$60,480.00` | `$60,764.37` | `$60,468.63` | `$60,718.59` | `+0.39%` | `262` |
| `2026-11-26 18:00` | `$60,530.00` | `$60,768.00` | `$60,398.00` | `$60,480.01` | `-0.08%` | `478` |
| `2026-11-26 17:00` | `$60,522.91` | `$60,657.39` | `$60,401.54` | `$60,529.99` | `+0.01%` | `766` |
| `2026-11-26 16:00` | `$60,618.80` | `$60,860.35` | `$60,348.04` | `$60,522.91` | `-0.16%` | `547` |
| `2026-11-26 15:00` | `$60,734.88` | `$60,734.88` | `$59,915.00` | `$60,618.79` | `-0.19%` | `1,057` |
| `2026-11-26 14:00` | `$60,876.82` | `$60,967.79` | `$60,702.34` | `$60,734.89` | `-0.23%` | `529` |
| `2026-11-26 13:00` | `$60,825.37` | `$60,956.01` | `$60,786.00` | `$60,876.81` | `+0.08%` | `476` |
| `2026-11-26 12:00` | `$60,714.00` | `$60,989.07` | `$60,590.51` | `$60,825.37` | `+0.18%` | `602` |
| `2026-11-26 11:00` | `$60,518.01` | `$60,790.76` | `$60,490.00` | `$60,714.01` | `+0.32%` | `363` |

### 7C. MODELED LIQUIDATION LADDER (`10x-100x`) & USD MACRO CALENDAR
**6-Tier Modeled Liquidation Ladder (`global_account_ls_ratio`):**
| Tier | Side | Level ($) | Dist% | Est Pool ($M) |
|---|---|---|---|---|
| `10x Shorts` | `UPPER` | `$66,490.40` | `+10.00%` | `$83.0M` |
| `25x Shorts` | `UPPER` | `$62,863.65` | `+4.00%` | `$110.7M` |
| `50-100x Shorts` | `UPPER` | `$61,050.28` | `+1.00%` | `$193.8M` |
| `100x Longs` | `LOWER` | `$59,841.36` | `-1.00%` | `$350.0M` |
| `25x Longs` | `LOWER` | `$58,027.99` | `-4.00%` | `$337.6M` |
| `10x Longs` | `LOWER` | `$54,401.24` | `-10.00%` | `$236.3M` |

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
