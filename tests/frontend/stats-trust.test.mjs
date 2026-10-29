import test from 'node:test';
import assert from 'node:assert/strict';
import {mount} from '../../app/static/js/features/stats/view.js';

const flush = () => new Promise(resolve => setImmediate(resolve));
const stats = label => ({total: 1, metric: 'alerts', pivot_by: 'rule_description', items: [{key: label, count: 1, percentage: 100}]});
const alert = id => ({id, description: `Synthetic evidence ${id}`, timestamp: '2026-01-01T00:00:00Z', severity: 5});

// Exercise the real view, query serialization, API client and renderers. Only the
// network and the DOM surface are synthetic; deferred fetches may ignore aborts.
function harness(t, params = 'tenant=Synthetic+North&facet=rule_id&facet_value=42&chart=table') {
  const requests = [];
  const elements = new Map();
  const handlers = new Map();
  const navigations = [];
  const notices = [];
  function element() {
    return {innerHTML: '', textContent: '', style: {}, addEventListener() {}, close() {}, showModal() {}};
  }
  for (const id of ['stats-results', 'stats-batch-incident-dialog', 'stats-batch-incident-form', 'stats-batch-incident-select', 'stats-batch-incident-hint', 'stats-batch-incident-count', 'stats-applied-filters']) {
    elements.set(`#${id}`, element());
  }
  const root = {
    innerHTML: '',
    querySelector: selector => elements.get(selector) || null,
    addEventListener: (type, fn) => handlers.set(type, fn),
  };
  t.mock.method(globalThis, 'fetch', (url, options) => new Promise((resolve, reject) => {
    requests.push({url, options, reject, respond: (body, status = 200) => resolve({ok: status < 400, status, json: async () => body})});
  }));
  const controller = new AbortController();
  const dispose = mount({root, route: {params: new URLSearchParams(params)}, signal: controller.signal,
    navigate: href => navigations.push(href), notify: (...args) => notices.push(args)});
  t.after(dispose);
  function click(dataset = {}, id = '') {
    const button = {dataset, id, hasAttribute: () => false};
    return handlers.get('click')({target: {closest: selector => selector === '[data-secondary-key]' ? null : button}});
  }
  function change(dataset, checked = true) {
    return handlers.get('change')({target: {id: '', dataset, checked,
      matches: selector => selector === '[data-select-drilldown]' ? 'selectDrilldown' in dataset : 'selectSecondaryKey' in dataset}});
  }
  return {requests, root, elements, controller, dispose, click, change, navigations, notices,
    results: elements.get('#stats-results')};
}

async function startSample(h, label = 'Synthetic original') {
  h.requests[0].respond(stats(label));
  await flush();
  assert.equal(h.requests.length, 2);
  assert.match(h.requests[1].url, /^\/api\/alerts\?/);
}

for (const action of ['create-incident', 'batch-secondary-create-incident']) {
  test(`${action} preserves all tenants in the new incident route`, async t => {
    const h = harness(t, 'tenant=Synthetic+North&tenant=Synthetic+South&facet=rule_id&facet_value=42&chart=table');
    await startSample(h);
    h.requests[1].respond({items: [alert(11)]});
    await flush();
    h.change({selectDrilldown: '11'});
    h.change({selectSecondaryKey: 'synthetic-path'});
    const creating = action === 'create-incident' ? h.click({statsAction: action}) : h.click({action});
    if (action === 'batch-secondary-create-incident') {
      h.requests[2].respond({alert_pks: [11]});
    }
    await creating;
    const params = new URLSearchParams(h.navigations[0].split('?')[1]);
    assert.deepEqual(params.getAll('tenant'), ['Synthetic North', 'Synthetic South']);
    assert.equal(params.get('alert_ids'), '11');
  });
}

test('empty incident fallback preserves repeated encoded tenants and selected evidence', async t => {
  const tenants = ['Synthetic & North', 'Synthetic / South'];
  const params = new URLSearchParams({facet: 'rule_id', facet_value: '42', chart: 'table'});
  tenants.forEach(tenant => params.append('tenant', tenant));
  const h = harness(t, params.toString());
  await startSample(h);
  h.requests[1].respond({items: [alert(11), alert(22)]});
  await flush();
  h.change({selectDrilldown: '11'});
  h.change({selectDrilldown: '22'});
  const opening = h.click({statsAction: 'add-to-incident'});
  assert.deepEqual(new URL(h.requests[2].url, 'https://fixture.invalid').searchParams.getAll('tenant'), tenants);
  h.requests[2].respond([]);
  await opening;
  const html = h.elements.get('#stats-batch-incident-hint').innerHTML;
  const href = html.match(/href="([^"]+)"/)[1].replaceAll('&amp;', '&');
  const target = new URLSearchParams(href.split('?')[1]);
  assert.deepEqual(target.getAll('tenant'), tenants);
  assert.equal(target.get('alert_ids'), '11,22');
  assert.match(href, /^#\/incidents\/new\?/);
});

test('sample HTTP failure is an explicit retryable error, not successful empty evidence', async t => {
  const h = harness(t);
  await startSample(h);
  h.requests[1].respond({detail: 'Synthetic evidence service unavailable'}, 503);
  await flush();
  assert.ok(h.results.innerHTML.includes('Synthetic evidence service unavailable'));
  assert.ok(h.results.innerHTML.includes('data-action="retry"'));
  assert.ok(!h.results.innerHTML.includes('Synthetic original'));
  const retry = h.click({action: 'retry'});
  h.requests[2].respond(stats('Synthetic recovered'));
  await flush();
  h.requests[3].respond({items: []});
  await retry;
  assert.match(h.results.innerHTML, /Synthetic recovered/);
  assert.doesNotMatch(h.results.innerHTML, /Synthetic evidence service unavailable/);
});

test('aborted sample never becomes a successful empty result', async t => {
  const h = harness(t);
  await startSample(h);
  const before = h.results.innerHTML;
  h.requests[1].reject(new DOMException('Synthetic cancellation', 'AbortError'));
  await flush();
  assert.ok(h.results.innerHTML === before, 'abort must not render empty evidence');
  assert.deepEqual(h.notices, []);
});

test('late sample response cannot overwrite a newer completed statistics request', async t => {
  const h = harness(t);
  await startSample(h);
  const retry = h.click({action: 'retry'});
  assert.equal(h.requests[1].options.signal.aborted, true);
  h.requests[2].respond(stats('Synthetic newest'));
  await flush();
  h.requests[3].respond({items: [alert(22)]});
  await retry;
  const latest = h.results.innerHTML;
  assert.match(latest, /Synthetic newest/);
  assert.match(latest, /Synthetic evidence 22/);
  h.requests[1].respond({items: [alert(11)]});
  await flush();
  assert.equal(h.results.innerHTML, latest, 'stale sample must not render or mutate evidence');
});
