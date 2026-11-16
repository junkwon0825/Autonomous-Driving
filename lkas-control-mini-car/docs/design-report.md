# LKAS Control + Mini Car 설계·시뮬레이션 보고서

- 실행 환경: MATLAB R2016a (9.0.0.341360), Windows
- 시뮬레이션 실행일: 2026-11-16
- 분석 대상: Dynamic Bicycle Model 기반 이산 PID 조향 제어 및 7개 시나리오

## 1. 요약

이 보고서는 MATLAB Dynamic Bicycle Model과 이산 PID 조향 제어기의 수학적 구조, 시험 환경 및 7개 시나리오의 성능 평가 결과를 정리한다. 미니카 관련 사진과 기술 설명은 별도 프로젝트 자료로 분리해 제시한다.

현재 구현은 MATLAB 함수 기반 선형 Dynamic Bicycle Model, 기록된 PID 숫자를 그대로 사용한다고 가정한 두 오차 PID 제어기, 조향 포화 및 조건부 적분 정지 로직으로 구성된다. 직선 복원, 곡선, 큰 초기 오차, 속도 램프, 측정 노이즈와 횡방향 외란, 방향지시등/차선 변경 상태, 무노이즈 비교 시나리오를 실행했다. Simulink와 Control System Toolbox가 설치되고 라이선스가 사용 가능함을 확인했지만, 본 실행 코드에는 추가 Toolbox가 필요하지 않다.

기준 시뮬레이션에서 RMS 횡오차 0.003795 m, 최대 횡오차 0.020486 m였다. 큰 초기 오차 시나리오에서는 초기 포화 4샘플을 포함하여 RMS 횡오차 0.025533 m, 최대 횡오차 0.154836 m, 정착 시간 1.9 s였다. 인위적인 센서 노이즈와 외란을 함께 적용한 경우 RMS 오차가 동일 초기조건의 무노이즈 비교 0.008993 m에서 0.025009 m로 증가했고, 0.02 m 정착 기준을 만족하지 않았다. 이는 **이 모델과 가정에 대한 시뮬레이션 결과**일 뿐 실제 차나 안전한 제어 성능의 증거는 아니다.

## 2. 구현 및 검증 범위

| 구성 | 내용 |
|---|---|
| 차량 동역학 | MATLAB 기반 선형 Dynamic Bicycle Model |
| 조향 제어 | Lateral/Heading 이산 PID, ±30° 조향 제한, 조건부 적분 갱신 |
| 실험 | 직선·곡선·초기 오차·속도 변화·노이즈/외란·차선 변경 및 비교 조건 등 7개 시나리오 |
| 검증 | MATLAB R2016a 자동 검사, 성능 지표·시계열 CSV 대조, 그래프 생성 |
| 실험 성격 | 차량 모델의 수치 시뮬레이션. 미니카 주행·센서 피드백 성능과 별개 |

차량 파라미터 및 제어 게인의 해석은 다음 절에 명시한 모델 가정을 따르며, 수치 결과는 이 시뮬레이션 조건에서 평가한다.

## 3. 시스템 구조

```text
scenario input (v_x, curvature, initial state, optional noise/disturbance)
          │
          ▼
Lateral / heading error state [e_y, e_psi]
          │
          ▼
two discrete PID loops → steering saturation / conditional integral hold
          │ delta [rad]
          ▼
linear Dynamic Bicycle Model → [v_y, yaw rate, e_y, e_psi]
          │                                  │
          └──── path curvature feedback ─────┘
                           │
                   CSV metrics / plots
```

MATLAB 참조 모델에는 카메라 영상 입력, 영상 좌표 보정, 조향 servo 보정 및 모터 속도 제어가 없다. 미니카의 영상 처리 및 구동 구성은 [프로젝트 사진](../original/mini-car/)에서 별도로 확인할 수 있다. 이 보고서의 제어 결과는 MATLAB 시뮬레이션에 한정된다.

## 4. 차량 모델과 좌표계

이번 참조 모델 상태는 `x = [v_y, r, e_y, e_psi]^T`다. `v_x > 0`은 종방향 속도, `v_y`는 횡속도, `r`은 반시계 방향 yaw rate, `e_y`는 기준 경로 대비 좌측 양의 횡오차, `e_psi`는 차량 heading에서 기준 경로 heading을 뺀 오차다. 조향각 `δ`는 좌측이 양수인 **전륜 road-wheel angle [rad]**로 가정한다.

