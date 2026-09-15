"""SQLite warehouse for trade dataset."""

import sqlite3
from pathlib import Path

import pandas as pd

SCHEMA = """
CREATE TABLE IF NOT EXISTS trade_annual (
    date              TEXT PRIMARY KEY,
    exports_pct_gdp   REAL,
    imports_pct_gdp   REAL,
    merch_exports_usd REAL,
    merch_imports_usd REAL,
    source            TEXT NOT NULL
);
"""


def connect(db_path: Path | str, **kwargs) -> sqlite3.Connection:
    from sokodata.datasets.markets.store import connect as base_connect

    return base_connect(db_path, **kwargs)


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()


def load_tables(conn: sqlite3.Connection, annual: pd.DataFrame) -> dict[str, int]:
    init_schema(conn)
    if not annual.empty and "date" in annual.columns:
        annual["date"] = pd.to_datetime(annual["date"]).dt.date.astype(str)
    try:
        conn.execute("DELETE FROM trade_annual")
        if not annual.empty:
            annual.to_sql("trade_annual", conn, if_exists="append", index=False)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    return {"annual": len(annual)}
