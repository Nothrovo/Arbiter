import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync, existsSync} from 'node:fs';
const root = new URL('../../', import.meta.url);
test('application loads local modular shell with four real destinations and no CDN dependency', () => {
  const html = readFileSync(new URL('app/index.html', root), 'utf8');
  assert.match(html, /src="\/static\/js\/app.js"/);
  assert.match(html, /type="module"/);
  assert.doesNotMatch(html, /fonts.googleapis|onclick=/);
  assert.match(html, /id="main-content"/);
  assert.match(html, /aria-live="polite"/);
  for (const file of ['app.js','features/triage/view.js']) assert.ok(existsSync(new URL(`app/static/js/${file}`, root)), file);
});
