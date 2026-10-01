# DPG Submission — Right to Redistribute Answer

**Question:** Do you have the right to re-distribute this data, content or code? Provide evidence to demonstrate the right to reproduce and/or distribute all of the content or data sets included in the collection.

---

## Code — YES

**License:** MIT (OSI-approved) — permits unrestricted use, modification, distribution, sublicensing, and commercial use.

**Evidence:**
- License file: https://github.com/alfredshingai/SokoData/blob/main/LICENSE
- SPDX header in all source files
- `pyproject.toml` declares `license = { text = "MIT" }`

**Contributor Rights:** Solo-author project (Alfred Shingai). `CONTRIBUTING.md` states all contributions are under MIT. No CLA required; GitHub Terms of Service + MIT license cover contributions.

---

## Data — YES (All 22+ datasets from openly licensed sources)

### Primary Sources & Licenses

| Dataset Category | Source | License | Redistribution Rights |
|------------------|--------|---------|----------------------|
| **Market Prices** | WFP via HDX | CC-BY-IGO 4.0 | ✅ Explicitly permits reproduction, distribution, adaptation, commercial use with attribution |
| **Economy (CPI, rates, fuel)** | World Bank WDI | CC-BY 4.0 | ✅ Permits sharing, adaptation, commercial use with attribution |
| **Climate (daily/monthly)** | Open-Meteo | CC-BY 4.0 | ✅ Free for any use including commercial with attribution |
| **Climate (NASA POWER)** | NASA | Public Domain (US Gov) | ✅ No copyright, unrestricted use |
| **Demographics** | World Bank WDI | CC-BY 4.0 | ✅ |
| **Agriculture** | World Bank WDI + FAOSTAT | CC-BY 4.0 | ✅ |
| **Health** | World Bank WDI | CC-BY 4.0 | ✅ |
| **Education** | World Bank WDI | CC-BY 4.0 | ✅ |
| **Energy** | World Bank WDI | CC-BY 4.0 | ✅ |
| **Water** | World Bank WDI | CC-BY 4.0 | ✅ |
| **Transport** | World Bank WDI | CC-BY 4.0 | ✅ |
| **Mining** | World Bank WDI | CC-BY 4.0 | ✅ |
| **Governance** | World Bank WDI | CC-BY 4.0 | ✅ |
| **Trade** | World Bank WDI | CC-BY 4.0 | ✅ |
| **Labour** | World Bank WDI | CC-BY 4.0 | ✅ |
| **Environment** | World Bank WDI | CC-BY 4.0 | ✅ |
| **Poverty** | World Bank WDI | CC-BY 4.0 | ✅ |
| **ICT** | World Bank WDI | CC-BY 4.0 | ✅ |
| **Finance** | World Bank WDI | CC-BY 4.0 | ✅ |
| **Tourism** | World Bank WDI | CC-BY 4.0 | ✅ |
| **Aid** | World Bank WDI + OECD | CC-BY 4.0 | ✅ |
| **Gender** | World Bank WDI + UN Women | CC-BY 4.0 | ✅ |
| **Geospatial (boundaries)** | HDX COD-AB | CC-BY 4.0 | ✅ |

### License Evidence URLs

- **CC-BY-IGO 4.0 (WFP/HDX):** https://creativecommons.org/licenses/by-igo/4.0/
- **CC-BY 4.0 (World Bank):** https://datacatalog.worldbank.org/public-licenses#cc-by
- **CC-BY 4.0 (Open-Meteo):** https://open-meteo.com/en/docs#license
- **Public Domain (NASA):** https://www.nasa.gov/nasa-brand-center/using-nasa-brand-center/nasa-multimedia-guidelines/
- **HDX COD-AB:** https://data.humdata.org/dataset/cod-ab (license noted per dataset)

---

## How SokoData Complies

1. **No proprietary sources** — every dataset fetched from openly licensed APIs or public domain
2. **Attribution preserved** — every stored record includes `source_url`, `fetched_at`, `country_iso3`; API responses include source metadata
3. **Transformative use** — ETL cleans, normalizes (USD), joins across sources; creates new analytical value (anomalies, forecasts, correlations)
4. **No redistribution of raw dumps** — API serves queried, processed data; export endpoints stream transformed data with provenance
5. **Source licenses compatible** — all CC-BY/CC-BY-IGO/Public Domain are mutually compatible and compatible with MIT code license

---

## Evidence Package for Reviewers

| Artifact | Location |
|----------|----------|
| MIT License (code) | `LICENSE` |
| Dataset source + license in each fetcher | `src/sokodata/datasets/*/fetch.py` |
| Provenance fields in every record | `source_url`, `fetched_at` columns |
| API catalog with source metadata | `GET /v1/catalog` |
| CONTRIBUTING.md (data source policy) | `CONTRIBUTING.md` |
| README data source table | `README.md` lines 21-97 |

---

## Declaration

I confirm that:
- All code is licensed MIT (OSI-approved)
- All data sources are openly licensed (CC-BY-IGO 4.0, CC-BY 4.0, Public Domain)
- No dataset uses restrictive, paywalled, or non-redistributable sources
- Attribution is preserved throughout the pipeline
- The combined work is distributable under MIT + CC-BY-IGO 4.0

---

*Copy-paste the above into the DPG submission form.*