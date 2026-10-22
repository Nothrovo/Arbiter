import {draftFrom, draftsEqual, TEXT_FIELDS, cleanIds, incidentPayload, validateDraft, evidenceParams} from './model.js';

const EVIDENCE_FIELDS = ['id', 'description', 'tenant', 'timestamp', 'first_seen', 'last_seen', 'hit_count', 'agent_name', 'agent_ip', 'source_ip', 'rule_id', 'rule_level', 'mitre_ids'];
const evidenceSummary = row => Object.fromEntries(EVIDENCE_FIELDS.map(key => [key, row[key]]));

export async function loadSelectedEvidence({ids, tenant, json, signal}) {
  const rows = [];
  const failedIds = [];
  const pending = cleanIds(ids);
  // Small batches avoid issuing hundreds of simultaneous detail requests.
  for (let offset = 0; offset < pending.length && !signal?.aborted; offset += 6) {
    await Promise.all(pending.slice(offset, offset + 6).map(async id => {
      try {
        const row = await json(`/api/alerts/${id}?${new URLSearchParams({tenant})}`, {signal});
        if (Number(row?.id) !== id || tenant !== 'all' && row.tenant !== tenant) throw new Error('Evidence is outside the active scope.');
        rows.push(evidenceSummary(row));
      } catch (error) {if (!aborted(error)) failedIds.push(id);}
    }));
  }
  rows.sort((a, b) => (Date.parse(a.first_seen || a.timestamp) || 0) - (Date.parse(b.first_seen || b.timestamp) || 0) || a.id - b.id);
  failedIds.sort((a, b) => a - b);
  return {rows, failedIds, error: failedIds.length ? `Bukti #${failedIds.join(', #')} tidak dapat dimuat dalam scope aktif. Coba lagi atau lepaskan tautannya.` : ''};
}

export function createEvidenceState({tenant = 'all', groupId = '', json, signal, limit = 50}) {
  let version = 0;
  const state = {
    rows: [], total: 0, offset: 0, q: '', limit, loading: false, error: '',
    get hasNext() {return state.offset + state.limit < state.total;},
    async load({offset = state.offset, q = state.q} = {}) {
      const current = ++version;
      state.loading = true;
      state.error = '';
      try {
        const result = await json(`/api/alerts?${evidenceParams({tenant, groupId, offset, q, limit})}`, {signal});
        if (current !== version || signal?.aborted) return false;
        if (!Array.isArray(result?.items) || !Number.isSafeInteger(result.total) || result.total < 0) throw new Error('The evidence response is incomplete. Try again.');
        state.rows = result.items;
        state.total = result.total;
        state.offset = offset;
        state.q = q;
        return true;
      } catch (error) {if (current === version && !aborted(error)) state.error = message(error); return false;}
      finally {if (current === version) state.loading = false;}
    },
  };
  return state;
}


const scoped = (path, tenant) => `${path}?${new URLSearchParams({tenant})}`;
const writeOptions = (method, body, signal) => ({method, signal, headers: {'Content-Type': 'application/json'}, ...(body ? {body: JSON.stringify(body)} : {})});

const message = error => error?.message || 'The request failed. Try again.';
const aborted = error => error?.name === 'AbortError';

