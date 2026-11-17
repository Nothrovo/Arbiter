import {json} from '../api/client.js';
import {esc, icon} from './primitives.js';
import {EXCLUSION_FIELD_OPTIONS, EXCLUSION_MATCH_OPTIONS} from '../features/settings/model.js';

/**
 * Open the shared "exclude alert data" dialog.
 *
 * Callers pass a preselected field/pattern (for example a URL from the Triage
 * inspector or a Stats category). The operator can still switch the field, so
 * data.url, agent, source IP, rule, referer, etc. are all reachable from the
 * same control. The rule is stored through the normal exclusion API.
 */
export function openExclusionDialog({
  root = document.body,
  signal,
  notify,
  initial = {},
  values = {},
  onSaved,
} = {}) {
  const dialog = document.createElement('dialog');
  dialog.className = 'app-dialog exclusion-dialog';
  const initialField = EXCLUSION_FIELD_OPTIONS.some(([key]) => key === initial.field) ? initial.field : 'url';
  const initialMatch = EXCLUSION_MATCH_OPTIONS.some(([key]) => key === initial.match) ? initial.match : 'glob';
  dialog.innerHTML = `
    <div class="dialog-header">
      <h2>Tambah pengecualian</h2>
      <button class="button icon-button" type="button" data-close-exclusion aria-label="Tutup dialog pengecualian">${icon('close')}</button>
    </div>
    <form class="stack" novalidate>
      <p class="meta">Alert yang cocok disembunyikan dari Triage, Statistik, ringkasan, dan AI Triage. Bukti insiden yang sudah ada tidak dihapus.</p>
      <div class="form-grid">
        <div class="field">
          <label for="exclusion-dialog-field">Field</label>
          <select class="select" id="exclusion-dialog-field" name="field">
            ${EXCLUSION_FIELD_OPTIONS.map(([key, label]) => `<option value="${esc(key)}" ${key === initialField ? 'selected' : ''}>${esc(label)}</option>`).join('')}
          </select>
        </div>
        <div class="field">
          <label for="exclusion-dialog-match">Pencocokan</label>
          <select class="select" id="exclusion-dialog-match" name="match">
            ${EXCLUSION_MATCH_OPTIONS.map(([key, label]) => `<option value="${esc(key)}" ${key === initialMatch ? 'selected' : ''}>${esc(label)}</option>`).join('')}
          </select>
        </div>
      </div>
      <div class="field">
        <label for="exclusion-dialog-pattern">Pola</label>
        <input class="input mono" id="exclusion-dialog-pattern" name="pattern" type="text" autocomplete="off" spellcheck="false" value="${esc(initial.pattern || '')}" placeholder="Contoh: */service/mbkm/logbook*">
        <span class="meta" id="exclusion-dialog-hint">Mode Glob memakai * (banyak karakter) dan ? (satu karakter).</span>
      </div>
      <div class="field">
        <label for="exclusion-dialog-label">Catatan (opsional)</label>
        <input class="input" id="exclusion-dialog-label" name="label" type="text" autocomplete="off" maxlength="160" value="${esc(initial.label || '')}" placeholder="Misalnya: noise endpoint logbook MBKM">
      </div>
      <p class="inline-status" data-kind="error" role="alert" data-exclusion-status></p>
      <div class="dialog-actions">
        <button class="button" type="button" data-close-exclusion>Batal</button>
        <button class="button primary" type="submit">${icon('shield')} Simpan pengecualian</button>
      </div>
    </form>`;

  root.append(dialog);
  const form = dialog.querySelector('form');
  const fieldSelect = dialog.querySelector('[name=field]');
  const matchSelect = dialog.querySelector('[name=match]');
  const patternInput = dialog.querySelector('[name=pattern]');
  const labelInput = dialog.querySelector('[name=label]');
  const status = dialog.querySelector('[data-exclusion-status]');
  const submit = form.querySelector('button[type=submit]');

  const close = () => {
    if (dialog.open) dialog.close();
    dialog.remove();
  };
  const onAbort = () => close();
  signal?.addEventListener('abort', onAbort, {once: true});
  dialog.addEventListener('close', () => {
    signal?.removeEventListener('abort', onAbort);
    dialog.remove();
  }, {once: true});
  dialog.addEventListener('click', event => {
    if (event.target === dialog) close();
  });
  dialog.querySelectorAll('[data-close-exclusion]').forEach(button => {
    button.addEventListener('click', close, {once: true});
  });

  patternInput.addEventListener('input', () => { lastPattern = patternInput.value; });
  fieldSelect.addEventListener('change', () => {
    const next = fieldSelect.value;
    const mapped = values[next];
    if (mapped != null && String(mapped).trim()) {
      patternInput.value = String(mapped);
    }
  });
  matchSelect.addEventListener('change', () => {
    const hint = dialog.querySelector('#exclusion-dialog-hint');
    if (!hint) return;
    hint.textContent = matchSelect.value === 'regex'
      ? 'Regex PostgreSQL. Gunakan mode Glob untuk pola yang memakai * atau ?.'
      : matchSelect.value === 'contains'
        ? 'Cocok bila field mengandung teks pola.'
        : matchSelect.value === 'exact'
          ? 'Cocok hanya bila nilai field sama persis.'
          : 'Mode Glob memakai * (banyak karakter) dan ? (satu karakter).';
  });

  form.addEventListener('submit', async event => {
    event.preventDefault();
    const pattern = patternInput.value.trim();
    if (!pattern) {
      status.textContent = 'Pola pengecualian tidak boleh kosong.';
      status.dataset.kind = 'error';
      patternInput.focus();
      return;
    }
    submit.disabled = true;
    status.textContent = '';
    try {
      const body = await json('/api/settings/exclusions', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          field: fieldSelect.value,
          match: matchSelect.value,
          pattern,
          label: labelInput.value.trim(),
        }),
        signal,
      });
      notify?.(
        body.added === false ? 'Pola tersebut sudah ada di daftar pengecualian.' : 'Aturan pengecualian ditambahkan.',
        body.added === false ? 'info' : 'success'
      );
      close();
      await onSaved?.(body);
    } catch (error) {
      if (error.name === 'AbortError') return;
      status.textContent = error.status === 404 || error.status === 405
        ? 'Endpoint pengecualian belum tersedia di server. Restart layanan Arbiter lalu coba lagi.'
        : (error.message || 'Gagal menyimpan aturan pengecualian.');
      status.dataset.kind = 'error';
    } finally {
      if (submit.isConnected) submit.disabled = false;
    }
  });

  dialog.showModal();
  patternInput.focus();
  patternInput.select();
  return dialog;
}
