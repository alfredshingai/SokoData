"""Water endpoints."""

from fastapi import APIRouter, Query, Request

router = APIRouter(tags=["water"])


@router.get("/water/annual")
def water_annual(request: Request, limit: int = Query(default=100, ge=1, le=500), offset: int = Query(default=0, ge=0)):
    sql = "SELECT date, safe_water_pct, safe_sanitation_pct, basic_water_pct, basic_sanitation_pct, source FROM water_annual ORDER BY date DESC LIMIT ? OFFSET ?"
    try:
        rows = request.app.state.conn.execute(sql, (limit, offset)).fetchall()
    except Exception:
        return []
    return [dict(r) for r in rows]
