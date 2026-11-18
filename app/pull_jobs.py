"""Background Wazuh alert pulls with resumable progress reporting.

The realtime monitor pulls small incremental batches. A manual backfill can span
days and tens of thousands of alerts, so it runs here as a cancellable background
job: the HTTP request returns immediately and the UI polls a progress document.

Only standard-library threading is used; the app runs as a single uvicorn
process, matching the job registry's process-local lifetime.
"""

from __future__ import annotations

import re
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from typing import Any

from app.core import normalize_alert
from app.database import get_db, ingest_alerts_batch, ingest_alert_with_dedup
from app.settings import _normalize_wazuh_timestamp, wazuh_count, wazuh_search

MAX_JOBS = 20
MAX_DOCS_LIMIT = 100000
PAGE_SIZE_DEFAULT = 2000
PAGE_SIZE_LIMIT = 10000

_JOBS: dict[str, dict[str, Any]] = {}
_LOCK = threading.Lock()
# Progress fields are shared by parallel window workers.
_STATE_LOCK = threading.Lock()
# Ingest is serialized so batch dedup sees rows committed by the previous page.
_INGEST_LOCK = threading.Lock()
WINDOW_WORKERS = 3


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _public(job: dict[str, Any]) -> dict[str, Any]:
    """Return a client-safe snapshot; drop credentials and thread internals."""
    fields = (
        "id", "status", "started_at", "finished_at", "time_from", "time_to",
        "min_rule_level", "max_rule_level", "max_docs", "page_size",
        "total", "target", "fetched", "inserted", "deduplicated", "failed",
        "windows_done", "windows_total", "current_window", "capped",
        "percent", "error", "index_pattern", "timings", "rate", "eta_seconds",
    )
    result = {key: job.get(key) for key in fields}
    result["cancel_requested"] = bool(job.get("cancel"))
    return result


def _parse_time(value: str) -> datetime | None:
    text = _normalize_wazuh_timestamp(str(value or "").strip())
    if not text:
        return None
    if text.lower() == "now":
        return datetime.now(timezone.utc)
    iso = re.sub(r"([+-]\d{2})(\d{2})$", r"\1:\2", text).replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(iso)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _stamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+0000")


def _build_windows(since: str, until: str, chunk_days: int) -> list[tuple[str, str]]:
    start = _parse_time(since)
    end = _parse_time(until) if str(until or "").strip() else datetime.now(timezone.utc)
    if start is None or end is None:
        return [(str(since or "").strip(), str(until or "").strip())]
    if start >= end:
        raise ValueError("Waktu mulai harus lebih awal daripada waktu selesai.")
    if chunk_days <= 0:
        return [(_stamp(start), _stamp(end))]
    windows: list[tuple[str, str]] = []
    step = timedelta(days=chunk_days)
    cursor = start
    while cursor < end:
        nxt = min(cursor + step, end)
        windows.append((_stamp(cursor), _stamp(nxt)))
        cursor = nxt
    return windows or [(_stamp(start), _stamp(end))]


def start_pull_job(config: dict[str, Any]) -> str:
    """Validate a pull request, register a job, and start its worker thread."""
    try:
        max_docs = MAX_DOCS_LIMIT if config.get("max_docs") in (None, "") else int(config["max_docs"])
        page_size = PAGE_SIZE_DEFAULT if config.get("page_size") in (None, "") else int(config["page_size"])
    except (TypeError, ValueError):
        raise ValueError("max_docs dan page_size harus berupa angka.") from None
    if not 1 <= max_docs <= MAX_DOCS_LIMIT:
        raise ValueError(f"max_docs harus antara 1 dan {MAX_DOCS_LIMIT}.")
    if not 50 <= page_size <= PAGE_SIZE_LIMIT:
        raise ValueError(f"page_size harus antara 50 dan {PAGE_SIZE_LIMIT}.")
    if page_size > max_docs:
        page_size = max_docs
    chunk_days = int(config.get("chunk_days") if config.get("chunk_days") is not None else 1)
    if not 0 <= chunk_days <= 30:
        raise ValueError("chunk_days harus antara 0 dan 30.")

    since = str(config.get("time_from") or "").strip()
    until = str(config.get("time_to") or "").strip()
    windows = _build_windows(since, until, chunk_days)

    job_id = str(uuid.uuid4())
    job: dict[str, Any] = {
        "id": job_id,
        "status": "queued",
        "started_at": _now(),
        "finished_at": None,
        "time_from": since,
        "time_to": until,
        "min_rule_level": int(config.get("min_rule_level") or 0),
        "max_rule_level": config.get("max_rule_level"),
        "max_docs": max_docs,
        "page_size": page_size,
        "total": None,
        "target": None,
        "fetched": 0,
        "inserted": 0,
        "deduplicated": 0,
        "failed": 0,
        "windows_done": 0,
        "windows_total": len(windows),
        "current_window": None,
        "capped": False,
        "percent": 0.0,
        "error": "",
        "timings": {"count_ms": 0, "fetch_ms": 0, "normalize_ms": 0, "ingest_ms": 0},
        "rate": 0.0,
        "eta_seconds": None,
        "index_pattern": config.get("index_pattern", "wazuh-alerts-*"),
        "cancel": threading.Event(),
        "_config": {**config, "max_docs": max_docs, "page_size": page_size, "_windows": windows},
    }
    with _LOCK:
        if len(_JOBS) >= MAX_JOBS:
            finished = [key for key, item in _JOBS.items() if item.get("status") in ("done", "error", "cancelled")]
            for key in finished[: max(1, len(_JOBS) - MAX_JOBS + 1)]:
                _JOBS.pop(key, None)
        _JOBS[job_id] = job
        thread = threading.Thread(target=_run_job, args=(job,), daemon=True, name=f"wazuh-pull-{job_id[:8]}")
        thread.start()
    return job_id


