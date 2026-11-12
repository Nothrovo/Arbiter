import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';

const root = new URL('../../', import.meta.url);
const settingsView = readFileSync(new URL('app/static/js/features/settings/view.js', root), 'utf8');
const triageView = readFileSync(new URL('app/static/js/features/triage/view.js', root), 'utf8');
const mainPy = readFileSync(new URL('app/main.py', root), 'utf8');

test('settings Intel panel exposes a read-only Neuropetra cache probe', () => {
  assert.match(settingsView, /data-action="test-intel-cache"/);
  assert.match(settingsView, /id="intel-cache-ip"/);
  assert.match(settingsView, /id="intel-cache-status"/);
  assert.match(settingsView, /\/api\/intel\/cache\/test/);
  assert.match(settingsView, /Tes cache Neuropetra/);
  assert.match(settingsView, /tidak memanggil AbuseIPDB/);
  assert.match(settingsView, /tetap <strong>read-only<\/strong>/);
  assert.match(settingsView, /127\.0\.0\.1:5433/);
  assert.match(settingsView, /#\/database/);
  assert.match(settingsView, /renderIntelStatus\(`Ditemukan di \$\{result\.source_table/);
});

test('intel cache probe endpoint is registered and validates the IP', () => {
  assert.match(mainPy, /@app\.post\("\/api\/intel\/cache\/test"\)/);
  assert.match(mainPy, /def api_intel_cache_test/);
  assert.match(mainPy, /lookup_remote_ip_cache_detail/);
  assert.match(mainPy, /Masukkan alamat IPv4\/IPv6 yang valid/);
});

test('triage Live Enrich surfaces real errors instead of a fake zero score', () => {
  assert.doesNotMatch(triageView, /abuse_score\s*\?\?\s*0/);
  assert.match(triageView, /item\.status==='error'/);
  assert.match(triageView, /item\.abuse_score===null\|\|item\.abuse_score===undefined/);
  assert.match(triageView, /Skor Abuse \$\{Number\(item\.abuse_score\)\}%/);
  assert.match(triageView, /cache \$\{item\.cache_source\}/);
  assert.match(triageView, /failed\.length/);
});
