# SokoData 🌾

**Open market-price intelligence for African food markets. Starting with Zimbabwe, built entirely on open data.**

[![CI](https://github.com/alfredshingai/sokodata/actions/workflows/ci.yml/badge.svg)](https://github.com/alfredshingai/sokodata/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.12%20%7C%203.13%20%7C%203.14-blue)](pyproject.toml)
[![Tests](https://img.shields.io/badge/tests-28%20passed-brightgreen)](#development)

## Why

A trader in Bulawayo, a farmer in Masvingo, an NGO monitoring food security — none of them can easily answer *"what does maize cost today at the markets near me, and is that normal?"*. The World Food Programme publishes [weekly retail prices](https://data.humdata.org/dataset/wfp-food-prices-for-zimbabwe) for ~300 Zimbabwean markets under CC BY-IGO, but as raw analyst CSVs: no API, no alerts, no product for end users, and a 2024 currency reform buried in the data that breaks naive price comparisons.

**SokoData turns that feed into a clean, documented, queryable product** — an ETL pipeline, a REST API, and honest analytics that survive Zimbabwe's currency history.

## What it gives you (live examples from real data)

```console
$ curl localhost:8000/v1/insights/movers?window_days=90
```
> Fish (kapenta) at **Marula**: $6.10 → $10.53/kg (**+72%**)
> Oil (vegetable) at **Gokwe**: $1.70 → $2.74/L (**+61%**)

```console
$ curl localhost:8000/v1/insights/anomalies
```
> Oil at **Tongogara Refugee Camp**: $2.22/L vs $1.51 recent norm (robust z = 47.9)
> Maize meal at **Marula**: $0.63/kg vs $0.70 norm (z = −4.7) — cheaper than usual

### API

| Endpoint | What it answers |
|---|---|
| `GET /v1/markets?q=&admin1=` | Market directory (486 markets, with coordinates) |
| `GET /v1/commodities?category=` | 31 commodities with coverage counts |
| `GET /v1/prices?market_id=&commodity_id=&start=&end=` | Raw price series (USD + local) |
| `GET /v1/prices/latest?commodity_id=` | Most recent price per market |
| `GET /v1/insights/movers?window_days=90` | Largest USD price changes per market/commodity |
| `GET /v1/insights/anomalies?threshold=2` | Prices deviating from their own 24-month robust norm |
| `GET /health` | Dataset coverage + data provenance |

Interactive OpenAPI docs ship at `/docs` when the server runs.

## Quickstart

```bash
pip install -e ".[dev]"

# build the warehouse (downloads ~3.5MB CSV from HDX)
python -m sokodata.etl.run

# serve the API
uvicorn sokodata.api.main:app --port 8000
```

To reuse already-downloaded CSVs: `python -m sokodata.etl.run --skip-fetch` (expects them in `data/raw/`).

## Architecture

```
HDX (WFP price DB, weekly)                      FastAPI
  │  fetch.py  (atomic download)                 ├─ /v1/markets
  ▼                                              ├─ /v1/commodities
clean.py  ── schema guard, dedupe,               ├─ /v1/prices, /v1/prices/latest
           implausible-USD nulling               ├─ /v1/insights/movers
  ▼                                              └─ /v1/insights/anomalies
store.py  ── SQLite warehouse               ◄──── analytics read the warehouse;
  ▼                                              seasonal.py computes movers +
etl.run.py ─ CLI orchestrator                    anomalies on USD-normalized data
```

- **Zero-infra warehouse** — SQLite with enforced natural keys and indexes; swap for Postgres later without touching the API layer.
- **Currency-safe analytics** — every temporal computation uses WFP's USD conversion, with broken hyperinflation-era conversions detected and nulled at load time (see [docs/data_dictionary.md](docs/data_dictionary.md) for the full rules and counts).
- **Honest analytics** — reporting-gap guards, staleness guards, robust (MAD-based) statistics, and the reasons documented where you'll read them.

## Data credit & license

Data: [World Food Programme Price Database via HDX](https://data.humdata.org/dataset/wfp-food-prices-for-zimbabwe), licensed [CC BY-IGO](https://data.humdata.org/dataset/wfp-food-prices-for-zimbabwe). This project ships that attribution through the API (`/health`). Code: MIT — see [LICENSE](LICENSE).

## Roadmap

- [ ] Telegram/WhatsApp price alerts (per market & commodity subscriptions)
- [ ] Web dashboard (mobile-first, market comparison + charts)
- [ ] Extend to all 98 countries in the WFP feed (config-driven, same pipeline)
- [ ] Seasonal baselines once WFP coverage density allows; harvest-cycle forecasting (ML)
- [ ] Digital Public Goods (DPG) submission

## Development

```bash
pip install -e ".[dev]"
ruff check .          # lint
pytest -q             # 28 tests: cleaning rules, warehouse, API, analytics
```

CI runs lint + tests on Python 3.12/3.13/3.14. Pull requests welcome — pick an issue or open one describing the problem first.

---

Built by [Alfred Shingai](https://github.com/alfredshingai) with AI pair-programming (ZCode). Not affiliated with WFP or HDX.
