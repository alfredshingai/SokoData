"""Fetch water data for Zimbabwe.

* World Bank WDI (open JSON, CC BY-4.0) - SH.H2O.SMDW.ZS, SH.STA.SMSS.ZS,
  SH.H2O.BASW.ZS, SH.STA.BASS.ZS
* ZINWA HTML/PDF scraping - dam levels, water supply updates, no API,
  degrades gracefully.
"""

import logging
from pathlib import Path

import pandas as pd

from sokodata.config import RAW_DIR
from sokodata.core.fetch import download_pdf, extract_pdf_tables, fetch_html_tables, fetch_json

log = logging.getLogger(__name__)

WDI_SAFE_WATER = "https://api.worldbank.org/v2/country/ZW/indicator/SH.H2O.SMDW.ZS?format=json&per_page=100&date=1960:2030"
WDI_SAFE_SANIT = "https://api.worldbank.org/v2/country/ZW/indicator/SH.STA.SMSS.ZS?format=json&per_page=100&date=1960:2030"
WDI_BASIC_WATER = "https://api.worldbank.org/v2/country/ZW/indicator/SH.H2O.BASW.ZS?format=json&per_page=100&date=1960:2030"
WDI_BASIC_SANIT = "https://api.worldbank.org/v2/country/ZW/indicator/SH.STA.BASS.ZS?format=json&per_page=100&date=1960:2030"

ZINWA_URL = "https://www.zinwa.co.zw/"
ZINWA_PDF = "https://www.zinwa.co.zw/wp-content/uploads/Dam_Levels.pdf"


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


def fetch_worldbank_water() -> pd.DataFrame:
    safe_w = _fetch_wdi(WDI_SAFE_WATER, "safe_water_pct")
    safe_s = _fetch_wdi(WDI_SAFE_SANIT, "safe_sanitation_pct")
    basic_w = _fetch_wdi(WDI_BASIC_WATER, "basic_water_pct")
    basic_s = _fetch_wdi(WDI_BASIC_SANIT, "basic_sanitation_pct")
    dfs = [d for d in (safe_w, safe_s, basic_w, basic_s) if not d.empty]
    if not dfs:
        return pd.DataFrame(columns=["date", "safe_water_pct", "safe_sanitation_pct", "basic_water_pct", "basic_sanitation_pct", "source"])
    out = dfs[0]
    for df in dfs[1:]:
        out = out.merge(df, on="date", how="outer", suffixes=("", "_y"))
        out["source"] = out["source"].fillna(out["source_y"])
        out = out.drop(columns=[c for c in out.columns if c.endswith("_y")])
    out = out.sort_values("date").reset_index(drop=True)
    out["source"] = "World Bank WDI"
    return out


def fetch_zinwa_html(raw_dir: Path | None = None) -> pd.DataFrame:
    tables = fetch_html_tables(ZINWA_URL, match="Dam|Level|Water|Supply|Harare|Kariba")
    rows = []
    for tbl in tables:
        rows.append({"raw": tbl.head(2).to_string(), "source": "ZINWA HTML"})
    df = pd.DataFrame(rows)
    log.info("ZINWA HTML: %d tables", len(df))
    return df


def fetch_water_all(raw_dir: Path | None = None) -> dict[str, pd.DataFrame]:
    wdi = fetch_worldbank_water()
    html = fetch_zinwa_html(raw_dir)
    try:
        base = raw_dir or RAW_DIR
        pdf_path = Path(base) / "zinwa_dams.pdf"
        download_pdf(ZINWA_PDF, pdf_path)
        tables = extract_pdf_tables(pdf_path, pages="1-2")
        log.info("ZINWA PDF: %d tables", len(tables))
    except Exception as e:
        log.warning("ZINWA PDF failed: %s", e)
    return {"annual": wdi, "zinwa": html}
