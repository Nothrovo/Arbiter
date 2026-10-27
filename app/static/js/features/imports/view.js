import {json} from '../../api/client.js';
import {createImportSession} from './model.js';
import {importPage, importResult} from './render.js';

export function mount(ctx) {
  const {root, signal} = ctx;
  root.innerHTML = importPage();
  const find = selector => root.querySelector(selector);
  const file = find('#import-file');
  const text = find('#import-content');
  const form = find('#import-form');
  const error = find('#import-error');
  const result = find('#import-result');
  const win = root.ownerDocument.defaultView;
  let lastResult = null;
  const session = createImportSession({send: json, signal, onChange: update});

  function update(state) {
    for (const control of root.querySelectorAll('[data-mode]')) {
      control.setAttribute('aria-pressed', String(control.dataset.mode === state.mode));
      control.disabled = state.pending;
    }
    for (const panel of root.querySelectorAll('[data-panel]')) panel.hidden = panel.dataset.panel !== state.mode;
    file.disabled = state.pending; text.disabled = state.pending;
    find('[data-action="reset"]').disabled = state.pending;
    find('#import-submit').disabled = state.pending;
    find('#import-submit').textContent = state.pending ? 'Mengimpor…' : 'Impor alert';
    form.setAttribute('aria-busy', String(state.pending));
    error.hidden = !state.error; error.textContent = state.error;
    find('#import-warning').textContent = state.warning;
    find('#import-file-note').textContent = state.file ? `File dipilih: ${state.file.name}` : 'Belum ada file dipilih.';
    find('#import-status').textContent = state.pending ? 'Menunggu hasil server. Jangan kirim ulang.' : state.result ? 'Impor selesai. Hasil aktual tersedia di bawah.' : '';
    if (text.value !== state.text) text.value = state.text;
    if (!state.file) file.value = '';
    result.hidden = !state.result;
    if (state.result && state.result !== lastResult) {
      result.innerHTML = importResult(state.result, ctx.route.params);
      lastResult = state.result;
    }
  }

  ctx.setGuard(() => !session.dirty());
  const beforeUnload = event => {
    if (session.dirty()) {event.preventDefault(); event.returnValue = '';}
  };
  win.addEventListener('beforeunload', beforeUnload, {signal});
  text.addEventListener('input', () => session.setText(text.value), {signal});
  file.addEventListener('change', () => session.setFile(file.files[0] || null), {signal});
  form.addEventListener('submit', async event => {
    event.preventDefault();
    if (session.state.pending) return;
    const ok = await session.submit();
    if (signal.aborted) return;
    if (ok) {ctx.notify('Impor selesai.', 'success'); result.focus();}
    else if (session.state.error) error.focus();
  }, {signal});
  root.addEventListener('click', event => {
    const control = event.target.closest('[data-action], [data-mode]');
    if (!control || !root.contains(control) || session.state.pending) return;
    if (control.dataset.mode) session.setMode(control.dataset.mode);
    if (['reset', 'again'].includes(control.dataset.action) && session.reset()) {
      lastResult = null;
      (session.state.mode === 'file' ? file : text).focus();
    }
  }, {signal});
  root.addEventListener('arbiter:refresh', () => {
    ctx.notify(session.dirty() ? 'Input impor dipertahankan; tidak dikirim ulang.' : 'Pilih file atau tempel JSON untuk memulai impor.', 'info');
  }, {signal});
  update(session.state);
  return () => {ctx.setGuard(null); win.removeEventListener('beforeunload', beforeUnload);};
}
