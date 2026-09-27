"""
YtDlpWorker: runs in its own QThread and downloads video/audio using yt-dlp,
exposing the same signal interface as DownloadWorker (progress, status_changed,
finished_ok, failed, filename_ready) so the GUI can treat both interchangeably.

Note: yt-dlp downloads cannot be paused/resumed mid-stream the way a plain
HTTP download can, so this worker only supports cancel. Merging video+audio
or extracting audio to MP3 requires ffmpeg to be installed and on PATH.
"""
import os
from PyQt5.QtCore import QThread, pyqtSignal

try:
    import yt_dlp
except ImportError:  # handled gracefully in the GUI layer
    yt_dlp = None

from core.downloader import human_size


class YtDlpCancelled(Exception):
    """Raised inside the progress hook to abort an in-progress yt-dlp download."""


class YtDlpWorker(QThread):
    progress = pyqtSignal(int, str, str)      # percent, speed_text, eta_text
    status_changed = pyqtSignal(str)          # connecting / downloading / processing / done / error / cancelled
    finished_ok = pyqtSignal(str)             # final filepath
    failed = pyqtSignal(str)                  # error message
    filename_ready = pyqtSignal(str)          # resolved title/filename

    def __init__(self, url: str, dest_dir: str, audio_only: bool = False, parent=None):
        super().__init__(parent)
        self.url = url
        self.dest_dir = dest_dir
        self.audio_only = audio_only
        self._cancelled = False
        self.filepath = None

    def cancel(self):
        self._cancelled = True

    # yt-dlp calls this repeatedly during download with a status dict
    def _hook(self, d):
        if self._cancelled:
            raise YtDlpCancelled("Cancelled by user")

        status = d.get("status")
        if status == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            downloaded = d.get("downloaded_bytes", 0)
            speed = d.get("speed") or 0
            eta = d.get("eta")

            pct = int(downloaded * 100 / total) if total else 0
            speed_text = f"{human_size(speed)}/s" if speed else "--"
            eta_text = f"ETA {eta}s" if eta is not None else "ETA --"

            self.progress.emit(pct, speed_text, eta_text)
            self.status_changed.emit("downloading")
        elif status == "finished":
            # Video/audio downloaded; ffmpeg post-processing (merge/convert) may follow
            self.progress.emit(100, "", "Processing…")
            self.status_changed.emit("processing")

    def run(self):
        if yt_dlp is None:
            self.status_changed.emit("error")
            self.failed.emit(
                "yt-dlp is not installed. Run: pip install -r requirements.txt"
            )
            return

        os.makedirs(self.dest_dir, exist_ok=True)
        outtmpl = os.path.join(self.dest_dir, "%(title).150s [%(id)s].%(ext)s")

        ydl_opts = {
            "outtmpl": outtmpl,
            "progress_hooks": [self._hook],
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
            "restrictfilenames": False,
        }

        if self.audio_only:
            ydl_opts.update({
                "format": "bestaudio/best",
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }],
            })
        else:
            ydl_opts["format"] = "bestvideo+bestaudio/best"
            ydl_opts["merge_output_format"] = "mp4"

        try:
            self.status_changed.emit("connecting")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.url, download=False)
                title = info.get("title") or "media"
                self.filename_ready.emit(title)

                if self._cancelled:
                    self.status_changed.emit("cancelled")
                    return

                ydl.download([self.url])

                filename = ydl.prepare_filename(info)
                if self.audio_only:
                    base, _ = os.path.splitext(filename)
                    filename = base + ".mp3"
                self.filepath = filename

            self.status_changed.emit("done")
            self.finished_ok.emit(self.filepath or "")

        except YtDlpCancelled:
            self.status_changed.emit("cancelled")
        except Exception as e:  # noqa: BLE001
            self.status_changed.emit("error")
            self.failed.emit(str(e))
