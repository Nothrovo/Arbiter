import test from 'node:test';
import assert from 'node:assert/strict';

class Control extends EventTarget {
  constructor() {super(); this.value = ''; this.textContent = ''; this.innerHTML = ''; this.hidden = false; this.disabled = false; this.dataset = {}; this.attributes = {}; this.files = [];}
  setAttribute(name, value) {this.attributes[name] = String(value);}
  removeAttribute(name) {delete this.attributes[name];}
  focus() {this.focused = true;}
  closest() {return this;}
  contains() {return true;}
}
function fixture(params = 'tenant=example') {
  const elements = new Map();
  const root = new Control();
  root.ownerDocument = {defaultView: new EventTarget()};
  root.querySelector = selector => {if (!elements.has(selector)) elements.set(selector, new Control()); return elements.get(selector);};
  const modes = ['file', 'paste'].map(mode => Object.assign(new Control(), {dataset: {mode}}));
  const panels = ['file', 'paste'].map(panel => Object.assign(new Control(), {dataset: {panel}}));
  root.querySelectorAll = selector => selector === '[data-mode]' ? modes : selector === '[data-panel]' ? panels : [];
  const abort = new AbortController(); let guard;
  return {root, elements, modes, panels, abort, ctx: {root, signal: abort.signal, route: {params: new URLSearchParams(params)}, setGuard: fn => {guard = fn;}, notify() {}, navigate() {}}, guard: () => guard};
}
function click(root, dataset) {
  const event = new Event('click');
  Object.defineProperty(event, 'target', {value: Object.assign(new Control(), {dataset})});
  root.dispatchEvent(event);
}
const tick = () => new Promise(resolve => setTimeout(resolve, 0));

test('Import mount guards nonempty drafts, keeps failed input, resets intentionally, and cleans lifecycle', async () => {
  const {mount} = await import('../../app/static/js/features/imports/view.js');
  const f = fixture(); let calls = 0;
  const original = globalThis.fetch;
  globalThis.fetch = async path => {assert.equal(path, '/api/import-text'); calls++; return new Response(JSON.stringify({detail: 'Synthetic rejected'}), {status: 400});};
  try {
    const cleanup = mount(f.ctx);
    assert.match(f.root.innerHTML, /Impor alert/);
    assert.equal(f.guard()(), true);
    click(f.root, {mode: 'paste'});
    const input = f.root.querySelector('#import-content'); input.value = '{synthetic}'; input.dispatchEvent(new Event('input'));
    assert.equal(f.guard()(), false);
    const form = f.root.querySelector('#import-form'); form.dispatchEvent(new Event('submit', {cancelable: true}));
    await tick(); await tick();
    assert.equal(calls, 1); assert.equal(input.value, '{synthetic}');
    assert.match(f.root.querySelector('#import-error').textContent, /Synthetic rejected/);
    click(f.root, {action: 'reset'});
    assert.equal(input.value, ''); assert.equal(f.guard()(), true);
    f.abort.abort(); cleanup(); assert.equal(f.guard(), null);
    form.dispatchEvent(new Event('submit', {cancelable: true})); await tick(); assert.equal(calls, 1);
  } finally {globalThis.fetch = original;}
});

test('Import result triage link retains every repeated tenant in the current scope', async () => {
  const {mount} = await import('../../app/static/js/features/imports/view.js');
  const f = fixture('tenant=Beta&tenant=Alpha'); const original = globalThis.fetch;
  globalThis.fetch = async path => {
    assert.equal(path, '/api/import-text');
    return new Response(JSON.stringify({parsed: 2, inserted: 2, deduplicated: 0, warnings: []}));
  };
  try {
    const cleanup = mount(f.ctx);
    click(f.root, {mode: 'paste'});
    const input = f.root.querySelector('#import-content'); input.value = '{"synthetic":true}'; input.dispatchEvent(new Event('input'));
    f.root.querySelector('#import-form').dispatchEvent(new Event('submit', {cancelable: true}));
    await tick(); await tick();
    assert.match(f.root.querySelector('#import-result').innerHTML, /href="#\/triage\?tenant=Alpha&amp;tenant=Beta&amp;review_status=all"/);
    f.abort.abort(); cleanup();
  } finally {globalThis.fetch = original;}
});
