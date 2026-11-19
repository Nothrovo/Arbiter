"""Threat intelligence enrichment and database caching for Arbiter & IP Intel."""

from __future__ import annotations

import ipaddress
import json
import logging
import os
import re
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

try:
    import app.config as _cfg
    ABUSEIPDB_API_KEY = getattr(_cfg, "ABUSEIPDB_API_KEY", "")
    VIRUSTOTAL_API_KEY = getattr(_cfg, "VIRUSTOTAL_API_KEY", "")
    INTEL_SIDECAR_URL = getattr(_cfg, "INTEL_SIDECAR_URL", "")
    REMOTE_DATABASE_URL = getattr(_cfg, "REMOTE_DATABASE_URL", "")
except (ImportError, AttributeError):
    ABUSEIPDB_API_KEY = os.getenv("ABUSEIPDB_API_KEY", "")
    VIRUSTOTAL_API_KEY = os.getenv("VIRUSTOTAL_API_KEY", "")
    INTEL_SIDECAR_URL = os.getenv("INTEL_SIDECAR_URL", "")
    REMOTE_DATABASE_URL = os.getenv("REMOTE_DATABASE_URL", "")

logger = logging.getLogger("arbiter.intel")

GEO_BATCH_URL = "http://ip-api.com/batch?fields=status,message,country,countryCode,isp,as,query"
VT_MAX_FALLBACK = 4
SIDECAR_TIMEOUT = 2.0


