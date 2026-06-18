import subprocess
from typing import List, Tuple, Optional
from app.core.constants import ADB_DEFAULT_PORT, ADB_TIMEOUT


class ConnectionManager:
    """Manages device connection attempts with multiple IP/port combinations."""

    COMMON_PORTS = [5555, 5037, 5038, 5039]
    SUBNET_RANGES = ["192.168.1", "192.168.0", "10.0.0", "172.16.0"]

    @staticmethod
    def try_connect(ip: str, port: int = ADB_DEFAULT_PORT) -> bool:
        """Try to connect to a device at the given IP and port."""
        try:
            result = subprocess.run(
                ["adb", "connect", f"{ip}:{port}"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return "connected" in result.stdout.lower() or result.returncode == 0
        except Exception as e:
            print(f"Connection attempt failed: {e}")
            return False

    @staticmethod
    def try_multiple_ports(ip: str, ports: List[int] = None) -> bool:
        """Try connecting with multiple ports."""
        if ports is None:
            ports = ConnectionManager.COMMON_PORTS

        for port in ports:
            print(f"Trying {ip}:{port}...")
            if ConnectionManager.try_connect(ip, port):
                print(f"Success! Connected to {ip}:{port}")
                return True

        print(f"Failed to connect to {ip} on any port")
        return False

    @staticmethod
    def try_multiple_ips(base_ip: str, ports: List[int] = None, max_attempts: int = 10) -> Optional[Tuple[str, int]]:
        """
        Try connecting with multiple IP combinations.

        Args:
            base_ip: Base IP like "192.168.1.100"
            ports: List of ports to try
            max_attempts: Max number of IPs to try in the subnet

        Returns:
            Tuple of (ip, port) if successful, None otherwise
        """
        if ports is None:
            ports = ConnectionManager.COMMON_PORTS

        # Extract subnet from base IP
        parts = base_ip.split('.')
        if len(parts) != 4:
            return None

        subnet = '.'.join(parts[:3])

        # Try IPs in the subnet
        for i in range(1, min(256, 1 + max_attempts)):
            test_ip = f"{subnet}.{i}"
            for port in ports:
                try:
                    result = subprocess.run(
                        ["adb", "connect", f"{test_ip}:{port}"],
                        capture_output=True,
                        text=True,
                        timeout=3
                    )
                    if "connected" in result.stdout.lower() or result.returncode == 0:
                        print(f"Found device at {test_ip}:{port}")
                        return (test_ip, port)
                except Exception:
                    continue

        print(f"Could not find device in {subnet}.* subnet")
        return None

    @staticmethod
    def auto_reconnect_wifi(saved_device) -> Optional[Tuple[str, int]]:
        """
        Attempt to reconnect to a previously paired Wi-Fi device.
        Tries last known IP first, then scans subnet.
        """
        if not saved_device:
            return None

        # Try last known IP first
        if saved_device.last_ip:
            print(f"Trying last known IP: {saved_device.last_ip}")
            if ConnectionManager.try_multiple_ports(saved_device.last_ip):
                return (saved_device.last_ip, saved_device.last_port)

        # Try subnet scan if last IP didn't work
        if saved_device.last_ip:
            print(f"Scanning subnet around {saved_device.last_ip}...")
            result = ConnectionManager.try_multiple_ips(saved_device.last_ip, max_attempts=20)
            if result:
                return result

        print(f"Could not reconnect to {saved_device.name}")
        return None
