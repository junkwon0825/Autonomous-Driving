import time

from common import load_database
from common import open_can_bus
from common import send_message


db = load_database()
bus = open_can_bus()

message = db.get_message_by_name("BodyStatus")


while True:

    signals = {
        "CabinTemperature": 26.0,
        "HvacTarget": 22.0,
        "DoorLocked": 1
    }


    send_message(
        bus,
        message,
        signals
    )


    print(
        "[BODY] "
        "Cabin=26C  "
        "HVAC=22C  "
        "Door=LOCKED"
    )


    time.sleep(1.0)