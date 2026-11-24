# wafe-modbus

Read and control WAFE heat recovery units with the ACE2 controller (WAFE 201 E and relatives) over Modbus TCP, as typed Python objects.

Built on [modbus-connection](https://github.com/home-assistant-libs/modbus-connection). The library never opens a connection. It takes a `ModbusUnit`, so the caller owns the link.

## Installation

```bash
pip install wafe-modbus
```

## Usage

```python
import asyncio

from modbus_connection import ModbusTcpParams
from modbus_connection.tmodbus import ModbusConnection

from wafe_modbus import OperatingMode, WafeUnit


async def main() -> None:
    connection = ModbusConnection(ModbusTcpParams(host="192.168.1.246", port=502))
    try:
        unit = WafeUnit(connection.for_unit(1))
        await unit.async_update()

        print("Outdoor:", unit.status.outdoor_temperature, "°C")
        print("CO2:", unit.status.co2, "ppm")
        print("Target airflow:", unit.status.target_airflow, "m³/h")
        print("Fan speeds:", unit.status.fan_1_speed, unit.status.fan_2_speed, "rpm")
        print("Mode:", unit.functions.operating_mode)

        await unit.async_set_operating_mode(OperatingMode.MANUAL)
        await unit.async_set_manual_airflow(120)
    finally:
        await connection.close()


asyncio.run(main())
```

## The device

- The controller answers Modbus TCP on port 502.
- It serves **one client at a time**. A second client is accepted and then reset. Keep a single connection.
- It ignores the unit id.
- It answers only these addresses. Anything else is refused.

| Table | Addresses | Component |
|---|---|---|
| Input registers | 1000–1001 | `Identity` |
| Input registers | 1002–1012 | `Status` |
| Coils | 0–13 | `Functions` |
| Holding registers | 2000–2071 | `Settings` |

`WafeUnit.async_update_readings()` reads `Status` and `Functions`. `WafeUnit.async_update_settings()` reads `Settings`. `WafeUnit.async_update()` reads both.

### Status

| Attribute | Register | Notes |
|---|---|---|
| `state` | 1002 | `UnitState`: ventilation, standby, holiday, manual |
| `sub_mode` | 1003 | `SubMode` flags; `bypass_active` reads bit 0 |
| `operating_mode` | 1004 | `OperatingMode`: the index of the active mode coil 0–3 |
| `outdoor_temperature` | 1005 | T1, °C |
| `supply_temperature` | 1006 | T2, °C |
| `extract_temperature` | 1007 | T3, °C |
| `exhaust_temperature` | 1008 | T4, °C |
| `co2` | 1009 | ppm |
| `fan_1_speed` | 1010 | Undocumented, rpm, see below |
| `fan_2_speed` | 1011 | Undocumented, rpm, see below |
| `target_airflow` | 1012 | Undocumented, m³/h, see below |

The vendor register sheet ends at 1009. Registers 1010–1012 were found on a WAFE 201 E:

- `fan_1_speed` (1010) and `fan_2_speed` (1011) are the speeds of the two fans in rpm. They fall to 0 when the fans stop, ramp up with them, and top out near 3200–3300. Which one is the supply fan is not confirmed.
- `target_airflow` (1012) is the airflow the unit currently aims for: the manual airflow in manual mode, the CO2 demand in intelligent mode, the maximum during a boost, the silent mode cap, and 0 in standby. The unit does not measure the airflow it actually delivers; when a fan runs at its maximum speed, the delivered airflow is lower.

### Functions

Coils 0–3 select the operating mode. Setting one clears the others. Scheduler mode with an empty weekly plan stops the fans.

Coils 4–10 switch standby, holiday, silent, short boost, long boost, bypass off, and fireplace mode. The boosts end by themselves after `Settings.short_boost_duration` / `long_boost_duration`; while either boost runs, both boost coils read as set, and clearing either coil ends it. `Functions.boost_active`, `async_start_boost()` and `async_stop_boost()` wrap this. Fireplace mode does nothing until an installer enables it. `bypass_off` follows `Settings.bypass_disabled`.

Coils 11–13 are scheduler commands. The library reads them but does not write them.

### Settings

Holding registers 2000–2071 follow the vendor sheet: operating mode, fan imbalance, CO2 PID and setpoint, airflow limits, bypass, boost durations, compressor, sensor simulator, scheduler slot, preheater, afterheater, and Voltdrive. Settings are written through `Settings.write(name, value)`, with range validation.

Tested on a WAFE 201 E, the device refuses writes to 2011, 2013, 2017, 2021–2024 and 2066, even of their current value. The library maps them read-only. The bypass months 2018–2019 read 0 until set, and then take only 1–12. `state` (2001) takes only ventilation and standby.

The vendor sheet has known errors. Input 1004 is not "AUT/MAN/SCH/USM" in that order: it follows the mode coils. `boost_airflow` (2011) does not hold m³/h.

## Development

```bash
uv sync
uv run pytest
uv run ruff check .
uv run mypy
```

Tests run against modbus-connection's mock backend, seeded with a register snapshot from a real WAFE 201 E (`tests/fixtures/w201e.json`).

## License

Apache-2.0
