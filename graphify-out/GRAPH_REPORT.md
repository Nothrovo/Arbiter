# Graph Report - Arbiter  (2026-11-18)

## Corpus Check
- 157 files · ~135,498 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 15 file(s) not represented in the graph (top: .css 5, (none) 4, .woff2 4)

## Summary
- 1740 nodes · 4239 edges · 95 communities (75 shown, 20 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 134 edges (avg confidence: 0.9)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `dcb58ba2`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- core.py
- ref_node_assert
- test_ui_api.py
- stats/view.js
- scope.js
- imports/render.js
- ApiIntegrationTests
- loadingRows
- AITriageAPITests
- start.sh
- json
- Arbiter — blueprint rombak UI/UX
- Arbiter — audit UI/UX dan keputusan redesign
- ARSITEKTUR.md
- UIAPIContractTests
- AGENTS.md — Arbiter Project Context for AI Agents
- normalize_tenants
- icon
- Control
- incidents/render.js
- SafetyTests
- pull/view.js
- api_get_ai_triage
- Arbiter
- exports.py
- mount
- enrich_intel
- db
- 📋 Protokol Eksekusi Rinci
- File Map and Interfaces
- SettingsAPITests
- test_pull_jobs.py
- app.js
- main.py
- exclusions.py
- SyntheticDB
- wazuh_intel.py
- router.js
- mount
- StatsEndpointContractTests
- triage-request.test.mjs
- normalize_alert
- Arsitektur Arbiter — Web & Tools
- ai_triage.py
- DatabaseTrustTests
- Dokumentasi Arbiter
- Arbiter UI/UX Redesign — Quiet Evidence Desk
- DESIGN.md
- settings.json
- ui-ux-redesign/README.md
- init_database
- Layout
- database.py
- suggestions_with_fallback
- database-workspace.test.mjs
- intel.py
- Testing — Arbiter
- 5\. Cara Kerja
- sanitize_text
- esc
- ⚡ Key Capabilities
- Arbiter Architecture — Wazuh Read, Classify, Correlate
- _SyncConnection
- get_db
- package.json
- ExclusionAPITests
- build
- Deploy config reference
- Code Style — Arbiter
- Deploy Arbiter
- 8\. Instalasi
- stats-trust.test.mjs
- auth.py
- 6.4 Skema database
- fix-issue.md
- validate-bash.sh
- setup-ai-symlinks.sh
- 6\. Komponen yang Dipakai
- 7\. Keamanan
- _load_profile_overrides
- SyntheticRoot
- wazuh_search
- 6. Correlation policy
- 2\. Deskripsi Produk
- 5. Classification policy
- 3\. Workflow
- settings.py
- stats/model.js
- _http_error_reason
- json
- wazuh-queries/model.js
- json

## God Nodes (most connected - your core abstractions)
1. `esc()` - 91 edges
2. `json()` - 68 edges
3. `get_db()` - 63 edges
4. `icon()` - 60 edges
5. `AITriageAPITests` - 40 edges
6. `mount()` - 40 edges
7. `mount()` - 38 edges
8. `errorState()` - 36 edges
9. `UIAPIContractTests` - 33 edges
10. `mount()` - 32 edges

## Surprising Connections (you probably didn't know these)
- `5.8 Profil database dan pemeliharaan` --references--> `get_db()`  [INFERRED]
  docs/ARSITEKTUR.md → app/database.py
- `8.2 Metode A — Docker standalone (paling cepat)` --references--> `init_database()`  [INFERRED]
  docs/DOKUMENTASI.md → app/database.py
- `5.7 Alur ekspor` --references--> `export_scope()`  [INFERRED]
  docs/ARSITEKTUR.md → app/main.py
- `Key finding: Active Response is evidence, not a separate attack` --references--> `correlate_alerts()`  [INFERRED]
  docs/ARCHITECTURE.md → app/wazuh_intel.py
- `4.2 Normalized alert` --references--> `normalize_alert()`  [INFERRED]
  docs/ARCHITECTURE.md → app/core.py

## Import Cycles
- None detected.

## Communities (95 total, 20 thin omitted)

### Community 0 - "core.py"
Cohesion: 0.11
Nodes (13): build_log_signature(), extract_alerts(), first_ip_in(), kv_details(), normalize_log_for_signature(), parse_export(), parse_log_line(), parse_timestamp_iso() (+5 more)

### Community 1 - "ref_node_assert"
Cohesion: 0.11
Nodes (14): url, modelURL, mainPy, root, settingsView, triageView, url, url (+6 more)

### Community 3 - "stats/view.js"
Cohesion: 0.17
Nodes (26): distributionPercentages(), drilldownScrollBehavior(), generateMarkdownSummary(), generateStatsCSV(), isMaliciousAlert(), isMaliciousPath(), statsScopeParams(), triageRouteFromStats() (+18 more)

### Community 4 - "scope.js"
Cohesion: 0.14
Nodes (20): cleanIds(), draftFrom(), draftsEqual(), evidenceParams(), incidentPayload(), incidentRoute(), selectedIds(), SEVERITIES (+12 more)

### Community 5 - "imports/render.js"
Cohesion: 0.12
Nodes (9): createImportSession(), importPage(), importResult(), mount(), update(), moduleURL, click(), Control (+1 more)

### Community 7 - "loadingRows"
Cohesion: 0.14
Nodes (36): mount(), pull(), render(), saveRealtime(), schedule(), aiLabel(), clone(), DEFAULT_SETTINGS (+28 more)

### Community 8 - "AITriageAPITests"
Cohesion: 0.05
Nodes (3): suggest_groups(), AITriageAPITests, fake_search()

### Community 10 - "json"
Cohesion: 0.19
Nodes (21): ApiError, copyHTML(), copyText(), download(), request(), caseReportRoute(), createReportSession(), exportURL() (+13 more)

### Community 11 - "Arbiter — blueprint rombak UI/UX"
Cohesion: 0.07
Nodes (30): 10. Open decisions sebelum build, 1. Keputusan desain, 2. Sitemap yang diusulkan, 3. Apa yang boleh muncul di depan, 4. Wireframe dan first viewport, 5. Information architecture & interaction contracts, 6. Arsitektur module yang disarankan, 7. Kesiapan backend: pakai yang ada vs perlu kerja (+22 more)

### Community 12 - "Arbiter — audit UI/UX dan keputusan redesign"
Cohesion: 0.15
Nodes (13): Arbiter — audit UI/UX dan keputusan redesign, Bukti komposisi dan responsive, Detector Impeccable — hasil nyata, bukan daftar bug unik, Hallmark audit — subset yang sesuai operational app, Handoff, Metode dan batas bukti, Nielsen heuristics, Persona dan emotional journey (+5 more)

### Community 13 - "ARSITEKTUR.md"
Cohesion: 0.32
Nodes (4): Arbiter, **DOCUMENT CONTROL**, *Dokumentasi Teknis*, **VERSION HISTORY**

### Community 15 - "AGENTS.md — Arbiter Project Context for AI Agents"
Cohesion: 0.13
Nodes (14): AGENTS.md — Arbiter Project Context for AI Agents, Architecture (frontend), Design direction: Quiet Evidence Desk, Four destinations (not a monolithic page), Graph, Key policies, Privacy — STRICT, Repository layout (+6 more)

### Community 16 - "normalize_tenants"
Cohesion: 0.11
Nodes (18): Agent: code-reviewer, Agent: security-auditor, Tenant scoping, delete_group(), export_scope(), get_alert_detail(), get_group_detail(), remove_group_member() (+10 more)

### Community 17 - "icon"
Cohesion: 0.17
Nodes (22): apiURL(), databaseIdentity(), summarizeTelemetryRange(), mount(), loadStatus(), maintain(), render(), switchTo() (+14 more)

### Community 18 - "Control"
Cohesion: 0.22
Nodes (3): click(), Control, fixture()

### Community 19 - "incidents/render.js"
Cohesion: 0.20
Nodes (28): caseHref(), filterIncidents(), allOptions(), options(), renderEvidence(), renderList(), renderWorkspace(), routeLink() (+20 more)

### Community 21 - "pull/view.js"
Cohesion: 0.31
Nodes (12): formatDuration(), mount(), paint(), paintProgress(), poll(), pollLater(), resumeJob(), stopPolling() (+4 more)

### Community 22 - "api_get_ai_triage"
Cohesion: 0.16
Nodes (16): get_triage_state_key(), safe_alerts(), with_exclusions(), api_ai_triage(), api_get_ai_triage(), _build_ai_triage_where(), _exclusion_document(), _find_matching_open_ai_group() (+8 more)

### Community 23 - "Arbiter"
Cohesion: 0.33
Nodes (5): Arbiter, Audience and usage, Development verification, Implemented case policy without schema changes, Product boundaries

### Community 24 - "exports.py"
Cohesion: 0.07
Nodes (19): generate_docx_landscape_report(), generate_gdocs_html_report(), generate_markdown_report(), generate_tsv_table(), generate_xlsx_workbook(), export_csv(), export_docx(), export_gdocs_html() (+11 more)

### Community 25 - "mount"
Cohesion: 0.18
Nodes (32): aiSeverityKey(), alertFacts(), alertIndex(), boundedInteger(), formatWibWindowLabel(), GROUP_BY_OPTIONS, groupAlerts(), LIMITS (+24 more)

### Community 26 - "enrich_intel"
Cohesion: 0.33
Nodes (4): is_valid_ip(), sync_remote_cache(), upsert_ip_cache(), enrich_intel()

### Community 27 - "db"
Cohesion: 0.06
Nodes (35): build, container_name, environment, network_mode, restart, volumes, context, dockerfile (+27 more)

### Community 28 - "📋 Protokol Eksekusi Rinci"
Cohesion: 0.13
Nodes (14): 1. Inisialisasi Task Otomatis (`todo_list`), 1. Mode Maksimal (`/work`) — Autonomous Deep Engineering Mode, 2. Mode Normal (Tanpa `/work`), 2. Proaktif Menggunakan Skills & Subagents, 3. Pelacakan Jahitan Data Ujung-ke-Ujung (*Trace Every Seam*), 4. Pengujian Kasus Negatif (Bukan Cuma Kasus Ideal), 5. Verifikasi Lingkungan & Container, 6. Anti-Pengerdilan Data (Zero Artificial Truncation) (+6 more)

### Community 29 - "File Map and Interfaces"
Cohesion: 0.22
Nodes (8): Alert Statistics & Pivot Implementation Plan, File Map and Interfaces, Global Constraints, Review Focus, Self-Review, Task 4: Add the compact Triage filter-summary strip, Task 5: Add approved post-core statistics enhancements, Task 6: Document the completed navigation and verification contract

### Community 31 - "test_pull_jobs.py"
Cohesion: 0.11
Nodes (7): base_config(), fake_get_db(), FakeConnection, FakeTransaction, load_pull_jobs(), PullJobTests, wait_for()

### Community 32 - "app.js"
Cohesion: 0.06
Nodes (31): adminOnlyPages, applyWorkspaceSettings(), canLeave(), checkPullActivity(), closeNav(), help, main, navigationMemory (+23 more)

### Community 33 - "main.py"
Cohesion: 0.10
Nodes (31): list_users(), api_alert_pull_cancel(), api_alert_pull_status(), api_auth_me(), api_create_user(), api_database_status(), api_delete_user(), api_delete_wazuh_query() (+23 more)

### Community 34 - "exclusions.py"
Cohesion: 0.17
Nodes (10): active_exclusion_rules(), build_exclusion_sql(), _coerce_enabled(), _escape_like(), glob_to_like(), normalize_exclusion_rule(), normalize_exclusions(), parse_wazuh_exclusion() (+2 more)

### Community 35 - "SyntheticDB"
Cohesion: 0.13
Nodes (3): Task 2: Build SQL aggregation endpoints and schema support, TriageScopeTests, SyntheticDB

### Community 36 - "wazuh_intel.py"
Cohesion: 0.16
Nodes (21): as_dict(), clean_val(), _alert_key(), _as_json(), build_attack_chains(), _bump(), _chain_steps(), classify_alert() (+13 more)

### Community 37 - "router.js"
Cohesion: 0.23
Nodes (4): createRouter(), change(), parseRoute(), root

### Community 38 - "mount"
Cohesion: 0.13
Nodes (29): intelBadge(), intelSummary(), renderQueue(), renderTriageSummary(), summaryRequestParams(), chainLine(), classificationBlock(), exclusionValuesFor() (+21 more)

### Community 40 - "triage-request.test.mjs"
Cohesion: 0.31
Nodes (3): createSelection(), Element, requestsFor()

### Community 41 - "normalize_alert"
Cohesion: 0.15
Nodes (6): normalize_alert(), extract_active_response(), _active_response(), ActiveResponseReadTests, CorrelationTests, NormalizeIntegrationTests

### Community 42 - "Arsitektur Arbiter — Web & Tools"
Cohesion: 0.05
Nodes (43): 10. Failure Modes dan Degradasi, 11. Keputusan Arsitektur dan Trade-off, 12. Batas Skalabilitas, 13. Peta Direktori Arsitektural, 14. Cara Memverifikasi Arsitektur, 15. Ringkasan Arsitektur, 1. Gaya Arsitektur, 2. Diagram Konteks (C4 Level 1) (+35 more)

### Community 43 - "ai_triage.py"
Cohesion: 0.09
Nodes (20): Backend (safe isolated suites), ai_triage(), _alert_tenant(), _cluster_alerts(), _cluster_prompt(), current_wib_window_key(), format_wib_window_label(), _group_by_rule_description() (+12 more)

### Community 45 - "Dokumentasi Arbiter"
Cohesion: 0.22
Nodes (9): 10\. Pengembangan dan Pemeliharaan, 11\. Lisensi, 1\. Ringkasan, 4.1 Alur end-to-end, 4.2 Pemisahan peran event, 4.3 Batas kepercayaan (trust boundary), 4\. Flowchart, 9\. Troubleshooting (+1 more)

### Community 46 - "Arbiter UI/UX Redesign — Quiet Evidence Desk"
Cohesion: 0.18
Nodes (11): Arbiter UI/UX Redesign — Quiet Evidence Desk, Arsitektur yang Terpasang, Audit (sebelum), Batas dan Catatan, Deliverable Desain, Evidence, Implementasi (sesudah), Keputusan Arsitektur Kunci (+3 more)

### Community 47 - "DESIGN.md"
Cohesion: 0.25
Nodes (7): Colors, Components, Do's and Don'ts, Elevation & Depth, Overview, Shapes, Typography

### Community 48 - "settings.json"
Cohesion: 0.12
Nodes (16): deny, note, model, coding, preferred, allow, note, permissions (+8 more)

### Community 49 - "ui-ux-redesign/README.md"
Cohesion: 0.29
Nodes (3): Approved implementation contract — Arbiter, Direction contract, Integration boundary

### Community 52 - "Layout"
Cohesion: 0.29
Nodes (7): Global shell, Impor dan Laporan, Insiden, Klasifikasi & korelasi, Layout, Responsive, Triage

### Community 54 - "database.py"
Cohesion: 0.08
Nodes (31): _batch_insert_values(), _batch_instance(), check_profile_ready(), _clean_expired_previews_locked(), create_preview_token(), get_active_profile(), get_active_profile_id(), get_database_status() (+23 more)

### Community 56 - "database-workspace.test.mjs"
Cohesion: 0.23
Nodes (12): loadBatchIncidentOptions(), updateQuery(), withParams(), createNavigationMemory(), normalizeSidebarState(), readSidebarState(), SIDEBAR_KEY, toggleSidebarState() (+4 more)

### Community 57 - "intel.py"
Cohesion: 0.07
Nodes (14): enrich_ip(), is_private_ip(), _json_object(), lookup_remote_ip_cache(), lookup_remote_ip_cache_detail(), query_abuseipdb(), _remote_profile_read_only(), _resolve_remote_db_url() (+6 more)

### Community 58 - "Testing — Arbiter"
Cohesion: 0.50
Nodes (3): Design lint, Frontend, Testing — Arbiter

### Community 59 - "5\. Cara Kerja"
Cohesion: 0.20
Nodes (10): 5.1 Ingesti dan parsing, 5.2 Normalisasi, 5.3 Deduplikasi, 5.4 Klasifikasi, 5.5 Korelasi, 5.6 AI Triage lokal, 5.7 Triage dan insiden, 5.8 Threat intelligence dan redaksi (+2 more)

### Community 62 - "esc"
Cohesion: 0.21
Nodes (13): /review — Code review pass, notify(), renderControls(), tenantOptionsHTML(), ERROR_CODE_CATEGORIES, ERROR_CODE_SECTIONS, ERROR_CODES, filterErrorCodeSections() (+5 more)

### Community 63 - "⚡ Key Capabilities"
Cohesion: 0.07
Nodes (28): 10. Privacy-First Redactor, 11. Official Deliverables (5 Export Paths), 1. Resilient Multi-Format Ingestion, 2. High-Precision Log Dissector (No False Fields), 3. Signature-Based Deduplication & Causal Correlation, 4. Enterprise Multi-Tenant Architecture, 5. Modular Destination UI, 6. Local AI Triage & Persistent Daily Case Grouping (`#/ai-triage`) (+20 more)

### Community 64 - "Arbiter Architecture — Wazuh Read, Classify, Correlate"
Cohesion: 0.13
Nodes (15): 10. Acceptance tests, 11. Non-goals, 1. Design constraints, 2. Dataset evidence used to shape the architecture, 3. End-to-end pipeline, 4.1 Raw Wazuh alert (minimum), 4.2 Normalized alert, 4.3 Classification result (+7 more)

### Community 65 - "_SyncConnection"
Cohesion: 0.12
Nodes (3): _FakeCursor, RemoteSyncTests, _SyncConnection

### Community 66 - "get_db"
Cohesion: 0.11
Nodes (31): get_db(), add_group_members(), api_add_exclusion(), api_ai_test(), api_ai_triage_save(), api_auth_login(), api_auth_logout(), api_database_config() (+23 more)

### Community 67 - "package.json"
Cohesion: 0.20
Nodes (9): description, engines, node, name, private, scripts, test, type (+1 more)

### Community 69 - "build"
Cohesion: 0.29
Nodes (6): build, volumes, context, dockerfile, services, arbiter

### Community 70 - "Deploy config reference"
Cohesion: 0.33
Nodes (5): Containers, Deploy config reference, Environment variables, Reverse proxy (optional), Secrets

### Community 72 - "Code Style — Arbiter"
Cohesion: 0.40
Nodes (4): Code Style — Arbiter, CSS, Frontend (JS), Python

### Community 73 - "Deploy Arbiter"
Cohesion: 0.40
Nodes (4): Deploy Arbiter, Local dev, Pre-deploy checks, Production (Docker Compose)

### Community 74 - "8\. Instalasi"
Cohesion: 0.20
Nodes (10): 8.1 Prasyarat, 8.2 Metode A — Docker standalone (paling cepat), 8.3 Metode B — Host mode (PostgreSQL yang sudah ada), 8.4 Metode C — Python lokal tanpa Docker, 8.5 Konfigurasi Wazuh Indexer (opsional, untuk Realtime), 8.6 Konfigurasi AI lokal (opsional), 8.7 Login pertama, 8.8 Verifikasi instalasi (+2 more)

### Community 75 - "stats-trust.test.mjs"
Cohesion: 0.28
Nodes (4): flush(), harness(), startSample(), stats()

### Community 76 - "auth.py"
Cohesion: 0.16
Nodes (20): authenticate_user(), create_session_token(), create_user(), _default_admin_credentials(), delete_user(), get_user(), _hash_password(), _load_raw_users() (+12 more)

### Community 77 - "6.4 Skema database"
Cohesion: 0.25
Nodes (8): 6.4.1 `wazuh.alerts`, 6.4.2 `wazuh.analysis_groups`, 6.4.3 `wazuh.alert_group_members`, 6.4.5 `public.ip_intel_cache`, 6.4.6 Tabel Remote milik provider, 6.4.7 Indeks performa, 6.4.8 Catatan operasional, 6.4 Skema database

### Community 85 - "6\. Komponen yang Dipakai"
Cohesion: 0.40
Nodes (5): 6.1 Stack, 6.2 Modul backend, 6.3 Modul frontend, 6.5 Kelompok endpoint API, 6\. Komponen yang Dipakai

### Community 87 - "7\. Keamanan"
Cohesion: 0.29
Nodes (7): 7.1 Prinsip desain, 7.2 Autentikasi dan otorisasi, 7.3 Rahasia saat istirahat, 7.4 Isolasi jaringan dan SSRF, 7.5 Perlindungan data dan ekspor, 7.6 Batasan keamanan yang perlu diketahui, 7\. Keamanan

### Community 91 - "SyntheticRoot"
Cohesion: 0.22
Nodes (3): context(), load(), SyntheticRoot

### Community 92 - "wazuh_search"
Cohesion: 0.15
Nodes (8): API Conventions — Arbiter, Credential redaction, Errors, wazuh_password(), wazuh_search(), _fmt(), main(), _existing()

### Community 93 - "6. Correlation policy"
Cohesion: 0.40
Nodes (5): 6.1 Response linkage, 6.2 Canonical group identity, 6.3 Ordered chain, 6.4 Correlation confidence, 6. Correlation policy

### Community 94 - "2\. Deskripsi Produk"
Cohesion: 0.40
Nodes (5): 2.1 Untuk siapa, 2.2 Batas produk, 2.3 Destinasi aplikasi, 2.4 Kemampuan inti, 2\. Deskripsi Produk

### Community 95 - "5. Classification policy"
Cohesion: 0.50
Nodes (4): 5.1 Curated rule profiles (explicit, not trained), 5.2 Context signals, 5.3 Wording policy, 5. Classification policy

### Community 96 - "3\. Workflow"
Cohesion: 0.50
Nodes (4): 3.1 Workflow analis (harian), 3.2 Workflow data, 3.3 Siklus hidup insiden, 3\. Workflow

### Community 99 - "settings.py"
Cohesion: 0.16
Nodes (11): _boolean(), _deep_merge(), default_settings(), intel_abuseipdb_key(), migrate_settings(), save_settings(), test_wazuh_connection(), _text() (+3 more)

### Community 100 - "stats/model.js"
Cohesion: 0.16
Nodes (19): scopeParams(), BENIGN_WHITELIST_PATTERNS, CHART_OPTIONS, INJECTION_PATTERNS, MALICIOUS_PATTERNS, METRIC_OPTIONS, normalizeStatsQuery(), PIVOT_OPTIONS (+11 more)

### Community 103 - "json"
Cohesion: 0.13
Nodes (6): api_realtime_pull(), _http_error_reason(), _normalize_wazuh_timestamp(), _valid_timestamp(), wazuh_count(), _wazuh_request()

### Community 104 - "wazuh-queries/model.js"
Cohesion: 0.33
Nodes (6): buildWazuhQueries(), parseSeverityBounds(), PRESET_CATEGORIES, PRESET_WAZUH_QUERIES, QUERY_SEVERITY_OPTIONS, QUERY_TIME_OPTIONS

### Community 105 - "json"
Cohesion: 0.22
Nodes (14): json(), applyUserPermissions(), databaseChanged(), health(), loadWorkspaceSettings(), render(), renderLoginGate(), renderTenantOptions() (+6 more)

## Knowledge Gaps
- **20 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `esc()` connect `esc` to `app.js`, `stats/view.js`, `imports/render.js`, `mount`, `loadingRows`, `Code Style — Arbiter`, `json`, `json`, `Arsitektur Arbiter — Web & Tools`, `normalize_tenants`, `icon`, `incidents/render.js`, `pull/view.js`, `6\. Komponen yang Dipakai`, `database-workspace.test.mjs`, `mount`?**
  _High betweenness centrality (0.230) - this node is a cross-community bridge._
- **Are the 6 inferred relationships involving `esc()` (e.g. with `Agent: code-reviewer` and `/review — Code review pass`) actually correct?**
  _`esc()` has 6 INFERRED edges - model-reasoned connections that need verification._
- **Should `core.py` be split into smaller, more focused modules?**
  _Cohesion score 0.1106612685560054 - nodes in this community are weakly interconnected._
- **Why does `Arsitektur Arbiter — Web & Tools` connect `Arsitektur Arbiter — Web & Tools` to `ARSITEKTUR.md`?**
  _High betweenness centrality (0.112) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `json()` (e.g. with `mount()` and `loadSelected()`) actually correct?**
  _`json()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Should `ref_node_assert` be split into smaller, more focused modules?**
  _Cohesion score 0.11264367816091954 - nodes in this community are weakly interconnected._
- **Why does `safe_alerts()` connect `api_get_ai_triage` to `Arbiter Architecture — Wazuh Read, Classify, Correlate`, `main.py`, `Arsitektur Arbiter — Web & Tools`, `ai_triage.py`, `7\. Keamanan`, `5\. Cara Kerja`?**
  _High betweenness centrality (0.108) - this node is a cross-community bridge._