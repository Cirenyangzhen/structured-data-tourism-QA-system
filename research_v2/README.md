# Research V2 · SQL-only baseline (Phase 1)

**State:** initial offline implementation, **not yet run/validated on the real tourism DB**, and **not a tested LLM pipeline**.

## Research question
Can a carefully controlled LLM-to-SQL pipeline answer Chinese tourism questions correctly and reliably before adding Python fallback?

## Pipeline
1. Natural-language question → schema-aware prompt (model adapter: **pending**).
2. LLM SQL response (model adapter: **pending**).
3. SQL AST validation (`sql_baseline.validate_sql`).
4. Read-only SQLite execution (`sql_baseline.run_read_only`).
5. Return bounded tabular results, and record execution status.
6. Evaluate on an independently reviewed, frozen gold question set (**pending**).

## Run offline tests
From repository root, install the repository's pinned `sqlglot` dependency in a disposable environment, then:

```bash
python -m unittest discover -s tests -p "test_sql_baseline.py" -v
```

Tests use a temporary tiny SQLite database and **no API credentials, no network, and no LLM calls**. They are not accuracy measurements. Do not execute existing CodexDB's LLM-generated Python on your host machine.

## Important caveats
- The legacy CodexDB `SqliteEngine` reconstructs an SQLite DB from CSV on execution; the V2 executor instead opens a fixed SQLite DB read-only. This is an intentional separate component.
- This read-only executor uses SQL parsing, SQLite read-only URI mode, query-only mode, an authorizer and execution limits as defense in depth. Security review and isolated runtime tests are still required before accepting arbitrary untrusted SQL from public users.
- The AST validator admits only single SELECT/UNION query roots; additional legitimate SQL syntax may need safe support added following tests.
- The original bachelor's thesis' reported 82% (246/300) is historical **thesis-reported** evidence, not a result of this branch.
- The 100-query historical prompt-comparison results are also not reproduced here.
- Before any new experiment: version the database, define evaluation questions, confirm ground-truth answers, prevent few-shot/test leakage, freeze metrics and prompts.

## Roadmap
1. Audit the real `CodexDB/tourism/database/tourism/tourism.sqlite` schema against CSV files, `schema.sql` and `schemata.json`.
2. Run the tests in a clean environment and fix any issues.
3. Implement a model adapter and verifiable Basic/Schema-aware/Few-shot prompt builders.
4. Create a CSV/JSONL per-question evaluation harness with correct SQL/results and full experimental metadata.
5. Freeze the SQL-only baseline. Only then implement an isolated Question-to-Python comparator and adaptive Hybrid routing.

No old records, data, or original thesis were overwritten.
