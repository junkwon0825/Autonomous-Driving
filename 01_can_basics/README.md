# CAN / Vehicle Agent Study

자동차 CAN 통신의 기본 구조를 이해하고, 가상 ECU와 Vehicle Data Service를 거쳐 LLM Tool Calling까지 연결한 개인 학습 구현입니다.

## Implemented

- CAN Frame / Signal Decode
- DBC + cantools
- SocketCAN / vcan
- Powertrain · Battery · Steering · Body ECU 시뮬레이션
- Vehicle Data Service
- Vehicle Tool / Tool Router
- LLM Tool Calling
- Safety Layer
- Vehicle Command Service
- HVAC 제어 예제

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
Tool Router
   ↓
LLM Agent
```

제어 명령은 다음 경로로 분리했습니다.

```text
LLM Agent
   ↓
Control Tool
   ↓
Safety Layer
   ↓
Vehicle Command Service
   ↓
DBC Encode
   ↓
CAN
   ↓
ECU
```

LLM이 CAN Frame이나 actuator 값을 직접 생성하지 않고, 정의된 고수준 Tool을 호출하도록 구성했습니다.

## Main Files

- `vehicle.dbc`: CAN signal definition
- `multi_ecu/vehicle_data_service.py`: CAN 수신·상태 캐시
- `multi_ecu/vehicle_tools.py`: Agent에서 호출하는 차량 Tool
- `multi_ecu/tool_router.py`: Tool routing
- `multi_ecu/llm_agent.py`: LLM tool calling
- `multi_ecu/safety_layer.py`: 명령 범위 검증
- `multi_ecu/vehicle_command_service.py`: DBC encode 및 CAN command
- `multi_ecu/test_vehicle_service.py`: Vehicle Data Service 테스트
