const jobsEl = document.querySelector("#jobs");
const detailEl = document.querySelector("#job-detail");
const gpuSummaryEl = document.querySelector("#gpu-summary");
const predictionEl = document.querySelector("#prediction");
const jobCountEl = document.querySelector("#job-count");
const query = new URLSearchParams(window.location.search);
let selectedJobId = query.get("job");

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
  } catch (error) {
    detailEl.textContent = error.message;
  }
}

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
    predictionEl.textContent = prediction.predicted_next_hour_requests;
    await loadJobDetail();
  } catch (error) {
    detailEl.textContent = error.message;
  }
}

refresh();
window.setInterval(refresh, 2000);
