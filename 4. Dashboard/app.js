const jobsEl = document.querySelector("#jobs");
const detailEl = document.querySelector("#job-detail");
const gpuSummaryEl = document.querySelector("#gpu-summary");
const predictionEl = document.querySelector("#prediction");
const jobCountEl = document.querySelector("#job-count");
const analyzeButton = document.querySelector("#analyze-button");
const analysisResultEl = document.querySelector("#analysis-result");
const lossChartEl = document.querySelector("#loss-chart");
const accuracyChartEl = document.querySelector("#accuracy-chart");
const gpuChartEl = document.querySelector("#gpu-chart");
const lossEmptyEl = document.querySelector("#loss-empty");
const accuracyEmptyEl = document.querySelector("#accuracy-empty");
const gpuEmptyEl = document.querySelector("#gpu-empty");
const query = new URLSearchParams(window.location.search);
let selectedJobId = query.get("job");

let lossChart = null;
let accuracyChart = null;
let gpuChart = null;

function createLineChart(canvas, trainLabel, valLabel) {
  return new Chart(canvas, {
    type: "line",
    data: {
      labels: [],
      datasets: [
        {
          label: trainLabel,
          data: [],
          borderColor: "#386641",
          backgroundColor: "#386641",
          tension: 0.25,
        },
        {
          label: valLabel,
          data: [],
          borderColor: "#bc4749",
          backgroundColor: "#bc4749",
          tension: 0.25,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      scales: {
        x: { title: { display: true, text: "Epoch" } },
      },
    },
  });
}

function setupCharts() {
  if (typeof Chart === "undefined") return;

  lossChart = createLineChart(lossChartEl, "Train Loss", "Val Loss");
  accuracyChart = createLineChart(accuracyChartEl, "Train Acc", "Val Acc");
  gpuChart = new Chart(gpuChartEl, {
    type: "bar",
    data: {
      labels: [],
      datasets: [
        { label: "사용률 (%)", data: [], backgroundColor: "#386641" },
        { label: "메모리 (%)", data: [], backgroundColor: "#1f7a8c" },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      scales: {
        y: { min: 0, max: 100 },
      },
    },
  });
}

function updateTrainingCharts(history) {
  if (!lossChart || !accuracyChart) return;
  const metrics = Array.isArray(history) ? history : [];
  const epochs = metrics.map((metric) => metric.epoch);

  lossEmptyEl.hidden = metrics.length > 0;
  accuracyEmptyEl.hidden = metrics.length > 0;

  lossChart.data.labels = epochs;
  lossChart.data.datasets[0].data = metrics.map((metric) => metric.train_loss);
  lossChart.data.datasets[1].data = metrics.map((metric) => metric.val_loss);
  lossChart.update("none");

  accuracyChart.data.labels = epochs;
  accuracyChart.data.datasets[0].data = metrics.map((metric) => metric.train_accuracy);
  accuracyChart.data.datasets[1].data = metrics.map((metric) => metric.val_accuracy);
  accuracyChart.update("none");
}

function updateGpuChart(gpu) {
  if (!gpuChart) return;
  const gpus = gpu.available ? gpu.gpus : [];

  gpuEmptyEl.hidden = gpus.length > 0;

  gpuChart.data.labels = gpus.map((item) => `GPU ${item.id}`);
  gpuChart.data.datasets[0].data = gpus.map((item) => item.utilization);
  gpuChart.data.datasets[1].data = gpus.map((item) => Math.round(item.memory_ratio * 100));
  gpuChart.update("none");
}

async function fetchJson(url) {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`${url} failed`);
  }
  return response.json();
}

function formatElapsed(job) {
  if (!job.started_at) return "-";
  const end = job.finished_at || Date.now() / 1000;
  return `${Math.max(0, Math.round(end - job.started_at))}s`;
}

function renderJobs(jobs) {
  jobCountEl.textContent = jobs.length;
  if (!jobs.length) {
    jobsEl.textContent = "아직 등록된 작업이 없습니다.";
    return;
  }

  jobsEl.innerHTML = "";
  jobs.forEach((job) => {
    const button = document.createElement("button");
    button.className = "job";
    button.innerHTML = `
      <span>
        <strong>${job.job_id}</strong>
        ${job.model.toUpperCase()} · ${job.epochs} epochs · ${formatElapsed(job)}
      </span>
      <span class="badge">${job.status}</span>
    `;
    button.addEventListener("click", () => {
      selectedJobId = job.job_id;
      analysisResultEl.hidden = true;
      loadJobDetail();
    });
    jobsEl.appendChild(button);
  });
}

async function loadJobDetail() {
  if (!selectedJobId) return;
  try {
    const job = await fetchJson(`/api/jobs/${selectedJobId}`);
    detailEl.textContent = JSON.stringify(job, null, 2);
    updateTrainingCharts(job.trainer_history);
  } catch (error) {
    detailEl.textContent = error.message;
  }
}

async function requestAnalysis() {
  if (!selectedJobId) {
    analysisResultEl.hidden = false;
    analysisResultEl.textContent = "먼저 작업을 선택하세요.";
    return;
  }
  analyzeButton.disabled = true;
  analyzeButton.textContent = "분석 중...";
  analysisResultEl.hidden = false;
  analysisResultEl.textContent = "AI가 학습 기록을 분석하고 있습니다...";
  try {
    const response = await fetch(`/api/jobs/${selectedJobId}/analyze`, { method: "POST" });
    const result = await response.json();
    analysisResultEl.textContent = result.analysis || result.message || "분석 결과가 없습니다.";
  } catch (error) {
    analysisResultEl.textContent = error.message;
  } finally {
    analyzeButton.disabled = false;
    analyzeButton.textContent = "AI 분석";
  }
}

analyzeButton.addEventListener("click", requestAnalysis);

async function refresh() {
  try {
    const [{ jobs }, gpu, prediction] = await Promise.all([
      fetchJson("/api/jobs"),
      fetchJson("/api/gpu"),
      fetchJson("/api/predict"),
    ]);
    renderJobs(jobs);
    if (!selectedJobId && jobs[0]) {
      selectedJobId = jobs[0].job_id;
    }
    gpuSummaryEl.textContent = gpu.available
      ? gpu.gpus.map((item) => `GPU ${item.id}: ${item.utilization}%`).join(", ")
      : "CPU fallback";
    updateGpuChart(gpu);
    predictionEl.textContent = prediction.predicted_next_hour_requests;
    await loadJobDetail();
  } catch (error) {
    detailEl.textContent = error.message;
  }
}

setupCharts();
refresh();
window.setInterval(refresh, 2000);
