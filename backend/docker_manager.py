from __future__ import annotations

from pathlib import Path


class DockerConfig:
    def __init__(
        self,
        image: str = "pytorch/pytorch:2.5.1-cuda12.4-cudnn9-runtime",
        trainer_dir: str | Path = "3. Trainer",
    ) -> None:
        self.image = image
        self.trainer_dir = Path(trainer_dir).resolve()

