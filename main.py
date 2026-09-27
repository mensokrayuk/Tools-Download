#!/usr/bin/env python3
"""
Purple Download Manager
------------------------
An all-in-one file downloader built with PyQt5.
Features:
 - Animated purple gradient background (shifting hue over time)
 - Glowing / color-pulsing buttons
 - Smooth animated progress bars per download
 - Multi-file download queue (add URLs, start/pause/cancel individually or all)
 - Live speed + ETA readout, log console
 - Drag & drop a .txt file full of URLs to bulk-add

Run:
    pip install -r requirements.txt
    python main.py
"""
import sys
from PyQt5.QtWidgets import QApplication
from gui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Purple Download Manager")
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
