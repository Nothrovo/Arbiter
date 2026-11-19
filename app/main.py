"""FastAPI Application Server for Arbiter — SOC Telemetry & Incident Workspace."""

from __future__ import annotations

import csv
import io
import json
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote

from fastapi import Body, Depends, FastAPI, File, HTTPException, Query, Request, Response, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from app.auth import (
    SESSION_COOKIE_NAME,
    SESSION_TTL_SECONDS,
    authenticate_user,
    create_session_token,
    create_user,
    delete_user,
    get_user,
    list_users,
    update_user,
    verify_session_token,
)
from app.config import HOST, PORT
from app.ai_triage import (
    AI_TRIAGE_STATE_KEY,
    current_wib_window_key,
    get_triage_state_key,
    merge_triage_groups,
    safe_alerts,
    test_ollama,
    triage_with_fallback,
    wib_window_key,
)
from app.core import normalize_alert, suggestions_with_fallback
from app.exclusions import (
    MAX_EXCLUSION_RULES,
    normalize_exclusion_rule,
    parse_wazuh_exclusion,
    with_exclusions,
)
from app.intel import enrich_ip, is_valid_ip, lookup_remote_ip_cache_detail, sync_remote_cache, upsert_ip_cache
import app.database as db_module
from app.database import get_db, init_database, ingest_alert_with_dedup
from app.exports import (
    generate_docx_landscape_report,
    generate_gdocs_html_report,
    generate_markdown_report,
    generate_tsv_table,
    generate_xlsx_workbook,
)
from app.parser import parse_export
from app.privacy import sanitize_text
from app.pull_jobs import cancel_job, get_job, list_jobs, start_pull_job
from app.query import alert_where, normalize_tenants, positive_ids, tenant_clause, validated_group_id, PIVOT_DEFINITIONS, FACET_COLUMNS, is_malicious_alert_record
from app.settings import (
    _normalize_wazuh_timestamp,
    _valid_timestamp,
    intel_abuseipdb_key,
    load_document,
    load_settings,
    migrate_settings,
    redact_settings,
    save_document,
    save_settings,
    test_wazuh_connection,
    validate_settings,
    wazuh_password,
    wazuh_search,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure tables, schemas, and indices are fully initialized on startup
    init_database()
    try:
        with get_db() as conn:
            migrate_settings(conn)
    except Exception:
        # Startup must not fail if legacy credential migration is not possible.
        pass
    yield


app = FastAPI(
    title="Arbiter — SOC Telemetry & Incident Workspace",
    version="2.0.0",
    lifespan=lifespan,
)


def _extract_request_user(request: Request) -> dict[str, Any] | None:
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        auth_header = request.headers.get("authorization") or ""
        if auth_header.lower().startswith("bearer "):
            token = auth_header[7:].strip()
        else:
            token = request.headers.get("x-arbiter-token")
    claims = verify_session_token(token)
    if not claims:
        return None
    try:
        with get_db() as conn:
            user = get_user(conn, claims["username"])
            return user
    except Exception:
        return claims


_PUBLIC_API_PATHS = {"/api/auth/login", "/api/auth/logout", "/api/auth/me", "/api/health"}


@app.middleware("http")
async def no_cache_and_auth_middleware(request: Request, call_next):
    path = request.url.path
    if path.startswith("/api/") and path not in _PUBLIC_API_PATHS:
        enforce_auth = (
            PORT != 0
            or request.headers.get("x-arbiter-auth-enforce") == "1"
            or SESSION_COOKIE_NAME in request.cookies
            or "authorization" in request.headers
            or "x-arbiter-token" in request.headers
            or path.startswith("/api/auth/users")
        )
        if enforce_auth:
            user = _extract_request_user(request)
            if not user:
                return JSONResponse(
                    {"detail": "Sesi login diperlukan. Silakan login terlebih dahulu."},
                    status_code=401,
                )
            request.state.user = user
            is_admin_only = (
                path.startswith("/api/auth/users")
                or path.startswith("/api/database")
                or (path.startswith("/api/settings") and request.method != "GET")
            )
            if is_admin_only and user.get("role") != "admin":
                return JSONResponse(
                    {"detail": "Akses ditolak. Fitur ini hanya dapat diakses oleh Admin."},
                    status_code=403,
                )

    response = await call_next(request)
    if path == "/" or path.startswith(("/static/js/", "/static/styles/")):
        response.headers["Cache-Control"] = "no-cache, must-revalidate"
    return response


app.mount("/static", StaticFiles(directory=Path(__file__).with_name("static"), check_dir=False), name="static")


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    fav_path = Path(__file__).with_name("static") / "img" / "favicon.svg"
    return FileResponse(fav_path, media_type="image/svg+xml")


@app.get("/api/health")
def health_check():
    with get_db() as conn:
        alerts_n = conn.execute("SELECT count(*) AS n FROM wazuh.alerts").fetchone()["n"]
        groups_n = conn.execute("SELECT count(*) AS n FROM wazuh.analysis_groups").fetchone()["n"]
        intel_n = 0
        try:
            intel_n = conn.execute("SELECT count(*) AS n FROM public.ip_intel_cache").fetchone()["n"]
        except Exception:
            pass

    return {
        "status": "ok",
        "app": "Arbiter",
        "alerts": alerts_n,
        "groups": groups_n,
        "ip_intel_records": intel_n,
        "privacy": "airgapped_local",
    }


@app.get("/health", include_in_schema=False)
def health_alias():
    """Lightweight liveness probe for reverse proxies and monitors.

    Full workspace aggregates remain at /api/health.
    """
    return {"status": "ok", "app": "Arbiter"}


@app.get("/api/tenants")
def get_tenants():
    with get_db() as conn:
        rows = conn.execute(
            """SELECT tenant, count(*) as count 
               FROM wazuh.alerts 
               GROUP BY tenant 
               ORDER BY count DESC, tenant ASC"""
        ).fetchall()
    return {"tenants": rows}


def _process_alerts_ingest(raw_alerts: list[dict[str, Any]]) -> dict[str, int]:
    inserted_count = 0
    dedup_count = 0
    with get_db() as conn:
        for item in raw_alerts:
            normalized = normalize_alert(item)
            inserted, deduped = ingest_alert_with_dedup(conn, normalized)
            if inserted:
                inserted_count += 1
            elif deduped:
                dedup_count += 1
    return {
        "parsed": len(raw_alerts),
        "inserted": inserted_count,
        "deduplicated": dedup_count,
    }


def _scope_tenant_value(tenant: str | list[str] | tuple[str, ...] | None) -> str | list[str]:
    """Normalize a request scope while retaining the legacy single-tenant echo."""
    tenants = normalize_tenants(tenant)
    if not tenants:
        return "all"
    return tenants[0] if len(tenants) == 1 else list(tenants)


def _tenant_label(tenant: str | list[str] | tuple[str, ...] | None) -> str:
    tenants = normalize_tenants(tenant)
    return ", ".join(tenants) if tenants else "Semua Tenant"


@app.post("/api/import")
async def import_file(file: UploadFile = File(...)):
    raw_bytes = await file.read()
    try:
        content = raw_bytes.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="File must be UTF-8 encoded text/JSON") from exc

    try:
        alerts, warnings = parse_export(content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    stats = _process_alerts_ingest(alerts)
    return {**stats, "warnings": warnings}


@app.post("/api/import-text")
def import_text(payload: dict[str, Any]):
    content = str(payload.get("content") or payload.get("text") or "").strip()
    if not content:
        raise HTTPException(status_code=400, detail="Content cannot be empty.")
    try:
        alerts, warnings = parse_export(content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    stats = _process_alerts_ingest(alerts)
    return {**stats, "warnings": warnings}


CLAIM_TIMEOUT_SECONDS = 30 * 60  # 30 minutes per PRD Section 3.B
ALLOWED_VERDICTS = {"tp", "fp", "benign", "needs_review"}


def _current_username(request: Request | None, fallback: str = "analyst") -> str:
    if request is not None:
        user = getattr(request.state, "user", None) or _extract_request_user(request)
        if user and user.get("username"):
            return str(user["username"])
    return fallback


def _expire_stale_claims(conn) -> int:
    """PRD Section 3.B Graceful Auto-Release: release claims older than 30 minutes without heartbeat."""
    cutoff = (datetime.now(timezone.utc) - timedelta(seconds=CLAIM_TIMEOUT_SECONDS)).isoformat()
    try:
        cur = conn.execute(
            """UPDATE wazuh.alerts
               SET status = 'claimed_expired'
               WHERE status = 'claimed' AND claimed_at IS NOT NULL AND claimed_at < %s""",
            (cutoff,),
        )
        return cur.rowcount if (cur and hasattr(cur, "rowcount") and cur.rowcount is not None and cur.rowcount >= 0) else 0
    except Exception:
        return 0


def _exclusion_document(conn) -> dict[str, Any]:
    """Load workspace exclusions for discovery views; never block on a bad row."""
    try:
        return load_settings(conn).get("exclusions") or {}
    except Exception:
        return {}


@app.get("/api/alerts")
def list_alerts(
    q: str = "",
    tenant: list[str] = Query(default=["all"]),
    status: str = "all",
    group_id: str | None = None,
    filter_preset: str = "",
    review_status: str = "all",
    time_preset: str = "",
    time_from: str = "",
    time_to: str = "",
    facet: str = "",
    facet_value: str = "",
    secondary_facet: str = "",
    secondary_facet_value: str = "",
    alert_ids: str = "",
    filters: str = "",
    reviewed_from: str = "",
    reviewed_to: str = "",
    sort: str = "desc",
    sort_by: str = "timestamp",
    limit: int = 500,
    offset: int = 0,
    summary: bool = False,
):
    if offset < 0:
        raise HTTPException(status_code=422, detail="offset must be zero or greater.")
    limit = min(max(limit, 1), 10000)
    where_sql, params = alert_where(
        q=q, tenant=tenant, status=status, group_id=group_id,
        filter_preset=filter_preset, review_status=review_status,
        time_preset=time_preset, time_from=time_from, time_to=time_to,
        facet=facet, facet_value=facet_value,
        secondary_facet=secondary_facet, secondary_facet_value=secondary_facet_value,
        alert_ids=alert_ids, filters=filters,
        reviewed_from=reviewed_from, reviewed_to=reviewed_to,
    )

    # Sort order
    order_dir = "ASC" if str(sort).lower() == "asc" else "DESC"
    if sort_by == "hits":
        order_col = f"a.hit_count {order_dir} NULLS LAST, a.timestamp {order_dir} NULLS LAST, a.id {order_dir}"
    elif sort_by == "severity":
        order_col = f"a.rule_level {order_dir} NULLS LAST, a.timestamp {order_dir} NULLS LAST, a.id {order_dir}"
    else:
        order_col = f"a.timestamp {order_dir} NULLS LAST, a.id {order_dir}"

    projection = """a.id, a.alert_id, a.timestamp, a.tenant, a.agent_name, a.agent_ip,
        a.rule_id, a.rule_level, a.description, a.rule_groups, a.decoder, a.location,
        a.source_ip, a.mitre_ids, a.cve, a.hit_count, a.first_seen, a.last_seen, a.is_reviewed, a.reviewed_at,
        a.status, a.claimed_by, a.claimed_at, a.verdict, a.reviewed_by"""
    if not summary:
        projection += """, a.data, a.raw, a.wazuh_ids, a.duplicate_instances,
        a.parsed_details, a.reviewer_notes,
        COALESCE(a.raw->>'full_log', '') AS full_log,
        COALESCE(a.raw->>'previous_output', '') AS previous_output"""

    explicit_selection = alert_ids is not None and str(alert_ids).strip() != ""
    with get_db() as conn:
        _expire_stale_claims(conn)
        scoped_sql, scoped_params = where_sql, params
        if not explicit_selection:
            scoped_sql, scoped_params = with_exclusions(where_sql, params, _exclusion_document(conn))
        sql = f"""
        SELECT {projection},
            ipc.abuse_score,
            ipc.vt_malicious,
            ipc.country_code,
            ipc.isp,
            ipc.attack_types,
            COALESCE(
                json_agg(json_build_object('id', g.id, 'title', g.title, 'category', g.category))
                FILTER (WHERE g.id IS NOT NULL),
                '[]'
            ) AS groups
        FROM wazuh.alerts a
        LEFT JOIN public.ip_intel_cache ipc ON a.source_ip = ipc.ip
        LEFT JOIN wazuh.alert_group_members m ON m.alert_pk = a.id
        LEFT JOIN wazuh.analysis_groups g ON g.id = m.group_id
        {scoped_sql}
        GROUP BY 
            a.id, ipc.abuse_score, ipc.vt_malicious, ipc.country_code, ipc.isp, ipc.attack_types
        ORDER BY {order_col}
        LIMIT %s OFFSET %s
        """
        count_sql = f"SELECT count(*) AS n FROM wazuh.alerts a {scoped_sql}"
        try:
            rows = conn.execute(sql, scoped_params + [limit, offset]).fetchall()
        except Exception:
            fallback_proj = projection.replace(",\n        a.status, a.claimed_by, a.claimed_at, a.verdict, a.reviewed_by", "")
            fallback_sql = sql.replace(projection, fallback_proj)
            rows = conn.execute(fallback_sql, scoped_params + [limit, offset]).fetchall()
        total = conn.execute(count_sql, scoped_params).fetchone()["n"]

    return {"items": rows, "total": total}


@app.get("/api/alerts/pull")
def api_list_alert_pulls(limit: int = Query(default=10, ge=1, le=50)):
    """List recent pull jobs so a page (or the shell) can resume after navigation."""
    return {"jobs": list_jobs(limit)}


@app.get("/api/alerts/{alert_id}")
def get_alert_detail(alert_id: int, tenant: list[str] = Query(default=["all"])):
    where = "a.id = %s"
    params: list[Any] = [alert_id]
    tenant_sql, tenant_params = tenant_clause("a", tenant)
    if tenant_sql:
        where += " AND " + tenant_sql
        params.extend(tenant_params)
    with get_db() as conn:
        _expire_stale_claims(conn)
        row = conn.execute(
            f"""SELECT a.*, COALESCE(a.raw->>'full_log', '') AS full_log,
                       COALESCE(a.raw->>'previous_output', '') AS previous_output,
                       ipc.abuse_score, ipc.vt_malicious, ipc.country_code, ipc.isp,
                       ipc.attack_types,
                       COALESCE(json_agg(json_build_object('id', g.id, 'title', g.title, 'category', g.category))
                                FILTER (WHERE g.id IS NOT NULL), '[]') AS groups
                FROM wazuh.alerts a
                LEFT JOIN public.ip_intel_cache ipc ON a.source_ip = ipc.ip
                LEFT JOIN wazuh.alert_group_members m ON m.alert_pk = a.id
                LEFT JOIN wazuh.analysis_groups g ON g.id = m.group_id
                WHERE {where}
                GROUP BY a.id, ipc.abuse_score, ipc.vt_malicious, ipc.country_code, ipc.isp, ipc.attack_types""",
            params,
        ).fetchone()
        if row is not None:
            record = dict(row)
            raw_obj = record.get("raw")
            if not raw_obj or (isinstance(raw_obj, dict) and not raw_obj):
                try:
                    ext = conn.execute(
                        "SELECT raw, duplicate_instances FROM wazuh.alert_raw WHERE alert_pk = %s",
                        (alert_id,),
                    ).fetchone()
                    if ext and ext.get("raw"):
                        record["raw"] = ext["raw"]
                        if isinstance(ext["raw"], dict):
                            record["full_log"] = record.get("full_log") or ext["raw"].get("full_log") or ""
                            record["previous_output"] = record.get("previous_output") or ext["raw"].get("previous_output") or ""
                        if ext.get("duplicate_instances") and not record.get("duplicate_instances"):
                            record["duplicate_instances"] = ext["duplicate_instances"]
                except Exception:
                    pass
            row = record
    if row is None:
        raise HTTPException(status_code=404, detail="Alert not found in this scope.")
    return row


@app.post("/api/alerts/{alert_id}/claim")
def claim_alert(
    alert_id: int,
    request: Request,
    payload: dict[str, Any] | None = Body(default=None),
    tenant: list[str] = Query(default=["all"]),
):
    """PRD Section 3.B Atomic Locking (Optimistic Update) for alert claiming."""
    data = payload if isinstance(payload, dict) else {}
    user_id = str(data.get("user_id") or _current_username(request)).strip() or "analyst"
    now_iso = datetime.now(timezone.utc).isoformat()
    with get_db() as conn:
        _validate_membership(conn, [alert_id], tenant)
        _expire_stale_claims(conn)
        cur = conn.execute(
            """UPDATE wazuh.alerts
               SET status = 'claimed', claimed_by = %s, claimed_at = %s
               WHERE id = %s AND (status IS NULL OR status = '' OR status = 'unread' OR status = 'claimed_expired' OR (status = 'claimed' AND claimed_by = %s))
               RETURNING id, status, claimed_by, claimed_at""",
            (user_id, now_iso, alert_id, user_id),
        )
        updated = cur.fetchone()
        if not updated:
            current = conn.execute(
                "SELECT id, status, claimed_by, claimed_at FROM wazuh.alerts WHERE id = %s",
                (alert_id,),
            ).fetchone()
            owner = (current or {}).get("claimed_by") or "analis lain"
            status_val = (current or {}).get("status") or "locked"
            raise HTTPException(
                status_code=409,
                detail=f"Alert #{alert_id} sudah diklaim oleh {owner} (status: {status_val}).",
            )
    return {
        "status": "claimed",
        "id": alert_id,
        "claimed_by": user_id,
        "claimed_at": now_iso,
    }


@app.post("/api/alerts/{alert_id}/heartbeat")
def heartbeat_alert_claim(
    alert_id: int,
    request: Request,
    payload: dict[str, Any] | None = Body(default=None),
    tenant: list[str] = Query(default=["all"]),
):
    """PRD Section 3.B Heartbeat: refresh claimed_at every 2 minutes while analyst inspects alert."""
    data = payload if isinstance(payload, dict) else {}
    user_id = str(data.get("user_id") or _current_username(request)).strip() or "analyst"
    now_iso = datetime.now(timezone.utc).isoformat()
    with get_db() as conn:
        _validate_membership(conn, [alert_id], tenant)
        _expire_stale_claims(conn)
        cur = conn.execute(
            """UPDATE wazuh.alerts
               SET claimed_at = %s, status = 'claimed'
               WHERE id = %s AND status = 'claimed' AND claimed_by = %s
               RETURNING id, status, claimed_by, claimed_at""",
            (now_iso, alert_id, user_id),
        )
        if not cur.fetchone():
            raise HTTPException(
                status_code=409,
                detail="Sesi klaim telah berakhir atau diambil alih. Klaim ulang alert ini untuk melanjutkan.",
            )
    return {
        "status": "claimed",
        "id": alert_id,
        "claimed_by": user_id,
        "claimed_at": now_iso,
    }


@app.post("/api/alerts/{alert_id}/release")
def release_alert_claim(
    alert_id: int,
    request: Request,
    payload: dict[str, Any] | None = Body(default=None),
    tenant: list[str] = Query(default=["all"]),
):
    """Release an active claim back to unread so another analyst can claim it."""
    data = payload if isinstance(payload, dict) else {}
    user = getattr(request.state, "user", None) or _extract_request_user(request)
    user_id = str(data.get("user_id") or (user.get("username") if user else "analyst")).strip() or "analyst"
    is_privileged = bool(user and user.get("role") in ("admin", "director")) or bool(data.get("force"))
    with get_db() as conn:
        _validate_membership(conn, [alert_id], tenant)
        if is_privileged:
            conn.execute(
                """UPDATE wazuh.alerts
                   SET status = CASE WHEN is_reviewed THEN 'reviewed' ELSE 'unread' END,
                       claimed_by = NULL, claimed_at = NULL
                   WHERE id = %s""",
                (alert_id,),
            )
        else:
            cur = conn.execute(
                """UPDATE wazuh.alerts
                   SET status = CASE WHEN is_reviewed THEN 'reviewed' ELSE 'unread' END,
                       claimed_by = NULL, claimed_at = NULL
                   WHERE id = %s AND (claimed_by = %s OR claimed_by IS NULL OR status != 'claimed')
                   RETURNING id""",
                (alert_id, user_id),
            )
            if not cur.fetchone():
                raise HTTPException(status_code=403, detail="Hanya pemilik klaim, Director, atau Admin yang dapat melepas klaim ini.")
    return {"status": "unread", "id": alert_id}


@app.put("/api/alerts/{alert_id}/review")
def update_alert_review(
    alert_id: int,
    payload: dict[str, Any],
    request: Request,
    tenant: list[str] = Query(default=["all"]),
):
    is_reviewed = bool(payload.get("is_reviewed", True))
    notes = str(payload.get("reviewer_notes") or "").strip()
    raw_verdict = payload.get("verdict")
    verdict: str | None = None
    if raw_verdict is not None and str(raw_verdict).strip() != "":
        v_clean = str(raw_verdict).strip().lower()
        if v_clean not in ALLOWED_VERDICTS:
            raise HTTPException(status_code=400, detail="Verdict harus berupa 'tp', 'fp', 'benign', atau 'needs_review'.")
        verdict = v_clean
    reviewer = str(payload.get("reviewed_by") or _current_username(request)).strip() or "analyst"
    new_status = "reviewed" if is_reviewed else "unread"
    with get_db() as conn:
        _validate_membership(conn, [alert_id], tenant)
        prev = conn.execute("SELECT tenant, is_reviewed FROM wazuh.alerts WHERE id = %s", (alert_id,)).fetchone()
        try:
            conn.execute(
                """UPDATE wazuh.alerts
                   SET is_reviewed = %s,
                       reviewed_at = CASE WHEN %s THEN now() ELSE NULL END,
                       reviewer_notes = %s,
                       status = %s,
                       verdict = CASE WHEN %s THEN COALESCE(%s, verdict) ELSE NULL END,
                       reviewed_by = CASE WHEN %s THEN %s ELSE NULL END,
                       claimed_by = CASE WHEN %s THEN COALESCE(claimed_by, %s) ELSE NULL END
                   WHERE id = %s""",
                (
                    is_reviewed,
                    is_reviewed,
                    notes,
                    new_status,
                    is_reviewed,
                    verdict,
                    is_reviewed,
                    reviewer,
                    is_reviewed,
                    reviewer,
                    alert_id,
                ),
            )
        except Exception:
            conn.execute(
                """UPDATE wazuh.alerts
                   SET is_reviewed = %s,
                       reviewed_at = CASE WHEN %s THEN now() ELSE NULL END,
                       reviewer_notes = %s
                   WHERE id = %s""",
                (is_reviewed, is_reviewed, notes, alert_id),
            )
        if prev and is_reviewed and not prev.get("is_reviewed") and hasattr(db_module, "bump_daily_metrics"):
            db_module.bump_daily_metrics(conn, str(prev.get("tenant") or "Default"), reviewed_delta=1, verdict=verdict)
    return {"status": "ok", "id": alert_id, "is_reviewed": is_reviewed, "verdict": verdict, "alert_status": new_status}


@app.post("/api/alerts/batch-review")
def batch_update_review(
    payload: dict[str, Any],
    request: Request,
    tenant: list[str] = Query(default=["all"]),
):
    normalize_tenants(tenant)
    alert_ids = payload.get("alert_ids") or []
    is_reviewed = bool(payload.get("is_reviewed", True))
    raw_verdict = payload.get("verdict")
    verdict: str | None = None
    if raw_verdict is not None and str(raw_verdict).strip() != "":
        v_clean = str(raw_verdict).strip().lower()
        if v_clean not in ALLOWED_VERDICTS:
            raise HTTPException(status_code=400, detail="Verdict harus berupa 'tp', 'fp', 'benign', atau 'needs_review'.")
        verdict = v_clean
    notes = str(payload.get("reviewer_notes") or "").strip()
    reviewer = str(payload.get("reviewed_by") or _current_username(request)).strip() or "analyst"
    new_status = "reviewed" if is_reviewed else "unread"
    if not alert_ids:
        raise HTTPException(status_code=400, detail="No valid alert IDs provided.")
    with get_db() as conn:
        clean_pks = _validate_membership(conn, alert_ids, tenant)
        try:
            conn.execute(
                """UPDATE wazuh.alerts
                   SET is_reviewed = %s,
                       reviewed_at = CASE WHEN %s THEN now() ELSE NULL END,
                       status = %s,
                       verdict = CASE WHEN %s THEN COALESCE(%s, verdict) ELSE NULL END,
                       reviewed_by = CASE WHEN %s THEN %s ELSE NULL END,
                       reviewer_notes = CASE WHEN %s != '' THEN %s ELSE reviewer_notes END
                   WHERE id = ANY(%s)""",
                (
                    is_reviewed,
                    is_reviewed,
                    new_status,
                    is_reviewed,
                    verdict,
                    is_reviewed,
                    reviewer,
                    notes,
                    notes,
                    clean_pks,
                ),
            )
        except Exception:
            conn.execute(
                """UPDATE wazuh.alerts
                   SET is_reviewed = %s,
                       reviewed_at = CASE WHEN %s THEN now() ELSE NULL END
                   WHERE id = ANY(%s)""",
                (is_reviewed, is_reviewed, clean_pks),
            )
        if is_reviewed and hasattr(db_module, "bump_daily_metrics"):
            db_module.bump_daily_metrics(conn, _tenant_label(tenant), reviewed_delta=len(clean_pks), verdict=verdict)
    return {"status": "ok", "count": len(clean_pks), "is_reviewed": is_reviewed, "verdict": verdict, "alert_status": new_status}


@app.post("/api/alerts/bulk-verdict-pattern")
def bulk_verdict_by_pattern(
    payload: dict[str, Any],
    request: Request,
    tenant: list[str] = Query(default=["all"]),
):
    """PRD Section 3.B Bulk Actions & Pattern Grouping: apply verdict (TP/FP/Benign) across similar alerts matching pattern/rule/IP."""
    normalize_tenants(tenant)
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Payload bulk verdict tidak valid.")
    raw_verdict = str(payload.get("verdict") or "").strip().lower()
    if raw_verdict not in {"tp", "fp", "benign"}:
        raise HTTPException(status_code=400, detail="Verdict wajib dipilih: 'tp', 'fp', atau 'benign'.")

    dry_run = bool(payload.get("dry_run", False))
    rule_id = str(payload.get("rule_id") or "").strip()
    description = str(payload.get("description") or "").strip()
    source_ip = str(payload.get("source_ip") or "").strip()
    agent_name = str(payload.get("agent_name") or "").strip()
    q = str(payload.get("q") or "").strip()
    only_unreviewed = bool(payload.get("only_unreviewed", True))
    notes = str(payload.get("reviewer_notes") or f"Bulk pattern verdict: {raw_verdict.upper()}").strip()
    reviewer = str(payload.get("reviewed_by") or _current_username(request)).strip() or "analyst"

    if not any([rule_id, description, source_ip, agent_name, q]):
        raise HTTPException(
            status_code=400,
            detail="Tentukan minimal satu kriteria pola (rule_id, description, source_ip, agent_name, atau kata kunci q).",
        )

    clauses: list[str] = []
    params: list[Any] = []
    t_sql, t_params = tenant_clause("a", tenant)
    if t_sql:
        clauses.append(t_sql)
        params.extend(t_params)
    if only_unreviewed:
        clauses.append("a.is_reviewed = false")
    if rule_id:
        clauses.append("a.rule_id = %s")
        params.append(rule_id)
    if description:
        clauses.append("a.description ILIKE %s")
        params.append(f"%{description}%")
    if source_ip:
        clauses.append("a.source_ip = %s")
        params.append(source_ip)
    if agent_name:
        clauses.append("a.agent_name = %s")
        params.append(agent_name)
    if q:
        clauses.append("(a.description ILIKE %s OR a.raw::text ILIKE %s)")
        params.extend([f"%{q}%", f"%{q}%"])

    where_sql = "WHERE " + " AND ".join(clauses) if clauses else ""
    with get_db() as conn:
        matching_rows = conn.execute(
            f"SELECT a.id, a.tenant FROM wazuh.alerts a {where_sql} LIMIT 50000",
            params,
        ).fetchall()
        pks = [int(r["id"]) for r in matching_rows]
        if dry_run or not pks:
            return {
                "status": "ok",
                "dry_run": dry_run,
                "count": len(pks),
                "verdict": raw_verdict,
            }
        conn.execute(
            """UPDATE wazuh.alerts
               SET is_reviewed = true,
                   reviewed_at = now(),
                   status = 'reviewed',
                   verdict = %s,
                   reviewed_by = %s,
                   reviewer_notes = %s
               WHERE id = ANY(%s)""",
            (raw_verdict, reviewer, notes, pks),
        )
        if hasattr(db_module, "bump_daily_metrics"):
            per_tenant: dict[str, int] = {}
            for r in matching_rows:
                t_key = str(r.get("tenant") or "Default")
                per_tenant[t_key] = per_tenant.get(t_key, 0) + 1
            for t_key, cnt in per_tenant.items():
                db_module.bump_daily_metrics(conn, t_key, reviewed_delta=cnt, verdict=raw_verdict)
    return {
        "status": "ok",
        "dry_run": False,
        "count": len(pks),
        "verdict": raw_verdict,
        "reviewed_by": reviewer,
    }


@app.post("/api/alerts/full-logs")
def bulk_full_logs(payload: dict[str, Any], tenant: list[str] = Query(default=["all"])):
    """Return full_log for a set of in-scope alert ids, for group-level copy.

    Mirrors the single-alert detail endpoint: full_log is the analyst's own
    local telemetry, returned only for alerts that pass the active tenant
    membership check. No silent widening — every id is validated.
    """
    normalize_tenants(tenant)
    alert_ids = payload.get("alert_ids") or []
    if not isinstance(alert_ids, list) or not alert_ids:
        raise HTTPException(status_code=400, detail="alert_ids harus berupa daftar id alert.")
    with get_db() as conn:
        clean_pks = _validate_membership(conn, alert_ids, tenant)
    with get_db() as conn:
        rows = conn.execute(
            """SELECT a.id, a.alert_id, a.description, a.source_ip, a.agent_name,
                      a.rule_id, a.rule_level, a.timestamp,
                      COALESCE(a.raw->>'full_log', '') AS full_log
               FROM wazuh.alerts a
               WHERE a.id = ANY(%s)
               ORDER BY a.rule_id NULLS LAST, a.timestamp NULLS LAST, a.id""",
            (clean_pks,),
        ).fetchall()
    items = [{**dict(row), "full_log": row["full_log"] or ""} for row in rows]
    return {"items": items, "count": len(items)}


@app.post("/api/intel/cache/test")
def api_intel_cache_test(payload: dict[str, Any]):
    """Read-only probe of the Neuropetra/IP Intel cache. Never calls AbuseIPDB."""
    ip = str(payload.get("ip") or "").strip()
    if not is_valid_ip(ip):
        raise HTTPException(status_code=400, detail="Masukkan alamat IPv4/IPv6 yang valid untuk diuji.")
    detail = lookup_remote_ip_cache_detail(ip)
    record = detail.get("record") or {}
    return {
        "ok": bool(detail.get("found")),
        "configured": bool(detail.get("configured")),
        "ip": ip,
        "source_table": detail.get("source_table"),
        "abuse_score": record.get("abuse_score"),
        "isp": record.get("isp"),
        "country_code": record.get("country_code"),
        "reputation_checked_at": record.get("reputation_checked_at"),
        "error": detail.get("error"),
    }


@app.post("/api/intel/enrich")
def enrich_intel(payload: dict[str, Any], tenant: list[str] = Query(default=["all"])):
    normalize_tenants(tenant)
    raw_ips = payload.get("ips") or []
    if isinstance(raw_ips, str):
        raw_ips = [raw_ips]
    alert_ids = payload.get("alert_ids") or []
    if isinstance(alert_ids, (int, str)):
        alert_ids = [alert_ids]

    target_ips: list[str] = [str(x).strip() for x in raw_ips if str(x).strip()]

    if alert_ids:
        clean_pks = positive_ids(alert_ids)
        if clean_pks:
            with get_db() as conn:
                where_clause = "WHERE a.id = ANY(%s)"
                params: list[Any] = [clean_pks]
                tenant_sql, tenant_params = tenant_clause("a", tenant)
                if tenant_sql:
                    where_clause += " AND " + tenant_sql
                    params.extend(tenant_params)
                rows = conn.execute(
                    f"SELECT DISTINCT a.source_ip FROM wazuh.alerts a {where_clause} AND a.source_ip IS NOT NULL AND a.source_ip != ''",
                    params,
                ).fetchall()
                for r in rows:
                    ip_val = (r["source_ip"] or "").strip()
                    if ip_val and ip_val not in target_ips:
                        target_ips.append(ip_val)

    unique_ips = list(dict.fromkeys(ip for ip in target_ips if is_valid_ip(ip)))[:50]
    if not unique_ips:
        raise HTTPException(status_code=400, detail="Tidak ada alamat IPv4/IPv6 valid yang diberikan untuk di-enrich.")

    results = []
    with get_db() as conn:
        stored_settings = load_settings(conn)
        stored_api_key = intel_abuseipdb_key(stored_settings)
        for ip in unique_ips:
            res = enrich_ip(ip, api_key=stored_api_key or None)
            if res.get("status") not in ("invalid", "error"):
                upsert_ip_cache(conn, res)
            results.append(res)
        if hasattr(conn, "commit"):
            conn.commit()

    sync_remote_cache(results)

    return {
        "status": "ok",
        "count": len(results),
        "enriched": results,
    }


def _scoped_groups(conn, tenant: str | list[str] | tuple[str, ...] | None = "all", group_id: str | None = None):
    group_id = validated_group_id(group_id)
    clauses: list[str] = []
    params: list[Any] = []
    tenant_sql, tenant_params = tenant_clause("a", tenant)
    if tenant_sql:
        clauses.append(tenant_sql)
        params.extend(tenant_params)
    if group_id:
        clauses.append("g.id = %s")
        params.append(group_id)
    where = "WHERE " + " AND ".join(clauses) if clauses else ""
    return conn.execute(
        f"""SELECT g.*,
                   COALESCE(array_agg(DISTINCT a.id) FILTER (WHERE a.id IS NOT NULL), '{{}}') AS alert_pks,
                   count(DISTINCT a.id) AS alert_count,
                   COALESCE(array_agg(DISTINCT a.tenant) FILTER (WHERE a.tenant IS NOT NULL), '{{}}') AS tenants
            FROM wazuh.analysis_groups g
            LEFT JOIN wazuh.alert_group_members m ON m.group_id = g.id
            LEFT JOIN wazuh.alerts a ON a.id = m.alert_pk
            {where}
            GROUP BY g.id
            ORDER BY g.created_at DESC, g.id DESC""",
        params,
    ).fetchall()


@app.get("/api/groups")
def list_groups(tenant: list[str] = Query(default=["all"])):
    with get_db() as conn:
        return _scoped_groups(conn, tenant)


@app.get("/api/groups/{group_id}")
def get_group_detail(group_id: str, tenant: list[str] = Query(default=["all"])):
    with get_db() as conn:
        rows = _scoped_groups(conn, tenant, group_id)
    if not rows:
        raise HTTPException(status_code=404, detail="Incident group not found in this scope.")
    return rows[0]


@app.post("/api/groups")
def create_group(payload: dict[str, Any], tenant: list[str] = Query(default=["all"])):
    normalize_tenants(tenant)
    title = str(payload.get("title", "")).strip()
    if not title:
        raise HTTPException(status_code=400, detail="Group / Incident title is required.")
    if normalize_tenants(tenant) and not payload.get("alert_pks"):
        raise HTTPException(status_code=400, detail="Pilih minimal satu bukti untuk tenant ini, atau buat kasus kosong dari scope Semua tenant.")
    group_id = uuid.uuid4()
    with get_db() as conn:
        pks = _validate_membership(conn, payload.get("alert_pks", []), tenant)
        conn.execute(
            """INSERT INTO wazuh.analysis_groups(
                id, title, category, analysis, conclusion, recommendation, status, severity, source
            ) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (
                group_id,
                title,
                payload.get("category", "General Incident"),
                payload.get("analysis", ""),
                payload.get("conclusion", ""),
                payload.get("recommendation", ""),
                payload.get("status", "open"),
                payload.get("severity", "medium"),
                payload.get("source", "human"),
            ),
        )
        for pk in pks:
            conn.execute(
                "INSERT INTO wazuh.alert_group_members(alert_pk, group_id) VALUES(%s, %s) ON CONFLICT DO NOTHING",
                (pk, group_id),
            )
    return {"id": str(group_id), "title": title}


@app.put("/api/groups/{group_id}")
def update_group(group_id: str, payload: dict[str, Any], tenant: list[str] = Query(default=["all"])):
    normalize_tenants(tenant)
    validated_group_id(group_id)
    if "title" in payload and not str(payload["title"] or "").strip():
        raise HTTPException(status_code=400, detail="Judul insiden wajib diisi.")
    with get_db() as conn:
        if not _scoped_groups(conn, tenant, group_id):
            raise HTTPException(status_code=404, detail="Incident group not found in this scope.")
        cur = conn.execute(
            """UPDATE wazuh.analysis_groups
               SET title = COALESCE(%s, title),
                   category = COALESCE(%s, category),
                   analysis = COALESCE(%s, analysis),
                   conclusion = COALESCE(%s, conclusion),
                   recommendation = COALESCE(%s, recommendation),
                   status = COALESCE(%s, status),
                   severity = COALESCE(%s, severity),
                   updated_at = now()
               WHERE id = %s RETURNING id""",
            (
                payload.get("title"),
                payload.get("category"),
                payload.get("analysis"),
                payload.get("conclusion"),
                payload.get("recommendation"),
                payload.get("status"),
                payload.get("severity"),
                group_id,
            ),
        )
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Incident group not found.")
    return {"status": "ok"}


@app.delete("/api/groups/{group_id}")
def delete_group(group_id: str, tenant: list[str] = Query(default=["all"])):
    normalize_tenants(tenant)
    validated_group_id(group_id)
    with get_db() as conn:
        if not _scoped_groups(conn, tenant, group_id):
            raise HTTPException(status_code=404, detail="Incident group not found in this scope.")
        conn.execute("DELETE FROM wazuh.analysis_groups WHERE id = %s", (group_id,))
    return {"status": "ok"}


@app.post("/api/groups/{group_id}/members")
def add_group_members(group_id: str, payload: dict[str, Any], tenant: list[str] = Query(default=["all"])):
    normalize_tenants(tenant)
    validated_group_id(group_id)
    with get_db() as conn:
        if not _scoped_groups(conn, tenant, group_id):
            raise HTTPException(status_code=404, detail="Incident group not found in this scope.")
        pks = _validate_membership(conn, payload.get("alert_pks", []), tenant)
        for pk in pks:
            conn.execute(
                "INSERT INTO wazuh.alert_group_members(alert_pk, group_id) VALUES(%s, %s) ON CONFLICT DO NOTHING",
                (pk, group_id),
            )
    return {"status": "ok"}


def _validate_membership(conn, values, tenant: str | list[str] | tuple[str, ...] | None) -> list[int]:
    if not isinstance(values, list):
        raise HTTPException(status_code=422, detail="alert_pks must be a list.")
    try:
        pks = positive_ids(values)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if pks:
        where = "id = ANY(%s)"
        params: list[Any] = [pks]
        tenant_sql, tenant_params = tenant_clause("a", tenant)
        if tenant_sql:
            where += " AND " + tenant_sql
            params.extend(tenant_params)
        rows = conn.execute(f"SELECT a.id FROM wazuh.alerts a WHERE {where}", params).fetchall()
        if {row["id"] for row in rows} != set(pks):
            raise HTTPException(status_code=400, detail="Selected alerts are missing or outside the active tenant.")
    return pks


@app.delete("/api/groups/{group_id}/members/{alert_pk}")
def remove_group_member(group_id: str, alert_pk: int, tenant: list[str] = Query(default=["all"])):
    validated_group_id(group_id)
    with get_db() as conn:
        _validate_membership(conn, [alert_pk], tenant)
        groups = _scoped_groups(conn, tenant, group_id)
        if not groups:
            raise HTTPException(status_code=404, detail="Incident group not found in this scope.")
        if normalize_tenants(tenant) and alert_pk in groups[0]["alert_pks"] and groups[0]["alert_count"] <= 1:
            raise HTTPException(status_code=409, detail="Bukti terakhir tenant tidak dapat dilepas dari scope ini. Gunakan Semua tenant untuk meninjau kasus sebelum melepasnya.")
        conn.execute(
            "DELETE FROM wazuh.alert_group_members WHERE group_id = %s AND alert_pk = %s",
            (group_id, alert_pk),
        )
    return {"status": "ok"}


@app.get("/api/stats")
def get_stats(
    pivot_by: str = "rule_description",
    secondary_pivot: str | None = None,
    exclude_facet: str = "",
    exclude_facet_value: str = "", 
    compare: str = "",
    metric: str = "alerts",
    top_n: int = 8,
    chart: str = "bar",
    chart_scale: str = "normal",
    bucket: str = "auto",
    pattern: str = "",
    other_details: bool = False,
    q: str = "",
    tenant: list[str] = Query(default=["all"]),
    status: str = "all",
    group_id: str | None = None,
    filter_preset: str = "",
    review_status: str = "all",
    time_preset: str = "",
    time_from: str = "",
    time_to: str = "",
    facet: str = "",
    facet_value: str = "",
    secondary_facet: str = "",
    secondary_facet_value: str = "",
    exclude_pivot: str | None = None,
    hide_reviewed: bool = False,
    filters: str = "",
    reviewed_from: str = "",
    reviewed_to: str = "",
):
    if pivot_by not in PIVOT_DEFINITIONS:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid pivot_by '{pivot_by}'. Supported pivots: {', '.join(PIVOT_DEFINITIONS.keys())}",
        )
    if secondary_pivot and (secondary_pivot not in PIVOT_DEFINITIONS or secondary_pivot == "pattern"):
        raise HTTPException(
            status_code=422,
            detail=f"Invalid secondary_pivot '{secondary_pivot}'. Must be a supported non-pattern dimension.",
        )
    if metric not in {"alerts", "events"}:
        raise HTTPException(status_code=422, detail="metric must be 'alerts' or 'events'.")
    if not (1 <= top_n <= 1000):
        raise HTTPException(status_code=422, detail="top_n must be between 1 and 1000.")
    if bucket not in {"auto", "minute", "hour", "day"}:
        raise HTTPException(status_code=422, detail="bucket must be one of: auto, minute, hour, day.")
    if pivot_by == "pattern":
        pat = pattern.strip()
        if not (1 <= len(pat) <= 120):
            raise HTTPException(
                status_code=422,
                detail="pattern parameter (1-120 chars) is required when pivot_by is 'pattern'.",
            )
    if time_from and time_to and str(time_from).strip() > str(time_to).strip():
        raise HTTPException(status_code=422, detail="time_from must be before or equal to time_to.")

    where_sql, base_params = alert_where(
        q=q,
        tenant=tenant,
        status=status,
        group_id=group_id,
        filter_preset=filter_preset,
        review_status=review_status,
        time_preset=time_preset,
        time_from=time_from,
        time_to=time_to,
        facet=facet,
        facet_value=facet_value,
        secondary_facet=secondary_facet,
        secondary_facet_value=secondary_facet_value,
        exclude_facet=exclude_facet,
        exclude_facet_value=exclude_facet_value,
        filters=filters,
        reviewed_from=reviewed_from,
        reviewed_to=reviewed_to,
    )
    parent_where_sql, parent_base_params = alert_where(
        q=q,
        tenant=tenant,
        status=status,
        group_id=group_id,
        filter_preset=filter_preset,
        review_status=review_status,
        time_preset=time_preset,
        time_from=time_from,
        time_to=time_to,
        facet=facet,
        facet_value=facet_value,
        filters=filters,
        reviewed_from=reviewed_from,
        reviewed_to=reviewed_to,
    )
    workspace_where_sql, workspace_base_params = alert_where(
        q=q,
        tenant=tenant,
        status=status,
        group_id=group_id,
        filter_preset=filter_preset,
        review_status=review_status,
        time_preset=time_preset,
        time_from=time_from,
        time_to=time_to,
        filters=filters,
        reviewed_from=reviewed_from,
        reviewed_to=reviewed_to,
    )

    metric_expr = "COUNT(*)" if metric == "alerts" else "COALESCE(SUM(COALESCE(a.hit_count, 1)), 0)"

    if pivot_by == "pattern":
        dim_sql = (
            "CASE WHEN ("
            "a.description ILIKE %s OR a.raw::text ILIKE %s OR a.parsed_details::text ILIKE %s"
            ") THEN 'Cocok pola' ELSE 'Tidak cocok pola' END"
        )
        dim_params = [f"%{pattern.strip()}%"] * 3
    else:
        dim_sql = PIVOT_DEFINITIONS[pivot_by]["sql"]
        dim_params = []

    with get_db() as conn:
        exclusion_doc = _exclusion_document(conn)
        where_sql, base_params = with_exclusions(where_sql, base_params, exclusion_doc)
        parent_where_sql, parent_base_params = with_exclusions(parent_where_sql, parent_base_params, exclusion_doc)
        workspace_where_sql, workspace_base_params = with_exclusions(workspace_where_sql, workspace_base_params, exclusion_doc)
        total_row = conn.execute(
            f"""SELECT COUNT(*) AS total_alerts,
                       COALESCE(SUM(COALESCE(a.hit_count, 1)), 0) AS total_events
                FROM wazuh.alerts a {where_sql}""",
            base_params,
        ).fetchone()
        total_alerts = int(total_row["total_alerts"] or 0)
        total_events = int(total_row["total_events"] or 0)
        total = total_alerts if metric == "alerts" else total_events

        fetch_limit = min(max(top_n, 1), 1000)
        grouped_sql = f"""
            SELECT {dim_sql} AS k, {metric_expr} AS n
            FROM wazuh.alerts a {where_sql}
            GROUP BY 1
            ORDER BY 2 DESC, 1 ASC
            LIMIT %s
        """
        top_rows = conn.execute(grouped_sql, dim_params + base_params + [fetch_limit]).fetchall()

        items = []
        for r in top_rows:
            cnt = int(r["n"] or 0)
            pct = round((cnt / total * 100.0), 2) if total > 0 else 0.0
            items.append({
                "key": str(r["k"] if r["k"] is not None else "Tidak tersedia"),
                "count": cnt,
                "percentage": pct,
            })

        other_count = 0
        other_percentage = 0.0
        other_items = []

        secondary_distribution = None
        secondary_breakdown = None

        parent_total = None
        workspace_total = None
        primary_percentage_of_total = None
        secondary_percentage_of_parent = None
        secondary_percentage_of_total = None

        if facet and facet_value:
            p_row = conn.execute(
                f"""SELECT COUNT(*) AS total_alerts,
                           COALESCE(SUM(COALESCE(a.hit_count, 1)), 0) AS total_events
                    FROM wazuh.alerts a {parent_where_sql}""",
                parent_base_params,
            ).fetchone()
            parent_total = int(p_row["total_alerts"] or 0) if metric == "alerts" else int(p_row["total_events"] or 0)

            w_row = conn.execute(
                f"""SELECT COUNT(*) AS total_alerts,
                           COALESCE(SUM(COALESCE(a.hit_count, 1)), 0) AS total_events
                    FROM wazuh.alerts a {workspace_where_sql}""",
                workspace_base_params,
            ).fetchone()
            workspace_total = int(w_row["total_alerts"] or 0) if metric == "alerts" else int(w_row["total_events"] or 0)

            if workspace_total > 0:
                primary_percentage_of_total = round((parent_total / workspace_total * 100.0), 2)
            else:
                primary_percentage_of_total = 0.0

            if secondary_facet and secondary_facet_value:
                if parent_total > 0:
                    secondary_percentage_of_parent = round((total / parent_total * 100.0), 2)
                else:
                    secondary_percentage_of_parent = 0.0

                if workspace_total > 0:
                    secondary_percentage_of_total = round((total / workspace_total * 100.0), 2)
                else:
                    secondary_percentage_of_total = 0.0

        if secondary_pivot:
            sec_dim_sql = PIVOT_DEFINITIONS[secondary_pivot]["sql"]
            sec_sql = f"""
                SELECT {dim_sql} AS k1, {sec_dim_sql} AS k2, {metric_expr} AS n
                FROM wazuh.alerts a {where_sql}
                GROUP BY 1, 2
                ORDER BY 3 DESC
                LIMIT 500
            """
            sec_rows = conn.execute(sec_sql, dim_params + base_params).fetchall()
            sec_dist: dict[str, list[dict[str, Any]]] = {}
            for r in sec_rows:
                k1 = str(r["k1"] if r["k1"] is not None else "Tidak tersedia")
                k2 = str(r["k2"] if r["k2"] is not None else "Tidak tersedia")
                if k1 not in sec_dist:
                    sec_dist[k1] = []
                sec_dist[k1].append({"key": k2, "count": int(r["n"] or 0)})
            secondary_distribution = sec_dist

            # When primary facet is active, secondary_breakdown provides the complete breakdown of secondary dimension
            # within the parent facet scope (using parent_where_sql so all sub-categories remain visible)
            if facet and facet_value:
                sec_break_sql = f"""
                    SELECT {sec_dim_sql} AS k, {metric_expr} AS n
                    FROM wazuh.alerts a {parent_where_sql}
                    GROUP BY 1
                    ORDER BY 2 DESC, 1 ASC
                    LIMIT 500
                """
                sec_break_rows = conn.execute(sec_break_sql, parent_base_params).fetchall()
                base_calc_total = parent_total if (parent_total and parent_total > 0) else total
                break_items = []
                for r in sec_break_rows:
                    cnt = int(r["n"] or 0)
                    pct = round((cnt / base_calc_total * 100.0), 2) if base_calc_total > 0 else 0.0
                    break_items.append({
                        "key": str(r["k"] if r["k"] is not None else "Tidak tersedia"),
                        "count": cnt,
                        "percentage": pct,
                    })
                secondary_breakdown = break_items

        granularity = bucket
        if granularity == "auto":
            time_bounds = conn.execute(
                f"""SELECT MIN(NULLIF(a.timestamp, '')) AS earliest,
                           MAX(NULLIF(a.timestamp, '')) AS latest
                    FROM wazuh.alerts a {where_sql}""",
                base_params,
            ).fetchone()
            earliest = time_bounds["earliest"] if time_bounds else None
            latest = time_bounds["latest"] if time_bounds else None
            if earliest and latest and len(earliest) >= 10 and len(latest) >= 10:
                if earliest[:10] == latest[:10]:
                    granularity = "minute"
                elif earliest[:7] == latest[:7]:
                    granularity = "hour"
                else:
                    granularity = "day"
            else:
                granularity = "hour"

        if granularity == "minute":
            bucket_sql = "substr(a.timestamp, 1, 16) || ':00Z'"
        elif granularity == "day":
            bucket_sql = "substr(a.timestamp, 1, 10)"
        else:
            bucket_sql = "substr(a.timestamp, 1, 13) || ':00:00Z'"

        ts_where = (where_sql + " AND " if where_sql else "WHERE ") + "(a.timestamp IS NOT NULL AND a.timestamp != '')"
        ts_sql = f"""
            SELECT {bucket_sql} AS b, {dim_sql} AS k, {metric_expr} AS n
            FROM wazuh.alerts a {ts_where}
            GROUP BY 1, 2
            ORDER BY 1 ASC
        """
        ts_rows = conn.execute(ts_sql, dim_params + base_params).fetchall()

        top_keys = [it["key"] for it in items]
        buckets_dict: dict[str, dict[str, Any]] = {}
        for r in ts_rows:
            b_key = str(r["b"])
            k_key = str(r["k"] if r["k"] is not None else "Tidak tersedia")
            cnt = int(r["n"] or 0)
            if b_key not in buckets_dict:
                buckets_dict[b_key] = {
                    "bucket": b_key,
                    "total": 0,
                    "series": {tk: 0 for tk in top_keys},
                    "above_average": False,
                }
            buckets_dict[b_key]["total"] += cnt
            if k_key in top_keys:
                buckets_dict[b_key]["series"][k_key] += cnt

        time_series = list(buckets_dict.values())
        if time_series:
            avg_val = sum(b["total"] for b in time_series) / len(time_series)
            threshold = avg_val * 1.5
            for b in time_series:
                b["above_average"] = bool(b["total"] > threshold and b["total"] > 1)

    res_data = {
        "pivot_by": pivot_by,
        "secondary_pivot": secondary_pivot,
        "secondary_distribution": secondary_distribution,
        "secondary_breakdown": secondary_breakdown,
        "metric": metric,
        "total": total,
        "total_alerts": total_alerts,
        "total_events": total_events,
        "top_n": top_n,
        "granularity": granularity,
        "items": items,
        "other_count": other_count,
        "other_percentage": other_percentage,
        "other_items": other_items,
        "time_series": time_series,
        "scope": {
            "tenant": list(normalize_tenants(tenant)),
            "q": q,
            "status": status,
            "group_id": group_id,
            "filter_preset": filter_preset,
            "review_status": review_status,
            "time_from": time_from,
            "time_to": time_to,
            "facet": facet,
            "facet_value": facet_value,
            "secondary_facet": secondary_facet,
            "secondary_facet_value": secondary_facet_value,
        },
    }
    if parent_total is not None:
        res_data["parent_total"] = parent_total
    if workspace_total is not None:
        res_data["workspace_total"] = workspace_total
    if primary_percentage_of_total is not None:
        res_data["primary_percentage_of_total"] = primary_percentage_of_total
    if secondary_percentage_of_parent is not None:
        res_data["secondary_percentage_of_parent"] = secondary_percentage_of_parent
    if secondary_percentage_of_total is not None:
        res_data["secondary_percentage_of_total"] = secondary_percentage_of_total
    return res_data


@app.post("/api/stats/facet-alert-ids")
def get_facet_alert_ids(payload: dict[str, Any]):
    tenant = payload.get("tenant", ["all"])
    if isinstance(tenant, str):
        tenant = [tenant]
    q = payload.get("q", "")
    status = payload.get("status", "all")
    group_id = payload.get("group_id")
    filter_preset = payload.get("filter_preset", "")
    review_status = payload.get("review_status", "all")
    time_preset = payload.get("time_preset", "")
    time_from = payload.get("time_from", "")
    time_to = payload.get("time_to", "")
    facet = payload.get("facet", "")
    facet_value = payload.get("facet_value", "")
    secondary_facet = payload.get("secondary_facet", "")
    secondary_facet_values = payload.get("secondary_facet_values", [])
    spotter_mode = str(payload.get("spotter_mode", "all")).strip().lower()
    filters = payload.get("filters", "")
    reviewed_from = payload.get("reviewed_from", "")
    reviewed_to = payload.get("reviewed_to", "")

    if not isinstance(secondary_facet_values, list):
        raise HTTPException(status_code=422, detail="secondary_facet_values must be a list.")

    where_sql, params = alert_where(
        q=q, tenant=tenant, status=status, group_id=group_id,
        filter_preset=filter_preset, review_status=review_status,
        time_preset=time_preset, time_from=time_from, time_to=time_to,
        facet=facet, facet_value=facet_value, filters=filters,
        reviewed_from=reviewed_from, reviewed_to=reviewed_to,
    )

    if secondary_facet and secondary_facet_values:
        if secondary_facet not in FACET_COLUMNS:
            raise HTTPException(status_code=422, detail="Invalid secondary_facet.")
        sec_col = FACET_COLUMNS[secondary_facet]
        where_sql += (" AND " if where_sql else "WHERE ") + f"{sec_col} = ANY(%s)"
        params.append(secondary_facet_values)

    with get_db() as conn:
        where_sql, params = with_exclusions(where_sql, params, _exclusion_document(conn))
        rows = conn.execute(
            f"SELECT a.id, a.data, a.parsed_details, a.raw FROM wazuh.alerts a {where_sql} ORDER BY a.rule_id ASC NULLS LAST, a.timestamp ASC NULLS LAST, a.id ASC LIMIT 10000",
            params,
        ).fetchall()

    filtered_ids = []
    for r in rows:
        row_dict = dict(r)
        if spotter_mode == "malicious":
            if is_malicious_alert_record(row_dict):
                filtered_ids.append(int(r["id"]))
        elif spotter_mode == "benign":
            if not is_malicious_alert_record(row_dict):
                filtered_ids.append(int(r["id"]))
        else:
            filtered_ids.append(int(r["id"]))

    return {
        "alert_pks": filtered_ids,
        "total": len(filtered_ids),
        "spotter_mode": spotter_mode,
        "raw_total": len(rows),
    }


@app.get("/api/triage/summary")
def triage_summary(
    q: str = "",
    secondary_facet: str = "",
    secondary_facet_value: str = "",
    tenant: list[str] = Query(default=["all"]),
    status: str = "all",
    group_id: str | None = None,
    filter_preset: str = "",
    review_status: str = "all",
    time_preset: str = "",
    time_from: str = "",
    time_to: str = "",
    facet: str = "",
    facet_value: str = "",
    alert_ids: str = "",
    filters: str = "",
    reviewed_from: str = "",
    reviewed_to: str = "",
):
    where_sql, params = alert_where(
        q=q,
        tenant=tenant,
        status=status,
        group_id=group_id,
        filter_preset=filter_preset,
        review_status=review_status,
        time_preset=time_preset,
        time_from=time_from,
        time_to=time_to,
        facet=facet,
        facet_value=facet_value,
        secondary_facet=secondary_facet,
        secondary_facet_value=secondary_facet_value,
        alert_ids=alert_ids,
        filters=filters,
        reviewed_from=reviewed_from,
        reviewed_to=reviewed_to,
    )

    with get_db() as conn:
        if not (alert_ids and str(alert_ids).strip()):
            where_sql, params = with_exclusions(where_sql, params, _exclusion_document(conn))
        counts = conn.execute(
            f"""SELECT COUNT(*) AS alerts,
                       COALESCE(SUM(COALESCE(a.hit_count, 1)), 0) AS events,
                       COUNT(DISTINCT NULLIF(a.source_ip, '')) AS unique_source_ips,
                       COUNT(DISTINCT NULLIF(a.agent_name, '')) AS unique_agents,
                       COUNT(*) FILTER (WHERE a.rule_level >= 15) AS sev_critical,
                       COUNT(*) FILTER (WHERE a.rule_level >= 12 AND a.rule_level < 15) AS sev_high,
                       COUNT(*) FILTER (WHERE a.rule_level >= 7 AND a.rule_level < 12) AS sev_medium,
                       COUNT(*) FILTER (WHERE a.rule_level < 7) AS sev_low,
                       MIN(NULLIF(a.timestamp, '')) AS earliest,
                       MAX(NULLIF(a.timestamp, '')) AS latest
                FROM wazuh.alerts a {where_sql}""",
            params,
        ).fetchone()

        sev_map = {
            "critical": int(counts["sev_critical"] or 0) if counts else 0,
            "high": int(counts["sev_high"] or 0) if counts else 0,
            "medium": int(counts["sev_medium"] or 0) if counts else 0,
            "low": int(counts["sev_low"] or 0) if counts else 0,
        }

        group_row = conn.execute(
            f"""SELECT COUNT(DISTINCT m.group_id) AS n
                FROM wazuh.alert_group_members m
                JOIN wazuh.alerts a ON a.id = m.alert_pk
                {where_sql}""",
            params,
        ).fetchone()
        incident_cases = int(group_row["n"] or 0) if group_row else 0

        top_rule_row = conn.execute(
            f"""SELECT
                    COALESCE(NULLIF(a.rule_id, ''), '-') AS rule_id,
                    COALESCE(NULLIF(a.description, ''), 'Wazuh Alert') AS description,
                    COUNT(*) AS n
                FROM wazuh.alerts a {where_sql}
                GROUP BY 1, 2
                ORDER BY 3 DESC, 1 ASC
                LIMIT 1""",
            params,
        ).fetchone()

        top_rule = None
        if top_rule_row and int(top_rule_row["n"] or 0) > 0:
            top_rule = {
                "rule_id": str(top_rule_row["rule_id"]),
                "description": str(top_rule_row["description"]),
                "count": int(top_rule_row["n"]),
            }

    return {
        "alerts": int(counts["alerts"] or 0) if counts else 0,
        "events": int(counts["events"] or 0) if counts else 0,
        "unique_source_ips": int(counts["unique_source_ips"] or 0) if counts else 0,
        "unique_agents": int(counts["unique_agents"] or 0) if counts else 0,
        "severity": sev_map,
        "incident_cases": incident_cases,
        "time_range": {
            "earliest": counts["earliest"] if counts else None,
            "latest": counts["latest"] if counts else None,
        },
        "top_rule": top_rule,
    }


@app.get("/api/reviews/activity")
def review_activity(
    tenant: list[str] = Query(default=["all"]),
    days: int = 14,
    tz_offset_minutes: int = 0,
):
    """Reviewed-alert counts per local calendar day for the Triage activity panel.

    ``tz_offset_minutes`` is the client's UTC offset in minutes (WIB = 420), so
    "today" follows the analyst's wall clock rather than the server's UTC date.
    """
    if not (1 <= days <= 90):
        raise HTTPException(status_code=422, detail="days must be between 1 and 90.")
    offset = max(-840, min(840, int(tz_offset_minutes or 0)))
    window = max(days, 30)
    now_local = datetime.now(timezone.utc) + timedelta(minutes=offset)
    today = now_local.date()
    start_date = today - timedelta(days=window - 1)
    start_local = datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc)
    since_utc = (start_local - timedelta(minutes=offset)).isoformat()

    where = "a.reviewed_at IS NOT NULL AND a.reviewed_at >= %s"
    params: list[Any] = [since_utc]
    tenant_sql, tenant_params = tenant_clause("a", tenant)
    if tenant_sql:
        where += " AND " + tenant_sql
        params.extend(tenant_params)

    with get_db() as conn:
        rows = conn.execute(
            f"SELECT a.reviewed_at FROM wazuh.alerts a WHERE {where}",
            params,
        ).fetchall()
        reviewed_row = conn.execute(
            f"SELECT COUNT(*) AS n FROM wazuh.alerts a WHERE a.reviewed_at IS NOT NULL"
            + (f" AND {tenant_sql}" if tenant_sql else ""),
            tenant_params,
        ).fetchone()
    total_reviewed = int(reviewed_row["n"] or 0) if reviewed_row else 0

    counts: dict[str, int] = {}
    for row in rows:
        day = _review_local_date(row["reviewed_at"], offset)
        if day:
            counts[day] = counts.get(day, 0) + 1

    days_list = []
    for index in range(days):
        day = (today - timedelta(days=index)).isoformat()
        days_list.append({"date": day, "count": counts.get(day, 0)})
    last_7 = sum(item["count"] for item in days_list[:7]) if days >= 7 else sum(item["count"] for item in days_list)
    last_30 = sum(counts.get((today - timedelta(days=index)).isoformat(), 0) for index in range(min(30, window)))
    return {
        "days": days_list,
        "today": days_list[0]["count"],
        "last_7_days": last_7,
        "last_30_days": last_30,
        "total_reviewed": total_reviewed,
        "tz_offset_minutes": offset,
    }


def _review_local_date(value: Any, offset_minutes: int) -> str | None:
    """Return an ISO local date for a timestamp, tolerating text and datetime."""
    if value is None:
        return None
    if isinstance(value, datetime):
        moment = value
        if moment.tzinfo is None:
            moment = moment.replace(tzinfo=timezone.utc)
    else:
        text = str(value).strip()
        if not text:
            return None
        try:
            moment = datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            return None
        if moment.tzinfo is None:
            moment = moment.replace(tzinfo=timezone.utc)
    return (moment + timedelta(minutes=offset_minutes)).date().isoformat()


@app.get("/api/suggestions")
def get_suggestions(
    use_local_ai: bool = False, tenant: list[str] = Query(default=["all"]), q: str = "",
    review_status: str = "all", filter_preset: str = "", status: str = "all",
    group_id: str | None = None, time_from: str = "", time_to: str = "",
    filters: str = "", reviewed_from: str = "", reviewed_to: str = "",
):
    where, params = alert_where(
        tenant=tenant, q=q, review_status=review_status, filter_preset=filter_preset,
        status=status, group_id=group_id, time_from=time_from, time_to=time_to,
        filters=filters, reviewed_from=reviewed_from, reviewed_to=reviewed_to,
    )
    with get_db() as conn:
        where, params = with_exclusions(where, params, _exclusion_document(conn))
        rows = conn.execute(
            f"""SELECT a.id, a.alert_id, a.timestamp, a.tenant, a.agent_name, a.agent_ip, a.rule_id, a.rule_level,
                       a.description, a.rule_groups, a.decoder, a.location, a.source_ip, a.mitre_ids, a.cve,
                       a.log_signature, a.raw, a.parsed_details
                FROM wazuh.alerts a {where}
                ORDER BY a.timestamp DESC NULLS LAST, a.id DESC LIMIT 300""",
            params,
        ).fetchall()
    candidate_alerts = [{**r, "id": str(r["id"])} for r in rows]
    groups_list, mode, warning = suggestions_with_fallback(candidate_alerts, enabled=use_local_ai)
    return {"mode": mode, "warning": warning, "suggestions": groups_list}


@app.get("/api/realtime/count")
def api_realtime_count():
    """Count Wazuh alerts in the configured severity range without downloading or storing any alert."""
    with get_db() as conn:
        stored = load_settings(conn)
    wazuh = stored.get("wazuh", {})
    realtime = stored.get("realtime", {})
    if not wazuh.get("indexer_url"):
        raise HTTPException(status_code=400, detail="Wazuh Indexer belum dikonfigurasi di halaman Pengaturan.")
    min_level = int(realtime.get("min_rule_level") if realtime.get("min_rule_level") is not None else 7)
    raw_max = realtime.get("max_rule_level")
    max_level = int(raw_max) if raw_max is not None and str(raw_max).strip() != "" else None
    try:
        result = test_wazuh_connection(
            indexer_url=wazuh.get("indexer_url", ""),
            username=wazuh.get("username", ""),
            password=wazuh_password(stored),
            index_pattern=wazuh.get("index_pattern", "wazuh-alerts-*"),
            verify_tls=bool(wazuh.get("verify_tls", True)),
            min_rule_level=min_level,
            max_rule_level=max_level,
        )
    except ValueError as error:
        raise HTTPException(status_code=502, detail=str(error)) from None
    return {**result, "checked_at": datetime.now(timezone.utc).isoformat()}


@app.post("/api/realtime/pull")
def api_realtime_pull(payload: dict[str, Any] | None = Body(default=None)):
    """Pull alerts in the configured severity range from the Wazuh Indexer and ingest them into the active DB.

    A manual pull (``force: true``) always runs, regardless of whether the
    realtime monitor is enabled and regardless of the daily 24h gate. Scheduled
    pulls keep the daily gate. Never downloads more than the requested
    ``max_alerts`` documents per call (maximum 100000).
    """
    now = datetime.now(timezone.utc)
    with get_db() as conn:
        stored = load_settings(conn)
    wazuh = stored.get("wazuh", {})
    realtime = stored.get("realtime", {})
    if not wazuh.get("indexer_url"):
        raise HTTPException(status_code=400, detail="Wazuh Indexer belum dikonfigurasi di halaman Pengaturan.")

    stored_min = int(realtime.get("min_rule_level") if realtime.get("min_rule_level") is not None else 7)
    raw_stored_max = realtime.get("max_rule_level")
    stored_max = int(raw_stored_max) if raw_stored_max is not None and str(raw_stored_max).strip() != "" else None

    min_rule_level = stored_min
    max_rule_level = stored_max
    severity_overridden = False
    pull_size = int(realtime.get("max_alerts") or 500)
    custom_time_from = ""
    custom_time_to = ""
    custom_range = False
    custom_range_key = ""
    force_pull = False

    if isinstance(payload, dict):
        force_pull = bool(payload.get("force") or payload.get("manual"))
        if "min_rule_level" in payload and payload["min_rule_level"] is not None and str(payload["min_rule_level"]).strip() != "":
            try:
                min_rule_level = int(payload["min_rule_level"])
            except (TypeError, ValueError):
                raise HTTPException(status_code=400, detail="min_rule_level harus berupa angka.") from None
            if not 0 <= min_rule_level <= 16:
                raise HTTPException(status_code=400, detail="min_rule_level harus antara 0 dan 16.")
            severity_overridden = True
        if "max_rule_level" in payload:
            raw_max = payload.get("max_rule_level")
            if raw_max is None or str(raw_max).strip() == "":
                max_rule_level = None
            else:
                try:
                    max_rule_level = int(raw_max)
                except (TypeError, ValueError):
                    raise HTTPException(status_code=400, detail="max_rule_level harus berupa angka.") from None
                if not 0 <= max_rule_level <= 16 or max_rule_level < min_rule_level:
                    raise HTTPException(status_code=400, detail="max_rule_level tidak valid.")
            severity_overridden = True
        if "max_alerts" in payload and payload["max_alerts"] is not None and str(payload["max_alerts"]).strip() != "":
            try:
                pull_size = int(payload["max_alerts"])
            except (TypeError, ValueError):
                raise HTTPException(status_code=400, detail="max_alerts harus berupa angka.") from None
            if not 1 <= pull_size <= 100000:
                raise HTTPException(status_code=400, detail="max_alerts harus antara 1 dan 100000.")
        raw_from = str(payload.get("time_from") or payload.get("since") or "").strip()
        raw_to = str(payload.get("time_to") or payload.get("until") or "").strip()
        custom_range_key = str(payload.get("range_key") or "").strip()[:200]
        if raw_from:
            norm_from = _normalize_wazuh_timestamp(raw_from)
            if not _valid_timestamp(norm_from):
                raise HTTPException(
                    status_code=400,
                    detail="Format waktu mulai (time_from) tidak valid. Gunakan format DD/MM/YYYY HH.MM.SS atau pilih dari kalender.",
                )
            custom_time_from = norm_from
            custom_range = True
        if raw_to:
            norm_to = _normalize_wazuh_timestamp(raw_to)
            if not _valid_timestamp(norm_to):
                raise HTTPException(
                    status_code=400,
                    detail="Format waktu selesai (time_to) tidak valid. Gunakan format DD/MM/YYYY HH.MM.SS, 'now', atau pilih dari kalender.",
                )
            custom_time_to = norm_to
            custom_range = True

    severity_changed = severity_overridden and (min_rule_level, max_rule_level) != (stored_min, stored_max)

    mode = str(realtime.get("mode") or "interval")
    last_pull_at = "" if severity_changed else str(realtime.get("last_pull_at") or "").strip()
    if not custom_range and not force_pull and mode == "daily" and last_pull_at:
        try:
            last = datetime.fromisoformat(last_pull_at.replace("Z", "+00:00"))
            if last.tzinfo is None:
                last = last.replace(tzinfo=timezone.utc)
            elapsed = now - last
            if elapsed.total_seconds() < 24 * 3600:
                next_pull = last + timedelta(hours=24)
                return {
                    "status": "skipped",
                    "reason": "Pull harian hanya dijalankan sekali setiap 24 jam.",
                    "last_pull_at": last_pull_at,
                    "next_pull_at": next_pull.isoformat(),
                }
        except ValueError:
            pass  # Unparseable timestamp: treat as never pulled.

    effective_since = custom_time_from if custom_range else last_pull_at
    effective_until = custom_time_to if custom_range else ""

    # Range pulls are capped per call. Persist a search_after cursor for the same
    # range/severity so the next pull continues instead of refetching the newest
    # subset over and over.
    range_signature = ""
    resume_after: list[Any] | None = None
    stored_cursor = realtime.get("range_cursor")
    if custom_range:
        range_signature = custom_range_key and f"{custom_range_key}|{min_rule_level}|{max_rule_level}|{wazuh.get('index_pattern', 'wazuh-alerts-*')}"
        if not range_signature:
            range_signature = json.dumps(
                {
                    "since": effective_since,
                    "until": effective_until,
                    "min": min_rule_level,
                    "max": max_rule_level,
                    "pattern": wazuh.get("index_pattern", "wazuh-alerts-*"),
                },
                sort_keys=True,
            )
        if isinstance(stored_cursor, dict) and stored_cursor.get("signature") == range_signature:
            candidate_after = stored_cursor.get("search_after")
            if isinstance(candidate_after, list) and candidate_after:
                resume_after = candidate_after
    search_cursor: dict[str, Any] = {}

    try:
        docs = wazuh_search(
            indexer_url=wazuh.get("indexer_url", ""),
            username=wazuh.get("username", ""),
            password=wazuh_password(stored),
            index_pattern=wazuh.get("index_pattern", "wazuh-alerts-*"),
            verify_tls=bool(wazuh.get("verify_tls", True)),
            size=pull_size,
            since=effective_since,
            until=effective_until,
            min_rule_level=min_rule_level,
            max_rule_level=max_rule_level,
            search_after=resume_after,
            cursor=search_cursor,
        )
    except ValueError as error:
        raise HTTPException(status_code=502, detail=str(error)) from None

    has_more = bool(search_cursor.get("has_more"))
    next_after = search_cursor.get("search_after")

    inserted = 0
    deduplicated = 0
    with get_db() as conn:
        for item in docs:
            normalized = normalize_alert(item)
            did_insert, did_dedup = ingest_alert_with_dedup(conn, normalized)
            if did_insert:
                inserted += 1
            else:
                # Covers both signature merges and alerts that already exist by
                # alert_id/wazuh_id; both are "not new" for reporting purposes.
                deduplicated += 1
        # Persist the pull timestamp and any updated severity selection.
        if not custom_range or not custom_time_to:
            stored["realtime"]["last_pull_at"] = now.isoformat()
        if custom_range and has_more and isinstance(next_after, list) and next_after:
            stored["realtime"]["range_cursor"] = {
                "signature": range_signature,
                "search_after": next_after,
                "saved_at": now.isoformat(),
            }
            range_cursor_saved = True
        else:
            stored["realtime"].pop("range_cursor", None)
            range_cursor_saved = False
        stored["realtime"]["min_rule_level"] = min_rule_level
        stored["realtime"]["max_rule_level"] = max_rule_level
        save_settings(conn, stored)

    return {
        "status": "pulled",
        "pulled_at": now.isoformat(),
        "searched": len(docs),
        "inserted": inserted,
        "deduplicated": deduplicated,
        "max_alerts": pull_size,
        # True when the indexer returned exactly the requested cap, meaning more
        # matching alerts may exist beyond this pull.
        "capped": len(docs) >= pull_size,
        "has_more": has_more,
        "resumed": bool(resume_after),
        "range_cursor_saved": range_cursor_saved,
        "min_rule_level": min_rule_level,
        "max_rule_level": max_rule_level,
        "time_from": effective_since,
        "time_to": effective_until or "now",
        "custom_range": custom_range,
        "index_pattern": wazuh.get("index_pattern", "wazuh-alerts-*"),
    }


@app.post("/api/alerts/pull")
def api_start_alert_pull(payload: dict[str, Any] | None = Body(default=None)):
    """Start a background Wazuh backfill job and return its progress handle."""
    data = payload if isinstance(payload, dict) else {}
    with get_db() as conn:
        stored = load_settings(conn)
    wazuh = stored.get("wazuh", {})
    if not wazuh.get("indexer_url"):
        raise HTTPException(status_code=400, detail="Wazuh Indexer belum dikonfigurasi di halaman Pengaturan.")

    realtime = stored.get("realtime", {})
    try:
        min_rule_level = int(data.get("min_rule_level") if data.get("min_rule_level") is not None else realtime.get("min_rule_level", 7))
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="min_rule_level harus berupa angka.") from None
    if not 0 <= min_rule_level <= 16:
        raise HTTPException(status_code=400, detail="min_rule_level harus antara 0 dan 16.")

    raw_max = data.get("max_rule_level", realtime.get("max_rule_level"))
    max_rule_level: int | None = None
    if raw_max is not None and str(raw_max).strip() != "":
        try:
            max_rule_level = int(raw_max)
        except (TypeError, ValueError):
            raise HTTPException(status_code=400, detail="max_rule_level harus berupa angka.") from None
        if not 0 <= max_rule_level <= 16 or max_rule_level < min_rule_level:
            raise HTTPException(status_code=400, detail="max_rule_level tidak valid.")

    raw_from = str(data.get("time_from") or "").strip()
    raw_to = str(data.get("time_to") or "").strip()
    if not raw_from and not data.get("all_time"):
        raw_from = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
    if raw_from:
        norm_from = _normalize_wazuh_timestamp(raw_from)
        if not _valid_timestamp(norm_from):
            raise HTTPException(status_code=400, detail="Format waktu mulai (time_from) tidak valid.")
        raw_from = norm_from
    if raw_to:
        norm_to = _normalize_wazuh_timestamp(raw_to)
        if not _valid_timestamp(norm_to):
            raise HTTPException(status_code=400, detail="Format waktu selesai (time_to) tidak valid.")
        raw_to = norm_to

    config = {
        "indexer_url": wazuh.get("indexer_url", ""),
        "username": wazuh.get("username", ""),
        "password": wazuh_password(stored),
        "index_pattern": wazuh.get("index_pattern", "wazuh-alerts-*"),
        "verify_tls": bool(wazuh.get("verify_tls", True)),
        "time_from": raw_from,
        "time_to": raw_to,
        "min_rule_level": min_rule_level,
        "max_rule_level": max_rule_level,
        "max_docs": data.get("max_docs", 100000),
        "page_size": data.get("page_size", 2000),
        "chunk_days": data.get("chunk_days", 1),
    }
    try:
        job_id = start_pull_job(config)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from None
    return {"job": get_job(job_id)}


@app.get("/api/alerts/pull/{job_id}")
def api_alert_pull_status(job_id: str):
    job = get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job pengambilan alert tidak ditemukan atau sudah kedaluwarsa.")
    return {"job": job}


@app.post("/api/alerts/pull/{job_id}/cancel")
def api_alert_pull_cancel(job_id: str):
    job = cancel_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job pengambilan alert tidak ditemukan atau sudah kedaluwarsa.")
    return {"job": job}


@app.post("/api/ai/test")
def api_ai_test(payload: dict[str, Any]):
    with get_db() as conn:
        stored = load_settings(conn)
    ai = stored.get("ai", {})
    base_url = str(payload.get("base_url") or ai.get("base_url") or "http://127.0.0.1:11434").strip()
    model = str(payload.get("model") or ai.get("model") or "").strip()
    if not model:
        raise HTTPException(status_code=400, detail="Model AI belum diatur.")
    try:
        return test_ollama(base_url=base_url, model=model)
    except ValueError as error:
        raise HTTPException(status_code=502, detail=str(error)) from None


def _build_ai_triage_where(
    tenant: Any,
    review_status: str,
    min_rule_level: int,
    max_rule_level: int | None,
) -> tuple[str, list[Any]]:
    where, params = alert_where(tenant=tenant, review_status=review_status)
    level_clause = "a.rule_level >= %s"
    level_params: list[Any] = [min_rule_level]
    if max_rule_level is not None:
        level_clause += " AND a.rule_level <= %s"
        level_params.append(max_rule_level)
    if where:
        where = f"{where} AND {level_clause}"
    else:
        where = f"WHERE {level_clause}"
    return where, list(params) + level_params


def _find_matching_open_ai_group(
    conn,
    *,
    title: str,
    group_tenant: str,
    group_win_key: str,
) -> str | None:
    """Find an open AI incident group in the same tenant and 17:00 WIB cutoff window."""
    candidates = conn.execute(
        """SELECT id, title, created_at
           FROM wazuh.analysis_groups
           WHERE source = 'ai' AND status != 'closed' AND title = %s
           ORDER BY created_at DESC""",
        (title,),
    ).fetchall()
    for cand in candidates:
        cid = cand["id"]
        members = conn.execute(
            """SELECT a.id, a.tenant, a.timestamp
               FROM wazuh.alert_group_members m
               JOIN wazuh.alerts a ON a.id = m.alert_pk
               WHERE m.group_id = %s""",
            (cid,),
        ).fetchall()
        if not members:
            continue
        member_tenants = {str(m["tenant"] or "Default") for m in members}
        if member_tenants != {group_tenant}:
            continue
        member_windows = {wib_window_key(m.get("timestamp")) for m in members if wib_window_key(m.get("timestamp"))}
        cand_win_key = next(iter(member_windows), "") or wib_window_key(cand.get("created_at"))
        if group_win_key and cand_win_key and group_win_key != cand_win_key:
            continue
        return str(cid)
    return None


def _sync_triage_groups_with_saved_incidents(
    conn,
    groups: list[dict[str, Any]],
    alerts_by_id: dict[str, dict[str, Any]],
) -> None:
    """If an open AI incident group already exists in the same 17:00 WIB window, auto-append new alerts."""
    for group in groups:
        if not isinstance(group, dict):
            continue
        ids = [str(aid) for aid in (group.get("alert_ids") or []) if str(aid) in alerts_by_id]
        pks = [int(aid) for aid in ids if aid.isdigit()]
        if not pks:
            continue
        first_alert = alerts_by_id[ids[0]]
        group_tenant = str(group.get("tenant") or first_alert.get("tenant") or "Default").strip() or "Default"
        group_win_key = str(group.get("window_key") or wib_window_key(first_alert.get("timestamp")) or "")
        title = str(group.get("title") or "").strip()[:200]
        if not title:
            continue
        existing_id = _find_matching_open_ai_group(
            conn,
            title=title,
            group_tenant=group_tenant,
            group_win_key=group_win_key,
        )
        if existing_id:
            for pk in pks:
                conn.execute(
                    "INSERT INTO wazuh.alert_group_members(alert_pk, group_id) VALUES(%s, %s) ON CONFLICT DO NOTHING",
                    (pk, existing_id),
                )
            conn.execute(
                "UPDATE wazuh.analysis_groups SET updated_at = now() WHERE id = %s",
                (existing_id,),
            )
            group["saved_group_id"] = existing_id


@app.get("/api/ai/triage")
def api_get_ai_triage(tenant: list[str] = Query(None)):
    """Return the persisted AI triage state, automatically merging any new alerts within the 17:00 WIB window."""
    norm_tenants = list(normalize_tenants(tenant)) or ["all"]
    state_key = get_triage_state_key(norm_tenants)
    with get_db() as conn:
        state = load_document(conn, state_key, None)
        if state is None and state_key != AI_TRIAGE_STATE_KEY:
             # Fallback to global state if specific tenant state not found
             state = load_document(conn, AI_TRIAGE_STATE_KEY, None)
        if not isinstance(state, dict) or not isinstance(state.get("options"), dict):
            return {"saved": False, "result": None}
        options = state["options"]
        tenant = options.get("tenant") or ["all"]
        try:
            limit = max(1, min(5000, int(options.get("limit") or 40)))
            min_rule_level = max(0, min(16, int(options.get("min_rule_level") if options.get("min_rule_level") is not None else 7)))
        except (TypeError, ValueError):
            limit, min_rule_level = 40, 7
        raw_max = options.get("max_rule_level")
        max_rule_level = int(raw_max) if raw_max is not None and str(raw_max).strip() != "" else None
        review_status = str(options.get("review_status") or "unreviewed")
        group_by = str(options.get("group_by") or "rule_description")
        if group_by not in {"host_rule", "rule_description"}:
            group_by = "rule_description"

        saved_ids = [int(aid) for aid in (state.get("alert_ids") or []) if str(aid).isdigit()]
        existing_rows: list[dict[str, Any]] = []
        if saved_ids:
            t_clause, t_params = tenant_clause("a", tenant)
            id_where = f"WHERE a.id = ANY(%s){f' AND {t_clause}' if t_clause else ''}"
            existing_rows = conn.execute(
                f"""SELECT a.id, a.alert_id, a.timestamp, a.tenant, a.agent_name, a.agent_ip,
                           a.rule_id, a.rule_level, a.description, a.rule_groups, a.source_ip,
                           a.mitre_ids, a.cve, a.hit_count, a.log_signature, a.parsed_details,
                           a.data, COALESCE(a.raw->>'full_log', '') AS full_log
                    FROM wazuh.alerts a {id_where}
                    ORDER BY a.rule_level DESC NULLS LAST, a.timestamp DESC NULLS LAST, a.id DESC""",
                [saved_ids, *t_params],
            ).fetchall()

        where, where_params = _build_ai_triage_where(tenant, review_status, min_rule_level, max_rule_level)
        where, where_params = with_exclusions(where, where_params, _exclusion_document(conn))
        candidate_rows = conn.execute(
            f"""SELECT a.id, a.alert_id, a.timestamp, a.tenant, a.agent_name, a.agent_ip,
                       a.rule_id, a.rule_level, a.description, a.rule_groups, a.source_ip,
                       a.mitre_ids, a.cve, a.hit_count, a.log_signature, a.parsed_details,
                       a.data, COALESCE(a.raw->>'full_log', '') AS full_log
                FROM wazuh.alerts a {where}
                ORDER BY a.rule_level DESC NULLS LAST, a.timestamp DESC NULLS LAST, a.id DESC
                LIMIT %s""",
            [*where_params, limit],
        ).fetchall()

        existing_map = {str(r["id"]): {**r, "id": str(r["id"])} for r in existing_rows}
        new_alerts: list[dict[str, Any]] = []
        for r in candidate_rows:
            aid = str(r["id"])
            record = {**r, "id": aid}
            if aid not in existing_map:
                existing_map[aid] = record
                new_alerts.append(record)

        all_alerts = list(existing_map.values())
        stored_settings = load_settings(conn)
        ai = stored_settings.get("ai", {})
        saved_groups = state.get("groups") if isinstance(state.get("groups"), list) else []
        mode = str(state.get("mode") or "local_rules")
        warning = state.get("warning")

        if new_alerts:
            inc_groups, inc_mode, inc_warn = triage_with_fallback(
                new_alerts,
                enabled=bool(ai.get("enabled")),
                model=str(ai.get("model") or ""),
                base_url=str(ai.get("base_url") or "http://127.0.0.1:11434"),
                timeout=float(ai.get("timeout_seconds") or 90),
                group_by=group_by,
            )
            groups = merge_triage_groups(saved_groups, inc_groups, existing_map)
            mode = inc_mode
            warning = inc_warn or warning
        else:
            groups = merge_triage_groups(saved_groups, [], existing_map)

        _sync_triage_groups_with_saved_incidents(conn, groups, existing_map)
        final_ids = [aid for g in groups for aid in (g.get("alert_ids") or []) if aid in existing_map]
        final_ids_set = set(final_ids)
        final_alerts = [a for a in all_alerts if a["id"] in final_ids_set] or all_alerts

        updated_state = {
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "window_key": current_wib_window_key(),
            "options": {
                "tenant": list(normalize_tenants(tenant)) or ["all"],
                "limit": limit,
                "min_rule_level": min_rule_level,
                "max_rule_level": max_rule_level,
                "review_status": review_status,
                "group_by": group_by,
            },
            "mode": mode,
            "warning": warning,
            "model": ai.get("model"),
            "alert_ids": list(dict.fromkeys(a["id"] for a in final_alerts)),
            "groups": groups,
        }
        save_document(conn, get_triage_state_key(norm_tenants), updated_state)

    return {
        "saved": True,
        "options": updated_state["options"],
        "result": {
            "mode": mode,
            "warning": warning,
            "model": ai.get("model"),
            "alert_count": len(final_alerts),
            "min_rule_level": min_rule_level,
            "max_rule_level": max_rule_level,
            "group_by": group_by,
            "saved_at": updated_state["saved_at"],
            "window_key": updated_state["window_key"],
            "alerts": safe_alerts(final_alerts, limit=max(limit, len(final_alerts))),
            "groups": groups,
        },
    }


@app.post("/api/ai/triage")
def api_ai_triage(payload: dict[str, Any]):
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Payload AI triage tidak valid.")
    raw_limit = payload.get("limit")
    raw_min_level = payload.get("min_rule_level")
    try:
        limit = int(40 if raw_limit is None or str(raw_limit).strip() == "" else raw_limit)
        min_rule_level = int(7 if raw_min_level is None or str(raw_min_level).strip() == "" else raw_min_level)
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="limit dan min_rule_level harus berupa angka.") from None
    if not 1 <= limit <= 100000:
        raise HTTPException(status_code=400, detail="limit harus antara 1 dan 100000.")
    if not 0 <= min_rule_level <= 16:
        raise HTTPException(status_code=400, detail="min_rule_level harus antara 0 dan 16.")

    raw_max_level = payload.get("max_rule_level")
    max_rule_level: int | None = None
    if raw_max_level is not None and str(raw_max_level).strip() != "":
        try:
            max_rule_level = int(raw_max_level)
        except (TypeError, ValueError):
            raise HTTPException(status_code=400, detail="max_rule_level harus berupa angka.") from None
        if not 0 <= max_rule_level <= 16 or max_rule_level < min_rule_level:
            raise HTTPException(status_code=400, detail="max_rule_level tidak valid.")

    group_by = str(payload.get("group_by") or "host_rule").strip()
    if group_by not in {"host_rule", "rule_description"}:
        raise HTTPException(status_code=400, detail="group_by harus berupa 'host_rule' atau 'rule_description'.")

    tenant = payload.get("tenant") or ["all"]
    review_status = str(payload.get("review_status") or "unreviewed")
    norm_tenants = list(normalize_tenants(tenant)) or ["all"]
    where, where_params = _build_ai_triage_where(tenant, review_status, min_rule_level, max_rule_level)
    with get_db() as conn:
        where, where_params = with_exclusions(where, where_params, _exclusion_document(conn))
        query_params = list(where_params) + [limit]
        rows = conn.execute(
            f"""SELECT a.id, a.alert_id, a.timestamp, a.tenant, a.agent_name, a.agent_ip,
                       a.rule_id, a.rule_level, a.description, a.rule_groups, a.source_ip,
                       a.mitre_ids, a.cve, a.hit_count, a.log_signature, a.parsed_details,
                       a.data, COALESCE(a.raw->>'full_log', '') AS full_log
                FROM wazuh.alerts a {where}
                ORDER BY a.rule_level DESC NULLS LAST, a.timestamp DESC NULLS LAST, a.id DESC
                LIMIT %s""",
            query_params,
        ).fetchall()
        stored = load_settings(conn)
        prev_state = load_document(conn, AI_TRIAGE_STATE_KEY, None)

        alerts_map = {str(row["id"]): {**row, "id": str(row["id"])} for row in rows}
        same_scope = False
        prev_groups: list[dict[str, Any]] = []
        if isinstance(prev_state, dict) and isinstance(prev_state.get("options"), dict):
            prev_opts = prev_state["options"]
            same_scope = (
                (prev_opts.get("tenant") or ["all"]) == norm_tenants
                and prev_opts.get("min_rule_level") == min_rule_level
                and prev_opts.get("max_rule_level") == max_rule_level
                and str(prev_opts.get("review_status") or "unreviewed") == review_status
                and str(prev_opts.get("group_by") or "host_rule") == group_by
            )
            if same_scope:
                prev_groups = prev_state.get("groups") if isinstance(prev_state.get("groups"), list) else []
                missing_pks = [
                    int(aid) for aid in (prev_state.get("alert_ids") or [])
                    if str(aid).isdigit() and str(aid) not in alerts_map
                ]
                if missing_pks:
                    extra_rows = conn.execute(
                        f"""SELECT a.id, a.alert_id, a.timestamp, a.tenant, a.agent_name, a.agent_ip,
                                   a.rule_id, a.rule_level, a.description, a.rule_groups, a.source_ip,
                                   a.mitre_ids, a.cve, a.hit_count, a.log_signature, a.parsed_details,
                                   a.data, COALESCE(a.raw->>'full_log', '') AS full_log
                            FROM wazuh.alerts a {where} AND a.id = ANY(%s)""",
                        [*where_params, missing_pks],
                    ).fetchall()
                    for r in extra_rows:
                        alerts_map[str(r["id"])] = {**r, "id": str(r["id"])}

        alerts = list(alerts_map.values())
        ai = stored.get("ai", {})
        fresh_groups, mode, warning = triage_with_fallback(
            alerts,
            enabled=bool(ai.get("enabled")),
            model=str(ai.get("model") or ""),
            base_url=str(ai.get("base_url") or "http://127.0.0.1:11434"),
            timeout=float(ai.get("timeout_seconds") or 90),
            group_by=group_by,
        )
        if same_scope and prev_groups and mode == prev_state.get("mode"):
            groups = merge_triage_groups(prev_groups, fresh_groups, alerts_map)
        else:
            groups = fresh_groups

        _sync_triage_groups_with_saved_incidents(conn, groups, alerts_map)

        if not ai.get("enabled") and not warning:
            warning = "AI Triage belum diaktifkan di Pengaturan; hasil memakai heuristik lokal."

        saved_state = {
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "window_key": current_wib_window_key(),
            "options": {
                "tenant": norm_tenants,
                "limit": limit,
                "min_rule_level": min_rule_level,
                "max_rule_level": max_rule_level,
                "review_status": review_status,
                "group_by": group_by,
            },
            "mode": mode,
            "warning": warning,
            "model": ai.get("model"),
            "alert_ids": [a["id"] for a in alerts],
            "groups": groups,
        }
        save_document(conn, get_triage_state_key(norm_tenants), saved_state)

    return {
        "mode": mode,
        "warning": warning,
        "model": ai.get("model"),
        "alert_count": len(alerts),
        "min_rule_level": min_rule_level,
        "max_rule_level": max_rule_level,
        "group_by": group_by,
        "saved_at": saved_state["saved_at"],
        "window_key": saved_state["window_key"],
        "alerts": safe_alerts(alerts, limit=max(limit, len(alerts))),
        "groups": groups,
    }


@app.post("/api/ai/triage/save")
def api_ai_triage_save(payload: dict[str, Any]):
    """Persist an AI triage result as editable incident groups (source='ai').

    If an open AI incident group already exists for the same tenant, title, and
    17:00 WIB cutoff window, new member alerts are merged into that existing case
    group rather than creating a duplicate. Alerts after 17:00 WIB open a new case.
    """
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Payload penyimpanan triage tidak valid.")
    groups = payload.get("groups")
    if not isinstance(groups, list) or not groups:
        raise HTTPException(status_code=400, detail="Tidak ada grup triage untuk disimpan.")
    tenant = payload.get("tenant") or ["all"]
    normalize_tenants(tenant)

    allowed_verdicts = {"tp", "fp", "needs_review"}
    saved: list[dict[str, Any]] = []
    with get_db() as conn:
        for index, group in enumerate(groups):
            if not isinstance(group, dict):
                continue
            verdict = str(group.get("verdict") or "needs_review").strip().lower()
            if verdict not in allowed_verdicts:
                verdict = "needs_review"
            title = str(group.get("title") or f"AI Triage {index + 1}").strip()[:200] or f"AI Triage {index + 1}"
            category = str(group.get("category") or "AI Triage")[:120]
            reason = str(group.get("reason") or "")[:400]
            pks = _validate_membership(conn, group.get("alert_ids") or [], tenant)
            group_tenant = "Default"
            group_win_key = str(group.get("window_key") or "").strip()
            if pks:
                t_rows = conn.execute(
                    "SELECT a.id, a.tenant, a.timestamp FROM wazuh.alerts a WHERE a.id = ANY(%s)",
                    [pks],
                ).fetchall()
                distinct_tenants = {str(r["tenant"] or "Default") for r in t_rows}
                if len(distinct_tenants) > 1:
                    raise HTTPException(
                        status_code=400,
                        detail="Satu grup kasus tidak boleh menggabungkan 2 tenant atau lebih.",
                    )
                if distinct_tenants:
                    group_tenant = next(iter(distinct_tenants))
                alert_windows = {wib_window_key(r.get("timestamp")) for r in t_rows if wib_window_key(r.get("timestamp"))}
                if len(alert_windows) > 1:
                    raise HTTPException(
                        status_code=400,
                        detail="Satu grup kasus tidak boleh menggabungkan alert melewati batas jam 17.00 WIB.",
                    )
                if not group_win_key and alert_windows:
                    group_win_key = next(iter(alert_windows))

            severity = {"tp": "high", "fp": "low", "needs_review": "medium"}.get(verdict, "medium")
            existing_id = _find_matching_open_ai_group(
                conn,
                title=title,
                group_tenant=group_tenant,
                group_win_key=group_win_key,
            )
            if existing_id:
                conn.execute(
                    """UPDATE wazuh.analysis_groups
                       SET category = %s, analysis = %s, severity = %s, verdict = %s, updated_at = now()
                       WHERE id = %s""",
                    (category, reason, severity, verdict, existing_id),
                )
                for pk in pks:
                    conn.execute(
                        "INSERT INTO wazuh.alert_group_members(alert_pk, group_id) VALUES(%s, %s) ON CONFLICT DO NOTHING",
                        (pk, existing_id),
                    )
                count_row = conn.execute(
                    "SELECT count(*) AS n FROM wazuh.alert_group_members WHERE group_id = %s",
                    (existing_id,),
                ).fetchone()
                total_members = int(count_row["n"]) if count_row else len(pks)
                saved.append({
                    "id": str(existing_id),
                    "title": title,
                    "verdict": verdict,
                    "alert_count": total_members,
                    "merged": True,
                    "window_key": group_win_key,
                })
            else:
                group_id = uuid.uuid4()
                conn.execute(
                    """INSERT INTO wazuh.analysis_groups(
                        id, title, category, analysis, conclusion, recommendation, status, severity, source, verdict
                    ) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (group_id, title, category, reason, "", "", "open", severity, "ai", verdict),
                )
                for pk in pks:
                    conn.execute(
                        "INSERT INTO wazuh.alert_group_members(alert_pk, group_id) VALUES(%s, %s) ON CONFLICT DO NOTHING",
                        (pk, group_id),
                    )
                saved.append({
                    "id": str(group_id),
                    "title": title,
                    "verdict": verdict,
                    "alert_count": len(pks),
                    "merged": False,
                    "window_key": group_win_key,
                })
    if not saved:
        raise HTTPException(status_code=400, detail="Tidak ada grup valid untuk disimpan.")
    return {"saved": saved, "count": len(saved)}


# A bounded, complete export is returned, or an explicit 413; never a partial file.
MAX_EXPORT_ALERTS = 10_000


def _get_alerts_for_export(
    group_id: str | None = None, alert_ids: str | None = None, tenant: str | list[str] | tuple[str, ...] | None = "all",
    q: str = "", review_status: str = "all", filter_preset: str = "", status: str = "all",
    time_preset: str = "", time_from: str = "", time_to: str = "",
    facet: str = "", facet_value: str = "",
    secondary_facet: str = "", secondary_facet_value: str = "",
    filters: str = "", reviewed_from: str = "", reviewed_to: str = "",
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    where, params = alert_where(
        q=q, tenant=tenant, review_status=review_status, filter_preset=filter_preset,
        status=status, group_id=group_id, time_preset=time_preset, time_from=time_from, time_to=time_to,
        facet=facet, facet_value=facet_value,
        secondary_facet=secondary_facet, secondary_facet_value=secondary_facet_value,
        filters=filters, reviewed_from=reviewed_from, reviewed_to=reviewed_to,
    )
    clean_pks: list[int] = []
    if alert_ids:
        clean_pks = positive_ids(alert_ids.split(","))
        where += (" AND " if where else "WHERE ") + "a.id = ANY(%s)"
        params.append(clean_pks)
    meta: dict[str, Any] = {
        "title": "SOC Security Telemetry Report", "category": "Incident Investigation",
        "severity": "Medium", "status": "Triage", "analysis": "", "conclusion": "", "recommendation": "",
    }
    with get_db() as conn:
        if not alert_ids and not group_id:
            where, params = with_exclusions(where, params, _exclusion_document(conn))
        if group_id and not alert_ids:
            groups = _scoped_groups(conn, tenant, group_id)
            if not groups:
                raise HTTPException(status_code=404, detail="Incident group not found in this scope.")
            meta = dict(groups[0])
        alerts = conn.execute(
            f"""SELECT a.*, ipc.abuse_score, ipc.vt_malicious, ipc.country_code, ipc.isp
                FROM wazuh.alerts a
                LEFT JOIN public.ip_intel_cache ipc ON a.source_ip = ipc.ip
                {where}
                ORDER BY a.rule_id ASC NULLS LAST, a.timestamp ASC NULLS LAST, a.id ASC
                LIMIT %s""",
            params + [MAX_EXPORT_ALERTS + 1],
        ).fetchall()
    if len(alerts) > MAX_EXPORT_ALERTS:
        raise HTTPException(status_code=413, detail=f"Export exceeds {MAX_EXPORT_ALERTS} alerts. Narrow the scope and retry.")
    if alert_ids and {row["id"] for row in alerts} != set(clean_pks):
        raise HTTPException(status_code=409, detail="Sebagian pilihan tidak tersedia pada tenant ini. Pilih ulang; tidak ada laporan parsial dibuat.")
    if alert_ids:
        meta["title"] = f"Investigasi Kasus ({len(alerts)} Alert Terpilih)"
    elif not group_id:
        tenant_tag = f"Tenant: {_tenant_label(tenant)}" if normalize_tenants(tenant) else "Semua Tenant"
        meta["title"] = f"Laporan Rekapitulasi Triage ({tenant_tag})"
    return alerts, meta


def export_scope(
    group_id: str | None = None, alert_ids: str | None = None, tenant: list[str] = Query(default=["all"]),
    q: str = "", review_status: str = "all", filter_preset: str = "", status: str = "all",
    time_preset: str = "", time_from: str = "", time_to: str = "",
    facet: str = "", facet_value: str = "",
    secondary_facet: str = "", secondary_facet_value: str = "",
    filters: str = "", reviewed_from: str = "", reviewed_to: str = "",
) -> dict[str, Any]:
    normalize_tenants(tenant)
    # Explicit selection replaces triage filters, never tenant context.
    if alert_ids is not None:
        try:
            alert_ids = ",".join(str(pk) for pk in positive_ids(alert_ids.split(",")))
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        group_id, q, review_status, filter_preset, status, time_preset, time_from, time_to, facet, facet_value, secondary_facet, secondary_facet_value, filters, reviewed_from, reviewed_to = None, "", "all", "", "all", "", "", "", "", "", "", "", "", "", ""
    return dict(group_id=group_id, alert_ids=alert_ids, tenant=_scope_tenant_value(tenant), q=q,
                review_status=review_status, filter_preset=filter_preset, status=status,
                time_preset=time_preset, time_from=time_from, time_to=time_to,
                facet=facet, facet_value=facet_value,
                secondary_facet=secondary_facet, secondary_facet_value=secondary_facet_value,
                filters=filters, reviewed_from=reviewed_from, reviewed_to=reviewed_to)


def _record_report_audit_log(
    request: Request | None,
    *,
    title: str,
    format_name: str,
    tenant: Any,
    alert_count: int,
    status: str = "published",
) -> None:
    """PRD Section 3.C Audit Log Laporan: record published/exported reports."""
    author = _current_username(request)
    tenant_str = _tenant_label(tenant)
    try:
        with get_db() as conn:
            conn.execute(
                """INSERT INTO wazuh.report_audit_logs(title, author, format, tenant, alert_count, status)
                   VALUES(%s, %s, %s, %s, %s, %s)""",
                (title[:240] or "SOC Telemetry Report", author, format_name, tenant_str, int(alert_count), status),
            )
    except Exception:
        pass


@app.get("/api/export/preview")
def export_preview(scope: dict[str, Any] = Depends(export_scope)):
    alerts, meta = _get_alerts_for_export(**scope)
    return {"count": len(alerts), "meta": meta, "scope": scope,
            "html": generate_gdocs_html_report(alerts, meta), "truncated": False}


@app.get("/api/export/report-html", response_class=HTMLResponse)
def export_gdocs_html(request: Request, scope: dict[str, Any] = Depends(export_scope)):
    alerts, meta = _get_alerts_for_export(**scope)
    html_content = generate_gdocs_html_report(alerts, meta)
    _record_report_audit_log(request, title=str(meta.get("title") or "Laporan HTML"), format_name="Google Docs HTML", tenant=scope.get("tenant"), alert_count=len(alerts))
    return HTMLResponse(content=html_content, headers={"X-Arbiter-Count": str(len(alerts))})


@app.get("/api/export/docx")
def export_docx(request: Request, scope: dict[str, Any] = Depends(export_scope)):
    alerts, meta = _get_alerts_for_export(**scope)
    buf = generate_docx_landscape_report(alerts, meta)
    _record_report_audit_log(request, title=str(meta.get("title") or "Laporan Word"), format_name="Word (.docx)", tenant=scope.get("tenant"), alert_count=len(alerts))
    filename = f"Arbiter-Report-{meta.get('title', 'SOC')[:24].replace(' ', '_')}.docx"
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": "attachment; filename=Arbiter-Report.docx; filename*=UTF-8''" + quote(filename, safe=""), "X-Arbiter-Count": str(len(alerts))},
    )


@app.get("/api/export/xlsx")
def export_xlsx(request: Request, scope: dict[str, Any] = Depends(export_scope)):
    alerts, meta = _get_alerts_for_export(**scope)
    buf = generate_xlsx_workbook(alerts)
    _record_report_audit_log(request, title=str(meta.get("title") or "Workbook Excel"), format_name="Excel (.xlsx)", tenant=scope.get("tenant"), alert_count=len(alerts))
    filename = "Arbiter-Alerts-Export.xlsx"
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"', "X-Arbiter-Count": str(len(alerts))},
    )


@app.get("/api/export/tsv")
def export_tsv(request: Request, scope: dict[str, Any] = Depends(export_scope)):
    alerts, meta = _get_alerts_for_export(**scope)
    tsv_content = generate_tsv_table(alerts)
    _record_report_audit_log(request, title=str(meta.get("title") or "Tabel TSV"), format_name="TSV", tenant=scope.get("tenant"), alert_count=len(alerts))
    return Response(content=tsv_content, media_type="text/tab-separated-values; charset=utf-8",
                    headers={"X-Arbiter-Count": str(len(alerts))})


@app.get("/api/export/markdown")
def export_markdown(request: Request, scope: dict[str, Any] = Depends(export_scope)):
    alerts, meta = _get_alerts_for_export(**scope)
    md_content = generate_markdown_report(alerts, meta)
    _record_report_audit_log(request, title=str(meta.get("title") or "Laporan Markdown"), format_name="Markdown (.md)", tenant=scope.get("tenant"), alert_count=len(alerts))
    return Response(content=md_content, media_type="text/markdown; charset=utf-8",
                    headers={"X-Arbiter-Count": str(len(alerts))})


@app.get("/api/export.csv")
def export_csv(request: Request, scope: dict[str, Any] = Depends(export_scope)):
    alerts, meta = _get_alerts_for_export(**scope)
    _record_report_audit_log(request, title=str(meta.get("title") or "Ekspor CSV"), format_name="CSV", tenant=scope.get("tenant"), alert_count=len(alerts))
    output = io.StringIO()
    fields = [
        "alert_id", "timestamp", "tenant", "agent_name", "agent_ip", "rule_id", "rule_level",
        "description", "source_ip", "abuse_score", "vt_malicious", "country_code",
        "hit_count", "location", "decoder", "cve", "mitre_ids", "is_reviewed"
    ]
    writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    for a in alerts:
        row = dict(a)
        row["mitre_ids"] = ", ".join(row.get("mitre_ids") or [])
        writer.writerow(row)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=arbiter-alerts.csv", "X-Arbiter-Count": str(len(alerts))},
    )


