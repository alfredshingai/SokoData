"""Clean geospatial metadata."""

import logging

import pandas as pd

log = logging.getLogger(__name__)


def clean_metadata(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    out = df.copy()
    for c in ("name", "format", "url", "source"):
        if c in out.columns:
            out[c] = out[c].astype("string").str.strip()
    out = out.dropna(subset=["name"])
    out = out.drop_duplicates(subset=["name"], keep="last")
    log.info("clean_geospatial: %d resources", len(out))
    return out
