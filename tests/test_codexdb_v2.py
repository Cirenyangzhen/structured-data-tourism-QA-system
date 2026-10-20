"""Offline V2 regression tests; no network and no LLM credentials required."""
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'CodexDB' / 'src'))

from codexdb.code import SqlGenerator
from codexdb.engine import SqliteEngine
from codexdb.v2_sql_pipeline import run_sql_only


class TinyCatalog:
    def __init__(self, root):
        self.root = Path(root)
        self.schema_def = {
            'db_id': 'tourism',
            'table_names_original': ['attractions'],
            'column_names_original': [[-1, '*'], [0, 'name'], [0, 'rating']],
            'foreign_keys': [],
        }

    def schema(self, db_id):
        return self.schema_def

    def files(self, db_id):
        return ['attractions.csv']

    def db_dir(self, db_id):
        return str(self.root / db_id)

    def db_ids(self):
        return ['tourism']


class V2IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.catalog = TinyCatalog(self.temp.name)
        root = Path(self.catalog.db_dir('tourism'))
        root.mkdir()
        self.db_path = root / 'tourism.sqlite'
        with sqlite3.connect(self.db_path) as connection:
            connection.executescript(
                "CREATE TABLE attractions (name TEXT, rating REAL);"
                "INSERT INTO attractions VALUES ('巴松措', 4.6);"
                "INSERT INTO attractions VALUES ('大峡谷', 4.7);"
                "INSERT INTO attractions VALUES ('山峰', 4.5);"
            )

    def test_sql_generator_is_sqlite_not_python(self):
        g = SqlGenerator(self.catalog, [], 0, 'schema', 'test-model')
        p = g.get_prompt(self.catalog.schema('tourism'), '', [], '评分最高的景点', '')
        self.assertIn('SQLite', p)
        self.assertIn('attractions(name, rating)', p)
        self.assertIn('评分最高的景点', p)
        self.assertIn('SQL', g.system_prompt)
        self.assertNotIn('You write Python code', g.system_prompt)

    def test_basic_prompt_does_not_leak_schema(self):
        g = SqlGenerator(self.catalog, [], 0, 'basic', 'test-model')
        p = g.get_prompt(self.catalog.schema('tourism'), '', [], '所有景点', '')
        self.assertNotIn('attractions(name', p)

    def test_fewshot_examples_are_real_and_counted(self):
        examples = [{'question': '所有景点', 'query': 'SELECT name FROM attractions;'}]
        g = SqlGenerator(self.catalog, examples, 1, 'fewshot', 'test-model')
        prefix = g._sample_prompts()
        self.assertIn('SELECT name FROM attractions;', prefix)
        with self.assertRaises(ValueError):
            SqlGenerator(self.catalog, [], 1, 'fewshot', 'test-model')._sample_prompts()

    def test_parse_sql_fence(self):
        g = SqlGenerator(self.catalog, [], 0, 'schema', 'test-model')
        code = g._extract_code({
            'choices': [{'message': {'content': '```sql\nSELECT name FROM attractions;\n```'}}]
        })
        self.assertEqual(code, 'SELECT name FROM attractions;')

    def test_engine_executes_select_in_existing_database(self):
        engine = SqliteEngine(self.catalog)
        ok, df, stats = engine.execute(
            'tourism',
            'SELECT name FROM attractions WHERE rating > 4.5 ORDER BY rating DESC',
            5,
        )
        self.assertTrue(ok, stats)
        self.assertEqual(df['name'].tolist(), ['大峡谷', '巴松措'])
        self.assertEqual(stats['row_count'], 2)

    def test_engine_does_not_write_or_recreate_database(self):
        engine = SqliteEngine(self.catalog)
        ok, _df, stats = engine.execute('tourism', 'DELETE FROM attractions', 5)
        self.assertFalse(ok)
        self.assertEqual(stats['error_type'], 'SQLValidationError')
        with sqlite3.connect(self.db_path) as conn:
            self.assertEqual(conn.execute('SELECT COUNT(*) FROM attractions').fetchone()[0], 3)

    def test_engine_rejects_multiple_statements(self):
        engine = SqliteEngine(self.catalog)
        ok, _df, stats = engine.execute('tourism', 'SELECT 1; DROP TABLE attractions', 5)
        self.assertFalse(ok)
        self.assertEqual(stats['error_type'], 'SQLValidationError')

    def test_engine_limits_result_rows(self):
        engine = SqliteEngine(self.catalog, max_rows=2)
        ok, df, stats = engine.execute('tourism', 'SELECT name FROM attractions', 5)
        self.assertTrue(ok, stats)
        self.assertEqual(len(df), 2)
        self.assertTrue(stats['truncated'])

    def test_pipeline_connects_both_codexdb_components_without_api(self):
        stub = (
            {'error': False, 'prompt_tokens': 15, 'completion_tokens': 20},
            'SELECT name FROM attractions WHERE rating > 4.5 ORDER BY rating DESC'
        )
        with patch.object(SqlGenerator, 'generate', return_value=stub):
            answer = run_sql_only(
                self.catalog, 'tourism', '有哪些评分高于4.5的景点？',
                model_id='mock', prompt_style='schema'
            )
        self.assertTrue(answer['ok'], answer)
        self.assertEqual(answer['result']['name'].tolist(), ['大峡谷', '巴松措'])
        self.assertEqual(answer['nr_samples'], 0)


if __name__ == '__main__':
    unittest.main()