class AbuseIPDBError(RuntimeError):
    """Error raised when AbuseIPDB API returns an error status or fails."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


def normalize_ip_address(raw: str) -> str:
    """Strip quotes, brackets, and trailing :port from IPv4/IPv6 inputs."""
    text = str(raw or "").strip().strip("\"' \t\r\n,;")
    if not text:
        return ""
    if text.startswith("["):
        m = re.match(r"^\[([0-9a-fA-F:.]+)\](?::\d{1,5})?$", text)
        if m:
            return m.group(1)
    elif re.match(r"^\d{1,3}(?:\.\d{1,3}){3}:\d{1,5}$", text):
        return re.sub(r":\d{1,5}$", "", text)
    return text


def is_valid_ip(ip: str) -> bool:
    """Validates IPv4 and IPv6 addresses."""
    if not isinstance(ip, str) or not ip.strip():
        return False
    clean = ip.strip()
    try:
        ipaddress.ip_address(clean)
        return True
    except ValueError:
        return False


def is_private_ip(ip: str) -> bool:
    """Checks if IP belongs to private/RFC1918, loopback, or link-local range."""
    try:
        obj = ipaddress.ip_address(ip.strip())
        return (
            obj.is_private
            or obj.is_loopback
            or obj.is_link_local
            or obj.is_multicast
            or obj.is_reserved
        )
    except ValueError:
        return False


def query_abuseipdb(ip: str, api_key: str | None = None) -> dict[str, Any]:
    """Queries AbuseIPDB API v2 check endpoint."""
    key = api_key or ABUSEIPDB_API_KEY
    if not key:
        raise ValueError("AbuseIPDB API key not configured")

    url = f"https://api.abuseipdb.com/api/v2/check?ipAddress={quote(ip)}&maxAgeInDays=90&verbose"
    req = Request(
        url,
        headers={
            "Key": key,
            "Accept": "application/json",
            "User-Agent": "Arbiter-SOC/2.0",
        },
    )
    try:
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("data") or {}
    except HTTPError as exc:
        err_msg = f"HTTP {exc.code}"
        try:
            body = json.loads(exc.read().decode("utf-8"))
            if body.get("errors"):
                err_msg = body["errors"][0].get("detail", err_msg)
        except Exception:
            pass
        raise AbuseIPDBError(f"AbuseIPDB error: {err_msg}", status_code=exc.code) from exc
    except (URLError, TimeoutError) as exc:
        raise AbuseIPDBError(f"AbuseIPDB network error: {exc}", status_code=None) from exc


def _resolve_remote_db_url() -> str:
    """Resolve the active remote IP Intel database URL (including runtime overrides from #/database)."""
    try:
        import app.database as _db_mod
        prof = getattr(_db_mod, "_db_profiles", {}).get("remote", {})
        url = str(prof.get("url") or "").strip()
        if url:
            return url
    except Exception:
        pass
    return str(REMOTE_DATABASE_URL or "").strip()


def _remote_profile_read_only() -> bool:
    """Whether the active Remote profile is read-only (fail closed on unknown state)."""
    try:
        import app.database as _db_mod
        prof = getattr(_db_mod, "_db_profiles", {}).get("remote", {})
        return str(prof.get("mode") or "read_only") == "read_only"
    except Exception:
        return True


def _safe_remote_cache_error(exc: Exception) -> str:
    """Translate database failures without leaking a DSN, host credentials, or raw SQL."""
    text = str(exc).lower()
    if "password authentication failed" in text or "authentication failed" in text:
        return "Autentikasi database IP Intel (Remote) gagal. Periksa URI profil PC Intel di menu Database."
    if "could not translate host name" in text or "name or service not known" in text:
        return "Host database IP Intel (Remote) tidak dapat ditemukan. Gunakan alamat yang bisa diakses dari container Arbiter (mis. 127.0.0.1:5433 untuk jembatan socat)."
    if any(hint in text for hint in ("connection refused", "could not connect", "timeout", "timed out", "connection failed")):
        return "Database IP Intel (Remote) tidak dapat dihubungi. Pastikan sidecar/jembatan database berjalan."
    if "permission denied" in text:
        return "Role database IP Intel tidak memiliki izin baca ke cache reputasi."
    if "does not exist" in text or "undefinedtable" in text:
        return "Tabel cache IP Intel tidak ditemukan pada database Remote."
    return "Cache IP Intel tidak dapat dibaca."


def _json_object(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except ValueError:
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


def lookup_remote_ip_cache_detail(ip: str, remote_url: str | None = None) -> dict[str, Any]:
    """Read one reputation record from Neuropetra/IP Intel without writing anything.

    Supports both schemas used by IP Intel:
    - ``ip_intel_reputation`` (provider-owned AbuseIPDB reputation, current schema)
    - ``ip_intel_cache`` (legacy/telemetry cache)
    """
    target_url = str(remote_url or _resolve_remote_db_url()).strip()
    result: dict[str, Any] = {
        "configured": bool(target_url),
        "found": False,
        "record": None,
        "source_table": None,
        "error": None,
    }
    if not target_url:
        result["error"] = "URI database PC Intel (Remote) belum diatur. Buka menu Database dan isi profil PC Intel."
        return result

    try:
        import psycopg  # type: ignore
        from psycopg.rows import dict_row  # type: ignore
    except ImportError:
        result["error"] = "Driver PostgreSQL tidak tersedia di server Arbiter."
        return result

    try:
        with psycopg.connect(target_url, connect_timeout=3, row_factory=dict_row) as rconn:
            tables = rconn.execute(
                """SELECT to_regclass('public.ip_intel_reputation') AS reputation_table,
                          to_regclass('public.ip_intel_cache') AS cache_table"""
            ).fetchone() or {}
            has_reputation = bool(tables.get("reputation_table"))
            has_cache = bool(tables.get("cache_table"))
            if not has_reputation and not has_cache:
                result["error"] = "Tabel ip_intel_reputation / ip_intel_cache tidak ditemukan pada database Remote."
                return result

            if has_reputation and has_cache:
                row = rconn.execute(
                    """SELECT r.ip,
                              r.abuse_score,
                              r.country_code,
                              r.isp,
                              r.reputation_json,
                              r.reputation_checked_at,
                              c.vt_malicious
                       FROM public.ip_intel_reputation r
                       LEFT JOIN public.ip_intel_cache c ON c.ip = r.ip
                       WHERE r.ip = %s
                       LIMIT 1""",
                    (ip,),
                ).fetchone()
                source_table = "ip_intel_reputation"
            elif has_reputation:
                row = rconn.execute(
                    """SELECT ip, abuse_score, country_code, isp, reputation_json,
                              reputation_checked_at, NULL::integer AS vt_malicious
                       FROM public.ip_intel_reputation
                       WHERE ip = %s
                       LIMIT 1""",
                    (ip,),
                ).fetchone()
                source_table = "ip_intel_reputation"
            else:
                row = rconn.execute(
                    """SELECT ip, abuse_score, country_code, isp,
                              NULL::jsonb AS reputation_json,
                              NULL::timestamptz AS reputation_checked_at,
                              vt_malicious
                       FROM public.ip_intel_cache
                       WHERE ip = %s
                       LIMIT 1""",
                    (ip,),
                ).fetchone()
                source_table = "ip_intel_cache"

            if not row:
                result["error"] = f"IP {ip} belum ada di cache IP Intel (Neuropetra)."
                return result

            score = row.get("abuse_score")
            result["source_table"] = source_table
            if score is None:
                result["error"] = "IP ditemukan di database IP Intel, tetapi belum memiliki skor AbuseIPDB. Jalankan enrich di Neuropetra terlebih dahulu."
                return result

            reputation = _json_object(row.get("reputation_json"))
            result["found"] = True
            result["record"] = {
                "ip": ip,
                "status": "enriched",
                "abuse_score": int(score),
                "vt_malicious": int(row.get("vt_malicious") or 0),
                "country_code": row.get("country_code"),
                "isp": row.get("isp") or "Unknown ISP",
                "domain": reputation.get("domain"),
                "usage_type": reputation.get("usageType"),
                "total_reports": int(reputation.get("totalReports") or 0),
                "last_reported_at": reputation.get("lastReportedAt"),
                "is_tor": bool(reputation.get("isTor")),
                "is_whitelisted": bool(reputation.get("isWhitelisted")),
                "reputation_checked_at": str(row.get("reputation_checked_at") or ""),
                "reputation_source": "neuropetra_cache",
                "cache_source": source_table,
                "is_private": False,
            }
            return result
    except Exception as exc:
        logger.debug("Remote IP Intel DB lookup skipped: %s", exc)
        result["error"] = _safe_remote_cache_error(exc)
        return result


def lookup_remote_ip_cache(ip: str, remote_url: str | None = None) -> dict[str, Any] | None:
    """Look up an existing IP record in the remote IP Intel PostgreSQL database."""
    detail = lookup_remote_ip_cache_detail(ip, remote_url)
    return detail.get("record") if detail.get("found") else None


def enrich_ip(ip: str, api_key: str | None = None, remote_url: str | None = None) -> dict[str, Any]:
    """Enriches a single IP address with threat intelligence."""
    clean_ip = ip.strip()
    if not is_valid_ip(clean_ip):
        return {
            "ip": clean_ip,
            "status": "invalid",
            "error": "Bukan format IPv4/IPv6 yang valid.",
            "abuse_score": None,
        }

    # Private IP check: keep telemetry private and airgapped
    if is_private_ip(clean_ip):
        return {
            "ip": clean_ip,
            "status": "private",
            "abuse_score": 0,
            "vt_malicious": 0,
            "country_code": "LAN",
            "isp": "Private Local Network (RFC1918)",
            "domain": None,
            "usage_type": "Private / Intranet",
            "total_reports": 0,
            "reputation_source": "local_private",
            "is_private": True,
        }

    effective_key = (api_key or ABUSEIPDB_API_KEY or "").strip()
    if effective_key:
        try:
            data = query_abuseipdb(clean_ip, effective_key)
            score = int(data.get("abuseConfidenceScore") or 0)
            return {
                "ip": clean_ip,
                "status": "enriched",
                "abuse_score": score,
                "vt_malicious": 0,
                "country_code": data.get("countryCode"),
                "isp": data.get("isp") or "Unknown ISP",
                "domain": data.get("domain"),
                "usage_type": data.get("usageType"),
                "total_reports": int(data.get("totalReports") or 0),
                "is_tor": bool(data.get("isTor")),
                "is_whitelisted": bool(data.get("isWhitelisted")),
                "reputation_source": "abuseipdb",
                "is_private": False,
            }
        except Exception as exc:
            remote = lookup_remote_ip_cache_detail(clean_ip, remote_url)
            if remote.get("found"):
                return remote["record"]
            return {
                "ip": clean_ip,
                "status": "error",
                "error": f"Live AbuseIPDB gagal: {exc}. {remote.get('error') or 'Cache IP Intel tidak tersedia.'}",
                "abuse_score": None,
            }

    # If no AbuseIPDB API key is configured, pull directly from the remote IP Intel database cache
    remote = lookup_remote_ip_cache_detail(clean_ip, remote_url)
    if remote.get("found"):
        return remote["record"]

    return {
        "ip": clean_ip,
        "status": "error",
        "error": f"AbuseIPDB API key belum diatur di Pengaturan dan cache IP Intel tidak tersedia. {remote.get('error') or ''}".strip(),
        "abuse_score": None,
    }


def upsert_ip_cache(conn: Any, enriched: dict[str, Any]) -> None:
    """Upserts enriched IP telemetry into public.ip_intel_cache."""
    ip = enriched.get("ip")
    if not ip or enriched.get("status") in ("invalid", "error"):
        return

    sql = """
    INSERT INTO public.ip_intel_cache (
        ip, abuse_score, vt_malicious, country_code, isp
    ) VALUES (%s, %s, %s, %s, %s)
    ON CONFLICT (ip) DO UPDATE SET
        abuse_score = COALESCE(EXCLUDED.abuse_score, ip_intel_cache.abuse_score),
        vt_malicious = COALESCE(EXCLUDED.vt_malicious, ip_intel_cache.vt_malicious),
        country_code = COALESCE(EXCLUDED.country_code, ip_intel_cache.country_code),
        isp = COALESCE(EXCLUDED.isp, ip_intel_cache.isp)
    """
    conn.execute(
        sql,
        (
            ip,
            enriched.get("abuse_score"),
            enriched.get("vt_malicious", 0),
            enriched.get("country_code"),
            enriched.get("isp"),
        ),
    )


def sync_remote_cache(enriched_list: list[dict[str, Any]], remote_url: str | None = None) -> None:
    """Best-effort mirror to the Remote IP Intel database, honoring its read-only mode."""
    target_url = str(remote_url or _resolve_remote_db_url()).strip()
    if not target_url or not enriched_list:
        return
    if _remote_profile_read_only():
        logger.debug("Remote cache sync skipped: profile is read-only")
        return
    try:
        import psycopg  # type: ignore
        with psycopg.connect(target_url, connect_timeout=3) as rconn:
            with rconn.cursor() as cur:
                for item in enriched_list:
                    # Records already read from the remote cache need no mirror write,
                    # and the Arbiter integration must keep the IP Intel database read-only.
                    if item.get("cache_source"):
                        continue
                    if item.get("status") not in ("invalid", "error"):
                        upsert_ip_cache(cur, item)
            rconn.commit()
    except Exception as exc:
        logger.debug("Remote cache sync skipped or unreachable: %s", exc)


_ATTACK_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("sql_injection", re.compile(r"sql\s*injection|\bsqli\b|union\s+(?:all\s+)?select", re.I)),
    ("xss", re.compile(r"cross[- ]site scripting|\bxss\b|<script", re.I)),
    ("path_traversal", re.compile(r"path traversal|\.\./|\.\.\\", re.I)),
    ("command_injection", re.compile(r"command injection|cmd=|exec\s*\(", re.I)),
    ("web_scan", re.compile(r"web[_ -]?scan|vulnerability scan|nikto|gobuster", re.I)),
    ("shellshock", re.compile(r"shellshock|\(\)\s*\{\s*:;\s*\}", re.I)),
    ("port_scan", re.compile(r"port\s*scan|nmap", re.I)),
    ("auth_bruteforce", re.compile(r"brute force|failed password|invalid user", re.I)),
    ("http_flood", re.compile(r"http flood|too many requests|rate.?limit", re.I)),
    ("buffer_overflow", re.compile(r"buffer overflow", re.I)),
)


def _json_value(value: Any, fallback: Any = None) -> Any:
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except ValueError:
            return fallback
    return fallback


def is_cdn_edge(geo: dict[str, Any] | None) -> bool:
    """Detect Cloudflare CDN edge IPs whose true client IP sits behind proxy headers."""
    if not isinstance(geo, dict):
        return False
    identity = f"{geo.get('isp') or ''} {geo.get('as') or ''}"
    return bool(re.search(r"cloudflare", identity, re.I))


def parse_sidecar_candidates(raw_url: str | None = None) -> list[str]:
    """Parse comma/newline-separated Sidecar base URLs, falling back to INTEL_SIDECAR_URL."""
    effective = str(raw_url if (raw_url is not None and str(raw_url).strip()) else INTEL_SIDECAR_URL or "").strip()
    if not effective:
        return []
    candidates: list[str] = []
    for part in re.split(r"[\n,]+", effective):
        item = part.strip()
        if not item:
            continue
        cleaned = re.sub(r"/ip-intel/?$", "", item.rstrip("/"), flags=re.IGNORECASE).rstrip("/")
        if cleaned and cleaned not in candidates:
            candidates.append(cleaned)
    return candidates[:10]


def has_usable_sidecar_cache(cached: dict[str, Any] | None) -> bool:
    """Return True if a Sidecar cached record holds usable AbuseIPDB, VT, or CDN edge intel."""
    if not isinstance(cached, dict) or not cached:
        return False
    geo = _json_object(cached.get("geo_json"))
    rep = _json_object(cached.get("reputation_json"))
    placeholder = re.search(
        r"pending batch query|external network",
        f"{cached.get('isp') or ''} {geo.get('isp') or ''}",
        re.I,
    )
    if placeholder and not rep:
        return False
    src = str(cached.get("reputation_source") or "").strip().lower()
    if src == "abuseipdb" and (bool(rep) or cached.get("abuse_score") is not None):
        return True
    if src == "virustotal" and (bool(rep) or cached.get("vt_malicious") is not None):
        return True
    if src == "cdn_edge":
        return True
    return False


def _vt_malicious_score(vt_data: dict[str, Any] | None) -> tuple[int, int] | tuple[None, None]:
    if not isinstance(vt_data, dict):
        return None, None
    attrs = vt_data.get("attributes") if isinstance(vt_data.get("attributes"), dict) else vt_data
    stats = attrs.get("last_analysis_stats") if isinstance(attrs.get("last_analysis_stats"), dict) else {}
    mal_raw = stats.get("malicious")
    if mal_raw is None:
        return None, None
    mal = int(mal_raw)
    score = 100 if mal >= 5 else (50 if mal >= 2 else (20 if mal >= 1 else 0))
    return score, mal


def normalize_sidecar_record(ip: str, cached: dict[str, Any], sidecar_url: str) -> dict[str, Any]:
    """Normalize a Sidecar `/ip-intel` cache record into Arbiter's enriched IP payload."""
    src = str(cached.get("reputation_source") or "abuseipdb").strip().lower()
    geo_raw = _json_object(cached.get("geo_json"))
    rep = _json_object(cached.get("reputation_json"))

    raw_country = str(cached.get("country_code") or geo_raw.get("countryCode") or geo_raw.get("country") or "").strip()
    country_code = cached.get("country_code") or geo_raw.get("countryCode") or (raw_country[:2].upper() if len(raw_country) == 2 else None)
    raw_isp = str(cached.get("isp") or geo_raw.get("isp") or "").strip()
    is_placeholder = bool(re.search(r"pending batch query|external network", raw_isp, re.I))
    isp = "Unknown ISP" if (not raw_isp or is_placeholder) else raw_isp

    geo = {
        **geo_raw,
        "country": geo_raw.get("country") or country_code or "Unknown",
        "countryCode": country_code,
        "isp": isp,
        "as": geo_raw.get("as") or isp,
    }

    score: int | None = None
    if cached.get("abuse_score") is not None and str(cached.get("abuse_score")).strip() != "":
        score = int(float(cached["abuse_score"]))
    elif rep.get("abuseConfidenceScore") is not None:
        score = int(float(rep["abuseConfidenceScore"]))

    vt_mal: int | None = None
    if cached.get("vt_malicious") is not None and str(cached.get("vt_malicious")).strip() != "":
        vt_mal = int(float(cached["vt_malicious"]))
    elif src == "virustotal":
        vt_score, parsed_mal = _vt_malicious_score(rep)
        vt_mal = parsed_mal
        if score is None:
            score = vt_score

    return {
        "ip": ip,
        "status": "cdn_edge" if src == "cdn_edge" else "enriched",
        "abuse_score": score,
        "vt_malicious": vt_mal or 0,
        "country_code": country_code,
        "isp": isp,
        "domain": rep.get("domain"),
        "usage_type": rep.get("usageType"),
        "total_reports": int(rep.get("totalReports") or 0),
        "is_tor": bool(rep.get("isTor")),
        "is_whitelisted": bool(rep.get("isWhitelisted")),
        "reputation_source": src,
        "cache_source": "sidecar",
        "sidecar_url": sidecar_url,
        "from_cache": True,
        "is_private": False,
        "geo": geo,
        "reputation": rep or None,
        "intel": {
            "first_seen": cached.get("first_seen"),
            "last_seen": cached.get("last_seen"),
            "total_alert_count": cached.get("total_alert_count"),
            "attack_types": cached.get("attack_types") or [],
            "mitre_tactics": cached.get("mitre_tactics") or [],
            "target_hosts": cached.get("target_hosts") or [],
            "endpoints_targeted": cached.get("endpoints_targeted") or [],
        },
    }


def probe_sidecar(
    candidates: list[str],
    sample_ips: list[str] | None = None,
    timeout: float = SIDECAR_TIMEOUT,
) -> dict[str, Any]:
    """Probe Sidecar candidate URLs in order with GET /ip-intel?ips=... and return the first healthy one."""
    sample = [normalize_ip_address(x) for x in (sample_ips or ["8.8.8.8"]) if normalize_ip_address(x)][:5]
    if not sample:
        sample = ["8.8.8.8"]
    query = quote(",".join(sample), safe=",")
    last_error: str | None = None

    for base in candidates:
        clean_base = base.rstrip("/")
        url = f"{clean_base}/ip-intel?ips={query}"
        req = Request(
            url,
            headers={
                "Accept": "application/json",
                "User-Agent": "Arbiter-SOC/2.0",
            },
        )
        try:
            with urlopen(req, timeout=timeout) as resp:
                raw_body = resp.read().decode("utf-8", errors="replace")
            body = json.loads(raw_body) if raw_body.strip() else {}
            if isinstance(body, dict) and ("cached" in body or body.get("status") == "ok" or "connected" in body):
                cached = body.get("cached") if isinstance(body.get("cached"), dict) else {}
                return {"connected": True, "url": clean_base, "cached": cached, "error": None}
            last_error = f"Respons Sidecar tidak sesuai format JSON /ip-intel dari {clean_base}."
        except HTTPError as exc:
            last_error = f"Sidecar {clean_base} mengembalikan HTTP {exc.code}."
        except (URLError, TimeoutError, ValueError, OSError) as exc:
            last_error = f"Sidecar {clean_base} tidak dapat dihubungi: {exc}"

    return {"connected": False, "url": None, "cached": {}, "error": last_error or "Sidecar IP Intel tidak dapat dihubungi."}


def fetch_sidecar_cache(
    sidecar_url: str,
    ips: list[str],
    timeout: float = SIDECAR_TIMEOUT,
) -> dict[str, dict[str, Any]]:
    """Fetch cached intel entries from an active Sidecar URL in chunks of 50 IPs."""
    clean_base = sidecar_url.rstrip("/")
    merged: dict[str, dict[str, Any]] = {}
    for idx in range(0, len(ips), 50):
        chunk = ips[idx: idx + 50]
        if not chunk:
            continue
        query = quote(",".join(chunk), safe=",")
        req = Request(
            f"{clean_base}/ip-intel?ips={query}",
            headers={"Accept": "application/json", "User-Agent": "Arbiter-SOC/2.0"},
        )
        try:
            with urlopen(req, timeout=timeout) as resp:
                body = json.loads(resp.read().decode("utf-8", errors="replace") or "{}")
            if isinstance(body, dict) and isinstance(body.get("cached"), dict):
                merged.update(body["cached"])
        except Exception as exc:
            logger.debug("Sidecar chunk fetch failed (%s): %s", clean_base, exc)
    return merged


def query_geo_batch(ips: list[str], timeout: float = 6.0) -> dict[str, dict[str, Any]]:
    """Best-effort batch geo lookup via ip-api.com (up to 100 IPs per request)."""
    geo_map: dict[str, dict[str, Any]] = {}
    for idx in range(0, len(ips), 100):
        chunk = ips[idx: idx + 100]
        if not chunk:
            continue
        payload = json.dumps([{"query": ip} for ip in chunk]).encode("utf-8")
        req = Request(
            GEO_BATCH_URL,
            data=payload,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "Arbiter-SOC/2.0",
            },
        )
        try:
            with urlopen(req, timeout=timeout) as resp:
                rows = json.loads(resp.read().decode("utf-8", errors="replace") or "[]")
            if isinstance(rows, list):
                for ip, row in zip(chunk, rows):
                    if isinstance(row, dict) and row.get("status") == "success":
                        geo_map[ip] = {
                            "country": str(row.get("country") or row.get("countryCode") or "Unknown"),
                            "countryCode": row.get("countryCode"),
                            "isp": str(row.get("isp") or row.get("as") or "Unknown ISP"),
                            "as": str(row.get("as") or row.get("isp") or "N/A"),
                        }
        except Exception as exc:
            logger.debug("Geo batch lookup skipped: %s", exc)
    return geo_map


