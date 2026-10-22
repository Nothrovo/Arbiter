"""Advanced multi-format log parser and extractor for Arbiter.

Combines high-precision regex decoders for Apache/Nginx access logs,
Syslog, AppArmor, sshd, and kernel audit logs with resilient JSON export
decoding (supporting Elasticsearch hits, unescaped newlines, and raw logs).
"""

from __future__ import annotations

import ipaddress
import json
import re
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from typing import Any

WIB = timezone(timedelta(hours=7))

# Combined access log pattern (Apache/Nginx)
ACCESS_LOG_RE = re.compile(
    r'^(?P<srcip>\S+)\s+(?P<ident>\S+)\s+(?P<auth>\S+)\s+'
    r'\[(?P<timestamp>[^\]]+)\]\s+"(?P<method>[A-Z]+)\s+(?P<uri>[^"\s]+)'
    r'(?:\s+(?P<protocol>HTTP/[0-9.]+))?"\s+(?P<status>\d{3})\s+(?P<bytes>\S+)'
    r'(?:\s+"(?P<referer>[^"]*)"\s+"(?P<ua>[^"]*)")?'
)

# Embedded HTTP request pattern inside other logs
HTTP_REQUEST_RE = re.compile(
    r'"(?P<method>[A-Z]+)\s+(?P<uri>[^"\s]+)'
    r'(?:\s+(?P<protocol>HTTP/[0-9.]+))?"'
)

SYSLOG_RE = re.compile(
    r'^(?P<timestamp>[A-Z][a-z]{2}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}(?:\.\d+)?)'
    r'\s+(?P<hostname>\S+)\s+(?P<rest>.*)$',
    re.S,
)

ISO_LOG_RE = re.compile(
    r'^(?P<timestamp>\d{4}[-/]\d{2}[-/]\d{2}[T ]\d{2}:\d{2}:\d{2}'
    r'(?:[.,]\d+)?(?:Z|[+-]\d{2}:?\d{2})?)\s+(?P<hostname>\S+)\s+(?P<rest>.*)$',
    re.S,
)

PROGRAM_RE = re.compile(
    r'^(?P<program>[A-Za-z0-9_.@/\-]+)(?:\[(?P<pid>\d+)\])?:\s*(?P<message>.*)$',
    re.S,
)

KV_RE = re.compile(
    r'(?P<key>[A-Za-z_][A-Za-z0-9_.\-]*)='
    r'(?:"(?P<qval>[^"]*)"|(?P<val>[^\s,]+))'
)

IPV4_RE = re.compile(r'(?<![\w.])(?:\d{1,3}\.){3}\d{1,3}(?![\w.])')
IPV6_RE = re.compile(r'(?<![\w:])(?:[0-9a-fA-F]{1,4}:){2,}[0-9a-fA-F:.]*(?![\w:])')

TIMESTAMP_FORMATS = (
    "%d/%b/%Y:%H:%M:%S %z",
    "%d/%b/%Y:%H:%M:%S",
    "%b %d %H:%M:%S",
    "%b %d %Y %H:%M:%S",
    "%Y/%m/%d %H:%M:%S",
    "%Y-%m-%d %H:%M:%S",
)

HTTP_STATUS_RE = re.compile(r'^\d{3}$')


