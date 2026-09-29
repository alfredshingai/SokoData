"""Fetch governance data for a country.

* World Bank WDI (open JSON, CC BY-4.0) - IQ.CPA.PROP.XQ (property rights),
  IQ.CPA.TRAN.XQ (transparency/corruption), SG.GEN.PARL.ZS (women in parliament),
  MS.MIL.XPND.GD.ZS (military expenditure), GC.DOD.TOTL.GD.ZS (central gov debt).
  Note: classic WGI CC.EST/GE.EST were archived from WDI - these CPIA/WDI
  proxies are the working fallback.
* Country-specific ZEC/Afrobarometer scrapers - degrade gracefully.
"""

import logging
from pathlib import Path

import pandas as pd

from sokodata.config import RAW_DIR, get_wb_country
from sokodata.core.fetch import download_pdf, extract_pdf_tables, fetch_html_tables, fetch_json

log = logging.getLogger(__name__)


def _fetch_wdi_indicator(indicator: str, col: str, country: str) -> pd.DataFrame:
    wb_country = get_wb_country(country)
    url = f"https://api.worldbank.org/v2/country/{wb_country}/indicator/{indicator}?format=json&per_page=100&date=2005:2030"
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


def fetch_worldbank_governance(country: str = "ZW") -> pd.DataFrame:
    prop = _fetch_wdi_indicator("IQ.CPA.PROP.XQ", "property_rights_cpia", country)
    tran = _fetch_wdi_indicator("IQ.CPA.TRAN.XQ", "transparency_cpia", country)
    women = _fetch_wdi_indicator("SG.GEN.PARL.ZS", "women_parliament_pct", country)
    mil = _fetch_wdi_indicator("MS.MIL.XPND.GD.ZS", "military_xpd_pct_gdp", country)
    debt = _fetch_wdi_indicator("GC.DOD.TOTL.GD.ZS", "gov_debt_pct_gdp", country)
    dfs = [d for d in (prop, tran, women, mil, debt) if not d.empty]
    if not dfs:
        return pd.DataFrame(columns=["date", "property_rights_cpia", "transparency_cpia", "women_parliament_pct", "military_xpd_pct_gdp", "gov_debt_pct_gdp", "source"])
    out = dfs[0]
    for df in dfs[1:]:
        out = out.merge(df, on="date", how="outer", suffixes=("", "_y"))
        out["source"] = out["source"].fillna(out["source_y"])
        out = out.drop(columns=[c for c in out.columns if c.endswith("_y")])
    out = out.sort_values("date").reset_index(drop=True)
    out["source"] = f"World Bank WDI (CPIA/WDI governance proxies) ({country})"
    return out


def fetch_zec_html(raw_dir: Path | None = None) -> pd.DataFrame:
    """Zimbabwe-specific ZEC/Afrobarometer scraper."""
    tables = fetch_html_tables("https://www.zec.org.zw/", match="Election|Results|Votes|Constituency|Ward")
    rows = []
    for tbl in tables:
        rows.append({"raw": tbl.head(2).to_string(), "source": "ZEC HTML"})
    try:
        afro = fetch_html_tables("https://www.afrobarometer.org/countries/zimbabwe/", match="Zimbabwe|Survey|Democracy|Trust")
        for tbl in afro:
            rows.append({"raw": tbl.head(2).to_string(), "source": "Afrobarometer HTML"})
    except Exception:
        pass
    df = pd.DataFrame(rows)
    log.info("Governance HTML: %d tables", len(df))
    return df


def fetch_governance_all(country: str = "ZW", raw_dir: Path | None = None) -> dict[str, pd.DataFrame]:
    wdi = fetch_worldbank_governance(country)
    if country == "ZW":
        html = fetch_zec_html(raw_dir)
        try:
            base = raw_dir or RAW_DIR
            pdf_path = Path(base) / "zec_results.pdf"
            download_pdf("https://www.zec.org.zw/wp-content/uploads/Election_Results.pdf", pdf_path)
            tables = extract_pdf_tables(pdf_path, pages="1-2")
            log.info("ZEC PDF: %d tables", len(tables))
        except Exception as e:
            log.warning("ZEC PDF failed: %s", e)
    else:
        html = pd.DataFrame()
    return {"annual": wdi, "zec": html}