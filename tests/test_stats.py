"""Isolated synthetic contract tests for Arbiter statistics and triage summary endpoints.

Uses SyntheticDB in-memory SQLite only; never touches production database or .env.
"""
from __future__ import annotations

import json
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient

from tests.test_ui_api import load_isolated_api, SyntheticDB, GROUP, OTHER_GROUP


class StatsEndpointContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.api = load_isolated_api()

    def setUp(self):
        self.db = SyntheticDB()
        self.db_patch = patch.object(self.api, "get_db", self.db.session)
        self.db_patch.start()
        self.client = TestClient(self.api.app)

        # Populate a diverse set of synthetic alerts across multiple tenants, rules, and HTTP fields
        # Current db has pk 1 (Alpha, hit_count 3), pk 2 (Beta, hit_count 3), pk 3 (Alpha, hit_count 1, reviewed)
        # Add additional synthetic alerts:
        self.db.add_alert(
            10, "Alpha",
            alert_id="syn-10", timestamp="2026-01-01T10:05:00Z",
            agent_name="host-web-1", rule_id="1001", rule_level=12,
            description="SQL injection probe", source_ip="203.0.113.5",
            hit_count=5, is_reviewed=False,
            parsed_details='{"status":"403","path":"/login.php","referer":"http://evil.com","ua":"sqlmap/1.0","log_type":"http"}',
        )
        self.db.add_alert(
            11, "Alpha",
            alert_id="syn-11", timestamp="2026-01-01T10:15:00Z",
            agent_name="host-web-1", rule_id="1001", rule_level=12,
            description="SQL injection probe", source_ip="203.0.113.5",
            hit_count=10, is_reviewed=False,
            parsed_details='{"status":"403","path":"/admin.php","referer":"http://evil.com","ua":"sqlmap/1.0","log_type":"http"}',
        )
        self.db.add_alert(
            12, "Alpha",
            alert_id="syn-12", timestamp="2026-01-01T11:20:00Z",
            agent_name="host-web-2", rule_id="2002", rule_level=7,
            description="Suspicious user agent", source_ip="198.51.100.22",
            hit_count=2, is_reviewed=True,
            parsed_details='{"status":"200","path":"/index.html","referer":"","ua":"curl/7.68.0","log_type":"http"}',
        )
        self.db.add_alert(
            13, "Beta",
            alert_id="syn-13", timestamp="2026-01-01T12:00:00Z",
            agent_name="host-db-1", rule_id="3003", rule_level=5,
            description="Database login failure", source_ip="192.0.2.99",
            hit_count=1, is_reviewed=False,
            parsed_details='{"log_type":"syslog"}',
        )

    def tearDown(self):
        self.client.close()
        self.db_patch.stop()
        self.db.connection.close()

    def test_stats_validates_pivot_by_against_whitelist(self):
        # Invalid pivot_by must fail with 422 before SQL
        res = self.client.get("/api/stats", params={"pivot_by": "invalid_column"})
        self.assertEqual(res.status_code, 422, res.text)
        self.assertIn("pivot_by", res.json()["detail"].lower())

    def test_stats_validates_top_n_bounds(self):
        for bad_top in (0, -1, 51, 100):
            res = self.client.get("/api/stats", params={"top_n": bad_top})
            self.assertEqual(res.status_code, 422, res.text)

    def test_stats_validates_pattern_pivot_requires_literal_pattern(self):
        res = self.client.get("/api/stats", params={"pivot_by": "pattern"})
        self.assertEqual(res.status_code, 422, res.text)
        self.assertIn("pattern", res.json()["detail"].lower())

        long_pattern = "x" * 121
        res2 = self.client.get("/api/stats", params={"pivot_by": "pattern", "pattern": long_pattern})
        self.assertEqual(res2.status_code, 422, res2.text)

    def test_stats_pivot_by_rule_description_alerts_metric(self):
        res = self.client.get("/api/stats", params={"tenant": "Alpha", "pivot_by": "rule_description", "metric": "alerts"})
        self.assertEqual(res.status_code, 200, res.text)
        data = res.json()
        self.assertEqual(data["pivot_by"], "rule_description")
        self.assertEqual(data["metric"], "alerts")
        self.assertEqual(data["total"], 5)  # 5 alerts in Alpha: pk 1, 3, 10, 11, 12
        items = data["items"]
        self.assertTrue(len(items) > 0)
        # Sum of items + other_count == total
        item_total = sum(item["count"] for item in items) + data["other_count"]
        self.assertEqual(item_total, data["total"])
        # Check rule 1001 description has count 2
        sqli_item = next((it for it in items if it["key"] == "SQL injection probe"), None)
        self.assertIsNotNone(sqli_item)
        self.assertEqual(sqli_item["count"], 2)

    def test_stats_pivot_by_rule_description_events_metric(self):
        res = self.client.get("/api/stats", params={"tenant": "Alpha", "pivot_by": "rule_description", "metric": "events"})
        self.assertEqual(res.status_code, 200, res.text)
        data = res.json()
        self.assertEqual(data["metric"], "events")
        # pk 1: 3, pk 3: 1, pk 10: 5, pk 11: 10, pk 12: 2 -> total hits = 21
        self.assertEqual(data["total"], 21)
        sqli_item = next((it for it in data["items"] if it["key"] == "SQL injection probe"), None)
        self.assertIsNotNone(sqli_item)
        self.assertEqual(sqli_item["count"], 15)  # 5 + 10

    def test_stats_pivot_distribution_and_other_bucket(self):
        # With top_n=1, the top item is displayed and the rest goes to other_count
        res = self.client.get("/api/stats", params={"tenant": "Alpha", "pivot_by": "source_ip", "top_n": 1})
        self.assertEqual(res.status_code, 200, res.text)
        data = res.json()
        self.assertEqual(len(data["items"]), 1)
        self.assertGreater(data["other_count"], 0)
        self.assertEqual(data["items"][0]["count"] + data["other_count"], data["total"])
        self.assertAlmostEqual(data["items"][0]["percentage"] + data["other_percentage"], 100.0, places=1)

    def test_stats_pivot_by_severity(self):
        res = self.client.get("/api/stats", params={"tenant": "Alpha", "pivot_by": "severity"})
        self.assertEqual(res.status_code, 200, res.text)
        data = res.json()
        keys = {it["key"].lower() for it in data["items"]}
        # In Alpha we have level 12 (critical), level 7 (medium)
        self.assertIn("critical", keys)
        self.assertIn("medium", keys)

    def test_stats_pivot_by_parsed_http_fields(self):
        for pivot in ("http_status", "url_path", "referer", "user_agent"):
            with self.subTest(pivot=pivot):
                res = self.client.get("/api/stats", params={"tenant": "Alpha", "pivot_by": pivot})
                self.assertEqual(res.status_code, 200, res.text)
                data = res.json()
                self.assertEqual(data["pivot_by"], pivot)
                self.assertIn("items", data)
                self.assertEqual(sum(it["count"] for it in data["items"]) + data["other_count"], data["total"])

    def test_stats_literal_pattern_matching(self):
        res = self.client.get("/api/stats", params={"tenant": "Alpha", "pivot_by": "pattern", "pattern": "sqlmap"})
        self.assertEqual(res.status_code, 200, res.text)
        data = res.json()
        match_item = next((it for it in data["items"] if "cocok" in it["key"].lower() and "tidak" not in it["key"].lower()), None)
        self.assertIsNotNone(match_item)
        self.assertEqual(match_item["count"], 2)  # syn-10 and syn-11 have sqlmap in parsed_details

    def test_stats_respects_tenant_isolation(self):
        res_alpha = self.client.get("/api/stats", params={"tenant": "Alpha", "pivot_by": "tenant"})
        self.assertEqual(res_alpha.status_code, 200)
        self.assertEqual(res_alpha.json()["total"], 5)
        self.assertEqual(len(res_alpha.json()["items"]), 1)
        self.assertEqual(res_alpha.json()["items"][0]["key"], "Alpha")

        res_multi = self.client.get("/api/stats", params=[("tenant", "Alpha"), ("tenant", "Beta"), ("pivot_by", "tenant")])
        self.assertEqual(res_multi.status_code, 200)
        self.assertEqual(res_multi.json()["total"], 7)  # 5 in Alpha + 2 in Beta

    def test_triage_summary_matches_filtered_alerts_count(self):
        # Test summary matches list_alerts total
        for tenant_param in ({"tenant": "Alpha"}, {"tenant": "Beta"}, {"tenant": "all"}):
            with self.subTest(tenant=tenant_param):
                alerts_res = self.client.get("/api/alerts", params=tenant_param)
                summary_res = self.client.get("/api/triage/summary", params=tenant_param)
                self.assertEqual(alerts_res.status_code, 200)
                self.assertEqual(summary_res.status_code, 200, summary_res.text)

                alerts_total = alerts_res.json()["total"]
                summary_data = summary_res.json()
                self.assertEqual(summary_data["alerts"], alerts_total)
                self.assertIsInstance(summary_data["events"], int)
                self.assertGreaterEqual(summary_data["events"], alerts_total)
                self.assertIn("severity", summary_data)
                self.assertIn("unique_source_ips", summary_data)
                self.assertIn("unique_agents", summary_data)
                self.assertIn("incident_cases", summary_data)
                self.assertIn("time_range", summary_data)
                self.assertIn("top_rule", summary_data)

    def test_triage_summary_top_rule_and_severity_breakdown(self):
        res = self.client.get("/api/triage/summary", params={"tenant": "Alpha"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["severity"]["critical"], 2)  # syn-10 and syn-11 (level 12)
        top_rule = data["top_rule"]
        self.assertIsNotNone(top_rule)
        self.assertEqual(top_rule["rule_id"], "1001")
        self.assertEqual(top_rule["count"], 2)


if __name__ == "__main__":
    unittest.main()
