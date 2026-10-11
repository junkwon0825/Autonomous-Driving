# CAN / Automotive AI Agent Study

`01_can_basics`는 자동차 CAN 통신부터 AI Agent 연동까지 단계적으로 구현하는 학습 디렉터리입니다.

## Progress

```text
DAY1  CAN Frame
DAY2  Signal Decode
DAY3  DBC + cantools
DAY4  Virtual CAN / SocketCAN
DAY5  Multi ECU Simulation
DAY6  Vehicle Data Service
DAY7  Vehicle Tool Layer
DAY8  LLM Tool Calling
DAY9  Control Tool + Safety Layer
```

## Architecture

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

제어 방향은 다음과 같이 분리합니다.

```text
LLM Agent
    ↓
Control Tool
    ↓
Safety Layer
    ↓
Vehicle Command Service
    ↓
CAN
    ↓
ECU
```

LLM은 CAN Frame, PWM, Steering/Throttle 값을 직접 생성하지 않습니다.

## Next

- DAY10: Command ACK / Status Verification / Timeout
- DAY11: Door Lock Control / Generic Command Architecture
