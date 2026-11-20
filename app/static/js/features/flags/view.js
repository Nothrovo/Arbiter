import {json, apiURL, copyText, copyHTML, download, request} from '../../api/client.js';
import {withParams} from '../../router.js';
import {tenantValues} from '../../state/scope.js';
import {
  normalizeFlagQuery,
  flagScopeParams,
  flagExportParams,
  flagExportURL,
  flagExportFormat,
} from './model.js';
import {renderFlagsPage} from './render.js';

export function mount(ctx) {
  const {root, route, signal, navigate, notify} = ctx;
  const query = normalizeFlagQuery(route.params);
  let data = null;
  let loading = true;
  let error = '';
  let requestVersion = 0;
  let activeRequest = null;
  let searchTimer = null;
  const expandedGroups = new Set();
  const groupAlertsCache = new Map();
  const expandedLogIds = new Set();
  const selectedGroupKeys = new Set();
  let exportPending = false;
  let exportStatus = '';
  let exportCount = null;
  let exportCountVersion = 0;
  let pendingRuleTarget = null;

  const tenantParams = () => {
    const p = new URLSearchParams();
    for (const t of tenantValues(query)) p.append('tenant', t);
    return p;
  };

  function updateRoute(changes, {replace = false} = {}) {
    const p = flagScopeParams(query);
    for (const [key, value] of Object.entries(changes)) {
      if (value === null || value === undefined || value === '') p.delete(key);
      else p.set(key, String(value));
    }
    navigate(withParams('/flags', p), {replace});
  }

  function paint() {
    const wasOpen = Boolean(root.querySelector('#flag-rule-dialog')?.open);
    root.innerHTML = renderFlagsPage(query, data, {
      loading,
      error,
      expandedGroups,
      groupAlertsCache,
      expandedLogIds,
      selectedGroupKeys,
      exportPending,
      exportStatus,
      exportCount,
    });
    if (wasOpen && pendingRuleTarget) {
      openRuleDialog(pendingRuleTarget);
    }
  }

  function setDialogStatus(message = '', kind = 'error') {
    const el = root.querySelector('#flag-rule-dialog-status');
    if (!el) return;
    el.textContent = message;
    if (el.dataset) el.dataset.kind = message ? kind : '';
  }

  function openRuleDialog(target) {
    pendingRuleTarget = target;
    const dialog = root.querySelector('#flag-rule-dialog');
    const desc = root.querySelector('#flag-rule-target-desc');
    const ruleInput = root.querySelector('#flag-custom-rule-id');
    const notesInput = root.querySelector('#flag-rule-notes');
    setDialogStatus('');
    if (desc) desc.textContent = target.label;
    if (ruleInput) ruleInput.value = target.customRuleId || '';
    if (notesInput) notesInput.value = target.ruleNotes || '';
    dialog?.showModal();
    ruleInput?.focus();
  }

  function closeRuleDialog() {
    pendingRuleTarget = null;
    root.querySelector('#flag-rule-dialog')?.close();
  }

  async function loadGroupAlerts(groupKey) {
    const cacheKey = String(groupKey ?? '');
    groupAlertsCache.set(cacheKey, {loading: true, error: '', items: [], total: 0});
    paint();
    try {
      const params = flagScopeParams(query);
      params.set('group_key', cacheKey);
      params.set('limit', '200');
      const body = await json(apiURL('/api/flags/alerts', params), {signal});
      if (signal.aborted) return;
      groupAlertsCache.set(cacheKey, {
        loading: false,
        error: '',
        items: Array.isArray(body.items) ? body.items : [],
        total: Number(body.total || 0),
      });
    } catch (err) {
      if (err.name === 'AbortError' || signal.aborted) return;
      groupAlertsCache.set(cacheKey, {
        loading: false,
        error: err.message || 'Gagal memuat daftar alert pada grup.',
        items: [],
        total: 0,
      });
    }
    paint();
  }

  async function refreshExportCount() {
    const version = ++exportCountVersion;
    try {
      const params = flagExportParams(query, [...selectedGroupKeys]);
      const body = await json(apiURL('/api/flags/export/preview', params), {signal, timeout: 20000});
      if (signal.aborted || version !== exportCountVersion) return;
      exportCount = Number(body?.count || 0);
    } catch (err) {
      if (err.name === 'AbortError' || signal.aborted || version !== exportCountVersion) return;
      exportCount = null;
    }
    paint();
  }

  async function performFlagExport(format) {
    if (exportPending) return;
    exportPending = true;
    exportStatus = format.startsWith('copy-') ? 'Menyiapkan salinan laporan Flag…' : 'Menyiapkan unduhan laporan Flag…';
    paint();
    const keys = [...selectedGroupKeys];
    try {
      const url = flagExportURL(query, keys, format);
      const resolved = flagExportFormat(format);
      if (format === 'copy-html') {
        const preview = await json(apiURL('/api/flags/export/preview', flagExportParams(query, keys)), {signal, timeout: 60000});
        if (!preview?.html) throw new Error('Preview laporan tidak tersedia untuk disalin.');
        await copyHTML(preview.html);
        exportStatus = 'Laporan Flag disalin ke clipboard (HTML untuk Google Docs).';
      } else if (format.startsWith('copy-')) {
        const response = await request(url, {signal, timeout: 60000});
        const text = await response.text();
        await copyText(text);
        exportStatus = 'Laporan Flag disalin ke clipboard.';
      } else {
        const extension = resolved === 'report-html' ? 'html' : resolved === 'markdown' ? 'md' : resolved;
        await download(url, `Arbiter-Flag.${extension}`);
        exportStatus = 'File laporan Flag disiapkan untuk diunduh.'; 
      }
      notify(exportStatus, 'success');
    } catch (err) {
      if (err.name !== 'AbortError') {
        exportStatus = err.message || 'Ekspor Flag gagal. Coba lagi.';
        notify(exportStatus, 'error');
      }
    } finally {
      exportPending = false;
      paint();
    }
  }

  async function loadGroups({preserveExpanded = false} = {}) {
    activeRequest?.abort();
    activeRequest = new AbortController();
    const version = ++requestVersion;
    const onAbort = () => activeRequest?.abort();
    signal.addEventListener('abort', onAbort, {once: true});
    loading = true;
    error = '';
    if (!preserveExpanded) {
      expandedGroups.clear();
      groupAlertsCache.clear();
      selectedGroupKeys.clear();
      exportCount = null;
    } else {
      groupAlertsCache.clear();
    }
    paint();
    try {
      const params = flagScopeParams(query);
      const body = await json(apiURL('/api/flags/groups', params), {signal: activeRequest.signal});
      if (signal.aborted || version !== requestVersion) return;
      data = body;
      loading = false;
      if (preserveExpanded && selectedGroupKeys.size) {
        const visibleKeys = new Set((data.groups || []).map(g => String(g.key ?? '')));
        for (const key of [...selectedGroupKeys]) {
          if (!visibleKeys.has(key)) selectedGroupKeys.delete(key);
        }
      }
      paint();
      void refreshExportCount();
      if (preserveExpanded && expandedGroups.size) {
        const visibleKeys = new Set((data.groups || []).map(g => String(g.key ?? '')));
        for (const key of [...expandedGroups]) {
          if (!visibleKeys.has(key)) expandedGroups.delete(key);
          else void loadGroupAlerts(key);
        }
      }
    } catch (err) {
      if (err.name === 'AbortError' || signal.aborted || version !== requestVersion) return;
      loading = false;
      error = err.message || 'Gagal memuat pengelompokan Flag.';
      paint();
    } finally {
      signal.removeEventListener('abort', onAbort);
    }
  }

  async function submitRuleStatus(payload, successMessage) {
    try {
      await json(apiURL('/api/flags/rule-status', tenantParams()), {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload),
        signal,
      });
      notify(successMessage, 'success');
      window.dispatchEvent(new CustomEvent('arbiter:flags-changed'));
      await loadGroups({preserveExpanded: true});
    } catch (err) {
      if (err.name !== 'AbortError') notify(err.message || 'Gagal memperbarui status rule.', 'error');
    }
  }

  function findAlertInCache(alertId) {
    for (const cached of groupAlertsCache.values()) {
      const hit = (cached?.items || []).find(item => Number(item.id) === Number(alertId));
      if (hit) return hit;
    }
    return null;
  }

  root.addEventListener('click', async e => {
    const tab = e.target.closest('[data-flag-tab]');
    if (tab) {
      const nextColor = tab.dataset.flagTab;
      if (nextColor && nextColor !== query.flag_color) {
        updateRoute({
          flag_color: nextColor,
          rule_status: nextColor === 'red' ? 'all' : 'pending',
        });
      }
      return;
    }

    const rFilter = e.target.closest('[data-rule-status]');
    if (rFilter) {
      const nextStatus = rFilter.dataset.ruleStatus;
      if (nextStatus && nextStatus !== query.rule_status) {
        updateRoute({rule_status: nextStatus});
      }
      return;
    }

    const btn = e.target.closest('button');
    if (!btn) return;
    if (btn.hasAttribute('data-close-flag-rule')) {
      closeRuleDialog();
      return;
    }

    const action = btn.dataset.action;
    if (btn.dataset.flagExport) {
      await performFlagExport(btn.dataset.flagExport);
      return;
    }
    if (action === 'flag-select-all') {
      const keys = (data?.groups || []).map(group => String(group.key ?? ''));
      selectedGroupKeys.clear();
      for (const key of keys) selectedGroupKeys.add(key);
      void refreshExportCount();
      paint();
      return;
    }
    if (action === 'flag-select-none') {
      selectedGroupKeys.clear();
      void refreshExportCount();
      paint();
      return;
    }
    if (action === 'refresh-flags' || action === 'retry') {
      await loadGroups({preserveExpanded: true});
      return;
    }
    if (action === 'apply-pattern') {
      const pat = String(root.querySelector('#flag-pattern-input')?.value || '').trim();
      const mode = String(root.querySelector('#flag-pattern-mode')?.value || 'contains');
      updateRoute({group_by: 'pattern', pattern: pat, pattern_mode: mode});
      return;
    }
    if (action === 'toggle-group') {
      const group = data?.groups?.[Number(btn.dataset.groupIndex)];
      if (!group) return;
      const key = String(group.key ?? '');
      if (expandedGroups.has(key)) {
        expandedGroups.delete(key);
        paint();
      } else {
        expandedGroups.add(key);
        await loadGroupAlerts(key);
      }
      return;
    }
    if (action === 'open-group-rule-modal') {
      const group = data?.groups?.[Number(btn.dataset.groupIndex)];
      if (!group) return;
      openRuleDialog({
        kind: 'group',
        groupKey: String(group.key ?? ''),
        customRuleId: group.custom_rule_id || '',
        ruleNotes: group.rule_notes || '',
        label: `Menandai ${Number(group.pending_count ?? group.alert_count ?? 0).toLocaleString('id-ID')} alert pada grup “${group.key}” (${query.group_by}) sebagai Rule Sudah Dibuat.`,
      });
      return;
    }
    if (action === 'revert-group-rule') {
      const group = data?.groups?.[Number(btn.dataset.groupIndex)];
      if (!group) return;
      await submitRuleStatus({
        rule_status: 'pending',
        flag_color: query.flag_color,
        group_by: query.group_by,
        group_key: String(group.key ?? ''),
        pattern: query.pattern,
        pattern_mode: query.pattern_mode,
        q: query.q,
        current_rule_status: query.rule_status,
      }, `Status custom rule untuk grup “${group.key}” dikembalikan ke Belum Dibuat.`);
      return;
    }
    if (action === 'open-alert-rule-modal') {
      const alertId = Number(btn.dataset.alertId);
      const item = findAlertInCache(alertId);
      openRuleDialog({
        kind: 'alert',
        alertId,
        customRuleId: item?.custom_rule_id || '',
        ruleNotes: item?.rule_notes || '',
        label: `Menandai Alert #${item?.alert_id || alertId} (${item?.description || 'Alert'}) sebagai Rule Sudah Dibuat.`,
      });
      return;
    }
    if (action === 'revert-alert-rule') {
      const alertId = Number(btn.dataset.alertId);
      await submitRuleStatus({
        alert_ids: [alertId],
        rule_status: 'pending',
      }, `Status custom rule alert #${alertId} dikembalikan ke Belum Dibuat.`);
      return;
    }
    if (action === 'unflag-alert') {
      const alertId = Number(btn.dataset.alertId);
      btn.disabled = true;
      try {
        await json(apiURL(`/api/alerts/${alertId}/flag`, tenantParams()), {
          method: 'PUT',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({flag_color: null}),
          signal,
        });
        notify(`Flag alert #${alertId} dihapus.`, 'success');
        window.dispatchEvent(new CustomEvent('arbiter:flags-changed'));
        await loadGroups({preserveExpanded: true});
      } catch (err) {
        if (err.name !== 'AbortError') notify(err.message || 'Gagal menghapus flag alert.', 'error');
      } finally {
        if (btn.isConnected) btn.disabled = false;
      }
      return;
    }
    if (action === 'unreview-alert') {
      const alertId = Number(btn.dataset.alertId);
      btn.disabled = true;
      try {
        await json(apiURL('/api/alerts/batch-review', tenantParams()), {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({alert_ids: [alertId], is_reviewed: false}),
          signal,
        });
        notify(`Alert #${alertId} dikembalikan ke belum direview dan Flag dihapus.`, 'success');
        window.dispatchEvent(new CustomEvent('arbiter:flags-changed'));
        await loadGroups({preserveExpanded: true});
      } catch (err) {
        if (err.name !== 'AbortError') notify(err.message || 'Gagal mengembalikan status alert.', 'error');
      } finally {
        if (btn.isConnected) btn.disabled = false;
      }
      return;
    }
    if (action === 'unflag-group') {
      const group = data?.groups?.[Number(btn.dataset.groupIndex)];
      if (!group) return;
      btn.disabled = true;
      try {
        const res = await json(apiURL('/api/alerts/flag', tenantParams()), {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({
            flag_color: null,
            current_flag_color: query.flag_color,
            group_by: query.group_by,
            group_key: String(group.key ?? ''),
            current_rule_status: query.rule_status,
            pattern: query.pattern,
            pattern_mode: query.pattern_mode,
            q: query.q,
          }),
          signal,
        });
        notify(`${Number(res.count || 0).toLocaleString('id-ID')} alert pada grup “${group.key}” berhasil dihapus Flag-nya.`, 'success');
        window.dispatchEvent(new CustomEvent('arbiter:flags-changed'));
        await loadGroups({preserveExpanded: true});
      } catch (err) {
        if (err.name !== 'AbortError') notify(err.message || 'Gagal menghapus flag grup.', 'error');
      } finally {
        if (btn.isConnected) btn.disabled = false;
      }
      return;
    }
    if (action === 'unreview-group') {
      const group = data?.groups?.[Number(btn.dataset.groupIndex)];
      if (!group) return;
      btn.disabled = true;
      try {
        const res = await json(apiURL('/api/alerts/flag', tenantParams()), {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({
            flag_color: null,
            unreview: true,
            current_flag_color: query.flag_color,
            group_by: query.group_by,
            group_key: String(group.key ?? ''),
            current_rule_status: query.rule_status,
            pattern: query.pattern,
            pattern_mode: query.pattern_mode,
            q: query.q,
          }),
          signal,
        });
        notify(`${Number(res.count || 0).toLocaleString('id-ID')} alert pada grup “${group.key}” dikembalikan ke belum direview dan Flag dihapus.`, 'success');
        window.dispatchEvent(new CustomEvent('arbiter:flags-changed'));
        await loadGroups({preserveExpanded: true});
      } catch (err) {
        if (err.name !== 'AbortError') notify(err.message || 'Gagal mengembalikan grup ke belum direview.', 'error');
      } finally {
        if (btn.isConnected) btn.disabled = false;
      }
      return;
    }
    if (action === 'toggle-flag-log') {
      const alertId = Number(btn.dataset.alertId);
      if (expandedLogIds.has(alertId)) expandedLogIds.delete(alertId);
      else expandedLogIds.add(alertId);
      paint();
      return;
    }
    if (action === 'copy-flag-log') {
      const item = findAlertInCache(Number(btn.dataset.alertId));
      const log = item?.full_log || '';
      if (!log) { notify('Full log tidak tersedia.', 'error'); return; }
      try {
        await copyText(log);
        notify('Full log alert disalin.', 'success');
      } catch (err) {
        notify(err.message || 'Gagal menyalin log.', 'error');
      }
    }
  }, {signal});

  root.addEventListener('change', async e => {
    const el = e.target;
    if (el.matches('[data-select-group-index]')) {
      const group = data?.groups?.[Number(el.dataset.selectGroupIndex)];
      if (!group) return;
      const key = String(group.key ?? '');
      if (el.checked) selectedGroupKeys.add(key);
      else selectedGroupKeys.delete(key);
      void refreshExportCount();
      paint();
      return;
    }
    if (el.id === 'flag-group-by') {
      updateRoute({group_by: el.value, pattern: el.value === 'pattern' ? query.pattern : null});
      return;
    }
    if (el.id === 'flag-pattern-mode') {
      const pat = String(root.querySelector('#flag-pattern-input')?.value || '').trim();
      updateRoute({group_by: 'pattern', pattern: pat, pattern_mode: el.value});
      return;
    }
    if (el.matches('[data-change-alert-flag]')) {
      const alertId = Number(el.dataset.changeAlertFlag);
      const nextColor = el.value;
      const bodyPayload = nextColor ? {flag_color: nextColor, auto_review: true} : {flag_color: null};
      el.disabled = true;
      try {
        await json(apiURL(`/api/alerts/${alertId}/flag`, tenantParams()), {
          method: 'PUT',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify(bodyPayload),
          signal,
        });
        notify(
          nextColor
            ? `Flag alert #${alertId} diperbarui menjadi ${nextColor === 'green' ? 'Hijau' : nextColor === 'yellow' ? 'Kuning' : 'Merah'}.`
            : `Flag alert #${alertId} dihapus.`,
          'success',
        );
        window.dispatchEvent(new CustomEvent('arbiter:flags-changed'));
        await loadGroups({preserveExpanded: true});
      } catch (err) {
        if (err.name !== 'AbortError') notify(err.message || 'Gagal mengubah flag.', 'error');
        el.disabled = false;
      }
    }
  }, {signal});

  root.addEventListener('input', e => {
    if (e.target.id === 'flag-search') {
      clearTimeout(searchTimer);
      const val = e.target.value;
      searchTimer = setTimeout(() => updateRoute({q: val}, {replace: true}), 350);
    }
  }, {signal});

  root.addEventListener('keydown', e => {
    if (e.target.id === 'flag-pattern-input' && e.key === 'Enter') {
      e.preventDefault();
      const pat = String(e.target.value || '').trim();
      const mode = String(root.querySelector('#flag-pattern-mode')?.value || 'contains');
      updateRoute({group_by: 'pattern', pattern: pat, pattern_mode: mode});
    }
  }, {signal});

  root.addEventListener('submit', async e => {
    if (e.target.id !== 'flag-rule-form' || !pendingRuleTarget) return;
    e.preventDefault();
    const customRuleId = String(root.querySelector('#flag-custom-rule-id')?.value || '').trim();
    const ruleNotes = String(root.querySelector('#flag-rule-notes')?.value || '').trim();
    const submitBtn = e.target.querySelector('button[type="submit"]');
    if (submitBtn) submitBtn.disabled = true;
    const payload = pendingRuleTarget.kind === 'group'
      ? {
          rule_status: 'done',
          custom_rule_id: customRuleId,
          rule_notes: ruleNotes,
          flag_color: query.flag_color,
          group_by: query.group_by,
          group_key: pendingRuleTarget.groupKey,
          pattern: query.pattern,
          pattern_mode: query.pattern_mode,
          q: query.q,
          current_rule_status: query.rule_status,
        }
      : {
          alert_ids: [pendingRuleTarget.alertId],
          rule_status: 'done',
          custom_rule_id: customRuleId,
          rule_notes: ruleNotes,
        };
    try {
      const res = await json(apiURL('/api/flags/rule-status', tenantParams()), {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload),
        signal,
      });
      closeRuleDialog();
      notify(`${Number(res.updated || 1).toLocaleString('id-ID')} alert ditandai sebagai Rule Sudah Dibuat${customRuleId ? ` (#${customRuleId})` : ''}.`, 'success');
      window.dispatchEvent(new CustomEvent('arbiter:flags-changed'));
      await loadGroups({preserveExpanded: true});
    } catch (err) {
      if (err.name !== 'AbortError') setDialogStatus(err.message || 'Gagal menyimpan status rule.');
    } finally {
      if (submitBtn) submitBtn.disabled = false;
    }
  }, {signal});

  root.addEventListener('arbiter:refresh', () => loadGroups({preserveExpanded: true}), {signal});

  loadGroups();

  return () => {
    clearTimeout(searchTimer);
    activeRequest?.abort();
    closeRuleDialog();
  };
}
