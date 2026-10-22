"""PostgreSQL database layer and schema migration for Arbiter."""

from __future__ import annotations

import json
from contextlib import contextmanager
from typing import Any, Generator

import psycopg
from fastapi import HTTPException
from psycopg.rows import dict_row

from app.config import DATABASE_URL

SCHEMA_SQL = """
CREATE SCHEMA IF NOT EXISTS wazuh;

CREATE TABLE IF NOT EXISTS wazuh.alerts (
    id BIGSERIAL PRIMARY KEY,
    alert_id TEXT NOT NULL DEFAULT '',
    timestamp TEXT,
    tenant TEXT NOT NULL DEFAULT 'Default',
    agent_name TEXT,
    agent_ip TEXT,
    rule_id TEXT,
    rule_level INTEGER,
    description TEXT NOT NULL DEFAULT '',
    rule_groups JSONB NOT NULL DEFAULT '[]',
    decoder TEXT,
    location TEXT,
    source_ip TEXT,
    mitre_ids JSONB NOT NULL DEFAULT '[]',
    cve TEXT,
    data JSONB NOT NULL DEFAULT '{}',
    raw JSONB NOT NULL,
    log_signature TEXT DEFAULT '',
    hit_count INTEGER DEFAULT 1,
    first_seen TEXT,
    last_seen TEXT,
    wazuh_ids JSONB DEFAULT '[]',
    duplicate_instances JSONB DEFAULT '[]',
    parsed_details JSONB DEFAULT '{}',
    is_reviewed BOOLEAN NOT NULL DEFAULT false,
    reviewed_at TIMESTAMPTZ,
    reviewer_notes TEXT DEFAULT '',
    imported_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(alert_id, timestamp, agent_name, rule_id)
);

CREATE TABLE IF NOT EXISTS wazuh.analysis_groups (
    id UUID PRIMARY KEY,
    title TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT '',
    analysis TEXT NOT NULL DEFAULT '',
    conclusion TEXT NOT NULL DEFAULT '',
    recommendation TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'open',
    severity TEXT NOT NULL DEFAULT 'medium',
    source TEXT NOT NULL DEFAULT 'human',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS wazuh.alert_group_members (
    alert_pk BIGINT REFERENCES wazuh.alerts(id) ON DELETE CASCADE,
    group_id UUID REFERENCES wazuh.analysis_groups(id) ON DELETE CASCADE,
    PRIMARY KEY(alert_pk, group_id)
);

-- Fallback mock table for public.ip_intel_cache so open-source users without IP Intel don't crash
CREATE TABLE IF NOT EXISTS public.ip_intel_cache (
    ip TEXT PRIMARY KEY,
    abuse_score INTEGER,
    vt_malicious INTEGER,
    country_code TEXT,
    isp TEXT,
    attack_types TEXT[] DEFAULT '{}',
    total_alert_count INTEGER DEFAULT 1,
    last_seen TIMESTAMPTZ DEFAULT now()
);

-- Performance indices
CREATE INDEX IF NOT EXISTS idx_wazuh_alerts_source_ip ON wazuh.alerts(source_ip);
CREATE INDEX IF NOT EXISTS idx_wazuh_alerts_rule_id ON wazuh.alerts(rule_id);
CREATE INDEX IF NOT EXISTS idx_wazuh_alerts_timestamp ON wazuh.alerts(timestamp);
CREATE INDEX IF NOT EXISTS idx_wazuh_alerts_tenant ON wazuh.alerts(tenant);
CREATE INDEX IF NOT EXISTS idx_wazuh_alerts_sig ON wazuh.alerts(tenant, log_signature);
CREATE INDEX IF NOT EXISTS idx_wazuh_alerts_reviewed ON wazuh.alerts(is_reviewed);
"""


def get_db_connection():
    """Returns a psycopg connection with dictionary row formatting."""
    try:
        return psycopg.connect(DATABASE_URL, row_factory=dict_row)
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Database connection error: {exc}",
        ) from exc


@contextmanager
def get_db() -> Generator[psycopg.Connection, None, None]:
    conn = get_db_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_database() -> None:
    """Executes schema migrations and ensures indices exist."""
    with get_db() as conn:
        conn.execute(SCHEMA_SQL)


