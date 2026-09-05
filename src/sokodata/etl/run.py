"""ETL entry point: fetch raw CSVs, clean, load into SQLite.

Usage:
    python -m sokodata.etl                 # fetch from HDX + load
    python -m sokodata.etl --skip-fetch    # re-load from files already in data/raw
"""

import argparse
import logging
from pathlib import Path

import pandas as pd

from sokodata.config import DB_PATH, RAW_DIR
from sokodata.etl.clean import clean_markets, clean_prices
from sokodata.etl.fetch import fetch_raw
from sokodata.etl.store import connect, load_tables

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
log = logging.getLogger(__name__)


def run_etl(data_dir: Path, db_path: Path, *, skip_fetch: bool = False) -> tuple[int, int]:
    if skip_fetch:
        prices_path = data_dir / "wfp_food_prices_zwe.csv"
        markets_path = data_dir / "wfp_markets_zwe.csv"
        if not prices_path.exists() or not markets_path.exists():
            raise FileNotFoundError(f"raw files not found in {data_dir}; run without --skip-fetch")
    else:
        prices_path, markets_path = fetch_raw(data_dir)

    raw_prices = pd.read_csv(prices_path)
    raw_markets = pd.read_csv(markets_path)
    prices = clean_prices(raw_prices)
    markets = clean_markets(raw_markets)

    conn = connect(db_path)
    try:
        n_prices, n_markets = load_tables(conn, prices, markets)
    finally:
        conn.close()
    log.info("loaded %d price rows and %d markets into %s", n_prices, n_markets, db_path)
    return n_prices, n_markets


def main() -> None:
    parser = argparse.ArgumentParser(description="SokoData ETL: HDX -> SQLite")
    parser.add_argument("--data-dir", type=Path, default=RAW_DIR, help="raw data directory")
    parser.add_argument("--db", type=Path, default=DB_PATH, help="output SQLite path")
    parser.add_argument("--skip-fetch", action="store_true", help="reuse already-downloaded CSVs")
    args = parser.parse_args()
    run_etl(args.data_dir, args.db, skip_fetch=args.skip_fetch)


if __name__ == "__main__":
    main()
