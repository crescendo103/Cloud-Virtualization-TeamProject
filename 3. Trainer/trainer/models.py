from __future__ import annotations

import torch
from torch import nn


class LinearClassifier(nn.Module):
    def __init__(self, num_classes: int, image_size: int = 28) -> None:
        super().__init__()
        input_features = 3 * image_size * image_size
        self.net = nn.Sequential(
            nn.Flatten(),
            nn.Linear(input_features, 256),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(256, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class CNNClassifier(nn.Module):
    def __init__(self, num_classes: int) -> None:
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d((1, 1)),
        )
        self.classifier = nn.Linear(128, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.features(x)
        return self.classifier(torch.flatten(x, 1))


def build_model(model_name: str, num_classes: int, image_size: int) -> nn.Module:
    normalized_name = model_name.lower()
    if normalized_name == "cnn":
        return CNNClassifier(num_classes=num_classes)
    if normalized_name == "linear":
        return LinearClassifier(num_classes=num_classes, image_size=image_size)
    raise ValueError(f"Unsupported model '{model_name}'. Use 'cnn' or 'linear'.")

