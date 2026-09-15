"""Dataset registry for the SokoData commons.

Each dataset registers its metadata. The API's /v1/catalog reads this
so adding a new angle of Zimbabwe data is just adding an entry here
and a folder under src/sokodata/datasets/<name>/.
"""

from dataclasses import dataclass, field

@dataclass
class DatasetMeta:
    id: str  # e.g. "markets", "economy", "climate"
    label: str
    description: str
    sources: list[dict]  # {name, url, license}
    tables: list[str]  # SQLite table names
    update_frequency: str  # "weekly", "monthly", "daily", "static"
    coverage: str  # human readable, e.g. "2010-present, 486 markets"
    fetch_strategy: str  # "open_api", "html_scrape", "pdf_extract", "mixed"
    etl_module: str  # e.g. "sokodata.datasets.markets.etl"
    status: str = "active"  # active | stub | deprecated
    tags: list[str] = field(default_factory=list)


DATASETS: dict[str, DatasetMeta] = {
    "markets": DatasetMeta(
        id="markets",
        label="Food Market Prices",
        description="Retail food prices for ~486 Zimbabwean markets from WFP via HDX. USD-normalized, currency-safe.",
        sources=[
            {
                "name": "WFP Price Database via HDX",
                "url": "https://data.humdata.org/dataset/wfp-food-prices-for-zimbabwe",
                "license": "CC BY-IGO",
            }
        ],
        tables=["markets", "prices"],
        update_frequency="weekly",
        coverage="2010-01-15 to present, 27k observations, 31 commodities",
        fetch_strategy="open_api",
        etl_module="sokodata.datasets.markets.etl",
        status="active",
        tags=["agriculture", "food-security", "prices"],
    ),
    "economy": DatasetMeta(
        id="economy",
        label="Economy & Finance",
        description="ZiG/USD rates (RBZ), CPI/inflation (ZIMSTAT), fuel prices (ZERA). Mixed: World Bank API + HTML/PDF scraping.",
        sources=[
            {"name": "RBZ Market Rates", "url": "https://www.rbz.co.zw/", "license": "public"},
            {"name": "ZIMSTAT CPI", "url": "https://www.zimstat.co.zw/", "license": "public"},
            {"name": "ZERA Fuel Prices", "url": "https://www.zera.co.zw/", "license": "public"},
            {
                "name": "World Bank WDI (fallback CPI/FX)",
                "url": "https://data.worldbank.org/indicator/FP.CPI.TOTL.ZG",
                "license": "CC BY-4.0",
            },
        ],
        tables=["economy_rates", "economy_cpi", "economy_fuel"],
        update_frequency="weekly/monthly",
        coverage="2019-present (ZiG era), monthly CPI, weekly fuel",
        fetch_strategy="mixed",
        etl_module="sokodata.datasets.economy.etl",
        status="active",
        tags=["economy", "finance", "inflation", "fuel"],
    ),
    "climate": DatasetMeta(
        id="climate",
        label="Climate & Weather",
        description="Rainfall and temperature for Zimbabwe by admin1/market. Open APIs: Open-Meteo Archive + NASA POWER, CHIRPS fallback.",
        sources=[
            {
                "name": "Open-Meteo Archive API",
                "url": "https://open-meteo.com/en/docs/historical-weather-api",
                "license": "CC BY-4.0",
            },
            {
                "name": "NASA POWER",
                "url": "https://power.larc.nasa.gov/",
                "license": "public",
            },
            {
                "name": "CHIRPS Rainfall",
                "url": "https://www.chc.ucsb.edu/data/chirps",
                "license": "public",
            },
        ],
        tables=["climate_daily", "climate_monthly"],
        update_frequency="daily",
        coverage="1981-present, daily by market/admin1",
        fetch_strategy="open_api",
        etl_module="sokodata.datasets.climate.etl",
        status="active",
        tags=["climate", "weather", "rainfall", "agriculture"],
    ),
    "demographics": DatasetMeta(
        id="demographics",
        label="Demographics & Population",
        description="Population, growth and 2022 Census by province. World Bank WDI + ZIMSTAT census PDF/HTML scraping.",
        sources=[
            {
                "name": "World Bank WDI Population",
                "url": "https://data.worldbank.org/indicator/SP.POP.TOTL",
                "license": "CC BY-4.0",
            },
            {
                "name": "ZIMSTAT Census 2022",
                "url": "https://www.zimstat.co.zw/",
                "license": "public",
            },
        ],
        tables=["demo_annual", "demo_census"],
        update_frequency="annual/static",
        coverage="1960-present annual, 2022 census by province",
        fetch_strategy="mixed",
        etl_module="sokodata.datasets.demographics.etl",
        status="active",
        tags=["demographics", "population", "census"],
    ),
    "agriculture": DatasetMeta(
        id="agriculture",
        label="Agriculture & Food Production",
        description="Cereal yields, food/crop production indices and FAO maize. World Bank WDI + FAO FAOSTAT + Agritex scrape.",
        sources=[
            {"name": "World Bank WDI Agriculture", "url": "https://data.worldbank.org/indicator/AG.YLD.CREL.KG", "license": "CC BY-4.0"},
            {"name": "FAO FAOSTAT QCL", "url": "https://www.fao.org/faostat/en/#data/QCL", "license": "CC BY-4.0"},
            {"name": "Agritex / ZIMSTAT", "url": "https://www.zimstat.co.zw/", "license": "public"},
        ],
        tables=["agri_annual", "agri_fao_maize"],
        update_frequency="annual",
        coverage="1961-present annual yields and production",
        fetch_strategy="mixed",
        etl_module="sokodata.datasets.agriculture.etl",
        status="active",
        tags=["agriculture", "food-security", "yields"],
    ),
}


def list_datasets() -> list[DatasetMeta]:
    return list(DATASETS.values())


def get_dataset(dataset_id: str) -> DatasetMeta | None:
    return DATASETS.get(dataset_id)
