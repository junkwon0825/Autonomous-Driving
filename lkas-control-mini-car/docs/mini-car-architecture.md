# Raspberry Pi + MCU 미니카 설계안

**상태: 문서상 제안만 완료. 부품 보유/구매, 배선, firmware, 실험은 확인되거나 수행되지 않았다.** 아래는 구현 결과 또는 구매 확정 목록이 아니다.

## 시스템 경계

```text
Camera
  │ frames
  ▼
Raspberry Pi (OpenCV ROI/edge/line fit → lane center, heading, confidence)
  │ timestamped bounded command + heartbeat
  ▼
MCU (command validation → watchdog/E-stop interlock → servo + motor PWM)
  │
  ├── steering servo / steering linkage
  ├── motor driver / DC gear motor
  ├── wheel encoder feedback (planned)
  └── independent motor-power emergency stop (planned)
```

Pi는 카메라 처리 및 상위 제어, MCU는 주기적인 하위 구동·timeout·안전 입력 처리를 담당한다. Pi 프로세스가 정지해도 MCU timeout은 독립적으로 동작해야 한다. 이 설계의 안전성을 검증한 것은 아니다.

## 부품 후보와 구매 전 입력

| 기능 | 후보 | 확정 전에 필요한 정보 |
|---|---|---|
| 상위 컴퓨터 | Raspberry Pi 5 또는 이미 보유한 Linux SBC | 보유 여부, OS, 부하/발열, 예산 |
| 카메라 | Pi 호환 camera module 또는 UVC camera | FOV, 장착 위치, 노출, 실내 조명 |
| 저수준 제어 | Arduino 호환 MCU 또는 타이머/PWM이 검증된 MCU | 보유 여부, PWM/serial 지원, watchdog |
| 조향 | RC servo + 실제 조향 링크 | 전압, stall torque, 서보각과 휠각, backlash |
| 구동 | DC gear motor + matching motor driver | 정격 및 stall current, 방향/PWM 입력, 방열 |
| 속도 센서 | 모터/바퀴 encoder | 펄스/회전, 최대 주파수, 설치 공간 |
| 전원 | 배터리 + fuse/BMS + 적절한 DC/DC regulator | chemistry, cell count, peak current, 충전기 |
| 긴급정지 | 운전자 reach 가능한 motor-power cut-off | 전류 정격, motor power isolation 방식 |

아무 부품도 현재 프로젝트의 보유품이라고 가정하지 않는다. 모터 드라이버 전류는 모터 stall current와 열/피크 여유를 확인해 고르고, 배터리·배선·커넥터는 구동 최대 전류에 맞춰 선정해야 한다. Raspberry Pi GPIO로 모터나 servo를 직접 구동하지 않는다. servo와 motor 전원이 분리되는 설계에서는 전원 기준/공통 접지와 역전압·노이즈 대책을 보드 사양에 따라 확인한다. 부품이 특정되지 않은 상태에서 핀 번호, 배선도 또는 안전 전압을 임의로 확정하지 않는다.

## 소프트웨어 계약 (제안)

상위 vision/control는 각 프레임에서 다음을 생성한다:

| 값 | 단위/범위 | 제안 용도 |
|---|---|---|
| `timestamp_ms` | MCU/Pi 합의 시계 기준 ms | 명령의 나이/지연 진단 |
| `steering_norm` | signed integer `[-1000, 1000]` | 보정 후 servo target |
| `throttle_norm` | integer `[0,1000]` | 제한된 구동 요구 |
| `confidence` | integer `[0,1000]` | 차선 검출 품질 |
| `sequence` | uint16 | 누락/중복 명령 감지 |
| `flags` | bit field | enable, fault, E-stop 상태 |

MCU는 프레임 포맷·CRC를 검증한 뒤 최신 sequence의 유효 명령만 사용한다. 초기 watchdog timeout 후보 100 ms는 **미검증 요구값**이며, 실제 제어주기/통신 지연과 MCU 구현에 맞춰 정하고 fault-injection으로 검증해야 한다. timeout, framing error, confidence 하한 미달, E-stop 또는 brownout이면 throttle을 0으로 하고 motor enable을 제거한다. steering neutral/hold 동작은 실제 linkage의 안전 상태를 판단해 별도로 검증해야 한다. 통신 loss 응답을 검증하기 전에 차량을 바닥에 내려 주행하지 않는다.

카메라 OpenCV 처리 제안은 grayscale → blur → Canny → 하부 ROI → 좌/우 차선 후보/robust line fit → 차선 중심/방향 추정 순이다. 한쪽 차선만 검출될 때 차선 폭을 무조건 정상으로 가정하지 말고, confidence를 낮추고 감속/정지 요구로 연결한다. 이미지 중심 pixel 편차를 미터나 전륜 조향각으로 직접 간주하지 않는다. 카메라 intrinsic/extrinsic, camera pitch, axle 기준 look-ahead 좌표, 조향 linkage 비선형을 각각 보정해야 한다. 기록된 Velog 사례의 ROI/threshold/servo 결과를 이 프로젝트가 검증한 것으로 취급하지 않는다.

## 제어/측정과 안전 시험 순서

1. 실물 연결 전에 protocol parser, range check, sequence, timeout 및 E-stop 논리를 desk test한다.
2. 바퀴를 들어 올린 상태에서 모터 방향/제한 PWM/브레이크 동작, 서보 neutral/최대각을 확인한다.
3. 실제 조향 휠각과 PWM 명령을 단계별로 측정하고 좌/우 부호 및 backlash를 기록한다.
4. encoder 기반 저속/속도 feedback을 확인한다.
5. 카메라 timestamp, 인지 시간, 통신 RTT, controller 주기 및 PWM 적용 시각을 동기화해 로그에 기록한다.
6. 바닥 비주행 시험에서 E-stop과 통신/카메라 fault를 주입해 throttle 차단을 확인한다.
7. 통제된 실내 트랙에서 저속 직선, 완만한 곡선, 작은 초기 오차 순으로 넓은 공간·물리적 안전 차단을 유지하며 시험한다.

위 목록은 수행 기록이 아닌 시험 계획이다. 모든 실주행은 보행자 없는 통제된 실내 공간에서만 계획하며, 현재 실험 결과는 없다.
