"""Research V2: read-only SQLite execution component (offline baseline).

This component is deliberately independent of the old CodexDB Python execution
engine. It accepts SQL, not a natural-language question. Model integration
belongs in a separate adapter and must be evaluated independently.

Safety layers: single-statement AST check, SQLite read-only connection, query_only
mode, authorizer for SQLite write/attach actions, progress callback, result limit.
These measures are defense in depth, not a complete security sandbox.
"""
from __future__ import annotations
from pathlib import Path
import sqlite3
from urllib.parse import quote

import sqlglot
from sqlglot import exp


class SQLValidationError(ValueError):
    pass


class SQLExecutionError(RuntimeError):
    pass


def validate_sql(sql: str) -> str:
    if not isinstance(sql, str) or not sql.strip():
        raise SQLValidationError("SQL must be a nonempty string")
    try:
        parsed = sqlglot.parse(sql, read="sqlite")
    except Exception as exc:
        raise SQLValidationError("SQL could not be parsed") from exc
    if len(parsed) != 1 or not isinstance(parsed[0], (exp.Select, exp.Union)):
        raise SQLValidationError("Only one SELECT statement is permitted")
    # Enforce no DML, DDL, transaction, command, or side effect inside subqueries.
    blocked_names = {'Insert', 'Update', 'Delete', 'Drop', 'Create',
                     'Alter', 'Command', 'Merge', 'Transaction', 'Set', 'Pragma'}
    if any(type(node).__name__ in blocked_names for node in parsed[0].walk()):
        raise SQLValidationError("SQL contains a forbidden operation")
    return sql.strip()


# Defense in depth: SQLite authorizer denies mutations and database attachment.
_FORBIDDEN_ACTIONS = {
    sqlite3.SQLITE_INSERT, sqlite3.SQLITE_UPDATE, sqlite3.SQLITE_DELETE,
    sqlite3.SQLITE_CREATE_INDEX, sqlite3.SQLITE_CREATE_TABLE,
    sqlite3.SQLITE_CREATE_TEMP_INDEX, sqlite3.SQLITE_CREATE_TEMP_TABLE,
    sqlite3.SQLITE_CREATE_TEMP_TRIGGER, sqlite3.SQLITE_CREATE_TEMP_VIEW,
    sqlite3.SQLITE_CREATE_TRIGGER, sqlite3.SQLITE_CREATE_VIEW,
    sqlite3.SQLITE_DROP_INDEX, sqlite3.SQLITE_DROP_TABLE,
    sqlite3.SQLITE_DROP_TEMP_INDEX, sqlite3.SQLITE_DROP_TEMP_TABLE,
    sqlite3.SQLITE_DROP_TEMP_TRIGGER, sqlite3.SQLITE_DROP_TEMP_VIEW,
    sqlite3.SQLITE_DROP_TRIGGER, sqlite3.SQLITE_DROP_VIEW,
    sqlite3.SQLITE_ALTER_TABLE, sqlite3.SQLITE_ATTACH, sqlite3.SQLITE_DETACH,
    sqlite3.SQLITE_PRAGMA, sqlite3.SQLITE_TRANSACTION,
}


def run_read_only(sql: str, db_path: str | Path, *, max_rows: int = 200,
                  max_steps: int = 100000, timeout_seconds: float = 5.0) -> dict:
    """Execute only read-only SELECT SQL and return a bounded result.

    This is not an LLM accuracy test; it only checks query execution.
    """
    import time

    statement = validate_sql(sql)
    path = Path(db_path).expanduser().resolve(strict=True)
    if not path.is_file():
        raise SQLExecutionError("Database path is not a file")
    if max_rows < 1 or max_steps < 1 or timeout_seconds <= 0:
        raise ValueError("Execution limits must be positive")

    # Quoting keeps spaces and special characters in filesystem paths valid.
    uri = "file:" + quote(str(path).replace("\\", "/"), safe="/:") + "?mode=ro"
    started = time.monotonic()
    ticks = 0

    def progress():
        nonlocal ticks
        ticks += 1
        if ticks * 1000 > max_steps or time.monotonic() - started > timeout_seconds:
            return 1
        return 0

    def authorize(action, arg1, arg2, dbname, source):
        return sqlite3.SQLITE_DENY if action in _FORBIDDEN_ACTIONS else sqlite3.SQLITE_OK

    try:
        with sqlite3.connect(uri, uri=True, timeout=timeout_seconds) as con:
            con.execute("PRAGMA query_only=ON")
            con.set_authorizer(authorize)
            con.set_progress_handler(progress, 1000)
            cursor = con.execute(statement)
            columns = [description[0] for description in cursor.description or []]
            rows = cursor.fetchmany(max_rows + 1)
    except sqlite3.Error as exc:
        raise SQLExecutionError("SQLite rejected or interrupted the query") from exc

    return {
        "columns": columns,
        "rows": [list(row) for row in rows[:max_rows]],
        "truncated": len(rows) > max_rows,
        "row_count": min(len(rows), max_rows),
    }
