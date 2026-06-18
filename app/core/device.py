from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class DeviceState(Enum):
    DEVICE = "device"
    OFFLINE = "offline"
    UNAUTHORIZED = "unauthorized"
    UNKNOWN = "unknown"


class ConnectionType(Enum):
    USB = "USB"
    WIFI = "Wi-Fi"
    UNKNOWN = "Unknown"


@dataclass
class Device:
    """Represents an Android device connected via ADB."""
    serial: str
    model: str = ""
    android_version: str = ""
    battery_level: int = -1
    state: DeviceState = DeviceState.UNKNOWN
    connection: ConnectionType = ConnectionType.UNKNOWN
    ip_address: Optional[str] = None
    port: int = 5555
    selected: bool = False

    def __str__(self):
        return f"{self.model or self.serial} ({self.serial})"

    def display_name(self):
        """Return a user-friendly device name."""
        if self.model:
            return f"{self.model} - {self.serial}"
        return self.serial

    def is_connected(self):
        """Check if device is connected and ready."""
        return self.state == DeviceState.DEVICE
