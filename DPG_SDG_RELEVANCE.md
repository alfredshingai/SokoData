# DPG Submission — SDG Relevance Answers

**Selected SDGs:** 3 (Good Health and Well-Being), 12 (Responsible Consumption and Production), 13 (Climate Action)

---

## SDG 3 – Good Health and Well-Being

SokoData provides open health indicators (WDI: immunization, mortality, disease prevalence, health expenditure) for 30+ African countries alongside real-time nutritious food prices. The `/v1/analyze/correlate` endpoint links climate anomalies (e.g., extreme rainfall) to market price spikes and health outcomes, enabling early warning for malnutrition and climate-sensitive disease outbreaks (cholera, malaria).

**Targets addressed:** 3.1 (maternal mortality), 3.2 (child mortality), 3.3 (communicable diseases), 3.8 (universal health coverage), 3.d (early warning/health risks)

---

## SDG 12 – Responsible Consumption and Production

Market price monitoring across 30+ countries detects supply-demand imbalances in real time, reducing post-harvest waste by signaling optimal sale timing. Agricultural datasets (FAO + WDI) track yields, fertilizer intensity, and land use; anomaly detection flags production shocks. Seasonal forecasting with crop calendars helps farmers align planting to market cycles, cutting overproduction and loss.

**Targets addressed:** 12.2 (sustainable resource use), 12.3 (food waste/loss), 12.4 (chemicals/waste), 12.a (developing country capacity)

---

## SDG 13 – Climate Action

Daily/monthly climate data (Open-Meteo, NASA POWER) covers all 30+ countries with temperature, rainfall, humidity, and soil moisture. The `/v1/analyze/forecast` and `/v1/analyze/correlate` endpoints quantify climate–price linkages (e.g., drought → maize price surge). Harmonic regression baselines + ML models embed climate seasonality into food security early warnings, supporting adaptation planning at subnational (admin1) resolution.

**Targets addressed:** 13.1 (resilience/adaptation), 13.2 (policy integration), 13.3 (education/awareness), 13.b (capacity building)

---

## Cross-SDG Synergy

The `/v1/analyze/join` endpoint combines markets + climate + health + agriculture tables on `(country, date, admin1)`, enabling multi-sector analysis that single-sector datasets cannot. Example: drought (SDG 13) → maize price spike (SDG 12) → reduced dietary diversity → child stunting (SDG 3) — all traceable via one API query.

---

*Copy-paste each section into the DPG submission form under "How is your solution relevant to each SDG you've selected above?"*