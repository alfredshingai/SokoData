# Contributing to SokoData

Thank you for your interest in contributing to SokoData — the Open Data Commons for African food markets.

## Ways to Contribute

### 1. Add a New Dataset
Each dataset lives under `src/sokodata/datasets/<name>/` with four files:
- `fetch.py` — source retrieval (open API, HTML scrape, PDF extract)
- `clean.py` — normalization, currency conversion, schema validation
- `store.py` — DuckDB persistence with idempotent upserts
- `etl.py` — orchestration: `fetch -> clean -> store`

Register it in `src/sokodata/core/registry.py`.

### 2. Extend Country Coverage
Add entries to `COUNTRIES` in `src/sokodata/config.py`:
- ISO3 code
- HDX dataset ID (for WFP markets)
- World Bank country code
- Geospatial boundary URL (HDX COD-AB)

### 3. Improve Analytics
Cross-dataset analysis lives in `src/sokodata/api/routers/analyze.py`:
- Join endpoints
- Correlation
- Anomaly detection (MAD-based)
- Forecasting (harmonic regression + ML)

### 4. Fix Bugs / Improve Tests
Tests in `tests/` — run with `pytest -q`. Lint with `ruff check`.

## Pull Request Process
1. Fork the repo, create a branch: `git checkout -b feat/your-change`
2. Make changes, add tests if applicable
3. Run `ruff check` and `pytest -q` locally
4. Open PR with clear description of what and why
5. CI must pass (GitHub Actions: lint, typecheck, tests on 3.12/3.13/3.14)

## Code Style
- Ruff for linting (`ruff check`, `ruff format`)
- Type hints where practical
- No comments unless explaining *why* (not *what*)
- Follow existing patterns in `src/sokodata/datasets/markets/`

## Data Sources
All sources must be **open** (CC-BY, CC-BY-IGO, public domain, government open data). No proprietary or paywalled sources.

## Questions?
Open an issue or start a discussion on GitHub.