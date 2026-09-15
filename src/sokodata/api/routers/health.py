"""Health endpoints."""

from fastapi import APIRouter, Query, Request

router = APIRouter(tags=["health"])


@router.get("/health-stats/annual")
def health_annual(request: Request, limit: int = Query(default=100, ge=1, le=500), offset: int = Query(default=0, ge=0)):
    sql = "SELECT date, infant_mort_per_1k, under5_mort_per_1k, measles_imm_pct, health_xpd_pct_gdp, source FROM health_annual ORDER BY date DESC LIMIT ? OFFSET ?"
    try:
        rows = request.app.state.conn.execute(sql, (limit, offset)).fetchall()
    except Exception:
        return []
    return [dict(r) for r in rows]
