from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QPlainTextEdit, QComboBox, QLineEdit
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont, QTextCursor
from app.ui.base_tab import BaseTab
from app.core.adb_manager import ADBManager
import subprocess
import time


class LogcatReader(QThread):
    """Background thread to read logcat."""

    log_line_received = Signal(str)
    error_occurred = Signal(str)

    def __init__(self, device_serial: str, log_level: str = "*:V"):
        super().__init__()
        self.device_serial = device_serial
        self.log_level = log_level
        self.running = False
        self.process = None

    def run(self):
        """Stream logcat output."""
        self.running = True
        try:
            self.process = subprocess.Popen(
                ["adb", "-s", self.device_serial, "logcat", "-v", "brief", self.log_level],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )

            while self.running and self.process.poll() is None:
                line = self.process.stdout.readline()
                if line:
                    self.log_line_received.emit(line.rstrip())

        except Exception as e:
            self.error_occurred.emit(f"Logcat error: {str(e)}")

    def stop(self):
        """Stop logcat reader."""
        self.running = False
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()
        self.wait()

    def set_log_level(self, level: str):
        """Change log level (restart required)."""
        self.log_level = level


class LogsTab(BaseTab):
    """Tab for viewing device logs."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.adb = ADBManager()
        self.logcat_reader = None
        self.init_ui()

    def init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout(self)

        # Log output
        layout.addWidget(QLabel("Logcat Output"))
        self.log_output = QPlainTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setFont(QFont("Courier", 9))
        self.log_output.setStyleSheet("background-color: #1e1e1e; color: #d4d4d4;")
        layout.addWidget(self.log_output)

        # Filter area
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Level:"))

        self.level_combo = QComboBox()
        self.level_combo.addItems(["V (Verbose)", "D (Debug)", "I (Info)", "W (Warn)", "E (Error)"])
        self.level_combo.currentTextChanged.connect(self.on_level_changed)
        filter_layout.addWidget(self.level_combo)

        filter_layout.addWidget(QLabel("Tag Filter:"))
        self.tag_filter = QLineEdit()
        self.tag_filter.setPlaceholderText("(optional) Filter by tag...")
        self.tag_filter.setMaximumWidth(200)
        filter_layout.addWidget(self.tag_filter)

        pause_btn = QPushButton("Pause")
        pause_btn.setCheckable(True)
        pause_btn.toggled.connect(self.on_pause_toggled)
        filter_layout.addWidget(pause_btn)

        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.log_output.clear)
        filter_layout.addWidget(clear_btn)

        filter_layout.addStretch()
        layout.addLayout(filter_layout)

    def update_devices(self, devices):
        """Update when selected devices change."""
        self.selected_devices = devices
        # Don't auto-start logcat to avoid blocking UI
        # Will start when tab becomes visible

    def on_show(self):
        """Called when tab becomes visible - start logcat streaming."""
        if self.selected_devices and self.logcat_reader is None:
            self.start_logcat(self.selected_devices[0].serial)

    def start_logcat(self, device_serial: str):
        """Start logcat reader."""
        if self.logcat_reader:
            self.logcat_reader.stop()

        self.logcat_reader = LogcatReader(device_serial, "*:V")
        self.logcat_reader.log_line_received.connect(self.on_log_line)
        self.logcat_reader.error_occurred.connect(self.on_logcat_error)
        self.logcat_reader.start()

    def on_log_line(self, line: str):
        """Handle new log line."""
        # Apply tag filter if set
        tag_filter = self.tag_filter.text()
        if tag_filter and tag_filter not in line:
            return

        # Keep output size reasonable
        doc = self.log_output.document()
        if doc.lineCount() > 1000:
            cursor = self.log_output.textCursor()
            cursor.movePosition(QTextCursor.Start)
            cursor.select(QTextCursor.BlockUnderCursor)
            cursor.removeSelectedText()

        self.log_output.appendPlainText(line)
        self.log_output.verticalScrollBar().setValue(
            self.log_output.verticalScrollBar().maximum()
        )

    def on_logcat_error(self, error: str):
        """Handle logcat error."""
        self.log_output.appendPlainText(f"Error: {error}")

    def on_level_changed(self, text: str):
        """Handle log level change."""
        # Map UI text to log level
        level_map = {
            "V (Verbose)": "*:V",
            "D (Debug)": "*:D",
            "I (Info)": "*:I",
            "W (Warn)": "*:W",
            "E (Error)": "*:E",
        }
        if self.selected_devices and text in level_map:
            self.log_output.clear()
            self.start_logcat(self.selected_devices[0].serial)

    def on_pause_toggled(self, checked: bool):
        """Pause/resume logcat."""
        if checked:
            if self.logcat_reader:
                self.logcat_reader.stop()
                self.logcat_reader = None
        else:
            if self.selected_devices:
                self.start_logcat(self.selected_devices[0].serial)

    def on_hide(self):
        """Stop logcat when tab is hidden."""
        if self.logcat_reader:
            self.logcat_reader.stop()
            self.logcat_reader = None

    def closeEvent(self, event):
        """Clean up when closing."""
        if self.logcat_reader:
            self.logcat_reader.stop()
        super().closeEvent(event)
