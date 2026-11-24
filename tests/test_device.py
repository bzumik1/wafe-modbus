from __future__ import annotations

import pytest
from modbus_connection import (
    IllegalDataAddressError,
    ModbusConnectionError,
    ModbusTimeoutError,
)
from modbus_connection.mock import MockModbusUnit, WriteEvent

from wafe_modbus import Model, OperatingMode, SubMode, UnitState, WafeUnit


async def test_decodes_a_captured_unit(device: WafeUnit) -> None:
    report = await device.async_update()

    assert report.complete
    assert report.updated == {"status", "functions", "settings"}
    assert device.unit_id == 1045
    assert device.model is Model.W201

    status = device.status
    assert status.state is UnitState.VENTILATION
    assert status.sub_mode == SubMode(0)
    assert status.bypass_active is False
    assert status.holiday_ventilation_active is False
    assert status.operating_mode is OperatingMode.INTELLIGENT
    assert status.outdoor_temperature == 2.2
    assert status.supply_temperature == 18.1
    assert status.extract_temperature == 21.5
    assert status.exhaust_temperature == 10.7
    assert status.co2 == 645
    assert status.fan_1_speed == 2888
    assert status.fan_2_speed == 3282
    assert status.target_airflow == 119

    functions = device.functions
    assert functions.intelligent is True
    assert functions.manual is False
    assert functions.operating_mode is OperatingMode.INTELLIGENT
    assert functions.short_boost is False
    assert functions.long_boost is False

    settings = device.settings
    assert settings.operating_mode is OperatingMode.INTELLIGENT
    assert settings.state is UnitState.VENTILATION
    assert settings.co2_setpoint == 400
    assert settings.max_airflow == 220
    assert settings.min_airflow == 50
    assert settings.manual_airflow == 75
    assert settings.short_boost_duration == 900
    assert settings.long_boost_duration == 3600
    assert settings.bypass_disabled is False
    assert settings.bypass_start_month is None
    assert settings.bypass_end_month is None
    assert settings.preheat_start_temperature == -3.0
    assert settings.co2_p == 0.001


async def test_negative_temperature(w201e: MockModbusUnit) -> None:
    w201e.input[1005] = 0x10000 - 125
    device = WafeUnit(w201e)
    await device.async_update_readings()
    assert device.status.outdoor_temperature == -12.5


async def test_bypass_bit(w201e: MockModbusUnit) -> None:
    w201e.input[1003] = 0b0011
    device = WafeUnit(w201e)
    await device.async_update_readings()
    assert device.status.sub_mode == SubMode.BYPASS | SubMode.HOLIDAY_VENTILATION
    assert device.status.bypass_active is True
    assert device.status.holiday_ventilation_active is True


async def test_reads_stay_inside_the_served_ranges(
    device: WafeUnit, w201e: MockModbusUnit
) -> None:
    await device.async_update()

    served = {"input": (1000, 1012), "holding": (2000, 2071), "coil": (0, 13)}
    for block in w201e.read_events:
        low, high = served[block.register_type]
        assert low <= block.address
        assert block.address + block.count - 1 <= high
    assert len(w201e.read_events) == 4


async def test_readings_and_settings_poll_separately(
    device: WafeUnit, w201e: MockModbusUnit
) -> None:
    report = await device.async_update_readings()
    assert report.updated == {"status", "functions"}
    report = await device.async_update_settings()
    assert report.updated == {"settings"}


async def test_set_operating_mode_writes_the_mode_coil(
    device: WafeUnit, w201e: MockModbusUnit
) -> None:
    writes: list[WriteEvent] = []
    w201e.on_write(writes.append)

    await device.async_set_operating_mode(OperatingMode.MANUAL)

    assert [(w.register_type, w.address, w.values) for w in writes] == [
        ("coil", 2, [True])
    ]


async def test_set_manual_airflow(device: WafeUnit, w201e: MockModbusUnit) -> None:
    await device.async_set_manual_airflow(120)
    assert w201e.holding[2009] == 120


@pytest.mark.parametrize("airflow", [49, 221])
async def test_set_manual_airflow_outside_limits(
    device: WafeUnit, airflow: int
) -> None:
    with pytest.raises(ValueError, match="outside 50-220"):
        await device.async_set_manual_airflow(airflow)


async def test_function_coil_write(device: WafeUnit, w201e: MockModbusUnit) -> None:
    await device.functions.write("short_boost", True)
    assert w201e.coil[7] is True


async def test_scheduler_commands_are_read_only(device: WafeUnit) -> None:
    with pytest.raises(AttributeError):
        await device.functions.write("scheduler_clear", True)


