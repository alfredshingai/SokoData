"""Fetch economy data for a country.

Strategy - per SokoData commons principle "where there's no API, scrape;
where there's an API, use it":

* World Bank WDI API (open JSON, CC BY-4.0) - CPI/inflation, FX, stable fallback
* Country-specific scrapers (RBZ, ZIMSTAT, ZERA for Zimbabwe) - with simple retries
"""

import logging
import time
from pathlib import Path

import pandas as pd

from sokodata.config import RAW_DIR, get_wb_country
from sokodata.core.fetch import download_pdf, extract_pdf_tables, fetch_html_tables, fetch_html_text, fetch_json, parse_fuel_text

log = logging.getLogger(__name__)

# Zimbabwe-specific scraper URLs (only used for ZW)
RBZ_RATES_URL = "https://www.rbz.co.zw/market-rates"
ZERA_FUEL_URL = "https://www.zera.co.zw/"
ZIMSTAT_CPI_URL = "https://www.zimstat.co.zw/wp-content/uploads/publications/Economic/Price/CPI.pdf"


def _fetch_wdi_indicator(indicator: str, country: str) -> pd.DataFrame:
    wb_country = get_wb_country(country)
    url = f"https://api.worldbank.org/v2/country/{wb_country}/indicator/{indicator}?format=json&per_page=100&date=2010:2030"
    try:
        data = fetch_json(url)
        recs = data[1] if isinstance(data, list) and len(data) > 1 else []
        rows = []
        for r in recs:
            if r.get("value") is None or r.get("date") is None:
                continue
            rows.append({"date": f"{r['date']}-12-31", "value": float(r["value"]), "source": f"WDI {indicator} ({country})"})
        df = pd.DataFrame(rows)
        if not df.empty:
            df["date"] = pd.to_datetime(df["date"])
        log.info("WDI %s for %s: %d points", indicator, country, len(df))
        return df
    except Exception as e:
        log.warning("WDI %s for %s failed: %s", indicator, country, e)
        return pd.DataFrame(columns=["date", "value", "source"])


def fetch_worldbank_cpi(country: str = "ZW") -> pd.DataFrame:
    df = _fetch_wdi_indicator("FP.CPI.TOTL.ZG", country)
    if not df.empty:
        df = df.rename(columns={"value": "inflation_yoy"})
        df["cpi"] = None
        df["inflation_mom"] = None
        df["source"] = f"World Bank WDI FP.CPI.TOTL.ZG ({country})"
    return df


def fetch_worldbank_fx(country: str = "ZW") -> pd.DataFrame:
    df = _fetch_wdi_indicator("PA.NUS.FCRF", country)
    if not df.empty:
        df = df.rename(columns={"value": "rate"})
        df["source"] = f"World Bank FX ({country})"
    return df


def _scrape_rbz_rates_with_retry(max_attempts: int = 3) -> pd.DataFrame:
    """Scrape RBZ interbank ZiG/USD with retries."""
    for attempt in range(1, max_attempts + 1):
        try:
            tables = fetch_html_tables(RBZ_RATES_URL, match="ZiG|USD|Interbank")
            rows = []
            for tbl in tables:
                tbl.columns = [str(c).strip().lower() for c in tbl.columns]
                for _, r in tbl.iterrows():
                    vals = [str(v) for v in r.values]
                    date_candidate = None
                    rate_candidate = None
                    for v in vals:
                        if not date_candidate and any(ch in v for ch in ("/", "-")) and len(v) >= 8:
                            date_candidate = v
                        if not rate_candidate:
                            try:
                                nv = float(str(v).replace(",", ""))
                                if 5 < nv < 100000:
                                    rate_candidate = nv
                            except Exception:
                                pass
                    if date_candidate and rate_candidate:
                        rows.append({"date": date_candidate, "rate": rate_candidate, "source": "RBZ scrape"})
            if rows:
                df = pd.DataFrame(rows)
                df["date"] = pd.to_datetime(df["date"], errors="coerce")
                df = df.dropna(subset=["date"])
                return df
            # Fallback: regex on raw HTML
            html = fetch_html_text(RBZ_RATES_URL)
            if html:
                import re
                for m in re.finditer(r"ZiG[^\d]*(\d+\.?\d*)\s*(?:per\s*)?USD", html, re.I):
                    rows.append({"date": str(date.today()), "rate": float(m.group(1)), "source": "RBZ regex"})
            if rows:
                df = pd.DataFrame(rows)
                df["date"] = pd.to_datetime(df["date"], errors="coerce")
                df = df.dropna(subset=["date"])
                return df
            return pd.DataFrame()
        except Exception as e:
            log.warning("RBZ scrape attempt %d/%d failed: %s", attempt, max_attempts, e)
            if attempt < max_attempts:
                time.sleep(2 ** attempt)  # exponential backoff
    return pd.DataFrame()


