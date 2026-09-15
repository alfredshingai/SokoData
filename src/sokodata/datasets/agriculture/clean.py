"""Clean agriculture data."""

import logging

import pandas as pd

log = logging.getLogger(__name__)


def clean_annual(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    out = df.copy()
    out["date"] = pd.to_datetime(out["date"], errors="coerce")
    for c in ("cereal_yield_kg_ha", "agri_gdp_pct", "food_prod_idx", "crop_prod_idx"):
        if c in out.columns:
            out[c] = pd.to_numeric(out[c], errors="coerce")
    out["source"] = out["source"].astype("string").str.strip()
    out = out.dropna(subset=["date"])
    out = out.drop_duplicates(subset=["date"], keep="last")
    out = out.sort_values("date").reset_index(drop=True)
    log.info("clean_agri_annual: %d rows", len(out))
    return out


def clean_fao(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    out = df.copy()
    out["date"] = pd.to_datetime(out["date"], errors="coerce")
    out["maize_tonnes"] = pd.to_numeric(out["maize_tonnes"], errors="coerce")
    out["source"] = out["source"].astype("string").str.strip()
    out = out.dropna(subset=["date", "maize_tonnes"])
    out = out.sort_values("date").reset_index(drop=True)
    log.info("clean_fao_maize: %d rows", len(out))
    return out
