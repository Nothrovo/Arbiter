import {filtersValue, parseFilters} from './filters.js';

export const choices = (value, allowed, fallback) => allowed.includes(value) ? value : fallback;
export const integer = (value, fallback) => Number.isFinite(Number(value)) ? Math.floor(Number(value)) : fallback;

const DAY_MS = 86400000;

export const REVIEW_DATE_PRESETS = [
  ['', 'Semua waktu review'],
  ['today', 'Hari ini'],
  ['yesterday', 'Kemarin'],
  ['exclude_1d', 'Sebelum hari ini (tanpa hari ini)'],
  ['exclude_2d', '≥ 2 hari lalu (tanpa hari ini & kemarin)'],
  ['exclude_3d', '> 2 hari lalu (tanpa 3 hari terakhir)'],
  ['exclude_7d', '> 7 hari lalu'],
  ['custom', 'Rentang tanggal kustom…'],
];

const REVIEW_PRESET_KEYS = REVIEW_DATE_PRESETS.map(([key]) => key);

export function localDateInputValue(isoValue) {
  const raw = String(isoValue || '').trim();
  if (!raw) return '';
  if (/^\d{4}-\d{2}-\d{2}$/.test(raw)) return raw;
  const date = new Date(raw);
  if (Number.isNaN(date.getTime())) return '';
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, '0');
  const d = String(date.getDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
}

export function localDayBoundsFromDateInput(dateStr, boundary = 'start') {
  const match = String(dateStr || '').trim().match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (!match) return '';
  const [, y, m, d] = match;
  if (boundary === 'end') {
    return new Date(Number(y), Number(m) - 1, Number(d), 23, 59, 59, 999).toISOString();
  }
  return new Date(Number(y), Number(m) - 1, Number(d), 0, 0, 0, 0).toISOString();
}

export function reviewDateRangeForPreset(preset, now = new Date()) {
  const key = String(preset || '').trim();
  const startOfToday = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 0, 0, 0, 0);
  const endOfToday = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 23, 59, 59, 999);
  if (key === 'today') {
    return {reviewed_from: startOfToday.toISOString(), reviewed_to: endOfToday.toISOString()};
  }
  if (key === 'yesterday') {
    const startOfYesterday = new Date(startOfToday.getTime() - DAY_MS);
    const endOfYesterday = new Date(startOfToday.getTime() - 1);
    return {reviewed_from: startOfYesterday.toISOString(), reviewed_to: endOfYesterday.toISOString()};
  }
  if (key === 'exclude_1d') {
    return {reviewed_from: '', reviewed_to: new Date(startOfToday.getTime() - 1).toISOString()};
  }
  if (key === 'exclude_2d') {
    return {reviewed_from: '', reviewed_to: new Date(startOfToday.getTime() - DAY_MS - 1).toISOString()};
  }
  if (key === 'exclude_3d') {
    return {reviewed_from: '', reviewed_to: new Date(startOfToday.getTime() - 2 * DAY_MS - 1).toISOString()};
  }
  if (key === 'exclude_7d') {
    return {reviewed_from: '', reviewed_to: new Date(startOfToday.getTime() - 7 * DAY_MS - 1).toISOString()};
  }
  return {reviewed_from: '', reviewed_to: ''};
}

export function reviewDateLabel(query = {}) {
  const preset = String(query?.reviewed_preset || '').trim();
  const from = localDateInputValue(query?.reviewed_from);
  const to = localDateInputValue(query?.reviewed_to);
  if (preset && preset !== 'custom') {
    const match = REVIEW_DATE_PRESETS.find(([k]) => k === preset);
    if (match) return to && preset.startsWith('exclude_') ? `${match[1]} (≤ ${to})` : match[1];
  }
  if (from && to) return from === to ? `Tanggal ${from}` : `${from} s/d ${to}`;
  if (from) return `Sejak ${from}`;
  if (to) return `Sampai ${to}`;
  return '';
}

function rawTenantValues(params) {
  if (typeof params === 'string') return [params];
  if (Array.isArray(params)) return params;
  if (params instanceof URLSearchParams) return params.has('tenant') ? params.getAll('tenant') : ['all'];
  if (params && Array.isArray(params.tenants)) return params.tenants.length ? params.tenants : ['all'];
  if (params && Object.hasOwn(params, 'tenant')) return Array.isArray(params.tenant) ? params.tenant : [params.tenant];
  return ['all'];
}

export function tenantScope(params = new URLSearchParams()) {
  const raw = rawTenantValues(params).map(value => String(value ?? '').trim());
  if (raw.some(value => !value)) throw new Error('Tenant tidak boleh kosong. Pilih scope tenant kembali.');
  const unique = [...new Set(raw)].sort((a, b) => a < b ? -1 : a > b ? 1 : 0);
  if (unique.includes('all')) {
    if (unique.length !== 1) throw new Error('Semua tenant tidak dapat digabungkan dengan tenant bernama.');
    return {all: true, tenants: [], key: 'all', label: 'Semua tenant'};
  }
  const tenants = unique;
  return {all: false, tenants, key: JSON.stringify(tenants), label: tenants.length === 1 ? `Tenant ${tenants[0]}` : `${tenants.length} tenant`};
}

