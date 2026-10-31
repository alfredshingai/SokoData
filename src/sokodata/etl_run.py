"""Unified ETL for the SokoData commons - runs datasets per country.

Usage:
    python -m sokodata.etl_run                        # all datasets, Zimbabwe
    python -m sokodata.etl_run --country KE           # all datasets, Kenya
    python -m sokodata.etl_run --only markets --country KE
    python -m sokodata.etl_run --countries ZW,KE,MW --only markets
    python -m sokodata.etl_run --all-countries        # markets ETL for every configured country
    python -m sokodata.etl_run --skip-fetch           # reuse raw CSVs (markets only)
"""

import argparse
import importlib
import logging
import sys
from pathlib import Path

from sokodata.config import COUNTRIES, DB_PATH, RAW_DIR

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
log = logging.getLogger(__name__)

DATASETS = [
    "markets", "economy", "climate", "demographics", "agriculture", "health",
    "education", "energy", "water", "transport", "mining", "governance", "trade",
    "labour", "environment", "poverty", "ict", "finance", "tourism", "aid",
    "gender", "geospatial", "indicators",
]


def _run_one(
    name: str,
    *,
    data_dir: Path,
    db: Path,
    country: str,
    skip_fetch: bool = False,
    climate_admin1: list[str] | None = None,
    climate_start: str | None = None,
) -> dict:
    if name == "markets":
        from sokodata.datasets.markets.etl import run_etl

        return run_etl(data_dir, db, skip_fetch=skip_fetch, country=country)
    if name == "climate":
        from sokodata.datasets.climate.etl import run_etl

        return run_etl(
            data_dir,
            db,
            country=country,
            admin1_list=climate_admin1,
            start_date=climate_start,
        )
    module = importlib.import_module(f"sokodata.datasets.{name}.etl")
    return module.run_etl(data_dir, db, country=country)


def run_selected(
    datasets: set[str],
    countries: list[str],
    *,
    data_dir: Path = RAW_DIR,
    db: Path = DB_PATH,
    skip_fetch: bool = False,
    climate_admin1: list[str] | None = None,
    climate_start: str | None = None,
) -> tuple[int, dict[str, str]]:
    """Run the given datasets for the given countries.

    Returns (runs_ok, failures) where failures maps "dataset/country" to the
    error. A failing dataset never raises; callers decide the exit code.
    """
    failures: dict[str, str] = {}
    ran = 0
    for country in countries:
        for name in DATASETS:
            if name not in datasets:
                continue
            try:
                _run_one(
                    name,
                    data_dir=data_dir,
                    db=db,
                    country=country,
                    skip_fetch=skip_fetch,
                    climate_admin1=climate_admin1,
                    climate_start=climate_start,
                )
                ran += 1
            except Exception as e:
                failures[f"{name}/{country}"] = str(e)
                log.warning("%s ETL failed for %s (commons continues): %s", name, country, e)
    return ran, failures


def main() -> int:
    parser = argparse.ArgumentParser(description="SokoData commons ETL")
    parser.add_argument("--data-dir", type=Path, default=RAW_DIR)
    parser.add_argument("--db", type=Path, default=DB_PATH)
    parser.add_argument("--country", default="ZW", help="single country ISO2 code")
    parser.add_argument(
        "--countries",
        default=None,
        help="comma-separated country ISO2 codes; runs the markets ETL per country unless --only",
    )
    parser.add_argument(
        "--all-countries",
        action="store_true",
        help="run the markets ETL for every configured country",
    )
    parser.add_argument("--only", action="append", choices=DATASETS, default=None)
    parser.add_argument(
        "--skip-fetch", action="store_true", help="reuse already-downloaded files for markets"
    )
    parser.add_argument("--climate-admin1", nargs="*", default=None)
    parser.add_argument("--climate-start", default=None)
    parser.add_argument(
        "--strict",
        action="store_true",
        help="exit non-zero if any dataset fails (default: only markets failures are fatal)",
    )
    args = parser.parse_args()

    if args.all_countries:
        countries = sorted(COUNTRIES)
        datasets = set(args.only) if args.only else {"markets"}
    elif args.countries:
        countries = [c.strip().upper() for c in args.countries.split(",") if c.strip()]
        datasets = set(args.only) if args.only else {"markets"}
    else:
        countries = [args.country.upper()]
        datasets = set(args.only) if args.only else set(DATASETS)

    ran, failures = run_selected(
        datasets,
        countries,
        data_dir=args.data_dir,
        db=args.db,
        skip_fetch=args.skip_fetch,
        climate_admin1=args.climate_admin1,
        climate_start=args.climate_start,
    )

    if failures:
        log.warning("commons ETL summary: %d ok, %d FAILED: %s", ran, len(failures), failures)
    else:
        log.info("commons ETL done: %d runs, no failures (countries=%s)", ran, countries)

    markets_broken = any(k.startswith("markets/") for k in failures)
    if markets_broken or (args.strict and failures):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
