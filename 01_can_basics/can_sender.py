import can
import cantools
import time


db = cantools.database.load_file("vehicle.dbc")

message = db.get_message_by_name("VehicleStatus")


bus = can.interface.Bus(
    channel="vcan0",
    interface="socketcan"
)


speed = 0.0


while True:

    speed += 1.0

    if speed > 120:
        speed = 0


    signals = {
        "VehicleSpeed": speed,
        "BatterySOC": 78,
        "SteeringAngle": -5.0,
        "CoolantTemperature": 60,
        "GearPosition": 3
    }


    encoded_data = message.encode(signals)


    can_msg = can.Message(
        arbitration_id=message.frame_id,
        data=encoded_data,
        is_extended_id=False
    )


    bus.send(can_msg)


    print(
        f"Speed = {speed:.1f} km/h"
    )


    time.sleep(0.1)