def query_virustotal_ip(ip: str, api_key: str | None = None, timeout: float = 8.0) -> dict[str, Any]:
    """Query VirusTotal v3 `/ip_addresses/{ip}` endpoint."""
    key = (api_key or VIRUSTOTAL_API_KEY or "").strip()
    if not key:
        raise ValueError("VirusTotal API key not configured")
    req = Request(
        f"https://www.virustotal.com/api/v3/ip_addresses/{quote(ip)}",
        headers={
            "x-apikey": key,
            "Accept": "application/json",
            "User-Agent": "Arbiter-SOC/2.0",
        },
    )
    try:
        with urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode("utf-8", errors="replace") or "{}")
            return body.get("data") or {}
    except HTTPError as exc:
        raise RuntimeError(f"VirusTotal error: HTTP {exc.code}") from exc
    except (URLError, TimeoutError, ValueError, OSError) as exc:
        raise RuntimeError(f"VirusTotal network error: {exc}") from exc


def extract_alert_intel_context(alerts: list[dict[str, Any]]) -> dict[str, Any]:
    """Extract target hosts, endpoints, HTTP methods, MITRE tactics, and attack types from alerts."""
    target_hosts: list[str] = []
    endpoints: list[str] = []
    methods: list[str] = []
    mitre_list: list[str] = []
    attack_types: list[str] = []
    seen_hosts: set[str] = set()
    seen_eps: set[str] = set()
    seen_methods: set[str] = set()
    seen_mitre: set[str] = set()
    seen_attacks: set[str] = set()

    for alert in alerts or []:
        if not isinstance(alert, dict):
            continue
        agent = str(alert.get("agent_name") or "").strip()
        if agent and agent not in seen_hosts:
            seen_hosts.add(agent)
            target_hosts.append(agent)

        data = _json_object(alert.get("data"))
        parsed = _json_object(alert.get("parsed_details"))
        raw_obj = _json_object(alert.get("raw"))

        uri = str(
            data.get("url")
            or data.get("request")
            or data.get("uri")
            or parsed.get("uri")
            or parsed.get("path")
            or ""
        ).strip()
        if uri and uri != "/" and uri not in seen_eps:
            seen_eps.add(uri[:500])
            endpoints.append(uri[:500])

        method = str(data.get("protocol") or parsed.get("method") or "").strip().upper()
        if method and method not in seen_methods:
            seen_methods.add(method)
            methods.append(method)

        mitre_vals = _json_value(alert.get("mitre_ids"), [])
        if isinstance(mitre_vals, list):
            for mid in mitre_vals:
                mstr = str(mid or "").strip()
                if mstr and mstr not in seen_mitre:
                    seen_mitre.add(mstr)
                    mitre_list.append(mstr)

        evidence = " ".join(
            part for part in (
                uri,
                str(alert.get("description") or ""),
                str(alert.get("full_log") or raw_obj.get("full_log") or ""),
                str(raw_obj.get("previous_output") or ""),
                str(data.get("payload") or ""),
            ) if part
        )
        for atk_name, pat in _ATTACK_PATTERNS:
            if atk_name not in seen_attacks and pat.search(evidence):
                seen_attacks.add(atk_name)
                attack_types.append(atk_name)

    return {
        "target_hosts": target_hosts or ["Unknown Host"],
        "endpoints_targeted": endpoints[:10],
        "http_methods_used": methods,
        "mitre_tactics": mitre_list,
        "attack_types": attack_types,
        "alert_type": None,
        "attack_subtype": attack_types[0] if attack_types else None,
        "target_host": target_hosts[0] if target_hosts else "Unknown Host",
        "endpoint": endpoints[0] if endpoints else None,
    }


