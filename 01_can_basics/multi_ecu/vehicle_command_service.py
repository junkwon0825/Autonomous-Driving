from pathlib import Path

import can
import cantools


class VehicleCommandService:

    def __init__(self):

        base_dir = Path(__file__).resolve().parent
        dbc_path = base_dir / "vehicle.dbc"

        self.db = cantools.database.load_file(
            dbc_path
        )

        self.bus = can.Bus(
            interface="socketcan",
            channel="vcan0"
        )

        self.body_command = (
            self.db.get_message_by_name(
                "BodyCommand"
            )
        )


    def set_hvac_temperature(
        self,
        temperature
    ):

        encoded_data = self.body_command.encode(
            {
                "HvacTargetCommand":
                    temperature
            }
        )


        message = can.Message(
            arbitration_id=
                self.body_command.frame_id,

            data=encoded_data,

            is_extended_id=False
        )


        self.bus.send(message)


        return {
            "success": True,
            "command": "set_hvac_temperature",
            "target_temperature": temperature,
            "unit": "degC"
        }