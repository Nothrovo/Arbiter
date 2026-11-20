"""Deliverables and report export engines for Arbiter.

Supports:
1. GDocs Table Report (Semantic HTML designed for direct Ctrl+V clipboard paste into Google Docs)
2. Word Document (.docx landscape with formal SOC headers and tables)
3. Excel Workbook (.xlsx styled sheets with threat intelligence metrics)
4. Tab-Separated Values (TSV clipboard text)
5. Markdown Executive Briefing

Every format shares one canonical evidence table so Triage, Reports, and the
Flag & Rule Tuning tracker produce the same columns in the same order.
"""

from __future__ import annotations

import csv
import io
import json
from html import escape
from typing import Any

from docx import Document
from docx.enum.section import WD_ORIENT
from docx.shared import Inches, Pt, RGBColor
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter


def _as_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str) and value.strip().startswith("{"):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else {}
        except ValueError:
            return {}
    return {}


def _first(*values: Any) -> str:
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return ""


def _split_uri(uri: str) -> tuple[str, str]:
    text = str(uri or "")
    if "?" not in text:
        return text, ""
    path, query = text.split("?", 1)
    return path, query


def alert_full_log(alert: dict[str, Any]) -> str:
    return _first(alert.get("full_log"), _as_dict(alert.get("raw")).get("full_log"))


def _evidence_fields(alert: dict[str, Any]) -> dict[str, Any]:
    parsed = _as_dict(alert.get("parsed_details"))
    data = _as_dict(alert.get("data"))
    uri = _first(parsed.get("uri"), data.get("uri"), data.get("url"))
    path, query = _split_uri(uri)
    payload = _first(
        parsed.get("query"),
        query,
        data.get("query"),
        data.get("payload"),
        data.get("body"),
    )
    tenant = _first(alert.get("tenant"), "Default")
    agent = _first(alert.get("agent_name"))
    return {
        "hit": int(alert.get("hit_count") or 1),
        "kejadian": _first(alert.get("timestamp")),
        "client_ip": _first(alert.get("source_ip"), parsed.get("srcip"), data.get("srcip")),
        "timestamp_log": _first(parsed.get("timestamp"), parsed.get("timestamp_display")),
        "alert_id": _first(alert.get("alert_id"), alert.get("id")),
        "method": _first(parsed.get("method"), data.get("method")),
        "path_uri": _first(parsed.get("path"), path, data.get("path"), uri),
        "query_payload": payload,
        "protocol": _first(parsed.get("protocol")),
        "status": _first(parsed.get("status"), data.get("status"), data.get("id")),
        "bytes": _first(parsed.get("bytes")),
        "rule_id": _first(alert.get("rule_id")),
        "rule_description": _first(alert.get("description")),
        "tenant_agent": f"{tenant} ({agent})" if agent else tenant,
        "full_log": alert_full_log(alert),
        "user_agent": _first(parsed.get("ua"), parsed.get("user_agent"), data.get("ua"), data.get("user_agent")),
    }


# (key, label) — the single source of truth for every exported evidence table.
EXPORT_COLUMNS: tuple[tuple[str, str], ...] = (
    ("no", "No"),
    ("hit", "Hit"),
    ("kejadian", "Kejadian"),
    ("client_ip", "Client IP"),
    ("timestamp_log", "Timestamp Log"),
    ("alert_id", "Wazuh ID"),
    ("method", "Method"),
    ("path_uri", "Path / URI"),
    ("query_payload", "Query / Payload"),
    ("protocol", "Protocol"),
    ("status", "Status"),
    ("bytes", "Bytes"),
    ("rule_id", "Rule ID"),
    ("rule_description", "Rule Description"),
    ("tenant_agent", "Tenant (Agent)"),
    ("full_log", "Full Log"),
    ("user_agent", "User-Agent"),
)

EXPORT_HEADERS = [label for _key, label in EXPORT_COLUMNS]
EXPORT_KEYS = [key for key, _label in EXPORT_COLUMNS]


