"""Climate endpoints - daily and monthly."""

from fastapi import APIRouter, Query, Request

router = APIRouter(tags=["climate"])


@router.get("/climate/daily")
def climate_daily(
    request: Request,
    admin1: str | None = Query(default=None),
    start: str | None = Query(default=None, description="YYYY-MM-DD"),
    end: str | None = Query(default=None),
    limit: int = Query(default=365, ge=1, le=5000),
    offset: int = Query(default=0, ge=0),
):
    clauses, params = [], []
    if admin1:
        clauses.append("admin1 = ?")
        params.append(admin1)
    if start:
        clauses.append("date >= ?")
        params.append(start)
    if end:
        clauses.append("date <= ?")
        params.append(end)
    sql = "SELECT date, admin1, latitude, longitude, tmean_c, tmax_c, tmin_c, precip_mm, source FROM climate_daily"
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    sql += " ORDER BY date DESC LIMIT ? OFFSET ?"
    params += [limit, offset]
    try:
        rows = request.app.state.conn.execute(sql, params).fetchall()
    except Exception:
        return []
    return [dict(r) for r in rows]


@router.get("/climate/monthly")
def climate_monthly(
    request: Request,
    admin1: str | None = Query(default=None),
    limit: int = Query(default=60, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    clauses, params = [], []
    if admin1:
        clauses.append("admin1 = ?")
        params.append(admin1)
    sql = "SELECT date, admin1, latitude, longitude, tmean_c, tmax_c, tmin_c, precip_mm, source FROM climate_monthly"
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    sql += " ORDER BY date DESC LIMIT ? OFFSET ?"
    params += [limit, offset]
    try:
        rows = request.app.state.conn.execute(sql, params).fetchall()
    except Exception:
        return []
    return [dict(r) for r in rows]
