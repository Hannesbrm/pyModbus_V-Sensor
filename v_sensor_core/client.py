"""Modbus client for the CMR Controls V-Sensor."""

from __future__ import annotations

import logging
from typing import Optional

from pymodbus.client import ModbusSerialClient, ModbusTcpClient

from .registers import VSensorRegister
from . import codec

LOGGER = logging.getLogger(__name__)


class VSensorClient:
    """High level API for talking to the V-Sensor."""

    def __init__(
        self,
        method: str = "rtu",
        port: str = "/dev/ttyUSB0",
        baudrate: int = 9600,
        host: str = "localhost",
        tcp_port: int = 502,
        device_id: int = 1,
    ) -> None:
        if method == "rtu":
            self._client = ModbusSerialClient(method="rtu", port=port, baudrate=baudrate)
        elif method == "tcp":
            self._client = ModbusTcpClient(host=host, port=tcp_port)
        else:
            raise ValueError(f"Unknown method {method}")
        self._device_id = device_id

    def connect(self) -> bool:
        LOGGER.debug("Connecting to V-Sensor")
        return self._client.connect()

    def close(self) -> None:
        LOGGER.debug("Closing connection to V-Sensor")
        self._client.close()

    def read_register(self, address: int) -> Optional[int]:
        LOGGER.debug("Reading register %s", address)
        rr = self._client.read_holding_registers(address, count=1, device_id=self._device_id)
        if rr.isError():
            LOGGER.error("Error reading register %s: %s", address, rr)
            return None
        return rr.registers[0]

    def write_register(self, address: int, value: int) -> bool:
        LOGGER.debug("Writing %s to register %s", value, address)
        rq = self._client.write_register(address, value, device_id=self._device_id)
        if rq.isError():
            LOGGER.error("Error writing register %s: %s", address, rq)
            return False
        return True

    def read_temperature(self) -> Optional[float]:
        raw = self.read_register(VSensorRegister.TEMPERATURE)
        return codec.decode_temperature(raw) if raw is not None else None

    def read_humidity(self) -> Optional[float]:
        raw = self.read_register(VSensorRegister.HUMIDITY)
        return codec.decode_humidity(raw) if raw is not None else None
