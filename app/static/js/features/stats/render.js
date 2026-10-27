import {esc, icon} from '../../ui/primitives.js';
import {PIVOT_OPTIONS, METRIC_OPTIONS, CHART_OPTIONS, distributionPercentages, triageRouteFromStats} from './model.js';
import {renderBarChart, renderDonutChart, renderLineChart} from '../../ui/charts.js';

export function statsPage(query) {
  const pivotOpts = PIVOT_OPTIONS.map(([val, label]) => `<option value="${val}" ${query.pivot_by === val ? 'selected' : ''}>${esc(label)}</option>`).join('');
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
      <div class="page-actions">
        <a class="button primary" id="btn-open-triage" href="${triageUrl}">${icon('inbox')} Buka di Triage</a>
        <button class="button" type="button" data-action="reset-stats">Reset</button>
      </div>
    </header>

    <section class="panel stats-controls stack" style="margin-bottom:16px;">
      <div class="stats-control-grid" style="display:grid; grid-template-columns:repeat(auto-fit, minmax(180px, 1fr)); gap:12px; align-items:end;">
        <div class="field">
          <label for="stats-pivot">Pivot berdasarkan</label>
          <select class="select" id="stats-pivot" name="pivot_by">${pivotOpts}</select>
        </div>
        <div class="field">
          <label for="stats-metric">Metrik hitungan</label>
          <div class="segmented" id="stats-metric-segmented">
            ${METRIC_OPTIONS.map(([val, lbl]) => `<button type="button" class="btn-seg ${query.metric === val ? 'active' : ''}" data-metric="${val}" aria-pressed="${query.metric === val}">${esc(lbl)}</button>`).join('')}
          </div>
        </div>
        <div class="field">
          <label for="stats-chart">Tipe visualisasi</label>
          <div class="segmented" id="stats-chart-segmented">
            ${CHART_OPTIONS.map(([val, lbl]) => `<button type="button" class="btn-seg ${query.chart === val ? 'active' : ''}" data-chart="${val}" aria-pressed="${query.chart === val}">${esc(lbl)}</button>`).join('')}
          </div>
        </div>
        <div class="field">
          <label for="stats-top-n">Batas kategori</label>
          <select class="select" id="stats-top-n" name="top_n">${topNOpts}</select>
        </div>
        <div class="field">
          <label for="stats-time">Rentang waktu</label>
          <select class="select" id="stats-time" name="time_preset">${timePresets}</select>
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
  `;
}

export function statsResults(data, query) {
  const total = Number(data.total) || 0;
  const metricLabel = data.metric === 'events' ? 'event' : 'alert';
  const otherCount = Number(data.other_count) || 0;
  const otherPct = Number(data.other_percentage) || 0;
  const items = distributionPercentages(data.items || [], otherCount, total);

  let chartHtml = '';
  if (query.chart === 'bar') {
    chartHtml = renderBarChart({items, otherCount, otherPercentage: otherPct, total, metric: data.metric});
  } else if (query.chart === 'donut') {
    chartHtml = renderDonutChart({items, otherCount, otherPercentage: otherPct, total, metric: data.metric});
  } else if (query.chart === 'line') {
    chartHtml = renderLineChart({timeSeries: data.time_series || [], topKeys: items.map(it => it.key), metric: data.metric});
  }

  const tableRows = items.map(item => {
    const keyEsc = esc(item.key);
    const triageUrl = triageRouteFromStats(query, {facet: data.pivot_by, facet_value: item.key});
    return `
      <tr>
        <td class="mono font-medium">${keyEsc}</td>
        <td class="numeric">${item.count.toLocaleString('id-ID')}</td>
        <td class="numeric">${item.displayPercentage}%</td>
        <td class="actions-col" style="text-align:right;">
          <button type="button" class="button text-button" data-drill-key="${keyEsc}" title="Saring statistik hanya ke kategori ini">Drill-down</button>
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
      </div>
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
      <section class="panel chart-container" style="margin-bottom:20px; overflow-x:auto;">
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
  `;
}
