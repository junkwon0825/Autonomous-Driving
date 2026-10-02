data = [
    0x80,
    0x14,
    0x4E,
    0xF6,
    0x00,
    0x00,
    0x00,
    0x00
]


# --------------------------------
# Vehicle Speed
# Little Endian / 16 bit
# Factor = 0.01
# --------------------------------

raw_speed = data[0] | (data[1] << 8)

vehicle_speed = raw_speed * 0.01


# --------------------------------
# Battery SOC
# Unsigned / 8 bit
# --------------------------------

raw_soc = data[2]

battery_soc = raw_soc


# --------------------------------
# Steering Angle
# Signed / 8 bit
# Factor = 0.5
# --------------------------------

raw_steering = data[3]

if raw_steering >= 128:
    raw_steering -= 256

steering_angle = raw_steering * 0.5


# --------------------------------
# Result
# --------------------------------

print("Vehicle Speed  :", vehicle_speed, "km/h")
print("Battery SOC    :", battery_soc, "%")
print("Steering Angle :", steering_angle, "deg")