def _scrape_zera_fuel_with_retry(max_attempts: int = 3) -> pd.DataFrame:
    """Scrape ZERA fuel prices with retries."""
    for attempt in range(1, max_attempts + 1):
        try:
            tables = fetch_html_tables(ZERA_FUEL_URL, match="Diesel|Petrol|Fuel")
            rows = []
            for tbl in tables:
                tbl.columns = [str(c).strip() for c in tbl.columns]
                tbl_str = tbl.to_string().lower()
                if "diesel" in tbl_str or "petrol" in tbl_str:
                    for _, r in tbl.iterrows():
                        vals = [str(v) for v in r.values]
                        for i, v in enumerate(vals):
                            vl = v.lower()
                            if "diesel" in vl or "petrol" in vl:
                                for nv in vals[i + 1 :]:
                                    try:
                                        price = float(str(nv).replace(",", "").replace("$", "").strip())
                                        if 0.5 < price < 10:
                                            rows.append({
                                                "date": str(date.today()),
                                                "fuel_type": v.strip(),
                                                "price": price,
                                                "currency": "USD",
                                                "source": "ZERA HTML table",
                                            })
                                            break
                                    except Exception:
                                        continue
            if not rows:
                html = fetch_html_text(ZERA_FUEL_URL)
                if html:
                    for item in parse_fuel_text(html):
                        rows.append({
                            "date": str(date.today()),
                            "fuel_type": item["fuel"],
                            "price": item["price"],
                            "currency": "USD",
                            "source": "ZERA HTML regex",
                        })
            if not rows:
                try:
                    pdf_path = RAW_DIR / "zera_fuel.pdf"
                    download_pdf(ZERA_FUEL_URL, pdf_path)
                    for tbl in extract_pdf_tables(pdf_path):
                        tbl.columns = [str(c).strip().lower() for c in tbl.columns]
                        log.info("ZERA PDF table cols: %s", list(tbl.columns))
                except Exception as e:
                    log.warning("ZERA PDF fallback failed: %s", e)
            if rows:
                df = pd.DataFrame(rows)
                df["date"] = pd.to_datetime(df["date"], errors="coerce")
                return df
            return pd.DataFrame()
        except Exception as e:
            log.warning("ZERA scrape attempt %d/%d failed: %s", attempt, max_attempts, e)
            if attempt < max_attempts:
                time.sleep(2 ** attempt)
    return pd.DataFrame()


def _scrape_zimstat_cpi_with_retry(max_attempts: int = 3) -> pd.DataFrame:
    """Attempt to extract CPI from ZIMSTAT PDF bulletin with retries."""
    for attempt in range(1, max_attempts + 1):
        try:
            pdf_path = RAW_DIR / "zimstat_cpi.pdf"
            download_pdf("https://www.zimstat.co.zw/wp-content/uploads/publications/Economic/Price/CPI.pdf", pdf_path)
            tables = extract_pdf_tables(pdf_path, pages="1-3")
            rows = []
            for tbl in tables:
                tbl.columns = [str(c).strip().lower() for c in tbl.columns]
                if any("cpi" in c or "inflation" in c or "index" in c for c in tbl.columns):
                    for _, r in tbl.iterrows():
                        rows.append({**{k: v for k, v in r.items()}, "source": "ZIMSTAT PDF"})
            df = pd.DataFrame(rows)
            log.info("ZIMSTAT PDF: %d rows from %d tables", len(df), len(tables))
            return df
        except Exception as e:
            log.warning("ZIMSTAT PDF attempt %d/%d failed: %s", attempt, max_attempts, e)
            if attempt < max_attempts:
                time.sleep(2 ** attempt)
    return pd.DataFrame(columns=["date", "cpi", "inflation_yoy", "inflation_mom", "source"])


def fetch_economy_all(country: str = "ZW", raw_dir: Path | None = None) -> dict[str, pd.DataFrame]:
    """Fetch all economy sources for a country - WDI API + country-specific scrapers with retries.

    For Zimbabwe: WDI + RBZ/ZERA/ZIMSTAT scrapers with retries
    For other countries: WDI only (scrapers can be added per-country)
    """
    base = raw_dir or RAW_DIR
    cpi_wdi = fetch_worldbank_cpi(country)

    # Zimbabwe-specific scrapers with retries
    cpi_pdf = pd.DataFrame()
    rates = pd.DataFrame()
    fuel = pd.DataFrame()

    if country == "ZW":
        rates = _scrape_rbz_rates_with_retry()
        fuel = _scrape_zera_fuel_with_retry()
        cpi_pdf = _scrape_zimstat_cpi_with_retry()
    else:
        pass

    # Combine CPI sources
    if not cpi_pdf.empty:
        cpi = pd.concat([cpi_wdi, cpi_pdf], ignore_index=True)
    else:
        cpi = cpi_wdi

    # Add WDI FX as fallback
    fx_wdi = fetch_worldbank_fx(country)
    if not fx_wdi.empty:
        if not rates.empty:
            rates = pd.concat([rates, fx_wdi], ignore_index=True)
        else:
            rates = fx_wdi

    return {"rates": rates, "cpi": cpi, "fuel": fuel}