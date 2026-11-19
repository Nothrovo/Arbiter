# Graph Report - Arbiter  (2026-11-19)

## Corpus Check
- 170 files · ~159,551 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 15 file(s) not represented in the graph (top: .css 5, (none) 4, .woff2 4)

## Summary
- 1964 nodes · 5046 edges · 113 communities (95 shown, 18 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 143 edges (avg confidence: 0.9)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `34245eb1`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- core.py
- ref_node_assert
- test_ui_api.py
- stats/view.js
- SyntheticRoot
- loadingRows
- ApiIntegrationTests
- loadingRows
- AITriageAPITests
- start.sh
- test_settings.py
- Arbiter — blueprint rombak UI/UX
- Arbiter — audit UI/UX dan keputusan redesign
- ARSITEKTUR.md
- UIAPIContractTests
- AGENTS.md — Arbiter Project Context for AI Agents
- Any
- triage/view.js
- lookup_remote_ip_cache_detail
- alert_where
- SafetyTests
- errorState
- api_get_ai_triage
- Arbiter
- exports.py
- mount
- re
- db
- 📋 Protokol Eksekusi Rinci
- File Map and Interfaces
- SettingsAPITests
- test_pull_jobs.py
- app.js
- esc
- exclusions.py
- SyntheticDB
- database-workspace.test.mjs
- main.py
- reports/view.js
- FlagWorkspaceTests
- tenantValues
- get_db
- Arsitektur Arbiter — Web & Tools
- ai_triage.py
- DatabaseTrustTests
- Dokumentasi Arbiter
- Arbiter UI/UX Redesign — Quiet Evidence Desk
- DESIGN.md
- settings.json
- ui-ux-redesign/README.md
- query.py
- StatsEndpointContractTests
- Layout
- Control
- database.py
- test_ollama
- 6. Correlation policy
- Control
- wazuh_intel.py
- 5\. Cara Kerja
- sanitize_text
- render
- router.js
- ⚡ Key Capabilities
- Arbiter Architecture — Wazuh Read, Classify, Correlate
- intel.py
- state.js
- package.json
- ExclusionAPITests
- build
- Deploy config reference
- 5. Arsitektur Tools (Backend)
- Code Style — Arbiter
- Deploy Arbiter
- 8\. Instalasi
- test_wazuh_intel.py
- secure_store.py
- 6.4 Skema database
- 4. Arsitektur Web (Frontend)
- 8. Roadmap implementasi, tiap tahap bisa diverifikasi
- fix-issue.md
- validate-bash.sh
- setup-ai-symlinks.sh
- 8. Deployment
- Arbiter
- 4. Wireframe dan first viewport
- 7\. Keamanan
- diagnose_realtime_pull.py
- _SyncConnection
- json
- triage-request.test.mjs
- load_settings
- get_db
- pull_jobs.py
- normalize_tenants
- scope.js
- 5. Information architecture & interaction contracts
- settings.py
- withParams
- 🚀 Setup & Getting Started
- 6. Arsitektur Data
- 2\. Deskripsi Produk
- 6\. Komponen yang Dipakai
- stats-trust.test.mjs
- imports/view.js
- 4. Data contracts
- 7. Arsitektur Keamanan
- 3\. Workflow
- feature-loader.test.mjs

## God Nodes (most connected - your core abstractions)
1. `esc()` - 102 edges
2. `json()` - 83 edges
3. `get_db()` - 79 edges
4. `icon()` - 72 edges
5. `mount()` - 53 edges
6. `mount()` - 52 edges
7. `AITriageAPITests` - 47 edges
8. `errorState()` - 42 edges
9. `UIAPIContractTests` - 37 edges
10. `mount()` - 35 edges

## Surprising Connections (you probably didn't know these)
- `5.7 Alur ekspor` --references--> `export_scope()`  [INFERRED]
  docs/ARSITEKTUR.md → app/main.py
- `5.6 AI Triage lokal` --references--> `safe_alerts()`  [INFERRED]
  docs/DOKUMENTASI.md → app/ai_triage.py
- `7.5 Perlindungan data dan ekspor` --references--> `safe_alerts()`  [INFERRED]
  docs/DOKUMENTASI.md → app/ai_triage.py
- `4.2 Normalized alert` --references--> `normalize_alert()`  [INFERRED]
  docs/ARCHITECTURE.md → app/core.py
- `6.3 Ordered chain` --references--> `build_attack_chains()`  [INFERRED]
  docs/ARCHITECTURE.md → app/wazuh_intel.py

## Import Cycles
- None detected.

## Communities (113 total, 18 thin omitted)

### Community 0 - "core.py"
Cohesion: 0.16
Nodes (4): local_ai_suggest_groups(), LocalAIUnavailable, suggest_groups(), suggestions_with_fallback()

### Community 1 - "ref_node_assert"
Cohesion: 0.07
Nodes (20): url, harness(), profiles, harness(), status, moduleURL, modelURL, mainPy (+12 more)

### Community 2 - "test_ui_api.py"
Cohesion: 0.10
Nodes (3): load_database(), SchemaMigrationOrderTests, load_isolated_api()

### Community 3 - "stats/view.js"
Cohesion: 0.13
Nodes (35): BENIGN_WHITELIST_PATTERNS, CHART_OPTIONS, distributionPercentages(), drilldownScrollBehavior(), generateMarkdownSummary(), generateStatsCSV(), INJECTION_PATTERNS, isMaliciousAlert() (+27 more)

### Community 4 - "SyntheticRoot"
Cohesion: 0.22
Nodes (3): context(), load(), SyntheticRoot

### Community 5 - "loadingRows"
Cohesion: 0.20
Nodes (27): caseHref(), filterIncidents(), allOptions(), options(), renderEvidence(), renderList(), renderWorkspace(), routeLink() (+19 more)

### Community 7 - "loadingRows"
Cohesion: 0.08
Nodes (56): ERROR_CODE_CATEGORIES, ERROR_CODE_SECTIONS, ERROR_CODES, filterErrorCodeSections(), mount(), render(), renderSections(), sectionBadge() (+48 more)

### Community 10 - "test_settings.py"
Cohesion: 0.15
Nodes (3): _normalize_wazuh_timestamp(), _valid_timestamp(), wazuh_count()

### Community 11 - "Arbiter — blueprint rombak UI/UX"
Cohesion: 0.17
Nodes (12): 10. Open decisions sebelum build, 1. Keputusan desain, 2. Sitemap yang diusulkan, 3. Apa yang boleh muncul di depan, 6. Arsitektur module yang disarankan, 7. Kesiapan backend: pakai yang ada vs perlu kerja, 9. Acceptance checklist, Alternatif yang dibandingkan (+4 more)

### Community 12 - "Arbiter — audit UI/UX dan keputusan redesign"
Cohesion: 0.15
Nodes (13): Arbiter — audit UI/UX dan keputusan redesign, Bukti komposisi dan responsive, Detector Impeccable — hasil nyata, bukan daftar bug unik, Hallmark audit — subset yang sesuai operational app, Handoff, Metode dan batas bukti, Nielsen heuristics, Persona dan emotional journey (+5 more)

### Community 13 - "ARSITEKTUR.md"
Cohesion: 0.32
Nodes (4): Arbiter, **DOCUMENT CONTROL**, *Dokumentasi Teknis*, **VERSION HISTORY**

### Community 15 - "AGENTS.md — Arbiter Project Context for AI Agents"
Cohesion: 0.13
Nodes (14): AGENTS.md — Arbiter Project Context for AI Agents, Architecture (frontend), Design direction: Quiet Evidence Desk, Four destinations (not a monolithic page), Graph, Key policies, Privacy — STRICT, Repository layout (+6 more)

### Community 16 - "Any"
Cohesion: 0.15
Nodes (26): bump_daily_metrics(), api_create_report_audit_log(), api_flag_alerts(), api_flag_single_alert(), api_flags_rule_status(), _apply_flag_update(), batch_update_review(), bulk_verdict_by_pattern() (+18 more)

### Community 17 - "triage/view.js"
Cohesion: 0.17
Nodes (17): intelBadge(), intelSummary(), renderQueue(), renderTriageSummary(), summaryRequestParams(), chainLine(), exclusionValuesFor(), correlation() (+9 more)

### Community 18 - "lookup_remote_ip_cache_detail"
Cohesion: 0.12
Nodes (6): lookup_remote_ip_cache_detail(), _safe_remote_cache_error(), _FakeConnection, _FakeResult, _psycopg_modules(), RemoteCacheLookupTests

### Community 19 - "alert_where"
Cohesion: 0.11
Nodes (15): Agent: code-reviewer, Agent: security-auditor, with_exclusions(), _build_ai_triage_where(), _exclusion_document(), get_facet_alert_ids(), get_stats(), get_suggestions() (+7 more)

### Community 21 - "errorState"
Cohesion: 0.39
Nodes (8): databaseIdentity(), summarizeTelemetryRange(), mount(), loadStatus(), maintain(), render(), switchTo(), errorState()

### Community 22 - "api_get_ai_triage"
Cohesion: 0.08
Nodes (25): current_wib_window_key(), get_triage_state_key(), safe_alerts(), _ai_triage_batch_size(), _ai_triage_candidate_count(), _ai_triage_exclude_ids(), _ai_triage_pick_state(), _ai_triage_progress() (+17 more)

### Community 23 - "Arbiter"
Cohesion: 0.33
Nodes (5): Arbiter, Audience and usage, Development verification, Implemented case policy without schema changes, Product boundaries

### Community 24 - "exports.py"
Cohesion: 0.08
Nodes (12): generate_docx_landscape_report(), generate_gdocs_html_report(), generate_markdown_report(), generate_tsv_table(), generate_xlsx_workbook(), Arbiter SOC Desk Upgrades Implementation Plan, Global Constraints, Task 1: Favicon & Logo Arbiter (+4 more)

### Community 25 - "mount"
Cohesion: 0.09
Nodes (56): aiSeverityKey(), alertFacts(), alertIndex(), boundedInteger(), DEFAULT_BATCH, formatWibWindowLabel(), GROUP_BY_OPTIONS, groupAlerts() (+48 more)

### Community 26 - "re"
Cohesion: 0.12
Nodes (14): normalize_alert(), build_log_signature(), extract_alerts(), first_ip_in(), kv_details(), normalize_log_for_signature(), parse_export(), parse_log_line() (+6 more)

### Community 27 - "db"
Cohesion: 0.06
Nodes (35): build, container_name, environment, network_mode, restart, volumes, context, dockerfile (+27 more)

### Community 28 - "📋 Protokol Eksekusi Rinci"
Cohesion: 0.13
Nodes (14): 1. Inisialisasi Task Otomatis (`todo_list`), 1. Mode Maksimal (`/work`) — Autonomous Deep Engineering Mode, 2. Mode Normal (Tanpa `/work`), 2. Proaktif Menggunakan Skills & Subagents, 3. Pelacakan Jahitan Data Ujung-ke-Ujung (*Trace Every Seam*), 4. Pengujian Kasus Negatif (Bukan Cuma Kasus Ideal), 5. Verifikasi Lingkungan & Container, 6. Anti-Pengerdilan Data (Zero Artificial Truncation) (+6 more)

### Community 29 - "File Map and Interfaces"
Cohesion: 0.22
Nodes (8): Alert Statistics & Pivot Implementation Plan, File Map and Interfaces, Global Constraints, Review Focus, Self-Review, Task 4: Add the compact Triage filter-summary strip, Task 5: Add approved post-core statistics enhancements, Task 6: Document the completed navigation and verification contract

### Community 30 - "SettingsAPITests"
Cohesion: 0.05
Nodes (3): SettingsAPITests, __init__(), __init__()

### Community 31 - "test_pull_jobs.py"
Cohesion: 0.11
Nodes (7): base_config(), fake_get_db(), FakeConnection, FakeTransaction, load_pull_jobs(), PullJobTests, wait_for()

### Community 32 - "app.js"
Cohesion: 0.07
Nodes (31): adminOnlyPages, applyWorkspaceSettings(), checkPullActivity(), closeNav(), health(), help, loadWorkspaceSettings(), main (+23 more)

### Community 33 - "esc"
Cohesion: 0.16
Nodes (23): /review — Code review pass, notify(), renderControls(), tenantOptionsHTML(), importPage(), PRESET_LABELS, PRESET_MS, STATUS_LABELS (+15 more)

### Community 34 - "exclusions.py"
Cohesion: 0.15
Nodes (11): active_exclusion_rules(), build_exclusion_sql(), _coerce_enabled(), _escape_like(), glob_to_like(), normalize_exclusion_rule(), normalize_exclusions(), parse_wazuh_exclusion() (+3 more)

### Community 35 - "SyntheticDB"
Cohesion: 0.18
Nodes (3): Task 2: Build SQL aggregation endpoints and schema support, TriageScopeTests, SyntheticDB

### Community 36 - "database-workspace.test.mjs"
Cohesion: 0.22
Nodes (11): createNavigationMemory(), paramsForScope(), scopeKey(), normalizeSidebarState(), readSidebarState(), SIDEBAR_KEY, toggleSidebarState(), writeSidebarState() (+3 more)

### Community 37 - "main.py"
Cohesion: 0.08
Nodes (22): check_profile_ready(), ingest_alert_with_dedup(), is_valid_ip(), api_ai_test(), api_ai_triage_save(), api_alert_pull_cancel(), api_auth_login(), api_auth_logout() (+14 more)

### Community 38 - "reports/view.js"
Cohesion: 0.20
Nodes (19): ApiError, copyHTML(), download(), request(), caseReportRoute(), createReportSession(), exportURL(), reportAction() (+11 more)

### Community 40 - "tenantValues"
Cohesion: 0.17
Nodes (25): FLAG_GROUP_BY_OPTIONS, FLAG_META_MAP, FLAG_TABS, flagBadge(), flagMeta(), flagScopeParams(), GROUP_KEYS, normalizeFlagQuery() (+17 more)

### Community 41 - "get_db"
Cohesion: 0.11
Nodes (16): api_alert_pull_status(), api_database_status(), api_get_monitoring(), api_list_alert_pulls(), _expire_stale_claims(), favicon(), get_alert_detail(), get_tenants() (+8 more)

### Community 42 - "Arsitektur Arbiter — Web & Tools"
Cohesion: 0.15
Nodes (13): 10. Failure Modes dan Degradasi, 11. Keputusan Arsitektur dan Trade-off, 12. Batas Skalabilitas, 13. Peta Direktori Arsitektural, 14. Cara Memverifikasi Arsitektur, 15. Ringkasan Arsitektur, 1. Gaya Arsitektur, 2. Diagram Konteks (C4 Level 1) (+5 more)

### Community 43 - "ai_triage.py"
Cohesion: 0.11
Nodes (23): Backend (safe isolated suites), ai_triage(), _alert_tenant(), _as_mapping(), _cluster_alerts(), _cluster_prompt(), format_wib_window_label(), _group_by_indicators() (+15 more)

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

### Community 50 - "query.py"
Cohesion: 0.14
Nodes (11): build_filter_sql(), _canonical_field(), _canonical_op(), _clean_value(), _error(), _escape_like(), _glob_to_like(), normalize_filter() (+3 more)

### Community 52 - "Layout"
Cohesion: 0.29
Nodes (7): Global shell, Impor dan Laporan, Insiden, Klasifikasi & korelasi, Layout, Responsive, Triage

### Community 53 - "Control"
Cohesion: 0.22
Nodes (3): click(), Control, fixture()

### Community 54 - "database.py"
Cohesion: 0.10
Nodes (23): _batch_insert_values(), _batch_instance(), _clean_expired_previews_locked(), create_preview_token(), get_active_profile(), get_active_profile_id(), get_database_status(), get_database_status_unavailable() (+15 more)

### Community 55 - "test_ollama"
Cohesion: 0.50
Nodes (3): Design lint, Frontend, Testing — Arbiter

### Community 56 - "6. Correlation policy"
Cohesion: 0.40
Nodes (5): 6.1 Response linkage, 6.2 Canonical group identity, 6.3 Ordered chain, 6.4 Correlation confidence, 6. Correlation policy

### Community 57 - "Control"
Cohesion: 0.22
Nodes (3): click(), Control, fixture()

### Community 58 - "wazuh_intel.py"
Cohesion: 0.21
Nodes (20): as_dict(), clean_val(), _alert_key(), _as_json(), build_attack_chains(), _bump(), _chain_steps(), classify_alert() (+12 more)

### Community 59 - "5\. Cara Kerja"
Cohesion: 0.20
Nodes (10): 5.1 Ingesti dan parsing, 5.2 Normalisasi, 5.3 Deduplikasi, 5.4 Klasifikasi, 5.5 Korelasi, 5.6 AI Triage lokal, 5.7 Triage dan insiden, 5.8 Threat intelligence dan redaksi (+2 more)

### Community 61 - "render"
Cohesion: 0.33
Nodes (10): applyUserPermissions(), canLeave(), checkFlagSummary(), databaseChanged(), render(), renderLoginGate(), renderTenantOptions(), routeScope() (+2 more)

### Community 62 - "router.js"
Cohesion: 0.29
Nodes (3): createRouter(), change(), parseRoute()

### Community 63 - "⚡ Key Capabilities"
Cohesion: 0.17
Nodes (12): 10. Privacy-First Redactor, 11. Official Deliverables (5 Export Paths), 1. Resilient Multi-Format Ingestion, 2. High-Precision Log Dissector (No False Fields), 3. Signature-Based Deduplication & Causal Correlation, 4. Enterprise Multi-Tenant Architecture, 5. Modular Destination UI, 6. Local AI Triage & Persistent Daily Case Grouping (`#/ai-triage`) (+4 more)

### Community 64 - "Arbiter Architecture — Wazuh Read, Classify, Correlate"
Cohesion: 0.13
Nodes (15): 10. Acceptance tests, 11. Non-goals, 1. Design constraints, 2. Dataset evidence used to shape the architecture, 3. End-to-end pipeline, 5.1 Curated rule profiles (explicit, not trained), 5.2 Context signals, 5.3 Wording policy (+7 more)

### Community 65 - "intel.py"
Cohesion: 0.09
Nodes (10): enrich_ip(), is_private_ip(), _json_object(), lookup_remote_ip_cache(), query_abuseipdb(), _remote_profile_read_only(), _resolve_remote_db_url(), sync_remote_cache() (+2 more)

### Community 66 - "state.js"
Cohesion: 0.14
Nodes (20): cleanIds(), draftFrom(), draftsEqual(), evidenceParams(), incidentPayload(), incidentRoute(), selectedIds(), SEVERITIES (+12 more)

### Community 67 - "package.json"
Cohesion: 0.20
Nodes (9): description, engines, node, name, private, scripts, test, type (+1 more)

### Community 69 - "build"
Cohesion: 0.29
Nodes (6): build, volumes, context, dockerfile, services, arbiter

### Community 70 - "Deploy config reference"
Cohesion: 0.33
Nodes (5): Containers, Deploy config reference, Environment variables, Reverse proxy (optional), Secrets

### Community 71 - "5. Arsitektur Tools (Backend)"
Cohesion: 0.25
Nodes (8): 5.1 Peta modul dan dependensi, 5.2 Tanggung jawab per modul, 5.3 Lapisan request, 5.4 Alur ingest end-to-end, 5.6 Alur AI Triage, 5.7 Alur ekspor, 5.8 Profil database dan pemeliharaan, 5. Arsitektur Tools (Backend)

### Community 72 - "Code Style — Arbiter"
Cohesion: 0.40
Nodes (4): Code Style — Arbiter, CSS, Frontend (JS), Python

### Community 73 - "Deploy Arbiter"
Cohesion: 0.40
Nodes (4): Deploy Arbiter, Local dev, Pre-deploy checks, Production (Docker Compose)

### Community 74 - "8\. Instalasi"
Cohesion: 0.22
Nodes (9): 8.1 Prasyarat, 8.3 Metode B — Host mode (PostgreSQL yang sudah ada), 8.4 Metode C — Python lokal tanpa Docker, 8.5 Konfigurasi Wazuh Indexer (opsional, untuk Realtime), 8.6 Konfigurasi AI lokal (opsional), 8.7 Login pertama, 8.8 Verifikasi instalasi, 8.9 Variabel lingkungan (+1 more)

### Community 75 - "test_wazuh_intel.py"
Cohesion: 0.12
Nodes (6): extract_active_response(), _active_response(), ActiveResponseReadTests, ClassificationTests, CorrelationTests, NormalizeIntegrationTests

### Community 76 - "secure_store.py"
Cohesion: 0.15
Nodes (20): authenticate_user(), create_session_token(), create_user(), _default_admin_credentials(), delete_user(), get_user(), _hash_password(), _load_raw_users() (+12 more)

### Community 77 - "6.4 Skema database"
Cohesion: 0.25
Nodes (8): 6.4.1 `wazuh.alerts`, 6.4.2 `wazuh.analysis_groups`, 6.4.3 `wazuh.alert_group_members`, 6.4.5 `public.ip_intel_cache`, 6.4.6 Tabel Remote milik provider, 6.4.7 Indeks performa, 6.4.8 Catatan operasional, 6.4 Skema database

### Community 78 - "4. Arsitektur Web (Frontend)"
Cohesion: 0.29
Nodes (7): 4.1 Lapisan frontend, 4.2 Pola feature module, 4.3 Routing dan scope, 4.4 Alur render satu halaman, 4.5 Login gate dan hak tampilan, 4.6 State yang tidak dipersistensi, 4. Arsitektur Web (Frontend)

### Community 79 - "8. Roadmap implementasi, tiap tahap bisa diverifikasi"
Cohesion: 0.29
Nodes (7): 8. Roadmap implementasi, tiap tahap bisa diverifikasi, Phase 0 — safety & baseline, Phase 1 — modular foundation + shell, Phase 2 — triage-first experience, Phase 3 — insiden workspace, Phase 4 — impor dan laporan, Phase 5 — hardening & rollout

### Community 84 - "8. Deployment"
Cohesion: 0.33
Nodes (6): 8.1 Topologi A — Docker standalone, 8.2 Topologi B — Host mode, 8.3 Topologi C — Python lokal, 8.4 Topologi D — Reverse proxy TLS, 8.5 Startup sequence, 8. Deployment

### Community 85 - "Arbiter"
Cohesion: 0.20
Nodes (10): Arbiter, 🛠️ Architecture & Tech Stack, Dataset calibration and limits, 📄 License, 🎯 Overview, 🔒 Security & Privacy Notice, 📖 SOC Analyst Quickstart Workflow, 🧪 Testing & Quality Assurance (+2 more)

### Community 86 - "4. Wireframe dan first viewport"
Cohesion: 0.33
Nodes (6): 4. Wireframe dan first viewport, A. Triage desktop, B. Insiden index dan case workspace, C. Impor, D. Laporan, E. Mobile

### Community 87 - "7\. Keamanan"
Cohesion: 0.29
Nodes (7): 7.1 Prinsip desain, 7.2 Autentikasi dan otorisasi, 7.3 Rahasia saat istirahat, 7.4 Isolasi jaringan dan SSRF, 7.5 Perlindungan data dan ekspor, 7.6 Batasan keamanan yang perlu diketahui, 7\. Keamanan

### Community 88 - "diagnose_realtime_pull.py"
Cohesion: 0.38
Nodes (3): _fmt(), main(), _existing()

### Community 89 - "_SyncConnection"
Cohesion: 0.12
Nodes (3): _FakeCursor, RemoteSyncTests, _SyncConnection

### Community 90 - "json"
Cohesion: 0.21
Nodes (23): apiURL(), copyText(), json(), save(), saveRealtime(), loadBatchIncidentOptions(), mount(), applyFlag() (+15 more)

### Community 91 - "triage-request.test.mjs"
Cohesion: 0.16
Nodes (3): createSelection(), Element, requestsFor()

### Community 92 - "load_settings"
Cohesion: 0.13
Nodes (14): api_add_exclusion(), api_get_settings(), api_put_settings(), api_realtime_count(), api_realtime_pull(), api_start_alert_pull(), api_test_wazuh(), api_update_exclusion() (+6 more)

### Community 93 - "get_db"
Cohesion: 0.18
Nodes (21): list_users(), get_db(), add_group_members(), api_auth_me(), api_create_user(), api_delete_exclusion(), api_delete_user(), api_delete_wazuh_query() (+13 more)

### Community 94 - "pull_jobs.py"
Cohesion: 0.17
Nodes (14): _build_windows(), cancel_job(), get_job(), _ingest(), list_jobs(), _now(), _parse_time(), _public() (+6 more)

### Community 95 - "normalize_tenants"
Cohesion: 0.15
Nodes (13): API Conventions — Arbiter, Credential redaction, Errors, Tenant scoping, api_flags_alerts(), api_flags_groups(), api_flags_summary(), _build_flag_scope_where() (+5 more)

### Community 96 - "scope.js"
Cohesion: 0.30
Nodes (9): parseFilters(), integer(), queryFrom(), rawTenantValues(), scopeDescription(), scopeParams(), tenantScope(), moduleURL (+1 more)

### Community 97 - "5. Information architecture & interaction contracts"
Cohesion: 0.40
Nodes (5): 5. Information architecture & interaction contracts, Accessibility, Editing dan destructive actions, Refresh, Scope

### Community 99 - "settings.py"
Cohesion: 0.13
Nodes (12): _boolean(), _deep_merge(), default_settings(), _http_error_reason(), intel_abuseipdb_key(), normalize_ollama_base_url(), test_wazuh_connection(), _text() (+4 more)

### Community 100 - "withParams"
Cohesion: 0.35
Nodes (8): renderMonitoringDashboard(), renderReviewActivity(), ROLE_LABELS, mount(), load(), report(), updateQuery(), withParams()

### Community 101 - "🚀 Setup & Getting Started"
Cohesion: 0.33
Nodes (6): Connecting to a Neuropetra `ip_intel` database, Method A: Standalone Docker Setup (Fastest for new users), Method B: Host Mode (Connect to existing PostgreSQL / IP Intel), Method C: Local Python Setup (Without Docker), Prerequisites, 🚀 Setup & Getting Started

### Community 102 - "6. Arsitektur Data"
Cohesion: 0.40
Nodes (5): 6.1 ERD, 6.2 Penyimpanan JSONB, 6.3 Indeks, 6.4 Kepemilikan data, 6. Arsitektur Data

### Community 103 - "2\. Deskripsi Produk"
Cohesion: 0.40
Nodes (5): 2.1 Untuk siapa, 2.2 Batas produk, 2.3 Destinasi aplikasi, 2.4 Kemampuan inti, 2\. Deskripsi Produk

### Community 104 - "6\. Komponen yang Dipakai"
Cohesion: 0.40
Nodes (5): 6.1 Stack, 6.2 Modul backend, 6.3 Modul frontend, 6.5 Kelompok endpoint API, 6\. Komponen yang Dipakai

### Community 105 - "stats-trust.test.mjs"
Cohesion: 0.28
Nodes (4): flush(), harness(), startSample(), stats()

### Community 108 - "imports/view.js"
Cohesion: 0.39
Nodes (4): createImportSession(), importResult(), mount(), update()

### Community 109 - "4. Data contracts"
Cohesion: 0.50
Nodes (4): 4.1 Raw Wazuh alert (minimum), 4.2 Normalized alert, 4.3 Classification result, 4. Data contracts

### Community 110 - "7. Arsitektur Keamanan"
Cohesion: 0.50
Nodes (4): 7.1 Trust boundary, 7.2 Kontrol keamanan per lapisan, 7.3 Batas yang harus dijaga saat deployment, 7. Arsitektur Keamanan

### Community 111 - "3\. Workflow"
Cohesion: 0.50
Nodes (4): 3.1 Workflow analis (harian), 3.2 Workflow data, 3.3 Siklus hidup insiden, 3\. Workflow

## Knowledge Gaps
- **18 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `esc()` connect `esc` to `app.js`, `stats/view.js`, `withParams`, `loadingRows`, `reports/view.js`, `loadingRows`, `Code Style — Arbiter`, `tenantValues`, `Arsitektur Arbiter — Web & Tools`, `6\. Komponen yang Dipakai`, `imports/view.js`, `7. Arsitektur Keamanan`, `triage/view.js`, `alert_where`, `errorState`, `mount`, `json`, `render`?**
  _High betweenness centrality (0.260) - this node is a cross-community bridge._
- **Are the 6 inferred relationships involving `esc()` (e.g. with `Agent: code-reviewer` and `/review — Code review pass`) actually correct?**
  _`esc()` has 6 INFERRED edges - model-reasoned connections that need verification._
- **Should `ref_node_assert` be split into smaller, more focused modules?**
  _Cohesion score 0.07419712070874862 - nodes in this community are weakly interconnected._
- **Why does `Task 1: Establish precise shared multi-tenant scope and safe facet contract` connect `alert_where` to `scope.js`, `Any`, `File Map and Interfaces`, `json`, `get_db`, `normalize_tenants`?**
  _High betweenness centrality (0.132) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `json()` (e.g. with `mount()` and `loadSelected()`) actually correct?**
  _`json()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Should `test_ui_api.py` be split into smaller, more focused modules?**
  _Cohesion score 0.10160427807486631 - nodes in this community are weakly interconnected._
- **Why does `Agent: code-reviewer` connect `alert_where` to `Any`, `esc`?**
  _High betweenness centrality (0.121) - this node is a cross-community bridge._