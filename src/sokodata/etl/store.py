"""SQLite warehouse for cleaned SokoData tables."""

import sqlite3
from pathlib import Path

import pandas as pd

SCHEMA = """
CREATE TABLE IF NOT EXISTS markets (
    market_id  INTEGER PRIMARY KEY,
    market     TEXT NOT NULL,
    countryiso3 TEXT,
    admin1     TEXT,
    admin2     TEXT,
    latitude   REAL,
    longitude  REAL
);

CREATE TABLE IF NOT EXISTS prices (
    date         TEXT NOT NULL,
    market_id    INTEGER NOT NULL REFERENCES markets(market_id),
    commodity_id INTEGER NOT NULL,
    commodity    TEXT NOT NULL,
    category     TEXT NOT NULL,
    unit         TEXT NOT NULL,
    priceflag    TEXT NOT NULL,
    pricetype    TEXT NOT NULL,
    currency     TEXT NOT NULL,
    price        REAL NOT NULL,
    usdprice     REAL,
    PRIMARY KEY (date, market_id, commodity_id, pricetype, priceflag)
);

CREATE INDEX IF NOT EXISTS idx_prices_commodity_market_date
    ON prices (commodity_id, market_id, date);
CREATE INDEX IF NOT EXISTS idx_prices_date ON prices (date);
"""


def connect(
    db_path: Path | str, *, read_only: bool = False, check_same_thread: bool = True
) -> sqlite3.Connection:
    """Open a connection; in read-only mode the database file must exist.

    Pass ``check_same_thread=False`` when sharing one connection across
    FastAPI's threadpool (the app serializes access via the GIL).
    """
    path = Path(db_path)
    if read_only:
        if not path.exists():
            raise FileNotFoundError(f"database not found: {path}")
        conn = sqlite3.connect(
            f"file:{path.as_posix()}?mode=ro", uri=True, check_same_thread=check_same_thread
        )
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(path, check_same_thread=check_same_thread)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()


def load_tables(
    conn: sqlite3.Connection, prices: pd.DataFrame, markets: pd.DataFrame
) -> tuple[int, int]:
    """Replace both tables in one transaction (idempotent full refresh).

    The cleaned prices frame keeps the full source schema for validation;
    storage stores the 11 warehouse columns (location fields live in
    ``markets`` and are re-joined at query time).
    """
    storage_cols = [
        "date",
        "market_id",
        "commodity_id",
        "commodity",
        "category",
        "unit",
        "priceflag",
        "pricetype",
        "currency",
        "price",
        "usdprice",
    ]
    price_rows = prices[storage_cols]
    init_schema(conn)
    try:
        conn.execute("DELETE FROM prices")
        conn.execute("DELETE FROM markets")
        markets.to_sql("markets", conn, if_exists="append", index=False)
        price_rows.to_sql("prices", conn, if_exists="append", index=False)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    return len(price_rows), len(markets)
