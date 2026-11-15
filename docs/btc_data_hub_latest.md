# TAB [D: DATA HUB] | CONSOLIDATED DATA-ONLY TELEMETRY REPORT
**Retrieval Time (UTC):** `2026-11-15 14:51:53 UTC`  |  **Retrieval Time (MYT):** `2026-11-15 22:51:53 MYT (UTC+8)`
**Spot Price (BTCUSDT):** `$64,913.29`  |  **Coverage:** `OK=61/66 | UNAVAILABLE=3 | STALE=1 | PROXY/STATIC=1`
**24H Range:** `$62,006.00 - $66,189.88`  |  **Returns (24H / 7D / 30D):** `-1.52% / -13.28% / -20.46%`
**Archive (SQLite):** `7 closed-4H snapshots (Last: 2026-11-15 12:00:00 UTC)`

## 1. PRICE, TREND & MARKET STRUCTURE
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| Binance Spot / Perp ($) | `$64,913.29 / $64,886.60` | `All Tabs` | `OK` |
| Coinbase Spot ($) | `$64,861.02` | `1,11,15,17` | `OK` |
| 1D SMA 200 / Slope | `$73,030.62 (-0.24%)` | `0,2,3,11,15,18` | `OK` |
| 1D SMA 50 / EMA 50 | `$80,225.41 / $77,157.60` | `0,2,4,15,18,20` | `OK` |
| 1D EMA 21 / 1W EMA 50 | `$74,190.30 / $78,248.63` | `3,18` | `OK` |
| 4H EMA 50 / EMA 200 | `$71,227.17 / $76,807.81` | `7,13,18,20` | `OK` |
| Grok EMA 9/21 & 1H SMA200 | `9:$65,117.97 · 21:$65,203.89 · 1H:$72,136.68` | `5,15` | `OK` |
| Daily / Weekly VWAP (Z) | `D:$64,348.35 (+0.54σ) | W:$69,906.94` | `4,11,15` | `OK` |
| RSI(14) 1D / 4H & 4H ROC12 | `1D:22.7 · 4H:30.9 · ROC:-5.72%` | `3,7,20` | `OK` |
| ADX(14) 1D/4H & ATR(14) 1D/4H/1H | `ADX 1D:31.5 4H:64.1 | ATR:$2,599.11/$1,505.10/$800.22` | `0,1,2,8,13,18,20` | `OK` |
| Macro 30D VAH / POC / VAL | `$83,467.25 / $81,559.58 / $74,310.45` | `1,3,6,11,19` | `OK` |
| Structure (L20/H20, PW, Asia) | `4H:$63,320.00-$81,971.00 | PW:$73,510.00-$81,196.01 | Asia:$62,006.00-$65,595.77` | `0,8,11,19` | `OK` |

## 2. ORDER FLOW, FOOTPRINT & LIQUIDITY
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| Spot/Perp CVD (15m / 1h) | `15m:-3.3/+229.2 | 1h:-176.3/-825.5 BTC` | `1,8,15` | `OK` |
| Spot/Perp CVD (4h / 24h) | `4h:-224.6/-1620.3 | 24h:-1914.1/-3765.8 BTC` | `0,1,15,16,17` | `OK` |
| Session / UTC-Day CVD | `Sess S:+0.0 P:+0.0 | Day S:-1244.4 P:+245.3` | `REST 15m` | `OK` |
| 24H Z-Scores (z_S / z_F / D) | `z_S:-2.00 · z_F:-0.77 · D:-1.24` | `1,19` | `OK` |
| 15m Footprint Delta / Stack | `Δ:-3.3 BTC (Prev:-66.6) · Stacks:0` | `1,11` | `OK` |
| Coinbase Premium ($ / % / Z) | `-52.3$ (-0.081%, Z=-0.75)` | `1,11,15` | `OK` |
| Cross-Exch 24H Spot Vol (BN/CB) | `BN:38,953 · CB:21,213 · Tot:60,165 BTC` | `1,11,Macro` | `OK` |
| L2 Depth ±1%/±2%, OBI & Spread | `1%:1.65x · 2%:1.52x · Spr:0.0015bps · OBI:+24.6%` | `16,Macro` | `OK` |
| Tactical 7D / Session 24H VP | `7D:$75,919.20/$73,805.81/$67,113.38 | 24H:$65,806.36/$65,527.43/$63,923.61` | `1,11` | `OK` |
| 30D VA Pos% & Dist to VAL | `-102.6% | -12.65% (-11.74 ATR)` | `1` | `OK` |
| SLSP Support / Resistance | `Sup:$64,742.09 | Res:$65,575.31` | `13` | `OK` |

