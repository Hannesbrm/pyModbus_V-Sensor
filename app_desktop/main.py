"""Streamlit dashboard for the V-Sensor."""

import streamlit as st

from v_sensor_core.client import VSensorClient
from v_sensor_core.config import load_config, setup_logging


config = load_config()
setup_logging(config)

st.title("V-Sensor Dashboard")

if st.button("Read data"):
    client = VSensorClient(
        method="rtu",
        port=config["modbus"]["port"],
        baudrate=config["modbus"]["baudrate"],
        device_id=config["modbus"]["unit"],
    )
    client.connect()
    temperature = client.read_temperature()
    humidity = client.read_humidity()
    client.close()
    st.write(f"Temperature: {temperature} °C")
    st.write(f"Humidity: {humidity} %")
