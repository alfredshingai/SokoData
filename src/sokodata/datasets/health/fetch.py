"""Fetch health data for Zimbabwe.

* World Bank WDI (open JSON, CC BY-4.0) - SP.DYN.IMRT.IN, SH.DYN.MORT, SH.IMM.MEAS, SH.MED.BEDS.ZS, SH.XPD.CHEX.GD.ZS
* WHO GHO API fallback (open JSON) - optional
* Ministry of Health HTML/PDF scraping - Zimbabwe HMIS bulletins, no API, degrades gracefully.
"""

import logging
from pathlib import Path

import pandas as pd

from sokodata.config import RAW_DIR
from sokodata.core.fetch import download_pdf, extract_pdf_tables, fetch_html_tables, fetch_json

log = logging.getLogger(__name__)

WDI_IMRT = "https://api.worldbank.org/v2/country/ZW/indicator/SP.DYN.IMRT.IN?format=json&per_page=100&date=1960:2030"
WDI_U5MORT = "https://api.worldbank.org/v2/country/ZW/indicator/SH.DYN.MORT?format=json&per_page=100&date=1960:2030"
WDI_MEASLES = "https://api.worldbank.org/v2/country/ZW/indicator/SH.IMM.MEAS?format=json&per_page=100&date=1960:2030"
WDI_HEALTH_XPD = "https://api.worldbank.org/v2/country/ZW/indicator/SH.XPD.CHEX.GD.ZS?format=json&per_page=100&date=1960:2030"

MOH_URL = "https://www.mohcc.gov.zw/"
MOH_PDF = "https://www.mohcc.gov.zw/wp-content/uploads/Health_Bulletin.pdf"


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


def fetch_worldbank_health() -> pd.DataFrame:
    imrt = _fetch_wdi(WDI_IMRT, "infant_mort_per_1k")
    u5 = _fetch_wdi(WDI_U5MORT, "under5_mort_per_1k")
    meas = _fetch_wdi(WDI_MEASLES, "measles_imm_pct")
    xpd = _fetch_wdi(WDI_HEALTH_XPD, "health_xpd_pct_gdp")
    dfs = [d for d in (imrt, u5, meas, xpd) if not d.empty]
    if not dfs:
        return pd.DataFrame(columns=["date", "infant_mort_per_1k", "under5_mort_per_1k", "measles_imm_pct", "health_xpd_pct_gdp", "source"])
    out = dfs[0]
    for df in dfs[1:]:
        out = out.merge(df, on="date", how="outer", suffixes=("", "_y"))
        out["source"] = out["source"].fillna(out["source_y"])
        out = out.drop(columns=[c for c in out.columns if c.endswith("_y")])
    out = out.sort_values("date").reset_index(drop=True)
    out["source"] = "World Bank WDI"
    return out


def fetch_moh_html(raw_dir: Path | None = None) -> pd.DataFrame:
    tables = fetch_html_tables(MOH_URL, match="Cholera|Malaria|Health|Cases")
    rows = []
    for tbl in tables:
        rows.append({"raw": tbl.head(2).to_string(), "source": "MoHCC HTML"})
    df = pd.DataFrame(rows)
    log.info("MoHCC HTML: %d tables", len(df))
    return df


def fetch_health_all(raw_dir: Path | None = None) -> dict[str, pd.DataFrame]:
    wdi = fetch_worldbank_health()
    html = fetch_moh_html(raw_dir)
    # Try MoH PDF
    try:
        base = raw_dir or RAW_DIR
        pdf_path = Path(base) / "moh_bulletin.pdf"
        download_pdf(MOH_PDF, pdf_path)
        tables = extract_pdf_tables(pdf_path, pages="1-2")
        log.info("MoH PDF: %d tables", len(tables))
    except Exception as e:
        log.warning("MoH PDF failed: %s", e)
    return {"annual": wdi, "moh": html}
