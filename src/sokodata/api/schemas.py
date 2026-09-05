"""Pydantic response models for the SokoData API."""

from datetime import date as Date

from pydantic import BaseModel


class Market(BaseModel):
    market_id: int
    market: str
    countryiso3: str | None = None
    admin1: str | None = None
    admin2: str | None = None
    latitude: float | None = None
    longitude: float | None = None


class Commodity(BaseModel):
    commodity_id: int
    commodity: str
    category: str
    unit: str
    observations: int
    markets: int


class PricePoint(BaseModel):
    date: Date
    market_id: int
    market: str
    commodity_id: int
    commodity: str
    unit: str
    priceflag: str
    pricetype: str
    currency: str
    price: float
    usdprice: float | None = None


class Mover(BaseModel):
    market_id: int
    market: str
    commodity_id: int
    commodity: str
    unit: str
    prev_date: Date
    prev_usd: float
    last_date: Date
    last_usd: float
    pct_change: float


class Anomaly(BaseModel):
    market_id: int
    market: str
    commodity_id: int
    commodity: str
    unit: str
    date: Date
    usdprice: float
    recent_median_usd: float
    z: float
    baseline_points: int


class Coverage(BaseModel):
    observations: int
    markets: int
    commodities: int
    first_date: Date | None = None
    last_date: Date | None = None


class Health(BaseModel):
    status: str
    version: str
    coverage: Coverage
    data_credit: dict[str, str]
