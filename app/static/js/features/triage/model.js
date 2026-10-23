import {esc, icon, severity, formatTime} from '../../ui/primitives.js';
export function intelSummary(alert) {
  if (!alert.source_ip) return 'Tanpa source IP';
  if (alert.abuse_score === null || alert.abuse_score === undefined) return 'Belum ada cache';
  if (Number(alert.abuse_score) === 0 && !Number(alert.vt_malicious)) return 'Tidak ada deteksi di cache';
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
    return '<span class="score-badge score-zero">Tidak ada deteksi di cache</span>';
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
