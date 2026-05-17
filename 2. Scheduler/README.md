# Scheduler

GPU 자원과 Docker 컨테이너를 관리하는 파트입니다. Input에서 들어온 학습 요청을 FIFO 큐에 넣고, 사용 가능한 GPU를 선택한 뒤 Trainer를 실행합니다.

## 담당 기능

- FIFO 기반 GPU 스케줄링
- Docker 컨테이너 생성
- GPU 자원 할당
- 작업 큐 관리
- 작업 상태를 JSON 파일로 저장

## 폴더 구조

```txt
2. Scheduler/
├─ scheduler/
│  ├─ __init__.py
│  ├─ cli.py
│  ├─ fifo_scheduler.py
│  ├─ gpu.py
│  ├─ job.py
│  └─ runner.py
├─ requirements.txt
└─ README.md
```

## 실행 방식

Scheduler는 두 가지 실행 모드를 지원합니다.

| 모드 | 설명 |
| --- | --- |
| `local` | 현재 PC에서 Trainer를 바로 실행합니다. 개발/검증용입니다. |
| `docker` | Docker 컨테이너를 생성해 Trainer를 실행합니다. 실제 클라우드 실행 구조에 가깝습니다. |

## Local 실행 예시

```powershell
cd "2. Scheduler"
python -m scheduler.cli `
  --runner local `
  --data-dir "C:\path\to\dataset" `
  --model cnn `
  --epochs 5
```

## Docker 실행 예시

```powershell
cd "2. Scheduler"
python -m scheduler.cli `
  --runner docker `
  --data-dir "C:\path\to\dataset" `
  --model cnn `
  --epochs 5 `
  --docker-image "pytorch/pytorch:2.5.1-cuda12.4-cudnn9-runtime"
```

Docker 모드에서는 다음 방식으로 컨테이너가 실행됩니다.

- dataset 폴더: `/app/dataset`에 read-only mount
- Trainer 코드: `/app/trainer`에 read-only mount
- 결과 폴더: `/app/outputs`에 mount
- GPU가 있으면 `--gpus device=<gpu_id>` 옵션 사용

## GPU 선택 기준

`nvidia-smi`를 사용해 GPU 상태를 조회합니다.

- GPU utilization이 80% 이하
- GPU memory 사용률이 90% 이하
- 조건을 만족하는 GPU 중 utilization이 가장 낮은 GPU 선택

개발 PC에 GPU 또는 `nvidia-smi`가 없으면 기본적으로 CPU fallback을 허용합니다. GPU가 반드시 필요하면 `--no-cpu-fallback` 옵션을 사용합니다.

## 상태 파일

Scheduler는 `scheduler_state` 폴더에 작업 상태를 저장합니다.

| 파일 | 설명 |
| --- | --- |
| `queue.json` | 전체 큐와 작업 목록 |
| `<job_id>.json` | 개별 작업 상태 |

작업 상태는 `queued`, `running`, `completed`, `failed` 중 하나입니다.

## Trainer 연동

Scheduler는 Trainer CLI를 다음 형식으로 호출합니다.

```powershell
python -m trainer.train `
  --data-dir "<dataset>" `
  --model "<cnn|linear>" `
  --epochs "<epoch>" `
  --batch-size "<batch-size>" `
  --learning-rate "<learning-rate>" `
  --image-size "<image-size>" `
  --output-dir "<output-dir>"
```

Trainer가 생성하는 `status.json`, `metrics.csv`, `history.json`, `best_model.pt`, `final_model.pt`는 Dashboard가 읽어서 화면에 표시할 수 있습니다.
