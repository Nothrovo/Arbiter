import {json, apiURL} from '../../api/client.js';
import {icon, errorState, loadingRows} from '../../ui/primitives.js';
import {queryFrom} from '../../state/scope.js';
import {withParams} from '../../router.js';
import {renderMonitoringDashboard} from './model.js';

export async function mount(ctx) {
  const {root, route, signal, notify} = ctx;
  const query = queryFrom(route.params);
  const tenant = query.tenantScope.all ? 'all' : query.tenants;

  root.innerHTML = `
    <header class="page-header">
      <div class="page-heading">
        <h1>User Review</h1>
        <p class="page-description">Aktivitas, backlog, dan kontribusi review analis.</p>
      </div>
      <div class="page-actions">
        <button class="button" type="button" data-action="refresh-monitoring">${icon('refresh')} Perbarui Data</button>
      </div>
    </header>
    <div id="monitoring-content">${loadingRows(4)}</div>
  `;

  const content = root.querySelector('#monitoring-content');

  async function load() {
    if (!content) return;
    content.setAttribute('aria-busy', 'true');
    try {
      const reviewerParam = String(route.params.get('reviewer') || '').trim();
      const params = {
        tenant,
        tz_offset_minutes: -new Date().getTimezoneOffset(),
      };
      if (reviewerParam) params.reviewer = reviewerParam;
      const data = await json(
        apiURL('/api/monitoring', params),
        {signal},
      );
      if (signal.aborted) return;
      content.innerHTML = renderMonitoringDashboard(data, query, {includeAudit: false});
    } catch (err) {
      if (err.name !== 'AbortError' && !signal.aborted) {
        content.innerHTML = errorState(err.message || 'Gagal memuat data monitoring.');
      }
    } finally {
      content.removeAttribute('aria-busy');
    }
  }

  root.addEventListener('click', async e => {
    const btn = e.target.closest('button');
    if (!btn) return;
    if (btn.dataset.reviewDay) {
      const [year, month, day] = btn.dataset.reviewDay.split('-').map(Number);
      const start = new Date(year, month - 1, day, 0, 0, 0, 0);
      const end = new Date(year, month - 1, day + 1, 0, 0, 0, 0);
      const params = new URLSearchParams();
      for (const t of (query.tenantScope.all ? ['all'] : query.tenants)) params.append('tenant', t);
      params.set('review_status', 'reviewed');
      params.set('reviewed_from', start.toISOString());
      params.set('reviewed_to', new Date(end.getTime() - 1).toISOString());
      const activeReviewer = root.querySelector('#monitoring-reviewer')?.value || String(route.params.get('reviewer') || '').trim();
      if (activeReviewer) params.set('reviewer', activeReviewer);
      location.hash = withParams('/triage', params);
      return;
    }
    if (btn.dataset.action === 'refresh-monitoring' || btn.dataset.action === 'retry') {
      btn.disabled = true;
      await load();
      if (btn.isConnected) btn.disabled = false;
      if (btn.dataset.action === 'refresh-monitoring') notify('Dashboard User Review diperbarui.', 'info');
    }
  }, {signal});

  root.addEventListener('change', e => {
    const select = e.target.closest('#monitoring-reviewer');
    if (!select) return;
    const params = new URLSearchParams();
    for (const t of (query.tenantScope.all ? ['all'] : query.tenants)) params.append('tenant', t);
    params.set('reviewer', select.value || 'all');
    location.hash = withParams('/monitoring', params);
  }, {signal});

  root.addEventListener('arbiter:refresh', () => load(), {signal});
  await load();
  return () => {};
}
