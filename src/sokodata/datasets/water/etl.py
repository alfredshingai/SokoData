"""Water ETL: World Bank + ZINWA scrape -> SQLite."""

import argparse
import logging
from pathlib import Path

from sokodata.config import DB_PATH, RAW_DIR
from sokodata.datasets.water.clean import clean_annual
from sokodata.datasets.water.fetch import fetch_water_all
from sokodata.datasets.water.store import connect, load_tables

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
log = logging.getLogger(__name__)


def run_etl(data_dir: Path = RAW_DIR, db_path: Path = DB_PATH) -> dict[str, int]:
    raw = fetch_water_all(data_dir)
    annual = clean_annual(raw["annual"])
    conn = connect(db_path)
    try:
        counts = load_tables(conn, annual)
    finally:
        conn.close()
    log.info("water loaded %s into %s", counts, db_path)
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description="SokoData water ETL")
    parser.add_argument("--data-dir", type=Path, default=RAW_DIR)
    parser.add_argument("--db", type=Path, default=DB_PATH)
    args = parser.parse_args()
    run_etl(args.data_dir, args.db)


if __name__ == "__main__":
    main()
