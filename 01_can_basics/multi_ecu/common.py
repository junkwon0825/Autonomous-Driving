from pathlib import Path

import can
import cantools


BASE_DIR = Path(__file__).resolve().parent

DBC_PATH = BASE_DIR / "vehicle.dbc"
CAN_CHANNEL = "vcan0"


def load_database():
    return cantools.database.load_file(DBC_PATH)


def open_can_bus():
    return can.Bus(
        interface="socketcan",
        channel=CAN_CHANNEL
    )


def send_message(bus, dbc_message, signals):

    encoded_data = dbc_message.encode(signals)

    msg = can.Message(
        arbitration_id=dbc_message.frame_id,
        data=encoded_data,
        is_extended_id=False
    )

    bus.send(msg)

