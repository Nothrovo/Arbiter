# Graph Report - Arbiter  (2026-11-20)

## Corpus Check
- 170 files · ~169,693 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 15 file(s) not represented in the graph (top: .css 5, (none) 4, .woff2 4)

## Summary
- 2074 nodes · 5480 edges · 111 communities (84 shown, 27 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 152 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `2d2a5e65`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- withParams
- ref_node_assert
- test_ui_api.py
- stats/view.js
- reports/view.js
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
- get_db
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
- json
- exclusions.py
- _cluster_alerts
- database-workspace.test.mjs
- pull_jobs.py
- Request
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
- esc
- Control
- wazuh_intel.py
- ingest_alert_with_dedup
- sanitize_text
- wazuh_count
- normalize_ollama_base_url
- ⚡ Key Capabilities
- Arbiter Architecture — Wazuh Read, Classify, Correlate
- intel.py
- _persist_profile_overrides
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
- SyntheticRoot
- wazuh_password
- enrich_intel
- 5. Classification policy
- triage-request.test.mjs
- _safe_remote_cache_error
- enrich_ip
- normalize_tenants
- suggest_groups
- 5. Information architecture & interaction contracts
- settings.py
- _FakeCursor
- 🚀 Setup & Getting Started
- stats-trust.test.mjs
- Control
- imports/view.js
- 8\. Instalasi
- Dokumentasi Arbiter
- feature-loader.test.mjs
- 6.4 Skema database
- router-history.test.mjs

## God Nodes (most connected - your core abstractions)
1. `esc()` - 103 edges
2. `json()` - 87 edges
3. `get_db()` - 83 edges
4. `icon()` - 72 edges
5. `mount()` - 57 edges
6. `mount()` - 53 edges
7. `AITriageAPITests` - 47 edges
8. `_analyst_username()` - 43 edges
9. `errorState()` - 42 edges
10. `UIAPIContractTests` - 39 edges

## Surprising Connections (you probably didn't know these)
- `5.7 Alur ekspor` --references--> `export_scope()`  [INFERRED]
  docs/ARSITEKTUR.md → app/main.py
- `5.8 Profil database dan pemeliharaan` --references--> `get_db()`  [INFERRED]
  docs/ARSITEKTUR.md → app/database.py
- `4.2 Normalized alert` --references--> `normalize_alert()`  [INFERRED]
  docs/ARCHITECTURE.md → app/core.py
- `5.6 AI Triage lokal` --references--> `safe_alerts()`  [INFERRED]
  docs/DOKUMENTASI.md → app/ai_triage.py
- `7.5 Perlindungan data dan ekspor` --references--> `safe_alerts()`  [INFERRED]
  docs/DOKUMENTASI.md → app/ai_triage.py

## Import Cycles
- None detected.

## Communities (111 total, 27 thin omitted)

### Community 0 - "withParams"
Cohesion: 0.15
Nodes (22): renderMonitoringDashboard(), renderReviewActivity(), renderReviewerFilter(), ROLE_LABELS, mount(), load(), report(), updateQuery() (+14 more)

### Community 1 - "ref_node_assert"
Cohesion: 0.08
Nodes (20): url, harness(), profiles, harness(), status, modelURL, mainPy, root (+12 more)

### Community 3 - "stats/view.js"
Cohesion: 0.13
Nodes (37): BENIGN_WHITELIST_PATTERNS, CHART_OPTIONS, distributionPercentages(), drilldownScrollBehavior(), generateMarkdownSummary(), generateStatsCSV(), INJECTION_PATTERNS, isMaliciousAlert() (+29 more)

### Community 4 - "reports/view.js"
Cohesion: 0.26
Nodes (16): caseReportRoute(), createReportSession(), exportURL(), reportAction(), reportScope(), groupOptions(), reportFallback(), reportPage() (+8 more)

### Community 5 - "state.js"
Cohesion: 0.15
Nodes (18): cleanIds(), draftFrom(), draftsEqual(), incidentPayload(), incidentRoute(), selectedIds(), SEVERITIES, STATUSES (+10 more)

### Community 7 - "loadingRows"
Cohesion: 0.11
Nodes (47): formatDuration(), mount(), paint(), paintProgress(), poll(), pollLater(), resumeJob(), stopPolling() (+39 more)

### Community 10 - "tenantValues"
Cohesion: 0.22
Nodes (19): ApiError, copyHTML(), copyText(), download(), request(), flagExportFormat(), flagExportParams(), flagExportURL() (+11 more)

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
Nodes (30): check_profile_ready(), add_group_members(), _alert_review_owner(), api_ai_triage_save(), api_alert_pull_cancel(), api_auth_login(), api_auth_logout(), api_create_report_audit_log() (+22 more)

### Community 17 - "test_settings.py"
Cohesion: 0.23
Nodes (7): decrypt_text(), encrypt_text(), _fernet(), is_encrypted(), _key_path(), _read_or_create_key_file(), SecretStoreError

### Community 18 - "lookup_remote_ip_cache_detail"
Cohesion: 0.15
Nodes (5): lookup_remote_ip_cache_detail(), _FakeConnection, _FakeResult, _psycopg_modules(), RemoteCacheLookupTests

### Community 19 - "get_db"
Cohesion: 0.08
Nodes (35): list_users(), get_db(), api_add_exclusion(), api_ai_test(), api_auth_me(), api_create_user(), api_database_purge_raw(), api_delete_exclusion() (+27 more)

### Community 21 - "normalize_alert"
Cohesion: 0.13
Nodes (9): _bump(), classify_alert(), extract_active_response(), _level_priority(), _profile_for(), _active_response(), ActiveResponseReadTests, ClassificationTests (+1 more)

### Community 22 - "Any"
Cohesion: 0.07
Nodes (35): get_triage_state_key(), safe_alerts(), _ai_triage_batch_size(), _ai_triage_candidate_count(), _ai_triage_exclude_ids(), _ai_triage_pick_state(), _ai_triage_progress(), _ai_triage_read_only() (+27 more)

### Community 23 - "Arbiter"
Cohesion: 0.33
Nodes (5): Arbiter, Audience and usage, Development verification, Implemented case policy without schema changes, Product boundaries

### Community 24 - "exports.py"
Cohesion: 0.08
Nodes (21): alert_full_log(), _as_dict(), _evidence_fields(), export_row(), export_rows(), _first(), _flat(), generate_docx_landscape_report() (+13 more)

### Community 25 - "mount"
Cohesion: 0.09
Nodes (59): aiSeverityKey(), alertFacts(), alertIndex(), boundedInteger(), DEFAULT_BATCH, formatWibWindowLabel(), GROUP_BY_OPTIONS, groupAlerts() (+51 more)

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
Cohesion: 0.11
Nodes (7): base_config(), fake_get_db(), FakeConnection, FakeTransaction, load_pull_jobs(), PullJobTests, wait_for()

### Community 32 - "app.js"
Cohesion: 0.07
Nodes (40): adminOnlyPages, applyUserPermissions(), applyWorkspaceSettings(), canLeave(), checkFlagSummary(), checkPullActivity(), closeNav(), databaseChanged() (+32 more)

### Community 33 - "json"
Cohesion: 0.14
Nodes (33): apiURL(), json(), databaseIdentity(), summarizeTelemetryRange(), mount(), loadStatus(), maintain(), render() (+25 more)

### Community 34 - "exclusions.py"
Cohesion: 0.14
Nodes (11): active_exclusion_rules(), build_exclusion_sql(), _coerce_enabled(), _escape_like(), glob_to_like(), normalize_exclusion_rule(), normalize_exclusions(), parse_wazuh_exclusion() (+3 more)

### Community 35 - "_cluster_alerts"
Cohesion: 0.17
Nodes (3): ai_triage(), _cluster_prompt(), _validate_cluster_verdicts()

### Community 36 - "database-workspace.test.mjs"
Cohesion: 0.25
Nodes (11): setSidebarState(), parseRoute(), createNavigationMemory(), normalizeSidebarState(), readSidebarState(), SIDEBAR_KEY, toggleSidebarState(), writeSidebarState() (+3 more)

### Community 37 - "pull_jobs.py"
Cohesion: 0.19
Nodes (12): _build_windows(), cancel_job(), get_job(), list_jobs(), _now(), _parse_time(), _public(), _run_job() (+4 more)

### Community 38 - "Request"
Cohesion: 0.15
Nodes (34): with_exclusions(), generate_gdocs_html_report(), _analyst_username(), api_flags_alerts(), api_flags_groups(), api_flags_summary(), _build_flag_scope_where(), _exclusion_document() (+26 more)

### Community 40 - "mount"
Cohesion: 0.10
Nodes (41): notify(), save(), FLAG_EXPORT_FORMATS, FLAG_EXPORT_KEYS, FLAG_GROUP_BY_OPTIONS, FLAG_META_MAP, FLAG_TABS, flagBadge() (+33 more)

### Community 41 - "api_get_monitoring"
Cohesion: 0.17
Nodes (7): api_database_status(), api_get_monitoring(), _expire_stale_claims(), health_check(), _review_activity_payload(), _review_local_date(), _savepoint()

### Community 42 - "Arsitektur Arbiter — Web & Tools"
Cohesion: 0.05
Nodes (43): 10. Failure Modes dan Degradasi, 11. Keputusan Arsitektur dan Trade-off, 12. Batas Skalabilitas, 13. Peta Direktori Arsitektural, 14. Cara Memverifikasi Arsitektur, 15. Ringkasan Arsitektur, 1. Gaya Arsitektur, 2. Diagram Konteks (C4 Level 1) (+35 more)

### Community 43 - "ai_triage.py"
Cohesion: 0.16
Nodes (17): _alert_tenant(), _as_mapping(), _cluster_alerts(), current_wib_window_key(), format_wib_window_label(), _group_by_indicators(), find(), union() (+9 more)

### Community 45 - ".test_enrich_ips_with_sidecar_uses_cache_then_live_fallback_and_writes_back_context"
Cohesion: 0.11
Nodes (3): AbuseIPDBError, SidecarEnrichTests, fake_abuse()

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
Cohesion: 0.17
Nodes (15): _clean_expired_previews_locked(), create_preview_token(), get_active_profile(), get_active_profile_id(), get_database_status(), get_database_status_unavailable(), mask_connection_url(), _profiles_payload() (+7 more)

### Community 55 - "SyntheticDB"
Cohesion: 0.18
Nodes (3): Task 2: Build SQL aggregation endpoints and schema support, TriageScopeTests, SyntheticDB

### Community 56 - "esc"
Cohesion: 0.16
Nodes (37): /review — Code review pass, caseHref(), evidenceParams(), filterIncidents(), allOptions(), options(), renderEvidence(), renderList() (+29 more)

### Community 57 - "Control"
Cohesion: 0.22
Nodes (3): click(), Control, fixture()

### Community 58 - "wazuh_intel.py"
Cohesion: 0.25
Nodes (16): as_dict(), clean_val(), _alert_key(), _as_json(), build_attack_chains(), _chain_steps(), correlate_alerts(), _extract_payload_indicators() (+8 more)

### Community 59 - "ingest_alert_with_dedup"
Cohesion: 0.18
Nodes (7): _batch_insert_values(), _batch_instance(), bump_daily_metrics(), ingest_alert_with_dedup(), ingest_alerts_batch(), _ingest(), 6.4.1 `wazuh.alerts`

### Community 61 - "wazuh_count"
Cohesion: 0.08
Nodes (5): _normalize_wazuh_timestamp(), _valid_timestamp(), wazuh_count(), _wazuh_opener(), wazuh_search()

### Community 62 - "normalize_ollama_base_url"
Cohesion: 0.13
Nodes (9): Backend (safe isolated suites), Design lint, Frontend, Testing — Arbiter, _parse_ai_json(), test_ollama(), LocalAIUnavailable, ollama_request() (+1 more)

### Community 63 - "⚡ Key Capabilities"
Cohesion: 0.17
Nodes (12): 10. Privacy-First Redactor, 11. Official Deliverables (5 Export Paths), 1. Resilient Multi-Format Ingestion, 2. High-Precision Log Dissector (No False Fields), 3. Signature-Based Deduplication & Causal Correlation, 4. Enterprise Multi-Tenant Architecture, 5. Modular Destination UI, 6. Local AI Triage & Persistent Daily Case Grouping (`#/ai-triage`) (+4 more)

### Community 64 - "Arbiter Architecture — Wazuh Read, Classify, Correlate"
Cohesion: 0.18
Nodes (11): 10. Acceptance tests, 11. Non-goals, 1. Design constraints, 2. Dataset evidence used to shape the architecture, 3. End-to-end pipeline, 7. API surfaces, 8. Storage and migration, 9. Failure modes and handling (+3 more)

### Community 65 - "intel.py"
Cohesion: 0.09
Nodes (19): enrich_ips_with_sidecar(), _enrich_single_public_live(), extract_alert_intel_context(), fetch_sidecar_cache(), has_usable_sidecar_cache(), is_cdn_edge(), is_private_ip(), is_valid_ip() (+11 more)

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

### Community 75 - "wazuh-queries/model.js"
Cohesion: 0.33
Nodes (6): buildWazuhQueries(), parseSeverityBounds(), PRESET_CATEGORIES, PRESET_WAZUH_QUERIES, QUERY_SEVERITY_OPTIONS, QUERY_TIME_OPTIONS

### Community 76 - "secure_store.py"
Cohesion: 0.26
Nodes (13): authenticate_user(), create_session_token(), create_user(), _default_admin_credentials(), delete_user(), get_user(), _hash_password(), _load_raw_users() (+5 more)

### Community 77 - "core.py"
Cohesion: 0.18
Nodes (6): local_ai_suggest_groups(), normalize_alert(), suggestions_with_fallback(), build_log_signature(), DedupSafeguardTests, NormalizeIntegrationTests

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

### Community 87 - "SyntheticRoot"
Cohesion: 0.22
Nodes (3): context(), load(), SyntheticRoot

### Community 88 - "wazuh_password"
Cohesion: 0.16
Nodes (7): API Conventions — Arbiter, Credential redaction, Errors, wazuh_password(), _fmt(), main(), _existing()

### Community 89 - "enrich_intel"
Cohesion: 0.16
Nodes (6): _remote_profile_read_only(), _resolve_remote_db_url(), sync_remote_cache(), upsert_ip_cache(), enrich_intel(), RemoteSyncTests

### Community 90 - "5. Classification policy"
Cohesion: 0.50
Nodes (4): 5.1 Curated rule profiles (explicit, not trained), 5.2 Context signals, 5.3 Wording policy, 5. Classification policy

### Community 91 - "triage-request.test.mjs"
Cohesion: 0.13
Nodes (3): createSelection(), Element, requestsFor()

### Community 94 - "enrich_ip"
Cohesion: 0.32
Nodes (3): enrich_ip(), query_abuseipdb(), EnrichFallbackTests

### Community 95 - "normalize_tenants"
Cohesion: 0.11
Nodes (19): Agent: code-reviewer, Agent: security-auditor, Tenant scoping, bulk_verdict_by_pattern(), delete_group(), export_scope(), flag_export_scope(), get_group_detail() (+11 more)

### Community 97 - "5. Information architecture & interaction contracts"
Cohesion: 0.40
Nodes (5): 5. Information architecture & interaction contracts, Accessibility, Editing dan destructive actions, Refresh, Scope

### Community 99 - "settings.py"
Cohesion: 0.12
Nodes (13): _boolean(), _deep_merge(), default_settings(), _http_error_reason(), intel_abuseipdb_key(), intel_virustotal_key(), _is_local_or_lan_host(), normalize_sidecar_urls() (+5 more)

### Community 101 - "🚀 Setup & Getting Started"
Cohesion: 0.33
Nodes (6): Connecting to a Neuropetra `ip_intel` database, Method A: Standalone Docker Setup (Fastest for new users), Method B: Host Mode (Connect to existing PostgreSQL / IP Intel), Method C: Local Python Setup (Without Docker), Prerequisites, 🚀 Setup & Getting Started

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
Cohesion: 0.06
Nodes (35): 10\. Pengembangan dan Pemeliharaan, 11\. Lisensi, 1\. Ringkasan, 2.1 Untuk siapa, 2.2 Batas produk, 2.3 Destinasi aplikasi, 2.4 Kemampuan inti, 2\. Deskripsi Produk (+27 more)

### Community 114 - "6.4 Skema database"
Cohesion: 0.17
Nodes (12): 6.1 Stack, 6.2 Modul backend, 6.3 Modul frontend, 6.4.2 `wazuh.analysis_groups`, 6.4.3 `wazuh.alert_group_members`, 6.4.5 `public.ip_intel_cache`, 6.4.6 Tabel Remote milik provider, 6.4.7 Indeks performa (+4 more)

## Knowledge Gaps
- **27 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `esc()` connect `esc` to `app.js`, `json`, `withParams`, `stats/view.js`, `reports/view.js`, `error-codes/view.js`, `Code Style — Arbiter`, `mount`, `loadingRows`, `Arsitektur Arbiter — Web & Tools`, `imports/view.js`, `6.4 Skema database`, `mount`, `normalize_tenants`?**
  _High betweenness centrality (0.241) - this node is a cross-community bridge._
- **Are the 6 inferred relationships involving `esc()` (e.g. with `Agent: code-reviewer` and `/review — Code review pass`) actually correct?**
  _`esc()` has 6 INFERRED edges - model-reasoned connections that need verification._
- **Should `ref_node_assert` be split into smaller, more focused modules?**
  _Cohesion score 0.07641196013289037 - nodes in this community are weakly interconnected._
- **Why does `Task 1: Establish precise shared multi-tenant scope and safe facet contract` connect `normalize_tenants` to `Any`, `json`, `reports/view.js`, `File Map and Interfaces`?**
  _High betweenness centrality (0.122) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `json()` (e.g. with `mount()` and `loadSelected()`) actually correct?**
  _`json()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Should `test_ui_api.py` be split into smaller, more focused modules?**
  _Cohesion score 0.12615384615384614 - nodes in this community are weakly interconnected._
- **Why does `Agent: code-reviewer` connect `normalize_tenants` to `Any`, `esc`?**
  _High betweenness centrality (0.120) - this node is a cross-community bridge._