def save_sidecar_intel(
    sidecar_url: str,
    ip: str,
    enriched: dict[str, Any],
    context: dict[str, Any] | None = None,
    timeout: float = SIDECAR_TIMEOUT,
) -> bool:
    """Persist an enriched or CDN-edge IP record back to Sidecar `POST /ip-intel`."""
    if not sidecar_url or not ip:
        return False
    ctx = context if isinstance(context, dict) else {}
    geo = enriched.get("geo") if isinstance(enriched.get("geo"), dict) else {
        "countryCode": enriched.get("country_code"),
        "isp": enriched.get("isp"),
    }
    payload = {
        "ip": ip,
        "reputation_source": enriched.get("reputation_source") or "unavailable",
        "abuse_score": enriched.get("abuse_score"),
        "country_code": enriched.get("country_code") or geo.get("countryCode"),
        "isp": enriched.get("isp") or geo.get("isp"),
        "geo_json": geo,
        "reputation_json": enriched.get("reputation"),
        "target_hosts": ctx.get("target_hosts") or ["Unknown Host"],
        "endpoints_targeted": ctx.get("endpoints_targeted") or [],
        "http_methods_used": ctx.get("http_methods_used") or [],
        "mitre_tactics": ctx.get("mitre_tactics") or [],
        "attack_types": ctx.get("attack_types") or [],
        "alert_type": ctx.get("alert_type"),
        "attack_subtype": ctx.get("attack_subtype"),
        "target_host": ctx.get("target_host") or "Unknown Host",
        "endpoint": ctx.get("endpoint"),
    }
    req = Request(
        f"{sidecar_url.rstrip('/')}/ip-intel",
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Arbiter-SOC/2.0",
        },
    )
    try:
        with urlopen(req, timeout=timeout) as resp:
            return 200 <= int(getattr(resp, "status", 200)) < 300
    except Exception as exc:
        logger.debug("Sidecar writeback failed for %s: %s", ip, exc)
        return False


