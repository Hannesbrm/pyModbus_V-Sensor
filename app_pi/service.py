"""Headless service reading the V-Sensor and publishing via MQTT."""

from __future__ import annotations

import json
import logging
import time

import paho.mqtt.publish as publish

from v_sensor_core.client import VSensorClient
from v_sensor_core.config import load_config, setup_logging


def main() -> None:
    config = load_config()
    setup_logging(config)
    logger = logging.getLogger(__name__)

    client = VSensorClient(
        method="rtu",
        port=config["modbus"]["port"],
        baudrate=config["modbus"]["baudrate"],
        device_id=config["modbus"]["unit"],
    )
    if not client.connect():
        logger.error("Unable to connect to V-Sensor")
        return

    try:
        interval = max(config.get("interval", 5), 1)
        while True:
            display = client.read_register(149)
            pressure = client.read_register(151)
            control = client.read_register(167)
            payload = json.dumps(
                {
                    "display": display,
                    "pressure": pressure,
                    "control_output": control,
                }
            )
            publish.single(
                config["mqtt"]["topic"], payload, hostname=config["mqtt"]["host"]
            )
            logger.info("Published %s", payload)
            time.sleep(interval)
    finally:
        client.close()


if __name__ == "__main__":
    main()
