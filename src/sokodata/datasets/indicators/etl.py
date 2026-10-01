"""Indicators ETL: World Bank WDI + UNSD SDG -> SQLite."""

import argparse
import logging
from pathlib import Path

from sokodata.config import DB_PATH, RAW_DIR
from sokodata.datasets.indicators.clean import clean_annual
from sokodata.datasets.indicators.fetch import fetch_indicators_all
from sokodata.datasets.indicators.store import connect, init_schema, load_annual

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
log = logging.getLogger(__name__)


def run_etl(data_dir: Path = RAW_DIR, db_path: Path = DB_PATH, *, country: str = "ZW") -> dict[str, int]:
    raw = fetch_indicators_all(country=country, raw_dir=data_dir)
    annual = clean_annual(raw["annual"])
    conn = connect(db_path)
    try:
        counts = load_annual(conn, annual)
    finally:
        conn.close()
    log.info("indicators loaded %s into %s", counts, db_path)
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description="SokoData indicators ETL")
    parser.add_argument("--data-dir", type=Path, default=RAW_DIR)
    parser.add_argument("--db", type=Path, default=DB_PATH)
    parser.add_argument("--country", default="ZW", help="Country ISO3 code")
    args = parser.parse_args()
    run_etl(args.data_dir, args.db, country=args.country)


if __name__ == "__main__":
    main()