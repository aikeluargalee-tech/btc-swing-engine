# TAB [D: DATA HUB] | CONSOLIDATED DATA-ONLY TELEMETRY REPORT
**Retrieval Time (UTC):** `2026-11-21 10:59:16 UTC`  |  **Retrieval Time (SGT):** `2026-11-21 18:59:16 SGT (UTC+8)`
**Spot Price (BTCUSDT):** `$57,962.13`  |  **Coverage:** `OK=65/71 | UNAVAILABLE=4 | STALE=1 (Genuine=0, Expected_Headless_WS_Offline=1) | PROXY/STATIC=1`
**24H Range:** `$55,130.00 - $62,179.45`  |  **Returns (24H / 7D / 30D):** `-6.59% / -9.65% / -28.81%`
**Archive (SQLite):** `35 closed-4H snapshots (Last: 2026-11-21 08:00:00 UTC)`

## 0. BIDIRECTIONAL REGIME ROUTER (GATE 0 — DUAL-INVENTORY SPOT WORKSTATION)
| Router Field | Value | Rule / Threshold |
|---|---|---|
| Latest Closed 1D Candle Close | `$58,951.51 (1D bar 2026-11-20 · closed 2026-11-21 00:00 UTC)` | `Same closed Binance Spot 1D series only (live candle excluded)` |
| Current 1D SMA 200 | `$72,589.19` | `200-bar SMA of same closed Binance Spot 1D series` |
| Distance vs 1D SMA 200 | `-18.79% (-$13,637.68)` | `(Closed 1D Close - 1D SMA 200) / 1D SMA 200` |
| 1D SMA 200 Position | `BELOW` | `BELOW if Closed 1D Close < 1D SMA 200 else ABOVE` |
| Closed 4H Market Structure (`7A`) | `DOWNTREND (LH/LL)` | `UPTREND / DOWNTREND / MIXED (500 closed 4H bars)` |
| 4H Downside BOS Status (`7A`) | `YES (BOS Down < $62,062.97 (11-19 20:00))` | `YES if latest closed 4H BOS is BOS Down else NO` |
| Upcoming Macro Event Caution (`7C`) | `CLEAR (>24h / NONE)` | `CAUTION (<24h USD high-impact event) else CLEAR` |
| Timestamp & Candle Closed Status | `2026-11-21 10:59:16 UTC | 2026-11-21 18:59:16 SGT (UTC+8) · Closed-Candle Inputs Only` | `Strict closed-bar verification gate` |

**BIDIRECTIONAL REGIME ROUTER STATUS:**
- **Active Route:** `MACRO_DOWNTREND_DISTRIBUTION`
- **Primary Active Rail:** `RAIL A — BTC -> USDT CONVERSION (DEFENSIVE / SELL RALLIES)`
- **Active BTC Inventory (`Rail A: BTC -> USDT`):** `ACTIVE (RAIL A) — CONVERT INTO OVERHEAD RESISTANCE`
- **Active USDT Inventory (`Rail B: USDT -> BTC`):** `RESTRICTED (RAIL B) — HOLD PENDING VALIDATED SWEEP & RECLAIM`
- **Condition A (`1D Close < 1D SMA 200`):** `YES`  |  **Condition B (`4H Downside Structure / BOS`):** `YES`

