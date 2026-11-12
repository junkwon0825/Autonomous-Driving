# LKA Control Project Evidence

국민대학교 자동차IT융합 전공 과정에서 수행한 Lane Keeping Assistant System 제어 프로젝트 정리입니다.

## Project Scope

차량이 차선 중앙을 유지하도록 횡방향 편차와 상대 Yaw Angle을 0에 가깝게 만드는 제어 구조를 설계하고 MATLAB/Simulink·Stateflow 환경에서 검증했습니다.

## Control Structure

- Bicycle Model 기반 횡방향 차량 모델
- Lateral Error PID Controller
- Yaw Error PID Controller
- 조향각 제한 및 상태 로직
- Lane Keeping / Lane Change 시나리오

```text
Lane / Reference
      ↓
Lateral Error + Yaw Error
      ↓
PID Controllers
      ↓
Steering Command
      ↓
Bicycle Vehicle Model
      ↓
Vehicle Response
```

## Vehicle Parameters

| Parameter | Value |
|---|---:|
| Vehicle mass | 2045 kg |
| Yaw inertia | 5428 kg·m² |
| Front CG distance | 1.488 m |
| Rear CG distance | 1.712 m |
| Wheelbase | 3.2 m |
| Front cornering stiffness | 38,925 N/rad |
| Rear cornering stiffness | 38,255 N/rad |
| Steering time constant | 0.1 s |
| Max steering angle | 30° |

## Controller

- Lateral PID: Kp 4.0 / Ki 0.1 / Kd 0.2
- Yaw PID: Kp 3.0 / Ki 0.1 / Kd 0.3
- Error gain: 6000

## Scenarios

- 직선 구간
- 곡선 구간
- S자 구간
- 회전 구간
- Lane Keeping / Lane Change 상태 전환

## Result

발표 결과 기준:

- Lateral Offset: **+10.67 / -13.64 cm**
- Yaw Error: **+5.53 / -4.64°**

## Evidence

원본 발표자료는 Autonomous Driving Control System Design — Lane Keeping Assistant System이며, 프로젝트 발표 자료에서 PID Controller, Bicycle Model, 시스템 구성, Lane Keeping Scenario를 확인할 수 있습니다.

현재 GitHub에는 재현 가능한 설명 문서와 Python 기반 차량 모델 학습 코드를 먼저 공개합니다. 원본 Simulink 모델은 공개 가능 여부를 확인한 뒤 별도 추가합니다.

## Connection to Current Study

이 프로젝트에서 경험한 Bicycle Model·PID 기반 횡방향 제어를 현재 개인 자율주행 학습 저장소에서 Python으로 다시 구현하고, 최종적으로 CARLA 차량 제어에 연결하는 것을 목표로 합니다.
