# Graph Report - Arbiter  (2026-10-28)

## Corpus Check
- 99 files · ~83,851 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 11 file(s) not represented in the graph (top: .woff2 4, (none) 3, .css 3)

## Summary
- 855 nodes · 1933 edges · 42 communities (32 shown, 10 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 58 edges (avg confidence: 0.91)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `4d4833ea`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- parser.py
- normalize_tenants
- test_ui_api.py
- incidents-view.test.mjs
- main.py
- Control
- ApiIntegrationTests
- init-db.sql
- start.sh
- Arbiter — blueprint rombak UI/UX
- Arbiter — audit UI/UX dan keputusan redesign
- ⚡ Key Capabilities
- UIAPIContractTests
- AGENTS.md — Arbiter Project Context for AI Agents
- Control
- incidents/render.js
- stats/view.js
- ref_node_assert
- SafetyTests
- SyntheticDB
- database.py
- Arbiter
- exports.py
- 5. Halaman web, bagian demi bagian
- enrich_intel
- IPIntel — CyberSOC & Threat Intelligence Web
- 📋 Protokol Eksekusi Rinci
- File Map and Interfaces
- 6. SOC Log Reader — bagian demi bagian
- MANUAL — Menjalankan IP Intel Web
- app.js
- Any
- 4. Menjalankan aplikasi
- 7. Alur data
- 9. Database
- Arbiter SOC Desk Upgrades Implementation Plan
- esc
- StatsEndpointContractTests
- Struktur Proyek `ipintel/`

## God Nodes (most connected - your core abstractions)
1. `esc()` - 49 edges
2. `json()` - 36 edges
3. `mount()` - 34 edges
4. `UIAPIContractTests` - 31 edges
5. `get_db()` - 30 edges
6. `icon()` - 27 edges
7. `mountWorkspace()` - 26 edges
8. `mount()` - 26 edges
9. `errorState()` - 26 edges
10. `StatsEndpointContractTests` - 25 edges

## Surprising Connections (you probably didn't know these)
- `3. Peta route Flask (`app.py`)` --references--> `batch()`  [INFERRED]
  GUIDE_WIRA/STRUCTURE.md → app/static/js/features/triage/view.js
- `Arbiter SOC Desk Upgrades Implementation Plan` --references--> `suggest_groups()`  [INFERRED]
  docs/superpowers/plans/2026-10-23-arbiter-enrichment-reports-favicon-correlation.md → app/core.py
- `Arbiter SOC Desk Upgrades Implementation Plan` --references--> `generate_tsv_table()`  [INFERRED]
  docs/superpowers/plans/2026-10-23-arbiter-enrichment-reports-favicon-correlation.md → app/exports.py
- `Task 2: GDocs & TSV Export: Full Log & Clean Borders` --references--> `generate_tsv_table()`  [INFERRED]
  docs/superpowers/plans/2026-10-23-arbiter-enrichment-reports-favicon-correlation.md → app/exports.py
- `Arbiter SOC Desk Upgrades Implementation Plan` --references--> `generate_gdocs_html_report()`  [INFERRED]
  docs/superpowers/plans/2026-10-23-arbiter-enrichment-reports-favicon-correlation.md → app/exports.py

## Import Cycles
- None detected.

## Communities (42 total, 10 thin omitted)

### Community 0 - "parser.py"
Cohesion: 0.06
Nodes (25): local_ai_suggest_groups(), LocalAIUnavailable, normalize_alert(), ollama_request(), suggest_groups(), suggestions_with_fallback(), as_dict(), build_log_signature() (+17 more)

### Community 1 - "normalize_tenants"
Cohesion: 0.27
Nodes (11): add_group_members(), delete_group(), remove_group_member(), _scoped_groups(), update_alert_review(), update_group(), _validate_membership(), normalize_tenants() (+3 more)

### Community 3 - "incidents-view.test.mjs"
Cohesion: 0.25
Nodes (3): context(), load(), SyntheticRoot

### Community 4 - "main.py"
Cohesion: 0.18
Nodes (16): get_db(), init_database(), api_database_status(), favicon(), get_alert_detail(), get_group_detail(), get_stats(), get_suggestions() (+8 more)

### Community 5 - "Control"
Cohesion: 0.22
Nodes (3): click(), Control, fixture()

### Community 7 - "init-db.sql"
Cohesion: 0.25
Nodes (14): idx_wazuh_alerts_agent_name, idx_wazuh_alerts_reviewed, idx_wazuh_alerts_rule_id, idx_wazuh_alerts_rule_level, idx_wazuh_alerts_sig, idx_wazuh_alerts_source_ip, idx_wazuh_alerts_status, idx_wazuh_alerts_tenant (+6 more)

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
Cohesion: 0.14
Nodes (13): AGENTS.md — Arbiter Project Context for AI Agents, Architecture (frontend), Design direction: Quiet Evidence Desk, Four destinations (not a monolithic page), Graph, Key policies, Privacy — STRICT, Running production (+5 more)

### Community 16 - "Control"
Cohesion: 0.22
Nodes (3): click(), Control, fixture()

### Community 17 - "incidents/render.js"
Cohesion: 0.10
Nodes (50): caseHref(), cleanIds(), draftFrom(), draftsEqual(), evidenceParams(), filterIncidents(), incidentPayload(), incidentRoute() (+42 more)

### Community 18 - "stats/view.js"
Cohesion: 0.11
Nodes (38): scopeParams(), BENIGN_WHITELIST_PATTERNS, CHART_OPTIONS, distributionPercentages(), generateMarkdownSummary(), generateStatsCSV(), INJECTION_PATTERNS, isMaliciousAlert() (+30 more)

### Community 19 - "ref_node_assert"
Cohesion: 0.10
Nodes (13): url, moduleURL, modelURL, load(), load(), url, url, url (+5 more)

### Community 22 - "database.py"
Cohesion: 0.08
Nodes (13): get_active_profile(), get_database_status(), get_db_connection(), mask_connection_url(), purge_alerts(), purge_incidents(), set_active_profile(), test_db_connection() (+5 more)

### Community 23 - "Arbiter"
Cohesion: 0.33
Nodes (5): Arbiter, Audience and usage, Development verification, Implemented case policy without schema changes, Product boundaries

### Community 24 - "exports.py"
Cohesion: 0.08
Nodes (15): generate_docx_landscape_report(), generate_gdocs_html_report(), generate_markdown_report(), generate_tsv_table(), generate_xlsx_workbook(), export_csv(), export_docx(), export_gdocs_html() (+7 more)

### Community 25 - "5. Halaman web, bagian demi bagian"
Cohesion: 0.08
Nodes (24): 5.10 MITRE ATT&CK — `GET /mitre`, 5.11 MISP Events — `GET /misp`, 5.12 Detail Event MISP — `GET /misp/event/<id>`, 5.13 Import MISP — `GET/POST /misp/import`, 5.14 Universal IoCs — `GET /iocs`, 5.15 Korelasi IOC — `GET /correlate?val=...`, 5.16 Threat Feeds — `GET /threat-feeds`, 5.17 Threat Actors / APT — `GET /actors` (+16 more)

### Community 26 - "enrich_intel"
Cohesion: 0.20
Nodes (6): sync_remote_cache(), upsert_ip_cache(), enrich_intel(), export_scope(), _scope_tenant_value(), positive_ids()

### Community 27 - "IPIntel — CyberSOC & Threat Intelligence Web"
Cohesion: 0.17
Nodes (11): 10. Parser SOC dan aturan keamanan tampilan, 11. Konfigurasi dan keamanan, 13. Troubleshooting, 14. Catatan operasional, 1. Ringkasan fungsi, 2. Arsitektur, 3. Struktur folder, 8.1 Halaman (+3 more)

### Community 28 - "📋 Protokol Eksekusi Rinci"
Cohesion: 0.13
Nodes (14): 1. Inisialisasi Task Otomatis (`todo_list`), 1. Mode Maksimal (`/work`) — Autonomous Deep Engineering Mode, 2. Mode Normal (Tanpa `/work`), 2. Proaktif Menggunakan Skills & Subagents, 3. Pelacakan Jahitan Data Ujung-ke-Ujung (*Trace Every Seam*), 4. Pengujian Kasus Negatif (Bukan Cuma Kasus Ideal), 5. Verifikasi Lingkungan & Container, 6. Anti-Pengerdilan Data (Zero Artificial Truncation) (+6 more)

### Community 29 - "File Map and Interfaces"
Cohesion: 0.22
Nodes (8): Alert Statistics & Pivot Implementation Plan, File Map and Interfaces, Global Constraints, Review Focus, Self-Review, Task 4: Add the compact Triage filter-summary strip, Task 5: Add approved post-core statistics enhancements, Task 6: Document the completed navigation and verification contract

### Community 30 - "6. SOC Log Reader — bagian demi bagian"
Cohesion: 0.22
Nodes (9): 6.1 Sumber data dan tampilan, 6.2 Filter, 6.3 Impor, 6.4 Signature dan dedup, 6.5 Hit, waktu, dan tampilan log, 6.6 Hapus data, 6.7 Export, 6.8 API SOC (+1 more)

### Community 31 - "MANUAL — Menjalankan IP Intel Web"
Cohesion: 0.25
Nodes (7): 1. Cara cepat (otomatis), 2. Cara manual (langkah per langkah), 3. Fitur web, 4. Utilitas CLI (`ipintel/`), 5. Troubleshooting, 6. File penting, MANUAL — Menjalankan IP Intel Web

### Community 32 - "app.js"
Cohesion: 0.10
Nodes (22): canLeave(), closeNav(), health(), help, main, navigationMemory, pageTitles, renderTenantOptions() (+14 more)

### Community 33 - "Any"
Cohesion: 0.20
Nodes (13): ingest_alert_with_dedup(), api_database_config(), api_database_purge_alerts(), api_database_purge_incidents(), api_database_switch(), api_database_test(), api_sanitize_logs(), batch_update_review() (+5 more)

### Community 34 - "4. Menjalankan aplikasi"
Cohesion: 0.50
Nodes (4): 4.1 Lewat Docker (cara yang dipakai sekarang), 4.2 Langsung dengan Python, 4.3 Health check, 4. Menjalankan aplikasi

### Community 35 - "7. Alur data"
Cohesion: 0.50
Nodes (4): 7.1 Enrichment IP, 7.2 Impor SOC, 7.3 MISP / CTI, 7. Alur data

### Community 36 - "9. Database"
Cohesion: 0.50
Nodes (4): 9.1 Tabel inti, 9.2 Tabel CTI, 9.3 Tabel SOC, 9. Database

### Community 37 - "Arbiter SOC Desk Upgrades Implementation Plan"
Cohesion: 0.29
Nodes (6): Arbiter SOC Desk Upgrades Implementation Plan, Global Constraints, Task 1: Favicon & Logo Arbiter, Task 2: GDocs & TSV Export: Full Log & Clean Borders, Task 3: Rich Forensic Correlation Cards, Task 4: Two-Way IP Intel Live Enrichment

### Community 38 - "esc"
Cohesion: 0.09
Nodes (64): ApiError, apiURL(), copyHTML(), copyText(), download(), json(), request(), notify() (+56 more)

### Community 40 - "Struktur Proyek `ipintel/`"
Cohesion: 0.29
Nodes (6): 1. Tree + ukuran file, 2. Graph dependensi modul (siapa import siapa), 3. Peta route Flask (`app.py`), 4. Alur data enrichment (DB-first), 5. Tabel database, Struktur Proyek `ipintel/`

## Knowledge Gaps
- **10 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Task 1: Establish precise shared multi-tenant scope and safe facet contract` connect `normalize_tenants` to `incidents/render.js`, `main.py`, `File Map and Interfaces`, `esc`?**
  _High betweenness centrality (0.232) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `json()` (e.g. with `mount()` and `loadSelected()`) actually correct?**
  _`json()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Should `parser.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05809979494190021 - nodes in this community are weakly interconnected._
- **Why does `Task 2: Build SQL aggregation endpoints and schema support` connect `SyntheticDB` to `test_ui_api.py`, `main.py`, `esc`, `incidents/render.js`, `File Map and Interfaces`?**
  _High betweenness centrality (0.170) - this node is a cross-community bridge._
- **Should `test_ui_api.py` be split into smaller, more focused modules?**
  _Cohesion score 0.12380952380952381 - nodes in this community are weakly interconnected._
- **Why does `selectedIds()` connect `incidents/render.js` to `Arbiter — audit UI/UX dan keputusan redesign`?**
  _High betweenness centrality (0.142) - this node is a cross-community bridge._
- **Should `Arbiter — blueprint rombak UI/UX` be split into smaller, more focused modules?**
  _Cohesion score 0.06666666666666667 - nodes in this community are weakly interconnected._