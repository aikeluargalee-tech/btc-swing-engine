"""Comprehensive Test Suite for B1 vs B2 Reconciliation & Data Integrity Audit Engine."""

import pytest
from datetime import datetime, timezone
from core.models import (
    B1TelemetrySnapshot,
    BTCMagnetEvaluation,
    BTCMagnetLevel,
    BTCMagnetRuleCheck,
)
from core.state_store import StateStore
from analytics.reconciliation_engine import (
    B1TelemetryParser,
    ReconciliationEngine,
    format_reconciliation_report,
)
from analytics.btc_magnet_engine import BTCMagnetEngine
from analytics.slsp_engine import SLSPEngine
from config.settings import DEFAULT_CONFIG


SAMPLE_B1_PROMPT_TEXT = """
INSTITUTIONAL BITCOIN (BTC) ORDER FLOW & LIQUIDATION TELEMETRY AUDIT
System: BTC Magnet Monitor | Verified Real-Time Feeds: Binance & Deribit
Mandate: SPOT-ONLY ROTATION (BTC / USDT). Zero borrowed leverage. Zero shorting.
Timestamp: 2026-11-10T04:29:59 UTC | Status: LIVE
================================================================================

[EXECUTIVE TRADING DIRECTIVE & SYSTEM CALL]:
• Engine Regime Diagnosis: Range / Liquidation Magnet (3/4 observations confirmed)
• Physical Microstructure Diagnosis: Positioning imbalance and forced liquidations dominate
• Recommended Spot Capital Rotation: USDT -> BTC
• Playbook Execution Protocol: Trade the Magnet: Buy Spot (0.75x)
• Prescribed Position Sizing: 0.75x (75% of deployable cash budget)
• Liquidation Sweep Engine (LSCE) Status: SWEEP_AND_RECLAIM_CONFIRMED
  └ Details: Lower liquidation shelf ($74,760) swept and reclaimed with positive spot absorption. Authorized 0.75x entry.
• Dual Inviolable Stop Architecture:
  ├ Structural Invalidation: 1-Hour candle close below $73,750.00 (Floor breakdown)
  └ Inviolable Disaster Hard Stop: $72,354.94 (3.30% distance) [Placed safely below 200D SMA ($73,196) & 25x shelf ($72,865)]
• Dominant Liquidation Magnet Target: Lower Long Sweep Magnet (LOWER (Immediate 24.5x / Ladder 1.70x; longs 64.9% crowded))
• Desk Risk Management Status: ✓ APPROVED (Within 1% Risk Budget) [Portfolio Risk Capped at 0.99%]

--------------------------------------------------------------------------------
SECTION 1 • PRICE BENCHMARKS & RANGE GEOMETRY (MACRO STRUCTURE)
--------------------------------------------------------------------------------
• Current BTC Spot Price: $74,827.09
• Daily VWAP (Anchored 00:00 UTC):   $74,951.20 [Price is -0.17% vs Daily VWAP]
• Weekly VWAP (Anchored Monday):     $74,733.95 [Price is +0.12% vs Weekly VWAP]
• Moving Averages: 20D EMA: $77,893.74 | 50D EMA: $79,146.11 | 200D SMA: $73,196.06
• 4-Hour Channel Range: $73,750 (Floor) to $75,568 (Ceiling) [Channel Width: 2.43%]

--------------------------------------------------------------------------------
SECTION 2 • ORDER FLOW & TAKER VOLUME DELTA (SPOT CVD)
--------------------------------------------------------------------------------
• 24h Spot Taker Volume: 14,851 BTC (Volume Ratio vs 20D MA: 1.02x)
• Spot CVD Ratio (Net Taker Buy / Sell Volume): 1.28 (>1.0 = Spot Bids Leading)

--------------------------------------------------------------------------------
SECTION 3 • DERIVATIVES POSITIONING & LEVERAGE CROWDING
--------------------------------------------------------------------------------
• 8-Hour Funding Rate: +0.0100% [ +10.95% Annualized ]
• Retail Account Long/Short Ratio: 1.85 (64.9% Longs vs 35.1% Shorts)
• Futures Basis (3-Month Annualized Premium): -1.20% (Calm / Inverted Basis)
• Immediate Tier Imbalance: Lower Long pool is 24.5x larger than Upper Shorts
  └ 100x Longs: $74,760 | Est. Pool: $102.8M vs 50-100x Shorts: $75,200 | Est. Pool: $4.2M
• Total Leverage Ladder Imbalance (10x to 100x): Total Lower Longs (~$354.0M) / Total Upper Shorts (~$215.0M) = 1.65x
"""


