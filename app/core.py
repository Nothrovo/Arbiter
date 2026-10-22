"""Core normalization, deduplication, and deterministic correlation logic for Arbiter."""

from __future__ import annotations

import json
from collections import defaultdict
from typing import Any

from app.parser import (
    as_dict,
    build_log_signature,
    clean_val,
    parse_log_line,
    parse_timestamp_iso,
    valid_ip,
)


def normalize_alert(raw: dict[str, Any]) -> dict[str, Any]:
    """Normalizes raw alert data from Wazuh/Elasticsearch into Arbiter's unified model."""
    raw_dict = dict(raw or {})
    agent = as_dict(raw_dict.get("agent"))
    agent_labels = as_dict(agent.get("labels"))
    rule = as_dict(raw_dict.get("rule"))
    data = as_dict(raw_dict.get("data"))
    vulnerability = as_dict(data.get("vulnerability"))

    # Extract Tenant
    tenant = (
        clean_val(agent_labels.get("tenant"))
        or clean_val(raw_dict.get("tenant"))
        or clean_val(raw_dict.get("tenant_id"))
        or "Default"
    )

    # Extract Source IP
    source_ip = (
        valid_ip(data.get("srcip"))
        or valid_ip(data.get("src_ip"))
        or valid_ip(data.get("source_ip"))
        or valid_ip(raw_dict.get("srcip"))
    )

    full_log = raw_dict.get("full_log") or ""
    if not isinstance(full_log, str):
        try:
            full_log = json.dumps(full_log, ensure_ascii=False)
        except Exception:
            full_log = str(full_log)

    raw_ts = raw_dict.get("timestamp") or raw_dict.get("@timestamp")
    parsed = parse_log_line(full_log, raw_ts)
    if not source_ip and parsed.get("srcip"):
        source_ip = valid_ip(parsed["srcip"])

    alert_id = clean_val(raw_dict.get("id") or raw_dict.get("_id") or raw_dict.get("wazuh_id") or "")
    wazuh_id = clean_val(raw_dict.get("wazuh_id") or raw_dict.get("_id") or alert_id)

    # Compute stable log signature for deduplication
    sig = build_log_signature(
        {
            "full_log": full_log,
            "rule": rule,
            "agent": agent,
            "tenant": tenant,
            "data": data,
        },
        parsed,
    )

    timestamp_iso = parse_timestamp_iso(raw_ts) or parsed.get("timestamp_iso") or ""

    return {
        "alert_id": alert_id,
        "wazuh_id": wazuh_id,
        "timestamp": timestamp_iso,
        "tenant": tenant,
        "agent_name": clean_val(agent.get("name") or agent.get("hostname") or "-"),
        "agent_ip": clean_val(agent.get("ip") or "-"),
        "rule_id": clean_val(rule.get("id") or "-"),
        "rule_level": int(rule.get("level") or 0) if rule.get("level") is not None else 0,
        "description": clean_val(rule.get("description") or vulnerability.get("title") or "Wazuh Alert"),
        "rule_groups": rule.get("groups") or [],
        "decoder": clean_val(as_dict(raw_dict.get("decoder")).get("name") or parsed.get("format") or "-"),
        "location": clean_val(raw_dict.get("location") or "-"),
        "source_ip": source_ip or "",
        "mitre_ids": as_dict(rule.get("mitre")).get("id") or [],
        "cve": clean_val(vulnerability.get("cve")),
        "log_signature": sig,
        "full_log": full_log,
        "previous_output": clean_val(raw_dict.get("previous_output")),
        "parsed_details": parsed,
        "data": data,
        "raw": raw_dict,
        "first_seen": timestamp_iso,
        "last_seen": timestamp_iso,
        "hit_count": 1,
        "is_reviewed": False,
        "reviewer_notes": "",
    }


