import {createRouter, withParams} from './router.js';
import {json} from './api/client.js';
import {createSelection} from './state/selection.js';
import {probeConnection} from './state/workspace.js';
import {createNavigationMemory} from './state/navigation.js';
import {esc, icon, emptyState, errorState, loadingRows} from './ui/primitives.js';

const main=document.querySelector('#main-content');
const tenantSelect=document.querySelector('#workspace-tenant');
const selection=createSelection(new URLSearchParams(location.hash.split('?')[1]||'').get('tenant')||'all');
let currentRoute, controller, cleanup, guard=null, notifyTimer, healthPending=false, lastHealth=null, routeVersion=0;
const scrollPositions=new Map();
const navigationMemory=createNavigationMemory();
const pageTitles={triage:'Triage',incidents:'Insiden',imports:'Impor',reports:'Laporan',database:'Database'};
for(const el of document.querySelectorAll('[data-icon]'))el.innerHTML=icon(el.dataset.icon);
document.querySelector('#open-navigation').innerHTML=icon('menu');
document.querySelector('#close-navigation').innerHTML=icon('close');
document.querySelector('#refresh-workspace').innerHTML=icon('refresh');
document.querySelector('[data-close-dialog]').innerHTML=icon('close');

function notify(message,kind='info'){
  const region=document.querySelector('#notifications');clearTimeout(notifyTimer);
  region.innerHTML=`<div class="notice" data-kind="${esc(kind)}"><p>${esc(message)}</p><button class="button icon-button" aria-label="Tutup pemberitahuan">${icon('close')}</button></div>`;
  region.querySelector('button').addEventListener('click',()=>{region.innerHTML='';});
  if(kind!=='error')notifyTimer=setTimeout(()=>{region.innerHTML='';},5500);
}
function canLeave(next){
  if(guard&&!guard()&&!confirm('Ada perubahan yang belum disimpan. Tinggalkan halaman dan buang perubahan?'))return false;
  const nextTenant=next.params.get('tenant')||'all';
  if(selection.scope()!==nextTenant&&selection.size()&&!confirm(`Ganti tenant dan batalkan ${selection.size()} pilihan alert?`))return false;
  selection.setScope(nextTenant,true);return true;
}
const router=createRouter(render,canLeave);
async function render(route){
  const version=++routeVersion;
  const oldSearch=main.querySelector('#triage-search');
  const restoreSearch=oldSearch===document.activeElement?{start:oldSearch.selectionStart,end:oldSearch.selectionEnd}:null;
  if(currentRoute){scrollPositions.set(currentRoute.path+'?'+currentRoute.params,window.scrollY);navigationMemory.remember(currentRoute);}
  controller?.abort();if(typeof cleanup==='function')cleanup();cleanup=null;guard=null;
  controller=new AbortController();currentRoute=route;navigationMemory.remember(route);
  closeNav(false);
  const tenant=route.params.get('tenant')||'all';
  if(![...tenantSelect.options].some(o=>o.value===tenant)){const o=new Option(tenant,tenant);tenantSelect.add(o);}
  tenantSelect.value=tenant;
  for(const link of document.querySelectorAll('.nav-link')){
    const active=link.dataset.page===route.page;
    active?link.setAttribute('aria-current','page'):link.removeAttribute('aria-current');
    link.href=navigationMemory.destination(link.dataset.page,tenant);
  }
  document.querySelector('.wordmark').href=withParams('/triage',new URLSearchParams({tenant}));
  document.title=`${pageTitles[route.page]||'Halaman tidak ditemukan'} — Arbiter`;
  main.innerHTML=loadingRows();
  if(route.page==='not-found'){
    main.innerHTML=`<div class="page-header"><h1>Halaman tidak ditemukan</h1></div>${emptyState('Tujuan ini tidak tersedia','Kembali ke antrean untuk melanjutkan pekerjaan.',`<a class="button primary" href="${withParams('/triage',new URLSearchParams({tenant}))}">Buka Triage</a>`)}`;return;
  }
  try{
    const feature=await import(`./features/${route.page}/view.js`);
    if(version!==routeVersion)return;
    const context={root:main,route,navigate:(...args)=>router.navigate(...args),selection,notify,signal:controller.signal,setGuard:fn=>{guard=fn;}};
    const dispose=await feature.mount(context);
    if(version!==routeVersion){if(typeof dispose==='function')dispose();return;}
    cleanup=dispose;
    if(restoreSearch&&route.page==='triage'){
      const search=main.querySelector('#triage-search');search?.focus({preventScroll:true});search?.setSelectionRange(restoreSearch.start,restoreSearch.end);
    }else if(!route.params.has('alert')){
      requestAnimationFrame(()=>{main.querySelector('h1')?.setAttribute('tabindex','-1');main.querySelector('h1')?.focus({preventScroll:true});window.scrollTo(0,scrollPositions.get(route.path+'?'+route.params)||0);});
    }
  }catch(error){
    if(error.name==='AbortError'||version!==routeVersion)return;
    main.innerHTML=`<h1>${pageTitles[route.page]}</h1>${errorState('Area kerja belum dapat dimuat. Muat ulang untuk mencoba lagi.')}`;
    main.querySelector('[data-action=retry]')?.addEventListener('click',()=>render(route),{signal:controller.signal});
  }
}
async function health(force=false){
  if(healthPending||(!force&&document.hidden&&lastHealth))return;
  healthPending=true;const el=document.querySelector('#connection-state');
  try{const result=await probeConnection(()=>json('/api/health',{timeout:10000}),lastHealth);lastHealth=result.lastSuccess;el.dataset.state=result.state;el.querySelector('.connection-label').textContent=result.label;el.title=lastHealth?`${result.label} · Terakhir diperiksa ${lastHealth.toLocaleTimeString('id-ID')}`:result.label;}
  finally{healthPending=false;}
}
async function tenants(){
  try{
    const data=await json('/api/tenants',{timeout:10000});
    const selected=tenantSelect.value;
    tenantSelect.innerHTML='<option value="all">Semua tenant</option>'+(data.tenants||[]).map(t=>`<option value="${esc(t.tenant)}">${esc(t.tenant)}</option>`).join('');
    if(![...tenantSelect.options].some(o=>o.value===selected))tenantSelect.add(new Option(selected,selected));tenantSelect.value=selected;
  }catch{tenantSelect.title='Daftar tenant belum dapat diperbarui. Scope saat ini tetap dipertahankan.';}
}
tenantSelect.addEventListener('change',()=>{
  const p=new URLSearchParams(currentRoute.params);p.set('tenant',tenantSelect.value);p.delete('offset');p.delete('alert');p.delete('alert_ids');p.delete('group_id');
  const target=currentRoute.path.startsWith('/incidents/')?'/incidents':currentRoute.path;
  router.navigate(withParams(target,p));
  setTimeout(()=>{tenantSelect.value=currentRoute.params.get('tenant')||'all';},0);
});
document.querySelector('#refresh-workspace').addEventListener('click',async e=>{
  const button=e.currentTarget;button.disabled=true;await Promise.all([health(),tenants()]);main.dispatchEvent(new CustomEvent('arbiter:refresh'));button.disabled=false;
});
const sidebar=document.querySelector('#sidebar'),scrim=document.querySelector('#nav-scrim');
function openNav(){sidebar.classList.add('is-open');scrim.classList.add('is-open');document.querySelector('#open-navigation').setAttribute('aria-expanded','true');document.querySelector('#workspace').inert=true;sidebar.querySelector('.nav-link')?.focus();}
function closeNav(restore=true){const wasOpen=sidebar.classList.contains('is-open');sidebar.classList.remove('is-open');scrim.classList.remove('is-open');document.querySelector('#open-navigation').setAttribute('aria-expanded','false');document.querySelector('#workspace').inert=false;if(wasOpen&&restore)document.querySelector('#open-navigation').focus();}
document.querySelector('#open-navigation').addEventListener('click',openNav);
document.querySelector('#close-navigation').addEventListener('click',()=>closeNav());scrim.addEventListener('click',()=>closeNav());
sidebar.addEventListener('keydown',e=>{if(e.key==='Escape')closeNav();if(e.key==='Tab'&&sidebar.classList.contains('is-open')){const focusable=[...sidebar.querySelectorAll('a,button')].filter(el=>el.getClientRects().length);const first=focusable[0],last=focusable.at(-1);if(e.shiftKey&&document.activeElement===first){e.preventDefault();last.focus();}else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first.focus();}}});
const help=document.querySelector('#help-dialog');document.querySelector('#help-button').addEventListener('click',()=>help.showModal());help.querySelector('[data-close-dialog]').addEventListener('click',()=>help.close());
document.querySelector('.skip-link').addEventListener('click',e=>{e.preventDefault();main.focus();});
window.addEventListener('beforeunload',e=>{if(guard&&!guard()){e.preventDefault();e.returnValue='';}});
document.addEventListener('visibilitychange',()=>{if(!document.hidden)health();});
window.addEventListener('online',health);window.addEventListener('offline',health);
router.start();health();tenants();setInterval(health,15000);
