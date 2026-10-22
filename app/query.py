"""Shared parameterized alert predicates; no database or configuration imports."""
from __future__ import annotations

import re
from typing import Any

from fastapi import HTTPException


def validated_group_id(value: str | None) -> str | None:
    if value is not None and not re.fullmatch(r"[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}", value):
        raise HTTPException(status_code=422, detail="group_id must be a UUID.")
    return value


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
    *, q: str = "", tenant: str = "all", status: str = "all",
    group_id: str | None = None, filter_preset: str = "",
    review_status: str = "all",
    time_from: str | None = None, time_to: str | None = None,
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
    if tenant and tenant != "all":
        clauses.append("a.tenant = %s")
        params.append(tenant)
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
    return ("WHERE " + " AND ".join(clauses) if clauses else ""), params
