"""CLI to write a register on the V-Sensor."""

import click

from v_sensor_core.client import VSensorClient
from v_sensor_core.config import load_config, setup_logging


@click.command()
@click.argument("address", type=int)
@click.argument("value", type=int)
def main(address: int, value: int) -> None:
    config = load_config()
    setup_logging(config)
    client = VSensorClient(
        port=config["modbus"]["port"],
        baudrate=config["modbus"]["baudrate"],
        device_id=config["modbus"]["unit"],
    )
    client.connect()
    ok = client.write_register(address, value)
    if ok:
        click.echo("Write successful")
    else:
        click.echo("Write failed", err=True)
    client.close()


if __name__ == "__main__":
    main()
