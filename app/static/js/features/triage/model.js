import {esc, icon, severity, formatTime} from '../../ui/primitives.js';
import {tenantValues} from '../../state/scope.js';
import {withParams} from '../../router.js';

export function summaryRequestParams(query) {
  const p = new URLSearchParams();
  for (const t of tenantValues(query)) p.append('tenant', t);
  if (query.q) p.set('q', query.q);
  if (query.filter_preset) p.set('filter_preset', query.filter_preset);
  if (query.status && query.status !== 'all') p.set('status', query.status);
  if (query.group_id) p.set('group_id', query.group_id);
  if (query.review_status && query.review_status !== 'all') p.set('review_status', query.review_status);
  if (query.time_preset) p.set('time_preset', query.time_preset);
  if (query.secondary_facet && query.secondary_facet_value) {
    p.set('secondary_facet', query.secondary_facet);
    p.set('secondary_facet_value', query.secondary_facet_value);
  }
  if (query.time_from) p.set('time_from', query.time_from);
  if (query.time_to) p.set('time_to', query.time_to);
  if (query.facet && query.facet_value) {
    p.set('facet', query.facet);
    p.set('facet_value', query.facet_value);
  }
  return p;
}

export function renderTriageSummary(data, query, {collapsed = false} = {}) {
  if (!data) return '';
  const statsParams = summaryRequestParams(query);
  const statsUrl = withParams('/stats', statsParams);

  if (collapsed) {
    return `
      <section class="triage-summary-strip is-collapsed" aria-label="Ringkasan antrean triage">
        <div class="summary-collapsed-bar" style="display:flex; align-items:center; justify-content:space-between; gap:12px; padding:6px 12px; font-size:12px; background:var(--surface); border:1px solid var(--border); border-radius:var(--radius-control); margin-bottom:12px;">
          <span><strong>${data.alerts.toLocaleString('id-ID')}</strong> alert (${data.events.toLocaleString('id-ID')} hits) dalam filter aktif</span>
          <div style="display:flex; align-items:center; gap:8px;">
            <a class="text-button" href="${statsUrl}">Lihat statistik lengkap →</a>
            <button class="button icon-button" type="button" data-action="toggle-summary" aria-label="Buka ringkasan">${icon('down')}</button>
          </div>
        </div>
      </section>
    `;
  }

  const sev = data.severity || {critical: 0, high: 0, medium: 0, low: 0};
  const topRule = data.top_rule;
  const timeEarliest = data.time_range?.earliest ? formatTime(data.time_range.earliest) : '—';
  const timeLatest = data.time_range?.latest ? formatTime(data.time_range.latest) : 'kini';

  return `
    <section class="triage-summary-strip" aria-label="Ringkasan hasil filter antrean">
      <div class="summary-strip-inner" style="display:flex; flex-wrap:wrap; align-items:center; justify-content:space-between; gap:12px; padding:10px 14px; background:var(--surface); border:1px solid var(--border); border-radius:var(--radius-control); margin-bottom:12px; font-size:12px;">
        <div class="summary-metrics" style="display:flex; flex-wrap:wrap; align-items:center; gap:16px;">
          <div class="summary-item">
            <span class="meta">Alert:</span> <strong class="num">${data.alerts.toLocaleString('id-ID')}</strong>
            <span class="meta">(${data.events.toLocaleString('id-ID')} hits)</span>
          </div>
          <div class="summary-item">
            <button type="button" class="text-button" data-summary-action="pivot-ip" title="Pivot IP di statistik">
              <span class="meta">Source IP:</span> <strong class="num">${data.unique_source_ips}</strong>
            </button>
          </div>
          <div class="summary-item">
            <button type="button" class="text-button" data-summary-action="pivot-agent" title="Pivot Host di statistik">
              <span class="meta">Host:</span> <strong class="num">${data.unique_agents}</strong>
            </button>
          </div>
          <div class="summary-item severity-mini-group" style="display:flex; align-items:center; gap:6px;">
            <span class="meta">Severity:</span>
            <button type="button" class="badge critical text-button" data-summary-action="severity" data-severity="critical" title="Saring Severity Critical">${sev.critical}</button>
            <button type="button" class="badge high text-button" data-summary-action="severity" data-severity="high" title="Saring Severity High">${sev.high}</button>
            <button type="button" class="badge medium text-button" data-summary-action="severity" data-severity="medium" title="Saring Severity Medium">${sev.medium}</button>
            <button type="button" class="badge low text-button" data-summary-action="severity" data-severity="low" title="Saring Severity Low">${sev.low}</button>
          </div>
          <div class="summary-item">
            <button type="button" class="text-button" data-summary-action="grouped" title="Saring alert yang sudah masuk insiden">
              <span class="meta">Insiden:</span> <strong>${data.incident_cases}</strong> kasus
            </button>
          </div>
          ${topRule ? `
            <div class="summary-item top-rule-item">
              <button type="button" class="text-button" data-summary-action="top-rule" data-rule-id="${esc(topRule.rule_id)}" title="Saring Rule ${esc(topRule.rule_id)}">
                <span class="meta">Top Rule:</span> <strong>${esc(topRule.description)}</strong> (${topRule.count})
              </button>
            </div>
          ` : ''}
          <div class="summary-item time-range-item meta">
            <span>Rentang: ${timeEarliest} s/d ${timeLatest}</span>
          </div>
        </div>
        <div class="summary-actions" style="display:flex; align-items:center; gap:10px; margin-left:auto;">
          <a class="button text-button primary" href="${statsUrl}" style="white-space:nowrap;">Lihat statistik lengkap →</a>
          <button class="button icon-button" type="button" data-action="toggle-summary" aria-label="Sembunyikan ringkasan">${icon('close')}</button>
        </div>
      </div>
    </section>
  `;
}
export function intelSummary(alert) {
  if (!alert.source_ip) return 'Tanpa source IP';
  if (alert.abuse_score === null || alert.abuse_score === undefined) return 'Belum ada cache';
  if (Number(alert.abuse_score) === 0 && !Number(alert.vt_malicious)) return '0% Low risk';
  return `Abuse ${Number(alert.abuse_score)}%${Number(alert.vt_malicious) ? ` · VT ${Number(alert.vt_malicious)}` : ''}`;
}

