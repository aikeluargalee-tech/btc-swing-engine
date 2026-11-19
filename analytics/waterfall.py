"""Tab [W] Waterfall — single source of truth for the 5-pillar decision state.

Why this module exists
----------------------
The HUD (`ui/terminal_hud.py`) and the exported report
(`analytics/data_only_reports.build_tab_w_data_only_report`) both claimed to show
"Tab W", but each computed its own set of five pillars from different fields and
with different thresholds. The exported artefact therefore described a different
model from the screen it was copied out of, and neither could be checked against
the other.

Everything that decides the waterfall state now lives here exactly once.
The HUD renders it; the report serialises it. Neither may recompute a pillar.

State vocabulary (not an order instruction):
    RED_SYSTEMIC    non-trade-zone hazard active
    RED_STEALTH     spot CVD dumping while perp lifts
    RED_CROWDED     OI expanding into positive funding
    RED_US_SELLING  Coinbase premium at a deep discount away from the shelf
    GREEN           all five pillars aligned and asymmetry satisfied
    BLUE            sitting at the structural edge, trigger not yet fired
    AMBER           no edge - mid-range, or nothing measured
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

# --- thresholds, named so the report and the HUD cannot disagree about them ---
FUNDING_PASS_MAX_PCT = 0.010      # pillar 4: neutral-or-negative funding
FUNDING_CROWDED_MIN_PCT = 0.012   # pillar 4: crowded-long veto
OI_CROWDED_MIN_PCT = 2.5          # pillar 4: OI expansion threshold
EDGE_TOLERANCE_PCT = 1.5          # pillar 2: how close to cVAL counts as "at the edge"
STEALTH_SPOT_MAX_BTC = -50.0      # pillar 3: spot distribution size
STEALTH_PERP_MIN_BTC = 50.0       # pillar 3: perp absorption size
STEALTH_DIV_Z_MAX = -1.5          # pillar 3: divergence z
CPI_PASS_MIN_USD = 2.0            # pillar 3: US institutional bid
CPI_CAUTION_USD = -5.0            # pillar 3: mild US spot lag
CPI_VETO_USD = -50.0              # pillar 3: heavy US spot selling
RRR_MIN = 3.0                     # pillar 2: asymmetry to the liquidation magnet


@dataclass
class WaterfallState:
    """All five pillar booleans, the inputs behind them, and the resolved state."""

    state: str = "AMBER"
    binding_pillar: str = "PILLAR 2"

    # pillar booleans
    p1_macro: bool = False
    p2_structure: bool = False
    p3_flow: bool = False
    p4_leverage: bool = False
    p5_trigger: bool = False
    pillars_aligned: bool = False

    # raw inputs echoed for the exported report
    inputs: Dict[str, Any] = field(default_factory=dict)


def _f(obj: Any, name: str, default: float = 0.0) -> float:
    """Float read that tolerates None/missing on optional snapshot objects."""
    if obj is None:
        return default
    val = getattr(obj, name, default)
    if val is None:
        return default
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


def _b(obj: Any, name: str, default: bool = False) -> bool:
    """Bool read that fails CLOSED on missing telemetry.

    These gates used to default to True, so an absent feed printed PASS and
    authorised full risk. Absence of evidence is not evidence of a passing gate.
    """
    if obj is None:
        return default
    val = getattr(obj, name, default)
    return bool(default if val is None else val)


def evaluate_waterfall(store: Any) -> WaterfallState:
    """Computes the Tab [W] five pillars and resolves the waterfall state."""
    f_ev = getattr(store, "footprint_evaluation", None)
    macro_ev = getattr(store, "macro_evaluation", None)
    spot_ev = getattr(store, "spot_swing_evaluation", None)
    proto_ev = getattr(store, "protocol_evaluation", None)
    flow = getattr(store, "flow_snapshot", None)
    deriv = getattr(store, "derivatives_snapshot", None)
    macro_vp = getattr(store, "macro_profile", None)
    mag = getattr(spot_ev, "magnet", None) if spot_ev else None
    sig = getattr(store, "latest_signal", None)

    price = float(
        getattr(store, "binance_spot_price", 0.0)
        or (getattr(f_ev, "current_price", 0.0) if f_ev else 0.0)
        or (getattr(spot_ev, "spot_price", 0.0) if spot_ev else 0.0)
        or 0.0
    )

    # ---------------- PILLAR 1: macro permission ----------------
    sma200_px = _f(macro_ev, "sma_200_1d") or _f(f_ev, "sma_200_1d")
    above_200 = _b(macro_ev, "above_200d_sma", _b(f_ev, "above_200d_sma", False))
    slope_pos = _b(macro_ev, "slope_200d_positive", False)
    sma200_slope_pct = _f(macro_ev, "sma_200_slope_5d_pct")

    ntz_active = bool(
        _b(f_ev, "ntz_veto_active", False)
        or getattr(proto_ev, "non_trade_zone_status", "NO") == "YES"
    )
    ntz_text = str(
        getattr(f_ev, "ntz_status_text", "")
        or (getattr(proto_ev, "active_ntz_reasons", ["ALL CLEAR"])[0]
            if (proto_ev and getattr(proto_ev, "active_ntz_reasons", None)) else "ALL CLEAR (8A-8F PASS)")
    ) or "ALL CLEAR (8A-8F PASS)"

    p1_macro = bool(above_200 and not ntz_active)

    # ---------------- PILLAR 2: structure & asymmetry ----------------
    c_val = _f(macro_vp, "c_val")
    c_poc = _f(macro_vp, "c_poc")
    c_vah = _f(macro_vp, "c_vah")
    hvn_floor = _f(macro_vp, "support_hvn_below_val") or (c_val * 0.985 if c_val > 0 else 0.0)

    va_pos = _f(sig, "va_position_pct", 50.0)
    if sig is None:
        is_mid_chop = 30.0 <= va_pos <= 70.0
    else:
        is_mid_chop = bool(getattr(sig, "is_mid_range_chop", False))

    if c_val > 0 and price > 0:
        dist_val_pct = (price - c_val) / c_val * 100.0
        at_edge = (abs(dist_val_pct) <= EDGE_TOLERANCE_PCT) or (price <= c_val)
    else:
        # Unknown cVAL must never read as "at the shelf".
        dist_val_pct = 0.0
        at_edge = False

    short_mag = _f(mag, "short_liq_magnet")
    long_mag = _f(mag, "long_liq_magnet")
    short_dist = _f(mag, "short_liq_distance_pct")
    long_dist = _f(mag, "long_liq_distance_pct")
    rrr_val = _f(mag, "rrr_to_magnet")
    rrr_pass = bool(_b(mag, "rrr_pass", False) or rrr_val >= RRR_MIN)
    max_entry_3r = _f(mag, "max_entry_for_3r")

    # label says edge AND not mid-range: both are required
    p2_structure = bool(at_edge and not is_mid_chop)

    # ---------------- PILLAR 3: cross-venue flow ----------------
    w4 = getattr(flow, "w_4h", None) if flow else None
    spot_cvd_4h = _f(w4, "spot_delta_btc")
    perp_cvd_4h = _f(w4, "perp_delta_btc")
    div_z = _f(w4, "flow_divergence_z")

    is_stealth_dist = bool(
        spot_cvd_4h < STEALTH_SPOT_MAX_BTC
        and perp_cvd_4h > STEALTH_PERP_MIN_BTC
        and div_z < STEALTH_DIV_Z_MAX
    )
    is_spot_accum = bool(
        spot_cvd_4h > 0 and (perp_cvd_4h <= 0 or spot_cvd_4h > perp_cvd_4h)
    )

    cpi_usd = cpi_pct = cpi_z = 0.0
    if deriv is not None:
        try:
            cpi_usd, cpi_pct, cpi_z = store.get_cpi_metrics()
        except Exception:
            cpi_usd = _f(deriv, "coinbase_premium_usd")
            cpi_pct = _f(deriv, "coinbase_premium_pct")
            cpi_z = _f(deriv, "coinbase_premium_zscore")

    p3_flow = bool((not is_stealth_dist) and (cpi_usd >= CPI_CAUTION_USD))

    # ---------------- PILLAR 4: leverage fuel ----------------
    oi_btc = _f(deriv, "open_interest_btc") or float(getattr(store, "open_interest_btc", 0.0) or 0.0)
    oi_4h_pct = _f(deriv, "oi_change_4h_pct")
    if oi_4h_pct == 0.0 and hasattr(store, "get_oi_change_pct"):
        try:
            oi_4h_pct = float(store.get_oi_change_pct(14400) or 0.0)
        except Exception:
            oi_4h_pct = 0.0
    funding_rate = _f(deriv, "funding_rate_pct") or float(getattr(store, "funding_rate_pct", 0.0) or 0.0)
    basis_usd = _f(deriv, "perp_basis_usd")

    is_crowded_long = bool(oi_4h_pct > OI_CROWDED_MIN_PCT and funding_rate > FUNDING_CROWDED_MIN_PCT)
    is_squeeze_fuel = bool(
        funding_rate < 0.0 or (oi_4h_pct > 1.5 and funding_rate <= FUNDING_PASS_MAX_PCT / 2.0)
    )
    p4_leverage = bool(not is_crowded_long)

    # ---------------- PILLAR 5: sniper trigger ----------------
    bar_delta = _f(f_ev, "active_bar_delta")
    prev_delta = _f(f_ev, "prev_bar_delta")
    wick_abs = _b(f_ev, "gate3_wick_absorption", False)
    delta_flip = _b(f_ev, "gate4_delta_flip", False)
    all_gates_pass = _b(f_ev, "all_gates_pass", False)
    auction_completed = _b(f_ev, "auction_completed", False)
    poc_rec = _b(f_ev, "bar_poc_reclaimed", False)

    p5_trigger = bool(all_gates_pass or (wick_abs and delta_flip))

    pillars_aligned = bool(p1_macro and p2_structure and p3_flow and p4_leverage and p5_trigger)

    # ---------------- resolve the state (order is the veto order) ----------------
    if ntz_active:
        state, binding = "RED_SYSTEMIC", "PILLAR 1"
    elif is_stealth_dist:
        state, binding = "RED_STEALTH", "PILLAR 3"
    elif is_crowded_long:
        state, binding = "RED_CROWDED", "PILLAR 4"
    elif cpi_usd < CPI_VETO_USD and not at_edge:
        state, binding = "RED_US_SELLING", "PILLAR 3"
    elif pillars_aligned and rrr_pass:
        state, binding = "GREEN", "NONE"
    elif at_edge or (wick_abs and not delta_flip):
        state, binding = "BLUE", "PILLAR 5"
    else:
        state, binding = "AMBER", "PILLAR 2"

    inputs = {
        "price": round(price, 2),
        "sma200_px": round(sma200_px, 2),
        "sma200_slope_5d_pct": round(sma200_slope_pct, 3),
        "above_200d_sma": above_200,
        "slope_200d_positive": slope_pos,
        "ntz_active": ntz_active,
        "ntz_text": ntz_text,
        "c_val": round(c_val, 2),
        "c_poc": round(c_poc, 2),
        "c_vah": round(c_vah, 2),
        "hvn_floor": round(hvn_floor, 2),
        "va_position_pct": round(va_pos, 1),
        "is_mid_range_chop": is_mid_chop,
        "dist_val_pct": round(dist_val_pct, 2),
        "at_edge": at_edge,
        "rrr_to_magnet": round(rrr_val, 2),
        "rrr_pass": rrr_pass,
        "short_liq_magnet": round(short_mag, 2),
        "long_liq_magnet": round(long_mag, 2),
        "spot_cvd_4h_btc": round(spot_cvd_4h, 1),
        "perp_cvd_4h_btc": round(perp_cvd_4h, 1),
        "flow_divergence_z": round(div_z, 2),
        "is_stealth_distribution": is_stealth_dist,
        "is_spot_accumulation": is_spot_accum,
        "coinbase_premium_usd": round(cpi_usd, 2),
        "coinbase_premium_pct": round(cpi_pct, 3),
        "open_interest_btc": round(oi_btc, 0),
        "oi_change_4h_pct": round(oi_4h_pct, 2),
        "funding_rate_pct": round(funding_rate, 4),
        "perp_basis_usd": round(basis_usd, 2),
        "is_crowded_long": is_crowded_long,
        "is_squeeze_fuel": is_squeeze_fuel,
        "footprint_all_gates_pass": all_gates_pass,
        "footprint_wick_absorption": wick_abs,
        "footprint_delta_flip": delta_flip,
        "footprint_active_delta_btc": round(bar_delta, 1),
        "footprint_prev_delta_btc": round(prev_delta, 1),
        "auction_completed": auction_completed,
        "bar_poc_reclaimed": poc_rec,
    }

    return WaterfallState(
        state=state,
        binding_pillar=binding,
        p1_macro=p1_macro,
        p2_structure=p2_structure,
        p3_flow=p3_flow,
        p4_leverage=p4_leverage,
        p5_trigger=p5_trigger,
        pillars_aligned=pillars_aligned,
        inputs=inputs,
    )
