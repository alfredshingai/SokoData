"""Geospatial endpoints."""

from fastapi import APIRouter, Request

router = APIRouter(tags=["geospatial"])


@router.get("/geospatial/boundaries")
def geospatial_boundaries(request: Request):
    sql = "SELECT name, format, url, source FROM geospatial_metadata ORDER BY name"
    try:
        rows = request.app.state.conn.execute(sql).fetchall()
    except Exception:
        return []
    return [dict(r) for r in rows]


@router.get("/geospatial/markets/geojson")
def markets_geojson(request: Request):
    """Return market locations as GeoJSON FeatureCollection (from markets table)."""
    try:
        rows = request.app.state.conn.execute("SELECT market_id, market, admin1, admin2, latitude, longitude FROM markets WHERE latitude IS NOT NULL AND longitude IS NOT NULL").fetchall()
    except Exception:
        return {"type": "FeatureCollection", "features": []}
    features = []
    for r in rows:
        features.append({
            "type": "Feature",
            "properties": {"market_id": r["market_id"], "market": r["market"], "admin1": r["admin1"], "admin2": r["admin2"]},
            "geometry": {"type": "Point", "coordinates": [r["longitude"], r["latitude"]]},
        })
    return {"type": "FeatureCollection", "features": features}
