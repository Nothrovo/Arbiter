import test from 'node:test';
import assert from 'node:assert/strict';
import {existsSync} from 'node:fs';
import {
  REVIEW_DATE_PRESETS,
  localDateInputValue,
  localDayBoundsFromDateInput,
  queryFrom,
  reviewDateLabel,
  reviewDateRangeForPreset,
  scopeDescription,
  scopeParams,
  tenantScope,
} from '../../app/static/js/state/scope.js';
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

test('review date presets and bounds compute accurate cutoffs to exclude recent days', () => {
  assert.ok(REVIEW_DATE_PRESETS.some(([k]) => k === 'exclude_1d'));
  assert.ok(REVIEW_DATE_PRESETS.some(([k]) => k === 'exclude_3d'));

  const ref = new Date(2026, 10, 20, 14, 30, 0, 0); // 2026-11-20 local
  const today = reviewDateRangeForPreset('today', ref);
  assert.equal(localDateInputValue(today.reviewed_from), '2026-11-20');
  assert.equal(localDateInputValue(today.reviewed_to), '2026-11-20');

  const noToday = reviewDateRangeForPreset('exclude_1d', ref);
  assert.equal(noToday.reviewed_from, '');
  assert.equal(localDateInputValue(noToday.reviewed_to), '2026-11-19');
  assert.ok(new Date(noToday.reviewed_to).getTime() < new Date(2026, 10, 20, 0, 0, 0, 0).getTime());

  const olderThan2d = reviewDateRangeForPreset('exclude_3d', ref);
  assert.equal(olderThan2d.reviewed_from, '');
  assert.equal(localDateInputValue(olderThan2d.reviewed_to), '2026-11-17');

  const startBound = localDayBoundsFromDateInput('2026-11-10', 'start');
  const endBound = localDayBoundsFromDateInput('2026-11-15', 'end');
  assert.equal(localDateInputValue(startBound), '2026-11-10');
  assert.equal(localDateInputValue(endBound), '2026-11-15');
  assert.equal(localDayBoundsFromDateInput('invalid', 'start'), '');

  const q = queryFrom(new URLSearchParams(`tenant=Alpha&review_status=reviewed&reviewer=analyst1&reviewed_preset=exclude_3d&reviewed_to=${encodeURIComponent(olderThan2d.reviewed_to)}`));
  assert.equal(q.reviewed_preset, 'exclude_3d');
  assert.equal(q.reviewer, 'analyst1');
  assert.match(reviewDateLabel(q), /> 2 hari lalu/);
  assert.match(scopeDescription(scopeParams(q)), /> 2 hari lalu/);
  assert.match(scopeDescription(scopeParams(q)), /Reviewer: @analyst1/);
});
