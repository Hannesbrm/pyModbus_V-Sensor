# pymodbus-vsensor

Skeleton project for communicating with a CMR Controls V-Sensor over RS-485 Modbus RTU using `pymodbus`.

## Structure

- `v_sensor_core` – reusable package with Modbus client and helpers.
- `app_desktop` – Streamlit dashboard application.
- `app_pi` – headless service for Raspberry Pi including systemd unit.
- `tools` – CLI utilities for reading and writing registers.
- `tests` – pytest based tests using the `pymodbus` simulator.

Configuration is loaded from `config.yaml` and environment variables prefixed with `VSENSOR_`.
