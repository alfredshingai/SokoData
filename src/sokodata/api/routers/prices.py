"""Price series endpoints."""

from datetime import date as Date

from fastapi import APIRouter, HTTPException, Query, Request

from sokodata.api.schemas import PricePoint

router = APIRouter(tags=["prices"])

SELECT_PRICE = """
    SELECT p.date, p.market_id, m.market, m.admin1, p.commodity_id, p.commodity,
           p.unit, p.priceflag, p.pricetype, p.currency, p.price, p.usdprice
    FROM prices p JOIN markets m ON m.market_id = p.market_id
"""


def _require_market(conn, market_id: int) -> None:
    row = conn.execute("SELECT 1 FROM markets WHERE market_id = ?", (market_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail=f"market {market_id} not found")


def _require_commodity(df, commodity_id: int) -> None:
    if commodity_id not in set(df["commodity_id"].dropna().unique()):
        raise HTTPException(status_code=404, detail=f"commodity {commodity_id} not found")


@router.get("/prices", response_model=list[PricePoint])
def price_series(
    request: Request,
    market_id: int | None = Query(default=None),
    commodity_id: int | None = Query(default=None),
    start: Date | None = Query(default=None, description="Inclusive start date (YYYY-MM-DD)"),
    end: Date | None = Query(default=None, description="Inclusive end date (YYYY-MM-DD)"),
    priceflag: str | None = Query(default=None, pattern="^(actual|aggregate)$"),
    limit: int = Query(default=500, ge=1, le=5000),
    offset: int = Query(default=0, ge=0),
):
    """Price observations, oldest first. Combine filters as needed."""
    clauses, params = [], []
    if market_id is not None:
        _require_market(request.app.state.conn, market_id)
        clauses.append("p.market_id = ?")
        params.append(market_id)
    if commodity_id is not None:
        _require_commodity(request.app.state.prices, commodity_id)
        clauses.append("p.commodity_id = ?")
        params.append(commodity_id)
    if start:
        clauses.append("p.date >= ?")
        params.append(start.isoformat())
    if end:
        clauses.append("p.date <= ?")
        params.append(end.isoformat())
    if priceflag:
        clauses.append("p.priceflag = ?")
        params.append(priceflag)

    sql = SELECT_PRICE
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    sql += " ORDER BY p.date LIMIT ? OFFSET ?"
    params += [limit, offset]

    rows = request.app.state.conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


@router.get("/prices/latest", response_model=list[PricePoint])
def latest_prices(
    request: Request,
    commodity_id: int | None = Query(default=None, description="Omit for all commodities"),
    market_id: int | None = Query(default=None),
    limit: int = Query(default=500, ge=1, le=2000),
):
    """Most recent observation per market (per commodity when unspecified)."""
    df = request.app.state.prices
    if commodity_id is not None:
        _require_commodity(df, commodity_id)
    if market_id is not None:
        _require_market(request.app.state.conn, market_id)

    sub = df
    if commodity_id is not None:
        sub = sub[sub["commodity_id"] == commodity_id]
    if market_id is not None:
        sub = sub[sub["market_id"] == market_id]
    if sub.empty:
        return []

    idx = sub.groupby(["market_id", "commodity_id"])["date"].idxmax()
    latest = sub.loc[idx].sort_values(["commodity", "market"]).head(limit)
    return [
        {
            "date": r.date.date(),
            "market_id": int(r.market_id),
            "market": r.market,
            "commodity_id": int(r.commodity_id),
            "commodity": r.commodity,
            "unit": r.unit,
            "priceflag": r.priceflag,
            "pricetype": r.pricetype,
            "currency": r.currency,
            "price": float(r.price),
            "usdprice": None if r.usdprice != r.usdprice else float(r.usdprice),
        }
        for r in latest.itertuples(index=False)
    ]
