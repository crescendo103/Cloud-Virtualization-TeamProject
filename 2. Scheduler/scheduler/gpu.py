from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass


@dataclass(frozen=True)
class GpuInfo:
    gpu_id: int
    utilization: int
    memory_used: int
    memory_total: int

    @property
    def memory_ratio(self) -> float:
        if self.memory_total == 0:
            return 1.0
        return self.memory_used / self.memory_total


class GpuManager:
    def __init__(self, max_utilization: int = 80, max_memory_ratio: float = 0.9) -> None:
        self.max_utilization = max_utilization
        self.max_memory_ratio = max_memory_ratio

    def list_gpus(self) -> list[GpuInfo]:
        if shutil.which("nvidia-smi") is None:
            return []

        command = [
            "nvidia-smi",
            "--query-gpu=index,utilization.gpu,memory.used,memory.total",
            "--format=csv,noheader,nounits",
        ]
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        gpus: list[GpuInfo] = []
        for line in result.stdout.strip().splitlines():
            gpu_id, utilization, memory_used, memory_total = [value.strip() for value in line.split(",")]
            gpus.append(
                GpuInfo(
                    gpu_id=int(gpu_id),
                    utilization=int(utilization),
                    memory_used=int(memory_used),
                    memory_total=int(memory_total),
                )
            )
        return gpus

    def acquire_gpu(self) -> int | None:
        candidates = [
            gpu
            for gpu in self.list_gpus()
            if gpu.utilization <= self.max_utilization and gpu.memory_ratio <= self.max_memory_ratio
        ]
        if not candidates:
            return None
        return sorted(candidates, key=lambda gpu: (gpu.utilization, gpu.memory_ratio))[0].gpu_id

