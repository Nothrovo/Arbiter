import test from 'node:test';
import assert from 'node:assert/strict';
import {existsSync} from 'node:fs';
import {tenantScope} from '../../app/static/js/state/scope.js';
const url = new URL('../../app/static/js/state/selection.js', import.meta.url);
test('selection survives rerender and refuses silent tenant changes', async () => {
  assert.ok(existsSync(url), 'selection state module must exist');
  const {createSelection} = await import(url);
  const selected = createSelection('synthetic-lab');
  selected.toggle(12, true);
  selected.toggle(15, true);
  assert.deepEqual(selected.ids(), [12, 15]);
  assert.equal(selected.setScope('other-lab'), false);
  assert.equal(selected.scope(), 'synthetic-lab');
  assert.equal(selected.setScope('other-lab', true), true);
  assert.equal(selected.size(), 0);
  selected.selectRange([1, 2, 3, 4], 1, 3, true);
  assert.deepEqual(selected.ids(), [1, 2, 3]);
  selected.toggle(2, false);
  assert.deepEqual(selected.ids(), [1, 3]);
});

test('selection uses a canonical tenant-set key and requires force to narrow it', async () => {
  const {createSelection} = await import(url);
  const both = tenantScope(new URLSearchParams('tenant=Alpha&tenant=Beta')).key;
  const alpha = tenantScope(new URLSearchParams('tenant=Alpha')).key;
  const selected = createSelection(both);
  selected.toggle(12, true);
  assert.equal(selected.setScope(alpha), false);
  assert.equal(selected.scope(), both);
  assert.equal(selected.setScope(alpha, true), true);
  assert.equal(selected.scope(), alpha);
  assert.equal(selected.size(), 0);
});

test('selection does not share state between delimiter-colliding tenant-set keys', async () => {
  const {createSelection} = await import(url);
  const first = tenantScope(new URLSearchParams('tenant=A%7CB&tenant=C'));
  const second = tenantScope(new URLSearchParams('tenant=A&tenant=B%7CC'));
  assert.notEqual(first.key, second.key);
  const selected = createSelection(first.key);
  selected.toggle(12, true);
  assert.equal(selected.setScope(second.key), false);
  assert.equal(selected.scope(), first.key);
  assert.deepEqual(selected.ids(), [12]);
});
