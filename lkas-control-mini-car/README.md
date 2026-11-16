# LKAS Control + Mini Car

학부 시절 LKA 제어 프로젝트를 근거 자료와 구분해 복원하고, 이후 소형 자율주행 차량으로 확장하기 위한 독립 프로젝트입니다. 목표는 모델링, 제어 구현, 재현 가능한 시험과 결과 분석을 한 저장소에서 추적하는 것입니다.

> **현재 범위:** 기존 저장소의 [`LKAS_PROJECT.md`](../LKAS_PROJECT.md)에 기록된 프로젝트 요약을 근거로 정리했습니다. 원본 MATLAB/Simulink 모델, 발표 파일, 실행 로그는 현재 저장소에서 확인되지 않았습니다. 따라서 아래 최소 시뮬레이션은 과거 모델의 복원본이 아니라 후보 파라미터를 사용한 별도 참조 구현입니다. 실제 하드웨어 시험은 수행하지 않았습니다.

## 현재 확인된 내용과 미확인 사항

| 구분 | 저장소 문서에서 확인한 기록 | 원본으로 재확인할 사항 |
|---|---|---|
| 제어 구조 | Bicycle Model, 횡방향 오차 PID, Yaw 오차 PID, 조향 제한 및 상태 로직 | 블록 연결, 부호/좌표계, 오차 결합식 |
| 차량 파라미터 | 질량 2045 kg, 요 관성 5428 kg·m², CG-전/후륜 거리 1.488/1.712 m, 휠베이스 3.2 m | 파라미터 출처와 적용 모델 |
| 타이어 파라미터 | 전/후 코너링 강성 38925/38255로 기록 | 축 합산값인지 타이어당 값인지, 실제 단위 |
| 제어 파라미터 | 횡 PID 4.0/0.1/0.2, Yaw PID 3.0/0.1/0.3, Error gain 6000 | PID 시간/출력 단위, Error gain 적용 위치 |
| 제한/주기 | 조향 제한 30°, 기록된 시간상수 0.1 s | 전륜 조향각인지 핸들각인지, 0.1 s가 샘플링 시간인지 조향 액추에이터 시정수인지 |
| 시나리오/결과 | 직선·곡선·S자·회전 및 상태 전환; 발표 결과 Lateral Offset +10.67/-13.64 cm, Yaw Error +5.53/-4.64° | 원본 실행 조건, 지표 정의, 원시 로그 및 그래프 |

위 결과 수치는 기존 요약 문서에 옮겨진 **발표 결과 기록**이며, 현재 재실행해 검증한 결과가 아닙니다.

## 재현용 MATLAB 실행 경로

현재 제공하는 모델은 상수 속도 선형 Dynamic Bicycle Model, 직선 기준 경로, 횡방향/헤딩 PID를 연결한 교육·검토용 참조 구현입니다. 기록된 게인과 파라미터를 사용하되, 축 코너링 강성 및 30°를 전륜 조향각으로 해석하는 등 확인되지 않은 선택은 코드와 문서에서 가정으로 표시했습니다. 불명확한 Error gain 6000은 제어식에 임의로 적용하지 않습니다.

- MATLAB script/function만 사용합니다.
- Simulink, Stateflow 및 별도 Toolbox 의존성은 없습니다.
- 확인 환경: MATLAB R2016a (9.0.0.341360), Simulink 설치/라이선스 사용 가능, Control System Toolbox 설치/라이선스 사용 가능. 본 스크립트 실행에는 두 Toolbox가 필요하지 않습니다.
- MATLAB에서 저장소 루트로 이동한 뒤 실행합니다:

```matlab
addpath(fullfile(pwd, 'lkas-control-mini-car', 'matlab'));
run_lkas_demo
```

수치 로그 CSV와 그래프 PNG는 실행 시 `lkas-control-mini-car/results/simulation/`에 생성됩니다. 아래 결과는 위에 명시한 참조 시나리오를 MATLAB R2016a에서 실제 실행한 값이며, 과거 원본 결과나 미니카 실측 결과가 아닙니다.

