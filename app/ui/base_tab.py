from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide6.QtCore import Qt


class BaseTab(QWidget):
    """Base class for all tabs."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_devices = []

    def update_devices(self, devices):
        """Called when selected devices change."""
        self.selected_devices = devices

    def on_show(self):
        """Called when tab becomes visible."""
        pass

    def on_hide(self):
        """Called when tab becomes hidden."""
        pass
