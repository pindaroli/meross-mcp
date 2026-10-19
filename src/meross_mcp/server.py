"""Model Context Protocol (MCP) server implementation for Meross devices."""


from fastmcp import FastMCP

from meross_mcp.client import MerossClientManager
from meross_mcp.devices import DeviceInfo, ElectricityData

mcp = FastMCP(
    "meross-mcp",
    instructions="Zero-install Model Context Protocol (MCP) server for Meross smart plugs and power strips",
)


@mcp.tool()
async def meross_list_devices(update: bool = True) -> list[DeviceInfo]:
    """List all registered Meross smart plugs and power strips with their current status."""
    client = await MerossClientManager.get_instance()
    return await client.list_devices(update=update)


@mcp.tool()
async def meross_get_device_state(device_id_or_name: str, update: bool = True) -> DeviceInfo:
    """Get detailed state, power status and channels for a single Meross device by UUID or friendly name."""
    client = await MerossClientManager.get_instance()
    return await client.get_device_info(device_id_or_name, update=update)


@mcp.tool()
async def meross_turn_on(device_id_or_name: str, channel: int = 0) -> DeviceInfo:
    """Turn on a Meross smart plug or a specific channel on a multi-channel strip."""
    client = await MerossClientManager.get_instance()
    return await client.turn_on(device_id_or_name, channel=channel)


@mcp.tool()
async def meross_turn_off(device_id_or_name: str, channel: int = 0) -> DeviceInfo:
    """Turn off a Meross smart plug or a specific channel on a multi-channel strip."""
    client = await MerossClientManager.get_instance()
    return await client.turn_off(device_id_or_name, channel=channel)


@mcp.tool()
async def meross_toggle(device_id_or_name: str, channel: int = 0) -> DeviceInfo:
    """Toggle current on/off power state of a Meross plug or a specific channel."""
    client = await MerossClientManager.get_instance()
    return await client.toggle(device_id_or_name, channel=channel)


@mcp.tool()
async def meross_get_electricity(device_id_or_name: str, channel: int = 0) -> ElectricityData:
    """Read instant power consumption telemetry (Watts, Volts, Amperes) from power-metering plugs (e.g. MSS310)."""
    client = await MerossClientManager.get_instance()
    return await client.get_electricity(device_id_or_name, channel=channel)
