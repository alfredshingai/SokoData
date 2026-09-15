"""Fetch transport data for Zimbabwe.

* World Bank WDI (open JSON, CC BY-4.0) - IS.AIR.DPRT, IS.RRS.TOTL.KM,
  IS.ROD.TOTL.KM, IT.NET.USER.ZS (connectivity proxy)
* Ministry of Transport / NRZ / CAAZ HTML/PDF scraping - no API,
  degrades gracefully.
"""

import logging
from pathlib import Path

import pandas as pd

from sokodata.config import RAW_DIR
from sokodata.core.fetch import download_pdf, extract_pdf_tables, fetch_html_tables, fetch_json

log = logging.getLogger(__name__)

WDI_AIR = "https://api.worldbank.org/v2/country/ZW/indicator/IS.AIR.DPRT?format=json&per_page=100&date=1960:2030"
WDI_RAIL = "https://api.worldbank.org/v2/country/ZW/indicator/IS.RRS.TOTL.KM?format=json&per_page=100&date=1960:2030"
WDI_ROAD = "https://api.worldbank.org/v2/country/ZW/indicator/IS.ROD.TOTL.KM?format=json&per_page=100&date=1960:2030"
WDI_INTERNET = "https://api.worldbank.org/v2/country/ZW/indicator/IT.NET.USER.ZS?format=json&per_page=100&date=1960:2030"

MOT_URL = "https://www.transport.gov.zw/"
MOT_PDF = "https://www.transport.gov.zw/wp-content/uploads/Transport_Statistics.pdf"


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


def fetch_worldbank_transport() -> pd.DataFrame:
    air = _fetch_wdi(WDI_AIR, "air_departures")
    rail = _fetch_wdi(WDI_RAIL, "rail_km")
    road = _fetch_wdi(WDI_ROAD, "road_km")
    net = _fetch_wdi(WDI_INTERNET, "internet_use_pct")
    dfs = [d for d in (air, rail, road, net) if not d.empty]
    if not dfs:
        return pd.DataFrame(columns=["date", "air_departures", "rail_km", "road_km", "internet_use_pct", "source"])
    out = dfs[0]
    for df in dfs[1:]:
        out = out.merge(df, on="date", how="outer", suffixes=("", "_y"))
        out["source"] = out["source"].fillna(out["source_y"])
        out = out.drop(columns=[c for c in out.columns if c.endswith("_y")])
    out = out.sort_values("date").reset_index(drop=True)
    out["source"] = "World Bank WDI"
    return out


def fetch_mot_html(raw_dir: Path | None = None) -> pd.DataFrame:
    tables = fetch_html_tables(MOT_URL, match="Road|Rail|Air|Traffic|Vehicle|NRZ")
    rows = []
    for tbl in tables:
        rows.append({"raw": tbl.head(2).to_string(), "source": "MoT HTML"})
    df = pd.DataFrame(rows)
    log.info("MoT HTML: %d tables", len(df))
    return df


def fetch_transport_all(raw_dir: Path | None = None) -> dict[str, pd.DataFrame]:
    wdi = fetch_worldbank_transport()
    html = fetch_mot_html(raw_dir)
    try:
        base = raw_dir or RAW_DIR
        pdf_path = Path(base) / "mot_stats.pdf"
        download_pdf(MOT_PDF, pdf_path)
        tables = extract_pdf_tables(pdf_path, pages="1-2")
        log.info("MoT PDF: %d tables", len(tables))
    except Exception as e:
        log.warning("MoT PDF failed: %s", e)
    return {"annual": wdi, "mot": html}
