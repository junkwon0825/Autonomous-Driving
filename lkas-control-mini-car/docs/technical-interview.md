# LKAS 기술면접 대비

답변은 현재 MATLAB 코드와 실행 CSV에 근거한다. 학부 원본 모델/미니카 사진은 제공되지 않았으므로 과거 구현·역할을 현재 재구현 결과와 혼합하지 않는다.

## 1. Bicycle Model이란 무엇인가?

전후 차축을 자전거의 전·후륜 하나씩으로 단순화해 조향과 차량 경로/횡방향 움직임을 표현하는 모델 계열이다. 현재 `lkas_reference_simulation.m`은 `v_y`, yaw rate, 횡오차, heading 오차를 상태로 두고 타이어 횡력을 계산하는 Dynamic Bicycle Model이다.

## 2. Kinematic Model과 Dynamic Model의 차이는?

Kinematic 모델은 힘/질량을 직접 계산하지 않고 저속·무슬립에 가까운 기하 관계로 경로를 구한다. Dynamic 모델은 `m`, `I_z`, `C_f`, `C_r`로 횡속도 및 yaw rate 과도 응답을 계산한다. 이번 재구현은 후자이며, 선형 타이어 및 소슬립을 가정한다.

## 3. Lateral Error와 Heading Error의 차이는?

`e_y [m]`는 차량 위치와 기준 경로의 횡방향 오프셋이고, `e_psi [rad]`는 차량 heading에서 기준 경로 heading을 뺀 상대각이다. 코드의 근사식은 `e_y_dot = v_y + v_x e_psi`, `e_psi_dot = r - v_x kappa`다. 카메라에서 계산한 오차는 아니다.

## 4. PID를 선택한 이유는?

학부 프로젝트 요약에 Lateral/Yaw PID 제어를 학습/사용했다는 기록이 있어, 기록된 구조를 출발점으로 단순하고 해석 가능한 참조 제어기를 새로 구성했다. 실제 원본 선택 이유나 게인 조정 이력은 원본 자료가 없어 확인할 수 없다.

## 5. 실제 구현한 제어기의 구조는?

두 discrete PID가 Lateral Error와 Heading Error 각각에 대해 P/I/D를 계산한다. 두 출력을 합산한 뒤 음의 부호를 적용해 하나의 front-road-wheel steering command를 만들고 ±30°에서 포화한다. 포화를 더 키우는 방향의 integral update는 보류한다. Python/Simulink의 PID block을 호출하지 않고 MATLAB 함수 안에서 직접 계산했다.

```text
delta = clip(-(PID_y(e_y) + PID_psi(e_psi)), -30 deg, +30 deg)
```

`Kp/Ki/Kd`는 코드에 모두 사용되지만, 기록 게인의 단위와 두 PID 출력의 조향각 변환 관계는 불명확하다. 따라서 숫자는 신규 참조 구현의 해석이지 검증된 학부 제어기 튜닝값이라는 뜻은 아니다.

## 6. 게인 변화가 조향 응답에 미치는 영향은?

일반적으로 `Kp` 변화는 현재 오차에 대한 조향 민감도, `Ki`는 누적 오차 제거와 포화 시 windup 위험, `Kd`는 오차 변화율에 대한 damping 성향에 영향을 준다. 이번 프로젝트에서는 gain sweep을 실행하지 않았기 때문에 특정 게인 증가에 대한 응답 변화 수치를 주장할 수 없다. 현재 게인으로 큰 초기 오차 케이스에서 조향 제한 4/101 샘플을 기록했다.

## 7. 차량 속도 증가 시 어떤 문제가 발생하는가?

횡/요 동역학 응답과 매 제어주기 사이 이동거리가 변하고, 고정된 제어주기와 게인의 위상여유·오차 특성도 달라질 수 있다. 이번에는 7→15 m/s/10 s 직선 ramp 한 경우를 계산했으나, 단일 가상 조건에서 안정성 한계나 일반 성능을 입증하지 않았다.

## 8. Stateflow는 무엇이며 이번 재구현에서 사용했는가?

Stateflow는 상태·이벤트·전이 기반 로직을 모델링하는 MATLAB/Simulink 도구다. 현재 재구현에는 Simulink/Stateflow 차트가 없다. MATLAB 함수에 정의한 차선 변경 scenario의 mode와 turn-signal 출력만 예시 상태 로직으로 구현했으며, 과거 차트 복원이 아니다.

## 9. 7개 시나리오 중 가장 어려운 조건은 무엇인가?

노이즈와 횡방향 외란을 함께 적용한 조건이 가장 약한 결과를 보였다. RMS `e_y`는 0.025009 m로 동일 초기조건의 무노이즈 비교 0.008993 m보다 컸고, 종료 전까지 0.02 m 정착 기준을 만족하지 않았다. 노이즈와 외란을 동시에 가했으므로 어느 하나의 영향만 분리한 결과는 아니다. 큰 초기 오차 case는 max `|e_y|=0.154836 m`, 조향 saturation 4샘플을 보였다.

## 10. 시뮬레이션과 실제 미니카 사이의 차이는?

실제 미니카는 질량/휠베이스, 타이어 접지, 링크 backlash, 조향 servo, 모터 응답, 카메라 기하와 처리/통신 지연이 모델에 추가된다. 현재는 하드웨어 부품/사진 및 실제 시험 로그가 없어 차이를 측정하지 않았다. 결과는 MATLAB 수치모델 시험이다.

## 11. 미니카를 실제 LKAS 시스템으로 확장하려면 무엇이 필요한가?

먼저 과거 실제 미니카 활동을 사진/문서로 확인한다. 신규 하드웨어 개발이 승인/범위에 포함될 때에만 부품 정격·구동계·안전 정지·통신 인터페이스를 설계하고, 센서/actuator 단위 시험 후 통제된 환경에서 실험한다. 이 포트폴리오 마감 작업에서는 신규 Raspberry Pi/Arduino 개발과 실시간 제어를 범위에서 제외했다.

## 12. 프로젝트에서 본인의 역할과 직접 구현한 부분은?

현재 저장소에서 확인 가능한 재구현 작업에는 Dynamic Bicycle Model, PID 계산/포화, 7개 시나리오, MATLAB 검사, 지표/CSV/그래프 및 문서화가 포함된다. 학부 당시 역할·팀 기여·부품 선택은 사진이나 원본 증빙 및 본인의 확인 설명이 아직 없어 추측하지 않는다. 면접에서는 과거 활동과 현재 새로 구현한 작업을 나누어 설명한다.

## 사용한 핵심 방정식

```text
alpha_f = delta - (v_y + a r) / v_x
alpha_r =             -(v_y - b r) / v_x
F_yf = C_f alpha_f
F_yr = C_r alpha_r
v_y_dot = (F_yf + F_yr + F_disturbance) / m - v_x r
r_dot = (a F_yf - b F_yr) / I_z
e_y_dot = v_y + v_x e_psi
e_psi_dot = r - v_x kappa
```

단위, 부호, 게인 가정, 계산된 전체 지표는 [설계·시뮬레이션 보고서](design-report.md)와 [실행 CSV](../results/simulation/scenario_metrics.csv)를 참조한다.
