import json
import os
import sys
from datetime import datetime, timedelta
from typing import Any, Dict, Iterable, Optional

from adafruit_board_toolkit import circuitpython_serial

from .serial_device import SerialDevice


class CircuitPythonDevice:
    TIME_UPDATE_FREQUENCY = timedelta(hours=1)

    port: circuitpython_serial.ListPortInfo
    serial_device: SerialDevice

    latest_time_update: Optional[datetime]
    active_window: Optional[str]

    def __init__(self, port: circuitpython_serial.ListPortInfo) -> None:
        self.port = port
        self.serial_device = SerialDevice(port.device)

        self.latest_time_update = None
        self.active_window = None

    def _send_data(self, data: Dict[str, Any]) -> bool:
        data_to_send = (json.dumps(data) + "\n\r").encode("ascii")
        return self.serial_device.send_data(data_to_send)

    def connect(self) -> bool:
        self.serial_device.connect()
        data = {
            "event": "connect",
            "host_name": os.environ["COMPUTERNAME"],
            "host_os": sys.platform,
        }
        return self._send_data(data)

    @property
    def connected(self) -> bool:
        return self.serial_device.connected

    def update_time(self) -> bool:
        current_time = datetime.now()
        data = {"event": "sync_time", "timestamp": int(current_time.timestamp())}
        result = self._send_data(data)
        if result:
            self.latest_time_update = current_time
        return result

    def update_active_window(self, active_window: str) -> bool:
        data = {"event": "update_active_window", "active_window": active_window}
        result = self._send_data(data)
        if result:
            self.active_window = active_window
        return result

    def __eq__(self, __o: object) -> bool:
        return isinstance(__o, self.__class__) and self.port == __o.port

    def __hash__(self) -> int:
        return hash(self.port)

    def needs_time_update(self) -> bool:
        return (
            self.latest_time_update is None
            or datetime.now() >= self.latest_time_update + self.TIME_UPDATE_FREQUENCY
        )

    def needs_window_update(self, window: str) -> bool:
        return self.active_window != window


class CircuitPythonDeviceCollection:
    devices: Dict[circuitpython_serial.ListPortInfo, CircuitPythonDevice]

    def __init__(self) -> None:
        self.devices = {}

    def connect_to_new_devices(self):
        for comport in circuitpython_serial.data_comports():
            if comport not in self.devices:
                new_device = CircuitPythonDevice(comport)
                if new_device.connect():
                    self.devices[comport] = new_device

    def connected_devices(self) -> Iterable[CircuitPythonDevice]:
        return (device for device in self.devices.values() if device.connected)
