const $ = (selector) => document.querySelector(selector);

let results = [];
let sortKey = "rank";
let sortDirection = 1;

async function fetchJSON(path) {
  const response = await fetch(path);
  if (!response.ok) throw new Error(`Could not load ${path}`);
  return response.json();
}

function countWhere(items, key, value) {
  return items.filter((item) => item[key] === value).length;
}

function addOptions(select, values) {
  values.sort().forEach((value) => select.add(new Option(value, value)));
}

function csvEscape(value) {
  const text = String(value ?? "");
  return /[",\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
}

function downloadCSV() {
  const keys = Object.keys(results[0] || {});
  const lines = [
    keys.map(csvEscape).join(","),
    ...results.map((row) => keys.map((key) => csvEscape(row[key])).join(",")),
  ];
  const blob = new Blob([lines.join("\n")], { type: "text/csv;charset=utf-8" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = "composio-research-results.csv";
  link.click();
  URL.revokeObjectURL(link.href);
}

function renderTable() {
  const query = $("#search").value.trim().toLowerCase();
  const access = $("#accessFilter").value;
  const category = $("#categoryFilter").value;
  const auth = $("#authFilter").value;
  const build = $("#buildFilter").value;

  const filtered = results.filter((row) =>
    (!query || `${row.app} ${row.category} ${row.description}`.toLowerCase().includes(query)) &&
    (!access || row.access === access) &&
    (!category || row.category === category) &&
    (!auth || row.auth_methods === auth) &&
    (!build || row.buildability === build)
  );

  filtered.sort((a, b) => {
    const left = String(a[sortKey] ?? "").toLowerCase();
    const right = String(b[sortKey] ?? "").toLowerCase();
    if (left === right) return 0;
    return left < right ? -sortDirection : sortDirection;
  });

  $("#tableBody").innerHTML = filtered.map((row) => {
    let accessClass = "gated";
    if (row.access === "Self-serve") accessClass = "self";
    if (row.access === "Partner / admin-gated") accessClass = "partner";
    return `<tr data-app="${row.app}">
      <td>${row.rank}</td>
      <td><strong>${row.app}</strong></td>
      <td>${row.category}</td>
      <td>${row.auth_methods}</td>
      <td><span class="pill ${accessClass}">${row.access}</span></td>
      <td>${row.public_rest_api}<br><small>${row.graphql_api}</small></td>
      <td><span class="pill verdict">${row.buildability}</span></td>
      <td><a href="${row.evidence_url}" target="_blank" rel="noreferrer">Evidence ↗</a></td>
    </tr>`;
  }).join("") || `<tr><td colspan="8">No applications match the selected filters.</td></tr>`;

  document.querySelectorAll("#tableBody tr[data-app]").forEach((tr) => {
    tr.addEventListener("click", () => showDetails(tr.dataset.app));
  });
}

function showDetails(appName) {
  const row = results.find((item) => item.app === appName);
  if (!row) return;
  const existing = $("#detailModal");
  if (existing) existing.remove();
  const modal = document.createElement("div");
  modal.id = "detailModal";
  modal.className = "modal";
  modal.innerHTML = `<div class="modal-panel">
    <button class="modal-close" aria-label="Close">×</button>
    <p class="eyebrow">${row.category}</p>
    <h2>${row.app}</h2>
    <p>${row.description}</p>
    <dl>
      <dt>Authentication</dt><dd>${row.auth_methods}</dd>
      <dt>Access</dt><dd>${row.access}</dd>
      <dt>REST</dt><dd>${row.public_rest_api}</dd>
      <dt>GraphQL</dt><dd>${row.graphql_api}</dd>
      <dt>API breadth</dt><dd>${row.api_breadth}</dd>
      <dt>Official MCP</dt><dd>${row.official_mcp}</dd>
      <dt>Community MCP</dt><dd>${row.community_mcp}</dd>
      <dt>Buildability</dt><dd>${row.buildability}</dd>
      <dt>Main blocker</dt><dd>${row.main_blocker}</dd>
      <dt>Evidence</dt><dd><a href="${row.evidence_url}" target="_blank" rel="noreferrer">${row.evidence_url}</a></dd>
      <dt>Confidence</dt><dd>${row.confidence}</dd>
      <dt>Last researched</dt><dd>${row.last_researched}</dd>
    </dl>
  </div>`;
  document.body.append(modal);
  $(".modal-close").addEventListener("click", () => modal.remove());
  modal.addEventListener("click", (event) => {
    if (event.target === modal) modal.remove();
  });
}

function parseCSV(text) {
  const lines = text.trim().split(/\r?\n/);
  const headers = lines.shift().split(",");
  return lines.map((line) => {
    const values = [];
    let value = "";
    let quoted = false;
    for (let i = 0; i < line.length; i++) {
      if (line[i] === '"') quoted = !quoted;
      else if (line[i] === "," && !quoted) { values.push(value); value = ""; }
      else value += line[i];
    }
    values.push(value);
    return Object.fromEntries(headers.map((header, index) => [header, values[index] ?? ""]));
  });
}

async function load() {
  const [data, patterns, accuracy, verificationText] = await Promise.all([
    fetchJSON("../data/research_results.json"),
    fetchJSON("../data/patterns.json"),
    fetchJSON("../verification/accuracy.json"),
    fetch("../verification/verification_report.csv").then((response) => response.text()),
  ]);
  results = data;

  const buildable = results.filter((row) =>
    row.buildability === "Buildable now" ||
    row.buildability === "Buildable with limits" ||
    row.buildability === "Buildable as local CLI integration"
  ).length;
  const partnerGated = countWhere(results, "access", "Partner / admin-gated");
  const officialMCP = results.filter((row) => !/Unknown|No known/.test(row.official_mcp)).length;

  $("#buildableRate").textContent = `${Math.round(buildable / results.length * 100)}%`;
  $("#kpis").innerHTML = [
    [results.length, "apps researched"],
    [buildable, "buildable now or with limits"],
    [partnerGated, "partner / admin gates"],
    [officialMCP, "official MCP evidence found"],
  ].map(([number, label]) => `<div class="kpi"><strong>${number}</strong><span>${label}</span></div>`).join("");

  const restYes = results.filter((row) => row.public_rest_api === "Yes").length;
  const restKnown = results.filter((row) => !["Unknown"].includes(row.public_rest_api)).length;
  $("#restCoverage").textContent = `${restKnown}/${results.length}`;
  $("#restNote").textContent = `${restYes} positively classified; rest remains unknown or unavailable.`;
  const graphYes = results.filter((row) => row.graphql_api === "Yes").length;
  $("#graphqlCoverage").textContent = `${results.filter((row) => row.graphql_api !== "Unknown").length}/${results.length}`;
  $("#graphqlNote").textContent = `${graphYes} positively classified; absence or presence is otherwise unverified.`;
  $("#mcpCoverage").textContent = `${officialMCP}/${results.length}`;
  $("#mcpNote").textContent = "Official MCP support only where a positive claim was evidenced.";

  const authEntries = Object.entries(patterns.auth).sort((a, b) => b[1] - a[1]).slice(0, 8);
  const max = authEntries[0]?.[1] || 1;
  $("#authChart").innerHTML = authEntries.map(([name, count]) =>
    `<div class="chart-row"><span>${name}</span><div class="bar"><i style="width:${count / max * 100}%"></i></div><b>${count}</b></div>`
  ).join("");

  const categoryRows = Object.entries(patterns.categories).sort((a, b) =>
    (b[1].self_serve / b[1].total) - (a[1].self_serve / a[1].total)
  );
  $("#headlines").innerHTML = `
    <li><strong>${categoryRows[0][0]}</strong> currently has the highest measured self-serve share in this dataset.</li>
    <li><strong>Unknown evidence</strong> is the dominant finding; it is safer than an unsupported classification.</li>
    <li><strong>Partnership and plan terms</strong> require independent account-level verification.</li>
    <li><strong>Mermaid CLI</strong> is the explicit CLI case with no hosted REST API.</li>`;

  addOptions($("#accessFilter"), [...new Set(results.map((row) => row.access))]);
  addOptions($("#categoryFilter"), [...new Set(results.map((row) => row.category))]);
  addOptions($("#authFilter"), [...new Set(results.map((row) => row.auth_methods))]);
  addOptions($("#buildFilter"), [...new Set(results.map((row) => row.buildability))]);

  ["search", "accessFilter", "categoryFilter", "authFilter", "buildFilter"].forEach((id) => {
    $("#" + id).addEventListener(id === "search" ? "input" : "change", renderTable);
  });

  document.querySelectorAll("th[data-sort]").forEach((th) => {
    th.addEventListener("click", () => {
      if (sortKey === th.dataset.sort) sortDirection *= -1;
      else { sortKey = th.dataset.sort; sortDirection = 1; }
      renderTable();
    });
  });
  renderTable();

  const verification = parseCSV(verificationText);
  $("#verificationBody").innerHTML = verification.map((row) =>
    `<tr><td><strong>${row.application}</strong></td><td><a href="${row.evidence_url}" target="_blank">Official evidence ↗</a></td><td class="miss">${row.outcome}</td><td>${row.verification_notes}</td></tr>`
  ).join("");
  $("#firstPass").textContent = accuracy.first_pass_accuracy ?? "Unmeasured";
  $("#finalPass").textContent = accuracy.final_accuracy ?? "Unmeasured";
  $("#sampleSize").textContent = accuracy.sample_size;
}

load().catch((error) => {
  console.error(error);
  document.body.insertAdjacentHTML("afterbegin", `<div class="error-banner">Dashboard data could not be loaded: ${error.message}</div>`);
});

window.downloadResearchCSV = downloadCSV;
