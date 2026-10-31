"""Download raw source files to the local data directory."""

import json
import logging
import shutil
import urllib.request
from pathlib import Path

from sokodata.config import (
    RAW_DIR,
    REQUEST_TIMEOUT,
    USER_AGENT,
    get_country_config,
    get_markets_url,
    get_prices_url,
)

log = logging.getLogger(__name__)

HDX_API = "https://data.humdata.org/api/3/action/package_show?id={dataset}"


def _resolve_via_hdx(country: str, kind: str) -> str | None:
    """Resolve a resource download URL from the HDX API at request time.

    Fallback for when a configured resource URL moves upstream. *kind* is
    "prices" or "markets"; matched by the resource filename pattern.
    """
    try:
        dataset = get_country_config(country)["hdx_dataset"]
        req = urllib.request.Request(
            HDX_API.format(dataset=dataset), headers={"User-Agent": USER_AGENT}
        )
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            result = json.load(resp).get("result", {})
        token = "food_prices" if kind == "prices" else "markets"
        for res in result.get("resources", []):
            url = (res.get("url") or "").lower()
            if token in url and url.endswith(".csv"):
                return res["url"]
    except Exception as e:
        log.warning("HDX resolution failed for %s %s: %s", country, kind, e)
    return None


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
    iso = get_country_config(country)["iso3"].lower()
    prices_path = Path(base) / f"wfp_food_prices_{iso}.csv"
    markets_path = Path(base) / f"wfp_markets_{iso}.csv"

    # Try configured URL, then live HDX resolution, else empty file (caller
    # handles empty data gracefully, e.g. a country without WFP data on HDX).
    prices = _fetch_one(country, "prices", get_prices_url(country), prices_path)
    markets = _fetch_one(country, "markets", get_markets_url(country), markets_path)
    return prices, markets


def _fetch_one(country: str, kind: str, url: str, dest: Path) -> Path:
    try:
        return download(url, dest)
    except Exception as e:
        log.warning("Configured %s URL failed for %s: %s", kind, country, e)
    resolved = _resolve_via_hdx(country, kind)
    if resolved:
        try:
            return download(resolved, dest)
        except Exception as e:
            log.warning("HDX-resolved %s URL failed for %s: %s", kind, country, e)
    dest.write_text("")  # empty file; ETL skips empty inputs
    return dest
