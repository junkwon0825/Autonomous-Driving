# CAN message example

can_message = {
    "id": 0x100,
    "dlc": 8,
    "data": [
        0x14,
        0x80,
        0x51,
        0xE0,
        0x00,
        0x00,
        0x00,
        0x00
    ]
}


# --------------------------------
# CAN message 출력
# --------------------------------

can_id = can_message["id"]
dlc = can_message["dlc"]
data = can_message["data"]

data_string = " ".join(
    f"{byte:02X}" for byte in data
)

print("CAN MESSAGE")
print("---------------------------")

print(
    f"{can_id:03X}  "
    f"{dlc}  "
    f"{data_string}"
)


# --------------------------------
# Vehicle Speed Decode
# --------------------------------

high_byte = data[0]
low_byte = data[1]

raw_speed = (high_byte << 8) | low_byte

vehicle_speed = raw_speed * 0.01


print("\nVEHICLE SIGNAL")
print("---------------------------")

print("Raw Speed     :", raw_speed)
print("Vehicle Speed :", vehicle_speed, "km/h")