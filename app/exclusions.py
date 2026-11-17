"""Custom exclusion rules for exploratory alert views.

Exclusions are operator-defined noise filters. They hide matching alerts from
Triage, Statistics, summaries, and AI triage candidates. They never delete
alerts, never mutate incident evidence, and never affect an export that names
alerts or an incident explicitly.

Rules are stored in the local settings document under ``exclusions`` and are
translated to parameterized SQL only through the closed whitelists below.
"""

from __future__ import annotations

import re
import uuid
from collections.abc import Iterable
from typing import Any

MAX_EXCLUSION_RULES = 200
MAX_EXCLUSION_PATTERN = 300
MAX_EXCLUSION_LABEL = 160
EXCLUSION_MATCHES = ("glob", "contains", "exact", "regex")

# Every expression is a trusted SQL fragment; user input is always bound.
_URL_EXPR = (
    "COALESCE(NULLIF(a.data->>'url', ''), "
    "NULLIF(a.data->>'uri', ''), "
    "NULLIF(a.parsed_details->>'path', ''), "
    "NULLIF(a.parsed_details->>'uri', ''), "
    "NULLIF(a.parsed_details->>'url_path', ''), '')"
)

EXCLUSION_FIELDS: dict[str, tuple[str, ...]] = {
    "url": (_URL_EXPR, f"split_part({_URL_EXPR}, '?', 1)"),
    "source_ip": ("COALESCE(a.source_ip, '')",),
    "agent": ("COALESCE(a.agent_name, '')",),
    "rule_id": ("COALESCE(a.rule_id, '')",),
    "rule_description": ("COALESCE(a.description, '')",),
    "http_method": ("COALESCE(a.parsed_details->>'method', '')",),
    "http_status": (
        "COALESCE(NULLIF(a.data->>'status', ''), NULLIF(a.data->>'id', ''), "
        "NULLIF(a.parsed_details->>'status', ''), NULLIF(a.parsed_details->>'http_status', ''), '')",
    ),
    "referer": ("COALESCE(a.parsed_details->>'referer', '')",),
    "user_agent": ("COALESCE(a.parsed_details->>'ua', '', a.parsed_details->>'user_agent', '')",),
    "location": ("COALESCE(a.location, '')",),
    "tenant": ("COALESCE(a.tenant, '')",),
    "syscheck_path": (
        "COALESCE(a.raw->'syscheck'->>'path', '')",
        "COALESCE(a.data->'syscheck'->>'path', '')",
    ),
    "any": ("COALESCE(a.raw::text, '')", "COALESCE(a.parsed_details::text, '')"),
}

EXCLUSION_FIELD_LABELS: dict[str, str] = {
    "url": "URL / Path",
    "source_ip": "Source IP",
    "agent": "Host / Agent",
    "rule_id": "Rule ID",
    "rule_description": "Deskripsi rule",
    "http_method": "HTTP Method",
    "http_status": "HTTP status",
    "referer": "HTTP Referer",
    "user_agent": "User-Agent",
    "location": "Location",
    "tenant": "Tenant",
    "syscheck_path": "Syscheck path",
    "any": "Semua teks alert",
}

_WAZUH_FIELD_ALIASES: dict[str, str] = {
    "data.url": "url",
    "data.uri": "url",
    "url": "url",
    "uri": "url",
    "data.srcip": "source_ip",
    "srcip": "source_ip",
    "source_ip": "source_ip",
    "agent.name": "agent",
    "agent": "agent",
    "rule.id": "rule_id",
    "rule_id": "rule_id",
    "rule.description": "rule_description",
    "rule_description": "rule_description",
    "data.method": "http_method",
    "method": "http_method",
    "http_method": "http_method",
    "data.status": "http_status",
    "status": "http_status",
    "http_status": "http_status",
    "data.referer": "referer",
    "referer": "referer",
    "data.user_agent": "user_agent",
    "data.ua": "user_agent",
    "user_agent": "user_agent",
    "location": "location",
    "data.tenant": "tenant",
    "tenant": "tenant",
    "syscheck.path": "syscheck_path",
    "syscheck_path": "syscheck_path",
}

_RULE_ID_RX = re.compile(r"^[0-9a-fA-F-]{8,36}$")


