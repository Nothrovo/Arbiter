import test from 'node:test';
import assert from 'node:assert/strict';
import {mount} from '../../app/static/js/features/triage/view.js';
import {createSelection} from '../../app/static/js/state/selection.js';

class Element extends EventTarget {
  constructor(){super();this.classList={add(){},remove(){},toggle(){}};this.value='';this.innerHTML='';this.textContent='';this.dataset={};this.hidden=false;this.closed=false;}
  setAttribute(){} removeAttribute(){} hasAttribute(){return false;} matches(){return false;} closest(){return null;} close(){this.closed=true;} showModal(){this.closed=false;}
  querySelector(){return new Element();}
}
async function requestsFor(search){
  const controls=new Map(), root=new Element(), requests=[];
  root.querySelector=s=>{if(!controls.has(s))controls.set(s,new Element());return controls.get(s);};
  root.querySelectorAll=()=>[];
  const controller=new AbortController(), original=globalThis.fetch;
  globalThis.fetch=async url=>{
    requests.push(new URL(url,'http://synthetic.invalid'));
    return new Response(JSON.stringify(String(url).includes('/summary')?{alerts:0,events:0,unique_source_ips:0,unique_agents:0,incident_cases:0}:{items:[],total:0}));
  };
  let dispose;
  try {
    dispose=mount({root,route:{params:new URLSearchParams(search)},signal:controller.signal,selection:createSelection('all'),navigate(){},notify(){}});
    await new Promise(resolve=>setTimeout(resolve,10));
    return requests;
  } finally {controller.abort();dispose?.();globalThis.fetch=original;}
}

test('default Triage sends the same explicit unreviewed scope to list and summary',async()=>{
  const requests=await requestsFor('');
  for(const path of ['/api/alerts','/api/triage/summary']){
    const params=requests.find(url=>url.pathname===path).searchParams;
    assert.equal(params.get('review_status'),'unreviewed',path);
  }
  const list=requests.find(url=>url.pathname==='/api/alerts').searchParams;
  assert.equal(list.get('limit'),'50');
  assert.equal(list.get('offset'),'0');
});

test('explicit review scope and repeated tenants survive queue and summary requests',async()=>{
  for(const review of ['all','reviewed','unreviewed']){
    const requests=await requestsFor(`tenant=Alpha&tenant=Beta&review_status=${review}&facet=rule_id&facet_value=5703&secondary_facet=agent&secondary_facet_value=node&limit=25&offset=25`);
    const queueAndSummary=requests.filter(url=>url.pathname==='/api/alerts'||url.pathname==='/api/triage/summary');
    assert.equal(queueAndSummary.length,2);
    for(const url of queueAndSummary){
      assert.deepEqual(url.searchParams.getAll('tenant'),['Alpha','Beta']);
      assert.equal(url.searchParams.get('facet'),'rule_id');
      assert.equal(url.searchParams.get('facet_value'),'5703');
      assert.equal(url.searchParams.get('secondary_facet'),'agent');
      assert.equal(url.searchParams.get('secondary_facet_value'),'node');
      assert.equal(url.searchParams.get('review_status'),review);
    }
  }
});

test('valid filters forward to queue and summary while malformed filters are stripped',async()=>{
  const validFilter=JSON.stringify([{field:'full_log',op:'is_not',value:'*/lib/minigalnano/createthumb.php?*'}]);
  const requests=await requestsFor(`tenant=Alpha&filters=${encodeURIComponent(validFilter)}`);
  for(const path of ['/api/alerts','/api/triage/summary']){
    const raw=requests.find(url=>url.pathname===path).searchParams.get('filters');
    assert.deepEqual(JSON.parse(raw),[{field:'full_log',op:'not_glob',value:'*/lib/minigalnano/createthumb.php?*',value2:''}]);
  }
  const badRequests=await requestsFor('tenant=Alpha&filters=not-valid-json');
  assert.equal(badRequests.find(url=>url.pathname==='/api/alerts').searchParams.get('filters'),null);
});

