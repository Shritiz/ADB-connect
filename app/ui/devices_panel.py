from PySide6.QtWidgets import QWidget, QVBoxLayout, QListWidget, QListWidgetItem, QLabel, QPushButton, QHBoxLayout
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon, QColor, QFont
from app.core.device import Device, DeviceState, ConnectionType
from app.core.device_registry import DeviceRegistry, SavedDevice
from app.core.connection_manager import ConnectionManager


class DeviceCard(QListWidgetItem):
    """Custom list item for displaying device information."""

    def __init__(self, device: Device = None, saved_device: SavedDevice = None, is_online: bool = False):
        super().__init__()
        self.device = device
        self.saved_device = saved_device
        self.is_online = is_online
        self.update_display()

    def update_display(self):
        """Update the display of the device card."""
        if self.is_online and self.device:
            # Online device
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
            self.setForeground(QColor("black"))
            self.setFont(self._get_font(bold=True))

        else:
            # Offline saved device
            display_text = f"{self.saved_device.name}\n{self.saved_device.serial}"
            display_text += f"\n⚫ Offline (saved)"

            if self.saved_device.last_ip:
                display_text += f" | Last IP: {self.saved_device.last_ip}"

            self.setText(display_text)
            # Grey out offline devices
            self.setForeground(QColor("#999999"))
            self.setFont(self._get_font(bold=False))

        self.setFlags(self.flags() | Qt.ItemIsSelectable | Qt.ItemIsEnabled)

    def _get_font(self, bold=False):
        """Get font for display."""
        font = QFont()
        font.setBold(bold)
        return font

    def get_serial(self):
        """Get device serial."""
        if self.device:
            return self.device.serial
        elif self.saved_device:
            return self.saved_device.serial
        return None


class DevicesPanel(QWidget):
    """Left sidebar panel showing connected and saved devices."""

    devices_selected = Signal(list)  # Emits list of selected Device objects
    device_double_clicked = Signal(Device)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.devices = []
        self.device_items = {}
        self.registry = DeviceRegistry()
        self.init_ui()
        self.load_saved_devices()

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
        layout.addWidget(self.device_list)

        # Reconnect button for offline devices
        reconnect_layout = QHBoxLayout()
        self.reconnect_btn = QPushButton("Reconnect Selected")
        self.reconnect_btn.clicked.connect(self.reconnect_selected)
        self.reconnect_btn.setEnabled(False)
        reconnect_layout.addWidget(self.reconnect_btn)

        forget_btn = QPushButton("Forget")
        forget_btn.clicked.connect(self.forget_selected)
        reconnect_layout.addWidget(forget_btn)

        layout.addLayout(reconnect_layout)

        # Status
        self.status_label = QLabel("Loading saved devices...")
        self.status_label.setStyleSheet("color: #666; font-size: 10px;")
        layout.addWidget(self.status_label)

    def load_saved_devices(self):
        """Load previously saved devices from registry."""
        saved = self.registry.get_all_saved_devices()
        self.status_label.setText(f"Loaded {len(saved)} saved device(s)")

    def update_devices(self, devices: list):
        """Update device list with online devices."""
        self.devices = devices

        # Get merged list of online and offline devices
        merged = self.registry.merge_devices(devices)

        # Update existing items or add new ones
        self.device_list.clear()
        self.device_items = {}

        for item_data in merged:
            device = item_data['device']
            saved = item_data['saved']
            is_online = item_data['is_online']

            serial = device.serial if device else saved.serial
            card = DeviceCard(device=device, saved_device=saved, is_online=is_online)
            self.device_list.addItem(card)
            self.device_items[serial] = card

        # Update status
        online_count = len([d for d in merged if d['is_online']])
        offline_count = len([d for d in merged if not d['is_online']])

        if online_count > 0 or offline_count > 0:
            self.status_label.setText(
                f"{online_count} online, {offline_count} offline"
            )
        else:
            self.status_label.setText("No devices")

    def get_selected_devices(self) -> list:
        """Get currently selected devices (online only)."""
        selected = []
        for item in self.device_list.selectedItems():
            if item.is_online and item.device:
                selected.append(item.device)
        return selected

    def on_selection_changed(self):
        """Handle device selection change."""
        selected = self.get_selected_devices()
        has_offline = any(
            item for item in self.device_list.selectedItems()
            if not item.is_online
        )
        self.reconnect_btn.setEnabled(has_offline)
        self.devices_selected.emit(selected)

    def reconnect_selected(self):
        """Attempt to reconnect to selected offline devices."""
        for item in self.device_list.selectedItems():
            if not item.is_online and item.saved_device:
                self.status_label.setText(f"Reconnecting {item.saved_device.name}...")
                result = ConnectionManager.auto_reconnect_wifi(item.saved_device)
                if result:
                    ip, port = result
                    self.registry.update_device_ip(item.saved_device.serial, ip, port)
                    self.status_label.setText(f"Reconnected! {ip}:{port}")
                else:
                    self.status_label.setText(f"Failed to reconnect {item.saved_device.name}")

    def forget_selected(self):
        """Remove selected offline devices from registry."""
        for item in self.device_list.selectedItems():
            if item.saved_device:
                self.registry.remove_device(item.saved_device.serial)
                self.status_label.setText(f"Forgot {item.saved_device.name}")

    def on_device_double_clicked(self, item):
        """Handle device double-click."""
        if item.is_online and item.device:
            self.device_double_clicked.emit(item.device)
