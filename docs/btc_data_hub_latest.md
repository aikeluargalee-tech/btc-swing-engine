# TAB [D: DATA HUB] | CONSOLIDATED DATA-ONLY TELEMETRY REPORT
**Retrieval Time (UTC):** `2026-11-28 11:30:30 UTC`  |  **Retrieval Time (SGT):** `2026-11-28 19:30:30 SGT (UTC+8)`
**Spot Price (BTCUSDT):** `$59,250.59`  |  **Coverage:** `OK=67/71 | UNAVAILABLE=2 | STALE=1 (Genuine=0, Expected_Headless_WS_Offline=1) | PROXY/STATIC=1`
**24H Range:** `$58,792.37 - $61,707.41`  |  **Returns (24H / 7D / 30D):** `-3.91% / -1.60% / -24.03%`
**Archive (SQLite):** `74 closed-4H snapshots (Last: 2026-11-28 08:00:00 UTC)`

## 0. BIDIRECTIONAL REGIME ROUTER (GATE 0 — DUAL-INVENTORY SPOT WORKSTATION)
| Router Field | Value | Rule / Threshold |
|---|---|---|
| Latest Closed 1D Candle Close | `$59,923.10 (1D bar 2026-11-27 · closed 2026-11-28 00:00 UTC)` | `Same closed Binance Spot 1D series only (live candle excluded)` |
| Current 1D SMA 200 | `$71,871.00` | `200-bar SMA of same closed Binance Spot 1D series` |
| Distance vs 1D SMA 200 | `-16.62% (-$11,947.90)` | `(Closed 1D Close - 1D SMA 200) / 1D SMA 200` |
| 1D SMA 200 Position | `BELOW` | `BELOW if Closed 1D Close < 1D SMA 200 else ABOVE` |
| Closed 4H Market Structure (`7A`) | `UPTREND (HH/HL)` | `UPTREND / DOWNTREND / MIXED (500 closed 4H bars)` |
| 4H Downside BOS Status (`7A`) | `NO (BOS Up > $61,622.38 (11-27 04:00))` | `YES if latest closed 4H BOS is BOS Down else NO` |
| Upcoming Macro Event Caution (`7C`) | `CLEAR (>24h / NONE)` | `CAUTION (<24h USD high-impact event) else CLEAR` |
| Timestamp & Candle Closed Status | `2026-11-28 11:30:30 UTC | 2026-11-28 19:30:30 SGT (UTC+8) · Closed-Candle Inputs Only` | `Strict closed-bar verification gate` |

**BIDIRECTIONAL REGIME ROUTER STATUS:**
- **Active Route:** `TRANSITIONAL_RANGE`
- **Primary Active Rail:** `TWO_WAY_RANGE_HARVEST (BOUNDARY SWINGS)`
- **Active BTC Inventory (`Rail A: BTC -> USDT`):** `TWO-WAY HARVEST — CONVERT AT 7A RESISTANCE & UPPER 7C`
- **Active USDT Inventory (`Rail B: USDT -> BTC`):** `TWO-WAY HARVEST — DEPLOY AT 7A SUPPORT & LOWER 7C SWEEPS`
- **Condition A (`1D Close < 1D SMA 200`):** `YES`  |  **Condition B (`4H Downside Structure / BOS`):** `NO`

