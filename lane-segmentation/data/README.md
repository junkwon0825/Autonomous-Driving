# Kaggle 데이터 접근

대상 대회는 [Lane Segmentation Challenge](https://www.kaggle.com/competitions/lanesegmentationchallenge)다. Kaggle 공개 설명에는 `train/images/`, `train/masks/`, `test/images/`와 `sample_submission.csv`가 표시되어 있고, RGB image는 720×1280, mask 값은 background 0 / lane 1로 설명되어 있다. Data 탭의 파일 목록과 실제 mask는 로그인 및 대회 규칙 동의 후 확인해야 한다. 현재 대회는 초대가 필요한 제한 참가 상태다.

현재 Kaggle CLI 파일 목록 조회는 인증정보가 없어 중단됐다. 초대된 계정으로 브라우저 로그인 → 규칙 동의를 마친 뒤 Kaggle CLI OAuth 인증을 진행한다.

```powershell
python -m pip install kaggle
.\.venv\Scripts\kaggle.exe auth login
.\.venv\Scripts\kaggle.exe competitions files -c lanesegmentationchallenge
.\.venv\Scripts\kaggle.exe competitions download -c lanesegmentationchallenge -p data/raw
```

다운로드 후 압축 구조를 먼저 확인한다. 파일명과 확장자, mask encoding, sample submission의 RLE 순서를 실제 데이터에서 확인하기 전까지 추측하여 변환하지 않는다. 실제 데이터 경로, 매칭, 검증을 통과한 뒤 `data/processed/train.csv`와 `data/processed/val.csv`에 `image,mask,sequence_id` manifest를 생성하고 `configs/baseline.yaml`에 반영한다. 동일 주행 구간의 연속 프레임이 있으면 `sequence_id` 단위로 split을 나눈다.

현재 제공된 ZIP은 train JPEG 7,252장, test JPEG 2,782장, `sample_submission.csv`만 포함하며 차선 mask가 없다. 따라서 train/validation 분할과 supervised 학습은 할 수 없다. ZIP의 sample template 열은 `image_id,encoded_pixels`이고 2,782개 test 파일 순서를 정의한다. 대회 설명은 빈 lane 예측을 `0`으로 표현하므로 all-empty 파일은 형식 확인용으로 생성할 수 있지만, 이를 모델 예측 또는 유효 성능 제출로 간주하지 않는다.

학습 checkpoint와 실제 `test/images`, `sample_submission.csv`를 확보한 뒤 `python -m lane_segmentation.submission`으로 제출 CSV를 생성한다. 대회 설명은 RLE flatten 방향과 run index base를 특정하지 않아 CLI에서 두 값을 필수로 받는다. 대회 제공 helper/명세를 확인하기 전에는 값을 선택하지 않는다. 출력은 `data/submissions/`에 저장하며 Git에서 제외한다.

대회 data page에 MIT license 링크가 표시된다. 이용 시 Kaggle 대회 규칙과 해당 라이선스 내용을 함께 확인한다. 데이터, sample submission, Kaggle token 파일은 Git에 올리지 않는다. 저장소의 `.gitignore`는 `data/raw/`, `data/processed/`, `data/submissions/`, Kaggle credential 파일을 제외한다.

CULane 다운로드 실험 파일은 로컬 `data/raw/downloads/`에 남아 있을 수 있으나 현재 대회의 실험 입력으로 사용하지 않는다.
