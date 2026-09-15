"""Fetch finance data for Zimbabwe.

* World Bank WDI (open JSON, CC BY-4.0) - FS.AST.DOMS.GD.ZS (domestic credit),
  BX.TRF.PWKR.CD.DT (remittances), FM.AST.CRNG.GD.ZS (bank credit), GFDD.AI.01 (accounts)
* RBZ / Bankers Association HTML/PDF scraping - no API, degrades gracefully.
"""

import logging
from pathlib import Path

import pandas as pd

from sokodata.config import RAW_DIR
from sokodata.core.fetch import download_pdf, extract_pdf_tables, fetch_html_tables, fetch_json

log = logging.getLogger(__name__)

WDI_DOM_CREDIT = "https://api.worldbank.org/v2/country/ZW/indicator/FS.AST.DOMS.GD.ZS?format=json&per_page=100&date=1960:2030"
WDI_REMIT = "https://api.worldbank.org/v2/country/ZW/indicator/BX.TRF.PWKR.CD.DT?format=json&per_page=100&date=1970:2030"
WDI_BANK_CREDIT = "https://api.worldbank.org/v2/country/ZW/indicator/FS.AST.PRVT.GD.ZS?format=json&per_page=100&date=1960:2030"
WDI_ACCOUNTS = "https://api.worldbank.org/v2/country/ZW/indicator/GFDD.AI.01?format=json&per_page=100&date=2010:2030"

RBZ_URL = "https://www.rbz.co.zw/"
RBZ_PDF = "https://www.rbz.co.zw/wp-content/uploads/Monetary_Policy.pdf"


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


def fetch_worldbank_finance() -> pd.DataFrame:
    dom = _fetch_wdi(WDI_DOM_CREDIT, "domestic_credit_pct_gdp")
    remit = _fetch_wdi(WDI_REMIT, "remittances_usd")
    bank = _fetch_wdi(WDI_BANK_CREDIT, "private_credit_pct_gdp")
    accts = _fetch_wdi(WDI_ACCOUNTS, "accounts_pct")
    dfs = [d for d in (dom, remit, bank, accts) if not d.empty]
    if not dfs:
        return pd.DataFrame(columns=["date", "domestic_credit_pct_gdp", "remittances_usd", "private_credit_pct_gdp", "accounts_pct", "source"])
    out = dfs[0]
    for df in dfs[1:]:
        out = out.merge(df, on="date", how="outer", suffixes=("", "_y"))
        out["source"] = out["source"].fillna(out["source_y"])
        out = out.drop(columns=[c for c in out.columns if c.endswith("_y")])
    out = out.sort_values("date").reset_index(drop=True)
    out["source"] = "World Bank WDI"
    return out


def fetch_rbz_html(raw_dir: Path | None = None) -> pd.DataFrame:
    tables = fetch_html_tables(RBZ_URL, match="Credit|Interest|Remittance|Finance|Monetary")
    rows = []
    for tbl in tables:
        rows.append({"raw": tbl.head(2).to_string(), "source": "RBZ HTML"})
    df = pd.DataFrame(rows)
    log.info("RBZ finance HTML: %d tables", len(df))
    return df


def fetch_finance_all(raw_dir: Path | None = None) -> dict[str, pd.DataFrame]:
    wdi = fetch_worldbank_finance()
    html = fetch_rbz_html(raw_dir)
    try:
        base = raw_dir or RAW_DIR
        pdf_path = Path(base) / "rbz_monetary.pdf"
        download_pdf(RBZ_PDF, pdf_path)
        tables = extract_pdf_tables(pdf_path, pages="1-2")
        log.info("RBZ PDF: %d tables", len(tables))
    except Exception as e:
        log.warning("RBZ PDF failed: %s", e)
    return {"annual": wdi, "rbz": html}
