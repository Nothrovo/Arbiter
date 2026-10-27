# Alert Statistics & Pivot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `subagent-driven-development` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a scoped, SVG-only statistics workbench at `#/stats`, a filter-consistent compact Triage summary strip, and the approved precise multi-tenant scope contract across Triage, Stats, navigation, and exports.

**Architecture:** The backend will make `app/query.py` the single canonical filter/scope builder for queue, summary, aggregation, drill-down, suggestions, and exports. `GET /api/stats` will use server-side SQL CTEs and a closed whitelist of pivot expressions; `GET /api/triage/summary` will aggregate from the same scoped relation. The frontend will serialize a tenant scope as repeated `tenant` parameters, coordinate route state with a Stats session version guard, and render accessible charts with a local reusable SVG helper—no runtime dependencies.

**Tech Stack:** Python 3.11+ / FastAPI / psycopg / PostgreSQL 16; Vanilla ES modules; native CSS with existing `tokens.css`; Node built-in test runner; isolated SQLite synthetic API harness only.

**Spec:** User-provided brief in `.hermes/composer-pastes/pasted_content_2026-10-27_01-59-40-268_3352d2.txt`.

## Global Constraints

- Keep FastAPI + psycopg + vanilla JS ES modules + native CSS. Do not add React, Vue, Angular, Svelte, Tailwind, package dependencies, CDN assets, analytics, or external fetches.
- Never read `.env`, production database, real alerts/logs, or the live application on port 8000. Use `tests.test_ui_api` / `tests.serve_synthetic_ui` fixtures only.
- Never run `tests.test_api`; it targets the active PostgreSQL database.
- Use IBM Plex and the existing Quiet Evidence Desk tokens/components. UI copy is Indonesian. Do not create an overview dashboard.
- Never label a security state `Clean`, `Aman`, or `Safe`; retain approved intelligence wording.
- Canonical multi-tenant scope is repeated `tenant` URL parameters (`tenant=Alpha&tenant=Beta`), sorted and de-duplicated. `tenant=all` is valid only by itself. No comma-separated tenant list and no silent broadening to `all`.
- Read endpoints, triage, Stats, suggestions, and exports accept the canonical tenant set. Selection and mutations retain that exact tenant-set key; membership validation rejects alert IDs outside it. A scope change clears an existing selection only after the existing confirmation flow.
- SQL identifiers for pivots and drill-down dimensions must come only from backend constant maps. Values remain bound parameters. Never interpolate user-controlled SQL identifiers, regexes, or column names.
- The custom pattern pivot is literal, case-insensitive text only (1–120 characters), with `Cocok pola` / `Tidak cocok pola` buckets. Do not introduce user-provided regex evaluation or database regex execution.
- Query output must remain bounded: `top_n` defaults to 8, is validated to `1..50`; category/details limits are bounded; `Lainnya` is calculated server-side.
- Use a pre-flight gate before each task (plan, synthetic test harness, and clean target scope available). Use a revision gate after implementation (spec review, then quality review; maximum three decreasing-issue cycles). Escalate ambiguities to the user; abort and checkpoint on a privacy breach or unavailable safe test boundary.
- After every source-code stage run `graphify update .`; include resulting `graphify-out/` updates in that stage commit. Do not treat the rewrite as churn.

## Review Focus

1. **Mixed scope query:** duplicate, blank, and `all`+named tenant combinations must normalize deterministically or fail with 422; no endpoint may quietly broaden them.
2. **Tenant isolation:** a selected ID, alert detail, batch mutation, incident membership update, suggestion, and export must never see a tenant outside the same canonical tenant set.
3. **Aggregation integrity:** deduplicated alert count means `COUNT(*)`; raw event count means `SUM(hit_count)`; top-N plus `Lainnya` exactly covers the filtered scope, including null/missing dimension values represented as `Tidak tersedia`.
4. **SQL injection / cardinality:** an unknown pivot/filter key, malformed time range, oversize `top_n`, or pattern outside the literal-text policy must fail before a database query; high-cardinality dimensions cannot return unbounded rows.
5. **Async/a11y UI:** stale Stats responses cannot overwrite newer filters; keyboard users can activate chart marks and legend entries, receive text/number labels and SVG pattern distinctions, and see loading/error/empty states without relying on color.

