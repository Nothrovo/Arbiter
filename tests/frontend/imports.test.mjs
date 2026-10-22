import test from 'node:test';
import assert from 'node:assert/strict';

const moduleURL = new URL('../../app/static/js/features/imports/model.js', import.meta.url);
const load = () => import(moduleURL);

test('paste submit prevents duplicate requests, keeps draft on failure, and clears only after honest server results', async () => {
  const {createImportSession} = await load();
  let calls = 0;
  let finish;
  let seen;
  const session = createImportSession({send: (path, options) => {
    calls++; seen = {path, options};
    return new Promise((resolve, reject) => {finish = {resolve, reject};});
  }});
  session.setMode('paste');
  session.setText('{"synthetic":true}');
  assert.equal(session.dirty(), true);
  const first = session.submit();
  assert.equal(session.state.pending, true);
  assert.equal(await session.submit(), false);
  assert.equal(calls, 1);
  assert.equal(seen.path, '/api/import-text');
  assert.deepEqual(JSON.parse(seen.options.body), {content: '{"synthetic":true}'});
  finish.reject(new Error('Synthetic server unavailable'));
  assert.equal(await first, false);
  assert.equal(session.state.text, '{"synthetic":true}');
  assert.equal(session.state.pending, false);
  assert.match(session.state.error, /unavailable/);
  const second = session.submit();
  finish.resolve({parsed: 8, inserted: 3, deduplicated: 5, warnings: ['Synthetic parser warning']});
  assert.equal(await second, true);
  assert.deepEqual(session.state.result, {parsed: 8, inserted: 3, deduplicated: 5, warnings: ['Synthetic parser warning']});
  assert.equal(session.dirty(), false);
  assert.equal(session.state.text, '');
});

test('file submit uses multipart and invalid server counters never clear pending input', async () => {
  const {createImportSession} = await load();
  const file = new File(['{"synthetic":1}'], 'sample.jsonl', {type: 'application/json'});
  let seen;
  const session = createImportSession({send: async (path, options) => {
    seen = {path, options}; return {inserted: 1};
  }});
  session.setFile(file);
  assert.equal(await session.submit(), false);
  assert.equal(seen.path, '/api/import');
  assert.equal(seen.options.body.get('file').name, 'sample.jsonl');
  assert.equal(seen.options.headers, undefined);
  assert.equal(session.state.file, file);
  assert.match(session.state.error, /hasil/i);
  session.reset();
  assert.equal(session.dirty(), false);
  assert.equal(await session.submit(), false);
});

test('aborted imports do not announce success or discard a draft', async () => {
  const {createImportSession} = await load();
  const abort = new AbortController();
  const session = createImportSession({signal: abort.signal, send: async () => {
    abort.abort(); return {parsed: 1, inserted: 1, deduplicated: 0, warnings: []};
  }});
  session.setMode('paste'); session.setText('{}');
  assert.equal(await session.submit(), false);
  assert.equal(session.state.text, '{}');
  assert.equal(session.state.result, null);
});

test('import page labels file and paste inputs and renders only actual counters with escaped warnings', async () => {
  const {importPage, importResult} = await import('../../app/static/js/features/imports/render.js');
  const page = importPage();
  assert.match(page, /accept="\.json,\.jsonl,\.txt"/);
  assert.match(page, /for="import-content"/);
  assert.match(page, /for="import-file"/);
  assert.match(page, /aria-live="polite"/);
  assert.doesNotMatch(page, /on(?:click|input)=/);
  const result = importResult({parsed: 19, inserted: 4, deduplicated: 15, warnings: ['<script>synthetic</script>']}, 'example');
  assert.match(result, />19</); assert.match(result, />4</); assert.match(result, />15</);
  assert.match(result, /&lt;script&gt;/);
  assert.match(result, /bukan hanya/i);
  assert.doesNotMatch(result, /<script>/);
});

test('import validation blocks blank input but keeps malformed JSON advisory for the server parser', async () => {
  const {validateText, validateFile} = await load();
  assert.equal(validateText(' \n\t').valid, false);
  assert.deepEqual(validateText('{"synthetic":true}\n{"synthetic":false}'), {valid: true, warning: ''});
  assert.equal(validateText('{broken').valid, true);
  assert.match(validateText('{broken').warning, /server/i);
  assert.equal(validateFile(null).valid, false);
  assert.equal(validateFile({name: 'events.json', size: 0}).valid, false);
  assert.equal(validateFile({name: 'events.exe', size: 10}).valid, false);
  for (const name of ['events.JSON', 'events.jsonl', 'events.txt']) {
    assert.equal(validateFile({name, size: 10}).valid, true);
  }
});
