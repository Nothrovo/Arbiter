import test from 'node:test';
import assert from 'node:assert/strict';
import {existsSync} from 'node:fs';
const url = new URL('../../app/static/js/api/client.js', import.meta.url);
test('API client fails closed on HTTP errors and refuses cross-origin requests', async () => {
  assert.ok(existsSync(url), 'shared API client must exist');
  const {json, request, apiURL} = await import(url);
  const original = globalThis.fetch;
  globalThis.fetch = async () => new Response(JSON.stringify({detail: 'Synthetic request denied'}), {status: 403});
  try {
    await assert.rejects(json('/api/groups'), /Synthetic request denied/);
    await assert.rejects(request('https://outside.invalid/data'), /lokal|origin/i);
    assert.equal(apiURL('/api/alerts', {tenant: 'lab', q: 'space value'}), '/api/alerts?tenant=lab&q=space+value');
    assert.equal(apiURL('/api/alerts', {tenant: ['Beta', 'Alpha'], q: 'space value'}), '/api/alerts?tenant=Beta&tenant=Alpha&q=space+value');
  } finally { globalThis.fetch = original; }
});
