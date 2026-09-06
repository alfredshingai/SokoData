"""API integration tests against a warehouse built from real sample rows."""

from sokodata.analysis.seasonal import dedupe_flag
from sokodata.etl.clean import clean_prices


def test_cors_allows_browser_origins(client):
    r = client.get("/v1/markets", headers={"Origin": "https://alfredshingai.github.io"})
    assert r.headers["access-control-allow-origin"] == "*"


def test_root_redirects_to_docs(client):
    r = client.get("/", follow_redirects=False)
    assert r.status_code in (302, 307)
    assert r.headers["location"].endswith("/docs")


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["coverage"]["markets"] == 2
    assert body["data_credit"]["license"] == "CC BY-IGO"


def test_markets_list_and_filter(client):
    r = client.get("/v1/markets")
    assert r.status_code == 200
    names = [m["market"] for m in r.json()]
    assert names == sorted(names)
    assert "Chiredzi Urban" in names

    r = client.get("/v1/markets", params={"q": "tongogara"})
    assert [m["market"] for m in r.json()] == ["Tongogara Refugee Camp 2"]


def test_market_404(client):
    assert client.get("/v1/markets/999999").status_code == 404


def test_commodities_have_coverage_counts(client):
    r = client.get("/v1/commodities")
    assert r.status_code == 200
    items = r.json()
    assert items, "expected commodities"
    assert all(c["observations"] > 0 and c["markets"] >= 1 for c in items)


def test_price_series_filters(client, raw_prices):
    df = dedupe_flag(clean_prices(raw_prices))
    any_market = int(df["market_id"].iloc[0])
    r = client.get("/v1/prices", params={"market_id": any_market, "limit": 5})
    assert r.status_code == 200
    rows = r.json()
    assert 0 < len(rows) <= 5
    dates = [row["date"] for row in rows]
    assert dates == sorted(dates)
    assert all(row["market_id"] == any_market for row in rows)


def test_price_series_unknown_market_404(client):
    assert client.get("/v1/prices", params={"market_id": 424242}).status_code == 404


def test_price_flag_validation(client):
    assert client.get("/v1/prices", params={"priceflag": "bogus"}).status_code == 422


def test_latest_prices(client):
    r = client.get("/v1/prices/latest")
    assert r.status_code == 200
    rows = r.json()
    keys = [(row["market_id"], row["commodity_id"]) for row in rows]
    assert len(keys) == len(set(keys)), "one row per market/commodity"


def test_movers_shape(client):
    r = client.get("/v1/insights/movers", params={"window_days": 365})
    assert r.status_code == 200
    for m in r.json():
        assert isinstance(m["pct_change"], float)
        assert m["last_usd"] > 0


def test_anomalies_shape(client):
    r = client.get("/v1/insights/anomalies", params={"threshold": 0.5})
    assert r.status_code == 200
    for a in r.json():
        assert a["baseline_points"] >= 6
        assert a["recent_median_usd"] > 0
