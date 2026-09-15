# SokoData 🌾

**Open Data Commons for Zimbabwe. Markets, economy, climate, demographics, agriculture, health, education, energy, water, transport and mining — one API, built entirely on open data.**

> 🔴 **Live API: [sokodata.onrender.com](https://sokodata.onrender.com)** — interactive docs at [`/docs`](https://sokodata.onrender.com/docs)
> 🖥️ **Live dashboard: [alfredshingai.github.io/SokoData](https://alfredshingai.github.io/SokoData/)** — browse markets & prices in your browser, no install

[![CI](https://github.com/alfredshingai/sokodata/actions/workflows/ci.yml/badge.svg)](https://github.com/alfredshingai/sokodata/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.12%20%7C%203.13%20%7C%203.14-blue)](pyproject.toml)
[![Tests](https://img.shields.io/badge/tests-47%20passed-brightgreen)](#development)

## Why

A trader in Bulawayo, a farmer in Masvingo, an NGO monitoring food security — none of them can easily answer *"what does maize cost today, what is ZiG worth, and did it rain where that maize was grown?"*. Zimbabwe's data is fragmented across WFP, RBZ, ZIMSTAT, ZERA, and climate APIs — as raw CSVs, PDFs, and HTML tables: no unified API, no provenance, no product for end users.

**SokoData is the commons that turns those scattered sources into a clean, documented, queryable product** — one ETL per dataset, one catalog, one API, with honest analytics that survive Zimbabwe's currency history.

## What it gives you

**Markets (live, WFP via HDX CC BY-IGO):**
```console
$ curl sokodata.onrender.com/v1/insights/movers?window_days=90
```
> Fish (kapenta) at **Marula**: $6.10 → $10.53/kg (**+72%**)
> Oil (vegetable) at **Gokwe**: $1.70 → $2.74/L (**+61%**)

**Economy (mixed: World Bank API + RBZ/ZERA/ZIMSTAT scraping):**
```console
$ curl sokodata.onrender.com/v1/economy/cpi
$ curl sokodata.onrender.com/v1/economy/rates
$ curl sokodata.onrender.com/v1/economy/fuel
```

**Climate (open API: Open-Meteo + NASA POWER):**
```console
$ curl "sokodata.onrender.com/v1/climate/daily?admin1=Harare"
$ curl "sokodata.onrender.com/v1/climate/monthly?admin1=Masvingo"
```

**Demographics, Agriculture, Health + Education, Energy (WDI + FAO + scraping):**
```console
$ curl sokodata.onrender.com/v1/demographics/annual
$ curl sokodata.onrender.com/v1/agriculture/annual
$ curl sokodata.onrender.com/v1/health-stats/annual
$ curl sokodata.onrender.com/v1/education/annual
$ curl sokodata.onrender.com/v1/energy/annual
```

**Water, Transport, Mining (WDI + ZINWA / MoT / Chamber scrape):**
```console
$ curl sokodata.onrender.com/v1/water/annual
$ curl sokodata.onrender.com/v1/transport/annual
$ curl sokodata.onrender.com/v1/mining/annual
```

**Catalog - discover every dataset:**
```console
$ curl sokodata.onrender.com/v1/catalog
```
> `markets` (WFP), `economy` (WB + scraped), `climate` (Open-Meteo), `demographics` (WDI + ZIMSTAT), `agriculture` (WDI + FAO), `health` (WDI + MoHCC), `education` (WDI + MoPSE), `energy` (WDI + ZESA), `water` (WDI + ZINWA), `transport` (WDI + MoT), `mining` (WDI + Chamber/RBZ)

### API

| Endpoint | What it answers |
|---|---|
| `GET /v1/catalog` | All datasets, sources, licenses, freshness |
| `GET /v1/markets?q=&admin1=` | Market directory (486 markets, with coordinates) |
| `GET /v1/commodities?category=` | 31 commodities with coverage counts |
| `GET /v1/prices?market_id=&commodity_id=&start=&end=` | Raw price series (USD + local) |
| `GET /v1/prices/latest?commodity_id=` | Most recent price per market |
| `GET /v1/insights/movers?window_days=90` | Largest USD price changes per market/commodity |
| `GET /v1/insights/anomalies?threshold=2` | Prices deviating from their own 24-month robust norm |
| `GET /v1/economy/rates` | ZiG/USD rates (RBZ scrape + World Bank fallback) |
| `GET /v1/economy/cpi` | CPI / inflation (ZIMSTAT PDF + World Bank) |
| `GET /v1/economy/fuel` | Fuel prices by type (ZERA scrape) |
| `GET /v1/climate/daily?admin1=&start=&end=` | Daily precip + temp by admin1 (Open-Meteo) |
| `GET /v1/climate/monthly?admin1=` | Monthly aggregates |
| `GET /v1/demographics/annual` | Population, growth, urban share (WDI) |
| `GET /v1/demographics/census?admin1=` | 2022 Census by province (ZIMSTAT scrape) |
| `GET /v1/agriculture/annual` | Cereal yield, agri GDP, food indices (WDI) |
| `GET /v1/agriculture/fao/maize` | Maize tonnes (FAO FAOSTAT) |
| `GET /v1/health-stats/annual` | Infant/under-5 mortality, immunization (WDI) |
| `GET /v1/education/annual` | Enrollment, literacy, completion (WDI) |
| `GET /v1/energy/annual` | Electricity access, use, renewables (WDI) |
| `GET /v1/water/annual` | Safe/basic water + sanitation (WDI) |
| `GET /v1/transport/annual` | Air, rail, road, internet use (WDI) |
| `GET /v1/mining/annual` | Mineral rents, ore/metal exports (WDI) |
| `GET /health` | Dataset coverage + data provenance |

Interactive OpenAPI docs ship at `/docs` when the server runs.

## Quickstart

```bash
pip install -e ".[dev]"          # add [pdf] for ZIMSTAT/ZERA PDF extraction: pip install -e ".[dev,pdf]"

# build the commons (all 11 datasets)
python -m sokodata.etl_run

# or run one dataset at a time:
python -m sokodata.datasets.markets.etl
python -m sokodata.datasets.economy.etl
python -m sokodata.datasets.climate.etl --admin1 Harare --start 2024-01-01
python -m sokodata.datasets.demographics.etl
python -m sokodata.datasets.agriculture.etl
python -m sokodata.datasets.health.etl
python -m sokodata.datasets.education.etl
python -m sokodata.datasets.energy.etl
python -m sokodata.datasets.water.etl
python -m sokodata.datasets.transport.etl
python -m sokodata.datasets.mining.etl

# legacy shim still works:
python -m sokodata.etl.run --skip-fetch

# serve the API
uvicorn sokodata.api.main:app --port 8000
```

To reuse already-downloaded CSVs: `python -m sokodata.datasets.markets.etl --skip-fetch` (expects them in `data/raw/`).

## Strategy: where there's no API, scrape

The commons principle: **open API first, HTML/PDF scraping where no API exists, graceful fallback always.**

*   **Markets** - `open_api` (HDX CSV, weekly) - `src/sokodata/datasets/markets/fetch.py`
*   **Economy** - `mixed`: World Bank WDI JSON (CPI/FX, stable fallback) + HTML table scraping for RBZ rates (`fetch_html_tables` + regex) + HTML/PDF for ZERA fuel + PDF extraction for ZIMSTAT CPI via `pdfplumber`. See `src/sokodata/core/fetch.py` for `fetch_html_tables`, `fetch_html_text`, `extract_pdf_tables`, `parse_fuel_text`. Scrapers log warnings and return `[]` if the upstream page/PDF changes — they never kill the ETL.
*   **Climate** - `open_api` (Open-Meteo Archive + NASA POWER, daily, 1981-present) - no scraping needed. Fetch by `admin1` centroid, stored as `climate_daily`/`climate_monthly`.

Adding a new angle = add `src/sokodata/datasets/<name>/` with `fetch.py/clean.py/store.py/etl.py` and register it in `src/sokodata/core/registry.py`. The unified runner `src/sokodata/etl_run.py` and `GET /v1/catalog` pick it up automatically.

## Deploy (free tier)

The repo ships a [Render Blueprint](render.yaml) — one click deploys the API:

1. Sign in at [render.com](https://render.com) with GitHub
2. **New → Blueprint** → pick `alfredshingai/SokoData` → **Apply**
3. Done — Render runs `python -m sokodata.etl_run` (rebuilds all datasets) and starts the API on every boot

Free-tier notes: the service sleeps after ~15 min without traffic (first request after that takes ~1 min while the warehouse rebuilds), and the disk is ephemeral — the SQLite file is rebuilt from source data each boot by design.

## Telegram alerts

A GitHub Actions cron job posts a daily price digest (biggest movers + unusual prices) to a Telegram channel at 08:00 Harare time.

Setup, once:

1. In Telegram, message **@BotFather** → `/newbot` → choose a name and a `..._bot` username → save the **token** it gives you
2. Create a **public channel** (e.g. `@soko_prices`) and add your bot as an administrator
3. Add repository secrets ([Settings → Secrets → Actions](../../settings/secrets/actions)): `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` (e.g. `@soko_prices`)
4. Trigger a test send from the [Telegram price digest workflow](../../actions/workflows/alerts.yml) → **Run workflow**

Anyone who wants alerts just joins the channel. Per-user subscriptions are on the roadmap once the project has persistent storage.

## Web dashboard

A zero-dependency, mobile-first dashboard lives in [`docs/`](docs/index.html) (vanilla HTML/CSS/JS + Chart.js from CDN, no build step). It ships with the repo and is served by GitHub Pages — data comes straight from the public API, which allows cross-origin browser requests (CORS `GET`).

Run it locally against your local API: `cd docs && python -m http.server 8899` → http://127.0.0.1:8899

## WhatsApp bot

Send any message to our WhatsApp number and get the live digest back (greeting first, prices after). Built on the official [WhatsApp Cloud API](https://developers.facebook.com/docs/whatsapp/cloud-api) — free because the bot only *replies* to user-initiated messages.

Setup, once:

1. Create an app at [developers.facebook.com](https://developers.facebook.com) → add the **WhatsApp** product → note the **Phone number ID** and temporary **access token** (API Setup page)
2. Add the test number as a recipient (dev mode allows 5 numbers; production needs business verification)
3. Webhooks: callback URL `https://sokodata.onrender.com/webhooks/whatsapp`, verify token = any string you choose, subscribe to the **messages** field
4. Set env vars on Render (`WHATSAPP_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_VERIFY_TOKEN`) or as GitHub secrets

The dev access token expires every 24h — refresh it on the API Setup page, or generate a permanent token via Business Settings when you verify the business.

## Architecture

 ```
  Commons                              FastAPI
  datasets/markets ─┐                   ├─ /v1/catalog
   HDX WFP (CSV)                    ├─ /v1/markets, /v1/commodities, /v1/prices
  datasets/economy ─┤                   ├─ /v1/economy/*, /v1/climate/*
  datasets/climate ─┤── SQLite ─────────┤  /v1/demographics/*, /v1/agriculture/*
  datasets/demographics ─┤              ├─ /v1/health-stats/*, /v1/education/*
  datasets/agriculture/health/edu/energy ┤  /v1/energy/*, /v1/water/*, /v1/transport/*
  datasets/water/transport/mining ─┘    └─ /v1/mining/*, /v1/insights/*, /health
                                        core/fetch: open_api | html_scrape | pdf_extract
```
```

*   **Zero-infra warehouse** — SQLite with enforced natural keys and indexes; swap for Postgres later without touching the API layer. Per-dataset tables (`prices`, `economy_*`, `climate_*`) + `dataset_meta`.
*   **Currency-safe analytics** — every temporal computation uses WFP's USD conversion, with broken hyperinflation-era conversions detected and nulled at load time (see [docs/data_dictionary.md](docs/data_dictionary.md) for the full rules and counts).
*   **Commons registry** — `src/sokodata/core/registry.py` is the catalog of record. `GET /v1/catalog` and `etl_run.py` read it; new dataset = new folder + registry entry.
*   **Graceful scraping** — `src/sokodata/core/fetch.py` atomic downloads, `fetch_html_tables` / `extract_pdf_tables` / `parse_fuel_text` log and return `[]` on upstream change instead of raising; ETL continues with open-API fallback.

## Data credit & license

Data: [World Food Programme Price Database via HDX](https://data.humdata.org/dataset/wfp-food-prices-for-zimbabwe), licensed [CC BY-IGO](https://data.humdata.org/dataset/wfp-food-prices-for-zimbabwe) + [World Bank WDI](https://data.worldbank.org/) CC BY-4.0 + [Open-Meteo](https://open-meteo.com/) CC BY-4.0. Each dataset surfaces its own attribution via `/v1/catalog/{id}` and the existing `/health`. Code: MIT — see [LICENSE](LICENSE).

## Roadmap

- [x] Commons foundation: `core/registry` + `core/fetch` (open_api / html_scrape / pdf_extract)
- [x] Markets dataset (WFP, 27k obs, 486 markets) + API + dashboard
- [x] Economy dataset (World Bank + RBZ/ZERA/ZIMSTAT scrapers) + `/v1/economy/*`
- [x] Climate dataset (Open-Meteo/NASA POWER, daily 1981-present) + `/v1/climate/*`
- [x] Demographics (WDI + ZIMSTAT 2022 Census) + `/v1/demographics/*`
- [x] Agriculture (WDI + FAO FAOSTAT + Agritex scrape) + `/v1/agriculture/*`
- [x] Health (WDI + MoHCC scrape) + `/v1/health-stats/*`
- [x] Education (WDI + MoPSE scrape) + `/v1/education/*`
- [x] Energy (WDI + ZESA/ZERA scrape) + `/v1/energy/*`
- [x] Water (WDI + ZINWA scrape) + `/v1/water/*`
- [x] Transport (WDI + MoT scrape) + `/v1/transport/*`
- [x] Mining (WDI + Chamber/RBZ scrape) + `/v1/mining/*`
- [x] Unified catalog `GET /v1/catalog` (11 datasets) + unified ETL `python -m sokodata.etl_run`
- [x] Telegram digest (channel push, GitHub Actions cron)
- [x] WhatsApp bot (on-demand digest replies via Cloud API)
- [ ] WhatsApp push notifications (paid template messages) + per-user subscriptions
- [ ] Extend to all 98 countries in the WFP feed (config-driven, same pipeline)
- [ ] Governance + Geospatial boundaries as next commons pillars
- [ ] Seasonal baselines + harvest-cycle forecasting (ML) linking markets ↔ climate ↔ economy ↔ agriculture
- [ ] Digital Public Goods (DPG) submission as a commons

## Development

```bash
pip install -e ".[dev]"          # 47 tests: cleaning rules, warehouse, API, analytics, commons
# for PDF extraction:
pip install -e ".[dev,pdf]"
ruff check .          # lint
pytest -q
```

CI runs lint + tests on Python 3.12/3.13/3.14. Pull requests welcome — pick an issue or open one describing the problem first. To add a new dataset: copy `src/sokodata/datasets/climate/` as a template, implement `fetch/clean/store/etl`, register in `core/registry.py`, and add `catalog` entry.

---

Built by [Alfred Shingai](https://github.com/alfredshingai). Not affiliated with WFP or HDX.
