/* SokoData dashboard — vanilla JS, no build step.
 * Commons: talks to the 22-dataset SokoData API (see /docs). */
"use strict";

const API_BASE = location.hostname.endsWith("github.io")
  ? "https://sokodata.onrender.com"
  : "http://127.0.0.1:8000";

const COLD_START_MS = 20000;
const CHART_WINDOW_DAYS = 730;

const el = (id) => document.getElementById(id);
let chart = null;
let genericChart = null;
let catalogCache = null;

async function fetchJSON(path) {
  const timer = setTimeout(() => el("coldstart-note").hidden = false, COLD_START_MS);
  try {
    const resp = await fetch(`${API_BASE}${path}`);
    if (!resp.ok) throw new Error(`${resp.status} ${resp.statusText}`);
    return await resp.json();
  } finally {
    clearTimeout(timer);
    el("coldstart-note").hidden = true;
  }
}

const money = (v) => "$" + Number(v).toLocaleString("en-US", { maximumFractionDigits: 2 });

function badge(pct) {
  const cls = pct >= 0 ? "up" : "down";
  return `<span class="badge ${cls}">${pct >= 0 ? "▲" : "▼"} ${Math.abs(pct).toFixed(0)}%</span>`;
}

function showError() { el("error-box").hidden = false; }
function hideError() { el("error-box").hidden = true; }

// tabs
document.querySelectorAll(".tab").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((b) => {
      b.classList.toggle("is-active", b === btn);
      b.setAttribute("aria-selected", b === btn);
    });
    document.querySelectorAll(".panel").forEach((p) => {
      const active = p.id === `tab-${btn.dataset.tab}`;
      p.hidden = !active;
      p.classList.toggle("is-active", active);
    });
    hideError();
  });
});

document.addEventListener("click", (e) => {
  const go = e.target.closest("[data-go]");
  if (go) {
    e.preventDefault();
    document.querySelector(`.tab[data-tab="${go.dataset.go}"]`)?.click();
  }
});

// overview
function renderStats(coverage) {
  el("stat-markets").textContent = coverage.markets.toLocaleString("en-US");
  el("stat-commodities").textContent = coverage.commodities.toLocaleString("en-US");
  el("stat-observations").textContent = coverage.observations.toLocaleString("en-US");
  el("stat-lastdate").textContent = coverage.last_date || "—";
}

function moverItem(m) {
  return `<li>${badge(m.pct_change)} <strong>${m.commodity}</strong> at ${m.market} — ${money(m.prev_usd)} → ${money(m.last_usd)}/${m.unit}</li>`;
}

function anomalyItem(a) {
  const dir = a.z > 0 ? "above" : "below";
  return `<li>🚨 <strong>${a.commodity}</strong> at ${a.market} — ${money(a.usdprice)}/${a.unit}, ${dir} the ${money(a.recent_median_usd)} norm</li>`;
}

async function loadOverview() {
  try {
    const [health, movers, anomalies, catalog] = await Promise.all([
      fetchJSON("/health"),
      fetchJSON("/v1/insights/movers?window_days=90&limit=6"),
      fetchJSON("/v1/insights/anomalies?limit=5"),
      fetchJSON("/v1/catalog"),
    ]);
    renderStats(health.coverage);
    el("movers-list").innerHTML = movers.length ? movers.map(moverItem).join("") : '<li class="muted">No significant movements in this window.</li>';
    el("anomalies-list").innerHTML = anomalies.length ? anomalies.map(anomalyItem).join("") : '<li class="muted">Nothing unusual right now.</li>';
    catalogCache = catalog;
    el("catalog-count").textContent = catalog.length;
    renderCatalogMini(catalog.slice(0, 6));
    hideError();
  } catch (err) {
    console.error(err);
    showError();
  }
}

function catalogCard(d) {
  const src = d.sources.map(s => `${s.name} (${s.license})`).join(" · ");
  const pills = `<span class="pill">${d.fetch_strategy}</span><span class="pill">${d.update_frequency}</span>`;
  return `<div class="catalog-card"><h3>${d.label}</h3><p class="muted">${d.description}</p><div>${pills}</div><div class="meta"><strong>Coverage:</strong> ${d.coverage}<br><strong>Tables:</strong> ${d.tables.join(", ")}<br><strong>Sources:</strong> ${src}</div></div>`;
}