## File Map and Interfaces

| File | Responsibility |
|---|---|
| `app/query.py` | Canonical tenant-set parsing, shared alert predicate, structured facet/drill-down predicate, and closed pivot definitions. |
| `app/main.py` | Read/mutation scope plumbing, `/api/stats`, `/api/triage/summary`, and stats-safe serialization. |
| `app/database.py`, `init-db.sql` | Matched idempotent indexes for scoped time queries and common low-cardinality pivots. |
| `app/static/js/state/scope.js` | URL normalization/serialization for repeated tenants, drill-down filters, and export-safe scope parameters. |
| `app/static/js/state/navigation.js`, `app/static/js/app.js`, `app/index.html` | Persistent multi-tenant workspace chooser, exact route restoration, six-destination routing/sidebar/title wiring. |
| `app/static/js/state/selection.js` | Canonical tenant-set scope key for selection containment. |
| `app/static/js/state/stats.js` | Versioned, abortable Stats request session. |
| `app/static/js/ui/charts.js` | Dependency-free accessible SVG line/bar/donut rendering and SVG export helpers. |
| `app/static/js/features/stats/{model,render,view}.js` | Stats normalization, workbench markup, data loading, chips, drill-down, charts/tables, and actions. |
| `app/static/js/features/triage/{model,view}.js` | Summary strip rendering/loading and exact-scope handoff to Stats. |
| `app/static/styles/components.css` | Compact summary strip and responsive Stats workbench/chart styles reusing tokens. |
| `tests/test_stats.py` | Isolated synthetic contract tests for aggregation and summary endpoints. |
| `tests/test_ui_api.py` | Existing synthetic SQLite harness and cross-tenant API integration coverage. |
| `tests/frontend/{scope,selection,navigation-state,router,shell,stats,charts,triage-summary}.test.mjs` | Scope, routing, session, rendering, drill-down, percentage, and summary behavior. |
| `AGENTS.md` | Correct route inventory and safe test command. |

### Task 1: Establish precise shared multi-tenant scope and safe facet contract

**Files:**
- Modify: `app/query.py`
- Modify: `app/main.py:138-584` (all shared read/export/suggestion/membership scopes)
- Modify: `app/static/js/api/client.js`
- Modify: `app/static/js/state/scope.js`
- Modify: `app/static/js/state/selection.js`
- Modify: `app/static/js/state/navigation.js`
- Modify: `app/static/js/app.js`, `app/index.html`
- Modify: `app/static/js/features/{triage,incidents,reports}/**/*.js` only at existing `tenant` URL/API call sites
- Modify: `tests/test_ui_api.py`, `tests/frontend/scope.test.mjs`, `tests/frontend/selection.test.mjs`, `tests/frontend/navigation-state.test.mjs`, `tests/frontend/client.test.mjs`

**Interfaces:**
- Produces `normalize_tenants(values) -> tuple[str, ...]` plus a canonical `tenant_clause(alias, values)` in `app/query.py`; named values become `a.tenant = ANY(%s)`, while sole `all` produces no predicate.
- Extends `alert_where(..., tenant: str | Sequence[str] | None, facet: str = '', facet_value: str = '') -> tuple[str, list[Any]]`; `facet` uses only a closed exact-match whitelist derived from pivot definitions.
- Produces `tenantScope(params) -> {all, tenants, key, label}` and repeated-param-aware `scopeParams(query, options)` in `state/scope.js`; `queryFrom()` exposes the canonical tenant set and never collapses it to `all`.
- `apiURL()` accepts `URLSearchParams` or object arrays and serializes every array item as a repeated local query parameter.

- [ ] **Step 1: Write failing synthetic API and frontend tests for tenant-set behavior.**