def _make_dummy_b2(
    spot_price: float = 74780.01,
    lsce_status: str = "UNTESTED",
    immediate_l_vol: float = 409.29,
    total_l_vol: float = 833.6,
    rotation: str = "BTC -> USDT",
    action: str = "Stand Aside (0.0x)",
    sizing_factor: float = 0.0,
) -> BTCMagnetEvaluation:
    now_utc = "2026-11-10 05:08:14 UTC"
    upper = BTCMagnetLevel(price=77024.20, dist_pct=3.00, usd_volume=242_610_000.0)
    lower = BTCMagnetLevel(price=73196.32, dist_pct=-2.12, usd_volume=immediate_l_vol * 1e6)

    return BTCMagnetEvaluation(
        timestamp_utc=now_utc,
        spot_price=spot_price,
        price_change_24h_pct=0.41,
        high_24h=75500.0,
        low_24h=73700.0,
        upper_magnet=upper,
        lower_magnet=lower,
        pull_direction="LOWER",
        pull_ratio=1.69,
        funding_rate_annual_pct=10.95,
        oi_delta_4h_pct=-0.12,
        market_regime="Range",
        verdict="SPEAK",
        verdict_badge="SWING EDGE PRESENT",
        headline="Downside Liquidation Magnet Active",
        body="Positioning is crowded long with $409.3M shelf untested below.",
        rule_subtitle="Lower Magnet Active",
        rules_passed_count=6,
        rule_checks=[
            BTCMagnetRuleCheck(1, "Clear Magnet", True, "Lower shelf $73,196"),
            BTCMagnetRuleCheck(2, "OI Velocity", True, "OI calm"),
            BTCMagnetRuleCheck(3, "Funding Carry", True, "+10.9%/yr"),
            BTCMagnetRuleCheck(4, "Regime", True, "Range"),
            BTCMagnetRuleCheck(5, "Spot Flow", True, "Neutral"),
            BTCMagnetRuleCheck(6, "Not Swept", True, "Untested"),
            BTCMagnetRuleCheck(7, "Conviction", True, "All passed"),
        ],
        magnet_summary_markdown="",
        regime_id="RANGE_LIQUIDATION_MAGNET",
        regime_name="Range / Liquidation Magnet",
        regime_diagnosis="Positioning imbalance and forced liquidations dominate",
        majority_score="4/4",
        majority_matches_count=4,
        matched_observations=[],
        all_observations=[
            ("Defined range (2.43% width) & ATR compressed 74.4%", True),
            ("Spot CVD neutral/balanced (Ratio 1.04)", True),
            ("Positioning crowded (L/S 1.85, funding 1.000%)", True),
            ("Clear liquidation clusters active above and below price", True),
        ],
        is_conflicted=False,
        lsce_status=lsce_status,
        lsce_cluster_tested="Lower Longs ($73,196)",
        lsce_sweep_depth_pct=2.12,
        lsce_reclaim_level=73196.32,
        lsce_spot_absorption="Pending",
        lsce_action_verdict="Lower pool ($73,196) is +2.12% away and untested. Maintain cash reserve.",
        immediate_ratio=1.69,
        immediate_l_vol=immediate_l_vol,
        immediate_u_vol=242.61,
        total_ladder_ratio=1.65,
        total_l_vol=total_l_vol,
        total_u_vol=215.0,
        six_factors={},
        levels_ladder={},
        sizing_factor=sizing_factor,
        action=action,
        rotation=rotation,
        entry_instruction="Price oscillating in range. Pending sweep confirmation.",
        structural_stop_price=73602.50,
        structural_stop_dist_pct=1.57,
        disaster_stop_price=71509.06,
        disaster_stop_dist_pct=4.37,
        risk_budget_pass=True,
    )


