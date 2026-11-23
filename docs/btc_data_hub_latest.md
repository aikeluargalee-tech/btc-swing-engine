# TAB [D: DATA HUB] | CONSOLIDATED DATA-ONLY TELEMETRY REPORT
**Retrieval Time (UTC):** `2026-11-23 01:35:17 UTC`  |  **Retrieval Time (SGT):** `2026-11-23 09:35:17 SGT (UTC+8)`
**Spot Price (BTCUSDT):** `$61,226.01`  |  **Coverage:** `OK=65/71 | UNAVAILABLE=4 | STALE=1 (Genuine=0, Expected_Headless_WS_Offline=1) | PROXY/STATIC=1`
**24H Range:** `$58,768.51 - $61,669.99`  |  **Returns (24H / 7D / 30D):** `+1.85% / -5.64% / -24.31%`
**Archive (SQLite):** `45 closed-4H snapshots (Last: 2026-11-23 00:00:00 UTC)`

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
| Timestamp & Candle Closed Status | `2026-11-23 01:35:17 UTC | 2026-11-23 09:35:17 SGT (UTC+8) · Closed-Candle Inputs Only` | `Strict closed-bar verification gate` |

**BIDIRECTIONAL REGIME ROUTER STATUS:**
- **Active Route:** `MACRO_DOWNTREND_DISTRIBUTION`
- **Primary Active Rail:** `RAIL A — BTC -> USDT CONVERSION (DEFENSIVE / SELL RALLIES)`
- **Active BTC Inventory (`Rail A: BTC -> USDT`):** `ACTIVE (RAIL A) — CONVERT INTO OVERHEAD RESISTANCE`
- **Active USDT Inventory (`Rail B: USDT -> BTC`):** `RESTRICTED (RAIL B) — HOLD PENDING VALIDATED SWEEP & RECLAIM`
- **Condition A (`1D Close < 1D SMA 200`):** `YES`  |  **Condition B (`4H Downside Structure / BOS`):** `YES`

## 1. PRICE, TREND & MARKET STRUCTURE
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| Binance Spot / Perp ($) | `$61,226.01 / $61,188.90` | `All Tabs` | `OK` |
| Coinbase Spot ($) | `$61,112.42` | `1,11,15,17` | `OK` |
| 1D SMA 200 / Slope | `$72,384.86 (-0.65%)` | `0,2,3,11,15,18` | `OK` |
| 1D SMA 50 / EMA 50 | `$76,762.02 / $73,000.45` | `0,2,4,15,18,20` | `OK` |
| 1D EMA 21 / 1W EMA 50 | `$67,577.77 / $77,712.30` | `3,18` | `OK` |
| 4H EMA 50 / EMA 200 | `$63,096.30 / $71,495.03` | `7,13,18,20` | `OK` |
| Grok EMA 9/21 & 1H SMA200 | `9:$61,074.14 · 21:$60,745.31 · 1H:$62,698.55` | `5,15` | `OK` |
| Daily / Weekly VWAP (Z) | `D:$61,201.15 (+0.40σ) | W:$61,401.50` | `4,11,15` | `OK` |
| RSI(14) 1D / 4H & 4H ROC12 | `1D:26.5 · 4H:50.5 · ROC:+3.93%` | `3,7,20` | `OK` |
| ADX(14) 1D/4H & ATR(14) 1D/4H/1H | `ADX 1D:50.8 4H:41.6 | ATR:$3,011.32/$1,297.89/$470.86` | `0,1,2,8,13,18,20` | `OK` |
| 4H ATR(14)% Pctile & RelVol(20) | `ATR%:2.25% (87th pct/120b) · RelVol:0.39x` | `0,1,2,20` | `OK` |
| Macro 30D VAH / POC / VAL | `BIMODAL (Peaks: $64,859.86 & $80,517.11 — single VA UNAVAILABLE)` | `1,3,6,11,19` | `UNAVAILABLE` |
| Structure (L20/H20, PW, Asia) | `4H:$55,130.00-$81,196.01 | PW:$55,130.00-$65,696.16 | Asia:$60,924.30-$61,464.35` | `0,8,11,19` | `OK` |