Add assertions that `tenant=Alpha&tenant=Beta` lists and exports only Alpha/Beta, `tenant=all&tenant=Alpha` and blank tenants return 422 before SQL execution, a scope change from `{Alpha,Beta}` to `{Alpha}` clears selection only with force, URL serialization preserves both entries, and navigation memory restores a Stats/Triage scope without inspector state leakage.

- [ ] **Step 2: Run the focused RED tests.**

Run: `.venv/bin/python -m unittest tests.test_ui_api -q` and `node --test tests/frontend/{scope,selection,navigation-state,client}.test.mjs`.

Expected: failures identify missing canonical multi-tenant support; no production database connection is attempted.

- [ ] **Step 3: Implement the minimal shared-scope contract.**

Add `normalize_tenants()` validation (strip, dedupe, deterministic sort; `all` exclusive); use its bound `ANY(%s)` clause in `alert_where()`, `_scoped_groups()`, `_validate_membership()`, alert detail, enrichment-by-ID, suggestions, and export scope. Preserve a single `tenant` URL parameter for legacy links; all writer/readers must accept the repeated canonical form.

Replace the single-value workspace control with a compact token/checklist dialog in the existing utility bar: `Semua tenant` is exclusive, selected named tenants remain visible as `N tenant`, and Apply rewrites the current route via `scopeParams()` without dropping its non-scope settings. Continue to use the current change-confirmation path when selection exists. Update navigation memory to remember both Triage and Stats complete URLs by canonical tenant-set key. Do not keep raw telemetry in localStorage.

- [ ] **Step 4: Run focused GREEN tests and inspect changed regions.**

Run: `.venv/bin/python -m unittest tests.test_ui_api -q` and `node --test tests/frontend/{scope,selection,navigation-state,client}.test.mjs`.

Expected: PASS; tests prove repeated tenants are exact and mutation membership cannot escape the active tenant set.

- [ ] **Step 5: Run safe regression suites and graph update.**

Run: `node --test tests/frontend/*.test.mjs`; `.venv/bin/python -m unittest tests.test_parser tests.test_exports tests.test_privacy tests.test_dedup tests.test_ui_api tests.test_ui_safety -q`; `graphify update .`.

Expected: all existing safe tests pass and the graph refresh completes.

- [ ] **Step 6: Commit stage-local work.**

```bash
git add app/query.py app/main.py app/static/js app/index.html tests/test_ui_api.py tests/frontend graphify-out
git commit -m "feat: add exact multi-tenant query scope"
```

### Task 2: Build SQL aggregation endpoints and schema support

**Files:**
- Modify: `app/query.py`
- Modify: `app/main.py`
- Modify: `app/database.py`, `init-db.sql`
- Create: `tests/test_stats.py`
- Modify: `tests/test_ui_api.py`

**Interfaces:**
- Produces `PIVOT_DEFINITIONS`: immutable keys `rule_description`, `rule_id`, `severity`, `source_ip`, `agent`, `referer`, `http_status`, `url_path`, `user_agent`, `pattern`, and `tenant`; each maps to a known SQL expression and Indonesian label. HTTP/referer/path/user-agent source from `parsed_details`; no schema column is invented.
- `GET /api/stats` accepts canonical shared filters plus `pivot_by`, `metric=alerts|events`, `chart=line|bar|donut`, `top_n=8`, `bucket=auto|minute|hour|day`, `facet`, `facet_value`, `pattern`, `secondary_pivot` (added only in Task 5), `other_details`, and bounded pagination. It returns filter echo, `total`, top rows, server-calculated `other`, distribution rows with exact counts/share, bucketed series, and optional bounded `other_details`.
- `GET /api/triage/summary` accepts the same core scope/filter/facet arguments and returns `{alerts, events, unique_source_ips, unique_agents, severity, incident_cases, time_range, top_rule}` calculated from the same scoped alerts CTE.

- [ ] **Step 1: Write failing `tests/test_stats.py` contract tests.**