def get_job(job_id: str) -> dict[str, Any] | None:
    with _LOCK:
        job = _JOBS.get(job_id)
        return _public(job) if job else None


def list_jobs(limit: int = 10) -> list[dict[str, Any]]:
    """Return active jobs first, then the most recently started finished jobs."""
    with _LOCK:
        jobs = sorted(_JOBS.values(), key=lambda item: item.get("started_at") or "", reverse=True)
        active = [job for job in jobs if job.get("status") in ("queued", "running")]
        finished = [job for job in jobs if job.get("status") not in ("queued", "running")]
        return [_public(job) for job in (active + finished)[: max(1, int(limit))]]


def cancel_job(job_id: str) -> dict[str, Any] | None:
    with _LOCK:
        job = _JOBS.get(job_id)
        if not job:
            return None
        if job.get("status") in ("queued", "running"):
            job["cancel"].set()
        return _public(job)


def _update_progress(job: dict[str, Any]) -> None:
    total = job.get("total")
    target = job.get("target")
    fetched = int(job.get("fetched") or 0)
    if target:
        job["percent"] = round(min(100.0, fetched / max(1, target) * 100), 1)
    elif total is not None and int(total) > 0:
        job["percent"] = round(min(100.0, fetched / int(total) * 100), 1)

    elapsed = 0.0
    try:
        elapsed = max(0.0, (datetime.now(timezone.utc) - datetime.fromisoformat(job["started_at"])).total_seconds())
    except (KeyError, TypeError, ValueError):
        elapsed = 0.0
    rate = fetched / elapsed if elapsed > 0.5 else 0.0
    job["rate"] = round(rate, 2)
    remaining = (target if target else total) or 0
    job["eta_seconds"] = (
        round(max(0, remaining - fetched) / rate) if rate > 0 and remaining > fetched else None
    )


