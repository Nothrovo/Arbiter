const choices = (value, allowed, fallback) => allowed.includes(value) ? value : fallback;
const integer = (value,fallback) => Number.isFinite(Number(value)) ? Math.floor(Number(value)) : fallback;
export function queryFrom(params = new URLSearchParams()) {
  const get = key => params instanceof URLSearchParams ? params.get(key) : params[key];
  return {
    tenant: get('tenant') || 'all', q: get('q') || '',
    review_status: choices(get('review_status'), ['all', 'reviewed', 'unreviewed'], 'unreviewed'),
    filter_preset: choices(get('filter_preset'), ['', '403', '404', 'repeating', 'non_http', 'bot', 'curl'], ''),
    status: choices(get('status'), ['all', 'grouped', 'ungrouped'], 'all'),
    group_id: get('group_id') || '',
    sort_by: choices(get('sort_by'), ['timestamp', 'severity', 'hits'], 'timestamp'),
    sort: choices(get('sort'), ['asc', 'desc'], 'desc'),
    limit: Math.min(200, Math.max(25, integer(get('limit'),50) || 50)),
    offset: Math.max(0, integer(get('offset'),0) || 0),
  };
}
export function scopeParams(query, {ids, groupId} = {}) {
  const normalized = queryFrom(query);
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(normalized)) {
    if (key !== 'limit' && key !== 'offset' && value !== '') params.set(key, String(value));
  }
  if (groupId) {
    params.set('group_id', groupId);
    for (const key of ['q', 'filter_preset', 'status']) params.delete(key);
    params.set('review_status', 'all');
  }
  if (ids !== undefined) {
    if (!Array.isArray(ids) || !ids.length || ids.some(id=>!(/^[1-9]\d*$/.test(String(id))))) throw new Error('Pilihan alert tidak valid. Pilih ulang sebelum mengekspor.');
    const clean = [...new Set(ids.map(Number))].filter(Number.isSafeInteger).filter(id => id > 0);
    if (clean.length !== new Set(ids.map(Number)).size) throw new Error('Pilihan alert tidak valid. Pilih ulang sebelum mengekspor.');
    for (const key of ['q', 'review_status', 'filter_preset', 'status', 'group_id']) params.delete(key);
    params.set('alert_ids', clean.join(','));
  }
  return params;
}
export function scopeDescription(params) {
  const p = params instanceof URLSearchParams ? params : new URLSearchParams(params);
  const parts = [p.get('tenant') && p.get('tenant') !== 'all' ? `Tenant ${p.get('tenant')}` : 'Semua tenant'];
  if (p.get('alert_ids')) parts.push(`${p.get('alert_ids').split(',').length} alert terpilih`);
  else {
    if (p.get('group_id')) parts.push('Insiden terpilih');
    if (p.get('q')) parts.push(`Pencarian: ${p.get('q')}`);
    if (p.get('review_status') === 'unreviewed') parts.push('Belum direview');
    if (p.get('review_status') === 'reviewed') parts.push('Sudah direview');
    if (p.get('filter_preset')) parts.push(`Filter ${p.get('filter_preset')}`);
    if (p.get('status') === 'ungrouped') parts.push('Belum masuk insiden');
    if (p.get('status') === 'grouped') parts.push('Sudah masuk insiden');
  }
  return parts.join(' · ');
}