Use `load_isolated_api()` and `SyntheticDB`; add authored synthetic records spanning tenants, levels, rule descriptions, source IPs, parsed HTTP fields, hit counts, and timestamps. Assert: unknown pivot/metric/bucket/facet, invalid date ordering, invalid literal pattern, and `top_n > 50` return clear 422 responses before SQL; tenant sets remain exact; `alerts` is deduplicated rows while `events` sums `hit_count`; top-N plus `Lainnya` equals filtered total; distribution shares sum to one before presentation rounding; `other_details` is bounded; and summary totals equal the matching `/api/alerts` total plus hit-count sum.

- [ ] **Step 2: Run the new tests to verify RED.**

Run: `.venv/bin/python -m unittest tests.test_stats -q`.

Expected: FAIL because endpoints and pivot validation do not yet exist.

- [ ] **Step 3: Implement server-side aggregate SQL and indexes.**

Build all aggregates from `WITH scoped AS (SELECT a.* FROM wazuh.alerts a {alert_where(...)})`. Use SQL `GROUP BY`, `COUNT(*)`, `SUM(COALESCE(hit_count, 1))`, `COUNT(DISTINCT NULLIF(...,''))`, and deterministic `ORDER BY count DESC, label ASC`; do not materialize source alert rows in Python. Build dimension expressions only from `PIVOT_DEFINITIONS`; coalesce missing values to `Tidak tersedia`. Use `substr(timestamp, 1, N)` for portable minute/hour/day grouping of normalized ISO text, choose `minute` for <=24h, `hour` for <=7d, otherwise `day`, and bound top series.

Return an explicit server `other_count` and bounded server details after top-N, rather than asking the browser to infer the remainder. For literal `pattern`, bind a `%value%` comparison over the same searchable fields as `alert_where`; return only named match/non-match buckets. Implement summary from the same `scoped` CTE and query incident cases through membership only after filtering evidence.

Add idempotent matching indexes to both schema definitions: `(tenant, timestamp)`, `rule_level`, `agent_name`, and the `parsed_details->>'status'` expression. Keep existing rule/source/timestamp indexes. Document in code why highly-cardinal user-agent, URL/path, referer, and arbitrary text/pattern dimensions intentionally have no broad btree index.

- [ ] **Step 4: Make the isolated SQLite adapter support only the new safe SQL dialect needed by these tests.**

Extend `SyntheticDB.execute()` narrowly for the known query constructs (for example SQL boolean/JSON extraction equivalents) rather than replacing aggregate outcomes with fixtures. Preserve execution recording so validation tests can prove no query ran.

- [ ] **Step 5: Run endpoint tests to verify GREEN.**

Run: `.venv/bin/python -m unittest tests.test_stats tests.test_ui_api -q`.

Expected: PASS; results come from synthetic SQLite executing translated parameterized SQL, not mock JSON.

- [ ] **Step 6: Run safe regression suites, update graph, and commit stage 1.**

Run: `node --test tests/frontend/*.test.mjs`; `.venv/bin/python -m unittest tests.test_parser tests.test_exports tests.test_privacy tests.test_dedup tests.test_ui_api tests.test_ui_safety tests.test_stats -q`; `graphify update .`.

```bash
git add app/query.py app/main.py app/database.py init-db.sql tests/test_stats.py tests/test_ui_api.py graphify-out
git commit -m "feat: add scoped alert statistics endpoints"
```

### Task 3: Add the `#/stats` pivot workbench and reusable SVG charts

**Files:**
- Modify: `app/static/js/router.js`, `app/static/js/app.js`, `app/index.html`
- Create: `app/static/js/state/stats.js`
- Create: `app/static/js/ui/charts.js`
- Create: `app/static/js/features/stats/model.js`
- Create: `app/static/js/features/stats/render.js`
- Create: `app/static/js/features/stats/view.js`
- Modify: `app/static/styles/components.css`
- Create: `tests/frontend/stats.test.mjs`, `tests/frontend/charts.test.mjs`
- Modify: `tests/frontend/router.test.mjs`, `tests/frontend/shell.test.mjs`

