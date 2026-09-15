"""Backward-compat shim - use sokodata.datasets.markets.* instead.

This keeps `python -m sokodata.etl.run` and existing tests working
after the commons refactor.
"""

from sokodata.datasets.markets.etl import main, run_etl

__all__ = ["main", "run_etl"]
