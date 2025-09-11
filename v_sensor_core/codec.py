"""Value encoders/decoders for the V-Sensor."""


def decode_temperature(value: int) -> float:
    """Decode a raw register value into degrees Celsius."""
    return value / 10.0


def encode_temperature(value: float) -> int:
    """Encode degrees Celsius into raw register representation."""
    return int(value * 10)


def decode_humidity(value: int) -> float:
    """Decode raw register value into relative humidity percent."""
    return value / 10.0


def encode_humidity(value: float) -> int:
    """Encode relative humidity percent into raw register representation."""
    return int(value * 10)
