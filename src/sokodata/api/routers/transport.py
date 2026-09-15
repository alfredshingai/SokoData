"""Transport endpoints."""

from fastapi import APIRouter, Query, Request

router = APIRouter(tags=["transport"])


@router.get("/transport/annual")
def transport_annual(request: Request, limit: int = Query(default=100, ge=1, le=500), offset: int = Query(default=0, ge=0)):
    sql = "SELECT date, air_departures, rail_km, road_km, internet_use_pct, source FROM transport_annual ORDER BY date DESC LIMIT ? OFFSET ?"
    try:
        rows = request.app.state.conn.execute(sql, (limit, offset)).fetchall()
    except Exception:
        return []
    return [dict(r) for r in rows]
