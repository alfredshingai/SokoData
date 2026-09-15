"""Clean economy data - RBZ rates, ZIMSTAT CPI, ZERA fuel.

PDF/HTML scraping is lossy; cleaning is strict: coerce types, drop
bad rows, dedupe on natural keys. Never fabricate values.
"""

import logging

import pandas as pd

log = logging.getLogger(__name__)


def clean_rates(df: pd.DataFrame) -> pd.DataFrame:
    """Clean ZiG/USD rate series: columns [date, rate, source]."""
    if df.empty:
        return df
    out = df.copy()
    out["date"] = pd.to_datetime(out["date"], errors="coerce")
    out["rate"] = pd.to_numeric(out["rate"], errors="coerce")
    out["source"] = out["source"].astype("string").str.strip()
    out = out.dropna(subset=["date", "rate"])
    out = out[out["rate"] > 0]
    out = out.drop_duplicates(subset=["date", "source"], keep="last")
    out = out.sort_values("date").reset_index(drop=True)
    log.info("clean_rates: %d rows", len(out))
    return out


def clean_cpi(df: pd.DataFrame) -> pd.DataFrame:
    """Clean CPI series: columns [date, cpi, inflation_yoy, inflation_mom, source]."""
    if df.empty:
        return df
    out = df.copy()
    out["date"] = pd.to_datetime(out["date"], errors="coerce")
    for col in ("cpi", "inflation_yoy", "inflation_mom"):
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")
    out["source"] = out["source"].astype("string").str.strip()
    out = out.dropna(subset=["date"])
    out = out.drop_duplicates(subset=["date", "source"], keep="last")
    out = out.sort_values("date").reset_index(drop=True)
    log.info("clean_cpi: %d rows", len(out))
    return out


def clean_fuel(df: pd.DataFrame) -> pd.DataFrame:
    """Clean fuel prices: columns [date, fuel_type, price, currency, source]."""
    if df.empty:
        return df
    out = df.copy()
    out["date"] = pd.to_datetime(out["date"], errors="coerce")
    out["fuel_type"] = out["fuel_type"].astype("string").str.strip()
    out["price"] = pd.to_numeric(out["price"], errors="coerce")
    out["currency"] = out["currency"].astype("string").str.strip().str.upper()
    out["source"] = out["source"].astype("string").str.strip()
    out = out.dropna(subset=["date", "fuel_type", "price"])
    out = out[out["price"] > 0]
    out = out.drop_duplicates(subset=["date", "fuel_type", "source"], keep="last")
    out = out.sort_values(["date", "fuel_type"]).reset_index(drop=True)
    log.info("clean_fuel: %d rows", len(out))
    return out
