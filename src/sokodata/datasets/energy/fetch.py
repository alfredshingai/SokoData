"""Fetch energy data for Zimbabwe.

* World Bank WDI (open JSON, CC BY-4.0) - EG.ELC.ACCS.ZS, EG.USE.ELEC.KH.PC, EG.USE.COMM.GD.PP.KD, EG.IMP.CONS.ZS
* IEA / IRENA fallback optional
* ZESA Holdings & ZERA HTML/PDF scraping - load-shedding schedules, fuel prices, no API, degrades gracefully.
"""

import logging
from pathlib import Path

import pandas as pd

from sokodata.config import RAW_DIR
from sokodata.core.fetch import download_pdf, extract_pdf_tables, fetch_html_tables, fetch_json

log = logging.getLogger(__name__)

WDI_ELEC_ACCESS = "https://api.worldbank.org/v2/country/ZW/indicator/EG.ELC.ACCS.ZS?format=json&per_page=100&date=1960:2030"
WDI_ELEC_USE = "https://api.worldbank.org/v2/country/ZW/indicator/EG.USE.ELEC.KH.PC?format=json&per_page=100&date=1960:2030"
WDI_ENERGY_IMP = "https://api.worldbank.org/v2/country/ZW/indicator/EG.IMP.CONS.ZS?format=json&per_page=100&date=1960:2030"
WDI_RENEW = "https://api.worldbank.org/v2/country/ZW/indicator/EG.FEC.RNEW.ZS?format=json&per_page=100&date=1960:2030"

ZESA_URL = "https://www.zesa.co.zw/"
ZERA_URL = "https://www.zera.co.zw/"
ZESA_PDF = "https://www.zesa.co.zw/wp-content/uploads/Load_Shedding_Schedule.pdf"


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


def fetch_worldbank_energy() -> pd.DataFrame:
    accs = _fetch_wdi(WDI_ELEC_ACCESS, "elec_access_pct")
    use = _fetch_wdi(WDI_ELEC_USE, "elec_use_kwh_pc")
    imp = _fetch_wdi(WDI_ENERGY_IMP, "energy_imports_pct")
    renew = _fetch_wdi(WDI_RENEW, "renewable_pct")
    dfs = [d for d in (accs, use, imp, renew) if not d.empty]
    if not dfs:
        return pd.DataFrame(columns=["date", "elec_access_pct", "elec_use_kwh_pc", "energy_imports_pct", "renewable_pct", "source"])
    out = dfs[0]
    for df in dfs[1:]:
        out = out.merge(df, on="date", how="outer", suffixes=("", "_y"))
        out["source"] = out["source"].fillna(out["source_y"])
        out = out.drop(columns=[c for c in out.columns if c.endswith("_y")])
    out = out.sort_values("date").reset_index(drop=True)
    out["source"] = "World Bank WDI"
    return out


def fetch_zesa_html(raw_dir: Path | None = None) -> pd.DataFrame:
    tables = fetch_html_tables(ZESA_URL, match="Load|Shedding|Schedule|Power|Outage")
    rows = []
    for tbl in tables:
        rows.append({"raw": tbl.head(2).to_string(), "source": "ZESA HTML"})
    df = pd.DataFrame(rows)
    log.info("ZESA HTML: %d tables", len(df))
    return df


def fetch_energy_all(raw_dir: Path | None = None) -> dict[str, pd.DataFrame]:
    wdi = fetch_worldbank_energy()
    html = fetch_zesa_html(raw_dir)
    try:
        base = raw_dir or RAW_DIR
        pdf_path = Path(base) / "zesa_schedule.pdf"
        download_pdf(ZESA_PDF, pdf_path)
        tables = extract_pdf_tables(pdf_path, pages="1-2")
        log.info("ZESA PDF: %d tables", len(tables))
    except Exception as e:
        log.warning("ZESA PDF failed: %s", e)
    # also try ZERA fuel schedule (reused in economy but also energy)
    try:
        # ZERA HTML already covered in economy, but keep hook
        fetch_html_tables(ZERA_URL, match="Fuel|Diesel|Petrol")
    except Exception:
        pass
    return {"annual": wdi, "zesa": html}