**Interfaces:**
- `parseRoute()` recognizes `stats`; page title/navigation includes `Statistik`; `createNavigationMemory()` restores full `#/stats` configuration by scope key.
- `createStatsSession()` exposes `nextRequest()`, `isCurrent(version)`, and `dispose()` for abortable stale-response rejection.
- `normalizeStatsQuery(params)` returns validated URL configuration (`pivot_by`, `metric`, `chart`, time preset/custom bounds, top-N, facet chip, literal pattern, and canonical tenant scope); `distributionPercentages(rows)` assigns presentation percentages with the final slice absorbing rounding remainder so visible output totals exactly 100%.
- `renderBarChart`, `renderDonutChart`, and `renderLineChart` return SVG markup with semantic labels and `data-chart-value` hooks; no remote chart library is loaded.

- [ ] **Step 1: Write failing frontend tests.**

Cover: `#/stats` routing/sidebar/title; URL round-trip of a multi-tenant Stats configuration; top-N default/max normalization; 100% display rounding including `Lainnya`; chart SVG includes `<title>`, `<desc>`, text count/percent labels, non-color SVG patterns, and keyboard-focusable marks; a slice/bar/legend activates a facet chip; removing a chip restores the prior scope; a stale response cannot replace a newer request; and `Buka di Triage` preserves the exact repeated tenant/filter/facet parameters.

- [ ] **Step 2: Run focused RED tests.**

Run: `node --test tests/frontend/{router,shell,stats,charts}.test.mjs`.

Expected: FAIL because Stats modules/route/chart helpers are absent.

- [ ] **Step 3: Implement the workbench with existing patterns.**

Add the sidebar entry between Triage and Insiden and set `pageTitles.stats = 'Statistik'`. Implement a dense workbench, not a dashboard: a page header, scope/filter panel, pivot selector containing exactly the backend-supported labels, metric/chart/table toggles, `top_n`, time presets/custom range, literal-pattern input only when chosen, applied drill-down chips, and a `Buka di Triage` action. Keep all configuration in the hash; update through `withParams()` and `scopeParams()`.

Use `apiURL('/api/stats', scopeParams(statsQuery))`, an abort controller, and `createStatsSession` monotonic version before rendering any response. Use `emptyState()` and `loadingRows()` for empty/pending; use `errorState()` for failure. Render donut/bar/line using local `charts.js`; add text legend buttons and keyboard handlers so every visual selection has accessible non-color labels. Clicking `Lainnya` requests only bounded `other_details` and shows a labelled detail table, not an unbounded popup. The table view renders the same response with count/share columns and retains drill-down behavior.

Append compact, token-only component styles with a one-column mobile flow, local table scrolling only, 44px interactive targets below 768px, and no novel palette.

- [ ] **Step 4: Run focused GREEN tests.**

Run: `node --test tests/frontend/{router,shell,stats,charts}.test.mjs`.

Expected: PASS; tests show no dependency/CDN was introduced and exact scope handoff works.

- [ ] **Step 5: Perform synthetic browser QA.**

Run `.venv/bin/python -m tests.serve_synthetic_ui` on `127.0.0.1:8767`, open only that origin, verify `X-Arbiter-Data: synthetic-only`, then inspect `#/stats` at desktop and narrow width. Exercise pivot, top-N/Lainnya, line/bar/donut/table, keyboard drill-down/removal, and `Buka di Triage`; stop the synthetic server when done.

- [ ] **Step 6: Run regression suites, update graph, and commit stage 2.**

Run: `node --test tests/frontend/*.test.mjs`; `.venv/bin/python -m unittest tests.test_parser tests.test_exports tests.test_privacy tests.test_dedup tests.test_ui_api tests.test_ui_safety tests.test_stats -q`; `graphify update .`.

```bash
git add app/index.html app/static/js app/static/styles/components.css tests/frontend graphify-out
git commit -m "feat: add alert statistics pivot workbench"
```

### Task 4: Add the compact Triage filter-summary strip

**Files:**
- Modify: `app/static/js/features/triage/model.js`
- Modify: `app/static/js/features/triage/view.js`
- Modify: `app/static/styles/components.css`
- Create: `tests/frontend/triage-summary.test.mjs`
- Modify: `tests/test_stats.py`

