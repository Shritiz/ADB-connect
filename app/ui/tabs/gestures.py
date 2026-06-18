from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QListWidget, QPushButton, QHBoxLayout
from app.ui.base_tab import BaseTab


class GesturesTab(BaseTab):
    """Tab for recording and playing gesture macros."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Gesture Macros (Coming Soon)"))

        # Placeholder
        info_label = QLabel(
            "This tab will allow you to:\n"
            "• Record sequences of taps and swipes\n"
            "• Save macros for later playback\n"
            "• Execute macros on multiple devices"
        )
        layout.addWidget(info_label)

        layout.addStretch()

    def update_devices(self, devices):
        """Update when selected devices change."""
        self.selected_devices = devices
