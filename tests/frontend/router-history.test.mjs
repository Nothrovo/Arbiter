import test from 'node:test';
import assert from 'node:assert/strict';
import {createRouter} from '../../app/static/js/router.js';

test('inspector replaceState does not reset query URL when the next navigation is cancelled', () => {
  const events = new Map(); const renders = [];
  globalThis.location = {hash:'#/triage?tenant=lab'};
  globalThis.history = {replaceState(_a,_b,hash){location.hash=hash;}};
  globalThis.window = {addEventListener(name,fn){events.set(name,fn);},removeEventListener(){}};
  let allowed=true;
  const router=createRouter(route=>renders.push(route),()=>allowed);
  router.start();
  history.replaceState(null,'','#/triage?tenant=lab&alert=12');
  events.get('arbiter:route-replaced')?.();
  allowed=false;
  location.hash='#/imports?tenant=lab';
  events.get('hashchange')();
  assert.equal(location.hash,'#/triage?tenant=lab&alert=12');
  events.get('hashchange')();
  allowed=false;
  router.navigate('/imports?tenant=lab',{replace:true});
  assert.equal(location.hash,'#/triage?tenant=lab&alert=12');
  allowed=true;
  router.navigate('/reports?tenant=lab',{replace:true});
  assert.equal(renders.at(-1).path,'/reports');
  router.dispose();
  delete globalThis.location;delete globalThis.history;delete globalThis.window;
});
