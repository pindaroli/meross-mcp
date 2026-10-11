"""Unit tests for MerossClientManager and device abstraction."""

import pytest

from meross_mcp.client import (
    MerossClientManager,
    MerossDeviceNotFoundError,
    MerossOperationError,
)


@pytest.mark.asyncio
async def test_list_devices(mock_client_manager: MerossClientManager) -> None:
    devices = await mock_client_manager.list_devices()
    assert len(devices) == 2
    assert devices[0].name == "Smart Plug Studio"
    assert devices[0].has_electricity_meter is True
    assert len(devices[1].channels) == 4


@pytest.mark.asyncio
async def test_get_device_by_uuid_and_name(mock_client_manager: MerossClientManager) -> None:
    # Lookup by exact UUID
    dev1 = await mock_client_manager.get_device_info("uuid-plug-mss310")
    assert dev1.name == "Smart Plug Studio"

    # Lookup by friendly name
    dev2 = await mock_client_manager.get_device_info("Ciabatta Scrivania")
    assert dev2.uuid == "uuid-strip-mss425e"

    # Lookup by partial name
    dev3 = await mock_client_manager.get_device_info("Studio")
    assert dev3.uuid == "uuid-plug-mss310"


@pytest.mark.asyncio
async def test_turn_on_and_off(mock_client_manager: MerossClientManager) -> None:
    # Initial state should be OFF
    dev = await mock_client_manager.get_device_info("uuid-plug-mss310")
    assert dev.channels[0].is_on is False

    # Turn ON
    dev_on = await mock_client_manager.turn_on("uuid-plug-mss310", channel=0)
    assert dev_on.channels[0].is_on is True

    # Turn OFF
    dev_off = await mock_client_manager.turn_off("uuid-plug-mss310", channel=0)
    assert dev_off.channels[0].is_on is False


@pytest.mark.asyncio
async def test_toggle_device(mock_client_manager: MerossClientManager) -> None:
    # Starts OFF -> Toggle -> ON
    dev_toggled = await mock_client_manager.toggle("uuid-plug-mss310", channel=0)
    assert dev_toggled.channels[0].is_on is True

    # Toggle again -> OFF
    dev_toggled2 = await mock_client_manager.toggle("uuid-plug-mss310", channel=0)
    assert dev_toggled2.channels[0].is_on is False


@pytest.mark.asyncio
async def test_get_electricity(mock_client_manager: MerossClientManager) -> None:
    power_data = await mock_client_manager.get_electricity("uuid-plug-mss310")
    assert power_data.power_w == 45.5
    assert power_data.voltage_v == 230.2
    assert power_data.current_a == 0.198


@pytest.mark.asyncio
async def test_electricity_unsupported(mock_client_manager: MerossClientManager) -> None:
    with pytest.raises(MerossOperationError):
        await mock_client_manager.get_electricity("uuid-strip-mss425e")


@pytest.mark.asyncio
async def test_device_not_found(mock_client_manager: MerossClientManager) -> None:
    with pytest.raises(MerossDeviceNotFoundError):
        await mock_client_manager.get_device_info("non-existent-device-id")
