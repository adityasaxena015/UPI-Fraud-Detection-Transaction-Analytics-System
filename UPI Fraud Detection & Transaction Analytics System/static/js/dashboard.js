/**
 * UPI Fraud Detection & Anomaly Sentinel — Dashboard JavaScript
 * Handles REST API integrations, dynamic charts, real-time simulation,
 * alert triage, and transaction forensics.
 */

// Global State
let trendChart = null;
let riskDonut = null;
let detectorChart = null;
let categoryChart = null;

let currentTxOffset = 0;
const txLimit = 25;

// Initialize on DOM Ready
document.addEventListener("DOMContentLoaded", () => {
  initClock();
  initNavigation();
  initCharts();
  loadDashboardData();
  setupEventListeners();
  loadModelArchitectureData();
});

// Clock Ticker
function initClock() {
  const clockEl = document.getElementById("live-clock");
  const update = () => {
    const now = new Date();
    if (clockEl) {
      clockEl.textContent = now.toLocaleTimeString("en-IN", { timeZone: "Asia/Kolkata" }) + " IST";
    }
  };
  update();
  setInterval(update, 1000);
}

// Navigation between Sections
function initNavigation() {
  const links = document.querySelectorAll(".sidebar-menu .nav-link");
  links.forEach(link => {
    link.addEventListener("click", (e) => {
      e.preventDefault();
      const targetSection = link.getAttribute("data-section");
      switchSection(targetSection);

      // Active state on link
      links.forEach(l => l.classList.remove("active"));
      link.classList.add("active");
    });
  });

  // Mobile sidebar toggle
  const toggleBtn = document.getElementById("sidebarToggle");
  const sidebar = document.getElementById("sidebar");
  if (toggleBtn && sidebar) {
    toggleBtn.addEventListener("click", () => {
      sidebar.classList.toggle("show");
    });
  }
}

function switchSection(sectionId) {
  document.querySelectorAll(".app-section").forEach(sec => sec.classList.remove("active"));
  const target = document.getElementById(sectionId);
  if (target) {
    target.classList.add("active");
    // Update active nav link
    document.querySelectorAll(".sidebar-menu .nav-link").forEach(l => {
      if (l.getAttribute("data-section") === sectionId) {
        l.classList.add("active");
      } else {
        l.classList.remove("active");
      }
    });

    // Refresh specific section data
    if (sectionId === "alerts-section") loadAlertsTable();
    if (sectionId === "transactions-section") loadTransactionsStream();
    if (sectionId === "overview-section") loadDashboardData();
  }
}

// Event Listeners
function setupEventListeners() {
  // Quick Simulation Header Buttons
  document.getElementById("quick-simulate-btn")?.addEventListener("click", () => {
    switchSection("simulator-section");
    document.getElementById("sim-scenario-select").value = "Normal";
    runSimulation();
  });

  document.getElementById("quick-fraud-btn")?.addEventListener("click", () => {
    switchSection("simulator-section");
    document.getElementById("sim-scenario-select").value = "Multiple Signals";
    runSimulation();
  });

  // Simulator Section Buttons
  document.getElementById("run-simulation-btn")?.addEventListener("click", runSimulation);
  document.getElementById("run-normal-sim-btn")?.addEventListener("click", () => {
    document.getElementById("sim-scenario-select").value = "Normal";
    runSimulation();
  });

  // Alerts Filter & Refresh
  document.getElementById("alert-status-filter")?.addEventListener("change", loadAlertsTable);
  document.getElementById("alert-risk-filter")?.addEventListener("change", loadAlertsTable);
  document.getElementById("refresh-alerts-btn")?.addEventListener("click", loadAlertsTable);

  // Alert Modal Save Status
  document.getElementById("modal-save-status-btn")?.addEventListener("click", saveAlertStatus);

  // Transaction Stream Filters & Pagination
  document.getElementById("apply-tx-filters-btn")?.addEventListener("click", () => {
    currentTxOffset = 0;
    loadTransactionsStream();
  });
  document.getElementById("tx-prev-page-btn")?.addEventListener("click", () => {
    if (currentTxOffset >= txLimit) {
      currentTxOffset -= txLimit;
      loadTransactionsStream();
    }
  });
  document.getElementById("tx-next-page-btn")?.addEventListener("click", () => {
    currentTxOffset += txLimit;
    loadTransactionsStream();
  });

  // Sandbox Form Submit
  document.getElementById("sandbox-form")?.addEventListener("submit", handleSandboxSubmit);
}

// -------------------------------------------------------------
// 1. Dashboard Overview & KPIs
// -------------------------------------------------------------
async function loadDashboardData() {
  try {
    const res = await fetch("/api/stats");
    const data = await res.json();
    if (data.status !== "success") return;

    const kpis = data.kpis;
    document.getElementById("kpi-total-tx").textContent = kpis.total_transactions.toLocaleString();
    document.getElementById("kpi-total-vol").textContent = "₹" + formatIndianCurrency(kpis.total_amount);
    document.getElementById("kpi-suspicious").textContent = kpis.suspicious_transactions.toLocaleString();
    document.getElementById("kpi-fraud-rate").textContent = kpis.fraud_percentage.toFixed(1) + "%";
    document.getElementById("kpi-high-critical").textContent = (kpis.high_risk_transactions + kpis.critical_transactions).toLocaleString();
    document.getElementById("nav-alert-badge").textContent = kpis.active_alerts_count;

    // Risk counts
    document.getElementById("count-low").textContent = data.risk_distribution.Low.toLocaleString();
    document.getElementById("count-med").textContent = data.risk_distribution.Medium.toLocaleString();
    document.getElementById("count-high").textContent = data.risk_distribution.High.toLocaleString();
    document.getElementById("count-crit").textContent = data.risk_distribution.Critical.toLocaleString();

    // Update charts
    updateCharts(data);

    // Load top recent alerts for overview table
    loadQuickAlerts();
  } catch (err) {
    console.error("Failed to load dashboard statistics:", err);
  }
}

