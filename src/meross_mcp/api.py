"""FastAPI REST API router for Meross devices."""


from fastapi import APIRouter, Depends, Header, HTTPException, Query, status

from meross_mcp.client import (
    MerossClientManager,
    MerossDeviceNotFoundError,
    MerossOperationError,
)
from meross_mcp.devices import DeviceInfo, ElectricityData

router = APIRouter(prefix="/api/v1/devices", tags=["Devices"])


async def get_client() -> MerossClientManager:
    """Dependency that returns the shared MerossClientManager instance."""
    return await MerossClientManager.get_instance()


async def verify_api_key(
    x_api_key: str | None = Header(None, alias="X-API-Key"),
    client: MerossClientManager = Depends(get_client),
) -> None:
    """Verify API Key on mutative operations if configured in settings."""
    required_key = client.settings.api_key
    if required_key:
        if not x_api_key or x_api_key != required_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing X-API-Key header",
            )


@router.get(
    "",
    response_model=list[DeviceInfo],
    summary="List all devices",
    description="Retrieve all registered Meross plugs and power strips with current state.",
)
async def list_devices(
    update: bool = Query(True, description="Query devices in real-time via MQTT"),
    client: MerossClientManager = Depends(get_client),
) -> list[DeviceInfo]:
    try:
        return await client.list_devices(update=update)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list Meross devices: {e}",
        ) from e


@router.get(
    "/{device_id}",
    response_model=DeviceInfo,
    summary="Get device details",
    description="Retrieve detailed status and channels for a single Meross device by UUID or name.",
)
async def get_device(
    device_id: str,
    update: bool = Query(True, description="Query device in real-time via MQTT"),
    client: MerossClientManager = Depends(get_client),
) -> DeviceInfo:
    try:
        return await client.get_device_info(device_id, update=update)
    except MerossDeviceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inspecting device '{device_id}': {e}",
        ) from e


@router.post(
    "/{device_id}/on",
    response_model=DeviceInfo,
    dependencies=[Depends(verify_api_key)],
    summary="Turn on device",
    description="Turn on the plug or a specific channel on a multi-channel strip.",
)
async def turn_on_device(
    device_id: str,
    channel: int = Query(0, description="Output channel index (0 is master or primary)"),
    client: MerossClientManager = Depends(get_client),
) -> DeviceInfo:
    try:
        return await client.turn_on(device_id, channel=channel)
    except MerossDeviceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except MerossOperationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to turn on device '{device_id}': {e}",
        ) from e


@router.post(
    "/{device_id}/off",
    response_model=DeviceInfo,
    dependencies=[Depends(verify_api_key)],
    summary="Turn off device",
    description="Turn off the plug or a specific channel on a multi-channel strip.",
)
async def turn_off_device(
    device_id: str,
    channel: int = Query(0, description="Output channel index (0 is master or primary)"),
    client: MerossClientManager = Depends(get_client),
) -> DeviceInfo:
    try:
        return await client.turn_off(device_id, channel=channel)
    except MerossDeviceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except MerossOperationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to turn off device '{device_id}': {e}",
        ) from e


@router.post(
    "/{device_id}/toggle",
    response_model=DeviceInfo,
    dependencies=[Depends(verify_api_key)],
    summary="Toggle device power",
    description="Invert the on/off power state of the plug or a specific channel.",
)
async def toggle_device(
    device_id: str,
    channel: int = Query(0, description="Output channel index (0 is master or primary)"),
    client: MerossClientManager = Depends(get_client),
) -> DeviceInfo:
    try:
        return await client.toggle(device_id, channel=channel)
    except MerossDeviceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except MerossOperationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to toggle device '{device_id}': {e}",
        ) from e


@router.get(
    "/{device_id}/power",
    response_model=ElectricityData,
    summary="Get power consumption",
    description="Retrieve real-time electricity telemetry (Watts, Volts, Amperes) from power-metering plugs.",
)
async def get_electricity(
    device_id: str,
    client: MerossClientManager = Depends(get_client),
) -> ElectricityData:
    try:
        return await client.get_electricity(device_id)
    except MerossDeviceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except MerossOperationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read electricity from '{device_id}': {e}",
        ) from e
