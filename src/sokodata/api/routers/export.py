"""Data export endpoints for CSV, Parquet, GeoJSON formats."""

import io
import logging
from datetime import date as Date
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse

from sokodata.core.auth import get_auth_context
from sokodata.datasets.markets.store import connect as db_connect

router = APIRouter(tags=["export"], prefix="/v1/export")

logger = logging.getLogger(__name__)

# Dataset to table mapping
DATASET_TABLES = {
    "markets": ("markets", ["market_id", "market", "country", "admin1", "admin2", "latitude", "longitude"]),
    "prices": ("prices", ["date", "market_id", "commodity_id", "commodity", "category", "unit", "priceflag", "pricetype", "currency", "price", "usdprice", "country"]),
    "economy_rates": ("economy_rates", ["date", "rate", "source"]),
    "economy_cpi": ("economy_cpi", ["date", "cpi", "inflation_yoy", "inflation_mom", "source"]),
    "economy_fuel": ("economy_fuel", ["date", "fuel_type", "price", "currency", "source"]),
    "climate_daily": ("climate_daily", ["date", "admin1", "latitude", "longitude", "tmean_c", "tmax_c", "tmin_c", "precip_mm", "source"]),
    "climate_monthly": ("climate_monthly", ["date", "admin1", "latitude", "longitude", "tmean_c", "tmax_c", "tmin_c", "precip_mm", "source"]),
    "demo_annual": ("demo_annual", ["date", "population", "pop_growth_pct", "urban_pct", "source"]),
    "demo_census": ("demo_census", ["admin1", "population", "male", "female", "source"]),
    "agri_annual": ("agri_annual", ["date", "cereal_yield_kg_ha", "agri_gdp_pct", "food_prod_idx", "crop_prod_idx", "source"]),
    "agri_fao_maize": ("agri_fao_maize", ["date", "maize_tonnes", "source"]),
    "health_annual": ("health_annual", ["date", "infant_mort_per_1k", "under5_mort_per_1k", "measles_imm_pct", "health_xpd_pct_gdp", "source"]),
    "education_annual": ("education_annual", ["date", "primary_ner_pct", "secondary_ner_pct", "adult_literacy_pct", "primary_completion_pct", "source"]),
    "energy_annual": ("energy_annual", ["date", "elec_access_pct", "elec_use_kwh_pc", "energy_imports_pct", "renewable_pct", "source"]),
    "water_annual": ("water_annual", ["date", "safe_water_pct", "safe_sanitation_pct", "basic_water_pct", "basic_sanitation_pct", "source"]),
    "transport_annual": ("transport_annual", ["date", "air_departures", "rail_km", "road_km", "internet_use_pct", "source"]),
    "mining_annual": ("mining_annual", ["date", "mineral_rents_pct_gdp", "ore_metal_exports_pct", "fuel_exports_pct", "source"]),
    "governance_annual": ("governance_annual", ["date", "property_rights_cpia", "transparency_cpia", "women_parliament_pct", "military_xpd_pct_gdp", "gov_debt_pct_gdp", "source"]),
    "trade_annual": ("trade_annual", ["date", "exports_pct_gdp", "imports_pct_gdp", "merch_exports_usd", "merch_imports_usd", "source"]),
    "labour_annual": ("labour_annual", ["date", "unemployment_pct", "unemployment_national_pct", "labour_force_participation_pct", "vulnerable_employment_pct", "source"]),
    "environment_annual": ("environment_annual", ["date", "co2_per_capita_t", "forest_pct", "pm25_ug_m3", "forest_km2", "source"]),
    "poverty_annual": ("poverty_annual", ["date", "extreme_poverty_pct", "gini_index", "national_poverty_pct", "bottom40_growth_pct", "source"]),
    "ict_annual": ("ict_annual", ["date", "internet_users_pct", "cell_subs_per_100", "fixed_broadband_per_100", "tel_lines_per_100", "source"]),
    "finance_annual": ("finance_annual", ["date", "domestic_credit_pct_gdp", "remittances_usd", "private_credit_pct_gdp", "accounts_pct", "source"]),
    "tourism_annual": ("tourism_annual", ["date", "tourist_arrivals", "tourism_receipts_usd", "tourism_expenditure_usd", "source"]),
    "aid_annual": ("aid_annual", ["date", "net_oda_usd", "oda_pct_gni", "oda_per_capita_usd", "source"]),
    "gender_annual": ("gender_annual", ["date", "women_parliament_pct", "female_lfpr_pct", "primary_parity_index", "maternal_mortality_per_100k", "source"]),
    "geospatial_metadata": ("geospatial_metadata", ["name", "format", "url", "source"]),
}


