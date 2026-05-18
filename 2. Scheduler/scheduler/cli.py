from __future__ import annotations

import argparse
from pathlib import Path

from .fifo_scheduler import FifoScheduler
from .job import TrainingJob
from .runner import DockerTrainerRunner, LocalTrainerRunner


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="FIFO scheduler for Trainer jobs.")
    parser.add_argument("--data-dir", required=True)
    parser.add_argument("--model", choices=["cnn", "linear"], default="cnn")
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--learning-rate", type=float, default=1e-3)
    parser.add_argument("--image-size", type=int, default=64)
    parser.add_argument("--output-dir", default="../3. Trainer/outputs")
    parser.add_argument("--state-dir", default="scheduler_state")
    parser.add_argument("--runner", choices=["local", "docker"], default="local")
    parser.add_argument("--trainer-dir", default="../3. Trainer")
    parser.add_argument("--docker-image", default="pytorch/pytorch:2.5.1-cuda12.4-cudnn9-runtime")
    parser.add_argument("--no-cpu-fallback", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    trainer_dir = Path(args.trainer_dir).resolve()
    if args.runner == "docker":
        runner = DockerTrainerRunner(image=args.docker_image, trainer_dir=trainer_dir)
    else:
        runner = LocalTrainerRunner(trainer_dir=trainer_dir)

    scheduler = FifoScheduler(
        runner=runner,
        state_dir=args.state_dir,
        allow_cpu_fallback=not args.no_cpu_fallback,
    )
    job = TrainingJob(
        data_dir=args.data_dir,
        model=args.model,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        image_size=args.image_size,
        output_dir=args.output_dir,
    )
    job_id = scheduler.submit(job)
    print(f"submitted job: {job_id}", flush=True)
    scheduler.run_until_empty()
    print(f"finished job: {job_id}", flush=True)


if __name__ == "__main__":
    main()