function formatIndianCurrency(num) {
  if (num >= 10000000) {
    return (num / 10000000).toFixed(2) + " Cr";
  } else if (num >= 100000) {
    return (num / 100000).toFixed(2) + " Lakh";
  } else {
    return Number(num).toLocaleString("en-IN");
  }
}

// -------------------------------------------------------------
// 2. Charts Initialization & Update
// -------------------------------------------------------------
function initCharts() {
  // Chart.js default styles for dark theme
  Chart.defaults.color = "#94a3b8";
  Chart.defaults.font.family = "'Inter', sans-serif";

  // 1. Volume & Anomaly Trends Chart
  const trendCtx = document.getElementById("trendVolumeChart")?.getContext("2d");
  if (trendCtx) {
    trendChart = new Chart(trendCtx, {
      type: "bar",
      data: {
        labels: [],
        datasets: [
          {
            type: "line",
            label: "Total Transactions",
            data: [],
            borderColor: "#818cf8",
            backgroundColor: "rgba(99, 102, 241, 0.15)",
            borderWidth: 2,
            tension: 0.35,
            fill: true,
            yAxisID: "y"
          },
          {
            type: "bar",
            label: "Flagged Anomalies",
            data: [],
            backgroundColor: "#f87171",
            borderRadius: 4,
            barPercentage: 0.5,
            yAxisID: "y1"
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: "top", labels: { boxWidth: 12, font: { size: 11 } } },
          tooltip: { mode: "index", intersect: false }
        },
        scales: {
          x: { grid: { color: "rgba(255, 255, 255, 0.05)" } },
          y: {
            type: "linear",
            display: true,
            position: "left",
            title: { display: true, text: "Total Tx Count" },
            grid: { color: "rgba(255, 255, 255, 0.05)" }
          },
          y1: {
            type: "linear",
            display: true,
            position: "right",
            title: { display: true, text: "Anomalies" },
            grid: { drawOnChartArea: false }
          }
        }
      }
    });
  }

  // 2. Risk Tiers Donut Chart
  const donutCtx = document.getElementById("riskDonutChart")?.getContext("2d");
  if (donutCtx) {
    riskDonut = new Chart(donutCtx, {
      type: "doughnut",
      data: {
        labels: ["Low Risk", "Medium Risk", "High Risk", "Critical Risk"],
        datasets: [{
          data: [0, 0, 0, 0],
          backgroundColor: ["#10b981", "#06b6d4", "#f59e0b", "#ef4444"],
          borderWidth: 0,
          hoverOffset: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: "70%",
        plugins: {
          legend: { display: false }
        }
      }
    });
  }

  // 3. Detection Methods Bar Chart
  const detectorCtx = document.getElementById("detectorBarChart")?.getContext("2d");
  if (detectorCtx) {
    detectorChart = new Chart(detectorCtx, {
      type: "bar",
      data: {
        labels: ["IQR Only", "IsoForest Only", "TimeSeries Only", "Multi-Detector", "Normal"],
        datasets: [{
          label: "Transactions Flagged",
          data: [0, 0, 0, 0, 0],
          backgroundColor: ["#818cf8", "#38bdf8", "#fbbf24", "#f87171", "#334155"],
          borderRadius: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { display: false } },
          y: { grid: { color: "rgba(255, 255, 255, 0.05)" } }
        }
      }
    });
  }

  // 4. Merchant Category Bar Chart
  const catCtx = document.getElementById("categoryBarChart")?.getContext("2d");
  if (catCtx) {
    categoryChart = new Chart(catCtx, {
      type: "bar",
      data: {
        labels: [],
        datasets: [{
          label: "Fraud Rate (%)",
          data: [],
          backgroundColor: "#f59e0b",
          borderRadius: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        indexAxis: "y",
        plugins: { legend: { display: false } },
        scales: {
          x: {
            title: { display: true, text: "Fraud Rate %" },
            grid: { color: "rgba(255, 255, 255, 0.05)" }
          },
          y: { grid: { display: false } }
        }
      }
    });
  }
}

function updateCharts(data) {
  // Update Trends
  if (trendChart && data.daily_trends) {
    trendChart.data.labels = data.daily_trends.map(d => d.date.slice(5)); // MM-DD
    trendChart.data.datasets[0].data = data.daily_trends.map(d => d.count);
    trendChart.data.datasets[1].data = data.daily_trends.map(d => d.anomalies);
    trendChart.update();
  }

  // Update Donut
  if (riskDonut && data.risk_distribution) {
    riskDonut.data.datasets[0].data = [
      data.risk_distribution.Low,
      data.risk_distribution.Medium,
      data.risk_distribution.High,
      data.risk_distribution.Critical
    ];
    riskDonut.update();
  }

  // Update Detectors Bar
  if (detectorChart && data.detector_distribution) {
    const d = data.detector_distribution;
    detectorChart.data.datasets[0].data = [
      d.IQR_Only,
      d.Isolation_Forest_Only,
      d.Time_Series_Only,
      d.Multiple_Detectors,
      d.No_Anomaly
    ];
    detectorChart.update();
  }

  // Update Categories Bar
  if (categoryChart && data.category_stats) {
    const sorted = [...data.category_stats].sort((a, b) => b.rate - a.rate).slice(0, 6);
    categoryChart.data.labels = sorted.map(c => c.category);
    categoryChart.data.datasets[0].data = sorted.map(c => c.rate);
    categoryChart.update();
  }
}

// -------------------------------------------------------------
// 3. Quick Alerts Table (Overview Section)
// -------------------------------------------------------------
async function loadQuickAlerts() {
  try {
    const res = await fetch("/api/alerts?limit=5&status=New");
    const data = await res.json();
    const tbody = document.getElementById("quick-alerts-tbody");
    if (!tbody) return;

    if (!data.alerts || data.alerts.length === 0) {
      tbody.innerHTML = `<tr><td colspan="9" class="text-center py-4 text-muted-custom">No unreviewed alerts found. All queues clear.</td></tr>`;
      return;
    }

    tbody.innerHTML = data.alerts.map(a => `
      <tr>
        <td class="font-monospace fw-semibold text-white">${a.alert_id}</td>
        <td><a href="#" class="text-accent text-decoration-none font-monospace" onclick="inspectTransaction('${a.transaction_id}'); return false;">${a.transaction_id}</a></td>
        <td><div class="small">${a.sender_id} <i class="bi bi-arrow-right text-muted"></i> ${a.receiver_id}</div></td>
        <td class="fw-semibold text-white font-monospace">₹${Number(a.amount).toLocaleString("en-IN", {minimumFractionDigits: 2})}</td>
        <td><span class="badge ${getScoreBadgeClass(a.risk_score)} font-monospace">${a.risk_score.toFixed(1)}</span></td>
        <td><span class="badge ${getTierBadgeClass(a.risk_level)}">${a.risk_level}</span></td>
        <td><span class="badge bg-dark border border-secondary text-muted-custom small">${a.detection_method}</span></td>
        <td><span class="badge ${getStatusBadgeClass(a.status)}">${a.status}</span></td>
        <td>
          <button class="btn btn-sm btn-outline-warning" onclick="openAlertModal('${a.alert_id}', '${a.status}')">
            Triage
          </button>
        </td>
      </tr>
    `).join("");
  } catch (err) {
    console.error("Error loading quick alerts:", err);
  }
}

// -------------------------------------------------------------
// 4. Real-Time Transaction Simulator
// -------------------------------------------------------------
async function runSimulation() {
  const scenarioSelect = document.getElementById("sim-scenario-select");
  const scenario = scenarioSelect ? scenarioSelect.value : "random";
  const runBtn = document.getElementById("run-simulation-btn");
  const resultBody = document.getElementById("sim-result-body");
  const statusBadge = document.getElementById("sim-status-badge");
  const subtitle = document.getElementById("sim-result-subtitle");

  if (runBtn) {
    runBtn.disabled = true;
    runBtn.innerHTML = `<span class="spinner-border spinner-border-sm me-2" role="status"></span>Analyzing Pipeline...`;
  }
  if (statusBadge) {
    statusBadge.textContent = "INSPECTING...";
    statusBadge.className = "badge bg-warning font-monospace";
  }

  try {
    const res = await fetch("/api/simulate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ scenario: scenario })
    });
    const data = await res.json();

    if (data.status !== "success") {
      showToast("Simulation Failed", data.message || "Unknown error", "danger");
      return;
    }

    const payload = data.transaction_payload;
    const analysis = data.analysis;

    if (statusBadge) {
      statusBadge.textContent = `${analysis.risk_level.toUpperCase()} RISK`;
      statusBadge.className = `badge ${getTierBadgeClass(analysis.risk_level)} font-monospace`;
    }
    if (subtitle) {
      subtitle.textContent = `Processed Transaction ID: ${analysis.transaction_id} (${data.simulated_scenario})`;
    }

    // Render Rich Forensics Panel
    const reasonsHtml = (analysis.reasons || []).map(r => `
      <div class="reason-item">
        <i class="bi bi-shield-exclamation text-warning reason-check"></i>
        <span>${r}</span>
      </div>
    `).join("");

    const tagsHtml = (analysis.factor_tags || []).map(tag => `
      <span class="badge bg-soft-danger text-danger me-1 mb-1 font-monospace"><i class="bi bi-tag-fill me-1"></i>${tag}</span>
    `).join("");

    const feat = analysis.engineered_features || {};

    resultBody.innerHTML = `
      <!-- Prominent Risk Banner if High/Critical -->
      ${(analysis.risk_level === "High" || analysis.risk_level === "Critical") ? `
        <div class="alert bg-soft-danger border border-danger text-white p-3 mb-4 d-flex align-items-center justify-content-between rounded-3">
          <div class="d-flex align-items-center gap-3">
            <i class="bi bi-radioactive fs-2 text-danger"></i>
            <div>
              <h6 class="m-0 fw-bold text-danger">POTENTIAL FRAUD ATTACK DETECTED</h6>
              <div class="small text-muted-custom">Vector: <strong>${data.simulated_scenario}</strong> — Escalated to Fraud Alert Triage</div>
            </div>
          </div>
          <span class="badge bg-danger fs-6 px-3 py-2 font-monospace">SCORE: ${analysis.risk_score.toFixed(1)}/100</span>
        </div>
      ` : `
        <div class="alert bg-soft-success border border-success text-white p-3 mb-4 d-flex align-items-center gap-3 rounded-3">
          <i class="bi bi-shield-check fs-2 text-success"></i>
          <div>
            <h6 class="m-0 fw-bold text-success">TRANSACTION APPROVED (BENIGN)</h6>
            <div class="small text-muted-custom">Behavior matches normal spending profile. No step-up authentication required.</div>
          </div>
        </div>
      `}

      <!-- Score Gauge & Recommendation -->
      <div class="row g-3 mb-4">
        <div class="col-md-5">
          <div class="p-3 rounded-3 bg-dark border border-secondary-subtle">
            <div class="d-flex justify-content-between align-items-baseline mb-2">
              <span class="small text-muted-custom text-uppercase fw-semibold">Fraud Risk Score</span>
              <span class="fs-4 fw-bold ${getScoreTextClass(analysis.risk_score)} font-monospace">${analysis.risk_score.toFixed(1)} <small class="text-muted fs-6">/ 100</small></span>
            </div>
            <div class="risk-meter-container">
              <div class="risk-meter-fill ${getScoreMeterFillClass(analysis.risk_score)}" style="width: ${analysis.risk_score}%"></div>
            </div>
            <div class="d-flex justify-content-between mt-2 small text-muted-custom font-monospace">
              <span>0 (Safe)</span>
              <span>30 (Med)</span>
              <span>60 (High)</span>
              <span>100 (Crit)</span>
            </div>
          </div>
        </div>

        <div class="col-md-7">
          <div class="p-3 rounded-3 bg-dark border border-secondary-subtle h-100">
            <span class="small text-muted-custom text-uppercase fw-semibold d-block mb-1">Operational Recommendation</span>
            <div class="text-white fw-semibold mb-2"><i class="bi bi-shield-shaded text-accent me-1"></i>${analysis.recommendation}</div>
            <div class="d-flex flex-wrap gap-2">
              <span class="badge bg-dark border border-secondary text-muted-custom">Method: ${analysis.detection_method}</span>
              ${analysis.alert_created ? `<span class="badge bg-soft-warning text-warning"><i class="bi bi-bell-fill me-1"></i>Alert: ${analysis.alert_id}</span>` : ''}
            </div>
          </div>
        </div>
      </div>

      <!-- Contributing Reasons Checklist -->
      <div class="mb-4">
        <h6 class="fw-bold text-white mb-2"><i class="bi bi-card-checklist text-info me-2"></i>Explainability Rationale & Factor Breakdown</h6>
        <div class="mb-2">${tagsHtml}</div>
        <div class="reasons-list">${reasonsHtml}</div>
      </div>

      <!-- Behavioral Feature Extraction Grid -->
      <div>
        <h6 class="fw-bold text-white mb-2"><i class="bi bi-cpu-fill text-primary-light me-2"></i>Engineered Behavioral Signals</h6>
        <div class="row g-2 text-center font-monospace small">
          <div class="col-3">
            <div class="p-2 bg-dark rounded border border-secondary-subtle">
              <div class="text-muted-custom" style="font-size: 0.7rem;">TX AMOUNT</div>
              <div class="text-white fw-bold">₹${Number(payload.amount).toLocaleString("en-IN")}</div>
            </div>
          </div>
          <div class="col-3">
            <div class="p-2 bg-dark rounded border border-secondary-subtle">
              <div class="text-muted-custom" style="font-size: 0.7rem;">AMT DEVIATION</div>
              <div class="${feat.amount_deviation > 3.0 ? 'text-danger' : 'text-success'} fw-bold">${feat.amount_deviation || 1.0}x</div>
            </div>
          </div>
          <div class="col-3">
            <div class="p-2 bg-dark rounded border border-secondary-subtle">
              <div class="text-muted-custom" style="font-size: 0.7rem;">BURST 1-HOUR</div>
              <div class="${feat.transactions_last_hour >= 5 ? 'text-danger' : 'text-white'} fw-bold">${feat.transactions_last_hour || 1} tx</div>
            </div>
          </div>
          <div class="col-3">
            <div class="p-2 bg-dark rounded border border-secondary-subtle">
              <div class="text-muted-custom" style="font-size: 0.7rem;">DEVICE / CITY</div>
              <div class="text-white fw-bold">${feat.device_changed ? '⚠️ NEW' : 'SAME'} / ${feat.location_changed ? '⚠️ HOP' : 'SAME'}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Detector Voting Breakdown -->
      <div class="mt-4 pt-3 border-top border-secondary-subtle">
        <h6 class="fw-bold text-white mb-2"><i class="bi bi-diagram-3-fill text-accent me-2"></i>Triple-Engine Anomaly Scores</h6>
        <div class="row g-2 text-center font-monospace small">
          <div class="col-4">
            <div class="p-2 bg-dark rounded border border-secondary-subtle">
              <div class="text-muted-custom" style="font-size: 0.7rem;">IQR STATISTICAL</div>
              <div class="fw-bold ${analysis.iqr_anomaly ? 'text-danger' : 'text-success'}">
                ${analysis.iqr_anomaly ? 'ANOMALY' : 'NORMAL'} (${analysis.detector_scores.iqr.score.toFixed(1)})
              </div>
            </div>
          </div>
          <div class="col-4">
            <div class="p-2 bg-dark rounded border border-secondary-subtle">
              <div class="text-muted-custom" style="font-size: 0.7rem;">ISOLATION FOREST</div>
              <div class="fw-bold ${analysis.isolation_anomaly ? 'text-danger' : 'text-success'}">
                ${analysis.isolation_anomaly ? 'OUTLIER' : 'NORMAL'} (${analysis.detector_scores.isolation_forest.score.toFixed(1)})
              </div>
            </div>
          </div>
          <div class="col-4">
            <div class="p-2 bg-dark rounded border border-secondary-subtle">
              <div class="text-muted-custom" style="font-size: 0.7rem;">TIME SERIES BURST</div>
              <div class="fw-bold ${analysis.time_series_anomaly ? 'text-danger' : 'text-success'}">
                ${analysis.time_series_anomaly ? 'SPIKE' : 'NORMAL'} (${analysis.detector_scores.time_series.score.toFixed(1)})
              </div>
            </div>
          </div>
        </div>
      </div>
    `;

    // Toast Alert
    showToast(
      `${analysis.risk_level} Risk Transaction Ingested`,
      `Tx ID: ${analysis.transaction_id} — Score: ${analysis.risk_score.toFixed(1)} (${analysis.recommendation})`,
      analysis.risk_level === "Critical" || analysis.risk_level === "High" ? "danger" : "info"
    );

    // Refresh KPI counts
    loadDashboardData();

  } catch (err) {
    console.error("Simulation error:", err);
    showToast("Error", "Could not complete simulation.", "danger");
  } finally {
    if (runBtn) {
      runBtn.disabled = false;
      runBtn.innerHTML = `<i class="bi bi-play-circle-fill me-2"></i>Inject & Analyze Transaction`;
    }
  }
}

// -------------------------------------------------------------
// 5. Fraud Alerts Triage Management
// -------------------------------------------------------------
async function loadAlertsTable() {
  const statusFilter = document.getElementById("alert-status-filter")?.value || "";
  const riskFilter = document.getElementById("alert-risk-filter")?.value || "";
  const tbody = document.getElementById("full-alerts-tbody");
  if (!tbody) return;

  tbody.innerHTML = `<tr><td colspan="11" class="text-center py-4 text-muted-custom"><span class="spinner-border spinner-border-sm me-2"></span>Loading alerts triage queue...</td></tr>`;

  try {
    let url = `/api/alerts?limit=50`;
    if (statusFilter) url += `&status=${encodeURIComponent(statusFilter)}`;
    if (riskFilter) url += `&risk_level=${encodeURIComponent(riskFilter)}`;

    const res = await fetch(url);
    const data = await res.json();

    if (!data.alerts || data.alerts.length === 0) {
      tbody.innerHTML = `<tr><td colspan="11" class="text-center py-4 text-muted-custom">No matching fraud alerts found.</td></tr>`;
      return;
    }

    tbody.innerHTML = data.alerts.map(a => {
      const reasonsSample = Array.isArray(a.reasons) ? a.reasons.slice(0, 2).join("; ") : a.reasons;
      return `
        <tr>
          <td class="font-monospace fw-semibold text-white">${a.alert_id}</td>
          <td><a href="#" class="text-accent text-decoration-none font-monospace" onclick="inspectTransaction('${a.transaction_id}'); return false;">${a.transaction_id}</a></td>
          <td><span class="font-monospace text-muted-custom">${a.sender_id}</span></td>
          <td><span class="font-monospace text-muted-custom">${a.receiver_id}</span></td>
          <td class="fw-bold text-white font-monospace">₹${Number(a.amount).toLocaleString("en-IN", {minimumFractionDigits: 2})}</td>
          <td><span class="badge ${getScoreBadgeClass(a.risk_score)} font-monospace">${a.risk_score.toFixed(1)}</span></td>
          <td><span class="badge ${getTierBadgeClass(a.risk_level)}">${a.risk_level}</span></td>
          <td><span class="badge bg-dark border border-secondary text-muted-custom small">${a.detection_method}</span></td>
          <td class="small text-muted-custom text-truncate" style="max-width: 220px;" title="${reasonsSample}">${reasonsSample}</td>
          <td><span class="badge ${getStatusBadgeClass(a.status)}">${a.status}</span></td>
          <td>
            <button class="btn btn-sm btn-outline-primary" onclick="openAlertModal('${a.alert_id}', '${a.status}', '${(a.notes || '').replace(/'/g, "\\'")}')">
              <i class="bi bi-pencil-square me-1"></i>Triage
            </button>
          </td>
        </tr>
      `;
    }).join("");
  } catch (err) {
    console.error("Error loading alerts:", err);
  }
}

function openAlertModal(alertId, currentStatus, currentNotes) {
  document.getElementById("modal-alert-id").value = alertId;
  document.getElementById("modal-display-alert-id").value = alertId;
  document.getElementById("modal-status-select").value = currentStatus || "New";
  document.getElementById("modal-notes").value = currentNotes || "";

  const modal = new bootstrap.Modal(document.getElementById("alertUpdateModal"));
  modal.show();
}

async function saveAlertStatus() {
  const alertId = document.getElementById("modal-alert-id").value;
  const status = document.getElementById("modal-status-select").value;
  const notes = document.getElementById("modal-notes").value;

  try {
    const res = await fetch(`/api/alerts/${alertId}/status`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status, notes })
    });
    const data = await res.json();

    if (data.status === "success") {
      const modalEl = document.getElementById("alertUpdateModal");
      bootstrap.Modal.getInstance(modalEl).hide();
      showToast("Alert Updated", `Alert ${alertId} set to status: ${status}`, "success");
      loadAlertsTable();
      loadQuickAlerts();
    } else {
      showToast("Update Failed", data.message || "Could not update status", "danger");
    }
  } catch (err) {
    console.error("Error updating alert status:", err);
  }
}

