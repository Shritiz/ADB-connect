# ADB Control Center

A comprehensive cross-platform desktop GUI for managing Android devices via Android Debug Bridge (ADB). Control your devices with remote gestures, file transfers, shell access, and real-time monitoring.

## Features

### Core Features (MVP)
- **Device Management**: Auto-detect USB and Wi-Fi connected devices
- **Remote Control**: Send taps, swipes, key events to control devices
- **File Explorer**: Browse device storage, push/pull files with drag-and-drop
- **Shell Terminal**: Execute shell commands directly on devices
- **Logcat Viewer**: Stream and filter device logs in real-time
- **Multi-Device Support**: Select and manage multiple devices simultaneously

### Planned Features (v1.0+)
- Gesture macros and scripting
- Wireless pairing wizard
- Screen mirroring (scrcpy integration)
- Application management (install/uninstall)
- Root mode features
- Plugin architecture

## Installation

### Requirements
- Python 3.8+
- Android Debug Bridge (ADB) installed and in PATH
- PySide6 (GUI framework)

### Setup

1. **Clone/Download the project**:
```bash
cd ADB-connect
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Run the application**:
```bash
python main.py
```

## Usage

### Starting the App
```bash
python main.py
```

The application will:
1. Start the ADB server automatically
2. Scan for connected devices
3. Display them in the left panel
4. Allow you to interact with them via the tabbed interface

### Device Selection
- **Left Panel**: Shows all connected devices with status indicators
  - 🟢 Green: Connected and ready
  - 🔴 Red: Offline
  - 🟡 Yellow: Unauthorized (approve on device)
- **Multi-select**: Hold Ctrl and click to select multiple devices
- **Single-select**: Click once to select a device

### Tabs

#### Remote Control
- View live device screen (refreshes every 1 second)
- **Tap**: Click on screen to tap
- **Swipe**: Drag to swipe
- **Quick Buttons**: Home, Back, Volume Up/Down
- **Text Input**: Send text to active field
- **Custom Keys**: Send any key event by code

#### File Explorer
- **Left pane**: Your PC file system
- **Right pane**: Device storage
- **Navigation**: Double-click folders to navigate
- **File Transfer**: 
  - Drag files from PC pane to device pane (push)
  - Double-click device files to browse
  - Right-click for context menu (delete, rename, create folder)
- **Breadcrumb**: Click path bar to navigate quickly

#### Shell
- Execute any ADB shell command
- View real-time output
- Type command and press Enter or click Run

#### Logs
- **Live logcat streaming**: Automatically shows device logs
- **Filters**:
  - Log level: V/D/I/W/E
  - Tag filter: Search for specific app/module
- **Pause**: Toggle to pause/resume streaming
- **Clear**: Clear log output

#### Gestures (Placeholder)
- Future: Record and playback tap/swipe sequences
- Future: Save and organize macros

## Project Structure

```
ADB-connect/
├── main.py                      # Application entry point
├── requirements.txt             # Python dependencies
├── README.md                    # This file
├── app/
│   ├── __init__.py
│   ├── core/                    # Core ADB functionality
│   │   ├── adb_manager.py      # ADB command wrapper
│   │   ├── device.py           # Device model
│   │   └── constants.py        # Constants and keycodes
│   ├── ui/                      # User interface
│   │   ├── main_window.py      # Main application window
│   │   ├── devices_panel.py    # Device list sidebar
│   │   ├── base_tab.py         # Base tab class
│   │   └── tabs/               # Feature tabs
│   │       ├── remote_control.py
│   │       ├── file_explorer.py
│   │       ├── shell.py
│   │       ├── logs.py
│   │       └── gestures.py
│   └── workers/                 # Background threads
│       └── device_scanner.py   # Device discovery
```

## Architecture

### Concurrency Model
- **Main Thread**: PySide6 event loop handles UI
- **Worker Threads**: 
  - Device Scanner: Polls for connected devices every 3 seconds
  - Screenshot Fetcher: Refreshes screen every 1 second
  - Logcat Reader: Streams logs continuously
- **Signal/Slot**: All data updates use Qt signals for thread-safe communication

### Device Model
```python
Device:
  - serial: Device identifier
  - model: Device model name
  - state: DEVICE, OFFLINE, UNAUTHORIZED
  - connection: USB or Wi-Fi
  - battery_level: 0-100
  - ip_address: For Wi-Fi devices
```

## Development

### Adding Features

1. **New Tab**:
   - Extend `BaseTab` class in `app/ui/base_tab.py`
   - Add to `app/ui/tabs/__init__.py`
   - Register in `MainWindow.init_ui()`

2. **New ADB Command**:
   - Add method to `ADBManager` in `app/core/adb_manager.py`
   - Use in your tab via `self.adb.your_command()`

3. **Background Task**:
   - Create worker in `app/workers/`
   - Emit `Signal` for results
   - Connect to slot in UI

### Running Tests

```bash
# Currently manual testing with real/emulated devices
# Automated tests coming soon
```

## Troubleshooting

### No devices appear
1. Check ADB is installed: `adb version`
2. Enable USB debugging on device
3. Accept RSA key prompt on device
4. Check connection: `adb devices`

### "Device unauthorized"
- Open your device and approve the RSA key for debugging

### Screenshot not updating
- Check device screen is on
- Verify device is connected: `adb devices`
- Try tapping a button to refresh

### Logcat errors
- Verify logcat permission: `adb shell logcat`
- Clear logcat buffer: `adb logcat -c`

### App won't start
1. Ensure Python 3.8+
2. Install dependencies: `pip install -r requirements.txt`
3. Check for error message in terminal

## Known Limitations

- Multi-touch not supported (Android limitation)
- Screenshot refresh is 1-second interval (not real-time video)
- Some devices may require root for accessing /data directory
- Wi-Fi connection may be unstable on poor networks

## Future Roadmap

### v0.2 (Near term)
- ✓ MVP features complete
- [ ] Gesture macro recording
- [ ] Performance optimizations

### v1.0 (Mid term)
- [ ] Wireless pairing wizard
- [ ] Screen mirroring (scrcpy integration)
- [ ] App management (install/uninstall)
- [ ] Plugin architecture
- [ ] Dark mode theming

### v2.0 (Long term)
- [ ] Advanced scripting (Lua/JavaScript)
- [ ] Performance profiling tools
- [ ] Mobile companion app
- [ ] Cloud device management

## Performance Notes

- Device scanning: Every 3 seconds (configurable)
- Screenshot refresh: Every 1 second (configurable)
- ADB connection pooling for efficiency
- Multi-threaded for non-blocking UI

## License

MIT License - See LICENSE file

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Open pull request

## Support

For issues or feature requests, open an issue on GitHub.

## Changelog

### v0.1.0 (Initial Release)
- Device detection (USB/Wi-Fi)
- Remote control (tap/swipe/keys)
- File explorer (push/pull/browse)
- Shell access
- Logcat streaming
- Multi-device support

