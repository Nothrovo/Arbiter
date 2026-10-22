import {json, apiURL, copyText} from '../../api/client.js';
import {esc, icon, severity, formatTime, emptyState, errorState, loadingRows} from '../../ui/primitives.js';
import {queryFrom, scopeParams} from '../../state/scope.js';
import {withParams} from '../../router.js';
import {createTriageSession} from '../../state/triage.js';
import {intelSummary, renderQueue} from './model.js';

const presets = [['','Semua jenis'],['403','403 Forbidden'],['404','404 Probes'],['repeating','Berulang'],['non_http','Non-HTTP'],['bot','Bot traffic'],['curl','Curl requests']];
export function mount(ctx) {
  const {root, route, signal, selection, navigate, notify} = ctx;
  const query = queryFrom(route.params);
  root.classList.add('triage-page');
  const session = createTriageSession();
  let items = [], total = 0, pageRequest, detailRequest, generation = 0, currentAlert = null, lastSelected = null, searchTimer;
  let activeTab = 'detail', activeId = route.params.get('alert'), showIntel = true;
  root.innerHTML = `<div class="page-header"><div class="page-heading"><h1>Triage</h1><p class="page-description">Periksa bukti. Tentukan langkah berikutnya.</p></div><div class="page-actions"><a class="button primary" href="${withParams('/imports',new URLSearchParams({tenant:query.tenant}))}">${icon('upload')}Impor</a></div></div>
    <div class="tabs" aria-label="Antrean review">${[['unreviewed','Belum direview'],['all','Semua'],['reviewed','Direview']].map(([key,label])=>`<button class="tab" data-review="${key}" aria-pressed="${query.review_status===key}">${label}</button>`).join('')}</div>
    <div class="toolbar"><div class="search-field"><label class="sr-only" for="triage-search">Cari alert</label>${icon('search')}<input type="search" id="triage-search" name="q" value="${esc(query.q)}" placeholder="Cari IP, asset, rule…" autocomplete="off" spellcheck="false"></div><button class="button" data-action="filters">${icon('filter')}Filter${query.filter_preset||query.status!=='all'||query.group_id?' aktif':''}</button><label class="sr-only" for="triage-sort">Urutan alert</label><select class="sort-control" id="triage-sort" name="sort"><option value="timestamp:desc">Terbaru</option><option value="timestamp:asc">Kronologis</option><option value="severity:desc">Severity tertinggi</option><option value="hits:desc">Hits terbanyak</option></select><button class="button icon-button" data-action="more" aria-label="Opsi antrean" aria-controls="queue-options" aria-expanded="false">${icon('more')}</button></div>
    <div id="queue-options" class="toolbar" hidden><label class="checkbox-label"><input type="checkbox" id="show-intel" checked>Kolom source / intel</label><button class="button" data-action="correlation">Korelasi</button><button class="button" data-action="report-query">Laporan hasil filter</button></div>
    <div id="applied-filters" class="applied-filters"></div><div id="correlation-slot"></div>
    <div class="triage-workspace" id="triage-workspace"><section class="queue-region" aria-label="Antrean kerja"><div id="selection-actions"></div><div id="queue-results">${loadingRows()}</div><div class="pagination" id="queue-pagination"></div></section><aside id="alert-inspector" class="inspector" aria-label="Detail alert" hidden></aside></div>
    <dialog class="filter-dialog" id="triage-filter-dialog" aria-labelledby="filter-title"><div class="dialog-header"><h2 id="filter-title">Filter &amp; urutan</h2><button class="button icon-button" data-close-filter aria-label="Tutup filter">${icon('close')}</button></div><form id="triage-filter-form" class="filter-form"><div class="field"><label for="filter-preset">Jenis event</label><select id="filter-preset" name="filter_preset">${presets.map(([v,l])=>`<option value="${v}" ${v===query.filter_preset?'selected':''}>${l}</option>`).join('')}</select></div><div class="field"><label for="filter-membership">Keanggotaan insiden</label><select id="filter-membership" name="status"><option value="all">Semua</option><option value="ungrouped">Belum masuk insiden</option><option value="grouped">Sudah masuk insiden</option></select></div><div class="field"><label for="filter-sort">Urutan</label><select id="filter-sort" name="ordering"><option value="timestamp:desc">Terbaru</option><option value="timestamp:asc">Kronologis</option><option value="severity:desc">Severity tertinggi</option><option value="hits:desc">Hits terbanyak</option></select></div><p class="meta">Tenant mengikuti workspace. Pilihan alert tetap tersimpan saat filter berubah.</p><div class="dialog-actions"><button type="button" class="button" data-action="reset">Reset filter</button><button class="button primary" type="submit">Terapkan</button></div></form></dialog>`;
  const results = root.querySelector('#queue-results'), inspector = root.querySelector('#alert-inspector');
  const workspace = root.querySelector('#triage-workspace');
  const dialog = root.querySelector('#triage-filter-dialog');
  root.querySelector('#triage-sort').value = `${query.sort_by}:${query.sort}`;
  root.querySelector('#filter-sort').value = `${query.sort_by}:${query.sort}`;
  root.querySelector('#filter-membership').value = query.status;
  const on = (el,type,fn) => el.addEventListener(type,fn,{signal});
  function updateQuery(changes, {replace=false}={}) {
    const p = new URLSearchParams(route.params);
    for (const [k,v] of Object.entries(changes)) v===null||v===''?p.delete(k):p.set(k,String(v));
    if (!Object.hasOwn(changes,'offset')) p.delete('offset');
    p.delete('alert');
    navigate(withParams('/triage',p),{replace});
  }
  function report(ids) {
    const p=scopeParams(query,ids?.length?{ids}:{});
    navigate(withParams('/reports',p));
  }
  function syncSelection() {
    const ids=selection.ids();
    root.querySelectorAll('[data-select]').forEach(el=>{el.checked=selection.has(Number(el.dataset.select));});
    root.querySelectorAll('[data-row]').forEach(el=>{const selected=selection.has(Number(el.dataset.row));el.setAttribute('aria-selected',String(selected));el.classList.toggle('is-selected',selected);});
    const visible=items.filter(a=>selection.has(a.id)).length;
    root.querySelectorAll('[data-select-page]').forEach(el=>{el.checked=!!items.length&&visible===items.length;el.indeterminate=visible>0&&visible<items.length;});
    const slot=root.querySelector('#selection-actions');
    slot.innerHTML=ids.length?`<div class="selection-toolbar" aria-label="Tindakan pilihan"><strong>${ids.length.toLocaleString('id-ID')} alert dipilih</strong><button class="button primary" data-action="create-incident">${icon('plus')}Buat insiden</button><button class="button" data-action="batch-review">Tandai direview</button><button class="button" data-action="batch-unreview">Belum direview</button><button class="button" data-action="report-selected">Laporan</button><button class="button icon-button" data-action="clear-selection" aria-label="Batalkan pilihan">${icon('close')}</button>${ids.length>visible?`<span class="selection-note">${ids.length-visible} pilihan berada di luar halaman/filter ini. Tindakan memakai seluruh pilihan pada tenant ini.</span>`:''}</div>`:'';
  }
  function renderResults() {
    if (!items.length) results.innerHTML=emptyState('Tidak ada alert pada antrean ini',query.q||query.filter_preset||query.group_id||query.review_status!=='all'?'Coba reset filter atau lihat antrean Semua. Pilihan sebelumnya tetap tersimpan.':'Impor export Wazuh untuk memulai triage.',`<button class="button" data-action="reset">Reset filter</button><a class="button primary" href="${withParams('/imports',new URLSearchParams({tenant:query.tenant}))}">Impor alert</a>`);
    else results.innerHTML=renderQueue(items,{selectedIds:selection.ids(),activeId,query,showIntel});
    root.querySelector('#queue-pagination').innerHTML=`<span>${total?`${(query.offset+1).toLocaleString('id-ID')}–${Math.min(query.offset+items.length,total).toLocaleString('id-ID')}`:'0'} dari ${total.toLocaleString('id-ID')} alert · ${query.limit} per halaman</span><div class="pagination-actions"><button class="button" data-page="previous" ${query.offset===0?'disabled':''}>Sebelumnya</button><button class="button" data-page="next" ${query.offset+items.length>=total?'disabled':''}>Berikutnya</button></div>`;
    syncSelection();
  }
  async function load() {
    pageRequest?.abort();pageRequest=new AbortController();const version=++generation;
    const abort=()=>pageRequest?.abort();signal.addEventListener('abort',abort,{once:true});
    results.setAttribute('aria-busy','true');
    try {
      const data=await json(apiURL('/api/alerts',{...query,summary:true}),{signal:pageRequest.signal});
      if(signal.aborted||version!==generation)return;
      if(!Array.isArray(data.items)||!Number.isFinite(Number(data.total)))throw new Error('Format antrean tidak valid. Coba lagi.');
      items=data.items;total=Number(data.total);renderResults();
      if(activeId)await openInspector(activeId,false);
    } catch(e) {if(e.name!=='AbortError'&&!signal.aborted)results.innerHTML=errorState(e.message);}
    finally {results.removeAttribute('aria-busy');signal.removeEventListener('abort',abort);}
  }
  function setInspectorURL(id) {
    const p=new URLSearchParams(route.params);id?p.set('alert',id):p.delete('alert');
    history.replaceState(null,'',withParams('/triage',p));
    window.dispatchEvent(new Event('arbiter:route-replaced'));
  }
  function closeInspector() {
    const old=activeId;const scroll=session.close();activeId=null;currentAlert=null;detailRequest?.abort();inspector.hidden=true;workspace.classList.remove('has-inspector');setInspectorURL(null);renderResults();
    requestAnimationFrame(()=>{window.scrollTo(0,scroll);root.querySelector(`[data-inspect="${Number(old)}"]`)?.focus({preventScroll:true});});
  }
  function inspectorBody(a) {
    if(activeTab==='raw')return `<div class="split"><h3>Raw alert JSON</h3><button class="button" data-action="copy-raw">${icon('copy')}Salin raw</button></div><p class="warning-copy">Konten mentah dapat memuat informasi sensitif. Tinjau sebelum dibagikan.</p><pre class="raw-log">${esc(JSON.stringify(a.raw||{},null,2))}</pre>`;
    if(activeTab==='occurrences')return `<div class="split"><h3>Kejadian berulang</h3><span class="meta num">${Number(a.hit_count)||1} hits</span></div><dl class="detail-grid"><div class="key-value"><dt>Pertama</dt><dd>${esc(formatTime(a.first_seen||a.timestamp))}</dd></div><div class="key-value"><dt>Terakhir</dt><dd>${esc(formatTime(a.last_seen||a.timestamp))}</dd></div></dl><ol class="timeline">${(a.duplicate_instances?.length?a.duplicate_instances:[{timestamp:a.timestamp,id:a.alert_id}]).map(inst=>`<li><time>${esc(formatTime(inst.timestamp))}</time><span class="meta mono">${esc(inst.id||'—')}</span>${inst.full_log?`<details><summary>Log kejadian</summary><pre class="raw-log">${esc(inst.full_log)}</pre></details>`:''}</li>`).join('')}</ol>`;
    const log=a.full_log||a.raw?.full_log;
    return `<dl class="detail-grid"><div class="key-value"><dt>Target asset</dt><dd>${esc(a.agent_name||'—')}</dd></div><div class="key-value"><dt>Tenant</dt><dd>${esc(a.tenant||'Default')}</dd></div><div class="key-value"><dt>Detection rule</dt><dd>${esc(a.rule_id||'—')} · Level ${Number(a.rule_level)||0}</dd></div><div class="key-value"><dt>Waktu</dt><dd>${esc(formatTime(a.timestamp))}</dd></div><div class="key-value wide"><dt>Source / intel</dt><dd class="mono">${esc(a.source_ip||'—')}</dd><dd class="meta">${esc(intelSummary(a))}</dd>${a.source_ip?`<dd><a class="button" href="http://localhost:3001/ip/${encodeURIComponent(a.source_ip)}" rel="noopener noreferrer" target="_blank">Buka IP Intel ${icon('external')}</a></dd>`:''}</div>${a.cve?`<div class="key-value"><dt>CVE</dt><dd>${esc(a.cve)}</dd></div>`:''}${a.mitre_ids?.length?`<div class="key-value wide"><dt>MITRE</dt><dd>${esc(a.mitre_ids.join(', '))}</dd></div>`:''}</dl>${log?`<section class="stack"><div class="split"><h3>Log utama</h3><button class="button" data-action="copy-redacted">Versi tersamarkan</button></div><pre class="raw-log">${esc(log)}</pre><p class="meta">Redaksi otomatis bukan jaminan aman untuk cloud. Tinjau hasil sebelum membagikan.</p></section>`:''}${a.previous_output?`<details><summary>Previous output</summary><pre class="raw-log">${esc(a.previous_output)}</pre></details>`:''}<section class="stack"><h3>Insiden terkait</h3>${a.groups?.length?a.groups.map(g=>`<div class="split"><a href="${withParams('/incidents/'+encodeURIComponent(g.id),new URLSearchParams({tenant:query.tenant}))}">${esc(g.title)}</a><button class="button icon-button" data-remove-group="${esc(g.id)}" aria-label="Keluarkan dari insiden ${esc(g.title)}">${icon('close')}</button></div>`).join(''):'<p class="meta">Belum terhubung ke insiden.</p>'}<div class="field"><label for="inspector-group">Tambahkan ke insiden</label><select id="inspector-group" name="group_id"><option value="">Memuat insiden…</option></select></div><button class="button" data-action="add-group">Tambahkan bukti</button></section><div class="inspector-actions"><button class="button primary" data-action="review-current">${a.is_reviewed?'Kembalikan ke belum direview':'Tandai direview'}</button><button class="button" data-action="create-current">Buat insiden</button></div>`;
  }
  async function renderInspector() {
    const a=currentAlert;if(!a)return;
    inspector.innerHTML=`<div class="inspector-head"><div class="inspector-title">${severity(a.rule_level)}<h2 tabindex="-1" id="inspector-title">${esc(a.description||'Detail alert')}</h2><span class="meta mono">${esc(a.alert_id||a.id)}</span></div><button class="button icon-button" data-action="close-inspector" aria-label="Tutup detail dan kembali ke antrean">${icon('close')}</button></div><div class="tabs inspector-tabs" aria-label="Bagian detail">${[['detail','Detail'],['occurrences','Kejadian'],['raw','Raw JSON']].map(([k,l])=>`<button class="tab" data-detail-tab="${k}" aria-pressed="${activeTab===k}">${l}</button>`).join('')}</div><div class="inspector-content">${inspectorBody(a)}</div>`;
    if(activeTab==='detail')try{
      const groups=await json(apiURL('/api/groups',{tenant:query.tenant}),{signal});
      const select=root.querySelector('#inspector-group');if(select)select.innerHTML='<option value="">Pilih insiden…</option>'+groups.filter(g=>!a.groups?.some(link=>link.id===g.id)).map(g=>`<option value="${esc(g.id)}">${esc(g.title)}</option>`).join('');
    }catch(e){if(e.name!=='AbortError'){const select=root.querySelector('#inspector-group');if(select)select.innerHTML='<option value="">Tidak dapat memuat insiden</option>';}}
  }
  async function openInspector(id,focus=true) {
    if(!session.activeId())session.rememberQueue(window.scrollY);session.open(id);const detailVersion=session.nextDetail();
    activeId=Number(id);detailRequest?.abort();detailRequest=new AbortController();
    inspector.hidden=false;workspace.classList.add('has-inspector');inspector.innerHTML=loadingRows(3);setInspectorURL(activeId);
    try{
      const a=await json(apiURL(`/api/alerts/${activeId}`,{tenant:query.tenant}),{signal:detailRequest.signal});if(signal.aborted||!session.isCurrentDetail(detailVersion)||Number(a.id)!==activeId)return;
      currentAlert=a;await renderInspector();renderResults();if(focus)root.querySelector('#inspector-title')?.focus({preventScroll:true});
    }catch(e){if(e.name!=='AbortError'&&!signal.aborted&&session.isCurrentDetail(detailVersion))inspector.innerHTML=`<div class="inspector-content">${errorState(e.message)}<button class="button" data-action="close-inspector">Kembali ke antrean</button></div>`;}
  }
  async function batch(reviewed,ids=selection.ids()) {
    if(!ids.length)return;
    try{await json(apiURL('/api/alerts/batch-review',{tenant:query.tenant}),{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({alert_ids:ids,is_reviewed:reviewed,tenant:query.tenant}),signal});notify(reviewed?'Alert ditandai direview.':'Alert dikembalikan ke antrean.','success');await load();}
    catch(e){if(e.name!=='AbortError')notify(e.message,'error');}
  }
  async function correlation(){
    const slot=root.querySelector('#correlation-slot');slot.innerHTML=`<div class="correlation-panel">${loadingRows(2)}</div>`;
    try{const d=await json(apiURL('/api/suggestions',scopeParams(query)),{signal});slot.innerHTML=`<section class="correlation-panel stack"><div class="split"><h2>Korelasi lokal</h2><button class="button icon-button" data-action="close-correlation" aria-label="Tutup korelasi">${icon('close')}</button></div><p class="meta">${esc(d.warning||'Saran berdasarkan rule lokal, bukan keputusan investigasi.')}</p>${d.suggestions?.length?d.suggestions.map((g,i)=>`<div class="evidence-row"><strong>${esc(g.title||g.category||'Saran insiden')}</strong><p class="meta">${esc(g.analysis||g.reason||'Tinjau bukti sebelum membuat insiden.')}</p><button class="button" data-suggestion="${i}">Tinjau sebagai insiden</button></div>`).join(''):'<p>Tidak ada saran pada scope ini.</p>'}</section>`;slot._suggestions=d.suggestions||[];}
    catch(e){if(e.name!=='AbortError')slot.innerHTML=errorState(e.message);}
  }
  on(root,'click',async e=>{
    const button=e.target.closest('button');if(!button)return;
    if(button.dataset.review){updateQuery({review_status:button.dataset.review});return;}
    if(button.dataset.sort){updateQuery({sort_by:button.dataset.sort,sort:query.sort_by===button.dataset.sort&&query.sort==='desc'?'asc':'desc'});return;}
    if(button.dataset.inspect){activeTab='detail';await openInspector(button.dataset.inspect);return;}
    if(button.dataset.detailTab){activeTab=button.dataset.detailTab;await renderInspector();return;}
    if(button.dataset.page){updateQuery({offset:button.dataset.page==='next'?query.offset+query.limit:Math.max(0,query.offset-query.limit)});return;}
    if(button.hasAttribute('data-close-filter')){dialog.close();return;}
    if(button.dataset.removeGroup){try{await json(apiURL(`/api/groups/${encodeURIComponent(button.dataset.removeGroup)}/members/${currentAlert.id}`,{tenant:query.tenant}),{method:'DELETE',signal});await openInspector(currentAlert.id,false);notify('Bukti dikeluarkan dari insiden.','success');}catch(err){if(err.name!=='AbortError')notify(err.message,'error');}return;}
    if(button.dataset.suggestion){const g=root.querySelector('#correlation-slot')._suggestions[Number(button.dataset.suggestion)];const ids=(g.alert_pks||g.alert_ids||[]).map(Number).filter(Number.isSafeInteger);if(ids.length)navigate(withParams('/incidents/new',new URLSearchParams({tenant:query.tenant,alert_ids:ids.join(',')})));else notify('Saran tidak memiliki ID bukti yang valid. Pilih bukti dari antrean.','error');return;}
    const action=button.dataset.action;
    if(action==='filters'){dialog.showModal();return;}
    if(action==='more'){const opts=root.querySelector('#queue-options');opts.hidden=!opts.hidden;button.setAttribute('aria-expanded',String(!opts.hidden));return;}
    if(action==='reset'){dialog.close();navigate(withParams('/triage',new URLSearchParams({tenant:query.tenant,review_status:'all'})));return;}
    if(action==='retry'){if(button.closest('#alert-inspector'))openInspector(activeId);else load();return;}
    if(action==='close-inspector'){closeInspector();return;}
    if(action==='clear-selection'){selection.clear();syncSelection();return;}
    if(action==='report-query'){report();return;}
    if(action==='report-selected'){report(selection.ids());return;}
    if(action==='create-incident'||action==='create-current'){const ids=action==='create-current'?[currentAlert.id]:selection.ids();navigate(withParams('/incidents/new',new URLSearchParams({tenant:query.tenant,alert_ids:ids.join(',')})));return;}
    if(action==='batch-review'||action==='batch-unreview'||action==='review-current'){button.disabled=true;await batch(action==='review-current'?!currentAlert.is_reviewed:action==='batch-review',action==='review-current'?[currentAlert.id]:selection.ids());if(button.isConnected)button.disabled=false;return;}
    if(action==='add-group'){const id=root.querySelector('#inspector-group').value;if(!id){notify('Pilih insiden terlebih dahulu.','error');return;}button.disabled=true;try{await json(apiURL(`/api/groups/${encodeURIComponent(id)}/members`,{tenant:query.tenant}),{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({alert_pks:[currentAlert.id],tenant:query.tenant}),signal});await openInspector(currentAlert.id,false);notify('Bukti ditambahkan ke insiden.','success');}catch(err){if(err.name!=='AbortError')notify(err.message,'error');}finally{button.disabled=false;}return;}
    if(action==='copy-raw'||action==='copy-redacted'){button.disabled=true;try{let text=action==='copy-raw'?JSON.stringify(currentAlert.raw||{},null,2):currentAlert.full_log||currentAlert.raw?.full_log||'';if(action==='copy-redacted'){const d=await json('/api/sanitize-logs',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text}),signal});text=d.sanitized;await copyText(text);notify('Versi tersamarkan disalin. Tinjau sebelum dibagikan.','info');}else{await copyText(text);notify('Raw JSON disalin. Berisi data sensitif.','info');}}catch(err){if(err.name!=='AbortError')notify('Gagal menyalin. Clipboard tidak diizinkan; salin manual dari panel.','error');}finally{button.disabled=false;}return;}
    if(action==='correlation'){correlation();return;}
    if(action==='close-correlation')root.querySelector('#correlation-slot').innerHTML='';
  });
  on(root,'change',e=>{
    const el=e.target;
    if(el.matches('[data-select]')){const id=Number(el.dataset.select);if(el._shift&&lastSelected!==null)selection.selectRange(items.map(a=>a.id),lastSelected,id,el.checked);else selection.toggle(id,el.checked);lastSelected=id;syncSelection();}
    if(el.matches('[data-select-page]')){items.forEach(a=>selection.toggle(a.id,el.checked));syncSelection();}
    if(el.id==='triage-sort'){const [sort_by,sort]=el.value.split(':');updateQuery({sort_by,sort});}
    if(el.id==='show-intel'){showIntel=el.checked;renderResults();}
  });
  on(root,'click',e=>{if(e.target.matches('[data-select]'))e.target._shift=e.shiftKey;});
  on(root.querySelector('#triage-search'),'input',e=>{clearTimeout(searchTimer);const q=e.target.value;searchTimer=setTimeout(()=>updateQuery({q},{replace:true}),350);});
  on(root.querySelector('#triage-filter-form'),'submit',e=>{e.preventDefault();const form=new FormData(e.target);const [sort_by,sort]=form.get('ordering').split(':');dialog.close();updateQuery({filter_preset:form.get('filter_preset'),status:form.get('status'),sort_by,sort});});
  on(root,'keydown',e=>{if(e.key==='Escape'&&activeId&&!dialog.open){e.preventDefault();closeInspector();}});
  on(root,'arbiter:refresh',()=>load());
  const filters=[];if(query.q)filters.push(`Pencarian: ${esc(query.q)}`);if(query.filter_preset)filters.push(esc(presets.find(([v])=>v===query.filter_preset)?.[1]));if(query.group_id)filters.push('Bukti insiden terpilih');if(query.status!=='all')filters.push(query.status==='grouped'?'Sudah masuk insiden':'Belum masuk insiden');
  root.querySelector('#applied-filters').innerHTML=filters.length?`${filters.map(f=>`<span>${f}</span>`).join('')}<button class="button" data-action="reset">Reset</button>`:'';
  load();
  return ()=>{session.dispose();root.classList.remove('triage-page');clearTimeout(searchTimer);pageRequest?.abort();detailRequest?.abort();dialog.close();};
}