function renderCatalogMini(list) {
  el("catalog-mini").innerHTML = list.map(catalogCard).join("");
}

async function loadCatalog() {
  try {
    const catalog = catalogCache || await fetchJSON("/v1/catalog");
    catalogCache = catalog;
    el("catalog-grid").innerHTML = catalog.map(catalogCard).join("");
    hideError();
  } catch (err) {
    console.error(err);
    el("catalog-grid").innerHTML = '<p class="muted">Could not load catalog. Try retry.</p>';
    showError();
  }
}

// explorer — dataset selector
const DATASET_ENDPOINTS = {
  economy: [{ label: "Rates (ZiG/USD)", path: "/v1/economy/rates?limit=200" }, { label: "CPI (inflation)", path: "/v1/economy/cpi?limit=500" }, { label: "Fuel", path: "/v1/economy/fuel?limit=200" }],
  climate: [{ label: "Daily (by admin1)", path: "/v1/climate/daily?limit=200" }, { label: "Monthly", path: "/v1/climate/monthly?limit=100" }],
  demographics: [{ label: "Annual population", path: "/v1/demographics/annual?limit=500" }, { label: "2022 Census", path: "/v1/demographics/census" }],
  agriculture: [{ label: "Annual", path: "/v1/agriculture/annual?limit=200" }, { label: "FAO Maize", path: "/v1/agriculture/fao/maize?limit=200" }],
  health: [{ label: "Annual", path: "/v1/health-stats/annual?limit=500" }],
  education: [{ label: "Annual", path: "/v1/education/annual?limit=500" }],
  energy: [{ label: "Annual", path: "/v1/energy/annual?limit=500" }],
  water: [{ label: "Annual", path: "/v1/water/annual?limit=500" }],
  transport: [{ label: "Annual", path: "/v1/transport/annual?limit=500" }],
  mining: [{ label: "Annual", path: "/v1/mining/annual?limit=500" }],
  governance: [{ label: "Annual", path: "/v1/governance/annual?limit=500" }],
  trade: [{ label: "Annual", path: "/v1/trade/annual?limit=500" }],
  labour: [{ label: "Annual", path: "/v1/labour/annual?limit=500" }],
  environment: [{ label: "Annual", path: "/v1/environment/annual?limit=500" }],
  poverty: [{ label: "Annual", path: "/v1/poverty/annual?limit=500" }],
  ict: [{ label: "Annual", path: "/v1/ict/annual?limit=500" }],
  finance: [{ label: "Annual", path: "/v1/finance/annual?limit=500" }],
  tourism: [{ label: "Annual", path: "/v1/tourism/annual?limit=500" }],
  aid: [{ label: "Annual", path: "/v1/aid/annual?limit=500" }],
  gender: [{ label: "Annual", path: "/v1/gender/annual?limit=500" }],
  geospatial: [{ label: "Boundaries metadata", path: "/v1/geospatial/boundaries" }, { label: "Markets GeoJSON", path: "/v1/geospatial/markets/geojson" }],
};

async function initExplorer() {
  const catalog = catalogCache || await fetchJSON("/v1/catalog");
  catalogCache = catalog;
  const dsSel = el("dataset-select");
  const genericDatasets = catalog.filter(d => d.id !== "markets");
  dsSel.innerHTML = '<option value="markets">markets — Food Market Prices</option>' + genericDatasets.map(d => `<option value="${d.id}">${d.id} — ${d.label}</option>`).join("");
  dsSel.addEventListener("change", onDatasetChange);
  el("explore-endpoint").addEventListener("change", loadGeneric);
  await onDatasetChange();
  await populateSelectors(); // markets explorer
}

