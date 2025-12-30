"""
This is the library for the modbus sensors.
Each sensor type has it's own class with it's own methods.
"""

from abc import abstractmethod
from pymodbus.constants import Endian
from pymodbus.exceptions import ModbusException

from .sensor import (
    Sensor,
    register_sensor,
    SensorProtocol,
)

from .wire_color import WireColorConfiguration
from .utilites import (
    decode_f32,
    read_holding_registers,
    read_input_registers,
    write_register,
    write_registers,
    decode_big_endian_32bits,
)

#   Sensors classes library.
#   Each sensor class should be decorated with the @register_sensor() decorator
#   in order to be listed in the global SENSOR_REGISTRY


class ModbusSensor(Sensor):
    """Extended base class for Modbus sensors with additional required methods."""

    protocol = SensorProtocol.MODBUS  # Set default protocol

    @property
    @abstractmethod
    def sensor_name(self) -> str:
        pass

    @abstractmethod
    def needs_power_cycle_before_setup(self) -> bool:
        """Whether the sensor needs a power cycle before setup"""

    @abstractmethod
    def can_broadcast_read(self) -> bool:
        """Whether broadcasting is possible for reading"""

    @abstractmethod
    def can_broadcast_setup(self) -> bool:
        """Whether broadcasting is possible for setup"""

    @abstractmethod
    def setup_sensor(
        self,
        *,
        client,
        current_slave_id: int,
        new_slave_id: int,
        **kwargs,
    ):
        """Setup/configure the sensor with new parameters."""


@register_sensor(name="Rika Par")
class RikaPar(ModbusSensor):
    """Rika Par"""
    @property
    def sensor_name(self) -> str:
        return "Rika Par"

    @property
    def wire_color_configurations(self):
        return [
            WireColorConfiguration(label="V+", color="red"),
            WireColorConfiguration(label="V-", color="green"),
            WireColorConfiguration(label="RS485A", color="yellow"),
            WireColorConfiguration(label="RS485B", color="blue"),
        ]

    @property
    def settings(self):
        return {
            "insolight": {
                "baudrate": 9600,
                "parity": "N",
                "state": "disable",
            },
        }

    def needs_power_cycle_before_setup(self) -> bool:
        return False

    def can_broadcast_read(self) -> bool:
        return True

    def can_broadcast_setup(self) -> bool:
        return True

    def setup_sensor(
        self,
        *,
        client,
        current_slave_id: int,
        new_slave_id: int,
        **kwargs,
    ):
        write_register(
            client=client, address=0x42, value=new_slave_id, slave_id=current_slave_id
        )

    def try_current_slave_id(self, *, client, slave_id: int = 0) -> int:
        try:
            slave_id = read_holding_registers(
                client=client, address=0, count=1, slave_id=slave_id
            ).slave_id
        except ModbusException:
            return -1
        return slave_id

    def read_sensor(self, client, slave_id) -> dict[str, int | float]:
        registers = read_holding_registers(
            client=client, address=0, count=2, slave_id=slave_id
        ).registers
        return {
            "radiation [umol/m2/s]": registers[0],
            "radiation_watt [W/m2]": registers[1],
        }


@register_sensor(name="Rika TH")
class RikaTH(ModbusSensor):
    """Rika Temperature and Humidity Sensor"""
    @property
    def sensor_name(self) -> str:
        return "Rika TH"

    @property
    def wire_color_configurations(self):
        return [
            WireColorConfiguration(label="V+", color="red"),
            WireColorConfiguration(label="V-", color="black"),
            WireColorConfiguration(label="RS485A", color="yellow"),
            WireColorConfiguration(label="RS485B", color="green"),
        ]

    @property
    def settings(self):
        return {
            "insolight": {
                "baudrate": 9600,
                "parity": "N",
                "state": "disable",
            },
        }

    def needs_power_cycle_before_setup(self) -> bool:
        return False

    def can_broadcast_read(self) -> bool:
        return True

    def can_broadcast_setup(self) -> bool:
        return True

    def setup_sensor(
        self,
        *,
        client,
        current_slave_id: int,
        new_slave_id: int,
        **kwargs,
    ):
        write_register(
            client=client, address=0x00, value=new_slave_id, slave_id=current_slave_id
        )

    def try_current_slave_id(self, *, client, slave_id: int = 0) -> int:
        try:
            slave_id = read_holding_registers(
                client=client, address=0, count=1, slave_id=slave_id
            ).slave_id
        except ModbusException:
            return -1
        return slave_id

    def read_sensor(self, client, slave_id) -> dict[str, int | float]:
        registers = read_holding_registers(
            client=client, address=0, count=2, slave_id=slave_id
        ).registers
        return {
            "T [°C]": registers[0] / 10,
            "H [%]": registers[1] / 10,
        }


