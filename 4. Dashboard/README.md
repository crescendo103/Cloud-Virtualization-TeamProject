# Dashboard - 정유찬

학습 작업의 진행 상태와 GPU 상태를 보여주는 웹 화면입니다.

## 기능

- 작업 큐 목록 표시
- 작업별 상태 표시: `queued`, `running`, `completed`, `failed`
- Trainer가 생성한 `status.json` 기반 학습 결과 표시
- GPU 사용률 표시
- 최근 요청량 기반 다음 요청 수 예측 표시

## 실행 위치

FastAPI 서버 실행 후 브라우저에서 접속합니다.

```txt
http://127.0.0.1:8000/dashboard/
```

Dashboard는 2초마다 다음 API를 호출합니다.

- `GET /api/jobs`
- `GET /api/jobs/{job_id}`
- `GET /api/gpu`
- `GET /api/predict`
