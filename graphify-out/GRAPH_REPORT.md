# Graph Report - Arbiter  (2026-10-22)

## Corpus Check
- 78 files · ~52,246 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 11 file(s) not represented in the graph (top: .woff2 4, (none) 3, .css 3)

## Summary
- 579 nodes · 1266 edges · 30 communities (20 shown, 10 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 23 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `6e245446`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- parser.py
- main.py
- serve_synthetic_ui.py
- esc
- ref_node_assert
- sanitize_text
- ApiIntegrationTests
- init-db.sql
- start.sh
- Arbiter — blueprint rombak UI/UX
- DESIGN.md
- Arbiter
- UIAPIContractTests
- reports/view.js
- incidents-view.test.mjs
- imports/view.js
- ui-ux-redesign/README.md
- app.js
- SafetyTests
- SyntheticDB
- state.js
- Arbiter
- Arbiter — audit UI/UX dan keputusan redesign
- Arbiter UI/UX Redesign — Quiet Evidence Desk
- 8. Roadmap implementasi, tiap tahap bisa diverifikasi
- 4. Wireframe dan first viewport
- 5. Information architecture & interaction contracts

## God Nodes (most connected - your core abstractions)
1. `esc()` - 34 edges
2. `mount()` - 29 edges
3. `json()` - 26 edges
4. `mountWorkspace()` - 25 edges
5. `get_db()` - 23 edges
6. `UIAPIContractTests` - 23 edges
7. `mount()` - 22 edges
8. `errorState()` - 19 edges
9. `parse_log_line()` - 18 edges
10. `renderList()` - 17 edges

## Surprising Connections (you probably didn't know these)
- `Keputusan Arsitektur Kunci` --references--> `selectedIds()`  [INFERRED]
  docs/ui-ux-redesign/README.md → app/static/js/features/incidents/model.js
- `Keputusan Arsitektur Kunci` --references--> `scopeParams()`  [INFERRED]
  docs/ui-ux-redesign/README.md → app/static/js/state/scope.js
- `mount()` --indirect_call--> `json()`  [INFERRED]
  app/static/js/features/imports/view.js → app/static/js/api/client.js
- `SafetyTests` --uses--> `UIAPIContractTests`  [INFERRED]
  tests/test_ui_safety.py → tests/test_ui_api.py
- `_process_alerts_ingest()` --calls--> `normalize_alert()`  [EXTRACTED]
  app/main.py → app/core.py

## Import Cycles
- None detected.

## Communities (30 total, 10 thin omitted)

### Community 0 - "parser.py"
Cohesion: 0.09
Nodes (21): local_ai_suggest_groups(), LocalAIUnavailable, normalize_alert(), ollama_request(), suggest_groups(), suggestions_with_fallback(), as_dict(), build_log_signature() (+13 more)

### Community 1 - "main.py"
Cohesion: 0.05
Nodes (44): get_db(), get_db_connection(), ingest_alert_with_dedup(), init_database(), generate_docx_landscape_report(), generate_gdocs_html_report(), generate_markdown_report(), generate_tsv_table() (+36 more)

### Community 3 - "esc"
Cohesion: 0.12
Nodes (56): apiURL(), json(), closeNav(), notify(), render(), caseHref(), filterIncidents(), incidentRoute() (+48 more)

### Community 4 - "ref_node_assert"
Cohesion: 0.08
Nodes (19): choices(), integer(), queryFrom(), scopeParams(), url, modelURL, load(), url (+11 more)

### Community 7 - "init-db.sql"
Cohesion: 0.33
Nodes (10): idx_wazuh_alerts_reviewed, idx_wazuh_alerts_rule_id, idx_wazuh_alerts_sig, idx_wazuh_alerts_source_ip, idx_wazuh_alerts_tenant, idx_wazuh_alerts_timestamp, public.ip_intel_cache, wazuh.alert_group_members (+2 more)

### Community 11 - "Arbiter — blueprint rombak UI/UX"
Cohesion: 0.17
Nodes (12): 10. Open decisions sebelum build, 1. Keputusan desain, 2. Sitemap yang diusulkan, 3. Apa yang boleh muncul di depan, 6. Arsitektur module yang disarankan, 7. Kesiapan backend: pakai yang ada vs perlu kerja, 9. Acceptance checklist, Alternatif yang dibandingkan (+4 more)

### Community 12 - "DESIGN.md"
Cohesion: 0.14
Nodes (13): Colors, Components, Do's and Don'ts, Elevation & Depth, Global shell, Impor dan Laporan, Insiden, Layout (+5 more)

### Community 13 - "Arbiter"
Cohesion: 0.09
Nodes (21): 1. Resilient Multi-Format Ingestion, 2. High-Precision Log Dissector (No False Fields), 3. Signature-Based Deduplication & Expandable View, 4. Enterprise Multi-Tenant Architecture, 5. Review & Triage Status Workflow, 6. Local Threat Intelligence Auto-Enrichment, 7. Privacy-First Cloud AI Redactor, 8. Official One-Click Deliverables (5 Export Paths) (+13 more)

### Community 15 - "reports/view.js"
Cohesion: 0.20
Nodes (20): ApiError, copyHTML(), copyText(), download(), request(), caseReportRoute(), createReportSession(), exportURL() (+12 more)

### Community 16 - "incidents-view.test.mjs"
Cohesion: 0.25
Nodes (3): context(), load(), SyntheticRoot

### Community 17 - "imports/view.js"
Cohesion: 0.13
Nodes (9): createImportSession(), importPage(), importResult(), mount(), update(), moduleURL, click(), Control (+1 more)

### Community 18 - "ui-ux-redesign/README.md"
Cohesion: 0.29
Nodes (3): Approved implementation contract — Arbiter, Direction contract, Integration boundary

### Community 19 - "app.js"
Cohesion: 0.09
Nodes (18): health(), help, main, navigationMemory, pageTitles, router, scrim, scrollPositions (+10 more)

### Community 22 - "state.js"
Cohesion: 0.16
Nodes (17): cleanIds(), draftFrom(), draftsEqual(), evidenceParams(), incidentPayload(), selectedIds(), SEVERITIES, STATUSES (+9 more)

### Community 23 - "Arbiter"
Cohesion: 0.33
Nodes (5): Arbiter, Audience and usage, Development verification, Implemented case policy without schema changes, Product boundaries

### Community 24 - "Arbiter — audit UI/UX dan keputusan redesign"
Cohesion: 0.15
Nodes (13): Arbiter — audit UI/UX dan keputusan redesign, Bukti komposisi dan responsive, Detector Impeccable — hasil nyata, bukan daftar bug unik, Hallmark audit — subset yang sesuai operational app, Handoff, Metode dan batas bukti, Nielsen heuristics, Persona dan emotional journey (+5 more)

### Community 25 - "Arbiter UI/UX Redesign — Quiet Evidence Desk"
Cohesion: 0.18
Nodes (11): Arbiter UI/UX Redesign — Quiet Evidence Desk, Arsitektur yang Terpasang, Audit (sebelum), Batas dan Catatan, Deliverable Desain, Evidence, Implementasi (sesudah), Keputusan Arsitektur Kunci (+3 more)

### Community 27 - "8. Roadmap implementasi, tiap tahap bisa diverifikasi"
Cohesion: 0.29
Nodes (7): 8. Roadmap implementasi, tiap tahap bisa diverifikasi, Phase 0 — safety & baseline, Phase 1 — modular foundation + shell, Phase 2 — triage-first experience, Phase 3 — insiden workspace, Phase 4 — impor dan laporan, Phase 5 — hardening & rollout

### Community 28 - "4. Wireframe dan first viewport"
Cohesion: 0.33
Nodes (6): 4. Wireframe dan first viewport, A. Triage desktop, B. Insiden index dan case workspace, C. Impor, D. Laporan, E. Mobile

### Community 29 - "5. Information architecture & interaction contracts"
Cohesion: 0.40
Nodes (5): 5. Information architecture & interaction contracts, Accessibility, Editing dan destructive actions, Refresh, Scope

## Knowledge Gaps
- **10 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Arbiter UI/UX Redesign — Quiet Evidence Desk` connect `Arbiter UI/UX Redesign — Quiet Evidence Desk` to `ui-ux-redesign/README.md`?**
  _High betweenness centrality (0.102) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `json()` (e.g. with `mount()` and `mountWorkspace()`) actually correct?**
  _`json()` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Should `parser.py` be split into smaller, more focused modules?**
  _Cohesion score 0.08506493506493507 - nodes in this community are weakly interconnected._
- **Why does `Keputusan Arsitektur Kunci` connect `Arbiter UI/UX Redesign — Quiet Evidence Desk` to `ref_node_assert`, `state.js`?**
  _High betweenness centrality (0.099) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `mountWorkspace()` (e.g. with `json()` and `refresh()`) actually correct?**
  _`mountWorkspace()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Should `main.py` be split into smaller, more focused modules?**
  _Cohesion score 0.0506578947368421 - nodes in this community are weakly interconnected._
- **Why does `scopeParams()` connect `ref_node_assert` to `Arbiter UI/UX Redesign — Quiet Evidence Desk`, `esc`, `state.js`, `reports/view.js`?**
  _High betweenness centrality (0.093) - this node is a cross-community bridge._