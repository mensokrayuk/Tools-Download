"""
DownloadWorker: runs in its own QThread and downloads a single URL to disk,
streaming in chunks so the UI can show live progress/speed, and supporting
pause/resume and cancel.
"""
import os
import time
import re
import requests
from urllib.parse import urlparse, unquote
from PyQt5.QtCore import QThread, pyqtSignal


def guess_filename(url: str, headers=None) -> str:
    """Try to derive a sensible filename from Content-Disposition or the URL."""
    if headers:
        cd = headers.get("Content-Disposition", "")
        match = re.search(r'filename\*?=(?:UTF-8\'\')?"?([^";]+)"?', cd)
        if match:
            return unquote(match.group(1))
    path = urlparse(url).path
    name = os.path.basename(path)
    return unquote(name) if name else f"download_{int(time.time())}"


def human_size(num_bytes: float) -> str:
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if num_bytes < 1024:
            return f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024
    return f"{num_bytes:.1f} PB"


class DownloadWorker(QThread):
    progress = pyqtSignal(int, str, str)      # percent, speed_text, eta_text
    status_changed = pyqtSignal(str)          # e.g. "downloading", "paused", "done", "error"
    finished_ok = pyqtSignal(str)             # final filepath
    failed = pyqtSignal(str)                  # error message
    filename_ready = pyqtSignal(str)          # resolved filename

    CHUNK_SIZE = 65536

    def __init__(self, url: str, dest_dir: str, parent=None):
        super().__init__(parent)
        self.url = url
        self.dest_dir = dest_dir
        self._paused = False
        self._cancelled = False
        self.filepath = None

    def pause(self):
        self._paused = True
        self.status_changed.emit("paused")

    def resume(self):
        self._paused = False
        self.status_changed.emit("downloading")

    def cancel(self):
        self._cancelled = True

    def run(self):
        try:
            self.status_changed.emit("connecting")
            resp = requests.get(self.url, stream=True, timeout=15)
            resp.raise_for_status()

            filename = guess_filename(self.url, resp.headers)
            os.makedirs(self.dest_dir, exist_ok=True)
            self.filepath = os.path.join(self.dest_dir, filename)
            self.filename_ready.emit(filename)

            total = int(resp.headers.get("Content-Length", 0))
            downloaded = 0
            start_time = time.time()
            last_emit = 0.0

            self.status_changed.emit("downloading")

            with open(self.filepath, "wb") as f:
                for chunk in resp.iter_content(chunk_size=self.CHUNK_SIZE):
                    if self._cancelled:
                        self.status_changed.emit("cancelled")
                        f.close()
                        try:
                            os.remove(self.filepath)
                        except OSError:
                            pass
                        return

                    while self._paused and not self._cancelled:
                        self.msleep(150)

                    if not chunk:
                        continue

                    f.write(chunk)
                    downloaded += len(chunk)

                    now = time.time()
                    if now - last_emit > 0.15:  # throttle UI updates
                        elapsed = max(now - start_time, 0.001)
                        speed = downloaded / elapsed
                        speed_text = f"{human_size(speed)}/s"
                        if total:
                            percent = int(downloaded * 100 / total)
                            remaining = (total - downloaded) / speed if speed > 0 else 0
                            eta_text = f"ETA {int(remaining)}s"
                        else:
                            percent = 0
                            eta_text = "ETA --"
                        self.progress.emit(percent, speed_text, eta_text)
                        last_emit = now

            if total:
                self.progress.emit(100, "", "Done")
            self.status_changed.emit("done")
            self.finished_ok.emit(self.filepath)

        except requests.exceptions.RequestException as e:
            self.status_changed.emit("error")
            self.failed.emit(str(e))
        except Exception as e:  # noqa: BLE001
            self.status_changed.emit("error")
            self.failed.emit(str(e))
