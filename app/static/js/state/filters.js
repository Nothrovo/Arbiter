// Shared filter-chip model for Triage and Statistics.
// The backend repeats these whitelists in app/filters.py; keep both in sync.

export const FILTER_FIELDS = [
  ['rule.description', 'Deskripsi rule'],
  ['rule.id', 'Rule ID'],
  ['rule.level', 'Rule level', 'int'],
  ['rule.groups', 'Rule groups'],
  ['agent.name', 'Host / Agent'],
  ['agent.ip', 'Agent IP'],
  ['data.srcip', 'Source IP'],
  ['data.url', 'URL / Path'],
  ['data.status', 'HTTP status'],
  ['location', 'Location'],
  ['decoder', 'Decoder'],
  ['mitre.id', 'MITRE ID'],
  ['cve', 'CVE'],
  ['tenant', 'Tenant'],
  ['full_log', 'Full log'],
];

export const FILTER_OPS = [
  ['is', 'is'],
  ['is_not', 'is not'],
  ['contains', 'contains'],
  ['not_contains', 'does not contain'],
  ['glob', 'matches glob'],
  ['not_glob', 'does not match glob'],
  ['regex', 'matches regex'],
  ['not_regex', 'does not match regex'],
  ['range', 'in range'],
  ['gte', '≥'],
  ['lte', '≤'],
];

const FIELD_LABELS = Object.fromEntries(FILTER_FIELDS.map(([value, label]) => [value, label]));
const OP_LABELS = Object.fromEntries(FILTER_OPS.map(([value, label]) => [value, label]));
const NUMERIC_FIELDS = new Set(FILTER_FIELDS.filter(([, , kind]) => kind === 'int').map(([value]) => value));

export function isNumericField(field) {
  return NUMERIC_FIELDS.has(field);
}

export function filterOpOptions(field) {
  if (isNumericField(field)) {
    return FILTER_OPS.filter(([op]) => ['is', 'is_not', 'range', 'gte', 'lte'].includes(op));
  }
  return FILTER_OPS.filter(([op]) => !['range', 'gte', 'lte'].includes(op));
}

export function normalizeFilter(raw) {
  if (!raw || typeof raw !== 'object') return null;
  const field = String(raw.field || '').trim();
  if (!FIELD_LABELS[field]) return null;
  const allowed = filterOpOptions(field).map(([op]) => op);
  const requested = raw.op ? String(raw.op) : 'is';
  if (!allowed.includes(requested)) return null;
  const op = requested;
  const value = String(raw.value ?? '').slice(0, 500);
  if (!value.trim()) return null;
  const value2 = String(raw.value2 ?? '').slice(0, 500);
  if (['range'].includes(op) && !value2.trim()) return null;
  return {field, op, value, value2};
}

export function parseFilters(raw) {
  if (!raw) return [];
  let data = raw;
  if (typeof raw === 'string') {
    try {
      data = JSON.parse(raw);
    } catch {
      return [];
    }
  }
  if (data && !Array.isArray(data) && Array.isArray(data.filters)) data = data.filters;
  if (!Array.isArray(data)) return [];
  return data.map(normalizeFilter).filter(Boolean).slice(0, 40);
}

export function filtersValue(filters) {
  const clean = (Array.isArray(filters) ? filters : []).map(normalizeFilter).filter(Boolean);
  return clean.length ? JSON.stringify(clean) : '';
}

export function filterLabel(filter) {
  const field = FIELD_LABELS[filter.field] || filter.field;
  const op = OP_LABELS[filter.op] || filter.op;
  const value = filter.op === 'range' ? `${filter.value}..${filter.value2}` : filter.value;
  return `${field} ${op} “${value}”`;
}

export function renderFilterChips(filters, {mutable = true} = {}) {
  if (!Array.isArray(filters) || !filters.length) return '';
  const chip = (filter, index) => `<span class="filter-chip" title="${escapeAttr(filterLabel(filter))}">
    <span class="filter-chip-text">${escapeHtml(filterLabel(filter))}</span>
    ${mutable ? `<button type="button" class="filter-chip-remove" data-remove-filter="${index}" aria-label="Hapus filter ${escapeAttr(filterLabel(filter))}">×</button>` : ''}
  </span>`;
  return filters.map(chip).join('');
}

export function filterBuilderHTML(filters = [], {prefix = 'flt'} = {}) {
  const fieldOptions = FILTER_FIELDS.map(([value, label]) => `<option value="${value}">${escapeHtml(label)}</option>`).join('');
  const opOptions = filterOpOptions(FILTER_FIELDS[0][0]).map(([value, label]) => `<option value="${value}">${escapeHtml(label)}</option>`).join('');
  return `<div class="filter-builder" data-filter-builder="${escapeAttr(prefix)}">
    <div class="filter-builder-row">
      <label class="sr-only" for="${prefix}-field">Field</label>
      <select class="select" id="${prefix}-field" data-filter-field>${fieldOptions}</select>
      <label class="sr-only" for="${prefix}-op">Operator</label>
      <select class="select" id="${prefix}-op" data-filter-op>${opOptions}</select>
      <label class="sr-only" for="${prefix}-value">Nilai</label>
      <input class="input" id="${prefix}-value" data-filter-value placeholder="Nilai atau pola (* untuk glob)" autocomplete="off" spellcheck="false">
      <input class="input" id="${prefix}-value2" data-filter-value2 placeholder="Sampai" autocomplete="off" spellcheck="false" hidden>
      <button type="button" class="button" data-add-filter>+ Tambah filter</button>
    </div>
    <div class="filter-chip-list" data-filter-chips>${renderFilterChips(filters)}</div>
    <p class="meta">Contoh: <code>rule.description does not contain mhs</code>, <code>data.url matches glob */mhs/*</code>, <code>rule.level in range 7..12</code>. Filter memakai AND dan ikut tersimpan di URL.</p>
  </div>`;
}

export function readFilterBuilder(root, prefix = 'flt') {
  const field = root.querySelector(`[data-filter-builder="${prefix}"] [data-filter-field]`);
  const op = root.querySelector(`[data-filter-builder="${prefix}"] [data-filter-op]`);
  const value = root.querySelector(`[data-filter-builder="${prefix}"] [data-filter-value]`);
  const value2 = root.querySelector(`[data-filter-builder="${prefix}"] [data-filter-value2]`);
  if (!field || !op || !value) return null;
  const candidate = normalizeFilter({field: field.value, op: op.value, value: value.value, value2: value2?.value || ''});
  if (!candidate) return null;
  value.value = '';
  if (value2) {
    value2.value = '';
    value2.hidden = true;
  }
  return candidate;
}

export function syncFilterBuilder(root, prefix = 'flt') {
  const builder = root.querySelector(`[data-filter-builder="${prefix}"]`);
  if (!builder) return;
  const field = builder.querySelector('[data-filter-field]');
  const op = builder.querySelector('[data-filter-op]');
  const value2 = builder.querySelector('[data-filter-value2]');
  if (!field || !op) return;
  const allowed = filterOpOptions(field.value);
  const previous = op.value;
  op.innerHTML = allowed.map(([value, label]) => `<option value="${value}">${escapeHtml(label)}</option>`).join('');
  op.value = allowed.some(([value]) => value === previous) ? previous : allowed[0][0];
  if (value2) value2.hidden = op.value !== 'range';
}

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, char => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[char]));
}

function escapeAttr(value) {
  return escapeHtml(value).replace(/`/g, '&#96;');
}
