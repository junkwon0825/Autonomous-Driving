# 차선 분할 포트폴리오

## 프로젝트 현황

이 저장소는 학부 시절의 Kaggle 참여 경험과 새로 수행하는 재현 실험을 구분해 기록한다. 학부 시절 기록인 Public Score `0.69166`은 과거 결과이며, 현재 구현의 성능으로 간주하지 않는다. 현재는 U-Net + BCE baseline과 재현 가능한 학습·평가 경로를 구현하는 단계다. 새 프로젝트의 점수는 실제 데이터로 학습과 평가를 수행한 뒤에만 기록한다.

기본 모델은 256×512 RGB 입력을 받는 binary U-Net이며, encoder 채널은 32, 64, 128, 256, 512다. 모델은 logits를 출력하고, 학습에는 `BCEWithLogitsLoss`를 사용한다. Sigmoid와 임계값 처리는 평가·추론 때만 적용한다.

## 데이터셋 조사와 선택

| 후보 | 과제/라벨 | 분량과 분할 | 접근·이용 조건 | 이 프로젝트와의 적합성 |
|---|---|---|---|---|
| [CVPR 2018 WAD Video Segmentation Challenge](https://www.kaggle.com/competitions/cvpr-2018-autonomous-driving) | 차선이 아니라 자동차·오토바이·자전거·보행자·트럭·버스·삼륜차의 인스턴스 분할. 학습 라벨 픽셀값에 클래스와 인스턴스 ID가 함께 인코딩되고, 제출은 인스턴스별 RLE CSV. | Kaggle 페이지에 `train_color.zip`, `train_label.zip`, `test.zip` 등 8개 파일이 표시되나, 현재 확인한 화면에는 총 용량이 표시되지 않았다. | Kaggle 로그인 및 규칙 동의가 요구될 수 있으며, 현재 페이지의 `Late Submission` 상태와 2018년 종료 일정을 확인했다. 새 제출·점수는 목표로 삼지 않는다. 데이터는 차선 모델 학습에 사용하지 않는다. | 지정한 대회이지만 차선 라벨이 없으므로 차선 분할 데이터로 부적합하다. 결과물에는 문제 정의와 제출 형식 비교를 위해 기록한다. |
| [CULane](https://xingangpan.github.io/projects/CULane.html) | 차선 마킹/곡선의 점 좌표와 `laneseg_label_w16` 픽셀 라벨을 제공. 공개 설명은 train 88,880 / validation 9,675 / test 34,680 프레임. | 55시간 이상 주행 영상에서 추출한 133,235 프레임. 공식 train/validation/test 목록과 어려운 장면 카테고리가 있다. | 공식 페이지에서 Google Drive/Baidu 다운로드. 데이터는 비상업적 연구·교육·개인 실험용이며 재배포와 상업적 이용을 제한한다. 원본에는 영상 프레임이 있어 임의 프레임 분할은 누수 위험이 있다. | **우선 후보.** 픽셀 마스크와 분리 목록이 있어 binary segmentation baseline에 가장 직접적이다. 우선 공식 train/val 목록을 사용하고 작은 부분 집합으로 시작한다. 전체 파일은 아직 받지 않았다. |
| [TuSimple Lane Detection Challenge](https://github.com/TuSimple/tusimple-benchmark) | JSON의 lane x/y 좌표를 담은 polyline 라벨이며 pixel mask가 아니다. segmentation 실험에는 선 두께를 정해 mask로 래스터화해야 하고, 공식 평가는 지정 높이의 lane point matching 기준이다. | 약 7,000개 1초 video clip(각 20 frames), train 3,626 annotated frames / test 2,782 clips. | CVPR 2017 challenge의 공개 benchmark 문서에서 데이터/ground-truth 다운로드를 안내한다. 실제 용량과 데이터 사용 조건은 배포처에서 확인해야 한다. 코드 저장소의 Apache-2.0은 데이터 자체의 이용 허가와 동일하지 않다. | 비교적 작고 접근이 간단한 대안이지만, 선 두께 선택이 픽셀 평가 정의에 영향을 준다. CVPR 2017 challenge 제출/leaderboard는 현재 목표가 아니다. |
| [BDD100K](https://github.com/bdd100k/bdd100k) | 다중 작업 주행 데이터. lane detection은 차선 좌표 기반이며 별도 drivable-area/semantic mask 과제와 구별해야 한다. | 공식 소개는 100K 주행 동영상 및 10개 태스크를 설명한다. 태스크별 라벨 수와 데이터 크기는 별도로 확인해야 한다. | 공식 홈페이지와 사용 문서를 통해 신청·이용 조건을 확인해야 한다. | 환경 다양성은 장점이나 이 binary lane-mask baseline의 첫 데이터셋으로는 전처리 범위가 커 후속 후보로 둔다. |

### 선택 및 데이터 접근 상태

첫 실험 데이터로 CULane을 선택했다. pixel label 파일과 공식 분할이 있어 모델 입출력을 과제에 바로 맞출 수 있고, 곡선·가림·야간 등 까다로운 조건을 살펴볼 수 있기 때문이다. 다만 전체 데이터 학습을 바로 하지 않고, 합법적인 개인 실험 사용 조건을 확인한 뒤 일부 데이터로 데이터 로딩과 학습 경로부터 검증한다. 원본 이미지/마스크를 Git에 올리지 않는다.

데이터는 CULane 공식 프로젝트 페이지의 Google Drive 또는 Baidu Cloud 링크에서 직접 내려받아야 한다. 안내된 train/validation 목록과 mask 파일을 확보하고, 각 샘플을 아래 CSV 형식으로 정리한다. `image`와 `mask`는 `data_root` 기준 상대 경로이며 `sequence_id`는 선택 필드다.

```csv
image,mask,sequence_id
driver_23_30frame/06030817_0755.MP4/00000.jpg,laneseg_label_w16/driver_23_30frame/06030817_0755.MP4/00000.png,driver_23_30frame/06030817_0755.MP4
```

원본 목록의 경로는 실제로 받은 데이터 디렉터리에 맞춰 CSV에 기록한다. 별도 `train.csv`, `val.csv`를 생성해 공식 분할을 보존한다. CSV의 영상 식별자(`sequence_id`)는 두 분할 간 겹치면 안 된다. 다운로드가 완료되지 않아 현재 저장소에는 실제 데이터·분할 파일이 없다. Kaggle 자격 증명도 설정하거나 저장하지 않았다.

## 구조

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
├── notebooks/README.md
├── experiments/README.md
├── results/README.md
├── tests/test_core.py
├── requirements.txt
└── .gitignore
```

### 코드 설명 기준

- `#1.data`: CSV 기반 데이터셋, 입력 크기 조정, image bilinear / mask nearest-neighbor.
- `#2.model`: 32-64-128-256-512 채널 U-Net과 skip connection.
- `#3.compile,train`: 고정 seed, BCEWithLogitsLoss, AdamW, early stopping, best checkpoint 및 epoch CSV.
- `#4.evaluate,predict`: validation loss, Dice/IoU/precision/recall, 원본·정답·예측·overlay 시각화.

## 환경 설정

Windows PowerShell에서 프로젝트 폴더를 기준으로 실행한다. Python 3.11 또는 3.12 사용을 권장한다. 현재 확인한 기본 Python 3.14에는 PyTorch가 없었고, RTX 4060(8 GB)이 감지됐다. 기존 conda 환경을 덮어쓰지 않도록 새 `.venv`에 CUDA 12.8 빌드의 PyTorch 2.11.0을 포함한 의존성을 설치한다.

```powershell
python --version
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -e .
python -c "import torch; print(torch.__version__, torch.cuda.is_available()); print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU')"
```

기본 requirements는 Windows용 PyTorch CUDA 12.8 wheel을 고정한다. 다른 OS/GPU 조합을 사용할 경우 PyTorch 공식 설치 안내에서 해당 플랫폼에 맞는 wheel을 고른다. `torch.cuda.is_available()`가 `False`이면 CPU로 조용히 넘어가지 말고 드라이버와 wheel 조합을 점검한다. 프로젝트 기본 설정은 CUDA 자동 선택이며, `device: cuda`를 명시하면 CUDA 미지원 시 오류를 낸다.

첫 명령의 Python이 3.11 또는 3.12가 아니면 해당 버전을 설치/선택한 뒤 `.venv`를 만든다. Windows Python Launcher(`py`)가 설치된 환경에서는 `py -3.12 -m venv .venv`를 대신 사용할 수 있다.

## 실행

먼저 핵심 테스트와 소량 합성 데이터 end-to-end smoke test를 수행한다.

```powershell
python -m pytest
python -m lane_segmentation.smoke_test
```

데이터를 준비한 뒤 `configs/baseline.yaml`의 `data_root`, `train_manifest`, `val_manifest`를 조정한다. 분할은 config/manifest로 고정하며, 프레임 단위 무작위 분할로 동일 영상이 양쪽에 섞이지 않도록 한다.

```powershell
python -m lane_segmentation.train --config configs/baseline.yaml
python -m lane_segmentation.evaluate --config configs/baseline.yaml --checkpoint experiments/baseline/best.pt
```

로그와 체크포인트는 `experiments/`에, 정성 시각화는 `results/`에 저장된다. 이 경로들은 기본적으로 Git에서 제외한다. 전체 학습, 개선 실험(BCE+Dice, augmentation, TTA), 외부 검증, 실제 CULane 결과 및 Kaggle 제출은 아직 수행하지 않았다.

## 평가 정의 및 면접 메모

학습은 pixel-level BCE와 logits를 사용한다. BCE는 각 픽셀의 이진 분류를 직접 최적화하고, Dice loss는 전경/배경 픽셀 불균형에서 겹침 비율을 강조한다. baseline에서는 변수를 분리하기 위해 BCE만 사용하고, 다음 실험에서 같은 split으로 BCE+Dice를 비교한다.

Dice와 IoU는 동일한 이진 예측에 대해 `Dice = 2 IoU / (1 + IoU)` 관계가 있다. 구현 지표는 validation 전체 픽셀의 혼동 행렬을 합산해 계산하며, threshold는 기본 0.5다. 전경과 예측이 모두 비어 있는 샘플/집합에서는 Dice와 IoU를 1로 정의하고, 양성 분모가 없는 precision/recall은 0으로 둔다. 이후 threshold tuning은 validation에서만 선택하고 테스트 데이터에는 재조정하지 않는다.

U-Net은 고해상도 위치 정보를 decoder에 전달하는 skip connection을 제공해 얇고 위치가 중요한 구조를 보존하는 데 적합하다. TTA는 원본/좌우 반전 등 변환 입력의 예측을 원본 좌표로 되돌려 평균하는 방식이지만, 현재 구현·성능 검증은 하지 않았다. 실제 주행 적용에는 시간 연속성, 카메라 캘리브레이션, 지연 시간, OOD/악천후 검증, 안전 모니터링과 시스템 통합이 추가로 필요하다.

## 현재 검증 상태

- Python 3.12 가상환경과 CUDA 12.8 PyTorch 2.11.0을 설치했고, RTX 4060 Laptop GPU 연산을 확인했다.
- `python -m pytest -q`: 5개 테스트 통과.
- 합성 데이터 2 train / 2 validation 샘플로 GPU에서 1 epoch 학습, validation metric 계산, checkpoint 저장·재로딩, 예측 shape 검사와 4-panel 시각화 생성까지 smoke test를 통과했다. 이 결과는 코드 실행 확인용이며 실제 데이터 성능이 아니다.
- 실제 데이터 접근, 전체 학습, 실제 모델 점수, 실패 사례 분석, Kaggle 제출 기록은 아직 없다.
- 과거 Public Score `0.69166`은 학부 시절 기록으로만 인용한다.
