"""Unit tests for the FastAPI Mobile API Gateway and Setup B PWA endpoints."""

import json
import unittest
from starlette.testclient import TestClient

from api.mobile_server import app, get_latest_metrics


class TestMobileAPIGateway(unittest.TestCase):
    """Test suite covering Setup B mobile REST endpoints and WebSocket stream."""

    def setUp(self):
        self.client = TestClient(app)

    def test_health_endpoint(self):
        """Verifies GET /api/v1/health returns 200 and healthy status."""
        response = self.client.get("/api/v1/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("status"), "healthy")
        self.assertEqual(data.get("service"), "btc_swing_mobile_gateway")
        self.assertIn("BTC Swing Engine", data.get("engine", ""))

    def test_metrics_latest_schema(self):
        """Verifies GET /api/v1/metrics/latest matches the Setup B mobile specification."""
        response = self.client.get("/api/v1/metrics/latest")
        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Required top-level fields
        required_keys = [
            "timestamp_utc",
            "spot_price",
            "confluence_score",
            "confluence_label",
            "regime",
            "trade_plan",
            "pillars",
            "deep_dive",
            "ai_audit_snippet",
        ]
        for key in required_keys:
            self.assertIn(key, data, f"Missing required key: {key}")

        # Confluence Score sanity (0 - 100)
        score = data["confluence_score"]
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 100.0)

    def test_trade_plan_risk_math(self):
        """Verifies the deterministic 0.75% equity risk cap ($750 on $100k)."""
        metrics = get_latest_metrics()
        plan = metrics["trade_plan"]

        self.assertIn("is_active", plan)
        self.assertEqual(plan["max_risk_usd"], 750.0)
        self.assertEqual(plan["risk_pct_equity"], 0.75)

        entry = plan["suggested_entry"]
        stop = plan["invalidation_floor"]
        self.assertLess(stop, entry, "Invalidation floor must be strictly below entry price")

        tp1 = plan["take_profit_1"]
        tp2 = plan["take_profit_2"]
        self.assertGreater(tp1, entry, "TP1 must be above entry")
        self.assertGreater(tp2, tp1, "TP2 must be above TP1")

        # Position Sizing math verification: Size = Risk / (Entry - Stop)
        risk_per_btc = entry - stop
        expected_size = round(750.0 / risk_per_btc, 4)
        self.assertAlmostEqual(plan["position_size_btc"], expected_size, places=4)

    def test_four_pillars_present(self):
        """Verifies all 4 quantitative confluence pillars are populated."""
        metrics = get_latest_metrics()
        pillars = metrics["pillars"]

        pillar_keys = ["order_flow", "derivatives", "macro", "volatility"]
        for pkey in pillar_keys:
            self.assertIn(pkey, pillars, f"Missing pillar: {pkey}")
            pdata = pillars[pkey]
            self.assertIn("score", pdata)
            self.assertIn("max", pdata)
            self.assertIn("pct", pdata)
            self.assertIn("status", pdata)
            self.assertIn("summary", pdata)

    def test_ai_packet_endpoint(self):
        """Verifies GET /api/v1/ai-packet delivers plain-text markdown."""
        response = self.client.get("/api/v1/ai-packet")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/plain", response.headers.get("content-type", ""))
        self.assertGreater(len(response.text), 100)

    def test_pwa_static_delivery(self):
        """Verifies static files (index.html, manifest.json, app.js) are properly delivered."""
        # Root index.html
        res_root = self.client.get("/")
        self.assertEqual(res_root.status_code, 200)
        self.assertIn("BTC SWING COCKPIT", res_root.text)

        # manifest.json
        res_manifest = self.client.get("/manifest.json")
        self.assertEqual(res_manifest.status_code, 200)
        manifest_data = res_manifest.json()
        self.assertEqual(manifest_data.get("short_name"), "BTC Swing")

        # app.js
        res_js = self.client.get("/app.js")
        self.assertEqual(res_js.status_code, 200)
        self.assertIn("initDataFeed", res_js.text)

    def test_websocket_stream(self):
        """Verifies WebSocket /ws/metrics connects and streams valid JSON payload."""
        with self.client.websocket_connect("/ws/metrics") as ws:
            data_text = ws.receive_text()
            data = json.loads(data_text)
            self.assertIn("confluence_score", data)
            self.assertIn("trade_plan", data)
            self.assertIn("pillars", data)


if __name__ == "__main__":
    unittest.main()