## 1. PRICE, TREND & MARKET STRUCTURE
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| Binance Spot / Perp ($) | `$59,250.59 / $59,229.70` | `All Tabs` | `OK` |
| Coinbase Spot ($) | `$59,193.89` | `1,11,15,17` | `OK` |
| 1D SMA 200 / Slope | `$71,871.00 (-0.71%)` | `0,2,3,11,15,18` | `OK` |
| 1D SMA 50 / EMA 50 | `$74,344.79 / $70,643.95` | `0,2,4,15,18,20` | `OK` |
| 1D EMA 21 / 1W EMA 50 | `$64,697.46 / $77,712.30` | `3,18` | `OK` |
| 4H EMA 50 / EMA 200 | `$61,138.97 / $68,458.13` | `7,13,18,20` | `OK` |
| Grok EMA 9/21 & 1H SMA200 | `9:$59,593.84 · 21:$59,900.64 · 1H:$60,268.30` | `5,15` | `OK` |
| Daily / Weekly VWAP (Z) | `D:$59,725.12 (-1.91σ) | W:$60,484.99` | `4,11,15` | `OK` |
| RSI(14) 1D / 4H & 4H ROC12 | `1D:25.5 · 4H:44.1 · ROC:-1.14%` | `3,7,20` | `OK` |
| ADX(14) 1D/4H & ATR(14) 1D/4H/1H | `ADX 1D:50.1 4H:17.1 | ATR:$3,002.75/$1,023.86/$395.99` | `0,1,2,8,13,18,20` | `OK` |
| 4H ATR(14)% Pctile & RelVol(20) | `ATR%:1.79% (38th pct/120b) · RelVol:0.66x` | `0,1,2,20` | `OK` |
| Macro 30D VAH / POC / VAL | `$74,254.21 / $64,859.86 / $55,912.86` | `1,3,6,11,19` | `OK` |
| Structure (L20/H20, PW, Asia) | `4H:$55,130.00-$76,200.00 | PW:$55,130.00-$65,696.16 | Asia:$59,188.34-$60,266.01` | `0,8,11,19` | `OK` |

## 2. ORDER FLOW, FOOTPRINT & LIQUIDITY
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| Spot/Perp CVD (15m / 1h) | `15m:-0.1/+0.2 | 1h:-38.0/+404.3 BTC` | `1,8,15` | `OK` |
| Spot/Perp CVD (4h / 24h) | `4h:-136.8/-510.7 | 24h:-552.6/-5918.0 BTC` | `0,1,15,16,17` | `OK` |
| Spot CVD Slopes (7D / 14D) | `7D:-1,421.7 BTC | 14D:-7,834.6 BTC` | `17` | `OK` |
| Session / UTC-Day CVD | `Sess S:+0.0 P:+0.0 | Day S:-100.3 P:-1226.5` | `REST 15m` | `OK` |
| 24H Z-Scores (z_S / z_F / D) | `z_S:-0.30 · z_F:-0.93 · D:+0.63` | `1,19` | `OK` |
| 15m Footprint Delta / Stack | `Δ:-0.1 BTC (Prev:+0.0) · Stacks:0` | `1,11` | `OK` |
| Coinbase Premium ($ / % / Z) | `-56.7$ (-0.096%, Z=+1.75)` | `1,11,15` | `OK` |
| Cross-Exch 24H Spot Vol (BN/CB) | `BN:16,390 · CB:13,891 · Tot:30,281 BTC` | `1,11,Macro` | `OK` |
| L2 Depth ±1%/±2%, OBI & Spread | `1%:1.74x · 2%:2.02x · Spr:0.0017bps · OBI:+26.9%` | `16,Macro` | `OK` |
| Tactical 7D / Session 24H VP | `7D:$61,712.45/$60,008.48/$59,460.77 | 24H:$60,177.01/$59,885.51/$59,448.25` | `1,11` | `OK` |
| 30D VA Pos% & Dist to VAL | `18.2% | +5.97% (+8.43 ATR)` | `1` | `OK` |
| SLSP Support / Resistance | `Sup:$58,961.64 | Res:$60,000.00` | `13` | `OK` |

