from __future__ import annotations

import json
import queue
import shutil
import sys
import threading
import time
import zipfile
from pathlib import Path
from typing import Literal

from fastapi import UploadFile

ROOT_DIR = Path(__file__).resolve().parents[1]
SCHEDULER_DIR = ROOT_DIR / "2. Scheduler"
TRAINER_DIR = ROOT_DIR / "3. Trainer"
sys.path.insert(0, str(SCHEDULER_DIR))

from scheduler.gpu import GpuManager
from scheduler.job import TrainingJob
from scheduler.runner import DockerTrainerRunner, LocalTrainerRunner, TrainerRunner


RunnerMode = Literal["local", "docker"]


class JobService:
    def __init__(
        self,
        upload_dir: str | Path,
        output_dir: str | Path,
        state_dir: str | Path,
        runner_mode: RunnerMode = "local",
    ) -> None:
        self.upload_dir = Path(upload_dir)
        self.output_dir = Path(output_dir)
        self.state_dir = Path(state_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.state_dir.mkdir(parents=True, exist_ok=True)

        self.gpu_manager = GpuManager()
        self.runner = self._build_runner(runner_mode)
        self.queue: queue.Queue[TrainingJob] = queue.Queue()
        self.jobs: dict[str, TrainingJob] = {}
        self._lock = threading.Lock()
        self._worker = threading.Thread(target=self._work_loop, daemon=True)
        self._worker.start()

    def submit_upload(
        self,
        dataset: UploadFile,
        model: str,
        epochs: int,
        batch_size: int,
        learning_rate: float,
        image_size: int,
    ) -> TrainingJob:
        job = TrainingJob(
            data_dir="",
            model=model,  # type: ignore[arg-type]
            epochs=epochs,
            batch_size=batch_size,
            learning_rate=learning_rate,
            image_size=image_size,
            output_dir=str(self.output_dir),
        )
        job_dir = self.upload_dir / job.job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        archive_path = job_dir / (dataset.filename or "dataset.zip")

        with archive_path.open("wb") as f:
            shutil.copyfileobj(dataset.file, f)

        data_dir = self._extract_dataset(archive_path, job_dir / "dataset")
        job.data_dir = str(data_dir)
        job.validate()

        with self._lock:
            self.jobs[job.job_id] = job
            self.queue.put(job)
            self._write_job(job)
            self._write_queue_snapshot()
        return job

    def list_jobs(self) -> list[dict]:
        with self._lock:
            return [job.to_dict() for job in sorted(self.jobs.values(), key=lambda item: item.created_at, reverse=True)]

    def get_job(self, job_id: str) -> dict | None:
        with self._lock:
            job = self.jobs.get(job_id)
            if job is None:
                disk_job = self.state_dir / f"{job_id}.json"
                if disk_job.exists():
                    return json.loads(disk_job.read_text(encoding="utf-8"))
                return None
            payload = job.to_dict()

        trainer_status_path = self.output_dir / job_id / "status.json"
        if trainer_status_path.exists():
            payload["trainer_status"] = json.loads(trainer_status_path.read_text(encoding="utf-8"))
        return payload

    def _build_runner(self, runner_mode: RunnerMode) -> TrainerRunner:
        if runner_mode == "docker":
            return DockerTrainerRunner(image="pytorch/pytorch:2.5.1-cuda12.4-cudnn9-runtime", trainer_dir=TRAINER_DIR)
        return LocalTrainerRunner(trainer_dir=TRAINER_DIR)

    def _work_loop(self) -> None:
        while True:
            job = self.queue.get()
            try:
                self._run_job(job)
            finally:
                self.queue.task_done()

    def _run_job(self, job: TrainingJob) -> None:
        gpu_id = self._select_gpu()
        with self._lock:
            job.status = "running"
            job.started_at = time.time()
            job.gpu_id = gpu_id
            self._write_job(job)
            self._write_queue_snapshot()

        try:
            self.runner.run(job, gpu_id)
            job.status = "completed"
        except Exception as exc:
            job.status = "failed"
            job.error = str(exc)
        finally:
            with self._lock:
                job.finished_at = time.time()
                self._write_job(job)
                self._write_queue_snapshot()

    def _select_gpu(self) -> int | None:
        gpu_id = self.gpu_manager.acquire_gpu()
        if gpu_id is not None:
            return gpu_id
        if not self.gpu_manager.list_gpus():
            return None
        while gpu_id is None:
            time.sleep(2)
            gpu_id = self.gpu_manager.acquire_gpu()
        return gpu_id

    def _extract_dataset(self, archive_path: Path, target_dir: Path) -> Path:
        target_dir.mkdir(parents=True, exist_ok=True)
        if archive_path.suffix.lower() != ".zip":
            raise ValueError("Only .zip datasets are supported. Zip folders by class name.")

        with zipfile.ZipFile(archive_path) as zf:
            for member in zf.infolist():
                normalized_name = member.filename.replace("\\", "/")
                destination = (target_dir / normalized_name).resolve()
                if not str(destination).startswith(str(target_dir.resolve())):
                    raise ValueError("Unsafe zip path detected.")
                if member.is_dir():
                    destination.mkdir(parents=True, exist_ok=True)
                    continue
                destination.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(member) as source, destination.open("wb") as output:
                    shutil.copyfileobj(source, output)

        return self._find_imagefolder_root(target_dir)

    def _find_imagefolder_root(self, root: Path) -> Path:
        image_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp"}
        candidates = [root, *[path for path in root.iterdir() if path.is_dir()]]
        for candidate in candidates:
            class_dirs = [path for path in candidate.iterdir() if path.is_dir()]
            usable_classes = [
                path
                for path in class_dirs
                if any(file.suffix.lower() in image_extensions for file in path.rglob("*") if file.is_file())
            ]
            if len(usable_classes) >= 2:
                return candidate
        raise ValueError("Dataset zip must contain at least two class folders with images.")

    def _write_job(self, job: TrainingJob) -> None:
        (self.state_dir / f"{job.job_id}.json").write_text(
            json.dumps(job.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _write_queue_snapshot(self) -> None:
        payload = {
            "queued": [job.to_dict() for job in list(self.queue.queue)],
            "jobs": [job.to_dict() for job in self.jobs.values()],
        }
        (self.state_dir / "queue.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
