"""Tourism endpoints."""

from fastapi import APIRouter, Query, Request

router = APIRouter(tags=["tourism"])


@router.get("/tourism/annual")
def tourism_annual(request: Request, limit: int = Query(default=100, ge=1, le=500), offset: int = Query(default=0, ge=0)):
    sql = "SELECT date, tourist_arrivals, tourism_receipts_usd, tourism_expenditure_usd, source FROM tourism_annual ORDER BY date DESC LIMIT ? OFFSET ?"
    try:
        rows = request.app.state.conn.execute(sql, (limit, offset)).fetchall()
    except Exception:
        return []
    return [dict(r) for r in rows]
