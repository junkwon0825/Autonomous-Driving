# Autonomous Driving Study & CARLA Integration

자율주행 소프트웨어를 **통신 → 차량 모델 → 제어 → 인지 → 시뮬레이션 통합** 순서로 학습하고 직접 구현하기 위한 개인 저장소입니다.

최종 목표는 개별 알고리즘을 따로 실행하는 데서 끝내지 않고, **CARLA에서 Perception–Decision–Control이 연결되는 개인 자율주행 프로젝트**로 통합하는 것입니다.

> 학습 중인 내용과 실제 구현이 끝난 내용은 구분해서 관리합니다. 빈 placeholder 폴더는 만들지 않고, 코드가 생긴 단계만 저장소에 추가합니다.

## Current Implementation

### 1. CAN / Vehicle Agent

현재 가장 먼저 구현한 영역입니다.

```text
Virtual ECU
   ↓
CAN / DBC
   ↓
Vehicle Data Service
   ↓
Vehicle Tools
   ↓
LLM Agent
```

구현 내용:

- CAN Frame / Signal Decode
- DBC + cantools
- SocketCAN / vcan
- Multi ECU Simulation
- Vehicle State Cache
- Vehicle Tool / Tool Router
- LLM Tool Calling
- Safety Layer
- Vehicle Command Service

코드: [01_can_basics](01_can_basics)

### 2. Vehicle Model

Bicycle Model을 직접 구현하며 차량의 위치·heading 변화와 steering 입력의 관계를 학습하고 있습니다.

코드: [01_vehicle_model](01_vehicle_model)

## Learning Roadmap

다음 순서로 실제 코드가 완성될 때마다 저장소에 추가합니다.

```text
CAN / DBC
    ↓
Vehicle Model
    ↓
PID / Lateral Control
    ↓
Pure Pursuit / Stanley
    ↓
Path Planning
    ↓
State Estimation
    ↓
Lane / Object Perception
    ↓
CARLA Integration
```

### Control
- PID lateral control
- Pure Pursuit
- Stanley Controller
- 기존 MATLAB/Simulink LKA 경험과 Python 구현 비교

### Planning / Estimation
- A*
- Kalman Filter / EKF
- waypoint 및 trajectory 처리

### Perception
- Lane Detection / Lane Segmentation
- Object Detection
- Camera 기반 차량 주변 환경 인식

## Final Personal Project — CARLA

학습 단계의 최종 결과물은 CARLA 기반 통합 자율주행 프로젝트로 구성할 계획입니다.

```text
CARLA Camera / Vehicle State
          ↓
      Perception
          ↓
Planning / Decision
          ↓
      Controller
          ↓
Throttle / Brake / Steering
          ↓
      CARLA Vehicle
```

목표 기능:

- CARLA 차량 및 센서 연결
- 카메라 기반 차선/객체 인지
- waypoint 기반 경로 추종
- lateral / longitudinal control
- 주행 로그 및 성능 지표 기록
- 실패 시나리오 분석

CARLA 통합 코드가 실제로 구현되면 별도 디렉터리로 추가하고, 이 README에서 결과 영상·성능·아키텍처를 연결합니다.

## Relation to Other Projects

이 저장소는 **개인 자율주행 학습 및 CARLA 통합 프로젝트** 전용입니다.

Furiosa NPU를 활용하는 최종 팀 프로젝트는 팀 프로젝트가 본격적으로 시작된 뒤 **별도 GitHub Repository**로 분리해 관리합니다. 개인 학습 코드와 팀 결과물을 섞지 않습니다.

## Repository Structure

```text
Autonomous-Driving/
├── 01_can_basics/
│   ├── README.md
│   ├── can_basic.py
│   ├── can_sender.py
│   ├── can_receiver.py
│   ├── signal_decode.py
│   ├── dbc_decode.py
│   ├── vehicle.dbc
│   └── multi_ecu/
│       ├── powertrain_ecu.py
│       ├── battery_ecu.py
│       ├── steering_ecu.py
│       ├── body_ecu.py
│       ├── vehicle_data_service.py
│       ├── vehicle_tools.py
│       ├── tool_router.py
│       ├── llm_agent.py
│       ├── safety_layer.py
│       └── vehicle_command_service.py
├── 01_vehicle_model/
│   └── bicycle_model.py
└── README.md
```

## Environment

- Python
- Windows / WSL2 Ubuntu
- python-can
- cantools
- SocketCAN / vcan
- NumPy
- Git / GitHub

추후 CARLA 통합 단계에서 CARLA Python API, OpenCV, PyTorch 등을 추가합니다.