@register_sensor(name="Apogee Par")
class ApogeePar(ModbusSensor):
    """Apogee pyranometer Models SP-422"""
    @property
    def sensor_name(self) -> str:
        return "Apogee Par"

    @property
    def wire_color_configurations(self):
        return [
            WireColorConfiguration(label="V+", color="red"),
            WireColorConfiguration(
                label="V-",
                color=["black", "green", "yellow"],
                text=["", "select", "earth"],
            ),
            WireColorConfiguration(label="RS485A", color="white"),
            WireColorConfiguration(label="RS485B", color="blue"),
        ]

    @property
    def settings(self):
        return {
            "insolight": {
                "baudrate": 9600,
                "parity": "N",
                "state": "disable",
            },
            "factory": {
                "slave_id": 1,
                "baudrate": 19200,
                "parity": "E",
                "state": "disable",
            },
            "custom": {
                "baudrate": 9600,
                "b_values": [9600, 19200, 38400, 57600, 115200],
                "parity": "N",
                "p_values": ["N", "E", "O"],
                "state": "readonly",
            },
        }

    def needs_power_cycle_before_setup(self) -> bool:
        return False

    def can_broadcast_read(self) -> bool:
        return True

    def can_broadcast_setup(self) -> bool:
        return True

    def setup_sensor(
        self,
        *,
        client,
        current_slave_id: int,
        new_slave_id: int,
        **kwargs,
    ):
        baud = {115200: 0, 57600: 1, 38400: 2, 19200: 3, 9600: 4}[
            kwargs.get("new_baudrate", 9600)
        ]
        parity = {"N": 0, "O": 1, "E": 2}[kwargs.get("new_parity", "N")]

        write_registers(
            client=client,
            address=0x33,
            values=[baud, parity],
            slave_id=current_slave_id,
        )
        write_register(
            client=client, address=0x30, value=new_slave_id, slave_id=current_slave_id
        )

    def try_current_slave_id(self, *, client, slave_id: int = 0) -> int:
        try:
            slave_id = read_holding_registers(
                client=client, address=0x30, count=1, slave_id=slave_id
            ).slave_id
        except ModbusException:
            return -1
        return slave_id

    def read_sensor(self, client, slave_id) -> dict[str, int | float]:
        registers = read_holding_registers(
            client=client, address=0, count=2, slave_id=slave_id
        ).registers
        return {
            "radiation [umol/m2/s]": decode_f32(registers, 0, wordorder=Endian.BIG),
        }


@register_sensor(name="Apogee Ghi")
class ApogeeGhi(ModbusSensor):
    """Apogee Ghi Model SQ-522"""
    @property
    def sensor_name(self) -> str:
        return "Apogee Ghi"

    @property
    def wire_color_configurations(self):
        return [
            WireColorConfiguration(label="V+", color="red"),
            WireColorConfiguration(
                label="V-",
                color=["black", "green", "yellow"],
                text=["", "select", "earth"],
            ),
            WireColorConfiguration(label="RS485A", color="white"),
            WireColorConfiguration(label="RS485B", color="blue"),
        ]

    @property
    def settings(self):
        return {
            "insolight": {
                "baudrate": 9600,
                "parity": "N",
                "state": "disable",
            },
            "factory": {
                "slave_id": 1,
                "baudrate": 19200,
                "parity": "E",
                "state": "disable",
            },
            "custom": {
                "baudrate": 9600,
                "b_values": [9600, 19200, 38400, 57600, 115200],
                "parity": "N",
                "p_values": ["N", "E", "O"],
                "state": "readonly",
            },
        }

    def needs_power_cycle_before_setup(self) -> bool:
        return False

    def can_broadcast_read(self) -> bool:
        return True

    def can_broadcast_setup(self) -> bool:
        return True

    def setup_sensor(
        self,
        *,
        client,
        current_slave_id: int,
        new_slave_id: int,
        **kwargs,
    ):
        baud = {115200: 0, 57600: 1, 38400: 2, 19200: 3, 9600: 4}[
            kwargs.get("new_baudrate", 9600)
        ]
        parity = {"N": 0, "O": 1, "E": 2}[kwargs.get("new_parity", "N")]
        write_registers(
            client=client,
            address=0x33,
            values=[baud, parity],
            slave_id=current_slave_id,
        )
        write_register(
            client=client, address=0x30, value=new_slave_id, slave_id=current_slave_id
        )

    def try_current_slave_id(self, *, client, slave_id: int = 0) -> int:
        try:
            slave_id = read_holding_registers(
                client=client, address=0x30, count=1, slave_id=slave_id
            ).slave_id
        except ModbusException:
            return -1
        return slave_id

    def read_sensor(self, client, slave_id) -> dict[str, int | float]:
        registers = read_holding_registers(
            client=client, address=0, count=2, slave_id=slave_id
        ).registers
        return {
            "irradiance [W/m2]": decode_f32(registers, 0, wordorder=Endian.BIG),
        }


