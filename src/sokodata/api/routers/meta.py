"""Meta endpoints for platform health and freshness."""

from fastapi import APIRouter, Query, Request

router = APIRouter(tags=["meta"])


@router.get("/meta/freshness")
def freshness(request: Request):
    """Return last update timestamp and row count for each table."""
    conn = request.app.state.conn
    tables = [
        "markets",
        "prices",
        "economy_rates",
        "economy_cpi",
        "economy_fuel",
        "climate_daily",
        "climate_monthly",
        "demo_annual",
        "demo_census",
        "agri_annual",
        "agri_fao_maize",
        "health_annual",
        "education_annual",
        "energy_annual",
        "water_annual",
        "transport_annual",
        "mining_annual",
        "governance_annual",
        "trade_annual",
        "labour_annual",
        "environment_annual",
        "poverty_annual",
        "ict_annual",
        "finance_annual",
        "tourism_annual",
        "aid_annual",
        "gender_annual",
        "geospatial_metadata",
    ]
    result = {}
    for table in tables:
        try:
            # Try to get max date and count
            row = conn.execute(
                f"SELECT MAX(date) as last_date, COUNT(*) as count FROM {table}"
            ).fetchone()
            if row and row["count"] > 0:
                result[table] = {
                    "last_date": row["last_date"],
                    "row_count": row["count"],
                }
            else:
                result[table] = {"last_date": None, "row_count": 0}
        except Exception:
            result[table] = {"last_date": None, "row_count": 0, "error": "table not found or no date column"}
    return result


@router.get("/meta/freshness/summary")
def freshness_summary(request: Request):
    """Return a summary: total rows, tables with data, oldest/newest dates."""
    conn = request.app.state.conn
    tables = [
        "markets",
        "prices",
        "economy_rates",
        "economy_cpi",
        "economy_fuel",
        "climate_daily",
        "climate_monthly",
        "demo_annual",
        "demo_census",
        "agri_annual",
        "agri_fao_maize",
        "health_annual",
        "education_annual",
        "energy_annual",
        "water_annual",
        "transport_annual",
        "mining_annual",
        "governance_annual",
        "trade_annual",
        "labour_annual",
        "environment_annual",
        "poverty_annual",
        "ict_annual",
        "finance_annual",
        "tourism_annual",
        "aid_annual",
        "gender_annual",
        "geospatial_metadata",
    ]
    total_rows = 0
    tables_with_data = 0
    oldest_date = None
    newest_date = None
    for table in tables:
        try:
            row = conn.execute(
                f"SELECT MAX(date) as max_date, MIN(date) as min_date, COUNT(*) as cnt FROM {table}"
            ).fetchone()
            if row and row["cnt"] > 0:
                tables_with_data += 1
                total_rows += row["cnt"]
                if row["min_date"]:
                    if oldest_date is None or row["min_date"] < oldest_date:
                        oldest_date = row["min_date"]
                if row["max_date"]:
                    if newest_date is None or row["max_date"] > newest_date:
                        newest_date = row["max_date"]
        except Exception:
            continue
    return {
        "total_rows": total_rows,
        "tables_with_data": tables_with_data,
        "total_tables": len(tables),
        "oldest_date": oldest_date,
        "newest_date": newest_date,
    }