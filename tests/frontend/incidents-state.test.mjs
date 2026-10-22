import test from 'node:test';
import assert from 'node:assert/strict';
const load = () => import('../../app/static/js/features/incidents/state.js');
test('new incident creates once, verifies scoped result and retries verification without duplicate creation', async () => {
  const {createCaseState} = await load();
  const calls = [];
  let verifyFails = true;
  let stored;
  const state = createCaseState({tenant: 'Synthetic North', alertIds: [8, 9], json: async (url, options = {}) => {
    calls.push([url, options]);
    if (options.method === 'POST') {stored = {id: 'created-synthetic', ...JSON.parse(options.body)}; return {id: stored.id};}
    if (options.method === 'PUT') {stored = {...stored, ...JSON.parse(options.body)}; return {status: 'ok'};}
    if (verifyFails) {verifyFails = false; throw new Error('Verification offline');}
    return structuredClone(stored);
  }});
  assert.equal(await state.save(), false, 'Blank title must not make a request');
  assert.equal(calls.length, 0);
  state.edit('title', 'Synthetic created case');
  assert.equal(await state.save(), false);
  assert.equal(state.id, 'created-synthetic');
  assert.equal(state.dirty, true);
  assert.equal(await state.save(), true);
  assert.equal(calls.filter(([, options]) => options.method === 'POST').length, 1);
  assert.deepEqual(stored.alert_pks, [8, 9]);
  assert.equal(calls[0][0], '/api/groups?tenant=Synthetic+North');
});

test('deletion requires a named confirmation and verifies absence before reporting success', async () => {
  const {createCaseState} = await load();
  let removed = false;
  let writes = 0;
  const state = createCaseState({id: 'synthetic-case', tenant: 'Synthetic North', json: async (url, options = {}) => {
    assert.equal(new URL(url, 'https://fixture.invalid').searchParams.get('tenant'), 'Synthetic North');
    if (options.method === 'DELETE') {writes++; removed = true; return {status: 'ok'};}
    if (removed) throw Object.assign(new Error('Not found'), {status: 404});
    return group();
  }});
  await state.load();
  assert.equal(await state.remove(() => false), false);
  assert.equal(writes, 0);
  assert.equal(await state.remove(text => {assert.match(text, /Synthetic investigation/); assert.match(text, /Alerts will not be deleted/); return true;}), true);
  assert.equal(writes, 1);
  assert.equal(state.deleted, true);
});

test('aborted and stale loads are ignored rather than replacing the current incident', async () => {
  const {createCaseState} = await load();
  const pending = [];
  const state = createCaseState({id: 'synthetic-case', json: () => new Promise(resolve => pending.push(resolve))});
  const first = state.load();
  const second = state.load();
  pending[1](group({analysis: 'Latest'}));
  await second;
  pending[0](group({analysis: 'Old'}));
  await first;
  assert.equal(state.draft.analysis, 'Latest');
  const aborted = createCaseState({id: 'synthetic-case', json: async () => {throw new DOMException('Cancelled', 'AbortError');}});
  assert.equal(await aborted.load(), false);
  assert.equal(aborted.error, '');
});

test('evidence pages are chronological, explicit-counted, tenant-scoped, and ignore stale responses', async () => {
  const {createEvidenceState} = await load();
  const pending = [];
  const calls = [];
  const state = createEvidenceState({tenant: 'Synthetic North', groupId: 'synthetic-case', json: (url, options) => {calls.push([url, options]); return new Promise(resolve => pending.push(resolve));}});
  const first = state.load();
  const second = state.load({offset: 50});
  pending[1]({items: [{id: 52, timestamp: '2026-01-03', hit_count: 0}], total: 73});
  await second;
  pending[0]({items: [{id: 1, timestamp: '2026-01-01'}], total: 73});
  await first;
  assert.equal(state.rows[0].id, 52);
  assert.equal(state.total, 73);
  assert.equal(state.offset, 50);
  assert.equal(state.hasNext, false);
  const params = new URL(calls[1][0], 'https://fixture.invalid').searchParams;
  assert.equal(params.get('tenant'), 'Synthetic North');
  assert.equal(params.get('group_id'), 'synthetic-case');
  assert.equal(params.get('summary'), 'true');
  assert.equal(params.get('review_status'), 'all');
  assert.equal(params.get('sort'), 'asc');
});

