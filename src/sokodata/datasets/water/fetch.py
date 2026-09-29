"""Fetch water data for a country.

* World Bank WDI (open JSON, CC BY-4.0) - SH.H2O.SMDW.ZS, SH.STA.SMSS.ZS,
  SH.H2O.BASW.ZS, SH.STA.BASS.ZS
* Country-specific ZINWA scraper - degrade gracefully.
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


def fetch_worldbank_water(country: str = "ZW") -> pd.DataFrame:
    safe_w = _fetch_wdi_indicator("SH.H2O.SMDW.ZS", "safe_water_pct", country)
    safe_s = _fetch_wdi_indicator("SH.STA.SMSS.ZS", "safe_sanitation_pct", country)
    basic_w = _fetch_wdi_indicator("SH.H2O.BASW.ZS", "basic_water_pct", country)
    basic_s = _fetch_wdi_indicator("SH.STA.BASS.ZS", "basic_sanitation_pct", country)
    dfs = [d for d in (safe_w, safe_s, basic_w, basic_s) if not d.empty]
    if not dfs:
        return pd.DataFrame(columns=["date", "safe_water_pct", "safe_sanitation_pct", "basic_water_pct", "basic_sanitation_pct", "source"])
    out = dfs[0]
    for df in dfs[1:]:
        out = out.merge(df, on="date", how="outer", suffixes=("", "_y"))
        out["source"] = out["source"].fillna(out["source_y"])
        out = out.drop(columns=[c for c in out.columns if c.endswith("_y")])
    out = out.sort_values("date").reset_index(drop=True)
    out["source"] = f"World Bank WDI ({country})"
    return out


def fetch_zinwa_html(raw_dir: Path | None = None) -> pd.DataFrame:
    """Zimbabwe-specific ZINWA scraper."""
    tables = fetch_html_tables("https://www.zinwa.co.zw/", match="Dam|Level|Water|Supply|Harare|Kariba")
    rows = []
    for tbl in tables:
        rows.append({"raw": tbl.head(2).to_string(), "source": "ZINWA HTML"})
    df = pd.DataFrame(rows)
    log.info("ZINWA HTML: %d tables", len(df))
    return df


def fetch_water_all(country: str = "ZW", raw_dir: Path | None = None) -> dict[str, pd.DataFrame]:
    wdi = fetch_worldbank_water(country)
    if country == "ZW":
        html = fetch_zinwa_html(raw_dir)
        try:
            base = raw_dir or RAW_DIR
            pdf_path = Path(base) / "zinwa_dams.pdf"
            download_pdf("https://www.zinwa.co.zw/wp-content/uploads/Dam_Levels.pdf", pdf_path)
            tables = extract_pdf_tables(pdf_path, pages="1-2")
            log.info("ZINWA PDF: %d tables", len(tables))
        except Exception as e:
            log.warning("ZINWA PDF failed: %s", e)
    else:
        html = pd.DataFrame()
    return {"annual": wdi, "zinwa": html}