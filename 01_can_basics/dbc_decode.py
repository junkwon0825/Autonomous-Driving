import cantools

db = cantools.database.load_file(
    "/home/jun0/autonomous-driving/01_can_basics/vehicle.dbc"
)
# print(db)
message = db.get_message_by_name("VehicleStatus")

print("Message Name :", message.name)
print("CAN ID       :", hex(message.frame_id))
print("DLC          :", message.length)


signals = {
    "VehicleSpeed": 52.48,
    "BatterySOC": 78,
    "SteeringAngle": -5.0,
    "CoolantTemperature": 60,
    "GearPosition": 3
}

encoded_data = message.encode(signals)

print(encoded_data)

hex_data = " ".join(
    f"{byte:02X}" for byte in encoded_data
)

print("CAN DATA :", hex_data)


decoded = message.decode(encoded_data)

print(decoded)