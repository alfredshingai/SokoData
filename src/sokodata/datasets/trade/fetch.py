"""Fetch trade data for a country.

* World Bank WDI (open JSON, CC BY-4.0) - NE.EXP.GNFS.ZS, NE.IMP.GNFS.ZS,
  TX.VAL.MRCH.CD.WT, TM.VAL.MRCH.CD.WT
* UN Comtrade API hook - optional
* Country-specific ZimTrade/ZIMSTAT scrapers - degrade gracefully.
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


def fetch_worldbank_trade(country: str = "ZW") -> pd.DataFrame:
    exp = _fetch_wdi_indicator("NE.EXP.GNFS.ZS", "exports_pct_gdp", country)
    imp = _fetch_wdi_indicator("NE.IMP.GNFS.ZS", "imports_pct_gdp", country)
    merch_exp = _fetch_wdi_indicator("TX.VAL.MRCH.CD.WT", "merch_exports_usd", country)
    merch_imp = _fetch_wdi_indicator("TM.VAL.MRCH.CD.WT", "merch_imports_usd", country)
    dfs = [d for d in (exp, imp, merch_exp, merch_imp) if not d.empty]
    if not dfs:
        return pd.DataFrame(columns=["date", "exports_pct_gdp", "imports_pct_gdp", "merch_exports_usd", "merch_imports_usd", "source"])
    out = dfs[0]
    for df in dfs[1:]:
        out = out.merge(df, on="date", how="outer", suffixes=("", "_y"))
        out["source"] = out["source"].fillna(out["source_y"])
        out = out.drop(columns=[c for c in out.columns if c.endswith("_y")])
    out = out.sort_values("date").reset_index(drop=True)
    out["source"] = f"World Bank WDI ({country})"
    return out


def fetch_zimtrade_html(raw_dir: Path | None = None) -> pd.DataFrame:
    """Zimbabwe-specific ZimTrade scraper."""
    tables = fetch_html_tables("https://www.tradezimbabwe.com/", match="Export|Import|Tobacco|Gold|Trade")
    rows = []
    for tbl in tables:
        rows.append({"raw": tbl.head(2).to_string(), "source": "ZimTrade HTML"})
    df = pd.DataFrame(rows)
    log.info("Trade HTML: %d tables", len(df))
    return df


def fetch_trade_all(country: str = "ZW", raw_dir: Path | None = None) -> dict[str, pd.DataFrame]:
    wdi = fetch_worldbank_trade(country)
    if country == "ZW":
        html = fetch_zimtrade_html(raw_dir)
        try:
            base = raw_dir or RAW_DIR
            pdf_path = Path(base) / "zimstat_trade.pdf"
            download_pdf("https://www.zimstat.co.zw/wp-content/uploads/publications/Economic/Trade/Monthly_Trade.pdf", pdf_path)
            tables = extract_pdf_tables(pdf_path, pages="1-2")
            log.info("ZIMSTAT trade PDF: %d tables", len(tables))
        except Exception as e:
            log.warning("ZIMSTAT trade PDF failed: %s", e)
    else:
        html = pd.DataFrame()
    return {"annual": wdi, "zimtrade": html}