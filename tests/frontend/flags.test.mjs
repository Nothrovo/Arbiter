import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {
  FLAG_TABS,
  FLAG_GROUP_BY_OPTIONS,
  normalizeFlagQuery,
  flagScopeParams,
  flagExportParams,
  flagExportURL,
  flagExportFormat,
  FLAG_EXPORT_FORMATS,
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
  const html = renderFlagsPage(query, data, {
    expandedGroups: new Set(['/lib/minigalnano/createthumb.php <script>alert(1)</script>']),
    groupAlertsCache: new Map([[
      '/lib/minigalnano/createthumb.php <script>alert(1)</script>',
      {
        loading: false,
        error: '',
        total: 1,
        items: [{
          id: 101,
          alert_id: 'syn-101',
          description: 'Web server 400 error code.',
          rule_level: 7,
          flag_color: 'green',
          flagged_by: 'analis1',
          rule_status: 'done',
          custom_rule_id: '100145',
        }],
      },
    ]]),
  });
  assert.match(html, /Rule Dibuat \(#100145\)/);
  assert.match(html, /@rule_eng/);
  assert.match(html, /Kembalikan Pending/);
  assert.match(html, /Hapus Flag Grup/);
  assert.match(html, /data-action="unreview-group"/);
  assert.match(html, /<option value="">— Hapus Flag \(Unflag\) —<\/option>/);
  assert.match(html, /data-action="unflag-alert"/);
  assert.match(html, /data-action="unreview-alert"/);
  assert.doesNotMatch(html, /<script>alert\(1\)<\/script>/);
  assert.doesNotMatch(html, /<img src=x/);
  assert.doesNotMatch(html, /\bAman\b|\bClean\b|\bSafe\b/);

  // Red tab hides exclusion rule marking buttons but allows unflag & unreview
  const redQuery = normalizeFlagQuery(new URLSearchParams('tenant=Alpha&flag_color=red'));
  const redHtml = renderFlagsPage(redQuery, {
    ...data,
    groups: [{key: 'Critical RCE', alert_count: 1, event_hits: 1, rule_status: 'none'}],
  }, {});
  assert.doesNotMatch(redHtml, /Tandai Rule Dibuat/);
  assert.match(redHtml, /Tidak boleh diabaikan dengan custom rule/);
  assert.match(redHtml, /Hapus Flag Grup/);
  assert.match(redHtml, /Belum direview/);
});

test('flag exports carry the active category and selected groups', () => {
  const query = normalizeFlagQuery(new URLSearchParams('tenant=Alpha&tenant=Beta&flag_color=yellow&group_by=url_path&q=thumb'));
  const params = flagExportParams(query, ['/a.php', '/b.php']);
  assert.deepEqual(params.getAll('tenant'), ['Alpha', 'Beta']);
  assert.equal(params.get('flag_color'), 'yellow');
  assert.equal(params.get('group_by'), 'url_path');
  assert.equal(params.get('q'), 'thumb');
  assert.deepEqual(params.getAll('group_key'), ['/a.php', '/b.php']);
  assert.equal(flagExportFormat('copy-html'), 'report-html');
  assert.equal(flagExportFormat('copy-tsv'), 'tsv');
  assert.equal(flagExportURL(query, [], 'docx'), `/api/flags/export/docx?${flagExportParams(query, [])}`);
  assert.ok(FLAG_EXPORT_FORMATS.some(([key]) => key === 'xlsx'));
  assert.throws(() => flagExportFormat('exe'));
});

test('renderFlagsPage renders the Flag export bar and group selection controls', () => {
  const query = normalizeFlagQuery(new URLSearchParams('tenant=Alpha&flag_color=green'));
  const data = {
    counts: {green: {total: 1, pending: 1, done: 0}, yellow: {total: 0, pending: 0, done: 0}, red: {total: 0, pending: 0, done: 0}},
    total_alerts: 1,
    total_groups: 1,
    groups: [{
      key: 'Rule A', alert_count: 1, event_hits: 1, rule_status: 'pending',
      flagged_earliest: '2026-11-18T08:00:00Z', flagged_latest: '2026-11-18T09:00:00Z',
    }],
  };
  const html = renderFlagsPage(query, data, {
    selectedGroupKeys: new Set(['Rule A']),
    exportCount: 1,
    exportStatus: 'Siap',
  });
  assert.match(html, /Ekspor Flag/);
  assert.match(html, /1 grup dipilih/);
  assert.match(html, /1<\/strong> alert siap diekspor/);
  assert.match(html, /data-flag-export="copy-html"/);
  assert.match(html, /data-flag-export="xlsx"/);
  assert.match(html, /data-select-group-index="0" checked/);
  assert.match(html, /data-action="flag-select-all"/);
  assert.match(html, /data-action="flag-select-none"/);
  assert.match(html, /Ditandai/);
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

test('triage view replaces TP/FP/Benign buttons with Flag Hijau/Kuning/Merah and Unflag controls', () => {
  const triageView = readFileSync(new URL('../../app/static/js/features/triage/view.js', import.meta.url), 'utf8');
  assert.match(triageView, /Flag Hijau/);
  assert.match(triageView, /Flag Kuning/);
  assert.match(triageView, /Flag Merah/);
  assert.match(triageView, /data-action="batch-unflag"/);
  assert.match(triageView, /data-action="unflag-current"/);
  assert.match(triageView, /Hapus Flag/);
  assert.match(triageView, /\/api\/alerts\/flag/);
  assert.doesNotMatch(triageView, /Verdict TP|Verdict FP|Verdict Benign/);
});

test('flag workspace supports team-wide rule creation, reviewer filter, and analyst own-flag edit bounds', () => {
  const query = normalizeFlagQuery(new URLSearchParams('tenant=Alpha&flag_color=green&reviewer=analyst2&reviewed_preset=exclude_3d&reviewed_to=2026-11-17T16:59:59.999Z'));
  const params = flagScopeParams(query);
  assert.equal(params.get('reviewer'), 'analyst2');
  assert.equal(params.get('reviewed_preset'), 'exclude_3d');
  assert.equal(params.get('reviewed_to'), '2026-11-17T16:59:59.999Z');

  const expParams = flagExportParams(query, ['Rule A']);
  assert.equal(expParams.get('reviewer'), 'analyst2');
  assert.equal(expParams.get('reviewed_to'), '2026-11-17T16:59:59.999Z');

  const html = renderFlagsPage(query, {
    counts: {green: {total: 3, pending: 3, done: 0}, yellow: {total: 0, pending: 0, done: 0}, red: {total: 0, pending: 0, done: 0}},
    total_alerts: 3,
    total_groups: 2,
    groups: [
      {key: 'Rule Mixed', alert_count: 2, own_alert_count: 1, pending_count: 2, event_hits: 2, rule_status: 'pending'},
      {key: 'Rule Others', alert_count: 1, own_alert_count: 0, pending_count: 1, event_hits: 1, rule_status: 'pending'},
    ],
  }, {
    currentUser: {username: 'analyst1', role: 'analyst'},
    reviewers: [
      {username: 'analyst1', display_name: 'Analis Satu'},
      {username: 'analyst2', display_name: 'Analis Dua'},
    ],
    expandedGroups: new Set(['Rule Mixed']),
    groupAlertsCache: new Map([[
      'Rule Mixed',
      {
        loading: false,
        error: '',
        total: 2,
        items: [
          {id: 10, alert_id: 'syn-10', description: 'Own flagged', rule_level: 7, flag_color: 'green', flagged_by: 'analyst1', reviewed_by: 'analyst1', rule_status: 'pending'},
          {id: 11, alert_id: 'syn-11', description: 'Other flagged', rule_level: 7, flag_color: 'green', flagged_by: 'analyst2', reviewed_by: 'analyst2', rule_status: 'pending'},
        ],
      },
    ]]),
  });
  assert.match(html, /id="flag-review-preset"/);
  assert.match(html, /id="flag-reviewer-filter"/);
  assert.match(html, /value="analyst2" selected/);
  assert.match(html, /Filter waktu review/);
  // Mixed group shows rule button + 'Saya (1)' partial unflag buttons
  assert.match(html, /Hapus Flag Grup Saya \(1\)/);
  // Row 10 (analyst1) keeps edit controls; Row 11 (analyst2) allows Tandai Rule Dibuat but hides unflag/unreview
  assert.match(html, /data-change-alert-flag="10"/);
  assert.doesNotMatch(html, /data-change-alert-flag="11"/);
  assert.match(html, /Hanya baca flag \(milik user lain\)/);
  assert.match(html, /data-action="open-alert-rule-modal" data-alert-id="11"/);
});
