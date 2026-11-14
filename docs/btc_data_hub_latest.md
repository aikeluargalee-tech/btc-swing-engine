# TAB [D: DATA HUB] | CONSOLIDATED DATA-ONLY TELEMETRY REPORT
**Retrieval Time (UTC):** `2026-11-14 17:12:55 UTC`  |  **Retrieval Time (MYT):** `2026-11-15 01:12:55 MYT (UTC+8)`
**Spot Price (BTCUSDT):** `$65,180.69`  |  **Coverage:** `OK=61/66 | UNAVAILABLE=3 | STALE=1 | PROXY/STATIC=1`
**24H Range:** `$65,000.00 - $69,124.53`  |  **Returns (24H / 7D / 30D):** `-5.46% / -14.09% / -20.75%`
**Archive (SQLite):** `2 closed-4H snapshots (Last: 2026-11-14 16:00:00 UTC)`

## 1. PRICE, TREND & MARKET STRUCTURE
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| Binance Spot / Perp ($) | `$65,180.69 / $65,158.30` | `All Tabs` | `OK` |
| Coinbase Spot ($) | `$65,160.40` | `1,11,15,17` | `OK` |
| 1D SMA 200 / Slope | `$73,091.58 (-0.18%)` | `0,2,3,11,15,18` | `OK` |
| 1D SMA 50 / EMA 50 | `$80,624.41 / $77,697.79` | `0,2,4,15,18,20` | `OK` |
| 1D EMA 21 / 1W EMA 50 | `$75,211.70 / $78,259.11` | `3,18` | `OK` |
| 4H EMA 50 / EMA 200 | `$72,648.82 / $77,425.94` | `7,13,18,20` | `OK` |
| Grok EMA 9/21 & 1H SMA200 | `9:$66,187.31 · 21:$67,049.37 · 1H:$73,309.06` | `5,15` | `OK` |
| Daily / Weekly VWAP (Z) | `D:$66,681.50 (-1.81σ) | W:$71,611.33` | `4,11,15` | `OK` |
| RSI(14) 1D / 4H & 4H ROC12 | `1D:20.7 · 4H:19.3 · ROC:-8.32%` | `3,7,20` | `OK` |
| ADX(14) 1D/4H & ATR(14) | `ADX 1D:28.4 4H:59.7 | ATR:$2,416.71/$1,194.82/$580.77` | `0,1,2,8,13,18,20` | `OK` |
| Macro 30D VAH / POC / VAL | `$83,322.74 / $81,664.58 / $75,529.36` | `1,3,6,11,19` | `OK` |
| Structure (L20/H20, PW, Asia) | `4H:$66,613.55-$81,971.00 | PW:$73,510.00-$81,196.01 | Asia:$66,456.00-$68,446.21` | `0,8,11,19` | `OK` |

## 2. ORDER FLOW, FOOTPRINT & LIQUIDITY
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| Spot/Perp CVD (15m / 1h) | `15m:-36.0/-2.6 | 1h:-110.1/-387.6 BTC` | `1,8,15` | `OK` |
| Spot/Perp CVD (4h / 24h) | `4h:-887.7/-1915.6 | 24h:-2322.3/-4581.6 BTC` | `0,1,15,16,17` | `OK` |
| Session / UTC-Day CVD | `Sess S:+0.0 P:+0.0 | Day S:-2156.0 P:-4415.4` | `REST 15m` | `OK` |
| 24H Z-Scores (z_S / z_F / D) | `z_S:-2.01 · z_F:-0.72 · D:-1.29` | `1,19` | `OK` |
| 15m Footprint Delta / Stack | `Δ:-36.0 BTC (Prev:-73.7) · Stacks:0` | `1,11` | `OK` |
| Coinbase Premium ($ / % / Z) | `-20.3$ (-0.031%, Z=+3.44)` | `1,11,15` | `OK` |
| Cross-Exch 24H Spot Vol (BN/CB) | `BN:23,894 · CB:12,930 · Tot:36,824 BTC` | `1,11,Macro` | `OK` |
| L2 Depth ±1%/±2%, OBI & Spread | `1%:2.92x · 2%:3.12x · Spr:0.00bps · OBI:+48.9%` | `16,Macro` | `OK` |
| Tactical 7D / Session 24H VP | `7D:$76,153.33/$73,726.67/$69,060.00 | 24H:$67,646.57/$67,234.12/$65,446.82` | `1,11` | `OK` |
| VA Pos% & Dist to VAL | `-132.8% | -13.70% (-17.82 ATR)` | `1` | `OK` |
| SLSP Support / Resistance | `Sup:$64,742.09 | Res:$65,575.31` | `13` | `OK` |

