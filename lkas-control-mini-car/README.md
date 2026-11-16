# LKAS Control + Mini Car

학부 시절 LKA 제어 프로젝트를 근거 자료와 구분해 정리하고, 새 차량 제어 참조 모델과 재현 가능한 시뮬레이션을 구성하는 프로젝트입니다. 미니카 확장은 실제 부품/시험 정보가 생기기 전까지 설계안과 구현 범위를 분리해 관리합니다.

> **증거 범위:** 기존 저장소의 [`LKAS_PROJECT.md`](../LKAS_PROJECT.md)는 과거 프로젝트에 대한 요약 기록입니다. 원본 MATLAB/Simulink 모델, 발표 파일, 실행 로그는 확인되지 않았습니다. 이 저장소의 MATLAB 모델/결과는 기록된 일부 후보 파라미터를 사용해 새로 만든 시뮬레이션이며 원본 복원본이 아닙니다. 실제 하드웨어 시험은 하지 않았습니다. 자세한 내용은 [설계·시뮬레이션 보고서](docs/design-report.md)를 참조하세요.

## 기존 기록과 확인되지 않은 점

| 구분 | 기존 요약 문서에 기록 | 원본으로 확인해야 할 사항 |
|---|---|---|
| 제어 구조 | Bicycle Model, 횡/Yaw PID, 조향 제한 및 상태 로직 | 신호 연결, 부호, 좌표계, 오차 결합식 |
| 차량 | 질량 2045 kg, 요 관성 5428 kg·m², CG-축 거리 1.488/1.712 m, wheelbase 3.2 m | 모델 유형 및 파라미터 원출처 |
| 타이어 | 전/후 cornering stiffness 38925/38255 | 차축 합산값인지 타이어당 값인지, 실제 단위 |
| 제어 | Lateral PID 4/0.1/0.2, Yaw PID 3/0.1/0.3, Error gain 6000 | PID 단위, 결합법, Error gain 적용 위치 |
| 제한/주기 | 조향 제한 30°, 기록된 시간 0.1 s | 전륜각인지 운전대각인지, 샘플주기인지 액추에이터 시정수인지 |
| 결과 | 발표 결과 횡방향 +10.67/-13.64 cm, Yaw +5.53/-4.64° 기록 | 원시 로그/조건/지표 정의 및 결과 재현 |

발표 수치는 기존 요약의 **기록**일 뿐, 본 작업에서 원본을 재실행해 확인한 결과가 아닙니다.

## MATLAB 실행 및 결과

MATLAB script/function만으로 선형 Dynamic Bicycle Model과 두 오차 PID를 연결했습니다. 코드는 Simulink/Stateflow나 추가 Toolbox를 사용하지 않습니다. MATLAB R2016a (9.0.0.341360)에서 실행했고, Simulink 및 Control System Toolbox 제품/라이선스 사용 가능 여부도 확인했습니다.

저장소 루트에서 전체 7개 시나리오를 실행하고 CSV/그래프를 다시 만들려면:

```matlab
addpath(fullfile(pwd, 'lkas-control-mini-car', 'matlab'));
run_lkas_suite
```

자동 검사:

```matlab
run(fullfile(pwd, 'lkas-control-mini-car', 'tests', 'test_lkas_reference.m'));
```

MATLAB R2016a에서 **7개 시나리오 검사가 통과**했습니다. 실행 결과:

| 시나리오 | RMS 횡오차 (m) | 최대 횡오차 (m) | 조향 포화 (샘플) |
|---|---:|---:|---:|
| 직선 복원 | 0.003795 | 0.020486 | 0 |
| 일정 곡률 | 0.009925 | 0.050000 | 0 |
| 큰 초기 오차 | 0.025533 | 0.154836 | 4 |
| 속도 7→15 m/s | 0.007267 | 0.050000 | 0 |
| 노이즈+외란 | 0.025009 | 0.050000 | 0 |
| 방향지시등/차선 변경 | 0.008401 | 0.019469 | 0 |
| 노이즈 없는 비교 | 0.008994 | 0.050000 | 0 |

