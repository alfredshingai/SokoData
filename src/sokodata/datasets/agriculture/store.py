"""SQLite warehouse for agriculture dataset."""

import sqlite3
from pathlib import Path

import pandas as pd

SCHEMA = """
CREATE TABLE IF NOT EXISTS agri_annual (
    date                TEXT PRIMARY KEY,
    cereal_yield_kg_ha  REAL,
    agri_gdp_pct        REAL,
    food_prod_idx       REAL,
    crop_prod_idx       REAL,
    source              TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS agri_fao_maize (
    date        TEXT PRIMARY KEY,
    maize_tonnes REAL NOT NULL,
    source      TEXT NOT NULL
);
"""


def connect(db_path: Path | str, **kwargs) -> sqlite3.Connection:
    from sokodata.datasets.markets.store import connect as base_connect

    return base_connect(db_path, **kwargs)


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()


def load_tables(conn: sqlite3.Connection, annual: pd.DataFrame, fao_maize: pd.DataFrame) -> dict[str, int]:
    init_schema(conn)
    for df in (annual, fao_maize):
        if not df.empty and "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"]).dt.date.astype(str)
    try:
        conn.execute("DELETE FROM agri_annual")
        conn.execute("DELETE FROM agri_fao_maize")
        if not annual.empty:
            annual.to_sql("agri_annual", conn, if_exists="append", index=False)
        if not fao_maize.empty:
            fao_maize.to_sql("agri_fao_maize", conn, if_exists="append", index=False)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    return {"annual": len(annual), "fao_maize": len(fao_maize)}