@app.post("/api/sanitize-logs")
def api_sanitize_logs(payload: dict[str, Any]):
    text = str(payload.get("text") or "").strip()
    return {"sanitized": sanitize_text(text)}


@app.get("/api/settings")
def api_get_settings():
    with get_db() as conn:
        stored = load_settings(conn)
    return {"settings": redact_settings(stored)}


@app.put("/api/settings")
def api_put_settings(payload: dict[str, Any]):
    with get_db() as conn:
        current = load_settings(conn)
        try:
            updated = validate_settings(payload, current)
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from None
        save_settings(conn, updated)
    return {"settings": redact_settings(updated)}


def _persist_exclusion_rules(conn, current: dict[str, Any], rules: list[dict[str, Any]]) -> dict[str, Any]:
    """Validate and persist a replacement rule list, preserving the rest of settings."""
    updated = validate_settings({"exclusions": {"rules": rules}}, current)
    save_settings(conn, updated)
    return updated


@app.post("/api/settings/exclusions")
def api_add_exclusion(payload: dict[str, Any]):
    with get_db() as conn:
        current = load_settings(conn)
        existing_rules = list((current.get("exclusions") or {}).get("rules") or [])
        try:
            rule = normalize_exclusion_rule(payload)
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from None
        duplicate = next(
            (item for item in existing_rules
             if item.get("field") == rule["field"]
             and item.get("match") == rule["match"]
             and item.get("pattern") == rule["pattern"]),
            None,
        )
        if duplicate is not None:
            rule = duplicate
            updated = current
            added = False
        else:
            if len(existing_rules) >= MAX_EXCLUSION_RULES:
                raise HTTPException(status_code=400, detail=f"Maksimal {MAX_EXCLUSION_RULES} aturan pengecualian.")
            try:
                updated = _persist_exclusion_rules(conn, current, existing_rules + [rule])
            except ValueError as error:
                raise HTTPException(status_code=400, detail=str(error)) from None
            added = True
    return {"settings": redact_settings(updated), "rule": rule, "added": added}


