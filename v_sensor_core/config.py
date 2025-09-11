"""Configuration helpers for the V-Sensor project."""

from __future__ import annotations

import logging
import os
from typing import Any, Dict

import yaml


def load_config(path: str | None = None) -> Dict[str, Any]:
    """Load configuration from YAML file and environment variables."""
    path = path or os.getenv("VSENSOR_CONFIG_FILE", "config.yaml")
    data: Dict[str, Any] = {}
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    data.setdefault("modbus", {})
    data["modbus"]["port"] = os.getenv("VSENSOR_PORT", data["modbus"].get("port", "/dev/ttyUSB0"))
    data["modbus"]["baudrate"] = int(
        os.getenv("VSENSOR_BAUDRATE", data["modbus"].get("baudrate", 9600))
    )
    data["modbus"]["unit"] = int(os.getenv("VSENSOR_UNIT", data["modbus"].get("unit", 1)))

    data.setdefault("mqtt", {})
    data["mqtt"]["host"] = os.getenv("VSENSOR_MQTT_HOST", data["mqtt"].get("host", "localhost"))
    data["mqtt"]["topic"] = os.getenv("VSENSOR_MQTT_TOPIC", data["mqtt"].get("topic", "vsensor/data"))

    data.setdefault("logging", {})
    data["logging"]["level"] = os.getenv("VSENSOR_LOG_LEVEL", data["logging"].get("level", "INFO"))
    data.setdefault("interval", int(os.getenv("VSENSOR_INTERVAL", data.get("interval", 5))))
    return data


def setup_logging(config: Dict[str, Any]) -> None:
    level_name = config.get("logging", {}).get("level", "INFO")
    level = getattr(logging, level_name.upper(), logging.INFO)
    logging.basicConfig(level=level)
