"""Fetch education data for a country.

* World Bank WDI (open JSON, CC BY-4.0) - SE.PRM.NENR, SE.SEC.NENR, SE.ADT.LITR.ZS, SE.PRM.CMPT.ZS, SE.TER.CMPT.ZS
* UNICEF / UNESCO fallback optional
* Country-specific MoPSE scrapers - degrade gracefully.
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


def fetch_worldbank_education(country: str = "ZW") -> pd.DataFrame:
    prim = _fetch_wdi_indicator("SE.PRM.NENR", "primary_ner_pct", country)
    sec = _fetch_wdi_indicator("SE.SEC.NENR", "secondary_ner_pct", country)
    litr = _fetch_wdi_indicator("SE.ADT.LITR.ZS", "adult_literacy_pct", country)
    cmpt = _fetch_wdi_indicator("SE.PRM.CMPT.ZS", "primary_completion_pct", country)
    dfs = [d for d in (prim, sec, litr, cmpt) if not d.empty]
    if not dfs:
        return pd.DataFrame(columns=["date", "primary_ner_pct", "secondary_ner_pct", "adult_literacy_pct", "primary_completion_pct", "source"])
    out = dfs[0]
    for df in dfs[1:]:
        out = out.merge(df, on="date", how="outer", suffixes=("", "_y"))
        out["source"] = out["source"].fillna(out["source_y"])
        out = out.drop(columns=[c for c in out.columns if c.endswith("_y")])
    out = out.sort_values("date").reset_index(drop=True)
    out["source"] = f"World Bank WDI ({country})"
    return out


def fetch_mopse_html(raw_dir: Path | None = None) -> pd.DataFrame:
    """Zimbabwe-specific MoPSE scraper."""
    tables = fetch_html_tables("https://www.mopse.gov.zw/", match="Enrolment|Enrol|School|Teacher|Literacy")
    rows = []
    for tbl in tables:
        rows.append({"raw": tbl.head(2).to_string(), "source": "MoPSE HTML"})
    df = pd.DataFrame(rows)
    log.info("MoPSE HTML: %d tables", len(df))
    return df


def fetch_education_all(country: str = "ZW", raw_dir: Path | None = None) -> dict[str, pd.DataFrame]:
    wdi = fetch_worldbank_education(country)
    if country == "ZW":
        html = fetch_mopse_html(raw_dir)
        try:
            base = raw_dir or RAW_DIR
            pdf_path = Path(base) / "mopse_stats.pdf"
            download_pdf("https://www.mopse.gov.zw/wp-content/uploads/Education_Statistics.pdf", pdf_path)
            tables = extract_pdf_tables(pdf_path, pages="1-2")
            log.info("MoPSE PDF: %d tables", len(tables))
        except Exception as e:
            log.warning("MoPSE PDF failed: %s", e)
    else:
        html = pd.DataFrame()
    return {"annual": wdi, "mopse": html}