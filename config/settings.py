import os
"""Centralized configuration and quantitative thresholds for the BTC Swing Engine."""



from dataclasses import dataclass, field

from pathlib import Path

from typing import List





BASE_DIR = Path(__file__).resolve().parent.parent





@dataclass(frozen=True)

class EngineConfig:

    """Configuration parameters for data ingestion, volume profile math, and signal detection."""



    # --- Symbols ---

    binance_symbol: str = "BTCUSDT"

    coinbase_symbol: str = "BTC-USD"



    # --- Public REST Endpoints (with automatic geo-resilient fallbacks) ---

    binance_spot_rest_urls: List[str] = field(

        default_factory=lambda: [

            "https://data-api.binance.vision",

            "https://api.binance.com",

            "https://api1.binance.com",

        ]

    )

    binance_perp_rest_urls: List[str] = field(

        default_factory=lambda: [

            "https://fapi.binance.com",

        ]

    )

    okx_rest_url: str = "https://www.okx.com"

    okx_perp_inst_id: str = "BTC-USDT-SWAP"   # Fallback perp venue (fapi.binance.com 451 / Bybit 403 on some hosts)

    okx_perp_ws_url: str = "wss://ws.okx.com:8443/ws/v5/public"

    bybit_rest_url: str = "https://api.bybit.com"

    coinbase_rest_url: str = "https://api.exchange.coinbase.com"



    # --- Public WebSocket Endpoints (with automatic fallbacks) ---

    binance_spot_ws_urls: List[str] = field(

        default_factory=lambda: [

            "wss://data-stream.binance.vision/ws/btcusdt@aggTrade",

            "wss://stream.binance.com:9443/ws/btcusdt@aggTrade",

        ]

    )

    binance_perp_ws_urls: List[str] = field(

        default_factory=lambda: [

            "wss://fstream.binance.com/ws/btcusdt@aggTrade",

        ]

    )

    bybit_perp_ws_url: str = "wss://stream.bybit.com/v5/public/linear"

    coinbase_ws_url: str = "wss://ws-feed.exchange.coinbase.com"



    # --- WebSocket & Polling Resilience ---

    ws_ping_interval: int = 20

    ws_ping_timeout: int = 20

    ws_reconnect_base_delay: float = 1.5

    ws_reconnect_max_delay: float = 30.0

    rest_poll_interval_sec: float = 15.0

    kline_sync_interval_sec: float = 60.0

    hud_refresh_rate_hz: float = 2.0



    # --- Structural Volume Profile Parameters ---

    macro_profile_days: int = 30        # 30-Day Macro Composite (720 x 1H klines)

    tactical_profile_days: int = 7      # 7-Day Tactical Composite (168 x 1H klines)

    profile_num_bins: int = 120         # Number of price bins across range

    value_area_pct: float = 0.70        # Standard 70% CME Value Area (1 SD)

    gaussian_sigma_bins: float = 1.5    # Smoothing sigma for HVN/LVN topology

    lvn_relative_threshold: float = 0.55  # Local min below 55% of mean bin volume

    hvn_relative_threshold: float = 1.20  # Local max above 120% of mean bin volume

    atr_period: int = 14                # 14-bar ATR on 1H & 4H timeframes



    # --- Order Flow & CVD Normalization ---

    cvd_zscore_lookback: int = 48       # Trailing windows for Z-score standardization

    absorption_effort_threshold: float = 1.8  # Effort-vs-Result ratio threshold at cVAL

    divergence_z_spread_threshold: float = 1.0  # Z_spot - Z_perp threshold for absorption

    leveraged_trap_z_spread: float = -1.2     # Z_spot - Z_perp threshold for perp chase trap



    # --- Derivatives & Positioning Thresholds ---

    oi_flush_pct_4h: float = -1.5       # 4H OI drop (%) signaling long liquidation reset

    oi_short_build_pct_1h: float = 0.4  # 1H OI rise (%) while price <= 0 at cVAL

    oi_surge_trap_pct_1h: float = 0.8   # 1H OI surge (%) during unconfirmed perp bounce

    funding_neutral_max_pct: float = 0.012    # <= 0.012% per 8h considered healthy/un-crowded

    funding_crowded_veto_pct: float = 0.035   # > 0.035% per 8h triggers crowded-long veto

    cpi_positive_threshold_pct: float = 0.0   # Direct USD premium over USDT

    cpi_zscore_bullish_threshold: float = 0.75



    # --- 4-Gate Execution & Risk Management ---

    val_proximity_atr_mult: float = 0.50      # Distance from cVAL (in 1H ATRs) to arm Gate 1

    min_structural_rr_to_poc: float = 1.5     # Minimum Reward:Risk to cPOC

    stop_atr_buffer_mult: float = 0.50        # Stop placed 0.5 x 1H ATR below sweep low / LVN

    tp1_allocation_pct: float = 55.0          # Scale out 55% at cPOC, move stop to BE

    tp2_allocation_pct: float = 45.0          # Trail 45% to cVAH

    signal_confluence_threshold: float = 70.0 # Minimum 0-100 score for actionable signal

    portfolio_equity_usd: float = 100_000.0   # Reference portfolio size for position sizing

    risk_per_trade_pct: float = 1.0           # 1.0% equity risk per swing setup

    counter_trend_risk_pct: float = 0.5       # 0.5% equity risk when below 1D 200 SMA



    # --- Protocol v1.3 & Macro Cycle Radar Parameters ---

    daily_kline_limit: int = 500              # 500x 1D candles (~1.4y) for 200D SMA + 20D slope + 180D BBW rank + 60D corr

    weekly_kline_limit: int = 100             # 100x 1W candles (~2y) for 1W EMA50 warmup & Cycle High

    four_hour_kline_limit: int = 500          # 500x 4H candles (~83d) to eliminate recursive seed drift on 4H EMA 200

    protocol_oi_high_threshold_btc: float = 90_000.0  # Protocol v1.3 8A OI threshold in strict BTC

    protocol_round_numbers_usd: List[float] = field(

        default_factory=lambda: [80_000.0, 85_000.0, 100_000.0]

    )

    protocol_round_proximity_pct: float = 2.0 # Within 2.0% of round number for 8A check

    default_cycle_ath_usd: float = 109_588.0  # Cycle ATH reference floor if higher than 255D window

    protocol_context_path: Path = field(

        default_factory=lambda: BASE_DIR / "config" / "protocol_context.json"

    )



    # --- Tab [0]: BTC Spot Swing Screening & Alert Engine ---

    spot_swing_account_equity_usd: float = 100_000.0  # Base account size for 1% risk sizing (env SPOT_SWING_EQUITY_USD)

    spot_swing_risk_pct: float = 1.0                  # Fixed equity risk per setup, in percent

    spot_swing_ema_fast: int = 50                     # Daily trend baseline EMAs

    spot_swing_ema_slow: int = 200

    spot_swing_bbw_period: int = 20                   # Bollinger-width period (2 sigma)

    spot_swing_bbw_rank_window: int = 180             # Rolling percentile-rank window (daily bars)

    spot_swing_bbw_max_percentile: float = 0.30       # Squeeze gate: percentile rank <= 0.30

    spot_swing_squeeze_lookback_bars: int = 1         # 1 = strict current daily bar; N = any of last N bars

    spot_swing_min_daily_bars: int = 250              # Minimum closed 1D bars required

    spot_swing_min_4h_bars: int = 100                 # Minimum closed 4H bars required

    spot_swing_sweep_window_bars: int = 12            # 12 x 4H = ~48h sweep lookback

    spot_swing_vol_sma_period: int = 3                # Reclaim-bar volume must exceed SMA(3)

    spot_swing_atr_period: int = 14                   # 4H ATR for the invalidation stop

    spot_swing_stop_atr_mult: float = 0.5             # P_stop = sweep_low - 0.5 x ATR14

    spot_swing_tp1_r_multiple: float = 2.0            # Partial exit at +2.0R

    spot_swing_tp1_fraction: float = 0.5              # Sell 50% at TP1, stop -> breakeven

    spot_swing_time_stop_days: int = 10               # Barrier 3: max holding period

    spot_swing_min_rrr: float = 3.0                   # Minimum 1:3 RRR required to Short-Liq Magnet

    spot_swing_range_lookback_days: int = 35          # 30-45 day range window for Liquidation Magnet Protocol

    spot_swing_stale_grace_sec: int = 600             # Tolerated lag for the newest closed bar

    spot_swing_state_path: Path = field(

        default_factory=lambda: BASE_DIR / "spot_swing_state.json"

    )



    # --- External Satellite Engine Feeds ---

    liquidation_report_path: Path = field(

        default_factory=lambda: Path(

            os.environ.get(

                "LIQUIDATION_REPORT_PATH",

                r"C:\Users\aikel\.gemini\antigravity\scratch\btc_liquidation_detector\latest_detector_report.json",

            )

        )

    )

    tell_tale_min_relvol: float = 5.0

    tell_tale_min_body_range: float = 0.65

    tell_tale_lookback: int = 20

    # --- Tab [13: P] Structure + Level Swing Protocol (SLSP v1.0) & 4-in-1 Integration ---
    slsp_risk_pct: float = 0.75                     # Default risk per trade: 0.75% equity
    slsp_max_risk_pct: float = 1.00                 # Maximum risk per trade: 1.00%
    slsp_min_rr: float = 1.50                       # Minimum reward-to-risk ratio: 1.50
    slsp_min_level_strength: int = 3                # Minimum level score (1-5): 3 stars
    slsp_max_daily_loss_pct: float = 2.0            # Max daily loss circuit breaker: 2.0%
    slsp_max_weekly_loss_pct: float = 4.0           # Max weekly loss circuit breaker: 4.0%
    slsp_tp1_r_multiple: float = 1.50               # Scale out 50% at +1.5R
    slsp_tp2_r_multiple: float = 2.50               # Target / trail remaining 50% at +2.5R
    slsp_be_r_multiple: float = 1.00                # Ratchet stop to Breakeven (+0.1% fee) at +1.0R
    slsp_mode: str = "SEMI_AUTO"                    # "ALERT_ONLY" or "SEMI_AUTO"
    slsp_state_path: Path = field(
        default_factory=lambda: BASE_DIR / "data" / "slsp_trade_state.json"
    )




    # --- Tab [20: X] BTC Short-Term Futures + Inventory Protocol v4.0 ---
    futures_v4_equity_usd: float = 100000.0
    futures_v4_spot_inventory_btc: float = 2.0
    futures_v4_max_leverage: float = 2.0
    futures_v4_risk_per_trade_pct: float = 0.004
    futures_v4_max_heat_pct: float = 0.015
    futures_v4_max_concurrent: int = 1
    futures_v4_max_stop_pct: float = 0.022
    futures_v4_min_rr: float = 1.6
    futures_v4_macro_blackout_min: float = 60.0
    futures_v4_long_threshold: float = 68.0
    futures_v4_short_threshold: float = 32.0
    futures_v4_weekend_long: float = 80.0
    futures_v4_weekend_short: float = 20.0
    futures_v4_weekend_size_mult: float = 0.5
    futures_v4_sell_inv_default_pct: float = 0.20
    futures_v4_sell_inv_min_pct: float = 0.15
    futures_v4_sell_inv_max_pct: float = 0.25
    futures_v4_be_r: float = 1.0
    futures_v4_partial_r: float = 1.5
    futures_v4_partial_pct: float = 0.45
    futures_v4_time_reduce_hours: float = 8.0
    futures_v4_time_exit_hours: float = 12.0
    futures_v4_max_hold_hours: float = 24.0
    futures_v4_intraday_loss_pct: float = -0.012
    futures_v4_daily_loss_pct: float = -0.020
    futures_v4_weekly_loss_pct: float = -0.040
    futures_v4_dd_tier1_pct: float = -0.060
    futures_v4_dd_tier1_risk_pct: float = 0.002
    futures_v4_dd_tier1_long: float = 75.0
    futures_v4_dd_tier1_short: float = 25.0
    futures_v4_dd_tier2_pct: float = -0.100
    futures_v4_ledger_path: Path = field(
        default_factory=lambda: BASE_DIR / "data" / "futures_v4_ledger.json"
    )

    # --- Logging ---

    signal_log_path: Path = field(

        default_factory=lambda: BASE_DIR / "logs" / "swing_signals.jsonl"

    )





DEFAULT_CONFIG = EngineConfig()

