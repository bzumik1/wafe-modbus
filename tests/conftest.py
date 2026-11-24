"""Fixtures: a WAFE 201 E on modbus-connection's in-memory mock backend."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from modbus_connection.mock import MockModbusUnit

from wafe_modbus import WafeUnit

FIXTURES = Path(__file__).parent / "fixtures"


def load_snapshot(name: str) -> dict[str, Any]:
    """Load a raw register snapshot captured from a real unit."""
    data: dict[str, Any] = json.loads((FIXTURES / name).read_text())
    return data


@pytest.fixture
def w201e(mock_modbus_unit: MockModbusUnit) -> MockModbusUnit:
    """A mock unit seeded with a WAFE 201 E in intelligent mode."""
    mock_modbus_unit.load_raw(load_snapshot("w201e.json"))
    return mock_modbus_unit


@pytest.fixture
def device(w201e: MockModbusUnit) -> WafeUnit:
    """The library's device object on the seeded mock unit."""
    return WafeUnit(w201e)