| 지표 | 참조 시뮬레이션 결과 |
|---|---:|
| RMS 횡방향 오차 | 0.025533 m |
| 최대 절대 횡방향 오차 | 0.154836 m |
| 최대 절대 헤딩 오차 | 0.111653 rad |
| 최대 절대 요레이트 | 0.804166 rad/s |
| 최대 조향 명령 | 30.0° |
| 조향 포화 샘플 | 4 / 101 |
| 10초 시점 횡방향 오차 | -0.000096 m |

[실행 CSV](results/simulation/reference_simulation.csv) · [오차/조향 그래프](results/simulation/reference_simulation.png)

자동 검사:

```matlab
addpath(fullfile(pwd, 'lkas-control-mini-car', 'matlab'));
run(fullfile(pwd, 'lkas-control-mini-car', 'tests', 'test_lkas_reference.m'));
```

위 기본 MATLAB 검사와 결과 생성은 해당 실행 환경에서 통과했습니다. Simulink/Stateflow 원본 모델을 실행하거나 복원한 것은 아닙니다.

## 시스템 경계와 단계

```text
현재 참조 시뮬레이션
차량 파라미터 → Dynamic Bicycle Model → PID → 전륜 조향 명령

향후 미니카 (미구현)
카메라 → 차선 인식 → 횡/헤딩 오차 → 상위 제어기
       → MCU 안전 로직 → 조향/모터 구동 → 실험 로그
```

미니카 확장 아이디어는 [참고 프로젝트](https://velog.io/@firstclass9903/110-scale-raspberrypi5-%EA%B8%B0%EB%B0%98-%EC%9E%90%EC%9C%A8%EC%A3%BC%ED%96%89-%ED%94%84%EB%A1%9C%EC%A0%9D%ED%8A%B8)의 Raspberry Pi 5/Picamera2, OpenCV Canny, 차선 중심 편차, 저편차 deadband, 차등 모터 속도 제어 사례를 참고합니다. 해당 글의 구현·성능은 이 프로젝트에서 직접 수행하거나 검증한 결과가 아닙니다. 실제 부품/조향 구조/전원/안전 계획은 장비와 예산 확인 전까지 미정입니다.

| 단계 | 상태 |
|---|---|
| 저장소 내 LKAS 기록 정리 및 원본 파일 확인 | 요약 문서만 확인; 원본 자료 미확보 |
| 후보 파라미터 기반 MATLAB 참조 시뮬레이션 | 코드 초안; MATLAB 실행/결과 검증 대기 |
| 원본 모델 복원 및 원본 시나리오 재현 | 원본 파일 확보 필요 |
| Simulink/Stateflow 모델 | 미구현 |
| 미니카 하드웨어/인지/제어 | 미구현; 하드웨어 미보유 정보 |
| 통제된 트랙 시험 및 Simulation-to-Real 비교 | 미실시 |

## 문서 및 디렉터리

- [`original/README.md`](original/README.md): 원본 자료 요청 및 상태
- [`matlab/`](matlab/): MATLAB 참조 모델과 실행 진입점
- [`simulation/`](simulation/): 시나리오 정의
- [`docs/requirements-and-traceability.md`](docs/requirements-and-traceability.md): 요구사항, 인터페이스 및 검증 추적
- [`docs/technical-interview.md`](docs/technical-interview.md): 확인된 근거와 미검증 항목을 구분한 기술 설명
- [`tests/`](tests/): MATLAB 기본 검사
- [`results/simulation/`](results/simulation/): 실행 시 생성되는 CSV/그래프

`simulink/`, `control/`, `perception/`, `embedded/`, `hardware/`, `experiments/`는 구현 자료가 생기기 전까지 빈 폴더로 만들지 않았습니다.

## 다음에 필요한 자료

1. 학부 발표 PDF/PPT, `.m`/`.slx`/`.mdl`/`.mat` 원본과 실행 당시 MATLAB/Toolbox 정보
2. 원본 차량 파라미터 표, PID 블록 설정, Stateflow 전이 및 시뮬레이션 로그
3. 현재 보유한 Raspberry Pi/카메라/MCU/모터/조향부품, 예산 및 전원 정보
4. MATLAB에서 위 실행 및 검사 명령을 수행한 로그

기능안전이나 ISO 26262 인증을 수행했다고 주장하지 않습니다. 실제 주행은 통제된 실내 저속 시험만 대상으로 하며, 원본과 실험 자료가 확보된 뒤에 다음 단계로 진행합니다.