## 1. PRICE, TREND & MARKET STRUCTURE
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| Binance Spot / Perp ($) | `$57,962.13 / $57,937.80` | `All Tabs` | `OK` |
| Coinbase Spot ($) | `$57,865.97` | `1,11,15,17` | `OK` |
| 1D SMA 200 / Slope | `$72,589.19 (-0.53%)` | `0,2,3,11,15,18` | `OK` |
| 1D SMA 50 / EMA 50 | `$77,717.72 / $73,891.02` | `0,2,4,15,18,20` | `OK` |
| 1D EMA 21 / 1W EMA 50 | `$68,702.25 / $78,318.53` | `3,18` | `OK` |
| 4H EMA 50 / EMA 200 | `$64,521.73 / $72,693.71` | `7,13,18,20` | `OK` |
| Grok EMA 9/21 & 1H SMA200 | `9:$57,873.79 · 21:$58,616.81 · 1H:$64,195.75` | `5,15` | `OK` |
| Daily / Weekly VWAP (Z) | `D:$57,252.81 (+0.66σ) | W:$62,493.10` | `4,11,15` | `OK` |
| RSI(14) 1D / 4H & 4H ROC12 | `1D:16.5 · 4H:28.6 · ROC:-9.01%` | `3,7,20` | `OK` |
| ADX(14) 1D/4H & ATR(14) 1D/4H/1H | `ADX 1D:46.9 4H:57.3 | ATR:$2,800.83/$1,449.91/$891.96` | `0,1,2,8,13,18,20` | `OK` |
| 4H ATR(14)% Pctile & RelVol(20) | `ATR%:2.65% (100th pct/120b) · RelVol:4.01x` | `0,1,2,20` | `OK` |
| Macro 30D VAH / POC / VAL | `BIMODAL (Peaks: $80,402.15 & $64,677.26 — single VA UNAVAILABLE)` | `1,3,6,11,19` | `UNAVAILABLE` |
| Structure (L20/H20, PW, Asia) | `4H:$57,778.35-$81,196.01 | PW:$62,006.00-$75,599.22 | Asia:$55,130.00-$59,248.06` | `0,8,11,19` | `OK` |

## 2. ORDER FLOW, FOOTPRINT & LIQUIDITY
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| Spot/Perp CVD (15m / 1h) | `15m:+71.7/+31.5 | 1h:-126.3/+108.2 BTC` | `1,8,15` | `OK` |
| Spot/Perp CVD (4h / 24h) | `4h:-971.0/+1226.7 | 24h:-8311.2/-8831.5 BTC` | `0,1,15,16,17` | `OK` |
| Spot CVD Slopes (7D / 14D) | `7D:-6,412.9 BTC | 14D:-5,189.7 BTC` | `17` | `OK` |
| Session / UTC-Day CVD | `Sess S:+0.0 P:+0.0 | Day S:-4220.6 P:-2472.7` | `REST 15m` | `OK` |
| 24H Z-Scores (z_S / z_F / D) | `z_S:-4.22 · z_F:-2.06 · D:-2.16` | `1,19` | `OK` |
| 15m Footprint Delta / Stack | `Δ:+71.7 BTC (Prev:+0.0) · Stacks:0` | `1,11` | `OK` |
| Coinbase Premium ($ / % / Z) | `-96.2$ (-0.166%, Z=+0.85)` | `1,11,15` | `OK` |
| Cross-Exch 24H Spot Vol (BN/CB) | `BN:60,438 · CB:29,734 · Tot:90,172 BTC` | `1,11,Macro` | `OK` |
| L2 Depth ±1%/±2%, OBI & Spread | `1%:0.56x · 2%:0.56x · Spr:0.0017bps · OBI:-27.8%` | `16,Macro` | `OK` |
| Tactical 7D / Session 24H VP | `7D:$65,988.80/$64,867.24/$61,400.58 | 24H:$59,535.91/$59,065.94/$56,363.65` | `1,11` | `OK` |
| 30D VA Pos% & Dist to VAL | `BIMODAL — DATA UNAVAILABLE` | `1` | `UNAVAILABLE` |
| SLSP Support / Resistance | `Sup:$57,957.60 | Res:$59,130.91` | `13` | `OK` |

