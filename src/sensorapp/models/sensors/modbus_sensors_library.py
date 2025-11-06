"""
This is the library for the modbus sensors.
Each sensor type has it's own class with it's own methods.
"""

from abc import abstractmethod
from pymodbus.client import ModbusSerialClient as ModbusClient
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
        pass

    @abstractmethod
    def can_broadcast_read(self) -> bool:
        """Whether broadcasting is possible for reading"""
        pass

    @abstractmethod
    def can_broadcast_setup(self) -> bool:
        """Whether broadcasting is possible for setup"""
        pass

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
        """Setup/configure the sensor with new parameters."""
        pass


@register_sensor(name="Rika Par")
class RikaPar(ModbusSensor):
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
        new_baudrate: int = 9600,
        new_parity: str = "N",
    ):
        write_register(
            client=client, address=0x42, value=new_slave_id, slave_id=current_slave_id
        )

    def try_current_slave_id(self, *, client, slave_id: int=0) -> int:
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
        new_baudrate: int = 9600,
        new_parity: str = "N",
    ):
        write_register(
            client=client, address=0x00, value=new_slave_id, slave_id=current_slave_id
        )

    def try_current_slave_id(self, *, client, slave_id: int=0) -> int:
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
        new_baudrate: int = 9600,
        new_parity: str = "N",
    ):
        baud = {115200: 0, 57600: 1, 38400: 2, 19200: 3, 9600: 4}[new_baudrate]
        parity = {"N": 0, "O": 1, "E": 2}[new_parity]

        write_registers(
            client=client, address=0x33, values=baud, slave_id=current_slave_id
        )
        write_registers(
            client=client, address=0x34, values=parity, slave_id=current_slave_id
        )
        write_registers(
            client=client, address=0x30, values=new_slave_id, slave_id=current_slave_id
        )

    def try_current_slave_id(self, *, client, slave_id: int=0) -> int:
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
        new_baudrate: int = 9600,
        new_parity: str = "N",
    ):
        baud = {115200: 0, 57600: 1, 38400: 2, 19200: 3, 9600: 4}[new_baudrate]
        parity = {"N": 0, "O": 1, "E": 2}[new_parity]
        print("Setting up Apogee GHI sensor...")
        write_registers(
            client=client, address=0x33, values=baud, slave_id=current_slave_id
        )
        print(f"Baudrate set to {new_baudrate}.")
        write_registers(
            client=client, address=0x34, values=parity, slave_id=current_slave_id
        )
        print(f"Parity set to {new_parity}.")
        write_registers(
            client=client, address=0x30, values=new_slave_id, slave_id=current_slave_id
        )
        print(f"Slave ID set to {new_slave_id}.")

    def try_current_slave_id(self, *, client, slave_id: int=0) -> int:
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
        new_baudrate: int = 9600,
        new_parity: str = "N",
    ):
        write_register(
            client=client, address=0x0200, value=new_slave_id, slave_id=current_slave_id
        )

    def try_current_slave_id(self, *, client, slave_id: int=0) -> int:
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
        new_baudrate: int = 9600,
        new_parity: str = "N",
    ):
        write_registers(
            client=client, address=512, values=new_slave_id, slave_id=current_slave_id
        )

    def try_current_slave_id(self, *, client, slave_id: int=0) -> int:
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
        new_baudrate: int = 9600,
        new_parity: str = "N",
    ):
        write_register(
            client=client, address=4100, value=new_slave_id, slave_id=current_slave_id
        )

    def try_current_slave_id(self, *, client, slave_id: int=0) -> int:
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
        new_baudrate: int = 9600,
        new_parity: str = "N",
    ):
        write_register(
            client=client, address=0x00, value=new_slave_id, slave_id=current_slave_id
        )

    def try_current_slave_id(self, *, client, slave_id: int=0) -> int:
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
            "radiation [W/m2]": registers[0],
            "temperature [°C]": registers[1] / 10,
        }

@register_sensor(name="Rika Test")
class RikaTest(ModbusSensor):
    @property
    def sensor_name(self) -> str:
        return "Rika Test"

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
        new_baudrate: int = 9600,
        new_parity: str = "N",
    ):
        print("Sensor setup complete")

    def try_current_slave_id(self, *, client, slave_id: int=0) -> int:
        return 0

    def read_sensor(self, client, slave_id) -> dict[str, int | float]:
        registers = read_holding_registers(
            client=client, address=0, count=2, slave_id=slave_id
        ).registers
        return {
            "radiation [umol/m2/s]": registers[0],
            "radiation_watt [W/m2]": registers[1],
        }
