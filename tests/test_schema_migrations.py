"""Static migration-order guard; never imports config or opens a database."""
import unittest
from pathlib import Path

SOURCE = (Path(__file__).resolve().parents[1] / "app" / "database.py").read_text(encoding="utf-8")


class SchemaMigrationOrderTests(unittest.TestCase):
    def test_claim_index_is_not_in_schema_sql(self):
        schema = SOURCE.split('SCHEMA_SQL = """', 1)[1].split('"""', 1)[0]
        self.assertNotIn(
            "CREATE INDEX IF NOT EXISTS idx_wazuh_alerts_claim_status",
            schema,
            "The claim index depends on columns added by ALTER TABLE after SCHEMA_SQL runs.",
        )

    def test_claim_index_is_created_after_profile_columns(self):
        init = SOURCE.split("def init_database", 1)[1].split("\ndef ", 1)[0]
        self.assertIn("ADD COLUMN IF NOT EXISTS status", init)
        self.assertIn("ADD COLUMN IF NOT EXISTS claimed_by", init)
        self.assertIn("idx_wazuh_alerts_claim_status", init)
        self.assertLess(
            init.index("ADD COLUMN IF NOT EXISTS status"),
            init.index("idx_wazuh_alerts_claim_status"),
        )


if __name__ == "__main__":
    unittest.main()
