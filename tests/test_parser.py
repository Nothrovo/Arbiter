import unittest
from app.parser import (
    parse_log_line,
    normalize_log_for_signature,
    build_log_signature,
    parse_export,
    extract_alerts,
)

ACCESS = (
    '123.253.78.154 - - [20/Oct/2026:07:34:08 +0700] '
    '"GET /index.php?id=1+UNION+SELECT+user(),database() HTTP/2.0" '
    '403 153 "-" "curl/8.18.0"'
)

APPARMOR_A = (
    'Oct 21 12:10:20 host kernel: [2955743.701286] audit: type=1400 '
    'audit(1609878390.062:96652): apparmor="DENIED" operation="ptrace" '
    'profile="docker-default" pid=26439 comm="telegraf" requested_mask="trace" '
    'denied_mask="trace" peer="unconfined"'
)

APPARMOR_B = (
    'Oct 21 13:00:20 host kernel: [2955799.881286] audit: type=1400 '
    'audit(1609879999.062:96653): apparmor="DENIED" operation="ptrace" '
    'profile="docker-default" pid=26440 comm="telegraf" requested_mask="trace" '
    'denied_mask="trace" peer="unconfined"'
)

SSHD = (
    'Apr 24 17:24:55 ip-10-0-1-52 sshd[32179]: Did not receive '
    'identification string from 68.183.216.91 port 53820'
)


class ParserUnitTests(unittest.TestCase):
    def test_access_log_parser(self):
        p = parse_log_line(ACCESS)
        self.assertEqual(p["log_type"], "http")
        self.assertEqual(p["srcip"], "123.253.78.154")
        self.assertEqual(p["method"], "GET")
        self.assertEqual(p["path"], "/index.php")
        self.assertEqual(p["query"], "id=1+UNION+SELECT+user(),database()")
        self.assertEqual(p["status"], "403")
        self.assertEqual(p["ua"], "curl/8.18.0")
        self.assertTrue(p["timestamp_iso"].startswith("2026-10-20T07:34:08"))

    def test_apparmor_syslog_without_bogus_path(self):
        p = parse_log_line(APPARMOR_A, "2026-10-21T05:10:20Z")
        self.assertEqual(p["log_type"], "syslog")
        self.assertEqual(p["path"], "kernel: AppArmor DENIED")
        self.assertNotEqual(p["path"], "21")
        self.assertEqual(p["method"], "")
        self.assertEqual(p["status"], "")
        self.assertIn("operation=ptrace", p["details"])

    def test_sshd_ip_extraction(self):
        p = parse_log_line(SSHD, "2026-04-24T00:00:00Z")
        self.assertEqual(p["log_type"], "syslog")
        self.assertEqual(p["srcip"], "68.183.216.91")
        self.assertIn("sshd", p["path"])

    def test_signature_normalization(self):
        sig_a = normalize_log_for_signature(APPARMOR_A)
        sig_b = normalize_log_for_signature(APPARMOR_B)
        self.assertEqual(sig_a, sig_b)

    def test_export_parser_with_control_chars(self):
        content = '{"hits":{"hits":[{"_source":{"id":"a","full_log":"bad\x01text\nmore"}}]}}'
        alerts, warnings = parse_export(content)
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0]["full_log"], "bad\x01text\nmore")


if __name__ == "__main__":
    unittest.main()
