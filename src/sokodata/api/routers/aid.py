"""Aid endpoints."""

from fastapi import APIRouter, Query, Request

router = APIRouter(tags=["aid"])


@router.get("/aid/annual")
def aid_annual(request: Request, limit: int = Query(default=100, ge=1, le=500), offset: int = Query(default=0, ge=0)):
    sql = "SELECT date, net_oda_usd, oda_pct_gni, oda_per_capita_usd, source FROM aid_annual ORDER BY date DESC LIMIT ? OFFSET ?"
    try:
        rows = request.app.state.conn.execute(sql, (limit, offset)).fetchall()
    except Exception:
        return []
    return [dict(r) for r in rows]
