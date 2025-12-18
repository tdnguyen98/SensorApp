"""This module provides a serial connection client for sensors using SDI-12 or Modbus protocols."""

from abc import ABC, abstractmethod

import serial
import re

from pymodbus.client import ModbusSerialClient as ModbusClient
from pymodbus.exceptions import ModbusException

from ..models.sensors.sensor import Sensor, SensorProtocol

from .logging_system import log_message

# Import sensor libraries to register sensors
import src.sensorapp.models.sensors.modbus_sensors_library  # This will register modbus sensors
import src.sensorapp.models.sensors.sdi_12_sensors_library  # This will register SDI-12 sensors


class SerialClient(ABC):
    def __init__(
        self,
        *,
        protocol: SensorProtocol,
        port: str,
        baudrate: int = 9600,
        parity: str = "N",
        stopbits: int = 1,
        bytesize: int = 8,
        timeout: int = 1,
        sensor: Sensor,
    ):
        self.protocol: SensorProtocol = protocol
        self.port: str = port
        self.baudrate: int = baudrate
        self.parity: str = parity
        self.stopbits: int = stopbits
        self.bytesize: int = bytesize
        self.timeout: int = timeout
        self.sensor: Sensor = sensor
        self.client: ModbusClient | serial.Serial

    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def disconnect(self):
        pass

    @abstractmethod
    def setup_sensor(
        self,
        *,
        current_slave_id: int,
        new_slave_id: int,
        new_baudrate: int = 9600,
        new_parity: str = "N",
    ):
        pass

    # @abstractmethod
    # def read_data(self, *, id: int) -> dict[str, int | float] | None:
    #     pass


class ModbusRS485Client(SerialClient):
    def __init__(
        self,
        *,
        port: str,
        baudrate: int = 9600,
        parity: str = "N",
        stopbits: int = 1,
        bytesize: int = 8,
        timeout: int = 1,
        sensor: Sensor,
    ):
        super().__init__(
            protocol=SensorProtocol.MODBUS,
            port=port,
            baudrate=baudrate,
            parity=parity,
            sensor=sensor,
        )
        self.client: ModbusClient
        self.connect()

    def connect(self):
        try:
            self.client = ModbusClient(
                method="rtu",
                port=self.port,
                baudrate=self.baudrate,
                parity=self.parity,
                stopbits=self.stopbits,
                bytesize=self.bytesize,
                timeout=0.5,
                retries=0,
            )
            if not self.client.connect():
                raise ModbusException("Failed to connect Modbus client.")
        except ModbusException as e:
            log_message(level="ERROR", message=f"Error connecting Modbus client: {e}")
            self.client = None

    def disconnect(self):
        if self.client:
            self.client.close()

    def setup_sensor(
        self,
        *,
        current_slave_id: int,
        new_slave_id: int,
        new_baudrate: int = 9600,
        new_parity: str = "N",
    ):
        self.sensor.setup_sensor(
            client=self.client,
            current_slave_id=current_slave_id,
            new_slave_id=new_slave_id,
            new_baudrate=new_baudrate,
            new_parity=new_parity,
        )

    def read_data(self, *, slave_id: int) -> dict[str, int | float] | None:
        if not self.client:
            log_message(level="ERROR", message="Modbus client is not connected.")
            return None
        if not self.sensor:
            log_message(level="ERROR", message="No sensor assigned to Modbus client.")
            return None
        try:
            data = self.sensor.read_sensor(client=self.client, slave_id=slave_id)
            log_message(
                level="INFO",
                message=f"Data read from sensor {self.sensor} (ID: {slave_id}): {data}",
            )
            return data
        except ModbusException as e:
            log_message(
                level="ERROR",
                message=f"Error reading data from sensor {self.sensor} (ID: {slave_id}): {e}",
            )
            return None


class SDI12Client(SerialClient):
    def __init__(
        self, *, port: str, baudrate: int = 1200, parity: str = "E", sensor: Sensor
    ):
        super().__init__(
            protocol=SensorProtocol.SDI_12,
            port=port,
            baudrate=baudrate,
            parity=parity,
            sensor=sensor,
        )
        self.client: serial.Serial
        self.connect()

    def connect(self):
        try:
            self.client = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                parity=self.parity,
                bytesize=7,
                stopbits=1,
                timeout=1,
            )
            if not self.client.is_open:
                raise serial.SerialException("Failed to open SDI-12 serial port.")
        except serial.SerialException as e:
            log_message(level="ERROR", message=f"Error connecting SDI-12 client: {e}")
            self.client = None

    def disconnect(self):
        if self.client and self.client.is_open:
            self.client.close()

    def setup_sensor(
        self,
        *,
        current_slave_id: int,
        new_slave_id: int,
        new_baudrate: int = 9600,
        new_parity: str = "N",
    ):
        self.sensor.setup_sensor(
            client=self.client,
            current_slave_id=current_slave_id,
            new_slave_id=new_slave_id,
        )

    def fetch_id(self) -> int | None:
        """Fetch the sensor ID using the SDI-12 protocol."""
        sensor_id: int | None = None
        try:
            self.client.reset_input_buffer()
            self.client.reset_output_buffer()
            command = b"?!"
            if isinstance(self.client, serial.Serial):
                self.client.write(command)

                response = self.client.readline()  # Read the echoed command
                response = response[:-2]
                match = re.search(b'[0-9a-zA-Z]$', response)
                if match:
                    sensor_id_match = match.group(0)
                    sensor_id = ord(sensor_id_match)
        except serial.SerialException as e:
            log_message(
                level="ERROR", message=f"Error fetching ID from SDI-12 sensor: {e}"
            )
        return sensor_id
