# Research V2 — Hybrid Text-to-SQL project

## Current implementation: Phase 1 SQL-only baseline

The goal is a robust **Text-to-SQL first** architecture based on existing CodexDB components. Do not confuse this stage with the final Hybrid system.

### Components actually wired together

- **CodexDB `DbCatalog.sqlite_schema`**: introspects the real read-only SQLite database, avoiding stale `schemata.json` entries.
- **CodexDB `SqlGenerator`**: generates SQLite SQL from Chinese natural language using the configured LLM, with `basic`, `schema`, and explicit `fewshot` styles.
- **CodexDB `SqliteEngine`**: keeps its `execute(db_id, sql, timeout_s)` interface, while executing against the existing SQLite file in read-only mode using `codexdb.sql_execution`.
- **`codexdb.v2_sql_pipeline.run_sql_only`**: links these components and returns structured metadata.
- **`codexdb/gui_v2.py`**: new Streamlit entry point. The original `gui.py` is retained unchanged as legacy evidence.
- **`tests/test_codexdb_v2.py`**: offline mocked-model integration tests.

The previous independent `research_v2/sql_baseline.py` is kept as a reference implementation; the new application uses **CodexDB's own `SqliteEngine`**, not that independent module.

### Start on Windows (PowerShell)

```powershell
git switch research-v2-rebuild-20261019
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r CodexDB/requirements.txt
python -m unittest discover -s tests -p "test_codexdb_v2.py" -v
streamlit run CodexDB/src/codexdb/gui_v2.py
```

Configure `OPENAI_API_KEY` securely as an environment variable before launching the Streamlit app; do not put API keys in command-line arguments, committed files, screenshots, or chat messages. The app **does not automatically read a `.env` file**. A model call may incur API costs and needs a model your account can access.

### Validation boundaries

- The integration tests use a temporary SQLite database and a **mocked LLM**. They do not measure actual Text-to-SQL accuracy, API latency, or cost.
- The real tourism database `CodexDB/tourism/database/tourism/tourism.sqlite` is required for the app. V2 reads its actual schema; it does **not** rebuild the DB on every query.
- Only read-only SELECT/UNION SQL is permitted; the executor also uses SQLite `mode=ro`, `query_only`, authorizer, opcode and row limits.
- These are defense-in-depth controls, **not** a complete public-facing sandbox or formal SQL safety proof.
- The sample Few-shot pairs in `CodexDB/tourism/fewshot_examples.json` are illustrative development examples, not evaluated gold-standard examples. Exclude overlaps with any test set.
- These changes have been **committed but not yet confirmed by executing the integration tests against the repository in the target environment**. Do not report an accuracy number until it is actually measured.
- The bachelor's thesis historical 82% (246/300) result is a **thesis-reported figure**, not a verified result from V2.

### Next phases (not implemented yet)

2. Independent Question-to-Python using the existing CodexDB `PythonGenerator`. **Never run LLM-generated Python on the host**; require isolated restricted execution first.
3. Paired SQL-only and Python-only experiments on a frozen gold question set.
4. LLM-based SQL Critic; evaluate TP/FP/FN/TN, Precision/Recall/F1 **separately** from final answer correctness.
5. Adaptive Hybrid decision/routing, SQL repair, safe Python fallback, and reporting of accuracy, costs and latency.

### Project hygiene

Development branch: `research-v2-rebuild-20261019`. Do not merge with `main` or the separate local `fix/security-credentials` branch until the security audit and comparison are complete. No edits to original thesis, experiments, or existing datasets are intended.