전후륜 선형 타이어 힘은 다음과 같이 모델링했다.

```text
alpha_f = delta - (v_y + a r) / v_x
alpha_r =             -(v_y - b r) / v_x
F_yf    = C_f alpha_f
F_yr    = C_r alpha_r
```

차량 횡/요 동역학 및 소각도 경로 오차 동역학:

```text
v_y_dot = (F_yf + F_yr + F_disturbance) / m - v_x r
r_dot   = (a F_yf - b F_yr) / I_z
e_y_dot = v_y + v_x e_psi
e_psi_dot = r - v_x kappa
```

여기서 `m [kg]`, `I_z [kg·m²]`, `a,b [m]`, `C_f,C_r [N/rad]`, `kappa [1/m]`이며, 차량 동역학은 각 제어주기 사이에서 1 ms 고정 간격 RK4로 적분한다. 제어 업데이트 간격은 0.1 s다.

모델은 작은 타이어 슬립, 선형 코너링 강성, 양의 종방향 속도, 평탄한 도로, 일정한 차량 파라미터를 가정한다. 큰 조향/슬립, 타이어 포화, roll/pitch, 하중 이동, 실제 조향 액추에이터, 도로 bank 및 영상/통신 지연은 모델링하지 않는다. 현재 `e_y`와 `e_psi`는 소각도·소오차 근사다.

### 4.1 차량 파라미터와 시뮬레이션 가정

| 파라미터 | 값 | 단위 | 사용/주의 |
|---|---:|---|---|
| 질량 `m` | 2045 | kg | 과거 요약에 기록된 값 |
| 요 관성 `I_z` | 5428 | kg·m² | 과거 요약에 기록된 값 |
| CG-전륜 `a` | 1.488 | m | 과거 요약에 기록된 값 |
| CG-후륜 `b` | 1.712 | m | 과거 요약에 기록된 값; `a+b=3.2 m` |
| 전륜 `C_f` | 38925 | N/rad | 차축 합산 강성으로 **신규 모델에서 가정** |
| 후륜 `C_r` | 38255 | N/rad | 차축 합산 강성으로 **신규 모델에서 가정** |
| 제어주기 `T_s` | 0.1 | s | 과거 기록의 시간상수를 샘플주기로 해석한 가정 |
| 조향 제한 | ±30 | deg | 전륜 조향각으로 해석한 가정 |
| PID 숫자 | `[4,0.1,0.2]`, `[3,0.1,0.3]` | 의미 미확인 | 저장소 요약의 횡/Yaw 게인을 직접 적용한 가정 |
| Error gain | 6000 | 미상 | 기록 위치/단위 불명으로 적용하지 않음 |

Cornering stiffness가 axle-total인지 tire 단위인지, 30°가 전륜각인지 운전대각인지, 0.1 s가 주기인지 액추에이터 시정수인지 원본 자료로 확인되지 않았다. 특히 게인 단위가 확인되지 않았으므로 본 결과를 차량 조향 성능으로 해석해서는 안 된다.

## 5. 제어기 및 상태 로직

제어 명령은 두 PID 출력을 합산하여 음의 피드백을 형성한다.

```text
u_y = Kp_y e_y + Ki_y integral(e_y) + Kd_y d(e_y)/dt
u_psi = Kp_psi e_psi + Ki_psi integral(e_psi) + Kd_psi d(e_psi)/dt
delta = saturate(-(u_y + u_psi), -30 deg, +30 deg)
```

이산 PID 게인은 표기한 가정에 따라 모델 내에서 적용했다. 오차는 매 0.1 s마다 샘플링하고, 미분은 측정 오차의 후진 차분으로 계산한다. 미분 필터는 넣지 않았다. 포화 상태에서 적분이 포화를 더 키우는 방향이면 해당 샘플에서 적분을 갱신하지 않는 조건부 적분 정지를 사용했다. 조건부 적분 정지는 포화 상황에서 적분항 누적을 제한하도록 구성했다.

`turn_signal_lane_change`는 신규 설계 예시다.

