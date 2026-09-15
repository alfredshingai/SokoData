"""Core fetchers for the SokoData commons.

Three strategies for Zimbabwean sources that lack open APIs:

1. OpenAPI fetch  - JSON APIs (WFP/HDX, World Bank, Open-Meteo, NASA POWER)
2. HTML scrape    - table scraping for RBZ, ZERA web pages
3. PDF extract    - ZIMSTAT CPI, ZERA fuel PDFs (tabular PDFs)

All fetchers share: atomic writes, User-Agent, timeout, logging.
HTML/PDF fetchers degrade gracefully - they log warnings instead of
raising SchemaDrift so a broken upstream page doesn't kill the whole ETL.
"""

import json
import logging
import re
import shutil
import urllib.request
from pathlib import Path

import pandas as pd

from sokodata.config import REQUEST_TIMEOUT, USER_AGENT

log = logging.getLogger(__name__)


def download(url: str, dest: Path, headers: dict | None = None) -> Path:
    """Fetch url to dest atomically (tmp then rename)."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".tmp")
    req_headers = {"User-Agent": USER_AGENT}
    if headers:
        req_headers.update(headers)
    req = urllib.request.Request(url, headers=req_headers)
    log.info("downloading %s", url)
    with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp, open(tmp, "wb") as out:
        shutil.copyfileobj(resp, out)
    tmp.replace(dest)
    log.info("saved %s (%d bytes)", dest, dest.stat().st_size)
    return dest


def fetch_json(url: str, headers: dict | None = None) -> dict | list:
    """GET JSON from an open API (World Bank, Open-Meteo, etc.)."""
    req_headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    if headers:
        req_headers.update(headers)
    req = urllib.request.Request(url, headers=req_headers)
    log.info("fetch_json %s", url)
    with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
        return json.loads(resp.read().decode())


# ---------------------------------------------------------------------------
# HTML table scraping - for RBZ, ZERA HTML pages
# ---------------------------------------------------------------------------

def fetch_html_tables(url: str, match: str | None = None) -> list[pd.DataFrame]:
    """Scrape HTML tables from a page.  Returns list of DataFrames.

    Uses pandas.read_html (lxml/html5lib) - zero extra deps beyond pandas.
    For more precise scraping, pass `match` regex to filter tables.

    If the page is unreachable or has no tables, returns [] and logs warning
    (does not raise) - caller decides whether that's fatal.
    """
    try:
        tables = pd.read_html(url, match=match, storage_options={"User-Agent": USER_AGENT})
        log.info("scraped %d HTML tables from %s", len(tables), url)
        return tables
    except Exception as e:
        log.warning("HTML scrape failed for %s: %s", url, e)
        return []


def fetch_html_text(url: str) -> str | None:
    """Fetch raw HTML text (for BeautifulSoup-style regex parsing)."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            return resp.read().decode(errors="replace")
    except Exception as e:
        log.warning("fetch_html_text failed for %s: %s", url, e)
        return None


# ---------------------------------------------------------------------------
# PDF table extraction - for ZIMSTAT CPI, ZERA fuel PDFs
# ---------------------------------------------------------------------------

def download_pdf(url: str, dest: Path) -> Path:
    """Download a PDF like ZIMSTAT CPI bulletin or ZERA schedule."""
    return download(url, dest, headers={"Accept": "application/pdf"})


def extract_pdf_tables(pdf_path: Path, pages: str = "all") -> list[pd.DataFrame]:
    """Extract tables from a PDF.

    Tries pdfplumber first (if installed), falls back to tabula-py hint.
    Returns [] if no extractor available - caller can fall back to manual
    CSV or HTML version. The commons pattern is: try PDF extract, if it
    fails log and keep the last known good CSV in data/raw/.

    Install: pip install pdfplumber  (pure python, no Java)
    Alternative: pip install tabula-py (requires Java)
    """
    # Try pdfplumber - best for text-based PDFs like ZIMSTAT/ZERA
    try:
        import pdfplumber  # type: ignore

        tables: list[pd.DataFrame] = []
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                # pages param like "1", "1-3", "all"
                if pages != "all" and str(i + 1) not in _expand_pages(pages):
                    continue
                for tbl in page.extract_tables() or []:
                    if not tbl or len(tbl) < 2:
                        continue
                    df = pd.DataFrame(tbl[1:], columns=tbl[0])
                    df = df.dropna(how="all")
                    if not df.empty:
                        tables.append(df)
        log.info("pdfplumber extracted %d tables from %s", len(tables), pdf_path)
        return tables
    except ImportError:
        log.warning("pdfplumber not installed - pip install pdfplumber to enable PDF extraction")
        return []
    except Exception as e:
        log.warning("PDF extraction failed for %s: %s", pdf_path, e)
        return []


def _expand_pages(pages: str) -> set[str]:
    out: set[str] = set()
    for part in pages.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-", 1)
            out.update(str(i) for i in range(int(a), int(b) + 1))
        else:
            out.add(part)
    return out


# ---------------------------------------------------------------------------
# Helpers for common Zim patterns
# ---------------------------------------------------------------------------

# ZERA fuel example: HTML page often contains "Diesel 1.XX, Petrol 1.YY"
FUEL_PRICE_RE = re.compile(r"(Diesel|Petrol|Blend|LP\s*Gas)[^\d]*(\d+\.\d{2,4})", re.I)

def parse_fuel_text(html: str) -> list[dict]:
    """Quick regex fallback for fuel prices embedded in HTML text."""
    results = []
    for m in FUEL_PRICE_RE.finditer(html):
        results.append({"fuel": m.group(1).strip(), "price": float(m.group(2))})
    return results
