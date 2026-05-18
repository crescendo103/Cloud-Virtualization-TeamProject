# Docker / CUDA 실행 세팅

## 전제 조건

- Docker Desktop 실행
- WSL2 기반 Linux engine 사용
- NVIDIA GPU 드라이버 설치
- Docker에서 GPU 사용 가능

## GPU 컨테이너 확인

```powershell
.\scripts\check_docker_gpu.ps1
```

마지막 명령에서 컨테이너 내부 `nvidia-smi`가 출력되면 CUDA 컨테이너 실행 준비가 된 상태입니다.

## 서버 실행

```powershell
docker compose up --build
```

브라우저에서 접속합니다.

```txt
http://127.0.0.1:8010/input/
http://127.0.0.1:8010/dashboard/
```

## 데이터와 결과 저장

Compose 실행 시 다음 폴더가 컨테이너와 공유됩니다.

| Host | Container | 용도 |
| --- | --- | --- |
| `./data` | `/app/data` | 업로드 데이터 |
| `./3. Trainer/outputs` | `/app/3. Trainer/outputs` | 학습 결과 |
| `./2. Scheduler/scheduler_state` | `/app/2. Scheduler/scheduler_state` | 큐 상태 |

## 문제가 생길 때

`docker info`에서 Linux engine 연결 오류가 나면 Docker Desktop이 꺼져 있거나 아직 시작 중입니다.

`docker run --gpus all ... nvidia-smi`가 실패하면 Docker Desktop 설정에서 WSL2 engine을 켜고, NVIDIA 드라이버가 WSL GPU 연동을 지원하는 버전인지 확인해야 합니다.
