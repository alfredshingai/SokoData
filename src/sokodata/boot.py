"""Render boot: serve the API immediately, rebuild the warehouse in the background.

The free-tier disk is ephemeral, so every boot starts with an empty warehouse.
Blocking on the full ETL before serving meant a slow or failed dataset kept
the API down entirely (the Oct 2026 outage). Instead: create an empty schema,
start uvicorn, and refresh the ETL in a daemon thread; the app picks up the
fresh data when it lands.
"""

import logging
import os
import threading

import uvicorn

from sokodata.config import DB_PATH
from sokodata.etl_run import DATASETS, run_selected

log = logging.getLogger(__name__)


def refresh_warehouse(app) -> tuple[int, dict[str, str]]:
    """Run the full commons ETL, then point the app at the fresh data."""
    ran, failures = run_selected(set(DATASETS), ["ZW"])
    if failures:
        log.warning("boot ETL summary: %d ok, %d FAILED: %s", ran, len(failures), failures)
    else:
        log.info("boot ETL done: %d datasets, no failures", ran)
    try:
        app.state.prices = app.state.refresher()
        log.info("reloaded %d price rows into the running app", len(app.state.prices))
    except Exception as e:
        log.warning("could not reload prices after ETL: %s", e)
    return ran, failures


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    from sokodata.api.main import app, load_prices_frame
    from sokodata.datasets.markets.store import connect, init_schema

    app.state.refresher = lambda: load_prices_frame(app.state.conn)

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = connect(DB_PATH)
    try:
        init_schema(conn)
    finally:
        conn.close()

    thread = threading.Thread(target=refresh_warehouse, args=(app,), daemon=True, name="etl")
    thread.start()

    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8000")), reload=False)


if __name__ == "__main__":
    main()
