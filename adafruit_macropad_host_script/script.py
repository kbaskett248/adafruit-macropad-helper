import time

import json
import logging
import os
import subprocess
from datetime import datetime
from typing import List

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


def send_data_to_serial_port(data, ports: List[str]):
    data_to_send = (json.dumps(data) + "\n\r").encode("ascii")
    for port in ports:
        logger.debug(f"{port} :: {data}")
        try:
            ser = serial.Serial(port, 115200)
            ser.write(data_to_send)
            ser.close()
        except Exception as e:
            logger.error(f"{e}")


def send_update():
    data_to_send = {
        "computername": os.environ["COMPUTERNAME"],
        "timestamp": int(datetime.now().timestamp()),
    }

    try:
        ports = [comport.device for comport in circuitpython_serial.data_comports()]
        logger.debug(f"{ports=}")
        send_data_to_serial_port(data_to_send, ports)
    except Exception as e:
        logger.debug(e)


def main():
    print("Starting script...")
    while True:
        send_update()
        time.sleep(5)

    print("done...")


if __name__ == "__main__":
    main()
