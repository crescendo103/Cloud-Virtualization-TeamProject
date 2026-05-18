from __future__ import annotations

import shutil
import subprocess
import time


def get_gpu_status() -> dict:
    if shutil.which("nvidia-smi") is None:
        return {
            "available": False,
            "checked_at": time.time(),
            "message": "nvidia-smi not found. Running with CPU fallback.",
            "gpus": [],
        }

    command = [
        "nvidia-smi",
        "--query-gpu=index,name,utilization.gpu,memory.used,memory.total",
        "--format=csv,noheader,nounits",
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as exc:
        return {
            "available": False,
            "checked_at": time.time(),
            "message": exc.stderr.strip() or "Failed to query GPU status.",
            "gpus": [],
        }

    gpus = []
    for line in result.stdout.strip().splitlines():
        gpu_id, name, utilization, memory_used, memory_total = [value.strip() for value in line.split(",")]
        memory_used_value = int(memory_used)
        memory_total_value = int(memory_total)
        gpus.append(
            {
                "id": int(gpu_id),
                "name": name,
                "utilization": int(utilization),
                "memory_used": memory_used_value,
                "memory_total": memory_total_value,
                "memory_ratio": round(memory_used_value / memory_total_value, 4) if memory_total_value else 1.0,
            }
        )

    return {
        "available": bool(gpus),
        "checked_at": time.time(),
        "message": "ok",
        "gpus": gpus,
    }

