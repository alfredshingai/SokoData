"""SQLite warehouse for ICT dataset."""

import sqlite3
from pathlib import Path

import pandas as pd

SCHEMA = """
CREATE TABLE IF NOT EXISTS ict_annual (
    date                  TEXT PRIMARY KEY,
    internet_users_pct    REAL,
    cell_subs_per_100     REAL,
    fixed_broadband_per_100 REAL,
    tel_lines_per_100     REAL,
    source                TEXT NOT NULL
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
        conn.execute("DELETE FROM ict_annual")
        if not annual.empty:
            annual.to_sql("ict_annual", conn, if_exists="append", index=False)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    return {"annual": len(annual)}
