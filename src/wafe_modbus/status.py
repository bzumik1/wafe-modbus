"""Live values, the input registers 1000-1012."""

from __future__ import annotations

from modbus_connection.model import Component, enum, flags, gauge, integer

from .enums import Model, OperatingMode, SubMode, UnitState

__all__ = ["Identity", "Status"]

_INPUT_RANGES = ((1000, 1012),)


class Identity(Component):
    """What the unit is, read once."""

    register_space = "input"
    register_ranges = _INPUT_RANGES

    unit_id = integer(1000, signed=False)
    """Identifier of the unit in the vendor cloud. Unique per unit."""
    model = enum(1001, Model)


class Status(Component):
    """What the unit measures and is doing."""

    register_space = "input"
    register_ranges = _INPUT_RANGES

    state = enum(1002, UnitState)
    sub_mode = flags(1003, SubMode)
    operating_mode = enum(1004, OperatingMode)
    outdoor_temperature = gauge(1005, 0.1, unit="°C")
    """T1, outdoor air entering the unit."""
    supply_temperature = gauge(1006, 0.1, unit="°C")
    """T2, fresh air the unit supplies to the rooms."""
    extract_temperature = gauge(1007, 0.1, unit="°C")
    """T3, room air the unit extracts."""
    exhaust_temperature = gauge(1008, 0.1, unit="°C")
    """T4, waste air the unit blows outside."""
    co2 = integer(1009, signed=False, unit="ppm")
    fan_1_speed = integer(1010, signed=False, unit="rpm")
    """Undocumented. Speed of one fan.

    Falls to 0 when the fans stop and ramps up with them. Whether it is the
    supply or the extract fan is not confirmed.
    """
    fan_2_speed = integer(1011, signed=False, unit="rpm")
    """Undocumented. Speed of the other fan."""
    target_airflow = integer(1012, signed=False, unit="m³/h")
    """Undocumented. The airflow the unit currently aims for.

    The manual airflow in manual mode, the CO2 demand in intelligent mode, the
    maximum during a boost, the silent mode cap, and 0 in standby. The unit does
    not measure the airflow it actually delivers.
    """

    @property
    def bypass_active(self) -> bool | None:
        """Whether the summer bypass is open."""
        sub_mode = self.sub_mode
        return None if sub_mode is None else SubMode.BYPASS in sub_mode
