# 학부 LKAS 프로젝트 — 기존 저장소 요약 기록

> **증거 상태:** 이 문서는 저장소에 먼저 남아 있던 학부 프로젝트 요약 기록이다. 원본 `.slx`/`.m`/Stateflow chart, 발표자료, 원시 실행 로그는 현재 확인되지 않았다. 아래 내용은 과거 활동을 입증하는 2차 기록으로 보존하며, 원본 프로젝트의 상세 구조/수치/결과를 독립 검증한 사실로 간주하지 않는다. 새로 실행한 MATLAB 모델은 [별도 LKAS 포트폴리오](lkas-control-mini-car/README.md)에 구분해 둔다.

## 프로젝트 배경

저장소 요약에는 국민대학교 자동차IT융합 전공 과정에서 Lane Keeping Assistant System 제어를 학습/구성한 이력이 기록되어 있다. 차량 횡방향 오차와 상대 heading/yaw 오차를 줄이는 LKA 구조를 MATLAB/Simulink 및 Stateflow로 다뤘다고 요약되어 있으나, 원본 파일이 없어 모델 블록/차트와 당시 구체적인 개인 역할은 다시 확인할 수 없다.

## 기존 기록에 기재된 제어 구조

- Bicycle Model 기반 차량 횡방향 모델
- Lateral Error 및 Yaw Error PID 기록
- Steering angle 제한 및 상태 로직 기록
- Lane Keeping/Lane Change 시나리오 기록

이 목록은 현재 확보된 2차 프로젝트 요약의 설명이며, 이번 repository revision에서 실제 Simulink/Stateflow를 재실행한 결과가 아니다.

## 기록된 후보 파라미터

| Parameter | 기존 요약에 기록된 값 | 해석 유의사항 |
|---|---:|---|
| Vehicle mass | 2045 kg | 원본 파라미터 출처 미확인 |
| Yaw inertia | 5428 kg·m² | 원본 파라미터 출처 미확인 |
| Front/Rear CG distance | 1.488 m / 1.712 m | CG에서 축까지 거리라는 기존 표기 |
| Wheelbase | 3.2 m | 위 두 거리의 합과 일치 |
| Front/Rear cornering stiffness | 38,925 / 38,255 | N/rad로 기록; axle-total인지 tire 단위인지 미확인 |
| `0.1 s` | “Steering time constant”로 기록 | Controller sample time 또는 actuator time constant인지 미확인 |
| Maximum steering | 30° | 전륜 road-wheel 각인지 steering-wheel 각인지 미확인 |

## 기록된 PID 값

- Lateral PID: `Kp=4.0`, `Ki=0.1`, `Kd=0.2`
- Yaw PID: `Kp=3.0`, `Ki=0.1`, `Kd=0.3`
- `Error gain=6000` 기재

게인의 단위, 출력 스케일, 두 제어 루프의 결합 위치 및 `Error gain`의 적용 블록은 확인되지 않았다. 이 숫자들을 원본과 동일한 제어기에 적용됐다고 입증할 `.slx`/`.m`은 없다.

## 기존 요약에 기재된 시나리오와 발표 수치

직선·곡선·S자·회전 및 Lane Keeping/Lane Change 상태 전환이 기록되어 있다. 발표 결과로 횡방향 offset `+10.67/-13.64 cm`, yaw error `+5.53/-4.64°`가 기재되어 있다. 정의/시험 조건/원시 로그를 확인하지 못했으므로 [`lkas-control-mini-car/results/simulation/`](lkas-control-mini-car/results/simulation/)의 신규 참조 모델 수치와 혼합하거나 재현 성공으로 표현하지 않는다.

## 증빙 및 복원 범위

- 과거 요약의 출처와 프로젝트 제목은 “Autonomous Driving Control System Design — Lane Keeping Assistant System”으로 적혀 있다. 발표 파일 자체는 현재 저장소에 없다.
- 과거 미니카 사진/장비/당시 역할 기록은 [`lkas-control-mini-car/original/mini-car/`](lkas-control-mini-car/original/mini-car/)에 추가한다. 현재 내용은 증빙 안내만 있다.
- 새 MATLAB Dynamic Bicycle Model, PID, scenario, 그래프와 CSV는 현재 코드에 근거한 **신규 재구현/검증 자료**다. 원본 Simulink/Stateflow 복원 결과가 아니다.
