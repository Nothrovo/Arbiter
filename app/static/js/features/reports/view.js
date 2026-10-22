import {json, request, download, copyText, copyHTML, apiURL} from '../../api/client.js';
import {esc, errorState, emptyState} from '../../ui/primitives.js';
import {reportScope, caseReportRoute, createReportSession, reportAction} from './model.js';
import {reportPage, reportPreview, reportFallback, groupOptions} from './render.js';

export function mount(ctx) {
  const {root, signal} = ctx;
  let scope;
  try {scope = reportScope(ctx.route.params);}
  catch (error) {
    root.innerHTML = `<header class="page-header"><h1 class="page-heading">Laporan</h1></header><div class="error-region" role="alert"><h2>Scope laporan tidak valid</h2><p>${esc(error.message)}</p><a class="button" href="#/triage?tenant=${esc(encodeURIComponent(ctx.route.params.get('tenant') || 'all'))}">Kembali ke Triage</a></div>`;
    return () => ctx.setGuard(null);
  }
  root.innerHTML = reportPage(scope);
  const find = selector => root.querySelector(selector);
  const documentRegion = find('#report-document');
  const actionStatus = find('#report-action-status');
  const fallbackRegion = find('#report-fallback');
  const groupSelect = find('#report-group');
  let actionPending = false;
  let disposed = false;
  const session = createReportSession({scope, getJSON: json, signal, onChange: update});

  function controls() {
    for (const control of root.querySelectorAll('[data-export]')) control.disabled = actionPending || session.state.loading || !session.state.preview;
    find('[data-action="refresh-preview"]').disabled = actionPending || session.state.loading;
  }
  function update(state) {
    documentRegion.setAttribute('aria-busy', String(state.loading));
    fallbackRegion.hidden = true;
    actionStatus.textContent = '';
    if (state.loading) {
      documentRegion.innerHTML = '<p class="inline-status" role="status">Memuat dokumen lengkap untuk scope ini…</p>';
      find('#report-count').textContent = 'Menghitung alert dari server…';
    } else if (state.error) {
      documentRegion.innerHTML = errorState(state.error);
      find('#report-count').textContent = 'Jumlah belum dapat diverifikasi. Ekspor dinonaktifkan.';
    } else if (state.preview) {
      documentRegion.innerHTML = reportPreview(state.preview);
      if (state.preview.count === 0) documentRegion.innerHTML = emptyState('Tidak ada alert dalam scope ini', 'Ubah filter di Triage atau pilih insiden lain. Dokumen kosong tetap dapat diekspor.') + documentRegion.innerHTML;
      find('#report-count').textContent = `${state.preview.count} alert dalam scope · tidak terpotong`;
    }
    controls();
  }
  async function loadGroups() {
    try {
      const data = await json(apiURL('/api/groups', {tenant: scope.get('tenant')}), {signal});
      if (disposed || signal.aborted) return;
      if (!Array.isArray(data) || !data.every(group => group && typeof group.id === 'string')) throw new Error('Daftar insiden tidak valid.');
      groupSelect.innerHTML = groupOptions(data, scope.get('group_id') || '');
      groupSelect.value = scope.get('group_id') || '';
      groupSelect.disabled = false;
      find('#report-groups-status').textContent = data.length ? '' : 'Belum ada insiden dalam tenant ini.';
    } catch (error) {
      if (disposed || signal.aborted) return;
      groupSelect.innerHTML = '<option value="">Daftar insiden tidak tersedia</option>';
      groupSelect.disabled = true;
      find('#report-groups-status').textContent = `Tidak dapat memuat insiden. ${error.message} Preview scope saat ini tidak diubah.`;
    }
  }
  groupSelect.addEventListener('change', () => {
    if (groupSelect.value) ctx.navigate(caseReportRoute(scope, groupSelect.value));
  }, {signal});
  root.addEventListener('click', async event => {
    const control = event.target.closest('[data-action], [data-export]');
    if (!control || !root.contains(control) || control.disabled) return;
    if (['retry', 'refresh-preview'].includes(control.dataset.action)) {if (!actionPending) void session.load(); return;}
    if (!control.dataset.export || actionPending || !session.state.preview || session.state.loading) return;
    actionPending = true; controls();
    actionStatus.textContent = control.dataset.export.startsWith('copy-') ? 'Menyalin laporan…' : 'Menyiapkan unduhan…';
    fallbackRegion.hidden = true;
    const result = await reportAction(control.dataset.export, {scope, preview: session.state.preview, request, download, copyHTML, copyText, signal});
    if (disposed || signal.aborted) return;
    actionPending = false;
    actionStatus.textContent = result.message;
    if (result.fallback) {
      fallbackRegion.innerHTML = reportFallback(result.fallback); fallbackRegion.hidden = false;
    }
    controls();
    ctx.notify(result.message, result.ok ? 'success' : 'error');
  }, {signal});
  root.addEventListener('arbiter:refresh', () => {if (!actionPending) {void session.load(); void loadGroups();}}, {signal});
  void session.load(); void loadGroups();
  return () => {disposed = true; session.dispose(); ctx.setGuard(null);};
}
