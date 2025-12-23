"""
This file contains helper functions for reading and writing data from the modbus sensors.
"""
import time

from pymodbus.client import ModbusSerialClient as ModbusClient
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.register_read_message import (
    ReadHoldingRegistersResponse,
    ReadInputRegistersResponse,
)
from pymodbus.register_write_message import (
    WriteSingleRegisterResponse,
    WriteMultipleRegistersResponse,
)
from serial import Serial
from serial.tools import list_ports



def read_holding_registers(
    *, client: ModbusClient, address: int, count: int, slave_id: int
) -> ReadHoldingRegistersResponse:
    """Helper for reading holding registers and checking for errors"""
    start_time = time.time()
    print(f"[{time.time() - start_time:.2f}s] Starting read for slave {id}")
    res = client.read_holding_registers(address=address, count=count, slave=slave_id)
    print(f"[{time.time() - start_time:.2f}s] Read completed")
    if isinstance(res, Exception):
        raise res
    if not isinstance(res, ReadHoldingRegistersResponse):
        raise TypeError(f"Unexpected answer type: {res}")
    return res


def read_input_registers(
    *, client: ModbusClient, address: int, count: int, slave_id: int
) -> ReadInputRegistersResponse:
    """Helper for reading input registers and checking for errors"""
    res = client.read_input_registers(address=address, count=count, slave=slave_id)
    if isinstance(res, Exception):
        raise res
    if not isinstance(res, ReadInputRegistersResponse):
        raise TypeError(f"Unexpected answer type: {res}")
    return res


def write_register(
    *, client: ModbusClient, address: int, value: int, slave_id: int
) -> WriteSingleRegisterResponse:
    """Helper for writing a single register and checking for errors"""
    res = client.write_register(address=address, value=value, slave=slave_id)
    if isinstance(res, Exception):
        raise res
    if not isinstance(res, WriteSingleRegisterResponse):
        raise TypeError(f"Unexpected answer type: {res}")
    return res


def write_registers(
    *, client: ModbusClient, address: int, values: list[int] | int, slave_id: int
) -> WriteMultipleRegistersResponse:
    """Helper for writing multiple registers and checking for errors"""
    res = client.write_registers(address=address, values=values, slave=slave_id)
    if isinstance(res, Exception):
        raise res
    if not isinstance(res, WriteMultipleRegistersResponse):
        raise TypeError(f"Unexpected answer type: {res}")
    return res


def decode_f32(regs: list[int], pos: int, *, wordorder=Endian.LITTLE) -> float:
    """Takes 2 register values in the list (i.e. 4 bytes) and converts them into a float"""
    return BinaryPayloadDecoder.fromRegisters(
        regs[pos : pos + 2], byteorder=Endian.BIG, wordorder=wordorder
    ).decode_32bit_float()


def decode_big_endian_32bits(regs: list) -> float:
    """Decode a big-endian 32-bit float"""
    return BinaryPayloadDecoder.fromRegisters(
        regs, byteorder=Endian.BIG, wordorder=Endian.BIG
    ).decode_32bit_float()


def write_serial(request: str, ser: Serial):
    """Helper that reads after writing"""
    print("SEND:", request)
    ser.write(f"{request}\r\n".encode())
    response = ser.read_until(b"\r\n").decode()
    print("RECV:", response)
    return response


def scan_com_ports():
    """Scans and returns a list of available COM ports"""
    return [port.device for port in list_ports.comports()]
