import {esc, icon, severity, formatTime, emptyState, errorState, loadingRows} from '../../ui/primitives.js';
import {withParams} from '../../router.js';
import {REVIEW_DATE_PRESETS, localDateInputValue, reviewDateLabel, tenantValues} from '../../state/scope.js';
import {
  FLAG_TABS,
  RULE_STATUS_FILTERS,
  FLAG_GROUP_BY_OPTIONS,
  FLAG_EXPORT_FORMATS,
  flagMeta,
  flagBadge,
  ruleStatusBadge,
} from './model.js';

function alertUrlPreview(alert) {
  return String(
    alert?.data?.url || alert?.data?.uri || alert?.parsed_details?.uri || alert?.parsed_details?.path || '',
  ).trim();
}

function triageLinkFor(query, alert) {
  const params = new URLSearchParams();
  const tenants = tenantValues(query);
  for (const t of tenants) params.append('tenant', t);
  if (alert?.id) params.set('alert_ids', String(alert.id));
  if (alert?.id) params.set('alert', String(alert.id));
  params.set('review_status', 'all');
  return withParams('/triage', params);
}

function renderAlertDetailRows(query, items, {expandedLogIds = new Set()} = {}) {
  if (!items.length) {
    return '<p class="meta">Tidak ada alert pada grup pola ini untuk filter status saat ini.</p>';
  }
  const showRuleCol = query.flag_color !== 'red';
  const rows = items.map(a => {
    const id = Number(a.id);
    const url = alertUrlPreview(a);
    const isLogOpen = expandedLogIds.has(id);
    const fullLog = a.full_log || 'Full log tidak tersedia.';
    const ruleDone = a.rule_status === 'done';
    const currentFlag = String(a.flag_color || query.flag_color || 'green').toLowerCase();
    const auditRule = ruleDone && a.rule_updated_by
      ? `<div class="meta">oleh @${esc(a.rule_updated_by)}${a.rule_updated_at ? ` · ${esc(formatTime(a.rule_updated_at))}` : ''}${a.rule_notes ? `<br>${esc(a.rule_notes)}` : ''}</div>`
      : '';
    const mainRow = `<tr data-flag-alert-row="${id}">
      <td><time datetime="${esc(a.timestamp || '')}" class="meta num">${esc(formatTime(a.timestamp))}</time></td>
      <td>${severity(a.rule_level)}</td>
      <td>
        <strong>${esc(a.description || 'Alert tanpa deskripsi')}</strong>
        <div class="meta">${esc(a.tenant || 'Default')} · ${esc(a.agent_name || '—')} · Rule ${esc(a.rule_id || '—')} · <span class="num">${Number(a.hit_count) || 1} hits</span></div>
        ${url ? `<div class="meta mono" style="word-break:break-all">${esc(url)}</div>` : ''}
      </td>
      <td><span class="mono">${esc(a.source_ip || '—')}</span></td>
      <td>
        ${flagBadge(currentFlag, {compact: true})}
        <div class="meta">oleh @${esc(a.flagged_by || 'analyst')}${a.flagged_at ? ` · ${esc(formatTime(a.flagged_at))}` : ''}</div>
        <label class="sr-only" for="alert-flag-select-${id}">Ubah flag alert ${id}</label>
        <select class="select" id="alert-flag-select-${id}" data-change-alert-flag="${id}" style="margin-top:4px;min-height:28px;font-size:12px;padding:2px 6px;">
          <option value="green" ${currentFlag === 'green' ? 'selected' : ''}>Hijau</option>
          <option value="yellow" ${currentFlag === 'yellow' ? 'selected' : ''}>Kuning</option>
          <option value="red" ${currentFlag === 'red' ? 'selected' : ''}>Merah</option>
          <option value="">— Hapus Flag (Unflag) —</option>
        </select>
      </td>
      ${showRuleCol ? `<td>
        ${ruleStatusBadge(a)}
        ${auditRule}
        <div style="display:flex;gap:6px;flex-wrap:wrap;margin-top:6px;">
          ${ruleDone
            ? `<button type="button" class="button text-button meta" data-action="revert-alert-rule" data-alert-id="${id}">Kembalikan pending</button>`
            : `<button type="button" class="button" style="min-height:28px;font-size:12px;padding:2px 8px;" data-action="open-alert-rule-modal" data-alert-id="${id}">${icon('check')}Tandai Rule Dibuat</button>`}
        </div>
      </td>` : ''}
      <td>
        <div style="display:flex;gap:6px;flex-wrap:wrap;">
          <button type="button" class="button text-button meta" data-action="toggle-flag-log" data-alert-id="${id}" aria-expanded="${isLogOpen}">[${isLogOpen ? 'Tutup Log' : 'Log'}]</button>
          <a class="button text-button meta" href="${esc(triageLinkFor(query, a))}">Buka di Triage</a>
          <button type="button" class="button text-button meta" data-action="unflag-alert" data-alert-id="${id}" title="Hapus Flag alert ini (status review tetap)">Hapus Flag</button>
          <button type="button" class="button text-button meta" data-action="unreview-alert" data-alert-id="${id}" title="Kembalikan ke Belum direview dan hapus Flag">Belum direview</button>
        </div>
      </td>
    </tr>`;
    const colSpan = showRuleCol ? 7 : 6;
    const logRow = isLogOpen ? `<tr class="log-expansion-row"><td colspan="${colSpan}" class="log-expansion-cell"><div class="queue-log-box flag-inline-log stack"><div class="split queue-log-head"><span class="meta mono">Log Alert #${esc(a.alert_id || a.id)}</span><button type="button" class="button text-button meta" data-action="copy-flag-log" data-alert-id="${id}">${icon('copy')}Salin log</button></div><pre class="raw-log">${esc(fullLog)}</pre></div></td></tr>` : '';
    return mainRow + logRow;
  }).join('');

  return `<div class="table-region"><table class="data-table">
    <thead>
      <tr>
        <th style="width:110px">Waktu</th>
        <th style="width:94px">Severity</th>
        <th>Deskripsi / Asset / URL</th>
        <th style="width:130px">Source IP</th>
        <th style="width:150px">Flag &amp; Auditor</th>
        ${showRuleCol ? '<th style="width:190px">Status Custom Rule</th>' : ''}
        <th style="width:150px">Aksi</th>
      </tr>
    </thead>
    <tbody>${rows}</tbody>
  </table></div>`;
}

