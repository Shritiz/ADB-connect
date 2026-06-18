from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QLineEdit, QFileSystemModel,
    QTreeView, QInputDialog, QMessageBox, QProgressBar, QSplitter
)
from PySide6.QtCore import Qt, QDir, QModelIndex, QSize
from PySide6.QtGui import QIcon
from app.ui.base_tab import BaseTab
from app.core.adb_manager import ADBManager
import os


class FileExplorerTab(BaseTab):
    """Tab for browsing and transferring files."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.adb = ADBManager()
        self.current_device_path = "/sdcard"
        self.selected_devices = None
        self.init_ui()

    def init_ui(self):
        """Initialize UI."""
        layout = QHBoxLayout(self)

        # Left: PC File System
        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel("PC Files"))

        self.pc_tree = QTreeView()
        self.fs_model = QFileSystemModel()
        self.fs_model.setRootPath(QDir.homePath())
        self.pc_tree.setModel(self.fs_model)
        self.pc_tree.setRootIndex(self.fs_model.index(QDir.homePath()))
        self.pc_tree.setColumnWidth(0, 200)
        left_layout.addWidget(self.pc_tree)

        layout.addLayout(left_layout, 1)

        # Splitter
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)

        # Right: Device File System
        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("Device Files"))

        # Path bar
        path_layout = QHBoxLayout()
        self.device_path_label = QLineEdit(self.current_device_path)
        self.device_path_label.returnPressed.connect(self.on_path_enter)
        path_layout.addWidget(self.device_path_label)
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh_device_files)
        path_layout.addWidget(self.refresh_btn)
        right_layout.addLayout(path_layout)

        # File list
        self.device_file_list = QListWidget()
        self.device_file_list.itemDoubleClicked.connect(self.on_file_double_clicked)
        right_layout.addWidget(self.device_file_list)

        # Control buttons
        button_layout = QHBoxLayout()
        back_btn = QPushButton("Back")
        back_btn.clicked.connect(self.go_back)
        button_layout.addWidget(back_btn)

        mkdir_btn = QPushButton("New Folder")
        mkdir_btn.clicked.connect(self.create_folder)
        button_layout.addWidget(mkdir_btn)

        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(self.delete_file)
        button_layout.addWidget(delete_btn)

        right_layout.addLayout(button_layout)

        # Status
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #0066cc;")
        right_layout.addWidget(self.status_label)

        layout.addLayout(right_layout, 1)

    def update_devices(self, devices):
        """Update when selected devices change."""
        self.selected_devices = devices
        # Don't auto-refresh to avoid blocking UI
        # Will refresh when tab becomes visible

    def on_show(self):
        """Called when tab becomes visible - refresh file list."""
        if self.selected_devices:
            self.refresh_device_files()

    def refresh_device_files(self):
        """Refresh file list from device."""
        if not self.selected_devices:
            self.status_label.setText("No device selected")
            return

        device = self.selected_devices[0]
        try:
            self.status_label.setText("Loading...")
            output = self.adb.list_files(device.serial, self.current_device_path)

            if not output or "error" in output.lower() or "permission denied" in output.lower():
                self.status_label.setText(f"Error: {output[:100] if output else 'No response'}")
                return

            self.device_file_list.clear()
            file_count = 0

            # Parse ls -la output
            for line in output.split('\n'):
                line = line.strip()
                if not line or line.startswith('total'):
                    continue

                parts = line.split()
                if len(parts) < 9:
                    continue

                # ls -la format: perms links owner group size month day time/year filename [-> target]
                # Extract filename (usually at index 8, but handle symlinks)
                filename = parts[8]

                # If there's a symlink indicator, extract just the name before ->
                if '->' in line:
                    # Split by -> and get the part before it
                    filename_part = line.split('->')[0].strip()
                    parts_before_arrow = filename_part.split()
                    if len(parts_before_arrow) >= 9:
                        filename = parts_before_arrow[-1]

                if not filename or filename == '.':
                    continue

                # Determine if directory
                is_dir = line.startswith('d')

                item = QListWidgetItem()
                if is_dir:
                    item.setText(f"📁 {filename}")
                    item.setData(Qt.UserRole, 'dir')
                else:
                    item.setText(f"📄 {filename}")
                    item.setData(Qt.UserRole, 'file')
                item.setData(Qt.UserRole + 1, filename)

                self.device_file_list.addItem(item)
                file_count += 1

            self.status_label.setText(f"Loaded {file_count} files from {self.current_device_path}")
            self.device_path_label.setText(self.current_device_path)

        except Exception as e:
            self.status_label.setText(f"Error: {str(e)[:100]}")

    def on_file_double_clicked(self, item):
        """Handle file double-click."""
        if item.data(Qt.UserRole) == 'dir':
            filename = item.data(Qt.UserRole + 1)
            self.current_device_path = f"{self.current_device_path.rstrip('/')}/{filename}"
            self.device_path_label.setText(self.current_device_path)
            self.refresh_device_files()

    def on_path_enter(self):
        """Handle custom path entry."""
        new_path = self.device_path_label.text().strip()
        if new_path and new_path != self.current_device_path:
            self.current_device_path = new_path
            self.refresh_device_files()

    def go_back(self):
        """Go back to parent directory."""
        if self.current_device_path != '/':
            self.current_device_path = '/'.join(self.current_device_path.split('/')[:-1])
            if not self.current_device_path:
                self.current_device_path = '/'
            self.device_path_label.setText(self.current_device_path)
            self.refresh_device_files()

    def create_folder(self):
        """Create new folder on device."""
        if not self.selected_devices:
            self.status_label.setText("No device selected")
            return

        folder_name, ok = QInputDialog.getText(self, "Create Folder", "Folder name:")
        if ok and folder_name:
            device = self.selected_devices[0]
            path = f"{self.current_device_path.rstrip('/')}/{folder_name}"
            if self.adb.mkdir(device.serial, path):
                self.status_label.setText(f"Created: {path}")
                self.refresh_device_files()
            else:
                self.status_label.setText("Failed to create folder")

    def delete_file(self):
        """Delete selected file."""
        if not self.selected_devices or not self.device_file_list.selectedItems():
            self.status_label.setText("No file selected")
            return

        item = self.device_file_list.selectedItems()[0]
        filename = item.data(Qt.UserRole + 1)
        path = f"{self.current_device_path.rstrip('/')}/{filename}"

        reply = QMessageBox.question(self, "Confirm Delete", f"Delete {filename}?")
        if reply == QMessageBox.Yes:
            device = self.selected_devices[0]
            if self.adb.remove_file(device.serial, path):
                self.status_label.setText(f"Deleted: {filename}")
                self.refresh_device_files()
            else:
                self.status_label.setText("Failed to delete file")
