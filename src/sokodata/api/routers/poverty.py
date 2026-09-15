"""Poverty endpoints."""

from fastapi import APIRouter, Query, Request

router = APIRouter(tags=["poverty"])


@router.get("/poverty/annual")
def poverty_annual(request: Request, limit: int = Query(default=100, ge=1, le=500), offset: int = Query(default=0, ge=0)):
    sql = "SELECT date, extreme_poverty_pct, gini_index, national_poverty_pct, bottom40_growth_pct, source FROM poverty_annual ORDER BY date DESC LIMIT ? OFFSET ?"
    try:
        rows = request.app.state.conn.execute(sql, (limit, offset)).fetchall()
    except Exception:
        return []
    return [dict(r) for r in rows]
