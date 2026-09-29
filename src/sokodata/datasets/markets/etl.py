"""ETL entry point: fetch raw CSVs, clean, load into SQLite.

Usage:
    python -m sokodata.datasets.markets.etl --country ZW
    python -m sokodata.datasets.markets.etl --country KE
    python -m sokodata.datasets.markets.etl --skip-fetch
"""

import argparse
import logging
from pathlib import Path

import pandas as pd

from sokodata.config import DB_PATH, RAW_DIR
from sokodata.datasets.markets.clean import clean_markets, clean_prices
from sokodata.datasets.markets.fetch import fetch_raw
from sokodata.datasets.markets.store import connect, load_tables

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
log = logging.getLogger(__name__)


def run_etl(data_dir: Path, db_path: Path, *, skip_fetch: bool = False, country: str = "ZW") -> tuple[int, int]:
    if skip_fetch:
        prices_path = data_dir / f"wfp_food_prices_{country.lower()}.csv"
        markets_path = data_dir / f"wfp_markets_{country.lower()}.csv"
        if not prices_path.exists() or not markets_path.exists():
            raise FileNotFoundError(f"raw files not found in {data_dir}; run without --skip-fetch")
    else:
        prices_path, markets_path = fetch_raw(data_dir, country)

    # Handle empty files (e.g., country without WFP data on HDX)
    try:
        raw_prices = pd.read_csv(prices_path)
    except pd.errors.EmptyDataError:
        raw_prices = pd.DataFrame()
        log.warning("Prices file empty for %s, skipping markets ETL", country)
        return 0, 0

    try:
        raw_markets = pd.read_csv(markets_path)
    except pd.errors.EmptyDataError:
        raw_markets = pd.DataFrame()
        log.warning("Markets file empty for %s, skipping markets ETL", country)
        return 0, 0
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
    parser.add_argument("--country", default="ZW", help="country ISO3 code (ZW, KE, etc.)")
    args = parser.parse_args()
    run_etl(args.data_dir, args.db, skip_fetch=args.skip_fetch, country=args.country)


if __name__ == "__main__":
    main()