def export_row(alert: dict[str, Any], index: int) -> dict[str, Any]:
    row = {"no": index}
    row.update(_evidence_fields(alert))
    return row


def export_rows(alerts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [export_row(alert, index) for index, alert in enumerate(alerts, 1)]


def _flat(value: Any) -> str:
    return str(value if value is not None else "").replace("\t", " ").replace("\r\n", " ").replace("\n", " ").strip()


def generate_tsv_table(alerts: list[dict[str, Any]]) -> str:
    """Generates a clean Tab-Separated Values table for instant pasting into Excel or Word."""
    alerts = sorted(alerts, key=lambda a: (str(a.get("rule_id") or ""), str(a.get("timestamp") or ""), int(a.get("id") or 0)))
    rows = [[_flat(label) for label in EXPORT_HEADERS]]
    for item in export_rows(alerts):
        rows.append([_flat(item.get(key)) for key in EXPORT_KEYS])
    output = io.StringIO()
    writer = csv.writer(output, delimiter="\t", lineterminator="\n")
    writer.writerows(rows)
    return output.getvalue()


def generate_markdown_report(alerts: list[dict[str, Any]], meta: dict[str, Any]) -> str:
    """Generates an executive SOC investigation summary in Markdown format."""
    alerts = sorted(alerts, key=lambda a: (str(a.get("rule_id") or ""), str(a.get("timestamp") or ""), int(a.get("id") or 0)))
    total_hits = sum(int(a.get("hit_count") or 1) for a in alerts)
    repeated = len([a for a in alerts if int(a.get("hit_count") or 1) > 1])
    highest_lvl = max([int(a.get("rule_level") or 0) for a in alerts], default=0)

    title = meta.get("title") or "SOC Security Telemetry Report"
    category = meta.get("category") or "General Incident"
    severity = meta.get("severity") or ("Critical" if highest_lvl >= 15 else "High" if highest_lvl >= 12 else "Medium" if highest_lvl >= 7 else "Low")
    status = meta.get("status") or "Investigating"

    lines = [
        f"# {title}",
        f"**Kategori:** {category} | **Severity:** {severity.upper()} | **Status:** {status.upper()}",
        f"- **Total Alert Unik:** {len(alerts)}",
        f"- **Total Kemunculan (Hits):** {total_hits} (dengan {repeated} kluster berulang)",
        f"- **Tingkat Severity Maksimum:** Level {highest_lvl}",
        "",
        "## 1. Tabel Kronologi Investigasi",
        "",
    ]

    def cell(value: Any) -> str:
        return _flat(value).replace("|", "\\|") or "-"

    lines.append("| " + " | ".join(EXPORT_HEADERS) + " |")
    lines.append("| " + " | ".join("---" for _ in EXPORT_HEADERS) + " |")
    for item in export_rows(alerts):
        lines.append("| " + " | ".join(cell(item.get(key)) for key in EXPORT_KEYS) + " |")

    lines.extend([
        "",
        "## 2. Analisis Teknis Investigasi",
        meta.get("analysis") or "Aktivitas serangan terekam secara kronologis pada tabel di atas. Diperlukan mitigasi berkelanjutan.",
        "",
        "## 3. Kesimpulan Investigasi (Verdict)",
        meta.get("conclusion") or "True Positive — Terkonfirmasi adanya anomali atau upaya akses yang terdeteksi Wazuh SIEM.",
        "",
        "## 4. Rekomendasi Tindakan (Containment & Mitigation)",
        meta.get("recommendation") or "1. Blokir alamat IP penyerang pada edge firewall / perimeter.\n2. Verifikasi status keamanan endpoint terkait.\n3. Lakukan audit pada rule deteksi.",
    ])
    return "\n".join(lines)


def generate_gdocs_html_report(alerts: list[dict[str, Any]], meta: dict[str, Any]) -> str:
    """Generates styled semantic HTML with clean table borders and colors for Google Docs pasting."""
    alerts = sorted(alerts, key=lambda a: (str(a.get("rule_id") or ""), str(a.get("timestamp") or ""), int(a.get("id") or 0)))
    title = meta.get("title") or "Laporan Hasil Investigasi Insiden Keamanan (SOC Incident Report)"
    category = meta.get("category") or "Security Incident"
    severity = meta.get("severity") or "Medium"
    status = meta.get("status") or "Open"
    analysis = meta.get("analysis") or ""
    conclusion = meta.get("conclusion") or ""
    recommendation = meta.get("recommendation") or ""

    lvl_class = "badge-high" if severity.lower() in ("high", "critical") else ("badge-med" if severity.lower() == "medium" else "badge-low")

    unique_ips = list(dict.fromkeys(a["source_ip"] for a in alerts if a.get("source_ip")))
    unique_agents = list(dict.fromkeys(a["agent_name"] for a in alerts if a.get("agent_name")))
    first_time = alerts[0].get("timestamp") if alerts else "-"
    last_time = alerts[-1].get("timestamp") if alerts else "-"
    total_hits = sum(int(a.get("hit_count") or 1) for a in alerts)

    html_parts = [
        """<!DOCTYPE html><html><head><meta charset="utf-8">
        <style>
        body { font-family: Arial, sans-serif; font-size: 10pt; color: #111; line-height: 1.35; margin: 0; padding: 0; }
        h1 { color: #1a365d; border-bottom: 2px solid #2b6cb0; padding-bottom: 4px; font-size: 15pt; margin: 8px 0 10px; }
        h2 { color: #2c5282; font-size: 12pt; margin: 16px 0 8px; border-bottom: 1px solid #cbd5e0; padding-bottom: 3px; }
        table { width: 100%; border-collapse: collapse; margin: 8px 0 14px; font-size: 8pt; line-height: 1.3; }
        th, td { border: 1px solid #cbd5e0; padding: 4px 6px; text-align: left; vertical-align: top; }
        th { background-color: #edf2f7; color: #2d3748; font-weight: bold; }
        tr:nth-child(even) { background-color: #f7fafc; }
        .badge-high { background-color: #fed7d7; color: #9b2c2c; padding: 1px 5px; border-radius: 3px; font-weight: bold; font-size: 8pt; }
        .badge-med { background-color: #feebc8; color: #7b341e; padding: 1px 5px; border-radius: 3px; font-weight: bold; font-size: 8pt; }
        .badge-low { background-color: #e2e8f0; color: #4a5568; padding: 1px 5px; border-radius: 3px; font-size: 8pt; }
        .meta-box { background: #f8fafc; border-left: 4px solid #3182ce; padding: 8px 12px; margin: 8px 0; font-size: 9.5pt; }
        .content-box { background: #ffffff; border: 1px solid #cbd5e0; padding: 8px 12px; border-radius: 4px; margin-bottom: 12px; font-size: 9.5pt; }
        .mono { font-family: Consolas, "Courier New", monospace; font-size: 7.5pt; word-break: break-all; }
        </style></head><body>
        """,
        f"<h1>{escape(title)}</h1>",
        f"""<div class="meta-box">
            <p style="margin: 2px 0;"><strong>Kategori:</strong> {escape(category)} | <strong>Severity:</strong> <span class="{lvl_class}">{escape(severity.upper())}</span> | <strong>Status:</strong> {escape(status.upper())}</p>
            <p style="margin: 2px 0;"><strong>Rentang Waktu:</strong> {escape(str(first_time))} s/d {escape(str(last_time))}</p>
            <p style="margin: 2px 0;"><strong>Total Alert:</strong> {len(alerts)} grup unik ({total_hits} total hits) | <strong>Host Terdampak:</strong> {escape(', '.join(unique_agents) or '-')} | <strong>IP Penyerang:</strong> {escape(', '.join(unique_ips) or '-')}</p>
        </div>
        <h2>1. Tabel Kronologi Investigasi (Attack Chronology)</h2>
        """,
    ]

    if alerts:
        header_html = "".join(
            f'<th style="border: 1px solid #cbd5e0; padding: 4px 6px; text-align: left; vertical-align: top; '
            f'font-weight: bold; color: #2d3748;">{escape(label)}</th>'
            for label in EXPORT_HEADERS
        )
        html_parts.append(
            '<table border="1" cellpadding="4" cellspacing="0" style="width: 100%; border-collapse: collapse; '
            'border: 1px solid #cbd5e0; margin: 8px 0 14px; font-family: Arial, sans-serif; font-size: 8pt; line-height: 1.3;">'
            f'<thead><tr style="background-color: #edf2f7;">{header_html}</tr></thead><tbody>'
        )
        for idx, item in enumerate(export_rows(alerts), 1):
            row_bg = "background-color: #f7fafc;" if idx % 2 == 0 else "background-color: #ffffff;"
            cells = []
            for key in EXPORT_KEYS:
                value = item.get(key)
                style = "border: 1px solid #cbd5e0; padding: 4px 6px; text-align: left; vertical-align: top;"
                if key == "full_log":
                    style += " font-family: Consolas, 'Courier New', monospace; font-size: 7.5pt; word-break: break-all; white-space: pre-wrap;"
                elif key == "hit":
                    style += " font-weight: bold;"
                content = escape(str(value if value is not None else "")) or "-"
                if key == "hit" and str(value or "") not in ("", "0"):
                    content = f"{content}x"
                cells.append(f'<td style="{style}">{content}</td>')
            html_parts.append(f'<tr style="{row_bg}">{"".join(cells)}</tr>')
        html_parts.append("</tbody></table>")
    else:
        html_parts.append("<p><em>Tidak ada alert terkait dalam laporan ini.</em></p>")

    html_parts.append(f"""
    <h2>2. Kronologi &amp; Analisis Investigasi</h2>
    <div class="content-box">
        {escape(analysis).replace(chr(10), '<br>') or '<em>Aktivitas serangan terekam secara kronologis pada tabel di atas. Diperlukan penelusuran lebih lanjut terkait payload yang dieksekusi.</em>'}
    </div>

    <h2>3. Kesimpulan Investigasi (Verdict)</h2>
    <div class="content-box">
        {escape(conclusion).replace(chr(10), '<br>') or '<em>True Positive — Terkonfirmasi adanya aktivitas anomali / serangan yang terdeteksi oleh Wazuh SIEM.</em>'}
    </div>

    <h2>4. Rekomendasi Tindakan (Containment & Remediation)</h2>
    <div class="content-box">
        {escape(recommendation).replace(chr(10), '<br>') or '<em>1. Terapkan pemblokiran IP penyerang pada Edge Firewall / WAF.<br>2. Verifikasi integritas akun dan file pada host terdampak.<br>3. Pastikan security patches dan konfigurasi hardening telah diperbarui.</em>'}
    </div>
    </body></html>
    """)
    return "".join(html_parts)


def generate_docx_landscape_report(alerts: list[dict[str, Any]], meta: dict[str, Any]) -> io.BytesIO:
    """Generates an official Word document (.docx) in landscape orientation."""
    alerts = sorted(alerts, key=lambda a: (str(a.get("rule_id") or ""), str(a.get("timestamp") or ""), int(a.get("id") or 0)))
    doc = Document()
    section = doc.sections[0]
    section.orientation = WD_ORIENT.LANDSCAPE
    new_width, new_height = section.page_height, section.page_width
    section.page_width = new_width
    section.page_height = new_height
    section.top_margin = Inches(0.5)
    section.bottom_margin = Inches(0.5)
    section.left_margin = Inches(0.5)
    section.right_margin = Inches(0.5)

    title = meta.get("title") or "SOC Security Telemetry & Incident Report"
    category = meta.get("category") or "Security Incident"
    severity = meta.get("severity") or "Medium"
    status = meta.get("status") or "Open"

    title_p = doc.add_paragraph()
    title_run = title_p.add_run(title)
    title_run.font.size = Pt(16)
    title_run.font.bold = True
    title_run.font.color.rgb = RGBColor(26, 54, 93)

    meta_p = doc.add_paragraph()
    meta_p.add_run(f"Kategori: {category}  |  Severity: {severity.upper()}  |  Status: {status.upper()}\n").bold = True
    first_time = alerts[0].get("timestamp") if alerts else "-"
    last_time = alerts[-1].get("timestamp") if alerts else "-"
    meta_p.add_run(f"Rentang Waktu: {first_time} s/d {last_time}  |  Total Alert: {len(alerts)}")

    doc.add_heading("1. Tabel Kronologi Investigasi", level=2)

    table = doc.add_table(rows=1, cols=len(EXPORT_HEADERS))
    table.style = "Table Grid"
    hdr_cells = table.rows[0].cells
    for i, label in enumerate(EXPORT_HEADERS):
        hdr_cells[i].text = label
        p = hdr_cells[i].paragraphs[0]
        p.runs[0].font.bold = True
        p.runs[0].font.size = Pt(7.5)

    for item in export_rows(alerts):
        row_cells = table.add_row().cells
        for i, key in enumerate(EXPORT_KEYS):
            value = item.get(key)
            row_cells[i].text = str(value if value is not None else "")
            for p in row_cells[i].paragraphs:
                for r in p.runs:
                    r.font.size = Pt(6.5)

    doc.add_heading("2. Analisis Investigasi", level=2)
    doc.add_paragraph(meta.get("analysis") or "Aktivitas serangan terekam secara kronologis pada tabel di atas.")

    doc.add_heading("3. Kesimpulan Investigasi (Verdict)", level=2)
    doc.add_paragraph(meta.get("conclusion") or "True Positive — Terkonfirmasi adanya aktivitas serangan.")

    doc.add_heading("4. Rekomendasi Tindakan", level=2)
    doc.add_paragraph(meta.get("recommendation") or "1. Blokir IP penyerang pada firewall.\n2. Verifikasi host target.")

    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf


def generate_xlsx_workbook(alerts: list[dict[str, Any]]) -> io.BytesIO:
    """Generates a styled Excel workbook (.xlsx) with the canonical evidence table."""
    alerts = sorted(alerts, key=lambda a: (str(a.get("rule_id") or ""), str(a.get("timestamp") or ""), int(a.get("id") or 0)))
    wb = Workbook()
    ws = wb.worksheets[0]
    ws.title = "Wazuh Alerts Triage"

    ws.append(EXPORT_HEADERS)

    header_fill = PatternFill(start_color="1A365D", end_color="1A365D", fill_type="solid")
    header_font = Font(name="Arial", size=9, bold=True, color="FFFFFF")
    thin_border = Border(
        left=Side(style="thin", color="CBD5E0"),
        right=Side(style="thin", color="CBD5E0"),
        top=Side(style="thin", color="CBD5E0"),
        bottom=Side(style="thin", color="CBD5E0"),
    )

    for col_idx in range(1, len(EXPORT_HEADERS) + 1):
        cell = ws.cell(row=1, column=col_idx)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = thin_border

    for idx, item in enumerate(export_rows(alerts), 1):
        row_vals = [item.get(key) for key in EXPORT_KEYS]
        ws.append(row_vals)
        for col_idx in range(1, len(row_vals) + 1):
            cell = ws.cell(row=idx + 1, column=col_idx)
            cell.font = Font(name="Arial", size=8)
            cell.border = thin_border
            cell.alignment = Alignment(vertical="top", wrap_text=True)

    for col in ws.columns:
        max_len = max(len(str(cell.value or "")) for cell in col)
        col_letter = get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = min(max(max_len + 3, 10), 60)

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf
