"""Shared test fixtures and mocks for Meross Dual Gateway testing."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from meross_mcp.client import MerossClientManager
from meross_mcp.config import MerossSettings


class MockChannel:
    """Mock for a single device output channel."""

    def __init__(self, index: int, name: str):
        self.index = index
        self.name = name


class MockPowerInfo:
    """Mock for meross_iot PowerInfo dataclass."""

    def __init__(self, power: float, voltage: float, current: float):
        self._power = power
        self._voltage = voltage
        self._current = current

    @property
    def power(self) -> float:
        return self._power

    @property
    def voltage(self) -> float:
        return self._voltage

    @property
    def current(self) -> float:
        return self._current


class MockDevice:
    """Mock representing a physical Meross smart device."""

    def __init__(
        self,
        uuid: str,
        name: str,
        device_type: str,
        channels: list[MockChannel],
        has_electricity: bool = False,
    ):
        self.uuid = uuid
        self.name = name
        self.type = device_type
        self.online_status = True
        self.channels = channels
        self._has_electricity = has_electricity
        self._states: dict[int, bool] = {ch.index: False for ch in channels}
        self.wifi_status = MagicMock(signal=92)
        self.firmware_version = "4.2.8"

    async def async_update(self) -> None:
        """Simulate device state refresh."""
        pass

    def is_on(self, channel: int = 0) -> bool:
        """Check channel state."""
        return self._states.get(channel, False)

    async def async_turn_on(self, channel: int = 0) -> None:
        """Turn on channel."""
        self._states[channel] = True

    async def async_turn_off(self, channel: int = 0) -> None:
        """Turn off channel."""
        self._states[channel] = False

    async def async_toggle(self, channel: int = 0) -> None:
        """Toggle channel."""
        self._states[channel] = not self._states.get(channel, False)

    async def async_get_instant_metrics(self, channel: int = 0) -> MockPowerInfo | None:
        """Simulate async_get_instant_metrics returning PowerInfo-like object."""
        if not self._has_electricity:
            return None
        return MockPowerInfo(power=45.5, voltage=230.2, current=0.198)

    def get_electricity(self) -> dict[str, float] | None:
        """Return simulated electricity telemetry fallback."""
        if not self._has_electricity:
            return None
        return {"power": 45.5, "voltage": 230.2, "current": 0.198}


@pytest.fixture
def mock_devices() -> list[MockDevice]:
    """Create a list of standard test devices."""
    plug_mss310 = MockDevice(
        uuid="uuid-plug-mss310",
        name="Smart Plug Studio",
        device_type="mss310",
        channels=[MockChannel(index=0, name="Master")],
        has_electricity=True,
    )
    strip_mss425e = MockDevice(
        uuid="uuid-strip-mss425e",
        name="Ciabatta Scrivania",
        device_type="mss425e",
        channels=[
            MockChannel(index=0, name="Main"),
            MockChannel(index=1, name="Monitor"),
            MockChannel(index=2, name="Lampada"),
            MockChannel(index=3, name="Speaker"),
        ],
        has_electricity=False,
    )
    return [plug_mss310, strip_mss425e]


@pytest.fixture
def test_settings() -> MerossSettings:
    """Fixture providing test configuration."""
    return MerossSettings(
        email="developer@example.com",
        password="supersecretpassword",
        api_key="test-api-key",
    )


@pytest.fixture
def mock_client_manager(mock_devices: list[MockDevice], test_settings: MerossSettings) -> MerossClientManager:
    """Fixture providing a connected MerossClientManager with mocked backend."""
    manager = MerossClientManager(test_settings)
    mock_meross_manager = MagicMock()
    mock_meross_manager.find_devices.return_value = mock_devices
    mock_meross_manager.close = MagicMock()

    mock_http_client = AsyncMock()
    mock_http_client.async_logout = AsyncMock()

    manager._manager = mock_meross_manager
    manager._http_client = mock_http_client
    manager._initialized = True

    # Register as singleton
    MerossClientManager._instance = manager
    return manager
