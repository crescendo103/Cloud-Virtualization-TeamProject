from __future__ import annotations

import json
import queue
import time
from pathlib import Path

from .gpu import GpuManager
from .job import TrainingJob
from .runner import TrainerRunner


class FifoScheduler:
    def __init__(
        self,
        runner: TrainerRunner,
        gpu_manager: GpuManager | None = None,
        state_dir: str | Path = "scheduler_state",
        allow_cpu_fallback: bool = True,
        poll_interval: float = 2.0,
    ) -> None:
        self.runner = runner
        self.gpu_manager = gpu_manager or GpuManager()
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.allow_cpu_fallback = allow_cpu_fallback
        self.poll_interval = poll_interval
        self._queue: queue.Queue[TrainingJob] = queue.Queue()
        self.jobs: dict[str, TrainingJob] = {}

    def submit(self, job: TrainingJob) -> str:
        job.validate()
        self.jobs[job.job_id] = job
        self._queue.put(job)
        self._write_job(job)
        self._write_queue_snapshot()
        return job.job_id

    def run_until_empty(self) -> None:
        while not self._queue.empty():
            job = self._queue.get()
            self._run_job(job)
            self._queue.task_done()
            self._write_queue_snapshot()

    def _run_job(self, job: TrainingJob) -> None:
        gpu_id = self._wait_for_gpu()
        job.status = "running"
        job.started_at = time.time()
        job.gpu_id = gpu_id
        self._write_job(job)

        try:
            self.runner.run(job, gpu_id)
            job.status = "completed"
        except Exception as exc:
            job.status = "failed"
            job.error = str(exc)
            raise
        finally:
            job.finished_at = time.time()
            self._write_job(job)

    def _wait_for_gpu(self) -> int | None:
        while True:
            gpu_id = self.gpu_manager.acquire_gpu()
            if gpu_id is not None:
                return gpu_id
            if self.allow_cpu_fallback and not self.gpu_manager.list_gpus():
                return None
            time.sleep(self.poll_interval)

    def _write_job(self, job: TrainingJob) -> None:
        path = self.state_dir / f"{job.job_id}.json"
        path.write_text(json.dumps(job.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")

    def _write_queue_snapshot(self) -> None:
        snapshot = {
            "queued": list(self._queue.queue),
            "jobs": [job.to_dict() for job in self.jobs.values()],
        }
        serializable = {
            "queued": [job.to_dict() for job in snapshot["queued"]],
            "jobs": snapshot["jobs"],
        }
        (self.state_dir / "queue.json").write_text(
            json.dumps(serializable, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

