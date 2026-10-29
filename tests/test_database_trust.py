"""Database trust contracts: synthetic config/driver, never .env or network."""
import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
from fastapi.testclient import TestClient
from tests.test_ui_api import load_isolated_api, SyntheticDB

ROOT = Path(__file__).resolve().parents[1]


def load_database():
    config = types.ModuleType('app.config')
    config.DATABASE_URL = 'postgresql://synthetic:local-secret@local.invalid/test'
    config.REMOTE_DATABASE_URL = 'postgresql://synthetic:remote-secret@remote.invalid/test'
    config.ACTIVE_DB_PROFILE = 'local'
    driver = types.ModuleType('psycopg')
    driver.connect = MagicMock(side_effect=AssertionError('Network forbidden'))
    rows = types.ModuleType('psycopg.rows')
    rows.dict_row = object()
    spec = importlib.util.spec_from_file_location('isolated_database_trust', ROOT / 'app/database.py')
    module = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, {'app.config': config, 'psycopg': driver, 'psycopg.rows': rows}):
        spec.loader.exec_module(module)
    return module


class DatabaseTrustTests(unittest.TestCase):
    def setUp(self):
        self.db = load_database()
        self.api = load_isolated_api()
        self.api.db_module = self.db
        self.client = TestClient(self.api.app)
        self.addCleanup(self.client.close)

    def test_profile_probe_uses_requested_profile_without_switching(self):
        connection = MagicMock()
        connection.__enter__.return_value.execute.return_value.fetchone.return_value = {'v': 'PostgreSQL synthetic'}
        self.db.psycopg.connect.side_effect = None
        self.db.psycopg.connect.return_value = connection
        response = self.client.post('/api/database/test', json={'profile': 'remote'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['ok'])
        self.assertEqual(self.db.psycopg.connect.call_args.args[0], self.db._db_profiles['remote']['url'])
        self.assertEqual(self.db.get_active_profile_id(), 'local')

    def test_masked_uri_replacement_is_rejected_without_mutation(self):
        original = self.db._db_profiles['remote']['url']
        for value in ('postgresql://user:***@synthetic.invalid/db', 'postgresql://user:%2A%2A%2A@synthetic.invalid/db'):
            response = self.client.post('/api/database/config', json={'profile': 'remote', 'url': value})
            self.assertEqual(response.status_code, 400)
            self.assertEqual(self.db._db_profiles['remote']['url'], original)

    def test_unknown_profile_probe_rejected_without_connection(self):
        response = self.client.post('/api/database/test', json={'profile': 'missing'})
        self.assertEqual(response.status_code, 400)
        self.db.psycopg.connect.assert_not_called()