export function intelBadge(alert) {
  if (!alert.source_ip) return '<span class="meta">Tanpa source IP</span>';
  if (alert.abuse_score === null || alert.abuse_score === undefined) {
    return '<span class="score-badge score-none">Belum ada cache</span>';
  }
  const score = Number(alert.abuse_score);
  const vt = Number(alert.vt_malicious) || 0;
  if (score === 0 && vt === 0) {
    return '<span class="score-badge score-zero" title="Skor Abuse 0% (Low risk)">0% Low risk</span>';
  }
  const cls = score >= 75 ? 'score-high' : score >= 25 ? 'score-med' : 'score-low';
  return `<span class="score-badge ${cls}">Abuse ${score}%${vt ? ` · VT ${vt}` : ''}</span>`;
}
export function renderQueue(items, {selectedIds = [], activeId, query, showIntel = true, showAllLogs = false, expandedLogIds = new Set(), wrapLog = true} = {}) {
  const selected = new Set(selectedIds);
  const sort = (key, label, className = '') => `<th class="${className}"${query.sort_by === key ? ` aria-sort="${query.sort === 'asc' ? 'ascending' : 'descending'}"` : ''}><button class="sort-button" data-sort="${key}" aria-pressed="${query.sort_by === key}">${label}${query.sort_by === key ? (query.sort === 'asc' ? ' ↑' : ' ↓') : ''}</button></th>`;
  const select = a => `<label class="checkbox-label"><input type="checkbox" data-select="${Number(a.id)}" aria-label="Pilih alert ${esc(a.alert_id || a.id)}" ${selected.has(a.id) ? 'checked' : ''}></label>`;
  const details = a => `${query.tenant === 'all' ? `${esc(a.tenant || 'Default')} · ` : ''}${esc(a.agent_name || 'Asset tidak diketahui')} · Rule ${esc(a.rule_id || '—')}`;
  const reviewed = a => `<span class="meta">${a.is_reviewed ? 'Direview' : 'Belum direview'}</span>`;
  const rows = items.map(a => {
    const isExpanded = showAllLogs || (expandedLogIds && expandedLogIds.has(a.id));
    const mainRow = `<tr data-row="${Number(a.id)}" aria-selected="${selected.has(a.id)}" class="${Number(activeId) === a.id ? 'inspected' : ''}"><td>${select(a)}</td><td><time datetime="${esc(a.timestamp || '')}" class="meta num">${esc(formatTime(a.timestamp))}</time></td><td>${severity(a.rule_level)}</td><td class="event-cell"><button class="event-title" data-inspect="${Number(a.id)}">${esc(a.description || 'Alert tanpa deskripsi')}</button><div class="event-sub">${details(a)} <button class="text-button meta" data-action="toggle-row-log" data-alert-id="${Number(a.id)}" type="button" style="margin-left:6px; cursor:pointer;" title="Buka/tutup full log alert">[${isExpanded ? 'Tutup Log' : 'Log'}]</button></div></td>${showIntel ? `<td><span class="mono">${esc(a.source_ip || '—')}</span><div style="margin-top:2px;">${intelBadge(a)}</div></td>` : ''}<td class="numeric">${Number(a.hit_count) || 1}</td><td>${reviewed(a)}</td></tr>`;
    const logRow = isExpanded ? `<tr class="log-expansion-row" data-log-for="${Number(a.id)}"><td colspan="${showIntel ? 7 : 6}" class="log-expansion-cell"><div class="queue-log-box stack"><div class="split queue-log-head"><span class="meta mono">Log Alert #${esc(a.alert_id || a.id)} · ${esc(a.agent_name || '—')} · Rule ${esc(a.rule_id || '—')}</span><div class="queue-log-actions" style="display:flex; gap:6px;"><button class="button text-button meta" type="button" data-action="copy-queue-log" data-alert-id="${a.id}">${icon('copy')} Salin</button><button class="button text-button meta" type="button" data-action="copy-queue-redacted" data-alert-id="${a.id}">Tersamarkan</button><button class="button text-button meta" type="button" data-action="copy-queue-defanged" data-alert-id="${a.id}">Defang</button></div></div><pre class="raw-log ${wrapLog ? '' : 'no-wrap'}">${esc(a.full_log || a.raw?.full_log || 'Log tidak tersedia atau memuat…')}</pre></div></td></tr>` : '';
    return mainRow + logRow;
  }).join('');
  const mobile = items.map(a => {
    const isExpanded = showAllLogs || (expandedLogIds && expandedLogIds.has(a.id));
    const logBox = isExpanded ? `<div class="queue-log-box stack" style="margin-top:10px;"><div class="split queue-log-head"><span class="meta mono">Log Alert #${esc(a.alert_id || a.id)}</span><div style="display:flex; gap:6px;"><button class="button text-button meta" type="button" data-action="copy-queue-log" data-alert-id="${a.id}">${icon('copy')} Salin</button><button class="button text-button meta" type="button" data-action="copy-queue-redacted" data-alert-id="${a.id}">Tersamarkan</button></div></div><pre class="raw-log ${wrapLog ? '' : 'no-wrap'}">${esc(a.full_log || a.raw?.full_log || 'Log tidak tersedia')}</pre></div>` : '';
    return `<article class="mobile-alert ${selected.has(a.id) ? 'is-selected' : ''}" data-row="${a.id}">${select(a)}<div>${severity(a.rule_level)}<button class="event-title" data-inspect="${a.id}">${esc(a.description || 'Alert tanpa deskripsi')}</button><div class="event-sub">${details(a)}</div><div class="meta mono" style="display:flex; align-items:center; gap:6px; flex-wrap:wrap;"><span>${esc(a.source_ip || 'Tanpa source IP')}</span>${intelBadge(a)}</div><div class="meta">${esc(formatTime(a.timestamp))} · ${a.is_reviewed ? 'Direview' : 'Belum direview'} <button class="text-button meta" data-action="toggle-row-log" data-alert-id="${a.id}" type="button" style="margin-left:6px;">[${isExpanded ? 'Tutup Log' : 'Log'}]</button></div>${logBox}</div><div class="alert-count">${Number(a.hit_count) || 1} hits</div></article>`;
  }).join('');
  return `<div class="table-region desktop-alerts" tabindex="0" aria-label="Antrean alert"><table class="data-table"><thead><tr><th class="select-col"><label class="checkbox-label"><input type="checkbox" data-select-page aria-label="Pilih semua alert di halaman ini"></label></th>${sort('timestamp','Waktu','time-col')}${sort('severity','Severity','severity-col')}<th>Event / asset</th>${showIntel ? '<th class="source-col">Source / intel</th>' : ''}${sort('hits','Hits','hits-col numeric')}<th class="review-col">Review</th></tr></thead><tbody>${rows}</tbody></table></div><div class="mobile-alerts" aria-label="Antrean alert mobile"><label class="checkbox-label"><input type="checkbox" data-select-page aria-label="Pilih semua alert di halaman ini">Pilih halaman ini</label>${mobile}</div>`;
}
