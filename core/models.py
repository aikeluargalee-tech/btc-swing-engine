"""Typed data structures for Auction Profiles, Order Flow, Derivatives, and Swing Signals."""

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class MarketRegime(str, Enum):
    """Macro-microstructure market state classification."""

    BALANCED = "BALANCED"
    ABSORPTION_AT_SUPPORT = "ABSORPTION_AT_SUPPORT"
    LEVERAGE_EXPANSION = "LEVERAGE_EXPANSION"
    LEVERAGE_TRAP = "LEVERAGE_TRAP"
    MARKDOWN = "MARKDOWN"


class ExecutionGateState(str, Enum):
    """4-Gate sequential execution funnel state."""

    CASH_MARKDOWN = "CASH_MARKDOWN"
    NEUTRAL_OBSERVATION = "NEUTRAL_OBSERVATION"
    GATE1_ZONE_ALERT = "GATE1_ZONE_ALERT"
    GATE2_MICROSTRUCTURE_ARMED = "GATE2_MICROSTRUCTURE_ARMED"
    GATE3_RECLAIM_TRIGGERED = "GATE3_RECLAIM_TRIGGERED"
    GATE4_PENDING_RETEST = "GATE4_PENDING_RETEST"


class OIPositioningQuadrant(str, Enum):
    """4-Quadrant Price vs. Open Interest classification."""

    LONG_LIQUIDATION_FLUSH = "LONG_LIQUIDATION_FLUSH (Price Down / OI Down)"
    AGGRESSIVE_SHORT_BUILD = "AGGRESSIVE_SHORT_BUILD (Price Down/Flat / OI Up)"
    LEVERAGED_LONG_EXPANSION = "LEVERAGED_LONG_EXPANSION (Price Up / OI Up)"
    SHORT_COVERING_BOUNCE = "SHORT_COVERING_BOUNCE (Price Up / OI Down)"
    NEUTRAL_CHURN = "NEUTRAL_CHURN"


@dataclass
class KlineBar:
    """Standardized OHLCV + Taker Buy/Sell Volume candle."""

    timestamp_ms: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    taker_buy_volume: float

    @property
    def taker_sell_volume(self) -> float:
        return max(0.0, self.volume - self.taker_buy_volume)

    @property
    def delta(self) -> float:
        return self.taker_buy_volume - self.taker_sell_volume

    @property
    def typical_price(self) -> float:
        return (self.high + self.low + self.close) / 3.0


@dataclass
class VolumeProfileResult:
    """Computed Composite Volume Profile with 70% Value Area and HVN/LVN topology."""

    horizon_label: str
    c_vah: float
    c_poc: float
    c_val: float
    range_high: float
    range_low: float
    total_volume: float
    bin_width: float
    lvn_levels: List[float] = field(default_factory=list)
    hvn_levels: List[float] = field(default_factory=list)
    primary_lvn_below_val: Optional[float] = None
    support_hvn_below_val: Optional[float] = None
    bin_centers: List[float] = field(default_factory=list)
    bin_volumes: List[float] = field(default_factory=list)


@dataclass
class HorizonFlowMetrics:
    """Normalized Spot vs. Perp order flow metrics over a specific rolling horizon."""

    window_label: str
    spot_delta_btc: float = 0.0
    spot_volume_btc: float = 0.0
    spot_delta_ratio: float = 0.0
    spot_zscore: float = 0.0
    perp_delta_btc: float = 0.0
    perp_volume_btc: float = 0.0
    perp_delta_ratio: float = 0.0
    perp_zscore: float = 0.0
    flow_divergence_z: float = 0.0
    absorption_index: float = 0.0
    price_change_pct: float = 0.0


@dataclass
class FlowSnapshot:
    """Complete multi-horizon order flow and live WebSocket CVD state."""

    session_spot_cvd: float = 0.0
    session_perp_cvd: float = 0.0
    utc_day_spot_cvd: float = 0.0
    utc_day_perp_cvd: float = 0.0
    spot_trade_count: int = 0
    perp_trade_count: int = 0
    w_15m: HorizonFlowMetrics = field(default_factory=lambda: HorizonFlowMetrics("15m"))
    w_1h: HorizonFlowMetrics = field(default_factory=lambda: HorizonFlowMetrics("1H"))
    w_4h: HorizonFlowMetrics = field(default_factory=lambda: HorizonFlowMetrics("4H"))
    w_24h: HorizonFlowMetrics = field(default_factory=lambda: HorizonFlowMetrics("24H"))
    bullish_pivot_divergence: bool = False
    absorption_divergence: bool = False
    flow_signature: str = "BALANCED"