def ingest_alert_with_dedup(conn: psycopg.Connection, a: dict[str, Any]) -> tuple[bool, bool]:
    """Ingests an alert with safeguard against identical Wazuh IDs and signature-based hit aggregation.

    Returns:
        (inserted, deduplicated)
    """
    alert_id = str(a.get("alert_id") or a.get("id") or "").strip()
    wazuh_id = str(a.get("wazuh_id") or alert_id).strip()
    tenant = a.get("tenant") or "Default"
    sig = a.get("log_signature") or ""
    timestamp = a.get("timestamp") or ""

    # Safeguard 1: Exact alert already exists by alert_id or contained in wazuh_ids
    existing_by_id = conn.execute(
        """SELECT id FROM wazuh.alerts 
           WHERE (alert_id = %s OR wazuh_ids @> %s::jsonb) AND tenant = %s 
           LIMIT 1""",
        (alert_id, json.dumps([wazuh_id]), tenant),
    ).fetchone()
    if existing_by_id:
        return False, False  # Exactly the same alert already in DB, safe ignore

    # Safeguard 2: Signature deduplication across identical recurring logs
    instance_meta = {
        "id": alert_id or wazuh_id,
        "timestamp": timestamp,
        "agent_name": a.get("agent_name"),
        "agent_ip": a.get("agent_ip"),
        "location": a.get("location"),
        "full_log": a.get("full_log"),
    }

    if sig:
        existing_sig = conn.execute(
            """SELECT id, hit_count, first_seen, last_seen, wazuh_ids, duplicate_instances 
               FROM wazuh.alerts 
               WHERE tenant = %s AND log_signature = %s AND log_signature != '' 
               LIMIT 1""",
            (tenant, sig),
        ).fetchone()

        if existing_sig:
            pk = existing_sig["id"]
            current_count = existing_sig["hit_count"] or 1
            existing_w_ids = existing_sig["wazuh_ids"] or []
            existing_instances = existing_sig["duplicate_instances"] or []

            if wazuh_id and wazuh_id not in existing_w_ids:
                existing_w_ids.append(wazuh_id)
            existing_instances.append(instance_meta)

            # Update time bounds
            times = [t for t in (existing_sig["first_seen"], existing_sig["last_seen"], timestamp) if t]
            first_t = min(times) if times else timestamp
            last_t = max(times) if times else timestamp

            conn.execute(
                """UPDATE wazuh.alerts 
                   SET hit_count = %s,
                       first_seen = %s,
                       last_seen = %s,
                       wazuh_ids = %s::jsonb,
                       duplicate_instances = %s::jsonb
                   WHERE id = %s""",
                (
                    current_count + 1,
                    first_t,
                    last_t,
                    json.dumps(existing_w_ids),
                    json.dumps(existing_instances, ensure_ascii=False),
                    pk,
                ),
            )
            return False, True  # Deduplicated into existing row

    # New distinct alert row
    wazuh_ids = [wazuh_id] if wazuh_id else []
    instances = [instance_meta]

    values = (
        alert_id,
        timestamp,
        tenant,
        a.get("agent_name"),
        a.get("agent_ip"),
        a.get("rule_id"),
        a.get("rule_level"),
        a.get("description"),
        json.dumps(a.get("rule_groups") or []),
        a.get("decoder"),
        a.get("location"),
        a.get("source_ip"),
        json.dumps(a.get("mitre_ids") or []),
        a.get("cve"),
        json.dumps(a.get("data") or {}),
        json.dumps(a.get("raw") or {}, ensure_ascii=False),
        sig,
        1,
        timestamp,
        timestamp,
        json.dumps(wazuh_ids),
        json.dumps(instances, ensure_ascii=False),
        json.dumps(a.get("parsed_details") or {}),
        False,
        "",
    )

    cur = conn.execute(
        """INSERT INTO wazuh.alerts(
            alert_id, timestamp, tenant, agent_name, agent_ip, rule_id, rule_level,
            description, rule_groups, decoder, location, source_ip, mitre_ids,
            cve, data, raw, log_signature, hit_count, first_seen, last_seen,
            wazuh_ids, duplicate_instances, parsed_details, is_reviewed, reviewer_notes
        ) VALUES(
            %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s, %s::jsonb,
            %s, %s::jsonb, %s::jsonb, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s::jsonb, %s, %s
        ) ON CONFLICT(alert_id, timestamp, agent_name, rule_id) DO NOTHING RETURNING id""",
        values,
    )

    if cur.fetchone():
        return True, False
    return False, False
