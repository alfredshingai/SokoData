"""Insight endpoints: price movers and seasonal anomalies."""

from fastapi import APIRouter, Query, Request

from sokodata.analysis import seasonal
from sokodata.api.schemas import Anomaly, Mover

router = APIRouter(tags=["insights"])


@router.get("/insights/movers", response_model=list[Mover])
def movers(
    request: Request,
    window_days: int = Query(default=90, ge=7, le=365),
    limit: int = Query(default=20, ge=1, le=100),
):
    """Largest USD price changes per market/commodity over a trailing window."""
    return seasonal.movers(request.app.state.prices, window_days=window_days, limit=limit)


@router.get("/insights/anomalies", response_model=list[Anomaly])
def anomalies(
    request: Request,
    threshold: float = Query(default=2.0, ge=0.5, le=5),
    limit: int = Query(default=50, ge=1, le=200),
):
    """Latest prices deviating strongly from their 5-year seasonal baseline.

    A z-score of 2 means the current price is two standard deviations above
    (or below) what this market usually sees in this calendar month.
    """
    return seasonal.anomalies(request.app.state.prices, threshold=threshold, limit=limit)