@dataclass
class DerivativesSnapshot:
    """Cross-exchange basis, Open Interest dynamics, and funding positioning."""

    open_interest_btc: float = 0.0
    open_interest_usd: float = 0.0
    oi_change_15m_pct: float = 0.0
    oi_change_1h_pct: float = 0.0
    oi_change_4h_pct: float = 0.0
    oi_regime_quadrant: OIPositioningQuadrant = OIPositioningQuadrant.NEUTRAL_CHURN
    funding_rate_pct: float = 0.0
    taker_long_short_ratio_5m: float = 1.0
    perp_5m_delta_btc: float = 0.0
    coinbase_price: float = 0.0
    binance_spot_price: float = 0.0
    binance_perp_price: float = 0.0
    coinbase_premium_usd: float = 0.0
    coinbase_premium_pct: float = 0.0
    coinbase_premium_zscore: float = 0.0
    perp_basis_usd: float = 0.0
    perp_source: str = "Binance USD-M"


@dataclass
class TradePlan:
    """Actionable spot swing trade execution geometry and dynamic position sizing."""

    entry_zone_low: float
    entry_zone_high: float
    reference_entry: float
    stop_loss: float
    tp1_poc: float
    tp1_allocation_pct: float
    tp2_vah: float
    tp2_allocation_pct: float
    rr_to_poc: float
    rr_to_vah: float
    position_size_btc: float
    position_notional_usd: float
    risk_usd: float
    risk_pct: float = 1.0


@dataclass
class CoinGlassPanelRow:
    """Single row of the fixed 6-panel CoinGlass audit (Tab 2 Panel 2)."""

    panel_num: int
    metric_name: str
    value_1d: str
    value_4h: str
    direction_status: str


@dataclass
class ProtocolNonTradeZoneItem:
    """Single Section 8 Non-Trade Zone check (8A-8F) in Protocol v1.3."""

    code: str
    rule_name: str
    status: str  # "CLEAR", "TRIGGERED", "UNVERIFIED"
    detail: str


@dataclass
class ProtocolSellTriggerItem:
    """Single Section 11 Long-Only Spot Sell Trigger (1-4) in Protocol v1.3."""

    trigger_num: int
    name: str
    status: str  # "CONFIRMED", "NOT CONFIRMED", "UNVERIFIED"
    detail: str


@dataclass
class ProtocolV13Evaluation:
    """Complete evaluation state for Tab [2]: BTC Spot Swing Protocol v1.3."""

    timestamp_utc: str
    current_price: float
    completed_1d_open: float
    completed_1d_high: float
    completed_1d_low: float
    completed_1d_close: float
    completed_1d_change_pct: float
    forming_1d_open: float
    forming_1d_high: float
    forming_1d_low: float
    forming_1d_close: float
    forming_1d_change_pct: float
    daily_support: float
    daily_resistance: float
    daily_bias: str  # "BULLISH", "NEUTRAL", "BEARISH"
    structure_4h: str
    timing_4h_ready: bool
    atr_14_1d: float
    atr_14_4h: float
    downside_ref_1d_atr: float
    upside_ref_1d_atr: float
    downside_ref_4h_atr: float
    upside_ref_4h_atr: float
    coinglass_rows: List[CoinGlassPanelRow] = field(default_factory=list)
    non_trade_zones: List[ProtocolNonTradeZoneItem] = field(default_factory=list)
    non_trade_zone_status: str = "NO"  # "YES", "NO", "UNVERIFIED"
    active_ntz_reasons: List[str] = field(default_factory=list)
    confidence: str = "LOW"  # "HIGH", "MEDIUM", "LOW"
    buy_allowed: str = "NO"  # "YES", "NO"
    entry_status: str = "NOT READY"  # "READY", "NOT READY"
    readiness_notes: List[str] = field(default_factory=list)
    sell_triggers: List[ProtocolSellTriggerItem] = field(default_factory=list)
    any_sell_confirmed: bool = False
    enforce_200d_hard_veto_on_tab1: bool = False
    context_last_reviewed: str = "N/A"
    sma_50_1d: float = 0.0
    range_pivot_usd: float = 0.0
    short_liq_magnet_usd: float = 0.0
    short_liq_source: str = "[EST. SWING LIQ POOL]"
    long_liq_magnet_usd: float = 0.0
    long_liq_source: str = "[EST. SWING LIQ POOL]"
    headline_filter_status: str = "NONE_SIGNIFICANT"
    magnet_confluence_aligned: int = 0
    liq_magnet_verdict: str = "DO NOTHING (Default Inaction)"
    liq_magnet_action_note: str = ""


