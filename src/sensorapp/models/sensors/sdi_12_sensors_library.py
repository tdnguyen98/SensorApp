"""
This is the library for the SDI-12 sensors.
Each sensor type has it's own class with it's own methods.
"""

from .sensor import (
    Sensor,
    register_sensor,
    SensorProtocol,
)
from .wire_color import WireColorConfiguration


@register_sensor(name="Apogee Radiation Frost", protocol=SensorProtocol.SDI_12)
class ApogeeRadiationFrost(Sensor):
    @property
    def sensor_name(self) -> str:
        return "Apogee Radiation Frost"

    @property
    def wire_color_configurations(self):
        return [
            WireColorConfiguration(label="V+", color="red"),
            WireColorConfiguration(label="Ground", color="black"),
            WireColorConfiguration(label="SDI-12 Data", color="white"),
        ]

    @property
    def settings(self):
        return {
            "insolight": {
                "baudrate": 1200,
                "parity": "N",
                "state": "disable",
            },
            "factory": {
                "slave_id": 1,
                "baudrate": 19200,
                "parity": "E",
                "state": "disable",
            },
        }

    def needs_power_cycle_before_setup(self) -> bool:
        return False

    def can_broadcast_read(self) -> bool:
        return True

    def can_broadcast_setup(self) -> bool:
        return True

    def get_current_slave_id(self, *, client, slave_id: int=0) -> int:
        return 1

    def read_sensor(self, client, slave_id) -> dict[str, int | float]:
    def setup_sensor(
        self,
        *,
        client,
        current_slave_id: int,
        new_slave_id: int,
        **kwargs,
    ):
        if isinstance(client, serial.Serial):
            try:
                client.reset_input_buffer()
                client.reset_output_buffer()
                command = f"{chr(current_slave_id)}A{chr(new_slave_id)}!".encode("ascii")
                client.write(command)
                time.sleep(0.5)
                if client.in_waiting > 0:
                    response = client.read(client.in_waiting).decode("ascii")
                    log_message(level="INFO", message=f"SDI-12 setup response: {response}")
                return
            except serial.SerialException as e:
                log_message(level="ERROR", message=f"Error setting up SDI-12 sensor: {e}")
        raise RuntimeError("Client is not a valid serial connection.")