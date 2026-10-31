"""CLI entrypoint: ``python -m sokodata.alerts`` sends the Telegram digest."""

import logging

from sokodata.alerts.telegram import run

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    raise SystemExit(run())
