# pyModbus_V-Sensor

Helper utilities for communicating with the V-Sensor using Modbus.

## Float codec

The module `codec.py` contains functions to decode and encode 32‑bit
floating point values from Modbus register pairs. Four different byte and
word orders are supported to match the formats offered by the V-Sensor.
Format 1 (*little endian with bytes swapped*) is used by default.

The float format can be configured via the `V_SENSOR_FLOAT_FORMAT`
environment variable or programmatically using
`set_default_float_format()`.

```python
from codec import encode_float32, decode_float32, set_default_float_format, FloatFormat

set_default_float_format(FloatFormat.FORMAT_1)
registers = encode_float32(1.23)
value = decode_float32(registers)
```