## 3. DERIVATIVES, OPTIONS & LIQUIDATIONS
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| BN Open Interest (BTC / USD) | `93,385 BTC ($5.41B)` | `0,1,4,15,17` | `OK` |
| Cross-Exch Perp OI & Funding | `160,891 BTC ($9.32B) · F:-0.0013% [BN+BYB+OKX 3/3]` | `Macro,15` | `OK` |
| Hyperliquid Perp OI & Funding | `36,654 BTC ($2.12B) · F:+0.0069% [HL DEX]` | `Macro,15` | `OK` |
| OI Δ% (15m/1h/4h/24h) & Quad | `-0.01%/+0.25%/+2.24%/-1.12% | NEUTRAL_CHURN` | `1,4,8,11,12,15,17` | `OK` |
| Funding 8H% / Ann% / 90D Pct | `+0.0004% (+0.5%/yr) · 90D Pct:1.1%` | `0,4,9,11,15,16,19,20` | `OK` |
| Perp Basis ($ / Ann %) | `-24.3$ (-0.042% | Carry:-0.00%/yr)` | `1,4` | `OK` |
| 5m Taker L/S & Top/Glb Acct | `5m:0.550 (Δ:-16.4) | Top:1.77(64L) · Glb:2.24` | `1,2,15,16` | `OK` |
| Options OI & Put/Call (Deribit) | `P/C:0.832 · TotOI:398,745 BTC` | `Macro,19` | `OK` |
| Options IV Term & Skew (Deribit) | `F:55.9% · B:48.1% · 25dSk:+8.6%` | `Macro,6,19` | `OK` |
| Vol: DVOL, RV20, GK & BBW% | `DVOL:58.9 · RV20:48.5% · GK:79.9% · BBW:94% · Sk20:-0.09` | `0,4,6,16,19` | `OK` |
| Upper / Lower Liq Magnet | `Up:$76,334.44 | Dn:$56,918.81` | `0,2,13,17` | `OK` |
| Magnet Ratios & LSCE | `Imm:1.81x · Ladder:1.39x · Pull:0.55x · LSCE:UNTESTED` | `13,17` | `OK` |
| Modeled Liq Ladder (10x-100x) | `Up[10x:$63,758.34($80M) / 25x:$60,280.62($107M) / 50-100x:$58,541.75($194M)] | Dn[100x:$57,382.51($350M) / 25x:$55,643.64($299M) / 10x:$52,165.92($210M)] [Modeled] (L/S:global_account_ls_ratio)` | `17` | `OK` |
| Liquidations (1H / 24H) & Flush | `DATA UNAVAILABLE` | `0,8,12,13` | `UNAVAILABLE` |

## 4. ON-CHAIN, ETF & STABLECOIN FLOWS
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| MVRV Ratio (On-Chain / Proxy) | `1.105 [CoinMetrics 2026-11-20]` | `Macro,16` | `OK` |
| On-Chain SOPR / aSOPR | `DATA UNAVAILABLE` | `16` | `UNAVAILABLE` |
| Exchange Netflow 24H (CM) | `Net:-515.4 BTC (-$30.3M) | In:41,306 Out:41,821` | `Macro,16` | `OK` |
| BTC Exchange Reserves (CM) | `2,709,906 BTC (2026-11-20)` | `Macro,16` | `OK` |
| Stablecoins USDT+USDC Supply | `$243.12B (USDT:$174.44B · USDC:$68.68B)` | `Macro` | `OK` |
| Stablecoin Net Issuance (7D/30D) | `7D:-1.14B · 30D:-12.00B` | `Macro` | `OK` |
| US Spot ETF Flow (Farside 1D/3D) | `1D:-$124.5M | 3D:-$1.01B | 5D:-$1.25B` | `2,13` | `OK` |
| US ETF Tape Proxy (IBIT+FBTC) | `1DVol:$4.02B · 5D:-$13.65B [PROXY]` | `Macro,2,13` | `PROXY` |
| Power-Law Fair & ATH DD% | `$150,057.43 (-61.4%) | DD:-54.1%` | `3` | `OK` |
| MTF MACD (1D / 1H Status) | `1D=negative_slope (Macro Whipsaw Veto) | 1H=positive_slope CROSS` | `13,16,18` | `OK` |

## 5. MACRO, CREDIT & US LIQUIDITY
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| US SOFR Rate & Vol (NY Fed) | `3.91% (Vol:$3,161B)` | `Macro` | `OK` |
| Fed ON RRP Balance (NY Fed) | `$0.40B` | `Macro` | `OK` |
| Credit Spread HYG/LQD & 5D% | `0.7361 (-1.63% 5D)` | `Macro,3` | `OK` |
| DXY / US 10Y (^TNX) | `103.84 (RISING (+0.40 over 5d)) | 10Y:4.91%` | `3,13` | `OK` |
| TIPS Real (DFII10) / BEI | `Real:+2.77% | BEI:2.14%` | `3,13` | `OK` |
| S&P 500 / Nasdaq (1D%) | `SPX:6,910 (-3.70%) | NDX:22,618` | `3,13` | `OK` |
| VIX / Brent Crude (BZ=F) | `VIX:35.89 | Brent:$89.95` | `3,13` | `OK` |
| BTC-SPX Corr (20D / 60D) | `20D:+0.74 | 60D:+0.74` | `3` | `OK` |
| Fear & Greed / BTC Dom% | `F&G:12 (Extreme Fear) | Dom:57.50%` | `3,13` | `OK` |
| USD Macro Calendar (High) | `NONE (next 7d)` | `Macro` | `OK` |
| Manual Context Overrides | `Legacy_200D_Veto_Override: IGNORED (Tab1_Flag=True) · Filter=NONE_SIGNIFICANT` | `2,13` | `OK` |

