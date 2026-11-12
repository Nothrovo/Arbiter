"""Read-only IP Intel (Neuropetra) cache contract tests using synthetic psycopg mocks.

No real database, .env, or network access is used. Every query result is synthetic.
"""

from __future__ import annotations

import sys
import types
import unittest
from unittest.mock import patch

from app import intel


class _FakeResult:
    def __init__(self, value):
        self._value = value

    def fetchone(self):
        if isinstance(self._value, list):
            return self._value[0] if self._value else None
        return self._value


class _FakeConnection:
    def __init__(self, tables, row, error=None):
        self.tables = tables
        self.row = row
        self.error = error
        self.queries = []

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        return False

    def execute(self, sql, params=None):
        if self.error:
            raise self.error
        self.queries.append((sql, params))
        if "to_regclass" in sql:
            return _FakeResult(self.tables)
        return _FakeResult([self.row] if self.row is not None else [])


def _psycopg_modules(connection):
    class FakePsycopg(types.ModuleType):
        def connect(self, *_args, **_kwargs):
            return connection

    psycopg = FakePsycopg("psycopg")
    rows = types.ModuleType("psycopg.rows")
    rows.dict_row = object()
    return {"psycopg": psycopg, "psycopg.rows": rows}


TABLES_BOTH = {"reputation_table": "public.ip_intel_reputation", "cache_table": "public.ip_intel_cache"}
REPUTATION_ROW = {
    "ip": "8.8.8.8",
    "abuse_score": 87,
    "country_code": "ID",
    "isp": "Example ISP",
    "reputation_json": '{"domain":"example.test","usageType":"Data Center","totalReports":42}',
    "reputation_checked_at": "2026-11-10T00:00:00+00:00",
    "vt_malicious": 3,
}


class RemoteCacheLookupTests(unittest.TestCase):
    def test_unconfigured_remote_returns_actionable_error(self):
        with patch.object(intel, "_resolve_remote_db_url", return_value=""):
            result = intel.lookup_remote_ip_cache_detail("8.8.8.8")
        self.assertFalse(result["configured"])
        self.assertFalse(result["found"])
        self.assertIn("Database", result["error"])

    def test_reputation_table_preferred_and_score_is_returned(self):
        connection = _FakeConnection(TABLES_BOTH, REPUTATION_ROW)
        with patch.dict(sys.modules, _psycopg_modules(connection)):
            result = intel.lookup_remote_ip_cache_detail("8.8.8.8", remote_url="postgresql://redacted@127.0.0.1:5433/ip_intel")
        self.assertTrue(result["configured"])
        self.assertTrue(result["found"])
        self.assertEqual(result["source_table"], "ip_intel_reputation")
        record = result["record"]
        self.assertEqual(record["abuse_score"], 87)
        self.assertEqual(record["vt_malicious"], 3)
        self.assertEqual(record["isp"], "Example ISP")
        self.assertEqual(record["total_reports"], 42)
        self.assertEqual(record["reputation_source"], "neuropetra_cache")
        self.assertNotIn("redacted", str(result))

    def test_legacy_cache_only_schema_is_supported(self):
        connection = _FakeConnection(
            {"reputation_table": None, "cache_table": "public.ip_intel_cache"},
            {"ip": "8.8.8.8", "abuse_score": 5, "country_code": None, "isp": None,
             "reputation_json": None, "reputation_checked_at": None, "vt_malicious": 0},
        )
        with patch.dict(sys.modules, _psycopg_modules(connection)):
            result = intel.lookup_remote_ip_cache_detail("8.8.8.8", remote_url="postgresql://redacted@localhost/db")
        self.assertTrue(result["found"])
        self.assertEqual(result["source_table"], "ip_intel_cache")
        self.assertEqual(result["record"]["abuse_score"], 5)
        self.assertEqual(result["record"]["isp"], "Unknown ISP")
        self.assertEqual(result["record"]["total_reports"], 0)

    def test_row_without_score_reports_enrichment_needed(self):
        row = {**REPUTATION_ROW, "abuse_score": None}
        connection = _FakeConnection(TABLES_BOTH, row)
        with patch.dict(sys.modules, _psycopg_modules(connection)):
            result = intel.lookup_remote_ip_cache_detail("8.8.8.8", remote_url="postgresql://redacted@localhost/db")
        self.assertFalse(result["found"])
        self.assertIn("skor AbuseIPDB", result["error"])

    def test_missing_ip_is_distinct_from_connection_failure(self):
        connection = _FakeConnection(TABLES_BOTH, None)
        with patch.dict(sys.modules, _psycopg_modules(connection)):
            result = intel.lookup_remote_ip_cache_detail("8.8.8.8", remote_url="postgresql://redacted@localhost/db")
        self.assertFalse(result["found"])
        self.assertIn("belum ada di cache", result["error"])

    def test_missing_tables_are_reported(self):
        connection = _FakeConnection({"reputation_table": None, "cache_table": None}, None)
        with patch.dict(sys.modules, _psycopg_modules(connection)):
            result = intel.lookup_remote_ip_cache_detail("8.8.8.8", remote_url="postgresql://redacted@localhost/db")
        self.assertFalse(result["found"])
        self.assertIn("tidak ditemukan", result["error"])

    def test_auth_failure_is_safe_and_leaks_no_dsn(self):
        connection = _FakeConnection({}, None, error=RuntimeError(
            "password authentication failed for user 'secretrole' at 10.0.0.5"
        ))
        with patch.dict(sys.modules, _psycopg_modules(connection)):
            result = intel.lookup_remote_ip_cache_detail("8.8.8.8", remote_url="postgresql://secretrole:secret@10.0.0.5/db")
        self.assertFalse(result["found"])
        self.assertIn("Autentikasi", result["error"])
        self.assertNotIn("secretrole", result["error"])
        self.assertNotIn("secret@", result["error"])

    def test_connection_refused_is_safe(self):
        connection = _FakeConnection({}, None, error=RuntimeError("connection refused"))
        with patch.dict(sys.modules, _psycopg_modules(connection)):
            result = intel.lookup_remote_ip_cache_detail("8.8.8.8", remote_url="postgresql://redacted@localhost/db")
        self.assertIn("tidak dapat dihubungi", result["error"])