## 3. DERIVATIVES, OPTIONS & LIQUIDATIONS
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| BN Open Interest (BTC / USD) | `99,404 BTC ($5.88B)` | `0,1,4,15,17` | `OK` |
| Cross-Exch Perp OI & Funding | `166,529 BTC ($9.85B) · F:+0.0057% [BN+BYB+OKX 3/3]` | `Macro,15` | `OK` |
| Hyperliquid Perp OI & Funding | `35,960 BTC ($2.13B) · F:-0.0165% [HL DEX]` | `Macro,15` | `OK` |
| OI Δ% (15m/1h/4h/24h) & Quad | `+0.00%/+0.02%/+1.09%/+0.78% | NEUTRAL_CHURN` | `1,4,8,11,12,15,17` | `OK` |
| Funding 8H% / Ann% / 90D Pct | `+0.0075% (+8.3%/yr) · 90D Pct:36.7%` | `0,4,9,11,15,16,19,20` | `OK` |
| Perp Basis ($ / Ann %) | `-20.9$ (-0.035% | Carry:+7.80%/yr)` | `1,4` | `OK` |
| 5m Taker L/S & Top/Glb Acct | `5m:1.929 (Δ:+41.2) | Top:2.03(67L) · Glb:2.91` | `1,2,15,16` | `OK` |
| Options OI & Put/Call (Deribit) | `P/C:0.806 · TotOI:344,874 BTC` | `Macro,19` | `OK` |
| Options IV Term & Skew (Deribit) | `F:52.6% · B:47.0% · 25dSk:+7.6%` | `Macro,6,19` | `OK` |
| Vol: DVOL, RV20, GK & BBW% | `DVOL:53.2 · RV20:44.3% · GK:61.3% · BBW:88% · Sk20:-0.54` | `0,4,6,16,19` | `OK` |
| Upper / Lower Liq Magnet | `Up:$76,334.44 | Dn:$58,184.08` | `0,2,13,17` | `OK` |
| Magnet Ratios & LSCE | `Imm:1.81x · Ladder:1.38x · Pull:0.55x · LSCE:UNTESTED` | `13,17` | `OK` |
| Modeled Liq Ladder (10x-100x) | `Up[10x:$65,175.65($72M) / 25x:$61,620.61($96M) / 50-100x:$59,843.10($194M)] | Dn[100x:$58,658.08($350M) / 25x:$56,880.57($351M) / 10x:$53,325.53($246M)] [Modeled] (L/S:global_account_ls_ratio)` | `17` | `OK` |
| Liquidations (1H / 24H) & Flush | `DATA UNAVAILABLE` | `0,8,12,13` | `UNAVAILABLE` |

## 4. ON-CHAIN, ETF & STABLECOIN FLOWS
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| MVRV Ratio (On-Chain / Proxy) | `1.129 [CoinMetrics 2026-11-27]` | `Macro,16` | `OK` |
| On-Chain SOPR / aSOPR | `DATA UNAVAILABLE` | `16` | `UNAVAILABLE` |
| Exchange Netflow 24H (CM) | `Net:-1,223.7 BTC (-$73.2M) | In:24,134 Out:25,358` | `Macro,16` | `OK` |
| BTC Exchange Reserves (CM) | `2,709,426 BTC (2026-11-27)` | `Macro,16` | `OK` |
| Stablecoins USDT+USDC Supply | `$242.89B (USDT:$173.52B · USDC:$69.38B)` | `Macro` | `OK` |
| Stablecoin Net Issuance (7D/30D) | `7D:-0.42B · 30D:-9.34B` | `Macro` | `OK` |
| US Spot ETF Flow (Farside 1D/3D) | `1D:-$389.0M | 3D:-$1.07B | 5D:-$2.31B` | `2,13` | `OK` |
| US ETF Tape Proxy (IBIT+FBTC) | `1DVol:$1.73B · 5D:-$2.21B [PROXY]` | `Macro,2,13` | `PROXY` |
| Power-Law Fair & ATH DD% | `$150,976.03 (-60.8%) | DD:-53.0%` | `3` | `OK` |
| MTF MACD (1D / 1H Status) | `1D=positive_slope (1D Trend Active) | 1H=negative_slope / NEUTRAL` | `13,16,18` | `OK` |

## 5. MACRO, CREDIT & US LIQUIDITY
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| US SOFR Rate & Vol (NY Fed) | `3.95% (Vol:$3,145B)` | `Macro` | `OK` |
| Fed ON RRP Balance (NY Fed) | `$0.35B` | `Macro` | `OK` |
| Credit Spread HYG/LQD & 5D% | `0.7366 (-0.78% 5D)` | `Macro,3` | `OK` |
| DXY / US 10Y (^TNX) | `104.01 (NEUTRAL / FLAT (+0.11 over 5d)) | 10Y:4.94%` | `3,13` | `OK` |
| TIPS Real (DFII10) / BEI | `Real:+2.79% | BEI:2.15%` | `3,13` | `OK` |
| S&P 500 / Nasdaq (1D%) | `SPX:7,297 (+1.60%) | NDX:24,130` | `3,13` | `OK` |
| VIX / Brent Crude (BZ=F) | `VIX:23.81 | Brent:$90.84` | `3,13` | `OK` |
| BTC-SPX Corr (20D / 60D) | `20D:+0.64 | 60D:+0.79` | `3` | `OK` |
| Fear & Greed / BTC Dom% | `F&G:10 (Extreme Fear) | Dom:58.40%` | `3,13` | `OK` |
| USD Macro Calendar (High) | `NONE (next 7d)` | `Macro` | `OK` |
| Manual Context Overrides | `Legacy_200D_Veto_Override: IGNORED (Tab1_Flag=True) · Filter=NONE_SIGNIFICANT` | `2,13` | `OK` |

