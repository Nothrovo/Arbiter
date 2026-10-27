import {choices, integer, queryFrom, scopeParams, tenantScope, tenantValues} from '../../state/scope.js';
import {withParams} from '../../router.js';

export const PIVOT_OPTIONS = [
  ['rule_description', 'Deskripsi rule'],
  ['rule_id', 'Rule ID'],
  ['severity', 'Severity level'],
  ['source_ip', 'Source IP'],
  ['agent', 'Host / Agent'],
  ['http_status', 'HTTP status code'],
  ['url_path', 'URL / Path'],
  ['referer', 'HTTP Referer'],
  ['user_agent', 'User-Agent'],
  ['pattern', 'Pola teks tertentu'],
  ['tenant', 'Tenant'],
];

export const METRIC_OPTIONS = [
  ['alerts', 'Alert (Dedup)'],
  ['events', 'Event mentah'],
];

export const CHART_OPTIONS = [
  ['bar', 'Balok'],
  ['donut', 'Donut'],
  ['line', 'Tren waktu'],
  ['table', 'Tabel'],
];

export function normalizeStatsQuery(params = new URLSearchParams()) {
  const get = key => params instanceof URLSearchParams ? params.get(key) : params?.[key];
  const base = queryFrom(params);
  const pKeys = PIVOT_OPTIONS.map(([k]) => k);
  const pivot_by = choices(get('pivot_by'), pKeys, 'rule_description');
  const metric = choices(get('metric'), ['alerts', 'events'], 'alerts');
  const chart = choices(get('chart'), ['bar', 'donut', 'line', 'table'], 'bar');
  const top_n = Math.min(1000, Math.max(1, integer(get('top_n'), 500) || 500));
  const bucket = choices(get('bucket'), ['auto', 'minute', 'hour', 'day'], 'auto');
  const pattern = String(get('pattern') || '').trim();
  const secondary_pivot = choices(get('secondary_pivot'), pKeys.filter(k => k !== 'pattern'), '');
  const facet = String(get('facet') || '').trim();
  const facet_value = String(get('facet_value') || '').trim();
  const secondary_facet = String(get('secondary_facet') || '').trim();
  const secondary_facet_value = String(get('secondary_facet_value') || '').trim();

  return {
    ...base,
    pivot_by,
    secondary_pivot,
    metric,
    chart,
    top_n,
    bucket,
    pattern,
    facet,
    facet_value,
    secondary_facet,
    secondary_facet_value,
  };
}

export function distributionPercentages(items = [], otherCount = 0, total = 0) {
  if (!items.length && otherCount <= 0) return [];
  if (total <= 0) return items.map(it => ({...it, displayPercentage: 0}));

  const all = items.map(it => ({...it, displayPercentage: (it.count / total) * 100}));
  let sum = 0;
  const rounded = all.map(it => {
    const val = Math.round(it.displayPercentage * 10) / 10;
    sum += val;
    return {...it, displayPercentage: val};
  });

  const remainder = Math.round((100.0 - sum) * 10) / 10;
  if (remainder !== 0 && rounded.length > 0) {
    rounded[rounded.length - 1].displayPercentage = Math.round((rounded[rounded.length - 1].displayPercentage + remainder) * 10) / 10;
  }
  return rounded;
}

export function statsScopeParams(query) {
  const p = scopeParams(query);
  if (query.pivot_by && query.pivot_by !== 'rule_description') p.set('pivot_by', query.pivot_by);
  if (query.secondary_pivot) p.set('secondary_pivot', query.secondary_pivot);
  if (query.metric && query.metric !== 'alerts') p.set('metric', query.metric);
  if (query.chart && query.chart !== 'bar') p.set('chart', query.chart);
  if (query.top_n && query.top_n !== 500) p.set('top_n', String(query.top_n));
  if (query.bucket && query.bucket !== 'auto') p.set('bucket', query.bucket);
  if (query.pattern) p.set('pattern', query.pattern);
  if (query.facet) p.set('facet', query.facet);
  if (query.facet_value) p.set('facet_value', query.facet_value);
  if (query.secondary_facet) p.set('secondary_facet', query.secondary_facet);
  if (query.secondary_facet_value) p.set('secondary_facet_value', query.secondary_facet_value);
  return p;
}

