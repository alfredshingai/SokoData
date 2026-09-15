"""Agriculture endpoints."""

from fastapi import APIRouter, Query, Request

router = APIRouter(tags=["agriculture"])


@router.get("/agriculture/annual")
def agri_annual(request: Request, limit: int = Query(default=100, ge=1, le=500), offset: int = Query(default=0, ge=0)):
    sql = "SELECT date, cereal_yield_kg_ha, agri_gdp_pct, food_prod_idx, crop_prod_idx, source FROM agri_annual ORDER BY date DESC LIMIT ? OFFSET ?"
    try:
        rows = request.app.state.conn.execute(sql, (limit, offset)).fetchall()
    except Exception:
        return []
    return [dict(r) for r in rows]


@router.get("/agriculture/fao/maize")
def agri_fao_maize(request: Request, limit: int = Query(default=100, ge=1, le=500), offset: int = Query(default=0, ge=0)):
    sql = "SELECT date, maize_tonnes, source FROM agri_fao_maize ORDER BY date DESC LIMIT ? OFFSET ?"
    try:
        rows = request.app.state.conn.execute(sql, (limit, offset)).fetchall()
    except Exception:
        return []
    return [dict(r) for r in rows]
