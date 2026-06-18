import re
import subprocess
from typing import List, Optional, Tuple
from app.core.device import Device, DeviceState, ConnectionType
from app.core.constants import ADB_TIMEOUT, ADB_DEFAULT_PORT

try:
    import adbutils
    HAS_ADBUTILS = True
except ImportError:
    HAS_ADBUTILS = False


class ADBManager:
    """Manages ADB operations and device communication."""

    def __init__(self):
        self.timeout = ADB_TIMEOUT
        self.adb = None
        self._init_adb()

    def _init_adb(self):
        """Initialize ADB connection."""
        try:
            if HAS_ADBUTILS:
                self.adb = adbutils.AdbClient(host='127.0.0.1', port=5037)
            else:
                self.adb = None
        except Exception as e:
            print(f"Failed to initialize ADB: {e}")
            self.adb = None

    def get_device_list(self) -> List[Device]:
        """Get list of all connected devices."""
        try:
            if self.adb:
                try:
                    devices = self.adb.device_list()
                    device_list = []
                    for d in devices:
                        device = self._parse_device_info(d)
                        if device:
                            device_list.append(device)
                    return device_list
                except Exception:
                    pass

            # Fallback: use subprocess
            return self._get_devices_via_subprocess()
        except Exception as e:
            print(f"Error getting device list: {e}")
            return []

    def _parse_device_info(self, device) -> Optional[Device]:
        """Parse device info from adbutils device object."""
        try:
            serial = device.serial
            state_str = str(device.get_state())

            # Determine state
            if "device" in state_str.lower():
                state = DeviceState.DEVICE
            elif "offline" in state_str.lower():
                state = DeviceState.OFFLINE
            elif "unauthorized" in state_str.lower():
                state = DeviceState.UNAUTHORIZED
            else:
                state = DeviceState.UNKNOWN

            # Get device properties
            model = self._get_device_property(device, "ro.product.model") or "Unknown"
            android_version = self._get_device_property(device, "ro.build.version.release") or ""
            battery = self._get_battery_level(device)

            # Determine connection type
            if ":" in serial:
                connection = ConnectionType.WIFI
                ip, port = serial.rsplit(":", 1)
            else:
                connection = ConnectionType.USB
                ip = None

            return Device(
                serial=serial,
                model=model,
                android_version=android_version,
                battery_level=battery,
                state=state,
                connection=connection,
                ip_address=ip,
                port=int(port) if ":" in serial else ADB_DEFAULT_PORT,
            )
        except Exception as e:
            print(f"Error parsing device info: {e}")
            return None

    def _get_device_property(self, device, prop_name: str) -> Optional[str]:
        """Get a device property."""
        try:
            result = device.shell(f"getprop {prop_name}")
            return result.strip() if result else None
        except Exception:
            return None

    def _get_battery_level(self, device) -> int:
        """Get battery level from device."""
        try:
            result = device.shell("dumpsys battery | grep level")
            match = re.search(r'level:\s*(\d+)', result)
            if match:
                return int(match.group(1))
        except Exception:
            pass
        return -1

    def _get_devices_via_subprocess(self) -> List[Device]:
        """Fallback method using subprocess to get devices."""
        try:
            result = subprocess.run(
                ["adb", "devices", "-l"],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )

            devices = []
            for line in result.stdout.split("\n")[1:]:
                line = line.strip()
                if not line:
                    continue

                parts = line.split()
                if len(parts) < 2:
                    continue

                serial = parts[0]
                state_str = parts[1]

                # Determine state
                if state_str == "device":
                    state = DeviceState.DEVICE
                elif state_str == "offline":
                    state = DeviceState.OFFLINE
                elif state_str == "unauthorized":
                    state = DeviceState.UNAUTHORIZED
                else:
                    state = DeviceState.UNKNOWN

                # Extract model if present
                model = ""
                for part in parts[2:]:
                    if part.startswith("model:"):
                        model = part.split(":", 1)[1]
                        break

                if ":" in serial:
                    connection = ConnectionType.WIFI
                    ip, port = serial.rsplit(":", 1)
                else:
                    connection = ConnectionType.USB
                    ip = None

                device = Device(
                    serial=serial,
                    model=model or "Unknown",
                    state=state,
                    connection=connection,
                    ip_address=ip,
                    port=int(port) if ":" in serial else ADB_DEFAULT_PORT,
                )
                devices.append(device)

            return devices
        except Exception as e:
            print(f"Error in subprocess device list: {e}")
            return []

    def shell(self, device_serial: str, command: str) -> str:
        """Execute a shell command on device."""
        try:
            if self.adb:
                device = self.adb.device(device_serial)
                return device.shell(command)
            else:
                result = subprocess.run(
                    ["adb", "-s", device_serial, "shell", command],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout
                )
                return result.stdout
        except Exception as e:
            return f"Error: {e}"

    def input_tap(self, device_serial: str, x: int, y: int) -> bool:
        """Send tap input to device."""
        return self._run_command(device_serial, f"shell input tap {x} {y}")

    def input_swipe(self, device_serial: str, x1: int, y1: int, x2: int, y2: int, duration: int = 500) -> bool:
        """Send swipe input to device."""
        return self._run_command(device_serial, f"shell input swipe {x1} {y1} {x2} {y2} {duration}")

    def input_text(self, device_serial: str, text: str) -> bool:
        """Send text input to device."""
        # Escape spaces and special characters
        escaped_text = text.replace(" ", "\\ ").replace("'", "\\'")
        return self._run_command(device_serial, f'shell input text "{escaped_text}"')

    def input_keyevent(self, device_serial: str, keycode: int) -> bool:
        """Send key event to device."""
        return self._run_command(device_serial, f"shell input keyevent {keycode}")

    def get_screenshot(self, device_serial: str) -> Optional[bytes]:
        """Get screenshot from device."""
        try:
            if self.adb:
                device = self.adb.device(device_serial)
                # Get screenshot in PPM format
                return device.shell("screencap -p", encoding=None)
            else:
                # Use exec-out for direct binary output (PNG format)
                result = subprocess.run(
                    ["adb", "-s", device_serial, "exec-out", "screencap"],
                    capture_output=True,
                    timeout=self.timeout
                )
                return result.stdout if result.returncode == 0 else None
        except Exception as e:
            print(f"Error getting screenshot: {e}")
            return None

    def push_file(self, device_serial: str, local_path: str, remote_path: str) -> bool:
        """Push file to device."""
        return self._run_command(device_serial, f"push {local_path} {remote_path}")

    def pull_file(self, device_serial: str, remote_path: str, local_path: str) -> bool:
        """Pull file from device."""
        return self._run_command(device_serial, f"pull {remote_path} {local_path}")

    def list_files(self, device_serial: str, path: str) -> str:
        """List files on device."""
        return self.shell(device_serial, f'ls -la "{path}"')

    def mkdir(self, device_serial: str, path: str) -> bool:
        """Create directory on device."""
        return self._run_command(device_serial, f"shell mkdir {path}")

    def remove_file(self, device_serial: str, path: str) -> bool:
        """Remove file from device."""
        return self._run_command(device_serial, f"shell rm {path}")

    def rename_file(self, device_serial: str, old_path: str, new_path: str) -> bool:
        """Rename file on device."""
        return self._run_command(device_serial, f"shell mv {old_path} {new_path}")

    def logcat(self, device_serial: str, *args) -> str:
        """Get logcat output from device."""
        cmd = ["adb", "-s", device_serial, "logcat"] + list(args)
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=2  # Short timeout for logcat check
            )
            return result.stdout
        except Exception as e:
            return f"Error: {e}"

    def reboot(self, device_serial: str) -> bool:
        """Reboot device."""
        return self._run_command(device_serial, "reboot")

    def connect_wireless(self, ip: str, port: int = ADB_DEFAULT_PORT) -> bool:
        """Connect to device via Wi-Fi."""
        return self._run_command_global(f"connect {ip}:{port}")

    def pair_wireless(self, ip: str, port: int, code: str) -> bool:
        """Pair with device via Wi-Fi."""
        return self._run_command_global(f"pair {ip}:{port} {code}")

    def disconnect(self, device_serial: str) -> bool:
        """Disconnect from device."""
        return self._run_command_global(f"disconnect {device_serial}")

    def _run_command(self, device_serial: str, command: str) -> bool:
        """Execute an adb command and return success status."""
        try:
            result = subprocess.run(
                ["adb", "-s", device_serial] + command.split(),
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            return result.returncode == 0
        except Exception as e:
            print(f"Error running command: {e}")
            return False

    def _run_command_global(self, command: str) -> bool:
        """Execute a global adb command."""
        try:
            result = subprocess.run(
                ["adb"] + command.split(),
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            return result.returncode == 0
        except Exception as e:
            print(f"Error running global command: {e}")
            return False

    def kill_server(self) -> bool:
        """Kill ADB server."""
        return self._run_command_global("kill-server")

    def start_server(self) -> bool:
        """Start ADB server."""
        return self._run_command_global("start-server")