def _escape_like(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def glob_to_like(pattern: str) -> str:
    """Translate wildcard globs to a LIKE pattern (case-sensitive)."""
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


def _coerce_enabled(value: Any, default: bool = True) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if value in (0, 1):
        return bool(value)
    raise ValueError("exclusions.enabled harus berupa boolean (true/false).")


def normalize_exclusion_rule(raw: Any) -> dict[str, Any]:
    """Validate one rule. Field and match are closed whitelists."""
    if not isinstance(raw, dict):
        raise ValueError("Aturan pengecualian tidak valid.")
    field = str(raw.get("field") or "url").strip()
    if field not in EXCLUSION_FIELDS:
        raise ValueError(f"Field pengecualian '{field}' tidak didukung.")
    match = str(raw.get("match") or "glob").strip().lower()
    if match not in EXCLUSION_MATCHES:
        raise ValueError("Mode pencocokan harus glob, contains, exact, atau regex.")
    pattern = str(raw.get("pattern") or "").strip()
    if pattern.lower().startswith("not "):
        pattern = pattern[4:].strip()
    if not pattern:
        raise ValueError("Pola pengecualian tidak boleh kosong.")
    if len(pattern) > MAX_EXCLUSION_PATTERN:
        raise ValueError(f"Pola pengecualian terlalu panjang (maksimal {MAX_EXCLUSION_PATTERN} karakter).")
    if any(ord(char) < 32 for char in pattern):
        raise ValueError("Pola pengecualian tidak boleh memuat karakter kontrol.")
    if match == "regex":
        try:
            re.compile(pattern)
        except re.error as exc:
            hint = " Gunakan mode Glob untuk pola dengan * atau ?." if ("*" in pattern or "?" in pattern) else ""
            raise ValueError(f"Regex pengecualian tidak valid: {exc}.{hint}") from None
    label = str(raw.get("label") or "").strip()
    if len(label) > MAX_EXCLUSION_LABEL:
        label = label[:MAX_EXCLUSION_LABEL]
    candidate_id = str(raw.get("id") or "").strip()
    rule_id = candidate_id if _RULE_ID_RX.fullmatch(candidate_id) else str(uuid.uuid4())
    return {
        "id": rule_id,
        "field": field,
        "match": match,
        "pattern": pattern,
        "label": label,
        "enabled": _coerce_enabled(raw.get("enabled"), True),
    }


def normalize_exclusions(raw: Any) -> dict[str, Any]:
    """Return a canonical exclusion document with unique, valid rules."""
    if raw is None:
        raw = {}
    if not isinstance(raw, dict):
        raise ValueError("Bagian exclusions tidak valid.")
    enabled = _coerce_enabled(raw.get("enabled"), True)
    rules_raw = raw.get("rules") or []
    if not isinstance(rules_raw, list):
        raise ValueError("exclusions.rules harus berupa daftar.")
    if len(rules_raw) > MAX_EXCLUSION_RULES:
        raise ValueError(f"Maksimal {MAX_EXCLUSION_RULES} aturan pengecualian.")
    rules: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for item in rules_raw:
        rule = normalize_exclusion_rule(item)
        key = (rule["field"], rule["match"], rule["pattern"])
        if key in seen:
            continue
        seen.add(key)
        rules.append(rule)
    return {"enabled": enabled, "rules": rules}


def active_exclusion_rules(document: Any) -> list[dict[str, Any]]:
    """Return enabled rules, or an empty list for a disabled/malformed document."""
    if not isinstance(document, dict) or document.get("enabled") is False:
        return []
    rules = document.get("rules")
    if not isinstance(rules, list):
        return []
    return [rule for rule in rules if isinstance(rule, dict) and rule.get("enabled", True)]


def build_exclusion_sql(document: Any) -> tuple[str, list[Any]]:
    """Build a parameterized NOT(...) predicate for enabled exclusion rules."""
    predicates: list[str] = []
    params: list[Any] = []
    for rule in active_exclusion_rules(document):
        field = str(rule.get("field") or "")
        expressions = EXCLUSION_FIELDS.get(field)
        if not expressions:
            continue
        match = str(rule.get("match") or "glob").lower()
        pattern = str(rule.get("pattern") or "").strip()
        if not pattern:
            continue
        expressions_sql: list[str] = []
        for expression in expressions:
            if match == "glob":
                expressions_sql.append(f"{expression} LIKE %s ESCAPE '\\'")
                params.append(glob_to_like(pattern))
            elif match == "contains":
                expressions_sql.append(f"{expression} LIKE %s ESCAPE '\\'")
                params.append(f"%{_escape_like(pattern)}%")
            elif match == "exact":
                expressions_sql.append(f"{expression} = %s")
                params.append(pattern)
            elif match == "regex":
                expressions_sql.append(f"{expression} ~ %s")
                params.append(pattern)
        if expressions_sql:
            predicates.append("(" + " OR ".join(expressions_sql) + ")")
    if not predicates:
        return "", []
    return "NOT (" + " OR ".join(predicates) + ")", params


def with_exclusions(
    where_sql: str, params: Iterable[Any], document: Any
) -> tuple[str, list[Any]]:
    """Append global exclusions to an existing WHERE clause."""
    clause, extra = build_exclusion_sql(document)
    result = list(params)
    if not clause:
        return where_sql, result
    joiner = " AND " if where_sql.strip() else "WHERE "
    return where_sql + joiner + clause, result + extra


def _split_top_level(text: str, separator: str) -> list[str]:
    """Split on a case-insensitive separator outside parentheses and quotes."""
    parts: list[str] = []
    depth = 0
    quote = ""
    start = 0
    index = 0
    lowered = text.lower()
    separator = separator.lower()
    while index < len(text):
        char = text[index]
        if quote:
            if char == quote and (index == 0 or text[index - 1] != "\\"):
                quote = ""
        elif char in ('"', "'"):
            quote = char
        elif char == "(":
            depth += 1
        elif char == ")":
            depth = max(0, depth - 1)
        elif depth == 0 and lowered.startswith(separator, index):
            before = text[index - 1] if index > 0 else " "
            after_index = index + len(separator)
            after = text[after_index] if after_index < len(text) else " "
            if before.isspace() and after.isspace():
                parts.append(text[start:index])
                index = after_index
                start = index
                continue
        index += 1
    parts.append(text[start:])
    return [part.strip() for part in parts if part.strip()]


def _strip_outer_parentheses(text: str) -> str:
    value = text.strip()
    while value.startswith("(") and value.endswith(")"):
        depth = 0
        balanced = True
        for index, char in enumerate(value):
            if char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth == 0 and index != len(value) - 1:
                    balanced = False
                    break
        if not balanced or depth != 0:
            break
        value = value[1:-1].strip()
    return value


def parse_wazuh_exclusion(expression: Any) -> list[dict[str, Any]]:
    """Parse a Wazuh-style ``not (field: (a or b) or field: c)`` exclusion.

    Only the exclusion shape used by operators is supported: a top-level ``not``
    (optional), one or more ``field: value`` terms joined by ``or``, and
    parenthesised value lists. Anything else is rejected instead of guessed.
    """
    text = str(expression or "").strip()
    if not text:
        raise ValueError("Query Wazuh kosong.")
    if re.match(r"(?i)^not\b", text):
        text = text[3:].strip()
    text = _strip_outer_parentheses(text)
    if not text:
        raise ValueError("Query Wazuh tidak memuat pola pengecualian.")
    rules: list[dict[str, Any]] = []
    for term in _split_top_level(text, "or"):
        if ":" not in term:
            raise ValueError("Setiap bagian query harus memakai format field: pola.")
        field_raw, value_raw = term.split(":", 1)
        field = _WAZUH_FIELD_ALIASES.get(field_raw.strip().lower())
        if not field:
            raise ValueError(f"Field Wazuh '{field_raw.strip()}' belum didukung untuk pengecualian.")
        values_text = _strip_outer_parentheses(value_raw.strip())
        for value in _split_top_level(values_text, "or"):
            pattern = value.strip().strip('"').strip("'").strip()
            if not pattern or pattern == "*":
                continue
            match = "glob" if ("*" in pattern or "?" in pattern) else "exact"
            rules.append({
                "id": str(uuid.uuid4()),
                "field": field,
                "match": match,
                "pattern": pattern,
                "label": "Impor query Wazuh",
                "enabled": True,
            })
    if not rules:
        raise ValueError("Query Wazuh tidak menghasilkan pola pengecualian.")
    return [normalize_exclusion_rule(rule) for rule in rules]
