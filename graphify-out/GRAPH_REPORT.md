# Graph Report - Arbiter  (2026-11-20)

## Corpus Check
- 170 files · ~170,934 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 15 file(s) not represented in the graph (top: .css 5, (none) 4, .woff2 4)

## Summary
- 2082 nodes · 5477 edges · 117 communities (91 shown, 26 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 153 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `2374da61`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- triage/view.js
- ref_node_assert
- test_ui_api.py
- stats/view.js
- errorState
- mountWorkspace
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
- test_wazuh_connection
- SafetyTests
- normalize_alert
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
- json
- exclusions.py
- pull/view.js
- database-workspace.test.mjs
- pull_jobs.py
- get_db
- FlagWorkspaceTests
- icon
- normalize_tenants
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
- esc
- Control
- wazuh_intel.py
- Any
- sanitize_text
- triage-request.test.mjs
- Testing — Arbiter
- ⚡ Key Capabilities
- Arbiter Architecture — Wazuh Read, Classify, Correlate
- enrich_ips_with_sidecar
- charts.js
- package.json
- ExclusionAPITests
- build
- Deploy config reference
- error-codes/view.js
- Code Style — Arbiter
- Deploy Arbiter
- .test_wazuh_search_exposes_resume_cursor_for_capped_range_pulls
- wazuh-queries/model.js
- secure_store.py
- core.py
- 6. Correlation policy
- 8. Roadmap implementasi, tiap tahap bisa diverifikasi
- fix-issue.md
- validate-bash.sh
- setup-ai-symlinks.sh
- 4. Data contracts
- Arbiter
- 4. Wireframe dan first viewport
- 5\. Cara Kerja
- wazuh_password
- intel.py
- load_isolated_api
- triage-request.test.mjs
- 5. Arsitektur Tools (Backend)
- .test_probe_sidecar_fails_over_between_candidates
- enrich_ip
- main.py
- 4. Arsitektur Web (Frontend)
- 5. Information architecture & interaction contracts
- settings.py
- test_intel_cache.py
- 🚀 Setup & Getting Started
- 7\. Keamanan
- 8. Deployment
- Global Constraints
- stats-trust.test.mjs
- Control
- imports/view.js
- 6. Arsitektur Data
- 7. Arsitektur Keamanan
- 8\. Instalasi
- Dokumentasi Arbiter
- 6.4 Skema database
- router-history.test.mjs

## God Nodes (most connected - your core abstractions)
1. `esc()` - 104 edges
2. `json()` - 88 edges
3. `get_db()` - 83 edges
4. `icon()` - 72 edges
5. `mount()` - 59 edges
6. `mount()` - 53 edges
7. `AITriageAPITests` - 47 edges
8. `errorState()` - 42 edges
9. `UIAPIContractTests` - 39 edges
10. `apiURL()` - 36 edges

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

## Communities (117 total, 26 thin omitted)

### Community 0 - "triage/view.js"
Cohesion: 0.14
Nodes (24): caseReportRoute(), exportURL(), reportAction(), reportScope(), exclusionValuesFor(), presets, priorityLabels, roleLabels (+16 more)

### Community 1 - "ref_node_assert"
Cohesion: 0.09
Nodes (18): renderTriageSummary(), summaryRequestParams(), loadSummary(), url, data, moduleURL, modelURL, mainPy (+10 more)

### Community 3 - "stats/view.js"
Cohesion: 0.15
Nodes (30): BENIGN_WHITELIST_PATTERNS, CHART_OPTIONS, distributionPercentages(), drilldownScrollBehavior(), generateMarkdownSummary(), generateStatsCSV(), INJECTION_PATTERNS, isMaliciousAlert() (+22 more)

### Community 4 - "errorState"
Cohesion: 0.16
Nodes (17): databaseIdentity(), summarizeTelemetryRange(), mount(), loadStatus(), maintain(), render(), switchTo(), chainLine() (+9 more)

### Community 5 - "mountWorkspace"
Cohesion: 0.08
Nodes (37): caseHref(), cleanIds(), draftFrom(), draftsEqual(), evidenceParams(), incidentPayload(), incidentRoute(), selectedIds() (+29 more)

### Community 7 - "loadingRows"
Cohesion: 0.14
Nodes (36): mount(), pull(), render(), saveRealtime(), schedule(), aiLabel(), clone(), DEFAULT_SETTINGS (+28 more)

### Community 8 - "AITriageAPITests"
Cohesion: 0.04
Nodes (3): suggest_groups(), AITriageAPITests, fake_search()

### Community 10 - "tenantValues"
Cohesion: 0.15
Nodes (28): ApiError, copyHTML(), copyText(), download(), request(), FLAG_EXPORT_FORMATS, FLAG_EXPORT_KEYS, FLAG_GROUP_BY_OPTIONS (+20 more)

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
Cohesion: 0.08
Nodes (27): check_profile_ready(), sync_remote_cache(), upsert_ip_cache(), api_add_exclusion(), api_ai_test(), api_ai_triage_save(), api_auth_login(), api_auth_logout() (+19 more)

### Community 17 - "test_settings.py"
Cohesion: 0.19
Nodes (6): decrypt_text(), _fernet(), _key_path(), _read_or_create_key_file(), SecretStoreError, intel_abuseipdb_key()

### Community 18 - "lookup_remote_ip_cache_detail"
Cohesion: 0.26
Nodes (4): lookup_remote_ip_cache_detail(), _FakeConnection, _psycopg_modules(), RemoteCacheLookupTests

### Community 19 - "test_wazuh_connection"
Cohesion: 0.15
Nodes (4): api_realtime_count(), api_test_wazuh(), test_wazuh_connection(), _wazuh_opener()

### Community 21 - "normalize_alert"
Cohesion: 0.14
Nodes (5): extract_active_response(), _active_response(), ActiveResponseReadTests, ClassificationTests, CorrelationTests

### Community 22 - "api_get_ai_triage"
Cohesion: 0.08
Nodes (26): current_wib_window_key(), get_triage_state_key(), safe_alerts(), _ai_triage_batch_size(), _ai_triage_candidate_count(), _ai_triage_exclude_ids(), _ai_triage_pick_state(), _ai_triage_progress() (+18 more)

### Community 23 - "Arbiter"
Cohesion: 0.33
Nodes (5): Arbiter, Audience and usage, Development verification, Implemented case policy without schema changes, Product boundaries

### Community 24 - "exports.py"
Cohesion: 0.09
Nodes (19): alert_full_log(), _as_dict(), _evidence_fields(), export_row(), export_rows(), _first(), _flat(), generate_docx_landscape_report() (+11 more)

### Community 25 - "mount"
Cohesion: 0.09
Nodes (60): aiSeverityKey(), alertFacts(), alertIndex(), boundedInteger(), DEFAULT_BATCH, formatWibWindowLabel(), GROUP_BY_OPTIONS, groupAlerts() (+52 more)

### Community 26 - "re"
Cohesion: 0.15
Nodes (11): extract_alerts(), first_ip_in(), kv_details(), normalize_log_for_signature(), parse_export(), parse_log_line(), parse_timestamp_iso(), parse_to_datetime() (+3 more)

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
Cohesion: 0.10
Nodes (7): base_config(), fake_get_db(), FakeConnection, FakeTransaction, load_pull_jobs(), PullJobTests, wait_for()

### Community 32 - "app.js"
Cohesion: 0.06
Nodes (37): adminOnlyPages, applyWorkspaceSettings(), canLeave(), checkPullActivity(), closeNav(), databaseChanged(), health(), help (+29 more)

### Community 33 - "json"
Cohesion: 0.14
Nodes (33): apiURL(), json(), applyUserPermissions(), checkFlagSummary(), notify(), render(), renderLoginGate(), scopeParams() (+25 more)

### Community 34 - "exclusions.py"
Cohesion: 0.15
Nodes (10): active_exclusion_rules(), build_exclusion_sql(), _coerce_enabled(), _escape_like(), glob_to_like(), normalize_exclusion_rule(), normalize_exclusions(), parse_wazuh_exclusion() (+2 more)

### Community 35 - "pull/view.js"
Cohesion: 0.31
Nodes (12): formatDuration(), mount(), paint(), paintProgress(), poll(), pollLater(), resumeJob(), stopPolling() (+4 more)

### Community 36 - "database-workspace.test.mjs"
Cohesion: 0.21
Nodes (14): loadBatchIncidentOptions(), withParams(), createNavigationMemory(), paramsForScope(), scopeKey(), tenantValues(), normalizeSidebarState(), readSidebarState() (+6 more)

### Community 37 - "pull_jobs.py"
Cohesion: 0.14
Nodes (14): api_realtime_pull(), _build_windows(), _ingest(), _now(), _parse_time(), _run_job(), pull_window(), _stamp() (+6 more)

### Community 38 - "get_db"
Cohesion: 0.11
Nodes (45): list_users(), get_db(), with_exclusions(), api_auth_me(), api_create_user(), api_database_status(), api_delete_user(), api_get_settings() (+37 more)

### Community 40 - "icon"
Cohesion: 0.17
Nodes (25): flagBadge(), flagMeta(), RULE_STATUS_FILTERS, ruleStatusBadge(), alertUrlPreview(), renderAlertDetailRows(), renderFlagGroups(), renderFlagsPage() (+17 more)

### Community 41 - "normalize_tenants"
Cohesion: 0.08
Nodes (38): Agent: code-reviewer, Agent: security-auditor, Tenant scoping, bump_daily_metrics(), _analyst_username(), api_flag_alerts(), api_flag_single_alert(), api_flags_alerts() (+30 more)

### Community 42 - "Arsitektur Arbiter — Web & Tools"
Cohesion: 0.15
Nodes (13): 10. Failure Modes dan Degradasi, 11. Keputusan Arsitektur dan Trade-off, 12. Batas Skalabilitas, 13. Peta Direktori Arsitektural, 14. Cara Memverifikasi Arsitektur, 15. Ringkasan Arsitektur, 1. Gaya Arsitektur, 2. Diagram Konteks (C4 Level 1) (+5 more)

### Community 43 - "ai_triage.py"
Cohesion: 0.10
Nodes (22): Backend (safe isolated suites), ai_triage(), _alert_tenant(), _as_mapping(), _cluster_alerts(), _cluster_prompt(), format_wib_window_label(), _group_by_indicators() (+14 more)

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
Cohesion: 0.12
Nodes (11): build_filter_sql(), _canonical_field(), _canonical_op(), _clean_value(), _error(), _escape_like(), _glob_to_like(), normalize_filter() (+3 more)

### Community 52 - "Layout"
Cohesion: 0.29
Nodes (7): Global shell, Impor dan Laporan, Insiden, Klasifikasi & korelasi, Layout, Responsive, Triage

### Community 54 - "database.py"
Cohesion: 0.15
Nodes (11): get_active_profile(), get_active_profile_id(), get_database_status(), get_database_status_unavailable(), get_db_connection(), mask_connection_url(), _persist_profile_overrides(), _profiles_payload() (+3 more)

### Community 56 - "esc"
Cohesion: 0.17
Nodes (27): /review — Code review pass, filterIncidents(), allOptions(), options(), renderEvidence(), renderList(), renderWorkspace(), routeLink() (+19 more)

### Community 57 - "Control"
Cohesion: 0.22
Nodes (3): click(), Control, fixture()

### Community 58 - "wazuh_intel.py"
Cohesion: 0.21
Nodes (19): as_dict(), clean_val(), _alert_key(), _as_json(), build_attack_chains(), _bump(), _chain_steps(), classify_alert() (+11 more)

### Community 59 - "Any"
Cohesion: 0.25
Nodes (9): _batch_insert_values(), _batch_instance(), _clean_expired_previews_locked(), create_preview_token(), ingest_alerts_batch(), purge_alerts(), purge_incidents(), purge_raw_alerts() (+1 more)

### Community 62 - "Testing — Arbiter"
Cohesion: 0.50
Nodes (3): Design lint, Frontend, Testing — Arbiter

### Community 63 - "⚡ Key Capabilities"
Cohesion: 0.17
Nodes (12): 10. Privacy-First Redactor, 11. Official Deliverables (5 Export Paths), 1. Resilient Multi-Format Ingestion, 2. High-Precision Log Dissector (No False Fields), 3. Signature-Based Deduplication & Causal Correlation, 4. Enterprise Multi-Tenant Architecture, 5. Modular Destination UI, 6. Local AI Triage & Persistent Daily Case Grouping (`#/ai-triage`) (+4 more)

### Community 64 - "Arbiter Architecture — Wazuh Read, Classify, Correlate"
Cohesion: 0.13
Nodes (15): 10. Acceptance tests, 11. Non-goals, 1. Design constraints, 2. Dataset evidence used to shape the architecture, 3. End-to-end pipeline, 5.1 Curated rule profiles (explicit, not trained), 5.2 Context signals, 5.3 Wording policy (+7 more)

### Community 65 - "enrich_ips_with_sidecar"
Cohesion: 0.13
Nodes (9): enrich_ips_with_sidecar(), fetch_sidecar_cache(), is_cdn_edge(), normalize_ip_address(), parse_sidecar_candidates(), probe_sidecar(), query_geo_batch(), save_sidecar_intel() (+1 more)

### Community 66 - "charts.js"
Cohesion: 0.42
Nodes (7): getColor(), PALETTE, renderBarChart(), renderDonutChart(), renderLineChart(), SIGNAL_COLORS, Task 3: Add the `#/stats` pivot workbench and reusable SVG charts

### Community 67 - "package.json"
Cohesion: 0.20
Nodes (9): description, engines, node, name, private, scripts, test, type (+1 more)

### Community 69 - "build"
Cohesion: 0.29
Nodes (6): build, volumes, context, dockerfile, services, arbiter

### Community 70 - "Deploy config reference"
Cohesion: 0.33
Nodes (5): Containers, Deploy config reference, Environment variables, Reverse proxy (optional), Secrets

### Community 71 - "error-codes/view.js"
Cohesion: 0.33
Nodes (8): ERROR_CODE_CATEGORIES, ERROR_CODE_SECTIONS, ERROR_CODES, filterErrorCodeSections(), mount(), render(), renderSections(), sectionBadge()

### Community 72 - "Code Style — Arbiter"
Cohesion: 0.40
Nodes (4): Code Style — Arbiter, CSS, Frontend (JS), Python

### Community 73 - "Deploy Arbiter"
Cohesion: 0.40
Nodes (4): Deploy Arbiter, Local dev, Pre-deploy checks, Production (Docker Compose)

### Community 74 - ".test_wazuh_search_exposes_resume_cursor_for_capped_range_pulls"
Cohesion: 0.13
Nodes (4): _http_error_reason(), _wazuh_request(), __init__(), __init__()

### Community 75 - "wazuh-queries/model.js"
Cohesion: 0.33
Nodes (6): buildWazuhQueries(), parseSeverityBounds(), PRESET_CATEGORIES, PRESET_WAZUH_QUERIES, QUERY_SEVERITY_OPTIONS, QUERY_TIME_OPTIONS

### Community 76 - "secure_store.py"
Cohesion: 0.26
Nodes (13): authenticate_user(), create_session_token(), create_user(), _default_admin_credentials(), delete_user(), get_user(), _hash_password(), _load_raw_users() (+5 more)

### Community 77 - "core.py"
Cohesion: 0.13
Nodes (9): local_ai_suggest_groups(), LocalAIUnavailable, normalize_alert(), ollama_request(), suggestions_with_fallback(), build_log_signature(), 5.5 Alur korelasi dan sugesti, DedupSafeguardTests (+1 more)

### Community 78 - "6. Correlation policy"
Cohesion: 0.40
Nodes (5): 6.1 Response linkage, 6.2 Canonical group identity, 6.3 Ordered chain, 6.4 Correlation confidence, 6. Correlation policy

### Community 79 - "8. Roadmap implementasi, tiap tahap bisa diverifikasi"
Cohesion: 0.29
Nodes (7): 8. Roadmap implementasi, tiap tahap bisa diverifikasi, Phase 0 — safety & baseline, Phase 1 — modular foundation + shell, Phase 2 — triage-first experience, Phase 3 — insiden workspace, Phase 4 — impor dan laporan, Phase 5 — hardening & rollout

### Community 84 - "4. Data contracts"
Cohesion: 0.50
Nodes (4): 4.1 Raw Wazuh alert (minimum), 4.2 Normalized alert, 4.3 Classification result, 4. Data contracts

### Community 85 - "Arbiter"
Cohesion: 0.20
Nodes (10): Arbiter, 🛠️ Architecture & Tech Stack, Dataset calibration and limits, 📄 License, 🎯 Overview, 🔒 Security & Privacy Notice, 📖 SOC Analyst Quickstart Workflow, 🧪 Testing & Quality Assurance (+2 more)

### Community 86 - "4. Wireframe dan first viewport"
Cohesion: 0.33
Nodes (6): 4. Wireframe dan first viewport, A. Triage desktop, B. Insiden index dan case workspace, C. Impor, D. Laporan, E. Mobile

### Community 87 - "5\. Cara Kerja"
Cohesion: 0.20
Nodes (10): 5.1 Ingesti dan parsing, 5.2 Normalisasi, 5.3 Deduplikasi, 5.4 Klasifikasi, 5.5 Korelasi, 5.6 AI Triage lokal, 5.7 Triage dan insiden, 5.8 Threat intelligence dan redaksi (+2 more)

### Community 88 - "wazuh_password"
Cohesion: 0.16
Nodes (7): API Conventions — Arbiter, Credential redaction, Errors, wazuh_password(), _fmt(), main(), _existing()

### Community 89 - "intel.py"
Cohesion: 0.09
Nodes (13): _enrich_single_public_live(), extract_alert_intel_context(), has_usable_sidecar_cache(), _json_object(), _json_value(), lookup_remote_ip_cache(), normalize_sidecar_record(), query_abuseipdb() (+5 more)

### Community 92 - "5. Arsitektur Tools (Backend)"
Cohesion: 0.25
Nodes (8): 5.1 Peta modul dan dependensi, 5.2 Tanggung jawab per modul, 5.3 Lapisan request, 5.4 Alur ingest end-to-end, 5.6 Alur AI Triage, 5.7 Alur ekspor, 5.8 Profil database dan pemeliharaan, 5. Arsitektur Tools (Backend)

### Community 94 - "enrich_ip"
Cohesion: 0.21
Nodes (4): enrich_ip(), is_private_ip(), is_valid_ip(), EnrichFallbackTests

### Community 95 - "main.py"
Cohesion: 0.09
Nodes (25): add_group_members(), _alert_review_owner(), api_alert_pull_cancel(), api_alert_pull_status(), api_delete_exclusion(), api_delete_wazuh_query(), api_list_alert_pulls(), delete_group() (+17 more)

### Community 96 - "4. Arsitektur Web (Frontend)"
Cohesion: 0.29
Nodes (7): 4.1 Lapisan frontend, 4.2 Pola feature module, 4.3 Routing dan scope, 4.4 Alur render satu halaman, 4.5 Login gate dan hak tampilan, 4.6 State yang tidak dipersistensi, 4. Arsitektur Web (Frontend)

### Community 97 - "5. Information architecture & interaction contracts"
Cohesion: 0.40
Nodes (5): 5. Information architecture & interaction contracts, Accessibility, Editing dan destructive actions, Refresh, Scope

### Community 99 - "settings.py"
Cohesion: 0.15
Nodes (17): api_put_settings(), encrypt_text(), is_encrypted(), _boolean(), _deep_merge(), default_settings(), intel_virustotal_key(), _is_local_or_lan_host() (+9 more)

### Community 100 - "test_intel_cache.py"
Cohesion: 0.09
Nodes (4): _FakeCursor, _FakeResult, RemoteSyncTests, _SyncConnection

### Community 101 - "🚀 Setup & Getting Started"
Cohesion: 0.33
Nodes (6): Connecting to a Neuropetra `ip_intel` database, Method A: Standalone Docker Setup (Fastest for new users), Method B: Host Mode (Connect to existing PostgreSQL / IP Intel), Method C: Local Python Setup (Without Docker), Prerequisites, 🚀 Setup & Getting Started

### Community 102 - "7\. Keamanan"
Cohesion: 0.29
Nodes (7): 7.1 Prinsip desain, 7.2 Autentikasi dan otorisasi, 7.3 Rahasia saat istirahat, 7.4 Isolasi jaringan dan SSRF, 7.5 Perlindungan data dan ekspor, 7.6 Batasan keamanan yang perlu diketahui, 7\. Keamanan

### Community 103 - "8. Deployment"
Cohesion: 0.33
Nodes (6): 8.1 Topologi A — Docker standalone, 8.2 Topologi B — Host mode, 8.3 Topologi C — Python lokal, 8.4 Topologi D — Reverse proxy TLS, 8.5 Startup sequence, 8. Deployment

### Community 104 - "Global Constraints"
Cohesion: 0.40
Nodes (5): intelSummary(), Global Constraints, Task 1: Favicon & Logo Arbiter, Task 3: Rich Forensic Correlation Cards, Task 4: Two-Way IP Intel Live Enrichment

### Community 105 - "stats-trust.test.mjs"
Cohesion: 0.28
Nodes (4): flush(), harness(), startSample(), stats()

### Community 106 - "Control"
Cohesion: 0.22
Nodes (3): click(), Control, fixture()

### Community 108 - "imports/view.js"
Cohesion: 0.36
Nodes (5): createImportSession(), importPage(), importResult(), mount(), update()

### Community 109 - "6. Arsitektur Data"
Cohesion: 0.40
Nodes (5): 6.1 ERD, 6.2 Penyimpanan JSONB, 6.3 Indeks, 6.4 Kepemilikan data, 6. Arsitektur Data

### Community 110 - "7. Arsitektur Keamanan"
Cohesion: 0.50
Nodes (4): 7.1 Trust boundary, 7.2 Kontrol keamanan per lapisan, 7.3 Batas yang harus dijaga saat deployment, 7. Arsitektur Keamanan

### Community 111 - "8\. Instalasi"
Cohesion: 0.14
Nodes (12): init_database(), _load_profile_overrides(), 8.1 Prasyarat, 8.2 Metode A — Docker standalone (paling cepat), 8.3 Metode B — Host mode (PostgreSQL yang sudah ada), 8.4 Metode C — Python lokal tanpa Docker, 8.5 Konfigurasi Wazuh Indexer (opsional, untuk Realtime), 8.6 Konfigurasi AI lokal (opsional) (+4 more)

### Community 112 - "Dokumentasi Arbiter"
Cohesion: 0.11
Nodes (18): 10\. Pengembangan dan Pemeliharaan, 11\. Lisensi, 1\. Ringkasan, 2.1 Untuk siapa, 2.2 Batas produk, 2.3 Destinasi aplikasi, 2.4 Kemampuan inti, 2\. Deskripsi Produk (+10 more)

### Community 114 - "6.4 Skema database"
Cohesion: 0.13
Nodes (14): ingest_alert_with_dedup(), 6.1 Stack, 6.2 Modul backend, 6.3 Modul frontend, 6.4.1 `wazuh.alerts`, 6.4.2 `wazuh.analysis_groups`, 6.4.3 `wazuh.alert_group_members`, 6.4.5 `public.ip_intel_cache` (+6 more)

### Community 124 - "router-history.test.mjs"
Cohesion: 0.24
Nodes (4): createRouter(), change(), parseRoute(), root

## Knowledge Gaps
- **26 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `esc()` connect `esc` to `triage/view.js`, `ref_node_assert`, `stats/view.js`, `errorState`, `mountWorkspace`, `loadingRows`, `tenantValues`, `mount`, `app.js`, `json`, `pull/view.js`, `database-workspace.test.mjs`, `icon`, `normalize_tenants`, `Arsitektur Arbiter — Web & Tools`, `charts.js`, `error-codes/view.js`, `Code Style — Arbiter`, `imports/view.js`, `7. Arsitektur Keamanan`, `6.4 Skema database`?**
  _High betweenness centrality (0.247) - this node is a cross-community bridge._
- **Are the 6 inferred relationships involving `esc()` (e.g. with `Agent: code-reviewer` and `/review — Code review pass`) actually correct?**
  _`esc()` has 6 INFERRED edges - model-reasoned connections that need verification._
- **Should `triage/view.js` be split into smaller, more focused modules?**
  _Cohesion score 0.13978494623655913 - nodes in this community are weakly interconnected._
- **Why does `Task 1: Establish precise shared multi-tenant scope and safe facet contract` connect `normalize_tenants` to `triage/view.js`, `json`, `get_db`, `File Map and Interfaces`, `main.py`?**
  _High betweenness centrality (0.143) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `json()` (e.g. with `mount()` and `loadSelected()`) actually correct?**
  _`json()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Should `ref_node_assert` be split into smaller, more focused modules?**
  _Cohesion score 0.09365079365079365 - nodes in this community are weakly interconnected._
- **Why does `Agent: code-reviewer` connect `normalize_tenants` to `esc`?**
  _High betweenness centrality (0.118) - this node is a cross-community bridge._