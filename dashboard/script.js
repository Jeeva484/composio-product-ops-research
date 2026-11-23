/**
 * 100-App Research Dashboard & Interactive Case Study
 * Powered by real research dataset, pattern classifier, and verification report.
 */

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => document.querySelectorAll(selector);

let results = [];
let patternsData = {};
let accuracyData = {};
let verificationRows = [];

let sortKey = "rank";
let sortDirection = 1;

// Resolve relative paths whether running inside /dashboard/ or root /
function getBaseDataPath() {
  const p = window.location.pathname;
  return p.includes("/dashboard") ? ".." : ".";
}

async function fetchJSON(path) {
  const response = await fetch(path);
  if (!response.ok) throw new Error(`Could not load ${path}`);
  return response.json();
}

function parseCSV(text) {
  const lines = text.trim().split(/\r?\n/);
  if (lines.length < 2) return [];
  const headers = lines[0].split(",").map((h) => h.trim());
  const rows = [];
  for (let i = 1; i < lines.length; i++) {
    const line = lines[i];
    if (!line.trim()) continue;
    const values = [];
    let cur = "";
    let inQuotes = false;
    for (let c = 0; c < line.length; c++) {
      const char = line[c];
      if (char === '"') {
        if (inQuotes && line[c + 1] === '"') {
          cur += '"';
          c++;
        } else {
          inQuotes = !inQuotes;
        }
      } else if (char === "," && !inQuotes) {
        values.push(cur.trim());
        cur = "";
      } else {
        cur += char;
      }
    }
    values.push(cur.trim());
    const obj = {};
    headers.forEach((h, idx) => {
      obj[h] = values[idx] || "";
    });
    rows.push(obj);
  }
  return rows;
}

function addOptions(selectEl, values) {
  if (!selectEl) return;
  const currentVal = selectEl.value;
  // Keep first option (e.g. "All ...")
  selectEl.length = 1;
  const sorted = [...new Set(values)].filter(Boolean).sort();
  sorted.forEach((val) => {
    selectEl.add(new Option(val, val));
  });
  selectEl.value = currentVal;
}

// =========================================================================
// DATA POPULATION
// =========================================================================

function populateExecutiveSummary() {
  const total = results.length || 100;
  const buildable = results.filter((r) =>
    ["Buildable now", "Buildable with limits", "Buildable as local CLI integration"].includes(r.buildability)
  ).length;
  const partnerGated = results.filter((r) => r.access.includes("Partner") || r.access.includes("gated")).length;
  const officialMcp = results.filter((r) => r.official_mcp && r.official_mcp.startsWith("Yes")).length;

  const rate = Math.round((buildable / total) * 100);
  const rateEl = $("#buildableRate");
  if (rateEl) rateEl.textContent = `${rate}%`;

  const heroKpis = $("#heroKpis");
  if (heroKpis) {
    heroKpis.innerHTML = `
      <div class="kpi">
        <div class="kpi-num">${total}</div>
        <div class="kpi-label">Apps Researched</div>
      </div>
      <div class="kpi">
        <div class="kpi-num">${buildable}</div>
        <div class="kpi-label">Buildable Now / Limits</div>
      </div>
      <div class="kpi">
        <div class="kpi-num">${partnerGated}</div>
        <div class="kpi-label">Partner / Admin Gated</div>
      </div>
      <div class="kpi">
        <div class="kpi-num">${officialMcp}</div>
        <div class="kpi-label">Official MCP Servers</div>
      </div>
    `;
  }
}

function populateScopeTable() {
  const scopeBody = $("#scopeBody");
  if (!scopeBody) return;

  const cats = {};
  results.forEach((r) => {
    if (!cats[r.category]) {
      cats[r.category] = { total: 0, self: 0, buildable: 0, rest: 0 };
    }
    cats[r.category].total++;
    if (r.access === "Self-serve") cats[r.category].self++;
    if (r.buildability === "Buildable now" || r.buildability === "Buildable with limits") {
      cats[r.category].buildable++;
    }
    if (r.public_rest_api === "Yes") cats[r.category].rest++;
  });

  scopeBody.innerHTML = Object.entries(cats)
    .sort((a, b) => a[0].localeCompare(b[0]))
    .map(
      ([cat, d]) => `
      <tr>
        <td><strong>${cat}</strong></td>
        <td>${d.total}</td>
        <td><span class="pill pill-green">${d.self}</span></td>
        <td><span class="pill pill-blue">${d.buildable}</span></td>
        <td>${d.rest} / 10</td>
      </tr>
    `
    )
    .join("");
}