// -------------------------------------------------------------
// 6. Transaction Stream & Forensics
// -------------------------------------------------------------
async function loadTransactionsStream() {
  const sender = document.getElementById("tx-search-sender")?.value.trim() || "";
  const category = document.getElementById("tx-category-filter")?.value || "";
  const risk = document.getElementById("tx-risk-filter")?.value || "";
  const tbody = document.getElementById("tx-stream-tbody");
  if (!tbody) return;

  tbody.innerHTML = `<tr><td colspan="13" class="text-center py-4 text-muted-custom"><span class="spinner-border spinner-border-sm me-2"></span>Loading transactions...</td></tr>`;

  try {
    let url = `/api/transactions?limit=${txLimit}&offset=${currentTxOffset}`;
    if (sender) url += `&sender=${encodeURIComponent(sender)}`;
    if (category) url += `&category=${encodeURIComponent(category)}`;
    if (risk) url += `&risk_level=${encodeURIComponent(risk)}`;

    const res = await fetch(url);
    const data = await res.json();

    if (!data.transactions || data.transactions.length === 0) {
      tbody.innerHTML = `<tr><td colspan="13" class="text-center py-4 text-muted-custom">No matching transactions found.</td></tr>`;
      document.getElementById("tx-pagination-info").textContent = "Showing 0 of 0";
      return;
    }

    document.getElementById("tx-pagination-info").textContent =
      `Showing ${currentTxOffset + 1}–${Math.min(currentTxOffset + data.transactions.length, data.total_matching)} of ${data.total_matching.toLocaleString()}`;

    document.getElementById("tx-prev-page-btn").disabled = (currentTxOffset === 0);
    document.getElementById("tx-next-page-btn").disabled = (currentTxOffset + txLimit >= data.total_matching);

    tbody.innerHTML = data.transactions.map(tx => `
      <tr>
        <td class="font-monospace text-white fw-semibold">${tx.transaction_id}</td>
        <td class="small text-muted-custom font-monospace">${(tx.timestamp || '').slice(0, 19).replace('T', ' ')}</td>
        <td class="font-monospace text-muted-custom">${tx.sender_id}</td>
        <td class="font-monospace text-muted-custom">${tx.receiver_id}</td>
        <td class="fw-bold text-white font-monospace">₹${Number(tx.amount).toLocaleString("en-IN", {minimumFractionDigits: 2})}</td>
        <td><span class="badge bg-dark border border-secondary text-muted-custom">${tx.merchant_category}</span></td>
        <td class="small text-muted-custom">${tx.device_type} • ${tx.location}</td>
        <td><span class="badge ${tx.iqr_anomaly ? 'bg-danger' : 'bg-secondary'}">${tx.iqr_anomaly ? 'OUT' : 'OK'}</span></td>
        <td><span class="badge ${tx.isolation_prediction ? 'bg-danger' : 'bg-secondary'}">${tx.isolation_prediction ? 'ANOM' : 'OK'}</span></td>
        <td><span class="badge ${tx.time_series_anomaly ? 'bg-danger' : 'bg-secondary'}">${tx.time_series_anomaly ? 'BURST' : 'OK'}</span></td>
        <td><span class="badge ${getScoreBadgeClass(tx.fraud_risk_score)} font-monospace">${tx.fraud_risk_score.toFixed(1)}</span></td>
        <td><span class="badge ${getTierBadgeClass(tx.risk_level)}">${tx.risk_level}</span></td>
        <td>
          <button class="btn btn-sm btn-outline-info" onclick="inspectTransaction('${tx.transaction_id}')">
            <i class="bi bi-eye"></i>
          </button>
        </td>
      </tr>
    `).join("");
  } catch (err) {
    console.error("Error loading transaction stream:", err);
  }
}

