/* SokoData dashboard — vanilla JS, no build step.
 * Talks to the public SokoData API (see /docs on the deployment). */
"use strict";

const API_BASE = location.hostname.endsWith("github.io")
  ? "https://sokodata.onrender.com"
  : "http://127.0.0.1:8000";

const COLD_START_MS = 20000; // show the wake-up note after this long
const CHART_WINDOW_DAYS = 730;

const el = (id) => document.getElementById(id);
let chart = null;

/* ---------- helpers ---------- */

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

function showError() {
  el("error-box").hidden = false;
}

function hideError() {
  el("error-box").hidden = true;
}

/* ---------- tabs ---------- */

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

/* ---------- overview ---------- */

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
    const [health, movers, anomalies] = await Promise.all([
      fetchJSON("/health"),
      fetchJSON("/v1/insights/movers?window_days=90&limit=6"),
      fetchJSON("/v1/insights/anomalies?limit=5"),
    ]);
    renderStats(health.coverage);
    el("movers-list").innerHTML = movers.length
      ? movers.map(moverItem).join("")
      : '<li class="muted">No significant movements in this window.</li>';
    el("anomalies-list").innerHTML = anomalies.length
      ? anomalies.map(anomalyItem).join("")
      : '<li class="muted">Nothing unusual right now.</li>';
    hideError();
  } catch (err) {
    console.error(err);
    showError();
  }
}

/* ---------- explorer ---------- */

async function populateSelectors() {
  const [commodities, markets] = await Promise.all([
    fetchJSON("/v1/commodities?limit=500"),
    fetchJSON("/v1/markets?limit=500"),
  ]);

  const cSel = el("commodity-select");
  cSel.innerHTML = commodities
    .map((c) => `<option value="${c.commodity_id}">${c.commodity} (${c.unit})</option>`)
    .join("");
  const mSel = el("market-select");
  mSel.innerHTML = markets
    .map((m) => `<option value="${m.market_id}">${m.market} — ${m.admin1 || ""}</option>`)
    .join("");

  // sensible defaults: most-covered commodity, a well-known market
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
    const series = await fetchJSON(
      `/v1/prices?market_id=${marketId}&commodity_id=${commodityId}&start=${cutoff}&limit=5000`
    );
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
  el("chart-caption").textContent = points.length
    ? `USD price of ${commodityLabel} at ${marketLabel}, last ${CHART_WINDOW_DAYS / 365} years (${points.length} observations).`
    : "No USD-normalized observations for this market/commodity in the window.";

  if (chart) chart.destroy();
  chart = new Chart(el("price-chart"), {
    type: "line",
    data: {
      labels: points.map((p) => p.date),
      datasets: [{
        label: "USD price",
        data: points.map((p) => p.usdprice),
        borderColor: "#1c7c43",
        backgroundColor: "rgba(28,124,67,0.12)",
        pointRadius: 2,
        tension: 0.15,
        fill: true,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: { ticks: { maxTicksLimit: 8 }, title: { display: false } },
        y: { title: { display: true, text: "USD" } },
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            title: (items) => (items[0] && items[0].label) || "",
            label: (item) => `${money(item.parsed.y)}`,
          },
        },
      },
    },
  });
}

async function renderLatestTable(commodityId) {
  const rows = await fetchJSON(`/v1/prices/latest?commodity_id=${commodityId}&limit=2000`);
  const priced = rows
    .filter((r) => r.usdprice !== null)
    .sort((a, b) => a.usdprice - b.usdprice);

  if (!priced.length) {
    el("latest-table").querySelector("tbody").innerHTML =
      '<tr><td colspan="6" class="muted">No USD-normalized prices available.</td></tr>';
    return;
  }
  const cheapest = priced[0];
  const priciest = priced[priced.length - 1];
  el("latest-table").querySelector("tbody").innerHTML = priced
    .map((r, i) => {
      const cls = r.market_id === cheapest.market_id ? ' class="cheapest"'
        : r.market_id === priciest.market_id ? ' class="priciest"' : "";
      return `<tr${cls}>
        <td>${i + 1}</td><td>${r.market}</td><td>${r.admin1 || "—"}</td>
        <td>${money(r.usdprice)}</td>
        <td>${Number(r.price).toLocaleString("en-US")} ${r.currency}</td>
        <td>${r.date}</td></tr>`;
    })
    .join("");
}

/* ---------- boot ---------- */

async function boot() {
  await loadOverview(); // overview loads even if explorer fails later
  try {
    await populateSelectors();
  } catch (err) {
    console.error(err);
  }
}

el("retry-btn").addEventListener("click", boot);
boot();