| 시간 | Mode | 방향지시등 | 기준 경로 |
|---|---|---|---|
| 0–2 s | LANE_KEEPING | OFF | 기존 차로 |
| 2–3 s | TURN_SIGNAL_ACTIVE | ON | 기존 차로 |
| 3–7 s | LANE_CHANGE | ON | 3.5 m 인접 차로로 quintic 이동 |
| 7–10 s | LANE_KEEPING_RESUME | OFF | 변경된 차로 |

상태 전이는 MATLAB 시나리오 함수로 정의하며 Stateflow 차트는 사용하지 않는다.

## 6. 실험 조건과 측정 지표

각 시나리오는 10초, 0.1초 제어주기(101개 샘플)다. 속도는 10 m/s 일정 또는 7→15 m/s 선형 ramp를 사용했다. 곡선 반경은 `1/0.003 ≈ 333 m`다. 노이즈는 재현을 위한 결정론적 sin 파형이며, lateral/heading 진폭 매개변수 0.01 m/0.003 rad를 사용한다. 횡방향 외란은 300 N 진폭의 0.8 Hz 사인파다.

- RMS 횡오차: `sqrt(mean(e_y^2))`
- 최대 절대 횡오차 `max(|e_y|) [m]`
- 최대 절대 헤딩 오차 `max(|e_psi|) [rad]`
- 최대 절대 yaw rate `max(|r|) [rad/s]`
- 최대 절대 steering command `max(|delta|)`; summary CSV에서는 deg, time-series/reference CSV에서는 rad
- 조향 포화 샘플 수: `|delta| >= delta_max - 1e-12`를 만족한 controller samples
- 정착 시간: 이후 모든 샘플에서 `|e_y| <= 0.02 m`가 유지되는 첫 샘플
- 횡오차 반대 방향 overshoot: 시작 오차 부호를 기준으로 반대 방향으로 진행한 최대 거리, 시작 횡오차가 0이면 NaN

노이즈 조건에서 정착 기준을 만족하지 못하면 `NaN`이다. 차선 변경은 회복 응답의 정착 시간 정의가 적절하지 않아 정착 시간과 overshoot를 보고하지 않는다. 이 지표 정의는 시뮬레이션을 위해 새로 정했다.

## 7. 시뮬레이션 결과

아래 표는 2026-11-16 MATLAB R2016a에서 실행한 [`scenario_metrics.csv`](../results/simulation/scenario_metrics.csv) 값을 소수점 6자리 또는 적절한 단위로 표시했다. 원시 707개 시계열 행은 [`scenario_timeseries.csv`](../results/simulation/scenario_timeseries.csv), 시각화는 [`scenario_comparison.png`](../results/simulation/scenario_comparison.png)에서 확인할 수 있다. 모두 **가상 모델 출력**이다.

| 시나리오 | 목적 및 입력 조건 | RMS `e_y` (m) | 최대 `|e_y|` (m) | 최대 `|e_psi|` (rad) | 최대 `|r|` (rad/s) | 최대 `|δ|` (deg) | 포화 (샘플) | 정착 (s) | 최종 `e_y` (m) |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 직선 복원 | 초기 `e_y=+0.02 m`, `e_psi=+0.01 rad`, 10 m/s; 작은 직선 오차 복원 | 0.003795 | 0.020486 | 0.016778 | 0.143757 | 7.491 | 0 | 0.2 | -0.000037 |
| 일정 곡률 | `kappa=0.003 1/m`, 10 m/s; 곡선 추종 | 0.009925 | 0.050000 | 0.043502 | 0.300134 | 18.814 | 0 | 1.0 | -0.003975 |
| 큰 초기 오차 | 초기 `e_y=+0.15 m`, `e_psi=+0.05 rad`, 10 m/s; 포화/복원 | 0.025533 | 0.154836 | 0.111653 | 0.804166 | 30.000 | 4 | 1.9 | -0.000096 |
| 속도 7→15 m/s | 10초 linear speed ramp; 속도 변경 중 응답 | 0.007267 | 0.050000 | 0.029615 | 0.256826 | 14.937 | 0 | 0.2 | -0.000116 |
| 노이즈+외란 | 초기 `+0.05 m/+0.02 rad`; 측정 noise 및 `300 N` 횡외란 | 0.025009 | 0.050000 | 0.046173 | 0.436017 | 23.829 | 0 | 실패 | +0.022640 |
| 노이즈 없는 비교 | 같은 초기조건에 noise/외란 제거; 비교 기준 | 0.008993 | 0.050000 | 0.039683 | 0.320051 | 17.432 | 0 | 1.0 | -0.000076 |
| 방향지시등/차선 변경 | 10 m/s; 3.5 m reference offset, 3–7 s quintic transition | 0.008401 | 0.019469 | 0.019602 | 0.171029 | 4.384 | 0 | 해당 없음 | +0.000238 |

