"""High level Modbus client for the CMR Controls V-Sensor.

This module contains the :class:`VSensorClient` which wraps the
:class:`pymodbus.client.ModbusSerialClient` (or ``ModbusTcpClient``) and
provides a convenient interface for reading and writing the V-Sensor's
registers.  All register definitions are stored in :mod:`registers`.

The client is safe to use as a context manager::

    with VSensorClient(port="/dev/ttyUSB0") as client:
        print(client.read_register(146))  # Heartbeat

Errors are handled gracefully – any Modbus related problem will be logged
and ``None``/``False`` will be returned instead of raising an exception.
Signed registers are automatically converted to Python ``int`` values.
"""

from __future__ import annotations

import logging
from typing import Any, Iterable, Optional

from pymodbus.client import ModbusSerialClient, ModbusTcpClient
from pymodbus.exceptions import ModbusException

from codec import decode_float32, encode_float32
from registers import BY_ADDR, BY_NAME, zero_based

LOGGER = logging.getLogger(__name__)


def _to_signed(value: int) -> int:
    """Convert a 16-bit unsigned integer to a signed value."""
    if value & 0x8000:
        return value - 0x10000
    return value


class VSensorClient:
    """High level API for talking to the V-Sensor."""

    def __init__(
        self,
        *,
        method: str = "rtu",
        port: str = "/dev/ttyUSB0",
        baudrate: int = 9600,
        host: str = "localhost",
        tcp_port: int = 502,
        device_id: int = 1,
        timeout: float = 3.0,
    ) -> None:
        """Create a new client.

        Parameters
        ----------
        method:
            Either ``"rtu"`` for serial communication or ``"tcp"`` for a TCP
            connection.  The serial client is backed by
            :class:`ModbusSerialClient` while the TCP variant uses
            :class:`ModbusTcpClient`.
        port:
            Serial port to use when ``method="rtu"``.
        baudrate:
            Baudrate for the serial connection.
        host, tcp_port:
            Target host and port for TCP connections.
        device_id:
            The Modbus unit id of the sensor.
        timeout:
            Timeout in seconds for Modbus operations.
        """

        if method == "rtu":
            self._client = ModbusSerialClient(
                method="rtu", port=port, baudrate=baudrate, timeout=timeout
            )
        elif method == "tcp":
            self._client = ModbusTcpClient(host=host, port=tcp_port, timeout=timeout)
        else:  # pragma: no cover - defensive programming
            raise ValueError(f"unknown method: {method}")
        self._device_id = device_id

        # ``pymodbus`` changed the keyword for the unit identifier from
        # ``unit`` to ``device_id`` in newer versions.  Determine the proper
        # keyword at runtime for maximum compatibility.
        import inspect

        params = inspect.signature(self._client.read_holding_registers).parameters
        self._unit_kw = "unit" if "unit" in params else "device_id"

    # ------------------------------------------------------------------
    # Context manager helpers
    # ------------------------------------------------------------------
    def __enter__(self) -> "VSensorClient":
        if not self.connect():  # pragma: no cover - connection problems
            raise ConnectionError("Unable to connect to V-Sensor")
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # pragma: no cover - trivial
        self.close()

    # ------------------------------------------------------------------
    # Connection handling
    # ------------------------------------------------------------------
    def connect(self) -> bool:
        """Open the connection to the sensor.

        Returns ``True`` on success, ``False`` otherwise.
        """

        try:
            return bool(self._client.connect())
        except Exception as exc:  # pragma: no cover - defensive
            LOGGER.error("Failed to connect: %s", exc)
            return False

    def close(self) -> None:
        """Close the connection to the sensor."""
        try:
            self._client.close()
        except Exception:  # pragma: no cover - defensive
            pass

    # ------------------------------------------------------------------
    # Register helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _spec_for(register: int | str) -> tuple[int, dict[str, Any] | None]:
        """Return address/count and register specification.

        ``register`` can be either a 1-based register address as documented in
        :mod:`registers` or a 0-based address.  If the register is known in the
        global ``REGISTERS`` dictionary its metadata is returned as well.
        """

        if isinstance(register, str):
            # allow lookup by symbolic name if desired
            reg_spec = BY_NAME.get(register)
            if not reg_spec:
                raise KeyError(f"Unknown register name: {register}")
            return zero_based(reg_spec["address"]), reg_spec

        reg_spec = BY_ADDR.get(register)
        if reg_spec:
            return zero_based(reg_spec["address"]), reg_spec
        # Not part of REGISTERS -> assume caller already used 0-based address
        return int(register), None

    # Public API -------------------------------------------------------
    def read_register(self, register: int | str) -> Optional[int | float]:
        """Read a single register or register block.

        ``register`` may be specified using the 1-based address as defined in
        :mod:`registers` or as a 0-based address.  When the register metadata
        is known, values are decoded automatically (signed integers and
        floating point formats).
        """

        address, spec = self._spec_for(register)
        count = spec.get("length", 1) if spec else 1

        try:
            kwargs = {self._unit_kw: self._device_id}
            response = self._client.read_holding_registers(
                address, count=count, **kwargs
            )
        except ModbusException as exc:
            LOGGER.error("Modbus error while reading %s: %s", register, exc)
            return None
        except Exception as exc:  # pragma: no cover - defensive
            LOGGER.error("Error while reading %s: %s", register, exc)
            return None

        if response.isError():  # type: ignore[attr-defined]
            LOGGER.error("Error response while reading %s: %s", register, response)
            return None

        regs = response.registers
        if spec is None:
            return regs[0]

        rtype = spec.get("type", "u16")
        if rtype == "float32":
            return decode_float32(regs)
        if rtype == "s16":
            return _to_signed(regs[0])
        return regs[0]

    def write_register(self, register: int | str, value: int | float) -> bool:
        """Write a register on the sensor.

        ``register`` can be the 1-based address or a 0-based address.  Values
        are encoded according to the register specification in ``REGISTERS``.
        The method returns ``True`` if the operation succeeded.
        """

        address, spec = self._spec_for(register)
        if spec and "W" not in spec.get("rw", "R"):
            raise ValueError(f"Register {register} is not writable")

        if spec and spec.get("type") == "float32":
            registers = encode_float32(float(value))
        else:
            intval = int(value)
            if spec and spec.get("type") == "s16":
                registers = [intval & 0xFFFF]
            else:
                registers = [intval & 0xFFFF]

        try:
            if len(registers) == 1:
                kwargs = {self._unit_kw: self._device_id}
                response = self._client.write_register(
                    address, registers[0], **kwargs
                )
            else:
                kwargs = {self._unit_kw: self._device_id}
                response = self._client.write_registers(
                    address, registers, **kwargs
                )
        except ModbusException as exc:
            LOGGER.error("Modbus error while writing %s: %s", register, exc)
            return False
        except Exception as exc:  # pragma: no cover - defensive
            LOGGER.error("Error while writing %s: %s", register, exc)
            return False

        if response.isError():  # type: ignore[attr-defined]
            LOGGER.error("Error response while writing %s: %s", register, response)
            return False
        return True

    # Convenience aliases ---------------------------------------------
    def __call__(self, register: int | str) -> Optional[int | float]:
        """Alias for :meth:`read_register` to allow ``client(address)`` syntax."""
        return self.read_register(register)

