from enum import IntEnum


class VSensorRegister(IntEnum):
    """Register map for the CMR Controls V-Sensor."""

    TEMPERATURE = 0
    HUMIDITY = 1
