# Graph Report - Arbiter  (2026-11-19)

## Corpus Check
- 170 files · ~163,895 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 15 file(s) not represented in the graph (top: .css 5, (none) 4, .woff2 4)

## Summary
- 2023 nodes · 5193 edges · 127 communities (99 shown, 28 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 151 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `5bd92622`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- test_wazuh_intel.py
- ref_node_assert
- test_ui_api.py
- stats/view.js
- incidents/render.js
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
- secure_store.py
- lookup_remote_ip_cache_detail
- with_exclusions
- SafetyTests
- enrich_ip
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
- errorState
- exclusions.py
- SyntheticDB
- database-workspace.test.mjs
- _cluster_alerts
- reports/view.js
- FlagWorkspaceTests
- json
- main.py
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
- withParams
- database.py
- load_isolated_api
- 6. Correlation policy
- Control
- wazuh_intel.py
- 5\. Cara Kerja
- sanitize_text
- wazuh_search
- createRouter
- ⚡ Key Capabilities
- Arbiter Architecture — Wazuh Read, Classify, Correlate
- intel.py
- _http_error_reason
- package.json
- ExclusionAPITests
- build
- Deploy config reference
- 5. Arsitektur Tools (Backend)
- Code Style — Arbiter
- Deploy Arbiter
- classify_alert
- _FakeResult
- secure_store.py
- LocalAIUnavailable
- 4. Arsitektur Web (Frontend)
- 8. Roadmap implementasi, tiap tahap bisa diverifikasi
- fix-issue.md
- validate-bash.sh
- setup-ai-symlinks.sh
- 8. Deployment
- Arbiter
- 4. Wireframe dan first viewport
- enrich_ips_with_sidecar
- diagnose_realtime_pull.py
- enrich_intel
- icon
- triage-request.test.mjs
- mountWorkspace
- get_db
- query_abuseipdb
- normalize_tenants
- incidents/view.js
- 5. Information architecture & interaction contracts
- settings.py
- _FakeCursor
- 🚀 Setup & Getting Started
- 6. Arsitektur Data
- setSidebarState
- render
- stats-trust.test.mjs
- Control
- imports/view.js
- 4. Data contracts
- 7. Arsitektur Keamanan
- 8\. Instalasi
- Dokumentasi Arbiter
- feature-loader.test.mjs
- 6.4 Skema database
- 7\. Keamanan
- _review_activity_payload
- 2\. Deskripsi Produk
- 6\. Komponen yang Dipakai
- intel-cache.test.mjs
- suggest_groups
- api_ai_triage_save
- 3\. Workflow
- database-gates.test.mjs
- .test_realtime_pull_respects_custom_severity_and_resets_since_on_severity_change

## God Nodes (most connected - your core abstractions)
1. `esc()` - 102 edges
2. `json()` - 84 edges
3. `get_db()` - 80 edges
4. `icon()` - 72 edges
5. `mount()` - 53 edges
6. `mount()` - 52 edges
7. `AITriageAPITests` - 47 edges
8. `errorState()` - 42 edges
9. `UIAPIContractTests` - 37 edges
10. `mount()` - 35 edges

## Surprising Connections (you probably didn't know these)
- `5.6 AI Triage lokal` --references--> `safe_alerts()`  [INFERRED]
  docs/DOKUMENTASI.md → app/ai_triage.py
- `7.5 Perlindungan data dan ekspor` --references--> `safe_alerts()`  [INFERRED]
  docs/DOKUMENTASI.md → app/ai_triage.py
- `5.7 Alur ekspor` --references--> `export_scope()`  [INFERRED]
  docs/ARSITEKTUR.md → app/main.py
- `4.2 Normalized alert` --references--> `normalize_alert()`  [INFERRED]
  docs/ARCHITECTURE.md → app/core.py
- `8.2 Metode A — Docker standalone (paling cepat)` --references--> `init_database()`  [INFERRED]
  docs/DOKUMENTASI.md → app/database.py

## Import Cycles
- None detected.

## Communities (127 total, 28 thin omitted)

### Community 0 - "test_wazuh_intel.py"
Cohesion: 0.16
Nodes (6): normalize_alert(), extract_active_response(), _active_response(), ActiveResponseReadTests, CorrelationTests, NormalizeIntegrationTests

### Community 1 - "ref_node_assert"
Cohesion: 0.10
Nodes (17): integer(), queryFrom(), rawTenantValues(), scopeDescription(), tenantScope(), url, modelURL, url (+9 more)

### Community 2 - "test_ui_api.py"
Cohesion: 0.09
Nodes (4): create_session_token(), verify_session_token(), load_database(), SchemaMigrationOrderTests

### Community 3 - "stats/view.js"
Cohesion: 0.13
Nodes (37): BENIGN_WHITELIST_PATTERNS, CHART_OPTIONS, distributionPercentages(), drilldownScrollBehavior(), generateMarkdownSummary(), generateStatsCSV(), INJECTION_PATTERNS, isMaliciousAlert() (+29 more)

### Community 4 - "incidents/render.js"
Cohesion: 0.22
Nodes (17): caseHref(), filterIncidents(), SEVERITIES, STATUSES, allOptions(), options(), renderList(), renderWorkspace() (+9 more)

### Community 5 - "state.js"
Cohesion: 0.19
Nodes (17): cleanIds(), draftFrom(), draftsEqual(), evidenceParams(), incidentPayload(), incidentRoute(), selectedIds(), TEXT_FIELDS (+9 more)

### Community 7 - "loadingRows"
Cohesion: 0.07
Nodes (63): ERROR_CODE_CATEGORIES, ERROR_CODE_SECTIONS, ERROR_CODES, filterErrorCodeSections(), mount(), render(), renderSections(), sectionBadge() (+55 more)

### Community 10 - "tenantValues"
Cohesion: 0.17
Nodes (24): FLAG_GROUP_BY_OPTIONS, FLAG_META_MAP, FLAG_TABS, flagBadge(), flagMeta(), flagScopeParams(), GROUP_KEYS, normalizeFlagQuery() (+16 more)

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
Cohesion: 0.09
Nodes (31): check_profile_ready(), get_db(), api_add_exclusion(), api_ai_test(), api_auth_login(), api_auth_logout(), api_create_report_audit_log(), api_database_config() (+23 more)

### Community 17 - "secure_store.py"
Cohesion: 0.36
Nodes (3): _fernet(), _key_path(), _read_or_create_key_file()

### Community 18 - "lookup_remote_ip_cache_detail"
Cohesion: 0.26
Nodes (4): lookup_remote_ip_cache_detail(), _FakeConnection, _psycopg_modules(), RemoteCacheLookupTests

### Community 19 - "with_exclusions"
Cohesion: 0.17
Nodes (11): with_exclusions(), api_database_status(), api_get_monitoring(), _exclusion_document(), _expire_stale_claims(), get_alert_detail(), get_stats(), get_suggestions() (+3 more)

### Community 21 - "enrich_ip"
Cohesion: 0.24
Nodes (4): enrich_ip(), is_private_ip(), is_valid_ip(), EnrichFallbackTests

### Community 22 - "api_get_ai_triage"
Cohesion: 0.09
Nodes (23): current_wib_window_key(), get_triage_state_key(), safe_alerts(), _ai_triage_batch_size(), _ai_triage_candidate_count(), _ai_triage_exclude_ids(), _ai_triage_pick_state(), _ai_triage_progress() (+15 more)

### Community 23 - "Arbiter"
Cohesion: 0.33
Nodes (5): Arbiter, Audience and usage, Development verification, Implemented case policy without schema changes, Product boundaries

### Community 24 - "exports.py"
Cohesion: 0.07
Nodes (14): generate_docx_landscape_report(), generate_gdocs_html_report(), generate_markdown_report(), generate_tsv_table(), generate_xlsx_workbook(), api_list_alert_pulls(), list_jobs(), Arbiter SOC Desk Upgrades Implementation Plan (+6 more)

### Community 25 - "mount"
Cohesion: 0.09
Nodes (57): aiSeverityKey(), alertFacts(), alertIndex(), boundedInteger(), DEFAULT_BATCH, formatWibWindowLabel(), GROUP_BY_OPTIONS, groupAlerts() (+49 more)

### Community 26 - "re"
Cohesion: 0.12
Nodes (12): build_log_signature(), extract_alerts(), first_ip_in(), kv_details(), normalize_log_for_signature(), parse_export(), parse_log_line(), parse_timestamp_iso() (+4 more)

### Community 27 - "db"
Cohesion: 0.06
Nodes (35): build, container_name, environment, network_mode, restart, volumes, context, dockerfile (+27 more)

### Community 28 - "📋 Protokol Eksekusi Rinci"
Cohesion: 0.13
Nodes (14): 1. Inisialisasi Task Otomatis (`todo_list`), 1. Mode Maksimal (`/work`) — Autonomous Deep Engineering Mode, 2. Mode Normal (Tanpa `/work`), 2. Proaktif Menggunakan Skills & Subagents, 3. Pelacakan Jahitan Data Ujung-ke-Ujung (*Trace Every Seam*), 4. Pengujian Kasus Negatif (Bukan Cuma Kasus Ideal), 5. Verifikasi Lingkungan & Container, 6. Anti-Pengerdilan Data (Zero Artificial Truncation) (+6 more)

### Community 29 - "File Map and Interfaces"
Cohesion: 0.17
Nodes (9): Alert Statistics & Pivot Implementation Plan, File Map and Interfaces, Global Constraints, Review Focus, Self-Review, Task 2: Build SQL aggregation endpoints and schema support, Task 4: Add the compact Triage filter-summary strip, Task 5: Add approved post-core statistics enhancements (+1 more)

### Community 30 - "SettingsAPITests"
Cohesion: 0.06
Nodes (6): API Conventions — Arbiter, Credential redaction, Errors, SettingsAPITests, __init__(), __init__()

### Community 31 - "test_pull_jobs.py"
Cohesion: 0.11
Nodes (7): base_config(), fake_get_db(), FakeConnection, FakeTransaction, load_pull_jobs(), PullJobTests, wait_for()

### Community 32 - "app.js"
Cohesion: 0.07
Nodes (26): adminOnlyPages, checkPullActivity(), health(), help, main, navigationMemory, pageTitles, pullActivity (+18 more)

### Community 33 - "errorState"
Cohesion: 0.19
Nodes (15): databaseIdentity(), summarizeTelemetryRange(), mount(), loadStatus(), maintain(), render(), switchTo(), PRESET_LABELS (+7 more)

### Community 34 - "exclusions.py"
Cohesion: 0.16
Nodes (10): active_exclusion_rules(), build_exclusion_sql(), _coerce_enabled(), _escape_like(), glob_to_like(), normalize_exclusion_rule(), normalize_exclusions(), parse_wazuh_exclusion() (+2 more)

### Community 36 - "database-workspace.test.mjs"
Cohesion: 0.22
Nodes (11): createNavigationMemory(), paramsForScope(), scopeKey(), normalizeSidebarState(), readSidebarState(), SIDEBAR_KEY, toggleSidebarState(), writeSidebarState() (+3 more)

### Community 37 - "_cluster_alerts"
Cohesion: 0.19
Nodes (4): ai_triage(), _cluster_alerts(), _cluster_prompt(), _validate_cluster_verdicts()

### Community 38 - "reports/view.js"
Cohesion: 0.21
Nodes (20): /review — Code review pass, renderControls(), tenantOptionsHTML(), caseReportRoute(), createReportSession(), exportURL(), reportAction(), reportScope() (+12 more)

### Community 40 - "json"
Cohesion: 0.18
Nodes (25): ApiError, apiURL(), copyHTML(), copyText(), download(), json(), request(), mount() (+17 more)

### Community 41 - "main.py"
Cohesion: 0.11
Nodes (27): init_database(), api_alert_pull_cancel(), api_alert_pull_status(), api_flags_alerts(), api_flags_groups(), api_list_wazuh_queries(), _build_flag_scope_where(), export_csv() (+19 more)

### Community 42 - "Arsitektur Arbiter — Web & Tools"
Cohesion: 0.15
Nodes (13): 10. Failure Modes dan Degradasi, 11. Keputusan Arsitektur dan Trade-off, 12. Batas Skalabilitas, 13. Peta Direktori Arsitektural, 14. Cara Memverifikasi Arsitektur, 15. Ringkasan Arsitektur, 1. Gaya Arsitektur, 2. Diagram Konteks (C4 Level 1) (+5 more)

### Community 43 - "ai_triage.py"
Cohesion: 0.13
Nodes (17): _alert_tenant(), _as_mapping(), format_wib_window_label(), _group_by_indicators(), find(), union(), _group_by_rule_description(), heuristic_triage() (+9 more)

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

### Community 53 - "withParams"
Cohesion: 0.30
Nodes (9): renderMonitoringDashboard(), renderReviewActivity(), ROLE_LABELS, mount(), load(), loadBatchIncidentOptions(), report(), updateQuery() (+1 more)

### Community 54 - "database.py"
Cohesion: 0.08
Nodes (31): _batch_insert_values(), _batch_instance(), bump_daily_metrics(), _clean_expired_previews_locked(), create_preview_token(), get_active_profile(), get_active_profile_id(), get_database_status() (+23 more)

### Community 55 - "load_isolated_api"
Cohesion: 0.18
Nodes (5): Backend (safe isolated suites), Design lint, Frontend, Testing — Arbiter, load_isolated_api()

### Community 56 - "6. Correlation policy"
Cohesion: 0.40
Nodes (5): 6.1 Response linkage, 6.2 Canonical group identity, 6.3 Ordered chain, 6.4 Correlation confidence, 6. Correlation policy

### Community 57 - "Control"
Cohesion: 0.22
Nodes (3): click(), Control, fixture()

### Community 58 - "wazuh_intel.py"
Cohesion: 0.27
Nodes (14): as_dict(), clean_val(), parse_to_datetime(), _alert_key(), _as_json(), build_attack_chains(), _chain_steps(), correlate_alerts() (+6 more)

### Community 59 - "5\. Cara Kerja"
Cohesion: 0.20
Nodes (10): 5.1 Ingesti dan parsing, 5.2 Normalisasi, 5.3 Deduplikasi, 5.4 Klasifikasi, 5.5 Korelasi, 5.6 AI Triage lokal, 5.7 Triage dan insiden, 5.8 Threat intelligence dan redaksi (+2 more)

### Community 61 - "wazuh_search"
Cohesion: 0.08
Nodes (7): api_realtime_pull(), api_start_alert_pull(), _normalize_wazuh_timestamp(), _valid_timestamp(), wazuh_count(), _wazuh_opener(), wazuh_search()

### Community 62 - "createRouter"
Cohesion: 0.67
Nodes (3): createRouter(), change(), parseRoute()

### Community 63 - "⚡ Key Capabilities"
Cohesion: 0.17
Nodes (12): 10. Privacy-First Redactor, 11. Official Deliverables (5 Export Paths), 1. Resilient Multi-Format Ingestion, 2. High-Precision Log Dissector (No False Fields), 3. Signature-Based Deduplication & Causal Correlation, 4. Enterprise Multi-Tenant Architecture, 5. Modular Destination UI, 6. Local AI Triage & Persistent Daily Case Grouping (`#/ai-triage`) (+4 more)

### Community 64 - "Arbiter Architecture — Wazuh Read, Classify, Correlate"
Cohesion: 0.13
Nodes (15): 10. Acceptance tests, 11. Non-goals, 1. Design constraints, 2. Dataset evidence used to shape the architecture, 3. End-to-end pipeline, 5.1 Curated rule profiles (explicit, not trained), 5.2 Context signals, 5.3 Wording policy (+7 more)

### Community 65 - "intel.py"
Cohesion: 0.13
Nodes (10): _enrich_single_public_live(), extract_alert_intel_context(), has_usable_sidecar_cache(), _json_object(), _json_value(), lookup_remote_ip_cache(), normalize_sidecar_record(), query_virustotal_ip() (+2 more)

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

### Community 74 - "classify_alert"
Cohesion: 0.21
Nodes (7): _bump(), classify_alert(), _intel_context(), _known_bad(), _level_priority(), _profile_for(), ClassificationTests

### Community 76 - "secure_store.py"
Cohesion: 0.32
Nodes (11): authenticate_user(), create_user(), _default_admin_credentials(), delete_user(), get_user(), _hash_password(), _load_raw_users(), sanitize_user() (+3 more)

### Community 77 - "LocalAIUnavailable"
Cohesion: 0.24
Nodes (5): local_ai_suggest_groups(), LocalAIUnavailable, ollama_request(), suggestions_with_fallback(), 5.5 Alur korelasi dan sugesti

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

### Community 87 - "enrich_ips_with_sidecar"
Cohesion: 0.13
Nodes (9): enrich_ips_with_sidecar(), fetch_sidecar_cache(), is_cdn_edge(), normalize_ip_address(), parse_sidecar_candidates(), probe_sidecar(), query_geo_batch(), save_sidecar_intel() (+1 more)

### Community 88 - "diagnose_realtime_pull.py"
Cohesion: 0.38
Nodes (3): _fmt(), main(), _existing()

### Community 89 - "enrich_intel"
Cohesion: 0.16
Nodes (6): _remote_profile_read_only(), _resolve_remote_db_url(), sync_remote_cache(), upsert_ip_cache(), enrich_intel(), RemoteSyncTests

### Community 90 - "icon"
Cohesion: 0.15
Nodes (25): save(), claimBadge(), intelBadge(), intelSummary(), renderQueue(), renderTriageSummary(), summaryRequestParams(), chainLine() (+17 more)

### Community 91 - "triage-request.test.mjs"
Cohesion: 0.13
Nodes (3): createSelection(), Element, requestsFor()

### Community 92 - "mountWorkspace"
Cohesion: 0.41
Nodes (12): renderEvidence(), mountWorkspace(), context(), initial(), loadPage(), loadSelected(), panels(), refresh() (+4 more)

### Community 93 - "get_db"
Cohesion: 0.18
Nodes (20): list_users(), api_auth_me(), api_create_user(), api_delete_user(), api_flag_alerts(), api_flag_single_alert(), api_flags_rule_status(), api_list_users() (+12 more)

### Community 94 - "query_abuseipdb"
Cohesion: 0.29
Nodes (3): AbuseIPDBError, query_abuseipdb(), fake_abuse()

### Community 95 - "normalize_tenants"
Cohesion: 0.12
Nodes (23): Agent: code-reviewer, Agent: security-auditor, Tenant scoping, add_group_members(), api_flags_summary(), batch_update_review(), delete_group(), export_scope() (+15 more)

### Community 96 - "incidents/view.js"
Cohesion: 0.21
Nodes (3): context(), load(), SyntheticRoot

### Community 97 - "5. Information architecture & interaction contracts"
Cohesion: 0.40
Nodes (5): 5. Information architecture & interaction contracts, Accessibility, Editing dan destructive actions, Refresh, Scope

### Community 99 - "settings.py"
Cohesion: 0.09
Nodes (23): _load_profile_overrides(), api_realtime_count(), decrypt_text(), encrypt_text(), is_encrypted(), SecretStoreError, _boolean(), _deep_merge() (+15 more)

### Community 101 - "🚀 Setup & Getting Started"
Cohesion: 0.33
Nodes (6): Connecting to a Neuropetra `ip_intel` database, Method A: Standalone Docker Setup (Fastest for new users), Method B: Host Mode (Connect to existing PostgreSQL / IP Intel), Method C: Local Python Setup (Without Docker), Prerequisites, 🚀 Setup & Getting Started

### Community 102 - "6. Arsitektur Data"
Cohesion: 0.40
Nodes (5): 6.1 ERD, 6.2 Penyimpanan JSONB, 6.3 Indeks, 6.4 Kepemilikan data, 6. Arsitektur Data

### Community 103 - "setSidebarState"
Cohesion: 0.40
Nodes (5): applyWorkspaceSettings(), closeNav(), loadWorkspaceSettings(), paintRealtime(), setSidebarState()

### Community 104 - "render"
Cohesion: 0.29
Nodes (11): applyUserPermissions(), canLeave(), checkFlagSummary(), databaseChanged(), notify(), render(), renderLoginGate(), renderTenantOptions() (+3 more)

### Community 105 - "stats-trust.test.mjs"
Cohesion: 0.28
Nodes (4): flush(), harness(), startSample(), stats()

### Community 106 - "Control"
Cohesion: 0.22
Nodes (3): click(), Control, fixture()

### Community 108 - "imports/view.js"
Cohesion: 0.27
Nodes (6): createImportSession(), importPage(), importResult(), mount(), update(), moduleURL

### Community 109 - "4. Data contracts"
Cohesion: 0.50
Nodes (4): 4.1 Raw Wazuh alert (minimum), 4.2 Normalized alert, 4.3 Classification result, 4. Data contracts

### Community 110 - "7. Arsitektur Keamanan"
Cohesion: 0.50
Nodes (4): 7.1 Trust boundary, 7.2 Kontrol keamanan per lapisan, 7.3 Batas yang harus dijaga saat deployment, 7. Arsitektur Keamanan

### Community 111 - "8\. Instalasi"
Cohesion: 0.20
Nodes (10): 8.1 Prasyarat, 8.2 Metode A — Docker standalone (paling cepat), 8.3 Metode B — Host mode (PostgreSQL yang sudah ada), 8.4 Metode C — Python lokal tanpa Docker, 8.5 Konfigurasi Wazuh Indexer (opsional, untuk Realtime), 8.6 Konfigurasi AI lokal (opsional), 8.7 Login pertama, 8.8 Verifikasi instalasi (+2 more)

### Community 112 - "Dokumentasi Arbiter"
Cohesion: 0.22
Nodes (9): 10\. Pengembangan dan Pemeliharaan, 11\. Lisensi, 1\. Ringkasan, 4.1 Alur end-to-end, 4.2 Pemisahan peran event, 4.3 Batas kepercayaan (trust boundary), 4\. Flowchart, 9\. Troubleshooting (+1 more)

### Community 114 - "6.4 Skema database"
Cohesion: 0.22
Nodes (9): 6.4.1 `wazuh.alerts`, 6.4.2 `wazuh.analysis_groups`, 6.4.3 `wazuh.alert_group_members`, 6.4.4 `wazuh.app_settings`, 6.4.5 `public.ip_intel_cache`, 6.4.6 Tabel Remote milik provider, 6.4.7 Indeks performa, 6.4.8 Catatan operasional (+1 more)

### Community 115 - "7\. Keamanan"
Cohesion: 0.29
Nodes (7): 7.1 Prinsip desain, 7.2 Autentikasi dan otorisasi, 7.3 Rahasia saat istirahat, 7.4 Isolasi jaringan dan SSRF, 7.5 Perlindungan data dan ekspor, 7.6 Batasan keamanan yang perlu diketahui, 7\. Keamanan

### Community 116 - "_review_activity_payload"
Cohesion: 0.33
Nodes (3): review_activity(), _review_activity_payload(), _review_local_date()

### Community 117 - "2\. Deskripsi Produk"
Cohesion: 0.40
Nodes (5): 2.1 Untuk siapa, 2.2 Batas produk, 2.3 Destinasi aplikasi, 2.4 Kemampuan inti, 2\. Deskripsi Produk

### Community 118 - "6\. Komponen yang Dipakai"
Cohesion: 0.40
Nodes (5): 6.1 Stack, 6.2 Modul backend, 6.3 Modul frontend, 6.5 Kelompok endpoint API, 6\. Komponen yang Dipakai

### Community 119 - "intel-cache.test.mjs"
Cohesion: 0.40
Nodes (4): mainPy, root, settingsView, triageView

### Community 122 - "3\. Workflow"
Cohesion: 0.50
Nodes (4): 3.1 Workflow analis (harian), 3.2 Workflow data, 3.3 Siklus hidup insiden, 3\. Workflow

## Knowledge Gaps
- **28 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `esc()` connect `reports/view.js` to `stats/view.js`, `incidents/render.js`, `state.js`, `loadingRows`, `tenantValues`, `mount`, `app.js`, `errorState`, `json`, `Arsitektur Arbiter — Web & Tools`, `withParams`, `Code Style — Arbiter`, `icon`, `mountWorkspace`, `normalize_tenants`, `render`, `imports/view.js`, `7. Arsitektur Keamanan`, `6\. Komponen yang Dipakai`?**
  _High betweenness centrality (0.265) - this node is a cross-community bridge._
- **Are the 6 inferred relationships involving `esc()` (e.g. with `Agent: code-reviewer` and `/review — Code review pass`) actually correct?**
  _`esc()` has 6 INFERRED edges - model-reasoned connections that need verification._
- **Should `ref_node_assert` be split into smaller, more focused modules?**
  _Cohesion score 0.10384068278805121 - nodes in this community are weakly interconnected._
- **Why does `Agent: code-reviewer` connect `normalize_tenants` to `reports/view.js`?**
  _High betweenness centrality (0.123) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `json()` (e.g. with `mount()` and `loadSelected()`) actually correct?**
  _`json()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Should `test_ui_api.py` be split into smaller, more focused modules?**
  _Cohesion score 0.08585858585858586 - nodes in this community are weakly interconnected._
- **Why does `safe_alerts()` connect `api_get_ai_triage` to `main.py`, `ai_triage.py`, `7. Arsitektur Keamanan`, `7\. Keamanan`, `5\. Cara Kerja`?**
  _High betweenness centrality (0.111) - this node is a cross-community bridge._