# 데이터 준비

데이터와 파생 파일은 Git에 추가하지 않는다. 첫 후보는 CULane이며, 공식 페이지의 다운로드와 이용 조건을 직접 확인한다: <https://xingangpan.github.io/projects/CULane.html>.

`processed/train.csv`, `processed/val.csv`를 생성하고 프로젝트 config의 `data_root`에서 상대 경로가 해석되게 한다. manifest 필수 컬럼은 `image,mask`, 선택 컬럼은 `sequence_id`다. `sequence_id`를 제공하면 train/validation 간 동일 영상 ID를 코드가 차단한다. split은 CULane의 공식 목록을 기준으로 유지한다.

loader는 이미지 RGB와 마스크 grayscale를 읽고 같은 크기인지 확인한다. 이미지는 bilinear, 마스크는 nearest-neighbor로 256×512에 맞춘 뒤 mask의 0 초과 픽셀을 차선으로 처리한다. 실제 데이터의 mask 값 분포가 이 가정과 다른지 전체 학습 전 확인한다.

지정된 Kaggle CVPR 2018 WAD 데이터는 차선 mask가 아닌 인스턴스별 도로 객체 라벨이다. 이를 lane segmentation으로 변환하거나 차선 성능의 근거로 사용하지 않는다.
