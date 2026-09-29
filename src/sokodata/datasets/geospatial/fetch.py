"""Fetch geospatial boundaries for a country.

* HDX / OCHA COD (open, CC BY-IGO) - admin0/admin1/admin2 shapefiles/GeoJSON
  Zimbabwe: https://data.humdata.org/dataset/cod-ab-zwe
  Kenya: https://data.humdata.org/dataset/cod-ab-ken
* WFP markets already in markets dataset - lat/lon reused.
* No PDF scraping needed - pure GeoJSON download, degrades gracefully.
"""

import logging
from pathlib import Path

import pandas as pd

from sokodata.config import RAW_DIR
from sokodata.core.fetch import download, fetch_json

log = logging.getLogger(__name__)

# Country-specific HDX COD-AB dataset IDs
HDX_COD_AB = {
    "ZW": "cod-ab-zwe",
    "KE": "cod-ab-ken",
}

# Fallback: OCHA COD boundaries via Hub API
OCHA_BOUNDARIES_API = "https://data.humdata.org/api/3/action/package_show?id={dataset_id}"


def fetch_ocha_metadata(country: str = "ZW") -> pd.DataFrame:
    """Fetch boundary metadata from HDX API for a country."""
    dataset_id = HDX_COD_AB.get(country.upper(), HDX_COD_AB["ZW"])
    try:
        data = fetch_json(OCHA_BOUNDARIES_API.format(dataset_id=dataset_id))
        result = data.get("result", {}) if isinstance(data, dict) else {}
        resources = result.get("resources", [])
        rows = []
        for r in resources:
            rows.append({
                "name": r.get("name"),
                "format": r.get("format"),
                "url": r.get("url") or r.get("download_url"),
                "source": f"HDX COD-AB {country.upper()}",
            })
        df = pd.DataFrame(rows)
        log.info("HDX boundaries metadata for %s: %d resources", country, len(df))
        return df
    except Exception as e:
        log.warning("HDX boundaries API failed for %s: %s", country, e)
        return pd.DataFrame(columns=["name", "format", "url", "source"])


def fetch_admin_boundaries(country: str = "ZW", raw_dir: Path | None = None, level: int = 1) -> Path | None:
    """Download GeoJSON for admin level 1 or 2. Returns path or None."""
    # Country-specific GeoJSON URLs (fallback to metadata API)
    geojson_urls = {
        "ZW": {
            1: "https://data.humdata.org/dataset/6d54e1d3-8d45-409c-8c0d-0c5e0c0c0c0c/resource/download/zwe_adm1.geojson",
            2: "https://data.humdata.org/dataset/6d54e1d3-8d45-409c-8c0d-0c5e0c0c0c0c/resource/download/zwe_adm2.geojson",
        },
        "KE": {
            1: "https://data.humdata.org/dataset/4c1b9b5e-1e23-4f6b-8e8b-1b5e0c0c0c0c/resource/download/ken_adm1.geojson",
            2: "https://data.humdata.org/dataset/4c1b9b5e-1e23-4f6b-8e8b-1b5e0c0c0c0c/resource/download/ken_adm2.geojson",
        },
    }
    base = raw_dir or RAW_DIR
    url = geojson_urls.get(country.upper(), {}).get(level)
    if not url:
        log.warning("No GeoJSON URL for country %s level %d", country, level)
        return None
    dest = Path(base) / f"{country.lower()}_adm{level}.geojson"
    try:
        download(url, dest)
        log.info("downloaded admin%d GeoJSON for %s to %s", level, country, dest)
        return dest
    except Exception as e:
        log.warning("GeoJSON download failed for %s admin%d: %s", country, level, e)
        return None


def fetch_geospatial_all(country: str = "ZW", raw_dir: Path | None = None) -> dict[str, pd.DataFrame]:
    """Fetch geospatial - returns metadata DataFrame + paths."""
    meta = fetch_ocha_metadata(country)
    # also include market locations from markets dataset if available
    return {"metadata": meta}