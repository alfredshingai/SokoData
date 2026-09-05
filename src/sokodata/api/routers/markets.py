"""Market reference endpoints."""

from fastapi import APIRouter, Query, Request

from sokodata.api.schemas import Market

router = APIRouter(tags=["markets"])


@router.get("/markets", response_model=list[Market])
def list_markets(
    request: Request,
    q: str | None = Query(default=None, max_length=60, description="Case-insensitive name filter"),
    admin1: str | None = Query(default=None, max_length=60, description="Province filter"),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    """List markets, alphabetically. Filter by name fragment or province."""
    rows = request.app.state.conn.execute(
        "SELECT market_id, market, countryiso3, admin1, admin2, latitude, longitude "
        "FROM markets ORDER BY market"
    ).fetchall()
    items = [dict(r) for r in rows]
    if q:
        ql = q.lower()
        items = [m for m in items if ql in m["market"].lower()]
    if admin1:
        a1 = admin1.lower()
        items = [m for m in items if m["admin1"] and a1 in m["admin1"].lower()]
    return items[offset : offset + limit]


@router.get("/markets/{market_id}", response_model=Market)
def get_market(market_id: int, request: Request):
    """Get one market by ID."""
    row = request.app.state.conn.execute(
        "SELECT market_id, market, countryiso3, admin1, admin2, latitude, longitude "
        "FROM markets WHERE market_id = ?",
        (market_id,),
    ).fetchone()
    if row is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail=f"market {market_id} not found")
    return dict(row)
