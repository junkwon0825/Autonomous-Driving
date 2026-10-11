class VehicleTools:

    def __init__(
        self,
        vehicle_service,
        command_service=None,
        safety_layer=None
):

        self.service = vehicle_service
        self.command_service = command_service
        self.safety_layer = safety_layer


    # =====================================
    # Vehicle Speed Tool
    # =====================================

    def get_vehicle_speed(self):

        value = self.service.get_vehicle_speed()

        if value is None:

            return {
                "success": False,
                "error": "VehicleSpeed signal has not been received yet."
            }


        age = self.service.get_signal_age(
            "VehicleSpeed"
        )


        return {
            "success": True,
            "signal": "VehicleSpeed",
            "value": value,
            "unit": "km/h",
            "age_sec": round(age, 3)
        }


    # =====================================
    # Battery SOC Tool
    # =====================================

    def get_battery_soc(self):

        value = self.service.get_battery_soc()

        if value is None:

            return {
                "success": False,
                "error": "BatterySOC signal has not been received yet."
            }


        age = self.service.get_signal_age(
            "BatterySOC"
        )


        return {
            "success": True,
            "signal": "BatterySOC",
            "value": value,
            "unit": "%",
            "age_sec": round(age, 3)
        }


    # =====================================
    # Steering Angle Tool
    # =====================================

    def get_steering_angle(self):

        value = self.service.get_steering_angle()

        if value is None:

            return {
                "success": False,
                "error": "SteeringAngle signal has not been received yet."
            }


        age = self.service.get_signal_age(
            "SteeringAngle"
        )


        return {
            "success": True,
            "signal": "SteeringAngle",
            "value": value,
            "unit": "deg",
            "age_sec": round(age, 3)
        }


    # =====================================
    # Cabin Temperature Tool
    # =====================================

    def get_cabin_temperature(self):

        value = self.service.get_cabin_temperature()

        if value is None:

            return {
                "success": False,
                "error": "CabinTemperature signal has not been received yet."
            }


        age = self.service.get_signal_age(
            "CabinTemperature"
        )


        return {
            "success": True,
            "signal": "CabinTemperature",
            "value": value,
            "unit": "degC",
            "age_sec": round(age, 3)
        }


    # =====================================
    # Entire Vehicle State Tool
    # =====================================

    def get_vehicle_state(self):

        state = self.service.get_vehicle_state()

        if not state:

            return {
                "success": False,
                "error": "Vehicle data has not been received yet."
            }


        return {
            "success": True,
            "vehicle_state": state
        }

    def set_hvac_temperature(
        self,
        temperature
    ):

        if (
            self.command_service is None
            or self.safety_layer is None
        ):

            return {
                "success": False,
                "error": "Control system is unavailable."
            }


        safety_result = (
            self.safety_layer
            .validate_hvac_temperature(
                temperature
            )
        )


        if not safety_result["safe"]:

            return {
                "success": False,
                "error":
                    safety_result["error"]
            }


        return (
            self.command_service
            .set_hvac_temperature(
                temperature
            )
        )