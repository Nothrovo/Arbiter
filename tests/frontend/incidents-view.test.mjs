import test from 'node:test';
import assert from 'node:assert/strict';

class SyntheticRoot {
  constructor() {this.innerHTML = ''; this.nodes = new Map(); this.listeners = new Map(); this.ownerDocument = {defaultView: {confirm: () => false}};}
  querySelector(selector) {
    if (!this.nodes.has(selector)) this.nodes.set(selector, {innerHTML: '', textContent: '', disabled: false, value: '', setAttribute() {}, removeAttribute() {}, focus() {}, scrollIntoView() {}});
    return this.nodes.get(selector);
  }
  querySelectorAll() {return [];}
  addEventListener(type, fn, options = {}) {
    const list = this.listeners.get(type) || [];
    list.push(fn); this.listeners.set(type, list);
    options.signal?.addEventListener('abort', () => this.removeEventListener(type, fn), {once: true});
  }
  removeEventListener(type, fn) {this.listeners.set(type, (this.listeners.get(type) || []).filter(value => value !== fn));}
  async send(type, target = {}) {const event = {target, preventDefault() {}, button: 0}; for (const fn of this.listeners.get(type) || []) await fn(event);}
}
const fixture = () => ({id: 'synthetic-case', title: 'Synthetic investigation', category: 'Network', severity: 'high', status: 'open', analysis: 'Synthetic initial', conclusion: '', recommendation: '', alert_pks: [7], tenants: ['Synthetic North']});
const context = (path = '/incidents') => {
  const controller = new AbortController(); const root = new SyntheticRoot(); const guards = []; const navigations = [];
  return {root, route: {path, params: new URLSearchParams('tenant=Synthetic+North')}, signal: controller.signal, controller, setGuard: value => guards.push(value), guards, navigate: (...args) => navigations.push(args), navigations, notify() {}};
};
const load = () => import('../../app/static/js/features/incidents/view.js');

test('case mount preserves typed analysis on refresh and saves exact input with scoped verification', async () => {
  const original = globalThis.fetch;
  let server = fixture();
  const calls = [];
  globalThis.fetch = async (url, options = {}) => {
    calls.push([String(url), options]);
    if (String(url).startsWith('/api/alerts?')) return Response.json({items: [{id: 7, tenant: 'Synthetic North', description: 'Synthetic evidence', hit_count: 3}], total: 1});
    if (options.method === 'PUT') {server = {...server, ...JSON.parse(options.body)}; return Response.json({status: 'ok'});}
    return Response.json(server);
  };
  try {
    const ctx = context('/incidents/synthetic-case');
    const {mount} = await load();
    const cleanup = await mount(ctx);
    assert.match(ctx.root.innerHTML, /name="analysis"/);
    assert.equal(typeof ctx.guards.at(-1), 'function');
    assert.equal(ctx.guards.at(-1)(), true);
    const value = 'Synthetic typed analysis\n\nwith exact line breaks';
    await ctx.root.send('input', {name: 'analysis', value, closest: selector => selector === '#incident-editor' ? {} : null});
    assert.equal(ctx.guards.at(-1)(), false);
    const before = calls.length;
    await ctx.root.send('arbiter:refresh');
    assert.equal(calls.length, before, 'Dirty refresh must not refetch or replace the editor');
    assert.match(ctx.root.querySelector('[data-refresh-notice]').textContent, /belum disimpan/);
    await ctx.root.send('submit', {id: 'incident-editor', matches: selector => selector === '#incident-editor'});
    assert.equal(server.analysis, value);
    assert.equal(ctx.guards.at(-1)(), true);
    const put = calls.find(([, options]) => options.method === 'PUT');
    assert.equal(new URL(put[0], 'https://fixture.invalid').searchParams.get('tenant'), 'Synthetic North');
    assert.equal(JSON.parse(put[1].body).analysis, value);
    cleanup(); assert.equal(ctx.guards.at(-1), null);
  } finally {globalThis.fetch = original;}
});

test('new case initializes evidence from alert_ids without querying global evidence', async () => {
  const original = globalThis.fetch;
  const calls = [];
  globalThis.fetch = async url => {calls.push(String(url)); return Response.json({id: 7, tenant: 'Synthetic North', description: 'Synthetic chosen alert'});};
  try {
    const ctx = context('/incidents/new');
    ctx.route.params.set('alert_ids', '7');
    const cleanup = await (await load()).mount(ctx);
    assert.match(ctx.root.innerHTML, /Buat insiden/);
    assert.deepEqual(calls, ['/api/alerts/7?tenant=Synthetic+North']);
    assert.match(ctx.root.querySelector('[data-selected-evidence]').innerHTML, /Synthetic chosen alert/);
    assert.equal(ctx.guards.at(-1)(), false);
    cleanup();
  } finally {globalThis.fetch = original;}
});

test('incident mount reads scoped list, refreshes through abortable listener and clears guard on cleanup', async () => {
  const original = globalThis.fetch;
  const calls = [];
  globalThis.fetch = async url => {calls.push(String(url)); return Response.json([fixture()]);};
  try {
    const ctx = context();
    const {mount} = await load();
    const cleanup = await mount(ctx);
    assert.match(ctx.root.innerHTML, /Synthetic investigation/);
    assert.equal(new URL(calls[0], 'https://fixture.invalid').searchParams.get('tenant'), 'Synthetic North');
    await ctx.root.send('arbiter:refresh');
    assert.equal(calls.length, 2);
    ctx.controller.abort();
    await ctx.root.send('arbiter:refresh');
    assert.equal(calls.length, 2);
    cleanup();
    assert.equal(ctx.guards.at(-1), null);
  } finally {globalThis.fetch = original;}
});
