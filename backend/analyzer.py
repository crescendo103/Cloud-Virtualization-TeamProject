from __future__ import annotations

import json
import os
import time
from pathlib import Path

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

SYSTEM_PROMPT = """당신은 딥러닝 학습 결과를 분석하는 전문가다.
주어진 작업 설정, Epoch별 학습 기록, GPU 상태를 보고 다음을 한국어로 간결하게 분석하라.

1. 수렴 여부와 과적합 징후 (train/val loss 곡선 비교)
2. 하이퍼파라미터(learning rate, epochs, batch size) 적정성과 조정 제안
3. best epoch과 마지막 epoch의 차이가 의미하는 것
4. GPU/CPU 자원 활용 관점의 코멘트

규칙:
- 항목별로 2~3문장 이내로 짧게 작성한다.
- 수치를 근거로 들어 설명한다.
- 근거 없는 단정은 피하고, 데이터가 부족하면 부족하다고 말한다.
- 마크다운 헤더 없이 번호 목록으로만 작성한다."""


class TrainingAnalyzer:
    def __init__(self, model: str = "gpt-4o-mini") -> None:
        self.model = model
        self._client = None

    def analyze_job(self, job: dict, output_dir: Path, gpu: dict) -> dict:
        history = job.get("trainer_history") or []
        if not history:
            return {
                "available": False,
                "cached": False,
                "analysis": None,
                "message": "분석할 학습 기록이 아직 없습니다.",
            }

        cache_path = output_dir / "analysis.json"
        cached = self._read_cache(cache_path)
        if cached and cached.get("analyzed_epochs") == len(history):
            return {
                "available": True,
                "cached": True,
                "analysis": cached.get("analysis"),
                "message": "ok",
            }

        client = self._get_client()
        if client is None:
            return {
                "available": False,
                "cached": False,
                "analysis": None,
                "message": "OPENAI_API_KEY가 설정되지 않아 AI 분석을 사용할 수 없습니다.",
            }

        payload = {
            "job_config": {
                key: job.get(key)
                for key in ("job_id", "model", "epochs", "batch_size", "learning_rate", "image_size", "status", "gpu_id")
            },
            "epoch_history": history,
            "trainer_status": job.get("trainer_status"),
            "gpu_status": gpu,
        }

        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
                ],
                max_tokens=800,
                temperature=0.4,
            )
        except Exception as exc:
            return {
                "available": False,
                "cached": False,
                "analysis": None,
                "message": f"AI 분석 호출에 실패했습니다: {exc}",
            }

        analysis = response.choices[0].message.content
        output_dir.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(
            json.dumps(
                {"analyzed_epochs": len(history), "analysis": analysis, "created_at": time.time()},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        return {"available": True, "cached": False, "analysis": analysis, "message": "ok"}

    def _get_client(self):
        if OpenAI is None or not os.environ.get("OPENAI_API_KEY"):
            return None
        if self._client is None:
            self._client = OpenAI()
        return self._client

    @staticmethod
    def _read_cache(path: Path) -> dict | None:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            return None
