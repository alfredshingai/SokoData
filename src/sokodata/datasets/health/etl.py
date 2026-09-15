"""Health ETL: World Bank + MoHCC scrape -> SQLite."""

import argparse
import logging
from pathlib import Path

from sokodata.config import DB_PATH, RAW_DIR
from sokodata.datasets.health.clean import clean_annual
from sokodata.datasets.health.fetch import fetch_health_all
from sokodata.datasets.health.store import connect, load_tables

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
log = logging.getLogger(__name__)


def run_etl(data_dir: Path = RAW_DIR, db_path: Path = DB_PATH) -> dict[str, int]:
    raw = fetch_health_all(data_dir)
    annual = clean_annual(raw["annual"])
    conn = connect(db_path)
    try:
        counts = load_tables(conn, annual)
    finally:
        conn.close()
    log.info("health loaded %s into %s", counts, db_path)
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description="SokoData health ETL")
    parser.add_argument("--data-dir", type=Path, default=RAW_DIR)
    parser.add_argument("--db", type=Path, default=DB_PATH)
    args = parser.parse_args()
    run_etl(args.data_dir, args.db)


if __name__ == "__main__":
    main()
