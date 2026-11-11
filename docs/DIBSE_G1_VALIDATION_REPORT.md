# DIBSE G1 Historical Validation & Ablation Report

**Generated:** 2026-11-11 16:58:42 UTC  
**Evaluation Horizon:** `2020-01-01 00:00 UTC` -> `2026-11-11 16:00 UTC`  
**Starting Active Sandbox:** \$20,000.00 (\$10,000.00 USDT Sleeve A + \$10,000.00 BTC Sleeve B; untouched 80% Core excluded)  
**Methodology:** Strictly closed 4H Binance Spot & Perp klines, causal 8H funding (`<= bar_close`), frozen G0 thresholds (no tuning), daily 00:00 UTC return resampling (`sqrt(365)` annualization), BAILEY-LdP DSR across `M = 10` active variants.

---

## 1. Data Integrity & Coverage Audit

- **Aligned Spot + Perp Closed 4H Bars:** `15,725` (`2019-09-08 16:00 UTC` -> `2026-11-11 16:00 UTC`)
- **Full Spot Warmup Archive (for 200d SMA):** `16,322` bars (from `2019-06-01 00:00 UTC`)
- **Causal 8H Funding Prints:** `7,859` prints
- **Timestamp Mismatches Dropped:** Spot-only=`597`, Perp-only=`1`
- **Exchange Maintenance Gaps (>4h step):** `1` gap events (`1` missing 4H bars)

## 2. Headline Performance: DIBSE vs. Four Apples-to-Apples Benchmarks (10 bps/side)

| Strategy / Benchmark | Cost (bps) | Final Eq | Tot Ret | CAGR | Ann Vol | Max DD | Sharpe | Sortino | Calmar | t-stat | PSR(0) | DSR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `DIBSE_FULL_4GATE` | 10 | \$55,989 | +180.4% | +16.20% | 17.5% | -31.6% | 0.95 | 1.34 | 0.51 | 2.49 | 98.7% | 93.3% |
| `BENCH_BH_100_BTC` | 10 | \$204,822 | +927.5% | +40.40% | 59.9% | -76.6% | 0.87 | 1.27 | 0.53 | 2.29 | 98.8% | 92.7% |
| `BENCH_50_50_HOLD` | 10 | \$112,411 | +463.0% | +28.62% | 47.6% | -69.2% | 0.77 | 1.13 | 0.41 | 2.01 | 97.8% | 88.5% |
| `BENCH_50_50_REBAL_WK` | 10 | \$86,788 | +334.7% | +23.86% | 29.8% | -48.7% | 0.87 | 1.27 | 0.49 | 2.27 | 98.7% | 92.5% |
| `BENCH_50_50_REBAL_5PCT` | 10 | \$89,715 | +349.3% | +24.46% | 30.1% | -48.9% | 0.88 | 1.28 | 0.50 | 2.30 | 98.8% | 92.9% |
| `BENCH_DETZEL_200D_SMA` | 10 | \$135,207 | +576.0% | +32.09% | 42.7% | -64.1% | 0.86 | 1.32 | 0.50 | 2.27 | 98.9% | 92.9% |

## 3. Dual-Sleeve Cycle & Inventory Mechanics Diagnostics (Full 4-Gate, 10 bps)

| Sleeve | Triggers | Completed Cycles | Open at End | % Time Exposed / Parked | Max Stuck Wait | Sleeve Ending USD | Sleeve Return |
|---|---:|---:|---:|---:|---:|---:|---:|
| **Loop A (`USDT -> BTC -> USDT`)** | 14 | 14 | NO (USDT) | 33.0% holding BTC | 622.3 days | \$34,567.80 | +245.68% |
| **Loop B (`BTC -> USDT -> BTC`)** | 2 | 1 | YES (USDT) | 87.6% parked USDT | 2194.7 days | \$21,421.65 | +114.22% |

