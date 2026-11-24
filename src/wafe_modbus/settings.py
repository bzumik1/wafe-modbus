"""Configuration, the holding registers 2000-2071."""

from __future__ import annotations

from collections.abc import Callable

from modbus_connection.model import Component, boolean, enum, gauge, integer

from .enums import OperatingMode, UnitState

__all__ = ["Settings"]


def _in_range(low: float, high: float) -> Callable[[float], float]:
    """Return a write validator that accepts ``low`` to ``high`` inclusive."""

    def validate(value: float) -> float:
        if not low <= value <= high:
            raise ValueError(f"{value} is outside {low}-{high}")
        return value

    return validate


def _state_command(value: UnitState) -> UnitState:
    """Accept only the states the device takes as a command."""
    if value not in (UnitState.VENTILATION, UnitState.STANDBY):
        raise ValueError(f"{value!r} cannot be written")
    return value


_AIRFLOW = _in_range(0, 1000)
_PID = _in_range(0, 65535)
_SCALED_PID = _in_range(0, 65.535)
_MONTH = _in_range(1, 12)
_TEMPERATURE = _in_range(-50, 50)
_DURATION = _in_range(0, 65535)


class Settings(Component):
    """Every setting of the unit, read in one block."""

    register_ranges = ((2000, 2071),)

    operating_mode = enum(2000, OperatingMode, writable=True)
    """Selected operating mode. Same as input 1004."""
    state = enum(2001, UnitState, writable=_state_command)
    """Unit state. Takes only VENTILATION and STANDBY as a command."""
    fan_imbalance = integer(2002, unit="%", writable=_in_range(-100, 100))
    """Positive slows the extract fan, negative slows the supply fan.

    Per the vendor sheet. On a WAFE 201 E, writing it changed neither fan speed.
    """
    co2_p = gauge(2003, 0.001, signed=False, writable=_SCALED_PID)
    co2_i = gauge(2004, 0.001, signed=False, writable=_SCALED_PID)
    co2_d = gauge(2005, 0.001, signed=False, writable=_SCALED_PID)
    co2_setpoint = integer(2006, signed=False, unit="ppm", writable=_in_range(0, 5000))
    max_airflow = integer(2007, signed=False, unit="m³/h", writable=_AIRFLOW)
    """The device refuses values above what the model can deliver."""
    min_airflow = integer(2008, signed=False, unit="m³/h", writable=_AIRFLOW)
    manual_airflow = integer(2009, signed=False, unit="m³/h", writable=_AIRFLOW)
    """Airflow in manual mode. The vendor app writes this register too."""
    limited_max_airflow = integer(2010, signed=False, unit="m³/h", writable=_AIRFLOW)
    boost_airflow = integer(2011, signed=False)
    """Undocumented scale. Reads 800 on a unit whose maximum is 220 m³/h.

    The device refuses writes.
    """
    airflow_limit = boolean(2012, writable=True)
    bypass_imbalance = integer(2013, unit="%")
    """The device refuses writes."""
    bypass_min_temperature_difference = gauge(
        2014, 0.1, unit="°C", writable=_TEMPERATURE
    )
    night_bypass_min_temperature_difference = gauge(
        2015, 0.1, unit="°C", writable=_TEMPERATURE
    )
    bypass_airflow = integer(2016, signed=False, unit="m³/h", writable=_AIRFLOW)
    night_bypass_airflow = integer(2017, signed=False, unit="m³/h")
    """The device refuses writes."""
    bypass_start_month = integer(2018, signed=False, nan=0, writable=_MONTH)
    """``None`` until set. The device then takes only 1-12 and never 0 again."""
    bypass_end_month = integer(2019, signed=False, nan=0, writable=_MONTH)
    """Like ``bypass_start_month``."""
    bypass_hysteresis = integer(2020, writable=_in_range(-32768, 32767))
    bypass_min_outdoor_temperature = integer(2021, unit="°C")
    """Undocumented scale. The device refuses writes."""
    bypass_min_indoor_temperature = integer(2022, unit="°C")
    """Undocumented scale. The device refuses writes."""
    night_bypass_min_outdoor_temperature = integer(2023, unit="°C")
    """Undocumented scale. The device refuses writes."""
    night_bypass_min_indoor_temperature = integer(2024, unit="°C")
    """Undocumented scale. The device refuses writes."""
    bypass_by_co2 = boolean(2025, writable=True)
    """0: bypass runs at ``bypass_airflow``, 1: bypass airflow follows CO2."""
    bypass_disabled = boolean(2026, writable=True)
    """Also sets ``Functions.bypass_off``."""
    short_boost_duration = integer(2027, signed=False, unit="s", writable=_DURATION)
    long_boost_duration = integer(2028, signed=False, unit="s", writable=_DURATION)
    compressor_p = gauge(2029, 0.001, signed=False, writable=_SCALED_PID)
    compressor_i = gauge(2030, 0.001, signed=False, writable=_SCALED_PID)
    compressor_d = gauge(2031, 0.001, signed=False, writable=_SCALED_PID)
    compressor_max_comfort_time = integer(2032, signed=False, writable=_DURATION)
    compressor_eco = boolean(2033, writable=True)
    compressor_eco_offset = gauge(2034, 0.1, unit="°C", writable=_TEMPERATURE)
    compressor_hysteresis = gauge(2035, 0.1, unit="°C", writable=_TEMPERATURE)
    compressor_min_co2 = integer(
        2036, signed=False, unit="ppm", writable=_in_range(0, 5000)
    )
    compressor_setpoint = gauge(2037, 0.1, unit="°C", writable=_TEMPERATURE)
    compressor_cooling = boolean(2038, writable=True)
    compressor_heating = boolean(2039, writable=True)
    simulator = boolean(2040, writable=True)
    simulator_sensors = integer(2041, signed=False, writable=_in_range(0, 0b11111))
    """Bit 0 T1, bit 1 T2, bit 2 T3, bit 3 T4, bit 4 CO2.

    The vendor sheet says bit 5 for CO2; the device uses bit 4.
    """
    simulated_outdoor_temperature = gauge(2042, 0.1, unit="°C", writable=_TEMPERATURE)
    simulated_supply_temperature = gauge(2043, 0.1, unit="°C", writable=_TEMPERATURE)
    simulated_extract_temperature = gauge(2044, 0.1, unit="°C", writable=_TEMPERATURE)
    simulated_exhaust_temperature = gauge(2045, 0.1, unit="°C", writable=_TEMPERATURE)
    simulated_co2 = integer(2046, signed=False, unit="ppm", writable=_in_range(0, 5000))
    schedule_index = integer(2047, signed=False, writable=_in_range(0, 255))
    schedule_mode = integer(2048, signed=False)
    schedule_days = integer(2049, signed=False)
    schedule_hours = integer(2050, signed=False)
    schedule_minutes = integer(2051, signed=False)
    preheat_p = integer(2052, signed=False, writable=_PID)
    preheat_i = integer(2053, signed=False, writable=_PID)
    preheat_d = integer(2054, signed=False, writable=_PID)
    preheat_start_temperature = gauge(2055, 0.1, unit="°C", writable=_TEMPERATURE)
    afterheat_p = integer(2056, signed=False, writable=_PID)
    afterheat_i = integer(2057, signed=False, writable=_PID)
    afterheat_d = integer(2058, signed=False, writable=_PID)
    afterheat_start_temperature = gauge(2059, 0.1, unit="°C", writable=_TEMPERATURE)
    afterheat_on_off = boolean(2060, writable=True)
    afterheat_enabled = boolean(2061, writable=True)
    voltdrive_setpoint = integer(2062, writable=_in_range(-32768, 32767))
    voltdrive_p = integer(2063, signed=False, writable=_PID)
    voltdrive_i = integer(2064, signed=False, writable=_PID)
    voltdrive_d = integer(2065, signed=False, writable=_PID)
    voltdrive_min_airflow = integer(2066, signed=False, unit="m³/h")
    """The device refuses writes."""
    voltdrive_input = integer(2067, signed=False, writable=_in_range(0, 2))
    """0: T1, 1: T4, 2: CO2."""
    voltdrive_alternative_input = integer(2068, signed=False, writable=_in_range(0, 2))
    voltdrive_enabled = boolean(2069, writable=True)
    voltdrive_switch_value = integer(2070, writable=_in_range(-32768, 32767))
    voltdrive_on_value = integer(2071, writable=_in_range(-32768, 32767))
