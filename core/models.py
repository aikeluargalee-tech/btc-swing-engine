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



    # True when taker_buy_volume is a candle-body estimate (not measured taker flow).



    # Estimated perp bars are dropped by StateStore.set_klines and never feed CVD/regime/scoring.



    estimated: bool = False







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



class LiquidationWindow:



    long_usd: float = 0.0



    short_usd: float = 0.0



    total_usd: float = 0.0



    long_count: int = 0



    short_count: int = 0



    dominant_side: str = "NEUTRAL"











@dataclass



class PostFlushStructure:



    status: str = "NONE"



    stabilisation_confirmed: bool = False



    stopped_making_lower_lows: bool = False



    higher_low_formed: bool = False



    break_prior_structure_high: bool = False



    spot_volume_expanded: bool = False



    volume_ratio: float = 1.0











@dataclass



class LiquidationDetectorReport:



    timestamp_utc: str = ""



    timestamp_ms: int = 0



    verdict: str = "STANDBY"



    verdict_detail: str = ""



    primary_classification: str = "NORMAL"



    magnitude_tier: str = "NORMAL"



    liquidation_multiple_24h: float = 0.0



    directional_classification: str = "NEUTRAL"



    windows: Dict[str, LiquidationWindow] = field(default_factory=dict)



    post_flush_price_structure: Optional[PostFlushStructure] = None



    is_stale: bool = False



    is_available: bool = False



    source_file: str = ""
    # Rich Telemetry for Demand Zone & Context
    demand_zone_status: str = "N/A"
    demand_zone_lower: float = 0.0
    demand_zone_upper: float = 0.0
    demand_zone_dist_lower_pct: float = 0.0
    demand_zone_dist_upper_pct: float = 0.0
    open_interest_contracts: float = 0.0
    funding_rate: float = 0.0
    funding_status: str = ""











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



    liquidation_report: Optional[LiquidationDetectorReport] = None











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



class TellTaleBarResult:



    timeframe: str = "15m"



    open_time: str = ""



    close: float = 0.0



    open: float = 0.0



    high: float = 0.0



    low: float = 0.0



    volume: float = 0.0



    baseline_volume: float = 0.0



    red: bool = False



    green: bool = False



    relvol: float = 0.0



    body_range: float = 0.0



    is_selling_climax: bool = False



    is_buying_climax: bool = False

    is_elevated_volume: bool = False











@dataclass



class TellTaleEvaluation:



    timestamp_utc: str = ""



    bar_15m: Optional[TellTaleBarResult] = None



    bar_5m: Optional[TellTaleBarResult] = None



    is_selling_climax: bool = False



    is_buying_climax: bool = False



    disruption_detected: bool = False



    climax_type: str = "NONE"



    plain_status: str = "NORMAL ORDER FLOW"











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



    tell_tale: Optional[TellTaleEvaluation] = None















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











# ============================================================================



# TAB [0]: BTC SPOT SWING SCREENING & ALERT ENGINE



# (Macro Regime Gate -> Weekly Liquidity Sweep/Reclaim -> Triple-Barrier Risk)



# ============================================================================







@dataclass



class SpotSwingMacroGate:



    """Module B: Daily macro regime gate (trend baseline + Bollinger-width squeeze)."""







    bar_ts_ms: int = 0              # open time of the last CLOSED daily bar used



    close: float = 0.0



    ema50: float = 0.0



    ema200: float = 0.0



    trend_pass: bool = False



    bbw: float = 0.0



    bbw_percentile: float = 1.0     # 0..1 rolling-rank of current BBW



    compression_pass: bool = False



    squeeze_lookback_bars: int = 1  # 1 = strict current bar (spec); N = any of last N bars



    macro_approved: bool = False











@dataclass