**위 값은 가상 모델의 시뮬레이션 결과이지 원본 프로젝트 결과나 미니카 실측 결과가 아닙니다.** 전체 지표 [CSV](results/simulation/scenario_metrics.csv), 시계열 [CSV](results/simulation/scenario_timeseries.csv), [비교 그래프](results/simulation/scenario_comparison.png)를 확인하세요. 모델 가정, 계산식, 해석 및 한계는 [보고서](docs/design-report.md)를 참조하세요.

## 신규 시뮬레이션 범위

- 직선 차로 초기 오차 복원
- 일정 곡률 차로
- 큰 초기 횡/헤딩 오차와 조향 포화
- 7→15 m/s 속도 ramp
- 결정론적 측정 노이즈 및 횡방향 외란
- 방향지시등/차선 변경 예시 state logic
- 같은 초기조건의 무노이즈 비교 시나리오

전륜 조향각/강성 해석, 게인 단위 및 모델 유효 범위는 미확정 가정으로 보고서에 명시했습니다. 과거 요약에 있는 Error gain 6000은 적용하지 않았습니다. 게인 sweep, Simulink 모델, 카메라 차선인식, 펌웨어, 센서 latency, 실측/track 시험은 수행하지 않았습니다.

## 미니카 확장 설계

```text
제안 (미구현)
Camera → Raspberry Pi 영상처리/상위제어 → MCU watchdog/저수준제어
       → servo + 모터 구동 → 실내 track 로그
```

주신 [Raspberry Pi 미니카 참고 글](https://velog.io/@firstclass9903/110-scale-raspberrypi5-%EA%B8%B0%EB%B0%98-%EC%9E%90%EC%9C%A8%EC%A3%BC%ED%96%89-%ED%94%84%EB%A1%9C%EC%A0%9D%ED%8A%B8)의 OpenCV Canny/차선 중심 사례를 아이디어로 참조했습니다. 해당 글의 구현·성능은 이 프로젝트에서 검증하지 않았습니다. 부품 후보와 구매 전 입력, 제안 통신 인터페이스, 안전 시험 계획은 [미니카 설계안](docs/mini-car-architecture.md)에 정리했습니다. 하드웨어와 실험은 미구현/미실시입니다.

## 현재 단계

| 단계 | 상태 |
|---|---|
| 저장소 내 LKAS 기록 점검 | 요약 문서 확인; 원본 자료 없음 |
| 신규 MATLAB 차량/제어 참조 모델 | 구현, 시나리오 실행, 자동 검사 통과 |
| 원본 모델/Stateflow 복원 | 원본 자료 확보 필요 |
| 신규 Simulink 모델 | 미작성 |
| 미니카 인터페이스/하드웨어 설계 문서 | 제안 문서 작성; 부품 미선정 |
| 카메라, MCU firmware, 실물 차량 | 미구현; 보유 장비/사양 정보 미확인 |
| 통제 트랙 시험/Simulation-to-Real | 미실시 |

## 프로젝트 문서

- [설계·시뮬레이션 보고서](docs/design-report.md)
- [미니카 시스템 설계안](docs/mini-car-architecture.md)
- [시나리오 조건](simulation/scenarios.md)
- [요구사항/검증 추적표](docs/requirements-and-traceability.md)
- [기술면접 설명](docs/technical-interview.md)
- [원본 자료 상태](original/README.md)
- [MATLAB 구현](matlab/)
- [자동 검사](tests/)
- [실행 결과](results/simulation/)

하드웨어/인지 코드는 실제 장비에서 만들고 확인하기 전까지 빈 폴더나 성공으로 오해할 placeholder를 만들지 않았습니다. ISO 26262 인증이나 양산 ADAS 기능안전 수행을 주장하지 않습니다.