@register_sensor(name="Seeed leaf wetness")
class SeeedLeafWetness(ModbusSensor):
    """Seeed Leaf Wetness and Temperature model S-YM-01"""
    @property
    def sensor_name(self) -> str:
        return "Seeed leaf wetness"

    @property
    def wire_color_configurations(self):
        return [
            WireColorConfiguration(
                label="V+", color=["red", "green", "green"], text=["", "SET", "ONLY!"]
            ),
            WireColorConfiguration(label="V-", color="black"),
            WireColorConfiguration(label="RS485A", color="yellow"),
            WireColorConfiguration(label="RS485B", color="white"),
        ]

    @property
    def settings(self):
        return {
            "insolight": {
                "baudrate": 9600,
                "parity": "N",
                "state": "disable",
            },
            "custom": {
                "baudrate": 9600,
                "b_values": [1200, 2400, 4800, 9600, 19200, 38400],
                "parity": "N",
                "p_values": ["N", "E", "O"],
                "state": "readonly",
            },
        }

    def needs_power_cycle_before_setup(self) -> bool:
        return False

    def can_broadcast_read(self) -> bool:
        return True

    def can_broadcast_setup(self) -> bool:
        return True

    def setup_sensor(
        self,
        *,
        client,
        current_slave_id: int,
        new_slave_id: int,
        **kwargs,
    ):
        baud = {1200: 0, 2400: 1, 4800: 2, 9600: 3, 19200: 4, 38400: 5}[
            kwargs.get("new_baudrate", 9600)
        ]
        parity = {"N": 0, "E": 1, "O": 2}[kwargs.get("new_parity", "N")]
        write_register(
            client=client, address=515, value=parity, slave_id=current_slave_id
        )
        write_registers(
            client=client,
            address=512,
            values=[new_slave_id, baud],
            slave_id=current_slave_id,
        )

    def try_current_slave_id(self, *, client, slave_id: int = 0) -> int:
        try:
            slave_id = read_holding_registers(
                client=client, address=0x0200, count=1, slave_id=slave_id
            ).slave_id
        except ModbusException:
            return -1
        return slave_id

    def read_sensor(self, client, slave_id) -> dict[str, int | float]:
        """
        Communicate and read from the Seeed Studio Leaf Wetness Sensor
        input: modbus client; sensor address
        output: Leaf Temperature (°C) and Wetness (%)
        """
        registers = read_holding_registers(
            client=client, address=0, count=2, slave_id=slave_id
        ).registers
        return {
            "Temperature [°C]": registers[0] / 100,
            "Humidity [%]": registers[1] / 100,
        }


