import test from 'node:test';
import assert from 'node:assert/strict';

const modelURL = new URL('../../app/static/js/features/incidents/model.js', import.meta.url);
const load = () => import(modelURL);

test('incident list filters combine search, status and severity without mutating source', async () => {
  const m = await load();
  const groups = [
    {id: 'case-a', title: 'Synthetic network review', category: 'Network', severity: 'high', status: 'open', updated_at: '2026-01-02', alert_count: 2},
    {id: 'case-b', title: 'Synthetic endpoint review', category: 'Endpoint', severity: 'low', status: 'closed', updated_at: '2026-01-03', alert_count: 0},
    {id: 'case-c', title: 'Synthetic network follow-up', category: 'Network', severity: 'high', status: 'open', updated_at: '2026-01-04', alert_count: 1},
  ];
  const result = m.filterIncidents(groups, {q: 'network', status: 'open', severity: 'high', sort: 'updated_desc'});
  assert.deepEqual(result.map(row => row.id), ['case-c', 'case-a']);
  assert.equal(groups[0].id, 'case-a');
  assert.deepEqual(m.filterIncidents(groups, {q: 'absent'}), []);
});

test('draft payload keeps long-form text exact, validates title and retains only editable fields', async () => {
  const m = await load();
  const draft = m.draftFrom({id: 'synthetic-case', title: '  Evidence review  ', analysis: '\nLine one\n\nLine two  ', severity: 'critical', status: 'investigating', alert_pks: [9, 4, 9], raw: {secret: 'not a draft'}});
  assert.deepEqual(draft.alert_pks, [4, 9]);
  assert.equal(draft.analysis, '\nLine one\n\nLine two  ');
  assert.equal('raw' in draft, false);
  assert.equal(m.validateDraft({...draft, title: ' \n '}).title, 'Enter an incident title.');
  assert.deepEqual(m.validateDraft(draft), {});
  assert.equal(m.incidentPayload(draft).title, 'Evidence review');
  assert.equal(m.incidentPayload(draft).analysis, draft.analysis);
  assert.equal(m.draftsEqual(draft, {...draft, alert_pks: [9, 4]}), true);
  assert.equal(m.draftsEqual(draft, {...draft, analysis: 'Changed'}), false);
});

test('case routes and evidence scopes never lose tenant or inherit triage review filters', async () => {
  const m = await load();
  const params = new URLSearchParams('tenant=Synthetic+North&alert_ids=8,4,8&review_status=unreviewed&q=old');
  assert.deepEqual(m.incidentRoute({path: '/incidents/new', params}), {mode: 'create', id: null, tenant: 'Synthetic North', alertIds: [4, 8]});
  assert.equal(m.incidentRoute({path: '/incidents/synthetic-case', params}).id, 'synthetic-case');
  const href = new URL(m.caseHref('synthetic-case', 'Synthetic North'), 'https://fixture.invalid');
  assert.equal(href.pathname, '/incidents/synthetic-case');
  assert.equal(href.searchParams.get('tenant'), 'Synthetic North');
  const scope = m.evidenceParams({tenant: 'Synthetic North', groupId: 'synthetic-case', offset: 50});
  assert.equal(scope.get('group_id'), 'synthetic-case');
  assert.equal(scope.get('tenant'), 'Synthetic North');
  assert.equal(scope.get('review_status'), 'all');
  assert.equal(scope.get('summary'), 'true');
  assert.equal(scope.get('offset'), '50');
  assert.equal(scope.get('sort'), 'asc');
  assert.throws(() => m.selectedIds('4,not-an-id'), /positive whole/);
});

