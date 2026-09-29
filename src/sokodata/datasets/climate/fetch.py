"""Fetch climate data for a country via open APIs.

Primary: Open-Meteo Archive API (free, no key, CC BY-4.0)
Fallback: NASA POWER (free, no key)
CHIRPS is also available but requires heavier processing.

Approach: fetch daily series for each admin1 centroid,
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

# Country-specific admin1 centroids (approx)
CENTROIDS = {
    "ZW": {
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
    },
    "KE": {
        "Nairobi": (-1.2921, 36.8219),
        "Mombasa": (-4.0435, 39.6682),
        "Kisumu": (-0.1022, 34.7617),
        "Nakuru": (-0.3031, 36.0800),
        "Eldoret": (0.5143, 35.2698),
        "Kakamega": (0.2827, 34.7519),
        "Machakos": (-1.5177, 37.2634),
        "Meru": (0.0463, 37.6558),
        "Nyeri": (-0.4201, 36.9476),
        "Kilifi": (-3.6305, 39.8499),
        "Kiambu": (-1.1699, 36.8331),
        "Kajiado": (-1.8500, 36.7833),
        "Uasin Gishu": (0.5000, 35.3000),
        "Trans-Nzoia": (1.0000, 35.0000),
        "Bungoma": (0.5667, 34.5667),
        "Kericho": (-0.3667, 35.2833),
        "Kisii": (-0.6833, 34.7667),
        "Nyamira": (-0.5667, 34.9333),
        "Migori": (-1.0667, 34.4667),
        "Homa Bay": (-0.5333, 34.4500),
        "Siaya": (0.0667, 34.2833),
        "Busia": (0.4667, 34.1167),
        "Vihiga": (0.0500, 34.7333),
        "Kakamega": (0.2827, 34.7519),
        "Bomet": (-0.7833, 35.3333),
        "Narok": (-1.0833, 35.8667),
        "Kajiado": (-1.8500, 36.7833),
        "Laikipia": (0.1333, 36.8000),
        "Samburu": (1.1000, 36.7333),
        "Marsabit": (2.3333, 37.9833),
        "Isiolo": (0.3500, 37.5833),
        "Meru": (0.0463, 37.6558),
        "Tharaka-Nithi": (0.0000, 37.9333),
        "Embu": (-0.5333, 37.4500),
        "Kitui": (-1.3667, 38.0167),
        "Machakos": (-1.5177, 37.2634),
        "Makueni": (-1.8000, 37.6167),
        "Nyandarua": (-0.1667, 36.3667),
        "Nyeri": (-0.4201, 36.9476),
        "Kirinyaga": (-0.5000, 37.2833),
        "Murang'a": (-0.7167, 37.1500),
        "Kiambu": (-1.1699, 36.8331),
        "Turkana": (3.1167, 35.6000),
        "West Pokot": (1.2500, 35.1167),
        "Elgeyo-Marakwet": (0.5000, 35.5000),
        "Nandi": (0.2000, 35.1167),
        "Baringo": (0.5000, 36.0000),
        "Laikipia": (0.1333, 36.8000),
        "Nakuru": (-0.3031, 36.0800),
        "Narok": (-1.0833, 35.8667),
        "Kajiado": (-1.8500, 36.7833),
        "Kericho": (-0.3667, 35.2833),
        "Bomet": (-0.7833, 35.3333),
        "Trans-Nzoia": (1.0000, 35.0000),
        "Uasin Gishu": (0.5143, 35.2698),
        "West Pokot": (1.2500, 35.1167),
        "Elgeyo-Marakwet": (0.5000, 35.5000),
        "Nandi": (0.2000, 35.1167),
        "Baringo": (0.5000, 36.0000),
        "Laikipia": (0.1333, 36.8000),
        "Nakuru": (-0.3031, 36.0800),
        "Narok": (-1.0833, 35.8667),
        "Kajiado": (-1.8500, 36.7833),
        "Kericho": (-0.3667, 35.2833),
        "Bomet": (-0.7833, 35.3333),
        "Trans-Nzoia": (1.0000, 35.0000),
        "Uasin Gishu": (0.5143, 35.2698),
        "West Pokot": (1.2500, 35.1167),
        "Elgeyo-Marakwet": (0.5000, 35.5000),
        "Nandi": (0.2000, 35.1167),
        "Baringo": (0.5000, 36.0000),
        "Laikipia": (0.1333, 36.8000),
        "Nakuru": (-0.3031, 36.0800),
        "Narok": (-1.0833, 35.8667),
        "Kajiado": (-1.8500, 36.7833),
        "Kericho": (-0.3667, 35.2833),
        "Bomet": (-0.7833, 35.3333),
    },
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
    country: str = "ZW",
    admin1_list: list[str] | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    """Fetch climate for given admin1s (or all centroids) for a country.

    Defaults: last 365 days for all country admin1 centroids.
    Pass admin1_list e.g. ["Nairobi", "Mombasa"] to limit.
    """
    if end_date is None:
        end_date = date.today().isoformat()
    if start_date is None:
        start_date = (date.today() - timedelta(days=365)).isoformat()

    centroids = CENTROIDS.get(country.upper(), CENTROIDS["ZW"])
    targets = {k: v for k, v in centroids.items() if admin1_list is None or k in admin1_list}
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
    log.info("climate all: %d rows for %d locations in %s", len(out), len(targets), country)
    return out