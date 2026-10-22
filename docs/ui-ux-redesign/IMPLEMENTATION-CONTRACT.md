# Approved implementation contract — Arbiter

User approved Quiet Evidence Desk and total implementation. Privacy reaffirmed: **never read actual alerts, database records, .env, real logs, or populated live UI**. Use source and synthetic fixtures only. Do not run original DB integration suite against live SGU. Do not commit/stage/reset user work.

## Direction contract

**THESIS:** Task-based investigation desk; reject single-page accumulation and marketing dashboards.
**OWN-WORLD:** Neutral dark 111/181818/242424, primary F5F5F5, secondary B8B8B8. Severity/status hues only. IBM Plex Sans 14px UI, 24px headings; Mono only code/IDs. Native CSS/ES modules.
**STORY:** Return to triage, inspect evidence without losing context, group evidence into incidents, write analysis, export explicit scope.
**FIRST VIEWPORT:** 208px labelled sidebar; 48px utility bar with one tenant switcher and honest status. Compact page header/views/toolbar; first row before 240px at 1440x900. Inspector closed until requested, contextual on wide desktop and single detail region on narrow screens.
**FORM:** User-approved Quiet Evidence Desk, code-led. seed: none (user-pinned direction; no random roll).
**FINISH:** unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance.

## Integration boundary

- Parent owns `app/index.html`, `app/static/styles/*`, `app/static/js/app.js`, `router.js`, `api/client.js`, `state/*`, `ui/*`, `features/triage/*`, global tests/harness/docs/fonts.
- Backend child owns `app/main.py`, additive `app/query.py` or scoped helper, backend tests (not original test_api.py), static mount. No schemas or live DB.
- Incident child owns `app/static/js/features/incidents/*` and `tests/frontend/incidents*.test.mjs` only.
- Import/report child owns `app/static/js/features/imports/*`, `features/reports/*` and respective frontend tests only.

Each feature `view.js` exports `mount(ctx)` (sync/async) returning optional cleanup function. Context:
```
{ root: HTMLElement,
  route: {path: '/triage'|'/incidents'|'/incidents/<uuid>'|'/imports'|'/reports', params: URLSearchParams},
  navigate: (hashOrPath: string, options?: {replace?:boolean}) => void,
  selection: {ids:()=>number[], size:()=>number, clear:()=>void, toggle:(id:number, checked:boolean)=>void},
  notify: (message:string, kind?:'success'|'error'|'info')=>void,
  signal: AbortSignal,
  setGuard: (fn:(()=>boolean)|null)=>void
}
```
Mount must clear guard on cleanup. Parent aborts signal before route replacement. Parent top Refresh dispatches `arbiter:refresh` on feature root; feature attaches with signal. Dirty drafts guard navigation and beforeunload. Query values in URL, no raw records/narratives persisted. Modules use static imports `.js` and escaped templates; no inline handlers.

Shared utilities provided by parent:
```
import {request, json, apiURL, download, copyText, copyHTML} from '../../api/client.js';
// request(path, options) -> Response, throws ApiError on !ok; timeout + passed signal.
// json(path, options) -> parsed JSON; apiURL('/api/alerts', params) builds pathname+query.
// download(url, filename?) fetches via request then browser download Blob (errors visible).
// copyText(text), copyHTML(html) await clipboard, reject on denial.
import {esc, icon, severity, statusLabel, formatTime, emptyState, errorState, loadingRows} from '../../ui/primitives.js';
// esc(value) -> HTML escaped string. icon(name) -> bounded inline SVG (16x16).
// severity(value) -> human-readable badge HTML; numeric Wazuh levels or low/medium/high/critical.
// statusLabel(value) -> humanized string; formatTime(value) -> humanized timestamp string.
// emptyState(title, description, actionHTML='') / errorState(message) / loadingRows(count=5) -> HTML.
import {queryFrom, scopeParams, scopeDescription} from '../../state/scope.js';
// queryFrom(URLSearchParams) -> {tenant,q,review_status,filter_preset,status,group_id,sort_by,sort,limit,offset} normalized
// scopeParams(query,{ids?,groupId?}={}) -> URLSearchParams; IDs explicitly override q/review/preset/group but preserve tenant; no pagination.
// scopeDescription(params) -> human-readable scope description.
```
Feature relative imports from `features/<feature>/view.js` to shared utils are `../../...`.

CSS shared classes: `.page-header`, `.page-heading`, `.page-description`, `.page-actions`, `.button`, `.button.primary`, `.button.danger`, `.button.icon-button`, `.toolbar`, `.field`, `.input`, `.select`, `.textarea`, `.panel`, `.section-heading`, `.muted`, `.meta`, `.mono`, `.badge`, `.badge.high/.critical/.medium/.low/.neutral/.success`, `.data-table`, `.table-region`, `.empty-state`, `.error-region`, `.inline-status`, `.tabs`, `.tab`, `.form-grid`, `.form-section`, `.editor-layout`, `.context-panel`, `.timeline`, `.evidence-row`, `.detail-grid`, `.key-value`, `.danger-zone`, `.stack`, `.split`, `.report-layout`, `.report-preview`, `.import-layout`, `.segmented`, `.metric-strip`, `.format-menu`. No raw inline colors/fonts. Parent styles responsive globally and can extend for feature-specific semantic classes.

Backend target contracts (child must report any deviation immediately):
- Existing API routes retained. GET `/api/alerts` same filters+total, optional `summary=true` omits raw/data/duplicate payload; limit+offset stable ordering.
- GET `/api/alerts/<id>?tenant=...` returns detail object; not found/out of scope 404.
- GET `/api/groups?tenant=...` returns group list with id/title/category/severity/status/alert_count/alert_pks/tenants.
- GET `/api/groups/<id>?tenant=...` returns group object with same metadata, analysis/conclusion/recommendation. Group evidence via `/api/alerts?group_id=...&tenant=...`.
- Existing group CRUD/membership routes preserved. Do not invent DB columns.
- Suggestions accepts tenant and triage filters, returns same {mode,warning,suggestions}; no global scope surprise.
- GET `/api/export/preview` accepts tenant,q,review_status,filter_preset,status,group_id OR alert_ids; returns `{count,meta,scope,html,truncated:false}`. All actual export endpoints accept identical scope. Explicit upper bound returns 413 instead of truncating. CSV retained.
- All existing import endpoints and response unchanged: parsed/inserted/deduplicated/warnings.
- `/api/health` only safe status aggregates, no real client testing by agents.

No permission/auth policy invented: tenant filtering is context, not authorization. Case can be inspected in all-tenant mode explicitly; scoped evidence retains tenant. Creating from selected alert IDs keeps tenant in URL/context. Backend must reject explicitly scoped membership if IDs outside tenant, rather than silently broaden it.