## 3. DERIVATIVES, OPTIONS & LIQUIDATIONS
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| BN Open Interest (BTC / USD) | `95,547 BTC ($6.18B)` | `0,1,4,15,17` | `OK` |
| Cross-Exch Perp OI & Funding | `163,854 BTC ($10.60B) · F:-0.0003% [BN+BYB+OKX 3/3]` | `Macro,15` | `OK` |
| OI Δ% (15m/1h/4h/24h) & Quad | `-0.20%/-0.29%/-0.07%/-4.21% | NEUTRAL_CHURN` | `1,4,8,11,12,15,17` | `OK` |
| Funding 8H% / Ann% / 90D Pct | `+0.0000% (+0.1%/yr) · 90D Pct:8.9%` | `0,4,9,11,15,16,19,20` | `OK` |
| Perp Basis ($ / Ann %) | `-26.7$ (-0.041% | Carry:-0.40%/yr)` | `1,4` | `OK` |
| 5m Taker L/S & Top/Glb Acct | `5m:1.000 (Δ:+1.6) | Top:1.56(61L) · Glb:2.41` | `1,2,15,16` | `OK` |
| Options OI & Put/Call (Deribit) | `P/C:0.761 · TotOI:378,477 BTC` | `Macro,19` | `OK` |
| Options IV Term & Skew (Deribit) | `F:43.5% · B:40.9% · 25dSk:+10.1%` | `Macro,6,19` | `OK` |
| Vol: DVOL, RV20, GK & BBW% | `DVOL:44.1 · RV20:48.8% · GK:80.2% · BBW:83% · Sk20:-0.48` | `0,4,6,16,19` | `OK` |
| Upper / Lower Liq Magnet | `Up:$76,334.44 | Dn:$63,744.85` | `0,2,13,17` | `OK` |
| Magnet Ratios & LSCE | `Imm:1.81x · Ladder:1.79x · Pull:0.55x · LSCE:UNTESTED` | `13,17` | `OK` |
| Liquidations (1H / 24H) & Flush | `DATA UNAVAILABLE` | `0,8,12,13` | `UNAVAILABLE` |

## 4. ON-CHAIN, ETF & STABLECOIN FLOWS
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| MVRV Ratio (On-Chain / Proxy) | `1.188 [CoinMetrics 2026-11-14]` | `Macro,16` | `OK` |
| On-Chain SOPR / aSOPR | `DATA UNAVAILABLE` | `16` | `UNAVAILABLE` |
| Exchange Netflow 24H (CM) | `Net:-3,376.2 BTC (-$215.5M) | In:16,820 Out:20,197` | `Macro,16` | `OK` |
| BTC Exchange Reserves (CM) | `2,720,719 BTC (2026-11-14)` | `Macro,16` | `OK` |
| Stablecoins USDT+USDC Supply | `$244.65B (USDT:$175.36B · USDC:$69.29B)` | `Macro` | `OK` |
| Stablecoin Net Issuance (7D/30D) | `7D:-2.89B · 30D:-11.70B` | `Macro` | `OK` |
| US Spot ETF Flow (Farside 1D/3D) | `DATA UNAVAILABLE` | `2,13` | `UNAVAILABLE` |
| US ETF Tape Proxy (IBIT+FBTC) | `1DVol:$2.28B · 5D:-$6.19B [PROXY]` | `Macro,2,13` | `PROXY` |
| Power-Law Fair & ATH DD% | `$149,297.12 (-56.5%) | DD:-48.6%` | `3` | `OK` |
| MTF MACD (1D / 1H Status) | `1D=negative_slope (Macro Whipsaw Veto) | 1H=positive_slope CROSS` | `13,16,18` | `OK` |

