"""Education endpoints."""

from fastapi import APIRouter, Query, Request

router = APIRouter(tags=["education"])


@router.get("/education/annual")
def edu_annual(request: Request, limit: int = Query(default=100, ge=1, le=500), offset: int = Query(default=0, ge=0)):
    sql = "SELECT date, primary_ner_pct, secondary_ner_pct, adult_literacy_pct, primary_completion_pct, source FROM education_annual ORDER BY date DESC LIMIT ? OFFSET ?"
    try:
        rows = request.app.state.conn.execute(sql, (limit, offset)).fetchall()
    except Exception:
        return []
    return [dict(r) for r in rows]
