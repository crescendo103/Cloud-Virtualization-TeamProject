# Trainer - 김승겸

AI 모델 학습을 담당하는 파트입니다. Input 파트에서 전달한 데이터셋, 모델 종류, epoch 값을 받아 학습을 실행하고, Scheduler/Dashboard가 사용할 수 있는 산출물을 저장합니다.

## 담당 기능

- CNN 모델 학습
- Linear 모델 학습
- 학습된 weight 저장
- epoch별 loss / accuracy 기록
- 현재 학습 상태를 `status.json`으로 출력

## 폴더 구조

```txt
3. Trainer/
├─ trainer/
│  ├─ __init__.py
│  ├─ models.py
│  └─ train.py
├─ outputs/
├─ requirements.txt
└─ README.md
```

## 입력 데이터 형식

`torchvision.datasets.ImageFolder` 형식을 사용합니다. 클래스 이름별 폴더 아래 이미지 파일을 넣으면 됩니다.

```txt
dataset/
├─ class_a/
│  ├─ image1.png
│  └─ image2.png
└─ class_b/
   ├─ image1.png
   └─ image2.png
```

## 실행 방법

```powershell
cd "3. Trainer"
pip install -r requirements.txt
python -m trainer.train --data-dir "C:\path\to\dataset" --model cnn --epochs 5 --output-dir outputs
```

Linear 모델을 사용할 때는 `--model linear`로 실행합니다.

```powershell
python -m trainer.train --data-dir "C:\path\to\dataset" --model linear --epochs 5 --output-dir outputs
```

## 주요 옵션

| 옵션 | 설명 | 기본값 |
| --- | --- | --- |
| `--data-dir` | 학습 데이터셋 경로 | 필수 |
| `--model` | `cnn` 또는 `linear` | `cnn` |
| `--epochs` | 학습 epoch 수 | `5` |
| `--batch-size` | batch 크기 | `32` |
| `--learning-rate` | learning rate | `0.001` |
| `--image-size` | 입력 이미지 크기 | `64` |
| `--val-ratio` | validation 비율 | `0.2` |
| `--output-dir` | 결과 저장 폴더 | `outputs` |

## 출력 산출물

학습이 완료되면 `--output-dir` 아래에 다음 파일이 생성됩니다.

| 파일 | 설명 |
| --- | --- |
| `best_model.pt` | validation accuracy가 가장 높았던 weight |
| `final_model.pt` | 마지막 epoch의 weight |
| `metrics.csv` | epoch별 train/validation loss와 accuracy |
| `history.json` | dashboard 연동용 학습 기록 |
| `classes.json` | 클래스 이름 목록 |
| `status.json` | 현재 학습 상태 또는 최종 결과 |

## Scheduler 연동 예시

Scheduler가 Docker 컨테이너를 실행할 때 다음처럼 명령을 전달하면 됩니다.

```powershell
python -m trainer.train `
  --data-dir "/app/dataset" `
  --model cnn `
  --epochs 10 `
  --batch-size 32 `
  --output-dir "/app/outputs/job-001"
```

Dashboard는 `status.json`을 주기적으로 읽거나, 표준 출력으로 찍히는 JSON 로그를 수집해서 진행률을 표시할 수 있습니다.