class SpotSwingSetup:



    """Module C: Weekly anchors + 4H sweep / reclaim / volume confirmation."""







    bar_ts_ms: int = 0              # open time of the last CLOSED 4H bar evaluated



    close: float = 0.0



    volume: float = 0.0



    vol_sma3: float = 0.0



    pwl: float = 0.0



    pwh: float = 0.0



    week_start_ms: int = 0          # Monday 00:00 UTC of the CURRENT (incomplete) week



    sweep_detected: bool = False



    sweep_low: float = 0.0



    sweep_bar_ts_ms: int = 0        # open time of the 4H bar that printed sweep_low



    reclaim_confirmed: bool = False



    volume_confirmed: bool = False



    signal_active: bool = False     # raw spec signal: sweep AND reclaim AND volume



    is_fresh: bool = False          # raw signal AND sweep is newer than the last traded sweep



    anchors_ready: bool = False











@dataclass



class SpotSwingRisk:



    """Module D: ATR stop, fixed-risk volatility-adjusted spot sizing, triple barriers."""







    entry: float = 0.0



    stop: float = 0.0



    atr14: float = 0.0



    stop_distance: float = 0.0



    stop_distance_pct: float = 0.0



    equity_usd: float = 0.0



    risk_pct: float = 1.0



    risk_budget_usd: float = 0.0



    qty_btc_uncapped: float = 0.0



    qty_btc: float = 0.0



    notional_usd: float = 0.0



    equity_alloc_pct: float = 0.0



    spot_capped: bool = False       # True when the 1%-risk size exceeded 100% of equity



    realized_risk_usd: float = 0.0  # qty * stop_distance (== budget unless capped)



    tp1: float = 0.0                # +2.0R partial exit



    tp2_pwh: float = 0.0            # structural target



    tp2_inside_tp1: bool = False    # PWH sits at/below +2R (target ordering warning)



    tp1_fraction: float = 0.5



    time_stop_ts_ms: int = 0
    tp_3r: float = 0.0                # +3.0R (1:3 RRR target)
    rrr_to_pwh: float = 0.0           # R:R to PWH
    rrr_to_magnet: float = 0.0        # R:R to Short-Liq Magnet
    rrr_meets_min: bool = False       # True when R:R >= 3.0
    max_entry_for_3r: float = 0.0     # Max entry price that preserves >= 1:3 RRR
    short_liq_magnet: float = 0.0     # Nearest dense short-liq cluster above











@dataclass



class SpotSwingTrade:



    """Persisted lifecycle of one alerted swing: OPEN_FULL -> TP1_HIT_RUNNER -> CLOSED."""







    setup_id: str



    status: str                     # OPEN_FULL | TP1_HIT_RUNNER | CLOSED



    entry_ts_ms: int                # open time of the reclaim 4H bar (signal bar)



    entry: float



    initial_stop: float



    current_stop: float



    tp1: float



    tp2: float



    qty_btc: float



    time_stop_ts_ms: int



    sweep_bar_ts_ms: int



    last_processed_bar_ts_ms: int



    tp1_hit: bool = False



    closed_reason: str = ""         # STOP_LOSS | BREAKEVEN_STOP | TP2_PWH | TIME_STOP



    exit_price: float = 0.0



    exit_ts_ms: int = 0



    realized_r: float = 0.0











