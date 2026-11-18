"""Background Wazuh pull jobs, exercised with synthetic stubs only.

No PostgreSQL, .env or network access: app.database is replaced by a stub while
app.pull_jobs is imported, then every outbound function is patched per test.
"""
from __future__ import annotations

import importlib
import json
import sys
import time
import types
import unittest
from contextlib import contextmanager
from unittest.mock import patch

MAX_WAIT_SECONDS = 5.0


def load_pull_jobs():
    config = types.ModuleType("app.config")
    config.__dict__.update(HOST="127.0.0.1", PORT=0)
    database = types.ModuleType("app.database")

    def forbidden(*args, **kwargs):
        raise AssertionError("Real database access is forbidden in pull job tests")

    database.__dict__.update(
        get_db=forbidden,
        init_database=forbidden,
        ingest_alert_with_dedup=forbidden,
        ingest_alerts_batch=forbidden,
    )
    with patch.dict(sys.modules, {"app.config": config, "app.database": database}):
        sys.modules.pop("app.pull_jobs", None)
        module = importlib.import_module("app.pull_jobs")
    return module


class FakeTransaction:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class FakeConnection:
    def transaction(self):
        return FakeTransaction()


@contextmanager
def fake_get_db():
    yield FakeConnection()


def base_config(**overrides):
    config = {
        "indexer_url": "https://wazuh.synthetic:9200",
        "username": "analyst",
        "password": "SyntheticPass123",
        "index_pattern": "wazuh-alerts-*",
        "verify_tls": True,
        "time_from": "2026-01-01T00:00:00+00:00",
        "time_to": "2026-01-03T00:00:00+00:00",
        "min_rule_level": 7,
        "max_rule_level": None,
        "max_docs": 100,
        "page_size": 50,
        "chunk_days": 1,
    }
    config.update(overrides)
    return config


def wait_for(pull_jobs, job_id):
    deadline = time.monotonic() + MAX_WAIT_SECONDS
    job = pull_jobs.get_job(job_id)
    while time.monotonic() < deadline:
        job = pull_jobs.get_job(job_id)
        if job and job.get("status") in ("done", "error", "cancelled"):
            return job
        time.sleep(0.01)
    raise AssertionError(f"job did not finish in time: {job}")


class PullJobTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pull = load_pull_jobs()

    def setUp(self):
        self.pull._JOBS.clear()

    def test_validation_rejects_unsafe_limits(self):
        with self.assertRaises(ValueError):
            self.pull.start_pull_job(base_config(max_docs=0))
        with self.assertRaises(ValueError):
            self.pull.start_pull_job(base_config(page_size=5))
        with self.assertRaises(ValueError):
            self.pull.start_pull_job(base_config(chunk_days=99))
        with self.assertRaises(ValueError):
            self.pull.start_pull_job(base_config(
                time_from="2026-01-03T00:00:00+00:00",
                time_to="2026-01-01T00:00:00+00:00",
            ))

    def test_queued_job_redacts_credentials_and_supports_cancel(self):
        class NotStartedThread:
            def __init__(self, *args, **kwargs):
                pass

            def start(self):
                pass

        with patch.object(self.pull.threading, "Thread", NotStartedThread):
            job_id = self.pull.start_pull_job(base_config())

        snapshot = self.pull.get_job(job_id)
        self.assertIsNotNone(snapshot)
        self.assertEqual(snapshot["status"], "queued")
        self.assertEqual(snapshot["windows_total"], 2)
        serialized = json.dumps(snapshot)
        self.assertNotIn("SyntheticPass123", serialized)
        self.assertNotIn("password", serialized)
        self.assertNotIn("_config", serialized)

        cancelled = self.pull.cancel_job(job_id)
        self.assertTrue(cancelled["cancel_requested"])
        self.assertIsNone(self.pull.get_job("does-not-exist"))

        listed = self.pull.list_jobs(5)
        self.assertEqual([item["id"] for item in listed], [job_id])
        self.assertNotIn("SyntheticPass123", json.dumps(listed))

    def test_progress_tracks_fetched_documents_and_finishes(self):
        calls = []

        def fake_search(**kwargs):
            calls.append({"since": kwargs.get("since"), "order": kwargs.get("order")})
            return [{"id": f"doc-{len(calls)}", "timestamp": "2026-01-01T00:00:00Z"}]

        with (
            patch.object(self.pull, "wazuh_count", lambda **kwargs: 2),
            patch.object(self.pull, "wazuh_search", fake_search),
            patch.object(self.pull, "get_db", fake_get_db),
            patch.object(self.pull, "ingest_alerts_batch", lambda conn, alerts: (len(alerts), 0, 0)),
            patch.object(self.pull, "ingest_alert_with_dedup", lambda conn, alert: (True, False)),
            patch.object(self.pull, "normalize_alert", lambda raw: raw),
        ):
            job_id = self.pull.start_pull_job(base_config())
            job = wait_for(self.pull, job_id)

        self.assertEqual(job["status"], "done")
        self.assertEqual(job["total"], 2)
        self.assertEqual(job["target"], 2)
        self.assertEqual(job["fetched"], 2)
        self.assertEqual(job["inserted"], 2)
        self.assertEqual(job["deduplicated"], 0)
        self.assertEqual(job["failed"], 0)
        self.assertEqual(job["windows_done"], 2)
        self.assertEqual(job["percent"], 100.0)
        self.assertTrue(job["finished_at"])
        self.assertGreaterEqual(job["rate"], 0)
        for stage in ("count_ms", "fetch_ms", "normalize_ms", "ingest_ms"):
            self.assertIn(stage, job["timings"])
        self.assertEqual(len(calls), 2)
        self.assertTrue(all(call["order"] == "asc" for call in calls))

    def test_batch_failure_falls_back_to_per_document_ingest(self):
        seen = []

        def failing_batch(conn, alerts):
            raise RuntimeError("synthetic batch failure")

        def fake_single(conn, alert):
            seen.append(alert["id"])
            return True, False

        with (
            patch.object(self.pull, "wazuh_count", lambda **kwargs: 2),
            patch.object(self.pull, "wazuh_search", lambda **kwargs: [{"id": "fallback-doc"}]),
            patch.object(self.pull, "get_db", fake_get_db),
            patch.object(self.pull, "ingest_alerts_batch", failing_batch),
            patch.object(self.pull, "ingest_alert_with_dedup", fake_single),
            patch.object(self.pull, "normalize_alert", lambda raw: raw),
        ):
            job_id = self.pull.start_pull_job(base_config())
            job = wait_for(self.pull, job_id)

        self.assertEqual(job["status"], "done")
        self.assertEqual(job["inserted"], 2)
        self.assertEqual(sorted(seen), ["fallback-doc", "fallback-doc"])

    def test_count_failure_does_not_abort_the_pull(self):
        def failing_count(**kwargs):
            raise RuntimeError("count endpoint unavailable")

        with (
            patch.object(self.pull, "wazuh_count", failing_count),
            patch.object(self.pull, "wazuh_search", lambda **kwargs: []),
            patch.object(self.pull, "get_db", fake_get_db),
            patch.object(self.pull, "ingest_alert_with_dedup", lambda conn, alert: (True, False)),
            patch.object(self.pull, "normalize_alert", lambda raw: raw),
        ):
            job_id = self.pull.start_pull_job(base_config())
            job = wait_for(self.pull, job_id)

        self.assertEqual(job["status"], "done")
        self.assertIsNone(job["total"])
        self.assertIsNone(job["target"])
        self.assertEqual(job["fetched"], 0)

    def test_search_failure_marks_the_job_as_error_without_credentials(self):
        def failing_search(**kwargs):
            raise RuntimeError("indexer rejected the query")

        with (
            patch.object(self.pull, "wazuh_count", lambda **kwargs: 10),
            patch.object(self.pull, "wazuh_search", failing_search),
            patch.object(self.pull, "get_db", fake_get_db),
            patch.object(self.pull, "ingest_alert_with_dedup", lambda conn, alert: (True, False)),
            patch.object(self.pull, "normalize_alert", lambda raw: raw),
        ):
            job_id = self.pull.start_pull_job(base_config())
            job = wait_for(self.pull, job_id)

        self.assertEqual(job["status"], "error")
        self.assertIn("indexer rejected the query", job["error"])
        self.assertNotIn("SyntheticPass123", json.dumps(job))


if __name__ == "__main__":
    unittest.main()
