"""SQLite warehouse for demographics dataset."""

import sqlite3
from pathlib import Path

import pandas as pd

SCHEMA = """
CREATE TABLE IF NOT EXISTS demo_annual (
    date            TEXT PRIMARY KEY,
    population      REAL,
    pop_growth_pct  REAL,
    urban_pct       REAL,
    source          TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS demo_census (
    admin1     TEXT PRIMARY KEY,
    population REAL NOT NULL,
    male       REAL,
    female     REAL,
    source     TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_demo_annual_date ON demo_annual(date);
"""


def connect(db_path: Path | str, **kwargs) -> sqlite3.Connection:
    from sokodata.datasets.markets.store import connect as base_connect

    return base_connect(db_path, **kwargs)


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()


def load_tables(conn: sqlite3.Connection, annual: pd.DataFrame, census: pd.DataFrame) -> dict[str, int]:
    init_schema(conn)
    for df in (annual,):
        if not df.empty and "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"]).dt.date.astype(str)
    try:
        conn.execute("DELETE FROM demo_annual")
        conn.execute("DELETE FROM demo_census")
        if not annual.empty:
            annual.to_sql("demo_annual", conn, if_exists="append", index=False)
        if not census.empty:
            census.to_sql("demo_census", conn, if_exists="append", index=False)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    return {"annual": len(annual), "census": len(census)}