test('selected evidence loads only requested IDs in tenant scope and exposes failures without losing selection', async () => {
  const {loadSelectedEvidence} = await load();
  const calls = [];
  const result = await loadSelectedEvidence({ids: [3, 4], tenant: 'Synthetic North', json: async url => {
    calls.push(url);
    if (url.includes('/4?')) throw new Error('Synthetic scope error');
    return {id: 3, tenant: 'Synthetic North', description: 'Synthetic selected evidence', raw: {secret: 'excluded'}, full_log: 'excluded'};
  }});
  assert.deepEqual(result.rows.map(row => row.id), [3]);
  assert.equal(result.rows[0].raw, undefined);
  assert.equal(result.rows[0].full_log, undefined);
  assert.deepEqual(result.failedIds, [4]);
  assert.match(result.error, /4/);
  for (const url of calls) assert.equal(new URL(url, 'https://fixture.invalid').searchParams.get('tenant'), 'Synthetic North');
});

const group = (extra = {}) => ({id: 'synthetic-case', title: 'Synthetic investigation', category: 'Network', severity: 'high', status: 'open', analysis: 'Initial narrative', conclusion: '', recommendation: '', alert_pks: [1, 2], tenants: ['Synthetic North'], ...extra});

test('refresh never replaces an unsaved narrative; explicit discard restores server values', async () => {
  const {createCaseState} = await load();
  let server = group();
  const calls = [];
  const state = createCaseState({id: 'synthetic-case', tenant: 'Synthetic North', json: async (url, options) => {calls.push([url, options]); return structuredClone(server);}});
  await state.load();
  assert.equal(state.dirty, false);
  state.edit('analysis', 'Unsaved\n\nlong-form narrative');
  server = group({analysis: 'Updated on server'});
  await state.refresh();
  assert.equal(state.draft.analysis, 'Unsaved\n\nlong-form narrative');
  assert.equal(state.refreshDeferred, true);
  assert.equal(calls.length, 1);
  assert.equal(new URL(calls[0][0], 'https://fixture.invalid').searchParams.get('tenant'), 'Synthetic North');
  state.discard();
  assert.equal(state.draft.analysis, 'Initial narrative');
  await state.refresh();
  assert.equal(state.draft.analysis, 'Updated on server');
  assert.equal(state.dirty, false);
});

test('save failures retain draft and retry writes metadata and staged membership in tenant scope', async () => {
  const {createCaseState} = await load();
  let server = group();
  const calls = [];
  let fail = true;
  const state = createCaseState({id: server.id, tenant: 'Synthetic North', json: async (url, options = {}) => {
    calls.push([url, options]);
    if (options.method === 'PUT') {
      if (fail) {fail = false; throw new Error('Synthetic offline');}
      server = {...server, ...JSON.parse(options.body)};
      return {status: 'ok'};
    }
    if (options.method === 'POST') {server.alert_pks.push(...JSON.parse(options.body).alert_pks); return {status: 'ok'};}
    if (options.method === 'DELETE') {server.alert_pks = server.alert_pks.filter(id => id !== 1); return {status: 'ok'};}
    return structuredClone(server);
  }});
  await state.load();
  state.edit('analysis', 'Synthetic new narrative');
  state.stage(3, true);
  state.stage(1, false);
  assert.equal(await state.save(), false);
  assert.equal(state.error, 'Synthetic offline');
  assert.equal(state.draft.analysis, 'Synthetic new narrative');
  assert.equal(state.dirty, true);
  assert.equal(await state.save(), true);
  assert.deepEqual(state.draft.alert_pks, [2, 3]);
  assert.equal(state.dirty, false);
  assert.equal(state.notice, 'Incident saved.');
  const writes = calls.filter(([, options]) => options.method);
  assert.deepEqual(writes.map(([, options]) => options.method), ['PUT', 'PUT', 'POST', 'DELETE']);
  for (const [url] of calls) assert.equal(new URL(url, 'https://fixture.invalid').searchParams.get('tenant'), 'Synthetic North');
  assert.equal(new URL(writes[2][0], 'https://fixture.invalid').pathname, '/api/groups/synthetic-case/members');
  assert.deepEqual(JSON.parse(writes[2][1].body).alert_pks, [3]);
  assert.equal(new URL(writes[3][0], 'https://fixture.invalid').pathname, '/api/groups/synthetic-case/members/1');
  assert.equal(calls.at(-1)[1].method, undefined, 'Save is verified with scoped GET, not the write response');
});
