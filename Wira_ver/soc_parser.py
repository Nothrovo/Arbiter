"""Parser & grouper untuk SOC Log Reader.

Fokus:
- full_log Wazuh tidak selalu berbentuk access log (Apache/Nginx). AppArmor,
  sshd, syslog, JSON, dan log generik harus tetap terbaca tanpa field palsu
  (mis. path "21" yang sebenarnya potongan tanggal).
- Dedup memakai signature log: _id Wazuh tetap disimpan, tetapi log yang
  isinya sama setelah timestamp/audit-serial/PID dinormalisasi digabung.
- first_seen / last_seen dipakai UI untuk menampilkan rentang waktu.

Tidak ada dependency Flask/DB di modul ini supaya mudah dites.
"""

from __future__ import annotations

import ipaddress
import json
import re
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from typing import Any

WIB = timezone(timedelta(hours=7))

# Apache / Nginx combined log (referer & user-agent opsional).
ACCESS_LOG_RE = re.compile(
    r'^(?P<srcip>\S+)\s+(?P<ident>\S+)\s+(?P<auth>\S+)\s+'
    r'\[(?P<timestamp>[^\]]+)\]\s+"(?P<method>[A-Z]+)\s+(?P<uri>[^"\s]+)'
    r'(?:\s+(?P<protocol>HTTP/[0-9.]+))?"\s+(?P<status>\d{3})\s+(?P<bytes>\S+)'
    r'(?:\s+"(?P<referer>[^"]*)"\s+"(?P<ua>[^"]*)")?'
)

# Request HTTP yang muncul di tengah log non-access (mis. setelah prefix syslog).
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


