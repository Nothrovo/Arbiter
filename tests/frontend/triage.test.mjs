import test from 'node:test';
import assert from 'node:assert/strict';
import {existsSync} from 'node:fs';
const url = new URL('../../app/static/js/features/triage/model.js', import.meta.url);
test('triage list keeps unknown intel distinct from zero detections and renders selected state safely', async () => {
  assert.ok(existsSync(url), 'triage view model exists');
  const {intelSummary, renderQueue} = await import(url);
  assert.match(intelSummary({source_ip:'192.0.2.10',abuse_score:null}), /Belum ada cache/);
  assert.match(intelSummary({source_ip:'192.0.2.10',abuse_score:0,vt_malicious:0}), /Tidak ada deteksi/);
  assert.doesNotMatch(intelSummary({abuse_score:0}), /Clean|Aman/);
  const row={id:1, description:'<script>synthetic</script>', tenant:'lab', agent_name:'Synthetic host', rule_level:10,hit_count:8};
  const html=renderQueue([row],{selectedIds:[1],activeId:1,query:{tenant:'all',sort_by:'timestamp',sort:'desc'}});
  assert.match(html,/&lt;script&gt;/);
  assert.doesNotMatch(html,/<script>/);
  assert.match(html,/aria-selected="true"/);
  assert.match(html,/aria-sort="descending"/);
  assert.match(html,/Pilih alert/);
});
