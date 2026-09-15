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
    parser.add_argument("--only", action="append", choices=["markets", "economy", "climate", "demographics", "agriculture", "health", "education", "energy", "water", "transport", "mining", "governance", "trade", "labour", "environment", "poverty", "ict", "finance", "tourism", "aid", "gender", "geospatial"], default=None, help="run only these datasets (repeatable)")
    parser.add_argument("--skip-fetch", action="store_true", help="reuse already-downloaded files for markets")
    parser.add_argument("--climate-admin1", nargs="*", default=None)
    parser.add_argument("--climate-start", default=None)
    args = parser.parse_args()

    only = set(args.only) if args.only else {"markets", "economy", "climate", "demographics", "agriculture", "health", "education", "energy", "water", "transport", "mining", "governance", "trade", "labour", "environment", "poverty", "ict", "finance", "tourism", "aid", "gender", "geospatial"}

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
    if "water" in only:
        try:
            from sokodata.datasets.water.etl import run_etl as run_water

            run_water(args.data_dir, args.db)
        except Exception as e:
            log.warning("water ETL failed (commons continues): %s", e)
    if "transport" in only:
        try:
            from sokodata.datasets.transport.etl import run_etl as run_transport

            run_transport(args.data_dir, args.db)
        except Exception as e:
            log.warning("transport ETL failed (commons continues): %s", e)
    if "mining" in only:
        try:
            from sokodata.datasets.mining.etl import run_etl as run_mining

            run_mining(args.data_dir, args.db)
        except Exception as e:
            log.warning("mining ETL failed (commons continues): %s", e)
    if "governance" in only:
        try:
            from sokodata.datasets.governance.etl import run_etl as run_gov

            run_gov(args.data_dir, args.db)
        except Exception as e:
            log.warning("governance ETL failed (commons continues): %s", e)
    if "trade" in only:
        try:
            from sokodata.datasets.trade.etl import run_etl as run_trade

            run_trade(args.data_dir, args.db)
        except Exception as e:
            log.warning("trade ETL failed (commons continues): %s", e)
    if "labour" in only:
        try:
            from sokodata.datasets.labour.etl import run_etl as run_labour

            run_labour(args.data_dir, args.db)
        except Exception as e:
            log.warning("labour ETL failed (commons continues): %s", e)
    if "environment" in only:
        try:
            from sokodata.datasets.environment.etl import run_etl as run_env

            run_env(args.data_dir, args.db)
        except Exception as e:
            log.warning("environment ETL failed (commons continues): %s", e)
    if "poverty" in only:
        try:
            from sokodata.datasets.poverty.etl import run_etl as run_pov

            run_pov(args.data_dir, args.db)
        except Exception as e:
            log.warning("poverty ETL failed (commons continues): %s", e)
    if "ict" in only:
        try:
            from sokodata.datasets.ict.etl import run_etl as run_ict

            run_ict(args.data_dir, args.db)
        except Exception as e:
            log.warning("ict ETL failed (commons continues): %s", e)
    if "finance" in only:
        try:
            from sokodata.datasets.finance.etl import run_etl as run_finance

            run_finance(args.data_dir, args.db)
        except Exception as e:
            log.warning("finance ETL failed (commons continues): %s", e)
    if "tourism" in only:
        try:
            from sokodata.datasets.tourism.etl import run_etl as run_tourism

            run_tourism(args.data_dir, args.db)
        except Exception as e:
            log.warning("tourism ETL failed (commons continues): %s", e)
    if "aid" in only:
        try:
            from sokodata.datasets.aid.etl import run_etl as run_aid

            run_aid(args.data_dir, args.db)
        except Exception as e:
            log.warning("aid ETL failed (commons continues): %s", e)
    if "gender" in only:
        try:
            from sokodata.datasets.gender.etl import run_etl as run_gender

            run_gender(args.data_dir, args.db)
        except Exception as e:
            log.warning("gender ETL failed (commons continues): %s", e)
    if "geospatial" in only:
        try:
            from sokodata.datasets.geospatial.etl import run_etl as run_geo

            run_geo(args.data_dir, args.db)
        except Exception as e:
            log.warning("geospatial ETL failed (commons continues): %s", e)

    log.info("commons ETL done: %s", only)


if __name__ == "__main__":
    main()
