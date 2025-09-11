"""Utilities for encoding and decoding floating point values.

The V-Sensor supports four different 32-bit float formats.  The default
format (``FloatFormat.FORMAT_1``) is *little endian with bytes swapped*.
The remaining formats cover all combinations of byte and word order that
are commonly used for Modbus devices.

The desired float format can be configured globally by setting the
``V_SENSOR_FLOAT_FORMAT`` environment variable to a value from 1 to 4 or
by using :func:`set_default_float_format`.
"""

from __future__ import annotations

import os
import struct
from enum import IntEnum
from typing import Iterable, List


class FloatFormat(IntEnum):
    """Enumeration of the supported float formats."""

    FORMAT_1 = 1  # Little Endian, bytes swapped
    FORMAT_2 = 2  # Little Endian
    FORMAT_3 = 3  # Big Endian
    FORMAT_4 = 4  # Big Endian, bytes swapped


# Map formats to the corresponding byte and word orders.  The first value
# controls the byte order within each 16‑bit word, the second value the order
# of the two words.
_ENDIAN_MAP = {
    FloatFormat.FORMAT_1: ("little", "little"),
    FloatFormat.FORMAT_2: ("big", "little"),
    FloatFormat.FORMAT_3: ("big", "big"),
    FloatFormat.FORMAT_4: ("little", "big"),
}


def _coerce_format(fmt: FloatFormat | int | None) -> FloatFormat:
    """Return a :class:`FloatFormat` instance."""

    if fmt is None:
        return DEFAULT_FLOAT_FORMAT
    if isinstance(fmt, FloatFormat):
        return fmt
    try:
        return FloatFormat(int(fmt))
    except (ValueError, TypeError) as exc:  # pragma: no cover - defensive
        raise ValueError(f"invalid float format: {fmt!r}") from exc


def _swap_bytes(value: int) -> int:
    """Swap the byte order of a 16-bit integer."""
    return ((value & 0xFF) << 8) | (value >> 8)


def decode_float32(registers: Iterable[int], fmt: FloatFormat | int | None = None) -> float:
    """Decode a 32-bit float from two Modbus registers."""

    fmt = _coerce_format(fmt)
    byteorder, wordorder = _ENDIAN_MAP[fmt]

    regs = list(registers)
    if byteorder == "little":
        regs = [_swap_bytes(r) for r in regs]
    if wordorder == "little":
        regs = regs[::-1]
    data = b"".join(r.to_bytes(2, "big") for r in regs)
    return struct.unpack("!f", data)[0]


def encode_float32(value: float, fmt: FloatFormat | int | None = None) -> List[int]:
    """Encode a 32-bit float into two Modbus registers."""

    fmt = _coerce_format(fmt)
    byteorder, wordorder = _ENDIAN_MAP[fmt]

    data = struct.pack("!f", float(value))
    regs = [int.from_bytes(data[0:2], "big"), int.from_bytes(data[2:4], "big")]
    if wordorder == "little":
        regs = regs[::-1]
    if byteorder == "little":
        regs = [_swap_bytes(r) for r in regs]
    return regs


# Configure default format from environment variable
_DEFAULT = os.getenv("V_SENSOR_FLOAT_FORMAT", str(FloatFormat.FORMAT_1.value))
try:
    DEFAULT_FLOAT_FORMAT = FloatFormat(int(_DEFAULT))
except ValueError:  # pragma: no cover - defensive
    DEFAULT_FLOAT_FORMAT = FloatFormat.FORMAT_1


def set_default_float_format(fmt: FloatFormat | int) -> None:
    """Set the global default float format."""

    global DEFAULT_FLOAT_FORMAT
    DEFAULT_FLOAT_FORMAT = _coerce_format(fmt)
