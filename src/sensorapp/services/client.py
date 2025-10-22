"""This module provides a serial connection client for sensors using SDI-12 or Modbus protocols."""

from abc import ABC, abstractmethod

import serial

from pymodbus.client import ModbusSerialClient as ModbusClient
from pymodbus.exceptions import ModbusException

from ..models.sensors.sensor import Sensor, SensorProtocol

from .logging_system import log_message

# Import sensor libraries to register sensors
import src.sensorapp.models.sensors.modbus_sensors_library # This will register modbus sensors
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
        self.sensor: Sensor | None = sensor

    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def disconnect(self):
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
        super().__init__(protocol=SensorProtocol.MODBUS, port=port, baudrate=baudrate, parity=parity, sensor=sensor)
        self.client: ModbusClient | None = None

    def connect(self):
        try:
            self.client = ModbusClient(
                method="rtu",
                port=self.port,
                baudrate=self.baudrate,
                parity=self.parity,
                stopbits=self.stopbits,
                bytesize=self.bytesize,
                timeout=self.timeout,
            )
            if self.client.connect():
                log_message(level="INFO", message=f"Modbus client connected on {self.port} at {self.baudrate} baud.")
            else:
                raise ModbusException("Failed to connect Modbus client.")
        except ModbusException as e:
            log_message(level="ERROR", message=f"Error connecting Modbus client: {e}")
            self.client = None

    def disconnect(self):
        if self.client:
            self.client.close()
            log_message(level="INFO", message="Modbus client disconnected.")

    def read_data(self, *, id: int) -> dict[str, int | float] | None:
        if not self.client:
            log_message(level="ERROR", message="Modbus client is not connected.")
            return None
        if not self.sensor:
            log_message(level="ERROR", message="No sensor assigned to Modbus client.")
            return None
        try:
            data = self.sensor.read_sensor(client=self.client, slave_id=id)
            log_message(
                level="INFO", message=f"Data read from sensor {self.sensor} (ID: {id}): {data}"
            )
            return data
        except ModbusException as e:
            log_message(
                level="ERROR", message=f"Error reading data from sensor {self.sensor} (ID: {id}): {e}"
            )
            return None


class SDI12Client(SerialClient):
    def __init__(self, *, port: str, baudrate: int = 1200, parity: str = "E", sensor: Sensor):
        super().__init__(protocol=SensorProtocol.SDI_12, port=port, baudrate=baudrate, parity=parity, sensor=sensor)
        self.client: serial.Serial | None = None

    def connect(self):
        try:
            self.client = serial.Serial(port=self.port, baudrate=self.baudrate, parity=self.parity, timeout=1)
            if self.client.is_open:
                log_message(level="INFO", message=f"SDI-12 client connected on {self.port} at {self.baudrate} baud.")
            else:
                raise serial.SerialException("Failed to open SDI-12 serial port.")
        except serial.SerialException as e:
            log_message(level="ERROR", message=f"Error connecting SDI-12 client: {e}")
            self.client = None

    def disconnect(self):
        if self.client and self.client.is_open:
            self.client.close()
            log_message(level="INFO", message="SDI-12 client disconnected.")