@app.put("/api/settings/exclusions/{rule_id}")
def api_update_exclusion(rule_id: str, payload: dict[str, Any]):
    with get_db() as conn:
        current = load_settings(conn)
        existing_rules = list((current.get("exclusions") or {}).get("rules") or [])
        index = next((i for i, item in enumerate(existing_rules) if item.get("id") == rule_id), None)
        if index is None:
            raise HTTPException(status_code=404, detail="Aturan pengecualian tidak ditemukan.")
        try:
            merged = normalize_exclusion_rule({**existing_rules[index], **payload, "id": rule_id})
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from None
        existing_rules[index] = merged
        try:
            updated = _persist_exclusion_rules(conn, current, existing_rules)
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from None
    return {"settings": redact_settings(updated), "rule": merged}


@app.delete("/api/settings/exclusions/{rule_id}")
def api_delete_exclusion(rule_id: str):
    with get_db() as conn:
        current = load_settings(conn)
        existing_rules = list((current.get("exclusions") or {}).get("rules") or [])
        remaining = [item for item in existing_rules if item.get("id") != rule_id]
        if len(remaining) == len(existing_rules):
            raise HTTPException(status_code=404, detail="Aturan pengecualian tidak ditemukan.")
        try:
            updated = _persist_exclusion_rules(conn, current, remaining)
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from None
    return {"settings": redact_settings(updated), "deleted": rule_id}


