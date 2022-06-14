import logging
import sys
import time
from typing import Optional

import pygetwindow as gw
import schedule
import typer

from .circuit_python import CircuitPythonDeviceCollection

logger = logging.getLogger(__name__)


def send_time_updates(collection: CircuitPythonDeviceCollection):
    for device in collection.connected_devices():
        if device.needs_time_update():
            device.update_time()


def send_window_updates(collection: CircuitPythonDeviceCollection):
    title = get_window_title()

    if not title:
        return

    for device in collection.connected_devices():
        if device.needs_window_update(title):
            device.update_active_window(title)


def get_window_title() -> Optional[str]:
    if sys.platform not in ("darwin", "win32"):
        return None

    active_window = gw.getActiveWindow()
    if not active_window:
        return None

    if isinstance(active_window, str):
        return active_window

    try:
        return active_window.title
    except AttributeError:
        pass

    return str(active_window)


def verbose_logging():
    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)-8s %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel("INFO")
    handler.setFormatter(formatter)

    logging.root.addHandler(handler)
    logging.root.setLevel("INFO")


def setup_schedule():
    collection = CircuitPythonDeviceCollection()

    schedule.every(5).seconds.do(collection.connect_to_new_devices)
    schedule.every(1).minute.do(send_time_updates, collection)
    schedule.every(2).seconds.do(send_window_updates, collection)


def main(
    verbose: bool = typer.Option(
        False, "-v", "--verbose", help="Display additional logging"
    )
):
    """Send data to a connected Adafruit Macropad."""
    print("Starting script... Press Ctrl+C to close")

    if verbose:
        verbose_logging()

    setup_schedule()
    # Run all tasks immediately upon startup
    schedule.run_all()

    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        print("Terminating...")
        sys.exit()


def app():
    typer.run(main)


if __name__ == "__main__":
    app()
