"""Synthetic isolated contract tests for Alert Flagging, Pattern Grouping & Rule Tuning Tracker."""
from __future__ import annotations

import json
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from tests.test_ui_api import SyntheticDB, load_isolated_api


class FlagWorkspaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.api = load_isolated_api()

    def setUp(self):
        self.db = SyntheticDB()
        self.db_patch = patch.object(self.api, "get_db", self.db.session)
        self.db_patch.start()
        self.client = TestClient(self.api.app)

    def tearDown(self):
        self.client.close()
        self.db_patch.stop()
        self.db.connection.close()

    def _seed_rich_alerts(self):
        self.db.add_alert(
            10, "Alpha",
            alert_id="syn-10",
            timestamp="2026-11-18T10:00:00Z",
            agent_name="web-01",
            rule_id="31101",
            rule_level=7,
            description="Web server 400 error code.",
            source_ip="192.0.2.50",
            hit_count=5,
            data=json.dumps({"url": "/lib/minigalnano/createthumb.php?w=120", "status": "400"}),
            parsed_details=json.dumps({
                "method": "GET",
                "status": "400",
                "uri": "/lib/minigalnano/createthumb.php?w=120",
                "path": "/lib/minigalnano/createthumb.php",
                "referer": "https://portal.example.test/gallery",
                "ua": "Mozilla/5.0 SyntheticCrawler",
            }),
            raw=json.dumps({
                "full_log": '192.0.2.50 - - [18/Nov/2026:10:00:00 +0700] "GET /lib/minigalnano/createthumb.php?w=120 HTTP/1.1" 400 321 "https://portal.example.test/gallery" "Mozilla/5.0 SyntheticCrawler"'
            }),
        )
        self.db.add_alert(
            11, "Alpha",
            alert_id="syn-11",
            timestamp="2026-11-18T11:00:00Z",
            agent_name="web-01",
            rule_id="31101",
            rule_level=7,
            description="Web server 400 error code.",
            source_ip="192.0.2.50",
            hit_count=3,
            data=json.dumps({"url": "/lib/minigalnano/createthumb.php?w=240", "status": "400"}),
            parsed_details=json.dumps({
                "method": "GET",
                "status": "400",
                "uri": "/lib/minigalnano/createthumb.php?w=240",
                "path": "/lib/minigalnano/createthumb.php",
                "referer": "https://portal.example.test/gallery",
                "ua": "Mozilla/5.0 SyntheticCrawler",
            }),
            raw=json.dumps({
                "full_log": '192.0.2.50 - - [18/Nov/2026:11:00:00 +0700] "GET /lib/minigalnano/createthumb.php?w=240 HTTP/1.1" 400 321 "https://portal.example.test/gallery" "Mozilla/5.0 SyntheticCrawler"'
            }),
        )
        self.db.add_alert(
            12, "Alpha",
            alert_id="syn-12",
            timestamp="2026-11-18T12:00:00Z",
            agent_name="db-01",
            rule_id="5710",
            rule_level=12,
            description="Attempt to login using a non-existent user",
            source_ip="198.51.100.99",
            hit_count=9,
            data=json.dumps({"url": "/admin/login.php", "status": "403"}),
            parsed_details=json.dumps({
                "method": "POST",
                "status": "403",
                "uri": "/admin/login.php",
                "path": "/admin/login.php",
                "referer": "https://evil.example.test",
                "ua": "sqlmap/1.7",
            }),
            raw=json.dumps({"full_log": 'POST /admin/login.php from 198.51.100.99 ua=sqlmap/1.7'}),
        )
        self.db.add_alert(
            13, "Beta",
            alert_id="syn-13",
            timestamp="2026-11-18T13:00:00Z",
            agent_name="web-beta",
            rule_id="31101",
            rule_level=7,
            description="Web server 400 error code.",
            source_ip="203.0.113.10",
            hit_count=2,
            data=json.dumps({"url": "/favicon.ico", "status": "404"}),
            parsed_details=json.dumps({"method": "GET", "status": "404", "path": "/favicon.ico", "ua": "curl/8.0"}),
            raw=json.dumps({"full_log": 'GET /favicon.ico 404'}),
        )

    def test_ac1_unreviewed_alert_rejected_without_auto_review_and_auto_review_succeeds(self):
        # Alert 1 starts unreviewed. Calling standalone flag without auto_review must reject with 400.
        denied = self.client.post(
            "/api/alerts/flag",
            params={"tenant": "Alpha"},
            json={"alert_ids": [1], "flag_color": "green"},
        )
        self.assertEqual(denied.status_code, 400, denied.text)

        # Direct review+flag from Triage uses auto_review=True -> reviews & flags atomically.
        flagged = self.client.post(
            "/api/alerts/flag",
            params={"tenant": "Alpha"},
            json={"alert_ids": [1], "flag_color": "green", "auto_review": True, "flagged_by": "analis_a"},
        )
        self.assertEqual(flagged.status_code, 200, flagged.text)
        body = flagged.json()
        self.assertEqual(body["flag_color"], "green")
        self.assertEqual(body["verdict"], "fp")
        self.assertEqual(body["flagged_by"], "analis_a")
        self.assertEqual(body["summary"]["counts"]["green"]["pending"], 1)

        detail = self.client.get("/api/alerts/1", params={"tenant": "Alpha"}).json()
        self.assertTrue(detail["is_reviewed"])
        self.assertEqual(detail["flag_color"], "green")
        self.assertEqual(detail["flagged_by"], "analis_a")
        self.assertEqual(detail["rule_status"], "pending")

        # Color can be changed directly because alert is already reviewed (auto_review=False allowed).
        changed = self.client.put(
            "/api/alerts/1/flag",
            params={"tenant": "Alpha"},
            json={"flag_color": "yellow", "flagged_by": "analis_b"},
        )
        self.assertEqual(changed.status_code, 200, changed.text)
        self.assertEqual(changed.json()["flag_color"], "yellow")

        # Un-reviewing clears the flag and rule status.
        unrev = self.client.post(
            "/api/alerts/batch-review",
            params={"tenant": "Alpha"},
            json={"alert_ids": [1], "is_reviewed": False},
        )
        self.assertEqual(unrev.status_code, 200, unrev.text)
        cleared = self.client.get("/api/alerts/1", params={"tenant": "Alpha"}).json()
        self.assertFalse(cleared["is_reviewed"])
        self.assertIsNone(cleared["flag_color"])

    def test_all_12_grouping_dimensions_and_bulk_rule_tuning_workflow(self):
        self._seed_rich_alerts()
        self.client.post(
            "/api/alerts/flag",
            json={"alert_ids": [10, 11, 13], "flag_color": "green", "auto_review": True, "flagged_by": "analis1"},
        )
        self.client.post(
            "/api/alerts/flag",
            json={"alert_ids": [12], "flag_color": "yellow", "auto_review": True, "flagged_by": "analis1"},
        )

        # Default GET /api/flags/groups loads green + pending grouped by rule_description
        default_groups = self.client.get("/api/flags/groups").json()
        self.assertEqual(default_groups["flag_color"], "green")
        self.assertEqual(default_groups["rule_status"], "pending")
        self.assertEqual(default_groups["total_alerts"], 3)
        self.assertEqual(default_groups["pending_tuning"], 4)
        self.assertEqual(default_groups["groups"][0]["key"], "Web server 400 error code.")
        self.assertEqual(default_groups["groups"][0]["alert_count"], 3)
        self.assertEqual(default_groups["groups"][0]["event_hits"], 10)

        # Test all 12 PRD dimensions (11 attribute dimensions + pattern substring & regex)
        dimension_expectations = {
            "rule_description": "Web server 400 error code.",
            "rule_id": "31101",
            "severity": "medium",
            "source_ip": "192.0.2.50",
            "agent": "web-01",
            "http_status": "400",
            "http_method": "GET",
            "url_path": "/lib/minigalnano/createthumb.php",
            "referer": "https://portal.example.test/gallery",
            "user_agent": "Mozilla/5.0 SyntheticCrawler",
            "tenant": "Alpha",
        }
        for dim, expected_key in dimension_expectations.items():
            resp = self.client.get("/api/flags/groups", params={"tenant": "Alpha", "flag_color": "green", "group_by": dim})
            self.assertEqual(resp.status_code, 200, f"{dim}: {resp.text}")
            keys = [g["key"] for g in resp.json()["groups"]]
            self.assertIn(expected_key, keys, f"Missing expected key for {dim}: {keys}")

        # Pattern text dimension (both contains and regex)
        pat_contains = self.client.get(
            "/api/flags/groups",
            params={"tenant": "Alpha", "flag_color": "green", "group_by": "pattern", "pattern": "createthumb.php"},
        )
        self.assertEqual(pat_contains.status_code, 200)
        self.assertEqual(pat_contains.json()["groups"][0]["key"], "Cocok pola")
        self.assertEqual(pat_contains.json()["groups"][0]["alert_count"], 2)

        pat_regex = self.client.get(
            "/api/flags/groups",
            params={"tenant": "Alpha", "flag_color": "green", "group_by": "pattern", "pattern": r"createthumb\.php\?w=240", "pattern_mode": "regex"},
        )
        self.assertEqual(pat_regex.status_code, 200)
        by_key = {g["key"]: g["alert_count"] for g in pat_regex.json()["groups"]}
        self.assertEqual(by_key.get("Cocok pola"), 1)
        self.assertEqual(by_key.get("Tidak cocok pola"), 1)

        # Expanding group loads individual member alerts with full_log
        members = self.client.get(
            "/api/flags/alerts",
            params={
                "tenant": "Alpha",
                "flag_color": "green",
                "rule_status": "pending",
                "group_by": "url_path",
                "group_key": "/lib/minigalnano/createthumb.php",
            },
        )
        self.assertEqual(members.status_code, 200, members.text)
        self.assertEqual({m["id"] for m in members.json()["items"]}, {10, 11})

        # Bulk mark entire pattern group as Rule Sudah Dibuat (#100145)
        done_resp = self.client.post(
            "/api/flags/rule-status",
            params={"tenant": "Alpha"},
            json={
                "rule_status": "done",
                "custom_rule_id": "100145",
                "rule_notes": "Whitelist thumbnail generator kampus",
                "rule_updated_by": "rule_eng",
                "flag_color": "green",
                "group_by": "url_path",
                "group_key": "/lib/minigalnano/createthumb.php",
            },
        )
        self.assertEqual(done_resp.status_code, 200, done_resp.text)
        self.assertEqual(done_resp.json()["updated"], 2)
        self.assertEqual(done_resp.json()["summary"]["counts"]["green"]["done"], 2)
        self.assertEqual(done_resp.json()["summary"]["counts"]["green"]["pending"], 0)
        global_summary = self.client.get("/api/flags/summary").json()
        self.assertEqual(global_summary["counts"]["green"]["pending"], 1)  # alert 13 in Beta still pending

        # Alpha pending view should now be empty, while done view shows #100145 & audit trail
        alpha_pending = self.client.get(
            "/api/flags/groups",
            params={"tenant": "Alpha", "flag_color": "green", "rule_status": "pending"},
        ).json()
        self.assertEqual(alpha_pending["total_alerts"], 0)

        alpha_done = self.client.get(
            "/api/flags/groups",
            params={"tenant": "Alpha", "flag_color": "green", "rule_status": "done", "group_by": "url_path"},
        ).json()
        self.assertEqual(alpha_done["total_alerts"], 2)
        self.assertEqual(alpha_done["groups"][0]["custom_rule_id"], "100145")
        self.assertEqual(alpha_done["groups"][0]["rule_updated_by"], "rule_eng")
        self.assertEqual(alpha_done["groups"][0]["rule_notes"], "Whitelist thumbnail generator kampus")

    def test_red_flag_cannot_be_marked_rule_done_and_bulk_pattern_supports_flag(self):
        self._seed_rich_alerts()
        self.client.post(
            "/api/alerts/flag",
            params={"tenant": "Alpha"},
            json={"alert_ids": [12], "flag_color": "red", "auto_review": True},
        )
        # Attempting by alert_ids fails with 400
        bad_id = self.client.post(
            "/api/flags/rule-status",
            params={"tenant": "Alpha"},
            json={"alert_ids": [12], "rule_status": "done", "custom_rule_id": "100999"},
        )
        self.assertEqual(bad_id.status_code, 400, bad_id.text)

        # Attempting by group with flag_color=red fails with 400
        bad_grp = self.client.post(
            "/api/flags/rule-status",
            params={"tenant": "Alpha"},
            json={"flag_color": "red", "group_by": "rule_id", "group_key": "5710", "rule_status": "done"},
        )
        self.assertEqual(bad_grp.status_code, 400, bad_grp.text)

        # Bulk pattern sweep in Triage supports flag_color directly
        sweep = self.client.post(
            "/api/alerts/bulk-verdict-pattern",
            params={"tenant": "Alpha"},
            json={"rule_id": "31101", "flag_color": "green", "reviewed_by": "analis_bulk"},
        )
        self.assertEqual(sweep.status_code, 200, sweep.text)
        self.assertEqual(sweep.json()["count"], 2)
        self.assertEqual(sweep.json()["flag_color"], "green")
        self.assertEqual(self.client.get("/api/alerts/10", params={"tenant": "Alpha"}).json()["flag_color"], "green")

    def test_flag_group_queries_bind_untrusted_text_safely(self):
        self._seed_rich_alerts()
        self.client.post(
            "/api/alerts/flag",
            params={"tenant": "Alpha"},
            json={"alert_ids": [10], "flag_color": "green", "auto_review": True},
        )
        sqli = "'; DROP TABLE wazuh.alerts; --"
        resp = self.client.get(
            "/api/flags/groups",
            params={"tenant": "Alpha", "flag_color": "green", "group_by": "pattern", "pattern": sqli, "q": sqli},
        )
        self.assertEqual(resp.status_code, 200, resp.text)
        self.assertEqual(self.client.get("/api/alerts/10", params={"tenant": "Alpha"}).status_code, 200)


if __name__ == "__main__":
    unittest.main()