- **Loop B Satoshi Stack Audit:** Initial BTC=`1.38408 BTC` -> Ending BTC-Equivalent=`0.28951 BTC` (`-79.08%` vs passively holding Sleeve B's initial BTC!)
- **Total Trading Fees Paid (10 bps/side):** \$691.03 (`34.55x` sandbox notional turnover)

## 4. Gate Ablation & Sleeve Isolation Matrix (10 bps/side, Bar-Close Exits)

| Strategy / Benchmark | Cost (bps) | Final Eq | Tot Ret | CAGR | Ann Vol | Max DD | Sharpe | Sortino | Calmar | t-stat | PSR(0) | DSR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `DIBSE_FULL_4GATE` | 10 | \$55,989 | +180.4% | +16.20% | 17.5% | -31.6% | 0.95 | 1.34 | 0.51 | 2.49 | 98.7% | 93.3% |
| `DIBSE_LOOP_A_ONLY` | 10 | \$136,979 | +586.0% | +32.38% | 49.6% | -74.4% | 0.81 | 1.20 | 0.44 | 2.13 | 98.3% | 90.7% |
| `DIBSE_LOOP_B_ONLY` | 10 | \$31,422 | +57.4% | +6.83% | 14.4% | -31.6% | 0.53 | 0.72 | 0.22 | 1.40 | 89.5% | 70.2% |
| `ABL_G3_ONLY` | 10 | \$40,465 | +103.2% | +10.88% | 33.2% | -48.9% | 0.48 | 0.68 | 0.22 | 1.26 | 89.2% | 67.2% |
| `ABL_G3_G1` | 10 | \$44,576 | +123.3% | +12.41% | 34.4% | -52.4% | 0.52 | 0.73 | 0.24 | 1.35 | 90.7% | 70.3% |
| `ABL_G3_G2` | 10 | \$37,412 | +87.4% | +9.58% | 20.7% | -32.1% | 0.55 | 0.81 | 0.30 | 1.43 | 92.3% | 73.3% |
| `ABL_G3_G4` | 10 | \$51,237 | +157.3% | +14.75% | 31.9% | -45.3% | 0.59 | 0.86 | 0.33 | 1.56 | 93.6% | 76.8% |

| Variant | Loop A Ent / Done | Loop B Sell / Done | Loop A Time in BTC | Loop B Time in USDT | Loop B BTC Alpha | Fees USD |
|---|---:|---:|---:|---:|---:|---:|
| `DIBSE_FULL_4GATE` | 14 / 14 | 2 / 1 | 33.0% | 87.6% | -79.08% | \$691 |
| `DIBSE_LOOP_A_ONLY` | 14 / 14 | 0 / 0 | 33.0% | 0.0% | +0.00% | \$637 |
| `DIBSE_LOOP_B_ONLY` | 0 / 0 | 2 / 1 | 0.0% | 87.6% | -79.08% | \$54 |
| `ABL_G3_ONLY` | 29 / 28 | 3 / 2 | 85.6% | 99.0% | -88.47% | \$1,451 |
| `ABL_G3_G1` | 26 / 25 | 3 / 2 | 81.4% | 99.0% | -88.47% | \$1,547 |
| `ABL_G3_G2` | 13 / 12 | 2 / 1 | 55.7% | 97.7% | -86.84% | \$507 |
| `ABL_G3_G4` | 30 / 29 | 2 / 1 | 83.3% | 97.5% | -82.87% | \$1,686 |

## 5. Transaction Cost Stress (2x = 20 bps) & Resting Limit Exit Sensitivity

| Strategy / Benchmark | Cost (bps) | Final Eq | Tot Ret | CAGR | Ann Vol | Max DD | Sharpe | Sortino | Calmar | t-stat | PSR(0) | DSR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `DIBSE_FULL_4GATE` | 10 | \$55,989 | +180.4% | +16.20% | 17.5% | -31.6% | 0.95 | 1.34 | 0.51 | 2.49 | 98.7% | 93.3% |
| `DIBSE_FULL_20BPS` | 20 | \$54,969 | +175.3% | +15.89% | 17.4% | -31.6% | 0.94 | 1.31 | 0.50 | 2.45 | 98.6% | 92.9% |
| `DIBSE_FULL_LIMIT_10BPS` | 10 | \$51,457 | +157.7% | +14.78% | 17.1% | -31.6% | 0.89 | 1.25 | 0.47 | 2.34 | 98.2% | 91.4% |
| `DIBSE_FULL_LIMIT_20BPS` | 20 | \$50,561 | +153.2% | +14.49% | 17.1% | -31.6% | 0.88 | 1.23 | 0.46 | 2.31 | 98.0% | 91.0% |
| `BENCH_50_50_REBAL_WK` | 20 | \$86,333 | +332.4% | +23.77% | 29.8% | -48.8% | 0.87 | 1.26 | 0.49 | 2.27 | 98.7% | 92.5% |
| `BENCH_50_50_REBAL_5PCT` | 20 | \$89,445 | +348.0% | +24.41% | 30.1% | -48.9% | 0.88 | 1.28 | 0.50 | 2.30 | 98.8% | 92.9% |
| `BENCH_DETZEL_200D_SMA` | 20 | \$127,705 | +538.5% | +31.00% | 42.7% | -64.8% | 0.84 | 1.29 | 0.48 | 2.21 | 98.9% | 92.9% |

## 6. Sub-Period Regime Attribution (Continuous Daily Equity Slices)

### 2020-2021 (Bull/Cycle)

| Strategy | Tot Ret | CAGR | Max DD | Sharpe | Sortino |
|---|---:|---:|---:|---:|---:|
| `DIBSE_FULL_4GATE` | +65.5% | +28.7% | -31.6% | 1.08 | 1.45 |
| `DIBSE_LOOP_A_ONLY` | +284.8% | +96.4% | -48.7% | 1.46 | 2.16 |
| `DIBSE_LOOP_B_ONLY` | +57.4% | +25.5% | -31.6% | 0.99 | 1.33 |
| `BENCH_BH_100_BTC` | +554.4% | +156.1% | -53.6% | 1.61 | 2.34 |
| `BENCH_50_50_HOLD` | +276.7% | +94.3% | -47.7% | 1.45 | 2.13 |
| `BENCH_50_50_REBAL_WK` | +197.9% | +72.7% | -29.6% | 1.60 | 2.32 |
| `BENCH_DETZEL_200D_SMA` | +116.5% | +47.2% | -64.0% | 0.95 | 1.40 |

### 2022 (Bear/Crash)

| Strategy | Tot Ret | CAGR | Max DD | Sharpe | Sortino |
|---|---:|---:|---:|---:|---:|
| `DIBSE_FULL_4GATE` | -19.0% | -19.0% | -23.2% | -1.33 | -1.71 |
| `DIBSE_LOOP_A_ONLY` | -62.5% | -62.6% | -65.8% | -1.30 | -1.70 |
| `DIBSE_LOOP_B_ONLY` | +0.0% | +0.0% | 0.0% | 0.00 | 0.00 |
| `BENCH_BH_100_BTC` | -64.1% | -64.2% | -66.9% | -1.28 | -1.69 |
| `BENCH_50_50_HOLD` | -55.4% | -55.5% | -58.1% | -1.35 | -1.77 |
| `BENCH_50_50_REBAL_WK` | -36.7% | -36.7% | -39.8% | -1.29 | -1.70 |
| `BENCH_DETZEL_200D_SMA` | +0.0% | +0.0% | 0.0% | 0.00 | 0.00 |

### 2023-2024 (Recovery/ETF)

| Strategy | Tot Ret | CAGR | Max DD | Sharpe | Sortino |
|---|---:|---:|---:|---:|---:|
| `DIBSE_FULL_4GATE` | +62.0% | +27.3% | -8.2% | 1.96 | 3.44 |
| `DIBSE_LOOP_A_ONLY` | +432.7% | +130.8% | -20.5% | 2.07 | 3.48 |
| `DIBSE_LOOP_B_ONLY` | +0.0% | +0.0% | 0.0% | 0.00 | 0.00 |
| `BENCH_BH_100_BTC` | +460.9% | +136.8% | -26.2% | 2.01 | 3.35 |
| `BENCH_50_50_HOLD` | +320.8% | +105.1% | -23.8% | 1.93 | 3.18 |
| `BENCH_50_50_REBAL_WK` | +151.5% | +58.6% | -12.6% | 2.01 | 3.35 |
| `BENCH_DETZEL_200D_SMA` | +250.0% | +87.1% | -25.8% | 1.63 | 2.70 |

### 2025-Present (Late Cycle)

| Strategy | Tot Ret | CAGR | Max DD | Sharpe | Sortino |
|---|---:|---:|---:|---:|---:|
| `DIBSE_FULL_4GATE` | +28.6% | +14.5% | -4.3% | 1.90 | 3.95 |
| `DIBSE_LOOP_A_ONLY` | -9.7% | -5.3% | -43.5% | 0.02 | 0.03 |
| `DIBSE_LOOP_B_ONLY` | +0.0% | +0.0% | 0.0% | 0.00 | 0.00 |
| `BENCH_BH_100_BTC` | -20.9% | -11.8% | -53.0% | -0.08 | -0.11 |
| `BENCH_50_50_HOLD` | -19.4% | -10.9% | -50.1% | -0.10 | -0.14 |
| `BENCH_50_50_REBAL_WK` | -7.7% | -4.2% | -30.2% | -0.10 | -0.14 |
| `BENCH_DETZEL_200D_SMA` | -11.5% | -6.4% | -31.7% | -0.09 | -0.13 |

## 7. Multi-Year De-Clustered Forward Event Study (30-Bar / 5D Embargo, N=14,979 bars)

- **Loop A Independent Buy Triggers (`N_A`):** `23`
- **Loop B Independent Sell Triggers (`N_B`):** `2`

| Loop & Horizon | N | Mean Ret | Median Ret | Win Rate | Uncond Baseline | Alpha vs Base | t-stat |
|---|---:|---:|---:|---:|---:|---:|---:|
| Loop A (Forward +Ret) **1D** | 23 | -0.27% | +0.36% | 52.2% | +0.14% | -0.42% | -0.53 |
| Loop A (Forward +Ret) **3D** | 23 | +1.06% | -0.15% | 43.5% | +0.43% | +0.64% | 1.39 |
| Loop A (Forward +Ret) **5D** | 23 | +1.56% | +0.64% | 56.5% | +0.71% | +0.85% | 1.73 |
| Loop A (Forward +Ret) **10D** | 23 | +1.62% | +0.83% | 56.5% | +1.42% | +0.20% | 1.45 |
| Loop B (Price Drop / Discount) **1D** | 2 | -0.27% | -0.27% | 50.0% | -0.14% | -0.12% | -0.06 |
| Loop B (Price Drop / Discount) **3D** | 2 | +4.48% | +4.48% | 50.0% | -0.43% | +4.91% | 0.58 |
| Loop B (Price Drop / Discount) **5D** | 2 | +1.78% | +1.78% | 50.0% | -0.71% | +2.49% | 0.15 |
| Loop B (Price Drop / Discount) **10D** | 2 | -2.78% | -2.78% | 50.0% | -1.42% | -1.35% | -0.17 |