@app.post("/api/settings/exclusions/import")
def api_import_exclusions(payload: dict[str, Any]):
    try:
        parsed = parse_wazuh_exclusion(payload.get("query"))
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from None
    with get_db() as conn:
        current = load_settings(conn)
        existing_rules = list((current.get("exclusions") or {}).get("rules") or [])
        seen = {(item.get("field"), item.get("match"), item.get("pattern")) for item in existing_rules}
        added: list[dict[str, Any]] = []
        for rule in parsed:
            key = (rule["field"], rule["match"], rule["pattern"])
            if key in seen:
                continue
            seen.add(key)
            added.append(rule)
        if len(existing_rules) + len(added) > MAX_EXCLUSION_RULES:
            raise HTTPException(status_code=400, detail=f"Maksimal {MAX_EXCLUSION_RULES} aturan pengecualian.")
        try:
            updated = _persist_exclusion_rules(conn, current, existing_rules + added) if added else current
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from None
    return {"settings": redact_settings(updated), "added": added, "added_count": len(added)}


@app.post("/api/settings/wazuh/test")
def api_test_wazuh(payload: dict[str, Any]):
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Payload pengujian tidak valid.")
    with get_db() as conn:
        stored = load_settings(conn)
    wazuh = stored.get("wazuh", {})
    url = str(payload.get("indexer_url", wazuh.get("indexer_url", "")) or "").strip()
    username = str(payload.get("username", wazuh.get("username", "")) or "").strip()
    password = payload.get("password")
    if password is None or password == "":
        password = wazuh_password(stored)
    pattern = str(payload.get("index_pattern", wazuh.get("index_pattern", "wazuh-alerts-*")) or "").strip()
    verify_tls = payload.get("verify_tls", wazuh.get("verify_tls", True))
    if not isinstance(verify_tls, bool):
        raise HTTPException(status_code=400, detail="verify_tls harus berupa boolean (true/false).")
    realtime = stored.get("realtime", {})
    raw_min = payload.get("min_rule_level", realtime.get("min_rule_level", 7))
    try:
        min_level = max(0, min(16, int(7 if raw_min is None or raw_min == "" else raw_min)))
    except (TypeError, ValueError):
        min_level = 7
    raw_max = payload.get("max_rule_level", realtime.get("max_rule_level"))
    try:
        max_level = int(raw_max) if raw_max is not None and str(raw_max).strip() != "" else None
    except (TypeError, ValueError):
        max_level = None
    extra_kwargs: dict[str, Any] = {}
    if min_level != 7 or max_level is not None:
        extra_kwargs["min_rule_level"] = min_level
        extra_kwargs["max_rule_level"] = max_level
    try:
        return test_wazuh_connection(
            indexer_url=url,
            username=username,
            password=str(password or ""),
            index_pattern=pattern,
            verify_tls=verify_tls,
            **extra_kwargs,
        )
    except ValueError as error:
        raise HTTPException(status_code=502, detail=str(error)) from None


