import test from 'node:test';
import assert from 'node:assert/strict';
const load = () => import('../../app/static/js/features/incidents/render.js');

test('case workspace exposes long-form fields, one explicit save model and scoped report link', async () => {
  const {renderWorkspace} = await load();
  const {draftFrom} = await import('../../app/static/js/features/incidents/model.js');
  const state = {id: 'synthetic-case', tenant: 'Synthetic North', draft: draftFrom({title: '</h1><script>unsafe</script>', analysis: 'Long\n\ntext & evidence'}), group: {tenants: ['Synthetic North']}, dirty: true};
  const html = renderWorkspace(state);
  for (const field of ['title', 'category', 'severity', 'status', 'analysis', 'conclusion', 'recommendation']) assert.match(html, new RegExp(`name="${field}"`));
  assert.match(html, /rows="16"/);
  assert.match(html, /data-save-status/);
  assert.match(html, /aria-live="polite"/);
  assert.match(html, /data-action="save"/);
  assert.match(html, /data-action="delete"/);
  assert.match(html, /group_id=synthetic-case/);
  assert.match(html, /tenant=Synthetic\+North/);
  assert.doesNotMatch(html, /<script>/);
  assert.match(html, /Long\n\ntext &amp; evidence/);
  assert.match(html, /data-evidence-region/);
  assert.match(html, /data-candidate-region/);
  const ids = [...html.matchAll(/\sid="([^"]+)"/g)].map(match => match[1]);
  assert.equal(new Set(ids).size, ids.length, 'Section anchors and text controls must have unique IDs');
  assert.doesNotMatch(html, /<main\b/, 'The parent already owns the main landmark');
  assert.match(html, /name="evidence_q"[^>]*placeholder="Event, asset, rule, atau sumber…"[^>]*autocomplete="off"/);
});

test('evidence chronology renders occurrence counts and semantic details but never raw logs', async () => {
  const {renderEvidence} = await load();
  const html = renderEvidence({rows: [{id: 7, description: 'Synthetic event <one>', first_seen: '2026-01-01', last_seen: '2026-01-02', hit_count: 0, rule_level: 10, agent_name: 'Synthetic asset', rule_id: '100', source_ip: '192.0.2.1', mitre_ids: ['T0000'], tenant: 'Synthetic North', full_log: 'SECRET RAW FIXTURE', raw: {private: 'PRIVATE FIXTURE'}}], total: 73, offset: 0, limit: 50, hasNext: true}, {selected: [7], tenant: 'Synthetic North'});
  assert.match(html, /Synthetic event &lt;one&gt;/);
  assert.match(html, /0 occurrence/);
  assert.match(html, /T0000/);
  assert.match(html, /192\.0\.2\.1/);
  assert.match(html, /73/);
  assert.match(html, /data-action="evidence-next"/);
  assert.match(html, /data-stage-id="7"/);
  assert.doesNotMatch(html, /SECRET RAW|PRIVATE FIXTURE/);
});

test('incident list renders escaped linked cases with filter controls and explicit empty/error states', async () => {
  const {renderList} = await load();
  const html = renderList({tenant: 'Synthetic North', groups: [{id: 'synthetic-case', title: '<Synthetic & case>', category: 'Network', severity: 'high', status: 'open', alert_count: 0}], filters: {}, loading: false});
  assert.match(html, /&lt;Synthetic &amp; case&gt;/);
  assert.doesNotMatch(html, /<Synthetic/);
  assert.match(html, /incidents\/synthetic-case\?tenant=Synthetic\+North/);
  assert.match(html, /name="q"/);
  assert.match(html, /name="case_status"/);
  assert.match(html, /name="severity"/);
  assert.match(html, /<td[^>]*>0<\/td>/);
  assert.match(renderList({tenant: 'all', groups: [], filters: {q: 'missing'}}), /Tidak ada insiden yang cocok/);
  assert.match(renderList({tenant: 'all', groups: [], filters: {}, error: 'Synthetic offline'}), /Synthetic offline/);
});