## 6. QUANT FEATURES, FEED HEALTH & ARCHIVE
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| Rough Path Lévy (A_SP / MM) | `4H A_SP:+0.0472 | MM PriceFlow:-0.6386 · Rough:2.160` | `5,19` | `OK` |
| Hurst / Kalman Vel / FracDiff | `H:0.553 · KVel:-0.70 · d:0.10` | `5,6` | `OK` |
| Hilbert Cycle / TD9 / TellTale | `Cyc:36.0b · TD(1H/4H):7/6 · RV(15m/5m):0.00/N/A` | `5,9,13` | `OK` |
| VCR 72H & TSFM Disp% | `VCR:7.57 | Disp:1.28%` | `6` | `OK` |
| Open FVGs & Sweep FSM | `FVGs:6 | FSM:None (0/12)` | `1,8` | `OK` |
| WebSocket Feeds & Warmup | `Spot:SYNC (no tick) | Perp:SYNC (no tick) | CB:SYNC (12s ago) | Warm:YES` | `Live Feeds` | `STALE` |
| Spot Klines (1W/1D/4H/1H/15m) | `1W:100 1D:500 bars · 11-28 00:00 UTC | 4H:500 1H:720 15m:240` | `All Tabs` | `OK` |
| Perp Klines / Est. Excluded | `1D:101 · 1H:720 · 15m:240 (Excl=399)` | `1,4,11,15,19` | `OK` |
| Closed 4H Anchor (Tab 19/20) | `2026-11-28 08:00:00 UTC` | `18,19,20` | `OK` |
| B1/B2 Rec & Companion Liq | `Rec:PASS (0s delta) | Liq:N/A` | `8,13,17` | `OK` |
| Telemetry History Archive (SQLite) | `74 bars logged (Last: 2026-11-28 08:00:00 UTC)` | `DB Archive` | `OK` |

## 7. RECENT CLOSED-4H SNAPSHOT TRAJECTORY (SQLITE ARCHIVE)
| Closed 4H Bar (UTC) | Spot ($) | 24H Spot/Perp CVD | Cross-Exch Perp OI & Funding | Funding 8H% / 90D Pct | MVRV Ratio |
|---|---|---|---|---|---|
| `2026-11-28 08:00:00 UTC` | `$59,539.17` | `24h:-526.6/-3818.2 BTC` | `165,619 BTC ($9.86B) · F:+0.0057% [BN+BYB+OKX 3/3]` | `+0.0065% (+7.2%/yr) · 90D Pct:36.7%` | `1.129 [CoinMetrics 2026-11-27]` |
| `2026-11-28 04:00:00 UTC` | `$59,631.27` | `24h:-660.8/-5117.5 BTC` | `165,654 BTC ($9.85B) · F:+0.0056% [BN+BYB+OKX 3/3]` | `+0.0073% (+8.0%/yr) · 90D Pct:54.1%` | `1.129 [CoinMetrics 2026-11-27]` |
| `2026-11-28 00:00:00 UTC` | `$60,161.29` | `24h:-97.7/-1485.1 BTC` | `163,604 BTC ($9.82B) · F:+0.0067% [BN+BYB+OKX 3/3]` | `+0.0085% (+9.3%/yr) · 90D Pct:54.1%` | `1.139 [CoinMetrics 2026-11-26]` |
| `2026-11-27 16:00:00 UTC` | `$60,054.01` | `24h:+444.4/-1205.8 BTC` | `164,467 BTC ($9.87B) · F:+0.0004% [BN+BYB+OKX 3/3]` | `+0.0001% (+0.1%/yr) · 90D Pct:13.0%` | `1.139 [CoinMetrics 2026-11-26]` |
| `2026-11-27 12:00:00 UTC` | `$61,580.99` | `24h:+326.6/+3576.8 BTC` | `164,021 BTC ($10.10B) · F:+0.0015% [BN+BYB+OKX 3/3]` | `+0.0022% (+2.4%/yr) · 90D Pct:50.0%` | `1.139 [CoinMetrics 2026-11-26]` |
| `2026-11-27 08:00:00 UTC` | `$61,689.61` | `24h:+428.4/+3043.5 BTC` | `163,972 BTC ($10.11B) · F:+0.0009% [BN+BYB+OKX 3/3]` | `+0.0018% (+2.0%/yr) · 90D Pct:0.0%` | `1.139 [CoinMetrics 2026-11-26]` |

