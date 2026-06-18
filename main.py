#!/usr/bin/env python3
"""ADB Control Center - Main application entry point."""

import sys
from PySide6.QtWidgets import QApplication
from app.ui.main_window import MainWindow


def main():
    """Run the application."""
    app = QApplication(sys.argv)
    app.setApplicationName("ADB Control Center")
    app.setApplicationVersion("0.1.1")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
