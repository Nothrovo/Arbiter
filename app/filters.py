"""Kibana-style alert filter chips for Triage and Statistics.

Filters are user-authored field predicates such as ``rule.description not
contains "mhs"`` or ``rule.level range 7..12``. They are translated to
parameterized SQL through a closed field/operator whitelist: nothing from the
client ever reaches the statement as SQL text.

An empty/invalid document is rejected rather than silently ignored so the UI
can surface a 422 instead of showing misleading counts.
"""

from __future__ import annotations

import json
import re
from typing import Any

from fastapi import HTTPException

MAX_FILTERS = 40
MAX_FILTER_VALUE = 500
MAX_FILTER_FIELD = 60

_URL_EXPR = (
    "COALESCE(NULLIF(a.data->>'url', ''), "
    "NULLIF(a.data->>'uri', ''), "
    "NULLIF(a.parsed_details->>'uri', ''), "
    "NULLIF(a.parsed_details->>'path', ''), "
    "NULLIF(a.parsed_details->>'url_path', ''), '')"
)
_STATUS_EXPR = (
    "COALESCE(NULLIF(a.data->>'status', ''), NULLIF(a.data->>'id', ''), "
    "NULLIF(a.parsed_details->>'status', ''), NULLIF(a.parsed_details->>'http_status', ''), '')"
)
_GROUPS_EXPR = "COALESCE(a.rule_groups::text, '')"
_MITRE_EXPR = "COALESCE(a.mitre_ids::text, '')"

# field -> (label, SQL expression, kind). ``kind`` selects integer or text binding.
FILTER_FIELDS: dict[str, tuple[str, str, str]] = {
    "rule.level": ("Rule level", "a.rule_level", "int"),
    "rule.id": ("Rule ID", "COALESCE(a.rule_id, '')", "text"),
    "rule.description": ("Deskripsi rule", "COALESCE(a.description, '')", "text"),
    "rule.groups": ("Rule groups", _GROUPS_EXPR, "text"),
    "agent.name": ("Host / Agent", "COALESCE(a.agent_name, '')", "text"),
    "agent.ip": ("Agent IP", "COALESCE(a.agent_ip, '')", "text"),
    "data.srcip": ("Source IP", "COALESCE(a.source_ip, '')", "text"),
    "data.url": ("URL / Path", _URL_EXPR, "text"),
    "data.status": ("HTTP status", _STATUS_EXPR, "text"),
    "location": ("Location", "COALESCE(a.location, '')", "text"),
    "decoder": ("Decoder", "COALESCE(a.decoder, '')", "text"),
    "mitre.id": ("MITRE ID", _MITRE_EXPR, "text"),
    "cve": ("CVE", "COALESCE(a.cve, '')", "text"),
    "tenant": ("Tenant", "COALESCE(a.tenant, '')", "text"),
    "full_log": ("Full log", "COALESCE(a.raw->>'full_log', '')", "text"),
}

# Aliases accepted from the UI (Wazuh dotted names and short names).
FILTER_FIELD_ALIASES: dict[str, str] = {
    "rule_level": "rule.level",
    "level": "rule.level",
    "rule.rule_id": "rule.id",
    "rule_id": "rule.id",
    "rule.description": "rule.description",
    "description": "rule.description",
    "rule_description": "rule.description",
    "rule.groups": "rule.groups",
    "agent": "agent.name",
    "agent_name": "agent.name",
    "source_ip": "data.srcip",
    "srcip": "data.srcip",
    "url": "data.url",
    "url_path": "data.url",
    "http_status": "data.status",
    "status": "data.status",
    "mitre": "mitre.id",
    "raw": "full_log",
}

FILTER_OPS = (
    "is", "is_not", "contains", "not_contains", "glob", "not_glob",
    "regex", "not_regex", "range", "gte", "lte",
)

_OP_ALIASES = {
    "eq": "is",
    "=": "is",
    "==": "is",
    "neq": "is_not",
    "!=": "is_not",
    "not": "is_not",
    "like": "contains",
    "not_like": "not_contains",
    "not_glob": "not_glob",
    "gt": "gte",
    ">=": "gte",
    "lt": "lte",
    "<=": "lte",
    "between": "range",
}


def _error(message: str) -> HTTPException:
    return HTTPException(status_code=422, detail=message)


def _canonical_field(raw: Any) -> str:
    field = str(raw or "").strip()
    if not field or len(field) > MAX_FILTER_FIELD:
        raise _error("Field filter tidak valid.")
    if field in FILTER_FIELDS:
        return field
    alias = FILTER_FIELD_ALIASES.get(field.lower())
    if alias:
        return alias
    raise _error(f"Field filter '{field}' tidak didukung.")


def _canonical_op(raw: Any) -> str:
    op = str(raw or "is").strip().lower()
    op = _OP_ALIASES.get(op, op)
    if op not in FILTER_OPS:
        raise _error(f"Operator filter '{op}' tidak didukung.")
    return op


def _clean_value(raw: Any, *, field: str) -> str:
    value = "" if raw is None else str(raw)
    value = value.strip()
    if len(value) > MAX_FILTER_VALUE:
        raise _error(f"Nilai filter terlalu panjang (maksimal {MAX_FILTER_VALUE} karakter).")
    if any(ord(char) < 32 for char in value):
        raise _error("Nilai filter tidak boleh memuat karakter kontrol.")
    return value