## 2. ORDER FLOW, FOOTPRINT & LIQUIDITY
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| Spot/Perp CVD (15m / 1h) | `15m:+18.5/+92.9 | 1h:+72.2/-108.0 BTC` | `1,8,15` | `OK` |
| Spot/Perp CVD (4h / 24h) | `4h:+95.1/-350.7 | 24h:+409.9/+2913.1 BTC` | `0,1,15,16,17` | `OK` |
| Spot CVD Slopes (7D / 14D) | `7D:-4,470.0 BTC | 14D:-8,305.8 BTC` | `17` | `OK` |
| Session / UTC-Day CVD | `Sess S:+0.0 P:+0.0 | Day S:+8.4 P:-477.2` | `REST 15m` | `OK` |
| 24H Z-Scores (z_S / z_F / D) | `z_S:+0.20 · z_F:+1.58 · D:-1.37` | `1,19` | `OK` |
| 15m Footprint Delta / Stack | `Δ:+18.5 BTC (Prev:+0.0) · Stacks:0` | `1,11` | `OK` |
| Coinbase Premium ($ / % / Z) | `-113.6$ (-0.186%, Z=-1.52)` | `1,11,15` | `OK` |
| Cross-Exch 24H Spot Vol (BN/CB) | `BN:20,416 · CB:9,194 · Tot:29,610 BTC` | `1,11,Macro` | `OK` |
| L2 Depth ±1%/±2%, OBI & Spread | `1%:0.78x · 2%:0.56x · Spr:0.0016bps · OBI:-12.6%` | `16,Macro` | `OK` |
| Tactical 7D / Session 24H VP | `7D:$65,299.93/$64,595.52/$59,488.54 | 24H:$61,452.38/$60,968.80/$59,904.92` | `1,11` | `OK` |
| 30D VA Pos% & Dist to VAL | `BIMODAL — DATA UNAVAILABLE` | `1` | `UNAVAILABLE` |
| SLSP Support / Resistance | `Sup:$61,166.36 | Res:$62,371.96` | `13` | `OK` |

## 3. DERIVATIVES, OPTIONS & LIQUIDATIONS
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| BN Open Interest (BTC / USD) | `93,318 BTC ($5.68B)` | `0,1,4,15,17` | `OK` |
| Cross-Exch Perp OI & Funding | `159,057 BTC ($9.69B) · F:-0.0002% [BN+BYB+OKX 3/3]` | `Macro,15` | `OK` |
| Hyperliquid Perp OI & Funding | `38,318 BTC ($2.34B) · F:+0.0070% [HL DEX]` | `Macro,15` | `OK` |
| OI Δ% (15m/1h/4h/24h) & Quad | `+0.05%/-0.22%/+0.27%/+0.65% | NEUTRAL_CHURN` | `1,4,8,11,12,15,17` | `OK` |
| Funding 8H% / Ann% / 90D Pct | `-0.0005% (-0.6%/yr) · 90D Pct:17.8%` | `0,4,9,11,15,16,19,20` | `OK` |
| Perp Basis ($ / Ann %) | `-37.1$ (-0.061% | Carry:-1.30%/yr)` | `1,4` | `OK` |
| 5m Taker L/S & Top/Glb Acct | `5m:1.416 (Δ:+37.0) | Top:1.65(62L) · Glb:2.14` | `1,2,15,16` | `OK` |
| Options OI & Put/Call (Deribit) | `P/C:0.811 · TotOI:422,144 BTC` | `Macro,19` | `OK` |
| Options IV Term & Skew (Deribit) | `F:53.0% · B:47.1% · 25dSk:+8.6%` | `Macro,6,19` | `OK` |
| Vol: DVOL, RV20, GK & BBW% | `DVOL:54.3 · RV20:51.7% · GK:85.2% · BBW:97% · Sk20:-0.26` | `0,4,6,16,19` | `OK` |
| Upper / Lower Liq Magnet | `Up:$76,334.44 | Dn:$60,123.94` | `0,2,13,17` | `OK` |
| Magnet Ratios & LSCE | `Imm:1.81x · Ladder:1.38x · Pull:0.55x · LSCE:UNTESTED` | `13,17` | `OK` |
| Modeled Liq Ladder (10x-100x) | `Up[10x:$67,348.61($87M) / 25x:$63,675.05($116M) / 50-100x:$61,838.27($194M)] | Dn[100x:$60,613.75($350M) / 25x:$58,776.97($312M) / 10x:$55,103.41($218M)] [Modeled] (L/S:global_account_ls_ratio)` | `17` | `OK` |
| Liquidations (1H / 24H) & Flush | `DATA UNAVAILABLE` | `0,8,12,13` | `UNAVAILABLE` |

