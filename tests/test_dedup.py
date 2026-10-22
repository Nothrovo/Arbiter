import unittest
from app.core import normalize_alert
from app.parser import normalize_log_for_signature, build_log_signature


class DedupSafeguardTests(unittest.TestCase):
    def test_same_log_different_timestamps_produce_identical_signature(self):
        log_1 = '192.168.1.1 - - [20/Oct/2026:07:34:08 +0700] "GET /test.php HTTP/1.1" 200 123 "-" "curl"'
        log_2 = '192.168.1.1 - - [20/Oct/2026:08:45:12 +0700] "GET /test.php HTTP/1.1" 200 123 "-" "curl"'

        sig_1 = build_log_signature({"full_log": log_1, "rule": {"id": "100"}})
        sig_2 = build_log_signature({"full_log": log_2, "rule": {"id": "100"}})
        self.assertEqual(sig_1, sig_2)
        self.assertTrue(len(sig_1) == 24)

    def test_normalize_alert_safeguards_default_review_flag(self):
        alert = normalize_alert({
            "id": "wazuh-101",
            "timestamp": "2026-10-21T01:02:03Z",
            "agent": {"name": "app-server", "labels": {"tenant": "TenantX"}},
            "rule": {"id": "5710", "level": 10, "description": "SSH failed"},
            "full_log": "Oct 21 01:02:03 app-server sshd[123]: Failed password for root from 1.2.3.4"
        })
        self.assertEqual(alert["wazuh_id"], "wazuh-101")
        self.assertEqual(alert["tenant"], "TenantX")
        self.assertFalse(alert["is_reviewed"])
        self.assertEqual(alert["hit_count"], 1)
        self.assertTrue(alert["log_signature"])

    def test_different_query_payload_produces_different_signature(self):
        log_a = '10.0.0.1 - - [20/Oct/2026:07:00:00 +0700] "GET /login?user=admin HTTP/1.1" 200 50'
        log_b = '10.0.0.1 - - [20/Oct/2026:07:00:00 +0700] "GET /login?user=hacker HTTP/1.1" 200 50'

        sig_a = build_log_signature({"full_log": log_a, "rule": {"id": "1"}})
        sig_b = build_log_signature({"full_log": log_b, "rule": {"id": "1"}})
        self.assertNotEqual(sig_a, sig_b)


if __name__ == "__main__":
    unittest.main()
