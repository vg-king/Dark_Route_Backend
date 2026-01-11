// API Base URL configuration for deployment support
// - Local development: http://localhost:8000
// - Render/Production: Set via window.API_BASE or environment at build time
// - Default fallback: Current origin (for same-host deployment)

const getAPIBase = () => {
  // Priority 1: Explicit window.API_BASE (set via HTML script tag or build process)
  if (typeof window.API_BASE !== 'undefined' && window.API_BASE) {
    return window.API_BASE;
  }
  
  // Priority 2: Environment variable at runtime (if injected)
  if (typeof API_URL !== 'undefined' && API_URL) {
    return API_URL;
  }
  
  // Priority 3: Check if running on Render or similar platform
  const hostname = window.location.hostname;
  if (hostname !== 'localhost' && hostname !== '127.0.0.1') {
    // On production domain, assume backend is on same origin
    return window.location.origin;
  }
  
  // Priority 4: Default to localhost:8000 for local development
  return "http://localhost:8000";
};

const API_BASE = getAPIBase();
const statusEl = document.getElementById("api-status");
const latencyEl = document.getElementById("latency");
const form = document.getElementById("analyze-form");
const analyzeBtn = document.getElementById("analyze-btn");
const reloadHealthBtn = document.getElementById("reload-health");
const loadHistoryBtn = document.getElementById("load-history");
const summaryEl = document.getElementById("result-summary");
const behaviorEl = document.getElementById("behavior");
const healthEl = document.getElementById("health");
const identifiersEl = document.getElementById("identifiers");
const vitalsEl = document.getElementById("vitals");
const recommendationsEl = document.getElementById("recommendations");
const previewEl = document.getElementById("preview");
const previewImg = document.getElementById("preview-img");
const historyBody = document.getElementById("history-body");

async function checkHealth() {
  statusEl.textContent = "Checking API…";
  statusEl.className = "status";
  try {
    const res = await fetch(`${API_BASE}/health`);
    const data = await res.json();
    if (data.status === "ok") {
      const loaded = data.model_loaded === "True" || data.model_loaded === true;
      statusEl.textContent = `✅ API Ready (v${data.version}) - ${loaded ? 'ML Model Loaded' : 'Heuristic Mode'}`;
      statusEl.className = "status success";
    }
  } catch (err) {
    statusEl.textContent = "❌ API Unreachable - Start server with: python server_enhanced.py";
    statusEl.className = "status error";
  }
}

function renderScores(scores) {
  if (!scores || Object.keys(scores).length === 0) return "";
  return Object.entries(scores)
    .map(([k, v]) => `<div class="score-line"><span>${k}</span><span>${(v * 100).toFixed(1)}%</span></div>`)
    .join("");
}

