"""Trade endpoints."""

from fastapi import APIRouter, Query, Request

router = APIRouter(tags=["trade"])


@router.get("/trade/annual")
def trade_annual(request: Request, limit: int = Query(default=100, ge=1, le=500), offset: int = Query(default=0, ge=0)):
    sql = "SELECT date, exports_pct_gdp, imports_pct_gdp, merch_exports_usd, merch_imports_usd, source FROM trade_annual ORDER BY date DESC LIMIT ? OFFSET ?"
    try:
        rows = request.app.state.conn.execute(sql, (limit, offset)).fetchall()
    except Exception:
        return []
    return [dict(r) for r in rows]
