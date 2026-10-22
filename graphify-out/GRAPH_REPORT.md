# Graph Report - Arbiter  (2026-10-22)

## Corpus Check
- 86 files · ~62,796 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 11 file(s) not represented in the graph (top: .woff2 4, (none) 3, .css 3)

## Summary
- 697 nodes · 1463 edges · 37 communities (27 shown, 10 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 26 edges (avg confidence: 0.88)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `a5a8fd7f`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- parser.py
- main.py
- test_ui_api.py
- esc
- state.js
- sanitize_text
- ApiIntegrationTests
- init-db.sql
- start.sh
- Arbiter — blueprint rombak UI/UX
- Arbiter — audit UI/UX dan keputusan redesign
- ⚡ Key Capabilities
- UIAPIContractTests
- AGENTS.md — Arbiter Project Context for AI Agents
- incidents-view.test.mjs
- imports/view.js
- reports/view.js
- app.js
- SafetyTests
- SyntheticDB
- database.py
- Arbiter
- exports.py
- 5. Halaman web, bagian demi bagian
- IPIntel — CyberSOC & Threat Intelligence Web
- Any
- 8. Daftar route
- 6. SOC Log Reader — bagian demi bagian
- MANUAL — Menjalankan IP Intel Web
- Struktur Proyek `ipintel/`
- post
- 4. Menjalankan aplikasi
- 7. Alur data
- 9. Database

## God Nodes (most connected - your core abstractions)
1. `esc()` - 38 edges
2. `mount()` - 31 edges
3. `json()` - 30 edges
4. `get_db()` - 26 edges
5. `mountWorkspace()` - 25 edges
6. `UIAPIContractTests` - 25 edges
7. `5. Halaman web, bagian demi bagian` - 24 edges
8. `mount()` - 22 edges
9. `icon()` - 22 edges
10. `errorState()` - 22 edges

## Surprising Connections (you probably didn't know these)
- `3. Peta route Flask (`app.py`)` --references--> `batch()`  [INFERRED]
  GUIDE_WIRA/STRUCTURE.md → app/static/js/features/triage/view.js
- `Key policies` --references--> `scopeParams()`  [INFERRED]
  AGENTS.md → app/static/js/state/scope.js
- `12. Graphify dan dokumentasi struktur` --references--> `parse_log_line()`  [INFERRED]
  GUIDE_WIRA/README.md → app/parser.py
- `12. Graphify dan dokumentasi struktur` --references--> `build_log_signature()`  [INFERRED]
  GUIDE_WIRA/README.md → app/parser.py
- `Keputusan Arsitektur Kunci` --references--> `selectedIds()`  [INFERRED]
  docs/ui-ux-redesign/README.md → app/static/js/features/incidents/model.js

## Import Cycles
- None detected.

## Communities (37 total, 10 thin omitted)

### Community 0 - "parser.py"
Cohesion: 0.09
Nodes (21): local_ai_suggest_groups(), LocalAIUnavailable, normalize_alert(), ollama_request(), suggest_groups(), suggestions_with_fallback(), as_dict(), build_log_signature() (+13 more)

### Community 1 - "main.py"
Cohesion: 0.16
Nodes (19): get_db(), init_database(), api_database_status(), delete_group(), get_alert_detail(), get_group_detail(), get_suggestions(), get_tenants() (+11 more)

### Community 3 - "esc"
Cohesion: 0.12
Nodes (59): apiURL(), json(), notify(), render(), summarizeTelemetryRange(), mount(), loadStatus(), render() (+51 more)

### Community 4 - "state.js"
Cohesion: 0.13
Nodes (19): cleanIds(), draftFrom(), draftsEqual(), evidenceParams(), incidentPayload(), incidentRoute(), selectedIds(), SEVERITIES (+11 more)

### Community 7 - "init-db.sql"
Cohesion: 0.33
Nodes (10): idx_wazuh_alerts_reviewed, idx_wazuh_alerts_rule_id, idx_wazuh_alerts_sig, idx_wazuh_alerts_source_ip, idx_wazuh_alerts_tenant, idx_wazuh_alerts_timestamp, public.ip_intel_cache, wazuh.alert_group_members (+2 more)

### Community 11 - "Arbiter — blueprint rombak UI/UX"
Cohesion: 0.07
Nodes (30): 10. Open decisions sebelum build, 1. Keputusan desain, 2. Sitemap yang diusulkan, 3. Apa yang boleh muncul di depan, 4. Wireframe dan first viewport, 5. Information architecture & interaction contracts, 6. Arsitektur module yang disarankan, 7. Kesiapan backend: pakai yang ada vs perlu kerja (+22 more)

### Community 12 - "Arbiter — audit UI/UX dan keputusan redesign"
Cohesion: 0.04
Nodes (40): Arbiter — audit UI/UX dan keputusan redesign, Bukti komposisi dan responsive, Detector Impeccable — hasil nyata, bukan daftar bug unik, Hallmark audit — subset yang sesuai operational app, Handoff, Metode dan batas bukti, Nielsen heuristics, Persona dan emotional journey (+32 more)

### Community 13 - "⚡ Key Capabilities"
Cohesion: 0.08
Nodes (23): 10. Official Deliverables (5 Export Paths), 1. Resilient Multi-Format Ingestion, 2. High-Precision Log Dissector (No False Fields), 3. Signature-Based Deduplication, 4. Enterprise Multi-Tenant Architecture, 5. Modular Four-Destination UI, 6. Review & Triage Workflow, 7. Incident Case Management (+15 more)

### Community 15 - "AGENTS.md — Arbiter Project Context for AI Agents"
Cohesion: 0.15
Nodes (12): AGENTS.md — Arbiter Project Context for AI Agents, Architecture (frontend), Design direction: Quiet Evidence Desk, Four destinations (not a monolithic page), Graph, Key policies, Privacy — STRICT, Running production (+4 more)

### Community 16 - "incidents-view.test.mjs"
Cohesion: 0.25
Nodes (3): context(), load(), SyntheticRoot

### Community 17 - "imports/view.js"
Cohesion: 0.13
Nodes (9): createImportSession(), importPage(), importResult(), mount(), update(), moduleURL, click(), Control (+1 more)

### Community 18 - "reports/view.js"
Cohesion: 0.06
Nodes (39): ApiError, copyHTML(), copyText(), download(), request(), caseReportRoute(), createReportSession(), exportURL() (+31 more)

### Community 19 - "app.js"
Cohesion: 0.08
Nodes (19): closeNav(), health(), help, main, navigationMemory, pageTitles, router, scrim (+11 more)

### Community 22 - "database.py"
Cohesion: 0.11
Nodes (15): get_active_profile(), get_database_status(), get_db_connection(), ingest_alert_with_dedup(), mask_connection_url(), purge_alerts(), purge_incidents(), set_active_profile() (+7 more)

### Community 23 - "Arbiter"
Cohesion: 0.33
Nodes (5): Arbiter, Audience and usage, Development verification, Implemented case policy without schema changes, Product boundaries

### Community 24 - "exports.py"
Cohesion: 0.09
Nodes (6): generate_docx_landscape_report(), generate_markdown_report(), generate_tsv_table(), generate_xlsx_workbook(), export_csv(), ExportTests

### Community 25 - "5. Halaman web, bagian demi bagian"
Cohesion: 0.08
Nodes (24): 5.10 MITRE ATT&CK — `GET /mitre`, 5.11 MISP Events — `GET /misp`, 5.12 Detail Event MISP — `GET /misp/event/<id>`, 5.13 Import MISP — `GET/POST /misp/import`, 5.14 Universal IoCs — `GET /iocs`, 5.15 Korelasi IOC — `GET /correlate?val=...`, 5.16 Threat Feeds — `GET /threat-feeds`, 5.17 Threat Actors / APT — `GET /actors` (+16 more)

### Community 27 - "IPIntel — CyberSOC & Threat Intelligence Web"
Cohesion: 0.20
Nodes (9): 10. Parser SOC dan aturan keamanan tampilan, 11. Konfigurasi dan keamanan, 12. Graphify dan dokumentasi struktur, 13. Troubleshooting, 14. Catatan operasional, 1. Ringkasan fungsi, 2. Arsitektur, 3. Struktur folder (+1 more)

### Community 28 - "Any"
Cohesion: 0.23
Nodes (10): generate_gdocs_html_report(), export_docx(), export_gdocs_html(), export_markdown(), export_preview(), export_scope(), export_tsv(), export_xlsx() (+2 more)

### Community 29 - "8. Daftar route"
Cohesion: 0.67
Nodes (3): 8.1 Halaman, 8.2 API utama, 8. Daftar route

### Community 30 - "6. SOC Log Reader — bagian demi bagian"
Cohesion: 0.22
Nodes (9): 6.1 Sumber data dan tampilan, 6.2 Filter, 6.3 Impor, 6.4 Signature dan dedup, 6.5 Hit, waktu, dan tampilan log, 6.6 Hapus data, 6.7 Export, 6.8 API SOC (+1 more)

### Community 31 - "MANUAL — Menjalankan IP Intel Web"
Cohesion: 0.25
Nodes (7): 1. Cara cepat (otomatis), 2. Cara manual (langkah per langkah), 3. Fitur web, 4. Utilitas CLI (`ipintel/`), 5. Troubleshooting, 6. File penting, MANUAL — Menjalankan IP Intel Web

### Community 32 - "Struktur Proyek `ipintel/`"
Cohesion: 0.29
Nodes (6): 1. Tree + ukuran file, 2. Graph dependensi modul (siapa import siapa), 3. Peta route Flask (`app.py`), 4. Alur data enrichment (DB-first), 5. Tabel database, Struktur Proyek `ipintel/`

### Community 33 - "post"
Cohesion: 0.24
Nodes (8): add_group_members(), api_sanitize_logs(), batch_update_review(), create_group(), import_file(), import_text(), _process_alerts_ingest(), _validate_membership()

### Community 34 - "4. Menjalankan aplikasi"
Cohesion: 0.50
Nodes (4): 4.1 Lewat Docker (cara yang dipakai sekarang), 4.2 Langsung dengan Python, 4.3 Health check, 4. Menjalankan aplikasi

### Community 35 - "7. Alur data"
Cohesion: 0.50
Nodes (4): 7.1 Enrichment IP, 7.2 Impor SOC, 7.3 MISP / CTI, 7. Alur data

### Community 36 - "9. Database"
Cohesion: 0.50
Nodes (4): 9.1 Tabel inti, 9.2 Tabel CTI, 9.3 Tabel SOC, 9. Database

## Knowledge Gaps
- **10 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `scopeParams()` connect `reports/view.js` to `esc`, `state.js`, `Arbiter — audit UI/UX dan keputusan redesign`, `AGENTS.md — Arbiter Project Context for AI Agents`?**
  _High betweenness centrality (0.087) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `json()` (e.g. with `mount()` and `loadSelected()`) actually correct?**
  _`json()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Should `parser.py` be split into smaller, more focused modules?**
  _Cohesion score 0.08686868686868687 - nodes in this community are weakly interconnected._
- **Why does `Keputusan Arsitektur Kunci` connect `Arbiter — audit UI/UX dan keputusan redesign` to `reports/view.js`, `state.js`?**
  _High betweenness centrality (0.077) - this node is a cross-community bridge._
- **Should `test_ui_api.py` be split into smaller, more focused modules?**
  _Cohesion score 0.11428571428571428 - nodes in this community are weakly interconnected._
- **Should `esc` be split into smaller, more focused modules?**
  _Cohesion score 0.11892583120204604 - nodes in this community are weakly interconnected._
- **Should `state.js` be split into smaller, more focused modules?**
  _Cohesion score 0.1349206349206349 - nodes in this community are weakly interconnected._