import logging
import sys
import time
from typing import Optional

import pygetwindow as gw
import schedule

from circuit_python import CircuitPythonDeviceCollection

logger = logging.getLogger(__name__)
logger.setLevel("INFO")

formatter = logging.Formatter(
    fmt="%(asctime)s %(levelname)-8s %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel("INFO")
handler.setFormatter(formatter)

logging.root.addHandler(handler)
logging.root.setLevel("INFO")


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
    logger.info("Starting script")
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
