"""CLI to read a register from the V-Sensor."""

import click

from v_sensor_core.client import VSensorClient
from v_sensor_core.config import load_config, setup_logging


@click.command()
@click.argument("address", type=int)
def main(address: int) -> None:
    config = load_config()
    setup_logging(config)
    client = VSensorClient(
        port=config["modbus"]["port"],
        baudrate=config["modbus"]["baudrate"],
        device_id=config["modbus"]["unit"],
    )
    client.connect()
    value = client.read_register(address)
    click.echo(f"Register {address}: {value}")
    client.close()


if __name__ == "__main__":
    main()
