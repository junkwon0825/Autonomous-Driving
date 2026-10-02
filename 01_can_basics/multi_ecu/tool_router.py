class ToolRouter:

    def __init__(self, vehicle_tools):

        self.vehicle_tools = vehicle_tools


        self.tools = {

            "get_vehicle_speed":
                self.vehicle_tools.get_vehicle_speed,

            "get_battery_soc":
                self.vehicle_tools.get_battery_soc,

            "get_steering_angle":
                self.vehicle_tools.get_steering_angle,

            "get_cabin_temperature":
                self.vehicle_tools.get_cabin_temperature,

            "get_vehicle_state":
                self.vehicle_tools.get_vehicle_state
        }


    def execute(
        self,
        tool_name
    ):

        tool = self.tools.get(
            tool_name
        )


        if tool is None:

            return {
                "success": False,
                "error": f"Unknown tool: {tool_name}"
            }


        try:

            return tool()


        except Exception as e:

            return {
                "success": False,
                "error": str(e)
            }