## 3. DERIVATIVES, OPTIONS & LIQUIDATIONS
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| BN Open Interest (BTC / USD) | `98,135 BTC ($6.39B)` | `0,1,4,15,17` | `OK` |
| Cross-Exch Perp OI & Funding | `167,117 BTC ($10.89B) · F:+0.0047% [BN+BYB+OKX]` | `Macro,15` | `OK` |
| OI Δ% (15m/1h/4h/24h) & Quad | `+0.10%/-0.47%/-0.72%/-2.13% | LONG_LIQUIDATION_FLUSH (Price Down / OI Down)` | `1,4,8,11,12,15,17` | `OK` |
| Funding 8H% / Ann% / P90 | `+0.0036% (+3.9%/yr) · P90:39.3%` | `0,4,9,11,15,16,19,20` | `OK` |
| Perp Basis ($ / Ann %) | `-22.4$ (-0.034% | Carry:+3.50%/yr)` | `1,4` | `OK` |
| 5m Taker L/S & Top/Glb Acct | `5m:0.954 (Δ:-0.6) | Top:1.90(66L) · Glb:2.78` | `1,2,15,16` | `OK` |
| Options OI & Put/Call (Deribit) | `P/C:0.729 · TotOI:357,638 BTC` | `Macro,19` | `OK` |
| Options IV Term & Skew (Deribit) | `F:45.7% · B:41.8% · 25dSk:+8.9%` | `Macro,6,19` | `OK` |
| Vol: DVOL, RV20, GK & BBW% | `DVOL:45.6 · RV20:45.2% · GK:57.6% · BBW:77% · Sk20:-0.31` | `0,4,6,16,19` | `OK` |
| Upper / Lower Liq Magnet | `Up:$76,334.44 | Dn:$64,007.44` | `0,2,13,17` | `OK` |
| Magnet Ratios & LSCE | `Imm:1.81x · Ladder:1.79x · Pull:0.55x · LSCE:UNTESTED` | `13,17` | `OK` |
| Liquidations (1H / 24H) & Flush | `DATA UNAVAILABLE` | `0,8,12,13` | `UNAVAILABLE` |

## 4. ON-CHAIN, ETF & STABLECOIN FLOWS
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| MVRV Ratio (On-Chain / Proxy) | `1.267 [CoinMetrics 2026-11-13]` | `Macro,16` | `OK` |
| On-Chain SOPR / aSOPR | `DATA UNAVAILABLE` | `16` | `UNAVAILABLE` |
| Exchange Netflow 24H (CM) | `Net:-2,129.5 BTC (-$145.0M) | In:26,738 Out:28,868` | `Macro,16` | `OK` |
| BTC Exchange Reserves (CM) | `2,723,962 BTC (2026-11-13)` | `Macro,16` | `OK` |
| Stablecoins USDT+USDC Supply | `$244.47B (USDT:$175.25B · USDC:$69.22B)` | `Macro` | `OK` |
| Stablecoin Net Issuance (7D/30D) | `7D:-2.96B · 30D:-12.17B` | `Macro` | `OK` |
| US Spot ETF Flow (Farside 1D/3D) | `DATA UNAVAILABLE` | `2,13` | `UNAVAILABLE` |
| US ETF Tape Proxy (IBIT+FBTC) | `1DVol:$2.28B · 5D:-$6.19B [PROXY]` | `Macro,2,13` | `PROXY` |
| Power-Law Fair & ATH DD% | `$149,179.94 (-56.3%) | DD:-48.4%` | `3` | `OK` |
| MTF MACD (1D / 1H Status) | `1D=negative_slope (Macro Whipsaw Veto) | 1H=negative_slope / NEUTRAL` | `13,16,18` | `OK` |

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
| BTC-SPX Corr (20D / 60D) | `20D:+0.42 | 60D:+0.44` | `3` | `OK` |
| Fear & Greed / BTC Dom% | `F&G:13 (Extreme Fear) | Dom:58.80%` | `3,13` | `OK` |
| Manual Context Overrides | `200D_Veto=False · Filter=NONE_SIGNIFICANT` | `2,13` | `OK` |