@dataclass
class CrashRungItem:
    """Single Cycle Drawdown Accumulation Rung (-25% to -65%) for Tab [3] Panel 2."""

    rung_label: str
    drawdown_pct: float
    target_price: float
    distance_pct: float
    allocation_tranche: str
    status: str  # "HIT / ACTIVE", "NEAR (<3%)", "STANDBY"


@dataclass
class MacroTimeframeRow:
    """Single timeframe row (1W / 1D Completed / 1D Forming / 4H) for Tab [3] Panel 3."""

    timeframe: str
    structure: str
    close_vs_open_pct: float
    candle_signature: str
    flow_momentum: str


@dataclass
class MacroRadarEvaluation:
    """Complete evaluation state for Tab [3]: Macro Quant & Cycle Radar."""

    timestamp_utc: str
    current_price: float
    completed_1d_close: float
    forming_1d_close: float
    sma_200_1d: float
    sma_200_slope_5d_usd: float
    sma_200_slope_5d_pct: float
    above_200d_sma: bool
    slope_200d_positive: bool
    gatekeeper_veto: bool
    gatekeeper_status_text: str
    ema_21_1d: float
    dist_to_21d_ema_pct: float
    rsi_14_1d: float
    rsi_zone: str
    poc_30d: float
    dist_to_30d_poc_pct: float
    power_law_fair_usd: float = 0.0
    power_law_discount_pct: float = 0.0
    power_law_zone_label: str = "[BIAS ONLY — NOT TIMING]"
    cycle_high_usd: float = 0.0
    current_drawdown_pct: float = 0.0
    active_crash_rung: str = "NONE"
    crash_rung_override_active: bool = False
    crash_rungs: List[CrashRungItem] = field(default_factory=list)
    scale_out_targets: List[str] = field(default_factory=list)
    tf_rows: List[MacroTimeframeRow] = field(default_factory=list)
    wick_flush_4h_detected: bool = False
    wick_flush_4h_ratio: float = 0.0
    wick_flush_detail: str = "NONE"
    trend_score: float = 0.0
    momentum_score: float = 0.0
    flow_score: float = 0.0
    structure_score: float = 0.0
    macro_confidence_pct: float = 0.0
    recommended_allocation: str = "0% (100% CASH)"
    macro_notes: List[str] = field(default_factory=list)


@dataclass
class RegimeConfigItem:
    """Single row/configuration (Config A through Config J) for Tab [4] Regime Matrix."""

    code: str  # "Config A" .. "Config J"
    short_title: str  # e.g. "Healthy Bull"
    diagnosis_subtitle: str  # e.g. "Genuine Spot-Led Expansion"
    category: str  # "BULL_LONG", "ACCUMULATE", "HARVEST_WAIT", "DEFENSIVE_CASH"
    match_pct: float  # 0.0 .. 100.0
    is_active: bool
    key_live_facts: str
    action_headline: str  # e.g. "Full Spot Long (1.0x)"
    sizing_rule: str
    entry_or_harvest_rule: str
    stop_rule: str
    computed_stop_usd: float
    observed_checklist: List[str] = field(default_factory=list)


@dataclass
class RegimeMatrixEvaluation:
    """Complete evaluation state for Tab [4]: Quantitative Microstructure Configurations A-J."""

    timestamp_utc: str
    current_price: float
    daily_vwap: float
    weekly_vwap: float
    ema_20_1d: float
    ema_50_1d: float
    spot_vol_vs_20d_ma: float
    spot_buy_sell_ratio_4h: float
    spot_cvd_7d_btc: float
    oi_change_24h_pct: float
    oi_change_4h_pct: float
    oi_change_1h_pct: float
    funding_rate_pct: float
    annualized_basis_pct: float
    atr_compression_pct: float
    base_width_72h_pct: float
    active_config_code: str
    runner_up_config_code: str
    configs: List[RegimeConfigItem] = field(default_factory=list)


@dataclass
class TabVerdictRow:
    """Single row in Tab [5] Panel 1 summarizing one specialist tab's live verdict."""

    tab_num: int
    tab_name: str
    traffic_light: str  # "GREEN", "BLUE", "YELLOW", "RED"
    score_or_status: str
    primary_driver: str
    tab_conclusion: str


@dataclass
class HierarchyLayerRow:
    """Single row in Tab [5] Panel 2 showing the 4-Layer Institutional Decision Funnel."""

    layer_num: int
    layer_name: str
    status: str  # "PASS", "ARMED", "STANDBY", "CAUTION", "VETO"
    authority_rule: str
    live_ruling: str


