import test from 'node:test';
import assert from 'node:assert/strict';

test('renderTriageSummary renders compact strip with all metrics, actions, and stats link', async () => {
  const {renderTriageSummary, summaryRequestParams} = await import('../../app/static/js/features/triage/model.js');
  
  const query = {
    tenant: 'Alpha',
    tenants: ['Alpha', 'Beta'],
    q: 'probe',
    filter_preset: '403',
  };

  const params = summaryRequestParams(query);
  assert.equal(params.getAll('tenant').length, 2);
  assert.equal(params.get('q'), 'probe');
  assert.equal(params.get('filter_preset'), '403');
  assert.equal(params.has('limit'), false);
  assert.equal(params.has('offset'), false);

  const summaryData = {
    alerts: 42,
    events: 180,
    unique_source_ips: 12,
    unique_agents: 3,
    severity: {critical: 5, high: 10, medium: 20, low: 7},
    incident_cases: 2,
    time_range: {earliest: '2026-01-01T10:00:00Z', latest: '2026-01-01T12:00:00Z'},
    top_rule: {rule_id: '1001', description: 'SQL injection probe', count: 18},
  };

  const html = renderTriageSummary(summaryData, query, {collapsed: false});
  assert.match(html, /42/);
  assert.match(html, /180/);
  assert.match(html, /12/); // unique ips
  assert.match(html, /3/);  // unique agents
  assert.match(html, /data-summary-action="severity"/);
  assert.match(html, /data-summary-action="grouped"/);
  assert.match(html, /data-summary-action="top-rule"/);
  assert.match(html, /#\/stats\?/);
  assert.match(html, /Lihat statistik lengkap/);
  assert.match(html, /SQL injection probe/);
});
