"""Fetch mining data for a country.

* World Bank WDI (open JSON, CC BY-4.0) - NY.GDP.TOTL.RT.ZS (mineral rents),
  TX.VAL.MMTL.ZS.UN (ores+metals exports), TX.VAL.FUEL.ZS.UN (fuel exports)
* UN Comtrade fallback optional (gold/platinum/lithium HS codes)
* Country-specific Chamber/RBZ scrapers - degrade gracefully.
"""

import logging
from pathlib import Path

import pandas as pd

from sokodata.config import RAW_DIR, get_wb_country
from sokodata.core.fetch import download_pdf, extract_pdf_tables, fetch_html_tables, fetch_json

log = logging.getLogger(__name__)


def _fetch_wdi_indicator(indicator: str, col: str, country: str) -> pd.DataFrame:
    wb_country = get_wb_country(country)
    url = f"https://api.worldbank.org/v2/country/{wb_country}/indicator/{indicator}?format=json&per_page=100&date=1960:2030"
    try:
        data = fetch_json(url)
        recs = data[1] if isinstance(data, list) and len(data) > 1 else []
        rows = []
        for r in recs:
            if r.get("value") is None or r.get("date") is None:
                continue
            rows.append({"date": f"{r['date']}-12-31", col: float(r["value"]), "source": f"WDI {col} ({country})"})
        df = pd.DataFrame(rows)
        if not df.empty:
            df["date"] = pd.to_datetime(df["date"])
        log.info("WDI %s for %s: %d", col, country, len(df))
        return df
    except Exception as e:
        log.warning("WDI %s for %s failed: %s", col, country, e)
        return pd.DataFrame(columns=["date", col, "source"])


def fetch_worldbank_mining(country: str = "ZW") -> pd.DataFrame:
    rents = _fetch_wdi_indicator("NY.GDP.TOTL.RT.ZS", "mineral_rents_pct_gdp", country)
    ore = _fetch_wdi_indicator("TX.VAL.MMTL.ZS.UN", "ore_metal_exports_pct", country)
    fuel = _fetch_wdi_indicator("TX.VAL.FUEL.ZS.UN", "fuel_exports_pct", country)
    dfs = [d for d in (rents, ore, fuel) if not d.empty]
    if not dfs:
        return pd.DataFrame(columns=["date", "mineral_rents_pct_gdp", "ore_metal_exports_pct", "fuel_exports_pct", "source"])
    out = dfs[0]
    for df in dfs[1:]:
        out = out.merge(df, on="date", how="outer", suffixes=("", "_y"))
        out["source"] = out["source"].fillna(out["source_y"])
        out = out.drop(columns=[c for c in out.columns if c.endswith("_y")])
    out = out.sort_values("date").reset_index(drop=True)
    out["source"] = f"World Bank WDI ({country})"
    return out


def fetch_chamber_html(raw_dir: Path | None = None) -> pd.DataFrame:
    """Zimbabwe-specific Chamber/RBZ scraper."""
    tables = fetch_html_tables("https://www.chamberofminesofzimbabwe.com/", match="Gold|Platinum|Lithium|Production|Deliveries")
    rows = []
    for tbl in tables:
        rows.append({"raw": tbl.head(2).to_string(), "source": "Chamber HTML"})
    # also try RBZ gold price / deliveries page
    try:
        rbz_tables = fetch_html_tables("https://www.rbz.co.zw/", match="Gold|Mineral|Export")
        for tbl in rbz_tables:
            rows.append({"raw": tbl.head(2).to_string(), "source": "RBZ HTML"})
    except Exception:
        pass
    df = pd.DataFrame(rows)
    log.info("Mining HTML: %d tables", len(df))
    return df


def fetch_mining_all(country: str = "ZW", raw_dir: Path | None = None) -> dict[str, pd.DataFrame]:
    wdi = fetch_worldbank_mining(country)
    if country == "ZW":
        html = fetch_chamber_html(raw_dir)
        try:
            base = raw_dir or RAW_DIR
            pdf_path = Path(base) / "gold_deliveries.pdf"
            download_pdf("https://www.rbz.co.zw/wp-content/uploads/Gold_Deliveries.pdf", pdf_path)
            tables = extract_pdf_tables(pdf_path, pages="1-2")
            log.info("Gold PDF: %d tables", len(tables))
        except Exception as e:
            log.warning("Gold PDF failed: %s", e)
    else:
        html = pd.DataFrame()
    return {"annual": wdi, "chamber": html}