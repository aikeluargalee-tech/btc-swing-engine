"""Unit tests for Tab [S4] Pattern Invalidation, Liquidity Sweep & SFP Trap Desk."""

import unittest
from datetime import datetime, timezone
from typing import List
import numpy as np

from analytics.ai_packet_exporter import build_ai_telemetry_packet
from analytics.trap_engine import TrapEngine
from config.settings import DEFAULT_CONFIG
from core.models import (
    DerivativesSnapshot,
    FlowSnapshot,
    KlineBar,
    PatternType,
    TrapState,
    VolumeProfileResult,
)
from core.state_store import StateStore
from ui.terminal_hud import build_dashboard_renderable


def _create_synthetic_bars_with_double_bottom(
    base_price: float = 82_000.0,
) -> List[KlineBar]:
    """Generates synthetic 1H bars with a double bottom at $80,000 swept down to $79,600 and reclaimed to $80,400."""
    bars: List[KlineBar] = []
    base_ts = 1_720_000_000_000
    prices = [
        83_000, 82_500, 81_500, 80_500, 80_000,  # Low 1 @ $80,000 (bar 4)
        80_800, 81_500, 82_200, 81_800, 80_900,  # Neckline bounce
        80_100, 80_020,                          # Low 2 @ $80,020 (bar 11 - Equal Lows)
        80_600, 81_000, 80_700, 80_200,
        79_600,                                  # Sweep Wick @ $79,600 (bar 16 - Stop Run)
        80_450,                                  # SFP Reclaim @ $80,450 (bar 17 - Reclaim > $80,000)
    ]
    for i, p in enumerate(prices):
        ts = base_ts + i * 3600 * 1000
        bars.append(
            KlineBar(
                timestamp_ms=ts,
                open=p - 100.0,
                high=p + 150.0,
                low=p - 150.0 if i != 16 else 79_500.0,
                close=p,
                volume=1000.0,
                taker_buy_volume=600.0 if i >= 16 else 450.0,
            )
        )
    return bars


