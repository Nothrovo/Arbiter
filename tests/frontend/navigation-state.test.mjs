import test from 'node:test';
import assert from 'node:assert/strict';
import {existsSync} from 'node:fs';
const url=new URL('../../app/static/js/state/navigation.js',import.meta.url);
test('returning to triage restores its working query but does not reopen inspector or leak cross-tenant state',async()=>{
 assert.ok(existsSync(url),'navigation memory must exist');
 const {createNavigationMemory}=await import(url);
 const memory=createNavigationMemory();
 memory.remember({page:'triage',path:'/triage',params:new URLSearchParams('tenant=Lab&q=probe&review_status=all&offset=50&alert=8')});
 const destination=memory.destination('triage','Lab');
 assert.match(destination,/q=probe/);assert.match(destination,/offset=50/);assert.doesNotMatch(destination,/alert=/);
 assert.equal(memory.destination('triage','Other'),'#/triage?tenant=Other');
 assert.equal(memory.destination('imports','Lab'),'#/imports?tenant=Lab');
});

test('navigation memory keys and restores an exact canonical tenant set',async()=>{
 const {createNavigationMemory}=await import(url);
 const memory=createNavigationMemory();
 memory.remember({page:'triage',path:'/triage',params:new URLSearchParams('tenant=Beta&tenant=Alpha&q=probe&alert=8')});
 const destination=memory.destination('triage',new URLSearchParams('tenant=Alpha&tenant=Beta'));
 assert.equal(destination,'#/triage?tenant=Alpha&tenant=Beta&q=probe');
 assert.equal(memory.destination('triage',new URLSearchParams('tenant=Alpha')),'#/triage?tenant=Alpha');
});

test('navigation memory does not share state between delimiter-colliding tenant sets',async()=>{
 const {createNavigationMemory}=await import(url);
 const memory=createNavigationMemory();
 memory.remember({page:'triage',path:'/triage',params:new URLSearchParams('tenant=A%7CB&tenant=C&q=first-set')});
 assert.equal(memory.destination('triage',new URLSearchParams('tenant=A&tenant=B%7CC')),'#/triage?tenant=A&tenant=B%7CC');
});
