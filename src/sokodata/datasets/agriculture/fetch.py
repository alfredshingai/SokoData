"""Fetch agriculture data for Zimbabwe.

Strategy:
* World Bank WDI (open JSON, CC BY-4.0) - AG.PRD.FOOD.XD, AG.YLD.CREL.KG, AG.LND.AGRI.ZS, AG.PRD.CROP.XD
  Annual, 1960-present, stable fallback.
* FAO FAOSTAT API (open JSON) - crops and livestock QCL, fallback if WDI gaps.
  https://fenixservices.fao.org/faostat/api/v1/en/data/QCL?area=181&item=56&element=5510
* Agritex / ZIMSTAT crop bulletins HTML/PDF scraping - seasonal planting/harvest,
  no API. Scrapers degrade gracefully via core.fetch.

All use core.fetch helpers.
"""

import logging
from pathlib import Path

import pandas as pd

from sokodata.config import RAW_DIR
from sokodata.core.fetch import download_pdf, extract_pdf_tables, fetch_html_tables, fetch_json

log = logging.getLogger(__name__)

# World Bank WDI agriculture
WDI_CEREAL_YIELD = "https://api.worldbank.org/v2/country/ZW/indicator/AG.YLD.CREL.KG?format=json&per_page=100&date=1960:2030"
WDI_AGRI_GDP = "https://api.worldbank.org/v2/country/ZW/indicator/NV.AGR.TOTL.ZS?format=json&per_page=100&date=1960:2030"
WDI_FOOD_PROD = "https://api.worldbank.org/v2/country/ZW/indicator/AG.PRD.FOOD.XD?format=json&per_page=100&date=1960:2030"
WDI_CROP_PROD = "https://api.worldbank.org/v2/country/ZW/indicator/AG.PRD.CROP.XD?format=json&per_page=100&date=1960:2030"

# FAO FAOSTAT - open, no key
FAO_QCL_MAIZE = "https://fenixservices.fao.org/faostat/api/v1/en/data/QCL?area=181&item=56&element=5510&show_codes=false"  # Maize production
AGRITEX_URL = "https://www.agrismis.gov.zw/"  # placeholder - update when Agritex publishes
ZIMSTAT_AGRI_PDF = "https://www.zimstat.co.zw/wp-content/uploads/publications/Agriculture/Crops.pdf"


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


def fetch_worldbank_agriculture() -> pd.DataFrame:
    yld = _fetch_wdi(WDI_CEREAL_YIELD, "cereal_yield_kg_ha")
    gdp = _fetch_wdi(WDI_AGRI_GDP, "agri_gdp_pct")
    food = _fetch_wdi(WDI_FOOD_PROD, "food_prod_idx")
    crop = _fetch_wdi(WDI_CROP_PROD, "crop_prod_idx")
    dfs = [d for d in (yld, gdp, food, crop) if not d.empty]
    if not dfs:
        return pd.DataFrame(columns=["date", "cereal_yield_kg_ha", "agri_gdp_pct", "food_prod_idx", "crop_prod_idx", "source"])
    out = dfs[0]
    for df in dfs[1:]:
        out = out.merge(df, on="date", how="outer", suffixes=("", "_y"))
        out["source"] = out["source"].fillna(out["source_y"])
        out = out.drop(columns=[c for c in out.columns if c.endswith("_y")])
    out = out.sort_values("date").reset_index(drop=True)
    out["source"] = "World Bank WDI"
    return out


def fetch_fao_maize() -> pd.DataFrame:
    """Fetch maize production from FAO FAOSTAT (if API reachable)."""
    try:
        data = fetch_json(FAO_QCL_MAIZE)
        # FAOSTAT returns {"data": [...]}
        rows = data.get("data", []) if isinstance(data, dict) else []
        out = []
        for r in rows:
            try:
                year = r.get("Year") or r.get("year")
                val = r.get("Value") or r.get("value")
                if year and val:
                    out.append({"date": f"{year}-12-31", "maize_tonnes": float(str(val).replace(",", "")), "source": "FAO FAOSTAT QCL"})
            except Exception:
                continue
        df = pd.DataFrame(out)
        if not df.empty:
            df["date"] = pd.to_datetime(df["date"])
        log.info("FAO maize: %d rows", len(df))
        return df
    except Exception as e:
        log.warning("FAO fetch failed: %s", e)
        return pd.DataFrame(columns=["date", "maize_tonnes", "source"])


def fetch_agritex_html(raw_dir: Path | None = None) -> pd.DataFrame:
    tables = fetch_html_tables(AGRITEX_URL, match="Maize|Wheat|Crop|Harvest")
    rows = []
    for tbl in tables:
        cols = [str(c).strip().lower() for c in tbl.columns]
        if any("maize" in c or "wheat" in c or "crop" in c for c in cols):
            for _, r in tbl.iterrows():
                vals = [str(v).strip() for v in r.values]
                rows.append({"raw": " | ".join(vals), "source": "Agritex HTML"})
    df = pd.DataFrame(rows)
    log.info("Agritex HTML: %d rows", len(df))
    return df


def fetch_agriculture_all(raw_dir: Path | None = None) -> dict[str, pd.DataFrame]:
    wdi = fetch_worldbank_agriculture()
    fao = fetch_fao_maize()
    html = fetch_agritex_html(raw_dir)
    # try ZIMSTAT agriculture PDF
    pdf = pd.DataFrame()
    try:
        base = raw_dir or RAW_DIR
        pdf_path = Path(base) / "zimstat_agri.pdf"
        download_pdf(ZIMSTAT_AGRI_PDF, pdf_path)
        tables = extract_pdf_tables(pdf_path, pages="1-3")
        log.info("ZIMSTAT agri PDF: %d tables", len(tables))
    except Exception as e:
        log.warning("ZIMSTAT agri PDF failed: %s", e)
    return {"annual": wdi, "fao_maize": fao, "agritex": html}
