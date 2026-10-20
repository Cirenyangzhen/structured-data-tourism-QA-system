"""Hardened SQLite execution for CodexDB Research V2.

Accepts only a single read-only SELECT/UNION query, runs against an existing
database file in read-only mode, and bounds work and output. Not a substitute
for a process/container sandbox on a public endpoint.
"""
from contextlib import closing
from pathlib import Path
from urllib.parse import quote
import sqlite3
import time

import pandas as pd
import sqlglot
from sqlglot import exp


class SQLValidationError(ValueError):
    pass


class SQLExecutionError(RuntimeError):
    pass


def validate_sql(sql):
    if not isinstance(sql, str) or not sql.strip():
        raise SQLValidationError("Empty SQL query")
    try:
        statements = sqlglot.parse(sql, read="sqlite")
    except Exception as exc:
        raise SQLValidationError("Cannot parse SQLite query") from exc
    if len(statements) != 1 or not isinstance(statements[0], (exp.Select, exp.Union)):
        raise SQLValidationError("Only a single read-only SELECT is supported")
    # The AST test is not the sole safety boundary; SQLite's authorizer is
    # additionally enabled below to deny every non-read operation.
    forbidden = {
        "Insert", "Update", "Delete", "Drop", "Create", "Alter",
        "Command", "Merge", "Transaction", "Set", "Pragma",
    }
    if any(type(node).__name__ in forbidden for node in statements[0].walk()):
        raise SQLValidationError("Forbidden SQL operation")
    return sql.strip()


_DENIED_ACTIONS = {
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


def execute_select(sql, db_path, *, max_rows=200, max_opcodes=1000000,
                   timeout_s=10.0):
    """Return (pandas DataFrame, stats) without mutating the SQLite file."""
    statement = validate_sql(sql)
    if max_rows < 1 or max_opcodes < 1000 or timeout_s <= 0:
        raise ValueError("Execution limits must be positive")
    path = Path(db_path).expanduser().resolve(strict=True)
    if not path.is_file():
        raise SQLExecutionError("SQLite file not found")
    uri = "file:" + quote(path.as_posix(), safe="/:") + "?mode=ro"
    started = time.monotonic()
    progress_count = 0

    def progress():
        nonlocal progress_count
        progress_count += 1000
        return int(
            progress_count >= max_opcodes
            or time.monotonic() - started >= timeout_s
        )

    def authorizer(action, p1, p2, db_name, trigger):
        if action in _DENIED_ACTIONS:
            return sqlite3.SQLITE_DENY
        if action == sqlite3.SQLITE_FUNCTION and (
            (p1 or p2 or "").lower() == "load_extension"
        ):
            return sqlite3.SQLITE_DENY
        return sqlite3.SQLITE_OK

    try:
        with closing(sqlite3.connect(uri, uri=True, timeout=timeout_s)) as con:
            con.execute("PRAGMA query_only = ON")
            con.set_authorizer(authorizer)
            con.set_progress_handler(progress, 1000)
            cursor = con.execute(statement)
            columns = [item[0] for item in cursor.description]
            values = cursor.fetchmany(max_rows + 1)
    except sqlite3.Error as exc:
        raise SQLExecutionError("SQLite refused or interrupted the query") from exc
    duration = time.monotonic() - started
    return pd.DataFrame.from_records(values[:max_rows], columns=columns), {
        "execution_s": duration,
        "row_count": min(len(values), max_rows),
        "truncated": len(values) > max_rows,
        "db_path": str(path),
    }
