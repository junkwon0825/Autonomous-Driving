import can
import cantools
import time

from pathlib import Path

import can
import cantools


BASE_DIR = Path(__file__).resolve().parent
DBC_PATH = BASE_DIR / "vehicle.dbc"

db = cantools.database.load_file(DBC_PATH)


bus = can.Bus(
    interface="socketcan",
    channel="vcan0"
)


vehicle_state = {}


print("Vehicle Monitor Started")
print("-----------------------------")


last_print_time = time.time()


while True:

    msg = bus.recv()


    try:

        dbc_message = db.get_message_by_frame_id(
            msg.arbitration_id
        )

        decoded = dbc_message.decode(msg.data)


        vehicle_state.update(decoded)


    except KeyError:

        print(
            "Unknown CAN ID:",
            hex(msg.arbitration_id)
        )

        continue


    # 1초마다 전체 상태 출력
    current_time = time.time()


    if current_time - last_print_time >= 1.0:

        print("\n===== VEHICLE STATE =====")


        for name, value in vehicle_state.items():

            print(
                f"{name:20s}: {value}"
            )


        last_print_time = current_time