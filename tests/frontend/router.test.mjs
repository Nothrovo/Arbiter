import test from 'node:test';
import assert from 'node:assert/strict';
import {existsSync} from 'node:fs';
const url = new URL('../../app/static/js/router.js', import.meta.url);
test('hash router preserves query and case identity and identifies unknown destinations', async () => {
  assert.ok(existsSync(url), 'modular router must exist');
  const {parseRoute, withParams} = await import(url);
  const route = parseRoute('#/incidents/synthetic-case?tenant=lab');
  assert.equal(route.path, '/incidents/synthetic-case');
  assert.equal(route.page, 'incidents');
  assert.equal(route.params.get('tenant'), 'lab');
  assert.equal(parseRoute('').path, '/triage');
  assert.equal(parseRoute('#/unknown').page, 'not-found');
  assert.equal(withParams('/triage', new URLSearchParams('tenant=lab')), '#/triage?tenant=lab');
});
