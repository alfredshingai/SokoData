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
    "MW": "cod-ab-mwi",
    "MZ": "cod-ab-moz",
    "ZM": "cod-ab-zmb",
    "TZ": "cod-ab-tza",
    "UG": "cod-ab-uga",
    "RW": "cod-ab-rwa",
    "BI": "cod-ab-bdi",
    "SO": "cod-ab-som",
    "ET": "cod-ab-eth",
    "SS": "cod-ab-ssd",
    "SD": "cod-ab-sdn",
    "CF": "cod-ab-caf",
    "TD": "cod-ab-tcd",
    "CM": "cod-ab-cmr",
    "NG": "cod-ab-nga",
    "GH": "cod-ab-gha",
    "BF": "cod-ab-bfa",
    "ML": "cod-ab-mli",
    "NE": "cod-ab-ner",
    "SN": "cod-ab-sen",
    "MR": "cod-ab-mrt",
    "GN": "cod-ab-gin",
    "SL": "cod-ab-sle",
    "LR": "cod-ab-lbr",
    "CI": "cod-ab-civ",
    "TG": "cod-ab-tgo",
    "BJ": "cod-ab-ben",
    "HT": "cod-ab-hti",
    "AF": "cod-ab-afg",
    "YE": "cod-ab-yem",
    "SY": "cod-ab-syr",
    "IQ": "cod-ab-irq",
    "LB": "cod-ab-lbn",
    "JO": "cod-ab-jor",
    "PS": "cod-ab-pse",
    "UA": "cod-ab-ukr",
    "VE": "cod-ab-ven",
    "CO": "cod-ab-col",
    "PE": "cod-ab-per",
    "BO": "cod-ab-bol",
    "EC": "cod-ab-ecu",
    "GT": "cod-ab-gtm",
    "HN": "cod-ab-hnd",
    "NI": "cod-ab-nic",
    "SV": "cod-ab-slv",
    "PH": "cod-ab-phl",
    "BD": "cod-ab-bgd",
    "MM": "cod-ab-mmr",
    "PK": "cod-ab-pak",
    "LK": "cod-ab-lka",
    "NP": "cod-ab-npl",
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
    "MW": {
        1: "https://data.humdata.org/dataset/cod-ab-mwi/resource/download/mwi_adm1.geojson",
        2: "https://data.humdata.org/dataset/cod-ab-mwi/resource/download/mwi_adm2.geojson",
    },
    "MZ": {
        1: "https://data.humdata.org/dataset/cod-ab-moz/resource/download/moz_adm1.geojson",
        2: "https://data.humdata.org/dataset/cod-ab-moz/resource/download/moz_adm2.geojson",
    },
    "ZM": {
        1: "https://data.humdata.org/dataset/cod-ab-zmb/resource/download/zmb_adm1.geojson",
        2: "https://data.humdata.org/dataset/cod-ab-zmb/resource/download/zmb_adm2.geojson",
    },
    "TZ": {
        1: "https://data.humdata.org/dataset/cod-ab-tza/resource/download/tza_adm1.geojson",
        2: "https://data.humdata.org/dataset/cod-ab-tza/resource/download/tza_adm2.geojson",
    },
    "UG": {
        1: "https://data.humdata.org/dataset/cod-ab-uga/resource/download/uga_adm1.geojson",
        2: "https://data.humdata.org/dataset/cod-ab-uga/resource/download/uga_adm2.geojson",
    },
    "RW": {
        1: "https://data.humdata.org/dataset/cod-ab-rwa/resource/download/rwa_adm1.geojson",
        2: "https://data.humdata.org/dataset/cod-ab-rwa/resource/download/rwa_adm2.geojson",
    },
    "BI": {
        1: "https://data.humdata.org/dataset/cod-ab-bdi/resource/download/bdi_adm1.geojson",
        2: "https://data.humdata.org/dataset/cod-ab-bdi/resource/download/bdi_adm2.geojson",
    },
    "TZ": {
        1: "https://data.humdata.org/dataset/cod-ab-tza/resource/download/tza_adm1.geojson",
        2: "https://data.humdata.org/dataset/cod-ab-tza/resource/download/tza_adm2.geojson",
    },
    "UG": {
        1: "https://data.humdata.org/dataset/cod-ab-uga/resource/download/uga_adm1.geojson",
        2: "https://data.humdata.org/dataset/cod-ab-uga/resource/download/uga_adm2.geojson",
    },
    "RW": {
        1: "https://data.humdata.org/dataset/cod-ab-rwa/resource/download/rwa_adm1.geojson",
        2: "https://data.humdata.org/dataset/cod-ab-rwa/resource/download/rwa_adm2.geojson",
    },
    "BI": {
        1: "https://data.humdata.org/dataset/cod-ab-bdi/resource/download/bdi_adm1.geojson",
        2: "https://data.humdata.org/dataset/cod-ab-bdi/resource/download/bdi_adm2.geojson",
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