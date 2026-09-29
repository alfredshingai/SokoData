"""Fetch demographics for a country.

* World Bank WDI API (open JSON, CC BY-4.0) - SP.POP.TOTL, SP.POP.GROW, SP.DYN.IMRT.IN
  Stable annual series, 1960-present, works today.
* ZIMSTAT 2022 Census HTML/PDF scraping - Zimbabwe-specific.
  For other countries, only WDI data is available.
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
        records = data[1] if isinstance(data, list) and len(data) > 1 else []
        rows = []
        for r in records:
            if r.get("value") is None or r.get("date") is None:
                continue
            rows.append({"date": f"{r['date']}-12-31", col: float(r["value"]), "source": f"WDI {indicator} ({country})"})
        df = pd.DataFrame(rows)
        if not df.empty:
            df["date"] = pd.to_datetime(df["date"])
        log.info("WDI %s for %s: %d points", indicator, country, len(df))
        return df
    except Exception as e:
        log.warning("WDI %s for %s failed: %s", indicator, country, e)
        return pd.DataFrame(columns=["date", col, "source"])


def fetch_worldbank_demographics(country: str = "ZW") -> pd.DataFrame:
    """Fetch annual population + growth + urban share from WDI for a country."""
    pop = _fetch_wdi_indicator("SP.POP.TOTL", "population", country)
    grow = _fetch_wdi_indicator("SP.POP.GROW", "pop_growth_pct", country)
    urb = _fetch_wdi_indicator("SP.URB.TOTL.IN.ZS", "urban_pct", country)
    dfs = [d for d in (pop, grow, urb) if not d.empty]
    if not dfs:
        return pd.DataFrame(columns=["date", "population", "pop_growth_pct", "urban_pct", "source"])
    out = dfs[0]
    for df in dfs[1:]:
        out = out.merge(df, on="date", how="outer", suffixes=("", "_y"))
        out["source"] = out["source"].fillna(out["source_y"])
        out = out.drop(columns=[c for c in out.columns if c.endswith("_y")])
    out = out.sort_values("date").reset_index(drop=True)
    out["source"] = f"World Bank WDI ({country})"
    return out


def fetch_zimstat_census_html(raw_dir: Path | None = None) -> pd.DataFrame:
    """Scrape ZIMSTAT 2022 census province tables via HTML.

    Returns [admin1, population, male, female, source] if tables found,
    else empty DF. Zimbabwe-specific.
    """
    tables = fetch_html_tables("https://www.zimstat.co.zw/census-2022/", match="Province|Harare|Population")
    rows = []
    for tbl in tables:
        cols = [str(c).strip().lower() for c in tbl.columns]
        if any("province" in c or "district" in c for c in cols) and any("pop" in c or "total" in c for c in cols):
            for _, r in tbl.iterrows():
                vals = [str(v).strip() for v in r.values]
                if not vals[0] or vals[0].lower() in ("total", "province", "nan"):
                    continue
                try:
                    nums = []
                    for v in vals[1:]:
                        try:
                            nums.append(float(str(v).replace(",", "")))
                        except Exception:
                            pass
                    if nums:
                        rows.append({"admin1": vals[0], "population": nums[0], "source": "ZIMSTAT HTML"})
                except Exception:
                    continue
    df = pd.DataFrame(rows)
    log.info("ZIMSTAT HTML census: %d rows", len(df))
    return df


def fetch_zimstat_census_pdf(raw_dir: Path | None = None) -> pd.DataFrame:
    base = raw_dir or RAW_DIR
    try:
        pdf_path = Path(base) / "zimstat_census2022.pdf"
        download_pdf("https://www.zimstat.co.zw/wp-content/uploads/publications/Population/Census2022_Population_Table.pdf", pdf_path)
        tables = extract_pdf_tables(pdf_path, pages="1-5")
        rows = []
        for tbl in tables:
            tbl.columns = [str(c).strip().lower() for c in tbl.columns]
            if any("province" in c or "district" in c for c in tbl.columns) and any("pop" in c for c in tbl.columns):
                for _, r in tbl.iterrows():
                    d = {k: str(v).strip() for k, v in r.items()}
                    prov = next((d[c] for c in tbl.columns if "province" in c or "district" in c), None)
                    pop = next((d[c] for c in tbl.columns if "pop" in c or "total" in c), None)
                    if prov and pop:
                        try:
                            rows.append({"admin1": prov, "population": float(pop.replace(",", "")), "source": "ZIMSTAT PDF"})
                        except Exception:
                            continue
        df = pd.DataFrame(rows)
        log.info("ZIMSTAT PDF census: %d rows from %d tables", len(df), len(tables))
        return df
    except Exception as e:
        log.warning("ZIMSTAT PDF census failed: %s", e)
        return pd.DataFrame(columns=["admin1", "population", "source"])


def fetch_demographics_all(country: str = "ZW", raw_dir: Path | None = None) -> dict[str, pd.DataFrame]:
    """Fetch all demographics sources for a country."""
    wdi = fetch_worldbank_demographics(country)
    # Zimbabwe-specific census scrapers
    if country == "ZW":
        html = fetch_zimstat_census_html(raw_dir)
        pdf = fetch_zimstat_census_pdf(raw_dir)
        census = pdf if not pdf.empty else html
    else:
        census = pd.DataFrame(columns=["admin1", "population", "source"])
    return {"annual": wdi, "census": census}