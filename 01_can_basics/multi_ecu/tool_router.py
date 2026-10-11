class ToolRouter:

    def __init__(
        self,
        vehicle_tools
    ):

        self.tools = {

            "get_vehicle_speed":
                vehicle_tools.get_vehicle_speed,

            "get_battery_soc":
                vehicle_tools.get_battery_soc,

            "get_steering_angle":
                vehicle_tools.get_steering_angle,

            "get_cabin_temperature":
                vehicle_tools.get_cabin_temperature,

            "get_vehicle_state":
                vehicle_tools.get_vehicle_state,

            "set_hvac_temperature":
                vehicle_tools.set_hvac_temperature
        }


    def execute(
        self,
        tool_name,
        arguments=None
    ):

        if arguments is None:
            arguments = {}


        tool = self.tools.get(
            tool_name
        )


        if tool is None:

            return {
                "success": False,
                "error":
                    f"Unknown tool: {tool_name}"
            }


        try:

            return tool(
                **arguments
            )


        except Exception as e:

            return {
                "success": False,
                "error": str(e)
            }