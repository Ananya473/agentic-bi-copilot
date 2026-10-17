
import sqlite3
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_PATH = PROJECT_ROOT / "data" / "retail_sales.db"
MAX_ROWS = 100


def _authorize_read_only(action, arg1, arg2, database, trigger):
    """Allow only read-only SELECT queries against approved tables."""

    if action == sqlite3.SQLITE_SELECT:
        return sqlite3.SQLITE_OK

    if action == sqlite3.SQLITE_READ:
        allowed_tables = {"sales", "transactions"}

        if database == "main" and arg1 in allowed_tables:
            return sqlite3.SQLITE_OK

        return sqlite3.SQLITE_DENY

    if action == sqlite3.SQLITE_FUNCTION:
        return sqlite3.SQLITE_OK

    return sqlite3.SQLITE_DENY


def execute_read_only_query(query: str) -> pd.DataFrame:
    """Execute a read-only query with restricted table access and row limits."""

    if not query or not query.strip():
        raise ValueError("SQL query cannot be empty.")

    cleaned_query = query.strip()

    # Accept one trailing semicolon, but reject multiple statements.
    if cleaned_query.endswith(";"):
        cleaned_query = cleaned_query[:-1].rstrip()

    if not cleaned_query:
        raise ValueError("SQL query cannot be empty.")

    if ";" in cleaned_query:
        raise ValueError("Only one SQL statement is allowed.")

    if not cleaned_query.lower().startswith(("select ", "with ")):
        raise ValueError("Only SELECT queries are allowed.")

    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            f"Database not found: {DATABASE_PATH}"
        )

    database_uri = f"{DATABASE_PATH.resolve().as_uri()}?mode=ro"

    with sqlite3.connect(database_uri, uri=True) as connection:
        connection.execute("PRAGMA query_only = ON")
        connection.set_authorizer(_authorize_read_only)

        # Wrap the query to cap returned rows.
        limited_query = (
            f"SELECT * FROM ({cleaned_query}) "
            f"AS query_result LIMIT {MAX_ROWS}"
        )

        return pd.read_sql_query(limited_query, connection)