@dataclass
class MasterSynthesisEvaluation:
    """Complete evaluation state for Tab [5]: Master Synthesis & Supreme Order of Battle."""

    timestamp_utc: str
    current_price: float
    tab_rows: List[TabVerdictRow] = field(default_factory=list)
    tabs_green_count: int = 0
    tabs_blue_count: int = 0
    tabs_yellow_count: int = 0
    tabs_red_count: int = 0
    hierarchy_rows: List[HierarchyLayerRow] = field(default_factory=list)
    master_alignment_score: float = 0.0
    alignment_status: str = "NEUTRAL / STANDBY"
    supreme_veto_active: bool = False
    supreme_veto_reason: str = "NONE"
    confluence_points: List[str] = field(default_factory=list)
    conflict_points: List[str] = field(default_factory=list)
    upgrade_catalysts: List[str] = field(default_factory=list)
    # Track A: If Flat in Cash
    cash_permission: str = "WAIT FOR STRUCTURAL EDGE"
    cash_entry_zone_str: str = ""
    cash_base_risk_pct: float = 1.0
    cash_regime_multiplier: float = 0.0
    cash_final_risk_pct: float = 0.0
    cash_final_notional_usd: float = 0.0
    cash_final_size_btc: float = 0.0
    cash_edge_risk_pct: float = 0.5
    cash_edge_notional_usd: float = 0.0
    cash_edge_size_btc: float = 0.0
    cash_trigger_instruction: str = ""
    # Track B: If Already Holding Spot BTC
    holder_action: str = "HOLD CORE SPOT LONG"
    holder_hard_stop_usd: float = 0.0
    holder_hard_stop_source: str = ""
    holder_tp1_usd: float = 0.0
    holder_tp1_source: str = ""
    holder_tp2_usd: float = 0.0
    holder_tp2_source: str = ""
    holder_management_note: str = ""
    # Panel 5: Supreme Master Executive Bottom Line
    master_traffic_light: str = "YELLOW"  # "GREEN", "BLUE", "YELLOW", "RED"
    master_headline: str = ""
    master_what_is_happening: str = ""
    master_why_resolution: str = ""
    master_final_command: str = ""


# ============================================================================
# SPECIAL TAB [S1]: MULTI-MODEL BTC QUANT RADAR (MM-BTC)
# ============================================================================

@dataclass
class PathSignatureResult:
    """Rough Path Signatures (Order N <= 2) and Lévy Signed Area curvature terms."""

    drift_L1: float = 0.0
    drift_flow: float = 0.0
    drift_oi: float = 0.0
    qv_p: float = 0.0
    roughness: float = 1.0
    area_time_price: float = 0.0
    area_price_flow: float = 0.0
    area_price_oi: float = 0.0
    time_price_classification: str = "BALANCED"
    flow_lead_lag_classification: str = "NEUTRAL"
    oi_lead_lag_classification: str = "NEUTRAL"
    arbiter_gate_status: str = "CONFIRMED CLEAR"
    signature_verdict: str = "ACCUMULATE"


@dataclass
class KalmanResult:
    """1D Constant-Velocity Kalman Filter latent price & velocity."""

    filtered_price: float = 0.0
    distance_pct: float = 0.0
    velocity: float = 0.0
    velocity_state: str = "DECELERATING"
    bias: str = "NEUTRAL"


@dataclass
class HurstResult:
    """Rolling Hurst Exponent (H) via Rescaled Range (R/S)."""

    hurst: float = 0.50
    regime: str = "RANDOM WALK"
    tactical_implication: str = "NEUTRAL"


@dataclass
class FractionalDiffResult:
    """Dynamic ADF-Optimized Fixed-Width Window Fractional Differentiation (FFD)."""

    optimal_d: float = 0.40
    adf_p_value: float = 0.05
    adf_stat: float = -2.86
    momentum: float = 0.0
    memory_state: str = "COMPRESSED NOISE"
    bias: str = "NEUTRAL"


@dataclass
class HilbertResult:
    """John Ehlers' MESA Hilbert Transform Analytic Signal with Hampel Wick Filter."""

    dominant_cycle: int = 24
    phase: float = 90.0
    phase_state: str = "MARKUP"
    bias: str = "CYCLE ACCUMULATION"
    outliers_cleaned: int = 0


