"""Asynchronous Client and Connection Manager for Meross Cloud and IoT devices."""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from meross_iot.http_api import MerossHttpClient
from meross_iot.manager import MerossManager

from meross_mcp.config import MerossSettings
from meross_mcp.devices import (
    DeviceInfo,
    ElectricityData,
    extract_device_info,
)

logger = logging.getLogger(__name__)


class MerossDeviceNotFoundError(Exception):
    """Raised when a requested Meross device cannot be found by ID or name."""


class MerossOperationError(Exception):
    """Raised when a Meross device command fails."""


class MerossClientManager:
    """Singleton Connection and Device Manager for Meross Cloud.

    Maintains a persistent MQTT over TLS session to minimize latency and
    prevent cloud rate limits.
    """

    _instance: Optional["MerossClientManager"] = None
    _lock = asyncio.Lock()

    def __init__(self, settings: Optional[MerossSettings] = None):
        """Initialize the client manager with configuration settings."""
        self.settings = settings or MerossSettings()
        self._http_client: Optional[MerossHttpClient] = None
        self._manager: Optional[MerossManager] = None
        self._initialized = False

    @classmethod
    async def get_instance(cls, settings: Optional[MerossSettings] = None) -> "MerossClientManager":
        """Get or initialize the shared singleton manager instance."""
        async with cls._lock:
            if cls._instance is None:
                cls._instance = cls(settings)
            return cls._instance

    async def connect(self) -> None:
        """Authenticate with Meross Cloud and initialize the MQTT manager."""
        if self._initialized and self._manager is not None:
            return

        if not self.settings.email or not self.settings.password:
            raise ValueError(
                "Meross credentials missing! Set MEROSS_EMAIL and MEROSS_PASSWORD."
            )

        logger.info(
            "Connecting to Meross Cloud API at %s for %s...",
            self.settings.api_base_url,
            self.settings.email,
        )

        self._http_client = await MerossHttpClient.async_from_user_password(
            api_base_url=self.settings.api_base_url,
            email=self.settings.email,
            password=self.settings.password,
        )

        self._manager = MerossManager(http_client=self._http_client)
        await self._manager.async_init()
        await self._manager.async_device_discovery()
        self._initialized = True
        logger.info("Connected to Meross Cloud. Discovered %d devices.", len(self._manager.find_devices()))

    async def close(self) -> None:
        """Gracefully shut down MQTT connections and log out from the HTTP API."""
        if self._manager is not None:
            try:
                self._manager.close()
            except Exception as e:
                logger.warning("Error closing MerossManager: %s", e)
            self._manager = None

        if self._http_client is not None:
            try:
                await self._http_client.async_logout()
            except Exception as e:
                logger.warning("Error logging out HTTP client: %s", e)
            self._http_client = None

        self._initialized = False
        logger.info("Meross manager connection closed.")

    async def __aenter__(self) -> "MerossClientManager":
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()

    def _find_raw_device(self, id_or_name: str) -> Any:
        """Find an underlying device object by UUID or friendly name."""
        if not self._manager:
            raise RuntimeError("Meross manager is not connected. Call connect() first.")

        devices = self._manager.find_devices()
        id_or_name_lower = id_or_name.strip().lower()

        # 1. Exact match by UUID
        for dev in devices:
            if str(getattr(dev, "uuid", "")).lower() == id_or_name_lower:
                return dev

        # 2. Exact match by name
        for dev in devices:
            if str(getattr(dev, "name", "")).lower() == id_or_name_lower:
                return dev

        # 3. Partial substring match by name
        for dev in devices:
            if id_or_name_lower in str(getattr(dev, "name", "")).lower():
                return dev

        raise MerossDeviceNotFoundError(
            f"Device '{id_or_name}' not found. Available devices: "
            f"{[getattr(d, 'name', '') for d in devices]}"
        )

    async def list_devices(self, update: bool = True) -> List[DeviceInfo]:
        """List all registered Meross devices and optionally refresh states."""
        await self.connect()
        devices = self._manager.find_devices() if self._manager else []

        if update:
            # Update devices concurrently
            update_tasks = [
                d.async_update()
                for d in devices
                if hasattr(d, "async_update")
            ]
            if update_tasks:
                await asyncio.gather(*update_tasks, return_exceptions=True)

        return [extract_device_info(d) for d in devices]

    async def get_device_info(self, id_or_name: str, update: bool = True) -> DeviceInfo:
        """Get detailed status for a single device."""
        await self.connect()
        dev = self._find_raw_device(id_or_name)
        if update and hasattr(dev, "async_update"):
            await dev.async_update()
        return extract_device_info(dev)

    async def turn_on(self, id_or_name: str, channel: int = 0) -> DeviceInfo:
        """Turn on a plug or a specific channel on a power strip."""
        await self.connect()
        dev = self._find_raw_device(id_or_name)
        if not hasattr(dev, "async_turn_on"):
            raise MerossOperationError(f"Device '{dev.name}' does not support turning on.")

        try:
            await dev.async_turn_on(channel=channel)
            if hasattr(dev, "async_update"):
                await dev.async_update()
        except Exception as e:
            raise MerossOperationError(f"Failed to turn on '{dev.name}' channel {channel}: {e}") from e

        return extract_device_info(dev)

    async def turn_off(self, id_or_name: str, channel: int = 0) -> DeviceInfo:
        """Turn off a plug or a specific channel on a power strip."""
        await self.connect()
        dev = self._find_raw_device(id_or_name)
        if not hasattr(dev, "async_turn_off"):
            raise MerossOperationError(f"Device '{dev.name}' does not support turning off.")

        try:
            await dev.async_turn_off(channel=channel)
            if hasattr(dev, "async_update"):
                await dev.async_update()
        except Exception as e:
            raise MerossOperationError(f"Failed to turn off '{dev.name}' channel {channel}: {e}") from e

        return extract_device_info(dev)

    async def toggle(self, id_or_name: str, channel: int = 0) -> DeviceInfo:
        """Toggle current on/off state of a plug or a specific channel."""
        await self.connect()
        dev = self._find_raw_device(id_or_name)

        if hasattr(dev, "async_toggle"):
            try:
                await dev.async_toggle(channel=channel)
                if hasattr(dev, "async_update"):
                    await dev.async_update()
                return extract_device_info(dev)
            except Exception as e:
                logger.debug("async_toggle failed, falling back to manual toggle: %s", e)

        # Fallback manual toggle: check current status
        current_state = False
        if hasattr(dev, "is_on"):
            try:
                current_state = bool(dev.is_on(channel=channel))
            except Exception:
                pass

        if current_state:
            return await self.turn_off(id_or_name, channel=channel)
        else:
            return await self.turn_on(id_or_name, channel=channel)

    async def get_electricity(self, id_or_name: str) -> ElectricityData:
        """Retrieve real-time power consumption (Watt, Volt, Ampere)."""
        await self.connect()
        dev = self._find_raw_device(id_or_name)

        # Ensure state is fresh
        if hasattr(dev, "async_update"):
            await dev.async_update()

        raw_metrics = None
        if hasattr(dev, "get_electricity"):
            raw_metrics = dev.get_electricity()
        elif hasattr(dev, "get_instant_metrics"):
            raw_metrics = dev.get_instant_metrics()

        if raw_metrics is None:
            raise MerossOperationError(
                f"Device '{dev.name}' ({getattr(dev, 'type', 'unknown')}) does not support electricity telemetry."
            )

        # Extract values (supporting both dict and object attributes)
        if isinstance(raw_metrics, dict):
            power = float(raw_metrics.get("power", 0.0))
            voltage = float(raw_metrics.get("voltage", 0.0))
            current = float(raw_metrics.get("current", 0.0))
        else:
            power = float(getattr(raw_metrics, "power", 0.0))
            voltage = float(getattr(raw_metrics, "voltage", 0.0))
            current = float(getattr(raw_metrics, "current", 0.0))

        return ElectricityData(
            power_w=power,
            voltage_v=voltage,
            current_a=current,
        )
