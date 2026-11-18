import {json} from '../../api/client.js';
import {esc, icon, errorState, loadingRows, formatTime} from '../../ui/primitives.js';
import {
  REALTIME_SEVERITY_OPTIONS,
  normalizeSettings,
  parseRealtimeSeverity,
  realtimeSeverityLabel,
  realtimeSeveritySelection,
} from '../settings/model.js';

const PRESET_MS = {
  '1h': 3600000,
  '24h': 86400000,
  '7d': 604800000,
  '30d': 2592000000,
};

const PRESET_LABELS = {
  '1h': '1 jam terakhir',
  '24h': '24 jam terakhir',
  '7d': '7 hari terakhir',
  '30d': '30 hari terakhir',
  custom: 'Rentang kustom',
  all: 'Semua waktu',
};

const STATUS_LABELS = {
  queued: 'Menunggu…',
  running: 'Mengambil alert…',
  done: 'Selesai',
  error: 'Gagal',
  cancelled: 'Dibatalkan',
};

const STORAGE_KEY = 'arbiter:pull:job';

function formatDuration(seconds) {
  const total = Math.max(0, Math.round(Number(seconds) || 0));
  if (total < 60) return `${total} dtk`;
  const minutes = Math.floor(total / 60);
  const rest = total % 60;
  if (minutes < 60) return rest ? `${minutes} mnt ${rest} dtk` : `${minutes} mnt`;
  const hours = Math.floor(minutes / 60);
  const restMinutes = minutes % 60;
  return restMinutes ? `${hours} jam ${restMinutes} mnt` : `${hours} jam`;
}

function rememberJob(id) {
  try {
    // localStorage survives closing the tab; the job itself lives on the server.
    if (id) localStorage.setItem(STORAGE_KEY, id);
    else localStorage.removeItem(STORAGE_KEY);
  } catch {
    // Private-mode browsers may block storage; the page still works.
  }
}