**Interfaces:**
- `summaryRequestParams(query)` returns the same normalized filter/facet/time/tenant scope used for `/api/alerts`, excluding paging/sort-only controls.
- `renderTriageSummary(summary, query)` renders a collapsible compact strip with count actions mapped to a precise shared filter or an exact Stats handoff.

- [ ] **Step 1: Write failing endpoint and frontend tests.**

Add summary assertions that the values exactly match filtered synthetic queue count/event hit sum, unique IP/agent counts, severity mini-bar, distinct related cases, time bounds, and deterministic top rule. Add UI tests that pending/stale summary responses are ignored, summary is collapsible, severity and top-rule actions add validated facet chips to Triage, related-case action sets grouped status, source/agent counts route to matching Stats pivots without losing scope, and `Lihat statistik lengkap` carries the exact current filter set.

- [ ] **Step 2: Run focused RED tests.**

Run: `.venv/bin/python -m unittest tests.test_stats -q` and `node --test tests/frontend/triage-summary.test.mjs`.

Expected: FAIL because summary UI/model behavior is missing.

- [ ] **Step 3: Implement the thin summary strip.**

Place it after current applied filters and before the queue workspace so it does not shift the header/tabs. Load `/api/triage/summary` alongside queue data using the same query/filter scope and its own abort/version guard. Render deduplicated alert count, raw-event sum, unique source IPs, unique hosts, accessible severity mini-bars with textual counts, related incident cases, time range, and top rule; all values must derive from server response, never page-only items.

Map actions precisely: severity/top rule add a backend-whitelisted facet chip; grouped cases set `status=grouped`; unique source/agent actions open Stats with the appropriate pivot and exact scope; total/events apply only their documented sort/action without widening scope. Add an explicit `Lihat statistik lengkap` link. Persist the collapsed state only in the current URL (`summary=collapsed`), not localStorage.

- [ ] **Step 4: Run focused GREEN tests.**

Run: `.venv/bin/python -m unittest tests.test_stats -q` and `node --test tests/frontend/triage-summary.test.mjs`.

Expected: PASS; summary counts agree with the same filtered synthetic queue.

- [ ] **Step 5: Synthetic browser QA and commit stage 3.**

Repeat synthetic-only desktop/narrow QA for Triage; verify strip collapse, actions, filter chips, and Stats handoff. Then run all safe suites and `graphify update .`.

```bash
git add app/static/js/features/triage app/static/styles/components.css tests/test_stats.py tests/frontend/triage-summary.test.mjs graphify-out
git commit -m "feat: add filter-scoped triage summary strip"
```

### Task 5: Add approved post-core statistics enhancements

**Files:**
- Modify: `app/main.py`, `app/query.py`
- Modify: `app/static/js/features/stats/{model,render,view}.js`, `app/static/js/ui/charts.js`
- Modify: `app/static/styles/components.css`
- Modify: `tests/test_stats.py`, `tests/frontend/stats.test.mjs`, `tests/frontend/charts.test.mjs`

**Interfaces:**
- Adds optional `compare=previous` only for a finite valid time range; response includes explicit comparable prior-period counts and neutral signed deltas.
- Adds optional bounded `secondary_pivot` (same whitelist excluding `pattern`) for SQL grouped stacked-bar data.
- Adds server-computed neutral `above_average` time bucket marker; copy must say `Di atas rata-rata`, never make an attack claim.
- Adds local aggregate-only CSV/SVG/PNG exports and copyable textual summary; no telemetry is uploaded.
- Stores only named Stats configuration presets in `localStorage` under a versioned tenant-scope key; never store results, alert rows, raw logs, or identifiers beyond user-entered filter configuration.

- [ ] **Step 1: Write failing tests for each enhancement.**

Test previous-period bounds and zero-denominator delta label, secondary-pivot whitelist/series bounds, neutral spike labeling, local SVG/PNG serialization, CSV column counts, copy summary scope text, configuration-only preset storage, and a detail table that uses `/api/alerts?summary=true` with the exact active drill-down scope and creates inspector links without raw evidence.

