# Arbiter SOC Desk Upgrades Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement two-way IP Intel live enrichment, fix Google Docs / TSV export table styling and un-truncate raw logs, add Arbiter brand favicon, and enhance local correlation cards with rich forensic details.

**Architecture:** 
1. Backend adds `/api/intel/enrich` endpoint with AbuseIPDB integration and PostgreSQL `public.ip_intel_cache` UPSERT; Triage UI adds live enrich buttons in inspector and batch bar with color-coded score indicators.
2. `generate_gdocs_html_report` and `generate_tsv_table` in `app/exports.py` eliminate length truncation and inject inline CSS table borders for flawless copy-pasting into Google Docs/Sheets.
3. Brand SVG favicon added to `app/static/img/` and wired into `index.html` and FastAPI `/favicon.ico`.
4. `suggest_groups` in `app/core.py` enriched to aggregate rule names, severity, targets, source IPs, hit counts, and human-readable forensic reasons for Triage correlation cards.

**Tech Stack:** FastAPI (Python 3.11+), PostgreSQL 16 (`psycopg`), Vanilla JS ES Modules, Native CSS (`tokens.css`, `DESIGN.md`).

---

## Global Constraints

- Never use React, Vue, Tailwind, or external CDNs.
- Strictly adhere to `DESIGN.md` tokens and Quiet Evidence Desk palette.
- Do not read `.env`, live database, or real alert records.
- Run only isolated test suites (`test_parser`, `test_exports`, `test_privacy`, `test_dedup`, `test_ui_api`, `test_ui_safety`, and `tests/frontend/*.test.mjs`).

---

### Task 1: Favicon & Logo Arbiter
- [ ] Create `app/static/img/favicon.svg` with Arbiter scales/pillar mark and brand colors.
- [ ] Add `<link rel="icon">` in `app/index.html`.
- [ ] Add route `/favicon.ico` in `app/main.py`.
- [ ] Update `tests/serve_synthetic_ui.py` to handle favicon requests.

### Task 2: GDocs & TSV Export: Full Log & Clean Borders
- [ ] In `app/exports.py`:
  - `generate_gdocs_html_report`: remove `[:160]` truncation, output complete `full_log`, add inline `style="border: 1px solid #cbd5e0; ..."` and table attributes `border="1" cellspacing="0" cellpadding="8"`.
  - `generate_tsv_table`: remove `[:180]` truncation, clean newlines/tabs while keeping full log text intact.
- [ ] Update `tests/test_exports.py` with tests for untruncated logs and inline borders.

### Task 3: Rich Forensic Correlation Cards
- [ ] In `app/core.py`:
  - Update `suggest_groups(alerts)` to return `title`, `basis`, `rule_id`, `rule_level`, `description`, `agent_name`, `source_ips`, `alert_count`, and `reason`.
- [ ] In `app/static/js/features/triage/view.js` & `components.css`:
  - Render rich correlation cards displaying rule details, severity level badge, target host, source IPs, alert count, and forensic explanation.
- [ ] Update `tests/test_dedup.py` or create tests verifying suggestion metadata.

### Task 4: Two-Way IP Intel Live Enrichment
- [ ] In `app/intel.py`:
  - Implement IP validator, private network guard, AbuseIPDB client, and database UPSERT to `public.ip_intel_cache`.
- [ ] In `app/main.py`:
  - Add `POST /api/intel/enrich` endpoint accepting `ips` or `alert_ids`.
- [ ] In `app/static/js/features/triage/model.js` & `view.js`:
  - Update `intelSummary` to display score badges with severity colors.
  - Add "Live Enrich" button in inspector sidebar.
  - Add "Live Enrich IP" button in batch selection toolbar.
- [ ] Add tests for `/api/intel/enrich` in `tests/test_ui_api.py`.
- [ ] Verify frontend tests `tests/frontend/*.test.mjs` and backend test suites pass.
