import json
import unittest
from fastapi.testclient import TestClient

from app.database import get_db
from app.main import app


class ApiIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        with get_db() as conn:
            conn.execute("DELETE FROM wazuh.alerts WHERE alert_id LIKE 'test-%' OR alert_id LIKE 'pasted-%';")
            conn.execute("DELETE FROM wazuh.analysis_groups WHERE title LIKE '%Test Case%';")

    def test_health_check(self):
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["app"], "Arbiter")

    def test_import_text_and_safeguard_duplicate_wazuh_id(self):
        alert_item = {
            "id": "test-wazuh-safeguard-001",
            "timestamp": "2026-10-21T14:30:00Z",
            "agent": {"name": "target-host", "labels": {"tenant": "TenantFinance"}},
            "rule": {"id": "5710", "level": 10, "description": "SSH auth failure"},
            "full_log": "Oct 21 14:30:00 target-host sshd[501]: Failed password for root from 1.2.3.4",
            "data": {"srcip": "1.2.3.4"}
        }

        # First ingest -> inserted
        res1 = self.client.post("/api/import-text", json={"content": json.dumps([alert_item])})
        self.assertEqual(res1.status_code, 200)
        d1 = res1.json()
        self.assertEqual(d1["inserted"], 1)

        # Second ingest with same wazuh ID -> safeguard ignores duplicate!
        res2 = self.client.post("/api/import-text", json={"content": json.dumps([alert_item])})
        self.assertEqual(res2.status_code, 200)
        d2 = res2.json()
        self.assertEqual(d2["inserted"], 0)
        self.assertEqual(d2["deduplicated"], 0)

    def test_alert_review_flag_and_batch_review(self):
        alert_item = {
            "id": "test-wazuh-review-001",
            "timestamp": "2026-10-21T15:00:00Z",
            "agent": {"name": "target-host", "labels": {"tenant": "TenantFinance"}},
            "rule": {"id": "5710", "level": 10, "description": "SSH auth failure"},
            "full_log": "Oct 21 15:00:00 target-host sshd[601]: Failed password for root from 1.2.3.4",
            "data": {"srcip": "1.2.3.4"}
        }
        self.client.post("/api/import-text", json={"content": json.dumps([alert_item])})

        # Query the alert
        res = self.client.get("/api/alerts?q=test-wazuh-review-001")
        self.assertEqual(res.status_code, 200)
        items = res.json()["items"]
        self.assertGreaterEqual(len(items), 1)
        alert_id = items[0]["id"]
        self.assertFalse(items[0]["is_reviewed"])

        # Mark as reviewed
        rev_res = self.client.put(f"/api/alerts/{alert_id}/review", json={"is_reviewed": True, "reviewer_notes": "Reviewed OK"})
        self.assertEqual(rev_res.status_code, 200)
        self.assertTrue(rev_res.json()["is_reviewed"])

        # Batch review toggle
        batch_res = self.client.post("/api/alerts/batch-review", json={"alert_ids": [alert_id], "is_reviewed": False})
        self.assertEqual(batch_res.status_code, 200)
        self.assertEqual(batch_res.json()["count"], 1)

    def test_create_group_and_all_export_formats(self):
        # Create group
        grp_payload = {
            "title": "Test Case: Brute Force Investigation",
            "category": "Brute Force",
            "severity": "High",
            "analysis": "Chronological audit revealed dictionary attack.",
            "conclusion": "True Positive.",
            "recommendation": "Block source IP.",
        }
        res_g = self.client.post("/api/groups", json=grp_payload)
        self.assertEqual(res_g.status_code, 200)
        group_id = res_g.json()["id"]

        # 1. GDocs HTML
        gdocs = self.client.get(f"/api/export/report-html?group_id={group_id}")
        self.assertEqual(gdocs.status_code, 200)
        self.assertIn("Test Case: Brute Force Investigation", gdocs.text)

        # 2. DOCX
        docx_res = self.client.get(f"/api/export/docx?group_id={group_id}")
        self.assertEqual(docx_res.status_code, 200)
        self.assertTrue(docx_res.content.startswith(b"PK"))

        # 3. XLSX
        xlsx_res = self.client.get(f"/api/export/xlsx?group_id={group_id}")
        self.assertEqual(xlsx_res.status_code, 200)
        self.assertTrue(xlsx_res.content.startswith(b"PK"))

        # 4. TSV
        tsv_res = self.client.get(f"/api/export/tsv?group_id={group_id}")
        self.assertEqual(tsv_res.status_code, 200)
        self.assertTrue(tsv_res.text.startswith("No\tHit Count"))

        # 5. Markdown
        md_res = self.client.get(f"/api/export/markdown?group_id={group_id}")
        self.assertEqual(md_res.status_code, 200)
        self.assertIn("# Test Case: Brute Force Investigation", md_res.text)

    def test_sanitize_logs_endpoint(self):
        payload = {"text": "Unauthorized login from 10.10.10.5 password=TopSecretPass123"}
        res = self.client.post("/api/sanitize-logs", json=payload)
        self.assertEqual(res.status_code, 200)
        clean = res.json()["sanitized"]
        self.assertNotIn("10.10.10.5", clean)
        self.assertNotIn("TopSecretPass123", clean)
        self.assertIn("<INTERNAL_IP>", clean)
        self.assertIn("<REDACTED_SECRET>", clean)


if __name__ == "__main__":
    unittest.main()
