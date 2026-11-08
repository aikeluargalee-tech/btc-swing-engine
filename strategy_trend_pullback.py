"""Root-level module entry point for BTC TREND-PULLBACK v1.0.

Re-exports all strategy functions, configuration, and engine classes from
`analytics.strategy_trend_pullback` for direct root-level import compatibility.
"""

from analytics.strategy_trend_pullback import (
    TrendPullbackConfig,
    TrendPullbackEngine,
    calculate_entry_zone,
    calculate_position_size,
    calculate_regime,
    calculate_stop,
    calculate_trend,
    compute_atr_series,
    compute_ema_series,
    compute_sma_series,
    copy_trend_pullback_to_clipboard,
    detect_pullback,
    evaluate_exit,
    generate_strategy_verdict,
    synthesize_closed_4h_from_1h,
    verify_and_extract_completed_candles,
)

__all__ = [
    "TrendPullbackConfig",
    "TrendPullbackEngine",
    "calculate_entry_zone",
    "calculate_position_size",
    "calculate_regime",
    "calculate_stop",
    "calculate_trend",
    "compute_atr_series",
    "compute_ema_series",
    "compute_sma_series",
    "copy_trend_pullback_to_clipboard",
    "detect_pullback",
    "evaluate_exit",
    "generate_strategy_verdict",
    "synthesize_closed_4h_from_1h",
    "verify_and_extract_completed_candles",
]
