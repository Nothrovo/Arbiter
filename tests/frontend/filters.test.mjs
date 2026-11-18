import test from 'node:test';
import assert from 'node:assert/strict';
import {filtersValue, normalizeFilter, parseFilters, renderFilterChips, filterBuilderHTML} from '../../app/static/js/state/filters.js';
import {queryFrom, scopeParams} from '../../app/static/js/state/scope.js';

test('filter model normalizes known fields and drops malformed chips', () => {
  const parsed = parseFilters(JSON.stringify([
    {field: 'rule.description', op: 'not_contains', value: 'mhs'},
    {field: 'rule.level', op: 'range', value: '7', value2: '12'},
    {field: 'unknown.field', op: 'is', value: 'x'},
    {field: 'data.url', op: 'glob', value: ''},
  ]));
  assert.equal(parsed.length, 2);
  assert.deepEqual(parsed[0], {field: 'rule.description', op: 'not_contains', value: 'mhs', value2: ''});
  assert.equal(parsed[1].op, 'range');
});

test('numeric fields reject text-only operators', () => {
  assert.equal(normalizeFilter({field: 'rule.level', op: 'contains', value: '7'}), null);
  assert.equal(normalizeFilter({field: 'rule.level', op: 'range', value: '7'}), null);
  assert.equal(normalizeFilter({field: 'rule.level', op: 'gte', value: '7'}).op, 'gte');
});

test('filters round-trip through the URL scope', () => {
  const filters = [
    {field: 'rule.description', op: 'not_contains', value: 'mhs', value2: ''},
    {field: 'data.srcip', op: 'is_not', value: '10.0.0.1', value2: ''},
  ];
  const params = scopeParams({tenant: 'all', review_status: 'unreviewed', filters});
  const back = queryFrom(params);
  assert.deepEqual(back.filters, filters);
  assert.equal(filtersValue(back.filters), JSON.stringify(filters));
});

test('export params keep filter chips and explicit selections drop them', () => {
  const params = scopeParams({tenant: 'acme', filters: [{field: 'rule.id', op: 'is', value: '5710'}]});
  assert.match(params.get('filters'), /5710/);
  const selected = scopeParams({tenant: 'acme', filters: [{field: 'rule.id', op: 'is', value: '5710'}]}, {ids: [3]});
  assert.equal(selected.get('filters'), null);
});

test('chip markup exposes a remove control and escapes values', () => {
  const html = renderFilterChips([{field: 'rule.description', op: 'not_contains', value: '<mhs>'}]);
  assert.match(html, /data-remove-filter="0"/);
  assert.match(html, /&lt;mhs&gt;/);
  assert.doesNotMatch(html, /<mhs>/);
});

test('filter builder offers numeric operators only for rule.level', () => {
  const html = filterBuilderHTML([], {prefix: 'triage-flt'});
  assert.match(html, /data-filter-field/);
  assert.match(html, /data-add-filter/);
  assert.match(html, /triage-flt-value/);
  assert.match(html, /matches glob/);
});