## 5. MACRO, CREDIT & US LIQUIDITY
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| US SOFR Rate & Vol (NY Fed) | `3.90% (Vol:$3,138B)` | `Macro` | `OK` |
| Fed ON RRP Balance (NY Fed) | `$0.33B` | `Macro` | `OK` |
| Credit Spread HYG/LQD & 5D% | `0.7484 (+1.29% 5D)` | `Macro,3` | `OK` |
| DXY / US 10Y (^TNX) | `103.41 (RISING (+1.76 over 5d)) | 10Y:5.15%` | `3,13` | `OK` |
| TIPS Real (DFII10) / BEI | `Real:+2.91% | BEI:2.24%` | `3,13` | `OK` |
| S&P 500 / Nasdaq (1D%) | `SPX:7,562 (-0.40%) | NDX:25,136` | `3,13` | `OK` |
| VIX / Brent Crude (BZ=F) | `VIX:19.30 | Brent:$95.84` | `3,13` | `OK` |
| BTC-SPX Corr (20D / 60D) | `20D:+0.41 | 60D:+0.44` | `3` | `OK` |
| Fear & Greed / BTC Dom% | `F&G:10 (Extreme Fear) | Dom:58.70%` | `3,13` | `OK` |
| Manual Context Overrides | `200D_Veto=False · Filter=NONE_SIGNIFICANT` | `2,13` | `OK` |

## 6. QUANT FEATURES, FEED HEALTH & ARCHIVE
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| Rough Path Lévy (A_SP / MM) | `4H A_SP:-2.5758 | MM PriceFlow:-0.0184 · Rough:0.630` | `5,19` | `OK` |
| Hurst / Kalman Vel / FracDiff | `H:0.659 · KVel:-47.30 · d:0.20` | `5,6` | `OK` |
| Hilbert Cycle / TD9 / TellTale | `Cyc:72.0b · TD(1H/4H):1/1 · RV(15m/5m):0.48/N/A` | `5,9,13` | `OK` |
| VCR 72H & TSFM Disp% | `VCR:13.17 | Disp:1.28%` | `6` | `OK` |
| Open FVGs & Sweep FSM | `FVGs:8 | FSM:None (0/12)` | `1,8` | `OK` |
| WebSocket Feeds & Warmup | `Spot:SYNC (no tick) | Perp:SYNC (no tick) | CB:SYNC (12s ago) | Warm:YES` | `Live Feeds` | `STALE` |
| Spot Klines (1W/1D/4H/1H/15m) | `1W:100 1D:500 bars · 11-15 00:00 UTC | 4H:500 1H:720 15m:240` | `All Tabs` | `OK` |
| Perp Klines / Est. Excluded | `1D:101 · 1H:720 · 15m:240 (Excl=399)` | `1,4,11,15,19` | `OK` |
| Closed 4H Anchor (Tab 19/20) | `2026-11-15 12:00:00 UTC` | `18,19,20` | `OK` |
| B1/B2 Rec & Companion Liq | `Rec:PASS (0s delta) | Liq:N/A` | `8,13,17` | `OK` |
| Telemetry History Archive (SQLite) | `7 bars logged (Last: 2026-11-15 12:00:00 UTC)` | `DB Archive` | `OK` |

