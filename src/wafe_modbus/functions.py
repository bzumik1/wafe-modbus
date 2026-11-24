"""Modes and functions, the coils 0-13."""

from __future__ import annotations

from modbus_connection.model import Component, coil

from .enums import OperatingMode

__all__ = ["Functions", "MODE_COILS"]


class Functions(Component):
    """Mode selection and on/off functions."""

    coil_ranges = ((0, 13),)

    intelligent = coil(0, writable=True)
    """Intelligent mode, ventilation follows CO2."""
    scheduler = coil(1, writable=True)
    """Scheduler mode, ventilation follows the weekly plan.

    With an empty plan the fans stop.
    """
    manual = coil(2, writable=True)
    """Manual mode, ventilation runs at the manual airflow."""
    ultra_saving = coil(3, writable=True)
    """Ultra-saving mode."""
    sleep = coil(4, writable=True)
    """Standby, the fans stop."""
    holiday = coil(5, writable=True)
    """Holiday mode, low energy with one airing a day."""
    silent = coil(6, writable=True)
    """Silent mode, caps the fan power."""
    short_boost = coil(7, writable=True)
    """Short boost, ends by itself after the short boost duration.

    While either boost runs, the device reports both boost coils set. Clearing
    either coil ends any running boost.
    """
    long_boost = coil(8, writable=True)
    """Long boost, ends by itself after the long boost duration."""
    bypass_off = coil(9, writable=True)
    """Keeps the summer bypass closed. Follows ``Settings.bypass_disabled``."""
    fireplace = coil(10, writable=True)
    """Fireplace mode, slight overpressure so smoke goes up the chimney.

    Has no effect until an installer enables fireplace mode on the unit.
    """
    scheduler_clear = coil(11)
    """Scheduler command: clear the plan. Not exposed for writing."""
    scheduler_operational = coil(12)
    """Scheduler command. Meaning undocumented. Not exposed for writing."""
    scheduler_save = coil(13)
    """Scheduler command: store the selected slot. Not exposed for writing."""

    @property
    def operating_mode(self) -> OperatingMode | None:
        """The mode whose coil is set, or ``None`` if none or several are."""
        active = [mode for mode, name in MODE_COILS.items() if getattr(self, name)]
        return active[0] if len(active) == 1 else None

    @property
    def boost_active(self) -> bool | None:
        """Whether a boost runs."""
        short, long = self.short_boost, self.long_boost
        if short is None or long is None:
            return None
        return short or long

    async def async_start_boost(self, *, long: bool = False) -> None:
        """Start the short boost, or the long boost."""
        await self.write("long_boost" if long else "short_boost", True)

    async def async_stop_boost(self) -> None:
        """End any running boost."""
        await self.write("short_boost", False)

    async def async_set_operating_mode(self, mode: OperatingMode) -> None:
        """Select a mode. The device clears the other mode coils itself."""
        await self.write(MODE_COILS[mode], True)


MODE_COILS: dict[OperatingMode, str] = {
    OperatingMode.INTELLIGENT: "intelligent",
    OperatingMode.SCHEDULER: "scheduler",
    OperatingMode.MANUAL: "manual",
    OperatingMode.ULTRA_SAVING: "ultra_saving",
}
"""The coil that selects each operating mode."""
