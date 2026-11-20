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

    def test_monitoring_returns_three_flag_categories(self):
        self._seed_rich_alerts()
        self.db.add_alert(
            14, "Alpha",
            alert_id="syn-14",
            timestamp="2026-11-18T14:00:00Z",
            agent_name="web-01",
            rule_id="9999",
            rule_level=12,
            description="Critical exploit attempt",
        )
        self.client.post(
            "/api/alerts/flag",
            params={"tenant": "Alpha"},
            json={"alert_ids": [10, 11], "flag_color": "green", "auto_review": True},
        )
        self.client.post(
            "/api/alerts/flag",
            params={"tenant": "Alpha"},
            json={"alert_ids": [12], "flag_color": "yellow", "auto_review": True},
        )
        self.client.post(
            "/api/alerts/flag",
            params={"tenant": "Alpha"},
            json={"alert_ids": [14], "flag_color": "red", "auto_review": True},
        )
        resp = self.client.get("/api/monitoring", params={"tenant": "Alpha"})
        self.assertEqual(resp.status_code, 200, resp.text)
        body = resp.json()
        self.assertEqual(body["metrics"]["flags"], {"green": 2, "yellow": 1, "red": 1})
        analyst_row = next((r for r in body["leaderboard"] if r["username"] == "analyst"), None)
        self.assertIsNotNone(analyst_row)
        self.assertEqual(analyst_row["green_count"], 2)
        self.assertEqual(analyst_row["yellow_count"], 1)
        self.assertEqual(analyst_row["red_count"], 1)
        self.assertEqual(analyst_row["total_contributions"], 4)

    def test_unreview_single_and_batch_clears_flag_claim_and_rule_tuning(self):
        self._seed_rich_alerts()
        self.client.post(
            "/api/alerts/flag",
            params={"tenant": "Alpha"},
            json={"alert_ids": [10, 11], "flag_color": "green", "auto_review": True},
        )
        self.client.post(
            "/api/flags/rule-status",
            params={"tenant": "Alpha"},
            json={"alert_ids": [10], "rule_status": "done", "custom_rule_id": "100145", "rule_notes": "Whitelist"},
        )
        self.client.put(
            "/api/alerts/11/flag",
            params={"tenant": "Alpha"},
            json={"flag_color": "yellow", "auto_review": True},
        )

        res_single = self.client.put(
            "/api/alerts/10/review",
            params={"tenant": "Alpha"},
            json={"is_reviewed": False},
        )
        self.assertEqual(res_single.status_code, 200, res_single.text)
        self.assertFalse(res_single.json()["is_reviewed"])
        self.assertIsNone(res_single.json()["flag_color"])
        row10 = self.db.connection.execute(
            """SELECT is_reviewed, status, verdict, reviewed_by, claimed_by, claimed_at,
                      flag_color, flagged_by, rule_status, custom_rule_id
               FROM wazuh.alerts WHERE id = 10"""
        ).fetchone()
        self.assertEqual(row10["is_reviewed"], 0)
        self.assertEqual(row10["status"], "unread")
        self.assertIsNone(row10["verdict"])
        self.assertIsNone(row10["reviewed_by"])
        self.assertIsNone(row10["claimed_by"])
        self.assertIsNone(row10["claimed_at"])
        self.assertIsNone(row10["flag_color"])
        self.assertIsNone(row10["flagged_by"])
        self.assertEqual(row10["rule_status"], "pending")
        self.assertIsNone(row10["custom_rule_id"])

        res_batch = self.client.post(
            "/api/alerts/batch-review",
            params={"tenant": "Alpha"},
            json={"alert_ids": [11], "is_reviewed": False},
        )
        self.assertEqual(res_batch.status_code, 200, res_batch.text)
        row11 = self.db.connection.execute(
            """SELECT is_reviewed, status, verdict, reviewed_by, flag_color, flagged_by
               FROM wazuh.alerts WHERE id = 11"""
        ).fetchone()
        self.assertEqual(row11["is_reviewed"], 0)
        self.assertEqual(row11["status"], "unread")
        self.assertIsNone(row11["verdict"])
        self.assertIsNone(row11["reviewed_by"])
        self.assertIsNone(row11["flag_color"])
        self.assertIsNone(row11["flagged_by"])

    def test_group_unflag_and_group_unreview_endpoints(self):
        self._seed_rich_alerts()
        self.client.post(
            "/api/alerts/flag",
            params={"tenant": "Alpha"},
            json={"alert_ids": [10, 11], "flag_color": "green", "auto_review": True},
        )

        # Group unflag only: alerts lose Flag but stay reviewed
        res_unflag = self.client.post(
            "/api/alerts/flag",
            params={"tenant": "Alpha"},
            json={
                "flag_color": None,
                "current_flag_color": "green",
                "group_by": "rule_id",
                "group_key": "31101",
                "current_rule_status": "pending",
            },
        )
        self.assertEqual(res_unflag.status_code, 200, res_unflag.text)
        self.assertEqual(res_unflag.json()["count"], 2)
        rows_after_unflag = self.db.connection.execute(
            "SELECT id, is_reviewed, flag_color FROM wazuh.alerts WHERE id IN (10, 11) ORDER BY id"
        ).fetchall()
        self.assertEqual([(r["id"], r["is_reviewed"], r["flag_color"]) for r in rows_after_unflag], [(10, 1, None), (11, 1, None)])

        # Re-flag and then group unreview + unflag together
        self.client.post(
            "/api/alerts/flag",
            params={"tenant": "Alpha"},
            json={"alert_ids": [10, 11], "flag_color": "green", "auto_review": True},
        )
        res_unrev = self.client.post(
            "/api/alerts/flag",
            params={"tenant": "Alpha"},
            json={
                "flag_color": None,
                "unreview": True,
                "current_flag_color": "green",
                "group_by": "rule_id",
                "group_key": "31101",
                "current_rule_status": "pending",
            },
        )
        self.assertEqual(res_unrev.status_code, 200, res_unrev.text)
        self.assertEqual(res_unrev.json()["count"], 2)
        self.assertFalse(res_unrev.json()["is_reviewed"])
        rows_after_unrev = self.db.connection.execute(
            "SELECT id, is_reviewed, status, flag_color FROM wazuh.alerts WHERE id IN (10, 11) ORDER BY id"
        ).fetchall()
        self.assertEqual(
            [(r["id"], r["is_reviewed"], r["status"], r["flag_color"]) for r in rows_after_unrev],
            [(10, 0, "unread", None), (11, 0, "unread", None)],
        )

        # Invalid combination: unreview=True while assigning a flag_color
        bad = self.client.post(
            "/api/alerts/flag",
            params={"tenant": "Alpha"},
            json={"alert_ids": [10], "flag_color": "green", "unreview": True},
        )
        self.assertEqual(bad.status_code, 400, bad.text)

    def test_flag_category_and_group_exports_match_scope(self):
        self._seed_rich_alerts()
        self.client.post(
            "/api/alerts/flag",
            json={"alert_ids": [10, 11, 13], "flag_color": "green", "auto_review": True},
        )
        self.client.post(
            "/api/alerts/flag",
            params={"tenant": "Alpha"},
            json={"alert_ids": [12], "flag_color": "red", "auto_review": True},
        )

        preview = self.client.get("/api/flags/export/preview", params={
            "tenant": "Alpha", "flag_color": "green", "group_by": "url_path",
            "group_key": "/lib/minigalnano/createthumb.php",
        })
        self.assertEqual(preview.status_code, 200, preview.text)
        body = preview.json()
        self.assertEqual(body["count"], 2)
        self.assertEqual(body["scope"]["group_key"], ["/lib/minigalnano/createthumb.php"])
        self.assertIn("Laporan Flag Hijau", body["meta"]["title"])
        self.assertIn("createthumb.php", body["html"])

        everything = self.client.get("/api/flags/export/preview", params={
            "tenant": "Alpha", "flag_color": "red", "rule_status": "all",
        })
        self.assertEqual(everything.status_code, 200, everything.text)
        self.assertEqual(everything.json()["count"], 1)

        csv_response = self.client.get("/api/flags/export/csv", params={
            "tenant": "Alpha", "flag_color": "green", "group_by": "url_path",
            "group_key": "/lib/minigalnano/createthumb.php",
        })
        self.assertEqual(csv_response.status_code, 200, csv_response.text)
        self.assertEqual(csv_response.headers.get("X-Arbiter-Count"), "2")
        import csv as csv_module
        import io
        rows = list(csv_module.DictReader(io.StringIO(csv_response.text)))
        self.assertEqual([row["alert_id"] for row in rows], ["syn-10", "syn-11"])
        self.assertEqual(rows[0]["method"], "GET")
        self.assertEqual(rows[0]["path_uri"], "/lib/minigalnano/createthumb.php")
        self.assertEqual(rows[0]["tenant_agent"], "Alpha (web-01)")

        for route in ("/api/flags/export/tsv", "/api/flags/export/report-html",
                      "/api/flags/export/docx", "/api/flags/export/xlsx", "/api/flags/export/markdown"):
            with self.subTest(route=route):
                response = self.client.get(route, params={
                    "tenant": "Alpha", "flag_color": "green", "group_by": "url_path",
                    "group_key": "/lib/minigalnano/createthumb.php",
                })
                self.assertEqual(response.status_code, 200, response.text[:100])
                self.assertEqual(response.headers.get("X-Arbiter-Count"), "2")

        empty = self.client.get("/api/flags/export/preview", params={
            "tenant": "Alpha", "flag_color": "green", "group_by": "url_path",
            "group_key": "/does-not-exist",
        })
        self.assertEqual(empty.status_code, 200, empty.text)
        self.assertEqual(empty.json()["count"], 0)

    def test_flag_export_rejects_unknown_grouping(self):
        response = self.client.get("/api/flags/export/preview", params={"group_by": "unknown"})
        self.assertEqual(response.status_code, 422, response.text)

    def test_review_and_flag_sql_never_binds_untyped_null_to_is_not_null(self):
        import re
        self._seed_rich_alerts()
        recorded_sql = []
        orig_execute = self.db.execute

        def spy_execute(sql, params=None):
            recorded_sql.append((sql, params))
            if re.search(r"%s\s+IS\s+(?:NOT\s+)?NULL|CASE\s+WHEN\s+NOT\s+%s", sql, re.I):
                raise AssertionError(f"Unsafe untyped NULL pattern in SQL: {sql}")
            return orig_execute(sql, params)

        with patch.object(self.db, "execute", side_effect=spy_execute):
            self.assertEqual(
                self.client.put("/api/alerts/10/review", params={"tenant": "Alpha"}, json={"is_reviewed": True}).status_code,
                200,
            )
            self.assertEqual(
                self.client.put("/api/alerts/10/review", params={"tenant": "Alpha"}, json={"is_reviewed": False}).status_code,
                200,
            )
            self.assertEqual(
                self.client.put("/api/alerts/10/review", params={"tenant": "Alpha"}, json={"is_reviewed": True, "flag_color": "red"}).status_code,
                200,
            )
            self.assertEqual(
                self.client.post("/api/alerts/batch-review", params={"tenant": "Alpha"}, json={"alert_ids": [10, 11], "is_reviewed": True}).status_code,
                200,
            )
            self.assertEqual(
                self.client.post("/api/alerts/batch-review", params={"tenant": "Alpha"}, json={"alert_ids": [10, 11], "is_reviewed": False}).status_code,
                200,
            )
            self.assertEqual(
                self.client.put("/api/alerts/10/flag", params={"tenant": "Alpha"}, json={"flag_color": "green", "auto_review": True}).status_code,
                200,
            )
            self.assertEqual(
                self.client.put("/api/alerts/10/flag", params={"tenant": "Alpha"}, json={"flag_color": None}).status_code,
                200,
            )
            self.assertEqual(
                self.client.post("/api/alerts/flag", params={"tenant": "Alpha"}, json={"alert_ids": [10], "flag_color": None, "unreview": True}).status_code,
                200,
            )

        for sql, params in recorded_sql:
            if not params:
                continue
            flat = []
            for p in params:
                if isinstance(p, (list, tuple)):
                    flat.extend(p)
                else:
                    flat.append(p)
            self.assertFalse(
                any(v is None for v in flat),
                f"Unexpected None parameter bound in SQL: {sql} -> {params!r}",
            )


if __name__ == "__main__":
    unittest.main()