@app.get("/api/database/status")
def api_database_status():
    if hasattr(db_module, "get_database_status"):
        try:
            with get_db() as conn:
                return db_module.get_database_status(conn)
        except Exception as exc:
            # A broken active database must never remove the controls that let
            # the operator switch back to a working profile.
            if hasattr(db_module, "get_database_status_unavailable"):
                detail = exc.detail if isinstance(exc, HTTPException) else str(exc)
                return db_module.get_database_status_unavailable(detail)
            raise
    with get_db() as conn:
        alerts_n = conn.execute("SELECT count(*) AS n FROM wazuh.alerts").fetchone()["n"]
        groups_n = conn.execute("SELECT count(*) AS n FROM wazuh.analysis_groups").fetchone()["n"]
        intel_n = 0
        try:
            intel_n = conn.execute("SELECT count(*) AS n FROM public.ip_intel_cache").fetchone()["n"]
        except Exception:
            pass
        tenants = conn.execute("SELECT tenant, count(*) AS count FROM wazuh.alerts GROUP BY tenant").fetchall()
        return {
            "status": "ok",
            "active_profile": {"id": "local", "name": "Laptop (Lokal)", "mode": "read_write", "masked_url": "postgresql://arbiter:***@127.0.0.1:5432/abuseip"},
            "profiles": [
                {"id": "local", "name": "Laptop (Lokal)", "mode": "read_write", "description": "PostgreSQL lokal di laptop. Workspace operasional SOC utama.", "masked_url": "postgresql://arbiter:***@127.0.0.1:5432/abuseip", "is_active": True},
                {"id": "remote", "name": "PC Intel (Remote)", "mode": "read_only", "description": "PostgreSQL pada host IP Intel. Sumber cache reputasi dan telemetri sekunder.", "masked_url": "postgresql://arbiter:***@192.168.1.50:5432/abuseip", "is_active": False},
            ],
            "stats": {"alerts": alerts_n, "groups": groups_n, "ip_intel_records": intel_n},
            "tenants": tenants or [],
            "table_sizes": {"wazuh.alerts": "N/A", "wazuh.analysis_groups": "N/A"},
        }


