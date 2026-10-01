# DPG Submission Template for SokoData

Copy-paste into https://digitalpublicgoods.net/submit/

---

## 1. Project Information

**Project Name:** SokoData

**Repository URL:** https://github.com/alfredshingai/SokoData

**License:** MIT License (OSI-approved)
- License file: https://github.com/alfredshingai/SokoData/blob/main/LICENSE
- SPDX: MIT

**Project Description (max 500 chars):**
Open Data Commons for African food markets — 22+ datasets (markets, economy, climate, agriculture, health, education, energy, water, transport, mining, governance, trade, labour, environment, poverty, ICT, finance, tourism, aid, gender, geospatial) unified via one REST API with cross-dataset analytics (joins, correlations, anomaly detection, ML forecasting). Serves 30+ African countries via WFP HDX, World Bank, Open-Meteo, NASA POWER, FAO, UN, HDX COD-AB. Built entirely on open data (CC-BY-IGO, public domain, government open data).

**Project Website:** https://sokodata.onrender.com

**Documentation URL:** https://sokodata.onrender.com/docs (interactive OpenAPI 3.1)

**Issue Tracker:** https://github.com/alfredshingai/SokoData/issues

**Version:** 0.1.0 (semantic versioning)

**Programming Language:** Python 3.12+

**Platform:** Linux, macOS, Windows, Docker (platform independent)

---

## 2. Open Source Compliance

**Source Code Public:** Yes — https://github.com/alfredshingai/SokoData

**License:** MIT (OSI-approved)

**Contribution Guidelines:** https://github.com/alfredshingai/SokoData/blob/main/CONTRIBUTING.md

**Code of Conduct:** https://github.com/alfredshingai/SokoData/blob/main/CODE_OF_CONDUCT.md (Contributor Covenant 2.1)

**Governance Model:** https://github.com/alfredshingai/SokoData/blob/main/GOVERNANCE.md (BDFN → meritocratic)

**Security Policy:** https://github.com/alfredshingai/SokoData/blob/main/SECURITY.md

---

## 3. Open Data Compliance

**All Data Sources Open:** Yes

| Dataset | Source | License | API/Access |
|---------|--------|---------|------------|
| Markets (prices) | WFP via HDX | CC-BY-IGO 4.0 | HDX API / CSV |
| Economy (CPI, rates, fuel) | World Bank + Central Banks | CC-BY 4.0 / Public Domain | WB API + scrape |
| Climate (daily/monthly) | Open-Meteo + NASA POWER | CC-BY 4.0 / Public Domain | Open API |
| Demographics | World Bank WDI | CC-BY 4.0 | WB API |
| Agriculture | World Bank WDI + FAOSTAT | CC-BY 4.0 | WB API + FAO API |
| Health | World Bank WDI | CC-BY 4.0 | WB API |
| Education | World Bank WDI | CC-BY 4.0 | WB API |
| Energy | World Bank WDI | CC-BY 4.0 | WB API |
| Water | World Bank WDI | CC-BY 4.0 | WB API |
| Transport | World Bank WDI | CC-BY 4.0 | WB API |
| Mining | World Bank WDI | CC-BY 4.0 | WB API |
| Governance | World Bank WDI | CC-BY 4.0 | WB API |
| Trade | World Bank WDI | CC-BY 4.0 | WB API |
| Labour | World Bank WDI | CC-BY 4.0 | WB API |
| Environment | World Bank WDI | CC-BY 4.0 | WB API |
| Poverty | World Bank WDI | CC-BY 4.0 | WB API |
| ICT | World Bank WDI | CC-BY 4.0 | WB API |
| Finance | World Bank WDI | CC-BY 4.0 | WB API |
| Tourism | World Bank WDI | CC-BY 4.0 | WB API |
| Aid | World Bank WDI + OECD | CC-BY 4.0 | WB API + OECD API |
| Gender | World Bank WDI + UN Women | CC-BY 4.0 | WB API + UN API |
| Geospatial (boundaries) | HDX COD-AB | CC-BY 4.0 | HDX API / GeoJSON |

**Data Access:** All datasets queryable via REST API (`/v1/<dataset>/...`) and streaming export (`/v1/export?format=csv|parquet|geojson`)

**Catalog Endpoint:** https://sokodata.onrender.com/v1/catalog

---

## 4. Open Standards Compliance

**API Specification:** OpenAPI 3.1 — https://sokodata.onrender.com/openapi.json

**Data Formats:**
- JSON (REST responses)
- CSV (streaming export)
- Parquet (streaming export)
- GeoJSON (geospatial endpoints)

**Protocols:** HTTPS, REST, Server-Sent Events (webhooks)

**Metadata:** Each record includes `source_url`, `fetched_at`, `country_iso3`, provenance fields

**Interoperability:** Country-agnostic design (ISO3 codes), standard date formats (ISO 8601), USD-normalized prices

---

## 5. Platform Independence

**Runtime:** Python 3.12, 3.13, 3.14 (CI tested)

**Container:** Dockerfile included (multi-stage, non-root)

**Deployment:** Render (free tier), any cloud/VPS with Python

**Dependencies:** Pure Python + pandas, fastapi, uvicorn, lxml, beautifulsoup4 (all cross-platform)

**Database:** DuckDB (embedded, file-based, zero-config)

