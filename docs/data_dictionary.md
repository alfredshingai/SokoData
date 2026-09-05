# Data Dictionary

## Provenance

| | |
|---|---|
| Source | World Food Programme Price Database, via [HDX (OCHA)](https://data.humdata.org/dataset/wfp-food-prices-for-zimbabwe) |
| License | CC BY-IGO (attribution required — SokoData surfaces it at `/health`) |
| Coverage | 2010-01-15 → 2026-05-15, 27,468 retail price observations, 486 market records (336 with prices), 31 commodities |
| Refresh | Upstream updates ~weekly; re-run the ETL to pull the latest |

## Tables

### `markets`

| Column | Type | Description |
|---|---|---|
| `market_id` | INTEGER PK | WFP market identifier |
| `market` | TEXT | Market name (e.g. `Mbare`) |
| `countryiso3` | TEXT | ISO-3 country code (`ZWE`) |
| `admin1` / `admin2` | TEXT | Province / district |
| `latitude` / `longitude` | REAL | Market coordinates |

### `prices`

Natural key: `(date, market_id, commodity_id, pricetype, priceflag)` — enforced as a PRIMARY KEY.

| Column | Type | Description |
|---|---|---|
| `date` | TEXT (ISO) | Observation date (WFP reports mid-month) |
| `market_id` | INTEGER FK → markets | |
| `commodity_id` | INTEGER | WFP commodity identifier |
| `commodity` | TEXT | e.g. `Maize meal`, `Oil (vegetable)` |
| `category` | TEXT | One of: cereals and tubers, pulses and nuts, oil and fats, meat/fish/eggs, miscellaneous food, non-food |
| `unit` | TEXT | `KG`, `L`, `100 ML`, `250 G` |
| `priceflag` | TEXT | `actual` (single observation) or `aggregate` (market-level aggregation published by WFP) |
| `pricetype` | TEXT | `Retail` (Zimbabwe dataset is retail-only) |
| `currency` | TEXT | `ZWL` (local-currency label, kept unchanged across the 2024 ZiG reform) or `USD` |
| `price` | REAL | Price in `currency` — **never altered by cleaning** |
| `usdprice` | REAL | WFP's USD conversion — **may be nulled by cleaning**, see below |

## Cleaning rules (`sokodata.etl.clean`)

1. **Schema guard** — the exact upstream column set is enforced; any drift raises `SchemaDrift` instead of silently loading garbage.
2. **Type coercion** — dates parse as ISO; prices coerce to float; rows without a valid date/market/commodity/price are dropped.
3. **Deduplication** — duplicate natural keys keep the last occurrence.
4. **Implausible USD nulling** — WFP's `usdprice` is unreliable for local-currency rows around the 2024 ZiG currency reform (the hyperinflation-era official-rate conversions produce values like $0.0017/kg of rice; **16,022 of 27,468 rows** were affected). Each commodity's median post-2024 USD price is used as a sanity reference, and conversions below **10%** of that reference are set to NULL. The local-currency `price` is always preserved. Commodities with no post-2024 rows are untouched.
5. **Flag preference (analytics only)** — where a market publishes both `aggregate` and `actual` rows for the same date, analytics use the `aggregate`.

## Analytics conventions (`sokodata.analysis.seasonal`)

- **All temporal analytics use `usdprice`**, never local-currency prices: the `ZWL` label spans the 2024 redenomination, so local-currency deltas across years are meaningless.
- **Movers** require a prior observation within 400 days — a change measured across a longer reporting gap is a data artifact, not a market signal.
- **Anomalies** compare each series' latest price against the median of its own trailing 24 months using a robust z-score (MAD-based, σ = 1.4826 × MAD). Series with a flat trailing window (MAD = 0) or whose latest observation is more than **90 days stale** are skipped. Calendar-month seasonal baselines were evaluated and rejected: WFP market coverage rotates, so most series lack same-month history.
