import {json} from '../../api/client.js';
import {esc, errorState, loadingRows, emptyState} from '../../ui/primitives.js';
import {caseHref, TEXT_FIELDS, validateDraft} from './model.js';
import {createCaseState, createEvidenceState, loadSelectedEvidence} from './state.js';
import {renderWorkspace, renderEvidence} from './render.js';

export async function mountWorkspace(ctx, route, {events, active}) {
  const {root, signal} = ctx;
  const state = createCaseState({id: route.id, tenant: route.tenant, alertIds: route.alertIds, json, signal});
  const candidates = createEvidenceState({tenant: route.tenant, json, signal});
  let evidence = state.id ? createEvidenceState({tenant: route.tenant, groupId: state.id, json, signal}) : null;
  let originalIds = new Set();
  let selectedRows = [];
  let selectedError = '';
  let selectedLoading = false;
  let selectedVersion = 0;
  let candidatesRequested = false;
  let mounted = false;
  const knownRows = new Map();
  const confirm = message => root.ownerDocument.defaultView.confirm(message);
  const node = selector => root.querySelector(selector);
  const text = (selector, value) => {const element = node(selector); if (element) element.textContent = value;};
  const html = (selector, value) => {const element = node(selector); if (element) element.innerHTML = value;};
  ctx.setGuard(() => !state.dirty && !state.pending);

  function status() {
    if (!active() || !mounted) return;
    const busy = state.pending || state.loading;
    text('[data-save-status]', state.pending ? 'Menyimpan perubahan…' : state.error ? 'Perubahan belum tersimpan. Perbaiki masalah lalu coba Simpan lagi.' : state.notice ? 'Insiden tersimpan.' : state.dirty ? 'Perubahan belum disimpan.' : state.id ? 'Tidak ada perubahan.' : 'Draft baru. Simpan untuk membuat insiden.');
    text('[data-refresh-notice]', state.refreshDeferred ? 'Pembaruan ditunda karena ada perubahan belum disimpan atau penyimpanan sedang berlangsung. Simpan atau buang perubahan, lalu Refresh.' : '');
    html('[data-case-error]', state.error ? `<div class="error-region" role="alert"><p>${esc(state.error)}</p></div>` : '');
    text('[data-membership-count]', `${state.draft.alert_pks.length} alert dipilih${state.tenant !== 'all' ? ' dalam seluruh kasus; bukti di bawah mengikuti tenant aktif' : ''}`);
    const fields = node('[data-editor-fields]');
    if (fields) fields.disabled = busy;
    const save = node('[data-action="save"]');
    if (save) {save.disabled = busy || !!state.id && !state.dirty && !state.error; save.textContent = state.pending ? 'Menyimpan…' : state.id ? 'Simpan perubahan' : 'Buat insiden';}
    const discard = node('[data-action="discard"]');
    if (discard) discard.disabled = busy || !state.dirty;
    const remove = node('[data-action="delete"]');
    if (remove) remove.disabled = busy;
    for (const button of root.querySelectorAll('[data-stage-id]')) button.disabled = busy;
    const form = node('#incident-editor');
    form?.setAttribute('aria-busy', String(busy));
  }

  function context() {
    const rows = evidence ? evidence.rows : selectedRows;
    const values = key => [...new Set(rows.map(row => row[key]).filter(Boolean))];
    const mitre = [...new Set(rows.flatMap(row => Array.isArray(row.mitre_ids) ? row.mitre_ids : []))];
    html('[data-evidence-context]', `<dl class="detail-grid">${[['Asset pada halaman ini', values('agent_name')], ['Rule pada halaman ini', values('rule_id')], ['MITRE pada halaman ini', mitre]].map(([label, values]) => `<div class="key-value"><dt>${label}</dt><dd>${esc(values.join(', ') || '—')}</dd></div>`).join('')}</dl>`);
  }

  function selected() {
    const ids = state.draft.alert_pks.filter(id => !originalIds.has(id));
    const removed = [...originalIds].filter(id => !state.draft.alert_pks.includes(id));
    const summary = id => esc(knownRows.get(id)?.description || `Alert #${id}`);
    const staged = ids.length || removed.length ? `<div class="stack"><h3 class="section-heading">${state.id ? 'Perubahan tautan belum disimpan' : 'Bukti yang dipilih'}</h3><ul>${ids.map(id => `<li>${summary(id)} <span class="meta">#${id}${state.id ? ' · akan ditautkan' : ''}</span> <button class="button" type="button" data-stage-id="${id}" data-stage-include="false">Lepas bukti #${id}</button></li>`).join('')}${removed.map(id => `<li>${summary(id)} <span class="meta">#${id} · akan dilepas</span> <button class="button" type="button" data-stage-id="${id}" data-stage-include="true">Batalkan pelepasan #${id}</button></li>`).join('')}</ul></div>` : '';
    html('[data-selected-evidence]', `${selectedLoading ? '<p class="inline-status" role="status">Memuat bukti terpilih…</p>' : ''}${selectedError ? `<div class="error-region" role="alert"><p>${esc(selectedError)}</p><button class="button" type="button" data-action="selected-retry">Coba muat bukti lagi</button></div>` : ''}${staged}`);
  }

  function panels() {
    if (!active() || !mounted) return;
    // Retain native evidence disclosures when membership changes or data refreshes.
    const open = new Set([...root.querySelectorAll('[data-evidence-region] details[open], [data-candidate-region] details[open]')].map(element => element.querySelector('summary')?.textContent));
    for (const row of [...(evidence?.rows || []), ...candidates.rows, ...selectedRows]) knownRows.set(Number(row.id), row);
    selected();
    html('[data-evidence-region]', evidence ? renderEvidence(evidence, {selected: state.draft.alert_pks, tenant: state.tenant}) : selectedRows.length ? renderEvidence({rows: selectedRows.filter(row => state.draft.alert_pks.includes(Number(row.id))), total: state.draft.alert_pks.length, offset: 0, hasNext: false}, {selected: state.draft.alert_pks, tenant: state.tenant}) : emptyState('Belum ada bukti yang dimuat', 'Pilih bukti dari Triage atau cari alert dalam scope aktif.'));
    if (candidatesRequested) html('[data-candidate-region]', renderEvidence(candidates, {selected: state.draft.alert_pks, tenant: state.tenant, kind: 'candidate'}));
    for (const element of root.querySelectorAll('[data-evidence-region] details, [data-candidate-region] details')) if (open.has(element.querySelector('summary')?.textContent)) element.open = true;
    context();
    status();
  }

  async function loadPage(target, options) {
    if (!active()) return;
    const loading = target.load(options);
    panels();
    await loading;
    if (active()) panels();
  }

  async function loadSelected() {
    const current = ++selectedVersion;
    selectedLoading = true; selectedError = ''; panels();
    const result = await loadSelectedEvidence({ids: state.draft.alert_pks.filter(id => !originalIds.has(id)), tenant: state.tenant, json, signal});
    if (!active() || current !== selectedVersion) return;
    selectedLoading = false;
    selectedRows = result.rows;
    selectedError = result.error;
    panels();
  }

  function syncFields() {
    for (const field of TEXT_FIELDS) {
      const input = node(`#incident-editor [name="${field}"]`);
      if (input) input.value = state.draft[field];
    }
    text('[data-case-heading]', state.id ? state.draft.title || 'Insiden tanpa judul' : 'Buat insiden');
    node('[name="title"]')?.removeAttribute('aria-invalid');
    text('[data-title-error]', '');
  }

  async function save() {
    if (!active() || state.pending || state.loading) return;
    const errors = validateDraft(state.draft);
    const title = node('[name="title"]');
    if (errors.title) title?.setAttribute('aria-invalid', 'true');
    else title?.removeAttribute('aria-invalid');
    text('[data-title-error]', errors.title || '');
    const creating = route.mode === 'create';
    const operation = state.save();
    status();
    const saved = await operation;
    if (!active()) return;
    if (!saved) {status(); if (errors.title) title?.focus(); return;}
    originalIds = new Set(state.draft.alert_pks);
    selectedRows = []; selectedError = '';
    syncFields();
    status();
    ctx.notify('Insiden tersimpan.', 'success');
    if (creating) {ctx.navigate(caseHref(state.id, state.tenant), {replace: true}); return;}
    await loadPage(evidence);
  }

  async function refresh() {
    if (!active()) return;
    if (state.dirty || state.pending) {await state.refresh(); status(); return;}
    const operation = state.refresh();
    status();
    const loaded = await operation;
    if (!active()) return;
    if (!loaded) {status(); return;}
    originalIds = new Set(state.group?.alert_pks || []);
    syncFields();
    status();
    if (evidence) await loadPage(evidence);
  }

  async function initial() {
    if (!active()) return;
    root.innerHTML = loadingRows();
    if (state.id && !await state.load()) {
      if (active()) root.innerHTML = errorState(state.error || 'Insiden tidak dapat dimuat. Coba lagi.');
      return;
    }
    if (!active()) return;
    originalIds = new Set(state.group?.alert_pks || []);
    root.innerHTML = renderWorkspace(state);
    mounted = true;
    status();
    if (evidence) await loadPage(evidence);
    else if (state.draft.alert_pks.length) await loadSelected();
    else panels();
  }

  root.addEventListener('input', event => {
    if (!active() || state.pending || !event.target.closest?.('#incident-editor')) return;
    state.edit(event.target.name, event.target.value);
    if (event.target.name === 'title') {event.target.removeAttribute?.('aria-invalid'); text('[data-title-error]', '');}
    status();
  }, events);
  root.addEventListener('change', event => {
    if (!active() || state.pending || !event.target.closest?.('#incident-editor')) return;
    state.edit(event.target.name, event.target.value);
    status();
  }, events);
  root.addEventListener('submit', async event => {
    if (event.target.matches?.('#incident-editor')) {event.preventDefault(); await save();}
    else if (event.target.matches?.('[data-evidence-search]')) {
      event.preventDefault();
      if (!active() || state.pending) return;
      candidatesRequested = true;
      await loadPage(candidates, {offset: 0, q: String(node('[name="evidence_q"]')?.value || '').trim()});
    }
  }, events);
  root.addEventListener('click', async event => {
    const link = event.target.closest?.('[data-incident-nav]');
    if (link && !event.ctrlKey && !event.metaKey && !event.shiftKey && !event.altKey && event.button === 0) {event.preventDefault(); ctx.navigate(link.getAttribute('href').slice(1)); return;}
    const section = event.target.closest?.('[data-section]');
    if (section) {event.preventDefault(); const target = node(`#${section.dataset.section}`); target?.setAttribute('tabindex', '-1'); target?.focus({preventScroll: true}); target?.scrollIntoView({block: 'start'}); return;}
    if (!active()) return;
    const stage = event.target.closest?.('[data-stage-id]');
    if (stage && !state.pending) {
      state.stage(Number(stage.dataset.stageId), stage.dataset.stageInclude === 'true');
      panels();
      root.querySelector(`[data-stage-id="${stage.dataset.stageId}"]`)?.focus();
      return;
    }
    const action = event.target.closest?.('[data-action]')?.dataset.action;
    if (action === 'retry') {await initial(); return;}
    if (action === 'selected-retry') {await loadSelected(); return;}
    if (action === 'discard' && !state.pending && state.dirty && confirm('Buang perubahan yang belum disimpan? Narasi dan tautan bukti akan kembali ke versi terakhir yang dimuat atau disimpan.')) {
      state.discard(); selectedRows = selectedRows.filter(row => state.draft.alert_pks.includes(Number(row.id))); selectedError = '';
      syncFields(); panels(); node('[name="title"]')?.focus(); return;
    }
    if (action === 'delete' && !state.pending) {
      const operation = state.remove(confirm); status();
      const removed = await operation;
      if (!active()) return;
      status();
      if (removed) {ctx.notify('Insiden dihapus. Alert asli tidak dihapus.', 'success'); ctx.navigate(caseHref(null, state.tenant), {replace: true});}
      return;
    }
    const match = /^(evidence|candidate)-(previous|next|retry)$/.exec(action || '');
    if (match) {
      const target = match[1] === 'evidence' ? evidence : candidates;
      if (!target || target.loading) return;
      const offset = match[2] === 'previous' ? Math.max(0, target.offset - target.limit) : match[2] === 'next' && target.hasNext ? target.offset + target.limit : target.offset;
      await loadPage(target, {offset});
    }
  }, events);
  root.addEventListener('arbiter:refresh', refresh, events);
  await initial();
}
