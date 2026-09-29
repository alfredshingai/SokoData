"""Fetch energy data for a country.

* World Bank WDI (open JSON, CC BY-4.0) - EG.ELC.ACCS.ZS, EG.USE.ELEC.KH.PC, EG.USE.COMM.GD.PP.KD, EG.IMP.CONS.ZS
* IEA / IRENA fallback optional
* Country-specific ZESA/ZERA scrapers - degrade gracefully.
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


def fetch_worldbank_energy(country: str = "ZW") -> pd.DataFrame:
    accs = _fetch_wdi_indicator("EG.ELC.ACCS.ZS", "elec_access_pct", country)
    use = _fetch_wdi_indicator("EG.USE.ELEC.KH.PC", "elec_use_kwh_pc", country)
    imp = _fetch_wdi_indicator("EG.IMP.CONS.ZS", "energy_imports_pct", country)
    renew = _fetch_wdi_indicator("EG.FEC.RNEW.ZS", "renewable_pct", country)
    dfs = [d for d in (accs, use, imp, renew) if not d.empty]
    if not dfs:
        return pd.DataFrame(columns=["date", "elec_access_pct", "elec_use_kwh_pc", "energy_imports_pct", "renewable_pct", "source"])
    out = dfs[0]
    for df in dfs[1:]:
        out = out.merge(df, on="date", how="outer", suffixes=("", "_y"))
        out["source"] = out["source"].fillna(out["source_y"])
        out = out.drop(columns=[c for c in out.columns if c.endswith("_y")])
    out = out.sort_values("date").reset_index(drop=True)
    out["source"] = f"World Bank WDI ({country})"
    return out


def fetch_zesa_html(raw_dir: Path | None = None) -> pd.DataFrame:
    """Zimbabwe-specific ZESA scraper."""
    tables = fetch_html_tables("https://www.zesa.co.zw/", match="Load|Shedding|Schedule|Power|Outage")
    rows = []
    for tbl in tables:
        rows.append({"raw": tbl.head(2).to_string(), "source": "ZESA HTML"})
    df = pd.DataFrame(rows)
    log.info("ZESA HTML: %d tables", len(df))
    return df


def fetch_energy_all(country: str = "ZW", raw_dir: Path | None = None) -> dict[str, pd.DataFrame]:
    wdi = fetch_worldbank_energy(country)
    # Zimbabwe-specific ZESA scraper
    if country == "ZW":
        html = fetch_zesa_html(raw_dir)
        try:
            base = raw_dir or RAW_DIR
            pdf_path = Path(base) / "zesa_schedule.pdf"
            download_pdf("https://www.zesa.co.zw/wp-content/uploads/Load_Shedding_Schedule.pdf", pdf_path)
            tables = extract_pdf_tables(pdf_path, pages="1-2")
            log.info("ZESA PDF: %d tables", len(tables))
        except Exception as e:
            log.warning("ZESA PDF failed: %s", e)
        # also try ZERA fuel schedule (reused in economy but also energy)
        try:
            fetch_html_tables("https://www.zera.co.zw/", match="Fuel|Diesel|Petrol")
        except Exception:
            pass
    else:
        html = pd.DataFrame()
    return {"annual": wdi, "zesa": html}