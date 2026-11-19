# Graph Report - Arbiter  (2026-11-19)

## Corpus Check
- 165 files · ~147,400 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 15 file(s) not represented in the graph (top: .css 5, (none) 4, .woff2 4)

## Summary
- 1862 nodes · 4640 edges · 93 communities (66 shown, 27 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 137 edges (avg confidence: 0.9)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `a965f719`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- wazuh_intel.py
- ref_node_assert
- test_ui_api.py
- stats/view.js
- scope.js
- esc
- ApiIntegrationTests
- loadingRows
- AITriageAPITests
- start.sh
- SyntheticRoot
- Arbiter — blueprint rombak UI/UX
- Arbiter — audit UI/UX dan keputusan redesign
- ARSITEKTUR.md
- UIAPIContractTests
- AGENTS.md — Arbiter Project Context for AI Agents
- normalize_tenants
- mount
- lookup_remote_ip_cache_detail
- pathlib
- SafetyTests
- api_get_ai_triage
- Arbiter
- exports.py
- mount
- 2\. Deskripsi Produk
- db
- 📋 Protokol Eksekusi Rinci
- File Map and Interfaces
- SettingsAPITests
- test_pull_jobs.py
- app.js
- main.py
- exclusions.py
- SyntheticDB
- suggest_groups
- Request
- emptyState
- StatsEndpointContractTests
- .test_realtime_pull_respects_custom_severity_and_resets_since_on_severity_change
- Arsitektur Arbiter — Web & Tools
- ai_triage.py
- DatabaseTrustTests
- Dokumentasi Arbiter
- Arbiter UI/UX Redesign — Quiet Evidence Desk
- DESIGN.md
- settings.json
- ui-ux-redesign/README.md
- query.py
- Layout
- Control
- database.py
- intel.py
- 5\. Cara Kerja
- sanitize_text
- _FakeResult
- error-codes/view.js
- ⚡ Key Capabilities
- Arbiter Architecture — Wazuh Read, Classify, Correlate
- sync_remote_cache
- Any
- package.json
- ExclusionAPITests
- build
- Deploy config reference
- 5. Arsitektur Tools (Backend)
- Code Style — Arbiter
- Deploy Arbiter
- 8\. Instalasi
- stats-trust.test.mjs
- auth.py
- 6.4 Skema database
- 4. Arsitektur Web (Frontend)
- 8. Roadmap implementasi, tiap tahap bisa diverifikasi
- fix-issue.md
- validate-bash.sh
- setup-ai-symlinks.sh
- 8. Deployment
- 4. Wireframe dan first viewport
- safe_alerts
- _FakeCursor
- get_db
- 5. Information architecture & interaction contracts
- settings.py
- intel.py

## God Nodes (most connected - your core abstractions)
1. `esc()` - 95 edges
2. `json()` - 73 edges
3. `get_db()` - 71 edges
4. `icon()` - 64 edges
5. `mount()` - 46 edges
6. `mount()` - 42 edges
7. `AITriageAPITests` - 42 edges
8. `errorState()` - 39 edges
9. `UIAPIContractTests` - 37 edges
10. `mount()` - 35 edges

## Surprising Connections (you probably didn't know these)
- `5.7 Alur ekspor` --references--> `export_scope()`  [INFERRED]
  docs/ARSITEKTUR.md → app/main.py
- `4.2 Normalized alert` --references--> `normalize_alert()`  [INFERRED]
  docs/ARCHITECTURE.md → app/core.py
- `8.2 Metode A — Docker standalone (paling cepat)` --references--> `init_database()`  [INFERRED]
  docs/DOKUMENTASI.md → app/database.py
- `Credential redaction` --references--> `wazuh_password()`  [INFERRED]
  .ai/rules/api-conventions.md → app/settings.py
- `5.5 Korelasi` --references--> `build_attack_chains()`  [INFERRED]
  docs/DOKUMENTASI.md → app/wazuh_intel.py

## Import Cycles
- None detected.

## Communities (93 total, 27 thin omitted)

### Community 0 - "wazuh_intel.py"
Cohesion: 0.05
Nodes (47): local_ai_suggest_groups(), normalize_alert(), suggestions_with_fallback(), as_dict(), build_log_signature(), clean_val(), extract_alerts(), first_ip_in() (+39 more)

### Community 1 - "ref_node_assert"
Cohesion: 0.05
Nodes (34): setSidebarState(), report(), updateQuery(), createRouter(), change(), parseRoute(), withParams(), createNavigationMemory() (+26 more)

### Community 3 - "stats/view.js"
Cohesion: 0.09
Nodes (50): BENIGN_WHITELIST_PATTERNS, CHART_OPTIONS, distributionPercentages(), drilldownScrollBehavior(), generateMarkdownSummary(), generateStatsCSV(), INJECTION_PATTERNS, isMaliciousAlert() (+42 more)

### Community 4 - "scope.js"
Cohesion: 0.12
Nodes (33): caseHref(), cleanIds(), draftFrom(), draftsEqual(), evidenceParams(), incidentPayload(), incidentRoute(), selectedIds() (+25 more)

### Community 5 - "esc"
Cohesion: 0.17
Nodes (28): /review — Code review pass, filterIncidents(), SEVERITIES, STATUSES, allOptions(), options(), renderEvidence(), renderList() (+20 more)

### Community 7 - "loadingRows"
Cohesion: 0.08
Nodes (57): formatDuration(), mount(), paint(), paintProgress(), poll(), pollLater(), resumeJob(), stopPolling() (+49 more)

### Community 10 - "SyntheticRoot"
Cohesion: 0.22
Nodes (3): context(), load(), SyntheticRoot

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
Cohesion: 0.11
Nodes (22): Agent: code-reviewer, Agent: security-auditor, API Conventions — Arbiter, Credential redaction, Errors, Tenant scoping, add_group_members(), api_delete_wazuh_query() (+14 more)

### Community 17 - "mount"
Cohesion: 0.08
Nodes (66): apiURL(), json(), save(), databaseIdentity(), summarizeTelemetryRange(), mount(), loadStatus(), maintain() (+58 more)

### Community 18 - "lookup_remote_ip_cache_detail"
Cohesion: 0.26
Nodes (4): lookup_remote_ip_cache_detail(), _FakeConnection, _psycopg_modules(), RemoteCacheLookupTests

### Community 22 - "api_get_ai_triage"
Cohesion: 0.11
Nodes (18): current_wib_window_key(), get_triage_state_key(), triage_with_fallback(), with_exclusions(), _ai_triage_batch_size(), _ai_triage_candidate_count(), _ai_triage_exclude_ids(), _ai_triage_progress() (+10 more)

### Community 23 - "Arbiter"
Cohesion: 0.33
Nodes (5): Arbiter, Audience and usage, Development verification, Implemented case policy without schema changes, Product boundaries

### Community 24 - "exports.py"
Cohesion: 0.09
Nodes (11): generate_docx_landscape_report(), generate_gdocs_html_report(), generate_markdown_report(), generate_tsv_table(), generate_xlsx_workbook(), Arbiter SOC Desk Upgrades Implementation Plan, Global Constraints, Task 1: Favicon & Logo Arbiter (+3 more)

### Community 25 - "mount"
Cohesion: 0.14
Nodes (38): copyText(), aiSeverityKey(), alertFacts(), alertIndex(), boundedInteger(), DEFAULT_BATCH, formatWibWindowLabel(), GROUP_BY_OPTIONS (+30 more)

### Community 26 - "2\. Deskripsi Produk"
Cohesion: 0.40
Nodes (5): 2.1 Untuk siapa, 2.2 Batas produk, 2.3 Destinasi aplikasi, 2.4 Kemampuan inti, 2\. Deskripsi Produk

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
Cohesion: 0.04
Nodes (3): SettingsAPITests, __init__(), __init__()

### Community 31 - "test_pull_jobs.py"
Cohesion: 0.11
Nodes (7): base_config(), fake_get_db(), FakeConnection, FakeTransaction, load_pull_jobs(), PullJobTests, wait_for()

### Community 32 - "app.js"
Cohesion: 0.06
Nodes (41): adminOnlyPages, applyUserPermissions(), applyWorkspaceSettings(), canLeave(), checkPullActivity(), closeNav(), databaseChanged(), health() (+33 more)

### Community 33 - "main.py"
Cohesion: 0.08
Nodes (30): list_users(), init_database(), api_alert_pull_cancel(), api_alert_pull_status(), api_auth_me(), api_create_user(), api_database_status(), api_delete_user() (+22 more)

### Community 34 - "exclusions.py"
Cohesion: 0.16
Nodes (10): active_exclusion_rules(), build_exclusion_sql(), _coerce_enabled(), _escape_like(), glob_to_like(), normalize_exclusion_rule(), normalize_exclusions(), parse_wazuh_exclusion() (+2 more)

### Community 37 - "Request"
Cohesion: 0.16
Nodes (16): api_create_report_audit_log(), batch_update_review(), bulk_verdict_by_pattern(), claim_alert(), _current_username(), export_docx(), export_gdocs_html(), export_markdown() (+8 more)

### Community 38 - "emptyState"
Cohesion: 0.12
Nodes (21): ApiError, copyHTML(), download(), request(), caseReportRoute(), createReportSession(), exportURL(), reportAction() (+13 more)

### Community 42 - "Arsitektur Arbiter — Web & Tools"
Cohesion: 0.11
Nodes (18): 10. Failure Modes dan Degradasi, 11. Keputusan Arsitektur dan Trade-off, 12. Batas Skalabilitas, 13. Peta Direktori Arsitektural, 14. Cara Memverifikasi Arsitektur, 15. Ringkasan Arsitektur, 1. Gaya Arsitektur, 2. Diagram Konteks (C4 Level 1) (+10 more)

### Community 43 - "ai_triage.py"
Cohesion: 0.11
Nodes (21): ai_triage(), _alert_tenant(), _as_mapping(), _cluster_alerts(), _cluster_prompt(), format_wib_window_label(), _group_by_indicators(), find() (+13 more)

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

### Community 50 - "query.py"
Cohesion: 0.15
Nodes (11): build_filter_sql(), _canonical_field(), _canonical_op(), _clean_value(), _error(), _escape_like(), _glob_to_like(), normalize_filter() (+3 more)

### Community 52 - "Layout"
Cohesion: 0.29
Nodes (7): Global shell, Impor dan Laporan, Insiden, Klasifikasi & korelasi, Layout, Responsive, Triage

### Community 53 - "Control"
Cohesion: 0.12
Nodes (9): createImportSession(), importPage(), importResult(), mount(), update(), moduleURL, click(), Control (+1 more)

### Community 54 - "database.py"
Cohesion: 0.07
Nodes (37): _batch_insert_values(), _batch_instance(), bump_daily_metrics(), check_profile_ready(), _clean_expired_previews_locked(), create_preview_token(), get_active_profile(), get_active_profile_id() (+29 more)

### Community 57 - "intel.py"
Cohesion: 0.27
Nodes (4): enrich_ip(), _json_object(), query_abuseipdb(), EnrichFallbackTests

### Community 59 - "5\. Cara Kerja"
Cohesion: 0.22
Nodes (9): 5.1 Ingesti dan parsing, 5.2 Normalisasi, 5.3 Deduplikasi, 5.4 Klasifikasi, 5.5 Korelasi, 5.7 Triage dan insiden, 5.8 Threat intelligence dan redaksi, 5.9 Ekspor (+1 more)

### Community 62 - "error-codes/view.js"
Cohesion: 0.33
Nodes (8): ERROR_CODE_CATEGORIES, ERROR_CODE_SECTIONS, ERROR_CODES, filterErrorCodeSections(), mount(), render(), renderSections(), sectionBadge()

### Community 63 - "⚡ Key Capabilities"
Cohesion: 0.07
Nodes (28): 10. Privacy-First Redactor, 11. Official Deliverables (5 Export Paths), 1. Resilient Multi-Format Ingestion, 2. High-Precision Log Dissector (No False Fields), 3. Signature-Based Deduplication & Causal Correlation, 4. Enterprise Multi-Tenant Architecture, 5. Modular Destination UI, 6. Local AI Triage & Persistent Daily Case Grouping (`#/ai-triage`) (+20 more)

### Community 64 - "Arbiter Architecture — Wazuh Read, Classify, Correlate"
Cohesion: 0.11
Nodes (18): 10. Acceptance tests, 11. Non-goals, 1. Design constraints, 2. Dataset evidence used to shape the architecture, 3. End-to-end pipeline, 4.1 Raw Wazuh alert (minimum), 4.2 Normalized alert, 4.3 Classification result (+10 more)

### Community 65 - "sync_remote_cache"
Cohesion: 0.17
Nodes (5): _remote_profile_read_only(), _resolve_remote_db_url(), sync_remote_cache(), upsert_ip_cache(), RemoteSyncTests

### Community 66 - "Any"
Cohesion: 0.11
Nodes (27): get_db(), is_valid_ip(), api_ai_test(), api_ai_triage_save(), api_auth_login(), api_auth_logout(), api_database_config(), api_database_purge_alerts() (+19 more)

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
Cohesion: 0.20
Nodes (10): 8.1 Prasyarat, 8.2 Metode A — Docker standalone (paling cepat), 8.3 Metode B — Host mode (PostgreSQL yang sudah ada), 8.4 Metode C — Python lokal tanpa Docker, 8.5 Konfigurasi Wazuh Indexer (opsional, untuk Realtime), 8.6 Konfigurasi AI lokal (opsional), 8.7 Login pertama, 8.8 Verifikasi instalasi (+2 more)

### Community 75 - "stats-trust.test.mjs"
Cohesion: 0.28
Nodes (4): flush(), harness(), startSample(), stats()

### Community 76 - "auth.py"
Cohesion: 0.12
Nodes (24): authenticate_user(), create_session_token(), create_user(), _default_admin_credentials(), delete_user(), get_user(), _hash_password(), _load_raw_users() (+16 more)

### Community 77 - "6.4 Skema database"
Cohesion: 0.15
Nodes (13): 6.1 Stack, 6.2 Modul backend, 6.3 Modul frontend, 6.4.1 `wazuh.alerts`, 6.4.2 `wazuh.analysis_groups`, 6.4.3 `wazuh.alert_group_members`, 6.4.5 `public.ip_intel_cache`, 6.4.6 Tabel Remote milik provider (+5 more)

### Community 78 - "4. Arsitektur Web (Frontend)"
Cohesion: 0.29
Nodes (7): 4.1 Lapisan frontend, 4.2 Pola feature module, 4.3 Routing dan scope, 4.4 Alur render satu halaman, 4.5 Login gate dan hak tampilan, 4.6 State yang tidak dipersistensi, 4. Arsitektur Web (Frontend)

### Community 79 - "8. Roadmap implementasi, tiap tahap bisa diverifikasi"
Cohesion: 0.29
Nodes (7): 8. Roadmap implementasi, tiap tahap bisa diverifikasi, Phase 0 — safety & baseline, Phase 1 — modular foundation + shell, Phase 2 — triage-first experience, Phase 3 — insiden workspace, Phase 4 — impor dan laporan, Phase 5 — hardening & rollout

### Community 84 - "8. Deployment"
Cohesion: 0.33
Nodes (6): 8.1 Topologi A — Docker standalone, 8.2 Topologi B — Host mode, 8.3 Topologi C — Python lokal, 8.4 Topologi D — Reverse proxy TLS, 8.5 Startup sequence, 8. Deployment

### Community 86 - "4. Wireframe dan first viewport"
Cohesion: 0.33
Nodes (6): 4. Wireframe dan first viewport, A. Triage desktop, B. Insiden index dan case workspace, C. Impor, D. Laporan, E. Mobile

### Community 87 - "safe_alerts"
Cohesion: 0.13
Nodes (15): safe_alerts(), 7.1 Field filter chips, 7. API surfaces, 7.1 Trust boundary, 7.2 Kontrol keamanan per lapisan, 7.3 Batas yang harus dijaga saat deployment, 7. Arsitektur Keamanan, 5.6 AI Triage lokal (+7 more)

### Community 92 - "get_db"
Cohesion: 0.12
Nodes (14): api_add_exclusion(), api_delete_exclusion(), api_get_settings(), api_import_exclusions(), api_put_settings(), api_realtime_count(), api_update_exclusion(), _persist_exclusion_rules() (+6 more)

### Community 97 - "5. Information architecture & interaction contracts"
Cohesion: 0.40
Nodes (5): 5. Information architecture & interaction contracts, Accessibility, Editing dan destructive actions, Refresh, Scope

### Community 99 - "settings.py"
Cohesion: 0.08
Nodes (22): Backend (safe isolated suites), Design lint, Frontend, Testing — Arbiter, _boolean(), _deep_merge(), default_settings(), _http_error_reason() (+14 more)

### Community 100 - "intel.py"
Cohesion: 0.20
Nodes (3): is_private_ip(), lookup_remote_ip_cache(), _safe_remote_cache_error()

## Knowledge Gaps
- **27 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `esc()` connect `esc` to `app.js`, `stats/view.js`, `scope.js`, `emptyState`, `loadingRows`, `Code Style — Arbiter`, `Arsitektur Arbiter — Web & Tools`, `6.4 Skema database`, `normalize_tenants`, `mount`, `Control`, `safe_alerts`, `mount`, `error-codes/view.js`?**
  _High betweenness centrality (0.237) - this node is a cross-community bridge._
- **Are the 6 inferred relationships involving `esc()` (e.g. with `Agent: code-reviewer` and `/review — Code review pass`) actually correct?**
  _`esc()` has 6 INFERRED edges - model-reasoned connections that need verification._
- **Should `wazuh_intel.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05292929292929293 - nodes in this community are weakly interconnected._
- **Why does `7.2 Kontrol keamanan per lapisan` connect `safe_alerts` to `esc`?**
  _High betweenness centrality (0.105) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `json()` (e.g. with `mount()` and `loadSelected()`) actually correct?**
  _`json()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Should `ref_node_assert` be split into smaller, more focused modules?**
  _Cohesion score 0.0546583850931677 - nodes in this community are weakly interconnected._
- **Why does `safe_alerts()` connect `safe_alerts` to `main.py`, `ai_triage.py`, `api_get_ai_triage`?**
  _High betweenness centrality (0.105) - this node is a cross-community bridge._