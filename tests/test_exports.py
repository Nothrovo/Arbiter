import unittest
from app.exports import (
    generate_tsv_table,
    generate_markdown_report,
    generate_gdocs_html_report,
    generate_docx_landscape_report,
    generate_xlsx_workbook,
)


class ExportTests(unittest.TestCase):
    def setUp(self):
        self.sample_alerts = [
            {
                "id": "1",
                "alert_id": "wazuh-101",
                "timestamp": "2026-10-21T10:00:00Z",
                "tenant": "TenantA",
                "agent_name": "web-srv",
                "agent_ip": "10.0.0.1",
                "rule_id": "31103",
                "rule_level": 10,
                "description": "SQL Injection attempt",
                "source_ip": "195.201.245.94",
                "abuse_score": 100,
                "vt_malicious": 8,
                "country_code": "DE",
                "hit_count": 5,
                "is_reviewed": True,
                "full_log": 'GET /index.php?id=1 UNION SELECT 1,2',
            }
        ]
        self.meta = {
            "title": "Incident Case: SQLi Attack",
            "category": "Web Attack",
            "severity": "High",
            "status": "Contained",
            "analysis": "Automated scan attempted SQL union query.",
            "conclusion": "True Positive blocked by perimeter.",
            "recommendation": "Block source IP permanently.",
        }

    def test_generate_tsv_table(self):
        tsv = generate_tsv_table(self.sample_alerts)
        self.assertIn("SQL Injection attempt", tsv)
        self.assertIn("195.201.245.94", tsv)
        self.assertIn("Reviewed", tsv)
        self.assertIn("Analisis", tsv)
        self.assertIn("GET /index.php?id=1 UNION SELECT 1,2", tsv)
        self.assertTrue(tsv.startswith("No\tHit Count"))

    def test_generate_markdown_report(self):
        md = generate_markdown_report(self.sample_alerts, self.meta)
        self.assertIn("# Incident Case: SQLi Attack", md)
        self.assertIn("SQL Injection attempt", md)
        self.assertIn("Total Kemunculan (Hits):** 5", md)
        self.assertIn("True Positive blocked by perimeter.", md)

    def test_generate_gdocs_html_report(self):
        html = generate_gdocs_html_report(self.sample_alerts, self.meta)
        self.assertIn("Incident Case: SQLi Attack", html)
        self.assertIn("badge-high", html)
        self.assertIn("195.201.245.94", html)
        self.assertIn("5x", html)
        self.assertIn("Tabel Kronologi Investigasi", html)
        self.assertIn('border="1"', html)
        self.assertIn('border: 1px solid #cbd5e0', html)
        self.assertIn('Full Log:</strong> GET /index.php?id=1 UNION SELECT 1,2', html)
        self.assertIn("Analisis", html)
        self.assertNotIn("CVE / MITRE", html)

    def test_generate_docx_landscape_report(self):
        buf = generate_docx_landscape_report(self.sample_alerts, self.meta)
        content = buf.getvalue()
        self.assertGreater(len(content), 1000)
        self.assertTrue(content.startswith(b"PK"))  # Valid docx zip magic

    def test_generate_xlsx_workbook(self):
        buf = generate_xlsx_workbook(self.sample_alerts)
        content = buf.getvalue()
        self.assertGreater(len(content), 1000)
        self.assertTrue(content.startswith(b"PK"))  # Valid xlsx zip magic


if __name__ == "__main__":
    unittest.main()