class _FakeCursor:
    def __init__(self):
        self.executed = []

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        return False

    def execute(self, sql, params=None):
        self.executed.append((sql, params))


class _SyncConnection:
    def __init__(self):
        self.cur = _FakeCursor()

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        return False

    def cursor(self):
        return self.cur

    def commit(self):
        pass


class RemoteSyncTests(unittest.TestCase):
    def test_remote_cache_records_are_not_written_back(self):
        connection = _SyncConnection()

        class FakePsycopg(types.ModuleType):
            def connect(self, *_args, **_kwargs):
                return connection

        with patch.dict(sys.modules, {"psycopg": FakePsycopg("psycopg")}), \
                patch.object(intel, "_resolve_remote_db_url", return_value="postgresql://redacted@localhost/db"):
            intel.sync_remote_cache([
                {"ip": "9.9.9.9", "status": "enriched", "abuse_score": 70, "cache_source": "ip_intel_reputation"},
                {"ip": "9.9.9.10", "status": "enriched", "abuse_score": 10},
            ])
        self.assertEqual(len(connection.cur.executed), 1)
        self.assertIn("9.9.9.10", connection.cur.executed[0][1])


class EnrichFallbackTests(unittest.TestCase):
    def test_without_api_key_returns_remote_cache_score(self):
        cached = {
            "configured": True,
            "found": True,
            "source_table": "ip_intel_reputation",
            "record": {"ip": "8.8.8.8", "status": "enriched", "abuse_score": 87, "cache_source": "ip_intel_reputation"},
            "error": None,
        }
        with patch.object(intel, "lookup_remote_ip_cache_detail", return_value=cached), \
                patch.object(intel, "ABUSEIPDB_API_KEY", ""):
            result = intel.enrich_ip("8.8.8.8", api_key="")
        self.assertEqual(result["status"], "enriched")
        self.assertEqual(result["abuse_score"], 87)
        self.assertEqual(result["cache_source"], "ip_intel_reputation")

    def test_without_api_key_and_missing_cache_reports_error(self):
        missing = {
            "configured": True, "found": False, "record": None, "source_table": None,
            "error": "IP 8.8.8.8 belum ada di cache IP Intel (Neuropetra).",
        }
        with patch.object(intel, "lookup_remote_ip_cache_detail", return_value=missing), \
                patch.object(intel, "ABUSEIPDB_API_KEY", ""):
            result = intel.enrich_ip("8.8.8.8", api_key="")
        self.assertEqual(result["status"], "error")
        self.assertIsNone(result["abuse_score"])
        self.assertIn("belum ada di cache", result["error"])

    def test_live_failure_falls_back_to_cache_and_keeps_real_score(self):
        cached = {
            "configured": True, "found": True, "source_table": "ip_intel_cache",
            "record": {"ip": "8.8.8.8", "status": "enriched", "abuse_score": 21, "cache_source": "ip_intel_cache"},
            "error": None,
        }
        with patch.object(intel, "lookup_remote_ip_cache_detail", return_value=cached), \
                patch.object(intel, "query_abuseipdb", side_effect=RuntimeError("quota exceeded")):
            result = intel.enrich_ip("8.8.8.8", api_key="synthetic-key")
        self.assertEqual(result["status"], "enriched")
        self.assertEqual(result["abuse_score"], 21)


if __name__ == "__main__":
    unittest.main()
