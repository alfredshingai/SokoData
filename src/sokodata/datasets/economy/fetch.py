"""Fetch economy data for a country.

Strategy - per SokoData commons principle "where there's no API, scrape;
where there's an API, use it":

* World Bank WDI API (open JSON, CC BY-4.0) - CPI/inflation, FX, stable fallback
* Country-specific scrapers (RBZ, ZIMSTAT, ZERA for Zimbabwe) - degrade gracefully
"""

import logging
from datetime import date
from pathlib import Path

import pandas as pd

from sokodata.config import RAW_DIR, get_wb_country
from sokodata.core.fetch import (
    download_pdf,
    extract_pdf_tables,
    fetch_html_tables,
    fetch_html_text,
    fetch_json,
    parse_fuel_text,
)

log = logging.getLogger(__name__)

# Zimbabwe-specific scraper URLs (only used for ZW)
RBZ_RATES_URL = "https://www.rbz.co.zw/market-rates"
ZERA_FUEL_URL = "https://www.zera.co.zw/"
ZIMSTAT_CPI_URL = "https://www.zimstat.co.zw/wp-content/uploads/publications/Economic/Price/CPI.pdf"


def _fetch_wdi_indicator(indicator: str, country: str) -> pd.DataFrame:
    """Fetch a WDI indicator for a country."""
    wb_country = get_wb_country(country)
    url = (
        f"https://api.worldbank.org/v2/country/{wb_country}/indicator/{indicator}"
        f"?format=json&per_page=100&date=2010:2030"
    )
    try:
        data = fetch_json(url)
        records = data[1] if isinstance(data, list) and len(data) > 1 else []
        rows = []
        for r in records:
            if r.get("value") is None or r.get("date") is None:
                continue
            rows.append({"date": f"{r['date']}-12-31", "value": float(r["value"]), "source": f"WDI {indicator}"})
        df = pd.DataFrame(rows)
        if not df.empty:
            df["date"] = pd.to_datetime(df["date"])
        log.info("WDI %s for %s: %d points", indicator, country, len(df))
        return df
    except Exception as e:
        log.warning("WDI %s for %s failed: %s", indicator, country, e)
        return pd.DataFrame(columns=["date", "value", "source"])


def fetch_worldbank_cpi(country: str = "ZW") -> pd.DataFrame:
    """Fetch annual CPI inflation % from World Bank WDI."""
    df = _fetch_wdi_indicator("FP.CPI.TOTL.ZG", country)
    if not df.empty:
        df = df.rename(columns={"value": "inflation_yoy"})
        df["cpi"] = None
        df["inflation_mom"] = None
        df["source"] = f"World Bank WDI FP.CPI.TOTL.ZG ({country})"
    return df


def fetch_worldbank_fx(country: str = "ZW") -> pd.DataFrame:
    """Fetch FX rate from World Bank WDI."""
    df = _fetch_wdi_indicator("PA.NUS.FCRF", country)
    if not df.empty:
        df = df.rename(columns={"value": "rate"})
        df["source"] = f"World Bank FX ({country})"
    return df


def fetch_economy_all(country: str = "ZW", raw_dir: Path | None = None) -> dict[str, pd.DataFrame]:
    """Fetch all economy sources for a country - WDI API + country-specific scrapers.

    For Zimbabwe: WDI + RBZ/ZERA/ZIMSTAT scrapers
    For other countries: WDI only (scrapers can be added per-country)
    """
    base = raw_dir or RAW_DIR
    cpi_wdi = fetch_worldbank_cpi(country)

    # Zimbabwe-specific scrapers
    cpi_pdf = pd.DataFrame()
    rates = pd.DataFrame()
    fuel = pd.DataFrame()

    if country == "ZW":
        from sokodata.datasets.economy.fetch import (
            fetch_rbz_rates_scrape as _fetch_rbz,
            fetch_zera_fuel_scrape as _fetch_zera,
            fetch_zimstat_cpi_pdf as _fetch_zimstat,
        )
        rates = _fetch_rbz()
        fuel = _fetch_zera(base)
        cpi_pdf = _fetch_zimstat(base)

    # Combine CPI sources
    if not cpi_pdf.empty:
        cpi = pd.concat([cpi_wdi, cpi_pdf], ignore_index=True)
    else:
        cpi = cpi_wdi

    # Add WDI FX as fallback
    fx_wdi = fetch_worldbank_fx(country)
    if not fx_wdi.empty:
        if not rates.empty:
            rates = pd.concat([rates, fx_wdi], ignore_index=True)
        else:
            rates = fx_wdi

    return {"rates": rates, "cpi": cpi, "fuel": fuel}