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

## 2. Scheduler - 

GPU 자원과 Docker 컨테이너를 관리하는 영역입니다.

### 담당 기능
- FIFO 기반 GPU 스케줄링
- Docker 컨테이너 생성
- GPU 자원 할당
- 작업 큐 관리

---

## 3. Trainer

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