## 7. RECENT CLOSED-4H SNAPSHOT TRAJECTORY (SQLITE ARCHIVE)
| Closed 4H Bar (UTC) | Spot ($) | 24H Spot/Perp CVD | Cross-Exch Perp OI & Funding | Funding 8H% / 90D Pct | MVRV Ratio |
|---|---|---|---|---|---|
| `2026-11-15 12:00:00 UTC` | `$64,913.29` | `24h:-1914.1/-3765.8 BTC` | `163,854 BTC ($10.60B) · F:-0.0003% [BN+BYB+OKX 3/3]` | `+0.0000% (+0.1%/yr) · 90D Pct:8.9%` | `1.188 [CoinMetrics 2026-11-14]` |
| `2026-11-15 08:00:00 UTC` | `$65,382.44` | `24h:-2631.4/-3894.5 BTC` | `165,148 BTC ($10.70B) · F:+0.0026% [BN+BYB+OKX 3/3]` | `+0.0025% (+2.8%/yr) · 90D Pct:0.0%` | `1.188 [CoinMetrics 2026-11-14]` |
| `2026-11-15 04:00:00 UTC` | `$64,080.97` | `24h:-2387.2/-6281.0 BTC` | `166,701 BTC ($10.71B) · F:+0.0018% [BN+BYB+OKX 3/3]` | `+0.0036% (+3.9%/yr) · 90D Pct:0.7%` | `1.188 [CoinMetrics 2026-11-14]` |
| `2026-11-15 00:00:00 UTC` | `$64,272.01` | `24h:-2238.0/-7818.2 BTC` | `167,545 BTC ($10.73B) · F:+0.0033% [BN+BYB+OKX]` | `+0.0050% (+5.5%/yr) · P90:0.7%` | `1.267 [CoinMetrics 2026-11-13]` |
| `2026-11-14 20:00:00 UTC` | `$65,534.82` | `24h:-2470.9/-3413.1 BTC` | `167,154 BTC ($10.95B) · F:+0.0026% [BN+BYB+OKX]` | `+0.0029% (+3.2%/yr) · P90:39.3%` | `1.267 [CoinMetrics 2026-11-13]` |
| `2026-11-14 16:00:00 UTC` | `$65,484.09` | `24h:-2202.7/-9856.6 BTC` | `200,720 BTC ($13.14B) · F:+0.0059% [BN+BYB+OKX]` | `+0.0035% (+3.8%/yr) · P90:31.9%` | `1.267 [CoinMetrics 2026-11-13]` |

### 7A. 500-BAR MARKET STRUCTURE & HISTORICAL S/R ZONES (`1D / 4H / 1H`)
| TF (Bars) | Swing Structure | Last Swing Pivots | Latest BOS | Resistance Zones (Above Spot) | Support Zones (Below Spot) |
|---|---|---|---|---|---|
| `1D (499)` | `DOWNTREND (LH/LL)` | `SH:$81,196.01 (11-04) · SL:$79,800.00 (10-15)` | `BOS Down < $79,800.00 (10-29)` | `$65,182.19 (5x), $67,124.15 (2x), $70,983.00 (1x)` | `$62,440.17 (3x), $60,000.00 (1x), $59,130.91 (1x)` |
| `4H (499)` | `DOWNTREND (LH/LL)` | `SH:$74,811.45 (11-11 20:00) · SL:$72,727.27 (11-10 16:00)` | `BOS Down < $72,727.27 (11-12 12:00)` | `$72,727.27 (1x), $73,510.00 (1x), $75,173.28 (6x)` | `None below in lookback` |
| `1H (500)` | `DOWNTREND (LH/LL)` | `SH:$65,595.77 (11-15 03:00) · SL:$62,006.00 (11-15 01:00)` | `BOS Up > $65,595.77 (11-15 10:00)` | `$65,595.77 (1x), $66,456.00 (1x), $67,731.35 (3x)` | `$62,006.00 (1x)` |

