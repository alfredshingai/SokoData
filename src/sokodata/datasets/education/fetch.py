"""Fetch education data for Zimbabwe.

* World Bank WDI (open JSON, CC BY-4.0) - SE.PRM.NENR, SE.SEC.NENR, SE.ADT.LITR.ZS, SE.PRM.CMPT.ZS, SE.TER.CMPT.ZS
* UNICEF / UNESCO fallback optional
* MoPSE (Ministry Primary Secondary Education) HTML/PDF scraping - no API, degrades gracefully.
"""

import logging
from pathlib import Path

import pandas as pd

from sokodata.config import RAW_DIR
from sokodata.core.fetch import download_pdf, extract_pdf_tables, fetch_html_tables, fetch_json

log = logging.getLogger(__name__)

WDI_PRIM_NER = "https://api.worldbank.org/v2/country/ZW/indicator/SE.PRM.NENR?format=json&per_page=100&date=1960:2030"
WDI_SEC_NER = "https://api.worldbank.org/v2/country/ZW/indicator/SE.SEC.NENR?format=json&per_page=100&date=1960:2030"
WDI_LITR = "https://api.worldbank.org/v2/country/ZW/indicator/SE.ADT.LITR.ZS?format=json&per_page=100&date=1960:2030"
WDI_PRIM_CMPT = "https://api.worldbank.org/v2/country/ZW/indicator/SE.PRM.CMPT.ZS?format=json&per_page=100&date=1960:2030"

MOPSE_URL = "https://www.mopse.gov.zw/"
MOPSE_PDF = "https://www.mopse.gov.zw/wp-content/uploads/Education_Statistics.pdf"


def _fetch_wdi(url: str, col: str) -> pd.DataFrame:
    try:
        data = fetch_json(url)
        recs = data[1] if isinstance(data, list) and len(data) > 1 else []
        rows = []
        for r in recs:
            if r.get("value") is None or r.get("date") is None:
                continue
            rows.append({"date": f"{r['date']}-12-31", col: float(r["value"]), "source": f"WDI {col}"})
        df = pd.DataFrame(rows)
        if not df.empty:
            df["date"] = pd.to_datetime(df["date"])
        log.info("WDI %s: %d", col, len(df))
        return df
    except Exception as e:
        log.warning("WDI %s failed: %s", col, e)
        return pd.DataFrame(columns=["date", col, "source"])


def fetch_worldbank_education() -> pd.DataFrame:
    prim = _fetch_wdi(WDI_PRIM_NER, "primary_ner_pct")
    sec = _fetch_wdi(WDI_SEC_NER, "secondary_ner_pct")
    litr = _fetch_wdi(WDI_LITR, "adult_literacy_pct")
    cmpt = _fetch_wdi(WDI_PRIM_CMPT, "primary_completion_pct")
    dfs = [d for d in (prim, sec, litr, cmpt) if not d.empty]
    if not dfs:
        return pd.DataFrame(columns=["date", "primary_ner_pct", "secondary_ner_pct", "adult_literacy_pct", "primary_completion_pct", "source"])
    out = dfs[0]
    for df in dfs[1:]:
        out = out.merge(df, on="date", how="outer", suffixes=("", "_y"))
        out["source"] = out["source"].fillna(out["source_y"])
        out = out.drop(columns=[c for c in out.columns if c.endswith("_y")])
    out = out.sort_values("date").reset_index(drop=True)
    out["source"] = "World Bank WDI"
    return out


def fetch_mopse_html(raw_dir: Path | None = None) -> pd.DataFrame:
    tables = fetch_html_tables(MOPSE_URL, match="Enrolment|Enrol|School|Teacher|Literacy")
    rows = []
    for tbl in tables:
        rows.append({"raw": tbl.head(2).to_string(), "source": "MoPSE HTML"})
    df = pd.DataFrame(rows)
    log.info("MoPSE HTML: %d tables", len(df))
    return df


def fetch_education_all(raw_dir: Path | None = None) -> dict[str, pd.DataFrame]:
    wdi = fetch_worldbank_education()
    html = fetch_mopse_html(raw_dir)
    try:
        base = raw_dir or RAW_DIR
        pdf_path = Path(base) / "mopse_stats.pdf"
        download_pdf(MOPSE_PDF, pdf_path)
        tables = extract_pdf_tables(pdf_path, pages="1-2")
        log.info("MoPSE PDF: %d tables", len(tables))
    except Exception as e:
        log.warning("MoPSE PDF failed: %s", e)
    return {"annual": wdi, "mopse": html}
