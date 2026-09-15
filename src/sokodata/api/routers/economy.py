"""Economy endpoints - rates, CPI, fuel."""

from fastapi import APIRouter, Query, Request

router = APIRouter(tags=["economy"])


@router.get("/economy/rates")
def economy_rates(
    request: Request,
    source: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
):
    clauses, params = [], []
    if source:
        clauses.append("source = ?")
        params.append(source)
    sql = "SELECT date, rate, source FROM economy_rates"
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    sql += " ORDER BY date DESC LIMIT ? OFFSET ?"
    params += [limit, offset]
    try:
        rows = request.app.state.conn.execute(sql, params).fetchall()
    except Exception:
        return []  # table not yet created (economy ETL not run)
    return [dict(r) for r in rows]


@router.get("/economy/cpi")
def economy_cpi(
    request: Request,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
):
    sql = "SELECT date, cpi, inflation_yoy, inflation_mom, source FROM economy_cpi ORDER BY date DESC LIMIT ? OFFSET ?"
    try:
        rows = request.app.state.conn.execute(sql, (limit, offset)).fetchall()
    except Exception:
        return []
    return [dict(r) for r in rows]


@router.get("/economy/fuel")
def economy_fuel(
    request: Request,
    fuel_type: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
):
    clauses, params = [], []
    if fuel_type:
        clauses.append("fuel_type = ?")
        params.append(fuel_type)
    sql = "SELECT date, fuel_type, price, currency, source FROM economy_fuel"
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    sql += " ORDER BY date DESC LIMIT ? OFFSET ?"
    params += [limit, offset]
    try:
        rows = request.app.state.conn.execute(sql, params).fetchall()
    except Exception:
        return []
    return [dict(r) for r in rows]
