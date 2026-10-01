"""Clean indicators data."""

import logging

import pandas as pd

log = logging.getLogger(__name__)


def clean_annual(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    out = df.copy()
    out["date"] = pd.to_datetime(out["date"], errors="coerce")
    out["country"] = out["country"].astype("string").str.strip().str.upper()
    out["source"] = out["source"].astype("string").str.strip()
    
    # Identify value columns (non-date, non-country, non-source)
    value_cols = [c for c in out.columns if c not in ("date", "country", "source")]
    for c in value_cols:
        out[c] = pd.to_numeric(out[c], errors="coerce")
    
    out = out.dropna(subset=["date", "country"])
    out = out.drop_duplicates(subset=["date", "country"], keep="last")
    out = out.sort_values(["country", "date"]).reset_index(drop=True)
    log.info("clean_annual: %d rows", len(out))
    return out