@dataclass
class SpotSwingMagnetProtocol:
    """Daily Liquidation Magnet Protocol (Master Prompt Steps 1-4) + Tight RRR 1:3 Money Management."""

    # Step 1: Data Gathering & Key Levels
    current_price: float = 0.0
    sma50_1d: float = 0.0
    ema50_1d: float = 0.0
    sma50_slope_5d_pct: float = 0.0
    range_high_30d: float = 0.0
    range_low_30d: float = 0.0
    range_pivot: float = 0.0
    range_pos_pct: float = 50.0          # 0% = 30D low, 100% = 30D high

    short_liq_magnet: float = 0.0        # Nearest dense short-liq cluster above price
    short_liq_distance_pct: float = 0.0
    short_liq_size_label: str = "Data unavailable"
    short_liq_source: str = "[EST. SWING LIQ POOL]"

    long_liq_magnet: float = 0.0         # Nearest dense long-liq cluster below price
    long_liq_distance_pct: float = 0.0
    long_liq_size_label: str = "Data unavailable"
    long_liq_source: str = "[EST. SWING LIQ POOL]"

    cum_liq_24h_summary: str = "Data unavailable"

    # Positioning Snapshot
    oi_trend: str = "Flat"               # Rising / Falling / Flat + change
    oi_change_24h_pct: float = 0.0
    oi_change_4h_pct: float = 0.0
    oi_btc: float = 0.0
    oi_interpretation: str = "Neutral"

    funding_rate_8h_pct: float = 0.0
    funding_status: str = "Neutral"      # Positive / Neutral / Negative + rate

    spot_cvd_24h_btc: float = 0.0
    perp_cvd_24h_btc: float = 0.0
    spot_cvd_4h_btc: float = 0.0
    perp_cvd_4h_btc: float = 0.0
    spot_cvd_assessment: str = "Mixed"   # Confirming / Not confirming / Mixed
    spot_cvd_confirming: bool = False

    headline_filter: str = "None significant"

    # Step 2: Regime Confirmation
    regime: str = "Range"                # Range / Possible Transition / Trend
    regime_detail: str = ""
    has_daily_hh_hl: bool = False
    has_daily_lh_ll: bool = False

    # Step 3 & Money Management: Tight RRR 1:3 Geometry
    min_required_rrr: float = 3.0
    entry_ref: float = 0.0
    invalidation_level: float = 0.0      # Range pivot or 50DMA
    hard_stop_price: float = 0.0
    risk_distance_usd: float = 0.0
    risk_distance_pct: float = 0.0
    reward_to_magnet_usd: float = 0.0
    reward_to_magnet_pct: float = 0.0
    rrr_to_magnet: float = 0.0           # Reward / Risk to Short-Liq Magnet
    rrr_pass: bool = False               # True when rrr_to_magnet >= 3.0
    tp_3r_price: float = 0.0             # Entry + 3.0 * Risk
    max_entry_for_3r: float = 0.0        # (Short_Liq_Magnet + 3 * Hard_Stop) / 4
    recommended_qty_btc: float = 0.0
    recommended_notional_usd: float = 0.0
    recommended_risk_usd: float = 0.0
    equity_alloc_pct: float = 0.0
    spot_capped: bool = False

    # Step 4: Strict Verdict Output
    verdict: str = "Do Nothing"          # Hold / Partial Profit into Magnet / Reduce or Exit / Do Nothing / Rare Add Consideration
    confidence: str = "Medium"           # High / Medium / Low
    primary_reason: str = ""
    invalidation_text: str = ""
    actionable_note: str = ""


@dataclass



class SpotSwingEvaluation:



    """Unified evaluation rendered by Tab [0] and exported to alerts / AI packet."""







    timestamp_utc: str



    spot_price: float



    verdict: str                    # e.g. "FROZEN (100% CASH)", "SETUP ARMED", "NEW LONG SETUP"



    traffic_light: str              # GREEN | BLUE | YELLOW | RED



    data_ready: bool



    data_notes: List[str] = field(default_factory=list)



    macro: Optional[SpotSwingMacroGate] = None



    setup: Optional[SpotSwingSetup] = None



    risk: Optional[SpotSwingRisk] = None



    trade: Optional[SpotSwingTrade] = None



    recent_events: List[str] = field(default_factory=list)



    alerts_enabled: bool = False



    read_only: bool = False



    plain_english_summary: str = ""



    equity_usd: float = 0.0



    risk_pct: float = 1.0
    magnet: Optional[SpotSwingMagnetProtocol] = None


# ============================================================================
# INTRA-CANDLE FOOTPRINT & ORDER FLOW MICROSTRUCTURE MODELS
# ============================================================================


@dataclass
class FootprintClusterRow:
    """Individual price bucket ($25 tick) within a Footprint bar."""

    price: float
    bid_vol: float = 0.0          # Aggressive sell volume hitting the bid
    ask_vol: float = 0.0          # Aggressive buy volume lifting the ask
    delta: float = 0.0            # ask_vol - bid_vol
    total_vol: float = 0.0        # ask_vol + bid_vol
    is_poc: bool = False          # Highest volume price bin in the bar
    is_battle_zone: bool = False  # Both bid and ask volume exceed threshold
    is_buy_imbalance: bool = False   # Diagonal ask >= 3.0 * bid
    is_sell_imbalance: bool = False  # Diagonal bid >= 3.0 * ask
    is_stacked_buy: bool = False     # Part of 3+ consecutive buy imbalances
    is_stacked_sell: bool = False    # Part of 3+ consecutive sell imbalances
    tag: str = ""                    # Display tag e.g. "[POC]", "[BATTLE]", "[STACK BUY]", "[TRAP SELL]"