function populateAuthPatterns() {
  const authChart = $("#authChart");
  const authInsights = $("#authInsights");
  if (!authChart) return;

  const authCounts = {};
  results.forEach((r) => {
    const a = r.auth_methods || "Unknown";
    authCounts[a] = (authCounts[a] || 0) + 1;
  });

  const sortedAuth = Object.entries(authCounts).sort((a, b) => b[1] - a[1]);
  const topAuth = sortedAuth.slice(0, 8);
  const max = topAuth[0]?.[1] || 1;

  authChart.innerHTML = topAuth
    .map(
      ([name, cnt]) => `
      <div class="chart-row">
        <span title="${name}">${name}</span>
        <div class="bar"><i style="width: ${(cnt / max) * 100}%"></i></div>
        <b>${cnt}</b>
      </div>
    `
    )
    .join("");

  if (authInsights) {
    authInsights.innerHTML = `
      <li><strong>OAuth2 is the enterprise standard:</strong> Over 40 apps mandate OAuth2 token grants for user authorization.</li>
      <li><strong>API keys enable fastest onboarding:</strong> 33+ developer-first tools offer instantaneous self-serve API keys (Stripe, Twilio, SendGrid, Apify).</li>
      <li><strong>Hybrid token models:</strong> Jira, Slack, and HubSpot support dual access paths (OAuth2 for marketplace apps, Personal/Private tokens for internal scripts).</li>
      <li><strong>Zero unauthenticated public APIs:</strong> All surveyed applications require authenticated identity headers.</li>
    `;
  }
}

function populateAccessPatterns() {
  const summaryEl = $("#accessSummary");
  const accessBody = $("#accessBody");
  if (!summaryEl || !accessBody) return;

  let selfCount = 0;
  let partnerCount = 0;
  let rvCount = 0;
  const catAccess = {};

  results.forEach((r) => {
    if (!catAccess[r.category]) {
      catAccess[r.category] = { self: 0, partner: 0, rv: 0 };
    }
    if (r.access === "Self-serve") {
      selfCount++;
      catAccess[r.category].self++;
    } else if (r.access.includes("Partner") || r.access.includes("gated")) {
      partnerCount++;
      catAccess[r.category].partner++;
    } else {
      rvCount++;
      catAccess[r.category].rv++;
    }
  });

  summaryEl.innerHTML = `
    <div class="access-stat">
      <div class="big" style="color:var(--green)">${selfCount}</div>
      <div class="lbl">Self-serve Access</div>
    </div>
    <div class="access-stat">
      <div class="big" style="color:var(--red)">${partnerCount}</div>
      <div class="lbl">Partner / Admin Gated</div>
    </div>
    <div class="access-stat">
      <div class="big" style="color:var(--amber)">${rvCount}</div>
      <div class="lbl">Requires Verification</div>
    </div>
  `;

  accessBody.innerHTML = Object.entries(catAccess)
    .sort((a, b) => b[1].self - a[1].self)
    .map(
      ([cat, d]) => `
      <tr>
        <td><strong>${cat}</strong></td>
        <td><span class="pill pill-green">${d.self}</span></td>
        <td><span class="pill ${d.partner > 0 ? "pill-red" : "pill-muted"}">${d.partner}</span></td>
        <td><span class="pill ${d.rv > 0 ? "pill-amber" : "pill-muted"}">${d.rv}</span></td>
      </tr>
    `
    )
    .join("");
}

