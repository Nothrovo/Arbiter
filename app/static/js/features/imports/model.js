export function validateText(content) {
  if (!String(content ?? '').trim()) return {valid: false, error: 'Tempel JSON atau JSONL sebelum mengimpor.'};
  const text = String(content).replace(/^\uFEFF/, '').trim();
  try {
    JSON.parse(text);
  } catch {
    try {
      for (const line of text.split(/\r?\n/).filter(line => line.trim())) JSON.parse(line);
    } catch {
      return {valid: true, warning: 'JSON belum dapat dibaca oleh pemeriksaan lokal. Server akan memvalidasi dan dapat menolak impor.'};
    }
  }
  return {valid: true, warning: ''};
}

export function createImportSession({send, signal, onChange = () => {}}) {
  const state = {mode: 'file', text: '', file: null, pending: false, error: '', warning: '', result: null};
  const change = () => {if (!signal?.aborted) onChange(state);};
  const dirty = () => state.pending || Boolean(state.text.trim() || state.file);
  const session = {
    state, dirty,
    setMode(mode) {if (!state.pending && ['file', 'paste'].includes(mode)) {state.mode = mode; state.error = ''; change();}},
    setText(text) {if (!state.pending) {state.text = text; state.error = ''; state.warning = validateText(text).warning || ''; change();}},
    setFile(file) {if (!state.pending) {state.file = file; state.error = ''; state.warning = ''; change();}},
    reset() {
      if (state.pending) return false;
      Object.assign(state, {text: '', file: null, error: '', warning: '', result: null}); change(); return true;
    },
    async submit() {
      if (state.pending || signal?.aborted) return false;
      const validation = state.mode === 'file' ? validateFile(state.file) : validateText(state.text);
      if (!validation.valid) {state.error = validation.error; change(); return false;}
      state.pending = true; state.error = ''; state.warning = validation.warning || ''; state.result = null; change();
      try {
        const options = {method: 'POST', signal};
        let path;
        if (state.mode === 'file') {
          path = '/api/import'; options.body = new FormData(); options.body.set('file', state.file);
        } else {
          path = '/api/import-text'; options.headers = {'Content-Type': 'application/json'};
          options.body = JSON.stringify({content: state.text});
        }
        const result = await send(path, options);
        if (signal?.aborted) return false;
        if (!result || !['parsed', 'inserted', 'deduplicated'].every(key => Number.isSafeInteger(result[key]) && result[key] >= 0) ||
            !Array.isArray(result.warnings) || !result.warnings.every(item => typeof item === 'string')) {
          throw new Error('Hasil impor tidak lengkap. Input dipertahankan; periksa respons server sebelum mencoba lagi.');
        }
        state.result = {parsed: result.parsed, inserted: result.inserted, deduplicated: result.deduplicated, warnings: [...result.warnings]};
        state.text = ''; state.file = null; state.warning = ''; return true;
      } catch (error) {
        if (!signal?.aborted) state.error = error.message || 'Impor gagal. Input tetap tersedia untuk dicoba kembali.';
        return false;
      } finally {state.pending = false; change();}
    },
  };
  return session;
}

export function validateFile(file) {
  if (!file) return {valid: false, error: 'Pilih file JSON, JSONL, atau TXT sebelum mengimpor.'};
  if (!/\.(json|jsonl|txt)$/i.test(file.name)) return {valid: false, error: 'Gunakan file .json, .jsonl, atau .txt berisi teks UTF-8.'};
  if (!Number.isFinite(file.size) || file.size <= 0) return {valid: false, error: 'File kosong. Pilih file yang berisi alert.'};
  return {valid: true, warning: ''};
}