@router.get("/datasets")
def list_exportable_datasets():
    """List all datasets available for export."""
    return {
        "datasets": [
            {"id": k, "table": v[0], "columns": v[1]}
            for k, v in DATASET_TABLES.items()
        ]
    }


def _build_query(dataset_id: str, request: Request, country: str | None = None, 
                 start: Date | None = None, end: Date | None = None,
                 limit: int | None = None, offset: int = 0) -> tuple[str, list]:
    """Build SQL query for dataset export."""
    if dataset_id not in DATASET_TABLES:
        raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} not found")
    
    table, columns = DATASET_TABLES[dataset_id]
    cols = ", ".join(columns)
    sql = f"SELECT {cols} FROM {table}"
    params = []
    
    where_clauses = []
    if country and dataset_id in ["markets", "prices"]:
        where_clauses.append("country = ?")
        params.append(country.upper())
    if dataset_id == "prices" and "commodity_id" in request.query_params:
        where_clauses.append("commodity_id = ?")
        params.append(int(request.query_params["commodity_id"]))
    if dataset_id == "prices" and "market_id" in request.query_params:
        where_clauses.append("market_id = ?")
        params.append(int(request.query_params["market_id"]))
    if start:
        where_clauses.append("date >= ?")
        params.append(start.isoformat())
    if end:
        where_clauses.append("date <= ?")
        params.append(end.isoformat())
    if dataset_id in ["climate_daily", "climate_monthly"] and "admin1" in request.query_params:
        where_clauses.append("admin1 = ?")
        params.append(request.query_params["admin1"])
    
    if where_clauses:
        sql += " WHERE " + " AND ".join(where_clauses)
    
    # Add ordering for time-series tables
    if "date" in columns:
        sql += " ORDER BY date"
    
    if limit:
        sql += " LIMIT ?"
        params.append(limit)
    if offset:
        sql += " OFFSET ?"
        params.append(offset)
    
    return sql, params


@router.get("/{dataset_id}")
async def export_dataset(
    dataset_id: str,
    request: Request,
    format: str = Query(default="csv", pattern="^(csv|parquet|geojson)$"),
    country: str | None = Query(default=None, max_length=3, description="Country ISO3 code"),
    start: Date | None = Query(default=None, description="Inclusive start date (YYYY-MM-DD)"),
    end: Date | None = Query(default=None, description="Inclusive end date (YYYY-MM-DD)"),
    limit: int | None = Query(default=None, ge=1, le=1000000, description="Max rows to return"),
    offset: int = Query(default=0, ge=0),
):
    """Export a dataset in CSV, Parquet, or GeoJSON format."""
    
    if dataset_id not in DATASET_TABLES:
        raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} not found")
    
    # Build query
    sql, params = _build_query(dataset_id, Request(scope=request.scope, receive=request._receive), 
                               country, limit, offset)
    
    # Execute query
    conn = connect("data/sokodata.db")
    try:
        df = pd.read_sql(sql, conn, params=params)
    finally:
        conn.close()
    
    if df.empty:
        raise HTTPException(status_code=404, detail="No data found for the given filters")
    
    # Generate filename
    from datetime import datetime
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"sokodata_{dataset_id}_{timestamp}"
    
    if format == "csv":
        output = io.StringIO()
        df.to_csv(output, index=False)
        output.seek(0)
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode()),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}.csv"}
        )
    elif format == "parquet":
        output = io.BytesIO()
        df.to_parquet(output, index=False)
        output.seek(0)
        return StreamingResponse(
            output,
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename={filename}.parquet"}
        )
    elif format == "geojson":
        # Only for datasets with lat/lon
        if "latitude" not in df.columns or "longitude" not in df.columns:
            raise HTTPException(status_code=400, detail="Dataset does not have geospatial coordinates")
        
        features = []
        for _, row in df.iterrows():
            props = {k: v for k, v in row.items() if k not in ["latitude", "longitude"]}
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [row["longitude"], row["latitude"]]
                },
                "properties": props
            })
        
        geojson = {
            "type": "FeatureCollection",
            "features": features
        }
        
        import json
        output = io.BytesIO()
        output.write(json.dumps(geojson).encode())
        output.seek(0)
        return StreamingResponse(
            output,
            media_type="application/geo+json",
            headers={"Content-Disposition": f"attachment; filename={filename}.geojson"}
        )
    
    raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")