@pytest.mark.parametrize(
    "field",
    [
        "boost_airflow",
        "bypass_imbalance",
        "night_bypass_airflow",
        "bypass_min_outdoor_temperature",
        "bypass_min_indoor_temperature",
        "night_bypass_min_outdoor_temperature",
        "night_bypass_min_indoor_temperature",
        "voltdrive_min_airflow",
    ],
)
async def test_settings_the_device_refuses_are_read_only(
    device: WafeUnit, field: str
) -> None:
    with pytest.raises(AttributeError):
        await device.settings.write(field, 1)


async def test_state_command(device: WafeUnit, w201e: MockModbusUnit) -> None:
    await device.settings.write("state", UnitState.STANDBY)
    assert w201e.holding[2001] == 2


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("fan_imbalance", 101),
        ("bypass_start_month", 13),
        ("state", UnitState.HOLIDAY),
        ("state", UnitState.MANUAL),
        ("bypass_start_month", 0),
        ("short_boost_duration", -1),
    ],
)
async def test_setting_validators_reject(
    device: WafeUnit, field: str, value: int
) -> None:
    with pytest.raises(ValueError):
        await device.settings.write(field, value)


async def test_signed_setting_write(device: WafeUnit, w201e: MockModbusUnit) -> None:
    await device.settings.write("fan_imbalance", -20)
    assert w201e.holding[2002] == 0x10000 - 20


async def test_refused_block_lands_in_report(w201e: MockModbusUnit) -> None:
    w201e.fail_read(2000, IllegalDataAddressError())
    device = WafeUnit(w201e)
    report = await device.async_update()
    assert report.updated == {"status", "functions"}
    assert isinstance(report.failed["settings"], IllegalDataAddressError)


async def test_silent_unit_raises_timeout(w201e: MockModbusUnit) -> None:
    w201e.fail_requests(ModbusTimeoutError())
    with pytest.raises(ModbusTimeoutError):
        await WafeUnit(w201e).async_update()


async def test_dropped_link_raises(w201e: MockModbusUnit) -> None:
    device = WafeUnit(w201e)
    await device.async_update()
    w201e.fail_requests(ModbusConnectionError())
    with pytest.raises(ModbusConnectionError):
        await device.async_update()


async def test_setup_retries_after_failure(w201e: MockModbusUnit) -> None:
    w201e.fail_requests(ModbusTimeoutError())
    device = WafeUnit(w201e)
    with pytest.raises(ModbusTimeoutError):
        await device.async_update()
    w201e.fail_requests(None)
    await device.async_update()
    assert device.unit_id == 1045


async def test_raw_read_covers_every_register(device: WafeUnit) -> None:
    raw = await device.async_read_raw()
    assert sorted(raw["input"]) == list(range(1000, 1013))
    assert sorted(raw["holding"]) == list(range(2000, 2072))
    assert sorted(raw["coil"]) == list(range(14))


async def test_unknown_mode_decodes_to_none(w201e: MockModbusUnit) -> None:
    w201e.input[1002] = 9
    w201e.coil[0] = False
    device = WafeUnit(w201e)
    await device.async_update_readings()
    assert device.status.state is None
    assert device.functions.operating_mode is None


async def test_boost_helpers(device: WafeUnit, w201e: MockModbusUnit) -> None:
    await device.async_update_readings()
    assert device.functions.boost_active is False

    await device.functions.async_start_boost(long=True)
    assert w201e.coil[8] is True
    await device.functions.async_start_boost()
    assert w201e.coil[7] is True
    await device.async_update_readings()
    assert device.functions.boost_active is True

    await device.functions.async_stop_boost()
    assert w201e.coil[7] is False


async def test_boost_active_unknown_before_read(device: WafeUnit) -> None:
    assert device.functions.boost_active is None


async def test_bypass_month_once_set(w201e: MockModbusUnit) -> None:
    w201e.holding[2018] = 5
    device = WafeUnit(w201e)
    await device.async_update_settings()
    assert device.settings.bypass_start_month == 5


async def test_sub_mode_unknown_before_read(device: WafeUnit) -> None:
    assert device.status.bypass_active is None
    assert device.status.holiday_ventilation_active is None


@pytest.mark.parametrize(
    ("field", "address"), [("co2_p", 2003), ("compressor_d", 2031)]
)
async def test_scaled_pid_range(
    device: WafeUnit, w201e: MockModbusUnit, field: str, address: int
) -> None:
    with pytest.raises(ValueError):
        await device.settings.write(field, 65.536)
    await device.settings.write(field, 65.535)
    assert w201e.holding[address] == 65535
