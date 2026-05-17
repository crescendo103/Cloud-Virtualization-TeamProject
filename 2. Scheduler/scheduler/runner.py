from __future__ import annotations

import subprocess
import sys
from abc import ABC, abstractmethod
from pathlib import Path

from .job import TrainingJob


class TrainerRunner(ABC):
    @abstractmethod
    def run(self, job: TrainingJob, gpu_id: int | None) -> None:
        raise NotImplementedError


class LocalTrainerRunner(TrainerRunner):
    def __init__(self, trainer_dir: str | Path) -> None:
        self.trainer_dir = Path(trainer_dir).resolve()

    def run(self, job: TrainingJob, gpu_id: int | None) -> None:
        output_dir = Path(job.output_dir)
        if not output_dir.is_absolute():
            output_dir = output_dir.resolve()
        output_dir = output_dir / job.job_id
        output_dir.mkdir(parents=True, exist_ok=True)

        command = [
            sys.executable,
            "-m",
            "trainer.train",
            "--data-dir",
            str(Path(job.data_dir).resolve()),
            "--model",
            job.model,
            "--epochs",
            str(job.epochs),
            "--batch-size",
            str(job.batch_size),
            "--learning-rate",
            str(job.learning_rate),
            "--image-size",
            str(job.image_size),
            "--output-dir",
            str(output_dir),
        ]
        subprocess.run(command, cwd=self.trainer_dir, check=True)


class DockerTrainerRunner(TrainerRunner):
    def __init__(self, image: str, trainer_dir: str | Path, container_workdir: str = "/app/trainer") -> None:
        self.image = image
        self.trainer_dir = Path(trainer_dir).resolve()
        self.container_workdir = container_workdir

    def run(self, job: TrainingJob, gpu_id: int | None) -> None:
        data_dir = Path(job.data_dir).resolve()
        output_dir = Path(job.output_dir).resolve() / job.job_id
        output_dir.mkdir(parents=True, exist_ok=True)

        command = [
            "docker",
            "run",
            "--rm",
            "--name",
            f"cv-trainer-{job.job_id}",
        ]
        if gpu_id is not None:
            command.extend(["--gpus", f"device={gpu_id}"])

        command.extend(
            [
                "-v",
                f"{data_dir}:/app/dataset:ro",
                "-v",
                f"{output_dir}:/app/outputs",
                "-v",
                f"{self.trainer_dir}:/app/trainer:ro",
                "-w",
                self.container_workdir,
                self.image,
                "python",
                "-m",
                "trainer.train",
                "--data-dir",
                "/app/dataset",
                "--model",
                job.model,
                "--epochs",
                str(job.epochs),
                "--batch-size",
                str(job.batch_size),
                "--learning-rate",
                str(job.learning_rate),
                "--image-size",
                str(job.image_size),
                "--output-dir",
                "/app/outputs",
            ]
        )
        subprocess.run(command, check=True)
