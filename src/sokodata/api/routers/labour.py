"""Labour endpoints."""

from fastapi import APIRouter, Query, Request

router = APIRouter(tags=["labour"])


@router.get("/labour/annual")
def labour_annual(request: Request, limit: int = Query(default=100, ge=1, le=500), offset: int = Query(default=0, ge=0)):
    sql = "SELECT date, unemployment_pct, unemployment_national_pct, labour_force_participation_pct, vulnerable_employment_pct, source FROM labour_annual ORDER BY date DESC LIMIT ? OFFSET ?"
    try:
        rows = request.app.state.conn.execute(sql, (limit, offset)).fetchall()
    except Exception:
        return []
    return [dict(r) for r in rows]
