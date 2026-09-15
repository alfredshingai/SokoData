"""Fetch ICT data for Zimbabwe.

* World Bank WDI (open JSON, CC BY-4.0) - IT.NET.USER.ZS, IT.CEL.SETS.P2,
  IT.NET.BBND.P2, IT.MLT.MAIN.P2
* ITU / POTRAZ HTML/PDF scraping - telecom subscriptions, no API, degrades gracefully.
"""

import logging
from pathlib import Path

import pandas as pd

from sokodata.config import RAW_DIR
from sokodata.core.fetch import download_pdf, extract_pdf_tables, fetch_html_tables, fetch_json

log = logging.getLogger(__name__)

WDI_NET = "https://api.worldbank.org/v2/country/ZW/indicator/IT.NET.USER.ZS?format=json&per_page=100&date=1990:2030"
WDI_CELL = "https://api.worldbank.org/v2/country/ZW/indicator/IT.CEL.SETS.P2?format=json&per_page=100&date=1990:2030"
WDI_BB = "https://api.worldbank.org/v2/country/ZW/indicator/IT.NET.BBND.P2?format=json&per_page=100&date=2000:2030"
WDI_TEL = "https://api.worldbank.org/v2/country/ZW/indicator/IT.MLT.MAIN.P2?format=json&per_page=100&date=1960:2030"

POTRAZ_URL = "https://www.potraz.gov.zw/"
POTRAZ_PDF = "https://www.potraz.gov.zw/wp-content/uploads/Telecom_Statistics.pdf"


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


def fetch_worldbank_ict() -> pd.DataFrame:
    net = _fetch_wdi(WDI_NET, "internet_users_pct")
    cell = _fetch_wdi(WDI_CELL, "cell_subs_per_100")
    bb = _fetch_wdi(WDI_BB, "fixed_broadband_per_100")
    tel = _fetch_wdi(WDI_TEL, "tel_lines_per_100")
    dfs = [d for d in (net, cell, bb, tel) if not d.empty]
    if not dfs:
        return pd.DataFrame(columns=["date", "internet_users_pct", "cell_subs_per_100", "fixed_broadband_per_100", "tel_lines_per_100", "source"])
    out = dfs[0]
    for df in dfs[1:]:
        out = out.merge(df, on="date", how="outer", suffixes=("", "_y"))
        out["source"] = out["source"].fillna(out["source_y"])
        out = out.drop(columns=[c for c in out.columns if c.endswith("_y")])
    out = out.sort_values("date").reset_index(drop=True)
    out["source"] = "World Bank WDI"
    return out


def fetch_potraz_html(raw_dir: Path | None = None) -> pd.DataFrame:
    tables = fetch_html_tables(POTRAZ_URL, match="Telecom|Mobile|Internet|Broadband|Subscriber")
    rows = []
    for tbl in tables:
        rows.append({"raw": tbl.head(2).to_string(), "source": "POTRAZ HTML"})
    df = pd.DataFrame(rows)
    log.info("POTRAZ HTML: %d tables", len(df))
    return df


def fetch_ict_all(raw_dir: Path | None = None) -> dict[str, pd.DataFrame]:
    wdi = fetch_worldbank_ict()
    html = fetch_potraz_html(raw_dir)
    try:
        base = raw_dir or RAW_DIR
        pdf_path = Path(base) / "potraz_stats.pdf"
        download_pdf(POTRAZ_PDF, pdf_path)
        tables = extract_pdf_tables(pdf_path, pages="1-2")
        log.info("POTRAZ PDF: %d tables", len(tables))
    except Exception as e:
        log.warning("POTRAZ PDF failed: %s", e)
    return {"annual": wdi, "potraz": html}
