# LKAS Control | MATLAB Simulation Portfolio

학부 시절의 차량 제어 학습 기록을 출발점으로 삼아 **MATLAB 함수 기반 차량 횡방향 제어 시뮬레이션을 새로 구현하고 검증**한 포트폴리오입니다.

> **구현 범위:** 이 저장소의 Dynamic Bicycle Model, PID 구현, 7개 시나리오와 수치는 모두 현재 MATLAB 코드로 재현되는 결과입니다. 학부 원본 `.slx`/Stateflow/코드가 제공되지 않아 원본 시스템의 완전한 복원이나 동일성은 주장하지 않습니다. Simulink 모델, 실제 카메라·미니카 폐루프 제어, 실물 주행 시험은 구현/수행하지 않았습니다.

## 01. Project Overview

자동차 제어 학습 과정에서 다룬 차체 횡방향 동역학, Lateral/Heading Error, PID 기반 조향 개념을 실제 실행 가능한 MATLAB 모델로 다시 구성했습니다. 목적은 과거 활동 기록과 현재 새로 구현한 작업을 구분하고, 수식·가정·코드·시험 데이터를 함께 검토할 수 있도록 정리하는 것입니다.

| 구분 | 확인 가능한 범위 |
|---|---|
| 학부 시절 기록 | 저장소의 [`LKAS_PROJECT.md`](../LKAS_PROJECT.md)에 LKA, Bicycle Model, Lateral/Yaw PID 등의 경험이 요약되어 있음. 원본 모델/발표자료는 현재 저장소에 없음. |
| 현재 신규 구현 | MATLAB Dynamic Bicycle Model, P/I/D 항을 포함한 두 오차 PID 루프, 조향 포화 및 조건부 적분 정지, 7개 결정론적 가상 시나리오, 지표/CSV/그래프/자동 검사. |
| 구현하지 않은 범위 | 원본 Simulink/Stateflow 모델 복원, 새 Simulink 모델, Raspberry Pi/Arduino 통합, 카메라 인식, 실물 폐루프 주행 및 실측 성능. |

## 02. System Architecture

```mermaid
flowchart LR
    REF["기준 경로<br/>곡률·속도·차선 변경"] --> ERR["모델 상태 기반 오차<br/>e_y, e_psi"]
    ERR --> PID["Lateral PID + Heading PID<br/>P / I / D"]
    PID --> SAT["조향 명령 포화<br/>±30° (가정)"]
    SAT --> PLANT["선형 Dynamic Bicycle Model"]
    PLANT --> STATE["v_y, yaw rate, e_y, e_psi"]
    STATE --> ERR
    STATE --> LOG["CSV 지표·시계열·그래프"]
```

![MATLAB LKAS scenario comparison](results/simulation/scenario_comparison.png)

![Large initial-offset case: lateral error, heading error, steering response](results/simulation/reference_simulation.png)

실제 제어 입력은 MATLAB 시나리오의 속도·곡률·초기 조건 및 인위적으로 설정한 오차/외란입니다. 카메라 영상에서 차선을 검출하는 입력 경로는 구현하지 않았습니다.

## 03. Vehicle Dynamics

구현은 **Kinematic Bicycle Model이 아니라 선형 Dynamic Bicycle Model**입니다. 전륜/후륜의 선형 코너링 힘을 이용해 차체 횡속도와 요레이트 동역학을 계산합니다.

상태와 부호:

- `v_y [m/s]`: 차체 좌표계 횡속도
- `r [rad/s]`: 반시계 방향 yaw rate
- `e_y [m]`: 기준 경로 왼쪽 방향 양수인 횡방향 추종 오차
- `e_psi [rad]`: 차량 heading − 기준 경로 heading
- `delta [rad]`: 좌회전 양수로 가정한 **전륜 road-wheel 조향각**
- `v_x [m/s]`: 양수 종방향 속도, 시나리오에서 매 제어주기마다 갱신

```text
alpha_f = delta - (v_y + a r) / v_x
alpha_r =             -(v_y - b r) / v_x
F_yf    = C_f alpha_f
F_yr    = C_r alpha_r

v_y_dot   = (F_yf + F_yr + F_disturbance) / m - v_x r
r_dot     = (a F_yf - b F_yr) / I_z
e_y_dot   = v_y + v_x e_psi
e_psi_dot = r - v_x kappa
```

차량 동역학은 제어주기 0.1 s 동안 0.001 s 간격의 RK4 적분으로 계산합니다. 소각도·소슬립, 선형 타이어, 평탄한 도로를 가정합니다. 타이어 포화, roll, 하중 이동, 실제 steering actuator, 영상/통신 지연은 모델링하지 않았습니다.

| 파라미터 | 값 | 단위 | 출처/해석 |
|---|---:|---|---|
| `m` | 2045 | kg | 기존 LKAS 요약 기록; 원본 대조 전 |
| `I_z` | 5428 | kg·m² | 기존 LKAS 요약 기록; 원본 대조 전 |
| `a`, `b` | 1.488, 1.712 | m | CG에서 각 축 거리로 기록됨 |
| `C_f`, `C_r` | 38925, 38255 | N/rad 가정 | 차축 합산값으로 신규 모델에서 해석 |
| `T_s` | 0.1 | s | 기록된 0.1 s를 제어주기로 가정 |
| 조향 제한 | ±30 | deg | 전륜 road-wheel 각으로 가정 |

