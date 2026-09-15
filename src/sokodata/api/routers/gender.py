"""Gender endpoints."""

from fastapi import APIRouter, Query, Request

router = APIRouter(tags=["gender"])


@router.get("/gender/annual")
def gender_annual(request: Request, limit: int = Query(default=100, ge=1, le=500), offset: int = Query(default=0, ge=0)):
    sql = "SELECT date, women_parliament_pct, female_lfpr_pct, primary_parity_index, maternal_mortality_per_100k, source FROM gender_annual ORDER BY date DESC LIMIT ? OFFSET ?"
    try:
        rows = request.app.state.conn.execute(sql, (limit, offset)).fetchall()
    except Exception:
        return []
    return [dict(r) for r in rows]
