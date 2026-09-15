"""Environment endpoints."""

from fastapi import APIRouter, Query, Request

router = APIRouter(tags=["environment"])


@router.get("/environment/annual")
def environment_annual(request: Request, limit: int = Query(default=100, ge=1, le=500), offset: int = Query(default=0, ge=0)):
    sql = "SELECT date, co2_per_capita_t, forest_pct, pm25_ug_m3, forest_km2, source FROM environment_annual ORDER BY date DESC LIMIT ? OFFSET ?"
    try:
        rows = request.app.state.conn.execute(sql, (limit, offset)).fetchall()
    except Exception:
        return []
    return [dict(r) for r in rows]