@register_sensor(name="Seeed T/H")
class SeeedTH(ModbusSensor):
    """Seeed Air Temperature and Humidity model S-TH-01"""
    @property
    def sensor_name(self) -> str:
        return "Seeed T/H"

    @property
    def wire_color_configurations(self):
        return [
            WireColorConfiguration(label="V+", color="red"),
            WireColorConfiguration(label="V-", color="black"),
            WireColorConfiguration(label="RS485A", color="yellow"),
            WireColorConfiguration(label="RS485B", color="white"),
        ]

    @property
    def settings(self):
        return {
            "insolight": {
                "baudrate": 9600,
                "parity": "N",
                "state": "disable",
            },
            "custom": {
                "baudrate": 9600,
                "b_values": [1200, 2400, 4800, 9600, 19200, 38400],
                "parity": "N",
                "p_values": ["N", "E", "O"],
                "state": "readonly",
            },
        }

    def needs_power_cycle_before_setup(self) -> bool:
        return False

    def can_broadcast_read(self) -> bool:
        return True

    def can_broadcast_setup(self) -> bool:
        return True

    def setup_sensor(
        self,
        *,
        client,
        current_slave_id: int,
        new_slave_id: int,
        **kwargs,
    ):
        baud = {1200: 0, 2400: 1, 4800: 2, 9600: 3, 19200: 4, 38400: 5}[
            kwargs.get("new_baudrate", 9600)
        ]
        parity = {"N": 0, "E": 1, "O": 2}[kwargs.get("new_parity", "N")]
        write_register(
            client=client, address=515, value=parity, slave_id=current_slave_id
        )
        write_registers(
            client=client,
            address=512,
            values=[new_slave_id, baud],
            slave_id=current_slave_id,
        )

    def try_current_slave_id(self, *, client, slave_id: int = 0) -> int:
        try:
            slave_id = read_holding_registers(
                client=client, address=512, count=1, slave_id=slave_id
            ).slave_id
        except ModbusException:
            return -1
        return slave_id

    def read_sensor(self, client, slave_id) -> dict[str, int | float]:
        """
        Communicate and read from the Seeed Air Temperature & Humidity
        & Barometric Pressure Sensor
        input: modbus client; sensor address
        output:
        """
        ADDRESS_MAP = {  # pylint: disable=invalid-name
            0: "Temperature [°C]",
            1: "Humidity [%]",
            2: "Dewpoint [°C]",
        }

        # Unit conversion (division) factors
        UNIT_MAP = {  # pylint: disable=invalid-name
            0: 100,
            1: 100,
            2: 100,
        }

        read_data: dict[str, float] = {}
        for address, name in ADDRESS_MAP.items():
            raw_data = read_holding_registers(
                client=client, address=address, count=2, slave_id=slave_id
            ).registers
            data = raw_data[0] / UNIT_MAP[address]
            read_data.update({name: data})
        return read_data


@register_sensor(name="Campbell soil T/H")
class CampbellSoilTH(ModbusSensor):
    """Campbell Soil Temperature and Humidity TEROS 54"""
    @property
    def sensor_name(self) -> str:
        return "Campbell soil T/H"

    @property
    def wire_color_configurations(self):
        return [
            WireColorConfiguration(label="V+", color="brown", text=["", "brown", ""]),
            WireColorConfiguration(label="V-", color="blue"),
            WireColorConfiguration(label="RS485A", color="white"),
            WireColorConfiguration(label="RS485B", color="black"),
        ]

    @property
    def settings(self):
        return {
            "insolight": {
                "baudrate": 9600,
                "parity": "N",
                "state": "disable",
            },
        }

    def needs_power_cycle_before_setup(self) -> bool:
        return False

    def can_broadcast_read(self) -> bool:
        return True

    def can_broadcast_setup(self) -> bool:
        return True

    def setup_sensor(
        self,
        *,
        client,
        current_slave_id: int,
        new_slave_id: int,
        **kwargs,
    ):
        write_register(
            client=client, address=4100, value=new_slave_id, slave_id=current_slave_id
        )

    def try_current_slave_id(self, *, client, slave_id: int = 0) -> int:
        try:
            slave_id = read_holding_registers(
                client=client, address=4100, count=1, slave_id=slave_id
            ).slave_id
        except ModbusException:
            return -1
        return slave_id

    def read_sensor(self, client, slave_id) -> dict[str, int | float]:
        """
        Communicate and read from the METER Soil Profile Probe
        input: modbus client; sensor address
        output: Volumetric Water Content (%), Dielectric Permittivity (-),
        and Soil Temperature (°C) at 15/30/45/60 cm
        In the doc, there is an error where permittivity@60 and SoilT@60 are
        set to address 3216 and 3217 instead of 3214 and 3215.
        """
        ADDRESS_MAP = {  # pylint: disable=invalid-name
            3201: "VWC@15cm",
            3202: "Permittivity@15cm",
            3203: "SoilT@15cm",
            3205: "VWC@30cm",
            3206: "Permittivity@30cm",
            3207: "SoilT@30cm",
            3209: "VWC@45cm",
            3210: "Permittivity@45cm",
            3211: "SoilT@45cm",
            3213: "VWC@60cm",
            3214: "Permittivity@60cm",
            3215: "SoilT@60cm",
        }
        read_data: dict[str, float] = {}
        for address, name in ADDRESS_MAP.items():
            raw_data = read_input_registers(
                client=client, address=address, count=2, slave_id=slave_id
            ).registers
            decoded = decode_big_endian_32bits(raw_data)
            read_data.update({name: decoded})
        return read_data