def _enrich_single_public_live(
    ip: str,
    *,
    abuse_key: str,
    vt_key: str,
    geo: dict[str, Any] | None,
    is_cdn: bool,
    remote_url: str | None,
    abuse_rate_limited: bool,
    vt_remaining: int,
    sidecar_connected: bool,
) -> tuple[dict[str, Any], bool, int]:
    """Run AbuseIPDB -> VirusTotal -> CDN fallback -> Remote DB cache for one public IP."""
    abuse_error: Exception | None = None
    if abuse_key and not abuse_rate_limited:
        try:
            data = query_abuseipdb(ip, abuse_key)
            if isinstance(data, dict) and data.get("abuseConfidenceScore") is not None and str(data.get("abuseConfidenceScore")).strip() != "":
                score = int(float(data["abuseConfidenceScore"]))
                country_code = data.get("countryCode") or (geo or {}).get("countryCode")
                isp = data.get("isp") or (geo or {}).get("isp") or "Unknown ISP"
                return (
                    {
                        "ip": ip,
                        "status": "enriched",
                        "abuse_score": score,
                        "vt_malicious": 0,
                        "country_code": country_code,
                        "isp": isp,
                        "domain": data.get("domain"),
                        "usage_type": data.get("usageType"),
                        "total_reports": int(data.get("totalReports") or 0),
                        "is_tor": bool(data.get("isTor")),
                        "is_whitelisted": bool(data.get("isWhitelisted")),
                        "reputation_source": "abuseipdb",
                        "is_private": False,
                        "geo": geo or {
                            "country": country_code or "Unknown",
                            "countryCode": country_code,
                            "isp": isp,
                            "as": isp,
                        },
                        "reputation": data,
                    },
                    False,
                    vt_remaining,
                )
        except Exception as exc:
            abuse_error = exc
            if getattr(exc, "status_code", None) == 429 or "429" in str(exc) or "rate limit" in str(exc).lower():
                abuse_rate_limited = True

    if vt_key and not abuse_rate_limited and vt_remaining > 0:
        vt_remaining -= 1
        try:
            vt_data = query_virustotal_ip(ip, vt_key)
            score, mal = _vt_malicious_score(vt_data)
            if score is not None and mal is not None:
                country_code = (geo or {}).get("countryCode")
                isp = (geo or {}).get("isp") or "Unknown ISP"
                return (
                    {
                        "ip": ip,
                        "status": "enriched",
                        "abuse_score": score,
                        "vt_malicious": mal,
                        "country_code": country_code,
                        "isp": isp,
                        "reputation_source": "virustotal",
                        "is_private": False,
                        "geo": geo or {"countryCode": country_code, "isp": isp, "as": isp},
                        "reputation": vt_data,
                    },
                    abuse_rate_limited,
                    vt_remaining,
                )
        except Exception as exc:
            logger.debug("VirusTotal fallback failed for %s: %s", ip, exc)

    if is_cdn and geo:
        return (
            {
                "ip": ip,
                "status": "cdn_edge",
                "abuse_score": None,
                "vt_malicious": 0,
                "country_code": geo.get("countryCode"),
                "isp": geo.get("isp") or "Cloudflare CDN",
                "reputation_source": "cdn_edge",
                "is_private": False,
                "geo": geo,
                "reputation": None,
            },
            abuse_rate_limited,
            vt_remaining,
        )

    remote = lookup_remote_ip_cache_detail(ip, remote_url)
    if remote.get("found") and remote.get("record"):
        return remote["record"], abuse_rate_limited, vt_remaining

    if abuse_rate_limited:
        err_detail = "Rate limit AbuseIPDB tercapai (HTTP 429)."
    elif abuse_error is not None:
        err_detail = f"Live AbuseIPDB gagal: {abuse_error}. {remote.get('error') or 'Cache IP Intel tidak tersedia.'}"
    elif sidecar_connected:
        err_detail = "IP belum ada di cache Sidecar dan API key AbuseIPDB/VirusTotal belum diatur atau tidak mengembalikan skor."
    else:
        err_detail = f"AbuseIPDB/VirusTotal API key belum diatur dan cache IP Intel tidak tersedia. {remote.get('error') or ''}".strip()

    return (
        {
            "ip": ip,
            "status": "error",
            "error": err_detail,
            "abuse_score": None,
            "reputation_source": "rate_limited" if abuse_rate_limited else "unavailable",
        },
        abuse_rate_limited,
        vt_remaining,
    )