@dataclass
class MMBTCEvaluation:
    """Unified evaluation for Special Tab [S1]: Multi-Model BTC Strategy (MM-BTC)."""

    timestamp_utc: str
    current_price: float
    signature: PathSignatureResult
    kalman: KalmanResult
    hurst: HurstResult
    frac_diff: FractionalDiffResult
    hilbert: HilbertResult
    cvd_48h: float = 0.0
    oi_delta_pct: float = 0.0
    microstructure_pattern: str = "NEUTRAL"
    microstructure_bias: str = "NEUTRAL"
    gate1_pass: bool = True
    gate2_pass: bool = True
    gate3_y_hat: float = 0.0
    gate3_sizing_mode: str = "WALK-FORWARD RIDGE"
    agreeing_models_count: int = 0
    final_weight: float = 0.0
    conflict_summary: str = ""
    sma_200_1h: float = 0.0
    above_200_1h: bool = True
    micro_tripwire_veto: bool = False
    action_plan_cash: str = "MAINTAIN 100% USDT"
    action_plan_holder: str = "HOLD EXISTING SPOT LONG"
    execution_zone_str: str = ""
    invalidation_str: str = ""
    target_zone_str: str = ""


# ============================================================================
# SPECIAL TAB [S2]: 72-HOUR FORWARD VOLATILITY CONE & AI BENCHMARK RADAR
# ============================================================================

@dataclass
class ConeHorizonRow:
    """Calculated Hurst-scaled Garman-Klass volatility cone slice and TSFM consensus at horizon k."""

    horizon_label: str  # "+4h (Bar +1)", "+24h (Bar +6)", "+48h (Bar +12)", "+72h (Bar +18)"
    bar_offset: int  # 1, 6, 12, 18
    hours: int  # 4, 24, 48, 72
    drift_center: float  # Damped Kalman drift center price
    gk_1sigma_lower: float  # -1 sigma (68% confidence)
    gk_1sigma_upper: float  # +1 sigma (68% confidence)
    gk_2sigma_lower: float  # -2 sigma (95% confidence)
    gk_2sigma_upper: float  # +2 sigma (95% confidence)
    gk_1sigma_spread_usd: float  # upper - lower in USD
    gk_1sigma_spread_pct: float  # spread as % of center
    kronos_close: float  # Kronos-base predicted close
    chronos_close: float  # Chronos-Bolt-small predicted close
    timesfm_close: float  # TimesFM 2.5 predicted close
    tsfm_mean_close: float  # Consensus mean across the 3 TSFMs
    tsfm_dispersion_pct: float  # Max diff among TSFMs as % of spot


@dataclass
class TSFMBenchmarkItem:
    """Quarantined Time-Series Foundation Model benchmark record."""

    name: str  # "Kronos-base", "Chronos-Bolt-small", "TimesFM 2.5"
    predicted_close_72h: float
    direction_str: str  # "UP +0.13%", "UP +0.22%", "DOWN -0.15%"
    predicted_range_min: float
    predicted_range_max: float
    range_dollar_spread: float
    range_pct: float
    sample_path: List[float] = field(default_factory=list)  # Closes at [+4h, +24h, +48h, +72h]
    architecture_tag: str = ""
    training_domain: str = ""
    quarantine_status: str = "BENCHMARK-ONLY (0.0% CAPITAL WEIGHT)"


@dataclass
class VolatilityConeEvaluation:
    """Unified evaluation for Special Tab [S2]: 72-Hour Forward Volatility Cone & AI Benchmark Radar Desk."""

    timestamp_utc: str
    spot_price: float
    garman_klass_vol_4h: float  # per 4H bar volatility (e.g. 0.0152 = 1.52%)
    garman_klass_annualized_vol: float  # annualized volatility (sigma_GK * sqrt(365 * 6))
    hurst_exponent: float  # Hurst exponent H in [0.30, 0.75]
    hurst_regime: str  # "SUPER-DIFFUSIVE EXPANSION (H > 0.50)", etc.
    kalman_mu_drift: float  # local 4H return drift
    kalman_lambda_decay: float = 0.90
    horizons: List[ConeHorizonRow] = field(default_factory=list)
    tsfm_benchmarks: List[TSFMBenchmarkItem] = field(default_factory=list)
    vcr_72h: float = 1.0  # Variance Compression Ratio = Delta_P_GK_1sigma(72h) / max(Delta_P_TSFMs)
    vcr_status: str = "NORMAL ALIGNMENT"
    coiled_spring_alert: bool = False
    liquidity_confluence_summary: str = ""
    quantitative_takeaway: str = ""
    plain_english_summary: str = ""
    capital_weight_allocated: float = 0.0  # Strictly 0.0% (quarantined)


