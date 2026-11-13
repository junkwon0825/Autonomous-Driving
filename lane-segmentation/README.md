# Lane Segmentation Challenge 재현 프로젝트

## 프로젝트 배경

학부 자동차 인공지능 수업에서 딥러닝과 차선 분할을 처음 경험하고, Coursera 학습 이후 Kaggle `Lane Segmentation Challenge`에 참가했다. 당시 기록한 Public Score `0.69166`은 과거 대회 결과이며, 현재 코드의 성능이나 새 실험 결과와 구분한다.

이번 구현은 같은 Kaggle 대회의 이진 차선 마스크 과제를 PyTorch로 재구성하고, 고정된 validation split에서 baseline과 개선 실험을 비교하는 것을 목표로 한다. 새 Kaggle 제출은 대회가 종료되어 가능한 것으로 간주하지 않는다.

## Kaggle 대회 및 데이터

대회: [Lane Segmentation Challenge](https://www.kaggle.com/competitions/lanesegmentationchallenge)

Kaggle 페이지에서 확인한 내용:

- 일정: 2025-05-15 시작, 2025-06-22 종료. 현재 페이지에 `Invitation required`가 표시되고 제한 참가 대회로 안내된다. 신규 참가와 늦은 제출이 열려 있다고 가정하지 않는다.
- 접근: Kaggle 로그인 후 규칙 동의가 필요하며, 참가자는 대회 주최자의 초대를 받아야 한다.
- 공개 데이터 설명: `train/images/`, `train/masks/`, `test/images/`, `sample_submission.csv`. RGB 원본은 720×1280, mask는 배경 0 / 차선 1로 설명되어 있다.
- 평가: test 이미지별 Dice를 계산하고 전체 이미지의 평균 Dice로 순위를 매긴다고 설명한다. 이는 전체 픽셀을 먼저 합산해 계산하는 pixel-global Dice와 다른 집계 방식이다.
- 제출: `filename,rle_mask` CSV, 테스트 이미지당 한 행, lane이 없으면 `0`. RLE의 flatten 순서 등 세부 구현은 실제 `sample_submission.csv`와 규칙을 확인한 뒤 구현한다.
- Data 탭에 표시된 라이선스는 MIT다. 공개 페이지는 로그인 전 상태이며 데이터 파일 목록과 개별 파일 크기는 공개하지 않는다. Data 탭에는 `sample_submission.csv` 85.98 kB가 표시되지만 미리보기는 규칙 동의 전 잠겨 있다.

실행 시점에는 브라우저에서 Kaggle 로그아웃 상태였고, `.kaggle/kaggle.json`, `KAGGLE_USERNAME`, `KAGGLE_KEY`도 없었다. 설치한 Kaggle CLI로 파일 목록을 요청했을 때 인증 오류가 반환됐다. 대회 페이지는 초대를 요구하므로, 데이터 다운로드와 실제 마스크 확인은 초대된 계정으로 로그인하고 규칙에 동의한 뒤 진행해야 한다. API 토큰을 코드나 저장소에 넣지 않는다.

## 현재 구현

### 모델과 학습

- PyTorch U-Net, encoder channels `32-64-128-256-512`, skip connection
- 입력 RGB, logits 출력, `BCEWithLogitsLoss`, AdamW
- seed 고정, best validation-loss checkpoint 저장, early stopping
- validation BCE, Dice/IoU/precision/recall, 예측 및 4-panel 시각화
- 지표에는 validation 샘플별 평균 Dice와 전체 픽셀 기준 Dice를 별도로 기록한다. 대회 설명의 평균 Dice와 비교할 때는 `mean_image_dice`를 사용한다.

원본 720×1280의 16:9 비율을 유지하기 위해 기본 입력 크기를 288×512로 설정했다. 이미지는 bilinear, mask는 nearest-neighbor로 축소하며, 실제 mask 픽셀값은 데이터 접근 후 다시 검사한다.

### 코드 구조

```text
lane-segmentation/
├── configs/baseline.yaml
├── data/README.md
├── src/lane_segmentation/
│   ├── data.py
│   ├── model.py
│   ├── metrics.py
│   ├── train.py
│   ├── inference.py
│   ├── evaluate.py
│   └── smoke_test.py
├── tests/
├── experiments/README.md
├── results/README.md
└── requirements.txt
```

학습 코드는 `#1.data`, `#2.model`, `#3.compile,train`, `#4.evaluate,predict` 흐름을 따른다. 현재 Dataset은 CSV manifest의 `image,mask` 쌍을 읽는다. 실제 Kaggle 파일의 이름·확장자·매칭 규칙·mask 값·분할을 확인한 뒤 manifest 생성/검증을 연결한다. 아직 Kaggle 데이터가 없어 데이터 구조에 대한 가정을 코드로 고정하지 않았다.

## 환경 설정

Windows PowerShell에서 프로젝트 폴더에서 실행한다. Python 3.11 또는 3.12와 기존 CUDA 12.8 PyTorch 2.11.0 환경을 사용한다.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -e .
python -m pip install kaggle
```

현재 개발 환경에서 PyTorch `2.11.0+cu128`가 RTX 4060 Laptop GPU에서 동작하는 것을 확인했다. 다른 PyTorch wheel로 덮어쓰지 말고 다음으로 CUDA 상태를 확인한다.

```powershell
python -c "import torch; print(torch.__version__, torch.cuda.is_available(), torch.version.cuda); print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU')"
```

## 데이터 접근 및 실행

1. [대회 페이지](https://www.kaggle.com/competitions/lanesegmentationchallenge)에 Kaggle 계정으로 로그인한다.
2. 대회 주최자에게 초대를 받아야 한다. 대회가 제한 참가 상태이므로 계정만으로 접근이 보장되지 않는다.
3. 초대를 받은 계정에서 Data 탭을 열고 대회 규칙에 동의한다.
4. Kaggle CLI 인증은 토큰을 직접 코드에 쓰지 않는 `kaggle auth login` OAuth 흐름을 권장한다. CLI 다운로드는 초대/규칙 동의가 된 뒤 실행한다.
5. 실제 파일 목록과 압축 구조를 확인한 후 `data/raw/`에 내려받고, 마스크 값·이미지 해상도·파일 매칭을 검증한다. 원본 데이터와 Kaggle 인증 파일은 Git에 추가하지 않는다.

CLI 인증 및 데이터 접근 확인:

```powershell
kaggle auth login
kaggle competitions files -c lanesegmentationchallenge
kaggle competitions download -c lanesegmentationchallenge -p data/raw
```

데이터가 준비되어 `configs/baseline.yaml`이 실제 manifest를 가리키도록 수정된 뒤:

```powershell
python -m pytest
python -m lane_segmentation.smoke_test
python -m lane_segmentation.train --config configs/baseline.yaml
python -m lane_segmentation.evaluate --config configs/baseline.yaml --checkpoint experiments/kaggle-unet-bce/best.pt
```

## 실험 계획

1. U-Net + BCE baseline
2. BCE/Dice combined loss
3. 같은 split에서 data augmentation 비교
4. validation 성능을 확인한 뒤 TTA 비교

대회 평가가 이미지별 평균 Dice인 점을 반영해 모든 실험에서 동일한 validation 이미지 목록과 `mean_image_dice`를 사용한다. validation threshold는 validation 데이터에서만 조정한다. 실제 점수나 개선 결과는 실행 후에만 기록한다.

## 검증 현황 및 한계

- 확인 완료: Python 3.12, PyTorch 2.11.0+cu128, RTX 4060 Laptop GPU.
- 현재 코드 검증: `python -m pytest -q` 6개 통과. 합성 이미지 2 train / 2 validation으로 1 epoch GPU smoke test, checkpoint 저장/재로딩, 시각화 생성도 통과했다. 이는 실행 경로 검증이며 Kaggle 데이터 성능이 아니다.
- Kaggle CLI 2.2.5의 파일 목록 조회는 API 인증정보 부재로 실패했다. 실제 Data 파일 목록과 개별 용량은 초대 계정으로 로그인하고 규칙에 동의한 뒤 확인해야 한다.
- 현재 미완료: 제한 대회 초대, Kaggle 로그인/OAuth, 규칙 동의, 데이터 다운로드, 실제 파일/라벨 검사, 실제 학습과 validation, 제출 RLE 검증.
- Kaggle 대회는 2025-06-22 종료되었다. 페이지에는 현재 초대 제한이 표시되며, 늦은 제출을 사용할 수 있다는 표시를 확인하지 못했다. 새 공식 점수는 보고하지 않는다.
- 실패 사례, loss curve, 실험별 성능 표는 실제 데이터 평가가 끝난 뒤 추가한다.

학부 시절의 Public Score `0.69166`과 신규 validation 지표는 평가 데이터가 다르므로 직접적인 개선량으로 비교하지 않는다.
