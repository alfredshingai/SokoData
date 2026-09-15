"""Finance endpoints."""

from fastapi import APIRouter, Query, Request

router = APIRouter(tags=["finance"])


@router.get("/finance/annual")
def finance_annual(request: Request, limit: int = Query(default=100, ge=1, le=500), offset: int = Query(default=0, ge=0)):
    sql = "SELECT date, domestic_credit_pct_gdp, remittances_usd, private_credit_pct_gdp, accounts_pct, source FROM finance_annual ORDER BY date DESC LIMIT ? OFFSET ?"
    try:
        rows = request.app.state.conn.execute(sql, (limit, offset)).fetchall()
    except Exception:
        return []
    return [dict(r) for r in rows]