def _clean(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if text in ("-", "null", "None", "N/A", "n/a"):
        return ""
    return text


def _as_dict(value: Any) -> dict:
    return value if isinstance(value, dict) else {}


def _valid_ip(value: str) -> str:
    text = (value or "").strip().strip("[]()<>,;\"'")
    if not text:
        return ""
    # Buang port :443 / [v6]:443.
    if text.startswith("[") and "]" in text:
        text = text[1:text.index("]")]
    elif text.count(":") == 1 and re.search(r":\d{1,5}$", text):
        text = text.rsplit(":", 1)[0]
    try:
        return str(ipaddress.ip_address(text))
    except ValueError:
        return ""


def _first_ip(text: str) -> str:
    """Ambil IP pertama dari log generik (mis. 'from 1.2.3.4 port ...')."""
    for pattern in (
        r'\bsrcip\s*[=:]\s*["\']?([0-9a-fA-F:.]+)',
        r'\bsrc\s*[=:]\s*["\']?([0-9a-fA-F:.]+)',
        r'\bfrom\s+["\']?([0-9a-fA-F:.]+)',
        r'\bclient(?:\s*ip)?\s*[=:]?\s*["\']?([0-9a-fA-F:.]+)',
    ):
        match = re.search(pattern, text, re.I)
        if match:
            ip = _valid_ip(match.group(1))
            if ip:
                return ip
    for match in IPV4_RE.finditer(text):
        ip = _valid_ip(match.group(0))
        if ip:
            return ip
    for match in IPV6_RE.finditer(text):
        ip = _valid_ip(match.group(0))
        if ip:
            return ip
    return ""


def _parse_to_datetime(value: Any, reference: Any = None) -> datetime | None:
    """Parse timestamp Wazuh, access log, syslog, atau ISO menjadi datetime aware."""
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
        # +0700 -> +07:00, koma milidetik -> titik.
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

    ref_dt = _parse_to_datetime(reference) if reference is not None and reference is not value else None
    if dt.tzinfo is None:
        # Syslog tidak membawa tahun. Ambil tahun dari timestamp alert (referensi)
        # atau tahun berjalan, lalu anggap waktu lokal WIB.
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


def parse_timestamp_value(value: Any, reference: Any = None) -> str | None:
    """Kembalikan ISO-8601 bertimezone, atau None bila tidak bisa diparse."""
    dt = _parse_to_datetime(value, reference)
    return dt.isoformat() if dt else None


def _short_action(message: str) -> str:
    """Ambil frasa aksi yang umum dari log syslog agar kolom Path terbaca."""
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


def _kv_details(message: str) -> str:
    parts = []
    for match in KV_RE.finditer(message):
        key = match.group("key")
        value = match.group("qval")
        if value is None:
            value = match.group("val") or ""
        parts.append(f"{key}={value}")
    return ", ".join(parts)


def _syslog_parts(rest: str) -> dict[str, str]:
    program = ""
    pid = ""
    message = rest
    match = PROGRAM_RE.match(rest)
    if match:
        program = match.group("program") or ""
        pid = match.group("pid") or ""
        message = match.group("message") or ""
    return {"program": program, "pid": pid, "message": message}


def _parse_json_log(text: str, reference: Any) -> dict[str, Any] | None:
    try:
        obj = json.loads(text)
    except (ValueError, TypeError):
        return None
    if not isinstance(obj, (dict, list)):
        return None

    def pick(*keys: str) -> str:
        if not isinstance(obj, dict):
            return ""
        for key in keys:
            value = obj.get(key)
            if value not in (None, "", "-"):
                return str(value)
        return ""

    raw_ts = pick("timestamp", "@timestamp", "time", "event_time")
    srcip = _valid_ip(pick("srcip", "src_ip", "source_ip", "client_ip", "ip"))
    url = pick("url", "uri", "path", "request_uri")
    method = pick("method", "http_method", "protocol")
    status = pick("status", "status_code", "http_status")
    ua = pick("user_agent", "useragent", "ua", "http_user_agent")
    message = json.dumps(obj, ensure_ascii=False, sort_keys=True)
    qidx = url.find("?")
    return {
        "format": "json",
        "log_type": "http" if (url or method) else "json",
        "timestamp": raw_ts,
        "timestamp_display": raw_ts,
        "timestamp_iso": parse_timestamp_value(raw_ts, reference),
        "srcip": srcip,
        "method": method,
        "uri": url,
        "path": url[:qidx] if qidx != -1 else url,
        "query": url[qidx + 1:] if qidx != -1 else "",
        "protocol": "",
        "status": status,
        "bytes": "",
        "referer": "",
        "ua": ua,
        "message": message,
        "details": message,
        "hostname": "",
        "program": "",
        "pid": "",
        "action": "",
    }


def _base_parsed(line: str) -> dict[str, Any]:
    return {
        "format": "text",
        "log_type": "text",
        "srcip": "",
        "ident": "",
        "auth": "",
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
        "message": line,
        "details": line,
        "hostname": "",
        "program": "",
        "pid": "",
        "action": "",
    }


def parse_log_line(line: Any, reference_ts: Any = None) -> dict[str, Any]:
    """Parse satu full_log tanpa mengasumsikan formatnya access log."""
    text = _clean(line)
    parsed = _base_parsed(text)
    if not text:
        return parsed

    # 1) Access log Apache/Nginx.
    match = ACCESS_LOG_RE.match(text)
    if match:
        uri = match.group("uri") or "/"
        qidx = uri.find("?")
        parsed.update({
            "format": "access_log",
            "log_type": "http",
            "srcip": _valid_ip(match.group("srcip")) or match.group("srcip") or "",
            "ident": match.group("ident") or "",
            "auth": match.group("auth") or "",
            "timestamp": match.group("timestamp") or "",
            "timestamp_display": match.group("timestamp") or "",
            "timestamp_iso": parse_timestamp_value(match.group("timestamp"), reference_ts),
            "method": match.group("method") or "",
            "uri": uri,
            "path": uri[:qidx] if qidx != -1 else uri,
            "query": uri[qidx + 1:] if qidx != -1 else "",
            "protocol": match.group("protocol") or "",
            "status": match.group("status") or "",
            "bytes": match.group("bytes") or "",
            "referer": _clean(match.group("referer")),
            "ua": _clean(match.group("ua")),
            "message": text,
            "details": uri,
        })
        return parsed

    # 2) Syslog / kernel / AppArmor / sshd.
    match = SYSLOG_RE.match(text) or ISO_LOG_RE.match(text)
    if match:
        raw_ts = match.group("timestamp") or ""
        hostname = match.group("hostname") or ""
        rest = match.group("rest") or ""
        parts = _syslog_parts(rest)
        message = parts["message"]
        kv = _kv_details(message)
        action = _short_action(message)
        apparmor = re.search(r'\bapparmor="([^"]+)"', message, re.I)
        if apparmor:
            action = apparmor.group(1)
        path = parts["program"] or "syslog"
        if apparmor:
            path = f"{parts['program'] or 'apparmor'}: AppArmor {action}"
        elif action:
            path = f"{parts['program'] or 'syslog'}: {action}"

        # Request HTTP yang kebetulan berada di dalam log syslog.
        http_match = HTTP_REQUEST_RE.search(rest)
        if http_match:
            uri = http_match.group("uri") or "/"
            qidx = uri.find("?")
            status_match = re.search(
                r'"\s+(\d{3})\s+(\S+)', rest[http_match.end():]
            )
            parsed.update({
                "format": "syslog_http",
                "log_type": "http",
                "timestamp": raw_ts,
                "timestamp_display": raw_ts,
                "timestamp_iso": parse_timestamp_value(raw_ts, reference_ts),
                "srcip": _first_ip(rest),
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
                "program": parts["program"],
                "pid": parts["pid"],
                "action": action,
            })
            return parsed

        parsed.update({
            "format": "syslog",
            "log_type": "syslog",
            "srcip": _first_ip(message),
            "timestamp": raw_ts,
            "timestamp_display": raw_ts,
            "timestamp_iso": parse_timestamp_value(raw_ts, reference_ts),
            "message": message,
            "details": kv or message,
            "hostname": hostname,
            "program": parts["program"],
            "pid": parts["pid"],
            "action": action,
            "path": path,
        })
        return parsed

    # 3) full_log berupa JSON (Wazuh kadang meneruskan event JSON mentah).
    json_parsed = _parse_json_log(text, reference_ts)
    if json_parsed:
        return json_parsed

    # 4) HTTP request di dalam teks bebas.
    http_match = HTTP_REQUEST_RE.search(text)
    if http_match:
        uri = http_match.group("uri") or "/"
        qidx = uri.find("?")
        status_match = re.search(r'"\s+(\d{3})\s+(\S+)', text[http_match.end():])
        parsed.update({
            "format": "http_embedded",
            "log_type": "http",
            "srcip": _first_ip(text),
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

    # 5) Generic text: jangan memakai token acak sebagai path/method.
    parsed["srcip"] = _first_ip(text)
    parsed["details"] = text
    parsed["message"] = text
    return parsed


def normalize_log_for_signature(line: Any) -> str:
    """Normalisasi minimal agar log berulang dianggap sama (bukan sekadar mirip).

    Yang dibuang hanya metadata volatil: timestamp, header hostname, audit
    serial, dan PID. Isi log lainnya harus tetap sama -> "100% sama".
    """
    text = _clean(line)
    if not text:
        return ""

    # JSON: buang field waktu/id agar event JSON berulang bisa bergabung.
    if text[:1] in ("{", "["):
        try:
            obj = json.loads(text)
            if isinstance(obj, dict):
                obj = {
                    key: value for key, value in obj.items()
                    if key.lower() not in ("timestamp", "@timestamp", "id", "_id", "time")
                }
            return "json:" + json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        except (ValueError, TypeError):
            pass

    # Timestamp access log: [20/Oct/2026:07:34:08 +0700]
    text = re.sub(
        r'\[\d{1,2}/[A-Za-z]{3}/\d{4}:\d{2}:\d{2}:\d{2}(?:\s+[+-]\d{4})?\]',
        '[TIMESTAMP]',
        text,
    )
    # Header syslog: "Oct 21 12:10:20 host "
    text = re.sub(
        r'^(?:[A-Z][a-z]{2}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}(?:\.\d+)?)\s+\S+\s+',
        '',
        text,
    )
    # Header ISO: "2026-10-21T12:10:20.123+07:00 host "
    text = re.sub(
        r'^\d{4}[-/]\d{2}[-/]\d{2}[T ]\d{2}:\d{2}:\d{2}(?:[.,]\d+)?'
        r'(?:Z|[+-]\d{2}:?\d{2})?\s+(?:\S+\s+)?',
        '',
        text,
    )
    # Prefix uptime kernel: "kernel: [2955743.701286] ".
    text = re.sub(r'\[\d+\.\d+\]\s*', '', text)
    # Timestamp lain yang masih tersisa (mis. di dalam pesan audit).
    text = re.sub(
        r'\b\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:[.,]\d+)?'
        r'(?:Z|[+-]\d{2}:?\d{2})?\b',
        '[TIMESTAMP]',
        text,
    )
    text = re.sub(
        r'\b[A-Z][a-z]{2}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}(?:\.\d+)?\b',
        '[TIMESTAMP]',
        text,
    )
    # Metadata volatil.
    text = re.sub(r'audit\(\d+(?:\.\d+)?:\d+\)', 'audit(...)', text)
    text = re.sub(r'\bpid=\d+', 'pid=...', text)
    text = re.sub(r'\bmsg=audit\([^)]*\)', 'msg=audit(...)', text)
    return re.sub(r'\s+', ' ', text).strip()


def build_log_signature(alert: dict, parsed: dict | None = None) -> str:
    """Signature stabil: rule + agent + sumber + isi log ternormalisasi."""
    full_log = _clean(alert.get("full_log"))
    if not full_log:
        return ""
    parsed = parsed or parse_log_line(full_log, alert.get("timestamp") or alert.get("@timestamp"))
    normalized = normalize_log_for_signature(full_log)
    if not normalized:
        return ""
    data = _as_dict(alert.get("data"))
    rule = _as_dict(alert.get("rule"))
    agent = _as_dict(alert.get("agent"))
    labels = _as_dict(agent.get("labels"))
    srcip = _clean(data.get("srcip")) or _clean(parsed.get("srcip"))
    hostname = _clean(parsed.get("hostname")) or _clean(agent.get("name")) or _clean(agent.get("hostname"))
    tenant = _clean(labels.get("tenant"))
    payload = "\x1f".join((
        _clean(rule.get("id")),
        tenant,
        _clean(agent.get("name")),
        srcip,
        hostname,
        normalized,
    ))
    return sha256(payload.encode("utf-8", "replace")).hexdigest()[:24]


def normalize_single_wazuh_alert(item: Any) -> dict:
    """Normalisasi satu item (dict Wazuh / string log mentah) sebelum INSERT.

    _id untuk baris dengan full_log memakai signature log supaya kemunculan
    berulang otomatis menaikkan hit_count dan mengisi first/last_seen.
    _id asli Wazuh tetap disimpan sebagai wazuh_id di raw_json.
    """
    if isinstance(item, str):
        line = item.strip()
        parsed = parse_log_line(line)
        signature = build_log_signature({"full_log": line, "rule": {"id": "RAW-LOG"}}, parsed)
        _id = f"sig_{signature}" if signature else "raw_" + sha256(line.encode("utf-8", "replace")).hexdigest()[:20]
        data = {
            "srcip": parsed.get("srcip") or "",
            "url": parsed.get("uri") or "",
            "protocol": parsed.get("method") or "",
            "id": parsed.get("status") or "",
        }
        desc = parsed.get("path") or parsed.get("action") or parsed.get("message") or "Raw log"
        if parsed.get("log_type") == "http" and parsed.get("method"):
            desc = f"Access log: {parsed['method']} {parsed.get('path', '/')} ({parsed.get('status') or '-'})"
        return {
            "_id": _id,
            "id": _id,
            "timestamp": parsed.get("timestamp_iso") or "",
            "full_log": line,
            "data": data,
            "rule": {
                "id": "RAW-LOG",
                "level": 5 if str(parsed.get("status") or "").startswith("4") else 3,
                "description": str(desc)[:240],
            },
            "agent": {"name": "manual-import", "labels": {"tenant": "manual"}},
            "log_signature": signature,
            "wazuh_id": "",
        }

    alert = dict(item or {})
    full_log = alert.get("full_log") or ""
    if not isinstance(full_log, str):
        try:
            full_log = json.dumps(full_log, ensure_ascii=False)
        except (TypeError, ValueError):
            full_log = str(full_log)
    alert["full_log"] = full_log

    wazuh_id = _clean(alert.get("wazuh_id")) or _clean(alert.get("_id")) or _clean(alert.get("id"))
    if wazuh_id:
        alert["wazuh_id"] = wazuh_id

    raw_ts = alert.get("timestamp") or alert.get("@timestamp")
    parsed = parse_log_line(full_log, raw_ts)
    signature = build_log_signature(alert, parsed)

    if signature:
        alert["log_signature"] = signature
        alert["_id"] = f"sig_{signature}"
    elif not alert.get("_id"):
        if alert.get("id"):
            alert["_id"] = str(alert["id"])
        else:
            base_s = f"{raw_ts or ''}|{full_log}"
            generated = sha256(base_s.encode("utf-8", "replace")).hexdigest()[:20]
            alert["_id"] = f"gen_{generated}"
            alert["id"] = alert["_id"]

    if not alert.get("id"):
        alert["id"] = wazuh_id or alert["_id"]

    if raw_ts:
        alert["timestamp"] = parse_timestamp_value(raw_ts) or parsed.get("timestamp_iso") or None
    elif parsed.get("timestamp_iso"):
        alert["timestamp"] = parsed["timestamp_iso"]

    return alert


def enrich_alert(alert: dict) -> dict:
    """Tambahkan hasil parse & signature untuk kebutuhan tampilan/export."""
    enriched = dict(alert or {})
    raw_ts = enriched.get("timestamp") or enriched.get("@timestamp")
    parsed = parse_log_line(enriched.get("full_log") or "", raw_ts)
    enriched["_parsed"] = parsed
    enriched["log_type"] = parsed.get("log_type") or "text"
    if not enriched.get("log_signature"):
        enriched["log_signature"] = build_log_signature(enriched, parsed)
    if not enriched.get("timestamp") and parsed.get("timestamp_iso"):
        enriched["timestamp"] = parsed["timestamp_iso"]
    return enriched


def _hit_count(alert: dict) -> int:
    try:
        return max(1, int(alert.get("hit_count") or 1))
    except (TypeError, ValueError):
        return 1


def _time_candidates(alert: dict) -> list[datetime]:
    """Waktu kemunculan alert, bukan campuran waktu log dan waktu ingest.

    first_seen/last_seen adalah sumber utama (sudah mencakup rentang hit).
    Waktu di dalam full_log hanya fallback bila alert tidak punya timestamp,
    supaya satu alert tidak terlihat punya rentang padahal hit_count = 1.
    """
    first = _parse_to_datetime(alert.get("first_seen"))
    last = _parse_to_datetime(alert.get("last_seen"))
    if first or last:
        return [value for value in (first, last) if value is not None]

    ts = _parse_to_datetime(alert.get("timestamp") or alert.get("@timestamp"))
    if ts is not None:
        return [ts]

    parsed = alert.get("_parsed") or {}
    parsed_ts = _parse_to_datetime(parsed.get("timestamp_iso"))
    return [parsed_ts] if parsed_ts is not None else []


def group_alerts(alerts: list[dict]) -> list[dict]:
    """Gabungkan log identik (signature sama), jumlahkan hit, rentang waktu."""
    groups: dict[str, dict] = {}
    for raw in alerts or []:
        alert = enrich_alert(raw)
        signature = alert.get("log_signature") or ""
        key = f"sig:{signature}" if signature else f"id:{alert.get('_id') or alert.get('id') or id(alert)}"
        times = _time_candidates(alert)
        hit = _hit_count(alert)

        incoming_ids = list(alert.get("wazuh_ids") or [])
        single_id = alert.get("wazuh_id")
        if single_id and single_id not in incoming_ids:
            incoming_ids.append(single_id)

        row_id = alert.get("_id") or alert.get("id")
        if key not in groups:
            group = dict(alert)
            group["hit_count"] = hit
            group["wazuh_ids"] = incoming_ids
            group["_group_key"] = key
            group["_group_rows"] = 1
            group["_group_row_ids"] = [row_id] if row_id else []
            group["_times"] = times
            groups[key] = group
        else:
            group = groups[key]
            group["hit_count"] += hit
            group["_group_rows"] += 1
            group["_times"].extend(times)
            known_ids = group.setdefault("wazuh_ids", [])
            for wazuh_id in incoming_ids:
                if wazuh_id not in known_ids:
                    known_ids.append(wazuh_id)
            row_ids = group.setdefault("_group_row_ids", [])
            if row_id and row_id not in row_ids:
                row_ids.append(row_id)
            # Simpan contoh full_log terbaru (input pertama = terbaru karena query DESC).
            if not group.get("full_log") and alert.get("full_log"):
                group["full_log"] = alert["full_log"]

    result = []
    for group in groups.values():
        times = group.pop("_times", [])
        if times:
            first = min(times)
            last = max(times)
            group["first_seen"] = first.isoformat()
            group["last_seen"] = last.isoformat()
        result.append(group)

    def sort_key(alert: dict) -> float:
        dt = _parse_to_datetime(alert.get("last_seen") or alert.get("timestamp"))
        return dt.timestamp() if dt else 0.0

    result.sort(key=sort_key, reverse=True)
    return result


def format_time_range(alert: dict) -> str:
    """Rentang waktu untuk tabel/export, mis. '12.10.20 s/d 13.00.20'."""
    first = _parse_to_datetime(alert.get("first_seen"))
    last = _parse_to_datetime(alert.get("last_seen"))
    if first is None and last is None:
        parsed = alert.get("_parsed") or parse_log_line(
            alert.get("full_log") or "",
            alert.get("timestamp") or alert.get("@timestamp"),
        )
        return _clean(parsed.get("timestamp_display")) or _clean(alert.get("timestamp")) or "-"
    if first is not None and last is not None and first != last:
        local_first = first.astimezone(WIB)
        local_last = last.astimezone(WIB)
        if local_first.date() == local_last.date():
            return f"{local_first:%H.%M.%S} s/d {local_last:%H.%M.%S}"
        return f"{local_first:%d/%m %H.%M.%S} s/d {local_last:%d/%m %H.%M.%S}"
    only = (first or last).astimezone(WIB)
    return f"{only:%d/%m/%Y %H.%M.%S}"


def parse_alert_fields(alert: dict) -> dict:
    """Field siap tampil/export; tidak pernah mengarang GET/200/path '21'."""
    parsed = alert.get("_parsed") or parse_log_line(
        alert.get("full_log") or "",
        alert.get("timestamp") or alert.get("@timestamp"),
    )
    data = _as_dict(alert.get("data"))
    rule = _as_dict(alert.get("rule"))

    is_http = parsed.get("log_type") == "http"
    srcip = _clean(data.get("srcip")) or _clean(parsed.get("srcip")) or "-"
    method = _clean(parsed.get("method")) if is_http else ""
    path = _clean(parsed.get("path"))
    if not path:
        path = "/" if is_http else "-"
    status = ""
    if is_http:
        for candidate in (_clean(data.get("id")), _clean(parsed.get("status"))):
            if HTTP_STATUS_RE.match(candidate):
                status = candidate
                break
    details = _clean(parsed.get("details")) or _clean(parsed.get("message"))
    if is_http:
        query = _clean(parsed.get("query"))
        if not query and "?" in _clean(data.get("url")):
            query = _clean(data.get("url")).split("?", 1)[1]
    else:
        query = details

    first = alert.get("first_seen")
    last = alert.get("last_seen")
    ts = _clean(parsed.get("timestamp_display")) or _clean(alert.get("timestamp")) or "-"

    return {
        "srcip": srcip,
        "timestamp": ts,
        "timestamp_iso": parsed.get("timestamp_iso") or alert.get("timestamp"),
        "first_seen": first,
        "last_seen": last,
        "method": method or "-",
        "path": path,
        "query": query or "",
        "protocol": _clean(parsed.get("protocol")) or "-",
        "status": status or "-",
        "bytes": _clean(parsed.get("bytes")) or "-",
        "referer": _clean(parsed.get("referer")) or "-",
        "ua": _clean(parsed.get("ua")) or "-",
        "full_log": alert.get("full_log") or "",
        "log_type": parsed.get("log_type") or "text",
        "program": _clean(parsed.get("program")),
        "action": _clean(parsed.get("action")),
        "message": _clean(parsed.get("message")),
        "details": details,
        "rule_id": _clean(rule.get("id")) or "-",
        "rule_desc": _clean(rule.get("description")) or "-",
    }
