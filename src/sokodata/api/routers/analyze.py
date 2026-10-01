"""Cross-dataset join/analysis API for the SokoData platform."""

import json
import logging
from datetime import date as Date
from typing import Any

import numpy as np
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse

from sokodata.core.auth import get_auth_context
from sokodata.core.registry import list_datasets
from sokodata.datasets.markets.store import connect as db_connect
from sokodata.datasets.markets.analysis.seasonal import anomalies, movers, seasonal_baseline

router = APIRouter(prefix="/analyze", tags=["analyze"])

logger = logging.getLogger(__name__)

# Known joinable fields across datasets
JOIN_KEYS = {
    "markets": ["country", "admin1"],
    "prices": ["country", "admin1", "date", "market_id"],
    "economy_rates": ["country", "date"],
    "economy_cpi": ["country", "date"],
    "economy_fuel": ["country", "date"],
    "climate_daily": ["country", "admin1", "date"],
    "climate_monthly": ["country", "admin1", "date"],
    "demo_annual": ["country", "date"],
    "demo_census": ["country", "admin1"],
    "agri_annual": ["country", "date"],
    "agri_fao_maize": ["country", "date"],
    "health_annual": ["country", "date"],
    "education_annual": ["country", "date"],
    "energy_annual": ["country", "date"],
    "water_annual": ["country", "date"],
    "transport_annual": ["country", "date"],
    "mining_annual": ["country", "date"],
    "governance_annual": ["country", "date"],
    "trade_annual": ["country", "date"],
    "labour_annual": ["country", "date"],
    "environment_annual": ["country", "date"],
    "poverty_annual": ["country", "date"],
    "ict_annual": ["country", "date"],
    "finance_annual": ["country", "date"],
    "tourism_annual": ["country", "date"],
    "aid_annual": ["country", "date"],
    "gender_annual": ["country", "date"],
    "geospatial_metadata": ["name", "format", "url"],
}

# Default join keys (most common)
DEFAULT_JOIN_KEYS = ["country", "date", "admin1"]


@router.get("/joinable")
def list_joinable_datasets():
    """List all datasets and their joinable fields."""
    return {
        "datasets": [
            {"id": ds, "joinable_fields": JOIN_KEYS.get(ds, [])}
            for ds in JOIN_KEYS.keys()
        ],
        "common_join_keys": DEFAULT_JOIN_KEYS,
    }


def _detect_join_keys(left_df: pd.DataFrame, right_df: pd.DataFrame) -> list[str]:
    """Detect common columns between two dataframes that could be join keys."""
    left_cols = set(left_df.columns)
    right_cols = set(right_df.columns)
    common = left_cols.intersection(right_cols)
    # Prefer standard join keys
    preferred = ["country", "date", "admin1", "admin2", "market_id"]
    return [c for c in preferred if c in common] or list(common)


def _load_table(conn, table: str, country: str | None = None, 
                start: Date | None = None, end: Date | None = None,
                admin1: str | None = None) -> pd.DataFrame:
    """Load a table with optional filters."""
    sql = f"SELECT * FROM {table}"
    params = []
    where = []
    
    # Check if table has country column
    if country:
        # First check if table has country column
        cols = pd.read_sql(f"PRAGMA table_info({table})", conn)["name"].tolist()
        if "country" in cols:
            where.append("country = ?")
            params.append(country.upper())
    
    if start:
        where.append("date >= ?")
        params.append(start.isoformat())
    if end:
        where.append("date <= ?")
        params.append(end.isoformat())
    if admin1:
        where.append("admin1 = ?")
        params.append(admin1)
    
    if where:
        sql += " WHERE " + " AND ".join(where)
    
    # Check if table has date column for ordering
    cols = pd.read_sql(f"PRAGMA table_info({table})", conn)["name"].tolist()
    if "date" in cols:
        sql += " ORDER BY date"
    
    return pd.read_sql(sql, conn, params=params)


@router.get("/joinable")
def list_joinable_datasets():
    """List all datasets and their joinable fields."""
    return {
        "datasets": [
            {"id": ds, "joinable_fields": JOIN_KEYS.get(ds, [])}
            for ds in JOIN_KEYS.keys()
        ],
        "common_join_keys": DEFAULT_JOIN_KEYS,
    }


