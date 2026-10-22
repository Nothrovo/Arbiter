import test from 'node:test';
import assert from 'node:assert/strict';
const load = () => import('../../app/static/js/features/reports/model.js');

test('report URLs carry the identical explicit query scope for preview and every format without pagination', async () => {
  const {reportScope, exportURL} = await load();
  const scope = reportScope(new URLSearchParams('tenant=example&q=synthetic&review_status=reviewed&filter_preset=403&status=grouped&sort=asc&sort_by=hits&group_id=case-1&limit=25&offset=50'));
  assert.equal(scope.has('limit'), false); assert.equal(scope.has('offset'), false);
  assert.equal(scope.get('q'), 'synthetic'); assert.equal(scope.get('group_id'), 'case-1');
  for (const format of ['preview', 'report-html', 'docx', 'xlsx', 'tsv', 'markdown', 'csv']) {
    const url = new URL(exportURL(scope, format), 'http://synthetic.invalid');
    assert.deepEqual([...url.searchParams], [...scope]);
    assert.equal(url.pathname, format === 'csv' ? '/api/export.csv' : `/api/export/${format}`);
  }
  assert.throws(() => exportURL(scope, 'unknown'));
});

test('preview uses server count, rejects incomplete or truncated reports, and ignores superseded requests', async () => {
  const {createReportSession, reportScope} = await load();
  const scope = reportScope(new URLSearchParams('tenant=example&review_status=all'));
  const calls = [];
  const session = createReportSession({scope, getJSON: (url, options) => new Promise((resolve, reject) => calls.push({url, options, resolve, reject}))});
  const first = session.load();
  const second = session.load();
  assert.equal(calls[0].options.signal.aborted, true);
  calls[1].resolve({count: 702, meta: {title: 'Synthetic report'}, scope: Object.fromEntries(scope), html: '<p>Synthetic evidence</p>', truncated: false});
  await second;
  calls[0].resolve({count: 1, meta: {}, scope: {}, html: 'stale', truncated: false});
  await first;
  assert.equal(session.state.preview.count, 702);
  assert.equal(session.state.preview.html, '<p>Synthetic evidence</p>');
  assert.equal(session.state.loading, false);
  const third = session.load();
  calls[2].resolve({count: 500, meta: {}, scope: {}, html: 'partial', truncated: true});
  await third;
  assert.equal(session.state.preview, null);
  assert.match(session.state.error, /terpotong|lengkap/i);
  const fourth = session.load(); calls[3].reject(new Error('Synthetic scope too large (413)')); await fourth;
  assert.match(session.state.error, /413/);
  assert.equal(session.state.preview, null);
  assert.equal(calls[3].url, `/api/export/preview?${scope}`);
  session.dispose();
});

test('preview scope mismatch disables exporting rather than showing a broader report', async () => {
  const {createReportSession, reportScope} = await load();
  const scope = reportScope(new URLSearchParams('tenant=example&q=synthetic&review_status=reviewed'));
  const session = createReportSession({scope, getJSON: async () => ({count: 10, meta: {}, scope: {tenant: 'all', q: '', review_status: 'all'}, html: '<p>Wrong scope</p>', truncated: false})});
  assert.equal(await session.load(), false);
  assert.equal(session.state.preview, null);
  assert.match(session.state.error, /scope/i);
  session.dispose();
});