export async function mount(ctx) {
  const {root, signal, notify} = ctx;
  let settings = null;
  let job = null;
  let timer = null;
  let pollAbort = null;
  let starting = false;

  function paint() {
    if (!settings) return;
    const wazuh = settings.wazuh;
    const realtime = settings.realtime;
    const configured = Boolean(wazuh.indexer_url);
    const severitySelection = realtimeSeveritySelection(realtime);
    root.innerHTML = `
      <header class="page-header">
        <div class="page-heading">
          <h1>Ambil Alert</h1>
          <p class="page-description">Tarik alert langsung dari Wazuh Indexer ke database aktif. Proses berjalan di latar belakang dengan progres per halaman, terpisah dari monitor realtime.</p>
        </div>
        <div class="page-actions">
          <a class="button" href="#/realtime">${icon('pulse')} Monitor realtime</a>
          <a class="button" href="#/triage">${icon('inbox')} Buka Triage</a>
        </div>
      </header>

      ${configured ? '' : `<div class="notice" data-kind="warning"><p><strong>Wazuh Indexer belum dikonfigurasi.</strong> Isi URL dan kredensial di <a href="#/settings">Pengaturan</a> sebelum mengambil alert.</p></div>`}

      <div class="pull-layout">
        <section class="form-section pull-card">
          <h2 class="section-heading">Rentang pengambilan</h2>
          <form id="pull-form" class="stack" novalidate>
            <div class="form-grid">
              <div class="field">
                <label for="pull-time-preset">Rentang waktu</label>
                <select class="select" id="pull-time-preset" name="time_preset">
                  ${['24h', '1h', '7d', '30d', 'custom', 'all'].map(key => `<option value="${key}" ${key === '24h' ? 'selected' : ''}>${esc(PRESET_LABELS[key])}</option>`).join('')}
                </select>
              </div>
              <div class="field">
                <label for="pull-severity">Ambang severity</label>
                <select class="select" id="pull-severity" name="severity">
                  ${REALTIME_SEVERITY_OPTIONS.map(([value, label]) => `<option value="${esc(value)}" ${value === severitySelection ? 'selected' : ''}>${esc(label)}</option>`).join('')}
                </select>
              </div>
            </div>
            <div id="pull-custom-time" class="form-grid" style="display:none">
              <div class="field">
                <label for="pull-time-from">Dari</label>
                <input class="input" type="datetime-local" id="pull-time-from" name="time_from">
              </div>
              <div class="field">
                <label for="pull-time-to">Sampai</label>
                <input class="input" type="datetime-local" id="pull-time-to" name="time_to">
              </div>
            </div>
            <div class="form-grid">
              <div class="field">
                <label for="pull-max-docs">Maks alert</label>
                <input class="input mono" id="pull-max-docs" name="max_docs" type="number" min="1" max="100000" step="1" value="100000">
                <span class="meta">1–100000 dokumen. Rentang yang lebih kecil lebih cepat selesai.</span>
              </div>
              <div class="field">
                <label for="pull-page-size">Per halaman</label>
                <input class="input mono" id="pull-page-size" name="page_size" type="number" min="50" max="10000" step="100" value="2000">
                <span class="meta">Dokumen per permintaan ke indexer (50–10000). Halaman lebih besar = lebih sedikit request.</span>
              </div>
              <div class="field">
                <label for="pull-chunk-days">Pecah per hari</label>
                <input class="input mono" id="pull-chunk-days" name="chunk_days" type="number" min="0" max="30" step="1" value="1">
                <span class="meta">0 = satu permintaan untuk seluruh rentang.</span>
              </div>
            </div>
            <p class="meta">Filter: <strong>${esc(wazuh.index_pattern || 'wazuh-alerts-*')}</strong> · ${esc(realtimeSeverityLabel(parseRealtimeSeverity(severitySelection)))}. Alert yang sudah ada otomatis digabung (dedup), bukan diduplikasi.</p>
            <div class="settings-actions">
              <button class="button primary" type="submit" ${configured ? '' : 'disabled'}>${icon('upload')} Mulai ambil alert</button>
              <span class="inline-status" id="pull-status" role="status"></span>
            </div>
          </form>
        </section>

        <section class="form-section pull-card" id="pull-progress-card" hidden>
          <h2 class="section-heading">Progres pengambilan</h2>
          <div class="pull-progress" data-state="idle">
            <div class="pull-progress-head">
              <span class="badge neutral" id="pull-progress-badge">Menunggu…</span>
              <span class="mono" id="pull-progress-percent">0%</span>
            </div>
            <div class="progress-track" role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuenow="0" id="pull-progress-track">
              <div class="progress-fill" id="pull-progress-fill" style="width:0%"></div>
            </div>
            <dl class="detail-grid pull-progress-grid">
              <div class="key-value"><dt>Diperiksa</dt><dd class="num" id="pull-fetched">0</dd></div>
              <div class="key-value"><dt>Target</dt><dd class="num" id="pull-target">—</dd></div>
              <div class="key-value"><dt>Laju</dt><dd class="num" id="pull-rate">—</dd></div>
              <div class="key-value"><dt>Perkiraan selesai</dt><dd class="num" id="pull-eta">—</dd></div>
              <div class="key-value"><dt>Alert baru</dt><dd class="num" id="pull-inserted">0</dd></div>
              <div class="key-value"><dt>Dedup / sudah ada</dt><dd class="num" id="pull-deduplicated">0</dd></div>
              <div class="key-value"><dt>Gagal dinormalisasi</dt><dd class="num" id="pull-failed">0</dd></div>
              <div class="key-value"><dt>Jendela waktu</dt><dd class="num" id="pull-windows">—</dd></div>
            </dl>
            <p class="meta" id="pull-progress-note">Job berjalan di server; halaman ini boleh ditinggal dan dibuka lagi nanti.</p>
            <div class="settings-actions">
              <button class="button" type="button" id="pull-cancel" hidden>${icon('close')} Batalkan</button>
              <a class="button" href="#/triage" id="pull-open-triage" hidden>${icon('inbox')} Lihat di Triage</a>
            </div>
          </div>
        </section>

        <section class="form-section pull-card">
          <h2 class="section-heading">Catatan</h2>
          <ul class="stack meta">
            <li>Monitor <a href="#/realtime">Realtime</a> tetap dipakai untuk pull kecil berkala (interval 30 detik atau harian). Halaman ini untuk backfill manual.</li>
            <li>Progres berasal dari server, bukan perkiraan browser. Total alert dihitung lebih dulu dari indexer.</li>
            <li>Alert yang dikecualikan tetap masuk database; pengecualian hanya menyembunyikannya dari Triage, Statistik, dan AI Triage.</li>
            <li>Job berjalan di server. Menutup tab atau berpindah menu tidak menghentikannya; buka lagi halaman ini untuk melanjutkan progres (ID job disimpan di browser).</li>
            <li>Job disimpan di memori proses. Restart server membatalkan job yang sedang berjalan.</li>
          </ul>
        </section>
      </div>`;

    const form = root.querySelector('#pull-form');
    const preset = root.querySelector('#pull-time-preset');
    const customWrap = root.querySelector('#pull-custom-time');
    const status = root.querySelector('#pull-status');
    const startButton = form.querySelector('button[type=submit]');

    preset.addEventListener('change', () => {
      customWrap.style.display = preset.value === 'custom' ? 'grid' : 'none';
    }, {signal});

    form.addEventListener('submit', async event => {
      event.preventDefault();
      if (starting) return;
      const timePreset = preset.value;
      const payload = {
        min_rule_level: undefined,
        max_rule_level: null,
        max_docs: Number(root.querySelector('#pull-max-docs').value) || 100000,
        page_size: Number(root.querySelector('#pull-page-size').value) || 2000,
        chunk_days: Number(root.querySelector('#pull-chunk-days').value),
      };
      const severity = parseRealtimeSeverity(root.querySelector('#pull-severity').value);
      payload.min_rule_level = severity.min_rule_level;
      payload.max_rule_level = severity.max_rule_level;

      if (preset.value === 'all') {
        payload.all_time = true;
      } else if (preset.value === 'custom') {
        const from = root.querySelector('#pull-time-from').value;
        const to = root.querySelector('#pull-time-to').value;
        if (!from && !to) {
          status.textContent = 'Pilih minimal tanggal/jam "Dari" untuk rentang kustom.';
          status.dataset.kind = 'error';
          return;
        }
        if (from) payload.time_from = from;
        if (to) payload.time_to = to;
      } else {
        payload.time_from = new Date(Date.now() - PRESET_MS[preset.value]).toISOString();
      }

      starting = true;
      startButton.disabled = true;
      status.textContent = '';
      stopPolling();
      try {
        const body = await json('/api/alerts/pull', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify(payload),
          signal,
          timeout: 30000,
        });
        job = body.job;
        rememberJob(job?.id);
        root.querySelector('#pull-progress-card').hidden = false;
        paintProgress();
        notify('Pengambilan alert dimulai. Progres diperbarui otomatis.', 'info');
        pollLater(600);
      } catch (error) {
        if (error.name === 'AbortError') return;
        status.textContent = error.status === 404 || error.status === 405
          ? 'Endpoint pengambilan alert belum tersedia di server. Restart layanan Arbiter lalu coba lagi.'
          : (error.message || 'Gagal memulai pengambilan alert.');
        status.dataset.kind = 'error';
        startButton.disabled = false;
      } finally {
        starting = false;
      }
    }, {signal});

    root.querySelector('#pull-cancel')?.addEventListener('click', async () => {
      if (!job) return;
      try {
        const body = await json(`/api/alerts/pull/${encodeURIComponent(job.id)}/cancel`, {method: 'POST', signal, timeout: 15000});
        job = body.job;
        paintProgress();
      } catch (error) {
        if (error.name !== 'AbortError') notify(error.message || 'Gagal membatalkan pengambilan.', 'error');
      }
    }, {signal});
  }

  function paintProgress() {
    if (!job || !root.querySelector('#pull-progress-card')) return;
    const running = job.status === 'queued' || job.status === 'running';
    const percent = Math.max(0, Math.min(100, Number(job.percent) || 0));
    const total = job.target ?? job.total;
    const stateEl = root.querySelector('.pull-progress');
    if (stateEl) stateEl.dataset.state = job.status;
    const badge = root.querySelector('#pull-progress-badge');
    if (badge) {
      badge.textContent = STATUS_LABELS[job.status] || job.status;
      badge.className = `badge ${job.status === 'done' ? 'success' : job.status === 'error' ? 'danger' : job.status === 'cancelled' ? 'neutral' : 'info'}`;
    }
    const percentEl = root.querySelector('#pull-progress-percent');
    if (percentEl) percentEl.textContent = total ? `${percent.toFixed(1)}%` : (running ? '…' : '—');
    const track = root.querySelector('#pull-progress-track');
    const fill = root.querySelector('#pull-progress-fill');
    if (track) {
      track.dataset.indeterminate = total ? 'false' : 'true';
      track.setAttribute('aria-valuenow', String(Math.round(percent)));
    }
    if (fill) fill.style.width = total ? `${percent}%` : '35%';
    const set = (selector, value) => {
      const el = root.querySelector(selector);
      if (el) el.textContent = value;
    };
    set('#pull-fetched', Number(job.fetched || 0).toLocaleString('id-ID'));
    set('#pull-target', total ? Number(total).toLocaleString('id-ID') : 'Menghitung…');
    set('#pull-inserted', Number(job.inserted || 0).toLocaleString('id-ID'));
    set('#pull-deduplicated', Number(job.deduplicated || 0).toLocaleString('id-ID'));
    set('#pull-failed', Number(job.failed || 0).toLocaleString('id-ID'));
    set('#pull-windows', job.windows_total ? `${job.windows_done || 0} / ${job.windows_total}` : '—');
    const rate = Number(job.rate) || 0;
    set('#pull-rate', rate > 0 ? `${rate.toLocaleString('id-ID', {maximumFractionDigits: 1})} alert/dtk` : '—');
    set('#pull-eta', job.eta_seconds ? formatDuration(job.eta_seconds) : (job.status === 'done' ? 'Selesai' : '—'));
    const note = root.querySelector('#pull-progress-note');
    if (note) {
      if (job.status === 'error') note.textContent = `Gagal: ${job.error || 'tidak diketahui'}`;
      else if (job.status === 'cancelled') note.textContent = 'Job dibatalkan. Alert yang sudah terambil tetap tersimpan.';
      else if (job.status === 'done') {
        note.textContent = job.capped
          ? `Selesai. Batas ${Number(job.max_docs).toLocaleString('id-ID')} alert tercapai; kecilkan rentang waktu untuk mengambil sisanya.`
          : `Selesai ${formatTime(job.finished_at)}. ${Number(job.fetched || 0).toLocaleString('id-ID')} alert diperiksa.`;
      } else if (job.current_window) {
        const win = job.current_window;
        note.textContent = `Jendela ${win.index}/${job.windows_total}: ${win.from || 'awal'} → ${win.to || 'sekarang'}.`;
      } else {
        note.textContent = 'Job berjalan di server; halaman ini boleh ditinggal.';
      }
    }
    const cancel = root.querySelector('#pull-cancel');
    if (cancel) cancel.hidden = !running;
    const open = root.querySelector('#pull-open-triage');
    if (open) open.hidden = job.status !== 'done';
    const start = root.querySelector('#pull-form button[type=submit]');
    if (start) start.disabled = running || starting || !settings?.wazuh?.indexer_url;
  }

  async function resumeJob() {
    let id = '';
    try {
      id = localStorage.getItem(STORAGE_KEY) || '';
    } catch {
      return;
    }
    if (id) {
      try {
        const body = await json(`/api/alerts/pull/${encodeURIComponent(id)}`, {signal, timeout: 15000});
        job = body.job;
        root.querySelector('#pull-progress-card').hidden = false;
        paintProgress();
        if (job.status === 'queued' || job.status === 'running') pollLater(1000);
        return;
      } catch (error) {
        if (error.name === 'AbortError') return;
        rememberJob('');
      }
    }
    // No stored id (new browser/tab) or it expired: fall back to the newest
    // server-side job, preferring one that is still running.
    try {
      const body = await json('/api/alerts/pull', {signal, timeout: 15000});
      const jobs = Array.isArray(body.jobs) ? body.jobs : [];
      const latest = jobs.find(item => item.status === 'queued' || item.status === 'running') || jobs[0];
      if (!latest) return;
      job = latest;
      rememberJob(job.id);
      root.querySelector('#pull-progress-card').hidden = false;
      paintProgress();
      if (job.status === 'queued' || job.status === 'running') pollLater(1000);
    } catch (error) {
      if (error.name !== 'AbortError') rememberJob('');
    }
  }

  function stopPolling() {
    clearTimeout(timer);
    timer = null;
    pollAbort?.abort();
    pollAbort = null;
  }

  function pollLater(delay = 1000) {
    stopPolling();
    timer = setTimeout(poll, delay);
  }

  async function poll() {
    if (!job || signal?.aborted) return;
    pollAbort = new AbortController();
    try {
      const body = await json(`/api/alerts/pull/${encodeURIComponent(job.id)}`, {signal: pollAbort.signal, timeout: 15000});
      job = body.job;
      paintProgress();
      if (job.status === 'queued' || job.status === 'running') pollLater(1000);
      else {
        stopPolling();
        if (job.status === 'done') {
          const capped = job.capped ? ' (batas maksimum tercapai)' : '';
          notify(`Selesai: ${Number(job.inserted || 0).toLocaleString('id-ID')} alert baru, ${Number(job.deduplicated || 0).toLocaleString('id-ID')} dedup${capped}.`, 'success');
        } else if (job.status === 'error') {
          notify(`Pengambilan gagal: ${job.error || 'tidak diketahui'}`, 'error');
        }
      }
    } catch (error) {
      if (error.name === 'AbortError' || signal?.aborted) return;
      notify(error.message || 'Gagal memeriksa progres pengambilan.', 'error');
      pollLater(2000);
    }
  }

  root.innerHTML = loadingRows(4);
  try {
    const body = await json('/api/settings', {signal, timeout: 15000});
    settings = normalizeSettings(body.settings);
    paint();
    resumeJob();
  } catch (error) {
    if (error.name === 'AbortError') return;
    root.innerHTML = `<header class="page-header"><div class="page-heading"><h1>Ambil Alert</h1></div></header>${errorState('Pengaturan workspace belum dapat dimuat.')}`;
    root.querySelector('[data-action=retry]')?.addEventListener('click', () => mount(ctx), {signal});
  }

  return () => {
    stopPolling();
  };
}
