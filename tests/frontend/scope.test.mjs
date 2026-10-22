import test from 'node:test';
import assert from 'node:assert/strict';
import {existsSync} from 'node:fs';
import {queryFrom, scopeParams} from '../../app/static/js/state/scope.js';
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