def _detect_join_keys(left_df: pd.DataFrame, right_df: pd.DataFrame) -> list[str]:
    """Detect common columns between two dataframes that could be join keys."""
    left_cols = set(left_df.columns)
    right_cols = set(right_df.columns)
    common = left_cols.intersection(right_cols)
    # Prefer standard join keys
    preferred = ["country", "date", "admin1", "admin2", "market_id"]
    return [c for c in preferred if c in common] or list(common)


def _load_table(conn, table: str, country: str | None = None, 
                start: Date | None = None, end: Date | None = None,
                admin1: str | None = None) -> pd.DataFrame:
    """Load a table with optional filters."""
    sql = f"SELECT * FROM {table}"
    params = []
    where = []
    
    # Check if table has country column
    if country:
        # First check if table has country column
        cols = pd.read_sql(f"PRAGMA table_info({table})", conn)["name"].tolist()
        if "country" in cols:
            where.append("country = ?")
            params.append(country.upper())
    
    if start:
        where.append("date >= ?")
        params.append(start.isoformat())
    if end:
        where.append("date <= ?")
        params.append(end.isoformat())
    if admin1:
        where.append("admin1 = ?")
        params.append(admin1)
    
    if where:
        sql += " WHERE " + " AND ".join(where)
    
    # Check if table has date column for ordering
    cols = pd.read_sql(f"PRAGMA table_info({table})", conn)["name"].tolist()
    if "date" in cols:
        sql += " ORDER BY date"
    
    return pd.read_sql(sql, conn, params=params)


@router.post("/join")
def join_datasets(
    request: Request,
    left_table: str = Query(..., description="Left table name"),
    right_table: str = Query(..., description="Right table name"),
    left_on: list[str] | None = Query(default=None, description="Left join keys"),
    right_on: list[str] | None = Query(default=None, description="Right join keys"),
    on: list[str] | None = Query(default=None, description="Common join keys"),
    how: str = Query(default="inner", pattern="^(inner|left|right|outer)$"),
    country: str | None = Query(default=None, max_length=3),
    start: Date | None = Query(default=None),
    end: Date | None = Query(default=None),
    admin1: str | None = Query(default=None),
    limit: int | None = Query(default=None, ge=1, le=100000),
    offset: int = Query(default=0, ge=0),
    format: str = Query(default="json", pattern="^(json|csv|parquet)$"),
):
    """Join two datasets on common or specified keys.
    
    Examples:
    - Join prices with climate: left=prices, right=climate_daily, on=["country","admin1","date"]
    - Join markets with economy: left=markets, right=economy_rates, on=["country"]
    - Join climate with agriculture: left=climate_monthly, right=agri_annual, on=["country","date"]
    """
    from sokodata.datasets.markets.store import connect as db_connect
    
    conn = db_connect("data/sokodata.db", read_only=True)
    try:
        # Load left table
        left_df = _load_table(conn, left_table, country=country, start=start, end=end, admin1=admin1)
        if left_df.empty:
            raise HTTPException(status_code=404, detail=f"No data in left table {left_table}")
        
        # Load right table
        right_df = _load_table(conn, right_table, country=country, start=start, end=end, admin1=admin1)
        if right_df.empty:
            raise HTTPException(status_code=404, detail=f"No data in right table {right_table}")
        
        # Determine join keys
        if on:
            join_keys = on
        elif left_on and right_on:
            join_keys = None  # Use left_on/right_on
        else:
            # Auto-detect
            join_keys = _detect_join_keys(left_df, right_df)
            if not join_keys:
                raise HTTPException(status_code=400, detail="No common columns found for join. Specify 'on' parameter.")
        
        # Perform join
        if left_on and right_on:
            joined = pd.merge(left_df, right_df, left_on=left_on, right_on=right_on, how=how)
        else:
            joined = pd.merge(left_df, right_df, on=join_keys, how=how)
        
        # Apply pagination
        if offset:
            joined = joined.iloc[offset:]
        if limit:
            joined = joined.head(limit)
        
        # Format output
        if format == "csv":
            import io
            output = io.StringIO()
            joined.to_csv(output, index=False)
            output.seek(0)
            return StreamingResponse(
                io.BytesIO(output.getvalue().encode()),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=join_{left_table}_{right_table}.csv"}
            )
        elif format == "parquet":
            import io
            output = io.BytesIO()
            joined.to_parquet(output, index=False)
            output.seek(0)
            return StreamingResponse(
                output,
                media_type="application/octet-stream",
                headers={"Content-Disposition": f"attachment; filename=join_{left_table}_{right_table}.parquet"}
            )
        
        return joined.to_dict(orient="records")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Join failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.get("/correlate")
