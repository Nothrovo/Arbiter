"""FastAPI Application Server for Arbiter — SOC Telemetry & Incident Workspace."""

from __future__ import annotations

import csv
import io
import json
import re
import uuid
from contextlib import asynccontextmanager, contextmanager
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
    AI_TRIAGE_LAST_KEY,
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
from app.intel import (
    enrich_ip,
    enrich_ips_with_sidecar,
    extract_alert_intel_context,
    has_usable_sidecar_cache,
    is_valid_ip,
    lookup_remote_ip_cache_detail,
    normalize_ip_address,
    normalize_sidecar_record,
    parse_sidecar_candidates,
    probe_sidecar,
    sync_remote_cache,
    upsert_ip_cache,
)
import app.database as db_module
from app.database import get_db, init_database, ingest_alert_with_dedup
from app.exports import (
    FLAG_EXPORT_COLUMNS,
    generate_docx_landscape_report,
    generate_gdocs_html_report,
    generate_markdown_report,
    generate_tsv_table,
    generate_xlsx_workbook,
)
from app.filters import build_filter_sql, parse_filters
from app.parser import parse_export
from app.privacy import sanitize_text
from app.pull_jobs import cancel_job, get_job, list_jobs, start_pull_job
from app.query import alert_where, normalize_tenants, positive_ids, tenant_clause, validated_group_id, PIVOT_DEFINITIONS, FACET_COLUMNS, is_malicious_alert_record
from app.settings import (
    _normalize_wazuh_timestamp,
    _valid_timestamp,
    intel_abuseipdb_key,
    intel_virustotal_key,
    load_document,
    load_settings,
    migrate_settings,
    normalize_sidecar_urls,
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
            with _savepoint(conn):
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
ALLOWED_FLAG_COLORS = {"green", "yellow", "red"}
ALLOWED_RULE_STATUSES = {"pending", "done"}
FLAG_TO_DEFAULT_VERDICT = {"green": "fp", "yellow": "needs_review", "red": "tp"}


@contextmanager
def _savepoint(conn):
    """Wrap optional/fallback SQL in a SAVEPOINT on psycopg so caught errors never abort the outer transaction."""
    tx = getattr(conn, "transaction", None)
    if callable(tx):
        with tx():
            yield
    else:
        yield


def _flag_counts(conn, tenant: str | list[str] | tuple[str, ...] | None = "all") -> dict[str, Any]:
    t_sql, t_params = tenant_clause("a", tenant)
    t_where = f"WHERE {t_sql}" if t_sql else ""
    try:
        with _savepoint(conn):
            row = conn.execute(
                f"""SELECT
                        COUNT(*) FILTER (WHERE a.flag_color = 'green') AS green_total,
                        COUNT(*) FILTER (WHERE a.flag_color = 'green' AND COALESCE(NULLIF(a.rule_status, ''), 'pending') != 'done') AS green_pending,
                        COUNT(*) FILTER (WHERE a.flag_color = 'green' AND a.rule_status = 'done') AS green_done,
                        COUNT(*) FILTER (WHERE a.flag_color = 'yellow') AS yellow_total,
                        COUNT(*) FILTER (WHERE a.flag_color = 'yellow' AND COALESCE(NULLIF(a.rule_status, ''), 'pending') != 'done') AS yellow_pending,
                        COUNT(*) FILTER (WHERE a.flag_color = 'yellow' AND a.rule_status = 'done') AS yellow_done,
                        COUNT(*) FILTER (WHERE a.flag_color = 'red') AS red_total
                    FROM wazuh.alerts a {t_where}""",
                t_params,
            ).fetchone()
    except Exception:
        row = None
    g_tot = int((row or {}).get("green_total") or 0)
    g_pen = int((row or {}).get("green_pending") or 0)
    g_don = int((row or {}).get("green_done") or 0)
    y_tot = int((row or {}).get("yellow_total") or 0)
    y_pen = int((row or {}).get("yellow_pending") or 0)
    y_don = int((row or {}).get("yellow_done") or 0)
    r_tot = int((row or {}).get("red_total") or 0)
    return {
        "counts": {
            "green": {"total": g_tot, "pending": g_pen, "done": g_don},
            "yellow": {"total": y_tot, "pending": y_pen, "done": y_don},
            "red": {"total": r_tot, "pending": 0, "done": 0},
        },
        "pending_tuning": g_pen + y_pen,
        "total_flagged": g_tot + y_tot + r_tot,
    }


def _flag_pattern_predicate(pattern: str, pattern_mode: str) -> tuple[str, list[Any]]:
    pat = str(pattern or "").strip()
    if len(pat) > 120:
        raise HTTPException(status_code=422, detail="Pola teks maksimal 120 karakter.")
    mode = str(pattern_mode or "contains").strip().lower()
    if mode not in {"contains", "regex"}:
        raise HTTPException(status_code=422, detail="pattern_mode harus 'contains' atau 'regex'.")
    if not pat:
        return "", []
    if mode == "regex":
        try:
            re.compile(pat)
        except re.error as exc:
            raise HTTPException(status_code=422, detail=f"Regex pola tidak valid: {exc}") from None
        expr = (
            "(a.description ~* %s OR COALESCE(a.raw->>'full_log', '') ~* %s "
            "OR a.raw::text ~* %s OR a.parsed_details::text ~* %s)"
        )
        return expr, [pat] * 4
    expr = (
        "(a.description ILIKE %s OR COALESCE(a.raw->>'full_log', '') ILIKE %s "
        "OR a.raw::text ILIKE %s OR a.parsed_details::text ILIKE %s)"
    )
    return expr, [f"%{pat}%"] * 4


def _build_flag_scope_where(
    *,
    tenant: Any,
    flag_color: str,
    rule_status: str = "all",
    q: str = "",
    group_by: str | None = None,
    group_key: str | None = None,
    pattern: str = "",
    pattern_mode: str = "contains",
) -> tuple[str, list[Any]]:
    color = str(flag_color or "").strip().lower()
    if color not in ALLOWED_FLAG_COLORS:
        raise HTTPException(status_code=422, detail="flag_color harus 'green', 'yellow', atau 'red'.")
    r_status = str(rule_status or "all").strip().lower()
    if r_status not in {"all", "pending", "done"}:
        raise HTTPException(status_code=422, detail="rule_status harus 'all', 'pending', atau 'done'.")
    clauses = ["a.flag_color = %s"]
    params: list[Any] = [color]
    t_sql, t_params = tenant_clause("a", tenant)
    if t_sql:
        clauses.append(t_sql)
        params.extend(t_params)
    if color != "red":
        if r_status == "pending":
            clauses.append("COALESCE(NULLIF(a.rule_status, ''), 'pending') != 'done'")
        elif r_status == "done":
            clauses.append("a.rule_status = 'done'")
    search_q = str(q or "").strip()
    if search_q:
        cols = (
            "a.alert_id", "a.agent_name", "a.rule_id", "a.description",
            "a.source_ip", "a.custom_rule_id", "a.rule_notes", "a.raw::text",
        )
        clauses.append("(" + " OR ".join(f"{col} ILIKE %s" for col in cols) + ")")
        params.extend([f"%{search_q}%"] * len(cols))
    if group_by is not None and group_key is not None:
        if group_by not in PIVOT_DEFINITIONS:
            raise HTTPException(status_code=422, detail=f"Parameter pengelompokan '{group_by}' tidak didukung.")
        if group_by == "pattern":
            match_expr, match_params = _flag_pattern_predicate(pattern, pattern_mode)
            if not match_expr:
                clauses.append("1 = 0")
            elif group_key == "Cocok pola":
                clauses.append(match_expr)
                params.extend(match_params)
            elif group_key == "Tidak cocok pola":
                clauses.append(f"NOT ({match_expr})")
                params.extend(match_params)
            else:
                clauses.append("1 = 0")
        else:
            dim_sql = PIVOT_DEFINITIONS[group_by]["sql"]
            clauses.append(f"({dim_sql}) = %s")
            params.append(str(group_key))
    return "WHERE " + " AND ".join(clauses), params


def _apply_flag_update(
    conn,
    clean_pks: list[int],
    *,
    flag_color: str | None,
    actor: str,
    auto_review: bool,
    reviewer_notes: str,
    tenant: Any,
) -> dict[str, Any]:
    if not clean_pks:
        raise HTTPException(status_code=400, detail="Pilih minimal satu alert.")
    rows = conn.execute(
        "SELECT id, tenant, is_reviewed, verdict, flag_color FROM wazuh.alerts WHERE id = ANY(%s)",
        (clean_pks,),
    ).fetchall()
    if not flag_color:
        conn.execute(
            """UPDATE wazuh.alerts
               SET flag_color = NULL,
                   flagged_by = NULL,
                   flagged_at = NULL,
                   rule_status = 'pending',
                   custom_rule_id = NULL,
                   rule_notes = '',
                   rule_updated_by = NULL,
                   rule_updated_at = NULL
               WHERE id = ANY(%s)""",
            (clean_pks,),
        )
        return {
            "status": "ok",
            "count": len(clean_pks),
            "flag_color": None,
            "flagged_by": None,
            "summary": _flag_counts(conn, tenant),
        }

    if not auto_review:
        unreviewed = [
            r for r in rows
            if not r.get("is_reviewed") and not str(r.get("verdict") or "").strip()
        ]
        if unreviewed:
            raise HTTPException(
                status_code=400,
                detail="Alert harus berstatus direview / dianalisa sebelum dapat diberikan Flag.",
            )

    mapped_verdict = FLAG_TO_DEFAULT_VERDICT[flag_color]
    if auto_review:
        conn.execute(
            """UPDATE wazuh.alerts
               SET is_reviewed = true,
                   reviewed_at = COALESCE(reviewed_at, now()),
                   status = 'reviewed',
                   verdict = %s,
                   reviewed_by = %s,
                   claimed_by = COALESCE(claimed_by, %s),
                   reviewer_notes = CASE WHEN %s != '' THEN %s ELSE reviewer_notes END,
                   flag_color = %s,
                   flagged_by = %s,
                   flagged_at = now(),
                   rule_status = CASE WHEN %s = 'red' THEN 'pending' ELSE COALESCE(NULLIF(rule_status, ''), 'pending') END,
                   custom_rule_id = CASE WHEN %s = 'red' THEN NULL ELSE custom_rule_id END,
                   rule_notes = CASE WHEN %s = 'red' THEN '' ELSE rule_notes END,
                   rule_updated_by = CASE WHEN %s = 'red' THEN NULL ELSE rule_updated_by END,
                   rule_updated_at = CASE WHEN %s = 'red' THEN NULL ELSE rule_updated_at END
               WHERE id = ANY(%s)""",
            (
                mapped_verdict,
                actor,
                actor,
                reviewer_notes,
                reviewer_notes,
                flag_color,
                actor,
                flag_color,
                flag_color,
                flag_color,
                flag_color,
                flag_color,
                clean_pks,
            ),
        )
        if hasattr(db_module, "bump_daily_metrics"):
            per_tenant: dict[str, int] = {}
            for r in rows:
                if not r.get("is_reviewed"):
                    t_key = str(r.get("tenant") or "Default")
                    per_tenant[t_key] = per_tenant.get(t_key, 0) + 1
            for t_key, cnt in per_tenant.items():
                db_module.bump_daily_metrics(conn, t_key, reviewed_delta=cnt, verdict=mapped_verdict)
    else:
        conn.execute(
            """UPDATE wazuh.alerts
               SET flag_color = %s,
                   flagged_by = %s,
                   flagged_at = now(),
                   rule_status = CASE WHEN %s = 'red' THEN 'pending' ELSE COALESCE(NULLIF(rule_status, ''), 'pending') END,
                   custom_rule_id = CASE WHEN %s = 'red' THEN NULL ELSE custom_rule_id END,
                   rule_notes = CASE WHEN %s = 'red' THEN '' ELSE rule_notes END,
                   rule_updated_by = CASE WHEN %s = 'red' THEN NULL ELSE rule_updated_by END,
                   rule_updated_at = CASE WHEN %s = 'red' THEN NULL ELSE rule_updated_at END
               WHERE id = ANY(%s)""",
            (
                flag_color,
                actor,
                flag_color,
                flag_color,
                flag_color,
                flag_color,
                flag_color,
                clean_pks,
            ),
        )

    return {
        "status": "ok",
        "count": len(clean_pks),
        "flag_color": flag_color,
        "verdict": mapped_verdict,
        "flagged_by": actor,
        "summary": _flag_counts(conn, tenant),
    }


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
        with _savepoint(conn):
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
        a.status, a.claimed_by, a.claimed_at, a.verdict, a.reviewed_by,
        a.flag_color, a.flagged_by, a.flagged_at, a.rule_status, a.custom_rule_id, a.rule_notes, a.rule_updated_by, a.rule_updated_at"""
    if not summary:
        projection += """, a.data, a.raw, a.wazuh_ids, a.duplicate_instances,
        a.parsed_details, a.reviewer_notes,
        COALESCE(a.raw->>'full_log', '') AS full_log,
        COALESCE(a.raw->>'previous_output', '') AS previous_output"""

    with get_db() as conn:
        _expire_stale_claims(conn)
        # Exclusions apply to every Triage read, including explicit alert_ids from
        # a saved AI Triage correlation. Otherwise excluded alerts reappear.
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
            with _savepoint(conn):
                rows = conn.execute(sql, scoped_params + [limit, offset]).fetchall()
        except Exception:
            fallback_proj = projection.replace(
                ",\n        a.status, a.claimed_by, a.claimed_at, a.verdict, a.reviewed_by,\n        a.flag_color, a.flagged_by, a.flagged_at, a.rule_status, a.custom_rule_id, a.rule_notes, a.rule_updated_by, a.rule_updated_at",
                "",
            )
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
                    with _savepoint(conn):
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


def _update_alerts_review_state(
    conn,
    target_pks: list[int],
    *,
    is_reviewed: bool,
    notes: str,
    overwrite_notes: bool,
    verdict: str | None,
    flag_color: str | None,
    reviewer: str,
) -> None:
    """Update alert review/flag state without binding untyped NULL parameters on PostgreSQL."""
    if not target_pks:
        return

    if not is_reviewed:
        set_clauses = [
            "is_reviewed = false",
            "reviewed_at = NULL",
            "status = 'unread'",
            "verdict = NULL",
            "reviewed_by = NULL",
            "claimed_by = NULL",
            "claimed_at = NULL",
            "flag_color = NULL",
            "flagged_by = NULL",
            "flagged_at = NULL",
            "rule_status = 'pending'",
            "custom_rule_id = NULL",
            "rule_notes = ''",
            "rule_updated_by = NULL",
            "rule_updated_at = NULL",
        ]
        sql_params: list[Any] = []
        if overwrite_notes or notes:
            set_clauses.append("reviewer_notes = %s")
            sql_params.append(notes)
        sql_params.append(target_pks)
        try:
            with _savepoint(conn):
                conn.execute(
                    f"UPDATE wazuh.alerts SET {', '.join(set_clauses)} WHERE id = ANY(%s)",
                    tuple(sql_params),
                )
        except Exception:
            if overwrite_notes:
                conn.execute(
                    """UPDATE wazuh.alerts
                       SET is_reviewed = false,
                           reviewed_at = NULL,
                           reviewer_notes = %s
                       WHERE id = ANY(%s)""",
                    (notes, target_pks),
                )
            else:
                conn.execute(
                    """UPDATE wazuh.alerts
                       SET is_reviewed = false,
                           reviewed_at = NULL
                       WHERE id = ANY(%s)""",
                    (target_pks,),
                )
        return

    set_clauses = [
        "is_reviewed = true",
        "reviewed_at = now()",
        "status = 'reviewed'",
        "reviewed_by = %s",
        "claimed_by = COALESCE(claimed_by, %s)",
    ]
    sql_params = [reviewer, reviewer]
    if overwrite_notes or notes:
        set_clauses.append("reviewer_notes = %s")
        sql_params.append(notes)
    if verdict is not None:
        set_clauses.append("verdict = %s")
        sql_params.append(verdict)
    if flag_color is not None:
        set_clauses.extend([
            "flag_color = %s",
            "flagged_by = %s",
            "flagged_at = now()",
        ])
        sql_params.extend([flag_color, reviewer])
        if flag_color == "red":
            set_clauses.extend([
                "rule_status = 'pending'",
                "custom_rule_id = NULL",
                "rule_notes = ''",
                "rule_updated_by = NULL",
                "rule_updated_at = NULL",
            ])
    sql_params.append(target_pks)
    try:
        with _savepoint(conn):
            conn.execute(
                f"UPDATE wazuh.alerts SET {', '.join(set_clauses)} WHERE id = ANY(%s)",
                tuple(sql_params),
            )
    except Exception:
        if overwrite_notes:
            conn.execute(
                """UPDATE wazuh.alerts
                   SET is_reviewed = true,
                       reviewed_at = now(),
                       reviewer_notes = %s
                   WHERE id = ANY(%s)""",
                (notes, target_pks),
            )
        else:
            conn.execute(
                """UPDATE wazuh.alerts
                   SET is_reviewed = true,
                       reviewed_at = now()
                   WHERE id = ANY(%s)""",
                (target_pks,),
            )


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
    raw_flag = payload.get("flag_color")
    flag_color: str | None = None
    if raw_flag is not None and str(raw_flag).strip() != "":
        f_clean = str(raw_flag).strip().lower()
        if f_clean not in ALLOWED_FLAG_COLORS:
            raise HTTPException(status_code=400, detail="Flag harus berupa 'green', 'yellow', atau 'red'.")
        flag_color = f_clean
        if verdict is None:
            verdict = FLAG_TO_DEFAULT_VERDICT[flag_color]
    reviewer = str(payload.get("reviewed_by") or _current_username(request)).strip() or "analyst"
    new_status = "reviewed" if is_reviewed else "unread"
    with get_db() as conn:
        _validate_membership(conn, [alert_id], tenant)
        prev = conn.execute("SELECT tenant, is_reviewed FROM wazuh.alerts WHERE id = %s", (alert_id,)).fetchone()
        _update_alerts_review_state(
            conn,
            [alert_id],
            is_reviewed=is_reviewed,
            notes=notes,
            overwrite_notes=True,
            verdict=verdict,
            flag_color=flag_color,
            reviewer=reviewer,
        )
        if prev and is_reviewed and not prev.get("is_reviewed") and hasattr(db_module, "bump_daily_metrics"):
            db_module.bump_daily_metrics(conn, str(prev.get("tenant") or "Default"), reviewed_delta=1, verdict=verdict)
    return {"status": "ok", "id": alert_id, "is_reviewed": is_reviewed, "verdict": verdict if is_reviewed else None, "flag_color": flag_color if is_reviewed else None, "alert_status": new_status}


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
    raw_flag = payload.get("flag_color")
    flag_color: str | None = None
    if raw_flag is not None and str(raw_flag).strip() != "":
        f_clean = str(raw_flag).strip().lower()
        if f_clean not in ALLOWED_FLAG_COLORS:
            raise HTTPException(status_code=400, detail="Flag harus berupa 'green', 'yellow', atau 'red'.")
        flag_color = f_clean
        if verdict is None:
            verdict = FLAG_TO_DEFAULT_VERDICT[flag_color]
    notes = str(payload.get("reviewer_notes") or "").strip()
    reviewer = str(payload.get("reviewed_by") or _current_username(request)).strip() or "analyst"
    new_status = "reviewed" if is_reviewed else "unread"
    if not alert_ids:
        raise HTTPException(status_code=400, detail="No valid alert IDs provided.")
    with get_db() as conn:
        clean_pks = _validate_membership(conn, alert_ids, tenant)
        _update_alerts_review_state(
            conn,
            clean_pks,
            is_reviewed=is_reviewed,
            notes=notes,
            overwrite_notes=False,
            verdict=verdict,
            flag_color=flag_color,
            reviewer=reviewer,
        )
        if is_reviewed and hasattr(db_module, "bump_daily_metrics"):
            db_module.bump_daily_metrics(conn, _tenant_label(tenant), reviewed_delta=len(clean_pks), verdict=verdict)
    return {"status": "ok", "count": len(clean_pks), "is_reviewed": is_reviewed, "verdict": verdict if is_reviewed else None, "flag_color": flag_color if is_reviewed else None, "alert_status": new_status}


@app.post("/api/alerts/bulk-verdict-pattern")
def bulk_verdict_by_pattern(
    payload: dict[str, Any],
    request: Request,
    tenant: list[str] = Query(default=["all"]),
):
    """Bulk Actions & Pattern Grouping: apply Flag (green/yellow/red) or legacy verdict across matching alerts."""
    normalize_tenants(tenant)
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Payload bulk pola tidak valid.")
    raw_flag = str(payload.get("flag_color") or "").strip().lower()
    raw_verdict = str(payload.get("verdict") or "").strip().lower()
    flag_color: str | None = None
    if raw_flag:
        if raw_flag not in ALLOWED_FLAG_COLORS:
            raise HTTPException(status_code=400, detail="Flag wajib dipilih: 'green', 'yellow', atau 'red'.")
        flag_color = raw_flag
        if raw_verdict not in {"tp", "fp", "benign"}:
            raw_verdict = FLAG_TO_DEFAULT_VERDICT[flag_color]
    elif raw_verdict not in {"tp", "fp", "benign"}:
        raise HTTPException(status_code=400, detail="Pilih Flag ('green', 'yellow', 'red') atau verdict ('tp', 'fp', 'benign').")

    dry_run = bool(payload.get("dry_run", False))
    rule_id = str(payload.get("rule_id") or "").strip()
    description = str(payload.get("description") or "").strip()
    source_ip = str(payload.get("source_ip") or "").strip()
    agent_name = str(payload.get("agent_name") or "").strip()
    q = str(payload.get("q") or "").strip()
    only_unreviewed = bool(payload.get("only_unreviewed", True))
    default_label = f"Flag {flag_color.upper()}" if flag_color else raw_verdict.upper()
    notes = str(payload.get("reviewer_notes") or f"Bulk pattern: {default_label}").strip()
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
                "flag_color": flag_color,
            }
        if flag_color:
            conn.execute(
                """UPDATE wazuh.alerts
                   SET is_reviewed = true,
                       reviewed_at = now(),
                       status = 'reviewed',
                       verdict = %s,
                       reviewed_by = %s,
                       reviewer_notes = %s,
                       flag_color = %s,
                       flagged_by = %s,
                       flagged_at = now(),
                       rule_status = 'pending',
                       custom_rule_id = NULL,
                       rule_notes = '',
                       rule_updated_by = NULL,
                       rule_updated_at = NULL
                   WHERE id = ANY(%s)""",
                (raw_verdict, reviewer, notes, flag_color, reviewer, pks),
            )
        else:
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
        "flag_color": flag_color,
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
            """SELECT a.id, a.alert_id, a.tenant, a.description, a.source_ip, a.agent_name,
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


@app.post("/api/intel/sidecar/test")
def api_intel_sidecar_test(payload: dict[str, Any]):
    """Read-only probe of the configured HTTP IP Intel Sidecar (/ip-intel)."""
    ip = normalize_ip_address(str(payload.get("ip") or "8.8.8.8"))
    if not is_valid_ip(ip):
        raise HTTPException(status_code=400, detail="Masukkan alamat IPv4/IPv6 yang valid untuk diuji.")

    raw_override = payload.get("sidecar_url")
    if raw_override is not None and str(raw_override).strip() != "":
        try:
            validated = normalize_sidecar_urls(raw_override)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        candidates = parse_sidecar_candidates(validated)
    else:
        with get_db() as conn:
            stored = load_settings(conn)
        saved_url = str((stored.get("intel") or {}).get("sidecar_url") or "")
        candidates = parse_sidecar_candidates(saved_url)

    if not candidates:
        return {
            "ok": False,
            "configured": False,
            "connected": False,
            "ip": ip,
            "error": "URL Sidecar IP Intel belum diatur.",
        }

    probe = probe_sidecar(candidates, [ip])
    if not probe.get("connected"):
        return {
            "ok": False,
            "configured": True,
            "connected": False,
            "active_url": None,
            "ip": ip,
            "error": probe.get("error") or "Sidecar IP Intel tidak dapat dihubungi.",
        }

    active_url = str(probe.get("url") or "")
    cached_map = probe.get("cached") if isinstance(probe.get("cached"), dict) else {}
    entry = cached_map.get(ip)
    if has_usable_sidecar_cache(entry):
        norm = normalize_sidecar_record(ip, entry, active_url)
        return {
            "ok": True,
            "configured": True,
            "connected": True,
            "found": True,
            "active_url": active_url,
            "ip": ip,
            "abuse_score": norm.get("abuse_score"),
            "vt_malicious": norm.get("vt_malicious"),
            "isp": norm.get("isp"),
            "country_code": norm.get("country_code"),
            "reputation_source": norm.get("reputation_source"),
            "cached_entries": len(cached_map),
            "error": None,
        }

    return {
        "ok": True,
        "configured": True,
        "connected": True,
        "found": False,
        "active_url": active_url,
        "ip": ip,
        "cached_entries": len(cached_map),
        "error": None,
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
    else:
        alert_ids = list(alert_ids)
    single_alert_id = payload.get("alert_id")
    if single_alert_id is not None and str(single_alert_id).strip() != "":
        alert_ids.append(single_alert_id)

    target_ips: list[str] = []
    for raw in raw_ips:
        norm_ip = normalize_ip_address(str(raw))
        if norm_ip and norm_ip not in target_ips:
            target_ips.append(norm_ip)

    alert_context: dict[str, Any] | None = None
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
                    f"""SELECT a.source_ip, a.agent_name, a.description, a.data,
                               a.mitre_ids, a.parsed_details,
                               COALESCE(a.raw->>'full_log', '') AS full_log
                        FROM wazuh.alerts a {where_clause}""",
                    params,
                ).fetchall()
                for r in rows:
                    ip_val = normalize_ip_address(str(r.get("source_ip") or ""))
                    if ip_val and ip_val not in target_ips:
                        target_ips.append(ip_val)
                if rows:
                    alert_context = extract_alert_intel_context(rows)

    unique_ips = list(dict.fromkeys(ip for ip in target_ips if is_valid_ip(ip)))[:50]
    if not unique_ips:
        raise HTTPException(status_code=400, detail="Tidak ada alamat IPv4/IPv6 valid yang diberikan untuk di-enrich.")

    with get_db() as conn:
        stored_settings = load_settings(conn)
        stored_abuse_key = intel_abuseipdb_key(stored_settings)
        stored_vt_key = intel_virustotal_key(stored_settings)
        intel_cfg = stored_settings.get("intel") or {}
        stored_sidecar_url = str(intel_cfg.get("sidecar_url") or "")
        stored_sidecar_writeback = bool(intel_cfg.get("sidecar_writeback", True))
        results, enrich_stats = enrich_ips_with_sidecar(
            unique_ips,
            abuseipdb_api_key=stored_abuse_key,
            virustotal_api_key=stored_vt_key,
            sidecar_url=stored_sidecar_url,
            sidecar_writeback=stored_sidecar_writeback,
            context=alert_context,
            single_enrich_fn=enrich_ip,
        )
        for res in results:
            if res.get("status") not in ("invalid", "error"):
                upsert_ip_cache(conn, res)
        if hasattr(conn, "commit"):
            conn.commit()

    sync_remote_cache(results)

    return {
        "status": "ok",
        "count": len(results),
        "enriched": results,
        "stats": enrich_stats,
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
        # Global exclusions must hide excluded alerts even for explicit alert_ids.
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


REVIEWER_IDENTITY_SQL = (
    "COALESCE(NULLIF(a.reviewed_by, ''), NULLIF(a.flagged_by, ''), NULLIF(a.claimed_by, ''), 'admin')"
)


def _review_activity_payload(
    conn,
    tenant: list[str],
    offset: int,
    days: int = 14,
    reviewer: str | None = None,
) -> dict[str, Any]:
    """Count reviewed alerts per local calendar day for a connection.

    ``reviewer`` limits the counts to alerts whose review identity matches the
    selected account; an empty value keeps the whole team in scope.
    """
    window = max(days, 30)
    now_local = datetime.now(timezone.utc) + timedelta(minutes=offset)
    today = now_local.date()
    start_date = today - timedelta(days=window - 1)
    start_local = datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc)
    since_utc = (start_local - timedelta(minutes=offset)).isoformat()

    selected_reviewer = str(reviewer or "").strip()
    reviewer_sql = f" AND {REVIEWER_IDENTITY_SQL} = %s" if selected_reviewer else ""

    where = "a.reviewed_at IS NOT NULL AND a.reviewed_at >= %s"
    params: list[Any] = [since_utc]
    tenant_sql, tenant_params = tenant_clause("a", tenant)
    if tenant_sql:
        where += " AND " + tenant_sql
        params.extend(tenant_params)
    if selected_reviewer:
        where += reviewer_sql
        params.append(selected_reviewer)

    rows = conn.execute(
        f"SELECT a.reviewed_at FROM wazuh.alerts a WHERE {where}",
        params,
    ).fetchall()
    total_where = "a.reviewed_at IS NOT NULL"
    total_params: list[Any] = []
    if tenant_sql:
        total_where += f" AND {tenant_sql}"
        total_params.extend(tenant_params)
    if selected_reviewer:
        total_where += reviewer_sql
        total_params.append(selected_reviewer)
    reviewed_row = conn.execute(
        f"SELECT COUNT(*) AS n FROM wazuh.alerts a WHERE {total_where}",
        total_params,
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


@app.get("/api/reviews/activity")
def review_activity(
    tenant: list[str] = Query(default=["all"]),
    days: int = 14,
    tz_offset_minutes: int = 0,
):
    """Reviewed-alert counts per local calendar day.

    ``tz_offset_minutes`` is the client's UTC offset in minutes (WIB = 420), so
    "today" follows the analyst's wall clock rather than the server's UTC date.
    """
    if not (1 <= days <= 90):
        raise HTTPException(status_code=422, detail="days must be between 1 and 90.")
    offset = max(-840, min(840, int(tz_offset_minutes or 0)))
    with get_db() as conn:
        return _review_activity_payload(conn, tenant, offset, days)


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


def _safe_saved_filters(raw: Any) -> list[dict[str, str]]:
    """Decode persisted AI triage filters without failing on legacy state."""
    try:
        return parse_filters(raw)
    except HTTPException:
        return []


def _build_ai_triage_where(
    tenant: Any,
    review_status: str,
    min_rule_level: int,
    max_rule_level: int | None,
    filters: Any = None,
) -> tuple[str, list[Any]]:
    where, params = alert_where(tenant=tenant, review_status=review_status, filters=filters)
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


AI_TRIAGE_DEFAULT_BATCH = 500
AI_TRIAGE_MAX_BATCH = 5000


def _ai_triage_scope_signature(
    tenant: Any,
    review_status: str,
    min_rule_level: int,
    max_rule_level: int | None,
    group_by: str,
    filters: list[dict[str, str]] | None = None,
) -> str:
    """Stable identity for one triage scope; progress is only reused within it."""
    return json.dumps({
        "tenant": sorted(str(item) for item in (tenant or ["all"])),
        "review_status": review_status,
        "min_rule_level": min_rule_level,
        "max_rule_level": max_rule_level,
        "group_by": group_by,
        "filters": filters or [],
    }, sort_keys=True)


def _ai_triage_batch_size(value: Any, fallback: int = AI_TRIAGE_DEFAULT_BATCH) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return fallback
    return max(1, min(AI_TRIAGE_MAX_BATCH, number))


def _ai_triage_progress(state: Any, scope_signature: str) -> tuple[list[int], dict[str, Any] | None]:
    """Return processed alert pks for this exact scope, plus the stored progress."""
    if not isinstance(state, dict):
        return [], None
    progress = state.get("progress")
    if not isinstance(progress, dict) or progress.get("scope") != scope_signature:
        return [], None
    processed = sorted({
        int(aid) for aid in (progress.get("processed_ids") or [])
        if str(aid).isdigit()
    })
    return processed, progress


def _ai_triage_exclude_ids(
    where: str,
    params: list[Any],
    excluded: list[int],
) -> tuple[str, list[Any]]:
    """Add a NOT IN guard so a batch only sees alerts not processed yet."""
    if not excluded:
        return where, params
    clause = "NOT (a.id = ANY(%s))"
    where = f"{where} AND {clause}" if where else f"WHERE {clause}"
    return where, [*params, excluded]


def _ai_triage_candidate_count(conn, where: str, params: list[Any]) -> int:
    row = conn.execute(f"SELECT count(*) AS n FROM wazuh.alerts a {where}", params).fetchone()
    return int(row["n"]) if row else 0


def _ai_triage_state_candidates(conn, norm_tenants: list[str]) -> list[tuple[str, dict[str, Any]]]:
    """All persisted triage states relevant to a request, newest-compatible first."""
    keys = [get_triage_state_key(norm_tenants), AI_TRIAGE_STATE_KEY]
    pointer = load_document(conn, AI_TRIAGE_LAST_KEY, None)
    if isinstance(pointer, dict) and str(pointer.get("key") or ""):
        keys.append(str(pointer["key"]))
    candidates: list[tuple[str, dict[str, Any]]] = []
    seen: set[str] = set()
    for key in keys:
        if key in seen:
            continue
        seen.add(key)
        state = load_document(conn, key, None)
        if isinstance(state, dict) and isinstance(state.get("options"), dict):
            candidates.append((key, state))
    return candidates


def _ai_triage_pick_state(conn, norm_tenants: list[str]) -> tuple[str, dict[str, Any] | None]:
    candidates = _ai_triage_state_candidates(conn, norm_tenants)
    if not candidates:
        return "", None
    exact_key = get_triage_state_key(norm_tenants)
    requested = {str(t) for t in norm_tenants}

    def covers(state: dict[str, Any]) -> bool:
        saved = {str(t) for t in ((state.get("options") or {}).get("tenant") or ["all"])}
        return "all" in saved or requested.issubset(saved)

    covering = [item for item in candidates if covers(item[1])] or candidates

    def rank(item: tuple[str, dict[str, Any]]) -> tuple[str, int]:
        key, state = item
        return str(state.get("saved_at") or ""), 1 if key == exact_key else 0

    return max(covering, key=rank)


def _ai_triage_state_matches(state: dict[str, Any], norm_tenants: list[str]) -> bool:
    options = state.get("options") or {}
    saved = options.get("tenant") or ["all"]
    return sorted(str(t) for t in saved) == sorted(str(t) for t in norm_tenants)


def _remember_triage_state(conn, state_key: str, state: dict[str, Any]) -> None:
    save_document(conn, AI_TRIAGE_LAST_KEY, {
        "key": state_key,
        "tenant": (state.get("options") or {}).get("tenant"),
        "saved_at": state.get("saved_at"),
    })


def _ai_triage_read_only(conn, state: dict[str, Any], norm_tenants: list[str]) -> dict[str, Any]:
    """Render a saved result for a different tenant scope without rewriting it.

    Groups are narrowed to the requested tenants so opening a tenant after an
    all-tenant run shows that tenant's share of the same saved result.
    """
    options = state.get("options") or {}
    saved_filters = _safe_saved_filters(options.get("filters"))
    options_out = {**options, "filters": saved_filters}
    group_list = state.get("groups") if isinstance(state.get("groups"), list) else []
    saved_ids = [int(aid) for aid in (state.get("alert_ids") or []) if str(aid).isdigit()]
    wanted_ids = {int(aid) for g in group_list for aid in (g.get("alert_ids") or []) if str(aid).isdigit()}
    wanted_ids.update(saved_ids)
    rows: list[Any] = []
    if wanted_ids:
        t_clause, t_params = tenant_clause("a", norm_tenants)
        id_where = f"WHERE a.id = ANY(%s){f' AND {t_clause}' if t_clause else ''}"
        id_params: list[Any] = [sorted(wanted_ids), *t_params]
        filter_sql, filter_params = build_filter_sql(saved_filters)
        if filter_sql:
            id_where += f" AND {filter_sql}"
            id_params.extend(filter_params)
        id_where, id_params = with_exclusions(id_where, id_params, _exclusion_document(conn))
        rows = conn.execute(
            f"""SELECT a.id, a.alert_id, a.timestamp, a.tenant, a.agent_name, a.agent_ip,
                       a.rule_id, a.rule_level, a.description, a.rule_groups, a.source_ip,
                       a.mitre_ids, a.cve, a.hit_count, a.log_signature, a.parsed_details,
                       a.data, COALESCE(a.raw->>'full_log', '') AS full_log
                FROM wazuh.alerts a {id_where}
                ORDER BY a.rule_level DESC NULLS LAST, a.timestamp DESC NULLS LAST, a.id DESC""",
            id_params,
        ).fetchall()
    by_id = {str(r["id"]): {**r, "id": str(r["id"])} for r in rows}
    groups: list[dict[str, Any]] = []
    for group in group_list:
        if not isinstance(group, dict):
            continue
        ids = [aid for aid in (group.get("alert_ids") or []) if str(aid) in by_id]
        if not ids:
            continue
        groups.append({**group, "alert_ids": ids, "alert_count": len(ids)})
    final_ids = list(dict.fromkeys(aid for g in groups for aid in g["alert_ids"]))
    final_alerts = [by_id[aid] for aid in final_ids if aid in by_id]
    group_by = str(options.get("group_by") or "rule_description")
    return {
        "saved": True,
        "read_only": True,
        "options": options_out,
        "progress": None,
        "result": {
            "mode": str(state.get("mode") or "local_rules"),
            "warning": state.get("warning"),
            "model": state.get("model"),
            "alert_count": len(final_alerts),
            "min_rule_level": int(options.get("min_rule_level") or 7),
            "max_rule_level": options.get("max_rule_level"),
            "group_by": group_by,
            "filters": saved_filters,
            "saved_at": state.get("saved_at"),
            "window_key": state.get("window_key"),
            "progress": None,
            "alerts": safe_alerts(final_alerts, limit=max(len(final_alerts), 1)),
            "groups": groups,
        },
    }


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
    with get_db() as conn:
        state_key, state = _ai_triage_pick_state(conn, norm_tenants)
        if not isinstance(state, dict) or not isinstance(state.get("options"), dict):
            return {"saved": False, "result": None}
        if not _ai_triage_state_matches(state, norm_tenants):
            return _ai_triage_read_only(conn, state, norm_tenants)
        options = state["options"]
        tenant = options.get("tenant") or ["all"]
        try:
            limit = max(1, min(100000, int(options.get("limit") or 40)))
            min_rule_level = max(0, min(16, int(options.get("min_rule_level") if options.get("min_rule_level") is not None else 7)))
        except (TypeError, ValueError):
            limit, min_rule_level = 40, 7
        raw_max = options.get("max_rule_level")
        max_rule_level = int(raw_max) if raw_max is not None and str(raw_max).strip() != "" else None
        review_status = str(options.get("review_status") or "unreviewed")
        group_by = str(options.get("group_by") or "rule_description")
        if group_by not in {"host_rule", "rule_description", "indicator"}:
            group_by = "rule_description"
        saved_filters = _safe_saved_filters(options.get("filters"))
        batch_size = _ai_triage_batch_size(options.get("batch_size"))
        scope_sig = _ai_triage_scope_signature(
            options.get("tenant") or ["all"], review_status, min_rule_level, max_rule_level, group_by,
            filters=saved_filters,
        )
        processed_ids, progress_state = _ai_triage_progress(state, scope_sig)

        excl_doc = _exclusion_document(conn)
        saved_ids = [int(aid) for aid in (state.get("alert_ids") or []) if str(aid).isdigit()]
        existing_rows: list[dict[str, Any]] = []
        if saved_ids:
            t_clause, t_params = tenant_clause("a", tenant)
            id_where = f"WHERE a.id = ANY(%s){f' AND {t_clause}' if t_clause else ''}"
            id_params: list[Any] = [saved_ids, *t_params]
            filter_sql, filter_params = build_filter_sql(saved_filters)
            if filter_sql:
                id_where += f" AND {filter_sql}"
                id_params.extend(filter_params)
            id_where, id_params = with_exclusions(id_where, id_params, excl_doc)
            existing_rows = conn.execute(
                f"""SELECT a.id, a.alert_id, a.timestamp, a.tenant, a.agent_name, a.agent_ip,
                           a.rule_id, a.rule_level, a.description, a.rule_groups, a.source_ip,
                           a.mitre_ids, a.cve, a.hit_count, a.log_signature, a.parsed_details,
                           a.data, COALESCE(a.raw->>'full_log', '') AS full_log
                    FROM wazuh.alerts a {id_where}
                    ORDER BY a.rule_level DESC NULLS LAST, a.timestamp DESC NULLS LAST, a.id DESC""",
                id_params,
            ).fetchall()

        base_where, base_params = _build_ai_triage_where(
            tenant, review_status, min_rule_level, max_rule_level, filters=saved_filters,
        )
        base_where, base_params = with_exclusions(base_where, base_params, excl_doc)
        total = int(progress_state.get("total") or 0) if progress_state else 0
        if total <= 0:
            total = _ai_triage_candidate_count(conn, base_where, base_params)
        chunk = max(1, min(limit, batch_size))
        candidate_where, candidate_params = _ai_triage_exclude_ids(
            base_where, base_params, sorted(set(processed_ids) | set(saved_ids)),
        )
        candidate_rows = conn.execute(
            f"""SELECT a.id, a.alert_id, a.timestamp, a.tenant, a.agent_name, a.agent_ip,
                       a.rule_id, a.rule_level, a.description, a.rule_groups, a.source_ip,
                       a.mitre_ids, a.cve, a.hit_count, a.log_signature, a.parsed_details,
                       a.data, COALESCE(a.raw->>'full_log', '') AS full_log
                FROM wazuh.alerts a {candidate_where}
                ORDER BY a.rule_level DESC NULLS LAST, a.timestamp DESC NULLS LAST, a.id DESC
                LIMIT %s""",
            [*candidate_params, chunk],
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
        final_ids = list(dict.fromkeys(
            aid for g in groups for aid in (g.get("alert_ids") or []) if aid in existing_map
        ))
        final_ids_set = set(final_ids)
        final_alerts = [a for a in all_alerts if a["id"] in final_ids_set] or all_alerts
        processed_new = sorted({
            *processed_ids,
            *saved_ids,
            *(int(aid) for aid in final_ids if str(aid).isdigit()),
        })
        total = max(total, len(processed_new))
        remaining = max(0, total - len(processed_new))
        done = len(new_alerts) < chunk or remaining <= 0
        progress_payload = {
            "processed": len(processed_new),
            "total": total,
            "remaining": remaining,
            "done": done,
            "batch_size": chunk,
        }

        updated_state = {
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "window_key": current_wib_window_key(),
            "options": {
                "tenant": list(normalize_tenants(tenant)) or ["all"],
                "limit": limit,
                "batch_size": batch_size,
                "min_rule_level": min_rule_level,
                "max_rule_level": max_rule_level,
                "review_status": review_status,
                "group_by": group_by,
                "filters": saved_filters,
            },
            "mode": mode,
            "warning": warning,
            "model": ai.get("model"),
            "alert_ids": list(dict.fromkeys(a["id"] for a in final_alerts)),
            "groups": groups,
            "progress": {
                "scope": scope_sig,
                "processed_ids": processed_new,
                "total": total,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            },
        }
        save_document(conn, get_triage_state_key(norm_tenants), updated_state)
        _remember_triage_state(conn, get_triage_state_key(norm_tenants), updated_state)

    return {
        "saved": True,
        "options": updated_state["options"],
        "progress": progress_payload,
        "result": {
            "mode": mode,
            "warning": warning,
            "model": ai.get("model"),
            "alert_count": len(final_alerts),
            "min_rule_level": min_rule_level,
            "max_rule_level": max_rule_level,
            "group_by": group_by,
            "filters": saved_filters,
            "saved_at": updated_state["saved_at"],
            "window_key": updated_state["window_key"],
            "progress": progress_payload,
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
    if group_by not in {"host_rule", "rule_description", "indicator"}:
        raise HTTPException(status_code=400, detail="group_by harus berupa 'host_rule', 'rule_description', atau 'indicator'.")

    tenant = payload.get("tenant") or ["all"]
    review_status = str(payload.get("review_status") or "unreviewed")
    norm_tenants = list(normalize_tenants(tenant)) or ["all"]
    parsed_filters = parse_filters(payload.get("filters"))

    raw_batch = payload.get("batch_size")
    batch_size: int | None = None
    if raw_batch is not None and str(raw_batch).strip() != "":
        try:
            batch_size = int(raw_batch)
        except (TypeError, ValueError):
            raise HTTPException(status_code=400, detail="batch_size harus berupa angka.") from None
        if not 1 <= batch_size <= AI_TRIAGE_MAX_BATCH:
            raise HTTPException(
                status_code=400,
                detail=f"batch_size harus antara 1 dan {AI_TRIAGE_MAX_BATCH}.",
            )
    resume = bool(payload.get("resume"))

    scope_sig = _ai_triage_scope_signature(
        norm_tenants, review_status, min_rule_level, max_rule_level, group_by,
        filters=parsed_filters,
    )
    chunk = limit if batch_size is None else min(batch_size, limit)
    with get_db() as conn:
        state_key = get_triage_state_key(norm_tenants)
        prev_state = load_document(conn, state_key, None)
        if prev_state is None and state_key != AI_TRIAGE_STATE_KEY:
            prev_state = load_document(conn, AI_TRIAGE_STATE_KEY, None)

        same_scope = False
        prev_groups: list[dict[str, Any]] = []
        processed_ids: list[int] = []
        progress_state: dict[str, Any] | None = None
        if isinstance(prev_state, dict) and isinstance(prev_state.get("options"), dict):
            prev_opts = prev_state["options"]
            same_scope = (
                sorted(str(t) for t in (prev_opts.get("tenant") or ["all"])) == sorted(norm_tenants)
                and prev_opts.get("min_rule_level") == min_rule_level
                and prev_opts.get("max_rule_level") == max_rule_level
                and str(prev_opts.get("review_status") or "unreviewed") == review_status
                and str(prev_opts.get("group_by") or "host_rule") == group_by
                and _safe_saved_filters(prev_opts.get("filters")) == parsed_filters
            )
            if same_scope:
                prev_groups = prev_state.get("groups") if isinstance(prev_state.get("groups"), list) else []
                if resume:
                    processed_ids, progress_state = _ai_triage_progress(prev_state, scope_sig)

        base_where, base_params = _build_ai_triage_where(
            tenant, review_status, min_rule_level, max_rule_level, filters=parsed_filters,
        )
        base_where, base_params = with_exclusions(base_where, base_params, _exclusion_document(conn))
        total = int(progress_state.get("total") or 0) if progress_state else 0
        if total <= 0:
            total = _ai_triage_candidate_count(conn, base_where, base_params)

        chunk_where, chunk_params = _ai_triage_exclude_ids(base_where, base_params, processed_ids)
        rows = conn.execute(
            f"""SELECT a.id, a.alert_id, a.timestamp, a.tenant, a.agent_name, a.agent_ip,
                       a.rule_id, a.rule_level, a.description, a.rule_groups, a.source_ip,
                       a.mitre_ids, a.cve, a.hit_count, a.log_signature, a.parsed_details,
                       a.data, COALESCE(a.raw->>'full_log', '') AS full_log
                FROM wazuh.alerts a {chunk_where}
                ORDER BY a.rule_level DESC NULLS LAST, a.timestamp DESC NULLS LAST, a.id DESC
                LIMIT %s""",
            [*chunk_params, chunk],
        ).fetchall()
        stored = load_settings(conn)

        rows_map = {str(row["id"]): {**row, "id": str(row["id"])} for row in rows}
        new_alerts = list(rows_map.values())
        alerts_map = dict(rows_map)

        if same_scope:
            needed: set[int] = {
                int(aid) for aid in (prev_state.get("alert_ids") or [])
                if str(aid).isdigit()
            }
            for group in prev_groups:
                needed.update(
                    int(aid) for aid in (group.get("alert_ids") or []) if str(aid).isdigit()
                )
            missing_pks = sorted(needed - {int(aid) for aid in alerts_map})
            if missing_pks:
                extra_rows = conn.execute(
                    f"""SELECT a.id, a.alert_id, a.timestamp, a.tenant, a.agent_name, a.agent_ip,
                               a.rule_id, a.rule_level, a.description, a.rule_groups, a.source_ip,
                               a.mitre_ids, a.cve, a.hit_count, a.log_signature, a.parsed_details,
                               a.data, COALESCE(a.raw->>'full_log', '') AS full_log
                        FROM wazuh.alerts a {base_where} AND a.id = ANY(%s)""",
                    [*base_params, missing_pks],
                ).fetchall()
                for r in extra_rows:
                    alerts_map[str(r["id"])] = {**r, "id": str(r["id"])}

        ai = stored.get("ai", {})
        if new_alerts:
            fresh_groups, mode, warning = triage_with_fallback(
                new_alerts,
                enabled=bool(ai.get("enabled")),
                model=str(ai.get("model") or ""),
                base_url=str(ai.get("base_url") or "http://127.0.0.1:11434"),
                timeout=float(ai.get("timeout_seconds") or 90),
                group_by=group_by,
            )
        else:
            fresh_groups, mode, warning = [], str(prev_state.get("mode") or "local_rules"), None
        if same_scope and prev_groups and (not new_alerts or mode == prev_state.get("mode")):
            groups = merge_triage_groups(prev_groups, fresh_groups, alerts_map)
            if not new_alerts:
                mode = str(prev_state.get("mode") or mode)
                warning = prev_state.get("warning")
        else:
            groups = fresh_groups

        _sync_triage_groups_with_saved_incidents(conn, groups, alerts_map)

        if not ai.get("enabled") and not warning:
            warning = "AI Triage belum diaktifkan di Pengaturan; hasil memakai heuristik lokal."

        final_ids = list(dict.fromkeys(
            aid for g in groups for aid in (g.get("alert_ids") or []) if aid in alerts_map
        ))
        missing_final = [int(aid) for aid in final_ids if aid not in alerts_map]
        if missing_final:
            extra_rows = conn.execute(
                f"""SELECT a.id, a.alert_id, a.timestamp, a.tenant, a.agent_name, a.agent_ip,
                           a.rule_id, a.rule_level, a.description, a.rule_groups, a.source_ip,
                           a.mitre_ids, a.cve, a.hit_count, a.log_signature, a.parsed_details,
                           a.data, COALESCE(a.raw->>'full_log', '') AS full_log
                    FROM wazuh.alerts a {base_where} AND a.id = ANY(%s)""",
                [*base_params, missing_final],
            ).fetchall()
            for r in extra_rows:
                alerts_map[str(r["id"])] = {**r, "id": str(r["id"])}
        final_alerts = [alerts_map[aid] for aid in final_ids if aid in alerts_map]

        processed_new = sorted({
            *processed_ids,
            *(int(aid) for aid in final_ids if str(aid).isdigit()),
            *(int(a["id"]) for a in new_alerts if str(a["id"]).isdigit()),
        })
        total = max(total, len(processed_new))
        remaining = max(0, total - len(processed_new))
        done = len(rows) < chunk or remaining <= 0
        progress_payload = {
            "processed": len(processed_new),
            "total": total,
            "remaining": remaining,
            "done": done,
            "batch_size": chunk,
        }

        saved_state = {
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "window_key": current_wib_window_key(),
            "options": {
                "tenant": norm_tenants,
                "limit": limit,
                "batch_size": batch_size or AI_TRIAGE_DEFAULT_BATCH,
                "min_rule_level": min_rule_level,
                "max_rule_level": max_rule_level,
                "review_status": review_status,
                "group_by": group_by,
                "filters": parsed_filters,
            },
            "mode": mode,
            "warning": warning,
            "model": ai.get("model"),
            "alert_ids": list(dict.fromkeys(a["id"] for a in final_alerts)),
            "groups": groups,
            "progress": {
                "scope": scope_sig,
                "processed_ids": processed_new,
                "total": total,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            },
        }
        save_document(conn, state_key, saved_state)
        _remember_triage_state(conn, state_key, saved_state)

    return {
        "mode": mode,
        "warning": warning,
        "model": ai.get("model"),
        "alert_count": len(final_alerts),
        "min_rule_level": min_rule_level,
        "max_rule_level": max_rule_level,
        "group_by": group_by,
        "filters": parsed_filters,
        "saved_at": saved_state["saved_at"],
        "window_key": saved_state["window_key"],
        "progress": progress_payload,
        "alerts": safe_alerts(final_alerts, limit=max(limit, len(final_alerts))),
        "groups": groups,
    }


@app.post("/api/ai/triage/remove")
def api_ai_triage_remove(payload: dict[str, Any]):
    """Dismiss one or more AI correlation groups from the persisted triage result.

    Removed alerts stay marked as processed so a resume does not recreate the
    dismissed correlation; a fresh triage run will group them again.
    """
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Payload hapus korelasi tidak valid.")
    raw_keys = payload.get("group_keys")
    if isinstance(raw_keys, str):
        raw_keys = [raw_keys]
    clean_keys = {
        str(key).strip() for key in raw_keys
        if str(key).strip()
    } if isinstance(raw_keys, list) else set()
    raw_titles = payload.get("group_titles")
    if isinstance(raw_titles, str):
        raw_titles = [raw_titles]
    clean_titles = {
        str(title).strip() for title in raw_titles
        if str(title).strip()
    } if isinstance(raw_titles, list) else set()
    if not clean_keys and not clean_titles:
        raise HTTPException(status_code=400, detail="group_keys atau group_titles harus berisi minimal satu grup.")

    tenant = payload.get("tenant") or ["all"]
    norm_tenants = list(normalize_tenants(tenant)) or ["all"]
    removed = 0
    with get_db() as conn:
        state_key, state = _ai_triage_pick_state(conn, norm_tenants)
        if not isinstance(state, dict) or not isinstance(state.get("groups"), list):
            raise HTTPException(status_code=404, detail="Belum ada hasil AI Triage yang bisa diubah.")
        kept: list[dict[str, Any]] = []
        for group in state["groups"]:
            if not isinstance(group, dict):
                continue
            key = str(group.get("group_key") or "").strip()
            title = str(group.get("title") or "").strip()
            if (key and key in clean_keys) or (title and title in clean_titles):
                removed += 1
                continue
            kept.append(group)
        if not removed:
            raise HTTPException(status_code=404, detail="Grup korelasi tidak ditemukan pada hasil tersimpan.")
        final_ids = [aid for group in kept for aid in (group.get("alert_ids") or [])]
        state["groups"] = kept
        state["alert_ids"] = list(dict.fromkeys(final_ids))
        state["saved_at"] = datetime.now(timezone.utc).isoformat()
        save_document(conn, state_key, state)
        _remember_triage_state(conn, state_key, state)
    return {"removed": removed, "group_count": len(kept)}


@app.post("/api/ai/triage/alerts/remove")
def api_ai_triage_remove_alerts(payload: dict[str, Any]):
    """Remove specific alerts from saved AI correlation groups.

    The alerts stay marked as processed so a resumed batch does not re-add them.
    """
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Payload hapus alert tidak valid.")
    raw_ids = payload.get("alert_ids")
    if not isinstance(raw_ids, list) or not raw_ids:
        raise HTTPException(status_code=400, detail="alert_ids harus berisi minimal satu alert.")
    try:
        alert_ids = positive_ids(raw_ids)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if not alert_ids:
        raise HTTPException(status_code=400, detail="alert_ids harus berisi minimal satu alert.")
    remove_ids = {str(pk) for pk in alert_ids}

    tenant = payload.get("tenant") or ["all"]
    norm_tenants = list(normalize_tenants(tenant)) or ["all"]
    removed = 0
    with get_db() as conn:
        state_key, state = _ai_triage_pick_state(conn, norm_tenants)
        if not isinstance(state, dict) or not isinstance(state.get("groups"), list):
            raise HTTPException(status_code=404, detail="Belum ada hasil AI Triage yang bisa diubah.")
        kept: list[dict[str, Any]] = []
        removed_ids: set[str] = set()
        for group in state["groups"]:
            if not isinstance(group, dict):
                continue
            ids = [str(aid) for aid in (group.get("alert_ids") or [])]
            kept_ids = [aid for aid in ids if aid not in remove_ids]
            removed_ids.update(set(ids) - set(kept_ids))
            if not kept_ids:
                continue
            kept.append({**group, "alert_ids": kept_ids, "alert_count": len(kept_ids)})
        if not removed_ids:
            raise HTTPException(status_code=404, detail="Alert tidak ditemukan pada korelasi tersimpan.")
        removed = len(removed_ids)
        state["groups"] = kept
        state["alert_ids"] = list(dict.fromkeys(
            aid for group in kept for aid in (group.get("alert_ids") or [])
        ))
        progress = state.get("progress")
        if isinstance(progress, dict):
            processed = {int(aid) for aid in (progress.get("processed_ids") or []) if str(aid).isdigit()}
            processed.update(int(aid) for aid in remove_ids if str(aid).isdigit())
            progress["processed_ids"] = sorted(processed)
        state["saved_at"] = datetime.now(timezone.utc).isoformat()
        save_document(conn, state_key, state)
        _remember_triage_state(conn, state_key, state)
    return {"removed": removed, "group_count": len(kept)}


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
    from app.exports import EXPORT_KEYS, export_rows

    writer = csv.DictWriter(output, fieldnames=list(EXPORT_KEYS), extrasaction="ignore")
    writer.writeheader()
    writer.writerows(export_rows(alerts))
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
            with _savepoint(conn):
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
    request: Request,
    tenant: list[str] = Query(default=["all"]),
    tz_offset_minutes: int = 420,
    reviewer: str = "",
):
    """PRD Section 3.C Monitoring Dashboard: Real-time metric cards, Analyst Leaderboard, and Report Audit Log."""
    offset = max(-840, min(840, int(tz_offset_minutes or 0)))
    now_utc = datetime.now(timezone.utc)
    now_local = now_utc + timedelta(minutes=offset)
    today_date = now_local.date()
    today_iso = today_date.isoformat()
    today_start_local = datetime.combine(today_date, datetime.min.time(), tzinfo=timezone.utc)
    today_start_utc = (today_start_local - timedelta(minutes=offset)).isoformat()

    current_user = _current_username(request, fallback="admin")
    requested_reviewer = str(reviewer or "").strip()
    if len(requested_reviewer) > 128 or any(ord(char) < 32 for char in requested_reviewer):
        raise HTTPException(status_code=422, detail="Filter reviewer tidak valid.")
    show_all_reviewers = requested_reviewer.lower() in {"all", "*", "semua"}
    effective_reviewer = "" if show_all_reviewers else (requested_reviewer or current_user)
    reviewer_cond = f"{REVIEWER_IDENTITY_SQL} = %s" if effective_reviewer else ""

    t_sql, t_params = tenant_clause("a", tenant)
    t_where = f"WHERE {t_sql}" if t_sql else ""
    t_and = f"AND {t_sql}" if t_sql else ""

    with get_db() as conn:
        _expire_stale_claims(conn)

        # 1. Check daily_metrics_cache first (PRD Section 4 Query Optimization)
        cached_pull_today = 0
        try:
            with _savepoint(conn):
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
            with _savepoint(conn):
                select_parts: list[str] = []
                select_params: list[Any] = []

                def add_metric(expr: str, alias: str, base: tuple[Any, ...] = (), scoped: bool = True) -> None:
                    scoped_expr = f"{expr} AND {reviewer_cond}" if (effective_reviewer and scoped) else expr
                    select_parts.append(f"COUNT(*) FILTER (WHERE {scoped_expr}) AS {alias}")
                    select_params.extend(base)
                    if effective_reviewer and scoped:
                        select_params.append(effective_reviewer)

                add_metric("a.imported_at >= %s OR a.timestamp >= %s", "pulled_today",
                           (today_start_utc, today_iso))
                add_metric("a.is_reviewed = false AND (a.imported_at < %s AND (a.timestamp IS NULL OR a.timestamp < %s))",
                           "outstanding_backlog", (today_start_utc, today_iso))
                add_metric("a.is_reviewed = false", "total_unreviewed")
                add_metric("a.is_reviewed = true", "global_review_count")
                add_metric("a.status = 'claimed'", "active_claims")
                add_metric("a.verdict = 'tp'", "tp_total")
                add_metric("a.verdict = 'fp'", "fp_total")
                add_metric("a.verdict = 'benign'", "benign_total")
                add_metric("a.flag_color = 'green'", "flag_green_total", scoped=False)
                add_metric("a.flag_color = 'yellow'", "flag_yellow_total", scoped=False)
                add_metric("a.flag_color = 'red'", "flag_red_total", scoped=False)

                m_row = conn.execute(
                    f"""SELECT {', '.join(select_parts)}
                        FROM wazuh.alerts a {t_where}""",
                    [*select_params, *t_params],
                ).fetchone()
        except Exception:
            # Fallback if imported_at or status/verdict/flag_color not present in minimal synthetic table
            m_row = conn.execute(
                f"""SELECT
                        COUNT(*) FILTER (WHERE a.timestamp >= %s) AS pulled_today,
                        COUNT(*) FILTER (WHERE a.is_reviewed = false AND (a.timestamp IS NULL OR a.timestamp < %s)) AS outstanding_backlog,
                        COUNT(*) FILTER (WHERE a.is_reviewed = false) AS total_unreviewed,
                        COUNT(*) FILTER (WHERE a.is_reviewed = true) AS global_review_count,
                        0 AS active_claims,
                        0 AS tp_total,
                        0 AS fp_total,
                        0 AS benign_total,
                        0 AS flag_green_total,
                        0 AS flag_yellow_total,
                        0 AS flag_red_total
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
            with _savepoint(conn):
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
                "green_count": 0,
                "yellow_count": 0,
                "red_count": 0,
            }

        try:
            with _savepoint(conn):
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
                    "green_count": 0, "yellow_count": 0, "red_count": 0,
                })
                entry["currently_claimed"] = int(r["n"] or 0)

            try:
                with _savepoint(conn):
                    reviewed_rows = conn.execute(
                        f"""SELECT COALESCE(NULLIF(a.reviewed_by, ''), NULLIF(a.flagged_by, ''), NULLIF(a.claimed_by, ''), 'admin') AS username,
                                   COUNT(*) AS total_n,
                                   COUNT(*) FILTER (WHERE a.reviewed_at >= %s) AS today_n,
                                   COUNT(*) FILTER (WHERE a.verdict = 'tp') AS tp_n,
                                   COUNT(*) FILTER (WHERE a.verdict = 'fp') AS fp_n,
                                   COUNT(*) FILTER (WHERE a.verdict = 'benign') AS benign_n,
                                   COUNT(*) FILTER (WHERE a.flag_color = 'green') AS green_n,
                                   COUNT(*) FILTER (WHERE a.flag_color = 'yellow') AS yellow_n,
                                   COUNT(*) FILTER (WHERE a.flag_color = 'red') AS red_n
                            FROM wazuh.alerts a
                            WHERE a.is_reviewed = true {t_and}
                            GROUP BY 1""",
                        [today_start_utc, *t_params],
                    ).fetchall()
            except Exception:
                with _savepoint(conn):
                    reviewed_rows = conn.execute(
                        f"""SELECT COALESCE(NULLIF(a.reviewed_by, ''), NULLIF(a.claimed_by, ''), 'admin') AS username,
                                   COUNT(*) AS total_n,
                                   COUNT(*) FILTER (WHERE a.reviewed_at >= %s) AS today_n,
                                   COUNT(*) FILTER (WHERE a.verdict = 'tp') AS tp_n,
                                   COUNT(*) FILTER (WHERE a.verdict = 'fp') AS fp_n,
                                   COUNT(*) FILTER (WHERE a.verdict = 'benign') AS benign_n,
                                   0 AS green_n,
                                   0 AS yellow_n,
                                   0 AS red_n
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
                    "green_count": 0, "yellow_count": 0, "red_count": 0,
                })
                entry["total_contributions"] = int(r["total_n"] or 0)
                entry["completed_today"] = int(r["today_n"] or 0)
                entry["tp_count"] = int(r["tp_n"] or 0)
                entry["fp_count"] = int(r["fp_n"] or 0)
                entry["benign_count"] = int(r["benign_n"] or 0)
                entry["green_count"] = int(r["green_n"] or 0)
                entry["yellow_count"] = int(r["yellow_n"] or 0)
                entry["red_count"] = int(r["red_n"] or 0)
        except Exception:
            pass

        reviewer_options = sorted(
            (
                {
                    "username": str(uname),
                    "display_name": str(info.get("display_name") or uname),
                    "role": str(info.get("role") or "analyst"),
                }
                for uname, info in leaderboard_map.items()
            ),
            key=lambda item: (item["display_name"].lower(), item["username"].lower()),
        )
        if not any(item["username"] == current_user for item in reviewer_options):
            reviewer_options.insert(0, {
                "username": current_user,
                "display_name": current_user,
                "role": "analyst",
            })

        leaderboard = sorted(
            leaderboard_map.values(),
            key=lambda x: (x["completed_today"], x["total_contributions"], x["currently_claimed"]),
            reverse=True,
        )

        # 3. Audit Log Laporan (Published Incident Cases + Exported Reports)
        audit_logs: list[dict[str, Any]] = []
        try:
            with _savepoint(conn):
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
            with _savepoint(conn):
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

        try:
            with _savepoint(conn):
                review_activity = _review_activity_payload(
                    conn, tenant, offset, 14, reviewer=effective_reviewer
                )
        except Exception:
            review_activity = None

    return {
        "review_activity": review_activity,
        "reviewer": {
            "current_user": current_user,
            "selected": effective_reviewer,
            "all": not effective_reviewer,
            "is_default": not requested_reviewer,
            "reviewers": reviewer_options,
        },
        "metrics": {
            "total_pull_today": pulled_today,
            "outstanding_backlog": outstanding_backlog,
            "total_unreviewed": total_unreviewed,
            "global_review_count": global_review_count,
            "active_claims": active_claims,
            "flags": {
                "green": int((m_row or {}).get("flag_green_total") or 0),
                "yellow": int((m_row or {}).get("flag_yellow_total") or 0),
                "red": int((m_row or {}).get("flag_red_total") or 0),
            },
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


@app.post("/api/alerts/flag")
def api_flag_alerts(
    payload: dict[str, Any],
    request: Request,
    tenant: list[str] = Query(default=["all"]),
):
    normalize_tenants(tenant)
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Payload flag tidak valid.")
    raw_flag = payload.get("flag_color")
    flag_color: str | None = None
    if raw_flag is not None and str(raw_flag).strip() != "":
        f_clean = str(raw_flag).strip().lower()
        if f_clean not in ALLOWED_FLAG_COLORS:
            raise HTTPException(status_code=400, detail="Warna flag harus 'green', 'yellow', atau 'red'.")
        flag_color = f_clean
    unreview = bool(payload.get("unreview", False))
    if unreview and flag_color is not None:
        raise HTTPException(
            status_code=400,
            detail="Alert yang dikembalikan ke belum direview tidak boleh tetap memiliki Flag.",
        )
    raw_ids = payload.get("alert_ids")
    auto_review = bool(payload.get("auto_review", False))
    notes = str(payload.get("reviewer_notes") or "").strip()
    actor = str(payload.get("flagged_by") or _current_username(request)).strip() or "analyst"
    with get_db() as conn:
        if raw_ids is not None:
            if not isinstance(raw_ids, list) or not raw_ids:
                raise HTTPException(status_code=400, detail="Pilih minimal satu alert.")
            clean_pks = _validate_membership(conn, raw_ids, tenant)
        else:
            group_by = payload.get("group_by")
            group_key = payload.get("group_key")
            current_flag_color = str(payload.get("current_flag_color") or "").strip().lower()
            if not group_by or group_key is None or current_flag_color not in ALLOWED_FLAG_COLORS:
                raise HTTPException(status_code=400, detail="Pilih minimal satu alert atau tentukan grup pola Flag.")
            where_sql, where_params = _build_flag_scope_where(
                tenant=tenant,
                flag_color=current_flag_color,
                rule_status=str(payload.get("current_rule_status") or "all").strip().lower(),
                q=str(payload.get("q") or ""),
                group_by=str(group_by),
                group_key=str(group_key),
                pattern=str(payload.get("pattern") or ""),
                pattern_mode=str(payload.get("pattern_mode") or "contains"),
            )
            matched_rows = conn.execute(
                f"SELECT a.id FROM wazuh.alerts a {where_sql}",
                where_params,
            ).fetchall()
            clean_pks = [int(r["id"]) for r in matched_rows]
            if not clean_pks:
                raise HTTPException(status_code=404, detail="Tidak ada alert yang cocok pada grup pola ini.")

        if unreview:
            _update_alerts_review_state(
                conn,
                clean_pks,
                is_reviewed=False,
                notes="",
                overwrite_notes=False,
                verdict=None,
                flag_color=None,
                reviewer=actor,
            )
            return {
                "status": "ok",
                "count": len(clean_pks),
                "is_reviewed": False,
                "flag_color": None,
                "flagged_by": None,
                "summary": _flag_counts(conn, tenant),
            }
        return _apply_flag_update(
            conn,
            clean_pks,
            flag_color=flag_color,
            actor=actor,
            auto_review=auto_review,
            reviewer_notes=notes,
            tenant=tenant,
        )


@app.put("/api/alerts/{alert_id}/flag")
def api_flag_single_alert(
    alert_id: int,
    payload: dict[str, Any],
    request: Request,
    tenant: list[str] = Query(default=["all"]),
):
    normalize_tenants(tenant)
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Payload flag tidak valid.")
    raw_flag = payload.get("flag_color")
    flag_color: str | None = None
    if raw_flag is not None and str(raw_flag).strip() != "":
        f_clean = str(raw_flag).strip().lower()
        if f_clean not in ALLOWED_FLAG_COLORS:
            raise HTTPException(status_code=400, detail="Warna flag harus 'green', 'yellow', atau 'red'.")
        flag_color = f_clean
    unreview = bool(payload.get("unreview", False))
    if unreview and flag_color is not None:
        raise HTTPException(
            status_code=400,
            detail="Alert yang dikembalikan ke belum direview tidak boleh tetap memiliki Flag.",
        )
    auto_review = bool(payload.get("auto_review", False))
    notes = str(payload.get("reviewer_notes") or "").strip()
    actor = str(payload.get("flagged_by") or _current_username(request)).strip() or "analyst"
    with get_db() as conn:
        clean_pks = _validate_membership(conn, [alert_id], tenant)
        if unreview:
            _update_alerts_review_state(
                conn,
                clean_pks,
                is_reviewed=False,
                notes="",
                overwrite_notes=False,
                verdict=None,
                flag_color=None,
                reviewer=actor,
            )
            return {
                "status": "ok",
                "id": alert_id,
                "count": len(clean_pks),
                "is_reviewed": False,
                "flag_color": None,
                "flagged_by": None,
                "summary": _flag_counts(conn, tenant),
            }
        res = _apply_flag_update(
            conn,
            clean_pks,
            flag_color=flag_color,
            actor=actor,
            auto_review=auto_review,
            reviewer_notes=notes,
            tenant=tenant,
        )
        res["id"] = alert_id
        return res


@app.get("/api/flags/summary")
def api_flags_summary(tenant: list[str] = Query(default=["all"])):
    normalize_tenants(tenant)
    with get_db() as conn:
        return _flag_counts(conn, tenant)


@app.get("/api/flags/groups")
def api_flags_groups(
    tenant: list[str] = Query(default=["all"]),
    flag_color: str = "green",
    rule_status: str = "pending",
    group_by: str = "rule_description",
    pattern: str = "",
    pattern_mode: str = "contains",
    q: str = "",
    limit: int = 200,
):
    normalize_tenants(tenant)
    if group_by not in PIVOT_DEFINITIONS:
        raise HTTPException(status_code=422, detail=f"Parameter pengelompokan '{group_by}' tidak didukung.")
    limit = min(max(int(limit or 200), 1), 500)
    color = str(flag_color or "green").strip().lower()
    effective_rule_status = "all" if color == "red" else str(rule_status or "pending").strip().lower()
    where_sql, params = _build_flag_scope_where(
        tenant=tenant,
        flag_color=color,
        rule_status=effective_rule_status,
        q=q,
    )

    dim_params: list[Any] = []
    pattern_required = False
    if group_by == "pattern":
        match_expr, match_params = _flag_pattern_predicate(pattern, pattern_mode)
        if not match_expr:
            pattern_required = True
            dim_sql = ""
        else:
            dim_sql = f"CASE WHEN {match_expr} THEN 'Cocok pola' ELSE 'Tidak cocok pola' END"
            dim_params = match_params
    else:
        dim_sql = PIVOT_DEFINITIONS[group_by]["sql"]

    with get_db() as conn:
        summary = _flag_counts(conn, tenant)
        if pattern_required:
            return {
                "flag_color": color,
                "rule_status": effective_rule_status,
                "group_by": group_by,
                "group_by_label": PIVOT_DEFINITIONS[group_by]["label"],
                "pattern": pattern.strip(),
                "pattern_mode": str(pattern_mode or "contains").strip().lower(),
                "pattern_required": True,
                "total_alerts": 0,
                "total_groups": 0,
                "groups": [],
                **summary,
            }

        tot_row = conn.execute(
            f"SELECT COUNT(*) AS n FROM wazuh.alerts a {where_sql}",
            params,
        ).fetchone()
        total_alerts = int((tot_row or {}).get("n") or 0)
        rows = conn.execute(
            f"""SELECT {dim_sql} AS k,
                       COUNT(*) AS alert_count,
                       COALESCE(SUM(COALESCE(a.hit_count, 1)), 0) AS event_hits,
                       COUNT(*) FILTER (WHERE COALESCE(NULLIF(a.rule_status, ''), 'pending') != 'done') AS pending_count,
                       COUNT(*) FILTER (WHERE a.rule_status = 'done') AS done_count,
                       MIN(NULLIF(a.timestamp, '')) AS earliest,
                       MAX(NULLIF(a.timestamp, '')) AS latest,
                       MIN(a.flagged_at) AS flagged_earliest,
                       MAX(a.flagged_at) AS flagged_latest,
                       MAX(NULLIF(a.custom_rule_id, '')) AS custom_rule_id,
                       MAX(NULLIF(a.rule_notes, '')) AS rule_notes,
                       MAX(NULLIF(a.rule_updated_by, '')) AS rule_updated_by,
                       MAX(a.rule_updated_at) AS rule_updated_at
                FROM wazuh.alerts a {where_sql}
                GROUP BY 1
                ORDER BY 2 DESC, 1 ASC
                LIMIT %s""",
            dim_params + params + [limit],
        ).fetchall()

    groups: list[dict[str, Any]] = []
    for r in rows:
        pending_c = int(r.get("pending_count") or 0)
        done_c = int(r.get("done_count") or 0)
        if color == "red":
            grp_status = "none"
        elif pending_c == 0 and done_c > 0:
            grp_status = "done"
        elif done_c == 0:
            grp_status = "pending"
        else:
            grp_status = "partial"
        groups.append({
            "key": str(r["k"] if r.get("k") is not None else "Tidak tersedia"),
            "alert_count": int(r.get("alert_count") or 0),
            "event_hits": int(r.get("event_hits") or 0),
            "pending_count": pending_c,
            "done_count": done_c,
            "rule_status": grp_status,
            "earliest": r.get("earliest") or "",
            "latest": r.get("latest") or "",
            "flagged_earliest": str(r["flagged_earliest"]) if r.get("flagged_earliest") else "",
            "flagged_latest": str(r["flagged_latest"]) if r.get("flagged_latest") else "",
            "custom_rule_id": r.get("custom_rule_id") or "",
            "rule_notes": r.get("rule_notes") or "",
            "rule_updated_by": r.get("rule_updated_by") or "",
            "rule_updated_at": str(r["rule_updated_at"]) if r.get("rule_updated_at") else "",
        })

    return {
        "flag_color": color,
        "rule_status": effective_rule_status,
        "group_by": group_by,
        "group_by_label": PIVOT_DEFINITIONS[group_by]["label"],
        "pattern": pattern.strip(),
        "pattern_mode": str(pattern_mode or "contains").strip().lower(),
        "pattern_required": False,
        "total_alerts": total_alerts,
        "total_groups": len(groups),
        "groups": groups,
        **summary,
    }


@app.get("/api/flags/alerts")
def api_flags_alerts(
    tenant: list[str] = Query(default=["all"]),
    flag_color: str = "green",
    rule_status: str = "pending",
    group_by: str = "rule_description",
    group_key: str = "",
    pattern: str = "",
    pattern_mode: str = "contains",
    q: str = "",
    limit: int = 100,
    offset: int = 0,
):
    normalize_tenants(tenant)
    limit = min(max(int(limit or 100), 1), 1000)
    offset = max(int(offset or 0), 0)
    color = str(flag_color or "green").strip().lower()
    effective_rule_status = "all" if color == "red" else str(rule_status or "pending").strip().lower()
    where_sql, params = _build_flag_scope_where(
        tenant=tenant,
        flag_color=color,
        rule_status=effective_rule_status,
        q=q,
        group_by=group_by,
        group_key=group_key,
        pattern=pattern,
        pattern_mode=pattern_mode,
    )
    with get_db() as conn:
        total_row = conn.execute(
            f"SELECT COUNT(*) AS n FROM wazuh.alerts a {where_sql}",
            params,
        ).fetchone()
        rows = conn.execute(
            f"""SELECT a.id, a.alert_id, a.timestamp, a.tenant, a.agent_name, a.agent_ip,
                       a.rule_id, a.rule_level, a.description, a.source_ip, a.hit_count,
                       a.data, a.parsed_details, COALESCE(a.raw->>'full_log', '') AS full_log,
                       a.flag_color, a.flagged_by, a.flagged_at,
                       a.rule_status, a.custom_rule_id, a.rule_notes, a.rule_updated_by, a.rule_updated_at,
                       a.verdict, a.reviewed_by, a.reviewed_at
                FROM wazuh.alerts a {where_sql}
                ORDER BY a.timestamp DESC NULLS LAST, a.id DESC
                LIMIT %s OFFSET %s""",
            [*params, limit, offset],
        ).fetchall()
    return {"items": rows, "total": int((total_row or {}).get("n") or 0)}


def flag_export_scope(
    tenant: list[str] = Query(default=["all"]),
    flag_color: str = "green",
    rule_status: str = "pending",
    group_by: str = "rule_description",
    pattern: str = "",
    pattern_mode: str = "contains",
    q: str = "",
    group_key: list[str] = Query(default=[]),
) -> dict[str, Any]:
    """Canonical export scope for flagged alerts (flag category + selected groups)."""
    normalize_tenants(tenant)
    color = str(flag_color or "green").strip().lower()
    if color not in ALLOWED_FLAG_COLORS:
        raise HTTPException(status_code=422, detail="flag_color harus 'green', 'yellow', atau 'red'.")
    if group_by not in PIVOT_DEFINITIONS:
        raise HTTPException(status_code=422, detail=f"Parameter pengelompokan '{group_by}' tidak didukung.")
    r_status = "all" if color == "red" else str(rule_status or "pending").strip().lower()
    if r_status not in {"all", "pending", "done"}:
        raise HTTPException(status_code=422, detail="rule_status harus 'all', 'pending', atau 'done'.")
    mode = str(pattern_mode or "contains").strip().lower()
    if mode not in {"contains", "regex"}:
        raise HTTPException(status_code=422, detail="pattern_mode harus 'contains' atau 'regex'.")
    keys = [str(value) for value in (group_key or []) if str(value) != ""]
    return dict(
        tenant=_scope_tenant_value(tenant),
        flag_color=color,
        rule_status=r_status,
        group_by=group_by,
        pattern=str(pattern or "").strip(),
        pattern_mode=mode,
        q=str(q or "").strip(),
        group_key=keys,
    )


def _get_flagged_alerts_for_export(
    *,
    tenant: Any,
    flag_color: str,
    rule_status: str,
    group_by: str,
    pattern: str,
    pattern_mode: str,
    q: str,
    group_key: list[str],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    where_sql, params = _build_flag_scope_where(
        tenant=tenant,
        flag_color=flag_color,
        rule_status=rule_status,
        q=q,
    )
    keys = [str(key) for key in (group_key or [])]
    if keys:
        if group_by == "pattern":
            match_expr, match_params = _flag_pattern_predicate(pattern, pattern_mode)
            branches: list[str] = []
            if "Cocok pola" in keys:
                if match_expr:
                    branches.append(match_expr)
                    params.extend(match_params)
                else:
                    branches.append("1 = 0")
            if "Tidak cocok pola" in keys:
                if match_expr:
                    branches.append(f"NOT ({match_expr})")
                    params.extend(match_params)
                else:
                    branches.append("1 = 1")
            if not branches:
                branches.append("1 = 0")
            where_sql += " AND (" + " OR ".join(branches) + ")"
        else:
            dim_sql = PIVOT_DEFINITIONS[group_by]["sql"]
            where_sql += f" AND ({dim_sql}) = ANY(%s)"
            params.append(keys)

    with get_db() as conn:
        rows = conn.execute(
            f"""SELECT a.*, COALESCE(a.raw->>'full_log', '') AS full_log
                FROM wazuh.alerts a {where_sql}
                ORDER BY a.timestamp ASC NULLS LAST, a.id ASC
                LIMIT %s""",
            [*params, MAX_EXPORT_ALERTS + 1],
        ).fetchall()
    alerts = [dict(row) for row in rows]
    if len(alerts) > MAX_EXPORT_ALERTS:
        raise HTTPException(status_code=413, detail=f"Export exceeds {MAX_EXPORT_ALERTS} alerts. Narrow the scope and retry.")

    color_label = {"green": "Hijau", "yellow": "Kuning", "red": "Merah"}.get(flag_color, flag_color)
    dimension = PIVOT_DEFINITIONS[group_by]["label"]
    selected = f" · {len(keys)} grup dipilih" if keys else ""
    meta: dict[str, Any] = {
        "title": f"Laporan Flag {color_label} — {dimension}{selected}",
        "category": "Flag & Rule Tuning",
        "severity": "Critical" if flag_color == "red" else "High" if flag_color == "yellow" else "Low",
        "status": "Triage",
        "analysis": "",
        "conclusion": "",
        "recommendation": "",
    }
    return alerts, meta


@app.get("/api/flags/export/preview")
def flag_export_preview(scope: dict[str, Any] = Depends(flag_export_scope)):
    alerts, meta = _get_flagged_alerts_for_export(**scope)
    return {
        "count": len(alerts),
        "meta": meta,
        "scope": scope,
        "html": generate_gdocs_html_report(alerts, meta, columns=FLAG_EXPORT_COLUMNS),
        "truncated": False,
    }


@app.get("/api/flags/export/report-html", response_class=HTMLResponse)
def flag_export_html(request: Request, scope: dict[str, Any] = Depends(flag_export_scope)):
    alerts, meta = _get_flagged_alerts_for_export(**scope)
    html_content = generate_gdocs_html_report(alerts, meta, columns=FLAG_EXPORT_COLUMNS)
    _record_report_audit_log(request, title=str(meta.get("title") or "Laporan Flag HTML"), format_name="Google Docs HTML (Flag)", tenant=scope.get("tenant"), alert_count=len(alerts))
    return HTMLResponse(content=html_content, headers={"X-Arbiter-Count": str(len(alerts))})


@app.get("/api/flags/export/docx")
def flag_export_docx(request: Request, scope: dict[str, Any] = Depends(flag_export_scope)):
    alerts, meta = _get_flagged_alerts_for_export(**scope)
    buf = generate_docx_landscape_report(alerts, meta, columns=FLAG_EXPORT_COLUMNS)
    _record_report_audit_log(request, title=str(meta.get("title") or "Laporan Flag Word"), format_name="Word (.docx) Flag", tenant=scope.get("tenant"), alert_count=len(alerts))
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": 'attachment; filename="Arbiter-Flag-Report.docx"', "X-Arbiter-Count": str(len(alerts))},
    )


@app.get("/api/flags/export/xlsx")
def flag_export_xlsx(request: Request, scope: dict[str, Any] = Depends(flag_export_scope)):
    alerts, meta = _get_flagged_alerts_for_export(**scope)
    buf = generate_xlsx_workbook(alerts, columns=FLAG_EXPORT_COLUMNS)
    _record_report_audit_log(request, title=str(meta.get("title") or "Workbook Flag Excel"), format_name="Excel (.xlsx) Flag", tenant=scope.get("tenant"), alert_count=len(alerts))
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="Arbiter-Flag-Report.xlsx"', "X-Arbiter-Count": str(len(alerts))},
    )


@app.get("/api/flags/export/tsv")
def flag_export_tsv(request: Request, scope: dict[str, Any] = Depends(flag_export_scope)):
    alerts, meta = _get_flagged_alerts_for_export(**scope)
    content = generate_tsv_table(alerts, columns=FLAG_EXPORT_COLUMNS)
    _record_report_audit_log(request, title=str(meta.get("title") or "Tabel Flag TSV"), format_name="TSV (Flag)", tenant=scope.get("tenant"), alert_count=len(alerts))
    return Response(content=content, media_type="text/tab-separated-values; charset=utf-8",
                    headers={"X-Arbiter-Count": str(len(alerts))})


@app.get("/api/flags/export/markdown")
def flag_export_markdown(request: Request, scope: dict[str, Any] = Depends(flag_export_scope)):
    alerts, meta = _get_flagged_alerts_for_export(**scope)
    content = generate_markdown_report(alerts, meta, columns=FLAG_EXPORT_COLUMNS)
    _record_report_audit_log(request, title=str(meta.get("title") or "Laporan Flag Markdown"), format_name="Markdown (.md) Flag", tenant=scope.get("tenant"), alert_count=len(alerts))
    return Response(content=content, media_type="text/markdown; charset=utf-8",
                    headers={"X-Arbiter-Count": str(len(alerts))})


@app.get("/api/flags/export/csv")
def flag_export_csv(request: Request, scope: dict[str, Any] = Depends(flag_export_scope)):
    from app.exports import export_rows

    alerts, meta = _get_flagged_alerts_for_export(**scope)
    _record_report_audit_log(request, title=str(meta.get("title") or "Ekspor Flag CSV"), format_name="CSV (Flag)", tenant=scope.get("tenant"), alert_count=len(alerts))
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=[key for key, _label in FLAG_EXPORT_COLUMNS], extrasaction="ignore")
    writer.writeheader()
    writer.writerows(export_rows(alerts))
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="arbiter-flagged-alerts.csv"', "X-Arbiter-Count": str(len(alerts))},
    )


@app.post("/api/flags/rule-status")
def api_flags_rule_status(
    payload: dict[str, Any],
    request: Request,
    tenant: list[str] = Query(default=["all"]),
):
    normalize_tenants(tenant)
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Payload status rule tidak valid.")
    r_status = str(payload.get("rule_status") or "").strip().lower()
    if r_status not in ALLOWED_RULE_STATUSES:
        raise HTTPException(status_code=400, detail="rule_status harus 'pending' atau 'done'.")
    custom_rule_id = str(payload.get("custom_rule_id") or "").strip()[:50]
    rule_notes = str(payload.get("rule_notes") or "").strip()[:1000]
    actor = str(payload.get("rule_updated_by") or _current_username(request)).strip() or "analyst"

    raw_ids = payload.get("alert_ids")
    with get_db() as conn:
        if raw_ids is not None:
            pks = _validate_membership(conn, raw_ids, tenant)
            if not pks:
                raise HTTPException(status_code=400, detail="Pilih minimal satu alert untuk diperbarui.")
            rows = conn.execute(
                "SELECT id, flag_color FROM wazuh.alerts WHERE id = ANY(%s)",
                (pks,),
            ).fetchall()
        else:
            color = str(payload.get("flag_color") or "").strip().lower()
            if color == "red":
                raise HTTPException(
                    status_code=400,
                    detail="Alert dengan Flag Merah tidak boleh ditandai sebagai custom rule pengecualian.",
                )
            group_by = payload.get("group_by")
            group_key = payload.get("group_key")
            if not group_by or group_key is None:
                raise HTTPException(status_code=400, detail="Tentukan alert_ids atau grup pola sasaran.")
            where_sql, params = _build_flag_scope_where(
                tenant=tenant,
                flag_color=color,
                rule_status=str(payload.get("current_rule_status") or "all").strip().lower(),
                q=str(payload.get("q") or ""),
                group_by=str(group_by),
                group_key=str(group_key),
                pattern=str(payload.get("pattern") or ""),
                pattern_mode=str(payload.get("pattern_mode") or "contains"),
            )
            rows = conn.execute(
                f"SELECT a.id, a.flag_color FROM wazuh.alerts a {where_sql}",
                params,
            ).fetchall()
            pks = [int(r["id"]) for r in rows]

        if not pks:
            raise HTTPException(status_code=404, detail="Tidak ada alert yang cocok pada scope ini.")
        if any((not r.get("flag_color")) or r.get("flag_color") == "red" for r in rows):
            raise HTTPException(
                status_code=400,
                detail="Hanya alert dengan Flag Hijau atau Kuning yang dapat ditandai status custom rule-nya.",
            )

        if r_status == "done":
            conn.execute(
                """UPDATE wazuh.alerts
                   SET rule_status = 'done',
                       custom_rule_id = %s,
                       rule_notes = %s,
                       rule_updated_by = %s,
                       rule_updated_at = now()
                   WHERE id = ANY(%s)""",
                (custom_rule_id or None, rule_notes, actor, pks),
            )
        else:
            conn.execute(
                """UPDATE wazuh.alerts
                   SET rule_status = 'pending',
                       custom_rule_id = NULL,
                       rule_notes = '',
                       rule_updated_by = NULL,
                       rule_updated_at = NULL
                   WHERE id = ANY(%s)""",
                (pks,),
            )

        summary = _flag_counts(conn, tenant)

    return {
        "status": "ok",
        "updated": len(pks),
        "rule_status": r_status,
        "custom_rule_id": custom_rule_id or None if r_status == "done" else None,
        "rule_notes": rule_notes if r_status == "done" else "",
        "rule_updated_by": actor if r_status == "done" else None,
        "summary": summary,
    }
