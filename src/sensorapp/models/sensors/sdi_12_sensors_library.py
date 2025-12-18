"""
This is the library for the SDI-12 sensors.
Each sensor type has it's own class with it's own methods.
"""
import serial
import time
import re
from ...services.logging_system import log_message
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
            WireColorConfiguration(label="SDI-12", color="white"),
        ]

    @property
    def settings(self):
        return {
            "SDI-12": {
                "baudrate": 1200,
                "parity": "E",
                "state": "disable",
            },
        }

    def needs_power_cycle_before_setup(self) -> bool:
        return False

    def can_broadcast_read(self) -> bool:
        return False

    def can_broadcast_setup(self) -> bool:
        return False

    def try_current_slave_id(self, *, client, slave_id: int=0) -> int:
        return 1

    def read_sensor(self, client, slave_id) -> dict[str, int | float]:
        if isinstance(client, serial.Serial):
            try:
                command = f"{chr(slave_id)}D0!".encode("ascii")
                client.write(command)
                time.sleep(0.5)
                if client.in_waiting > 0:
                    response = client.read(client.in_waiting).decode("ascii").strip()
                    if len(response) > 1:
                        data_part = response[1:]  # Remove address
                        # Find all numbers (with + or - signs)
                        values = re.findall(r'[+-]?\d*\.?\d+', data_part)
                        parsed_values = [float(v) for v in values]
                        measurements = {'temperature': parsed_values[0]}
                        return measurements
                    else:
                        log_message(level="ERROR", message="No data received from SDI-12 sensor.")
            except serial.SerialException as e:
                log_message(level="ERROR", message=f"Error reading from SDI-12 sensor: {e}")
                return {}
        raise RuntimeError("Client is not a valid serial connection.")
    
    def request_to_take_measurements(self, *, client, slave_id: int=0) -> None:
        """Sends the command to the SDI-12 sensor to take measurements."""
        if isinstance(client, serial.Serial):
            try:
                client.reset_input_buffer()
                client.reset_output_buffer()
                command = f"{chr(slave_id)}M!".encode("ascii")
                client.write(command)
                time.sleep(0.5)
                if client.in_waiting > 0:
                    client.read(client.in_waiting).decode("ascii").strip()
                return
            except serial.SerialException as e:
                log_message(level="ERROR", message=f"Error requesting measurements from SDI-12 sensor: {e}")
        raise RuntimeError("Client is not a valid serial connection.")

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