"""CodexDB Research V2 SQL-only pipeline.

The natural-language step intentionally uses CodexDB's SqlGenerator,
and the execution step uses its refactored SqliteEngine. Python fallback
is NOT activated here; this is the frozen baseline candidate.
"""
import time

from codexdb.code import SqlGenerator
from codexdb.engine import SqliteEngine



class _LiveSchemaCatalog:
    """CodexDB catalog facade exposing SQLite's real tables to SqlGenerator."""
    def __init__(self, catalog):
        self._catalog = catalog

    def schema(self, db_id):
        if hasattr(self._catalog, 'sqlite_schema'):
            return self._catalog.sqlite_schema(db_id)
        # Allows minimal in-memory test catalogs that implement schema().
        return self._catalog.schema(db_id)

    def files(self, db_id):
        if hasattr(self._catalog, 'file_name'):
            return [
                self._catalog.file_name(db_id, table)
                for table in self.schema(db_id)['table_names_original']
            ]
        return self._catalog.files(db_id)

    def __getattr__(self, attribute):
        return getattr(self._catalog, attribute)


def run_sql_only(catalog, db_id, question, *, model_id, prompt_style='schema',
                 examples=None, nr_samples=0, temperature=0.0,
                 max_rows=200, timeout_s=10):
    """Return structured metadata and DataFrame; errors are not counted as correct.

    Raises on invalid prompt/experiment configuration. LLM API calls still
    require configured credentials, are nondeterministic and may incur costs.
    """
    if not question or not question.strip():
        raise ValueError('A nonempty natural-language question is required')
    if db_id not in catalog.db_ids():
        raise ValueError('Unknown database id: ' + str(db_id))

    schema_catalog = _LiveSchemaCatalog(catalog)
    generator = SqlGenerator(
        schema_catalog, list(examples or []), nr_samples, prompt_style, model_id
    )
    engine = SqliteEngine(catalog, max_rows=max_rows)
    test_case = {'question': question.strip(), 'query': '', 'db_id': db_id}
    started = time.monotonic()
    gen_stats, sql = generator.generate(test_case, temperature)
    response = {
        'question': question.strip(),
        'db_id': db_id,
        'model_id': model_id,
        'prompt_style': prompt_style,
        'nr_samples': nr_samples,
        'sql': sql,
        'generation': gen_stats,
        'ok': False,
        'execution': {},
        'elapsed_s': None,
        'result': None,
    }
    if gen_stats.get('error') or not sql.strip():
        response['execution'] = {'error_type': 'GenerationError'}
    else:
        success, df, exec_stats = engine.execute(db_id, sql, timeout_s)
        response['ok'] = success
        response['execution'] = exec_stats
        if success:
            response['result'] = df
    response['elapsed_s'] = time.monotonic() - started
    return response
