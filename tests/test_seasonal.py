"""Analytics tests with synthetic series where the answer is known."""

import pandas as pd

from sokodata.analysis.seasonal import anomalies, coverage, dedupe_flag, movers


def make_df(rows):
    df = pd.DataFrame(
        rows,
        columns=[
            "date",
            "market_id",
            "market",
            "commodity_id",
            "commodity",
            "usdprice",
            "priceflag",
        ],
    ).assign(
        category="cereals and tubers", unit="KG", currency="ZWL", price=1.0, pricetype="Retail"
    )
    df["date"] = pd.to_datetime(df["date"])
    return df


def test_dedupe_flag_prefers_aggregate():
    rows = [
        ("2025-01-15", 1, "A", 10, "Maize", 1.0, "actual"),
        ("2025-01-15", 1, "A", 10, "Maize", 2.0, "aggregate"),
    ]
    out = dedupe_flag(make_df(rows))
    assert len(out) == 1
    assert out.iloc[0]["usdprice"] == 2.0


def test_movers_pct_change():
    rows = []
    # six stable months at 0.50, then a doubling in the last 30 days
    for month in range(1, 7):
        rows.append((f"2025-{month:02d}-15", 1, "A", 10, "Maize", 0.50, "aggregate"))
    rows.append(("2025-11-20", 1, "A", 10, "Maize", 1.00, "aggregate"))
    result = movers(make_df(rows), window_days=30)
    assert len(result) == 1
    assert result[0]["pct_change"] == 100.0


def test_movers_skips_long_reporting_gaps():
    # 0.50 in early 2024, then 1.00 two years later: a data gap, not a signal
    rows = [
        ("2024-01-15", 1, "A", 10, "Maize", 0.50, "aggregate"),
        ("2026-04-15", 1, "A", 10, "Maize", 1.00, "aggregate"),
    ]
    assert movers(make_df(rows), window_days=90) == []


def test_anomalies_flags_spike_above_recent_norm():
    rows = []
    # a year of stable-but-varying months around 1.0, then a spike to 3.0
    for i, month in enumerate(range(1, 13)):
        value = 0.9 if i % 2 == 0 else 1.1
        rows.append((f"2024-{month:02d}-15", 1, "A", 10, "Maize", value, "aggregate"))
    rows.append(("2025-01-15", 1, "A", 10, "Maize", 3.0, "aggregate"))
    result = anomalies(make_df(rows), threshold=2.0)
    assert len(result) == 1
    assert result[0]["z"] > 2
    assert result[0]["usdprice"] == 3.0
    assert result[0]["recent_median_usd"] == 1.0
    assert result[0]["baseline_points"] == 12


def test_anomalies_skips_stale_series():
    # spikes in a series that stopped reporting long ago are not actionable
    rows = [
        (f"2024-{month:02d}-15", 1, "A", 10, "Maize", 0.9 if month % 2 else 1.1, "aggregate")
        for month in range(1, 13)
    ]
    rows.append(("2025-01-15", 1, "A", 10, "Maize", 3.0, "aggregate"))
    # a different series still reporting at the global newest date
    for month in range(1, 13):
        rows.append((f"2025-{month:02d}-15" if month < 12 else "2025-12-15",
                     2, "B", 10, "Maize", 1.0 + 0.01 * (month % 2), "aggregate"))

    result = anomalies(make_df(rows), threshold=2.0)
    assert all(r["market_id"] == 2 for r in result)


def test_anomalies_ignores_insufficient_baseline():
    rows = [
        ("2024-06-15", 1, "A", 10, "Maize", 1.0, "aggregate"),
        ("2025-06-15", 1, "A", 10, "Maize", 9.0, "aggregate"),
    ]
    assert anomalies(make_df(rows)) == []


def test_anomalies_ignores_flat_history():
    # constant history -> MAD = 0 -> z is undefined, series must be skipped
    rows = [
        (f"2024-{month:02d}-15", 1, "A", 10, "Maize", 1.0, "aggregate")
        for month in range(1, 13)
    ]
    rows.append(("2025-01-15", 1, "A", 10, "Maize", 3.0, "aggregate"))
    assert anomalies(make_df(rows)) == []


def test_coverage_counts():
    rows = [
        ("2025-01-15", 1, "A", 10, "Maize", 1.0, "actual"),
        ("2025-01-15", 1, "A", 10, "Maize", 2.0, "aggregate"),
        ("2025-02-15", 2, "B", 11, "Rice", 3.0, "actual"),
    ]
    cov = coverage(make_df(rows))
    assert cov["markets"] == 2
    assert cov["commodities"] == 2
    assert cov["observations"] == 2  # deduped
