"""Fetch health data for a country.

* World Bank WDI (open JSON, CC BY-4.0) - SP.DYN.IMRT.IN, SH.DYN.MORT, SH.IMM.MEAS, SH.MED.BEDS.ZS, SH.XPD.CHEX.GD.ZS
* WHO GHO API fallback (open JSON) - optional
* Country-specific MoH scrapers - degrade gracefully.
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


def fetch_worldbank_health(country: str = "ZW") -> pd.DataFrame:
    imrt = _fetch_wdi_indicator("SP.DYN.IMRT.IN", "infant_mort_per_1k", country)
    u5 = _fetch_wdi_indicator("SH.DYN.MORT", "under5_mort_per_1k", country)
    meas = _fetch_wdi_indicator("SH.IMM.MEAS", "measles_imm_pct", country)
    xpd = _fetch_wdi_indicator("SH.XPD.CHEX.GD.ZS", "health_xpd_pct_gdp", country)
    dfs = [d for d in (imrt, u5, meas, xpd) if not d.empty]
    if not dfs:
        return pd.DataFrame(columns=["date", "infant_mort_per_1k", "under5_mort_per_1k", "measles_imm_pct", "health_xpd_pct_gdp", "source"])
    out = dfs[0]
    for df in dfs[1:]:
        out = out.merge(df, on="date", how="outer", suffixes=("", "_y"))
        out["source"] = out["source"].fillna(out["source_y"])
        out = out.drop(columns=[c for c in out.columns if c.endswith("_y")])
    out = out.sort_values("date").reset_index(drop=True)
    out["source"] = f"World Bank WDI ({country})"
    return out


def fetch_moh_html(raw_dir: Path | None = None) -> pd.DataFrame:
    """Zimbabwe-specific MoHCC scraper."""
    tables = fetch_html_tables("https://www.mohcc.gov.zw/", match="Cholera|Malaria|Health|Cases")
    rows = []
    for tbl in tables:
        rows.append({"raw": tbl.head(2).to_string(), "source": "MoHCC HTML"})
    df = pd.DataFrame(rows)
    log.info("MoHCC HTML: %d tables", len(df))
    return df


def fetch_health_all(country: str = "ZW", raw_dir: Path | None = None) -> dict[str, pd.DataFrame]:
    wdi = fetch_worldbank_health(country)
    # Zimbabwe-specific MoHCC scraper
    if country == "ZW":
        html = fetch_moh_html(raw_dir)
        # Try MoH PDF
        try:
            base = raw_dir or RAW_DIR
            pdf_path = Path(base) / "moh_bulletin.pdf"
            download_pdf("https://www.mohcc.gov.zw/wp-content/uploads/Health_Bulletin.pdf", pdf_path)
            tables = extract_pdf_tables(pdf_path, pages="1-2")
            log.info("MoH PDF: %d tables", len(tables))
        except Exception as e:
            log.warning("MoH PDF failed: %s", e)
    else:
        html = pd.DataFrame()
    return {"annual": wdi, "moh": html}