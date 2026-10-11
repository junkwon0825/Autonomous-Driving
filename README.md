# Autonomous-Driving

자동차 소프트웨어, CAN 통신, 차량 제어, AI Agent를 하나의 프로젝트로 연결하기 위한 개인 학습 및 구현 프로젝트입니다.

현재는 **Virtual ECU → CAN/DBC → Vehicle Data Service → Vehicle Tool → LLM Agent** 구조를 구현하고 있으며,
이후 ROS2, 차량 모델, 제어 알고리즘, RAG, RC카 하드웨어까지 확장할 예정입니다.

## 1. Project Goal

최종 목표는 **Automotive AI Agent + Vehicle Digital Twin / RC Car** 구조입니다.

```text
User
 │
 ▼
LLM Automotive Agent
 │
 ├── Vehicle Tool
 ├── RAG Tool
 ├── Diagnostic Tool
 └── Navigation Tool
 │
 ▼
Vehicle Data Service
 │
 ├── CAN / DBC
 ├── ROS2
 └── Vehicle State
 │
 ▼
Vehicle Controller
 │
 ├── PID
 ├── Pure Pursuit
 ├── Stanley
 └── Safety Layer
 │
 ▼
Virtual ECU / Raspberry Pi / STM32 / RC Car
```

LLM은 차량을 직접 제어하지 않고 고수준 Tool만 호출하도록 설계합니다.

## 2. Development Environment

- Windows + WSL2 Ubuntu 24.04
- Python virtual environment (`.venv`)
- VS Code
- Python
- python-can
- cantools
- SocketCAN / vcan
- OpenAI-compatible LLM API
- Git / GitHub

향후 추가 예정:
- ROS2 Jazzy
- Qdrant
- PostgreSQL
- Docker
- Raspberry Pi 5
- STM32
- Camera / IMU / Wheel Encoder

## 3. Current Progress

### DAY1 - CAN Frame
- CAN ID, DLC, DATA
- Hex / Byte / Bit
- Python으로 CAN Message 표현

### DAY2 - CAN Signal Decode
- Start Bit / Length
- Signed / Unsigned
- Factor / Offset
- Little Endian / Big Endian
- `Physical Value = Raw Value × Factor + Offset`

### DAY3 - DBC + cantools
```text
Physical Signal → DBC Encode → CAN Raw Bytes
CAN Raw Bytes → DBC Decode → Physical Signal
```

### DAY4 - Virtual CAN
- `vcan0`
- SocketCAN
- `candump`
- `cansend`
- `python-can`

### DAY5 - Multi ECU Simulation
```text
Powertrain ECU ──────┐
Battery ECU ─────────┤
Steering ECU ────────┼──── vcan0
Body ECU ────────────┘
```

```text
0x100 → PowertrainStatus
0x200 → BatteryStatus
0x300 → SteeringStatus
0x400 → BodyStatus
```

### DAY6 - Vehicle Data Service
```text
CAN
 ↓
DBC Decode
 ↓
Vehicle Data Service
 ↓
get_vehicle_speed()
get_battery_soc()
get_steering_angle()
get_vehicle_state()
```

추가 구현:
- Background Thread CAN Receiver
- `threading.Lock`
- Vehicle State Cache
- Signal Timestamp
- Stale Signal 검사

### DAY7 - Vehicle Tool Layer
```text
Vehicle Data Service
        ↓
Vehicle Tools
        ↓
Tool Router
        ↓
Agent
```

### DAY8 - LLM Tool Calling
```text
User
 ↓
LLM
 ↓
Tool Selection
 ↓
Tool Router
 ↓
Vehicle Tool
 ↓
Vehicle Data Service
 ↓
CAN / DBC
 ↓
ECU
```

### DAY9 - Vehicle Control + Safety Layer

첫 제어 기능:
```text
set_hvac_temperature(temperature)
```

구조:
```text
User
 ↓
LLM
 ↓
set_hvac_temperature(24)
 ↓
Vehicle Tool
 ↓
Safety Layer
 ↓
Vehicle Command Service
 ↓
DBC Encode
 ↓
CAN 0x410
 ↓
Body ECU
```

Safety Layer:
```text
16°C ~ 30°C → 허용
그 외 값      → 거부
```

설계 원칙:
> LLM이 직접 CAN Frame 또는 저수준 Actuator 값을 생성하지 않는다.

## 4. Current Folder Structure

```text
Autonomous-Driving/
│
├── 01_can_basics/
│   ├── can_basic.py
│   ├── can_sender.py
│   ├── can_receiver.py
│   ├── dbc_decode.py
│   ├── signal_decode.py
│   ├── vehicle.dbc
│   │
│   └── multi_ecu/
│       ├── battery_ecu.py
│       ├── body_ecu.py
│       ├── common.py
│       ├── powertrain_ecu.py
│       ├── steering_ecu.py
│       ├── vehicle.dbc
│       ├── vehicle_monitor.py
│       ├── vehicle_data_service.py
│       ├── vehicle_tools.py
│       ├── tool_router.py
│       ├── manual_agent.py
│       ├── llm_agent.py
│       ├── safety_layer.py
│       └── vehicle_command_service.py
│
├── 02_vehicle_model/
├── 03_pid_tracking/
├── 04_pure_pursuit/
├── 05_stanley/
├── 06_astar_planning/
├── 07_kalman_filter/
├── 08_lane_detection/
├── 09_ros2_basics/
├── data/
├── rag/
├── infra/
└── .venv/
```

## 5. Current Read / Write Architecture

### Read Path
```text
ECU → CAN → DBC Decode → Vehicle Data Service → Vehicle Tool → LLM Agent
```

### Write Path
```text
LLM Agent → Control Tool → Safety Layer → Vehicle Command Service
→ DBC Encode → CAN → ECU
```

## 6. Next Plan

앞으로는 **2 DAY 단위**로 진행합니다.

### DAY10
**Command ACK / 상태 검증 / Timeout**

```text
Command Sent
    ↓
ECU Apply
    ↓
Status Message
    ↓
State Verification
    ↓
Success / Failure
```

### DAY11
**Door Lock Control + Generic Command Architecture**

- Door Lock / Unlock Tool
- Command 공통 처리 구조
- Safety Validation 확장
- Vehicle Command Result 표준화

## 7. Long-Term Roadmap

```text
CAN / DBC
   ↓
Vehicle Data Service
   ↓
Vehicle Agent
   ↓
Vehicle Model
   ↓
PID
   ↓
Pure Pursuit
   ↓
Stanley
   ↓
A*
   ↓
Kalman / EKF
   ↓
Lane Detection
   ↓
ROS2
   ↓
Vehicle Digital Twin
   ↓
RAG / Diagnostics
   ↓
Raspberry Pi + STM32 + RC Car
```

## 8. Git

기능 단위로 Commit합니다.

```bash
git add .
git commit -m "feat: add LLM vehicle agent and safe HVAC CAN control"
git push
```

`.env`, API Key, 가상환경 등은 GitHub에 업로드하지 않습니다.
