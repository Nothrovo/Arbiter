import test from 'node:test';
import assert from 'node:assert/strict';
import {existsSync} from 'node:fs';
import {queryFrom, scopeParams, tenantScope} from '../../app/static/js/state/scope.js';
const moduleURL = new URL('../../app/static/js/state/scope.js', import.meta.url);

test('query scope normalizes filters and exports the same working set without paging', async () => {
  assert.ok(existsSync(moduleURL), 'shared scope module must exist');
  const {queryFrom, scopeParams} = await import(moduleURL);
  const q = queryFrom(new URLSearchParams('tenant=synthetic-lab&q=probe&review_status=unreviewed&filter_preset=403&sort_by=hits&sort=asc&limit=50&offset=100'));
  const result = scopeParams(q);
  assert.equal(result.get('tenant'), 'synthetic-lab');
  assert.equal(result.get('q'), 'probe');
  assert.equal(result.get('review_status'), 'unreviewed');
  assert.equal(result.get('filter_preset'), '403');
  assert.equal(result.get('sort_by'), 'hits');
  assert.equal(result.get('sort'), 'asc');
  assert.equal(result.has('limit'), false);
  assert.equal(result.has('offset'), false);
});

test('case scope includes reviewed evidence and rejects invalid selected IDs', () => {
  const result = scopeParams(queryFrom(new URLSearchParams('tenant=synthetic-lab')), {groupId: 'synthetic-case'});
  assert.equal(result.get('review_status'), 'all');
  assert.equal(result.get('group_id'), 'synthetic-case');
  assert.throws(() => scopeParams({tenant: 'synthetic-lab'}, {ids: [-1, 'invalid']}), /pilihan|valid/i);
});

test('tenant scope canonicalizes repeated named tenants without broadening', () => {
  const scope = tenantScope(new URLSearchParams('tenant=Beta&tenant=Alpha&tenant=Beta'));
  assert.deepEqual(scope, {all: false, tenants: ['Alpha', 'Beta'], key: JSON.stringify(['Alpha', 'Beta']), label: '2 tenant'});
  const query = queryFrom(new URLSearchParams('tenant=Beta&tenant=Alpha&q=probe'));
  assert.deepEqual(query.tenants, ['Alpha', 'Beta']);
  const params = scopeParams(query);
  assert.deepEqual(params.getAll('tenant'), ['Alpha', 'Beta']);
  assert.equal(params.get('q'), 'probe');
  assert.throws(() => tenantScope(new URLSearchParams('tenant=all&tenant=Alpha')), /tenant/i);
  assert.throws(() => tenantScope(new URLSearchParams('tenant=%20')), /tenant/i);
});

test('tenant scope keys distinguish tenant names containing the key delimiter', () => {
  const first = tenantScope(new URLSearchParams('tenant=A%7CB&tenant=C'));
  const second = tenantScope(new URLSearchParams('tenant=A&tenant=B%7CC'));
  assert.notEqual(first.key, second.key);
});
