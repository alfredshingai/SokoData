"""Unified ETL for the SokoData commons - runs all datasets.

Usage:
    python -m sokodata.etl_run              # markets (required) + economy + climate
    python -m sokodata.etl_run --only markets
    python -m sokodata.etl_run --only economy --only climate
    python -m sokodata.etl_run --skip-fetch  # reuse raw CSVs
"""

import argparse
import logging
from pathlib import Path

from sokodata.config import DB_PATH, RAW_DIR

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
log = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="SokoData commons ETL")
    parser.add_argument("--data-dir", type=Path, default=RAW_DIR)
    parser.add_argument("--db", type=Path, default=DB_PATH)
    parser.add_argument("--only", action="append", choices=["markets", "economy", "climate", "demographics", "agriculture", "health", "education", "energy"], default=None, help="run only these datasets (repeatable)")
    parser.add_argument("--skip-fetch", action="store_true", help="reuse already-downloaded files for markets")
    parser.add_argument("--climate-admin1", nargs="*", default=None)
    parser.add_argument("--climate-start", default=None)
    args = parser.parse_args()

    only = set(args.only) if args.only else {"markets", "economy", "climate", "demographics", "agriculture", "health", "education", "energy"}

    if "markets" in only:
        from sokodata.datasets.markets.etl import run_etl as run_markets

        run_markets(args.data_dir, args.db, skip_fetch=args.skip_fetch)
    if "economy" in only:
        try:
            from sokodata.datasets.economy.etl import run_etl as run_economy

            run_economy(args.data_dir, args.db)
        except Exception as e:
            log.warning("economy ETL failed (commons continues): %s", e)
    if "climate" in only:
        try:
            from sokodata.datasets.climate.etl import run_etl as run_climate

            run_climate(args.data_dir, args.db, admin1_list=args.climate_admin1, start_date=args.climate_start)
        except Exception as e:
            log.warning("climate ETL failed (commons continues): %s", e)
    if "demographics" in only:
        try:
            from sokodata.datasets.demographics.etl import run_etl as run_demo

            run_demo(args.data_dir, args.db)
        except Exception as e:
            log.warning("demographics ETL failed (commons continues): %s", e)
    if "agriculture" in only:
        try:
            from sokodata.datasets.agriculture.etl import run_etl as run_agri

            run_agri(args.data_dir, args.db)
        except Exception as e:
            log.warning("agriculture ETL failed (commons continues): %s", e)
    if "health" in only:
        try:
            from sokodata.datasets.health.etl import run_etl as run_health

            run_health(args.data_dir, args.db)
        except Exception as e:
            log.warning("health ETL failed (commons continues): %s", e)
    if "education" in only:
        try:
            from sokodata.datasets.education.etl import run_etl as run_edu

            run_edu(args.data_dir, args.db)
        except Exception as e:
            log.warning("education ETL failed (commons continues): %s", e)
    if "energy" in only:
        try:
            from sokodata.datasets.energy.etl import run_etl as run_energy

            run_energy(args.data_dir, args.db)
        except Exception as e:
            log.warning("energy ETL failed (commons continues): %s", e)

    log.info("commons ETL done: %s", only)


if __name__ == "__main__":
    main()