def suggest_groups(alerts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Local deterministic grouping; no text or log is transmitted to any model."""
    rules = [
        ("Same source + rule", lambda a: (a.get("source_ip"), a.get("rule_id")) if a.get("source_ip") and a.get("rule_id") and a.get("rule_id") != "-" else None),
        ("Same agent + rule", lambda a: (a.get("agent_name"), a.get("rule_id")) if a.get("agent_name") and a.get("rule_id") and a.get("rule_id") != "-" else None),
        ("Same CVE identifier", lambda a: a.get("cve") if a.get("cve") else None),
        ("Identical Log Signature", lambda a: a.get("log_signature") if a.get("log_signature") else None),
    ]
    out = []
    for category, keyfn in rules:
        buckets: dict[Any, list[str]] = defaultdict(list)
        for alert in alerts:
            key = keyfn(alert)
            if key:
                buckets[key].append(str(alert.get("id") or alert.get("alert_id")))
        for key, ids in buckets.items():
            unique = list(dict.fromkeys(ids))
            if len(unique) > 1:
                out.append({
                    "category": category,
                    "key": list(key) if isinstance(key, tuple) else key,
                    "alert_ids": unique,
                })
    return out


class LocalAIUnavailable(RuntimeError):
    """Local inference endpoint failed or returned an unusable response."""


def ollama_request(prompt: str, model: str, base_url: str) -> str:
    """Invokes ONLY a loopback Ollama endpoint; remote/cloud hosts are strictly refused."""
    from urllib.parse import urlparse
    from urllib.request import Request, urlopen

    parsed = urlparse(base_url)
    if parsed.scheme != "http" or parsed.hostname not in {"localhost", "127.0.0.1", "::1"}:
        raise LocalAIUnavailable("Local AI endpoint must use http://localhost or a loopback IP; cloud hosts are refused.")
    body = json.dumps({"model": model, "prompt": prompt, "stream": False, "format": "json"}).encode("utf-8")
    request = Request(
        base_url.rstrip("/") + "/api/generate",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=12) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        raise LocalAIUnavailable(f"Local AI is unavailable: {exc}") from exc
    text = payload.get("response")
    if not isinstance(text, str):
        raise LocalAIUnavailable("Local AI returned no response text.")
    return text


def local_ai_suggest_groups(alerts: list[dict[str, Any]], model: str, base_url: str) -> list[dict[str, Any]]:
    # Raw JSON and full_logs are strictly excluded; only sanitized structured tuples are sent to loopback.
    allowed_fields = ("id", "alert_id", "timestamp", "agent_name", "rule_id", "rule_level", "description", "source_ip", "rule_groups", "cve", "mitre_ids")
    safe_alerts = [{k: a.get(k) for k in allowed_fields} for a in alerts[:150]]
    prompt = (
        "Group only alerts that plausibly belong to the same event. Do not infer missing facts. "
        "Return JSON array items {\"category\":string,\"key\":string,\"alert_ids\":[string,...]}. "
        "Use only input IDs, and require at least two alerts per group. Input: "
        + json.dumps(safe_alerts, ensure_ascii=False)
    )
    try:
        value = json.loads(ollama_request(prompt, model, base_url))
    except (json.JSONDecodeError, TypeError) as exc:
        raise LocalAIUnavailable("Local AI returned malformed JSON; deterministic rules will be used.") from exc
    if not isinstance(value, list):
        raise LocalAIUnavailable("Local AI response must be a JSON array.")
    allowed_ids = {str(a.get("id") or a.get("alert_id")) for a in alerts[:150]}
    result = []
    for item in value:
        if not isinstance(item, dict) or not isinstance(item.get("alert_ids"), list):
            continue
        ids = list(dict.fromkeys(str(x) for x in item["alert_ids"] if str(x) in allowed_ids))
        if len(ids) >= 2:
            result.append({
                "category": str(item.get("category") or "AI suggestion")[:120],
                "key": str(item.get("key") or "local model suggestion")[:300],
                "alert_ids": ids,
            })
    return result


def suggestions_with_fallback(
    alerts: list[dict[str, Any]],
    enabled: bool,
    model: str = "qwen2.5:3b",
    base_url: str = "http://127.0.0.1:11434",
) -> tuple[list[dict[str, Any]], str, str | None]:
    if not enabled:
        return suggest_groups(alerts), "local_rules", None
    try:
        return local_ai_suggest_groups(alerts, model=model, base_url=base_url), "local_ai", None
    except Exception as exc:
        return suggest_groups(alerts), "local_rules_fallback", str(exc)