export function renderFlagGroups(query, data, {
  expandedGroups = new Set(),
  groupAlertsCache = new Map(),
  expandedLogIds = new Set(),
  selectedGroupKeys = new Set(),
  exportPending = false,
  exportStatus = '',
  exportCount = null,
} = {}) {
  const groups = Array.isArray(data?.groups) ? data.groups : [];
  if (data?.pattern_required) {
    return emptyState(
      'Masukkan pola teks atau regex',
      'Pilih atau ketik substring maupun ekspresi regex pada kolom Pola teks di atas, lalu tekan Terapkan Pola untuk mengelompokkan alert.',
    );
  }
  if (!groups.length) {
    return emptyState(
      'Belum ada alert pada kategori Flag ini',
      query.rule_status === 'pending' && query.flag_color !== 'red'
        ? 'Tidak ada pola yang menunggu pembuatan custom rule pada filter ini. Coba tab Sudah Dibuat Rule atau tandai alert baru dari Triage.'
        : 'Tandai alert hasil review di Triage dengan Flag Hijau, Kuning, atau Merah untuk mengelompokkannya di sini.',
      `<a class="button primary" href="#/triage">${icon('inbox')}Buka Triage</a>`,
    );
  }

  const isRed = query.flag_color === 'red';
  const selectedCount = selectedGroupKeys.size;
  const exportButtons = FLAG_EXPORT_FORMATS.map(([format, label]) =>
    `<button class="button" type="button" data-flag-export="${format}" ${exportPending ? 'disabled' : ''}>${esc(label)}</button>`
  ).join('');
  const countText = exportCount === null
    ? 'Menghitung alert dalam scope ekspor…'
    : `<strong class="num">${Number(exportCount).toLocaleString('id-ID')}</strong> alert siap diekspor`;
  const exportBar = `<section class="flag-export-bar panel stack" aria-label="Ekspor alert Flag">
    <div class="split" style="align-items:flex-start;gap:12px;flex-wrap:wrap;">
      <div>
        <h2 class="section-heading">Ekspor Flag</h2>
        <p class="meta">${selectedCount ? `<strong>${selectedCount.toLocaleString('id-ID')} grup dipilih</strong> · ` : 'Tanpa centang = seluruh alert pada kategori ini · '}${countText}</p>
      </div>
      <div class="page-actions" style="flex-wrap:wrap;">
        <button class="button" type="button" data-action="flag-select-all">Pilih semua grup</button>
        <button class="button" type="button" data-action="flag-select-none" ${selectedCount ? '' : 'disabled'}>Kosongkan pilihan</button>
        <details class="format-menu"><summary class="button primary">${icon('down')} Ekspor / Salin</summary><div class="stack" aria-label="Format ekspor Flag">${exportButtons}</div></details>
      </div>
    </div>
    <p class="inline-status" id="flag-export-status" role="status" aria-live="polite">${esc(exportStatus)}</p>
  </section>`;

  return `${exportBar}<div class="flag-group-list">${groups.map((group, index) => {
    const key = String(group.key ?? '');
    const isExpanded = expandedGroups.has(key);
    const cached = groupAlertsCache.get(key);
    const count = Number(group.alert_count || 0).toLocaleString('id-ID');
    const hits = Number(group.event_hits || 0).toLocaleString('id-ID');
    const rangeText = group.earliest || group.latest
      ? `${group.earliest ? esc(formatTime(group.earliest)) : '—'} s/d ${group.latest ? esc(formatTime(group.latest)) : 'kini'}`
      : 'Rentang waktu tidak tersedia';
    const flaggedEarliest = group.flagged_earliest || '';
    const flaggedLatest = group.flagged_latest || '';
    const flaggedText = flaggedEarliest || flaggedLatest
      ? `<span>Ditandai ${flaggedEarliest && flaggedLatest && flaggedEarliest !== flaggedLatest
          ? `${esc(formatTime(flaggedEarliest))} s/d ${esc(formatTime(flaggedLatest))}`
          : esc(formatTime(flaggedLatest || flaggedEarliest))}</span>`
      : '';
    const doneAudit = group.rule_status !== 'pending' && group.rule_updated_by
      ? `<span>Rule ditandai oleh <strong>@${esc(group.rule_updated_by)}</strong>${group.rule_updated_at ? ` · ${esc(formatTime(group.rule_updated_at))}` : ''}${group.rule_notes ? ` — “${esc(group.rule_notes)}”` : ''}</span>`
      : '';
    const actionsHTML = isRed
      ? `<span class="meta">Tidak boleh diabaikan dengan custom rule</span>
         <button type="button" class="button" data-action="unflag-group" data-group-index="${index}" title="Hapus Flag semua alert pada grup ini">Hapus Flag Grup</button>
         <button type="button" class="button" data-action="unreview-group" data-group-index="${index}" title="Kembalikan semua alert pada grup ini ke Belum direview dan hapus Flag">Belum direview</button>`
      : `
        ${group.rule_status !== 'done'
          ? `<button type="button" class="button primary" data-action="open-group-rule-modal" data-group-index="${index}">${icon('check')}Tandai Rule Dibuat (${Number(group.pending_count ?? group.alert_count).toLocaleString('id-ID')})</button>`
          : ''}
        ${group.rule_status === 'done' || group.rule_status === 'partial'
          ? `<button type="button" class="button" data-action="revert-group-rule" data-group-index="${index}">Kembalikan Pending</button>`
          : ''}
        <button type="button" class="button" data-action="unflag-group" data-group-index="${index}" title="Hapus Flag semua alert pada grup ini">Hapus Flag Grup</button>
        <button type="button" class="button" data-action="unreview-group" data-group-index="${index}" title="Kembalikan semua alert pada grup ini ke Belum direview dan hapus Flag">Belum direview</button>
      `;

    let bodyHTML = '';
    if (isExpanded) {
      if (!cached || cached.loading) {
        bodyHTML = loadingRows(2);
      } else if (cached.error) {
        bodyHTML = `${errorState(cached.error)}`;
      } else {
        const items = cached.items || [];
        const moreNote = Number(cached.total || items.length) > items.length
          ? `<p class="meta" style="margin-top:8px">Menampilkan ${items.length.toLocaleString('id-ID')} dari ${Number(cached.total).toLocaleString('id-ID')} alert dalam grup pola ini.</p>`
          : '';
        bodyHTML = `${renderAlertDetailRows(query, items, {expandedLogIds})}${moreNote}`;
      }
    }

    return `<article class="flag-group-card" data-group-index="${index}">
      <div class="flag-group-head">
        <label class="flag-group-select" title="Pilih grup ini untuk diekspor">
          <input type="checkbox" data-select-group-index="${index}" ${selectedGroupKeys.has(key) ? 'checked' : ''} aria-label="Pilih grup ${esc(key)} untuk diekspor">
        </label>
        <button type="button" class="flag-group-toggle" data-action="toggle-group" data-group-index="${index}" aria-expanded="${isExpanded}">
          ${icon('chevron')}
          <div style="min-width:0">
            <div class="flag-group-title">${esc(key)}</div>
            <div class="flag-group-meta">
              <span><strong class="num">${count}</strong> alert · <span class="num">${hits}</span> hits</span>
              <span>${rangeText}</span>
              ${flaggedText}
              ${!isRed ? ruleStatusBadge(group) : ''}
              ${doneAudit}
            </div>
          </div>
        </button>
        <div class="flag-group-actions">${actionsHTML}</div>
      </div>
      ${isExpanded ? `<div class="flag-group-body">${bodyHTML}</div>` : ''}
    </article>`;
  }).join('')}</div>`;
}