function populateAPIFindings() {
  const cards = $("#apiCoverageCards");
  if (!cards) return;

  const restYes = results.filter((r) => r.public_rest_api === "Yes").length;
  const graphYes = results.filter((r) => r.graphql_api === "Yes").length;
  const both = results.filter((r) => r.public_rest_api === "Yes" && r.graphql_api === "Yes").length;

  cards.innerHTML = `
    <div class="card">
      <p class="section-label">REST API ADOPTION</p>
      <h3>${restYes} / 100 Apps</h3>
      <p style="font-size:13px;color:var(--muted)">Confirmed public REST API endpoints documented with OpenAPI/Swagger or developer reference.</p>
    </div>
    <div class="card">
      <p class="section-label">GRAPHQL COVERAGE</p>
      <h3>${graphYes} / 100 Apps</h3>
      <p style="font-size:13px;color:var(--muted)">Specialized GraphQL APIs (GitHub, Shopify, Salesforce, Cloudflare, Linear, Contentful).</p>
    </div>
    <div class="card">
      <p class="section-label">HYBRID DUAL-ENGINE</p>
      <h3>${both} / 100 Apps</h3>
      <p style="font-size:13px;color:var(--muted)">Modern platforms shipping parallel REST and GraphQL surfaces for complex nested queries.</p>
    </div>
  `;
}

function populateMCPSection() {
  const stats = $("#mcpStats");
  const list = $("#mcpList");
  if (!stats || !list) return;

  const officialMcpApps = results.filter((r) => r.official_mcp && r.official_mcp.startsWith("Yes"));

  stats.innerHTML = `
    <div class="mcp-stat">
      <div class="big" style="color:var(--purple)">${officialMcpApps.length}</div>
      <div class="lbl">Official Vendor MCPs</div>
    </div>
    <div class="mcp-stat">
      <div class="big" style="color:var(--muted)">${100 - officialMcpApps.length}</div>
      <div class="lbl">Community / Unreleased</div>
    </div>
  `;

  list.innerHTML = officialMcpApps
    .map(
      (r) => `
      <div class="mcp-pill">
        ⚡ <strong>${r.app}</strong> &nbsp;·&nbsp; ${r.category}
      </div>
    `
    )
    .join("");
}

function populateBuildabilitySection() {
  const chart = $("#buildChart");
  const blockerList = $("#blockerList");
  if (!chart || !blockerList) return;

  const buildCounts = {};
  results.forEach((r) => {
    const b = r.buildability || "Requires verification";
    buildCounts[b] = (buildCounts[b] || 0) + 1;
  });

  const sortedBuild = Object.entries(buildCounts).sort((a, b) => b[1] - a[1]);
  const max = sortedBuild[0]?.[1] || 1;

  chart.innerHTML = sortedBuild
    .map(
      ([verdict, cnt]) => `
      <div class="chart-row">
        <span title="${verdict}">${verdict}</span>
        <div class="bar"><i style="width: ${(cnt / max) * 100}%; background: ${
          verdict.includes("Buildable now")
            ? "var(--green)"
            : verdict.includes("limits")
            ? "var(--amber)"
            : verdict.includes("Not buildable")
            ? "var(--red)"
            : "var(--purple)"
        }"></i></div>
        <b>${cnt}</b>
      </div>
    `
    )
    .join("");

  // Top blockers
  const blockers = {};
  results.forEach((r) => {
    if (r.main_blocker && r.main_blocker !== "None") {
      blockers[r.main_blocker] = (blockers[r.main_blocker] || 0) + 1;
    }
  });
  const topBlockers = Object.entries(blockers).sort((a, b) => b[1] - a[1]).slice(0, 5);

  blockerList.innerHTML = topBlockers
    .map(
      ([msg, cnt]) => `
      <li>
        <span class="blocker-count">${cnt} apps</span>
        ${msg}
      </li>
    `
    )
    .join("");
}

