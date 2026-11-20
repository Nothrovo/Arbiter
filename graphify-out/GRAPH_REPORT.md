# Graph Report - Arbiter  (2026-11-20)

## Corpus Check
- 170 files · ~166,176 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 15 file(s) not represented in the graph (top: .css 5, (none) 4, .woff2 4)

## Summary
- 2055 nodes · 5348 edges · 117 communities (94 shown, 23 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 153 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `4ae74eb5`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- withParams
- ref_node_assert
- stats/view.js
- esc
- incidents/render.js
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
- main.py
- test_settings.py
- lookup_remote_ip_cache_detail
- Request
- SafetyTests
- enrich_ip
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
- _http_error_reason
- database-workspace.test.mjs
- test_wazuh_connection
- reports/view.js
- FlagWorkspaceTests
- mount
- _review_activity_payload
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
- 6. Correlation policy
- Control
- wazuh_intel.py
- 5\. Cara Kerja
- sanitize_text
- test_settings.py
- Testing — Arbiter
- ⚡ Key Capabilities
- Arbiter Architecture — Wazuh Read, Classify, Correlate
- intel.py
- _safe_remote_cache_error
- package.json
- ExclusionAPITests
- build
- Deploy config reference
- 5. Arsitektur Tools (Backend)
- Code Style — Arbiter
- Deploy Arbiter
- api_intel_sidecar_test
- wazuh-queries/model.js
- secure_store.py
- json
- 4. Arsitektur Web (Frontend)
- 8. Roadmap implementasi, tiap tahap bisa diverifikasi
- fix-issue.md
- validate-bash.sh
- setup-ai-symlinks.sh
- 8. Deployment
- Arbiter
- 4. Wireframe dan first viewport
- init_database
- load_settings
- enrich_intel
- filters.js
- triage-request.test.mjs
- query_abuseipdb
- get_db
- 5. Information architecture & interaction contracts
- settings.py
- _FakeCursor
- 🚀 Setup & Getting Started
- 6. Arsitektur Data
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
- 2\. Deskripsi Produk
- 6\. Komponen yang Dipakai
- 3\. Workflow
- router-history.test.mjs

## God Nodes (most connected - your core abstractions)
1. `esc()` - 103 edges
2. `json()` - 86 edges
3. `get_db()` - 81 edges
4. `icon()` - 72 edges
5. `mount()` - 53 edges
6. `mount()` - 52 edges
7. `AITriageAPITests` - 47 edges
8. `errorState()` - 42 edges
9. `UIAPIContractTests` - 38 edges
10. `mount()` - 35 edges

## Surprising Connections (you probably didn't know these)
- `5.7 Alur ekspor` --references--> `export_scope()`  [INFERRED]
  docs/ARSITEKTUR.md → app/main.py
- `5.8 Profil database dan pemeliharaan` --references--> `get_db()`  [INFERRED]
  docs/ARSITEKTUR.md → app/database.py
- `5.6 AI Triage lokal` --references--> `safe_alerts()`  [INFERRED]
  docs/DOKUMENTASI.md → app/ai_triage.py
- `7.5 Perlindungan data dan ekspor` --references--> `safe_alerts()`  [INFERRED]
  docs/DOKUMENTASI.md → app/ai_triage.py
- `Frontend (JS)` --references--> `esc()`  [INFERRED]
  .ai/rules/code-style.md → app/static/js/ui/primitives.js

## Import Cycles
- None detected.

## Communities (117 total, 23 thin omitted)

### Community 0 - "withParams"
Cohesion: 0.23
Nodes (13): triageLinkFor(), renderMonitoringDashboard(), renderReviewActivity(), renderReviewerFilter(), ROLE_LABELS, mount(), load(), loadBatchIncidentOptions() (+5 more)

### Community 1 - "ref_node_assert"
Cohesion: 0.09
Nodes (24): parseFilters(), scopeKey(), choices(), integer(), queryFrom(), rawTenantValues(), scopeDescription(), scopeParams() (+16 more)

### Community 3 - "stats/view.js"
Cohesion: 0.13
Nodes (36): BENIGN_WHITELIST_PATTERNS, CHART_OPTIONS, distributionPercentages(), drilldownScrollBehavior(), generateMarkdownSummary(), generateStatsCSV(), INJECTION_PATTERNS, isMaliciousAlert() (+28 more)

### Community 4 - "esc"
Cohesion: 0.14
Nodes (26): /review — Code review pass, copyText(), notify(), save(), ERROR_CODE_CATEGORIES, ERROR_CODE_SECTIONS, ERROR_CODES, filterErrorCodeSections() (+18 more)

### Community 5 - "incidents/render.js"
Cohesion: 0.07
Nodes (47): caseHref(), cleanIds(), draftFrom(), draftsEqual(), evidenceParams(), filterIncidents(), incidentPayload(), incidentRoute() (+39 more)

### Community 7 - "loadingRows"
Cohesion: 0.11
Nodes (44): formatDuration(), mount(), paint(), paintProgress(), poll(), pollLater(), resumeJob(), stopPolling() (+36 more)

### Community 8 - "AITriageAPITests"
Cohesion: 0.04
Nodes (3): _validate_cluster_verdicts(), AITriageAPITests, fake_search()

### Community 10 - "tenantValues"
Cohesion: 0.14
Nodes (33): ApiError, copyHTML(), download(), request(), FLAG_EXPORT_FORMATS, FLAG_EXPORT_KEYS, FLAG_GROUP_BY_OPTIONS, FLAG_META_MAP (+25 more)

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

### Community 16 - "main.py"
Cohesion: 0.06
Nodes (37): check_profile_ready(), ingest_alert_with_dedup(), normalize_exclusion_rule(), parse_wazuh_exclusion(), api_add_exclusion(), api_ai_test(), api_ai_triage_save(), api_alert_pull_cancel() (+29 more)

### Community 17 - "test_settings.py"
Cohesion: 0.21
Nodes (7): _verify_password(), decrypt_text(), _fernet(), is_encrypted(), _key_path(), _read_or_create_key_file(), SecretStoreError

### Community 18 - "lookup_remote_ip_cache_detail"
Cohesion: 0.15
Nodes (5): lookup_remote_ip_cache_detail(), _FakeConnection, _FakeResult, _psycopg_modules(), RemoteCacheLookupTests

### Community 19 - "Request"
Cohesion: 0.26
Nodes (12): list_users(), api_auth_me(), api_create_user(), api_delete_user(), api_list_users(), api_save_wazuh_query(), api_update_user(), api_update_wazuh_notepad() (+4 more)

### Community 21 - "enrich_ip"
Cohesion: 0.24
Nodes (4): enrich_ip(), is_private_ip(), is_valid_ip(), EnrichFallbackTests

### Community 22 - "Any"
Cohesion: 0.08
Nodes (34): current_wib_window_key(), get_triage_state_key(), safe_alerts(), with_exclusions(), _ai_triage_batch_size(), _ai_triage_candidate_count(), _ai_triage_exclude_ids(), _ai_triage_pick_state() (+26 more)

### Community 23 - "Arbiter"
Cohesion: 0.33
Nodes (5): Arbiter, Audience and usage, Development verification, Implemented case policy without schema changes, Product boundaries

### Community 24 - "exports.py"
Cohesion: 0.06
Nodes (49): alert_full_log(), _as_dict(), _evidence_fields(), export_row(), export_rows(), _first(), _flat(), generate_docx_landscape_report() (+41 more)

### Community 25 - "mount"
Cohesion: 0.12
Nodes (43): aiSeverityKey(), alertFacts(), alertIndex(), boundedInteger(), DEFAULT_BATCH, formatWibWindowLabel(), GROUP_BY_OPTIONS, groupAlerts() (+35 more)

### Community 26 - "re"
Cohesion: 0.11
Nodes (15): normalize_alert(), build_log_signature(), extract_alerts(), first_ip_in(), kv_details(), normalize_log_for_signature(), parse_export(), parse_log_line() (+7 more)

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
Cohesion: 0.07
Nodes (31): adminOnlyPages, applyWorkspaceSettings(), checkPullActivity(), closeNav(), health(), help, loadWorkspaceSettings(), main (+23 more)

### Community 33 - "errorState"
Cohesion: 0.15
Nodes (21): json(), databaseIdentity(), summarizeTelemetryRange(), mount(), loadStatus(), maintain(), render(), switchTo() (+13 more)

### Community 34 - "exclusions.py"
Cohesion: 0.19
Nodes (6): active_exclusion_rules(), build_exclusion_sql(), _escape_like(), glob_to_like(), _split_top_level(), _strip_outer_parentheses()

### Community 35 - "_http_error_reason"
Cohesion: 0.13
Nodes (4): _http_error_reason(), _wazuh_request(), __init__(), __init__()

### Community 36 - "database-workspace.test.mjs"
Cohesion: 0.29
Nodes (9): createNavigationMemory(), normalizeSidebarState(), readSidebarState(), SIDEBAR_KEY, toggleSidebarState(), writeSidebarState(), shell(), source (+1 more)

### Community 37 - "test_wazuh_connection"
Cohesion: 0.18
Nodes (3): api_test_wazuh(), test_wazuh_connection(), _wazuh_opener()

### Community 38 - "reports/view.js"
Cohesion: 0.27
Nodes (15): caseReportRoute(), createReportSession(), exportURL(), reportAction(), reportScope(), groupOptions(), reportFallback(), reportPage() (+7 more)

### Community 40 - "mount"
Cohesion: 0.12
Nodes (35): apiURL(), intelBadge(), intelSummary(), renderQueue(), renderTriageSummary(), summaryRequestParams(), chainLine(), classificationBlock() (+27 more)

### Community 41 - "_review_activity_payload"
Cohesion: 0.33
Nodes (3): review_activity(), _review_activity_payload(), _review_local_date()

### Community 42 - "Arsitektur Arbiter — Web & Tools"
Cohesion: 0.15
Nodes (13): 10. Failure Modes dan Degradasi, 11. Keputusan Arsitektur dan Trade-off, 12. Batas Skalabilitas, 13. Peta Direktori Arsitektural, 14. Cara Memverifikasi Arsitektur, 15. Ringkasan Arsitektur, 1. Gaya Arsitektur, 2. Diagram Konteks (C4 Level 1) (+5 more)

### Community 43 - "ai_triage.py"
Cohesion: 0.12
Nodes (21): Backend (safe isolated suites), ai_triage(), _alert_tenant(), _as_mapping(), _cluster_alerts(), _cluster_prompt(), format_wib_window_label(), _group_by_indicators() (+13 more)

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
Cohesion: 0.08
Nodes (31): _batch_insert_values(), _batch_instance(), _clean_expired_previews_locked(), create_preview_token(), get_active_profile(), get_active_profile_id(), get_database_status(), get_database_status_unavailable() (+23 more)

### Community 55 - "SyntheticDB"
Cohesion: 0.12
Nodes (5): Task 2: Build SQL aggregation endpoints and schema support, load_database(), TriageScopeTests, load_isolated_api(), SyntheticDB

### Community 56 - "6. Correlation policy"
Cohesion: 0.40
Nodes (5): 6.1 Response linkage, 6.2 Canonical group identity, 6.3 Ordered chain, 6.4 Correlation confidence, 6. Correlation policy

### Community 57 - "Control"
Cohesion: 0.22
Nodes (3): click(), Control, fixture()

### Community 58 - "wazuh_intel.py"
Cohesion: 0.11
Nodes (25): as_dict(), clean_val(), _alert_key(), _as_json(), build_attack_chains(), _bump(), _chain_steps(), classify_alert() (+17 more)

### Community 59 - "5\. Cara Kerja"
Cohesion: 0.20
Nodes (10): 5.1 Ingesti dan parsing, 5.2 Normalisasi, 5.3 Deduplikasi, 5.4 Klasifikasi, 5.5 Korelasi, 5.6 AI Triage lokal, 5.7 Triage dan insiden, 5.8 Threat intelligence dan redaksi (+2 more)

### Community 61 - "test_settings.py"
Cohesion: 0.14
Nodes (4): api_start_alert_pull(), _normalize_wazuh_timestamp(), _valid_timestamp(), wazuh_count()

### Community 62 - "Testing — Arbiter"
Cohesion: 0.50
Nodes (3): Design lint, Frontend, Testing — Arbiter

### Community 63 - "⚡ Key Capabilities"
Cohesion: 0.17
Nodes (12): 10. Privacy-First Redactor, 11. Official Deliverables (5 Export Paths), 1. Resilient Multi-Format Ingestion, 2. High-Precision Log Dissector (No False Fields), 3. Signature-Based Deduplication & Causal Correlation, 4. Enterprise Multi-Tenant Architecture, 5. Modular Destination UI, 6. Local AI Triage & Persistent Daily Case Grouping (`#/ai-triage`) (+4 more)

### Community 64 - "Arbiter Architecture — Wazuh Read, Classify, Correlate"
Cohesion: 0.13
Nodes (15): 10. Acceptance tests, 11. Non-goals, 1. Design constraints, 2. Dataset evidence used to shape the architecture, 3. End-to-end pipeline, 5.1 Curated rule profiles (explicit, not trained), 5.2 Context signals, 5.3 Wording policy (+7 more)

### Community 65 - "intel.py"
Cohesion: 0.12
Nodes (16): _coerce_enabled(), normalize_exclusions(), enrich_ips_with_sidecar(), _enrich_single_public_live(), extract_alert_intel_context(), fetch_sidecar_cache(), has_usable_sidecar_cache(), is_cdn_edge() (+8 more)

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

### Community 74 - "api_intel_sidecar_test"
Cohesion: 0.29
Nodes (4): normalize_ip_address(), parse_sidecar_candidates(), probe_sidecar(), api_intel_sidecar_test()

### Community 75 - "wazuh-queries/model.js"
Cohesion: 0.33
Nodes (6): buildWazuhQueries(), parseSeverityBounds(), PRESET_CATEGORIES, PRESET_WAZUH_QUERIES, QUERY_SEVERITY_OPTIONS, QUERY_TIME_OPTIONS

### Community 76 - "secure_store.py"
Cohesion: 0.30
Nodes (13): authenticate_user(), create_session_token(), create_user(), _default_admin_credentials(), delete_user(), get_user(), _hash_password(), _load_raw_users() (+5 more)

### Community 77 - "json"
Cohesion: 0.13
Nodes (6): local_ai_suggest_groups(), LocalAIUnavailable, ollama_request(), suggest_groups(), suggestions_with_fallback(), is_malicious_alert_record()

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

### Community 87 - "init_database"
Cohesion: 0.40
Nodes (3): init_database(), _load_profile_overrides(), 8.2 Metode A — Docker standalone (paling cepat)

### Community 88 - "load_settings"
Cohesion: 0.12
Nodes (11): API Conventions — Arbiter, Credential redaction, Errors, api_realtime_count(), load_settings(), migrate_settings(), wazuh_password(), wazuh_search() (+3 more)

### Community 89 - "enrich_intel"
Cohesion: 0.16
Nodes (6): _remote_profile_read_only(), _resolve_remote_db_url(), sync_remote_cache(), upsert_ip_cache(), enrich_intel(), RemoteSyncTests

### Community 90 - "filters.js"
Cohesion: 0.24
Nodes (15): escapeAttr(), escapeHtml(), FIELD_LABELS, FILTER_FIELDS, FILTER_OPS, filterBuilderHTML(), filterLabel(), filterOpOptions() (+7 more)

### Community 91 - "triage-request.test.mjs"
Cohesion: 0.13
Nodes (3): createSelection(), Element, requestsFor()

### Community 94 - "query_abuseipdb"
Cohesion: 0.29
Nodes (3): AbuseIPDBError, query_abuseipdb(), fake_abuse()

### Community 95 - "get_db"
Cohesion: 0.08
Nodes (41): Agent: code-reviewer, Agent: security-auditor, Tenant scoping, bump_daily_metrics(), get_db(), add_group_members(), api_database_status(), api_flag_alerts() (+33 more)

### Community 97 - "5. Information architecture & interaction contracts"
Cohesion: 0.40
Nodes (5): 5. Information architecture & interaction contracts, Accessibility, Editing dan destructive actions, Refresh, Scope

### Community 99 - "settings.py"
Cohesion: 0.17
Nodes (11): _boolean(), _deep_merge(), default_settings(), intel_abuseipdb_key(), intel_virustotal_key(), _is_local_or_lan_host(), normalize_ollama_base_url(), normalize_sidecar_urls() (+3 more)

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

### Community 109 - "4. Data contracts"
Cohesion: 0.50
Nodes (4): 4.1 Raw Wazuh alert (minimum), 4.2 Normalized alert, 4.3 Classification result, 4. Data contracts

### Community 110 - "7. Arsitektur Keamanan"
Cohesion: 0.50
Nodes (4): 7.1 Trust boundary, 7.2 Kontrol keamanan per lapisan, 7.3 Batas yang harus dijaga saat deployment, 7. Arsitektur Keamanan

### Community 111 - "8\. Instalasi"
Cohesion: 0.22
Nodes (9): 8.1 Prasyarat, 8.3 Metode B — Host mode (PostgreSQL yang sudah ada), 8.4 Metode C — Python lokal tanpa Docker, 8.5 Konfigurasi Wazuh Indexer (opsional, untuk Realtime), 8.6 Konfigurasi AI lokal (opsional), 8.7 Login pertama, 8.8 Verifikasi instalasi, 8.9 Variabel lingkungan (+1 more)

### Community 112 - "Dokumentasi Arbiter"
Cohesion: 0.22
Nodes (9): 10\. Pengembangan dan Pemeliharaan, 11\. Lisensi, 1\. Ringkasan, 4.1 Alur end-to-end, 4.2 Pemisahan peran event, 4.3 Batas kepercayaan (trust boundary), 4\. Flowchart, 9\. Troubleshooting (+1 more)

### Community 114 - "6.4 Skema database"
Cohesion: 0.25
Nodes (8): 6.4.1 `wazuh.alerts`, 6.4.2 `wazuh.analysis_groups`, 6.4.3 `wazuh.alert_group_members`, 6.4.5 `public.ip_intel_cache`, 6.4.6 Tabel Remote milik provider, 6.4.7 Indeks performa, 6.4.8 Catatan operasional, 6.4 Skema database

### Community 115 - "7\. Keamanan"
Cohesion: 0.29
Nodes (7): 7.1 Prinsip desain, 7.2 Autentikasi dan otorisasi, 7.3 Rahasia saat istirahat, 7.4 Isolasi jaringan dan SSRF, 7.5 Perlindungan data dan ekspor, 7.6 Batasan keamanan yang perlu diketahui, 7\. Keamanan

### Community 117 - "2\. Deskripsi Produk"
Cohesion: 0.40
Nodes (5): 2.1 Untuk siapa, 2.2 Batas produk, 2.3 Destinasi aplikasi, 2.4 Kemampuan inti, 2\. Deskripsi Produk

### Community 118 - "6\. Komponen yang Dipakai"
Cohesion: 0.40
Nodes (5): 6.1 Stack, 6.2 Modul backend, 6.3 Modul frontend, 6.5 Kelompok endpoint API, 6\. Komponen yang Dipakai

### Community 122 - "3\. Workflow"
Cohesion: 0.50
Nodes (4): 3.1 Workflow analis (harian), 3.2 Workflow data, 3.3 Siklus hidup insiden, 3\. Workflow

### Community 124 - "router-history.test.mjs"
Cohesion: 0.29
Nodes (3): createRouter(), change(), parseRoute()

## Knowledge Gaps
- **23 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `esc()` connect `esc` to `app.js`, `errorState`, `withParams`, `stats/view.js`, `incidents/render.js`, `reports/view.js`, `loadingRows`, `Code Style — Arbiter`, `render`, `tenantValues`, `mount`, `imports/view.js`, `Arsitektur Arbiter — Web & Tools`, `7. Arsitektur Keamanan`, `6\. Komponen yang Dipakai`, `mount`, `get_db`?**
  _High betweenness centrality (0.227) - this node is a cross-community bridge._
- **Are the 6 inferred relationships involving `esc()` (e.g. with `Agent: code-reviewer` and `/review — Code review pass`) actually correct?**
  _`esc()` has 6 INFERRED edges - model-reasoned connections that need verification._
- **Should `ref_node_assert` be split into smaller, more focused modules?**
  _Cohesion score 0.09302325581395349 - nodes in this community are weakly interconnected._
- **Why does `safe_alerts()` connect `Any` to `ai_triage.py`, `7. Arsitektur Keamanan`, `main.py`, `7\. Keamanan`, `5\. Cara Kerja`?**
  _High betweenness centrality (0.108) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `json()` (e.g. with `mount()` and `loadSelected()`) actually correct?**
  _`json()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Should `test_ui_api.py` be split into smaller, more focused modules?**
  _Cohesion score 0.1282051282051282 - nodes in this community are weakly interconnected._
- **Why does `Agent: code-reviewer` connect `get_db` to `esc`?**
  _High betweenness centrality (0.107) - this node is a cross-community bridge._