async function inspectTransaction(txId) {
  try {
    const res = await fetch(`/api/transactions/${txId}`);
    const data = await res.json();
    if (data.status !== "success") return;

    const tx = data.transaction;
    const body = document.getElementById("txModalBody");

    body.innerHTML = `
      <div class="d-flex justify-content-between align-items-center mb-3 p-3 bg-dark rounded border border-secondary-subtle">
        <div>
          <span class="text-muted-custom small">TRANSACTION ID</span>
          <h5 class="m-0 fw-bold text-white font-monospace">${tx.transaction_id}</h5>
        </div>
        <div class="text-end">
          <span class="badge ${getTierBadgeClass(tx.risk_level)} fs-6">${tx.risk_level} RISK (${tx.fraud_risk_score.toFixed(1)})</span>
          <div class="small text-muted-custom mt-1 font-monospace">${tx.timestamp}</div>
        </div>
      </div>

      <div class="row g-3 mb-3">
        <div class="col-md-6">
          <div class="p-3 bg-dark rounded border border-secondary-subtle h-100">
            <h6 class="text-white fw-bold mb-2"><i class="bi bi-person-fill text-primary-light me-1"></i>Counterparty Information</h6>
            <div class="small text-muted-custom mb-1"><strong>Sender:</strong> <span class="font-monospace text-white">${tx.sender_id}</span></div>
            <div class="small text-muted-custom mb-1"><strong>Receiver:</strong> <span class="font-monospace text-white">${tx.receiver_id}</span></div>
            <div class="small text-muted-custom mb-1"><strong>Amount:</strong> <span class="font-monospace text-white fw-bold">₹${Number(tx.amount).toLocaleString("en-IN", {minimumFractionDigits: 2})}</span></div>
            <div class="small text-muted-custom mb-1"><strong>Merchant Category:</strong> ${tx.merchant_category}</div>
            <div class="small text-muted-custom"><strong>Transaction Type:</strong> ${tx.transaction_type}</div>
          </div>
        </div>

        <div class="col-md-6">
          <div class="p-3 bg-dark rounded border border-secondary-subtle h-100">
            <h6 class="text-white fw-bold mb-2"><i class="bi bi-geo-alt-fill text-danger me-1"></i>Contextual Signals</h6>
            <div class="small text-muted-custom mb-1"><strong>Location:</strong> ${tx.location} ${tx.location_changed ? '<span class="badge bg-danger ms-1">Changed</span>' : ''}</div>
            <div class="small text-muted-custom mb-1"><strong>Device:</strong> ${tx.device_type} ${tx.device_changed ? '<span class="badge bg-danger ms-1">Changed</span>' : ''}</div>
            <div class="small text-muted-custom mb-1"><strong>UPI Channel:</strong> ${tx.upi_channel}</div>
            <div class="small text-muted-custom mb-1"><strong>Historical Avg:</strong> ₹${Number(tx.historical_avg_amount).toFixed(2)}</div>
            <div class="small text-muted-custom"><strong>Amount Deviation:</strong> <span class="fw-bold ${tx.amount_deviation > 3 ? 'text-danger' : 'text-success'}">${tx.amount_deviation}x</span></div>
          </div>
        </div>
      </div>

      <div class="p-3 bg-dark rounded border border-secondary-subtle mb-3">
        <h6 class="text-white fw-bold mb-2"><i class="bi bi-cpu text-info me-1"></i>Detector Verdicts</h6>
        <div class="d-flex flex-wrap gap-2 font-monospace small">
          <span class="badge ${tx.iqr_anomaly ? 'bg-danger' : 'bg-secondary'}">IQR: ${tx.iqr_anomaly ? 'ANOMALY' : 'NORMAL'} (${tx.iqr_score.toFixed(1)})</span>
          <span class="badge ${tx.isolation_prediction ? 'bg-danger' : 'bg-secondary'}">IsoForest: ${tx.isolation_prediction ? 'ANOMALY' : 'NORMAL'} (${tx.isolation_score.toFixed(1)})</span>
          <span class="badge ${tx.time_series_anomaly ? 'bg-danger' : 'bg-secondary'}">TimeSeries: ${tx.time_series_anomaly ? 'BURST' : 'NORMAL'} (${tx.time_series_score.toFixed(1)})</span>
          <span class="badge bg-dark border border-secondary text-white">Consensus: ${tx.detection_method}</span>
        </div>
      </div>

      ${tx.alert ? `
        <div class="p-3 bg-soft-danger rounded border border-danger">
          <div class="d-flex justify-content-between align-items-center mb-1">
            <h6 class="text-danger fw-bold m-0"><i class="bi bi-bell-fill me-1"></i>Active Alert: ${tx.alert.alert_id}</h6>
            <span class="badge ${getStatusBadgeClass(tx.alert.status)}">${tx.alert.status}</span>
          </div>
          <div class="small text-muted-custom">${Array.isArray(tx.alert.reasons) ? tx.alert.reasons.join(" • ") : tx.alert.reasons}</div>
        </div>
      ` : ''}
    `;

    const modal = new bootstrap.Modal(document.getElementById("txDetailModal"));
    modal.show();
  } catch (err) {
    console.error("Error inspecting transaction:", err);
  }
}

