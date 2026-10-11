"""Meross Dual Gateway (MCP Server + REST API Gateway + Python Library)."""

from meross_mcp.client import (
    MerossClientManager,
    MerossDeviceNotFoundError,
    MerossOperationError,
)
from meross_mcp.config import MerossSettings
from meross_mcp.devices import (
    DeviceChannel,
    DeviceInfo,
    ElectricityData,
)

__version__ = "0.1.0"
__all__ = [
    "MerossClientManager",
    "MerossSettings",
    "DeviceInfo",
    "DeviceChannel",
    "ElectricityData",
    "MerossDeviceNotFoundError",
    "MerossOperationError",
    "__version__",
]
