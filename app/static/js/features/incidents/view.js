import {json} from '../../api/client.js';
import {errorState} from '../../ui/primitives.js';
import {mountWorkspace} from './workspace.js';
import {incidentRoute, caseHref} from './model.js';
import {renderList} from './render.js';
import {scopeParams} from '../../state/scope.js';

export async function mount(ctx) {
  const {root, signal} = ctx;
  const lifecycle = new AbortController();
  const events = {signal: lifecycle.signal};
  const cleanup = () => {lifecycle.abort(); ctx.setGuard(null);};
  if (signal.aborted) {cleanup(); return cleanup;}
  signal.addEventListener('abort', cleanup, {once: true});
  ctx.setGuard(null);
  let route;
  try {route = incidentRoute(ctx.route);} catch (error) {
    root.innerHTML = errorState(error.message);
    return cleanup;
  }
  const active = () => !signal.aborted && !lifecycle.signal.aborted;
  if (route.mode !== 'list') {
    await mountWorkspace(ctx, route, {events, active});
    return cleanup;
  }
  const filters = {q: ctx.route.params.get('q') || '', status: ctx.route.params.get('case_status') || 'all', severity: ctx.route.params.get('severity') || 'all', sort: ctx.route.params.get('order') || 'updated_desc'};
  const list = {tenant: route.tenant, groups: [], filters, loading: false, error: ''};
  let version = 0;
  const render = () => {if (active()) root.innerHTML = renderList(list);};
  async function loadList() {
    if (!active()) return;
    const current = ++version;
    list.loading = true; list.error = ''; render();
    try {
      const groups = await json(`/api/groups?${scopeParams({tenant: route.tenant})}`, {signal});
      if (current !== version || !active()) return;
      if (!Array.isArray(groups) || groups.some(group => !group?.id)) throw new Error('Respons daftar insiden tidak valid. Coba lagi.');
      list.groups = groups;
    } catch (error) {if (current === version && error.name !== 'AbortError') list.error = error.message;}
    finally {if (current === version) {list.loading = false; render();}}
  }
  root.addEventListener('click', event => {
    const link = event.target.closest?.('[data-incident-nav]');
    if (link && !event.ctrlKey && !event.metaKey && !event.shiftKey && !event.altKey && event.button === 0) {event.preventDefault(); ctx.navigate(link.getAttribute('href').slice(1)); return;}
    if (event.target.closest?.('[data-action="retry"]')) return loadList();
  }, events);
  root.addEventListener('submit', event => {
    if (!event.target.matches?.('[data-incident-filters]')) return;
    event.preventDefault();
    const form = new FormData(event.target);
    ctx.navigate(caseHref(null, route.tenant, {q: String(form.get('q') || '').trim(), case_status: String(form.get('case_status') || 'all'), severity: String(form.get('severity') || 'all'), order: String(form.get('order') || 'updated_desc')}));
  }, events);
  root.addEventListener('arbiter:refresh', loadList, events);
  await loadList();
  return cleanup;
}
