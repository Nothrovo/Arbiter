# Graph Report - Arbiter  (2026-11-17)

## Corpus Check
- 157 files · ~133,601 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 16 file(s) not represented in the graph (top: .css 5, (none) 4, .woff2 4)

## Summary
- 1715 nodes · 4194 edges · 109 communities (87 shown, 22 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 131 edges (avg confidence: 0.9)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `81583029`
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
- json
- Any
- Arbiter
- exports.py
- mount
- intel.py
- db
- 📋 Protokol Eksekusi Rinci
- File Map and Interfaces
- SettingsAPITests
- test_pull_jobs.py
- app.js
- get_db
- exclusions.py
- SyntheticDB
- wazuh_intel.py
- createRouter
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
- 8. Roadmap implementasi, tiap tahap bisa diverifikasi
- 4. Wireframe dan first viewport
- Layout
- 5. Information architecture & interaction contracts
- database.py
- json
- database-workspace.test.mjs
- _FakeConnection
- Testing — Arbiter
- 5\. Cara Kerja
- sanitize_text
- enrich_ip
- esc
- ⚡ Key Capabilities
- Arbiter Architecture — Wazuh Read, Classify, Correlate
- _SyncConnection
- main.py
- package.json
- ExclusionAPITests
- build
- Deploy config reference
- Arbiter
- Code Style — Arbiter
- Deploy Arbiter
- 8\. Instalasi
- stats-trust.test.mjs
- secure_store.py
- 6.4 Skema database
- auth.py
- test_intel_cache.py
- fix-issue.md
- validate-bash.sh
- setup-ai-symlinks.sh
- 🚀 Setup & Getting Started
- 6\. Komponen yang Dipakai
- mountWorkspace
- 7\. Keamanan
- api_get_ai_triage
- load_settings
- 4. Data contracts
- SyntheticRoot
- wazuh_search
- 6. Correlation policy
- 2\. Deskripsi Produk
- 5. Classification policy
- 3\. Workflow
- _safe_remote_cache_error
- settings.py
- scope.js
- _http_error_reason
- test_wazuh_connection
- test_settings.py
- wazuh-queries/model.js
- createNavigationMemory
- _FakeCursor
- setSidebarState
- feature-loader.test.mjs

## God Nodes (most connected - your core abstractions)
1. `esc()` - 91 edges
2. `json()` - 67 edges
3. `get_db()` - 63 edges
4. `icon()` - 60 edges
5. `AITriageAPITests` - 40 edges
6. `mount()` - 40 edges
7. `mount()` - 38 edges
8. `errorState()` - 36 edges
9. `UIAPIContractTests` - 33 edges
10. `mount()` - 32 edges

## Surprising Connections (you probably didn't know these)
- `5.7 Alur ekspor` --references--> `export_scope()`  [INFERRED]
  docs/ARSITEKTUR.md → app/main.py
- `Credential redaction` --references--> `wazuh_password()`  [INFERRED]
  .ai/rules/api-conventions.md → app/settings.py
- `5.8 Profil database dan pemeliharaan` --references--> `get_db()`  [INFERRED]
  docs/ARSITEKTUR.md → app/database.py
- `Frontend (JS)` --references--> `esc()`  [INFERRED]
  .ai/rules/code-style.md → app/static/js/ui/primitives.js
- `Konsekuensi yang disadari` --references--> `esc()`  [INFERRED]
  docs/ARSITEKTUR.md → app/static/js/ui/primitives.js

## Import Cycles
- None detected.

## Communities (109 total, 22 thin omitted)

### Community 0 - "core.py"
Cohesion: 0.11
Nodes (15): normalize_alert(), build_log_signature(), extract_alerts(), first_ip_in(), kv_details(), normalize_log_for_signature(), parse_export(), parse_log_line() (+7 more)

### Community 1 - "ref_node_assert"
Cohesion: 0.07
Nodes (19): url, harness(), profiles, harness(), status, modelURL, mainPy, root (+11 more)

### Community 3 - "stats/view.js"
Cohesion: 0.12
Nodes (39): BENIGN_WHITELIST_PATTERNS, CHART_OPTIONS, distributionPercentages(), drilldownScrollBehavior(), generateMarkdownSummary(), generateStatsCSV(), INJECTION_PATTERNS, isMaliciousAlert() (+31 more)

### Community 4 - "scope.js"
Cohesion: 0.15
Nodes (19): cleanIds(), draftFrom(), draftsEqual(), evidenceParams(), incidentPayload(), incidentRoute(), selectedIds(), SEVERITIES (+11 more)

### Community 5 - "imports/render.js"
Cohesion: 0.12
Nodes (9): createImportSession(), importPage(), importResult(), mount(), update(), moduleURL, click(), Control (+1 more)

### Community 7 - "loadingRows"
Cohesion: 0.18
Nodes (26): aiLabel(), clone(), DEFAULT_SETTINGS, EXCLUSION_FIELD_OPTIONS, EXCLUSION_MATCH_OPTIONS, exclusionFieldLabel(), exclusionMatchLabel(), exclusionRuleStats() (+18 more)

### Community 8 - "AITriageAPITests"
Cohesion: 0.05
Nodes (3): suggest_groups(), AITriageAPITests, fake_search()

### Community 10 - "json"
Cohesion: 0.18
Nodes (22): ApiError, copyHTML(), copyText(), download(), request(), caseReportRoute(), createReportSession(), exportURL() (+14 more)

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

### Community 16 - "normalize_tenants"
Cohesion: 0.10
Nodes (25): Agent: code-reviewer, Agent: security-auditor, API Conventions — Arbiter, Credential redaction, Errors, Tenant scoping, add_group_members(), batch_update_review() (+17 more)

### Community 17 - "icon"
Cohesion: 0.28
Nodes (16): databaseIdentity(), summarizeTelemetryRange(), mount(), loadStatus(), maintain(), render(), switchTo(), renderEvidence() (+8 more)

### Community 18 - "Control"
Cohesion: 0.22
Nodes (3): click(), Control, fixture()

### Community 19 - "incidents/render.js"
Cohesion: 0.35
Nodes (12): caseHref(), filterIncidents(), allOptions(), options(), renderList(), renderWorkspace(), routeLink(), scopeText() (+4 more)

### Community 21 - "json"
Cohesion: 0.17
Nodes (26): json(), mount(), paint(), paintProgress(), poll(), pollLater(), resumeJob(), stopPolling() (+18 more)

### Community 22 - "Any"
Cohesion: 0.18
Nodes (19): _exclusion_document(), export_csv(), export_docx(), export_gdocs_html(), export_markdown(), export_preview(), export_tsv(), export_xlsx() (+11 more)

### Community 23 - "Arbiter"
Cohesion: 0.33
Nodes (5): Arbiter, Audience and usage, Development verification, Implemented case policy without schema changes, Product boundaries

### Community 24 - "exports.py"
Cohesion: 0.08
Nodes (12): generate_docx_landscape_report(), generate_gdocs_html_report(), generate_markdown_report(), generate_tsv_table(), generate_xlsx_workbook(), Arbiter SOC Desk Upgrades Implementation Plan, Global Constraints, Task 1: Favicon & Logo Arbiter (+4 more)

### Community 25 - "mount"
Cohesion: 0.18
Nodes (31): aiSeverityKey(), alertFacts(), alertIndex(), boundedInteger(), formatWibWindowLabel(), GROUP_BY_OPTIONS, groupAlerts(), LIMITS (+23 more)

### Community 26 - "intel.py"
Cohesion: 0.14
Nodes (7): _json_object(), lookup_remote_ip_cache(), query_abuseipdb(), _remote_profile_read_only(), _resolve_remote_db_url(), sync_remote_cache(), upsert_ip_cache()

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
Cohesion: 0.08
Nodes (24): adminOnlyPages, health(), help, main, navigationMemory, pageTitles, realtimeState, realtimeToggle (+16 more)

### Community 33 - "get_db"
Cohesion: 0.16
Nodes (22): list_users(), get_db(), api_add_exclusion(), api_auth_me(), api_create_user(), api_delete_exclusion(), api_delete_user(), api_delete_wazuh_query() (+14 more)

### Community 34 - "exclusions.py"
Cohesion: 0.15
Nodes (11): active_exclusion_rules(), build_exclusion_sql(), _coerce_enabled(), _escape_like(), glob_to_like(), normalize_exclusion_rule(), normalize_exclusions(), parse_wazuh_exclusion() (+3 more)

### Community 35 - "SyntheticDB"
Cohesion: 0.15
Nodes (3): Task 2: Build SQL aggregation endpoints and schema support, TriageScopeTests, SyntheticDB

### Community 36 - "wazuh_intel.py"
Cohesion: 0.25
Nodes (16): as_dict(), clean_val(), _alert_key(), _as_json(), build_attack_chains(), _chain_steps(), correlate_alerts(), _extract_payload_indicators() (+8 more)

### Community 38 - "mount"
Cohesion: 0.13
Nodes (33): apiURL(), intelBadge(), intelSummary(), renderQueue(), renderTriageSummary(), summaryRequestParams(), chainLine(), classificationBlock() (+25 more)

### Community 41 - "normalize_alert"
Cohesion: 0.13
Nodes (9): _bump(), classify_alert(), extract_active_response(), _level_priority(), _profile_for(), _active_response(), ActiveResponseReadTests, ClassificationTests (+1 more)

### Community 42 - "Arsitektur Arbiter — Web & Tools"
Cohesion: 0.05
Nodes (43): 10. Failure Modes dan Degradasi, 11. Keputusan Arsitektur dan Trade-off, 12. Batas Skalabilitas, 13. Peta Direktori Arsitektural, 14. Cara Memverifikasi Arsitektur, 15. Ringkasan Arsitektur, 1. Gaya Arsitektur, 2. Diagram Konteks (C4 Level 1) (+35 more)

### Community 43 - "ai_triage.py"
Cohesion: 0.11
Nodes (17): ai_triage(), _alert_tenant(), _cluster_alerts(), _cluster_prompt(), current_wib_window_key(), format_wib_window_label(), _group_by_rule_description(), heuristic_triage() (+9 more)

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

### Community 50 - "8. Roadmap implementasi, tiap tahap bisa diverifikasi"
Cohesion: 0.29
Nodes (7): 8. Roadmap implementasi, tiap tahap bisa diverifikasi, Phase 0 — safety & baseline, Phase 1 — modular foundation + shell, Phase 2 — triage-first experience, Phase 3 — insiden workspace, Phase 4 — impor dan laporan, Phase 5 — hardening & rollout

### Community 51 - "4. Wireframe dan first viewport"
Cohesion: 0.33
Nodes (6): 4. Wireframe dan first viewport, A. Triage desktop, B. Insiden index dan case workspace, C. Impor, D. Laporan, E. Mobile

### Community 52 - "Layout"
Cohesion: 0.29
Nodes (7): Global shell, Impor dan Laporan, Insiden, Klasifikasi & korelasi, Layout, Responsive, Triage

### Community 53 - "5. Information architecture & interaction contracts"
Cohesion: 0.40
Nodes (5): 5. Information architecture & interaction contracts, Accessibility, Editing dan destructive actions, Refresh, Scope

### Community 54 - "database.py"
Cohesion: 0.09
Nodes (27): check_profile_ready(), _clean_expired_previews_locked(), create_preview_token(), get_active_profile(), get_active_profile_id(), get_database_status(), get_database_status_unavailable(), get_db_connection() (+19 more)

### Community 55 - "json"
Cohesion: 0.16
Nodes (5): local_ai_suggest_groups(), LocalAIUnavailable, ollama_request(), suggestions_with_fallback(), is_malicious_alert_record()

### Community 56 - "database-workspace.test.mjs"
Cohesion: 0.22
Nodes (11): parseRoute(), createSelection(), normalizeSidebarState(), readSidebarState(), SIDEBAR_KEY, toggleSidebarState(), writeSidebarState(), shell() (+3 more)

### Community 57 - "_FakeConnection"
Cohesion: 0.26
Nodes (4): lookup_remote_ip_cache_detail(), _FakeConnection, _psycopg_modules(), RemoteCacheLookupTests

### Community 58 - "Testing — Arbiter"
Cohesion: 0.40
Nodes (4): Backend (safe isolated suites), Design lint, Frontend, Testing — Arbiter

### Community 59 - "5\. Cara Kerja"
Cohesion: 0.20
Nodes (10): 5.1 Ingesti dan parsing, 5.2 Normalisasi, 5.3 Deduplikasi, 5.4 Klasifikasi, 5.5 Korelasi, 5.6 AI Triage lokal, 5.7 Triage dan insiden, 5.8 Threat intelligence dan redaksi (+2 more)

### Community 61 - "enrich_ip"
Cohesion: 0.28
Nodes (3): enrich_ip(), is_private_ip(), EnrichFallbackTests

### Community 62 - "esc"
Cohesion: 0.17
Nodes (18): /review — Code review pass, applyUserPermissions(), notify(), render(), renderLoginGate(), render(), renderControls(), renderIntro() (+10 more)

### Community 63 - "⚡ Key Capabilities"
Cohesion: 0.17
Nodes (12): 10. Privacy-First Redactor, 11. Official Deliverables (5 Export Paths), 1. Resilient Multi-Format Ingestion, 2. High-Precision Log Dissector (No False Fields), 3. Signature-Based Deduplication & Causal Correlation, 4. Enterprise Multi-Tenant Architecture, 5. Modular Destination UI, 6. Local AI Triage & Persistent Daily Case Grouping (`#/ai-triage`) (+4 more)

### Community 64 - "Arbiter Architecture — Wazuh Read, Classify, Correlate"
Cohesion: 0.18
Nodes (11): 10. Acceptance tests, 11. Non-goals, 1. Design constraints, 2. Dataset evidence used to shape the architecture, 3. End-to-end pipeline, 7. API surfaces, 8. Storage and migration, 9. Failure modes and handling (+3 more)

### Community 66 - "main.py"
Cohesion: 0.09
Nodes (22): init_database(), is_valid_ip(), api_alert_pull_cancel(), api_alert_pull_status(), api_auth_logout(), api_database_config(), api_database_purge_alerts(), api_database_purge_incidents() (+14 more)

### Community 67 - "package.json"
Cohesion: 0.20
Nodes (9): description, engines, node, name, private, scripts, test, type (+1 more)

### Community 69 - "build"
Cohesion: 0.29
Nodes (6): build, volumes, context, dockerfile, services, arbiter

### Community 70 - "Deploy config reference"
Cohesion: 0.33
Nodes (5): Containers, Deploy config reference, Environment variables, Reverse proxy (optional), Secrets

### Community 71 - "Arbiter"
Cohesion: 0.20
Nodes (10): Arbiter, 🛠️ Architecture & Tech Stack, Dataset calibration and limits, 📄 License, 🎯 Overview, 🔒 Security & Privacy Notice, 📖 SOC Analyst Quickstart Workflow, 🧪 Testing & Quality Assurance (+2 more)

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

### Community 76 - "secure_store.py"
Cohesion: 0.22
Nodes (8): _verify_password(), decrypt_text(), encrypt_text(), _fernet(), is_encrypted(), _key_path(), _read_or_create_key_file(), SecretStoreError

### Community 77 - "6.4 Skema database"
Cohesion: 0.25
Nodes (8): 6.4.1 `wazuh.alerts`, 6.4.2 `wazuh.analysis_groups`, 6.4.3 `wazuh.alert_group_members`, 6.4.5 `public.ip_intel_cache`, 6.4.6 Tabel Remote milik provider, 6.4.7 Indeks performa, 6.4.8 Catatan operasional, 6.4 Skema database

### Community 78 - "auth.py"
Cohesion: 0.29
Nodes (14): authenticate_user(), create_session_token(), create_user(), _default_admin_credentials(), delete_user(), get_user(), _hash_password(), _load_raw_users() (+6 more)

### Community 84 - "🚀 Setup & Getting Started"
Cohesion: 0.33
Nodes (6): Connecting to a Neuropetra `ip_intel` database, Method A: Standalone Docker Setup (Fastest for new users), Method B: Host Mode (Connect to existing PostgreSQL / IP Intel), Method C: Local Python Setup (Without Docker), Prerequisites, 🚀 Setup & Getting Started

### Community 85 - "6\. Komponen yang Dipakai"
Cohesion: 0.40
Nodes (5): 6.1 Stack, 6.2 Modul backend, 6.3 Modul frontend, 6.5 Kelompok endpoint API, 6\. Komponen yang Dipakai

### Community 86 - "mountWorkspace"
Cohesion: 0.41
Nodes (12): validateDraft(), mountWorkspace(), context(), initial(), loadPage(), loadSelected(), panels(), refresh() (+4 more)

### Community 87 - "7\. Keamanan"
Cohesion: 0.29
Nodes (7): 7.1 Prinsip desain, 7.2 Autentikasi dan otorisasi, 7.3 Rahasia saat istirahat, 7.4 Isolasi jaringan dan SSRF, 7.5 Perlindungan data dan ekspor, 7.6 Batasan keamanan yang perlu diketahui, 7\. Keamanan

### Community 88 - "api_get_ai_triage"
Cohesion: 0.13
Nodes (11): get_triage_state_key(), _load_profile_overrides(), api_ai_triage(), api_ai_triage_save(), api_get_ai_triage(), api_list_wazuh_queries(), _build_ai_triage_where(), _find_matching_open_ai_group() (+3 more)

### Community 89 - "load_settings"
Cohesion: 0.16
Nodes (9): api_ai_test(), api_realtime_count(), api_realtime_pull(), api_start_alert_pull(), api_test_wazuh(), load_settings(), migrate_settings(), save_settings() (+1 more)

### Community 90 - "4. Data contracts"
Cohesion: 0.50
Nodes (4): 4.1 Raw Wazuh alert (minimum), 4.2 Normalized alert, 4.3 Classification result, 4. Data contracts

### Community 91 - "SyntheticRoot"
Cohesion: 0.22
Nodes (3): context(), load(), SyntheticRoot

### Community 92 - "wazuh_search"
Cohesion: 0.15
Nodes (5): _wazuh_request(), wazuh_search(), _fmt(), main(), _existing()

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
Cohesion: 0.27
Nodes (7): _boolean(), _deep_merge(), default_settings(), intel_abuseipdb_key(), normalize_ollama_base_url(), _text(), validate_settings()

### Community 100 - "scope.js"
Cohesion: 0.28
Nodes (10): loadList(), report(), scopeKey(), choices(), integer(), queryFrom(), rawTenantValues(), scopeParams() (+2 more)

### Community 101 - "_http_error_reason"
Cohesion: 0.17
Nodes (3): _http_error_reason(), __init__(), __init__()

### Community 102 - "test_wazuh_connection"
Cohesion: 0.18
Nodes (3): test_wazuh_connection(), wazuh_alert_query(), _wazuh_opener()

### Community 103 - "test_settings.py"
Cohesion: 0.24
Nodes (3): _normalize_wazuh_timestamp(), _valid_timestamp(), wazuh_count()

### Community 104 - "wazuh-queries/model.js"
Cohesion: 0.33
Nodes (6): buildWazuhQueries(), parseSeverityBounds(), PRESET_CATEGORIES, PRESET_WAZUH_QUERIES, QUERY_SEVERITY_OPTIONS, QUERY_TIME_OPTIONS

### Community 105 - "createNavigationMemory"
Cohesion: 0.33
Nodes (6): canLeave(), databaseChanged(), renderTenantOptions(), routeScope(), tenants(), createNavigationMemory()

### Community 107 - "setSidebarState"
Cohesion: 0.40
Nodes (5): applyWorkspaceSettings(), closeNav(), loadWorkspaceSettings(), paintRealtime(), setSidebarState()

## Knowledge Gaps
- **22 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `esc()` connect `esc` to `app.js`, `stats/view.js`, `scope.js`, `imports/render.js`, `mount`, `loadingRows`, `Code Style — Arbiter`, `createNavigationMemory`, `json`, `Arsitektur Arbiter — Web & Tools`, `normalize_tenants`, `icon`, `incidents/render.js`, `json`, `mountWorkspace`, `6\. Komponen yang Dipakai`, `mount`?**
  _High betweenness centrality (0.266) - this node is a cross-community bridge._
- **Are the 6 inferred relationships involving `esc()` (e.g. with `Agent: code-reviewer` and `/review — Code review pass`) actually correct?**
  _`esc()` has 6 INFERRED edges - model-reasoned connections that need verification._
- **Should `core.py` be split into smaller, more focused modules?**
  _Cohesion score 0.1064102564102564 - nodes in this community are weakly interconnected._
- **Why does `safe_alerts()` connect `ai_triage.py` to `Arbiter Architecture — Wazuh Read, Classify, Correlate`, `main.py`, `Arsitektur Arbiter — Web & Tools`, `7\. Keamanan`, `api_get_ai_triage`, `5\. Cara Kerja`?**
  _High betweenness centrality (0.127) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `json()` (e.g. with `mount()` and `loadSelected()`) actually correct?**
  _`json()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Should `ref_node_assert` be split into smaller, more focused modules?**
  _Cohesion score 0.0707070707070707 - nodes in this community are weakly interconnected._
- **Why does `Agent: code-reviewer` connect `normalize_tenants` to `esc`?**
  _High betweenness centrality (0.111) - this node is a cross-community bridge._