// -------------------------------------------------------------
// 7. API Sandbox & Manual Testing Form
// -------------------------------------------------------------
async function handleSandboxSubmit(e) {
  e.preventDefault();

  const payload = {
    sender_id: document.getElementById("sb-sender").value.trim(),
    receiver_id: document.getElementById("sb-receiver").value.trim(),
    amount: parseFloat(document.getElementById("sb-amount").value),
    merchant_category: document.getElementById("sb-category").value,
    transaction_type: document.getElementById("sb-tx-type").value,
    location: document.getElementById("sb-location").value.trim(),
    device_type: document.getElementById("sb-device").value,
    upi_channel: document.getElementById("sb-channel").value
  };

  const tsVal = document.getElementById("sb-timestamp").value;
  if (tsVal) {
    payload.timestamp = new Date(tsVal).toISOString();
  }

  const rawJsonEl = document.getElementById("sb-raw-json");
  const visualEl = document.getElementById("sb-response-visual");
  const statusBadge = document.getElementById("sb-status-badge");

  statusBadge.textContent = "INSPECTING...";
  statusBadge.className = "badge bg-warning font-monospace";

  try {
    const res = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const data = await res.json();

    rawJsonEl.textContent = JSON.stringify(data, null, 2);

    if (data.status !== "success") {
      statusBadge.textContent = "REJECTED";
      statusBadge.className = "badge bg-danger font-monospace";
      visualEl.innerHTML = `<div class="alert alert-danger">${data.message}</div>`;
      return;
    }

    statusBadge.textContent = `${data.risk_level.toUpperCase()}`;
    statusBadge.className = `badge ${getTierBadgeClass(data.risk_level)} font-monospace`;

    const reasonsList = (data.reasons || []).map(r => `
      <div class="reason-item">
        <i class="bi bi-shield-exclamation text-warning reason-check"></i>
        <span>${r}</span>
      </div>
    `).join("");

    visualEl.innerHTML = `
      <div class="d-flex justify-content-between align-items-center mb-3 p-3 bg-dark rounded border border-secondary-subtle">
        <div>
          <span class="text-muted-custom small">TRANSACTION ID GENERATED</span>
          <h5 class="m-0 fw-bold text-white font-monospace">${data.transaction_id}</h5>
        </div>
        <div class="text-end">
          <div class="fs-4 fw-bold ${getScoreTextClass(data.risk_score)} font-monospace">${data.risk_score.toFixed(1)} / 100</div>
          <span class="badge ${getTierBadgeClass(data.risk_level)}">${data.risk_level} RISK</span>
        </div>
      </div>

      <div class="alert bg-soft-info border border-info text-white p-3 mb-3">
        <strong>Recommendation:</strong> ${data.recommendation}
      </div>

      <div class="mb-3">
        <h6 class="text-white fw-bold mb-2">Explanations & Contributing Flags</h6>
        <div class="reasons-list">${reasonsList}</div>
      </div>

      <div class="p-3 bg-dark rounded border border-secondary-subtle">
        <div class="d-flex justify-content-around text-center font-monospace small">
          <div><div class="text-muted-custom">IQR</div><div class="${data.iqr_anomaly ? 'text-danger' : 'text-success'} fw-bold">${data.iqr_anomaly ? 'ANOMALY' : 'PASS'}</div></div>
          <div><div class="text-muted-custom">ISOLATION FOREST</div><div class="${data.isolation_anomaly ? 'text-danger' : 'text-success'} fw-bold">${data.isolation_anomaly ? 'OUTLIER' : 'PASS'}</div></div>
          <div><div class="text-muted-custom">TIME SERIES</div><div class="${data.time_series_anomaly ? 'text-danger' : 'text-success'} fw-bold">${data.time_series_anomaly ? 'BURST' : 'PASS'}</div></div>
        </div>
      </div>
    `;

    showToast("Transaction Analyzed", `Tx ID: ${data.transaction_id} — Score: ${data.risk_score.toFixed(1)}`, "info");
    loadDashboardData();

  } catch (err) {
    console.error("Sandbox test error:", err);
    rawJsonEl.textContent = `{"error": "${err.message}"}`;
    statusBadge.textContent = "ERROR";
    statusBadge.className = "badge bg-danger font-monospace";
  }
}

