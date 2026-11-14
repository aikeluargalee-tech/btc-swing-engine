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
from analytics.data_only_reports import build_tab_d_data_only_report, copy_tab_data_only_report_to_clipboard
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

        self.assertEqual(ev.total_metrics, 66)
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

            self.assertEqual(ev.total_metrics, 66)
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
            self.assertIn("Spr:0.14bps", all_rows["L2 Depth ±1%/±2%, OBI & Spread"].value)
            self.assertIn("[BN+BYB+OKX]", all_rows["Cross-Exch Perp OI & Funding"].value)
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
            report = build_tab_d_data_only_report(self.cfg, store)
            self.assertIn("TAB [D: DATA HUB] | CONSOLIDATED DATA-ONLY TELEMETRY REPORT", report)
            self.assertIn("1 closed-4H snapshots (Last: 2026-11-14 08:00:00 UTC)", report)
            self.assertIn("## 5. MACRO, CREDIT & US LIQUIDITY", report)
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
        self.assertIn("ADX 1D:28.1 4H:34.6", p1["ADX(14) 1D/4H & ATR(14)"].value)

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
            md_report = build_tab_d_data_only_report(self.cfg, store)

            paths = write_dashboard_artifacts(
                output_dir=out_dir,
                ev=ev,
                md_report=md_report,
                db_path=db_file,
                repo_url="https://github.com/example/btc-swing-engine",
                pages_url="https://example.github.io/btc-swing-engine/",
                utc_str="2026-11-14 15:30:00 UTC",
                myt_str="2026-11-14 23:30:00 MYT (UTC+8)",
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
                myt_str="2026-11-14 23:30:00 MYT (UTC+8)",
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
                myt_str="2026-11-14 23:30:00 MYT (UTC+8)",
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
                        myt_str="2026-11-14 23:30:00 MYT (UTC+8)",
                        pages_url="https://example.github.io/btc-swing-engine/",
                        repo_url="https://github.com/example/btc-swing-engine",
                    )
                )
            self.assertEqual(len(posted_urls), 3)
            self.assertTrue(posted_urls[0].endswith("/sendMessage"))
            self.assertTrue(posted_urls[1].endswith("/sendMessage"))
            self.assertTrue(posted_urls[2].endswith("/sendDocument"))


if __name__ == "__main__":
    unittest.main()
