import time

from common import (
    load_database,
    open_can_bus,
    send_message
)


db = load_database()
bus = open_can_bus()


status_message = (
    db.get_message_by_name(
        "BodyStatus"
    )
)

command_message = (
    db.get_message_by_name(
        "BodyCommand"
    )
)


cabin_temperature = 26.0
hvac_target = 22.0
door_locked = 1

last_status_time = 0


print("[BODY ECU] Started")


while True:

    # Command Receive
    msg = bus.recv(
        timeout=0.05
    )


    if (
        msg is not None
        and
        msg.arbitration_id
        == command_message.frame_id
    ):

        decoded = (
            command_message.decode(
                msg.data
            )
        )


        hvac_target = (
            decoded[
                "HvacTargetCommand"
            ]
        )


        print(
            f"[BODY ECU] "
            f"HVAC command received: "
            f"{hvac_target} degC"
        )


    # Status TX
    current_time = time.time()


    if (
        current_time
        - last_status_time
        >= 1.0
    ):

        signals = {

            "CabinTemperature":
                cabin_temperature,

            "HvacTarget":
                hvac_target,

            "DoorLocked":
                door_locked
        }


        send_message(
            bus,
            status_message,
            signals
        )


        print(
            f"[BODY] "
            f"Cabin={cabin_temperature}C "
            f"HVAC={hvac_target}C "
            f"Door={'LOCKED' if door_locked else 'UNLOCKED'}"
        )


        last_status_time = (
            current_time
        )