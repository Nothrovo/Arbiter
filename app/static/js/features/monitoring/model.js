import {esc, icon, formatTime, emptyState} from '../../ui/primitives.js';
import {withParams} from '../../router.js';
import {tenantValues} from '../../state/scope.js';

const ROLE_LABELS = {
  admin: 'Admin',
  director: 'Director / Lead',
  analyst: 'Analyst (L1/L2)',
};

export function renderReviewActivity(data) {
  if (!data) return '';
  const days = Array.isArray(data.days) ? data.days : [];
  const max = Math.max(1, ...days.map(day => Number(day.count) || 0));
  const today = days[0]?.date || '';
  const bars = days.slice().reverse().map(day => {
    const count = Number(day.count) || 0;
    const height = count ? Math.max(8, Math.round(count / max * 100)) : 2;
    const label = day.date === today ? 'Hari ini' : day.date.slice(8, 10) + '/' + day.date.slice(5, 7);
    return `<button type="button" class="review-bar${day.date === today ? ' is-today' : ''}${count ? '' : ' is-empty'}" data-review-day="${esc(day.date)}" title="${esc(day.date)}: ${count} alert direview" aria-label="${esc(day.date)}: ${count} alert direview">
      <span class="review-bar-track"><span class="review-bar-fill" style="height:${height}%"></span></span>
      <span class="review-bar-count num">${count || ''}</span>
      <span class="review-bar-day">${esc(label)}</span>
    </button>`;
  }).join('');
  return `<section class="review-activity" aria-label="Aktivitas review">
    <div class="review-activity-head">
      <h2>Aktivitas review</h2>
      <span class="review-activity-stats">Hari ini <strong class="num">${Number(data.today || 0).toLocaleString('id-ID')}</strong> alert · 7 hari <strong class="num">${Number(data.last_7_days || 0).toLocaleString('id-ID')}</strong> · total <strong class="num">${Number(data.total_reviewed || 0).toLocaleString('id-ID')}</strong></span>
    </div>
    <div class="review-bars" role="group" aria-label="Jumlah alert direview per hari">${bars}</div>
    <p class="meta">Klik satu hari untuk menampilkan alert yang direview pada hari itu. Tanggal mengikuti zona waktu perangkat ini.</p>
  </section>`;
}

export function renderReviewerFilter(reviewerInfo) {
  const info = reviewerInfo && typeof reviewerInfo === 'object' ? reviewerInfo : {};
  const currentUser = String(info.current_user || 'analyst');
  if (info.locked) {
    return `<section class="monitoring-reviewer-filter" aria-label="Filter reviewer">
      <div class="field">
        <span>Reviewer</span>
        <div class="badge info" data-reviewer-locked="true">Akun Saya · @${esc(currentUser)}</div>
      </div>
      <p class="meta">Akun Analis hanya dapat melihat statistik, flag, dan aktivitas review milik <strong>@${esc(currentUser)}</strong>.</p>
    </section>`;
  }
  const reviewers = Array.isArray(info.reviewers) ? info.reviewers : [];
  const selected = info.all ? 'all' : String(info.selected || currentUser || 'all');
  const options = [`<option value="all"${selected === 'all' ? ' selected' : ''}>Semua reviewer</option>`];
  const seen = new Set(['all']);
  for (const item of reviewers) {
    const username = String(item?.username || '').trim();
    if (!username || seen.has(username)) continue;
    seen.add(username);
    const label = String(item?.display_name || username);
    const suffix = username === currentUser ? ' (akun saya)' : '';
    options.push(`<option value="${esc(username)}"${selected === username ? ' selected' : ''}>${esc(label)}${esc(suffix)}</option>`);
  }
  if (selected !== 'all' && !seen.has(selected)) {
    options.push(`<option value="${esc(selected)}" selected>${esc(selected)}</option>`);
  }
  return `<section class="monitoring-reviewer-filter" aria-label="Filter reviewer">
    <label class="field" for="monitoring-reviewer">
      <span>Reviewer</span>
      <select class="select" id="monitoring-reviewer">${options.join('')}</select>
    </label>
    <p class="meta">${selected === 'all'
      ? 'Menampilkan aktivitas seluruh akun.'
      : `Menampilkan aktivitas review <strong>@${esc(selected)}</strong>${info.is_default ? ' (akun yang sedang login)' : ''}.`}</p>
  </section>`;
}

