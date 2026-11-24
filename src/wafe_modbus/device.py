"""The top-level object for a WAFE heat recovery unit."""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING, Final

from modbus_connection.model import Device, Raw, UpdateReport

from .enums import Model, OperatingMode
from .functions import Functions
from .settings import Settings
from .status import Identity, Status

if TYPE_CHECKING:
    from modbus_connection import ModbusUnit

__all__ = ["ALL", "READINGS", "SETTINGS", "WafeUnit"]

READINGS: Final = ("status", "functions")
"""The sub-systems that change on their own."""
SETTINGS: Final = ("settings",)
"""The sub-systems that change only when someone configures the unit."""
ALL: Final = ("identity", *READINGS, *SETTINGS)


class WafeUnit(Device):
    """A WAFE heat recovery unit with an ACE2 controller.

    Reached through a ``ModbusUnit``.

    The controller serves one Modbus TCP client at a time and ignores the unit
    id. Keep a single connection to it.
    """

    def __init__(self, unit: ModbusUnit) -> None:
        super().__init__(unit)
        self.identity = Identity(unit)
        self.status = Status(unit)
        self.functions = Functions(unit)
        self.settings = Settings(unit)

    async def _async_setup(self) -> None:
        """Read the identity, which never changes."""
        await self.identity.async_update()

    @property
    def unit_id(self) -> int | None:
        """Identifier of the unit in the vendor cloud, unique per unit."""
        return self.identity.unit_id

    @property
    def model(self) -> Model | None:
        """The unit model."""
        return self.identity.model

    async def async_update_readings(self) -> UpdateReport:
        """Refresh the live values and the mode coils."""
        return await self.async_poll(READINGS)

    async def async_update_settings(self) -> UpdateReport:
        """Refresh the configuration."""
        return await self.async_poll(SETTINGS)

    async def async_update(self) -> UpdateReport:
        """Refresh everything."""
        report = await self.async_poll(READINGS)
        return await self.async_poll(SETTINGS, report)

    async def async_read_raw(self, names: Iterable[str] = ALL) -> Raw:
        """Every register this library reads, undecoded, for diagnostics."""
        return await super().async_read_raw(names)

    async def async_set_operating_mode(self, mode: OperatingMode) -> None:
        """Select the operating mode."""
        await self.functions.async_set_operating_mode(mode)

    async def async_set_manual_airflow(self, airflow: int) -> None:
        """Set the manual airflow, in m³/h, within the configured limits.

        Reads the limits fresh, so a stale poll does not let a value through.
        """
        await self.settings.async_update()
        low, high = self.settings.min_airflow, self.settings.max_airflow
        if low is None or high is None or not low <= airflow <= high:
            raise ValueError(f"airflow {airflow} is outside {low}-{high} m³/h")
        await self.settings.write("manual_airflow", airflow)
