"""SQLite warehouse for climate dataset."""

import sqlite3
from pathlib import Path

import pandas as pd

SCHEMA = """
CREATE TABLE IF NOT EXISTS climate_daily (
    date      TEXT NOT NULL,
    admin1    TEXT NOT NULL,
    latitude  REAL,
    longitude REAL,
    tmean_c   REAL,
    tmax_c    REAL,
    tmin_c    REAL,
    precip_mm REAL,
    source    TEXT NOT NULL,
    PRIMARY KEY (date, admin1, source)
);
CREATE TABLE IF NOT EXISTS climate_monthly (
    date      TEXT NOT NULL,
    admin1    TEXT NOT NULL,
    latitude  REAL,
    longitude REAL,
    tmean_c   REAL,
    tmax_c    REAL,
    tmin_c    REAL,
    precip_mm REAL,
    source    TEXT NOT NULL,
    PRIMARY KEY (date, admin1, source)
);
CREATE INDEX IF NOT EXISTS idx_climate_daily_admin1_date ON climate_daily(admin1, date);
CREATE INDEX IF NOT EXISTS idx_climate_monthly_admin1_date ON climate_monthly(admin1, date);
"""


def connect(db_path: Path | str, **kwargs) -> sqlite3.Connection:
    from sokodata.datasets.markets.store import connect as base_connect

    return base_connect(db_path, **kwargs)


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()


def load_tables(
    conn: sqlite3.Connection, daily: pd.DataFrame, monthly: pd.DataFrame | None = None
) -> dict[str, int]:
    init_schema(conn)
    for df in (daily, monthly):
        if df is not None and not df.empty and "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"]).dt.date.astype(str)

    try:
        conn.execute("DELETE FROM climate_daily")
        conn.execute("DELETE FROM climate_monthly")
        if not daily.empty:
            daily.to_sql("climate_daily", conn, if_exists="append", index=False)
        if monthly is not None and not monthly.empty:
            monthly.to_sql("climate_monthly", conn, if_exists="append", index=False)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    return {"daily": len(daily), "monthly": len(monthly) if monthly is not None else 0}
