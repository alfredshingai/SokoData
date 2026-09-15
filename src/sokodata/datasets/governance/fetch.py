"""Fetch governance data for Zimbabwe.

* World Bank WDI (open JSON, CC BY-4.0) - IQ.CPA.PROP.XQ (property rights),
  IQ.CPA.TRAN.XQ (transparency/corruption), SG.GEN.PARL.ZS (women in parliament),
  MS.MIL.XPND.GD.ZS (military expenditure), GC.DOD.TOTL.GD.ZS (central gov debt).
  Note: classic WGI CC.EST/GE.EST were archived from WDI - these CPIA/WDI
  proxies are the working fallback.
* Afrobarometer / ZEC HTML/PDF scraping - election results, surveys, no API,
  degrades gracefully.
"""

import logging
from pathlib import Path

import pandas as pd

from sokodata.config import RAW_DIR
from sokodata.core.fetch import download_pdf, extract_pdf_tables, fetch_html_tables, fetch_json

log = logging.getLogger(__name__)

WDI_PROP = "https://api.worldbank.org/v2/country/ZW/indicator/IQ.CPA.PROP.XQ?format=json&per_page=100&date=2005:2030"
WDI_TRAN = "https://api.worldbank.org/v2/country/ZW/indicator/IQ.CPA.TRAN.XQ?format=json&per_page=100&date=2005:2030"
WDI_WOMEN = "https://api.worldbank.org/v2/country/ZW/indicator/SG.GEN.PARL.ZS?format=json&per_page=100&date=1996:2030"
WDI_MIL = "https://api.worldbank.org/v2/country/ZW/indicator/MS.MIL.XPND.GD.ZS?format=json&per_page=100&date=1960:2030"
WDI_DEBT = "https://api.worldbank.org/v2/country/ZW/indicator/GC.DOD.TOTL.GD.ZS?format=json&per_page=100&date=1960:2030"

ZEC_URL = "https://www.zec.org.zw/"
AFRO_URL = "https://www.afrobarometer.org/countries/zimbabwe/"
ZEC_PDF = "https://www.zec.org.zw/wp-content/uploads/Election_Results.pdf"


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


def fetch_worldbank_governance() -> pd.DataFrame:
    prop = _fetch_wdi(WDI_PROP, "property_rights_cpia")
    tran = _fetch_wdi(WDI_TRAN, "transparency_cpia")
    women = _fetch_wdi(WDI_WOMEN, "women_parliament_pct")
    mil = _fetch_wdi(WDI_MIL, "military_xpd_pct_gdp")
    debt = _fetch_wdi(WDI_DEBT, "gov_debt_pct_gdp")
    dfs = [d for d in (prop, tran, women, mil, debt) if not d.empty]
    if not dfs:
        return pd.DataFrame(columns=["date", "property_rights_cpia", "transparency_cpia", "women_parliament_pct", "military_xpd_pct_gdp", "gov_debt_pct_gdp", "source"])
    out = dfs[0]
    for df in dfs[1:]:
        out = out.merge(df, on="date", how="outer", suffixes=("", "_y"))
        out["source"] = out["source"].fillna(out["source_y"])
        out = out.drop(columns=[c for c in out.columns if c.endswith("_y")])
    out = out.sort_values("date").reset_index(drop=True)
    out["source"] = "World Bank WDI (CPIA/WDI governance proxies)"
    return out


def fetch_zec_html(raw_dir: Path | None = None) -> pd.DataFrame:
    tables = fetch_html_tables(ZEC_URL, match="Election|Results|Votes|Constituency|Ward")
    rows = []
    for tbl in tables:
        rows.append({"raw": tbl.head(2).to_string(), "source": "ZEC HTML"})
    try:
        afro = fetch_html_tables(AFRO_URL, match="Zimbabwe|Survey|Democracy|Trust")
        for tbl in afro:
            rows.append({"raw": tbl.head(2).to_string(), "source": "Afrobarometer HTML"})
    except Exception:
        pass
    df = pd.DataFrame(rows)
    log.info("Governance HTML: %d tables", len(df))
    return df


def fetch_governance_all(raw_dir: Path | None = None) -> dict[str, pd.DataFrame]:
    wdi = fetch_worldbank_governance()
    html = fetch_zec_html(raw_dir)
    try:
        base = raw_dir or RAW_DIR
        pdf_path = Path(base) / "zec_results.pdf"
        download_pdf(ZEC_PDF, pdf_path)
        tables = extract_pdf_tables(pdf_path, pages="1-2")
        log.info("ZEC PDF: %d tables", len(tables))
    except Exception as e:
        log.warning("ZEC PDF failed: %s", e)
    return {"annual": wdi, "zec": html}
