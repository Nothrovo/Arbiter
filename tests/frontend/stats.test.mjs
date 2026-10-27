import test from 'node:test';
import assert from 'node:assert/strict';

test('stats session manages monotonic versions and ignores stale responses', async () => {
  const {createStatsSession} = await import('../../app/static/js/state/stats.js');
  const session = createStatsSession();
  const v1 = session.nextRequest();
  const v2 = session.nextRequest();
  assert.equal(session.isCurrent(v1), false);
  assert.equal(session.isCurrent(v2), true);
  session.dispose();
  assert.equal(session.isCurrent(v2), false);
});

test('normalizeStatsQuery validates defaults, bounds, and preserves multi-tenant scope', async () => {
  const {normalizeStatsQuery, distributionPercentages, triageRouteFromStats} = await import('../../app/static/js/features/stats/model.js');
  
  const params = new URLSearchParams('tenant=Alpha&tenant=Beta&pivot_by=severity&secondary_pivot=url_path&facet=rule_description&facet_value=Web+400&secondary_facet=url_path&secondary_facet_value=%2F.env&metric=events&chart=donut&top_n=100&q=test');
  const query = normalizeStatsQuery(params);
  assert.equal(query.pivot_by, 'severity');
  assert.equal(query.secondary_pivot, 'url_path');
  assert.equal(query.facet, 'rule_description');
  assert.equal(query.facet_value, 'Web 400');
  assert.equal(query.secondary_facet, 'url_path');
  assert.equal(query.secondary_facet_value, '/.env');
  assert.equal(query.metric, 'events');
  assert.equal(query.chart, 'donut');
  assert.equal(query.top_n, 100);
  assert.deepEqual(query.tenants, ['Alpha', 'Beta']);
  assert.equal(query.q, 'test');

  // Distribution percentages absorb rounding remainder to sum to exactly 100.0%
  const rows = [
    {key: 'A', count: 1, percentage: 33.33},
    {key: 'B', count: 1, percentage: 33.33},
    {key: 'C', count: 1, percentage: 33.33},
  ];
  const adjusted = distributionPercentages(rows, 0, 3);
  const sum = adjusted.reduce((acc, r) => acc + r.displayPercentage, 0);
  assert.equal(Math.round(sum * 10) / 10, 100.0);

  // Triage route carries exact multi-tenant scope and active filters
  const triageHref = triageRouteFromStats(query);
  assert.match(triageHref, /#\/triage\?/);
  assert.match(triageHref, /tenant=Alpha/);
  assert.match(triageHref, /tenant=Beta/);
  assert.match(triageHref, /q=test/);
});

test('stats export formatters generate clean CSV and markdown analysis summary', async () => {
  const {generateStatsCSV, generateMarkdownSummary} = await import('../../app/static/js/features/stats/model.js');
  
  const statsData = {
    pivot_by: 'rule_description',
    metric: 'alerts',
    total: 100,
    items: [
      {key: 'SQL Injection', count: 60, displayPercentage: 60.0},
      {key: 'Brute Force', count: 30, displayPercentage: 30.0},
    ],
    other_count: 10,
    other_percentage: 10.0,
    scope: {tenant: ['Alpha'], q: ''},
  };

  const csv = generateStatsCSV(statsData);
  assert.match(csv, /Kategori,Jumlah,Persen/);
  assert.match(csv, /"SQL Injection",60,60/);
  assert.match(csv, /"Lainnya",10,10/);

  const md = generateMarkdownSummary(statsData);
  assert.match(md, /### Ringkasan Statistik Alert/);
  assert.match(md, /SQL Injection: 60 \(60%\)/);
  assert.match(md, /Total: 100 alert/);
});