def test_b1_telemetry_parser():
    snapshot = B1TelemetryParser.parse_text(SAMPLE_B1_PROMPT_TEXT)
    assert snapshot.is_valid is True
    assert snapshot.spot_price == 74827.09
    assert snapshot.regime_name == "Range / Liquidation Magnet"
    assert snapshot.majority_score == "3/4"
    assert snapshot.rotation == "USDT -> BTC"
    assert snapshot.sizing_factor == 0.75
    assert snapshot.lsce_status == "SWEEP_AND_RECLAIM_CONFIRMED"
    assert snapshot.structural_stop == 73750.00
    assert snapshot.disaster_stop == 72354.94
    assert snapshot.immediate_ratio == 24.5
    assert snapshot.funding_rate_8h_pct == 0.0100
    assert snapshot.funding_rate_annual_pct == 10.95
    assert snapshot.long_short_ratio == 1.85


def test_module_a_ladder_math_fail():
    """Module A: Inviolable math law (Total Ladder must be >= Immediate Tier)."""
    # Create mathematically impossible B2: Total ($354M) < Immediate ($409.29M)
    b2_bad = _make_dummy_b2(immediate_l_vol=409.29, total_l_vol=354.0)
    engine = ReconciliationEngine()
    audit = engine.reconcile(None, b2_bad)

    assert audit.ladder_check_passed is False
    assert audit.verdict == "FAIL"
    assert audit.execution_authorization == "DENIED"
    assert audit.capital_allocation == 0.00
    assert audit.portfolio_rotation == "BTC -> USDT"
    assert any("MATHEMATICAL IMPOSSIBILITY IN B2" in r for r in audit.fail_reasons)


def test_module_b_funding_rate_normalization():
    """Module B: Funding rate normalization and formatting multiplier artifact detection."""
    b2 = _make_dummy_b2()
    engine = ReconciliationEngine()
    audit = engine.reconcile(SAMPLE_B1_PROMPT_TEXT, b2)

    # Multiplier warning should be present because B2 observations had 'funding 1.000%'
    assert any("multiplier artifact" in w for w in audit.warnings)
    table_items = [i for i in audit.discrepancy_table if "Funding" in i.metric]
    assert len(table_items) > 0
    assert table_items[0].severity == "WARNING"


def test_module_c_horizon_divergence():
    """Module C: Discloses micro (<0.5%) vs macro (>1.5%) horizon divergence."""
    b2 = _make_dummy_b2()
    engine = ReconciliationEngine()
    audit = engine.reconcile(SAMPLE_B1_PROMPT_TEXT, b2)

    table_items = [i for i in audit.discrepancy_table if "Geometry" in i.metric]
    assert len(table_items) > 0
    assert "MICRO_HORIZON" in table_items[0].b1_value
    assert "MACRO_HORIZON" in table_items[0].b2_value


def test_module_d_lsce_contradiction_lockout():
    """Module D: Contradictory LSCE sweep claim locks out execution to 0.00x / 100% USDT."""
    b2 = _make_dummy_b2(lsce_status="UNTESTED")
    engine = ReconciliationEngine()
    audit = engine.reconcile(SAMPLE_B1_PROMPT_TEXT, b2)

    assert audit.lsce_check_passed is False
    assert audit.verdict == "FAIL"
    assert audit.execution_authorization == "DENIED"
    assert audit.capital_allocation == 0.00
    assert audit.target_allocation == "100% USDT"
    assert audit.portfolio_rotation == "BTC -> USDT"
    assert audit.trading_status == "NO TRADE"
    assert any("CRITICAL LSCE CONTRADICTION" in r for r in audit.fail_reasons)


def test_module_e_asynchronous_delta():
    """Module E: Detects asynchronous snapshots (>15 minutes delta)."""
    b2 = _make_dummy_b2()
    # B1 is 2026-11-10T04:29:59 UTC, B2 is 2026-11-10 05:08:14 UTC (~38 min delta)
    engine = ReconciliationEngine(max_timestamp_delta_min=15.0)
    audit = engine.reconcile(SAMPLE_B1_PROMPT_TEXT, b2)

    assert any("Asynchronous snapshots" in w for w in audit.warnings)


