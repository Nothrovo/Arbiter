import test from 'node:test';
import assert from 'node:assert/strict';
import {renderMonitoringDashboard} from '../../app/static/js/features/monitoring/model.js';
import {claimBadge} from '../../app/static/js/features/triage/model.js';
import {queryFrom} from '../../app/static/js/state/scope.js';

test('renderMonitoringDashboard renders real-time metric cards, analyst leaderboard, and report audit logs safely', () => {
  const html = renderMonitoringDashboard(
    {
      checked_at: '2026-11-18T10:00:00Z',
      review_activity: {
        days: [
          {date: '2026-11-18', count: 12},
          {date: '2026-11-17', count: 4},
        ],
        today: 12,
        last_7_days: 16,
        total_reviewed: 342,
      },
      metrics: {
        total_pull_today: 1450,
        outstanding_backlog: 98550,
        total_unreviewed: 100000,
        global_review_count: 3420,
        active_claims: 4,
        flags: {green: 3100, yellow: 200, red: 120},
        verdicts: {tp: 120, fp: 3100, benign: 200},
      },
      leaderboard: [
        {
          username: 'analis1',
          display_name: 'Analis Satu <script>alert(1)</script>',
          role: 'analyst',
          currently_claimed: 2,
          completed_today: 85,
          total_contributions: 1240,
          green_count: 1100,
          yellow_count: 100,
          red_count: 40,
        },
        {
          username: 'lead_csirt',
          display_name: 'Kasubag CSIRT',
          role: 'director',
          currently_claimed: 0,
          completed_today: 12,
          total_contributions: 530,
          green_count: 480,
          yellow_count: 25,
          red_count: 25,
        },
      ],
      audit_logs: [
        {
          id: 'rep-1',
          title: 'Laporan Insiden Web Probe <img src=x onerror=alert(1)>',
          author: 'analis1',
          created_at: '2026-11-18T09:30:00Z',
          export_status: 'Diekspor (Word .docx)',
          tenant: 'Alpha',
          alert_count: 45,
        },
      ],
    },
    queryFrom(new URLSearchParams('tenant=Alpha')),
  );

  assert.match(html, /Total Pull Hari Ini/);
  assert.match(html, /Aktivitas review/);
  assert.match(html, /data-review-day="2026-11-18"/);
  assert.match(html, /Hari ini <strong class="num">12<\/strong> alert/);
  assert.match(html, /Outstanding Backlog/);
  assert.match(html, /Global Review Count/);
  assert.match(html, /Hijau 3\.100/);
  assert.match(html, /Kuning 200/);
  assert.match(html, /Merah 120/);
  assert.match(html, /Rincian Flag/);
  assert.match(html, /badge flag-green">Hijau 1\.100/);
  assert.match(html, /badge flag-yellow">Kuning 100/);
  assert.match(html, /badge flag-red">Merah 40/);
  assert.doesNotMatch(html, /Rincian Verdict/);
  assert.doesNotMatch(html, /TP 40/);
  assert.doesNotMatch(html, /Benign 100/);
  assert.match(html, /Leaderboard &amp; Akuntabilitas Analis/);
  assert.match(html, /Audit Log Laporan Insiden/);
  assert.match(html, /Director \/ Lead/);
  assert.match(html, /Diekspor \(Word \.docx\)/);
  assert.doesNotMatch(html, /<script>alert\(1\)<\/script>/);
  assert.doesNotMatch(html, /<img src=x/);
});

test('claimBadge renders active claim owner, timeout state, and final verdict badges', () => {
  const claimed = claimBadge({
    is_reviewed: false,
    status: 'claimed',
    claimed_by: 'analis_soc',
  });
  assert.match(claimed, /Diklaim @analis_soc/);

  const expired = claimBadge({
    is_reviewed: false,
    status: 'claimed_expired',
  });
  assert.match(expired, /Bebas diklaim \(timeout\)/);

  const reviewedTp = claimBadge({
    is_reviewed: true,
    verdict: 'tp',
    reviewed_by: 'analis_soc',
    reviewed_at: '2026-11-18T10:00:00Z',
  });
  assert.match(reviewedTp, />TP</);
  assert.match(reviewedTp, /Direview oleh @analis_soc/);
});
