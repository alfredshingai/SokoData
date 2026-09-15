"""Fetch economy data for Zimbabwe.

Strategy - per SokoData commons principle "where there's no API, scrape;
where there's an API, use it":

* World Bank WDI API (open JSON) - CPI/inflation for ZW, stable fallback
* RBZ website HTML scraping - ZiG/USD interbank rates (PDF/HTML table)
* ZERA website HTML/PDF scraping - weekly fuel prices (Diesel, Petrol Blend)

All scrapers use core.fetch helpers and degrade gracefully:
if HTML/PDF parsing fails, we log and return what we have (often
World Bank data) rather than failing the whole ETL.
"""

import logging
from datetime import date
from pathlib import Path

import pandas as pd

from sokodata.config import RAW_DIR
from sokodata.core.fetch import (
    download_pdf,
    extract_pdf_tables,
    fetch_html_tables,
    fetch_html_text,
    fetch_json,
    parse_fuel_text,
)

log = logging.getLogger(__name__)

# World Bank WDI - open, no key, CC BY-4.0
WDI_CPI_URL = (
    "https://api.worldbank.org/v2/country/ZW/indicator/FP.CPI.TOTL.ZG"
    "?format=json&per_page=100&date=2010:2030"
)
WDI_FX_URL = (
    "https://api.worldbank.org/v2/country/ZW/indicator/PA.NUS.FCRF"
    "?format=json&per_page=100&date=2010:2030"
)

# Scraping targets - update if ZIMSTAT/RBZ/ZERA redesigns site
RBZ_RATES_URL = "https://www.rbz.co.zw/market-rates"
ZERA_FUEL_URL = "https://www.zera.co.zw/"
ZIMSTAT_CPI_URL = "https://www.zimstat.co.zw/wp-content/uploads/publications/Economic/Price/CPI.pdf"


def fetch_worldbank_cpi() -> pd.DataFrame:
    """Fetch annual CPI inflation % from World Bank WDI for ZW."""
    try:
        data = fetch_json(WDI_CPI_URL)
        # WDI returns [metadata, [records]]
        records = data[1] if isinstance(data, list) and len(data) > 1 else []
        rows = []
        for r in records:
            if r.get("value") is None or r.get("date") is None:
                continue
            rows.append(
                {
                    "date": f"{r['date']}-12-31",
                    "cpi": None,
                    "inflation_yoy": float(r["value"]),
                    "inflation_mom": None,
                    "source": "World Bank WDI FP.CPI.TOTL.ZG",
                }
            )
        df = pd.DataFrame(rows)
        if not df.empty:
            df["date"] = pd.to_datetime(df["date"])
        log.info("WDI CPI: %d annual points", len(df))
        return df
    except Exception as e:
        log.warning("WDI CPI fetch failed: %s", e)
        return pd.DataFrame(columns=["date", "cpi", "inflation_yoy", "inflation_mom", "source"])


def fetch_rbz_rates_scrape() -> pd.DataFrame:
    """Scrape RBZ interbank ZiG/USD from HTML tables.

    This is the correct fallback where no open API exists:
    read_html on the RBZ page, look for a table containing ZiG/USD.
    If scraping fails, returns empty DF (caller merges with WDI FX).
    """
    tables = fetch_html_tables(RBZ_RATES_URL, match="ZiG|USD|Interbank")
    rows = []
    for tbl in tables:
        # Normalize columns
        tbl.columns = [str(c).strip().lower() for c in tbl.columns]
        # Heuristic: find date + rate columns
        for _, r in tbl.iterrows():
            try:
                vals = [str(v) for v in r.values]
                # crude: first date-like, first number-like as rate
                date_candidate = None
                rate_candidate = None
                for v in vals:
                    if not date_candidate and any(ch in v for ch in ("/", "-")) and len(v) >= 8:
                        date_candidate = v
                    if not rate_candidate:
                        try:
                            nv = float(str(v).replace(",", ""))
                            if 5 < nv < 100000:  # ZiG range
                                rate_candidate = nv
                        except Exception:
                            pass
                if date_candidate and rate_candidate:
                    rows.append(
                        {"date": date_candidate, "rate": rate_candidate, "source": "RBZ scrape"}
                    )
            except Exception:
                continue

    # Fallback: regex on raw HTML
    if not rows:
        html = fetch_html_text(RBZ_RATES_URL)
        if html:
            import re

            # e.g. "ZiG 26.50 per USD" on page
            for m in re.finditer(r"ZiG[^\d]*(\d+\.?\d*)\s*(?:per\s*)?USD", html, re.I):
                rows.append({"date": str(date.today()), "rate": float(m.group(1)), "source": "RBZ regex"})

    df = pd.DataFrame(rows)
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.dropna(subset=["date"])
    log.info("RBZ scrape: %d rate points", len(df))
    return df