@app.post("/api/database/switch")
def api_database_switch(payload: dict[str, Any]):
    profile = str(payload.get("profile") or "").strip()
    if hasattr(db_module, "set_active_profile"):
        active = db_module.get_active_profile_id() if hasattr(db_module, "get_active_profile_id") else None
        # Validate a new target before committing the switch. The Local profile is
        # always allowed so a broken active database can be escaped.
        if profile != active and profile != "local" and hasattr(db_module, "check_profile_ready"):
            ready = db_module.check_profile_ready(profile)
            if not ready.get("ok"):
                raise HTTPException(
                    status_code=409,
                    detail=f"Tidak dapat beralih ke '{profile}': {ready.get('error') or 'database target tidak siap'} Database aktif tidak diubah.",
                )
        return db_module.set_active_profile(profile)
    return {"id": profile, "status": "switched"}


@app.post("/api/database/test")
def api_database_test(payload: dict[str, Any]):
    url = payload.get("url")
    if hasattr(db_module, "test_db_connection"):
        if "profile" in payload:
            profile = str(payload["profile"]).strip()
            result = db_module.test_db_connection(url, profile_id=profile)
            if result.get("ok") and hasattr(db_module, "check_profile_ready"):
                ready = db_module.check_profile_ready(profile)
                result["ready"] = bool(ready.get("ok"))
                if not ready.get("ok"):
                    result["schema_error"] = ready.get("error") or "Skema Arbiter belum tersedia."
            return result
        return db_module.test_db_connection(url)
    return {"ok": True, "latency_ms": 1.0, "version": "PostgreSQL Mock"}


