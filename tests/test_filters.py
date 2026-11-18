"""Filter-chip translation and validation; no database access."""
import unittest

from fastapi import HTTPException

from app.filters import build_filter_sql, parse_filters
from app.query import alert_where


class FilterSqlTests(unittest.TestCase):
    def test_contains_and_negation_are_parameterized(self):
        sql, params = build_filter_sql(
            '[{"field":"rule.description","op":"not_contains","value":"mhs"}]'
        )
        self.assertIn("NOT (", sql)
        self.assertIn("COALESCE(a.description, '') ILIKE %s", sql)
        self.assertEqual(params, ["%mhs%"])

    def test_glob_and_source_ip_negation(self):
        sql, params = build_filter_sql(
            '[{"field":"data.url","op":"glob","value":"*/mhs/*"},'
            '{"field":"data.srcip","op":"is_not","value":"10.0.0.1"}]'
        )
        self.assertIn("LIKE %s", sql)
        self.assertIn("NOT (COALESCE(a.source_ip, '') = %s)", sql)
        self.assertEqual(params, ["%/mhs/%", "10.0.0.1"])

    def test_level_range_uses_integer_bounds(self):
        sql, params = build_filter_sql(
            '[{"field":"rule.level","op":"range","value":"12","value2":"7"}]'
        )
        self.assertIn("a.rule_level BETWEEN %s AND %s", sql)
        self.assertEqual(params, [7, 12])

    def test_level_equality_binds_integer(self):
        _sql, params = build_filter_sql('[{"field":"rule.level","op":"is","value":"7"}]')
        self.assertEqual(params, [7])

    def test_aliases_and_list_input_are_accepted(self):
        parsed = parse_filters([{"field": "source_ip", "op": "contains", "value": "10."}])
        self.assertEqual(parsed[0]["field"], "data.srcip")

    def test_malformed_filters_are_rejected(self):
        for raw in (
            "not json",
            '[{"field":"unknown","op":"is","value":"x"}]',
            '[{"field":"rule.level","op":"range","value":"x","value2":"2"}]',
            '[{"field":"rule.description","op":"regex","value":"("}]',
            '[{"field":"rule.description","op":"is","value":""}]',
            '[{"field":"rule.description","op":"gte","value":"1"}]',
        ):
            with self.subTest(raw=raw):
                with self.assertRaises(HTTPException) as ctx:
                    build_filter_sql(raw)
                self.assertEqual(ctx.exception.status_code, 422)

    def test_alert_where_appends_filter_clause(self):
        sql, params = alert_where(
            tenant=["acme"],
            filters='[{"field":"rule.description","op":"not_glob","value":"*mhs*"}]',
        )
        self.assertIn("a.tenant = ANY(%s)", sql)
        self.assertIn("NOT (COALESCE(a.description, '') LIKE %s", sql)
        self.assertEqual(params, [["acme"], "%mhs%"])

    def test_alert_where_without_filters_is_unchanged(self):
        sql, params = alert_where(tenant=["acme"])
        self.assertNotIn("ILIKE", sql)
        self.assertEqual(params, [["acme"]])


if __name__ == "__main__":
    unittest.main()
