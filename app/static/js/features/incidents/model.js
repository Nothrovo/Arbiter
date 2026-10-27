import {scopeParams, tenantScope} from '../../state/scope.js';

export function selectedIds(value = '') {
  if (!String(value).trim()) return [];
  const parts = String(value).split(',').map(part => part.trim());
  if (parts.some(part => !/^[1-9]\d*$/.test(part) || !Number.isSafeInteger(Number(part)))) throw new Error('Alert IDs must be positive whole numbers separated by commas.');
  return cleanIds(parts);
}
export function incidentRoute(route) {
  const params = route.params || new URLSearchParams();
  const tail = route.path.replace(/^\/incidents\/?/, '').replace(/\/$/, '');
  const scope = tenantScope(params);
  const tenant = scope.all ? 'all' : scope.tenants.length === 1 ? scope.tenants[0] : scope.tenants;
  return {mode: !tail ? 'list' : tail === 'new' ? 'create' : 'edit', id: !tail || tail === 'new' ? null : decodeURIComponent(tail), tenant, alertIds: selectedIds(params.get('alert_ids') || '')};
}
export function caseHref(id, tenant, extra = {}) {
  const scope = tenantScope(tenant);
  const params = new URLSearchParams();
  for (const value of scope.all ? ['all'] : scope.tenants) params.append('tenant', value);
  for (const [key, value] of Object.entries(extra)) if (value !== undefined && value !== null && value !== '') params.set(key, String(value));
  return `/incidents${id ? `/${encodeURIComponent(id)}` : ''}?${params}`;
}
export function evidenceParams({tenant = 'all', groupId, offset = 0, q = '', limit = 50} = {}) {
  const params = scopeParams({tenant, review_status: 'all', status: 'all', q}, groupId ? {groupId} : {});
  params.set('summary', 'true');
  params.set('sort', 'asc');
  params.set('sort_by', 'timestamp');
  params.set('limit', String(limit));
  params.set('offset', String(offset));
  return params;
}

export const TEXT_FIELDS = ['title', 'category', 'severity', 'status', 'analysis', 'conclusion', 'recommendation'];
export const SEVERITIES = ['low', 'medium', 'high', 'critical'];
export const STATUSES = ['open', 'investigating', 'contained', 'resolved', 'closed'];

export function cleanIds(values = []) {
  return [...new Set(values.filter(value => /^(?:[1-9]\d*)$/.test(String(value))).map(Number).filter(Number.isSafeInteger))].sort((a, b) => a - b);
}
export function draftFrom(group = {}) {
  const defaults = {title: '', category: 'General Incident', severity: 'medium', status: 'open', analysis: '', conclusion: '', recommendation: ''};
  return {...Object.fromEntries(TEXT_FIELDS.map(field => [field, String(group[field] ?? defaults[field])])), alert_pks: cleanIds(group.alert_pks || [])};
}
export function incidentPayload(draft) {
  const value = draftFrom(draft);
  value.title = value.title.trim();
  return value;
}
export function validateDraft(draft) {
  const errors = {};
  if (!String(draft.title || '').trim()) errors.title = 'Enter an incident title.';
  if (!String(draft.severity || '').trim()) errors.severity = 'Choose a severity.';
  if (!String(draft.status || '').trim()) errors.status = 'Choose a status.';
  return errors;
}
export function draftsEqual(a, b) {
  return JSON.stringify(draftFrom(a)) === JSON.stringify(draftFrom(b));
}

export function filterIncidents(groups, filters = {}) {
  const q = String(filters.q || '').trim().toLocaleLowerCase();
  const rank = {critical: 4, high: 3, medium: 2, low: 1};
  const stamp = row => Date.parse(row.updated_at || row.created_at || '') || 0;
  return groups.filter(row => (!q || [row.title, row.category, row.id].some(value => String(value || '').toLocaleLowerCase().includes(q)))
    && (!filters.status || filters.status === 'all' || row.status === filters.status)
    && (!filters.severity || filters.severity === 'all' || row.severity === filters.severity))
    .sort((a, b) => {
      if (filters.sort === 'title') return String(a.title).localeCompare(String(b.title)) || String(a.id).localeCompare(String(b.id));
      if (filters.sort === 'severity') return (rank[b.severity] || 0) - (rank[a.severity] || 0) || stamp(b) - stamp(a);
      return stamp(b) - stamp(a) || String(a.id).localeCompare(String(b.id));
    });
}
