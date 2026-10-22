# Arbiter

<p align="center">
  <strong>Unified Wazuh SIEM Telemetry Normalizer, Attack Chronology Triage &amp; Incident Investigation Platform</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue?style=flat-square&logo=python" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-Production-009688?style=flat-square&logo=fastapi" alt="FastAPI">
  <img src="https://img.shields.io/badge/PostgreSQL-16-336791?style=flat-square&logo=postgresql" alt="PostgreSQL">
  <img src="https://img.shields.io/badge/Docker-Ready-2496ED?style=flat-square&logo=docker" alt="Docker">
  <img src="https://img.shields.io/badge/Privacy-Airgapped%20Local-emerald?style=flat-square" alt="Privacy">
</p>

---

## 🎯 Overview

**Arbiter** is an open-source, airgapped SOC investigation desk built to bridge the gap between raw **Wazuh SIEM alerts** and **executive incident reporting**. 

When investigating high-volume attacks (credential stuffing, SSH brute-force, web vulnerability probing), raw Wazuh Elasticsearch JSON exports often flood analysts with tens of thousands of repetitive log lines. Arbiter normalizes multi-format logs, deduplicates recurring attacks using stable hashing, enriches source IPs with local Threat Intelligence, and produces **Google Docs**, **Word (.docx)**, and **Excel (.xlsx)** deliverables in one click.

---

## ⚡ Key Capabilities

### 1. Resilient Multi-Format Ingestion
- **Any Ingest Format**: Accepts Elasticsearch `hits.hits[]` exports, raw JSON arrays, JSON Lines (`.jsonl`), or single alert objects.
- **Direct Paste & File Upload**: Ingest via file upload (`.json` / `.txt`) or instant paste with real-time JSON validation.
- **Control Byte Salvage**: Built-in parser (`strict=False`) safely decodes raw logs containing unescaped control characters (such as raw newlines inside HTTP request logs) without mutating or dropping valid events.
- **Duplicate Wazuh ID Safeguard**: Re-ingesting identical alerts or previously imported Wazuh IDs is automatically identified and ignored to prevent data corruption.

### 2. High-Precision Log Dissector (No False Fields)
- Specialized regex engines for:
  - **Web Access Logs**: Apache / Nginx combined logs (Method, Path, Query string, Status code, Referer, User-Agent).
  - **Syslog & Auth Logs**: OpenSSH (`sshd`), PAM authentication failures, session lifecycle.
  - **Linux Kernel & Audit**: AppArmor profiles, syscall audit events without misinterpreting timestamps as path names.
  - **Embedded HTTP & JSON Payloads**: Auto-detects URLs, methods, and status codes inside generic syslog lines.

### 3. Signature-Based Deduplication & Expandable View
- Computes a stable 24-character SHA-256 signature across `(tenant, agent, rule_id, srcip, normalized_log)`.
- Eliminates noise by condensing thousands of repetitive scans into a single triage row with `Hit Count` and `first_seen s/d last_seen` time range.
- **Expandable Occurrences**: Click `▶ Rincian Duplikasi` to expand an inline drawer showing every single duplicate instance with exact timestamps and individual Wazuh IDs.

### 4. Enterprise Multi-Tenant Architecture
- Automatic tenant extraction from `agent.labels.tenant`.
- Top-level tenant navigation tabs with real-time count badges.
- Isolate investigations per tenant or triage across all tenants simultaneously.

### 5. Review & Triage Status Workflow
- Flag alerts as `⭕ Pending` or `✅ Reviewed`.
- **Shift + Click Range Selection**: Select batches of 50+ alerts in seconds without clicking checkboxes one by one.
- Quick batch selection chips: *Pilih Yang Tampil*, *Pilih Belum Direview*, *Batal Pilihan*.
- Floating batch toolbar for one-click mass review marking and group assignment.

### 6. Local Threat Intelligence Auto-Enrichment
- Zero external API exposure: Joins incoming `source_ip` directly with local PostgreSQL Threat Intelligence tables (`ip_intel_cache`).
- Real-time AbuseIPDB confidence score, VirusTotal malicious detection count, ISP, and country code.
- Clickable IP detail modal + direct pivot link (`↗`) to local deep-dive intelligence dashboards.

### 7. Privacy-First Cloud AI Redactor
- **Zero-Cloud Log Transmission**: Raw logs, database records, and credentials never leave your local environment.
- **One-Click Sanitizer**: Deterministic regex redactor masks private RFC1918 IPs (`<INTERNAL_IP>`), public IPs (`<EXTERNAL_IP>`), passwords/tokens (`<REDACTED_SECRET>`), and emails (`<REDACTED_EMAIL>`). Safely copy logs for external LLM consultation (ChatGPT / Claude) without leaking company infrastructure.

### 8. Official One-Click Deliverables (5 Export Paths)
- **📋 Salin GDocs**: Formatted HTML table with zebra striping, severity badges, attack chronology, root cause analysis, and remediation ready for direct `Ctrl+V` pasting into Google Docs.
- **📄 Word Document (.docx)**: Formal landscape document with styled tables and executive summary sections.
- **📊 Excel Workbook (.xlsx)**: Multi-column spreadsheet with Threat Intel metrics and auto-adjusted columns.
- **📋 Salin TSV**: Tab-Separated Values for instant pasting into spreadsheet software.
- **📝 Markdown Briefing**: Executive incident summary with KPI metrics.

---

## 🛠️ Architecture & Tech Stack