## 4. ON-CHAIN, ETF & STABLECOIN FLOWS
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| MVRV Ratio (On-Chain / Proxy) | `1.130 [CoinMetrics 2026-11-21]` | `Macro,16` | `OK` |
| On-Chain SOPR / aSOPR | `DATA UNAVAILABLE` | `16` | `UNAVAILABLE` |
| Exchange Netflow 24H (CM) | `Net:-12,025.4 BTC (-$723.0M) | In:37,664 Out:49,690` | `Macro,16` | `OK` |
| BTC Exchange Reserves (CM) | `2,698,129 BTC (2026-11-21)` | `Macro,16` | `OK` |
| Stablecoins USDT+USDC Supply | `$243.20B (USDT:$174.53B · USDC:$68.67B)` | `Macro` | `OK` |
| Stablecoin Net Issuance (7D/30D) | `7D:-1.33B · 30D:-10.98B` | `Macro` | `OK` |
| US Spot ETF Flow (Farside 1D/3D) | `1D:-$124.5M | 3D:-$1.01B | 5D:-$1.25B` | `2,13` | `OK` |
| US ETF Tape Proxy (IBIT+FBTC) | `1DVol:$4.02B · 5D:-$13.65B [PROXY]` | `Macro,2,13` | `PROXY` |
| Power-Law Fair & ATH DD% | `$150,267.43 (-59.3%) | DD:-51.5%` | `3` | `OK` |
| MTF MACD (1D / 1H Status) | `1D=negative_slope (Macro Whipsaw Veto) | 1H=positive_slope CROSS` | `13,16,18` | `OK` |

## 5. MACRO, CREDIT & US LIQUIDITY
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| US SOFR Rate & Vol (NY Fed) | `3.91% (Vol:$3,161B)` | `Macro` | `OK` |
| Fed ON RRP Balance (NY Fed) | `$0.40B` | `Macro` | `OK` |
| Credit Spread HYG/LQD & 5D% | `0.7361 (-1.63% 5D)` | `Macro,3` | `OK` |
| DXY / US 10Y (^TNX) | `103.75 (NEUTRAL / FLAT (+0.20 over 5d)) | 10Y:4.91%` | `3,13` | `OK` |
| TIPS Real (DFII10) / BEI | `Real:+2.77% | BEI:2.14%` | `3,13` | `OK` |
| S&P 500 / Nasdaq (1D%) | `SPX:6,910 (-3.70%) | NDX:22,618` | `3,13` | `OK` |
| VIX / Brent Crude (BZ=F) | `VIX:35.89 | Brent:$89.55` | `3,13` | `OK` |
| BTC-SPX Corr (20D / 60D) | `20D:+0.67 | 60D:+0.71` | `3` | `OK` |
| Fear & Greed / BTC Dom% | `F&G:11 (Extreme Fear) | Dom:58.90%` | `3,13` | `OK` |
| USD Macro Calendar (High) | `Core PCE Price Index m/m (in 59.9h Fc:0.3%) | Prelim GDP q/q (in 59.9h Fc:3.5%)` | `Macro` | `OK` |
| Manual Context Overrides | `Legacy_200D_Veto_Override: IGNORED (Tab1_Flag=True) · Filter=NONE_SIGNIFICANT` | `2,13` | `OK` |

## 6. QUANT FEATURES, FEED HEALTH & ARCHIVE
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| Rough Path Lévy (A_SP / MM) | `4H A_SP:-0.5393 | MM PriceFlow:-2.6072 · Rough:2.070` | `5,19` | `OK` |
| Hurst / Kalman Vel / FracDiff | `H:0.780 · KVel:-41.10 · d:0.15` | `5,6` | `OK` |
| Hilbert Cycle / TD9 / TellTale | `Cyc:23.0b · TD(1H/4H):5/5 · RV(15m/5m):0.29/N/A` | `5,9,13` | `OK` |
| VCR 72H & TSFM Disp% | `VCR:18.23 | Disp:1.28%` | `6` | `OK` |
| Open FVGs & Sweep FSM | `FVGs:4 | FSM:None (0/12)` | `1,8` | `OK` |
| WebSocket Feeds & Warmup | `Spot:SYNC (no tick) | Perp:SYNC (no tick) | CB:SYNC (12s ago) | Warm:YES` | `Live Feeds` | `STALE` |
| Spot Klines (1W/1D/4H/1H/15m) | `1W:100 1D:500 bars · 11-23 00:00 UTC | 4H:500 1H:720 15m:240` | `All Tabs` | `OK` |
| Perp Klines / Est. Excluded | `1D:101 · 1H:720 · 15m:240 (Excl=399)` | `1,4,11,15,19` | `OK` |
| Closed 4H Anchor (Tab 19/20) | `2026-11-23 00:00:00 UTC` | `18,19,20` | `OK` |
| B1/B2 Rec & Companion Liq | `Rec:PASS (0s delta) | Liq:N/A` | `8,13,17` | `OK` |
| Telemetry History Archive (SQLite) | `45 bars logged (Last: 2026-11-23 00:00:00 UTC)` | `DB Archive` | `OK` |

## 7. RECENT CLOSED-4H SNAPSHOT TRAJECTORY (SQLITE ARCHIVE)
| Closed 4H Bar (UTC) | Spot ($) | 24H Spot/Perp CVD | Cross-Exch Perp OI & Funding | Funding 8H% / 90D Pct | MVRV Ratio |
|---|---|---|---|---|---|
| `2026-11-23 00:00:00 UTC` | `$61,209.38` | `24h:+346.3/+3356.7 BTC` | `159,028 BTC ($9.73B) · F:+0.0018% [BN+BYB+OKX 3/3]` | `+0.0026% (+2.8%/yr) · 90D Pct:17.8%` | `1.130 [CoinMetrics 2026-11-21]` |
| `2026-11-22 20:00:00 UTC` | `$60,715.96` | `24h:+57.3/+2761.9 BTC` | `159,257 BTC ($9.66B) · F:+0.0017% [BN+BYB+OKX 3/3]` | `+0.0024% (+2.6%/yr) · 90D Pct:21.5%` | `1.130 [CoinMetrics 2026-11-21]` |
| `2026-11-22 16:00:00 UTC` | `$60,912.18` | `24h:+375.5/+3168.4 BTC` | `159,936 BTC ($9.73B) · F:-0.0001% [BN+BYB+OKX 3/3]` | `-0.0008% (-0.8%/yr) · 90D Pct:21.5%` | `1.130 [CoinMetrics 2026-11-21]` |
| `2026-11-22 12:00:00 UTC` | `$60,790.52` | `24h:+533.1/+3830.1 BTC` | `159,713 BTC ($9.71B) · F:+0.0032% [BN+BYB+OKX 3/3]` | `+0.0035% (+3.9%/yr) · 90D Pct:33.0%` | `1.130 [CoinMetrics 2026-11-21]` |
| `2026-11-22 08:00:00 UTC` | `$59,652.48` | `24h:+173.0/+5997.3 BTC` | `158,396 BTC ($9.51B) · F:+0.0045% [BN+BYB+OKX 3/3]` | `+0.0060% (+6.6%/yr) · 90D Pct:33.0%` | `1.130 [CoinMetrics 2026-11-21]` |
| `2026-11-22 04:00:00 UTC` | `$59,227.59` | `24h:-1482.1/+3498.9 BTC` | `157,253 BTC ($9.33B) · F:+0.0050% [BN+BYB+OKX 3/3]` | `+0.0061% (+6.7%/yr) · 90D Pct:1.9%` | `1.130 [CoinMetrics 2026-11-21]` |

### 7A. 500-BAR MARKET STRUCTURE & HISTORICAL S/R ZONES (`1D / 4H / 1H`)
| TF (Bars) | Swing Structure | Last Swing Pivots | Latest BOS | Resistance Zones (Above Spot) | Support Zones (Below Spot) |
|---|---|---|---|---|---|
| `1D (499)` | `DOWNTREND (LH/LL)` | `SH:$81,196.01 (11-04) · SL:$79,800.00 (10-15)` | `BOS Down < $79,800.00 (10-29)` | `$62,440.17 (3x), $65,182.19 (5x), $67,124.15 (2x)` | `$60,000.00 (1x), $59,130.91 (1x), $57,957.60 (2x)` |
| `4H (499)` | `DOWNTREND (LH/LL)` | `SH:$65,696.16 (11-16 12:00) · SL:$55,130.00 (11-21 04:00)` | `BOS Down < $62,062.97 (11-19 20:00)` | `$62,034.49 (2x), $63,620.51 (2x), $65,696.16 (1x)` | `$55,130.00 (1x)` |
| `1H (500)` | `UPTREND (HH/HL)` | `SH:$61,669.99 (11-22 12:00) · SL:$58,768.51 (11-22 05:00)` | `BOS Up > $60,568.01 (11-22 09:00)` | `$62,166.63 (6x), $63,894.86 (4x), $65,429.09 (7x)` | `$60,951.53 (3x), $58,768.51 (1x), $57,778.35 (1x)` |

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
| `2026-11-21 04:00` | `$56,740.43` | `$58,672.05` | `$55,130.00` | `$57,997.00` | `+2.21%` | `18,082` |
| `2026-11-21 00:00` | `$58,951.51` | `$59,248.06` | `$56,400.00` | `$56,740.43` | `-3.75%` | `9,620` |

