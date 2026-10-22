import test from 'node:test';
import assert from 'node:assert/strict';
import {createCaseState} from '../../app/static/js/features/incidents/state.js';
test('tenant-scoped empty case is stopped before request with actionable policy', async()=>{
  let calls=0;
  const state=createCaseState({tenant:'Synthetic Lab',json:async()=>{calls++;throw new Error('must not send');}});
  state.edit('title','Synthetic scoped draft');
  assert.equal(await state.save(),false);
  assert.equal(calls,0);
  assert.match(state.error,/bukti|Semua tenant/);
  assert.equal(state.dirty,true);
});
