# 데이터 파일 및 준비

사용 데이터는 Kaggle [Lane Segmentation Challenge](https://www.kaggle.com/competitions/lanesegmentationchallenge)의 로컬 아카이브 `data/lanesegmentationchallenge.zip`이다. 압축 파일에는 train RGB 이미지, `train/train/lane-masks/`의 대응 mask, test 이미지, `sample_submission.csv`가 포함되어 있다. 실제 해상도와 mask 픽셀 분포는 전처리 실행 결과 `data/processed/dataset_report.json`에서 확인한다.

ZIP은 Git에 포함하지 않는다. 아래 명령은 image-mask 파일명 및 해상도를 확인하고, 모든 학습 mask의 grayscale 픽셀값과 threshold 127 기준 foreground 비율을 계산한다. 파일명의 날짜 단위로 sequence를 묶어 고정 seed의 group holdout을 생성한다.

```powershell
python -m lane_segmentation.prepare_data `
  --archive data/lanesegmentationchallenge.zip `
  --data-root data/raw/lanesegmentationchallenge `
  --processed-root data/processed `
  --seed 42
```

산출 manifest:

- `data/processed/train.csv`
- `data/processed/val.csv`
- `data/processed/train_smoke.csv`
- `data/processed/val_smoke.csv`
- `data/processed/dataset_report.json`

원본 이미지·mask와 압축 파일, manifest, Kaggle 인증 파일, 생성 submission은 Git에서 제외한다. 과거 `data/submissions/submission.csv`는 사용자의 기존 결과물이므로 덮어쓰지 않는다.