```text
               +-------------------------------------------------------+
               |                  Browser / SOC Analyst                |
               +---------------------------+---------------------------+
                                           | HTTP (Port 8000)
                                           v
+--------------------------------------------------------------------------------------+
| Arbiter Application Container                                                        |
|                                                                                      |
|   +---------------------+   +---------------------+   +--------------------------+   |
|   |   FastAPI Backend   |   |   Log Dissector     |   |   Deliverables Engine    |   |
|   |  - REST Endpoints   |   |  - Access log / Sys |   |  - Google Docs HTML      |   |
|   |  - Multi-Tenant API |   |  - AppArmor / sshd  |   |  - Word (.docx)          |   |
|   |  - Incident Groups  |   |  - Signature Dedup  |   |  - Excel (.xlsx)         |   |
|   +----------+----------+   +----------+----------+   +--------------------------+   |
|              |                         |                                             |
|              +-------------------------+                                             |
|                                        |                                             |
+----------------------------------------|---------------------------------------------+
                                         v SQL
+--------------------------------------------------------------------------------------+
| PostgreSQL Database (abuseip / arbiter)                                             |
|  - wazuh.alerts (telemetry, deduplication hits, review flags, wazuh_ids)             |
|  - wazuh.analysis_groups (investigation cases, verdicts, remediation)                |
|  - wazuh.alert_group_members (many-to-many incident mapping)                         |
|  - public.ip_intel_cache (local threat intelligence cache)                           |
+--------------------------------------------------------------------------------------+
```

- **Backend**: Python 3.11+, FastAPI, Uvicorn, Psycopg 3
- **Frontend**: Linear-inspired High-Density Dark Theme (Inter, JetBrains Mono, Tailwind CSS variables)
- **Reporting**: python-docx, openpyxl
- **Database**: PostgreSQL 15+

---

## 🚀 Setup & Getting Started

### Prerequisites
- Docker & Docker Compose **OR** Python 3.11+ with PostgreSQL.

---

### Method A: Standalone Docker Setup (Fastest for new users)

If you **do not** have PostgreSQL installed, Arbiter provides a bundled PostgreSQL service initialized automatically via `init-db.sql`:

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Nothrovo/Arbiter.git
   cd Arbiter
   ```

2. **Run with standalone profile**:
   ```bash
   docker compose --profile standalone up -d --build
   ```

3. **Access Arbiter**:
   Open **`http://localhost:8000`** in your browser.
   The database and all schemas are pre-configured and ready for use.

---

### Method B: Host Mode (Connect to existing PostgreSQL / IP Intel)

If you already run PostgreSQL locally (e.g. on port 5432 with database `abuseip`):

1. **Configure `.env`**:
   ```bash
   cp .env.example .env
   # Edit .env and point DATABASE_URL to your local database:
   # DATABASE_URL=postgresql://user:password@127.0.0.1:5432/abuseip
   ```

2. **Start Arbiter**:
   ```bash
   docker compose up -d --build
   ```

3. **Access**:
   Open **`http://localhost:8000`**.

---

### Method C: Local Python Setup (Without Docker)

1. **Create and activate a virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment & start**:
   ```bash
   cp .env.example .env
   ./start.sh
   ```

---

## 📖 SOC Analyst Quickstart Workflow

1. **Ingest Telemetry**:
   - Click **`📥 Ingest Alert`** on the top toolbar.
   - Either paste your raw Wazuh / Elasticsearch hits JSON or upload your `.json`/`.txt` file.
   - Alerts are parsed, deduplicated, and enriched instantly.

2. **Select Tenant**:
   - Click the tenant tab (e.g. `🏢 wicida`, `🏢 sgu`) to isolate investigations to a specific client.

3. **Triage & Chronology**:
   - Use the quick preset chips (`🚫 403`, `🔁 Berulang`, `🤖 Bot`) to filter noisy scans.
   - Click **`⏳ Urutan: Terlama → Terbaru`** to replay the attack chronologically from the initial probe to the final exploit attempt.

4. **Group into an Incident Case**:
   - Hold **Shift + Click** to select multiple relevant alerts.
   - Click **`＋ Buat Insiden`** on the floating batch bar.
   - Enter Case Title, Category, Severity, Technical Analysis, Verdict (Conclusion), and Remediation.

5. **Export Deliverable**:
   - Click **`📋 Salin GDocs`** ➔ Open your Google Doc and press **`Ctrl+V`**. Your complete formatted investigation report with colored severity tags and clean chronology tables is ready for submission!

---

## 🧪 Testing & Quality Assurance

Run the comprehensive unit and integration test suite:

```bash
# Run all 23+ automated tests
python -m unittest discover -s tests -v
```

Tests cover:
- Combined Apache/Nginx, Syslog, AppArmor, and OpenSSH log parsing
- Signature-based deduplication and timestamp normalization
- Duplicate Wazuh ID safeguards
- Multi-tenant isolation and review status flags
- Document deliverables (HTML, DOCX, XLSX, TSV, Markdown)
- Privacy sanitization engine

---

## 🔒 Security & Privacy Notice

- **No Remote Telemetry**: Arbiter does not phone home, load tracking pixels, or transmit sensitive telemetry to third parties.
- **Airgapped Design**: Local rule-based correlation and local database queries ensure that internal IP addresses, infrastructure paths, and user data remain strictly confidential.

---

## 📄 License

Distributed under the **MIT License**. See `LICENSE` for more information.