def correlate_datasets(
    table_x: str = Query(..., description="First dataset (x-axis)"),
    column_x: str = Query(..., description="Column in first dataset"),
    table_y: str = Query(..., description="Second dataset (y-axis)"),
    column_y: str = Query(..., description="Column in second dataset"),
    join_on: list[str] = Query(default=["country", "date"], description="Join keys"),
    method: str = Query(default="pearson", pattern="^(pearson|spearman|kendall)$"),
    country: str | None = Query(default=None, max_length=3),
    start: Date | None = Query(default=None),
    end: Date | None = Query(default=None),
    admin1: str | None = Query(default=None),
):
    """Calculate correlation between columns from two joined datasets."""
    from sokodata.datasets.markets.store import connect as db_connect
    
    conn = db_connect("data/sokodata.db", read_only=True)
    try:
        df_x = _load_table(conn, table_x, country=country, start=start, end=end, admin1=admin1)
        df_y = _load_table(conn, table_y, country=country, start=start, end=end, admin1=admin1)
        
        if df_x.empty or df_y.empty:
            raise HTTPException(status_code=404, detail="No data in one or both datasets")
        
        if column_x not in df_x.columns or column_y not in df_y.columns:
            raise HTTPException(status_code=400, detail="Specified columns not found")
        
        # Join on specified keys
        df_joined = pd.merge(df_x[[*join_on, column_x]], df_y[[*join_on, column_y]], 
                            on=join_on, how="inner")
        
        if df_joined.empty:
            raise HTTPException(status_code=404, detail="No overlapping data after join")
        
        # Calculate correlation
        corr = df_joined[column_x].corr(df_joined[column_y], method=method)
        n = len(df_joined)
        
        return {
            "correlation": float(corr) if not pd.isna(corr) else None,
            "method": method,
            "sample_size": int(n),
            "join_keys": join_on,
            "x": {"table": table_x, "column": column_x},
            "y": {"table": table_y, "column": column_y},
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Correlation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.get("/summary")
def join_summary(
    tables: list[str] = Query(..., description="Tables to analyze"),
    country: str | None = Query(default=None, max_length=3),
    start: Date | None = Query(default=None),
    end: Date | None = Query(default=None),
    admin1: str | None = Query(default=None),
):
    """Get summary statistics for potential joins between multiple tables."""
    from sokodata.datasets.markets.store import connect as db_connect
    
    conn = db_connect("data/sokodata.db", read_only=True)
    try:
        results = {}
        for table in tables:
            try:
                df = _load_table(conn, table, country=country, start=start, end=end, admin1=admin1)
                if not df.empty:
                    results[table] = {
                        "rows": len(df),
                        "columns": list(df.columns),
                        "dtypes": {k: str(v) for k, v in df.dtypes.items()},
                        "date_range": {
                            "min": df["date"].min() if "date" in df.columns else None,
                            "max": df["date"].max() if "date" in df.columns else None,
                        } if "date" in df.columns else None,
                        "common_with_others": {},
                    }
                else:
                    results[table] = {"rows": 0, "empty": True}
            except Exception as e:
                results[table] = {"error": str(e)}
        
        # Calculate common columns between pairs
        table_list = list(results.keys())
        for i, t1 in enumerate(table_list):
            for t2 in table_list[i+1:]:
                if "columns" in results[t1] and "columns" in results[t2]:
                    common = set(results[t1]["columns"]).intersection(set(results[t2]["columns"]))
                    results[t1]["common_with_others"][t2] = list(common)
                    results[t2]["common_with_others"][t1] = list(common)
        
        return results
    except Exception as e:
        logger.error(f"Join summary failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.get("/anomalies")
def detect_anomalies(
    table: str = Query(..., description="Table name"),
    column: str = Query(..., description="Column to check for anomalies"),
    threshold: float = Query(default=2.0, description="Z-score threshold for anomaly detection"),
    country: str | None = Query(default=None, max_length=3),
    start: Date | None = Query(default=None),
    end: Date | None = Query(default=None),
    admin1: str | None = Query(default=None),
):
    """Detect anomalies in a single dataset column using robust z-score (MAD-based)."""
    from sokodata.datasets.markets.store import connect as db_connect
    from sokodata.datasets.markets.analysis.seasonal import anomalies
    
    conn = db_connect("data/sokodata.db", read_only=True)
    try:
        df = _load_table(conn, table, country=country, start=start, end=end, admin1=admin1)
        if df.empty:
            raise HTTPException(status_code=404, detail=f"No data in table {table}")
        
        if column not in df.columns:
            raise HTTPException(status_code=400, detail=f"Column {column} not found in table {table}")
        
        # Use the existing anomaly detection from seasonal module
        anomalies = anomalies(df, threshold=threshold)
        
        return {
            "table": table,
            "column": column,
            "threshold": threshold,
            "anomaly_count": len(anomalies),
            "anomalies": anomalies
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Anomaly detection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.get("/anomalies/correlated")
def correlated_anomalies(
    table_x: str = Query(..., description="First dataset"),
    column_x: str = Query(..., description="Column in first dataset"),
    table_y: str = Query(..., description="Second dataset"),
    column_y: str = Query(..., description="Column in second dataset"),
    join_on: list[str] = Query(default=["country", "date"], description="Join keys"),
    threshold: float = Query(default=2.0, description="Z-score threshold for anomaly detection"),
    country: str | None = Query(default=None, max_length=3),
    start: Date | None = Query(default=None),
    end: Date | None = Query(default=None),
    admin1: str | None = Query(default=None),
):
    """Find correlated anomalies between two joined datasets.
    
    Returns anomalies that occur at the same time in both datasets.
    """
    from sokodata.datasets.markets.store import connect as db_connect
    from sokodata.datasets.markets.analysis.seasonal import anomalies
    
    conn = db_connect("data/sokodata.db", read_only=True)
    try:
        df_x = _load_table(conn, table_x, country=country, start=start, end=end, admin1=admin1)
        df_y = _load_table(conn, table_y, country=country, start=start, end=end, admin1=admin1)
        
        if df_x.empty or df_y.empty:
            raise HTTPException(status_code=404, detail="No data in one or both datasets")
        
        if column_x not in df_x.columns or column_y not in df_y.columns:
            raise HTTPException(status_code=400, detail="Specified columns not found")
        
        # Detect anomalies in both datasets
        anomalies_x = anomalies(df_x, threshold=threshold)
        anomalies_y = anomalies(df_y, threshold=threshold)
        
        # Join on keys to find correlated anomalies
        if not anomalies_x.empty and not anomalies_y.empty:
            # Get the anomalous points
            merged_x = df_x[df_x.index.isin(anomalies_x.index)].copy()
            merged_y = df_y[df_y.index.isin(anomalies_y.index)].copy()
            
            # Join on keys
            merged = pd.merge(merged_x, merged_y, on=join_on, how="inner")
        else:
            merged = pd.DataFrame()
        
        return {
            "table_x": table_x,
            "column_x": column_x,
            "table_y": table_y,
            "column_y": column_y,
            "join_keys": join_on,
            "threshold": threshold,
            "anomaly_count_x": len(anomalies_x),
            "anomaly_count_y": len(anomalies_y),
            "correlated_anomaly_count": len(merged),
            "correlated_anomalies": merged.to_dict(orient="records") if not merged.empty else []
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Correlated anomaly detection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.get("/anomalies/pattern")
def anomaly_pattern(
    table: str = Query(..., description="Table name"),
    column: str = Query(..., description="Column to analyze"),
    window: int = Query(default=30, description="Rolling window size for pattern detection"),
    country: str | None = Query(default=None, max_length=3),
    start: Date | None = Query(default=None),
    end: Date | None = Query(default=None),
    admin1: str | None = Query(default=None),
):
    """Detect anomaly patterns (seasonal, trend, level shifts) in a time series."""
    from sokodata.datasets.markets.store import connect as db_connect
    
    conn = db_connect("data/sokodata.db", read_only=True)
    try:
        df = _load_table(conn, table, country=country, start=start, end=end, admin1=admin1)
        if df.empty:
            raise HTTPException(status_code=404, detail=f"No data in table {table}")
        
        if column not in df.columns:
            raise HTTPException(status_code=400, detail=f"Column {column} not found")
        
        # Simple pattern detection using rolling statistics
        series = df.set_index("date")[column].sort_index()
        
        # Rolling mean and std
        rolling_mean = series.rolling(window=window, center=True).mean()
        rolling_std = series.rolling(window=window, center=True).std()
        
        # Z-score
        z_score = (series - rolling_mean) / rolling_std
        
        # Detect anomalies
        anomalies = z_score.abs() > 2.0
        
        # Detect level shifts (rolling mean change)
        mean_diff = rolling_mean.diff().abs()
        level_shifts = mean_diff > mean_diff.quantile(0.95)
        
        # Trend detection (linear regression slope over window)
        def rolling_trend(s):
            if len(s.dropna()) < 3:
                return np.nan
            x = np.arange(len(s))
            y = s.values
            mask = ~np.isnan(y)
            if mask.sum() < 3:
                return np.nan
            slope = np.polyfit(x[mask], y[mask], 1)[0]
            return slope
        
        trend = series.rolling(window=window).apply(rolling_trend, raw=True)
        trend_changes = trend.diff().abs() > trend.diff().abs().quantile(0.95)
        
        return {
            "table": table,
            "column": column,
            "window": window,
            "anomaly_count": int(anomalies.sum()),
            "anomalies": z_score[anomalies].to_dict(),
            "level_shift_count": int(level_shifts.sum()),
            "level_shifts": z_score[level_shifts].to_dict(),
            "trend_change_count": int(trend_changes.sum()),
            "trend_changes": z_score[trend_changes].to_dict(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Anomaly pattern detection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.get("/forecast")
def forecast(
    table: str = Query(..., description="Table name"),
    column: str = Query(..., description="Column to forecast"),
    horizon: int = Query(default=30, ge=1, le=365, description="Forecast horizon (days)"),
    periods: int = Query(default=365, description="Seasonal period (days)"),
    n_harmonics: int = Query(default=3, ge=1, le=10),
    country: str | None = Query(default=None, max_length=3),
    start: Date | None = Query(default=None),
    end: Date | None = Query(default=None),
    admin1: str | None = Query(default=None),
):
    """Forecast future values using harmonic regression seasonal baseline."""
    from sokodata.datasets.markets.store import connect as db_connect
    from sokodata.datasets.markets.analysis.seasonal import seasonal_baseline
    
    conn = db_connect("data/sokodata.db", read_only=True)
    try:
        df = _load_table(conn, table, country=country, start=start, end=end, admin1=admin1)
        if df.empty:
            raise HTTPException(status_code=404, detail=f"No data in table {table}")
        
        if column not in df.columns:
            raise HTTPException(status_code=400, detail=f"Column {column} not found in table {table}")
        
        # Use seasonal baseline for forecasting
        result = seasonal_baseline(
            df, 
            column, 
            date_col="date", 
            periods=365,  # Use 365 for daily data
            n_harmonics=3
        )
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        # Generate forecast for the requested horizon
        forecast_values = result["forecast"][:horizon]
        forecast_dates = result["forecast_dates"][:horizon]
        
        return {
            "table": table,
            "column": column,
            "horizon": horizon,
            "forecast": forecast_values,
            "forecast_dates": forecast_dates,
            "method": "harmonic_regression",
            "model_r_squared": result["r_squared"],
            "periods": result["periods"],
            "n_harmonics": result["n_harmonics"],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Forecast failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()