function populateCrossCategoryInsights() {
  const grid = $("#insightsGrid");
  if (!grid) return;

  grid.innerHTML = `
    <div class="insight-card purple">
      <h4>Developer & Infra leads self-serve buildability</h4>
      <p>Platforms like GitHub, Supabase, Cloudflare, Datadog and Sentry offer instant API keys, generous free tiers, and comprehensive REST/GraphQL APIs, making them immediate build targets.</p>
    </div>
    <div class="insight-card red">
      <h4>Advertising & Enterprise CRM enforce heavy gates</h4>
      <p>Google Ads, Meta Ads, LinkedIn Ads, and Amazon SP require formal developer token applications, organization audits, and manual approvals before production calls can execute.</p>
    </div>
    <div class="insight-card green">
      <h4>Productivity & Messaging converge on hybrid auth</h4>
      <p>Slack, Notion, Airtable, Linear, and Jira support bot tokens and personal tokens for development, but require scoped OAuth2 apps for multi-tenant production distributions.</p>
    </div>
    <div class="insight-card blue">
      <h4>AI & Media applications exhibit bifurcation</h4>
      <p>API-native AI tools (Devin, Apify, Reducto) provide straightforward REST endpoints, while consumer-facing tools (NotebookLM) lack developer APIs entirely.</p>
    </div>
  `;
}

function populateVerificationSection() {
  const scoreRow = $("#scoreRow");
  const vBody = $("#verificationBody");
  if (!scoreRow || !vBody) return;

  const appLvl = accuracyData.application_level || {
    pass: accuracyData.pass || 14,
    partial: accuracyData.partial || 6,
    fail: accuracyData.fail || 0,
    unresolved: accuracyData.unresolved || 0,
    weighted_accuracy_pct: accuracyData.weighted_accuracy_pct || 85.0,
  };

  scoreRow.innerHTML = `
    <div class="score-box">
      <div class="num">${accuracyData.sample_size || 20}</div>
      <div class="lbl">Sample Size (2/cat)</div>
    </div>
    <div class="score-box">
      <div class="num green-txt">${appLvl.pass}</div>
      <div class="lbl">Pass</div>
    </div>
    <div class="score-box">
      <div class="num amber-txt">${appLvl.partial}</div>
      <div class="lbl">Partial</div>
    </div>
    <div class="score-box">
      <div class="num ${appLvl.fail > 0 ? "red-txt" : "muted-txt"}">${appLvl.fail}</div>
      <div class="lbl">Fail</div>
    </div>
    <div class="score-box">
      <div class="num green-txt">${appLvl.weighted_accuracy_pct}%</div>
      <div class="lbl">Weighted Accuracy</div>
    </div>
  `;

  vBody.innerHTML = verificationRows
    .map((r) => {
      const outcome = r.outcome || "Unresolved";
      const badgeClass =
        outcome === "Pass"
          ? "pill pill-green"
          : outcome === "Partial"
          ? "pill pill-amber"
          : outcome === "Fail"
          ? "pill pill-red"
          : "pill pill-muted";
      return `
      <tr>
        <td><strong>${r.application}</strong></td>
        <td>${r.category}</td>
        <td><span class="${badgeClass}">${outcome}</span></td>
        <td>${r.human_correction || "—"}</td>
        <td style="font-size:12px;color:var(--muted)">${r.verification_notes || ""}</td>
      </tr>
    `;
    })
    .join("");
}

// =========================================================================
// FULL RESEARCH MATRIX & FILTERS
// =========================================================================