def test_clean_synchronous_pass():
    """When both feeds are consistent, sweep verified or both untested, gate authorizes."""
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    b2 = _make_dummy_b2(
        spot_price=74800.0,
        lsce_status="UNTESTED",
        immediate_l_vol=409.29,
        total_l_vol=833.6,
        rotation="Remain USDT",
        action="Stand Aside (0.0x)",
        sizing_factor=0.0,
    )
    b2.timestamp_utc = now_str
    b2.all_observations = [("Observations clean", True)]

    # Clean synchronized B1 snapshot matching B2
    b1 = B1TelemetrySnapshot(
        raw_text="CLEAN_TEST",
        timestamp_utc=now_str,
        spot_price=74800.0,
        regime_name="Range / Liquidation Magnet",
        majority_score="4/4",
        rotation="Remain USDT",
        action="Stand Aside (0.0x)",
        sizing_factor=0.0,
        lsce_status="UNTESTED",
        structural_stop=73600.0,
        disaster_stop=71500.0,
        immediate_ratio=1.69,
        total_ladder_ratio=1.65,
        lower_immediate_pool_px=73196.0,
        lower_immediate_pool_usd=409_290_000.0,
        upper_immediate_pool_px=77024.0,
        upper_immediate_pool_usd=242_610_000.0,
        total_lower_usd=833_600_000.0,
        total_upper_usd=215_000_000.0,
        spot_cvd_ratio=1.04,
        funding_rate_8h_pct=0.0100,
        funding_rate_annual_pct=10.95,
        long_short_ratio=1.85,
        futures_basis_annual_pct=-1.20,
        is_valid=True,
    )

    engine = ReconciliationEngine()
    audit = engine.reconcile(b1, b2)

    assert audit.verdict == "PASS"
    assert audit.execution_authorization == "AUTHORIZED"
    assert len(audit.fail_reasons) == 0


def test_btc_magnet_engine_integration_lockout():
    """Verify BTCMagnetEngine automatically executes fail-closed lockout on contradictory B1."""
    store = StateStore()
    store.spot_price = 74800.0
    store.binance_spot_price = 74800.0
    store.b1_raw_telemetry = SAMPLE_B1_PROMPT_TEXT

    mag_engine = BTCMagnetEngine(DEFAULT_CONFIG)
    mag_eval = mag_engine.evaluate(store)

    assert mag_eval.reconciliation_auth == "DENIED"
    assert mag_eval.sizing_factor == 0.00
    assert mag_eval.rotation == "BTC -> USDT"
    assert mag_eval.verdict == "WAIT"
    assert mag_eval.verdict_badge == "DATA INTEGRITY LOCKOUT"
    assert "FAIL-CLOSED LOCKOUT" in mag_eval.entry_instruction
    assert store.reconciliation_evaluation is not None
    assert store.reconciliation_evaluation.execution_authorization == "DENIED"


def test_slsp_engine_integration_lockout():
    """Verify SLSPEngine honors Reconciliation Gate lockout and forces STAND_ASIDE / 100% USDT."""
    store = StateStore()
    store.spot_price = 74800.0
    store.binance_spot_price = 74800.0
    store.b1_raw_telemetry = SAMPLE_B1_PROMPT_TEXT

    # 1. Run BTCMagnetEngine first to generate evaluation & reconciliation audit
    mag_engine = BTCMagnetEngine(DEFAULT_CONFIG)
    mag_eval = mag_engine.evaluate(store)
    assert mag_eval.reconciliation_auth == "DENIED"

    # 2. Run SLSPEngine
    slsp_engine = SLSPEngine(DEFAULT_CONFIG)
    slsp = slsp_engine.evaluate(store, current_price=74800.0)

    assert slsp.trade_state == "STAND_ASIDE"
    assert slsp.macro_hard_lock_cash is True
    assert "RECONCILIATION GATE FAIL-CLOSED LOCKOUT" in slsp.macro_lock_reason


def test_format_reconciliation_report():
    """Verify report formatting produces valid ASCII markdown."""
    b2 = _make_dummy_b2()
    engine = ReconciliationEngine()
    audit = engine.reconcile(SAMPLE_B1_PROMPT_TEXT, b2)
    rep = format_reconciliation_report(audit)

    assert "# [R: RECONCILIATION] | B1 vs B2 DATA INTEGRITY AUDIT" in rep
    assert "DENIED" in rep
    assert "LOCKOUT DIRECTIVE" in rep
    assert "Module A" in rep
    # Ensure plain ASCII
    rep.encode("ascii")
