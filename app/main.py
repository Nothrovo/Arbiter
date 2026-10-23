"""FastAPI Application Server for Arbiter — SOC Telemetry & Incident Workspace."""

from __future__ import annotations

import csv
import io
import json
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any
from urllib.parse import quote

from fastapi import Depends, FastAPI, File, HTTPException, Response, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from app.config import HOST, PORT
from app.core import normalize_alert, suggestions_with_fallback
from app.intel import enrich_ip, is_valid_ip, sync_remote_cache, upsert_ip_cache
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
from app.query import alert_where, positive_ids, validated_group_id


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure tables, schemas, and indices are fully initialized on startup
    init_database()
    yield


app = FastAPI(
    title="Arbiter — SOC Telemetry & Incident Workspace",
    version="2.0.0",
    lifespan=lifespan,
)
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


@app.get("/api/alerts")
def list_alerts(
    q: str = "",
    tenant: str = "all",
    status: str = "all",
    group_id: str | None = None,
    filter_preset: str = "",
    review_status: str = "all",
    time_from: str = "",
    time_to: str = "",
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
        time_from=time_from, time_to=time_to,
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
        a.source_ip, a.mitre_ids, a.cve, a.hit_count, a.first_seen, a.last_seen, a.is_reviewed"""
    if not summary:
        projection += """, a.data, a.raw, a.wazuh_ids, a.duplicate_instances,
        a.parsed_details, a.reviewer_notes,
        COALESCE(a.raw->>'full_log', '') AS full_log,
        COALESCE(a.raw->>'previous_output', '') AS previous_output"""
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
    {where_sql}
    GROUP BY 
        a.id, ipc.abuse_score, ipc.vt_malicious, ipc.country_code, ipc.isp, ipc.attack_types
    ORDER BY {order_col}
    LIMIT %s OFFSET %s
    """
    count_sql = f"SELECT count(DISTINCT a.id) AS n FROM wazuh.alerts a {where_sql}"

    with get_db() as conn:
        rows = conn.execute(sql, params + [limit, offset]).fetchall()
        total = conn.execute(count_sql, params).fetchone()["n"]

    return {"items": rows, "total": total}


@app.get("/api/alerts/{alert_id}")
def get_alert_detail(alert_id: int, tenant: str = "all"):
    where = "a.id = %s"
    params: list[Any] = [alert_id]
    if tenant and tenant != "all":
        where += " AND a.tenant = %s"
        params.append(tenant)
    with get_db() as conn:
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
    if row is None:
        raise HTTPException(status_code=404, detail="Alert not found in this scope.")
    return row


@app.put("/api/alerts/{alert_id}/review")
def update_alert_review(alert_id: int, payload: dict[str, Any], tenant: str = "all"):
    is_reviewed = bool(payload.get("is_reviewed", True))
    notes = str(payload.get("reviewer_notes") or "").strip()
    with get_db() as conn:
        _validate_membership(conn, [alert_id], tenant)
        conn.execute(
            """UPDATE wazuh.alerts
               SET is_reviewed = %s,
                   reviewed_at = CASE WHEN %s THEN now() ELSE NULL END,
                   reviewer_notes = %s
               WHERE id = %s""",
            (is_reviewed, is_reviewed, notes, alert_id),
        )
    return {"status": "ok", "id": alert_id, "is_reviewed": is_reviewed}


@app.post("/api/alerts/batch-review")
def batch_update_review(payload: dict[str, Any], tenant: str = "all"):
    alert_ids = payload.get("alert_ids") or []
    is_reviewed = bool(payload.get("is_reviewed", True))
    if not alert_ids:
        raise HTTPException(status_code=400, detail="No valid alert IDs provided.")
    with get_db() as conn:
        clean_pks = _validate_membership(conn, alert_ids, tenant)
        conn.execute(
            """UPDATE wazuh.alerts
               SET is_reviewed = %s,
                   reviewed_at = CASE WHEN %s THEN now() ELSE NULL END
               WHERE id = ANY(%s)""",
            (is_reviewed, is_reviewed, clean_pks),
        )
    return {"status": "ok", "count": len(clean_pks), "is_reviewed": is_reviewed}


@app.post("/api/intel/enrich")
def enrich_intel(payload: dict[str, Any], tenant: str = "all"):
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
                where_clause = "WHERE id = ANY(%s)"
                params: list[Any] = [clean_pks]
                if tenant and tenant != "all":
                    where_clause += " AND tenant = %s"
                    params.append(tenant)
                rows = conn.execute(
                    f"SELECT DISTINCT source_ip FROM wazuh.alerts {where_clause} AND source_ip IS NOT NULL AND source_ip != ''",
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
        for ip in unique_ips:
            res = enrich_ip(ip)
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


def _scoped_groups(conn, tenant: str = "all", group_id: str | None = None):
    group_id = validated_group_id(group_id)
    clauses: list[str] = []
    params: list[Any] = []
    if tenant and tenant != "all":
        clauses.append("a.tenant = %s")
        params.append(tenant)
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
def list_groups(tenant: str = "all"):
    with get_db() as conn:
        return _scoped_groups(conn, tenant)


@app.get("/api/groups/{group_id}")
def get_group_detail(group_id: str, tenant: str = "all"):
    with get_db() as conn:
        rows = _scoped_groups(conn, tenant, group_id)
    if not rows:
        raise HTTPException(status_code=404, detail="Incident group not found in this scope.")
    return rows[0]


@app.post("/api/groups")
def create_group(payload: dict[str, Any], tenant: str = "all"):
    title = str(payload.get("title", "")).strip()
    if not title:
        raise HTTPException(status_code=400, detail="Group / Incident title is required.")
    if tenant != "all" and not payload.get("alert_pks"):
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
def update_group(group_id: str, payload: dict[str, Any], tenant: str = "all"):
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
def delete_group(group_id: str, tenant: str = "all"):
    validated_group_id(group_id)
    with get_db() as conn:
        if not _scoped_groups(conn, tenant, group_id):
            raise HTTPException(status_code=404, detail="Incident group not found in this scope.")
        conn.execute("DELETE FROM wazuh.analysis_groups WHERE id = %s", (group_id,))
    return {"status": "ok"}


@app.post("/api/groups/{group_id}/members")
def add_group_members(group_id: str, payload: dict[str, Any], tenant: str = "all"):
    validated_group_id(group_id)
    with get_db() as conn:
        if not conn.execute("SELECT 1 FROM wazuh.analysis_groups WHERE id = %s", (group_id,)).fetchone():
            raise HTTPException(status_code=404, detail="Incident group not found.")
        pks = _validate_membership(conn, payload.get("alert_pks", []), tenant)
        for pk in pks:
            conn.execute(
                "INSERT INTO wazuh.alert_group_members(alert_pk, group_id) VALUES(%s, %s) ON CONFLICT DO NOTHING",
                (pk, group_id),
            )
    return {"status": "ok"}


def _validate_membership(conn, values, tenant: str) -> list[int]:
    if not isinstance(values, list):
        raise HTTPException(status_code=422, detail="alert_pks must be a list.")
    try:
        pks = positive_ids(values)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if pks:
        where = "id = ANY(%s)"
        params: list[Any] = [pks]
        if tenant and tenant != "all":
            where += " AND tenant = %s"
            params.append(tenant)
        rows = conn.execute(f"SELECT id FROM wazuh.alerts WHERE {where}", params).fetchall()
        if {row["id"] for row in rows} != set(pks):
            raise HTTPException(status_code=400, detail="Selected alerts are missing or outside the active tenant.")
    return pks


@app.delete("/api/groups/{group_id}/members/{alert_pk}")
def remove_group_member(group_id: str, alert_pk: int, tenant: str = "all"):
    validated_group_id(group_id)
    with get_db() as conn:
        _validate_membership(conn, [alert_pk], tenant)
        groups = _scoped_groups(conn, tenant, group_id)
        if not groups:
            raise HTTPException(status_code=404, detail="Incident group not found in this scope.")
        if tenant != "all" and alert_pk in groups[0]["alert_pks"] and groups[0]["alert_count"] <= 1:
            raise HTTPException(status_code=409, detail="Bukti terakhir tenant tidak dapat dilepas dari scope ini. Gunakan Semua tenant untuk meninjau kasus sebelum melepasnya.")
        conn.execute(
            "DELETE FROM wazuh.alert_group_members WHERE group_id = %s AND alert_pk = %s",
            (group_id, alert_pk),
        )
    return {"status": "ok"}


@app.get("/api/suggestions")
def get_suggestions(
    use_local_ai: bool = False, tenant: str = "all", q: str = "",
    review_status: str = "all", filter_preset: str = "", status: str = "all",
    group_id: str | None = None, time_from: str = "", time_to: str = "",
):
    where, params = alert_where(
        tenant=tenant, q=q, review_status=review_status, filter_preset=filter_preset,
        status=status, group_id=group_id, time_from=time_from, time_to=time_to,
    )
    with get_db() as conn:
        rows = conn.execute(
            f"""SELECT a.id, a.alert_id, a.timestamp, a.tenant, a.agent_name, a.agent_ip, a.rule_id, a.rule_level,
                       a.description, a.rule_groups, a.decoder, a.location, a.source_ip, a.mitre_ids, a.cve,
                       a.log_signature, a.raw
                FROM wazuh.alerts a {where}
                ORDER BY a.timestamp DESC NULLS LAST, a.id DESC LIMIT 300""",
            params,
        ).fetchall()
    candidate_alerts = [{**r, "id": str(r["id"])} for r in rows]
    groups_list, mode, warning = suggestions_with_fallback(candidate_alerts, enabled=use_local_ai)
    return {"mode": mode, "warning": warning, "suggestions": groups_list}


# A bounded, complete export is returned, or an explicit 413; never a partial file.
MAX_EXPORT_ALERTS = 10_000


def _get_alerts_for_export(
    group_id: str | None = None, alert_ids: str | None = None, tenant: str = "all",
    q: str = "", review_status: str = "all", filter_preset: str = "", status: str = "all",
    time_from: str = "", time_to: str = "",
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    where, params = alert_where(
        q=q, tenant=tenant, review_status=review_status, filter_preset=filter_preset,
        status=status, group_id=group_id, time_from=time_from, time_to=time_to,
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
                ORDER BY a.timestamp ASC NULLS LAST, a.id ASC
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
        tenant_tag = f"Tenant: {tenant}" if tenant != "all" else "Semua Tenant"
        meta["title"] = f"Laporan Rekapitulasi Triage ({tenant_tag})"
    return alerts, meta


def export_scope(
    group_id: str | None = None, alert_ids: str | None = None, tenant: str = "all",
    q: str = "", review_status: str = "all", filter_preset: str = "", status: str = "all",
    time_from: str = "", time_to: str = "",
) -> dict[str, Any]:
    # Explicit selection replaces triage filters, never tenant context.
    if alert_ids is not None:
        try:
            alert_ids = ",".join(str(pk) for pk in positive_ids(alert_ids.split(",")))
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        group_id, q, review_status, filter_preset, status, time_from, time_to = None, "", "all", "", "all", "", ""
    return dict(group_id=group_id, alert_ids=alert_ids, tenant=tenant, q=q,
                review_status=review_status, filter_preset=filter_preset, status=status,
                time_from=time_from, time_to=time_to)


@app.get("/api/export/preview")
def export_preview(scope: dict[str, Any] = Depends(export_scope)):
    alerts, meta = _get_alerts_for_export(**scope)
    return {"count": len(alerts), "meta": meta, "scope": scope,
            "html": generate_gdocs_html_report(alerts, meta), "truncated": False}


@app.get("/api/export/report-html", response_class=HTMLResponse)
def export_gdocs_html(scope: dict[str, Any] = Depends(export_scope)):
    alerts, meta = _get_alerts_for_export(**scope)
    html_content = generate_gdocs_html_report(alerts, meta)
    return HTMLResponse(content=html_content, headers={"X-Arbiter-Count": str(len(alerts))})


@app.get("/api/export/docx")
def export_docx(scope: dict[str, Any] = Depends(export_scope)):
    alerts, meta = _get_alerts_for_export(**scope)
    buf = generate_docx_landscape_report(alerts, meta)
    filename = f"Arbiter-Report-{meta.get('title', 'SOC')[:24].replace(' ', '_')}.docx"
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": "attachment; filename=Arbiter-Report.docx; filename*=UTF-8''" + quote(filename, safe=""), "X-Arbiter-Count": str(len(alerts))},
    )


@app.get("/api/export/xlsx")
def export_xlsx(scope: dict[str, Any] = Depends(export_scope)):
    alerts, _ = _get_alerts_for_export(**scope)
    buf = generate_xlsx_workbook(alerts)
    filename = "Arbiter-Alerts-Export.xlsx"
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"', "X-Arbiter-Count": str(len(alerts))},
    )


@app.get("/api/export/tsv")
def export_tsv(scope: dict[str, Any] = Depends(export_scope)):
    alerts, _ = _get_alerts_for_export(**scope)
    tsv_content = generate_tsv_table(alerts)
    return Response(content=tsv_content, media_type="text/tab-separated-values; charset=utf-8",
                    headers={"X-Arbiter-Count": str(len(alerts))})


@app.get("/api/export/markdown")
def export_markdown(scope: dict[str, Any] = Depends(export_scope)):
    alerts, meta = _get_alerts_for_export(**scope)
    md_content = generate_markdown_report(alerts, meta)
    return Response(content=md_content, media_type="text/markdown; charset=utf-8",
                    headers={"X-Arbiter-Count": str(len(alerts))})


@app.get("/api/export.csv")
def export_csv(scope: dict[str, Any] = Depends(export_scope)):
    alerts, _ = _get_alerts_for_export(**scope)
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


@app.get("/api/database/status")
def api_database_status():
    if hasattr(db_module, "get_database_status"):
        with get_db() as conn:
            return db_module.get_database_status(conn)
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
        return db_module.set_active_profile(profile)
    return {"id": profile, "status": "switched"}


@app.post("/api/database/test")
def api_database_test(payload: dict[str, Any]):
    url = payload.get("url")
    if hasattr(db_module, "test_db_connection"):
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
    if older_than_days is not None:
        try:
            older_than_days = int(older_than_days)
        except (ValueError, TypeError):
            older_than_days = None
    time_from = payload.get("time_from")
    time_to = payload.get("time_to")
    tenant = payload.get("tenant", "all")
    dry_run = bool(payload.get("dry_run", True))
    with get_db() as conn:
        if hasattr(db_module, "purge_alerts"):
            return db_module.purge_alerts(
                conn, older_than_days=older_than_days, time_from=time_from,
                time_to=time_to, tenant=tenant, dry_run=dry_run,
            )
        return {"dry_run": dry_run, "count": 0}


@app.post("/api/database/purge-incidents")
def api_database_purge_incidents(payload: dict[str, Any]):
    status_filter = str(payload.get("status") or "closed_only")
    dry_run = bool(payload.get("dry_run", True))
    with get_db() as conn:
        if hasattr(db_module, "purge_incidents"):
            return db_module.purge_incidents(
                conn, status_filter=status_filter, dry_run=dry_run,
            )
        return {"dry_run": dry_run, "count": 0}


@app.get("/", response_class=HTMLResponse)
def index_page():
    html_path = Path(__file__).with_name("index.html")
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))
