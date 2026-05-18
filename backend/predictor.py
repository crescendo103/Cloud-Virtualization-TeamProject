from __future__ import annotations

import json
import time
from collections import Counter
from pathlib import Path


class RequestPredictor:
    def __init__(self, log_path: str | Path, window_size: int = 5) -> None:
        self.log_path = Path(log_path)
        self.window_size = window_size
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.log_path.exists():
            self.log_path.write_text("[]", encoding="utf-8")

    def record_request(self) -> None:
        events = self._read_events()
        events.append({"timestamp": time.time()})
        self.log_path.write_text(json.dumps(events, ensure_ascii=False, indent=2), encoding="utf-8")

    def predict_next_request_count(self) -> dict:
        events = self._read_events()
        counts = self._hourly_counts(events)
        latest_counts = [count for _, count in counts[-self.window_size :]]
        predicted = round(sum(latest_counts) / len(latest_counts), 2) if latest_counts else 0.0
        return {
            "window_size": self.window_size,
            "recent_hourly_counts": latest_counts,
            "predicted_next_hour_requests": predicted,
        }

    def _read_events(self) -> list[dict]:
        try:
            return json.loads(self.log_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def _hourly_counts(self, events: list[dict]) -> list[tuple[int, int]]:
        counter: Counter[int] = Counter()
        for event in events:
            hour_bucket = int(event["timestamp"] // 3600)
            counter[hour_bucket] += 1
        return sorted(counter.items())