async function onDatasetChange() {
  const ds = el("dataset-select").value;
  const marketsUI = el("explore-markets-ui");
  const genericUI = el("explore-generic");
  if (ds === "markets") {
    marketsUI.hidden = false;
    genericUI.hidden = true;
    el("explore-subcontrol").hidden = true;
    await loadExplorer();
    return;
  }
  marketsUI.hidden = true;
  genericUI.hidden = false;
  const eps = DATASET_ENDPOINTS[ds] || [{ label: "Annual", path: `/v1/${ds}/annual?limit=500` }];
  const epSel = el("explore-endpoint");
  epSel.innerHTML = eps.map(e => `<option value="${e.path}">${e.label}</option>`).join("");
  el("explore-subcontrol").hidden = false;
  // simple param for climate admin1
  const params = el("explore-params");
  params.innerHTML = "";
  if (ds === "climate" && eps[0].path.includes("daily")) {
    params.innerHTML = `<div class="control"><label for="param-admin1">admin1 (optional)</label><select id="param-admin1"><option value="">All</option><option>Harare</option><option>Bulawayo</option><option>Manicaland</option><option>Masvingo</option><option>Midlands</option></select></div>`;
    el("param-admin1")?.addEventListener("change", loadGeneric);
  }
  await loadGeneric();
}

async function loadGeneric() {
  const path = el("explore-endpoint").value;
  if (!path) return;
  let url = path;
  const admin1 = el("param-admin1")?.value;
  if (admin1) {
    url += (url.includes("?") ? "&" : "?") + `admin1=${encodeURIComponent(admin1)}`;
  }
  el("generic-title").textContent = url;
  el("generic-caption").textContent = "Loading…";
  try {
    const data = await fetchJSON(url);
    const rows = Array.isArray(data) ? data : (data.features ? data.features : []);
    renderGenericTable(rows);
    renderGenericChart(rows);
    el("generic-caption").textContent = Array.isArray(rows) ? `${rows.length} rows from ${url}` : `${url}`;
    hideError();
  } catch (err) {
    console.error(err);
    el("generic-caption").textContent = "Failed to load.";
    showError();
  }
}

function renderGenericTable(rows) {
  const table = el("generic-table");
  const thead = table.querySelector("thead");
  const tbody = table.querySelector("tbody");
  if (!Array.isArray(rows) || rows.length === 0) {
    thead.innerHTML = "";
    tbody.innerHTML = '<tr><td class="muted">No data.</td></tr>';
    return;
  }
  // if GeoJSON features
  const flat = rows[0].type === "Feature" ? rows.map(f => ({ ...f.properties, longitude: f.geometry.coordinates[0], latitude: f.geometry.coordinates[1] })) : rows;
  const cols = Object.keys(flat[0]).slice(0, 8);
  thead.innerHTML = `<tr>${cols.map(c => `<th>${c}</th>`).join("")}</tr>`;
  tbody.innerHTML = flat.slice(0, 200).map(r => `<tr>${cols.map(c => `<td>${r[c] ?? "—"}</td>`).join("")}</tr>`).join("");
}

function renderGenericChart(rows) {
  const box = el("generic-chart-box");
  if (!Array.isArray(rows) || rows.length === 0 || rows[0].type === "Feature") {
    box.hidden = true;
    if (genericChart) { genericChart.destroy(); genericChart = null; }
    return;
  }
  // find first numeric + date col
  const cols = Object.keys(rows[0]);
  const dateCol = cols.find(c => c === "date") || null;
  if (!dateCol) { box.hidden = true; return; }
  const numericCols = cols.filter(c => typeof rows[0][c] === "number" || !isNaN(parseFloat(rows[0][c])));
  const yCol = numericCols.find(c => c !== "date" && c !== "source") || numericCols[0];
  if (!yCol) { box.hidden = true; return; }
  const pts = rows.filter(r => r[dateCol] && r[yCol] !== null && r[yCol] !== undefined).slice().reverse().slice(0, 300);
  if (pts.length < 2) { box.hidden = true; return; }
  box.hidden = false;
  if (genericChart) genericChart.destroy();
  genericChart = new Chart(el("generic-chart"), {
    type: "line",
    data: {
      labels: pts.map(p => p[dateCol]),
      datasets: [{ label: yCol, data: pts.map(p => Number(p[yCol])), borderColor: "#1c7c43", backgroundColor: "rgba(28,124,67,0.12)", pointRadius: 1, tension: 0.15, fill: true }],
    },
    options: { responsive: true, maintainAspectRatio: false, scales: { x: { ticks: { maxTicksLimit: 8 } }, y: { title: { display: true, text: yCol } } }, plugins: { legend: { display: false } } },
  });
}