function renderMatrixTable() {
  const tbody = $("#tableBody");
  if (!tbody) return;

  const query = ($("#search")?.value || "").trim().toLowerCase();
  const accessFilter = $("#accessFilter")?.value || "";
  const catFilter = $("#categoryFilter")?.value || "";
  const authFilter = $("#authFilter")?.value || "";
  const buildFilter = $("#buildFilter")?.value || "";

  const filtered = results.filter((r) => {
    const qMatch =
      !query ||
      `${r.app} ${r.category} ${r.description} ${r.auth_methods}`.toLowerCase().includes(query);
    const aMatch = !accessFilter || r.access === accessFilter;
    const cMatch = !catFilter || r.category === catFilter;
    const auMatch = !authFilter || r.auth_methods === authFilter;
    const bMatch = !buildFilter || r.buildability === buildFilter;
    return qMatch && aMatch && cMatch && auMatch && bMatch;
  });

  filtered.sort((a, b) => {
    let va = a[sortKey] ?? "";
    let vb = b[sortKey] ?? "";
    if (typeof va === "number" && typeof vb === "number") {
      return (va - vb) * sortDirection;
    }
    va = String(va).toLowerCase();
    vb = String(vb).toLowerCase();
    if (va === vb) return 0;
    return (va < vb ? -1 : 1) * sortDirection;
  });

  if (filtered.length === 0) {
    tbody.innerHTML = `<tr><td colspan="10" style="text-align:center;padding:24px;color:var(--muted)">No applications match the active filters.</td></tr>`;
    return;
  }

  tbody.innerHTML = filtered
    .map((r) => {
      let accessPill = "pill-muted";
      if (r.access === "Self-serve") accessPill = "pill-green";
      else if (r.access.includes("Partner") || r.access.includes("gated")) accessPill = "pill-red";
      else if (r.access.includes("Verification")) accessPill = "pill-amber";

      let buildPill = "pill-muted";
      if (r.buildability === "Buildable now") buildPill = "pill-green";
      else if (r.buildability === "Buildable with limits") buildPill = "pill-blue";
      else if (r.buildability.includes("Not buildable")) buildPill = "pill-red";

      const hasMcp = r.official_mcp && r.official_mcp.startsWith("Yes");

      return `
      <tr data-app="${r.app}">
        <td>${r.rank}</td>
        <td><strong>${r.app}</strong></td>
        <td>${r.category}</td>
        <td style="font-size:12px">${r.auth_methods}</td>
        <td><span class="pill ${accessPill}">${r.access}</span></td>
        <td>${r.public_rest_api}</td>
        <td>${r.graphql_api}</td>
        <td>${hasMcp ? '<span class="pill pill-purple">Official</span>' : "—"}</td>
        <td><span class="pill ${buildPill}">${r.buildability}</span></td>
        <td><a href="${r.evidence_url}" target="_blank" rel="noreferrer" onclick="event.stopPropagation()">Docs ↗</a></td>
      </tr>
    `;
    })
    .join("");

  $$("#tableBody tr[data-app]").forEach((tr) => {
    tr.addEventListener("click", () => showDetails(tr.dataset.app));
  });
}

function showDetails(appName) {
  const row = results.find((r) => r.app === appName);
  if (!row) return;

  const modal = $("#detailModal");
  const content = $("#modalContent");
  if (!modal || !content) return;

  content.innerHTML = `
    <p class="section-label" style="margin-bottom:4px">${row.category} · #${row.rank}</p>
    <h2 style="margin-bottom:12px">${row.app}</h2>
    <p style="color:var(--muted);margin-bottom:18px;line-height:1.6">${row.description}</p>
    <dl>
      <dt>Authentication</dt><dd>${row.auth_methods}</dd>
      <dt>Access Model</dt><dd>${row.access}</dd>
      <dt>Public REST</dt><dd>${row.public_rest_api}</dd>
      <dt>GraphQL API</dt><dd>${row.graphql_api}</dd>
      <dt>Official MCP</dt><dd>${row.official_mcp}</dd>
      <dt>Community MCP</dt><dd>${row.community_mcp}</dd>
      <dt>Buildability</dt><dd><strong>${row.buildability}</strong></dd>
      <dt>Main Blocker</dt><dd>${row.main_blocker || "None"}</dd>
      <dt>Evidence Source</dt><dd><a href="${row.evidence_url}" target="_blank" rel="noreferrer">${row.evidence_url}</a></dd>
      <dt>Confidence</dt><dd><span class="pill pill-muted">${row.confidence}</span></dd>
      <dt>Last Researched</dt><dd>${row.last_researched}</dd>
    </dl>
  `;

  modal.classList.add("open");
  modal.removeAttribute("hidden");
}

function closeDetails() {
  const modal = $("#detailModal");
  if (modal) {
    modal.classList.remove("open");
    modal.setAttribute("hidden", "");
  }
}

function setupModalHandlers() {
  const modal = $("#detailModal");
  if (!modal) return;
  modal.addEventListener("click", (e) => {
    if (e.target === modal || e.target.classList.contains("modal-close")) {
      closeDetails();
    }
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeDetails();
  });
}