### 7B. RECENT CLOSED KLINES — OHLCV PRICE ACTION (`1D`×7, `4H`×12, `1H`×12)
**1D Closed Candles (Last 7 of 499 available, Newest First):**
| Open Time (UTC) | Open | High | Low | Close | Chg% | Vol (BTC) |
|---|---|---|---|---|---|---|
| `2026-11-14` | `$68,314.01` | `$68,446.21` | `$63,320.00` | `$64,150.00` | `-6.10%` | `32,675` |
| `2026-11-13` | `$71,460.00` | `$71,514.01` | `$67,568.00` | `$68,314.00` | `-4.40%` | `29,649` |
| `2026-11-12` | `$74,015.20` | `$74,217.49` | `$71,113.06` | `$71,460.00` | `-3.45%` | `15,228` |
| `2026-11-11` | `$73,796.06` | `$74,811.45` | `$73,209.12` | `$74,015.19` | `+0.30%` | `16,146` |
| `2026-11-10` | `$75,368.41` | `$75,442.01` | `$72,727.27` | `$73,796.06` | `-2.09%` | `16,466` |
| `2026-11-09` | `$74,851.44` | `$75,599.22` | `$73,750.00` | `$75,368.41` | `+0.69%` | `15,687` |
| `2026-11-08` | `$75,867.58` | `$76,200.00` | `$73,510.00` | `$74,851.44` | `-1.34%` | `9,458` |

**4H Closed Candles (Last 12 of 499 available, Newest First):**
| Open Time (UTC) | Open | High | Low | Close | Chg% | Vol (BTC) |
|---|---|---|---|---|---|---|
| `2026-11-15 08:00` | `$64,012.59` | `$66,132.01` | `$63,873.26` | `$65,351.00` | `+2.09%` | `5,254` |
| `2026-11-15 04:00` | `$64,826.00` | `$65,169.23` | `$63,777.00` | `$64,012.60` | `-1.25%` | `3,302` |
| `2026-11-15 00:00` | `$64,150.01` | `$65,595.77` | `$62,006.00` | `$64,825.99` | `+1.05%` | `11,461` |
| `2026-11-14 20:00` | `$65,727.61` | `$65,884.01` | `$63,320.00` | `$64,150.00` | `-2.40%` | `8,948` |
| `2026-11-14 16:00` | `$65,742.00` | `$66,189.88` | `$65,000.00` | `$65,727.61` | `-0.02%` | `4,554` |
| `2026-11-14 12:00` | `$67,272.79` | `$67,322.87` | `$65,066.66` | `$65,742.01` | `-2.28%` | `8,079` |
| `2026-11-14 08:00` | `$67,165.42` | `$67,523.05` | `$66,966.79` | `$67,272.79` | `+0.16%` | `2,719` |
| `2026-11-14 04:00` | `$66,755.91` | `$67,460.01` | `$66,456.00` | `$67,165.42` | `+0.61%` | `3,414` |
| `2026-11-14 00:00` | `$68,314.01` | `$68,446.21` | `$66,613.55` | `$66,755.66` | `-2.28%` | `4,961` |
| `2026-11-13 20:00` | `$69,060.50` | `$69,118.02` | `$67,865.00` | `$68,314.00` | `-1.08%` | `2,123` |
| `2026-11-13 16:00` | `$68,899.65` | `$69,134.01` | `$68,383.99` | `$69,060.50` | `+0.23%` | `1,693` |
| `2026-11-13 12:00` | `$69,318.23` | `$70,214.31` | `$68,103.00` | `$68,899.65` | `-0.60%` | `5,645` |

