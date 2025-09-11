"""Tests for VSensorClient using a Modbus simulator."""

from __future__ import annotations

import pathlib
import sys
import threading
import time

# Ensure project root on path
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from pymodbus.datastore import (
    ModbusDeviceContext,
    ModbusServerContext,
    ModbusSequentialDataBlock,
)
from pymodbus.server import StartTcpServer

from client import VSensorClient


def _run_server(port: int, initial: list[int]) -> None:
    """Run a simple Modbus TCP server for testing."""

    block = ModbusSequentialDataBlock(1, initial)
    device = ModbusDeviceContext(hr=block)
    context = ModbusServerContext(device, single=True)
    StartTcpServer(context, address=("127.0.0.1", port))


def _start_server(port: int, initial: list[int]) -> None:
    thread = threading.Thread(target=_run_server, args=(port, initial), daemon=True)
    thread.start()
    time.sleep(0.2)


def test_read_registers() -> None:
    _start_server(5020, [25, 50])

    client = VSensorClient(method="tcp", host="127.0.0.1", tcp_port=5020)
    assert client.connect()
    assert client.read_register(0) == 25
    assert client.read_register(1) == 50
    client.close()


def test_write_registers() -> None:
    _start_server(5021, [0, 0])

    client = VSensorClient(method="tcp", host="127.0.0.1", tcp_port=5021)
    assert client.connect()
    assert client.write_register(0, 123)
    assert client.read_register(0) == 123
    client.close()
