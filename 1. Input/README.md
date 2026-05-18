# Input - 김동주

사용자가 학습 요청을 입력하는 웹 화면입니다.

## 기능

- dataset ZIP 업로드
- 모델 선택: `CNN` 또는 `Linear`
- epoch, batch size, learning rate, image size 설정
- FastAPI 백엔드의 `/api/jobs`로 학습 요청 전송
- 요청 후 Dashboard로 이동

## 실행 위치

FastAPI 서버 실행 후 브라우저에서 접속합니다.

```txt
http://127.0.0.1:8000/input/
```

업로드 ZIP은 다음처럼 클래스별 폴더 구조를 가져야 합니다.

```txt
dataset.zip
├─ class_a/
│  ├─ image1.png
│  └─ image2.png
└─ class_b/
   ├─ image1.png
   └─ image2.png
```
