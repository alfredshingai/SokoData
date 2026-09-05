"""Unit tests for the cleaning rules."""

import pandas as pd
import pytest

from sokodata.etl.clean import SchemaDrift, clean_markets, clean_prices


def test_clean_keps_valid_rows_and_normalizes(raw_prices):
    out = clean_prices(raw_prices)
    assert len(out) == len(raw_prices)
    assert str(out["date"].dtype).startswith("datetime64")
    assert out["price"].notna().all()


def test_clean_drops_null_keys(raw_prices):
    bad = raw_prices.copy()
    bad.loc[0, "price"] = None
    out = clean_prices(bad)
    assert len(out) == len(raw_prices) - 1


def test_clean_removes_duplicates(raw_prices):
    duped = pd.concat([raw_prices, raw_prices.tail(3)], ignore_index=True)
    out = clean_prices(duped)
    assert len(out) == len(raw_prices)


def test_clean_strips_whitespace(raw_prices):
    messy = raw_prices.copy()
    messy["market"] = "  " + messy["market"] + " "
    out = clean_prices(messy)
    assert not out["market"].str.startswith(" ").any()


def test_clean_rejects_unknown_flags(raw_prices):
    odd = raw_prices.copy()
    odd.loc[0, "priceflag"] = "weird"
    out = clean_prices(odd)
    assert "weird" not in set(out["priceflag"])


def test_clean_raises_on_schema_drift(raw_prices):
    broken = raw_prices.rename(columns={"price": "cost"})
    with pytest.raises(SchemaDrift):
        clean_prices(broken)


def test_clean_nulls_implausible_usd():
    """Broken USD conversions are nulled in any era; sane ones survive."""
    def row(date, usd):
        return (date, "Harare", "Harare", "A", 1, -17.9, 31.0,
                "cereals and tubers", "Maize", 10, "KG", "aggregate", "Retail",
                "ZWL", 100.0, usd)

    df = pd.DataFrame(
        [
            row("2025-01-15", 1.0),
            row("2025-02-15", 1.0),
            row("2025-03-15", 1.0),
            row("2021-06-15", 0.001),  # broken ZWL-era conversion
            row("2022-06-15", 0.9),  # plausibly cheap but sane
        ],
        columns=["date", "admin1", "admin2", "market", "market_id", "latitude", "longitude",
                 "category", "commodity", "commodity_id", "unit", "priceflag", "pricetype",
                 "currency", "price", "usdprice"],
    )
    out = clean_prices(df).set_index("date")["usdprice"]

    assert pd.isna(out["2021-06-15"]), "broken conversion must be nulled"
    assert out["2022-06-15"] == 0.9, "sane old conversion must survive"
    assert (out.loc[["2025-01-15", "2025-02-15", "2025-03-15"]] == 1.0).all()


def test_clean_markets_basic():
    df = clean_markets(
        pd.DataFrame(
            [
                {"market_id": 1, "market": " Mbare ", "countryiso3": "ZWE",
                 "admin1": "Harare", "admin2": None, "latitude": -17.86, "longitude": 31.04},
                {"market_id": 1, "market": "Mbare", "countryiso3": "ZWE",
                 "admin1": "Harare", "admin2": None, "latitude": -17.86, "longitude": 31.04},
            ]
        )
    )
    assert len(df) == 1
    assert df.iloc[0]["market"] == "Mbare"
