"""Synthetic-only summary/list scope contracts; no configuration or live DB."""
import json
import unittest
from urllib.parse import urlencode
from unittest.mock import patch
from fastapi.testclient import TestClient
from tests.test_ui_api import load_isolated_api, SyntheticDB


class TriageScopeTests(unittest.TestCase):
    def test_secondary_facet_and_review_status_match_summary_and_list(self):
        api = load_isolated_api()
        db = SyntheticDB()
        db.add_alert(4, 'Alpha', agent_name='other-host')
        try:
            with patch.object(api, 'get_db', db.session):
                client = TestClient(api.app)
                try:
                    for review, expected in [('unreviewed', 2), ('reviewed', 1), ('all', 3)]:
                        params = [('tenant', 'Alpha'), ('tenant', 'Beta'), ('review_status', review),
                                  ('facet', 'rule_id'), ('facet_value', 'synthetic-rule'),
                                  ('secondary_facet', 'agent'), ('secondary_facet_value', 'synthetic-host')]
                        listed = client.get('/api/alerts', params=urlencode(params))
                        summary = client.get('/api/triage/summary', params=urlencode(params))
                        self.assertEqual(listed.status_code, 200)
                        self.assertEqual(summary.status_code, 200)
                        self.assertEqual(listed.json()['total'], expected)
                        self.assertEqual(summary.json()['alerts'], expected)
                        self.assertNotIn(4, [row['id'] for row in listed.json()['items']])
                finally:
                    client.close()
        finally:
            db.connection.close()

    def test_full_log_is_not_wildcard_filters_default_and_explicit_alert_ids_triage(self):
        api = load_isolated_api()
        db = SyntheticDB()
        createthumb_log = (
            '192.0.2.50 - - [19/Nov/2026:12:00:00 +0700] '
            '"GET /lib/minigalnano/createthumb.php?filename=images%2Fdocs%2Fcreatethumb_%281%29.jpg.jpg&width=120 HTTP/1.1" '
            '200 1234'
        )
        other_log = '192.0.2.51 - - [19/Nov/2026:12:00:01 +0700] "GET /login.php HTTP/1.1" 200 500'
        db.add_alert(
            10, 'Alpha',
            description='Web access log',
            raw=json.dumps({'full_log': createthumb_log}),
        )
        db.add_alert(
            11, 'Alpha',
            description='Web access log',
            raw=json.dumps({'full_log': other_log}),
        )
        filters = json.dumps([{
            'field': 'full_log',
            'op': 'is_not',
            'value': '*/lib/minigalnano/createthumb.php?*',
            'value2': '',
        }])
        try:
            with patch.object(api, 'get_db', db.session):
                client = TestClient(api.app)
                try:
                    # Default Triage list + summary
                    default_list = client.get('/api/alerts', params={
                        'tenant': 'Alpha', 'review_status': 'all', 'filters': filters,
                    })
                    self.assertEqual(default_list.status_code, 200, default_list.text)
                    default_ids = {item['id'] for item in default_list.json()['items']}
                    self.assertNotIn(10, default_ids)
                    self.assertIn(11, default_ids)

                    # Triage opened from AI Triage with alert_ids + filters
                    scoped_params = {
                        'tenant': 'Alpha',
                        'review_status': 'all',
                        'alert_ids': '10,11',
                        'filters': filters,
                    }
                    ai_opened = client.get('/api/alerts', params=scoped_params)
                    ai_summary = client.get('/api/triage/summary', params=scoped_params)
                    self.assertEqual(ai_opened.status_code, 200, ai_opened.text)
                    self.assertEqual(ai_summary.status_code, 200, ai_summary.text)
                    self.assertEqual([item['id'] for item in ai_opened.json()['items']], [11])
                    self.assertEqual(ai_opened.json()['total'], 1)
                    self.assertEqual(ai_summary.json()['alerts'], 1)
                finally:
                    client.close()
        finally:
            db.connection.close()
