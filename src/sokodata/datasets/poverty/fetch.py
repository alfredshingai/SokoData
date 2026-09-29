"""Fetch poverty/inequality data for a country.

* World Bank WDI (open JSON, CC BY-4.0) - SI.POV.DDAY, SI.POV.GINI,
  SI.POV.LMIC, SI.POV.NAHC, SI.DST.05TH.20 (shared prosperity)
* Country-specific ZIMSTAT PICES scraper - degrades gracefully.
"""

import logging
from pathlib import Path

import pandas as pd

from sokodata.config import RAW_DIR, get_wb_country
from sokodata.core.fetch import download_pdf, extract_pdf_tables, fetch_html_tables, fetch_json

log = logging.getLogger(__name__)


def _fetch_wdi_indicator(indicator: str, col: str, country: str) -> pd.DataFrame:
    wb_country = get_wb_country(country)
    url = f"https://api.worldbank.org/v2/country/{wb_country}/indicator/{indicator}?format=json&per_page=100&date=1980:2030"
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


def fetch_worldbank_poverty(country: str = "ZW") -> pd.DataFrame:
    dday = _fetch_wdi_indicator("SI.POV.DDAY", "extreme_poverty_pct", country)
    gini = _fetch_wdi_indicator("SI.POV.GINI", "gini_index", country)
    nahc = _fetch_wdi_indicator("SI.POV.NAHC", "national_poverty_pct", country)
    bot = _fetch_wdi_indicator("SI.DST.05TH.20", "bottom40_growth_pct", country)
    dfs = [d for d in (dday, gini, nahc, bot) if not d.empty]
    if not dfs:
        return pd.DataFrame(columns=["date", "extreme_poverty_pct", "gini_index", "national_poverty_pct", "bottom40_growth_pct", "source"])
    out = dfs[0]
    for df in dfs[1:]:
        out = out.merge(df, on="date", how="outer", suffixes=("", "_y"))
        out["source"] = out["source"].fillna(out["source_y"])
        out = out.drop(columns=[c for c in out.columns if c.endswith("_y")])
    out = out.sort_values("date").reset_index(drop=True)
    out["source"] = f"World Bank WDI ({country})"
    return out


def fetch_poverty_html(raw_dir: Path | None = None) -> pd.DataFrame:
    """Zimbabwe-specific ZIMSTAT poverty scraper."""
    tables = fetch_html_tables("https://www.zimstat.co.zw/", match="Poverty|PICES|Income|Gini")
    rows = []
    for tbl in tables:
        rows.append({"raw": tbl.head(2).to_string(), "source": "ZIMSTAT HTML"})
    df = pd.DataFrame(rows)
    log.info("Poverty HTML: %d tables", len(df))
    return df


def fetch_poverty_all(country: str = "ZW", raw_dir: Path | None = None) -> dict[str, pd.DataFrame]:
    wdi = fetch_worldbank_poverty(country)
    if country == "ZW":
        html = fetch_poverty_html(raw_dir)
        try:
            base = raw_dir or RAW_DIR
            pdf_path = Path(base) / "pices.pdf"
            download_pdf("https://www.zimstat.co.zw/wp-content/uploads/publications/Economic/Poverty/PICES.pdf", pdf_path)
            tables = extract_pdf_tables(pdf_path, pages="1-2")
            log.info("PICES PDF: %d tables", len(tables))
        except Exception as e:
            log.warning("PICES PDF failed: %s", e)
    else:
        html = pd.DataFrame()
    return {"annual": wdi, "pices": html}