"""Synthetic-only summary/list scope contracts; no configuration or live DB."""
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
