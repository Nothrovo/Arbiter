import {esc, icon, formatTime, emptyState} from '../../ui/primitives.js';
import {withParams} from '../../router.js';
import {tenantValues} from '../../state/scope.js';

const ROLE_LABELS = {
  admin: 'Admin',
  director: 'Director / Lead',
  analyst: 'Analyst (L1/L2)',
};

export function renderMonitoringDashboard(data, query) {
  const metrics = data?.metrics || {};
  const verdicts = metrics.verdicts || {};
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
          <td class="meta num">TP ${num(row.tp_count)} · FP ${num(row.fp_count)} · Benign ${num(row.benign_count)}</td>
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
    <section class="form-section" aria-label="Kartu Metrik Real-time">
      <div class="split">
        <div>
          <h2 class="section-heading">Metrik Operasional Real-Time</h2>
          <p class="meta">Ritme penarikan alert harian, sisa antrean lintas hari (backlog persistence), dan akumulasi verdict tim SOC.</p>
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
          <dd class="meta">TP ${num(verdicts.tp)} · FP ${num(verdicts.fp)} · Benign ${num(verdicts.benign)}</dd>
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
          <p class="meta">Pemantauan beban kerja aktif (sedang diklaim), penyelesaian hari ini, dan total kontribusi verdict per analis.</p>
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
              <th scope="col">Rincian Verdict</th>
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
