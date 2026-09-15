"""Download raw source files to the local data directory."""

import logging
import shutil
import urllib.request
from pathlib import Path

from sokodata.config import MARKETS_URL, PRICES_URL, RAW_DIR, REQUEST_TIMEOUT, USER_AGENT

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


def fetch_raw(data_dir: Path | None = None) -> tuple[Path, Path]:
    """Download both source CSVs; returns (prices_path, markets_path)."""
    base = data_dir or RAW_DIR
    prices = download(PRICES_URL, Path(base) / "wfp_food_prices_zwe.csv")
    markets = download(MARKETS_URL, Path(base) / "wfp_markets_zwe.csv")
    return prices, markets
