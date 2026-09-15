"""Validate and normalize raw WFP price/market data.

The source (WFP via HDX) is already fairly clean; these rules guard against
upstream schema drift and keep the warehouse contract stable:

- exact column set is enforced (fail loudly if WFP changes the schema)
- dates parse as ISO; prices coerce to float; bad rows are dropped and counted
- text fields are stripped; duplicates on the natural key are removed
- local-currency ``price`` is kept as-is, but every temporal computation in
  this project uses ``usdprice`` — Zimbabwe redenominated its currency
  (ZWL -> ZiG/ZWG in 2024) and upstream still labels the local currency
  "ZWL", so local-currency time series are not comparable across years.
"""

import logging

import pandas as pd

log = logging.getLogger(__name__)

PRICE_COLUMNS = [
    "date",
    "admin1",
    "admin2",
    "market",
    "market_id",
    "latitude",
    "longitude",
    "category",
    "commodity",
    "commodity_id",
    "unit",
    "priceflag",
    "pricetype",
    "currency",
    "price",
    "usdprice",
]

MARKET_COLUMNS = ["market_id", "market", "countryiso3", "admin1", "admin2", "latitude", "longitude"]

NATURAL_KEY = ["date", "market_id", "commodity_id", "pricetype", "priceflag"]
VALID_FLAGS = {"actual", "aggregate"}

# WFP's ``usdprice`` is unreliable for local-currency rows before the 2024
# ZiG reform: official-rate conversions during the hyperinflation years
# produce values like "$0.0017/kg of rice". We keep the raw price but null
# USD conversions that are implausibly cheap relative to the commodity's own
# post-2024 price level (see docs/data_dictionary.md).
IMPLAUSIBLE_ERA_START = "2024-01-01"
IMPLAUSIBLE_FACTOR = 0.10


class SchemaDrift(Exception):
    """Raised when upstream columns no longer match the expected schema."""


def _check_columns(df: pd.DataFrame, expected: list[str], label: str) -> None:
    missing = set(expected) - set(df.columns)
    if missing:
        raise SchemaDrift(f"{label}: upstream schema changed, missing columns: {sorted(missing)}")


def clean_prices(df: pd.DataFrame) -> pd.DataFrame:
    _check_columns(df, PRICE_COLUMNS, "prices")
    out = df[PRICE_COLUMNS].copy()

    for col in ("admin1", "admin2", "market", "category", "commodity", "unit", "currency"):
        out[col] = out[col].astype("string").str.strip()

    out["date"] = pd.to_datetime(out["date"], errors="coerce")
    for col in ("market_id", "commodity_id"):
        out[col] = pd.to_numeric(out[col], errors="coerce").astype("Int64")
    out["latitude"] = pd.to_numeric(out["latitude"], errors="coerce")
    out["longitude"] = pd.to_numeric(out["longitude"], errors="coerce")
    out["price"] = pd.to_numeric(out["price"], errors="coerce")
    out["usdprice"] = pd.to_numeric(out["usdprice"], errors="coerce")

    before = len(out)
    out = out.dropna(subset=["date", "market_id", "commodity_id", "price"])
    dropped_nulls = before - len(out)

    out = out[out["priceflag"].isin(VALID_FLAGS)]
    out = out.drop_duplicates(subset=NATURAL_KEY, keep="last")
    out = _null_implausible_usd(out)
    out = out.sort_values(NATURAL_KEY).reset_index(drop=True)

    log.info(
        "clean_prices: %d rows kept (%d dropped for null keys/ids, %d dupes removed)",
        len(out),
        dropped_nulls,
        before - dropped_nulls - len(out),
    )
    return out


def _null_implausible_usd(df: pd.DataFrame) -> pd.DataFrame:
    """Null USD conversions that are implausibly cheap for their commodity.

    Reference level = the commodity's median ``usdprice`` over the post-reform
    era (2024+), where WFP's USD conversions are sane. Anything below
    ``IMPLAUSIBLE_FACTOR`` of that reference is a broken conversion, not a
    price. The local-currency price is always preserved; only ``usdprice``
    is set to null. Commodities with no post-2024 rows are left untouched.
    """
    out = df.copy()
    era = out[out["date"] >= pd.Timestamp(IMPLAUSIBLE_ERA_START)]
    ref = era.groupby("commodity_id")["usdprice"].median()
    floors = ref * IMPLAUSIBLE_FACTOR

    mask = out["commodity_id"].map(floors)
    implausible = out["usdprice"].notna() & mask.notna() & (out["usdprice"] < mask)
    n = int(implausible.sum())
    if n:
        log.info(
            "nulled %d implausible USD conversions (< %.0f%% of commodity's "
            "post-%s median), e.g. ZWL-era rows",
            n,
            IMPLAUSIBLE_FACTOR * 100,
            IMPLAUSIBLE_ERA_START[:4],
        )
        out.loc[implausible, "usdprice"] = float("nan")
    return out


def clean_markets(df: pd.DataFrame) -> pd.DataFrame:
    _check_columns(df, MARKET_COLUMNS, "markets")
    out = df[MARKET_COLUMNS].copy()
    for col in ("market", "countryiso3", "admin1", "admin2"):
        out[col] = out[col].astype("string").str.strip()
    out["market_id"] = pd.to_numeric(out["market_id"], errors="coerce").astype("Int64")
    out["latitude"] = pd.to_numeric(out["latitude"], errors="coerce")
    out["longitude"] = pd.to_numeric(out["longitude"], errors="coerce")
    out = out.dropna(subset=["market_id"]).drop_duplicates(subset="market_id", keep="last")
    log.info("clean_markets: %d markets", len(out))
    return out
