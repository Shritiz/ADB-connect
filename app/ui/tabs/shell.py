from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QPlainTextEdit, QLineEdit, QComboBox
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont
from app.ui.base_tab import BaseTab
from app.core.adb_manager import ADBManager


class ShellTab(BaseTab):
    """Tab for interactive shell access."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.adb = ADBManager()
        self.init_ui()

    def init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout(self)

        # Output area
        layout.addWidget(QLabel("Shell Output"))
        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setFont(QFont("Courier", 10))
        self.output.setStyleSheet("background-color: #1e1e1e; color: #d4d4d4;")
        layout.addWidget(self.output)

        # Input area
        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("Command:"))
        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("Enter shell command...")
        self.command_input.returnPressed.connect(self.run_command)
        input_layout.addWidget(self.command_input)

        run_btn = QPushButton("Run")
        run_btn.clicked.connect(self.run_command)
        input_layout.addWidget(run_btn)

        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.output.clear)
        input_layout.addWidget(clear_btn)

        layout.addLayout(input_layout)

    def update_devices(self, devices):
        """Update when selected devices change."""
        self.selected_devices = devices

    def run_command(self):
        """Execute shell command."""
        if not self.selected_devices:
            self.output.appendPlainText("Error: No device selected\n")
            return

        command = self.command_input.text()
        if not command:
            return

        device = self.selected_devices[0]
        self.output.appendPlainText(f"$ {command}\n")

        result = self.adb.shell(device.serial, command)
        self.output.appendPlainText(result + "\n")
        self.command_input.clear()
