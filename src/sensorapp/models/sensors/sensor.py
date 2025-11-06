"""
Base sensor classes and unified registry system for all sensor types.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Type
from enum import Enum

from .wire_color import WireColorConfiguration

class SensorProtocol(Enum):
    """Enum to identify sensor communication protocols."""

    MODBUS = "modbus"
    SDI_12 = "sdi_12"


class Sensor(ABC):
    """Base abstract sensor class that all sensor implementations must inherit from."""

    # Class attribute to be set by subclasses
    protocol: SensorProtocol | None = None

    @property
    @abstractmethod
    def sensor_name(self) -> str:
        pass

    @property
    @abstractmethod
    def wire_color_configurations(self) -> List[WireColorConfiguration]:
        """
        Define the wire configurations for the sensor.
        4 needed configurations are:
        - V+ (Power supply)
        - V- (Ground)
        - RS485A
        - RS485B
        """

    @property
    @abstractmethod
    def settings(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def needs_power_cycle_before_setup(self) -> bool:
        """Wether the sensor needs a power cycle in order to be detected before setup"""

    @abstractmethod
    def can_broadcast_read(self) -> bool:
        """Wether broadcasting is possible for reading the sensor in normal use"""

    @abstractmethod
    def can_broadcast_setup(self) -> bool:
        """Wether broadcasting is possible for setup"""

    @abstractmethod
    def setup_sensor(
        self,
        *,
        client,
        current_slave_id: int,
        new_slave_id: int,
        new_baudrate: int = 9600,
        new_parity: str = "N",
    ):
        pass

    @abstractmethod
    def try_current_slave_id(self, *, client, slave_id: int = 0) -> int:
        pass

    @abstractmethod
    def read_sensor(self, client, slave_id) -> dict[str, int | float]:
        pass


# Unified global registry for all sensor classes
SENSOR_REGISTRY: Dict[str, Type[Sensor]] = {}


def register_sensor(name: str | None = None, protocol: SensorProtocol | None = None):
    """Universal decorator to register a sensor class in the unified registry."""

    def decorator(cls):
        sensor_name = name if name else cls.__name__
        cls.sensor_name = sensor_name

        # Set protocol if provided
        if protocol:
            cls.protocol = protocol

        # Ensure protocol is set
        if not hasattr(cls, "protocol") or cls.protocol is None:
            raise ValueError(f"Sensor {sensor_name} must have a protocol defined")

        SENSOR_REGISTRY[sensor_name] = cls
        return cls

    return decorator


def fetch_sensors_list() -> List[str]:
    """Retrieve the list of all registered sensor classes."""
    return list(SENSOR_REGISTRY.keys())


def fetch_sensors_by_protocol(protocol: SensorProtocol) -> Dict[str, Type[Sensor]]:
    """Retrieve sensors filtered by protocol."""
    return {
        name: cls for name, cls in SENSOR_REGISTRY.items() if cls.protocol == protocol
    }


def fetch_modbus_sensors() -> Dict[str, Type[Sensor]]:
    """Retrieve only Modbus sensors."""
    return fetch_sensors_by_protocol(SensorProtocol.MODBUS)


def fetch_sdi12_sensors() -> Dict[str, Type[Sensor]]:
    """Retrieve only SDI-12 sensors."""
    return fetch_sensors_by_protocol(SensorProtocol.SDI_12)


def get_sensor_protocol(sensor_name: str) -> SensorProtocol | None:
    """Get the protocol of a registered sensor by its name."""
    sensor_cls = SENSOR_REGISTRY.get(sensor_name)
    if sensor_cls:
        return sensor_cls.protocol
    return None
