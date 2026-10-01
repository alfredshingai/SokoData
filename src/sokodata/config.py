"""Central configuration: data sources, default paths, country support."""

import os
from pathlib import Path

HDX_DATASET = "https://data.humdata.org/dataset/wfp-food-prices-for-zimbabwe"

# Default country (Zimbabwe)
DEFAULT_COUNTRY = "ZW"

# ISO3 country codes supported (WFP food prices via HDX)
# Resource IDs need to be verified per country on HDX
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
        "prices_resource": "c7c8c8c8-8c8c-4c8c-8c8c-8c8c8c8c8c8c",
        "markets_resource": "m8m8m8m8-m8m8-4m8m-8m8m-8m8m8m8m8m8m",
        "wb_country": "KE",
    },
    "MW": {
        "name": "Malawi",
        "iso3": "MW",
        "hdx_dataset": "wfp-food-prices-for-malawi",
        "prices_resource": "RESOURCE_ID_TO_BE_FOUND",
        "markets_resource": "RESOURCE_ID_TO_BE_FOUND",
        "wb_country": "MW",
    },
    "MZ": {
        "name": "Mozambique",
        "iso3": "MZ",
        "hdx_dataset": "wfp-food-prices-for-mozambique",
        "prices_resource": "RESOURCE_ID_TO_BE_FOUND",
        "markets_resource": "RESOURCE_ID_TO_BE_FOUND",
        "wb_country": "MZ",
    },
    "ZM": {
        "name": "Zambia",
        "iso3": "ZM",
        "hdx_dataset": "wfp-food-prices-for-zambia",
        "prices_resource": "RESOURCE_ID_TO_BE_FOUND",
        "markets_resource": "RESOURCE_ID_TO_BE_FOUND",
        "wb_country": "ZM",
    },
    "TZ": {
        "name": "Tanzania",
        "iso3": "TZ",
        "hdx_dataset": "wfp-food-prices-for-tanzania",
        "prices_resource": "RESOURCE_ID_TO_BE_FOUND",
        "markets_resource": "RESOURCE_ID_TO_BE_FOUND",
        "wb_country": "TZ",
    },
    "UG": {
        "name": "Uganda",
        "iso3": "UG",
        "hdx_dataset": "wfp-food-prices-for-uganda",
        "prices_resource": "RESOURCE_ID_TO_BE_FOUND",
        "markets_resource": "RESOURCE_ID_TO_BE_FOUND",
        "wb_country": "UG",
    },
    "RW": {
        "name": "Rwanda",
        "iso3": "RW",
        "hdx_dataset": "wfp-food-prices-for-rwanda",
        "prices_resource": "RESOURCE_ID_TO_BE_FOUND",
        "markets_resource": "RESOURCE_ID_TO_BE_FOUND",
        "wb_country": "RW",
    },
    "BI": {
        "name": "Burundi",
        "iso3": "BI",
        "hdx_dataset": "wfp-food-prices-for-burundi",
        "prices_resource": "RESOURCE_ID_TO_BE_FOUND",
        "markets_resource": "RESOURCE_ID_TO_BE_FOUND",
        "wb_country": "BI",
    },
    "SO": {
        "name": "Somalia",
        "iso3": "SO",
        "hdx_dataset": "wfp-food-prices-for-somalia",
        "prices_resource": "RESOURCE_ID_TO_BE_FOUND",
        "markets_resource": "RESOURCE_ID_TO_BE_FOUND",
        "wb_country": "SO",
    },
    "ET": {
        "name": "Ethiopia",
        "iso3": "ET",
        "hdx_dataset": "wfp-food-prices-for-ethiopia",
        "prices_resource": "RESOURCE_ID_TO_BE_FOUND",
        "markets_resource": "RESOURCE_ID_TO_BE_FOUND",
        "wb_country": "ET",
    },
    "SS": {
        "name": "South Sudan",
        "iso3": "SS",
        "hdx_dataset": "wfp-food-prices-for-south-sudan",
        "prices_resource": "RESOURCE_ID_TO_BE_FOUND",
        "markets_resource": "RESOURCE_ID_TO_BE_FOUND",
        "wb_country": "SS",
    },
    "SD": {
        "name": "Sudan",
        "iso3": "SD",
        "hdx_dataset": "wfp-food-prices-for-sudan",
        "prices_resource": "RESOURCE_ID_TO_BE_FOUND",
        "markets_resource": "RESOURCE_ID_TO_BE_FOUND",
        "wb_country": "SD",
    },
    "CF": {
        "name": "Central African Republic",
        "iso3": "CF",
        "hdx_dataset": "wfp-food-prices-for-central-african-republic",
        "prices_resource": "RESOURCE_ID_TO_BE_FOUND",
        "markets_resource": "RESOURCE_ID_TO_BE_FOUND",
        "wb_country": "CF",
    },
    "TD": {
        "name": "Chad",
        "iso3": "TD",
        "hdx_dataset": "wfp-food-prices-for-chad",
        "prices_resource": "RESOURCE_ID_TO_BE_FOUND",
        "markets_resource": "RESOURCE_ID_TO_BE_FOUND",
        "wb_country": "TD",
    },
    "CM": {
        "name": "Cameroon",
        "iso3": "CM",
        "hdx_dataset": "wfp-food-prices-for-cameroon",
        "prices_resource": "RESOURCE_ID_TO_BE_FOUND",
        "markets_resource": "RESOURCE_ID_TO_BE_FOUND",
        "wb_country": "CM",
    },
    "NG": {
        "name": "Nigeria",
        "iso3": "NG",
        "hdx_dataset": "wfp-food-prices-for-nigeria",
        "prices_resource": "RESOURCE_ID_TO_BE_FOUND",
        "markets_resource": "RESOURCE_ID_TO_BE_FOUND",
        "wb_country": "NG",
    },
    "GH": {
        "name": "Ghana",
        "iso3": "GH",
        "hdx_dataset": "wfp-food-prices-for-ghana",
        "prices_resource": "RESOURCE_ID_TO_BE_FOUND",
        "markets_resource": "RESOURCE_ID_TO_BE_FOUND",
        "wb_country": "GH",
    },
    "BF": {
        "name": "Burkina Faso",
        "iso3": "BF",
        "hdx_dataset": "wfp-food-prices-for-burkina-faso",
        "prices_resource": "RESOURCE_ID_TO_BE_FOUND",
        "markets_resource": "RESOURCE_ID_TO_BE_FOUND",
        "wb_country": "BF",
    },
    "ML": {
        "name": "Mali",
        "iso3": "ML",
        "hdx_dataset": "wfp-food-prices-for-mali",
        "prices_resource": "RESOURCE_ID_TO_BE_FOUND",
        "markets_resource": "RESOURCE_ID_TO_BE_FOUND",
        "wb_country": "ML",
    },
    "NE": {
        "name": "Niger",
        "iso3": "NE",
        "hdx_dataset": "wfp-food-prices-for-niger",
        "prices_resource": "RESOURCE_ID_TO_BE_FOUND",
        "markets_resource": "RESOURCE_ID_TO_BE_FOUND",
        "wb_country": "NE",
    },
    "SN": {
        "name": "Senegal",
        "iso3": "SN",
        "hdx_dataset": "wfp-food-prices-for-senegal",
        "prices_resource": "RESOURCE_ID_TO_BE_FOUND",
        "markets_resource": "RESOURCE_ID_TO_BE_FOUND",
        "wb_country": "SN",
    },
    "MR": {
        "name": "Mauritania",
        "iso3": "MR",
        "hdx_dataset": "wfp-food-prices-for-mauritania",
        "prices_resource": "RESOURCE_ID_TO_BE_FOUND",
        "markets_resource": "RESOURCE_ID_TO_BE_FOUND",
        "wb_country": "MR",
    },
    "GN": {
        "name": "Guinea",
        "iso3": "GN",
        "hdx_dataset": "wfp-food-prices-for-guinea",
        "prices_resource": "RESOURCE_ID_TO_BE_FOUND",
        "markets_resource": "RESOURCE_ID_TO_BE_FOUND",
        "wb_country": "GN",
    },
    "SL": {
        "name": "Sierra Leone",
        "iso3": "SL",
        "hdx_dataset": "wfp-food-prices-for-sierra-leone",
        "prices_resource": "RESOURCE_ID_TO_BE_FOUND",
        "markets_resource": "RESOURCE_ID_TO_BE_FOUND",
        "wb_country": "SL",
    },
    "LR": {
        "name": "Liberia",
        "iso3": "LR",
        "hdx_dataset": "wfp-food-prices-for-liberia",
        "prices_resource": "RESOURCE_ID_TO_BE_FOUND",
        "markets_resource": "RESOURCE_ID_TO_BE_FOUND",
        "wb_country": "LR",
    },
    "CI": {
        "name": "Côte d'Ivoire",
        "iso3": "CI",
        "hdx_dataset": "wfp-food-prices-for-cote-divoire",
        "prices_resource": "RESOURCE_ID_TO_BE_FOUND",
        "markets_resource": "RESOURCE_ID_TO_BE_FOUND",
        "wb_country": "CI",
    },
    "TG": {
        "name": "Togo",
        "iso3": "TG",
        "hdx_dataset": "wfp-food-prices-for-togo",
        "prices_resource": "RESOURCE_ID_TO_BE_FOUND",
        "markets_resource": "RESOURCE_ID_TO_BE_FOUND",
        "wb_country": "TG",
    },
    "BJ": {
        "name": "Benin",
        "iso3": "BJ",
        "hdx_dataset": "wfp-food-prices-for-benin",
        "prices_resource": "RESOURCE_ID_TO_BE_FOUND",
        "markets_resource": "RESOURCE_ID_TO_BE_FOUND",
        "wb_country": "BJ",
    },
    "HT": {
        "name": "Haiti",
        "iso3": "HT",
        "hdx_dataset": "wfp-food-prices-for-haiti",
        "prices_resource": "RESOURCE_ID_TO_BE_FOUND",
        "markets_resource": "RESOURCE_ID_TO_BE_FOUND",
        "wb_country": "HT",
    },
    "AF": {
        "name": "Afghanistan",
        "iso3": "AF",
        "hdx_dataset": "wfp-food-prices-for-afghanistan",
        "prices_resource": "RESOURCE_ID_TO_BE_FOUND",
        "markets_resource": "RESOURCE_ID_TO_BE_FOUND",
        "wb_country": "AF",
    },
    "YE": {
        "name": "Yemen",
        "iso3": "YE",
        "hdx_dataset": "wfp-food-prices-for-yemen",
        "prices_resource": "RESOURCE_ID_TO_BE_FOUND",
        "markets_resource": "RESOURCE_ID_TO_BE_FOUND",
        "wb_country": "YE",
    },
    "SY": {
        "name": "Syria",
        "iso3": "SY",
        "hdx_dataset": "wfp-food-prices-for-syria",
        "prices_resource": "RESOURCE_ID_TO_BE_FOUND",
        "markets_resource": "RESOURCE_ID_TO_BE_FOUND",
        "wb_country": "SY",
    },
    "IQ": {
        "name": "Iraq",
        "iso3": "IQ",
        "hdx_dataset": "wfp-food-prices-for-iraq",
        "prices_resource": "RESOURCE_ID_TO_BE_FOUND",
        "markets_resource": "RESOURCE_ID_TO_BE_FOUND",
        "wb_country": "IQ",
    },
    "LB": {
        "name": "Lebanon",
        "iso3": "LB",
        "hdx_dataset": "wfp-food-prices-for-lebanon",
        "prices_resource": "RESOURCE_ID_TO_BE_FOUND",
        "markets_resource": "RESOURCE_ID_TO_BE_FOUND",
        "wb_country": "LB",
    },
    "JO": {
        "name": "Jordan",
        "iso3": "JO",
        "hdx_dataset": "wfp-food-prices-for-jordan",
        "prices_resource": "RESOURCE_ID_TO_BE_FOUND",
        "markets_resource": "RESOURCE_ID_TO_BE_FOUND",
        "wb_country": "JO",
    },
    "PS": {
        "name": "Palestine",
        "iso3": "PS",
        "hdx_dataset": "wfp-food-prices-for-palestine",
        "prices_resource": "RESOURCE_ID_TO_BE_FOUND",
        "markets_resource": "RESOURCE_ID_TO_BE_FOUND",
        "wb_country": "PS",
    },
    "UA": {
        "name": "Ukraine",
        "iso3": "UA",
        "hdx_dataset": "wfp-food-prices-for-ukraine",
        "prices_resource": "RESOURCE_ID_TO_BE_FOUND",
        "markets_resource": "RESOURCE_ID_TO_BE_FOUND",
        "wb_country": "UA",
    },
    "VE": {
        "name": "Venezuela",
        "iso3": "VE",
        "hdx_dataset": "wfp-food-prices-for-venezuela",
        "prices_resource": "RESOURCE_ID_TO_BE_FOUND",
        "markets_resource": "RESOURCE_ID_TO_BE_FOUND",
        "wb_country": "VE",
    },
    "CO": {
        "name": "Colombia",
        "iso3": "CO",
        "hdx_dataset": "wfp-food-prices-for-colombia",
        "prices_resource": "RESOURCE_ID_TO_BE_FOUND",
        "markets_resource": "RESOURCE_ID_TO_BE_FOUND",
        "wb_country": "CO",
    },
    "PE": {
        "name": "Peru",
        "iso3": "PE",
        "hdx_dataset": "wfp-food-prices-for-peru",
        "prices_resource": "RESOURCE_ID_TO_BE_FOUND",
        "markets_resource": "RESOURCE_ID_TO_BE_FOUND",
        "wb_country": "PE",
    },
    "BO": {
        "name": "Bolivia",
        "iso3": "BO",
        "hdx_dataset": "wfp-food-prices-for-bolivia",
        "prices_resource": "RESOURCE_ID_TO_BE_FOUND",
        "markets_resource": "RESOURCE_ID_TO_BE_FOUND",
        "wb_country": "BO",
    },
    "EC": {
        "name": "Ecuador",
        "iso3": "EC",
        "hdx_dataset": "wfp-food-prices-for-ecuador",
        "prices_resource": "RESOURCE_ID_TO_BE_FOUND",
        "markets_resource": "RESOURCE_ID_TO_BE_FOUND",
        "wb_country": "EC",
    },
    "GT": {
        "name": "Guatemala",
        "iso3": "GT",
        "hdx_dataset": "wfp-food-prices-for-guatemala",
        "prices_resource": "RESOURCE_ID_TO_BE_FOUND",
        "markets_resource": "RESOURCE_ID_TO_BE_FOUND",
        "wb_country": "GT",
    },
    "HN": {
        "name": "Honduras",
        "iso3": "HN",
        "hdx_dataset": "wfp-food-prices-for-honduras",
        "prices_resource": "RESOURCE_ID_TO_BE_FOUND",
        "markets_resource": "RESOURCE_ID_TO_BE_FOUND",
        "wb_country": "HN",
    },
    "NI": {
        "name": "Nicaragua",
        "iso3": "NI",
        "hdx_dataset": "wfp-food-prices-for-nicaragua",
        "prices_resource": "RESOURCE_ID_TO_BE_FOUND",
        "markets_resource": "RESOURCE_ID_TO_BE_FOUND",
        "wb_country": "NI",
    },
    "SV": {
        "name": "El Salvador",
        "iso3": "SV",
        "hdx_dataset": "wfp-food-prices-for-el-salvador",
        "prices_resource": "RESOURCE_ID_TO_BE_FOUND",
        "markets_resource": "RESOURCE_ID_TO_BE_FOUND",
        "wb_country": "SV",
    },
    "PH": {
        "name": "Philippines",
        "iso3": "PH",
        "hdx_dataset": "wfp-food-prices-for-philippines",
        "prices_resource": "RESOURCE_ID_TO_BE_FOUND",
        "markets_resource": "RESOURCE_ID_TO_BE_FOUND",
        "wb_country": "PH",
    },
    "BD": {
        "name": "Bangladesh",
        "iso3": "BD",
        "hdx_dataset": "wfp-food-prices-for-bangladesh",
        "prices_resource": "RESOURCE_ID_TO_BE_FOUND",
        "markets_resource": "RESOURCE_ID_TO_BE_FOUND",
        "wb_country": "BD",
    },
    "MM": {
        "name": "Myanmar",
        "iso3": "MM",
        "hdx_dataset": "wfp-food-prices-for-myanmar",
        "prices_resource": "RESOURCE_ID_TO_BE_FOUND",
        "markets_resource": "RESOURCE_ID_TO_BE_FOUND",
        "wb_country": "MM",
    },
    "PK": {
        "name": "Pakistan",
        "iso3": "PK",
        "hdx_dataset": "wfp-food-prices-for-pakistan",
        "prices_resource": "RESOURCE_ID_TO_BE_FOUND",
        "markets_resource": "RESOURCE_ID_TO_BE_FOUND",
        "wb_country": "PK",
    },
    "LK": {
        "name": "Sri Lanka",
        "iso3": "LK",
        "hdx_dataset": "wfp-food-prices-for-sri-lanka",
        "prices_resource": "RESOURCE_ID_TO_BE_FOUND",
        "markets_resource": "RESOURCE_ID_TO_BE_FOUND",
        "wb_country": "LK",
    },
    "NP": {
        "name": "Nepal",
        "iso3": "NP",
        "hdx_dataset": "wfp-food-prices-for-nepal",
        "prices_resource": "RESOURCE_ID_TO_BE_FOUND",
        "markets_resource": "RESOURCE_ID_TO_BE_FOUND",
        "wb_country": "NP",
    },
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