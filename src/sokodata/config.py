"""Central configuration: data sources, default paths, country support."""

import os
from pathlib import Path

HDX_DATASET = "https://data.humdata.org/dataset/wfp-food-prices-for-zimbabwe"

# Default country (Zimbabwe)
DEFAULT_COUNTRY = "ZW"

# ISO3 country codes supported
COUNTRIES = {
    "ZW": {
        "name": "Zimbabwe",
        "iso3": "ZW",
        "hdx_dataset": "wfp-food-prices-for-zimbabwe",
        "prices_resource": "7c48c192-36d4-422e-996d-19cc62e2e4fd",
        "markets_resource": "69d1652a-ee48-42a1-b4a7-1321296c31ac",
        "wb_country": "ZW",
    },
    "KE": {
        "name": "Kenya",
        "iso3": "KE",
        "hdx_dataset": "wfp-food-prices-for-kenya",
        "prices_resource": "RESOURCE_ID_TO_BE_FOUND",
        "markets_resource": "RESOURCE_ID_TO_BE_FOUND",
        "wb_country": "KE",
    },
    # Add more countries as needed
}

def get_country_config(country: str = DEFAULT_COUNTRY) -> dict:
    """Get configuration for a specific country."""
    # Handle Path objects passed by mistake
    if hasattr(country, 'name'):
        country = str(country)
    return COUNTRIES.get(country.upper(), COUNTRIES[DEFAULT_COUNTRY])


def get_prices_url(country: str = DEFAULT_COUNTRY) -> str:
    """Build WFP prices URL for a country."""
    cfg = get_country_config(country)
    if cfg["prices_resource"]:
        return (
            f"https://data.humdata.org/dataset/"
            f"{cfg['hdx_dataset']}/resource/"
            f"{cfg['prices_resource']}/download/wfp_food_prices_{cfg['iso3'].lower()}.csv"
        )
    # Fallback: try standard pattern
    return (
        f"https://data.humdata.org/dataset/"
        f"wfp-food-prices-for-{cfg['name'].lower()}/resource/"
        f"download/wfp_food_prices_{cfg['iso3'].lower()}.csv"
    )


def get_markets_url(country: str = DEFAULT_COUNTRY) -> str:
    """Build WFP markets URL for a country."""
    cfg = get_country_config(country)
    if cfg["markets_resource"]:
        return (
            f"https://data.humdata.org/dataset/"
            f"{cfg['hdx_dataset']}/resource/"
            f"{cfg['markets_resource']}/download/wfp_markets_{cfg['iso3'].lower()}.csv"
        )
    return (
        f"https://data.humdata.org/dataset/"
        f"wfp-food-prices-for-{cfg['name'].lower()}/resource/"
        f"download/wfp_markets_{cfg['iso3'].lower()}.csv"
    )


def get_wb_country(country: str = DEFAULT_COUNTRY) -> str:
    """Get World Bank country code for a country."""
    return get_country_config(country)["wb_country"]


# Attribution required by CC BY-IGO; surfaced in /health and the README.
DATA_CREDIT = {
    "source": "World Food Programme Price Database, via HDX (OCHA)",
    "dataset": HDX_DATASET,
    "license": "CC BY-IGO",
}

_DATA_DIR = os.environ.get("SOKODATA_DATA_DIR", "data")
DB_PATH = Path(_DATA_DIR) / "sokodata.db"
RAW_DIR = Path(_DATA_DIR) / "raw"

USER_AGENT = "sokodata-etl/0.1 (+https://github.com/alfredshingai/sokodata)"
REQUEST_TIMEOUT = 60