## 6. QUANT FEATURES, FEED HEALTH & ARCHIVE
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| Rough Path Lévy (A_SP / MM) | `4H A_SP:-2.1229 | MM PriceFlow:-1.4079 · Rough:0.540` | `5,19` | `OK` |
| Hurst / Kalman Vel / FracDiff | `H:0.602 · KVel:-53.70 · d:0.15` | `5,6` | `OK` |
| Hilbert Cycle / TD9 / TellTale | `Cyc:19.0b · TD(1H/4H):1/9 · RV(15m/5m):0.37/N/A` | `5,9,13` | `OK` |
| VCR 72H & TSFM Disp% | `VCR:11.06 | Disp:1.28%` | `6` | `OK` |
| Open FVGs & Sweep FSM | `FVGs:8 | FSM:None (0/12)` | `1,8` | `OK` |
| WebSocket Feeds & Warmup | `Spot:SYNC (no tick) | Perp:SYNC (no tick) | CB:SYNC (11s ago) | Warm:YES` | `Live Feeds` | `STALE` |
| Spot Klines (1W/1D/4H/1H/15m) | `1W:100 1D:500 bars · 11-21 00:00 UTC | 4H:500 1H:720 15m:240` | `All Tabs` | `OK` |
| Perp Klines / Est. Excluded | `1D:101 · 1H:720 · 15m:240 (Excl=399)` | `1,4,11,15,19` | `OK` |
| Closed 4H Anchor (Tab 19/20) | `2026-11-21 08:00:00 UTC` | `18,19,20` | `OK` |
| B1/B2 Rec & Companion Liq | `Rec:PASS (0s delta) | Liq:N/A` | `8,13,17` | `OK` |
| Telemetry History Archive (SQLite) | `35 bars logged (Last: 2026-11-21 08:00:00 UTC)` | `DB Archive` | `OK` |

## 7. RECENT CLOSED-4H SNAPSHOT TRAJECTORY (SQLITE ARCHIVE)
| Closed 4H Bar (UTC) | Spot ($) | 24H Spot/Perp CVD | Cross-Exch Perp OI & Funding | Funding 8H% / 90D Pct | MVRV Ratio |
|---|---|---|---|---|---|
| `2026-11-21 08:00:00 UTC` | `$57,964.51` | `24h:-7565.0/-9052.8 BTC` | `160,812 BTC ($9.30B) · F:-0.0005% [BN+BYB+OKX 3/3]` | `+0.0022% (+2.4%/yr) · 90D Pct:1.1%` | `1.105 [CoinMetrics 2026-11-20]` |
| `2026-11-21 04:00:00 UTC` | `$55,726.38` | `24h:-6604.6/-9343.4 BTC` | `163,846 BTC ($9.13B) · F:-0.0070% [BN+BYB+OKX 3/3]` | `-0.0077% (-8.5%/yr) · 90D Pct:0.4%` | `1.105 [CoinMetrics 2026-11-20]` |
| `2026-11-21 00:00:00 UTC` | `$58,983.67` | `24h:-3894.9/-8000.4 BTC` | `163,780 BTC ($9.64B) · F:-0.0056% [BN+BYB+OKX 3/3]` | `-0.0060% (-6.6%/yr) · 90D Pct:0.4%` | `1.159 [CoinMetrics 2026-11-19]` |
| `2026-11-20 16:00:00 UTC` | `$59,168.10` | `24h:-2398.7/-4279.0 BTC` | `166,370 BTC ($9.91B) · F:+0.0009% [BN+BYB+OKX 3/3]` | `+0.0014% (+1.6%/yr) · 90D Pct:35.2%` | `1.159 [CoinMetrics 2026-11-19]` |
| `2026-11-20 12:00:00 UTC` | `$61,620.00` | `24h:-936.1/-3399.0 BTC` | `166,196 BTC ($10.22B) · F:+0.0019% [BN+BYB+OKX 3/3]` | `+0.0024% (+2.7%/yr) · 90D Pct:1.1%` | `1.159 [CoinMetrics 2026-11-19]` |
| `2026-11-20 08:00:00 UTC` | `$61,950.22` | `24h:-1167.7/-3849.5 BTC` | `167,102 BTC ($10.33B) · F:-0.0016% [BN+BYB+OKX 3/3]` | `+0.0006% (+0.7%/yr) · 90D Pct:1.1%` | `1.159 [CoinMetrics 2026-11-19]` |

