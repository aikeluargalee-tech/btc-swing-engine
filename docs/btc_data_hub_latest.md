# TAB [D: DATA HUB] | CONSOLIDATED DATA-ONLY TELEMETRY REPORT
**Retrieval Time (UTC):** `2026-11-14 17:31:56 UTC`  |  **Retrieval Time (MYT):** `2026-11-15 01:31:56 MYT (UTC+8)`
**Spot Price (BTCUSDT):** `$65,625.21`  |  **Coverage:** `OK=61/66 | UNAVAILABLE=3 | STALE=1 | PROXY/STATIC=1`
**24H Range:** `$65,000.00 - $69,124.53`  |  **Returns (24H / 7D / 30D):** `-4.81% / -13.50% / -20.21%`
**Archive (SQLite):** `2 closed-4H snapshots (Last: 2026-11-14 16:00:00 UTC)`

## 1. PRICE, TREND & MARKET STRUCTURE
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| Binance Spot / Perp ($) | `$65,625.21 / $65,593.30` | `All Tabs` | `OK` |
| Coinbase Spot ($) | `$65,580.83` | `1,11,15,17` | `OK` |
| 1D SMA 200 / Slope | `$73,091.58 (-0.18%)` | `0,2,3,11,15,18` | `OK` |
| 1D SMA 50 / EMA 50 | `$80,624.41 / $77,715.22` | `0,2,4,15,18,20` | `OK` |
| 1D EMA 21 / 1W EMA 50 | `$75,252.11 / $78,276.54` | `3,18` | `OK` |
| 4H EMA 50 / EMA 200 | `$72,648.82 / $77,425.94` | `7,13,18,20` | `OK` |
| Grok EMA 9/21 & 1H SMA200 | `9:$66,276.22 · 21:$67,089.78 · 1H:$73,311.28` | `5,15` | `OK` |
| Daily / Weekly VWAP (Z) | `D:$66,659.97 (-1.24σ) | W:$71,593.41` | `4,11,15` | `OK` |
| RSI(14) 1D / 4H & 4H ROC12 | `1D:21.1 · 4H:19.3 · ROC:-8.32%` | `3,7,20` | `OK` |
| ADX(14) 1D/4H & ATR(14) | `ADX 1D:28.4 4H:59.7 | ATR:$2,416.71/$1,194.99/$609.41` | `0,1,2,8,13,18,20` | `OK` |
| Macro 30D VAH / POC / VAL | `$83,322.74 / $81,664.58 / $75,529.36` | `1,3,6,11,19` | `OK` |
| Structure (L20/H20, PW, Asia) | `4H:$66,613.55-$81,971.00 | PW:$73,510.00-$81,196.01 | Asia:$66,456.00-$68,446.21` | `0,8,11,19` | `OK` |

## 2. ORDER FLOW, FOOTPRINT & LIQUIDITY
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| Spot/Perp CVD (15m / 1h) | `15m:+3.0/+150.2 | 1h:-123.6/+469.3 BTC` | `1,8,15` | `OK` |
| Spot/Perp CVD (4h / 24h) | `4h:-901.6/-932.9 | 24h:-2336.1/-3598.8 BTC` | `0,1,15,16,17` | `OK` |
| Session / UTC-Day CVD | `Sess S:+0.0 P:+0.0 | Day S:-2169.9 P:-3346.8` | `REST 15m` | `OK` |
| 24H Z-Scores (z_S / z_F / D) | `z_S:-2.01 · z_F:-0.72 · D:-1.29` | `1,19` | `OK` |
| 15m Footprint Delta / Stack | `Δ:+3.0 BTC (Prev:-5.8) · Stacks:0` | `1,11` | `OK` |
| Coinbase Premium ($ / % / Z) | `-44.4$ (-0.068%, Z=+1.25)` | `1,11,15` | `OK` |
| Cross-Exch 24H Spot Vol (BN/CB) | `BN:24,273 · CB:13,158 · Tot:37,432 BTC` | `1,11,Macro` | `OK` |
| L2 Depth ±1%/±2%, OBI & Spread | `1%:2.47x · 2%:1.45x · Spr:0.00bps · OBI:+42.3%` | `16,Macro` | `OK` |
| Tactical 7D / Session 24H VP | `7D:$76,153.33/$73,726.67/$69,060.00 | 24H:$67,646.57/$67,234.12/$65,446.82` | `1,11` | `OK` |
| VA Pos% & Dist to VAL | `-127.1% | -13.11% (-16.25 ATR)` | `1` | `OK` |
| SLSP Support / Resistance | `Sup:$65,575.31 | Res:$67,055.15` | `13` | `OK` |

## 3. DERIVATIVES, OPTIONS & LIQUIDATIONS
| Metric | Value | Source Tabs | Status |
|---|---|---|---|
| BN Open Interest (BTC / USD) | `97,831 BTC ($6.37B)` | `0,1,4,15,17` | `OK` |
| Cross-Exch Perp OI & Funding | `166,965 BTC ($10.89B) · F:+0.0049% [BN+BYB+OKX]` | `Macro,15` | `OK` |
| OI Δ% (15m/1h/4h/24h) & Quad | `+0.15%/+0.74%/+0.16%/-0.93% | LEVERAGED_LONG_EXPANSION (Price Up / OI Up)` | `1,4,8,11,12,15,17` | `OK` |
| Funding 8H% / Ann% / P90 | `+0.0040% (+4.3%/yr) · P90:39.3%` | `0,4,9,11,15,16,19,20` | `OK` |
| Perp Basis ($ / Ann %) | `-31.9$ (-0.049% | Carry:+3.80%/yr)` | `1,4` | `OK` |
| 5m Taker L/S & Top/Glb Acct | `5m:2.491 (Δ:+22.1) | Top:1.90(66L) · Glb:2.83` | `1,2,15,16` | `OK` |
| Options OI & Put/Call (Deribit) | `P/C:0.730 · TotOI:357,797 BTC` | `Macro,19` | `OK` |
| Options IV Term & Skew (Deribit) | `F:44.3% · B:41.5% · 25dSk:+9.9%` | `Macro,6,19` | `OK` |
| Vol: DVOL, RV20, GK & BBW% | `DVOL:44.9 · RV20:44.3% · GK:57.9% · BBW:77% · Sk20:-0.28` | `0,4,6,16,19` | `OK` |
| Upper / Lower Liq Magnet | `Up:$76,334.44 | Dn:$64,443.96` | `0,2,13,17` | `OK` |
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
| Power-Law Fair & ATH DD% | `$149,181.65 (-56.0%) | DD:-48.0%` | `3` | `OK` |
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
| Rough Path Lévy (A_SP / MM) | `4H A_SP:-0.3576 | MM PriceFlow:-0.0396 · Rough:0.330` | `5,19` | `OK` |
| Hurst / Kalman Vel / FracDiff | `H:0.616 · KVel:-46.60 · d:0.20` | `5,6` | `OK` |
| Hilbert Cycle / TD9 / TellTale | `Cyc:8.0b · TD(1H/4H):6/6 · RV(15m/5m):0.04/N/A` | `5,9,13` | `OK` |
| VCR 72H & TSFM Disp% | `VCR:8.40 | Disp:1.28%` | `6` | `OK` |
| Open FVGs & Sweep FSM | `FVGs:10 | FSM:None (0/12)` | `1,8` | `OK` |
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
