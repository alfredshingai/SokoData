"""Shared fixtures: build a test warehouse from the committed real-data sample."""

from pathlib import Path

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from sokodata.api.main import create_app
from sokodata.etl.clean import clean_markets, clean_prices
from sokodata.etl.store import connect, load_tables

FIXTURES = Path(__file__).parent / "fixtures"

# Real market_ids for the fixture rows (Chiredzi Urban, Tongogara Refugee Camp 2)
SAMPLE_MARKETS = pd.DataFrame(
    [
        {"market_id": 5532, "market": "Chiredzi Urban", "countryiso3": "ZWE",
         "admin1": "Masvingo", "admin2": "Chiredzi", "latitude": -21.05, "longitude": 31.60},
        {"market_id": 5065, "market": "Tongogara Refugee Camp 2", "countryiso3": "ZWE",
         "admin1": "Manicaland", "admin2": "Chipinge", "latitude": -21.07, "longitude": 32.42},
    ]
)


@pytest.fixture(scope="session")
def raw_prices() -> pd.DataFrame:
    return pd.read_csv(FIXTURES / "wfp_food_prices_zwe_sample.csv")


@pytest.fixture(scope="session")
def sample_markets() -> pd.DataFrame:
    return clean_markets(SAMPLE_MARKETS.copy())


@pytest.fixture(scope="session")
def test_db(tmp_path_factory, raw_prices, sample_markets) -> Path:
    db = tmp_path_factory.mktemp("data") / "test.db"
    conn = connect(db)
    try:
        load_tables(conn, clean_prices(raw_prices), sample_markets)
    finally:
        conn.close()
    return db


@pytest.fixture()
def client(test_db) -> TestClient:
    app = create_app(test_db)
    with TestClient(app) as c:
        yield c
