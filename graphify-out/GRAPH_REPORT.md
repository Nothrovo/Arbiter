# Graph Report - Arbiter  (2026-11-20)

## Corpus Check
- 170 files · ~166,666 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 15 file(s) not represented in the graph (top: .css 5, (none) 4, .woff2 4)

## Summary
- 2061 nodes · 5367 edges · 119 communities (92 shown, 27 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 153 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `b8152cce`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- withParams
- ref_node_assert
- test_ui_api.py
- stats/view.js
- esc
- state.js
- ApiIntegrationTests
- loadingRows
- AITriageAPITests
- start.sh
- tenantValues
- Arbiter — blueprint rombak UI/UX
- Arbiter — audit UI/UX dan keputusan redesign
- ARSITEKTUR.md
- UIAPIContractTests
- AGENTS.md — Arbiter Project Context for AI Agents
- Any
- test_settings.py
- lookup_remote_ip_cache_detail
- Request
- SafetyTests
- normalize_alert
- Any
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
- errorState
- exclusions.py
- _cluster_alerts
- database-workspace.test.mjs
- pull_jobs.py
- scope.js
- FlagWorkspaceTests
- mount
- api_get_monitoring
- Arsitektur Arbiter — Web & Tools
- ai_triage.py
- DatabaseTrustTests
- .test_enrich_ips_with_sidecar_uses_cache_then_live_fallback_and_writes_back_context
- Arbiter UI/UX Redesign — Quiet Evidence Desk
- DESIGN.md
- settings.json
- ui-ux-redesign/README.md
- query.py
- StatsEndpointContractTests
- Layout
- test_schema_migrations.py
- database.py
- SyntheticDB
- incidents/render.js
- Control
- wazuh_intel.py
- 5\. Cara Kerja
- sanitize_text
- wazuh_count
- Testing — Arbiter
- ⚡ Key Capabilities
- Arbiter Architecture — Wazuh Read, Classify, Correlate
- intel.py
- get_database_status
- package.json
- ExclusionAPITests
- build
- Deploy config reference
- 5. Arsitektur Tools (Backend)
- Code Style — Arbiter
- Deploy Arbiter
- mountWorkspace
- wazuh-queries/model.js
- secure_store.py
- core.py
- 4. Arsitektur Web (Frontend)
- 8. Roadmap implementasi, tiap tahap bisa diverifikasi
- fix-issue.md
- validate-bash.sh
- setup-ai-symlinks.sh
- 8. Deployment
- Arbiter
- 4. Wireframe dan first viewport
- SyntheticRoot
- load_settings
- enrich_intel
- redact_settings
- triage-request.test.mjs
- extract_active_response
- api_database_switch
- enrich_ip
- get_db
- suggest_groups
- 5. Information architecture & interaction contracts
- settings.py
- _FakeCursor
- 🚀 Setup & Getting Started
- 6. Arsitektur Data
- _enrich_single_public_live
- render
- stats-trust.test.mjs
- Control
- imports/view.js
- .test_realtime_pull_respects_custom_severity_and_resets_since_on_severity_change
- 8\. Instalasi
- Dokumentasi Arbiter
- feature-loader.test.mjs
- 6.4 Skema database
- 7\. Keamanan
- 2\. Deskripsi Produk
- router-history.test.mjs

## God Nodes (most connected - your core abstractions)
1. `esc()` - 103 edges
2. `json()` - 87 edges
3. `get_db()` - 83 edges
4. `icon()` - 72 edges
5. `mount()` - 53 edges
6. `mount()` - 53 edges
7. `AITriageAPITests` - 47 edges
8. `errorState()` - 42 edges
9. `UIAPIContractTests` - 39 edges
10. `apiURL()` - 36 edges

## Surprising Connections (you probably didn't know these)
- `5.7 Alur ekspor` --references--> `export_scope()`  [INFERRED]
  docs/ARSITEKTUR.md → app/main.py
- `5.6 AI Triage lokal` --references--> `safe_alerts()`  [INFERRED]
  docs/DOKUMENTASI.md → app/ai_triage.py
- `7.5 Perlindungan data dan ekspor` --references--> `safe_alerts()`  [INFERRED]
  docs/DOKUMENTASI.md → app/ai_triage.py
- `4.2 Normalized alert` --references--> `normalize_alert()`  [INFERRED]
  docs/ARCHITECTURE.md → app/core.py
- `Frontend (JS)` --references--> `esc()`  [INFERRED]
  .ai/rules/code-style.md → app/static/js/ui/primitives.js

## Import Cycles
- None detected.

## Communities (119 total, 27 thin omitted)

### Community 0 - "withParams"
Cohesion: 0.22
Nodes (12): renderMonitoringDashboard(), renderReviewActivity(), renderReviewerFilter(), ROLE_LABELS, mount(), load(), report(), updateQuery() (+4 more)

### Community 1 - "ref_node_assert"
Cohesion: 0.08
Nodes (19): url, harness(), profiles, harness(), status, modelURL, mainPy, root (+11 more)

### Community 3 - "stats/view.js"
Cohesion: 0.12
Nodes (39): BENIGN_WHITELIST_PATTERNS, CHART_OPTIONS, distributionPercentages(), drilldownScrollBehavior(), generateMarkdownSummary(), generateStatsCSV(), INJECTION_PATTERNS, isMaliciousAlert() (+31 more)

### Community 4 - "esc"
Cohesion: 0.15
Nodes (23): /review — Code review pass, notify(), renderControls(), tenantOptionsHTML(), ERROR_CODE_CATEGORIES, ERROR_CODE_SECTIONS, ERROR_CODES, filterErrorCodeSections() (+15 more)

### Community 5 - "state.js"
Cohesion: 0.19
Nodes (16): cleanIds(), draftFrom(), draftsEqual(), evidenceParams(), incidentPayload(), selectedIds(), TEXT_FIELDS, validateDraft() (+8 more)

### Community 7 - "loadingRows"
Cohesion: 0.10
Nodes (54): json(), save(), formatDuration(), mount(), paint(), paintProgress(), poll(), pollLater() (+46 more)

### Community 10 - "tenantValues"
Cohesion: 0.16
Nodes (29): ApiError, apiURL(), copyHTML(), copyText(), download(), request(), FLAG_EXPORT_FORMATS, FLAG_EXPORT_KEYS (+21 more)

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
Cohesion: 0.11
Nodes (20): api_ai_test(), api_ai_triage_save(), api_auth_login(), api_auth_logout(), api_create_report_audit_log(), api_database_config(), api_database_purge_alerts(), api_database_purge_incidents() (+12 more)

### Community 17 - "test_settings.py"
Cohesion: 0.22
Nodes (7): decrypt_text(), encrypt_text(), _fernet(), is_encrypted(), _key_path(), _read_or_create_key_file(), SecretStoreError

### Community 18 - "lookup_remote_ip_cache_detail"
Cohesion: 0.26
Nodes (4): lookup_remote_ip_cache_detail(), _FakeConnection, _psycopg_modules(), RemoteCacheLookupTests

### Community 19 - "Request"
Cohesion: 0.23
Nodes (15): list_users(), get_db(), api_auth_me(), api_create_user(), api_delete_user(), api_list_users(), api_reviewers(), api_save_wazuh_query() (+7 more)

### Community 21 - "normalize_alert"
Cohesion: 0.15
Nodes (5): normalize_alert(), _active_response(), ClassificationTests, CorrelationTests, NormalizeIntegrationTests

### Community 22 - "Any"
Cohesion: 0.07
Nodes (40): current_wib_window_key(), get_triage_state_key(), safe_alerts(), with_exclusions(), _ai_triage_batch_size(), _ai_triage_candidate_count(), _ai_triage_exclude_ids(), _ai_triage_pick_state() (+32 more)

### Community 23 - "Arbiter"
Cohesion: 0.33
Nodes (5): Arbiter, Audience and usage, Development verification, Implemented case policy without schema changes, Product boundaries

### Community 24 - "exports.py"
Cohesion: 0.06
Nodes (46): alert_full_log(), _as_dict(), _evidence_fields(), export_row(), export_rows(), _first(), _flat(), generate_docx_landscape_report() (+38 more)

### Community 25 - "mount"
Cohesion: 0.09
Nodes (56): aiSeverityKey(), alertFacts(), alertIndex(), boundedInteger(), DEFAULT_BATCH, formatWibWindowLabel(), GROUP_BY_OPTIONS, groupAlerts() (+48 more)

### Community 26 - "re"
Cohesion: 0.12
Nodes (13): build_log_signature(), extract_alerts(), first_ip_in(), kv_details(), normalize_log_for_signature(), parse_export(), parse_log_line(), parse_timestamp_iso() (+5 more)

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
Cohesion: 0.06
Nodes (3): SettingsAPITests, __init__(), __init__()

### Community 31 - "test_pull_jobs.py"
Cohesion: 0.11
Nodes (7): base_config(), fake_get_db(), FakeConnection, FakeTransaction, load_pull_jobs(), PullJobTests, wait_for()

### Community 32 - "app.js"
Cohesion: 0.07
Nodes (31): adminOnlyPages, applyWorkspaceSettings(), checkPullActivity(), closeNav(), health(), help, loadWorkspaceSettings(), main (+23 more)

### Community 33 - "errorState"
Cohesion: 0.39
Nodes (8): databaseIdentity(), summarizeTelemetryRange(), mount(), loadStatus(), maintain(), render(), switchTo(), errorState()

### Community 34 - "exclusions.py"
Cohesion: 0.15
Nodes (10): active_exclusion_rules(), build_exclusion_sql(), _coerce_enabled(), _escape_like(), glob_to_like(), normalize_exclusion_rule(), normalize_exclusions(), parse_wazuh_exclusion() (+2 more)

### Community 35 - "_cluster_alerts"
Cohesion: 0.17
Nodes (4): ai_triage(), _cluster_alerts(), _cluster_prompt(), _validate_cluster_verdicts()

### Community 36 - "database-workspace.test.mjs"
Cohesion: 0.31
Nodes (8): normalizeSidebarState(), readSidebarState(), SIDEBAR_KEY, toggleSidebarState(), writeSidebarState(), shell(), source, root

### Community 37 - "pull_jobs.py"
Cohesion: 0.20
Nodes (11): _build_windows(), _ingest(), list_jobs(), _now(), _parse_time(), _public(), _run_job(), pull_window() (+3 more)

### Community 38 - "scope.js"
Cohesion: 0.22
Nodes (14): loadList(), caseReportRoute(), exportURL(), reportAction(), reportScope(), parseFilters(), queryFrom(), rawTenantValues() (+6 more)

### Community 40 - "mount"
Cohesion: 0.09
Nodes (54): flagBadge(), flagMeta(), ruleStatusBadge(), alertUrlPreview(), renderAlertDetailRows(), renderFlagGroups(), triageLinkFor(), renderEvidence() (+46 more)

### Community 41 - "api_get_monitoring"
Cohesion: 0.14
Nodes (9): api_database_status(), api_get_monitoring(), _expire_stale_claims(), get_alert_detail(), health_check(), review_activity(), _review_activity_payload(), _review_local_date() (+1 more)

### Community 42 - "Arsitektur Arbiter — Web & Tools"
Cohesion: 0.12
Nodes (17): 10. Failure Modes dan Degradasi, 11. Keputusan Arsitektur dan Trade-off, 12. Batas Skalabilitas, 13. Peta Direktori Arsitektural, 14. Cara Memverifikasi Arsitektur, 15. Ringkasan Arsitektur, 1. Gaya Arsitektur, 2. Diagram Konteks (C4 Level 1) (+9 more)

### Community 43 - "ai_triage.py"
Cohesion: 0.14
Nodes (16): _alert_tenant(), _as_mapping(), format_wib_window_label(), _group_by_indicators(), find(), union(), _group_by_rule_description(), heuristic_triage() (+8 more)

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
Cohesion: 0.13
Nodes (11): build_filter_sql(), _canonical_field(), _canonical_op(), _clean_value(), _error(), _escape_like(), _glob_to_like(), normalize_filter() (+3 more)

### Community 52 - "Layout"
Cohesion: 0.29
Nodes (7): Global shell, Impor dan Laporan, Insiden, Klasifikasi & korelasi, Layout, Responsive, Triage

### Community 54 - "database.py"
Cohesion: 0.18
Nodes (11): _batch_insert_values(), _batch_instance(), bump_daily_metrics(), _clean_expired_previews_locked(), create_preview_token(), ingest_alerts_batch(), purge_alerts(), purge_incidents() (+3 more)

### Community 55 - "SyntheticDB"
Cohesion: 0.18
Nodes (3): Task 2: Build SQL aggregation endpoints and schema support, TriageScopeTests, SyntheticDB

### Community 56 - "incidents/render.js"
Cohesion: 0.23
Nodes (16): caseHref(), filterIncidents(), incidentRoute(), SEVERITIES, STATUSES, allOptions(), options(), renderList() (+8 more)

### Community 57 - "Control"
Cohesion: 0.22
Nodes (3): click(), Control, fixture()

### Community 58 - "wazuh_intel.py"
Cohesion: 0.21
Nodes (20): as_dict(), clean_val(), _alert_key(), _as_json(), build_attack_chains(), _bump(), _chain_steps(), classify_alert() (+12 more)

### Community 59 - "5\. Cara Kerja"
Cohesion: 0.20
Nodes (10): 5.1 Ingesti dan parsing, 5.2 Normalisasi, 5.3 Deduplikasi, 5.4 Klasifikasi, 5.5 Korelasi, 5.6 AI Triage lokal, 5.7 Triage dan insiden, 5.8 Threat intelligence dan redaksi (+2 more)

### Community 62 - "Testing — Arbiter"
Cohesion: 0.33
Nodes (5): Backend (safe isolated suites), Design lint, Frontend, Testing — Arbiter, test_ollama()

### Community 63 - "⚡ Key Capabilities"
Cohesion: 0.17
Nodes (12): 10. Privacy-First Redactor, 11. Official Deliverables (5 Export Paths), 1. Resilient Multi-Format Ingestion, 2. High-Precision Log Dissector (No False Fields), 3. Signature-Based Deduplication & Causal Correlation, 4. Enterprise Multi-Tenant Architecture, 5. Modular Destination UI, 6. Local AI Triage & Persistent Daily Case Grouping (`#/ai-triage`) (+4 more)

### Community 64 - "Arbiter Architecture — Wazuh Read, Classify, Correlate"
Cohesion: 0.08
Nodes (24): 10. Acceptance tests, 11. Non-goals, 1. Design constraints, 2. Dataset evidence used to shape the architecture, 3. End-to-end pipeline, 4.1 Raw Wazuh alert (minimum), 4.2 Normalized alert, 4.3 Classification result (+16 more)

### Community 65 - "intel.py"
Cohesion: 0.08
Nodes (19): enrich_ips_with_sidecar(), extract_alert_intel_context(), fetch_sidecar_cache(), has_usable_sidecar_cache(), is_cdn_edge(), is_private_ip(), is_valid_ip(), _json_object() (+11 more)

### Community 66 - "get_database_status"
Cohesion: 0.18
Nodes (8): get_active_profile(), get_database_status(), get_database_status_unavailable(), get_db_connection(), mask_connection_url(), _persist_profile_overrides(), _profiles_payload(), update_profile_url()

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

### Community 74 - "mountWorkspace"
Cohesion: 0.45
Nodes (11): mountWorkspace(), context(), initial(), loadPage(), loadSelected(), panels(), refresh(), save() (+3 more)

### Community 75 - "wazuh-queries/model.js"
Cohesion: 0.33
Nodes (6): buildWazuhQueries(), parseSeverityBounds(), PRESET_CATEGORIES, PRESET_WAZUH_QUERIES, QUERY_SEVERITY_OPTIONS, QUERY_TIME_OPTIONS

### Community 76 - "secure_store.py"
Cohesion: 0.26
Nodes (13): authenticate_user(), create_session_token(), create_user(), _default_admin_credentials(), delete_user(), get_user(), _hash_password(), _load_raw_users() (+5 more)

### Community 77 - "core.py"
Cohesion: 0.27
Nodes (4): local_ai_suggest_groups(), LocalAIUnavailable, ollama_request(), suggestions_with_fallback()

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

### Community 87 - "SyntheticRoot"
Cohesion: 0.22
Nodes (3): context(), load(), SyntheticRoot

### Community 88 - "load_settings"
Cohesion: 0.09
Nodes (14): API Conventions — Arbiter, Credential redaction, Errors, api_realtime_count(), api_realtime_pull(), load_settings(), migrate_settings(), _normalize_wazuh_timestamp() (+6 more)

### Community 89 - "enrich_intel"
Cohesion: 0.16
Nodes (6): _remote_profile_read_only(), _resolve_remote_db_url(), sync_remote_cache(), upsert_ip_cache(), enrich_intel(), RemoteSyncTests

### Community 90 - "redact_settings"
Cohesion: 0.36
Nodes (6): api_add_exclusion(), api_delete_exclusion(), api_import_exclusions(), api_update_exclusion(), _persist_exclusion_rules(), redact_settings()

### Community 91 - "triage-request.test.mjs"
Cohesion: 0.13
Nodes (3): createSelection(), Element, requestsFor()

### Community 93 - "api_database_switch"
Cohesion: 0.40
Nodes (4): check_profile_ready(), get_active_profile_id(), set_active_profile(), api_database_switch()

### Community 94 - "enrich_ip"
Cohesion: 0.16
Nodes (5): AbuseIPDBError, enrich_ip(), query_abuseipdb(), EnrichFallbackTests, fake_abuse()

### Community 95 - "get_db"
Cohesion: 0.09
Nodes (36): Agent: code-reviewer, Agent: security-auditor, Tenant scoping, add_group_members(), api_flag_alerts(), api_flag_single_alert(), api_flags_alerts(), api_flags_groups() (+28 more)

### Community 97 - "5. Information architecture & interaction contracts"
Cohesion: 0.40
Nodes (5): 5. Information architecture & interaction contracts, Accessibility, Editing dan destructive actions, Refresh, Scope

### Community 99 - "settings.py"
Cohesion: 0.12
Nodes (16): api_put_settings(), _boolean(), _deep_merge(), default_settings(), _http_error_reason(), intel_abuseipdb_key(), intel_virustotal_key(), _is_local_or_lan_host() (+8 more)

### Community 100 - "_FakeCursor"
Cohesion: 0.11
Nodes (3): _FakeCursor, _FakeResult, _SyncConnection

### Community 101 - "🚀 Setup & Getting Started"
Cohesion: 0.33
Nodes (6): Connecting to a Neuropetra `ip_intel` database, Method A: Standalone Docker Setup (Fastest for new users), Method B: Host Mode (Connect to existing PostgreSQL / IP Intel), Method C: Local Python Setup (Without Docker), Prerequisites, 🚀 Setup & Getting Started

### Community 102 - "6. Arsitektur Data"
Cohesion: 0.40
Nodes (5): 6.1 ERD, 6.2 Penyimpanan JSONB, 6.3 Indeks, 6.4 Kepemilikan data, 6. Arsitektur Data

### Community 104 - "render"
Cohesion: 0.33
Nodes (10): applyUserPermissions(), canLeave(), checkFlagSummary(), databaseChanged(), render(), renderLoginGate(), renderTenantOptions(), routeScope() (+2 more)

### Community 105 - "stats-trust.test.mjs"
Cohesion: 0.28
Nodes (4): flush(), harness(), startSample(), stats()

### Community 106 - "Control"
Cohesion: 0.22
Nodes (3): click(), Control, fixture()

### Community 108 - "imports/view.js"
Cohesion: 0.27
Nodes (6): createImportSession(), importPage(), importResult(), mount(), update(), moduleURL

### Community 111 - "8\. Instalasi"
Cohesion: 0.14
Nodes (12): init_database(), _load_profile_overrides(), 8.1 Prasyarat, 8.2 Metode A — Docker standalone (paling cepat), 8.3 Metode B — Host mode (PostgreSQL yang sudah ada), 8.4 Metode C — Python lokal tanpa Docker, 8.5 Konfigurasi Wazuh Indexer (opsional, untuk Realtime), 8.6 Konfigurasi AI lokal (opsional) (+4 more)

### Community 112 - "Dokumentasi Arbiter"
Cohesion: 0.15
Nodes (13): 10\. Pengembangan dan Pemeliharaan, 11\. Lisensi, 1\. Ringkasan, 3.1 Workflow analis (harian), 3.2 Workflow data, 3.3 Siklus hidup insiden, 3\. Workflow, 4.1 Alur end-to-end (+5 more)

### Community 114 - "6.4 Skema database"
Cohesion: 0.13
Nodes (14): ingest_alert_with_dedup(), 6.1 Stack, 6.2 Modul backend, 6.3 Modul frontend, 6.4.1 `wazuh.alerts`, 6.4.2 `wazuh.analysis_groups`, 6.4.3 `wazuh.alert_group_members`, 6.4.5 `public.ip_intel_cache` (+6 more)

### Community 115 - "7\. Keamanan"
Cohesion: 0.29
Nodes (7): 7.1 Prinsip desain, 7.2 Autentikasi dan otorisasi, 7.3 Rahasia saat istirahat, 7.4 Isolasi jaringan dan SSRF, 7.5 Perlindungan data dan ekspor, 7.6 Batasan keamanan yang perlu diketahui, 7\. Keamanan

### Community 117 - "2\. Deskripsi Produk"
Cohesion: 0.40
Nodes (5): 2.1 Untuk siapa, 2.2 Batas produk, 2.3 Destinasi aplikasi, 2.4 Kemampuan inti, 2\. Deskripsi Produk

### Community 124 - "router-history.test.mjs"
Cohesion: 0.29
Nodes (3): createRouter(), change(), parseRoute()

## Knowledge Gaps
- **27 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `esc()` connect `esc` to `app.js`, `errorState`, `withParams`, `stats/view.js`, `state.js`, `loadingRows`, `Code Style — Arbiter`, `render`, `tenantValues`, `mount`, `imports/view.js`, `mountWorkspace`, `Arsitektur Arbiter — Web & Tools`, `6.4 Skema database`, `incidents/render.js`, `mount`, `get_db`?**
  _High betweenness centrality (0.221) - this node is a cross-community bridge._
- **Are the 6 inferred relationships involving `esc()` (e.g. with `Agent: code-reviewer` and `/review — Code review pass`) actually correct?**
  _`esc()` has 6 INFERRED edges - model-reasoned connections that need verification._
- **Should `ref_node_assert` be split into smaller, more focused modules?**
  _Cohesion score 0.08232118758434548 - nodes in this community are weakly interconnected._
- **Why does `Task 1: Establish precise shared multi-tenant scope and safe facet contract` connect `get_db` to `scope.js`, `tenantValues`, `File Map and Interfaces`, `Any`?**
  _High betweenness centrality (0.129) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `json()` (e.g. with `mount()` and `loadSelected()`) actually correct?**
  _`json()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Should `test_ui_api.py` be split into smaller, more focused modules?**
  _Cohesion score 0.12561576354679804 - nodes in this community are weakly interconnected._
- **Why does `Agent: code-reviewer` connect `get_db` to `esc`?**
  _High betweenness centrality (0.103) - this node is a cross-community bridge._