### 7A. 500-BAR MARKET STRUCTURE & HISTORICAL S/R ZONES (`1D / 4H / 1H`)
| TF (Bars) | Swing Structure | Last Swing Pivots | Latest BOS | Resistance Zones (Above Spot) | Support Zones (Below Spot) |
|---|---|---|---|---|---|
| `1D (499)` | `DOWNTREND (LH/LL)` | `SH:$81,196.01 (11-04) · SL:$79,800.00 (10-15)` | `BOS Down < $79,800.00 (10-29)` | `$59,130.91 (1x), $60,000.00 (1x), $62,440.17 (3x)` | `None below in lookback` |
| `4H (499)` | `DOWNTREND (LH/LL)` | `SH:$65,696.16 (11-16 12:00) · SL:$62,062.97 (11-18 20:00)` | `BOS Down < $62,062.97 (11-19 20:00)` | `$62,034.49 (2x), $63,620.51 (2x), $65,696.16 (1x)` | `None below in lookback` |
| `1H (500)` | `DOWNTREND (LH/LL)` | `SH:$62,341.94 (11-20 10:00) · SL:$57,778.35 (11-20 19:00)` | `BOS Down < $57,778.35 (11-21 03:00)` | `$61,290.58 (1x), $62,265.96 (5x), $63,894.86 (4x)` | `$57,778.35 (1x)` |

### 7B. RECENT CLOSED KLINES — OHLCV PRICE ACTION (`1D`×7, `4H`×12, `1H`×12)
**1D Closed Candles (Last 7 of 499 available, Newest First):**
| Open Time (UTC) | Open | High | Low | Close | Chg% | Vol (BTC) |
|---|---|---|---|---|---|---|
| `2026-11-20` | `$61,986.73` | `$62,639.52` | `$57,778.35` | `$58,951.51` | `-4.90%` | `38,126` |
| `2026-11-19` | `$63,068.21` | `$64,080.80` | `$61,428.26` | `$61,986.73` | `-1.71%` | `19,880` |
| `2026-11-18` | `$64,947.36` | `$65,002.00` | `$62,062.97` | `$63,068.22` | `-2.89%` | `18,700` |
| `2026-11-17` | `$64,882.88` | `$65,447.00` | `$63,336.00` | `$64,947.35` | `+0.10%` | `28,317` |
| `2026-11-16` | `$65,351.05` | `$65,696.16` | `$63,905.01` | `$64,882.87` | `-0.72%` | `21,929` |
| `2026-11-15` | `$64,150.01` | `$66,132.01` | `$62,006.00` | `$65,351.05` | `+1.87%` | `29,231` |
| `2026-11-14` | `$68,314.01` | `$68,446.21` | `$63,320.00` | `$64,150.00` | `-6.10%` | `32,675` |