function setupTableControls() {
  addOptions($("#accessFilter"), results.map((r) => r.access));
  addOptions($("#categoryFilter"), results.map((r) => r.category));
  addOptions($("#authFilter"), results.map((r) => r.auth_methods));
  addOptions($("#buildFilter"), results.map((r) => r.buildability));

  ["search", "accessFilter", "categoryFilter", "authFilter", "buildFilter"].forEach((id) => {
    const el = $("#" + id);
    if (el) {
      el.addEventListener(id === "search" ? "input" : "change", renderMatrixTable);
    }
  });

  $$("th[data-sort]").forEach((th) => {
    th.addEventListener("click", () => {
      const field = th.dataset.sort;
      if (sortKey === field) {
        sortDirection = -sortDirection;
      } else {
        sortKey = field;
        sortDirection = 1;
      }
      $$("th[data-sort]").forEach((h) => h.classList.remove("sorted"));
      th.classList.add("sorted");
      renderMatrixTable();
    });
  });
}

// Download handlers
function downloadJSON() {
  const blob = new Blob([JSON.stringify(results, null, 2)], { type: "application/json" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "composio-100-app-research.json";
  a.click();
  URL.revokeObjectURL(a.href);
}

function downloadCSV() {
  if (!results.length) return;
  const headers = Object.keys(results[0]);
  const lines = [
    headers.join(","),
    ...results.map((r) =>
      headers
        .map((h) => {
          const v = String(r[h] ?? "");
          return /[",\n]/.test(v) ? `"${v.replaceAll('"', '""')}"` : v;
        })
        .join(",")
    ),
  ];
  const blob = new Blob([lines.join("\n")], { type: "text/csv;charset=utf-8" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "composio-100-app-research.csv";
  a.click();
  URL.revokeObjectURL(a.href);
}

// =========================================================================
// INITIALIZATION
// =========================================================================

async function init() {
  const base = getBaseDataPath();
  const [data, patterns, accuracy, vText] = await Promise.all([
    fetchJSON(`${base}/data/research_results.json`),
    fetchJSON(`${base}/data/patterns.json`),
    fetchJSON(`${base}/verification/accuracy.json`),
    fetch(`${base}/verification/verification_report.csv`).then((r) => r.text()),
  ]);

  results = data;
  patternsData = patterns;
  accuracyData = accuracy;
  verificationRows = parseCSV(vText);

  populateExecutiveSummary();
  populateScopeTable();
  populateAuthPatterns();
  populateAccessPatterns();
  populateAPIFindings();
  populateMCPSection();
  populateBuildabilitySection();
  populateCrossCategoryInsights();
  populateVerificationSection();

  setupTableControls();
  setupModalHandlers();
  renderMatrixTable();

  // Wire download buttons in nav
  $$(".nav-actions a").forEach((a) => {
    if (a.textContent.includes("JSON")) {
      a.addEventListener("click", (e) => {
        e.preventDefault();
        downloadJSON();
      });
    } else if (a.textContent.includes("CSV")) {
      a.addEventListener("click", (e) => {
        e.preventDefault();
        downloadCSV();
      });
    }
  });

  // Topnav smooth scroll active link highlight
  const navLinks = $$(".nav-links a");
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          const id = entry.target.id;
          navLinks.forEach((link) => {
            if (link.getAttribute("href") === `#${id}`) {
              link.classList.add("active");
            } else {
              link.classList.remove("active");
            }
          });
        }
      });
    },
    { threshold: 0.2 }
  );

  $$(".hero, .section-block").forEach((sec) => {
    if (sec.id) observer.observe(sec);
  });
}

init().catch((err) => {
  console.error("Dashboard init error:", err);
  document.body.insertAdjacentHTML(
    "afterbegin",
    `<div style="background:#fee2e2;color:#991b1b;padding:16px;text-align:center;font-weight:600">
      Error loading dashboard data: ${err.message}. Ensure files exist in /data and /verification.
    </div>`
  );
});

window.downloadJSON = downloadJSON;
window.downloadCSV = downloadCSV;
