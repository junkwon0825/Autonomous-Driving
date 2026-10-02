import time
import math

from common import load_database
from common import open_can_bus
from common import send_message


db = load_database()
bus = open_can_bus()

message = db.get_message_by_name("SteeringStatus")


start_time = time.time()


while True:

    t = time.time() - start_time


    steering_angle = 20 * math.sin(t)

    yaw_rate = 5 * math.sin(t)


    signals = {
        "SteeringAngle": steering_angle,
        "YawRate": yaw_rate
    }


    send_message(
        bus,
        message,
        signals
    )


    print(
        f"[STEERING] "
        f"Angle={steering_angle:.2f} deg  "
        f"YawRate={yaw_rate:.2f} deg/s"
    )


    time.sleep(0.02)