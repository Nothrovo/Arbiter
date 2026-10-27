import {esc, icon, severity} from '../../ui/primitives.js';
import {PIVOT_OPTIONS, METRIC_OPTIONS, CHART_OPTIONS, distributionPercentages, triageRouteFromStats} from './model.js';
import {renderBarChart, renderDonutChart, renderLineChart} from '../../ui/charts.js';

export function statsPage(query) {
  const pivotOpts = PIVOT_OPTIONS.map(([val, label]) => `<option value="${val}" ${query.pivot_by === val ? 'selected' : ''}>${esc(label)}</option>`).join('');
  const secPivotOpts = [
    ['', 'Tidak ada (satu level)'],
    ...PIVOT_OPTIONS.filter(([val]) => val !== 'pattern' && val !== query.pivot_by),
  ].map(([val, label]) => `<option value="${val}" ${query.secondary_pivot === val ? 'selected' : ''}>${esc(label)}</option>`).join('');

  const topNOpts = [5, 8, 10, 15, 20, 50].map(n => `<option value="${n}" ${query.top_n === n ? 'selected' : ''}>Top ${n}</option>`).join('');
  const timePresets = [
    ['', 'Semua waktu'],
    ['1h', '1 jam terakhir'],
    ['24h', '24 jam terakhir'],
    ['7d', '7 hari terakhir'],
    ['30d', '30 hari terakhir'],
    ['custom', 'Rentang kustom…'],
  ].map(([v, l]) => `<option value="${v}" ${query.time_preset === v ? 'selected' : ''}>${l}</option>`).join('');

  const triageUrl = triageRouteFromStats(query);

  return `
    <header class="page-header">
      <div class="page-heading">
        <h1 id="stats-title">Statistik &amp; Pivot</h1>
        <p class="page-description">Workbench investigasi analitis berbasis agregasi telemetri SQL murni.</p>
      </div>
      <div class="page-actions stats-page-actions">
        <button class="button" type="button" data-action="export-csv">${icon('report')} CSV</button>
        <button class="button" type="button" data-action="export-svg">${icon('copy')} SVG</button>
        <button class="button" type="button" data-action="copy-summary">${icon('copy')} Salin Ringkasan</button>
        <span class="stats-action-divider" aria-hidden="true"></span>
        <a class="button primary" id="btn-open-triage" href="${triageUrl}">${icon('inbox')} Buka di Triage</a>
        <button class="button" type="button" data-action="reset-stats">${icon('refresh')} Reset</button>
      </div>
    </header>

    <section class="panel stats-controls stack" style="margin-bottom:16px;">
      <div class="stats-control-row">
        <div class="field stats-field-grow">
          <label for="stats-pivot">Pivot acuan utama</label>
          <select class="select" id="stats-pivot" name="pivot_by">${pivotOpts}</select>
        </div>
        <div class="field stats-field-grow">
          <label for="stats-secondary-pivot">Pivot kedua (stacked bar)</label>
          <select class="select" id="stats-secondary-pivot" name="secondary_pivot">${secPivotOpts}</select>
        </div>
        <div class="field stats-field-auto">
          <label for="stats-metric-segmented">Metrik hitungan</label>
          <div class="segmented stats-segmented" id="stats-metric-segmented">
            ${METRIC_OPTIONS.map(([val, lbl]) => `<button type="button" class="btn-seg ${query.metric === val ? 'active' : ''}" data-metric="${val}" aria-pressed="${query.metric === val}">${esc(lbl)}</button>`).join('')}
          </div>
        </div>
        <div class="field stats-field-auto">
          <label for="stats-chart-segmented">Tipe visualisasi</label>
          <div class="segmented stats-segmented" id="stats-chart-segmented">
            ${CHART_OPTIONS.map(([val, lbl]) => `<button type="button" class="btn-seg ${query.chart === val ? 'active' : ''}" data-chart="${val}" aria-pressed="${query.chart === val}">${esc(lbl)}</button>`).join('')}
          </div>
        </div>
      </div>

      <div class="stats-control-row" style="margin-top:10px;">
        <div class="field stats-field-grow">
          <label for="stats-top-n">Batas kategori teratas</label>
          <select class="select" id="stats-top-n" name="top_n">${topNOpts}</select>
        </div>
        <div class="field stats-field-grow">
          <label for="stats-time">Rentang waktu</label>
          <select class="select" id="stats-time" name="time_preset">${timePresets}</select>
        </div>
        <div class="field stats-field-grow">
          <label for="stats-preset-select">Preset tersimpan</label>
          <div class="stats-preset-control">
            <select class="select" id="stats-preset-select" style="flex:1;">
              <option value="">Pilih preset…</option>
              <option value="preset-top-rules-24h">Top Rules 24 Jam</option>
              <option value="preset-top-ips-7d">Top IP Sumber 7 Hari</option>
              <option value="preset-http-status">Distribusi HTTP Status</option>
            </select>
            <button class="button icon-button" type="button" id="btn-save-preset" title="Simpan konfigurasi tampilan saat ini">${icon('plus')}</button>
          </div>
        </div>
      </div>

      <div id="stats-custom-time-wrap" style="display:${query.time_preset === 'custom' || (query.time_from && !query.time_preset) ? 'grid' : 'none'}; grid-template-columns:1fr 1fr; gap:12px; margin-top:8px;">
        <div class="field">
          <label for="stats-time-from">Dari waktu</label>
          <input class="input" type="datetime-local" id="stats-time-from" value="${esc(query.time_from)}">
        </div>
        <div class="field">
          <label for="stats-time-to">Sampai waktu</label>
          <input class="input" type="datetime-local" id="stats-time-to" value="${esc(query.time_to)}">
        </div>
      </div>

      <div id="stats-pattern-wrap" class="field" style="display:${query.pivot_by === 'pattern' ? 'block' : 'none'}; margin-top:8px;">
        <label for="stats-pattern-input">Kata kunci / pola teks (pencarian literal)</label>
        <div style="display:flex; gap:8px;">
          <input class="input" type="text" id="stats-pattern-input" value="${esc(query.pattern)}" placeholder="Contoh: sqlmap, bot, /admin, 403..." maxlength="120" style="max-width:400px;">
          <button class="button" type="button" id="btn-apply-pattern">Terapkan Pola</button>
        </div>
      </div>

      ${query.facet && query.facet_value ? `
        <div class="applied-filters" style="margin-top:12px;">
          <span class="badge neutral" style="display:inline-flex; align-items:center; gap:6px;">
            Drill-down: <strong>${esc(query.facet)} = ${esc(query.facet_value)}</strong>
            <button type="button" class="text-button" id="btn-clear-drilldown" title="Hapus filter drill-down" style="cursor:pointer;">${icon('close')}</button>
          </span>
        </div>
      ` : ''}
    </section>

    <div id="stats-workspace" class="stack">
      <div id="stats-results"></div>
    </div>

    <dialog class="app-dialog" id="stats-batch-incident-dialog" aria-labelledby="stats-batch-incident-title">
      <div class="dialog-header">
        <h2 id="stats-batch-incident-title">Masukkan Bukti ke Insiden</h2>
        <button class="button icon-button" data-close-stats-batch-incident aria-label="Tutup dialog">${icon('close')}</button>
      </div>
      <form id="stats-batch-incident-form" class="stack">
        <p class="muted"><span id="stats-batch-incident-count">0</span> alert terpilih dari hasil drill-down akan ditautkan ke kasus insiden di bawah ini.</p>
        <div class="field">
          <label for="stats-batch-incident-select">Pilih Insiden Sasaran</label>
          <select class="select" id="stats-batch-incident-select" name="group_id" required>
            <option value="">Memuat daftar insiden…</option>
          </select>
        </div>
        <div class="dialog-actions" style="margin-top:20px; display:flex; justify-content:flex-end; gap:8px;">
          <button type="button" class="button" data-close-stats-batch-incident>Batal</button>
          <button class="button primary" type="submit">Tautkan ke Insiden</button>
        </div>
      </form>
    </dialog>
  `;
}

