"""Device models and abstraction utilities for Meross devices."""

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class DeviceChannel(BaseModel):
    """Channel state representation for a smart plug or multi-channel power strip."""

    channel_id: int = Field(description="Channel index (0 is master or primary channel)")
    name: str = Field(default="", description="Channel name or descriptor")
    is_on: bool | None = Field(default=None, description="Power state of this channel")


class ElectricityData(BaseModel):
    """Real-time electricity telemetry measurements."""

    power_w: float = Field(description="Instant active power in Watts (W)")
    voltage_v: float = Field(description="Instant AC voltage in Volts (V)")
    current_a: float = Field(description="Instant electric current in Amperes (A)")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC measurement timestamp",
    )


class DeviceInfo(BaseModel):
    """Complete device status model."""

    uuid: str = Field(description="Unique device hardware UUID / MAC ID")
    name: str = Field(description="User-assigned friendly name of the device")
    device_type: str = Field(description="Hardware device model (e.g. mss310, mss210, mss425e)")
    online: bool = Field(description="Online reachability status via Meross Cloud MQTT")
    channels: list[DeviceChannel] = Field(default_factory=list, description="Available output channels")
    has_electricity_meter: bool = Field(
        default=False, description="True if this device model measures power/voltage/current"
    )
    wifi_signal: int | None = Field(default=None, description="Wi-Fi signal strength percentage")
    firmware_version: str | None = Field(default=None, description="Firmware version string")


def extract_device_info(device: Any) -> DeviceInfo:
    """Extract standard DeviceInfo from an underlying Meross device object."""
    channels_list: list[DeviceChannel] = []

    # Identify channels
    raw_channels = getattr(device, "channels", None)
    if raw_channels:
        for idx, ch in enumerate(raw_channels):
            ch_id = getattr(ch, "index", idx) if hasattr(ch, "index") else idx
            ch_name = getattr(ch, "name", f"Channel {ch_id}")
            ch_on = None
            if hasattr(device, "is_on"):
                try:
                    ch_on = bool(device.is_on(channel=ch_id))
                except Exception:
                    ch_on = None
            channels_list.append(DeviceChannel(channel_id=ch_id, name=str(ch_name), is_on=ch_on))
    else:
        # Fallback for single-channel device
        ch_on = None
        if hasattr(device, "is_on"):
            try:
                ch_on = bool(device.is_on(channel=0))
            except Exception:
                ch_on = None
        channels_list.append(DeviceChannel(channel_id=0, name="Master", is_on=ch_on))

    # Check power consumption capability
    has_electricity = (
        hasattr(device, "get_electricity")
        or hasattr(device, "get_instant_metrics")
        or "electricity" in getattr(device, "abilities", {})
    )

    # Extract wifi & firmware metadata
    wifi = None
    if hasattr(device, "wifi_status") and device.wifi_status:
        wifi = getattr(device.wifi_status, "signal", None)

    firmware = None
    if hasattr(device, "firmware_version"):
        firmware = str(device.firmware_version)

    return DeviceInfo(
        uuid=str(getattr(device, "uuid", "")),
        name=str(getattr(device, "name", "Unnamed Meross Device")),
        device_type=str(getattr(device, "type", "unknown")),
        online=bool(getattr(device, "online_status", False)),
        channels=channels_list,
        has_electricity_meter=has_electricity,
        wifi_signal=wifi,
        firmware_version=firmware,
    )