def enrich_ips_with_sidecar(
    ips: list[str],
    *,
    abuseipdb_api_key: str = "",
    virustotal_api_key: str = "",
    sidecar_url: str = "",
    sidecar_writeback: bool = True,
    remote_url: str | None = None,
    context: dict[str, Any] | None = None,
    single_enrich_fn: Any = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Batch-enrich IPs using HTTP Sidecar cache, ip-api Geo/CDN detection, AbuseIPDB, and VirusTotal fallback."""
    ordered_ips = list(dict.fromkeys(normalize_ip_address(x) for x in ips if normalize_ip_address(x)))
    effective_abuse_key = (abuseipdb_api_key or ABUSEIPDB_API_KEY or "").strip()
    effective_vt_key = (virustotal_api_key or VIRUSTOTAL_API_KEY or "").strip()
    candidates = parse_sidecar_candidates(sidecar_url)

    if not candidates and not effective_vt_key and single_enrich_fn is not None:
        ordered_results = []
        for ip in ordered_ips:
            if remote_url is None:
                ordered_results.append(single_enrich_fn(ip, api_key=abuseipdb_api_key or None))
            else:
                ordered_results.append(single_enrich_fn(ip, api_key=abuseipdb_api_key or None, remote_url=remote_url))
        stats = {
            "total_ips": len(ordered_ips),
            "private_ips": sum(1 for r in ordered_results if r.get("status") == "private"),
            "public_ips": sum(1 for r in ordered_results if r.get("status") not in ("private", "invalid")),
            "from_cache": sum(1 for r in ordered_results if r.get("cache_source") or r.get("from_cache")),
            "cdn_edge": sum(1 for r in ordered_results if r.get("status") == "cdn_edge"),
            "enriched_live": sum(1 for r in ordered_results if not r.get("cache_source") and r.get("reputation_source") in ("abuseipdb", "virustotal")),
            "rate_limited": sum(1 for r in ordered_results if r.get("reputation_source") == "rate_limited"),
            "unavailable": sum(1 for r in ordered_results if r.get("status") == "error"),
            "sidecar": {
                "configured": False,
                "connected": False,
                "url": None,
                "cached_entries": 0,
                "writeback_count": 0,
            },
        }
        return ordered_results, stats

    results_by_ip: dict[str, dict[str, Any]] = {}
    private_ips: list[str] = []
    public_ips: list[str] = []

    for ip in ordered_ips:
        if not is_valid_ip(ip):
            results_by_ip[ip] = {
                "ip": ip,
                "status": "invalid",
                "error": "Bukan format IPv4/IPv6 yang valid.",
                "abuse_score": None,
            }
        elif is_private_ip(ip):
            private_ips.append(ip)
            results_by_ip[ip] = {
                "ip": ip,
                "status": "private",
                "abuse_score": 0,
                "vt_malicious": 0,
                "country_code": "LAN",
                "isp": "Private Local Network (RFC1918)",
                "domain": None,
                "usage_type": "Private / Intranet",
                "total_reports": 0,
                "reputation_source": "local_private",
                "is_private": True,
            }
        else:
            public_ips.append(ip)

    active_sidecar_url: str | None = None
    sidecar_cached_entries = 0
    from_cache_ips: set[str] = set()
    uncached_public: list[str] = []

    if candidates and public_ips:
        probe = probe_sidecar(candidates, public_ips[:5])
        if probe.get("connected") and probe.get("url"):
            active_sidecar_url = str(probe["url"])
            cached_map: dict[str, dict[str, Any]] = dict(probe.get("cached") or {})
            if len(public_ips) > 5:
                cached_map.update(fetch_sidecar_cache(active_sidecar_url, public_ips[5:]))
            sidecar_cached_entries = len(cached_map)
            for ip in public_ips:
                entry = cached_map.get(ip)
                if has_usable_sidecar_cache(entry):
                    results_by_ip[ip] = normalize_sidecar_record(ip, entry, active_sidecar_url)  # type: ignore[arg-type]
                    from_cache_ips.add(ip)
                else:
                    uncached_public.append(ip)
        else:
            uncached_public = list(public_ips)
    else:
        uncached_public = list(public_ips)

    writeback_count = 0

    if uncached_public:
        geo_map = query_geo_batch(uncached_public)
        cdn_queue: list[str] = []
        reputation_queue: list[str] = []
        for ip in uncached_public:
            if is_cdn_edge(geo_map.get(ip)):
                cdn_queue.append(ip)
            else:
                reputation_queue.append(ip)

        abuse_rate_limited = False
        vt_remaining = VT_MAX_FALLBACK

        for ip in reputation_queue:
            res, abuse_rate_limited, vt_remaining = _enrich_single_public_live(
                ip,
                abuse_key=effective_abuse_key,
                vt_key=effective_vt_key,
                geo=geo_map.get(ip),
                is_cdn=False,
                remote_url=remote_url,
                abuse_rate_limited=abuse_rate_limited,
                vt_remaining=vt_remaining,
                sidecar_connected=bool(active_sidecar_url),
            )
            results_by_ip[ip] = res

        for ip in cdn_queue:
            # Second pass for CDN edge only when AbuseIPDB quota is healthy
            res, abuse_rate_limited, vt_remaining = _enrich_single_public_live(
                ip,
                abuse_key=effective_abuse_key if not abuse_rate_limited else "",
                vt_key="",
                geo=geo_map.get(ip),
                is_cdn=True,
                remote_url=remote_url,
                abuse_rate_limited=abuse_rate_limited,
                vt_remaining=0,
                sidecar_connected=bool(active_sidecar_url),
            )
            results_by_ip[ip] = res

        if active_sidecar_url and sidecar_writeback:
            for ip in uncached_public:
                res = results_by_ip[ip]
                if not res.get("from_cache") and res.get("status") in ("enriched", "cdn_edge"):
                    if save_sidecar_intel(active_sidecar_url, ip, res, context=context):
                        writeback_count += 1

    ordered_results = [results_by_ip[ip] for ip in ordered_ips if ip in results_by_ip]
    stats = {
        "total_ips": len(ordered_ips),
        "private_ips": len(private_ips),
        "public_ips": len(public_ips),
        "from_cache": len(from_cache_ips),
        "cdn_edge": sum(1 for r in ordered_results if r.get("status") == "cdn_edge" or r.get("reputation_source") == "cdn_edge"),
        "enriched_live": sum(
            1 for r in ordered_results
            if not r.get("from_cache") and r.get("reputation_source") in ("abuseipdb", "virustotal")
        ),
        "rate_limited": sum(1 for r in ordered_results if r.get("reputation_source") == "rate_limited"),
        "unavailable": sum(1 for r in ordered_results if r.get("status") == "error"),
        "sidecar": {
            "configured": bool(candidates),
            "connected": bool(active_sidecar_url),
            "url": active_sidecar_url,
            "cached_entries": sidecar_cached_entries,
            "writeback_count": writeback_count,
        },
    }
    return ordered_results, stats
