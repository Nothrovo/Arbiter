import test from 'node:test';
import assert from 'node:assert/strict';

test('stats session manages monotonic versions and ignores stale responses', async () => {
  const {createStatsSession} = await import('../../app/static/js/state/stats.js');
  const session = createStatsSession();
  const v1 = session.nextRequest();
  const v2 = session.nextRequest();
  assert.equal(session.isCurrent(v1), false);
  assert.equal(session.isCurrent(v2), true);
  session.dispose();
  assert.equal(session.isCurrent(v2), false);
});

test('normalizeStatsQuery validates defaults, bounds, and preserves multi-tenant scope', async () => {
  const {normalizeStatsQuery, distributionPercentages, triageRouteFromStats} = await import('../../app/static/js/features/stats/model.js');
  
  const params = new URLSearchParams('tenant=Alpha&tenant=Beta&pivot_by=severity&secondary_pivot=url_path&facet=rule_description&facet_value=Web+400&secondary_facet=url_path&secondary_facet_value=%2F.env&metric=events&chart=donut&top_n=100&q=test');
  const query = normalizeStatsQuery(params);
  assert.equal(query.pivot_by, 'severity');
  assert.equal(query.secondary_pivot, 'url_path');
  assert.equal(query.facet, 'rule_description');
  assert.equal(query.facet_value, 'Web 400');
  assert.equal(query.secondary_facet, 'url_path');
  assert.equal(query.secondary_facet_value, '/.env');
  assert.equal(query.metric, 'events');
  assert.equal(query.chart, 'donut');
  assert.equal(query.top_n, 100);
  assert.deepEqual(query.tenants, ['Alpha', 'Beta']);
  assert.equal(query.q, 'test');

  // Distribution percentages absorb rounding remainder to sum to exactly 100.0%
  const rows = [
    {key: 'A', count: 1, percentage: 33.33},
    {key: 'B', count: 1, percentage: 33.33},
    {key: 'C', count: 1, percentage: 33.33},
  ];
  const adjusted = distributionPercentages(rows, 0, 3);
  const sum = adjusted.reduce((acc, r) => acc + r.displayPercentage, 0);
  assert.equal(Math.round(sum * 10) / 10, 100.0);

  // Triage route carries exact multi-tenant scope and active filters
  const triageHref = triageRouteFromStats(query);
  assert.match(triageHref, /#\/triage\?/);
  assert.match(triageHref, /tenant=Alpha/);
  assert.match(triageHref, /tenant=Beta/);
  assert.match(triageHref, /q=test/);
});

test('stats export formatters generate clean CSV and markdown analysis summary', async () => {
  const {generateStatsCSV, generateMarkdownSummary} = await import('../../app/static/js/features/stats/model.js');
  
  const statsData = {
    pivot_by: 'rule_description',
    metric: 'alerts',
    total: 100,
    items: [
      {key: 'SQL Injection', count: 60, displayPercentage: 60.0},
      {key: 'Brute Force', count: 30, displayPercentage: 30.0},
    ],
    other_count: 10,
    other_percentage: 10.0,
    scope: {tenant: ['Alpha'], q: ''},
  };

  const csv = generateStatsCSV(statsData);
  assert.match(csv, /Kategori,Jumlah,Persen/);
  assert.match(csv, /"SQL Injection",60,60/);
  assert.match(csv, /"Lainnya",10,10/);

  const md = generateMarkdownSummary(statsData);
  assert.match(md, /### Ringkasan Statistik Alert/);
  assert.match(md, /SQL Injection: 60 \(60%\)/);
  assert.match(md, /Total: 100 alert/);
});

test('isMaliciousPath identifies high-signal sensitive and probe paths', async () => {
  const {isMaliciousPath} = await import('../../app/static/js/features/stats/model.js');
  
  // Malicious / sensitive paths
  assert.equal(isMaliciousPath('/.env'), true);
  assert.equal(isMaliciousPath('/.env.bak'), true);
  assert.equal(isMaliciousPath('/.git/config'), true);
  assert.equal(isMaliciousPath('/.ssh/id_rsa'), true);
  assert.equal(isMaliciousPath('/xmlrpc.php'), true);
  assert.equal(isMaliciousPath('/wp-config.php.save'), true);
  assert.equal(isMaliciousPath('/config.php.bak'), true);
  assert.equal(isMaliciousPath('/administrator/index.php'), true);
  assert.equal(isMaliciousPath('/admin/login'), true);
  assert.equal(isMaliciousPath('/.aws/credentials.bak'), true);
  assert.equal(isMaliciousPath('/dump.sql'), true);
  assert.equal(isMaliciousPath('/c99shell.php'), true);

  // Benign / normal paths
  assert.equal(isMaliciousPath('/plugins/generic/pdfJsViewer/locale/locale.properties'), false);
  assert.equal(isMaliciousPath('/index.html'), false);
  assert.equal(isMaliciousPath('/static/css/style.css'), false);
  assert.equal(isMaliciousPath('/assets/logo.png'), false);
  assert.equal(isMaliciousPath(''), false);
});

test('Benign Spotter filters out malicious paths and selects only benign items', async () => {
  const {isMaliciousPath} = await import('../../app/static/js/features/stats/model.js');
  
  const sampleBreakdown = [
    {key: '/.env', count: 12},
    {key: '/.git/config', count: 10},
    {key: '/plugins/generic/pdfJsViewer/locale/locale.properties', count: 55},
    {key: '/index.html', count: 20},
    {key: '/xmlrpc.php', count: 8},
  ];

  const malicious = sampleBreakdown.filter(it => isMaliciousPath(it.key));
  assert.deepEqual(malicious.map(it => it.key), ['/.env', '/.git/config', '/xmlrpc.php']);

  const benign = sampleBreakdown.filter(it => !isMaliciousPath(it.key));
  assert.deepEqual(benign.map(it => it.key), [
    '/plugins/generic/pdfJsViewer/locale/locale.properties',
    '/index.html',
  ]);
  assert.equal(benign.reduce((acc, it) => acc + it.count, 0), 75);
});

test('isMaliciousPath detects real-world exploit probe paths from telemetry (JBoss, GPON, ColdFusion, Cobbler, wp-json, Bower, IPFS)', async () => {
  const {isMaliciousPath} = await import('../../app/static/js/features/stats/model.js');

  // Real-world telemetry probes that must never leak into benign:
  assert.equal(isMaliciousPath('/jmx-console/HtmlAdaptor'), true);
  assert.equal(isMaliciousPath('/web-console/ServerInfo.jsp'), true);
  assert.equal(isMaliciousPath('/jboss/status'), true);
  assert.equal(isMaliciousPath('/cobbler_api'), true);
  assert.equal(isMaliciousPath('/GponForm/diag_Form?images/'), true);
  assert.equal(isMaliciousPath('/boaform/admin/formLogin'), true);
  assert.equal(isMaliciousPath('/rom-0'), true);
  assert.equal(isMaliciousPath('/router/config.bin'), true);
  assert.equal(isMaliciousPath('/CFIDE/scripts/ajax/FCKeditor/editor/filemanager/connectors/cfm/upload.cfm'), true);
  assert.equal(isMaliciousPath('/userfiles/uploadedFiles/payload.jsp'), true);
  assert.equal(isMaliciousPath('/wp-json/batch/v1'), true);
  assert.equal(isMaliciousPath('/wp-json/wp/v2/users'), true);
  assert.equal(isMaliciousPath('/bower.json'), true);
  assert.equal(isMaliciousPath('/vendor/jquery-file-upload/server/php/'), true);
  assert.equal(isMaliciousPath('/ipfs/QmXoypizjW3WknFiJnKLwHCnL72vedxjQkDDP1mXWo6uco'), true);
  assert.equal(isMaliciousPath('/phpmyadmin/scripts/setup.php'), true);
  assert.equal(isMaliciousPath('/actuator/env'), true);
  assert.equal(isMaliciousPath('/solr/admin/info/system'), true);

  // Argon telemetry report vectors (CVEs, Cloud/CI-CD harvesting, double-ext):
  assert.equal(isMaliciousPath('/esp/cms_changeDeviceContext.esp?device=aaaaa:a%27";user|s."1337";'), true);
  assert.equal(isMaliciousPath('/avi/avigui/avigwt'), true);
  assert.equal(isMaliciousPath('/data/cache_template/rss.tpl.php'), true);
  assert.equal(isMaliciousPath('/service-account.json'), true);
  assert.equal(isMaliciousPath('/gcp-key.json'), true);
  assert.equal(isMaliciousPath('/gcp-sa.json'), true);
  assert.equal(isMaliciousPath('/aws.json'), true);
  assert.equal(isMaliciousPath('/.npmrc'), true);
  assert.equal(isMaliciousPath('/.boto'), true);
  assert.equal(isMaliciousPath('/firebase-adminsdk.json'), true);
  assert.equal(isMaliciousPath('/firebase.json'), true);
  assert.equal(isMaliciousPath('/env.json'), true);
  assert.equal(isMaliciousPath('/application.yml'), true);
  assert.equal(isMaliciousPath('/.netrc'), true);
  assert.equal(isMaliciousPath('/.composer/auth.json'), true);
  assert.equal(isMaliciousPath('/docker-compose.yml'), true);
  assert.equal(isMaliciousPath('/.gitlab-ci.yml'), true);
  assert.equal(isMaliciousPath('/.github/workflows/deploy.yml'), true);
  assert.equal(isMaliciousPath('/client.key'), true);
  assert.equal(isMaliciousPath('/.htpasswd'), true);
  assert.equal(isMaliciousPath('/.env1'), true);
  assert.equal(isMaliciousPath('/.env2'), true);
  assert.equal(isMaliciousPath('/_environment'), true);
  assert.equal(isMaliciousPath('/info.php'), true);
  assert.equal(isMaliciousPath('/debug.php'), true);
  assert.equal(isMaliciousPath('/appsettings.json'), true);
  assert.equal(isMaliciousPath('/configuration.php'), true);
  assert.equal(isMaliciousPath('/application-dev.yml'), true);
  assert.equal(isMaliciousPath('/application-prod.yml'), true);
  assert.equal(isMaliciousPath('/application.properties'), true);
  assert.equal(isMaliciousPath('/icons/test.php'), true);
  assert.equal(isMaliciousPath('/icons/info.php'), true);
  assert.equal(isMaliciousPath('/icons/?phpinfo=-1'), true);
  assert.equal(isMaliciousPath('/icons/settings.json'), true);
  assert.equal(isMaliciousPath('/db/websql/index.php'), true);
  assert.equal(isMaliciousPath('/database/index.php'), true);
  assert.equal(isMaliciousPath('/db/webdb/index.php'), true);
  assert.equal(isMaliciousPath('/include/function.js.php'), true);
  assert.equal(isMaliciousPath('/geoserver/web/'), true);
  assert.equal(isMaliciousPath('/?rest_route=/batch/v1'), true);

  // Benign legitimate OJS application paths MUST remain false:
  assert.equal(isMaliciousPath('/index.php/sebatik/article/view/123/456'), false);
  assert.equal(isMaliciousPath('/index.php/sebatik/issue/view/10'), false);
  assert.equal(isMaliciousPath('/plugins/generic/pdfJsViewer/pdf.js/web/locale/locale.properties'), false);
  assert.equal(isMaliciousPath('/index.html'), false);
  assert.equal(isMaliciousPath('/favicon.ico'), false);
});
