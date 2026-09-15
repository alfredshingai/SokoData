"""Fetch environment data for Zimbabwe.

* World Bank WDI (open JSON, CC BY-4.0) - EN.ATM.CO2E.PC, AG.LND.FRST.ZS,
  EN.ATM.PM25.MC.M3, AG.LND.FRST.K2 (forest km2)
* EMA Zimbabwe / ZINWA HTML/PDF scraping - no API, degrades gracefully.
"""

import logging
from pathlib import Path

import pandas as pd

from sokodata.config import RAW_DIR
from sokodata.core.fetch import download_pdf, extract_pdf_tables, fetch_html_tables, fetch_json

log = logging.getLogger(__name__)

WDI_CO2 = "https://api.worldbank.org/v2/country/ZW/indicator/EN.ATM.CO2E.PC?format=json&per_page=100&date=1960:2030"
WDI_FOREST = "https://api.worldbank.org/v2/country/ZW/indicator/AG.LND.FRST.ZS?format=json&per_page=100&date=1960:2030"
WDI_PM25 = "https://api.worldbank.org/v2/country/ZW/indicator/EN.ATM.PM25.MC.M3?format=json&per_page=100&date=2000:2030"
WDI_FOREST_KM2 = "https://api.worldbank.org/v2/country/ZW/indicator/AG.LND.FRST.K2?format=json&per_page=100&date=1960:2030"

EMA_URL = "https://www.ema.co.zw/"
EMA_PDF = "https://www.ema.co.zw/wp-content/uploads/Environment_Status.pdf"


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


def fetch_worldbank_environment() -> pd.DataFrame:
    co2 = _fetch_wdi(WDI_CO2, "co2_per_capita_t")
    forest = _fetch_wdi(WDI_FOREST, "forest_pct")
    pm25 = _fetch_wdi(WDI_PM25, "pm25_ug_m3")
    forest_km2 = _fetch_wdi(WDI_FOREST_KM2, "forest_km2")
    dfs = [d for d in (co2, forest, pm25, forest_km2) if not d.empty]
    if not dfs:
        return pd.DataFrame(columns=["date", "co2_per_capita_t", "forest_pct", "pm25_ug_m3", "forest_km2", "source"])
    out = dfs[0]
    for df in dfs[1:]:
        out = out.merge(df, on="date", how="outer", suffixes=("", "_y"))
        out["source"] = out["source"].fillna(out["source_y"])
        out = out.drop(columns=[c for c in out.columns if c.endswith("_y")])
    out = out.sort_values("date").reset_index(drop=True)
    out["source"] = "World Bank WDI"
    return out


def fetch_ema_html(raw_dir: Path | None = None) -> pd.DataFrame:
    tables = fetch_html_tables(EMA_URL, match="Environment|Forest|Emission|Pollution|Dam")
    rows = []
    for tbl in tables:
        rows.append({"raw": tbl.head(2).to_string(), "source": "EMA HTML"})
    df = pd.DataFrame(rows)
    log.info("EMA HTML: %d tables", len(df))
    return df


def fetch_environment_all(raw_dir: Path | None = None) -> dict[str, pd.DataFrame]:
    wdi = fetch_worldbank_environment()
    html = fetch_ema_html(raw_dir)
    try:
        base = raw_dir or RAW_DIR
        pdf_path = Path(base) / "ema_status.pdf"
        download_pdf(EMA_PDF, pdf_path)
        tables = extract_pdf_tables(pdf_path, pages="1-2")
        log.info("EMA PDF: %d tables", len(tables))
    except Exception as e:
        log.warning("EMA PDF failed: %s", e)
    return {"annual": wdi, "ema": html}
