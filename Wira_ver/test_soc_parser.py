"""Unit test parser/grouper SOC Log Reader (tanpa Flask/DB)."""
import unittest

import soc_parser as SP


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


class ParseTests(unittest.TestCase):
    def test_access_log(self):
        p = SP.parse_log_line(ACCESS)
        self.assertEqual(p["log_type"], "http")
        self.assertEqual(p["srcip"], "123.253.78.154")
        self.assertEqual(p["method"], "GET")
        self.assertEqual(p["path"], "/index.php")
        self.assertEqual(p["query"], "id=1+UNION+SELECT+user(),database()")
        self.assertEqual(p["status"], "403")
        self.assertEqual(p["bytes"], "153")
        self.assertEqual(p["ua"], "curl/8.18.0")
        self.assertTrue(p["timestamp_iso"].startswith("2026-10-20T07:34:08"))

    def test_apparmor_syslog_tidak_jadi_path_21(self):
        p = SP.parse_log_line(APPARMOR_A, "2026-10-21T05:10:20Z")
        self.assertEqual(p["log_type"], "syslog")
        self.assertEqual(p["path"], "kernel: AppArmor DENIED")
        self.assertNotEqual(p["path"], "21")
        self.assertEqual(p["method"], "")
        self.assertEqual(p["status"], "")
        self.assertIn("operation=ptrace", p["details"])
        self.assertEqual(p["timestamp_display"], "Oct 21 12:10:20")
        self.assertTrue(p["timestamp_iso"].startswith("2026-10-21T12:10:20"))

    def test_sshd_extract_ip(self):
        p = SP.parse_log_line(SSHD, "2026-04-24T00:00:00Z")
        self.assertEqual(p["log_type"], "syslog")
        self.assertEqual(p["srcip"], "68.183.216.91")
        self.assertIn("sshd", p["path"])
        self.assertEqual(p["method"], "")

    def test_generic_tidak_mengarang_get_200(self):
        p = SP.parse_log_line("Oct 21 12:10:20 host myapp: something happened")
        self.assertEqual(p["log_type"], "syslog")
        self.assertEqual(p["method"], "")
        self.assertEqual(p["status"], "")
        self.assertEqual(p["path"], "myapp")

    def test_json_full_log(self):
        p = SP.parse_log_line(
            '{"timestamp":"2026-10-21T12:10:20Z","srcip":"1.2.3.4",'
            '"url":"/x?a=1","method":"GET","status":403}'
        )
        self.assertEqual(p["log_type"], "http")
        self.assertEqual(p["srcip"], "1.2.3.4")
        self.assertEqual(p["path"], "/x")
        self.assertEqual(p["query"], "a=1")
        self.assertEqual(p["status"], "403")


