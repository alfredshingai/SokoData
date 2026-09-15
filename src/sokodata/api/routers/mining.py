"""Mining endpoints."""

from fastapi import APIRouter, Query, Request

router = APIRouter(tags=["mining"])


@router.get("/mining/annual")
def mining_annual(request: Request, limit: int = Query(default=100, ge=1, le=500), offset: int = Query(default=0, ge=0)):
    sql = "SELECT date, mineral_rents_pct_gdp, ore_metal_exports_pct, fuel_exports_pct, source FROM mining_annual ORDER BY date DESC LIMIT ? OFFSET ?"
    try:
        rows = request.app.state.conn.execute(sql, (limit, offset)).fetchall()
    except Exception:
        return []
    return [dict(r) for r in rows]
