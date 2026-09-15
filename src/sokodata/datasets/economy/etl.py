"""Economy ETL: World Bank API + RBZ/ZERA scraping -> SQLite."""

import argparse
import logging
from pathlib import Path

from sokodata.config import DB_PATH, RAW_DIR
from sokodata.datasets.economy.clean import clean_cpi, clean_fuel, clean_rates
from sokodata.datasets.economy.fetch import fetch_economy_all
from sokodata.datasets.economy.store import connect, load_tables

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
log = logging.getLogger(__name__)


def run_etl(data_dir: Path = RAW_DIR, db_path: Path = DB_PATH) -> dict[str, int]:
    raw = fetch_economy_all(data_dir)
    rates = clean_rates(raw["rates"])
    cpi = clean_cpi(raw["cpi"])
    fuel = clean_fuel(raw["fuel"])

    conn = connect(db_path)
    try:
        counts = load_tables(conn, rates, cpi, fuel)
    finally:
        conn.close()
    log.info("economy loaded %s into %s", counts, db_path)
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description="SokoData economy ETL")
    parser.add_argument("--data-dir", type=Path, default=RAW_DIR)
    parser.add_argument("--db", type=Path, default=DB_PATH)
    args = parser.parse_args()
    run_etl(args.data_dir, args.db)


if __name__ == "__main__":
    main()
