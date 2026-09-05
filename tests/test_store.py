"""Tests for the SQLite store."""

from sokodata.etl.clean import clean_prices
from sokodata.etl.store import connect, load_tables


def test_load_and_read_back(test_db, raw_prices):
    conn = connect(test_db, read_only=True)
    try:
        n = conn.execute("SELECT COUNT(*) FROM prices").fetchone()[0]
        m = conn.execute("SELECT COUNT(*) FROM markets").fetchone()[0]
        assert n == len(clean_prices(raw_prices))
        assert m == 2
        # natural key is enforced
        assert conn.execute(
            "SELECT COUNT(*) FROM (SELECT DISTINCT date, market_id, commodity_id,"
            " pricetype, priceflag FROM prices)"
        ).fetchone()[0] == n
    finally:
        conn.close()


def test_load_is_idempotent(test_db, raw_prices, sample_markets):
    prices = clean_prices(raw_prices)
    conn = connect(test_db)
    try:
        load_tables(conn, prices, sample_markets)
    finally:
        conn.close()
    conn = connect(test_db, read_only=True)
    try:
        assert conn.execute("SELECT COUNT(*) FROM prices").fetchone()[0] == len(prices)
        assert conn.execute("SELECT COUNT(*) FROM markets").fetchone()[0] == len(sample_markets)
    finally:
        conn.close()
