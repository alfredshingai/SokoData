"""Fetch agriculture data for a country.

* World Bank WDI (open JSON, CC BY-4.0) - AG.PRD.FOOD.XD, AG.YLD.CREL.KG, AG.LND.AGRI.ZS, AG.PRD.CROP.XD
  Annual, 1960-present, stable fallback.
* FAO FAOSTAT API (open JSON) - crops and livestock QCL, fallback if WDI gaps.
* Country-specific scrapers (Agritex/ZIMSTAT for Zimbabwe) - degrade gracefully.
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


def fetch_worldbank_agriculture(country: str = "ZW") -> pd.DataFrame:
    yld = _fetch_wdi_indicator("AG.YLD.CREL.KG", "cereal_yield_kg_ha", country)
    gdp = _fetch_wdi_indicator("NV.AGR.TOTL.ZS", "agri_gdp_pct", country)
    food = _fetch_wdi_indicator("AG.PRD.FOOD.XD", "food_prod_idx", country)
    crop = _fetch_wdi_indicator("AG.PRD.CROP.XD", "crop_prod_idx", country)
    dfs = [d for d in (yld, gdp, food, crop) if not d.empty]
    if not dfs:
        return pd.DataFrame(columns=["date", "cereal_yield_kg_ha", "agri_gdp_pct", "food_prod_idx", "crop_prod_idx", "source"])
    out = dfs[0]
    for df in dfs[1:]:
        out = out.merge(df, on="date", how="outer", suffixes=("", "_y"))
        out["source"] = out["source"].fillna(out["source_y"])
        out = out.drop(columns=[c for c in out.columns if c.endswith("_y")])
    out = out.sort_values("date").reset_index(drop=True)
    out["source"] = f"World Bank WDI ({country})"
    return out


def fetch_fao_maize(country: str = "ZW") -> pd.DataFrame:
    """Fetch maize production from FAO FAOSTAT. Area code 181 = Zimbabwe, 114 = Kenya, etc."""
    # Map ISO3 to FAO area codes
    fao_area_codes = {"ZW": 181, "KE": 114}
    area = fao_area_codes.get(country, 181)
    url = f"https://fenixservices.fao.org/faostat/api/v1/en/data/QCL?area={area}&item=56&element=5510&show_codes=false"
    try:
        data = fetch_json(url)
        rows = data.get("data", []) if isinstance(data, dict) else []
        out = []
        for r in rows:
            try:
                year = r.get("Year") or r.get("year")
                val = r.get("Value") or r.get("value")
                if year and val:
                    out.append({"date": f"{year}-12-31", "maize_tonnes": float(str(val).replace(",", "")), "source": f"FAO FAOSTAT QCL ({country})"})
            except Exception:
                continue
        df = pd.DataFrame(out)
        if not df.empty:
            df["date"] = pd.to_datetime(df["date"])
        log.info("FAO maize for %s: %d rows", country, len(df))
        return df
    except Exception as e:
        log.warning("FAO fetch failed: %s", e)
        return pd.DataFrame(columns=["date", "maize_tonnes", "source"])


def fetch_agritex_html(raw_dir: Path | None = None) -> pd.DataFrame:
    """Zimbabwe-specific Agritex scraper."""
    tables = fetch_html_tables("https://www.agrismis.gov.zw/", match="Maize|Wheat|Crop|Harvest")
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


def fetch_agriculture_all(country: str = "ZW", raw_dir: Path | None = None) -> dict[str, pd.DataFrame]:
    wdi = fetch_worldbank_agriculture(country)
    fao = fetch_fao_maize(country)
    # Zimbabwe-specific scrapers
    if country == "ZW":
        html = fetch_agritex_html(raw_dir)
        pdf = pd.DataFrame()
        try:
            base = raw_dir or RAW_DIR
            pdf_path = Path(base) / "zimstat_agri.pdf"
            download_pdf("https://www.zimstat.co.zw/wp-content/uploads/publications/Agriculture/Crops.pdf", pdf_path)
            tables = extract_pdf_tables(pdf_path, pages="1-3")
            log.info("ZIMSTAT agri PDF: %d tables", len(tables))
        except Exception as e:
            log.warning("ZIMSTAT agri PDF failed: %s", e)
    else:
        html = pd.DataFrame()
    return {"annual": wdi, "fao_maize": fao, "agritex": html}