// -------------------------------------------------------------
// 8. Model Architecture & Benchmarks
// -------------------------------------------------------------
async function loadModelArchitectureData() {
  try {
    const res = await fetch("/api/model-info");
    const data = await res.json();
    if (data.status !== "success") return;

    const benchmarks = data.evaluation_benchmarks;
    if (benchmarks && benchmarks.scenario_detection_rates) {
      const scenariosGrid = document.getElementById("scenarios-grid");
      if (!scenariosGrid) return;

      const entries = Object.entries(benchmarks.scenario_detection_rates);
      scenariosGrid.innerHTML = entries.map(([scName, sc]) => `
        <div class="col-md-3 col-sm-6">
          <div class="p-3 bg-dark rounded border border-secondary-subtle h-100">
            <div class="small fw-bold text-white mb-1">${scName}</div>
            <div class="d-flex justify-content-between align-items-baseline">
              <span class="fs-5 fw-bold text-accent font-monospace">${sc.detection_rate}%</span>
              <span class="small text-muted-custom">${sc.detected}/${sc.total} Caught</span>
            </div>
            <div class="risk-meter-container mt-2" style="height: 6px;">
              <div class="risk-meter-fill bg-accent" style="width: ${sc.detection_rate}%; background-color: var(--text-accent);"></div>
            </div>
            <div class="small text-muted-custom mt-2" style="font-size: 0.72rem;">Avg Risk Score: <strong>${sc.avg_risk_score}</strong></div>
          </div>
        </div>
      `).join("");
    }
  } catch (err) {
    console.error("Error loading model architecture info:", err);
  }
}

