from PySide6.QtWidgets import QWidget, QVBoxLayout, QListWidget, QListWidgetItem, QLabel
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon, QColor
from app.core.device import Device, DeviceState


class DeviceCard(QListWidgetItem):
    """Custom list item for displaying device information."""

    def __init__(self, device: Device):
        super().__init__()
        self.device = device
        self.update_display()

    def update_display(self):
        """Update the display of the device card."""
        # Create display text
        display_text = f"{self.device.model or 'Unknown'}\n{self.device.serial}"

        if self.device.state == DeviceState.DEVICE:
            status_color = "🟢"
            status_text = "Connected"
        elif self.device.state == DeviceState.OFFLINE:
            status_color = "🔴"
            status_text = "Offline"
        elif self.device.state == DeviceState.UNAUTHORIZED:
            status_color = "🟡"
            status_text = "Unauthorized"
        else:
            status_color = "⚪"
            status_text = "Unknown"

        display_text += f"\n{status_color} {status_text}"

        if self.device.battery_level >= 0:
            display_text += f" | 🔋 {self.device.battery_level}%"

        if self.device.connection:
            display_text += f" | {self.device.connection.value}"

        self.setText(display_text)
        self.setFlags(self.flags() | Qt.ItemIsSelectable | Qt.ItemIsEnabled)


class DevicesPanel(QWidget):
    """Left sidebar panel showing connected devices."""

    devices_selected = Signal(list)  # Emits list of selected Device objects
    device_double_clicked = Signal(Device)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.devices = []
        self.device_items = {}
        self.init_ui()

    def init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # Title
        title = QLabel("Connected Devices")
        title.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(title)

        # Device list
        self.device_list = QListWidget()
        self.device_list.setSelectionMode(QListWidget.MultiSelection)
        self.device_list.itemSelectionChanged.connect(self.on_selection_changed)
        self.device_list.itemDoubleClicked.connect(self.on_device_double_clicked)
        layout.addWidget(self.device_list)

        # Status
        self.status_label = QLabel("No devices")
        self.status_label.setStyleSheet("color: #666; font-size: 10px;")
        layout.addWidget(self.status_label)

    def update_devices(self, devices: list):
        """Update device list."""
        self.devices = devices

        # Update existing items or add new ones
        for device in devices:
            if device.serial in self.device_items:
                # Update existing item
                item = self.device_items[device.serial]
                item.device = device
                item.update_display()
            else:
                # Add new item
                card = DeviceCard(device)
                self.device_list.addItem(card)
                self.device_items[device.serial] = card

        # Remove disconnected devices
        for serial in list(self.device_items.keys()):
            if not any(d.serial == serial for d in devices):
                del self.device_items[serial]
                for i in range(self.device_list.count()):
                    item = self.device_list.item(i)
                    if item.device.serial == serial:
                        self.device_list.takeItem(i)
                        break

        # Update status
        if devices:
            self.status_label.setText(f"{len(devices)} device(s) connected")
        else:
            self.status_label.setText("No devices")
            self.device_list.clear()

    def get_selected_devices(self) -> list:
        """Get currently selected devices."""
        selected = []
        for item in self.device_list.selectedItems():
            selected.append(item.device)
        return selected

    def on_selection_changed(self):
        """Handle device selection change."""
        selected_devices = self.get_selected_devices()
        self.devices_selected.emit(selected_devices)

    def on_device_double_clicked(self, item):
        """Handle device double-click."""
        self.device_double_clicked.emit(item.device)