@app.post("/api/database/config")
def api_database_config(payload: dict[str, Any]):
    profile = str(payload.get("profile") or "remote").strip()
    url = str(payload.get("url") or "").strip()
    if hasattr(db_module, "update_profile_url"):
        return db_module.update_profile_url(profile, url)
    return {"status": "ok"}


@app.post("/api/database/purge-alerts")
def api_database_purge_alerts(payload: dict[str, Any]):
    older_than_days = payload.get("older_than_days")
    if older_than_days is not None and str(older_than_days).strip() != "":
        try:
            older_than_days = int(older_than_days)
            if older_than_days <= 0 or older_than_days > 36500:
                raise ValueError()
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail="Parameter older_than_days harus berupa bilangan bulat positif.")
    else:
        older_than_days = None

    time_from = payload.get("time_from")
    if time_from and str(time_from).strip():
        time_from = str(time_from).strip()
        try:
            from datetime import datetime
            datetime.fromisoformat(time_from.replace("Z", "+00:00"))
        except Exception:
            raise HTTPException(status_code=400, detail="Format time_from tidak valid (gunakan ISO 8601).")
    else:
        time_from = ""

    time_to = payload.get("time_to")
    if time_to and str(time_to).strip():
        time_to = str(time_to).strip()
        try:
            from datetime import datetime
            datetime.fromisoformat(time_to.replace("Z", "+00:00"))
        except Exception:
            raise HTTPException(status_code=400, detail="Format time_to tidak valid (gunakan ISO 8601).")
    else:
        time_to = ""

    if time_from and time_to and time_from > time_to:
        raise HTTPException(status_code=400, detail="Rentang waktu tidak valid: time_from harus sebelum atau sama dengan time_to.")

    tenant = str(payload.get("tenant") or "all").strip()

    if "dry_run" in payload:
        if not isinstance(payload["dry_run"], bool):
            raise HTTPException(status_code=400, detail="Parameter dry_run harus berupa boolean (true/false).")
        dry_run = payload["dry_run"]
    else:
        dry_run = True

    preview_token = payload.get("preview_token")
    if not dry_run and (preview_token is None or not str(preview_token).strip()):
        raise HTTPException(
            status_code=400,
            detail="Eksekusi pembersihan memerlukan server-side preview_token yang valid. Lakukan pratinjau terlebih dahulu."
        )

    expected_profile = payload.get("expected_profile") or payload.get("profile")

    with get_db() as conn:
        if hasattr(db_module, "purge_alerts"):
            return db_module.purge_alerts(
                conn, older_than_days=older_than_days, time_from=time_from,
                time_to=time_to, tenant=tenant, dry_run=dry_run,
                preview_token=preview_token, expected_profile=expected_profile,
            )
        return {"dry_run": dry_run, "count": 0}


@app.post("/api/database/purge-incidents")
def api_database_purge_incidents(payload: dict[str, Any]):
    status_filter = str(payload.get("status") or "closed_only").strip()
    valid_statuses = {"closed_only", "all", "closed", "resolved", "open", "in_progress"}
    if status_filter not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Kriteria status insiden '{status_filter}' tidak valid.")

    if "dry_run" in payload:
        if not isinstance(payload["dry_run"], bool):
            raise HTTPException(status_code=400, detail="Parameter dry_run harus berupa boolean (true/false).")
        dry_run = payload["dry_run"]
    else:
        dry_run = True

    preview_token = payload.get("preview_token")
    if not dry_run and (preview_token is None or not str(preview_token).strip()):
        raise HTTPException(
            status_code=400,
            detail="Eksekusi pembersihan memerlukan server-side preview_token yang valid. Lakukan pratinjau terlebih dahulu."
        )

    expected_profile = payload.get("expected_profile") or payload.get("profile")

    with get_db() as conn:
        if hasattr(db_module, "purge_incidents"):
            return db_module.purge_incidents(
                conn, status_filter=status_filter, dry_run=dry_run,
                preview_token=preview_token, expected_profile=expected_profile,
            )
        return {"dry_run": dry_run, "count": 0}


@app.post("/api/database/purge-raw")
def api_database_purge_raw(payload: dict[str, Any]):
    """PRD Section 3.A Data Retention: purge raw payload extension older than 30-90 days while retaining metadata & verdicts."""
    retention_days = payload.get("retention_days")
    if retention_days is not None and str(retention_days).strip() != "":
        try:
            retention_days = int(retention_days)
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail="Parameter retention_days harus berupa angka.")
    else:
        with get_db() as conn:
            stored = load_settings(conn)
            retention_days = int((stored.get("retention") or {}).get("raw_days") or 30)

    if not (30 <= int(retention_days) <= 90):
        raise HTTPException(status_code=400, detail="Retensi log mentah (retention_days) harus antara 30 dan 90 hari.")

    tenant = str(payload.get("tenant") or "all").strip()
    dry_run = bool(payload.get("dry_run", True))
    preview_token = payload.get("preview_token")
    expected_profile = payload.get("expected_profile") or payload.get("profile")

    with get_db() as conn:
        if hasattr(db_module, "purge_raw_alerts"):
            return db_module.purge_raw_alerts(
                conn,
                retention_days=int(retention_days),
                tenant=tenant,
                dry_run=dry_run,
                preview_token=preview_token,
                expected_profile=expected_profile,
            )
        return {"dry_run": dry_run, "count": 0, "retention_days": int(retention_days)}