export function triageRouteFromStats(query, {facet, facet_value, secondary_facet, secondary_facet_value} = {}) {
  const p = new URLSearchParams();
  for (const t of tenantValues(query)) p.append('tenant', t);
  if (query.q) p.set('q', query.q);
  if (query.filter_preset) p.set('filter_preset', query.filter_preset);
  if (query.status && query.status !== 'all') p.set('status', query.status);
  if (query.review_status && query.review_status !== 'unreviewed') p.set('review_status', query.review_status);
  if (query.time_preset) p.set('time_preset', query.time_preset);
  if (query.time_from) p.set('time_from', query.time_from);
  if (query.time_to) p.set('time_to', query.time_to);

  const f = facet || query.facet;
  const fv = facet_value || query.facet_value;
  if (f && fv) {
    p.set('facet', f);
    p.set('facet_value', fv);
  }
  const sf = secondary_facet || query.secondary_facet;
  const sfv = secondary_facet_value || query.secondary_facet_value;
  if (sf && sfv) {
    p.set('secondary_facet', sf);
    p.set('secondary_facet_value', sfv);
  }
  return withParams('/triage', p);
}

export function generateStatsCSV(data) {
  const lines = ['Kategori,Jumlah,Persen'];
  for (const it of (data.items || [])) {
    const key = String(it.key).replace(/"/g, '""');
    lines.push(`"${key}",${it.count},${it.displayPercentage ?? it.percentage}`);
  }
  if (data.other_count > 0) {
    lines.push(`"Lainnya",${data.other_count},${data.other_percentage}`);
  }
  return lines.join('\n');
}

export function generateMarkdownSummary(data) {
  const metricLabel = data.metric === 'events' ? 'event' : 'alert';
  const lines = [
    '### Ringkasan Statistik Alert',
    `- Acuan Pivot: ${data.pivot_by}`,
    `- Total: ${data.total} ${metricLabel}`,
    '- Top Kategori:',
  ];
  for (const it of (data.items || [])) {
    lines.push(`  - ${it.key}: ${it.count} (${it.displayPercentage ?? it.percentage}%)`);
  }
  if (data.other_count > 0) {
    lines.push(`  - Lainnya: ${data.other_count} (${data.other_percentage}%)`);
  }
  return lines.join('\n');
}

export const MALICIOUS_PATTERNS = [
  /\.env(\b|\.|\/|$)/i,
  /\.git(\b|\/|$)/i,
  /\.ssh(\b|\/|$)/i,
  /id_rsa/i,
  /xmlrpc(\.php)?/i,
  /(wp-)?config(\.php)?(\.bak|\.old|\.save|\.swp|\.orig)?(\b|$)/i,
  /credentials?/i,
  /secret/i,
  /admin(istrator)?(\b|\/|\.|$)/i,
  /phpinfo/i,
  /shell(\.php)?/i,
  /backup(\b|\/|\.|$)/i,
  /\.(bak|old|save|swp|sql|tar|gz|zip|rar)$/i,
  /\.(aws|firebase)(\b|\/|$)/i,
  /etc\/(passwd|shadow)/i,
  /eval-stdin/i,
  /cmd(\.exe)?/i,
  /setup(\.php)?/i,
  /install(\.php)?/i,
  /web\.config/i,
  /\.htaccess/i,
];

export function isMaliciousPath(text = '') {
  const str = String(text || '').trim();
  if (!str) return false;
  return MALICIOUS_PATTERNS.some(rx => rx.test(str));
}
