"""Geospatial ETL: HDX COD-AB boundaries -> SQLite + GeoJSON on disk."""

import argparse
import logging
from pathlib import Path

from sokodata.config import DB_PATH, RAW_DIR
from sokodata.datasets.geospatial.clean import clean_metadata
from sokodata.datasets.geospatial.fetch import fetch_admin_boundaries, fetch_geospatial_all
from sokodata.datasets.geospatial.store import connect, load_tables

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
log = logging.getLogger(__name__)


def run_etl(data_dir: Path = RAW_DIR, db_path: Path = DB_PATH) -> dict[str, int]:
    raw = fetch_geospatial_all(data_dir)
    meta = clean_metadata(raw["metadata"])
    # also download GeoJSON files to disk (best-effort)
    try:
        fetch_admin_boundaries(data_dir, level=1)
        fetch_admin_boundaries(data_dir, level=2)
    except Exception as e:
        log.warning("GeoJSON download best-effort failed: %s", e)
    conn = connect(db_path)
    try:
        counts = load_tables(conn, meta)
    finally:
        conn.close()
    log.info("geospatial loaded %s into %s", counts, db_path)
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description="SokoData geospatial ETL")
    parser.add_argument("--data-dir", type=Path, default=RAW_DIR)
    parser.add_argument("--db", type=Path, default=DB_PATH)
    args = parser.parse_args()
    run_etl(args.data_dir, args.db)


if __name__ == "__main__":
    main()
