# Graph Report - Arbiter  (2026-11-17)

## Corpus Check
- 152 files · ~129,118 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 15 file(s) not represented in the graph (top: .css 5, (none) 4, .woff2 4)

## Summary
- 1641 nodes · 3962 edges · 99 communities (76 shown, 23 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 122 edges (avg confidence: 0.91)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `368acc12`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- core.py
- ref_node_assert
- test_ui_api.py
- stats/view.js
- esc
- Control
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
- SyntheticDB
- main.py
- Arbiter
- exports.py
- mount
- intel.py
- db
- 📋 Protokol Eksekusi Rinci
- File Map and Interfaces
- SettingsAPITests
- get_db
- app.js
- Any
- exclusions.py
- load_settings
- wazuh_intel.py
- router-history.test.mjs
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
- ai_triage
- database-workspace.test.mjs
- _FakeConnection
- Testing — Arbiter
- 5\. Cara Kerja
- sanitize_text
- enrich_ip
- settings.py
- ⚡ Key Capabilities
- Arbiter Architecture — Wazuh Read, Classify, Correlate
- _SyncConnection
- api_get_ai_triage
- package.json
- ExclusionAPITests
- build
- Deploy config reference
- secure_store.py
- Code Style — Arbiter
- Deploy Arbiter
- 8\. Instalasi
- stats-trust.test.mjs
- test_settings.py
- imports/view.js
- auth.py
- test_intel_cache.py
- fix-issue.md
- validate-bash.sh
- setup-ai-symlinks.sh
- query.py
- test_wazuh_connection
- mountWorkspace
- 7\. Keamanan
- normalize_alert
- test_ai_triage.py
- _FakeCursor
- SyntheticRoot
- enrich_intel
- 6. Correlation policy
- 2\. Deskripsi Produk
- 5. Classification policy
- database-gates.test.mjs
- .test_realtime_pull_respects_custom_severity_and_resets_since_on_severity_change

## God Nodes (most connected - your core abstractions)
1. `esc()` - 86 edges
2. `json()` - 60 edges
3. `get_db()` - 60 edges
4. `icon()` - 55 edges
5. `AITriageAPITests` - 40 edges
6. `mount()` - 40 edges
7. `mount()` - 36 edges
8. `errorState()` - 34 edges
9. `UIAPIContractTests` - 33 edges
10. `load_settings()` - 30 edges

## Surprising Connections (you probably didn't know these)
- `5.7 Alur ekspor` --references--> `export_scope()`  [INFERRED]
  docs/ARSITEKTUR.md → app/main.py
- `5.8 Profil database dan pemeliharaan` --references--> `get_db()`  [INFERRED]
  docs/ARSITEKTUR.md → app/database.py
- `6.3 Ordered chain` --references--> `build_attack_chains()`  [INFERRED]
  docs/ARCHITECTURE.md → app/wazuh_intel.py
- `5.5 Korelasi` --references--> `build_attack_chains()`  [INFERRED]
  docs/DOKUMENTASI.md → app/wazuh_intel.py
- `6.1 Response linkage` --references--> `correlate_alerts()`  [INFERRED]
  docs/ARCHITECTURE.md → app/wazuh_intel.py

## Import Cycles
- None detected.

## Communities (99 total, 23 thin omitted)

### Community 0 - "core.py"
Cohesion: 0.15
Nodes (11): extract_alerts(), first_ip_in(), kv_details(), normalize_log_for_signature(), parse_export(), parse_log_line(), parse_timestamp_iso(), parse_to_datetime() (+3 more)

### Community 1 - "ref_node_assert"
Cohesion: 0.09
Nodes (19): url, harness(), status, moduleURL, modelURL, mainPy, root, settingsView (+11 more)

### Community 3 - "stats/view.js"
Cohesion: 0.12
Nodes (37): BENIGN_WHITELIST_PATTERNS, CHART_OPTIONS, distributionPercentages(), drilldownScrollBehavior(), generateMarkdownSummary(), generateStatsCSV(), INJECTION_PATTERNS, isMaliciousAlert() (+29 more)

### Community 4 - "esc"
Cohesion: 0.19
Nodes (15): /review — Code review pass, notify(), render(), renderControls(), renderIntro(), tenantOptionsHTML(), ERROR_CODE_CATEGORIES, ERROR_CODE_SECTIONS (+7 more)

### Community 5 - "Control"
Cohesion: 0.22
Nodes (3): click(), Control, fixture()

### Community 7 - "loadingRows"
Cohesion: 0.12
Nodes (41): mount(), pull(), render(), saveRealtime(), schedule(), aiLabel(), clone(), DEFAULT_SETTINGS (+33 more)

### Community 10 - "json"
Cohesion: 0.20
Nodes (20): ApiError, copyHTML(), download(), request(), caseReportRoute(), createReportSession(), exportURL(), reportAction() (+12 more)

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
Cohesion: 0.15
Nodes (13): Agent: code-reviewer, Agent: security-auditor, Tenant scoping, api_ai_triage_save(), batch_update_review(), bulk_full_logs(), create_group(), export_scope() (+5 more)

### Community 17 - "icon"
Cohesion: 0.17
Nodes (25): copyText(), json(), save(), databaseIdentity(), summarizeTelemetryRange(), mount(), loadStatus(), maintain() (+17 more)

### Community 18 - "Control"
Cohesion: 0.22
Nodes (3): click(), Control, fixture()

### Community 19 - "incidents/render.js"
Cohesion: 0.11
Nodes (39): caseHref(), cleanIds(), draftFrom(), draftsEqual(), evidenceParams(), filterIncidents(), incidentPayload(), incidentRoute() (+31 more)

### Community 22 - "main.py"
Cohesion: 0.16
Nodes (21): get_db(), init_database(), add_group_members(), api_database_status(), api_delete_exclusion(), api_delete_wazuh_query(), api_get_settings(), delete_group() (+13 more)

### Community 23 - "Arbiter"
Cohesion: 0.33
Nodes (5): Arbiter, Audience and usage, Development verification, Implemented case policy without schema changes, Product boundaries

### Community 24 - "exports.py"
Cohesion: 0.07
Nodes (21): generate_docx_landscape_report(), generate_gdocs_html_report(), generate_markdown_report(), generate_tsv_table(), generate_xlsx_workbook(), export_csv(), export_docx(), export_gdocs_html() (+13 more)

### Community 25 - "mount"
Cohesion: 0.19
Nodes (30): aiSeverityKey(), alertFacts(), alertIndex(), boundedInteger(), formatWibWindowLabel(), GROUP_BY_OPTIONS, groupAlerts(), LIMITS (+22 more)

### Community 26 - "intel.py"
Cohesion: 0.12
Nodes (4): lookup_remote_ip_cache(), _remote_profile_read_only(), _resolve_remote_db_url(), _safe_remote_cache_error()

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
Cohesion: 0.08
Nodes (3): SettingsAPITests, __init__(), __init__()

### Community 31 - "get_db"
Cohesion: 0.28
Nodes (12): list_users(), api_auth_me(), api_create_user(), api_delete_user(), api_list_users(), api_save_wazuh_query(), api_update_user(), api_update_wazuh_notepad() (+4 more)

### Community 32 - "app.js"
Cohesion: 0.07
Nodes (37): adminOnlyPages, applyUserPermissions(), applyWorkspaceSettings(), canLeave(), closeNav(), databaseChanged(), health(), help (+29 more)

### Community 33 - "Any"
Cohesion: 0.15
Nodes (17): api_add_exclusion(), api_ai_test(), api_auth_login(), api_auth_logout(), api_database_config(), api_database_purge_alerts(), api_database_purge_incidents(), api_database_test() (+9 more)

### Community 34 - "exclusions.py"
Cohesion: 0.16
Nodes (10): active_exclusion_rules(), build_exclusion_sql(), _coerce_enabled(), _escape_like(), glob_to_like(), normalize_exclusion_rule(), normalize_exclusions(), parse_wazuh_exclusion() (+2 more)

### Community 35 - "load_settings"
Cohesion: 0.13
Nodes (10): API Conventions — Arbiter, Credential redaction, Errors, api_realtime_count(), load_settings(), migrate_settings(), wazuh_password(), _fmt() (+2 more)

### Community 36 - "wazuh_intel.py"
Cohesion: 0.25
Nodes (16): as_dict(), clean_val(), _alert_key(), _as_json(), build_attack_chains(), _chain_steps(), correlate_alerts(), _extract_payload_indicators() (+8 more)

### Community 38 - "mount"
Cohesion: 0.14
Nodes (31): apiURL(), loadBatchIncidentOptions(), intelBadge(), intelSummary(), renderQueue(), renderTriageSummary(), summaryRequestParams(), chainLine() (+23 more)

### Community 40 - "triage-request.test.mjs"
Cohesion: 0.31
Nodes (3): createSelection(), Element, requestsFor()

### Community 41 - "normalize_alert"
Cohesion: 0.13
Nodes (9): _bump(), classify_alert(), extract_active_response(), _level_priority(), _profile_for(), _active_response(), ActiveResponseReadTests, ClassificationTests (+1 more)

### Community 42 - "Arsitektur Arbiter — Web & Tools"
Cohesion: 0.05
Nodes (43): 10. Failure Modes dan Degradasi, 11. Keputusan Arsitektur dan Trade-off, 12. Batas Skalabilitas, 13. Peta Direktori Arsitektural, 14. Cara Memverifikasi Arsitektur, 15. Ringkasan Arsitektur, 1. Gaya Arsitektur, 2. Diagram Konteks (C4 Level 1) (+35 more)

### Community 43 - "ai_triage.py"
Cohesion: 0.20
Nodes (12): _alert_tenant(), _cluster_alerts(), current_wib_window_key(), format_wib_window_label(), _group_by_rule_description(), heuristic_triage(), _heuristic_verdict(), _intel_summary() (+4 more)

### Community 45 - "Dokumentasi Arbiter"
Cohesion: 0.15
Nodes (13): 10\. Pengembangan dan Pemeliharaan, 11\. Lisensi, 1\. Ringkasan, 3.1 Workflow analis (harian), 3.2 Workflow data, 3.3 Siklus hidup insiden, 3\. Workflow, 4.1 Alur end-to-end (+5 more)

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
Cohesion: 0.07
Nodes (32): check_profile_ready(), _clean_expired_previews_locked(), create_preview_token(), get_active_profile(), get_active_profile_id(), get_database_status(), get_database_status_unavailable(), get_db_connection() (+24 more)

### Community 55 - "ai_triage"
Cohesion: 0.19
Nodes (4): ai_triage(), _validate_cluster_verdicts(), LocalAIUnavailable, ollama_request()

### Community 56 - "database-workspace.test.mjs"
Cohesion: 0.25
Nodes (11): setSidebarState(), parseRoute(), createNavigationMemory(), normalizeSidebarState(), readSidebarState(), SIDEBAR_KEY, toggleSidebarState(), writeSidebarState() (+3 more)

### Community 57 - "_FakeConnection"
Cohesion: 0.24
Nodes (5): _json_object(), lookup_remote_ip_cache_detail(), _FakeConnection, _psycopg_modules(), RemoteCacheLookupTests

### Community 58 - "Testing — Arbiter"
Cohesion: 0.33
Nodes (5): Backend (safe isolated suites), Design lint, Frontend, Testing — Arbiter, test_ollama()

### Community 59 - "5\. Cara Kerja"
Cohesion: 0.22
Nodes (9): 5.1 Ingesti dan parsing, 5.2 Normalisasi, 5.3 Deduplikasi, 5.4 Klasifikasi, 5.5 Korelasi, 5.7 Triage dan insiden, 5.8 Threat intelligence dan redaksi, 5.9 Ekspor (+1 more)

### Community 61 - "enrich_ip"
Cohesion: 0.22
Nodes (4): enrich_ip(), is_private_ip(), query_abuseipdb(), EnrichFallbackTests

### Community 62 - "settings.py"
Cohesion: 0.22
Nodes (10): api_put_settings(), _boolean(), _deep_merge(), default_settings(), intel_abuseipdb_key(), normalize_ollama_base_url(), redact_settings(), save_settings() (+2 more)

### Community 63 - "⚡ Key Capabilities"
Cohesion: 0.07
Nodes (28): 10. Privacy-First Redactor, 11. Official Deliverables (5 Export Paths), 1. Resilient Multi-Format Ingestion, 2. High-Precision Log Dissector (No False Fields), 3. Signature-Based Deduplication & Causal Correlation, 4. Enterprise Multi-Tenant Architecture, 5. Modular Destination UI, 6. Local AI Triage & Persistent Daily Case Grouping (`#/ai-triage`) (+20 more)

### Community 64 - "Arbiter Architecture — Wazuh Read, Classify, Correlate"
Cohesion: 0.14
Nodes (14): 10. Acceptance tests, 11. Non-goals, 1. Design constraints, 2. Dataset evidence used to shape the architecture, 3. End-to-end pipeline, 4.1 Raw Wazuh alert (minimum), 4.2 Normalized alert, 4.3 Classification result (+6 more)

### Community 66 - "api_get_ai_triage"
Cohesion: 0.15
Nodes (11): get_triage_state_key(), _load_profile_overrides(), api_ai_triage(), api_get_ai_triage(), api_list_wazuh_queries(), _build_ai_triage_where(), _find_matching_open_ai_group(), _sync_triage_groups_with_saved_incidents() (+3 more)

### Community 67 - "package.json"
Cohesion: 0.20
Nodes (9): description, engines, node, name, private, scripts, test, type (+1 more)

### Community 69 - "build"
Cohesion: 0.29
Nodes (6): build, volumes, context, dockerfile, services, arbiter

### Community 70 - "Deploy config reference"
Cohesion: 0.33
Nodes (5): Containers, Deploy config reference, Environment variables, Reverse proxy (optional), Secrets

### Community 71 - "secure_store.py"
Cohesion: 0.22
Nodes (8): _verify_password(), decrypt_text(), encrypt_text(), _fernet(), is_encrypted(), _key_path(), _read_or_create_key_file(), SecretStoreError

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

### Community 76 - "test_settings.py"
Cohesion: 0.15
Nodes (6): api_realtime_pull(), _http_error_reason(), _normalize_wazuh_timestamp(), _valid_timestamp(), _wazuh_request(), wazuh_search()

### Community 77 - "imports/view.js"
Cohesion: 0.36
Nodes (5): createImportSession(), importPage(), importResult(), mount(), update()

### Community 78 - "auth.py"
Cohesion: 0.32
Nodes (12): authenticate_user(), create_session_token(), create_user(), _default_admin_credentials(), delete_user(), get_user(), _hash_password(), _load_raw_users() (+4 more)

### Community 84 - "query.py"
Cohesion: 0.21
Nodes (10): with_exclusions(), _exclusion_document(), get_facet_alert_ids(), get_stats(), get_suggestions(), list_alerts(), triage_summary(), alert_where() (+2 more)

### Community 85 - "test_wazuh_connection"
Cohesion: 0.18
Nodes (3): test_wazuh_connection(), wazuh_alert_query(), _wazuh_opener()

### Community 86 - "mountWorkspace"
Cohesion: 0.41
Nodes (12): renderEvidence(), mountWorkspace(), context(), initial(), loadPage(), loadSelected(), panels(), refresh() (+4 more)

### Community 87 - "7\. Keamanan"
Cohesion: 0.20
Nodes (10): safe_alerts(), 7. API surfaces, 5.6 AI Triage lokal, 7.1 Prinsip desain, 7.2 Autentikasi dan otorisasi, 7.3 Rahasia saat istirahat, 7.4 Isolasi jaringan dan SSRF, 7.5 Perlindungan data dan ekspor (+2 more)

### Community 88 - "normalize_alert"
Cohesion: 0.18
Nodes (6): local_ai_suggest_groups(), normalize_alert(), suggestions_with_fallback(), build_log_signature(), DedupSafeguardTests, NormalizeIntegrationTests

### Community 91 - "SyntheticRoot"
Cohesion: 0.22
Nodes (3): context(), load(), SyntheticRoot

### Community 92 - "enrich_intel"
Cohesion: 0.32
Nodes (4): is_valid_ip(), sync_remote_cache(), upsert_ip_cache(), enrich_intel()

### Community 93 - "6. Correlation policy"
Cohesion: 0.40
Nodes (5): 6.1 Response linkage, 6.2 Canonical group identity, 6.3 Ordered chain, 6.4 Correlation confidence, 6. Correlation policy

### Community 94 - "2\. Deskripsi Produk"
Cohesion: 0.40
Nodes (5): 2.1 Untuk siapa, 2.2 Batas produk, 2.3 Destinasi aplikasi, 2.4 Kemampuan inti, 2\. Deskripsi Produk

### Community 95 - "5. Classification policy"
Cohesion: 0.50
Nodes (4): 5.1 Curated rule profiles (explicit, not trained), 5.2 Context signals, 5.3 Wording policy, 5. Classification policy

## Knowledge Gaps
- **23 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `esc()` connect `esc` to `app.js`, `stats/view.js`, `mount`, `loadingRows`, `Code Style — Arbiter`, `json`, `Arsitektur Arbiter — Web & Tools`, `imports/view.js`, `normalize_tenants`, `icon`, `incidents/render.js`, `mountWorkspace`, `database.py`, `mount`?**
  _High betweenness centrality (0.221) - this node is a cross-community bridge._
- **Are the 6 inferred relationships involving `esc()` (e.g. with `Agent: code-reviewer` and `/review — Code review pass`) actually correct?**
  _`esc()` has 6 INFERRED edges - model-reasoned connections that need verification._
- **Should `ref_node_assert` be split into smaller, more focused modules?**
  _Cohesion score 0.08502024291497975 - nodes in this community are weakly interconnected._
- **Why does `safe_alerts()` connect `7\. Keamanan` to `api_get_ai_triage`, `ai_triage.py`, `Arsitektur Arbiter — Web & Tools`, `main.py`?**
  _High betweenness centrality (0.118) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `json()` (e.g. with `mount()` and `loadSelected()`) actually correct?**
  _`json()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Should `test_ui_api.py` be split into smaller, more focused modules?**
  _Cohesion score 0.14666666666666667 - nodes in this community are weakly interconnected._
- **Why does `Arsitektur Arbiter — Web & Tools` connect `Arsitektur Arbiter — Web & Tools` to `ARSITEKTUR.md`?**
  _High betweenness centrality (0.110) - this node is a cross-community bridge._