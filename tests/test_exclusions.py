"""Custom exclusion rules: synthetic in-memory storage only, never a live database."""
from __future__ import annotations

import unittest
from typing import Any

from tests import test_ui_api as ui_api


class ExclusionAPITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ui_api.UIAPIContractTests.setUpClass.__func__(cls)

    def setUp(self):
        ui_api.UIAPIContractTests.setUp(self)  # type: ignore[arg-type]
        self.db.add_alert(20, "Alpha", data='{"url":"/service/mbkm/logbook/total-verif"}',
                          parsed_details='{"status":"401","log_type":"http"}')
        self.db.add_alert(21, "Alpha", data='{"url":"/service/mbkm/logbook/other"}',
                          parsed_details='{"status":"401","log_type":"http"}')
        self.db.add_alert(22, "Alpha", data='{"url":"/service/krs/list"}',
                          parsed_details='{"status":"200","log_type":"http"}')

    tearDown = ui_api.UIAPIContractTests.tearDown
    db: Any
    client: Any
    api: Any

    def add_rule(self, **overrides):
        payload = {"field": "url", "match": "glob", "pattern": "*/service/mbkm/logbook*"}
        payload.update(overrides)
        return self.client.post("/api/settings/exclusions", json=payload)

    def alpha_ids(self):
        response = self.client.get("/api/alerts", params={"tenant": "Alpha", "limit": 500})
        self.assertEqual(response.status_code, 200, response.text)
        return {item["id"] for item in response.json()["items"]}

    def test_defaults_expose_an_empty_enabled_exclusion_document(self):
        settings = self.client.get("/api/settings").json()["settings"]
        self.assertEqual(settings["exclusions"], {"enabled": True, "rules": []})

    def test_glob_rule_hides_matching_alerts_from_triage_stats_and_summary(self):
        added = self.add_rule()
        self.assertEqual(added.status_code, 200, added.text)
        self.assertTrue(added.json()["added"])
        self.assertTrue(added.json()["rule"]["id"])

        self.assertEqual(self.alpha_ids(), {1, 3, 22})

        stats = self.client.get("/api/stats", params={"tenant": "Alpha"})
        self.assertEqual(stats.status_code, 200, stats.text)
        self.assertEqual(stats.json()["total"], 3)

        summary = self.client.get("/api/triage/summary", params={"tenant": "Alpha"})
        self.assertEqual(summary.status_code, 200, summary.text)
        self.assertEqual(summary.json()["alerts"], 3)

        removed = self.client.delete(f"/api/settings/exclusions/{added.json()['rule']['id']}")
        self.assertEqual(removed.status_code, 200, removed.text)
        self.assertEqual(self.alpha_ids(), {1, 3, 20, 21, 22})

    def test_duplicate_rules_are_not_added_twice(self):
        first = self.add_rule()
        second = self.add_rule()
        self.assertEqual(second.status_code, 200, second.text)
        self.assertFalse(second.json()["added"])
        self.assertEqual(len(second.json()["settings"]["exclusions"]["rules"]), 1)
        self.assertEqual(first.json()["rule"]["id"], second.json()["rule"]["id"])

    def test_disabled_rule_or_document_does_not_filter(self):
        added = self.add_rule()
        rule_id = added.json()["rule"]["id"]
        disabled = self.client.put(f"/api/settings/exclusions/{rule_id}", json={"enabled": False})
        self.assertEqual(disabled.status_code, 200, disabled.text)
        self.assertEqual(self.alpha_ids(), {1, 3, 20, 21, 22})

        self.client.put(f"/api/settings/exclusions/{rule_id}", json={"enabled": True})
        self.assertEqual(self.alpha_ids(), {1, 3, 22})

        global_off = self.client.put("/api/settings", json={"exclusions": {"enabled": False}})
        self.assertEqual(global_off.status_code, 200, global_off.text)
        self.assertEqual(self.alpha_ids(), {1, 3, 20, 21, 22})

    def test_exact_match_and_field_validation(self):
        exact = self.add_rule(match="exact", pattern="/service/mbkm/logbook/total-verif")
        self.assertEqual(exact.status_code, 200, exact.text)
        self.assertEqual(self.alpha_ids(), {1, 3, 21, 22})

        for payload in (
            {"field": "unknown", "match": "glob", "pattern": "x"},
            {"field": "url", "match": "fuzzy", "pattern": "x"},
            {"field": "url", "match": "glob", "pattern": "  "},
            {"field": "url", "match": "regex", "pattern": "("},
        ):
            with self.subTest(payload=payload):
                response = self.client.post("/api/settings/exclusions", json=payload)
                self.assertEqual(response.status_code, 400, response.text)

    def test_wazuh_query_import_maps_url_and_syscheck_paths(self):
        query = (
            "not (data.url: (*/mhs/* or */repository/* or */mod/quiz*) "
            "or syscheck.path: */var/www/vendor/mpdf/mpdf/*)"
        )
        imported = self.client.post("/api/settings/exclusions/import", json={"query": query})
        self.assertEqual(imported.status_code, 200, imported.text)
        body = imported.json()
        self.assertEqual(body["added_count"], 4)
        fields = {(rule["field"], rule["pattern"]) for rule in body["settings"]["exclusions"]["rules"]}
        self.assertIn(("url", "*/mhs/*"), fields)
        self.assertIn(("syscheck_path", "*/var/www/vendor/mpdf/mpdf/*"), fields)

        self.db.add_alert(23, "Alpha", data='{"url":"/safe/path"}',
                          raw='{"syscheck":{"path":"/var/www/vendor/mpdf/mpdf/file.php"},"full_log":""}')
        self.db.add_alert(24, "Alpha", data='{"url":"/service/mhs/dashboard"}')
        self.assertNotIn(23, self.alpha_ids())
        self.assertNotIn(24, self.alpha_ids())

    def test_explicit_export_keeps_excluded_evidence(self):
        self.add_rule()
        exported = self.client.get("/api/export.csv", params={"tenant": "Alpha", "alert_ids": "20"})
        self.assertEqual(exported.status_code, 200, exported.text)
        self.assertIn("synthetic-20", exported.text)

    def test_patterns_are_bound_and_never_execute_sql(self):
        malicious = self.add_rule(pattern="'; DROP TABLE wazuh.alerts; --")
        self.assertEqual(malicious.status_code, 200, malicious.text)
        self.assertEqual(self.alpha_ids(), {1, 3, 20, 21, 22})
        count = self.db.connection.execute("SELECT count(*) AS n FROM wazuh.alerts").fetchone()["n"]
        self.assertEqual(count, 6)


if __name__ == "__main__":
    unittest.main()