### 7A. 500-BAR MARKET STRUCTURE & HISTORICAL S/R ZONES (`1D / 4H / 1H`)
| TF (Bars) | Swing Structure | Last Swing Pivots | Latest BOS | Resistance Zones (Above Spot) | Support Zones (Below Spot) |
|---|---|---|---|---|---|
| `1D (499)` | `DOWNTREND (LH/LL)` | `SH:$81,196.01 (11-04) · SL:$55,130.00 (11-21)` | `BOS Down < $79,800.00 (10-29)` | `$60,000.00 (1x), $62,440.17 (3x), $65,182.19 (5x)` | `$59,130.91 (1x), $57,957.60 (2x), $55,130.00 (1x)` |
| `4H (499)` | `UPTREND (HH/HL)` | `SH:$62,248.91 (11-27 08:00) · SL:$57,300.38 (11-25 12:00)` | `BOS Up > $61,622.38 (11-27 04:00)` | `$61,985.07 (4x), $63,620.51 (2x), $64,603.12 (1x)` | `$57,300.38 (1x), $55,130.00 (1x)` |
| `1H (500)` | `DOWNTREND (LH/LL)` | `SH:$60,266.01 (11-28 02:00) · SL:$58,792.37 (11-27 15:00)` | `BOS Down < $60,390.65 (11-27 14:00)` | `$60,542.26 (10x), $61,916.41 (10x), $62,639.52 (1x)` | `$59,133.41 (5x), $57,539.36 (2x), $55,130.00 (1x)` |

### 7B. RECENT CLOSED KLINES — OHLCV PRICE ACTION (`1D`×7, `4H`×12, `1H`×12)
**1D Closed Candles (Last 7 of 499 available, Newest First):**
| Open Time (UTC) | Open | High | Low | Close | Chg% | Vol (BTC) |
|---|---|---|---|---|---|---|
| `2026-11-27` | `$60,577.18` | `$62,248.91` | `$58,792.37` | `$59,923.10` | `-1.08%` | `21,003` |
| `2026-11-26` | `$60,458.00` | `$61,622.38` | `$59,915.00` | `$60,577.18` | `+0.20%` | `16,482` |
| `2026-11-25` | `$59,832.00` | `$60,568.01` | `$57,300.38` | `$60,458.01` | `+1.05%` | `26,999` |
| `2026-11-24` | `$61,270.92` | `$61,682.01` | `$59,260.00` | `$59,832.00` | `-2.35%` | `19,707` |
| `2026-11-23` | `$61,271.09` | `$64,603.12` | `$60,386.00` | `$61,270.93` | `-0.00%` | `27,494` |
| `2026-11-22` | `$60,215.78` | `$61,669.99` | `$58,768.51` | `$61,271.08` | `+1.75%` | `20,137` |
| `2026-11-21` | `$58,951.51` | `$60,996.00` | `$55,130.00` | `$60,215.77` | `+2.14%` | `48,558` |

