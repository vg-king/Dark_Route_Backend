const API_BASE = "http://localhost:8080";
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
  try {
    const res = await fetch(`${API_BASE}/health`);
    const data = await res.json();
    const loaded = data.model_loaded === "True" || data.model_loaded === true;
    statusEl.textContent = loaded ? "API ready (model loaded)" : "API ready (model not loaded)";
  } catch (err) {
    statusEl.textContent = "API unreachable";
  }
}

function renderScores(scores) {
  if (!scores) return "";
  return Object.entries(scores)
    .map(([k, v]) => `<div class="score-line"><span>${k}</span><span>${(v * 100).toFixed(1)}%</span></div>`) // eslint-disable-line
    .join("");
}

function renderResult(data) {
  latencyEl.textContent = `${data.elapsedMs || "--"} ms`;
  summaryEl.innerHTML = `
    <h3>Summary</h3>
    <p><strong>Animal:</strong> ${data.animalId || "unknown"}</p>
    <p><strong>Recorded:</strong> ${data.recordedAt || "--"}</p>
  `;

  behaviorEl.innerHTML = `
    <div class="badge">${data.behavior?.label || "--"}</div>
    <div class="scores">${renderScores(data.behavior?.scores)}</div>
  `;

  healthEl.innerHTML = `
    <div class="badge">${data.health?.label || "--"}</div>
    <p class="muted">Confidence: ${(data.health?.confidence || 0).toFixed(2)}</p>
    <div class="scores">${renderScores(data.health?.scores)}</div>
  `;

  identifiersEl.innerHTML = `
    <div class="score-line"><span>Ear Tag</span><span>${data.identifiers?.earTagId || "--"}</span></div>
    <div class="score-line"><span>RFID</span><span>${data.identifiers?.rfid || "--"}</span></div>
    <div class="score-line"><span>QR Collar</span><span>${data.identifiers?.qrId || "--"}</span></div>
  `;

  vitalsEl.innerHTML = `
    <div class="score-line"><span>Weight</span><span>${data.metrics?.weightKg || "--"} kg</span></div>
    <div class="score-line"><span>Body Temp</span><span>${data.metrics?.bodyTempC || "--"} °C</span></div>
    <div class="score-line"><span>Heart Rate</span><span>${data.metrics?.heartRateBpm || "--"} bpm</span></div>
  `;

  recommendationsEl.innerHTML = (data.recommendations || [])
    .map((r) => `<li>${r}</li>`) // eslint-disable-line
    .join("") || '<li class="muted">No recommendations</li>';
}

async function loadHistory() {
  try {
    const res = await fetch(`${API_BASE}/records`);
    const data = await res.json();
    const rows = (data.items || []).map((item) => `
      <tr>
        <td>${item.animal_id}</td>
        <td>${item.behavior?.label || "--"}</td>
        <td>${item.health?.label || "--"}</td>
        <td>${item.location || "--"}</td>
        <td>${item.recorded_at?.replace('T', ' ').replace('Z', '') || "--"}</td>
      </tr>
    `);
    historyBody.innerHTML = rows.join("") || '<tr><td colspan="5" class="muted">No records yet.</td></tr>';
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
    if (!res.ok) throw new Error("Analysis failed");
    const data = await res.json();
    renderResult(data);
    loadHistory();
  } catch (err) {
    summaryEl.innerHTML = `<p class="muted">Error: ${err.message}</p>`;
  } finally {
    analyzeBtn.textContent = "Analyze";
    analyzeBtn.disabled = false;
  }
});

reloadHealthBtn.addEventListener("click", checkHealth);
loadHistoryBtn.addEventListener("click", loadHistory);

checkHealth();
loadHistory();
