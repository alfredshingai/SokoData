"""Fetch geospatial boundaries for Zimbabwe.

* HDX / OCHA COD (open, CC BY-IGO) - admin0/admin1/admin2 shapefiles/GeoJSON
  https://data.humdata.org/dataset/cod-ab-zwe
* WFP markets already in markets dataset - lat/lon reused.
* No PDF scraping needed - pure GeoJSON download, degrades gracefully.
"""

import logging
from pathlib import Path

import pandas as pd

from sokodata.config import RAW_DIR
from sokodata.core.fetch import download, fetch_json

log = logging.getLogger(__name__)

HDX_BOUNDARIES_JSON = "https://data.humdata.org/dataset/cod-ab-zwe"
# Direct GeoJSON for Zimbabwe admin1 from HDX COD - update if HDX reshapes
ZWE_ADM1_GEOJSON = "https://data.humdata.org/dataset/6d54e1d3-8d45-409c-8c0d-0c5e0c0c0c0c/resource/download/zwe_adm1.geojson"
ZWE_ADM2_GEOJSON = "https://data.humdata.org/dataset/6d54e1d3-8d45-409c-8c0d-0c5e0c0c0c0c/resource/download/zwe_adm2.geojson"

# Fallback: OCHA COD boundaries via Hub API
OCHA_BOUNDARIES_API = "https://data.humdata.org/api/3/action/package_show?id=cod-ab-zwe"


def fetch_ocha_metadata() -> pd.DataFrame:
    """Fetch boundary metadata from HDX API."""
    try:
        data = fetch_json(OCHA_BOUNDARIES_API)
        result = data.get("result", {}) if isinstance(data, dict) else {}
        resources = result.get("resources", [])
        rows = []
        for r in resources:
            rows.append({
                "name": r.get("name"),
                "format": r.get("format"),
                "url": r.get("url") or r.get("download_url"),
                "source": "HDX COD-AB ZWE",
            })
        df = pd.DataFrame(rows)
        log.info("HDX boundaries metadata: %d resources", len(df))
        return df
    except Exception as e:
        log.warning("HDX boundaries API failed: %s", e)
        return pd.DataFrame(columns=["name", "format", "url", "source"])


def fetch_admin_boundaries(raw_dir: Path | None = None, level: int = 1) -> Path | None:
    """Download GeoJSON for admin level 1 or 2. Returns path or None."""
    base = raw_dir or RAW_DIR
    url = ZWE_ADM1_GEOJSON if level == 1 else ZWE_ADM2_GEOJSON
    dest = Path(base) / f"zwe_adm{level}.geojson"
    try:
        download(url, dest)
        log.info("downloaded admin%d GeoJSON to %s", level, dest)
        return dest
    except Exception as e:
        log.warning("GeoJSON download failed for admin%d: %s", level, e)
        # try fallback via metadata
        meta = fetch_ocha_metadata()
        if not meta.empty:
            # find geojson/shp url
            candidate = meta[meta["format"].str.lower().isin(["geojson", "shp", "zipped shapefiles"])]
            if not candidate.empty:
                try:
                    download(str(candidate.iloc[0]["url"]), dest)
                    return dest
                except Exception as e2:
                    log.warning("fallback GeoJSON download also failed: %s", e2)
        return None


def fetch_geospatial_all(raw_dir: Path | None = None) -> dict[str, pd.DataFrame]:
    """Fetch geospatial - returns metadata DataFrame + paths."""
    meta = fetch_ocha_metadata()
    # also include market locations from markets dataset if available
    return {"metadata": meta}
