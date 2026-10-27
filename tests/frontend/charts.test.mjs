import test from 'node:test';
import assert from 'node:assert/strict';

test('charts helper renders accessible SVG bar, donut, and line charts with title, desc, and labels', async () => {
  const {renderBarChart, renderDonutChart, renderLineChart} = await import('../../app/static/js/ui/charts.js');
  
  const items = [
    {key: 'Rule 1001', count: 10, displayPercentage: 50.0},
    {key: 'Rule 2002', count: 6, displayPercentage: 30.0},
  ];
  const barSvg = renderBarChart({items, otherCount: 4, otherPercentage: 20.0, total: 20, metric: 'alerts'});
  assert.match(barSvg, /<svg/);
  assert.match(barSvg, /role="img"/);
  assert.match(barSvg, /<title>/);
  assert.match(barSvg, /<desc>/);
  assert.match(barSvg, /data-chart-key="Rule 1001"/);
  assert.match(barSvg, /10 alert/);
  assert.match(barSvg, /50%/);

  const donutSvg = renderDonutChart({items, otherCount: 4, otherPercentage: 20.0, total: 20, metric: 'alerts'});
  assert.match(donutSvg, /<svg/);
  assert.match(donutSvg, /role="img"/);
  assert.match(donutSvg, /class="donut-slice"/);
  assert.match(donutSvg, /data-chart-key="Rule 1001"/);

  const timeSeries = [
    {bucket: '2026-01-01T10:00:00Z', total: 10, series: {'Rule 1001': 8, 'Lainnya': 2}},
    {bucket: '2026-01-01T11:00:00Z', total: 10, series: {'Rule 1001': 2, 'Lainnya': 8}},
  ];
  const lineSvg = renderLineChart({timeSeries, topKeys: ['Rule 1001'], metric: 'alerts'});
  assert.match(lineSvg, /<svg/);
  assert.match(lineSvg, /class="line-series"/);
  assert.match(lineSvg, /class="line-point"/);
});
