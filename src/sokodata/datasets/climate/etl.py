"""Climate ETL: Open-Meteo -> SQLite."""

import argparse
import logging
from pathlib import Path

from sokodata.config import DB_PATH, RAW_DIR
from sokodata.datasets.climate.clean import clean_climate, to_monthly
from sokodata.datasets.climate.fetch import fetch_climate_all
from sokodata.datasets.climate.store import connect, load_tables

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
log = logging.getLogger(__name__)


def run_etl(
    data_dir: Path = RAW_DIR,
    db_path: Path = DB_PATH,
    admin1_list: list[str] | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict[str, int]:
    raw = fetch_climate_all(data_dir, admin1_list=admin1_list, start_date=start_date, end_date=end_date)
    daily = clean_climate(raw)
    monthly = to_monthly(daily)

    conn = connect(db_path)
    try:
        counts = load_tables(conn, daily, monthly)
    finally:
        conn.close()
    log.info("climate loaded %s into %s", counts, db_path)
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description="SokoData climate ETL")
    parser.add_argument("--data-dir", type=Path, default=RAW_DIR)
    parser.add_argument("--db", type=Path, default=DB_PATH)
    parser.add_argument("--admin1", nargs="*", default=None, help="limit to admin1 names")
    parser.add_argument("--start", default=None)
    parser.add_argument("--end", default=None)
    args = parser.parse_args()
    run_etl(args.data_dir, args.db, admin1_list=args.admin1, start_date=args.start, end_date=args.end)


if __name__ == "__main__":
    main()
