import time

from common import load_database
from common import open_can_bus
from common import send_message


db = load_database()
bus = open_can_bus()

message = db.get_message_by_name("PowertrainStatus")


speed = 0.0


while True:

    speed += 0.5

    if speed > 120:
        speed = 0


    engine_rpm = 800 + speed * 35


    if speed < 1:
        gear = 0

    elif speed < 20:
        gear = 1

    elif speed < 40:
        gear = 2

    elif speed < 70:
        gear = 3

    elif speed < 100:
        gear = 4

    else:
        gear = 5


    signals = {
        "VehicleSpeed": speed,
        "EngineRPM": engine_rpm,
        "GearPosition": gear
    }


    send_message(
        bus,
        message,
        signals
    )


    print(
        f"[POWERTRAIN] "
        f"Speed={speed:.1f} km/h  "
        f"RPM={engine_rpm:.0f}  "
        f"Gear={gear}"
    )


    time.sleep(0.05)