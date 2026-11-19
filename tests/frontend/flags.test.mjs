import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {
  FLAG_TABS,
  FLAG_GROUP_BY_OPTIONS,
  normalizeFlagQuery,
  flagScopeParams,
  flagBadge,
  ruleStatusBadge,
} from '../../app/static/js/features/flags/model.js';
import {renderFlagsPage} from '../../app/static/js/features/flags/render.js';
import {claimBadge} from '../../app/static/js/features/triage/model.js';

test('normalizeFlagQuery defaults to green pending rule_description and locks red to all', () => {
  const def = normalizeFlagQuery(new URLSearchParams('tenant=Alpha'));
  assert.equal(def.flag_color, 'green');
  assert.equal(def.rule_status, 'pending');
  assert.equal(def.group_by, 'rule_description');

  const red = normalizeFlagQuery(new URLSearchParams('tenant=Alpha&flag_color=red&rule_status=pending'));
  assert.equal(red.flag_color, 'red');
  assert.equal(red.rule_status, 'all');

  const params = flagScopeParams(def);
  assert.deepEqual(params.getAll('tenant'), ['Alpha']);
  assert.equal(params.get('flag_color'), 'green');
  assert.equal(params.get('rule_status'), 'pending');
});

test('FLAG_GROUP_BY_OPTIONS exposes all 12 PRD dimensions without Aman/Clean/Safe labels', () => {
  assert.equal(FLAG_GROUP_BY_OPTIONS.length, 12);
  const keys = FLAG_GROUP_BY_OPTIONS.map(([k]) => k);
  for (const required of [
    'rule_description', 'rule_id', 'severity', 'source_ip', 'agent',
    'http_status', 'http_method', 'url_path', 'referer', 'user_agent',
    'pattern', 'tenant',
  ]) {
    assert.ok(keys.includes(required), `missing ${required}`);
  }
  for (const tab of FLAG_TABS) {
    assert.doesNotMatch(tab.title + ' ' + tab.description, /\bClean\b|\bSafe\b|\bAman\b/i);
  }
});

test('renderFlagsPage renders counts, done badges with audit info, escapes XSS, and disables tuning on Red tab', () => {
  const query = normalizeFlagQuery(new URLSearchParams('tenant=Alpha&flag_color=green&rule_status=done'));
  const data = {
    counts: {
      green: {total: 5, pending: 2, done: 3},
      yellow: {total: 1, pending: 1, done: 0},
      red: {total: 4, pending: 0, done: 0},
    },
    pending_tuning: 3,
    total_alerts: 3,
    total_groups: 1,
    groups: [{
      key: '/lib/minigalnano/createthumb.php <script>alert(1)</script>',
      alert_count: 3,
      event_hits: 9,
      pending_count: 0,
      done_count: 3,
      rule_status: 'done',
      earliest: '2026-11-18T10:00:00Z',
      latest: '2026-11-18T12:00:00Z',
      custom_rule_id: '100145',
      rule_notes: 'Whitelist crawler <img src=x onerror=alert(1)>',
      rule_updated_by: 'rule_eng',
      rule_updated_at: '2026-11-18T13:00:00Z',
    }],
  };
  const html = renderFlagsPage(query, data, {});
  assert.match(html, /Rule Dibuat \(#100145\)/);
  assert.match(html, /@rule_eng/);
  assert.match(html, /Kembalikan Pending/);
  assert.doesNotMatch(html, /<script>alert\(1\)<\/script>/);
  assert.doesNotMatch(html, /<img src=x/);
  assert.doesNotMatch(html, /\bAman\b|\bClean\b|\bSafe\b/);

  // Red tab hides exclusion rule marking buttons
  const redQuery = normalizeFlagQuery(new URLSearchParams('tenant=Alpha&flag_color=red'));
  const redHtml = renderFlagsPage(redQuery, {
    ...data,
    groups: [{key: 'Critical RCE', alert_count: 1, event_hits: 1, rule_status: 'none'}],
  }, {});
  assert.doesNotMatch(redHtml, /Tandai Rule Dibuat/);
  assert.match(redHtml, /Tidak boleh diabaikan dengan custom rule/);
});

test('claimBadge prioritizes Flag badge with Rule Dibuat status and retains legacy TP fallback', () => {
  const flagged = claimBadge({
    is_reviewed: true,
    flag_color: 'green',
    rule_status: 'done',
    custom_rule_id: '100145',
    reviewed_by: 'analis1',
    reviewed_at: '2026-11-18T10:00:00Z',
  });
  assert.match(flagged, /flag-green/);
  assert.match(flagged, /Hijau/);
  assert.match(flagged, /Rule #100145/);

  const legacyTp = claimBadge({is_reviewed: true, verdict: 'tp', reviewed_by: 'analis2'});
  assert.match(legacyTp, />TP</);
  assert.match(flagBadge('yellow'), /Flag Kuning/);
  assert.match(ruleStatusBadge({flag_color: 'green', rule_status: 'pending'}), /Belum Dibuat Rule/);
  assert.equal(ruleStatusBadge({flag_color: 'red', rule_status: 'pending'}), '');
});

test('triage view replaces TP/FP/Benign buttons with Flag Hijau/Kuning/Merah controls', () => {
  const triageView = readFileSync(new URL('../../app/static/js/features/triage/view.js', import.meta.url), 'utf8');
  assert.match(triageView, /Flag Hijau/);
  assert.match(triageView, /Flag Kuning/);
  assert.match(triageView, /Flag Merah/);
  assert.match(triageView, /\/api\/alerts\/flag/);
  assert.doesNotMatch(triageView, /Verdict TP|Verdict FP|Verdict Benign/);
});
