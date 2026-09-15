"""Fetch gender data for Zimbabwe.

* World Bank WDI (open JSON, CC BY-4.0) - SG.GEN.PARL.ZS, SG.VAW.ARGU.ZS,
  SL.TLF.CACT.FE.ZS, SE.ADT.LITR.FE.ZS
* UN Women / ZIMSTAT HTML/PDF scraping - no API, degrades gracefully.
"""

import logging
from pathlib import Path

import pandas as pd

from sokodata.config import RAW_DIR
from sokodata.core.fetch import download_pdf, extract_pdf_tables, fetch_html_tables, fetch_json

log = logging.getLogger(__name__)

WDI_PARL = "https://api.worldbank.org/v2/country/ZW/indicator/SG.GEN.PARL.ZS?format=json&per_page=100&date=1990:2030"
WDI_LFP_FE = "https://api.worldbank.org/v2/country/ZW/indicator/SL.TLF.CACT.FE.ZS?format=json&per_page=100&date=1990:2030"
WDI_PRIM_FE = "https://api.worldbank.org/v2/country/ZW/indicator/SE.ENR.PRIM.FM.ZS?format=json&per_page=100&date=1970:2030"
WDI_MORT_MAT = "https://api.worldbank.org/v2/country/ZW/indicator/SH.STA.MMRT?format=json&per_page=100&date=1990:2030"

UNWOMEN_URL = "https://data.unwomen.org/country/zimbabwe"
ZIMSTAT_GENDER_PDF = "https://www.zimstat.co.zw/wp-content/uploads/publications/Social/Gender_Statistics.pdf"


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


def fetch_worldbank_gender() -> pd.DataFrame:
    parl = _fetch_wdi(WDI_PARL, "women_parliament_pct")
    lfp = _fetch_wdi(WDI_LFP_FE, "female_lfpr_pct")
    prim = _fetch_wdi(WDI_PRIM_FE, "primary_parity_index")
    mat = _fetch_wdi(WDI_MORT_MAT, "maternal_mortality_per_100k")
    dfs = [d for d in (parl, lfp, prim, mat) if not d.empty]
    if not dfs:
        return pd.DataFrame(columns=["date", "women_parliament_pct", "female_lfpr_pct", "primary_parity_index", "maternal_mortality_per_100k", "source"])
    out = dfs[0]
    for df in dfs[1:]:
        out = out.merge(df, on="date", how="outer", suffixes=("", "_y"))
        out["source"] = out["source"].fillna(out["source_y"])
        out = out.drop(columns=[c for c in out.columns if c.endswith("_y")])
    out = out.sort_values("date").reset_index(drop=True)
    out["source"] = "World Bank WDI"
    return out


def fetch_unwomen_html(raw_dir: Path | None = None) -> pd.DataFrame:
    tables = fetch_html_tables(UNWOMEN_URL, match="Gender|Women|Parity|Maternal")
    rows = []
    for tbl in tables:
        rows.append({"raw": tbl.head(2).to_string(), "source": "UN Women HTML"})
    df = pd.DataFrame(rows)
    log.info("Gender HTML: %d tables", len(df))
    return df


def fetch_gender_all(raw_dir: Path | None = None) -> dict[str, pd.DataFrame]:
    wdi = fetch_worldbank_gender()
    html = fetch_unwomen_html(raw_dir)
    try:
        base = raw_dir or RAW_DIR
        pdf_path = Path(base) / "gender_stats.pdf"
        download_pdf(ZIMSTAT_GENDER_PDF, pdf_path)
        tables = extract_pdf_tables(pdf_path, pages="1-2")
        log.info("Gender PDF: %d tables", len(tables))
    except Exception as e:
        log.warning("Gender PDF failed: %s", e)
    return {"annual": wdi, "unwomen": html}
