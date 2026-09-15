"""Clean climate data."""

import logging

import pandas as pd

log = logging.getLogger(__name__)


def clean_climate(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    out = df.copy()
    out["date"] = pd.to_datetime(out["date"], errors="coerce")
    for col in ("tmean_c", "tmax_c", "tmin_c", "precip_mm", "latitude", "longitude"):
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")
    out["admin1"] = out["admin1"].astype("string").str.strip()
    out["source"] = out["source"].astype("string").str.strip()
    # Drop rows with no date or both temp+precip null
    out = out.dropna(subset=["date", "admin1"])
    out = out.sort_values(["admin1", "date"]).reset_index(drop=True)
    # Dedupe on natural key
    out = out.drop_duplicates(subset=["date", "admin1", "source"], keep="last")
    log.info("clean_climate: %d rows", len(out))
    return out


def to_monthly(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate daily to monthly: mean temp, sum precip."""
    if df.empty:
        return df
    out = df.copy()
    out["month"] = out["date"].dt.to_period("M").dt.to_timestamp()
    agg = out.groupby(["admin1", "month"], as_index=False).agg(
        tmean_c=("tmean_c", "mean"),
        tmax_c=("tmax_c", "max"),
        tmin_c=("tmin_c", "min"),
        precip_mm=("precip_mm", "sum"),
        latitude=("latitude", "first"),
        longitude=("longitude", "first"),
    )
    agg = agg.rename(columns={"month": "date"})
    agg["source"] = "open-meteo-monthly"
    return agg.sort_values(["admin1", "date"]).reset_index(drop=True)