@dataclass
class FootprintBarData:
    """15-Minute Footprint Bar containing intra-candle price clusters."""

    start_ts_ms: int
    end_ts_ms: int
    open: float = 0.0
    high: float = 0.0
    low: float = 0.0
    close: float = 0.0
    volume: float = 0.0
    net_delta: float = 0.0
    poc_price: float = 0.0
    poc_volume: float = 0.0
    clusters: Dict[float, FootprintClusterRow] = field(default_factory=dict)
    is_closed: bool = False
    has_wick_absorption: bool = False
    wick_absorption_price: float = 0.0
    has_upper_wick_exhaustion: bool = False
    upper_wick_exhaustion_price: float = 0.0
    has_stacked_buy: bool = False
    has_stacked_sell: bool = False
    has_battle_zone: bool = False
    auction_completed: bool = True


@dataclass
class FootprintEvaluation:
    """Microstructure Footprint Evaluation & 3-Gate Execution Funnel."""

    timestamp_utc: str = ""
    current_price: float = 0.0
    direction: str = "NEUTRAL"           # "ACCUMULATE_BUY", "DISTRIBUTE_SELL", "OBSERVATION"
    active_bar_delta: float = 0.0
    prev_bar_delta: float = 0.0
    delta_flipped_bullish: bool = False  # prev < 0 and active > 0
    delta_flipped_bearish: bool = False  # prev > 0 and active < 0
    gate1_level_tap: bool = False        # Tapped key support or resistance level
    gate1_level_type: str = ""           # "SUPPORT" or "RESISTANCE"
    gate1_tapped_level_name: str = ""
    gate1_tapped_level_price: float = 0.0
    gate2_absorption: bool = False       # Lower-wick seller absorption OR upper-wick buyer exhaustion
    gate2_detail: str = ""
    gate3_delta_flip: bool = False       # 15m delta flip in trade direction confirmed

    # 4-Gate Quantitative Confluence (Phase 1 Specification)
    gate1_macro_tap: bool = False        # Gate 1: Macro Structure (30D/7D HVN, POC, or Liq Magnet floor)
    gate2_positioning_crowded: bool = False  # Gate 2: Positioning (Funding Rate <= 15th pctile OR Spot CVD holding)
    gate2_positioning_detail: str = ""
    gate3_wick_absorption: bool = False  # Gate 3: Footprint Micro-Veto (Lower-Wick Absorption OR Battle Zone)
    gate3_wick_detail: str = ""
    gate4_delta_flip: bool = False       # Gate 4: Tactical Trigger (15m Positive Delta Flip)
    stacked_imbalances_count: int = 0
    active_battle_zone: float = 0.0
    funding_rate_pct: float = 0.0
    funding_pctile_short: float = 0.0
    oi_4h_change_pct: float = 0.0
    cvd_absorption_status: str = ""

    all_gates_pass: bool = False
    signal_status: str = "OBSERVATION"   # "OBSERVATION", "ARMED", "TRIGGERED_ACCUMULATE", "TRIGGERED_DISTRIBUTE"
    entry_price: float = 0.0
    stop_loss: float = 0.0
    tp1_1to2: float = 0.0
    tp2_1to3: float = 0.0
    rr_to_tp1: float = 2.0
    rr_to_tp2: float = 3.0
    rebuy_target_price: float = 0.0      # For distribution: rebuy target at support
    rebuy_target_name: str = ""
    target_coin_yield_pct: float = 0.0   # (sell_price - rebuy_price) / rebuy_price * 100%
    harvest_tranche_pct: float = 50.0    # 50% staged trim or 100% full rotation

    # Institutional Gate Hardening & Ergonomic Telemetry
    auction_completed: bool = True
    bar_poc_reclaimed: bool = True
    cascade_velocity_veto: bool = False
    ntz_veto_active: bool = False
    ntz_status_text: str = "ALL CLEAR (8A-8F PASS)"
    cpi_usd: float = 0.0
    cpi_pct: float = 0.0
    cpi_zscore: float = 0.0
    daily_vwap: float = 0.0
    asia_high: float = 0.0
    asia_low: float = 0.0
    sma_200_1d: float = 0.0
    above_200d_sma: bool = True

    # Deterministic Capital Preservation Order Card Geometry
    reference_equity_usd: float = 100000.0
    risk_budget_usd: float = 1000.0
    raw_position_btc: float = 0.0
    final_position_btc: float = 0.0
    final_notional_usd: float = 0.0
    effective_risk_usd: float = 0.0
    notional_clamped: bool = False
    tp1_fair_value_poc: float = 0.0
    tp2_short_liq_magnet: float = 0.0

    active_ladder_rows: List[FootprintClusterRow] = field(default_factory=list)
    recent_bars_deltas: List[float] = field(default_factory=list)
    summary_notes: List[str] = field(default_factory=list)

    # 3-Variant Parallel Forward Test Scorecards
    forward_test_scorecards: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ForwardTestTrade:
    """Atomic record of a simulated forward-test trade."""

    trade_id: str
    variant_id: str  # "OPT_1_PURE_FP", "OPT_2_4GATE", "OPT_3_INSTITUTIONAL"
    direction: str = "BUY"
    entry_time_utc: str = ""
    entry_price: float = 0.0
    stop_loss: float = 0.0
    tp1_price: float = 0.0
    tp2_price: float = 0.0
    size_btc: float = 0.0
    remaining_size: float = 0.0
    notional_usd: float = 0.0
    risk_usd: float = 0.0
    state: str = "OPEN"  # "OPEN", "TP1_HIT", "CLOSED_STOP", "CLOSED_TP2", "CLOSED_TIMEOUT"
    tp1_hit: bool = False
    already_realized_pnl: float = 0.0
    exit_time_utc: str = ""
    exit_price: float = 0.0
    total_realized_pnl: float = 0.0
    unrealized_pnl_usd: float = 0.0
    notes: str = ""
    level_name: str = ""


