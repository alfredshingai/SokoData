"""Governance endpoints."""

from fastapi import APIRouter, Query, Request

router = APIRouter(tags=["governance"])


@router.get("/governance/annual")
def governance_annual(request: Request, limit: int = Query(default=100, ge=1, le=500), offset: int = Query(default=0, ge=0)):
    sql = "SELECT date, property_rights_cpia, transparency_cpia, women_parliament_pct, military_xpd_pct_gdp, gov_debt_pct_gdp, source FROM governance_annual ORDER BY date DESC LIMIT ? OFFSET ?"
    try:
        rows = request.app.state.conn.execute(sql, (limit, offset)).fetchall()
    except Exception:
        return []
    return [dict(r) for r in rows]
