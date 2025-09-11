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
    client.connect()
    try:
        while True:
            temperature = client.read_temperature()
            humidity = client.read_humidity()
            payload = json.dumps({"temperature": temperature, "humidity": humidity})
            publish.single(
                config["mqtt"]["topic"], payload, hostname=config["mqtt"]["host"]
            )
            logger.info("Published %s", payload)
            time.sleep(config.get("interval", 5))
    finally:
        client.close()


if __name__ == "__main__":
    main()
