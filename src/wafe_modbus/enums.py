"""Enumerations of the WAFE ACE2 controller."""

from __future__ import annotations

from enum import IntEnum, IntFlag

__all__ = ["Model", "OperatingMode", "SubMode", "UnitState"]


class Model(IntEnum):
    """Unit model, input register 1001."""

    W200 = 0
    W201 = 1
    W1000 = 2
    W1100S = 3
    W1100M = 4
    W1100JF = 5
    W1100JC = 6
    W350E = 7


class UnitState(IntEnum):
    """What the unit is doing, input register 1002."""

    NONE = 0
    VENTILATION = 1
    STANDBY = 2
    HOLIDAY = 3
    MANUAL = 4


class SubMode(IntFlag):
    """Extra conditions on top of the unit state, input register 1003."""

    BYPASS = 1
    HOLIDAY_VENTILATION = 2
    CO2_TEST = 4
    STANDBY_AUTO = 8


class OperatingMode(IntEnum):
    """Selected operating mode, input register 1004 and holding register 2000.

    The value is the index of the active mode coil 0-3. The vendor sheet lists
    a different order, which the device does not follow.
    """

    INTELLIGENT = 0
    SCHEDULER = 1
    MANUAL = 2
    ULTRA_SAVING = 3
