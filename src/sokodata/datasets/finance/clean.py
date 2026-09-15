"""Clean finance data."""

import logging

import pandas as pd

log = logging.getLogger(__name__)


def clean_annual(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    out = df.copy()
    out["date"] = pd.to_datetime(out["date"], errors="coerce")
    for c in ("domestic_credit_pct_gdp", "remittances_usd", "private_credit_pct_gdp", "accounts_pct"):
        if c in out.columns:
            out[c] = pd.to_numeric(out[c], errors="coerce")
    out["source"] = out["source"].astype("string").str.strip()
    out = out.dropna(subset=["date"])
    out = out.drop_duplicates(subset=["date"], keep="last")
    out = out.sort_values("date").reset_index(drop=True)
    log.info("clean_finance_annual: %d rows", len(out))
    return out