**1H Closed Candles (Last 12 of 719 available, Newest First):**
| Open Time (UTC) | Open | High | Low | Close | Chg% | Vol (BTC) |
|---|---|---|---|---|---|---|
| `2026-11-23 00:00` | `$61,271.09` | `$61,464.35` | `$61,050.04` | `$61,351.33` | `+0.13%` | `860` |
| `2026-11-22 23:00` | `$61,115.09` | `$61,407.99` | `$60,796.82` | `$61,271.08` | `+0.26%` | `897` |
| `2026-11-22 22:00` | `$60,953.86` | `$61,115.09` | `$60,773.56` | `$61,115.08` | `+0.26%` | `579` |
| `2026-11-22 21:00` | `$60,916.86` | `$61,118.01` | `$60,869.33` | `$60,953.87` | `+0.06%` | `339` |
| `2026-11-22 20:00` | `$60,737.12` | `$60,977.78` | `$60,581.04` | `$60,916.85` | `+0.30%` | `447` |
| `2026-11-22 19:00` | `$60,763.84` | `$60,787.63` | `$60,625.85` | `$60,737.12` | `-0.04%` | `353` |
| `2026-11-22 18:00` | `$60,827.14` | `$60,863.82` | `$60,537.43` | `$60,763.83` | `-0.10%` | `667` |
| `2026-11-22 17:00` | `$61,252.47` | `$61,267.46` | `$60,763.56` | `$60,827.15` | `-0.69%` | `568` |
| `2026-11-22 16:00` | `$60,894.90` | `$61,411.34` | `$60,888.63` | `$61,252.48` | `+0.59%` | `996` |
| `2026-11-22 15:00` | `$60,934.91` | `$61,068.00` | `$60,757.77` | `$60,894.91` | `-0.07%` | `458` |
| `2026-11-22 14:00` | `$60,739.82` | `$61,067.60` | `$60,618.00` | `$60,934.91` | `+0.32%` | `660` |
| `2026-11-22 13:00` | `$60,852.29` | `$60,937.00` | `$60,516.44` | `$60,739.82` | `-0.18%` | `566` |

### 7C. MODELED LIQUIDATION LADDER (`10x-100x`) & USD MACRO CALENDAR
**6-Tier Modeled Liquidation Ladder (`global_account_ls_ratio`):**
| Tier | Side | Level ($) | Dist% | Est Pool ($M) |
|---|---|---|---|---|
| `10x Shorts` | `UPPER` | `$67,348.61` | `+10.00%` | `$87.3M` |
| `25x Shorts` | `UPPER` | `$63,675.05` | `+4.00%` | `$116.5M` |
| `50-100x Shorts` | `UPPER` | `$61,838.27` | `+1.00%` | `$193.8M` |
| `100x Longs` | `LOWER` | `$60,613.75` | `-1.00%` | `$350.0M` |
| `25x Longs` | `LOWER` | `$58,776.97` | `-4.00%` | `$311.5M` |
| `10x Longs` | `LOWER` | `$55,103.41` | `-10.00%` | `$218.1M` |

**Upcoming USD High-Impact Macro Events (`-60m` to `+7d`):**
| Event | Time (UTC) | Countdown | Forecast | Previous |
|---|---|---|---|---|
| `Core PCE Price Index m/m` | `2026-11-25T13:30:00Z` | `in 59.9h` | `0.3%` | `0.3%` |
| `Prelim GDP q/q` | `2026-11-25T13:30:00Z` | `in 59.9h` | `3.5%` | `3.4%` |

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
