# Adafruit Macropad Helper

This project is a computer-side companion to my
[App Pad code](https://github.com/kbaskett248/adafruit_macropad)
for the [Adafruit Macropad](https://learn.adafruit.com/adafruit-macropad-rp2040).
With it, the computer can send messages to the Macropad,
enabling richer integration.

## Getting Started

1. Clone this repo.
2. Install using [PipX](https://github.com/pypa/pipx).
   ```bash
   pipx install ./adafruit-macropad-helper
   ```
3. Run
   ```bash
   macropad-helper
   ```

## Features

- The host operating system is sent to the Macropad when the helper starts up, and is used to set the operating system setting.
- The window name of the currently active window is sent whenever it changes. This is used to automatically switch the Macropad app if there is one to handle that app.
