"""Offline regression tests for the V2 SQL-only execution component."""
import sqlite3
import tempfile
import unittest
from pathlib import Path

from research_v2.sql_baseline import SQLValidationError, run_read_only, validate_sql


class ReadOnlyBaselineTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db = Path(self.temp_dir.name) / "tourism.sqlite"
        with sqlite3.connect(self.db) as con:
            con.executescript("""
                CREATE TABLE attractions (name TEXT, rating REAL);
                INSERT INTO attractions VALUES ('巴松措', 4.6);
                INSERT INTO attractions VALUES ('南迦巴瓦峰', 4.5);
                INSERT INTO attractions VALUES ('雅鲁藏布大峡谷', 4.7);
            """)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_select_and_order(self):
        result = run_read_only(
            "SELECT name FROM attractions WHERE rating > 4.5 ORDER BY rating DESC",
            self.db,
        )
        self.assertEqual([r[0] for r in result["rows"]], ["雅鲁藏布大峡谷", "巴松措"])

    def test_with_cte(self):
        result = run_read_only(
            "WITH top AS (SELECT * FROM attractions WHERE rating > 4.5) "
            "SELECT COUNT(*) AS n FROM top", self.db
        )
        self.assertEqual(result["rows"], [[2]])

    def test_limit_and_truncation(self):
        result = run_read_only("SELECT name FROM attractions ORDER BY name", self.db, max_rows=2)
        self.assertEqual(result["row_count"], 2)
        self.assertTrue(result["truncated"])

    def test_write_rejected_before_execution(self):
        with self.assertRaises(SQLValidationError):
            run_read_only("DELETE FROM attractions", self.db)

    def test_multistatement_rejected(self):
        with self.assertRaises(SQLValidationError):
            validate_sql("SELECT 1; DROP TABLE attractions;")

    def test_empty_sql_rejected(self):
        with self.assertRaises(SQLValidationError):
            validate_sql("")

    def test_database_remains_unchanged(self):
        with self.assertRaises(SQLValidationError):
            run_read_only("UPDATE attractions SET rating=0", self.db)
        with sqlite3.connect(self.db) as con:
            self.assertEqual(con.execute("SELECT COUNT(*) FROM attractions").fetchone()[0], 3)


if __name__ == "__main__":
    unittest.main()
