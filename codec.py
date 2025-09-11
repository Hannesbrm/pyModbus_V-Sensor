"""Utilities for encoding and decoding floating point values.

The V-Sensor supports four different 32-bit float formats.  The default
format (``FloatFormat.FORMAT_1``) is *little endian with bytes swapped*.
The remaining formats cover all combinations of byte and word order that
are commonly used for Modbus devices.

These helpers build on :class:`pymodbus.payload.BinaryPayloadDecoder` and
:class:`pymodbus.payload.BinaryPayloadBuilder` in order to correctly
convert between Python ``float`` values and the two 16-bit Modbus
registers used to transfer them.

The desired float format can be configured globally by setting the
``V_SENSOR_FLOAT_FORMAT`` environment variable to a value from 1 to 4 or
by using :func:`set_default_float_format`.
"""

from __future__ import annotations

import os
from enum import IntEnum
from typing import Iterable, List

from pymodbus.payload import BinaryPayloadDecoder, BinaryPayloadBuilder
from pymodbus.constants import Endian


class FloatFormat(IntEnum):
    """Enumeration of the supported float formats."""

    FORMAT_1 = 1  # Little Endian, bytes swapped
    FORMAT_2 = 2  # Little Endian
    FORMAT_3 = 3  # Big Endian
    FORMAT_4 = 4  # Big Endian, bytes swapped


# Map formats to the corresponding byte and word orders used by pymodbus
_ENDIAN_MAP = {
    FloatFormat.FORMAT_1: (Endian.Little, Endian.Little),
    FloatFormat.FORMAT_2: (Endian.Big, Endian.Little),
    FloatFormat.FORMAT_3: (Endian.Big, Endian.Big),
    FloatFormat.FORMAT_4: (Endian.Little, Endian.Big),
}


def _coerce_format(fmt: FloatFormat | int | None) -> FloatFormat:
    """Return a :class:`FloatFormat` instance.

    Parameters
    ----------
    fmt:
        Either ``None`` (use default), an ``int`` in ``1..4`` or a
        ``FloatFormat`` instance.
    """

    if fmt is None:
        return DEFAULT_FLOAT_FORMAT
    if isinstance(fmt, FloatFormat):
        return fmt
    try:
        return FloatFormat(int(fmt))
    except (ValueError, TypeError) as exc:  # pragma: no cover - defensive
        raise ValueError(f"invalid float format: {fmt!r}") from exc


def decode_float32(registers: Iterable[int], fmt: FloatFormat | int | None = None) -> float:
    """Decode a 32-bit float from two Modbus registers.

    Parameters
    ----------
    registers:
        An iterable with two 16-bit register values.
    fmt:
        The float format to use.  If ``None`` the global default is used.
    """

    fmt = _coerce_format(fmt)
    byteorder, wordorder = _ENDIAN_MAP[fmt]
    decoder = BinaryPayloadDecoder.fromRegisters(
        list(registers), byteorder=byteorder, wordorder=wordorder
    )
    return decoder.decode_32bit_float()


def encode_float32(value: float, fmt: FloatFormat | int | None = None) -> List[int]:
    """Encode a 32-bit float into two Modbus registers.

    Parameters
    ----------
    value:
        The floating point value to encode.
    fmt:
        The float format to use.  If ``None`` the global default is used.
    """

    fmt = _coerce_format(fmt)
    byteorder, wordorder = _ENDIAN_MAP[fmt]
    builder = BinaryPayloadBuilder(byteorder=byteorder, wordorder=wordorder)
    builder.add_32bit_float(value)
    return builder.to_registers()


# Configure default format from environment variable
_DEFAULT = os.getenv("V_SENSOR_FLOAT_FORMAT", str(FloatFormat.FORMAT_1.value))
try:
    DEFAULT_FLOAT_FORMAT = FloatFormat(int(_DEFAULT))
except ValueError:  # pragma: no cover - defensive
    DEFAULT_FLOAT_FORMAT = FloatFormat.FORMAT_1


def set_default_float_format(fmt: FloatFormat | int) -> None:
    """Set the global default float format.

    This allows applications to change the float format at runtime
    instead of relying solely on the ``V_SENSOR_FLOAT_FORMAT``
    environment variable.
    """

    global DEFAULT_FLOAT_FORMAT
    DEFAULT_FLOAT_FORMAT = _coerce_format(fmt)
