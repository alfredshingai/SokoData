"""ICT endpoints."""

from fastapi import APIRouter, Query, Request

router = APIRouter(tags=["ict"])


@router.get("/ict/annual")
def ict_annual(request: Request, limit: int = Query(default=100, ge=1, le=500), offset: int = Query(default=0, ge=0)):
    sql = "SELECT date, internet_users_pct, cell_subs_per_100, fixed_broadband_per_100, tel_lines_per_100, source FROM ict_annual ORDER BY date DESC LIMIT ? OFFSET ?"
    try:
        rows = request.app.state.conn.execute(sql, (limit, offset)).fetchall()
    except Exception:
        return []
    return [dict(r) for r in rows]