**1H Closed Candles (Last 12 of 719 available, Newest First):**
| Open Time (UTC) | Open | High | Low | Close | Chg% | Vol (BTC) |
|---|---|---|---|---|---|---|
| `2026-11-15 13:00` | `$65,509.24` | `$65,800.75` | `$65,368.00` | `$65,442.01` | `-0.10%` | `689` |
| `2026-11-15 12:00` | `$65,351.00` | `$65,578.01` | `$65,184.35` | `$65,509.24` | `+0.24%` | `712` |
| `2026-11-15 11:00` | `$65,599.49` | `$65,599.49` | `$65,244.94` | `$65,351.00` | `-0.38%` | `727` |
| `2026-11-15 10:00` | `$65,350.52` | `$65,677.21` | `$65,340.00` | `$65,599.48` | `+0.38%` | `877` |
| `2026-11-15 09:00` | `$65,207.01` | `$66,132.01` | `$65,117.60` | `$65,350.51` | `+0.22%` | `1,920` |
| `2026-11-15 08:00` | `$64,012.59` | `$65,272.04` | `$63,873.26` | `$65,216.00` | `+1.88%` | `1,730` |
| `2026-11-15 07:00` | `$64,463.38` | `$64,544.01` | `$63,777.00` | `$64,012.60` | `-0.70%` | `1,191` |
| `2026-11-15 06:00` | `$64,516.04` | `$64,640.99` | `$64,179.90` | `$64,463.38` | `-0.08%` | `767` |
| `2026-11-15 05:00` | `$64,934.20` | `$65,032.16` | `$64,455.27` | `$64,515.67` | `-0.64%` | `605` |
| `2026-11-15 04:00` | `$64,826.00` | `$65,169.23` | `$64,666.00` | `$64,934.20` | `+0.17%` | `739` |
| `2026-11-15 03:00` | `$64,900.01` | `$65,595.77` | `$64,745.15` | `$64,825.99` | `-0.11%` | `1,977` |
| `2026-11-15 02:00` | `$62,624.99` | `$65,111.93` | `$62,485.54` | `$64,900.00` | `+3.63%` | `3,490` |

## 8. METRIC FORMULA LEGEND & CORTEX DESK LITE PROTOCOL
- **Rough Path Lévy (`4H A_SP`)**: Lévy signed area over 6 closed 4H bars (`> 0`: Spot path leads price markup; `< 0`: Spot path lags price / distribution).
- **24H Z-Scores (`z_S / z_F / D`)**: 30-day rolling Z-scores of 24H Spot (`z_S`) and Perp (`z_F`) cumulative delta; `D = z_S - z_F` (`D > 0` = Spot buying divergence vs Perps).
- **Volume Profile & Structure**: `30D VA Pos% = (Spot - VAL) / (VAH - VAL) * 100` (Macro 30D Value Area); `ATR(14) 1D/4H/1H`; `L20/H20` = 20-bar (80H) 4H range boundaries; `SLSP` = structural liquidity pool S/R; `7A` scans 500 closed bars (`5x5` pivots) for `HH/HL/LH/LL`, `BOS`, and `1%`-clustered S/R zones.
- **Derivatives & Quant**: `90D Pct` = 0-100 rolling 90-day percentile rank of 8H funding; `[... X/3 PARTIAL_VENUE]` suppresses OI quadrant tagging when `<3` venues report; `H` = Hurst exponent (`>0.5` trending, `<0.5` mean-reverting); `VCR 72H` = Volatility Compression Ratio; `TSFM Disp%` = horizon dispersion; `LSCE` = liquidation sweep state.
- **Headless Snapshot Note**: Scheduled/GitHub Actions runs execute a one-shot REST warmup (`Warm:YES`) without a persistent WebSocket loop, so `WebSocket Feeds & Warmup` reporting `STALE` (`no tick`) is expected by design and does not indicate stale REST, orderbook, CVD, or derivatives data.

### DIRECT AI EXECUTION PROTOCOL: CORTEX BTC DESK LITE v1.0
Analyze BTC using the telemetry snapshot above. Operate as **CORTEX BTC DESK LITE v1.0** — a Spot-Only Institutional Capital Preservation & Swing Execution Workstation. Apply strict **zero-hallucination** rules using only metrics explicitly reported above (`7`, `7A`, `7B`, and Sections `1-6`).

