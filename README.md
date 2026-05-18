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
- GPU 사용률 표시
- 학습 진행 상태 출력
- 결과 시각화

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

## Docker / CUDA 실행

Docker 환경 실행 방법은 [DOCKER.md](/C:/Users/32210813/Documents/클가기/Cloud-Virtualization-TeamProject/DOCKER.md)에 정리되어 있습니다.

```powershell
.\scripts\check_docker_gpu.ps1
docker compose up --build
```

Docker 실행 시 접속 주소는 다음과 같습니다.

```txt
http://127.0.0.1:8010/input/
http://127.0.0.1:8010/dashboard/
```