// -------------------------------------------------------------
// Utility Helpers
// -------------------------------------------------------------
function getTierBadgeClass(tier) {
  switch (tier) {
    case "Critical": return "bg-danger";
    case "High": return "bg-warning text-dark";
    case "Medium": return "bg-info text-dark";
    case "Low":
    default: return "bg-success";
  }
}

function getStatusBadgeClass(status) {
  switch (status) {
    case "Resolved": return "bg-soft-success text-success";
    case "Reviewing": return "bg-soft-warning text-warning";
    case "New":
    default: return "bg-soft-danger text-danger";
  }
}

function getScoreBadgeClass(score) {
  if (score >= 80) return "bg-soft-danger text-danger";
  if (score >= 60) return "bg-soft-warning text-warning";
  if (score >= 30) return "bg-soft-info text-info";
  return "bg-soft-success text-success";
}

function getScoreTextClass(score) {
  if (score >= 80) return "text-danger";
  if (score >= 60) return "text-warning";
  if (score >= 30) return "text-info";
  return "text-success";
}

function getScoreMeterFillClass(score) {
  if (score >= 80) return "bg-danger";
  if (score >= 60) return "bg-warning";
  if (score >= 30) return "bg-info";
  return "bg-success";
}

function showToast(title, message, variant = "info") {
  const toastEl = document.getElementById("liveToast");
  const titleEl = document.getElementById("toast-title");
  const bodyEl = document.getElementById("toast-body");
  const timeEl = document.getElementById("toast-time");

  if (toastEl && titleEl && bodyEl) {
    titleEl.textContent = title;
    bodyEl.textContent = message;
    timeEl.textContent = "Just now";
    const toast = new bootstrap.Toast(toastEl, { delay: 4500 });
    toast.show();
  }
}
