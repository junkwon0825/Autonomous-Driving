# Lane Segmentation Challenge 재현 프로젝트

## 프로젝트 배경

학부 자동차 인공지능 수업에서 딥러닝과 차선 분할을 처음 경험했고, Coursera 학습 이후 Kaggle `Lane Segmentation Challenge`에 참가했다. 당시 기록한 Public Score `0.69166`은 과거 대회 결과이며, 이번 구현의 성능으로 간주하지 않는다.

이번 프로젝트는 같은 대회의 실제 학습 이미지와 차선 mask로 PyTorch U-Net을 재학습하고, 고정된 주행 그룹 validation에서 정량·정성 평가를 재현하는 작업이다. 검증 점수와 Kaggle 제출 점수는 다른 지표이며, 종료된 대회에서 새 점수를 얻었다고 가정하지 않는다.

## 대회와 데이터

- 대회: [Lane Segmentation Challenge](https://www.kaggle.com/competitions/lanesegmentationchallenge)
- 사용 파일: `data/lanesegmentationchallenge.zip` (로컬 전용, Git 제외)
- ZIP에는 train RGB 이미지 3,626장, `lane-masks` 3,626장, test 이미지 2,782장, `sample_submission.csv`가 들어 있다.
- 원본 이미지와 mask는 1280×720 JPEG다. Mask가 JPEG로 압축되어 픽셀값이 완전한 0/255가 아니므로, grayscale 값 `>127`을 차선으로 이진화한다. 전처리 시 전체 mask 픽셀값과 foreground 비율을 `data/processed/dataset_report.json`에 기록한다.
- 파일명에서 날짜 그룹을 추출한다. `0313-1`과 `0313-2`는 모두 `0313` 그룹으로 묶어 동일 날짜의 인접 시퀀스가 train/validation에 나뉘지 않게 한다. 실제 분할은 seed 42로 `0601` 410장을 validation으로 선택하고, 나머지 3,216장을 train에 둔다. 전체 mask에서 grayscale 값은 0-8 및 247-255이고, `>127` 기준 lane foreground는 4.28%다. 그룹 수가 적어 validation은 주행 전체 분포를 대표하지 않을 수 있다.
- Kaggle 설명의 평가는 이미지별 Dice 평균이다. 코드에서는 이를 `mean_image_dice`로 기록하고 pixel-global Dice/IoU와 구분한다.

Kaggle 대회는 2025-06-22 종료되었고 페이지에서 초대 제한 상태를 확인했다. 따라서 제출 파일을 만들 수는 있어도, 새 Kaggle 제출/점수가 등록된다고 보장할 수 없다. 과거 제출 CSV는 test 이미지의 과거 예측일 뿐 정답이 아니므로 점수 재계산에 쓰지 않는다.

## 모델과 실험

- 입력 RGB, 기본 크기 288×512
- U-Net encoder 채널 `32-64-128-256-512`, skip connection, 1채널 logits 출력
- Loss `BCEWithLogitsLoss`, optimizer AdamW
- 학습 이미지 bilinear resize, mask nearest-neighbor resize 및 `>127` 이진화
- 날짜 그룹 holdout, 고정 seed, validation loss 기준 best checkpoint 및 early stopping
- 지표: validation BCE, 이미지별 평균 Dice, pixel Dice/IoU, precision, recall
- 제출 생성은 sample submission의 순서와 헤더를 보존한다. 과거 제출 형식인 `filename,rle`도 지원한다.

기존 제출 CSV를 test 이미지에 overlay해 확인한 결과, 차선이 이미지에 정렬되는 RLE 해석은 C-order, 1-based였다. 이는 과거 CSV의 시각적 검증이며 공식 evaluator 코드로 독립 확인한 것은 아니다. 실제 제출 가능 여부와 점수는 Kaggle에서 별도로 확인한다.

## 환경 설정

Windows PowerShell에서 프로젝트 폴더에서 실행한다. 기존 `.venv`와 CUDA PyTorch 환경을 유지한다.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -e .
```

현재 개발 환경은 Python 3.12, PyTorch 2.11.0+cu128, RTX 4060 Laptop GPU다. 설치 후 확인:

```powershell
python -c "import torch; print(torch.__version__, torch.cuda.is_available(), torch.version.cuda); print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU')"
```

## 데이터 준비 및 학습

ZIP을 `data/raw/`에 안전하게 풀고, 이미지-mask 이름·크기·열림 여부, mask 값 분포, sequence 그룹 분할을 검사한다. Train/validation manifest와 8장씩의 실제 데이터 smoke manifest를 생성한다.

```powershell
python -m lane_segmentation.prepare_data `
  --archive data/lanesegmentationchallenge.zip `
  --data-root data/raw/lanesegmentationchallenge `
  --processed-root data/processed `
  --seed 42
```

소규모 실제 데이터 GPU 학습, checkpoint 저장 확인:

```powershell
python -m lane_segmentation.train --config configs/smoke.yaml
```

Baseline 전체 train split 학습, validation 평가 및 시각화 생성:

```powershell
python -m lane_segmentation.train --config configs/baseline.yaml
python -m lane_segmentation.evaluate `
  --config configs/baseline.yaml `
  --checkpoint experiments/kaggle-unet-bce/best.pt `
  --output-dir results/predictions
```

대회 sample submission을 사용해 test 예측 CSV를 생성한다. 대회 template의 헤더와 행 순서를 그대로 유지한다.

```powershell
python -m lane_segmentation.submission `
  --config configs/baseline.yaml `
  --checkpoint experiments/kaggle-unet-bce/best.pt `
  --sample-submission data/raw/lanesegmentationchallenge/sample_submission.csv `
  --test-root data/raw/lanesegmentationchallenge/test/test/frames `
  --output data/submissions/submission_unet_bce.csv `
  --legacy-template data/submissions/submission.csv `
  --legacy-output data/submissions/submission_unet_bce_legacy.csv `
  --threshold 0.35 `
  --rle-order C `
  --index-base 1
```

위 명령은 이번 validation sweep에서 선택된 threshold `0.35`를 사용해 official sample 형식과 사용자의 과거 `filename,rle` 형식 두 가지를 같은 추론 결과로 생성한다. 다른 checkpoint/split을 사용하면 validation threshold sweep 결과로 값을 다시 지정한다. 두 파일은 official template과 과거 CSV의 파일명·행 순서가 일치할 때만 만들어진다. `data/submissions/submission.csv` 자체는 덮어쓰지 않는다. 대회가 종료 상태인 만큼 CSV 생성과 실제 제출/공식 점수는 별개다. 데이터, checkpoint, 인증 파일, 생성 CSV는 Git에 올리지 않는다.

## 검증 및 결과 기록

```powershell
python -m pytest -q
```

전체 BCE baseline은 7 epoch에서 early stopping 되었으며, 최소 validation BCE checkpoint는 epoch 3이다. Checkpoint의 validation BCE는 0.08538, threshold 0.5에서 이미지별 평균 Dice 0.68558 / pixel Dice 0.68366 / IoU 0.51936을 기록했다. 같은 validation group에서 threshold sweep으로 0.35를 선택하면 이미지별 평균 Dice 0.71535 / pixel Dice 0.71309 / IoU 0.55411이다. Threshold 선택과 보고에 같은 validation을 사용했으므로 선택 threshold 성능은 독립 test score가 아니다. 학습 epoch 6의 mean image Dice 0.69826은 별도 로그 수치이며, checkpoint가 epoch 3인 사실과 구분한다.

Loss curve는 [kaggle-unet-bce-loss.png](./results/figures/kaggle-unet-bce-loss.png), best/failure validation 시각화와 JSON/CSV 평가 결과는 [kaggle-unet-bce/](./results/predictions/kaggle-unet-bce/)에 저장한다. 실험 수치와 산출물 목록은 [experiments/README.md](./experiments/README.md)에 기록한다.

새 Kaggle 제출 또는 공식 점수는 확인하지 않았다. Validation Dice를 과거 Public Score `0.69166` 또는 공식 Kaggle 점수와 직접 비교하지 않는다. Baseline 이후 BCE/Dice, augmentation, TTA는 같은 split에서 각각 검증한 다음 비교한다.

## 프로젝트 구조

```text
configs/                 학습 및 실제 데이터 smoke 설정
data/                    데이터 안내 (원본 및 처리물은 Git 제외)
src/lane_segmentation/   Dataset, U-Net, 학습, 평가, 제출 생성
tests/                   데이터·모델·지표·제출 형식 테스트
experiments/             실험 기록 및 checkpoint (checkpoint Git 제외)
results/                 실제 평가 시각화 (결과물만 관리)
```

## 한계와 다음 단계

- 데이터셋이 날짜 그룹 4개뿐이므로 한 그룹 holdout validation의 표본과 조건 다양성이 제한적이다.
- 과거 제출 CSV는 test 정답을 포함하지 않으며, 과거 Public Score 자체를 재현하거나 그 CSV만으로 개선 점수를 계산할 수 없다.
- 종료된 대회의 late submission 가능 여부는 계정별 접근과 대회 설정에 따라 Kaggle에서 확인해야 한다. 실제 제출을 하지 않았다면 새 공식 점수를 보고하지 않는다.
- 우선 실제 데이터 smoke test와 BCE baseline을 실행하고, loss curve·validation 예측·실패 사례를 저장한다. 이후 BCE/Dice, augmentation, TTA를 동일한 validation split에서 비교한다.
- 실제 자율주행 적용 전에는 더 다양한 주행 조건, 장면 단위 검증, temporal consistency, 추론 지연 측정, 차량용 배포 검증이 필요하다.