@app.get("/api/monitoring")
def api_get_monitoring(
    tenant: list[str] = Query(default=["all"]),
    tz_offset_minutes: int = 420,
):
    """PRD Section 3.C Monitoring Dashboard: Real-time metric cards, Analyst Leaderboard, and Report Audit Log."""
    offset = max(-840, min(840, int(tz_offset_minutes or 0)))
    now_utc = datetime.now(timezone.utc)
    now_local = now_utc + timedelta(minutes=offset)
    today_date = now_local.date()
    today_iso = today_date.isoformat()
    today_start_local = datetime.combine(today_date, datetime.min.time(), tzinfo=timezone.utc)
    today_start_utc = (today_start_local - timedelta(minutes=offset)).isoformat()

    t_sql, t_params = tenant_clause("a", tenant)
    t_where = f"WHERE {t_sql}" if t_sql else ""
    t_and = f"AND {t_sql}" if t_sql else ""

    with get_db() as conn:
        _expire_stale_claims(conn)

        # 1. Check daily_metrics_cache first (PRD Section 4 Query Optimization)
        cached_pull_today = 0
        try:
            cache_t_sql, cache_t_params = tenant_clause("c", tenant)
            cache_where = f"WHERE c.metric_date = %s{f' AND {cache_t_sql}' if cache_t_sql else ''}"
            c_row = conn.execute(
                f"SELECT COALESCE(SUM(c.pulled_count), 0) AS pulled FROM wazuh.daily_metrics_cache c {cache_where}",
                [today_iso, *cache_t_params],
            ).fetchone()
            cached_pull_today = int((c_row or {}).get("pulled") or 0)
        except Exception:
            cached_pull_today = 0

        # Indexed metrics query using idx_wazuh_alerts_reviewed, idx_wazuh_alerts_imported_at, idx_wazuh_alerts_timestamp
        try:
            m_row = conn.execute(
                f"""SELECT
                        COUNT(*) FILTER (WHERE a.imported_at >= %s OR a.timestamp >= %s) AS pulled_today,
                        COUNT(*) FILTER (WHERE a.is_reviewed = false AND (a.imported_at < %s AND (a.timestamp IS NULL OR a.timestamp < %s))) AS outstanding_backlog,
                        COUNT(*) FILTER (WHERE a.is_reviewed = false) AS total_unreviewed,
                        COUNT(*) FILTER (WHERE a.is_reviewed = true) AS global_review_count,
                        COUNT(*) FILTER (WHERE a.status = 'claimed') AS active_claims,
                        COUNT(*) FILTER (WHERE a.verdict = 'tp') AS tp_total,
                        COUNT(*) FILTER (WHERE a.verdict = 'fp') AS fp_total,
                        COUNT(*) FILTER (WHERE a.verdict = 'benign') AS benign_total
                    FROM wazuh.alerts a {t_where}""",
                [today_start_utc, today_iso, today_start_utc, today_iso, *t_params],
            ).fetchone()
        except Exception:
            # Fallback if imported_at or status/verdict not present in minimal synthetic table
            m_row = conn.execute(
                f"""SELECT
                        COUNT(*) FILTER (WHERE a.timestamp >= %s) AS pulled_today,
                        COUNT(*) FILTER (WHERE a.is_reviewed = false AND (a.timestamp IS NULL OR a.timestamp < %s)) AS outstanding_backlog,
                        COUNT(*) FILTER (WHERE a.is_reviewed = false) AS total_unreviewed,
                        COUNT(*) FILTER (WHERE a.is_reviewed = true) AS global_review_count,
                        0 AS active_claims,
                        0 AS tp_total,
                        0 AS fp_total,
                        0 AS benign_total
                    FROM wazuh.alerts a {t_where}""",
                [today_iso, today_iso, *t_params],
            ).fetchone()

        pulled_today = max(cached_pull_today, int((m_row or {}).get("pulled_today") or 0))
        outstanding_backlog = int((m_row or {}).get("outstanding_backlog") or 0)
        total_unreviewed = int((m_row or {}).get("total_unreviewed") or 0)
        global_review_count = int((m_row or {}).get("global_review_count") or 0)
        active_claims = int((m_row or {}).get("active_claims") or 0)

        # 2. Analyst Leaderboard & Accountability
        try:
            known_users = {u["username"]: u for u in list_users(conn)}
        except Exception:
            known_users = {"admin": {"username": "admin", "display_name": "Administrator", "role": "admin"}}
        leaderboard_map: dict[str, dict[str, Any]] = {}
        for uname, uinfo in known_users.items():
            leaderboard_map[uname] = {
                "username": uname,
                "display_name": uinfo.get("display_name") or uname,
                "role": uinfo.get("role") or "analyst",
                "currently_claimed": 0,
                "completed_today": 0,
                "total_contributions": 0,
                "tp_count": 0,
                "fp_count": 0,
                "benign_count": 0,
            }

        try:
            claimed_rows = conn.execute(
                f"""SELECT a.claimed_by AS username, COUNT(*) AS n
                    FROM wazuh.alerts a
                    WHERE a.status = 'claimed' AND a.claimed_by IS NOT NULL AND a.claimed_by != '' {t_and}
                    GROUP BY a.claimed_by""",
                t_params,
            ).fetchall()
            for r in claimed_rows:
                uname = str(r["username"])
                entry = leaderboard_map.setdefault(uname, {
                    "username": uname, "display_name": uname, "role": "analyst",
                    "currently_claimed": 0, "completed_today": 0, "total_contributions": 0,
                    "tp_count": 0, "fp_count": 0, "benign_count": 0,
                })
                entry["currently_claimed"] = int(r["n"] or 0)

            reviewed_rows = conn.execute(
                f"""SELECT COALESCE(NULLIF(a.reviewed_by, ''), NULLIF(a.claimed_by, ''), 'admin') AS username,
                           COUNT(*) AS total_n,
                           COUNT(*) FILTER (WHERE a.reviewed_at >= %s) AS today_n,
                           COUNT(*) FILTER (WHERE a.verdict = 'tp') AS tp_n,
                           COUNT(*) FILTER (WHERE a.verdict = 'fp') AS fp_n,
                           COUNT(*) FILTER (WHERE a.verdict = 'benign') AS benign_n
                    FROM wazuh.alerts a
                    WHERE a.is_reviewed = true {t_and}
                    GROUP BY 1""",
                [today_start_utc, *t_params],
            ).fetchall()
            for r in reviewed_rows:
                uname = str(r["username"])
                entry = leaderboard_map.setdefault(uname, {
                    "username": uname, "display_name": uname, "role": "analyst",
                    "currently_claimed": 0, "completed_today": 0, "total_contributions": 0,
                    "tp_count": 0, "fp_count": 0, "benign_count": 0,
                })
                entry["total_contributions"] = int(r["total_n"] or 0)
                entry["completed_today"] = int(r["today_n"] or 0)
                entry["tp_count"] = int(r["tp_n"] or 0)
                entry["fp_count"] = int(r["fp_n"] or 0)
                entry["benign_count"] = int(r["benign_n"] or 0)
        except Exception:
            pass

        leaderboard = sorted(
            leaderboard_map.values(),
            key=lambda x: (x["completed_today"], x["total_contributions"], x["currently_claimed"]),
            reverse=True,
        )

        # 3. Audit Log Laporan (Published Incident Cases + Exported Reports)
        audit_logs: list[dict[str, Any]] = []
        try:
            rep_rows = conn.execute(
                """SELECT id, title, author, format, tenant, alert_count, status, created_at
                   FROM wazuh.report_audit_logs
                   ORDER BY created_at DESC, id DESC
                   LIMIT 50"""
            ).fetchall()
            for r in rep_rows:
                audit_logs.append({
                    "id": f"rep-{r['id']}",
                    "title": str(r.get("title") or "Laporan Insiden"),
                    "author": str(r.get("author") or "analyst"),
                    "created_at": str(r.get("created_at") or ""),
                    "export_status": f"Diekspor ({r.get('format') or 'HTML'})",
                    "format": str(r.get("format") or "HTML"),
                    "tenant": str(r.get("tenant") or "Semua Tenant"),
                    "alert_count": int(r.get("alert_count") or 0),
                })
        except Exception:
            pass

        try:
            inc_rows = _scoped_groups(conn, tenant)
            for g in inc_rows[:30]:
                audit_logs.append({
                    "id": str(g["id"]),
                    "title": str(g.get("title") or "Kasus Insiden"),
                    "author": "AI Triage" if g.get("source") == "ai" else "Tim Analis SOC",
                    "created_at": str(g.get("updated_at") or g.get("created_at") or ""),
                    "export_status": f"Kasus {str(g.get('status') or 'open').upper()} · Siap Ekspor",
                    "format": "Kasus Insiden",
                    "tenant": ", ".join(g.get("tenants") or []) or "Semua Tenant",
                    "alert_count": int(g.get("alert_count") or 0),
                })
        except Exception:
            pass

        audit_logs.sort(key=lambda x: x.get("created_at") or "", reverse=True)

    return {
        "metrics": {
            "total_pull_today": pulled_today,
            "outstanding_backlog": outstanding_backlog,
            "total_unreviewed": total_unreviewed,
            "global_review_count": global_review_count,
            "active_claims": active_claims,
            "verdicts": {
                "tp": int((m_row or {}).get("tp_total") or 0),
                "fp": int((m_row or {}).get("fp_total") or 0),
                "benign": int((m_row or {}).get("benign_total") or 0),
            },
        },
        "leaderboard": leaderboard,
        "audit_logs": audit_logs[:50],
        "checked_at": now_utc.isoformat(),
    }


@app.post("/api/monitoring/audit-log")
def api_create_report_audit_log(payload: dict[str, Any], request: Request):
    """Explicitly record a report publication/export event from the UI."""
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Payload audit log tidak valid.")
    title = str(payload.get("title") or "Laporan Insiden SOC").strip()[:240]
    fmt = str(payload.get("format") or "HTML").strip()[:60]
    tenant_val = payload.get("tenant") or "all"
    count = int(payload.get("alert_count") or 0)
    status = str(payload.get("status") or "published").strip()[:60]
    _record_report_audit_log(request, title=title, format_name=fmt, tenant=tenant_val, alert_count=count, status=status)
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def index_page():
    html_path = Path(__file__).with_name("index.html")
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))


# ── Authentication, User Management & Shared Wazuh Query Formulas ──

WAZUH_QUERIES_STATE_KEY = "wazuh_query_formulas"


def _require_admin_user(request: Request, conn) -> dict[str, Any]:
    user = getattr(request.state, "user", None) or _extract_request_user(request)
    if not user:
        if PORT == 0 and request.headers.get("x-arbiter-auth-enforce") != "1":
            users = list_users(conn)
            return next((u for u in users if u["role"] == "admin"), {"username": "admin", "role": "admin", "display_name": "Administrator"})
        raise HTTPException(status_code=401, detail="Sesi login diperlukan. Silakan login terlebih dahulu.")
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Akses ditolak. Fitur ini hanya dapat diakses oleh Admin.")
    return user


@app.get("/api/auth/me")
def api_auth_me(request: Request):
    with get_db() as conn:
        list_users(conn)  # Ensure initial admin seed exists
    user = _extract_request_user(request)
    if not user:
        return {"authenticated": False, "user": None}
    return {"authenticated": True, "user": user}


@app.post("/api/auth/login")
def api_auth_login(payload: dict[str, Any], response: Response):
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Payload login tidak valid.")
    username = str(payload.get("username") or "").strip()
    password = str(payload.get("password") or "")
    if not username or not password:
        raise HTTPException(status_code=400, detail="Username dan password wajib diisi.")
    with get_db() as conn:
        user = authenticate_user(conn, username, password)
    if not user:
        raise HTTPException(status_code=401, detail="Username atau password salah.")
    token = create_session_token(user)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=SESSION_TTL_SECONDS,
        httponly=True,
        samesite="lax",
        path="/",
    )
    return {"ok": True, "user": user, "token": token}


@app.post("/api/auth/logout")
def api_auth_logout(response: Response):
    response.delete_cookie(key=SESSION_COOKIE_NAME, path="/")
    return {"ok": True}


@app.get("/api/auth/users")
def api_list_users(request: Request):
    with get_db() as conn:
        _require_admin_user(request, conn)
        return {"users": list_users(conn)}


@app.post("/api/auth/users")
def api_create_user(payload: dict[str, Any], request: Request):
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Payload pengguna tidak valid.")
    with get_db() as conn:
        _require_admin_user(request, conn)
        try:
            created = create_user(
                conn,
                username=str(payload.get("username") or ""),
                password=str(payload.get("password") or ""),
                role=str(payload.get("role") or "analyst"),
                display_name=str(payload.get("display_name") or ""),
            )
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from None
        return {"user": created, "users": list_users(conn)}


@app.put("/api/auth/users/{username}")
def api_update_user(username: str, payload: dict[str, Any], request: Request):
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Payload pembaruan pengguna tidak valid.")
    with get_db() as conn:
        _require_admin_user(request, conn)
        try:
            updated = update_user(
                conn,
                username,
                password=payload.get("password"),
                role=payload.get("role"),
                display_name=payload.get("display_name"),
            )
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from None
        return {"user": updated, "users": list_users(conn)}


@app.delete("/api/auth/users/{username}")
def api_delete_user(username: str, request: Request):
    with get_db() as conn:
        actor = _require_admin_user(request, conn)
        try:
            delete_user(conn, username, actor_username=str(actor.get("username") or ""))
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from None
        return {"deleted": username, "users": list_users(conn)}


@app.get("/api/wazuh-queries")
def api_list_wazuh_queries():
    with get_db() as conn:
        doc = load_document(conn, WAZUH_QUERIES_STATE_KEY, None)
    data = doc if isinstance(doc, dict) else {}
    items = data.get("items") if isinstance(data.get("items"), list) else []
    notepad = str(data.get("notepad") or "")
    return {
        "notepad": notepad,
        "updated_at": str(data.get("updated_at") or ""),
        "updated_by": str(data.get("updated_by") or ""),
        "items": items,
        "queries": items,
    }


@app.put("/api/wazuh-queries")
def api_update_wazuh_notepad(payload: dict[str, Any], request: Request):
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Payload notepad tidak valid.")
    notepad = str(payload.get("notepad") or "")[:100000]
    user = _extract_request_user(request)
    author = str(user.get("username") if user else payload.get("author") or "analyst")
    now_iso = datetime.now(timezone.utc).isoformat()
    with get_db() as conn:
        doc = load_document(conn, WAZUH_QUERIES_STATE_KEY, None)
        data = dict(doc) if isinstance(doc, dict) else {}
        items = list(data.get("items")) if isinstance(data.get("items"), list) else []
        data["notepad"] = notepad
        data["updated_at"] = now_iso
        data["updated_by"] = author
        data["items"] = items
        save_document(conn, WAZUH_QUERIES_STATE_KEY, data)
    return {
        "notepad": notepad,
        "updated_at": now_iso,
        "updated_by": author,
        "items": items,
        "queries": items,
    }


@app.post("/api/wazuh-queries")
def api_save_wazuh_query(payload: dict[str, Any], request: Request):
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Payload rumus query tidak valid.")
    title = str(payload.get("title") or "").strip()[:160]
    category = str(payload.get("category") or "Catatan").strip()[:80] or "Catatan"
    content = str(payload.get("content") or payload.get("dql") or "").strip()[:50000]
    dsl = str(payload.get("dsl") or "").strip()[:8000]
    lucene = str(payload.get("lucene") or "").strip()[:4000]
    description = str(payload.get("description") or "").strip()[:600]
    if not title:
        raise HTTPException(status_code=400, detail="Judul catatan rumus wajib diisi.")
    if not (content or dsl or lucene):
        raise HTTPException(status_code=400, detail="Isi rumus query wajib diisi.")

    user = _extract_request_user(request)
    author = str(user.get("username") if user else payload.get("author") or "analyst")
    item = {
        "id": str(uuid.uuid4()),
        "title": title,
        "category": category,
        "description": description,
        "content": content,
        "dql": content,
        "dsl": dsl,
        "lucene": lucene,
        "author": author,
        "created_by": author,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    with get_db() as conn:
        doc = load_document(conn, WAZUH_QUERIES_STATE_KEY, None)
        data = dict(doc) if isinstance(doc, dict) else {}
        items = list(data.get("items")) if isinstance(data.get("items"), list) else []
        items.insert(0, item)
        items = items[:200]
        data["items"] = items
        save_document(conn, WAZUH_QUERIES_STATE_KEY, data)
    return {"item": item, "items": items, "queries": items, "notepad": str(data.get("notepad") or "")}


@app.delete("/api/wazuh-queries/{query_id}")
def api_delete_wazuh_query(query_id: str):
    target = str(query_id or "").strip()
    if not target:
        raise HTTPException(status_code=400, detail="ID rumus query tidak valid.")
    with get_db() as conn:
        doc = load_document(conn, WAZUH_QUERIES_STATE_KEY, None)
        data = dict(doc) if isinstance(doc, dict) else {}
        items = list(data.get("items")) if isinstance(data.get("items"), list) else []
        filtered = [it for it in items if str(it.get("id") or "") != target]
        if len(filtered) == len(items):
            raise HTTPException(status_code=404, detail="Rumus query tidak ditemukan.")
        data["items"] = filtered
        save_document(conn, WAZUH_QUERIES_STATE_KEY, data)
    return {"deleted": target, "items": filtered, "queries": filtered, "notepad": str(data.get("notepad") or "")}
