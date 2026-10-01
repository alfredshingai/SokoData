"""Market analytics on USD-normalized prices.

All functions take a "long" DataFrame with columns
``[date, market_id, market, commodity_id, commodity, usdprice, priceflag]``
and return plain dicts ready for JSON responses.

Why USD: the local-currency column keeps the "ZWL" label across the 2024
ZiG redenomination, so local-currency deltas are meaningless across years.
USD price is the comparable series (WFP computes it from parallel-market
and official rates at observation time).
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler

# Aggregated rows are market-level aggregates published by WFP; use them for
# analytics when present, falling back to actual rows. Keep both otherwise.
FLAG_PRIORITY = {"aggregate": 0, "actual": 1}


def dedupe_flag(df: pd.DataFrame) -> pd.DataFrame:
    """Prefer 'aggregate' rows over 'actual' for the same (date, market, commodity)."""
    out = df.copy()
    out["_flag_rank"] = out["priceflag"].map(FLAG_PRIORITY).fillna(9)
    out = out.sort_values(["date", "market_id", "commodity_id", "_flag_rank"])
    out = out.drop_duplicates(subset=["date", "market_id", "commodity_id"], keep="first")
    return out.drop(columns="_flag_rank")


def movers(
    df: pd.DataFrame,
    *,
    window_days: int = 90,
    limit: int = 20,
    min_baseline: int = 2,
    max_gap_days: int = 400,
) -> list[dict]:
    """Largest USD price changes per (market, commodity) over a trailing window.

    A series qualifies if it has a price inside the window and a price at
    least ``min_baseline`` observations before the window start, no further
    back than ``max_gap_days`` — a change measured across a long reporting
    gap is a data artifact, not a market signal.
    """
    s = dedupe_flag(df)
    s = s.dropna(subset=["usdprice"])
    end = s["date"].max()
    if pd.isna(end):
        return []
    start = end - pd.Timedelta(days=window_days)

    results: list[dict] = []
    for (_mkt, _com), g in s.groupby(["market_id", "commodity_id"]):
        g = g.sort_values("date")
        recent = g[g["date"] > start]
        prior = g[g["date"] <= start]
        if recent.empty or len(prior) < min_baseline:
            continue
        last = recent.iloc[-1]
        prev = prior.iloc[-1]
        if prev["usdprice"] <= 0:
            continue
        if (last["date"] - prev["date"]).days > max_gap_days:
            continue
        pct = (last["usdprice"] - prev["usdprice"]) / prev["usdprice"] * 100
        results.append(
            {
                "market_id": int(_mkt),
                "market": last["market"],
                "commodity_id": int(_com),
                "commodity": last["commodity"],
                "unit": last["unit"],
                "prev_date": prev["date"].date().isoformat(),
                "prev_usd": round(float(prev["usdprice"]), 4),
                "last_date": last["date"].date().isoformat(),
                "last_usd": round(float(last["usdprice"]), 4),
                "pct_change": round(float(pct), 2),
            }
        )

    results.sort(key=lambda r: abs(r["pct_change"]), reverse=True)
    return results[:limit]


def anomalies(
    df: pd.DataFrame,
    *,
    threshold: float = 2.0,
    baseline_months: int = 24,
    min_baseline: int = 6,
    max_staleness_days: int = 90,
    limit: int = 50,
) -> list[dict]:
    """Latest observations deviating strongly from their own recent norm.

    Baseline per (market, commodity): the median of that series' prices over
    the ``baseline_months`` preceding its latest observation. Deviation is a
    robust z-score using the median absolute deviation (MAD), which tolerates
    the outlier-heavy tails of food-price data.

    Series whose latest observation is older than ``max_staleness_days``
    (relative to the dataset's newest date) are skipped — flagging a market
    that stopped reporting a year ago is not actionable.

    Why not calendar-month seasonality: WFP market coverage rotates, so most
    series lack same-month history. A trailing robust baseline works with
    sparse, rotating coverage; seasonal refinement is a roadmap item.
    """
    s = dedupe_flag(df)
    s = s.dropna(subset=["usdprice"])
    if s.empty:
        return []
    newest = s["date"].max()

    results: list[dict] = []
    for (_mkt, _com), g in s.groupby(["market_id", "commodity_id"]):
        g = g.sort_values("date")
        if len(g) < min_baseline + 1:
            continue
        last = g.iloc[-1]
        if (newest - last["date"]).days > max_staleness_days:
            continue
        window_start = last["date"] - pd.DateOffset(months=baseline_months)
        prior = g[(g["date"] >= window_start) & (g["date"] < last["date"])]
        if len(prior) < min_baseline:
            continue

        median = float(prior["usdprice"].median())
        mad = float((prior["usdprice"] - median).abs().median())
        sigma = 1.4826 * mad
        if sigma <= 0:
            continue
        z = (float(last["usdprice"]) - median) / sigma
        if abs(z) >= threshold:
            results.append(
                {
                    "market_id": int(_mkt),
                    "market": last["market"],
                    "commodity_id": int(_com),
                    "commodity": last["commodity"],
                    "unit": last["unit"],
                    "date": last["date"].date().isoformat(),
                    "usdprice": round(float(last["usdprice"]), 4),
                    "recent_median_usd": round(median, 4),
                    "z": round(z, 2),
                    "baseline_points": int(len(prior)),
                }
            )
        results.sort(key=lambda r: abs(r["z"]), reverse=True)
    return results[:limit]


# Crop calendar for major crops (planting/harvest months by region)
CROP_CALENDARS = {
    "maize": {
        "southern_africa": {"planting": [10, 11, 12], "harvest": [4, 5, 6]},
        "eastern_africa": {"planting": [3, 4], "harvest": [8, 9]},
        "western_africa": {"planting": [5, 6], "harvest": [9, 10]},
    },
    "wheat": {
        "southern_africa": {"planting": [5, 6], "harvest": [11, 12]},
        "eastern_africa": {"planting": [10, 11], "harvest": [3, 4]},
    },
    "rice": {
        "eastern_africa": {"planting": [3, 4], "harvest": [7, 8]},
        "western_africa": {"planting": [6, 7], "harvest": [10, 11]},
    },
    "sorghum": {
        "southern_africa": {"planting": [10, 11], "harvest": [4, 5]},
        "western_africa": {"planting": [6, 7], "harvest": [10, 11]},
    },
    "millet": {
        "western_africa": {"planting": [6, 7], "harvest": [10, 11]},
        "eastern_africa": {"planting": [3, 4], "harvest": [8, 9]},
    },
}


def get_crop_calendar(crop: str, region: str = "southern_africa") -> dict:
    """Get planting/harvest months for a crop in a region."""
    crop_cal = CROP_CALENDARS.get(crop.lower(), {})
    return crop_cal.get(region, {"planting": [], "harvest": []})


def add_crop_calendar_features(df: pd.DataFrame, date_col: str = "date", region: str = "southern_africa") -> pd.DataFrame:
    """Add crop calendar features to a DataFrame."""
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col])
    df["month"] = df[date_col].dt.month
    df["day_of_year"] = df[date_col].dt.dayofyear
    df["week_of_year"] = df[date_col].dt.isocalendar().week
    
    # Add crop calendar features for major crops
    for crop in ["maize", "wheat", "rice", "sorghum", "millet"]:
        cal = get_crop_calendar(crop)
        planting_months = set(cal.get("planting", []))
        harvest_months = set(cal.get("harvest", []))
        
        df[f"{crop}_planting_season"] = df["month"].isin(planting_months).astype(int)
        df[f"{crop}_harvest_season"] = df["month"].isin(harvest_months).astype(int)
        df[f"{crop}_growing_season"] = (
            df["month"].isin(planting_months) | df["month"].isin(harvest_months)
        ).astype(int)
    
    return df


def prepare_ml_features(
    df: pd.DataFrame,
    target_col: str,
    date_col: str = "date",
    lags: list[int] = [1, 7, 14, 30],
    rolling_windows: list[int] = [7, 14, 30, 60],
) -> tuple[pd.DataFrame, pd.Series]:
    """Prepare ML features for time series forecasting."""
    df = df.copy()
    df = df.sort_values("date")
    
    # Lag features
    for lag in lags:
        df[f"{target_col}_lag_{lag}"] = df[target_col].shift(lag)
    
    # Rolling statistics
    for window in rolling_windows:
        df[f"{target_col}_rolling_mean_{window}"] = df[target_col].rolling(window=window, min_periods=1).mean()
        df[f"{target_col}_rolling_std_{window}"] = df[target_col].rolling(window=window, min_periods=1).std()
        df[f"{target_col}_rolling_min_{window}"] = df[target_col].rolling(window=window, min_periods=1).min()
        df[f"{target_col}_rolling_max_{window}"] = df[target_col].rolling(window=window, min_periods=1).max()
    
    # Date features
    df["date"] = pd.to_datetime(df["date"])
    df["day_of_year"] = df["date"].dt.dayofyear
    df["month"] = df["date"].dt.month
    df["week"] = df["date"].dt.isocalendar().week
    df["quarter"] = df["date"].dt.quarter
    df["day_of_week"] = df["date"].dt.dayofweek
    df["is_month_start"] = df["date"].dt.is_month_start.astype(int)
    df["is_month_end"] = df["date"].dt.is_month_end.astype(int)
    df["is_quarter_start"] = df["date"].dt.is_quarter_start.astype(int)
    df["is_quarter_end"] = df["date"].dt.is_quarter_end.astype(int)
    
    # Cyclical encoding for seasonal features
    df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
    df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12)
    df["day_of_year_sin"] = np.sin(2 * np.pi * df["day_of_year"] / 365)
    df["day_of_year_cos"] = np.cos(2 * np.pi * df["day_of_year"] / 365)
    
    # Target
    y = df[target_col]
    
    # Drop NaN rows
    feature_cols = [c for c in df.columns if c not in [target_col, "date"]]
    df_clean = df.dropna(subset=[target_col] + feature_cols)
    
    return df_clean[feature_cols], df_clean[target_col]


def train_ml_model(
    X: pd.DataFrame,
    y: pd.Series,
    model_type: str = "rf",
    **kwargs
):
    """Train ML model for forecasting."""
    if model_type == "rf":
        model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1, **kwargs)
    elif model_type == "lr":
        model = LinearRegression(**kwargs)
    else:
        raise ValueError(f"Unknown model type: {model_type}")
    
    # Scale features for linear regression
    scaler = None
    if model_type == "lr":
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        model.fit(X_scaled, y)
        return model, scaler
    else:
        model.fit(X, y)
        return model, None


def forecast_with_ml(
    df: pd.DataFrame,
    target_col: str,
    horizon: int = 30,
    model_type: str = "rf",
    **kwargs
) -> dict:
    """Train ML model and forecast future values."""
    from sokodata.datasets.markets.analysis.seasonal import seasonal_baseline
    
    # First get seasonal baseline
    baseline_result = seasonal_baseline(df, target_col, periods=365)
    if "error" in baseline_result:
        return {"error": "Insufficient data for forecasting"}
    
    # Prepare ML features
    X, y = prepare_ml_features(df, target_col)
    
    # Train ML model
    model, scaler = train_ml_model(X, y, model_type=model_type)
    
    # Generate future features for forecasting
    last_date = df["date"].max()
    future_dates = pd.date_range(start=df["date"].max() + pd.Timedelta(days=1), periods=horizon, freq='D')
    
    # Create future feature dataframe
    future_df = pd.DataFrame({"date": future_dates})
    future_df = add_crop_calendar_features(future_df, "date")
    
    # Add lag/rolling features using last known values
    last_values = df[target_col].tail(60).values
    for lag in [1, 7, 14, 30]:
        future_df[f"lag_{lag}"] = np.roll(np.append(last_values, np.nan * np.ones(horizon)), lag)[-horizon:]
    
    # Add rolling features (use last known values)
    for window in [7, 14, 30, 60]:
        future_df[f"rolling_mean_{window}"] = np.mean(last_values[-window:]) if len(last_values) >= window else np.nan
        future_df[f"rolling_std_{window}"] = np.std(last_values[-window:]) if len(last_values) >= window else np.nan
    
    # Add date features
    future_df["date"] = pd.to_datetime(future_df["date"])
    future_df["day_of_year"] = future_df["date"].dt.dayofyear
    future_df["month"] = future_df["date"].dt.month
    future_df["week"] = future_df["date"].dt.isocalendar().week
    future_df["quarter"] = future_df["date"].dt.quarter
    future_df["day_of_week"] = future_df["date"].dt.dayofweek
    future_df["month_sin"] = np.sin(2 * np.pi * future_df["month"] / 12)
    future_df["month_cos"] = np.cos(2 * np.pi * future_df["month"] / 12)
    future_df["day_of_year_sin"] = np.sin(2 * np.pi * future_df["day_of_year"] / 365)
    future_df["day_of_year_cos"] = np.cos(2 * np.pi * future_df["day_of_year"] / 365)
    
    # Add crop calendar features
    future_df = add_crop_calendar_features(future_df, "date")
    
    # Prepare features for prediction
    feature_cols = [c for c in X.columns if c in future_df.columns]
    X_future = future_df[feature_cols]
    
    # Scale if needed
    if scaler:
        X_future = scaler.transform(X_future)
    else:
        X_future = X_future.values
    
    # Predict
    predictions = model.predict(X_future)
    
    # Combine with seasonal baseline
    baseline_result = seasonal_baseline(
        pd.DataFrame({"date": pd.date_range(end=pd.Timestamp.now(), periods=365, freq='D'), "value": np.nan}),
        "value",
        periods=365
    )
    seasonal_baseline = np.interp(
        np.arange(horizon),
        np.linspace(0, 1, len(baseline_result["forecast"])),
        baseline_result["forecast"][:horizon]
    ) if "forecast" in baseline_result else np.zeros(horizon)
    
    # Combine ML predictions with seasonal baseline
    final_forecast = predictions + seasonal_baseline
    
    return {
        "forecast": final_forecast.tolist(),
        "forecast_dates": [str(d) for d in future_dates],
        "method": "ml_with_seasonal_baseline",
        "baseline_r2": baseline_result.get("r_squared", 0),
    }


def coverage(df: pd.DataFrame) -> dict:
    """Dataset-level stats for the /health and README numbers."""
    s = dedupe_flag(df)
    return {
        "observations": int(len(s)),
        "markets": int(s["market_id"].nunique()),
        "commodities": int(s["commodity_id"].nunique()),
        "first_date": s["date"].min().date().isoformat() if not s.empty else None,
        "last_date": s["date"].max().date().isoformat() if not s.empty else None,
    }


__all__ = ["anomalies", "coverage", "dedupe_flag", "movers", "seasonal_baseline"]


def seasonal_baseline(
    df: pd.DataFrame,
    value_col: str,
    date_col: str = "date",
    periods: int = 365,
    n_harmonics: int = 3,
) -> dict:
    """Compute seasonal baseline using harmonic regression.
    
    Fits a harmonic regression model to detect seasonal patterns.
    Returns baseline values and seasonal components.
    
    Args:
        df: DataFrame with date and value columns
        value_col: Name of the value column
        date_col: Name of the date column (default: 'date')
        periods: Number of periods in a cycle (default: 365 for daily data)
        n_harmonics: Number of harmonics to fit (default: 3)
    
    Returns:
        Dictionary with baseline values, seasonal components, and metadata
    """
    df = df.copy()
    df = df.sort_values(date_col)
    
    # Create time index
    t = np.arange(len(df))
    y = df[value_col].values
    dates = df[date_col].values
    
    # Remove NaN values
    mask = ~np.isnan(y)
    if mask.sum() < 10:
        return {"error": "Insufficient data points"}
    
    t_clean = t[mask]
    y_clean = y[mask]
    dates_clean = dates[mask]
    
    # Normalize time to [0, 2*pi] for one period
    t_norm = 2 * np.pi * t_clean / periods
    
    # Build design matrix with harmonics
    X = np.ones((len(y_clean), 1 + 2 * n_harmonics))
    for k in range(1, n_harmonics + 1):
        X[:, 2*k - 1] = np.sin(k * 2 * np.pi * t_clean / periods)
        X[:, 2*k] = np.cos(k * 2 * np.pi * t_clean / periods)
    
    # Fit linear regression
    coeffs, residuals, rank, s = np.linalg.lstsq(X, y_clean, rcond=None)
    
    # Predict baseline
    baseline = X @ coeffs
    residuals = y_clean - baseline
    
    # Seasonal component (without intercept)
    seasonal = baseline - coeffs[0]
    
    # Forecast next period
    t_future = np.arange(len(df), len(df) + periods)
    t_future_norm = 2 * np.pi * t_future / periods
    
    X_future = np.ones((len(t_future), 1 + 2 * n_harmonics))
    for k in range(1, n_harmonics + 1):
        X_future[:, 2*k - 1] = np.sin(k * 2 * np.pi * t_future / periods)
        X_future[:, 2*k] = np.cos(k * 2 * np.pi * t_future / periods)
    
    forecast = X_future @ coeffs
    
    return {
        "baseline": baseline.tolist(),
        "seasonal": seasonal.tolist(),
        "residuals": residuals.tolist(),
        "forecast": forecast.tolist(),
        "forecast_dates": [str(d) for d in pd.date_range(dates[-1], periods=periods+1, freq='D')[1:]],
        "coefficients": coeffs.tolist(),
        "r_squared": 1 - np.sum(residuals**2) / np.sum((y_clean - np.mean(y_clean))**2),
        "n_observations": int(mask.sum()),
        "periods": periods,
        "n_harmonics": n_harmonics,
    }