@dataclass
class VariantScorecard:
    """Performance telemetry tracking for a forward test variant."""

    variant_id: str
    display_name: str
    timeframe_desc: str
    status: str = "OBSERVING"  # "OBSERVING", "ARMED", "IN_POSITION"
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate_pct: float = 0.0
    realized_pnl_usd: float = 0.0
    unrealized_pnl_usd: float = 0.0
    peak_pnl_usd: float = 0.0
    max_drawdown_usd: float = 0.0
    max_drawdown_pct: float = 0.0
    active_trade: Optional[ForwardTestTrade] = None
    last_closed_trade_summary: str = ""


# Type aliases conforming to Technical Specification
PriceCluster = FootprintClusterRow
FootprintBar = FootprintBarData




@dataclass
class SLSPKeyLevel:
    """A scored horizontal support or resistance level (SLSP Section 4)."""

    price_min: float
    price_max: float
    center_price: float
    level_type: str  # "SUPPORT" or "RESISTANCE"
    strength: int  # 1 to 5
    touch_count: int = 2
    is_round_number: bool = False
    is_hvn: bool = False
    is_swing_pivot: bool = True
    description: str = ""


@dataclass
class SLSPTradeSetup:
    """Trade plan generated by SLSP v1.0 and 4-in-1 confluence (SLSP Sections 5, 6, 7)."""

    is_valid: bool = False
    direction: str = "LONG"  # "LONG", "SHORT", "STAND_ASIDE"
    regime: str = "UPTREND"  # "UPTREND", "DOWNTREND", "RANGE", "UNCLEAR"
    level: Optional[SLSPKeyLevel] = None
    entry_price: float = 0.0
    stop_loss: float = 0.0
    risk_per_coin: float = 0.0
    risk_pct: float = 0.75
    position_size_btc: float = 0.0
    notional_value_usd: float = 0.0
    tp1_price: float = 0.0  # +1.5R
    tp2_price: float = 0.0  # +2.5R
    breakeven_trigger_price: float = 0.0  # +1.0R
    breakeven_active: bool = False
    obstacle_detected: bool = False
    obstacle_r: float = 999.0
    obstacle_description: str = ""
    rejection_candle_type: str = "NONE"  # "PINBAR", "ENGULFING", "MOMENTUM_CLOSE", "NONE"
    rejection_wick_ratio: float = 0.0
    rejection_volume_ratio: float = 0.0
    invalidation_rule: str = "Close beyond stop on 4H"
    confluence_notes: List[str] = field(default_factory=list)


