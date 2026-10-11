"""Meross Dual Gateway (MCP Server + REST API Gateway + Python Library)."""

from meross_mcp.app import create_app
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
from meross_mcp.server import mcp

__version__ = "0.1.0"
__all__ = [
    "MerossClientManager",
    "MerossSettings",
    "DeviceInfo",
    "DeviceChannel",
    "ElectricityData",
    "MerossDeviceNotFoundError",
    "MerossOperationError",
    "create_app",
    "mcp",
    "__version__",
]
