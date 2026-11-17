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
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from app.core import normalize_alert
from app.database import get_db, ingest_alert_with_dedup
from app.settings import _normalize_wazuh_timestamp, wazuh_count, wazuh_search

MAX_JOBS = 20
MAX_DOCS_LIMIT = 100000
PAGE_SIZE_DEFAULT = 1000
PAGE_SIZE_LIMIT = 5000

_JOBS: dict[str, dict[str, Any]] = {}
_LOCK = threading.Lock()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _public(job: dict[str, Any]) -> dict[str, Any]:
    """Return a client-safe snapshot; drop credentials and thread internals."""
    fields = (
        "id", "status", "started_at", "finished_at", "time_from", "time_to",
        "min_rule_level", "max_rule_level", "max_docs", "page_size",
        "total", "target", "fetched", "inserted", "deduplicated", "failed",
        "windows_done", "windows_total", "current_window", "capped",
        "percent", "error", "index_pattern",
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


def _run_job(job: dict[str, Any]) -> None:
    config = job["_config"]
    job["status"] = "running"
    cancel = job["cancel"]
    windows = config["_windows"]
    try:
        try:
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

        remaining = job["max_docs"]
        for index, (window_from, window_until) in enumerate(windows):
            if cancel.is_set() or remaining <= 0:
                break
            job["current_window"] = {"from": window_from, "to": window_until, "index": index + 1}
            search_after: list[Any] | None = None
            while remaining > 0 and not cancel.is_set():
                cursor: dict[str, Any] = {}
                docs = wazuh_search(
                    indexer_url=config["indexer_url"],
                    username=config.get("username", ""),
                    password=config.get("password", ""),
                    index_pattern=config["index_pattern"],
                    verify_tls=bool(config.get("verify_tls", True)),
                    size=min(job["page_size"], remaining),
                    since=window_from,
                    until=window_until,
                    min_rule_level=job["min_rule_level"],
                    max_rule_level=job["max_rule_level"],
                    search_after=search_after,
                    cursor=cursor,
                    order="asc",
                )
                if not docs:
                    break
                inserted, dedup, failed = _ingest(docs)
                job["fetched"] += len(docs)
                job["inserted"] += inserted
                job["deduplicated"] += dedup
                job["failed"] += failed
                remaining -= len(docs)
                _update_progress(job)
                if not cursor.get("has_more"):
                    break
                search_after = cursor.get("search_after")
                if not isinstance(search_after, list) or not search_after:
                    break
            job["windows_done"] = index + 1
            _update_progress(job)

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


def _ingest(docs: list[dict[str, Any]]) -> tuple[int, int, int]:
    inserted = deduplicated = failed = 0
    with get_db() as conn:
        for item in docs:
            try:
                # Savepoint per document: one bad alert must not abort the rest
                # of the page's transaction.
                with conn.transaction():
                    normalized = normalize_alert(item)
                    did_insert, _ = ingest_alert_with_dedup(conn, normalized)
            except Exception:
                failed += 1
                continue
            if did_insert:
                inserted += 1
            else:
                deduplicated += 1
    return inserted, deduplicated, failed