@dataclass
class SLSPEvaluation:
    """Unified evaluation for Tab [13]: Structure + Level Swing Protocol (SLSP v1.0) & 4-in-1 Integration."""

    timestamp_utc: str = ""
    spot_price: float = 0.0
    regime: str = "UPTREND"  # "UPTREND", "DOWNTREND", "RANGE", "UNCLEAR"
    regime_reason: str = ""
    key_levels: List[SLSPKeyLevel] = field(default_factory=list)
    nearest_support: Optional[SLSPKeyLevel] = None
    nearest_resistance: Optional[SLSPKeyLevel] = None
    active_setup: Optional[SLSPTradeSetup] = None
    trade_state: str = "SCANNING"  # "SCANNING", "VALUE_ZONE_WATCH", "REJECTION_ARMED", "TRIGGER_FIRED", "IN_POSITION", "STAND_ASIDE"
    mode: str = "SEMI_AUTO"  # "ALERT_ONLY", "SEMI_AUTO"
    circuit_breaker_active: bool = False
    circuit_breaker_reason: str = ""
    daily_loss_pct: float = 0.0
    weekly_loss_pct: float = 0.0
    # Component 2 (File B: Industrial 3-EMA) Telemetry:
    ema_3_regime: str = "NEUTRAL"
    ema_3_slope_200: float = 0.0
    ema_3_value_zone_active: bool = False
    ema_3_adx: float = 0.0
    ema_3_positioning_met: int = 0
    # Component 3 (Project 7: Tell-Tale Climax) Telemetry:
    tell_tale_status: str = "NORMAL"
    tell_tale_veto: bool = False
    tell_tale_relvol_15m: float = 0.0
    tell_tale_relvol_5m: float = 0.0
    # Component 4 (Project 8: Liquidation Flush Detector) Telemetry:
    liq_flush_status: str = "STANDBY"
    liq_flush_detected: bool = False
    liq_flush_wick_ratio: float = 0.0
    liq_flush_oi_delta: float = 0.0
    liq_detector_report: Optional[LiquidationDetectorReport] = None
    # Synthesized Confluence:
    confluence_score: int = 0  # 0 to 100
    plain_english_summary: str = ""
    decision_log: List[str] = field(default_factory=list)


@dataclass
class PatternCandidate:
    """Individual detected classic chart pattern candidate."""

    pattern: str = ""
    bias: str = "Neutral"  # "Bullish", "Bearish", "Neutral"
    confidence: float = 0.0  # 0.0 to 1.0
    timeframe: str = "1h"  # "1h" or "4h"
    neckline: Optional[float] = None
    floor_or_roof: Optional[float] = None
    details: Dict[str, Any] = field(default_factory=dict)
    high_slope: Optional[float] = None
    low_slope: Optional[float] = None


@dataclass
class PatternEvaluation:
    """Complete evaluation state for Classic Chart Pattern & Candlestick Geometry."""

    timestamp_utc: str = ""
    spot_price: float = 0.0
    structure_trend: str = "Ranging"  # "Bullish structure", "Bearish structure", "Ranging"
    top_pattern: Optional[PatternCandidate] = None
    candidates: List[PatternCandidate] = field(default_factory=list)
    multi_timeframe_aligned: bool = False
    active_bias: str = "Neutral"
    neckline_trigger: Optional[float] = None
    invalidation_level: Optional[float] = None
    trigger_status: str = "STANDBY"  # "CONFIRMED_BREAKOUT", "PENDING_BREAKOUT", "INVALIDATED", "CONSOLIDATING", "STANDBY"
    tactical_playbook: str = ""
    html_chart_path: str = ""

