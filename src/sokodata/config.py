"""Central configuration: data sources, default paths."""

import os
from pathlib import Path

HDX_DATASET = "https://data.humdata.org/dataset/wfp-food-prices-for-zimbabwe"

# WFP Zimbabwe food prices via HDX (CC BY-IGO). Update weekly upstream.
PRICES_URL = (
    "https://data.humdata.org/dataset/"
    "d878cfac-a45f-48bd-8460-a2e16ab0ea94/resource/"
    "7c48c192-36d4-422e-996d-19cc62e2e4fd/download/wfp_food_prices_zwe.csv"
)
MARKETS_URL = (
    "https://data.humdata.org/dataset/"
    "d878cfac-a45f-48bd-8460-a2e16ab0ea94/resource/"
    "69d1652a-ee48-42a1-b4a7-1321296c31ac/download/wfp_markets_zwe.csv"
)

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
