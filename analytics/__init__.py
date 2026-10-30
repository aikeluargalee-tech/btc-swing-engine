"""Quantitative analytics modules: Composite Volume Profile, Multi-Horizon CVD, and 4-Gate Signal Engine."""

from .ai_packet_exporter import build_ai_telemetry_packet, copy_ai_packet_to_clipboard_and_disk
from .cvd_engine import compute_derivatives_snapshot, compute_flow_snapshot
from .macro_radar import MacroRadarEvaluator, compute_200d_sma_and_slope, compute_ema, compute_wilder_rsi
from .master_synthesis import MasterSynthesisEvaluator
from .protocol_v13 import ProtocolV13Evaluator, synthesize_1d_bars_from_1h
from .regime_matrix import RegimeMatrixEvaluator
from .signal_detector import SignalDetector
from .volatility_cone_engine import VolatilityConeEngine
from .volume_profile import compute_atr, compute_composite_profile, synthesize_4h_bars

__all__ = [
    "MacroRadarEvaluator",
    "MasterSynthesisEvaluator",
    "ProtocolV13Evaluator",
    "RegimeMatrixEvaluator",
    "SignalDetector",
    "VolatilityConeEngine",
    "build_ai_telemetry_packet",
    "compute_200d_sma_and_slope",
    "compute_atr",
    "compute_composite_profile",
    "compute_derivatives_snapshot",
    "compute_ema",
    "compute_flow_snapshot",
    "compute_wilder_rsi",
    "copy_ai_packet_to_clipboard_and_disk",
    "synthesize_1d_bars_from_1h",
    "synthesize_4h_bars",
]
