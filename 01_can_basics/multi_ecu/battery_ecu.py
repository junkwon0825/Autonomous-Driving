import time

from common import load_database
from common import open_can_bus
from common import send_message


db = load_database()
bus = open_can_bus()

message = db.get_message_by_name("BatteryStatus")


soc = 100


while True:

    soc -= 1

    if soc < 20:
        soc = 100


    voltage = 400 + (soc * 0.3)

    temperature = 30


    signals = {
        "BatterySOC": soc,
        "BatteryVoltage": voltage,
        "BatteryTemperature": temperature
    }


    send_message(
        bus,
        message,
        signals
    )


    print(
        f"[BATTERY] "
        f"SOC={soc}%  "
        f"Voltage={voltage:.1f}V  "
        f"Temp={temperature}C"
    )


    time.sleep(0.5)