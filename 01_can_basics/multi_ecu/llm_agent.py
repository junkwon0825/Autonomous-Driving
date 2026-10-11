import json
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from vehicle_data_service import VehicleDataService
from vehicle_tools import VehicleTools
from tool_router import ToolRouter

from safety_layer import SafetyLayer
from vehicle_command_service import VehicleCommandService

# =========================================================
# 1. API
# =========================================================

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

API_KEY = os.getenv("MONOGPT_API_KEY")
BASE_URL = os.getenv("MONOGPT_BASE_URL")
MODEL = os.getenv("MONOGPT_MODEL")


if not API_KEY:
    raise ValueError("MONOGPT_API_KEY가 없습니다.")

if not BASE_URL:
    raise ValueError("MONOGPT_BASE_URL이 없습니다.")

if not MODEL:
    raise ValueError("MONOGPT_MODEL이 없습니다.")


client = OpenAI(
    api_key=API_KEY,
    base_url=BASE_URL
)


# =========================================================
# 2. Tool Schema
# =========================================================

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_vehicle_speed",
            "description": "현재 차량 속도를 조회한다.",
            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_battery_soc",
            "description": "현재 차량 배터리 SOC를 조회한다.",
            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_steering_angle",
            "description": "현재 차량 조향각을 조회한다.",
            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_cabin_temperature",
            "description": "현재 차량 실내 온도를 조회한다.",
            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_vehicle_state",
            "description": "현재 차량 전체 상태를 조회한다.",
            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        }
    }
    {
        "type": "function",

        "function": {

            "name":
                "set_hvac_temperature",

            "description":
                "차량 HVAC 목표 온도를 설정한다.",

            "parameters": {

                "type": "object",

                "properties": {

                    "temperature": {

                        "type": "number",

                        "description":
                            "설정할 HVAC 목표 온도. "
                            "섭씨 16~30도."
                    }
                },

                "required": [
                    "temperature"
                ],

                "additionalProperties":
                    False
            }
        }
    },
    
]


SYSTEM_PROMPT = """
너는 Automotive AI Agent다.

현재 차량의 실시간 정보는 반드시 Vehicle Tool을 사용한다.

차량 데이터를 추측하지 않는다.
Tool 결과를 기반으로 한국어로 답변한다.
단위가 있으면 단위를 포함한다.

HVAC 온도 변경 요청은 set_hvac_temperature Tool을 사용한다.
Safety Layer 제한을 우회하지 않는다.
Tool 실행 실패 시 제어가 성공했다고 말하지 않는다.
"""


# =========================================================
# 3. Vehicle
# =========================================================

service = VehicleDataService()
service.start()

time.sleep(1)

command_service = (
    VehicleCommandService()
)

safety_layer = (
    SafetyLayer()
)


vehicle_tools = VehicleTools(
    service,
    command_service,
    safety_layer
)
router = ToolRouter(vehicle_tools)


# =========================================================
# 4. Agent
# =========================================================

def run_agent(user_input):

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        },
        {
            "role": "user",
            "content": user_input
        }
    ]


    while True:

        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto"
        )

        assistant_message = response.choices[0].message


        if not assistant_message.tool_calls:
            return assistant_message.content


        messages.append(
            {
                "role": "assistant",
                "content": assistant_message.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in assistant_message.tool_calls
                ]
            }
        )


        for tool_call in assistant_message.tool_calls:

            tool_name = tool_call.function.name

            try:
                arguments = json.loads(
                    tool_call.function.arguments or "{}"
                )
            except json.JSONDecodeError:
                arguments = {}


            print("\n[LLM TOOL CALL]")
            print("Tool:", tool_name)
            print("Arguments:", arguments)


            result = router.execute(
                tool_name,
                arguments
            )


            print("Result:", result)


            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(
                        result,
                        ensure_ascii=False
                    )
                }
            )


print("\n==============================")
print(" Automotive LLM Vehicle Agent")
print("==============================")

try:

    while True:

        user_input = input("\nUser > ")

        if user_input.lower() == "exit":
            break

        try:
            answer = run_agent(user_input)
            print("\nAgent >", answer)

        except Exception as e:
            print("\n[ERROR]", e)

finally:

    service.stop()