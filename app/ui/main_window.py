from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QTabWidget,
    QLabel, QPushButton, QStatusBar, QSplitter
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon
from app.ui.devices_panel import DevicesPanel
from app.ui.tabs import (
    RemoteControlTab, GesturesTab, FileExplorerTab, ShellTab, LogsTab
)
from app.workers.device_scanner import DeviceScanner


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("ADB Control Center")
        self.setWindowIcon(QIcon("📱"))
        self.setGeometry(100, 100, 1400, 900)

        # Initialize workers
        self.device_scanner = None

        # Initialize UI
        self.init_ui()

        # Start device scanning
        self.start_device_scanner()

    def init_ui(self):
        """Initialize the main UI."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)

        # Left: Device panel
        self.device_panel = DevicesPanel()
        self.device_panel.setMaximumWidth(300)
        self.device_panel.devices_selected.connect(self.on_devices_selected)
        main_layout.addWidget(self.device_panel)

        # Splitter
        splitter = QSplitter(Qt.Horizontal)

        # Right: Tab widget
        self.tab_widget = QTabWidget()

        self.remote_control_tab = RemoteControlTab()
        self.tab_widget.addTab(self.remote_control_tab, "Remote Control")

        self.gestures_tab = GesturesTab()
        self.tab_widget.addTab(self.gestures_tab, "Gestures")

        self.file_explorer_tab = FileExplorerTab()
        self.tab_widget.addTab(self.file_explorer_tab, "File Explorer")

        self.shell_tab = ShellTab()
        self.tab_widget.addTab(self.shell_tab, "Shell")

        self.logs_tab = LogsTab()
        self.tab_widget.addTab(self.logs_tab, "Logs")

        # Connect tab changes to visibility events
        self.tab_widget.currentChanged.connect(self.on_tab_changed)

        main_layout.addWidget(self.tab_widget, 1)

        # Status bar
        self.statusBar().showMessage("Ready")

    def start_device_scanner(self):
        """Start background device scanning."""
        self.device_scanner = DeviceScanner(interval=3)
        self.device_scanner.devices_updated.connect(self.on_devices_updated)
        self.device_scanner.error_occurred.connect(self.on_scan_error)
        self.device_scanner.start()

    def on_devices_updated(self, devices: list):
        """Handle device list update."""
        self.device_panel.update_devices(devices)
        self.statusBar().showMessage(
            f"{len(devices)} device(s) connected" if devices else "No devices connected"
        )

    def on_scan_error(self, error: str):
        """Handle scan error."""
        print(f"Scan error: {error}")

    def on_devices_selected(self, devices: list):
        """Handle device selection."""
        self.remote_control_tab.update_devices(devices)
        self.gestures_tab.update_devices(devices)
        self.file_explorer_tab.update_devices(devices)
        self.shell_tab.update_devices(devices)
        self.logs_tab.update_devices(devices)

        if devices:
            device = devices[0]
            self.statusBar().showMessage(
                f"Selected: {device.model} ({device.serial}) - {device.state.value}"
            )
        else:
            self.statusBar().showMessage("No device selected")

    def on_tab_changed(self, index):
        """Handle tab change - start background tasks for visible tab."""
        tab = self.tab_widget.widget(index)
        if tab and hasattr(tab, 'on_show'):
            tab.on_show()

    def closeEvent(self, event):
        """Clean up when closing."""
        if self.device_scanner:
            self.device_scanner.stop()

        # Stop all tabs
        self.remote_control_tab.on_hide()
        self.logs_tab.on_hide()

        super().closeEvent(event)
