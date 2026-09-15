"""Fetch labour data for Zimbabwe.

* World Bank WDI (open JSON, CC BY-4.0) - SL.UEM.TOTL.ZS, SL.UEM.TOTL.NE.ZS,
  SL.TLF.CACT.ZS, SL.EMP.VULN.ZS
* ILO ILOSTAT API hook - optional fallback
* ZIMSTAT LFCLS HTML/PDF scraping - no API, degrades gracefully.
"""

import logging
from pathlib import Path

import pandas as pd

from sokodata.config import RAW_DIR
from sokodata.core.fetch import download_pdf, extract_pdf_tables, fetch_html_tables, fetch_json

log = logging.getLogger(__name__)

WDI_UEM = "https://api.worldbank.org/v2/country/ZW/indicator/SL.UEM.TOTL.ZS?format=json&per_page=100&date=1960:2030"
WDI_UEM_NAT = "https://api.worldbank.org/v2/country/ZW/indicator/SL.UEM.TOTL.NE.ZS?format=json&per_page=100&date=1960:2030"
WDI_LFPR = "https://api.worldbank.org/v2/country/ZW/indicator/SL.TLF.CACT.ZS?format=json&per_page=100&date=1960:2030"
WDI_VULN = "https://api.worldbank.org/v2/country/ZW/indicator/SL.EMP.VULN.ZS?format=json&per_page=100&date=1960:2030"

ZIMSTAT_LFCLS_URL = "https://www.zimstat.co.zw/"
ZIMSTAT_LFCLS_PDF = "https://www.zimstat.co.zw/wp-content/uploads/publications/Economic/Labour/LFCLS.pdf"


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


def fetch_worldbank_labour() -> pd.DataFrame:
    uem = _fetch_wdi(WDI_UEM, "unemployment_pct")
    uem_nat = _fetch_wdi(WDI_UEM_NAT, "unemployment_national_pct")
    lfpr = _fetch_wdi(WDI_LFPR, "labour_force_participation_pct")
    vuln = _fetch_wdi(WDI_VULN, "vulnerable_employment_pct")
    dfs = [d for d in (uem, uem_nat, lfpr, vuln) if not d.empty]
    if not dfs:
        return pd.DataFrame(columns=["date", "unemployment_pct", "unemployment_national_pct", "labour_force_participation_pct", "vulnerable_employment_pct", "source"])
    out = dfs[0]
    for df in dfs[1:]:
        out = out.merge(df, on="date", how="outer", suffixes=("", "_y"))
        out["source"] = out["source"].fillna(out["source_y"])
        out = out.drop(columns=[c for c in out.columns if c.endswith("_y")])
    out = out.sort_values("date").reset_index(drop=True)
    out["source"] = "World Bank WDI"
    return out


def fetch_lfcls_html(raw_dir: Path | None = None) -> pd.DataFrame:
    tables = fetch_html_tables(ZIMSTAT_LFCLS_URL, match="Labour|Employment|Unemployment|LFCLS")
    rows = []
    for tbl in tables:
        rows.append({"raw": tbl.head(2).to_string(), "source": "ZIMSTAT HTML"})
    df = pd.DataFrame(rows)
    log.info("Labour HTML: %d tables", len(df))
    return df


def fetch_labour_all(raw_dir: Path | None = None) -> dict[str, pd.DataFrame]:
    wdi = fetch_worldbank_labour()
    html = fetch_lfcls_html(raw_dir)
    try:
        base = raw_dir or RAW_DIR
        pdf_path = Path(base) / "zimstat_lfcls.pdf"
        download_pdf(ZIMSTAT_LFCLS_PDF, pdf_path)
        tables = extract_pdf_tables(pdf_path, pages="1-2")
        log.info("LFCLS PDF: %d tables", len(tables))
    except Exception as e:
        log.warning("LFCLS PDF failed: %s", e)
    return {"annual": wdi, "lfcls": html}
