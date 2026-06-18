import json
import os
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Optional
from app.core.device import Device, DeviceState, ConnectionType


@dataclass
class SavedDevice:
    """Represents a saved device that can be reconnected to."""
    name: str
    serial: str
    model: str
    last_ip: Optional[str] = None
    last_port: int = 5555
    connection_type: str = "USB"  # USB or Wi-Fi


class DeviceRegistry:
    """Manages saved devices and persistent storage."""

    CONFIG_DIR = Path.home() / ".adb_control_center"
    DEVICES_FILE = CONFIG_DIR / "devices.json"

    def __init__(self):
        self.saved_devices: List[SavedDevice] = []
        self.config_dir = self.CONFIG_DIR
        self.config_dir.mkdir(exist_ok=True)
        self.load_devices()

    def load_devices(self):
        """Load previously saved devices from disk."""
        try:
            if self.DEVICES_FILE.exists():
                with open(self.DEVICES_FILE, 'r') as f:
                    data = json.load(f)
                    self.saved_devices = [
                        SavedDevice(**device) for device in data.get('devices', [])
                    ]
                print(f"Loaded {len(self.saved_devices)} saved devices")
            else:
                self.saved_devices = []
        except Exception as e:
            print(f"Error loading devices: {e}")
            self.saved_devices = []

    def save_devices(self):
        """Save devices to disk."""
        try:
            data = {'devices': [asdict(d) for d in self.saved_devices]}
            with open(self.DEVICES_FILE, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"Saved {len(self.saved_devices)} devices")
        except Exception as e:
            print(f"Error saving devices: {e}")

    def add_device(self, device: Device, name: str = None):
        """Add or update a device in the registry."""
        device_name = name or device.model or device.serial

        # Remove if already exists
        self.saved_devices = [
            d for d in self.saved_devices if d.serial != device.serial
        ]

        # Add new device
        saved = SavedDevice(
            name=device_name,
            serial=device.serial,
            model=device.model,
            last_ip=device.ip_address,
            last_port=device.port,
            connection_type=device.connection.value
        )
        self.saved_devices.append(saved)
        self.save_devices()

    def get_device(self, serial: str) -> Optional[SavedDevice]:
        """Get a saved device by serial."""
        for device in self.saved_devices:
            if device.serial == serial:
                return device
        return None

    def remove_device(self, serial: str):
        """Remove a device from the registry."""
        self.saved_devices = [
            d for d in self.saved_devices if d.serial != serial
        ]
        self.save_devices()

    def update_device_ip(self, serial: str, ip: str, port: int = 5555):
        """Update device IP and port for Wi-Fi connections."""
        for device in self.saved_devices:
            if device.serial == serial:
                device.last_ip = ip
                device.last_port = port
                device.connection_type = "Wi-Fi"
                self.save_devices()
                break

    def get_all_saved_devices(self) -> List[SavedDevice]:
        """Get all saved devices."""
        return self.saved_devices

    def merge_devices(self, online_devices: List[Device]) -> List[dict]:
        """
        Merge online devices with saved devices.
        Returns list of dicts with online and saved device info.
        """
        result = []
        seen_serials = set()

        # Add online devices first
        for device in online_devices:
            result.append({
                'device': device,
                'saved': self.get_device(device.serial),
                'is_online': True
            })
            seen_serials.add(device.serial)

        # Add offline saved devices
        for saved in self.saved_devices:
            if saved.serial not in seen_serials:
                result.append({
                'device': None,
                'saved': saved,
                'is_online': False
            })

        return result
