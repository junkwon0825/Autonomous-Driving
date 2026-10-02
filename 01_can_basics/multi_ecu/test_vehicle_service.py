import time

from vehicle_data_service import VehicleDataService


# Vehicle Data Service 생성
service = VehicleDataService()


# CAN 수신 시작
service.start()


try:

    while True:

        print("\n==========================")

        print(
            "Speed:",
            service.get_vehicle_speed()
        )

        print(
            "Battery SOC:",
            service.get_battery_soc()
        )

        print(
            "Steering:",
            service.get_steering_angle()
        )

        print(
            "Cabin Temp:",
            service.get_cabin_temperature()
        )

        print(
            "Battery stale:",
            service.is_signal_stale(
                "BatterySOC"
            )
        )

        time.sleep(1)


except KeyboardInterrupt:

    service.stop()