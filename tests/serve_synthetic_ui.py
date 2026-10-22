"""Privacy-safe browser QA: real API, authored in-memory evidence, no live DB.

Run with .venv/bin/python -m tests.serve_synthetic_ui.
Never used by production. app.config/database are replaced before main imports;
uvicorn lifespan is disabled. UI carries a visible synthetic-data label.
"""
from pathlib import Path
import json
import sys
import types
from tests.test_ui_api import load_isolated_api, SyntheticDB, GROUP, OTHER_GROUP

api = load_isolated_api()
db = SyntheticDB()
db.connection.create_function('now', 0, lambda: '2026-01-01T12:00:00Z')
api.get_db = db.session
counter = 100

def synthetic_ingest(conn, normalized):
    global counter
    counter += 1
    db.add_alert(counter, 'Synthetic Lab', description='Synthetic imported event', rule_level=7)
    return True, False

api.ingest_alert_with_dedup = synthetic_ingest
# Replace seeded helper data with explicitly authored browser-test records.
db.connection.execute('DELETE FROM wazuh.alert_group_members')
db.connection.execute('DELETE FROM wazuh.alerts')
db.connection.execute('DELETE FROM wazuh.analysis_groups')
names = ['Synthetic repeated SSH authentication failure', 'Synthetic web endpoint probe', 'Synthetic application audit event', 'Synthetic suspicious user agent', 'Synthetic access denied at gateway', 'Synthetic vulnerability scan pattern']
for pk in range(1, 59):
    minute = str(pk % 60).zfill(2)
    db.add_alert(pk, 'Synthetic Lab' if pk <= 46 else 'Synthetic Sandbox',
        description=names[(pk - 1) % len(names)],
        timestamp=f'2026-01-01T10:{minute}:00Z',
        agent_name=f'synthetic-node-{pk % 4 + 1}', rule_id=f'{5700 + pk % 5}',
        rule_level=[5, 7, 10, 12][pk % 4], source_ip=f'192.0.2.{pk}',
        hit_count=[1, 8, 32, 124][pk % 4], is_reviewed=pk % 5 == 0,
        mitre_ids=json.dumps(['T1110'] if pk % 2 else ['T1595']),
        duplicate_instances=json.dumps([{'timestamp': '2026-01-01T10:01:00Z', 'id': f'synthetic-occurrence-{pk}', 'full_log': 'Synthetic evidence only — no production telemetry'}]),
        raw=json.dumps({'full_log': 'Synthetic QA evidence only. No real infrastructure.', 'synthetic': True}),
    )
for number, title, sev, status in [(1, 'Synthetic credential attack investigation', 'high', 'open'), (2, 'Synthetic gateway reconnaissance review', 'medium', 'in_progress')]:
    gid = GROUP if number == 1 else OTHER_GROUP
    db.connection.execute('INSERT INTO wazuh.analysis_groups VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
        (gid, title, 'Authentication' if number == 1 else 'Web activity', 'Synthetic investigation narrative for browser QA.', 'Synthetic conclusion pending review.', 'Synthetic recommendation, not an operational instruction.', status, sev, 'human', '2026-01-01', '2026-01-01'))
    db.connection.executemany('INSERT INTO wazuh.alert_group_members VALUES (?, ?)', [(pk, gid) for pk in range(1 if number == 1 else 8, 8 if number == 1 else 13)])

@api.app.middleware('http')
async def synthetic_boundary(request, call_next):
    response = await call_next(request)
    if request.url.path == '/' and response.status_code == 200:
        content = b''.join([chunk async for chunk in response.body_iterator]).decode()
        content = content.replace('<body>', '<body><div class="fixture-notice" role="note">SYNTHETIC QA · Authored test evidence only · No production database connection</div>')
        from fastapi.responses import HTMLResponse
        response = HTMLResponse(content)
    response.headers['X-Arbiter-Data'] = 'synthetic-only'
    return response

if __name__ == '__main__':
    import uvicorn
    print('SYNTHETIC QA ONLY: binding 127.0.0.1:8767; no production DB/config')
    uvicorn.run(api.app, host='127.0.0.1', port=8767, lifespan='off', access_log=False, log_level='warning')