def _run_job(job: dict[str, Any]) -> None:
    config = job["_config"]
    job["status"] = "running"
    cancel = job["cancel"]
    windows = config["_windows"]
    try:
        try:
            count_started = time.perf_counter()
            total = wazuh_count(
                indexer_url=config["indexer_url"],
                username=config.get("username", ""),
                password=config.get("password", ""),
                index_pattern=config["index_pattern"],
                verify_tls=bool(config.get("verify_tls", True)),
                since=config.get("time_from", ""),
                until=config.get("time_to", ""),
                min_rule_level=job["min_rule_level"],
                max_rule_level=job["max_rule_level"],
            )
            job["total"] = total
            job["target"] = min(total, job["max_docs"])
            job["capped"] = total > job["max_docs"]
        except Exception:
            # A failed count must not stop the pull; progress becomes per-window.
            job["total"] = None
            job["target"] = None
        finally:
            job["timings"]["count_ms"] += round((time.perf_counter() - count_started) * 1000)
        _update_progress(job)

        remaining = job["max_docs"]

        def pull_window(index: int, window_from: str, window_until: str) -> None:
            nonlocal remaining
            search_after: list[Any] | None = None
            while not cancel.is_set():
                with _STATE_LOCK:
                    if remaining <= 0:
                        return
                    wanted = min(job["page_size"], remaining)
                    remaining -= wanted
                    job["current_window"] = {"from": window_from, "to": window_until, "index": index + 1}
                cursor: dict[str, Any] = {}
                fetch_started = time.perf_counter()
                try:
                    docs = wazuh_search(
                        indexer_url=config["indexer_url"],
                        username=config.get("username", ""),
                        password=config.get("password", ""),
                        index_pattern=config["index_pattern"],
                        verify_tls=bool(config.get("verify_tls", True)),
                        size=wanted,
                        since=window_from,
                        until=window_until,
                        min_rule_level=job["min_rule_level"],
                        max_rule_level=job["max_rule_level"],
                        search_after=search_after,
                        cursor=cursor,
                        order="asc",
                    )
                finally:
                    with _STATE_LOCK:
                        job["timings"]["fetch_ms"] += round((time.perf_counter() - fetch_started) * 1000)
                if len(docs) < wanted:
                    # Return the unused reservation so the cap stays tight.
                    with _STATE_LOCK:
                        remaining += wanted - len(docs)
                if not docs:
                    break
                inserted, dedup, failed = _ingest(docs, job["timings"])
                with _STATE_LOCK:
                    job["fetched"] += len(docs)
                    job["inserted"] += inserted
                    job["deduplicated"] += dedup
                    job["failed"] += failed
                    _update_progress(job)
                if not cursor.get("has_more"):
                    break
                search_after = cursor.get("search_after")
                if not isinstance(search_after, list) or not search_after:
                    break
            if not cancel.is_set():
                with _STATE_LOCK:
                    job["windows_done"] += 1
                    _update_progress(job)

        workers = min(WINDOW_WORKERS, max(1, len(windows)))
        if workers == 1:
            for index, (window_from, window_until) in enumerate(windows):
                if cancel.is_set():
                    break
                pull_window(index, window_from, window_until)
        else:
            with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="wazuh-window") as pool:
                futures = [
                    pool.submit(pull_window, index, window_from, window_until)
                    for index, (window_from, window_until) in enumerate(windows)
                ]
                for future in futures:
                    future.result()

        if cancel.is_set():
            job["status"] = "cancelled"
        else:
            job["status"] = "done"
        job["percent"] = 100.0 if job["status"] == "done" else job.get("percent", 0.0)
    except Exception as error:  # noqa: BLE001 - job boundary must report, not crash the worker
        job["status"] = "error"
        job["error"] = str(error)[:500]
    finally:
        job["finished_at"] = _now()
        job["current_window"] = None
        # Credentials live only for the duration of the job.
        job.pop("_config", None)


def _ingest(docs: list[dict[str, Any]], timings: dict[str, Any] | None = None) -> tuple[int, int, int]:
    normalize_started = time.perf_counter()
    normalized: list[dict[str, Any]] = []
    failed = 0
    for item in docs:
        try:
            normalized.append(normalize_alert(item))
        except Exception:
            failed += 1
    if timings is not None:
        with _STATE_LOCK:
            timings["normalize_ms"] = timings.get("normalize_ms", 0) + round((time.perf_counter() - normalize_started) * 1000)
    if not normalized:
        return 0, 0, failed

    inserted = deduplicated = 0
    ingest_started = time.perf_counter()
    # Window workers fetch in parallel but write through one lock so batch dedup
    # always sees the previous page's committed rows.
    with _INGEST_LOCK:
        with get_db() as conn:
            try:
                # One transaction per page; the batch preloads duplicates instead of
                # issuing two or three queries for every single alert.
                with conn.transaction():
                    inserted, deduplicated, batch_failed = ingest_alerts_batch(conn, normalized)
                failed += batch_failed
            except Exception:
                # A page-level batch failure rolls back to its savepoint; retry the
                # page per document so one malformed alert cannot lose the rest.
                inserted = deduplicated = 0
                for alert in normalized:
                    try:
                        with conn.transaction():
                            did_insert, _ = ingest_alert_with_dedup(conn, alert)
                    except Exception:
                        failed += 1
                        continue
                    if did_insert:
                        inserted += 1
                    else:
                        deduplicated += 1
    if timings is not None:
        with _STATE_LOCK:
            timings["ingest_ms"] = timings.get("ingest_ms", 0) + round((time.perf_counter() - ingest_started) * 1000)
    return inserted, deduplicated, failed