**4H Closed Candles (Last 12 of 499 available, Newest First):**
| Open Time (UTC) | Open | High | Low | Close | Chg% | Vol (BTC) |
|---|---|---|---|---|---|---|
| `2026-11-21 04:00` | `$56,740.43` | `$58,672.05` | `$55,130.00` | `$57,997.00` | `+2.21%` | `18,082` |
| `2026-11-21 00:00` | `$58,951.51` | `$59,248.06` | `$56,400.00` | `$56,740.43` | `-3.75%` | `9,620` |
| `2026-11-20 20:00` | `$58,558.66` | `$59,410.63` | `$58,200.00` | `$58,951.51` | `+0.67%` | `6,035` |
| `2026-11-20 16:00` | `$59,475.47` | `$60,025.24` | `$57,778.35` | `$58,558.66` | `-1.54%` | `12,721` |
| `2026-11-20 12:00` | `$61,808.00` | `$62,179.45` | `$59,388.00` | `$59,475.47` | `-3.77%` | `8,714` |
| `2026-11-20 08:00` | `$61,858.95` | `$62,341.94` | `$61,552.00` | `$61,808.00` | `-0.08%` | `2,563` |
| `2026-11-20 04:00` | `$62,156.32` | `$62,156.32` | `$61,389.05` | `$61,858.96` | `-0.48%` | `3,567` |
| `2026-11-20 00:00` | `$61,986.73` | `$62,639.52` | `$61,290.58` | `$62,156.32` | `+0.27%` | `4,526` |
| `2026-11-19 20:00` | `$62,372.01` | `$62,467.25` | `$61,428.26` | `$61,986.73` | `-0.62%` | `5,049` |
| `2026-11-19 16:00` | `$63,103.30` | `$63,408.62` | `$62,227.80` | `$62,372.01` | `-1.16%` | `4,149` |
| `2026-11-19 12:00` | `$63,947.59` | `$64,080.00` | `$62,780.07` | `$63,103.30` | `-1.32%` | `3,555` |
| `2026-11-19 08:00` | `$63,737.62` | `$64,080.80` | `$63,565.52` | `$63,947.59` | `+0.33%` | `2,108` |

**1H Closed Candles (Last 12 of 719 available, Newest First):**
| Open Time (UTC) | Open | High | Low | Close | Chg% | Vol (BTC) |
|---|---|---|---|---|---|---|
| `2026-11-21 09:00` | `$57,805.51` | `$58,128.01` | `$57,769.25` | `$58,029.60` | `+0.39%` | `1,326` |
| `2026-11-21 08:00` | `$57,997.00` | `$58,142.00` | `$57,381.45` | `$57,805.52` | `-0.33%` | `2,176` |
| `2026-11-21 07:00` | `$58,066.71` | `$58,672.05` | `$57,736.86` | `$57,997.00` | `-0.12%` | `3,960` |
| `2026-11-21 06:00` | `$55,792.83` | `$58,115.02` | `$55,130.00` | `$58,066.71` | `+4.08%` | `5,254` |
| `2026-11-21 05:00` | `$56,300.89` | `$56,504.01` | `$55,716.48` | `$55,792.83` | `-0.90%` | `2,751` |
| `2026-11-21 04:00` | `$56,740.43` | `$56,842.02` | `$55,555.55` | `$56,300.89` | `-0.77%` | `6,118` |
| `2026-11-21 03:00` | `$58,589.23` | `$58,589.23` | `$56,400.00` | `$56,740.43` | `-3.16%` | `5,598` |
| `2026-11-21 02:00` | `$59,030.84` | `$59,081.17` | `$58,578.45` | `$58,589.22` | `-0.75%` | `1,489` |
| `2026-11-21 01:00` | `$59,036.77` | `$59,248.06` | `$58,910.10` | `$59,030.85` | `-0.01%` | `1,140` |
| `2026-11-21 00:00` | `$58,951.51` | `$59,164.35` | `$58,880.00` | `$59,036.76` | `+0.14%` | `1,393` |
| `2026-11-20 23:00` | `$59,170.55` | `$59,294.00` | `$58,858.00` | `$58,951.51` | `-0.37%` | `774` |
| `2026-11-20 22:00` | `$59,012.81` | `$59,318.66` | `$58,908.00` | `$59,170.56` | `+0.27%` | `1,388` |

### 7C. MODELED LIQUIDATION LADDER (`10x-100x`) & USD MACRO CALENDAR
**6-Tier Modeled Liquidation Ladder (`global_account_ls_ratio`):**
| Tier | Side | Level ($) | Dist% | Est Pool ($M) |
|---|---|---|---|---|
| `10x Shorts` | `UPPER` | `$63,758.34` | `+10.00%` | `$80.2M` |
| `25x Shorts` | `UPPER` | `$60,280.62` | `+4.00%` | `$106.9M` |
| `50-100x Shorts` | `UPPER` | `$58,541.75` | `+1.00%` | `$193.8M` |
| `100x Longs` | `LOWER` | `$57,382.51` | `-1.00%` | `$350.0M` |
| `25x Longs` | `LOWER` | `$55,643.64` | `-4.00%` | `$299.4M` |
| `10x Longs` | `LOWER` | `$52,165.92` | `-10.00%` | `$209.6M` |

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
