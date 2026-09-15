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
    "health": DatasetMeta(
        id="health",
        label="Health",
        description="Infant/under-5 mortality, immunization, health expenditure. World Bank WDI + MoHCC bulletin scrape.",
        sources=[
            {"name": "World Bank WDI Health", "url": "https://data.worldbank.org/indicator/SP.DYN.IMRT.IN", "license": "CC BY-4.0"},
            {"name": "MoHCC Zimbabwe", "url": "https://www.mohcc.gov.zw/", "license": "public"},
        ],
        tables=["health_annual"],
        update_frequency="annual",
        coverage="1960-present annual health indicators",
        fetch_strategy="mixed",
        etl_module="sokodata.datasets.health.etl",
        status="active",
        tags=["health", "mortality", "immunization"],
    ),
    "education": DatasetMeta(
        id="education",
        label="Education",
        description="Primary/secondary enrollment, literacy, completion. World Bank WDI + MoPSE scrape.",
        sources=[
            {"name": "World Bank WDI Education", "url": "https://data.worldbank.org/indicator/SE.PRM.NENR", "license": "CC BY-4.0"},
            {"name": "MoPSE Zimbabwe", "url": "https://www.mopse.gov.zw/", "license": "public"},
        ],
        tables=["education_annual"],
        update_frequency="annual",
        coverage="1960-present annual education indicators",
        fetch_strategy="mixed",
        etl_module="sokodata.datasets.education.etl",
        status="active",
        tags=["education", "literacy", "enrollment"],
    ),
    "energy": DatasetMeta(
        id="energy",
        label="Energy",
        description="Electricity access, consumption, renewable share. World Bank WDI + ZESA/ZERA scrape.",
        sources=[
            {"name": "World Bank WDI Energy", "url": "https://data.worldbank.org/indicator/EG.ELC.ACCS.ZS", "license": "CC BY-4.0"},
            {"name": "ZESA Holdings", "url": "https://www.zesa.co.zw/", "license": "public"},
            {"name": "ZERA", "url": "https://www.zera.co.zw/", "license": "public"},
        ],
        tables=["energy_annual"],
        update_frequency="annual",
        coverage="1960-present annual energy indicators",
        fetch_strategy="mixed",
        etl_module="sokodata.datasets.energy.etl",
        status="active",
        tags=["energy", "electricity", "renewable"],
    ),
    "water": DatasetMeta(
        id="water",
        label="Water & Sanitation",
        description="Safe/basic drinking water and sanitation. World Bank WDI + ZINWA dam levels scrape.",
        sources=[
            {"name": "World Bank WDI Water", "url": "https://data.worldbank.org/indicator/SH.H2O.SMDW.ZS", "license": "CC BY-4.0"},
            {"name": "ZINWA", "url": "https://www.zinwa.co.zw/", "license": "public"},
        ],
        tables=["water_annual"],
        update_frequency="annual",
        coverage="2000-present annual water/sanitation indicators",
        fetch_strategy="mixed",
        etl_module="sokodata.datasets.water.etl",
        status="active",
        tags=["water", "sanitation", "zinwa"],
    ),
    "transport": DatasetMeta(
        id="transport",
        label="Transport & Connectivity",
        description="Air departures, rail/road network, internet use. World Bank WDI + Ministry of Transport scrape.",
        sources=[
            {"name": "World Bank WDI Transport", "url": "https://data.worldbank.org/indicator/IS.AIR.DPRT", "license": "CC BY-4.0"},
            {"name": "Ministry of Transport Zimbabwe", "url": "https://www.transport.gov.zw/", "license": "public"},
        ],
        tables=["transport_annual"],
        update_frequency="annual",
        coverage="1970-present annual transport indicators",
        fetch_strategy="mixed",
        etl_module="sokodata.datasets.transport.etl",
        status="active",
        tags=["transport", "roads", "aviation"],
    ),
    "mining": DatasetMeta(
        id="mining",
        label="Mining & Minerals",
        description="Mineral rents, ore/metal exports, gold deliveries. World Bank WDI + Chamber of Mines / RBZ scrape.",
        sources=[
            {"name": "World Bank WDI Mining", "url": "https://data.worldbank.org/indicator/NY.GDP.TOTL.RT.ZS", "license": "CC BY-4.0"},
            {"name": "Chamber of Mines Zimbabwe", "url": "https://www.chamberofminesofzimbabwe.com/", "license": "public"},
            {"name": "RBZ Gold Deliveries", "url": "https://www.rbz.co.zw/", "license": "public"},
        ],
        tables=["mining_annual"],
        update_frequency="annual",
        coverage="1960-present annual mining indicators",
        fetch_strategy="mixed",
        etl_module="sokodata.datasets.mining.etl",
        status="active",
        tags=["mining", "gold", "minerals"],
    ),
    "governance": DatasetMeta(
        id="governance",
        label="Governance",
        description="CPIA property rights/transparency, women in parliament, military spending, gov debt. World Bank WDI + ZEC/Afrobarometer scrape.",
        sources=[
            {"name": "World Bank WDI Governance", "url": "https://data.worldbank.org/indicator/IQ.CPA.PROP.XQ", "license": "CC BY-4.0"},
            {"name": "ZEC Zimbabwe", "url": "https://www.zec.org.zw/", "license": "public"},
            {"name": "Afrobarometer Zimbabwe", "url": "https://www.afrobarometer.org/countries/zimbabwe/", "license": "CC BY"},
        ],
        tables=["governance_annual"],
        update_frequency="annual",
        coverage="2005-present CPIA + 1990-present parliament/military/debt",
        fetch_strategy="mixed",
        etl_module="sokodata.datasets.governance.etl",
        status="active",
        tags=["governance", "institutions", "elections"],
    ),
    "trade": DatasetMeta(
        id="trade",
        label="Trade",
        description="Exports/imports % GDP and merchandise values. World Bank WDI + ZimTrade/ZIMSTAT scrape.",
        sources=[
            {"name": "World Bank WDI Trade", "url": "https://data.worldbank.org/indicator/NE.EXP.GNFS.ZS", "license": "CC BY-4.0"},
            {"name": "ZimTrade", "url": "https://www.tradezimbabwe.com/", "license": "public"},
        ],
        tables=["trade_annual"],
        update_frequency="annual",
        coverage="1960-present annual trade indicators",
        fetch_strategy="mixed",
        etl_module="sokodata.datasets.trade.etl",
        status="active",
        tags=["trade", "exports", "imports"],
    ),
    "labour": DatasetMeta(
        id="labour",
        label="Labour & Jobs",
        description="Unemployment, participation, vulnerable employment. World Bank WDI + ILO/ZIMSTAT LFCLS scrape.",
        sources=[
            {"name": "World Bank WDI Labour", "url": "https://data.worldbank.org/indicator/SL.UEM.TOTL.ZS", "license": "CC BY-4.0"},
            {"name": "ZIMSTAT LFCLS", "url": "https://www.zimstat.co.zw/", "license": "public"},
        ],
        tables=["labour_annual"],
        update_frequency="annual",
        coverage="1991-present annual labour indicators",
        fetch_strategy="mixed",
        etl_module="sokodata.datasets.labour.etl",
        status="active",
        tags=["labour", "jobs", "unemployment"],
    ),
    "environment": DatasetMeta(
        id="environment",
        label="Environment",
        description="CO2 per capita, forest share/area, PM2.5. World Bank WDI + EMA scrape.",
        sources=[
            {"name": "World Bank WDI Environment", "url": "https://data.worldbank.org/indicator/EN.ATM.CO2E.PC", "license": "CC BY-4.0"},
            {"name": "EMA Zimbabwe", "url": "https://www.ema.co.zw/", "license": "public"},
        ],
        tables=["environment_annual"],
        update_frequency="annual",
        coverage="1960-present CO2/forest, 2010-present PM2.5",
        fetch_strategy="mixed",
        etl_module="sokodata.datasets.environment.etl",
        status="active",
        tags=["environment", "climate", "forest"],
    ),
    "poverty": DatasetMeta(
        id="poverty",
        label="Poverty & Inequality",
        description="Extreme/national poverty, Gini, shared prosperity. World Bank WDI + ZIMSTAT PICES scrape.",
        sources=[
            {"name": "World Bank WDI Poverty", "url": "https://data.worldbank.org/indicator/SI.POV.DDAY", "license": "CC BY-4.0"},
            {"name": "ZIMSTAT PICES", "url": "https://www.zimstat.co.zw/", "license": "public"},
        ],
        tables=["poverty_annual"],
        update_frequency="annual",
        coverage="1983-present poverty/Gini (sparse)",
        fetch_strategy="mixed",
        etl_module="sokodata.datasets.poverty.etl",
        status="active",
        tags=["poverty", "inequality", "gini"],
    ),
    "ict": DatasetMeta(
        id="ict",
        label="ICT & Digital",
        description="Internet use, mobile subscriptions, broadband. World Bank WDI + POTRAZ scrape.",
        sources=[
            {"name": "World Bank WDI ICT", "url": "https://data.worldbank.org/indicator/IT.NET.USER.ZS", "license": "CC BY-4.0"},
            {"name": "POTRAZ Zimbabwe", "url": "https://www.potraz.gov.zw/", "license": "public"},
        ],
        tables=["ict_annual"],
        update_frequency="annual",
        coverage="1960-present tel, 1990-present internet/mobile",
        fetch_strategy="mixed",
        etl_module="sokodata.datasets.ict.etl",
        status="active",
        tags=["ict", "telecom", "digital"],
    ),
    "finance": DatasetMeta(
        id="finance",
        label="Finance & Inclusion",
        description="Domestic/private credit, remittances, bank accounts. World Bank WDI + RBZ scrape.",
        sources=[
            {"name": "World Bank WDI Finance", "url": "https://data.worldbank.org/indicator/FS.AST.DOMS.GD.ZS", "license": "CC BY-4.0"},
            {"name": "RBZ", "url": "https://www.rbz.co.zw/", "license": "public"},
        ],
        tables=["finance_annual"],
        update_frequency="annual",
        coverage="1960-present domestic credit, 1970-present remittances",
        fetch_strategy="mixed",
        etl_module="sokodata.datasets.finance.etl",
        status="active",
        tags=["finance", "credit", "remittances"],
    ),
    "tourism": DatasetMeta(
        id="tourism",
        label="Tourism",
        description="Tourist arrivals and receipts. World Bank WDI + ZTA scrape.",
        sources=[
            {"name": "World Bank WDI Tourism", "url": "https://data.worldbank.org/indicator/ST.INT.ARVL", "license": "CC BY-4.0"},
            {"name": "ZTA", "url": "https://www.zimbabwetourism.net/", "license": "public"},
        ],
        tables=["tourism_annual"],
        update_frequency="annual",
        coverage="1995-present arrivals/receipts",
        fetch_strategy="mixed",
        etl_module="sokodata.datasets.tourism.etl",
        status="active",
        tags=["tourism", "arrivals"],
    ),
    "aid": DatasetMeta(
        id="aid",
        label="Aid & ODA",
        description="Net ODA, ODA % GNI, per capita. World Bank WDI + OECD scrape.",
        sources=[
            {"name": "World Bank WDI Aid", "url": "https://data.worldbank.org/indicator/DT.ODA.ALLD.CD", "license": "CC BY-4.0"},
            {"name": "OECD DAC", "url": "https://www.oecd.org/dac/", "license": "CC BY"},
        ],
        tables=["aid_annual"],
        update_frequency="annual",
        coverage="1960-present ODA",
        fetch_strategy="mixed",
        etl_module="sokodata.datasets.aid.etl",
        status="active",
        tags=["aid", "oda", "humanitarian"],
    ),
    "gender": DatasetMeta(
        id="gender",
        label="Gender",
        description="Women in parliament, female LFPR, primary parity, maternal mortality. World Bank WDI + UN Women scrape.",
        sources=[
            {"name": "World Bank WDI Gender", "url": "https://data.worldbank.org/indicator/SG.GEN.PARL.ZS", "license": "CC BY-4.0"},
            {"name": "UN Women", "url": "https://data.unwomen.org/country/zimbabwe", "license": "CC BY"},
        ],
        tables=["gender_annual"],
        update_frequency="annual",
        coverage="1990-present gender indicators",
        fetch_strategy="mixed",
        etl_module="sokodata.datasets.gender.etl",
        status="active",
        tags=["gender", "women", "parity"],
    ),
    "geospatial": DatasetMeta(
        id="geospatial",
        label="Geospatial & Boundaries",
        description="Admin boundaries (HDX COD-AB) and market GeoJSON. GeoJSON + metadata.",
        sources=[
            {"name": "HDX COD-AB ZWE", "url": "https://data.humdata.org/dataset/cod-ab-zwe", "license": "CC BY-IGO"},
        ],
        tables=["geospatial_metadata"],
        update_frequency="static",
        coverage="Admin0/1/2 boundaries + 486 markets GeoJSON",
        fetch_strategy="open_api",
        etl_module="sokodata.datasets.geospatial.etl",
        status="active",
        tags=["geospatial", "boundaries", "gis"],
    ),
}


def list_datasets() -> list[DatasetMeta]:
    return list(DATASETS.values())


def get_dataset(dataset_id: str) -> DatasetMeta | None:
    return DATASETS.get(dataset_id)
