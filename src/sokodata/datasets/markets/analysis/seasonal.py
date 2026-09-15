"""Market analytics on USD-normalized prices.

All functions take a "long" DataFrame with columns
``[date, market_id, market, commodity_id, commodity, usdprice, priceflag]``
and return plain dicts ready for JSON responses.

Why USD: the local-currency column keeps the "ZWL" label across the 2024
ZiG redenomination, so local-currency deltas are meaningless across years.
USD price is the comparable series (WFP computes it from parallel-market
and official rates at observation time).
"""

import pandas as pd

# Aggregated rows are market-level aggregates published by WFP; use them for
# analytics when present, falling back to actual rows. Keep both otherwise.
FLAG_PRIORITY = {"aggregate": 0, "actual": 1}


def dedupe_flag(df: pd.DataFrame) -> pd.DataFrame:
    """Prefer 'aggregate' rows over 'actual' for the same (date, market, commodity)."""
    out = df.copy()
    out["_flag_rank"] = out["priceflag"].map(FLAG_PRIORITY).fillna(9)
    out = out.sort_values(["date", "market_id", "commodity_id", "_flag_rank"])
    out = out.drop_duplicates(subset=["date", "market_id", "commodity_id"], keep="first")
    return out.drop(columns="_flag_rank")


def movers(
    df: pd.DataFrame,
    *,
    window_days: int = 90,
    limit: int = 20,
    min_baseline: int = 2,
    max_gap_days: int = 400,
) -> list[dict]:
    """Largest USD price changes per (market, commodity) over a trailing window.

    A series qualifies if it has a price inside the window and a price at
    least ``min_baseline`` observations before the window start, no further
    back than ``max_gap_days`` — a change measured across a long reporting
    gap is a data artifact, not a market signal.
    """
    s = dedupe_flag(df)
    s = s.dropna(subset=["usdprice"])
    end = s["date"].max()
    if pd.isna(end):
        return []
    start = end - pd.Timedelta(days=window_days)

    results: list[dict] = []
    for (_mkt, _com), g in s.groupby(["market_id", "commodity_id"]):
        g = g.sort_values("date")
        recent = g[g["date"] > start]
        prior = g[g["date"] <= start]
        if recent.empty or len(prior) < min_baseline:
            continue
        last = recent.iloc[-1]
        prev = prior.iloc[-1]
        if prev["usdprice"] <= 0:
            continue
        if (last["date"] - prev["date"]).days > max_gap_days:
            continue
        pct = (last["usdprice"] - prev["usdprice"]) / prev["usdprice"] * 100
        results.append(
            {
                "market_id": int(_mkt),
                "market": last["market"],
                "commodity_id": int(_com),
                "commodity": last["commodity"],
                "unit": last["unit"],
                "prev_date": prev["date"].date().isoformat(),
                "prev_usd": round(float(prev["usdprice"]), 4),
                "last_date": last["date"].date().isoformat(),
                "last_usd": round(float(last["usdprice"]), 4),
                "pct_change": round(float(pct), 2),
            }
        )

    results.sort(key=lambda r: abs(r["pct_change"]), reverse=True)
    return results[:limit]


def anomalies(
    df: pd.DataFrame,
    *,
    threshold: float = 2.0,
    baseline_months: int = 24,
    min_baseline: int = 6,
    max_staleness_days: int = 90,
    limit: int = 50,
) -> list[dict]:
    """Latest observations deviating strongly from their own recent norm.

    Baseline per (market, commodity): the median of that series' prices over
    the ``baseline_months`` preceding its latest observation. Deviation is a
    robust z-score using the median absolute deviation (MAD), which tolerates
    the outlier-heavy tails of food-price data.

    Series whose latest observation is older than ``max_staleness_days``
    (relative to the dataset's newest date) are skipped — flagging a market
    that stopped reporting a year ago is not actionable.

    Why not calendar-month seasonality: WFP market coverage rotates, so most
    series lack same-month history. A trailing robust baseline works with
    sparse, rotating coverage; seasonal refinement is a roadmap item.
    """
    s = dedupe_flag(df)
    s = s.dropna(subset=["usdprice"])
    if s.empty:
        return []
    newest = s["date"].max()

    results: list[dict] = []
    for (_mkt, _com), g in s.groupby(["market_id", "commodity_id"]):
        g = g.sort_values("date")
        if len(g) < min_baseline + 1:
            continue
        last = g.iloc[-1]
        if (newest - last["date"]).days > max_staleness_days:
            continue
        window_start = last["date"] - pd.DateOffset(months=baseline_months)
        prior = g[(g["date"] >= window_start) & (g["date"] < last["date"])]
        if len(prior) < min_baseline:
            continue

        median = float(prior["usdprice"].median())
        mad = float((prior["usdprice"] - median).abs().median())
        sigma = 1.4826 * mad
        if sigma <= 0:
            continue
        z = (float(last["usdprice"]) - median) / sigma
        if abs(z) >= threshold:
            results.append(
                {
                    "market_id": int(_mkt),
                    "market": last["market"],
                    "commodity_id": int(_com),
                    "commodity": last["commodity"],
                    "unit": last["unit"],
                    "date": last["date"].date().isoformat(),
                    "usdprice": round(float(last["usdprice"]), 4),
                    "recent_median_usd": round(median, 4),
                    "z": round(z, 2),
                    "baseline_points": int(len(prior)),
                }
            )

    results.sort(key=lambda r: abs(r["z"]), reverse=True)
    return results[:limit]


def coverage(df: pd.DataFrame) -> dict:
    """Dataset-level stats for the /health and README numbers."""
    s = dedupe_flag(df)
    return {
        "observations": int(len(s)),
        "markets": int(s["market_id"].nunique()),
        "commodities": int(s["commodity_id"].nunique()),
        "first_date": s["date"].min().date().isoformat() if not s.empty else None,
        "last_date": s["date"].max().date().isoformat() if not s.empty else None,
    }


__all__ = ["anomalies", "coverage", "dedupe_flag", "movers"]
