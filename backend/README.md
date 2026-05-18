# Backend

FastAPI 기반 통합 서버입니다. Input 화면에서 들어온 요청을 받아 FIFO Scheduler에 등록하고, Trainer를 실행한 뒤 Dashboard에 상태 API를 제공합니다.

## 주요 파일

| 파일 | 역할 |
| --- | --- |
| `main.py` | FastAPI 라우팅과 정적 HTML 서빙 |
| `job_service.py` | 업로드 저장, FIFO 큐, Trainer 실행 |
| `gpu_monitor.py` | `nvidia-smi` 기반 GPU 상태 조회 |
| `predictor.py` | 최근 요청 수 기반 간단 예측 |
| `docker_manager.py` | Docker 실행 설정 |
| `logs.json` | 요청 시간 기록 |

## API

| Method | Path | 설명 |
| --- | --- | --- |
| `POST` | `/api/jobs` | dataset ZIP과 학습 옵션 제출 |
| `GET` | `/api/jobs` | 전체 작업 목록 |
| `GET` | `/api/jobs/{job_id}` | 특정 작업 상태 |
| `GET` | `/api/gpu` | GPU 상태 |
| `GET` | `/api/predict` | 다음 요청 수 예측 |

