import {esc, icon} from '../../ui/primitives.js';
import {scopeDescription} from '../../state/scope.js';

export function reportPage(scope) {
  const type = scope.has('alert_ids') ? 'Alert terpilih' : scope.has('group_id') ? 'Insiden dan filter' : 'Query Triage';
  return `<header class="page-header"><div><h1 class="page-heading">Laporan</h1><p class="page-description">Tinjau dokumen dan ekspor scope bukti yang sama.</p></div><div class="page-actions"><details class="format-menu"><summary class="button">Ekspor ${icon('down')}</summary><div class="stack" aria-label="Format laporan">
    ${[['copy-html', 'Salin untuk Google Docs'], ['report-html', 'Unduh HTML'], ['docx', 'Unduh DOCX'], ['xlsx', 'Unduh XLSX'], ['tsv', 'Unduh TSV'], ['copy-tsv', 'Salin TSV'], ['markdown', 'Unduh Markdown'], ['copy-markdown', 'Salin Markdown'], ['csv', 'Unduh CSV']].map(([format, label]) => `<button class="button" type="button" data-export="${format}" disabled>${label}</button>`).join('')}
    </div></details></div></header>
    <div class="report-layout"><aside class="context-panel stack" aria-labelledby="report-scope-heading"><h2 id="report-scope-heading" class="section-heading">Scope laporan</h2><p><strong>${type}</strong></p><p>${esc(scopeDescription(scope))}</p>
    ${scope.has('group_id') ? `<p class="meta">ID insiden: <span class="mono">${esc(scope.get('group_id'))}</span></p>` : ''}
    ${scope.has('alert_ids') ? `<details><summary>ID alert terpilih</summary><p class="mono">${esc(scope.get('alert_ids'))}</p></details>` : ''}
    <p class="meta">Urutan: ${esc(scope.get('sort_by'))}, ${esc(scope.get('sort'))}. Seluruh hasil dalam scope; tidak mengikuti pagination Triage.</p>
    <p id="report-count" class="inline-status" aria-live="polite">Menghitung alert dari server…</p>
    <div class="field"><label for="report-group">Ganti ke scope insiden</label><select id="report-group" class="select" disabled><option value="">Memuat insiden…</option></select><p class="meta">Mengganti insiden mempertahankan tenant; filter pencarian dan pilihan alert dilepas.</p></div><p id="report-groups-status" class="inline-status" role="status"></p>
    <button type="button" class="button" data-action="refresh-preview">${icon('refresh')} Muat ulang preview</button>
    <p class="meta">Google Docs menggunakan clipboard HTML, bukan integrasi akun. Tinjau data sensitif sebelum membagikan laporan. Preview dan unduhan membaca scope yang sama; isi dapat berubah bila data diperbarui di antaranya.</p>
    </aside><section id="report-document" class="report-preview" aria-label="Preview dokumen" aria-live="polite" aria-busy="true"><p class="inline-status">Memuat preview dokumen…</p></section></div>
    <p id="report-action-status" class="inline-status" aria-live="polite"></p><div id="report-fallback" class="panel stack" hidden></div>`;
}

export function sandboxDocument(html) {
  return `<!doctype html><html><head><meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'none'; style-src 'unsafe-inline'; img-src data:; base-uri 'none'; form-action 'none'"></head><body>${html}</body></html>`;
}

export function reportPreview(preview) {
  return `<div class="report-document-header"><h2 class="section-heading">${esc(preview.meta.title || 'Preview laporan')}</h2><p class="meta">${esc(preview.count)} alert · Dokumen lengkap, tidak terpotong</p></div><iframe class="report-frame" title="Preview dokumen laporan" sandbox="" referrerpolicy="no-referrer" srcdoc="${esc(sandboxDocument(preview.html))}"></iframe>`;
}

export function groupOptions(groups, selected = '') {
  const missing = selected && !groups.some(group => group.id === selected);
  return `<option value="">Pilih insiden…</option>${missing ? `<option value="${esc(selected)}" selected>Insiden saat ini (${esc(selected)})</option>` : ''}${groups.map(group => `<option value="${esc(group.id)}"${group.id === selected ? ' selected' : ''}>${esc(group.title || group.id)}${Number.isSafeInteger(group.alert_count) ? ` (${group.alert_count} alert)` : ''}</option>`).join('')}`;
}

export function reportFallback(fallback) {
  return `<h2 class="section-heading">Salin tidak berhasil</h2><p>Clipboard tidak tersedia atau ditolak. Buka atau unduh format yang sama dengan scope laporan ini; tidak ada perluasan scope.</p><div class="page-actions"><a class="button" href="${esc(fallback.url)}" target="_blank" rel="noopener noreferrer">Buka dokumen</a><button class="button" type="button" data-export="${esc(fallback.format)}">Unduh ${esc(fallback.format === 'report-html' ? 'HTML' : fallback.format.toUpperCase())}</button></div>`;
}