Cornering stiffness의 타이어/차축 기준, 기록된 0.1 s의 의미, 조향각의 기준점은 원본 자료가 없어 확인되지 않았습니다. 자세한 모델 유도와 한계는 [설계·시뮬레이션 보고서](docs/design-report.md)를 참고하세요.

## 04. Control Algorithm

코드는 `matlab/lkas_reference_simulation.m`에서 두 개의 이산 PID 출력을 합산해 단일 조향 명령을 생성합니다. **P/I/D 세 항을 모두 계산**하며, 별도의 feed-forward 항이나 D 필터는 없습니다.

```text
u_y   = Kp_y e_y + Ki_y ∫e_y dt + Kd_y d(e_y)/dt
u_psi = Kp_psi e_psi + Ki_psi ∫e_psi dt + Kd_psi d(e_psi)/dt
delta = clip(-(u_y + u_psi), -30°, +30°)
```

각 오차는 0.1 s마다 샘플링되고, 미분은 측정 오차의 후진 차분입니다. 조향 출력이 포화된 상태에서 두 적분항의 합이 포화를 더 키우는 방향이면 해당 주기의 적분 갱신을 보류합니다(conditional integration).

| 루프 | `Kp, Ki, Kd` | 값의 상태 |
|---|---|---|
| Lateral Error | 4.0, 0.1, 0.2 | 기존 요약 문서에 기록. 단위/원본 블록 미확인. |
| Heading Error | 3.0, 0.1, 0.3 | 기존 요약 문서에 기록. 단위/원본 블록 미확인. |

두 출력이 조향각 단위와 어떻게 스케일되는지는 원본에서 확인되지 않았습니다. 그래서 성능은 오직 명시된 신규 모델의 출력으로만 해석하며 실제 차량 성능으로 일반화하지 않습니다. `Error gain = 6000` 기록은 적용 위치와 단위가 불명확하여 사용하지 않았습니다.

## 05. MATLAB Simulation

- MATLAB R2016a (9.0.0.341360), Windows
- 본 시뮬레이션 코드 실행 및 테스트에 Simulink/Stateflow/추가 Toolbox 불필요
- 환경 점검 시 Simulink와 Control System Toolbox 제품/라이선스 사용 가능 상태 확인
- 총 7개 결정론적 시나리오, 각 10초·101 제어 샘플
- 각 시나리오 입력과 결과 해석: [시나리오 요약](simulation/scenarios.md)

저장소 루트에서 실행:

```matlab
addpath(fullfile(pwd, 'lkas-control-mini-car', 'matlab'));
run_lkas_suite
```

자동 테스트 및 CSV/그래프 일관성 검사:

```matlab
run(fullfile(pwd, 'lkas-control-mini-car', 'tests', 'test_lkas_reference.m'));
```

## 06. Results

아래 수치는 MATLAB 실행으로 생성한 CSV에서 가져온 **시뮬레이션 값**입니다. 헤딩/요/조향 최대치는 각 시나리오의 절대 최대값입니다. 추종 오차는 차량 모델 내부 상태이며 영상으로 측정한 차선 오차가 아닙니다.

| 시나리오 | 초기 조건/입력 | RMS `e_y` (m) | max `|e_y|` (m) | max `|e_psi|` (rad) | max `|r|` (rad/s) | max `|delta|` (deg) | 포화 샘플 | 정착시간 (s) |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| 직선 복원 | 10 m/s; `e_y=0.02 m`, `e_psi=0.01 rad` | 0.003795 | 0.020486 | 0.016778 | 0.143757 | 7.491 | 0 | 0.2 |
| 일정 곡률 | 10 m/s; `kappa=0.003 1/m`; 초기 `0.05 m`, `0.02 rad` | 0.009925 | 0.050000 | 0.043502 | 0.300134 | 18.814 | 0 | 1.0 |
| 큰 초기 오차 | 10 m/s; `e_y=0.15 m`, `e_psi=0.05 rad` | 0.025533 | 0.154836 | 0.111653 | 0.804166 | 30.000 | 4 | 1.9 |
| 속도 변화 | 7→15 m/s/10 s; 초기 `0.05 m`, `0.02 rad` | 0.007267 | 0.050000 | 0.029615 | 0.256826 | 14.937 | 0 | 0.2 |
| 노이즈+외란 | 노이즈 `0.01 m/0.003 rad`, 외란 `300 N` | 0.025009 | 0.050000 | 0.046173 | 0.436017 | 23.829 | 0 | 미정착 |
| 차선 변경 예시 | 10 m/s; 3.5 m 기준경로 이동, turn signal | 0.008401 | 0.019469 | 0.019602 | 0.171029 | 4.384 | 0 | 해당 없음 |
| 노이즈 없는 비교 | 노이즈/외란 없음; noisy case와 같은 초기조건 | 0.008993 | 0.050000 | 0.039683 | 0.320051 | 17.432 | 0 | 1.0 |

