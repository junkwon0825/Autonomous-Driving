import can
import cantools


# DBC 불러오기
db = cantools.database.load_file("vehicle.dbc")

message_db = db.get_message_by_name("VehicleStatus")


# CAN Bus 연결
bus = can.interface.Bus(
    channel="vcan0",
    interface="socketcan"
)


print("Waiting for CAN message...")


while True:

    msg = bus.recv()

    if msg.arbitration_id == message_db.frame_id:

        decoded = message_db.decode(msg.data)

        print("\nCAN MESSAGE RECEIVED")
        print("------------------------")

        print("CAN ID:", hex(msg.arbitration_id))

        print(
            "DATA:",
            " ".join(f"{byte:02X}" for byte in msg.data)
        )

        print("\nDecoded Signals")

        for name, value in decoded.items():
            print(name, ":", value)
