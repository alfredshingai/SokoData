"""SQLite warehouse for economy dataset."""

import sqlite3
from pathlib import Path

import pandas as pd

SCHEMA = """
CREATE TABLE IF NOT EXISTS economy_rates (
    date   TEXT NOT NULL,
    rate   REAL NOT NULL,
    source TEXT NOT NULL,
    PRIMARY KEY (date, source)
);
CREATE TABLE IF NOT EXISTS economy_cpi (
    date            TEXT NOT NULL,
    cpi             REAL,
    inflation_yoy   REAL,
    inflation_mom   REAL,
    source          TEXT NOT NULL,
    PRIMARY KEY (date, source)
);
CREATE TABLE IF NOT EXISTS economy_fuel (
    date      TEXT NOT NULL,
    fuel_type TEXT NOT NULL,
    price     REAL NOT NULL,
    currency  TEXT NOT NULL,
    source    TEXT NOT NULL,
    PRIMARY KEY (date, fuel_type, source)
);
CREATE TABLE IF NOT EXISTS dataset_meta (
    dataset_id TEXT PRIMARY KEY,
    last_sync  TEXT,
    rows       INTEGER
);
"""


def connect(db_path: Path | str, **kwargs) -> sqlite3.Connection:
    from sokodata.datasets.markets.store import connect as base_connect

    return base_connect(db_path, **kwargs)


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()


def load_tables(
    conn: sqlite3.Connection,
    rates: pd.DataFrame,
    cpi: pd.DataFrame,
    fuel: pd.DataFrame,
) -> dict[str, int]:
    init_schema(conn)
    # Normalize dates to ISO
    for df in (rates, cpi, fuel):
        if not df.empty and "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"]).dt.date.astype(str)

    try:
        conn.execute("DELETE FROM economy_rates")
        conn.execute("DELETE FROM economy_cpi")
        conn.execute("DELETE FROM economy_fuel")
        if not rates.empty:
            rates.to_sql("economy_rates", conn, if_exists="append", index=False)
        if not cpi.empty:
            cpi.to_sql("economy_cpi", conn, if_exists="append", index=False)
        if not fuel.empty:
            fuel.to_sql("economy_fuel", conn, if_exists="append", index=False)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    return {"rates": len(rates), "cpi": len(cpi), "fuel": len(fuel)}
