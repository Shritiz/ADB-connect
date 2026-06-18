from PySide6.QtCore import QThread, Signal
from app.core.adb_manager import ADBManager
from app.core.device import Device
import time


class DeviceScanner(QThread):
    """Background thread that scans for connected devices."""

    devices_updated = Signal(list)  # Emits list of Device objects
    error_occurred = Signal(str)    # Emits error message

    def __init__(self, interval: int = 3):
        super().__init__()
        self.adb_manager = ADBManager()
        self.interval = interval
        self.running = False

    def run(self):
        """Scan for devices continuously."""
        self.running = True
        last_devices = []

        while self.running:
            try:
                devices = self.adb_manager.get_device_list()

                # Only emit if devices changed
                if devices != last_devices:
                    self.devices_updated.emit(devices)
                    last_devices = devices

            except Exception as e:
                self.error_occurred.emit(f"Device scan error: {str(e)}")

            # Sleep for the specified interval
            for _ in range(self.interval * 10):
                if not self.running:
                    break
                time.sleep(0.1)

    def stop(self):
        """Stop the scanner thread."""
        self.running = False
        self.wait()
