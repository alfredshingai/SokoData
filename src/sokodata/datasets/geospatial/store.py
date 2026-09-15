"""SQLite warehouse for geospatial dataset (metadata only; GeoJSON on disk)."""

import sqlite3
from pathlib import Path

import pandas as pd

SCHEMA = """
CREATE TABLE IF NOT EXISTS geospatial_metadata (
    name   TEXT PRIMARY KEY,
    format TEXT,
    url    TEXT,
    source TEXT NOT NULL
);
"""


def connect(db_path: Path | str, **kwargs) -> sqlite3.Connection:
    from sokodata.datasets.markets.store import connect as base_connect

    return base_connect(db_path, **kwargs)


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()


def load_tables(conn: sqlite3.Connection, metadata: pd.DataFrame) -> dict[str, int]:
    init_schema(conn)
    try:
        conn.execute("DELETE FROM geospatial_metadata")
        if not metadata.empty:
            metadata.to_sql("geospatial_metadata", conn, if_exists="append", index=False)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    return {"metadata": len(metadata)}
