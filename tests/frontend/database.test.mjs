import test from 'node:test';
import assert from 'node:assert/strict';
import {summarizeTelemetryRange} from '../../app/static/js/features/database/model.js';
import {parseRoute} from '../../app/static/js/router.js';

test('database route parses correctly in hash router', () => {
  const route = parseRoute('#/database?tenant=sgu');
  assert.equal(route.page, 'database');
  assert.equal(route.params.get('tenant'), 'sgu');
});

test('summarizeTelemetryRange formats bounds correctly', () => {
  assert.match(summarizeTelemetryRange('2026-01-01T10:00:00Z', '2026-01-02T10:00:00Z'), /2026|01/);
  assert.equal(summarizeTelemetryRange(null, null), 'Belum ada telemetri tercatat');
});
