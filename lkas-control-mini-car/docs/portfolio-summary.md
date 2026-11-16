# LKAS Control — 포트폴리오 요약

## 이력서용 요약

학부 차량 제어 학습 기록을 바탕으로 MATLAB에서 선형 Dynamic Bicycle Model과 이산 Lateral/Heading PID 제어를 새로 구현하고, 직선·곡률·속도 변화·오차/외란 등 7개 시나리오에서 자동 검증했습니다. CSV 성능 지표와 시계열·그래프를 생성했으며, 원본 Simulink/Stateflow 복원 및 실제 하드웨어 주행은 수행하지 않았습니다.

## 포트폴리오 소개

학부 시절의 LKA/Bicycle Model/PID 제어 학습 경험을 기록으로 남기고, 과거 구현 범위와 현재 새로 구현한 작업을 구분하기 위해 MATLAB 기반 참조 모델을 구성했다. 질량·요관성·축간 거리와 선형 코너링 강성을 사용하는 Dynamic Bicycle Model에 두 개의 이산 PID 오차 루프를 연결하고, 조향 포화 및 조건부 적분 정지를 적용했다. 직선 복원, 곡률, 큰 초기 오차, 속도 ramp, 측정 노이즈와 횡방향 외란, 차선 변경 reference, 무노이즈 비교 시나리오를 실행하고 단위가 명시된 지표 및 CSV/그래프를 생성했다. 결과는 신규 시뮬레이션의 출력으로만 해석하며 원본 Simulink 모델 또는 실제 미니카/실차 검증으로 주장하지 않는다.

## 기술 스택

- MATLAB R2016a
- MATLAB functions, fixed-step RK4 integration
- Linear Dynamic Bicycle Model
- Discrete PID, steering saturation, conditional integration hold
- CSV time series / scenario metrics, MATLAB plots
- MATLAB automated scenario and saved-result checks
- Git / GitHub

Simulink/Stateflow, OpenCV, Python, Raspberry Pi, Arduino 및 하드웨어 코드/시험은 이 결과물에 사용되지 않았다.

## 본인의 역할

- 기존 저장소의 LKAS 요약 기록과 모델 후보 파라미터 검토
- Dynamic Bicycle Model의 상태/좌표/단위/가정 정의
- PID 조향 참조 구현 및 7개 deterministic test scenario 작성
- MATLAB 실행과 자동 검사, CSV/그래프 생성 및 결과 교차검증
- 설계 보고서·요구사항 추적·면접 문서 작성
- 과거 원본/사진/부품 정보가 없는 부분을 미확인/미실시로 구분

과거 학부 팀 프로젝트에서의 실제 역할/기여율은 제공된 증빙으로 확인할 수 없어 별도 주장하지 않는다. 위 역할은 현재 저장소에 새로 작성한 재구현 작업을 말한다.

## 핵심 결과

- MATLAB R2016a에서 7개 시나리오 자동 검사 통과
- 직선 복원 시나리오 RMS lateral error: **0.003795 m**
- 큰 초기 오차 시나리오 `e_y=0.15 m`, `e_psi=0.05 rad`: 최대 횡오차 **0.154836 m**, 조향 포화 **4/101 샘플**, settling time **1.9 s**
- 일정 곡률 `0.003 1/m`: RMS lateral error **0.009925 m**
- 노이즈+외란 조건: RMS lateral error **0.025009 m**, 0.02 m settling 조건 미달
- 시나리오별 CSV 지표와 원시 시계열 CSV 사이 수치 대조

모두 이상화된 MATLAB 차량 모델의 **시뮬레이션 결과**이며, 실차/미니카 성능은 아니다.

## 한계와 미완료 사항

- 학부 원본 `.slx`, `.m`, Stateflow, 발표자료 및 원시 로그가 없어 역사적 모델을 대조·복원하지 못함
- 게인 단위, cornering stiffness 타이어/축 기준, 30° 조향 기준, `0.1 s` 기록의 의미를 미확인
- 선형 타이어·소슬립 가정, 조향 actuator 및 센서/통신 지연 미모델링
- 실제 camera perception, MCU control, 미니카/실차 폐루프 주행 및 측정 미실시
- 학부 미니카 사진/자료와 사용자 역할 설명이 미제공; 증빙 위치만 준비

## 1분 설명

“학부에서 차량 횡방향 제어와 LKA를 공부했던 경험을 바탕으로, 당시 구현을 확인 가능한 사실과 현재 새로 만든 결과로 나누어 정리했습니다. 현재는 MATLAB에서 질량·요 관성·전후륜 선형 타이어 강성을 갖는 Dynamic Bicycle Model과 Lateral/Heading PID 조향 루프를 구현했습니다. 직선, 곡률, 큰 초기 오차, 속도 변화, 노이즈/외란, 차선 변경 reference 등을 포함한 7개 deterministic 시나리오를 실행하고 자동 검사와 CSV·그래프 대조를 했습니다. 큰 초기 오차 케이스에서 RMS 횡오차는 2.55 cm이고 조향 제한에 4회 닿았습니다. 원본 Simulink 파일과 미니카 사진/부품 기록이 없어 이를 복원 또는 실물 주행이라고 말하지 않고, 실제 수행 범위와 한계를 분리해 문서화했습니다.”

## 3분 설명 구성

1. **배경:** 학부 프로젝트 요약에는 LKA, Bicycle Model, Lateral/Yaw PID 학습이 기록되어 있으나 원본 파일을 현재 확보하지 못했다.
2. **재구현:** 현재 코드는 Kinematic이 아니라 선형 Dynamic Bicycle Model이다. 상태는 `[v_y, r, e_y, e_psi]`, 타이어 횡력은 cornering stiffness×slip angle이다. 0.1 s 제어 갱신 사이를 1 ms RK4로 적분한다.
3. **제어기:** 두 개의 discrete PID가 Lateral/Heading Error의 P/I/D 항을 계산해 출력하고 합산한 뒤 ±30°로 제한한다. anti-windup은 포화를 더 키우는 방향의 integral update를 보류한다. 기록 게인의 단위는 확인되지 않아 수치 결과를 실제 조향 성능으로 일반화하지 않는다.
4. **시험:** 7개 시나리오를 같은 10초·101샘플 기반으로 실행했다. noisy/disturbed case의 RMS는 0.025009 m이고, 대응 baseline RMS 0.008993 m보다 크며 2 cm 정착 조건을 만족하지 않았다. 큰 초기오차 case는 4번 saturation되었다.
5. **검증:** MATLAB R2016a에서 자동 assertion을 실행했고 저장 CSV의 지표를 시계열에서 다시 계산하여 수치 대조했다. 그래프는 같은 시뮬레이션 출력으로 생성했다.
6. **경계와 다음 증빙:** 원본 Simulink 복원, Stateflow, 카메라·MCU·실제 미니카 제어/주행은 미구현/미실시다. 사진이 추가되면 실제 보이는 정보와 당시 작업/개인 역할을 사용자 확인으로 보강할 예정이다.
