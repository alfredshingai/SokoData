"""Regression tests for the Oct 2026 repair pass.

Each test pins a bug that shipped with the commons expansion and is now
fixed; if one of these fails again, the corresponding endpoint is broken
for real users, not just for lint.
"""

import os
import subprocess
import sys

from fastapi.testclient import TestClient

from sokodata.api.main import create_app
from sokodata.core.auth import check_rate_limit, create_api_key, hash_key, init_auth_db


def test_export_prices_csv(client):
    r = client.get("/v1/export/prices?format=csv")
    assert r.status_code == 200
    assert "text/csv" in r.headers["content-type"]
    header = r.text.splitlines()[0]
    assert "usdprice" in header


def test_export_markets_geojson(client):
    r = client.get("/v1/export/markets?format=geojson")
    assert r.status_code == 200
    body = r.json()
    assert body["type"] == "FeatureCollection"
    assert len(body["features"]) >= 1


def test_export_unknown_dataset_404(client):
    assert client.get("/v1/export/not_a_table").status_code == 404


def test_export_schema_tolerant(client):
    """The fixture prices table has no 'country' column; export must still work."""
    r = client.get("/v1/export/prices?format=csv&limit=5")
    assert r.status_code == 200


def test_analyze_anomalies_numeric(client):
    r = client.get("/v1/analyze/anomalies?table=prices&column=usdprice")
    assert r.status_code == 200
    body = r.json()
    assert {"table", "column", "anomaly_count", "anomalies"} <= set(body)
    for row in body["anomalies"]:
        assert "robust_z" in row


def test_analyze_anomalies_rejects_non_numeric(client):
    r = client.get("/v1/analyze/anomalies?table=prices&column=commodity")
    assert r.status_code == 400


def test_coverage_endpoint(client):
    r = client.get("/v1/coverage")
    assert r.status_code == 200
    body = r.json()
    assert body["totals"]["observations"] > 0
    assert any(c["country"] == "ZWE" for c in body["countries"])


def test_app_serves_on_missing_database(tmp_path):
    """Boot resilience: an absent warehouse must not take the API down."""
    app = create_app(tmp_path / "missing.db")
    with TestClient(app) as client:
        assert client.get("/health").status_code == 200
        assert client.get("/v1/markets").status_code == 200


def test_rate_limit_is_per_identity():
    """One anonymous client exhausting its budget must not throttle another."""
    check_rate_limit.__globals__["_rate_limit_cache"].clear()
    for _ in range(60):
        assert check_rate_limit("ip:1.2.3.4", 0)
    assert not check_rate_limit("ip:1.2.3.4", 0)
    assert check_rate_limit("ip:5.6.7.8", 0)


def test_alerts_cli_exits_cleanly_without_secrets(tmp_path):
    """python -m sokodata.alerts needs a __main__.py to run at all."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("TELEGRAM")}
    env["PYTHONPATH"] = "src"
    r = subprocess.run(
        [sys.executable, "-m", "sokodata.alerts"],
        capture_output=True,
        text=True,
        env=env,
        timeout=60,
    )
    assert r.returncode == 0, r.stderr


def test_etl_run_records_failures(tmp_path):
    """run_selected never raises; an unknown country lands in failures."""
    from sokodata.etl_run import run_selected

    ran, failures = run_selected({"markets"}, ["XX"], data_dir=tmp_path, db=tmp_path / "t.db")
    assert ran == 0
    assert "markets/XX" in failures


def test_api_key_roundtrip(tmp_path):
    db = tmp_path / "auth.db"
    init_auth_db(db)
    key_id, raw_key = create_api_key(name="test", tier=1, db_path=db)
    assert raw_key.startswith("sk_")

    import sqlite3

    conn = sqlite3.connect(db)
    try:
        stored = conn.execute(
            "SELECT key_hash, enabled FROM api_keys WHERE id=?", (key_id,)
        ).fetchone()
    finally:
        conn.close()
    assert stored[0] == hash_key(raw_key)  # the raw key is never stored
    assert stored[1] == 1
