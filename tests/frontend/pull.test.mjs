import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const root = new URL('../../', import.meta.url);
const read = path => readFileSync(new URL(path, root), 'utf8');

test('pull page is routed, titled, and linked from the sidebar', async () => {
  const {parseRoute} = await import('../../app/static/js/router.js');
  assert.equal(parseRoute('#/pull').page, 'pull');
  assert.equal(parseRoute('#/pull?preset=7d').params.get('preset'), '7d');

  const app = read('app/static/js/app.js');
  assert.match(app, /pull:'Ambil Alert'/);

  const html = read('app/index.html');
  assert.match(html, /data-page="pull" href="#\/pull"/);
});

test('pull page runs a background job with real progress and cancellation', () => {
  const view = read('app/static/js/features/pull/view.js');
  assert.match(view, /\/api\/alerts\/pull/);
  assert.match(view, /method: 'POST'/);
  assert.match(view, /\/cancel/);
  assert.match(view, /progress-track/);
  assert.match(view, /progress-fill/);
  assert.match(view, /aria-valuenow/);
  assert.match(view, /job\.percent/);
  assert.match(view, /job\.fetched/);
  assert.match(view, /job\.inserted/);
  assert.match(view, /job\.deduplicated/);
  assert.match(view, /windows_done/);
  assert.match(view, /chunk_days/);
  assert.match(view, /all_time/);
  assert.match(view, /#\/realtime/);
  assert.match(view, /localStorage/);
  assert.match(view, /\/api\/alerts\/pull'/, 'resume falls back to the server-side job list');
  assert.match(view, /job\.rate/);
  assert.match(view, /job\.eta_seconds/);
  assert.doesNotMatch(view, /fetch\(/, 'pull page must use the shared API client');
});

test('shell shows a running pull indicator that survives page changes', () => {
  const html = read('app/index.html');
  assert.match(html, /id="pull-activity"/);
  const app = read('app/static/js/app.js');
  assert.match(app, /checkPullActivity/);
  assert.match(app, /\/api\/alerts\/pull/);
  assert.match(app, /pull-activity-label/);
  assert.match(app, /checkPullActivity\(\);\s*setInterval/);
});

test('exclusion dialog offers a field picker from Triage and Statistics', () => {
  const dialog = read('app/static/js/ui/exclusion-dialog.js');
  assert.match(dialog, /EXCLUSION_FIELD_OPTIONS/);
  assert.match(dialog, /EXCLUSION_MATCH_OPTIONS/);
  assert.match(dialog, /name="field"/);
  assert.match(dialog, /name="match"/);
  assert.match(dialog, /name="pattern"/);
  assert.match(dialog, /\/api\/settings\/exclusions/);
  assert.match(dialog, /Restart layanan Arbiter/);

  const statsView = read('app/static/js/features/stats/view.js');
  assert.match(statsView, /openExclusionDialog/);
  assert.match(statsView, /secondar/i);
  assert.doesNotMatch(statsView, /confirm\(/, 'exclusions must use the dialog, not a confirm prompt');

  const statsRender = read('app/static/js/features/stats/render.js');
  assert.match(statsRender, /data-global-exclude-key/);
  assert.match(statsRender, /Exclude…/);
  assert.doesNotMatch(statsRender, />Sembunyikan</);

  const charts = read('app/static/js/ui/charts.js');
  assert.match(charts, /data-secondary-exclude-key/);

  const triage = read('app/static/js/features/triage/view.js');
  assert.match(triage, /data-action="exclude-data"/);
  assert.match(triage, /exclusionValuesFor/);
  assert.match(triage, /source_ip/);
  assert.match(triage, /rule_description/);
  assert.doesNotMatch(triage, /exclude-url/);
});

test('exclusion model exposes URL, source IP, agent, and other fields', async () => {
  const {EXCLUSION_FIELD_OPTIONS, EXCLUSION_MATCH_OPTIONS, exclusionFieldLabel} =
    await import('../../app/static/js/features/settings/model.js');
  const fields = EXCLUSION_FIELD_OPTIONS.map(([key]) => key);
  for (const expected of ['url', 'source_ip', 'agent', 'rule_id', 'rule_description', 'referer', 'user_agent', 'location', 'tenant', 'syscheck_path', 'any']) {
    assert.ok(fields.includes(expected), `missing exclusion field ${expected}`);
  }
  assert.equal(exclusionFieldLabel('url'), 'URL / Path');
  assert.deepEqual(EXCLUSION_MATCH_OPTIONS.map(([key]) => key), ['glob', 'contains', 'exact', 'regex']);
});
