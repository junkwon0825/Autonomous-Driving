# LKAS — 차량 횡방향 제어 학습 및 프로젝트 기록

## 개요

자동차 제어 학습에서 다룬 LKA, Bicycle Model, 횡방향·Heading 오차 기반 조향 제어를 정리한 프로젝트 기록입니다. 실행 코드와 정량 시뮬레이션 결과는 [LKAS Control 프로젝트](lkas-control-mini-car/README.md)에서 확인할 수 있습니다.

## 주요 제어 요소

- 차량 횡방향 및 Yaw 동역학
- Lateral/Heading Error PID 조향 제어
- 조향 명령 제한 및 차선 추종 시나리오
- MATLAB 시뮬레이션을 이용한 제어 응답 분석

## 차량 파라미터

| 항목 | 모델 설정값 |
|---|---:|
| 차량 질량 | 2045 kg |
| Yaw 관성모멘트 | 5428 kg·m² |
| 전륜/후륜 CG 거리 | 1.488 m / 1.712 m |
| Wheelbase | 3.2 m |
| 전륜/후륜 Cornering Stiffness | 38,925 / 38,255 N/rad (차축 기준 모델 가정) |
| 제어주기 | 0.1 s (시뮬레이션 설정) |
| 최대 조향각 | ±30° (전륜 기준 모델 가정) |

## PID 파라미터

| 제어 루프 | Kp | Ki | Kd |
|---|---:|---:|---:|
| Lateral | 4.0 | 0.1 | 0.2 |
| Heading | 3.0 | 0.1 | 0.3 |

위 설정을 이용한 실제 구현 수식, 단위 및 시험 결과는 [설계 보고서](lkas-control-mini-car/docs/design-report.md)에 명시했습니다.

## 프로젝트 결과

- [7개 주행 시나리오 및 성능 비교](lkas-control-mini-car/README.md#05-simulation-scenarios)
- [시뮬레이션 지표 CSV](lkas-control-mini-car/results/simulation/scenario_metrics.csv)
- [미니카 관련 이미지 자료](lkas-control-mini-car/original/mini-car/)
