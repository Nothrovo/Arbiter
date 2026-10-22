import test from 'node:test';
import assert from 'node:assert/strict';
import {existsSync} from 'node:fs';
const url=new URL('../../app/static/js/state/triage.js',import.meta.url);
test('triage session keeps queue scroll and restores stale-response-safe detail identity',async()=>{
  assert.ok(existsSync(url),'triage session state must exist');
  const {createTriageSession}=await import(url);
  const session=createTriageSession();
  session.rememberQueue(820);
  session.open(7);
  assert.equal(session.activeId(),7);
  assert.equal(session.close(),820);
  const old=session.nextDetail();const next=session.nextDetail();
  assert.equal(session.isCurrentDetail(old),false);
  assert.equal(session.isCurrentDetail(next),true);
  session.dispose();assert.equal(session.isCurrentDetail(next),false);
});
