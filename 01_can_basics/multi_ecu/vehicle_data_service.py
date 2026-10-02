from pathlib import Path
import threading
import time

import can
import cantools


class VehicleDataService:

    def __init__(self):

        # 현재 파일 위치 기준으로 vehicle.dbc 찾기
        base_dir = Path(__file__).resolve().parent
        dbc_path = base_dir / "vehicle.dbc"

        # DBC 파일 읽기
        self.db = cantools.database.load_file(dbc_path)

        # Virtual CAN 연결
        self.bus = can.Bus(
            interface="socketcan",
            channel="vcan0"
        )

        # 차량의 최신 상태 저장
        self.vehicle_state = {}

        # 각 signal을 마지막으로 받은 시간 저장
        self.signal_timestamp = {}

        # 여러 thread가 동시에 데이터 접근하는 것을 보호
        self.lock = threading.Lock()

        # CAN receiver 실행 여부
        self.running = False

        # receiver thread
        self.receiver_thread = None


    # =====================================
    # CAN 메시지 계속 받는 함수
    # =====================================

    def _receive_loop(self):

        while self.running:

            msg = self.bus.recv(timeout=1.0)

            if msg is None:
                continue

            try:

                # CAN ID에 해당하는 DBC Message 찾기
                dbc_message = self.db.get_message_by_frame_id(
                    msg.arbitration_id
                )

                # Raw CAN → 실제 Vehicle Signal
                decoded = dbc_message.decode(
                    msg.data
                )

                current_time = time.time()

                # 차량 상태 업데이트
                with self.lock:

                    self.vehicle_state.update(decoded)

                    for signal_name in decoded:

                        self.signal_timestamp[
                            signal_name
                        ] = current_time

            except KeyError:

                print(
                    "Unknown CAN ID:",
                    hex(msg.arbitration_id)
                )


    # =====================================
    # Service 시작
    # =====================================

    def start(self):

        if self.running:
            return

        self.running = True

        self.receiver_thread = threading.Thread(
            target=self._receive_loop,
            daemon=True
        )

        self.receiver_thread.start()

        print("Vehicle Data Service Started")


    # =====================================
    # Service 종료
    # =====================================

    def stop(self):

        self.running = False

        if self.receiver_thread:

            self.receiver_thread.join(
                timeout=2.0
            )

        self.bus.shutdown()

        print("Vehicle Data Service Stopped")


    # =====================================
    # 전체 차량 상태 가져오기
    # =====================================

    def get_vehicle_state(self):

        with self.lock:

            return self.vehicle_state.copy()


    # =====================================
    # 특정 Signal 가져오기
    # =====================================

    def get_signal(self, signal_name):

        with self.lock:

            return self.vehicle_state.get(
                signal_name
            )


    # =====================================
    # 차량 전용 API
    # =====================================

    def get_vehicle_speed(self):

        return self.get_signal(
            "VehicleSpeed"
        )


    def get_battery_soc(self):

        return self.get_signal(
            "BatterySOC"
        )


    def get_steering_angle(self):

        return self.get_signal(
            "SteeringAngle"
        )


    def get_cabin_temperature(self):

        return self.get_signal(
            "CabinTemperature"
        )


    # =====================================
    # Signal을 마지막으로 받은 시간
    # =====================================

    def get_signal_age(self, signal_name):

        with self.lock:

            timestamp = self.signal_timestamp.get(
                signal_name
            )

        if timestamp is None:
            return None

        return time.time() - timestamp


    # =====================================
    # 데이터가 너무 오래됐는지 확인
    # =====================================

    def is_signal_stale(
        self,
        signal_name,
        timeout=2.0
    ):

        age = self.get_signal_age(
            signal_name
        )

        if age is None:
            return True

        return age > timeout