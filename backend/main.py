from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .gpu_monitor import get_gpu_status
from .job_service import JobService
from .predictor import RequestPredictor

ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
INPUT_DIR = ROOT_DIR / "1. Input"
DASHBOARD_DIR = ROOT_DIR / "4. Dashboard"

app = FastAPI(title="Cloud Virtualization Team Project")
job_service = JobService(
    upload_dir=DATA_DIR / "uploads",
    output_dir=ROOT_DIR / "3. Trainer" / "outputs",
    state_dir=ROOT_DIR / "2. Scheduler" / "scheduler_state",
)
predictor = RequestPredictor(ROOT_DIR / "backend" / "logs.json")

app.mount("/input", StaticFiles(directory=INPUT_DIR, html=True), name="input")
app.mount("/dashboard", StaticFiles(directory=DASHBOARD_DIR, html=True), name="dashboard")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(INPUT_DIR / "index.html")


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/api/jobs")
def create_job(
    dataset: UploadFile = File(...),
    model: str = Form("cnn"),
    epochs: int = Form(5),
    batch_size: int = Form(32),
    learning_rate: float = Form(1e-3),
    image_size: int = Form(64),
) -> dict:
    predictor.record_request()
    try:
        job = job_service.submit_upload(
            dataset=dataset,
            model=model,
            epochs=epochs,
            batch_size=batch_size,
            learning_rate=learning_rate,
            image_size=image_size,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"job_id": job.job_id, "status": job.status}


@app.get("/api/jobs")
def list_jobs() -> dict:
    return {"jobs": job_service.list_jobs()}


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str) -> dict:
    job = job_service.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")
    return job


@app.get("/api/gpu")
def gpu_status() -> dict:
    return get_gpu_status()


@app.get("/api/predict")
def predict() -> dict:
    return predictor.predict_next_request_count()