// explorer — markets (unchanged but now nested)
async function populateSelectors() {
  const [commodities, markets] = await Promise.all([
    fetchJSON("/v1/commodities?limit=500"),
    fetchJSON("/v1/markets?limit=500"),
  ]);
  const cSel = el("commodity-select");
  cSel.innerHTML = commodities.map((c) => `<option value="${c.commodity_id}">${c.commodity} (${c.unit})</option>`).join("");
  const mSel = el("market-select");
  mSel.innerHTML = markets.map((m) => `<option value="${m.market_id}">${m.market} — ${m.admin1 || ""}</option>`).join("");
  const byCoverage = [...commodities].sort((a, b) => b.observations - a.observations);
  if (byCoverage[0]) cSel.value = byCoverage[0].commodity_id;
  const mbare = markets.find((m) => m.market === "Mbare") || markets[0];
  if (mbare) mSel.value = mbare.market_id;
  cSel.addEventListener("change", loadExplorer);
  mSel.addEventListener("change", loadExplorer);
  await loadExplorer();
}

async function loadExplorer() {
  const commodityId = el("commodity-select").value;
  const marketId = el("market-select").value;
  const commodity = (el("commodity-select").selectedOptions[0] || {}).textContent || "";
  const market = (el("market-select").selectedOptions[0] || {}).textContent || "";
  if (!commodityId || !marketId) return;
  el("chart-title").textContent = `Price history — ${commodity}`;
  el("chart-caption").textContent = "Loading…";
  el("table-title").textContent = `Latest prices across markets — ${commodity}`;
  try {
    const cutoff = new Date(Date.now() - CHART_WINDOW_DAYS * 864e5).toISOString().slice(0, 10);
    const series = await fetchJSON(`/v1/prices?market_id=${marketId}&commodity_id=${commodityId}&start=${cutoff}&limit=5000`);
    drawChart(series, market, commodity);
    await renderLatestTable(commodityId);
    hideError();
  } catch (err) {
    console.error(err);
    showError();
  }
}

function drawChart(series, marketLabel, commodityLabel) {
  const points = series.filter((p) => p.usdprice !== null);
  el("chart-caption").textContent = points.length ? `USD price of ${commodityLabel} at ${marketLabel}, last ${CHART_WINDOW_DAYS / 365} years (${points.length} observations).` : "No USD-normalized observations for this market/commodity in the window.";
  if (chart) chart.destroy();
  chart = new Chart(el("price-chart"), {
    type: "line",
    data: {
      labels: points.map((p) => p.date),
      datasets: [{ label: "USD price", data: points.map((p) => p.usdprice), borderColor: "#1c7c43", backgroundColor: "rgba(28,124,67,0.12)", pointRadius: 2, tension: 0.15, fill: true }],
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      scales: { x: { ticks: { maxTicksLimit: 8 } }, y: { title: { display: true, text: "USD" } } },
      plugins: { legend: { display: false }, tooltip: { callbacks: { title: (items) => (items[0] && items[0].label) || "", label: (item) => `${money(item.parsed.y)}` } } },
    },
  });
}

async function renderLatestTable(commodityId) {
  const rows = await fetchJSON(`/v1/prices/latest?commodity_id=${commodityId}&limit=2000`);
  const priced = rows.filter((r) => r.usdprice !== null).sort((a, b) => a.usdprice - b.usdprice);
  if (!priced.length) {
    el("latest-table").querySelector("tbody").innerHTML = '<tr><td colspan="6" class="muted">No USD-normalized prices available.</td></tr>';
    return;
  }
  const cheapest = priced[0];
  const priciest = priced[priced.length - 1];
  el("latest-table").querySelector("tbody").innerHTML = priced.map((r, i) => {
    const cls = r.market_id === cheapest.market_id ? ' class="cheapest"' : r.market_id === priciest.market_id ? ' class="priciest"' : "";
    return `<tr${cls}><td>${i + 1}</td><td>${r.market}</td><td>${r.admin1 || "—"}</td><td>${money(r.usdprice)}</td><td>${Number(r.price).toLocaleString("en-US")} ${r.currency}</td><td>${r.date}</td></tr>`;
  }).join("");
}

// boot
async function boot() {
  await loadOverview();
  // load catalog in bg
  loadCatalog();
  try { await initExplorer(); } catch (err) { console.error(err); }
}

el("retry-btn").addEventListener("click", boot);
boot();
