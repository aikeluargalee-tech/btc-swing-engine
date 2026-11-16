"""Unit tests for Tab [21: D] Unified Data Hub Engine, HUD rendering, and DATA-ONLY export."""

from __future__ import annotations

import io
import json
import sqlite3
import tempfile
import time
import unittest
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from rich.console import Console

from analytics.data_hub_engine import UNAVAILABLE, DataHubEngine
from analytics.data_only_reports import (
    build_tab_d_data_only_report,
    copy_tab_data_only_report_to_clipboard,
    evaluate_hard_market_veto,
)
from collectors.macro_collector import MacroIntermarketSnapshot
from config.settings import EngineConfig
from core.models import (
    DerivativesSnapshot,
    FlowSnapshot,
    FourGateEvaluation,
    HorizonFlowMetrics,
    KlineBar,
    LiquidationDetectorReport,
    LiquidationWindow,
    OIPositioningQuadrant,
    PostFlushStructure,
    VolumeProfileResult,
)
from core.state_store import StateStore
from ui.terminal_hud import build_dashboard_renderable


def _render_str(renderable) -> str:
    buf = io.StringIO()
    con = Console(file=buf, width=200, force_terminal=False)
    con.print(renderable)
    return buf.getvalue()


def _make_klines(n: int = 30, step_ms: int = 14_400_000, base_px: float = 73_000.0) -> list:
    now_ms = int(datetime(2026, 11, 14, 8, 0, tzinfo=timezone.utc).timestamp() * 1000)
    out = []
    for i in range(n):
        px = base_px + (i * 80.0) + ((-1) ** i) * 40.0
        out.append(
            KlineBar(
                timestamp_ms=now_ms - (n - 1 - i) * step_ms,
                open=px - 50.0,
                high=px + 120.0,
                low=px - 110.0,
                close=px,
                volume=1000.0 + i * 10.0,
                taker_buy_volume=520.0,
            )
        )
    return out