export function createCaseState({id = null, tenant = 'all', alertIds = [], json, signal}) {
  let baseline = draftFrom();
  let version = 0;
  const state = {
    id, tenant, draft: draftFrom({alert_pks: alertIds}), group: null,
    loading: false, pending: false, error: '', notice: '', refreshDeferred: false,
    get dirty() { return !draftsEqual(state.draft, baseline); },
    edit(field, value) {
      if (TEXT_FIELDS.includes(field)) state.draft[field] = String(value);
      state.notice = '';
    },
    stage(id, included) {
      if (state.pending) return;
      state.draft.alert_pks = cleanIds(included ? [...state.draft.alert_pks, id] : state.draft.alert_pks.filter(value => value !== Number(id)));
      state.notice = '';
    },
    discard() { state.draft = draftFrom(baseline); state.error = ''; },
    async save() {
      if (state.pending || state.loading) return false;
      const errors = validateDraft(state.draft);
      if (Object.keys(errors).length) {state.error = Object.values(errors)[0]; return false;}
      if (!state.id && tenant !== 'all' && !state.draft.alert_pks.length) {state.error = 'Pilih minimal satu bukti untuk tenant ini, atau buat kasus kosong dari scope Semua tenant.'; return false;}
      state.pending = true;
      state.error = '';
      state.notice = '';
      const payload = incidentPayload(state.draft);
      try {
        if (!state.id) {
          const created = await json(scoped('/api/groups', tenant), writeOptions('POST', payload, signal));
          if (!created?.id) throw new Error('The server did not return an incident ID. Check the incident list before retrying.');
          state.id = String(created.id);
          baseline.alert_pks = [...payload.alert_pks];
        } else {
          await json(scoped(`/api/groups/${encodeURIComponent(state.id)}`, tenant), writeOptions('PUT', Object.fromEntries(TEXT_FIELDS.map(key => [key, payload[key]])), signal));
        }
        const added = payload.alert_pks.filter(id => !baseline.alert_pks.includes(id));
        if (added.length) {
          await json(scoped(`/api/groups/${encodeURIComponent(state.id)}/members`, tenant), writeOptions('POST', {alert_pks: added}, signal));
          baseline.alert_pks = cleanIds([...baseline.alert_pks, ...added]);
        }
        for (const id of [...baseline.alert_pks].filter(id => !payload.alert_pks.includes(id))) {
          await json(scoped(`/api/groups/${encodeURIComponent(state.id)}/members/${id}`, tenant), writeOptions('DELETE', null, signal));
          baseline.alert_pks = baseline.alert_pks.filter(value => value !== id);
        }
        const verified = await json(scoped(`/api/groups/${encodeURIComponent(state.id)}`, tenant), {signal});
        if (!verified || String(verified.id) !== state.id || !draftsEqual(verified, payload)) throw new Error('The saved incident could not be verified. Your draft is retained; refresh or retry.');
        if (signal?.aborted) return false;
        state.group = verified;
        state.draft = draftFrom(verified);
        baseline = draftFrom(verified);
        state.refreshDeferred = false;
        state.notice = 'Incident saved.';
        return true;
      } catch (error) {
        if (!aborted(error)) state.error = message(error);
        return false;
      } finally {state.pending = false;}
    },
    async remove(confirm) {
      if (!state.id || state.pending) return false;
      const title = state.group?.title || state.draft.title;
      if (!confirm(`Delete incident “${title}”? This removes the case and its evidence links. Alerts will not be deleted.${state.dirty ? ' Unsaved edits will be discarded.' : ''}`)) return false;
      state.pending = true;
      state.error = '';
      try {
        const url = scoped(`/api/groups/${encodeURIComponent(state.id)}`, tenant);
        await json(url, writeOptions('DELETE', null, signal));
        let absent = false;
        try {await json(url, {signal});} catch (error) {if (error?.status === 404) absent = true; else throw error;}
        if (!absent) throw new Error('Deletion could not be verified. Refresh the incident list before retrying.');
        if (signal?.aborted) return false;
        state.deleted = true;
        baseline = draftFrom(state.draft);
        return true;
      } catch (error) {if (!aborted(error)) state.error = message(error); return false;}
      finally {state.pending = false;}
    },
    async load() {
      if (!state.id) return true;
      const current = ++version;
      state.loading = true;
      state.error = '';
      try {
        const group = await json(`/api/groups/${encodeURIComponent(state.id)}?${new URLSearchParams({tenant})}`, {signal});
        if (current !== version || signal?.aborted) return false;
        if (!group || typeof group !== 'object' || String(group.id) !== state.id || !Array.isArray(group.alert_pks)) throw new Error('The incident response is incomplete. Try refreshing.');
        state.group = group;
        state.draft = draftFrom(group);
        baseline = draftFrom(group);
        state.refreshDeferred = false;
        return true;
      } catch (error) {
        if (current === version && !aborted(error)) state.error = message(error);
        return false;
      } finally { if (current === version) state.loading = false; }
    },
    async refresh() {
      if (state.dirty || state.pending) { state.refreshDeferred = true; return false; }
      return state.load();
    },
  };
  return state;
}
