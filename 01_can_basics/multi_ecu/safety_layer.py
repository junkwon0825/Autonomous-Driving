class SafetyLayer:

    MIN_HVAC_TEMPERATURE = 16.0
    MAX_HVAC_TEMPERATURE = 30.0


    def validate_hvac_temperature(
        self,
        temperature
    ):

        if not isinstance(
            temperature,
            (int, float)
        ):

            return {
                "safe": False,
                "error": "Temperature must be a number."
            }


        if (
            temperature < self.MIN_HVAC_TEMPERATURE
            or
            temperature > self.MAX_HVAC_TEMPERATURE
        ):

            return {
                "safe": False,
                "error":
                    "HVAC temperature must be between 16 and 30 degC."
            }


        return {
            "safe": True
        }