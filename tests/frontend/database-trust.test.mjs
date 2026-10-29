import test from 'node:test';
import assert from 'node:assert/strict';
import {mount} from '../../app/static/js/features/database/view.js';

const status = {active_profile: {id:'local',mode:'read_write'}, profiles:[{id:'remote', masked_url:'postgresql://user:***@synthetic.invalid/db'}],tenants:[{tenant:'Alpha',count:2}],stats:{}};
async function harness(handler = () => status, extra = {}) {
  const listeners = {}, elements = new Map(), notices = [], calls = [];
  let html = '';
  const root = {
    get innerHTML(){return html;},
    set innerHTML(value){html=value; elements.clear(); for(const match of value.matchAll(/<(input|select|button|div)\b([^>]*\bid="([^"]+)"[^>]*)>/g)){
      const [,tag,attrs,id]=match;
      const body=html.slice(match.index+match[0].length).split('</'+tag+'>')[0];
      let value=attrs.match(/\bvalue="([^"]*)"/)?.[1]||'';
      if(tag==='select') value=body.match(/<option value="([^"]*)" selected/)?.[1]??body.match(/<option value="([^"]*)"/)?.[1]??'';
      elements.set('#'+id,{value,checked:false,style:{},textContent:'',innerHTML:'',addEventListener(){}});
    }},
    querySelector(selector){return elements.get(selector)||null;},
    addEventListener(type,fn){listeners[type]=fn;},
  };
  globalThis.fetch=async (url,options={})=>{const body=options.body?JSON.parse(options.body):null;calls.push({url,body});const result=await handler(url,body);return {ok:true,json:async()=>result};};
  globalThis.confirm=()=>true;
  let guard;
  await mount({root,route:{params:new URLSearchParams('tenant=Alpha')},signal:new AbortController().signal,notify:(...args)=>notices.push(args),setGuard:fn=>guard=fn,...extra});
  return {root,calls,notices,elements,guard:()=>guard,async click(action,profile='remote'){const btn={dataset:{action,profile},disabled:false,textContent:''};await listeners.click({target:{closest:()=>btn}});},change(id,value){const target=elements.get(id);target.value=value;listeners.input?.({target});listeners.change?.({target});}};
}

test('failed refresh never announces success',async()=>{
  let fail=false;
  const h=await harness(()=>{if(fail)throw Error('synthetic offline');return status;});
  fail=true;await h.click('refresh-status');
  assert.equal(h.notices.some(([text])=>text==='Status database diperbarui.'),false);
  assert.equal(h.notices.some(([,kind])=>kind==='error'),true);
});

test('URI draft survives profile test and blocks switch when discard declined',async()=>{
  const h=await harness(url=>url.endsWith('/test')?{ok:true}:status);
  h.change('#remote-url-input','postgresql://synthetic:new@synthetic.invalid/db');
  assert.equal(typeof h.guard(),'function');
  assert.equal(h.guard()(),false);
  await h.click('test-profile');
  assert.equal(h.elements.get('#remote-url-input').value,'postgresql://synthetic:new@synthetic.invalid/db');
  globalThis.confirm=()=>false;
  await h.click('switch-profile');
  assert.equal(h.calls.some(x=>x.url.endsWith('/switch')),false);
});

test('masked display URI is not prefilled or submitted as replacement',async()=>{
  const h=await harness();
  assert.match(h.root.innerHTML,/id="remote-url-input"[^>]*value=""/);
  await h.click('save-remote-url');
  assert.equal(h.calls.filter(x=>x.url.endsWith('/config')).length,0);
});
