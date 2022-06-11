import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from typing import Any, Dict, Iterable, Optional

import pygetwindow as gw
import schedule
import serial
from adafruit_board_toolkit import circuitpython_serial

formatter = logging.Formatter(
    fmt="%(asctime)s %(levelname)-8s %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("serial")
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler("serial.log")
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
logger.addHandler(fh)


class SerialDevice:
    serial_: serial.Serial

    connected: bool
    error_count: int

    MAX_ERROR_COUNT = 5

    def __init__(self, port: Any, baudrate=115200, **kwargs) -> None:
        self.connected = False
        self.error_count = 0

        self.serial_ = serial.Serial(baudrate=baudrate, **kwargs)
        self.serial_.setPort(port)

    def send_data(self, data: bytes) -> bool:
        if not self.connected:
            return False

        logger.debug(f"{self.serial_.port} :: {data}")
        try:
            self.serial_.open()
            self.serial_.write(data)
            self.serial_.close()
        except Exception as e:
            logger.exception(e)
            self.error_count += 1
            if self.error_count > self.MAX_ERROR_COUNT:
                self.connected = False
                logger.error(
                    f"{self} exceeded {self.MAX_ERROR_COUNT} errors; disconnecting device"
                )
            return False
        else:
            self.error_count = 0
            return True

    def connect(self):
        logger.info(f"Connected to new device: {self.serial_.port}")
        self.connected = True


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


def send_time_updates(collection: CircuitPythonDeviceCollection):
    for device in collection.connected_devices():
        if device.needs_time_update():
            device.update_time()


def send_window_updates(collection: CircuitPythonDeviceCollection):
    title: Optional[str] = None
    if sys.platform in ("darwin", "win32"):
        active_window = gw.getActiveWindow()
        if active_window:
            try:
                title = active_window.title
            except AttributeError:
                title = str(active_window)

    if not title:
        return

    for device in collection.connected_devices():
        if device.needs_window_update(title):
            device.update_active_window(title)


def main():
    logger.debug("Starting script")
    collection = CircuitPythonDeviceCollection()

    schedule.every(5).seconds.do(collection.connect_to_new_devices)
    schedule.every(1).minute.do(send_time_updates, collection)
    schedule.every(2).seconds.do(send_window_updates, collection)

    # Run all tasks immediately upon startup
    schedule.run_all()

    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    main()
