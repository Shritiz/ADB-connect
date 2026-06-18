from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QScrollArea, QSpinBox
)
from PySide6.QtCore import Qt, QThread, Signal, QSize
from PySide6.QtGui import QPixmap, QImage
from app.ui.base_tab import BaseTab
from app.core.adb_manager import ADBManager
from app.core.constants import QUICK_ACTIONS, KEYCODES
import io
from PIL import Image


class ScreenshotWidget(QLabel):
    """Custom label to display screenshots and handle input."""

    mouse_clicked = Signal(int, int)  # x, y
    mouse_dragged = Signal(int, int, int, int)  # x1, y1, x2, y2

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("border: 1px solid #ccc; background-color: #f0f0f0;")
        self.setMinimumSize(QSize(400, 600))
        self.start_pos = None
        self.scale_x = 1.0
        self.scale_y = 1.0

    def mousePressEvent(self, event):
        """Handle mouse click."""
        if event.button() == Qt.LeftButton:
            self.start_pos = event.pos()

    def mouseMoveEvent(self, event):
        """Handle mouse drag."""
        if self.start_pos is not None and event.buttons() == Qt.LeftButton:
            end_pos = event.pos()
            # Scale coordinates to actual screen size
            x1 = int(self.start_pos.x() / self.scale_x)
            y1 = int(self.start_pos.y() / self.scale_y)
            x2 = int(end_pos.x() / self.scale_x)
            y2 = int(end_pos.y() / self.scale_y)
            self.mouse_dragged.emit(x1, y1, x2, y2)

    def mouseReleaseEvent(self, event):
        """Handle mouse click."""
        if event.button() == Qt.LeftButton and self.start_pos is not None:
            end_pos = event.pos()
            # Check if it's a click (small distance) or a drag
            distance = (self.start_pos - end_pos).manhattanLength()
            if distance < 10:
                # It's a click
                x = int(end_pos.x() / self.scale_x)
                y = int(end_pos.y() / self.scale_y)
                self.mouse_clicked.emit(x, y)
            self.start_pos = None

    def set_pixmap_from_bytes(self, image_bytes):
        """Set pixmap from screenshot bytes."""
        try:
            img = Image.open(io.BytesIO(image_bytes))
            # Convert PIL image to QPixmap
            img_rgb = img.convert('RGB')
            data = img_rgb.tobytes("rgb")
            q_img = QImage(data, img_rgb.width, img_rgb.height, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(q_img)

            # Scale to fit widget while maintaining aspect ratio
            scaled_pixmap = pixmap.scaledToWidth(self.width() - 4, Qt.SmoothTransformation)
            self.setPixmap(scaled_pixmap)

            # Calculate scale factors for coordinate mapping
            self.scale_x = pixmap.width() / scaled_pixmap.width()
            self.scale_y = pixmap.height() / scaled_pixmap.height()
        except Exception as e:
            self.setText(f"Error loading image: {e}")


class ScreenshotFetcher(QThread):
    """Background thread to fetch screenshots."""

    screenshot_ready = Signal(bytes)
    error_occurred = Signal(str)

    def __init__(self, device_serial: str):
        super().__init__()
        self.device_serial = device_serial
        self.adb = ADBManager()
        self.running = False
        self.error_count = 0
        self.max_errors = 5

    def run(self):
        """Fetch screenshots continuously."""
        self.running = True
        while self.running and self.error_count < self.max_errors:
            try:
                screenshot = self.adb.get_screenshot(self.device_serial)
                if screenshot:
                    self.screenshot_ready.emit(screenshot)
                    self.error_count = 0  # Reset error count on success
                else:
                    self.error_count += 1
            except Exception as e:
                self.error_count += 1
                if self.error_count == 1:  # Only emit error once
                    self.error_occurred.emit(str(e))

            # Sleep with checks so we can stop quickly
            for _ in range(10):
                if not self.running:
                    break
                self.msleep(100)

    def stop(self):
        """Stop fetching screenshots."""
        self.running = False
        self.wait(timeout=2000)


class RemoteControlTab(BaseTab):
    """Tab for remote control of Android device."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.adb = ADBManager()
        self.screenshot_fetcher = None
        self.init_ui()

    def init_ui(self):
        """Initialize UI."""
        layout = QHBoxLayout(self)

        # Left side: Screenshot
        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel("Device Screen"))
        self.screenshot_widget = ScreenshotWidget()
        self.screenshot_widget.mouse_clicked.connect(self.on_tap)
        self.screenshot_widget.mouse_dragged.connect(self.on_swipe)
        left_layout.addWidget(self.screenshot_widget)
        layout.addLayout(left_layout, 1)

        # Right side: Controls
        right_layout = QVBoxLayout()

        # Key buttons
        right_layout.addWidget(QLabel("Quick Actions"))
        button_layout = QVBoxLayout()
        for action_name, (keycode_name, keycode) in QUICK_ACTIONS.items():
            btn = QPushButton(action_name)
            btn.clicked.connect(lambda checked, kc=keycode: self.on_key_button(kc))
            button_layout.addWidget(btn)
        right_layout.addLayout(button_layout)

        right_layout.addSpacing(20)

        # Text input
        right_layout.addWidget(QLabel("Send Text"))
        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("Enter text to send...")
        self.text_input.returnPressed.connect(self.on_send_text)
        right_layout.addWidget(self.text_input)

        # Custom keycode
        right_layout.addWidget(QLabel("Send Key"))
        keycode_layout = QHBoxLayout()
        self.keycode_combo = QComboBox()
        self.keycode_combo.addItems(sorted(KEYCODES.keys()))
        keycode_layout.addWidget(self.keycode_combo)
        send_key_btn = QPushButton("Send")
        send_key_btn.clicked.connect(self.on_send_key)
        keycode_layout.addWidget(send_key_btn)
        right_layout.addLayout(keycode_layout)

        # Swipe parameters
        right_layout.addWidget(QLabel("Swipe Duration (ms)"))
        self.swipe_duration = QSpinBox()
        self.swipe_duration.setValue(500)
        self.swipe_duration.setRange(100, 5000)
        right_layout.addWidget(self.swipe_duration)

        # Status
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #0066cc;")
        right_layout.addWidget(self.status_label)

        right_layout.addStretch()
        layout.addLayout(right_layout, 0)

    def update_devices(self, devices):
        """Update when selected devices change."""
        self.selected_devices = devices
        # Don't auto-start screenshot fetching here to avoid blocking UI
        # Will start when tab becomes visible

    def on_show(self):
        """Called when tab becomes visible - start screenshot fetching."""
        if self.selected_devices and self.screenshot_fetcher is None:
            self.start_screenshot_fetch(self.selected_devices[0].serial)

    def on_hide(self):
        """Stop screenshot fetching when tab is hidden."""
        if self.screenshot_fetcher:
            self.screenshot_fetcher.stop()
            self.screenshot_fetcher = None

    def start_screenshot_fetch(self, device_serial: str):
        """Start background screenshot fetching."""
        if self.screenshot_fetcher:
            self.screenshot_fetcher.stop()

        self.screenshot_fetcher = ScreenshotFetcher(device_serial)
        self.screenshot_fetcher.screenshot_ready.connect(self.on_screenshot_ready)
        self.screenshot_fetcher.error_occurred.connect(self.on_screenshot_error)
        self.screenshot_fetcher.start()

    def on_screenshot_ready(self, image_bytes):
        """Handle screenshot received."""
        self.screenshot_widget.set_pixmap_from_bytes(image_bytes)

    def on_screenshot_error(self, error):
        """Handle screenshot error."""
        self.screenshot_widget.setText(f"Error: {error}")

    def on_tap(self, x: int, y: int):
        """Handle tap gesture."""
        if not self.selected_devices:
            self.status_label.setText("No device selected")
            return

        device = self.selected_devices[0]
        if self.adb.input_tap(device.serial, x, y):
            self.status_label.setText(f"Tapped at ({x}, {y})")
        else:
            self.status_label.setText("Tap failed")

    def on_swipe(self, x1: int, y1: int, x2: int, y2: int):
        """Handle swipe gesture."""
        if not self.selected_devices:
            self.status_label.setText("No device selected")
            return

        device = self.selected_devices[0]
        duration = self.swipe_duration.value()
        if self.adb.input_swipe(device.serial, x1, y1, x2, y2, duration):
            self.status_label.setText(f"Swiped ({x1},{y1}) → ({x2},{y2})")
        else:
            self.status_label.setText("Swipe failed")

    def on_send_text(self):
        """Send text to device."""
        if not self.selected_devices:
            self.status_label.setText("No device selected")
            return

        text = self.text_input.text()
        if not text:
            return

        device = self.selected_devices[0]
        if self.adb.input_text(device.serial, text):
            self.status_label.setText(f"Sent: {text}")
            self.text_input.clear()
        else:
            self.status_label.setText("Text input failed")

    def on_send_key(self):
        """Send key event to device."""
        if not self.selected_devices:
            self.status_label.setText("No device selected")
            return

        key_name = self.keycode_combo.currentText()
        keycode = KEYCODES.get(key_name, 0)
        device = self.selected_devices[0]

        if self.adb.input_keyevent(device.serial, keycode):
            self.status_label.setText(f"Sent key: {key_name}")
        else:
            self.status_label.setText("Key send failed")

    def on_key_button(self, keycode: int):
        """Handle quick action button press."""
        if not self.selected_devices:
            self.status_label.setText("No device selected")
            return

        device = self.selected_devices[0]
        if self.adb.input_keyevent(device.serial, keycode):
            self.status_label.setText(f"Key {keycode} sent")
        else:
            self.status_label.setText("Key send failed")