정착시간은 `|e_y| <= 0.02 m`가 이후 끝까지 유지되는 첫 시점입니다. 차선 변경은 회복 정착시간으로 해석할 수 없어 해당 없으며, 노이즈+외란 시나리오는 종료 시점까지 기준을 만족하지 않아 미정착입니다. Overshoot 정의 등은 [보고서의 지표 정의](docs/design-report.md#6-실험-조건과-측정-지표)를 확인하세요.

결과 파일:

- [전체 지표 CSV](results/simulation/scenario_metrics.csv)
- [7개 시나리오 시계열 CSV](results/simulation/scenario_timeseries.csv)
- [큰 초기 오차 로그 CSV](results/simulation/reference_simulation.csv)
- [시나리오 비교 그래프](results/simulation/scenario_comparison.png)
- [큰 초기 오차 추종/조향 그래프](results/simulation/reference_simulation.png)

노이즈와 횡방향 외란을 함께 적용한 케이스의 RMS 오차는 동일 초기조건의 무노이즈 비교보다 컸습니다. 두 영향을 분리한 검증은 아니며, 모든 수치가 가상 모델 결과입니다. 실제 미니카나 실차 시험 결과가 아닙니다.

## 07. Undergraduate Mini-Car Experience

학부 미니카 사진·부품 목록·당시 자료는 아직 제공되지 않았습니다. 따라서 현재는 과거 제작 여부, 실제 센서/보드, 수행 기능 및 개인 역할을 구체적으로 단정하지 않습니다. 사진이나 기록이 확인되는 대로 캡션과 근거를 추가할 위치는 [`original/mini-car/`](original/mini-car/)에 마련했습니다.

실제 원본 사진은 AI로 생성하거나 공개 블로그의 사진으로 대체하지 않습니다. 카메라 연동, 자동 조향, 폐루프 차선 유지, 주행 실험 및 성능은 확인 자료가 없는 한 수행 사실로 기재하지 않습니다. 이 프로젝트에서 신규 Raspberry Pi/Arduino 개발도 진행하지 않습니다.

## 08. Engineering Analysis

- 동적 모델은 `v_y`, yaw rate, tire cornering stiffness를 포함해 운동 응답을 표현하지만, 타이어 선형/소슬립 가정에 제한됩니다.
- Lateral/heading PID 구조는 기록된 두 게인 세트를 조합한 새로운 참조 구현입니다. 원본의 블록 연결·단위가 확인되기 전까지 동일 제어기라고 단정하지 않습니다.
- 큰 초기 오차 case에서 조향 제한에 4샘플 닿았습니다. 노이즈+외란 case는 2 cm 정착 기준을 만족하지 못했습니다.
- 차선 변경 state/기준 경로는 새로 만든 시뮬레이션 예시로, 과거 Stateflow 재현이 아닙니다.
- 실차/미니카에 적용하려면 실제 질량, wheelbase, tire, steering map, sensor delay/제어주기 등을 식별하고 별도 시험해야 합니다.

가장 중요한 한계는 원본 모델 부재, 기록 게인의 단위 불명, 실제 센서·액추에이터 모델 부재, 하드웨어 시험 부재입니다. 세부 분석은 [설계 보고서](docs/design-report.md)에 기록했습니다.

## 09. Reproducibility

```text
MATLAB: R2016a (9.0.0.341360)에서 검증
필수 Toolbox: 없음 (base MATLAB 함수 및 table/writetable 사용)
실행: run_lkas_suite
검사: tests/test_lkas_reference.m
```

테스트는 시뮬레이션 유한성/조향 제한/상태 흐름을 검사하고, 저장 지표 CSV 및 두 CSV 사이의 baseline 시계열을 수치로 대조합니다. 그래프도 동일한 시뮬레이션 결과 객체에서 생성되며 저장 파일 존재를 검사합니다. MATLAB 버전이 다르면 figure renderer/이미지 모양은 달라질 수 있습니다.

## 10. Technical Interview Notes

실제 코드와 결과에 근거한 질문/답변은 [기술면접 문서](docs/technical-interview.md)를 참고하세요. `Dynamic`/`Kinematic` 모델 차이, 오차 정의, P/I/D와 anti-windup, 속도 변화, Stateflow 미사용, 가장 어려운 noisy case, 학부 경험과 현재 재구현의 경계를 포함합니다. 이력서용 요약과 1/3분 답변은 [포트폴리오 요약](docs/portfolio-summary.md)에 있습니다.

## 파일 구성

```text
lkas-control-mini-car/
├── README.md
├── matlab/             # Dynamic Bicycle Model, PID 및 실행 함수
├── tests/              # MATLAB 시나리오/CSV 결과 검사
├── simulation/         # 입력 조건 및 지표 정의
├── results/simulation/ # 실제 생성한 CSV와 그래프
├── docs/               # 설계 보고서, 면접 및 포트폴리오 요약
└── original/
    ├── README.md       # 학부 LKA 원본 자료 현황
    └── mini-car/       # 과거 미니카 사진/문서 추가 위치
```
