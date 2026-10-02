import time

from vehicle_data_service import VehicleDataService
from vehicle_tools import VehicleTools
from tool_router import ToolRouter


# =====================================
# Vehicle System
# =====================================

service = VehicleDataService()

service.start()


# CAN 데이터가 들어올 시간 조금 기다리기
time.sleep(1)


# =====================================
# Vehicle Tools
# =====================================

vehicle_tools = VehicleTools(
    service
)


# =====================================
# Tool Router
# =====================================

router = ToolRouter(
    vehicle_tools
)


print()
print("==============================")
print(" Automotive Vehicle Agent")
print("==============================")
print()

print("질문 예시")
print("속도")
print("배터리")
print("조향")
print("실내 온도")
print("차량 상태")
print()

print("종료하려면 exit 입력")


try:

    while True:

        user_input = input(
            "\nUser > "
        )


        # -----------------------------
        # Exit
        # -----------------------------

        if user_input.lower() == "exit":

            break


        # -----------------------------
        # Manual Intent Routing
        # -----------------------------

        if "속도" in user_input:

            tool_name = (
                "get_vehicle_speed"
            )


        elif "배터리" in user_input:

            tool_name = (
                "get_battery_soc"
            )


        elif "조향" in user_input:

            tool_name = (
                "get_steering_angle"
            )


        elif (
            "온도" in user_input
            or "실내" in user_input
        ):

            tool_name = (
                "get_cabin_temperature"
            )


        elif (
            "상태" in user_input
            or "전체" in user_input
        ):

            tool_name = (
                "get_vehicle_state"
            )


        else:

            print(
                "Agent > "
                "어떤 차량 정보를 원하는지 "
                "이해하지 못했습니다."
            )

            continue


        # -----------------------------
        # Execute Tool
        # -----------------------------

        result = router.execute(
            tool_name
        )


        print(
            "Tool Selected >",
            tool_name
        )


        print(
            "Tool Result >",
            result
        )


finally:

    service.stop()