**Step 1 — Mandatory Data Hygiene Gate (Run First):**
- Verify `Coverage` and isolate all `UNAVAILABLE`, `STALE`, and `PROXY/STATIC` feeds before scoring.
- Verify whether `WebSocket Feeds & Warmup` (`STALE`) is a headless REST warmup (`Warm:YES`), distinguishing expected one-shot snapshot behavior from genuine REST staleness.
- Flag `[... PARTIAL_VENUE]` on `Cross-Exch Perp OI & Funding` or Section `7` history — never treat partial venue counts (`< 3/3`) as genuine deleveraging.
- Read `90D Pct` strictly as a `0-100` rolling 90-day funding rank, `30D VA Pos%` strictly vs Macro 30D VAH/VAL, and `ATR(14) 1D/4H/1H` across matching timeframes.
- Do not cite missing metrics or external prices outside this telemetry snapshot.

**Step 2 — 5-Function Deterministic Synthesis:**
1. **Multi-Timeframe Regime Classifier:** Integrate Section `1`, `7A` (`1D/4H/1H` swing structure & BOS), `7B` closed OHLCV price action, `1D/4H` ADX, `RSI(14)`, EMA/SMA stack, and Hurst `H` -> classify as `UPTREND`, `DOWNTREND`, `RANGE-BOUND`, or `TRANSITIONAL`.
2. **Spot Flow & Liquidity Inspector:** Evaluate `Spot/Perp CVD` across `15m/1h/4h/24h`, `z_S / z_F / D`, `Coinbase Premium`, `L2 Depth`, `OBI`, `Spr`, `30D VA Pos%`, `SLSP`, and `7A` S/R clusters -> classify true spot accumulation vs distribution or passive absorption.
3. **Derivatives & Squeeze Risk Profiler:** Evaluate `BN OI`, `Cross-Exch OI` (only when `3/3` venues valid), `OI Δ%` & Quad, `Funding 8H% / Ann% / 90D Pct`, `DVOL`, `25d RR Skew`, and liquidation clusters -> classify leverage fragility and squeeze asymmetry.
4. **Macro, On-Chain & ETF Gatekeeper:** Synthesize `MVRV`, `SOPR`, `ETF Net Flow`, `Stablecoin Supply`, `DXY`, `US10Y`, `VIX`, `SPX`, and `Net Liquidity` -> assign macro backdrop (`Tailwind`, `Neutral`, or `Headwind`).
5. **Spot-Only Risk & Decision Arbiter:** Enforce hard capital-preservation gates: if `1D` closes below `1D SMA 200` and `4H` shows active downtrend / broken structure, or trend conviction fails multi-gate alignment, enforce `100% USDT CASH — NO ENTRY`. Never force an entry in chop (`ADX < 20` or `TRANSITIONAL`). For any qualified spot setup, cap maximum portfolio risk at `0.75%` per position.

**Step 3 — Mandatory Output Contract:**
- **1. EXECUTIVE SUMMARY & DESK POSTURE** (Spot Price, Regime State, Posture: `ACTIVE SPOT LONG` or `100% USDT CASH — NO ENTRY`, Confidence `/100`).
- **2. DATA HYGIENE AUDIT** (Exact `OK/UNAVAILABLE/STALE/PROXY` tally, headless WS clarification, any `PARTIAL_VENUE` anomalies, degraded-signal list).
- **3. MULTI-TIMEFRAME REGIME & FLOW SYNTHESIS** (Price/EMA/ADX structure vs Spot CVD, Coinbase Premium, and 4H SQLite Section `7` + `7A/7B` trajectory).
- **4. DERIVATIVES, LIQUIDITY & MACRO CONTEXT** (OI venue-integrity check, funding `90D Pct`, options skew, liquidity pools, macro/ETF headwind vs tailwind).
- **5. CRITICAL LEVELS MAP** (Immediate & Major Support, Immediate & Major Resistance, Hard Invalidation Levels tied to `7A/7B` & `SLSP`).
- **6. SPOT EXECUTION PLAN (OR NO-ENTRY GATE)** (Exact Entry Zone, Stop Loss, Take Profit Targets, Position Size at `<= 0.75%` portfolio risk, and explicit Multi-Gate Validation Triggers required to shift posture).
