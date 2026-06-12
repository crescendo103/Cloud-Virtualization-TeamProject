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

const SVG_NS = "http://www.w3.org/2000/svg";
const CHART_WIDTH = 600;
const CHART_HEIGHT = 220;
const CHART_PADDING = 36;

function svgElement(name, attributes = {}) {
  const element = document.createElementNS(SVG_NS, name);
  Object.entries(attributes).forEach(([key, value]) => element.setAttribute(key, value));
  return element;
}

function addChartFrame(svg, labels, maxValue, labelPlacement = "spread") {
  svg.replaceChildren();
  const plotWidth = CHART_WIDTH - CHART_PADDING * 2;
  const plotHeight = CHART_HEIGHT - CHART_PADDING * 2;

  svg.append(
    svgElement("line", {
      x1: CHART_PADDING,
      y1: CHART_PADDING,
      x2: CHART_PADDING,
      y2: CHART_PADDING + plotHeight,
      class: "chart-axis",
    }),
    svgElement("line", {
      x1: CHART_PADDING,
      y1: CHART_PADDING + plotHeight,
      x2: CHART_PADDING + plotWidth,
      y2: CHART_PADDING + plotHeight,
      class: "chart-axis",
    }),
  );

  [0, 0.5, 1].forEach((ratio) => {
    const y = CHART_PADDING + plotHeight * (1 - ratio);
    const label = svgElement("text", {
      x: CHART_PADDING - 8,
      y: y + 4,
      class: "chart-label chart-label-y",
    });
    label.textContent = (maxValue * ratio).toFixed(maxValue < 10 ? 1 : 0);
    svg.append(label);
  });

  const labelStep = Math.max(1, Math.ceil(labels.length / 12));
  labels.forEach((value, index) => {
    if (index % labelStep !== 0 && index !== labels.length - 1) return;
    const x = labelPlacement === "band"
      ? CHART_PADDING + (plotWidth / labels.length) * (index + 0.5)
      : labels.length === 1
        ? CHART_PADDING + plotWidth / 2
        : CHART_PADDING + (plotWidth * index) / (labels.length - 1);
    const label = svgElement("text", {
      x,
      y: CHART_HEIGHT - 8,
      class: "chart-label chart-label-x",
    });
    label.textContent = value;
    svg.append(label);
  });

  return { plotWidth, plotHeight };
}

function renderLineChart(svg, labels, datasets, fixedMax = null) {
  const values = datasets.flatMap((dataset) => dataset.values);
  const maxValue = fixedMax || Math.max(...values, 1e-6);
  const { plotWidth, plotHeight } = addChartFrame(svg, labels, maxValue);

  datasets.forEach((dataset, datasetIndex) => {
    const points = dataset.values.map((value, index) => {
      const x = labels.length === 1
        ? CHART_PADDING + plotWidth / 2
        : CHART_PADDING + (plotWidth * index) / (labels.length - 1);
      const y = CHART_PADDING + plotHeight * (1 - value / maxValue);
      return `${x},${y}`;
    });
    svg.append(svgElement("polyline", {
      points: points.join(" "),
      class: `chart-line chart-series-${datasetIndex}`,
    }));

    const legend = svgElement("text", {
      x: CHART_PADDING + datasetIndex * 120,
      y: 18,
      class: `chart-legend chart-series-${datasetIndex}`,
    });
    legend.textContent = dataset.label;
    svg.append(legend);
  });
}

function renderBarChart(svg, labels, datasets) {
  const { plotWidth, plotHeight } = addChartFrame(svg, labels, 100, "band");
  const groupWidth = plotWidth / Math.max(labels.length, 1);
  const barWidth = Math.min(36, groupWidth / (datasets.length + 1));

  datasets.forEach((dataset, datasetIndex) => {
    dataset.values.forEach((value, index) => {
      const height = plotHeight * (value / 100);
      const groupStart = CHART_PADDING + index * groupWidth;
      const groupCenter = groupStart + groupWidth / 2;
      const x = groupCenter + (datasetIndex - (datasets.length - 1) / 2) * barWidth - barWidth / 2;
      svg.append(svgElement("rect", {
        x,
        y: CHART_PADDING + plotHeight - height,
        width: barWidth - 3,
        height,
        class: `chart-bar chart-series-${datasetIndex}`,
      }));
    });

    const legend = svgElement("text", {
      x: CHART_PADDING + datasetIndex * 120,
      y: 18,
      class: `chart-legend chart-series-${datasetIndex}`,
    });
    legend.textContent = dataset.label;
    svg.append(legend);
  });
}

function updateTrainingCharts(history) {
  const metrics = Array.isArray(history) ? history : [];
  const epochs = metrics.map((metric) => metric.epoch);

  lossEmptyEl.hidden = metrics.length > 0;
  accuracyEmptyEl.hidden = metrics.length > 0;

  if (!metrics.length) {
    lossChartEl.replaceChildren();
    accuracyChartEl.replaceChildren();
    return;
  }

  renderLineChart(lossChartEl, epochs, [
    { label: "Train Loss", values: metrics.map((metric) => metric.train_loss) },
    { label: "Val Loss", values: metrics.map((metric) => metric.val_loss) },
  ]);
  renderLineChart(accuracyChartEl, epochs, [
    { label: "Train Acc", values: metrics.map((metric) => metric.train_accuracy) },
    { label: "Val Acc", values: metrics.map((metric) => metric.val_accuracy) },
  ], 1);
}

function updateGpuChart(gpu) {
  const gpus = gpu.available ? gpu.gpus : [];

  gpuEmptyEl.hidden = gpus.length > 0;

  if (!gpus.length) {
    gpuChartEl.replaceChildren();
    return;
  }

  renderBarChart(gpuChartEl, gpus.map((item) => `GPU ${item.id}`), [
    { label: "사용률 (%)", values: gpus.map((item) => item.utilization) },
    { label: "메모리 (%)", values: gpus.map((item) => Math.round(item.memory_ratio * 100)) },
  ]);
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

refresh();
window.setInterval(refresh, 2000);
