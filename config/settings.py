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
    daily_kline_limit: int = 255              # 255x 1D candles for 200D SMA + 5D slope + 14D RSI
    weekly_kline_limit: int = 60              # 60x 1W candles for Weekly structure & Cycle High
    protocol_oi_high_threshold_btc: float = 90_000.0  # Protocol v1.3 8A OI threshold in strict BTC
    protocol_round_numbers_usd: List[float] = field(
        default_factory=lambda: [80_000.0, 85_000.0, 100_000.0]
    )
    protocol_round_proximity_pct: float = 2.0 # Within 2.0% of round number for 8A check
    default_cycle_ath_usd: float = 109_588.0  # Cycle ATH reference floor if higher than 255D window
    protocol_context_path: Path = field(
        default_factory=lambda: BASE_DIR / "config" / "protocol_context.json"
    )

    # --- Logging ---
    signal_log_path: Path = field(
        default_factory=lambda: BASE_DIR / "logs" / "swing_signals.jsonl"
    )


DEFAULT_CONFIG = EngineConfig()