export function tenantValues(params = new URLSearchParams()) {
  const scope = tenantScope(params);
  return scope.all ? ['all'] : scope.tenants;
}

export function queryFrom(params = new URLSearchParams()) {
  const get = key => params instanceof URLSearchParams ? params.get(key) : params?.[key];
  const scope = tenantScope(params);
  return {
    tenant: scope.all ? 'all' : scope.tenants[0], tenants: scope.tenants, tenantScope: scope,
    q: get('q') || '',
    review_status: choices(get('review_status'), ['all', 'reviewed', 'unreviewed'], 'unreviewed'),
    filter_preset: choices(get('filter_preset'), ['', '403', '404', 'repeating', 'non_http', 'bot', 'curl'], ''),
    status: choices(get('status'), ['all', 'grouped', 'ungrouped'], 'all'),
    group_id: get('group_id') || '',
    alert_ids: get('alert_ids') || '',
    facet: get('facet') || '',
    facet_value: get('facet_value') || '',
    secondary_facet: get('secondary_facet') || '',
    secondary_facet_value: get('secondary_facet_value') || '',
    filters: parseFilters(get('filters')),
    sort_by: choices(get('sort_by'), ['timestamp', 'severity', 'hits'], 'timestamp'),
    sort: choices(get('sort'), ['asc', 'desc'], 'desc'),
    time_from: get('time_from') || '',
    time_to: get('time_to') || '',
    time_preset: get('time_preset') || '',
    reviewed_preset: choices(get('reviewed_preset') || '', REVIEW_PRESET_KEYS, ''),
    reviewed_from: get('reviewed_from') || '',
    reviewed_to: get('reviewed_to') || '',
    reviewer: get('reviewer') || '',
    limit: Math.min(10000, Math.max(1, integer(get('limit'), 50) || 50)),
    offset: Math.max(0, integer(get('offset'), 0) || 0),
  };
}

export function scopeParams(query, {ids, groupId} = {}) {
  const normalized = queryFrom(query instanceof URLSearchParams ? query : query || {});
  const params = new URLSearchParams();
  for (const tenant of tenantValues(normalized)) params.append('tenant', tenant);
  for (const [key, value] of Object.entries(normalized)) {
    if (!['tenant', 'tenants', 'tenantScope', 'limit', 'offset', 'filters'].includes(key) && value !== '') params.set(key, String(value));
  }
  if (normalized.filters?.length) params.set('filters', filtersValue(normalized.filters));
  if (groupId) {
    params.set('group_id', groupId);
    for (const key of ['q', 'filter_preset', 'status']) params.delete(key);
    params.set('review_status', 'all');
  }
  if (ids !== undefined) {
    if (!Array.isArray(ids) || !ids.length || ids.some(id => !(/^[1-9]\d*$/.test(String(id))))) throw new Error('Pilihan alert tidak valid. Pilih ulang sebelum mengekspor.');
    const clean = [...new Set(ids.map(Number))].filter(Number.isSafeInteger).filter(id => id > 0);
    if (clean.length !== new Set(ids.map(Number)).size) throw new Error('Pilihan alert tidak valid. Pilih ulang sebelum mengekspor.');
    for (const key of ['q', 'review_status', 'filter_preset', 'status', 'group_id', 'filters']) params.delete(key);
    params.set('alert_ids', clean.join(','));
  }
  return params;
}

export function scopeDescription(params) {
  const p = params instanceof URLSearchParams ? params : scopeParams(params);
  const scope = tenantScope(p);
  const parts = [scope.label];
  if (p.get('alert_ids')) parts.push(`${p.get('alert_ids').split(',').length} alert terpilih`);
  else {
    if (p.get('group_id')) parts.push('Insiden terpilih');
    if (p.get('q')) parts.push(`Pencarian: ${p.get('q')}`);
    if (p.get('review_status') === 'unreviewed') parts.push('Belum direview');
    if (p.get('review_status') === 'reviewed') parts.push('Sudah direview');
    if (p.get('filter_preset')) parts.push(`Filter ${p.get('filter_preset')}`);
    const chips = parseFilters(p.get('filters') || '');
    if (chips.length) parts.push(`${chips.length} filter lapangan`);
    if (p.get('status') === 'ungrouped') parts.push('Belum masuk insiden');
    if (p.get('status') === 'grouped') parts.push('Sudah masuk insiden');
    if (p.get('time_preset')) parts.push(`Waktu: ${p.get('time_preset')}`);
    else if (p.get('time_from') || p.get('time_to')) parts.push(`Waktu: ${p.get('time_from') || '—'} s/d ${p.get('time_to') || 'kini'}`);
    const revLabel = reviewDateLabel({
      reviewed_preset: p.get('reviewed_preset') || '',
      reviewed_from: p.get('reviewed_from') || '',
      reviewed_to: p.get('reviewed_to') || '',
    });
    if (revLabel) parts.push(`Review: ${revLabel}`);
    if (p.get('reviewer') && p.get('reviewer') !== 'all') parts.push(`Reviewer: @${p.get('reviewer')}`);
  }
  return parts.join(' · ');
}
