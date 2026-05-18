from __future__ import annotations

import argparse
import csv
import json
import random
import time
from dataclasses import asdict, dataclass
from pathlib import Path

import torch
from torch import nn, optim
from torch.utils.data import DataLoader, random_split
from torchvision import datasets, transforms

try:
    from .models import build_model
except ImportError:
    from models import build_model


@dataclass
class EpochMetric:
    epoch: int
    train_loss: float
    train_accuracy: float
    val_loss: float
    val_accuracy: float
    elapsed_sec: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train CNN or Linear model for uploaded image datasets.")
    parser.add_argument("--data-dir", required=True, help="ImageFolder dataset path. Use class-name subdirectories.")
    parser.add_argument("--model", choices=["cnn", "linear"], default="cnn")
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--learning-rate", type=float, default=1e-3)
    parser.add_argument("--image-size", type=int, default=64)
    parser.add_argument("--val-ratio", type=float, default=0.2)
    parser.add_argument("--output-dir", default="outputs")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--num-workers", type=int, default=0)
    return parser.parse_args()


def set_seed(seed: int) -> None:
    random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def build_dataloaders(args: argparse.Namespace) -> tuple[DataLoader, DataLoader, list[str]]:
    transform = transforms.Compose(
        [
            transforms.Resize((args.image_size, args.image_size)),
            transforms.ToTensor(),
            transforms.Normalize(mean=(0.5, 0.5, 0.5), std=(0.5, 0.5, 0.5)),
        ]
    )
    dataset = datasets.ImageFolder(args.data_dir, transform=transform)
    if len(dataset.classes) < 2:
        raise ValueError("Dataset must contain at least two class folders.")

    val_size = max(1, int(len(dataset) * args.val_ratio))
    train_size = len(dataset) - val_size
    if train_size < 1:
        raise ValueError("Dataset is too small to split into train and validation sets.")

    generator = torch.Generator().manual_seed(args.seed)
    train_dataset, val_dataset = random_split(dataset, [train_size, val_size], generator=generator)
    train_loader = DataLoader(
        train_dataset,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=args.num_workers,
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=args.num_workers,
    )
    return train_loader, val_loader, dataset.classes


def run_epoch(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    device: torch.device,
    optimizer: optim.Optimizer | None = None,
) -> tuple[float, float]:
    is_train = optimizer is not None
    model.train(is_train)

    total_loss = 0.0
    correct = 0
    total = 0

    for images, labels in loader:
        images = images.to(device)
        labels = labels.to(device)

        if is_train:
            optimizer.zero_grad()

        with torch.set_grad_enabled(is_train):
            logits = model(images)
            loss = criterion(logits, labels)
            if is_train:
                loss.backward()
                optimizer.step()

        batch_size = labels.size(0)
        total_loss += loss.item() * batch_size
        correct += (logits.argmax(dim=1) == labels).sum().item()
        total += batch_size

    return total_loss / total, correct / total


def write_status(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def save_metrics_csv(path: Path, history: list[EpochMetric]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(asdict(history[0]).keys()))
        writer.writeheader()
        for metric in history:
            writer.writerow(asdict(metric))


def train(args: argparse.Namespace) -> dict:
    set_seed(args.seed)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    status_path = output_dir / "status.json"
    write_status(status_path, {"state": "loading_dataset", "model": args.model})

    train_loader, val_loader, class_names = build_dataloaders(args)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = build_model(args.model, num_classes=len(class_names), image_size=args.image_size).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=args.learning_rate)

    best_val_accuracy = 0.0
    history: list[EpochMetric] = []
    started_at = time.time()

    write_status(
        status_path,
        {
            "state": "training",
            "model": args.model,
            "device": str(device),
            "classes": class_names,
            "epochs": args.epochs,
        },
    )

    for epoch in range(1, args.epochs + 1):
        epoch_started_at = time.time()
        train_loss, train_accuracy = run_epoch(model, train_loader, criterion, device, optimizer)
        val_loss, val_accuracy = run_epoch(model, val_loader, criterion, device)
        metric = EpochMetric(
            epoch=epoch,
            train_loss=round(train_loss, 6),
            train_accuracy=round(train_accuracy, 6),
            val_loss=round(val_loss, 6),
            val_accuracy=round(val_accuracy, 6),
            elapsed_sec=round(time.time() - epoch_started_at, 3),
        )
        history.append(metric)

        if val_accuracy >= best_val_accuracy:
            best_val_accuracy = val_accuracy
            torch.save(model.state_dict(), output_dir / "best_model.pt")

        status = {
            "state": "training",
            "epoch": epoch,
            "epochs": args.epochs,
            "latest": asdict(metric),
            "best_val_accuracy": round(best_val_accuracy, 6),
        }
        write_status(status_path, status)
        print(json.dumps(status, ensure_ascii=False), flush=True)

    torch.save(model.state_dict(), output_dir / "final_model.pt")
    save_metrics_csv(output_dir / "metrics.csv", history)
    (output_dir / "history.json").write_text(
        json.dumps([asdict(metric) for metric in history], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (output_dir / "classes.json").write_text(json.dumps(class_names, ensure_ascii=False, indent=2), encoding="utf-8")

    result = {
        "state": "completed",
        "model": args.model,
        "device": str(device),
        "classes": class_names,
        "epochs": args.epochs,
        "best_val_accuracy": round(best_val_accuracy, 6),
        "elapsed_sec": round(time.time() - started_at, 3),
        "artifacts": {
            "best_weights": str(output_dir / "best_model.pt"),
            "final_weights": str(output_dir / "final_model.pt"),
            "metrics_csv": str(output_dir / "metrics.csv"),
            "history_json": str(output_dir / "history.json"),
            "status_json": str(status_path),
        },
    }
    write_status(status_path, result)
    return result


def main() -> None:
    args = parse_args()
    try:
        result = train(args)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as exc:
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        write_status(output_dir / "status.json", {"state": "failed", "error": str(exc)})
        raise


if __name__ == "__main__":
    main()

