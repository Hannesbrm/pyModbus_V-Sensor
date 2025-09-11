"""Tests for VSensorClient using a Modbus simulator."""

from __future__ import annotations

import pathlib
import sys
import threading
import time

# Ensure project root on path
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from pymodbus.datastore import ModbusSequentialDataBlock, ModbusDeviceContext, ModbusServerContext
from pymodbus.server import StartTcpServer

from client import VSensorClient


def _run_server() -> None:
    block = ModbusSequentialDataBlock(1, [25, 50])
    device = ModbusDeviceContext(hr=block)
    context = ModbusServerContext(device, single=True)
    StartTcpServer(context, address=("127.0.0.1", 5020))


def test_read_registers() -> None:
    thread = threading.Thread(target=_run_server, daemon=True)
    thread.start()
    time.sleep(0.2)

    client = VSensorClient(method="tcp", host="127.0.0.1", tcp_port=5020)
    assert client.connect()
    assert client.read_register(0) == 25
    assert client.read_register(1) == 50
    client.close()