class GroupTests(unittest.TestCase):
    def test_normalisasi_apparmor_abaikan_waktu_audit_pid(self):
        self.assertEqual(
            SP.normalize_log_for_signature(APPARMOR_A),
            SP.normalize_log_for_signature(APPARMOR_B),
        )

    def test_operasi_berbeda_tidak_digabung(self):
        other = APPARMOR_A.replace('operation="ptrace"', 'operation="open"')
        self.assertNotEqual(
            SP.normalize_log_for_signature(APPARMOR_A),
            SP.normalize_log_for_signature(other),
        )

    def test_dua_alert_sama_digabung_dan_ada_rentang(self):
        a = SP.normalize_single_wazuh_alert({
            "_id": "wazuh-1", "timestamp": "2026-10-21T05:10:20Z",
            "full_log": APPARMOR_A, "rule": {"id": "52002"}, "agent": {"name": "h"},
        })
        b = SP.normalize_single_wazuh_alert({
            "_id": "wazuh-2", "timestamp": "2026-10-21T06:00:20Z",
            "full_log": APPARMOR_B, "rule": {"id": "52002"}, "agent": {"name": "h"},
        })
        self.assertEqual(a["_id"], b["_id"])
        grouped = SP.group_alerts([b, a])
        self.assertEqual(len(grouped), 1)
        self.assertEqual(grouped[0]["hit_count"], 2)
        self.assertLess(grouped[0]["first_seen"], grouped[0]["last_seen"])

    def test_wazuh_ids_dari_semua_baris_digabung(self):
        base = {
            "timestamp": "2026-10-21T05:10:20Z", "full_log": APPARMOR_A,
            "rule": {"id": "52002"}, "agent": {"name": "h"},
        }
        a = dict(base, _id="sig_x", wazuh_ids=["w1"], wazuh_id="w1")
        b = dict(base, _id="sig_x", wazuh_ids=["w2"], wazuh_id="w2")
        grouped = SP.group_alerts([a, b])
        self.assertEqual(grouped[0]["wazuh_ids"], ["w1", "w2"])

    def test_akses_log_sama_digabung_yang_query_beda_tidak(self):
        a = SP.normalize_single_wazuh_alert({
            "_id": "1", "timestamp": "2026-10-20T00:34:08Z",
            "full_log": ACCESS, "rule": {"id": "31103"}, "agent": {"name": "web"},
        })
        b = SP.normalize_single_wazuh_alert({
            "_id": "2", "timestamp": "2026-10-20T01:34:08Z",
            "full_log": ACCESS.replace("07:34:08", "08:34:08"),
            "rule": {"id": "31103"}, "agent": {"name": "web"},
        })
        c = SP.normalize_single_wazuh_alert({
            "_id": "3", "timestamp": "2026-10-20T02:34:08Z",
            "full_log": ACCESS.replace("id=1+UNION", "id=2+UNION"),
            "rule": {"id": "31103"}, "agent": {"name": "web"},
        })
        self.assertEqual(a["_id"], b["_id"])
        self.assertNotEqual(a["_id"], c["_id"])
        grouped = SP.group_alerts([a, b, c])
        self.assertEqual(len(grouped), 2)

    def test_group_row_ids_untuk_baris_legacy(self):
        base = {
            "timestamp": "2026-10-21T05:10:20Z", "full_log": APPARMOR_A,
            "rule": {"id": "52002"}, "agent": {"name": "h"},
        }
        a = SP.enrich_alert(dict(base, _id="legacy-1"))
        b = SP.enrich_alert(dict(base, _id="legacy-2"))
        grouped = SP.group_alerts([a, b])
        self.assertEqual(len(grouped), 1)
        self.assertEqual(grouped[0]["_group_rows"], 2)
        self.assertEqual(sorted(grouped[0]["_group_row_ids"]), ["legacy-1", "legacy-2"])

    def test_format_rentang_jam_sama(self):
        alert = {
            "first_seen": "2026-10-21T05:10:20+00:00",
            "last_seen": "2026-10-21T06:00:20+00:00",
        }
        self.assertEqual(SP.format_time_range(alert), "12.10.20 s/d 13.00.20")

    def test_parse_alert_fields_tidak_default_200(self):
        alert = SP.enrich_alert({
            "_id": "x", "full_log": APPARMOR_A, "data": {},
            "rule": {"id": "52002", "description": "Apparmor DENIED"},
        })
        fields = SP.parse_alert_fields(alert)
        self.assertEqual(fields["status"], "-")
        self.assertEqual(fields["method"], "-")
        self.assertIn("AppArmor DENIED", fields["path"])

    def test_status_data_id_tidak_dipakai_untuk_non_http(self):
        alert = SP.enrich_alert({
            "_id": "x", "full_log": APPARMOR_A, "data": {"id": "1400"},
            "rule": {"id": "52002", "description": "Apparmor DENIED"},
        })
        self.assertEqual(SP.parse_alert_fields(alert)["status"], "-")

    def test_wazuh_id_asli_tetap_disimpan(self):
        alert = SP.normalize_single_wazuh_alert({
            "_id": "wz-original-1", "timestamp": "2026-10-21T05:10:20Z",
            "full_log": APPARMOR_A, "rule": {"id": "52002"}, "agent": {"name": "h"},
        })
        self.assertTrue(alert["_id"].startswith("sig_"))
        self.assertEqual(alert["wazuh_id"], "wz-original-1")


if __name__ == "__main__":
    unittest.main()