**4H Closed Candles (Last 12 of 499 available, Newest First):**
| Open Time (UTC) | Open | High | Low | Close | Chg% | Vol (BTC) |
|---|---|---|---|---|---|---|
| `2026-11-28 04:00` | `$60,029.20` | `$60,088.05` | `$59,188.34` | `$59,832.00` | `-0.33%` | `2,229` |
| `2026-11-28 00:00` | `$59,923.10` | `$60,266.01` | `$59,834.38` | `$60,029.20` | `+0.18%` | `1,308` |
| `2026-11-27 20:00` | `$59,910.33` | `$59,925.98` | `$59,580.00` | `$59,923.10` | `+0.02%` | `1,496` |
| `2026-11-27 16:00` | `$60,116.97` | `$60,559.62` | `$59,513.30` | `$59,910.33` | `-0.34%` | `2,750` |
| `2026-11-27 12:00` | `$61,662.57` | `$61,707.41` | `$58,792.37` | `$60,116.98` | `-2.51%` | `6,853` |
| `2026-11-27 08:00` | `$61,672.09` | `$62,248.91` | `$61,415.65` | `$61,662.57` | `-0.02%` | `3,252` |
| `2026-11-27 04:00` | `$61,411.00` | `$62,025.00` | `$61,336.73` | `$61,673.45` | `+0.43%` | `2,951` |
| `2026-11-27 00:00` | `$60,577.18` | `$61,881.03` | `$60,472.00` | `$61,411.00` | `+1.38%` | `3,701` |
| `2026-11-26 20:00` | `$60,718.59` | `$61,006.00` | `$60,390.65` | `$60,577.18` | `-0.23%` | `1,073` |
| `2026-11-26 16:00` | `$60,618.80` | `$60,860.35` | `$60,348.04` | `$60,718.59` | `+0.16%` | `2,053` |
| `2026-11-26 12:00` | `$60,714.00` | `$60,989.07` | `$59,915.00` | `$60,618.79` | `-0.16%` | `2,664` |
| `2026-11-26 08:00` | `$60,521.78` | `$61,070.01` | `$60,466.00` | `$60,714.01` | `+0.32%` | `2,748` |

**1H Closed Candles (Last 12 of 719 available, Newest First):**
| Open Time (UTC) | Open | High | Low | Close | Chg% | Vol (BTC) |
|---|---|---|---|---|---|---|
| `2026-11-28 10:00` | `$59,588.28` | `$59,588.28` | `$59,047.96` | `$59,250.59` | `-0.57%` | `570` |
| `2026-11-28 09:00` | `$59,572.35` | `$59,664.34` | `$59,521.81` | `$59,588.29` | `+0.03%` | `617` |
| `2026-11-28 08:00` | `$59,832.00` | `$59,861.78` | `$59,508.46` | `$59,572.34` | `-0.43%` | `475` |
| `2026-11-28 07:00` | `$59,749.24` | `$59,874.88` | `$59,188.34` | `$59,832.00` | `+0.14%` | `1,260` |
| `2026-11-28 06:00` | `$59,738.42` | `$59,919.83` | `$59,664.00` | `$59,749.23` | `+0.02%` | `381` |
| `2026-11-28 05:00` | `$59,997.05` | `$59,997.05` | `$59,608.12` | `$59,738.41` | `-0.43%` | `379` |
| `2026-11-28 04:00` | `$60,029.20` | `$60,088.05` | `$59,932.12` | `$59,997.06` | `-0.05%` | `209` |
| `2026-11-28 03:00` | `$59,968.19` | `$60,063.89` | `$59,892.33` | `$60,029.20` | `+0.10%` | `382` |
| `2026-11-28 02:00` | `$60,186.64` | `$60,266.01` | `$59,930.00` | `$59,968.19` | `-0.36%` | `366` |
| `2026-11-28 01:00` | `$59,897.25` | `$60,229.09` | `$59,834.38` | `$60,186.64` | `+0.48%` | `357` |
| `2026-11-28 00:00` | `$59,923.10` | `$60,022.01` | `$59,897.25` | `$59,897.25` | `-0.04%` | `203` |
| `2026-11-27 23:00` | `$59,737.24` | `$59,925.98` | `$59,737.24` | `$59,923.10` | `+0.31%` | `315` |

### 7C. MODELED LIQUIDATION LADDER (`10x-100x`) & USD MACRO CALENDAR
**6-Tier Modeled Liquidation Ladder (`global_account_ls_ratio`):**
| Tier | Side | Level ($) | Dist% | Est Pool ($M) |
|---|---|---|---|---|
| `10x Shorts` | `UPPER` | `$65,175.65` | `+10.00%` | `$72.3M` |
| `25x Shorts` | `UPPER` | `$61,620.61` | `+4.00%` | `$96.4M` |
| `50-100x Shorts` | `UPPER` | `$59,843.10` | `+1.00%` | `$193.8M` |
| `100x Longs` | `LOWER` | `$58,658.08` | `-1.00%` | `$350.0M` |
| `25x Longs` | `LOWER` | `$56,880.57` | `-4.00%` | `$350.7M` |
| `10x Longs` | `LOWER` | `$53,325.53` | `-10.00%` | `$245.5M` |

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
