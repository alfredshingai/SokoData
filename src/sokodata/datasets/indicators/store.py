"""SQLite warehouse for indicators dataset."""

import sqlite3
from pathlib import Path

import pandas as pd

SCHEMA = """
CREATE TABLE IF NOT EXISTS indicators_annual (
    date       TEXT NOT NULL,
    country    TEXT NOT NULL,
    source     TEXT NOT NULL,
    -- SDG indicators will be added as columns dynamically
    PRIMARY KEY (date, country)
);
"""


def connect(db_path: str | Path, **kwargs) -> sqlite3.Connection:
    from sokodata.datasets.markets.store import connect as base_connect
    return base_connect(db_path, **kwargs)


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()


def load_annual(conn: sqlite3.Connection, annual: pd.DataFrame) -> dict[str, int]:
    if annual.empty:
        return {"annual": 0}
    
    annual = annual.copy()
    annual["date"] = pd.to_datetime(annual["date"]).dt.date.astype(str)
    annual["country"] = annual["country"].astype("string").str.strip().str.upper()
    annual["source"] = annual["source"].astype("string").str.strip()
    
    # Get value columns (exclude date, country, source)
    value_cols = [c for c in annual.columns if c not in ("date", "country", "source")]
    
    # Ensure table has columns for all value columns
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(indicators_annual)")
    existing_cols = {row[1] for row in cursor.fetchall()}
    
    for col in value_cols:
        if col not in existing_cols:
            conn.execute(f'ALTER TABLE indicators_annual ADD COLUMN "{col}" REAL')
            log.info("Added column %s to indicators_annual", col)
    
    try:
        conn.execute("DELETE FROM indicators_annual")
        # Select only columns that exist in table
        cols_to_insert = ["date", "country", "source"] + [c for c in value_cols if c in existing_cols or True]
        annual[cols_to_insert].to_sql("indicators_annual", conn, if_exists="append", index=False)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    return {"annual": len(annual)}