### 해석

1. 직선·일정 곡률·속도 ramp 예제에서는 모델 내부의 횡오차가 감소했다. 이를 실제 자동차 안정성의 증명으로 해석할 수는 없다.
2. 큰 초기 오차 케이스에서 처음 4개 제어 샘플의 조향 명령이 ±30°에 포화되었다. 최대 횡오차는 초기 위치 자체보다 약간 크며 overshoot는 0.054317 m였다.
3. 노이즈와 외란을 동시에 가한 결과는 동일 초기조건의 무노이즈 케이스보다 RMS가 약 2.78배 컸다. 센서 노이즈 효과와 물리 외란 효과를 분리한 실험은 아니며, 오차가 끝까지 2 cm 안에 유지되지 않아 정착 시간도 산출하지 못했다.
4. 차선 변경 케이스의 기준 오프셋은 3.5 m에 도달했고, 최대 경로 추종 오차는 0.019469 m였다. 이 수치는 완전 관측 가능한 이상 모델에서 생성된 결과이며, 카메라 인식이나 실제 차선 변경 주행 증거가 아니다.
5. 이 보고서에서는 PID 게인 sweep이나 gain tuning 완료를 주장하지 않는다. 원본 게인의 단위와 제어기 출력 해석이 확인되지 않았고, 단일 게인 세트만 사용했다.

초기 오차 0.15 m 조건의 큰 초기 오차 시나리오를 기준 시뮬레이션으로 삼았다. 기준 시나리오 결과 원시 로그/그래프는 `reference_simulation.csv`와 `reference_simulation.png`에 별도로 저장되어 있다.

## 8. 검증 기록

[`tests/test_lkas_reference.m`](../tests/test_lkas_reference.m)는 일곱 시나리오를 실행해 유한한 출력, 조향 포화 준수, 직선/곡선 오차 기준, 속도 변화, 노이즈 영향 및 방향지시등/상태/차선 오프셋을 확인한다. MATLAB R2016a에서 **“All 7 LKAS reference scenario checks passed.”**를 확인했다. 결과 CSV/PNG 생성도 실행했다.

검사 통과 범위는 코드의 결정론적 시뮬레이션 조건에 한정된다. 별도의 차량 동역학 검증 데이터, 원본 Simulink 비교, 통계적 강건성 시험, 코드생성/실시간 측정 및 차량 시험은 없다.

재현:

```matlab
addpath(fullfile(pwd, 'lkas-control-mini-car', 'matlab'));
run_lkas_suite
```

자동 검사:

```matlab
run(fullfile(pwd, 'lkas-control-mini-car', 'tests', 'test_lkas_reference.m'));
```

## 9. 미니카 관련 프로젝트 자료

Raspberry Pi 5, Picamera2, OpenCV Canny 기반 차선 검출과 GPIO PWM 기반 좌우 모터 속도 제어에 관한 사진 및 설명은 [LKAS 프로젝트 README](../README.md#09-undergraduate-mini-car-project)에 정리했다.

이 절의 MATLAB 평가 지표는 미니카 실측값이 아닌 시뮬레이션 값이다.

<sub>사진·기술 설명 출처: [공개 프로젝트 기록](https://velog.io/@firstclass9903/110-scale-raspberrypi5-%EA%B8%B0%EB%B0%98-%EC%9E%90%EC%9C%A8%EC%A3%BC%ED%96%89-%ED%94%84%EB%A1%9C%EC%A0%9D%ED%8A%B8). 사진에 표시된 장비와 영상 처리 과정은 MATLAB 제어 시뮬레이션과 별개의 자료입니다.</sub>