class TestDataHub(unittest.TestCase):
    def setUp(self) -> None:
        self.cfg = EngineConfig()

    def test_cold_start_fails_closed_with_unavailable(self) -> None:
        store = StateStore()
        with tempfile.TemporaryDirectory() as tmp:
            ev = DataHubEngine(self.cfg, db_path=Path(tmp) / "cold.sqlite", write_archive=False).evaluate(store)

        self.assertEqual(ev.total_metrics, 71)
        self.assertGreater(ev.unavailable_count, 40)
        self.assertEqual(
            ev.ok_count + ev.unavailable_count + ev.stale_count + ev.proxy_or_static_count,
            ev.total_metrics,
        )
        # Ensure missing spot price, volume profile, and SOPR clearly report UNAVAILABLE
        labels = {r.label: r for r in (ev.panel_1_feeds + ev.panel_4_flow_quant + ev.panel_6_macro_onchain)}
        self.assertIn(UNAVAILABLE, labels["Binance Spot / Perp ($)"].value)
        self.assertEqual(labels["Macro 30D VAH / POC / VAL"].value, UNAVAILABLE)
        self.assertEqual(labels["Macro 30D VAH / POC / VAL"].status, "UNAVAILABLE")
        self.assertEqual(labels["On-Chain SOPR / aSOPR"].value, UNAVAILABLE)
        self.assertEqual(labels["Telemetry History Archive (SQLite)"].status, "UNAVAILABLE")

    def test_populated_store_aggregates_all_panels_and_tags_proxies(self) -> None:
        store = StateStore()
        now_ts = time.time()
        store.warmup_complete = True
        store.spot_ws_connected = True
        store.perp_ws_connected = True
        store.coinbase_ws_connected = True
        store.last_spot_tick_ts = now_ts
        store.last_perp_tick_ts = now_ts
        store.last_cb_tick_ts = now_ts
        store.binance_spot_price = 73_650.0
        store.binance_perp_price = 73_680.0
        store.coinbase_spot_price = 73_670.0
        store.open_interest_btc = 85_400.0
        store.open_interest_usd = 6_290_000_000.0
        store.funding_rate_pct = 0.0085
        store.taker_long_short_ratio_5m = 1.07
        store.top_trader_long_pct = 55.2
        store.top_trader_short_pct = 44.8
        store.top_trader_ls_ratio = 1.23
        store.global_account_ls_ratio = 1.48
        store.spot_trade_count = 420
        store.perp_trade_count = 610

        store.spot_klines_1w.extend(_make_klines(30, 604_800_000))
        store.spot_klines_1d.extend(_make_klines(30, 86_400_000))
        store.perp_klines_1d.extend(_make_klines(30, 86_400_000))
        store.spot_klines_4h.extend(_make_klines(40, 14_400_000))
        store.spot_klines_1h.extend(_make_klines(40, 3_600_000))
        store.perp_klines_1h.extend(_make_klines(40, 3_600_000))
        store.spot_klines_15m.extend(_make_klines(40, 900_000))
        store.perp_klines_15m.extend(_make_klines(40, 900_000))

        store.macro_profile = VolumeProfileResult("30D", 82342.0, 81612.0, 75770.0, 83000.0, 72000.0, 100000.0, 50.0, [74000.0], [72800.0])
        store.flow_snapshot = FlowSnapshot(
            w_15m=HorizonFlowMetrics("15m", spot_delta_btc=12.4, perp_delta_btc=-5.1),
            w_1h=HorizonFlowMetrics("1h", spot_delta_btc=45.0, perp_delta_btc=-18.0),
            w_4h=HorizonFlowMetrics("4h", spot_delta_btc=110.0, perp_delta_btc=-42.0),
            w_24h=HorizonFlowMetrics("24h", spot_delta_btc=244.0, perp_delta_btc=120.0, spot_zscore=0.45, perp_zscore=0.12, flow_divergence_z=0.33),
        )
        store.derivatives_snapshot = DerivativesSnapshot(
            open_interest_btc=85_400.0,
            open_interest_usd=6_290_000_000.0,
            oi_change_15m_pct=0.12,
            oi_change_1h_pct=0.45,
            oi_change_4h_pct=-1.10,
            oi_regime_quadrant=OIPositioningQuadrant.NEUTRAL_CHURN,
            funding_rate_pct=0.0085,
            coinbase_premium_usd=20.0,
            coinbase_premium_pct=0.027,
            coinbase_premium_zscore=0.62,
            perp_basis_usd=30.0,
        )
        store.macro_evaluation = SimpleNamespace(
            sma_200_1d=68_500.0,
            sma_200_slope_5d_pct=0.42,
            ema_21_1d=74_900.0,
            rsi_14_1d=49.5,
            power_law_fair_usd=92_000.0,
            power_law_discount_pct=-19.9,
            current_drawdown_pct=-32.8,
        )
        store.four_gate_evaluation = FourGateEvaluation(
            last_closed_bar_utc="2026-11-14 08:00:00 UTC",
            loop_a_g1_val=0.1842,
            loop_a_g2_val=1.15,
            loop_a_g2_z_s=1.35,
            loop_a_g2_z_f=0.20,
            gate_3_l20=72_727.3,
            loop_b_g3_h20=82_060.9,
            loop_a_g4_funding_p90=18.4,
            dvol_current=47.5,
        )
        store.ssrn_alpha_evaluation = SimpleNamespace(
            daily_macd_status="BEAR",
            hourly_macd_status="BULL",
            realized_vol_20d_ann=41.2,
            live_skewness_20d=-0.28,
            live_obi_ratio_pct=5.4,
            live_mvrv_ratio=1.73,
            live_sopr_level=1.02,
        )
        store.grok_quant_evaluation = SimpleNamespace(
            vwap_daily=73_900.0,
            vwap_stretch_z=-0.45,
            ema_9=74_100.0,
            ema_21=74_500.0,
            ema_50_1d=75_200.0,
        )
        store.liquidation_report = LiquidationDetectorReport(
            is_available=True,
            is_stale=False,
            magnitude_tier="MODERATE",
            liquidation_multiple_24h=1.42,
            windows={
                "1h": LiquidationWindow(long_usd=3_200_000.0, short_usd=1_100_000.0, total_usd=4_300_000.0),
                "24h": LiquidationWindow(long_usd=28_000_000.0, short_usd=19_000_000.0, total_usd=47_000_000.0),
            },
            post_flush_price_structure=PostFlushStructure(status="STABILIZED"),
        )
        store.macro_intermarket = MacroIntermarketSnapshot(
            dxy_index=104.2,
            dxy_direction_5_10d="UP",
            us_10y_treasury_yield=4.28,
            us_10y_real_yield_tips=1.95,
            us_10y_breakeven_inflation=2.33,
            sp500_price=5980.0,
            sp500_change_1d_pct=0.35,
            nasdaq_price=19100.0,
            vix_index=15.4,
            brent_crude_price=72.5,
            btc_spx_corr_20d=0.41,
            btc_spx_corr_60d=0.34,
            fear_and_greed_score=64,
            fear_and_greed_classification="Greed",
            btc_dominance_pct=58.3,
            orderbook_depth_ratio_1pct=1.18,
            orderbook_depth_ratio_2pct=1.09,
            orderbook_spread_bps=0.14,
            coinbase_spot_vol_24h_btc=14_820.0,
            onchain_mvrv_cur=1.420,
            onchain_mvrv_date="2026-11-13",
            onchain_exch_inflow_btc=12_400.0,
            onchain_exch_outflow_btc=15_100.0,
            onchain_exch_netflow_btc=-2_700.0,
            onchain_exch_netflow_usd=-198_000_000.0,
            onchain_exch_supply_btc=2_310_000.0,
            stablecoin_usdt_b=138.40,
            stablecoin_usdc_b=56.20,
            stablecoin_total_b=194.60,
            stablecoin_7d_delta_b=1.85,
            stablecoin_30d_delta_b=6.40,
            options_put_call_oi_ratio=0.625,
            options_total_oi_btc=285_400.0,
            options_iv_front=51.4,
            options_iv_back=55.8,
            options_skew_25d_proxy=3.6,
            agg_perp_oi_btc=215_400.0,
            agg_perp_oi_usd=15_860_000_000.0,
            agg_perp_funding_8h_pct=0.0091,
            agg_perp_venues_str="BN+BYB+OKX",
            etf_daily_net_flow_usd=240_000_000.0,
            etf_daily_net_flow_status="OK",
            etf_3d_cumulative_flow_usd=510_000_000.0,
            etf_3d_cumulative_flow_status="OK",
            etf_proxy_vol_1d_usd=2_450_000_000.0,
            etf_proxy_flow_5d_usd=680_000_000.0,
            us_sofr_rate_pct=4.33,
            us_sofr_vol_b=2340.0,
            us_rrp_balance_b=142.50,
            credit_hyg_lqd_ratio=0.7312,
            credit_hyg_lqd_5d_chg_pct=0.45,
        )
        store.protocol_evaluation = SimpleNamespace(
            atr_14_1d=2150.0,
            atr_14_4h=780.0,
            enforce_200d_hard_veto_on_tab1=False,
            headline_filter_status="CLEAR",
        )
        store.volatility_cone_evaluation = SimpleNamespace(garman_klass_annualized_vol=43.8, vcr_72h=1.12, horizons=[])
        store.mm_btc_evaluation = SimpleNamespace()

        with tempfile.TemporaryDirectory() as tmp:
            db_file = Path(tmp) / "dd_test.sqlite"
            ev = DataHubEngine(self.cfg, db_path=db_file, write_archive=True).evaluate(store)

            self.assertEqual(ev.total_metrics, 71)
            self.assertGreater(ev.ok_count, 50)
            self.assertEqual(ev.proxy_or_static_count, 1)  # ETF tape proxy only; live CoinMetrics MVRV is OK, static SOPR retired
            self.assertEqual(ev.archive_snapshots_count, 1)
            self.assertEqual(ev.archive_last_bar_utc, "2026-11-14 08:00:00 UTC")

            all_rows = {
                r.label: r
                for r in (
                    ev.panel_1_feeds
                    + ev.panel_2_trend_vol
                    + ev.panel_3_structure_magnets
                    + ev.panel_4_flow_quant
                    + ev.panel_5_derivs_liq
                    + ev.panel_6_macro_onchain
                )
            }
            # On-Chain CoinMetrics MVRV is primary OK; static SOPR=1.02 refused
            self.assertEqual(all_rows["MVRV Ratio (On-Chain / Proxy)"].status, "OK")
            self.assertIn("1.420 [CoinMetrics 2026-11-13]", all_rows["MVRV Ratio (On-Chain / Proxy)"].value)
            self.assertEqual(all_rows["On-Chain SOPR / aSOPR"].value, UNAVAILABLE)
            self.assertEqual(all_rows["On-Chain SOPR / aSOPR"].status, "UNAVAILABLE")
            self.assertEqual(all_rows["US ETF Tape Proxy (IBIT+FBTC)"].status, "PROXY")
            self.assertIn("$2.45B", all_rows["US ETF Tape Proxy (IBIT+FBTC)"].value)

            # New DD v2 free-feed panels populated accurately
            self.assertIn("CB:14,820", all_rows["Cross-Exch 24H Spot Vol (BN/CB)"].value)
            self.assertIn("Spr:0.1400bps", all_rows["L2 Depth ±1%/±2%, OBI & Spread"].value)
            self.assertIn("[BN+BYB+OKX 3/3]", all_rows["Cross-Exch Perp OI & Funding"].value)
            self.assertIn("P/C:0.625", all_rows["Options OI & Put/Call (Deribit)"].value)
            self.assertIn("+3.6%", all_rows["Options IV Term & Skew (Deribit)"].value)
            self.assertIn("-2,700.0 BTC", all_rows["Exchange Netflow 24H (CM)"].value)
            self.assertIn("2,310,000 BTC", all_rows["BTC Exchange Reserves (CM)"].value)
            self.assertIn("$194.60B", all_rows["Stablecoins USDT+USDC Supply"].value)
            self.assertIn("+1.85B", all_rows["Stablecoin Net Issuance (7D/30D)"].value)
            self.assertIn("4.33%", all_rows["US SOFR Rate & Vol (NY Fed)"].value)
            self.assertIn("$142.50B", all_rows["Fed ON RRP Balance (NY Fed)"].value)
            self.assertIn("0.7312", all_rows["Credit Spread HYG/LQD & 5D%"].value)
            self.assertIn("1 bars logged", all_rows["Telemetry History Archive (SQLite)"].value)
            # 4H RSI(14) computed from closed 4H klines
            self.assertNotIn("4H:N/A", all_rows["RSI(14) 1D / 4H & 4H ROC12"].value)

            # Render Tab 21 via numeric & alias overrides
            txt_num = _render_str(build_dashboard_renderable(self.cfg, store, tab_override=21))
            txt_alias = _render_str(build_dashboard_renderable(self.cfg, store, tab_override="d"))
            for rendered in (txt_num, txt_alias):
                self.assertIn("UNIFIED DATA HUB | TAB 21 [D]", rendered)
                self.assertIn("1. PRICE, TREND & MARKET STRUCTURE", rendered)
                self.assertIn("4. ON-CHAIN, ETF & STABLECOIN FLOWS", rendered)
                self.assertIn("6. QUANT FEATURES, FEED HEALTH & ARCHIVE", rendered)

            # Pure DATA-ONLY markdown report check (0 forbidden interpretive words)
            report = build_tab_d_data_only_report(self.cfg, store, db_path=db_file)
            self.assertIn("TAB [D: DATA HUB] | CONSOLIDATED DATA-ONLY TELEMETRY REPORT", report)
            self.assertIn("**24H Range:**", report)
            self.assertIn("**Returns (24H / 7D / 30D):**", report)
            self.assertIn("1 closed-4H snapshots (Last: 2026-11-14 08:00:00 UTC)", report)
            self.assertIn("## 5. MACRO, CREDIT & US LIQUIDITY", report)
            self.assertIn("## 7. RECENT CLOSED-4H SNAPSHOT TRAJECTORY (SQLITE ARCHIVE)", report)
            self.assertIn("| Funding 8H% / 90D Pct |", report)
            self.assertIn("## 8. METRIC FORMULA LEGEND & CORTEX DESK LITE PROTOCOL", report)
            self.assertIn("DIRECT AI EXECUTION PROTOCOL: CORTEX BTC DESK LITE v1.0", report)
            self.assertIn("100% USDT CASH — NO ENTRY", report)
            self.assertIn("`2026-11-14 08:00:00 UTC` | `$73,650.00`", report)
            self.assertNotIn("OIPositioningQuadrant.", report)
            self.assertIn("NEUTRAL_CHURN`", report)
            self.assertNotIn("Top participant", report)
            for bad in ("verdict", "bullish", "bearish", "recommend"):
                self.assertNotIn(bad, report.lower())

            with patch("analytics.data_only_reports.subprocess.run") as mock_run:
                mock_run.return_value.returncode = 0
                ok, path, nchars = copy_tab_data_only_report_to_clipboard(21, self.cfg, store)
                self.assertTrue(path.endswith("btc_data_hub_latest.md"))
                self.assertGreater(nchars, 400)

    def test_mvrv_proxy_fallback_and_sqlite_archive_dedup(self) -> None:
        store = StateStore()
        store.binance_spot_price = 70_000.0
        store.ssrn_alpha_evaluation = SimpleNamespace(live_mvrv_ratio=1.73, live_sopr_level=1.02)
        store.four_gate_evaluation = FourGateEvaluation(last_closed_bar_utc="2026-11-14 08:00:00 UTC")

        with tempfile.TemporaryDirectory() as tmp:
            db_file = Path(tmp) / "dedup.sqlite"
            eng = DataHubEngine(self.cfg, db_path=db_file, write_archive=True)

            ev1 = eng.evaluate(store)
            p4 = {r.label: r for r in ev1.panel_4_flow_quant}
            self.assertEqual(p4["MVRV Ratio (On-Chain / Proxy)"].status, "PROXY")
            self.assertIn("1.73 [PROXY", p4["MVRV Ratio (On-Chain / Proxy)"].value)
            self.assertEqual(p4["On-Chain SOPR / aSOPR"].status, "UNAVAILABLE")
            self.assertEqual(ev1.archive_snapshots_count, 1)

            # Calling again on same closed 4H bar must deduplicate
            ev2 = eng.evaluate(store)
            self.assertEqual(ev2.archive_snapshots_count, 1)

            # New closed 4H bar appends row #2 with valid JSON payload
            store.four_gate_evaluation = FourGateEvaluation(last_closed_bar_utc="2026-11-14 12:00:00 UTC")
            ev3 = eng.evaluate(store)
            self.assertEqual(ev3.archive_snapshots_count, 2)
            self.assertEqual(ev3.archive_last_bar_utc, "2026-11-14 12:00:00 UTC")

            conn = sqlite3.connect(str(db_file))
            try:
                rows = conn.execute(
                    "SELECT closed_4h_bar_utc, payload_json FROM telemetry_snapshots ORDER BY id ASC"
                ).fetchall()
                self.assertEqual(len(rows), 2)
                payload = json.loads(rows[1][1])
                self.assertEqual(payload["schema_version"], "dd_v2")
                self.assertEqual(len(payload["panels"]), 6)
            finally:
                conn.close()

    def test_vwap_adx_and_master_footprint_fixes(self) -> None:
        from analytics.master_synthesis import MasterSynthesisEvaluator
        from analytics.signal_detector import SignalDetector

        store = StateStore()
        store.binance_spot_price = 66_587.61
        store.grok_quant_evaluation = SimpleNamespace(vwap_daily=67_187.69, vwap_stretch_z=-1.44, ema_9=67_088.0, ema_21=67_654.0, ema_50_1d=77_752.0)
        store.regime_matrix_evaluation = SimpleNamespace(daily_vwap=67_629.49, weekly_vwap=71_979.14, ema_50_1d=77_752.0)
        store.slsp_evaluation = SimpleNamespace(ema_3_adx=28.1)
        store.latest_signal = SimpleNamespace(ema_strategy=SimpleNamespace(daily_adx=28.1, adx_4h=34.6))

        ev = DataHubEngine(self.cfg, write_archive=False).evaluate(store)
        p1 = {r.label: r for r in ev.panel_1_feeds}
        # Daily VWAP must come from grok.vwap_daily to match vwap_stretch_z (-1.44σ), not rm.daily_vwap
        self.assertIn("D:$67,187.69 (-1.44σ)", p1["Daily / Weekly VWAP (Z)"].value)
        # ADX(14) 1D and 4H must be cleanly separated instead of mislabeling 1D ADX as ADX4H
        self.assertIn("ADX 1D:28.1 4H:34.6", p1["ADX(14) 1D/4H & ATR(14) 1D/4H/1H"].value)

        # MasterSynthesisEvaluator must read fp.active_bar_delta rather than nonexistent current_bar_delta
        eval_store = StateStore()
        eval_store.binance_spot_price = 66_587.61
        eval_store.spot_klines_1d.extend(_make_klines(260, 86_400_000))
        eval_store.spot_klines_4h.extend(_make_klines(60, 14_400_000))
        eval_store.spot_klines_1h.extend(_make_klines(250, 3_600_000))
        eval_store.spot_klines_15m.extend(_make_klines(120, 900_000))
        with patch("time.time", return_value=eval_store.spot_klines_15m[-1].timestamp_ms / 1000.0):
            sig = SignalDetector(self.cfg).evaluate(eval_store)
        eval_store.footprint_evaluation = SimpleNamespace(active_bar_delta=-25.48, signal_state="OBSERVING")
        msev = MasterSynthesisEvaluator(self.cfg).evaluate(
            store=eval_store,
            sig=sig,
            pev=eval_store.protocol_evaluation,
            mev=eval_store.macro_evaluation,
            rmev=eval_store.regime_matrix_evaluation,
            flow=FlowSnapshot(),
            deriv=DerivativesSnapshot(),
        )
        row_f = next(r for r in msev.tab_rows if r.tab_num == 11)
        self.assertIn("-25.5", row_f.score_or_status)
        self.assertIn("-25.5", row_f.primary_driver)

    def test_500_kline_config_headless_cvd_and_unit_scaling(self) -> None:
        self.assertEqual(self.cfg.daily_kline_limit, 500)
        self.assertEqual(self.cfg.weekly_kline_limit, 100)
        self.assertEqual(self.cfg.four_hour_kline_limit, 500)

        store = StateStore()
        self.assertEqual(store.spot_klines_1d.maxlen, 600)
        self.assertEqual(store.perp_klines_1d.maxlen, 600)
        self.assertEqual(store.spot_klines_4h.maxlen, 600)

        store.binance_spot_price = 65_278.02
        store.spot_klines_4h.extend(_make_klines(40, 14_400_000))
        store.spot_klines_15m.extend(_make_klines(12, 900_000))
        store.utc_day_spot_cvd = -1907.6
        store.utc_day_perp_cvd = -8545.6
        # Headless run has 0 live WS trades, yet REST-seeded 15m klines provide UTC-day CVD
        self.assertEqual(store.spot_trade_count, 0)
        self.assertEqual(store.perp_trade_count, 0)

        store.derivatives_snapshot = DerivativesSnapshot(perp_basis_usd=-23.4)
        store.regime_matrix_evaluation = SimpleNamespace(annualized_basis_pct=3.60)
        store.volatility_cone_evaluation = SimpleNamespace(garman_klass_annualized_vol=0.562, vcr_72h=1.12, horizons=[])
        store.spot_swing_evaluation = SimpleNamespace(macro=SimpleNamespace(bbw_percentile=0.94))
        store.macro_intermarket = MacroIntermarketSnapshot(
            orderbook_depth_ratio_1pct=1.25,
            orderbook_depth_ratio_2pct=2.10,
            orderbook_spread_bps=0.0015,
        )

        ev = DataHubEngine(self.cfg, write_archive=False).evaluate(store)
        rows = {
            r.label: r
            for r in (ev.panel_1_feeds + ev.panel_2_trend_vol + ev.panel_3_structure_magnets)
        }
        self.assertEqual(rows["Session / UTC-Day CVD"].status, "OK")
        self.assertEqual(rows["Session / UTC-Day CVD"].tabs, "REST 15m")
        self.assertIn("Spr:0.0015bps", rows["L2 Depth ±1%/±2%, OBI & Spread"].value)
        self.assertIn("-23.4$ (-0.036% | Carry:+3.60%/yr)", rows["Perp Basis ($ / Ann %)"].value)
        self.assertIn("GK:56.2%", rows["Vol: DVOL, RV20, GK & BBW%"].value)
        self.assertIn("BBW:94%", rows["Vol: DVOL, RV20, GK & BBW%"].value)

    def test_headless_publisher_dashboard_and_telegram_formatting(self) -> None:
        import asyncio
        from scripts.publish_dd_hub import (
            build_telegram_messages,
            send_dd_to_telegram,
            write_dashboard_artifacts,
        )

        store = StateStore()
        store.binance_spot_price = 65_278.02
        store.spot_klines_15m.extend(_make_klines(12, 900_000))
        store.four_gate_evaluation = FourGateEvaluation(last_closed_bar_utc="2026-11-14 12:00:00 UTC")

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            db_file = tmp_path / "pub.sqlite"
            out_dir = tmp_path / "docs"
            ev = DataHubEngine(self.cfg, db_path=db_file, write_archive=True).evaluate(store)
            md_report = build_tab_d_data_only_report(self.cfg, store, db_path=db_file)

            paths = write_dashboard_artifacts(
                output_dir=out_dir,
                ev=ev,
                md_report=md_report,
                db_path=db_file,
                repo_url="https://github.com/example/btc-swing-engine",
                pages_url="https://example.github.io/btc-swing-engine/",
                utc_str="2026-11-14 15:30:00 UTC",
                sgt_str="2026-11-14 23:30:00 SGT (UTC+8)",
                also_write_logs=False,
            )

            self.assertTrue(paths["html"].exists())
            self.assertTrue(paths["json"].exists())
            self.assertTrue(paths["md"].exists())

            html_txt = paths["html"].read_text(encoding="utf-8")
            self.assertIn("COPY FULL DD REPORT FOR AI", html_txt)
            self.assertIn("1. PRICE, TREND &amp; MARKET STRUCTURE", html_txt)
            self.assertIn("2026-11-14 12:00:00 UTC", html_txt)

            json_payload = json.loads(paths["json"].read_text(encoding="utf-8"))
            self.assertEqual(json_payload["schema_version"], "dd_v2")
            self.assertEqual(len(json_payload["panels"]), 6)
            self.assertEqual(len(json_payload["recent_archive"]), 1)

            msgs = build_telegram_messages(
                ev,
                utc_str="2026-11-14 15:30:00 UTC",
                sgt_str="2026-11-14 23:30:00 SGT (UTC+8)",
                pages_url="https://example.github.io/btc-swing-engine/",
                repo_url="https://github.com/example/btc-swing-engine",
            )
            self.assertEqual(len(msgs), 2)
            for m in msgs:
                self.assertLessEqual(len(m), 4096)

            # Force narrow limit to test dynamic multi-part chunking
            chunked = build_telegram_messages(
                ev,
                utc_str="2026-11-14 15:30:00 UTC",
                sgt_str="2026-11-14 23:30:00 SGT (UTC+8)",
                pages_url="https://example.github.io/btc-swing-engine/",
                repo_url="https://github.com/example/btc-swing-engine",
                max_len=1400,
            )
            self.assertGreater(len(chunked), 2)

            posted_urls = []

            class _FakeResp:
                status = 200
                async def text(self) -> str:
                    return "ok"
                async def __aenter__(self):
                    return self
                async def __aexit__(self, *args):
                    return False

            class _FakeSession:
                async def __aenter__(self):
                    return self
                async def __aexit__(self, *args):
                    return False
                def post(self, url, **kwargs):
                    posted_urls.append(url)
                    return _FakeResp()

            with patch("scripts.publish_dd_hub.aiohttp.ClientSession", return_value=_FakeSession()):
                asyncio.run(
                    send_dd_to_telegram(
                        token="TEST_TOK",
                        chat_id="12345",
                        ev=ev,
                        md_path=paths["md"],
                        utc_str="2026-11-14 15:30:00 UTC",
                        sgt_str="2026-11-14 23:30:00 SGT (UTC+8)",
                        pages_url="https://example.github.io/btc-swing-engine/",
                        repo_url="https://github.com/example/btc-swing-engine",
                    )
                )
            self.assertEqual(len(posted_urls), 3)
            self.assertTrue(posted_urls[0].endswith("/sendMessage"))
            self.assertTrue(posted_urls[1].endswith("/sendMessage"))
            self.assertTrue(posted_urls[2].endswith("/sendDocument"))

    def test_us_runner_parity_fixes(self) -> None:
        from analytics.data_hub_engine import _canonical_4h_utc
        from collectors.macro_collector import extract_coingecko_perp_venue
        from scripts.publish_dd_hub import _format_telegram_panel_block

        self.assertEqual(_canonical_4h_utc("2026-11-14 12:00Z"), "2026-11-14 12:00:00 UTC")
        self.assertEqual(_canonical_4h_utc("2026-11-14 12:00:00 UTC"), "2026-11-14 12:00:00 UTC")

        store = StateStore()
        store.binance_spot_price = 65_667.51
        store.futures_v4_evaluation = SimpleNamespace(last_4h_close_utc="2026-11-14 12:00Z")
        store.macro_intermarket = MacroIntermarketSnapshot(
            etf_proxy_vol_1d_usd=2_280_000_000.0,
            etf_proxy_flow_5d_usd=-6_190_000_000.0,
        )

        with tempfile.TemporaryDirectory() as tmp:
            db_file = Path(tmp) / "legacy_z.sqlite"
            # Seed a legacy 12:00Z row (plus another where canonical also exists)
            conn = sqlite3.connect(str(db_file))
            conn.execute(
                """
                CREATE TABLE telemetry_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    closed_4h_bar_utc TEXT NOT NULL UNIQUE,
                    retrieval_utc TEXT NOT NULL,
                    spot_price REAL NOT NULL,
                    ok_count INTEGER NOT NULL,
                    unavailable_count INTEGER NOT NULL,
                    stale_count INTEGER NOT NULL,
                    proxy_or_static_count INTEGER NOT NULL,
                    payload_json TEXT NOT NULL
                )
                """
            )
            conn.execute(
                "INSERT INTO telemetry_snapshots (closed_4h_bar_utc, retrieval_utc, spot_price, ok_count, unavailable_count, stale_count, proxy_or_static_count, payload_json) "
                "VALUES ('2026-11-14 12:00Z', '2026-11-14 15:51:28 UTC', 65667.51, 60, 4, 1, 1, '{}')"
            )
            conn.commit()
            conn.close()

            ev = DataHubEngine(self.cfg, db_path=db_file, write_archive=True).evaluate(store)
            self.assertEqual(ev.archive_snapshots_count, 1)
            self.assertEqual(ev.archive_last_bar_utc, "2026-11-14 12:00:00 UTC")
            p6 = {r.label: r for r in ev.panel_6_macro_onchain}
            self.assertEqual(p6["Closed 4H Anchor (Tab 19/20)"].value, "2026-11-14 12:00:00 UTC")

            blk = _format_telegram_panel_block("4. ON-CHAIN, ETF & STABLECOIN FLOWS", ev.panel_4_flow_quant)
            self.assertIn("1DVol:$2.28B · 5D:-$6.19B [PROXY]", blk)
            self.assertNotIn("[PROXY] [PROXY]", blk)

        cg_sample = [
            {"market": "Binance (Futures)", "symbol": "BTCUSDT", "price": "65000.0", "open_interest": 6500000000.0, "funding_rate": 0.0042},
            {"market": "Bybit (Futures)", "symbol": "BTCUSDT", "price": "65000.0", "open_interest": 3250000000.0, "funding_rate": 0.0051},
        ]
        bn = extract_coingecko_perp_venue(cg_sample, "Binance (Futures)", "BTCUSDT", "BN")
        byb = extract_coingecko_perp_venue(cg_sample, "Bybit (Futures)", "BTCUSDT", "BYB")
        self.assertIsNotNone(bn)
        self.assertAlmostEqual(bn[1], 100_000.0)
        self.assertAlmostEqual(bn[3], 0.0042)
        self.assertIsNotNone(byb)
        self.assertAlmostEqual(byb[1], 50_000.0)

    def test_500_bar_structure_and_recent_ohlcv_sections(self) -> None:
        import math

        store = StateStore()
        now_ms = int(time.time() * 1000)

        def _wave_klines(n: int, step_ms: int) -> list:
            # Align last bar to the active (unclosed) period so it must be excluded cleanly
            cur_open = (now_ms // step_ms) * step_ms
            bars = []
            for i in range(n):
                wave = 2500.0 * math.sin(i * 0.45) - (i * 35.0)
                mid = 72_000.0 + wave
                bars.append(
                    KlineBar(
                        timestamp_ms=cur_open - (n - 1 - i) * step_ms,
                        open=mid - 120.0,
                        high=mid + 420.0,
                        low=mid - 390.0,
                        close=mid + 80.0,
                        volume=1500.0 + i,
                        taker_buy_volume=750.0,
                    )
                )
            return bars

        store.spot_klines_1d.extend(_wave_klines(60, 86_400_000))
        store.spot_klines_4h.extend(_wave_klines(80, 14_400_000))
        store.spot_klines_1h.extend(_wave_klines(80, 3_600_000))
        store.binance_spot_price = float(store.spot_klines_1h[-2].close)

        report = build_tab_d_data_only_report(self.cfg, store, db_path=Path(tempfile.gettempdir()) / "nonexistent_dd_test.sqlite")
        self.assertIn("### 7A. 500-BAR MARKET STRUCTURE & HISTORICAL S/R ZONES", report)
        self.assertIn("### 7B. RECENT CLOSED KLINES — OHLCV PRICE ACTION", report)
        self.assertIn("**1D Closed Candles (Last 7 of 59 available, Newest First):**", report)
        self.assertIn("**4H Closed Candles (Last 12 of 79 available, Newest First):**", report)
        self.assertIn("**1H Closed Candles (Last 12 of 79 available, Newest First):**", report)
        self.assertIn("BOS ", report)
        for bad in ("verdict", "bullish", "bearish", "recommend"):
            self.assertNotIn(bad, report.lower())

    def test_cortex_desk_lite_labels_partial_venue_and_archive_backcompat(self) -> None:
        from analytics.data_only_reports import _query_tab_d_trajectory_rows

        store = StateStore()
        store.binance_spot_price = 64_080.59
        store.derivatives_snapshot = DerivativesSnapshot(
            open_interest_btc=98_404.0,
            open_interest_usd=6_170_000_000.0,
            oi_change_15m_pct=-0.24,
            oi_regime_quadrant=OIPositioningQuadrant.SHORT_COVERING_BOUNCE,
            funding_rate_pct=0.0059,
        )
        store.four_gate_evaluation = FourGateEvaluation(loop_a_g4_funding_p90=0.7)
        store.macro_intermarket = MacroIntermarketSnapshot(
            orderbook_depth_ratio_1pct=0.79,
            orderbook_depth_ratio_2pct=0.77,
            orderbook_spread_bps=0.0016,
            agg_perp_oi_btc=167_154.0,
            agg_perp_oi_usd=10_500_000_000.0,
            agg_perp_funding_8h_pct=0.0026,
            agg_perp_venues_str="BN+OKX",
            agg_perp_venues_count=2,
            agg_perp_venues_expected=3,
        )

        ev = DataHubEngine(self.cfg, write_archive=False).evaluate(store)
        all_rows = {
            r.label: r
            for r in (
                ev.panel_1_feeds
                + ev.panel_2_trend_vol
                + ev.panel_3_structure_magnets
                + ev.panel_4_flow_quant
                + ev.panel_5_derivs_liq
                + ev.panel_6_macro_onchain
            )
        }
        self.assertIn("30D VA Pos% & Dist to VAL", all_rows)
        self.assertIn("Spr:0.0016bps", all_rows["L2 Depth ±1%/±2%, OBI & Spread"].value)
        self.assertIn("[BN+OKX 2/3 PARTIAL_VENUE]", all_rows["Cross-Exch Perp OI & Funding"].value)
        self.assertIn("PARTIAL_VENUE (2/3)", all_rows["OI Δ% (15m/1h/4h/24h) & Quad"].value)
        self.assertNotIn("SHORT_COVERING_BOUNCE", all_rows["OI Δ% (15m/1h/4h/24h) & Quad"].value)
        self.assertIn("Funding 8H% / Ann% / 90D Pct", all_rows)
        self.assertIn("90D Pct:0.7%", all_rows["Funding 8H% / Ann% / 90D Pct"].value)

        with tempfile.TemporaryDirectory() as tmp:
            db_file = Path(tmp) / "compat.sqlite"
            conn = sqlite3.connect(str(db_file))
            conn.execute(
                """
                CREATE TABLE telemetry_snapshots (
                    closed_4h_bar_utc TEXT PRIMARY KEY,
                    collected_at_utc TEXT NOT NULL,
                    spot_price REAL NOT NULL,
                    ok_count INTEGER NOT NULL,
                    unavailable_count INTEGER NOT NULL,
                    stale_count INTEGER NOT NULL,
                    proxy_count INTEGER NOT NULL,
                    payload_json TEXT NOT NULL
                )
                """
            )
            legacy_payload = json.dumps({
                "panels": {
                    "2_order_flow_liquidity": [],
                    "3_derivatives_options_liq": [
                        {"label": "Cross-Exch Perp OI & Funding", "value": "167k [BN+OKX 2/3 PARTIAL_VENUE]"},
                        {"label": "Funding 8H% / Ann% / P90", "value": "+0.0050% (+5.5%) · P90:12.0%"},
                    ],
                    "4_onchain_etf_stablecoins": [],
                }
            })
            new_payload = json.dumps({
                "panels": {
                    "2_order_flow_liquidity": [],
                    "3_derivatives_options_liq": [
                        {"label": "Cross-Exch Perp OI & Funding", "value": "200k [BN+BYB+OKX 3/3]"},
                        {"label": "Funding 8H% / Ann% / 90D Pct", "value": "+0.0059% (+6.5%) · 90D Pct:0.7%"},
                    ],
                    "4_onchain_etf_stablecoins": [],
                }
            })
            conn.execute(
                "INSERT INTO telemetry_snapshots VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                ("2026-11-14 16:00:00 UTC", "2026-11-14T16:05:00+00:00", 65000.0, 60, 3, 1, 2, legacy_payload),
            )
            conn.execute(
                "INSERT INTO telemetry_snapshots VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                ("2026-11-14 20:00:00 UTC", "2026-11-14T20:05:00+00:00", 64000.0, 60, 3, 1, 2, new_payload),
            )
            conn.commit()
            conn.close()

            rows = _query_tab_d_trajectory_rows(db_file, limit=6)
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0][4], "+0.0059% (+6.5%) · 90D Pct:0.7%")
            self.assertEqual(rows[1][4], "+0.0050% (+5.5%) · P90:12.0%")

    def test_ported_metrics_farside_hyperliquid_atr_pctile_cvd_ladder_calendar(self) -> None:
        from analytics.btc_magnet_engine import BTCMagnetEngine

        store = StateStore()
        store.binance_spot_price = 91_250.0
        store.open_interest_btc = 92_000.0
        store.spot_klines_1d.extend(_make_klines(n=240, step_ms=86_400_000, base_px=88_000.0))
        store.spot_klines_4h.extend(_make_klines(n=160, step_ms=14_400_000, base_px=89_500.0))
        store.spot_klines_1h.extend(_make_klines(n=60, step_ms=3_600_000, base_px=90_800.0))

        mag_ev = BTCMagnetEngine(self.cfg).evaluate(store)
        self.assertNotEqual(mag_ev.spot_cvd_slope_7d, 0.0)
        self.assertNotEqual(mag_ev.spot_cvd_slope_14d, 0.0)
        tiers = mag_ev.levels_ladder.get("tiers_6", [])
        self.assertEqual(len(tiers), 6)
        tier_prices = [t["price"] for t in tiers]
        self.assertEqual(tier_prices, sorted(tier_prices, reverse=True))

        store.macro_intermarket = MacroIntermarketSnapshot(
            agg_perp_oi_btc=210_000.0,
            agg_perp_oi_usd=19_162_500_000.0,
            agg_perp_funding_8h_pct=0.0102,
            agg_perp_venues_str="BN+BYB+OKX",
            agg_perp_venues_count=3,
            hyperliquid_oi_btc=18_450.0,
            hyperliquid_oi_usd=1_683_562_500.0,
            hyperliquid_funding_8h_pct=0.0115,
            etf_daily_net_flow_usd=315_000_000.0,
            etf_daily_net_flow_status="CONFIRMED (Farside 14 Nov 2026)",
            etf_3d_cumulative_flow_usd=640_000_000.0,
            etf_3d_cumulative_flow_status="CONFIRMED (Farside 3D to 14 Nov 2026)",
            etf_5d_cumulative_flow_usd=920_000_000.0,
            macro_calendar_fetched=True,
            macro_calendar_events=[
                {
                    "title": "CPI m/m",
                    "time_utc": "2026-11-17T13:30:00Z",
                    "minutes_away": 180.0,
                    "forecast": "0.3%",
                    "previous": "0.2%",
                }
            ],
        )

        with tempfile.TemporaryDirectory() as tmp:
            db_file = Path(tmp) / "ported.sqlite"
            ev = DataHubEngine(self.cfg, db_path=db_file, write_archive=False).evaluate(store)

        all_rows = {
            r.label: r
            for r in (
                ev.panel_1_feeds
                + ev.panel_2_trend_vol
                + ev.panel_3_structure_magnets
                + ev.panel_4_flow_quant
                + ev.panel_5_derivs_liq
                + ev.panel_6_macro_onchain
            )
        }
        self.assertEqual(ev.total_metrics, 71)
        # 1. Farside CONFIRMED status no longer dropped to UNAVAILABLE
        self.assertEqual(all_rows["US Spot ETF Flow (Farside 1D/3D)"].status, "OK")
        self.assertIn("1D:+$315.0M | 3D:+$640.0M | 5D:+$920.0M", all_rows["US Spot ETF Flow (Farside 1D/3D)"].value)
        # 2. Hyperliquid DEX row alongside intact BN+BYB+OKX 3/3
        self.assertIn("[BN+BYB+OKX 3/3]", all_rows["Cross-Exch Perp OI & Funding"].value)
        self.assertEqual(all_rows["Hyperliquid Perp OI & Funding"].status, "OK")
        self.assertIn("18,450 BTC", all_rows["Hyperliquid Perp OI & Funding"].value)
        self.assertIn("[HL DEX]", all_rows["Hyperliquid Perp OI & Funding"].value)
        # 3. 4H ATR% percentile & RelVol(20)
        self.assertEqual(all_rows["4H ATR(14)% Pctile & RelVol(20)"].status, "OK")
        self.assertIn("pct/120b", all_rows["4H ATR(14)% Pctile & RelVol(20)"].value)
        self.assertIn("RelVol:", all_rows["4H ATR(14)% Pctile & RelVol(20)"].value)
        # 4. Spot CVD 7D / 14D slopes
        self.assertEqual(all_rows["Spot CVD Slopes (7D / 14D)"].status, "OK")
        self.assertIn("7D:", all_rows["Spot CVD Slopes (7D / 14D)"].value)
        self.assertIn("14D:", all_rows["Spot CVD Slopes (7D / 14D)"].value)
        # 5. Modeled Liq Ladder
        self.assertEqual(all_rows["Modeled Liq Ladder (10x-100x)"].status, "OK")
        self.assertIn("[Modeled]", all_rows["Modeled Liq Ladder (10x-100x)"].value)
        # 6. USD Macro Calendar (High)
        self.assertEqual(all_rows["USD Macro Calendar (High)"].status, "OK")
        self.assertIn("CPI m/m", all_rows["USD Macro Calendar (High)"].value)

        # Empty-but-fetched calendar renders OK + NONE (next 7d)
        store.macro_intermarket.macro_calendar_events = []
        ev_clear = DataHubEngine(self.cfg, write_archive=False).evaluate(store)
        cal_clear = next(r for r in ev_clear.panel_5_derivs_liq if r.label == "USD Macro Calendar (High)")
        self.assertEqual(cal_clear.status, "OK")
        self.assertEqual(cal_clear.value, "NONE (next 7d)")

        # Restore event and verify Tab D Section 7C + zero forbidden words
        store.macro_intermarket.macro_calendar_events = [
            {"title": "CPI m/m", "time_utc": "2026-11-17T13:30:00Z", "minutes_away": 180.0, "forecast": "0.3%", "previous": "0.2%"}
        ]
        report = build_tab_d_data_only_report(self.cfg, store)
        self.assertIn("### 7C. MODELED LIQUIDATION LADDER (`10x-100x`) & USD MACRO CALENDAR", report)
        self.assertIn("`10x Shorts`", report)
        self.assertIn("`CPI m/m`", report)
        self.assertIn("4H ATR(14)% Pctile` & `RelVol(20)", report)
        self.assertIn("Spot CVD Slopes (7D / 14D)", report)
        self.assertIn("Hyperliquid Perp OI & Funding", report)
        self.assertIn("6-Tier Modeled Liq Ladder (7C)", report)
        self.assertIn("USD Macro Calendar (High)", report)
        self.assertIn("**Retrieval Time (SGT):**", report)
        self.assertIn("## 0. HARD DOWNTREND MARKET VETO (PRE-ENTRY CAPITAL PRESERVATION GATE)", report)
        self.assertIn("**Gate 0 — HARD DOWNTREND MARKET VETO (EVALUATE FIRST, BEFORE ALL OTHER SIGNALS):**", report)
        self.assertNotIn("MYT", report)
        for bad in ("verdict", "bullish", "bearish", "recommend", "confirmed", "trade", "wait"):
            self.assertNotIn(bad, report.lower())

    @staticmethod
    def _make_swing_klines(n: int, step_ms: int, base_px: float, slope: float, wave_amp: float = 1200.0) -> list:
        import math

        now_ms = int(datetime(2026, 11, 14, 8, 0, tzinfo=timezone.utc).timestamp() * 1000)
        out = []
        for i in range(n):
            px = base_px + (slope * i) + wave_amp * math.sin((2.0 * math.pi * i) / 14.0)
            out.append(
                KlineBar(
                    timestamp_ms=now_ms - (n - 1 - i) * step_ms,
                    open=px - 20.0,
                    high=px + 150.0,
                    low=px - 150.0,
                    close=px,
                    volume=1200.0,
                    taker_buy_volume=600.0,
                )
            )
        return out

    def test_hard_downtrend_market_veto_active_inactive_and_undetermined(self) -> None:
        ref_ms = int(datetime(2026, 11, 15, 12, 0, tzinfo=timezone.utc).timestamp() * 1000)

        # Case 1: Both Condition A (1D < SMA200) and Condition B (4H DOWNTREND / BOS Down) TRUE -> ACTIVE
        bars_1d_below = _make_klines(n=220, step_ms=86_400_000, base_px=85_000.0)
        # Drop the final closed 1D bars sharply below the 200D average
        for idx in range(205, 220):
            b = bars_1d_below[idx]
            bars_1d_below[idx] = KlineBar(
                timestamp_ms=b.timestamp_ms,
                open=66_000.0,
                high=66_500.0,
                low=63_500.0,
                close=64_150.0,
                volume=b.volume,
                taker_buy_volume=b.taker_buy_volume,
            )
        bars_4h_down = self._make_swing_klines(n=80, step_ms=14_400_000, base_px=80_000.0, slope=-200.0)
        bars_4h_up = self._make_swing_klines(n=80, step_ms=14_400_000, base_px=60_000.0, slope=+200.0)

        store_active = StateStore()
        store_active.binance_spot_price = 65_300.0
        store_active.spot_klines_1d.extend(bars_1d_below)
        store_active.spot_klines_4h.extend(bars_4h_down)
        store_active.spot_klines_1h.extend(_make_klines(n=40, step_ms=3_600_000, base_px=64_800.0))

        v_active = evaluate_hard_market_veto(store_active, spot_px=65_300.0, now_ms=ref_ms)
        self.assertEqual(v_active["cond_a"], "YES")
        self.assertEqual(v_active["sma200_pos"], "BELOW")
        self.assertEqual(v_active["cond_b"], "YES")
        self.assertEqual(v_active["struct_4h_str"], "DOWNTREND (LH/LL)")
        self.assertTrue(v_active["bos_4h_str"].startswith("YES"))
        self.assertEqual(v_active["veto_status"], "ACTIVE")
        self.assertEqual(v_active["portfolio_status"], "100% USDT CASH")
        self.assertEqual(v_active["new_entry"], "PROHIBITED")

        rep_active = build_tab_d_data_only_report(self.cfg, store_active)
        self.assertIn("- **Veto Status:** `ACTIVE`", rep_active)
        self.assertIn("- **Portfolio Status:** `100% USDT CASH`", rep_active)
        self.assertIn("- **New BTC Entry:** `PROHIBITED`", rep_active)
        for bad in ("verdict", "bullish", "bearish", "recommend", "confirmed", "trade", "wait"):
            self.assertNotIn(bad, rep_active.lower())

        # Case 2a: Only Condition A TRUE (1D < SMA200, but 4H UPTREND + no downside BOS) -> INACTIVE
        store_only_a = StateStore()
        store_only_a.binance_spot_price = 65_300.0
        store_only_a.spot_klines_1d.extend(bars_1d_below)
        store_only_a.spot_klines_4h.extend(bars_4h_up)
        v_only_a = evaluate_hard_market_veto(store_only_a, spot_px=65_300.0, now_ms=ref_ms)
        self.assertEqual(v_only_a["cond_a"], "YES")
        self.assertEqual(v_only_a["cond_b"], "NO")
        self.assertEqual(v_only_a["struct_4h_str"], "UPTREND (HH/HL)")
        self.assertTrue(v_only_a["bos_4h_str"].startswith("NO"))
        self.assertEqual(v_only_a["veto_status"], "INACTIVE")
        self.assertEqual(v_only_a["portfolio_status"], "NORMAL ASSESSMENT REQUIRED")
        self.assertEqual(v_only_a["new_entry"], "ELIGIBLE FOR FULL ASSESSMENT")

        # Case 2b: Only Condition B TRUE (1D > SMA200, 4H DOWNTREND) -> INACTIVE
        bars_1d_above = _make_klines(n=220, step_ms=86_400_000, base_px=60_000.0)
        store_only_b = StateStore()
        store_only_b.binance_spot_price = 78_000.0
        store_only_b.spot_klines_1d.extend(bars_1d_above)
        store_only_b.spot_klines_4h.extend(bars_4h_down)
        v_only_b = evaluate_hard_market_veto(store_only_b, spot_px=78_000.0, now_ms=ref_ms)
        self.assertEqual(v_only_b["cond_a"], "NO")
        self.assertEqual(v_only_b["sma200_pos"], "ABOVE")
        self.assertEqual(v_only_b["cond_b"], "YES")
        self.assertEqual(v_only_b["veto_status"], "INACTIVE")
        self.assertEqual(v_only_b["new_entry"], "ELIGIBLE FOR FULL ASSESSMENT")

        # Case 3: Missing/incomplete closed 1D series (< 200 closed 1D bars even if macro_evaluation has a cached value) -> UNDETERMINED + PROHIBITED
        store_missing = StateStore()
        store_missing.binance_spot_price = 65_300.0
        store_missing.spot_klines_1d.extend(_make_klines(n=20, step_ms=86_400_000, base_px=65_000.0))
        store_missing.macro_evaluation = SimpleNamespace(sma_200_1d=72_000.0)
        v_missing = evaluate_hard_market_veto(store_missing, spot_px=65_300.0, now_ms=ref_ms)
        self.assertEqual(v_missing["cond_a"], "UNAVAILABLE")
        self.assertEqual(v_missing["cond_b"], "UNAVAILABLE")
        self.assertEqual(v_missing["veto_status"], "UNDETERMINED")
        self.assertIn("FAIL-CLOSED", v_missing["portfolio_status"])
        self.assertEqual(v_missing["new_entry"], "PROHIBITED")

        rep_missing = build_tab_d_data_only_report(self.cfg, store_missing)
        self.assertIn("- **Veto Status:** `UNDETERMINED`", rep_missing)
        self.assertIn("- **New BTC Entry:** `PROHIBITED`", rep_missing)

        # Case 4: Verify Legacy_200D_Veto_Override, headless WS coverage breakdown, and 4H S/R clustering accuracy
        from analytics.data_only_reports import _summarize_kline_structure

        store_cov = StateStore()
        store_cov.binance_spot_price = 65_300.0
        store_cov.warmup_complete = True
        store_cov.spot_klines_1d.extend(bars_1d_below)
        store_cov.spot_klines_4h.extend(bars_4h_up)
        store_cov.spot_klines_1h.extend(_make_klines(n=40, step_ms=3_600_000, base_px=65_000.0))
        store_cov.protocol_evaluation = SimpleNamespace(
            atr_14_1d=2000.0,
            atr_14_4h=800.0,
            enforce_200d_hard_veto_on_tab1=False,
            headline_filter_status="NONE_SIGNIFICANT",
        )
        rep_cov = build_tab_d_data_only_report(self.cfg, store_cov)
        self.assertIn("Legacy_200D_Veto_Override: IGNORED", rep_cov)
        self.assertIn("Genuine=0, Expected_Headless_WS_Offline=1", rep_cov)
        for bad in ("verdict", "bullish", "bearish", "recommend", "confirmed", "trade", "wait"):
            self.assertNotIn(bad, rep_cov.lower())

        # Verify 4H 500-bar clustering surfaces multiple distinct historical support zones when below spot
        sr_4h_multi = _summarize_kline_structure(bars_4h_up, spot_px=75_500.0, tf_label="4H", interval_ms=14_400_000, now_ms=ref_ms)
        self.assertIn(",", sr_4h_multi["sup"])
        self.assertNotEqual(sr_4h_multi["sup"], "None below in lookback")

    def test_web_ui_cards_and_json_parity_preserve_markdown(self) -> None:
        import re
        from analytics.btc_magnet_engine import BTCMagnetEngine
        from scripts.publish_dd_hub import write_dashboard_artifacts

        bars_1d_below = _make_klines(n=220, step_ms=86_400_000, base_px=85_000.0)
        for idx in range(205, 220):
            b = bars_1d_below[idx]
            bars_1d_below[idx] = KlineBar(
                timestamp_ms=b.timestamp_ms,
                open=66_000.0,
                high=66_500.0,
                low=63_500.0,
                close=64_150.0,
                volume=b.volume,
                taker_buy_volume=b.taker_buy_volume,
            )

        store = StateStore()
        store.warmup_complete = True
        store.binance_spot_price = 65_300.0
        store.open_interest_btc = 92_000.0
        store.spot_klines_1d.extend(bars_1d_below)
        store.spot_klines_4h.extend(self._make_swing_klines(n=80, step_ms=14_400_000, base_px=80_000.0, slope=-200.0))
        store.spot_klines_1h.extend(_make_klines(n=40, step_ms=3_600_000, base_px=64_800.0))

        BTCMagnetEngine(self.cfg).evaluate(store)
        store.macro_intermarket = MacroIntermarketSnapshot(
            macro_calendar_fetched=True,
            macro_calendar_events=[
                {
                    "title": "CPI m/m",
                    "time_utc": "2026-11-17T13:30:00Z",
                    "minutes_away": 180.0,
                    "forecast": "0.3%",
                    "previous": "0.2%",
                }
            ],
        )

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            db_file = tmp_path / "web_ui.sqlite"
            out_dir = tmp_path / "docs"
            ev = DataHubEngine(self.cfg, db_path=db_file, write_archive=True).evaluate(store)
            md_report = build_tab_d_data_only_report(self.cfg, store, db_path=db_file)

            paths = write_dashboard_artifacts(
                output_dir=out_dir,
                ev=ev,
                md_report=md_report,
                db_path=db_file,
                repo_url="https://github.com/example/btc-swing-engine",
                pages_url="https://example.github.io/btc-swing-engine/",
                utc_str="2026-11-16 00:30:00 UTC",
                sgt_str="2026-11-16 08:30:00 SGT (UTC+8)",
                also_write_logs=False,
                store=store,
            )

            json_payload = json.loads(paths["json"].read_text(encoding="utf-8"))
            self.assertEqual(json_payload["stale_breakdown"]["expected_headless_ws_offline"], 1)
            self.assertEqual(json_payload["stale_breakdown"]["genuine"], 0)
            self.assertEqual(json_payload["section_0_veto"]["veto_status"], "ACTIVE")
            self.assertEqual(len(json_payload["section_7a_structure"]), 3)
            self.assertEqual(len(json_payload["section_7c"]["liquidation_ladder"]), 6)
            self.assertEqual(len(json_payload["section_7c"]["macro_calendar"]), 1)

            html_txt = paths["html"].read_text(encoding="utf-8")
            self.assertIn('id="veto" class="veto-banner veto-active"', html_txt)
            self.assertIn("WS_Off=1", html_txt)
            self.assertIn('id="snapshot-age"', html_txt)
            self.assertIn('id="flt-issues"', html_txt)
            self.assertIn('id="structure-7a"', html_txt)
            self.assertIn('id="liq-macro-7c"', html_txt)
            self.assertIn("10x Shorts", html_txt)
            self.assertIn("CPI m/m", html_txt)

            m_payload = re.search(
                r'<script type="application/json" id="dd-markdown-payload">(.*?)</script>',
                html_txt,
                flags=re.DOTALL,
            )
            self.assertIsNotNone(m_payload)
            decoded_md = json.loads(m_payload.group(1))
            self.assertEqual(decoded_md, md_report)

            # Empty-but-fetched calendar renders CLEAR / NONE (next 7d) in 7C-2
            store.macro_intermarket.macro_calendar_events = []
            ev_clear = DataHubEngine(self.cfg, db_path=db_file, write_archive=False).evaluate(store)
            md_clear = build_tab_d_data_only_report(self.cfg, store, db_path=db_file)
            paths_clear = write_dashboard_artifacts(
                output_dir=out_dir,
                ev=ev_clear,
                md_report=md_clear,
                db_path=db_file,
                repo_url="https://github.com/example/btc-swing-engine",
                pages_url="https://example.github.io/btc-swing-engine/",
                utc_str="2026-11-16 00:35:00 UTC",
                sgt_str="2026-11-16 08:35:00 SGT (UTC+8)",
                also_write_logs=False,
                store=store,
            )
            html_clear = paths_clear["html"].read_text(encoding="utf-8")
            self.assertIn("NONE (next 7d)", html_clear)
            self.assertIn("CLEAR", html_clear)


if __name__ == "__main__":
    unittest.main()
