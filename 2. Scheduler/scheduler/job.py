from __future__ import annotations

import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Literal


JobStatus = Literal["queued", "running", "completed", "failed"]
ModelName = Literal["cnn", "linear"]


@dataclass
class TrainingJob:
    data_dir: str
    model: ModelName = "cnn"
    epochs: int = 5
    batch_size: int = 32
    learning_rate: float = 1e-3
    image_size: int = 64
    output_dir: str = "outputs"
    job_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    status: JobStatus = "queued"
    created_at: float = field(default_factory=time.time)
    started_at: float | None = None
    finished_at: float | None = None
    gpu_id: int | None = None
    error: str | None = None

    def validate(self) -> None:
        if self.model not in ("cnn", "linear"):
            raise ValueError("model must be 'cnn' or 'linear'")
        if self.epochs < 1:
            raise ValueError("epochs must be at least 1")
        if self.batch_size < 1:
            raise ValueError("batch_size must be at least 1")
        if self.learning_rate <= 0:
            raise ValueError("learning_rate must be greater than 0")
        if not Path(self.data_dir).exists():
            raise FileNotFoundError(f"data_dir does not exist: {self.data_dir}")

    def to_dict(self) -> dict:
        return asdict(self)

