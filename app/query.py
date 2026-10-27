"""Shared parameterized alert predicates; no database or configuration imports."""
from __future__ import annotations

import re
from collections.abc import Sequence
from typing import Any

from fastapi import HTTPException


def validated_group_id(value: str | None) -> str | None:
    if value is not None and not re.fullmatch(r"[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}", value):
        raise HTTPException(status_code=422, detail="group_id must be a UUID.")
    return value


# These names are an API contract, not client-provided SQL. Task 2 reuses this
# exact closed set for pivots and drill-down facets.
FACET_COLUMNS = {
    "rule_description": "a.description",
    "rule_id": "a.rule_id",
    "severity": "a.rule_level",
    "source_ip": "a.source_ip",
    "agent": "a.agent_name",
    "referer": "a.parsed_details->>'referer'",
    "http_status": "a.parsed_details->>'status'",
    "url_path": "a.parsed_details->>'url_path'",
    "user_agent": "a.parsed_details->>'user_agent'",
    "tenant": "a.tenant",
}


def normalize_tenants(values: str | Sequence[str] | None) -> tuple[str, ...]:
    """Return the canonical exact tenant set; an empty tuple represents all."""
    if values is None:
        return ()
    raw_values = [values] if isinstance(values, str) else list(values)
    if not raw_values:
        return ()
    tenants = [str(value).strip() for value in raw_values]
    if any(not value for value in tenants):
        raise HTTPException(status_code=422, detail="tenant must not be blank.")
    unique = tuple(sorted(set(tenants)))
    if "all" in unique:
        if len(unique) != 1:
            raise HTTPException(status_code=422, detail="tenant=all cannot be combined with named tenants.")
        return ()
    return unique


def tenant_clause(alias: str, values: str | Sequence[str] | None) -> tuple[str, list[Any]]:
    """Build a bound exact-set tenant predicate for a trusted query alias."""
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", alias):
        raise ValueError("SQL alias must be a simple identifier.")
    tenants = normalize_tenants(values)
    return (f"{alias}.tenant = ANY(%s)", [list(tenants)]) if tenants else ("", [])


def positive_ids(values: list[Any]) -> list[int]:
    """Validate every explicit ID; never silently discard a bad selection."""
    result = []
    for value in values:
        token = str(value)
        if not token.isascii() or not token.isdecimal() or int(token) < 1:
            raise ValueError("Alert IDs must be positive integers.")
        number = int(token)
        if number > 9_223_372_036_854_775_807:
            raise ValueError("Alert ID exceeds the supported integer range.")
        if number not in result:
            result.append(number)
    return result


def alert_where(
    *, q: str = "", tenant: str | Sequence[str] | None = "all", status: str = "all",
    group_id: str | None = None, filter_preset: str = "",
    review_status: str = "all",
    time_from: str | None = None, time_to: str | None = None,
    facet: str = "", facet_value: str = "",
) -> tuple[str, list[Any]]:
    group_id = validated_group_id(group_id)
    clauses: list[str] = []
    params: list[Any] = []
    if q:
        columns = (
            "a.alert_id", "a.agent_name", "a.agent_ip", "a.rule_id", "a.description",
            "a.source_ip", "a.cve", "a.tenant", "a.location", "a.decoder", "a.raw::text",
        )
        clauses.append("(" + " OR ".join(f"{column} ILIKE %s" for column in columns) + ")")
        params.extend([f"%{q}%"] * len(columns))
    tenant_sql, tenant_params = tenant_clause("a", tenant)
    if tenant_sql:
        clauses.append(tenant_sql)
        params.extend(tenant_params)
    if status in {"grouped", "ungrouped"}:
        prefix = "NOT " if status == "ungrouped" else ""
        clauses.append(prefix + "EXISTS (SELECT 1 FROM wazuh.alert_group_members m WHERE m.alert_pk = a.id)")
    if group_id and group_id.strip():
        clauses.append("EXISTS (SELECT 1 FROM wazuh.alert_group_members m WHERE m.alert_pk = a.id AND m.group_id = %s::uuid)")
        params.append(group_id.strip())
    if review_status in {"reviewed", "unreviewed"}:
        clauses.append("a.is_reviewed = " + ("true" if review_status == "reviewed" else "false"))
    if filter_preset in {"403", "404"}:
        clauses.append("(a.raw::text ILIKE %s OR a.parsed_details->>'status' = %s)")
        params.extend([f"% {filter_preset} %", filter_preset])
    elif filter_preset == "repeating":
        clauses.append("a.hit_count > 1")
    elif filter_preset == "bot":
        clauses.append("(a.description ILIKE %s OR a.raw::text ILIKE %s)")
        params.extend(["%bot%", "%bot%"])
    elif filter_preset == "curl":
        clauses.append("a.raw::text ILIKE %s")
        params.append("%curl%")
    elif filter_preset == "non_http":
        clauses.append("a.parsed_details->>'log_type' != 'http'")
    if time_from and str(time_from).strip():
        clauses.append("a.timestamp >= %s")
        params.append(str(time_from).strip())
    if time_to and str(time_to).strip():
        clauses.append("a.timestamp <= %s")
        params.append(str(time_to).strip())
    if facet or facet_value:
        if facet not in FACET_COLUMNS or not str(facet_value).strip():
            raise HTTPException(status_code=422, detail="facet and facet_value must use a supported exact facet.")
        clauses.append(f"{FACET_COLUMNS[facet]} = %s")
        params.append(str(facet_value).strip())
    return ("WHERE " + " AND ".join(clauses) if clauses else ""), params
