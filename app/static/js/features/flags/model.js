import {esc, icon} from '../../ui/primitives.js';
import {choices, tenantScope, tenantValues} from '../../state/scope.js';

export const FLAG_TABS = [
  {
    key: 'green',
    label: 'Hijau',
    title: 'Kandidat Pengecualian',
    description: 'False positive atau aktivitas rutin yang layak dibuatkan custom rule pengabaian di Wazuh.',
    badgeClass: 'flag-green',
    buttonClass: 'flag-btn-green',
  },
  {
    key: 'yellow',
    label: 'Kuning',
    title: 'Perlu Pemantauan',
    description: 'Aktivitas mencurigakan atau borderline yang membutuhkan pemantauan pola lanjutan sebelum diputuskan pengecualian atau eskalasi.',
    badgeClass: 'flag-yellow',
    buttonClass: 'flag-btn-yellow',
  },
  {
    key: 'red',
    label: 'Merah',
    title: 'Tidak Diabaikan',
    description: 'Ancaman nyata (True Positive) atau pola kritis yang wajib ditindaklanjuti atau dilaporkan dan tidak boleh diabaikan dengan custom rule.',
    badgeClass: 'flag-red',
    buttonClass: 'flag-btn-red',
  },
];

const FLAG_META_MAP = Object.fromEntries(FLAG_TABS.map(tab => [tab.key, tab]));

export const RULE_STATUS_FILTERS = [
  ['all', 'Semua'],
  ['pending', 'Belum Dibuat Rule'],
  ['done', 'Sudah Dibuat Rule'],
];

export const FLAG_GROUP_BY_OPTIONS = [
  ['rule_description', 'Deskripsi rule'],
  ['rule_id', 'Rule ID'],
  ['severity', 'Severity level'],
  ['source_ip', 'Source IP'],
  ['agent', 'Host / Agent'],
  ['http_status', 'HTTP status code'],
  ['http_method', 'HTTP Method'],
  ['url_path', 'URL / Path'],
  ['referer', 'HTTP Referer'],
  ['user_agent', 'User-Agent'],
  ['pattern', 'Pola teks tertentu'],
  ['tenant', 'Tenant'],
];

const GROUP_KEYS = FLAG_GROUP_BY_OPTIONS.map(([key]) => key);

export function flagMeta(color) {
  const key = String(color || '').trim().toLowerCase();
  return FLAG_META_MAP[key] || null;
}

export function flagBadge(color, {compact = false} = {}) {
  const meta = flagMeta(color);
  if (!meta) return '';
  const text = compact ? meta.label : `Flag ${meta.label} · ${meta.title}`;
  return `<span class="badge ${meta.badgeClass}" title="${esc(meta.description)}"><span class="status-dot" aria-hidden="true"></span>${esc(text)}</span>`;
}

export function ruleStatusBadge(item) {
  if (!item || item.flag_color === 'red' || item.rule_status === 'none') return '';
  if (item.rule_status === 'done') {
    const rid = item.custom_rule_id ? ` (#${esc(item.custom_rule_id)})` : '';
    return `<span class="badge flag-rule-badge-done">${icon('check')}Rule Dibuat${rid}</span>`;
  }
  if (item.rule_status === 'partial') {
    return `<span class="badge medium">Sebagian (${Number(item.done_count || 0).toLocaleString('id-ID')}/${Number(item.alert_count || 0).toLocaleString('id-ID')})</span>`;
  }
  return '<span class="badge flag-rule-badge-pending">Belum Dibuat Rule</span>';
}

export function normalizeFlagQuery(params = new URLSearchParams()) {
  const get = key => (params instanceof URLSearchParams ? params.get(key) : params?.[key]);
  const scope = tenantScope(params);
  const flag_color = choices(get('flag_color'), ['green', 'yellow', 'red'], 'green');
  const rule_status = flag_color === 'red'
    ? 'all'
    : choices(get('rule_status'), ['all', 'pending', 'done'], 'pending');
  return {
    tenant: scope.all ? 'all' : scope.tenants[0],
    tenants: scope.tenants,
    tenantScope: scope,
    flag_color,
    rule_status,
    group_by: choices(get('group_by'), GROUP_KEYS, 'rule_description'),
    pattern: String(get('pattern') || ''),
    pattern_mode: choices(get('pattern_mode'), ['contains', 'regex'], 'contains'),
    q: String(get('q') || ''),
  };
}

export function flagScopeParams(query) {
  const normalized = query?.tenantScope ? query : normalizeFlagQuery(query);
  const params = new URLSearchParams();
  for (const tenant of tenantValues(normalized)) params.append('tenant', tenant);
  params.set('flag_color', normalized.flag_color);
  params.set('rule_status', normalized.rule_status);
  params.set('group_by', normalized.group_by);
  if (normalized.pattern) params.set('pattern', normalized.pattern);
  if (normalized.pattern_mode && normalized.pattern_mode !== 'contains') {
    params.set('pattern_mode', normalized.pattern_mode);
  }
  if (normalized.q) params.set('q', normalized.q);
  return params;
}

export const FLAG_EXPORT_FORMATS = [
  ['copy-html', 'Salin untuk Google Docs'],
  ['report-html', 'Unduh HTML'],
  ['docx', 'Unduh Word (.docx)'],
  ['xlsx', 'Unduh Excel (.xlsx)'],
  ['tsv', 'Unduh TSV'],
  ['copy-tsv', 'Salin TSV (spreadsheet)'],
  ['markdown', 'Unduh Markdown'],
  ['copy-markdown', 'Salin Markdown'],
  ['csv', 'Unduh CSV'],
];

const FLAG_EXPORT_KEYS = new Set(FLAG_EXPORT_FORMATS.map(([key]) => key));

export function flagExportFormat(value) {
  const action = String(value || '');
  if (!FLAG_EXPORT_KEYS.has(action)) throw new Error('Format ekspor Flag tidak dikenal.');
  if (action === 'copy-html') return 'report-html';
  return action.startsWith('copy-') ? action.slice(5) : action;
}

export function flagExportParams(query, groupKeys = []) {
  const params = flagScopeParams(query);
  for (const key of groupKeys) {
    if (key === null || key === undefined || String(key) === '') continue;
    params.append('group_key', String(key));
  }
  return params;
}

export function flagExportURL(query, groupKeys, format) {
  return `/api/flags/export/${flagExportFormat(format)}?${flagExportParams(query, groupKeys)}`;
}

