"""Clean demographics data."""

import logging

import pandas as pd

log = logging.getLogger(__name__)


def clean_annual(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    out = df.copy()
    out["date"] = pd.to_datetime(out["date"], errors="coerce")
    for col in ("population", "pop_growth_pct", "urban_pct"):
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")
    out["source"] = out["source"].astype("string").str.strip()
    out = out.dropna(subset=["date"])
    out = out.drop_duplicates(subset=["date"], keep="last")
    out = out.sort_values("date").reset_index(drop=True)
    log.info("clean_annual: %d rows", len(out))
    return out


def clean_census(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    out = df.copy()
    out["admin1"] = out["admin1"].astype("string").str.strip()
    out["population"] = pd.to_numeric(out["population"], errors="coerce")
    for col in ("male", "female"):
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")
    out["source"] = out["source"].astype("string").str.strip()
    out = out.dropna(subset=["admin1", "population"])
    out = out[out["population"] > 0]
    out = out.drop_duplicates(subset=["admin1"], keep="last")
    out = out.sort_values("admin1").reset_index(drop=True)
    log.info("clean_census: %d rows", len(out))
    return out