export function statsResults(data, query, {drilldownAlerts = null, selectedIds = [], expandedLogIds = new Set(), showAllLogs = false} = {}) {
  const total = Number(data.total) || 0;
  const metricLabel = data.metric === 'events' ? 'event' : 'alert';
  const otherCount = Number(data.other_count) || 0;
  const otherPct = Number(data.other_percentage) || 0;
  const items = distributionPercentages(data.items || [], otherCount, total);

  let chartHtml = '';
  if (query.chart === 'bar') {
    const secLabel = data.secondary_pivot ? (PIVOT_OPTIONS.find(([k]) => k === data.secondary_pivot)?.[1] || data.secondary_pivot) : '';
    chartHtml = renderBarChart({
      items,
      otherCount,
      otherPercentage: otherPct,
      total,
      metric: data.metric,
      secondaryDistribution: data.secondary_distribution,
      secondaryLabel: secLabel,
    });
  } else if (query.chart === 'donut') {
    chartHtml = renderDonutChart({items, otherCount, otherPercentage: otherPct, total, metric: data.metric});
  } else if (query.chart === 'line') {
    chartHtml = renderLineChart({timeSeries: data.time_series || [], topKeys: items.map(it => it.key), metric: data.metric});
  }

  const tableRows = items.map(item => {
    const keyEsc = esc(item.key);
    const triageUrl = triageRouteFromStats(query, {facet: data.pivot_by, facet_value: item.key});
    const subDist = data.secondary_distribution?.[item.key] || [];
    const subBreakdown = subDist.length ? `
      <div class="meta" style="margin-top:4px; font-size:11px;">
        ${subDist.slice(0, 3).map(s => `${esc(s.key)} (${s.count})`).join(' · ')}
        ${subDist.length > 3 ? ` · +${subDist.length - 3} lainnya` : ''}
      </div>
    ` : '';

    return `
      <tr>
        <td class="mono font-medium">
          ${keyEsc}
          ${subBreakdown}
        </td>
        <td class="numeric">${item.count.toLocaleString('id-ID')}</td>
        <td class="numeric">${item.displayPercentage}%</td>
        <td class="actions-col" style="text-align:right;">
          <button type="button" class="button text-button" data-drill-key="${keyEsc}" title="Saring statistik dan tampilkan bukti alert">Drill-down</button>
          <a class="button text-button" href="${triageUrl}" title="Lihat di antrean Triage">Triage</a>
        </td>
      </tr>
    `;
  }).join('');

  const otherRow = otherCount > 0 ? `
    <tr class="muted">
      <td class="mono"><em>Lainnya (${otherCount.toLocaleString('id-ID')} ${metricLabel})</em></td>
      <td class="numeric">${otherCount.toLocaleString('id-ID')}</td>
      <td class="numeric">${otherPct}%</td>
      <td class="actions-col" style="text-align:right;">
        <button type="button" class="button text-button" data-action="toggle-other-details">Rincian</button>
      </td>
    </tr>
  ` : '';

  const otherDetailsSection = data.other_items?.length ? `
    <div class="panel stack other-breakdown" style="margin-top:16px;">
      <div class="section-heading">
        <h3>Rincian Kategori "Lainnya" (${data.other_items.length} item berikutnya)</h3>
        <button type="button" class="button icon-button" data-action="close-other-details" aria-label="Tutup rincian">${icon('close')}</button>
      </div>
      <div class="table-region">
        <table class="data-table">
          <thead>
            <tr><th>Kategori</th><th class="numeric">Jumlah</th><th class="numeric">Persen</th></tr>
          </thead>
          <tbody>
            ${data.other_items.map(it => `
              <tr>
                <td class="mono">${esc(it.key)}</td>
                <td class="numeric">${it.count.toLocaleString('id-ID')}</td>
                <td class="numeric">${it.percentage}%</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    </div>
  ` : '';

  let drilldownSection = '';
  if (drilldownAlerts && drilldownAlerts.length) {
    const selectedSet = new Set(selectedIds);
    const allSelected = selectedIds.length > 0 && selectedIds.length === drilldownAlerts.length;

    const drilldownRows = drilldownAlerts.map(a => {
      const isSel = selectedSet.has(a.id);
      const isExp = showAllLogs || expandedLogIds.has(a.id);
      const logText = a.full_log || a.raw?.full_log || (a.raw ? JSON.stringify(a.raw, null, 2) : 'Log tidak tersedia.');

      const mainRow = `
        <tr data-drilldown-row="${a.id}" class="${isSel ? 'is-selected' : ''}">
          <td style="width:40px;">
            <input type="checkbox" data-select-drilldown="${a.id}" ${isSel ? 'checked' : ''} aria-label="Pilih alert #${a.id}">
          </td>
          <td class="meta num">${esc(a.timestamp?.slice(0, 16).replace('T', ' ') || '—')}</td>
          <td>${severity(a.rule_level)}</td>
          <td>
            <span class="font-medium">${esc(a.description || 'Alert')}</span>
            <span class="meta mono">(${esc(a.rule_id || '—')})</span>
            <button type="button" class="text-button meta" data-stats-action="toggle-log" data-alert-id="${a.id}" style="margin-left:6px; cursor:pointer;" title="Buka/tutup full log">
              [${isExp ? 'Tutup Log' : 'Log'}]
            </button>
          </td>
          <td class="mono">${esc(a.source_ip || '—')}</td>
          <td style="text-align:right;">
            <a class="button text-button" href="#/triage?alert=${a.id}" title="Buka detail lengkap di Triage">Triage</a>
          </td>
        </tr>
      `;

      const logRow = isExp ? `
        <tr class="log-expansion-row" data-log-for="${a.id}">
          <td colspan="6" class="log-expansion-cell">
            <div class="queue-log-box stack">
              <div class="split queue-log-head">
                <span class="meta mono">Log Alert #${esc(a.alert_id || a.id)} · Host: ${esc(a.agent_name || '—')} · Rule ${esc(a.rule_id || '—')}</span>
                <div style="display:flex; gap:6px;">
                  <button class="button text-button meta" type="button" data-stats-action="copy-single-log" data-alert-id="${a.id}">${icon('copy')} Salin</button>
                  <button class="button text-button meta" type="button" data-stats-action="copy-single-redacted" data-alert-id="${a.id}">Tersamarkan</button>
                  <button class="button text-button meta" type="button" data-stats-action="copy-single-defanged" data-alert-id="${a.id}">Defang</button>
                </div>
              </div>
              <pre class="raw-log">${esc(logText)}</pre>
            </div>
          </td>
        </tr>
      ` : '';

      return mainRow + logRow;
    }).join('');

    drilldownSection = `
      <section class="panel stack drilldown-evidence-section" style="margin-top:24px;">
        <div class="section-heading" style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
          <div>
            <h2>Bukti Alert Hasil Drill-down</h2>
            <span class="meta">${drilldownAlerts.length} alert ditampilkan (${esc(query.facet)} = ${esc(query.facet_value)})</span>
          </div>
          <div style="display:flex; gap:8px; align-items:center;">
            <button type="button" class="button" id="btn-toggle-all-stats-logs" aria-pressed="${showAllLogs}">
              ${icon('cases')} <span id="toggle-all-logs-label">${showAllLogs ? 'Tutup semua log' : 'Semua log'}</span>
            </button>
          </div>
        </div>

        <div id="stats-selection-toolbar" class="selection-toolbar" style="display:${selectedIds.length ? 'flex' : 'none'};">
          <strong>${selectedIds.length} alert dipilih</strong>
          <button class="button primary" type="button" data-stats-action="create-incident">${icon('plus')} Buat insiden</button>
          <button class="button" type="button" data-stats-action="add-to-incident">${icon('cases')} Masukkan ke insiden</button>
          <button class="button" type="button" data-stats-action="batch-review">Tandai direview</button>
          <button class="button" type="button" data-stats-action="batch-unreview">Belum direview</button>
          <button class="button" type="button" data-stats-action="copy-logs">${icon('copy')} Salin log</button>
          <button class="button" type="button" data-stats-action="copy-redacted">Tersamarkan</button>
          <button class="button icon-button" type="button" data-stats-action="clear-selection" aria-label="Batalkan pilihan">${icon('close')}</button>
        </div>

        <div class="table-region">
          <table class="data-table">
            <thead>
              <tr>
                <th style="width:40px;"><input type="checkbox" id="stats-select-all-drilldown" ${allSelected ? 'checked' : ''} aria-label="Pilih semua alert hasil drill-down"></th>
                <th style="width:110px;">Waktu</th>
                <th style="width:90px;">Severity</th>
                <th>Deskripsi / Rule</th>
                <th style="width:140px;">Source IP</th>
                <th style="width:100px; text-align:right;">Aksi</th>
              </tr>
            </thead>
            <tbody>
              ${drilldownRows}
            </tbody>
          </table>
        </div>
      </section>
    `;
  }

  return `
    <div class="metric-strip" style="margin-bottom:16px;">
      <div>
        <dt>Total ${metricLabel}</dt>
        <dd>${total.toLocaleString('id-ID')}</dd>
      </div>
      <div>
        <dt>Kategori teratas (Top-${data.top_n})</dt>
        <dd>${items.length} <span class="meta" style="font-size:14px;">kategori</span></dd>
      </div>
      <div>
        <dt>Kategori lainnya</dt>
        <dd>${otherCount.toLocaleString('id-ID')} <span class="meta" style="font-size:14px;">(${otherPct}%)</span></dd>
      </div>
    </div>

    ${query.chart !== 'table' ? `
      <section class="panel chart-container" id="stats-chart-wrapper" style="margin-bottom:20px; overflow-x:auto;">
        ${chartHtml}
      </section>
    ` : ''}

    <section class="panel table-container">
      <div class="section-heading">
        <h2>Tabel Distribusi Pivot</h2>
        <span class="meta">${items.length} baris ditampilkan</span>
      </div>
      <div class="table-region">
        <table class="data-table">
          <thead>
            <tr>
              <th>Nilai / Kategori</th>
              <th class="numeric" style="width:120px;">${data.metric === 'events' ? 'Event' : 'Alert'}</th>
              <th class="numeric" style="width:100px;">Proporsi</th>
              <th style="width:150px; text-align:right;">Aksi</th>
            </tr>
          </thead>
          <tbody>
            ${tableRows}
            ${otherRow}
          </tbody>
        </table>
      </div>
      ${otherDetailsSection}
    </section>

    ${drilldownSection}
  `;
}
