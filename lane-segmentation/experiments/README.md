# 실험 결과

## Kaggle 실제 데이터 전처리

- 아카이브: `lanesegmentationchallenge.zip` (1,292,489,382 bytes)
- train/validation: 3,216 / 410 images, 날짜 그룹 단위 split
- 그룹: `0313` 2,858장, `0531` 358장, `0601` 410장; seed 42 holdout은 `0601`
- test: 2,782 images
- 원본 image/mask: 1280×720 JPEG, 파일명·크기 일치
- grayscale mask 고유값: 0-8, 247-255; foreground 기준 `>127`, 전체 픽셀의 4.28%
- 전처리 결과 전체: `data/processed/dataset_report.json`

## 실제 데이터 smoke test

8 train / 8 validation image, 128×256 입력, 1 epoch, batch size 1로 CUDA 학습을 수행했다. Best checkpoint 저장 후 다시 로드해 validation 평가와 4-panel 시각화를 실행했다. 학습 손실 0.62639, validation 손실 0.63533이었고 Dice는 0.0이다. 이는 단일 epoch의 파이프라인 smoke test이며 baseline 성능으로 취급하지 않는다. 모든 출력 checkpoint 및 이미지 파일은 로컬에서 Git 제외 상태다.

## U-Net + BCE baseline

- 설정: `configs/baseline.yaml`; 입력 288×512, batch 2, AdamW lr 0.001, weight decay 0.0001, seed 42, 최대 12 epochs, early-stopping patience 4
- 실행 데이터: train 3,216 / validation 410, validation group `0601`
- GPU: RTX 4060 Laptop GPU, PyTorch 2.11.0+cu128
- 학습 시간: 약 21.2분
- Early stopping: epoch 7; best validation BCE checkpoint: epoch 3, BCE 0.08538
- checkpoint의 threshold 0.5 결과: mean image Dice 0.68558, pixel Dice 0.68366, IoU 0.51936, precision 0.82400, recall 0.58416
- 같은 validation group에서 threshold candidates 0.25-0.75를 비교해 0.35를 선택했다. 이 선택 threshold의 mean image Dice는 0.71535, pixel Dice 0.71309, IoU 0.55411, precision 0.74471, recall 0.68405다. Threshold 선택과 성능 보고가 같은 validation을 사용했으므로 이 값은 독립 평가가 아니며, test/generalization score를 뜻하지 않는다.
- 학습 epoch 6의 Dice 0.69826은 로그에만 있으며, checkpoint 선택 기준은 validation BCE이므로 best checkpoint epoch 3과 혼동하지 않는다.
- Loss curve: `results/figures/kaggle-unet-bce-loss.png`
- 전체 validation 지표, threshold sweep, 이미지별 점수와 best/failure 시각화: `results/predictions/kaggle-unet-bce/`
- 실제 Kaggle 제출/점수: 수행하지 않음. 과거 Public Score `0.69166`과 직접 비교할 수 없다.

재현 명령:

```powershell
python -m lane_segmentation.prepare_data --archive data/lanesegmentationchallenge.zip --data-root data/raw/lanesegmentationchallenge --processed-root data/processed --seed 42
python -m lane_segmentation.train --config configs/baseline.yaml
python -m lane_segmentation.evaluate --config configs/baseline.yaml --checkpoint experiments/kaggle-unet-bce/best.pt --output-dir results/predictions/kaggle-unet-bce
```

설정, epoch 로그, checkpoint는 실험별 하위 폴더에 생성되며 Git에서 제외된다. 모델 비교는 동일한 날짜 그룹 split과 seed를 유지한다.