export function renderFlagsPage(query, data = null, state = {}) {
  const counts = data?.counts || {
    green: {total: 0, pending: 0, done: 0},
    yellow: {total: 0, pending: 0, done: 0},
    red: {total: 0, pending: 0, done: 0},
  };
  const activeMeta = flagMeta(query.flag_color) || FLAG_TABS[0];
  const isRed = query.flag_color === 'red';

  const tabsHTML = FLAG_TABS.map(tab => {
    const stat = counts[tab.key] || {total: 0, pending: 0, done: 0};
    const countLabel = tab.key === 'red'
      ? Number(stat.total || 0).toLocaleString('id-ID')
      : `${Number(stat.pending || 0).toLocaleString('id-ID')} pending / ${Number(stat.total || 0).toLocaleString('id-ID')}`;
    const selected = query.flag_color === tab.key;
    return `<button type="button" class="flag-tab" role="tab" data-flag-tab="${tab.key}" aria-selected="${selected}" title="${esc(tab.description)}">
      ${icon('flag')}
      <span>${esc(tab.label)} · ${esc(tab.title)}</span>
      <span class="flag-tab-count num">${esc(countLabel)}</span>
    </button>`;
  }).join('');

  const ruleFiltersHTML = !isRed
    ? `<div class="flag-rule-filters" role="group" aria-label="Filter status custom rule">
        ${RULE_STATUS_FILTERS.map(([val, label]) => `<button type="button" class="button" data-rule-status="${val}" aria-pressed="${query.rule_status === val}">${esc(label)}</button>`).join('')}
      </div>`
    : '<span class="meta">Tab Merah menampilkan semua alert kritis prioritas (pembuatan rule pengabaian dinonaktifkan).</span>';

  const groupOptions = FLAG_GROUP_BY_OPTIONS.map(([val, label]) =>
    `<option value="${val}" ${query.group_by === val ? 'selected' : ''}>${esc(label)}</option>`
  ).join('');
  const activeReviewPreset = query.reviewed_preset || ((query.reviewed_from || query.reviewed_to) ? 'custom' : '');
  const reviewPresetOptions = REVIEW_DATE_PRESETS.map(([val, label]) =>
    `<option value="${esc(val)}" ${activeReviewPreset === val ? 'selected' : ''}>${esc(label)}</option>`
  ).join('');
  const activeReviewLabel = reviewDateLabel(query);
  const currentUser = state.currentUser || null;
  const isAnalyst = currentUser?.role === 'analyst';

  const noticeKind = isRed ? 'warning' : 'info';
  const resultsContent = state.error
    ? errorState(state.error)
    : state.loading && !data
    ? loadingRows(4)
    : renderFlagGroups(query, data, state);

  return `
    <header class="page-header">
      <div class="page-heading">
        <h1>Flag &amp; Rule Tuning Tracker</h1>
        <p class="page-description">Kelompokkan alert ber-flag menurut pola atribut untuk mempercepat pembuatan custom rule Wazuh dan mencegah tuning ganda.</p>
      </div>
      <div class="page-actions">
        <button class="button" type="button" data-action="refresh-flags">${icon('refresh')}Muat Ulang</button>
        <a class="button" href="#/triage">${icon('inbox')}Kembali ke Triage</a>
      </div>
    </header>

    <div class="flag-tabs" role="tablist" aria-label="Kategori warna Flag">${tabsHTML}</div>

    <div class="notice" data-kind="${noticeKind}" style="margin-bottom:14px;">
      <p><strong>Flag ${esc(activeMeta.label)} (${esc(activeMeta.title)}):</strong> ${esc(activeMeta.description)}${isAnalyst ? ` <span class="meta">· Menampilkan alert Flag milik akun Anda (@${esc(currentUser.username)}).</span>` : ''}</p>
    </div>

    <div class="flag-filter-bar">
      ${ruleFiltersHTML}
      <span class="meta">${data && !data.pattern_required ? `<strong class="num">${Number(data.total_groups || 0).toLocaleString('id-ID')}</strong> grup pola · <strong class="num">${Number(data.total_alerts || 0).toLocaleString('id-ID')}</strong> alert${activeReviewLabel ? ` · Filter waktu review: <strong>${esc(activeReviewLabel)}</strong>` : ''}` : ''}</span>
    </div>

    <section class="flag-controls" aria-label="Kontrol pengelompokan pola">
      <div class="field">
        <label for="flag-group-by">Kelompokkan berdasarkan</label>
        <select class="select" id="flag-group-by" name="group_by">${groupOptions}</select>
      </div>
      <div class="field">
        <label for="flag-review-preset">Waktu review</label>
        <select class="select" id="flag-review-preset" name="reviewed_preset">${reviewPresetOptions}</select>
      </div>
      <div class="flag-pattern-controls" id="flag-review-custom" style="display:${activeReviewPreset === 'custom' ? 'flex' : 'none'}">
        <div class="field">
          <label for="flag-reviewed-from">Dari</label>
          <input class="input" id="flag-reviewed-from" type="date" value="${esc(localDateInputValue(query.reviewed_from))}">
        </div>
        <div class="field">
          <label for="flag-reviewed-to">Sampai</label>
          <input class="input" id="flag-reviewed-to" type="date" value="${esc(localDateInputValue(query.reviewed_to))}">
        </div>
        <button class="button primary" type="button" data-action="flag-apply-reviewed-date">Terapkan</button>
        ${(query.reviewed_from || query.reviewed_to || query.reviewed_preset) ? '<button class="button text-button" type="button" data-action="flag-clear-reviewed-date">Reset</button>' : ''}
      </div>
      <div class="flag-pattern-controls" id="flag-pattern-wrap" style="display:${query.group_by === 'pattern' ? 'flex' : 'none'}">
        <div class="field">
          <label for="flag-pattern-input">Pola teks / payload</label>
          <input class="input mono" id="flag-pattern-input" type="search" value="${esc(query.pattern)}" placeholder="Contoh: createthumb.php atau GET /wp-login" maxlength="120" autocomplete="off" spellcheck="false">
        </div>
        <div class="field" style="flex:0 1 140px">
          <label for="flag-pattern-mode">Mode</label>
          <select class="select" id="flag-pattern-mode">
            <option value="contains" ${query.pattern_mode === 'contains' ? 'selected' : ''}>Substring</option>
            <option value="regex" ${query.pattern_mode === 'regex' ? 'selected' : ''}>Regex</option>
          </select>
        </div>
        <button class="button primary" type="button" data-action="apply-pattern">Terapkan Pola</button>
      </div>
      <div class="field search-field">
        <label for="flag-search">Cari di dalam Flag</label>
        ${icon('search')}
        <input class="input" id="flag-search" type="search" value="${esc(query.q)}" placeholder="Cari IP, rule ID, catatan…" autocomplete="off" spellcheck="false">
      </div>
    </section>

    <section id="flag-groups-region" aria-live="polite">${resultsContent}</section>

    <dialog class="app-dialog" id="flag-rule-dialog" aria-labelledby="flag-rule-dialog-title">
      <div class="dialog-header">
        <h2 id="flag-rule-dialog-title">Tandai Custom Rule Sudah Dibuat</h2>
        <button class="button icon-button" type="button" data-close-flag-rule aria-label="Tutup dialog">${icon('close')}</button>
      </div>
      <form id="flag-rule-form" class="stack">
        <p class="meta" id="flag-rule-target-desc"></p>
        <div class="field">
          <label for="flag-custom-rule-id">Nomor Custom Rule Wazuh (opsional)</label>
          <input class="input mono" id="flag-custom-rule-id" name="custom_rule_id" type="text" maxlength="50" placeholder="Contoh: 100145" autocomplete="off" spellcheck="false">
        </div>
        <div class="field">
          <label for="flag-rule-notes">Catatan konfigurasi / alasan tuning (opsional)</label>
          <textarea class="input" id="flag-rule-notes" name="rule_notes" rows="3" maxlength="1000" placeholder="Contoh: Whitelist crawler kampus / pengecualian path static"></textarea>
        </div>
        <p class="inline-status" id="flag-rule-dialog-status" role="status" aria-live="polite"></p>
        <div class="dialog-actions">
          <button type="button" class="button" data-close-flag-rule>Batal</button>
          <button type="submit" class="button primary">${icon('check')}Simpan Status Rule Dibuat</button>
        </div>
      </form>
    </dialog>
  `;
}

