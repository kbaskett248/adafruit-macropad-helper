import logging
import serial
from typing import Any


logger = logging.getLogger(__name__)


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

        logger.info(f"{self.serial_.port} :: {data}")
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
