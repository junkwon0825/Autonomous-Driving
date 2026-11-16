# LKAS Control — 취업 포트폴리오 요약

## 이력서용 핵심 문장

MATLAB 기반 선형 Dynamic Bicycle Model과 Lateral/Heading PID 조향 제어기를 구현하고, 직선·곡선·속도 변화·외란 등 7개 시뮬레이션 시나리오에서 횡방향 추종 성능과 조향 응답을 정량적으로 검증했습니다.

## 프로젝트 소개

차량 횡방향 동역학과 조향 제어 과정을 분석할 수 있도록 선형 Dynamic Bicycle Model을 MATLAB 함수로 구성하고, Lateral Error와 Heading Error에 각각 이산 PID를 적용했습니다. 조건부 적분 정지와 ±30° 조향 포화를 적용하고 직선 복원, 곡률, 큰 초기 오차, 속도 ramp, 노이즈·외란, 차선 변경 reference 등 7개 시나리오를 평가했습니다. 실행 결과를 지표/시계열 CSV와 그래프로 남기고, 자동 검사를 통해 시나리오 출력과 저장 지표의 일관성을 확인했습니다.

## 기술 스택 및 구현 항목

- MATLAB R2016a, MATLAB functions, fixed-step RK4
- Linear Dynamic Bicycle Model and linear tire cornering-force model
- Two discrete PID error loops: lateral and heading
- Steering saturation and conditional integration anti-windup
- Seven deterministic simulation scenarios
- CSV metrics/time series, MATLAB plots, automated assertions

MATLAB 코드는 Simulink/Stateflow, 추가 Toolbox, OpenCV, Python, Raspberry Pi, Arduino에 의존하지 않습니다.

## 수행 역할

- 차량 상태·좌표계·단위·가정 정리
- Dynamic Bicycle Model과 PID steering loop 구현
- 7개 scenario 입력/초기조건/외란 구성
- MATLAB 실행, 성능 지표와 CSV/그래프 산출
- 시나리오별 출력 및 저장 CSV 수치 교차검증
- 설계 보고서, 요구사항 추적, 기술면접 자료 작성

## 핵심 결과

- MATLAB R2016a에서 **7개 시나리오 자동 검사 통과**
- 직선 복원 RMS lateral error: **0.003795 m**
- 일정 곡률 `0.003 1/m` RMS lateral error: **0.009925 m**
- 큰 초기 오차 case(`e_y=0.15 m`, `e_psi=0.05 rad`): 최대 absolute lateral error **0.154836 m**, steering saturation **4/101 samples**
- 속도 ramp `7→15 m/s` RMS lateral error: **0.007267 m**
- 측정 노이즈+횡외란 case RMS lateral error: **0.025009 m**, settling threshold 미달
- Scenario metrics와 원시 시계열 CSV의 RMS/max/heading/yaw/steering 값 대조

위 성과는 지정된 MATLAB 모델 및 deterministic 입력 조건에서 산출된 시뮬레이션 결과입니다.

## 기술적 한계 및 프로젝트 배경

학부 자동차 제어 과정의 LKA/Bicycle Model/PID 학습 경험을 배경으로 프로젝트를 구성했습니다. 현재 저장소의 모델과 실행 결과는 코드와 CSV로 확인 가능한 MATLAB 시뮬레이션 산출물입니다. 원본 Simulink/Stateflow 모델은 이 구현의 일부가 아니며, 실시간 영상 인식/미니카 제어도 포함하지 않습니다.

모델은 작은 타이어 슬립, 선형 코너링 강성, 양의 종방향 속도, 평탄한 도로를 가정합니다. 타이어 포화, steering actuator 동특성, 측정 지연은 포함하지 않습니다. 후보 차량 파라미터와 PID 게인의 원 단위/차축 기준은 [Design Report](design-report.md)에 가정으로 구분했습니다. 과거 미니카 경험은 실제 자료가 확인되는 범위에서만 [`original/mini-car/`](../original/mini-car/README.md)에 보강합니다.

## 1분 면접 설명

“MATLAB에서 선형 Dynamic Bicycle Model과 Lateral/Heading PID 조향 제어기를 구현했습니다. 차량 상태 `[v_y, r, e_y, e_psi]`와 전후륜 선형 타이어 횡력을 사용하고, 0.1초마다 PID 출력을 계산해 조향각을 ±30°로 제한합니다. 직선, 일정 곡률, 초기 오차, 속도 ramp, 노이즈·외란, 차선 변경 reference 등 7개 시나리오를 시험했고, 직선 복원 RMS 횡오차는 0.003795 m, 큰 초기 오차 case에서는 조향 포화가 101샘플 중 4회 발생했습니다. MATLAB 자동 검사와 저장 CSV의 지표 교차검증도 추가했습니다. 이 수치는 선형 모델의 시뮬레이션 결과이므로 실제 차량 성능으로 일반화하지 않습니다.”

## 3분 면접 설명 구성

1. **문제/모델:** LKA 횡방향 거동을 분석하기 위해 질량·요 관성·축간 거리·선형 코너링 강성을 포함한 Dynamic Bicycle Model을 구현했습니다.
2. **상태/수식:** 상태는 `[v_y, r, e_y, e_psi]`; `v_y_dot=(F_yf+F_yr+F_d)/m-v_x r`, `r_dot=(aF_yf-bF_yr)/I_z`, `e_y_dot=v_y+v_x e_psi`, `e_psi_dot=r-v_x kappa`입니다.
3. **제어기:** 두 개의 이산 PID 출력을 합산하여 조향을 만들고 ±30°로 제한합니다. saturation을 더 키우는 방향의 integral update를 보류합니다.
4. **시나리오/결과:** 7개 시험에서 RMS/최대 횡오차, heading, yaw rate, steering, saturation과 settling time을 산출합니다. 큰 초기 오차 case와 noisy/disturbed case의 응답을 비교해 포화와 외란 조건의 한계를 확인했습니다.
5. **검증/범위:** MATLAB R2016a 검사에서 7개 case와 저장 CSV 수치를 검증했습니다. 모델 가정과 단위 불확실성은 문서화했고, 시뮬레이션 결과를 실차 주행 성능과 구분합니다.
