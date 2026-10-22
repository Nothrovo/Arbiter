import {queryFrom, scopeParams} from '../../state/scope.js';

export function reportScope(params) {
  if (params.has('alert_ids')) {
    const tokens = params.get('alert_ids').split(',');
    if (tokens.some(token => !/^[1-9]\d*$/.test(token) || !Number.isSafeInteger(Number(token)))) {
      throw new Error('Pilihan alert tidak valid. Kembali ke Triage dan pilih ulang; scope tidak diperluas.');
    }
    return scopeParams(queryFrom(params), {ids: tokens.map(Number)});
  }
  return scopeParams(queryFrom(params));
}

export function exportURL(scope, format) {
  if (!['preview', 'report-html', 'docx', 'xlsx', 'tsv', 'markdown', 'csv'].includes(format)) throw new Error('Format ekspor tidak dikenal.');
  return `${format === 'csv' ? '/api/export.csv' : `/api/export/${format}`}?${scope}`;
}

export function createReportSession({scope, getJSON, signal, onChange = () => {}}) {
  const capturedScope = new URLSearchParams(scope);
  const state = {loading: false, preview: null, error: ''};
  let version = 0;
  let controller;
  let disposed = false;
  const change = () => {if (!disposed && !signal?.aborted) onChange(state);};
  const dispose = () => {disposed = true; version++; controller?.abort();};
  signal?.addEventListener('abort', dispose, {once: true});
  return {
    state,
    dispose() {dispose(); signal?.removeEventListener('abort', dispose);},
    async load() {
      if (disposed || signal?.aborted) return false;
      const requestVersion = ++version;
      controller?.abort(); controller = new AbortController();
      state.loading = true; state.preview = null; state.error = ''; change();
      try {
        const data = await getJSON(exportURL(capturedScope, 'preview'), {signal: controller.signal});
        if (disposed || requestVersion !== version || signal?.aborted) return false;
        if (!data || !Number.isSafeInteger(data.count) || data.count < 0 || typeof data.html !== 'string' ||
            !data.meta || typeof data.meta !== 'object' || !data.scope || typeof data.scope !== 'object' || data.truncated !== false) {
          throw new Error('Preview tidak lengkap atau terpotong. Persempit scope dan coba lagi; ekspor dinonaktifkan.');
        }
        const defaults = {tenant: 'all', q: '', review_status: 'all', filter_preset: '', status: 'all', group_id: '', alert_ids: ''};
        for (const [key, fallback] of Object.entries(defaults)) {
          const expected = capturedScope.get(key) || fallback;
          const received = String(data.scope[key] ?? fallback);
          if (expected !== received) throw new Error('Scope preview berbeda dari permintaan. Ekspor dinonaktifkan; muat ulang atau pilih scope kembali.');
        }
        state.preview = data; return true;
      } catch (error) {
        if (!disposed && requestVersion === version && !signal?.aborted) state.error = error.message || 'Preview gagal dimuat. Coba lagi.';
        return false;
      } finally {
        if (!disposed && requestVersion === version) {state.loading = false; change();}
      }
    },
  };
}

export async function reportAction(action, {scope, preview, request, download, copyHTML, copyText, signal}) {
  const copy = action.startsWith('copy-');
  const format = action === 'copy-html' ? 'report-html' : copy ? action.slice(5) : action;
  let url;
  try {
    url = exportURL(scope, format);
    if (signal?.aborted) return {ok: false, message: 'Aksi dibatalkan.'};
    if (action === 'copy-html') {
      if (typeof preview?.html !== 'string') throw new Error('Muat preview lengkap sebelum menyalin.');
      await copyHTML(preview.html);
    } else if (copy && ['tsv', 'markdown'].includes(format)) {
      const response = await request(url, {signal});
      const text = await response.text();
      if (signal?.aborted) return {ok: false, message: 'Aksi dibatalkan.'};
      await copyText(text);
    } else if (!copy) {
      await download(url, `Arbiter-Report.${format === 'report-html' ? 'html' : format === 'markdown' ? 'md' : format}`);
    } else throw new Error('Format salin tidak dikenal.');
    return {ok: true, message: copy ? 'Laporan disalin ke clipboard.' : 'File laporan disiapkan untuk diunduh.'};
  } catch (error) {
    return {ok: false, message: `${copy ? 'Laporan tidak disalin.' : 'Unduhan gagal.'} ${error.message || 'Coba lagi.'}`, ...(url && copy ? {fallback: {url, format}} : {})};
  }
}

export function caseReportRoute(scope, groupId) {
  const params = new URLSearchParams(scope);
  params.delete('alert_ids'); params.delete('group_id');
  return `/reports?${scopeParams(queryFrom(params), groupId ? {groupId} : {})}`;
}
