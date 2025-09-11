"""Modbus register map for the CMR V-Sensor.

Addresses in ``REGISTERS`` are **1-based** as documented in the manual.
When accessing them with :mod:`pymodbus`, convert to 0-based addresses
using :func:`zero_based`.

Each entry is represented as a dictionary with the following keys:

``address``
    Register address (1-based).
``type``
    Data type (``u16``, ``s16``, ``float32``).
``rw``
    Access mode (``R``, ``W``, ``RW``).
``description``
    Human readable description of the register.
``length``
    Number of 16-bit registers this entry spans. Only present for
    multi-register types such as ``float32``.
"""


def zero_based(address: int) -> int:
    """Convert 1-based register addresses to 0-based for pymodbus."""
    return address - 1

REGISTERS = {
    138: {
        "address": 138,
        "name": "low_alarm_threshold_deprecated",
        "type": "u16",
        "rw": "RW",
        "description": "Low Alarm Threshold (deprecated, use 216/217)",
    },
    139: {
        "address": 139,
        "name": "high_alarm_threshold_deprecated",
        "type": "u16",
        "rw": "RW",
        "description": "High Alarm Threshold (deprecated, use 218/219)",
    },
    140: {
        "address": 140,
        "name": "alarm_timer_1",
        "type": "u16",
        "rw": "RW",
        "description": "Alarm Timer 1 (s or 0.1 h)",
    },
    141: {
        "address": 141,
        "name": "alarm1_status",
        "type": "u16",
        "rw": "R",
        "description": "Alarm 1 Status (0=OK, 1=Low Alarm)",
    },
    142: {
        "address": 142,
        "name": "alarm2_status",
        "type": "u16",
        "rw": "R",
        "description": "Alarm 2 Status (0=OK, 1=High Alarm)",
    },
    143: {
        "address": 143,
        "name": "alarm_timer_2",
        "type": "u16",
        "rw": "RW",
        "description": "Alarm Timer 2",
    },
    144: {
        "address": 144,
        "name": "alarm_bits",
        "type": "u16",
        "rw": "RW",
        "description": "Alarm Bits: Bit0 Low, Bit1 High, Bit2 Common, Bit3 Unmuted, Bit4 Healthy",
    },
    145: {
        "address": 145,
        "name": "buzzer_status",
        "type": "u16",
        "rw": "RW",
        "description": "Buzzer Status (1=Unmuted Alarm present)",
    },
    146: {
        "address": 146,
        "name": "heartbeat",
        "type": "u16",
        "rw": "R",
        "description": "Heartbeat (seconds tick, rolls over at 65535)",
    },
    147: {
        "address": 147,
        "name": "alarm_mode0_relay",
        "type": "u16",
        "rw": "RW",
        "description": "Alarm Mode 0 Relay (write 1 = energize)",
    },
    148: {
        "address": 148,
        "name": "alarm_mode0_buzzer",
        "type": "u16",
        "rw": "RW",
        "description": "Alarm Mode 0 Buzzer (write 1 = ON)",
    },
    149: {
        "address": 149,
        "name": "display_value",
        "type": "float32",
        "length": 2,
        "rw": "R",
        "description": "Display Value (as shown on display)",
    },
    151: {
        "address": 151,
        "name": "pascals",
        "type": "float32",
        "length": 2,
        "rw": "R",
        "description": "Pascals (measured pressure)",
    },
    153: {
        "address": 153,
        "name": "setpoint",
        "type": "float32",
        "length": 2,
        "rw": "RW",
        "description": "Control/PID Setpoint",
    },
    155: {
        "address": 155,
        "name": "pid_output",
        "type": "s16",
        "rw": "R",
        "description": "PID Output (–4095…+4095)",
    },
    156: {
        "address": 156,
        "name": "mode",
        "type": "u16",
        "rw": "RW",
        "description": "Mode: 0=Disabled, 1=Auto, 2=Hand, 3=Off, 4=Hand@current",
    },
    158: {
        "address": 158,
        "name": "pressure",
        "type": "s16",
        "rw": "R",
        "description": "Pressure (int, 0.1 Pa <2500Pa, else 1 Pa)",
    },
    164: {
        "address": 164,
        "name": "text_display",
        "type": "u16",
        "rw": "RW",
        "description": "Text Display (LED version only, 0=Normal, 1=Error, 2=Fault, 3=Off, 4=Stop; +16 = alternating)",
    },
    165: {
        "address": 165,
        "name": "hand_setpoint",
        "type": "float32",
        "length": 2,
        "rw": "RW",
        "description": "Hand Setpoint (%)",
    },
    167: {
        "address": 167,
        "name": "control_output",
        "type": "float32",
        "length": 2,
        "rw": "R",
        "description": "Control Output (%)",
    },
    216: {
        "address": 216,
        "name": "low_alarm_threshold",
        "type": "float32",
        "length": 2,
        "rw": "RW",
        "description": "Low Alarm Threshold (Display Units)",
    },
    218: {
        "address": 218,
        "name": "high_alarm_threshold",
        "type": "float32",
        "length": 2,
        "rw": "RW",
        "description": "High Alarm Threshold (Display Units)",
    },
}

BY_ADDR = {spec["address"]: spec for spec in REGISTERS.values()}
BY_NAME = {spec["name"]: spec for spec in REGISTERS.values()}