export function renderMonitoringDashboard(data, query) {
  const metrics = data?.metrics || {};
  const flags = metrics.flags || {};
  const leaderboard = Array.isArray(data?.leaderboard) ? data.leaderboard : [];
  const auditLogs = Array.isArray(data?.audit_logs) ? data.audit_logs : [];
  const num = v => Number(v || 0).toLocaleString('id-ID');

  const tenantParams = () => {
    const p = new URLSearchParams();
    for (const t of tenantValues(query)) p.append('tenant', t);
    return p;
  };
  const triageLink = (extra = {}) => {
    const p = tenantParams();
    for (const [k, v] of Object.entries(extra)) p.set(k, String(v));
    return withParams('/triage', p);
  };

  const leaderboardRows = leaderboard.length
    ? leaderboard.map((row, idx) => {
        const roleBadge = row.role === 'admin' ? 'warning' : row.role === 'director' ? 'info' : 'neutral';
        const roleText = ROLE_LABELS[row.role] || 'Analyst (L1/L2)';
        return `<tr data-analyst-row="${esc(row.username)}">
          <td class="numeric num">${idx + 1}</td>
          <td>
            <strong>${esc(row.display_name || row.username)}</strong>
            <span class="meta mono" style="margin-left:6px">@${esc(row.username)}</span>
          </td>
          <td><span class="badge ${roleBadge}">${esc(roleText)}</span></td>
          <td class="numeric num">${row.currently_claimed > 0 ? `<span class="badge warning">${num(row.currently_claimed)} aktif</span>` : '0'}</td>
          <td class="numeric num"><strong>${num(row.completed_today)}</strong></td>
          <td class="numeric num">${num(row.total_contributions)}</td>
          <td class="num"><div style="display:flex;flex-wrap:wrap;gap:6px;align-items:center;"><span class="badge flag-green">Hijau ${num(row.green_count)}</span><span class="badge flag-yellow">Kuning ${num(row.yellow_count)}</span><span class="badge flag-red">Merah ${num(row.red_count)}</span></div></td>
        </tr>`;
      }).join('')
    : `<tr><td colspan="7" class="meta" style="text-align:center;padding:var(--space-4)">Belum ada aktivitas klaim atau review analis tercatat.</td></tr>`;

  const auditRows = auditLogs.length
    ? auditLogs.map(log => {
        const isCase = !String(log.id || '').startsWith('rep-') && String(log.id || '').length === 36;
        const titleCell = isCase
          ? `<a href="${withParams('/incidents/' + encodeURIComponent(log.id), tenantParams())}"><strong>${esc(log.title)}</strong></a>`
          : `<strong>${esc(log.title)}</strong>`;
        return `<tr>
          <td>${titleCell}<div class="meta">${esc(log.tenant || 'Semua Tenant')} · ${num(log.alert_count)} bukti</div></td>
          <td><span class="mono">${esc(log.author || 'analyst')}</span></td>
          <td class="meta num">${esc(formatTime(log.created_at))}</td>
          <td><span class="badge neutral">${esc(log.export_status || 'Diterbitkan')}</span></td>
        </tr>`;
      }).join('')
    : `<tr><td colspan="4" class="meta" style="text-align:center;padding:var(--space-4)">Belum ada riwayat laporan insiden atau ekspor dokumen.</td></tr>`;

  return `
    ${renderReviewerFilter(data?.reviewer)}
    ${renderReviewActivity(data?.review_activity)}
    <section class="form-section" aria-label="Kartu Metrik Real-time">
      <div class="split">
        <div>
          <h2 class="section-heading">Metrik Operasional Real-Time</h2>
          <p class="meta">Ritme penarikan alert harian, sisa antrean lintas hari (backlog persistence), dan akumulasi flag tim SOC.</p>
        </div>
        <span class="meta">Diperbarui ${esc(formatTime(data?.checked_at))}</span>
      </div>
      <div class="detail-grid" style="margin-top:16px;grid-template-columns:repeat(auto-fit, minmax(220px, 1fr));gap:16px;">
        <div class="key-value" style="padding:16px;border:1px solid var(--border-subtle);border-radius:var(--radius-sm);">
          <dt>Total Pull Hari Ini</dt>
          <dd class="num" style="font-size:26px;font-weight:600;margin-top:4px;">${num(metrics.total_pull_today)}</dd>
          <dd class="meta">Alert masuk hari ini (rule.level ≥ 7)</dd>
        </div>
        <div class="key-value" style="padding:16px;border:1px solid var(--border-subtle);border-radius:var(--radius-sm);">
          <dt>Outstanding Backlog</dt>
          <dd class="num" style="font-size:26px;font-weight:600;margin-top:4px;color:var(--warning, inherit);">${num(metrics.outstanding_backlog)}</dd>
          <dd class="meta">Belum ditinjau dari hari sebelumnya · Total antrean: <a href="${esc(triageLink({review_status: 'unreviewed'}))}">${num(metrics.total_unreviewed)}</a></dd>
        </div>
        <div class="key-value" style="padding:16px;border:1px solid var(--border-subtle);border-radius:var(--radius-sm);">
          <dt>Global Review Count</dt>
          <dd class="num" style="font-size:26px;font-weight:600;margin-top:4px;">${num(metrics.global_review_count)}</dd>
          <dd class="meta" style="display:flex;flex-wrap:wrap;gap:6px;margin-top:6px;"><span class="badge flag-green">Hijau ${num(flags.green)}</span><span class="badge flag-yellow">Kuning ${num(flags.yellow)}</span><span class="badge flag-red">Merah ${num(flags.red)}</span></dd>
        </div>
        <div class="key-value" style="padding:16px;border:1px solid var(--border-subtle);border-radius:var(--radius-sm);">
          <dt>Klaim Aktif Saat Ini</dt>
          <dd class="num" style="font-size:26px;font-weight:600;margin-top:4px;">${num(metrics.active_claims)}</dd>
          <dd class="meta">Atomic lock aktif (auto-release 30 menit)</dd>
        </div>
      </div>
    </section>

    <section class="form-section" style="margin-top:24px;" aria-label="Leaderboard Analis">
      <div class="split">
        <div>
          <h2 class="section-heading">Leaderboard &amp; Akuntabilitas Analis</h2>
          <p class="meta">Pemantauan beban kerja aktif (sedang diklaim), penyelesaian hari ini, dan total kontribusi flag (Hijau, Kuning, Merah) per analis.</p>
        </div>
        <a class="button" href="${esc(triageLink({review_status: 'unreviewed'}))}">${icon('inbox')} Buka Antrean Backlog</a>
      </div>
      <div class="table-region" tabindex="0" style="margin-top:12px;">
        <table class="data-table">
          <thead>
            <tr>
              <th scope="col" class="numeric" style="width:48px">#</th>
              <th scope="col">Analis</th>
              <th scope="col">Role</th>
              <th scope="col" class="numeric">Sedang Diklaim</th>
              <th scope="col" class="numeric">Selesai Hari Ini</th>
              <th scope="col" class="numeric">Total Kontribusi</th>
              <th scope="col">Rincian Flag</th>
            </tr>
          </thead>
          <tbody>${leaderboardRows}</tbody>
        </table>
      </div>
    </section>

    <section class="form-section" style="margin-top:24px;" aria-label="Audit Log Laporan">
      <div class="split">
        <div>
          <h2 class="section-heading">Audit Log Laporan Insiden</h2>
          <p class="meta">Daftar seluruh laporan insiden dan dokumen ekspor yang telah diterbitkan tim SOC (Judul, Pembuat, Waktu, Status Ekspor).</p>
        </div>
        <a class="button" href="${esc(withParams('/reports', tenantParams()))}">${icon('report')} Buat Laporan Baru</a>
      </div>
      <div class="table-region" tabindex="0" style="margin-top:12px;">
        <table class="data-table">
          <thead>
            <tr>
              <th scope="col">Judul Laporan / Kasus</th>
              <th scope="col">Pembuat</th>
              <th scope="col">Waktu</th>
              <th scope="col">Status Ekspor</th>
            </tr>
          </thead>
          <tbody>${auditRows}</tbody>
        </table>
      </div>
    </section>
  `;
}