test('submitting triage filter form auto-commits typed draft filter and keeps invalid draft open',async()=>{
  const controls=new Map(), root=new Element(), navigated=[];
  root.querySelector=s=>{if(!controls.has(s))controls.set(s,new Element());return controls.get(s);};
  root.querySelectorAll=()=>[];
  const controller=new AbortController();
  const originalFetch=globalThis.fetch, originalFormData=globalThis.FormData;
  globalThis.fetch=async url=>new Response(JSON.stringify(String(url).includes('/summary')?{alerts:0,events:0,unique_source_ips:0,unique_agents:0,incident_cases:0}:{items:[],total:0}));
  globalThis.FormData=class {
    constructor(){this._m=new Map([['filter_preset',''],['status','all'],['time_preset',''],['time_from',''],['time_to',''],['ordering','timestamp:desc']]);}
    get(k){return this._m.has(k)?this._m.get(k):null;}
  };
  let dispose;
  try {
    dispose=mount({
      root,
      route:{params:new URLSearchParams('tenant=Alpha&review_status=all')},
      signal:controller.signal,
      selection:createSelection('all'),
      navigate(url){navigated.push(url);},
      notify(){},
    });
    const dialog=root.querySelector('#triage-filter-dialog');
    const field=root.querySelector('[data-filter-builder="triage-flt"] [data-filter-field]');
    const op=root.querySelector('[data-filter-builder="triage-flt"] [data-filter-op]');
    const val=root.querySelector('[data-filter-builder="triage-flt"] [data-filter-value]');
    const val2=root.querySelector('[data-filter-builder="triage-flt"] [data-filter-value2]');
    const form=root.querySelector('#triage-filter-form');
    const status=root.querySelector('#triage-filter-status');

    // Invalid draft (missing value2 for range) stays open and surfaces inline error
    dialog.closed=false;
    field.value='rule.level'; op.value='range'; val.value='7'; val2.value='';
    form.dispatchEvent(new Event('submit',{cancelable:true}));
    assert.equal(dialog.closed,false);
    assert.equal(navigated.length,0);
    assert.match(status.textContent,/belum valid/i);

    // Valid typed draft auto-commits on submit without clicking + Tambah filter
    field.value='full_log'; op.value='is_not'; val.value='*/lib/minigalnano/createthumb.php?*'; val2.value='';
    form.dispatchEvent(new Event('submit',{cancelable:true}));
    assert.equal(dialog.closed,true);
    assert.equal(navigated.length,1);
    const targetParams=new URLSearchParams(navigated[0].split('?')[1]);
    assert.deepEqual(JSON.parse(targetParams.get('filters')),[
      {field:'full_log',op:'not_glob',value:'*/lib/minigalnano/createthumb.php?*',value2:''},
    ]);
  } finally {
    controller.abort(); dispose?.();
    globalThis.fetch=originalFetch; globalThis.FormData=originalFormData;
  }
});

test('triage clears selection after flag, review, queue pruning, and navigation/tab changes',async()=>{
  const controls=new Map(), root=new Element(), navigated=[], calls=[];
  root.querySelector=s=>{if(!controls.has(s))controls.set(s,new Element());return controls.get(s);};
  root.querySelectorAll=()=>[];
  let queueItems=[
    {id:10,alert_id:'a-10',description:'A',hit_count:1},
    {id:11,alert_id:'a-11',description:'B',hit_count:1},
  ];
  const controller=new AbortController(), originalFetch=globalThis.fetch;
  globalThis.fetch=async(url,opts={})=>{
    const parsed=new URL(url,'http://synthetic.invalid');
    calls.push({path:parsed.pathname,method:opts.method||'GET'});
    if(parsed.pathname==='/api/triage/summary')return new Response(JSON.stringify({alerts:queueItems.length,events:queueItems.length,unique_source_ips:0,unique_agents:0,incident_cases:0}));
    if(parsed.pathname==='/api/alerts')return new Response(JSON.stringify({items:queueItems,total:queueItems.length}));
    return new Response(JSON.stringify({status:'ok',count:2}));
  };
  const selection=createSelection('all');
  const flush=()=>new Promise(resolve=>setTimeout(resolve,15));
  const clickAction=(dataset)=>{
    const btn=new Element();
    btn.dataset=dataset;
    btn.closest=sel=>sel==='button'?btn:null;
    btn.matches=()=>false;
    const ev=new Event('click');
    Object.defineProperty(ev,'target',{value:btn});
    root.dispatchEvent(ev);
  };
  let dispose;
  try{
    dispose=mount({
      root,
      route:{params:new URLSearchParams('tenant=Alpha&review_status=unreviewed')},
      signal:controller.signal,
      selection,
      navigate(url){navigated.push(url);},
      notify(){},
    });
    await flush();

    // 1. batch-flag removes processed alerts from selection
    selection.toggle(10,true);
    selection.toggle(11,true);
    clickAction({action:'batch-flag',flagColor:'green'});
    await flush();
    assert.ok(calls.some(c=>c.path==='/api/alerts/flag'&&c.method==='POST'));
    assert.equal(selection.size(),0);

    // 2. batch-review removes processed alerts from selection
    selection.toggle(10,true);
    selection.toggle(11,true);
    clickAction({action:'batch-review'});
    await flush();
    assert.ok(calls.some(c=>c.path==='/api/alerts/batch-review'&&c.method==='POST'));
    assert.equal(selection.size(),0);

    // 3. load() prunes IDs that are no longer in the visible queue
    queueItems=[{id:10,alert_id:'a-10',description:'A',hit_count:1}];
    selection.toggle(10,true);
    selection.toggle(999,true);
    root.dispatchEvent(new Event('arbiter:refresh'));
    await flush();
    assert.deepEqual(selection.ids(),[10]);

    // 4. switching review tab clears selection immediately
    clickAction({review:'reviewed'});
    assert.equal(selection.size(),0);
    assert.ok(navigated.some(u=>u.includes('review_status=reviewed')));

    // 5. leaving Triage (dispose) clears remaining selection
    selection.toggle(10,true);
    dispose();
    assert.equal(selection.size(),0);
  }finally{
    controller.abort();
    globalThis.fetch=originalFetch;
  }
});