def clean_val(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if text in ("-", "null", "None", "N/A", "n/a"):
        return ""
    return text


def as_dict(value: Any) -> dict:
    return value if isinstance(value, dict) else {}


def valid_ip(value: Any) -> str:
    text = str(value or "").strip().strip("[]()<>,;\"'")
    if not text:
        return ""
    if text.startswith("[") and "]" in text:
        text = text[1 : text.index("]")]
    elif text.count(":") == 1 and re.search(r":\d{1,5}$", text):
        text = text.rsplit(":", 1)[0]
    try:
        return str(ipaddress.ip_address(text))
    except ValueError:
        return ""


def first_ip_in(text: str) -> str:
    """Finds the first valid IP from a log message string."""
    for pattern in (
        r'\bsrcip\s*[=:]\s*["\']?([0-9a-fA-F:.]+)',
        r'\bsrc\s*[=:]\s*["\']?([0-9a-fA-F:.]+)',
        r'\bfrom\s+["\']?([0-9a-fA-F:.]+)',
        r'\bclient(?:\s*ip)?\s*[=:]?\s*["\']?([0-9a-fA-F:.]+)',
    ):
        match = re.search(pattern, text, re.I)
        if match:
            ip = valid_ip(match.group(1))
            if ip:
                return ip
    for match in IPV4_RE.finditer(text):
        ip = valid_ip(match.group(0))
        if ip:
            return ip
    for match in IPV6_RE.finditer(text):
        ip = valid_ip(match.group(0))
        if ip:
            return ip
    return ""


def parse_to_datetime(value: Any, reference: Any = None) -> datetime | None:
    """Parses a timestamp string or epoch into timezone-aware datetime."""
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(float(value), tz=timezone.utc)
        except (ValueError, OSError, OverflowError):
            return None
    else:
        text = str(value).strip().strip("[]")
        if not text:
            return None
        text = re.sub(r'([+-]\d{2})(\d{2})$', r'\1:\2', text)
        text = re.sub(r'(\d),(\d)', r'\1.\2', text)
        dt = None
        try:
            dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            for fmt in TIMESTAMP_FORMATS:
                try:
                    dt = datetime.strptime(text, fmt)
                    break
                except ValueError:
                    continue
        if dt is None:
            return None

    ref_dt = parse_to_datetime(reference) if reference is not None and reference is not value else None
    if dt.tzinfo is None:
        if dt.year == 1900:
            ref_year = (ref_dt or datetime.now(WIB)).year
            dt = dt.replace(year=ref_year)
            if ref_dt is not None:
                ref_naive = ref_dt.replace(tzinfo=None)
                if dt - ref_naive > timedelta(days=30):
                    dt = dt.replace(year=ref_year - 1)
                elif ref_naive - dt > timedelta(days=330):
                    dt = dt.replace(year=ref_year + 1)
        dt = dt.replace(tzinfo=WIB)
    return dt


def parse_timestamp_iso(value: Any, reference: Any = None) -> str | None:
    dt = parse_to_datetime(value, reference)
    return dt.isoformat() if dt else None


def short_action_desc(message: str) -> str:
    patterns = (
        r'(Failed password[^,;]*)',
        r'(Invalid user[^,;]*)',
        r'(Accepted password[^,;]*)',
        r'(Accepted publickey[^,;]*)',
        r'(Did not receive identification string[^,;]*)',
        r'(session (?:opened|closed)[^,;]*)',
        r'(Connection (?:closed|reset)[^,;]*)',
        r'(authentication failure[^,;]*)',
        r'(apparmor="[^"]+")',
    )
    for pattern in patterns:
        match = re.search(pattern, message, re.I)
        if match:
            return match.group(1).strip()
    return ""


def kv_details(message: str) -> str:
    parts = []
    for match in KV_RE.finditer(message):
        key = match.group("key")
        value = match.group("qval")
        if value is None:
            value = match.group("val") or ""
        parts.append(f"{key}={value}")
    return ", ".join(parts)


def parse_log_line(line: Any, reference_ts: Any = None) -> dict[str, Any]:
    """Parses a full_log line without naively assuming it is an HTTP access log."""
    text = clean_val(line)
    parsed = {
        "format": "text",
        "log_type": "text",
        "srcip": "",
        "timestamp": "",
        "timestamp_display": "",
        "timestamp_iso": None,
        "method": "",
        "uri": "",
        "path": "",
        "query": "",
        "protocol": "",
        "status": "",
        "bytes": "",
        "referer": "",
        "ua": "",
        "message": text,
        "details": text,
        "hostname": "",
        "program": "",
        "pid": "",
        "action": "",
    }
    if not text:
        return parsed

    # 1. Apache / Nginx combined access log
    match = ACCESS_LOG_RE.match(text)
    if match:
        uri = match.group("uri") or "/"
        qidx = uri.find("?")
        parsed.update({
            "format": "access_log",
            "log_type": "http",
            "srcip": valid_ip(match.group("srcip")) or match.group("srcip") or "",
            "timestamp": match.group("timestamp") or "",
            "timestamp_display": match.group("timestamp") or "",
            "timestamp_iso": parse_timestamp_iso(match.group("timestamp"), reference_ts),
            "method": match.group("method") or "",
            "uri": uri,
            "path": uri[:qidx] if qidx != -1 else uri,
            "query": uri[qidx + 1:] if qidx != -1 else "",
            "protocol": match.group("protocol") or "",
            "status": match.group("status") or "",
            "bytes": match.group("bytes") or "",
            "referer": clean_val(match.group("referer")),
            "ua": clean_val(match.group("ua")),
            "message": text,
            "details": uri,
        })
        return parsed

    # 2. Syslog / kernel / AppArmor / sshd
    match = SYSLOG_RE.match(text) or ISO_LOG_RE.match(text)
    if match:
        raw_ts = match.group("timestamp") or ""
        hostname = match.group("hostname") or ""
        rest = match.group("rest") or ""

        program = ""
        pid = ""
        msg = rest
        pmatch = PROGRAM_RE.match(rest)
        if pmatch:
            program = pmatch.group("program") or ""
            pid = pmatch.group("pid") or ""
            msg = pmatch.group("message") or ""

        action = short_action_desc(msg)
        apparmor = re.search(r'\bapparmor="([^"]+)"', msg, re.I)
        if apparmor:
            action = apparmor.group(1)
            path = f"{program or 'apparmor'}: AppArmor {action}"
        elif action:
            path = f"{program or 'syslog'}: {action}"
        else:
            path = program or "syslog"

        # Embedded HTTP in syslog
        http_match = HTTP_REQUEST_RE.search(rest)
        if http_match:
            uri = http_match.group("uri") or "/"
            qidx = uri.find("?")
            status_match = re.search(r'"\s+(\d{3})\s+(\S+)', rest[http_match.end():])
            parsed.update({
                "format": "syslog_http",
                "log_type": "http",
                "timestamp": raw_ts,
                "timestamp_display": raw_ts,
                "timestamp_iso": parse_timestamp_iso(raw_ts, reference_ts),
                "srcip": first_ip_in(rest),
                "method": http_match.group("method") or "",
                "uri": uri,
                "path": uri[:qidx] if qidx != -1 else uri,
                "query": uri[qidx + 1:] if qidx != -1 else "",
                "protocol": http_match.group("protocol") or "",
                "status": status_match.group(1) if status_match else "",
                "bytes": status_match.group(2) if status_match else "",
                "message": rest,
                "details": rest,
                "hostname": hostname,
                "program": program,
                "pid": pid,
                "action": action,
            })
            return parsed

        parsed.update({
            "format": "syslog",
            "log_type": "syslog",
            "srcip": first_ip_in(msg),
            "timestamp": raw_ts,
            "timestamp_display": raw_ts,
            "timestamp_iso": parse_timestamp_iso(raw_ts, reference_ts),
            "message": msg,
            "details": kv_details(msg) or msg,
            "hostname": hostname,
            "program": program,
            "pid": pid,
            "action": action,
            "path": path,
        })
        return parsed

    # 3. JSON formatted full_log
    if text.startswith("{") or text.startswith("["):
        try:
            obj = json.loads(text)
            if isinstance(obj, dict):
                url = clean_val(obj.get("url") or obj.get("uri") or obj.get("path"))
                method = clean_val(obj.get("method") or obj.get("http_method") or obj.get("protocol"))
                srcip = valid_ip(obj.get("srcip") or obj.get("src_ip") or obj.get("source_ip") or "")
                raw_ts = clean_val(obj.get("timestamp") or obj.get("@timestamp") or obj.get("time"))
                qidx = url.find("?")
                parsed.update({
                    "format": "json",
                    "log_type": "http" if (url or method) else "json",
                    "timestamp": raw_ts,
                    "timestamp_display": raw_ts,
                    "timestamp_iso": parse_timestamp_iso(raw_ts, reference_ts),
                    "srcip": srcip,
                    "method": method,
                    "uri": url,
                    "path": url[:qidx] if qidx != -1 else url,
                    "query": url[qidx + 1:] if qidx != -1 else "",
                    "status": clean_val(obj.get("status") or obj.get("status_code")),
                    "ua": clean_val(obj.get("user_agent") or obj.get("ua")),
                    "message": text,
                    "details": text,
                })
                return parsed
        except Exception:
            pass

    # 4. Embedded HTTP in general text
    http_match = HTTP_REQUEST_RE.search(text)
    if http_match:
        uri = http_match.group("uri") or "/"
        qidx = uri.find("?")
        status_match = re.search(r'"\s+(\d{3})\s+(\S+)', text[http_match.end():])
        parsed.update({
            "format": "http_embedded",
            "log_type": "http",
            "srcip": first_ip_in(text),
            "method": http_match.group("method") or "",
            "uri": uri,
            "path": uri[:qidx] if qidx != -1 else uri,
            "query": uri[qidx + 1:] if qidx != -1 else "",
            "protocol": http_match.group("protocol") or "",
            "status": status_match.group(1) if status_match else "",
            "bytes": status_match.group(2) if status_match else "",
            "message": text,
            "details": text,
        })
        return parsed

    # 5. Generic log line
    parsed["srcip"] = first_ip_in(text)
    parsed["details"] = text
    return parsed


def normalize_log_for_signature(line: Any) -> str:
    """Strips volatile fields (timestamps, audit serials, PIDs) to produce a stable deduplication string."""
    text = clean_val(line)
    if not text:
        return ""

    if text.startswith("{") or text.startswith("["):
        try:
            obj = json.loads(text)
            if isinstance(obj, dict):
                filtered = {
                    k: v for k, v in obj.items()
                    if k.lower() not in ("timestamp", "@timestamp", "id", "_id", "time")
                }
                return "json:" + json.dumps(filtered, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        except Exception:
            pass

    # Timestamps in access log: [20/Oct/2026:07:34:08 +0700]
    text = re.sub(r'\[\d{1,2}/[A-Za-z]{3}/\d{4}:\d{2}:\d{2}:\d{2}(?:\s+[+-]\d{4})?\]', '[TIMESTAMP]', text)
    # Header syslog: "Oct 21 12:10:20 host "
    text = re.sub(r'^(?:[A-Z][a-z]{2}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}(?:\.\d+)?)\s+\S+\s+', '', text)
    # Header ISO: "2026-10-21T12:10:20.123+07:00 host "
    text = re.sub(r'^\d{4}[-/]\d{2}[-/]\d{2}[T ]\d{2}:\d{2}:\d{2}(?:[.,]\d+)?(?:Z|[+-]\d{2}:?\d{2})?\s+(?:\S+\s+)?', '', text)
    # Kernel uptime: [2955743.701286]
    text = re.sub(r'\[\d+\.\d+\]\s*', '', text)
    # Remaining timestamps
    text = re.sub(r'\b\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:[.,]\d+)?(?:Z|[+-]\d{2}:?\d{2})?\b', '[TIMESTAMP]', text)
    text = re.sub(r'\b[A-Z][a-z]{2}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}(?:\.\d+)?\b', '[TIMESTAMP]', text)
    # Volatile audit metadata
    text = re.sub(r'audit\(\d+(?:\.\d+)?:\d+\)', 'audit(...)', text)
    text = re.sub(r'\bpid=\d+', 'pid=...', text)
    text = re.sub(r'\bmsg=audit\([^)]*\)', 'msg=audit(...)', text)
    return re.sub(r'\s+', ' ', text).strip()


def build_log_signature(alert: dict, parsed: dict | None = None) -> str:
    """Produces a stable 24-character SHA-256 signature for grouping identical recurring logs."""
    full_log = clean_val(alert.get("full_log"))
    if not full_log:
        return ""
    parsed = parsed or parse_log_line(full_log, alert.get("timestamp") or alert.get("@timestamp"))
    normalized = normalize_log_for_signature(full_log)
    if not normalized:
        return ""
    data = as_dict(alert.get("data"))
    rule = as_dict(alert.get("rule"))
    agent = as_dict(alert.get("agent"))
    labels = as_dict(agent.get("labels"))

    srcip = clean_val(data.get("srcip")) or clean_val(parsed.get("srcip"))
    hostname = clean_val(parsed.get("hostname")) or clean_val(agent.get("name")) or clean_val(agent.get("hostname"))
    tenant = clean_val(labels.get("tenant")) or clean_val(alert.get("tenant"))

    payload = "\x1f".join((
        clean_val(rule.get("id")),
        tenant,
        clean_val(agent.get("name")),
        srcip,
        hostname,
        normalized,
    ))
    return sha256(payload.encode("utf-8", "replace")).hexdigest()[:24]


def extract_alerts(document: Any) -> list[dict[str, Any]]:
    """Accepts Wazuh Elasticsearch exports, raw hit arrays, or single event dictionaries."""
    if isinstance(document, list):
        return [x for x in document if isinstance(x, dict)]
    if not isinstance(document, dict):
        return []
    hits = document.get("hits", {}).get("hits") if isinstance(document.get("hits"), dict) else None
    if isinstance(hits, list):
        out = []
        for row in hits:
            if isinstance(row, dict):
                src = row.get("_source", row)
                if "_id" in row and isinstance(src, dict) and "wazuh_id" not in src:
                    src["wazuh_id"] = str(row["_id"])
                out.append(src)
        return out
    if "_source" in document and isinstance(document["_source"], dict):
        src = document["_source"]
        if "_id" in document and "wazuh_id" not in src:
            src["wazuh_id"] = str(document["_id"])
        return [src]
    return [document] if any(k in document for k in ("rule", "agent", "timestamp", "id", "full_log")) else []


def parse_export(content: str) -> tuple[list[dict[str, Any]], list[str]]:
    """Robust parser that handles unescaped control characters in raw HTTP/log payloads."""
    errors: list[str] = []
    try:
        document = json.loads(content, strict=False)
    except json.JSONDecodeError as exc:
        cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", " ", content)
        try:
            document = json.loads(cleaned, strict=False)
            errors.append(f"Replaced invalid control characters (line {exc.lineno}, col {exc.colno}).")
        except json.JSONDecodeError as retry_exc:
            raise ValueError(f"Invalid JSON near line {retry_exc.lineno}, col {retry_exc.colno}: {retry_exc.msg}") from retry_exc

    return extract_alerts(document), errors
