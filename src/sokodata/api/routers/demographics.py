"""Demographics endpoints."""

from fastapi import APIRouter, Query, Request

router = APIRouter(tags=["demographics"])


@router.get("/demographics/annual")
def demo_annual(
    request: Request,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    sql = "SELECT date, population, pop_growth_pct, urban_pct, source FROM demo_annual ORDER BY date DESC LIMIT ? OFFSET ?"
    try:
        rows = request.app.state.conn.execute(sql, (limit, offset)).fetchall()
    except Exception:
        return []
    return [dict(r) for r in rows]


@router.get("/demographics/census")
def demo_census(
    request: Request,
    admin1: str | None = Query(default=None),
):
    sql = "SELECT admin1, population, male, female, source FROM demo_census"
    params: list = []
    if admin1:
        sql += " WHERE admin1 = ?"
        params.append(admin1)
    sql += " ORDER BY population DESC"
    try:
        rows = request.app.state.conn.execute(sql, params).fetchall()
    except Exception:
        return []
    return [dict(r) for r in rows]