test('rich and text clipboard failures are awaited and retain the exact format scope in fallback', async () => {
  const {reportAction, reportScope} = await load();
  const scope = reportScope(new URLSearchParams('tenant=example&q=synthetic&review_status=reviewed'));
  const seen = [];
  let release;
  const deps = {
    scope, request: async url => {seen.push(url); return new Response('Synthetic exported text');},
    download: async url => {seen.push(url);},
    copyText: async text => {assert.equal(text, 'Synthetic exported text'); throw new Error('Clipboard denied');},
    copyHTML: html => {assert.equal(html, '<p>Synthetic</p>'); return new Promise((resolve, reject) => {release = reject;});},
    preview: {html: '<p>Synthetic</p>'},
  };
  let finished = false;
  const rich = reportAction('copy-html', deps).then(result => {finished = true; return result;});
  await Promise.resolve(); assert.equal(finished, false);
  release(new Error('Clipboard denied'));
  const failure = await rich;
  assert.equal(failure.ok, false);
  assert.equal(failure.fallback.url, `/api/export/report-html?${scope}`);
  assert.match(failure.message, /tidak|gagal/i);
  for (const format of ['tsv', 'markdown']) {
    const result = await reportAction(`copy-${format}`, deps);
    assert.equal(result.ok, false); assert.equal(result.fallback.url, `/api/export/${format}?${scope}`);
  }
  const good = await reportAction('docx', deps);
  assert.equal(good.ok, true); assert.equal(seen.at(-1), `/api/export/docx?${scope}`);
  const bad = await reportAction('xlsx', {...deps, download: async () => {throw new Error('Synthetic offline');}});
  assert.equal(bad.ok, false); assert.match(bad.message, /offline/);
  const copied = await reportAction('copy-html', {...deps, copyHTML: async () => {}});
  assert.equal(copied.ok, true);
});

test('report UI isolates document HTML and escapes scope, title, group options, and failure fallback', async () => {
  const {reportPage, reportPreview, reportFallback, groupOptions, sandboxDocument} = await import('../../app/static/js/features/reports/render.js');
  const scope = new URLSearchParams({tenant: '<example>', q: '<synthetic>', review_status: 'all'});
  const page = reportPage(scope);
  assert.match(page, /for="report-group"/);
  assert.match(page, /<details/); assert.match(page, /<summary/);
  assert.match(page, /&lt;example&gt;/); assert.doesNotMatch(page, /<example>/);
  const preview = reportPreview({count: 702, meta: {title: '<Synthetic title>'}, html: '<script>synthetic</script>', truncated: false});
  assert.match(preview, /702/); assert.match(preview, /&lt;Synthetic title&gt;/);
  assert.match(preview, /sandbox=""/); assert.doesNotMatch(preview, /allow-scripts|<script>/);
  const document = sandboxDocument('<p>Synthetic evidence</p>');
  assert.match(document, /Content-Security-Policy/); assert.match(document, /default-src 'none'/);
  const groups = groupOptions([{id: 'case"1', title: '<Synthetic case>', alert_count: 3}], 'case"1');
  assert.match(groups, /&lt;Synthetic case&gt;/); assert.match(groups, /selected/);
  const fallback = reportFallback({url: '/api/export/report-html?tenant=example&q=%3Cscript%3E', format: 'report-html'});
  assert.match(fallback, /rel="noopener noreferrer"/); assert.match(fallback, /&amp;q=/);
  assert.match(fallback, /Unduh/); assert.match(fallback, /scope/i);
});

test('selected IDs preserve tenant and never silently broaden malformed or empty explicit selections', async () => {
  const {reportScope, caseReportRoute} = await load();
  const scope = reportScope(new URLSearchParams('tenant=example&alert_ids=7,3,7&q=ignored&group_id=ignored&review_status=reviewed'));
  assert.equal(scope.get('alert_ids'), '7,3'); assert.equal(scope.get('tenant'), 'example');
  for (const key of ['q', 'review_status', 'filter_preset', 'group_id', 'status']) assert.equal(scope.has(key), false);
  for (const ids of ['', '1,', '1e2', '0', '1,bad', '-1', '9007199254740993']) {
    assert.throws(() => reportScope(new URLSearchParams({tenant: 'example', alert_ids: ids})), /pilihan/i);
  }
  const route = new URL(caseReportRoute(scope, 'synthetic-case'), 'http://synthetic.invalid');
  assert.equal(route.pathname, '/reports'); assert.equal(route.searchParams.get('group_id'), 'synthetic-case');
  assert.equal(route.searchParams.get('tenant'), 'example'); assert.equal(route.searchParams.has('alert_ids'), false);
});
