"""Fetch climate data for Zimbabwe via open APIs.

Primary: Open-Meteo Archive API (free, no key, CC BY-4.0)
Fallback: NASA POWER (free, no key)
CHIRPS is also available but requires heavier processing.

Approach: fetch daily series for each market/admin1 centroid,
aggregate to monthly for the warehouse. This mirrors markets
dataset - location from markets table, joined at query time.

Single location example uses Harare centroid; production ETL loops
over markets from SQLite to fill all provinces.
"""

import logging
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

from sokodata.config import RAW_DIR
from sokodata.core.fetch import fetch_json

log = logging.getLogger(__name__)

# Zimbabwe admin1 centroids (approx) - used when market table unavailable
ZIM_CENTROIDS = {
    "Harare": (-17.8292, 31.0530),
    "Bulawayo": (-20.15, 28.58),
    "Manicaland": (-18.96, 32.67),
    "Masvingo": (-20.07, 30.83),
    "Midlands": (-19.46, 29.81),
    "Mashonaland East": (-17.80, 31.50),
    "Mashonaland West": (-17.50, 30.00),
    "Mashonaland Central": (-17.20, 31.00),
    "Matabeleland North": (-19.00, 28.50),
    "Matabeleland South": (-21.00, 29.00),
}


def fetch_openmeteo_daily(
    latitude: float,
    longitude: float,
    start_date: str,
    end_date: str,
) -> pd.DataFrame:
    """Fetch daily precipitation + temperature from Open-Meteo Archive."""
    url = (
        "https://archive-api.open-meteo.com/v1/archive"
        f"?latitude={latitude}&longitude={longitude}"
        f"&start_date={start_date}&end_date={end_date}"
        "&daily=temperature_2m_mean,precipitation_sum,temperature_2m_max,temperature_2m_min"
        "&timezone=Africa%2FHarare"
    )
    try:
        data = fetch_json(url)
        daily = data.get("daily", {})
        dates = daily.get("time", [])
        tmean = daily.get("temperature_2m_mean", [])
        precip = daily.get("precipitation_sum", [])
        tmax = daily.get("temperature_2m_max", [])
        tmin = daily.get("temperature_2m_min", [])
        rows = []
        for i, d in enumerate(dates):
            rows.append(
                {
                    "date": d,
                    "latitude": latitude,
                    "longitude": longitude,
                    "tmean_c": tmean[i] if i < len(tmean) else None,
                    "tmax_c": tmax[i] if i < len(tmax) else None,
                    "tmin_c": tmin[i] if i < len(tmin) else None,
                    "precip_mm": precip[i] if i < len(precip) else None,
                    "source": "open-meteo",
                }
            )
        df = pd.DataFrame(rows)
        log.info("open-meteo %s,%s: %d days %s->%s", latitude, longitude, len(df), start_date, end_date)
        return df
    except Exception as e:
        log.warning("open-meteo fetch failed for %s,%s: %s", latitude, longitude, e)
        return pd.DataFrame(
            columns=["date", "latitude", "longitude", "tmean_c", "tmax_c", "tmin_c", "precip_mm", "source"]
        )


def fetch_climate_all(
    raw_dir: Path | None = None,
    admin1_list: list[str] | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    """Fetch climate for given admin1s (or all centroids).

    Defaults: last 365 days for all Zim admin1 centroids.
    Pass admin1_list e.g. ["Harare", "Masvingo"] to limit.
    """
    if end_date is None:
        end_date = date.today().isoformat()
    if start_date is None:
        start_date = (date.today() - timedelta(days=365)).isoformat()

    targets = {k: v for k, v in ZIM_CENTROIDS.items() if admin1_list is None or k in admin1_list}
    frames = []
    for admin1, (lat, lon) in targets.items():
        df = fetch_openmeteo_daily(lat, lon, start_date, end_date)
        if not df.empty:
            df["admin1"] = admin1
            frames.append(df)

    if not frames:
        return pd.DataFrame(
            columns=["date", "admin1", "latitude", "longitude", "tmean_c", "tmax_c", "tmin_c", "precip_mm", "source"]
        )
    out = pd.concat(frames, ignore_index=True)
    log.info("climate all: %d rows for %d locations", len(out), len(targets))
    return out