@register_sensor(name="Kipp&Zonen RT1")
class KippZonenRT1(ModbusSensor):
    """Kipp&Zonen RT1 Rooftop Monitoring System"""
    @property
    def sensor_name(self) -> str:
        return "Kipp&Zonen RT1"

    @property
    def wire_color_configurations(self):
        return [
            WireColorConfiguration(label="V+", color="red"),
            WireColorConfiguration(label="V-", color="blue"),
            WireColorConfiguration(label="RS485A", color="yellow"),
            WireColorConfiguration(label="RS485B", color="grey"),
        ]

    @property
    def settings(self):
        return {
            "insolight": {
                "baudrate": 9600,
                "parity": "N",
                "state": "disable",
            },
            "factory": {
                "baudrate": 19200,
                "parity": "E",
                "state": "disable",
            },
            "custom": {
                "baudrate": 9600,
                "b_values": [1200, 2400, 4800, 9600, 19200, 38400],
                "parity": "N",
                "p_values": ["N", "E", "O"],
                "state": "readonly",
            },
        }

    def needs_power_cycle_before_setup(self) -> bool:
        return False

    def can_broadcast_read(self) -> bool:
        return True

    def can_broadcast_setup(self) -> bool:
        return True

    def setup_sensor(
        self,
        *,
        client,
        current_slave_id: int,
        new_slave_id: int,
        **kwargs,
    ):
        baudrate = kwargs.get("new_baudrate", 9600)
        parity = {"N": 0, "E": 1, "O": 2}[kwargs.get("new_parity", "N")]
        bytesize = 8
        stopbits = 1
        try:
            client.write_coil(address=12, value=True, slave=current_slave_id)
            client.write_registers(
                address=209,
                values=[baudrate, parity, bytesize, stopbits, new_slave_id],
                slave=current_slave_id,
            )
            client.write_coil(address=16, value=True, slave=current_slave_id)
        except ModbusException as exc:
            raise exc

    def try_current_slave_id(self, *, client, slave_id: int = 0) -> int:
        try:
            read_input_registers(client=client, address=0, count=1, slave_id=slave_id)
        except ModbusException:
            return -1
        return slave_id

    def read_sensor(self, client, slave_id) -> dict[str, int | float]:
        radiation = read_holding_registers(
            client=client, address=5, count=1, slave_id=slave_id
        ).registers
        temperature = read_holding_registers(
            client=client, address=8, count=1, slave_id=slave_id
        ).registers
        return {
            "radiation [W/m2]": radiation[0],
            "temperature [°C]": temperature[0] / 10,
        }


@register_sensor(name="Sensor Modbus Test")
class SensorModbusTest(ModbusSensor):
    """Sensor Modbus Test"""
    @property
    def sensor_name(self) -> str:
        return "Sensor Modbus Test"

    @property
    def wire_color_configurations(self):
        return [
            WireColorConfiguration(
                label="V+",
                color=["brown", "red", "red"],
                text=["", "heating", "heating"],
            ),
            WireColorConfiguration(
                label="V-",
                color=["blue", "white", "white"],
                text=["heating", "gnd", ""],
            ),
            WireColorConfiguration(label="RS485A", color="green"),
            WireColorConfiguration(label="RS485B", color="yellow"),
        ]

    @property
    def settings(self):
        return {
            "insolight": {
                "baudrate": 38400,
                "parity": "E",
                "state": "disable",
            },
            "custom": {
                "baudrate": 9600,
                "b_values": [1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200],
                "parity": "N",
                "p_values": ["N", "E", "O"],
                "state": "readonly",
            },
        }

    def needs_power_cycle_before_setup(self) -> bool:
        return False

    def can_broadcast_read(self) -> bool:
        return True

    def can_broadcast_setup(self) -> bool:
        return True

    def setup_sensor(
        self,
        *,
        client,
        current_slave_id: int,
        new_slave_id: int,
        **kwargs,
    ):
        print("Sensor setup complete")

    def try_current_slave_id(self, *, client, slave_id: int = 0) -> int:
        return 0

    def read_sensor(self, client, slave_id) -> dict[str, int | float]:
        registers = read_holding_registers(
            client=client, address=0, count=2, slave_id=slave_id
        ).registers
        return {
            "radiation [umol/m2/s]": registers[0],
            "radiation_watt [W/m2]": registers[1],
        }
