"""Energy endpoints."""

from fastapi import APIRouter, Query, Request

router = APIRouter(tags=["energy"])


@router.get("/energy/annual")
def energy_annual(request: Request, limit: int = Query(default=100, ge=1, le=500), offset: int = Query(default=0, ge=0)):
    sql = "SELECT date, elec_access_pct, elec_use_kwh_pc, energy_imports_pct, renewable_pct, source FROM energy_annual ORDER BY date DESC LIMIT ? OFFSET ?"
    try:
        rows = request.app.state.conn.execute(sql, (limit, offset)).fetchall()
    except Exception:
        return []
    return [dict(r) for r in rows]
