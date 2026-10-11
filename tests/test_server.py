"""Functional tests for FastMCP tools."""

import pytest

from meross_mcp.client import MerossClientManager
from meross_mcp.server import (
    meross_get_device_state,
    meross_get_electricity,
    meross_list_devices,
    meross_toggle,
    meross_turn_off,
    meross_turn_on,
)


@pytest.mark.asyncio
async def test_mcp_list_devices(mock_client_manager: MerossClientManager) -> None:
    devices = await meross_list_devices()
    assert len(devices) == 2
    assert devices[0].name == "Smart Plug Studio"
    assert devices[1].name == "Ciabatta Scrivania"


@pytest.mark.asyncio
async def test_mcp_get_device_state(mock_client_manager: MerossClientManager) -> None:
    dev = await meross_get_device_state("Smart Plug Studio")
    assert dev.uuid == "uuid-plug-mss310"
    assert dev.online is True
    assert dev.wifi_signal == 92


@pytest.mark.asyncio
async def test_mcp_turn_on_and_off(mock_client_manager: MerossClientManager) -> None:
    # Turn ON
    dev_on = await meross_turn_on("uuid-plug-mss310", channel=0)
    assert dev_on.channels[0].is_on is True

    # Turn OFF
    dev_off = await meross_turn_off("uuid-plug-mss310", channel=0)
    assert dev_off.channels[0].is_on is False


@pytest.mark.asyncio
async def test_mcp_toggle(mock_client_manager: MerossClientManager) -> None:
    # Toggle from OFF to ON
    dev_toggled = await meross_toggle("uuid-plug-mss310", channel=0)
    assert dev_toggled.channels[0].is_on is True


@pytest.mark.asyncio
async def test_mcp_get_electricity(mock_client_manager: MerossClientManager) -> None:
    power = await meross_get_electricity("Smart Plug Studio")
    assert power.power_w == 45.5
    assert power.voltage_v == 230.2
    assert power.current_a == 0.198