# ============================================================================
# SPECIAL TAB [S3]: GARTLEY 222 & 5-STRATEGY CONFLUENCE RADAR
# ============================================================================

@dataclass
class GartleyTimeframeResult:
    """Quantitative state machine & harmonic evaluation for a single horizon (1D Macro or 4H Tactical)."""

    timeframe: str  # "1D" or "4H"
    close: float
    verdict: str  # "NO TRADE", "HOLD", "GARTLEY BUY", "CONFLUENCE BUY", "CONFLUENCE + GARTLEY BUY", "GARTLEY SELL TO USDT", etc.
    v1_breakout: str  # "NEW", "HOLD", "EXIT", "FLAT"
    v2_sma200: str
    sma200_val: float
    v3_ema: str
    ema20_val: float
    ema50_val: float
    v4_rsi: str
    rsi_val: float
    v5_bb: str
    v6_gartley_bull: str
    v7_gartley_bear: str
    bull_d: Optional[float] = None
    bear_d: Optional[float] = None
    bull_ratios: Dict[str, float] = field(default_factory=dict)
    bear_ratios: Dict[str, float] = field(default_factory=dict)
    is_new1: bool = False
    is_new2: bool = False
    is_new3: bool = False
    is_new4: bool = False
    is_new5: bool = False
    is_new6: bool = False
    is_new7: bool = False
    is_exit1: bool = False
    is_exit2: bool = False
    is_exit3: bool = False
    is_exit4: bool = False
    is_exit5: bool = False
    is_exit6: bool = False
    is_exit7: bool = False


@dataclass
class Gartley5StrategyEvaluation:
    """Unified evaluation for Special Tab [S3]: Gartley 222 & 5-Strategy Confluence Radar Desk."""

    timestamp_utc: str
    close_price: float
    overall_verdict: str  # e.g., "HOLD (1D Trend Strong, 4H Waiting for Trigger)" or "🔥 CONFLUENCE BUY (GARTLEY BUY)"
    res_1d: GartleyTimeframeResult
    res_4h: GartleyTimeframeResult
    plain_english_summary: str
    standalone_bot_repo: str = "aikeluargalee-tech/btc-spot-verdict-bot"
    telegram_bot: str = "@Gartleyy_bot"
    telegram_chat_id: str = "1273979711"
    webhook_url: str = "https://script.google.com/macros/s/AKfycbx0M21chsQ_k-a5SWbM6KbZmzlN81I32DZBO520ylh9iriUtlS-WUlkxsXlkjdR7hUE/exec"
    schedule_cron: str = "0 0,4,8,12,16,20 * * * (Every 4H UTC)"
    capital_mandate: str = "SPOT SWING CONFLUENCE RADAR (NON-LEVERAGED)"


# ============================================================================
# SPECIAL TAB [S4]: PATTERN INVALIDATION, LIQUIDITY SWEEP & SFP TRAP RADAR
# ============================================================================

class PatternType(str, Enum):
    """Classical chart pattern geometry classified as liquidity magnets."""

    HEAD_AND_SHOULDERS = "HEAD_AND_SHOULDERS"
    INVERSE_HEAD_AND_SHOULDERS = "INVERSE_HEAD_AND_SHOULDERS"
    DOUBLE_BOTTOM = "DOUBLE_BOTTOM"
    DOUBLE_TOP = "DOUBLE_TOP"
    BULL_FLAG_CONSOLIDATION = "BULL_FLAG_CONSOLIDATION"
    BEAR_FLAG_CONSOLIDATION = "BEAR_FLAG_CONSOLIDATION"
    RANGE_SUPPORT_EXTREME = "RANGE_SUPPORT_EXTREME"
    RANGE_RESISTANCE_EXTREME = "RANGE_RESISTANCE_EXTREME"
    ASIA_SESSION_HIGH = "ASIA_SESSION_HIGH"
    ASIA_SESSION_LOW = "ASIA_SESSION_LOW"


class TrapState(str, Enum):
    """3-State Microstructure Trap Finite State Machine."""

    STATE_0_COMPRESSION = "STATE 0: COMPRESSION (Building OI)"
    STATE_1_BOUNDARY_SWEEP = "STATE 1: BOUNDARY BREACH & SWEEP"
    STATE_2_SFP_RECLAIM_TRIGGERED = "STATE 2: SFP RECLAIM & ABSORPTION (TRIGGER)"
    NEUTRAL_OBSERVATION = "NEUTRAL OBSERVATION"