def normalize_filter(raw: Any) -> dict[str, str]:
    """Validate one chip and return its canonical representation."""
    if not isinstance(raw, dict):
        raise _error("Filter tidak valid.")
    field = _canonical_field(raw.get("field"))
    op = _canonical_op(raw.get("op") or raw.get("operator") or "is")
    if field == "rule.level" and op in {"is", "is_not", "range", "gte", "lte"}:
        kind = "int"
    else:
        kind = FILTER_FIELDS[field][2]
    value = _clean_value(raw.get("value"), field=field)
    value2 = _clean_value(raw.get("value2", raw.get("value_to", "")), field=field)
    if op in {"range", "gte", "lte"} and kind != "int":
        raise _error(f"Operator '{op}' hanya tersedia untuk field numerik seperti rule.level.")
    if kind == "int":
        bound = []
        for part in (value, value2):
            if part == "":
                bound.append("")
                continue
            try:
                bound.append(str(int(part)))
            except ValueError as exc:
                raise _error(f"Nilai '{part}' harus berupa angka untuk {FILTER_FIELDS[field][0]}.") from exc
        value, value2 = bound
    if op in {"is", "is_not", "contains", "not_contains", "glob", "not_glob", "regex", "not_regex", "gte", "lte"} and not value:
        raise _error("Nilai filter tidak boleh kosong.")
    # Operators "is"/"is not" are exact comparisons. When the value carries glob
    # wildcards, honour them as glob so a chip like
    # "Full log is not */lib/x.php*" actually filters instead of doing a no-op
    # exact comparison. Numeric fields keep exact semantics.
    if kind != "int" and op in {"is", "is_not"} and ("*" in value or "?" in value):
        op = "glob" if op == "is" else "not_glob"
    if op == "range" and not (value and value2):
        raise _error("Rentang filter membutuhkan nilai awal dan akhir.")
    if op in {"regex", "not_regex"}:
        try:
            re.compile(value)
        except re.error as exc:
            raise _error(f"Regex filter tidak valid: {exc}") from None
    return {"field": field, "op": op, "value": value, "value2": value2}


def parse_filters(raw: Any) -> list[dict[str, str]]:
    """Normalize a JSON string, list, or ``None`` into filter chips."""
    if raw is None or raw == "":
        return []
    if isinstance(raw, str):
        text = raw.strip()
        if not text:
            return []
        try:
            raw = json.loads(text)
        except json.JSONDecodeError as exc:
            raise _error("Parameter filters harus berupa JSON yang valid.") from exc
    if isinstance(raw, dict):
        raw = raw.get("filters", [raw]) if "field" not in raw else [raw]
    if not isinstance(raw, list):
        raise _error("Parameter filters harus berupa daftar filter.")
    if len(raw) > MAX_FILTERS:
        raise _error(f"Maksimal {MAX_FILTERS} filter per permintaan.")
    return [normalize_filter(item) for item in raw]


def _escape_like(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _glob_to_like(pattern: str) -> str:
    out: list[str] = []
    for char in pattern:
        if char == "*":
            out.append("%")
        elif char == "?":
            out.append("_")
        elif char in ("\\", "%", "_"):
            out.append("\\" + char)
        else:
            out.append(char)
    return "".join(out)


def _predicate(item: dict[str, str]) -> tuple[str, list[Any]]:
    field, op = item["field"], item["op"]
    _label, expression, kind = FILTER_FIELDS[field]
    value, value2 = item["value"], item.get("value2", "")

    if op in {"range", "gte", "lte"}:
        if op == "gte":
            return f"{expression} >= %s", [int(value)]
        if op == "lte":
            return f"{expression} <= %s", [int(value)]
        low, high = sorted((int(value), int(value2)))
        return f"{expression} BETWEEN %s AND %s", [low, high]

    negated = op.startswith("not_") or op.endswith("_not")
    if op.startswith("not_"):
        base = op[4:]
    elif op.endswith("_not"):
        base = op[:-4]
    else:
        base = op
    bound_value: Any = int(value) if kind == "int" and base == "is" else value
    if base == "is":
        sql, params = f"{expression} = %s", [bound_value]
    elif base == "contains":
        sql, params = f"{expression} ILIKE %s ESCAPE '\\'", [f"%{_escape_like(value)}%"]
    elif base == "glob":
        sql, params = f"{expression} ILIKE %s ESCAPE '\\'", [_glob_to_like(value)]
    elif base == "regex":
        sql, params = f"{expression} ~* %s", [value]
    else:  # pragma: no cover - normalize_filter rejects unknown ops
        raise _error(f"Operator filter '{op}' tidak didukung.")
    if negated:
        return f"NOT ({sql})", params
    return sql, params


def build_filter_sql(filters: Any) -> tuple[str, list[Any]]:
    """Return a parenthesised AND predicate and its bound parameters."""
    parsed = parse_filters(filters)
    if not parsed:
        return "", []
    predicates: list[str] = []
    params: list[Any] = []
    for item in parsed:
        sql, bound = _predicate(item)
        predicates.append(sql)
        params.extend(bound)
    return "(" + " AND ".join(predicates) + ")", params