- [ ] **Step 2: Run RED tests.**

Run: `.venv/bin/python -m unittest tests.test_stats -q` and `node --test tests/frontend/{stats,charts}.test.mjs`.

Expected: FAIL for each new capability before its minimal implementation.

- [ ] **Step 3: Implement bounded enhancements.**

Use SQL CTE/window calculations for prior-period totals, secondary distribution, and average bucket comparisons. Keep `secondary_pivot` series bounded to top-N and fold surplus into `Lainnya`. Serialize already-rendered local SVG for SVG download; draw that same local SVG to an in-memory canvas for PNG; build CSV only from aggregate response rows. Require a finite range before comparison. Detail table calls the existing summary projection endpoint and routes each row to `#/triage` with the same scope plus `alert=<id>`.

- [ ] **Step 4: Run GREEN tests, safe suites, synthetic QA, graph update, and commit stage 4.**

Run: `node --test tests/frontend/*.test.mjs`; `.venv/bin/python -m unittest tests.test_parser tests.test_exports tests.test_privacy tests.test_dedup tests.test_ui_api tests.test_ui_safety tests.test_stats -q`; synthetic-only QA at 8767; `graphify update .`.

```bash
git add app/query.py app/main.py app/static/js app/static/styles/components.css tests/test_stats.py tests/frontend graphify-out
git commit -m "feat: extend statistics analysis tools"
```

### Task 6: Document the completed navigation and verification contract

**Files:**
- Modify: `AGENTS.md`
- Modify: `tests/frontend/shell.test.mjs`

- [ ] **Step 1: Write the failing shell/documentation contract test.**

Assert the application exposes six real destinations including `stats` and `database`, does not load CDN resources, and retains Triage as the default—not an overview dashboard.

- [ ] **Step 2: Update documentation and make the test pass.**

Change `Four destinations` to `Six destinations`, list `#/stats` as a pivot-analysis workbench and `#/database` as workspace database management, and explicitly retain the no-overview policy. Update the safe backend command to include `tests.test_stats`; state that browser QA stays on synthetic port 8767.

- [ ] **Step 3: Final verification and repository audit.**

Run:

```bash
node --test tests/frontend/*.test.mjs
.venv/bin/python -m unittest tests.test_parser tests.test_exports tests.test_privacy tests.test_dedup tests.test_ui_api tests.test_ui_safety tests.test_stats -q
npx -y @google/design.md@0.4.0 lint docs/ui-ux-redesign/DESIGN.md
graphify update .
git status --short
git log --oneline -4
```

Expected: all safe tests/lint pass; only intended working-tree changes remain; all four feature-stage commits are present.

- [ ] **Step 4: Dispatch final integration review.**

A fresh reviewer checks exact tenant-set preservation from Stats → Triage → export, SQL whitelist and bounds, no production-data access, chart accessibility, compact responsive layout, test adequacy, and commit/graph completeness. Any critical/important issue returns through the revision gate before completion.

## Self-Review

- **Spec coverage:** Tasks 1–2 cover exact shared filtering, APIs, validation, SQL grouping, indexes, top-N/Lainnya, all requested pivot fields, and summary parity. Task 3 covers new route/sidebar/hash/state/SVG/accessibility/drill-down/table. Task 4 covers every requested compact Triage metric and handoff. Task 5 covers all six post-core additions. Task 6 corrects AGENTS.md to the actual six routes and verifies safe delivery.
- **Explicit decisions:** Parser-backed `parsed_details` supports referer, HTTP status, URL path, and user agent; no nonexistent columns are added. Literal matching replaces optional user regex to prevent runaway query behavior. Repeated tenant parameters preserve multi-select scope exactly.
- **Known boundary:** Existing incident/case grouping has no stored tenant owner. The plan validates every selected/mutated evidence ID against the active tenant set and preserves the established selection reset rules; it does not claim tenant authorization.
- **Revision behavior:** Each implementation task must show RED before production edits, GREEN after, then pass specification review before quality review. Three non-converging review cycles require user escalation rather than silent scope reduction.