@dataclass
class PatternBoundaryItem:
    """Registered classical pattern boundary level and liquidity proximity."""

    pattern_name: str  # e.g., "1H Head & Shoulders Neckline"
    pattern_type: PatternType
    boundary_level: float  # Price level where retail orders cluster
    sweep_wick_extreme: float  # Extreme wick reached during sweep
    distance_pct: float  # (Current - Boundary) / Boundary * 100
    distance_atr: float  # Distance in 1H ATR multiples
    status: str  # "COMPRESSION", "SWEEPING", "SFP RECLAIMED", "UNTESTED"
    trap_bias: str  # "BULLISH (BEAR TRAP)", "BEARISH (BULL TRAP)", "NEUTRAL"
    liquidation_tier: str = "HIGH DENSITY CLUSTER"


@dataclass
class FairValueGapItem:
    """3-Bar Displacement Imbalance (Fair Value Gap) and Consequent Encroachment."""

    id: int
    direction: str  # "BULLISH" or "BEARISH"
    timeframe: str  # "15m" or "1H"
    top_price: float
    bottom_price: float
    ce_midpoint: float  # Consequent Encroachment (50% level)
    gap_pct: float
    status: str  # "UNMITIGATED" or "PARTIALLY_MITIGATED"
    distance_pct: float  # (Current - ce_midpoint) / ce_midpoint * 100


@dataclass
class TrapTradePlan:
    """Actionable asymmetric execution parameters for trapped pattern reclaims."""

    direction: str  # "LONG (BEAR TRAP SQUEEZE)" or "USDT HEDGE (BULL TRAP)"
    entry_price: float
    stop_loss: float
    tp1_poc: float
    tp2_opposite_boundary: float
    risk_dollars: float
    reward_dollars: float
    rr_ratio: float
    invalidation_summary: str


@dataclass
class TrapRadarEvaluation:
    """Unified evaluation for Special Tab [S4]: Pattern Invalidation, Liquidity Sweep & SFP Trap Desk."""

    timestamp_utc: str
    spot_price: float
    active_trap_state: TrapState
    active_trap_signal: str  # "BEAR TRAP (LONG SQUEEZE TRIGGER)", "BULL TRAP (USDT HEDGE)", "COMPRESSION", "MONITORING"
    rolling_1m_cvd: float
    rolling_5m_cvd: float
    rolling_15m_cvd: float
    oi_15m_delta_pct: float
    oi_1h_delta_pct: float
    oi_surge_flag: bool  # True if dOI >= 0.40%
    passive_absorption_flag: bool  # True if high CVD fails to displace price
    absorption_divergence_ratio: float  # |CVD| / (|Price Change %| + 1e-6)
    active_patterns: List[PatternBoundaryItem] = field(default_factory=list)
    active_fvgs: List[FairValueGapItem] = field(default_factory=list)
    asia_high: float = 0.0
    asia_low: float = 0.0
    asia_high_swept: bool = False
    asia_low_swept: bool = False
    trade_plan: Optional[TrapTradePlan] = None
    plain_english_summary: str = ""
    quantitative_takeaway: str = ""


# ==============================================================================
# SPECIAL TAB [S5]: TERMINAL EXHAUSTION & DELTA DIVERGENCE RADAR MODELS
# ==============================================================================

class ExhaustionRegime(str, Enum):
    """Regime state of market trend momentum maturity and exhaustion."""

    MOMENTUM_HEALTHY = "MOMENTUM HEALTHY (Trend Intact)"
    LATE_CYCLE_STRAIN = "LATE CYCLE STRAIN (Momentum Deceleration)"
    TERMINAL_EXHAUSTION_ARMED = "TERMINAL EXHAUSTION ARMED (TD-9 + CVD Divergence)"
    ACTIVE_REVERSAL_TRIGGER = "ACTIVE REVERSAL TRIGGER (Climax Reversal Confirmed)"


@dataclass
class TDSignal:
    """Tom DeMark (TD) Sequential Setup and exhaustion countdown metrics."""

    horizon: str  # "1H" or "4H"
    setup_count: int  # 1 to 9
    direction: str  # "BEARISH_EXHAUSTION" (Price surging into top) or "BULLISH_EXHAUSTION" (Price falling into bottom) or "NEUTRAL"
    is_perfected: bool  # True if bar 8 or 9 high/low exceeds bars 6 & 7
    status: str  # "PERFECTED", "ARMED (9/9)", "COUNTING", "NEUTRAL"
    invalidation_level: float = 0.0