class TestTrapRadarEngine(unittest.TestCase):
    """Verifies pattern boundary discovery, CVD absorption, SFP reclaim execution, and Tab S4 HUD rendering."""

    def setUp(self) -> None:
        self.config = DEFAULT_CONFIG
        self.engine = TrapEngine(self.config)
        self.store = StateStore()

    def test_pattern_boundary_discovery_double_bottom(self) -> None:
        """Verifies automated detection of double bottom equal lows liquidity shelf."""
        bars_1h = _create_synthetic_bars_with_double_bottom()
        current_price = bars_1h[-1].close
        atr_1h = 400.0

        vp = VolumeProfileResult(
            horizon_label="30D Macro",
            c_vah=84_000.0,
            c_poc=82_000.0,
            c_val=80_000.0,
            range_high=86_000.0,
            range_low=79_000.0,
            total_volume=50_000.0,
            bin_width=100.0,
        )

        boundaries = self.engine._discover_pattern_boundaries(bars_1h, current_price, atr_1h, active_vp=vp)
        self.assertGreaterEqual(len(boundaries), 2)

        types = [b.pattern_type for b in boundaries]
        self.assertIn(PatternType.RANGE_SUPPORT_EXTREME, types)
        self.assertIn(PatternType.RANGE_RESISTANCE_EXTREME, types)

    def test_trap_engine_evaluation_bear_trap_sfp(self) -> None:
        """Verifies SFP reclaim triggers State 2 BEAR TRAP and generates asymmetric trade plan."""
        bars_1h = _create_synthetic_bars_with_double_bottom()
        bars_15m = bars_1h[-4:]

        self.store.spot_klines_1h.extend(bars_1h)
        self.store.spot_klines_15m.extend(bars_15m)
        self.store.binance_spot_price = bars_1h[-1].close

        deriv = DerivativesSnapshot(
            perp_5m_delta_btc=-20.0,
            oi_change_15m_pct=0.45,  # Surge flag
            oi_change_1h_pct=1.20,
        )
        flow = FlowSnapshot()
        flow.w_15m.spot_delta_btc = 15.0  # Spot buying
        flow.w_1h.spot_delta_btc = 35.0
        flow.w_1h.perp_delta_btc = -50.0  # Heavy perp selling absorbed

        vp = VolumeProfileResult(
            horizon_label="30D Macro",
            c_vah=84_500.0,
            c_poc=82_500.0,
            c_val=80_000.0,
            range_high=86_000.0,
            range_low=79_000.0,
            total_volume=50_000.0,
            bin_width=100.0,
        )

        ev = self.engine.evaluate(self.store, bars_1h, bars_15m, deriv, flow, active_vp=vp)
        self.assertIsNotNone(ev)
        self.assertIsNotNone(self.store.trap_evaluation)
        assert ev is not None

        # Check Trap State and Signal
        self.assertEqual(ev.active_trap_state, TrapState.STATE_2_SFP_RECLAIM_TRIGGERED)
        self.assertIn("BEAR TRAP", ev.active_trap_signal)
        self.assertTrue(ev.oi_surge_flag)
        self.assertTrue(ev.passive_absorption_flag)

        # Check Asymmetric Trade Plan
        self.assertIsNotNone(ev.trade_plan)
        assert ev.trade_plan is not None
        self.assertEqual(ev.trade_plan.direction, "LONG (BEAR TRAP SQUEEZE)")
        self.assertGreater(ev.trade_plan.rr_ratio, 1.0)
        self.assertLess(ev.trade_plan.stop_loss, ev.trade_plan.entry_price)
        self.assertGreater(ev.trade_plan.tp1_poc, ev.trade_plan.entry_price)

    def test_tab_s4_hud_rendering(self) -> None:
        """Verifies Tab [S4] 5-panel layout renders into Rich renderable without exceptions."""
        bars_1h = _create_synthetic_bars_with_double_bottom()
        bars_15m = bars_1h[-4:]
        self.store.spot_klines_1h.extend(bars_1h)
        self.store.spot_klines_15m.extend(bars_15m)
        self.store.binance_spot_price = bars_1h[-1].close

        deriv = DerivativesSnapshot()
        flow = FlowSnapshot()
        self.engine.evaluate(self.store, bars_1h, bars_15m, deriv, flow)

        renderable = build_dashboard_renderable(self.config, self.store, tab_override=9)
        self.assertIsNotNone(renderable)

    def test_ai_packet_exporter_includes_section_10(self) -> None:
        """Verifies AI Telemetry Packet appends SECTION 10 with Tables 10A, 10B, and 10C."""
        bars_1h = _create_synthetic_bars_with_double_bottom()
        bars_15m = bars_1h[-4:]
        self.store.spot_klines_1h.extend(bars_1h)
        self.store.spot_klines_15m.extend(bars_15m)
        self.store.binance_spot_price = bars_1h[-1].close

        deriv = DerivativesSnapshot()
        flow = FlowSnapshot()
        self.engine.evaluate(self.store, bars_1h, bars_15m, deriv, flow)

        packet = build_ai_telemetry_packet(self.config, self.store)
        self.assertIn("## SECTION 10: TAB [S4] PATTERN INVALIDATION, LIQUIDITY SWEEP & SFP TRAP RADAR", packet)
        self.assertIn("### 10A. Active Classical Pattern Boundaries & Liquidity Proximity Registry", packet)
        self.assertIn("### 10C. Anti-Sycophancy Rulebook for Classical Patterns", packet)

    def test_fair_value_gap_detection_and_mitigation(self) -> None:
        """Verifies 3-bar displacement Bullish FVG detection and 50% Consequent Encroachment (CE) state tracking."""
        base_ms = int(datetime(2026, 10, 28, 10, 0, tzinfo=timezone.utc).timestamp() * 1000)
        bars = [
            KlineBar(base_ms, 79_500, 80_000, 79_400, 79_900, 10.0, 5.0),          # Candle 1: High = 80,000
            KlineBar(base_ms + 900_000, 79_900, 81_500, 79_850, 81_400, 50.0, 40.0), # Candle 2: Impulse
            KlineBar(base_ms + 1800_000, 81_400, 81_800, 80_600, 81_500, 20.0, 12.0), # Candle 3: Low = 80,600 (Gap = 600)
        ]
        # Current price = 81,500 (Gap is unmitigated)
        fvgs = self.engine._detect_fair_value_gaps(bars, timeframe="15m", current_price=81_500)
        self.assertEqual(len(fvgs), 1)
        fvg = fvgs[0]
        self.assertEqual(fvg.direction, "BULLISH")
        self.assertEqual(fvg.bottom_price, 80_000.0)
        self.assertEqual(fvg.top_price, 80_600.0)
        self.assertEqual(fvg.ce_midpoint, 80_300.0)
        self.assertEqual(fvg.status, "UNMITIGATED")

        # Candle 4 pulls back to 80,250 (dips below CE midpoint 80,300 but above 80,000 bottom) -> PARTIALLY_MITIGATED
        bars.append(KlineBar(base_ms + 2700_000, 81_500, 81_500, 80_250, 80_400, 15.0, 7.0))
        fvgs_partial = self.engine._detect_fair_value_gaps(bars, timeframe="15m", current_price=80_400)
        self.assertEqual(len(fvgs_partial), 1)
        self.assertEqual(fvgs_partial[0].status, "PARTIALLY_MITIGATED")

    def test_asia_session_liquidity_sweep_detection(self) -> None:
        """Verifies detection of Asia Session (00:00 - 08:00 UTC) range and post-Asia SFP reclaim."""
        from datetime import datetime, timezone
        # Create Asia session bars (02:00 UTC to 07:45 UTC)
        start_dt = datetime(2026, 10, 28, 2, 0, tzinfo=timezone.utc)
        start_ms = int(start_dt.timestamp() * 1000)
        bars_15m: List[KlineBar] = []
        for i in range(24):  # 6 hours of 15m bars
            t_ms = start_ms + i * 900_000
            bars_15m.append(KlineBar(t_ms, 80_500, 81_200, 80_100, 80_600, 10.0, 5.0))

        # Add London open bar (08:15 UTC) that sweeps below Asia low (80,100) to 79,800 and reclaims to 80_300
        london_ms = start_ms + 25 * 900_000
        bars_15m.append(KlineBar(london_ms, 80_600, 80_700, 79_800, 80_300, 45.0, 30.0))

        items, asia_h, asia_l, h_swept, l_swept = self.engine._detect_asia_session_levels(
            bars_15m, current_price=80_300, atr_1h=300.0
        )
        self.assertEqual(asia_h, 81_200.0)
        self.assertEqual(asia_l, 80_100.0)
        self.assertFalse(h_swept)
        self.assertTrue(l_swept)
        self.assertEqual(len(items), 2)
        low_item = [it for it in items if it.pattern_type == PatternType.ASIA_SESSION_LOW][0]
        self.assertEqual(low_item.status, "SFP RECLAIMED")
        self.assertEqual(low_item.sweep_wick_extreme, 79_800.0)


if __name__ == "__main__":
    unittest.main()
