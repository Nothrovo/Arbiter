import test from 'node:test';
import assert from 'node:assert/strict';
import {existsSync} from 'node:fs';
const url=new URL('../../app/static/js/state/workspace.js',import.meta.url);
test('connection probe checks initial background tab and reports a verified offline state',async()=>{
  assert.ok(existsSync(url),'workspace connection state must exist');
  const {probeConnection}=await import(url);
  const online=await probeConnection(async()=>({status:'ok'}),null);
  assert.equal(online.state,'online');
  assert.ok(online.lastSuccess);
  const offline=await probeConnection(async()=>{throw new Error('synthetic offline');},online.lastSuccess);
  assert.equal(offline.state,'offline');
  assert.equal(offline.lastSuccess,online.lastSuccess);
  assert.match(offline.label,/Tidak terhubung/);
});