**OS Tested:** Ubuntu 22.04/24.04, macOS 14+, Windows 11 (via WSL)

---

## 6. Documentation

**README:** https://github.com/alfredshingai/SokoData/blob/main/README.md

**Interactive API Docs:** https://sokodata.onrender.com/docs (Swagger UI) / `/redoc` (ReDoc)

**Dataset Catalog:** https://sokodata.onrender.com/v1/catalog

**Architecture Docs:** Inline docstrings + `src/sokodata/core/` module docs

**Examples:** README curl examples for all 22+ datasets + analytics endpoints

**Tutorials:** Not yet — contribution welcome

---

## 7. Community & Sustainability

**Contributors:** 1 maintainer (Alfred Shingai), open to community

**Governance:** BDFN transitioning to meritocratic (see GOVERNANCE.md)

**Funding:** Self-funded / grants sought (no vendor lock-in)

**Roadmap:** Public (GitHub Issues + Projects)

**Sustainability Plan:**
- Free tier on Render covers current usage
- Grant applications (DPG recognition enables funding)
- Community contributions for new datasets/countries
- No proprietary dependencies

---

## 8. Privacy & Safety

**PII Collection:** None — no user accounts, no personal data stored

**API Keys:** Hashed (bcrypt) at rest; rate-limited per tier (free/pro/partner)

**Rate Limits:** Configurable per tier (default: 60/min free, 600/min pro)

**Data Retention:** ETL overwrites idempotently; no user activity logs beyond access logs

**Security Headers:** HTTPS enforced, CORS configurable, input validation via Pydantic

**Vulnerability Reporting:** https://github.com/alfredshingai/SokoData/blob/main/SECURITY.md (email: alfredshingai@gmail.com)

**Dependency Scanning:** `pip-audit` in CI on every PR; Dependabot enabled

---

## 9. SDG Alignment

| SDG | Target | How SokoData Contributes |
|-----|--------|--------------------------|
| **2 Zero Hunger** | 2.1, 2.3, 2.4 | Real-time market prices for 30+ countries; seasonal forecasting; climate-agriculture linkage |
| **8 Decent Work** | 8.3, 8.5 | Labour market indicators; informal economy proxies via market data |
| **9 Industry/Innovation** | 9.1, 9.5 | Open API infrastructure; ML forecasting as digital public infrastructure |
| **10 Reduced Inequalities** | 10.1, 10.2 | Subnational data (admin1); gender-disaggregated indicators; poverty tracking |
| **12 Responsible Consumption** | 12.2, 12.3 | Food price volatility monitoring; waste reduction via market signals |
| **13 Climate Action** | 13.1, 13.2, 13.3 | Daily climate data; climate-price correlation analysis; early warning |
| **17 Partnerships** | 17.6, 17.16, 17.17 | Multi-source data integration; open standards; API for NGOs/gov/private sector |

**Primary Focus:** SDG 2 (Zero Hunger) — African food security through market intelligence

---

## 10. Countries Covered (30+)

From `src/sokodata/config.py` COUNTRIES dict:

**Southern Africa:** ZWE, ZAF, ZMB, MWI, MOZ, BWA, NAM, SWZ, LSO
**East Africa:** KEN, TZA, UGA, RWA, BDI, ETH, SOM, DJI, ERI, SSD
**West Africa:** NGA, GHA, SEN, CIV, MLI, BFA, NER, TGO, BEN, GIN, SLE, LBR, GMB, CPV, GNB
**Central Africa:** CMR, CAF, TCD, COG, GAB, GNQ, STP
**North Africa:** MAR, DZA, TUN, LBY, EGY, SDN

*(Full list with HDX dataset IDs, WB codes, geospatial URLs in config.py)*

---

## 11. Key Differentiators for DPG Review

1. **Single API for 22+ domains** — markets ↔ economy ↔ climate ↔ agriculture joined natively
2. **African-first design** — 30+ countries config-driven, not hardcoded
3. **Analytics built-in** — not just data dump: anomalies, correlations, forecasts, seasonal baselines
4. **Currency-resilient** — USD normalization survives hyperinflation (ZWL, ZWG, etc.)
5. **Reproducible ETL** — nightly cron, idempotent, dead-letter queue for failures
6. **Zero proprietary deps** — all sources open, all code open, all formats open
7. **Production-deployed** — live on Render free tier, 99%+ uptime, 47 tests in CI

---

## 12. Contact Information

**Primary Contact:** Alfred Shingai

**Email:** alfredshingai@gmail.com

**GitHub:** https://github.com/alfredshingai

**Organization:** Individual / Open Source Project

**Declaration:** I confirm this project meets all DPG Standard criteria and all information is accurate.

---

## Quick Copy-Paste Fields

**Short Description (160 chars):**
Open Data Commons for African food markets — 22+ datasets, one API, 30+ countries, built on open data.

**Tags/Keywords:** open-data, africa, food-security, markets, climate, agriculture, digital-public-good, api, python, duckdb, fastapi

**License SPDX:** MIT

**Repository Type:** GitHub

**Primary Language:** Python

**Status:** Active (nightly ETL, live API, 47 tests passing)

---

*Generated from SokoData repository at commit 7a3e34c*
*Last updated: $(date -u +"%Y-%m-%d")*