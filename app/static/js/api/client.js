export class ApiError extends Error {
  constructor(message, status = 0) { super(message); this.name = 'ApiError'; this.status = status; }
}
export function apiURL(path, params = {}) {
  const query = params instanceof URLSearchParams ? new URLSearchParams(params) : new URLSearchParams();
  if (!(params instanceof URLSearchParams)) {
    for (const [key, value] of Object.entries(params)) {
      if (value === undefined || value === null || value === '') continue;
      if (Array.isArray(value)) {
        for (const item of value) if (item !== undefined && item !== null && item !== '') query.append(key, String(item));
      } else query.append(key, String(value));
    }
  }
  return path + (query.size ? `?${query}` : '');
}
export async function request(path, {timeout = 30000, ...options} = {}) {
  if (!String(path).startsWith('/') || String(path).startsWith('//')) throw new ApiError('Permintaan harus memakai endpoint lokal (same origin).');
  const controller = new AbortController();
  let timedOut = false;
  const abort = () => controller.abort(options.signal?.reason);
  if (options.signal?.aborted) abort();
  else options.signal?.addEventListener('abort', abort, {once: true});
  const timer = setTimeout(() => { timedOut = true; controller.abort(); }, timeout);
  try {
    const response = await fetch(path, {...options, signal: controller.signal, credentials: 'same-origin', cache: 'no-store', headers: {...options.headers}});
    if (!response.ok) {
      let message = `Permintaan gagal (${response.status}). Coba lagi.`;
      try { const body = await response.json(); if (typeof body.detail === 'string') message = body.detail; } catch { /* Non-JSON errors are not echoed to avoid disclosing raw payloads. */ }
      throw new ApiError(message, response.status);
    }
    return response;
  } catch (error) {
    if (timedOut) throw new ApiError('Permintaan terlalu lama. Periksa koneksi lalu coba lagi.');
    if (error.name === 'AbortError' || error instanceof ApiError) throw error;
    throw new ApiError('Tidak dapat terhubung ke workspace lokal. Periksa layanan lalu coba lagi.');
  } finally {
    clearTimeout(timer); options.signal?.removeEventListener('abort', abort);
  }
}
export async function json(path, options = {}) {
  const response = await request(path, options);
  try { return await response.json(); } catch { throw new ApiError('Respons server tidak valid. Muat ulang atau coba lagi.'); }
}
export async function download(url, filename = 'Arbiter-report') {
  const response = await request(url, {timeout: 120000});
  const disposition = response.headers.get('Content-Disposition') || '';
  const suggested = disposition.match(/filename="([^"]+)"/)?.[1];
  const blob = await response.blob();
  const objectURL = URL.createObjectURL(blob);
  const link = document.createElement('a'); link.href = objectURL; link.download = (suggested || filename).replace(/[\\/\r\n]/g, '_');
  document.body.append(link); link.click(); link.remove();
  setTimeout(() => URL.revokeObjectURL(objectURL), 1000);
}
export async function copyText(text) {
  if (!navigator.clipboard?.writeText) throw new ApiError('Clipboard tidak tersedia. Gunakan unduh atau salin manual.');
  await navigator.clipboard.writeText(text);
}
export async function copyHTML(html) {
  if (!navigator.clipboard?.write || typeof ClipboardItem === 'undefined') throw new ApiError('Clipboard berformat tidak tersedia. Unduh atau buka preview untuk menyalin manual.');
  const doc = new DOMParser().parseFromString(html, 'text/html');
  await navigator.clipboard.write([new ClipboardItem({'text/html': new Blob([html], {type: 'text/html'}), 'text/plain': new Blob([doc.body.textContent || ''], {type: 'text/plain'})})]);
}
