"""Download raw source files to the local data directory."""

import logging
import shutil
import urllib.request
from pathlib import Path

from sokodata.config import RAW_DIR, REQUEST_TIMEOUT, USER_AGENT, get_prices_url, get_markets_url

log = logging.getLogger(__name__)


def download(url: str, dest: Path) -> Path:
    """Fetch *url* to *dest*, writing atomically (tmp file, then rename)."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".tmp")
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    log.info("downloading %s", url)
    with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp, open(tmp, "wb") as out:
        shutil.copyfileobj(resp, out)
    tmp.replace(dest)
    log.info("saved %s (%d bytes)", dest, dest.stat().st_size)
    return dest


def fetch_raw(data_dir: Path | None = None, country: str = "ZW") -> tuple[Path, Path]:
    """Download both source CSVs for a country; returns (prices_path, markets_path).

    If a country's WFP data is not available on HDX, logs warning and returns
    empty files (caller should handle empty data gracefully).
    """
    base = data_dir or RAW_DIR
    prices_url = get_prices_url(country)
    markets_url = get_markets_url(country)
    iso = country.lower()
    prices_path = Path(base) / f"wfp_food_prices_{iso}.csv"
    markets_path = Path(base) / f"wfp_markets_{iso}.csv"

    # Try to download, but don't crash if 404 (e.g. Kenya WFP not yet on HDX)
    try:
        prices = download(prices_url, prices_path)
    except Exception as e:
        log.warning("Failed to download prices for %s: %s", country, e)
        prices_path.write_text("")  # empty file
        prices = prices_path

    try:
        markets = download(markets_url, markets_path)
    except Exception as e:
        log.warning("Failed to download markets for %s: %s", country, e)
        markets_path.write_text("")
        markets = markets_path

    return prices, markets