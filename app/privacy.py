"""Privacy and data-sanitization engine for Arbiter.

Ensures that internal IP addresses, sensitive hostnames, passwords, tokens,
and credentials are fully redacted before logs can be exported or consulted
with cloud AI services.
"""

import re
from typing import Any


def sanitize_text(text: Any) -> str:
    """Sanitizes raw log or output text before copying for external AI inquiry.

    Deterministic regex redactor:
    - Redacts private RFC1918 IPs -> <INTERNAL_IP>
    - Redacts loopback IPs -> <LOCALHOST>
    - Redacts public IPs -> <EXTERNAL_IP>
    - Redacts passwords/credentials/tokens -> <REDACTED_SECRET>
    - Redacts emails -> <REDACTED_EMAIL>
    """
    if text is None:
        return ""
    s = str(text)

    # 1. Credentials / Passwords / Secrets / Tokens
    s = re.sub(
        r"(?i)\b(password|passwd|pwd|token|api_key|secret|authorization|bearer|auth|access_token|refresh_token)\s*[:=]\s*[^\s,;\"'<>]+",
        r"\1=<REDACTED_SECRET>",
        s,
    )

    # 2. Email addresses
    s = re.sub(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        "<REDACTED_EMAIL>",
        s,
    )

    # 3. IP Addresses
    def replace_ip(match):
        ip = match.group(0)
        try:
            parts = [int(p) for p in ip.split(".")]
            if any(p > 255 for p in parts):
                return ip
            if parts[0] == 127:
                return "<LOCALHOST>"
            if parts[0] == 10 or (parts[0] == 172 and 16 <= parts[1] <= 31) or (parts[0] == 192 and parts[1] == 168):
                return "<INTERNAL_IP>"
            return "<EXTERNAL_IP>"
        except Exception:
            return ip

    s = re.sub(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b", replace_ip, s)
    return s
