"""Tests for float encoding/decoding helpers."""

from __future__ import annotations

import pytest

import codec
from codec import FloatFormat, decode_float32, set_default_float_format


@pytest.mark.parametrize(
    "fmt, registers",
    [
        (FloatFormat.FORMAT_1, [0xA470, 0x9D3F]),
        (FloatFormat.FORMAT_2, [0x70A4, 0x3F9D]),
        (FloatFormat.FORMAT_3, [0x3F9D, 0x70A4]),
        (FloatFormat.FORMAT_4, [0x9D3F, 0xA470]),
    ],
)
def test_decode_float32_all_formats(fmt: FloatFormat, registers: list[int]) -> None:
    assert decode_float32(registers, fmt) == pytest.approx(1.23, rel=1e-6)


def test_decode_uses_default_format() -> None:
    original = codec.DEFAULT_FLOAT_FORMAT
    try:
        set_default_float_format(FloatFormat.FORMAT_3)
        assert decode_float32([0x3F9D, 0x70A4]) == pytest.approx(1.23, rel=1e-6)
    finally:
        set_default_float_format(original)