@dataclass
class CVDDivergenceItem:
    """Cumulative Volume Delta (CVD) vs. Price fractal divergence."""

    horizon: str  # "15m", "1H", "4H"
    divergence_type: str  # "REGULAR_BEARISH", "REGULAR_BULLISH", "HIDDEN_BEARISH", "HIDDEN_BULLISH", "NONE"
    price_extrema: str  # e.g. "Higher High ($81,300 vs $80,900)"
    cvd_extrema: str  # e.g. "Lower High (-35 BTC vs +120 BTC)"
    spot_delta: float
    perp_delta: float
    significance: str  # "CRITICAL DIVERGENCE", "MODERATE", "ABSORPTION", "NONE"


@dataclass
class ExhaustionTradePlan:
    """Actionable asymmetric counter-trend / mean-reversion trade plan."""

    direction: str  # "SHORT (WAVE 5 EXHAUSTION SQUEEZE)" or "LONG (WAVE C CLIMAX REVERSAL)"
    entry_price: float
    stop_loss: float
    tp1_fast_mean: float  # e.g. 1H POC or 20 EMA
    tp2_value_poc: float  # Composite POC or Value Area Boundary
    risk_dollars: float
    reward_dollars: float
    rr_ratio: float
    invalidation_summary: str


@dataclass
class ExhaustionRadarEvaluation:
    """Unified evaluation for Special Tab [S5]: Terminal Exhaustion & Delta Divergence Radar."""

    timestamp_utc: str
    spot_price: float
    exhaustion_regime: ExhaustionRegime
    exhaustion_score: float  # 0.0 to 100.0 (Higher = more extreme terminal exhaustion)
    active_exhaustion_signal: str
    td_1h: TDSignal
    td_4h: TDSignal
    divergences: List[CVDDivergenceItem] = field(default_factory=list)
    oi_climax_pct: float = 0.0
    oi_climax_flag: bool = False
    funding_climax_flag: bool = False
    current_funding_pct: float = 0.0
    trade_plan: Optional[ExhaustionTradePlan] = None
    plain_english_summary: str = ""
    quantitative_takeaway: str = ""



@dataclass
class EMAStrategySnapshot:
    """Unified telemetry snapshot for the Industrial 3-EMA (Daily/4H) Trend & Pullback System."""

    daily_regime: str = "NEUTRAL"
    daily_ema_20: float = 0.0
    daily_ema_50: float = 0.0
    daily_ema_200: float = 0.0
    daily_ema_200_slope: float = 0.0
    daily_adx: float = 0.0
    ema_4h_9: float = 0.0
    ema_4h_20: float = 0.0
    ema_4h_50: float = 0.0
    ema_4h_200: float = 0.0
    adx_4h: float = 0.0
    trend_quality_pass: bool = False
    pullback_zone_active: bool = False
    rejection_active: bool = False
    positioning_confirmations_met: int = 0
    positioning_pass: bool = False
    trigger_active: bool = False
    setup_status: str = "NO_SETUP"
    suggested_atr_stop: float = 0.0
    suggested_risk_pct: float = 0.75
    summary_text: str = ""


@dataclass
class SignalEvaluation:
    """Output of the 4-Gate State Machine and 0-100 Confluence Scorer."""

    timestamp_utc: str
    regime: MarketRegime
    gate_state: ExecutionGateState
    confluence_score: float
    location_score: float
    flow_score: float
    derivatives_score: float
    trigger_score: float
    active_horizon: str
    current_price: float
    c_vah: float
    c_poc: float
    c_val: float
    primary_lvn: Optional[float]
    support_hvn: Optional[float]
    atr_1h: float
    atr_4h: float
    distance_to_val_pct: float
    distance_to_val_atr: float
    va_position_pct: float = 0.0
    is_mid_range_chop: bool = False
    is_reclaim_candle: bool = False
    hard_veto_triggered: bool = False
    veto_reasons: List[str] = field(default_factory=list)
    rationale_notes: List[str] = field(default_factory=list)
    trade_plan: Optional[TradePlan] = None
    fsm_instance_id: Optional[str] = None
    fsm_state: Optional[str] = None
    fsm_bars_elapsed: int = 0
    fsm_max_bars: int = 12
    fsm_retest_band_low: float = 0.0
    fsm_retest_band_high: float = 0.0
    fsm_invalidation_level: float = 0.0
    fsm_suggested_stop: float = 0.0
    fsm_direction: Optional[str] = None
    fsm_status_summary: str = ""
    ema_strategy: Optional[EMAStrategySnapshot] = None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["regime"] = self.regime.value
        data["gate_state"] = self.gate_state.value
        return data
