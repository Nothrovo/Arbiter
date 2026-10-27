import {json, apiURL} from '../../api/client.js';
import {emptyState, errorState, loadingRows} from '../../ui/primitives.js';
import {withParams} from '../../router.js';
import {createStatsSession} from '../../state/stats.js';
import {normalizeStatsQuery, statsScopeParams} from './model.js';
import {statsPage, statsResults} from './render.js';

export function mount(ctx) {
  const {root, route, signal, navigate, notify} = ctx;
  const query = normalizeStatsQuery(route.params);
  const session = createStatsSession();

  let activeRequest = null;
  let currentData = null;
  let showOtherDetails = false;

  root.innerHTML = statsPage(query);
  const resultsContainer = root.querySelector('#stats-results');

  const on = (el, type, fn) => el?.addEventListener(type, fn, {signal});

  function updateRoute(changes, {replace = false} = {}) {
    const p = statsScopeParams(query);
    for (const [k, v] of Object.entries(changes)) {
      if (v === null || v === undefined || v === '') p.delete(k);
      else p.set(k, String(v));
    }
    navigate(withParams('/stats', p), {replace});
  }

  async function loadData() {
    activeRequest?.abort();
    activeRequest = new AbortController();
    const version = session.nextRequest();

    resultsContainer.innerHTML = loadingRows(4);

    try {
      const fetchParams = statsScopeParams(query);
      if (showOtherDetails) fetchParams.set('other_details', 'true');
      const data = await json(apiURL('/api/stats', fetchParams), {signal: activeRequest.signal});
      if (signal?.aborted || !session.isCurrent(version)) return;
      currentData = data;

      if (!data || data.total === 0) {
        resultsContainer.innerHTML = emptyState(
          'Tidak ada data statistik pada scope ini',
          'Coba ubah filter rentang waktu atau pilih acuan pivot lain.',
          `<button class="button primary" type="button" data-action="reset-stats">Reset Filter</button>`
        );
        return;
      }

      resultsContainer.innerHTML = statsResults(data, query);
    } catch (err) {
      if (err.name !== 'AbortError' && !signal?.aborted && session.isCurrent(version)) {
        resultsContainer.innerHTML = errorState(err.message || 'Gagal memuat data statistik.');
      }
    }
  }

  // Event handlers
  on(root, 'change', e => {
    if (e.target.id === 'stats-pivot') {
      const val = e.target.value;
      const wrap = root.querySelector('#stats-pattern-wrap');
      if (wrap) wrap.style.display = val === 'pattern' ? 'block' : 'none';
      updateRoute({pivot_by: val, facet: null, facet_value: null});
    }
    if (e.target.id === 'stats-top-n') {
      updateRoute({top_n: Number(e.target.value)});
    }
    if (e.target.id === 'stats-time') {
      const val = e.target.value;
      updateRoute({time_preset: val, time_from: null, time_to: null});
    }
  });

  on(root, 'click', async e => {
    const btn = e.target.closest('button, [role="button"]');
    if (!btn) return;

    if (btn.dataset.metric) {
      updateRoute({metric: btn.dataset.metric});
      return;
    }
    if (btn.dataset.chart) {
      updateRoute({chart: btn.dataset.chart});
      return;
    }
    if (btn.id === 'btn-apply-pattern') {
      const input = root.querySelector('#stats-pattern-input');
      const val = input?.value?.trim() || '';
      if (!val) {
        notify('Ketik kata kunci untuk pencarian pola teks.', 'error');
        return;
      }
      updateRoute({pattern: val});
      return;
    }
    if (btn.id === 'btn-clear-drilldown') {
      updateRoute({facet: null, facet_value: null});
      return;
    }
    if (btn.dataset.drillKey || btn.dataset.chartKey) {
      const key = btn.dataset.drillKey || btn.dataset.chartKey;
      if (key && key !== 'Lainnya') {
        updateRoute({facet: query.pivot_by, facet_value: key});
      }
      return;
    }
    if (btn.dataset.action === 'reset-stats') {
      const p = new URLSearchParams();
      for (const t of query.tenants) p.append('tenant', t);
      navigate(withParams('/stats', p));
      return;
    }
    if (btn.dataset.action === 'toggle-other-details') {
      showOtherDetails = !showOtherDetails;
      await loadData();
      return;
    }
    if (btn.dataset.action === 'close-other-details') {
      showOtherDetails = false;
      await loadData();
      return;
    }
    if (btn.dataset.action === 'retry') {
      await loadData();
      return;
    }
  });

  on(root, 'keydown', e => {
    if (e.target.id === 'stats-pattern-input' && e.key === 'Enter') {
      e.preventDefault();
      const val = e.target.value?.trim() || '';
      if (val) updateRoute({pattern: val});
    }
    if ((e.key === 'Enter' || e.key === ' ') && (e.target.matches('[data-chart-key]') || e.target.matches('[data-drill-key]'))) {
      e.preventDefault();
      const key = e.target.dataset.chartKey || e.target.dataset.drillKey;
      if (key && key !== 'Lainnya') {
        updateRoute({facet: query.pivot_by, facet_value: key});
      }
    }
  });

  loadData();

  return () => {
    session.dispose();
    activeRequest?.abort();
  };
}
