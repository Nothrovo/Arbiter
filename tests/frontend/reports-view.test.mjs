import test from 'node:test';
import assert from 'node:assert/strict';

class Control extends EventTarget {
  constructor() {super(); this.value = ''; this.textContent = ''; this.innerHTML = ''; this.hidden = false; this.disabled = false; this.dataset = {}; this.attributes = {};}
  setAttribute(name, value) {this.attributes[name] = String(value);}
  focus() {this.focused = true;}
  closest() {return this;}
  contains() {return true;}
  removeAttribute(name) {delete this.attributes[name];}
}
function fixture(params = 'tenant=example&q=synthetic&review_status=reviewed') {
  const elements = new Map(); const root = new Control();
  root.querySelector = selector => {if (!elements.has(selector)) elements.set(selector, new Control()); return elements.get(selector);};
  const exports = ['copy-html', 'docx'].map(format => Object.assign(new Control(), {dataset: {export: format}}));
  root.querySelectorAll = selector => selector === '[data-export]' ? exports : [];
  const abort = new AbortController(); const routes = []; const notices = [];
  return {root, exports, abort, routes, notices, ctx: {root, signal: abort.signal, route: {params: new URLSearchParams(params)}, setGuard() {}, navigate: path => routes.push(path), notify: (...args) => notices.push(args)}};
}
function click(root, dataset) {
  const event = new Event('click'); Object.defineProperty(event, 'target', {value: Object.assign(new Control(), {dataset})}); root.dispatchEvent(event);
}
const tick = () => new Promise(resolve => setTimeout(resolve, 0));

test('Reports mount loads scoped document, navigates case scope in URL, and retains scope when clipboard is unavailable', async () => {
  const {mount} = await import('../../app/static/js/features/reports/view.js');
  const f = fixture(); const requests = []; const original = globalThis.fetch;
  globalThis.fetch = async path => {
    requests.push(path);
    if (path.startsWith('/api/groups?')) return new Response(JSON.stringify([{id: 'synthetic-case', title: 'Synthetic case', alert_count: 702}]));
    assert.match(path, /^\/api\/export\/preview\?/);
    return new Response(JSON.stringify({count: 702, meta: {title: 'Synthetic report'}, scope: Object.fromEntries(new URL(path, 'http://synthetic.invalid').searchParams), html: '<p>Synthetic evidence</p>', truncated: false}));
  };
  try {
    const cleanup = mount(f.ctx); await tick(); await tick();
    assert.match(f.root.innerHTML, /Laporan/);
    assert.match(f.root.querySelector('#report-document').innerHTML, /sandbox=""/);
    assert.match(f.root.querySelector('#report-count').textContent, /702/);
    assert.equal(f.exports[0].disabled, false);
    assert.equal(requests.includes('/api/groups?tenant=example'), true);
    click(f.root, {export: 'copy-html'}); await tick(); await tick();
    assert.match(f.root.querySelector('#report-action-status').textContent, /tidak disalin/);
    const fallback = f.root.querySelector('#report-fallback');
    assert.equal(fallback.hidden, false); assert.match(fallback.innerHTML, /tenant=example&amp;q=synthetic/);
    const select = f.root.querySelector('#report-group'); select.value = 'synthetic-case'; select.dispatchEvent(new Event('change'));
    const route = new URL(f.routes[0], 'http://synthetic.invalid');
    assert.equal(route.searchParams.get('tenant'), 'example'); assert.equal(route.searchParams.get('group_id'), 'synthetic-case');
    assert.equal(route.searchParams.has('q'), false);
    f.abort.abort(); cleanup(); const count = requests.length;
    f.root.dispatchEvent(new Event('arbiter:refresh')); await tick(); assert.equal(requests.length, count);
  } finally {globalThis.fetch = original;}
});

test('Reports invalid selection does not call any endpoint or offer broad export', async () => {
  const {mount} = await import('../../app/static/js/features/reports/view.js');
  const f = fixture('tenant=example&alert_ids='); const original = globalThis.fetch;
  globalThis.fetch = async () => {assert.fail('No requests allowed for invalid scope');};
  try {const cleanup = mount(f.ctx); await tick(); assert.match(f.root.innerHTML, /Pilihan alert tidak valid/); f.abort.abort(); cleanup();}
  finally {globalThis.fetch = original;}
});
