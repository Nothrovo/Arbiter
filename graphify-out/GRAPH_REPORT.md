# Graph Report - Arbiter  (2026-11-13)

## Corpus Check
- 148 files · ~113,663 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 15 file(s) not represented in the graph (top: .css 5, (none) 4, .woff2 4)

## Summary
- 1456 nodes · 3626 edges · 84 communities (66 shown, 18 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 105 edges (avg confidence: 0.9)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `b2eb7ac6`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- core.py
- ref_node_assert
- test_ui_api.py
- stats/view.js
- tenantScope
- imports/render.js
- ApiIntegrationTests
- loadingRows
- AITriageAPITests
- start.sh
- _cluster_alerts
- Arbiter — blueprint rombak UI/UX
- Arbiter — audit UI/UX dan keputusan redesign
- Arbiter
- UIAPIContractTests
- AGENTS.md — Arbiter Project Context for AI Agents
- get
- incidents-view.test.mjs
- Control
- incidents/render.js
- SafetyTests
- SyntheticDB
- database.py
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
- main.py
- wazuh_search
- settings.py
- wazuh_intel.py
- router.js
- esc
- StatsEndpointContractTests
- triage-request.test.mjs
- normalize_alert
- normalize_tenants
- ai_triage.py
- DatabaseTrustTests
- secure_store.py
- Arbiter UI/UX Redesign — Quiet Evidence Desk
- DESIGN.md
- settings.json
- ui-ux-redesign/README.md
- 8. Roadmap implementasi, tiap tahap bisa diverifikasi
- 4. Wireframe dan first viewport
- Layout
- 5. Information architecture & interaction contracts
- auth.py
- json
- database-workspace.test.mjs
- _FakeConnection
- ai_triage
- api_get_ai_triage
- sanitize_text
- enrich_ip
- test_wazuh_connection
- ⚡ Key Capabilities
- Arbiter Architecture — Wazuh Read, Classify, Correlate
- _SyncConnection
- classify_alert
- package.json
- build
- Deploy config reference
- 🚀 Setup & Getting Started
- Code Style — Arbiter
- Deploy Arbiter
- 6. Correlation policy
- .test_remote_cache_records_are_not_written_back
- feature-loader.test.mjs
- 4. Data contracts
- 5. Classification policy
- _FakeResult
- fix-issue.md
- validate-bash.sh
- setup-ai-symlinks.sh

## God Nodes (most connected - your core abstractions)
1. `esc()` - 82 edges
2. `json()` - 58 edges
3. `get_db()` - 55 edges
4. `icon()` - 52 edges
5. `mount()` - 40 edges
6. `AITriageAPITests` - 38 edges
7. `mount()` - 36 edges
8. `errorState()` - 33 edges
9. `UIAPIContractTests` - 33 edges
10. `mount()` - 30 edges

## Surprising Connections (you probably didn't know these)
- `7. API surfaces` --references--> `safe_alerts()`  [INFERRED]
  docs/ARCHITECTURE.md → app/ai_triage.py
- `4.2 Normalized alert` --references--> `normalize_alert()`  [INFERRED]
  docs/ARCHITECTURE.md → app/core.py
- `Frontend (JS)` --references--> `esc()`  [INFERRED]
  .ai/rules/code-style.md → app/static/js/ui/primitives.js
- `6.1 Response linkage` --references--> `correlate_alerts()`  [INFERRED]
  docs/ARCHITECTURE.md → app/wazuh_intel.py
- `Key finding: Active Response is evidence, not a separate attack` --references--> `correlate_alerts()`  [INFERRED]
  docs/ARCHITECTURE.md → app/wazuh_intel.py

## Import Cycles
- None detected.

## Communities (84 total, 18 thin omitted)

### Community 0 - "core.py"
Cohesion: 0.11
Nodes (13): build_log_signature(), extract_alerts(), first_ip_in(), kv_details(), normalize_log_for_signature(), parse_export(), parse_log_line(), parse_timestamp_iso() (+5 more)

### Community 1 - "ref_node_assert"
Cohesion: 0.09
Nodes (17): url, harness(), profiles, modelURL, mainPy, root, settingsView, triageView (+9 more)

### Community 3 - "stats/view.js"
Cohesion: 0.11
Nodes (36): BENIGN_WHITELIST_PATTERNS, CHART_OPTIONS, distributionPercentages(), drilldownScrollBehavior(), generateMarkdownSummary(), generateStatsCSV(), INJECTION_PATTERNS, isMaliciousAlert() (+28 more)

### Community 4 - "tenantScope"
Cohesion: 0.36
Nodes (7): scopeParams(), resolveAlertIdsForSecondaryKeys(), paramsForScope(), scopeKey(), rawTenantValues(), tenantScope(), tenantValues()

### Community 5 - "imports/render.js"
Cohesion: 0.12
Nodes (9): createImportSession(), importPage(), importResult(), mount(), update(), moduleURL, click(), Control (+1 more)

### Community 7 - "loadingRows"
Cohesion: 0.13
Nodes (35): mount(), pull(), render(), saveRealtime(), schedule(), aiLabel(), clone(), DEFAULT_SETTINGS (+27 more)

### Community 10 - "_cluster_alerts"
Cohesion: 0.23
Nodes (3): _cluster_alerts(), _cluster_prompt(), _validate_cluster_verdicts()

### Community 11 - "Arbiter — blueprint rombak UI/UX"
Cohesion: 0.17
Nodes (12): 10. Open decisions sebelum build, 1. Keputusan desain, 2. Sitemap yang diusulkan, 3. Apa yang boleh muncul di depan, 6. Arsitektur module yang disarankan, 7. Kesiapan backend: pakai yang ada vs perlu kerja, 9. Acceptance checklist, Alternatif yang dibandingkan (+4 more)

### Community 12 - "Arbiter — audit UI/UX dan keputusan redesign"
Cohesion: 0.15
Nodes (13): Arbiter — audit UI/UX dan keputusan redesign, Bukti komposisi dan responsive, Detector Impeccable — hasil nyata, bukan daftar bug unik, Hallmark audit — subset yang sesuai operational app, Handoff, Metode dan batas bukti, Nielsen heuristics, Persona dan emotional journey (+5 more)

### Community 13 - "Arbiter"
Cohesion: 0.17
Nodes (10): Arbiter, 🛠️ Architecture & Tech Stack, Dataset calibration and limits, 📄 License, 🎯 Overview, 🔒 Security & Privacy Notice, 📖 SOC Analyst Quickstart Workflow, 🧪 Testing & Quality Assurance (+2 more)

### Community 15 - "AGENTS.md — Arbiter Project Context for AI Agents"
Cohesion: 0.13
Nodes (14): AGENTS.md — Arbiter Project Context for AI Agents, Architecture (frontend), Design direction: Quiet Evidence Desk, Four destinations (not a monolithic page), Graph, Key policies, Privacy — STRICT, Repository layout (+6 more)

### Community 16 - "get"
Cohesion: 0.13
Nodes (15): api_get_settings(), api_realtime_count(), favicon(), get_alert_detail(), get_group_detail(), get_stats(), get_suggestions(), get_tenants() (+7 more)

### Community 17 - "incidents-view.test.mjs"
Cohesion: 0.22
Nodes (3): context(), load(), SyntheticRoot

### Community 18 - "Control"
Cohesion: 0.22
Nodes (3): click(), Control, fixture()

### Community 19 - "incidents/render.js"
Cohesion: 0.14
Nodes (20): cleanIds(), draftFrom(), draftsEqual(), evidenceParams(), incidentPayload(), incidentRoute(), selectedIds(), SEVERITIES (+12 more)

### Community 21 - "SyntheticDB"
Cohesion: 0.15
Nodes (4): Task 2: Build SQL aggregation endpoints and schema support, TriageScopeTests, load_isolated_api(), SyntheticDB

### Community 22 - "database.py"
Cohesion: 0.13
Nodes (15): _clean_expired_previews_locked(), create_preview_token(), get_active_profile(), get_database_status(), get_db_connection(), ingest_alert_with_dedup(), mask_connection_url(), _persist_profile_overrides() (+7 more)

### Community 23 - "Arbiter"
Cohesion: 0.33
Nodes (5): Arbiter, Audience and usage, Development verification, Implemented case policy without schema changes, Product boundaries

### Community 24 - "exports.py"
Cohesion: 0.07
Nodes (21): generate_docx_landscape_report(), generate_gdocs_html_report(), generate_markdown_report(), generate_tsv_table(), generate_xlsx_workbook(), export_csv(), export_docx(), export_gdocs_html() (+13 more)

### Community 25 - "mount"
Cohesion: 0.16
Nodes (34): aiSeverityKey(), alertFacts(), alertIndex(), boundedInteger(), formatWibWindowLabel(), GROUP_BY_OPTIONS, groupAlerts(), LIMITS (+26 more)

### Community 26 - "intel.py"
Cohesion: 0.13
Nodes (9): _json_object(), lookup_remote_ip_cache(), lookup_remote_ip_cache_detail(), query_abuseipdb(), _remote_profile_read_only(), _resolve_remote_db_url(), _safe_remote_cache_error(), sync_remote_cache() (+1 more)

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
Cohesion: 0.08
Nodes (6): API Conventions — Arbiter, Credential redaction, Errors, wazuh_password(), SettingsAPITests, __init__()

### Community 31 - "get_db"
Cohesion: 0.17
Nodes (20): list_users(), get_db(), init_database(), _load_profile_overrides(), api_auth_me(), api_create_user(), api_delete_user(), api_delete_wazuh_query() (+12 more)

### Community 32 - "app.js"
Cohesion: 0.07
Nodes (33): adminOnlyPages, applyWorkspaceSettings(), canLeave(), closeNav(), databaseChanged(), health(), help, loadWorkspaceSettings() (+25 more)

### Community 33 - "main.py"
Cohesion: 0.14
Nodes (20): api_ai_test(), api_ai_triage_save(), api_auth_login(), api_auth_logout(), api_database_config(), api_database_purge_alerts(), api_database_purge_incidents(), api_database_switch() (+12 more)

### Community 34 - "wazuh_search"
Cohesion: 0.10
Nodes (7): _normalize_wazuh_timestamp(), _valid_timestamp(), _wazuh_request(), wazuh_search(), _fmt(), main(), _existing()

### Community 35 - "settings.py"
Cohesion: 0.21
Nodes (12): api_put_settings(), encrypt_text(), _boolean(), _deep_merge(), default_settings(), load_settings(), migrate_settings(), normalize_ollama_base_url() (+4 more)

### Community 36 - "wazuh_intel.py"
Cohesion: 0.27
Nodes (15): as_dict(), clean_val(), _alert_key(), _as_json(), build_attack_chains(), _chain_steps(), correlate_alerts(), _extract_payload_indicators() (+7 more)

### Community 37 - "router.js"
Cohesion: 0.31
Nodes (3): createRouter(), change(), parseRoute()

### Community 38 - "esc"
Cohesion: 0.05
Nodes (117): /review — Code review pass, ApiError, apiURL(), copyHTML(), copyText(), download(), json(), request() (+109 more)

### Community 40 - "triage-request.test.mjs"
Cohesion: 0.31
Nodes (3): createSelection(), Element, requestsFor()

### Community 41 - "normalize_alert"
Cohesion: 0.15
Nodes (6): normalize_alert(), extract_active_response(), _active_response(), ActiveResponseReadTests, CorrelationTests, NormalizeIntegrationTests

### Community 42 - "normalize_tenants"
Cohesion: 0.16
Nodes (16): Agent: code-reviewer, Agent: security-auditor, Tenant scoping, add_group_members(), delete_group(), export_scope(), remove_group_member(), _scope_tenant_value() (+8 more)

### Community 43 - "ai_triage.py"
Cohesion: 0.22
Nodes (10): _alert_tenant(), format_wib_window_label(), _group_by_rule_description(), heuristic_triage(), _heuristic_verdict(), _intel_summary(), merge_triage_groups(), _partition_by_tenant() (+2 more)

### Community 45 - "secure_store.py"
Cohesion: 0.19
Nodes (8): _verify_password(), decrypt_text(), _fernet(), is_encrypted(), _key_path(), _read_or_create_key_file(), SecretStoreError, intel_abuseipdb_key()

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

### Community 54 - "auth.py"
Cohesion: 0.32
Nodes (12): authenticate_user(), create_session_token(), create_user(), _default_admin_credentials(), delete_user(), get_user(), _hash_password(), _load_raw_users() (+4 more)

### Community 55 - "json"
Cohesion: 0.17
Nodes (4): local_ai_suggest_groups(), suggestions_with_fallback(), is_malicious_alert_record(), _http_error_reason()

### Community 56 - "database-workspace.test.mjs"
Cohesion: 0.29
Nodes (9): createNavigationMemory(), normalizeSidebarState(), readSidebarState(), SIDEBAR_KEY, toggleSidebarState(), writeSidebarState(), shell(), source (+1 more)

### Community 57 - "_FakeConnection"
Cohesion: 0.25
Nodes (3): _FakeConnection, _psycopg_modules(), RemoteCacheLookupTests

### Community 58 - "ai_triage"
Cohesion: 0.15
Nodes (7): Backend (safe isolated suites), Design lint, Frontend, Testing — Arbiter, ai_triage(), LocalAIUnavailable, ollama_request()

### Community 59 - "api_get_ai_triage"
Cohesion: 0.20
Nodes (9): current_wib_window_key(), get_triage_state_key(), safe_alerts(), triage_with_fallback(), api_ai_triage(), api_get_ai_triage(), _build_ai_triage_where(), _find_matching_open_ai_group() (+1 more)

### Community 61 - "enrich_ip"
Cohesion: 0.23
Nodes (5): enrich_ip(), is_private_ip(), is_valid_ip(), enrich_intel(), EnrichFallbackTests

### Community 62 - "test_wazuh_connection"
Cohesion: 0.18
Nodes (3): test_wazuh_connection(), wazuh_alert_query(), _wazuh_opener()

### Community 63 - "⚡ Key Capabilities"
Cohesion: 0.17
Nodes (12): 10. Privacy-First Redactor, 11. Official Deliverables (5 Export Paths), 1. Resilient Multi-Format Ingestion, 2. High-Precision Log Dissector (No False Fields), 3. Signature-Based Deduplication & Causal Correlation, 4. Enterprise Multi-Tenant Architecture, 5. Modular Destination UI, 6. Local AI Triage & Persistent Daily Case Grouping (`#/ai-triage`) (+4 more)

### Community 64 - "Arbiter Architecture — Wazuh Read, Classify, Correlate"
Cohesion: 0.18
Nodes (11): 10. Acceptance tests, 11. Non-goals, 1. Design constraints, 2. Dataset evidence used to shape the architecture, 3. End-to-end pipeline, 7. API surfaces, 8. Storage and migration, 9. Failure modes and handling (+3 more)

### Community 66 - "classify_alert"
Cohesion: 0.27
Nodes (5): _bump(), classify_alert(), _level_priority(), _profile_for(), ClassificationTests

### Community 67 - "package.json"
Cohesion: 0.20
Nodes (9): description, engines, node, name, private, scripts, test, type (+1 more)

### Community 69 - "build"
Cohesion: 0.29
Nodes (6): build, volumes, context, dockerfile, services, arbiter

### Community 70 - "Deploy config reference"
Cohesion: 0.33
Nodes (5): Containers, Deploy config reference, Environment variables, Reverse proxy (optional), Secrets

### Community 71 - "🚀 Setup & Getting Started"
Cohesion: 0.33
Nodes (6): Connecting to a Neuropetra `ip_intel` database, Method A: Standalone Docker Setup (Fastest for new users), Method B: Host Mode (Connect to existing PostgreSQL / IP Intel), Method C: Local Python Setup (Without Docker), Prerequisites, 🚀 Setup & Getting Started

### Community 72 - "Code Style — Arbiter"
Cohesion: 0.40
Nodes (4): Code Style — Arbiter, CSS, Frontend (JS), Python

### Community 73 - "Deploy Arbiter"
Cohesion: 0.40
Nodes (4): Deploy Arbiter, Local dev, Pre-deploy checks, Production (Docker Compose)

### Community 74 - "6. Correlation policy"
Cohesion: 0.40
Nodes (5): 6.1 Response linkage, 6.2 Canonical group identity, 6.3 Ordered chain, 6.4 Correlation confidence, 6. Correlation policy

### Community 77 - "4. Data contracts"
Cohesion: 0.50
Nodes (4): 4.1 Raw Wazuh alert (minimum), 4.2 Normalized alert, 4.3 Classification result, 4. Data contracts

### Community 78 - "5. Classification policy"
Cohesion: 0.50
Nodes (4): 5.1 Curated rule profiles (explicit, not trained), 5.2 Context signals, 5.3 Wording policy, 5. Classification policy

## Knowledge Gaps
- **18 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `esc()` connect `esc` to `app.js`, `stats/view.js`, `imports/render.js`, `loadingRows`, `Code Style — Arbiter`, `normalize_tenants`, `mount`?**
  _High betweenness centrality (0.220) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `esc()` (e.g. with `Agent: code-reviewer` and `/review — Code review pass`) actually correct?**
  _`esc()` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Should `core.py` be split into smaller, more focused modules?**
  _Cohesion score 0.11379800853485064 - nodes in this community are weakly interconnected._
- **Why does `Agent: code-reviewer` connect `normalize_tenants` to `esc`?**
  _High betweenness centrality (0.198) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `json()` (e.g. with `mount()` and `loadSelected()`) actually correct?**
  _`json()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Should `ref_node_assert` be split into smaller, more focused modules?**
  _Cohesion score 0.09411764705882353 - nodes in this community are weakly interconnected._
- **Why does `Task 1: Establish precise shared multi-tenant scope and safe facet contract` connect `normalize_tenants` to `get`, `File Map and Interfaces`, `esc`?**
  _High betweenness centrality (0.166) - this node is a cross-community bridge._