function renderResult(data) {
  latencyEl.textContent = `${data.elapsedMs || "--"} ms`;
  
  // Summary with identification info
  let summaryHTML = `<h3>Summary</h3>`;
  summaryHTML += `<p><strong>Animal ID:</strong> ${data.animalId || "unknown"}</p>`;
  
  if (data.identification) {
    summaryHTML += `<p><strong>ID Method:</strong> ${data.identification.method || "manual"}</p>`;
    summaryHTML += `<p><strong>ID Confidence:</strong> ${(data.identification.confidence * 100).toFixed(1)}%</p>`;
    
    if (data.identification.qr_detected) {
      summaryHTML += `<p class="badge success">✓ QR Code Detected</p>`;
    }
    if (data.identification.ear_tags_detected) {
      summaryHTML += `<p class="badge warning">✓ Ear Tag Detected</p>`;
    }
    if (data.identification.biometric_available) {
      summaryHTML += `<p class="badge info">✓ Biometric Available</p>`;
    }
  }
  
  if (data.attendanceMarked) {
    summaryHTML += `<p class="badge success">✓ Attendance Marked</p>`;
  }
  
  summaryHTML += `<p><strong>Recorded:</strong> ${data.recordedAt ? new Date(data.recordedAt).toLocaleString() : "--"}</p>`;
  summaryEl.innerHTML = summaryHTML;

  // Behavior
  behaviorEl.innerHTML = `
    <div class="badge">${data.behavior?.label || "--"}</div>
    <div class="scores">${renderScores(data.behavior?.scores)}</div>
  `;

  // Health with comprehensive analysis
  let healthHTML = `<div class="badge health-${(data.health?.label || '').toLowerCase()}">${data.health?.label || "--"}</div>`;
  healthHTML += `<p class="muted">Confidence: ${((data.health?.confidence || 0) * 100).toFixed(1)}%</p>`;
  
  if (data.health?.comprehensive) {
    const comp = data.health.comprehensive;
    healthHTML += `<p><strong>Overall Status:</strong> ${comp.overall_status}</p>`;
    healthHTML += `<p><strong>Health Score:</strong> ${comp.health_score}/100</p>`;
    
    if (comp.body_condition?.score) {
      healthHTML += `<p><strong>Body Condition:</strong> ${comp.body_condition.score}/5</p>`;
      healthHTML += `<p class="muted">${comp.body_condition.assessment}</p>`;
    }
    
    if (comp.lameness?.detected) {
      healthHTML += `<p class="badge warning">⚠️ Lameness Detected</p>`;
    }
    
    if (comp.symptoms?.total_detected > 0) {
      healthHTML += `<p class="badge warning">⚠️ ${comp.symptoms.total_detected} Symptoms Detected</p>`;
    }
  }
  
  healthHTML += `<div class="scores">${renderScores(data.health?.scores)}</div>`;
  healthEl.innerHTML = healthHTML;

  // Identifiers
  identifiersEl.innerHTML = `
    <div class="score-line"><span>Ear Tag</span><span>${data.identifiers?.earTagId || "--"}</span></div>
    <div class="score-line"><span>RFID</span><span>${data.identifiers?.rfid || "--"}</span></div>
    <div class="score-line"><span>QR Collar</span><span>${data.identifiers?.qrId || "--"}</span></div>
  `;

  // Vitals
  const metrics = data.metrics || {};
  vitalsEl.innerHTML = `
    <div class="score-line"><span>Weight</span><span>${metrics.weight_kg || "--"} kg</span></div>
    <div class="score-line"><span>Body Temp</span><span>${metrics.body_temperature_c || "--"} °C</span></div>
    <div class="score-line"><span>Heart Rate</span><span>${metrics.heart_rate_bpm || "--"} bpm</span></div>
    <div class="score-line"><span>Respiratory</span><span>${metrics.respiratory_rate_bpm || "--"} bpm</span></div>
  `;

  // Recommendations - handle both array and single strings
  let recs = [];
  if (Array.isArray(data.recommendations)) {
    recs = data.recommendations;
  } else if (data.recommendations) {
    recs = [data.recommendations];
  }
  
  recommendationsEl.innerHTML = recs.length > 0
    ? recs.map((r) => `<li>${r}</li>`).join("")
    : '<li class="muted">No recommendations</li>';
}

async function loadHistory() {
  try {
    const res = await fetch(`${API_BASE}/records`);
    const data = await res.json();
    const rows = (data.items || []).map((item) => {
      const recordedAt = item.recorded_at ? new Date(item.recorded_at).toLocaleString() : "--";
      const healthLabel = item.health_status || item.health?.label || "--";
      const behaviorLabel = item.behavior_status || item.behavior?.label || "--";
      
      return `
        <tr>
          <td>${item.animal_id}</td>
          <td>${behaviorLabel}</td>
          <td class="health-${healthLabel.toLowerCase()}">${healthLabel}</td>
          <td>${item.location || "--"}</td>
          <td>${recordedAt}</td>
        </tr>
      `;
    });
    historyBody.innerHTML = rows.length > 0
      ? rows.join("")
      : '<tr><td colspan="5" class="muted">No records yet.</td></tr>';
  } catch (err) {
    historyBody.innerHTML = '<tr><td colspan="5" class="muted">Could not load records.</td></tr>';
  }
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const fileInput = document.getElementById("file");
  if (!fileInput.files.length) {
    alert("Please select an image.");
    return;
  }

  const file = fileInput.files[0];
  const formData = new FormData(form);

  analyzeBtn.textContent = "Analyzing…";
  analyzeBtn.disabled = true;

  // Preview image
  previewEl.classList.remove("hidden");
  previewImg.src = URL.createObjectURL(file);

  try {
    const res = await fetch(`${API_BASE}/analyze/image`, {
      method: "POST",
      body: formData,
    });
    if (!res.ok) {
      const errorData = await res.json().catch(() => ({ detail: "Unknown error" }));
      throw new Error(errorData.detail || `HTTP ${res.status}`);
    }
    const data = await res.json();
    renderResult(data);
    loadHistory();
  } catch (err) {
    summaryEl.innerHTML = `<h3>Error</h3><p class="error">❌ ${err.message}</p>`;
    console.error("Analysis error:", err);
  } finally {
    analyzeBtn.textContent = "Analyze";
    analyzeBtn.disabled = false;
  }
});

reloadHealthBtn.addEventListener("click", checkHealth);
loadHistoryBtn.addEventListener("click", loadHistory);

// Initial load
checkHealth();
loadHistory();