def fetch_zera_fuel_scrape(raw_dir: Path | None = None) -> pd.DataFrame:
    """Scrape ZERA fuel prices (Diesel, Petrol) via HTML then PDF fallback.

    Priority: HTML table -> HTML regex -> PDF tables.
    Returns DataFrame [date, fuel_type, price, currency, source].
    """
    base = raw_dir or RAW_DIR

    # 1) HTML tables
    tables = fetch_html_tables(ZERA_FUEL_URL, match="Diesel|Petrol|Fuel")
    rows: list[dict] = []
    for tbl in tables:
        tbl.columns = [str(c).strip() for c in tbl.columns]
        tbl_str = tbl.to_string().lower()
        if "diesel" in tbl_str or "petrol" in tbl_str:
            # Attempt to parse rows with fuel + price
            for _, r in tbl.iterrows():
                vals = [str(v) for v in r.values]
                for i, v in enumerate(vals):
                    vl = v.lower()
                    if "diesel" in vl or "petrol" in vl:
                        # price is often next column
                        for nv in vals[i + 1 :]:
                            try:
                                price = float(str(nv).replace(",", "").replace("$", "").strip())
                                if 0.5 < price < 10:
                                    rows.append(
                                        {
                                            "date": str(date.today()),
                                            "fuel_type": v.strip(),
                                            "price": price,
                                            "currency": "USD",
                                            "source": "ZERA HTML table",
                                        }
                                    )
                                    break
                            except Exception:
                                continue

    # 2) HTML regex fallback
    if not rows:
        html = fetch_html_text(ZERA_FUEL_URL)
        if html:
            for item in parse_fuel_text(html):
                rows.append(
                    {
                        "date": str(date.today()),
                        "fuel_type": item["fuel"],
                        "price": item["price"],
                        "currency": "USD",
                        "source": "ZERA HTML regex",
                    }
                )

    # 3) PDF fallback (ZERA sometimes publishes PDF schedule)
    # We try to download a known PDF if HTML failed - example path; update URL when ZERA changes
    if not rows:
        try:
            pdf_path = Path(base) / "zera_fuel.pdf"
            # This URL is illustrative; real ZERA PDF link changes monthly
            # download_pdf(ZERA_PDF_URL, pdf_path)  # uncomment when URL known
            if pdf_path.exists():
                for tbl in extract_pdf_tables(pdf_path):
                    tbl.columns = [str(c).strip().lower() for c in tbl.columns]
                    log.info("ZERA PDF table cols: %s", list(tbl.columns))
                    # Parse similarly...
        except Exception as e:
            log.warning("ZERA PDF fallback failed: %s", e)

    df = pd.DataFrame(rows)
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    log.info("ZERA scrape: %d fuel points", len(df))
    return df


def fetch_zimstat_cpi_pdf(raw_dir: Path | None = None) -> pd.DataFrame:
    """Attempt to extract CPI from ZIMSTAT PDF bulletin.

    ZIMSTAT publishes monthly CPI bulletin as PDF - no API.
    This demonstrates the PDF -> table -> clean pattern.
    If pdfplumber not installed or PDF not reachable, returns empty.
    """
    base = raw_dir or RAW_DIR
    try:
        pdf_path = Path(base) / "zimstat_cpi.pdf"
        download_pdf(ZIMSTAT_CPI_URL, pdf_path)
        tables = extract_pdf_tables(pdf_path, pages="1-3")
        rows = []
        for tbl in tables:
            tbl.columns = [str(c).strip().lower() for c in tbl.columns]
            # Heuristic: look for month + CPI/inflation columns
            if any("cpi" in c or "inflation" in c or "index" in c for c in tbl.columns):
                for _, r in tbl.iterrows():
                    rows.append({**{k: v for k, v in r.items()}, "source": "ZIMSTAT PDF"})
        df = pd.DataFrame(rows)
        log.info("ZIMSTAT PDF: %d rows from %d tables", len(df), len(tables))
        # Normalization to standard cpi schema would happen in clean_cpi
        return df
    except Exception as e:
        log.warning("ZIMSTAT PDF fetch failed (expected until pdfplumber + URL verified): %s", e)
        return pd.DataFrame(columns=["date", "cpi", "inflation_yoy", "inflation_mom", "source"])


def fetch_economy_all(raw_dir: Path | None = None) -> dict[str, pd.DataFrame]:
    """Fetch all economy sources - open API + scraped.

    Returns dict with keys: rates, cpi, fuel
    """
    base = raw_dir or RAW_DIR
    cpi_wdi = fetch_worldbank_cpi()
    cpi_pdf = fetch_zimstat_cpi_pdf(base)
    # Combine: prefer ZIMSTAT monthly when available, else WDI annual
    cpi = pd.concat([cpi_wdi, cpi_pdf], ignore_index=True) if not cpi_pdf.empty else cpi_wdi

    rates = fetch_rbz_rates_scrape()
    # Could also merge WDI FX annual here
    try:
        wdi_fx = fetch_json(WDI_FX_URL)
        records = wdi_fx[1] if isinstance(wdi_fx, list) and len(wdi_fx) > 1 else []
        fx_rows = [
            {"date": f"{r['date']}-12-31", "rate": float(r["value"]), "source": "World Bank FX"}
            for r in records
            if r.get("value") is not None
        ]
        fx_df = pd.DataFrame(fx_rows)
        if not fx_df.empty:
            fx_df["date"] = pd.to_datetime(fx_df["date"])
            rates = pd.concat([rates, fx_df], ignore_index=True) if not rates.empty else fx_df
    except Exception as e:
        log.warning("WDI FX fetch failed: %s", e)

    fuel = fetch_zera_fuel_scrape(base)
    return {"rates": rates, "cpi": cpi, "fuel": fuel}