## 6. QUANT FEATURES, FEED HEALTH & ARCHIVE
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| Rough Path Lévy (A_SP / MM) | `4H A_SP:-0.3576 | MM PriceFlow:-0.0383 · Rough:0.320` | `5,19` | `OK` |
| Hurst / Kalman Vel / FracDiff | `H:0.522 · KVel:-47.80 · d:0.20` | `5,6` | `OK` |
| Hilbert Cycle / TD9 / TellTale | `Cyc:8.0b · TD(1H/4H):6/6 · RV(15m/5m):0.56/N/A` | `5,9,13` | `OK` |
| VCR 72H & TSFM Disp% | `VCR:6.37 | Disp:1.28%` | `6` | `OK` |
| Open FVGs & Sweep FSM | `FVGs:8 | FSM:None (0/12)` | `1,8` | `OK` |
| WebSocket Feeds & Warmup | `Spot:SYNC (no tick) | Perp:SYNC (no tick) | CB:SYNC (11s ago) | Warm:YES` | `Live Feeds` | `STALE` |
| Spot Klines (1W/1D/4H/1H/15m) | `1W:100 1D:500 bars · 11-14 00:00 UTC | 4H:500 1H:720 15m:240` | `All Tabs` | `OK` |
| Perp Klines / Est. Excluded | `1D:100 · 1H:720 · 15m:240 (Excl=400)` | `1,4,11,15,19` | `OK` |
| Closed 4H Anchor (Tab 19/20) | `2026-11-14 16:00:00 UTC` | `18,19,20` | `OK` |
| B1/B2 Rec & Companion Liq | `Rec:PASS (0s delta) | Liq:N/A` | `8,13,17` | `OK` |
| Telemetry History Archive (SQLite) | `2 bars logged (Last: 2026-11-14 16:00:00 UTC)` | `DB Archive` | `OK` |

## 7. RECENT CLOSED-4H SNAPSHOT TRAJECTORY (SQLITE ARCHIVE)
| Closed 4H Bar (UTC) | Spot ($) | 24H Spot/Perp CVD | Cross-Exch Perp OI & Funding | Funding 8H% / P90 | MVRV Ratio |
|---|---|---|---|---|---|
| `2026-11-14 16:00:00 UTC` | `$65,484.09` | `24h:-2202.7/-9856.6 BTC` | `200,720 BTC ($13.14B) · F:+0.0059% [BN+BYB+OKX]` | `+0.0035% (+3.8%/yr) · P90:31.9%` | `1.267 [CoinMetrics 2026-11-13]` |
| `2026-11-14 12:00:00 UTC` | `$65,871.93` | `24h:-1587.1/-10846.6 BTC` | `201,340 BTC ($13.26B) · F:+0.0037% [BN+BYB+OKX]` | `+0.0031% (+3.4%/yr) · P90:35.6%` | `1.267 [CoinMetrics 2026-11-13]` |

## 8. METRIC FORMULA LEGEND & AI ANALYSIS PROMPT
- **Rough Path Lévy (`4H A_SP`)**: Lévy signed area over 6 closed 4H bars (`> 0`: Spot path leads price markup; `< 0`: Spot path lags price / distribution).
- **24H Z-Scores (`z_S / z_F / D`)**: 30-day rolling Z-scores of 24H Spot (`z_S`) and Perp (`z_F`) cumulative delta; `D = z_S - z_F` (`D > 0` = Spot buying divergence vs Perps).
- **Volume Profile & Structure**: `VA Pos% = (Spot - VAL) / (VAH - VAL) * 100`; `L20/H20` = 20-bar (80H) 4H range boundaries; `SLSP` = structural liquidity pool S/R.
- **Quant & Volatility**: `H` = Hurst exponent (`>0.5` trending, `<0.5` mean-reverting); `VCR 72H` = 72H Volatility Compression Ratio; `TSFM Disp%` = horizon dispersion; `LSCE` = liquidation sweep state.
- **AI Analysis Task (For Uploaded File)**: Synthesize all 6 domains + the 4H archive trajectory into: (1) Multi-Timeframe Regime & Structural Map (`1W/1D/4H/1H`), (2) Spot Absorption vs Perpetual Leverage Alignment, (3) Derivatives & Options Skew/IV Pricing, (4) On-Chain, Stablecoin & US Macro Liquidity Impulse, and (5) Concrete Upside/Downside Scenarios with Key Invalidation Levels.
- **Direct AI Instruction**: Analyze BTC using the telemetry report above. Follow the 5-part analysis framework in Section 8 and give me a clear bull vs. bear probability, key support/resistance & liquidation levels, and actionable swing / intraday setups with invalidation levels.
