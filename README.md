# Cloud Virtualization Team Project

## 프로젝트 소개

사용자가 AI 모델과 데이터셋을 업로드하면  
GPU 자원을 동적으로 할당하여 학습을 수행하는  
클라우드 기반 AI 학습 시스템입니다.

각자 맡을 역할을 제목 옆에 추가해주세요
ex) 1. Input - 김동주

---

# 역할 분담

## 1. Input - 김동주

사용자로부터 입력을 받는 영역입니다.

### 담당 기능
- dataset 파일 업로드
- 모델 선택 (CNN / Linear)
- epoch 설정
- FastAPI 요청 전송

---

## 2. Scheduler - 박준영

GPU 자원과 Docker 컨테이너를 관리하는 영역입니다.

### 담당 기능
- FIFO 기반 GPU 스케줄링
- Docker 컨테이너 생성
- GPU 자원 할당
- 작업 큐 관리

---

## 3. Trainer - 김승겸 

AI 모델 학습을 담당하는 영역입니다.

### 담당 기능
- CNN 모델 학습
- Linear 모델 학습
- weights 저장
- loss / accuracy 기록

---

## 4. Dashboard - 정유찬

사용자에게 현재 상태를 출력하는 영역입니다.

### 담당 기능
- 실행 시간 표시
- GPU 사용률 표시 (SVG 막대 차트)
- 학습 진행 상태 출력
- Epoch별 Loss / Accuracy 그래프 시각화

### 시각화 상세

외부 CDN 없이 동작하는 SVG 기반 그래프로 학습 결과를 표시합니다.

- **Loss 차트**: 선택한 작업의 Epoch별 Train/Validation Loss 라인 차트
- **Accuracy 차트**: Epoch별 Train/Validation Accuracy 라인 차트
- **GPU 차트**: GPU 장치별 사용률(%)과 메모리 사용률(%) 막대 차트
- 2초 폴링 주기에 맞춰 학습 중에도 그래프가 실시간으로 갱신됩니다
- 데이터가 없으면 "학습 기록이 없습니다" / "GPU가 없습니다 (CPU fallback)" 안내를 표시합니다

이를 위해 Trainer가 `history.json`을 학습 종료 시점이 아닌 **매 Epoch마다 갱신**하도록 변경했고,
백엔드 `GET /api/jobs/{job_id}` 응답에 `trainer_history`(Epoch별 지표 배열)를 추가했습니다.

---

# 프로젝트 구조

```txt
1. Input
2. Scheduler
3. Trainer
4. Dashboard
```

# 시스템 흐름

Client Input
->
FastAPI
->
GPU Scheduler
->
Docker Container
->
AI Training
->
Dashboard Output

---

# 실행 방법

## 1. 의존성 설치

```powershell
pip install -r requirements.txt
```

## 2. 서버 실행

```powershell
uvicorn backend.main:app --reload
```

실행 후 브라우저에서 접속합니다.

```txt
http://127.0.0.1:8000/input/
http://127.0.0.1:8000/dashboard/
```

## 3. Dataset ZIP 형식

업로드할 ZIP 파일은 클래스별 폴더를 포함해야 합니다.

```txt
dataset.zip
├─ class_a/
│  ├─ image1.png
│  └─ image2.png
└─ class_b/
   ├─ image1.png
   └─ image2.png
```

## 구현된 전체 구조

```txt
backend/
├─ main.py
├─ job_service.py
├─ gpu_monitor.py
├─ predictor.py
├─ docker_manager.py
└─ logs.json

1. Input/
├─ index.html
├─ styles.css
└─ app.js

2. Scheduler/
└─ scheduler/
   ├─ cli.py
   ├─ fifo_scheduler.py
   ├─ gpu.py
   ├─ job.py
   └─ runner.py

3. Trainer/
└─ trainer/
   ├─ train.py
   └─ models.py

4. Dashboard/
├─ index.html
├─ styles.css
└─ app.js
```

## 현재 실행 방식

기본 서버는 개발 환경에서 바로 검증할 수 있도록 `local` runner로 Trainer를 실행합니다.  
Scheduler에는 Docker runner도 구현되어 있어 Docker와 CUDA 환경이 준비된 PC에서는 컨테이너 실행 구조로 확장할 수 있습니다.

## Docker로 바로 실행

Docker Desktop 또는 Docker Engine만 설치되어 있으면 CPU 모드로 실행할 수 있습니다.

```bash
git clone https://github.com/crescendo103/Cloud-Virtualization-TeamProject.git
cd Cloud-Virtualization-TeamProject
cp .env.example .env
docker compose up --build
```

AI 분석 기능을 사용하려면 `.env`에 본인의 OpenAI API 키를 입력합니다.

```env
OPENAI_API_KEY=your-api-key
```

키가 비어 있어도 데이터 업로드, 학습, 차트 및 대시보드는 정상 동작하며 AI 분석 기능만 비활성화됩니다. `.env`는 Git에 포함되지 않습니다.

실행 후 접속 주소는 다음과 같습니다.

```txt
http://127.0.0.1:8010/input/
http://127.0.0.1:8010/dashboard/
```

종료할 때는 다음 명령을 사용합니다.

```bash
docker compose down
```

## NVIDIA GPU로 실행

NVIDIA 드라이버와 NVIDIA Container Toolkit이 준비된 Windows/WSL2 또는 Linux에서는 GPU override를 함께 사용합니다.

```powershell
.\scripts\check_docker_gpu.ps1
docker compose -f docker-compose.yml -f docker-compose.gpu.yml up --build
```

세부 환경 준비 방법은 [DOCKER.md](./DOCKER.md)에 정리되어 있습니다.
