"""Live Streamlit dashboard for the V-Sensor."""

from __future__ import annotations

import time

import streamlit as st

from v_sensor_core.client import VSensorClient
from v_sensor_core.config import load_config, setup_logging


config = load_config()
setup_logging(config)

st.title("V-Sensor Dashboard")


def _client() -> VSensorClient:
    return VSensorClient(
        method="rtu",
        port=config["modbus"]["port"],
        baudrate=config["modbus"]["baudrate"],
        device_id=config["modbus"]["unit"],
    )


def read_values() -> tuple[float | None, float | None, float | None, float | None, float | None, float | None]:
    with _client() as client:
        display = client.read_register(149)
        pressure = client.read_register(151)
        control = client.read_register(167)
        setpoint = client.read_register(153)
        low_alarm = client.read_register(216)
        high_alarm = client.read_register(218)
    return display, pressure, control, setpoint, low_alarm, high_alarm


def write_parameters(setpoint: float, low_alarm: float, high_alarm: float) -> None:
    with _client() as client:
        client.write_register(153, setpoint)
        client.write_register(216, low_alarm)
        client.write_register(218, high_alarm)


# ---------------------------------------------------------------------------
# Periodic update
# ---------------------------------------------------------------------------

display, pressure, control, setpoint, low_alarm, high_alarm = read_values()

col1, col2, col3 = st.columns(3)
col1.metric("Display Value", f"{display:.2f}" if display is not None else "–")
col2.metric("Pressure", f"{pressure:.2f}" if pressure is not None else "–")
col3.metric("Control Output", f"{control:.2f}" if control is not None else "–")

if "setpoint" not in st.session_state:
    st.session_state["setpoint"] = setpoint or 0.0
if "low_alarm" not in st.session_state:
    st.session_state["low_alarm"] = low_alarm or 0.0
if "high_alarm" not in st.session_state:
    st.session_state["high_alarm"] = high_alarm or 0.0

st.number_input("Setpoint", key="setpoint")
st.number_input("Low Alarm Threshold", key="low_alarm")
st.number_input("High Alarm Threshold", key="high_alarm")

if st.button("Update Parameters"):
    write_parameters(
        st.session_state["setpoint"],
        st.session_state["low_alarm"],
        st.session_state["high_alarm"],
    )
    st.success("Parameters updated")

# Refresh every second
REFRESH_SECONDS = 1.0
time.sleep(REFRESH_SECONDS)
st.experimental_rerun()
